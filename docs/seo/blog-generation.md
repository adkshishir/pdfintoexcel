# Blog generation (LLM drafts)

AI-assisted blog drafts from the content strategy defined in
[`pdfintoexcel-blog-content-strategy.md`](../../pdfintoexcel-blog-content-strategy.md).

## Prerequisites

1. Postgres running (`make up`)
2. Categories seeded: `make seed` (or `python -m app.scripts.seed`)
3. LLM API key in `backend/.env`:

```env
BLOG_LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.0-flash
```

For OpenAI instead:

```env
BLOG_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1
```

For Anthropic instead:

```env
BLOG_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

## Admin dashboard

1. Log in at `/dashboard/login`
2. Open **Blog → Generate draft** (`/dashboard/blog/generate`)
3. Review the suggested next topic (picked from the 8-week calendar, then backlog)
4. Click **Generate draft** — creates a `draft` post via LLM
5. Edit, fix quality warnings, then publish or schedule

## CLI

From `backend/` with venv active:

```bash
# Next topic from strategy
.venv/bin/python -m app.scripts.generate_blog_post

# Custom topic
.venv/bin/python -m app.scripts.generate_blog_post --topic "PDFIntoExcel vs Smallpdf"
```

Output includes post `id` and slug. Edit in the dashboard before publishing.

## Topic selection rules

- Skips topics whose slug or title already exists (published or draft)
- Prefers calendar order (weeks 1–16) over extended backlog
- Balances categories (`tutorial`, `guide`, `workflow`, `features`)
- Targets ~45% comparison posts (`COMPARISON_POST_RATIO`)

## Pre-publish checklist

Before publishing a generated draft:

- [ ] Primary keyword in title, first paragraph, and meta description
- [ ] Category matches content type
- [ ] Comparison posts include a comparison table and named competitors
- [ ] At least 5 FAQs present
- [ ] 2–4 internal links to `/`, landing pages, or existing blog posts
- [ ] No unrealistic accuracy claims
- [ ] CTA links include `?utm_source=blog&utm_medium=article`
- [ ] Slug is unique and URL-safe

## Code layout

| Module | Role |
|--------|------|
| `app/services/blog_content_strategy.py` | Calendar, backlog, helpers |
| `app/services/blog_topic_picker.py` | `pick_next_topic()` |
| `app/services/blog_generator.py` | Prompts, quality check, draft save |
| `app/services/llm_client.py` | Gemini / OpenAI / Anthropic JSON completion |
| `frontend/src/lib/blog-content-strategy.data.ts` | TS mirror for UI |

## API (admin auth required)

- `GET /api/admin/blog/categories`
- `GET /api/admin/blog/next-topic`
- `POST /api/admin/blog/generate` — body: `{ "topic": "optional custom title" }`
