#!/usr/bin/env bash
# Epic: cicd_mvp_ldr_to_main_pipeline_2026_06_30
# Lifecycle: permanent
# Delete-when: NA
# install_ldr_to_main_promote_heartbeat.sh — install the LDR->main promote heartbeat systemd timer.
#
# Must run as root (or with sudo) on the orchestrator VM (id `planning`, EIP 13.113.200.22),
# the same box that already runs reap-stale-blockers.timer / slot-cron-ff-pull.
#
# Usage:
#   sudo bash scripts/orchestrator/install_ldr_to_main_promote_heartbeat.sh
#   sudo bash scripts/orchestrator/install_ldr_to_main_promote_heartbeat.sh --uninstall
#
# [OPERATOR] This installer must be RUN ON THE ORCHESTRATOR VM ITSELF (not from a dev
# checkout / slot worktree) -- it writes into /etc/systemd/system and calls systemctl, which
# require root on that box. See the plan's Task-1 handoff note in
# plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md for the exact command.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="ldr-to-main-promote-heartbeat"
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
"") ;;
*)
  echo "Usage: $0 [--uninstall]" >&2
  exit 2
  ;;
esac

echo "Installing ${SERVICE_NAME} systemd timer (every 15 min)..."

mkdir -p "${LOG_DIR}"

install -m 644 "${SCRIPT_DIR}/${SERVICE_NAME}.service" "${SYSTEMD_DIR}/"
install -m 644 "${SCRIPT_DIR}/${SERVICE_NAME}.timer" "${SYSTEMD_DIR}/"
chmod 755 "${SCRIPT_DIR}/${SERVICE_NAME}.sh"

systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}.timer"

echo ""
echo "Installed. Timer status:"
systemctl status "${SERVICE_NAME}.timer" --no-pager | head -10
echo ""
echo "Next fire time:"
systemctl list-timers "${SERVICE_NAME}.timer" --no-pager | tail -3
