"""Public blog API (published posts only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services import blog_service

router = APIRouter(prefix="/blog", tags=["blog"])


@router.get("/posts")
def list_posts(db: Session = Depends(get_db)) -> list[dict]:
    posts = blog_service.list_published(db)
    return [
        {
            "id": str(p.id),
            "slug": p.slug,
            "title": p.title,
            "meta_description": p.meta_description,
            "published_at": p.published_at.isoformat() if p.published_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in posts
    ]


@router.get("/posts/{slug}")
def get_post(slug: str, db: Session = Depends(get_db)) -> dict:
    post = blog_service.get_published_by_slug(db, slug)
    if post is None:
        raise HTTPException(status_code=404, detail="not found")
    return post.to_public_dict()
