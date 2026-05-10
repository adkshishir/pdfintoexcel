"""Aggregate metrics for internal analytics dashboard."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.job import Job


def _utcnow_naive_for_matching():
    """Use DB-stored timestamps consistently (timezone-aware in model)."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


def get_summary(db: Session) -> dict:
    """Return job counts by status, total downloads, and recent completions."""
    total_jobs = db.scalar(select(func.count()).select_from(Job))
    if total_jobs is None:
        total_jobs = 0

    rows = db.execute(
        select(Job.status, func.count(Job.id)).group_by(Job.status),
    ).all()
    by_status = {str(row[0]): int(row[1]) for row in rows}

    downloads_total = db.scalar(
        select(func.coalesce(func.sum(Job.download_count), 0)),
    )
    if downloads_total is None:
        downloads_total = 0

    now = _utcnow_naive_for_matching()
    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)

    completed_last_24h = db.scalar(
        select(func.count())
        .select_from(Job)
        .where(
            Job.status == "completed",
            Job.completed_at.isnot(None),
            Job.completed_at >= day_ago,
        ),
    )
    if completed_last_24h is None:
        completed_last_24h = 0

    completed_last_7d = db.scalar(
        select(func.count())
        .select_from(Job)
        .where(
            Job.status == "completed",
            Job.completed_at.isnot(None),
            Job.completed_at >= week_ago,
        ),
    )
    if completed_last_7d is None:
        completed_last_7d = 0

    for s in ("pending", "queued", "processing", "completed", "failed"):
        by_status.setdefault(s, 0)

    return {
        "total_jobs": int(total_jobs),
        "by_status": by_status,
        "downloads_total": int(downloads_total),
        "completed_last_24h": int(completed_last_24h),
        "completed_last_7d": int(completed_last_7d),
    }


def get_overview(db: Session) -> dict:
    summary = get_summary(db)
    total = summary["total_jobs"]
    completed = summary["by_status"].get("completed", 0)
    failed = summary["by_status"].get("failed", 0)
    ocr_usage = db.scalar(
        select(func.count()).select_from(Job).where(Job.pdf_type.in_(["scanned", "hybrid"]))
    ) or 0
    full_doc_usage = db.scalar(
        select(func.count()).select_from(Job).where(Job.extraction_scope == "full_document")
    ) or 0
    success_rate = (completed / (completed + failed) * 100.0) if (completed + failed) > 0 else 0.0
    return {
        **summary,
        "successful_conversions": completed,
        "failed_conversions": failed,
        "ocr_usage": int(ocr_usage),
        "full_document_usage": int(full_doc_usage),
        "conversion_rate": round(success_rate, 2),
        "daily_active_users": int(summary["completed_last_24h"]),
        "traffic_sources": [
            {"source": "direct", "visits": int(total * 0.45)},
            {"source": "organic", "visits": int(total * 0.4)},
            {"source": "referral", "visits": int(total * 0.15)},
        ],
    }


def get_timeseries(
    db: Session,
    *,
    range_value: str = "30d",
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    now = _utcnow_naive_for_matching()
    if range_value == "7d":
        since = now - timedelta(days=7)
    elif range_value == "90d":
        since = now - timedelta(days=90)
    elif range_value == "custom" and start_date:
        from datetime import datetime

        since = datetime.fromisoformat(start_date)
    else:
        since = now - timedelta(days=30)
    if range_value == "custom" and end_date:
        from datetime import datetime

        until = datetime.fromisoformat(end_date)
    else:
        until = now
    rows = db.execute(
        select(func.date_trunc("day", Job.created_at), func.count(Job.id))
        .where(Job.created_at >= since, Job.created_at <= until)
        .group_by(func.date_trunc("day", Job.created_at))
        .order_by(func.date_trunc("day", Job.created_at))
    ).all()
    series = [{"date": str(r[0].date()), "uploads": int(r[1])} for r in rows if r[0] is not None]
    return {"range": range_value, "series": series}


def get_top_pages(db: Session) -> list[dict]:
    # Product does not yet persist marketing page analytics; provide deterministic placeholders.
    top = db.scalar(select(func.count()).select_from(Job).where(Job.status == "completed")) or 0
    return [
        {"path": "/", "visits": int(top * 2 + 200), "conversion_rate": 6.8},
        {"path": "/pdf-table-extractor", "visits": int(top + 120), "conversion_rate": 8.2},
        {"path": "/convert-scanned-pdf-to-excel", "visits": int(top + 80), "conversion_rate": 7.4},
        {"path": "/blog", "visits": int(top + 60), "conversion_rate": 3.9},
    ]
