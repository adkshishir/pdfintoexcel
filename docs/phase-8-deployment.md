# Phase 8 — Infrastructure & deployment

**Shipped:** 2026-05-01
**Acceptance criteria** (PROJECT_PLAN.md §8):
> `docker compose up` brings the whole stack up locally; nginx routes; Oracle Object Storage credentials work.

## What landed

| Concern                        | File                                          | Notes                                                              |
| ------------------------------ | --------------------------------------------- | ------------------------------------------------------------------ |
| Real Oracle Object Storage     | `backend/app/storage/oracle.py`               | boto3 against S3-compatible OCI endpoint, lazy client.             |
| Oracle storage tests           | `backend/tests/test_oracle_storage.py`        | 4 tests, in-memory fake S3 (no moto/network).                      |
| Frontend production Dockerfile | `frontend/Dockerfile` + `.dockerignore`       | Multi-stage: deps → build → runner. Inlines `NEXT_PUBLIC_API_BASE_URL` at build. |
| Production compose overlay     | `infrastructure/docker-compose.prod.yml`      | No source mounts, restart policies, loopback **4017**/ **4018** for host nginx (optional `compose.host-ports.env`). |
| Production env template        | `infrastructure/.env.prod.example`            | Documents Oracle creds + locked-down CORS + secrets to fill in.    |
| Hardened nginx                 | `infrastructure/nginx/nginx.conf`             | gzip + security headers + smart timeouts + keepalive upstreams.    |
| Make targets                   | `Makefile`                                    | `up/down/logs/migrate/shell-*/test/prod-*`.                        |

37 tests pass (33 from earlier phases + 4 new Oracle storage tests).

## Oracle Object Storage backend

OCI exposes an S3-compatible API; we use boto3 against a custom endpoint.

```python
boto3.client(
    "s3",
    endpoint_url="https://<namespace>.compat.objectstorage.<region>.oraclecloud.com",
    region_name=region,
    aws_access_key_id=...,
    aws_secret_access_key=...,
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)
```

Two OCI quirks worth knowing:
1. **Path-style addressing** (`endpoint/bucket/key`) — virtual-hosted style isn't supported.
2. **SigV4 signing** (always, no SigV2 fallback).

The client is lazy-initialized in `_get_client()` so importing the module
doesn't pull in boto3 (keeps test runs of the local backend snappy).

### Tests without moto

`tests/test_oracle_storage.py` injects a tiny `_FakeS3Client` into
`OracleObjectStore._client`, exercising the full call sequence (put → get
→ delete → open_local) without needing `moto` or live OCI credentials.
The `_get_client()` lazy load is what makes this clean.

## Production compose overlay

Use the prod overlay on top of the base compose:

```bash
docker compose \
  -f infrastructure/docker-compose.yml \
  -f infrastructure/docker-compose.prod.yml \
  up -d --build
```

Or via Makefile: `make prod-up`.

Key differences from dev:

| Aspect          | Dev                                    | Prod                                    |
| --------------- | -------------------------------------- | --------------------------------------- |
| Frontend image  | `node:20-alpine` + `npm install` on boot | Built from `frontend/Dockerfile`     |
| Source mounts   | `frontend/` bind-mounted (HMR)         | None — code baked into image            |
| Port exposure   | backend:8000, frontend:3000, nginx:8080 (via `docker-compose.dev-host-ports.yml`) | **127.0.0.1:4017** (API) + **127.0.0.1:4018** (Next); host nginx on :80 |
| Restart policy  | implicit (none)                        | `restart: unless-stopped`               |
| Env source      | `backend/.env.example`                 | `infrastructure/.env.prod` (gitignored) |
| Storage backend | `local` → docker volume                | `oracle` → OCI Object Storage           |

## nginx hardening

Beyond the dev config:

- **Compression** (gzip, level 5, JSON/JS/CSS/HTML; .xlsx excluded — already a zip).
- **Security headers**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: geolocation=(), microphone=(), camera=()`.
- **`server_tokens off`** — don't leak nginx version.
- **Keepalive upstreams** (`keepalive 32`) — reuse backend/frontend connections.
- **Stream the .xlsx** (`proxy_buffering off` on /api/) so big workbooks don't fill the proxy buffer.
- **TLS termination** is documented but not enabled — uncomment the listen-443 + cert mounts when you wire Let's Encrypt or your provider's certs.

## Deploy walkthrough (Oracle Cloud VM)

1. **Provision VM** — Oracle Cloud A1 Flex, 2 OCPU + 12 GB RAM is enough. Open ports 80 (and 443 once TLS is on).
2. **Install Docker + Compose plugin** on the VM.
3. **Clone the repo + create credentials**:
   ```bash
   cp infrastructure/.env.prod.example infrastructure/.env.prod
   # fill in DB password, Oracle creds, your domain in CORS_ORIGINS
   ```
4. **Create the Object Storage bucket** in the OCI console; generate Customer Secret Keys under Identity → Users → Customer Secret Keys.
5. **Boot**: `make prod-up`. Backend container runs `alembic upgrade head` automatically before uvicorn.
6. **Verify**: `curl http://<vm-ip>/api/healthz` → `{"status":"ok"}`. Then upload a PDF through the browser at `http://<vm-ip>/`.
7. **TLS** (optional but strongly recommended): `certbot certonly --standalone` then uncomment the 443 listener + cert volumes in `docker-compose.prod.yml`.

## What couldn't be validated locally

- **`docker compose up`** — Docker isn't installed on the dev box where this work happens. Validation done at the unit level (Oracle backend tests pass; YAML syntax checked; production frontend build passes via `next build`).
- **End-to-end against real OCI Object Storage** — needs OCI tenant credentials. Code follows the documented OCI S3-compat contract; first prod run will be the live integration test.

## Architectural decisions

- **boto3, not the OCI Python SDK.** OCI's official SDK requires API-key signing and per-request OCID dance; the S3-compat path is simpler, faster to ship, and lets the same code work against MinIO / AWS S3 if we ever migrate.
- **Lazy boto3 import.** Same rationale as the lazy DB engine in Phase 1: importing the module shouldn't force the dependency to load. Lets local-backend tests skip boto3 entirely.
- **No multi-stage build for backend yet.** Backend image stays simple (single stage, `python:3.11-slim`) because the build is just `pip install`. If image size becomes an issue (PaddleOCR is the big one), a builder/runner split with `--target` is a one-paragraph change.
- **`!reset` to clear dev overrides** in the prod compose. Compose's documented mechanism for "remove this from the base"; cleaner than having two parallel compose files.

## What Phase 8 deliberately leaves unfinished

- **TLS certs.** Production-specific; user-supplied. Config is staged but commented.
- **Multi-replica backend** — Alembic on backend boot only works for a single backend container; multi-replica needs a one-shot migration job (Kubernetes pattern). Not in scope until horizontal scaling is needed.
- **Resource limits** (memory/CPU caps in compose). Depends on target hardware; document at deploy time.
- **Centralized logging** (Loki, ELK, etc.). Out of scope.
- **Backup / restore** of the Postgres volume. Use OCI Block Volume backups or `pg_dump` on a cron — not embedded.
