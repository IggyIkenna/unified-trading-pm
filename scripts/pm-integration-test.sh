#!/usr/bin/env bash
# PM Integration Test — verify setup scripts and quality gates work for all repos.
#
# For each repo in workspace-manifest.json:
#   1. cd $repo && bash scripts/setup.sh (or setup-workspace-from-manifest.sh for workspace-level)
#   2. Verify expected files exist: scripts/quality-gates.sh, scripts/setup.sh
#   3. Run bash scripts/quality-gates.sh --lint (fast path) — must pass
#
# Usage: bash scripts/pm-integration-test.sh [--repo NAME] [--skip-setup]
#   --repo NAME   Run for single repo only
#   --skip-setup  Skip setup.sh (assume already run)
#
# Exit 0 if all pass; 1 on first failure (reports which repo/step failed).

set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MANIFEST="${REPO_ROOT}/unified-trading-pm/workspace-manifest.json"
SKIP_SETUP=false
SINGLE_REPO=""

for arg in "$@"; do
    case "$arg" in
        --skip-setup) SKIP_SETUP=true ;;
        --repo) SINGLE_REPO="NEXT" ;;
        *)
            if [ "$SINGLE_REPO" = "NEXT" ]; then
                SINGLE_REPO="$arg"
            fi
            ;;
    esac
done

get_repos() {
    python3 -c "
import json
with open('$MANIFEST') as f:
    m = json.load(f)
for name in m.get('repositories', {}):
    print(name)
"
}

FAILED=0
for repo in $(get_repos); do
    [ -n "$SINGLE_REPO" ] && [ "$repo" != "$SINGLE_REPO" ] && continue
    REPO_PATH="${REPO_ROOT}/${repo}"
    [ ! -d "$REPO_PATH" ] && echo "⚠️  Skip $repo (not found)" && continue

    echo "▶ $repo"
    cd "$REPO_PATH"

    # Step 1: Verify required files
    if [ ! -f "scripts/quality-gates.sh" ]; then
        echo "❌ $repo: missing scripts/quality-gates.sh"
        FAILED=1
        continue
    fi
    [ ! -f "scripts/setup.sh" ] && [ "$SKIP_SETUP" = false ] && echo "⚠️  $repo: missing scripts/setup.sh"

    # Step 2: Run setup (optional)
    if [ "$SKIP_SETUP" = false ] && [ -f "scripts/setup.sh" ]; then
        if ! bash scripts/setup.sh > /tmp/setup_out.txt 2>&1; then
            tail -5 /tmp/setup_out.txt
            echo "❌ $repo: setup.sh failed"
            FAILED=1
            continue
        fi
    fi

    # Step 3: Run quality gates --lint (fast path)
    if ! bash scripts/quality-gates.sh --lint > /tmp/qg_out.txt 2>&1; then
        tail -5 /tmp/qg_out.txt
        echo "❌ $repo: quality-gates.sh --lint failed"
        FAILED=1
    else
        echo "✅ $repo OK"
    fi
done

[ $FAILED -gt 0 ] && exit 1
exit 0
