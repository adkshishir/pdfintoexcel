"""Map API / job OCR language hints to engine-specific codes."""

from __future__ import annotations

import re

from app.config import get_settings

_TESS_LANG_TOKEN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")


def validate_tesseract_lang_list(raw: str) -> str:
    """Return a cleaned Tesseract `lang` string or raise ValueError.

    Expected form: ``eng``, ``nep``, ``nep+eng``, ``hin+eng``, etc.
    """
    s = raw.strip()
    if not s:
        raise ValueError("empty language list")
    parts = [p.strip() for p in s.split("+") if p.strip()]
    if not parts:
        raise ValueError("no languages after split")
    for p in parts:
        if not _TESS_LANG_TOKEN.match(p):
            raise ValueError(f"invalid tessdata language token: {p!r}")
    return "+".join(parts)


def resolve_tesseract_langs(api_value: str | None, *, fallback: str | None = None) -> str:
    fb = fallback or get_settings().ocr_default_tesseract_lang
    if api_value is None or not str(api_value).strip():
        return fb.strip() or "eng"
    return validate_tesseract_lang_list(str(api_value))


def resolve_paddle_lang(
    paddle_explicit: str | None,
    tesseract_langs: str,
    *,
    fallback: str | None = None,
) -> str:
    """Pick a PaddleOCR ``lang`` code.

    If the client sets ``paddle_explicit``, that wins.
    Otherwise we infer Devanagari-family codes from Tesseract hints (common
    for Nepali bilingual jobs that pass ``nep+eng``).
    """
    if paddle_explicit and str(paddle_explicit).strip():
        return str(paddle_explicit).strip()

    fb = fallback or get_settings().ocr_default_paddle_lang
    parts = {p.strip().lower() for p in tesseract_langs.split("+") if p.strip()}
    # Order matters — first match wins.
    if {"nep"} & parts or any(p.startswith("nep") for p in parts):
        return "ne"
    if {"hin", "hi", "san", "dev"} & parts or any(p.startswith(("hin", "dev")) for p in parts):
        return "hi"
    if any("chi_tra" in p for p in parts):
        return "chinese_cht"
    if any(p.startswith("chi") or p in ("ch",) for p in parts):
        return "ch"
    if any(p.startswith("jpn") for p in parts):
        return "japan"
    if any(p.startswith("kor") for p in parts):
        return "korean"
    if any(p.startswith("ara") for p in parts):
        return "arabic"
    if any(p.startswith(("rus", "ukr", "bul", "srp", "bel")) for p in parts):
        return "cyrillic"
    if any(p.startswith(("fra", "fre")) for p in parts):
        return "french"
    if any(p.startswith("deu") or p.startswith("ger") for p in parts):
        return "german"

    return fb.strip() or "en"
