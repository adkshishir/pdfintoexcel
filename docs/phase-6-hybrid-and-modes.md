# Phase 6 — Hybrid mode + fast/accurate modes

**Shipped:** 2026-05-01
**Acceptance criteria** (PROJECT_PLAN.md §8):
> Mode flag honored end-to-end; hybrid merger implemented.

## What landed

| Concern                  | File                                  | Notes                                                      |
| ------------------------ | ------------------------------------- | ---------------------------------------------------------- |
| Per-page text detection  | `app/pipeline/detector.py`            | `DetectionResult.text_page_indices` (was just a count).    |
| Digital-word extractor   | `app/pipeline/digital_words.py`       | NEW. pdfplumber → WordBox[]. Optional `page_indices` for hybrid. |
| Geometry on RawTable     | `app/pipeline/types.py`               | `RawTable.row_y_centers` carries per-row Y for cleaner.    |
| Geometry on CleanTable   | `app/pipeline/types.py`               | `CleanTable.row_gaps` (with +inf at page boundaries).      |
| Reconstructor            | `app/table/reconstructor.py`          | Populates `row_y_centers`.                                 |
| Geometry-aware merger    | `app/pipeline/cleaner.py`             | `_merge_continuations` now uses `row_gaps` + median-gap threshold. Safe to enable by default in accurate mode. |
| Stricter table filter    | `app/pipeline/cleaner.py`             | `_looks_label`: rejects 2-col tables whose headers are prose phrases (catches the cover-page noise the unified path now emits). |
| Unified orchestrator     | `app/pipeline/orchestrator.py`        | All three paths (digital/scanned/hybrid) share `WordBox[] → reconstruct → clean → export`. |
| Retired Phase 2 extractor| `app/pipeline/digital.py`             | **Deleted.** Reconstructor handles digital + OCR uniformly. |
| Tests                    | `tests/test_hybrid_and_modes.py`      | 3 new tests: hybrid routing, pure-digital no-OCR, accurate-vs-fast row count on real fixture. **33 tests pass total.** |

## The unification

Before Phase 6 the digital and scanned paths used different extractors:
- Digital → `digital.py` header-anchored clusterer → RawTable[]
- Scanned → OCR engine → WordBox[] → reconstructor → RawTable[]

Phase 6 routes both through the same pipeline:

```
                ┌─ digital pages ─► extract_digital_words ──┐
   detector ────┤                                           ├─► WordBox[]
                └─ scanned pages ─► extract_ocr ───────────┘
                                                              │
                                                              ▼
                                                       reconstruct_tables
                                                              │
                                                              ▼
                                                       clean_tables (with geometry)
                                                              │
                                                              ▼
                                                       export_excel
```

The reconstructor was already source-agnostic (Phase 4's design rationale —
digital and OCR boxes share the `WordBox` type). Phase 6 finishes the job:
hybrid mode just picks digital_words for some pages and OCR for the rest,
combines the WordBox lists, and feeds them to the same reconstructor.

This deletes ~150 lines of duplicate code (`digital.py`) and means there's
one algorithm to debug, not two.

## Mode flag end-to-end

| Component           | `fast` (default)            | `accurate`                              |
| ------------------- | --------------------------- | --------------------------------------- |
| OCR rendering DPI   | 200                         | 300                                     |
| Continuation merge  | off                         | **on** (now safe — uses geometry)       |

The mode flag is accepted at `POST /api/jobs`, persisted in `Job.mode`, and
threaded through `process_job → run_pipeline → extract_ocr / clean_tables`.

## Why continuation merging is now safe

Phase 5 shipped continuation merging *off* because text-only signal couldn't
distinguish "annotation continuation" from "next transaction's wrap" — both
look like an empty-Date row containing one Description cell.

Phase 6 carries `row_y_centers` through the reconstructor → `row_gaps`
through the cleaner. The merger now uses the gap as a discriminator:

```
median_gap = median of finite gaps within the table
threshold  = median_gap × 1.5
fold iff: anchor empty AND gap_to_previous ≤ threshold
```

In a bank statement: within-transaction wraps have gap ≈ 1× median;
between-transaction breaks have gap ≈ 2× median. The 1.5× cutoff cleanly
separates them. Empirical: `MonzoBus.pdf` accurate mode drops body rows
**798 → 550** (≈30% fewer) with no transactions merged incorrectly.

Cross-page boundaries get a sentinel `+inf` gap so cross-page rows never
fold — a wrapped description that crossed a page break would need a
different mechanism (currently appears as separate rows on each page).

## Empirical (`MonzoBus.pdf`)

```
mode=fast      : 798 body rows, ['date', 'text', 'text', 'number'] columns
mode=accurate  : 550 body rows, descriptions like
                  "STREET\TFL.GOV.UK/CP\SW1H 0TL GBR This relates to a previous transaction"
                  cleanly folded onto the right Date row.
```

Same pipeline, just the mode flag changes.

## Architectural decisions

- **Delete `digital.py`** rather than mark deprecated. Two extractors that
  must be kept in sync is a perpetual tax; the reconstructor produces
  equivalent output on the bank-statement fixture.
- **`row_gaps` lives on CleanTable, not as a side-channel.** Cleaning
  transforms (cross-page merge, continuation merge) need it; keeping it
  in the dataclass means transformations stay pure functions over
  CleanTable.
- **Sentinel `+inf` for cross-page boundaries** rather than tracking
  page-of-origin. `+inf > any threshold` so the existing fold check just
  works without special-casing.
- **Mode flag stays narrow.** Resisted the temptation to add Camelot
  fallback / dual-engine OCR / image preprocessing under accurate mode —
  current accurate mode is "more DPI + smarter cleaning". Each future
  toggle gets justified by a fixture that needs it.

## What Phase 6 deliberately leaves unfinished

- **Cross-page wrap merging.** A description wrapping across a page break
  doesn't fold (we drop a +inf gap there). Bank statements don't do this
  often; if a fixture needs it we'd need to detect "incomplete row at end
  of page" → "anchor-less row at start of next page" patterns.
- **Hybrid validation against a real mixed PDF.** Local hybrid test uses
  a synthetic 3-page PDF with mocked OCR. Real validation will happen
  once we have a digital-with-scanned-pages fixture.
- **Camelot fallback under accurate mode.** Listed in the spec; deferred
  until a fixture exposes a case the reconstructor mishandles.
