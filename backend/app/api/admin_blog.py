"""Admin blog API — same auth as analytics (`X-Analytics-Key`)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.internal_auth import verify_analytics_key
from app.models.database import get_db
from app.schemas.blog import BlogPostCreate
from app.services import blog_service

router = APIRouter(
    prefix="/admin/blog",
    tags=["admin-blog"],
    dependencies=[Depends(verify_analytics_key)],
)


@router.get("/posts")
def admin_list_posts(db: Session = Depends(get_db)) -> list[dict]:
    posts = blog_service.list_all(db)
    return [p.to_list_dict() for p in posts]


@router.post("/posts", status_code=201)
def admin_create_post(data: BlogPostCreate, db: Session = Depends(get_db)) -> dict:
    try:
        post = blog_service.create_post(db, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return post.to_admin_detail_dict()


@router.get("/posts/{post_id}")
def admin_get_post(post_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    post = blog_service.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="not found")
    return post.to_admin_detail_dict()


@router.put("/posts/{post_id}")
def admin_replace_post(
    post_id: uuid.UUID,
    data: BlogPostCreate,
    db: Session = Depends(get_db),
) -> dict:
    post = blog_service.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="not found")
    try:
        blog_service.replace_post(db, post, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return post.to_admin_detail_dict()


@router.delete("/posts/{post_id}", status_code=204)
def admin_delete_post(post_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    post = blog_service.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="not found")
    blog_service.delete_post(db, post)
    return Response(status_code=204)
