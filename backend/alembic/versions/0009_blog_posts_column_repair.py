"""Repair drifted blog_posts columns (safe idempotent ADDs).

Some environments reached revision 0008 without all ALTER TABLE statements
applied. Postgres: one ALTER per execute for reliable application.

Revision ID: 0009_blog_posts_column_repair
Revises: 0008_blog_posts_ensure_columns
Create Date: 2026-05-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_blog_posts_column_repair"
down_revision = "0008_blog_posts_ensure_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return
    stmts = [
        "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS meta_title VARCHAR(320)",
        "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMPTZ",
        "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS cover_image_url TEXT",
        "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS robots_directives VARCHAR(120)",
        "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS schema_jsonld JSONB",
        "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS category_id UUID",
    ]
    for stmt in stmts:
        op.execute(sa.text(stmt))


def downgrade() -> None:
    pass
