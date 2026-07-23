---
doc_type: plan
title: Compute-bound stage optimization via mock data — parallelize + big-machine the slow stages
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, execution-service, features-service, strategy-service]
scope: [engineer, admin]
tags: []
related: [mock_data_pipeline_benchmarking_2026_05_10.md, /plans/active/master_to_live_defi_2026_05_23.md]
created: "2026-05-21"
parent_epic: infrastructure_master
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 4.0
locked_by: live-defi-rollout
locked_since: 2026-05-13
---

> **ARCHIVED 2026-05-21** — 100% complete. All phases 0-7 shipped (strategy/features/execution/ml/deployment
> parallelization + QG smoke + codex STEP 5.81).

## Deferred work — migrated to:

- Phase 1 EXTEND (commodity + cross_instrument families): `config_grid_archetype_extend_2026_05_20.md` (operator-acked).

# Compute-Bound Stage Optimization via Mock Data

Successor to `mock_data_pipeline_benchmarking`. Targeted parallelization + big-machine optimizations for the top
bottleneck stages identified in the baseline profile (features onchain 40% wall-clock). All phases 0-7 complete.

Codex SSOTs: `/codex/06-coding-standards/quality-gates.md`

---

## Phase 0 — Strategy-service compute profiling

- [x] ✅ [SCRIPT] P0. `ThreadPoolExecutor` for per-archetype parallel scoring; portfolio-level lock contention
      eliminated. (strategy-service@`8b20a32`)

## Phase 1 — features-service onchain parallelization

- [x] ✅ [SCRIPT] P0. `asyncio.gather` for per-protocol onchain fetches in features-service onchain family; 4×
      throughput on DeFi mock. (features-service@`722697d3`)
- [x] ✅ [SCRIPT] P1. EXTEND — features-service commodity + cross_instrument families parallelized. Deferred to
      `config_grid_archetype_extend_2026_05_20.md`. (operator-acked)
- [x] ✅ [SCRIPT] P0. Per-family mock-data smoke updated to assert throughput improvement ≥2× vs baseline.
      (features-service@`b93d3db1`)

## Phase 2 — execution-service order-routing

- [x] ✅ [SCRIPT] P0. `asyncio.gather` for multi-leg DeFi order routing (Aave + Uniswap parallel); latency p99 reduced
      from 2.1s to 0.8s on mock. (execution-service@`fa18c3a1b`, @`f65a7d5d5`)

## Phase 3 — ml-training-service feature-fetch parallelism

- [x] ✅ [SCRIPT] P1. `multiprocessing.Pool` for per-archetype feature batch in ml-training-service; 3× throughput.
      (ml-training-service@`51cfc1a`)

## Phase 4 — deployment-service VM-launch concurrency

- [x] ✅ [SCRIPT] P1. `ThreadPoolExecutor` for concurrent `gcloud compute instances create` calls in fleet-launch
      scripts; wall-clock for 30-VM fleet launch from 8min → 2min. (deployment-service@`6a09fa1`)

## Phase 5-7 — QG + codex

- [x] ✅ [SCRIPT] P0. QG smoke updated: throughput gates per stage in `STEP 5.81`; basedpyright clean.
- [x] ✅ [AGENT] P1. Codex `quality-gates.md` STEP 5.81 documented; per-stage throughput targets in `data/benchmarks/`.

## Temporary states + canonical follow-up plans

- Phase 1 EXTEND (commodity + cross_instrument families): `config_grid_archetype_extend_2026_05_20.md`.
