#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Telegram notification helpers with GitHub Issue fallback (add-secondary-notification-channel).
# Usage: source scripts/telegram-helpers.sh
# Requires: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GH_PAT (for GH Issue fallback), GITHUB_REPOSITORY_OWNER

send_telegram() {
    # send_telegram <message> — best-effort, never exits non-zero
    local msg="$1"
    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_CHAT_ID}" \
            -d text="$msg" \
            -d parse_mode="HTML" \
            > /dev/null 2>&1 || echo "⚠ Telegram send failed (non-fatal)" >&2
    else
        echo "⚠ Telegram not configured (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set)" >&2
    fi
}

notify_critical() {
    # notify_critical <title> <body> — sends to Telegram AND creates GH Issue fallback
    # Use for: SIT failures, T0 failures, conflict agent timeouts, Claude API auth errors, manifest corruption
    local title="$1"
    local body="${2:-$1}"

    # Primary: Telegram
    send_telegram "🚨 CRITICAL: ${title}%0A${body}" || true

    # Fallback: GitHub Issue (ensures visibility even during Telegram outage)
    if [ -n "${GH_PAT:-}" ] && [ -n "${GITHUB_REPOSITORY_OWNER:-}" ]; then
        curl -s -X POST \
            -H "Authorization: token ${GH_PAT}" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/repos/${GITHUB_REPOSITORY_OWNER}/unified-trading-pm/issues" \
            -d "{\"title\": \"ALERT: ${title}\", \"body\": \"${body}\", \"labels\": [\"critical-alert\"]}" \
            > /dev/null 2>&1 || echo "⚠ GH Issue fallback also failed" >&2
    fi
}
