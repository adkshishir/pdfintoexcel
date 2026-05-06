"""Smoke tests that don't need Postgres or Redis.

Run: pytest backend/tests
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    client = TestClient(app)
    r = client.get("/api/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_openapi_lists_jobs_routes() -> None:
    client = TestClient(app)
    spec = client.get("/api/openapi.json").json()
    paths = set(spec["paths"].keys())
    assert "/api/jobs" in paths
    assert "/api/jobs/{job_id}" in paths
    assert "/api/jobs/{job_id}/download" in paths
