"""Extract embedded raster images from PDFs (PyMuPDF).

Used by layout export and optional ``Figures`` workbook sheets. Capped extraction
avoids multi‑hundred‑MB Excel files from huge marketing PDFs.

Tiled logos (many 2–3pt-tall placements) are merged into one image per visual region.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

DEFAULT_MAX_PER_PAGE = 20
DEFAULT_MAX_TOTAL = 200
DEFAULT_MAX_IMAGE_BYTES = 4 * 1024 * 1024
DEFAULT_MAX_DIMENSION = 2048

MIN_BBOX_PT = 12.0
X_ALIGN_TOL = 2.0
VERT_GAP_TOL = 4.0
CLIP_RENDER_DPI = 144


def _get_image_bbox(page: Any, img_item: Any):
    try:
        return page.get_image_bbox(img_item)
    except TypeError:
        pass
    try:
        return page.get_image_bbox(img_item[0])
    except Exception:
        pass
    try:
        for block in page.get_text("rawdict")["blocks"]:
            if block.get("type") == 1 and block.get("number") == img_item[0]:
                import fitz

                return fitz.Rect(block["bbox"])
    except Exception:
        pass
    return None


def _bbox_tuple(rect: Any) -> tuple[float, float, float, float]:
    return float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)


def _union_bbox(
    boxes: list[tuple[float, float, float, float]],
) -> tuple[float, float, float, float]:
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def _bbox_width_height(b: tuple[float, float, float, float]) -> tuple[float, float]:
    return b[2] - b[0], b[3] - b[1]


def _is_tiny_bbox(b: tuple[float, float, float, float]) -> bool:
    w, h = _bbox_width_height(b)
    return w < MIN_BBOX_PT or h < MIN_BBOX_PT


def _x_aligned(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> bool:
    return abs(a[0] - b[0]) <= X_ALIGN_TOL and abs(a[2] - b[2]) <= X_ALIGN_TOL


def _vertical_gap(
    upper: tuple[float, float, float, float],
    lower: tuple[float, float, float, float],
) -> float:
    return lower[1] - upper[3]


def _merge_vertical_strip_clusters(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge placements that look like horizontal tiles of one logo."""
    if len(items) <= 1:
        return items

    items = sorted(items, key=lambda it: (it["bbox"][1], it["bbox"][0]))
    merged: list[dict[str, Any]] = []
    cluster: list[dict[str, Any]] = [items[0]]

    def flush() -> None:
        if not cluster:
            return
        if len(cluster) == 1:
            merged.append(cluster[0])
            return
        boxes = [c["bbox"] for c in cluster]
        xrefs = {c["xref"] for c in cluster}
        merged.append({
            "bbox": _union_bbox(boxes),
            "xref": cluster[0]["xref"],
            "render_clip": True,
            "fragment_count": len(cluster),
            "xrefs": xrefs,
        })

    for item in items[1:]:
        prev = cluster[-1]["bbox"]
        cur = item["bbox"]
        if _x_aligned(prev, cur) and _vertical_gap(prev, cur) <= VERT_GAP_TOL:
            cluster.append(item)
        else:
            flush()
            cluster = [item]
    flush()
    return merged


def _group_by_xref(placements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_xref: dict[int, list[tuple[float, float, float, float]]] = {}
    for p in placements:
        by_xref.setdefault(p["xref"], []).append(p["bbox"])

    out: list[dict[str, Any]] = []
    for xref, boxes in by_xref.items():
        if len(boxes) == 1:
            out.append({"bbox": boxes[0], "xref": xref, "render_clip": False})
        else:
            out.append({
                "bbox": _union_bbox(boxes),
                "xref": xref,
                "render_clip": True,
                "fragment_count": len(boxes),
            })
    return out


def _render_clip_jpeg(page: Any, bbox: tuple[float, float, float, float]) -> tuple[bytes, str]:
    import fitz

    rect = fitz.Rect(*bbox)
    pix = page.get_pixmap(clip=rect, dpi=CLIP_RENDER_DPI)
    return pix.tobytes("jpeg"), "jpeg"


def _maybe_downscale_image_bytes(
    raw_bytes: bytes,
    ext: str,
    *,
    max_dimension: int,
) -> tuple[bytes, str]:
    """Return (bytes, ext) possibly JPEG-recompressed after downscaling."""
    try:
        from PIL import Image
    except ImportError:
        return raw_bytes, ext
    try:
        im = Image.open(io.BytesIO(raw_bytes))
        im = im.convert("RGB") if im.mode not in ("RGB", "L") else im
        w, h = im.size
        if w <= max_dimension and h <= max_dimension:
            return raw_bytes, ext
        scale = min(max_dimension / w, max_dimension / h)
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        im = im.resize((nw, nh), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=85)
        return buf.getvalue(), "jpeg"
    except Exception:
        return raw_bytes, ext


def _collect_logical_images(page: Any, doc: Any, stats: dict[str, int]) -> list[dict[str, Any]]:
    placements: list[dict[str, Any]] = []
    for img_item in page.get_images(full=True):
        xref = img_item[0]
        bbox_r = _get_image_bbox(page, img_item)
        if bbox_r is None:
            stats["skipped_bbox"] += 1
            continue
        placements.append({"xref": xref, "bbox": _bbox_tuple(bbox_r)})

    if not placements:
        return []

    logical = _group_by_xref(placements)
    logical = _merge_vertical_strip_clusters(logical)

    kept: list[dict[str, Any]] = []
    for item in logical:
        # Merged tiles often have narrow reported bboxes; clip render uses union rect.
        if not item.get("render_clip") and _is_tiny_bbox(item["bbox"]):
            stats["skipped_tiny"] += 1
            continue
        if item.get("render_clip"):
            stats["merged_fragments"] += int(item.get("fragment_count", 2)) - 1
        kept.append(item)
    return kept


def _materialize_image(
    page: Any,
    doc: Any,
    item: dict[str, Any],
    *,
    max_image_bytes: int,
    max_dimension: int,
    stats: dict[str, int],
) -> dict | None:
    bbox = item["bbox"]
    try:
        if item.get("render_clip"):
            blob, ext = _render_clip_jpeg(page, bbox)
            stats["rendered_clip"] += 1
        else:
            raw = doc.extract_image(item["xref"])
            blob = raw["image"]
            ext = raw.get("ext", "png") or "png"
        if len(blob) > max_image_bytes:
            stats["skipped_size"] += 1
            return None
        blob2, ext2 = _maybe_downscale_image_bytes(blob, ext, max_dimension=max_dimension)
        return {"data": blob2, "ext": ext2, "bbox": bbox}
    except Exception as exc:
        log.debug("skip image xref %s: %s", item.get("xref"), exc)
        return None


def extract_page_images(
    pdf_path: Path,
    page_idx: int,
    *,
    max_y: float | None = None,
    max_per_page: int | None = DEFAULT_MAX_PER_PAGE,
    max_image_bytes: int = DEFAULT_MAX_IMAGE_BYTES,
    max_dimension: int = DEFAULT_MAX_DIMENSION,
) -> list[dict]:
    """Images on one page (merged), optionally limited to content above *max_y*."""
    try:
        import fitz
    except ImportError:
        return []

    stats = {"skipped_tiny": 0, "skipped_bbox": 0, "merged_fragments": 0, "rendered_clip": 0}
    try:
        doc = fitz.open(str(pdf_path))
        page = doc[page_idx]
        logical = _collect_logical_images(page, doc, stats)
        out: list[dict] = []
        for item in logical:
            if max_y is not None and item["bbox"][1] >= max_y:
                continue
            if max_per_page is not None and len(out) >= max_per_page:
                break
            img = _materialize_image(
                page, doc, item,
                max_image_bytes=max_image_bytes,
                max_dimension=max_dimension,
                stats=stats,
            )
            if img is not None:
                out.append(img)
        doc.close()
        return out
    except Exception as exc:
        log.debug("extract_page_images page %d: %s", page_idx, exc)
        return []


def extract_pdf_images_with_stats(
    pdf_path: Path,
    *,
    max_per_page: int | None = DEFAULT_MAX_PER_PAGE,
    max_total: int | None = DEFAULT_MAX_TOTAL,
    max_image_bytes: int = DEFAULT_MAX_IMAGE_BYTES,
    max_dimension: int = DEFAULT_MAX_DIMENSION,
) -> tuple[dict[int, list[dict]], dict[str, int]]:
    """Extract images keyed by 0-based page index.

    Each image dict: ``{"data": bytes, "ext": str, "bbox": (x0,y0,x1,y1)}``.

    Returns ``(images_by_page, stats)`` where stats contains
    ``embedded``, ``skipped_size``, ``skipped_cap``, ``skipped_bbox``,
    ``skipped_tiny``, ``merged_fragments``, ``rendered_clip``.
    """
    result: dict[int, list[dict]] = {}
    stats: dict[str, int] = {
        "embedded": 0,
        "skipped_size": 0,
        "skipped_cap": 0,
        "skipped_bbox": 0,
        "skipped_tiny": 0,
        "merged_fragments": 0,
        "rendered_clip": 0,
    }
    try:
        import fitz
    except ImportError:
        log.warning("PyMuPDF not available — skipping image extraction")
        return result, stats

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as exc:
        log.warning("fitz.open failed for %s: %s", pdf_path, exc)
        return result, stats

    total = 0
    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_stats = {k: 0 for k in ("skipped_bbox", "skipped_tiny", "merged_fragments", "rendered_clip")}
            logical = _collect_logical_images(page, doc, page_stats)
            for k in page_stats:
                stats[k] += page_stats[k]

            images: list[dict] = []
            page_count = 0
            for item in logical:
                if max_per_page is not None and page_count >= max_per_page:
                    stats["skipped_cap"] += 1
                    continue
                if max_total is not None and total >= max_total:
                    stats["skipped_cap"] += 1
                    continue
                img = _materialize_image(
                    page, doc, item,
                    max_image_bytes=max_image_bytes,
                    max_dimension=max_dimension,
                    stats=stats,
                )
                if img is None:
                    continue
                images.append(img)
                page_count += 1
                total += 1
                stats["embedded"] += 1
            if images:
                result[page_idx] = images
    finally:
        doc.close()

    log.info(
        "pdf_images: embedded=%s skipped_size=%s skipped_cap=%s skipped_bbox=%s "
        "skipped_tiny=%s merged_fragments=%s rendered_clip=%s",
        stats["embedded"],
        stats["skipped_size"],
        stats["skipped_cap"],
        stats["skipped_bbox"],
        stats["skipped_tiny"],
        stats["merged_fragments"],
        stats["rendered_clip"],
    )
    return result, stats


def extract_pdf_images(pdf_path: Path) -> dict[int, list[dict]]:
    """Uncapped extraction for legacy layout export (may be large)."""
    d, _ = extract_pdf_images_with_stats(
        pdf_path,
        max_per_page=None,
        max_total=None,
    )
    return d
