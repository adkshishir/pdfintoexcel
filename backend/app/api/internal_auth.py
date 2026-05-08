"""Shared secret verification for internal/admin HTTP APIs."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.config import Settings, get_settings


def verify_analytics_key(
    settings: Annotated[Settings, Depends(get_settings)],
    x_analytics_key: Annotated[str | None, Header()] = None,
) -> None:
    if not settings.analytics_api_key:
        raise HTTPException(status_code=503, detail="analytics API not configured")
    if not x_analytics_key or x_analytics_key != settings.analytics_api_key:
        raise HTTPException(status_code=401, detail="invalid analytics key")
