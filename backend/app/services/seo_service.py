"""SEO and growth management services."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.seo import (
    AuditLog,
    InternalLinkSuggestion,
    LandingPage,
    SchemaDocument,
    SeoMeta,
    SitemapExclusion,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_or_create_meta(db: Session, entity_type: str, entity_id: str) -> SeoMeta:
    row = db.scalar(
        select(SeoMeta).where(SeoMeta.entity_type == entity_type, SeoMeta.entity_id == entity_id)
    )
    if row is None:
        row = SeoMeta(entity_type=entity_type, entity_id=entity_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def upsert_meta(db: Session, entity_type: str, entity_id: str, payload: dict) -> dict:
    row = get_or_create_meta(db, entity_type, entity_id)
    for key in [
        "title",
        "description",
        "keywords",
        "canonical_url",
        "robots",
        "og_title",
        "og_description",
        "og_image",
    ]:
        if key in payload:
            setattr(row, key, payload[key])
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return {
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "title": row.title,
        "description": row.description,
        "keywords": row.keywords,
        "canonical_url": row.canonical_url,
        "robots": row.robots,
        "og_title": row.og_title,
        "og_description": row.og_description,
        "og_image": row.og_image,
    }


def get_or_create_schema(db: Session, entity_type: str, entity_id: str) -> SchemaDocument:
    row = db.scalar(
        select(SchemaDocument).where(
            SchemaDocument.entity_type == entity_type, SchemaDocument.entity_id == entity_id
        )
    )
    if row is None:
        row = SchemaDocument(
            entity_type=entity_type,
            entity_id=entity_id,
            schema_type="WebSite",
            payload_json={"@context": "https://schema.org", "@type": "WebSite"},
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def upsert_schema(db: Session, entity_type: str, entity_id: str, payload: dict) -> dict:
    row = get_or_create_schema(db, entity_type, entity_id)
    row.schema_type = str(payload.get("schema_type", row.schema_type))
    row.payload_json = payload.get("payload_json", row.payload_json)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return {
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "schema_type": row.schema_type,
        "payload_json": row.payload_json,
    }


def list_landing_pages(db: Session) -> list[dict]:
    pages = list(db.scalars(select(LandingPage).order_by(LandingPage.updated_at.desc())).all())
    return [
        {"id": str(p.id), "slug": p.slug, "title": p.title, "status": p.status, "updated_at": p.updated_at.isoformat()}
        for p in pages
    ]


def get_landing_page(db: Session, page_id: str) -> dict | None:
    row = db.get(LandingPage, uuid.UUID(page_id))
    if row is None:
        return None
    return {
        "id": str(row.id),
        "slug": row.slug,
        "title": row.title,
        "body": row.body,
        "faq_items": row.faq_items,
        "internal_links": row.internal_links,
        "status": row.status,
        "updated_at": row.updated_at.isoformat(),
    }


def upsert_landing_page(db: Session, payload: dict) -> dict:
    page_id = payload.get("id")
    row = db.get(LandingPage, uuid.UUID(page_id)) if page_id else None
    if row is None:
        row = LandingPage(
            slug=payload["slug"],
            title=payload["title"],
            body=payload.get("body", ""),
            faq_items=payload.get("faq_items", []),
            internal_links=payload.get("internal_links", []),
            status=payload.get("status", "draft"),
        )
        db.add(row)
    else:
        row.slug = payload["slug"]
        row.title = payload["title"]
        row.body = payload.get("body", row.body)
        row.faq_items = payload.get("faq_items", row.faq_items)
        row.internal_links = payload.get("internal_links", row.internal_links)
        row.status = payload.get("status", row.status)
        row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return {"id": str(row.id), "slug": row.slug, "title": row.title, "status": row.status}


def get_internal_link_suggestions(db: Session) -> list[dict]:
    rows = list(
        db.scalars(select(InternalLinkSuggestion).order_by(InternalLinkSuggestion.created_at.desc())).all()
    )
    return [
        {
            "id": str(r.id),
            "source_type": r.source_type,
            "source_id": r.source_id,
            "target_path": r.target_path,
            "anchor_text": r.anchor_text,
            "score": r.score,
            "accepted": r.accepted,
        }
        for r in rows
    ]


def suggest_links_for_entity(db: Session, source_type: str, source_id: str) -> list[dict]:
    suggestions = [
        {"target_path": "/pdf-table-extractor", "anchor_text": "pdf table extractor", "score": 0.86},
        {"target_path": "/convert-scanned-pdf-to-excel", "anchor_text": "scanned pdf to excel", "score": 0.81},
    ]
    out: list[dict] = []
    for s in suggestions:
        row = InternalLinkSuggestion(
            source_type=source_type,
            source_id=source_id,
            target_path=s["target_path"],
            anchor_text=s["anchor_text"],
            score=s["score"],
            accepted=False,
        )
        db.add(row)
        db.flush()
        out.append({"id": str(row.id), **s, "accepted": False})
    db.commit()
    return out


def rebuild_sitemap(db: Session) -> dict:
    excluded = list(
        db.scalars(select(SitemapExclusion).where(SitemapExclusion.is_active.is_(True))).all()
    )
    return {"ok": True, "excluded_paths": [e.path for e in excluded], "generated_at": _utcnow().isoformat()}


def list_sitemap_exclusions(db: Session) -> list[dict]:
    rows = list(
        db.scalars(select(SitemapExclusion).order_by(SitemapExclusion.created_at.desc())).all()
    )
    return [{"id": str(r.id), "path": r.path, "reason": r.reason, "is_active": r.is_active} for r in rows]


def add_sitemap_exclusion(db: Session, path: str, reason: str | None = None) -> dict:
    row = SitemapExclusion(path=path, reason=reason, is_active=True)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": str(row.id), "path": row.path, "reason": row.reason, "is_active": row.is_active}


def write_audit_log(
    db: Session,
    *,
    actor_user_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str,
    summary: str | None = None,
    payload: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=uuid.UUID(actor_user_id) if actor_user_id else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
            payload=payload,
        )
    )
    db.commit()


def list_audit_logs(db: Session) -> list[dict]:
    rows = list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200)).all())
    return [
        {
            "id": str(r.id),
            "actor_user_id": str(r.actor_user_id) if r.actor_user_id else None,
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "summary": r.summary,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
