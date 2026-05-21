#!/usr/bin/env bash
# verify-slot-host-symmetry.sh — does this host (operator laptop / VM / Harsh laptop)
# satisfy the local↔VM slot-host symmetry contract from CLAUDE.md § "Local slot host
# = VM slot host"?
#
# Returns exit 0 on full compliance, non-zero on any failure with a clear message.
#
# Checks:
#   1. slot-cron-ff-pull cron installed
#   2. slot-git-status-report cron installed
#   3. FF-pull log shows activity within last 10 min
#   4. git-status-report log shows activity within last 10 min
#   5. Last reporter post returned HTTP 200 (against $ORCH_URL)
#   6. ${WORKSPACE_ROOT}/.tabs/ exists with at least 1 slot worktree
#   7. ${ORCH_TOKEN_FILE:-$HOME/.orch_token} is readable
#
# Usage: bash unified-trading-pm/scripts/verify-slot-host-symmetry.sh
#        bash unified-trading-pm/scripts/verify-slot-host-symmetry.sh --quiet
#
# Used by:
#   - Operator on new-host setup (`bash scripts/verify-slot-host-symmetry.sh`)
#   - Harsh's migration recipe (Step 5 sanity check)
#   - CI (future — once we wire it into the workflow)
#
# Cross-platform: macOS + Linux. Uses POSIX-ish primitives only.

set -uo pipefail

QUIET=0
[[ "${1:-}" == "--quiet" ]] && QUIET=1

ORCH_URL="${ORCH_URL:-https://api.agent-orchestrator.odum-research.com}"
TOKEN_FILE="${ORCH_TOKEN_FILE:-${HOME}/.orch_token}"

# Auto-detect workspace root: climb cwd until we find unified-trading-system-repos
detect_workspace() {
    local d
    d="$(pwd)"
    while [[ "$(basename "${d}")" != "unified-trading-system-repos" && "${d}" != "/" ]]; do
        d="$(dirname "${d}")"
    done
    if [[ "${d}" == "/" ]]; then
        # Try the common defaults
        for c in "${HOME}/Code/unified-trading-system-repos" "/home/ubuntu/unified-trading-system-repos"; do
            [[ -d "$c" ]] && d="$c" && break
        done
    fi
    echo "${d}"
}

WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(detect_workspace)}"

FF_LOG=/tmp/slot-cron-ff-pull.log
GS_LOG=/tmp/slot-git-status-report.log

pass=0
fail=0

ok() { [[ ${QUIET} -eq 0 ]] && echo "  ✓ $1"; pass=$((pass+1)); }
bad() { echo "  ✗ $1" >&2; fail=$((fail+1)); }
section() { [[ ${QUIET} -eq 0 ]] && echo; [[ ${QUIET} -eq 0 ]] && echo "=== $1 ==="; }

section "host: $(hostname -s) | workspace: ${WORKSPACE_ROOT}"

# 1. FF-pull cron installed
if crontab -l 2>/dev/null | grep -q "slot-cron-ff-pull"; then
    ok "slot-cron-ff-pull cron installed"
else
    bad "slot-cron-ff-pull cron MISSING — see CLAUDE.md § Local slot host"
fi

# 2. git-status-report cron installed
if crontab -l 2>/dev/null | grep -q "slot-git-status-report"; then
    ok "slot-git-status-report cron installed"
else
    bad "slot-git-status-report cron MISSING"
fi

# 3. FF-pull log activity in last 10 min
if [[ -f "${FF_LOG}" ]]; then
    last_mtime=$(stat -c %Y "${FF_LOG}" 2>/dev/null || stat -f %m "${FF_LOG}" 2>/dev/null || echo 0)
    age_min=$(( ($(date +%s) - last_mtime) / 60 ))
    if [[ ${age_min} -le 10 ]]; then
        ok "FF-pull log fresh (${age_min}m ago)"
    else
        bad "FF-pull log STALE (${age_min}m ago — cron not running?)"
    fi
else
    bad "FF-pull log missing (${FF_LOG} — cron has never run?)"
fi

# 4. git-status-report log activity in last 10 min
if [[ -f "${GS_LOG}" ]]; then
    last_mtime=$(stat -c %Y "${GS_LOG}" 2>/dev/null || stat -f %m "${GS_LOG}" 2>/dev/null || echo 0)
    age_min=$(( ($(date +%s) - last_mtime) / 60 ))
    if [[ ${age_min} -le 10 ]]; then
        ok "git-status-report log fresh (${age_min}m ago)"
    else
        bad "git-status-report log STALE (${age_min}m ago)"
    fi
else
    bad "git-status-report log missing (${GS_LOG})"
fi

# 5. Last reporter post returned 200 (grep [ok] in recent log)
if [[ -f "${GS_LOG}" ]]; then
    if tail -50 "${GS_LOG}" | grep -qE "^\[[0-9:]+Z\] \[ok\] slot"; then
        ok "git-status reporter posted [ok] recently"
    else
        bad "git-status reporter has NO [ok] in last 50 lines (auth issue? backend down?)"
    fi
fi

# 6. Workspace .tabs/ exists with ≥1 slot worktree
if [[ -d "${WORKSPACE_ROOT}/.tabs" ]]; then
    slot_count=$(find "${WORKSPACE_ROOT}/.tabs" -maxdepth 1 -mindepth 1 -type d -regex '.*/[0-9]+' 2>/dev/null | wc -l | tr -d ' ')
    if [[ ${slot_count} -ge 1 ]]; then
        ok "${slot_count} slot worktree(s) under .tabs/"
    else
        bad "no numeric slot dirs under ${WORKSPACE_ROOT}/.tabs/"
    fi
else
    bad ".tabs/ missing at ${WORKSPACE_ROOT} — run setup-tab-worktrees.sh --init"
fi

# 7. Orch token readable
if [[ -r "${TOKEN_FILE}" ]]; then
    ok "orch token readable at ${TOKEN_FILE}"
else
    # try per-slot fallback
    fallback_found=""
    for slot_dir in "${WORKSPACE_ROOT}/.tabs"/*/; do
        if [[ -r "${slot_dir}.orch_token" ]]; then
            fallback_found="${slot_dir}.orch_token"
            break
        fi
    done
    if [[ -n "${fallback_found}" ]]; then
        ok "orch token readable via per-slot fallback (${fallback_found})"
    else
        bad "no orch token at ${TOKEN_FILE} or per-slot fallback (reporter will skip every slot)"
    fi
fi

# 8. Backend reachable
section "backend reachability"
if [[ -r "${TOKEN_FILE}" ]]; then
    TOKEN=$(cat "${TOKEN_FILE}")
    code=$(curl -sS -o /tmp/.symcheck.$$ -w '%{http_code}' \
        -H "Authorization: Bearer $TOKEN" \
        "${ORCH_URL}/api/mode" 2>/dev/null || echo "000")
    if [[ "$code" == "200" ]]; then
        mode=$(python3 -c 'import json, sys; print(json.load(sys.stdin).get("mode","?"))' < /tmp/.symcheck.$$ 2>/dev/null || echo "?")
        ok "backend reachable @ ${ORCH_URL} (mode=${mode})"
    else
        bad "backend HTTP ${code} @ ${ORCH_URL}/api/mode"
    fi
    rm -f /tmp/.symcheck.$$
fi

section "result: ${pass} passed / ${fail} failed"

if [[ ${fail} -gt 0 ]]; then
    [[ ${QUIET} -eq 0 ]] && cat <<EOF

This host is NOT fully compliant with the local↔VM slot-host symmetry contract.
See CLAUDE.md § "Local slot host = VM slot host — symmetric worker model".

To fix common issues:
  - Missing crons: see codex/12-agent-workflow/harsh-laptop-migration-2026-05-20.md Step 5
  - Missing token: ask Ikenna to issue one (or mint via auth.issue_token if on VM)
  - Backend unreachable: check that you can curl https://api.agent-orchestrator.odum-research.com/api/mode
  - Stale log: cron may be installed but failing — \`tail -30 /tmp/slot-cron-ff-pull.log\`
EOF
    exit 1
fi
exit 0
