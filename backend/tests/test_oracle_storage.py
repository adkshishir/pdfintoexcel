"""Phase 8 — Oracle Object Storage backend tests.

We don't depend on `moto` or a live OCI tenant: the boto3 client is built
lazily, so we can monkeypatch it with a fake before the first call. That
exercises the full call sequence (put → get → delete → open_local) without
touching the network.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest

from app.storage.oracle import OracleObjectStore


class _FakeS3Client:
    """Tiny in-memory S3 stand-in that records calls."""
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}
        self.put_calls: list[dict] = []
        self.delete_calls: list[tuple[str, str]] = []

        class _NoSuchKey(Exception):
            pass
        self.exceptions = type("Exceptions", (), {"NoSuchKey": _NoSuchKey})()

    def upload_fileobj(self, fileobj, bucket, key, ExtraArgs=None):  # noqa: N803
        self.objects[(bucket, key)] = fileobj.read()
        self.put_calls.append({"bucket": bucket, "key": key, "extra": ExtraArgs})

    def download_fileobj(self, bucket, key, fileobj):
        if (bucket, key) not in self.objects:
            raise self.exceptions.NoSuchKey
        fileobj.write(self.objects[(bucket, key)])

    def download_file(self, bucket, key, dest_path):
        Path(dest_path).write_bytes(self.objects[(bucket, key)])

    def delete_object(self, *, Bucket, Key):  # noqa: N803
        self.objects.pop((Bucket, Key), None)
        self.delete_calls.append((Bucket, Key))


@pytest.fixture
def store_with_fake() -> tuple[OracleObjectStore, _FakeS3Client]:
    s = OracleObjectStore(
        endpoint="https://example.compat.objectstorage.region.example.com",
        region="us-phx-1",
        access_key="k", secret_key="s",
        bucket="test-bucket",
    )
    fake = _FakeS3Client()
    s._client = fake
    return s, fake


def test_put_get_round_trip(store_with_fake):
    store, fake = store_with_fake
    payload = b"%PDF-1.4\nhello"
    store.put("uploads/abc/input.pdf", BytesIO(payload), content_type="application/pdf")
    assert fake.put_calls == [{
        "bucket": "test-bucket",
        "key": "uploads/abc/input.pdf",
        "extra": {"ContentType": "application/pdf"},
    }]
    assert store.get("uploads/abc/input.pdf") == payload


def test_delete_idempotent(store_with_fake):
    store, fake = store_with_fake
    store.put("k", BytesIO(b"x"))
    store.delete("k")
    store.delete("k")  # second delete should not raise
    # Both calls are recorded; backend should swallow the NoSuchKey.
    assert len(fake.delete_calls) == 2


def test_open_local_yields_temp_file_and_cleans_up(store_with_fake, tmp_path):
    store, _ = store_with_fake
    store.put("outputs/job1/output.xlsx", BytesIO(b"PK\x03\x04 fake xlsx"))

    seen_path: Path | None = None
    with store.open_local("outputs/job1/output.xlsx") as p:
        assert p.exists()
        assert p.suffix == ".xlsx"
        assert p.read_bytes() == b"PK\x03\x04 fake xlsx"
        seen_path = p
    # File deleted on context exit.
    assert seen_path is not None
    assert not seen_path.exists()


def test_lazy_client_construction():
    """No boto3 import or network until first operation."""
    s = OracleObjectStore(
        endpoint="https://example.com", region="r",
        access_key="k", secret_key="s", bucket="b",
    )
    assert s._client is None
