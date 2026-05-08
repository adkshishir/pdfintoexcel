"""blog_posts CMS table

Revision ID: 0006_blog_posts
Revises: 0005_add_download_count
Create Date: 2026-05-07
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_blog_posts"
down_revision = "0005_add_download_count"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # PostgreSQL: idempotent DDL (safe if a concurrent migrator partially ran).
    if conn.dialect.name == "postgresql":
        op.execute(
            sa.text("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id UUID NOT NULL,
                slug VARCHAR(160) NOT NULL,
                title VARCHAR(300) NOT NULL,
                meta_description TEXT NOT NULL,
                body TEXT NOT NULL,
                published BOOLEAN DEFAULT false NOT NULL,
                og_title VARCHAR(300),
                og_description TEXT,
                og_image_url TEXT,
                canonical_path VARCHAR(500),
                keywords VARCHAR(500),
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                published_at TIMESTAMP WITH TIME ZONE,
                PRIMARY KEY (id),
                CONSTRAINT blog_posts_slug_key UNIQUE (slug)
            );
            """),
        )
        op.execute(
            sa.text(
                "CREATE INDEX IF NOT EXISTS blog_posts_published_idx ON blog_posts (published)",
            ),
        )
        return

    if "blog_posts" in inspector.get_table_names():
        return
    op.create_table(
        "blog_posts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("meta_description", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("og_title", sa.String(length=300), nullable=True),
        sa.Column("og_description", sa.Text(), nullable=True),
        sa.Column("og_image_url", sa.Text(), nullable=True),
        sa.Column("canonical_path", sa.String(length=500), nullable=True),
        sa.Column("keywords", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("blog_posts_published_idx", "blog_posts", ["published"], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute(sa.text("DROP INDEX IF EXISTS blog_posts_published_idx"))
        op.execute(sa.text("DROP TABLE IF EXISTS blog_posts"))
        return

    inspector = sa.inspect(conn)
    if "blog_posts" not in inspector.get_table_names():
        return
    op.drop_index("blog_posts_published_idx", table_name="blog_posts")
    op.drop_table("blog_posts")
