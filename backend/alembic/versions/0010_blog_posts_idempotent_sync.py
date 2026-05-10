"""Sync blog_posts columns with ORM (idempotent; fixes partial 0007 / drift).

Revision ID: 0010_blog_posts_idempotent_sync
Revises: 0009_blog_posts_column_repair
Create Date: 2026-05-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010_blog_posts_idempotent_sync"
down_revision = "0009_blog_posts_column_repair"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    for stmt in (
        "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS meta_title VARCHAR(320)",
        "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMPTZ",
        "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS cover_image_url TEXT",
        "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS robots_directives VARCHAR(120)",
        "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS schema_jsonld JSONB",
        "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS category_id UUID",
    ):
        op.execute(sa.text(stmt))

    op.execute(
        sa.text(
            """
            DO $blk$
            BEGIN
              IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'blog_posts'
                  AND column_name = 'canonical_path'
              ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'blog_posts'
                  AND column_name = 'canonical_url'
              ) THEN
                ALTER TABLE blog_posts RENAME COLUMN canonical_path TO canonical_url;
              END IF;
            END
            $blk$;
            """
        )
    )


def downgrade() -> None:
    pass
