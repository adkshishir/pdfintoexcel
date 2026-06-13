#!/usr/bin/env bash
# Restart the production stack. Run from repo root:
#   sudo bash infrastructure/prod-restart.sh
#
# snap Docker cannot stop containers normally; we force-stop the project, then
# recreate it with `up -d` (equivalent to a full restart).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=infrastructure/lib/docker-unstick.sh
source "$ROOT/infrastructure/lib/docker-unstick.sh"
# shellcheck source=infrastructure/lib/compose-prod.sh
source "$ROOT/infrastructure/lib/compose-prod.sh"

unstick_project_containers "$@"
compose_prod up -d "$@"
