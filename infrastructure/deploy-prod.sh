#!/usr/bin/env bash
# Production deploy helper. Run from repo root:
#   sudo bash infrastructure/deploy-prod.sh
#
# Work around snap Docker + AppArmor denying container stop/kill (see
# canonical/docker-snap#272): force-stop project containers from the host so
# Compose can recreate them cleanly.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=infrastructure/lib/docker-unstick.sh
source "$ROOT/infrastructure/lib/docker-unstick.sh"

unstick_project_containers

make prod-up
make prod-migrate
