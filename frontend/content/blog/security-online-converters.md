---
title: Security basics for online PDF converters
description: What happens to your file after upload, and the questions every team should ask before using a cloud converter.
date: 2026-04-15
---

## Data handling questions

Before you upload a contract, payroll extract, or customer list, ask:

1. **Is the file encrypted in transit?** (HTTPS is table stakes.)
2. **How long are files retained?** Shorter is usually better for privacy.
3. **Is content used to train models?** For many enterprise workflows, the answer must be **no**.

## Operational hygiene

Retention windows and automatic deletion reduce risk even if a storage bucket is misconfigured. Prefer secrets that are **scoped per job**, not long-lived links to raw uploads.

## pdfintoexcel

We designed pdfintoexcel around short-lived storage and predictable deletion — see our [Privacy](/privacy) page for the current policy language.

If you operate in a regulated industry, run your DPIA against the actual subprocessors in production, not the marketing site alone.
