"""Phase 4 unit tests — synthetic WordBox inputs only.

Each test asserts one slice of the algorithm in `docs/table-reconstruction.md`.
"""

from __future__ import annotations

from app.pipeline.types import WordBox
from app.table.reconstructor import reconstruct_tables


def _wb(text: str, x: float, y: float, w: float = 30, h: float = 10,
        page: int = 0, conf: float = 1.0) -> WordBox:
    return WordBox(text=text, x=x, y=y, w=w, h=h, page=page, confidence=conf)


def test_basic_3col_table_extracts_correctly() -> None:
    """Three columns, three body rows. Anchored header at top."""
    boxes = [
        # Header row at y=10
        _wb("Name",   x=20,  y=10, w=40),
        _wb("Qty",    x=120, y=10, w=20),
        _wb("Price",  x=220, y=10, w=40),
        # Body rows at y=40, 70, 100
        _wb("Apple",  x=20,  y=40, w=40),  _wb("3",  x=125, y=40, w=10),  _wb("1.20", x=220, y=40, w=30),
        _wb("Banana", x=20,  y=70, w=50),  _wb("5",  x=125, y=70, w=10),  _wb("0.40", x=220, y=70, w=30),
        _wb("Cherry", x=20,  y=100, w=50), _wb("12", x=120, y=100, w=20), _wb("3.50", x=220, y=100, w=30),
    ]
    tables = reconstruct_tables(boxes, page_count=1)
    assert len(tables) == 1
    t = tables[0]
    assert t.n_cols == 3
    assert t.n_rows == 4

    # Verify header
    header = sorted([c for c in t.cells if c.row == 0], key=lambda c: c.col)
    assert [c.text for c in header] == ["Name", "Qty", "Price"]

    # Verify body
    by_row = {}
    for c in t.cells:
        by_row.setdefault(c.row, {})[c.col] = c.text
    assert by_row[1] == {0: "Apple",  1: "3",  2: "1.20"}
    assert by_row[2] == {0: "Banana", 1: "5",  2: "0.40"}
    assert by_row[3] == {0: "Cherry", 1: "12", 2: "3.50"}


def test_row_clustering_tolerates_slight_y_skew() -> None:
    """Words on same logical row with sub-pixel Y noise still cluster together."""
    boxes = [
        _wb("A", x=20,  y=40),
        _wb("B", x=120, y=42),    # +2 pt drift
        _wb("C", x=220, y=39),    # -1 pt drift
        # next row
        _wb("D", x=20,  y=70),
        _wb("E", x=120, y=71),
        _wb("F", x=220, y=70),
        # header
        _wb("X", x=20,  y=10),
        _wb("Y", x=120, y=10),
        _wb("Z", x=220, y=10),
    ]
    tables = reconstruct_tables(boxes, page_count=1)
    assert len(tables) == 1
    assert tables[0].n_rows == 3
    by_row = {}
    for c in tables[0].cells:
        by_row.setdefault(c.row, set()).add(c.text)
    # Header
    assert by_row[0] == {"X", "Y", "Z"}
    # Both data rows merged correctly despite Y noise
    assert by_row[1] == {"A", "B", "C"}
    assert by_row[2] == {"D", "E", "F"}


def test_column_count_uses_mode_not_max() -> None:
    """Header row has extra (GBP)-style decoration; body mode is what matters."""
    boxes = [
        # Header: 5 distinct word groups (Date, Description, (GBP), Amount, (GBP), Balance — 6 words)
        _wb("Date",        x=20,  y=10, w=40),
        _wb("Description", x=100, y=10, w=70),
        _wb("(GBP)",       x=220, y=10, w=30),
        _wb("Amount",      x=255, y=10, w=40),  # gap to (GBP) is 5pt → merged
        _wb("(GBP)",       x=320, y=10, w=30),
        _wb("Balance",     x=355, y=10, w=40),  # gap to (GBP) is 5pt → merged
        # Body rows with 4 words each
        _wb("01/01", x=20, y=40, w=30), _wb("Alpha", x=100, y=40, w=40), _wb("10.00", x=255, y=40, w=30), _wb("90.00", x=355, y=40, w=30),
        _wb("02/01", x=20, y=70, w=30), _wb("Beta",  x=100, y=70, w=30), _wb("20.00", x=255, y=70, w=30), _wb("80.00", x=355, y=70, w=30),
        _wb("03/01", x=20, y=100, w=30), _wb("Gamma", x=100, y=100, w=40), _wb("30.00", x=255, y=100, w=30), _wb("70.00", x=355, y=100, w=30),
    ]
    tables = reconstruct_tables(boxes, page_count=1)
    assert len(tables) == 1
    assert tables[0].n_cols == 4
    header = sorted([c for c in tables[0].cells if c.row == 0], key=lambda c: c.col)
    assert [c.text for c in header] == ["Date", "Description", "(GBP) Amount", "(GBP) Balance"]


def test_section_break_drops_decorative_rows() -> None:
    """A row separated by a huge Y gap shouldn't be in the table."""
    boxes = [
        # Top decoration
        _wb("Page header line", x=20, y=5, w=200),
        # Big gap then table
        _wb("X", x=20, y=200), _wb("Y", x=120, y=200),
        _wb("a", x=20, y=215), _wb("b", x=120, y=215),
        _wb("c", x=20, y=230), _wb("d", x=120, y=230),
        _wb("e", x=20, y=245), _wb("f", x=120, y=245),
    ]
    tables = reconstruct_tables(boxes, page_count=1)
    assert len(tables) == 1
    # Decoration row excluded — table should have 4 rows (header + 3 body).
    assert tables[0].n_rows == 4


def test_per_page_isolation() -> None:
    """Boxes from different pages don't bleed into each other."""
    p0 = [
        _wb("Item",  x=20, y=10, page=0), _wb("Qty", x=120, y=10, page=0),
        _wb("Apple", x=20, y=40, page=0), _wb("3",   x=120, y=40, page=0),
        _wb("Pear",  x=20, y=70, page=0), _wb("5",   x=120, y=70, page=0),
    ]
    p1 = [
        _wb("Name",  x=20, y=10, page=1), _wb("Score", x=120, y=10, page=1),
        _wb("Sam",   x=20, y=40, page=1), _wb("90",    x=120, y=40, page=1),
        _wb("Lee",   x=20, y=70, page=1), _wb("85",    x=120, y=70, page=1),
    ]
    tables = reconstruct_tables(p0 + p1, page_count=2)
    assert len(tables) == 2
    pages = {t.page for t in tables}
    assert pages == {0, 1}


def test_confidence_propagates_from_word_to_cell() -> None:
    """Body-cell confidence ≈ ocr_conf × geometric_conf."""
    boxes = [
        _wb("H1", x=20, y=10), _wb("H2", x=120, y=10),
        _wb("a",  x=20, y=40, conf=1.0), _wb("b", x=120, y=40, conf=0.5),
    ]
    tables = reconstruct_tables(boxes, page_count=1)
    body_cells = [c for c in tables[0].cells if c.row == 1]
    confs = {c.col: c.confidence for c in body_cells}
    # col 0 has full confidence; col 1 has 0.5 OCR conf, both well-centered.
    assert confs[0] > 0.5
    assert confs[1] < confs[0]
    assert confs[1] >= 0.5 * 0.2  # at minimum, ocr * geometric_floor


def test_two_vertical_tables_same_page() -> None:
    """Large Y-gap splits the page into two reconstructed tables."""
    block1 = [
        _wb("A", x=20, y=10), _wb("B", x=120, y=10),
        _wb("1", x=20, y=25), _wb("2", x=120, y=25),
    ]
    block2 = [
        _wb("U", x=20, y=300), _wb("V", x=120, y=300),
        _wb("x", x=20, y=315), _wb("y", x=120, y=315),
    ]
    tables = reconstruct_tables(block1 + block2, page_count=1)
    assert len(tables) == 2
    assert all(t.n_cols == 2 for t in tables)
    assert all(t.page == 0 for t in tables)


def test_too_few_boxes_returns_no_table() -> None:
    """Below MIN rows × cols, skip the page."""
    tables = reconstruct_tables([_wb("just one", x=10, y=10)], page_count=1)
    assert tables == []


def test_inter_column_y_tolerance_merges_offset_date() -> None:
    """Date/amount cells that are vertically centred inside a tall cell while
    the adjacent description text starts at the top should land in the same
    reconstructed row, not in a separate row below.

    Layout (h=10 words, 4-col bank-statement style):
      y=10: header row (Date, Desc, Amount, Balance)
      y=40: description line 1 only  (x=80-180)
      y=55: date (x=0-30), description line 2 (x=80-180), amount (x=200-240),
            balance (x=260-300)
      y=90: next transaction (all 4 cols at same y)

    The date at y=55 is 15 pt below desc line 1 at y=40.  With h_med≈10 the
    old strict tolerance (0.5×10=5) would split them; the new inter-column
    tolerance (1.5×10=15) keeps them together.
    """
    boxes = [
        # Header
        _wb("Date",    x=0,   y=10, w=30),
        _wb("Desc",    x=80,  y=10, w=100),
        _wb("Amount",  x=200, y=10, w=40),
        _wb("Balance", x=260, y=10, w=40),
        # Transaction 1 — description starts at y=40, date/amount at y=55
        _wb("desc pt1",  x=80,  y=40, w=100),
        _wb("01/01",     x=0,   y=55, w=30),
        _wb("desc pt2",  x=80,  y=55, w=100),
        _wb("50.00",     x=200, y=55, w=40),
        _wb("950.00",    x=260, y=55, w=40),
        # Transaction 2 — normal single-line row
        _wb("02/01",     x=0,   y=90, w=30),
        _wb("short",     x=80,  y=90, w=60),
        _wb("20.00",     x=200, y=90, w=40),
        _wb("930.00",    x=260, y=90, w=40),
        # Transaction 3
        _wb("03/01",     x=0,   y=120, w=30),
        _wb("another",   x=80,  y=120, w=60),
        _wb("10.00",     x=200, y=120, w=40),
        _wb("920.00",    x=260, y=120, w=40),
    ]
    tables = reconstruct_tables(boxes, page_count=1)
    assert len(tables) == 1
    t = tables[0]
    # 4 rows total: 1 header + 3 body.  desc pt1 must be in the SAME row as
    # the date, not in a separate row of its own.
    assert t.n_rows == 4, (
        f"expected 4 rows (header+3 body), got {t.n_rows}; "
        "date likely split into its own row"
    )
    # Date cell must be in row 1, col 0.
    date_cells = [c for c in t.cells if c.row == 1 and c.col == 0]
    assert date_cells and "01/01" in date_cells[0].text


def test_synthetic_header_when_no_row_matches_K() -> None:
    """If no row has K columns, synthesize col_1, col_2, … and emit anyway."""
    boxes = [
        # No clear "header" — all rows have different word counts
        _wb("a", x=20, y=10), _wb("b", x=120, y=10),
        _wb("c", x=20, y=40), _wb("d", x=120, y=40),
        _wb("e", x=20, y=70), _wb("f", x=120, y=70),
    ]
    tables = reconstruct_tables(boxes, page_count=1)
    assert len(tables) == 1
    # All rows have 2 cols — first row IS the header in this case.
    assert tables[0].n_cols == 2
