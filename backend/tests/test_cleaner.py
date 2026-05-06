"""Phase 5 cleaner tests — independent of any PDF/OCR machinery."""

from __future__ import annotations

from app.pipeline.cleaner import clean_tables
from app.pipeline.types import RawCell, RawTable


def _table(page: int, cells: list[tuple[int, int, str]]) -> RawTable:
    raw_cells = [RawCell(row=r, col=c, text=t) for (r, c, t) in cells]
    n_rows = max(r for r, _, _ in cells) + 1
    n_cols = max(c for _, c, _ in cells) + 1
    return RawTable(page=page, bbox=(0, 0, 100, 100),
                    cells=raw_cells, n_rows=n_rows, n_cols=n_cols)


def test_drops_table_too_few_rows() -> None:
    t = _table(0, [
        (0, 0, "A"), (0, 1, "B"),
        (1, 0, "x"), (1, 1, "y"),
    ])
    assert clean_tables([t]) == []  # 1 body row < MIN_TABLE_ROWS=3


def test_drops_table_with_prose_header() -> None:
    t = _table(0, [
        (0, 0, "This is a long sentence pretending to be a header label"),
        (0, 1, "B"),
        (1, 0, "x"), (1, 1, "y"),
        (2, 0, "x2"), (2, 1, "y2"),
        (3, 0, "x3"), (3, 1, "y3"),
    ])
    assert clean_tables([t]) == []  # header > MAX_HEADER_LEN


def test_drops_layout_coincidence_table() -> None:
    """A table where every column has middling fill rate (~50%) is layout
    artifact, not a real table."""
    t = _table(0, [
        (0, 0, "X"), (0, 1, "Y"),
        # Body: alternate which column is filled — every column ~50%, no
        # consistently-filled or consistently-empty column.
        (1, 0, "a"),
        (2, 1, "b"),
        (3, 0, "c"),
        (4, 1, "d"),
        (5, 0, "e"),
        (6, 1, "f"),
    ])
    assert clean_tables([t]) == []


def test_keeps_real_table() -> None:
    """One column ≥70% filled → real table."""
    t = _table(0, [
        (0, 0, "Date"), (0, 1, "Amount"),
        (1, 0, "01/01/2025"),  (1, 1, "10"),
        (2, 0, "02/01/2025"),  (2, 1, "20"),
        (3, 0, "03/01/2025"),  (3, 1, "30"),
    ])
    out = clean_tables([t])
    assert len(out) == 1
    assert out[0].headers == ["Date", "Amount"]
    assert out[0].column_types == ["date", "number"]


def test_merges_consecutive_same_header_tables() -> None:
    """Multi-page table with identical headers → one sheet."""
    base_cells = [
        (0, 0, "Date"), (0, 1, "Amount"),
        (1, 0, "01/01/2025"),  (1, 1, "10"),
        (2, 0, "02/01/2025"),  (2, 1, "20"),
        (3, 0, "03/01/2025"),  (3, 1, "30"),
    ]
    t1 = _table(0, base_cells)
    t2 = _table(1, [(0, 0, "Date"), (0, 1, "Amount"),
                    (1, 0, "04/01/2025"), (1, 1, "40"),
                    (2, 0, "05/01/2025"), (2, 1, "50"),
                    (3, 0, "06/01/2025"), (3, 1, "60")])
    out = clean_tables([t1, t2])
    assert len(out) == 1
    assert len(out[0].rows) == 6
    assert "merged" in out[0].sheet_name


def test_keeps_distinct_tables_separate() -> None:
    t1 = _table(0, [
        (0, 0, "Date"), (0, 1, "Amount"),
        (1, 0, "1/1"), (1, 1, "10"),
        (2, 0, "2/1"), (2, 1, "20"),
        (3, 0, "3/1"), (3, 1, "30"),
    ])
    t2 = _table(1, [
        (0, 0, "Item"), (0, 1, "Qty"),
        (1, 0, "Apple"), (1, 1, "1"),
        (2, 0, "Pear"), (2, 1, "2"),
        (3, 0, "Plum"), (3, 1, "3"),
    ])
    out = clean_tables([t1, t2])
    assert len(out) == 2


def test_continuation_merging_off_by_default() -> None:
    """An empty-Date row stays as-is (off by default in Phase 5)."""
    t = _table(0, [
        (0, 0, "Date"), (0, 1, "Amount"),
        (1, 0, "01/01/2025"), (1, 1, "10"),
        (2, 1, "wrap"),                      # empty Date
        (3, 0, "02/01/2025"), (3, 1, "20"),
        (4, 0, "03/01/2025"), (4, 1, "30"),
    ])
    out = clean_tables([t], merge_continuations=False)
    assert len(out) == 1
    assert len(out[0].rows) == 4   # 4 body rows preserved


def test_continuation_merging_on_folds_correctly() -> None:
    t = _table(0, [
        (0, 0, "Date"), (0, 1, "Desc"),
        (1, 0, "01/01/2025"), (1, 1, "first"),
        (2, 1, "wrap"),                      # empty Date → fold into row 1
        (3, 0, "02/01/2025"), (3, 1, "second"),
        (4, 0, "03/01/2025"), (4, 1, "third"),
    ])
    out = clean_tables([t], merge_continuations=True)
    assert len(out) == 1
    # Row 1 should now have Desc = "first wrap"
    assert out[0].rows[0] == ["01/01/2025", "first wrap"]


def test_forward_preamble_first_row() -> None:
    """Description-first layout: first body row has no date (preamble), next
    row has date + continuation.  The two should merge into one output row."""
    t = _table(0, [
        (0, 0, "Date"),       (0, 1, "Desc"),       (0, 2, "Amount"),
        # First logical transaction: description wraps, date is on line 2.
        (1, 1, "long desc start"),                              # no Date
        (2, 0, "01/01/2025"), (2, 1, "long desc end"), (2, 2, "50.00"),
        # Second transaction (normal).
        (3, 0, "02/01/2025"), (3, 1, "short"),       (3, 2, "20.00"),
        # Third transaction (normal).
        (4, 0, "03/01/2025"), (4, 1, "another"),     (4, 2, "30.00"),
    ])
    out = clean_tables([t], merge_continuations=True)
    assert len(out) == 1
    rows = out[0].rows
    # Preamble merged into its anchor row → 3 output rows
    assert len(rows) == 3
    assert rows[0][0] == "01/01/2025"
    assert "long desc start" in rows[0][1]
    assert "long desc end" in rows[0][1]
    assert rows[0][2] == "50.00"


def test_forward_preamble_multi_line() -> None:
    """Two preamble lines before the first anchor row — both should fold in."""
    t = _table(0, [
        (0, 0, "Date"),       (0, 1, "Desc"),
        (1, 1, "line one"),                    # no Date
        (2, 1, "line two"),                    # no Date
        (3, 0, "01/01/2025"), (3, 1, "line three"),
        (4, 0, "02/01/2025"), (4, 1, "other"),
        (5, 0, "03/01/2025"), (5, 1, "third"),
    ])
    out = clean_tables([t], merge_continuations=True)
    assert len(out) == 1
    rows = out[0].rows
    assert len(rows) == 3
    assert rows[0][0] == "01/01/2025"
    assert "line one" in rows[0][1]
    assert "line two" in rows[0][1]
    assert "line three" in rows[0][1]


def test_type_inference_dates() -> None:
    t = _table(0, [
        (0, 0, "Date"), (0, 1, "Note"),
        (1, 0, "01/01/2025"), (1, 1, "x"),
        (2, 0, "02/01/2025"), (2, 1, "y"),
        (3, 0, "03/01/2025"), (3, 1, "z"),
    ])
    out = clean_tables([t])
    assert out[0].column_types == ["date", "text"]


def test_type_inference_numbers_with_currency_and_commas() -> None:
    t = _table(0, [
        (0, 0, "Item"), (0, 1, "Total"),
        (1, 0, "A"), (1, 1, "£1,000.00"),
        (2, 0, "B"), (2, 1, "£250.50"),
        (3, 0, "C"), (3, 1, "£42.00"),
    ])
    out = clean_tables([t])
    assert out[0].column_types == ["text", "number"]
