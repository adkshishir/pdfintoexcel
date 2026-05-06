#!/usr/bin/env sh
# Backend container entrypoint.
# Runs Alembic migrations to head, then execs the given command (uvicorn by default).
set -eu

echo "[entrypoint] running alembic upgrade head"
alembic upgrade head

echo "[entrypoint] starting: $*"
exec "$@"
