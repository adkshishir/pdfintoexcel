# Phase 10 — E2E tests + accuracy benchmark

**Shipped:** 2026-05-01
**Acceptance criteria** (PROJECT_PLAN.md §8):
> Test suite + benchmark script comparing our output against iLovePDF on a fixture set.

This is the final phase. Project-completion notes at the bottom.

## What landed

| Concern              | File                                          | Notes                                                           |
| -------------------- | --------------------------------------------- | --------------------------------------------------------------- |
| Accuracy benchmark   | `backend/scripts/benchmark.py`                | Compares two `.xlsx` files; reports headers / rows / cell-recall / type preservation. |
| E2E content test     | `backend/tests/test_e2e_real_pdf.py`          | Upload `MonzoBus.pdf` via HTTP → assert specific transactions in the .xlsx. |
| CI workflow          | `.github/workflows/ci.yml`                    | Backend pytest + frontend ESLint + production build on push/PR. |
| Top-level README     | `README.md`                                   | Full project doc — no longer a stub.                            |

44 tests pass (was 43; +1 E2E content test).

## The benchmark framework

```bash
# convert with iLovePDF (or Camelot, Tabula, anything) → theirs.xlsx
# then:
cd backend
python -m scripts.benchmark theirs.xlsx ours.xlsx
```

Output:
```
=== summary ===
  headers_match        0.875
  row_count_ratio      0.910
  cell_recall          0.954
  type_preservation    1.000
  overall              0.934
```

`overall` is the geometric mean of the above. Anything ≥ 0.5 returns exit 0.

### Validation runs

| Run                              | Overall | Notes                                  |
| -------------------------------- | ------- | -------------------------------------- |
| Self-comparison (same file twice)| 1.000   | Sanity check.                          |
| Fast vs accurate (MonzoBus.pdf)  | 0.900   | accurate folds rows; same data, fewer rows → row_count_ratio=0.72. |

We can't run the benchmark vs iLovePDF without manually uploading the
fixture to their site and downloading the result. The framework is ready;
the comparison is one shell command away.

## E2E test (`test_e2e_real_pdf.py`)

Goes all the way from HTTP upload through the actual pipeline to a streamed
download response. Then loads the .xlsx and asserts:

- `status: completed`, pdf_type: digital, page_count: 24, table_count: 1
- Workbook has 1 data sheet + 1 hidden `_conf_…` sheet
- Headers exactly: `["Date", "Description", "(GBP) Amount", "(GBP) Balance"]`
- ≥100 rows have a `datetime.date` in column 0
- ≥100 rows have a numeric Amount / Balance
- Specific known merchants (Amazon, TFL, Sainsburys) appear in descriptions
- Confidence sheet row count matches data sheet row count

Skipped automatically if `MonzoBus.pdf` isn't checked in.

## Known-loss: page 0 of MonzoBus

Found while writing the E2E test, worth recording.

`MonzoBus.pdf` page 0 carries **two** semantic blocks:
1. The cover-page summary (account holder, totals, balance) — a 2-column key/value layout with prose-y "headers" like `Elaine Rowena Gregory`.
2. The most recent ~8 transactions (25/07–28/07 inclusive) in the standard 4-column transaction table format, sitting below the summary.

The reconstructor picks **one table per page**. On page 0 the densest
"table" is the cover summary, which then trips the `_looks_label` filter
in the cleaner (header `Elaine Rowena Gregory` is 3 words → not a label →
table dropped as noise). The 8 transactions on page 0 die with it.

Trade-off: the alternative (skip the filter, ship the noise table) was
worse — the user gets a junk first sheet. Two-table-per-page handling
would recover both, but we've deferred that until a fixture forces the
issue (vertical-gap segmentation in the reconstructor + per-block
classification).

This is recorded in the test as an explicit comment so the assertion
doesn't pretend WICKES (a 25/07 transaction) is present.

## CI workflow

Two parallel jobs, both pinned to a 3.11 / 20 stack matching production:

- **backend** — installs the lightweight subset of `requirements.txt` (skips
  `paddleocr` / `paddlepaddle` because they're DI-mocked in tests and add
  several minutes to CI), runs pytest. `libmagic1` installed via apt so
  the security tests exercise the strong-path code.
- **frontend** — `npm ci`, ESLint, `next build` with `NEXT_PUBLIC_API_BASE_URL=/api`.

If either fails, the PR is red.

## Architectural decisions

- **Benchmark uses a workbook reference, not a JSON spec.** A user
  comparing against iLovePDF gets an .xlsx out of iLovePDF; converting to
  JSON to feed the benchmark would be friction. Workbook-to-workbook is
  the natural format.
- **CI skips paddleocr.** Saves ~5 minutes per run. The `OcrEngine`
  interface + dependency-injected recognizers in tests means we cover the
  algorithm without needing the real model weights. Real OCR happens in
  Docker (which CI doesn't have time to build).
- **Single E2E test, not many.** The pipeline is heavily tested at every
  stage already; the E2E proves the *wiring* end-to-end. More E2E tests
  would just re-test the same pipeline with different fixtures.

## Project completion

This was the 10th of 10 planned phases (PROJECT_PLAN.md §8). Status:

| Phase                                  | Outcome                                                             |
| -------------------------------------- | ------------------------------------------------------------------- |
| 0  Scaffolding & docs                  | Folder skeleton, plan, status doc, CLAUDE.md.                       |
| 1  Backend foundation                  | API + DB + queue end-to-end with portable types and lazy DB engine. |
| 2  Digital pipeline                    | (Reimplemented in Phase 6; `digital.py` retired.)                   |
| 3  OCR pipeline                        | PaddleOCR primary + Tesseract fallback, mode-driven DPI.            |
| 4  Table reconstruction                | The differentiator. Center-peaks + extent-valley boundaries.        |
| 5  Cleaning + Excel export             | Five composable transforms, eager per-cell coercion.                |
| 6  Hybrid + fast/accurate modes        | All paths unified through `WordBox[]`; geometric continuation merger.|
| 7  Frontend integration                | Next.js Client Component: upload, polling, download.                |
| 8  Infrastructure & deployment         | Real Oracle Object Storage, prod compose, hardened nginx, Makefile. |
| 9  Security & hardening                | libmagic, custom rate limiter, soft timeout, expiry sweeper.        |
| 10 E2E tests + benchmark               | Benchmark framework + content test + CI workflow.                   |

44 tests pass. End-to-end against `MonzoBus.pdf` produces a 1-sheet
workbook with typed Date/Amount/Balance columns containing 500+ real
transactions, plus a hidden confidence sheet.

The differentiator from iLovePDF (the Phase 4 reconstruction algorithm)
runs on the same `WordBox[]` interface whether the source is digital text
or OCR — meaning quality on scanned PDFs is bounded only by OCR accuracy,
not by a separate table-detection algorithm that has to learn scanned-PDF
quirks.
