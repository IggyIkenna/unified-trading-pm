#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# install_reap_stale_blockers.sh — install the stale-blocker reaper systemd timer.
#
# Must run as root (or with sudo) on the orchestrator VM.
#
# Usage:
#   sudo bash scripts/orchestrator/install_reap_stale_blockers.sh
#   sudo bash scripts/orchestrator/install_reap_stale_blockers.sh --uninstall

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="reap-stale-blockers"
SYSTEMD_DIR="/etc/systemd/system"
LOG_DIR="/var/log/orchestrator"

case "${1:-}" in
    --uninstall)
        echo "Uninstalling ${SERVICE_NAME}..."
        systemctl disable --now "${SERVICE_NAME}.timer" 2>/dev/null || true
        rm -f "${SYSTEMD_DIR}/${SERVICE_NAME}.service" "${SYSTEMD_DIR}/${SERVICE_NAME}.timer"
        systemctl daemon-reload
        echo "Done."
        exit 0
        ;;
    "")
        ;;
    *)
        echo "Usage: $0 [--uninstall]" >&2; exit 2;;
esac

echo "Installing ${SERVICE_NAME} systemd timer (daily 04:00 UTC)..."

# Ensure log dir exists
mkdir -p "${LOG_DIR}"

# Copy unit files
install -m 644 "${SCRIPT_DIR}/${SERVICE_NAME}.service" "${SYSTEMD_DIR}/"
install -m 644 "${SCRIPT_DIR}/${SERVICE_NAME}.timer"   "${SYSTEMD_DIR}/"

# Reload + enable
systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}.timer"

echo ""
echo "Installed. Timer status:"
systemctl status "${SERVICE_NAME}.timer" --no-pager | head -10
echo ""
echo "Next fire time:"
systemctl list-timers "${SERVICE_NAME}.timer" --no-pager | tail -3
