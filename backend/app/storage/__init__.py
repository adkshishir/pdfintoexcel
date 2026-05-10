"""Storage factory.

Callers do `from app.storage import get_storage` — they don't import concrete
backends. Picking the backend is settings-driven.
"""

from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.storage.base import ObjectStore
from app.storage.local import LocalObjectStore
from app.storage.oracle import OracleObjectStore


@lru_cache
def get_storage() -> ObjectStore:
    s = get_settings()
    if s.storage_backend == "local":
        return LocalObjectStore(s.storage_local_root)
    if s.storage_backend == "oracle":
        if not (s.oracle_endpoint and s.oracle_region and s.oracle_access_key and s.oracle_secret_key):
            raise RuntimeError(
                "STORAGE_BACKEND=oracle but ORACLE_* env vars are not set. "
                "See backend/.env.example."
            )
        return OracleObjectStore(
            endpoint=s.oracle_endpoint,
            region=s.oracle_region,
            access_key=s.oracle_access_key,
            secret_key=s.oracle_secret_key,
            bucket=s.storage_bucket,
        )
    raise ValueError(f"unknown STORAGE_BACKEND: {s.storage_backend}")


__all__ = ["ObjectStore", "get_storage"]
