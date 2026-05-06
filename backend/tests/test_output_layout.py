"""Tests for the `output_layout` flag (merged vs split)."""

from __future__ import annotations

import io
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.pipeline.cleaner import clean_tables
from app.pipeline.types import RawCell, RawTable


def _table(page: int, cells: list[tuple[int, int, str]]) -> RawTable:
    raw_cells = [RawCell(row=r, col=c, text=t) for (r, c, t) in cells]
    n_rows = max(r for r, _, _ in cells) + 1
    n_cols = max(c for _, c, _ in cells) + 1
    return RawTable(page=page, bbox=(0, 0, 100, 100),
                    cells=raw_cells, n_rows=n_rows, n_cols=n_cols)


# Two same-header tables on consecutive pages.
_BANK_LIKE_PAIR = [
    _table(0, [
        (0, 0, "Date"), (0, 1, "Amount"),
        (1, 0, "01/01/2025"), (1, 1, "10"),
        (2, 0, "02/01/2025"), (2, 1, "20"),
        (3, 0, "03/01/2025"), (3, 1, "30"),
    ]),
    _table(1, [
        (0, 0, "Date"), (0, 1, "Amount"),
        (1, 0, "04/01/2025"), (1, 1, "40"),
        (2, 0, "05/01/2025"), (2, 1, "50"),
        (3, 0, "06/01/2025"), (3, 1, "60"),
    ]),
]


def test_merged_default_collapses_same_header_tables() -> None:
    out = clean_tables(_BANK_LIKE_PAIR)  # default = "merged"
    assert len(out) == 1
    assert len(out[0].rows) == 6
    assert "merged" in out[0].sheet_name


def test_split_keeps_tables_separate() -> None:
    out = clean_tables(_BANK_LIKE_PAIR, output_layout="split")
    assert len(out) == 2
    assert all(len(t.rows) == 3 for t in out)
    # Sheet names shouldn't have "(merged)".
    assert all("merged" not in t.sheet_name for t in out)


def test_split_with_continuation_folds_within_each_sheet() -> None:
    """Continuation merging is per-sheet — accurate + split should still
    fold wraps within a single page's table."""
    table = _table(0, [
        (0, 0, "Date"), (0, 1, "Desc"),
        (1, 0, "01/01/2025"), (1, 1, "first"),
        (2, 1, "wrap"),                       # continuation of row 1
        (3, 0, "02/01/2025"), (3, 1, "second"),
        (4, 0, "03/01/2025"), (4, 1, "third"),
    ])
    table.row_y_centers = [10.0, 20.0, 25.0, 35.0, 45.0]
    out = clean_tables([table], merge_continuations=True, output_layout="split")
    assert len(out) == 1
    # Row 1 absorbs row 2's "wrap".
    assert out[0].rows[0] == ["01/01/2025", "first wrap"]
    assert len(out[0].rows) == 3


# =====================================================================
# API + E2E
# =====================================================================
@pytest.fixture(scope="module")
def client(tmp_path_factory):
    storage_root = tmp_path_factory.mktemp("storage")
    db_path = tmp_path_factory.mktemp("db") / "split.db"
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

    from app.api import limiter as lim
    lim.enabled = False

    from app.main import app
    return TestClient(app)


def _make_two_page_pdf() -> bytes:
    """Two pages, identical Item/Quantity table on each."""
    import fitz
    doc = fitz.open()
    for page_idx in range(2):
        p = doc.new_page(width=400, height=300)
        p.insert_text((40, 40), "Item")
        p.insert_text((180, 40), "Quantity")
        offset = page_idx * 100
        for i, (name, qty) in enumerate([("Apple", "1"), ("Banana", "2"),
                                          ("Cherry", "3"), ("Durian", "4")]):
            p.insert_text((40,  70 + 30*i), f"{name}{offset}")
            p.insert_text((180, 70 + 30*i), qty)
    out = doc.tobytes()
    doc.close()
    return out


def test_api_accepts_output_layout_split(client) -> None:
    pdf_bytes = _make_two_page_pdf()
    r = client.post(
        "/api/jobs",
        files={"file": ("two.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"mode": "fast", "output_layout": "split"},
    )
    assert r.status_code == 202, r.text
    job = r.json()
    assert job["output_layout"] == "split"
    final = client.get(f"/api/jobs/{job['id']}").json()
    assert final["status"] == "completed", final
    # Two same-header pages, but split mode keeps them as 2 sheets.
    assert final["metrics"]["table_count"] == 2


def test_api_default_output_layout_merged(client) -> None:
    pdf_bytes = _make_two_page_pdf()
    r = client.post(
        "/api/jobs",
        files={"file": ("two.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"mode": "fast"},        # no output_layout → defaults to merged
    )
    assert r.status_code == 202
    job = r.json()
    assert job["output_layout"] == "merged"
    final = client.get(f"/api/jobs/{job['id']}").json()
    assert final["metrics"]["table_count"] == 1


def test_api_rejects_invalid_output_layout(client) -> None:
    pdf_bytes = b"%PDF-1.4\n" + b"x" * 200
    r = client.post(
        "/api/jobs",
        files={"file": ("x.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"mode": "fast", "output_layout": "supercalifragilistic"},
    )
    assert r.status_code == 400
