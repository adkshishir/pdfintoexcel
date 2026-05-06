"""OCR engine interface.

Concrete engines (Paddle, Tesseract) implement `OcrEngine`. The pipeline
selects an engine via `app.config.Settings.ocr_engine` and falls back to
the next one on failure.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.pipeline.types import WordBox


class OcrEngine(ABC):
    name: str

    @abstractmethod
    def recognize_page(self, image_path: Path, page_index: int) -> list[WordBox]:
        """Return word-level boxes for one rendered page image."""
