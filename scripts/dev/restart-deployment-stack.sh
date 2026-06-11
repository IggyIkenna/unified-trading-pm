#!/usr/bin/env bash
# restart-deployment-stack.sh — local SSOT for the deployment-api + deployment-ui stack.
#
# Tier-2 startup (`dev-tiers.sh --tier 2 --real`) wires up the shared
# domain APIs + downstream services + Next.js UI. The legacy
# deployment-api (FastAPI on port 8004) + deployment-ui (Vite SPA on
# port 5183) are bolted onto tier-2 there, but during day-to-day
# data-status / deployment-flow work you usually only want to bounce
# THIS pair without touching the rest of the fleet.
#
# This script is the SSOT for that. It:
#   * Stops any process holding 8004 / 5183 (sweeps orphans).
#   * Starts deployment-api (FastAPI uvicorn) on port 8004.
#   * Starts deployment-ui (Vite dev) on port 5183.
#   * ALWAYS uses real cloud mode (CLOUD_PROVIDER=gcp, CLOUD_MOCK_MODE=false)
#     — no mock flag. The local deployment-api reads the same Cloud Run
#     rollup bucket the shared service does, so the in-region slicer
#     fast-path lights up locally too.
#
# Hardcoded ports (NOT configurable — UI's CloudProviderContext checks
# window.location.hostname to flip between localhost:8004 and the same-
# origin path on Cloud Run; if you change the API port the UI's relative
# /api proxy stops resolving and every widget shows "Failed to load").
#
# Usage:
#   bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh           # both
#   bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --api      # just deployment-api on 8004
#   bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --ui       # just deployment-ui on 5183
#   bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --stop     # stop both, don't restart

set -euo pipefail

API_PORT=8004
UI_PORT=5183

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="${UNIFIED_TRADING_WORKSPACE_ROOT:-$(cd "${SCRIPT_DIR}/../../.." && pwd)}"
API_DIR="${WORKSPACE_ROOT}/deployment-api"
UI_DIR="${WORKSPACE_ROOT}/deployment-ui"

WHAT="all"
STOP_ONLY=false

while [ $# -gt 0 ]; do
  case "$1" in
    --api)  WHAT="api"; shift ;;
    --ui)   WHAT="ui"; shift ;;
    --all|"") WHAT="all"; shift || true ;;
    --stop) STOP_ONLY=true; shift ;;
    -h|--help)
      sed -n '1,/^set -euo/p' "$0" | sed 's/^# *//; /^!/d; q' >&2
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

PIDS_DIR="${TMPDIR:-/tmp}/deployment-stack-pids"
mkdir -p "$PIDS_DIR"

stop_port() {
  local port="$1" name="$2"
  local pids
  pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    echo "  stopping ${name} (port ${port}, pids ${pids})"
    kill $pids 2>/dev/null || true
    sleep 0.5
    pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
    if [ -n "$pids" ]; then
      echo "  force-killing ${name} (still holding ${port})"
      kill -9 $pids 2>/dev/null || true
    fi
  fi
  rm -f "${PIDS_DIR}/${name}.pid"
}

start_api() {
  if [ ! -d "$API_DIR" ]; then
    echo "ERROR: deployment-api dir not found at $API_DIR" >&2
    exit 1
  fi
  cd "$API_DIR"
  if [ ! -d ".venv" ]; then
    echo "ERROR: deployment-api .venv missing — run 'cd deployment-api && uv venv && uv pip install -e .' first" >&2
    exit 1
  fi
  echo "==> Starting deployment-api on :${API_PORT} (real mode, real cloud, 4 workers)"
  local logfile="${PIDS_DIR}/deployment-api.log"
  # 4 workers — the Data Status tab fires 5 concurrent requests on open
  # (manifest + config/region + expected-start-dates + fixtures + checklist).
  # Single-worker uvicorn serialises them behind the heaviest one (the
  # transpacific GCS rollup fetch, 8-10s cold) and you get a 24s wallclock
  # even though no individual endpoint is slow. Each worker has its own
  # in-process _ROLLUP_CACHE; the 30-min TTL means they all warm up after
  # one cold hit each.
  # GCP_PROJECT_ID is required: the Repo-CI tab resolves the GH_PAT secret via
  # get_secret_client() -> get_project_id(), which raises if the project id is
  # unset (every other tab reads GCS via ADC and doesn't need it). Honour an
  # already-exported value; default to the canonical prod project otherwise.
  env CLOUD_PROVIDER=gcp CLOUD_MOCK_MODE=false DISABLE_AUTH=true \
      ENVIRONMENT=development DEPLOYMENT_ENV=prod \
      GCP_PROJECT_ID="${GCP_PROJECT_ID:-central-element-323112}" \
    nohup .venv/bin/python -m uvicorn deployment_api.main:app \
      --host 0.0.0.0 --port "$API_PORT" --workers 4 \
    > "$logfile" 2>&1 &
  echo $! > "${PIDS_DIR}/deployment-api.pid"
  echo "  pid $(cat "${PIDS_DIR}/deployment-api.pid") — log $logfile"
}

start_ui() {
  if [ ! -d "$UI_DIR" ]; then
    echo "ERROR: deployment-ui dir not found at $UI_DIR" >&2
    exit 1
  fi
  cd "$UI_DIR"
  if [ ! -d "node_modules" ]; then
    echo "  deployment-ui node_modules missing — running 'npm install' first"
    npm install --silent
  fi
  echo "==> Starting deployment-ui on :${UI_PORT} (Vite dev)"
  local logfile="${PIDS_DIR}/deployment-ui.log"
  nohup npm run dev > "$logfile" 2>&1 &
  echo $! > "${PIDS_DIR}/deployment-ui.pid"
  echo "  pid $(cat "${PIDS_DIR}/deployment-ui.pid") — log $logfile"
}

wait_for_port() {
  local port="$1" name="$2" max_wait=60 elapsed=0
  while [ "$elapsed" -lt "$max_wait" ]; do
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}/" 2>/dev/null | grep -qE "^[2345]"; then
      echo "  ${name} ready on :${port}"
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  echo "  ⚠️  ${name} did not respond on :${port} within ${max_wait}s — check ${PIDS_DIR}/${name}.log"
  return 1
}

# Stop phase
case "$WHAT" in
  all) stop_port "$API_PORT" "deployment-api"; stop_port "$UI_PORT" "deployment-ui" ;;
  api) stop_port "$API_PORT" "deployment-api" ;;
  ui)  stop_port "$UI_PORT"  "deployment-ui" ;;
esac

if $STOP_ONLY; then
  echo "Stop complete."
  exit 0
fi

# Start phase
case "$WHAT" in
  all) start_api; start_ui ;;
  api) start_api ;;
  ui)  start_ui ;;
esac

# Wait phase
case "$WHAT" in
  all) wait_for_port "$API_PORT" "deployment-api" || true; wait_for_port "$UI_PORT" "deployment-ui" || true ;;
  api) wait_for_port "$API_PORT" "deployment-api" || true ;;
  ui)  wait_for_port "$UI_PORT"  "deployment-ui" || true ;;
esac

cat <<EOF

═══════════════════════════════════════════════════════════
  Deployment stack ($WHAT) restarted
═══════════════════════════════════════════════════════════
  API:  http://localhost:${API_PORT}/api/health
  UI:   http://localhost:${UI_PORT}/
  Logs: ${PIDS_DIR}/

  Stop with: bash $0 --stop
EOF
