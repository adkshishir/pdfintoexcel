"""LLM-powered blog post generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.blog_post import BlogPost
from app.models.seo import LandingPage
from app.schemas.blog import BlogPostCreate
from app.services import blog_service, llm_client
from app.services.blog_content_strategy import (
    BLOG_CTA_MARKDOWN,
    COMPETITOR_PLATFORMS,
    BlogTopicStrategy,
    slug_from_topic,
)

SITE_BASE = "https://pdfintoexcel.com"


@dataclass
class GenerationResult:
    data: BlogPostCreate
    faqs: list[dict[str, str]]
    quality_warnings: list[str]


def _build_system_prompt() -> str:
    return """You are an expert SEO content writer for pdfintoexcel.com, a free online PDF to Excel converter.

Product facts:
- Converts PDF files to editable Excel (.xlsx) spreadsheets
- Handles native PDF tables, scanned documents (OCR), multi-page files
- Preserves row/column structure; flags low-confidence cells in accurate mode
- Browser-based, no desktop install required
- Strong table detection on financial documents (bank statements, invoices)
- Files are deleted after conversion (privacy-first)
- Free tier with sensible limits

Differentiators to mention naturally (without overstating):
- Geometric table reconstruction (not just text paste)
- OCR for scanned/image PDFs
- Honest about OCR errors and complex multi-column layouts

Tone: factual, helpful, no emojis, no unrealistic claims like "100% accuracy".

Output MUST be valid JSON with these keys:
- title (string)
- slug (lowercase hyphenated, max 160 chars)
- meta_title (50-60 chars ideal)
- meta_description (120-160 chars)
- keywords (comma-separated, 5-10 phrases)
- body (Markdown string, 1800-2500 words, NO H1 — title is separate)
- faqs (array of {q, a}, minimum 5 items)

Body format rules:
- Use Markdown only (## for H2, ### for H3, lists, **bold**, links)
- For comparison articles: include a GFM pipe table comparing platforms
- Each FAQ question becomes ### heading in a "## Frequently Asked Questions" section
- Include 2-4 internal markdown links to provided blog/landing pages or homepage
- Do NOT link to /pricing or /features (those pages do not exist)
- End body WITHOUT the CTA block (it is appended automatically)

Comparison articles (when is_comparison=true) MUST include these H2 sections:
1. Introduction (primary keyword in first paragraph)
2. How PDFIntoExcel compares (with comparison table)
3. When to choose each platform
4. Step-by-step guide or practical implementation
5. Common mistakes and best practices
6. Frequently Asked Questions
7. Further reading (2-4 external links)

Non-comparison articles MUST include:
1. Introduction (primary keyword in first paragraph)
2. Core category content
3. Practical step-by-step or actionable section
4. Common mistakes and best practices
5. Frequently Asked Questions
6. Further reading (optional, 1-3 external links)
"""


def _build_user_prompt(
    topic: BlogTopicStrategy,
    *,
    existing_posts: list[dict[str, str]],
    landing_slugs: list[str],
) -> str:
    internal_links = "\n".join(
        f"- /blog/{p['slug']} — {p['title']}" for p in existing_posts[:20]
    )
    landings = "\n".join(f"- /{s}" for s in landing_slugs)

    competitors = ", ".join(topic.comparison_targets or COMPETITOR_PLATFORMS[:3])

    return f"""Write a blog article with these parameters:

Topic: {topic.topic}
Primary keyword: {topic.primary_keyword}
Category: {topic.category_slug}
Is comparison article: {topic.is_comparison}
{"Named competitors: " + competitors if topic.is_comparison else ""}

Available internal blog links:
{internal_links or "(none yet — link to homepage /)"}

Available landing pages:
{landings or "(none — link to /)"}

Homepage CTA target: /?utm_source=blog&utm_medium=article

Position pdfintoexcel as recommended where relevant, with honest limitations.
Return JSON only.
"""


def _build_schema_jsonld(
    title: str,
    meta_description: str,
    faqs: list[dict[str, str]],
) -> dict[str, Any]:
    graph: list[dict[str, Any]] = [
        {
            "@type": "BlogPosting",
            "headline": title,
            "description": meta_description,
            "author": {"@type": "Organization", "name": "pdfintoexcel"},
            "publisher": {"@type": "Organization", "name": "pdfintoexcel"},
        }
    ]
    if faqs:
        graph.append(
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f["q"],
                        "acceptedAnswer": {"@type": "Answer", "text": f["a"]},
                    }
                    for f in faqs
                ],
            }
        )
    return {"@context": "https://schema.org", "@graph": graph}


def quality_check(
    payload: dict[str, Any],
    topic: BlogTopicStrategy,
    *,
    existing_slugs: set[str],
) -> list[str]:
    warnings: list[str] = []
    title = str(payload.get("title", ""))
    slug = str(payload.get("slug", ""))
    meta_desc = str(payload.get("meta_description", ""))
    body = str(payload.get("body", ""))
    faqs = payload.get("faqs") or []

    if not title:
        warnings.append("missing title")
    if topic.primary_keyword.lower() not in title.lower():
        warnings.append("primary keyword not in title")
    first_para = body.split("\n\n")[0] if body else ""
    if topic.primary_keyword.lower() not in first_para.lower():
        warnings.append("primary keyword not in first paragraph")

    if len(meta_desc) < 120 or len(meta_desc) > 160:
        warnings.append(f"meta_description length {len(meta_desc)} (want 120-160)")

    if len(faqs) < 5:
        warnings.append(f"only {len(faqs)} FAQs (want >= 5)")

    if slug in existing_slugs:
        warnings.append(f"slug '{slug}' already exists")

    if topic.is_comparison:
        has_table = "|" in body and "---" in body
        if not has_table:
            warnings.append("comparison post missing GFM table")

    word_count = len(body.split())
    if word_count < 1500:
        warnings.append(f"body word count {word_count} (target 1800-2500)")

    return warnings


def _gather_context(db: Session) -> tuple[list[dict[str, str]], list[str], set[str]]:
    posts = list(
        db.scalars(
            select(BlogPost)
            .where(BlogPost.status.in_(["published", "draft"]))
            .order_by(BlogPost.updated_at.desc())
        ).all()
    )
    existing = [{"slug": p.slug, "title": p.title} for p in posts]
    slugs = {p.slug for p in posts}
    landings = [
        row.slug
        for row in db.scalars(
            select(LandingPage).where(LandingPage.status == "published")
        ).all()
    ]
    return existing, landings, slugs


def generate_post(
    db: Session,
    topic: BlogTopicStrategy,
    *,
    category_id: str | None = None,
    llm_complete_json: Any = None,
) -> GenerationResult:
    """Generate a draft blog post. llm_complete_json injectable for tests."""
    complete = llm_complete_json or llm_client.complete_json
    existing_posts, landing_slugs, existing_slugs = _gather_context(db)

    raw = complete(_build_system_prompt(), _build_user_prompt(
        topic,
        existing_posts=existing_posts,
        landing_slugs=landing_slugs,
    ))

    slug = raw.get("slug") or slug_from_topic(topic.topic)
    slug = blog_service.normalize_slug(str(slug))
    body = str(raw.get("body", "")).strip()
    if BLOG_CTA_MARKDOWN.strip() not in body:
        body = body + BLOG_CTA_MARKDOWN

    faqs = raw.get("faqs") or []
    if isinstance(faqs, list):
        faqs = [{"q": str(f.get("q", "")), "a": str(f.get("a", ""))} for f in faqs]
    else:
        faqs = []

    title = str(raw.get("title", topic.topic))
    meta_description = str(raw.get("meta_description", ""))
    warnings = quality_check(raw, topic, existing_slugs=existing_slugs)

    schema = _build_schema_jsonld(title, meta_description, faqs)

    data = BlogPostCreate(
        slug=slug,
        title=title,
        meta_title=raw.get("meta_title"),
        meta_description=meta_description,
        body=body,
        status="draft",
        category_id=category_id,
        keywords=raw.get("keywords"),
        schema_jsonld=schema,
        tag_ids=[],
    )
    return GenerationResult(data=data, faqs=faqs, quality_warnings=warnings)


def generate_and_save(
    db: Session,
    topic: BlogTopicStrategy,
    *,
    category_id: str | None = None,
    llm_complete_json: Any = None,
) -> tuple[Any, GenerationResult]:
    result = generate_post(
        db, topic, category_id=category_id, llm_complete_json=llm_complete_json
    )
    post = blog_service.create_post(db, result.data)
    return post, result
