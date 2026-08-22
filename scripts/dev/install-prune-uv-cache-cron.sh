#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# install-prune-uv-cache-cron.sh — register the periodic shared `.uv-cache` prune cron.
#
# Idempotent: re-runs are safe. Operator runs this ONCE per host (the shared
# `${WORKSPACE_ROOT}/.tabs/.uv-cache` is read/written by every slot's `uv sync`, so this is
# a per-HOST install, not per-slot — mirrors install-cleanup-stale-qg-tmp-cron.sh). (Relocated
# INSIDE .tabs/ 2026-08-09 — see tabs_mount_boundary_defeats_uv_cache_hardlink_dedup_2026_08_09.md.)
#
# Usage:
#   bash unified-trading-pm/scripts/dev/install-prune-uv-cache-cron.sh
#   bash unified-trading-pm/scripts/dev/install-prune-uv-cache-cron.sh --uninstall
#   bash unified-trading-pm/scripts/dev/install-prune-uv-cache-cron.sh --interval 360   # 6h cadence
#
# Defaults:
#   - Interval: every 6 hours (240 free-space MB-to-hours ratio observed 2026-07-13 was
#     ~2 full-disk excursions in one session — a cadence more frequent than the tmp-scratch
#     sweep isn't warranted; `uv cache prune` scans the whole cache each run so it isn't free)
#   - Log file: ${XDG_RUNTIME_DIR:-/tmp}/prune-uv-cache.$(id -u).log (per-uid, mirrors
#     cleanup-stale-qg-tmp's convention)
#
# plans/active/issues/host_root_disk_full_transient_2026_07_13.md
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Cron-based FF puller"
# (same self-pull / idempotent-install convention)

set -euo pipefail

if [ "${EUID:-$(id -u)}" -eq 0 ] && [ "${ALLOW_ROOT_CRON:-0}" != "1" ]; then
    echo "Refusing to install as root (EUID=0) — belongs in the OPERATOR's per-user crontab." >&2
    echo "Re-run as the operator:  sudo -u <operator> WORKSPACE_ROOT=<workspace-root> bash $0" >&2
    exit 1
fi

INTERVAL_MIN=360
ACTION="install"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LOG_FILE="${XDG_RUNTIME_DIR:-/tmp}/prune-uv-cache.$(id -u).log"
MARKER="# prune-uv-cache"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --interval) INTERVAL_MIN="$2"; shift 2;;
        --uninstall) ACTION="uninstall"; shift;;
        -h|--help) sed -n '2,22p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0;;
        *) echo "Unknown arg: $1" >&2; exit 2;;
    esac
done

# Phase D guard (mirrors install-cleanup-stale-qg-tmp-cron.sh / install-slot-cron-ff-pull.sh):
# install from the workspace-ROOT PM clone, never a slot worktree — else the baked-in
# absolute path points at .tabs/N/.tabs/N.
case "${WORKSPACE_ROOT}" in
    */.tabs/*|*/.tabs) echo "Refusing: WORKSPACE_ROOT='${WORKSPACE_ROOT}' is inside a slot worktree (.tabs/). Run install from the root clone." >&2; exit 1;;
esac

PM_DIR="${WORKSPACE_ROOT}/unified-trading-pm"
INTEGRATION_BRANCH="live-defi-rollout"
PRUNE_SCRIPT="${PM_DIR}/scripts/dev/prune-uv-cache.sh"
# INSIDE .tabs/ (tabs_mount_boundary_defeats_uv_cache_hardlink_dedup_2026_08_09) — must
# match base-service.sh's / prune-uv-cache.sh's relocated default, else this cron prunes
# the (now unused) sibling-of-.tabs cache instead of the one the fleet actually writes to.
CACHE_DIR="${WORKSPACE_ROOT}/.tabs/.uv-cache"

source "$(dirname "${BASH_SOURCE[0]}")/cron-self-pull-lib.sh"
SELF_PULL="$(emit_cron_self_pull "${PM_DIR}" "${INTEGRATION_BRANCH}" "scripts/dev/prune-uv-cache.sh")"

CRON_LINE="0 */$((INTERVAL_MIN / 60)) * * * ${SELF_PULL}; bash \"${PRUNE_SCRIPT}\" --cache-dir \"${CACHE_DIR}\" --quiet >> \"${LOG_FILE}\" 2>&1 ${MARKER}"

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
    remove_cron "${MARKER}" "prune-uv-cache"
    exit 0
fi

if [ ! -f "${PRUNE_SCRIPT}" ]; then
    echo "Prune script not found at ${PRUNE_SCRIPT}" >&2
    exit 1
fi
chmod +x "${PRUNE_SCRIPT}"

ensure_cron "${MARKER}" "${CRON_LINE}" "prune-uv-cache (every ${INTERVAL_MIN}m)"

echo "[done] cron entry registered:"
echo "  ${CRON_LINE}"
echo ""
echo "Verify with: crontab -l | grep prune-uv-cache"
echo "First run will fire at the next $((INTERVAL_MIN / 60))-hour mark. Logs: ${LOG_FILE}"
