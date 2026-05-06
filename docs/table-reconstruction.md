# Table reconstruction — algorithm

> Phase 4's deliverable. Input: `WordBox[]` (text + axis-aligned bbox + page +
> OCR confidence). Output: `RawTable[]` (cells with row/col + spans + per-cell
> confidence). The same algorithm runs whether boxes came from OCR or from
> digital text extraction — they share the `WordBox` type.

## Why this matters

The competitor (iLovePDF, Camelot's stream mode) treats column detection as
"find vertical gaps in word density and split there". That works on clean
digital tables and breaks on:

- **Skewed scans** — the median Y-line of "row 5" is 4 pt off "row 4", and the
  band-cluster splits one row into two.
- **Tables without ruling lines** — no anchor for column boundaries; the
  vertical-projection valleys move with each row.
- **Right-aligned numeric columns** — word x-centers vary widely within a
  column because numbers are different lengths.
- **Wrapped cells** — a long description wraps to a second visual line and
  pollutes the row count.

We address each of these explicitly. Sections 3–7 below describe the steps;
section 8 is the empirical evaluation plan.

---

## 1. Coordinate system + assumptions

- Coordinates are PDF user space (top-left origin, points). Stage 2b
  (`ocr_pipeline.py`) converts pixel coords back to points before this stage
  ever sees them.
- One _table_ per page in v1. Multi-table pages are deferred — when needed
  we'll segment by detecting large vertical gaps between row clusters.
- Words are atomic. We never split a `WordBox`; we only group them into cells.

## 2. Pipeline

```
WordBox[]
   │
   ▼
[A] per-page partition
   │
   ▼  (per page)
[B] row clustering   ──► row-bands
   │
   ▼
[C] table region detection (drop noise rows)
   │
   ▼
[D] column count K  via mode-of-row-widths
   │
   ▼
[E] column boundaries  via vertical density valleys
   │
   ▼
[F] header row pick   (top-most row with K filled columns)
   │
   ▼
[G] cell assignment + merged-cell detection
   │
   ▼
[H] per-cell confidence
   │
   ▼
RawTable
```

Each step has a single, testable responsibility.

---

## 3. Row clustering [B]

Naive "cluster within ±N points" breaks on skew and font variation. We use a
**band-based clusterer** where the band scales with the local median word
height:

1. Sort words by Y-center ascending.
2. Compute median height `H_med` across all words on the page.
3. Set band tolerance `T = max(2.0, H_med * ROW_TOLERANCE_FACTOR)`. Default
   factor: `0.5`.
4. Walk sorted words. Maintain `current_row.mean_y`. If next word's Y-center
   is within `T` of `current_row.mean_y`, append; else start a new row.
5. After clustering, sort words within each row left-to-right by `x0`.

**Why mean_y, not first-word_y?** Otherwise a slightly-low first word drags
the band down and grabs noise from the row below.

## 4. Table region detection [C]

Ignore rows that are clearly _not_ part of a table:

- Rows with a single word that's short and far above/below the dense region.
- Rows whose Y-spacing to the next row is `> 3 × median_row_spacing` —
  treated as a section break, not a table continuation.

After dropping noise rows, the remaining contiguous block is the table region.

## 5. Column count K [D]

Look at the count of words per row across the table region. Take the **mode**.
Tiebreaker: the larger value (we'd rather over-segment columns than collapse
two columns into one — Phase 5's cleaner can detect and merge runaway columns
later via consistent emptiness, but it can't un-merge collapsed columns).

This is robust to:

- Header row having extra "(GBP)" tokens (won't match the body's mode).
- Footer rows (page numbers, totals) with 1–2 words.
- Random row with an extra annotation.

## 6. Column boundaries [E]

This is the core insight that beats Camelot's stream mode.

Build the **vertical density profile**: for each x in `[0, page_width]`,
count the number of words whose `[x0, x1]` interval covers x. We build this
at 1-point resolution (cheap — pages are < 1000 pt wide).

Now find K-1 boundaries:

1. The profile's "table region" runs from `min(x0)` to `max(x1)` across all
   words.
2. Within that region, find local minima (valleys) in the density profile.
3. Among those valleys, pick the K-1 with the **lowest density** that are
   also **at least `MIN_COLUMN_WIDTH` apart** (default 20 pt).

Why this is robust:

- Skewed rows still contribute to the density profile correctly because we
  project across all rows.
- Right-aligned numeric columns produce density that _peaks_ on the right
  side of each column and _drops to zero_ in the gap between columns — the
  valleys are unambiguous.
- A few missing words in some rows don't move the valleys (each valley has
  contributions from many rows).

## 7. Header row [F]

The header is the **first row whose number of horizontally-merged groups
matches K**. Horizontal merging uses gap ≤ `HEADER_GAP_PT` (default 10 pt)
so labels like "(GBP) Amount" count as one column.

If no row matches K exactly, fall back to "first row with ≥ K-1 groups" and
add a synthetic empty header for the missing column.

If still no plausible header, generate `col_1, col_2, ...` headers and treat
the entire region as body. We never refuse to emit a table just because the
header is unclear — better to give the user a structured Excel they can
relabel than to skip the page.

## 8. Cell assignment + merged cells [G]

For each body row:

1. Bucket each word into the column whose `[boundary_left, boundary_right]`
   interval contains the word's center.
2. **Merged cell detection**: if a single word's `[x0, x1]` straddles a column
   boundary by more than `MERGE_OVERFLOW_PT` (default 4 pt), and that word's
   text is _longer_ than `MERGE_MIN_CHARS` (default 6), tag it as `col_span`
   = (number of straddled columns).

We don't handle vertical spans (`row_span > 1`) in v1 — they're rare in
financial / statement tables and require image-feature analysis (ruling
lines) that we don't have in scope.

## 9. Per-cell confidence [H]

```
cell_conf = ocr_conf * geometric_conf
ocr_conf  = mean(WordBox.confidence for words in cell)
geometric_conf = clip(1.0 - mean_normalized_offset, 0.2, 1.0)
```

Where `mean_normalized_offset` is the mean distance from each word's center
to its assigned column's center, divided by the column's width. A word
sitting dead-center in its column scores 1.0; a word at the column boundary
scores 0.5; a wildly out-of-place word scores 0.2 (the floor).

These scores will surface in Phase 5's hidden `_confidence` sheet and are
already plumbed through `RawCell.confidence`.

---

## 10. Tunable constants

All in one block at the top of `app/table/reconstructor.py`:

| Constant               | Default | Why this default                                                      |
| ---------------------- | ------- | --------------------------------------------------------------------- |
| `ROW_TOLERANCE_FACTOR` | 0.5     | Half a row-height — empirically separates rows even on 2-degree skew. |
| `MIN_COLUMN_WIDTH`     | 20 pt   | Below this, columns are visual artifacts (sub-letter spacing).        |
| `HEADER_GAP_PT`        | 10 pt   | Two header words within 10 pt are the same label ("(GBP) Amount").    |
| `MERGE_OVERFLOW_PT`    | 4 pt    | Smaller than glyph kerning noise.                                     |
| `MERGE_MIN_CHARS`      | 6       | Filters out punctuation that happens to overflow.                     |
| `MIN_TABLE_ROWS`       | 2       | A header alone isn't a table.                                         |
| `MIN_TABLE_COLS`       | 2       | A single column is a list, not a table.                               |
| `SECTION_BREAK_FACTOR` | 3.0     | Row gap > 3× median = section break, not table continuation.          |

---

## 11. Why the digital path also benefits

Phase 2's `digital.py` uses a header-anchored clusterer. That works because
digital PDFs have one obvious header. The reconstruction algorithm here is
strictly more general: header-anchored is one of its sub-cases (when the
density-valley boundaries happen to coincide with header word centers).

For Phase 4 we keep the digital path as-is to avoid regressing the bank
statement. After Phase 5 stabilizes, Phase 6 will swap the digital path to
the unified reconstructor and the digital-specific clusterer goes away.

---

## 12. Validation plan

1. **Unit tests** (hermetic, synthetic WordBox lists):
   - Row clustering on noisy Y-coords
   - K detection on a row-set with header noise
   - Column boundaries on aligned vs. skewed inputs
   - Merged cell detection
   - Confidence scoring monotonicity

2. **Integration test** against `MonzoBus.scanned.pdf` (inside Docker, where
   OCR is available). Compare reconstructed `.xlsx` against the Phase 2 ground
   truth from `MonzoBus.pdf`. Pass criteria:
   - Same number of detected sheets (23, plus or minus 1 for cover page)
   - Headers ≥ 80% string-match on `Date | Description | (GBP) Amount | (GBP) Balance`
   - Numeric Amount column: > 90% of values parse as floats and match the
     digital extraction (string equal after normalization)
   - Date column: > 90% match `DD/MM/YYYY`

3. **CLI dry-run** (`scripts/dry_run_reconstruction.py`) that pipes
   pdfplumber word boxes through the reconstructor (no OCR needed) so we can
   iterate on the algorithm locally.

---

## 13. Out of scope (for v1)

- Vertical row spans (`row_span > 1`).
- Multi-table-per-page (will revisit when a fixture demands it).
- Image-feature ruling-line detection. Useful for bank statements with
  faint horizontal lines, but adds an OpenCV dependency to a hot path.
  Phase 5 candidate.
- Deskewing prior to OCR. Phase 5 / preprocessing.
- Multi-line cell merging. Phase 5 (cleaning).
