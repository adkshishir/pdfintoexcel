"""Merge tiled PDF image placements into single figures."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.pipeline.pdf_images import extract_pdf_images_with_stats


def _tiled_logo_pdf(tmp_path: Path, *, n_tiles: int = 10, tile_height: float = 2.0) -> Path:
    import fitz
    from PIL import Image

    png = tmp_path / "logo.png"
    Image.new("RGB", (120, 40), color=(20, 60, 140)).save(png)
    pdf = tmp_path / "tiled.pdf"
    doc = fitz.open()
    page = doc.new_page(width=300, height=400)
    y = 44.0
    for _ in range(n_tiles):
        r = fitz.Rect(72, y, 253, y + tile_height)
        page.insert_image(r, filename=str(png))
        y += tile_height + 1.0
    doc.save(pdf)
    doc.close()
    return pdf


def test_vertical_tiles_merge_to_one_image(tmp_path: Path) -> None:
    pdf = _tiled_logo_pdf(tmp_path)
    by_page, stats = extract_pdf_images_with_stats(pdf, max_per_page=None, max_total=None)
    assert 0 in by_page
    assert len(by_page[0]) == 1
    _x0, y0, _x1, y1 = by_page[0][0]["bbox"]
    assert y1 - y0 >= 12.0
    assert stats["merged_fragments"] >= 1 or stats["rendered_clip"] >= 1


def test_single_large_image_unchanged(tmp_path: Path) -> None:
    import fitz
    from PIL import Image

    png = tmp_path / "one.png"
    Image.new("RGB", (80, 50), color=(200, 10, 10)).save(png)
    pdf = tmp_path / "one.pdf"
    doc = fitz.open()
    page = doc.new_page(width=300, height=400)
    page.insert_image(fitz.Rect(50, 50, 200, 200), filename=str(png))
    doc.save(pdf)
    doc.close()

    by_page, stats = extract_pdf_images_with_stats(pdf)
    assert len(by_page[0]) == 1
    assert stats["embedded"] == 1
    assert stats.get("merged_fragments", 0) == 0
