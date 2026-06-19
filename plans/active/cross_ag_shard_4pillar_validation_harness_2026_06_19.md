---
title: "Cross-AG 4-pillar shard-validation harness + first comprehensive run + QG smoke"
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
created: 2026-06-19
status: active
priority: P2
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Cross-AG 4-pillar shard-validation harness

**Codex SSOTs:** `codex/04-architecture/shard-level-failure-isolation.md` ·
`codex/02-data/availability-manifest-and-data-status.md` · `plans/epics/infrastructure_master.md` (shard-granularity
SSOT).

## Brief

An audit found shard 4-pillar validation was a GAP: only TradFi had a named pillar script
(`market-tick-data-service/scripts/validate_tradfi_ohlcv_4pillar.py`); NaN-ratio + cluster-coverage pillars were
unverified fleet-wide; no comprehensive cross-AG run existed. This plan generalises the harness to all 5 asset_groups ×
both buckets, RUNS it (first comprehensive run), wires it as a repeatable smoke, and files the real findings it
surfaced.

The 4 pillars (shard-granularity SSOT): (1) row_count > 0 OR `record_empty`; (2) NaN-ratio < threshold; (3) schema
matches the UAC contract; (4) cluster coverage ≥ expected (bundled data_types).

## Harness

The harness reads the canonical `_index/availability_index.parquet` directly (read-only — bypasses the consolidator
liveness gate, which is for live consumers not a sampler), drives a date-stratified sample of shard parquets per
AG×data_type off the index `date` column, and checks all 4 pillars per parquet. Pillar-3 is path-aware (identity columns
carried as hive path keys are not required as row columns) and accepts native time columns
(`ts_event`/`date`/venue-native). Pillar-4 reads the manifest `capture_status` for bundled types (the writer gates
cluster coverage at `record_captured`).

## Phase 1 — Harness + first comprehensive run

- [x] ✅ [SCRIPT] P0. Build AG-parametrized `e2e-testing/scripts/validation/validate_shards_4pillar.py` (all 5 AGs ×
      tick + instruments buckets; UAC schema contract; manifest-index cross-check; date-stratified sampling;
      lifecycle-marked). — e2e-testing@42eb9a4 | ruff-green; generalises the tradfi-only pillar script.
- [x] ✅ [SCRIPT] P0. RUN the first comprehensive cross-AG validation (per-data-type=5, all AGs/buckets). Result: **145+
      sampled shards; cefi 21/21, tradfi 29/29, sports 10/10, prediction 10/10 GREEN; defi 44/46 green** (2 genuine
      0-row pillar-1 failures, Phase-3 P1). instruments-store buckets store reference catalogue
      (`_catalogue/`+`_index/`), NOT per-shard parquets → 0 sampled is correct (manifest-index pillar check still runs).
      — e2e-testing@42eb9a4 | report `/tmp/shard_4pillar_report.json`.

## Phase 2 — Repeatable smoke wiring

- [x] ✅ [SCRIPT] P0. Wire `validate_shards_4pillar.py --smoke` into `market-tick-data-service/scripts/quality-gates.sh`
      STEP 5.88 (primary-consumer QG, per the Peripheral-Script-QG rule) — ruff-lint + warn-only smoke (small sample,
      tick bucket) that proves the harness imports + lists + reads; the comprehensive run is the operator/scheduled
      invocation. — market-tick-data-service@4da1cc9 (dirty-deps carve-out: UTL foreign-dirty).

## Phase 3 — Real findings surfaced by the first run

- [ ] [DATA] P1. **DeFi `vault_share_price` silent-empty parquets** — 0-row parquets physically present in GCS
      (`market-data-tick-defi-prd`, legacy 2021/2022 `batch_onchain_subgraph` dates, e.g.
      `…/data_type=vault_share_price/vault_share_price_1647432000.parquet`) carry ONLY identity columns + 0 rows. Honest
      absence IS recorded in the manifest (64410 `empty_confirmed` rows for this data_type), so these parquets are
      redundant placeholders that should be manifest-only `empty_confirmed` with NO parquet object (the banned "empty
      placeholder that looks populated" antipattern, CLAUDE.md § Manifest). **Fix**: delete the 0-row
      `vault_share_price` parquets from GCS (manifest already correct) after a scoped walk confirms they are all
      empty-confirmed-in-manifest; verify no consumer reads the parquet directly. Repo: market-tick-data-service.
      Provenance: 4-pillar harness first comprehensive run 2026-06-19.
- [ ] [DATA] P2. **Manifest `row_count` column 100% NULL in the tradfi index** (likely fleet-wide) — the
      `_index/availability_index.parquet` `row_count` column is unpopulated for `captured` rows (100% null in tradfi),
      so a manifest-side phantom check (`captured & row_count<=0`) cannot run from the index alone (the harness guards
      against the false positive but loses the cheap manifest-side phantom signal). **Fix**: materialise `row_count` at
      `record_captured` (the writer has the df length) so the consolidated index carries it; then the manifest-side
      phantom detector becomes a cheap whole-corpus check. Repo: unified-trading-library (manifest_writer) +
      market-tick-data-service (recorder). Provenance: 4-pillar harness first comprehensive run 2026-06-19.

## Continuous verification

`validate_shards_4pillar.py --smoke` runs in MTDS `quality-gates.sh` (warn-only mechanism check). The comprehensive run
(`--per-data-type 5 --json-out …`) is operator-invokable; a scheduled validation job is the post-cutover successor (file
under this plan when scoped).

## Temporary states + their canonical follow-up plans

None — the harness is permanent; Phase-3 findings are tracked above.
