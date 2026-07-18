"""Jobs router — upload, status, download.

Hard rule (CLAUDE.md): no pipeline imports here. Enqueueing is done by
sending the task by name so we don't import worker code into the API.
"""

from __future__ import annotations

import io
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.limiter import limit_create_job, limit_download, limit_get_job
from app.config import get_settings
from app.models.database import get_db
from app.models.job import (
    DocumentType,
    ExtractionScope,
    FullDocumentPages,
    ImageExport,
    JobMode,
    JobStatus,
    OutputLayout,
)
from app.queue.tasks import process_job
from app.services import job_service
from app.storage import get_storage
from app.utils.http_headers import content_disposition_attachment
from app.utils.security import looks_like_pdf

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(limit_create_job)])
async def create_job(
    file: UploadFile = File(...),
    mode: str = Form(default="fast"),
    output_layout: str = Form(default="merged"),
    extraction_scope: str = Form(default="tables_only"),
    full_document_pages: str = Form(default="single_sheet"),
    document_type: str = Form(default="normal"),
    image_export: str = Form(default="none"),
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
    if document_type not in (DocumentType.NORMAL, DocumentType.SCANNED):
        raise HTTPException(400, f"invalid document_type: {document_type}")
    if image_export not in (ImageExport.NONE, ImageExport.FIGURES, ImageExport.ONLY):
        raise HTTPException(400, f"invalid image_export: {image_export}")

    head = await file.read(1024)
    if not looks_like_pdf(head):
        raise HTTPException(415, "file is not a PDF")

    await file.seek(0)
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(1 << 20):
        total += len(chunk)
        if total > settings.max_upload_bytes:
            raise HTTPException(413, f"file exceeds {settings.max_upload_bytes} bytes")
        chunks.append(chunk)

    trust_pdf_text = document_type == DocumentType.NORMAL
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
        trust_pdf_text=trust_pdf_text,
        image_export=ImageExport(image_export),
    )

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
    out_name = (job.filename.rsplit(".", 1)[0] if "." in job.filename else job.filename) + ".xlsx"

    return StreamingResponse(
        storage.iter_bytes(job.output_url),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": content_disposition_attachment(out_name)},
    )
