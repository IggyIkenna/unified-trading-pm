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

# ── Colors ──────────────────────────────────────────────────────────────────
if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
  RED=$(tput setaf 1); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3)
  BOLD=$(tput bold); NC=$(tput sgr0)
else
  RED=""; GREEN=""; YELLOW=""; BOLD=""; NC=""
fi

info() { echo "${GREEN}>>>${NC} $*"; }
warn() { echo "${YELLOW}WARN:${NC} $*"; }

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
    kill "$pid" 2>/dev/null || true
    # Wait briefly for graceful shutdown
    local i=0
    while kill -0 "$pid" 2>/dev/null && [ $i -lt 10 ]; do
      sleep 0.2
      i=$((i + 1))
    done
    # Force kill if still running
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
    info "Stopped ${BOLD}${name}${NC} (PID $pid)"
  else
    warn "$name (PID $pid) was not running"
  fi

  rm -f "$pid_file"
  rm -f "/tmp/unified-dev-pids/${name}.log"
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
if [ ! -d "$PID_DIR" ]; then
  info "No dev servers are running (PID directory does not exist)."
else

echo "${BOLD}=== Stopping dev servers ===${NC}"

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
    info "No dev servers are running."
  fi

  # Clean up empty directory
  rmdir "$PID_DIR" 2>/dev/null || true
fi

fi  # end of "PID_DIR exists" block

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
