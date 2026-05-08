"""Analytics summary API and download counter."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models.job import Job, JobStatus


@pytest.fixture()
def analytics_client(tmp_path):
    db_path = tmp_path / "analytics.db"
    storage_root = tmp_path / "storage"
    storage_root.mkdir()

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["STORAGE_BACKEND"] = "local"
    os.environ["STORAGE_LOCAL_ROOT"] = str(storage_root)
    os.environ["ANALYTICS_API_KEY"] = "test-analytics-secret"

    from app import config, storage
    from app.models import database

    config.get_settings.cache_clear()
    storage.get_storage.cache_clear()
    database._engine = None
    database._SessionLocal = None

    from app.models.database import Base, get_engine
    from app.models import job as _job  # noqa: F401

    Base.metadata.create_all(get_engine())

    from app.api import limiter as lim
    lim.enabled = False

    from app.main import app as fastapi_app
    return TestClient(fastapi_app)


def test_analytics_summary_counts_and_key(analytics_client: TestClient) -> None:
    from sqlalchemy.orm import Session

    from app.models.database import get_engine
    from app.services.job_service import input_key

    now = datetime.now(timezone.utc)
    engine = get_engine()
    with Session(engine) as db:
        for status, n in [
            (JobStatus.COMPLETED, 2),
            (JobStatus.FAILED, 1),
            (JobStatus.QUEUED, 1),
        ]:
            for _ in range(n):
                jid = uuid.uuid4()
                db.add(
                    Job(
                        id=jid,
                        status=status,
                        mode="fast",
                        output_layout="merged",
                        extraction_scope="tables_only",
                        full_document_pages="single_sheet",
                        input_url=input_key(jid),
                        filename="f.pdf",
                        size_bytes=100,
                        download_count=3 if status == JobStatus.COMPLETED else 0,
                        created_at=now,
                        expires_at=now + timedelta(hours=1),
                        completed_at=now if status != JobStatus.QUEUED else None,
                    ),
                )
        db.commit()

    r = analytics_client.get("/api/analytics/summary")
    assert r.status_code == 401

    r = analytics_client.get(
        "/api/analytics/summary",
        headers={"X-Analytics-Key": "wrong"},
    )
    assert r.status_code == 401

    r = analytics_client.get(
        "/api/analytics/summary",
        headers={"X-Analytics-Key": "test-analytics-secret"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total_jobs"] == 4
    assert body["by_status"]["completed"] == 2
    assert body["by_status"]["failed"] == 1
    assert body["by_status"]["queued"] == 1
    assert body["downloads_total"] == 6


def test_record_download_increments(tmp_path) -> None:
    db_path = tmp_path / "dl.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["STORAGE_BACKEND"] = "local"
    os.environ["STORAGE_LOCAL_ROOT"] = str(tmp_path / "s")
    (tmp_path / "s").mkdir()

    from app import config, storage
    from app.models import database

    config.get_settings.cache_clear()
    storage.get_storage.cache_clear()
    database._engine = None
    database._SessionLocal = None

    from sqlalchemy.orm import Session

    from app.models.database import Base, get_engine
    from app.models import job as _job  # noqa: F401

    Base.metadata.create_all(get_engine())
    from app.services import job_service

    jid = uuid.uuid4()
    now = datetime.now(timezone.utc)
    engine = get_engine()
    with Session(engine) as db:
        db.add(
            Job(
                id=jid,
                status=JobStatus.COMPLETED,
                mode="fast",
                output_layout="merged",
                extraction_scope="tables_only",
                full_document_pages="single_sheet",
                input_url=job_service.input_key(jid),
                output_url="outputs/x.xlsx",
                filename="f.pdf",
                size_bytes=100,
                download_count=0,
                created_at=now,
                expires_at=now + timedelta(hours=1),
                completed_at=now,
            ),
        )
        db.commit()

    with Session(engine) as db:
        job_service.record_download(db, jid)
        job_service.record_download(db, jid)

    with Session(engine) as db:
        row = db.execute(select(Job).where(Job.id == jid)).scalar_one()
        assert row.download_count == 2
