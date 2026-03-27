#!/usr/bin/env bash
# Run codex/PM validators for production readiness.
# Invoked by quality-gates.sh [6/6] when present.
# SSOT: unified-trading-codex/06-coding-standards/quality-gates.md

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_ROOT="$(dirname "$SCRIPT_DIR")"
WORKSPACE_ROOT="${REPO_ROOT:-$(dirname "$(dirname "$CODEX_ROOT")")}"
PM_SCRIPTS="${WORKSPACE_ROOT}/unified-trading-pm/scripts"

run_pm_validators() {
    local scope="${1:-all}"
    if [ -f "${PM_SCRIPTS}/run_validators.py" ]; then
        python3 "${PM_SCRIPTS}/run_validators.py" --scope "$scope" 2>/dev/null || return 1
    fi
    return 0
}

main() {
    local category="${1:-all}"
    case "$category" in
        all) run_pm_validators all ;;
        *) run_pm_validators "$category" ;;
    esac
}

main "$@"
