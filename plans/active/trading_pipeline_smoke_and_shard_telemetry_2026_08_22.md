---
doc_type: plan
title: Trading-pipeline smoke suite MTDS→ML + standardised per-shard resource/cost telemetry — the delta to an optimised setup
summary: >-
  Operator-owned human plan (2026-08-22 session) for the end-to-end smoke suite from MTDS through MDPS, features, ML and
  strategy, built on the existing data-pipeline-check skills after a per-AG audit — with one standardised, contract-backed
  per-shard telemetry record (stage timings, inbound/outbound I/O, throughput, RAM, CPU, GCS ops, $) emitted by every VM,
  Cloud Run job and smoke run, landing where the deployment UI already reads resource samples, plus the
  expected-vs-actual cost model that projects capacity and spend per shard-day across N years. Carries the read-path
  (manifest-derived read set, per-cell index, hive-pruned scans, engine per feature family), MTDS→MDPS/features/ML
  hardening parity abstracted into UAC/UTL, honest coverage for MDPS + feature groups, a QG-bounded feature registry,
  MDPS per-data_type rules, look-ahead/pre-flight/gap-recording hardening, the ML sizing run that decides GPU vs CPU,
  and the two new skills /trading-pipeline-check-ml and /trading-pipeline-check-strategy.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, features, strategy, meta]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    ml-service,
    strategy-service,
    instruments-service,
    deployment-api,
    deployment-service,
    deployment-ui,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    smoke-test,
    benchmark,
    resource-telemetry,
    cost,
    capacity,
    manifest,
    honest-coverage,
    look-ahead,
    feature-registry,
    data-engine-selection,
    ml,
    skills,
    observability,
  ]
related:
  [
    /plans/active/data_pipeline_completion_2026_08_21.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md,
    /plans/active/venue_smoke_test_bar_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/bigquery_feature_ml_compute_engine_option_2026_06_08.md,
    /plans/epics/system_readiness_master.md,
    /plans/epics/observability_master.md,
    /plans/epics/features_and_ml_master.md,
  ]
created: 2026-08-22
last_updated: 2026-08-22
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P1
milestone: M3
estimate_class: infra
estimate_baseline_ai_days: 40
estimate_calibrated_ai_days: 32
assigned_role: data_engineering
effort: max
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  [
    operator interactive session 2026-08-22 (slot 6) — "lets make a human plan ... smoke test everything from MTDS to
    ML ... resource usage and time taken per shard clearly recorded ... detailed performance and cost expectation
    analytics are essential ... should be standardised",
  ]
context_scope:
  [
    /codex/06-coding-standards/data-engine-selection.md,
    /codex/06-coding-standards/read-time-filter-pushdown.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/shard-coverage-classification.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/04-architecture/ml-experiment-lifecycle.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    unified-trading-library/unified_trading_library/pipeline_e2e_check/,
    unified-trading-library/unified_trading_library/manifest_writer/_read_index.py,
    unified-trading-library/unified_trading_library/point_in_time.py,
    unified-trading-library/unified_trading_library/deployment_registry.py,
    unified-api-contracts/unified_api_contracts/registry/processed_data_dependencies.py,
    unified-api-contracts/unified_api_contracts/canonical/domain/features/registry.py,
    unified-api-contracts/unified_api_contracts/internal/cloud_run_job_registry.py,
    features-service/features_service/delta_one/app/core/data_loader.py,
    features-service/features_service/cross_instrument/engine/raw_data_loader.py,
    features-service/features_service/multi_timeframe/engine/orchestrator.py,
    deployment-api/deployment_api/services/operational_data_queries.py,
    deployment-service/scripts/setup-pubsub.sh,
  ]
---

# Trading-pipeline smoke suite MTDS→ML + standardised per-shard resource/cost telemetry

> **Human plan** (`assigned_vm: NA`, operator ruling 2026-08-22) — operator-driven, never ingested. It is the **delta
> register** between today's measured state (§0) and the optimised setup (§2) for cost / speed / stability /
> observability, and the place every smoke-test + telemetry decision is ruled (§1). Work that already has an owner is
> **linked, not duplicated**: the BATCH/PAPER/LIVE gate register is
> [`data_pipeline_completion_2026_08_21.md`](/plans/active/data_pipeline_completion_2026_08_21.md); the shipped
> three-stage (fetch/process/write) benchmark harness (`run_three_stage_benchmark()` +
> `scripts/three_stage_benchmark.py`) is batch15 items 4-6 in
> [`cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md`](/plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md);
> the per-venue batch smoke bar is [`venue_smoke_test_bar_2026_08_16.md`](/plans/active/venue_smoke_test_bar_2026_08_16.md).
> This plan adds what none of them own: **one telemetry contract for every compute unit**, the **cost-expectation
> model**, the **ML + strategy check skills**, and the **read-path / hardening / gap-recording** delta.

## 0. Measured starting point (2026-08-22, this session) — the facts the delta is built on

| Area                         | Measured fact                                                                                                                                                                                                                                                           |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Hive layout                  | Path convention only. Every features/ML read = `blob_exists` → `download_bytes` → `pl.read_parquet(BytesIO)` → `pl.concat`; zero `scan_parquet(hive_partitioning=…)`, zero DuckDB, column projection in one site (`cefi_wire_bridge.py`)                                |
| `blob_exists` probes (src)   | MTDS 67 · MDPS 11 · features 34 · ML 3. Rationale in `delta_one/app/core/data_loader.py`: a storage 404 goes through `@handle_storage_errors(RETRY)` and collapses to `None` — the probe is an error-handler dodge, not a data need                                    |
| Manifest read                | One `_index/availability_index.parquet` per bucket (~6.5 GB decompressed sports, ~33M rows DeFi); slim (column-pruned) + filtered read path and a >7200 s staleness fallback exist (`_read_index.py`); no per-cell index                                                 |
| MTF re-download              | `multi_timeframe/engine/orchestrator.py` downloads the whole consolidated `data.parquet` per (instrument, group, timeframe) then filters to one `instrument_id` — N instruments × T timeframes re-downloads per day                                                     |
| Hardening parity (src refs)  | `classify_venue_error` MTDS 251 / MDPS 7 / features 11 / ML 0 · `honest_absence` 283 / 15 / 14 / 0 · `PerLeafFailure` 48 / 0 / 0 / 0 · `read_captured_days` 8 / 10 / 0 / 0 · `check_shard_freshness` 35 / 45 / 9 / 0                                                    |
| Look-ahead parity            | `available_at` MTDS 878 / MDPS 292 / features 331 / ML 2 / strategy 40 · PIT primitives (`validate_pit_safety` etc.) 2 / 6 / 121 / 0 / 6                                                                                                                                  |
| Telemetry pipe (exists)      | VM heartbeat → `host_metrics_window` (`cpu_pct/mem_pct/disk_pct/mem_slope/io_write…/net_recv…`) in `deployment_registry.py` → Pub/Sub `resource-samples` → BigQuery `deployment_operational_data.resource_samples` → deployment-api `resource_samples_rolling_sql` → UI |
| Telemetry gaps               | Nothing per **shard** (stage timings, bytes, objects, GCS ops, rows, $); Cloud Run jobs emit no samples; `pipeline_e2e_check/report.py` records `duration_sec` only — no RSS, bytes, ops or cost column anywhere                                                        |
| Benchmark leg                | Exists for IS/MTDS/MDPS/features (own driver VM, one steady-state VM per cell). Every features `benchmark` row so far is either `objects=0` (TRADFI:volatility ×3) or boot-dominated at 7 days; `multi_timeframe`/`cross_instrument` never benchmarked                  |
| Skills                       | `data-pipeline-check-{is,mtds,mdps,features}` live in `cursor-configs/skills/` (slot symlink `.claude/skills`); **no ML or strategy check exists** (`ml-service/scripts/` has no `pipeline_e2e_check.py`)                                                                 |
| Runtimes / billing           | Batch = Cloud Run Job per family (4 vCPU / 16 GiB / 24 h cap, cron 12:00 UTC); backfill/benchmark = SPOT VM (`launch-features-vm.sh` `e2-standard-8`); live = 12 long-lived VMs on Redis Streams; Memorystore/ElastiCache terraformed, `enable_*=false` by default      |
| ML                           | Training on VMs (`launch-ml-vm.sh`: `n2-highmem-8` default, T4 option); JSON `ModelRegistry`; promotion human-gated; Vertex never used. delta_one = **1,389 specs** in `registry_specs.yaml`, declared at `timeframes: [5m, 15m, 1h, 4h, 24h]` — no 1m pass exists   |
| GCS cost split               | ~48 % object operations / ~30 % stored bytes (`cloud-spend-forecast-and-credits-2026-08.md`) — read-path op count is a first-order cost lever, not only latency                                                                                                          |
| Manifest read BYTES          | `_read_index.py` downloads the WHOLE consolidated blob (`client.download_bytes(bucket, _INDEX_PATH)`) on every uncached read; `filters=` only prunes row groups at DECODE (the consolidator sorts `ORDER BY date, venue, data_type`); `columns=` alone bounds nothing on a large index  |
| Bare index reads (grep est.) | Call sites with neither `columns=` nor `filters=` / total: IS 30/56 · MTDS 29/94 · MDPS 1/6 · features 10/24 · ML 0/2 · strategy 1/2 — `read_availability_index_safe` only WARNS on a bare call                                                                                         |
| Manifest WRITES              | Per-VM shard `_index/per_vm/{instance}.parquet`: every flush = read own shard → merge pending → generation-matched REWRITE (CAS, 200 MiB merge budget); consolidator dedups by key (last write wins). VM-specific, yes — but read-modify-write of one growing file, not append         |
| VM boot                      | Stock `ubuntu-2404-lts` image + `setup-data-pipeline-vm.sh` (`apt-get` + `uv pip install`, GCS wheel cache) on EVERY boot — no baked image; the e2e engine launches ONE VM per (shard, leg) via `launch_vm_and_wait`                                                                  |

## 1. Decision ledger (ruled in the 2026-08-22 session; T7 ratifies)

- **D1 — No full manifest read on the hot path; partitioning is the point.** Read set = per-cell index (T3) → column-projected
  hive-pruned scan; `blob_exists` is removed; `captured ⇒ object exists` is the contract, 404 = honest absence.
- **D2 — Engine per feature family, same `formula_version` regardless of engine** (extends
  `/codex/06-coding-standards/data-engine-selection.md`): `delta_one` + `multi_timeframe` → in-process polars scan;
  `cross_instrument` + `volatility` → DuckDB in-process (joins), BigQuery when the underlying × venues × lookback stops
  fitting one VM; ML matrix assembly → BigQuery external tables (or DuckDB on a highmem VM). BQ/DuckDB are executors,
  never a second SSOT; one Arrow hop at the boundary is not the banned polars↔pandas round-trip (codex ruling in T3).
- **D3 — One telemetry contract for every compute unit** (VM, Cloud Run job, smoke driver, live worker): UAC
  `ShardRunTelemetry`, emitted via the existing `resource-samples` pipe, landing in BigQuery next to `resource_samples`,
  surfaced in the deployment UI with **expected vs actual**. Standardised, not per-service.
- **D4 — Cost expectation = measured $/shard-day × expected shard-days** (honest-coverage denominator, clipped by
  `SOURCE_COVERAGE_START`/launch/genesis, with a common-start-date override) → per service/AG/mode, N years.
- **D5 — Hardening is abstracted, not copied**: taxonomies + contracts in UAC, mechanics in UTL, services keep adapters
  only. `classify_venue_error` stays the venue branch of a new compute-stage `classify_pipeline_error`.
- **D6 — Manifest records produced-with-gaps**; downstream decides via a `GapPolicy`, the manifest never forces action.
  `missing_upstream` ≠ `insufficient_history` ≠ `produced_with_gaps` must be distinguishable on the row.
- **D7 — Skill names**: existing four keep `data-pipeline-check-*`; new ones are `/trading-pipeline-check-ml` and
  `/trading-pipeline-check-strategy <slot_label>` (`StrategySlot.slot_label` = `ARCHETYPE@venue-...-env`).
- **D8 — ML placement (recommendation pending ratification)**: SPOT VM for training, Cloud Run Job for batch inference,
  per-AG live VM for live inference; Vertex not adopted (same SKUs + margin, no AWS twin, duplicates `ModelRegistry` +
  `experiment_tracker`); GPU only on the T6 sizing evidence.
- **D9 — Every benchmark number quotes its denominator and window**; a 7-day force-leg duration is never a rate.

- **D10 — Shard-scoped manifest I/O (audit 2026-08-22).** A service knows its shard set at startup; it reads ONLY those
  cells' BYTES (cell-partitioned index, T3), never the whole blob; a bare `read_availability_index` call is a QG
  violation ratcheted to zero. Writes stay per-VM-shard but become append-only parts compacted by the consolidator — no
  read-modify-write of a growing file.
- **D11 — Smoke matrix on warm workers, never one VM per shard.** One long-lived worker VM per (service × asset_group)
  iterates its shard list: skip leg = manifest-only decision (no download), force leg = the one download + compute
  into an empty `-test-` cell. Boot is paid per worker, not per shard, and cut further by a baked image. All smoke
  runs are VMs (T8 child plan).
- **D12 — Memory before machine size; 64 GB is the ceiling.** Resize only after per-shard cleanup, single-engine,
  cell-scoped manifest reads and read-once caches are proven in telemetry; a shard that still needs > 64 GB
  (`*-highmem-8`) is a defect to file, never a bigger machine.

- **D13 — Deterministic config-shard id (ruled 2026-08-22).** `<human components>__cfg<v>__<semver>__<hash8>` —
  strategy `<client_id>__<slot_label>…`, ML `<model_family>__<period>__<universe>…`, execution adds `<region>`; the
  service checks the manifest for that id and SKIPS unless `--force`, which dumps regardless as `run_attempt+1`.
  Force / freshness-check / skip-if-fresh exist for ALL services. Supersedes the v7 "new job_id per re-run" rule; job
  ids are shared across strategy / ML / execution. Child: `trading_pipeline_config_shard_identity_and_latency_profile`.
- **D14 — Bare manifest reads are banned from day one.** Migrate EVERY bare `read_availability_index` site to
  cell / cell-group reads first, then the QG check hard-fails any bare read (baseline 0 — no ratchet).
- **D15 — Worker unit** = (service × asset_group × data_type × instrument_type), × model_family for ML / strategy /
  execution where many configs are optimised — ~120-200 warm VMs, not 1-2k. dp-heartbeat / exit-code / Cloud Run
  monitors and alert routing must acknowledge a vertically-scaled multi-shard VM (progress = checkpoint growth).
- **D16 — Consolidators.** PROD consolidators' liveness is asserted pre-run (a lagging cycle does not block); `-test-`
  buckets get NO scheduled consolidator — the controller triggers the prod-identical job `--once` per test bucket
  after the run (optionally between layers): zero config drift, no wasted runs at a ~monthly per-shard cadence. A central metadata-only staleness sentinel per (service, AG) publishes consolidated-age vs newest per-VM shard; worker pre-flight consumes that verdict (never recomputes) and fails loud into the DP alerts; a deadman pages when a consolidator stops running.
- **D17 — Latency.** Exchange→local delta where the source carries it (Tardis), 200 ms total fallback, always
  widenable; `LatencyProfile` (per-region / per-venue offsets + multiplier) on the config shard, hash in `RunManifest`;
  execution region is a config axis; sent/received derived at runtime, never stored on batch rows.
- **D18 — ShardPlan owner** = deployment-service control plane + UAC contract + UTL resolver; shapes and workers
  inferred from telemetry, launchers stop hard-coding; shard-loop = spawn-context processes (intra-shard subprocesses always permitted, audited + QG-hardened to stream/flush when memory-intensive), readers stream where a
  shard exceeds the ladder. Instrument spec deltas → `instruments_master` child; IS gets its own layer-0 honest
  coverage and the rollup shows IS and MTDS separately.

- **D19 — Event-driven consolidation (ruled 2026-08-22).** Consolidators fire off per-VM shard writes (GCS
  `OBJECT_FINALIZE` on `_index/per_vm/` → Pub/Sub → debounce dispatcher), floor-throttled to 15-min UTC boundaries
  fleet-wide — no writes → no run; a mid-run trigger queues exactly one follow-up. Wall-clock staleness budgets retire
  for trigger-aware staleness (newest per-VM write newer than consolidated AND no run within debounce + grace). Every
  AG's worst-case merge must fit the 15-min window; the merge home (long-lived min-instances Cloud Run service with
  warm DuckDB + spill volume vs the existing job) is decided by a per-AG worst-case benchmark with DEFI/CEFI rows
  modelled at ~2× (measure the already-tagged share first). Child: `event_driven_manifest_consolidation_2026_08_22`.

## 2. Target architecture — the optimised setup

- **Read path**: per-cell index → read set → hive-pruned projected scan (engine per D2) → single-engine compute → write +
  manifest row with gap columns (D6) → telemetry row (D3). No probes, no full-index loads, no N× re-downloads.
- **Runtime per mode** (unchanged shape, now sized by data): daily = Cloud Run Job if p95 shard-day fits 24 h at ≤8 vCPU;
  backfill/benchmark = SPOT VM sized from measured peak RSS + CPU; live = long-lived per-AG VMs on Redis Streams.
- **Observability**: one `ShardRunTelemetry` row per (shard, leg/run) with stage split (list / fetch / process / write —
  the batch15 harness stage names), rows/bytes/objects in+out, GCS Class A/B ops, peak RSS, CPU avg/p95, wall clock,
  machine type + pricing class, `usd_estimate`, expected twins + variance; queryable per shard atom in the deployment UI.
- **Correctness**: PIT enforcement at every consumer boundary; pre-flight classifies RUNNABLE / INSUFFICIENT_HISTORY /
  HONEST_EMPTY / RUNNABLE_WITH_GAPS before compute; honest coverage exists for MDPS and feature groups, not just MTDS.

## 3. ML sizing prior (BTC, 6 y, 1 m target, LightGBM) — a prior to be REPLACED by T6's measured run

Rows 6 × 365 × 1440 ≈ **3.15 M** at 1 m (≈ 630 k at 5 m). Columns: 1,389 delta_one specs at one timeframe; ≈ 6,900 if
all five declared timeframes are joined as columns. Float32 matrix ≈ 17.5 GB (1,389 cols @ 1 m) / ≈ 87 GB (6,900 cols @
1 m — does not fit `n2-highmem-8`, fits `n2-highmem-16` only after binning); LightGBM binning ≈ 1 byte/cell → 4.4 / 22 GB.
CPU histogram build on 8 cores ≈ 1.5-3 × 10⁸ cells/s → 1,389 cols ≈ 15-30 s/iteration → **light model (300 iters) ≈
1.2-2.5 h**; the 2-10 % slice (28-139 cols) at 1,000-3,000 iterations ≈ **0.5-1.5 h**; walk-forward folds multiply both.
T4 GPU (LightGBM CUDA / XGBoost `gpu_hist`) ≈ 3-8× on these shapes at ≈ 2× node cost → GPU pays once the light pass
exceeds ~1 h per run or folds × trials are large. **Matrix assembly dominates today**: 2,190 days × groups × timeframes
of per-blob downloads ≈ 4 × 10⁴-2 × 10⁵ objects ≈ 1-6 h serialized vs minutes via a pruned BQ/DuckDB read — fix I/O (T3)
before buying GPU. Caveat: no 1 m delta_one pass exists (§0), so a 1 m target implies a ×5-row feature pass or a 5 m
target (T6 decision).

## Tracks + todos

### T0 — Audit the four existing check skills per AG (read-only first)

- [ ] [REVIEW] P0. **Per-(skill × AG) audit table** for `data-pipeline-check-{is,mtds,mdps,features}` — verify each of
      the 4 skills × 5 AGs against codex: shard atom (`/codex/02-data/data-status-drilldown-hierarchy.md`),
      `--require-captured --auto-day`, the Phase-0 `-test-` resolved-bucket assertion, the driver-VM launch path
      (`unified_trading_library.pipeline_e2e_check.launcher`), and `benchmark` at ≥ 30 days. Done-when: a 20-row table
      appended under "T0 results" in this plan with OK / GAP + the fix-todo id per GAP.
- [ ] [REVIEW] P0. **Root-cause every historical features `benchmark` row** in
      `plans/audit/results/data_pipeline_e2e_check_features_*.md` (`objects=0` on TRADFI:volatility ×3; 7-day
      boot-dominated windows; `_FAMILY_TIMEOUT_OVERRIDES` hand values) and file one T2 fix todo per class. Done-when:
      each row carries a root-cause label in the T0 results table.
- [ ] [DATA] P1. **3-checkpoint cadence for the 10 multi-instrument/multi-timeframe cells** — `multi_timeframe` ×
      {CEFI, DEFI, TRADFI}, `cross_instrument` × {CEFI, TRADFI, PREDICTION}, `delta_one` × 4 as the baseline input — at
      `--benchmark-days 30`, after T2's telemetry columns land. Done-when: 10 cited report paths, zero `objects=0` rows.
- [ ] [DATA] P1. **Same cadence for IS / MTDS / MDPS per AG** via their skills. Done-when: 15 cited report paths
      (3 skills × 5 AGs), each with the T1 telemetry columns populated.

### T0 results

**Method**: read each driver's source directly (`grep`/inline read, not report-inference) —
`instruments-service/scripts/pipeline_e2e_check.py` (1268 lines), `market-tick-data-service/scripts/pipeline_e2e_check.py`
(3735 lines), `market-data-processing-service/scripts/pipeline_e2e_check.py` (2489 lines),
`features-service/scripts/pipeline_e2e_check.py` (2462 lines) — cross-checked against each SKILL.md's own documented
"Known gap"/"Canonical-oracle audit" sections (several of these criteria were already found and written up by prior
sessions; this pass re-verified them live against current code rather than trusting the doc) and every dated report
under `plans/audit/results/data_pipeline_e2e_check_{is,mtds,mdps,features}_*.md`. All four drivers import and call
`unified_trading_library.pipeline_e2e_check.launcher.launch_vm_and_wait` (criterion 4) with no bespoke/legacy launch
path found in any driver — that column is OK uniformly across all 20 rows and is folded into the Verdict column instead
of repeated 20×. Criteria 1-3 are materially AG-agnostic in code (one code path handles all 5 asset_groups per
service) except where a per-AG note says otherwise; criterion 5 (benchmark evidence) is genuinely per-AG/per-service
and is NOT uniform.

| Skill | Asset Group | Shard atom OK? | `--require-captured --auto-day`? | Phase-0 `-test-` bucket guard? | Shared launcher? | `benchmark` ≥30d evidence | Verdict |
|---|---|---|---|---|---|---|---|
| data-pipeline-check-is | CEFI | OK — `(asset_group, venue, day)` matches codex `instruments-service: venue → date` | **GAP** — no such flags exist in argparse at all (live-confirmed 2026-08-14: `unrecognized arguments`) | OK — `--test-run` hardcoded in the launcher argv the driver itself builds (not caller-supplied); `_force_consolidate_test_buckets` refuses non-`-test-` buckets | YES | **N/A — no `benchmark` leg exists in this driver** (no `--benchmark-days` flag, `--legs` valid set is force/skip/live only) | GAP: fix-todo = ship `--require-captured`/`--auto-day` parity (tracked, unshipped, `tradfi_consolidated_closeout_2026_07_18.md` Phase D) + add a benchmark leg or explicitly declare IS out-of-scope for throughput (reference data is largely day-insensitive) |
| data-pipeline-check-is | DEFI | OK — driver's `_shard_target_filters` emits `{asset_group, venue: protocol, chain}` for DeFi cells, matching codex's `venue → chain → date` | GAP (same, code is AG-agnostic — the flags don't exist for any AG) | OK (same driver-wide guard) | YES | N/A (same — no benchmark leg) | GAP: same two fix-todos as CEFI |
| data-pipeline-check-is | TRADFI | OK — `(venue, day)` only, 7 venues, no `data_type` axis; matches codex `venue → date` (tradfi) | GAP (skill's own "Known gap" section names this explicitly, with the Phase D follow-up as the tracked fix) | OK (same) | YES | N/A | GAP: same two fix-todos |
| data-pipeline-check-is | SPORTS | **GAP (codex-side)** — driver's real shard atom is `(sports_provider, day)`; codex `data-status-drilldown-hierarchy.md` has NO instruments-service-sports row at all (only an MTDS-sports row: `data_type → league_id → date`) — nothing to verify IS's sports shape against | GAP (same) | OK (same) | YES | N/A | GAP: (a) fix-todo = add an IS-sports row to the codex hierarchy doc; (b) same require-captured/benchmark gaps as above |
| data-pipeline-check-is | PREDICTION | OK — comment confirms "non-prediction behavior is byte-unchanged"; CQG cluster collapse is the prediction-specific wrinkle, same `(asset_group, venue, day)` shape otherwise | GAP (same) | OK (same) | YES | N/A | GAP: same require-captured/benchmark gaps |
| data-pipeline-check-mtds | CEFI | OK — 6-tuple `(asset_group, venue, data_type, day)` + one sampled instrument/root matches codex `MTDS CeFi spot/perp` and `options/futures` (bundled-by-root) rows; the single-sample-per-cell scope is a documented, deliberate smoke-check coarsening, not a mismatch | OK — confirmed present in argparse (`--require-captured` / `--auto-day`, lines ~3467-3474) and the skill mandates always passing both | OK-with-a-hole — force/skip legs hardcode `--test-run`; BUT the code ALSO registers an explicit prod-write escape hatch, `--allow-live-prod-writes` (skill cites `pipeline_e2e_check.py:2561,2642,1983`), which is prohibited **only by skill-doc convention** — nothing in the Python code refuses the flag or asserts against it | YES | **N/A — no `benchmark` leg exists in this driver either** (grep for `benchmark`/`--benchmark-days` in the 3735-line file returns zero hits) | GAP: (a) `--allow-live-prod-writes` has no code-level guard/confirmation — a fix-todo to add one; (b) no benchmark leg — throughput here is explicitly documented as needing a real sharded backfill VM + RX-counter instead (skill's own "Measuring throughput" section), so T2's planned benchmark-leg hardening for MTDS has no existing leg to harden — it would be new work, not a fix |
| data-pipeline-check-mtds | DEFI | OK (same 6-tuple, codex DeFi row `venue → chain → instrument_id → data_type → date`) | OK (same, AG-agnostic flag) | OK-with-a-hole (same escape hatch) | YES | N/A (same) | GAP: same two items |
| data-pipeline-check-mtds | TRADFI | OK — the driver narrows the raw cartesian product to the real fetchable 12-cell surface (documented `_TRADFI_BILLING_GATED_DATA_TYPES` etc.), matching codex's `venue → data_type → instrument_type → root → date` (bundled) shape; the hand-listed 6-cell MVP set is explicitly NOT derived from `is_mvp()` (documented, working-as-designed) | OK (same) | OK-with-a-hole (same escape hatch) | YES | N/A (same) | GAP: same two items |
| data-pipeline-check-mtds | SPORTS | OK — league_id is enumerated as its own axis (not collapsed), matching codex `data_type → league_id → date` | OK (same) | OK-with-a-hole (same escape hatch) | YES | N/A (same) | GAP: same two items |
| data-pipeline-check-mtds | PREDICTION | OK — matches codex `venue → canonical_question_group → data_type → date` (CQG bundling documented) | OK (same) | OK-with-a-hole (same escape hatch) | YES | N/A (same) | GAP: same two items |
| data-pipeline-check-mdps | CEFI | **GAP (codex-side)** — driver shard atom `(asset_group, venue, instrument_type, data_type, timeframe, day)` is internally coherent (one VM/cell derives every valid timeframe, each verified as its own `ShardCheckResult`) but `/codex/02-data/data-status-drilldown-hierarchy.md` has **no MDPS row at all** — there is no codex SSOT to check MDPS's tree against | OK — confirmed present in argparse (lines ~2284-2290), skill mandates it always | **GAP** — driver always derives the output bucket via `_test_bucket()` → `resolve_bucket_name(deployment_env="test")` (safe by construction in the happy path), but there is **no explicit runtime assert** immediately before the force-leg's `_launch()`/`launch_vm_and_wait` call that refuses a non-`-test-` result; the only in-code `"-test-" not in bucket` check lives in the UNRELATED `_force_consolidate_test_buckets` Phase-0 step, not on the write path. The skill's own §2a documents this precise gap as living in the launcher shell script (`launch-mdps-backfill-vm.sh`, fail-open on `--output-bucket`) and requires a **bash-level** guard the skill author must remember to run — nothing inside `pipeline_e2e_check.py` self-defends | YES | **GAP** — `_DEFAULT_BENCHMARK_DAYS = 7` (never raised to 30, unlike features); grepping every MDPS report file (`data_pipeline_e2e_check_mdps_*.md`) for a `\| benchmark \|` row returns **zero matches** — the benchmark leg has apparently never actually been run/reported for MDPS, at any window length, for any asset_group | GAP: (a) add an MDPS row to the codex drilldown-hierarchy doc; (b) add an in-driver pre-write bucket assert (mirror the `_force_consolidate_test_buckets` pattern onto the actual launch call); (c) raise `_DEFAULT_BENCHMARK_DAYS` to 30 and actually run+report a benchmark leg at least once per AG |
| data-pipeline-check-mdps | DEFI | GAP (same — no codex row) | OK (same) | GAP (same) | YES | GAP (same — zero benchmark rows in the whole MDPS report corpus, not AG-specific) | GAP: same three items |
| data-pipeline-check-mdps | TRADFI | GAP (same) | OK (same) | GAP (same) | YES | GAP (same) | GAP: same three items |
| data-pipeline-check-mdps | SPORTS | GAP (same — codex has no MDPS row; separately, MDPS's own MVP-universe helper `mdps_mvp_universe` RAISES for sports/prediction by design, so this AG enumerates from a different code path — documented, not a bug) | OK (same) | GAP (same) | YES | GAP (same) | GAP: same three items |
| data-pipeline-check-mdps | PREDICTION | GAP (same, same sports/prediction MVP-universe caveat) | OK (same) | GAP (same) | YES | GAP (same) | GAP: same three items |
| data-pipeline-check-features | CEFI | OK — `(asset_group, feature_family)` + day/lookback-window matches codex's `feature_family` outer axis; `feature_group` is explicitly documented as a reporting dimension only, so this driver checks a valid **ancestor** node of the codex leaf tree, not the leaf itself (coarser grain, consistent with the codex doc's own "aggregate counts at every non-leaf node reflect the full subtree" design — not a mismatch, but T1's planned per-shard telemetry will need to drop to the leaf) | OK — confirmed present in argparse (lines ~2325-2332), and additionally checks the WHOLE lookback window, not just the target day | **GAP** — same class as MDPS: `_test_bucket()` always calls `resolve_bucket_name(deployment_env="test")` (or, for the `commodity` flat-kind fallback, an explicit `"-test-" in base else base.replace(...)` construction that is itself safe-by-construction) but there is no runtime assert immediately before the force-leg's launch call; skill's own §2a names `launch-features-vm.sh` as fail-open on `--sink-bucket` and requires a bash-level pre-launch guard the skill must remember to run, not something the Python driver enforces itself | YES | **GAP** — code default is now `_DEFAULT_BENCHMARK_DAYS = 30` (D9-compliant), but grepping the window-day token across **every** dated features report returns "7 (7d)" for **100% of historical benchmark rows** — no `--benchmark-days ≥ 30` run has ever actually been executed/reported for ANY asset_group, despite the default already being right | GAP: (a) add the same in-driver pre-write bucket assert as MDPS; (b) actually run and cite a `--benchmark-days 30` report per AG (T0's own third todo); (c) see Root-cause labels below for the `objects=0` bug specific to this cell |
| data-pipeline-check-features | DEFI | OK (same ancestor-node caveat; `onchain` family is DEFI-only per the viability matrix) | OK (same) | GAP (same) | YES | GAP (same — zero ≥30d rows anywhere in the corpus) | GAP: same items (a)-(b) |
| data-pipeline-check-features | TRADFI | OK (same; `commodity`+`volatility` families are TRADFI-scoped) | OK (same) | GAP (same) | YES | **GAP, confirmed live** — the only asset_group whose `benchmark` leg actually appears in the report corpus (`TRADFI:volatility`, 2026-08-04/07/14) is TRADFI, and all 3 occurrences show the `objects=0` fabricated-rate bug (see Root-cause labels) | GAP: same (a)-(b) plus the confirmed-live bug in (c) |
| data-pipeline-check-features | SPORTS | OK (same; `sports` is the only viable family for this AG, per the viability matrix — 1 cell, not several) | OK (same) | GAP (same) | YES | GAP (same — zero ≥30d rows) | GAP: same (a)-(b) |
| data-pipeline-check-features | PREDICTION | OK (same; `delta_one`+`cross_instrument` are the viable families) | OK (same) | GAP (same) | YES | GAP (same) | GAP: same (a)-(b) |

**Tally**: 20/20 rows share the shared-launcher OK (criterion 4, folded into Verdict). Of the remaining 4 scored criteria
× 20 rows = 80 cells: shard atom **15 OK / 5 GAP** (all 5 GAPs are codex-doc gaps — IS-sports has no codex row, MDPS has
no codex row at all — never a driver-code defect); `--require-captured --auto-day` **10 OK (MTDS+MDPS+features, all
AGs) / 10 GAP (IS, all AGs — flags don't exist)**; Phase-0 bucket guard **10 OK-ish (IS+MTDS, though MTDS carries an
undefended escape hatch) / 10 GAP (MDPS+features, no in-driver pre-write assert)**; benchmark ≥30d evidence **0 OK / 20
GAP** (IS+MTDS have no benchmark leg at all — 10 rows N/A-as-GAP; MDPS has never run one — 5 rows GAP; features has the
right default but zero actual ≥30d runs and a confirmed live bug on the one AG that has been run — 5 rows GAP).
**0 of 20 rows are a clean, no-caveat OK across all 4 scored criteria.**

**Root-cause labels** (T0's second todo):

- **features `objects=0` fabricated-rate bug (TRADFI:volatility ×3, 2026-08-04/07/14 reports)** — **CONFIRMED STILL
  PRESENT** in current code. `features-service/scripts/pipeline_e2e_check.py::_run_benchmark_leg` (current lines
  1976-2029, bug specifically at 2005-2006) computes `passed = vm_result.exit_status == 0 and write_verified` (correct)
  but then unconditionally computes `per_day = duration_sec / max(1, benchmark_days)` and folds it plus
  `objects={parquet_count}` into the human-readable `reason` string regardless of `passed` — so a run that never
  completed still prints a plausible-looking "~25s/shard-day" rate next to `objects=0`. The `status` column correctly
  says `failed`, so a machine reader is safe; a human/LLM skimming the `reason` text is not. **Partial mitigation
  shipped 2026-08-15** (`vm_reason_prefix = "vm_not_success:<reason> "` prepended when `exit_status != 0`) postdates
  all 3 historical reports above (hence none of them show the prefix) and would label a NEW failing run — but does not
  stop the fabricated rate from being computed and printed. **Not yet fixed at the root** (T2's planned "fail loud on
  `objects=0`, never report a rate" hardening is still open work, not done). **Same bug class confirmed present in
  MDPS** (`market-data-processing-service/scripts/pipeline_e2e_check.py::_run_one_benchmark`, lines 2071-2102):
  `rows_per_sec`/`sec_per_shard_day` are likewise computed unconditionally and folded into `reason` with the same
  `vm_not_success:` prefix pattern on failure — never yet triggered in a real report only because MDPS's benchmark leg
  has never been run/reported at all (see table above). **IS and MTDS cannot exhibit this bug** — neither has a
  benchmark leg in the first place (N/A, not a clean pass).
- **7-day boot-dominated windows** — MDPS's `_DEFAULT_BENCHMARK_DAYS = 7` was never raised to 30 (features' was, per
  D9). Separately and more strikingly: even though features' own default is now 30, grepping the day-token across every
  dated features report shows **100% of historical benchmark rows used a 7-day window** — the 30-day default exists in
  code but nothing has ever enforced it actually being used for a real "planning number" run. Root cause: the skill doc
  instructs `--benchmark-days 30` but nothing (CI, the driver, or the skill invocation habit) enforces it — a
  documentation-only rule, unexercised in the observed report history. **Same absence-of-enforcement class applies to
  MDPS** (7 is still the code default, so even a compliant invocation with no override would under-run); **N/A for
  IS/MTDS** (no benchmark leg to have a window length at all).
- **`_FAMILY_TIMEOUT_OVERRIDES` provenance** — **NOT a bug; the plan's framing overstated this.** Every entry in both
  dicts carries an inline code comment citing a specific measured VM run (name/date/wall-clock) and an explicit safety
  margin: features' 4 entries (`volatility/TRADFI`=7200, `delta_one/CEFI`=108000 — raised from 72000 after a real
  61793s/10-of-18-groups partial completion, `delta_one/PREDICTION`=36000, `sports/SPORTS`=10800, ~48% margin over a
  measured 7320s/30d prediction) and MDPS's 1 entry (`SPORTS/odds_horizon_bucket`=3600, two independent from-scratch
  runs at 2208s/1908s cited, ~65% margin). **Root-cause label: NOT-A-BUG / already-provenanced** — no fix-todo needed
  here; this item can be dropped from any future audit of "undocumented" values.

### T1 — Standardised resource / performance / cost telemetry (the pillar)

- [ ] [DESIGN] P0. **UAC `ShardRunTelemetry` contract** — new `unified_api_contracts.internal.shard_run_telemetry`:
      deployment target (VM name or `cloud_run_job_registry` stem), service, mode (batch/paper/live), shard atom
      (asset_group, venue, instrument_type, data_type | feature_group + feature_group_version, timeframe, day),
      machine_type + pricing_class, stage timings (list/fetch/process/write — batch15 harness names), rows_in/out,
      bytes_in/out, objects_read/written, gcs_ops_class_a/b, peak_rss_bytes, cpu_pct_avg/p95, wall_clock_sec,
      usd_estimate, `expected_*` twins + variance. Done-when: model + guard test shipped, `unified-api-contracts@<sha>`.
- [ ] [BACKEND] P0. **UTL `ShardTelemetryRecorder`** (context manager, `unified_trading_library/monitors/`) — times
      stages, samples RSS/CPU (psutil), counts GCS ops by instrumenting the UCI storage client
      (`cloud_interface/protocol.py` `download_bytes` / `list_blobs` / upload), computes `usd_estimate` from the price
      table, publishes to the existing `resource-samples` Pub/Sub topic (`deployment-service/scripts/setup-pubsub.sh`)
      as a new message kind. Done-when: unit test + one real VM run shows rows in BigQuery.
- [ ] [DATA] P0. **Compute price-table SSOT** `unified_api_contracts.internal.compute_price_table` — dated GCP machine
      types (on-demand + spot $/h), Cloud Run Job $/vCPU-s + $/GiB-s, GCS Class A/B ops + storage $/GB-month, AWS
      Fargate/EC2-spot equivalents, `price_table_version`. Done-when: module + a QG check that every
      `deployment-service/scripts/vm/launch-*.sh` `MACHINE_TYPE` resolves in the table.
- [ ] [INFRA] P0. **BigQuery landing** — `deployment_operational_data.shard_run_telemetry` (terraform,
      `deployment-service/terraform/gcp`), fed by the `resource-samples-bq` subscription or a sibling, day-partitioned,
      90-day retention. Done-when: terraform applied with the apply log / `cloudbuild=<id>` cited.
- [ ] [BACKEND] P0. **Cloud Run jobs emit samples too** — `ServiceBootstrap`
      (`unified_trading_library/service_framework/bootstrap.py`) starts a sampler publishing `host_metrics_window`-shaped
      samples for every job in `cloud_run_job_registry.py`, so VMs and jobs are one population. Done-when: one job
      execution shows rows in `resource_samples` with `target_kind=cloud_run_job`.
- [ ] [BACKEND] P1. **deployment-api per-shard queries** — sibling of `resource_samples_rolling_sql` in
      `deployment_api/services/operational_data_queries.py`: p50/p95 per (service, shard atom, mode) for wall clock,
      peak RSS, bytes, ops, usd; expected-vs-actual variance. Done-when: route + tests green.
- [ ] [UI] P1. **deployment-ui "Shard capacity & cost" panel** beside the existing resource view — per shard-day
      p50/p95, $/shard-day, expected vs actual, sortable by variance. Done-when: `pw:L2 ✓` with the regression spec cited.
- [ ] [BACKEND] P1. **Expected-cost model** `scripts/cost/shard_cost_model.py` — Σ cells measured-p50 $/shard-day ×
      `expected_universe_count` (honest-coverage denominator; `--common-start-date` override for the operator's
      same-start assumption) → per service / AG / mode totals for N years, split compute / GCS ops / bytes; writes
      `plans/audit/results/benchmarks/shard_cost_model_<date>.md` + parquet. Done-when: first artefact committed.
- [ ] [INFRA] P1. **QG guard — every compute unit is telemetry-covered** — guard test asserting every
      `deployment-service/scripts/vm/launch-*.sh` and every `cloud_run_job_registry` stem uses `ShardTelemetryRecorder`
      or the bootstrap sampler, or sits on a dated, reasoned exemption list. Done-when: wired into `quality-gates.sh`.
- [ ] [DOC] P1. **Codex SSOT** new codex SSOT `shard-resource-telemetry` under `codex/05-infrastructure/` — contract, emitters,
      landing, price table, expected-vs-actual, how to read the UI; `deployment-observability.md` and the
      `vm-resource-rightsizing-check` skill updated to read the new table. Done-when: `check_codex_refs.sh` clean.

### T2 — Smoke suite MTDS → ML on the shared `pipeline_e2e_check` engine

- [ ] [BACKEND] P0. **`ShardCheckResult` gains telemetry** — `unified_trading_library/pipeline_e2e_check/report.py`
      records a `ShardRunTelemetry` row per (shard, leg); report markdown gains the columns; the benchmark leg prints
      $/shard-day beside s/shard-day. Done-when: a features `--legs benchmark` report shows every new column non-null.
- [ ] [BACKEND] P0. **Benchmark-leg hardening** — `_run_benchmark_leg` in `features-service/scripts/pipeline_e2e_check.py`
      and the MDPS/MTDS siblings: fail loud on `objects=0` (never report a rate), record boot time separately from
      compute, keep `--benchmark-days` 30, derive per-family timeouts from measured p95 instead of
      `_FAMILY_TIMEOUT_OVERRIDES`. Done-when: a test per T0 failure class proves it cannot recur.
- [ ] [BACKEND] P1. **`--read-engine {blob,polars-scan,duckdb,bigquery}`** on the features / MDPS / ML drivers, passed
      to the T3 loaders so one cell is benchmarked per engine. Done-when: one cell with telemetry rows under ≥ 2 engines.
- [ ] [SKILL] P0. **`/trading-pipeline-check-ml`** — new `ml-service/scripts/pipeline_e2e_check.py` on the UTL engine +
      `cursor-configs/skills/trading-pipeline-check-ml/SKILL.md`. Shard atom = (asset_group, model_family,
      universe/instrument, timeframe, training_window). Legs: `force` (train into a `-test-` registry), `skip`
      (registry freshness), `benchmark` (matrix assembly + train time per engine, CPU vs GPU), `canonical` (artefact
      path + `ModelRegistry` entry), `pit` (`validate_pit_safety` on the assembled matrix). Done-when: listed by
      `link-claude-skills.sh`, first report in `plans/audit/results/`.
- [ ] [SKILL] P0. **`/trading-pipeline-check-strategy <slot_label>`** — `strategy-service/scripts/pipeline_e2e_check.py`;
      shard = `StrategySlot.slot_label`. Legs: `features` (every `FEATURE_REQUIRED_INPUTS` group present for the slot's
      venue/day), `position` (position adapter reachable), `batch-paper` (paper(W) vs batch-rerun(W) via
      `reconcile_day`, ε = 0), `benchmark` (tick→signal latency + telemetry). Done-when: first report for one
      live-candidate slot.
- [ ] [DOC] P1. **Update the four existing SKILL.md files** with the telemetry columns, `--read-engine`, and the
      3-checkpoint cadence rule (task_template finding K); names unchanged. Done-when: `docs(skills):` commit cited.

### T3 — Read path: manifest-derived read set, per-cell index, hive-pruned scans

- [ ] [DESIGN] P0. **Per-cell light index design** — new § in `/codex/02-data/availability-manifest-and-data-status.md`:
      writer-side `_index/cells/<service>/<asset_group>/<venue>/<data_type>/<day>.parquet` (KB-sized) maintained by
      `manifest_consolidator`, a `read_cell_index()` UTL API, and the invariant `captured ⇒ object exists` so readers
      never probe. Done-when: § merged with the prefix shape and consolidator cadence ruled.
- [ ] [BACKEND] P0. **Implement the per-cell index** in `unified_trading_library/manifest_writer/` (`_writer.py` emits,
      `manifest_consolidator.py` merges) + `read_cell_index()`; telemetry compares its read cost against
      `read_availability_index(columns=…)`. Done-when: delta_one `get_available_instruments` served from the cell index
      with ≤ 1 GCS read per cell.
- [ ] [BACKEND] P0. **Remove `blob_exists` probes in features-service** — `delta_one/app/core/data_loader.py`
      (`_probe_one_day`), `cross_instrument/engine/raw_data_loader.py` (`_load_day`), `multi_timeframe/engine/orchestrator.py`,
      the onchain/sports loaders: read set from the manifest, 404 = honest absence; fix the root cause — UTL
      `@handle_storage_errors(RETRY)` collapsing a 404 to `None` — so a missing object raises `FileNotFoundError` once
      with no retry. Done-when: `rg -c 'blob_exists\(' features_service` = 0 outside tests; QG green.
- [ ] [BACKEND] P0. **MTF read-once cache** — `multi_timeframe/engine/orchestrator.py` loads each consolidated
      `data.parquet` once per (day, group, timeframe) and serves every instrument from it. Done-when: telemetry shows
      objects_read per day = groups × timeframes.
- [ ] [BACKEND] P1. **Hive-pruned, column-projected scan path** (`pl.scan_parquet(…, hive_partitioning=True)` over the
      day / feature_group / timeframe prefixes with `columns=` needed) behind `--read-engine polars-scan` in the three
      features loaders, the MDPS tick reader, and `ml_service/training/app/core/*_feature_loader.py`. Done-when:
      bytes_in per shard-day drops vs `blob` in telemetry, numbers cited.
- [ ] [BACKEND] P1. **DuckDB path for `cross_instrument` + `volatility`** (ASOF / window joins over the day prefix)
      behind `--read-engine duckdb`, one Arrow hop to polars at the boundary. Done-when: benchmarked vs polars-scan on
      one CEFI and one TRADFI cell.
- [ ] [DOC] P1. **Codex ruling — reader engine vs compute engine** — amend
      `/codex/06-coding-standards/data-engine-selection.md`: DuckDB → Arrow → polars one hop is permitted, BQ + DuckDB
      are executors, the polars↔pandas round-trip ban is unchanged, plus the per-family engine table (D2). Done-when:
      doc merged.
- [ ] [BACKEND] P2. **BigQuery executor for ML matrix assembly** — `uts_feature_external` → BQ Storage Read API →
      Arrow → training VM, `require_partition_filter` kept. Engine ownership stays with
      `/plans/active/bigquery_feature_ml_compute_engine_option_2026_06_08.md`; this todo only wires
      `--read-engine bigquery` to it. Done-when: one BTC 6 y matrix assembled via BQ with telemetry.

- [ ] [BACKEND] P0. **Migrate every bare manifest read to cell reads, then hard-ban** (D14) — rewrite all
      `read_availability_index(` / `_safe(` sites without `filters=` (IS 30, MTDS 29, MDPS 1, features 10, strategy 1
      per §0) to `read_cell_index()` / `prefetch_cells(shard_set)` on their startup shard set; THEN ship
      `check_manifest_bare_reads.py` as a hard QG failure with baseline 0 — no ratchet, no new-only carve-out.
      Done-when: grep count of bare sites = 0 in every repo and the check is wired into each `quality-gates.sh`.
- [ ] [BACKEND] P0. **Cell-partitioned index BYTES** — `manifest_consolidator.py` additionally writes the canonical index
      hive-partitioned by (asset_group, venue, data_type) with date-sorted row groups; `read_cell_index()` /
      `prefetch_cells(shard_set)` download only those partitions. Done-when: telemetry shows a features VM's manifest
      bytes_in per run equals its cells' partition size, not the blob's.
- [ ] [BACKEND] P1. **Append-only per-VM parts** — `_flush_per_vm_pending` (`manifest_writer/_writer_io.py`) writes
      `per_vm/{instance}/{seq}.parquet` parts instead of a generation-matched rewrite of one growing file; the
      consolidator compacts parts; the self-shard merge on read unions them. Done-when: flush cost is O(pending rows);
      `test_manifest_writer_per_vm.py` + a NEW adversarial concurrent-writer test green (finding V bar).

### T4 — Hardening parity MTDS → MDPS / features / ML, abstracted into UAC + UTL

- [ ] [DESIGN] P0. **Abstraction ruling — UAC vs UTL** — new codex SSOT `pipeline-hardening-primitives` under `codex/04-architecture/`:
      UAC = contracts + taxonomies (error classes, capture_status + gap classes, telemetry, feature registry); UTL =
      mechanics (shard-loop runner, manifest-derived read set, freshness, PIT enforcer, telemetry recorder); services =
      adapters only. Done-when: doc merged with §0's parity table as the baseline.
- [ ] [BACKEND] P0. **`classify_pipeline_error()` in UAC** — compute-stage taxonomy (UPSTREAM_MISSING /
      INSUFFICIENT_HISTORY / SCHEMA_MISMATCH / COMPUTE_EXCEPTION / WRITE_GATE_FAILED / RESOURCE_EXHAUSTED) with
      `classify_venue_error()` as the venue/vendor branch — MDPS / features / ML errors are not venue errors. Done-when:
      the three per-shard loops call it; unit tests per class.
- [ ] [BACKEND] P0. **UTL `run_shard_loop()`** — shard-level failure isolation (no `raise` in the loop; `PerLeafFailure`
      + `record_failed` + continue), `check_shard_freshness` read-once, telemetry recorder, T5 pre-flight hook — adopted
      by MDPS batch/live orchestrators, every features family orchestrator, ML training shards. Done-when: the §0 parity
      grep re-run shows MDPS / features / ML ≥ MTDS on `PerLeafFailure` + `honest_absence`; tests per repo.
- [ ] [DATA] P0. **Honest coverage for MDPS + feature groups** — extend `instruments-service/scripts/measure_honest_coverage.py`
      with the processed-candle atom (+ timeframe, `service_name=market-data-processing-service`) and the features atom
      (feature_group, feature_group_version, timeframe) clipped by `FEATURE_COVERAGE_START`; `/honest-coverage-dump` and
      `/readiness-state-dump` read both layers (the readiness MDPS leg is a capability proxy today). Done-when:
      coverage.json carries both layers and both skills print them.
- [ ] [BACKEND] P0. **Feature registry QG-bounded** — `check_feature_registry_parity.py`: every
      `features_service/delta_one/app/features/registry_specs.yaml` spec (and each other family's registry) ↔ UAC
      `EXPECTED_FEATURE_GROUPS_BY_SERVICE` / `FEATURE_GROUP_TO_FAMILY` / `FEATURE_REQUIRED_INPUTS` /
      `ARCHETYPE_FEATURE_GROUPS`, with `formula_version` + the `formula_hash.py` digest pinned per spec. Done-when:
      wired into features-service + UAC `quality-gates.sh`, baseline 0 drift.
- [ ] [DATA] P0. **MDPS per-data_type rules are one SSOT** — audit `unified_api_contracts/registry/processed_data_dependencies.py`
      (`MDPS_DERIVABLE_DATA_TYPES`, `_PASSTHROUGH_RAW_FOR_OHLCV`, `PROCESSED_REQUIRES_RAW`) against the MDPS dispatch:
      (a) lowest-resolution-already-candles passthrough declared per (venue, data_type), not only globally; (b) sports =
      odds only (`SportsOddsMovementAdapter` / `SportsOddsSnapshotAdapter`), every other sports data_type explicitly
      non-derivable; (c) `funding_rates` vs `derivative_ticker.funding_rate` — one canonical funding source per venue,
      the other marked derived/duplicate. Done-when: new codex SSOT `mdps-data-type-rules` under `codex/02-data/` + a guard test over
      the registry; the MDPS CLI rejects an undeclared (venue, data_type).
- [ ] [BACKEND] P1. **ML-service parity** — `ml_service` adopts `run_shard_loop`, manifest-driven feature reads,
      `classify_pipeline_error`, telemetry (today 0 / 0 / 2 on classify / honest_absence / available_at). Done-when: §0
      parity counts updated from the same grep.

### T5 — Look-ahead hardening, pre-flight, and gap recording downstream can act on

- [ ] [BACKEND] P0. **PIT enforcement at every consumer boundary** — `validate_pit_safety` / `PointInTimeEnforcer`
      (`unified_trading_library/point_in_time.py`) in MDPS candle emission (`available_at` = period_end + publish lag),
      features inputs, ML matrix assembly (`sports_feature_loader.py`, the cross-asset pipeline), strategy `on_tick`
      feature reads; a QG check forbids a candle/feature read in ml-service or strategy-service without a PIT filter.
      Done-when: the §0 parity grep shows `pit > 0` in ml-service; check wired into QG.
- [ ] [BACKEND] P0. **Pre-flight per shard run** (MDPS / features / ML) — resolve the required upstream window
      transitively (reuse the B25 transitive-closure todo in `/plans/active/data_pipeline_completion_2026_08_21.md`,
      do not duplicate), compare with the per-cell index, classify per `/codex/02-data/shard-coverage-classification.md`
      RUNNABLE / INSUFFICIENT_HISTORY / HONEST_EMPTY **plus new `RUNNABLE_WITH_GAPS`** carrying the gap list (days,
      ratio). Done-when: every shard run logs and records its pre-flight verdict before any compute.
- [ ] [DESIGN] P0. **Manifest records produced-with-gaps** — extend the manifest row (UAC schema +
      `manifest_writer/_schema.py`) with `upstream_gap_class` (none / missing_upstream / insufficient_history /
      produced_with_gaps), `upstream_gap_days`, `upstream_gap_ratio`, written by the producing service; the 4-state
      `capture_status` is untouched; downstream reads the class and decides via a UAC `GapPolicy` enum. Done-when:
      schema-v10 proposal in `/codex/02-data/availability-manifest-and-data-status.md` + a migration plan per
      `/codex/02-data/chunk-safe-manifest-migrations.md`.
- [ ] [BACKEND] P1. **Implement the gap columns end-to-end** — writers (MDPS / features / ML), consolidator projection,
      `/codex/02-data/honest-absence-downstream-handling.md` read rules, data-status drilldown shows the class.
      Done-when: one features shard with a known upstream hole shows `produced_with_gaps` in the UI.

### T6 — ML cost + structure (measured, not guessed)

- [ ] [DATA] P0. **BTC 6-year LightGBM sizing run** on a SPOT `n2-highmem-8` and a T4 node via `launch-ml-vm.sh`:
      assemble the matrix per `--read-engine` (blob / polars-scan / bigquery), light model on all delta_one features,
      then the 2-10 % slice on the big model, walk-forward folds, every step through telemetry. Done-when:
      `plans/audit/results/benchmarks/ml_btc_6y_sizing_<date>.md` with $/run and h/run per path, replacing §3's prior.
- [ ] [DESIGN] P1. **1-minute feature-pass decision** — delta_one specs declare `timeframes: [5m, 15m, 1h, 4h, 24h]`;
      a 1 m prediction target needs a 1 m feature pass (×5 rows) or a 5 m target. Done-when: ruling added to §1 with the
      cost difference from the sizing run; `registry_specs.yaml` updated if 1 m is added.
- [ ] [DESIGN] P1. **Training / inference placement ruling** (D8) written into
      `/codex/04-architecture/ml-experiment-lifecycle.md` § deployment placement, including the GPU threshold derived
      from the sizing run. Done-when: § merged.

### T8 — Forked child plans (finding R; digest only — each child's file is its dispatch surface)

- [`trading_pipeline_all_shard_smoke_matrix_2026_08_22.md`](/plans/active/trading_pipeline_all_shard_smoke_matrix_2026_08_22.md)
  (`system_readiness_master`) — all-shard matrix on warm workers (D11 / D15 / D16), alerts interleave, 64 GB ceiling.
- [`trading_pipeline_config_shard_identity_and_latency_profile_2026_08_22.md`](/plans/active/trading_pipeline_config_shard_identity_and_latency_profile_2026_08_22.md)
  (`batch_live_symmetry_master`) — D13 ids, force/freshness/skip everywhere, `DecisionTimeline` + `LatencyProfile`
  (D17), code-semver + config-version stamping (manifest v10).
- [`shard_plan_and_resource_driven_shapes_2026_08_22.md`](/plans/active/shard_plan_and_resource_driven_shapes_2026_08_22.md)
  (`infrastructure_master`) — D18 `ShardPlan`, launcher de-hardcoding, multiprocess shard loop, streaming readers,
  monitors for multi-shard VMs.
- [`instrument_spec_versions_and_is_layer0_coverage_2026_08_22.md`](/plans/active/instrument_spec_versions_and_is_layer0_coverage_2026_08_22.md)
  (`instruments_master`) — `InstrumentSpecVersion` with effective dates, execution reads specs by date, IS layer-0
  honest coverage with separate IS / MTDS rollups.

- [`event_driven_manifest_consolidation_2026_08_22.md`](/plans/active/event_driven_manifest_consolidation_2026_08_22.md)
  (`manifest_master`) — D19 write-triggered consolidation, 15-min floor, trigger-aware staleness, benchmark-gated merge home.

### T7 — Ratification, codex audit, closure

- [ ] [OPERATOR] P0. **Ratify the decision ledger §1** (D1-D9: engine per family, telemetry contract ownership, price
      table ownership, gap model, skill names, ML placement). Spend and structure judgment — not delegable.
- [ ] [REVIEW] P1. **Post-phase codex audit** — every path under "Codex SSOTs" re-read against shipped code, stale
      claims fixed in place, `/docs-reconcile` run. Done-when: list of touched codex docs with shas in the Progress Log.
- [ ] [DOC] P1. **Fork per owning epic** (finding R + the epic-assignment rule) — T1 telemetry → child under
      `observability_master`; T3 index/read path + T5 gap columns → `manifest_master`; T4 parity →
      `mtds_mdps_master` + `features_and_ml_master`; T8 matrix → `system_readiness_master` (done 2026-08-22). Parent
      keeps `depends_on` + digest lines. Done-when: each child exists with `parent_epic` set and the sections here
      point to them.
- [ ] [DOC] P2. **Archive this plan** per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` once
      every todo above is `[x]`.

## Codex SSOTs

- `/codex/06-coding-standards/data-engine-selection.md` — single-engine rule; BQ tier; amended by T3 (reader vs compute).
- `/codex/06-coding-standards/read-time-filter-pushdown.md` — list-stage filtering; T3 extends it to scan-stage pruning.
- `/codex/02-data/availability-manifest-and-data-status.md` — manifest SSOT; T3 per-cell index, T5 gap columns.
- `/codex/02-data/honest-absence-downstream-handling.md` — read-side absence rules; T5 adds produced-with-gaps.
- `/codex/02-data/shard-coverage-classification.md` — RUNNABLE / INSUFFICIENT_HISTORY / HONEST_EMPTY; T5 adds RUNNABLE_WITH_GAPS.
- `/codex/02-data/honest-coverage-model.md` — denominators; T1 cost model and T4 MDPS/features layers reuse them.
- `/codex/04-architecture/shard-level-failure-isolation.md` — no-raise-in-loop; T4 `run_shard_loop` implements it.
- `/codex/05-infrastructure/deployment-observability.md` — compute-unit classification + `CLOUD_RUN_JOBS`; T1 extends.
- `/codex/05-infrastructure/vm-launcher-runbook.md` — VM launch gotchas; every T0/T2/T6 VM run follows it.
- `/codex/04-architecture/ml-experiment-lifecycle.md` — registry + promotion; T6 adds placement.
- `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` — ε = 0 spine; the strategy skill's batch-paper leg.
- `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` — every VM/benchmark run here is polled on a progress metric.

## Explicitly out of scope (owned elsewhere)

- The BATCH / PAPER / LIVE gate sets and their ratification — `/plans/active/data_pipeline_completion_2026_08_21.md`.
- Per-venue batch smoke bar and e2e contract walks — `/plans/active/venue_smoke_test_bar_2026_08_16.md`,
  `/plans/active/venue_e2e_wiring_2026_08_16.md`.
- Three-stage benchmark harness + portability + reference ETA — batch15 items 4-6 (shipped); T1/T2 consume its stage names.
- kdb+ as a hot-tier read replica — assessed 2026-08-22 (no measured gap yet); revisit only after T1 telemetry gives a
  live-path p50/p95 and a licensing/cost decision exists.

## Progress Log

- **2026-08-22 (interactive session, slot 6, operator)**: Plan created from the kdb → hive/engine → smoke-test →
  telemetry discussion. Every §0 number was measured in-session (`rg` counts over `src/` excluding tests, codex reads,
  skill + result-file reads); §3 is an explicit prior, not a measurement. Operator rulings captured as D1-D9; D8 is a
  recommendation pending T7 ratification. Human plan by operator choice ("lets make a human plan").
- **2026-08-22 (interactive session, slot 6, operator — extension)**: Manifest read/write audit added to §0 (whole-blob
  download on every read; ~40 % bare call sites; per-VM shard = CAS rewrite; stock image + `uv pip install` per boot;
  one VM per (shard, leg)); rulings D10-D12; three T3 todos (bare-read ratchet, cell-partitioned index bytes,
  append-only per-VM parts); T8 forked to `trading_pipeline_all_shard_smoke_matrix_2026_08_22.md`; epic-fork todo in
  T7. Operator asks captured: one day per shard for ALL shards (existing shard → skip timing + perf; empty cell → full
  e2e), startup abstracted away, memory management before resizing with a 64 GB hard stop, VMs only, alerts-reconcile
  running while shards process.
- **2026-08-22 (interactive Q&A, slot 6, operator)**: Two rounds of rulings recorded as D13-D18; bare-read todo
  rewritten to migrate-all-then-ban; T8 became the child-plan index (four children, each under its owning epic).
- **2026-08-22 (operator, consolidation-trigger ruling)**: D19 added; event_driven_manifest_consolidation child created under manifest_master; assigned to tranche B.
- **Tranche ownership (2026-08-22, dispatch round)** — five /autonomous agents, one per tab/slot; boundaries are the
  collision contract, recorded here so the dispatch prompts are regenerable from the repo alone. **A**: T0+T1+T2 +
  provider auth/billing probe (smallest real pull per provider per AG → `plans/audit/results/provider_auth_billing_probe_<date>.md`;
  Databento = BLOCKED-CREDENTIALS until new keys); OWNS the `pipeline_e2e_check` engine + the `ShardRunTelemetry`
  contract (ships it first, posts sha here). **B**: T3+T5 + the whole event_driven_manifest_consolidation plan, in its
  stated order (sequencing gate before any cron slows); OWNS `manifest_writer/**` + `manifest_consolidator.py` — v10
  columns land only through B. **C**: T4 + instrument_spec_versions_and_is_layer0_coverage; adopts `run_shard_loop`
  after D posts its sha. **D**: shard_plan_and_resource_driven_shapes; OWNS `run_shard_loop` + the MDPS/execution
  reader files (streaming). **E**: config_shard_identity_and_latency_profile + the matrix BUILD-OUT (runner, launcher,
  baked image, sentinel/deadman, controller — but NOT the matrix runs) + T6 sizing; `check_config_shard_fresh` lives in
  `manifest_freshness.py`, not `manifest_writer/**`. **Excluded fleet-wide**: executing the all-shard matrix, its
  3-checkpoint cadences and skip-time SLO — operator-triggered with an operator `--day` per AG. **The post-completion
  audit must verify the performance analytics and resource analytics end-to-end** (telemetry rows per shard/leg → BQ →
  deployment-ui expected-vs-actual, VM + Cloud Run parity) before any smoke run is prepared. Session lessons: BSD awk
  has no `\s` (use `[[:space:]]` — a silent no-op cost one push cycle); prefer append-only Progress-Log edits over
  mid-file matching once prettier has re-wrapped a landed doc; `TMPDIR=$HOME/.cache/...` keeps safe-doc-push's isolated
  worktree out of swept temp roots; a HEAD-behind checkout makes new-at-origin files look untracked — `git pull
  --ff-only` before editing them.
- **2026-08-22 (autonomous session, slot 7 — this is tranche A)**: Confirmed via the tranche-ownership entry above —
  this dispatch matches tranche A (T0+T1+T2+provider probe) exactly. Slot 6 had 10 live occupants (collision warning)
  at dispatch time — claimed unclaimed slot 7 instead, all 12 target repos pulled clean to latest `live-defi-rollout`.
  T0 audit landed (appended above as "T0 results"): 20/20 skill×AG rows filled, 0 clean — IS has no
  `--require-captured`/`--auto-day`/benchmark leg at all; MTDS has an undefended `--allow-live-prod-writes` escape
  hatch + no benchmark leg; MDPS has zero benchmark history ever + no codex row for its shard hierarchy; features'
  `_run_benchmark_leg` confirmed still fabricates a rate when `exit_status != 0` (`objects=0` bug), same bug class
  confirmed present (dormant) in MDPS's `_run_one_benchmark`; 100% of historical features benchmark runs used 7 days
  despite the code default being 30. Filed as T2 P0 fix-todos (already in this plan's benchmark-leg-hardening item).
  Shipped (pending QG — see below) T1's foundational contract, code-complete + unit-tested:
  - **UAC** `unified_api_contracts/internal/{shard_run_telemetry,compute_price_table}.py` + guard tests
    (`tests/internal/unit/test_{shard_run_telemetry,compute_price_table}.py`). Pydantic `ShardRunTelemetry` (wire
    record) + `ShardAtom`/`StageTiming`/enums; `compute_price_table` prices every GCP machine type currently in
    `deployment-service/scripts/vm/launch-*.sh` (e2-{micro,small,medium,standard-*,highmem-*}, n1-standard-8,
    n2-{standard-8,highmem-*}) + AWS equivalents + T4 GPU + Cloud Run Jobs + GCS ops, all dated 2026-08-22 approximate
    public list prices (WebFetch on the live GCP pricing pages failed — JS-rendered, no static content — so this is a
    documented reference snapshot, not a live-fetched one; refresh via the Cloud Billing Catalog API in a follow-up).
    **Deviation from this plan's literal wording, documented in the new codex SSOT**: `ShardRunTelemetry` publishes on
    a SIBLING `shard-run-telemetry` topic, not "the existing `resource-samples` topic as a new message kind" as
    originally written — a native BigQuery Pub/Sub subscription binds one topic to exactly one destination table
    (confirmed via the deployment-service terraform research pass), so a differently-shaped row can't fan out of
    `resource-samples` into a second table. `to_publish_dict()` flattens `shard.*`/`stage_timings` to
    `shard_*`/`stage_*_sec` keys to match.
  - **UTL** `unified_trading_library/monitors/shard_telemetry_recorder.py` (+ exported from `monitors/__init__.py`) —
    `ShardTelemetryRecorder` context manager (mirrors `core.performance_monitor.PerformanceContext`'s shape: records
    on `__exit__` regardless of exception, never swallows it) with `wrap_storage_client()` — a counting proxy around
    `StorageClient` rather than monkeypatching the process-wide `get_storage_client()` cache (would leak counters
    across unrelated concurrent callers). 24 unit tests, quality-gates.sh GREEN (7270 passed, 3 pre-existing failures
    unrelated to this change — `test_ws_session_manager`/`test_g9_regression_canonicalisation`/
    `test_synthetic_harness`, already documented host-capacity flakiness per
    `fleet_wide_qg_self_hosted_runner_capacity_crisis_progress_log_history_2026_07_29.md` and 2 other corpus docs, not
    caused by this session).
  - **deployment-service**: `bootstrap_operational_data_bq.py` gets a new `shard_run_telemetry` TABLES entry
    (day-partitioned on `run_started_at`, clustered `(service, shard_asset_group, mode)`, 90-day retention) — found
    mid-implementation that `resource_samples`'s BigQuery landing is **Python-bootstrapped, not terraform**
    (`deployment_operational_data` is a deliberate exception to this repo's otherwise-terraform-managed BQ datasets,
    confirmed via a dedicated research pass); followed that established precedent instead of introducing a
    first-of-its-kind terraform table. `setup-pubsub.sh` gets the sibling `shard-run-telemetry` topic +
    `shard-run-telemetry-bq` native BQ subscription entries. New QG guard
    `scripts/quality_gates/check_machine_type_price_coverage.py`, wired into `quality-gates.sh` — fails if any
    `launch-*.sh` `MACHINE_TYPE` has no registered price (no ratchet, fleet fully priced today). QG not yet run this
    session (host contention — see below).
  - **deployment-api**: `shard_run_telemetry_rolling_sql()` (sibling of `resource_samples_rolling_sql`) +
    `GET /api/vm-resources/shard-telemetry` route + `ShardTelemetryRow`/`Response` models, mirroring the existing
    `/rolling` endpoint's honest-degrade pattern (mock-mode/no-project/query-failure → empty rows, never 5xx) exactly.
    16 new unit tests added to `test_vm_resource_history.py`. quality-gates.sh GREEN after one E501 fix.
  - New codex SSOT `/codex/05-infrastructure/shard-resource-telemetry.md` — the contract, pricing, landing-deviation,
    and read-path all in one place; T1's DOC todo.
  - Provider-probe scoping (EXTRA DELIVERABLE) done via a dedicated research pass: full provider inventory across the
    5 AGs (MTDS `market_interface/adapters/` — the `adapters/` dir one level up is legacy UMI code, not live;
    instruments-service `reference_data/adapters/{cefi,defi,tradfi,prediction,sports}/`), credential pattern per
    provider (uniformly `get_secret_client()` — no `os.getenv` found anywhere), the `-test-` bucket resolution
    pattern, and the reusable `pipeline_e2e_check.py --day --asset-group --venue --legs force --auto-day` CLI as the
    per-provider probe driver (no bespoke fetch code needed). Execution (real 1-instrument/1-day requests) not yet run
    this session — next tick.
  - **Infra finding**: this laptop's QG-governor (`qg-host-governor.sh`) is running host-wide cap 7 / per-repo
    sub-caps (unified-api-contracts sub-cap 1) under heavy multi-slot contention (dozens of concurrent `running.*`/
    `timeout.*` markers in `.benchmarks/qg-governor/` from many peer sessions across slots 1-6). The UAC QG run timed
    out at the governor's own 3600s cap waiting for its sub-cap-1 slot (never got to run pytest) and was retried;
    genuinely unrelated to code correctness — UTL's identical editable-path import of the same new UAC code passed
    clean. Not filing a new issue doc — this exact class of problem is already tracked in
    `fleet_wide_qg_self_hosted_runner_capacity_crisis_*` history.
  - **Learned the hard way**: `git checkout HEAD -- <this file>` to clear a safe-doc-push merge-conflict-marker
    corruption also silently discarded an EARLIER uncommitted edit (the T0-results append from a sub-agent, done via
    Edit tool, never committed) stacked in the same working tree — recovered byte-exact from the sub-agent's own
    transcript JSONL (`grep`+`json.loads` extraction of the Edit tool call's `new_string`, never a full-file read) and
    re-spliced in programmatically. Lesson for the next tranche hitting this: after ANY safe-doc-push conflict
    recovery, verify every uncommitted section your OWN prior turns added is still present before re-editing — a
    "restore to entry content" safety net only protects the push script's OWN corruption, not prior uncommitted work
    stacked underneath it.
  - **Nothing has been shipped via quickmerge yet this session** — all of the above is uncommitted working-tree state
    in slot 7, pending UAC's QG clearing the governor queue. Ship order once green: UAC → UTL → deployment-service →
    deployment-api (dependency order; UTL/deployment-service/deployment-api already resolve the new UAC symbols via
    each repo's `path = "../unified-api-contracts", editable = true` dependency, so none of this is actually blocked
    on UAC being *published* — only on UAC's own QG confirming green before its commit).
