---
name: cefi_master_audit_instructions
type: audit-instructions
epic: cefi_master
assigned_vm: vm-cefi
tier: L0
last_updated: 2026-05-22
---

# CeFi Master — Audit Instructions

## Epic Scope

CeFi adapters for all supported venues, CCXT adapter layer, CEFFU custody (June-1), perp funding adapters, spot price
adapters, and the perp hedge legs used in DeFi+CeFi hybrid archetypes.

Key venues: Binance, Bybit, OKX, Deribit, Hyperliquid, Aster, Kraken (7+ venues). Key code surfaces: venue adapters in
MTDS, perp funding readers, spot price readers, CeFi archetype definitions.

## Triggers

- Monthly (minimum cadence)
- After any venue API version bump (Binance API v4, OKX v5, etc.)
- When perp funding data shows manifest gaps (`empty_confirmed` without valid reason for cefi rows)
- When `instruments_master` adds or removes a venue from the universe
- After CEFFU custody provider integration changes

## Checklist

- [ ] (a) **Error classification wired**: all 7+ CeFi venues have `classify_venue_error()` called in their adapters.
      Grep: `rg "classify_venue_error" market-tick-data-service/ --include="*.py"` — verify each venue handler present

- [ ] (b) **ADAPTER_FETCH_FAILED emitted**: every adapter emits `ADAPTER_FETCH_FAILED` event on error path. Grep:
      `rg "ADAPTER_FETCH_FAILED" market-tick-data-service/ --include="*.py"`

- [ ] (c) **No hardcoded venue universe**: QG `no_hardcoded_venue_universe.sh` passes. Run:
      `bash scripts/quality-gates/no_hardcoded_venue_universe.sh`

- [ ] (d) **IS→MTDS contract honored**: CeFi MTDS handlers derive venue URLs from instruments-service, not hardcoded.
      Run: `bash scripts/quality-gates/no_hardcoded_venue_urls.sh` Verify: `no_silent_absence_handlers.sh` passes

- [ ] (e) **Perp funding + spot batch/live parity**: all 7+ venue funding adapters have both `--mode batch` and
      `--mode live` implemented. Check: `a6_batch_live_adapter_parity.py` output for cefi rows — batch count == live
      count per venue

- [ ] (f) **CEFFU custody codex alignment**: `codex/04-architecture/custody-providers.md` describes CEFFU correctly.
      Verify the June-1 timeline is documented and code reflects the May-23 `CLOUD_KMS_ENCRYPTED` path.

- [ ] (g) **DeFi+CeFi hybrid hedge leg**: perp hedge leg for `carry_staked_basis` archetype wires correctly to the CeFi
      execution path. Read: `codex/09-strategy/architecture-v2/archetypes/` — verify hybrid architecture description
      matches code

- [ ] (h) **No banned reasoning for missing venues**: every venue in the universe has an adapter or a
      `BLOCKED-CREDENTIALS` ping filed. No silent deferrals. Check: `human_led_audit_pool_2026_05_21.md` +
      `instruments-service` universe list

## Success Criteria

- All 8 checklist items GREEN
- `a6_batch_live_adapter_parity.py` shows 100% parity for `asset_group=cefi` rows
- Manifest divergence A3: zero `MISSING_EXPECTED` for cefi asset_group
- QG exits 0 for MTDS + instruments-service

## Output Format

Result file at `plans/audit/results/cefi_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
