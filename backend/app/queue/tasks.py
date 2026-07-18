"""Celery tasks.

`process_job` lifecycle:
  load → mark processing → run pipeline → upload .xlsx → mark completed/failed

The pipeline is lazy-imported so the API container never pulls in
PaddleOCR/Camelot just by referencing this module.

`cleanup_expired_jobs` is a periodic task (Celery beat) that deletes
storage objects + DB rows for expired jobs and marks stuck-in-processing
jobs as failed.
"""

from __future__ import annotations

import logging
import tempfile
import time
import uuid
from pathlib import Path

from celery.exceptions import SoftTimeLimitExceeded

from app.config import get_settings
from app.models.database import session_scope
from app.queue.celery_app import celery_app
from app.services import job_service
from app.services import blog_service
from app.storage import get_storage

log = logging.getLogger(__name__)


@celery_app.task(name="converter.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="converter.process_job", bind=True)
def process_job(self, job_id: str) -> dict:  # noqa: ANN001
    jid = uuid.UUID(job_id)
    started = time.time()

    with session_scope() as db:
        job = job_service.get_job(db, jid)
        if job is None:
            log.warning("process_job: job %s not found, dropping", jid)
            return {"job_id": job_id, "status": "missing"}
        job_service.mark_processing(db, jid)
        job_service.notify_job_subscribers(db, jid)
        input_key = job.input_url
        mode = job.mode
        output_layout = job.output_layout
        extraction_scope = job.extraction_scope
        full_document_pages = job.full_document_pages
        trust_pdf_text = job.trust_pdf_text
        image_export = job.image_export
        document_type = job.document_type

    try:
        from app.pipeline.orchestrator import run_pipeline
        from app.services.job_service import output_key as build_output_key

        storage = get_storage()
        out_key = build_output_key(jid)

        with storage.open_local(input_key) as input_path, \
             tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        def _report_progress(stage: str, pct: int | None = None, extra: dict | None = None) -> None:
            try:
                with session_scope() as s:
                    job_service.mark_progress(s, jid, stage=stage, progress_pct=pct, extra=extra)
            except Exception:
                log.warning("progress update failed for job %s (stage=%s)", jid, stage, exc_info=True)

        try:
            result = run_pipeline(
                input_path,
                tmp_path,
                mode=mode,
                output_layout=output_layout,
                extraction_scope=extraction_scope,
                full_document_pages=full_document_pages,
                trust_pdf_text=trust_pdf_text,
                image_export=image_export,
                progress=_report_progress,
            )
            with tmp_path.open("rb") as fh:
                storage.put(out_key, fh, content_type=
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        finally:
            tmp_path.unlink(missing_ok=True)

        em = result.export_metrics

        with session_scope() as db:
            job_service.mark_completed(
                db, jid,
                output_url=out_key,
                page_count=result.page_count,
                pdf_type=result.pdf_type,
                metrics={
                    **result.timings_ms,
                    "table_count": len(result.tables),
                    "mean_confidence": result.mean_confidence,
                    "elapsed_ms": int((time.time() - started) * 1000),
                    "extraction_scope": extraction_scope,
                    "full_document_pages": full_document_pages,
                    "document_type": document_type,
                    "image_export": image_export,
                    **({"layout_row_count": result.layout_row_count} if result.layout_row_count is not None else {}),
                    **em,
                },
            )
            job_service.notify_job_subscribers(db, jid)
        return {"job_id": job_id, "status": "completed"}

    except SoftTimeLimitExceeded:
        log.warning("process_job %s exceeded soft time limit", jid)
        with session_scope() as db:
            job_service.mark_failed(db, jid, error="TIMEOUT: pipeline exceeded job_timeout_seconds")
            job_service.notify_job_subscribers(db, jid)
        return {"job_id": job_id, "status": "failed", "reason": "timeout"}

    except NotImplementedError as e:
        with session_scope() as db:
            job_service.mark_failed(db, jid, error=f"PIPELINE_NOT_IMPLEMENTED: {e}")
            job_service.notify_job_subscribers(db, jid)
        return {"job_id": job_id, "status": "failed", "reason": "not_implemented"}

    except Exception as e:
        log.exception("process_job %s failed", jid)
        with session_scope() as db:
            job_service.mark_failed(db, jid, error=f"{type(e).__name__}: {e}")
            job_service.notify_job_subscribers(db, jid)
        return {"job_id": job_id, "status": "failed", "reason": "exception"}


@celery_app.task(name="converter.cleanup_expired_jobs")
def cleanup_expired_jobs() -> dict:
    """Periodic sweeper. Runs from Celery beat (see celery_app.beat_schedule).

    Two passes per call:
      1. Delete files + rows for jobs past their `expires_at`.
      2. Mark stuck-in-processing jobs (worker hard-killed) as failed.
    """
    settings = get_settings()
    with session_scope() as db:
        cleanup_counts = job_service.cleanup_expired_jobs(db)
        stuck_count = job_service.mark_stuck_processing_as_failed(
            db, max_processing_seconds=settings.job_timeout_seconds * 2,
        )
    out = {**cleanup_counts, "stuck_marked_failed": stuck_count}
    if any(out.values()):
        log.info("cleanup_expired_jobs: %s", out)
    return out


@celery_app.task(name="converter.publish_scheduled_blog_posts")
def publish_scheduled_blog_posts() -> dict:
    with session_scope() as db:
        published = blog_service.publish_scheduled_posts(db)
    return {"published": published}
