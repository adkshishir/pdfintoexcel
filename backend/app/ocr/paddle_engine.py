"""PaddleOCR engine.

PaddleOCR ships its own detector + recognizer pipeline and returns polygon
bounding boxes. We convert to axis-aligned (x, y, w, h) for consistency
with the rest of the pipeline.

Models are downloaded on first call into `~/.paddleocr` (mounted as the
`paddle-models` volume in compose so cold starts only happen once per host).
"""

from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock

from app.ocr.base import OcrEngine
from app.pipeline.types import WordBox

log = logging.getLogger(__name__)

_paddle_lock = Lock()
_paddle_by_lang: dict[str, object] = {}


def _get_paddle(lang: str):  # noqa: ANN202 — paddleocr typed lazily
    """Lazy + cached per language. Initialization is expensive (~3s each)."""
    key = (lang or "en").strip() or "en"
    inst = _paddle_by_lang.get(key)
    if inst is not None:
        return inst
    with _paddle_lock:
        if key not in _paddle_by_lang:
            from paddleocr import PaddleOCR

            _paddle_by_lang[key] = PaddleOCR(use_angle_cls=True, lang=key, show_log=False)
    return _paddle_by_lang[key]


class PaddleEngine(OcrEngine):
    name = "paddle"

    def __init__(self, *, lang: str = "en") -> None:
        self.lang = lang

    def recognize_page(self, image_path: Path, page_index: int) -> list[WordBox]:
        ocr = _get_paddle(self.lang)
        result = ocr.ocr(str(image_path), cls=True)
        # PaddleOCR returns: [[[poly, (text, conf)], ...]] for each image.
        # When called on one image we have one outer entry.
        if not result or not result[0]:
            return []

        boxes: list[WordBox] = []
        for entry in result[0]:
            poly, (text, conf) = entry
            text = (text or "").strip()
            if not text:
                continue
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            x0, x1 = min(xs), max(xs)
            y0, y1 = min(ys), max(ys)
            boxes.append(
                WordBox(
                    text=text,
                    x=float(x0),
                    y=float(y0),
                    w=float(x1 - x0),
                    h=float(y1 - y0),
                    page=page_index,
                    confidence=float(conf),
                )
            )
        log.debug("paddle page %d: %d boxes", page_index, len(boxes))
        return boxes
