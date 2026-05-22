---
name: predictions_master_audit_instructions
type: audit-instructions
epic: predictions_master
assigned_vm: vm-prediction
tier: L0
last_updated: 2026-05-22
---

# Predictions Master — Audit Instructions

## Epic Scope

Prediction market adapters (Polymarket, Kalshi), binary-outcome archetype definitions, and the
Polymarket vs Kalshi spread strategy. Key invariant: binary resolution events handled correctly; no hardcoded
market IDs.

## Triggers

- Monthly (minimum cadence)
- After major prediction market events (US elections, macro events)
- When UAC binary-outcome schema changes
- When new prediction market venues are considered for universe expansion

## Checklist

- [ ] (a) **Polymarket adapter handles binary resolution**: adapter correctly processes `resolved: true/false` events
      and emits manifest rows with `capture_status=captured` or `empty_confirmed[reason=SOURCE_RETURNED_ZERO]`.
      Read: Polymarket adapter + verify resolution event handling

- [ ] (b) **Kalshi adapter covers REST + WebSocket**: both polling (batch) and streaming (live) modes implemented.
      Find: `rg "kalshi" market-tick-data-service/ --include="*.py" -l`
      Verify: `--mode batch` and `--mode live` both present in adapter

- [ ] (c) **Polymarket vs Kalshi spread archetype**: archetype produces valid signals when market exists on both venues.
      Read: strategy-service archetype for predictions — verify it handles the case where only one venue has the market

- [ ] (d) **UAC binary-outcome schema completeness**: all fields needed by the spread archetype are present in UAC.
      Read: `unified_api_contracts/canonical/domain/predictions/` — verify schema covers outcome probability,
      settlement time, market liquidity, and resolution status

- [ ] (e) **Manifest rows with asset_group=prediction**: archetypes emit rows with correct hive key.
      Check: A3 manifest divergence scan for `asset_group=prediction` — zero `MISSING_EXPECTED`

- [ ] (f) **No hardcoded market IDs**: archetype logic does not reference specific Polymarket/Kalshi market IDs.
      Grep: `rg "0x[a-f0-9]{40}|market_id.*=.*\"[A-Z]" strategy-service/ --include="*.py"` — should be 0 hits in
      archetype business logic (only in test fixtures is acceptable)

- [ ] (g) **Credential asks filed**: if Polymarket or Kalshi API keys not provisioned, `BLOCKED-CREDENTIALS` ping
      filed with account type, cost, and unblocks.

## Success Criteria

- All 7 checklist items GREEN
- `a6_batch_live_adapter_parity.py` shows parity for `asset_group=prediction` rows
- Manifest divergence A3: zero `MISSING_EXPECTED` for prediction asset_group
- QG exits 0 for features-service (predictions family)

## Output Format

Result file at `plans/audit/results/predictions_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date | Result file | Status |
|------|-------------|--------|
| (populated as audits run) | | |
