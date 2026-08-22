#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# install-prune-prek-patch-cache-cron.sh — register the periodic shared prek patch-cache prune cron.
#
# Idempotent: re-runs are safe. Operator runs this ONCE per host (the shared
# ~/.cache/prek/patches/ is written by every slot's prek/quickmerge hook runs, so this is
# a per-HOST install, not per-slot — mirrors install-prune-uv-cache-cron.sh).
#
# Usage:
#   bash unified-trading-pm/scripts/dev/install-prune-prek-patch-cache-cron.sh
#   bash unified-trading-pm/scripts/dev/install-prune-prek-patch-cache-cron.sh --uninstall
#   bash unified-trading-pm/scripts/dev/install-prune-prek-patch-cache-cron.sh --interval 720   # 12h cadence
#   bash unified-trading-pm/scripts/dev/install-prune-prek-patch-cache-cron.sh --min-age-days 3  # 3-day retention
#
# Defaults:
#   - Interval: every 24 hours (measured growth is 6.7MB/520 files in one investigation
#     session on one host — not urgent enough to warrant a tighter cadence than a daily sweep)
#   - Retention: 7 days (comfortably past any single hook-run's stash/restore cycle;
#     a patch is only ever read by the same in-process struct that wrote it, never
#     re-selected from the directory later, so old patches are dead weight, not live state)
#   - Log file: ${XDG_RUNTIME_DIR:-/tmp}/prune-prek-patch-cache.$(id -u).log (per-uid,
#     mirrors prune-uv-cache/cleanup-stale-qg-tmp's convention)
#
# plans/archive/issues/prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Cron-based FF puller"
# (same self-pull / idempotent-install convention)

set -euo pipefail

if [ "${EUID:-$(id -u)}" -eq 0 ] && [ "${ALLOW_ROOT_CRON:-0}" != "1" ]; then
    echo "Refusing to install as root (EUID=0) — belongs in the OPERATOR's per-user crontab." >&2
    echo "Re-run as the operator:  sudo -u <operator> WORKSPACE_ROOT=<workspace-root> bash $0" >&2
    exit 1
fi

INTERVAL_MIN=1440
MIN_AGE_DAYS=7
ACTION="install"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LOG_FILE="${XDG_RUNTIME_DIR:-/tmp}/prune-prek-patch-cache.$(id -u).log"
MARKER="# prune-prek-patch-cache"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --interval) INTERVAL_MIN="$2"; shift 2;;
        --min-age-days) MIN_AGE_DAYS="$2"; shift 2;;
        --uninstall) ACTION="uninstall"; shift;;
        -h|--help) sed -n '2,23p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0;;
        *) echo "Unknown arg: $1" >&2; exit 2;;
    esac
done

# Phase D guard (mirrors install-prune-uv-cache-cron.sh / install-slot-cron-ff-pull.sh):
# install from the workspace-ROOT PM clone, never a slot worktree — else the baked-in
# absolute path points at .tabs/N/.tabs/N.
case "${WORKSPACE_ROOT}" in
    */.tabs/*|*/.tabs) echo "Refusing: WORKSPACE_ROOT='${WORKSPACE_ROOT}' is inside a slot worktree (.tabs/). Run install from the root clone." >&2; exit 1;;
esac

PM_DIR="${WORKSPACE_ROOT}/unified-trading-pm"
INTEGRATION_BRANCH="live-defi-rollout"
PRUNE_SCRIPT="${PM_DIR}/scripts/dev/prune-prek-patch-cache.sh"
PATCHES_DIR="${HOME}/.cache/prek/patches"

source "$(dirname "${BASH_SOURCE[0]}")/cron-self-pull-lib.sh"
SELF_PULL="$(emit_cron_self_pull "${PM_DIR}" "${INTEGRATION_BRANCH}" "scripts/dev/prune-prek-patch-cache.sh")"

CRON_LINE="0 */$((INTERVAL_MIN / 60)) * * * ${SELF_PULL}; bash \"${PRUNE_SCRIPT}\" --patches-dir \"${PATCHES_DIR}\" --min-age-days ${MIN_AGE_DAYS} --quiet >> \"${LOG_FILE}\" 2>&1 ${MARKER}"

ensure_cron() {
    local marker="$1" line="$2" label="$3" current existing
    current=$(crontab -l 2>/dev/null || true)
    if echo "${current}" | grep -qF "${marker}"; then
        existing=$(echo "${current}" | grep -F "${marker}" | head -1)
        if [ "${existing}" = "${line}" ]; then
            echo "[already-installed] ${label}"
            return 0
        fi
        echo "[updating] ${label} (entry differs; replacing)"
        printf '%s\n%s\n' "$(echo "${current}" | grep -vF "${marker}")" "${line}" | crontab -
    else
        echo "[installing] ${label}"
        if [ -z "${current}" ]; then printf '%s\n' "${line}" | crontab -
        else printf '%s\n%s\n' "${current}" "${line}" | crontab -; fi
    fi
}
remove_cron() {
    local marker="$1" label="$2" current
    current=$(crontab -l 2>/dev/null || true)
    if echo "${current}" | grep -qF "${marker}"; then
        echo "${current}" | grep -vF "${marker}" | crontab -
        echo "[uninstalled] ${label}"
    else
        echo "[noop] no ${label} entry"
    fi
}

if [ "${ACTION}" = "uninstall" ]; then
    remove_cron "${MARKER}" "prune-prek-patch-cache"
    exit 0
fi

if [ ! -f "${PRUNE_SCRIPT}" ]; then
    echo "Prune script not found at ${PRUNE_SCRIPT}" >&2
    exit 1
fi
chmod +x "${PRUNE_SCRIPT}"

ensure_cron "${MARKER}" "${CRON_LINE}" "prune-prek-patch-cache (every ${INTERVAL_MIN}m, retention=${MIN_AGE_DAYS}d)"

echo "[done] cron entry registered:"
echo "  ${CRON_LINE}"
echo ""
echo "Verify with: crontab -l | grep prune-prek-patch-cache"
echo "First run will fire at the next $((INTERVAL_MIN / 60))-hour mark. Logs: ${LOG_FILE}"
