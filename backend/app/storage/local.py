"""Local filesystem object store. Dev + tests only.

Maps `key="uploads/abc/input.pdf"` to `<root>/uploads/abc/input.pdf`. The
`open_local` context manager just yields the real path — no temp copies
needed when storage is already on disk.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator

from app.storage.base import ObjectStore


class LocalObjectStore(ObjectStore):
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Reject path traversal — keys are caller-controlled in some flows.
        if ".." in Path(key).parts:
            raise ValueError(f"invalid key: {key}")
        return self.root / key

    def put(self, key: str, fileobj: BinaryIO, content_type: str | None = None) -> str:
        dest = self._path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as out:
            while chunk := fileobj.read(1 << 20):
                out.write(chunk)
        return key

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    @contextmanager
    def open_local(self, key: str) -> Iterator[Path]:
        yield self._path(key)
