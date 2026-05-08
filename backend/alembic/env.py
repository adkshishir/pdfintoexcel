"""Alembic env. Reads DB URL from app settings (i.e. from env vars), so the
container doesn't need a separate alembic config.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

from app.config import get_settings
from app.models.database import Base
import app.models.blog_post  # noqa: F401 — register model with Base.metadata
import app.models.job  # noqa: F401 — register model with Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    # Backend, worker, and beat all run `alembic upgrade head` on boot. Serialize
    # so two processes never race on CREATE TABLE (PostgreSQL composite type name).
    _LOCK_KEY_1 = 715_914_251
    _LOCK_KEY_2 = 1
    with connectable.connect() as connection:
        dialect = connection.dialect.name
        if dialect == "postgresql":
            connection.execute(text(f"SELECT pg_advisory_lock({_LOCK_KEY_1}, {_LOCK_KEY_2})"))
        try:
            context.configure(
                connection=connection, target_metadata=target_metadata, compare_type=True
            )
            with context.begin_transaction():
                context.run_migrations()
        finally:
            if dialect == "postgresql":
                connection.execute(text(f"SELECT pg_advisory_unlock({_LOCK_KEY_1}, {_LOCK_KEY_2})"))


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
