"""Replace include_embedded_images with image_export on jobs.

Revision ID: 0014_job_image_export
Revises: 0013_job_images_ocr_lang
Create Date: 2026-06-01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0014_job_image_export"
down_revision = "0013_job_images_ocr_lang"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "image_export",
            sa.String(16),
            nullable=False,
            server_default="none",
        ),
    )
    op.execute(
        "UPDATE jobs SET image_export = 'figures' WHERE include_embedded_images = true"
    )
    op.drop_column("jobs", "include_embedded_images")


def downgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "include_embedded_images",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.execute(
        "UPDATE jobs SET include_embedded_images = true "
        "WHERE image_export IN ('figures', 'only')"
    )
    op.drop_column("jobs", "image_export")
