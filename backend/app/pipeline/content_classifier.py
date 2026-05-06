"""Full-document content classifier.

Classifies WordBox tokens from a PDF into a DocumentContent structure:
  - header_lines  : repeated top-of-page text (deduplicated across pages)
  - footer_lines  : repeated bottom-of-page text (deduplicated, printed once at end)
  - body_blocks   : text paragraphs + table references, sorted by (page, y_start)

The header/footer detection is delegated entirely to layout_export helpers so
the two modes share the same detection logic.  Table regions are identified by
the bounding boxes of the RawTable objects from the table-extraction pipeline.
Words that fall inside a table bbox are excluded from text classification (the
table extractor already handles them).

Public entry point
------------------
  classify_document(boxes, raw_tables, clean_tables, page_count, pdf_path) -> DocumentContent
"""

from __future__ import annotations

import re
from pathlib import Path
from statistics import median
from typing import TYPE_CHECKING

from app.pipeline.types import (
    CleanTable,
    ContentBlock,
    DocumentContent,
    RawTable,
    WordBox,
)

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------
_TABLE_SLACK       = 6.0    # pts — bbox expansion when testing word-in-table
_LINE_Y_TOL_FACTOR = 0.6    # multiplied by median word height to get line-group tol
_PARA_GAP_FACTOR   = 2.5    # gap > h_med * this → new paragraph
_HEADING_MAX_WORDS = 10     # paragraph with ≤ this many words is a heading candidate
_KV_MIN_FRACTION   = 0.60   # fraction of lines that must look like "Key: Value"

_BULLET_CHARS = frozenset("•·‣◦▪▸►●○◉–—")
_NUMBERED_RE  = re.compile(r"^\d+[\.\)]\s|^[a-zA-Z][\.\)]\s")
_KV_RE        = re.compile(r"^.{1,50}:\s+\S")   # "Key: Value"
_ENDS_SENTENCE = re.compile(r"[.?!;,]$")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def classify_document(
    boxes: list[WordBox],
    raw_tables: list[RawTable],
    clean_tables: list[CleanTable],
    page_count: int,
    pdf_path: Path | None = None,
) -> DocumentContent:
    """Classify all word boxes into a structured DocumentContent.

    Parameters
    ----------
    boxes         : All word boxes from the PDF (from digital or OCR extraction).
    raw_tables    : Raw table regions from the reconstructor (provides bboxes).
    clean_tables  : Cleaned tables ready for export (attached as table blocks).
    page_count    : Total page count.
    pdf_path      : Path to the source PDF (for page-height detection).
    """
    # Lazy-import layout_export helpers to avoid any circular-import risk.
    from app.pipeline.layout_export import (
        _detect_header_footer,
        _get_page_heights,
        _group_lines,
        _word_in_confirmed_zone,
    )

    by_page: dict[int, list[WordBox]] = {}
    for b in boxes:
        by_page.setdefault(b.page, []).append(b)

    page_heights   = _get_page_heights(pdf_path, page_count)
    h_thresh, f_thresh, confirmed_h_fps, confirmed_f_fps = _detect_header_footer(
        by_page, page_count, page_heights,
    )
    table_index = _build_table_index(raw_tables)

    # ---- canonical header (from page 0 header-zone words) ----
    header_lines = _extract_zone_lines(
        by_page, 0, h_thresh, confirmed_h_fps, "header",
        _word_in_confirmed_zone,
    )
    # ---- canonical footer (from the last page that has footer-zone words) ----
    footer_lines = _extract_last_footer_lines(
        by_page, page_count, f_thresh, confirmed_f_fps,
        _word_in_confirmed_zone, _group_lines,
    )

    # ---- body blocks (text paragraphs per page) ----
    body_blocks: list[ContentBlock] = []

    hdr_ids: set[int] = set()
    ftr_ids: set[int] = set()

    for page in range(page_count):
        page_words = by_page.get(page, [])
        if not page_words:
            continue

        ht         = h_thresh.get(page, 0.0)
        ft         = f_thresh.get(page, float("inf"))
        tbl_bboxes = table_index.get(page, [])

        body_words = []
        for w in page_words:
            in_header = (
                w.y < ht
                and _word_in_confirmed_zone(w, page_words, ht, "header", confirmed_h_fps)
            )
            in_footer = (
                w.y2 > ft
                and _word_in_confirmed_zone(w, page_words, ft, "footer", confirmed_f_fps)
            )
            in_table = _in_table_region(w, tbl_bboxes)
            if in_header:
                hdr_ids.add(id(w))
            elif in_footer:
                ftr_ids.add(id(w))
            elif not in_table:
                body_words.append(w)

        if not body_words:
            continue

        h_med = median(w.h for w in body_words) or 12.0
        lines = _group_lines_adaptive(body_words, h_med * _LINE_Y_TOL_FACTOR)
        paragraphs = _split_into_paragraphs(lines, h_med * _PARA_GAP_FACTOR)

        for para_lines in paragraphs:
            all_words  = [w for line in para_lines for w in line]
            text_lines = [
                " ".join(w.text for w in sorted(line, key=lambda w: w.x))
                for line in para_lines
            ]
            # Skip empty or whitespace-only paragraphs.
            if not any(t.strip() for t in text_lines):
                continue
            y_start = min(w.y for w in all_words)
            kind    = _classify_para_kind(text_lines)
            body_blocks.append(ContentBlock(
                kind=kind, page=page, y_start=y_start, lines=text_lines,
            ))

    # ---- table blocks ----
    for ct in clean_tables:
        body_blocks.append(ContentBlock(
            kind="table",
            page=ct.source_page,
            y_start=ct.source_y,
            lines=[],
            table=ct,
        ))

    body_blocks.sort(key=lambda b: (b.page, b.y_start))

    return DocumentContent(
        header_lines=header_lines,
        footer_lines=footer_lines,
        body_blocks=body_blocks,
        page_count=page_count,
    )


# ---------------------------------------------------------------------------
# Table-region helpers
# ---------------------------------------------------------------------------

def _build_table_index(
    raw_tables: list[RawTable],
) -> dict[int, list[tuple[float, float, float, float]]]:
    """Map page → list of (x0, y0, x1, y1) bounding boxes."""
    index: dict[int, list] = {}
    for t in raw_tables:
        index.setdefault(t.page, []).append(t.bbox)
    return index


def _in_table_region(
    word: WordBox,
    table_bboxes: list[tuple[float, float, float, float]],
) -> bool:
    """Return True if the word's centre falls inside any table bbox."""
    cx = word.x + word.w / 2.0
    cy = word.y + word.h / 2.0
    for (x0, y0, x1, y1) in table_bboxes:
        if (x0 - _TABLE_SLACK) <= cx <= (x1 + _TABLE_SLACK) and \
           (y0 - _TABLE_SLACK) <= cy <= (y1 + _TABLE_SLACK):
            return True
    return False


# ---------------------------------------------------------------------------
# Header / footer text extraction
# ---------------------------------------------------------------------------

def _extract_zone_lines(
    by_page: dict[int, list[WordBox]],
    page: int,
    thresh_map: dict[int, float],
    confirmed_fps: set,
    zone: str,
    word_in_zone_fn,
) -> list[str]:
    """Return text lines for a confirmed zone on *page*.

    Returns an empty list if the page has no words or no confirmed fingerprints.
    """
    from app.pipeline.layout_export import _group_lines

    if not confirmed_fps:
        return []
    page_words = by_page.get(page, [])
    thresh     = thresh_map.get(page, 0.0 if zone == "header" else float("inf"))

    if zone == "header":
        zone_words = [
            w for w in page_words
            if w.y < thresh and word_in_zone_fn(w, page_words, thresh, zone, confirmed_fps)
        ]
    else:
        zone_words = [
            w for w in page_words
            if w.y2 > thresh and word_in_zone_fn(w, page_words, thresh, zone, confirmed_fps)
        ]

    return [
        " ".join(w.text for w in sorted(line, key=lambda w: w.x))
        for line in _group_lines(zone_words)
    ]


def _extract_last_footer_lines(
    by_page: dict[int, list[WordBox]],
    page_count: int,
    f_thresh: dict[int, float],
    confirmed_f_fps: set,
    word_in_zone_fn,
    group_lines_fn,
) -> list[str]:
    """Return text lines for the footer from the last page that has footer words."""
    if not confirmed_f_fps:
        return []
    for page in reversed(range(page_count)):
        page_words = by_page.get(page, [])
        if not page_words:
            continue
        ft = f_thresh.get(page, float("inf"))
        footer_words = [
            w for w in page_words
            if w.y2 > ft and word_in_zone_fn(w, page_words, ft, "footer", confirmed_f_fps)
        ]
        if footer_words:
            return [
                " ".join(w.text for w in sorted(line, key=lambda w: w.x))
                for line in group_lines_fn(footer_words)
            ]
    return []


# ---------------------------------------------------------------------------
# Text block grouping
# ---------------------------------------------------------------------------

def _group_lines_adaptive(
    words: list[WordBox],
    y_tol: float,
) -> list[list[WordBox]]:
    """Group words into horizontal text lines using an adaptive Y tolerance."""
    if not words:
        return []
    ordered = sorted(words, key=lambda w: (w.y + w.y2) / 2.0)
    lines: list[list[WordBox]] = [[ordered[0]]]
    for w in ordered[1:]:
        cy      = (w.y + w.y2) / 2.0
        line_cy = sum((u.y + u.y2) / 2.0 for u in lines[-1]) / len(lines[-1])
        if abs(cy - line_cy) <= y_tol:
            lines[-1].append(w)
        else:
            lines.append([w])
    return lines


def _split_into_paragraphs(
    lines: list[list[WordBox]],
    gap_thresh: float,
) -> list[list[list[WordBox]]]:
    """Split a list of word-lines into paragraphs based on Y gap between lines."""
    if not lines:
        return []
    paragraphs: list[list[list[WordBox]]] = [[lines[0]]]
    for line in lines[1:]:
        prev_bottom = max(w.y2 for w in paragraphs[-1][-1])
        this_top    = min(w.y  for w in line)
        if (this_top - prev_bottom) <= gap_thresh:
            paragraphs[-1].append(line)
        else:
            paragraphs.append([line])
    return paragraphs


# ---------------------------------------------------------------------------
# Paragraph kind classification
# ---------------------------------------------------------------------------

def _classify_para_kind(text_lines: list[str]) -> str:
    """Classify a list of text lines into a ContentBlockKind string."""
    if not text_lines:
        return "paragraph"

    total_text = " ".join(text_lines).strip()
    if not total_text:
        return "paragraph"

    total_words = len(total_text.split())
    last_char   = total_text[-1] if total_text else ""

    # --- bullet ---
    first_stripped = text_lines[0].lstrip()
    if first_stripped:
        if first_stripped[0] in _BULLET_CHARS or _NUMBERED_RE.match(first_stripped):
            return "bullet"

    # --- key_value block: ≥60% of lines look like "Key: value" ---
    if text_lines:
        kv_count = sum(1 for l in text_lines if _KV_RE.match(l.strip()))
        if kv_count >= max(1, len(text_lines) * _KV_MIN_FRACTION):
            return "key_value"

    # --- heading: short, no sentence-ending punctuation ---
    if total_words <= _HEADING_MAX_WORDS and not _ENDS_SENTENCE.search(total_text):
        return "heading"

    return "paragraph"
