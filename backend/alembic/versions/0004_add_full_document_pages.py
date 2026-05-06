"""add full_document_pages

Revision ID: 0004_add_full_document_pages
Revises: 0003_add_extraction_scope
Create Date: 2026-05-06
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_add_full_document_pages"
down_revision = "0003_add_extraction_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Safe when several containers run `alembic upgrade head` at once (backend,
    # worker, beat entrypoints): only the first ADD succeeds; others must no-op.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("jobs")}
    if "full_document_pages" in existing:
        return
    op.add_column(
        "jobs",
        sa.Column(
            "full_document_pages",
            sa.String(20),
            nullable=False,
            server_default="single_sheet",
        ),
    )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("jobs")}
    if "full_document_pages" not in existing:
        return
    op.drop_column("jobs", "full_document_pages")
