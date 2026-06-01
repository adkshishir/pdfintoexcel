"""Redis pub/sub for job status updates (WebSocket push)."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from app.config import get_settings

log = logging.getLogger(__name__)


def channel_for(job_id: uuid.UUID | str) -> str:
    return f"job:{job_id}"


def publish_job_update(job_id: uuid.UUID | str, payload: dict[str, Any]) -> None:
    """Publish a job snapshot to subscribers. Failures are logged, not raised."""
    try:
        import redis

        r = redis.from_url(get_settings().redis_url)
        try:
            r.publish(channel_for(job_id), json.dumps(payload))
        finally:
            r.close()
    except Exception as exc:
        log.warning("publish_job_update failed for %s: %s", job_id, exc)
