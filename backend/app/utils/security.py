"""File validation at the upload boundary.

Phase 9 swap: prefer python-magic (libmagic) over the magic-byte string check
when libmagic is available. Falls back to the byte-string check when it
isn't (test envs without `libmagic1`, certain CI runners).
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

PDF_MAGIC = b"%PDF-"
PDF_MIME_TYPES = {"application/pdf", "application/x-pdf"}

_magic = None
_magic_unavailable = False


def _get_magic():
    """Lazy + cached. Returns a configured magic.Magic, or None if unavailable."""
    global _magic, _magic_unavailable
    if _magic is not None or _magic_unavailable:
        return _magic
    try:
        import magic
        _magic = magic.Magic(mime=True)
    except Exception as e:  # ImportError, libmagic missing, etc.
        log.warning("python-magic unavailable (%s); falling back to magic-byte check", e)
        _magic_unavailable = True
    return _magic


def looks_like_pdf(head: bytes) -> bool:
    """True iff the first chunk of an upload looks like a PDF.

    Tries libmagic first (catches edge cases the byte-string check misses,
    like polyglot files with a junk PDF header). Falls back to the original
    magic-byte search through the first 1 KiB.
    """
    m = _get_magic()
    if m is not None:
        try:
            mime = m.from_buffer(head[:4096])
            if mime in PDF_MIME_TYPES:
                return True
            log.debug("libmagic rejected upload: mime=%r", mime)
            return False
        except Exception as e:
            log.warning("libmagic threw on buffer (%s); falling back", e)

    # PDF spec allows up to 1024 bytes of junk before %PDF-.
    return PDF_MAGIC in head[:1024]
