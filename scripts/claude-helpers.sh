#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# claude-helpers.sh — Unified error classification and Telegram notification for Claude API errors.
#
# Usage (source this file, then call the function):
#   source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/claude-helpers.sh"
#   classify_claude_error /tmp/claude_err.txt cicd instruments-service staging
#   EXIT_CODE=$?
#   # 0 = service_down (graceful skip), 1 = auth_error (rotate key), 2 = rate_limited (retry)
#
# Required environment variables when calling classify_claude_error:
#   TELEGRAM_BOT_TOKEN    — Telegram bot token (optional; skip TG if unset)
#   TELEGRAM_CHAT_ID      — Telegram chat ID (optional)
#
# classify_claude_error(stderr_file, tier, repo, context)
#   stderr_file : path to file containing Claude CLI stderr output
#   tier        : cicd | syshealth | analysis
#   repo        : repository name (e.g. instruments-service)
#   context     : operation context (e.g. preflight, conflict-resolution, agent-audit)
#
# Exports:
#   CLAUDE_ERROR_CLASS — auth_error | rate_limited | service_down | timeout | unknown
#   CLAUDE_ERROR_MSG   — human-readable summary
#
# Return codes:
#   0 — service_down:  graceful skip, exit 0 (no pipeline failure)
#   1 — auth_error:    key invalid/expired, exit 1 (must rotate)
#   2 — rate_limited:  rate-limited/overloaded, exit 2 (retry with backoff)
#   3 — timeout:       job timeout, exit 1 (treated as failure)
#   4 — unknown:       unclassified error, exit 1

classify_claude_error() {
    local stderr_file="${1:-/dev/null}"
    local tier="${2:-unknown}"
    local repo="${3:-unknown}"
    local context="${4:-unknown}"

    export CLAUDE_ERROR_CLASS="unknown"
    export CLAUDE_ERROR_MSG=""

    # Read stderr (truncate to 500 chars for Telegram safety)
    local raw_stderr=""
    if [ -f "$stderr_file" ]; then
        raw_stderr=$(head -c 500 "$stderr_file" 2>/dev/null || true)
    fi

    # ── Classify by HTTP status code / keyword ───────────────────────────────
    if echo "$raw_stderr" | grep -qiE '401|403|unauthorized|invalid.*api.*key|api key.*invalid|authentication.*fail'; then
        CLAUDE_ERROR_CLASS="auth_error"
        CLAUDE_ERROR_MSG="API key invalid or expired (401/403). Rotate ANTHROPIC_API_KEY_${tier^^} immediately. No retry."
        _tg_claude_alert "⛔" "Auth Error — rotate key" "$tier" "$repo" "$context" "$CLAUDE_ERROR_MSG"
        return 1

    elif echo "$raw_stderr" | grep -qiE '429|529|rate.limit|too.many.requests|overload|capacity'; then
        CLAUDE_ERROR_CLASS="rate_limited"
        CLAUDE_ERROR_MSG="Rate limited / model overloaded (429/529). Will retry with backoff."
        _tg_claude_alert "⚠️" "Rate Limited — retrying" "$tier" "$repo" "$context" "$CLAUDE_ERROR_MSG"
        return 2

    elif echo "$raw_stderr" | grep -qiE '503|502|connection.refused|service.unavailable|unreachable|network.*error|timeout.*connect'; then
        CLAUDE_ERROR_CLASS="service_down"
        CLAUDE_ERROR_MSG="Claude API unreachable (503/connection refused). Check status.anthropic.com. Graceful skip — no pipeline failure."
        _tg_claude_alert "🔴" "Claude Unreachable — graceful skip" "$tier" "$repo" "$context" "$CLAUDE_ERROR_MSG"
        return 0

    elif [ "${CLAUDE_TIMEOUT_FIRED:-false}" = "true" ]; then
        CLAUDE_ERROR_CLASS="timeout"
        CLAUDE_ERROR_MSG="Agent job timed out. Repo: $repo. Context: $context."
        _tg_claude_alert "⏰" "Agent Timeout" "$tier" "$repo" "$context" "$CLAUDE_ERROR_MSG"
        return 3

    else
        CLAUDE_ERROR_CLASS="unknown"
        # Include first 200 chars of stderr for triage
        local excerpt
        excerpt=$(echo "$raw_stderr" | head -c 200 | tr '\n' ' ')
        CLAUDE_ERROR_MSG="Unknown Claude error. Excerpt: ${excerpt}"
        _tg_claude_alert "❓" "Unknown Claude Error" "$tier" "$repo" "$context" "$CLAUDE_ERROR_MSG"
        return 4
    fi
}

# ── Internal: send Telegram alert ────────────────────────────────────────────
_tg_claude_alert() {
    local emoji="$1"
    local title="$2"
    local tier="$3"
    local repo="$4"
    local context="$5"
    local msg="$6"

    if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
        echo "[claude-helpers] TG not configured — skipping alert: $title"
        return 0
    fi

    local text
    text="${emoji} *Claude API — ${title}*
Tier: \`${tier}\`
Repo: \`${repo}\`
Context: \`${context}\`
Error class: \`${CLAUDE_ERROR_CLASS}\`
${msg}"

    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_CHAT_ID}" \
        -d text="${text}" \
        -d parse_mode="Markdown" > /dev/null 2>&1 || true
}

# ── claude_preflight: run a quick API ping, classify on failure ───────────────
# Usage:
#   claude_preflight cicd instruments-service preflight
#   Returns same exit codes as classify_claude_error.
#   On service_down (exit 0): caller should skip gracefully.
#   On auth_error (exit 1): caller should fail job.
claude_preflight() {
    local tier="${1:-unknown}"
    local repo="${2:-unknown}"
    local context="${3:-preflight}"
    local err_file
    err_file=$(mktemp)

    echo "[claude-helpers] Running Claude API preflight ping (tier=$tier, repo=$repo)..."

    if timeout 30 claude --print "ping: respond with exactly the word OK" \
        2>"$err_file" | grep -qi "ok"; then
        echo "[claude-helpers] Claude API: healthy ✅"
        rm -f "$err_file"
        return 0
    fi

    echo "[claude-helpers] Claude API preflight failed. Classifying..."
    classify_claude_error "$err_file" "$tier" "$repo" "$context"
    local code=$?
    rm -f "$err_file"
    return $code
}
