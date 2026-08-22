#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# send-telegram-rate-limited.sh — Rate-limited Telegram alert sender.
# Max 1 alert per workflow per 60s. Uses a temp file to track last send time.
#
# Usage:
#   source scripts/agents/send-telegram-rate-limited.sh
#   send_telegram_rate_limited "workflow-name" "Message text here"
#
# Requires env vars:
#   TELEGRAM_BOT_TOKEN — Bot token
#   TELEGRAM_CHAT_ID   — Target chat ID
#
# Optional env vars:
#   TELEGRAM_RATE_LIMIT_SECONDS — Override default 60s rate limit
#
# Returns:
#   0 = message sent (or Telegram not configured)
#   1 = rate-limited (message suppressed)

set -euo pipefail

send_telegram_rate_limited() {
  local workflow_name="${1:?Usage: send_telegram_rate_limited <workflow_name> <message>}"
  local message="${2:?Usage: send_telegram_rate_limited <workflow_name> <message>}"
  local rate_limit="${TELEGRAM_RATE_LIMIT_SECONDS:-60}"
  local parse_mode="${3:-Markdown}"

  # Skip if Telegram not configured
  if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
    echo "[telegram-rate-limit] Telegram not configured — skipping"
    return 0
  fi

  # Sanitize workflow name for use as filename
  local safe_name
  safe_name=$(echo "$workflow_name" | tr '[:upper:]' '[:lower:]' | sed 's|[^a-z0-9_-]|_|g')
  local stamp_file="/tmp/telegram_rate_limit_${safe_name}.stamp"

  # Check if we're within the rate limit window
  if [ -f "$stamp_file" ]; then
    local last_sent
    last_sent=$(cat "$stamp_file" 2>/dev/null || echo "0")
    local now
    now=$(date +%s)
    local elapsed=$((now - last_sent))

    if [ "$elapsed" -lt "$rate_limit" ]; then
      echo "[telegram-rate-limit] Suppressed for ${workflow_name}: ${elapsed}s < ${rate_limit}s since last alert"
      return 1
    fi
  fi

  # Send the message
  local http_status
  http_status=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    -d "text=${message}" \
    -d "parse_mode=${parse_mode}" 2>/dev/null || echo "000")

  if [ "$http_status" = "200" ]; then
    # Record timestamp of successful send
    date +%s > "$stamp_file"
    echo "[telegram-rate-limit] Sent for ${workflow_name} (HTTP ${http_status})"
    return 0
  else
    echo "[telegram-rate-limit] Failed for ${workflow_name} (HTTP ${http_status})"
    return 0  # Don't fail the workflow on Telegram errors
  fi
}
