# Phase 9 — Security & hardening

**Shipped:** 2026-05-01
**Acceptance criteria** (PROJECT_PLAN.md §8):
> File-type sniffing, size limits, rate limiting, job timeouts, expiry sweeper.

## What landed

| Concern                  | File                                          | Notes                                                                |
| ------------------------ | --------------------------------------------- | -------------------------------------------------------------------- |
| libmagic content sniff   | `backend/app/utils/security.py`               | Tries python-magic first, falls back to magic-byte search if libmagic isn't installed. |
| Rate limiter             | `backend/app/api/limiter.py`                  | In-process per-IP token-window dependency (rolled our own — see "Why not slowapi" below). |
| Per-route limits         | `backend/app/api/jobs.py`                     | POST=10/min, GET status=120/min (polling), download=30/min.          |
| Soft-timeout handling    | `backend/app/queue/tasks.py`                  | `SoftTimeLimitExceeded` caught → job marked failed with `TIMEOUT:` prefix. |
| Stuck-processing watchdog| `backend/app/services/job_service.py`         | `mark_stuck_processing_as_failed()` for hard-killed worker cases.    |
| Expiry sweeper           | `backend/app/services/job_service.py`         | `cleanup_expired_jobs()` deletes files + rows past `expires_at`.    |
| Beat task                | `backend/app/queue/tasks.py`                  | `converter.cleanup_expired_jobs` runs both passes per call.          |
| Beat schedule            | `backend/app/queue/celery_app.py`             | Every 5 minutes via `beat_schedule`.                                 |
| Beat container           | `infrastructure/docker-compose.yml`           | Dedicated `beat` service (single instance — schedule-multiplication risk). |
| Tests                    | `backend/tests/test_security_and_sweeper.py`  | 6 tests: libmagic+fallback, 429 enforcement, sweeper, watchdog. **43 tests pass total.** |

## libmagic with magic-byte fallback

Phase 1 used `b"%PDF-" in head[:1024]` — easy to spoof and misses polyglot
files (e.g. a JPG with a PDF header glued on). Phase 9 prefers
`magic.from_buffer(head)` checking the actual MIME type. If libmagic isn't
present (test envs that haven't installed `libmagic1`), the magic-byte
fallback kicks in so dev workflows aren't broken.

The `Dockerfile` and `Dockerfile.worker` both already install `libmagic1`,
so production always uses the strong path.

## Why not slowapi

Tried slowapi 0.1.9 first; its `@limiter.limit(...)` decorator wraps the
handler in a way that confuses FastAPI's response-model inference. On
`POST /api/jobs` (which uses `UploadFile`), FastAPI errored:

> `Invalid args for response field! Hint: check that ForwardRef('UploadFile') is a valid Pydantic field type.`

Rather than patch around it, wrote a 40-line `rate_limit(per_minute=N)`
factory returning a FastAPI dependency. Plugged in via `dependencies=[...]`
on the route decorator — no signature wrapping, no introspection conflict.

Tradeoffs:
- **In-memory state.** Single-replica backend per the deploy guide; for
  multi-replica we'd swap the deque for Redis-backed state (~10 line change,
  same dependency interface).
- **No header-based quota response.** Adds `Retry-After` on rejection but
  not `X-RateLimit-*` informational headers. Easy to add if a UI wants them.
- **Tests can disable** via `from app.api import limiter; limiter.enabled = False`.

## Job timeout flow

Celery's existing config (Phase 1) sets two limits:
- `task_soft_time_limit = JOB_TIMEOUT_SECONDS` (default 600s)
- `task_time_limit = JOB_TIMEOUT_SECONDS + 60s` (hard kill)

When the soft limit fires, Celery raises `SoftTimeLimitExceeded` inside the
task. `process_job` now catches that *separately* from generic `Exception`
and marks the job failed with `error="TIMEOUT: pipeline exceeded job_timeout_seconds"`.
This gives the worker ~60s to clean up before the hard kill, instead of
leaving the job stuck in `PROCESSING` forever.

If the worker is hard-killed before it can mark the job (rare but possible
on OOM kills, container restarts, etc.), the periodic
`mark_stuck_processing_as_failed()` watchdog catches jobs whose
`started_at < now - 2 × JOB_TIMEOUT_SECONDS` and marks them failed. That
gives a generous safety margin without false positives on legitimately
long-running jobs.

## Expiry sweeper

`cleanup_expired_jobs()`:
1. Finds jobs with `expires_at < now()` (any status — completed, failed, even processing if it stuck around).
2. Deletes `input_url` + `output_url` from object storage (idempotent — missing keys are tolerated).
3. Deletes the DB row.
4. Returns `{"rows": N, "objects": M}` for the beat task to log.

Default cadence: every 5 minutes. Default TTL: 24 hours (configurable via
`JOB_TTL_SECONDS`). The dedicated `beat` service in compose runs at scale
1; running multiple would multiply the schedule and run cleanup repeatedly.

## What Phase 9 deliberately leaves unfinished

- **Authentication.** Out of scope per `PROJECT_PLAN.md §10`. Anonymous
  job IDs are intentional — adding accounts is a separate phase with auth,
  rate-limiting-by-account, billing implications, etc.
- **PDF malicious-content scanning.** We extract text/structure, never
  render PDFs in-browser — the attack surface is small. ClamAV scanning
  could be added pre-pipeline if compliance requires it.
- **Distributed rate limiting.** In-memory works for single-replica deploys;
  multi-replica needs Redis-backed state.
- **Per-account quotas.** Same dependency, different `key_func`, when
  accounts ship.
- **Audit log.** Every action is currently in Postgres or container logs;
  no separate immutable audit trail.
