"""CMS blog posts for public site + SEO metadata."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    meta_title: Mapped[str | None] = mapped_column(String(320), nullable=True)
    meta_description: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("blog_categories.id", ondelete="SET NULL"), nullable=True
    )

    og_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    og_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    og_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    robots_directives: Mapped[str | None] = mapped_column(String(120), nullable=True)
    keywords: Mapped[str | None] = mapped_column(String(500), nullable=True)
    schema_jsonld: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (Index("blog_posts_status_idx", "status"),)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "slug": self.slug,
            "title": self.title,
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "body": self.body,
            "og_title": self.og_title,
            "og_description": self.og_description,
            "og_image_url": self.og_image_url,
            "canonical_url": self.canonical_url,
            "robots_directives": self.robots_directives,
            "keywords": self.keywords,
            "cover_image_url": self.cover_image_url,
            "schema_jsonld": self.schema_jsonld,
            "status": self.status,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_list_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "slug": self.slug,
            "title": self.title,
            "meta_description": self.meta_description,
            "status": self.status,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_admin_detail_dict(self) -> dict[str, Any]:
        out = self.to_public_dict()
        out["category_id"] = str(self.category_id) if self.category_id else None
        return out
