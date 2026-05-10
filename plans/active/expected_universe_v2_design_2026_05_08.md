---
name: expected-universe-v2-design-2026-05-08
type: plan
plan_type: design
asset_group: cross-cutting
owner: ikenna
status: draft
priority: P1
created: 2026-05-08
last_updated: 2026-05-08
parent: writegate_honest_coverage_endtoend_2026_05_06
related_plans:
  - writegate_honest_coverage_endtoend_2026_05_06
  - gcs_migration_bundle_pipeline_mode_2026_05_08
  - manifest_migration_master_2026_05_07
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

> **🟡 FOLDED INTO UMBRELLA — `manifest_evolution_master_2026_05_08`** (codified 2026-05-08)
>
> This plan's manifest-touching scope MUST execute as part of the umbrella's gate sequence — NOT in isolation. Operator
> direction: "manifest, code, and data migrate in the same group plan to avoid collision risk; force batch execution;
> don't allow execution in isolation." Three-axis invariant: schema (UAC) + writer code (UTL + adapter callsites) + GCS
> data layout co-evolve.
>
> Child of: [`plans/epics/manifest_evolution_master_2026_05_08.md`](../epics/manifest_evolution_master_2026_05_08.md)
>
> This plan's phases land in gate(s): **G3** (per-instrument enumerator launch — sequenced AFTER G4 v8 schema)

# Expected_universe v2 enumerator — design (2026-05-08, Tab 3 separate scope)

> Item 4 of Tab 3 in [`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md). v2 extends the v1 enumerator
> with a cross-bucket join on the instruments-service catalog so the manifest's expected universe is instrument-grain
> (not just venue-grain).

## Why

`writegate_honest_coverage_endtoend_2026_05_06` Phase 3.D.4 v1 shipped 2026-05-07 (1.4M rows) — enumerates the full
expected universe per `(asset_group, venue, data_type, day)` from the UAC SSOTs (`*_LAUNCH_DATES`, `*_GENESIS_DATES`,
`SOURCE_COVERAGE_START`, `venue_trading_calendar`, `KNOWN_COVERAGE_GAPS`). v1 closes the rollup-vs-drilldown
denominator-divergence at the venue grain but doesn't capture per-instrument lifecycle bounds. v2 adds the second SSOT
half (per CLAUDE.md "Two SSOTs for the manifest's expected universe"): instruments-service catalog × dates × data_types
cross-product applied at expected-row generation, not just at write-side.

## v1 recap (already shipped)

- Walks UAC SSOTs to enumerate every `(asset_group, venue, data_type, day)` row that SHOULD exist on
  `live-defi- rollout`.
- Pre-skips:
  - `venue_trading_calendar` non-trading days for tradfi.
  - `*_LAUNCH_DATES` / `*_GENESIS_DATES` pre-launch / pre-genesis dates for cefi / defi.
  - `SOURCE_COVERAGE_START` per-source pre-coverage dates for sports / prediction.
  - `KNOWN_COVERAGE_GAPS` documented outage windows.
- Output: ~1.4M `record_expected_unattempted` rows merged into the canonical manifest via per-VM shard isolation +
  consolidator daemon.
- Implementation: `instruments-service/scripts/enumerate_expected_universe.py` + per-VM launcher.

## v2 — cross-bucket join with instruments-service catalog

v1 produces venue-grain coverage. v2 cross-joins v1's `(asset_group, venue, data_type, day)` axis with the
instruments-service catalog's per-instrument lifecycle:

| Asset group          | v1 grain                                           | v2 grain (after catalog join)                                                                   |
| -------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| cefi spot/perp       | `(asset_group, venue, data_type, day)`             | `(asset_group, venue, data_type, instrument_type, instrument_id, day)` per per-instrument shard |
| cefi options/futures | `(asset_group, venue, data_type, day)`             | `(asset_group, venue, data_type, root, day)` per options_chain / futures_chain root             |
| tradfi futures       | `(asset_group, venue, data_type, day)`             | `(asset_group, venue, data_type, root, day)` per futures root                                   |
| tradfi options       | `(asset_group, venue, data_type, day)`             | `(asset_group, venue, data_type, root, day)` per ES.OPT 11-cluster bundle                       |
| tradfi ETFs          | `(asset_group, venue, data_type, day)`             | `(asset_group, venue, data_type, instrument_type, instrument_id, day)` per per-instrument shard |
| defi                 | `(asset_group, chain, venue, data_type, day)`      | `(asset_group, chain, venue/protocol, data_type, instrument_id_or_protocol_id, day)`            |
| sports               | `(asset_group, source, data_type, league_id, day)` | `(asset_group, source, data_type, league_id, fixture_id, day)` for per-fixture data_types       |
| prediction           | `(asset_group, venue, data_type, day)`             | `(asset_group, venue, data_type, canonical_question_group, day)` per market lifecycle window    |

### Lifecycle bounds applied at v2

- **cefi instrument-listing**: NO rows before `active_from`; NO rows after `active_to` (instrument delisted).
- **prediction market lifecycle**: NO rows before `market_created_at`; NO rows after `settlement_time`. Recurring
  canonical groups (`BTC_UP_DOWN_HOURLY`, etc.) cycle through multiple market_ids — v2 enumerates the per-market_id
  lifecycle and rolls back up to the canonical_question_group bundle.
- **defi protocol-launch**: NO rows before `protocol_launch_date` per chain (UAC `PROTOCOL_LAUNCH_DATES`).
- **sports fixture lifecycle**: per-fixture data_types only emit on the fixture's day; reference-data (TEAMS, PLAYERS,
  VENUES, LEAGUES) stays day-aggregate.

## Implementation

Extend `instruments-service/scripts/enumerate_expected_universe.py`:

```python
def enumerate_v2(
    *,
    asset_group: str,
    catalog: InstrumentCatalog,    # read from instruments-service catalog parquets
    date_axis: list[date],          # output of v1's pre-skip rules
    data_types: list[str],
) -> Iterator[ExpectedRow]:
    """Cross-join v1's date axis with catalog's per-instrument lifecycle.
    Yields one row per (catalog-alive-instrument × applicable-date × data_type) triple,
    respecting per-asset_group lifecycle rules above."""
```

Per-VM shard isolation MANDATORY for the launch run (`MANIFEST_PER_VM_SHARDS=true` +
`VM_NAME=expected-universe-v2- {asset_group}-{RUN_TS}`).

## Output volume estimate

- v1 = ~1.4M rows (venue-grain).
- v2 estimate (per-instrument grain × ~5 years × ~5 data_types):
  - cefi spot/perp: ~10 venues × ~2000 instruments × 1825 days × 5 data_types ≈ 180M rows (HEAVY).
  - cefi options/futures: ~5 venues × ~50 roots × 1825 days × 3 data_types ≈ 1.4M rows.
  - tradfi: ~6 venues × ~50 instruments × 1500 days × 4 data_types ≈ 1.8M rows.
  - defi: ~10 chains × ~30 protocols × ~1500 days × 5 data_types ≈ 2.3M rows.
  - sports: ~30 leagues × ~400 fixtures/year × 5 years × 8 data_types ≈ 4.8M rows.
  - prediction: ~10 canonical groups × ~24 markets/day × 1500 days × 3 data_types ≈ 1.1M rows.
- **Total estimate: ~190M rows** (cefi spot/perp dominates by 95%).

This is a 100× scale-up from v1. Per-VM shard isolation + consolidator daemon handles it at write-side, but readers need
to be ready for 190M-row manifest scans. Use pyarrow column-projection + duckdb for any aggregate queries on the
canonical manifest post-v2.

## Codex SSOT updates needed (when v2 ships)

- **UPDATE** `codex/02-data/availability-manifest-and-data-status.md` — extend "Expected universe" section to describe
  v1 (venue-grain) vs v2 (instrument-grain), with the per-asset-group grain table from this plan.
- **UPDATE** `codex/02-data/honest-absence-downstream-handling.md` — note that v2's `record_expected_unattempted` rows
  at instrument grain mean honest-coverage % calculations now have a 100× larger denominator; downstream consumers
  (deployment-api data-status drilldown, features-\* pre-flight, ML training row counts) need to handle the volume.

## Open questions

- Q1 — cefi spot/perp 180M-row output: do we shard the v2 launch by venue (one VM per venue) or by date-window? Bias
  toward venue-sharding so a single VM doesn't burn a full Tardis catalog read just to enumerate.
- Q2 — read-time denominator query: pyarrow scans 190M rows in ~30s on a same-region VM. Cache the denominator in redis
  with 24h TTL? Or compute live per-request? Defer to deployment-api scope.
- Q3 — operator-decision: launch v2 NOW or AFTER manifest v6→v7→v8 schema migration? v8 adds `service_emission_state` +
  2 sibling columns; if v2 lands first, v8 migration walks 190M rows; if v8 lands first, v2 enumerator writes the new
  columns immediately. Lean toward v8 first (smaller working set on the migration walk).

## Cross-plan coordination

- `manifest_migration_master_2026_05_07` — Stage 4 includes residual sweeps that overlap with v2 launch. Coordinate
  banner during v2 launch window.
- `manifest_v7_schema_migration_design_2026_05_08` (sibling Tab 3 design) — both designs touch manifest schema +
  enumeration. v2 launch should happen AFTER v8 migration for write-side simplicity.
- `live_pipeline_mtds_mdps_features_2026_05_08` Phase 12 — batch-vs-live reconciliation needs the v2 expected universe
  to compute a meaningful completeness denominator per shard atom.
