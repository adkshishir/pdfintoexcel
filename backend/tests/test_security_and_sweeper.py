"""Phase 9 — security + sweeper tests.

Covers:
  - libmagic vs magic-byte fallback in `looks_like_pdf`
  - rate limit kicks in after the configured per-minute quota
  - expiry sweeper deletes files + rows
  - stuck-in-processing watchdog
"""

from __future__ import annotations

import io
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient


# =====================================================================
# libmagic / magic-byte fallback
# =====================================================================
def test_magic_byte_check_accepts_pdf_with_junk_prefix():
    from app.utils import security
    # Force the byte-string fallback path for a deterministic test.
    security._magic = None
    security._magic_unavailable = True
    head = b"junk junk junk %PDF-1.4\nrest"
    assert security.looks_like_pdf(head) is True


def test_magic_byte_check_rejects_non_pdf():
    from app.utils import security
    security._magic = None
    security._magic_unavailable = True
    assert security.looks_like_pdf(b"hello world") is False


def test_libmagic_path_used_when_available(monkeypatch):
    from app.utils import security
    security._magic = None
    security._magic_unavailable = False

    class FakeMagic:
        def from_buffer(self, head):
            return "application/pdf"

    class FakeMagicModule:
        def Magic(self, mime: bool):  # noqa: N802
            return FakeMagic()

    monkeypatch.setitem(__import__("sys").modules, "magic", FakeMagicModule())
    assert security.looks_like_pdf(b"anything") is True


# =====================================================================
# rate limiting
# =====================================================================
def test_rate_limit_returns_429_after_quota(tmp_path):
    """POST /api/jobs is capped at 10/minute per IP. Hit it ≥10 times → 429."""
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path}/rl.db"
    os.environ["STORAGE_BACKEND"] = "local"
    os.environ["STORAGE_LOCAL_ROOT"] = str(tmp_path / "storage")

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
    lim.reset()
    lim.enabled = True

    from app.main import app
    client = TestClient(app)

    pdf_bytes = b"%PDF-1.4\n" + b"x" * 100
    statuses = []
    for _ in range(15):
        r = client.post(
            "/api/jobs",
            files={"file": ("x.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            data={"mode": "fast"},
        )
        statuses.append(r.status_code)
    # First 10 should be accepted (202 or 415/etc — anything not 429); the rest should be 429.
    assert 429 in statuses, f"expected at least one 429 in {statuses}"
    # Cleanup so other tests aren't affected.
    lim.reset()
    lim.enabled = False


# =====================================================================
# expiry sweeper
# =====================================================================
@pytest.fixture
def db_session(tmp_path):
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path}/sweeper.db"
    os.environ["STORAGE_BACKEND"] = "local"
    os.environ["STORAGE_LOCAL_ROOT"] = str(tmp_path / "storage")

    from app import config, storage
    from app.models import database
    config.get_settings.cache_clear()
    storage.get_storage.cache_clear()
    database._engine = None
    database._SessionLocal = None

    from app.models.database import Base, get_engine
    from app.models import job as _job  # noqa: F401
    Base.metadata.create_all(get_engine())

    s = database._session_factory()()
    yield s
    s.close()


def test_cleanup_expired_jobs_deletes_files_and_rows(db_session):
    from app.models.job import Job, JobStatus
    from app.services import job_service
    from app.storage import get_storage

    storage = get_storage()
    # One expired completed job + one fresh one.
    expired_id = uuid.uuid4()
    fresh_id = uuid.uuid4()
    storage.put(f"uploads/{expired_id}/input.pdf",  io.BytesIO(b"old"))
    storage.put(f"outputs/{expired_id}/output.xlsx", io.BytesIO(b"oldx"))
    storage.put(f"uploads/{fresh_id}/input.pdf",   io.BytesIO(b"new"))

    now = datetime.now(timezone.utc)
    db_session.add_all([
        Job(id=expired_id, status=JobStatus.COMPLETED, mode="fast",
            input_url=f"uploads/{expired_id}/input.pdf",
            output_url=f"outputs/{expired_id}/output.xlsx",
            filename="a.pdf", size_bytes=3,
            created_at=now - timedelta(days=2),
            expires_at=now - timedelta(hours=1)),
        Job(id=fresh_id, status=JobStatus.COMPLETED, mode="fast",
            input_url=f"uploads/{fresh_id}/input.pdf",
            filename="b.pdf", size_bytes=3,
            created_at=now,
            expires_at=now + timedelta(hours=1)),
    ])
    db_session.commit()

    counts = job_service.cleanup_expired_jobs(db_session)
    assert counts == {"rows": 1, "objects": 2}

    # Expired row gone; fresh row still there.
    assert job_service.get_job(db_session, expired_id) is None
    assert job_service.get_job(db_session, fresh_id) is not None
    # Fresh file still there.
    assert storage.get(f"uploads/{fresh_id}/input.pdf") == b"new"


def test_mark_stuck_processing_as_failed(db_session):
    from app.models.job import Job, JobStatus
    from app.services import job_service

    now = datetime.now(timezone.utc)
    stuck_id = uuid.uuid4()
    fresh_id = uuid.uuid4()
    db_session.add_all([
        Job(id=stuck_id, status=JobStatus.PROCESSING, mode="fast",
            input_url="uploads/x/input.pdf", filename="a.pdf", size_bytes=1,
            created_at=now - timedelta(hours=2),
            started_at=now - timedelta(hours=1),
            expires_at=now + timedelta(hours=22)),
        Job(id=fresh_id, status=JobStatus.PROCESSING, mode="fast",
            input_url="uploads/y/input.pdf", filename="b.pdf", size_bytes=1,
            created_at=now, started_at=now,
            expires_at=now + timedelta(hours=24)),
    ])
    db_session.commit()

    n = job_service.mark_stuck_processing_as_failed(db_session, max_processing_seconds=600)
    assert n == 1
    db_session.expire_all()
    stuck = job_service.get_job(db_session, stuck_id)
    fresh = job_service.get_job(db_session, fresh_id)
    assert stuck.status == JobStatus.FAILED
    assert "TIMEOUT" in stuck.error
    assert fresh.status == JobStatus.PROCESSING
