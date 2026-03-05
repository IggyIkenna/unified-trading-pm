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

cd "$WORKSPACE_ROOT"
# Don't let set -e exit before we can show notification when audit finds high-risk (exit 1)
exit_code=0
bash "$SCRIPT_DIR/audit-reflog-resets.sh" >> "$LOG" 2>&1 || exit_code=$?

if [[ $exit_code -eq 1 ]]; then
  # Use full path — launchd has minimal PATH and won't find terminal-notifier
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
fi

exit $exit_code
