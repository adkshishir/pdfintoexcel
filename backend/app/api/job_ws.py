"""WebSocket stream for job status (replaces client polling)."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import get_settings
from app.models.database import session_scope
from app.models.job import JobStatus
from app.queue.job_events import channel_for
from app.services import job_service

log = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])

_TERMINAL = frozenset({JobStatus.COMPLETED, JobStatus.FAILED})


def _is_terminal(payload: dict[str, Any]) -> bool:
    return payload.get("status") in _TERMINAL


async def _send_json(ws: WebSocket, payload: dict[str, Any]) -> None:
    await ws.send_text(json.dumps(payload))


async def _close_done(ws: WebSocket, *, code: int = 1000, reason: str = "done") -> None:
    try:
        await ws.close(code=code, reason=reason)
    except Exception:
        pass


@router.websocket("/{job_id}/ws")
async def job_status_ws(websocket: WebSocket, job_id: uuid.UUID) -> None:
    """Push job snapshots until terminal status, then close cleanly."""
    await websocket.accept()
    settings = get_settings()
    idle_seconds = settings.job_timeout_seconds + 60

    with session_scope() as db:
        job = job_service.get_job(db, job_id)
    if job is None:
        await _close_done(websocket, code=4404, reason="not_found")
        return

    initial = job.to_dict()
    redis_client = None
    pubsub = None

    try:
        await _send_json(websocket, initial)
        if _is_terminal(initial):
            await _close_done(websocket)
            return

        import redis.asyncio as aioredis

        redis_client = aioredis.from_url(settings.redis_url)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel_for(job_id))

        loop = asyncio.get_running_loop()
        deadline = loop.time() + idle_seconds
        last_payload = initial

        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                await _close_done(websocket, code=1001, reason="timeout")
                return

            msg = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=min(1.0, remaining),
            )
            if msg is None:
                continue
            if msg.get("type") != "message":
                continue

            raw = msg.get("data")
            if isinstance(raw, bytes):
                raw = raw.decode()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if payload == last_payload:
                continue
            last_payload = payload
            await _send_json(websocket, payload)

            if _is_terminal(payload):
                await _close_done(websocket)
                return

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        log.debug("job_status_ws %s: %s", job_id, exc)
        await _close_done(websocket, code=1011, reason="error")
    finally:
        if pubsub is not None:
            try:
                await pubsub.unsubscribe(channel_for(job_id))
                await pubsub.aclose()
            except Exception:
                pass
        if redis_client is not None:
            try:
                await redis_client.aclose()
            except Exception:
                pass
