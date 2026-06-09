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
# We derive PROJECT_ROOT by walking UP from the caller stub's directory to the
# nearest pyproject.toml (the repo boundary marker). This is more robust than
# `dirname dirname` because it:
#   - handles non-standard repo layouts (scripts/ nested deeper than 1 level)
#   - never jumps to a sibling worktree's root under .tabs/<N>/ per-tab layout
#   - resolves correctly under symlinked invocations
# If no caller stub (direct invocation), fall back to this file's own location.
_QG_CALLER="${BASH_SOURCE[2]:-${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}}"
QG_SCRIPT_DIR="$(cd "$(dirname "$_QG_CALLER")" && pwd)"
_qg_walk_up_to_pyproject() {
    local d="$1"
    while [[ "$d" != "/" && -n "$d" ]]; do
        [[ -f "$d/pyproject.toml" ]] && { echo "$d"; return 0; }
        d="$(dirname "$d")"
    done
    return 1
}
QG_PROJECT_ROOT="$(_qg_walk_up_to_pyproject "$QG_SCRIPT_DIR")" \
    || QG_PROJECT_ROOT="$(dirname "$QG_SCRIPT_DIR")"
unset -f _qg_walk_up_to_pyproject

# Export as the canonical names used by all base scripts
SCRIPT_DIR="${SCRIPT_DIR:-$QG_SCRIPT_DIR}"
PROJECT_ROOT="${PROJECT_ROOT:-$QG_PROJECT_ROOT}"
REPO_ROOT="${REPO_ROOT:-$(cd "$PROJECT_ROOT/.." 2>/dev/null && pwd)}"

# Banner — names the resolved repo so the operator can spot wrong-resolution at a glance.
# Critical under per-tab worktrees (.tabs/<N>/<repo>/) where sibling-worktree confusion
# was the root cause of slot_worktree_qg_repo_root_resolution_2026_05_11.
if [[ -z "${QG_BANNER_SUPPRESS:-}" ]]; then
    _qg_project_basename="$(basename "$PROJECT_ROOT")"
    if [[ -n "${SERVICE_NAME:-}" && "${SERVICE_NAME}" != "${_qg_project_basename}" ]]; then
        echo -e "\033[1;33m⚠️  [quality-gates] SERVICE_NAME='${SERVICE_NAME}' but PROJECT_ROOT='${PROJECT_ROOT}' (basename='${_qg_project_basename}') — possible sibling-worktree confusion\033[0m" >&2
    else
        echo -e "\033[0;34m[quality-gates] ${SERVICE_NAME:-${_qg_project_basename}} @ ${PROJECT_ROOT}\033[0m" >&2
    fi
    unset _qg_project_basename
fi
unset _QG_CALLER QG_SCRIPT_DIR QG_PROJECT_ROOT

# ── QG PROFILER (opt-in; inactive unless QG_PROFILE=1) ────────────────────────
# No-op by default — zero behaviour change for normal runs across all repos. When
# QG_PROFILE=1, qg_prof appends one JSONL marker per phase/check boundary to
# $QG_PROFILE_FILE; an external profiler (scripts/quality_gates/profile_qg_resources.py)
# pairs start/end markers + samples RSS to produce a per-span wall+RAM JSON report.
# Output lives under .qg_profile/ (gitignored) so it never churns the worktree.
if [[ "${QG_PROFILE:-}" == "1" ]]; then
    QG_PROFILE_FILE="${QG_PROFILE_FILE:-${PROJECT_ROOT}/.qg_profile/markers.jsonl}"
    mkdir -p "$(dirname "$QG_PROFILE_FILE")" 2>/dev/null || true
    : > "$QG_PROFILE_FILE" 2>/dev/null || true
    qg_prof() { printf '{"ts":%s,"event":"%s","name":"%s"}\n' "$(date +%s.%N)" "${1:-}" "${2:-}" >> "$QG_PROFILE_FILE" 2>/dev/null || true; }
else
    qg_prof() { :; }
fi

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
