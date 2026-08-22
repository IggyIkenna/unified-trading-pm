#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# telegram-rate-limit.sh — Manifest-based Telegram rate-limit guard.
#
# Checks `telegram_last_alert_ts` map in workspace-manifest.json.
# Max 1 alert per workflow per 60s. If within cooldown, skip sending.
# Updates the timestamp in the manifest after a successful send.
#
# Usage:
#   source scripts/telegram-rate-limit.sh
#   telegram_rate_limited_send "workflow-name" "Message text"
#
# Requires env vars:
#   TELEGRAM_BOT_TOKEN — Bot token
#   TELEGRAM_CHAT_ID   — Target chat ID
#
# Optional env vars:
#   TELEGRAM_COOLDOWN_SECONDS — Override default 60s cooldown
#   MANIFEST_PATH             — Override default workspace-manifest.json path
#
# Returns:
#   0 = message sent (or Telegram not configured)
#   1 = rate-limited (message suppressed)
#   2 = send failed (non-fatal)

# Guard against double-sourcing
if [ -n "${_TELEGRAM_RATE_LIMIT_LOADED:-}" ]; then
  return 0 2>/dev/null || true
fi
_TELEGRAM_RATE_LIMIT_LOADED=1

telegram_rate_limited_send() {
  local workflow_name="${1:?Usage: telegram_rate_limited_send <workflow_name> <message>}"
  local message="${2:?Usage: telegram_rate_limited_send <workflow_name> <message>}"
  local parse_mode="${3:-Markdown}"
  local cooldown="${TELEGRAM_COOLDOWN_SECONDS:-60}"
  local manifest="${MANIFEST_PATH:-workspace-manifest.json}"

  # Skip if Telegram not configured
  if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
    echo "[telegram-rate-limit] Telegram not configured — skipping"
    return 0
  fi

  # Check if manifest exists
  if [ ! -f "$manifest" ]; then
    echo "[telegram-rate-limit] Manifest not found at $manifest — sending without rate limit"
    _trl_send_message "$message" "$parse_mode"
    return $?
  fi

  # Read last alert timestamp for this workflow from manifest
  local now_ts
  now_ts=$(date +%s)

  local last_ts
  last_ts=$(python3 -c "
import json, sys
try:
    with open('${manifest}') as f:
        m = json.load(f)
    ts = m.get('telegram_last_alert_ts', {}).get('${workflow_name}', 0)
    print(int(ts))
except Exception:
    print('0')
" 2>/dev/null || echo "0")

  local elapsed=$((now_ts - last_ts))

  if [ "$elapsed" -lt "$cooldown" ]; then
    echo "[telegram-rate-limit] Suppressed for ${workflow_name}: ${elapsed}s < ${cooldown}s cooldown"
    return 1
  fi

  # Send the message
  if _trl_send_message "$message" "$parse_mode"; then
    # Update timestamp in manifest (atomic: tmp + rename)
    python3 -c "
import json, os

manifest_path = '${manifest}'
workflow = '${workflow_name}'
ts = ${now_ts}

with open(manifest_path) as f:
    m = json.load(f)

if 'telegram_last_alert_ts' not in m:
    m['telegram_last_alert_ts'] = {}

m['telegram_last_alert_ts'][workflow] = ts

tmp_path = manifest_path + '.tmp'
with open(tmp_path, 'w') as f:
    json.dump(m, f, indent=2, ensure_ascii=False)
    f.write('\n')
os.replace(tmp_path, manifest_path)
" 2>/dev/null || echo "[telegram-rate-limit] WARNING: failed to update manifest timestamp" >&2

    echo "[telegram-rate-limit] Sent for ${workflow_name}, updated manifest timestamp"
    return 0
  else
    echo "[telegram-rate-limit] Send failed for ${workflow_name}"
    return 2
  fi
}

_trl_send_message() {
  local message="$1"
  local parse_mode="${2:-Markdown}"

  local http_status
  http_status=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    -d "text=${message}" \
    -d "parse_mode=${parse_mode}" 2>/dev/null || echo "000")

  if [ "$http_status" = "200" ]; then
    return 0
  else
    echo "[telegram-rate-limit] HTTP ${http_status}" >&2
    return 1
  fi
}
