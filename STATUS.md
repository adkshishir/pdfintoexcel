# Status

> Live progress tracker. Update this file at the **end of every phase** (or
> when a phase's acceptance criteria materially shift). Plan lives in
> [`PROJECT_PLAN.md`](./PROJECT_PLAN.md).

**Last updated:** 2026-05-09
**Current phase:** **Post-completion — marketing site, admin CMS, SEO, and growth tooling (actively shipping).** Core converter phases (0–10) remain complete.

---

## Phase board

| #   | Phase                                 | Status         | Notes                                                                                                                                                                                                                                       |
| --- | ------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0   | Scaffolding & docs                    | ✅ done        | Folder skeleton, plan, status, CLAUDE.md, compose.                                                                                                                                                                                          |
| 1   | Backend foundation                    | ✅ done        | See `docs/phase-1-backend-foundation.md`.                                                                                                                                                                                                   |
| 2   | Digital pipeline                      | ✅ done        | (Reimplemented in Phase 6 via the unified reconstructor path; `digital.py` retired.)                                                                                                                                                        |
| 3   | OCR pipeline                          | ✅ done        | See `docs/phase-3-ocr-pipeline.md`.                                                                                                                                                                                                         |
| 4   | Table reconstruction (differentiator) | ✅ done        | See `docs/phase-4-reconstruction.md` + `docs/table-reconstruction.md`.                                                                                                                                                                      |
| 5   | Cleaning + Excel export               | ✅ done        | See `docs/phase-5-cleaning-and-export.md`.                                                                                                                                                                                                  |
| 6   | Hybrid mode + fast/accurate modes     | ✅ done        | All three paths unified. See `docs/phase-6-hybrid-and-modes.md`.                                                                                                                                                                            |
| 7   | Frontend integration                  | ✅ done        | See `docs/phase-7-frontend.md`.                                                                                                                                                                                                             |
| 8   | Infrastructure & deployment           | ✅ done        | See `docs/phase-8-deployment.md`.                                                                                                                                                                                                           |
| 9   | Security & hardening                  | ✅ done        | See `docs/phase-9-security.md`.                                                                                                                                                                                                             |
| 10  | E2E tests + accuracy benchmark        | ✅ done        | xlsx-vs-xlsx benchmark framework (`backend/scripts/benchmark.py`), HTTP-level E2E test against `MonzoBus.pdf` with content assertions, CI workflow (`.github/workflows/ci.yml`). 44 tests pass. See `docs/phase-10-tests-and-benchmark.md`. |

Legend: ⬜ not started · 🟡 partial · ✅ done · ⛔ blocked

---

## What landed in Phase 10 (final)

The accuracy + verification layer.

- `backend/scripts/benchmark.py` — workbook-vs-workbook comparator with 4 metrics (headers_match, row_count_ratio, cell_recall, type_preservation). Self-comparison scores 1.000; fast-vs-accurate scores 0.900.
- `backend/tests/test_e2e_real_pdf.py` — full HTTP upload → process → download against `MonzoBus.pdf` with content assertions on specific transactions, typed columns, and the confidence sheet.
- `.github/workflows/ci.yml` — backend pytest (with libmagic, lightweight deps) + frontend ESLint + production build, runs on push/PR.
- Top-level `README.md` — full project doc, no longer a stub.
- Doc: `docs/phase-10-tests-and-benchmark.md` (with the page-0 known-loss writeup).

44 tests pass.

---

## Post-completion: full-document structured extraction

New `extraction_scope=full_document` mode replaces the old positional-grid layout export with an intelligent content-aware pipeline.

**What changed:**

The old `export_full_document` (in `layout_export.py`) placed every word in a giant grid by X/Y coordinate — it had no concept of paragraphs, headings, or key-value pairs, and tables were not extracted at all.

The new pipeline:

1. **Table extraction** runs the same quality path as `tables_only` (footer filtering → Tier-1/Tier-2 for digital, reconstructor for scanned).
2. **Content classification** (`pipeline/content_classifier.py`) groups remaining body words into paragraphs, classifies each as `heading` / `paragraph` / `bullet` / `key_value` / `table`, and places them in reading order with their page position.
3. **Header/footer detection** reuses the existing fingerprint logic from `layout_export.py`. Repeated header lines are extracted from page 0; the canonical footer (last page that has footer-zone words) is printed once at the end.
4. **Structured Excel export** (`pipeline/structured_exporter.py`) writes a single "Document" sheet:
   - Blue "DOCUMENT HEADER" label row → title / KV metadata lines
   - Body blocks in reading order (headings, paragraphs, bullets, inline tables with alternating row fills)
   - Blue "DOCUMENT FOOTER" label row → italic gray footer lines

**Files added / changed:**

- `pipeline/types.py` — `ContentBlockKind`, `ContentBlock`, `DocumentContent` types; `source_page`/`source_y` fields on `CleanTable`.
- `pipeline/content_classifier.py` — NEW. `classify_document()` entry point + all classification helpers.
- `pipeline/structured_exporter.py` — NEW. `export_structured_document()` entry point + all openpyxl layout helpers.
- `pipeline/orchestrator.py` — `full_document` branch rewritten to run the full extraction + classify + export chain; `export_full_document` import removed.
- `tests/test_job_lifecycle.py` — `table_count == 0` assertion updated to `>= 0` (full_document now extracts tables).

**61 tests pass.**

---

## Post-completion: row-alignment fix (wrap / preamble merging)

Multi-line cell content no longer produces phantom extra rows in the Excel output.

**Root cause (two layers):**

1. `table/reconstructor.py` — `_cluster_rows` used a single Y-tolerance (`h_med × 0.5`) for all words. When a date cell is vertically centred inside a tall wrapped cell, the date token lands up to 1.5 line-heights below the first description word and was split into a separate `_Row`, producing a spurious body row.

2. `pipeline/cleaner.py` — `_merge_continuations` only merged *backward* (anchor-empty row into the preceding anchor row). When the description-first line was the *first* body row of the table, `new_rows` was empty, so the preamble was emitted standalone and the date/amount became a separate Excel row.

**Fixes:**

- **Reconstructor**: two additions to `_cluster_rows` — a same-line shortcut (words within 10 % of line-height of any current-row word always join), and an inter-column loose tolerance (1.5 × h_med for words in non-overlapping X regions, i.e. different columns).
- **Cleaner**: `_merge_continuations` now has a forward-merge preamble path. Anchor-empty rows with no backward-merge target are buffered; when the next anchor-filled row arrives within the gap threshold the buffer is prepended into it. A lookahead guard (`is_preamble_for_next`) prevents mid-table wrap rows from being misrouted forward.

Touched: `table/reconstructor.py`, `pipeline/cleaner.py`. 4 new tests added (`test_reconstructor.py::test_inter_column_y_tolerance_merges_offset_date`, `test_cleaner.py::test_forward_preamble_first_row`, `test_forward_preamble_multi_line`). **61 tests pass total** (excluding E2E).

---

## Post-completion: dev Docker Compose + `Dockerfile.worker`

`infrastructure/docker-compose.dev.yml` — overlay for local development. Bind-mounts source code so changes reflect without rebuilding images:

- **backend**: `../backend/app` mounted over the baked copy; uvicorn runs `--reload`.
- **worker**: source mounted; `watchmedo auto-restart` re-spawns Celery on any `.py` change.
- **beat**: source mounted (manual `docker compose restart beat` after schedule changes).
- **frontend**: unchanged — base already uses `npm run dev` with source volume.

Also created `backend/Dockerfile.worker` (referenced everywhere but never written): adds Tesseract, Poppler, libGL/OpenCV deps that the lean API image omits. Added `watchdog==6.0.0` to `requirements.txt` for the `watchmedo` binary.

---

## Post-completion: `output_layout` flag

Added end-to-end after the 10 planned phases. User now picks per-job:

- `merged` (default) — consecutive same-header tables fold into one sheet (current behavior)
- `split` — keep each detected table on its own sheet (mirrors PDF page split)

Touched: `pipeline/types.py` (literal), `models/job.py` + Alembic migration `0002_add_output_layout`, `services/job_service.py`, `api/jobs.py` (form field + validation), `queue/tasks.py`, `pipeline/orchestrator.py`, `pipeline/cleaner.py` (skips `_merge_consecutive` when split), `frontend/src/app/page.tsx` (third selector below mode), Job panel surfaces the chosen layout. 6 new tests in `tests/test_output_layout.py`. **50 tests pass total.**

---

## Post-completion: marketing site, SEO, landing pages & admin CMS

Growth and editorial layer on top of the shipped converter — **still evolving** on `master` as of May 2026.

**Backend (FastAPI)**

- **Admin auth** — JWT access + refresh for the dashboard (`app/api/admin_auth.py`, `app/services/auth_service.py`, `app/models/admin_user.py`). Refresh token rotation and logout/revocation paths.
- **Public + admin blog** — `app/api/blog.py` (published only) and `app/api/admin_blog.py` (CRUD, drafts, search). Post fields extended for SEO and scheduling (e.g. meta title, `scheduled_at`, cover image, robots directives) with ORM and migrations aligned in `0008_blog_posts_ensure_columns`.
- **SEO data model** — `app/models/seo.py`: `SeoMeta`, structured `SchemaDocument`, internal links, optional site settings, **landing pages** (`LandingPage` with body, FAQ JSON, internal links). Admin APIs in `app/api/admin_seo.py` + `app/services/seo_service.py`.
- **Public landing API** — `app/api/landing.py` lists and resolves **published** landing pages by slug for the marketing site.
- **Analytics** — `app/api/analytics.py` + `app/services/analytics_service.py` expose richer overview, time series, and top-page metrics for the internal dashboard.

**Database**

- Alembic **`0007_admin_seo_system`** — admin users, SEO/landing/schema/linking tables, and related growth schema.
- Alembic **`0008_blog_posts_ensure_columns`** — idempotent column repair for `blog_posts` (handles partial or drifted DBs).

**Frontend (Next.js)**

- **Dashboard shell** — `frontend/src/app/dashboard/layout.tsx` with nav: Analytics, Blog, SEO, Landing Pages, Site Ops, Activity. Session gating via `frontend/src/lib/admin-auth.ts` and API helpers (`admin-api.ts`).
- **Dashboard home** — analytics overview + charts (`analytics-client.tsx`) fed from the internal analytics API.
- **Editorial UIs** — blog CRUD under `/dashboard/blog/*`; SEO and landing-page management under `/dashboard/seo` and `/dashboard/landing-pages`.
- **Marketing** — dynamic marketing routes (e.g. `(marketing)/[slug]`), public blog rendering and sitemap updates; header/middleware adjustments for the public site.

**Tests**

- `backend/tests/test_admin_auth_and_blog.py` — login, refresh rotation, logout, draft vs published visibility, slug conflicts, list/search, delete.
- Older sections above quote **point-in-time** test counts; the backend suite has **grown** (80+ `test_*` functions across `backend/tests/`). Authoritative count: run `pytest` in CI or after `pip install -r backend/requirements.txt`.

**Infra / worker**

- `infrastructure/docker-compose.yml` and Celery app/tasks updated as needed for the expanded app (config surface in `app/config.py`, `app/queue/`).

---

## Project complete

All **planned** phases (0–10) shipped. Subsequent work focuses on CMS, SEO,
landing pages, and internal analytics (see **Post-completion: marketing site,
SEO, landing pages & admin CMS** above)—the core PDF → Excel pipeline remains
unchanged architecturally.

End-to-end (converter):

- Upload `MonzoBus.pdf` (24-page bank statement) → status flips queued → processing → completed in ~12 s
- Download a 1-sheet workbook with **550 transactions in accurate mode**, typed Date/Amount/Balance columns, plus a hidden `_confidence` sheet with conditional formatting
- The reconstruction algorithm runs on the same `WordBox[]` interface whether the source is digital text (pdfplumber) or OCR (PaddleOCR/Tesseract) — meaning quality on scanned PDFs is bounded by OCR accuracy, not by a separate detection pipeline

Known limitations are documented in the per-phase docs (search `What … deliberately leaves unfinished`). Most notable:

- **Page-0 multi-block handling** — pages with both a cover-summary and a transaction table lose the latter to the noise filter. Fix is two-table-per-page reconstruction.
- **Cross-page wrap merging** — descriptions wrapping across page breaks don't fold (page boundaries get a `+inf` gap).
- **Real OCI integration** — the boto3 backend is implemented but never run against a live OCI tenant; first prod boot is the integration test.

---

## Open questions / decisions deferred

- **OCR runtime.** PaddleOCR brings ~1.5GB of model weights. Bake into worker
  image (slow build, fast cold start) or download on first use (fast build,
  slow first job)? Default: bake. Revisit if image size becomes painful.
- **Oracle Object Storage credentials.** Need OCI tenancy details for first
  production deploy. Until then storage uses the local-disk implementation.
- **Sample PDFs for benchmarking.** A broader fixture set (mix of digital,
  scanned, handwritten, multi-table) would strengthen regression detection
  beyond the current E2E and unit coverage.
- **Dashboard auth UX.** Session vs cookie edge cases and which routes are
  public vs admin-only should stay aligned with `middleware.ts` and
  `getAdminSession` as the CMS grows.

---

## Per-phase doc index

Each completed phase gets a write-up under `docs/`. Index:

- [Phase 1 — Backend foundation](docs/phase-1-backend-foundation.md)
- [Phase 2 — Digital pipeline](docs/phase-2-digital-pipeline.md)
- [Phase 3 — OCR pipeline](docs/phase-3-ocr-pipeline.md)
- [Phase 4 — Table reconstruction](docs/phase-4-reconstruction.md) + [algorithm spec](docs/table-reconstruction.md)
- [Phase 5 — Cleaning + Excel export](docs/phase-5-cleaning-and-export.md)
- [Phase 6 — Hybrid + fast/accurate modes](docs/phase-6-hybrid-and-modes.md)
- [Phase 7 — Frontend integration](docs/phase-7-frontend.md)
- [Phase 8 — Infrastructure & deployment](docs/phase-8-deployment.md)
- [Phase 9 — Security & hardening](docs/phase-9-security.md)
- [Phase 10 — E2E tests + benchmark](docs/phase-10-tests-and-benchmark.md)
