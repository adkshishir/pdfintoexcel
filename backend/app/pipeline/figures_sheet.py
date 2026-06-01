"""Append a workbook sheet with embedded PDF raster images (stacked layout)."""

from __future__ import annotations

import io
import logging
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from app.pipeline.exporter import _safe_sheet_name
from app.pipeline.pdf_images import extract_pdf_images_with_stats

log = logging.getLogger(__name__)

# Display size cap for Excel floating images (px).
_MAX_DISPLAY_WIDTH = 480


def append_figures_sheet_from_pdf(
    wb,
    pdf_path: Path,
    *,
    sheet_title: str = "Figures",
) -> dict[str, int]:
    """Extract capped images from *pdf_path* and append one sheet to *wb*.

    Returns stats (same keys as :func:`extract_pdf_images_with_stats` second value).
    """
    by_page, stats = extract_pdf_images_with_stats(pdf_path)
    append_figures_sheet(wb, by_page, sheet_title=sheet_title)
    return stats


def append_figures_sheet(
    wb,
    page_images: dict[int, list[dict]],
    *,
    sheet_title: str = "Figures",
) -> None:
    """Write one sheet with labels and stacked images."""
    if not page_images:
        return
    name = _safe_sheet_name(sheet_title)
    # Avoid duplicate sheet names
    base = name
    n = 1
    while name in wb.sheetnames:
        name = _safe_sheet_name(f"{base[:28]}_{n}")
        n += 1
    ws = wb.create_sheet(name)
    ws.cell(row=1, column=1, value="Embedded images from PDF").font = Font(bold=True, size=12)
    row = 3
    label_font = Font(bold=True)
    for page_idx in sorted(page_images.keys()):
        for i, img in enumerate(page_images[page_idx]):
            x0, y0, x1, y1 = img["bbox"]
            caption = f"Page {page_idx + 1} — image {i + 1} — bbox ({x0:.0f},{y0:.0f})-({x1:.0f},{y1:.0f})"
            ws.cell(row=row, column=1, value=caption).font = label_font
            row += 1
            anchor_row = row
            try:
                from openpyxl.drawing.image import Image as XLImage

                xl_img = XLImage(io.BytesIO(img["data"]))
                w_nat, h_nat = xl_img.width, xl_img.height
                if w_nat > _MAX_DISPLAY_WIDTH and w_nat > 0:
                    scale = _MAX_DISPLAY_WIDTH / float(w_nat)
                    xl_img.width = int(w_nat * scale)
                    xl_img.height = int(h_nat * scale)
                anchor = f"B{anchor_row}"
                ws.add_image(xl_img, anchor)
                # Advance row by approximate image height in points (~1 row ≈ 15 px)
                est_rows = max(3, int((xl_img.height or 120) / 18) + 1)
                row = anchor_row + est_rows
            except Exception as exc:
                log.debug("figures sheet: skip image: %s", exc)
                ws.cell(row=row, column=2, value=f"(could not embed: {exc})")
                row += 2
    ws.column_dimensions["A"].width = 72
