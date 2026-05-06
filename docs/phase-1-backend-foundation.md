# Phase 1 — Backend foundation

**Shipped:** 2026-05-01
**Acceptance criteria** (from PROJECT_PLAN.md §8):
> `POST /api/jobs` accepts a PDF, persists row, enqueues task. `GET /api/jobs/{id}` returns status. Celery worker boots and marks `processing → completed/failed` (no real work yet).

## What landed

| Concern         | File                                 | Notes                                                                       |
| --------------- | ------------------------------------ | --------------------------------------------------------------------------- |
| DB session      | `app/models/database.py`             | Sync SQLAlchemy 2.x; `get_db` for FastAPI, `session_scope` for Celery.      |
| Job model       | `app/models/job.py`                  | UUID PK, status enum, JSONB metrics, partial index for expiry sweeper.      |
| Migration       | `alembic/versions/0001_create_jobs.py` | Creates jobs table + both indices.                                        |
| Storage (local) | `app/storage/local.py`               | Dev backend; rejects path traversal in keys.                                |
| Storage (Oracle) | `app/storage/oracle.py`             | Stub — Phase 8.                                                             |
| Storage factory | `app/storage/__init__.py`            | `get_storage()` picks backend from settings.                                |
| Service layer   | `app/services/job_service.py`        | The shared API/worker contract. `create_job`, `get_job`, `mark_*`.          |
| Upload route    | `app/api/jobs.py` `POST /jobs`       | Magic-byte PDF check, streamed size guard, persists, sends Celery task by name. |
| Status route    | `app/api/jobs.py` `GET /jobs/{id}`   | 404 / 200 with full job row.                                                |
| Download route  | `app/api/jobs.py` `GET /jobs/{id}/download` | 409 unless `completed`. Streams the .xlsx from object storage.        |
| Worker task     | `app/queue/tasks.py` `process_job`   | Lifecycle wired; calls `run_pipeline` (raises `NotImplementedError`).       |
| Boot migrations | `scripts/entrypoint.sh`              | Backend container runs `alembic upgrade head` before uvicorn.               |
| Tests           | `tests/test_api_smoke.py`            | No-DB-needed smoke tests.                                                   |

## Architectural decisions

- **Sync DB throughout.** The hot path (upload + status poll) is small and Celery is sync anyway. Async would buy us nothing here and adds session-management cost.
- **`api/` does not import `queue/tasks.py` for sending.** It calls `celery_current_app.send_task("converter.process_job", args=[...])`. This preserves the hard rule from CLAUDE.md ("API never imports from `pipeline/`") while still warming the registry via a top-level `import app.queue.tasks` for ergonomic dev.
- **Celery `process_job` catches `NotImplementedError` separately.** Phase-1 jobs end in `failed` with `error="PIPELINE_NOT_IMPLEMENTED: …"`. This is the *intended* Phase-1 acceptance signal — it proves the queue, DB, storage, and lifecycle all wire end-to-end without needing pipeline code. Phase 2 removes the failure path by making `run_pipeline` succeed.
- **Migrations on backend boot.** Worker container does *not* run migrations — multiple workers would race. Single backend replica owns DDL.

## How to run (Docker)

```bash
cp backend/.env.example backend/.env       # tweak if needed
docker compose -f infrastructure/docker-compose.yml up --build

# in another terminal:
curl -F file=@MonzoBus.pdf -F mode=fast http://localhost:8000/api/jobs
# → {"id":"…","status":"queued",…}

curl http://localhost:8000/api/jobs/<id>
# → status flips to "processing" then "failed" with error PIPELINE_NOT_IMPLEMENTED
```

## What Phase 1 deliberately leaves unfinished

- **Real pipeline.** `run_pipeline` raises. Phase 2 implements the digital path; Phase 3 the OCR path.
- **Rate limiting.** Bare endpoints. Phase 9.
- **libmagic content sniffing.** Phase 1 uses a magic-byte string check. Phase 9 swaps to `python-magic`.
- **Expiry sweeper.** No Celery beat task yet to delete expired files. Phase 9.
- **Authentication.** Anonymous job IDs only — confirmed out of scope by PROJECT_PLAN.md §10.
