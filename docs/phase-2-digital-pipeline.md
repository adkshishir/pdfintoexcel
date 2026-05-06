# Phase 2 — Digital PDF pipeline

**Shipped:** 2026-05-01
**Acceptance criteria** (PROJECT_PLAN.md §8):
> Worker extracts tables from a text-layer PDF using pdfplumber + Camelot and produces a real `.xlsx`.

## What landed

| Concern             | File                              | Notes                                                                     |
| ------------------- | --------------------------------- | ------------------------------------------------------------------------- |
| Type detection      | `app/pipeline/detector.py`        | PyMuPDF text-density heuristic. Returns `digital`/`scanned`/`hybrid`.    |
| Digital extraction  | `app/pipeline/digital.py`         | pdfplumber word boxes → Y-cluster rows → header-anchored column buckets. |
| Cleaning            | `app/pipeline/cleaner.py`         | Whitespace collapse, blank-row drop, sheet-name dedupe.                  |
| Excel export        | `app/pipeline/exporter.py`        | openpyxl: one sheet per table, bold header, frozen first row.            |
| Orchestrator        | `app/pipeline/orchestrator.py`    | Wires detect → extract → clean → export with per-stage timings.          |
| Worker upload path  | `app/queue/tasks.py`              | Tempfile out, `storage.put` after pipeline succeeds.                     |
| Synthetic test      | `tests/test_digital_pipeline.py`  | Hermetic test builds a 3-col PDF with PyMuPDF, asserts round-trip.       |
| Fixture test        | `tests/test_digital_pipeline.py`  | Runs against `MonzoBus.pdf` if present (skipped otherwise).              |
| Lifecycle test      | `tests/test_job_lifecycle.py`     | Updated to assert `completed` + downloadable .xlsx.                      |

## Key algorithm — header-anchored column clustering

For each page:

1. Get word boxes (`pdfplumber.extract_words`).
2. Cluster words into rows by Y proximity (`ROW_BAND_TOLERANCE = 3 pt`).
3. Find the **header row**: first row whose horizontally-merged word groups
   number ≥ `MIN_HEADER_COLUMNS` (3). Merging adjacent words into groups
   means a label like `(GBP) Amount` counts as one column, not two.
4. Use the merged groups' centers as **column anchors**.
5. For every subsequent row, assign each word to the nearest anchor column
   and concatenate within a column.

This works because digital PDFs have pixel-perfect coordinates. Phase 4 will
generalize to OCR (noisy boxes, no reliable header).

## Empirical result on `MonzoBus.pdf`

```
detected: type=digital pages=24 with_text=24
digital extract: 23 raw tables across 24 pages
clean: 23 tables retained
timings_ms: detect=83, extract=11856, clean=2, export=90
```

- 23/24 pages produce a transaction table (page 0 is the cover/summary, correctly skipped — no header).
- Headers on every page: `Date | Description | (GBP) Amount | (GBP) Balance`.
- Numeric Amount values column-align across all 23 sheets.

### Known cosmetic issue

Multi-line transaction descriptions (e.g. `"E D OSTEOPATHY LTD (Faster Payments)" / "Reference: EXPENSES"` or wrapped merchant names) appear as **separate rows** in the .xlsx because the date/amount only renders on one of the visual rows. The data is all present and correctly columned; what's missing is row-merging logic that says "this row has no Date — fold it into the previous row's Description". That's deferred to **Phase 5** (cleaning).

## Architectural decisions

- **Custom geometric extractor over pdfplumber's `extract_tables()`.** With default settings, pdfplumber finds zero tables on the bank-statement fixture (it requires ruling lines). With text-strategy settings, it finds them but fragments columns badly. Building our own clusterer on top of `extract_words()` was simpler than tuning pdfplumber per fixture, and it foreshadows the Phase 4 algorithm.
- **Camelot deferred.** The spec calls for `camelot` as one of the digital tools. Empirically, our custom extractor handles the fixture better than Camelot's stream mode and is faster (no ghostscript spawn). Camelot remains in `requirements.txt` and `Dockerfile.worker` for ruled-line tables we may encounter — it'll be plugged in as a per-page fallback once a fixture demonstrates the need. This is a deliberate scope choice, not a forgotten requirement.
- **Detector returns `hybrid` for partially-text PDFs.** Phase 2 raises `NotImplementedError` for hybrid; Phase 6 will handle it by routing each page through the appropriate path.
- **Confidence is `1.0` for digital text.** It's only meaningful as an OCR signal (Phase 3+).

## What Phase 2 deliberately leaves unfinished

- Multi-line cell merging (deferred to Phase 5).
- Cross-page table merging — the bank statement is logically one table split across 23 pages but currently exports as 23 sheets (Phase 5).
- Column type inference (numeric, date, currency) — values are exported as strings (Phase 5).
- Camelot fallback path (Phase 5 if a fixture exposes the need).
- OCR pipeline (Phase 3).
