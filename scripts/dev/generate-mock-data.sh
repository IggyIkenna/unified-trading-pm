#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# generate-mock-data.sh — Mock Data Seed Orchestration
# Generates mock data for all services in dependency order.
#
# Usage:
#   bash scripts/dev/generate-mock-data.sh                                  # defaults: local, normal, seed=42
#   bash scripts/dev/generate-mock-data.sh --env dev --scenario heavy       # dev env, heavy scenario
#   bash scripts/dev/generate-mock-data.sh --layer 3                        # only run layer 3 (features)
#   bash scripts/dev/generate-mock-data.sh --dry-run                        # show plan without executing
#   bash scripts/dev/generate-mock-data.sh --force                          # continue past failures

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"

# -- Colors ----------------------------------------------------------------
if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
  RED=$(tput setaf 1); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3)
  CYAN=$(tput setaf 6); BOLD=$(tput bold); NC=$(tput sgr0)
else
  RED=""; GREEN=""; YELLOW=""; CYAN=""; BOLD=""; NC=""
fi

# -- Helpers ---------------------------------------------------------------
die()  { echo "${RED}ERROR:${NC} $*" >&2; exit 1; }
info() { echo "${GREEN}>>>${NC} $*"; }
warn() { echo "${YELLOW}WARN:${NC} $*"; }

# -- Defaults --------------------------------------------------------------
ENV="local"
SCENARIO="normal"
SEED=42
TARGET_LAYER=""
FORCE=false
DRY_RUN=false
GENERATE_TICKS=false

# -- Argument parsing ------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)
      shift
      [[ $# -gt 0 ]] || die "--env requires a value: dev or local"
      ENV="$1"
      shift
      ;;
    --scenario)
      shift
      [[ $# -gt 0 ]] || die "--scenario requires a value (e.g. normal, heavy, bust)"
      SCENARIO="$1"
      shift
      ;;
    --seed)
      shift
      [[ $# -gt 0 ]] || die "--seed requires a numeric value"
      SEED="$1"
      shift
      ;;
    --layer)
      shift
      [[ $# -gt 0 ]] || die "--layer requires a layer number (1-7)"
      TARGET_LAYER="$1"
      shift
      ;;
    --force)
      FORCE=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --ticks)
      GENERATE_TICKS=true
      shift
      ;;
    -h|--help)
      echo "Usage: bash scripts/dev/generate-mock-data.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --env ENV          Target environment: dev or local (default: local)"
      echo "  --scenario NAME    Mock scenario: normal, heavy, bust, ... (default: normal)"
      echo "  --seed N           RNG seed for deterministic output (default: 42)"
      echo "  --layer N          Only run a specific layer 1-7 (for debugging)"
      echo "  --force            Continue past layer failures"
      echo "  --dry-run          Show what would run without executing"
      echo "  --ticks            Generate tick-level data in Layer 2 (disabled by default, data is large)"
      echo "  -h, --help         Show this help"
      echo ""
      echo "Dependency layers:"
      echo "  1  instruments-service"
      echo "  2  market-tick-data-service, market-data-processing-service"
      echo "  3  features-delta-one-service, features-volatility-service,"
      echo "     features-onchain-service, features-cross-instrument-service,"
      echo "     features-multi-timeframe-service, features-commodity-service,"
      echo "     features-calendar-service, features-sports-service"
      echo "  4  ml-training-service, ml-inference-service"
      echo "  5  strategy-service, execution-service"
      echo "  6  risk-and-exposure-service, position-balance-monitor-service,"
      echo "     pnl-attribution-service"
      echo "  7  alerting-service, batch-live-reconciliation-service,"
      echo "     trading-agent-service"
      exit 0
      ;;
    *)
      die "Unknown argument: $1 (use --help for usage)"
      ;;
  esac
done

# -- Environment setup -----------------------------------------------------
export DATA_MODE=mock
export CLOUD_PROVIDER="${CLOUD_PROVIDER:-local}"
export DEPLOYMENT_ENV="$ENV"
export MOCK_SCENARIO="$SCENARIO"
export MOCK_SEED="$SEED"
export GENERATE_TICKS

# -- Dependency layers (stable order from runtime-topology.yaml) -----------
LAYER_1=("instruments-service")
LAYER_2=("market-tick-data-service" "market-data-processing-service")
LAYER_3=("features-delta-one-service" "features-volatility-service" "features-onchain-service" "features-cross-instrument-service" "features-multi-timeframe-service" "features-commodity-service" "features-calendar-service" "features-sports-service")
LAYER_4=("ml-training-service" "ml-inference-service")
LAYER_5=("strategy-service" "execution-service")
LAYER_6=("risk-and-exposure-service" "position-balance-monitor-service" "pnl-attribution-service")
LAYER_7=("alerting-service" "batch-live-reconciliation-service" "trading-agent-service")

ALL_LAYERS=(1 2 3 4 5 6 7)

# -- Status tracking via temp directory ------------------------------------
# Background processes (& + wait) run in subshells, so associative arrays
# cannot propagate status back. Use one file per service instead.
STATUS_DIR="$(mktemp -d)"
trap 'rm -rf "$STATUS_DIR"' EXIT

set_status() { echo "$2" > "${STATUS_DIR}/$1"; }
get_status() { cat "${STATUS_DIR}/$1" 2>/dev/null || echo "skip"; }

# -- Run a single service seed script --------------------------------------
run_seed() {
  local service="$1"
  local seed_script="${WORKSPACE_ROOT}/${service}/scripts/seed_mock_data.py"
  local python_bin="${WORKSPACE_ROOT}/${service}/.venv/bin/python"

  if [ ! -f "$seed_script" ]; then
    warn "${service}: no seed script found (scripts/seed_mock_data.py)"
    set_status "$service" "skip"
    return 0
  fi

  if [ ! -f "$python_bin" ]; then
    echo "  ${RED}FAIL${NC} ${service}: .venv/bin/python not found"
    set_status "$service" "fail"
    return 1
  fi

  if [ "$DRY_RUN" = true ]; then
    echo "  ${CYAN}DRY${NC}  ${service}: would run ${python_bin} ${seed_script} --scenario ${SCENARIO} --seed ${SEED} --env ${ENV}"
    set_status "$service" "skip"
    return 0
  fi

  echo "  ${CYAN}RUN${NC}  ${service}..."
  if "$python_bin" "$seed_script" --scenario "$SCENARIO" --seed "$SEED" --env "$ENV" 2>&1; then
    echo "  ${GREEN}OK${NC}   ${service}"
    set_status "$service" "success"
    return 0
  else
    echo "  ${RED}FAIL${NC} ${service}: seed script exited with error"
    set_status "$service" "fail"
    return 1
  fi
}

# -- Run a full layer (parallel within layer) -------------------------------
run_layer() {
  local layer_num="$1"
  shift
  local services=("$@")

  echo ""
  echo "${BOLD}=== Layer ${layer_num} ===${NC}"
  echo "  Services: ${services[*]}"
  echo ""

  # Run upstream validation if the script exists
  local validate_script="${SCRIPT_DIR}/validate-mock-upstream.sh"
  if [ -f "$validate_script" ] && [ "$DRY_RUN" = false ]; then
    for service in "${services[@]}"; do
      info "Validating upstream for ${service}..."
      if ! bash "$validate_script" --service "$service" --env "$ENV" 2>&1; then
        warn "Upstream validation failed for ${service} (continuing anyway)"
      fi
    done
  fi

  # Launch all services in this layer in parallel
  local pids=()
  local pid_to_service=()

  for service in "${services[@]}"; do
    run_seed "$service" &
    local pid=$!
    pids+=("$pid")
    pid_to_service+=("$pid:$service")
  done

  # Wait for all parallel jobs — status is set by run_seed itself, not here
  local layer_failed=false
  for entry in "${pid_to_service[@]}"; do
    local pid="${entry%%:*}"
    local service="${entry#*:}"
    if ! wait "$pid"; then
      # Only mark fail if run_seed didn't already set a status (avoids race condition
      # where wait returns non-zero due to signal but run_seed already wrote "success")
      local current_status
      current_status="$(get_status "$service")"
      if [ "$current_status" != "success" ]; then
        set_status "$service" "fail"
      fi
      layer_failed=true
    fi
  done

  # Layer results
  local success_count=0 fail_count=0 skip_count=0
  for service in "${services[@]}"; do
    case "$(get_status "$service")" in
      success) success_count=$((success_count + 1)) ;;
      fail)    fail_count=$((fail_count + 1)) ;;
      skip)    skip_count=$((skip_count + 1)) ;;
    esac
  done

  echo ""
  echo "  Layer ${layer_num} results: ${GREEN}${success_count} success${NC}, ${YELLOW}${skip_count} skip${NC}, ${RED}${fail_count} fail${NC}"

  if [ "$layer_failed" = true ] && [ "$FORCE" = false ] && [ "$DRY_RUN" = false ]; then
    die "Layer ${layer_num} had failures. Use --force to continue past failures."
  fi
}

# -- Banner ----------------------------------------------------------------
echo ""
echo "${BOLD}=== Mock Data Seed Orchestration ===${NC}"
echo "  Environment:  ${CYAN}${ENV}${NC}"
echo "  Scenario:     ${CYAN}${SCENARIO}${NC}"
echo "  Seed:         ${CYAN}${SEED}${NC}"
echo "  Cloud:        ${CYAN}${CLOUD_PROVIDER}${NC}"
if [ -n "$TARGET_LAYER" ]; then
  echo "  Target layer: ${CYAN}${TARGET_LAYER}${NC}"
fi
if [ "$FORCE" = true ]; then
  echo "  Force:        ${YELLOW}yes (continue past failures)${NC}"
fi
if [ "$DRY_RUN" = true ]; then
  echo "  Dry run:      ${YELLOW}yes (no execution)${NC}"
fi
if [ "$GENERATE_TICKS" = true ]; then
  echo "  Ticks:        ${CYAN}yes (tick-level data after Layer 2)${NC}"
fi

# -- Determine which layers to run ----------------------------------------
if [ -n "$TARGET_LAYER" ]; then
  case "$TARGET_LAYER" in
    1|2|3|4|5|6|7) LAYERS_TO_RUN=("$TARGET_LAYER") ;;
    *) die "Invalid layer: ${TARGET_LAYER} (must be 1-7)" ;;
  esac
else
  LAYERS_TO_RUN=("${ALL_LAYERS[@]}")
fi

# -- Execute layers sequentially -------------------------------------------
for layer_num in "${LAYERS_TO_RUN[@]}"; do
  case "$layer_num" in
    1) run_layer 1 "${LAYER_1[@]}" ;;
    2)
      run_layer 2 "${LAYER_2[@]}"
      # Optional: generate tick-level data after OHLCV (Layer 2 extension)
      if [ "$GENERATE_TICKS" = true ]; then
        echo ""
        echo "${BOLD}=== Layer 2 Extension: Tick Data ===${NC}"
        local_tick_script="${WORKSPACE_ROOT}/market-tick-data-service/scripts/seed_tick_data.py"
        tick_python="${WORKSPACE_ROOT}/market-tick-data-service/.venv/bin/python"
        if [ -f "$local_tick_script" ] && [ -f "$tick_python" ]; then
          if [ "$DRY_RUN" = true ]; then
            echo "  ${CYAN}DRY${NC}  Would generate tick data: ${tick_python} ${local_tick_script} --seed ${SEED} --env ${ENV}"
          else
            echo "  ${CYAN}RUN${NC}  Generating tick-level data for top 5 instruments..."
            if "$tick_python" "$local_tick_script" --seed "$SEED" --env "$ENV" 2>&1; then
              echo "  ${GREEN}OK${NC}   Tick data generated"
            else
              echo "  ${RED}FAIL${NC} Tick data generation failed"
              if [ "$FORCE" = false ]; then
                die "Tick data generation failed. Use --force to continue."
              fi
            fi
          fi
        else
          warn "Tick data script or venv not found — skipping tick generation"
        fi
      fi
      ;;
    3) run_layer 3 "${LAYER_3[@]}" ;;
    4) run_layer 4 "${LAYER_4[@]}" ;;
    5) run_layer 5 "${LAYER_5[@]}" ;;
    6) run_layer 6 "${LAYER_6[@]}" ;;
    7) run_layer 7 "${LAYER_7[@]}" ;;
  esac
done

# -- Summary table ---------------------------------------------------------
echo ""
echo "${BOLD}=== Summary ===${NC}"
printf "  %-42s %s\n" "SERVICE" "STATUS"
printf "  %-42s %s\n" "-------" "------"

total_success=0
total_fail=0
total_skip=0

# Print in layer order for readability
for layer_num in "${LAYERS_TO_RUN[@]}"; do
  layer_services=()
  case "$layer_num" in
    1) layer_services=("${LAYER_1[@]}") ;;
    2) layer_services=("${LAYER_2[@]}") ;;
    3) layer_services=("${LAYER_3[@]}") ;;
    4) layer_services=("${LAYER_4[@]}") ;;
    5) layer_services=("${LAYER_5[@]}") ;;
    6) layer_services=("${LAYER_6[@]}") ;;
    7) layer_services=("${LAYER_7[@]}") ;;
  esac

  for service in "${layer_services[@]}"; do
    status="$(get_status "$service")"
    case "$status" in
      success)
        printf "  %-42s ${GREEN}%s${NC}\n" "${service}" "OK"
        total_success=$((total_success + 1))
        ;;
      fail)
        printf "  %-42s ${RED}%s${NC}\n" "${service}" "FAIL"
        total_fail=$((total_fail + 1))
        ;;
      skip)
        printf "  %-42s ${YELLOW}%s${NC}\n" "${service}" "SKIP"
        total_skip=$((total_skip + 1))
        ;;
    esac
  done
done

echo ""
echo "  Total: ${GREEN}${total_success} success${NC}, ${YELLOW}${total_skip} skip${NC}, ${RED}${total_fail} fail${NC}"
echo ""

# -- Exit code -------------------------------------------------------------
if [ "$total_fail" -gt 0 ]; then
  exit 1
fi
exit 0
