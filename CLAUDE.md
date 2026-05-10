# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

PDF → Excel SaaS converter. Goal: beat iLovePDF on scanned/handwritten PDFs by
implementing a real geometric table-reconstruction pipeline rather than relying
on a single library.

**Read [`PROJECT_PLAN.md`](./PROJECT_PLAN.md) first.** It defines the
architecture, the typed contracts between pipeline stages, and the phase
ordering. Day-to-day progress lives in [`STATUS.md`](./STATUS.md) — check it
before starting work to know what phase is current and what's already in.

## Layout

```
frontend/         Next.js 16.2.4 + React 19.2.4 UI (upload, polling, download).
backend/app/      FastAPI app + Celery worker. See PROJECT_PLAN.md §2.
infrastructure/   docker-compose + nginx config.
docs/             One write-up per completed phase (see STATUS.md index).
```

## Hard rules

- **API never imports from `pipeline/`. Worker never imports from `api/`.**
  Both go through `services/` and `models/`. This separation is what lets the
  worker scale independently.
- **Pipeline stages communicate via the typed contracts in
  `backend/app/pipeline/types.py`** (`WordBox`, `RawCell`, `RawTable`,
  `CleanTable`). Changing one of these is a cross-cutting change — touch
  every stage.
- **After completing a phase, update `STATUS.md` and add `docs/phase-N-*.md`.**
  Don't silently mark phases done; the doc is the deliverable.
- **Frontend Next.js is non-standard.** `frontend/AGENTS.md` warns the
  installed Next.js (16.2.4) has breaking changes vs. training data. Before
  writing or editing frontend code, consult
  `frontend/node_modules/next/dist/docs/` for the actual current API.

## Commands

The stack runs via Docker Compose. Once Phase 1 lands:

```bash
# from repo root (recommended)
make up
# or: docker compose -f infrastructure/docker-compose.yml \
#   -f infrastructure/docker-compose.dev-host-ports.yml --profile compose-nginx up --build
```

Backend-only iteration (after `pip install -r backend/requirements.txt`):

```bash
cd backend
uvicorn app.main:app --reload          # API
celery -A app.queue.celery_app worker  # worker (separate terminal)
```

Tests / lint commands will be added with Phase 1 — they don't exist yet.

## Working style for this repo

- Keep changes inside the current phase's scope. If something needs to land
  earlier than its phase, update `PROJECT_PLAN.md` first to record the
  reordering, then implement.
- The differentiator vs. competitors is **Phase 4** (table reconstruction
  from OCR boxes). Don't take shortcuts there — algorithm choices belong
  in `docs/table-reconstruction.md` so they're reviewable.
