"""Public landing page API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.seo import LandingPage

router = APIRouter(prefix="/landing-pages", tags=["landing-pages"])


@router.get("")
def list_landing_pages(db: Session = Depends(get_db)) -> list[dict]:
    rows = list(
        db.scalars(
            select(LandingPage).where(LandingPage.status == "published").order_by(LandingPage.updated_at.desc())
        ).all()
    )
    return [
        {"id": str(r.id), "slug": r.slug, "title": r.title, "updated_at": r.updated_at.isoformat()}
        for r in rows
    ]


@router.get("/{slug}")
def get_landing_page(slug: str, db: Session = Depends(get_db)) -> dict:
    row = db.scalar(select(LandingPage).where(LandingPage.slug == slug, LandingPage.status == "published"))
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    return {
        "id": str(row.id),
        "slug": row.slug,
        "title": row.title,
        "body": row.body,
        "faq_items": row.faq_items,
        "internal_links": row.internal_links,
        "updated_at": row.updated_at.isoformat(),
    }
