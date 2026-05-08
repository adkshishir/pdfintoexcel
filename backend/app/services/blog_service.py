"""Blog CMS persistence."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.blog_post import BlogPost
from app.schemas.blog import BlogPostCreate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_slug(raw: str) -> str:
    s = raw.strip().lower()
    s = re.sub(r"\s+", "-", s)
    return s


def list_published(db: Session) -> list[BlogPost]:
    stmt = (
        select(BlogPost)
        .where(BlogPost.published.is_(True))
        .order_by(BlogPost.updated_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_published_by_slug(db: Session, slug: str) -> BlogPost | None:
    norm = normalize_slug(slug)
    return db.scalar(
        select(BlogPost).where(BlogPost.slug == norm, BlogPost.published.is_(True))
    )


def list_all(db: Session) -> list[BlogPost]:
    stmt = select(BlogPost).order_by(BlogPost.updated_at.desc())
    return list(db.scalars(stmt).all())


def get_by_id(db: Session, post_id: uuid.UUID) -> BlogPost | None:
    return db.get(BlogPost, post_id)


def create_post(db: Session, data: BlogPostCreate) -> BlogPost:
    slug = normalize_slug(data.slug)
    if db.scalar(select(BlogPost).where(BlogPost.slug == slug)):
        raise ValueError("slug already exists")
    now = _utcnow()
    published_at = now if data.published else None
    post = BlogPost(
        slug=slug,
        title=data.title.strip(),
        meta_description=data.meta_description.strip(),
        body=data.body,
        published=data.published,
        og_title=(data.og_title.strip() if data.og_title else None),
        og_description=(data.og_description.strip() if data.og_description else None),
        og_image_url=(data.og_image_url.strip() if data.og_image_url else None),
        canonical_path=(data.canonical_path.strip() if data.canonical_path else None),
        keywords=(data.keywords.strip() if data.keywords else None),
        created_at=now,
        updated_at=now,
        published_at=published_at,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def replace_post(db: Session, post: BlogPost, data: BlogPostCreate) -> BlogPost:
    slug = normalize_slug(data.slug)
    if slug != post.slug:
        other = db.scalar(select(BlogPost).where(BlogPost.slug == slug))
        if other and other.id != post.id:
            raise ValueError("slug already exists")
    post.slug = slug
    post.title = data.title.strip()
    post.meta_description = data.meta_description.strip()
    post.body = data.body
    post.published = data.published
    post.og_title = data.og_title.strip() if data.og_title else None
    post.og_description = data.og_description.strip() if data.og_description else None
    post.og_image_url = data.og_image_url.strip() if data.og_image_url else None
    post.canonical_path = data.canonical_path.strip() if data.canonical_path else None
    post.keywords = data.keywords.strip() if data.keywords else None
    post.updated_at = _utcnow()
    if data.published and post.published_at is None:
        post.published_at = _utcnow()
    elif not data.published:
        post.published_at = None
    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post: BlogPost) -> None:
    db.delete(post)
    db.commit()
