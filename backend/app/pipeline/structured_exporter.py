"""Structured full-document Excel exporter.

Converts a DocumentContent into a single-sheet Excel workbook with clear
visual sections:

  ┌──────────────────────────────────────┐
  │  DOCUMENT HEADER (blue label row)    │
  │  Title / metadata lines              │
  │  Key         │ Value                 │
  ├──────────────────────────────────────┤
  │  (spacer)                            │
  │  Body: pre-table lines (footer-style)│
  │  Body: heading / paragraph / bullet  │
  │  Body: inline table                  │
  │  ...                                 │
  │  (spacer)                            │
  ├──────────────────────────────────────┤
  │  DOCUMENT FOOTER (blue label row)    │
  │  Footer lines (italic, gray)         │
  └──────────────────────────────────────┘

Public entry points
-------------------
  export_structured_document(content, output_path) -> int  (total rows written)
  export_structured_document_per_page(content, output_path) -> int  (sum across sheets)
"""

from __future__ import annotations

import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.pipeline.exporter import (
    _autofit_columns,
    _coerce_row,
    _infer_dayfirst_flags,
    _safe_sheet_name,
)
from app.pipeline.types import CleanTable, ContentBlock, DocumentContent, ImageExport

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------
_SECTION_LABEL_FONT  = Font(bold=True, color="FFFFFF", size=11)
_SECTION_LABEL_FILL  = PatternFill("solid", fgColor="2E75B6")   # blue
_TITLE_FONT          = Font(bold=True, size=14)
_HEADING_FONT        = Font(bold=True, size=12)
_BOLD                = Font(bold=True)
_ITALIC_GRAY         = Font(italic=True, color="767171")
_TABLE_HEADER_FONT   = Font(bold=True, color="FFFFFF")
_TABLE_HEADER_FILL   = PatternFill("solid", fgColor="4472C4")   # mid blue
_ALT_ROW_FILL        = PatternFill("solid", fgColor="EBF3FB")   # very light blue
_WRAP_ALIGN          = Alignment(wrap_text=True, vertical="top")
_VCENTER_ALIGN       = Alignment(vertical="center")

_KV_RE = re.compile(r"^(.{1,50}):\s+(.+)$")   # detect "Key: Value" lines


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def export_structured_document(
    content: DocumentContent,
    output_path: Path,
    *,
    image_export: ImageExport = "none",
    pdf_path: Path | None = None,
    export_metrics: dict | None = None,
) -> int:
    """Write DocumentContent to a structured Excel workbook.

    Returns the total number of rows written.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = _safe_sheet_name("Document")
    _populate_structured_worksheet(ws, content)
    n_cols = max(6, _doc_col_count(content))
    _set_col_widths(ws, n_cols, content)
    if image_export == "figures" and pdf_path is not None:
        from app.pipeline.figures_sheet import append_figures_sheet_from_pdf

        st = append_figures_sheet_from_pdf(wb, pdf_path)
        if export_metrics is not None:
            export_metrics.update({f"figures_{k}": v for k, v in st.items()})
    wb.save(output_path)
    return max(1, ws.max_row or 1)


def export_structured_document_per_page(
    content: DocumentContent,
    output_path: Path,
    *,
    image_export: ImageExport = "none",
    pdf_path: Path | None = None,
    export_metrics: dict | None = None,
) -> int:
    """Same structured layout as `export_structured_document`, one sheet per PDF page.

    Repeated `header_lines` appear on every sheet. `footer_lines` are written
    only on the last sheet so legal disclaimers are not duplicated on each page.
    Returns the sum of max row indices across sheets (for metrics).
    """
    wb = Workbook()
    wb.remove(wb.active)
    total_rows = 0
    pc = content.page_count

    for p in range(pc):
        blocks = [b for b in content.body_blocks if b.page == p]
        sub = DocumentContent(
            header_lines=list(content.header_lines),
            footer_lines=list(content.footer_lines) if p == pc - 1 else [],
            body_blocks=blocks,
            page_count=1,
        )
        title = _safe_sheet_name(f"Page_{p + 1}")
        ws = wb.create_sheet(title)
        if not (sub.header_lines or sub.body_blocks or sub.footer_lines):
            ws.cell(row=1, column=1, value="(no content on this page)")
            ws.row_dimensions[1].height = 16
            total_rows += 1
        else:
            _populate_structured_worksheet(ws, sub)
            total_rows += max(1, ws.max_row or 1)
        n_cols = max(6, _doc_col_count(sub))
        _set_col_widths(ws, n_cols, sub)

    if image_export == "figures" and pdf_path is not None:
        from app.pipeline.figures_sheet import append_figures_sheet_from_pdf

        st = append_figures_sheet_from_pdf(wb, pdf_path)
        if export_metrics is not None:
            export_metrics.update({f"figures_{k}": v for k, v in st.items()})

    wb.save(output_path)
    return total_rows


def _populate_structured_worksheet(ws, content: DocumentContent) -> None:
    """Write header, body blocks, and footer to *ws* (mutates workbook)."""
    n_cols = _doc_col_count(content)
    current_row = 1

    if content.header_lines:
        current_row = _write_section_label(ws, current_row, "DOCUMENT HEADER", n_cols)
        for i, line in enumerate(content.header_lines):
            current_row = _write_header_line(ws, current_row, line, n_cols, is_first=(i == 0))
        current_row += 1

    for block in content.body_blocks:
        current_row = _write_block(ws, block, current_row, n_cols)

    current_row += 1

    if content.footer_lines:
        current_row = _write_section_label(ws, current_row, "DOCUMENT FOOTER", n_cols)
        for line in content.footer_lines:
            _write_merged(ws, current_row, line, n_cols,
                          font=_ITALIC_GRAY, alignment=_WRAP_ALIGN)
            ws.row_dimensions[current_row].height = 14
            current_row += 1


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

def _doc_col_count(content: DocumentContent) -> int:
    """Auto-detect document sheet width: max(6, widest table header count)."""
    max_tbl = max(
        (len(b.table.headers) for b in content.body_blocks
         if b.kind == "table" and b.table is not None),
        default=0,
    )
    return max(6, max_tbl)


def _write_merged(
    ws,
    row: int,
    text: str,
    n_cols: int,
    *,
    font=None,
    fill=None,
    alignment=None,
) -> None:
    """Write text into A{row}, merge across n_cols, apply optional formatting."""
    cell = ws.cell(row=row, column=1, value=text)
    if n_cols > 1:
        ws.merge_cells(f"A{row}:{get_column_letter(n_cols)}{row}")
    if font:
        cell.font = font
    if fill:
        cell.fill = fill
    if alignment:
        cell.alignment = alignment


def _write_kv_row(ws, row: int, key: str, value: str, n_cols: int) -> None:
    """Key in col 1 (bold), value in col 2 (merged to n_cols)."""
    ws.cell(row=row, column=1, value=key).font = _BOLD
    val_cell = ws.cell(row=row, column=2, value=value)
    if n_cols > 2:
        ws.merge_cells(f"B{row}:{get_column_letter(n_cols)}{row}")
    val_cell.alignment = _WRAP_ALIGN


def _write_section_label(ws, row: int, label: str, n_cols: int) -> int:
    """Write a full-width section label row (white bold text on blue). Returns next row."""
    _write_merged(ws, row, label, n_cols,
                  font=_SECTION_LABEL_FONT, fill=_SECTION_LABEL_FILL)
    ws.row_dimensions[row].height = 16
    return row + 1


def _write_header_line(ws, row: int, line: str, n_cols: int, *, is_first: bool) -> int:
    """Write one header line — auto-detect KV pair or title."""
    m = _KV_RE.match(line.strip())
    if m:
        _write_kv_row(ws, row, m.group(1).strip(), m.group(2).strip(), n_cols)
    elif is_first or len(line.split()) <= 6:
        # First line or short line → title style
        font = _TITLE_FONT if is_first else _HEADING_FONT
        _write_merged(ws, row, line, n_cols, font=font)
        ws.row_dimensions[row].height = 20 if is_first else 16
    else:
        _write_merged(ws, row, line, n_cols)
    return row + 1


# ---------------------------------------------------------------------------
# Body block writers
# ---------------------------------------------------------------------------

def _write_block(ws, block: ContentBlock, row: int, n_cols: int) -> int:
    """Write a single ContentBlock and return the next available row."""
    if block.kind == "pre_table":
        return _write_pre_table_block(ws, block, row, n_cols)
    if block.kind == "heading":
        return _write_heading_block(ws, block, row, n_cols)
    if block.kind == "key_value":
        return _write_kv_block(ws, block, row, n_cols)
    if block.kind in ("paragraph", "bullet"):
        return _write_text_block(ws, block, row, n_cols)
    if block.kind == "table":
        return _write_table_block(ws, block, row, n_cols)
    return row


def _write_pre_table_block(ws, block: ContentBlock, row: int, n_cols: int) -> int:
    """Letterhead / intro above the first table — line-by-line like the footer section."""
    for line in block.lines:
        stripped = line.strip()
        if not stripped:
            continue
        _write_merged(ws, row, stripped, n_cols,
                      font=_ITALIC_GRAY, alignment=_WRAP_ALIGN)
        ws.row_dimensions[row].height = 14
        row += 1
    return row + 1


def _write_heading_block(ws, block: ContentBlock, row: int, n_cols: int) -> int:
    text = " ".join(block.lines).strip()
    if not text:
        return row
    _write_merged(ws, row, text, n_cols, font=_HEADING_FONT)
    ws.row_dimensions[row].height = 16
    return row + 2   # blank row after heading


def _write_kv_block(ws, block: ContentBlock, row: int, n_cols: int) -> int:
    for line in block.lines:
        m = _KV_RE.match(line.strip())
        if m:
            _write_kv_row(ws, row, m.group(1).strip(), m.group(2).strip(), n_cols)
        else:
            _write_merged(ws, row, line, n_cols)
        row += 1
    return row + 1   # blank row after KV block


def _write_text_block(ws, block: ContentBlock, row: int, n_cols: int) -> int:
    text = "\n".join(block.lines).strip()
    if not text:
        return row
    _write_merged(ws, row, text, n_cols, alignment=_WRAP_ALIGN)
    # Height: ~15 pt per visible line
    ws.row_dimensions[row].height = max(15, 15 * len(block.lines))
    return row + 2   # blank row after text block


def _write_table_block(ws, block: ContentBlock, row: int, n_cols: int) -> int:
    ct = block.table
    if ct is None or not ct.headers:
        return row

    K = len(ct.headers)

    # ── header row ──
    for col_idx, header in enumerate(ct.headers, start=1):
        cell = ws.cell(row=row, column=col_idx, value=header)
        cell.font  = _TABLE_HEADER_FONT
        cell.fill  = _TABLE_HEADER_FILL
        cell.alignment = _VCENTER_ALIGN
    ws.row_dimensions[row].height = 16
    row += 1

    # ── data rows ──
    dayfirst = _infer_dayfirst_flags(ct)
    for data_idx, data_row in enumerate(ct.rows):
        coerced = _coerce_row(data_row, ct.column_types, dayfirst)
        fill = _ALT_ROW_FILL if data_idx % 2 == 1 else None
        for col_idx, val in enumerate(coerced, start=1):
            cell = ws.cell(row=row, column=col_idx, value=val)
            if fill:
                cell.fill = fill
        row += 1

    # ── number / date formats ──
    data_start = row - len(ct.rows)
    data_end   = row - 1
    for col_idx, col_type in enumerate(ct.column_types, start=1):
        if col_type == "number":
            for r in range(data_start, data_end + 1):
                ws.cell(row=r, column=col_idx).number_format = "#,##0.00"
        elif col_type == "date":
            for r in range(data_start, data_end + 1):
                ws.cell(row=r, column=col_idx).number_format = "dd/mm/yyyy"

    # ── auto-fit table columns (only up to n_cols) ──
    _autofit_table_cols(ws, ct, row - len(ct.rows) - 1, data_end, K)

    return row + 2   # two blank rows after table


def _autofit_table_cols(ws, ct: CleanTable, header_row: int, last_row: int, K: int) -> None:
    """Set column widths based on the widest value in this table."""
    for col_idx, header in enumerate(ct.headers, start=1):
        max_w = max(8, len(str(header)))
        for row_data in ct.rows:
            if col_idx - 1 < len(row_data):
                max_w = max(max_w, len(str(row_data[col_idx - 1] or "")))
        current = ws.column_dimensions[get_column_letter(col_idx)].width or 0
        ws.column_dimensions[get_column_letter(col_idx)].width = min(50, max(current, max_w + 2))


# ---------------------------------------------------------------------------
# Column width finaliser
# ---------------------------------------------------------------------------

def _set_col_widths(ws, n_cols: int, content: DocumentContent) -> None:
    """Final pass: ensure every document column has a reasonable width."""
    # Set a floor for non-table columns.
    for ci in range(1, n_cols + 1):
        letter = get_column_letter(ci)
        if (ws.column_dimensions[letter].width or 0) < 12:
            ws.column_dimensions[letter].width = 18

    # Column 2 (value column for KV pairs) should be wider.
    if n_cols >= 2:
        c2 = ws.column_dimensions[get_column_letter(2)].width or 0
        ws.column_dimensions[get_column_letter(2)].width = max(c2, 28)
