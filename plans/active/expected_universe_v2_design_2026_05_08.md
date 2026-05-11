---
name: expected-universe-v2-design-2026-05-08
type: plan
plan_type: execution
asset_group: cross-cutting
owner: ikenna
status: active
priority: P1
created: 2026-05-08
last_updated: 2026-05-11
parent: writegate_honest_coverage_endtoend_2026_05_06
related_plans:
  - writegate_honest_coverage_endtoend_2026_05_06
  - gcs_migration_bundle_pipeline_mode_2026_05_08
  - manifest_migration_master_2026_05_07
  - manifest_schema_final_gate_2026_05_09
locked_by: live-defi-rollout
locked_since: 2026-05-08
estimate_class: design
estimate_baseline_ai_days: TBD
estimate_calibrated_ai_days: TBD
estimate_calibration_note: |
  No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from filename (design, multiplier 0.6×).
  Owner agent: fill baseline + multiply × 0.6 per codex/08-workflows/estimation-calibration.md. Refine class if dominant work-class differs.
---

> **🟡 BLOCKED-ON G4 v8 SCHEMA** — execution can't start until `manifest_schema_final_gate_2026_05_09` ships the
> atomic v7→v8 rename + `record_captured(service_emission_state=)` MANDATORY enforcement. Per the umbrella's gate
> sequence, this plan's enumerator launch (G3) runs ONCE on the v8 manifest, NOT pre-v8 then re-run post-v8. Design
> + execution phases below are paste-ready; flip `status:` to `in-progress` when G4 lands.

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
- Q3 — **RESOLVED 2026-05-10** (per `manifest_evolution_master_2026_05_08.md` § G3: "Decision: launch AFTER G4" + this
  plan's frontmatter line 29 "sequenced AFTER G4 v8 schema"). v8 schema migration runs first (read-once + write-once +
  blocking via `manifest_schema_final_gate_2026_05_09` consolidated v8 SSOT); v2 enumerator launches AFTER on the v8
  manifest, writing `service_emission_state` + 2 sibling columns directly. Avoids doubling compute cost of running v2
  pre-v8 then re-running post-v8.

## Cross-plan coordination

- `manifest_migration_master_2026_05_07` — Stage 4 includes residual sweeps that overlap with v2 launch. Coordinate
  banner during v2 launch window.
- `manifest_schema_final_gate_2026_05_09` (consolidated v8 SSOT — supersedes archived
  `manifest_v7_schema_migration_design_2026_05_08`) — both plans touch manifest schema + enumeration. v2 launch should
  happen AFTER v8 migration for write-side simplicity.
- `live_pipeline_mtds_mdps_features_2026_05_08` Phase 12 — batch-vs-live reconciliation needs the v2 expected universe
  to compute a meaningful completeness denominator per shard atom.

## Execution phases (promoted to active 2026-05-11)

> **Gate**: every phase below assumes G4 v8 schema has landed (`record_captured(service_emission_state=)` MANDATORY,
> v7 paths grep-zero). When G4 lands, flip the banner above + `status:` to `in-progress` + start Phase 1.

### Phase 1 — v2 enumerator implementation (P1, ~1 day)

- [ ] [SCRIPT] P1. Extend `instruments-service/scripts/enumerate_expected_universe.py` with `enumerate_v2()` function
      per the design § Implementation. Signature: `enumerate_v2(*, asset_group, catalog: InstrumentCatalog, date_axis:
      list[date], data_types: list[str]) -> Iterator[ExpectedRow]`. Cross-joins v1's date axis with catalog's per-
      instrument lifecycle, respecting per-asset_group lifecycle rules (cefi instrument-listing `active_from`/`active_to`,
      prediction market `market_created_at`/`settlement_time`, defi protocol-launch `PROTOCOL_LAUNCH_DATES`, sports
      per-fixture lifecycle).
- [ ] [SCRIPT] P1. Add CLI flag `--enumerator-version v1|v2` (default v2 once G4 lands). v1 stays callable via flag for
      diff-debug.
- [ ] [SCRIPT] P1. Unit test: `tests/test_enumerate_expected_universe.py` covers per-asset-group lifecycle rules with
      synthetic catalog + date axis. Asserts: cefi instrument delisted on 2024-06-01 → no rows after; prediction market
      `settlement_time=2024-12-31` → no rows in 2025; defi protocol `PROTOCOL_LAUNCH_DATES[(arbitrum, aave-v3)]=
      2022-03-16` → no rows before.
- [ ] [SCRIPT] P1. Integration test: real instruments-service catalog read (~50K cefi instruments) × 100-day axis × 3
      data_types → asserts ~15M rows enumerated within 60s on a same-region VM. Assert no v1 row missing from v2 output
      (v2 is strict superset).

### Phase 2 — Per-VM launcher + watchdog registration (P1, ~0.5 day)

- [ ] [SCRIPT] P1. New launcher `deployment-service/scripts/vm/launch-expected-universe-v2-vm.sh` per the workspace
      launcher SSOT. Args: `--asset-group <cefi|defi|tradfi|sports|prediction>` (sharding axis); `--clip-after <date>`
      optional. Sets `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=expected-universe-v2-{asset_group}-{RUN_TS}`. Reads
      `DEPLOYMENT_ENV` per bucket-name-SSOT rule.
- [ ] [SCRIPT] P1. Register `expected-universe-v2-` prefix in `deployment-service/scripts/vm/vm_zombie_watchdog.py`
      `VM_PREFIX_TO_BUCKET` dict (per "VM Naming Convention" rule). Bucket: the manifest's per-VM shard bucket.
      **After dict edit, RELAUNCH watchdog VM**.
- [ ] [SCRIPT] P1. Singleton-lock pattern in launcher: refuses launch if same-asset-group VM already RUNNING in zone
      (catalog reads are sequential per asset_group; thundering-herd protection — per `launch-sfi-forward-poll.sh`
      precedent).

### Phase 3 — Q1-resolution: sharding strategy (P1, ~0.25 day)

- [ ] [DECISION] P1. Resolve plan Q1: cefi spot/perp v2 = 180M rows → shard by venue (one VM per venue) per the design
      bias toward "single VM doesn't burn full catalog read just to enumerate". Verify on a same-region test VM that
      bybit-only enumeration completes in <30 min wall-clock. Document the venue-sharding decision in the plan body +
      codex SSOT before Phase 4 launch.

### Phase 4 — Production launch (P1, ~0.5 day wall-clock; 2-4 hrs per asset_group)

- [ ] [VM] P1. Launch v2 enumerator VMs per asset_group (~10 total: 7 cefi venues + 1 defi + 1 tradfi + 1 sports + 1
      prediction). Apply CLAUDE.md "No fire-and-forget VM launches" rule: verify STARTED event within 60s + ≥1 progress
      event per hour + STOPPED/FAILED at exit per VM. Total wall-clock ~3-4 hrs running in parallel.
- [ ] [VM] P1. Manifest consolidator daemon merges per-VM shards into canonical manifest. Expected: ~190M rows in
      `_index/availability_index.parquet`.
- [ ] [VERIFY] P1. Post-run verification (per "Plans Run To Actual Completion" HARD RULE):
      ```bash
      gsutil ls gs://{pid}-events/events/instruments-service/{today}/expected-universe-v2-*/   # STARTED+STOPPED for every VM
      python -c "import pyarrow.parquet as pq; t = pq.read_table('gs://{manifest_bucket}/_index/availability_index.parquet', columns=['capture_status']); from collections import Counter; print(Counter(t['capture_status'].to_pylist()))"
      # expect: expected_unattempted count ~190M; captured + empty_confirmed + attempted_failed unchanged
      ```
- [ ] [VERIFY] P1. Per-asset-group spot-check: sample 100 random `(instrument_id, day)` pairs per asset_group; assert
      lifecycle bounds enforced (no rows pre-`active_from` / post-`active_to` for cefi; no rows pre-genesis for defi;
      etc.).

### Phase 5 — Codex SSOT updates (P1, ~0.25 day) — per "Post-Plan-Phase Codex Audit" HARD RULE

- [ ] [CODEX] P1. UPDATE `codex/02-data/availability-manifest-and-data-status.md` § "Expected universe": extend to
      describe v1 (venue-grain) vs v2 (instrument-grain), with the per-asset-group grain table from this plan body.
      Reference: this plan + the umbrella `manifest_evolution_master_2026_05_08.md` G3.
- [ ] [CODEX] P1. UPDATE `codex/02-data/honest-absence-downstream-handling.md`: add note that v2's
      `record_expected_unattempted` rows at instrument grain mean honest-coverage % calculations have a 100× larger
      denominator. Downstream consumers (deployment-api data-status drilldown, features-* pre-flight, ML training row
      counts) need to handle the volume via column-projection + duckdb-style aggregates.
- [ ] [CODEX] P1. UPDATE `unified-trading-pm/codex/05-infrastructure/launcher-script-ssot.md`: register the new
      `launch-expected-universe-v2-vm.sh` launcher + the `expected-universe-v2-` watchdog prefix.

## Done definition (per "Plans Run To Actual Completion" HARD RULE)

**Code gates**:
- ✅ `instruments-service/scripts/enumerate_expected_universe.py` extended with `enumerate_v2()`; unit + integration
  tests pass; basedpyright clean; ruff clean.
- ✅ `deployment-service/scripts/vm/launch-expected-universe-v2-vm.sh` shipped per launcher SSOT; watchdog dict updated;
  watchdog VM relaunched.
- ✅ codex docs (3 listed in Phase 5) updated in same logical unit as the operational launch.

**Operational gates** (the load-bearing half — code-shipped ≠ operationally-shipped):
- ✅ All ~10 v2-enumerator VMs ran to completion. STARTED + ≥1 hourly progress + STOPPED in event stream per VM.
- ✅ Canonical manifest contains ~190M `expected_unattempted` rows at instrument grain.
- ✅ Per-asset-group spot-check (100 random pairs) confirms lifecycle bounds enforced.
- ✅ Downstream consumer smoke (deployment-api data-status drilldown / features-* pre-flight / ML training denominator)
  runs against the 190M-row manifest without timeout — confirms readers handled the 100× scale-up.

**Full-execution criterion**:
- ✅ ~190M `expected_unattempted` rows on canonical manifest at instrument grain across all 5 asset_groups.
  - **What ran**: `launch-expected-universe-v2-vm.sh --asset-group {X}` × 10 VMs (7 cefi venues + 1 defi + 1 tradfi +
    1 sports + 1 prediction). Duration: ~3-4 hrs parallel wall-clock.
  - **Verification**: `pq.read_table(canonical_manifest, columns=['capture_status'])` Counter shows
    `expected_unattempted` ≈ 190M; per-asset-group spot-check passes lifecycle bounds.

**Handoff exception(s)**: none — this plan ships its own operation; no downstream takes over.

## Prerequisites (BLOCKING — won't start Phase 1 until satisfied)

1. **G4 v8 schema landed** per `manifest_schema_final_gate_2026_05_09.md`. Verifier: `record_captured()` callsites
   workspace-wide require `service_emission_state=` kwarg; v7 reader fallback grep returns zero hits.
2. **PROTOCOL_LAUNCH_DATES SSOT complete** for DeFi. Verifier: `uac@<sha>` has all (chain, protocol) launch dates
   either confirmed or routed via `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION`. Currently slot 5 shipped 12 confident
   pairs + 13 pending @uac@495d262.
3. **instruments-service catalog read endpoint live**. Verifier: `python -c "from instruments_service.catalog import
   InstrumentCatalog; c = InstrumentCatalog.from_canonical_bucket(); print(len(c.all_instruments()))"` returns >0 for
   each asset_group.
