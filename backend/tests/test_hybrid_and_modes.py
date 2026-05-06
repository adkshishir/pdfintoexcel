"""Phase 6 — hybrid pipeline + mode flag.

Hybrid: a PDF with some text-layer pages and some image-only pages should
route each page through the right extractor and combine WordBoxes into a
single reconstruction pass.

Modes: `accurate` enables continuation merging; `fast` keeps it off.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from app.pipeline import orchestrator
from app.pipeline.types import WordBox


def _make_mixed_pdf(path: Path) -> None:
    """Two pages with text + one blank page (image-only / no text layer)."""
    doc = fitz.open()

    # Page 0 — text table
    p0 = doc.new_page(width=400, height=300)
    p0.insert_text((40, 40), "Date")
    p0.insert_text((180, 40), "Amount")
    p0.insert_text((40, 70), "01/01/2025")
    p0.insert_text((180, 70), "10")
    p0.insert_text((40, 100), "02/01/2025")
    p0.insert_text((180, 100), "20")
    p0.insert_text((40, 130), "03/01/2025")
    p0.insert_text((180, 130), "30")

    # Page 1 — text table (more text rows for type inference)
    p1 = doc.new_page(width=400, height=300)
    p1.insert_text((40, 40), "Date")
    p1.insert_text((180, 40), "Amount")
    p1.insert_text((40, 70), "04/01/2025")
    p1.insert_text((180, 70), "40")
    p1.insert_text((40, 100), "05/01/2025")
    p1.insert_text((180, 100), "50")
    p1.insert_text((40, 130), "06/01/2025")
    p1.insert_text((180, 130), "60")

    # Page 2 — blank (no text → forces hybrid)
    doc.new_page(width=400, height=300)

    doc.save(path)
    doc.close()


def test_hybrid_routes_each_page_correctly(tmp_path: Path, monkeypatch) -> None:
    pdf = tmp_path / "mixed.pdf"
    _make_mixed_pdf(pdf)

    seen_ocr_pages: list[list[int]] = []

    def fake_extract_ocr(path, *, mode, page_indices=None, recognizer=None):  # noqa: ANN001
        seen_ocr_pages.append(list(page_indices) if page_indices is not None else [])
        # Return a coherent table for the OCR'd page so reconstruction can build it.
        target = (page_indices or [2])[0]
        return ([
            WordBox("Date",   20, 10, 40, 10, page=target, confidence=0.9),
            WordBox("Amount", 180, 10, 40, 10, page=target, confidence=0.9),
            WordBox("07/01/2025", 20, 40, 50, 10, page=target, confidence=0.9),
            WordBox("70",     185, 40, 20, 10, page=target, confidence=0.9),
            WordBox("08/01/2025", 20, 70, 50, 10, page=target, confidence=0.9),
            WordBox("80",     185, 70, 20, 10, page=target, confidence=0.9),
            WordBox("09/01/2025", 20, 100, 50, 10, page=target, confidence=0.9),
            WordBox("90",     185, 100, 20, 10, page=target, confidence=0.9),
        ], 3)

    monkeypatch.setattr(orchestrator, "extract_ocr", fake_extract_ocr)

    out = tmp_path / "out.xlsx"
    result = orchestrator.run_pipeline(pdf, out, mode="fast")

    assert result.pdf_type == "hybrid"
    # OCR was called only for page 2 (the blank one).
    assert seen_ocr_pages == [[2]]
    # All three pages contributed; same headers everywhere → one merged sheet.
    assert len(result.tables) == 1
    assert result.tables[0].headers == ["Date", "Amount"]
    # 3 rows per page × 3 pages = 9 body rows.
    assert len(result.tables[0].rows) == 9


def test_pure_digital_does_not_call_ocr(tmp_path: Path, monkeypatch) -> None:
    pdf = tmp_path / "digital.pdf"
    doc = fitz.open()
    p = doc.new_page(width=400, height=400)
    p.insert_text((40, 40), "Item")
    p.insert_text((180, 40), "Quantity")
    rows = [("Apple", "3"), ("Banana", "5"), ("Cherry", "12"),
            ("Durian", "1"), ("Elderberry", "20")]
    for i, (name, qty) in enumerate(rows):
        p.insert_text((40,  70 + 30*i), name)
        p.insert_text((180, 70 + 30*i), qty)
    doc.save(pdf)
    doc.close()

    ocr_called = {"n": 0}

    def fake_extract_ocr(*a, **kw):  # noqa: ANN001, ANN002
        ocr_called["n"] += 1
        return ([], 0)

    monkeypatch.setattr(orchestrator, "extract_ocr", fake_extract_ocr)

    orchestrator.run_pipeline(pdf, tmp_path / "out.xlsx", mode="fast")
    assert ocr_called["n"] == 0


@pytest.fixture(scope="module")
def monzo_pdf() -> Path:
    p = Path(__file__).resolve().parents[2] / "MonzoBus.pdf"
    if not p.exists():
        pytest.skip("MonzoBus.pdf fixture not present")
    return p


def test_accurate_mode_folds_wrapped_descriptions(tmp_path: Path, monzo_pdf: Path) -> None:
    """Accurate mode should produce *fewer* rows than fast mode on
    MonzoBus.pdf because wrapped transaction descriptions get folded."""
    fast = orchestrator.run_pipeline(monzo_pdf, tmp_path / "fast.xlsx", mode="fast")
    acc  = orchestrator.run_pipeline(monzo_pdf, tmp_path / "acc.xlsx",  mode="accurate")

    assert fast.tables and acc.tables
    fast_rows = sum(len(t.rows) for t in fast.tables)
    acc_rows  = sum(len(t.rows) for t in acc.tables)
    # Continuation merge should drop ≥ 20% of rows on this fixture.
    assert acc_rows < fast_rows * 0.85, f"fast={fast_rows} accurate={acc_rows}"
