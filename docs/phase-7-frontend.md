# Phase 7 — Frontend integration

**Shipped:** 2026-05-01
**Acceptance criteria** (PROJECT_PLAN.md §8):
> Upload, polling, download UI wired to real backend.

## What landed

| Concern              | File                                       | Notes                                                       |
| -------------------- | ------------------------------------------ | ----------------------------------------------------------- |
| Converter page       | `frontend/src/app/page.tsx`                | Single Client Component (`"use client"`). Upload, mode select, polling, download, metrics. |
| Layout metadata      | `frontend/src/app/layout.tsx`              | Title + description updated from create-next-app defaults.  |
| Native dev env       | `frontend/.env.local.example`              | `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api` for `npm run dev` outside Docker. |
| Compose env          | `infrastructure/docker-compose.yml`        | `frontend` service gets `NEXT_PUBLIC_API_BASE_URL=http://localhost:8080/api` (through nginx). |

Production build passes (`npx next build` → all routes prerendered, TypeScript clean, ESLint clean).

## Why one Client Component, not split

Per the bundled Next.js 16 docs (`node_modules/next/dist/docs/01-app/01-getting-started/05-server-and-client-components.md`):

> Use **Client Components** when you need state, event handlers, lifecycle logic.

The whole UI is interactive — file picker, mode toggle, polling, download trigger. There's nothing meaningfully server-renderable on this page (no DB queries, no auth, no static content beyond a heading). Splitting into a Server Component shell + Client Component body would just add ceremony without buying anything.

## UX

- **File picker** — accepts `.pdf` only. Shows filename + size after selection.
- **Mode toggle** — radio buttons styled as cards (`fast` 200 DPI vs `accurate` 300 DPI + merged rows). Disabled while a job is in flight.
- **Convert button** — disabled until a file is picked; shows "Uploading…" → "Working…" during the request.
- **Status pill** — color-coded by state (queued blue / processing amber pulsing / completed emerald / failed red).
- **Metrics panel** — pages, type, tables, time, confidence (each only rendered if the backend reported it).
- **Download button** — appears only when `status === "completed"`. Hits `/api/jobs/{id}/download`.
- **Error panel** — surfaces both upload-time and polling-time failures, separately from the `error` field on a failed job.

## Polling

```tsx
useEffect(() => {
  if (!job || job.status === "completed" || job.status === "failed") return;
  const h = setInterval(async () => {
    const r = await fetch(`${API_BASE}/jobs/${job.id}`);
    setJob(await r.json());
  }, 1500);
  return () => clearInterval(h);
}, [job]);
```

`[job]` dependency — re-runs on each new job state. When the new state is terminal, early return prevents a new interval; the previous one was cleaned up by the cleanup fn. No leaked timers.

1.5 s interval is a deliberate choice: short enough to feel responsive on small PDFs (~3 s pipeline), long enough to not hammer the API for big PDFs (~30 s pipeline). If we add WebSocket push later, this loop is replaced; until then, polling is fine.

## Env config

`NEXT_PUBLIC_*` vars are inlined at build time per the Next.js 16 upgrade
notes (no more `publicRuntimeConfig`). The frontend gets the API URL from
`NEXT_PUBLIC_API_BASE_URL`:

| Where                | Value                          | Why                                                     |
| -------------------- | ------------------------------ | ------------------------------------------------------- |
| Native dev           | `http://localhost:8000/api`    | Frontend at `:3000` hits backend at `:8000` directly.   |
| Docker compose       | `http://localhost:8080/api`    | Nginx at `:8080` routes `/api/*` → backend container.   |
| Production           | `/api`                         | Nginx serves frontend + backend on the same origin.     |

Backend's CORS already allows `http://localhost:3000` (set in `backend/app/config.py`).

## Architectural decisions

- **No state library.** `useState` + `useEffect` is enough for one page with one in-flight job. Adding Zustand/Redux would be ceremony.
- **No HTTP client library.** Native `fetch` works; adding axios/ky is unwarranted.
- **No form library.** One file picker + one radio group; React's controlled-input handles it.
- **Confidence as a percentage in the metrics panel** rather than highlighting low-confidence cells. Cell-level highlighting requires reading the workbook in-browser (or a separate preview API); both are Phase 7+ work.
- **Production build run as part of phase verification.** Catches type errors and import issues that lint would miss. Took 1.6s.

## What Phase 7 deliberately leaves unfinished

- **In-browser preview of the .xlsx.** Would need a workbook viewer (e.g. SheetJS) and a separate "preview" endpoint that returns JSON, not a binary blob. Adds ~500 KB to the bundle. Defer until users ask.
- **Confidence-based cell highlighting.** Backend already writes the hidden `_confidence` sheet; frontend would need to read it and overlay. Same dependency as preview.
- **Drag-and-drop upload.** Standard `<input type="file">` works; drag-drop is purely cosmetic.
- **Job history.** No persistent client state between sessions. Each upload is one-shot. Add when there's a "my conversions" use case.
- **Server-side rendering of the form.** The form has no SEO value, so the cost of converting to a Server Component (file-picker state has to come from somewhere) isn't worth it.
