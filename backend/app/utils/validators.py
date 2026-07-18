"""Upfront PDF validation at upload time (Section 5 of optimization plan).

Validates the file before enqueueing so bad files fail fast with clear
error codes instead of failing deep inside a worker.
"""

from __future__ import annotations

import logging
from pathlib import Path

import fitz  # PyMuPDF

from app.config import get_settings

log = logging.getLogger(__name__)

MAX_PAGES = 300


class ValidationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message


def validate_pdf(file_path: Path, file_size_mb: float) -> int:
    """Validate a PDF file and return its page count.

    Raises
    ------
    ValidationError
        With a structured error code when the file fails validation:
        - ``file_too_large`` — exceeds max upload size
        - ``corrupt_pdf`` — cannot be opened by PyMuPDF
        - ``password_protected`` — PDF is encrypted and requires a password
        - ``empty_pdf`` — zero pages
        - ``too_many_pages`` — exceeds MAX_PAGES limit
    """
    settings = get_settings()

    if file_size_mb > settings.max_upload_bytes / (1024 * 1024):
        raise ValidationError(
            "file_too_large",
            f"File exceeds {settings.max_upload_bytes / (1024 * 1024):.0f} MB limit.",
        )

    try:
        doc = fitz.open(file_path)
    except Exception as exc:
        raise ValidationError("corrupt_pdf", f"Could not read file as a valid PDF: {exc}")

    if doc.is_encrypted or doc.needs_pass:
        doc.close()
        raise ValidationError("password_protected", "PDF is password-protected and cannot be processed.")

    page_count = doc.page_count
    doc.close()

    if page_count == 0:
        raise ValidationError("empty_pdf", "PDF has no pages.")

    if page_count > MAX_PAGES:
        raise ValidationError(
            "too_many_pages",
            f"PDF exceeds {MAX_PAGES}-page limit (found {page_count} pages).",
        )

    return page_count
