#!/usr/bin/env bash
# Build the production `docker compose` command. Source from prod lifecycle scripts.

compose_prod() {
  local compose=(docker compose -f infrastructure/docker-compose.yml)
  if [[ -f infrastructure/.env.prod ]]; then
    compose+=(--env-file infrastructure/.env.prod)
  fi
  if [[ -f infrastructure/compose.host-ports.env ]]; then
    compose+=(--env-file infrastructure/compose.host-ports.env)
  fi
  compose+=(-f infrastructure/docker-compose.prod.yml)
  "${compose[@]}" "$@"
}
