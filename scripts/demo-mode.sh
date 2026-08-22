#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# demo-mode.sh — Single-command stakeholder demo environment
# Starts all services (mock mode) + all UIs (VITE_MOCK_API=true)
# No credentials required.
#
# Usage:
#   bash scripts/demo-mode.sh           # start services only
#   bash scripts/demo-mode.sh --seed    # start + seed fixture data
#   bash scripts/demo-mode.sh --open-browser  # start + open browser
#   bash scripts/demo-mode.sh --seed --open-browser

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/../docker/docker-compose.mock.yml"

SEED=false
OPEN_BROWSER=false
GCP_EMULATORS=false

# Parse args
for arg in "$@"; do
  case $arg in
    --seed) SEED=true ;;
    --open-browser) OPEN_BROWSER=true ;;
    --gcp-emulators) GCP_EMULATORS=true ;;
    *) echo "Unknown arg: $arg"; exit 1 ;;
  esac
done

echo "=== Unified Trading System — Demo Mode ==="
echo "  CLOUD_PROVIDER=local, CLOUD_MOCK_MODE=true"
echo "  No credentials required."
echo ""

# Build compose args
PROFILES="services"
if [[ "$GCP_EMULATORS" == "true" ]]; then
  PROFILES="${PROFILES},gcp-emulators"
fi

echo "Starting services..."
docker compose \
  -f "$COMPOSE_FILE" \
  --profile "$PROFILES" \
  up -d --build

echo "Waiting for services to be healthy..."
sleep 5

if [[ "$SEED" == "true" ]]; then
  echo "Seeding fixture data..."
  if [[ -f "${WORKSPACE_ROOT}/unified-trading-pm/scripts/dev/seed_fixtures.py" ]]; then
    cd "${WORKSPACE_ROOT}" && python unified-trading-pm/scripts/dev/seed_fixtures.py
  else
    echo "  (seed script not yet available — see mock_data_dev_project plan)"
  fi
fi

echo ""
echo "=== Demo environment ready ==="
echo "  market-data-service: http://localhost:8001"
echo "  execution-service:   http://localhost:8002"
echo "  (unified-trading-api is not in this compose file — run locally on :8030 when needed; see scripts/dev/ui-api-mapping.json)"
echo ""
echo "Stop with: docker compose -f ${COMPOSE_FILE} down"

if [[ "$OPEN_BROWSER" == "true" ]]; then
  sleep 2
  open "http://localhost:8001" 2>/dev/null || xdg-open "http://localhost:8001" 2>/dev/null || true
fi
