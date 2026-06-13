#!/usr/bin/env bash
# Stop the production stack. Run from repo root:
#   sudo bash infrastructure/prod-down.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=infrastructure/lib/docker-unstick.sh
source "$ROOT/infrastructure/lib/docker-unstick.sh"
# shellcheck source=infrastructure/lib/compose-prod.sh
source "$ROOT/infrastructure/lib/compose-prod.sh"

unstick_project_containers
compose_prod down "$@"
