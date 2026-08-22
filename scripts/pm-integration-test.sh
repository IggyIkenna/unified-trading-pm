#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# PM Integration Test — verify all repos integrate with unified-trading-pm scripts.
#
# Uses the canonical integration test in PM: tests/integration/test_pm_scripts_integration.py
# For each repo: runs pytest with PROJECT_ROOT set. When PM scripts change, update the test
# in PM only — repos inherit the check via quality-gates (base-service runs it).
#
# Usage: bash scripts/pm-integration-test.sh [--repo NAME] [--full]
#   --repo NAME   Run for single repo only
#   --full        Also run quality-gates.sh --lint per repo (slower)
#
# Exit 0 if all pass; 1 on first failure.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_ROOT="$(dirname "$PM_ROOT")"
MANIFEST="${PM_ROOT}/workspace-manifest.json"
PM_INT_TEST="${PM_ROOT}/tests/integration/test_pm_scripts_integration.py"
SKIP_SETUP=false
SINGLE_REPO=""
FULL=false

for arg in "$@"; do
    case "$arg" in
        --full) FULL=true ;;
        --repo) SINGLE_REPO="NEXT" ;;
        *)
            [ "$SINGLE_REPO" = "NEXT" ] && SINGLE_REPO="$arg"
            ;;
    esac
done

get_repos() {
    python3 << PYINNER
import json
with open("$MANIFEST") as f:
    m = json.load(f)
for name in m.get("repositories", {}):
    print(name)
PYINNER
}

PYTHON_CMD="${PYTHON_CMD:-python3}"
FAILED=0
for repo in $(get_repos); do
    [ -n "$SINGLE_REPO" ] && [ "$repo" != "$SINGLE_REPO" ] && continue
    REPO_PATH="${WORKSPACE_ROOT}/${repo}"
    [ ! -d "$REPO_PATH" ] && echo "⚠️  Skip $repo (not found)" && continue

    echo -n "▶ $repo "
    cd "$REPO_PATH"

    if ! PROJECT_ROOT="$REPO_PATH" $PYTHON_CMD -m pytest "$PM_INT_TEST" -v -m integration --tb=line -q 2>/dev/null; then
        echo "❌ PM integration failed"
        FAILED=1
        continue
    fi

    if [ "$FULL" = true ]; then
        if ! bash scripts/quality-gates.sh --lint > /tmp/qg_out.txt 2>&1; then
            tail -5 /tmp/qg_out.txt
            echo "❌ $repo: quality-gates.sh --lint failed"
            FAILED=1
        else
            echo "✅ OK (lint)"
        fi
    else
        echo "✅ OK"
    fi
done

[ $FAILED -gt 0 ] && exit 1
exit 0
