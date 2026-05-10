"""Admin authentication APIs."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.internal_auth import require_admin_user
from app.models.admin_user import AdminUser
from app.models.database import get_db
from app.schemas.auth import AdminMeResponse, AuthTokens, LoginRequest, RefreshRequest
from app.services import auth_service

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=AuthTokens)
def admin_login(data: LoginRequest, db: Session = Depends(get_db)) -> AuthTokens:
    auth_service.ensure_bootstrap_admin(db)
    user = auth_service.authenticate_admin(db, data.email, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid credentials")
    roles = auth_service.get_roles_for_user(db, user.id)
    if "admin" not in roles:
        raise HTTPException(status_code=403, detail="admin role required")
    return AuthTokens(
        access_token=auth_service.create_access_token(user, roles),
        refresh_token=auth_service.create_refresh_token(db, user),
    )


@router.post("/refresh", response_model=AuthTokens)
def admin_refresh(data: RefreshRequest, db: Session = Depends(get_db)) -> AuthTokens:
    rotated = auth_service.rotate_refresh_token(db, data.refresh_token)
    if rotated is None:
        raise HTTPException(status_code=401, detail="invalid refresh token")
    user, refresh_token = rotated
    roles = auth_service.get_roles_for_user(db, user.id)
    return AuthTokens(
        access_token=auth_service.create_access_token(user, roles),
        refresh_token=refresh_token,
    )


@router.post("/logout")
def admin_logout(data: RefreshRequest, db: Session = Depends(get_db)) -> dict:
    auth_service.revoke_refresh_token(db, data.refresh_token)
    return {"ok": True}


@router.get("/me", response_model=AdminMeResponse)
def admin_me(
    user: AdminUser = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminMeResponse:
    return AdminMeResponse(
        id=str(user.id),
        email=user.email,
        roles=sorted(auth_service.get_roles_for_user(db, uuid.UUID(str(user.id)))),
    )


@router.get("/users")
def admin_users(
    _: AdminUser = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return auth_service.list_admin_users(db)
