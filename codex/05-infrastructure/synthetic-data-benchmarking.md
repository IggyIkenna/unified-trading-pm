---
doc_type: codex-ssot
title: Synthetic-Data Pipeline Benchmarking
summary:
  SSOT for the synthetic-data benchmark harness — the 5 UAC contract axes
  (SyntheticGeneratorId/Domain/RealismAxis/ShardLayout/Params), the UTL generator + per-stage profiler +
  BenchmarkHarness DAG, the benchmark CLI/launcher, and the (still-unpopulated) VM-shape recommendation matrix.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, unified-trading-library]
scope: [engineer, admin]
tags: [synthetic-data, performance, benchmark, infrastructure, spot-vm]
related:
  [
    /codex/05-infrastructure/runtime-tiers-and-deployment.md,
    /codex/06-coding-standards/performance-targets.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-05-12
authoritative_for: [synthetic-data pipeline benchmark harness]
referenced_by:
  [/codex/05-infrastructure/runtime-tiers-and-deployment.md, /codex/06-coding-standards/performance-targets.md]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Synthetic-Data Pipeline Benchmarking

> **SSOT for the synthetic-data benchmark harness** — the generator contract, the per-stage profiler, the harness DAG,
> the benchmark CLI / launcher, and the VM-shape recommendation matrix. Pre-cutover MVP per
> `plans/archive/2026_05/mock_data_pipeline_benchmarking_2026_05_10.md` (Phase 7.A — archived 2026-05-21). Composes with
> [`runtime-tiers-and-deployment.md`](runtime-tiers-and-deployment.md) (VM-shape recommendations feed the data-pipeline
> VM machine-type defaults) and
> [`/codex/06-coding-standards/performance-targets.md`](/codex/06-coding-standards/performance-targets.md) (the
> per-stage targets there should be backed by benchmark profile data, not guessed).

## Why this exists

May-23 cutover gates on Group F item 18 ("the 2-yr batch backtest completes inside an operationally-acceptable window").
Real-data per-stage profiling is gated on full backfill completion (mid-flight). The synthetic harness lets us pre-empt
VM-shape sizing surprises ~2 weeks early by driving the **same prod pipeline DAG** on synthetic input whose _shape_ (row
count / parquet byte size / shard fan-out) matches a real backfill, even though the _values_ are cheap-RNG fills.
Bottleneck measurement is shape-driven, not value-driven — so realism axes 1-3 suffice; axis 4 (calibrated GBM / SDEs
for value correctness) is post-cutover.

## The five contract axes (UAC — `canonical/crosscutting/synthetic_generator.py`)

1. **`SyntheticGeneratorId`** — closed StrEnum, one id per `(asset_group, data_type)` a cutover archetype consumes.
   Pre-cutover: 6 cefi (`cefi_trades` / `cefi_ohlcv_1m` / `cefi_ohlcv_15m` / `cefi_funding_rate` / `cefi_open_interest`
   / `cefi_liquidations`) + 5 defi (`defi_gas` / `defi_lst_rates` / `defi_lending_indices` / `defi_dex_pool_state` /
   `defi_oracle_feeds`) + 2 tradfi (`tradfi_ohlcv_1m` / `tradfi_ohlcv_1d`, the cross-asset hedge overlay).
   Sports/prediction = post-cutover.
2. **`SyntheticDataDomain`** — 8 shape families (`CEFI_TICK` / `CEFI_OHLCV` / `CEFI_DERIVATIVES` / `DEFI_ONCHAIN` /
   `DEFI_RATES` / `DEFI_DEX` / `DEFI_ORACLE` / `TRADFI_OHLCV`); UTL `synthetic/generator.py` dispatches a column
   skeleton + cardinality model per family.
3. **`SyntheticRealismAxis`** — `CARDINALITY` (axis 1: right row count + dtypes + monotone ts) → `PARQUET_SIZE` (axis
   2: + string-column width tuned to a real backfill byte-size sample) → `SHARD_COUNT` (axis 3: + correct fan-out so
   GCS/S3 listing depth matches prod). `CALIBRATED_DYNAMICS` (axis 4) is declared but NOT shipped.
4. **`SyntheticShardLayout`** — `shard_key_axes` (the SAME shard atom the `ManifestWriter` row key uses for that
   `(asset_group, data_type)` — see [`/codex/02-data/availability-manifest-and-data-status.md`] + the per-asset_group
   shard-atom matrix in `plans/epics/infrastructure_master.md`) + `shards_per_day` + `partition_template`. Drift between
   `shard_key_axes` and the manifest matrix is review-blocking.
5. **`SyntheticParams`** — a concrete generation request (a generator id + date range + cardinality knobs + resolved
   `output_uri` + RNG seed). Built from a `SyntheticGeneratorSpec.make_default_params(...)`; `params_hash()` is the
   idempotency key + part of the run_id.

Registry: `unified_api_contracts/registry/generators/{cefi,defi,tradfi}.py` each register `SyntheticGeneratorSpec`
instances into `SYNTHETIC_GENERATOR_REGISTRY` at import (mirrors the `registry/scenarios/` pattern). Lookup helpers:
`get_generator_spec(id)`, `generators_for_archetype(archetype)`. All surfaced on the top-level UAC facade.

## The generator (UTL — `unified_trading_library/synthetic/generator.py`)

`generate(params, *, writer=None) -> SyntheticOutputManifest`:

- enumerates the shard cells (cross-product of the non-`dt` shard-key axes),
- per (cell, day): allocates `row_count_per_day` to the cell (uniform split EXCEPT `defi_gas`, which is weighted by
  `PER_CHAIN_BLOCK_RATE_PER_DAY` — ETH ~7.2k / ARB ~350k / OP+BASE ~43.2k / SOL ~216k blocks per day; do NOT use a
  uniform split for gas), seeds a per-shard RNG (`params.seed XOR hash(day, cell)` → deterministic, byte-stable
  parquets), builds a polars DataFrame with the domain's column skeleton + a per-row
  `available_at = event_ts + emission_latency` (write-time arrival, per the CLAUDE.md "available_at is per-row,
  write-time" rule),
- writes one `part-0.parquet` per (cell, day) under `partition_template`, plus a `_synthetic_manifest.json`
  (`SyntheticOutputManifest` — the harness loads it to verify row counts + shard existence before kicking the pipeline).
  `writer` defaults to a local-FS writer for plain paths, a `gs://`/`s3://` writer via `get_storage_client()` otherwise;
  inject a fake writer in unit tests.

The `_synthetic_manifest.json` is a generator-side **receipt**, NOT a coverage record — the synthetic _pipeline run_
writes a real availability manifest of its own (live = batch).

## The per-stage profiler (UTL — `unified_trading_library/synthetic/profile.py`)

`profile_stage(name, ...)` context manager wraps one pipeline stage and records a `StageProfile`: `wall_clock_seconds`,
`cpu_seconds` / `cpu_max_percent` (sampler thread, process + children), `rss_max_bytes`, `io_read_bytes` /
`io_write_bytes` (psutil io-counters delta), `cloud_list_calls` / `cloud_objects_listed` (via `record_cloud_listing()`
thread-local — the harness wraps the storage client's `list_blobs` with a counter, so deep partition trees show up as a
real listing-depth bottleneck). An exception inside the block is recorded (`exit_code=1` + `error_summary`) and
re-raised — the harness catches it at the loop level so one bad stage doesn't lose the others' profiles
(shard-level-failure-isolation analogue for stages). `StageProfileAccumulator` collects the rows + `write_parquet()`s
`stage_profile.parquet`.

## The harness (UTL — `unified_trading_library/synthetic/harness.py`)

`BenchmarkHarness.run(archetype, ...)`:

1. **Generator step** — runs `generate()` for each spec the archetype consumes → builds a `SyntheticRunManifest`.
2. **Pipeline step** — drives the canonical DAG
   `PIPELINE_STAGE_ORDER = (mtds_read, mdps_compute, features, ml_inference, strategy, matching_engine)` — or the subset
   the run's generators declare in `pipeline_stages_touching` (optional stages, e.g. `ml_inference`, are _skipped_ not
   _failed_ when no generator touches them). Each stage runs inside `profile_stage()`.
   - **`subprocess` mode** (the real mode): each stage is a `subprocess.run` of the service CLI with
     `--synthetic-input-uri <prefix>` (the flag each service CLI gains — Phase 4-tail; until then a placeholder stage
     raises `HarnessStageNotWiredError`). NO parallel pipeline — the harness only sequences + profiles the prod CLIs.
   - **`stub` mode**: in-process stubs that touch ~16 MB + sleep ∝ input cardinality so the profiler emits non-trivial
     rows — for smoke / CI / wiring tests only (the profiles are meaningless — they measure the stubs).
3. **Emit** — `stage_profile.parquet` + `synthetic_run_manifest.json` under `<report-uri>/{archetype}/{run_id}/`.

`strict_stages=True` stops after the first failed stage; default continues so the report shows where the pipeline broke.

## The benchmark CLI + launcher

- **CLI**:
  `python -m unified_trading_library.synthetic --archetype <X> --date-start.. --date-end.. --input-uri.. --report-uri.. --mode stub|subprocess --row-count-scale.. [--venues/--instruments/--chains/--protocols/--strict-stages]`.
  `--input-uri` / `--report-uri` are explicit (the launcher resolves them; when the `benchmark-reports` bucket kind
  lands in `cloud-providers.yaml` the CLI should derive it via `resolve_bucket_name(kind="benchmark-reports")`).
- **Launcher**:
  `deployment-service/scripts/vm/launch-synthetic-benchmark-vm.sh --archetype <X> --shapes "c2-standard-8 c2-standard-16 c2-standard-32 c3-highcpu-44" --date-start.. --date-end.. --mode.. --env..`
  — fans out one GCE VM per (archetype, machine-type) via the `setup-data-pipeline-vm.sh` bootstrap with `SYNTHETIC_*`
  metadata; VM name `synbench-{arch}-{shape}-{ts}` (the `synbench-` prefix is registered in
  `vm_zombie_watchdog.py:VM_PREFIX_TO_BUCKET` — relaunch the watchdog VM before the first real run). No fire-and-forget:
  each VM emits STARTED + per-stage progress
  - STOPPED to `gs://{pid}-events/events/unified-trading-library/{date}/{vm_name}/`.

## VM-shape recommendation matrix (Phase 6 — populated from real-VM runs)

The Phase-6 aggregation groups the per-`(archetype, vm_shape)` `stage_profile.parquet` files into per-stage P50/P95/P99
wall-clock + CPU% + RSS + IO, then derives a per-archetype × per-stage `(min_cpu, min_ram, min_disk, min_iops)`
recommendation justified by the profile. Stages whose `wall_clock × scale_factor` exceeds the Group F item 18
"operationally-acceptable window" are filed as P0 follow-ups for `live_pipeline_mtds_mdps_features_2026_05_08`
consumers. The recommendation matrix replaces the guessed defaults in `runtime-tiers-and-deployment.md` (data-pipeline
VM machine type) + `performance-targets.md` (per-stage targets). **Status (2026-05-22): matrix not yet populated** — the
real-VM runs remain blocked; this is post-cutover backlog tracked under `plans/epics/infrastructure_master.md`.

> **[DELTA 2026-05-22]** **Current state:** VM-shape recommendation matrix remains unpopulated as of 2026-05-22. Real-VM
> benchmarking runs have not yet executed (Phase-4-tail blocked). **Planned delta:** Populate matrix post-cutover under
> `plans/epics/infrastructure_master.md`. **Target architecture:** Per-archetype × per-stage
> `(min_cpu, min_ram, min_disk, min_iops)` recommendations derived from `stage_profile.parquet` runs on real VMs.

## Execution-owner

```yaml
execution:
  owner: mock_data_pipeline_benchmarking_2026_05_10.md Phase 5 (slot 7 — Harsh side); one-shot per cutover-archetype
  cadence: one-shot (pre-cutover); a continuous nightly-perf cron is post-cutover (plan non-goal)
  verifier:
    per-VM STARTED + per-stage progress + STOPPED in gs://{pid}-events/events/unified-trading-library/<date>/<vm>/ ;
    >=10 (archetype x shape) stage_profile.parquet in gs://{pid}-benchmark-reports/
  last_executed: NEVER
```

## Adding a new generator (the 4-step workflow)

1. Append the id to `SyntheticGeneratorId` (closed StrEnum).
2. Add a `SyntheticGeneratorSpec` to `registry/generators/<asset_group>.py` (self-registers via `register_generator`).
3. Implement the column skeleton in UTL `synthetic/generator.py` `_build_dataframe` for the spec's `domain` (in the SAME
   logical unit — Citadel pre-audit: workspace-grep every existing reader of that `(asset_group, data_type)` and match
   the prod schema, per the Phase-3.D schema-parity rule).
4. Update this doc.
