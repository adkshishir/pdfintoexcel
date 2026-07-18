"""Blog CMS persistence."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.blog_post import BlogPost
from app.models.seo import BlogCategory, BlogPostTag
from app.schemas.blog import BlogPostCreate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_slug(raw: str) -> str:
    s = raw.strip().lower()
    s = re.sub(r"\s+", "-", s)
    return s


def category_slug_map(db: Session) -> dict[uuid.UUID, str]:
    return {
        row.id: row.slug
        for row in db.scalars(select(BlogCategory)).all()
    }


def list_categories(db: Session) -> list[BlogCategory]:
    return list(db.scalars(select(BlogCategory).order_by(BlogCategory.slug)).all())


def list_published(db: Session) -> list[BlogPost]:
    stmt = (
        select(BlogPost)
        .where(BlogPost.status == "published")
        .order_by(BlogPost.updated_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_published_by_slug(db: Session, slug: str) -> BlogPost | None:
    norm = normalize_slug(slug)
    return db.scalar(
        select(BlogPost).where(BlogPost.slug == norm, BlogPost.status == "published")
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
    published_at = now if data.status == "published" else None
    category_uuid = uuid.UUID(data.category_id) if data.category_id else None
    post = BlogPost(
        slug=slug,
        title=data.title.strip(),
        meta_title=(data.meta_title.strip() if data.meta_title else None),
        meta_description=data.meta_description.strip(),
        body=data.body,
        status=data.status,
        scheduled_at=data.scheduled_at,
        cover_image_url=(data.cover_image_url.strip() if data.cover_image_url else None),
        category_id=category_uuid,
        og_title=(data.og_title.strip() if data.og_title else None),
        og_description=(data.og_description.strip() if data.og_description else None),
        og_image_url=(data.og_image_url.strip() if data.og_image_url else None),
        canonical_url=(data.canonical_url.strip() if data.canonical_url else None),
        robots_directives=(
            data.robots_directives.strip() if data.robots_directives else None
        ),
        keywords=(data.keywords.strip() if data.keywords else None),
        schema_jsonld=data.schema_jsonld,
        created_at=now,
        updated_at=now,
        published_at=published_at,
    )
    db.add(post)
    db.flush()
    for tag_id in data.tag_ids:
        db.add(BlogPostTag(post_id=post.id, tag_id=uuid.UUID(tag_id)))
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
    post.meta_title = data.meta_title.strip() if data.meta_title else None
    post.meta_description = data.meta_description.strip()
    post.body = data.body
    post.status = data.status
    post.scheduled_at = data.scheduled_at
    post.cover_image_url = data.cover_image_url.strip() if data.cover_image_url else None
    post.category_id = uuid.UUID(data.category_id) if data.category_id else None
    post.og_title = data.og_title.strip() if data.og_title else None
    post.og_description = data.og_description.strip() if data.og_description else None
    post.og_image_url = data.og_image_url.strip() if data.og_image_url else None
    post.canonical_url = data.canonical_url.strip() if data.canonical_url else None
    post.robots_directives = (
        data.robots_directives.strip() if data.robots_directives else None
    )
    post.keywords = data.keywords.strip() if data.keywords else None
    post.schema_jsonld = data.schema_jsonld
    post.updated_at = _utcnow()
    if data.status == "published" and post.published_at is None:
        post.published_at = _utcnow()
    elif data.status != "published":
        post.published_at = None
    db.query(BlogPostTag).filter(BlogPostTag.post_id == post.id).delete(synchronize_session=False)
    for tag_id in data.tag_ids:
        db.add(BlogPostTag(post_id=post.id, tag_id=uuid.UUID(tag_id)))
    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post: BlogPost) -> None:
    db.delete(post)
    db.commit()


def publish_scheduled_posts(db: Session) -> int:
    now = _utcnow()
    rows = list(
        db.scalars(
            select(BlogPost).where(
                BlogPost.status == "scheduled",
                BlogPost.scheduled_at.is_not(None),
                BlogPost.scheduled_at <= now,
            )
        ).all()
    )
    for row in rows:
        row.status = "published"
        row.published_at = now
        row.updated_at = now
    db.commit()
    return len(rows)
