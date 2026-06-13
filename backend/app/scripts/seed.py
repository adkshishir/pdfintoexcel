"""Idempotent database seed: bootstrap admin (same as first login) + sample blog posts.

Host-side (venv + Postgres on localhost:5433 via `make up`):

    cp .env.example .env   # uses localhost, not the in-compose hostname `postgres`
    .venv/bin/python -m app.scripts.seed

Inside the running stack (no host DATABASE_URL needed):

    make seed

Reads credentials and JWT settings from `backend/.env` / environment via `Settings`.

Runs `alembic upgrade head` first so a fresh Postgres volume has `admin_users`
and other tables before inserts (same as the API container entrypoint).
"""

from __future__ import annotations

import sys
from pathlib import Path

# `python -m app.scripts.seed` puts backend/ on sys.path[0], which shadows the
# installed `alembic` package with this repo's migrations folder (also alembic/).
_backend_root = Path(__file__).resolve().parents[2]
if sys.path and Path(sys.path[0]).resolve() == _backend_root:
    sys.path.pop(0)

try:
    from alembic import command
    from alembic.config import Config
except ImportError as exc:
    raise ImportError(
        "Alembic is not installed for this Python interpreter. "
        "From backend/, run: .venv/bin/python -m app.scripts.seed "
        "(or activate .venv and pip install -r requirements.txt)."
    ) from exc
from sqlalchemy import select

from app.models.blog_post import BlogPost
from app.models.database import session_scope
from app.models.seo import LandingPage
from app.schemas.blog import BlogPostCreate
from app.services import auth_service, blog_service
from app.scripts.seo_content import LANDING_PAGES, SEO_BLOG_POSTS


def _upgrade_schema_to_head() -> None:
    """Apply migrations so seeding never hits missing-table errors on a new DB."""
    ini_path = _backend_root / "alembic.ini"
    if not ini_path.is_file():
        raise FileNotFoundError(f"alembic.ini not found at {ini_path}")
    cfg = Config(str(ini_path))
    command.upgrade(cfg, "head")

_SAMPLE_POSTS: tuple[BlogPostCreate, ...] = (
    BlogPostCreate(
        slug="welcome",
        title="Welcome",
        meta_description="Getting started with the blog.",
        body="This post was created by the seed script. Edit or delete it in the dashboard.",
        status="published",
        tag_ids=[],
    ),
    BlogPostCreate(
        slug="hello-world",
        title="Hello world",
        meta_description="A second sample post in draft state.",
        body="Draft content — publish from the admin console when ready.",
        status="draft",
        tag_ids=[],
    ),
)


def run_seed() -> None:
    _upgrade_schema_to_head()

    with session_scope() as db:
        auth_service.ensure_bootstrap_admin(db)

    with session_scope() as db:
        for sample in _SAMPLE_POSTS:
            existing = db.scalar(select(BlogPost).where(BlogPost.slug == sample.slug))
            if existing:
                continue
            blog_service.create_post(db, sample)

    with session_scope() as db:
        for landing in LANDING_PAGES:
            existing = db.scalar(select(LandingPage).where(LandingPage.slug == landing.slug))
            if existing:
                continue
            db.add(
                LandingPage(
                    slug=landing.slug,
                    title=landing.title,
                    body=landing.body,
                    faq_items=landing.faq_items,
                    internal_links=landing.internal_links,
                    status=landing.status,
                )
            )
        db.commit()

    with session_scope() as db:
        for post in SEO_BLOG_POSTS:
            existing = db.scalar(select(BlogPost).where(BlogPost.slug == post.slug))
            if existing:
                continue
            blog_service.create_post(
                db,
                BlogPostCreate(
                    slug=post.slug,
                    title=post.title,
                    meta_title=post.meta_title,
                    meta_description=post.meta_description,
                    body=post.body,
                    status=post.status,
                    keywords=post.keywords,
                    tag_ids=[],
                ),
            )


def main() -> None:
    run_seed()


if __name__ == "__main__":
    main()
