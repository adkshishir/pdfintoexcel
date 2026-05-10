"""Oracle Object Storage backend.

OCI exposes an S3-compatible API; we use boto3 against a custom endpoint.
Endpoint format: `https://<namespace>.compat.objectstorage.<region>.oraclecloud.com`

The contract matches `LocalObjectStore` so callers (services + worker) don't
care which backend is configured — `get_storage()` picks based on settings.
"""

from __future__ import annotations

import logging
import tempfile
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Iterator

from app.storage.base import ObjectStore

log = logging.getLogger(__name__)


class OracleObjectStore(ObjectStore):
    def __init__(
        self,
        *,
        endpoint: str,
        region: str,
        access_key: str,
        secret_key: str,
        bucket: str,
    ) -> None:
        self.endpoint = endpoint
        self.region = region
        self.bucket = bucket
        self._access_key = access_key
        self._secret_key = secret_key
        self._client = None  # lazy

    def _get_client(self):
        """Lazy boto3 client. Avoids forcing the import at module load time
        — `get_storage()` is called at API/worker boot regardless of backend."""
        if self._client is None:
            import boto3
            from botocore.config import Config
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint,
                region_name=self.region,
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
                # OCI requires path-style addressing + SigV4.
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"},
                    retries={"max_attempts": 3, "mode": "standard"},
                ),
            )
        return self._client

    def put(self, key: str, fileobj: BinaryIO, content_type: str | None = None) -> str:
        extra = {"ContentType": content_type} if content_type else {}
        self._get_client().upload_fileobj(fileobj, self.bucket, key, ExtraArgs=extra)
        log.info("oracle put: bucket=%s key=%s", self.bucket, key)
        return key

    def get(self, key: str) -> bytes:
        buf = BytesIO()
        self._get_client().download_fileobj(self.bucket, key, buf)
        return buf.getvalue()

    def delete(self, key: str) -> None:
        client = self._get_client()
        try:
            client.delete_object(Bucket=self.bucket, Key=key)
        except client.exceptions.NoSuchKey:  # type: ignore[attr-defined]
            log.debug("oracle delete: key %s already absent", key)

    @contextmanager
    def open_local(self, key: str) -> Iterator[Path]:
        """Download to a temp file, yield the path, clean up on exit."""
        suffix = Path(key).suffix or ".bin"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            self._get_client().download_file(self.bucket, key, str(tmp_path))
            yield tmp_path
        finally:
            tmp_path.unlink(missing_ok=True)
