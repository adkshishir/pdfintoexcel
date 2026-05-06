"""Tests for extraction_scope (tables_only vs full_document)."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    storage_root = tmp_path_factory.mktemp("storage")
    db_path = tmp_path_factory.mktemp("db") / "extract.db"

    import os
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["STORAGE_BACKEND"] = "local"
    os.environ["STORAGE_LOCAL_ROOT"] = str(storage_root)
    os.environ["REDIS_URL"] = "memory://"

    from app import config, storage
    from app.models import database
    config.get_settings.cache_clear()
    storage.get_storage.cache_clear()
    database._engine = None
    database._SessionLocal = None

    from app.models.database import Base, get_engine
    from app.models import job as _job  # noqa: F401
    Base.metadata.create_all(get_engine())

    from app.queue.celery_app import celery_app
    celery_app.conf.broker_url = "memory://"
    celery_app.conf.result_backend = "cache+memory://"
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = False

    from app.api import limiter as lim
    lim.enabled = False

    from app.main import app
    return TestClient(app)


def test_api_accepts_extraction_scope_full_document(client) -> None:
    pdf = b"%PDF-1.4\n" + b"x" * 200
    r = client.post(
        "/api/jobs",
        files={"file": ("x.pdf", io.BytesIO(pdf), "application/pdf")},
        data={"mode": "fast", "extraction_scope": "full_document"},
    )
    assert r.status_code == 202, r.text
    job = r.json()
    assert job["extraction_scope"] == "full_document"
    assert job["full_document_pages"] == "single_sheet"


def test_api_accepts_full_document_per_page(client) -> None:
    pdf = b"%PDF-1.4\n" + b"x" * 200
    r = client.post(
        "/api/jobs",
        files={"file": ("x.pdf", io.BytesIO(pdf), "application/pdf")},
        data={
            "mode": "fast",
            "extraction_scope": "full_document",
            "full_document_pages": "per_page",
        },
    )
    assert r.status_code == 202, r.text
    assert r.json()["full_document_pages"] == "per_page"


def test_api_default_extraction_scope_tables_only(client) -> None:
    pdf = b"%PDF-1.4\n" + b"x" * 200
    r = client.post(
        "/api/jobs",
        files={"file": ("x.pdf", io.BytesIO(pdf), "application/pdf")},
        data={"mode": "fast"},
    )
    assert r.status_code == 202
    assert r.json()["extraction_scope"] == "tables_only"
    assert r.json()["full_document_pages"] == "single_sheet"


def test_api_rejects_invalid_full_document_pages(client) -> None:
    pdf = b"%PDF-1.4\n" + b"x" * 200
    r = client.post(
        "/api/jobs",
        files={"file": ("x.pdf", io.BytesIO(pdf), "application/pdf")},
        data={"mode": "fast", "full_document_pages": "grid"},
    )
    assert r.status_code == 400


def test_api_rejects_invalid_extraction_scope(client) -> None:
    pdf = b"%PDF-1.4\n" + b"x" * 200
    r = client.post(
        "/api/jobs",
        files={"file": ("x.pdf", io.BytesIO(pdf), "application/pdf")},
        data={"mode": "fast", "extraction_scope": "everything"},
    )
    assert r.status_code == 400
