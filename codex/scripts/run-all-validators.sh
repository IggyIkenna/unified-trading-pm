#!/usr/bin/env bash
# Run codex/PM validators for production readiness.
# Invoked by quality-gates.sh [6/6] when present.
# SSOT: unified-trading-pm/codex/06-coding-standards/quality-gates.md

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
    # base-service.sh / base-library.sh call:
    #   run-all-validators.sh --asset-group all --failed-only
    # Historically also:  run-all-validators.sh all
    local category="all"
    while [ $# -gt 0 ]; do
        case "$1" in
            --asset-group)
                category="${2:-all}"
                shift 2
                ;;
            --failed-only)
                # informational flag for parity with historical CI wiring
                shift
                ;;
            all | checklist | manifest)
                category="$1"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    case "$category" in
        all) run_pm_validators all ;;
        checklist | manifest) run_pm_validators "$category" ;;
        *) run_pm_validators all ;;
    esac
}

main "$@"
