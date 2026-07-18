"""Public blog API (published posts only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.schemas.blog import BlogPostDetail, BlogPostPublicListItem
from app.services import blog_service

router = APIRouter(prefix="/blog", tags=["blog"])


@router.get("/posts", response_model=list[BlogPostPublicListItem])
def list_posts(db: Session = Depends(get_db)) -> list[BlogPostPublicListItem]:
    posts = blog_service.list_published(db)
    cat_map = blog_service.category_slug_map(db)
    return [
        BlogPostPublicListItem(
            id=str(p.id),
            slug=p.slug,
            title=p.title,
            meta_description=p.meta_description,
            category_slug=cat_map.get(p.category_id) if p.category_id else None,
            published_at=p.published_at.isoformat() if p.published_at else None,
            updated_at=p.updated_at.isoformat() if p.updated_at else None,
        )
        for p in posts
    ]


@router.get("/posts/{slug}", response_model=BlogPostDetail)
def get_post(slug: str, db: Session = Depends(get_db)) -> BlogPostDetail:
    post = blog_service.get_published_by_slug(db, slug)
    if post is None:
        raise HTTPException(status_code=404, detail="not found")
    return BlogPostDetail.model_validate(post.to_public_dict())
