"""add output_layout

Revision ID: 0002_add_output_layout
Revises: 0001_create_jobs
Create Date: 2026-05-01
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_add_output_layout"
down_revision = "0001_create_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Default existing rows to "merged" — preserves prior behavior.
    op.add_column(
        "jobs",
        sa.Column("output_layout", sa.String(16), nullable=False, server_default="merged"),
    )


def downgrade() -> None:
    op.drop_column("jobs", "output_layout")
