#!/usr/bin/env bash
# install-slot-cron-ff-pull.sh — register the 15-min FF-pull cron for an operator.
#
# Idempotent: re-runs are safe. Detects existing identical crontab entry and skips.
# Operator runs this ONCE per machine (not per slot — one cron run walks every slot).
#
# Usage:
#   bash unified-trading-pm/scripts/dev/install-slot-cron-ff-pull.sh
#   bash unified-trading-pm/scripts/dev/install-slot-cron-ff-pull.sh --uninstall
#   bash unified-trading-pm/scripts/dev/install-slot-cron-ff-pull.sh --interval 10   # 10-min cadence
#
# Defaults:
#   - Interval: 15 minutes
#   - Slot dir: ${WORKSPACE_ROOT}/.tabs/1 (uses --all-slots to walk every slot)
#   - Log file: /tmp/slot-cron-ff-pull.log (overwritten by puller, rotation manual)
#
# What it does:
#   1. Reads current `crontab -l`.
#   2. Checks for a line matching the slot-cron-ff-pull.sh marker.
#   3. If absent: appends a new entry running every <interval> minutes.
#   4. If present + identical: prints "already installed" and exits.
#   5. If present + differs: replaces the existing line.
#
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Cron-based FF puller"

set -euo pipefail

INTERVAL=15
ACTION="install"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
SLOT_DIR="${WORKSPACE_ROOT}/.tabs/1"
LOG_FILE="/tmp/slot-cron-ff-pull.log"
MARKER="# slot-cron-ff-pull"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --interval) INTERVAL="$2"; shift 2;;
        --uninstall) ACTION="uninstall"; shift;;
        --slot-dir) SLOT_DIR="$2"; shift 2;;
        -h|--help) sed -n '2,24p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0;;
        *) echo "Unknown arg: $1" >&2; exit 2;;
    esac
done

if [ ! -d "${SLOT_DIR}" ]; then
    echo "Slot dir does not exist: ${SLOT_DIR}" >&2
    echo "Set WORKSPACE_ROOT or pass --slot-dir <path>." >&2
    exit 1
fi

PULL_SCRIPT="${WORKSPACE_ROOT}/unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh"
if [ ! -x "${PULL_SCRIPT}" ]; then
    echo "FF-pull script not executable at ${PULL_SCRIPT}" >&2
    exit 1
fi

CRON_LINE="*/${INTERVAL} * * * * cd \"${SLOT_DIR}\" && bash \"${PULL_SCRIPT}\" --all-slots --quiet >> \"${LOG_FILE}\" 2>&1 ${MARKER}"

# Read existing crontab (empty if none).
CURRENT=$(crontab -l 2>/dev/null || true)

if [ "${ACTION}" = "uninstall" ]; then
    if echo "${CURRENT}" | grep -qF "${MARKER}"; then
        echo "${CURRENT}" | grep -vF "${MARKER}" | crontab -
        echo "[uninstalled] removed slot-cron-ff-pull entry from crontab"
    else
        echo "[noop] no slot-cron-ff-pull entry in crontab"
    fi
    exit 0
fi

# Install / update.
if echo "${CURRENT}" | grep -qF "${MARKER}"; then
    EXISTING=$(echo "${CURRENT}" | grep -F "${MARKER}" | head -1)
    if [ "${EXISTING}" = "${CRON_LINE}" ]; then
        echo "[already-installed] crontab entry already present + identical:"
        echo "  ${CRON_LINE}"
        exit 0
    fi
    echo "[updating] existing entry differs; replacing"
    NEW=$(echo "${CURRENT}" | grep -vF "${MARKER}")
    printf '%s\n%s\n' "${NEW}" "${CRON_LINE}" | crontab -
else
    echo "[installing] adding new entry"
    if [ -z "${CURRENT}" ]; then
        printf '%s\n' "${CRON_LINE}" | crontab -
    else
        printf '%s\n%s\n' "${CURRENT}" "${CRON_LINE}" | crontab -
    fi
fi

echo "[done] cron entry registered:"
echo "  ${CRON_LINE}"
echo ""
echo "Verify with: crontab -l | grep slot-cron-ff-pull"
echo "First run will fire at the next */${INTERVAL}-minute mark. Logs: ${LOG_FILE}"
