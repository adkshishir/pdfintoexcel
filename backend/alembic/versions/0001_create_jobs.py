"""create jobs

Revision ID: 0001_create_jobs
Revises:
Create Date: 2026-05-01
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_create_jobs"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id",           sa.Uuid(),       primary_key=True),
        sa.Column("status",       sa.String(16),   nullable=False, server_default="pending"),
        sa.Column("mode",         sa.String(16),   nullable=False, server_default="fast"),
        sa.Column("input_url",    sa.Text(),       nullable=False),
        sa.Column("output_url",   sa.Text(),       nullable=True),
        sa.Column("filename",     sa.Text(),       nullable=False),
        sa.Column("size_bytes",   sa.BigInteger(), nullable=False),
        sa.Column("page_count",   sa.Integer(),    nullable=True),
        sa.Column("pdf_type",     sa.String(16),   nullable=True),
        sa.Column("error",        sa.Text(),       nullable=True),
        sa.Column("metrics",      sa.JSON(),       nullable=True),
        sa.Column("created_at",   sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("started_at",   sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at",   sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("jobs_status_idx", "jobs", ["status"])
    op.create_index(
        "jobs_expires_at_idx", "jobs", ["expires_at"],
        postgresql_where=sa.text("status = 'completed'"),
    )


def downgrade() -> None:
    op.drop_index("jobs_expires_at_idx", table_name="jobs")
    op.drop_index("jobs_status_idx", table_name="jobs")
    op.drop_table("jobs")
