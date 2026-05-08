"""add download_count to jobs

Revision ID: 0005_add_download_count
Revises: 0004_add_full_document_pages
Create Date: 2026-05-07
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_add_download_count"
down_revision = "0004_add_full_document_pages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("jobs")}
    if "download_count" in existing:
        return
    op.add_column(
        "jobs",
        sa.Column(
            "download_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("jobs")}
    if "download_count" not in existing:
        return
    op.drop_column("jobs", "download_count")
