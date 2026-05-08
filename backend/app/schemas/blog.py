"""Request/response bodies for blog CMS APIs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BlogPostCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=160)
    title: str = Field(..., min_length=1, max_length=300)
    meta_description: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    published: bool = False
    og_title: str | None = Field(None, max_length=300)
    og_description: str | None = None
    og_image_url: str | None = None
    canonical_path: str | None = Field(None, max_length=500)
    keywords: str | None = Field(None, max_length=500)
