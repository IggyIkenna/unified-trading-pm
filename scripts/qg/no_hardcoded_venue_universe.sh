#!/usr/bin/env bash
# QG: no-hardcoded-venue-universe
# Universe MUST come from load_*_metadata_for_date() (IS catalogue) not hardcoded lists.
# Scanning for known hardcoded universe patterns in MTDS handler AND engine files.
#
# Blocked patterns (from is_mtds_contract_audit_2026_05_20 + cefi Dim-6 audit 2026-06-04):
#   - SOLANA_LST_TOKENS = [...] (hardcoded Solana LST token universe)
#   - DRIFT_MARKETS = [...] or similar hardcoded Drift market list
#   - _PHOENIX_PAIRS = (...) (hardcoded Phoenix trading pairs)
#   - module-level tuples/lists named *_PAIRS, *_MARKETS, *_TOKENS, *_UNIVERSE
#   - wire-symbol FALLBACK dicts named *_WIRE_SYMBOL_FALLBACK / *_VENUE_*_FALLBACK
#     (a date-BLIND hardcoded universe that bypasses the IS SSOT — cefi Dim-6 GAP:
#     engine/orchestrator.py:_VENUE_WIRE_SYMBOL_FALLBACK was INVISIBLE to the
#     handler-only scan).
#
# The scan now covers BOTH cli/handlers/ AND engine/ (the fallback dict lived in
# engine/, outside the original handler-only scan window).
#
# Sanctioned exception: a deliberately gated fallback (substituted ONLY behind an
# explicit opt-in flag, never the default/live path) may carry an inline marker
#   # qg-allow: venue-universe-fallback <reason>
# on the assignment line to suppress the violation. Use sparingly — the default
# behaviour MUST be honest-skip / IS-derived, never a hardcoded substitution.
#
# Usage: bash scripts/qg/no_hardcoded_venue_universe.sh <repo_root>
# Returns: 0 (pass), 1 (violations found)
#
# owner: slot-8  cadence: CI (pre-merge)  verifier: quality-gates.sh
# last_executed: 2026-06-04

set -euo pipefail

REPO_ROOT="${1:-$(git rev-parse --show-toplevel)}"

MTDS_SRC="${REPO_ROOT}/market-tick-data-service/market_tick_data_service"
HANDLER_DIR="${MTDS_SRC}/cli/handlers"
ENGINE_DIR="${MTDS_SRC}/engine"

# Inline marker that sanctions a deliberately-gated fallback (assignment line).
SANCTION_MARKER="qg-allow: venue-universe-fallback"

# Module-level *_TOKENS / *_MARKETS / *_PAIRS / *_UNIVERSE list/tuple assignments
# plus wire-symbol FALLBACK dicts (annotated `: dict` OR plain `=`, hence [:=]).
UNIVERSE_PATTERNS=(
    'SOLANA_LST_TOKENS\s*='
    'DRIFT_MARKETS\s*='
    '_PHOENIX_PAIRS\s*='
    '_LST_TOKENS\s*='
    '_MARKET_LIST\s*='
    '_UNIVERSE\s*='
    '_WIRE_SYMBOL_FALLBACK\s*[:=]'
    '_VENUE_[A-Z_]*_FALLBACK\s*[:=]'
)

VIOLATIONS=0

scan_dir() {
    # $1 = directory to scan, $2 = human label
    local dir="$1" label="$2"
    [[ -d "$dir" ]] || return 0
    local pattern matches
    for pattern in "${UNIVERSE_PATTERNS[@]}"; do
        # Drop lines carrying the explicit sanction marker.
        matches="$(grep -rn "$pattern" "$dir" --include="*.py" 2>/dev/null | grep -v "$SANCTION_MARKER" || true)"
        if [[ -n "$matches" ]]; then
            echo "$matches"
            echo "ERROR: Hardcoded universe pattern '$pattern' in MTDS ${label}"
            echo "  Universe MUST come from IS catalogue via load_*_metadata_for_date()"
            echo "  (or carry an inline '# ${SANCTION_MARKER} <reason>' for a gated fallback)"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done
}

if [[ ! -d "$HANDLER_DIR" && ! -d "$ENGINE_DIR" ]]; then
    echo "SKIP: MTDS source dirs not found under: $MTDS_SRC"
    exit 0
fi

scan_dir "$HANDLER_DIR" "handlers"
scan_dir "$ENGINE_DIR" "engine"

if [[ $VIOLATIONS -gt 0 ]]; then
    echo "ERROR: $VIOLATIONS hardcoded-universe violation(s) in MTDS handlers/engine"
    echo "MTDS MUST call load_*_metadata_for_date() to enumerate the universe."
    echo "SSOT: plans/active/is_mtds_contract_audit_2026_05_20.md Phase 7"
    echo "      plans/active/cefi_manifest_canonicalisation_2026_06_01.md Dim-6"
    exit 1
fi

echo "OK: no_hardcoded_venue_universe — no hardcoded universe patterns in MTDS handlers/engine"
exit 0
