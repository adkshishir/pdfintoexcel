"""Auth dependencies for internal/admin HTTP APIs."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models.admin_user import AdminUser
from app.models.database import get_db
from app.services import auth_service


def verify_analytics_key(
    settings: Annotated[Settings, Depends(get_settings)],
    x_analytics_key: Annotated[str | None, Header()] = None,
) -> None:
    if not settings.analytics_api_key:
        raise HTTPException(status_code=503, detail="analytics API not configured")
    if not x_analytics_key or x_analytics_key != settings.analytics_api_key:
        raise HTTPException(status_code=401, detail="invalid analytics key")


_bearer = HTTPBearer(auto_error=False)


def require_admin_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminUser:
    if creds is None:
        raise HTTPException(status_code=401, detail="missing bearer token")
    user = auth_service.get_admin_from_access_token(db, creds.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    return user
