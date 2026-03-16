#!/usr/bin/env bash
# qg-common.sh — Shared foundation for all quality-gate base scripts.
# Owned by unified-trading-pm. Do NOT edit per-repo.
#
# Provides:
#   - Color variables (RED, GREEN, YELLOW, BLUE, NC)
#   - Logging functions: log_section, log_success, log_fail, log_warn, log_ok
#   - QG_START timestamp
#   - REPO_ROOT / PROJECT_ROOT / SCRIPT_DIR detection (from BASH_SOURCE chain)
#   - _ci-status-updater.sh source + _qg_record_failure trap
#   - run_timeout() portable timeout wrapper
#
# Sourced by: base-service.sh, base-library.sh, base-ui.sh, base-codex.sh
# Must be sourced BEFORE version-alignment-gate.sh (which depends on REPO_ROOT).
#
# IMPORTANT: This file must NOT contain any repo-type-specific logic
# (no pytest, no npm, no ruff config, no mode parsing).

# ── TIMESTAMP ────────────────────────────────────────────────────────────────
QG_START=$(date +%s)

# ── COLORS ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ── LOGGING ──────────────────────────────────────────────────────────────────
log_section() { echo -e "\n${BLUE}── $1 ──${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_fail()    { echo -e "${RED}❌ $1${NC}"; }
log_warn()    { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_ok()      { :; }

# ── PROJECT / REPO ROOT DETECTION ────────────────────────────────────────────
# When a base-*.sh sources this file, the BASH_SOURCE stack is:
#   [0] = qg-common.sh  [1] = base-*.sh  [2] = caller stub (repo's quality-gates.sh)
# We derive PROJECT_ROOT from the caller stub's location (the repo that sourced us).
# If no caller stub (direct invocation), fall back to this file's own location.
_QG_CALLER="${BASH_SOURCE[2]:-${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}}"
QG_SCRIPT_DIR="$(cd "$(dirname "$_QG_CALLER")" && pwd)"
QG_PROJECT_ROOT="$(dirname "$QG_SCRIPT_DIR")"

# Export as the canonical names used by all base scripts
SCRIPT_DIR="${SCRIPT_DIR:-$QG_SCRIPT_DIR}"
PROJECT_ROOT="${PROJECT_ROOT:-$QG_PROJECT_ROOT}"
REPO_ROOT="${REPO_ROOT:-$(cd "$PROJECT_ROOT/.." 2>/dev/null && pwd)}"
unset _QG_CALLER QG_SCRIPT_DIR QG_PROJECT_ROOT

# ── CI_STATUS HANDLER (shared, locked) ───────────────────────────────────────
# SSOT: _ci-status-updater.sh — unified name resolution + fcntl locking for all base scripts.
source "$(dirname "${BASH_SOURCE[0]}")/_ci-status-updater.sh"

_qg_record_failure() {
    local exit_code=$?
    [[ $exit_code -eq 0 ]] && return 0
    [[ "${GITHUB_ACTIONS:-}" == "true" ]] && return $exit_code
    _qg_update_ci_status_failing
    return $exit_code
}
# Default trap — base scripts may override (e.g. base-ui.sh adds _qg_kill_children)
trap _qg_record_failure EXIT

# ── PORTABLE TIMEOUT ─────────────────────────────────────────────────────────
# Wraps a command with a wall-clock timeout. Tries GNU timeout, gtimeout (macOS
# via coreutils), perl alarm, then bare execution as last resort.
run_timeout() {
    local secs=$1; shift
    if command -v timeout &>/dev/null; then timeout "$secs" "$@"
    elif command -v gtimeout &>/dev/null; then gtimeout "$secs" "$@"
    elif command -v perl &>/dev/null; then perl -e 'alarm shift; exec @ARGV' -- "$secs" "$@"
    else "$@"; fi
}
