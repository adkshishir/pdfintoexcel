"""Generate a blog post draft via LLM and save to Postgres.

Host-side:

    cd backend && .venv/bin/python -m app.scripts.generate_blog_post
    cd backend && .venv/bin/python -m app.scripts.generate_blog_post --topic "PDFIntoExcel vs Smallpdf"

Requires GEMINI_API_KEY (default), or OPENAI_API_KEY / ANTHROPIC_API_KEY in backend/.env.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_backend_root = Path(__file__).resolve().parents[2]
if sys.path and Path(sys.path[0]).resolve() == _backend_root:
    sys.path.pop(0)

from app.models.database import session_scope
from app.services import blog_generator
from app.services.blog_topic_picker import pick_next_topic, resolve_topic


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a blog post draft")
    parser.add_argument("--topic", help="Custom topic title (optional)")
    parser.add_argument(
        "--category",
        choices=["tutorial", "guide", "workflow", "features"],
        help="Category slug override",
    )
    parser.add_argument(
        "--comparison",
        action="store_true",
        help="Force comparison article",
    )
    parser.add_argument(
        "--no-comparison",
        action="store_true",
        help="Force non-comparison article",
    )
    args = parser.parse_args()

    is_comparison = None
    if args.comparison:
        is_comparison = True
    elif args.no_comparison:
        is_comparison = False

    with session_scope() as db:
        if args.topic:
            topic = resolve_topic(
                args.topic,
                category_slug=args.category,
                is_comparison=is_comparison,
            )
            from app.services import blog_service

            cats = {c.slug: str(c.id) for c in blog_service.list_categories(db)}
            category_id = cats.get(topic.category_slug)
        else:
            pick = pick_next_topic(db)
            topic = pick.topic
            category_id = pick.category_id
            print(f"Selected topic: {topic.topic}")
            print(f"Rationale: {pick.rationale}")

        post, result = blog_generator.generate_and_save(
            db, topic, category_id=category_id
        )

    if result.quality_warnings:
        print("\nQuality warnings:")
        for w in result.quality_warnings:
            print(f"  - {w}")

    print(f"\nDraft created: slug={post.slug} id={post.id}")
    print(f"Edit at: /dashboard/blog/{post.id}/edit")


if __name__ == "__main__":
    main()
