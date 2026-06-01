"""Add OCR / text-layer tuning columns on jobs.

Revision ID: 0012_job_ocr_preferences
Revises: 0011_ensure_admin_auth_tables
Create Date: 2026-05-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012_job_ocr_preferences"
down_revision = "0011_ensure_admin_auth_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "trust_pdf_text",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column("jobs", sa.Column("ocr_tesseract_langs", sa.String(64), nullable=True))
    op.add_column("jobs", sa.Column("ocr_paddle_lang", sa.String(16), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "ocr_paddle_lang")
    op.drop_column("jobs", "ocr_tesseract_langs")
    op.drop_column("jobs", "trust_pdf_text")
