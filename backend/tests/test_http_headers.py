"""Tests for HTTP header helpers."""

from __future__ import annotations

from app.utils.http_headers import content_disposition_attachment


def test_content_disposition_ascii_filename() -> None:
    header = content_disposition_attachment("Global_Audit_Report_2026.xlsx")
    assert header == 'attachment; filename="Global_Audit_Report_2026.xlsx"; filename*=UTF-8\'\'Global_Audit_Report_2026.xlsx'
    header.encode("latin-1")


def test_content_disposition_unicode_filename() -> None:
    header = content_disposition_attachment("प्रदेश कृषि डायरी, २०८३ (1).xlsx")
    assert 'filename="' in header
    assert "filename*=UTF-8''" in header
    header.encode("latin-1")
