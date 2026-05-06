"""add extraction_scope

Revision ID: 0003_add_extraction_scope
Revises: 0002_add_output_layout
Create Date: 2026-05-03
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_add_extraction_scope"
down_revision = "0002_add_output_layout"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "extraction_scope",
            sa.String(20),
            nullable=False,
            server_default="tables_only",
        ),
    )


def downgrade() -> None:
    op.drop_column("jobs", "extraction_scope")
