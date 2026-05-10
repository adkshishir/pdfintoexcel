"""Admin blog API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.internal_auth import require_admin_user
from app.models.database import get_db
from app.schemas.blog import BlogPostAdminListItem, BlogPostCreate, BlogPostDetail, BlogPostPublicListItem
from app.services import blog_service

router = APIRouter(
    prefix="/admin/blog",
    tags=["admin-blog"],
    dependencies=[Depends(require_admin_user)],
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
