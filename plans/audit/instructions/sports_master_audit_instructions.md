---
name: sports_master_audit_instructions
type: audit-instructions
epic: sports_master
assigned_vm: vm-sports
tier: L0
last_updated: 2026-06-01
---

# Sports Master — Audit Instructions

## Epic Scope

Sports adapters (Sportradar, Footystats, The-Odds-API), GBP settlement path, sports archetypes (odds dispersion), GCS
path utilities from UAC (`unified_api_contracts.sports`), and coverage gap handling.

Key invariants: GCS paths always from `candidate_parquet_paths()`; date coverage always clipped via
`clip_dates_to_source_coverage()` + `is_in_known_gap()`.

## Triggers

- Weekly (minimum cadence)
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

- [x] ✅ (f) **GCS paths use `asset_group=` canonical key**: no `category=` in sports GCS paths. **MIGRATION COMPLETE
      2026-05-24**: dry-run confirmed GCS bucket `market-data-tick-sports-central-element-323112` already canonical —
      `found=0` across all 2139 days (2020-06-06 → 2026-04-14). Bucket uses `asset_group=sports/` throughout (two path
      structures: `day=*/asset_group=sports/data_source=ODDS_API/` for early data;
      `day=*/pipeline_mode=batch_api_football/asset_group=sports/venue=*/` for later data). Code audit:
      `rg "category=" --include="*.py"` in sports adapter files → 0 hits ✓. Plan:
      `plans/active/sports_gcs_partition_rekey_2026_05_23.md` Phase 1+2 complete 2026-05-24.

- [ ] (g) **Credential asks filed**: any adapter without live credentials has a `BLOCKED-CREDENTIALS` ping with
      Sportradar/Footystats/The-Odds-API tier + cost estimate.

### Dual-source provenance (the `source` column + SOURCE_PRIORITY)

> Codified 2026-06-01 (crosscutting plan: `plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`). Sports
> is inherently multi-source — `SOURCE_PRIORITY[("sports","FIXTURES")] = ["api_football","footystats"]`, plus multi-book
> odds. Design: same hive drop, disambiguated by a **row-level `source` column**, resolved via UAC `SOURCE_PRIORITY`.
>
> **Sports-specific divergence to fix (audit 2026-06-01)**: sports currently encodes the source in the **GCS PATH**, not
> a column — legacy `day=…/asset_group=sports/data_source=ODDS_API/` and newer
> `day=…/pipeline_mode=batch_api_football/asset_group=sports/venue=…/` (see item (f)). This contradicts the
> operator-confirmed column model (2026-06-01: `source` is a column, better for batch=live symmetry). Sports must migrate
> source-as-path → source-as-column to match the other asset groups.

- [ ] (h) **Source recorded per row, not per path**: sports writers pass `source=` to `record_captured`; the `source`
      column is populated on sports parquet rows. RED if source lives only in the `data_source=`/`pipeline_mode=` path
      segment. Read ACTUAL prod rows — note the path-vs-column inconsistency and migrate to column.
- [ ] (i) **SOURCE_PRIORITY sports multi-entries operationalized**: the FIXTURES merge (`api_football`+`footystats`,
      currently "deferred Phase 1B" in `source_priority.py`) has an active plan slot; multi-entry lists are not stale.
- [ ] (j) **Read-time reconciliation wired**: NO `select_primary_available_source("sports", …)` calls exist today —
      verify the sports consumer read path resolves source priority. 2-source fixture (same fixture from api_football +
      footystats) → exactly one resolved row, no silent double-count, divergence surfaced via
      `detect_dual_source_conflicts()`.

### E2E Batch, Paper, and Live Verification

- (e2e-batch) **Batch e2e**: For the MVP archetypes of this domain, run a dry-run batch audit using mock upstream
  fixtures (`CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local`) — confirm signals are generated end-to-end from adapter output
  through strategy. If real upstream unavailable, synthetic fixtures from `tests/e2e/fixtures/` suffice; the test MUST
  exercise the downstream code regardless of upstream readiness.
- (e2e-paper) **Paper trading audit** (once paper is running): confirm paper PnL events flow from strategy → execution →
  PnL calculator for ≥1 MVP archetype in this domain. Check manifest for strategy_output rows with
  `capture_status=captured` for the date range. If paper not yet running, verify the code path is wired (not
  BLOCKED-CREDENTIALS level — code exists, paper not started).
- (e2e-live) **Live trading audit** (once live is running): verify live execution produces execution_record rows in
  manifest with no DIVERGENT_EMPTY. Alert thresholds fire within SLA. PnL reported correctly.
- (mock-upstream) **Mock upstream pattern**: this domain's audit MUST be runnable WITHOUT live upstream data. Document
  the exact `pytest` fixtures or `CLOUD_MOCK_MODE=true` invocation in `## Output Format` so any slot can run the
  downstream-only audit independently.

## Success Criteria

- All 7 scaffold checklist items (a)–(g) GREEN
- Dual-source provenance items (h)–(j) GREEN: `source` lives in a column (not only the path), zero blank on multi-source
  cells, 2-source fixture resolves to one row with no double-count
- `a6_batch_live_adapter_parity.py` shows parity for `asset_group=sports` rows
- Manifest divergence A3: zero `MISSING_EXPECTED` for sports asset_group
- QG exits 0 for features-service (sports family)
- e2e batch audit produces signals for ≥1 MVP archetype using mock upstream data (CLOUD_MOCK_MODE=true green)
- Paper trading goal post: ≥1 archetype runs ≥7 continuous paper days without silent failures

## Output Format

Result file at `plans/audit/results/sports_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
