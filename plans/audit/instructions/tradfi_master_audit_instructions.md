---
name: tradfi_master_audit_instructions
type: audit-instructions
epic: tradfi_master
assigned_vm: vm-tradfi
tier: L0
last_updated: 2026-05-22
---

# TradFi Master — Audit Instructions

## Epic Scope

TradFi adapters (Databento, Polygon.io), CME dated futures, options pricing, VIX 15m feed, and TradFi archetypes:
S&P prediction (CME) and price arbitrage (CME futures + ETFs). Credential-gated adapters expected since subscriptions
are required — audit for scaffold completeness, not live data.

## Triggers

- Monthly (minimum cadence)
- After Databento or Polygon.io API version changes
- When strategy-service reports missing TradFi feature data
- After any new instrument type is added to the TradFi universe

## Checklist

- [ ] (a) **Databento adapter scaffold**: adapter file exists with correct UAC schema, auth shape, retry/backoff,
      rate-limit, and error classification.
      Find: `rg "databento" market-tick-data-service/ --include="*.py" -l`

- [ ] (b) **Polygon.io adapter scaffold**: same requirements as Databento.
      Find: `rg "polygon" market-tick-data-service/ --include="*.py" -l`

- [ ] (c) **Credential-gated tests marked**: integration tests for both adapters have `@pytest.mark.requires_credentials`
      and are skipped by default in CI.
      Grep: `rg "requires_credentials" market-tick-data-service/tests/ --include="*.py"`

- [ ] (d) **VIX 15m implementation**: Barchart preload path + Yahoo Finance rolling 60d + honest gap documented.
      Grep: `rg "VIX|vix" market-tick-data-service/ --include="*.py"` — verify all 3 paths present
      Check: UAC constants in `registry/data_source_continuity.py` are current

- [ ] (e) **CME dated contract roll logic**: roll logic follows codex specification (no hardcoded expiry dates).
      Read: relevant adapter + verify against codex/09-strategy/architecture-v2/archetypes/ TradFi archetype docs

- [ ] (f) **No hardcoded bucket names**: `resolve_bucket_name()` used for all TradFi GCS operations.
      Run: QG STEP 5.69 passes for all TradFi adapters

- [ ] (g) **Credential asks filed**: any adapter without live credentials has a `BLOCKED-CREDENTIALS` ping in
      `ikenna_orchestrator/pings/` with vendor, tier, cost estimate, and unblocks listed.

## Success Criteria

- All 7 checklist items GREEN (adapters scaffold present even if credentials are BLOCKED-CREDENTIALS)
- Unit tests against mocks pass; integration tests skip by default
- QG exits 0 for MTDS (TradFi adapter files)

## Output Format

Result file at `plans/audit/results/tradfi_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date | Result file | Status |
|------|-------------|--------|
| (populated as audits run) | | |
