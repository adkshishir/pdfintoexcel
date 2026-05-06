"""Pipeline orchestrator — Phase 6 + post-phase improvements.

All three PDF types share the same downstream pipeline:

    RawTable[]  →  clean_tables  →  export_excel

Where RawTable[] comes from:

    digital   →  Tier-1 (pdfplumber ruled-line) + Tier-2 (geometry reconstructor
                  for pages not covered by Tier-1)
    scanned   →  OCR → geometry reconstructor
    hybrid    →  digital pages via Tier-1/Tier-2, scanned pages via OCR

`mode` flag (`fast` | `accurate`):
    - `accurate` raises OCR DPI (200 → 300, handled in ocr_pipeline).
    - `accurate` enables continuation merging (geometry-aware; now also
      applied in fast mode for obvious rowspan cases via the sparse-row
      signal added in Phase 10+).
    - `fast` keeps continuation merging off for speed.

`extraction_scope`:
    - `tables_only`   — structured table path (default).
    - `full_document` — layout workbook (position-mapped text + embedded images).

Footer-word filtering (tables_only only)
-----------------------------------------
Footer words are detected BEFORE table reconstruction and stripped from the
word-box list.  This prevents footer text from being treated as table rows
by the geometry reconstructor.  The canonical footer text is written once at
the very end of the output sheet.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from app.pipeline.cleaner import clean_tables
from app.pipeline.detector import detect_pdf_type
from app.pipeline.digital_words import extract_digital_words
from app.pipeline.exporter import export_excel
from app.pipeline.ocr_pipeline import extract_ocr
from app.pipeline.pdfplumber_tables import extract_pdfplumber_tables
from app.pipeline.types import ExtractionScope, Mode, OutputLayout, PipelineResult, WordBox
from app.table.reconstructor import reconstruct_tables

log = logging.getLogger(__name__)


def run_pipeline(
    pdf_path: Path,
    output_path: Path,
    *,
    mode: Mode = "fast",
    output_layout: OutputLayout = "merged",
    extraction_scope: ExtractionScope = "tables_only",
) -> PipelineResult:
    timings: dict[str, int] = {}

    t0 = time.time()
    detection = detect_pdf_type(pdf_path)
    timings["detect_ms"] = _ms_since(t0)
    log.info(
        "detected: type=%s pages=%s with_text=%s",
        detection.pdf_type, detection.page_count, detection.pages_with_text,
    )

    boxes, page_count = _collect_boxes(pdf_path, detection, mode, timings)

    layout_row_count: int | None = None
    if extraction_scope == "full_document":
        from app.pipeline.content_classifier import classify_document
        from app.pipeline.structured_exporter import export_structured_document

        # Run footer detection + table extraction (same quality path as tables_only).
        t_fd = time.time()
        footer_word_ids, _ = _detect_footer_words(pdf_path, boxes, page_count)
        table_boxes = [b for b in boxes if id(b) not in footer_word_ids] if footer_word_ids else boxes
        timings["footer_detect_ms"] = _ms_since(t_fd)

        if detection.pdf_type == "digital":
            raw = _extract_digital_tables(pdf_path, page_count, timings, all_boxes=table_boxes)
        else:
            t_recon = time.time()
            raw = reconstruct_tables(table_boxes, page_count)
            timings["reconstruct_ms"] = _ms_since(t_recon)
        log.info("full_document reconstruct: %d tables", len(raw))

        t_clean = time.time()
        clean = clean_tables(
            raw,
            merge_continuations=(mode == "accurate"),
            output_layout=output_layout,
        )
        timings["clean_ms"] = _ms_since(t_clean)

        t_classify = time.time()
        content = classify_document(boxes, raw, clean, page_count, pdf_path=pdf_path)
        layout_row_count = export_structured_document(content, output_path)
        timings["export_ms"] = _ms_since(t_classify)
        log.info("full_document structured export: %d rows", layout_row_count)
    else:
        # --- tables_only path ---

        # 1. Detect footer words FIRST so they can be excluded from reconstruction.
        #    This is the key fix: the geometry reconstructor never sees footer words,
        #    so they cannot appear as spurious table rows on any page.
        t_fd = time.time()
        footer_word_ids, footer_lines = _detect_footer_words(pdf_path, boxes, page_count)
        timings["footer_detect_ms"] = _ms_since(t_fd)
        if footer_word_ids:
            log.info("footer detection: %d words filtered across all pages", len(footer_word_ids))
            table_boxes = [b for b in boxes if id(b) not in footer_word_ids]
        else:
            table_boxes = boxes

        # 2. Reconstruct tables from footer-clean boxes.
        if detection.pdf_type == "digital":
            raw = _extract_digital_tables(
                pdf_path, page_count, timings, all_boxes=table_boxes,
            )
        else:
            t_recon = time.time()
            raw = reconstruct_tables(table_boxes, page_count)
            timings["reconstruct_ms"] = _ms_since(t_recon)
        log.info("reconstruct: %d tables", len(raw))

        t_clean = time.time()
        clean = clean_tables(
            raw,
            merge_continuations=(mode == "accurate"),
            output_layout=output_layout,
        )
        timings["clean_ms"] = _ms_since(t_clean)
        log.info("clean: %d tables retained (layout=%s)", len(clean), output_layout)

        t_export = time.time()
        # Preamble uses the full boxes (footer words are fine in the header area).
        preamble_boxes, preamble_images = _extract_preamble(pdf_path, boxes, raw)
        export_excel(
            clean, output_path,
            preamble_boxes=preamble_boxes,
            preamble_images=preamble_images,
            footer_lines=footer_lines,
        )
        timings["export_ms"] = _ms_since(t_export)

    mean_conf = (
        sum(b.confidence for b in boxes) / len(boxes) if boxes else 0.0
    )

    return PipelineResult(
        pdf_type=detection.pdf_type,
        tables=clean,
        page_count=detection.page_count,
        mean_confidence=mean_conf,
        timings_ms=timings,
        layout_row_count=layout_row_count,
    )


# ---- box collection ---------------------------------------------------

def _collect_boxes(pdf_path, detection, mode, timings) -> tuple[list[WordBox], int]:
    """Route each page to the right extraction source and combine."""
    if detection.pdf_type == "digital":
        t = time.time()
        boxes, page_count = extract_digital_words(pdf_path)
        timings["digital_ms"] = _ms_since(t)
        return boxes, page_count

    if detection.pdf_type == "scanned":
        t = time.time()
        boxes, page_count = extract_ocr(pdf_path, mode=mode)
        timings["ocr_ms"] = _ms_since(t)
        return boxes, page_count

    # hybrid
    text_pages = sorted(detection.text_page_indices)
    scan_pages = sorted(detection.scanned_page_indices())
    log.info(
        "hybrid: %d digital pages, %d scanned pages",
        len(text_pages), len(scan_pages),
    )

    t = time.time()
    digital_boxes, page_count = extract_digital_words(pdf_path, page_indices=text_pages)
    timings["digital_ms"] = _ms_since(t)

    if scan_pages:
        t = time.time()
        ocr_boxes, _ = extract_ocr(pdf_path, mode=mode, page_indices=scan_pages)
        timings["ocr_ms"] = _ms_since(t)
    else:
        ocr_boxes = []

    return digital_boxes + ocr_boxes, page_count


# ---- Tier-1 + Tier-2 digital table extraction -------------------------

def _extract_digital_tables(
    pdf_path: Path,
    page_count: int,
    timings: dict[str, int],
    *,
    all_boxes: list | None = None,
) -> list:
    """Two-tier extraction for digital PDFs.

    Tier 1 — pdfplumber ruled-line detection: exact cell boundaries, native
    rowspan handling. Only activates when the PDF has drawn table borders.

    Tier 2 — geometry reconstructor on WordBox[]: handles text-only tables
    (whitespace-separated columns, no visible borders) for pages not covered
    by Tier 1.

    `all_boxes`: pre-extracted (and optionally pre-filtered) word boxes.
    When provided the internal extract_digital_words call is skipped so we
    avoid double-extraction and respect any caller-side filtering (e.g. footer
    words already removed).
    """
    t = time.time()
    tier1 = extract_pdfplumber_tables(pdf_path)
    timings["tier1_ms"] = _ms_since(t)
    tier1_pages = {tbl.page for tbl in tier1}

    if all_boxes is None:
        # Caller did not supply boxes — extract now.
        t = time.time()
        all_boxes, _ = extract_digital_words(pdf_path)
        timings["digital_ms"] = _ms_since(t)
    # else: digital_ms was already written by _collect_boxes.

    uncovered_boxes = [b for b in all_boxes if b.page not in tier1_pages]
    if uncovered_boxes:
        t = time.time()
        tier2 = reconstruct_tables(uncovered_boxes, page_count)
        timings["reconstruct_ms"] = _ms_since(t)
    else:
        tier2 = []
        timings["reconstruct_ms"] = 0

    log.info(
        "digital: %d tier-1 (ruled) tables, %d tier-2 (geometry) tables",
        len(tier1), len(tier2),
    )
    return tier1 + tier2


# ---- footer detection -------------------------------------------------

def _detect_footer_words(
    pdf_path: Path,
    boxes: list,
    page_count: int,
) -> tuple[set[int], list[str]]:
    """Detect repeated footer content across ALL pages.

    Returns:
        footer_word_ids  — id(w) for every footer word on every page.
                           Caller uses this to filter boxes before reconstruction
                           so footer text never enters table cells.
        footer_text_lines — canonical footer text (from the last page that has
                            footer content), deduplicated and sorted top-to-bottom.
                            Written once at the end of the output sheet.

    Detection is centralised: the same fingerprint set (built from all pages) is
    used to classify every page consistently.  A word is footer if:
      1. Its line fingerprint is confirmed as a repeated footer fingerprint, AND
      2. Its position is in the lower portion of the page (hard zone: y2 > ft)
         OR it is contiguous with confirmed footer words (expansion).
    """
    try:
        from app.pipeline.layout_export import (
            _detect_header_footer,
            _get_page_heights,
            _group_lines,
            _word_in_confirmed_zone,
        )
    except ImportError:
        return set(), []

    by_page: dict[int, list] = {}
    for b in boxes:
        by_page.setdefault(b.page, []).append(b)

    page_heights = _get_page_heights(pdf_path, page_count)
    _, f_thresh, _, confirmed_f_fps = _detect_header_footer(
        by_page, page_count, page_heights,
    )

    if not confirmed_f_fps:
        return set(), []

    log.debug("footer fingerprints confirmed: %d", len(confirmed_f_fps))

    # Collect footer word IDs from EVERY page using the confirmed fingerprint set.
    #
    # Key design choice: we do NOT gate on y2 > ft here.  On most pages the
    # footer sits in the bottom zone, but on a short last page the disclaimer
    # can appear right after the last transaction — well above the threshold.
    # Using fingerprints without a positional gate handles both cases:
    # the fingerprints were confirmed from the pages where the footer IS in the
    # zone, and those same fingerprints match the identical text on any page
    # regardless of its Y position.
    all_footer_ids: set[int] = set()
    canonical_words: list = []          # footer words from last zone-positioned page
    canonical_from_zone: list = []      # best representation: footer in the hard zone

    for page in range(page_count):
        words = by_page.get(page, [])
        if not words:
            continue
        ft = f_thresh.get(page, float("inf"))

        # Match every word on the page against confirmed footer fingerprints.
        page_footer = [
            w for w in words
            if _word_in_confirmed_zone(w, words, ft, "footer", confirmed_f_fps)
        ]
        for w in page_footer:
            all_footer_ids.add(id(w))

        if page_footer:
            canonical_words = page_footer
            # Prefer canonical from pages where footer is in the standard zone
            # (avoids a short page where footer text may blend with body content).
            if any(w.y2 > ft for w in page_footer):
                canonical_from_zone = page_footer

    if not all_footer_ids:
        return set(), []

    best_canonical = canonical_from_zone if canonical_from_zone else canonical_words

    # Convert canonical page's footer words to ordered text lines.
    lines = _group_lines(best_canonical)
    footer_text = [
        " ".join(w.text for w in sorted(line, key=lambda w: w.x))
        for line in lines
    ]

    return all_footer_ids, footer_text


# ---- preamble extraction -----------------------------------------------

def _extract_preamble(
    pdf_path: Path,
    boxes: list,
    raw_tables: list,
) -> tuple[list, list[dict]]:
    """Return (preamble_word_boxes, preamble_images) for page 0.

    Preamble = content on page 0 that appears *above* the first table.
    This covers business headers, logos, account summaries, etc. that are
    outside the structured table area.
    """
    page0_tables = [t for t in raw_tables if t.page == 0]
    if not page0_tables:
        return [], []

    # The "main" table (transactions) is the one that starts furthest down the
    # page.  Everything above it — including any summary / header area tables —
    # is preamble content we want to display.
    table_top_y = max(t.bbox[1] for t in page0_tables)
    if table_top_y <= 2:
        # Table starts at the very top of the page → nothing to show as preamble.
        return [], []

    preamble_boxes = [
        b for b in boxes
        if b.page == 0 and b.y < table_top_y
    ]

    preamble_images = _extract_page_images(pdf_path, page_idx=0, max_y=table_top_y)
    return preamble_boxes, preamble_images


def _extract_page_images(
    pdf_path: Path,
    page_idx: int,
    max_y: float,
) -> list[dict]:
    """Extract images from *page_idx* with top-edge y < max_y via PyMuPDF."""
    try:
        import fitz
    except ImportError:
        return []
    try:
        doc  = fitz.open(str(pdf_path))
        page = doc[page_idx]
        imgs: list[dict] = []
        for item in page.get_images(full=True):
            xref = item[0]
            try:
                bbox_r = page.get_image_bbox(item)
                if bbox_r is None or float(bbox_r.y0) >= max_y:
                    continue
                raw = doc.extract_image(xref)
                imgs.append({
                    "data": raw["image"],
                    "ext":  raw.get("ext", "png"),
                    "bbox": (
                        float(bbox_r.x0), float(bbox_r.y0),
                        float(bbox_r.x1), float(bbox_r.y1),
                    ),
                })
            except Exception:
                pass
        doc.close()
        return imgs
    except Exception:
        return []


# ---- helpers ----------------------------------------------------------

def _ms_since(t0: float) -> int:
    return int((time.time() - t0) * 1000)
