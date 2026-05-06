"""End-to-end Phase-1 lifecycle test using SQLite + in-process Celery (eager).

Proves the upload → queue → worker → failed-with-NotImplemented loop without
needing Postgres or Redis. Phase 2 will flip the expected end-state to
COMPLETED once the orchestrator is real.
"""

from __future__ import annotations

import io
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    storage_root = tmp_path_factory.mktemp("storage")
    db_path = tmp_path_factory.mktemp("db") / "test.db"

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["STORAGE_BACKEND"] = "local"
    os.environ["STORAGE_LOCAL_ROOT"] = str(storage_root)
    os.environ["REDIS_URL"] = "memory://"

    # Reset cached singletons so the new env takes effect.
    from app import config, storage
    from app.models import database
    config.get_settings.cache_clear()
    storage.get_storage.cache_clear()
    database._engine = None
    database._SessionLocal = None

    # Create schema directly from the model metadata.
    from app.models.database import Base, get_engine
    from app.models import job as _job  # noqa: F401 — register Job with metadata
    Base.metadata.create_all(get_engine())

    # Run Celery tasks inline. Override broker + result backend with the
    # in-memory transports so no Redis is needed.
    from app.queue.celery_app import celery_app
    celery_app.conf.broker_url = "memory://"
    celery_app.conf.result_backend = "cache+memory://"
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = False

    # Disable rate limiting so the four sequential POST requests below don't
    # trip the per-IP quota.
    from app.api import limiter as lim
    lim.enabled = False

    from app.main import app
    return TestClient(app)


def _make_minimal_pdf() -> bytes:
    """Small digital-text PDF with a realistic 3-column table."""
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=400, height=300)
    page.insert_text((40,  40), "Product")
    page.insert_text((180, 40), "Quantity")
    page.insert_text((300, 40), "Price")
    rows = [("Apple", "3", "1.20"), ("Banana", "5", "0.40"),
            ("Cherry", "12", "0.10"), ("Durian", "1", "9.50")]
    for i, (name, qty, price) in enumerate(rows):
        y = 70 + 30 * i
        page.insert_text((40, y), name)
        page.insert_text((180, y), qty)
        page.insert_text((300, y), price)
    out = doc.tobytes()
    doc.close()
    return out


def test_upload_runs_lifecycle_to_completed(client):
    pdf_bytes = _make_minimal_pdf()
    r = client.post(
        "/api/jobs",
        files={"file": ("sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"mode": "fast"},
    )
    assert r.status_code == 202, r.text
    job_id = r.json()["id"]

    # With eager Celery the task body has already run end-to-end.
    final = client.get(f"/api/jobs/{job_id}").json()
    assert final["status"] == "completed", final
    assert final["pdf_type"] == "digital"
    assert final["page_count"] == 1
    assert final["metrics"]["table_count"] >= 1
    assert final["extraction_scope"] == "tables_only"

    # Download endpoint streams the .xlsx.
    dl = client.get(f"/api/jobs/{job_id}/download")
    assert dl.status_code == 200
    assert dl.headers["content-type"].startswith("application/vnd.openxml")
    # XLSX files are ZIP archives — magic = "PK".
    assert dl.content[:2] == b"PK"


def test_rejects_non_pdf(client):
    r = client.post(
        "/api/jobs",
        files={"file": ("x.txt", io.BytesIO(b"hello"), "text/plain")},
        data={"mode": "fast"},
    )
    assert r.status_code == 415


def test_rejects_invalid_mode(client):
    pdf_bytes = b"%PDF-1.4\n"
    r = client.post(
        "/api/jobs",
        files={"file": ("x.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"mode": "lightning"},
    )
    assert r.status_code == 400


def test_upload_full_document_scope_completes(client):
    pdf_bytes = _make_minimal_pdf()
    r = client.post(
        "/api/jobs",
        files={"file": ("sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"mode": "fast", "extraction_scope": "full_document"},
    )
    assert r.status_code == 202, r.text
    job_id = r.json()["id"]
    final = client.get(f"/api/jobs/{job_id}").json()
    assert final["status"] == "completed", final
    assert final["extraction_scope"] == "full_document"
    assert final["full_document_pages"] == "single_sheet"
    assert final["metrics"]["table_count"] >= 0
    assert final["metrics"]["extraction_scope"] == "full_document"
    assert "layout_row_count" in final["metrics"]
    assert final["metrics"]["layout_row_count"] >= 1

    dl = client.get(f"/api/jobs/{job_id}/download")
    assert dl.status_code == 200
    assert dl.content[:2] == b"PK"


def test_get_unknown_job_returns_404(client):
    r = client.get("/api/jobs/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
