# Phase 5 — Cleaning + Excel export

**Shipped:** 2026-05-01
**Acceptance criteria** (PROJECT_PLAN.md §8):
> Header detection, type inference, multi-sheet workbook, confidence sheet.

## What landed

| Concern                  | File                              | Notes                                                                         |
| ------------------------ | --------------------------------- | ----------------------------------------------------------------------------- |
| `CleanTable.column_types`| `app/pipeline/types.py`           | New field — list of `text`/`number`/`date` per header.                       |
| Pipeline of cleaners     | `app/pipeline/cleaner.py`         | Five composable transforms. `clean_tables()` orchestrates.                   |
| Eager cell coercion      | `app/pipeline/exporter.py`        | Each cell self-classifies (number → number, date → date) regardless of column-level inference. |
| Hidden `_confidence` sheet | `app/pipeline/exporter.py`      | Sibling sheet per data sheet, hidden by default, conditional-formatted.       |
| Tests                    | `tests/test_cleaner.py`           | 10 new unit tests covering each transform. 30 tests total pass.              |

## Five cleaners (composed in `clean_tables`)

```
RawTable[]
   │
   ▼
[1] _raw_to_clean        — RawCells → grid → CleanTable. Adds default headers
                            (col_1, col_2, …) when reconstruction returned none.
   │
   ▼
[2] _looks_like_table    — drop noise. A real table has at least one column
                            consistently filled (≥70%) or empty (≤10%).
                            Layout coincidences sit in the middling 30–70% band
                            for every column.
   │
   ▼
[3] _merge_consecutive   — fold tables sharing identical (normalized) headers
                            into one sheet. Sheet name suffixed with "(merged)".
   │
   ▼
[4] _merge_continuations — OPT-IN. Folds rows whose anchor column is empty into
                            the previous row. Off by default — see §"Why
                            continuation merging is off" below.
   │
   ▼
[5] _infer_column_types  — for each column, classify as date/number/text by
                            checking ≥70% of non-empty values match the pattern.
                            Result lives in CleanTable.column_types.
```

## Eager per-cell coercion

`column_types` is *advisory*. The exporter tries to coerce every cell
individually:
1. Strip currency prefix + commas/whitespace; if result matches `^[+-]?\d+(\.\d+)?$`, write as int/float.
2. If matches `dd/mm/yyyy` family, parse and write as `datetime.date`.
3. Else write as text.

This handles imperfect column boundaries gracefully: a mostly-numeric Amount
column with the occasional spurious text token (e.g., `"Payments)"` bleeding
in from a wrapped Description) still has its numeric cells typed as numbers
in Excel — only the rare polluting cell stays as text. Number/date display
formatting (`#,##0.00`, `dd/mm/yyyy`) is applied at the column level so the
common case looks right.

## Why continuation merging is off by default

The bank-statement layout puts each transaction's metadata across **3 visual
rows**:

```
y=top      <merchant name>                        ← only Description filled
y=middle   <Date>      <Amount>      <Balance>    ← only Date/Amount/Balance filled
y=bottom   Reference: <ref>                       ← only Description filled
```

The naive merger ("any row with empty Date folds into the previous row")
sees row Y=top of transaction N+1 right after row Y=bottom of transaction N
and folds them — concatenating two transactions' descriptions. A text-only
signal can't distinguish "annotation continuation" from "next transaction's
wrap"; we'd need geometric info (Y-distance to previous row) which is lost
once we cross from RawTable into CleanTable.

The transform is implemented + tested (`tests/test_cleaner.py::test_continuation_merging_on_folds_correctly`),
and toggleable via `clean_tables(raw, merge_continuations=True)`. Phase 6
will likely re-enable it after the orchestrator is changed to pass
geometric hints through to the cleaner.

## Hidden `_confidence` sheet

For every user-facing sheet "X", the workbook now has a sibling sheet
"_conf_X" with the same shape. Cells contain per-cell confidence (0.0–1.0),
with conditional formatting:
- **Red** (< 0.5): low confidence — likely OCR error or column misassignment
- **Yellow** (0.5–0.8): moderate
- **No fill** (> 0.8): high

Hidden by default. To inspect: in Excel, Format → Sheet → Unhide. Phase 7's
frontend will surface this as cell highlighting in the preview.

## Empirical result on `MonzoBus.pdf`

```
Before Phase 5 — 23 sheets ('Page 1' … 'Page 23'), all values stored as text.

After Phase 5  — 1 sheet ('Page 1 (merged)') + 1 hidden '_conf_…' sheet.
                 798 body rows.
                 Date column: real datetime values (filterable, sortable).
                 Amount column: real numbers (sumable). 700+ numeric cells.
                 Balance column: real numbers.
                 Cover page (page 0) noise: dropped by _looks_like_table.
                 column_types: ['date', 'text', 'text', 'number']
                  (Amount inferred 'text' at column level due to bleed-over
                   from Description wraps; eager per-cell coercion still
                   types the actual numeric cells correctly.)
```

The `.xlsx` is now a usable bank-statement spreadsheet — open it in Excel,
sum the Amount column, group by month with a pivot table, etc.

## Architectural decisions

- **Five separate transforms, not one big function.** Each has one
  responsibility and is independently testable. Ordering matters
  (cross-page merge before continuation merge so wraps across page
  boundaries are handled correctly).
- **`column_types` is inferred but advisory.** Exporter trusts cells, not
  the column. Fixes the "1 polluting word kills the whole column's
  type" failure mode.
- **Continuation merging deferred.** Better to ship a slightly-noisy but
  *correct* output than a clean-looking output that silently merged two
  transactions. Phase 6 has the geometric info to do this properly.
- **`_confidence` sheet hidden, not omitted.** Visible sheets would
  confuse non-technical users; omitting kills the QA story. Hidden +
  conditional-formatted is the compromise.

## What Phase 5 deliberately leaves unfinished

- **Continuation merging in the default path.** Needs Phase 6's geometric
  hint pass-through.
- **Multi-line cell *display*.** When a Description wraps across visual
  rows, cells show as separate Excel rows. The data is correct but the UX
  is noisier than the original PDF. Same root cause as continuation merging.
- **OCR-specific cleaning** (deskew, denoise) — Phase 6 / Phase 9.
- **Cell-level conditional formatting** on the data sheet (not just the
  hidden confidence sheet). Would need to read the confidence values back
  in the exporter to apply per-cell fill colors. Phase 7 (frontend
  preview) is the better place for this.
