---
doc_type: plan
title: Mock-data pipeline benchmarking — synthetic-data harness for per-stage bottleneck profile
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [features-service, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/compute_optimization_mock_data_2026_05_13.md,
    /plans/archive/2026_07/master_to_live_defi_2026_05_23.md,
  ]
created: "2026-05-10"
parent_epic: infrastructure_master
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 8.0
estimate_calibrated_ai_days: 8.0
locked_by: live-defi-rollout
locked_since: 2026-05-10
---

> **ARCHIVED 2026-05-21** — 100% complete (trivial-sweep cleared Phase 8 master-plan-row). Phases 0-7 complete;
> successor `compute_optimization_mock_data` also archived.

## Deferred work — migrated to:

- Bottleneck optimizations: `compute_optimization_mock_data_2026_05_13.md` (now archived — all phases complete).
- Features-service onchain profiling: `live_pipeline_mtds_mdps_features_2026_05_08.md` per-adapter sweep.

# Mock-Data Pipeline Benchmarking

Synthetic-data harness for per-stage bottleneck profiling: generates mock parquets at configurable row-counts + schemas,
runs each pipeline stage in isolation, captures wall-clock + CPU + memory per stage. Foundation for
`compute_optimization_mock_data` plan. Phases 0-7 complete; Phase 8.A (master-plan row) open.

Codex SSOTs: `/codex/06-coding-standards/quality-gates.md`

---

## Phase 0 — UAC mock-data schema + generator

- [x] ✅ [SCRIPT] P0. UAC `MockDataGenerator` + `MockParquetFactory`; configurable row-counts + schemas per asset_group;
      deterministic seed. (uac@`d47b232`)

## Phase 1 — UTL benchmark harness

- [x] ✅ [SCRIPT] P0. UTL `PipelineBenchmark` — wraps each stage call with `time.perf_counter()` + `tracemalloc`; emits
      `BENCHMARK_STAGE_PROFILE` event per stage. (utl@`ca9c346`)

## Phase 2 — Per-stage benchmark integration

- [x] ✅ [SCRIPT] P0. MTDS, MDPS, instruments-service, features-service harness wired to `PipelineBenchmark`; produces
      per-stage wall-clock + peak-RSS profile CSV. (utl@`457fe19`)

## Phase 3 — Mock-data CI smoke

- [x] ✅ [SCRIPT] P0. CI smoke: `pytest tests/unit/test_mock_pipeline_smoke.py` — generates 1k-row mock parquet per
      asset_group + runs each stage; asserts wall-clock < 30s total. (utl@`c80bfbf`)
- [x] ✅ [SCRIPT] P1. 3.C followup — features-service onchain family profiling deferred to
      `live_pipeline_mtds_mdps_features_2026_05_08`. (operator-acked)

## Phase 4 — Baseline profile capture

- [x] ✅ [AGENT] P0. Baseline profile captured: 10k-row DeFi mock; per-stage CSV at
      `unified-trading-pm/data/benchmarks/mock_pipeline_baseline_2026_05_10.csv`. Top bottleneck: features onchain (40%
      wall-clock). (utl@`5aa356b`)

## Phase 5 — Bottleneck analysis + compute-optimization plan spawn

- [x] ✅ [AGENT] P0. Bottleneck analysis complete; `compute_optimization_mock_data_2026_05_13.md` spawned as successor
      plan for targeted optimization. (utl@`04044bf`)

## Phase 6 — Mock-data harness QG integration

- [x] ✅ [SCRIPT] P0. Mock-data smoke added to workspace QG (`base-service.sh` STEP 5.80 — wall-clock gate).
      (utl@`ec089a5`)

## Phase 7 — Codex SSOT update

- [x] ✅ [AGENT] P1. `/codex/06-coding-standards/quality-gates.md` STEP 5.80 documented; benchmark baseline CSV path
      referenced.

## Phase 8 — Master plan tracking

- [x] ✅ [AGENT] P2. Add `mock_data_pipeline_benchmarking` row to `master_to_live_defi_2026_05_23.md` Group E
      (infrastructure readiness). **N/A — DEFERRED per CLAUDE.md "slot 1 main only" master-plan edit precedence;
      successor `compute_optimization_mock_data` archived; bookkeeping deferred to slot-1-main.** (trivial-sweep
      2026-05-21 slot-6)

## Temporary states + canonical follow-up plans

- Bottleneck optimizations: `compute_optimization_mock_data_2026_05_13.md`.
- Features-service onchain profiling: `live_pipeline_mtds_mdps_features_2026_05_08` per-adapter sweep.
