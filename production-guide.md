# Production guide (same-day deploy checklist)

Concise steps to ship with Docker Compose and nginx. Repo paths are relative to the project root.

---

## 1. Freeze the codebase

1. **Commit** all intentional changes (including migrations under `backend/alembic/versions/`).
2. **Push** to origin (prefer `main` if hosting or CI expect it; `master` is fine too—CI runs on both).
3. On the **server** (or locally before deploy), confirm tests pass:

   ```bash
   cd backend && pip install -r requirements-ci.txt && pytest -q tests/
   ```

   Expect **82 passed** (or run `make test-backend` against the Docker dev stack).

---

## 2. Server prerequisites

- **Docker** and **Docker Compose v2**
- Ports **80** (and **443** if you terminate TLS on the box) open on the firewall
- **Git** to clone the repo

---

## 3. Configure production env

On the server, after `git clone`:

1. **Copy** the template:

   ```bash
   cp infrastructure/.env.prod.example infrastructure/.env.prod
   ```

2. **Edit** `infrastructure/.env.prod` and set at least:

   - `POSTGRES_PASSWORD` and matching `DATABASE_URL`
   - `CORS_ORIGINS` → your real `https://` origins
   - `JWT_SECRET` → long random string (not the sample)
   - `ADMIN_BOOTSTRAP_EMAIL` / `ADMIN_BOOTSTRAP_PASSWORD` → strong bootstrap (first admin seed)
   - `ANALYTICS_API_KEY` → long random string (same discipline as other internal keys)

3. **Storage for “today”:**

   - If Oracle is **not** ready: set `STORAGE_BACKEND=local` and keep the **`storage-data`** volume (Compose already defines it). Switch to **`oracle`** when credentials exist.

4. **Optional** but recommended for the dashboard: create **`infrastructure/.env`** (same folder as the compose files) with:

   ```bash
   ANALYTICS_API_KEY=<same as in .env.prod>
   ```

   so Compose can pass it to the **frontend** service (see comments in `infrastructure/.env.prod.example`).

---

## 4. Point nginx at your domain (once)

Edit `infrastructure/nginx/nginx.conf`: **`server_name`** should match your real hostname(s) (the example lists `pdfintoexcel.com`). A mismatch mainly matters if you host multiple sites on one nginx.

---

## 5. TLS (HTTPS)

The Compose setup listens on **80** by default; **443** is commented in nginx. For a public launch you normally:

- **Option A:** Uncomment the **443** block in nginx and mount **Let’s Encrypt** certs, or  
- **Option B:** Put **Cloudflare** or a **load balancer** in front and terminate TLS there.

Until TLS is in place, users hit **HTTP only**—fine for a private smoke test; **not** ideal once real accounts and passwords matter.

---

## 6. Build and start

From the **repo root**:

```bash
make prod-up
```

That builds API/worker plus the production **frontend** image and starts **postgres**, **redis**, **backend**, **worker**, **beat**, **frontend**, and **nginx**.

---

## 7. Run database migrations

```bash
make prod-migrate
```

Run this **after every deploy** that adds or changes migrations.

---

## 8. Smoke checks

- **Site:** `http://YOUR_SERVER/` (or HTTPS once configured).
- **API health:** `curl -sf http://YOUR_SERVER/api/healthz` (adjust host/scheme if needed).
- **Converter:** upload a PDF in the UI, wait for completion, download the XLSX.
- **Admin:** sign in via your hidden admin URL (e.g. `/auth/control-panel-access-9xq7k`), then open `/dashboard`.

---

## 9. Operational hygiene (same day if you can)

- **Backups:** Postgres volume or regular dumps.
- **Secrets:** never commit `.env.prod` or `infrastructure/.env`.
- **Monitoring:** `make prod-logs`, or ship container logs to your host journald/agent.

---

## Realistic “done today?” checklist

| Must-have for go-live               | Owner / note                                      |
| ----------------------------------- | ------------------------------------------------- |
| Code + migrations committed        | You                                               |
| `.env.prod` + secrets               | You                                               |
| `make prod-up` + `make prod-migrate` | You                                               |
| HTTPS                               | You (or load balancer)                             |
| Object storage                      | Optional day-one: `STORAGE_BACKEND=local` + backups |

---
