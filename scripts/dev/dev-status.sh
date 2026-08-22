#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# dev-status.sh — Show status of dev servers started by dev-start.sh
#
# Shows expected vs actual state for each service based on the mode and
# component filter (--frontend-only / --backend-only / --both) that was
# used when dev-start.sh was invoked.
#
# Statuses:
#   RUNNING     — process alive, expected
#   DEAD        — process died, was expected to be running (problem)
#   SKIPPED     — not started due to component filter (expected)
#   NOT STARTED — should be running but no PID file found (problem)
#
# Usage:
#   bash scripts/dev/dev-status.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAPPING_FILE="${SCRIPT_DIR}/ui-api-mapping.json"
PID_DIR="/tmp/unified-dev-pids"
MODE_FILE="/tmp/unified-dev-pids/.dev-mode"

# ── Colors ──────────────────────────────────────────────────────────────────
if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
  RED=$(tput setaf 1); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3)
  CYAN=$(tput setaf 6); BOLD=$(tput bold); NC=$(tput sgr0)
else
  RED=""; GREEN=""; YELLOW=""; CYAN=""; BOLD=""; NC=""
fi

# ── Helpers ─────────────────────────────────────────────────────────────────
require_jq() {
  command -v jq >/dev/null 2>&1 || { echo "${RED}ERROR:${NC} jq is required. Install with: brew install jq" >&2; exit 1; }
}

# Determine if a service name is a UI or API by checking the mapping file
is_ui_service() {
  local name="$1"
  jq -e --arg name "$name" '.stacks | to_entries[] | select(.value.ui == $name)' "$MAPPING_FILE" >/dev/null 2>&1
}

is_api_service() {
  local name="$1"
  jq -e --arg name "$name" '.stacks | to_entries[] | select(.value.api == $name)' "$MAPPING_FILE" >/dev/null 2>&1
}

get_port_for_service() {
  local name="$1"
  local port=""
  # Try UI first
  port=$(jq -r --arg name "$name" '
    .stacks | to_entries[] | select(.value.ui == $name) | .value.ui_port // empty
  ' "$MAPPING_FILE" 2>/dev/null || true)
  if [ -n "$port" ]; then
    echo "$port"
    return
  fi
  # Try API
  port=$(jq -r --arg name "$name" '
    .stacks | to_entries[] | select(.value.api == $name) | .value.api_port // empty
  ' "$MAPPING_FILE" 2>/dev/null || true)
  echo "$port"
}

# ── Main ────────────────────────────────────────────────────────────────────
require_jq

echo "${BOLD}=== Unified Trading System — Dev Status ===${NC}"
echo ""

if [ ! -d "$PID_DIR" ]; then
  echo "  No dev servers have been started."
  echo ""
  echo "  Start with: bash scripts/dev/dev-start.sh --all --mode mock"
  exit 0
fi

# Load mode info
COMPONENT_FILTER="both"
ENV_MODE=""
UI_DATA="" UI_AUTH="" API_DATA="" API_AUTH="" MOCK_STATE=""

if [ -f "$MODE_FILE" ]; then
  source "$MODE_FILE" 2>/dev/null || true
fi

# Show current mode if available
if [ -n "$ENV_MODE" ]; then
  echo "  Preset:     ${CYAN}${BOLD}${ENV_MODE}${NC}"
  echo "  Components: ${CYAN}${BOLD}${COMPONENT_FILTER}${NC}"
  echo ""
  echo "  ${BOLD}Mode Axes:${NC}"
  ui_data_color=$( [ "${UI_DATA:-mock}" = "mock" ] && echo "$YELLOW" || echo "$GREEN" )
  ui_auth_color=$( [ "${UI_AUTH:-skip}" = "skip" ] && echo "$YELLOW" || echo "$GREEN" )
  api_data_color=$( [ "${API_DATA:-mock}" = "mock" ] && echo "$YELLOW" || echo "$GREEN" )
  api_auth_color=$( [ "${API_AUTH:-disabled}" = "disabled" ] && echo "$YELLOW" || echo "$GREEN" )
  mock_state_color=$( [ "${MOCK_STATE:-n/a}" = "deterministic" ] && echo "$CYAN" || echo "$YELLOW" )
  printf "    %-12s ${ui_data_color}%-14s${NC}  (VITE_MOCK_API)\n" "UI data:" "${UI_DATA:-mock}"
  printf "    %-12s ${ui_auth_color}%-14s${NC}  (VITE_SKIP_AUTH)\n" "UI auth:" "${UI_AUTH:-skip}"
  printf "    %-12s ${api_data_color}%-14s${NC}  (CLOUD_MOCK_MODE)\n" "API data:" "${API_DATA:-mock}"
  printf "    %-12s ${api_auth_color}%-14s${NC}  (DISABLE_AUTH)\n" "API auth:" "${API_AUTH:-disabled}"
  printf "    %-12s ${mock_state_color}%-14s${NC}  (MOCK_STATE_MODE)\n" "Mock state:" "${MOCK_STATE:-n/a}"
  echo ""
fi

# ── Build expected service list from mapping file ───────────────────────────
# Collect all expected services based on component filter
declare -a expected_uis=()
declare -a expected_apis=()

for stack in $(jq -r '.stacks | keys[]' "$MAPPING_FILE"); do
  ui_repo=$(jq -r --arg s "$stack" '.stacks[$s].ui // empty' "$MAPPING_FILE")
  api_repo=$(jq -r --arg s "$stack" '.stacks[$s].api // empty' "$MAPPING_FILE")

  if [ -n "$ui_repo" ] && [ "$ui_repo" != "null" ]; then
    expected_uis+=("$ui_repo")
  fi
  if [ -n "$api_repo" ] && [ "$api_repo" != "null" ]; then
    expected_apis+=("$api_repo")
  fi
done

# Determine which services should be running based on component filter
declare -a expected_running=()
declare -a expected_skipped=()

case "$COMPONENT_FILTER" in
  frontend-only)
    expected_running=("${expected_uis[@]}")
    expected_skipped=("${expected_apis[@]}")
    ;;
  backend-only)
    expected_running=("${expected_apis[@]}")
    expected_skipped=("${expected_uis[@]}")
    ;;
  both|*)
    expected_running=("${expected_uis[@]}" "${expected_apis[@]}")
    expected_skipped=()
    ;;
esac

# ── Print status table ─────────────────────────────────────────────────────
counts_running=0
counts_dead=0
counts_skipped=0
counts_not_started=0

printf "  %-28s %-8s %-14s %-6s %s\n" "SERVICE" "PID" "STATUS" "PORT" "URL"
printf "  %-28s %-8s %-14s %-6s %s\n" "-------" "---" "------" "----" "---"

# Helper: check if a value is in an array
in_array() {
  local needle="$1"; shift
  for item in "$@"; do
    [ "$item" = "$needle" ] && return 0
  done
  return 1
}

# Process all known services (expected running + expected skipped)
all_services=("${expected_running[@]}" ${expected_skipped[@]+"${expected_skipped[@]}"})

for service in "${all_services[@]}"; do
  port=$(get_port_for_service "$service")
  url=""
  [ -n "$port" ] && url="http://localhost:${port}"
  pid_file="${PID_DIR}/${service}.pid"

  if in_array "$service" ${expected_skipped[@]+"${expected_skipped[@]}"}; then
    # Service was intentionally not started
    printf "  %-28s %-8s ${YELLOW}%-14s${NC} %-6s %s\n" "$service" "—" "SKIPPED" "${port:-?}" ""
    counts_skipped=$((counts_skipped + 1))
  elif [ -f "$pid_file" ]; then
    pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
      printf "  %-28s %-8s ${GREEN}%-14s${NC} %-6s %s\n" "$service" "$pid" "RUNNING" "${port:-?}" "$url"
      counts_running=$((counts_running + 1))
    else
      # PID is dead — check if something is actually listening on the port (orphan child process)
      actual_pid=""
      if [ -n "$port" ]; then
        actual_pid=$(lsof -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)
      fi
      if [ -n "$actual_pid" ]; then
        printf "  %-28s %-8s ${GREEN}%-14s${NC} %-6s %s\n" "$service" "$actual_pid" "RUNNING" "${port:-?}" "$url"
        counts_running=$((counts_running + 1))
      else
        printf "  %-28s %-8s ${RED}%-14s${NC} %-6s %s\n" "$service" "$pid" "DEAD" "${port:-?}" "$url"
        counts_dead=$((counts_dead + 1))
      fi
    fi
  else
    # No PID file — check if something is listening on the port anyway (started outside dev-start.sh)
    actual_pid=""
    if [ -n "$port" ]; then
      actual_pid=$(lsof -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)
    fi
    if [ -n "$actual_pid" ]; then
      printf "  %-28s %-8s ${GREEN}%-14s${NC} %-6s %s\n" "$service" "$actual_pid" "RUNNING" "${port:-?}" "$url"
      counts_running=$((counts_running + 1))
    else
      printf "  %-28s %-8s ${RED}%-14s${NC} %-6s %s\n" "$service" "—" "NOT STARTED" "${port:-?}" ""
      counts_not_started=$((counts_not_started + 1))
    fi
  fi
done

echo ""

# ── Summary ─────────────────────────────────────────────────────────────────
total=$((counts_running + counts_dead + counts_skipped + counts_not_started))
echo "  ${BOLD}Summary:${NC} ${GREEN}${counts_running} running${NC}, ${RED}${counts_dead} dead${NC}, ${RED}${counts_not_started} not started${NC}, ${YELLOW}${counts_skipped} skipped${NC} (${total} total)"

if [ $counts_dead -gt 0 ] || [ $counts_not_started -gt 0 ]; then
  echo ""
  echo "  ${RED}${BOLD}Issues detected.${NC} Check logs: tail -f /tmp/unified-dev-pids/<service>.log"
fi

echo ""
echo "  Logs: tail -f /tmp/unified-dev-pids/<service>.log"
echo "  Stop: bash scripts/dev/dev-stop.sh"
echo ""
