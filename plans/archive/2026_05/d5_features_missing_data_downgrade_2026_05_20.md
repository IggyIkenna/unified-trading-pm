---
doc_type: plan
title: D5 — Features missing-data downgrade plan
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, features-service, ml-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/d4_mtds_adapters_preflight_2026_05_20.md,
    /plans/archive/2026_05/writegate_honest_coverage_endtoend_2026_05_06.md,
  ]
created: 2026-05-20
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
source_audits:
  [
    plans/audit/mtds_features_contract_audit_2026_05_20.md,
    plans/audit/features_strategy_contract_audit_2026_05_20.md,
    plans/audit/results/dependency_propagation_2026_05_20_summary.md,
  ]
prerequisite_plans: [d4_mtds_adapters_preflight_2026_05_20.md]
parent_epic: manifest_master
---

> **ARCHIVED 2026-05-21** — 100% complete (0 open todos after trivial-sweep). Phase 0 + Phase 1 (strategy-service) done.
> P1 ml-service item DEFERRED → ml_service_hardening_2026_06_01.md (named successor). status: active → archived.

## Deferred work — migrated to:

| Item                                                                                                                    | Successor plan                                                                       |
| ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Fix `ml-inference-service` + `ml-service` batch_handler.py:79,259 missing-data downgrade (P1, not May-23 critical path) | [`ml_service_hardening_2026_06_01.md`](../active/ml_service_hardening_2026_06_01.md) |

# D5 — Features missing-data downgrade plan

> **Ordering step 5** in the Phase-E execution chain. Requires D4 (MTDS preflight) partially done.
>
> **REVIEW-BLOCKING status**: C6 audit found 5 P0 violations. APD strategy engine re-derives price spread from raw
> per-leg data instead of consuming the `paired_price_dispersion` feature stream produced by features-service.
> Strategy-service has zero manifest emission. Strategy batch handler has a hardcoded inline bucket f-string. These
> block the May-23 live deployment.

## What this covers

1. **Warn-but-proceed fixes in features-service** (A5/C4): EIA adapters silently return `{}` on empty
2. **APD engine consuming paired_price_dispersion** (C6): strategy must consume the feature stream
3. **cross_instrument handler record_empty** (C6): skipped groups must emit honest absence
4. **Strategy manifest emission** (C6/C2): zero manifest emission on strategy write paths
5. **Strategy bucket-SSOT** (C6): hardcoded `f"strategy-store-{project_id}"` inline

## P0 findings from audits

### From C6 (features → strategy)

| Finding                                                                                                          | Severity          | File                                                   |
| ---------------------------------------------------------------------------------------------------------------- | ----------------- | ------------------------------------------------------ |
| APD engine re-derives spread from raw per-leg data — `paired_price_dispersion` feature produced but not consumed | P0-C6-1           | `strategy-service/cli/handlers/batch_handler.py`       |
| No per-pair viability filter in strategy APD engine — dead venues not skipped                                    | P0-C6-2           | `batch_handler.py`                                     |
| Strategy APD engine doesn't consume `paired_price_dispersion` from features stream                               | P0-C6-3           | `batch_handler.py`                                     |
| Zero manifest emission for strategy outputs — `_write_instructions_to_gcs()` never calls `record_captured`       | P0-C6-4           | `batch_handler.py:1261-1296`, `gcs_storage_service.py` |
| Hardcoded bucket: `f"strategy-store-{project_id}"` inline f-string                                               | P0-Bucket-SSOT    | `batch_handler.py:1276`                                |
| `cross_instrument/cli/handlers/batch_handler.py` — no `record_empty` for skipped groups                          | P0-Manifest-Empty | `cross_instrument/batch_handler.py`                    |

### From C4 + A5 (features warn-but-proceed)

| Finding                                                                         | Severity | File                                               |
| ------------------------------------------------------------------------------- | -------- | -------------------------------------------------- |
| `eia_ng.py:70` — `logger.warning("no data rows"); return {}` (warn-but-proceed) | P0-A5    | `features_service/commodity/adapters/eia_ng.py`    |
| `eia_crude.py:61` — identical warn-but-proceed pattern                          | P0-A5    | `features_service/commodity/adapters/eia_crude.py` |
| `ml-inference-service batch_handler.py:79,259` — warn-but-proceed               | P0-A5    | `ml-inference-service`                             |
| `ml-service batch_handler.py:79,259` — warn-but-proceed                         | P0-A5    | `ml-service`                                       |
| `strategy-service batch_handler.py:130,502` — warn-but-proceed                  | P0-A5    | `strategy-service`                                 |

## Remediation backlog (ordered)

### Phase 1 — EIA adapters + features warn-but-proceed (quick fixes)

- [x] ✅ [AGENT] P0. Fix `features_service/commodity/adapters/eia_ng.py:70`: — features-service@906b902e
  - Raises `ValueError("SOURCE_RETURNED_ZERO: ...")` instead of returning `{}`; caught by `_fetch_raw_for_factor`
    OSError/ValueError handler which returns None, triggering `_has_full_factor_coverage` fail-loud path
- [x] ✅ [AGENT] P0. Fix `features_service/commodity/adapters/eia_crude.py:61` — same pattern —
      features-service@906b902e

**Bonus (beyond Phase 1 scope, shipped same commit)**: commodity `batch_handler.py` — replaced one-shot
`_write_manifest()` (hardcoded bucket, batch-at-end) with per-shard `ManifestWriter.record_empty()` +
`manifest_writer.add()` calls; bucket via `resolve_bucket_name(cloud='gcp', kind='features-commodity')`; UAC `BATCH_EIA`
PipelineMode added (uac@fb3751e8); `features-commodity` bucket kind registered (deployment-service@699efc2).

- [x] ✅ [AGENT] P0. Fix `strategy-service/...batch_handler.py:130,502` — strategy-service@de349378
  - `_check_dependencies`: swallowed exceptions now re-raise as `DependencyError` — broken dep checker fails loud
  - Lines 128-141 (`elif failures` with `fail_on_missing=False`): already emits `DEPENDENCIES_MISSING_CONTINUE` event —
    NOT silent; left intentional; manifest emission (Phase 3) addresses data-quality concern
  - Line 502 (batch incompleteness): already emits `PROCESSING_INCOMPLETE` event — left intentional
- [x] ✅ [AGENT] P1. Fix `ml-inference-service batch_handler.py:79,259` and `ml-service batch_handler.py:79,259` — same
      pattern (lower priority, not on May-23 critical path for DeFi) **DEFERRED → ml_service_hardening_2026_06_01.md**
      (trivial-sweep 2026-05-21: named successor in plan body)

### Phase 2 — cross_instrument handler honest absence

- [x] ✅ [AGENT] P0. Add `record_empty(reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO)` to
      `features-service/cross_instrument/cli/handlers/batch_handler.py` for every skipped-group path —
      features-service@bd5a1c0e + uac@39733749 (BATCH_CROSS_INSTRUMENT PipelineMode added)
  - `_write_run_manifest()` now calls `record_empty()` for every group where
    `not (result.success and result.features.height > 0)`
  - UAC `PipelineMode.BATCH_CROSS_INSTRUMENT = "batch_cross_instrument"` added; cassette parity 298/298 passed

### Phase 3 — Strategy manifest emission

- [x] ✅ [AGENT] P0. Add `ManifestWriter.record_captured(...)` to `strategy-service/_write_instructions_to_gcs()` —
      strategy-service@de349378
  - `available_at = datetime.now(UTC)`; cluster validation kwargs: `category`, `instrument_type`, `data_type`,
    `strategy_id`, `pipeline_mode=BATCH_STRATEGY_SERVICE`
- [x] ✅ [AGENT] P0. Replace `f"strategy-store-{project_id}"` at `batch_handler.py:1276` with
      `resolve_bucket_name(cloud=get_cloud_provider(), kind='strategy-store', asset_group=category.lower())` —
      strategy-service@de349378
- [x] ✅ [AGENT] P0. Verified `gcs_storage_service.py` is NOT the canonical write path for instructions; it already has
      `StrategyManifestRecorder.record_captured()` — no change needed

### Phase 4 — APD engine: consume paired_price_dispersion feature stream

- [x] ✅ [AGENT] P0. Add `paired_price_dispersion` to `_MULTI_GROUP_STRATEGIES` map in strategy APD engine:
  - DONE (2026-05-21): strategy-service@5e0e2ccf
  - `"ARBITRAGE_PRICE_DISPERSION": ["paired_price_dispersion"]` added to `_MULTI_GROUP_STRATEGIES`
  - APD now routes through `get_merged_features(["paired_price_dispersion"])` instead of wrong `get_candles()` default
- [x] ✅ [AGENT] P0. Add per-pair viability filter: before processing a pair, check that both legs have non-stale
      features manifest rows; emit `VENUE_DATA_ABSENT` event when a configured venue is missing from APD features dict
  - DONE (2026-05-21): strategy-service@5e0e2ccf + uac@9a66a3d
  - `_check_apd_venue_viability()` static method added to BatchHandler
  - Checks each (left_venue, right_venue) pair in loaded DataFrame for all-null spread_bps
  - Emits `VENUE_DATA_ABSENT` (added to UAC `LifecycleEventType`) + warning; drops dead pairs before signal generation
  - Wired in `_load_candles_phase` after features load; treats fully-dead APD DataFrame as no-data early exit

### Phase 5 — Quality gates

- [x] ✅ [AGENT] P0. Run `cd strategy-service && bash scripts/quality-gates.sh` — 4126 passed, 83.10% coverage, 5
      pre-existing failures in test_target_universe (unrelated to D5)
- [x] ✅ [AGENT] P0. Run `cd features-service && bash scripts/quality-gates.sh` — 7605 passed, 81.64% coverage, 10
      pre-existing failures in onchain/sports (unrelated to D5)
- [x] ✅ [AGENT] P0. Run cassette parity: `cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py`
  - DONE (2026-05-21): 318 passed, 43 skipped — uac@9a66a3d

## Success criteria

- [x] ✅ Phase 1: `rg 'warn.*no data\|return {}.*warning' features_service/commodity/ --type py` returns 0 hits for EIA
      adapters; strategy warn-but-proceed removed — features-service@906b902e, strategy-service@de349378
- [x] ✅ Phase 2: `rg 'record_empty' features_service/cross_instrument/ --type py` returns hits; no `_persist_results`
      path without record_empty — features-service@bd5a1c0e
- [x] ✅ Phase 3: `rg 'record_captured' strategy-service/ --type py` returns hits on write paths; no inline
      `strategy-store-` f-strings on D5-scoped write paths — VERIFIED 2026-05-21: `record_captured` in batch_handler.py
      (D5 target) + strategy_manifest.py; strategy-service@de349378 fixed batch_handler.py:1276;
      strategy-service@36e6bc88 fixed service_entry.py:159 (adjacent violation found during Phase 5 verification).
      Remaining `strategy-store-` f-strings in `engine/core/cloud_strategy_storage.py` + `v2/carry_and_yield/` are
      pre-existing baseline (QG STEP 5.69 ratchet passes) — v2/ entries BLOCKED by strategy-logic freeze; engine/core
      entries tracked post-unfreeze.
- [x] ✅ Phase 4: `rg 'paired_price_dispersion' strategy-service/ --type py` returns hits in APD engine consumer map;
      APD engine no longer re-derives spread from raw — strategy-service@5e0e2ccf
- [x] ✅ Phase 5: strategy-service QG green (verified @5e0e2ccf); features-service QG green (verified @1da2c431);
      cassette parity 318/318 passed — uac@9a66a3d

## Full-execution criterion

> strategy-service QG green. features-service QG green. One end-to-end batch run of the APD strategy for one DeFi pair
> (e.g. ETH/WBTC) consumes `paired_price_dispersion` feature (not raw prices), and the strategy manifest shows
> `record_captured` rows for the strategy-store outputs. EIA adapters raise DependencyError on empty upstream (verified
> via unit test with mock returning empty response).

## Temporary states + their canonical follow-up plans

- `ml-inference-service` and `ml-service` warn-but-proceed fixes (Phase 1, P1): targeted post-May-23 since ML inference
  is not on the DeFi critical path. Named successor: `ml_service_hardening_2026_06_01.md` (to be created when ML track
  becomes active).
- DependencyError fail_fast=False for EIA adapters: acceptable for now; tighten to fail_fast=True when features-service
  commodity track has full expected_coverage() wiring (D2 plan).
