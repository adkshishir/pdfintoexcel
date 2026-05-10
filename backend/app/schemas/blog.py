"""Request/response bodies for blog CMS APIs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BlogPostCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=160)
    title: str = Field(..., min_length=1, max_length=300)
    meta_title: str | None = Field(None, max_length=320)
    meta_description: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    status: str = Field(default="draft", pattern="^(draft|scheduled|published|archived)$")
    scheduled_at: datetime | None = None
    cover_image_url: str | None = None
    category_id: str | None = None
    tag_ids: list[str] = Field(default_factory=list)
    og_title: str | None = Field(None, max_length=300)
    og_description: str | None = None
    og_image_url: str | None = None
    canonical_url: str | None = Field(None, max_length=500)
    robots_directives: str | None = Field(None, max_length=120)
    keywords: str | None = Field(None, max_length=500)
    schema_jsonld: dict | None = None


class BlogPostPublicListItem(BaseModel):
    """Published posts index (marketing site)."""

    id: str
    slug: str
    title: str
    meta_description: str
    published_at: str | None
    updated_at: str | None


class BlogPostAdminListItem(BaseModel):
    """Admin post list rows (all statuses)."""

    id: str
    slug: str
    title: str
    meta_description: str
    status: str
    published_at: str | None
    updated_at: str | None


class BlogPostDetail(BaseModel):
    """Full post payload returned by public and admin detail endpoints."""

    id: str
    slug: str
    title: str
    meta_title: str | None
    meta_description: str
    body: str
    og_title: str | None
    og_description: str | None
    og_image_url: str | None
    canonical_url: str | None
    robots_directives: str | None
    keywords: str | None
    cover_image_url: str | None
    schema_jsonld: dict | None
    status: str
    scheduled_at: str | None
    published_at: str | None
    updated_at: str | None
