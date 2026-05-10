"""Ensure blog_posts columns match ORM (repair partial migrations).

Revision ID: 0008_blog_posts_ensure_columns
Revises: 0007_admin_seo_system
Create Date: 2026-05-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_blog_posts_ensure_columns"
down_revision = "0007_admin_seo_system"
branch_labels = None
depends_on = None


def _cols(inspector: sa.Inspector, table: str) -> set[str]:
    try:
        return {c["name"] for c in inspector.get_columns(table)}
    except Exception:
        return set()


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if conn.dialect.name == "postgresql":
        exists_row = conn.execute(
            sa.text(
                """
                SELECT EXISTS (
                  SELECT 1 FROM information_schema.tables
                  WHERE table_schema = current_schema()
                    AND table_name = 'blog_posts'
                )
                """
            )
        ).scalar()
        if not exists_row:
            return
        inspector = sa.inspect(conn)

    elif "blog_posts" not in inspector.get_table_names():
        return

    # Postgres: one ALTER per execute (bundled scripts are not reliable with all drivers/layers).
    if conn.dialect.name == "postgresql":
        _pg_if_not_cols = (
            "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS meta_title VARCHAR(320)",
            "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMPTZ",
            "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS cover_image_url TEXT",
            "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS robots_directives VARCHAR(120)",
            "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS schema_jsonld JSONB",
            "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS category_id UUID",
        )
        for stmt in _pg_if_not_cols:
            op.execute(sa.text(stmt))
        inspector = sa.inspect(conn)

    cols = _cols(inspector, "blog_posts")

    # status + drop published (legacy)
    if "status" not in cols and "published" in cols:
        op.add_column("blog_posts", sa.Column("status", sa.String(length=20), nullable=True))
        op.execute(
            sa.text(
                "UPDATE blog_posts SET status = CASE WHEN published THEN 'published' ELSE 'draft' END"
            )
        )
        op.alter_column("blog_posts", "status", nullable=False)
        op.drop_column("blog_posts", "published")
        inspector = sa.inspect(conn)
        cols = _cols(inspector, "blog_posts")
    elif "status" not in cols:
        op.add_column(
            "blog_posts",
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        )
        op.alter_column("blog_posts", "status", server_default=None)
        inspector = sa.inspect(conn)
        cols = _cols(inspector, "blog_posts")

    if "meta_title" not in cols:
        op.add_column(
            "blog_posts", sa.Column("meta_title", sa.String(length=320), nullable=True)
        )
        cols.add("meta_title")

    if "scheduled_at" not in cols:
        op.add_column(
            "blog_posts",
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        )
        cols.add("scheduled_at")

    if "cover_image_url" not in cols:
        op.add_column("blog_posts", sa.Column("cover_image_url", sa.Text(), nullable=True))
        cols.add("cover_image_url")

    if "canonical_path" in cols and "canonical_url" not in cols:
        op.alter_column("blog_posts", "canonical_path", new_column_name="canonical_url")
        cols.discard("canonical_path")
        cols.add("canonical_url")

    if "robots_directives" not in cols:
        op.add_column(
            "blog_posts",
            sa.Column("robots_directives", sa.String(length=120), nullable=True),
        )
        cols.add("robots_directives")

    if "schema_jsonld" not in cols:
        op.add_column("blog_posts", sa.Column("schema_jsonld", sa.JSON(), nullable=True))
        cols.add("schema_jsonld")

    inspector = sa.inspect(conn)
    cols = _cols(inspector, "blog_posts")

    if "category_id" not in cols:
        op.add_column("blog_posts", sa.Column("category_id", sa.Uuid(), nullable=True))
        cols.add("category_id")

    inspector = sa.inspect(conn)
    if "blog_categories" in inspector.get_table_names():
        fk_names = {fk["name"] for fk in inspector.get_foreign_keys("blog_posts")}
        if "blog_posts_category_fk" not in fk_names and "category_id" in _cols(
            inspector, "blog_posts"
        ):
            op.create_foreign_key(
                "blog_posts_category_fk",
                "blog_posts",
                "blog_categories",
                ["category_id"],
                ["id"],
                ondelete="SET NULL",
            )

    # Ensure index on status matches ORM (blog_posts_status_idx)
    inspector = sa.inspect(conn)
    idx_names = {x["name"] for x in inspector.get_indexes("blog_posts")}
    if "blog_posts_published_idx" in idx_names:
        op.drop_index("blog_posts_published_idx", table_name="blog_posts")
        idx_names.discard("blog_posts_published_idx")
    if "blog_posts_status_idx" not in idx_names and "status" in _cols(
        inspector, "blog_posts"
    ):
        op.create_index("blog_posts_status_idx", "blog_posts", ["status"], unique=False)


def downgrade() -> None:
    pass
