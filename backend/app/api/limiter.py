"""In-memory per-IP rate limiter, exposed as a FastAPI dependency.

Why not slowapi: its `@limit(...)` decorator wraps handler signatures in a
way that confuses FastAPI's response-model introspection (got bitten on
`POST /api/jobs` which uses `UploadFile`).

For multi-replica deploys this needs Redis-backed state — currently single
backend replica per the deployment guide, so in-memory is fine.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

# Singleton state — a deque of timestamps per IP.
_state: dict[str, deque[float]] = defaultdict(deque)
_lock = threading.Lock()

# Toggle for tests.
enabled = True


def reset() -> None:
    """Wipe the limiter state. Tests use this between cases."""
    with _lock:
        _state.clear()


def rate_limit(*, per_minute: int) -> callable:
    """Return a FastAPI dependency that enforces N requests per minute per IP."""
    window = 60.0
    def dep(request: Request) -> None:
        if not enabled:
            return
        client_ip = (request.client.host if request.client else "unknown")
        now = time.monotonic()
        with _lock:
            timestamps = _state[client_ip]
            # Drop timestamps outside the window.
            cutoff = now - window
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()
            if len(timestamps) >= per_minute:
                retry_after = max(1, int(timestamps[0] + window - now))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="rate limit exceeded",
                    headers={"Retry-After": str(retry_after)},
                )
            timestamps.append(now)
    return dep


# Per-route limit dependencies. Tunable in one place.
limit_create_job = rate_limit(per_minute=10)
limit_get_job    = rate_limit(per_minute=120)   # the frontend polls every 1.5s
limit_download   = rate_limit(per_minute=30)
