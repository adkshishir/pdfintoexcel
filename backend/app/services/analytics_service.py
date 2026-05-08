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
