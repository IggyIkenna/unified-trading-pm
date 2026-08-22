#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Repository dispatch helpers with retry and Telegram alerting.
# Usage: source scripts/dispatch-helpers.sh (requires GH_PAT, OWNER, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID in env)
# Functions: dispatch_with_retry, dispatch_to_all

dispatch_with_retry() {
    # dispatch_with_retry <repo> <event_type> <payload_json>
    # Returns 0 on 204 success, 1 after 3 failed attempts (sends TG alert).
    local repo="$1"
    local event_type="$2"
    local payload="${3:-{}}"
    local attempt

    for attempt in 1 2 3; do
        local http_code
        http_code=$(curl -s -o /tmp/dispatch_resp_"${repo//\//-}".txt -w "%{http_code}" \
            -X POST \
            -H "Authorization: token ${GH_PAT}" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/repos/${OWNER}/${repo}/dispatches" \
            -d "$payload" 2>/dev/null || echo "000")

        if [ "$http_code" = "204" ]; then
            echo "✓ dispatch $event_type → $repo (attempt $attempt)"
            return 0
        fi
        echo "⚠ dispatch $event_type → $repo attempt $attempt failed (HTTP $http_code)" >&2
        if [ "$attempt" -lt 3 ]; then
            sleep $((attempt * 5))
        fi
    done

    # All 3 attempts failed — alert
    local resp
    resp=$(cat /tmp/dispatch_resp_"${repo//\//-}".txt 2>/dev/null | head -c 200 || true)
    echo "❌ dispatch $event_type → $repo failed after 3 attempts: $resp" >&2
    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_CHAT_ID}" \
            -d text="❌ Dispatch FAILED%0AEvent: ${event_type}%0ARepo: ${repo}%0AOwner: ${OWNER}%0AResponse: ${resp}" \
            > /dev/null 2>&1 || true
    fi
    return 1
}

dispatch_to_all() {
    # dispatch_to_all <event_type> <payload_json> <repo1> [repo2 ...]
    # Dispatches to all repos, collects failures, alerts if any fail.
    local event_type="$1"
    local payload="$2"
    shift 2
    local repos=("$@")
    local failed=()

    for repo in "${repos[@]}"; do
        dispatch_with_retry "$repo" "$event_type" "$payload" || failed+=("$repo")
    done

    if [ "${#failed[@]}" -gt 0 ]; then
        echo "❌ dispatch_to_all: ${#failed[@]} repos did not receive $event_type: ${failed[*]}" >&2
        if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
            local failed_str="${failed[*]}"
            curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
                -d chat_id="${TELEGRAM_CHAT_ID}" \
                -d text="❌ Bulk dispatch FAILED%0AEvent: ${event_type}%0AFailed repos (${#failed[@]}): ${failed_str// /, }%0AManual retry required." \
                > /dev/null 2>&1 || true
        fi
        return 1
    fi
    echo "✓ dispatch_to_all: $event_type sent to ${#repos[@]} repos"
    return 0
}
