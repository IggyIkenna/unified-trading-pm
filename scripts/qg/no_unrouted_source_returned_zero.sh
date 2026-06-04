#!/usr/bin/env bash
# QG: A10c — DeFi "source succeeded, zero rows" shards MUST route through
# DefiManifestRecorder.record_zero_rows(...), NOT a raw record_empty(reason=SOURCE_RETURNED_ZERO).
#
# record_zero_rows resolves the venue's UAC DEFI_VENUE_LAUNCH_DATES and demotes pre-launch days to
# EXPECTED_PRE_VENUE_LAUNCH instead of the blanket SOURCE_RETURNED_ZERO lie (plan §A2b/§A10d). This
# ratchet makes the backstop un-bypassable: a NEW raw record_empty(SOURCE_RETURNED_ZERO) in a DeFi
# handler fails the gate. A genuinely-typed reason already in hand (e.g. the expected_coverage()
# oracle's EXPECTED_* reason in lending_indices_handler) is exempt via an inline `# QG-allow:`
# comment INSIDE the record_empty(...) call block.
#
# Scope: market-tick-data-service DeFi handlers (record_zero_rows is the DefiManifestRecorder path).
# Fleet extension to other AGs/services (UTL ManifestWriter.record_zero_rows) tracked as A10c-fleet.
#
# Usage:  bash scripts/qg/no_unrouted_source_returned_zero.sh <workspace_root>
# Returns: 0 (pass), 1 (violations found)
#
# owner: slot-2  cadence: CI (pre-merge)  verifier: market-tick-data-service/scripts/quality-gates.sh
# last_executed: 2026-06-05

set -euo pipefail

WS_ROOT="${1:-${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel)/.." && pwd)}}"

HANDLERS="${WS_ROOT}/market-tick-data-service/market_tick_data_service/cli/handlers"
if [[ ! -d "${HANDLERS}" ]]; then
    # Allow running from inside the mtds repo too.
    HANDLERS="$(git rev-parse --show-toplevel 2>/dev/null)/market_tick_data_service/cli/handlers"
fi
if [[ ! -d "${HANDLERS}" ]]; then
    echo "OK: A10c — no DeFi handlers dir found (skipping)"
    exit 0
fi

VIOLATIONS=0
for f in "${HANDLERS}"/*_handler.py; do
    [[ -f "$f" ]] || continue
    # Block-scan each `.record_empty(` call: flag it if its block contains SOURCE_RETURNED_ZERO
    # and does NOT carry an inline `# QG-allow:` waiver.
    hits="$(awk '
        /\.record_empty\(/ { s = NR; c = 1; srz = 0; allow = 0; next }
        c == 1 {
            if ($0 ~ /SOURCE_RETURNED_ZERO/) srz = 1
            if ($0 ~ /# QG-allow:/) allow = 1
            if ($0 ~ /\)/) { if (srz == 1 && allow == 0) print FILENAME ":" s; c = 0 }
        }
    ' "$f" 2>/dev/null || true)"
    if [[ -n "${hits}" ]]; then
        echo "ERROR (A10c): unrouted record_empty(SOURCE_RETURNED_ZERO) — route via record_zero_rows (or add '# QG-allow:'):"
        echo "${hits}"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

if [[ "${VIOLATIONS}" -gt 0 ]]; then
    echo "A10c FAILED: ${VIOLATIONS} DeFi handler file(s) with an unrouted zero-rows record_empty."
    echo "  Fix: call recorder.record_zero_rows(...) (drops the reason= kwarg) — plan §A10d."
    exit 1
fi
echo "OK: A10c — all DeFi handler zero-rows shards route through record_zero_rows (or carry # QG-allow:)."
exit 0
