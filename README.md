# PDF → Excel Converter

A SaaS that converts digital, scanned, and handwritten PDFs into structured
Excel files. Differentiator vs. iLovePDF / Camelot: a unified geometric
table-reconstruction algorithm that runs on word boxes from *either* source.

[![ci](https://github.com/<org>/file-converter/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)

## Layout

```
frontend/         Next.js 16.2.4 + React 19.2.4 UI (upload → polling → download)
backend/app/      FastAPI + Celery worker + Celery beat
infrastructure/   docker-compose (dev + prod overlay) + nginx
docs/             one write-up per completed phase
```

## Quick start

```bash
cp backend/.env.example backend/.env
make up                                       # build + start dev stack
curl -F file=@MonzoBus.pdf -F mode=accurate http://localhost:8080/api/jobs
# wait ~12s, get the job id back, then:
curl -OJ http://localhost:8080/api/jobs/<id>/download
```

UI: <http://localhost:8080> (through nginx) or <http://localhost:3000> (direct frontend).
API docs: <http://localhost:8080/api/docs>.

## Architecture

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
                                                                    │  Object    │
                                                                    │  Storage   │
                                                                    │  (Oracle)  │
                                                                    └────────────┘
```

A separate Celery `beat` service runs the periodic expiry sweeper.

## The pipeline

```
PDF
 │
 ▼
detect_pdf_type      → digital | scanned | hybrid
 │
 ▼
WordBox[]  ←─── extract_digital_words   (pdfplumber, for text-layer pages)
              + extract_ocr             (PyMuPDF render → PaddleOCR/Tesseract)
 │
 ▼
reconstruct_tables   ← THE DIFFERENTIATOR: word-CENTER peaks identify columns,
                       extent-density VALLEYS pick the boundaries between them.
                       Same algorithm, any source.
 │
 ▼
clean_tables          (drop-non-tables → cross-page-merge → continuation-fold → type-infer)
 │
 ▼
export_excel          (typed cells, hidden _confidence sheet, conditional formatting)
```

Algorithm details: [`docs/table-reconstruction.md`](docs/table-reconstruction.md).

## Modes

| Flag        | OCR DPI | Continuation merge | Notes                                        |
| ----------- | ------- | ------------------ | -------------------------------------------- |
| `fast`      | 200     | off                | Default. Slightly noisier, no risk of merging two transactions. |
| `accurate`  | 300     | on (geometric)     | Fewer rows, wraps folded onto right Date row. |

Mode is set via `?mode=fast|accurate` form field on `POST /api/jobs`.

## API

- `POST   /api/jobs`             — upload PDF (multipart). Returns `{id, status, ...}`.
- `GET    /api/jobs/{id}`        — current status + metrics. Frontend polls every 1.5s.
- `GET    /api/jobs/{id}/download` — streams the .xlsx (after `status=completed`).
- `GET    /api/healthz`          — health check.

Per-IP rate limits: 10 POST/min, 120 GET/min, 30 download/min.

## Tests + benchmark

```bash
make test                                      # 44 tests, ~40 s
python -m scripts.benchmark theirs.xlsx ours.xlsx    # vs iLovePDF or any other tool
```

Self-comparison scores 1.000; fast-vs-accurate scores 0.900 (fewer rows in
accurate, same data).

## Deploy

See [`docs/phase-8-deployment.md`](docs/phase-8-deployment.md) for the full
Oracle Cloud VM walkthrough. Short version:

```bash
cp infrastructure/.env.prod.example infrastructure/.env.prod
# fill in DB password, Oracle creds, your domain in CORS_ORIGINS
make prod-up
```

## Documentation

- [`PROJECT_PLAN.md`](PROJECT_PLAN.md) — architecture, phase plan, hard rules
- [`STATUS.md`](STATUS.md) — live phase board
- [`CLAUDE.md`](CLAUDE.md) — guidance for Claude Code sessions
- [`docs/`](docs/) — one write-up per completed phase + the algorithm spec

## License

Internal — not for public distribution.
