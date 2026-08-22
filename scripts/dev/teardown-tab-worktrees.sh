#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# teardown-tab-worktrees.sh — remove a per-slot worktree fleet.
#
# Usage:
#   teardown-tab-worktrees.sh --slot <N> [--operator <name>] [--force]
#       Remove slot <N>'s worktrees + delete its branches across every active
#       repo. Aborts if any worktree has dirty state, unless --force is passed.
#
# Use only when shrinking the slot fleet (rare). For between-theme cleanup,
# use setup-tab-worktrees.sh --reset-slot <N> instead.
#
# Codex SSOT: unified-trading-pm/codex/05-infrastructure/per-tab-worktrees.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WORKSPACE_ROOT="${UNIFIED_TRADING_WORKSPACE_ROOT:-$(cd "${PM_DIR}/.." && pwd)}"
TABS_DIR="${WORKSPACE_ROOT}/.tabs"
MANIFEST="${PM_DIR}/workspace-manifest.json"

OPERATOR="${USER:-unknown}"
SLOT_NUM=""
FORCE=0

usage() { sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-1}"; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --slot)     SLOT_NUM="$2";  shift 2;;
        --operator) OPERATOR="$2";  shift 2;;
        --force)    FORCE=1;        shift;;
        -h|--help)  usage 0;;
        *)          echo "Unknown arg: $1" >&2; usage 1;;
    esac
done

[[ -z "${SLOT_NUM}" ]] && { echo "ERROR: --slot <N> required" >&2; usage 1; }

log() { printf '[teardown-tab-worktrees] %s\n' "$*"; }
err() { printf '[teardown-tab-worktrees] ERROR: %s\n' "$*" >&2; }

active_repos() {
    python3 - "${MANIFEST}" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
for k, v in d.get("repositories", {}).items():
    if not v.get("archived_into"):
        print(k)
PY
}

SLOT_DIR="${TABS_DIR}/${SLOT_NUM}"
BRANCH="tab/${OPERATOR}/${SLOT_NUM}"

if [[ ! -d "${SLOT_DIR}" ]]; then
    log "Slot ${SLOT_NUM} not present at ${SLOT_DIR}. Nothing to do."
    exit 0
fi

# Pre-flight: refuse if any repo has dirty state, unless --force.
if [[ "${FORCE}" == "0" ]]; then
    dirty_count=0
    while IFS= read -r repo; do
        rd="${SLOT_DIR}/${repo}"
        [[ -d "${rd}/.git" || -f "${rd}/.git" ]] || continue
        d=$(git -C "${rd}" status --porcelain=v1 2>/dev/null | wc -l | tr -d ' ')
        if [[ "${d}" != "0" ]]; then
            err "${repo}: ${d} dirty file(s); commit/push or pass --force"
            git -C "${rd}" status --short
            dirty_count=$((dirty_count + 1))
        fi
    done < <(active_repos)
    if [[ "${dirty_count}" -gt 0 ]]; then
        err "Slot ${SLOT_NUM} has dirty state across ${dirty_count} repo(s). Aborting."
        exit 2
    fi
fi

# Remove worktree per repo + delete branch.
log "Tearing down slot ${SLOT_NUM} (branch ${BRANCH})"
while IFS= read -r repo; do
    rd="${SLOT_DIR}/${repo}"
    sibling="${WORKSPACE_ROOT}/${repo}"
    [[ -d "${sibling}/.git" ]] || continue
    if [[ -d "${rd}/.git" || -f "${rd}/.git" ]]; then
        force_flag=""
        [[ "${FORCE}" == "1" ]] && force_flag="--force"
        git -C "${sibling}" worktree remove ${force_flag} "${rd}" 2>/dev/null \
            && log "  REMOVED ${repo} worktree" \
            || err "  FAILED  ${repo} worktree remove (continuing)"
    fi
    if git -C "${sibling}" show-ref --verify --quiet "refs/heads/${BRANCH}"; then
        git -C "${sibling}" branch -D "${BRANCH}" >/dev/null 2>&1 \
            && log "  DELETED ${repo} branch ${BRANCH}" \
            || err "  FAILED  ${repo} branch delete (continuing)"
    fi
done < <(active_repos)

# Clean up the slot directory (any leftover .envrc / .cache).
rm -rf "${SLOT_DIR}" 2>/dev/null || true
log "Slot ${SLOT_NUM} teardown complete."
