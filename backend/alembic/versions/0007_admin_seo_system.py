"""admin auth + seo growth schema

Revision ID: 0007_admin_seo_system
Revises: 0006_blog_posts
Create Date: 2026-05-08
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_admin_seo_system"
down_revision = "0006_blog_posts"
branch_labels = None
depends_on = None


def _has_table(conn, table_name: str) -> bool:
    # Inspector.get_table_names() can reflect a stale snapshot on the migration
    # connection; use live catalog checks on PostgreSQL so we never skip CREATEs.
    if conn.dialect.name == "postgresql":
        return bool(
            conn.execute(
                sa.text(
                    """
                    SELECT EXISTS (
                      SELECT 1 FROM information_schema.tables
                      WHERE table_catalog = current_database()
                        AND table_schema = current_schema()
                        AND table_name = :t
                    )
                    """
                ),
                {"t": table_name},
            ).scalar()
        )
    return table_name in sa.inspect(conn).get_table_names()


def _has_column(conn, table_name: str, col: str) -> bool:
    if conn.dialect.name == "postgresql":
        return bool(
            conn.execute(
                sa.text(
                    """
                    SELECT EXISTS (
                      SELECT 1 FROM information_schema.columns
                      WHERE table_catalog = current_database()
                        AND table_schema = current_schema()
                        AND table_name = :t
                        AND column_name = :c
                    )
                    """
                ),
                {"t": table_name, "c": col},
            ).scalar()
        )
    try:
        return col in {c["name"] for c in sa.inspect(conn).get_columns(table_name)}
    except Exception:
        return False


def upgrade() -> None:
    conn = op.get_bind()

    if not _has_table(conn, "admin_users"):
        op.create_table(
            "admin_users",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.Text(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email"),
        )

    if not _has_table(conn, "roles"):
        op.create_table(
            "roles",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.String(length=64), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )

    if not _has_table(conn, "user_roles"):
        op.create_table(
            "user_roles",
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("role_id", sa.Uuid(), nullable=False),
            sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["admin_users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id", "role_id"),
        )

    if not _has_table(conn, "refresh_tokens"):
        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("token_hash", sa.Text(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["admin_users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("refresh_tokens_user_idx", "refresh_tokens", ["user_id"])

    if not _has_table(conn, "blog_categories"):
        op.create_table(
            "blog_categories",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("slug", sa.String(length=160), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
            sa.UniqueConstraint("slug"),
        )
    if not _has_table(conn, "blog_tags"):
        op.create_table(
            "blog_tags",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("slug", sa.String(length=160), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
            sa.UniqueConstraint("slug"),
        )
    if not _has_table(conn, "blog_post_tags"):
        op.create_table(
            "blog_post_tags",
            sa.Column("post_id", sa.Uuid(), nullable=False),
            sa.Column("tag_id", sa.Uuid(), nullable=False),
            sa.ForeignKeyConstraint(["post_id"], ["blog_posts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["tag_id"], ["blog_tags.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("post_id", "tag_id"),
        )

    if not _has_column(conn, "blog_posts", "status"):
        op.add_column("blog_posts", sa.Column("status", sa.String(length=20), nullable=True))
        op.execute(sa.text("UPDATE blog_posts SET status = CASE WHEN published THEN 'published' ELSE 'draft' END"))
        op.alter_column("blog_posts", "status", nullable=False)
    if _has_column(conn, "blog_posts", "published"):
        op.drop_column("blog_posts", "published")
    if not _has_column(conn, "blog_posts", "meta_title"):
        op.add_column("blog_posts", sa.Column("meta_title", sa.String(length=320), nullable=True))
    if not _has_column(conn, "blog_posts", "scheduled_at"):
        op.add_column("blog_posts", sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True))
    if not _has_column(conn, "blog_posts", "cover_image_url"):
        op.add_column("blog_posts", sa.Column("cover_image_url", sa.Text(), nullable=True))
    if not _has_column(conn, "blog_posts", "category_id"):
        op.add_column("blog_posts", sa.Column("category_id", sa.Uuid(), nullable=True))
        op.create_foreign_key("blog_posts_category_fk", "blog_posts", "blog_categories", ["category_id"], ["id"], ondelete="SET NULL")
    if _has_column(conn, "blog_posts", "canonical_path"):
        op.alter_column("blog_posts", "canonical_path", new_column_name="canonical_url")
    if not _has_column(conn, "blog_posts", "robots_directives"):
        op.add_column("blog_posts", sa.Column("robots_directives", sa.String(length=120), nullable=True))
    if not _has_column(conn, "blog_posts", "schema_jsonld"):
        op.add_column("blog_posts", sa.Column("schema_jsonld", sa.JSON(), nullable=True))

    if not _has_table(conn, "seo_meta"):
        op.create_table(
            "seo_meta",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("entity_type", sa.String(length=40), nullable=False),
            sa.Column("entity_id", sa.String(length=100), nullable=False),
            sa.Column("title", sa.String(length=320), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("keywords", sa.String(length=500), nullable=True),
            sa.Column("canonical_url", sa.String(length=500), nullable=True),
            sa.Column("robots", sa.String(length=120), nullable=True),
            sa.Column("og_title", sa.String(length=320), nullable=True),
            sa.Column("og_description", sa.Text(), nullable=True),
            sa.Column("og_image", sa.Text(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("seo_meta_entity_idx", "seo_meta", ["entity_type", "entity_id"], unique=True)

    if not _has_table(conn, "schema_documents"):
        op.create_table(
            "schema_documents",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("entity_type", sa.String(length=40), nullable=False),
            sa.Column("entity_id", sa.String(length=100), nullable=False),
            sa.Column("schema_type", sa.String(length=60), nullable=False),
            sa.Column("payload_json", sa.JSON(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("schema_documents_entity_idx", "schema_documents", ["entity_type", "entity_id"], unique=True)

    if not _has_table(conn, "landing_pages"):
        op.create_table(
            "landing_pages",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("slug", sa.String(length=180), nullable=False),
            sa.Column("title", sa.String(length=300), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("faq_items", sa.JSON(), nullable=False),
            sa.Column("internal_links", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("slug"),
        )

    if not _has_table(conn, "sitemap_exclusions"):
        op.create_table(
            "sitemap_exclusions",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("path", sa.String(length=300), nullable=False),
            sa.Column("reason", sa.String(length=250), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("path"),
        )

    if not _has_table(conn, "internal_link_suggestions"):
        op.create_table(
            "internal_link_suggestions",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("source_type", sa.String(length=30), nullable=False),
            sa.Column("source_id", sa.String(length=100), nullable=False),
            sa.Column("target_path", sa.String(length=300), nullable=False),
            sa.Column("anchor_text", sa.String(length=200), nullable=False),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("accepted", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table(conn, "audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("actor_user_id", sa.Uuid(), nullable=True),
            sa.Column("action", sa.String(length=80), nullable=False),
            sa.Column("entity_type", sa.String(length=40), nullable=False),
            sa.Column("entity_id", sa.String(length=100), nullable=False),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("internal_link_suggestions")
    op.drop_table("sitemap_exclusions")
    op.drop_table("landing_pages")
    op.drop_index("schema_documents_entity_idx", table_name="schema_documents")
    op.drop_table("schema_documents")
    op.drop_index("seo_meta_entity_idx", table_name="seo_meta")
    op.drop_table("seo_meta")
    op.drop_table("blog_post_tags")
    op.drop_table("blog_tags")
    op.drop_table("blog_categories")
    op.drop_index("refresh_tokens_user_idx", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.drop_table("admin_users")
