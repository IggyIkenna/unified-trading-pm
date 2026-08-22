#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# install_template_drift_daily_check.sh — install the workflow-template drift daily-check systemd
# timer (rollout-ratchet panel backend).
#
# Must run as root (or with sudo) on the orchestrator VM (id `planning`,
# api.agent-orchestrator.odum-research.com — see orchestrator_vm_registry.yaml for the
# current instance id/IP, which changes across cloud migrations), the same box that
# already runs reap-stale-blockers.timer / ldr-to-main-promote-heartbeat.timer /
# qg-baseline-daily-promote.timer.
#
# Usage:
#   sudo bash scripts/orchestrator/install_template_drift_daily_check.sh
#   sudo bash scripts/orchestrator/install_template_drift_daily_check.sh --uninstall
#
# [OPERATOR] This installer must be RUN ON THE ORCHESTRATOR VM ITSELF (not from a dev
# checkout / slot worktree) — it writes into /etc/systemd/system and calls systemctl, which
# require root on that box.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="template-drift-daily-check"
SYSTEMD_DIR="/etc/systemd/system"

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

echo "Installing ${SERVICE_NAME} systemd timer (daily, 03:23 UTC)..."

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
