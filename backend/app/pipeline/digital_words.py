"""Stage 2a — extract WordBox[] from a digital PDF.

Mirrors `ocr_pipeline.extract_ocr`'s shape so the orchestrator can treat
both sources uniformly. Optional `page_indices` lets hybrid mode pull
words only from the digital pages, leaving the scanned ones for OCR.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

import pdfplumber

from app.pipeline.types import WordBox

log = logging.getLogger(__name__)


def extract_digital_words(
    pdf_path: Path,
    *,
    page_indices: Iterable[int] | None = None,
) -> tuple[list[WordBox], int]:
    """Return (boxes, page_count). pdfplumber gives clean coords in PDF
    user-space points already; no rescaling needed."""
    boxes: list[WordBox] = []
    target_set = set(page_indices) if page_indices is not None else None
    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            if target_set is not None and i not in target_set:
                continue
            for w in page.extract_words(keep_blank_chars=False):
                text = (w["text"] or "").strip()
                if not text:
                    continue
                boxes.append(WordBox(
                    text=text,
                    x=float(w["x0"]),
                    y=float(w["top"]),
                    w=float(w["x1"] - w["x0"]),
                    h=float(w["bottom"] - w["top"]),
                    page=i,
                    confidence=1.0,
                ))
            log.debug("digital page %d: %d words", i, len([b for b in boxes if b.page == i]))
    return boxes, page_count
