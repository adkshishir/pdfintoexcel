"""OCR language hint resolution (Tesseract + Paddle)."""

from __future__ import annotations

import pytest

from app.ocr.lang_resolve import (
    resolve_paddle_lang,
    resolve_tesseract_langs,
    validate_tesseract_lang_list,
)


def test_validate_tesseract_accepts_plus_list() -> None:
    assert validate_tesseract_lang_list("  nep+eng  ") == "nep+eng"


def test_validate_tesseract_rejects_bad_token() -> None:
    with pytest.raises(ValueError):
        validate_tesseract_lang_list("nep+eng;rm")


def test_resolve_tesseract_defaults() -> None:
    assert resolve_tesseract_langs(None) == "eng"


def test_resolve_paddle_inferrs_from_tesseract_string() -> None:
    tess = validate_tesseract_lang_list("nep+eng")
    assert resolve_paddle_lang(None, tess) == "ne"
    tess2 = validate_tesseract_lang_list("hin+eng")
    assert resolve_paddle_lang(None, tess2) == "hi"


def test_resolve_paddle_explicit_wins_over_inference() -> None:
    tess = validate_tesseract_lang_list("nep+eng")
    assert resolve_paddle_lang("en", tess) == "en"
