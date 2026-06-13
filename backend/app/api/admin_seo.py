"""Admin SEO, landing pages, sitemap, links, and audit endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.internal_auth import require_admin_user
from app.models.admin_user import AdminUser
from app.models.database import get_db
from app.services import seo_service

router = APIRouter(prefix="/admin", tags=["admin-seo"], dependencies=[Depends(require_admin_user)])


@router.get("/seo/meta/{entity_type}/{entity_id}")
def get_seo_meta(entity_type: str, entity_id: str, db: Session = Depends(get_db)) -> dict:
    row = seo_service.get_or_create_meta(db, entity_type, entity_id)
    return seo_service.upsert_meta(
        db,
        entity_type,
        entity_id,
        {
            "title": row.title,
            "description": row.description,
            "keywords": row.keywords,
            "canonical_url": row.canonical_url,
            "robots": row.robots,
            "og_title": row.og_title,
            "og_description": row.og_description,
            "og_image": row.og_image,
        },
    )


@router.put("/seo/meta/{entity_type}/{entity_id}")
def put_seo_meta(entity_type: str, entity_id: str, payload: dict, db: Session = Depends(get_db)) -> dict:
    return seo_service.upsert_meta(db, entity_type, entity_id, payload)


@router.get("/seo/schema/{entity_type}/{entity_id}")
def get_schema(entity_type: str, entity_id: str, db: Session = Depends(get_db)) -> dict:
    row = seo_service.get_or_create_schema(db, entity_type, entity_id)
    return {
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "schema_type": row.schema_type,
        "payload_json": row.payload_json,
    }


@router.put("/seo/schema/{entity_type}/{entity_id}")
def put_schema(entity_type: str, entity_id: str, payload: dict, db: Session = Depends(get_db)) -> dict:
    return seo_service.upsert_schema(db, entity_type, entity_id, payload)


@router.get("/landing-pages")
def landing_pages(db: Session = Depends(get_db)) -> list[dict]:
    return seo_service.list_landing_pages(db)


@router.post("/landing-pages")
def save_landing_page(payload: dict, db: Session = Depends(get_db)) -> dict:
    return seo_service.upsert_landing_page(db, payload)


@router.get("/landing-pages/{page_id}")
def get_landing_page(page_id: str, db: Session = Depends(get_db)) -> dict:
    row = seo_service.get_landing_page(db, page_id)
    if row is None:
        raise HTTPException(status_code=404, detail="landing page not found")
    return row


@router.get("/site/internal-links")
def list_internal_links(db: Session = Depends(get_db)) -> list[dict]:
    return seo_service.get_internal_link_suggestions(db)


@router.post("/site/internal-links/suggest")
def suggest_internal_links(payload: dict, db: Session = Depends(get_db)) -> list[dict]:
    return seo_service.suggest_links_for_entity(
        db, source_type=payload.get("source_type", "blog"), source_id=payload.get("source_id", "unknown")
    )


@router.get("/site/sitemap/exclusions")
def sitemap_exclusions(db: Session = Depends(get_db)) -> list[dict]:
    return seo_service.list_sitemap_exclusions(db)


@router.post("/site/sitemap/exclusions")
def add_sitemap_exclusion(payload: dict, db: Session = Depends(get_db)) -> dict:
    return seo_service.add_sitemap_exclusion(db, payload["path"], payload.get("reason"))


@router.post("/site/sitemap/rebuild")
def rebuild_sitemap(db: Session = Depends(get_db)) -> dict:
    return seo_service.rebuild_sitemap(db)


@router.get("/audit-logs")
def audit_logs(db: Session = Depends(get_db)) -> list[dict]:
    return seo_service.list_audit_logs(db)


@router.post("/audit-logs")
def create_audit_log(
    payload: dict,
    user: AdminUser = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> dict:
    seo_service.write_audit_log(
        db,
        actor_user_id=str(user.id),
        action=payload["action"],
        entity_type=payload["entity_type"],
        entity_id=payload["entity_id"],
        summary=payload.get("summary"),
        payload=payload.get("payload"),
    )
    return {"ok": True}
