"""Geometric table reconstruction.

Implements the algorithm in `docs/table-reconstruction.md`. Single entry
point: `reconstruct_tables(boxes, page_count)`. Pure function over WordBox
input — no I/O, no PDF library dependencies, deterministic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from statistics import median

from app.pipeline.types import RawCell, RawTable, WordBox

log = logging.getLogger(__name__)


# ---- tunables (see docs/table-reconstruction.md §10) ----
ROW_TOLERANCE_FACTOR = 0.5   # baseline; see docs/table-reconstruction.md §10
MIN_COLUMN_WIDTH = 20.0          # points
HEADER_GAP_PT = 10.0             # points; horizontally-adjacent header words
MERGE_OVERFLOW_PT = 4.0          # points; below this is glyph-kerning noise
MERGE_MIN_CHARS = 6              # don't tag short tokens as merged-cell
MIN_TABLE_ROWS = 2
MIN_TABLE_COLS = 2
SECTION_BREAK_FACTOR = 3.0       # row-gap > 3 × median ⇒ section break
DENSITY_RESOLUTION = 1.0         # x-grid step (points)
GEOMETRIC_CONF_FLOOR = 0.2       # cell geometric confidence floor


# ---- internal types ----
@dataclass
class _Row:
    words: list[WordBox]
    mean_y: float
    top: float
    bot: float


# =====================================================================
# public entry
# =====================================================================
def reconstruct_tables(boxes: list[WordBox], page_count: int) -> list[RawTable]:
    by_page: dict[int, list[WordBox]] = {}
    for b in boxes:
        by_page.setdefault(b.page, []).append(b)

    tables: list[RawTable] = []
    for page_idx in range(page_count):
        page_boxes = by_page.get(page_idx, [])
        if not page_boxes:
            continue
        rows = _cluster_rows(page_boxes)
        segments = _split_row_segments(rows)
        for seg in segments:
            table = _reconstruct_segment(seg, page_idx)
            if table is not None:
                tables.append(table)
    return tables


# =====================================================================
# Multi-table-per-page: split at large vertical gaps, then reconstruct each band.
# =====================================================================
def _split_row_segments(rows: list[_Row]) -> list[list[_Row]]:
    if len(rows) < MIN_TABLE_ROWS:
        return []
    if len(rows) < 3:
        return [rows]

    gaps = [rows[i + 1].mean_y - rows[i].mean_y for i in range(len(rows) - 1)]
    med_gap = median(gaps) or 1.0
    threshold = med_gap * SECTION_BREAK_FACTOR

    raw_chunks: list[list[_Row]] = []
    start = 0
    for i, g in enumerate(gaps):
        if g > threshold:
            raw_chunks.append(rows[start : i + 1])
            start = i + 1
    raw_chunks.append(rows[start:])

    major = [c for c in raw_chunks if len(c) >= MIN_TABLE_ROWS]
    if len(major) >= 2:
        return major
    if len(raw_chunks) == 1:
        dense = _drop_section_breaks(rows)
        return [dense] if len(dense) >= MIN_TABLE_ROWS else []
    if major:
        return [max(major, key=len)]
    dense = _drop_section_breaks(rows)
    return [dense] if len(dense) >= MIN_TABLE_ROWS else []


# =====================================================================
# per-segment (one candidate table region)
# =====================================================================
def _reconstruct_segment(rows: list[_Row], page_idx: int) -> RawTable | None:
    if len(rows) < MIN_TABLE_ROWS:
        return None

    K = _column_count(rows)                                                  # [D]
    if K < MIN_TABLE_COLS:
        return None

    boundaries = _column_boundaries(rows, K)                                 # [E]
    if len(boundaries) != K + 1:
        # Couldn't find K-1 valleys → fall back to equal-width split.
        x0 = min(w.x for r in rows for w in r.words)
        x1 = max(w.x2 for r in rows for w in r.words)
        step = (x1 - x0) / K
        boundaries = [x0 + i * step for i in range(K + 1)]

    header_idx = _find_header_row(rows, K)                                   # [F]
    if header_idx is None:
        # No usable header — synthesize names + treat all rows as body.
        synthetic_headers = [f"col_{i+1}" for i in range(K)]
        body_rows = rows
        header_cells = [
            RawCell(row=0, col=c, text=synthetic_headers[c]) for c in range(K)
        ]
    else:
        header_cells = _row_to_cells(rows[header_idx], 0, boundaries, K, is_header=True)
        body_rows = rows[header_idx + 1:]

    cells: list[RawCell] = list(header_cells)
    for body_idx, row in enumerate(body_rows, start=1):
        cells.extend(_row_to_cells(row, body_idx, boundaries, K, is_header=False))

    if not cells:
        return None

    n_rows = max(c.row for c in cells) + 1
    bbox = (
        boundaries[0],
        min(r.top for r in rows),
        boundaries[-1],
        max(r.bot for r in rows),
    )

    # row_y_centers parallel to row indices (header is row 0, body 1..N-1).
    # Header is rows[header_idx] if known; body rows are rows[header_idx+1:].
    if header_idx is None:
        ordered_rows = rows
    else:
        ordered_rows = [rows[header_idx]] + list(rows[header_idx + 1:])
    row_y_centers = [r.mean_y for r in ordered_rows[: n_rows]]
    # Pad in case rows < n_rows (shouldn't happen but defensive).
    while len(row_y_centers) < n_rows:
        row_y_centers.append(row_y_centers[-1] if row_y_centers else 0.0)

    return RawTable(
        page=page_idx, bbox=bbox, cells=cells,
        n_rows=n_rows, n_cols=K, row_y_centers=row_y_centers,
    )


# =====================================================================
# [B] row clustering
# =====================================================================
def _cluster_rows(words: list[WordBox]) -> list[_Row]:
    if not words:
        return []
    h_med = median(w.h for w in words) or 1.0
    strict_tol = max(2.0, h_med * ROW_TOLERANCE_FACTOR)
    # Words in non-overlapping X regions (different columns) tolerate more Y
    # spread: a date cell can be vertically centred while the description
    # beside it wraps to multiple lines, placing the two tokens up to 1.5
    # line-heights apart even though they are in the same logical row.
    inter_col_tol = max(2.0, h_med * 1.5)

    by_y = sorted(words, key=lambda w: ((w.y + w.y2) / 2.0, w.x))
    rows: list[_Row] = []
    cur: list[WordBox] = [by_y[0]]
    cur_mean_y = (by_y[0].y + by_y[0].y2) / 2.0

    for w in by_y[1:]:
        cy = (w.y + w.y2) / 2.0

        # Fast-path: word shares the same visual line as an existing row word
        # (OCR coords are imprecise; use 10 % of line-height as "same line").
        if any(abs(cy - (u.y + u.y2) / 2.0) <= h_med * 0.1 for u in cur):
            cur.append(w)
            cur_mean_y = sum((u.y + u.y2) / 2.0 for u in cur) / len(cur)
            continue

        # Use a looser tolerance for words in non-overlapping X regions.
        x_overlaps = any(w.x < u.x2 and u.x < w.x2 for u in cur)
        tol = strict_tol if x_overlaps else inter_col_tol

        if abs(cy - cur_mean_y) <= tol:
            cur.append(w)
            cur_mean_y = sum((u.y + u.y2) / 2.0 for u in cur) / len(cur)
        else:
            rows.append(_finalize_row(cur))
            cur = [w]
            cur_mean_y = cy

    rows.append(_finalize_row(cur))
    return rows


def _finalize_row(words: list[WordBox]) -> _Row:
    words.sort(key=lambda w: w.x)
    return _Row(
        words=words,
        mean_y=sum((w.y + w.y2) / 2.0 for w in words) / len(words),
        top=min(w.y for w in words),
        bot=max(w.y2 for w in words),
    )


# =====================================================================
# [C] table region — drop section-break gaps
# =====================================================================
def _drop_section_breaks(rows: list[_Row]) -> list[_Row]:
    if len(rows) < 3:
        return rows
    gaps = [rows[i + 1].mean_y - rows[i].mean_y for i in range(len(rows) - 1)]
    med_gap = median(gaps) or 1.0
    threshold = med_gap * SECTION_BREAK_FACTOR

    # Find the longest run of consecutive rows with gap ≤ threshold.
    best_start, best_end = 0, 0
    cur_start = 0
    for i, g in enumerate(gaps):
        if g > threshold:
            if i - cur_start > best_end - best_start:
                best_start, best_end = cur_start, i
            cur_start = i + 1
    if (len(rows) - 1) - cur_start > best_end - best_start:
        best_start, best_end = cur_start, len(rows) - 1
    return rows[best_start: best_end + 1]


# =====================================================================
# [D] column count K
# =====================================================================
def _column_count(rows: list[_Row]) -> int:
    counts: list[int] = []
    for r in rows:
        groups = _merge_horizontally(r.words, gap=HEADER_GAP_PT)
        counts.append(len(groups))
    if not counts:
        return 0
    # Mode; tiebreak = largest. Drop singletons (decoration rows).
    freq: dict[int, int] = {}
    for c in counts:
        if c >= MIN_TABLE_COLS:
            freq[c] = freq.get(c, 0) + 1
    if not freq:
        return 0
    return max(freq, key=lambda k: (freq[k], k))


# =====================================================================
# [E] column boundaries via vertical density valleys
# =====================================================================
def _column_boundaries(rows: list[_Row], K: int) -> list[float]:
    """Find K-1 internal column boundaries from word-CENTER clustering.

    Why centers, not extents:
      A word's extent (x..x2) bleeds across visual gaps — e.g. a long
      "(GBP) Amount" header word fills part of what *would* be the gap
      between Description and Amount in the body. So an extent-density
      profile may have NO zero-density bins even when the table is
      visually well-separated.

      Word *centers* cluster tightly at column centers (left-aligned columns
      → centers near the column's left edge + word-half-width; right-aligned
      → centers near the right edge − word-half-width; either way each
      column produces a tight cluster of centers). Boundaries are the
      midpoints between consecutive peaks.

    Algorithm:
      1. Project each word's center to a 1-D array.
      2. Smooth with a triangular kernel of width MIN_COLUMN_WIDTH.
      3. Find the K tallest peaks that are also ≥ MIN_COLUMN_WIDTH apart.
      4. Boundaries = midpoints between consecutive peaks (+ table edges).
    """
    if K <= 0:
        return []
    all_words = [w for r in rows for w in r.words]
    if not all_words:
        return []
    x0 = min(w.x for w in all_words)
    x1 = max(w.x2 for w in all_words)
    if x1 - x0 < MIN_COLUMN_WIDTH:
        return [x0, x1]

    n_bins = max(1, int((x1 - x0) / DENSITY_RESOLUTION) + 1)
    centers = [0.0] * n_bins
    for w in all_words:
        cx = (w.x + w.x2) / 2.0
        b = max(0, min(n_bins - 1, int((cx - x0) / DENSITY_RESOLUTION)))
        centers[b] += 1.0

    # Smooth with a triangular kernel of half-width = MIN_COLUMN_WIDTH/2.
    half = max(1, int(MIN_COLUMN_WIDTH / DENSITY_RESOLUTION / 2))
    smoothed = [0.0] * n_bins
    for i in range(n_bins):
        s = 0.0
        for j in range(-half, half + 1):
            k = i + j
            if 0 <= k < n_bins:
                weight = 1.0 - abs(j) / (half + 1)
                s += centers[k] * weight
        smoothed[i] = s

    # Find local maxima (peaks). A bin is a peak if its smoothed value is
    # ≥ all smoothed values in [i-half, i+half], and > 0.
    peaks: list[tuple[float, int]] = []
    for i in range(n_bins):
        v = smoothed[i]
        if v <= 0:
            continue
        lo = max(0, i - half)
        hi = min(n_bins, i + half + 1)
        if v >= max(smoothed[lo:hi]):
            peaks.append((v, i))

    # Greedy non-max suppression: pick K tallest peaks, ≥ MIN_COLUMN_WIDTH apart.
    peaks.sort(key=lambda vi: -vi[0])
    min_bin_gap = max(1, int(MIN_COLUMN_WIDTH / DENSITY_RESOLUTION))
    chosen_bins: list[int] = []
    for _, b in peaks:
        if any(abs(b - c) < min_bin_gap for c in chosen_bins):
            continue
        chosen_bins.append(b)
        if len(chosen_bins) >= K:
            break
    chosen_bins.sort()

    if len(chosen_bins) < 2:
        # Only one peak — fall back to equal-width split.
        step = (x1 - x0) / K
        return [x0 + i * step for i in range(K + 1)]

    # Build extent density too — boundary location uses extent valleys, not
    # center peaks. (Centers tell us how many columns and where they are;
    # extent valleys tell us where the visual gaps between them are.)
    extent = [0] * n_bins
    for w in all_words:
        lo = max(0, int((w.x - x0) / DENSITY_RESOLUTION))
        hi = min(n_bins - 1, int((w.x2 - x0) / DENSITY_RESOLUTION))
        for i in range(lo, hi + 1):
            extent[i] += 1

    peak_bins = sorted(chosen_bins)
    boundaries = [x0]
    for i in range(len(peak_bins) - 1):
        a = peak_bins[i] + half        # don't search inside the peak's own column
        b = peak_bins[i + 1] - half
        if b <= a:
            # Peaks too close to have a proper inter-region; fall back to midpoint.
            boundaries.append(x0 + ((peak_bins[i] + peak_bins[i + 1]) / 2.0) * DENSITY_RESOLUTION)
            continue
        # Pick the lowest-extent bin in [a, b]. Tiebreak: bin closest to midpoint
        # (avoids weird placements when there's a wide flat valley).
        mid = (peak_bins[i] + peak_bins[i + 1]) // 2
        best_bin = min(range(a, b + 1), key=lambda k: (extent[k], abs(k - mid)))
        boundaries.append(x0 + best_bin * DENSITY_RESOLUTION)
    boundaries.append(x1)

    # Top up to K+1 boundaries if peak detection found fewer than K columns.
    while len(boundaries) < K + 1:
        gaps = [(boundaries[i + 1] - boundaries[i], i) for i in range(len(boundaries) - 1)]
        _, idx = max(gaps)
        mid = (boundaries[idx] + boundaries[idx + 1]) / 2.0
        boundaries.insert(idx + 1, mid)

    return boundaries


# =====================================================================
# [F] header row pick
# =====================================================================
def _find_header_row(rows: list[_Row], K: int) -> int | None:
    for idx, r in enumerate(rows):
        groups = _merge_horizontally(r.words, gap=HEADER_GAP_PT)
        if len(groups) == K:
            return idx
    # Fallback: first row with K-1 groups (one missing column).
    for idx, r in enumerate(rows):
        groups = _merge_horizontally(r.words, gap=HEADER_GAP_PT)
        if len(groups) == max(K - 1, MIN_TABLE_COLS):
            return idx
    return None


# =====================================================================
# [G] cell assignment + merged cells
# =====================================================================
def _row_to_cells(
    row: _Row, row_idx: int, boundaries: list[float], K: int, *, is_header: bool
) -> list[RawCell]:
    """Bucket words into columns. For headers, merge adjacent words within
    HEADER_GAP_PT into one cell label."""
    if not row.words:
        return []

    if is_header:
        # Group adjacent header words first; assign each *group* to a column.
        groups = _merge_horizontally(row.words, gap=HEADER_GAP_PT)
        cells: list[RawCell] = []
        for g in groups:
            cx = (g[0].x + g[-1].x2) / 2.0
            col = _bucket(cx, boundaries, K)
            text = " ".join(w.text for w in sorted(g, key=lambda w: w.x))
            conf = sum(w.confidence for w in g) / len(g)
            cells.append(RawCell(row=row_idx, col=col, text=text, confidence=conf))
        return _merge_same_col(cells)

    # Body row: assign each word to a column.
    by_col: dict[int, list[WordBox]] = {}
    by_col_span: dict[int, int] = {}
    for w in row.words:
        cx = (w.x + w.x2) / 2.0
        col = _bucket(cx, boundaries, K)
        # Merged-cell detection: word straddles a boundary by > overflow.
        span = _merged_span(w, boundaries, col, K)
        by_col.setdefault(col, []).append(w)
        by_col_span[col] = max(by_col_span.get(col, 1), span)

    cells: list[RawCell] = []
    for col, words in sorted(by_col.items()):
        words.sort(key=lambda w: w.x)
        text = " ".join(w.text for w in words)
        ocr_conf = sum(w.confidence for w in words) / len(words)
        # Geometric confidence: how centered the words are in their column.
        col_left = boundaries[col]
        col_right = boundaries[col + 1] if col + 1 < len(boundaries) else col_left
        col_center = (col_left + col_right) / 2.0
        col_width = max(1.0, col_right - col_left)
        offsets = [abs((w.x + w.x2) / 2.0 - col_center) / col_width for w in words]
        geo = max(GEOMETRIC_CONF_FLOOR, 1.0 - (sum(offsets) / len(offsets)))
        cells.append(RawCell(
            row=row_idx, col=col, text=text,
            col_span=by_col_span.get(col, 1),
            confidence=ocr_conf * geo,
        ))
    return cells


def _merge_same_col(cells: list[RawCell]) -> list[RawCell]:
    """If two header groups bucket into the same column, concatenate."""
    out: dict[int, RawCell] = {}
    for c in cells:
        if c.col in out:
            prev = out[c.col]
            prev.text = (prev.text + " " + c.text).strip()
            prev.confidence = (prev.confidence + c.confidence) / 2.0
        else:
            out[c.col] = c
    return [out[k] for k in sorted(out)]


def _bucket(cx: float, boundaries: list[float], K: int) -> int:
    """Return column index for x-center cx given K+1 boundaries."""
    for i in range(K):
        if boundaries[i] <= cx < boundaries[i + 1]:
            return i
    if cx < boundaries[0]:
        return 0
    return K - 1


def _merged_span(w: WordBox, boundaries: list[float], col: int, K: int) -> int:
    """Number of columns this word straddles. ≥1."""
    if len(w.text) < MERGE_MIN_CHARS:
        return 1
    span = 1
    # Count boundaries strictly inside (x0, x2) by more than overflow.
    for b_idx in range(1, len(boundaries) - 1):
        b = boundaries[b_idx]
        if w.x + MERGE_OVERFLOW_PT < b < w.x2 - MERGE_OVERFLOW_PT:
            span += 1
    return min(span, K - col)


# =====================================================================
# rowspan post-pass (geometry path only)
# =====================================================================
def _fill_rowspans(
    cells: list[RawCell],
    rows: list[_Row],
    n_rows: int,
    n_cols: int,
) -> list[RawCell]:
    """Propagate content into empty cells that sit directly below a filled cell
    in the same column, when the two rows are close enough to be part of the
    same logical cell (rowspan).

    Only fills when:
      - The cell is genuinely absent from the grid (OCR found no word there).
      - The row gap to the previous row is ≤ 2.5× the previous row's height
        (so we don't bleed across table-section breaks).
      - At least one OTHER cell in the current row has content (so we don't
        fill into blank separator rows).
    """
    grid: dict[tuple[int, int], RawCell] = {(c.row, c.col): c for c in cells}

    # Pre-compute which rows have any content, for the "other cell" guard.
    rows_with_content: set[int] = set()
    for c in cells:
        if c.text.strip():
            rows_with_content.add(c.row)

    extra: list[RawCell] = []
    for r in range(1, n_rows):
        # Guard: skip rows with no content at all (blank separators).
        if r not in rows_with_content:
            continue

        # Guard: only fill when rows are spatially close.
        if r < len(rows) and r - 1 < len(rows):
            prev_row = rows[r - 1]
            row_height = max(1.0, prev_row.bot - prev_row.top)
            row_gap = rows[r].mean_y - prev_row.mean_y
            if row_gap > row_height * 2.5:
                continue
        else:
            continue

        for col in range(n_cols):
            if (r, col) in grid:
                continue
            prev_cell = grid.get((r - 1, col))
            if prev_cell is None or not prev_cell.text.strip():
                continue
            fill = RawCell(
                row=r,
                col=col,
                text=prev_cell.text,
                row_span=1,
                confidence=prev_cell.confidence * 0.85,
            )
            extra.append(fill)
            grid[(r, col)] = fill

    return cells + extra


# =====================================================================
# helpers
# =====================================================================
def _merge_horizontally(words: list[WordBox], *, gap: float) -> list[list[WordBox]]:
    """Group L→R-sorted words whose horizontal gap ≤ `gap`."""
    if not words:
        return []
    ordered = sorted(words, key=lambda w: w.x)
    groups: list[list[WordBox]] = [[ordered[0]]]
    for w in ordered[1:]:
        last = groups[-1][-1]
        if w.x - last.x2 <= gap:
            groups[-1].append(w)
        else:
            groups.append([w])
    return groups
