#!/usr/bin/env python3
"""Render a digital PDF to a synthetic 'scanned' PDF (image-only, no text layer).

Useful for OCR pipeline testing when no real scanned fixture is on hand.
The output has the same page count and visual content but pdfplumber/PyMuPDF
will report zero text — the detector will route it to the OCR pipeline.

Usage:
    python -m scripts.make_scanned_pdf input.pdf output.pdf [--dpi 200]

Run from `backend/` with the venv active.
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import fitz  # PyMuPDF


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--dpi", type=int, default=200,
                        help="Render resolution (higher = larger file, sharper OCR).")
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 2

    src = fitz.open(args.input)
    dst = fitz.open()
    zoom = args.dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    for i, page in enumerate(src):
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        # New page in destination, sized to the original PDF page (in points).
        new_page = dst.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(page.rect, stream=pix.tobytes("png"))
        print(f"  page {i+1}/{len(src)}: rendered {pix.width}x{pix.height}px")

    dst.save(args.output, garbage=4, deflate=True)
    print(f"wrote {args.output} ({args.output.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
