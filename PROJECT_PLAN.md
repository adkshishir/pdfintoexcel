# PDF → Excel Converter — Master Plan

> Goal: convert digital, scanned, and handwritten PDFs into clean structured
> Excel files with higher table-reconstruction accuracy than iLovePDF.

This document is the **architectural plan**. Day-to-day progress is tracked in
[`STATUS.md`](./STATUS.md). When a phase completes, update STATUS.md — do
**not** rewrite this plan unless the architecture itself changes.

---

## 1. System overview

```
                ┌────────────┐  upload   ┌────────────┐  enqueue  ┌────────────┐
   browser ───► │  Next.js   │ ────────► │  FastAPI   │ ────────► │   Redis    │
                │  frontend  │ ◄──────── │   API      │           │   queue    │
                └────────────┘  status/  └─────┬──────┘           └─────┬──────┘
                                download       │                        │
                                                │ writes job             │ pops job
                                          ┌─────▼──────┐           ┌─────▼──────┐
                                          │ PostgreSQL │           │  Celery    │
                                          │   jobs     │ ◄──update │  worker(s) │
                                          └────────────┘           └─────┬──────┘
                                                                          │
                                                          read input /    │
                                                          write output    ▼
                                                                    ┌────────────┐
                                                                    │ Object     │
                                                                    │ Storage    │
                                                                    │ (Oracle)   │
                                                                    └────────────┘
```

Reverse proxy: nginx terminates TLS and routes `/api/*` to FastAPI, everything
else to Next.js.

---

## 2. Component responsibilities

| Component       | Responsibility                                                    |
| --------------- | ----------------------------------------------------------------- |
| `frontend/`     | Upload UI, job polling, download. **No business logic.**          |
| `backend/api/`  | HTTP surface only — validation, auth, enqueue, status, download.  |
| `backend/services/` | Glue between API and DB/queue/storage.                        |
| `backend/pipeline/` | Orchestrator that runs detect → extract → reconstruct → export. |
| `backend/ocr/`  | Pluggable OCR engines (Paddle, Tesseract). Returns word boxes.    |
| `backend/table/`| Geometric table reconstruction from word boxes (the differentiator). |
| `backend/storage/` | Object storage abstraction (Oracle OS in prod, local in dev).  |
| `backend/queue/` | Celery app + task definitions. Worker imports tasks from here.   |
| `backend/models/`| SQLAlchemy models + DB session.                                  |

**Hard rule:** API never imports from `pipeline/`. Workers never import from `api/`.
Both go through `services/` and `models/`.

---

## 3. Processing pipeline (the core)

The pipeline is one orchestrator (`pipeline/orchestrator.py`) that runs five
stages. Each stage produces a typed intermediate that the next stage consumes —
this is what lets us swap OCR engines, run hybrid mode, and unit-test stages
independently.

```
PDF bytes
   │
   ▼
[1] detect_pdf_type    → DigitalDoc | ScannedDoc | HybridDoc
   │
   ├── digital ──► [2a] digital_extract  (pdfplumber + Camelot)
   │                       │
   │                       ▼
   │                 List[RawTable]
   │
   └── scanned ──► [2b] ocr_extract      (Paddle, fallback Tesseract)
                           │
                           ▼
                     List[WordBox]   (text + x/y/w/h + page + confidence)
                           │
                           ▼
                  [3] reconstruct_tables  ← THE DIFFERENTIATOR
                           │  - Y-axis row clustering (DBSCAN-style)
                           │  - X-axis column detection (vertical projection)
                           │  - merged-cell handling, ruling-line hints
                           ▼
                     List[RawTable]
                           │
                           ▼
                    [4] clean_tables
                           │  - whitespace normalization, header detection,
                           │    column type inference, dedupe artifacts
                           ▼
                    List[CleanTable]
                           │
                           ▼
                  [5] export_excel  (pandas + openpyxl, one sheet per table)
                           │
                           ▼
                       output.xlsx
```

**Hybrid mode (accurate):** when a digital PDF has *some* text but *also*
detectable raster regions (e.g., a scanned receipt embedded in a digital
report), we run *both* 2a and 2b and merge by bounding-box overlap before
stage 3. This is the path that should beat iLovePDF on mixed documents.

**Confidence scoring:** stage 3 emits a per-cell confidence (OCR confidence ×
geometric alignment score). The Excel export adds a hidden `_confidence`
sheet so callers can highlight low-confidence cells in a future UI.

---

## 4. Data contracts (typed intermediates)

These types live in `backend/app/pipeline/types.py` and are the *contract*
between stages. Changing them is a cross-cutting change.

```python
WordBox    = (text, x, y, w, h, page, ocr_conf)
RawCell    = (row, col, row_span, col_span, text, conf)
RawTable   = (page, bbox, cells: list[RawCell])
CleanTable = (sheet_name, headers, rows, conf_grid)
```

---

## 5. Job lifecycle

```
pending  ──enqueue──►  queued  ──worker picks up──►  processing
                                                          │
                                ┌─────────────────────────┴─────────────┐
                                ▼                                       ▼
                            completed                                failed
                                │                                       │
                                └────── expires_at (1–24h) ── deleted ──┘
```

States are persisted in `jobs` table; the API never asks the worker directly.
A periodic Celery beat task (`cleanup_expired_jobs`) deletes expired files
from object storage and marks rows.

---

## 6. Database schema (initial)

```sql
CREATE TABLE jobs (
  id            UUID PRIMARY KEY,
  status        TEXT NOT NULL,            -- pending|queued|processing|completed|failed
  mode          TEXT NOT NULL,            -- 'fast' | 'accurate'
  input_url     TEXT NOT NULL,            -- object storage key
  output_url    TEXT,                     -- set when completed
  filename      TEXT NOT NULL,
  size_bytes    BIGINT NOT NULL,
  page_count    INT,
  pdf_type      TEXT,                     -- digital|scanned|hybrid (filled by detector)
  error         TEXT,                     -- present when failed
  metrics       JSONB,                    -- timings, table count, mean confidence
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at    TIMESTAMPTZ,
  completed_at  TIMESTAMPTZ,
  expires_at    TIMESTAMPTZ NOT NULL
);

CREATE INDEX jobs_expires_at_idx ON jobs (expires_at) WHERE status = 'completed';
CREATE INDEX jobs_status_idx     ON jobs (status);
```

Migrations managed by Alembic.

---

## 7. Storage layout (object storage)

```
uploads/{job_id}/input.pdf
outputs/{job_id}/output.xlsx
debug/{job_id}/page-{n}.png        # only when mode=accurate, kept for QA
```

All keys auto-deleted after `expires_at`.

---

## 8. Phase plan

Each phase delivers something runnable end-to-end at its scope. After every
phase, update `STATUS.md` and write a short doc under `docs/` describing what
landed.

| Phase | Title                                | Acceptance criteria                                                  |
| ----- | ------------------------------------ | -------------------------------------------------------------------- |
| 0     | Scaffolding & docs                   | This plan + STATUS.md + folder skeleton + docker-compose.yml exist.  |
| 1     | Backend foundation                   | `POST /api/jobs` accepts a PDF, persists row, enqueues task. `GET /api/jobs/{id}` returns status. Celery worker boots and marks `processing → completed` (no real work yet). |
| 2     | Digital pipeline                     | Worker extracts tables from a text-layer PDF using pdfplumber+Camelot and produces a real `.xlsx`. |
| 3     | OCR pipeline                         | Scanned PDF → page images → PaddleOCR → `WordBox[]`. Tesseract fallback wired. |
| 4     | Table reconstruction (differentiator)| `WordBox[]` → `RawTable[]`. Algorithm doc in `docs/table-reconstruction.md`. Beats Camelot on a held-out scanned sample. |
| 5     | Cleaning + Excel export              | Header detection, type inference, multi-sheet workbook, confidence sheet. |
| 6     | Hybrid mode + accurate/fast modes    | Mode flag honored end-to-end; hybrid merger implemented.             |
| 7     | Frontend integration                 | Upload, polling, download UI wired to real backend.                  |
| 8     | Infrastructure & deployment          | `docker-compose up` brings the whole stack up locally; nginx routes; Oracle Object Storage credentials work. |
| 9     | Security & hardening                 | File-type sniffing, size limits, rate limiting, job timeouts, expiry sweeper. |
| 10    | E2E tests + accuracy benchmark       | Test suite + benchmark script comparing our output against iLovePDF on a fixture set. |

Phases 1–6 are sequential. Phases 7–9 can overlap once 6 is done.

---

## 9. Tech choices (locked)

| Concern         | Choice                                  | Why                                            |
| --------------- | --------------------------------------- | ---------------------------------------------- |
| Backend         | FastAPI + uvicorn                       | Async, type-driven, fits queue model.          |
| Queue           | Celery + Redis broker                   | Mature, easy worker scaling, beat scheduler.   |
| DB              | PostgreSQL + SQLAlchemy 2.x + Alembic   | Stable, JSONB for `metrics`.                   |
| Object storage  | Oracle Object Storage (S3 compat)       | Per spec; abstracted behind interface.         |
| OCR primary     | PaddleOCR                               | Strong on tables + multilingual.               |
| OCR fallback    | Tesseract (pytesseract)                 | Available everywhere, deterministic.           |
| PDF text/tables | PyMuPDF + pdfplumber + Camelot          | PyMuPDF for detect, plumber/Camelot for digital tables. |
| Excel output    | pandas + openpyxl                       | Multi-sheet, formula-friendly.                 |
| Frontend        | Next.js 16.2.4 + React 19.2.4           | Already scaffolded. **Consult `node_modules/next/dist/docs/`** before changes. |

---

## 10. Out of scope (for now)

- User accounts / auth (anonymous job IDs only — add later behind a flag).
- Stripe / billing.
- Multi-tenancy.
- WebSocket job push (polling is fine until proven otherwise).
- LLM-based table interpretation (separate, expensive path; revisit after Phase 6).
