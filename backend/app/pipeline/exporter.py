"""CleanTable[] → .xlsx via openpyxl.

Improvements over the original:
  - Date coercion uses python-dateutil for robust multi-format parsing.
  - dayfirst (day-first vs month-first) is inferred per date column from the
    data itself: if any value has a first component > 12 it's unambiguously
    day-first; otherwise European convention (day-first) is the default.
  - Accounting-style negative numbers  (123.45) → -123.45.
  - Column widths are auto-fitted to content (capped at 50 chars).
  - Hidden `_confidence` sheet preserved for per-cell quality inspection.
"""

from __future__ import annotations

import io
import re
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.formatting.rule import CellIsRule
from openpyxl.utils import get_column_letter

try:
    from dateutil import parser as _du_parser
    from dateutil.parser import ParserError as _DuParserError
    _DATEUTIL = True
except ImportError:
    _DATEUTIL = False

from app.pipeline.types import CleanTable, ColumnType, ImageExport, WordBox

# Y-grouping tolerance for preamble line reconstruction (pt).
_PRE_LINE_TOL = 8.0
# Minimum X gap between adjacent words that signals a two-column layout (pt).
_PRE_COL_GAP = 150.0

_BAD_CHARS = str.maketrans({c: "_" for c in ":\\/?*[]"})

_NUM_CLEAN = re.compile(r"[,\s£\$€¥]")
_NUM_RE = re.compile(r"^[\-\+]?\d+(?:\.\d+)?$")
# Accounting negative: (1,234.56) → -1234.56
_PARENS_RE = re.compile(r"^\(([^)]+)\)$")
# Date pattern for dayfirst sniffing (numeric separators only — unambiguous cases).
_SNIFF_DATE = re.compile(r"^(\d{1,2})[/\-\.](\d{1,2})[/\-\.]\d{2,4}$")
# Legacy fallback formats used when dateutil is unavailable.
_DATE_FORMATS_FALLBACK = (
    "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
    "%m/%d/%Y", "%Y-%m-%d",
    "%d %b %Y", "%d-%b-%Y", "%d/%b/%Y",
    "%b %d, %Y", "%B %d, %Y",
)

_LOW = PatternFill("solid", fgColor="F8B4B4")
_MED = PatternFill("solid", fgColor="FCE596")


def export_excel(
    tables: list[CleanTable],
    output_path: Path,
    *,
    preamble_boxes: list[WordBox] | None = None,
    preamble_images: list[dict] | None = None,
    footer_lines: list[str] | None = None,
    image_export: ImageExport = "none",
    pdf_path: Path | None = None,
    export_metrics: dict | None = None,
) -> None:
    wb = Workbook()
    default_sheet = wb.active

    if not tables:
        default_sheet.title = "empty"
        default_sheet["A1"] = "No tables were detected in this document."
        if image_export == "figures" and pdf_path is not None:
            from app.pipeline.figures_sheet import append_figures_sheet_from_pdf

            st = append_figures_sheet_from_pdf(wb, pdf_path)
            if export_metrics is not None:
                export_metrics.update({f"figures_{k}": v for k, v in st.items()})
        wb.save(output_path)
        return

    wb.remove(default_sheet)

    bold = Font(bold=True)
    first = True
    for ct in tables:
        sheet_name = _safe_sheet_name(ct.sheet_name)
        ws = wb.create_sheet(sheet_name)

        # Write page preamble (non-table header content) before the first table.
        pre_rows = 0
        if first and (preamble_boxes or preamble_images):
            n_cols = max(1, len(ct.headers))
            pre_rows = _write_preamble(ws, preamble_boxes or [], preamble_images or [], n_cols)
        first = False

        # Infer dayfirst per date column before coercing.
        dayfirst = _infer_dayfirst_flags(ct)

        header_row = pre_rows + 1
        for col_idx, header in enumerate(ct.headers, start=1):
            ws.cell(row=header_row, column=col_idx, value=header).font = bold

        for row_idx, row in enumerate(ct.rows, start=header_row + 1):
            coerced = _coerce_row(row, ct.column_types, dayfirst)
            for col_idx, val in enumerate(coerced, start=1):
                ws.cell(row=row_idx, column=col_idx, value=val)

        ws.freeze_panes = f"A{header_row + 1}"

        # Number/date formats (start from first data row, not row 2).
        for col_idx, col_type in enumerate(ct.column_types, start=1):
            if col_type == "number":
                for row_idx in range(header_row + 1, ws.max_row + 1):
                    ws.cell(row=row_idx, column=col_idx).number_format = "#,##0.00"
            elif col_type == "date":
                for row_idx in range(header_row + 1, ws.max_row + 1):
                    ws.cell(row=row_idx, column=col_idx).number_format = "dd/mm/yyyy"

        _autofit_columns(ws, ct.headers, ct.rows)

        # Hidden _confidence sibling sheet.
        conf_name = _safe_sheet_name(f"_conf_{sheet_name}")
        cws = wb.create_sheet(conf_name)
        cws.sheet_state = "hidden"
        cws.append(ct.headers)
        for conf_row in ct.confidence:
            cws.append([round(c, 3) for c in conf_row])
        last_col = cws.cell(row=1, column=len(ct.headers)).column_letter
        cell_range = f"A2:{last_col}{cws.max_row}"
        cws.conditional_formatting.add(
            cell_range,
            CellIsRule(operator="lessThan", formula=["0.5"], fill=_LOW),
        )
        cws.conditional_formatting.add(
            cell_range,
            CellIsRule(operator="between", formula=["0.5", "0.8"], fill=_MED),
        )

    # Write footer once at the end of the last data sheet.
    if footer_lines:
        data_sheets = [n for n in wb.sheetnames if not n.startswith("_conf_")]
        if data_sheets:
            _write_footer(wb[data_sheets[-1]], footer_lines)

    if image_export == "figures" and pdf_path is not None:
        from app.pipeline.figures_sheet import append_figures_sheet_from_pdf

        st = append_figures_sheet_from_pdf(wb, pdf_path)
        if export_metrics is not None:
            export_metrics.update({f"figures_{k}": v for k, v in st.items()})

    wb.save(output_path)


# ---- dayfirst inference -----------------------------------------------

def _infer_dayfirst_flags(ct: CleanTable) -> list[bool]:
    """Return one bool per column: True = day-first (European), False = month-first."""
    flags: list[bool] = []
    for col_idx, col_type in enumerate(ct.column_types):
        if col_type != "date":
            flags.append(True)
            continue
        values = [
            row[col_idx]
            for row in ct.rows
            if col_idx < len(row) and row[col_idx].strip()
        ]
        flags.append(_dayfirst_for_column(values))
    return flags


def _dayfirst_for_column(values: list[str]) -> bool:
    """Detect day-first from unambiguous numeric date values.

    If ANY value has first component > 12, it MUST be day-first (e.g. 25/01/2024).
    If ANY value has second component > 12, it MUST be month-first (e.g. 01/25/2024).
    Default: True (European day-first).
    """
    for v in values:
        m = _SNIFF_DATE.match(v.strip())
        if m:
            first, second = int(m.group(1)), int(m.group(2))
            if first > 12:
                return True
            if second > 12:
                return False
    return True


# ---- row/cell coercion ------------------------------------------------

def _coerce_row(
    row: list[str],
    types: list[ColumnType],
    dayfirst: list[bool],
) -> list[object]:
    out: list[object] = []
    for i, val in enumerate(row):
        t = types[i] if i < len(types) else "text"
        df = dayfirst[i] if i < len(dayfirst) else True
        out.append(_coerce_cell(val, t, df))
    return out


def _coerce_cell(value: str, col_type: ColumnType, dayfirst: bool = True) -> object:
    """Coerce a single cell value.

    Always attempts numeric and date parsing regardless of the column-type
    hint (the hint only controls number_format). This handles mixed columns
    gracefully: a mostly-numeric column with a few stray text tokens still
    gets those tokens typed correctly.
    """
    if not value or not value.strip():
        return None
    s = value.strip()

    # --- numeric (including accounting negatives) ---
    paren = _PARENS_RE.match(s)
    raw = paren.group(1) if paren else s
    cleaned = _NUM_CLEAN.sub("", raw)
    if _NUM_RE.match(cleaned):
        try:
            num = float(cleaned) if "." in cleaned else int(cleaned)
            return -abs(num) if paren else num
        except ValueError:
            pass

    # --- date ---
    if _DATEUTIL:
        parsed = _parse_date_dateutil(s, dayfirst)
        if parsed is not None:
            return parsed
    else:
        parsed = _parse_date_fallback(s)
        if parsed is not None:
            return parsed

    return s


def _parse_date_dateutil(s: str, dayfirst: bool) -> date | None:
    try:
        return _du_parser.parse(s, dayfirst=dayfirst, fuzzy=False).date()
    except (_DuParserError, OverflowError, ValueError, TypeError):
        return None


def _parse_date_fallback(s: str) -> date | None:
    from datetime import datetime
    for fmt in _DATE_FORMATS_FALLBACK:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# ---- formatting helpers -----------------------------------------------

def _autofit_columns(ws, headers: list[str], rows: list[list[str]]) -> None:
    """Set column widths to fit the widest value, capped at 50 chars."""
    for col_idx, header in enumerate(headers, start=1):
        max_len = max(8, len(str(header)))
        for row in rows:
            if col_idx - 1 < len(row):
                max_len = max(max_len, len(str(row[col_idx - 1] or "")))
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = min(50, max_len + 2)


def _safe_sheet_name(name: str) -> str:
    cleaned = name.translate(_BAD_CHARS).strip()
    return (cleaned or "Sheet")[:31]


# ---- preamble writing (non-table first-page content) ------------------

def _write_footer(ws, footer_lines: list[str]) -> None:
    """Append footer text below all table data with a visual separator."""
    if not footer_lines:
        return
    n_cols    = max(1, ws.max_column or 1)
    last_col  = get_column_letter(n_cols)
    start_row = (ws.max_row or 0) + 2        # one blank separator row

    italic_gray = Font(italic=True, color="808080")
    wrap        = Alignment(wrap_text=True)

    # Optional thin separator label.
    sep_row = start_row - 1
    sep_cell = ws.cell(row=sep_row, column=1, value="─" * 30)
    sep_cell.font = Font(color="CCCCCC")
    if n_cols > 1:
        ws.merge_cells(f"A{sep_row}:{last_col}{sep_row}")

    for i, line in enumerate(footer_lines):
        r = start_row + i
        cell = ws.cell(row=r, column=1, value=line)
        cell.font      = italic_gray
        cell.alignment = wrap
        if n_cols > 1:
            ws.merge_cells(f"A{r}:{last_col}{r}")
        ws.row_dimensions[r].height = 14


def _write_preamble(
    ws,
    boxes: list[WordBox],
    images: list[dict],
    n_table_cols: int,
) -> int:
    """Write position-aware non-table content before the table header.

    Words are grouped into visual lines by Y proximity.  If a line contains
    words from two clearly separate X columns (gap > _PRE_COL_GAP) the line is
    split into a left cell and a right cell; otherwise it spans all columns.

    Returns the number of Excel rows consumed (including a blank separator row
    so the caller knows where to place the table header).
    """
    if not boxes and not images:
        return 0

    lines = _preamble_group_lines(boxes)
    n_cols = max(1, n_table_cols)
    last_letter = get_column_letter(n_cols)
    mid_col     = max(1, n_cols // 2)
    mid_letter  = get_column_letter(mid_col)

    title_font  = Font(bold=True, size=12)
    label_font  = Font(bold=True)
    preamble_fill = PatternFill("solid", fgColor="F0F4FF")   # very light blue tint

    row_num = 1
    for line_idx, line in enumerate(lines):
        sw = sorted(line, key=lambda w: w.x)
        left_words, right_words = _split_columns(sw)

        if right_words and n_cols >= 4:
            # Two-column line: left in cols 1..mid, right in mid+1..n_cols
            left_text  = " ".join(w.text for w in left_words)
            right_text = " ".join(w.text for w in right_words)
            if left_text:
                cell = ws.cell(row=row_num, column=1, value=left_text)
                cell.fill = preamble_fill
                if mid_col > 1:
                    ws.merge_cells(f"A{row_num}:{mid_letter}{row_num}")
            if right_text:
                right_col  = mid_col + 1
                right_cell = ws.cell(row=row_num, column=right_col, value=right_text)
                right_cell.fill = preamble_fill
                if right_col < n_cols:
                    ws.merge_cells(
                        f"{get_column_letter(right_col)}{row_num}:{last_letter}{row_num}"
                    )
        else:
            text = " ".join(w.text for w in sw)
            if text:
                cell = ws.cell(row=row_num, column=1, value=text)
                cell.fill = preamble_fill
                # First two rows are treated as the document title / date range
                # — render them bold and slightly larger.
                if line_idx == 0:
                    cell.font = title_font
                elif line_idx == 1:
                    cell.font = label_font
                if n_cols > 1:
                    ws.merge_cells(f"A{row_num}:{last_letter}{row_num}")
        row_num += 1

    # Insert images at approximate positions.
    for img in images:
        _insert_preamble_image(ws, img)

    # Blank separator row between preamble and table header.
    row_num += 1
    return row_num - 1


def _preamble_group_lines(boxes: list[WordBox]) -> list[list[WordBox]]:
    """Group words into horizontal text lines by Y-centre proximity."""
    if not boxes:
        return []
    ordered = sorted(boxes, key=lambda w: (w.y + w.y2) / 2.0)
    lines: list[list[WordBox]] = [[ordered[0]]]
    for w in ordered[1:]:
        cy      = (w.y + w.y2) / 2.0
        line_cy = sum((u.y + u.y2) / 2.0 for u in lines[-1]) / len(lines[-1])
        if abs(cy - line_cy) <= _PRE_LINE_TOL:
            lines[-1].append(w)
        else:
            lines.append([w])
    return lines


def _split_columns(
    sorted_words: list[WordBox],
) -> tuple[list[WordBox], list[WordBox]]:
    """Split words into left/right groups when there is a large X gap.

    Returns (left, right).  If no big gap exists the whole list is left
    and right is empty.
    """
    if len(sorted_words) < 2:
        return sorted_words, []
    # Find the largest gap between adjacent words.
    max_gap  = 0.0
    split_at = -1
    for i in range(len(sorted_words) - 1):
        gap = sorted_words[i + 1].x - sorted_words[i].x2
        if gap > max_gap:
            max_gap  = gap
            split_at = i + 1
    if max_gap < _PRE_COL_GAP:
        return sorted_words, []
    return sorted_words[:split_at], sorted_words[split_at:]


def _insert_preamble_image(ws, img_info: dict) -> None:
    """Insert an image extracted from the PDF preamble into the sheet."""
    try:
        from openpyxl.drawing.image import Image as XLImage
    except ImportError:
        return
    try:
        x0, y0, x1, y1 = img_info["bbox"]
        # Map PDF pt to rough Excel row/col; images go at top-left of their bbox.
        col_letter = get_column_letter(max(1, int(x0 / 6.0) + 1))
        row_num    = max(1, int(y0 / 12.0) + 1)
        anchor     = f"{col_letter}{row_num}"
        xl_img         = XLImage(io.BytesIO(img_info["data"]))
        xl_img.width   = max(16, int((x1 - x0) * 1.333))
        xl_img.height  = max(16, int((y1 - y0) * 1.333))
        ws.add_image(xl_img, anchor)
    except Exception:
        pass
