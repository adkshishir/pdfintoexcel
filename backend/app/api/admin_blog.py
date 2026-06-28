"""Admin blog API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.internal_auth import require_admin_user
from app.models.database import get_db
from app.schemas.blog import (
    BlogCategoryItem,
    BlogGenerateRequest,
    BlogGenerateResponse,
    BlogPostAdminListItem,
    BlogPostCreate,
    BlogPostDetail,
    BlogTopicPickResponse,
)
from app.services import blog_generator, blog_service
from app.services.blog_topic_picker import pick_next_topic, resolve_topic
from app.services.llm_client import LlmError

router = APIRouter(
    prefix="/admin/blog",
    tags=["admin-blog"],
    dependencies=[Depends(require_admin_user)],
)


@router.get("/categories", response_model=list[BlogCategoryItem])
def admin_list_categories(db: Session = Depends(get_db)) -> list[BlogCategoryItem]:
    rows = blog_service.list_categories(db)
    return [
        BlogCategoryItem(id=str(r.id), slug=r.slug, name=r.name)
        for r in rows
    ]


@router.get("/next-topic", response_model=BlogTopicPickResponse)
def admin_next_topic(db: Session = Depends(get_db)) -> BlogTopicPickResponse:
    try:
        pick = pick_next_topic(db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    t = pick.topic
    return BlogTopicPickResponse(
        topic=t.topic,
        primary_keyword=t.primary_keyword,
        category_slug=t.category_slug,
        is_comparison=t.is_comparison,
        comparison_targets=list(t.comparison_targets),
        category_id=pick.category_id,
        rationale=pick.rationale,
    )


@router.post("/generate", status_code=201, response_model=BlogGenerateResponse)
def admin_generate_post(
    body: BlogGenerateRequest,
    db: Session = Depends(get_db),
) -> BlogGenerateResponse:
    cats = {c.slug: str(c.id) for c in blog_service.list_categories(db)}

    if body.topic:
        topic = resolve_topic(
            body.topic,
            category_slug=body.category_slug,
            is_comparison=body.is_comparison,
        )
        slug_key = body.category_slug or topic.category_slug
        category_id = cats.get(slug_key)
    else:
        try:
            pick = pick_next_topic(db)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        topic = pick.topic
        category_id = pick.category_id or cats.get(topic.category_slug)

    try:
        post, result = blog_generator.generate_and_save(
            db, topic, category_id=category_id
        )
    except LlmError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    return BlogGenerateResponse(
        post=BlogPostDetail.model_validate(post.to_admin_detail_dict()),
        quality_warnings=result.quality_warnings,
    )


@router.get("/posts", response_model=list[BlogPostAdminListItem])
def admin_list_posts(
    search: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[BlogPostAdminListItem]:
    posts = blog_service.list_all(db)
    if search:
        s = search.strip().lower()
        posts = [p for p in posts if s in p.title.lower() or s in p.slug.lower()]
    if status:
        posts = [p for p in posts if p.status == status]
    return [BlogPostAdminListItem.model_validate(p.to_list_dict()) for p in posts]


@router.post("/posts", status_code=201, response_model=BlogPostDetail)
def admin_create_post(data: BlogPostCreate, db: Session = Depends(get_db)) -> BlogPostDetail:
    try:
        post = blog_service.create_post(db, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return BlogPostDetail.model_validate(post.to_admin_detail_dict())


@router.get("/posts/{post_id}", response_model=BlogPostDetail)
def admin_get_post(post_id: uuid.UUID, db: Session = Depends(get_db)) -> BlogPostDetail:
    post = blog_service.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="not found")
    return BlogPostDetail.model_validate(post.to_admin_detail_dict())


@router.put("/posts/{post_id}", response_model=BlogPostDetail)
def admin_replace_post(
    post_id: uuid.UUID,
    data: BlogPostCreate,
    db: Session = Depends(get_db),
) -> BlogPostDetail:
    post = blog_service.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="not found")
    try:
        blog_service.replace_post(db, post, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return BlogPostDetail.model_validate(post.to_admin_detail_dict())


@router.delete("/posts/{post_id}", status_code=204)
def admin_delete_post(post_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    post = blog_service.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="not found")
    blog_service.delete_post(db, post)
    return Response(status_code=204)
