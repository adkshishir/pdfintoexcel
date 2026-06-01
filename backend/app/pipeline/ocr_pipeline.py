"""Stage 2b — OCR pipeline.

Renders each PDF page to a high-DPI image (PyMuPDF), runs the configured
OCR engine, and returns WordBox[]. The DPI is settings-driven so accurate
mode can pay more for sharper boxes.

The reconstruction algorithm (Phase 4) consumes these boxes; this module
deliberately does *not* attempt table layout — that's Phase 4's job.
"""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Callable
from pathlib import Path

import fitz  # PyMuPDF

from app.ocr import recognize_with_fallback
from app.pipeline.types import Mode, WordBox

log = logging.getLogger(__name__)

# DPI per mode. PaddleOCR/Tesseract both top out around 300 DPI for accuracy
# vs runtime; below ~200 DPI thin glyphs lose strokes.
_DPI_BY_MODE: dict[Mode, int] = {"fast": 200, "accurate": 300}


def extract_ocr(
    pdf_path: Path,
    *,
    mode: Mode = "fast",
    page_indices: list[int] | None = None,
    recognizer: Callable[..., list[WordBox]] = recognize_with_fallback,
) -> tuple[list[WordBox], int]:
    """Return (all_word_boxes, page_count).

    Args:
      page_indices: if given, only OCR these pages. Used by hybrid mode to
        OCR only the pages the digital path failed on.
      recognizer: injectable for tests so we don't need a real OCR engine.
    """
    dpi = _DPI_BY_MODE[mode]
    boxes: list[WordBox] = []

    with fitz.open(pdf_path) as doc:
        page_count = len(doc)
        targets = page_indices if page_indices is not None else range(page_count)
        with tempfile.TemporaryDirectory(prefix="ocr_") as tmp:
            tmp_dir = Path(tmp)
            for page_idx in targets:
                if page_idx < 0 or page_idx >= page_count:
                    log.warning("ocr: page %d out of range, skipping", page_idx)
                    continue
                page = doc[page_idx]
                # Matrix scales PyMuPDF's default 72 DPI rendering up to `dpi`.
                zoom = dpi / 72.0
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
                img_path = tmp_dir / f"page-{page_idx:04d}.png"
                pix.save(img_path)

                page_boxes = recognizer(img_path, page_idx)
                # Convert image-space pixels back to PDF user space (points)
                # so coords are comparable with digital extraction.
                scale = 72.0 / dpi
                for b in page_boxes:
                    boxes.append(WordBox(
                        text=b.text,
                        x=b.x * scale,
                        y=b.y * scale,
                        w=b.w * scale,
                        h=b.h * scale,
                        page=page_idx,
                        confidence=b.confidence,
                    ))
                log.info("ocr page %d: %d boxes", page_idx, len(page_boxes))

    return boxes, page_count
