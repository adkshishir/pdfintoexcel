"""Internal analytics API (protected by shared secret)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.internal_auth import verify_analytics_key
from app.models.database import get_db
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", dependencies=[Depends(verify_analytics_key)])
def analytics_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    return analytics_service.get_summary(db)
