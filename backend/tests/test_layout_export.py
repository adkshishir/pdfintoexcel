"""Unit tests for full-document layout Excel export."""

from __future__ import annotations

from pathlib import Path

import openpyxl

from app.pipeline.layout_export import export_full_document
from app.pipeline.types import WordBox


def _wb(text: str, x: float, y: float, w: float = 30, h: float = 10, page: int = 0) -> WordBox:
    return WordBox(text=text, x=x, y=y, w=w, h=h, page=page, confidence=1.0)


def test_layout_export_two_lines_two_columns(tmp_path: Path) -> None:
    boxes = [
        _wb("Hello", x=10, y=20, w=40),
        _wb("World", x=200, y=20, w=40),
        _wb("Foo", x=10, y=50, w=30),
        _wb("Bar", x=200, y=50, w=30),
    ]
    out = tmp_path / "out.xlsx"
    n = export_full_document(boxes, page_count=1, output_path=out)
    wb = openpyxl.load_workbook(out)
    assert "Page_1" in wb.sheetnames
    ws = wb["Page_1"]

    # Position-mapped layout: words land at PDF-coordinate-derived Excel cells.
    from app.pipeline.layout_export import COL_RES, ROW_RES
    r_top = int(20 / ROW_RES) + 1
    r_bot = int(50 / ROW_RES) + 1
    c_left = int(10 / COL_RES) + 1
    c_right = int(200 / COL_RES) + 1

    assert ws.cell(r_top, c_left).value == "Hello"
    assert ws.cell(r_top, c_right).value == "World"
    assert ws.cell(r_bot, c_left).value == "Foo"
    assert ws.cell(r_bot, c_right).value == "Bar"
    # n = max Excel row written on this page
    assert n == r_bot


def test_layout_export_empty_page(tmp_path: Path) -> None:
    out = tmp_path / "empty.xlsx"
    n = export_full_document([], page_count=1, output_path=out)
    assert n == 1
    wb = openpyxl.load_workbook(out)
    assert wb["Page_1"]["A1"].value == "(empty page)"


def test_layout_export_multi_page(tmp_path: Path) -> None:
    boxes = [_wb("p0", x=10, y=10, page=0), _wb("p1", x=10, y=10, page=1)]
    out = tmp_path / "m.xlsx"
    n = export_full_document(boxes, page_count=2, output_path=out)
    assert n == 2
    wb = openpyxl.load_workbook(out)
    assert "Page_1" in wb.sheetnames and "Page_2" in wb.sheetnames


def test_layout_export_merged_footer_appears_once(tmp_path: Path) -> None:
    """Footer block taller than _FOOTER_ZONE must be written exactly once.

    Simulates a 5-page document where the bottom portion of each page contains
    a multi-line disclaimer paragraph.  Only the last few lines of the disclaimer
    fall inside the hard footer-detection zone; the earlier lines are above it.
    After contiguous-block expansion the full disclaimer should land in the footer
    and be written once at the end of the merged sheet — not once per page.

    Layout (ROW_RES=12 pt, _FOOTER_ZONE=15 %):
      - Body word at y=10.
      - 8 disclaimer lines at y=100, 112, 124, … 184  (spacing = ROW_RES, no gap).
      - Page extents: y_max ≈ 184+10=194, y_min=10, span=184.
      - ft = 194 − 184×0.15 ≈ 166.4  → last 2 lines (y=172, y=184) in hard zone.
      - Confirmed footer fingerprints come from those 2 lines.
      - Contiguous expansion walks upward (gap=0 ≤ 2×ROW_RES) and absorbs all
        earlier disclaimer lines.
    """
    from app.pipeline.layout_export import export_full_document

    PAGES = 5
    # 8 disclaimer lines, one token each, spaced exactly ROW_RES=12 pt apart so
    # consecutive lines are contiguous (gap = 0).
    disclaimer_tokens = [
        "Disclaimer", "Company", "Registered", "Office",
        "Broadwalk", "House", "Authorised", "Regulated",
    ]
    DISC_Y_START = 100  # first disclaimer line
    SPACING      = 12   # = ROW_RES → contiguous, one Excel row each

    boxes: list[WordBox] = []
    for page in range(PAGES):
        boxes.append(_wb(f"Body-{page}", x=10, y=10, page=page))
        for i, tok in enumerate(disclaimer_tokens):
            y_tok = DISC_Y_START + i * SPACING
            boxes.append(_wb(tok, x=10, y=y_tok, h=10, page=page))

    out = tmp_path / "merged_footer.xlsx"
    export_full_document(boxes, page_count=PAGES, output_path=out, output_layout="merged")

    wb = openpyxl.load_workbook(out)
    assert "Document" in wb.sheetnames
    ws = wb["Document"]

    # Flatten all non-empty cell values (may contain space-joined tokens).
    all_text = " ".join(
        str(cell.value)
        for row in ws.iter_rows()
        for cell in row
        if cell.value
    )

    # Each unique body token must appear exactly PAGES times (once per page body).
    # Actually body tokens are suppressed if they land in footer — but here each
    # body word is at y=10 which is far above the footer zone and not contiguous
    # with the disclaimer block, so they stay as body.
    for page in range(PAGES):
        count = all_text.count(f"Body-{page}")
        assert count == 1, f"Body-{page} should appear exactly once, got {count}"

    # Each disclaimer token must appear exactly ONCE in the full sheet
    # (written once as footer, not duplicated per page).
    for tok in disclaimer_tokens:
        count = all_text.count(tok)
        assert count == 1, \
            f"Footer token '{tok}' should appear once but found {count} times"
