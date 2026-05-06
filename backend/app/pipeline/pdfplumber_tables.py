"""Tier-1 table extraction for digital PDFs using pdfplumber's native
ruling-line detection.

Returns RawTable[] only for tables found via actual drawn borders/rectangles
in the PDF. Returns [] for pages with text-only tables so the geometry
reconstructor handles them.

Rowspan handling: pdfplumber returns None for cells that are empty or merged
from above. We forward-fill column-by-column so spanning content is visible
in every row it occupies (better for data analysis than blank cells).
"""
from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

import pdfplumber

from app.pipeline.types import RawCell, RawTable

log = logging.getLogger(__name__)

_LINES_SETTINGS: dict[str, Any] = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "snap_tolerance": 3,
    "snap_x_tolerance": 3,
    "snap_y_tolerance": 3,
    "join_tolerance": 3,
    "join_x_tolerance": 3,
    "join_y_tolerance": 3,
    "edge_min_length": 3,
    "min_words_vertical": 3,
    "min_words_horizontal": 1,
    "intersection_tolerance": 3,
    "intersection_x_tolerance": 3,
    "intersection_y_tolerance": 3,
    "text_tolerance": 3,
    "text_x_tolerance": 3,
    "text_y_tolerance": 3,
}


def extract_pdfplumber_tables(pdf_path: Path) -> list[RawTable]:
    """Extract tables using pdfplumber's line-detection engine.

    Only returns tables found via ruling lines/rectangles. Pages with
    whitespace-only tables return nothing so the geometry reconstructor
    handles them.
    """
    tables: list[RawTable] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                try:
                    found = page.find_tables(_LINES_SETTINGS)
                except Exception as exc:
                    log.debug("line-detect failed page %d: %s", page_idx, exc)
                    continue
                for tbl in found:
                    raw = _table_to_raw(tbl, page_idx)
                    if raw is not None:
                        tables.append(raw)
    except Exception as exc:
        log.warning("pdfplumber tier-1 extraction failed: %s", exc)
        return []

    log.info("pdfplumber tier-1: %d ruled tables", len(tables))
    return tables


def _table_to_raw(tbl: Any, page_idx: int) -> RawTable | None:
    extracted = tbl.extract()
    if not extracted or len(extracted) < 2:
        return None

    n_rows = len(extracted)
    n_cols = max((len(r) for r in extracted), default=0)
    if n_cols < 2:
        return None

    # Detect which None cells are genuine rowspans (vs genuinely empty cells).
    # We forward-fill only in columns where the None run immediately follows a
    # non-empty value AND the column has at least one other None-after-value
    # pattern — i.e., the column looks like it has merged cells, not sparse data.
    spanned_cols = _detect_spanned_columns(extracted, n_rows, n_cols)
    grid = _forward_fill_spans(extracted, n_rows, n_cols, spanned_cols)

    cells: list[RawCell] = []
    for r_idx, row in enumerate(grid):
        for c_idx, text in enumerate(row):
            val = (text or "").strip()
            cells.append(RawCell(row=r_idx, col=c_idx, text=val, confidence=1.0))

    if not cells:
        return None

    row_y_centers = _row_y_centers(tbl, n_rows)

    return RawTable(
        page=page_idx,
        bbox=tbl.bbox,
        cells=cells,
        n_rows=n_rows,
        n_cols=n_cols,
        row_y_centers=row_y_centers,
    )


def _detect_spanned_columns(
    grid: list[list[str | None]],
    n_rows: int,
    n_cols: int,
) -> set[int]:
    """Return column indices that appear to have merged (spanning) cells.

    A column is treated as "spanned" when it has at least one run of
    [non-empty, None, …, non-empty] where the None run length is shorter
    than the surrounding non-empty values' count. This pattern is typical of
    a cell that physically spans multiple rows — as opposed to a column that
    is just sparsely filled (which would show random Nones with no clear run
    structure). A simple threshold: if ≥50% of the column's None cells appear
    in runs that immediately follow a non-empty cell, treat it as spanned.
    """
    spanned: set[int] = set()
    for c in range(n_cols):
        col_vals = [
            (grid[r][c] if c < len(grid[r]) else None)
            for r in range(n_rows)
        ]
        none_count = sum(1 for v in col_vals if v is None)
        if none_count == 0:
            continue
        # Count Nones that immediately follow a non-empty value.
        post_value_nones = 0
        prev_has_value = False
        for v in col_vals:
            if v is not None and v.strip():
                prev_has_value = True
            elif v is None and prev_has_value:
                post_value_nones += 1
            else:
                prev_has_value = False
        if none_count > 0 and post_value_nones / none_count >= 0.5:
            spanned.add(c)
    return spanned


def _forward_fill_spans(
    grid: list[list[str | None]],
    n_rows: int,
    n_cols: int,
    spanned_cols: set[int],
) -> list[list[str | None]]:
    """Forward-fill None cells only in columns detected as having rowspans.

    For columns with genuinely sparse data (sparse fill, no clear span
    pattern) we leave None as-is so empty cells stay empty.
    """
    result: list[list[str | None]] = [
        list(row) + [None] * (n_cols - len(row)) for row in grid
    ]
    for c in spanned_cols:
        prev: str | None = None
        for r in range(n_rows):
            val = result[r][c]
            if val is not None and val.strip():
                prev = val
            elif val is None and prev is not None:
                result[r][c] = prev
    return result


def _row_y_centers(tbl: Any, n_rows: int) -> list[float]:
    """Derive per-row Y-centers from the cell bounding boxes."""
    rows_by_top: dict[float, list[tuple]] = defaultdict(list)
    for cell_bbox in tbl.cells:
        if cell_bbox is not None:
            key = round(cell_bbox[1], 1)
            rows_by_top[key].append(cell_bbox)

    sorted_tops = sorted(rows_by_top.keys())
    y_centers: list[float] = []
    for top in sorted_tops:
        cells_at = rows_by_top[top]
        bottom = max(c[3] for c in cells_at)
        y_centers.append((top + bottom) / 2.0)

    while len(y_centers) < n_rows:
        y_centers.append(y_centers[-1] if y_centers else 0.0)
    return y_centers[:n_rows]
