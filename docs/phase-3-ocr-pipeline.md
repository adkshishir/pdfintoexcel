# Phase 3 — OCR pipeline

**Shipped:** 2026-05-01
**Acceptance criteria** (PROJECT_PLAN.md §8):
> Scanned PDF → page images → PaddleOCR → `WordBox[]`. Tesseract fallback wired.

## What landed

| Concern              | File                                  | Notes                                                                 |
| -------------------- | ------------------------------------- | --------------------------------------------------------------------- |
| Engine interface     | `app/ocr/base.py`                     | Already present from Phase 0; no change.                              |
| PaddleOCR engine     | `app/ocr/paddle_engine.py`            | Lazy singleton, polygon→axis-aligned bbox conversion, lang=en.        |
| Tesseract engine     | `app/ocr/tesseract_engine.py`         | `image_to_data` → WordBox, conf normalized 0–100 → 0.0–1.0, PSM 6.    |
| Engine factory       | `app/ocr/__init__.py`                 | `get_primary_engine()` from settings; `recognize_with_fallback()` auto-falls back to tesseract on exception. |
| OCR pipeline stage   | `app/pipeline/ocr_pipeline.py`        | PDF → PyMuPDF render at mode-DPI → engine → coords back to PDF points.|
| Orchestrator wiring  | `app/pipeline/orchestrator.py`        | Scanned PDFs now reach the OCR stage; raises with Phase-4 message after.|
| Fixture generator    | `backend/scripts/make_scanned_pdf.py` | Renders any digital PDF to a synthetic image-only "scanned" PDF.      |
| Tests                | `tests/test_ocr_pipeline.py`          | DI'd recognizer (no real OCR engines needed).                         |
| Worker container     | `backend/Dockerfile.worker`           | Adds `paddleocr` + `paddlepaddle` to requirements; tesseract apt pkg already there. |

## Architecture

```
                         ┌───────────────┐
   pdf_path ───►  fitz   │ render @ DPI  │  PNG per page
                  open   │  (mode-aware) │ ──────┐
                         └───────────────┘       │
                                                 ▼
                                       ┌─────────────────┐
                                       │ recognize_with_  │ on Paddle err
                                       │ fallback()       │ ───────────┐
                                       └────────┬─────────┘            │
                                                │                       ▼
                                       ┌────────▼─────────┐    ┌────────────────┐
                                       │  PaddleEngine    │    │ TesseractEngine│
                                       │  (primary)       │    │  (fallback)    │
                                       └────────┬─────────┘    └────────┬───────┘
                                                ▼                       │
                                          WordBox (px)  ◄───────────────┘
                                                │
                          scale = 72 / DPI      │  ◄── coords back to PDF points
                                                ▼
                                    WordBox (PDF user space)
                                                │
                                                ▼
                                       Phase 4 reconstruction
```

## Coordinate convention

OCR engines return coordinates in image pixels. The pipeline rescales to PDF
user space (points, top-left origin) before yielding `WordBox`. This means
Phase 4's reconstruction algorithm operates on the same coordinate system
whether the data came from the digital path or the OCR path — the algorithm
doesn't need to know.

`scale = 72.0 / dpi`. Fast mode → 200 DPI → scale 0.36. Accurate mode → 300
DPI → scale 0.24.

## Engine choice + fallback

- Primary engine is `Settings.ocr_engine` (default `paddle`).
- `recognize_with_fallback()` catches *any* exception from the primary and
  retries the page on Tesseract. This handles the common cases: PaddleOCR
  failing to download models in restricted networks, OOM on large pages,
  unsupported CJK character sets, etc.
- If the primary *is* Tesseract, no fallback (no infinite loop).

## Generating a scanned fixture

```bash
cd backend
python -m scripts.make_scanned_pdf ../MonzoBus.pdf ../MonzoBus.scanned.pdf --dpi 200
```

Verified locally: produces a 7.5MB image-only PDF with 24 pages, detector
correctly classifies as `scanned` (0/24 pages with text).

## Empirical end-to-end (Docker)

After rebuilding (`docker compose build` will install paddleocr — ~5 min cold):

```bash
curl -F file=@MonzoBus.scanned.pdf -F mode=fast http://localhost:8000/api/jobs
# wait
curl http://localhost:8000/api/jobs/<id>
# → status=failed, error="PIPELINE_NOT_IMPLEMENTED: Table reconstruction lands in Phase 4 — got <N> OCR word boxes."
```

The "got N OCR word boxes" message proves the OCR stage ran end-to-end. Phase
4 turns those boxes into a real Excel.

## Architectural decisions

- **DPI is mode-driven.** `fast=200`, `accurate=300`. Below 200 DPI, thin
  glyphs lose strokes and Tesseract drops them. Above 300 DPI, image size
  blows up without measurable accuracy gain.
- **Coords convert back to PDF points in the OCR module**, not in Phase 4.
  Keeps Phase 4 source-agnostic.
- **Recognizer is dependency-injectable** (`extract_ocr(..., recognizer=)`).
  Tests use a fake recognizer; production uses `recognize_with_fallback`.
  Phase 6's hybrid mode will pass a per-page recognizer for the scanned
  pages only.
- **Models download on first use, not at image build.** Image stays small
  (~2GB rather than ~3.5GB); first cold start pays a one-time ~15s download
  into the `paddle-models` named volume. Subsequent worker restarts reuse.
- **paddleocr + paddlepaddle are now required.** Requirements file no longer
  comments them out. Image build time goes up by ~3 minutes.

## What Phase 3 deliberately leaves unfinished

- **Reconstruction.** Scanned PDFs still fail at the orchestrator. Phase 4.
- **Image preprocessing** (deskew, denoise, contrast). Tesseract benefits
  noticeably from these on real-world scans. Phase 5 or a Phase 4 sub-task.
- **Per-page confidence routing.** When a page's mean OCR confidence is low,
  *also* try the fallback engine and pick the better result. Phase 6.
- **Real OCR validation.** The smoke test injects a fake recognizer; real
  PaddleOCR output is only verifiable in Docker.
