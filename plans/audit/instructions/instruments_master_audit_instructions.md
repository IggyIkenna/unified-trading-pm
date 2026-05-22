---
name: instruments_master_audit_instructions
type: audit-instructions
epic: instruments_master
assigned_vm: vm-cefi
tier: L1
last_updated: 2026-05-22
---

# Instruments Master — Audit Instructions

## Epic Scope

instruments-service as the reference data SSOT: venue URL ownership, instrument universe management, `InstrumentRecord`
schema, and the IS→MTDS contract enforced by QG STEP 5.70 (three scripts). MTDS handlers derive all venue URLs and
universes from IS — never hardcoded.

Codex SSOT: `codex/04-architecture/instruments-service-as-ssot-for-mtds.md`

## Triggers

- Weekly (minimum cadence)
- When a new venue is added to MTDS (IS must be updated first)
- After any `InstrumentRecord` schema change in UAC
- When `reconcile_phantom_manifest_rows_all.py` shows phantom rows for any asset_group

## Checklist

- [ ] (a) **QG STEP 5.70 — no_silent_absence_handlers.sh**: passes for all MTDS handler files. Run:
      `bash scripts/quality-gates/no_silent_absence_handlers.sh`

- [ ] (b) **QG STEP 5.70 — no_hardcoded_venue_urls.sh**: passes for all MTDS handler files. Run:
      `bash scripts/quality-gates/no_hardcoded_venue_urls.sh`

- [ ] (c) **QG STEP 5.70 — no_hardcoded_venue_universe.sh**: passes for all MTDS handler files. Run:
      `bash scripts/quality-gates/no_hardcoded_venue_universe.sh`

- [ ] (d) **InstrumentRecord coverage**: IS universe covers all active venues in the trading system. Check:
      `instruments-service` universe manifest vs MTDS handler list — no gaps Grep:
      `rg "venue" instruments-service/instruments_service/ --include="*.py" -l`

- [ ] (e) **MTDS handlers derive URLs from IS**: no MTDS handler file constructs a venue URL directly. Grep:
      `rg "http[s]?://" market-tick-data-service/ --include="*.py"` — should be 0 hits in handler business logic (test
      fixtures and config schema excluded)

- [ ] (f) **Zero phantom manifest rows**: `reconcile_phantom_manifest_rows_all.py` returns zero phantoms. Run:
      `python3 instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run` Run:
      `python3 instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run`

- [ ] (g) **No URDI references**: `URDI` (phantom name) does not appear anywhere in the codebase. Grep:
      `rg "URDI" --include="*.py"` — should be 0 hits

### Batch vs Live Parity

- (batch-live) **Batch adapter output**: confirm each adapter in scope produces manifest rows with
  `capture_status=captured` for a known date range using the batch invocation path (`--mode batch`). Run against mock
  data if real upstream is unavailable (`CLOUD_MOCK_MODE=true`).
- (live-adapter) **Live adapter parity**: for each batch adapter, confirm the live adapter exists, accepts the same
  schema, and emits `available_at` at write-time (not read-time). Confirm no `DIVERGENT_EMPTY` rows for live mode.
- (mock-upstream) **Mock upstream pattern**: audits for this data layer MUST be runnable without hitting real APIs.
  Document fixture paths and `CLOUD_MOCK_MODE=true` invocations so downstream services can be audited independently.

## Success Criteria

- All 7 checklist items GREEN (especially QG STEP 5.70 triple-pass)
- Zero phantom manifest rows for cefi + defi asset groups
- QG exits 0 for instruments-service and market-tick-data-service

## Output Format

Result file at `plans/audit/results/instruments_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
