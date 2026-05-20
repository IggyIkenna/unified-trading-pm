#!/usr/bin/env bash
# QG: no-hardcoded-venue-universe
# Universe MUST come from load_*_metadata_for_date() (IS catalogue) not hardcoded lists.
# Scanning for known hardcoded universe patterns in MTDS handler files.
#
# Blocked patterns (from is_mtds_contract_audit_2026_05_20):
#   - SOLANA_LST_TOKENS = [...] (hardcoded Solana LST token universe)
#   - DRIFT_MARKETS = [...] or similar hardcoded Drift market list
#   - _PHOENIX_PAIRS = (...) (hardcoded Phoenix trading pairs)
#   - module-level tuples/lists named *_PAIRS, *_MARKETS, *_TOKENS, *_UNIVERSE in handlers
#
# Usage: bash scripts/qg/no_hardcoded_venue_universe.sh <repo_root>
# Returns: 0 (pass), 1 (violations found)
#
# owner: slot-8  cadence: CI (pre-merge)  verifier: quality-gates.sh
# last_executed: 2026-05-20

set -euo pipefail

REPO_ROOT="${1:-$(git rev-parse --show-toplevel)}"

HANDLER_DIR="${REPO_ROOT}/market-tick-data-service/market_tick_data_service/cli/handlers"

if [[ ! -d "$HANDLER_DIR" ]]; then
    echo "SKIP: MTDS handler directory not found: $HANDLER_DIR"
    exit 0
fi

VIOLATIONS=0

# Pattern: module-level *_TOKENS / *_MARKETS / *_PAIRS / *_UNIVERSE assignments that are list/tuple literals
UNIVERSE_PATTERNS=(
    'SOLANA_LST_TOKENS\s*='
    'DRIFT_MARKETS\s*='
    '_PHOENIX_PAIRS\s*='
    '_LST_TOKENS\s*='
    '_MARKET_LIST\s*='
    '_UNIVERSE\s*='
)

for pattern in "${UNIVERSE_PATTERNS[@]}"; do
    if grep -rn "$pattern" "$HANDLER_DIR" --include="*.py" 2>/dev/null; then
        echo "ERROR: Hardcoded universe pattern '$pattern' in MTDS handler"
        echo "  Universe MUST come from IS catalogue via load_*_metadata_for_date()"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

if [[ $VIOLATIONS -gt 0 ]]; then
    echo "ERROR: $VIOLATIONS hardcoded-universe violation(s) in MTDS handlers"
    echo "MTDS handlers MUST call load_*_metadata_for_date() to enumerate the universe."
    echo "SSOT: plans/active/is_mtds_contract_audit_2026_05_20.md Phase 7"
    exit 1
fi

echo "OK: no_hardcoded_venue_universe — no hardcoded universe patterns in MTDS handlers"
exit 0
