"""JWT auth and admin RBAC helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.admin_user import AdminUser, RefreshToken, Role, UserRole


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return f"{base64.b64encode(salt).decode()}:{base64.b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        salt_b64, hash_b64 = encoded.split(":", 1)
        salt = base64.b64decode(salt_b64.encode())
        expected = base64.b64decode(hash_b64.encode())
    except Exception:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return hmac.compare_digest(digest, expected)


def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _role_names_for_user(db: Session, user_id: uuid.UUID) -> set[str]:
    stmt = (
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    return {r for r in db.scalars(stmt).all()}


def ensure_bootstrap_admin(db: Session) -> None:
    settings = get_settings()
    existing = db.scalar(select(AdminUser).where(AdminUser.email == settings.admin_bootstrap_email))
    if existing:
        return
    admin_role = db.scalar(select(Role).where(Role.name == "admin"))
    if admin_role is None:
        admin_role = Role(name="admin")
        db.add(admin_role)
        db.flush()
    user = AdminUser(
        email=settings.admin_bootstrap_email,
        password_hash=_hash_password(settings.admin_bootstrap_password),
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=admin_role.id))
    db.commit()


def authenticate_admin(db: Session, email: str, password: str) -> AdminUser | None:
    user = db.scalar(select(AdminUser).where(AdminUser.email == email.strip().lower()))
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login_at = _utcnow()
    db.commit()
    return user


def create_access_token(user: AdminUser, roles: set[str]) -> str:
    settings = get_settings()
    now = _utcnow()
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "roles": sorted(roles),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_access_ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(db: Session, user: AdminUser) -> str:
    settings = get_settings()
    raw = secrets.token_urlsafe(48)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=_hash_refresh_token(raw),
            expires_at=_utcnow() + timedelta(days=settings.jwt_refresh_ttl_days),
        )
    )
    db.commit()
    return raw


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def get_admin_from_access_token(db: Session, token: str) -> AdminUser | None:
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    user = db.get(AdminUser, uuid.UUID(user_id))
    if user is None or not user.is_active:
        return None
    roles = set(payload.get("roles", []))
    if "admin" not in roles:
        return None
    return user


def rotate_refresh_token(db: Session, raw_refresh_token: str) -> tuple[AdminUser, str] | None:
    hashed = _hash_refresh_token(raw_refresh_token)
    token_row = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hashed,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > _utcnow(),
        )
    )
    if token_row is None:
        return None
    user = db.get(AdminUser, token_row.user_id)
    if user is None or not user.is_active:
        return None
    token_row.revoked_at = _utcnow()
    new_raw = secrets.token_urlsafe(48)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=_hash_refresh_token(new_raw),
            expires_at=_utcnow() + timedelta(days=get_settings().jwt_refresh_ttl_days),
        )
    )
    db.commit()
    return user, new_raw


def revoke_refresh_token(db: Session, raw_refresh_token: str) -> None:
    hashed = _hash_refresh_token(raw_refresh_token)
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hashed))
    if row is None or row.revoked_at is not None:
        return
    row.revoked_at = _utcnow()
    db.commit()


def get_roles_for_user(db: Session, user_id: uuid.UUID) -> set[str]:
    return _role_names_for_user(db, user_id)


def list_admin_users(db: Session) -> list[dict]:
    users = list(db.scalars(select(AdminUser).order_by(AdminUser.created_at.desc())).all())
    out = []
    for u in users:
        out.append(
            {
                "id": str(u.id),
                "email": u.email,
                "is_active": u.is_active,
                "roles": sorted(_role_names_for_user(db, u.id)),
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                "created_at": u.created_at.isoformat(),
            }
        )
    return out


def revoke_all_user_refresh_tokens(db: Session, user_id: uuid.UUID) -> None:
    db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
    db.commit()
