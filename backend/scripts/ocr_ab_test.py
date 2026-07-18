#!/usr/bin/env python3
"""A/B test: adaptive DPI vs fixed 300 DPI OCR.

Runs both strategies on a corpus of PDFs and reports per-page & aggregate
metrics so you can verify the adaptive path doesn't regress accuracy.

Usage:
    python -m scripts.ocr_ab_test path/to/corpus/                   # all PDFs
    python -m scripts.ocr_ab_test path/to/single.pdf                # single file
    python -m scripts.ocr_ab_test results.json --report-only        # re-print saved results

Output (also saved as JSON):
    {
      "summary":  { "total_pages": N, "pages_escalated": M, ... },
      "per_page": [ { "file": "a.pdf", "page": 0, "old_conf": 0.92, ... }, ... ]
    }
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import tempfile
import time
from pathlib import Path

import fitz

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

LOW_CONF_THRESHOLD = 0.75


def _old_fixed_300(page, page_idx, tmp_dir):
    """Fixed 300 DPI + PaddleOCR (with Tesseract fallback on error)."""
    from app.ocr import recognize_with_fallback

    zoom = 300 / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    img_path = tmp_dir / f"old_{page_idx:04d}.png"
    pix.save(img_path)
    del pix

    t0 = time.perf_counter()
    boxes = recognize_with_fallback(img_path, page_idx)
    elapsed = time.perf_counter() - t0

    scale = 72.0 / 300
    for b in boxes:
        b.x *= scale
        b.y *= scale
        b.w *= scale
        b.h *= scale
    return boxes, elapsed


def _new_adaptive(page, page_idx, tmp_dir):
    """Adaptive DPI path: 200 + PaddleOCR, escalate if low confidence."""
    from app.ocr.paddle_engine import PaddleEngine
    from app.ocr.tesseract_engine import TesseractEngine

    escalated = False

    dpi1 = 200
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi1 / 72.0, dpi1 / 72.0), alpha=False)
    img_path = tmp_dir / f"new_{page_idx:04d}_p1.png"
    pix.save(img_path)
    del pix

    t0 = time.perf_counter()
    engine = PaddleEngine()
    boxes = engine.recognize_page(img_path, page_idx)
    elapsed = time.perf_counter() - t0

    avg_conf = (sum(b.confidence for b in boxes) / len(boxes)) if boxes else 0.0

    if avg_conf < LOW_CONF_THRESHOLD:
        dpi2 = 300
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi2 / 72.0, dpi2 / 72.0), alpha=False)
        img_path = tmp_dir / f"new_{page_idx:04d}_p2.png"
        pix.save(img_path)
        del pix

        t0 = time.perf_counter()
        engine = TesseractEngine()
        boxes = engine.recognize_page(img_path, page_idx)
        elapsed = time.perf_counter() - t0
        escalated = True

    scale = 72.0 / (dpi2 if escalated else dpi1)
    for b in boxes:
        b.x *= scale
        b.y *= scale
        b.w *= scale
        b.h *= scale
    return boxes, elapsed, escalated


def _compute_metrics(old_boxes, new_boxes):
    """Compute per-page comparison metrics."""
    old_conf = (sum(b.confidence for b in old_boxes) / len(old_boxes)) if old_boxes else 0.0
    new_conf = (sum(b.confidence for b in new_boxes) / len(new_boxes)) if new_boxes else 0.0

    old_conf = round(old_conf, 4)
    new_conf = round(new_conf, 4)

    return {
        "old_box_count": len(old_boxes),
        "new_box_count": len(new_boxes),
        "old_avg_confidence": old_conf,
        "new_avg_confidence": new_conf,
        "conf_delta": round(new_conf - old_conf, 4),
    }


def test_page(page, page_idx, tmp_dir):
    old_boxes, old_ms = _old_fixed_300(page, page_idx, tmp_dir)
    new_boxes, new_ms, escalated = _new_adaptive(page, page_idx, tmp_dir)

    m = _compute_metrics(old_boxes, new_boxes)
    m["page"] = page_idx
    m["old_time_ms"] = round(old_ms * 1000, 1)
    m["new_time_ms"] = round(new_ms * 1000, 1)
    m["time_delta_ms"] = round((new_ms - old_ms) * 1000, 1)
    m["escalated"] = escalated
    return m


def test_pdf(pdf_path, max_pages=None):
    results = []
    with fitz.open(pdf_path) as doc:
        total = min(len(doc), max_pages) if max_pages else len(doc)
        with tempfile.TemporaryDirectory(prefix="ab_") as tmp:
            tmp_dir = Path(tmp)
            for i in range(total):
                results.append(test_page(doc[i], i, tmp_dir))
    return results, total


def run_corpus(paths, max_pages=None):
    all_results = []
    total_pages = 0
    escalated_pages = 0

    for p in paths:
        name = p.name
        pages, n = test_pdf(p, max_pages)
        for r in pages:
            r["file"] = name
        all_results.extend(pages)
        total_pages += n
        escalated_pages += sum(1 for r in pages if r.get("escalated"))

    if not all_results:
        print("No results collected.")
        return all_results, {}, total_pages, escalated_pages

    avg_old_conf = sum(r["old_avg_confidence"] for r in all_results) / len(all_results)
    avg_new_conf = sum(r["new_avg_confidence"] for r in all_results) / len(all_results)
    avg_old_time = sum(r["old_time_ms"] for r in all_results) / len(all_results)
    avg_new_time = sum(r["new_time_ms"] for r in all_results) / len(all_results)

    summary = {
        "total_pages": total_pages,
        "pages_escalated": escalated_pages,
        "escalation_pct": round(escalated_pages / len(all_results) * 100, 1) if all_results else 0,
        "avg_old_confidence": round(avg_old_conf, 4),
        "avg_new_confidence": round(avg_new_conf, 4),
        "avg_confidence_delta": round(avg_new_conf - avg_old_conf, 4),
        "avg_old_time_ms": round(avg_old_time, 1),
        "avg_new_time_ms": round(avg_new_time, 1),
        "avg_time_delta_ms": round(avg_new_time - avg_old_time, 1),
    }
    return all_results, summary, total_pages, escalated_pages


def print_report(all_results, summary, total_pages, escalated_pages):
    print("=" * 72)
    print("  OCR A/B Test  —  Adaptive DPI vs Fixed 300 DPI")
    print("=" * 72)

    print(f"\n  Total pages scanned: {total_pages}")
    print(f"  Pages that escalated: {escalated_pages} / {len(all_results)} ({summary['escalation_pct']}%)")

    print(f"\n  {'Metric':<40} {'Fixed 300':>12} {'Adaptive':>12} {'Delta':>10}")
    print("  " + "-" * 74)
    print(f"  {'Average confidence':<40} {summary['avg_old_confidence']:>12.4f} {summary['avg_new_confidence']:>12.4f} {summary['avg_confidence_delta']:>+10.4f}")
    print(f"  {'Average time (ms)':<40} {summary['avg_old_time_ms']:>12.1f} {summary['avg_new_time_ms']:>12.1f} {summary['avg_time_delta_ms']:>+10.1f}")

    if summary["avg_time_delta_ms"] <= 0:
        print(f"\n  ✓ ADAPTIVE IS FASTER by {abs(summary['avg_time_delta_ms']):.1f} ms avg")
    else:
        print(f"\n  ⚠ Adaptive is slower by {summary['avg_time_delta_ms']:.1f} ms avg")

    conf_delta = summary["avg_confidence_delta"]
    if conf_delta >= 0:
        print(f"  ✓ Adaptive confidence is {conf_delta:+.4f} higher (one-sided OK)")
    else:
        print(f"  ✗ Adaptive confidence is {conf_delta:+.4f} LOWER — regression!")

    print(f"\n  Per-page breakdown:")
    print(f"  {'File':<30} {'Pg':>3} {'OldConf':>8} {'NewConf':>8} {'ΔConf':>8} {'OldMs':>7} {'NewMs':>7} {'Esc':>4}")
    print("  " + "-" * 78)
    for r in all_results:
        esc = "YES" if r["escalated"] else ""
        print(f"  {r['file']:<30} {r['page']:>3} {r['old_avg_confidence']:>8.4f} {r['new_avg_confidence']:>8.4f} {r['conf_delta']:>+8.4f} {r['old_time_ms']:>7.1f} {r['new_time_ms']:>7.1f} {esc:>4}")
    print()


def main():
    parser = argparse.ArgumentParser(description="OCR A/B test")
    parser.add_argument("target", help="PDF file, directory, or results JSON")
    parser.add_argument("--max-pages", type=int, default=None, help="Max pages per PDF")
    parser.add_argument("--report-only", action="store_true", help="Re-print from saved JSON")
    args = parser.parse_args()

    target = Path(args.target)

    if args.report_only:
        with open(target) as f:
            data = json.load(f)
        print_report(data["per_page"], data["summary"], data["total_pages"], data["pages_escalated"])
        return

    if target.is_dir():
        paths = sorted(target.glob("*.pdf"))
    elif target.is_file() and target.suffix == ".pdf":
        paths = [target]
    else:
        print(f"Not a PDF or directory: {target}", file=sys.stderr)
        sys.exit(1)

    if not paths:
        print("No PDFs found.", file=sys.stderr)
        sys.exit(1)

    print(f"Processing {len(paths)} PDF(s) ...\n")
    all_results, summary, total_pages, escalated_pages = run_corpus(paths, args.max_pages)

    print_report(all_results, summary, total_pages, escalated_pages)

    out_path = Path("ocr_ab_test_results.json")
    with open(out_path, "w") as f:
        json.dump({
            "summary": summary,
            "per_page": all_results,
            "total_pages": total_pages,
            "pages_escalated": escalated_pages,
        }, f, indent=2)
    print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
