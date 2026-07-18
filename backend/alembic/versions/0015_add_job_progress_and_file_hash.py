"""Add stage, progress_pct, file_hash, extra columns to jobs table.

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-18
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014_job_image_export"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("stage", sa.String(32), nullable=True))
    op.add_column("jobs", sa.Column("progress_pct", sa.Integer, nullable=True))
    op.add_column("jobs", sa.Column("file_hash", sa.String(64), nullable=True))
    op.add_column("jobs", sa.Column("extra", sa.JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "extra")
    op.drop_column("jobs", "file_hash")
    op.drop_column("jobs", "progress_pct")
    op.drop_column("jobs", "stage")
