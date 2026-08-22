#!/usr/bin/env bash
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: shared bare-repo dep-clone fast path retired
#
# install-prune-shared-bare-repo-worktrees.sh — install the hourly worktree-prune systemd timer
# on the CI glue-runner host.
#
# Must run as root (or with sudo) on the CI VM (the same host that already runs
# docker-disk-cleanup.timer / ci-vm-resource-watchdog.timer / tmpfs-disk-cleanup.timer).
#
# Usage:
#   sudo bash scripts/self-hosted-runners/install-prune-shared-bare-repo-worktrees.sh
#   sudo bash scripts/self-hosted-runners/install-prune-shared-bare-repo-worktrees.sh --uninstall
#
# [OPERATOR] This installer must be RUN ON THE CI VM ITSELF (not from a dev checkout / slot
# worktree) — it writes into /etc/systemd/system and calls systemctl, which require root on that
# box. The .sh it drives is deployed to /usr/local/sbin/ separately by
# github-glue-deploy-sync.timer (deploy-sbin-scripts.sh) — this installer only wires the unit.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="prune-shared-bare-repo-worktrees"
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

echo "Installing ${SERVICE_NAME} systemd timer (hourly)..."

install -m 644 "${SCRIPT_DIR}/${SERVICE_NAME}.service" "${SYSTEMD_DIR}/"
install -m 644 "${SCRIPT_DIR}/${SERVICE_NAME}.timer" "${SYSTEMD_DIR}/"

systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}.timer"

echo ""
echo "Installed. Timer status:"
systemctl status "${SERVICE_NAME}.timer" --no-pager | head -10
echo ""
echo "Next fire time:"
systemctl list-timers "${SERVICE_NAME}.timer" --no-pager | tail -3
