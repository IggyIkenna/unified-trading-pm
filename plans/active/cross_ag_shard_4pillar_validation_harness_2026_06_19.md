---
doc_type: plan
title: Cross-AG 4-pillar shard-validation harness + first comprehensive run + QG smoke
summary:
  "Build and run a cross-asset-group 4-pillar shard validation harness (row_count, NaN-ratio, schema, cluster-coverage)
  across all 5 AGs and wire it as a repeatable smoke test."
status: active
nature: process
stage: [meta]
repos: [e2e-testing, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [validation, shard, 4-pillar, cross-asset-group, harness, smoke-test, manifest]
related: []
created: 2026-06-19
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: data-pipeline-engineer
drift_direction: advance-code
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-05-21
supersedes:
superseded_by:
depends_on:
source:
asset_group: cross-asset
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

- [x] ✅ [DATA] P1. **DeFi `vault_share_price` silent-empty parquets — DELETED + harness GREEN** (2026-06-19). Scoped
      walk of `market-data-tick-defi-prd` found 7,683 `vault_share_price` parquets; OPENED every footer (row count,
      never size-as-proxy): **1,113 genuinely 0-row** (legacy 2020-2022 `batch_onchain_subgraph` VAULT cells) AND every
      one's `(date,data_type)` manifest cell is NON-captured (honest `empty_confirmed`/`SOURCE_RETURNED_ZERO` after the
      N5 rebuild) → deleted (1,113/1,113, 0 failures, ~3.40 MB reclaimed); the other **6,570 HAS_DATA (≥1 row) were
      PRESERVED** (real captured vault cells, e.g. MAKER 2023 / ETHENA 2024) — redundant-empty cleanup, NOT a
      twin-delete. No consumer reads these parquets directly (the only writer of 0-row markers is the
      vault_share_price_handler empty-marker path; the manifest empty_confirmed row is the cell SSOT). **4-pillar re-run
      on defi: 67/67 GREEN, p1_fail=0 (was 2), manifest_phantom_captured_zero_rows=0, overall_green=True.** Script:
      `market-tick-data-service/market_tick_data_service/scripts/delete_defi_zero_row_placeholders.py` (oneoff,
      lifecycle-marked). Provenance: 4-pillar harness first comprehensive run 2026-06-19.
- [x] ✅ [CODE] P2. **Manifest `row_count` now materialised on captured rows by the WRITER** — unified-trading-library
      `manifest_writer._records_to_dataframe()` now emits a `row_count` column == `instrument_count` (the same logical
      value: `effective_count`==`len(df)` at `record_captured` / `total_rows` at `record_captured_from_counts`; the
      legacy `add(row_count=...)` path already maps row_count→instrument_count), and the read/merge backfill
      (`_read_index._backfill` + `_writer_io._backfill_columns`) backfills `row_count` FROM `instrument_count` for
      legacy indexes — so the consolidated `_index` carries `row_count` populated on captured rows going forward, making
      the cheap manifest-side `captured & row_count<=0` phantom / 4-pillar proxy work from the index alone (it was 100%
      NULL). Regression test `tests/unit/test_manifest_writer_row_count_materialised.py` (3 cases); 446 manifest tests
      pass. **Diagnosis note**: the index ALREADY had a `row_count` COLUMN (from rebuild scripts) but the writer
      serializer never populated it — `instrument_count` was the materialised count. Repo: unified-trading-library.
      Provenance: 4-pillar harness first comprehensive run 2026-06-19.
- [ ] [SCRIPT] P3. **DEFERRED (optional) — backfill `row_count` into HISTORICAL consolidated `_index` rows fleet-wide**
      (currently 100% NULL on captured rows in the existing on-disk indexes; the writer-fix only populates NEW
      captures). Cheap: a single-walk pass per AG bucket that sets `row_count = instrument_count` where
      `capture_status=='captured'` and `row_count` is null, then re-writes the index (or rides the next manifest
      canonicalisation walk). Until then, the harness/read-path backfill already derives `row_count` from
      `instrument_count` at READ time, so the cheap phantom check works for any consumer that reads via
      `read_availability_index`; this todo only materialises it ON DISK. Repo: market-tick-data-service (index
      canonicalisation). Provenance: P2 follow-up, 2026-06-19.

## Continuous verification

`validate_shards_4pillar.py --smoke` runs in MTDS `quality-gates.sh` (warn-only mechanism check). The comprehensive run
(`--per-data-type 5 --json-out …`) is operator-invokable; a scheduled validation job is the post-cutover successor (file
under this plan when scoped).

## Temporary states + their canonical follow-up plans

None — the harness is permanent; Phase-3 findings are tracked above.
