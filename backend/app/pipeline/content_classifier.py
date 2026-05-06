"""Full-document content classifier.

Classifies WordBox tokens from a PDF into a DocumentContent structure:
  - header_lines  : repeated top-of-page text (deduplicated across pages;
                  lines that only repeat the main table’s column titles are dropped)
  - footer_lines  : repeated bottom-of-page text (deduplicated, printed once at end)
  - body_blocks   : text paragraphs + table references, sorted by (page, y_start)

The header/footer detection is delegated entirely to layout_export helpers so
the two modes share the same detection logic.  Table regions use the same
"preamble vs main grid" split as `orchestrator._extract_preamble`: on a page
with several detected tables, everything above the table that starts furthest
down the page is narrative; with a single table we split at the row that looks
like a transaction header (Date + Description/Amount…).

Words below that split are masked by RawTable bboxes and excluded from body
classification (the table exporter owns them).

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
_TABLE_SLACK       = 6.0    # pts — bbox expansion (left/right/bottom)
_TABLE_SLACK_TOP   = 1.5    # tight top edge so letterhead above the grid is not swallowed
_LINE_Y_TOL_FACTOR = 0.6    # multiplied by median word height to get line-group tol
_PARA_GAP_FACTOR   = 2.5    # gap > h_med * this → new paragraph
_HEADING_MAX_WORDS = 10     # paragraph with ≤ this many words is a heading candidate
_KV_MIN_FRACTION   = 0.60   # fraction of lines that must look like "Key: Value"

_BULLET_CHARS = frozenset("•·‣◦▪▸►●○◉–—")
_NUMBERED_RE  = re.compile(r"^\d+[\.\)]\s|^[a-zA-Z][\.\)]\s")
_KV_RE        = re.compile(r"^.{1,50}:\s+\S")   # "Key: Value"
_ENDS_SENTENCE = re.compile(r"[.?!;,]$")

# Header-zone lines that repeat every page but are identical to the grid header
# (Date / Description / Amount / …) must not become DOCUMENT HEADER — the Excel
# table block already has those column titles.


def _norm_banner(s: str) -> str:
    return " ".join(s.strip().lower().split())


def _primary_headers_joined(clean_tables: list[CleanTable]) -> str | None:
    if not clean_tables or not clean_tables[0].headers:
        return None
    return _norm_banner(" ".join(clean_tables[0].headers))


def _matches_primary_column_headers(blob: str, clean_tables: list[CleanTable]) -> bool:
    ref = _primary_headers_joined(clean_tables)
    if not ref or len(ref) < 8:
        return False
    cand = _norm_banner(blob)
    if cand == ref:
        return True
    if len(cand) > 12 and len(ref) > 12 and (cand in ref or ref in cand):
        return True
    return False


def _looks_like_repeated_txn_column_banner(blob: str) -> bool:
    """Short per-page banner that repeats bank-statement column titles."""
    s = _norm_banner(blob)
    if len(s) > 160:
        return False
    if "date" not in s:
        return False
    if "description" not in s and "details" not in s:
        return False
    if not any(k in s for k in ("amount", "balance", "gbp", "debit", "credit")):
        return False
    return True


def _filter_grid_banner_header_lines(
    lines: list[str],
    clean_tables: list[CleanTable],
) -> list[str]:
    out: list[str] = []
    for ln in lines:
        if _matches_primary_column_headers(ln, clean_tables):
            continue
        if _looks_like_repeated_txn_column_banner(ln):
            continue
        out.append(ln)
    return out


def _strip_redundant_grid_header_body_blocks(
    blocks: list[ContentBlock],
    clean_tables: list[CleanTable],
) -> list[ContentBlock]:
    """Remove narrative blocks that only repeat the main table's column header."""
    if not clean_tables:
        return blocks
    pages_tbl = {ct.source_page for ct in clean_tables}
    out: list[ContentBlock] = []
    for b in blocks:
        if b.page not in pages_tbl:
            out.append(b)
            continue
        blob = _norm_banner(" ".join(b.lines))
        if not blob:
            out.append(b)
            continue
        if _matches_primary_column_headers(blob, clean_tables):
            continue
        if _looks_like_repeated_txn_column_banner(blob):
            continue
        out.append(b)
    return out


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
    table_index    = _build_table_index(raw_tables)
    cut_by_page    = _narrative_cutoff_by_page(raw_tables)

    # ---- canonical header: first page that actually has repeated header text ----
    # (Page 0 may be a cover without the running header; using only page 0 drops
    # the banner from the export while still stripping those words from body.)
    header_lines: list[str] = []
    if confirmed_h_fps:
        for p in range(page_count):
            lines = _extract_zone_lines(
                by_page, p, h_thresh, confirmed_h_fps, "header",
                _word_in_confirmed_zone,
            )
            if lines:
                header_lines = lines
                break
    header_lines = _filter_grid_banner_header_lines(header_lines, clean_tables)
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
        cut_y      = cut_by_page.get(page)

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
            cy = (w.y + w.y2) / 2.0
            # Preamble (statement title, balances, address, etc.): never treat as
            # table text, mirroring orchestrator._extract_preamble (max bbox top).
            if cut_y is not None and cy < cut_y - 0.5:
                in_table = False
            else:
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

    # ---- body above main grid: footer-like layout in Excel (per line) ----
    _mark_pre_table_blocks(body_blocks, cut_by_page)
    body_blocks = _strip_redundant_grid_header_body_blocks(body_blocks, clean_tables)

    # ---- table blocks ----
    for ct in clean_tables:
        sort_y = cut_by_page.get(ct.source_page, ct.source_y)
        body_blocks.append(ContentBlock(
            kind="table",
            page=ct.source_page,
            y_start=sort_y,
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
# Preamble vs main grid — match orchestrator._extract_preamble semantics
# ---------------------------------------------------------------------------

def _narrative_cutoff_by_page(raw_tables: list[RawTable]) -> dict[int, float]:
    """Y (PDF space) above which centres are eligible for table masking.

    Multiple tables on a page: use ``max(bbox[1])`` — the main grid starts
    furthest down; everything above is statement header / summary (Monzo-style).

    Single table: split at the visual top of the transaction header row
    (``Date`` + ``Description`` / ``Amount`` / …) when discoverable; else bbox top.
    """
    by_page: dict[int, list[RawTable]] = {}
    for t in raw_tables:
        by_page.setdefault(t.page, []).append(t)
    out: dict[int, float] = {}
    for p, tbls in by_page.items():
        y = _page_narrative_cutoff(tbls)
        if y is not None:
            out[p] = y
    return out


def _page_narrative_cutoff(tables: list[RawTable]) -> float | None:
    if not tables:
        return None
    if len(tables) >= 2:
        return max(t.bbox[1] for t in tables)
    return _single_table_narrative_cutoff_y(tables[0])


def _single_table_narrative_cutoff_y(raw: RawTable) -> float:
    r = _find_transaction_header_row(raw)
    if r is not None and r < len(raw.row_y_centers):
        return _row_top_y(raw, r)
    return float(raw.bbox[1])


def _find_transaction_header_row(raw: RawTable) -> int | None:
    """Row index of the column-header band (Date, Description, …)."""
    by_row: dict[int, list[str]] = {}
    for c in raw.cells:
        txt = (c.text or "").strip()
        if not txt:
            continue
        by_row.setdefault(c.row, []).append(txt)
    for r in sorted(by_row):
        joined = " ".join(by_row[r]).lower()
        if "date" not in joined:
            continue
        if any(
            k in joined
            for k in ("description", "amount", "balance", "details", "payee", "debit", "credit")
        ):
            return r
    return None


def _row_top_y(raw: RawTable, r: int) -> float:
    """Approximate top Y of logical row *r* from row centre spacing."""
    cy = raw.row_y_centers[r]
    centers = raw.row_y_centers
    if r + 1 < len(centers):
        step = centers[r + 1] - cy
    elif r > 0:
        step = cy - centers[r - 1]
    else:
        step = 24.0
    half = max(8.0, step * 0.48)
    return cy - half


# ---------------------------------------------------------------------------
# Table-region helpers (bbox mask below narrative cutoff)
# ---------------------------------------------------------------------------

def _mark_pre_table_blocks(
    body_blocks: list[ContentBlock],
    narrative_cutoff: dict[int, float],
) -> None:
    """Mark non-table blocks above the main grid on each page as `pre_table`."""
    for i, blk in enumerate(body_blocks):
        top = narrative_cutoff.get(blk.page)
        if top is None or blk.kind == "table":
            continue
        if blk.y_start < top - 0.5:
            body_blocks[i] = ContentBlock(
                kind="pre_table",
                page=blk.page,
                y_start=blk.y_start,
                lines=list(blk.lines),
                table=None,
            )


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
           (y0 - _TABLE_SLACK_TOP) <= cy <= (y1 + _TABLE_SLACK):
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
