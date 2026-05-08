"""Job model — see PROJECT_PLAN.md §6 for schema rationale."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class JobStatus(StrEnum):
    PENDING    = "pending"     # row created, file not yet uploaded
    QUEUED     = "queued"      # uploaded + enqueued, worker hasn't picked up
    PROCESSING = "processing"  # worker is running the pipeline
    COMPLETED  = "completed"
    FAILED     = "failed"


class JobMode(StrEnum):
    FAST     = "fast"
    ACCURATE = "accurate"


class OutputLayout(StrEnum):
    MERGED = "merged"   # consecutive same-header tables → one sheet (default)
    SPLIT  = "split"    # one sheet per detected table


class ExtractionScope(StrEnum):
    TABLES_ONLY = "tables_only"       # reconstruct → clean → typed Excel (default)
    FULL_DOCUMENT = "full_document"   # structured reading-order workbook from words + tables


class FullDocumentPages(StrEnum):
    """Used when extraction_scope is full_document."""

    SINGLE_SHEET = "single_sheet"   # default — one "Document" sheet
    PER_PAGE = "per_page"          # one worksheet per PDF page


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Job(Base):
    __tablename__ = "jobs"

    # `Uuid` is portable: native UUID on Postgres, CHAR(32) on SQLite/MySQL.
    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=JobStatus.PENDING)
    mode: Mapped[str] = mapped_column(String(16), nullable=False, default=JobMode.FAST)
    output_layout: Mapped[str] = mapped_column(String(16), nullable=False, default=OutputLayout.MERGED)
    extraction_scope: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ExtractionScope.TABLES_ONLY,
    )
    full_document_pages: Mapped[str] = mapped_column(
        String(20), nullable=False, default=FullDocumentPages.SINGLE_SHEET,
    )

    input_url: Mapped[str] = mapped_column(Text, nullable=False)
    output_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    filename: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int | None] = mapped_column(nullable=True)
    pdf_type: Mapped[str | None] = mapped_column(String(16), nullable=True)

    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # `JSON` is portable: JSONB on Postgres, TEXT-with-JSON-encoding elsewhere.
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    download_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at:   Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    started_at:   Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at:   Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("jobs_status_idx", "status"),
        # Partial index is Postgres-specific; SQLAlchemy silently ignores
        # `postgresql_where` on other dialects.
        Index("jobs_expires_at_idx", "expires_at", postgresql_where="status = 'completed'"),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id":           str(self.id),
            "status":       self.status,
            "mode":         self.mode,
            "output_layout": self.output_layout,
            "extraction_scope": self.extraction_scope,
            "full_document_pages": self.full_document_pages,
            "filename":     self.filename,
            "size_bytes":   self.size_bytes,
            "page_count":   self.page_count,
            "pdf_type":     self.pdf_type,
            "error":        self.error,
            "metrics":      self.metrics,
            "download_count": self.download_count,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
            "started_at":   self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "expires_at":   self.expires_at.isoformat() if self.expires_at else None,
        }
