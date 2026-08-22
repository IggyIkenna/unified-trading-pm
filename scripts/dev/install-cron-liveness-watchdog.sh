#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# install-cron-liveness-watchdog.sh — register the off-GHA dead-man's-switch cron on
# the orchestrator VM (planning, i-0c9b283b31d6b5ca7). Idempotent: re-runs are safe.
#
# The watchdog (cron_liveness_watchdog.py) polls gh run list every 30 minutes to detect
# stale GHA cron monitors — catching the class where a billing-wall / Actions-disable
# silences the alarms along with CI (plan L1583).
#
# Run ONCE on the orchestrator VM:
#   bash scripts/dev/install-cron-liveness-watchdog.sh
#   bash scripts/dev/install-cron-liveness-watchdog.sh --uninstall
#   bash scripts/dev/install-cron-liveness-watchdog.sh --interval 60   # 60-min cadence
#
# Requires on the VM:
#   - GH_TOKEN (or $HOME/.config/gh/hosts.yml from `gh auth login`)
#   - SLACK_CI_WEBHOOK_URL (set in the VM's env-file, e.g. /etc/operator-env or ~/.operator-env)
#   - Python 3.9+
#
# Codex SSOT: codex/08-workflows/ci-cd-flow.md § "External liveness watchdog"

set -euo pipefail

INTERVAL="${INTERVAL:-30}"  # minutes between watchdog runs
ACTION="install"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WATCHDOG_SCRIPT="${SCRIPT_DIR}/../repo-management/cron_liveness_watchdog.py"
PM_REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Crontab marker — unique string that lets us detect / replace an existing entry.
CRON_MARKER="cron-liveness-watchdog"

# Source env-file for SLACK_CI_WEBHOOK_URL / GH_TOKEN if it exists (VM convention).
ENV_FILE="${OPERATOR_ENV_FILE:-${HOME}/.operator-env}"

# Log file: per-uid temp dir so a root-owned log never blocks the operator cron.
LOG_FILE="${XDG_RUNTIME_DIR:-/tmp}/cron-liveness-watchdog.$(id -u).log"

for arg in "$@"; do
  case "$arg" in
    --uninstall) ACTION="uninstall" ;;
    --interval) INTERVAL="${2:-30}"; shift ;;
    --interval=*) INTERVAL="${arg#--interval=}" ;;
    *) echo "Unknown arg: $arg" >&2; exit 1 ;;
  esac
done

# Refuse to install into root's crontab (mirrors install-slot-cron-ff-pull.sh guard).
if [ "${EUID:-$(id -u)}" -eq 0 ] && [ "${ALLOW_ROOT_CRON:-0}" != "1" ]; then
    echo "Refusing to install cron as root — run as the operator:" >&2
    echo "  sudo -u <operator> bash $0" >&2
    exit 1
fi

if [ ! -f "${WATCHDOG_SCRIPT}" ]; then
    echo "Watchdog script not found: ${WATCHDOG_SCRIPT}" >&2
    echo "Run from the unified-trading-pm repo root." >&2
    exit 1
fi

# Build the cron command.
# Source the env-file first so SLACK_CI_WEBHOOK_URL + GH_TOKEN are set in the cron env.
ENV_SOURCE=""
if [ -f "${ENV_FILE}" ]; then
    ENV_SOURCE="source ${ENV_FILE} 2>/dev/null; "
fi
CRON_CMD="${ENV_SOURCE}cd ${PM_REPO_ROOT} && python3 ${WATCHDOG_SCRIPT} >> ${LOG_FILE} 2>&1"
CRON_LINE="*/${INTERVAL} * * * * ${CRON_CMD}  # ${CRON_MARKER}"

# Read current crontab (empty if none).
CURRENT_CRONTAB="$(crontab -l 2>/dev/null || true)"

if [ "${ACTION}" = "uninstall" ]; then
    NEW_CRONTAB="$(echo "${CURRENT_CRONTAB}" | grep -v "${CRON_MARKER}" || true)"
    if [ "${NEW_CRONTAB}" = "${CURRENT_CRONTAB}" ]; then
        echo "[cron-liveness-watchdog] not found in crontab — nothing to uninstall."
    else
        echo "${NEW_CRONTAB}" | crontab -
        echo "[cron-liveness-watchdog] removed from crontab."
    fi
    exit 0
fi

# Check for an existing entry.
EXISTING="$(echo "${CURRENT_CRONTAB}" | grep "${CRON_MARKER}" || true)"
if [ "${EXISTING}" = "${CRON_LINE}" ]; then
    echo "[cron-liveness-watchdog] already installed (identical entry) — nothing to do."
    exit 0
fi

# Replace existing or append new.
if [ -n "${EXISTING}" ]; then
    NEW_CRONTAB="$(echo "${CURRENT_CRONTAB}" | grep -v "${CRON_MARKER}")"$'\n'"${CRON_LINE}"
    echo "[cron-liveness-watchdog] replacing existing crontab entry."
else
    NEW_CRONTAB="${CURRENT_CRONTAB}"$'\n'"${CRON_LINE}"
    echo "[cron-liveness-watchdog] adding new crontab entry (every ${INTERVAL} min)."
fi

echo "${NEW_CRONTAB}" | crontab -
echo "[cron-liveness-watchdog] installed. Verify with: crontab -l | grep ${CRON_MARKER}"
echo "Logs: ${LOG_FILE}"
echo ""
echo "Env-file checked: ${ENV_FILE}"
if [ ! -f "${ENV_FILE}" ]; then
    echo "  WARNING: env-file does not exist on this machine. Set SLACK_CI_WEBHOOK_URL"
    echo "  and GH_TOKEN in the cron environment manually or create ${ENV_FILE}."
fi
