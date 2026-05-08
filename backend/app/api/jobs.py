"""Jobs router — upload, status, download.

Hard rule (CLAUDE.md): no pipeline imports here. Enqueueing is done by
sending the task by name so we don't import worker code into the API.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.limiter import limit_create_job, limit_download, limit_get_job
from app.config import get_settings
from app.models.database import get_db
from app.models.job import (
    ExtractionScope,
    FullDocumentPages,
    JobMode,
    JobStatus,
    OutputLayout,
)
from app.queue.tasks import process_job
from app.services import job_service
from app.storage import get_storage
from app.utils.security import looks_like_pdf

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(limit_create_job)])
async def create_job(
    file: UploadFile = File(...),
    mode: str = Form(default="fast"),
    output_layout: str = Form(default="merged"),
    extraction_scope: str = Form(default="tables_only"),
    full_document_pages: str = Form(default="single_sheet"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    settings = get_settings()

    if mode not in (JobMode.FAST, JobMode.ACCURATE):
        raise HTTPException(400, f"invalid mode: {mode}")
    if output_layout not in (OutputLayout.MERGED, OutputLayout.SPLIT):
        raise HTTPException(400, f"invalid output_layout: {output_layout}")
    if extraction_scope not in (ExtractionScope.TABLES_ONLY, ExtractionScope.FULL_DOCUMENT):
        raise HTTPException(400, f"invalid extraction_scope: {extraction_scope}")
    if full_document_pages not in (FullDocumentPages.SINGLE_SHEET, FullDocumentPages.PER_PAGE):
        raise HTTPException(400, f"invalid full_document_pages: {full_document_pages}")

    head = await file.read(1024)
    if not looks_like_pdf(head):
        raise HTTPException(415, "file is not a PDF")

    # Stream-validate size while building the on-disk file. We can't trust
    # `UploadFile.size` (None for some clients) so we count as we go.
    await file.seek(0)
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(1 << 20):
        total += len(chunk)
        if total > settings.max_upload_bytes:
            raise HTTPException(413, f"file exceeds {settings.max_upload_bytes} bytes")
        chunks.append(chunk)

    # Re-wrap in a BinaryIO for the storage put. (UploadFile.file would also
    # work, but we've already drained it.)
    import io
    body = io.BytesIO(b"".join(chunks))

    job = job_service.create_job(
        db,
        upload=body,
        filename=file.filename or "upload.pdf",
        size_bytes=total,
        mode=JobMode(mode),
        output_layout=OutputLayout(output_layout),
        extraction_scope=ExtractionScope(extraction_scope),
        full_document_pages=FullDocumentPages(full_document_pages),
    )

    # Importing the task here keeps API ↔ worker boundary clean *because*
    # `process_job` lazy-imports the pipeline (so the API container never
    # pulls in PaddleOCR/Camelot just by depending on tasks.py). Using
    # .delay() instead of send_task() so eager mode works in tests.
    process_job.delay(str(job.id))

    return job.to_dict()


@router.get("/{job_id}", dependencies=[Depends(limit_get_job)])
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> dict[str, Any]:
    job = job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    return job.to_dict()


@router.get("/{job_id}/download", dependencies=[Depends(limit_download)])
def download(job_id: uuid.UUID, db: Session = Depends(get_db)) -> StreamingResponse:
    job = job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    if job.status != JobStatus.COMPLETED or not job.output_url:
        raise HTTPException(409, f"job is {job.status}")

    job_service.record_download(db, job_id)

    storage = get_storage()
    data = storage.get(job.output_url)

    out_name = (job.filename.rsplit(".", 1)[0] if "." in job.filename else job.filename) + ".xlsx"

    def stream():
        yield data

    return StreamingResponse(
        stream(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
    )
