#!/usr/bin/env bash
# QG: no-hardcoded-venue-urls
# Handlers MUST source URLs from IS-loaded InstrumentRecord.source_archive_url_template.
# Scanning for known hardcoded URL patterns in MTDS handler files.
#
# Blocked patterns (from is_mtds_contract_audit_2026_05_20):
#   - _DRIFT_S3_BASE (hardcoded Drift S3 base URL constant)
#   - https://.*\.s3\. URL literals in handlers (S3 archive URL hardcodes)
#   - _DRIFT_DATA_API = (hardcoded Drift data API)
#   - api.phoenix.trade (Phoenix REST API — dead; use Jupiter route via IS)
#   - hardcoded Solana program IDs in URL-like contexts
#
# Usage: bash scripts/qg/no_hardcoded_venue_urls.sh <repo_root>
# Returns: 0 (pass), 1 (violations found)
#
# owner: slot-8  cadence: CI (pre-merge)  verifier: quality-gates.sh
# last_executed: 2026-05-20

set -euo pipefail

REPO_ROOT="${1:-$(git rev-parse --show-toplevel)}"

HANDLER_DIR="${REPO_ROOT}/market-tick-data-service/market_tick_data_service/cli/handlers"
LIVE_CONNECTORS_DIR="${REPO_ROOT}/market-tick-data-service/market_tick_data_service/live/connectors"
ADAPTERS_DEFI_DIR="${REPO_ROOT}/market-tick-data-service/market_tick_data_service/market_interface/adapters/defi"

if [[ ! -d "$HANDLER_DIR" ]]; then
    echo "SKIP: MTDS handler directory not found: $HANDLER_DIR"
    exit 0
fi

VIOLATIONS=0

# Pattern: module-level _DRIFT_S3_BASE assignment in handler files
if grep -rn '_DRIFT_S3_BASE\s*=' "$HANDLER_DIR" --include="*.py" 2>/dev/null | grep -v "get_solana_protocol_url"; then
    echo "ERROR: _DRIFT_S3_BASE hardcoded in MTDS handler (load from IS InstrumentRecord.source_archive_url_template)"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# Pattern: raw https://*.s3.* URL string literals in handler files (not wrapped in get_solana_protocol_url)
if grep -rn '"https://.*\.s3\.' "$HANDLER_DIR" --include="*.py" 2>/dev/null | grep -v "get_solana_protocol_url\|#\s*noqa\|# noqa"; then
    echo "ERROR: Hardcoded S3 URL literal in MTDS handler (load from IS InstrumentRecord.source_archive_url_template)"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# Pattern: hardcoded api.phoenix.trade in non-comment handler lines
if grep -rn 'api\.phoenix\.trade' "$HANDLER_DIR" --include="*.py" 2>/dev/null | grep -v '^\s*#\|:[[:space:]]*#'; then
    echo "ERROR: api.phoenix.trade hardcoded in MTDS handler (dead endpoint — use Jupiter route from IS record)"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# Pattern: inline CeFi perp venue URL string literals (must come from UAC CEFI_PERP_VENUE_API_ENDPOINTS — F-21)
for _PAT in \
    '"https://api\.hyperliquid\.xyz' \
    '"https://fapi\.asterdex\.com' \
    '"https://api\.pacifica\.fi' \
; do
    if grep -rn "$_PAT" "$HANDLER_DIR" --include="*.py" 2>/dev/null | grep -v '^\s*#\|:[[:space:]]*#'; then
        echo "ERROR: Hardcoded CeFi perp venue URL in MTDS handler (use CEFI_PERP_VENUE_API_ENDPOINTS from unified_api_contracts.registry)"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

# ── Extended scan: live/connectors + market_interface/adapters/defi ────────
# Bare literal host strings that must derive from UAC registry functions:
#   api.curve.finance  → get_evm_protocol_rest_url("curve")
#   blue-api.morpho.org → get_evm_protocol_rest_url("morpho")
#   lite-api.jup.ag    → get_solana_protocol_url("jupiter")
# Exclude lines that already call the getter on the same line (the fallback
# string in `get_evm_protocol_rest_url("curve") or "https://api.curve.finance"`
# appears on the same line as the getter → excluded correctly).

for _SCAN_DIR in "$LIVE_CONNECTORS_DIR" "$ADAPTERS_DEFI_DIR" "$HANDLER_DIR"; do
    [[ -d "$_SCAN_DIR" ]] || continue
    if grep -rn '"https://api\.curve\.finance' "$_SCAN_DIR" --include="*.py" 2>/dev/null \
            | grep -v "get_evm_protocol_rest_url\|#.*noqa\|^\s*#"; then
        echo "ERROR: api.curve.finance bare literal in $_SCAN_DIR (use get_evm_protocol_rest_url(\"curve\") from unified_api_contracts.registry)"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
    if grep -rn '"https://blue-api\.morpho\.org' "$_SCAN_DIR" --include="*.py" 2>/dev/null \
            | grep -v "get_evm_protocol_rest_url\|#.*noqa\|^\s*#"; then
        echo "ERROR: blue-api.morpho.org bare literal in $_SCAN_DIR (use get_evm_protocol_rest_url(\"morpho\") from unified_api_contracts.registry)"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
    if grep -rn '"https://lite-api\.jup\.ag' "$_SCAN_DIR" --include="*.py" 2>/dev/null \
            | grep -v "get_solana_protocol_url\|#.*noqa\|^\s*#"; then
        echo "ERROR: lite-api.jup.ag bare literal in $_SCAN_DIR (use get_solana_protocol_url(\"jupiter\") from unified_api_contracts.registry)"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

if [[ $VIOLATIONS -gt 0 ]]; then
    echo "ERROR: $VIOLATIONS hardcoded-URL violation(s) in MTDS handlers"
    echo "MTDS handlers MUST read source_archive_url_template from IS InstrumentRecord."
    echo "SSOT: plans/active/is_mtds_contract_audit_2026_05_20.md Phase 7"
    exit 1
fi

echo "OK: no_hardcoded_venue_urls — no hardcoded URL patterns in MTDS handlers"
exit 0
