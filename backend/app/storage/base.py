"""Object storage interface.

`local` backend writes to `Settings.storage_local_root` (dev/tests).
`oracle` backend uses Oracle Object Storage's S3-compatible API.

Always reference objects by *key* (e.g. `uploads/{job_id}/input.pdf`) — never
by absolute filesystem path. Backends translate.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator


class ObjectStore(ABC):
    @abstractmethod
    def put(self, key: str, fileobj: BinaryIO, content_type: str | None = None) -> str:
        """Store `fileobj` at `key`. Return the canonical URL/key."""

    @abstractmethod
    def get(self, key: str) -> bytes:
        ...

    @abstractmethod
    def iter_bytes(self, key: str, *, chunk_size: int = 1 << 20) -> Iterator[bytes]:
        """Yield object bytes in chunks for streaming downloads."""

    @abstractmethod
    def delete(self, key: str) -> None:
        ...

    @abstractmethod
    @contextmanager
    def open_local(self, key: str) -> Iterator[Path]:
        """Yield a local filesystem path for the object.

        For the local backend this is the real file. For the cloud backend
        this downloads to a temp file and cleans up on exit. Pipeline code
        always uses this so it doesn't care which backend is configured.
        """
