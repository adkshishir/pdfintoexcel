"""OCR engine factory.

Picks the configured engine and provides an automatic fallback chain. The
engine is held as a module-level singleton so warm-up cost (PaddleOCR's
model loading) is paid once per worker process.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from app.config import get_settings
from app.ocr.base import OcrEngine
from app.pipeline.types import WordBox

log = logging.getLogger(__name__)


@lru_cache
def get_primary_engine() -> OcrEngine:
    name = get_settings().ocr_engine
    if name == "paddle":
        from app.ocr.paddle_engine import PaddleEngine
        return PaddleEngine()
    if name == "tesseract":
        from app.ocr.tesseract_engine import TesseractEngine
        return TesseractEngine()
    raise ValueError(f"unknown OCR engine: {name}")


@lru_cache
def get_fallback_engine() -> OcrEngine:
    """Always Tesseract. Cheap to import, present in worker image."""
    from app.ocr.tesseract_engine import TesseractEngine
    return TesseractEngine()


def recognize_with_fallback(image_path: Path, page_index: int) -> list[WordBox]:
    """Try primary engine; on exception, fall back to Tesseract."""
    primary = get_primary_engine()
    try:
        return primary.recognize_page(image_path, page_index)
    except Exception as e:
        if isinstance(primary, type(get_fallback_engine())):
            # Already Tesseract — no fallback to try.
            raise
        log.warning("OCR primary engine %s failed (%s); falling back to tesseract",
                    primary.name, e)
        return get_fallback_engine().recognize_page(image_path, page_index)


__all__ = ["OcrEngine", "get_primary_engine", "get_fallback_engine", "recognize_with_fallback"]
