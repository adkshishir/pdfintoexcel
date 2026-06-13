#!/usr/bin/env bash
# Shared helpers for snap Docker + AppArmor denying `docker stop` / `docker kill`
# (canonical/docker-snap#272). Source from deploy/stop scripts; do not execute directly.

PROJECT="${COMPOSE_PROJECT_NAME:-pdf-excel-converter}"
COMPOSE_PROJECT_FILTER="label=com.docker.compose.project=${PROJECT}"

unstick_container() {
  local cid="$1"
  local pid

  docker update --restart=no "$cid" 2>/dev/null || true

  if docker stop -t 2 "$cid" 2>/dev/null; then
    docker rm -f "$cid" 2>/dev/null || true
    return 0
  fi

  pid="$(docker inspect -f '{{.State.Pid}}' "$cid" 2>/dev/null || echo 0)"
  if [[ "$pid" != "0" && -n "$pid" ]]; then
    kill -TERM "$pid" 2>/dev/null || true
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
      kill -KILL "$pid" 2>/dev/null || true
      sleep 1
    fi
  fi
  docker rm -f "$cid" 2>/dev/null || true
}

unstick_project_containers() {
  local cid status
  local -a extra_filters=()

  if (($# > 0)); then
    for svc in "$@"; do
      extra_filters+=(--filter "label=com.docker.compose.service=${svc}")
    done
  fi

  mapfile -t running < <(docker ps -q --filter "$COMPOSE_PROJECT_FILTER" "${extra_filters[@]}" 2>/dev/null || true)
  for cid in "${running[@]:-}"; do
    [[ -n "$cid" ]] || continue
    unstick_container "$cid"
  done

  for status in created exited; do
    mapfile -t orphans < <(docker ps -aq \
      --filter "$COMPOSE_PROJECT_FILTER" \
      "${extra_filters[@]}" \
      --filter "status=${status}" 2>/dev/null || true)
    for cid in "${orphans[@]:-}"; do
      [[ -n "$cid" ]] || continue
      docker rm -f "$cid" 2>/dev/null || true
    done
  done
}
