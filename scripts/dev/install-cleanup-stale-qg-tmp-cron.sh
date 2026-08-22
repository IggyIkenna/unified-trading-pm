#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# install-cleanup-stale-qg-tmp-cron.sh — register the hourly stale-QG-scratch cleanup cron.
#
# Idempotent: re-runs are safe. Operator runs this ONCE per host (the cleanup script
# sweeps ${HOME}/.cache/qg-tmp + legacy /tmp/pytest-of-* for the invoking user, which
# covers every slot on this host — not a per-slot install).
#
# Usage:
#   bash unified-trading-pm/scripts/dev/install-cleanup-stale-qg-tmp-cron.sh
#   bash unified-trading-pm/scripts/dev/install-cleanup-stale-qg-tmp-cron.sh --uninstall
#   bash unified-trading-pm/scripts/dev/install-cleanup-stale-qg-tmp-cron.sh --interval 30   # 30-min cadence
#   bash unified-trading-pm/scripts/dev/install-cleanup-stale-qg-tmp-cron.sh --min-age 90    # 90-min stale threshold
#
# Defaults:
#   - Interval: hourly (belt-and-suspenders sweep, not latency-sensitive)
#   - Min-age threshold: 60 minutes (comfortably past any single QG run's runtime)
#   - Log file: ${XDG_RUNTIME_DIR:-/tmp}/cleanup-stale-qg-tmp.$(id -u).log (per-uid, mirrors slot-cron-ff-pull.sh)
#
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Cron-based FF puller"
# (same self-pull / idempotent-install convention)

set -euo pipefail

if [ "${EUID:-$(id -u)}" -eq 0 ] && [ "${ALLOW_ROOT_CRON:-0}" != "1" ]; then
    echo "Refusing to install as root (EUID=0) — belongs in the OPERATOR's per-user crontab." >&2
    echo "Re-run as the operator:  sudo -u <operator> WORKSPACE_ROOT=<workspace-root> bash $0" >&2
    exit 1
fi

INTERVAL=60
MIN_AGE=60
ACTION="install"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LOG_FILE="${XDG_RUNTIME_DIR:-/tmp}/cleanup-stale-qg-tmp.$(id -u).log"
MARKER="# cleanup-stale-qg-tmp"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --interval) INTERVAL="$2"; shift 2;;
        --min-age) MIN_AGE="$2"; shift 2;;
        --uninstall) ACTION="uninstall"; shift;;
        -h|--help) sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0;;
        *) echo "Unknown arg: $1" >&2; exit 2;;
    esac
done

# Phase D guard (mirrors install-slot-cron-ff-pull.sh): install from the workspace-ROOT
# PM clone, never a slot worktree — else the baked-in absolute path points at .tabs/N/.tabs/N.
case "${WORKSPACE_ROOT}" in
    */.tabs/*|*/.tabs) echo "Refusing: WORKSPACE_ROOT='${WORKSPACE_ROOT}' is inside a slot worktree (.tabs/). Run install from the root clone." >&2; exit 1;;
esac

PM_DIR="${WORKSPACE_ROOT}/unified-trading-pm"
INTEGRATION_BRANCH="live-defi-rollout"
CLEANUP_SCRIPT="${PM_DIR}/scripts/dev/cleanup-stale-qg-tmp.sh"

source "$(dirname "${BASH_SOURCE[0]}")/cron-self-pull-lib.sh"
SELF_PULL="$(emit_cron_self_pull "${PM_DIR}" "${INTEGRATION_BRANCH}" "scripts/dev/cleanup-stale-qg-tmp.sh")"

CRON_LINE="*/${INTERVAL} * * * * ${SELF_PULL}; bash \"${CLEANUP_SCRIPT}\" --min-age ${MIN_AGE} --quiet >> \"${LOG_FILE}\" 2>&1 ${MARKER}"

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
    remove_cron "${MARKER}" "cleanup-stale-qg-tmp"
    exit 0
fi

if [ ! -f "${CLEANUP_SCRIPT}" ]; then
    echo "Cleanup script not found at ${CLEANUP_SCRIPT}" >&2
    exit 1
fi
chmod +x "${CLEANUP_SCRIPT}"

ensure_cron "${MARKER}" "${CRON_LINE}" "cleanup-stale-qg-tmp (*/${INTERVAL}m, min-age=${MIN_AGE}m)"

echo "[done] cron entry registered:"
echo "  ${CRON_LINE}"
echo ""
echo "Verify with: crontab -l | grep cleanup-stale-qg-tmp"
echo "First run will fire at the next */${INTERVAL}-minute mark. Logs: ${LOG_FILE}"
