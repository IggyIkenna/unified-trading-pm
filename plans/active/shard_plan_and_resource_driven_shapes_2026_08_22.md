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
features 8, ML 5, strategy 2, execution 5 sites; `ProcessPoolExecutor` only in features 2 / execution 2 service-code +1
script — **re-measured 2026-08-22 autonomous session, corrects the original 6/9 claim**); 129 launchers hard-code
`MACHINE_TYPE` (14 distinct literal values, not 8 — **re-measured**) and 17 hard-code `WORKERS`-equivalent knobs (not 23
— **re-measured**, `rg -c 'WORKERS=' scripts/vm/` = 40 hits / 17 files); streaming reads: MDPS already has a streaming
primary path in `live_workers.py:501` (`pl.scan_parquet`, predicate-pushed) with only the no-filter fallback
(`:513`) and 7 other production call-sites still eager — **not "0 of 26"**; execution-service has **zero**
`scan_parquet`/`iter_batches` call sites anywhere in the repo (all reads are `pd.read_parquet`) — **not "7 of 34"**,
execution is actually the one furthest behind. features-service streaming state not re-verified this pass.

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
- **2026-08-22 (autonomous session, slot 2)**: Picked up under `/autonomous`. Verified no other active plan claims this scope; T1 `ShardRunTelemetry` (owned by a sibling agent per dispatch) not yet forked into its own `observability_master` child — still resident in the parent telemetry plan's T1 section, not shipped to UAC yet (confirmed via grep, no `shard_run_telemetry.py` found as of this check). Dispatched 5 parallel read-only Explore agents to map current state before writing code: (1) UAC internal/ contracts + cloud_run_job_registry pattern + guard-test convention, (2) UTL deployment_shard_responsibility/deployment_registry/ClientWorker spawn pattern/streaming-read state, (3) deployment-service launcher MACHINE_TYPE=/WORKERS= literal counts + shared bash lib + VM_PREFIX_TO_BUCKET registry, (4) deployment-api/deployment-ui operational-data query + panel conventions, (5) per-service CLI entrypoints + ProcessPoolExecutor sites + MDPS/execution streaming-read audit. Will design the UAC `ShardPlan` contract first once these land (todo 1, foundational — everything else depends on it). Noted: deployment-service has a pre-existing uncommitted `scripts/cloud-run/deploy-shared.sh` (not mine — will stage by name only, never touch).
- **2026-08-22 (autonomous session, slot 2 — research complete)**: All 5 mapping agents returned. §0 corrected in place
  (measured-vs-claimed drift — see diff above; largest gap: execution-service has ZERO streaming call sites, it is the
  furthest-behind service, not mid-migrated as the original "7 of 34" implied). Key landing points fixed for build:
  UAC `ShardPlan` → `unified_api_contracts/internal/shard_plan.py` (clean slate, mirror `cloud_run_job_registry.py`'s
  Pydantic/`StrEnum`/`Final[tuple]` style); `ShardRunTelemetry` (T1, sibling-owned) confirmed NOT landed — resolver
  input modeled as a local minimal `ShardTelemetryBaseline` (peak_rss_p95, cpu_pct_avg, bytes_in/out, source_axis) so
  this plan isn't blocked, swappable for the real contract once T1 ships. UTL `resolve_shard_plan()` → next to
  `deployment_shard_responsibility.py`, same import/typing conventions. UTL `run_shard_loop` → mirror
  strategy-service's real spawn-context worker (`strategy_service/client_worker.py` + spawn site
  `supervisor/client_admission_controller.py:108`); `unified_trading_library/services/client_worker_base.py` is the
  documented ABC to extend. Streaming-reader idiom in this codebase is pyarrow `ParquetFile.iter_batches`
  (`manifest_migrations/migrator.py:334`, `manifest_writer/_read_index.py:1475`) — NOT `pl.scan_parquet` (zero hits in
  UTL) — MDPS already leans polars-scan in its own app code (`live_workers.py`) so MDPS stays polars-scan for
  consistency with itself, execution-service gets pyarrow `iter_batches` per UTL's own idiom (no existing polars
  dependency there to disturb). `--shard-spec` lands once in `unified_trading_library/service_cli.py`
  `ServiceCLI.build_parser()` (shared by IS/MTDS/MDPS/strategy/execution's `ServiceCLI`-based entrypoints); ml-service
  and features-service have NO single unified CLI (features: 8+ per-family CLIs, ml: 2 separate train/infer CLIs) — flag
  support arrives fleet-wide via the shared parser the instant any of those sub-CLIs constructs a `ServiceCLI`, but
  per-family *consumption* wiring (actually restricting the run to the named shards) is scoped per sub-CLI, largest
  fan-out item in this plan. Launchers: shared helper `deployment-service/scripts/vm/lib/launcher_common.sh` is the one
  place to add a `lc_resolve_shard_plan` helper; `deployment_service/vm_prefix_registry.py` is the existing
  VM_PREFIX_TO_BUCKET registry to extend; `deployment_service/data_pipeline_monitors/launcher_registry.py` is the
  closest existing pattern for a new shard-plan-manager module. deployment-api: mirror
  `routes/vm_resource_history.py` + `services/operational_data_queries.py` (typed route, `_validate_identifier`-guarded
  SQL builder, `run_query()` via UTL analytics client, degrade-to-empty never-5xx). deployment-ui: new page flat under
  `src/pages/` (mirror `VmResourceComparison.tsx`, local-state fetch, no React Query, `recharts`), route in `App.tsx`,
  nav entry in `NavMenu.tsx`, Playwright spec under `tests/e2e/`. Execution order chosen: UAC contract → UTL resolver →
  shared `--shard-spec` flag → per-service consumption (parallel sub-agents, one per service, never same file) →
  launchers → global manager + UI → `run_shard_loop` → streaming readers (execution first, it's furthest behind) →
  intra-shard audit/QG → monitors → codex doc.
