"""Create admin auth tables if missing (repair skipped 0007 CREATEs).

Revision ID: 0011_ensure_admin_auth_tables
Revises: 0010_blog_posts_idempotent_sync
Create Date: 2026-05-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011_ensure_admin_auth_tables"
down_revision = "0010_blog_posts_idempotent_sync"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    # Matches 0007 / ORM — IF NOT EXISTS is safe when tables already exist.
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS admin_users (
                id UUID NOT NULL,
                email VARCHAR(255) NOT NULL,
                password_hash TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT true,
                created_at TIMESTAMPTZ NOT NULL,
                last_login_at TIMESTAMPTZ NULL,
                CONSTRAINT admin_users_pkey PRIMARY KEY (id),
                CONSTRAINT admin_users_email_key UNIQUE (email)
            );
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS roles (
                id UUID NOT NULL,
                name VARCHAR(64) NOT NULL,
                CONSTRAINT roles_pkey PRIMARY KEY (id),
                CONSTRAINT roles_name_key UNIQUE (name)
            );
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id UUID NOT NULL,
                role_id UUID NOT NULL,
                assigned_at TIMESTAMPTZ NOT NULL,
                CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id),
                CONSTRAINT user_roles_role_id_fkey
                    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
                CONSTRAINT user_roles_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES admin_users (id) ON DELETE CASCADE
            );
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id UUID NOT NULL,
                user_id UUID NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                revoked_at TIMESTAMPTZ NULL,
                created_at TIMESTAMPTZ NOT NULL,
                CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id),
                CONSTRAINT refresh_tokens_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES admin_users (id) ON DELETE CASCADE
            );
            """
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS refresh_tokens_user_idx ON refresh_tokens (user_id)"
        )
    )


def downgrade() -> None:
    pass
