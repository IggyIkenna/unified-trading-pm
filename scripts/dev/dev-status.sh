#!/usr/bin/env bash
# dev-status.sh — Show status of dev servers started by dev-start.sh
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

# ── Main ────────────────────────────────────────────────────────────────────
echo "${BOLD}=== Unified Trading System — Dev Status ===${NC}"
echo ""

if [ ! -d "$PID_DIR" ]; then
  echo "  No dev servers have been started."
  echo ""
  echo "  Start with: bash scripts/dev/dev-start.sh --stack <name>"
  exit 0
fi

# Show current mode if available
if [ -f "$MODE_FILE" ]; then
  source "$MODE_FILE" 2>/dev/null
  echo "  Preset:     ${CYAN}${BOLD}${ENV_MODE:-unknown}${NC}"
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

found=false
printf "  %-28s %-8s %-8s %-6s %s\n" "SERVICE" "PID" "STATUS" "PORT" "URL"
printf "  %-28s %-8s %-8s %-6s %s\n" "-------" "---" "------" "----" "---"

for pid_file in "$PID_DIR"/*.pid; do
  [ -f "$pid_file" ] || continue
  found=true

  name=$(basename "$pid_file" .pid)
  pid=$(cat "$pid_file")

  # Determine port from mapping
  port="?"
  if command -v jq >/dev/null 2>&1 && [ -f "$MAPPING_FILE" ]; then
    # Check if it's a UI
    ui_port=$(jq -r --arg name "$name" '
      .stacks | to_entries[] | select(.value.ui == $name) | .value.ui_port // empty
    ' "$MAPPING_FILE" 2>/dev/null || true)

    if [ -n "$ui_port" ]; then
      port="$ui_port"
    else
      # Check if it's an API
      api_port=$(jq -r --arg name "$name" '
        .stacks | to_entries[] | select(.value.api == $name) | .value.api_port // empty
      ' "$MAPPING_FILE" 2>/dev/null || true)
      if [ -n "$api_port" ]; then
        port="$api_port"
      fi
    fi
  fi

  url=""
  if [ "$port" != "?" ]; then
    url="http://localhost:${port}"
  fi

  if kill -0 "$pid" 2>/dev/null; then
    printf "  %-28s %-8s ${GREEN}%-8s${NC} %-6s %s\n" "$name" "$pid" "RUNNING" "$port" "$url"
  else
    printf "  %-28s %-8s ${RED}%-8s${NC} %-6s %s\n" "$name" "$pid" "DEAD" "$port" "$url"
  fi
done

if [ "$found" = false ]; then
  echo "  No dev servers are running."
fi

echo ""

# Show log tail hint
if [ "$found" = true ]; then
  echo "  Logs: tail -f /tmp/unified-dev-pids/<service>.log"
  echo "  Stop: bash scripts/dev/dev-stop.sh"
  echo ""
fi
