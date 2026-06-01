"""Full-document layout export: positions every word on an Excel grid that
mirrors the PDF's spatial layout.

output_layout="split"  (default)
    One sheet per PDF page. Headers and footers are included as-is.

output_layout="merged"
    All pages on a single "Document" sheet. Repeated page headers/footers are
    detected by repetition analysis and printed exactly once:
      • Header once at the very top.
      • Each page's body content stacked vertically in order.
      • Footer once at the very bottom.

Header / footer detection
-------------------------
A word is classified as a header/footer candidate if it sits inside the top or
bottom Y-zone of its page (default: 10 % of the page height). A candidate is
confirmed as a *repeated* header/footer if the same word text (case-insensitive,
ignoring pure numbers / single characters) appears in that zone on ≥ 55 % of
the document's pages. This threshold is intentionally conservative so that
incidental first/last lines of body content are not misidentified.

Grid resolution
---------------
  COL_RES = 6.0 pt   →  1 Excel column  ≈ 6 PDF points wide
  ROW_RES = 12.0 pt  →  1 Excel row     ≈ 12 PDF points tall

A standard A4 page (595 × 842 pt) maps to ≈ 99 cols × 70 rows.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from app.pipeline.exporter import _safe_sheet_name
from app.pipeline.pdf_images import extract_pdf_images as _extract_pdf_images
from app.pipeline.types import OutputLayout, WordBox

log = logging.getLogger(__name__)

COL_RES: float = 6.0    # PDF points per Excel column
ROW_RES: float = 12.0   # PDF points per Excel row

_PT_TO_PX = 1.333        # 1 PDF pt ≈ 1.333 screen px

# Header / footer detection tunables.
_HEADER_ZONE     = 0.10   # top 10 % of page height
_FOOTER_ZONE     = 0.15   # bottom 15 % — footers sit up to ~1.5 in from edge
_REPEAT_FRACTION = 0.55   # line must appear in zone on ≥ 55 % of pages
_LINE_Y_TOL      = 4.0    # pt — words within this Y-band belong to same line
_PAGE_GAP_ROWS   = 2      # blank rows inserted between consecutive pages


# ======================================================================
# Public entry point
# ======================================================================

def export_full_document(
    boxes: list[WordBox],
    page_count: int,
    output_path: Path,
    pdf_path: Path | None = None,
    output_layout: OutputLayout = "split",
) -> int:
    """Write a layout workbook and return total body rows written.

    Parameters
    ----------
    boxes:         All WordBox tokens extracted from the PDF.
    page_count:    Total pages in the source PDF.
    output_path:   Destination .xlsx path.
    pdf_path:      Original PDF path — used for image extraction and for
                   deriving page heights for zone detection.
    output_layout: "split" → one sheet per page (default / unchanged).
                   "merged" → all pages on one sheet with header/footer
                              deduplicated.
    """
    by_page: dict[int, list[WordBox]] = {}
    for b in boxes:
        by_page.setdefault(b.page, []).append(b)

    page_images: dict[int, list[dict]] = {}
    if pdf_path is not None:
        page_images = _extract_pdf_images(pdf_path)

    page_heights = _get_page_heights(pdf_path, page_count)

    wb = Workbook()
    default = wb.active
    wb.remove(default)

    if output_layout == "merged":
        total_rows = _export_merged(
            wb, by_page, page_count, page_images, page_heights,
        )
    else:
        total_rows = _export_split(
            wb, by_page, page_count, page_images,
        )

    if not wb.sheetnames:
        fallback = wb.create_sheet(_safe_sheet_name("empty"))
        fallback.append(["No content extracted from this document."])

    wb.save(output_path)
    return total_rows


# ======================================================================
# Split mode — one sheet per page (original behaviour, unchanged)
# ======================================================================

def _export_split(
    wb: Workbook,
    by_page: dict[int, list[WordBox]],
    page_count: int,
    page_images: dict[int, list[dict]],
) -> int:
    total_rows = 0
    for page_idx in range(page_count):
        name = _safe_sheet_name(f"Page_{page_idx + 1}")
        ws = wb.create_sheet(name)

        page_boxes  = by_page.get(page_idx, [])
        images_here = page_images.get(page_idx, [])

        if not page_boxes and not images_here:
            ws.append(["(empty page)"])
            total_rows += 1
            continue

        max_er, max_ec = _write_words(ws, page_boxes, row_offset=0)

        _set_dimensions(ws, max_er, max_ec)

        for img in images_here:
            _insert_image(ws, img, row_offset=0)

        total_rows += max_er

    return total_rows


# ======================================================================
# Merged mode — all pages on one sheet, header/footer deduplicated
# ======================================================================

def _export_merged(
    wb: Workbook,
    by_page: dict[int, list[WordBox]],
    page_count: int,
    page_images: dict[int, list[dict]],
    page_heights: dict[int, float],
) -> int:
    ws = wb.create_sheet(_safe_sheet_name("Document"))

    # ---- detect repeated header / footer lines ----
    h_thresh, f_thresh, confirmed_h_fps, confirmed_f_fps = _detect_header_footer(
        by_page, page_count, page_heights,
    )
    log.info(
        "header/footer detection: %d header line-fps, %d footer line-fps",
        len(confirmed_h_fps), len(confirmed_f_fps),
    )

    pages = [p for p in range(page_count) if by_page.get(p)]
    if not pages:
        ws.append(["(no content)"])
        return 1

    # ---- split each page's words into header / body / footer ----
    def classify(page: int) -> tuple[list[WordBox], list[WordBox], list[WordBox]]:
        words = by_page.get(page, [])
        ht    = h_thresh.get(page, 0.0)
        ft    = f_thresh.get(page, float("inf"))
        header: list[WordBox] = []
        footer: list[WordBox] = []
        for w in words:
            if w.y < ht and _word_in_confirmed_zone(w, words, ht, "header", confirmed_h_fps):
                header.append(w)
            elif w.y2 > ft and _word_in_confirmed_zone(w, words, ft, "footer", confirmed_f_fps):
                footer.append(w)
        # Use identity set so body = everything not classified above.
        hdr_ids = {id(w) for w in header}
        ftr_ids = {id(w) for w in footer}
        body = [w for w in words if id(w) not in hdr_ids and id(w) not in ftr_ids]

        # Contiguous upward expansion: footer blocks often extend above the hard
        # zone threshold (e.g. a long disclaimer paragraph).  Walk upward from the
        # topmost confirmed footer word and absorb body lines that are spatially
        # adjacent (gap ≤ 2× ROW_RES) so the full block is written once at the end.
        if footer:
            footer = _expand_footer_upward(footer, body, ht)
            ftr_ids2 = {id(w) for w in footer}
            body = [w for w in words if id(w) not in hdr_ids and id(w) not in ftr_ids2]

        return header, body, footer

    # Canonical header comes from the first page that has header words.
    # Canonical footer comes from the last page that has footer words.
    canonical_header: list[WordBox] = []
    canonical_footer: list[WordBox] = []
    for p in pages:
        hdr, _, _ = classify(p)
        if hdr and not canonical_header:
            canonical_header = hdr
            break
    for p in reversed(pages):
        _, _, ftr = classify(p)
        if ftr and not canonical_footer:
            canonical_footer = ftr
            break

    # ---- write header once ----
    current_offset = 0
    if canonical_header:
        h_max_er, h_max_ec = _write_words(ws, canonical_header, row_offset=0)
        _apply_bold_zone(ws, 1, h_max_er)
        current_offset = h_max_er + _PAGE_GAP_ROWS
        log.debug("merged: header written (%d rows)", h_max_er)

    # ---- write each page's body ----
    max_written = current_offset
    for page in pages:
        _, body_words, _ = classify(page)

        if not body_words:
            # Still advance offset by one gap so page boundaries show.
            current_offset += _PAGE_GAP_ROWS
            continue

        # Normalise body Y so each page starts at row 1 relative to offset.
        body_y_min = min(w.y for w in body_words)
        adjusted   = [
            _shift_box(w, y_shift=-body_y_min)
            for w in body_words
        ]
        er, ec = _write_words(ws, adjusted, row_offset=current_offset)
        max_written = max(max_written, current_offset + er)

        # Images for this page, shifted to match body offset.
        img_row_offset = current_offset - int(body_y_min / ROW_RES)
        for img in page_images.get(page, []):
            _insert_image(ws, img, row_offset=img_row_offset)

        # Advance offset: end of this page's body + gap.
        current_offset = current_offset + er + _PAGE_GAP_ROWS

    # ---- write footer once ----
    if canonical_footer:
        footer_offset = max(max_written, current_offset) + _PAGE_GAP_ROWS
        f_y_min = min(w.y for w in canonical_footer)
        adjusted = [_shift_box(w, y_shift=-f_y_min) for w in canonical_footer]
        f_er, _ = _write_words(ws, adjusted, row_offset=footer_offset)
        _apply_bold_zone(ws, footer_offset + 1, footer_offset + f_er)
        max_written = footer_offset + f_er
        log.debug("merged: footer written (%d rows)", f_er)

    total_rows = max(1, max_written)
    _set_dimensions(ws, total_rows, ws.max_column or 1)
    return total_rows


# ======================================================================
# Header / footer detection — line-fingerprint approach
# ======================================================================

def _get_page_heights(
    pdf_path: Path | None,
    page_count: int,
) -> dict[int, float]:
    """Return {page_idx: height_in_pt} using PyMuPDF when available."""
    if pdf_path is None:
        return {}
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        heights = {i: float(doc[i].rect.height)
                   for i in range(min(page_count, len(doc)))}
        doc.close()
        return heights
    except Exception as exc:
        log.debug("page height extraction failed: %s", exc)
        return {}


def _detect_header_footer(
    by_page: dict[int, list[WordBox]],
    page_count: int,
    page_heights: dict[int, float],
) -> tuple[
    dict[int, float],          # h_thresh  {page: y < this → header zone}
    dict[int, float],          # f_thresh  {page: y2 > this → footer zone}
    set[frozenset[str]],       # confirmed header line fingerprints
    set[frozenset[str]],       # confirmed footer line fingerprints
]:
    """Line-fingerprint header/footer detection.

    Detection strategy
    ------------------
    1. For each page compute a header zone (top _HEADER_ZONE %) and footer
       zone (bottom _FOOTER_ZONE %).
    2. Group zone words into horizontal text lines (words within _LINE_Y_TOL
       of each other in Y).
    3. Compute a *fingerprint* for each line: the frozenset of its
       non-trivial, non-numeric tokens (lowercase). Page numbers that
       change between pages ("1", "24") are stripped, so "Page 1 of 24"
       and "Page 5 of 24" produce the same fingerprint {"page", "of"}.
    4. A fingerprint is *confirmed* if it appears in that zone on ≥
       _REPEAT_FRACTION of pages (minimum 2 pages).
    5. A word is part of a header/footer if it sits in the zone AND its
       enclosing line's fingerprint is confirmed.  This means numbers on
       the same line as confirmed tokens are correctly included even though
       they were stripped from the fingerprint.
    """
    pages = [p for p in range(page_count) if by_page.get(p)]
    if len(pages) < 2:
        return {}, {}, set(), set()

    h_thresh: dict[int, float] = {}
    f_thresh: dict[int, float] = {}

    for page in pages:
        words = by_page[page]
        if not words:
            continue
        ph = page_heights.get(page)
        if ph and ph > 0:
            h_thresh[page] = ph * _HEADER_ZONE
            f_thresh[page] = ph * (1.0 - _FOOTER_ZONE)
        else:
            y_min = min(w.y  for w in words)
            y_max = max(w.y2 for w in words)
            span  = max(1.0, y_max - y_min)
            h_thresh[page] = y_min + span * _HEADER_ZONE
            f_thresh[page] = y_max - span * _FOOTER_ZONE

    # Count how many pages each line fingerprint appears in each zone.
    h_fp_pages: dict[frozenset, set[int]] = {}
    f_fp_pages: dict[frozenset, set[int]] = {}

    for page in pages:
        ht = h_thresh.get(page, 0.0)
        ft = f_thresh.get(page, float("inf"))
        all_words = by_page.get(page, [])

        h_words = [w for w in all_words if w.y  < ht]
        f_words = [w for w in all_words if w.y2 > ft]

        for line in _group_lines(h_words):
            fp = _line_fp(line)
            if fp:
                h_fp_pages.setdefault(fp, set()).add(page)

        for line in _group_lines(f_words):
            fp = _line_fp(line)
            if fp:
                f_fp_pages.setdefault(fp, set()).add(page)

    min_pages = max(2, int(len(pages) * _REPEAT_FRACTION))

    confirmed_h = {fp for fp, pgs in h_fp_pages.items() if len(pgs) >= min_pages}
    confirmed_f = {fp for fp, pgs in f_fp_pages.items() if len(pgs) >= min_pages}

    log.debug(
        "h_fp candidates=%d confirmed=%d  f_fp candidates=%d confirmed=%d",
        len(h_fp_pages), len(confirmed_h), len(f_fp_pages), len(confirmed_f),
    )
    return h_thresh, f_thresh, confirmed_h, confirmed_f


def _group_lines(words: list[WordBox]) -> list[list[WordBox]]:
    """Group words into horizontal text lines by Y-centre proximity."""
    if not words:
        return []
    ordered = sorted(words, key=lambda w: (w.y + w.y2) / 2.0)
    lines: list[list[WordBox]] = [[ordered[0]]]
    for w in ordered[1:]:
        cy      = (w.y + w.y2) / 2.0
        line_cy = sum((u.y + u.y2) / 2.0 for u in lines[-1]) / len(lines[-1])
        if abs(cy - line_cy) <= _LINE_Y_TOL:
            lines[-1].append(w)
        else:
            lines.append([w])
    return lines


def _line_fp(words: list[WordBox]) -> frozenset[str]:
    """Fingerprint a text line: lowercase non-trivial non-numeric tokens.

    Strips pure numbers so "Page 1 of 24" and "Page 5 of 24" hash the same.
    Returns an empty frozenset for lines that are entirely numeric/trivial
    (e.g. a lone page number) so they are excluded from repetition counts.
    """
    tokens: set[str] = set()
    for w in words:
        t = w.text.strip().lower()
        # Skip: empty, single char, pure number, or common lone punctuation.
        if len(t) <= 1:
            continue
        stripped = t.replace(",", "").replace(".", "").replace("-", "")
        if stripped.isdigit():
            continue
        tokens.add(t)
    return frozenset(tokens)


def _word_in_confirmed_zone(
    word: WordBox,
    page_words: list[WordBox],
    zone_thresh: float,
    zone: str,           # "header" or "footer"
    confirmed_fps: set[frozenset[str]],
) -> bool:
    """Return True if *word* belongs to a confirmed header/footer line.

    The word's line is reconstructed from all page words at similar Y, then
    its fingerprint is checked against the confirmed set.  This ensures that
    numbers on the same line as confirmed tokens are also included.
    """
    if not confirmed_fps:
        return False
    word_cy = (word.y + word.y2) / 2.0
    # Collect all words at similar Y (the word's line, across the full page).
    line_words = [
        w for w in page_words
        if abs((w.y + w.y2) / 2.0 - word_cy) <= _LINE_Y_TOL
    ]
    fp = _line_fp(line_words)
    return fp in confirmed_fps and bool(fp)


# ======================================================================
# Low-level helpers
# ======================================================================

def _expand_footer_upward(
    footer: list[WordBox],
    body: list[WordBox],
    header_thresh: float,
) -> list[WordBox]:
    """Expand *footer* upward by absorbing contiguous body lines above it.

    Footer blocks (e.g. multi-paragraph disclaimers) are often taller than
    _FOOTER_ZONE, so only their lowest lines land in the hard detection zone.
    Starting from the topmost confirmed footer word, we walk upward through
    body lines and absorb any line whose bottom is within 2×ROW_RES of the
    current frontier — i.e. there is no visible gap between it and the footer
    block already collected.  We stop as soon as a gap appears or we reach the
    header zone.
    """
    if not footer or not body:
        return footer

    footer_y_top = min(w.y for w in footer)

    # Group body words into lines and sort descending (closest to footer first).
    body_lines = _group_lines(body)
    body_lines_above = sorted(
        [line for line in body_lines if max(w.y for w in line) < footer_y_top],
        key=lambda l: max(w.y2 for w in l),
        reverse=True,
    )

    absorbed: list[WordBox] = list(footer)
    current_top = footer_y_top

    for line in body_lines_above:
        line_bottom = max(w.y2 for w in line)
        line_top    = min(w.y  for w in line)
        if line_top <= header_thresh:
            break                            # don't eat into the header zone
        gap = current_top - line_bottom
        if gap <= ROW_RES * 2.0:            # contiguous (within ~2 text rows)
            absorbed.extend(line)
            current_top = line_top
        else:
            break                            # gap found — stop expansion

    return absorbed


def _write_words(
    ws,
    words: list[WordBox],
    row_offset: int,
) -> tuple[int, int]:
    """Write words onto the sheet at (y/ROW_RES + row_offset, x/COL_RES).

    Returns (max_excel_row_relative_to_offset, max_excel_col).
    """
    max_er = 0
    max_ec = 0
    for box in words:
        er = max(1, int(box.y / ROW_RES) + 1)
        ec = max(1, int(box.x / COL_RES) + 1)
        abs_er = er + row_offset
        cell   = ws.cell(row=abs_er, column=ec)
        existing = cell.value or ""
        cell.value = (existing + " " + box.text).strip() if existing else box.text
        max_er = max(max_er, er)
        max_ec = max(max_ec, ec)
    return max_er, max_ec


def _shift_box(box: WordBox, *, y_shift: float) -> WordBox:
    """Return a new WordBox with y and y2 shifted (x unchanged)."""
    return WordBox(
        text=box.text,
        x=box.x,
        y=box.y + y_shift,
        w=box.w,
        h=box.h,
        page=box.page,
        confidence=box.confidence,
    )


def _set_dimensions(ws, max_row: int, max_col: int) -> None:
    col_width = COL_RES / 5.25
    for ci in range(1, max_col + 1):
        ws.column_dimensions[get_column_letter(ci)].width = col_width
    row_height = ROW_RES * 0.75
    for ri in range(1, max_row + 1):
        ws.row_dimensions[ri].height = row_height


def _apply_bold_zone(ws, row_start: int, row_end: int) -> None:
    """Bold all non-empty cells in the header/footer rows."""
    bold = Font(bold=True)
    for ri in range(row_start, row_end + 1):
        for cell in ws[ri]:
            if cell.value:
                cell.font = bold


# Image bytes: see pdf_images.extract_pdf_images (used as _extract_pdf_images).


def _insert_image(ws, img_info: dict, row_offset: int = 0) -> None:
    """Insert a raster image at its PDF-mapped position, shifted by row_offset."""
    try:
        from openpyxl.drawing.image import Image as XLImage
    except ImportError:
        return
    try:
        x0, y0, x1, y1 = img_info["bbox"]
        anchor_row = max(1, int(y0 / ROW_RES) + 1 + row_offset)
        anchor_col = max(1, int(x0 / COL_RES) + 1)
        anchor     = f"{get_column_letter(anchor_col)}{anchor_row}"

        xl_img        = XLImage(io.BytesIO(img_info["data"]))
        xl_img.width  = int(max(1.0, x1 - x0) * _PT_TO_PX)
        xl_img.height = int(max(1.0, y1 - y0) * _PT_TO_PX)
        ws.add_image(xl_img, anchor)
    except Exception as exc:
        log.debug("image insert failed: %s", exc)
