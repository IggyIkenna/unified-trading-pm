---
name: sports_master_audit_instructions
type: audit-instructions
epic: sports_master
assigned_vm: vm-sports
tier: L0
last_updated: 2026-05-22
---

# Sports Master — Audit Instructions

## Epic Scope

Sports adapters (Sportradar, Footystats, The-Odds-API), GBP settlement path, sports archetypes (odds dispersion), GCS
path utilities from UAC (`unified_api_contracts.sports`), and coverage gap handling.

Key invariants: GCS paths always from `candidate_parquet_paths()`; date coverage always clipped via
`clip_dates_to_source_coverage()` + `is_in_known_gap()`.

## Triggers

- Monthly (minimum cadence)
- After sports season transitions (pre-season, new league coverage)
- When odds dispersion targets change (new bookmaker added to universe)
- When UAC sports schema changes

## Checklist

- [ ] (a) **GCS path utility usage**: every sports adapter uses `candidate_parquet_paths()` from
      `unified_api_contracts.sports` — no manual GCS path construction. Grep:
      `rg "candidate_parquet_paths" --include="*.py"` — verify all sports adapters import from UAC Anti-pattern:
      `rg "gs://.*sports" --include="*.py"` should return 0 hits outside of utility/test files

- [ ] (b) **Coverage gap utilities wired**: `clip_dates_to_source_coverage()` and `is_in_known_gap()` called in all
      sports adapters that have known data coverage gaps. Grep:
      `rg "clip_dates_to_source_coverage|is_in_known_gap" --include="*.py"`

- [ ] (c) **GBP settlement end-to-end**: settlement path has an integration test covering GBP → base currency conversion
      for sports positions. Find: `rg "GBP|settlement" market-tick-data-service/tests/ --include="*.py" -l`

- [ ] (d) **The-Odds-API rate-limit + retry**: adapter has rate-limit handling and exponential backoff. Read:
      The-Odds-API adapter file — verify retry decorator or equivalent

- [ ] (e) **Manifest rows for sports**: archetypes produce manifest rows with `asset_group=sports` hive key and correct
      `schema_version`. Check: A3 manifest divergence scan for `asset_group=sports` — zero `MISSING_EXPECTED`

- [ ] (f) **GCS paths use `asset_group=` canonical key**: no `category=` in sports GCS paths. Grep:
      `rg "category=" --include="*.py"` in sports adapter files — should be 0 hits

- [ ] (g) **Credential asks filed**: any adapter without live credentials has a `BLOCKED-CREDENTIALS` ping with
      Sportradar/Footystats/The-Odds-API tier + cost estimate.

## Success Criteria

- All 7 checklist items GREEN
- `a6_batch_live_adapter_parity.py` shows parity for `asset_group=sports` rows
- Manifest divergence A3: zero `MISSING_EXPECTED` for sports asset_group
- QG exits 0 for features-service (sports family)

## Output Format

Result file at `plans/audit/results/sports_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
