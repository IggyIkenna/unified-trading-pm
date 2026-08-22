#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# §3 — Security
# Checks: hardcoded secrets, verify=False, AUTH_FAILURE, SECRET_ACCESSED/CONFIG_CHANGED.
# Usage: bash unified-trading-pm/scripts/audit/s03-security.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$SCRIPT_DIR/lib.sh"
cd "$WORKSPACE_ROOT"

echo "=== §3 Security ==="

# Hardcoded credentials (value ≥20 chars after = sign, not in tests)
hardcoded=$(rg '(api_key|secret_key|password|token)\s*=\s*["\x27][a-zA-Z0-9+/]{20,}' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' --glob '!**/test_*' \
  --glob '!**/fixtures/**' \
  -n 2>/dev/null || true)
pass_if_empty "§3" "no hardcoded secrets in prod source" "$hardcoded"

# verify=False in HTTP clients (production only)
verify_false=$(rg 'verify\s*=\s*False' --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' --glob '!**/test_*' \
  -n 2>/dev/null || true)
pass_if_empty "§3" "no verify=False in HTTP clients" "$verify_false"

# AUTH_FAILURE event in API services (should be present — warn if absent)
auth_failure_repos=$(rg 'AUTH_FAILURE' --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  -l 2>/dev/null | wc -l | tr -d ' ')
if [ "$auth_failure_repos" -ge 2 ]; then
  emit "§3" "AUTH_FAILURE event logged in API services" "PASS" \
    "$auth_failure_repos repos emit AUTH_FAILURE"
else
  emit "§3" "AUTH_FAILURE event logged in API services" "FAIL" \
    "only $auth_failure_repos repos — execution-service and alerting-service both required"
fi

# SECRET_ACCESSED event (should exist somewhere)
secret_accessed=$(rg 'SECRET_ACCESSED|CONFIG_CHANGED' --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  -l 2>/dev/null | wc -l | tr -d ' ')
if [ "$secret_accessed" -ge 1 ]; then
  emit "§3" "SECRET_ACCESSED / CONFIG_CHANGED events wired" "PASS" \
    "$secret_accessed repos"
else
  emit "§3" "SECRET_ACCESSED / CONFIG_CHANGED events wired" "WARN" \
    "no files found — check execution-service and alerting-service"
fi

# DISABLE_AUTH flag — should not appear in non-test production paths
disable_auth=$(rg 'DISABLE_AUTH' --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' --glob '!**/test_*' \
  -n 2>/dev/null || true)
if [ -z "$disable_auth" ]; then
  emit "§3" "DISABLE_AUTH absent from prod source" "PASS" "none"
else
  count=$(echo "$disable_auth" | wc -l | tr -d ' ')
  emit "§3" "DISABLE_AUTH absent from prod source" "WARN" \
    "$count hits — verify each is behind feature-flag guard: $(echo "$disable_auth" | head -1)"
fi

audit_summary
