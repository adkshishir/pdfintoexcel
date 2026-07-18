"""Phase 3 tests.

OCR engines aren't invoked here — the engine is dependency-injected via
`extract_ocr(..., recognizer=...)` so we can deterministically assert the
PDF→image→engine→WordBox plumbing without needing tesseract or paddleocr.
"""

from __future__ import annotations

from pathlib import Path

import fitz

from app.pipeline.ocr_pipeline import extract_ocr
from app.pipeline.types import WordBox


def _make_blank_pdf(path: Path, pages: int = 2, w: float = 200.0, h: float = 100.0) -> None:
    """Page-only PDF with no text — forces the OCR path."""
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page(width=w, height=h)
    doc.save(path)
    doc.close()


def test_renders_each_page_and_collects_boxes(tmp_path: Path) -> None:
    pdf = tmp_path / "blank.pdf"
    _make_blank_pdf(pdf, pages=3)

    seen_pages: list[int] = []

    def fake_recognizer(image_path: Path, page_index: int) -> list[WordBox]:
        seen_pages.append(page_index)
        # Return one synthetic word per page in image-pixel coords.
        return [WordBox(text=f"p{page_index}", x=10, y=20, w=30, h=10,
                        page=page_index, confidence=0.9)]

    boxes, page_count = extract_ocr(pdf, mode="fast", recognizer=fake_recognizer)

    assert page_count == 3
    assert seen_pages == [0, 1, 2]
    assert len(boxes) == 3

    # The pipeline must convert image-space coords back to PDF points.
    # fast mode = 200 dpi → scale = 72/200 = 0.36
    assert abs(boxes[0].x - 10 * 72 / 200) < 1e-6
    assert boxes[0].text == "p0"
    assert boxes[0].confidence == 0.9


def test_page_indices_filter(tmp_path: Path) -> None:
    pdf = tmp_path / "blank.pdf"
    _make_blank_pdf(pdf, pages=4)

    seen: list[int] = []

    def fake_recognizer(image_path: Path, page_index: int) -> list[WordBox]:
        seen.append(page_index)
        return []

    extract_ocr(pdf, mode="fast", page_indices=[1, 3], recognizer=fake_recognizer)
    assert seen == [1, 3]


def test_fast_mode_uses_expected_dpi(tmp_path: Path) -> None:
    """Fast mode renders at 200 DPI (recognizer is used in fast mode only).

    Accurate mode uses the adaptive path which hardcodes PaddleOCR/Tesseract
    and ignores the recognizer arg, so it cannot be tested with a fake.
    """
    pdf = tmp_path / "blank.pdf"
    _make_blank_pdf(pdf, pages=1, w=400.0, h=200.0)

    captured_sizes: list[tuple[int, int]] = []

    def fake_recognizer(image_path: Path, page_index: int) -> list[WordBox]:
        from PIL import Image
        with Image.open(image_path) as img:
            captured_sizes.append(img.size)
        return []

    extract_ocr(pdf, mode="fast", recognizer=fake_recognizer)

    fast_w, fast_h = captured_sizes[0]
    # fast mode = 200 DPI on a 400pt-wide page → 400 * 200/72 ≈ 1111px
    assert fast_w > 1000 and fast_w < 1300


def test_orchestrator_routes_scanned_pdf_through_ocr_then_reconstruct(
    tmp_path: Path, monkeypatch
) -> None:
    """End-to-end: scanned PDF → OCR → reconstruction → xlsx."""
    from app.pipeline import orchestrator

    pdf = tmp_path / "scanned.pdf"
    _make_blank_pdf(pdf, pages=2, w=400.0, h=300.0)

    called = {"n": 0}

    def fake_extract_ocr(path, *, mode, page_indices=None, recognizer=None, **kwargs):  # noqa: ANN001, ANN003
        called["n"] += 1
        # Return a coherent table with header + 3 body rows (cleaner's
        # MIN_TABLE_ROWS = 3 floor).
        return ([
            WordBox("Name",   20, 10, 40, 10, page=0, confidence=0.95),
            WordBox("Qty",   120, 10, 20, 10, page=0, confidence=0.95),
            WordBox("Price", 220, 10, 40, 10, page=0, confidence=0.95),
            WordBox("Apple",  20, 40, 40, 10, page=0, confidence=0.9),
            WordBox("3",     125, 40, 10, 10, page=0, confidence=0.9),
            WordBox("1.20",  220, 40, 30, 10, page=0, confidence=0.9),
            WordBox("Pear",   20, 70, 40, 10, page=0, confidence=0.9),
            WordBox("5",     125, 70, 10, 10, page=0, confidence=0.9),
            WordBox("0.40",  220, 70, 30, 10, page=0, confidence=0.9),
            WordBox("Plum",   20, 100, 40, 10, page=0, confidence=0.9),
            WordBox("12",    120, 100, 20, 10, page=0, confidence=0.9),
            WordBox("0.80",  220, 100, 30, 10, page=0, confidence=0.9),
        ], 2)

    monkeypatch.setattr(orchestrator, "extract_ocr", fake_extract_ocr)

    out = tmp_path / "out.xlsx"
    result = orchestrator.run_pipeline(pdf, out, mode="fast")
    assert called["n"] == 1
    assert result.pdf_type == "scanned"
    assert len(result.tables) == 1
    assert result.mean_confidence > 0.8  # mean of OCR confidences
    assert "ocr_ms" in result.timings_ms and "reconstruct_ms" in result.timings_ms
    assert out.exists() and out.stat().st_size > 0
