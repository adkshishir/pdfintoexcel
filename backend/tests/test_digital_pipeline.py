"""Phase 2 tests.

`test_synthetic_pdf` is hermetic — builds a tiny PDF with PyMuPDF, runs the
pipeline, asserts an .xlsx came out with the expected headers + rows.

`test_monzo_fixture_if_present` runs against the real bank-statement PDF if
it's at the repo root. Skipped otherwise so CI doesn't depend on a fixture
the team may not check in.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import fitz
import pytest
from openpyxl import load_workbook

from app.pipeline.orchestrator import run_pipeline


REPO_ROOT = Path(__file__).resolve().parents[2]
MONZO_PDF = REPO_ROOT / "MonzoBus.pdf"


def _make_synthetic_pdf(path: Path) -> None:
    """Build a one-page PDF with a 3-column 'table' positioned by absolute coords."""
    doc = fitz.open()
    page = doc.new_page(width=400, height=300)

    def write(x: float, y: float, text: str) -> None:
        page.insert_text((x, y), text, fontsize=10)

    # header
    write(40,  40, "Name")
    write(160, 40, "Qty")
    write(280, 40, "Price")
    # rows
    write(40,  70, "Apple");  write(160, 70, "3");  write(280, 70, "1.20")
    write(40, 100, "Banana"); write(160, 100, "5"); write(280, 100, "0.40")
    write(40, 130, "Cherry"); write(160, 130, "2"); write(280, 130, "3.50")

    doc.save(path)
    doc.close()


def test_synthetic_pdf_round_trip(tmp_path: Path) -> None:
    pdf = tmp_path / "in.pdf"
    out = tmp_path / "out.xlsx"
    _make_synthetic_pdf(pdf)

    result = run_pipeline(pdf, out, mode="fast")

    assert result.pdf_type == "digital"
    assert result.page_count == 1
    assert len(result.tables) == 1

    wb = load_workbook(out)
    # Cleaner adds a hidden _conf_<name> sheet per data sheet — find the data one.
    data_sheets = [n for n in wb.sheetnames if not n.startswith("_conf_")]
    assert len(data_sheets) == 1
    ws = wb[data_sheets[0]]
    rows = [[c.value for c in row] for row in ws.iter_rows()]
    assert rows[0] == ["Name", "Qty", "Price"]
    # Body — Qty + Price are inferred numeric and coerced.
    assert rows[1] == ["Apple",  3, 1.20]
    assert rows[2] == ["Banana", 5, 0.40]
    assert rows[3] == ["Cherry", 2, 3.50]


@pytest.mark.skipif(not MONZO_PDF.exists(), reason="MonzoBus.pdf fixture not present")
def test_monzo_bank_statement(tmp_path: Path) -> None:
    out = tmp_path / "monzo.xlsx"
    result = run_pipeline(MONZO_PDF, out, mode="fast")

    assert result.pdf_type == "digital"
    assert result.page_count == 24
    # 23 transaction pages (page 0 is cover) collapse into 1 sheet via
    # cross-page header merging; the cover-page noise is dropped by the
    # not-a-table filter. So we expect exactly 1 user-facing sheet.
    assert len(result.tables) == 1

    wb = load_workbook(out)
    data_sheets = [n for n in wb.sheetnames if not n.startswith("_conf_")]
    assert len(data_sheets) == 1
    ws = wb[data_sheets[0]]

    # Locate the table header row (may be preceded by preamble rows).
    table_header_row = None
    for row in ws.iter_rows():
        vals = [c.value for c in row]
        if vals[0] == "Date" and "Description" in vals:
            table_header_row = row[0].row
            break
    assert table_header_row is not None, "Could not find table header row in sheet"
    headers = [c.value for c in ws[table_header_row]]
    assert headers == ["Date", "Description", "(GBP) Amount", "(GBP) Balance"]

    # Amount column inferred numeric → cells should be floats.
    body = [[c.value for c in r] for r in ws.iter_rows(min_row=table_header_row + 1)]
    numeric_amounts = [r[2] for r in body if isinstance(r[2], (int, float))]
    assert len(numeric_amounts) >= 100   # 23 pages × ~10 transactions

    # Date column inferred date → cells should be datetime.date.
    from datetime import date
    date_cells = [r[0] for r in body if isinstance(r[0], date)]
    assert len(date_cells) >= 100
