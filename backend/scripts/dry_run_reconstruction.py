#!/usr/bin/env python3
"""Dry-run the table reconstructor against any digital PDF.

Pipes pdfplumber word boxes through `reconstruct_tables` (treating them as
if they came from OCR) and prints the result. No OCR engine is invoked, so
this works locally without tesseract / paddleocr installed.

Usage:
    python -m scripts.dry_run_reconstruction path/to.pdf [--page N] [--xlsx out.xlsx]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pdfplumber

from app.pipeline.cleaner import clean_tables
from app.pipeline.exporter import export_excel
from app.pipeline.types import WordBox
from app.table.reconstructor import reconstruct_tables


def _pdf_to_wordboxes(pdf_path: Path, page_filter: int | None) -> tuple[list[WordBox], int]:
    boxes: list[WordBox] = []
    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            if page_filter is not None and i != page_filter:
                continue
            for w in page.extract_words(keep_blank_chars=False):
                if not w["text"].strip():
                    continue
                boxes.append(WordBox(
                    text=w["text"],
                    x=float(w["x0"]),
                    y=float(w["top"]),
                    w=float(w["x1"] - w["x0"]),
                    h=float(w["bottom"] - w["top"]),
                    page=i,
                    confidence=1.0,
                ))
    return boxes, page_count


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("pdf", type=Path)
    p.add_argument("--page", type=int, default=None,
                   help="Only process this page index (0-based). Default: all pages.")
    p.add_argument("--xlsx", type=Path, default=None,
                   help="Also write the reconstructed result to this .xlsx.")
    p.add_argument("--limit", type=int, default=10,
                   help="Max rows to print per table.")
    args = p.parse_args(argv)

    if not args.pdf.exists():
        print(f"input not found: {args.pdf}", file=sys.stderr)
        return 2

    boxes, page_count = _pdf_to_wordboxes(args.pdf, args.page)
    print(f"pdf:    {args.pdf} ({page_count} pages, {len(boxes)} word boxes)")

    raw = reconstruct_tables(boxes, page_count)
    print(f"raw:    {len(raw)} tables reconstructed")

    clean = clean_tables(raw)
    print(f"clean:  {len(clean)} tables retained")
    print()

    for ct in clean:
        print(f"--- {ct.sheet_name} ({len(ct.rows)} rows, {len(ct.headers)} cols) ---")
        print("  headers:", ct.headers)
        for r in ct.rows[:args.limit]:
            print("    ", r)
        if len(ct.rows) > args.limit:
            print(f"     ... +{len(ct.rows) - args.limit} more rows")
        print()

    if args.xlsx:
        export_excel(clean, args.xlsx)
        print(f"wrote {args.xlsx} ({args.xlsx.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
