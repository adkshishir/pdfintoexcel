"""SQLAlchemy 2.x engine + session.

We use a single sync engine; the FastAPI handlers are thin enough that
async DB doesn't earn its keep, and Celery tasks are sync anyway.

Engine is created lazily so importing this module doesn't force the DB
driver to load — keeps tests / OpenAPI generation runnable without psycopg.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None
_lock = Lock()


def get_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        with _lock:
            if _engine is None:
                _engine = create_engine(
                    get_settings().database_url,
                    pool_pre_ping=True,
                    future=True,
                )
                _SessionLocal = sessionmaker(
                    bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False
                )
    return _engine


def _session_factory() -> sessionmaker[Session]:
    get_engine()
    assert _SessionLocal is not None  # set by get_engine
    return _SessionLocal


def get_db() -> Iterator[Session]:
    """FastAPI dependency."""
    with _session_factory()() as session:
        yield session


@contextmanager
def session_scope() -> Iterator[Session]:
    """For Celery tasks and scripts. Commits on success, rolls back on error."""
    session = _session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
