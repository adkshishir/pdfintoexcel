"""Idempotent database seed: bootstrap admin (same as first login) + sample blog posts.

Run from repo `backend/` directory:

    python -m app.scripts.seed

Reads credentials and JWT settings from `.env` / environment via `Settings`.

Runs `alembic upgrade head` first so a fresh Postgres volume has `admin_users`
and other tables before inserts (same as the API container entrypoint).
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import select

from app.models.blog_post import BlogPost
from app.models.database import session_scope
from app.schemas.blog import BlogPostCreate
from app.services import auth_service, blog_service


def _upgrade_schema_to_head() -> None:
    """Apply migrations so seeding never hits missing-table errors on a new DB."""
    backend_root = Path(__file__).resolve().parents[2]
    ini_path = backend_root / "alembic.ini"
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


def main() -> None:
    run_seed()


if __name__ == "__main__":
    main()
