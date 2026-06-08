#!/usr/bin/env bash
# Run audit-reflog-resets and show a desktop notification on high-risk findings.
# Cross-platform: macOS (terminal-notifier/osascript) + Linux (notify-send). Notifications +
# Telegram fire ONLY on high-risk (exit 1) — a clean run is silent on every channel.
# Scheduled by launchd (macOS) or systemd-user (Linux); also run manually to test.
# Install both via: scripts/repo-management/install-audit-reflog-guard.sh
#
# Location: unified-trading-pm/scripts/repo-management/run-audit-reflog-with-alert.sh
# Log:        /tmp/audit-reflog.log
#
# Notification: Click opens log, plays sound. To keep until acknowledged:
#   System Settings > Notifications > terminal-notifier > set to "Alerts"
#
# Run from: workspace root

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
LOG="/tmp/audit-reflog.log"

# Load Telegram credentials from .act-secrets if not already in env
ACT_SECRETS="$WORKSPACE_ROOT/.act-secrets"
if [[ -z "${TELEGRAM_BOT_TOKEN:-}" || -z "${TELEGRAM_CHAT_ID:-}" ]] && [[ -f "$ACT_SECRETS" ]]; then
  while IFS='=' read -r key val; do
    [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
    key="${key%%*( )}" val="${val##*( )}"
    case "$key" in
      TELEGRAM_BOT_TOKEN) export TELEGRAM_BOT_TOKEN="$val" ;;
      TELEGRAM_CHAT_ID)   export TELEGRAM_CHAT_ID="$val" ;;
    esac
  done < "$ACT_SECRETS"
fi

cd "$WORKSPACE_ROOT"
# Write each run to a temp file so extraction is always from the current run only
RUN_LOG=$(mktemp /tmp/audit-reflog-run.XXXXXX)
# Don't let set -e exit before we can show notification when audit finds high-risk (exit 1)
exit_code=0
bash "$SCRIPT_DIR/audit-reflog-resets.sh" 2>&1 | tee "$RUN_LOG" >> "$LOG" || exit_code=${PIPESTATUS[0]}

if [[ $exit_code -eq 1 ]]; then
  # Extract from current run only (RUN_LOG), not accumulated history
  SUMMARY=$(grep "^Summary:" "$RUN_LOG" | tail -1 || true)
  # Extract the HIGH RISK section: from "=== HIGH RISK" up to "=== MEDIUM RISK"
  HIGH_RISK=$(sed -n '/=== HIGH RISK/,/=== MEDIUM RISK/p' "$RUN_LOG" \
    | grep -v "^===" | grep -v "^$" | sed 's/^  //' | head -10 || true)

  # Desktop notification — cross-platform + BEST-EFFORT. Reached ONLY on high-risk (exit 1),
  # so success is always silent on every platform (no banner, no Telegram). Every call is
  # guarded `|| true` so a missing notifier under `set -e` can NEVER abort before the Telegram
  # alert below. macOS = terminal-notifier (full path; launchd has minimal PATH) else osascript;
  # Linux = notify-send (libnotify), with a DBUS fallback for SSH/headless sessions; a server
  # with no notifier just no-ops silently. SSOT: docs/audit-reflog-scheduled-job.md.
  notify_desktop() {
    local msg="High-risk reset(s) found. Check ${LOG}"
    case "$(uname -s)" in
      Darwin)
        local notifier=""
        for p in /opt/homebrew/bin/terminal-notifier /usr/local/bin/terminal-notifier; do
          [[ -x "$p" ]] && notifier="$p" && break
        done
        if [[ -n "$notifier" ]]; then
          "$notifier" -title "Audit Reflog" -message "${msg}" -sound default -execute "open $LOG" || true
        else
          osascript -e "display notification \"${msg}\" with title \"Audit Reflog\" sound name \"Basso\"" || true
        fi
        ;;
      Linux)
        if command -v notify-send >/dev/null 2>&1; then
          # Headless/SSH: point libnotify at the user's session bus if not already set.
          [[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" && -S "/run/user/$(id -u)/bus" ]] \
            && export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
          notify-send -u critical "Audit Reflog — High Risk" "${msg}" >/dev/null 2>&1 || true
        fi
        ;;
    esac
    return 0
  }
  notify_desktop

  # Telegram notification
  if [[ -n "${TELEGRAM_BOT_TOKEN:-}" && -n "${TELEGRAM_CHAT_ID:-}" ]]; then
    MSG="🚨 *Audit Reflog — High Risk*%0A%0A${SUMMARY}%0A%0A\`\`\`%0A${HIGH_RISK}%0A\`\`\`%0A%0ASee \`/tmp/audit-reflog.log\` for full report."
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d chat_id="${TELEGRAM_CHAT_ID}" \
      -d text="${MSG}" \
      -d parse_mode="Markdown" > /dev/null
  fi
fi

rm -f "$RUN_LOG"
exit $exit_code
