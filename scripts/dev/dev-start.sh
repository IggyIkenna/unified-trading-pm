#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# dev-start.sh — Start UI and/or API dev servers for the unified trading system
#
# Usage:
#   bash scripts/dev/dev-start.sh --stack deployment                         # mock mode, both UI+API
#   bash scripts/dev/dev-start.sh --stack deployment --mode real             # real cloud, both UI+API
#   bash scripts/dev/dev-start.sh --stack deployment --frontend-only         # mock mode, UI only
#   bash scripts/dev/dev-start.sh --stack deployment --backend-only          # mock mode, API only
#   bash scripts/dev/dev-start.sh --all --mode mock --both                   # start everything in mock mode
#   bash scripts/dev/dev-start.sh --ui deployment-ui                         # start just a single UI
#   bash scripts/dev/dev-start.sh --api deployment-api --mode real           # start just an API with real cloud
#   bash scripts/dev/dev-start.sh --list                                     # list available stacks
#
# Flags:
#   --mode mock      (default) CLOUD_MOCK_MODE=true, CLOUD_PROVIDER=local, DISABLE_AUTH=true, MOCK_STATE_MODE=interactive
#   --mode ci        Like mock but deterministic — MOCK_STATE_MODE=deterministic (no persistence, pure seed data)
#   --mode api-real  UI mocked, API reads real cloud (test API against real data)
#   --mode real      CLOUD_MOCK_MODE=false, CLOUD_PROVIDER=gcp (or $CLOUD_PROVIDER), no DISABLE_AUTH
#   --frontend-only  Only start UI dev server(s), skip API
#   --backend-only   Only start API server(s), skip UI
#   --both           (default) Start both UI and API
#   --reset          Remove .local-dev-cache/ before starting (fresh mock state)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
MAPPING_FILE="${SCRIPT_DIR}/ui-api-mapping.json"
PID_DIR="/tmp/unified-dev-pids"
MODE_FILE="/tmp/unified-dev-pids/.dev-mode"

# ── Signal handling ──────────────────────────────────────────────────────────
cleanup() {
  echo ""
  echo "Caught signal — stopping all dev servers..."
  bash "${SCRIPT_DIR}/dev-stop.sh" 2>/dev/null || true
  exit 130
}
trap cleanup INT TERM

# ── Colors ──────────────────────────────────────────────────────────────────
if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
  RED=$(tput setaf 1); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3)
  CYAN=$(tput setaf 6); BOLD=$(tput bold); NC=$(tput sgr0)
else
  RED=""; GREEN=""; YELLOW=""; CYAN=""; BOLD=""; NC=""
fi

# ── Helpers ─────────────────────────────────────────────────────────────────
die()  { echo "${RED}ERROR:${NC} $*" >&2; exit 1; }
info() { echo "${GREEN}>>>${NC} $*"; }
warn() { echo "${YELLOW}WARN:${NC} $*"; }

require_jq() {
  command -v jq >/dev/null 2>&1 || die "jq is required. Install with: brew install jq"
}

ensure_pid_dir() {
  mkdir -p "$PID_DIR"
}

# ── JSON helpers ────────────────────────────────────────────────────────────
get_stack_field() {
  local stack="$1" field="$2"
  jq -r ".stacks[\"${stack}\"].${field} // empty" "$MAPPING_FILE"
}

list_stacks() {
  jq -r '.stacks | keys[]' "$MAPPING_FILE"
}

# ── Environment setup based on --mode ────────────────────────────────────────
# 5 independent mode axes:
#   UI data:     VITE_MOCK_API    (true = mock-api.ts intercepts | false = real API calls)
#   UI auth:     VITE_SKIP_AUTH   (true = skip OAuth | false = real OAuth flow)
#   API data:    CLOUD_MOCK_MODE  (true = mock_data.py returns | false = real cloud storage)
#   API auth:    DISABLE_AUTH     (true = no token checks | false = token required)
#   Mock state:  MOCK_STATE_MODE  (interactive = mutations persist in .local-dev-cache | deterministic = pure seed data)
#
# Preset modes:
#   mock      — all mocked, interactive state (local dev, no credentials needed)
#   ci        — all mocked, deterministic state (CI/test, no persistence, pure seed data)
#   api-real  — UI mocked, API reads real cloud (test API against real data)
#   real      — everything real (staging-like, needs credentials + OAuth client ID)
ENV_MODE="mock"  # default

resolve_env_vars() {
  # Use ``: "${VAR:=default}"`` semantics so callers can override individual
  # axes by pre-exporting ``DEV_UI_MOCK`` / ``DEV_DISABLE_AUTH`` etc. Useful
  # for tier wrappers (e.g. deployment-ui's dev-tiers.sh T2) that need a
  # combination not covered by the four named modes — UI off-mock + auth
  # disabled + cloud reads, for instance.
  case "$ENV_MODE" in
    mock)
      : "${DEV_UI_MOCK:=true}"
      : "${DEV_UI_SKIP_AUTH:=true}"
      : "${DEV_CLOUD_PROVIDER:=local}"
      : "${DEV_CLOUD_MOCK_MODE:=true}"
      : "${DEV_RUNTIME_MODE:=local}"
      : "${DEV_DISABLE_AUTH:=true}"
      : "${DEV_MOCK_STATE_MODE:=interactive}"
      ;;
    ci)
      : "${DEV_UI_MOCK:=true}"
      : "${DEV_UI_SKIP_AUTH:=true}"
      : "${DEV_CLOUD_PROVIDER:=local}"
      : "${DEV_CLOUD_MOCK_MODE:=true}"
      : "${DEV_RUNTIME_MODE:=local}"
      : "${DEV_DISABLE_AUTH:=true}"
      : "${DEV_MOCK_STATE_MODE:=deterministic}"
      ;;
    api-real)
      : "${DEV_UI_MOCK:=true}"
      : "${DEV_UI_SKIP_AUTH:=true}"
      : "${DEV_CLOUD_PROVIDER:=${CLOUD_PROVIDER:-gcp}}"
      : "${DEV_CLOUD_MOCK_MODE:=false}"
      : "${DEV_RUNTIME_MODE:=local}"
      : "${DEV_DISABLE_AUTH:=true}"
      : "${DEV_MOCK_STATE_MODE:=}"
      ;;
    real)
      : "${DEV_UI_MOCK:=false}"
      : "${DEV_UI_SKIP_AUTH:=false}"
      : "${DEV_CLOUD_PROVIDER:=${CLOUD_PROVIDER:-gcp}}"
      : "${DEV_CLOUD_MOCK_MODE:=false}"
      : "${DEV_RUNTIME_MODE:=${RUNTIME_MODE:-production}}"
      : "${DEV_DISABLE_AUTH:=}"
      : "${DEV_MOCK_STATE_MODE:=}"
      ;;
    *)
      die "Unknown --mode: $ENV_MODE (expected mock, ci, api-real, or real)"
      ;;
  esac
  export DEV_UI_MOCK DEV_UI_SKIP_AUTH DEV_CLOUD_PROVIDER DEV_CLOUD_MOCK_MODE
  export DEV_RUNTIME_MODE DEV_DISABLE_AUTH DEV_MOCK_STATE_MODE

  # Persist mode info for dev-status.sh
  mkdir -p "$PID_DIR"
  cat > "${PID_DIR}/.dev-mode" <<MEOF
ENV_MODE=$ENV_MODE
UI_DATA=$([ "$DEV_UI_MOCK" = "true" ] && echo "mock" || echo "live")
UI_AUTH=$([ "$DEV_UI_SKIP_AUTH" = "true" ] && echo "skip" || echo "real")
API_DATA=$([ "$DEV_CLOUD_MOCK_MODE" = "true" ] && echo "mock" || echo "real")
API_AUTH=$([ "$DEV_DISABLE_AUTH" = "true" ] && echo "disabled" || echo "enabled")
MOCK_STATE=$([ -n "$DEV_MOCK_STATE_MODE" ] && echo "$DEV_MOCK_STATE_MODE" || echo "n/a")
COMPONENT_FILTER=$COMPONENT_FILTER
MEOF
}

# ── Emulator env vars ─────────────────────────────────────────────────────
# Only export emulator host vars AFTER confirming the emulator started.
# Exporting a dead emulator host causes SDKs to hang for 600s on connection.
# These are set inside start_gcs_emulator() / start_pubsub_emulator() on success.

# ── GCP Emulator lifecycle ─────────────────────────────────────────────────
start_gcs_emulator() {
  if curl -sf http://localhost:4443 >/dev/null 2>&1; then
    info "GCS emulator (fake-gcs-server) already running on :4443"
    export STORAGE_EMULATOR_HOST="http://localhost:4443"
    return
  fi

  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    # Remove stale container if it exists but is stopped
    docker rm -f fake-gcs 2>/dev/null || true
    info "Starting ${BOLD}fake-gcs-server${NC} (GCS emulator) on :4443..."
    if ! docker run -d --name fake-gcs -p 4443:4443 \
      fsouza/fake-gcs-server -scheme http -port 4443 >/dev/null 2>&1; then
      warn "docker run failed — skipping GCS emulator"
      return
    fi
    echo "docker:fake-gcs" > "${PID_DIR}/fake-gcs.pid"
    # Wait for container to be ready
    local i=0
    while ! curl -sf http://localhost:4443 >/dev/null 2>&1 && [ $i -lt 15 ]; do
      sleep 1
      i=$((i + 1))
    done
    if curl -sf http://localhost:4443 >/dev/null 2>&1; then
      export STORAGE_EMULATOR_HOST="http://localhost:4443"
      info "  fake-gcs-server ready"
    else
      warn "fake-gcs-server failed to start within 15s — GCS-dependent tests may skip"
    fi
  else
    warn "Docker not available — skipping GCS emulator (fake-gcs-server). GCS-dependent SIT tests may skip."
  fi
}

start_pubsub_emulator() {
  # PubSub emulator health check: the emulator doesn't serve HTTP on /, so
  # we check if anything is listening on port 8085.
  if lsof -iTCP:8085 -sTCP:LISTEN -t >/dev/null 2>&1; then
    info "PubSub emulator already running on :8085"
    export PUBSUB_EMULATOR_HOST="localhost:8085"
    return
  fi

  if command -v gcloud >/dev/null 2>&1; then
    info "Starting ${BOLD}PubSub emulator${NC} on :8085..."
    gcloud beta emulators pubsub start --host-port=0.0.0.0:8085 \
      > "${PID_DIR}/pubsub-emulator.log" 2>&1 &
    local pid=$!
    echo "$pid" > "${PID_DIR}/pubsub-emulator.pid"
    # Wait for emulator to bind the port
    local i=0
    while ! lsof -iTCP:8085 -sTCP:LISTEN -t >/dev/null 2>&1 && [ $i -lt 10 ]; do
      sleep 1
      i=$((i + 1))
    done
    if lsof -iTCP:8085 -sTCP:LISTEN -t >/dev/null 2>&1; then
      export PUBSUB_EMULATOR_HOST="localhost:8085"
      info "  PubSub emulator ready (PID $pid)"
    else
      warn "PubSub emulator failed to start within 10s — PubSub-dependent tests may skip"
    fi
  else
    warn "gcloud CLI not available — skipping PubSub emulator. PubSub-dependent SIT tests may skip."
  fi
}

# ── Backend service workers (not in UI/API stacks) ─────────────────────────
# These are standalone services needed for integration tests. They are read
# from the "service_workers" section of ui-api-mapping.json.
start_service_worker() {
  local svc_name="$1" svc_repo="$2" svc_port="$3" svc_module="$4"
  local svc_dir="${WORKSPACE_ROOT}/${svc_repo}"

  if [ ! -d "$svc_dir" ]; then
    warn "Service worker repo not found: ${svc_repo} — skipping"
    return
  fi

  # Use the repo's own .venv if it exists, otherwise fall back to workspace venv
  local python_bin
  if [ -f "$svc_dir/.venv/bin/python" ]; then
    python_bin="$svc_dir/.venv/bin/python"
  elif [ -f "$WORKSPACE_ROOT/.venv-workspace/bin/python" ]; then
    python_bin="$WORKSPACE_ROOT/.venv-workspace/bin/python"
  else
    warn "No Python venv found for ${svc_repo} — skipping"
    return
  fi

  info "Starting ${BOLD}${svc_name}${NC} worker on port ${svc_port}..."
  cd "$svc_dir"

  local env_args=(
    "CLOUD_PROVIDER=${DEV_CLOUD_PROVIDER}"
    "CLOUD_MOCK_MODE=${DEV_CLOUD_MOCK_MODE}"
    "RUNTIME_MODE=${DEV_RUNTIME_MODE}"
    "MODE=live"
    "PORT=${svc_port}"
    "HEALTH_PORT=${svc_port}"
    "API_PORT=${svc_port}"
    "STORAGE_EMULATOR_HOST=${STORAGE_EMULATOR_HOST:-}"
    "PUBSUB_EMULATOR_HOST=${PUBSUB_EMULATOR_HOST:-}"
    "BIGQUERY_EMULATOR_HOST=${BIGQUERY_EMULATOR_HOST:-}"
    "GOOGLE_APPLICATION_CREDENTIALS="
  )
  if [ -n "$DEV_DISABLE_AUTH" ]; then
    env_args+=("DISABLE_AUTH=${DEV_DISABLE_AUTH}")
  fi
  if [ -n "$DEV_MOCK_STATE_MODE" ]; then
    env_args+=("MOCK_STATE_MODE=${DEV_MOCK_STATE_MODE}")
  fi

  # Read extra_args from mapping file (CLI flags the service requires)
  local svc_extra_args
  svc_extra_args=$(jq -r ".service_workers[\"${svc_name}\"].extra_args // empty" "$MAPPING_FILE")

  # shellcheck disable=SC2086 — intentional word-splitting of extra_args
  env "${env_args[@]}" \
    "$python_bin" -m "$svc_module" $svc_extra_args > "${PID_DIR}/${svc_name}.log" 2>&1 &

  local pid=$!
  echo "$pid" > "${PID_DIR}/${svc_name}.pid"
  echo "$svc_port" > "${PID_DIR}/${svc_name}.port"
  info "  ${svc_name} started (PID $pid, port $svc_port)"
}

start_all_service_workers() {
  local worker_count
  worker_count=$(jq -r '[.service_workers // {} | keys[] | select(startswith("$") | not)] | length' "$MAPPING_FILE")

  if [ "$worker_count" -eq 0 ]; then
    info "No service workers defined in ui-api-mapping.json"
    return
  fi

  echo ""
  info "Starting ${BOLD}${worker_count} backend service workers${NC}..."

  local workers
  workers=$(jq -r '.service_workers | keys[] | select(startswith("$") | not)' "$MAPPING_FILE")

  local n=0
  for svc_name in $workers; do
    n=$((n + 1))
    local svc_repo svc_port svc_module
    svc_repo=$(jq -r ".service_workers[\"${svc_name}\"].repo" "$MAPPING_FILE")
    svc_port=$(jq -r ".service_workers[\"${svc_name}\"].port" "$MAPPING_FILE")
    svc_module=$(jq -r ".service_workers[\"${svc_name}\"].module" "$MAPPING_FILE")

    info "[$n/$worker_count] Service worker: $svc_name"
    start_service_worker "$svc_name" "$svc_repo" "$svc_port" "$svc_module"
  done
}

# ── Shared library watch processes ──────────────────────────────────────────
# Starts `npm run dev` (vite build --watch) in each shared UI library so that
# any source change is immediately rebuilt and picked up by consumer Vite HMR.
start_shared_lib_watchers() {
  local libs=(
    "unified-trading-ui-kit"
    "unified-trading-ui-auth"
  )

  for lib in "${libs[@]}"; do
    local lib_dir="${WORKSPACE_ROOT}/${lib}"

    if [ ! -d "$lib_dir" ]; then
      warn "Shared lib not found: $lib — skipping watcher"
      continue
    fi

    if [ ! -f "$lib_dir/package.json" ]; then
      warn "No package.json in $lib — skipping watcher"
      continue
    fi

    # Check if a watcher is already running for this lib
    local pid_file="${PID_DIR}/${lib}-watcher.pid"
    if [ -f "$pid_file" ]; then
      local existing_pid
      existing_pid=$(cat "$pid_file")
      if kill -0 "$existing_pid" 2>/dev/null; then
        info "  ${lib} watcher already running (PID $existing_pid) — skipping"
        continue
      fi
    fi

    info "Starting ${BOLD}${lib}${NC} watcher (hot-reload for consumer UIs)..."
    cd "$lib_dir"

    if [ ! -d "node_modules" ]; then
      warn "node_modules missing in $lib — running npm install"
      npm install --silent
    fi

    npm run dev > "/tmp/unified-dev-pids/${lib}-watcher.log" 2>&1 &
    local pid=$!
    echo "$pid" > "$pid_file"
    info "  ${lib} watcher started (PID $pid)"
  done

  # Give watchers time to complete their first build before UIs start
  # importing from their dist/ directories (ui-kit build ~3s)
  sleep 4
}

# ── Start functions ─────────────────────────────────────────────────────────
start_ui() {
  local ui_repo="$1" ui_port="$2"
  local ui_dir="${WORKSPACE_ROOT}/${ui_repo}"

  if [ ! -d "$ui_dir" ]; then
    warn "UI repo not found: $ui_dir — skipping"
    return
  fi

  if [ ! -f "$ui_dir/package.json" ]; then
    warn "No package.json in $ui_repo — skipping"
    return
  fi

  info "Starting ${BOLD}${ui_repo}${NC} on port ${ui_port}..."
  cd "$ui_dir"

  # Check node_modules
  if [ ! -d "node_modules" ]; then
    warn "node_modules missing in $ui_repo — running npm install"
    npm install --silent
  fi

  local ui_env=()
  [ "$DEV_UI_MOCK" = "true" ] && ui_env+=(VITE_MOCK_API=true)
  [ "$DEV_UI_SKIP_AUTH" = "true" ] && ui_env+=(VITE_SKIP_AUTH=true)
  # Use npx vite directly (not npm run dev) so the PID we capture is the
  # actual vite/node process, not an npm wrapper that exits immediately.
  env ${ui_env[@]+"${ui_env[@]}"} npx vite --port "$ui_port" > "/tmp/unified-dev-pids/${ui_repo}.log" 2>&1 &
  local pid=$!
  echo "$pid" > "${PID_DIR}/${ui_repo}.pid"
  # Also persist the port so dev-stop.sh can kill by port as a fallback
  echo "$ui_port" > "${PID_DIR}/${ui_repo}.port"
  info "  ${ui_repo} started (PID $pid, port $ui_port)"
}

start_api() {
  local api_repo="$1" api_port="$2" api_module="$3"
  local api_dir="${WORKSPACE_ROOT}/${api_repo}"

  if [ ! -d "$api_dir" ]; then
    warn "API repo not found: $api_dir — skipping"
    return
  fi

  info "Starting ${BOLD}${api_repo}${NC} on port ${api_port}..."

  # Use the repo's own .venv if it exists, otherwise fall back to workspace venv
  local python_bin
  if [ -f "$api_dir/.venv/bin/python" ]; then
    python_bin="$api_dir/.venv/bin/python"
  elif [ -f "$WORKSPACE_ROOT/.venv-workspace/bin/python" ]; then
    python_bin="$WORKSPACE_ROOT/.venv-workspace/bin/python"
  else
    die "No Python venv found for $api_repo"
  fi

  cd "$api_dir"

  # Build env vars based on mode
  local env_args=(
    "CLOUD_PROVIDER=${DEV_CLOUD_PROVIDER}"
    "CLOUD_MOCK_MODE=${DEV_CLOUD_MOCK_MODE}"
    "RUNTIME_MODE=${DEV_RUNTIME_MODE}"
    "PORT=${api_port}"
    "GCP_PROJECT_ID=${GCP_PROJECT_ID:-central-element-323112}"
  )
  if [ -n "$DEV_DISABLE_AUTH" ]; then
    env_args+=("DISABLE_AUTH=${DEV_DISABLE_AUTH}")
  fi
  if [ -n "$DEV_MOCK_STATE_MODE" ]; then
    env_args+=("MOCK_STATE_MODE=${DEV_MOCK_STATE_MODE}")
  fi

  env "${env_args[@]}" \
    "$python_bin" -m "$api_module" > "/tmp/unified-dev-pids/${api_repo}.log" 2>&1 &

  local pid=$!
  echo "$pid" > "${PID_DIR}/${api_repo}.pid"
  echo "$api_port" > "${PID_DIR}/${api_repo}.port"
  info "  ${api_repo} started (PID $pid, port $api_port)"
}

start_stack() {
  local stack="$1"

  local ui_repo api_repo ui_port api_port api_module
  ui_repo=$(get_stack_field "$stack" "ui")
  api_repo=$(get_stack_field "$stack" "api")
  ui_port=$(get_stack_field "$stack" "ui_port")
  api_port=$(get_stack_field "$stack" "api_port")
  api_module=$(get_stack_field "$stack" "api_module")

  if [[ "$COMPONENT_FILTER" != "frontend-only" ]]; then
    if [ -n "$api_repo" ] && [ "$api_repo" != "null" ]; then
      start_api "$api_repo" "$api_port" "$api_module"
    fi
  fi

  if [[ "$COMPONENT_FILTER" != "backend-only" ]]; then
    if [ -n "$ui_repo" ] && [ "$ui_repo" != "null" ]; then
      start_ui "$ui_repo" "$ui_port"
    fi
  fi
}

# Find stack name by UI or API repo name
find_stack_for_repo() {
  local repo="$1"
  jq -r --arg repo "$repo" '
    .stacks | to_entries[] |
    select(.value.ui == $repo or .value.api == $repo) |
    .key
  ' "$MAPPING_FILE"
}

# ── Collect URLs for final summary ──────────────────────────────────────────
STARTED_URLS=()

collect_urls_for_stack() {
  local stack="$1"
  local ui_repo api_repo ui_port api_port
  ui_repo=$(get_stack_field "$stack" "ui")
  api_repo=$(get_stack_field "$stack" "api")
  ui_port=$(get_stack_field "$stack" "ui_port")
  api_port=$(get_stack_field "$stack" "api_port")

  if [[ "$COMPONENT_FILTER" != "frontend-only" ]]; then
    if [ -n "$api_repo" ] && [ "$api_repo" != "null" ] && [ -n "$api_port" ]; then
      STARTED_URLS+=("$(printf "  %-28s http://localhost:%s" "${api_repo}:" "$api_port")")
    fi
  fi

  if [[ "$COMPONENT_FILTER" != "backend-only" ]]; then
    if [ -n "$ui_repo" ] && [ "$ui_repo" != "null" ] && [ -n "$ui_port" ]; then
      STARTED_URLS+=("$(printf "  %-28s http://localhost:%s" "${ui_repo}:" "$ui_port")")
    fi
  fi
}

# ── Argument parsing ───────────────────────────────────────────────────────
TARGET_MODE=""
TARGETS=()
COMPONENT_FILTER="both"  # both | frontend-only | backend-only
RESET_CACHE=false
OPEN_BROWSER=false  # use --open to open UI URLs in browser after startup

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      shift
      [[ $# -gt 0 ]] || die "--mode requires a value: mock or real"
      ENV_MODE="$1"
      shift
      ;;
    --frontend-only)
      COMPONENT_FILTER="frontend-only"
      shift
      ;;
    --backend-only)
      COMPONENT_FILTER="backend-only"
      shift
      ;;
    --both)
      COMPONENT_FILTER="both"
      shift
      ;;
    --stack)
      TARGET_MODE="stack"
      shift
      [[ $# -gt 0 ]] || die "--stack requires a stack name"
      TARGETS+=("$1")
      shift
      ;;
    --ui)
      TARGET_MODE="ui"
      shift
      [[ $# -gt 0 ]] || die "--ui requires a repo name"
      TARGETS+=("$1")
      shift
      ;;
    --api)
      TARGET_MODE="api"
      shift
      [[ $# -gt 0 ]] || die "--api requires a repo name"
      TARGETS+=("$1")
      shift
      ;;
    --all)
      TARGET_MODE="all"
      shift
      ;;
    --reset)
      RESET_CACHE=true
      shift
      ;;
    --open)
      OPEN_BROWSER=true
      shift
      ;;
    --no-open)
      OPEN_BROWSER=false
      shift
      ;;
    --list)
      TARGET_MODE="list"
      shift
      ;;
    -h|--help)
      echo "Usage: bash scripts/dev/dev-start.sh [OPTIONS]"
      echo ""
      echo "Target options (pick one or more):"
      echo "  --stack NAME    Start a UI+API stack (e.g. deployment, unified-trading)"
      echo "  --ui NAME       Start just a UI repo (e.g. deployment-ui)"
      echo "  --api NAME      Start just an API repo (e.g. deployment-api)"
      echo "  --all           Start all stacks"
      echo "  --list          List available stacks"
      echo ""
      echo "Mode presets (controls 5 independent axes):"
      echo "  --mode mock      (default) Fully mocked, interactive state — no credentials needed"
      echo "                     UI data: mock  | UI auth: skip  | API data: mock  | API auth: disabled  | Mock state: interactive"
      echo "  --mode ci        Fully mocked, deterministic state — CI/test, no persistence"
      echo "                     UI data: mock  | UI auth: skip  | API data: mock  | API auth: disabled  | Mock state: deterministic"
      echo "  --mode api-real  UI mocked, API reads real cloud — test API against real data"
      echo "                     UI data: mock  | UI auth: skip  | API data: real  | API auth: disabled  | Mock state: n/a"
      echo "  --mode real      Everything real — staging-like, needs credentials + OAuth client ID"
      echo "                     UI data: live  | UI auth: real  | API data: real  | API auth: enabled   | Mock state: n/a"
      echo ""
      echo "Check current mode:  bash scripts/dev/dev-status.sh"
      echo ""
      echo "Cache options:"
      echo "  --reset         Clear .local-dev-cache/ (mock state) before starting"
      echo ""
      echo "Browser options:"
      echo "  --no-open       Don't open UI URLs in browser (default: opens automatically)"
      echo ""
      echo "Component options:"
      echo "  --frontend-only Only start UI dev server(s), skip API"
      echo "  --backend-only  Only start API server(s), skip UI"
      echo "  --both          (default) Start both UI and API"
      echo ""
      echo "  -h, --help      Show this help"
      echo ""
      echo "Examples:"
      echo "  bash scripts/dev/dev-start.sh --stack deployment                     # mock mode, UI + API"
      echo "  bash scripts/dev/dev-start.sh --stack deployment --mode real         # real cloud, UI + API"
      echo "  bash scripts/dev/dev-start.sh --stack deployment --frontend-only     # mock mode, UI only"
      echo "  bash scripts/dev/dev-start.sh --all --backend-only                   # mock mode, all APIs only"
      echo "  bash scripts/dev/dev-start.sh --all --mode real --frontend-only      # real mode, all UIs only"
      echo "  bash scripts/dev/dev-start.sh --ui unified-trading-system-ui --api unified-trading-api"
      exit 0
      ;;
    *)
      die "Unknown argument: $1 (use --help for usage)"
      ;;
  esac
done

[[ -n "$TARGET_MODE" ]] || die "No target specified. Use --stack, --ui, --api, --all, or --list."

# ── Main ────────────────────────────────────────────────────────────────────
require_jq

if [[ "$TARGET_MODE" == "list" ]]; then
  echo "${BOLD}Available stacks:${NC}"
  echo ""
  printf "  %-22s %-24s %-6s %-24s %-6s\n" "STACK" "UI" "PORT" "API" "PORT"
  printf "  %-22s %-24s %-6s %-24s %-6s\n" "-----" "--" "----" "---" "----"
  for stack in $(list_stacks); do
    local_ui=$(get_stack_field "$stack" "ui")
    local_ui_port=$(get_stack_field "$stack" "ui_port")
    local_api=$(get_stack_field "$stack" "api")
    local_api_port=$(get_stack_field "$stack" "api_port")
    [ -z "$local_ui" ] && local_ui="—"
    [ -z "$local_ui_port" ] && local_ui_port="—"
    [ -z "$local_api" ] && local_api="—"
    [ -z "$local_api_port" ] && local_api_port="—"
    printf "  %-22s %-24s %-6s %-24s %-6s\n" "$stack" "$local_ui" "$local_ui_port" "$local_api" "$local_api_port"
  done
  exit 0
fi

# Resolve environment variables based on --mode
resolve_env_vars
ensure_pid_dir

# ── Auto-stop existing services (prevents port-in-use errors) ────────────
# Always run dev-stop before starting: stops PID-tracked services and sweeps
# orphaned processes on known dev ports (e.g. from manual npm run dev).
STOP_SCRIPT="${SCRIPT_DIR}/dev-stop.sh"
if [ -f "$STOP_SCRIPT" ]; then
  info "Stopping any existing dev servers..."
  bash "$STOP_SCRIPT" 2>/dev/null || true
  sleep 1
fi
ensure_pid_dir

# Clear mock state cache if --reset
if [ "$RESET_CACHE" = true ]; then
  CACHE_DIR="${WORKSPACE_ROOT}/.local-dev-cache"
  if [ -d "$CACHE_DIR" ]; then
    rm -rf "$CACHE_DIR"
    info "Cleared mock state cache: ${CACHE_DIR}"
  else
    info "No mock state cache to clear."
  fi
fi

# Mode already persisted by resolve_env_vars() above

# ── Start GCP emulators (must be ready before any service) ─────────────────
# Emulators are started for mock/ci modes so that services and SIT tests that
# depend on GCS/PubSub don't skip due to missing backends.
if [[ "$ENV_MODE" == "mock" || "$ENV_MODE" == "ci" ]]; then
  if [[ "$COMPONENT_FILTER" != "frontend-only" ]]; then
    echo ""
    info "Starting GCP emulators for ${ENV_MODE} mode..."
    start_gcs_emulator
    start_pubsub_emulator
  fi
fi

echo ""
echo "${BOLD}=== Unified Trading System — Dev Mode ===${NC}"
if [[ "$ENV_MODE" == "mock" || "$ENV_MODE" == "ci" ]]; then
  echo "  Mode:           ${CYAN}${ENV_MODE}${NC}"
  echo "  CLOUD_PROVIDER=local, CLOUD_MOCK_MODE=true, DISABLE_AUTH=true, MOCK_STATE_MODE=${DEV_MOCK_STATE_MODE}"
  echo "  Emulators:      GCS=:4443, PubSub=:8085, BQ=:9050 (env vars exported)"
else
  echo "  Mode:           ${CYAN}${ENV_MODE}${NC}"
  echo "  CLOUD_PROVIDER=${DEV_CLOUD_PROVIDER}, CLOUD_MOCK_MODE=false, DISABLE_AUTH not set"
fi
echo "  Components:     ${CYAN}${COMPONENT_FILTER}${NC}"
echo ""

# Start shared library watchers before any consumer UI so their dist/ is
# ready and future saves hot-reload into all running Vite dev servers.
if [[ "$COMPONENT_FILTER" != "backend-only" ]]; then
  start_shared_lib_watchers
fi

spawn_n=0
spawn_total=0

case "$TARGET_MODE" in
  stack)
    spawn_total=${#TARGETS[@]}
    for target in "${TARGETS[@]}"; do
      spawn_n=$((spawn_n + 1))
      info "[$spawn_n/$spawn_total] Starting stack: $target"
      start_stack "$target"
      collect_urls_for_stack "$target"
      [ "$spawn_n" -lt "$spawn_total" ] && sleep 1
    done
    ;;
  ui)
    spawn_total=${#TARGETS[@]}
    for target in "${TARGETS[@]}"; do
      spawn_n=$((spawn_n + 1))
      stack=$(find_stack_for_repo "$target")
      if [ -z "$stack" ]; then
        die "No stack found for UI: $target"
      fi
      ui_port=$(get_stack_field "$stack" "ui_port")
      info "[$spawn_n/$spawn_total] Starting UI: $target"
      start_ui "$target" "$ui_port"
      STARTED_URLS+=("$(printf "  %-28s http://localhost:%s" "${target}:" "$ui_port")")
      [ "$spawn_n" -lt "$spawn_total" ] && sleep 1
    done
    ;;
  api)
    spawn_total=${#TARGETS[@]}
    for target in "${TARGETS[@]}"; do
      spawn_n=$((spawn_n + 1))
      stack=$(find_stack_for_repo "$target")
      if [ -z "$stack" ]; then
        die "No stack found for API: $target"
      fi
      api_port=$(get_stack_field "$stack" "api_port")
      api_module=$(get_stack_field "$stack" "api_module")
      info "[$spawn_n/$spawn_total] Starting API: $target"
      start_api "$target" "$api_port" "$api_module"
      STARTED_URLS+=("$(printf "  %-28s http://localhost:%s" "${target}:" "$api_port")")
      [ "$spawn_n" -lt "$spawn_total" ] && sleep 1
    done
    ;;
  all)
    all_stacks=($(list_stacks))
    spawn_total=${#all_stacks[@]}
    for stack in "${all_stacks[@]}"; do
      spawn_n=$((spawn_n + 1))
      info "[$spawn_n/$spawn_total] Starting stack: $stack"
      start_stack "$stack"
      collect_urls_for_stack "$stack"
      [ "$spawn_n" -lt "$spawn_total" ] && sleep 1
    done
    ;;
esac

# ── Start backend service workers (for --all or --backend-only) ────────────
# Service workers are standalone services (execution, risk, alerting, etc.)
# that don't have their own UI but are needed for SIT integration tests.
if [[ "$TARGET_MODE" == "all" ]] && [[ "$COMPONENT_FILTER" != "frontend-only" ]]; then
  start_all_service_workers
fi

echo ""

# Print URLs summary
if [ ${#STARTED_URLS[@]} -gt 0 ]; then
  echo "${BOLD}URLs:${NC}"
  for url_line in "${STARTED_URLS[@]}"; do
    echo "$url_line"
  done
  echo ""
fi

# Open UI URLs in browser
if [ "$OPEN_BROWSER" = true ] && [ ${#STARTED_URLS[@]} -gt 0 ]; then
  # Collect UI ports (skip API ports)
  UI_URLS=()
  if [[ "$COMPONENT_FILTER" != "backend-only" ]]; then
    case "$TARGET_MODE" in
      all)
        for stack in $(list_stacks); do
          local_ui_port=$(get_stack_field "$stack" "ui_port")
          local_ui_repo=$(get_stack_field "$stack" "ui")
          if [ -n "$local_ui_repo" ] && [ "$local_ui_repo" != "null" ] && [ -n "$local_ui_port" ]; then
            UI_URLS+=("http://localhost:${local_ui_port}")
          fi
        done
        ;;
      stack)
        for target in "${TARGETS[@]}"; do
          local_ui_port=$(get_stack_field "$target" "ui_port")
          local_ui_repo=$(get_stack_field "$target" "ui")
          if [ -n "$local_ui_repo" ] && [ "$local_ui_repo" != "null" ] && [ -n "$local_ui_port" ]; then
            UI_URLS+=("http://localhost:${local_ui_port}")
          fi
        done
        ;;
      ui)
        for target in "${TARGETS[@]}"; do
          local_stack=$(find_stack_for_repo "$target")
          if [ -n "$local_stack" ]; then
            local_ui_port=$(get_stack_field "$local_stack" "ui_port")
            UI_URLS+=("http://localhost:${local_ui_port}")
          fi
        done
        ;;
    esac
  fi

  if [ ${#UI_URLS[@]} -gt 0 ]; then
    # Wait briefly for vite to bind ports
    sleep 2
    info "Opening ${#UI_URLS[@]} UI(s) in browser..."
    open_cmd=""
    case "$(uname -s)" in
      Darwin) open_cmd="open" ;;
      Linux)  open_cmd="xdg-open" ;;
    esac
    if [ -n "$open_cmd" ]; then
      for url in "${UI_URLS[@]}"; do
        "$open_cmd" "$url" 2>/dev/null || true
        sleep 0.5  # stagger browser tabs to avoid memory spike
      done
    else
      warn "Could not detect browser open command — open URLs manually"
    fi
  fi
fi

if [[ "$COMPONENT_FILTER" != "backend-only" ]]; then
  echo "${BOLD}Shared lib watchers (hot-reload):${NC}"
  for lib in "unified-trading-ui-kit" "unified-trading-ui-auth"; do
    pid_file="${PID_DIR}/${lib}-watcher.pid"
    if [ -f "$pid_file" ]; then
      watcher_pid=$(cat "$pid_file")
      printf "  %-28s PID %s  (log: /tmp/unified-dev-pids/%s-watcher.log)\n" \
        "${lib}:" "$watcher_pid" "$lib"
    fi
  done
  echo ""
fi

# Print emulator status
if [[ "$ENV_MODE" == "mock" || "$ENV_MODE" == "ci" ]] && [[ "$COMPONENT_FILTER" != "frontend-only" ]]; then
  echo "${BOLD}GCP Emulators:${NC}"
  if [ -f "${PID_DIR}/fake-gcs.pid" ]; then
    printf "  %-28s %s\n" "fake-gcs-server (GCS):" "http://localhost:4443"
  else
    printf "  %-28s %s\n" "fake-gcs-server (GCS):" "NOT RUNNING (docker unavailable?)"
  fi
  if [ -f "${PID_DIR}/pubsub-emulator.pid" ]; then
    printf "  %-28s %s\n" "PubSub emulator:" "localhost:8085"
  else
    printf "  %-28s %s\n" "PubSub emulator:" "NOT RUNNING (gcloud unavailable?)"
  fi
  echo ""
fi

# Print service worker status
if [[ "$TARGET_MODE" == "all" ]] && [[ "$COMPONENT_FILTER" != "frontend-only" ]]; then
  local_worker_count=$(jq -r '[.service_workers // {} | keys[] | select(startswith("$") | not)] | length' "$MAPPING_FILE")
  if [ "$local_worker_count" -gt 0 ]; then
    echo "${BOLD}Service workers:${NC}"
    for svc_name in $(jq -r '.service_workers | keys[] | select(startswith("$") | not)' "$MAPPING_FILE"); do
      pid_file="${PID_DIR}/${svc_name}.pid"
      if [ -f "$pid_file" ]; then
        local_pid=$(cat "$pid_file")
        local_port=$(cat "${PID_DIR}/${svc_name}.port" 2>/dev/null || echo "?")
        printf "  %-34s PID %-8s port %s\n" "${svc_name}:" "$local_pid" "$local_port"
      else
        printf "  %-34s %s\n" "${svc_name}:" "SKIPPED (repo not found)"
      fi
    done
    echo ""
  fi
fi

info "Dev servers started. Logs in /tmp/unified-dev-pids/*.log"
info "Stop with: bash scripts/dev/dev-stop.sh"
info "Status:    bash scripts/dev/dev-status.sh"
echo ""
