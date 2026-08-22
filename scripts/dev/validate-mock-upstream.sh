#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# validate-mock-upstream.sh — Validate that upstream mock data exists for a service before seeding.
#
# Checks the .local-dev-cache/mock-seed/ directory for .seed-complete markers
# from each upstream dependency, ensuring data flows are satisfied in order.
#
# Usage:
#   bash scripts/dev/validate-mock-upstream.sh --service <service-name>
#   bash scripts/dev/validate-mock-upstream.sh --service <service-name> --env dev
#   bash scripts/dev/validate-mock-upstream.sh --service all
#   bash scripts/dev/validate-mock-upstream.sh --service all --verbose
#
# Options:
#   --service <name|all>   Service to validate (or "all" for full matrix)
#   --env <local|dev>      Environment to check (default: local)
#   --verbose              Show full paths being checked
#   --help                 Show this help
#
# Exit codes:
#   0  All upstream data present
#   1  Missing upstream data (prints missing list)

set -euo pipefail

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"

# ---------------------------------------------------------------------------
# Colors (only if stdout is a terminal)
# ---------------------------------------------------------------------------
if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
  GREEN=$(tput setaf 2); RED=$(tput setaf 1); YELLOW=$(tput setaf 3)
  CYAN=$(tput setaf 6); BOLD=$(tput bold); NC=$(tput sgr0)
else
  GREEN=""; RED=""; YELLOW=""; CYAN=""; BOLD=""; NC=""
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
die()  { echo "${RED}ERROR:${NC} $*" >&2; exit 1; }
info() { echo "${GREEN}>>>${NC} $*"; }
warn() { echo "${YELLOW}WARN:${NC} $*"; }

# ---------------------------------------------------------------------------
# Upstream dependency map (derived from runtime-topology.yaml service_flows)
# ---------------------------------------------------------------------------
# Key = service, Value = space-separated list of upstream services
# Empty string = L1 root (no upstream dependencies)

declare -A UPSTREAM_DEPS
UPSTREAM_DEPS[instruments-service]=""
UPSTREAM_DEPS[market-tick-data-service]="instruments-service"
UPSTREAM_DEPS[market-data-processing-service]="instruments-service market-tick-data-service"
UPSTREAM_DEPS[features-delta-one-service]="market-data-processing-service"
UPSTREAM_DEPS[features-volatility-service]="market-data-processing-service"
UPSTREAM_DEPS[features-onchain-service]="market-data-processing-service"
UPSTREAM_DEPS[features-cross-instrument-service]="market-data-processing-service"
UPSTREAM_DEPS[features-multi-timeframe-service]="market-data-processing-service"
UPSTREAM_DEPS[features-commodity-service]="market-data-processing-service"
UPSTREAM_DEPS[features-calendar-service]="market-data-processing-service"
UPSTREAM_DEPS[features-sports-service]="market-data-processing-service"
UPSTREAM_DEPS[ml-training-service]="features-delta-one-service features-volatility-service"
UPSTREAM_DEPS[ml-inference-service]="ml-training-service features-delta-one-service"
UPSTREAM_DEPS[strategy-service]="features-delta-one-service features-volatility-service ml-inference-service"
UPSTREAM_DEPS[execution-service]="strategy-service"
UPSTREAM_DEPS[risk-and-exposure-service]="execution-service"
UPSTREAM_DEPS[position-balance-monitor-service]="execution-service"
UPSTREAM_DEPS[pnl-attribution-service]="execution-service risk-and-exposure-service"
UPSTREAM_DEPS[alerting-service]="risk-and-exposure-service"
UPSTREAM_DEPS[batch-live-reconciliation-service]="execution-service position-balance-monitor-service"
UPSTREAM_DEPS[trading-agent-service]="strategy-service"

# Sorted list for consistent output (topological order)
ALL_SERVICES=(
  instruments-service
  market-tick-data-service
  market-data-processing-service
  features-delta-one-service
  features-volatility-service
  features-onchain-service
  features-cross-instrument-service
  features-multi-timeframe-service
  features-commodity-service
  features-calendar-service
  features-sports-service
  ml-training-service
  ml-inference-service
  strategy-service
  execution-service
  risk-and-exposure-service
  position-balance-monitor-service
  pnl-attribution-service
  alerting-service
  batch-live-reconciliation-service
  trading-agent-service
)

# ---------------------------------------------------------------------------
# Marker path resolution
# ---------------------------------------------------------------------------
get_marker_path_local() {
  local service="$1"
  echo "${WORKSPACE_ROOT}/.local-dev-cache/mock-seed/${service}/.seed-complete"
}

check_marker_local() {
  local marker
  marker="$(get_marker_path_local "$1")"
  [ -f "$marker" ]
}

check_marker_dev_gcs() {
  local service="$1"
  local bucket="${GCS_BUCKET:-unified-trading-dev-mock-seed}"
  local gcs_path="gs://${bucket}/mock-seed/${service}/.seed-complete"

  if ! command -v gsutil >/dev/null 2>&1; then
    warn "gsutil not available — cannot check GCS marker for ${service}"
    return 1
  fi

  gsutil -q stat "$gcs_path" 2>/dev/null
}

# ---------------------------------------------------------------------------
# Validate a single service
# ---------------------------------------------------------------------------
validate_service() {
  local service="$1"
  local env="$2"
  local verbose="$3"
  local missing=()
  local deps="${UPSTREAM_DEPS[$service]:-}"

  # If service is not in the dependency map, error
  if [[ -z "${UPSTREAM_DEPS[$service]+exists}" ]]; then
    die "Unknown service: ${service}. Use --service all to see valid services."
  fi

  # L1 root — no upstream dependencies
  if [[ -z "$deps" ]]; then
    info "${BOLD}${service}${NC}: L1 root — no upstream dependencies"
    return 0
  fi

  local has_failure=false

  for upstream in $deps; do
    local marker_path
    local found=false

    if [[ "$env" == "local" ]]; then
      marker_path="$(get_marker_path_local "$upstream")"
      if check_marker_local "$upstream"; then
        found=true
      fi
    elif [[ "$env" == "dev" ]]; then
      local bucket="${GCS_BUCKET:-unified-trading-dev-mock-seed}"
      marker_path="gs://${bucket}/mock-seed/${upstream}/.seed-complete"
      if check_marker_dev_gcs "$upstream"; then
        found=true
      fi
    fi

    if $found; then
      echo "  ${GREEN}OK${NC}  ${upstream}"
      if [[ "$verbose" == "true" ]]; then
        echo "       ${CYAN}${marker_path}${NC}"
      fi
    else
      echo "  ${RED}MISSING${NC}  ${upstream}"
      if [[ "$verbose" == "true" ]]; then
        echo "       ${CYAN}${marker_path}${NC}"
      fi
      missing+=("$upstream")
      has_failure=true
    fi
  done

  if $has_failure; then
    return 1
  fi
  return 0
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
SERVICE=""
ENV="local"
VERBOSE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --service)
      [[ $# -ge 2 ]] || die "--service requires an argument"
      SERVICE="$2"
      shift 2
      ;;
    --env)
      [[ $# -ge 2 ]] || die "--env requires an argument"
      ENV="$2"
      shift 2
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --help|-h)
      echo "Usage: bash scripts/dev/validate-mock-upstream.sh --service <name|all> [--env local|dev] [--verbose]"
      echo ""
      echo "Options:"
      echo "  --service <name>   Service name to validate (or 'all' for full matrix)"
      echo "  --env <local|dev>  Environment: local (.local-dev-cache) or dev (GCS)"
      echo "  --verbose          Show full marker paths"
      echo ""
      echo "Available services:"
      for svc in "${ALL_SERVICES[@]}"; do
        local_deps="${UPSTREAM_DEPS[$svc]:-}"
        if [[ -z "$local_deps" ]]; then
          echo "  ${svc}  (L1 root)"
        else
          echo "  ${svc}  <- ${local_deps}"
        fi
      done
      exit 0
      ;;
    *)
      die "Unknown argument: $1. Use --help for usage."
      ;;
  esac
done

[[ -n "$SERVICE" ]] || die "Missing --service argument. Use --help for usage."
[[ "$ENV" == "local" || "$ENV" == "dev" ]] || die "--env must be 'local' or 'dev'"

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
echo "${BOLD}Upstream Mock Data Validator${NC}"
echo "Environment: ${CYAN}${ENV}${NC}"
echo ""

if [[ "$SERVICE" == "all" ]]; then
  # Full matrix mode
  total=0
  ready=0
  blocked=0
  roots=0

  for svc in "${ALL_SERVICES[@]}"; do
    total=$((total + 1))
    deps="${UPSTREAM_DEPS[$svc]:-}"

    if [[ -z "$deps" ]]; then
      echo "${GREEN}ROOT${NC}  ${svc}"
      roots=$((roots + 1))
      ready=$((ready + 1))
      continue
    fi

    echo "${BOLD}${svc}${NC}  (needs: ${deps})"
    if validate_service "$svc" "$ENV" "$VERBOSE" 2>/dev/null; then
      ready=$((ready + 1))
    else
      blocked=$((blocked + 1))
    fi
    echo ""
  done

  echo "────────────────────────────────────────"
  echo "${BOLD}Summary:${NC} ${total} services | ${GREEN}${ready} ready${NC} | ${RED}${blocked} blocked${NC} | ${roots} roots"

  if [[ $blocked -gt 0 ]]; then
    echo ""
    echo "${RED}Some services are blocked by missing upstream data.${NC}"
    echo "Seed upstream services first, then re-run validation."
    exit 1
  else
    echo ""
    echo "${GREEN}All services have upstream data available.${NC}"
    exit 0
  fi
else
  # Single service mode
  echo "Checking upstream dependencies for ${BOLD}${SERVICE}${NC}..."
  echo ""
  if validate_service "$SERVICE" "$ENV" "$VERBOSE"; then
    echo ""
    info "All upstream data available for ${BOLD}${SERVICE}${NC}"
    exit 0
  else
    echo ""
    echo "${RED}Missing upstream data for ${SERVICE}.${NC}"
    echo "Seed the missing upstream service(s) first, then re-run."
    exit 1
  fi
fi
