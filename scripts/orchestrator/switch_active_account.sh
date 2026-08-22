#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# switch_active_account.sh — write the active-account sidecar.
#
# Phase 4a/4b of orchestrator_master.md r3. Replacement for
# swap_claude_account.sh (which copied .credentials.json between files — the
# wrong mechanism per the SSOT, causes refresh-token-rotation lockouts).
#
# Under the long-lived-token architecture (see
# codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md), each
# account's CLAUDE_CODE_OAUTH_TOKEN lives in its own env file at
# ~/.claude-accounts/<account_id>.env. The orchestrator's tmux_spawn.py
# sources the right file before exec claude — no file-copy involved.
#
# This script just records WHICH account_id is currently considered "active"
# in ~/.claude/.active_account so any helper code (e.g. claude /usage probe
# in usage_poller) can route to the right env file.
#
# Usage:
#   bash switch_active_account.sh sub-a-ikenna
#   bash switch_active_account.sh sub-b-iggy2london
#
# Does NOT bounce running workers. Each worker continues on whatever token
# its env was sourced with at spawn time. Rotation only affects FUTURE spawns
# (which is the correct behavior — switching mid-session doesn't actually
# affect claude's in-memory auth state).
#
# Telegram alert: emits an account_swap notification via the orchestrator's
# /api/accounts/{id}/switch-active endpoint if reachable, else just logs locally.

set -euo pipefail

if [[ -z "${1:-}" ]]; then
    echo "Usage: $0 <account_id>" >&2
    echo "Example: $0 sub-a-ikenna" >&2
    exit 2
fi

NEW_ACCOUNT="$1"
ENV_FILE="${HOME}/.claude-accounts/${NEW_ACCOUNT}.env"
SIDECAR="${HOME}/.claude/.active_account"
LOG_FILE="/tmp/account_swaps.log"

if [[ ! -f "${ENV_FILE}" ]]; then
    echo "ERROR: ${ENV_FILE} does not exist." >&2
    echo "Operator: generate the token via \`claude setup-token\` on a browser machine," >&2
    echo "then write it to ${ENV_FILE} with shape:" >&2
    echo "  unset ANTHROPIC_API_KEY" >&2
    echo "  export CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-..." >&2
    echo "  export CLAUDE_ACCOUNT_LABEL=${NEW_ACCOUNT}" >&2
    exit 1
fi

# Verify the env file looks right
if ! grep -q "unset ANTHROPIC_API_KEY" "${ENV_FILE}"; then
    echo "WARNING: ${ENV_FILE} missing 'unset ANTHROPIC_API_KEY' line." >&2
    echo "Without it, if ANTHROPIC_API_KEY is inherited from a parent shell," >&2
    echo "billing silently flips to metered API instead of Max subscription." >&2
    echo "Continuing anyway, but fix the env file." >&2
fi
if ! grep -q "CLAUDE_CODE_OAUTH_TOKEN" "${ENV_FILE}"; then
    echo "ERROR: ${ENV_FILE} doesn't set CLAUDE_CODE_OAUTH_TOKEN. Won't auth." >&2
    exit 1
fi

# Record the new active account
PREV_ACCOUNT="$(cat "${SIDECAR}" 2>/dev/null || echo unknown)"
mkdir -p "$(dirname "${SIDECAR}")"
echo -n "${NEW_ACCOUNT}" > "${SIDECAR}"
chmod 600 "${SIDECAR}"

# Audit log
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "[${TS}] ACCOUNT SWITCH ${PREV_ACCOUNT} → ${NEW_ACCOUNT}" >> "${LOG_FILE}"

# Direct Telegram alert if creds available (so operator sees the swap even when orch down)
if [[ -n "${TELEGRAM_BOT_TOKEN:-}" && -n "${TELEGRAM_CHAT_ID:-}" ]]; then
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d "chat_id=${TELEGRAM_CHAT_ID}" \
        --data-urlencode "text=🔄 Active account switched: ${PREV_ACCOUNT} → ${NEW_ACCOUNT} on $(hostname) at ${TS}" \
        > /dev/null 2>&1 || true
fi

echo "Active account switched: ${PREV_ACCOUNT} → ${NEW_ACCOUNT}"
echo "Future spawns will source ${ENV_FILE}."
echo "Existing workers continue on their original tokens (will rotate on next spawn)."
