"""Internal analytics APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.internal_auth import require_admin_user, verify_analytics_key
from app.models.database import get_db
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", dependencies=[Depends(verify_analytics_key)])
def analytics_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    return analytics_service.get_summary(db)


@router.get("/overview", dependencies=[Depends(require_admin_user)])
def admin_overview(db: Session = Depends(get_db)) -> dict[str, Any]:
    return analytics_service.get_overview(db)


@router.get("/timeseries", dependencies=[Depends(require_admin_user)])
def admin_timeseries(
    range: str = "30d",
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return analytics_service.get_timeseries(db, range_value=range, start_date=start_date, end_date=end_date)


@router.get("/top-pages", dependencies=[Depends(require_admin_user)])
def admin_top_pages(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return analytics_service.get_top_pages(db)
