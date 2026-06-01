"""OCR engine factory.

Picks the configured engine and provides an automatic fallback chain. Paddle
instances are cached per language inside `paddle_engine`; Tesseract is cheap
to spin up per call.
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.config import get_settings
from app.ocr.base import OcrEngine
from app.pipeline.types import WordBox

log = logging.getLogger(__name__)


def recognize_with_fallback(
    image_path: Path,
    page_index: int,
    *,
    tesseract_langs: str | None = None,
    paddle_lang: str | None = None,
) -> list[WordBox]:
    """Try primary engine; on exception, fall back to Tesseract.

    Keyword args are threaded from the job / pipeline so multilingual OCR
    honours Tesseract ``nep+eng``-style lists and the matching Paddle code.
    """
    from app.ocr.lang_resolve import resolve_paddle_lang, resolve_tesseract_langs
    from app.ocr.paddle_engine import PaddleEngine
    from app.ocr.tesseract_engine import TesseractEngine

    settings = get_settings()
    tess = resolve_tesseract_langs(tesseract_langs)
    paddle = resolve_paddle_lang(paddle_lang, tess)

    if settings.ocr_engine == "paddle":
        primary: OcrEngine = PaddleEngine(lang=paddle)
        try:
            return primary.recognize_page(image_path, page_index)
        except Exception as e:
            fb = TesseractEngine(lang=tess)
            log.warning(
                "OCR primary engine paddle failed (%s); falling back to tesseract (%s)",
                e,
                tess,
            )
            return fb.recognize_page(image_path, page_index)

    primary = TesseractEngine(lang=tess)
    return primary.recognize_page(image_path, page_index)


__all__ = ["OcrEngine", "recognize_with_fallback"]
