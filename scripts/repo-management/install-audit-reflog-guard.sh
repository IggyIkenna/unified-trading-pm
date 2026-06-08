#!/usr/bin/env bash
# install-audit-reflog-guard.sh — install the reflog-reset safety guard on THIS host, cross-platform.
#
#   macOS → launchd (delegates to launchd/install-audit-reflog*.sh + launchctl load)
#   Linux → systemd --user (audit-reflog.timer every 10m + audit-reflog-watch.service via inotifywait)
#
# Installs BOTH the periodic audit and the event-based watcher. Idempotent — safe to re-run.
# The guard ALERTS (Telegram + desktop notification) ONLY on high-risk resets; a clean run is silent
# on every channel. SSOT: docs/audit-reflog-scheduled-job.md.
#
# Usage:
#   bash unified-trading-pm/scripts/repo-management/install-audit-reflog-guard.sh
#   bash unified-trading-pm/scripts/repo-management/install-audit-reflog-guard.sh --uninstall
#
# Run from: workspace root (or anywhere — WORKSPACE_ROOT auto-resolves).

set -euo pipefail

# Bash floor (portability pin): every reflog-guard + slot-cron script targets the fleet's OLDEST
# bash — macOS /bin/bash 3.2 (frozen 2007). We use NO bash-4+ features (mapfile/declare -A/${,,})
# so the same script runs on macOS 3.2, Ubuntu desktop, and the VMs alike — that uniformity is what
# lets a VM bootstrap itself. Fail fast if run under plain sh or a pre-3.2 bash so a future
# portability regression surfaces here, not mid-bootstrap. SSOT: docs/audit-reflog-scheduled-job.md.
if [ -z "${BASH_VERSION:-}" ]; then echo "ERROR: run with bash, not sh — e.g. 'bash $0'" >&2; exit 1; fi
if [ "${BASH_VERSINFO[0]}" -lt 3 ] || { [ "${BASH_VERSINFO[0]}" -eq 3 ] && [ "${BASH_VERSINFO[1]}" -lt 2 ]; }; then
  echo "ERROR: bash >= 3.2 required (found ${BASH_VERSION})" >&2; exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SYSTEMD_SRC="$SCRIPT_DIR/systemd"
USER_UNIT_DIR="$HOME/.config/systemd/user"
ACTION="install"

for a in "$@"; do
  case "$a" in
    --uninstall) ACTION="uninstall" ;;
    -h|--help) sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown arg: $a" >&2; exit 2 ;;
  esac
done

log() { printf '[install-audit-reflog-guard] %s\n' "$*"; }

OS="$(uname -s)"

# ───────────────────────── macOS (launchd) ─────────────────────────
install_macos() {
  log "macOS → launchd"
  bash "$SCRIPT_DIR/launchd/install-audit-reflog.sh"
  bash "$SCRIPT_DIR/launchd/install-audit-reflog-watch.sh"
  for plist in com.unified-trading.audit-reflog com.unified-trading.audit-reflog-watch; do
    p="$HOME/Library/LaunchAgents/${plist}.plist"
    launchctl unload "$p" 2>/dev/null || true   # idempotent reload
    launchctl load "$p" 2>/dev/null && log "  loaded ${plist}" || log "  WARN: launchctl load failed for ${plist}"
  done
}
uninstall_macos() {
  for plist in com.unified-trading.audit-reflog com.unified-trading.audit-reflog-watch; do
    p="$HOME/Library/LaunchAgents/${plist}.plist"
    launchctl unload "$p" 2>/dev/null || true
    rm -f "$p" && log "  removed ${plist}"
  done
}

# ───────────────────────── Linux (systemd --user) ─────────────────────────
install_linux() {
  log "Linux → systemd --user"
  command -v systemctl >/dev/null 2>&1 || { log "ERROR: systemctl not found — cannot install user units"; exit 1; }

  # Prereqs (warn, don't fail — the timer still works without them; the watcher needs inotifywait).
  command -v inotifywait >/dev/null 2>&1 || log "  WARN: inotifywait missing → event-watcher won't run. Install: sudo apt install inotify-tools"
  command -v notify-send >/dev/null 2>&1 || log "  NOTE: notify-send missing → high-risk desktop popups skipped (Telegram still fires). Install: sudo apt install libnotify-bin"

  mkdir -p "$USER_UNIT_DIR"
  for unit in audit-reflog.service audit-reflog.timer audit-reflog-watch.service; do
    sed "s|WORKSPACE_ROOT_PLACEHOLDER|${WORKSPACE_ROOT}|g" "$SYSTEMD_SRC/$unit" > "$USER_UNIT_DIR/$unit"
    log "  installed $USER_UNIT_DIR/$unit"
  done

  systemctl --user daemon-reload
  systemctl --user enable --now audit-reflog.timer 2>&1 | sed 's/^/    /' || log "  WARN: enabling timer failed"
  if command -v inotifywait >/dev/null 2>&1; then
    systemctl --user enable --now audit-reflog-watch.service 2>&1 | sed 's/^/    /' || log "  WARN: enabling watch service failed"
  fi

  # On a headless server, --user units stop when the operator logs out unless lingering is on.
  if command -v loginctl >/dev/null 2>&1 && [[ "$(loginctl show-user "$USER" -p Linger --value 2>/dev/null || echo no)" != "yes" ]]; then
    log "  NOTE: enable lingering so the guard survives logout (servers): sudo loginctl enable-linger $USER"
  fi
  log "  done. Status: systemctl --user list-timers | grep audit-reflog ; systemctl --user status audit-reflog-watch.service"
}
uninstall_linux() {
  systemctl --user disable --now audit-reflog.timer 2>/dev/null || true
  systemctl --user disable --now audit-reflog-watch.service 2>/dev/null || true
  for unit in audit-reflog.service audit-reflog.timer audit-reflog-watch.service; do
    rm -f "$USER_UNIT_DIR/$unit" && log "  removed $unit"
  done
  systemctl --user daemon-reload 2>/dev/null || true
}

case "$OS" in
  Darwin) [[ "$ACTION" == install ]] && install_macos || uninstall_macos ;;
  Linux)  [[ "$ACTION" == install ]] && install_linux || uninstall_linux ;;
  *) log "ERROR: unsupported OS '$OS'"; exit 1 ;;
esac

log "${ACTION} complete (${OS})."
