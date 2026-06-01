"""Job service — the only layer the API and worker share.

API never touches Celery directly; worker never touches FastAPI. Both call
through here so the contract is testable.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import BinaryIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.job import (
    ExtractionScope,
    FullDocumentPages,
    ImageExport,
    Job,
    JobMode,
    JobStatus,
    OutputLayout,
)
from app.storage import get_storage


def _now() -> datetime:
    return datetime.now(timezone.utc)


def input_key(job_id: uuid.UUID) -> str:
    return f"uploads/{job_id}/input.pdf"


def output_key(job_id: uuid.UUID) -> str:
    return f"outputs/{job_id}/output.xlsx"


def create_job(
    db: Session,
    *,
    upload: BinaryIO,
    filename: str,
    size_bytes: int,
    mode: JobMode = JobMode.FAST,
    output_layout: OutputLayout = OutputLayout.MERGED,
    extraction_scope: ExtractionScope = ExtractionScope.TABLES_ONLY,
    full_document_pages: FullDocumentPages = FullDocumentPages.SINGLE_SHEET,
    trust_pdf_text: bool = True,
    image_export: ImageExport = ImageExport.NONE,
) -> Job:
    """Persist file to storage, create a row in `queued` state, return it.

    Caller is responsible for enqueueing the Celery task after this returns
    (we keep that out of here to avoid a hard dependency on the queue from
    the service layer — useful for tests).
    """
    settings = get_settings()
    job_id = uuid.uuid4()

    key = input_key(job_id)
    get_storage().put(key, upload, content_type="application/pdf")

    job = Job(
        id=job_id,
        status=JobStatus.QUEUED,
        mode=mode,
        output_layout=output_layout,
        extraction_scope=extraction_scope,
        full_document_pages=full_document_pages,
        trust_pdf_text=trust_pdf_text,
        image_export=image_export,
        input_url=key,
        filename=filename,
        size_bytes=size_bytes,
        created_at=_now(),
        expires_at=_now() + timedelta(seconds=settings.job_ttl_seconds),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: uuid.UUID) -> Job | None:
    return db.execute(select(Job).where(Job.id == job_id)).scalar_one_or_none()


def notify_job_subscribers(db: Session, job_id: uuid.UUID) -> None:
    """Push current job row to Redis (for WebSocket clients)."""
    job = get_job(db, job_id)
    if job is None:
        return
    from app.queue.job_events import publish_job_update

    publish_job_update(job_id, job.to_dict())


def mark_processing(db: Session, job_id: uuid.UUID) -> None:
    job = get_job(db, job_id)
    if job is None:
        return
    job.status = JobStatus.PROCESSING
    job.started_at = _now()
    db.commit()


def mark_completed(
    db: Session,
    job_id: uuid.UUID,
    *,
    output_url: str,
    page_count: int | None,
    pdf_type: str | None,
    metrics: dict | None,
) -> None:
    job = get_job(db, job_id)
    if job is None:
        return
    job.status = JobStatus.COMPLETED
    job.completed_at = _now()
    job.output_url = output_url
    job.page_count = page_count
    job.pdf_type = pdf_type
    job.metrics = metrics
    db.commit()


def mark_failed(db: Session, job_id: uuid.UUID, *, error: str) -> None:
    job = get_job(db, job_id)
    if job is None:
        return
    job.status = JobStatus.FAILED
    job.completed_at = _now()
    job.error = error[:4000]  # cap to avoid runaway tracebacks
    db.commit()


def cleanup_expired_jobs(db: Session, *, batch_size: int = 200) -> dict[str, int]:
    """Delete files + DB rows for jobs past their `expires_at`.

    Returns a small counters dict for the caller (Celery beat task) to log.
    Idempotent: missing storage objects are tolerated.
    """
    storage = get_storage()
    now = _now()
    expired = (
        db.execute(
            select(Job).where(Job.expires_at < now).limit(batch_size)
        ).scalars().all()
    )

    deleted_rows = 0
    deleted_objects = 0
    for job in expired:
        for key in (job.input_url, job.output_url):
            if not key:
                continue
            try:
                storage.delete(key)
                deleted_objects += 1
            except Exception:
                # Don't let a stuck object block row deletion.
                pass
        db.delete(job)
        deleted_rows += 1
    if deleted_rows:
        db.commit()
    return {"rows": deleted_rows, "objects": deleted_objects}


def mark_stuck_processing_as_failed(db: Session, *, max_processing_seconds: int) -> int:
    """Watchdog: jobs whose `status='processing'` for too long are dead.

    Hard-killed worker processes leave jobs stuck in `processing`; this sweeps
    them. Called from the beat task alongside `cleanup_expired_jobs`.
    """
    cutoff = _now() - timedelta(seconds=max_processing_seconds)
    stuck = db.execute(
        select(Job).where(
            Job.status == JobStatus.PROCESSING,
            Job.started_at < cutoff,
        )
    ).scalars().all()
    for job in stuck:
        job.status = JobStatus.FAILED
        job.completed_at = _now()
        job.error = (job.error or "") + "TIMEOUT: worker exceeded job_timeout_seconds"
    if stuck:
        db.commit()
    return len(stuck)


def record_download(db: Session, job_id: uuid.UUID) -> None:
    """Increment download_count atomically (each successful download stream)."""
    from sqlalchemy import update

    db.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(download_count=Job.download_count + 1),
    )
    db.commit()
