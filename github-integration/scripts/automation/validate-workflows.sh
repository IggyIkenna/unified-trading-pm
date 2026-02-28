#!/usr/bin/env bash
#
# Validate GitHub Actions workflow syntax
#
# Checks for common YAML errors that cause workflow validation failures:
# - Duplicate run: keys in a single step
# - Empty steps (- name: with no run:)
#
# Usage:
#   bash validate-workflows.sh [repo-path]  # Check specific repo
#   bash validate-workflows.sh --all        # Check all repos in workspace

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"

check_workflow() {
    local workflow_file="$1"
    local repo_name="$(basename "$(dirname "$(dirname "$(dirname "$workflow_file")")")")"

    if [ ! -f "$workflow_file" ]; then
        return 0  # No workflow file, nothing to check
    fi

    echo -n "🔍 Checking $repo_name... "

    local has_errors=false

    # Check 1: Duplicate run: keys in a single step
    # Pattern: A step with a run: followed by blank line and another run:
    if awk '
        /^      - name:/ { in_step=1; run_count=0; next }
        in_step && /^        run:/ { run_count++; if (run_count > 1) { print "Line " NR ": Duplicate run: in step"; exit 1 } }
        in_step && /^      [^ ]/ { in_step=0 }
    ' "$workflow_file"; then
        :  # No error
    else
        echo ""
        echo "  ❌ ERROR: Duplicate run: keys detected"
        echo "     A step can only have ONE run: block"
        echo "     Fix: Split into separate steps or use multi-line run: |"
        has_errors=true
    fi

    # Check 2: Empty steps (name without run:, uses:, etc.)
    if grep -Pzo '- name:[^\n]*\n\n      - name:' "$workflow_file" >/dev/null 2>&1; then
        if [ "$has_errors" = false ]; then
            echo ""
        fi
        echo "  ⚠️  WARNING: Empty step detected (- name: with no run: or uses:)"
        has_errors=true
    fi

    # Check 3: run: at wrong indentation level (orphaned from step)
    if grep -n '^        run:' "$workflow_file" | grep -v '^        run: |' >/dev/null 2>&1; then
        local line_nums=$(grep -n '^        run:' "$workflow_file" | grep -v '^        run: |' | cut -d: -f1)
        if [ "$has_errors" = false ]; then
            echo ""
        fi
        echo "  ⚠️  WARNING: Possible orphaned run: at lines: $line_nums"
        echo "     Check if these belong to a step above"
        has_errors=true
    fi

    if [ "$has_errors" = false ]; then
        echo "✅"
        return 0
    else
        echo ""
        echo "  📝 File: $workflow_file"
        echo ""
        return 1
    fi
}

main() {
    if [ $# -eq 0 ]; then
        echo "Usage: $0 [repo-path|--all]"
        exit 1
    fi

    echo "🔍 Validating GitHub Actions workflows"
    echo ""

    local error_count=0

    if [ "$1" = "--all" ]; then
        # Check all repos in workspace
        for repo_dir in "$WORKSPACE_ROOT"/*/; do
            workflow="$repo_dir/.github/workflows/quality-gates.yml"
            if [ -f "$workflow" ]; then
                if ! check_workflow "$workflow"; then
                    ((error_count++))
                fi
            fi
        done
    else
        # Check specific repo
        repo_path="$1"
        workflow="$repo_path/.github/workflows/quality-gates.yml"
        if ! check_workflow "$workflow"; then
            ((error_count++))
        fi
    fi

    echo ""
    echo "========================================================================"
    if [ $error_count -eq 0 ]; then
        echo "✅ All workflows valid"
        exit 0
    else
        echo "❌ Found issues in $error_count workflow(s)"
        echo ""
        echo "Fix with:"
        echo "  cd unified-trading-codex/11-project-management/github-integration/scripts/automation"
        echo "  python3 /tmp/fix-all-workflows.py"
        echo ""
        echo "See: unified-trading-codex/11-project-management/github-integration/docs/WORKFLOW-SYNTAX-ERROR-PREVENTION.md"
        exit 1
    fi
}

main "$@"
