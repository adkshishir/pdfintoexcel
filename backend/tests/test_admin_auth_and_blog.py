"""Admin auth + admin/public blog API tests (SQLite temp DB)."""

from __future__ import annotations

import os
from typing import Any

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def admin_blog_client(tmp_path) -> TestClient:
    db_path = tmp_path / "admin_blog.db"
    storage_root = tmp_path / "storage"
    storage_root.mkdir()

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["STORAGE_BACKEND"] = "local"
    os.environ["STORAGE_LOCAL_ROOT"] = str(storage_root)
    os.environ["JWT_SECRET"] = "test-jwt-secret-min-32-chars-long!!"
    os.environ["ADMIN_BOOTSTRAP_EMAIL"] = "admin@example.com"
    os.environ["ADMIN_BOOTSTRAP_PASSWORD"] = "bootstrap-pass-123"

    from app import config, storage
    from app.models import database

    config.get_settings.cache_clear()
    storage.get_storage.cache_clear()
    database._engine = None
    database._SessionLocal = None

    from app.models.database import Base, get_engine

    import app.models.admin_user  # noqa: F401
    import app.models.blog_post  # noqa: F401
    import app.models.seo  # noqa: F401

    Base.metadata.create_all(get_engine())

    from app.api import limiter as lim

    lim.enabled = False

    from app.main import app as fastapi_app

    return TestClient(fastapi_app)


def _login(admin_blog_client: TestClient) -> dict[str, Any]:
    r = admin_blog_client.post(
        "/api/admin/auth/login",
        json={
            "email": "admin@example.com",
            "password": "bootstrap-pass-123",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _minimal_post(slug: str, status: str = "draft") -> dict[str, Any]:
    return {
        "slug": slug,
        "title": f"Title {slug}",
        "meta_description": f"Meta for {slug}",
        "body": f"Body {slug}",
        "status": status,
        "tag_ids": [],
    }


def test_login_wrong_password(admin_blog_client: TestClient) -> None:
    r = admin_blog_client.post(
        "/api/admin/auth/login",
        json={"email": "admin@example.com", "password": "wrong"},
    )
    assert r.status_code == 401


def test_login_success_and_me(admin_blog_client: TestClient) -> None:
    tokens = _login(admin_blog_client)
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens.get("token_type") == "bearer"

    r = admin_blog_client.get("/api/admin/auth/me")
    assert r.status_code == 401

    r = admin_blog_client.get(
        "/api/admin/auth/me",
        headers=_auth_headers("not-a-jwt"),
    )
    assert r.status_code == 401

    r = admin_blog_client.get(
        "/api/admin/auth/me",
        headers=_auth_headers(tokens["access_token"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "admin@example.com"
    assert "admin" in body["roles"]


def test_refresh_invalid_and_rotate(admin_blog_client: TestClient) -> None:
    r = admin_blog_client.post(
        "/api/admin/auth/refresh",
        json={"refresh_token": "x" * 40},
    )
    assert r.status_code == 401

    tokens = _login(admin_blog_client)
    r = admin_blog_client.post(
        "/api/admin/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert r.status_code == 200
    new_tokens = r.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
    # Access token is re-issued; payload may match within the same second.

    r = admin_blog_client.post(
        "/api/admin/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert r.status_code == 401


def test_logout_revokes_refresh(admin_blog_client: TestClient) -> None:
    tokens = _login(admin_blog_client)
    r = admin_blog_client.post(
        "/api/admin/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    r = admin_blog_client.post(
        "/api/admin/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert r.status_code == 401


def test_admin_blog_requires_auth(admin_blog_client: TestClient) -> None:
    r = admin_blog_client.get("/api/admin/blog/posts")
    assert r.status_code == 401
    r = admin_blog_client.post("/api/admin/blog/posts", json=_minimal_post("x"))
    assert r.status_code == 401


def test_blog_flow_draft_hidden_publish_visible(admin_blog_client: TestClient) -> None:
    tokens = _login(admin_blog_client)
    h = _auth_headers(tokens["access_token"])

    r = admin_blog_client.post(
        "/api/admin/blog/posts",
        headers=h,
        json=_minimal_post("my-draft", "draft"),
    )
    assert r.status_code == 201
    pid = r.json()["id"]

    r = admin_blog_client.get("/api/blog/posts")
    assert r.status_code == 200
    assert not any(p["slug"] == "my-draft" for p in r.json())

    r = admin_blog_client.get("/api/blog/posts/my-draft")
    assert r.status_code == 404

    r = admin_blog_client.put(
        f"/api/admin/blog/posts/{pid}",
        headers=h,
        json=_minimal_post("my-draft", "published"),
    )
    assert r.status_code == 200

    r = admin_blog_client.get("/api/blog/posts")
    assert r.status_code == 200
    slugs = [p["slug"] for p in r.json()]
    assert "my-draft" in slugs

    r = admin_blog_client.get("/api/blog/posts/my-draft")
    assert r.status_code == 200
    assert r.json()["slug"] == "my-draft"
    assert r.json()["status"] == "published"


def test_duplicate_slug_conflict(admin_blog_client: TestClient) -> None:
    tokens = _login(admin_blog_client)
    h = _auth_headers(tokens["access_token"])
    payload = _minimal_post("dup-slug", "draft")

    r = admin_blog_client.post("/api/admin/blog/posts", headers=h, json=payload)
    assert r.status_code == 201

    r = admin_blog_client.post("/api/admin/blog/posts", headers=h, json=payload)
    assert r.status_code == 409


def test_admin_list_search_and_status(admin_blog_client: TestClient) -> None:
    tokens = _login(admin_blog_client)
    h = _auth_headers(tokens["access_token"])

    admin_blog_client.post(
        "/api/admin/blog/posts",
        headers=h,
        json=_minimal_post("alpha-search", "draft"),
    )
    admin_blog_client.post(
        "/api/admin/blog/posts",
        headers=h,
        json=_minimal_post("beta-pub", "published"),
    )

    r = admin_blog_client.get("/api/admin/blog/posts?search=alpha", headers=h)
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 1
    assert all("alpha" in p["slug"].lower() or "alpha" in p["title"].lower() for p in rows)

    r = admin_blog_client.get("/api/admin/blog/posts?status=published", headers=h)
    assert r.status_code == 200
    assert all(p["status"] == "published" for p in r.json())
    assert any(p["slug"] == "beta-pub" for p in r.json())


def test_delete_post(admin_blog_client: TestClient) -> None:
    tokens = _login(admin_blog_client)
    h = _auth_headers(tokens["access_token"])

    r = admin_blog_client.post(
        "/api/admin/blog/posts",
        headers=h,
        json=_minimal_post("to-delete", "published"),
    )
    assert r.status_code == 201
    pid = r.json()["id"]

    r = admin_blog_client.delete(f"/api/admin/blog/posts/{pid}", headers=h)
    assert r.status_code == 204

    r = admin_blog_client.get(f"/api/admin/blog/posts/{pid}", headers=h)
    assert r.status_code == 404

    r = admin_blog_client.get("/api/blog/posts/to-delete")
    assert r.status_code == 404
