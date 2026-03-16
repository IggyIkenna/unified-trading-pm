#!/usr/bin/env bash
# dev-stop.sh — Stop all dev servers started by dev-start.sh
#
# Usage:
#   bash scripts/dev/dev-stop.sh           # stop all
#   bash scripts/dev/dev-stop.sh NAME      # stop specific service (e.g. deployment-ui)
#   bash scripts/dev/dev-stop.sh --clean   # stop all + remove .local-dev-cache/

set -euo pipefail

PID_DIR="/tmp/unified-dev-pids"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
CLEAN_CACHE=false

# Known dev ports for final sweep
UI_PORTS=(5173 5174 5175 5176 5177 5178 5179 5180 5181 5182 5183)
API_PORTS=(8004 8005 8006 8007 8008 8009 8010 8011 8012 8013 8014 8015 8016)

# ── Colors ──────────────────────────────────────────────────────────────────
if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
  RED=$(tput setaf 1); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3)
  BOLD=$(tput bold); NC=$(tput sgr0)
else
  RED=""; GREEN=""; YELLOW=""; BOLD=""; NC=""
fi

info() { echo "${GREEN}>>>${NC} $*"; }
warn() { echo "${YELLOW}WARN:${NC} $*"; }

# Kill a process and all its children
kill_tree() {
  local pid="$1"
  local sig="${2:-TERM}"
  # Kill children first
  pkill "-${sig}" -P "$pid" 2>/dev/null || true
  # Then kill the parent
  kill "-${sig}" "$pid" 2>/dev/null || true
}

stop_service() {
  local pid_file="$1"
  local name
  name=$(basename "$pid_file" .pid)

  if [ ! -f "$pid_file" ]; then
    return
  fi

  local pid
  pid=$(cat "$pid_file")

  if kill -0 "$pid" 2>/dev/null; then
    # Graceful: kill process tree with SIGTERM
    kill_tree "$pid" "TERM"
    # Wait briefly for graceful shutdown
    local i=0
    while kill -0 "$pid" 2>/dev/null && [ $i -lt 10 ]; do
      sleep 0.2
      i=$((i + 1))
    done
    # Force kill if still running
    if kill -0 "$pid" 2>/dev/null; then
      kill_tree "$pid" "9"
    fi
    info "Stopped ${BOLD}${name}${NC} (PID $pid)"
  else
    # PID not running — try killing by port as fallback (handles orphaned child processes)
    local port_file="${PID_DIR}/${name}.port"
    local killed_by_port=false
    if [ -f "$port_file" ]; then
      local port
      port=$(cat "$port_file")
      local port_pid
      port_pid=$(lsof -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)
      if [ -n "$port_pid" ]; then
        kill_tree "$port_pid" "TERM"
        info "Stopped ${BOLD}${name}${NC} (orphan PID $port_pid on port $port)"
        killed_by_port=true
      fi
    fi
    if [ "$killed_by_port" = false ]; then
      warn "$name (PID $pid) was not running"
    fi
  fi

  rm -f "$pid_file"
  rm -f "${PID_DIR}/${name}.port"
  rm -f "${PID_DIR}/${name}.log"
  # Watcher processes use a -watcher suffix on their log files
  rm -f "${PID_DIR}/${name%-watcher}.log" 2>/dev/null || true
}

# Final sweep: kill anything still listening on known dev ports
sweep_ports() {
  local swept=0
  for port in "${UI_PORTS[@]}" "${API_PORTS[@]}"; do
    local remaining
    remaining=$(lsof -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)
    if [ -n "$remaining" ]; then
      kill "$remaining" 2>/dev/null || true
      swept=$((swept + 1))
    fi
  done
  if [ "$swept" -gt 0 ]; then
    info "Swept $swept orphaned process(es) from dev ports"
  fi
}

# ── Argument parsing ────────────────────────────────────────────────────────
SERVICES=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --clean)
      CLEAN_CACHE=true
      shift
      ;;
    *)
      SERVICES+=("$1")
      shift
      ;;
  esac
done

# ── Main ────────────────────────────────────────────────────────────────────
echo "${BOLD}=== Stopping dev servers ===${NC}"

if [ ! -d "$PID_DIR" ]; then
  info "No PID-tracked dev servers."
else
  if [ ${#SERVICES[@]} -gt 0 ]; then
    # Stop specific services
    for name in "${SERVICES[@]}"; do
      pid_file="${PID_DIR}/${name}.pid"
      if [ -f "$pid_file" ]; then
        stop_service "$pid_file"
      else
        warn "No PID file found for: $name"
      fi
    done
  else
    # Stop all
    found=false
    for pid_file in "$PID_DIR"/*.pid; do
      [ -f "$pid_file" ] || continue
      found=true
      stop_service "$pid_file"
    done

    if [ "$found" = false ]; then
      info "No PID-tracked dev servers."
    fi

    # Clean up empty directory
    rmdir "$PID_DIR" 2>/dev/null || true
  fi
fi

# Always sweep: kill orphan processes on known dev ports (e.g. from manual npm run dev)
sweep_ports

# ── Clean mock state cache ────────────────────────────────────────────────
if [ "$CLEAN_CACHE" = true ]; then
  CACHE_DIR="${WORKSPACE_ROOT}/.local-dev-cache"
  if [ -d "$CACHE_DIR" ]; then
    rm -rf "$CACHE_DIR"
    info "Cleaned mock state cache: ${CACHE_DIR}"
  else
    info "No mock state cache to clean."
  fi
fi

echo ""
info "Done."
