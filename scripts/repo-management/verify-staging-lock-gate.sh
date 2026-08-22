#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Verify that staging-lock-gate is a required status check on every T0-T3 repo's staging branch.
# Usage: bash scripts/repo-management/verify-staging-lock-gate.sh [--fix]
# Options: --fix  — attempt to add missing required check via gh api
set -euo pipefail

FIX_MODE=false
for arg in "$@"; do
    [[ "$arg" == "--fix" ]] && FIX_MODE=true
done

OWNER="${GITHUB_REPOSITORY_OWNER:-IggyIkenna}"
MANIFEST="workspace-manifest.json"

if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: $MANIFEST not found — run from PM repo root" >&2
    exit 1
fi

FAILED=()
MISSING=()
PASSED=()

# Extract repos with arch_tier T0-T3 from manifest
REPOS=$(python3 - <<'PYEOF'
import json, sys
with open("workspace-manifest.json") as f:
    manifest = json.load(f)
repos = manifest.get("repositories", {})
for repo, info in repos.items():
    if isinstance(info, dict) and info.get("arch_tier") in ["T0", "T1", "T2", "T3"]:
        print(repo)
PYEOF
)

for repo in $REPOS; do
    protection=$(gh api "repos/${OWNER}/${repo}/branches/staging/protection/required_status_checks" \
        --jq '.contexts[]' 2>/dev/null || echo "")

    if echo "$protection" | grep -q "staging-lock-gate"; then
        PASSED+=("$repo")
        echo "✓ $repo: staging-lock-gate present"
    else
        MISSING+=("$repo")
        echo "✗ $repo: staging-lock-gate MISSING" >&2

        if [ "$FIX_MODE" = true ]; then
            # Get current required checks to append (not replace)
            current_checks=$(gh api "repos/${OWNER}/${repo}/branches/staging/protection/required_status_checks" \
                --jq '[.contexts[]]' 2>/dev/null || echo "[]")
            new_checks=$(python3 -c "
import json, sys
checks = json.loads('${current_checks}')
if 'staging-lock-gate' not in checks:
    checks.append('staging-lock-gate')
print(json.dumps(checks))
")
            gh api --method PATCH \
                "repos/${OWNER}/${repo}/branches/staging/protection/required_status_checks" \
                --input - <<< "{\"strict\": false, \"contexts\": ${new_checks}}" \
                && echo "  → Added staging-lock-gate to $repo" \
                || { echo "  → Failed to add staging-lock-gate to $repo" >&2; FAILED+=("$repo"); }
        fi
    fi
done

echo ""
echo "Summary: ${#PASSED[@]} repos OK, ${#MISSING[@]} repos missing staging-lock-gate"
if [ "${#FAILED[@]}" -gt 0 ]; then
    echo "Failed to fix: ${FAILED[*]}" >&2
    exit 1
fi
if [ "${#MISSING[@]}" -gt 0 ] && [ "$FIX_MODE" = false ]; then
    echo "Run with --fix to automatically add the required check."
    exit 1
fi
