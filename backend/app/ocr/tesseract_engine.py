"""Tesseract OCR engine.

Used as both a primary engine (when configured) and the auto-fallback when
PaddleOCR errors. Wraps `pytesseract.image_to_data` to get word-level
bounding boxes + per-word confidence.

The `tesseract` binary must be on PATH (provided by `Dockerfile.worker`).
"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image

from app.ocr.base import OcrEngine
from app.pipeline.types import WordBox

log = logging.getLogger(__name__)

# Tesseract returns confidence as 0–100 (or -1 for "no confidence reported").
# We normalize to 0.0–1.0 and treat -1 as 0.
_MIN_TEXT_LEN = 1


class TesseractEngine(OcrEngine):
    name = "tesseract"

    def __init__(self, *, lang: str = "eng", psm: int = 6) -> None:
        # PSM 6 = "Assume a single uniform block of text" — good default for
        # table-like layouts. Phase 4 may pass a different PSM per region.
        self.lang = lang
        self.psm = psm

    def recognize_page(self, image_path: Path, page_index: int) -> list[WordBox]:
        # Local import so this module can be imported on machines without
        # the tesseract binary (CI/lint).
        import pytesseract

        config = f"--psm {self.psm}"
        with Image.open(image_path) as img:
            data = pytesseract.image_to_data(
                img, lang=self.lang, config=config,
                output_type=pytesseract.Output.DICT,
            )

        boxes: list[WordBox] = []
        n = len(data["text"])
        for i in range(n):
            text = (data["text"][i] or "").strip()
            if len(text) < _MIN_TEXT_LEN:
                continue
            conf_raw = float(data["conf"][i])
            conf = max(0.0, conf_raw / 100.0) if conf_raw >= 0 else 0.0
            boxes.append(WordBox(
                text=text,
                x=float(data["left"][i]),
                y=float(data["top"][i]),
                w=float(data["width"][i]),
                h=float(data["height"][i]),
                page=page_index,
                confidence=conf,
            ))
        log.debug("tesseract page %d: %d boxes", page_index, len(boxes))
        return boxes
