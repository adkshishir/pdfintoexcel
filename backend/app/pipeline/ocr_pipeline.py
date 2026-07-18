"""Stage 2b — OCR pipeline.

Renders each PDF page to a high-DPI image (PyMuPDF), runs the configured
OCR engine, and returns WordBox[]. The DPI is settings-driven so accurate
mode can pay more for sharper boxes.

In accurate mode uses *adaptive DPI*: renders at 200 DPI + PaddleOCR first.
If per-page average confidence falls below ``ADAPTIVE_LOW_CONFIDENCE``,
re-renders at 300 DPI + Tesseract.  Fast mode uses fixed 200 DPI.

The reconstruction algorithm (Phase 4) consumes these boxes; this module
deliberately does *not* attempt table layout — that is Phase 4's job.
"""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Callable
from pathlib import Path

import fitz  # PyMuPDF

from app.pipeline.types import Mode, WordBox

log = logging.getLogger(__name__)

# DPI per mode for the non-adaptive (fast) path.
_DPI_BY_MODE: dict[Mode, int] = {"fast": 200, "accurate": 300}

# Adaptive: if average confidence < threshold at 200 DPI, redo at 300 DPI.
ADAPTIVE_LOW_CONFIDENCE = 0.75


def extract_ocr(
    pdf_path: Path,
    *,
    mode: Mode = "fast",
    page_indices: list[int] | None = None,
    recognizer: Callable[..., list[WordBox]] | None = None,
    progress: Callable[[str, int | None, dict | None], None] | None = None,
) -> tuple[list[WordBox], int]:
    """Return (all_word_boxes, page_count).

    * **fast** mode — fixed 200 DPI, uses *recognizer* for the engine.
    * **accurate** mode — adaptive DPI (200→300) with per-page confidence
      gating.  The *recognizer* arg is unused in accurate mode because the
      adaptive path calls PaddleOCR / Tesseract directly.

    *recognizer* is kept for backward compat with fast-mode tests.
    """
    boxes: list[WordBox] = []

    with fitz.open(pdf_path) as doc:
        page_count = len(doc)
        targets = page_indices if page_indices is not None else range(page_count)
        with tempfile.TemporaryDirectory(prefix="ocr_") as tmp:
            tmp_dir = Path(tmp)
            for i, page_idx in enumerate(targets):
                if page_idx < 0 or page_idx >= page_count:
                    log.warning("ocr: page %d out of range, skipping", page_idx)
                    continue

                if progress:
                    pct = 10 + int(80 * i / max(len(targets), 1))
                    progress("ocr", pct, {"page": page_idx, "total_pages": len(targets)})

                page = doc[page_idx]

                if mode == "accurate":
                    page_box_list = _ocr_page_adaptive(page, page_idx, tmp_dir)
                else:
                    dpi = _DPI_BY_MODE[mode]
                    page_box_list = _ocr_page_fixed(page, page_idx, dpi, tmp_dir, recognizer)

                boxes.extend(page_box_list)
                log.info("ocr page %d: %d boxes", page_idx, len(page_box_list))

            if progress:
                progress("ocr", 90, {"page": page_idx, "total_pages": len(targets)})

    return boxes, page_count


# ---------------------------------------------------------------------------
# Adaptive DPI — accurate mode only
# ---------------------------------------------------------------------------

def _ocr_page_adaptive(
    page: fitz.Page,
    page_idx: int,
    tmp_dir: Path,
) -> list[WordBox]:
    """200 DPI + PaddleOCR; escalate to 300 DPI + Tesseract if low confidence."""
    from app.ocr.paddle_engine import PaddleEngine
    from app.ocr.tesseract_engine import TesseractEngine

    dpi1 = 200
    zoom1 = dpi1 / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom1, zoom1), alpha=False)
    img_path = tmp_dir / f"p{page_idx:04d}_p1.png"
    pix.save(img_path)
    del pix

    engine = PaddleEngine()
    boxes = engine.recognize_page(img_path, page_idx)

    avg_conf = _average_confidence(boxes)
    if avg_conf >= ADAPTIVE_LOW_CONFIDENCE:
        return [_scale_box(b, 72.0 / dpi1, page_idx) for b in boxes]

    log.info(
        "adaptive pg %d: confidence %.3f < %.2f at 200 DPI, "
        "re-rendering at 300 DPI + Tesseract",
        page_idx, avg_conf, ADAPTIVE_LOW_CONFIDENCE,
    )

    dpi2 = 300
    zoom2 = dpi2 / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom2, zoom2), alpha=False)
    img_path = tmp_dir / f"p{page_idx:04d}_p2.png"
    pix.save(img_path)
    del pix

    engine = TesseractEngine()
    boxes = engine.recognize_page(img_path, page_idx)

    return [_scale_box(b, 72.0 / dpi2, page_idx) for b in boxes]


# ---------------------------------------------------------------------------
# Fixed DPI — fast mode (backward-compatible code path)
# ---------------------------------------------------------------------------

def _ocr_page_fixed(
    page: fitz.Page,
    page_idx: int,
    dpi: int,
    tmp_dir: Path,
    recognizer: Callable[..., list[WordBox]] | None,
) -> list[WordBox]:
    """Render once at *dpi* and OCR with *recognizer*."""
    from app.ocr import recognize_with_fallback

    r = recognizer or recognize_with_fallback
    zoom = dpi / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    img_path = tmp_dir / f"p{page_idx:04d}.png"
    pix.save(img_path)
    del pix

    page_boxes = r(img_path, page_idx)
    scale = 72.0 / dpi
    return [_scale_box(b, scale, page_idx) for b in page_boxes]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _scale_box(b: WordBox, scale: float, page_idx: int) -> WordBox:
    """Convert image-space pixel coords to PDF user-space points."""
    return WordBox(
        text=b.text,
        x=b.x * scale,
        y=b.y * scale,
        w=b.w * scale,
        h=b.h * scale,
        page=page_idx,
        confidence=b.confidence,
    )


def _average_confidence(boxes: list[WordBox]) -> float:
    if not boxes:
        return 0.0
    return sum(b.confidence for b in boxes) / len(boxes)
