"""HTTP response header helpers."""

from __future__ import annotations

from urllib.parse import quote


def content_disposition_attachment(filename: str) -> str:
    """Build a latin-1-safe Content-Disposition value for file downloads.

    Starlette encodes header values as latin-1, so non-ASCII filenames must
    use RFC 5987 ``filename*`` with a UTF-8 percent-encoded value plus an ASCII
    ``filename`` fallback for older clients.
    """
    safe = filename.replace("\\", "_").replace('"', "_")
    ascii_fallback = "".join(c if ord(c) < 128 else "_" for c in safe).strip()
    if not ascii_fallback or ascii_fallback in {".", ".."}:
        ascii_fallback = "download.xlsx"
    encoded = quote(filename, safe="")
    return f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{encoded}'
