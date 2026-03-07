#!/usr/bin/env bash
# Run audit-reflog-resets and show macOS notification on high-risk findings.
# Used by launchd for weekly scheduled runs. Also run manually to test.
#
# Location: unified-trading-pm/scripts/repo-management/run-audit-reflog-with-alert.sh
# Cancel job: launchctl unload ~/Library/LaunchAgents/com.unified-trading.audit-reflog.plist
# Start job:  launchctl load ~/Library/LaunchAgents/com.unified-trading.audit-reflog.plist
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

  # macOS notification — Use full path (launchd has minimal PATH)
  NOTIFIER=""
  for p in /opt/homebrew/bin/terminal-notifier /usr/local/bin/terminal-notifier; do
    [[ -x "$p" ]] && NOTIFIER="$p" && break
  done
  if [[ -n "$NOTIFIER" ]]; then
    "$NOTIFIER" -title "Audit Reflog" \
      -message "High-risk reset(s) found. Click to open log." \
      -sound default \
      -execute "open $LOG"
  else
    osascript -e "display notification \"High-risk reset(s) found. Check $LOG\" with title \"Audit Reflog\" sound name \"Basso\""
  fi

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
