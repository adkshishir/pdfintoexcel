"""Add include_embedded_images and ocr_auto_lang to jobs.

Revision ID: 0013_job_images_ocr_lang
Revises: 0012_job_ocr_preferences
Create Date: 2026-05-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0013_job_images_ocr_lang"
down_revision = "0012_job_ocr_preferences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "include_embedded_images",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "ocr_auto_lang",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("jobs", "ocr_auto_lang")
    op.drop_column("jobs", "include_embedded_images")
