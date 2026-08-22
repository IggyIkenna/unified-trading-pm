---
doc_type: plan
title: ShardPlan — sharding, workers-per-VM and machine shapes inferred from measured resources, owned by the deployment control plane; multiprocess shard loop; streaming readers; monitors for multi-shard VMs
summary: >-
  Child of trading_pipeline_smoke_and_shard_telemetry_2026_08_22 under infrastructure_master. Ruling D18 (operator Q&A
  2026-08-22) — horizontal vs vertical scaling is decided from the ShardRunTelemetry baseline (peak RSS → shape; CPU
  vs inbound/outbound bytes → fan-out vs bigger VM; source_axis → contention rule: fan-out is free across different
  data sources, capped per source) and expressed as a UAC ShardPlan contract resolved by UTL, launched by
  deployment-service and monitored globally in deployment-api/UI. Service CLIs take --shard-spec; launchers stop
  hard-coding MACHINE_TYPE (129 today, 8 distinct values) and WORKERS (23); the shard loop runs spawn-context processes
  (threads stay only for per-request I/O); MDPS tick reads and execution MTDS reads stream (polars scan + streaming
  collect / pyarrow iter_batches) before features; a QG ratchet bans NEW ThreadPoolExecutor at shard level.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library, deployment-service, deployment-api, deployment-ui, market-tick-data-service, market-data-processing-service, features-service, ml-service, strategy-service, execution-service, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [shard-plan, scaling, machine-type, workers, multiprocess, streaming, launchers, monitors, telemetry]
related:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md,
    /plans/active/trading_pipeline_all_shard_smoke_matrix_2026_08_22.md,
    /codex/05-infrastructure/deployment-observability.md,
    /plans/epics/infrastructure_master.md,
  ]
created: 2026-08-22
last_updated: 2026-08-22
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 20
estimate_calibrated_ai_days: 16
assigned_role: infra
effort: max
drift_direction: advance-code
depends_on: [trading_pipeline_smoke_and_shard_telemetry_2026_08_22]
locked_by:
locked_since:
supersedes:
superseded_by:
source: [operator Q&A 2026-08-22 (slot 6) — "machine types should be built from the resource needed ... sharding shouldn't be hard coded rather inferred from the deployment and managed/monitored at a global level. multi process generally preferred"; "shard-loop runner goes multiprocess now; readers stream where a shard exceeds the memory ladder"]
context_scope:
  [
    unified-trading-library/unified_trading_library/deployment_shard_responsibility.py,
    unified-trading-library/unified_trading_library/deployment_registry.py,
    unified-api-contracts/unified_api_contracts/internal/cloud_run_job_registry.py,
    deployment-service/scripts/vm/launch-mdps-sharded-backfill.sh,
    deployment-service/scripts/vm/launch-features-sharded-backfill.sh,
    deployment-service/scripts/vm/launch-features-vm.sh,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/06-coding-standards/data-engine-selection.md,
    /codex/06-coding-standards/service-orchestration-patterns.md,
  ]
---

# ShardPlan — resource-driven sharding, shapes and workers

> **Human plan**, child of
> [`trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md`](/plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md).
> Governing ruling: D18. Consumes the telemetry baseline (parent T1) and the matrix results
> ([`trading_pipeline_all_shard_smoke_matrix_2026_08_22.md`](/plans/active/trading_pipeline_all_shard_smoke_matrix_2026_08_22.md)).

## Measured starting point

`ShardResponsibility` / `responsibility_for_deployment()` (UTL) resolves a deployment to the data shards it owns — the
only sharding SSOT, data-plane only. Work partitioning lives in bash (year-sharded launchers); shard-index CLI args
exist only in three MTDS one-off scripts; `ThreadPoolExecutor` sizes are code constants (IS 156, MTDS 372, MDPS 27,
features 8, ML 5, strategy 2, execution 5 sites; `ProcessPoolExecutor` only in features 6 / execution 9); 129 launchers
hard-code `MACHINE_TYPE` (8 distinct values) and 23 hard-code `WORKERS=`; streaming reads: MDPS 0 of 26 eager, features
0 of 83, execution 7 of 34.

## Todos

- [ ] [DESIGN] P0. **UAC `ShardPlan` contract** — `unified_api_contracts.internal.shard_plan`: shard atom → list of
      shards, `worker_unit` (D15 axes), `workers_per_vm` (processes), `machine_shape`, `pricing_class`, `source_axis`
      + per-source concurrency cap (Tardis = 1 fleet-wide), `expected_*` from the telemetry baseline, `plan_version`.
      Done-when: contract + guard tests shipped.
- [ ] [BACKEND] P0. **UTL resolver** — `resolve_shard_plan(telemetry_baseline, shard_universe, constraints)` next to
      `deployment_shard_responsibility.py`: peak-RSS p95 → smallest shape under the 64 GB ceiling, CPU-bound vs
      I/O-bound (bytes_in/out) → horizontal vs vertical, `source_axis` contention rule. Done-when: unit tests over
      recorded telemetry fixtures reproduce a hand-checked plan.
- [ ] [BACKEND] P0. **`--shard-spec` in every service CLI** (IS, MTDS, MDPS, features, ML, strategy, execution) via
      the shared `cli-convention` parser: the service executes exactly the shards the plan names, with
      `workers_per_vm` processes; env vars (`UnifiedCloudConfig`) only override, never define. Done-when: each service
      runs one plan-driven shard set end to end.
- [ ] [INFRA] P0. **Launchers read the plan** — `deployment-service/scripts/vm/launch-*.sh` take `--shard-plan <gcs
      uri>`; shape, workers and SPOT/on-demand come from it; delete every `MACHINE_TYPE=` / `WORKERS=` literal; the
      guard test in `cloud_run_job_registry` gains a sibling for VM launchers. Done-when: `rg MACHINE_TYPE=
      deployment-service/scripts/vm` = 0.
- [ ] [BACKEND] P0. **Global manager in deployment-service + view in deployment-api/UI** — plans stored at
      `gs://<deployment bucket>/_ops/shard_plans/<service>/<plan_version>.json`, published to the deployment registry;
      UI shows per worker unit plan vs actual (telemetry), drift flagged. Done-when: one service's plan visible with
      actuals beside it.
- [ ] [BACKEND] P0. **Multiprocess shard loop** — UTL `run_shard_loop` spawns `multiprocessing.get_context("spawn")`
      workers per shard (the strategy `ClientWorker` pattern), telemetry recorder per process, failure isolation per
      shard; per-request I/O threads may remain inside a worker; QG ratchet bans NEW shard-level `ThreadPoolExecutor`.
      Done-when: MDPS + features + ML shard loops run on processes; ratchet baseline frozen.
- [ ] [BACKEND] P0. **Streaming readers where the ladder demands** — MDPS tick reads (`live_workers.py` and batch
      orchestrators) and execution MTDS reads move to `pl.scan_parquet(...).collect(streaming=True)` / pyarrow
      `iter_batches`; features next; single-engine rule kept. Done-when: peak RSS per shard-day drops in telemetry for
      the two heaviest MDPS cells and the heaviest execution backtest cell (numbers cited).
- [ ] [BACKEND] P0. **Intra-shard subprocess audit + QG hardening (operator refinement 2026-08-22)** — intra-shard
      multiprocessing is ALWAYS permitted (distinct from the D15 worker unit); audit every existing intra-shard
      subprocess/worker (features `ProcessPoolExecutor` ×6, execution ×9, strategy `ClientWorker` spawns, script-level
      `multiprocessing`) and fix memory-intensive ones to STREAM their reads and FLUSH/exit per shard (no arena
      accumulation across shards); ship a QG check that a subprocess worker reading parquet above a size threshold uses
      a streaming path and a per-shard flush/exit. Done-when: audit table appended to this plan + the check wired into
      each repo's `quality-gates.sh`.
- [ ] [INFRA] P1. **Monitors for multi-shard VMs** — dp-heartbeat-watcher / exit-code monitor / Cloud Run monitors and
      alert dedup keyed by the D15 worker unit + checkpoint growth, never "one VM = one shard". Done-when: zero false
      DP-\* alerts across one matrix run (shared done-when with the matrix child).
- [ ] [DOC] P1. **Codex** — new codex SSOT `shard-plan` under `codex/05-infrastructure/` (contract, resolver rule, owner, how scaling
      decisions are read from telemetry); `vm-launcher-runbook.md` + `service-orchestration-patterns.md` updated for
      processes + streaming. Done-when: docs merged, `check_codex_refs.sh` clean.
- [ ] [DOC] P2. **Archive** per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` once every todo is
      `[x]`.

## Codex SSOTs

- `/codex/05-infrastructure/deployment-observability.md` — compute-unit classification the plan keys on.
- `/codex/05-infrastructure/vm-launcher-runbook.md` — launcher rules; plan-driven launch lands here.
- `/codex/06-coding-standards/service-orchestration-patterns.md` — per-shard cleanup + loop discipline.
- `/codex/06-coding-standards/data-engine-selection.md` — single-engine rule the streaming readers must keep.

## Progress Log

- **2026-08-22 (operator Q&A, slot 6)**: Created from ruling D18 + the pools/streaming ruling.
- **2026-08-22 (operator, mid-session)**: Intra-shard multiprocessing ruled always-permitted; audit + stream/flush QG hardening todo added.
