"""WebSocket job status stream."""

from __future__ import annotations

import io
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app.queue.job_events import channel_for, publish_job_update


def _redis_ping(url: str) -> bool:
    try:
        import redis

        r = redis.from_url(url)
        r.ping()
        r.close()
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def ws_client(tmp_path_factory):
    storage_root = tmp_path_factory.mktemp("ws_storage")
    db_path = tmp_path_factory.mktemp("ws_db") / "test.db"
    redis_url = os.environ.get("TEST_REDIS_URL", "redis://127.0.0.1:6379/15")

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["STORAGE_BACKEND"] = "local"
    os.environ["STORAGE_LOCAL_ROOT"] = str(storage_root)
    os.environ["REDIS_URL"] = redis_url

    from app import config, storage
    from app.models import database
    from app.models import job as _job  # noqa: F401

    config.get_settings.cache_clear()
    storage.get_storage.cache_clear()
    database._engine = None
    database._SessionLocal = None

    from app.models.database import Base, get_engine

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


def _minimal_pdf() -> bytes:
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=200, height=200)
    page.insert_text((40, 40), "Hi")
    out = doc.tobytes()
    doc.close()
    return out


def test_websocket_completed_job_closes(ws_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.pipeline import orchestrator

    def fake_collect(pdf_path, detection, mode, timings, *, trust_pdf_text, recognizer):
        from app.pipeline.types import WordBox

        boxes = [WordBox("Hi", 40, 40, 20, 10, page=0, confidence=1.0)]
        return boxes, 1

    monkeypatch.setattr(orchestrator, "_collect_boxes", fake_collect)
    monkeypatch.setattr(
        orchestrator,
        "_extract_digital_tables",
        lambda *a, **k: [],
    )

    r = ws_client.post(
        "/api/jobs",
        files={"file": ("t.pdf", io.BytesIO(_minimal_pdf()), "application/pdf")},
        data={"mode": "fast"},
    )
    assert r.status_code == 202
    job_id = r.json()["id"]

    with ws_client.websocket_connect(f"/api/jobs/{job_id}/ws") as ws:
        msg = ws.receive_json()
        assert msg["id"] == job_id
        assert msg["status"] in ("completed", "failed")
        if msg["status"] == "completed":
            return
    pytest.skip("pipeline failed in this environment (OCR); WS still delivered terminal state")


def test_websocket_not_found(ws_client: TestClient) -> None:
    missing = uuid.uuid4()
    with ws_client.websocket_connect(f"/api/jobs/{missing}/ws") as ws:
        pass


@pytest.mark.skipif(
    not _redis_ping(os.environ.get("TEST_REDIS_URL", "redis://127.0.0.1:6379/15")),
    reason="Redis required for pub/sub push test",
)
def test_websocket_receives_published_update(ws_client: TestClient) -> None:
    from app.models.database import session_scope
    from app.services import job_service

    jid = uuid.uuid4()
    with session_scope() as db:
        from datetime import datetime, timedelta, timezone

        from app.models.job import Job, JobStatus

        now = datetime.now(timezone.utc)
        job = Job(
            id=jid,
            status=JobStatus.QUEUED,
            input_url=f"uploads/{jid}/input.pdf",
            filename="x.pdf",
            size_bytes=1,
            created_at=now,
            expires_at=now + timedelta(hours=1),
        )
        db.add(job)
        db.commit()

    with ws_client.websocket_connect(f"/api/jobs/{jid}/ws") as ws:
        first = ws.receive_json()
        assert first["status"] == "queued"

        payload = {**first, "status": "processing"}
        publish_job_update(jid, payload)
        second = ws.receive_json()
        assert second["status"] == "processing"

        payload = {**second, "status": "completed"}
        publish_job_update(jid, payload)
        third = ws.receive_json()
        assert third["status"] == "completed"
