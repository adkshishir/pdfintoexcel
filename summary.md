# Project summary — for everyone

This document explains **where we are**, **what it means in plain English**, and **what to tackle next**. You do not need a technical background to read it.

**Last refreshed:** May 2026 (aligned with `STATUS.md`)

---

## What we built

**We built a web product that turns PDFs into usable Excel spreadsheets**, with emphasis on documents that confuse ordinary converters:

- Typed columns (dates as dates, amounts as numbers, and so on) where possible.
- **Printed or handwritten PDFs**, not only “digital” PDFs born from Word or spreadsheets.
- A **technical approach that rebuilds tables from layout** rather than blindly copying blocks of text—a difference that mainly matters when tables are noisy, scanned, or irregular.

Behind the curtain there is an upload page, servers that convert files in the background, and storage so users can retrieve results later. Automated checks help catch regressions when we change code.

---

## Where we are today (by audience)

### For end users (conversion product)

Customers can typically:

1. Upload a PDF.
2. Wait while the job is processed (the heavy work runs in the background).
3. Download an `.xlsx` file.

**Choices that matter today include:** speed versus maximum accuracy for difficult PDFs; whether to extract **only tables** or turn a **whole document** into structured Excel (headings, body text, and tables arranged in reading order—not a raw dump of coordinates); whether similar tables **merge onto one sheet** or **stay on separate sheets** for easier layout control.

Outputs can include hints about uncertainty on difficult cells so a human can sanity-check questionable spots.

---

### For growth and Marketing (still developing)

Beyond the converter, **we’re adding the pieces a real SaaS landing site needs**:

- **Blog**: publish educational or SEO-focused articles without editing code.
- **Landing pages**: custom pages with titles, body copy, FAQs, and internal links (for campaigns or SEO).
- **SEO metadata**: structured information so search engines and social previews show the right titles and descriptions.
- **Private admin dashboard**: one place with **Analytics** (traffic and conversion-ish signals tied to usage), Blog, SEO, Landing pages, Site operations, and Activity—intended for the team running the site, not for end customers uploading PDFs.

**Admin login matters:** only trusted people should access the dashboard. That needs sensible passwords, HTTPS in production, and clear rules for who counts as admin.

Database updates run through formal “migrations” so production can be upgraded safely; your technical owner should apply those before trusting new blog or landing features in production.

---

## Honest limits (things that can still bite)

These are trade-offs worth knowing—not blockers on shipping, but things support and product should recognise:

| Area | Plain-English implication |
| ---- | ------------------------- |
| **Very busy first pages** | If page 1 mixes a brochure-style block with a real table underneath, advanced cleanup may prioritise one block—the other sometimes loses out until we specialise that case further. |
| **Text that spills across printed pages** | A sentence that wraps from the bottom of one page to the top of another may split across rows differently than humans expect. |
| **Cloud file storage “for real”** | Object storage wiring exists, but flipping to a paid cloud tenancy is a **first-production** integration step (credentials and smoke tests). |

---

## What to do next (practical checklist)

Use this list in order—it mixes business, ops, and one line for whoever deploys software.

### 1. Decide who does what

- **Product/marketing**: owns wording on the homepage, landing pages, and blog roadmap.
- **Support**: knows the limitations above and when to escalate to engineering.
- **Technical owner**: runs deployments, backups, migrations, secrets, and monitoring.

### 2. Before real customers rely on dashboard features

Ask your technical owner to confirm:

- **Database migrations** are applied wherever the app runs (staging and production blog/SEO/admin features depend on newer tables and columns).
- **Admin accounts** exist only for the right people with strong passwords.
- **Secrets** (API keys, JWT signing secrets, DB passwords) live in secure environment configuration—not in git or Slack screenshots.

### 3. Finish the commercial story around the converter

Priorities that parallel most SaaS launches:

- **Hosting and domain**: public site on HTTPS, separate from local developer machines.
- **Legal hygiene**: Terms, privacy policy, and cookie stance if you track visitors or use analytics.
- **Payments and limits**: if/when trials, quotas, or paid tiers exist, align them with the rate limits and observability already in the stack.

### 4. Content and demand

Even the best extractor needs discoverability:

- Publish a **steady stream of concrete help** (“bank statements”, “scanned invoices”, “multi-page reports”) tied to landing pages or blog posts people actually search for.
- Collect **diverse PDF samples** from real workflows (digital, scanned, messy tables) so quality doesn’t degrade on edge cases—the technical team feeds these into benchmarking and QA.

### 5. Decide open product choices (document the decision once)

Someone with authority should record:

- **OCR sizing**: heavyweight accuracy models bundled in deployment images versus downloaded on demand (impacts build time, image size, and first-run speed).
- **Where files live in production** (local disk for early pilots vs cloud object storage for scale).

### 6. After launch, keep a short feedback loop

- Watch **failed jobs** and user complaints for patterns.
- Review **dashboard analytics** for top pages and drop-off.
- Revisit **SEO** titles and descriptions quarterly as offerings change.

---

## Where technical detail lives

- **Day-to-day engineering status and file-level notes:** [`STATUS.md`](./STATUS.md)
- **Architecture and phase history:** [`PROJECT_PLAN.md`](./PROJECT_PLAN.md) and the `docs/phase-*.md` write-ups
- **How to run the stack:** top-level [`README.md`](./README.md) and `infrastructure/docker-compose.yml`

If this summary and `STATUS.md` disagree, treat **`STATUS.md` as the source of truth** for engineers and update this file when something material changes for stakeholders.
