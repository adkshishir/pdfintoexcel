"""PDF type detection.

A PDF is "digital" if at least `MIN_DIGITAL_RATIO` of its pages carry a
useful text layer. Otherwise it's "scanned" (Phase 3 OCR pipeline). A PDF
that mixes the two is "hybrid" — Phase 6 routes it through both paths.

For Phase 2 only `digital` is fully supported. `scanned` and `hybrid`
return the right type so the orchestrator can fail with a precise error.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from app.pipeline.types import PdfType

# A page counts as "having text" if `get_text("text")` yields more than this
# many non-whitespace characters. Tuned to ignore page numbers / headers /
# Acrobat metadata that some scanners stamp onto otherwise-image-only pages.
MIN_PAGE_TEXT_CHARS = 40

# A whole document counts as "digital" when this fraction of pages have text.
MIN_DIGITAL_RATIO = 0.6


@dataclass(frozen=True)
class DetectionResult:
    pdf_type: PdfType
    page_count: int
    text_page_indices: frozenset[int]  # which pages have a usable text layer

    @property
    def pages_with_text(self) -> int:
        return len(self.text_page_indices)

    @property
    def text_ratio(self) -> float:
        return self.pages_with_text / self.page_count if self.page_count else 0.0

    def scanned_page_indices(self) -> frozenset[int]:
        return frozenset(range(self.page_count)) - self.text_page_indices


def detect_pdf_type(pdf_path: Path) -> DetectionResult:
    with fitz.open(pdf_path) as doc:
        n = len(doc)
        text_pages: set[int] = set()
        for i, page in enumerate(doc):
            txt = page.get_text("text") or ""
            if sum(1 for c in txt if not c.isspace()) >= MIN_PAGE_TEXT_CHARS:
                text_pages.add(i)

    if n == 0:
        return DetectionResult("scanned", 0, frozenset())

    ratio = len(text_pages) / n
    if ratio >= MIN_DIGITAL_RATIO:
        # Near-perfect text coverage = pure digital; mixed = hybrid so the
        # orchestrator OCRs only the missing pages.
        kind: PdfType = "digital" if ratio > 0.95 else "hybrid"
        return DetectionResult(kind, n, frozenset(text_pages))
    return DetectionResult("scanned", n, frozenset(text_pages))
