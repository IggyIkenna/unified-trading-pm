#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# install-cleanup-stale-tmp-parquet-scratch-cron.sh — register the periodic
# large-one-off-parquet-scratch reaper cron.
#
# Idempotent: re-runs are safe. Operator runs this ONCE per host (the cleanup
# script sweeps $HOME/.cache/instruments-scratch + /tmp for the invoking user,
# which covers every slot on this host — not a per-slot install). Mirrors
# install-cleanup-stale-manifest-consolidate-tmp-cron.sh's install pattern exactly.
#
# Usage:
#   bash unified-trading-pm/scripts/dev/install-cleanup-stale-tmp-parquet-scratch-cron.sh
#   bash unified-trading-pm/scripts/dev/install-cleanup-stale-tmp-parquet-scratch-cron.sh --uninstall
#   bash unified-trading-pm/scripts/dev/install-cleanup-stale-tmp-parquet-scratch-cron.sh --interval 360   # 6h cadence (minutes; <60 uses minute-of-hour cron syntax)
#   bash unified-trading-pm/scripts/dev/install-cleanup-stale-tmp-parquet-scratch-cron.sh --min-age 720   # 12h threshold
#   bash unified-trading-pm/scripts/dev/install-cleanup-stale-tmp-parquet-scratch-cron.sh --private-tmp-min-age 60  # PrivateTmp sweep threshold
#
# Defaults (revised 2026-08-21 — see cleanup-stale-tmp-parquet-scratch.sh header for the
# PrivateTmp-namespace offender class that motivated the tighter cadence: a single such
# dir took a shared 8G tmpfs to 100% and caused live SQLite disk-full errors; the original
# 6h cadence let it accumulate unchecked for the service's whole 18h uptime):
#   - Interval: every 15 minutes — sub-hourly by design (INTERVAL is minutes; values <60
#     emit a `*/N * * * *` cron line, values >=60 emit the original `0 */(N/60) * * * *`
#     form for backward compatibility with any existing hour-granularity install)
#   - Min-age threshold: 6 hours (360 min) for the original glob-scoped sweep (unchanged —
#     that offender class is genuinely slow-accumulating, not urgent)
#   - Private-tmp min-age threshold: 60 min for the PrivateTmp whole-namespace sweep
#     (tighter — liveness-gating is the real safety net there, see script header)
#   - Log file: ${XDG_RUNTIME_DIR:-/tmp}/cleanup-stale-tmp-parquet-scratch.$(id -u).log
#     (per-uid, mirrors slot-cron-ff-pull.sh + install-cleanup-stale-qg-tmp-cron.sh)
#
# NOTE (2026-08-21): the PrivateTmp sweep (see script header) needs ROOT privilege —
# `/tmp/systemd-private-*` dirs are `drwx------ root:root`, so an operator-user crontab
# installed by THIS script (which deliberately refuses to install as root, below) can
# never see into them. This script still installs the operator-level cron for the
# ORIGINAL (sweep 1) offender class; the PrivateTmp sweep needs a SEPARATE root-owned
# mechanism (systemd timer) — tracked in
# /plans/active/issues/ao_tmp_tmpfs_full_sqlite_disk_full_errors_2026_08_21.md.
#
# Codex SSOT: codex/05-infrastructure/shared-host-tmp-tmpfs-capacity.md,
#             codex/05-infrastructure/per-tab-worktrees.md § "Cron-based FF puller"

set -euo pipefail

if [ "${EUID:-$(id -u)}" -eq 0 ] && [ "${ALLOW_ROOT_CRON:-0}" != "1" ]; then
    echo "Refusing to install as root (EUID=0) — belongs in the OPERATOR's per-user crontab." >&2
    echo "Re-run as the operator:  sudo -u <operator> WORKSPACE_ROOT=<workspace-root> bash $0" >&2
    exit 1
fi

INTERVAL=15
MIN_AGE=360
PRIVATE_TMP_MIN_AGE=60
ACTION="install"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LOG_FILE="${XDG_RUNTIME_DIR:-/tmp}/cleanup-stale-tmp-parquet-scratch.$(id -u).log"
MARKER="# cleanup-stale-tmp-parquet-scratch"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --interval) INTERVAL="$2"; shift 2;;
        --min-age) MIN_AGE="$2"; shift 2;;
        --private-tmp-min-age) PRIVATE_TMP_MIN_AGE="$2"; shift 2;;
        --uninstall) ACTION="uninstall"; shift;;
        -h|--help) sed -n '2,33p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0;;
        *) echo "Unknown arg: $1" >&2; exit 2;;
    esac
done

# Phase D guard (mirrors install-slot-cron-ff-pull.sh / install-cleanup-stale-qg-tmp-cron.sh):
# install from the workspace-ROOT PM clone, never a slot worktree — else the
# baked-in absolute path points at .tabs/N/.tabs/N.
case "${WORKSPACE_ROOT}" in
    */.tabs/*|*/.tabs) echo "Refusing: WORKSPACE_ROOT='${WORKSPACE_ROOT}' is inside a slot worktree (.tabs/). Run install from the root clone." >&2; exit 1;;
esac

PM_DIR="${WORKSPACE_ROOT}/unified-trading-pm"
INTEGRATION_BRANCH="live-defi-rollout"
CLEANUP_SCRIPT="${PM_DIR}/scripts/dev/cleanup-stale-tmp-parquet-scratch.sh"

source "$(dirname "${BASH_SOURCE[0]}")/cron-self-pull-lib.sh"
SELF_PULL="$(emit_cron_self_pull "${PM_DIR}" "${INTEGRATION_BRANCH}" "scripts/dev/cleanup-stale-tmp-parquet-scratch.sh")"

# INTERVAL is minutes. <60 needs minute-of-hour cron syntax (`*/N * * * *`); >=60 keeps
# the original hour-granularity form (`0 */(N/60) * * * *`) for backward compatibility
# with any existing install still passing an hour-multiple.
if [ "${INTERVAL}" -lt 60 ]; then
    CRON_SCHEDULE="*/${INTERVAL} * * * *"
else
    CRON_SCHEDULE="0 */$((INTERVAL / 60)) * * *"
fi

CRON_LINE="${CRON_SCHEDULE} ${SELF_PULL}; bash \"${CLEANUP_SCRIPT}\" --min-age ${MIN_AGE} --private-tmp-min-age ${PRIVATE_TMP_MIN_AGE} --quiet >> \"${LOG_FILE}\" 2>&1 ${MARKER}"

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
    remove_cron "${MARKER}" "cleanup-stale-tmp-parquet-scratch"
    exit 0
fi

if [ ! -f "${CLEANUP_SCRIPT}" ]; then
    echo "Cleanup script not found at ${CLEANUP_SCRIPT}" >&2
    exit 1
fi
chmod +x "${CLEANUP_SCRIPT}"

ensure_cron "${MARKER}" "${CRON_LINE}" "cleanup-stale-tmp-parquet-scratch (every ${INTERVAL}m, min-age=${MIN_AGE}m, private-tmp-min-age=${PRIVATE_TMP_MIN_AGE}m)"

echo "[done] cron entry registered:"
echo "  ${CRON_LINE}"
echo ""
echo "Verify with: crontab -l | grep cleanup-stale-tmp-parquet-scratch"
echo "First run will fire within ${INTERVAL} minutes. Logs: ${LOG_FILE}"
