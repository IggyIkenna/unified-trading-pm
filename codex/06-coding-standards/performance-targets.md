---
doc_type: codex-ssot
title: Performance Targets
summary:
  Performance-target SSOT — latency (p50/p95/p99/max per path), throughput, and per-Cloud-Run resource ceilings, the
  machine-readable YAML block, memory-leak soak tolerance (+10%/30min, +15%/peak), and the benchmark-backed per-stage
  bottleneck classification + top-3 optimization priorities (features_compute/mtds_read/mdps_compute) for the cutover
  pipeline, with spot-instance viability + checkpoint-restart grains.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, features-service, strategy-service]
scope: [engineer]
tags: [performance, monitoring, cost, backfill, spot-vm, data-pipeline]
related:
  [/codex/05-infrastructure/synthetic-data-benchmarking.md, /codex/08-workflows/cutover-window-dependency-order.md]
created: 2026-03-27
authoritative_for: [performance latency/throughput/resource targets, per-stage benchmark bottleneck classification]
referenced_by: [/codex/05-infrastructure/synthetic-data-benchmarking.md, plans/epics/features_and_ml_master.md]
owner:
last_reviewed:
code_refs:
---

# Performance Targets

**Status:** Active — all CI performance gates must validate against these targets.

---

## Latency Targets

All latencies measured end-to-end (wall clock), using mocked external dependencies unless otherwise noted.

| Path                                                   | p50   | p95    | p99    | max    |
| ------------------------------------------------------ | ----- | ------ | ------ | ------ |
| Order submission (execution-service → venue mock)      | 200ms | 400ms  | 500ms  | 1000ms |
| Signal generation (strategy-service, full cycle)       | 500ms | 800ms  | 1000ms | 2000ms |
| Feature computation (any single service, 1 symbol)     | 100ms | 300ms  | 500ms  | 1000ms |
| ML inference (ml-inference-service, single prediction) | 50ms  | 150ms  | 250ms  | 500ms  |
| End-to-end signal-to-order (strategy → execution)      | 800ms | 1500ms | 2000ms | 5000ms |
| GCS read (feature batch, 1 day, 1 symbol)              | 500ms | 1000ms | 2000ms | 5000ms |
| PubSub publish (single event)                          | 10ms  | 50ms   | 100ms  | 200ms  |

### In-process matching (execution-service, BatchMatchingEngine)

| Path                        | p99 target |
| --------------------------- | ---------- |
| Simulated fill (batch mode) | <1ms       |
| Order routing overhead      | <1ms       |
| TWAP schedule generation    | <1ms       |
| VWAP volume calculation     | <2ms       |

---

## Throughput Targets

| Component           | Target                                           |
| ------------------- | ------------------------------------------------ |
| Tick ingestion      | ≥1000 ticks/second per venue                     |
| PubSub events       | ≥500 events/second sustained                     |
| Backfill            | ≥1M ticks/hour per venue (with Tardis/Databento) |
| Feature computation | ≥100 instrument-days/second                      |
| ML inference batch  | ≥10 predictions/second                           |

---

## Resource Targets

Per service, per Cloud Run instance under normal load.

| Service tier               | Max CPU | Max memory | Max GCS ops/min |
| -------------------------- | ------- | ---------- | --------------- |
| Data services (MTDH, MDPS) | 80%     | 2GB        | 1000            |
| Feature services (all 8)   | 70%     | 1.5GB      | 500             |
| ML inference               | 90%     | 4GB        | 100             |
| Strategy service           | 60%     | 1GB        | 200             |
| Execution service          | 70%     | 2GB        | 300             |

---

## Machine-Readable Targets (YAML)

```yaml
latency_targets_ms:
  order_submission:
    p50: 200
    p95: 400
    p99: 500
    max: 1000
  signal_generation:
    p50: 500
    p95: 800
    p99: 1000
    max: 2000
  feature_computation:
    p50: 100
    p95: 300
    p99: 500
    max: 1000
  ml_inference:
    p50: 50
    p95: 150
    p99: 250
    max: 500
  e2e_signal_to_order:
    p50: 800
    p95: 1500
    p99: 2000
    max: 5000
  gcs_read:
    p50: 500
    p95: 1000
    p99: 2000
    max: 5000
  pubsub_publish:
    p50: 10
    p95: 50
    p99: 100
    max: 200

inprocess_matching_targets_ms:
  simulated_fill_p99: 1
  order_routing_p99: 1
  twap_schedule_p99: 1
  vwap_calculation_p99: 2

throughput_targets:
  tick_ingestion_per_sec: 1000
  pubsub_events_per_sec: 500
  backfill_ticks_per_hour: 1000000
  feature_computation_instrument_days_per_sec: 100
  ml_inference_predictions_per_sec: 10

resource_targets:
  data_services:
    max_cpu_pct: 80
    max_memory_gb: 2
    max_gcs_ops_per_min: 1000
  feature_services:
    max_cpu_pct: 70
    max_memory_gb: 1.5
    max_gcs_ops_per_min: 500
  ml_inference:
    max_cpu_pct: 90
    max_memory_gb: 4
    max_gcs_ops_per_min: 100
  strategy_service:
    max_cpu_pct: 60
    max_memory_gb: 1
    max_gcs_ops_per_min: 200
  execution_service:
    max_cpu_pct: 70
    max_memory_gb: 2
    max_gcs_ops_per_min: 300
```

---

## Memory Leak Tolerance

All services must stay within **+10% RSS growth** over a 30-minute soak test at normal load. Peak-load soak (5×
multiplier, 1 hour): **+15% RSS growth** maximum.

---

## CI Load Scenarios

| Scenario  | Multiplier | Duration | When runs |
| --------- | ---------- | -------- | --------- |
| normal    | 1×         | 60s      | Every PR  |
| peak      | 5×         | 600s     | Nightly   |
| sustained | 5×         | 3600s    | Weekly    |

Slow tests are marked `@pytest.mark.slow`. PR CI runs only `normal` scenario (excludes `slow`).

---

## Per-pipeline-stage targets — backed by the synthetic benchmark, not guessed

Per-stage wall-clock / CPU / RSS / IO targets for the cutover pipeline (`mtds_read` → `mdps_compute` → `features` →
`ml_inference` → `strategy` → `matching_engine`) should be derived from the synthetic-data benchmark harness's per-stage
profile, NOT estimated. See
[`/codex/05-infrastructure/synthetic-data-benchmarking.md`](/codex/05-infrastructure/synthetic-data-benchmarking.md) for
the harness, the `StageProfile` shape, and the per-`(archetype, vm_shape)` recommendation matrix.

---

## Per-stage bottleneck table (Phase 0 classification — 2026-05-13)

**Source**: `gs://central-element-323112-benchmark-reports/` — 8 benchmark runs across 2 archetypes × 4 VM shapes
(`c2-standard-8`, `c2-standard-16`, `c2-standard-30`, `c3-highcpu-44`), 1-day synthetic window at `row_count_scale=0.1`.
Run date: 2026-05-12. Plan: `plans/active/mock_data_pipeline_benchmarking_2026_05_10.md`.

### Stages with measured data (2 stages)

| Stage       | VM Shape       | Wall-clock (p50) |  CPU% (peak) |      RSS p95 |   Avg Threads | Net Write | io_read | Classification                         |
| ----------- | -------------- | ---------------: | -----------: | -----------: | ------------: | --------: | ------: | -------------------------------------- |
| `mtds_read` | c2-standard-8  |            8.07s |          38% |      1.28 GB |          0.04 |   6.96 MB |       0 | **NETWORK/GCS-I/O-bound**              |
| `mtds_read` | c2-standard-16 |       7.84–8.00s |          38% | 1.35–1.38 GB |          0.06 |   6.96 MB |       0 | **NETWORK/GCS-I/O-bound**              |
| `mtds_read` | c2-standard-30 |       7.82–7.88s |      39–200% | 1.50–1.51 GB |     0.08–0.09 |   6.96 MB |       0 | **NETWORK/GCS-I/O-bound**              |
| `mtds_read` | c3-highcpu-44  |       6.91–6.94s |          36% | 1.60–1.63 GB |          0.08 |   6.96 MB |       0 | **NETWORK/GCS-I/O-bound**              |
| `strategy`  | c2-standard-8  |       6.35–6.42s |          38% | 1.19–1.21 GB |     0.04–0.05 |   1.13 MB |       0 | **CPU-bound serial**                   |
| `strategy`  | c2-standard-16 |       6.24–6.36s |       19–38% | 1.26–1.30 GB |          0.06 |   1.13 MB |       0 | **CPU-bound serial**                   |
| `strategy`  | c2-standard-30 |       6.24–6.30s |       19–37% | 1.41–1.43 GB |     0.08–0.09 |   1.13 MB |       0 | **CPU-bound serial**                   |
| `strategy`  | c3-highcpu-44  |   **5.43–5.55s** | **131–196%** | 1.52–1.54 GB | **1.31–1.96** |   1.13 MB |       0 | **CPU-bound parallel (1.3–2 threads)** |

**Per-column interpretation:**

- `Avg Threads` = `cpu_seconds / wall_clock_seconds` — effective thread-level parallelism across the wall-clock window.
- `RSS p95` = peak resident memory at p95. For production: ~10× larger with full-scale data (row_count_scale 0.1→1.0).
- `io_read = 0` for ALL stages — confirms GCS reads bypass the OS I/O counter (network, not disk).
- `Net Write` = bytes written to local disk (working files + output parquet).
- `CPU% >100` on c3-highcpu-44 for `strategy` confirms multi-threaded execution (NumPy/pandas BLAS pools).

### Stages without measured data — DEFERRED (4 stages)

All 4 stages failed with import errors during the benchmarking run. The process started and consumed ~6s wall-clock
(Python init + partial module load) before crashing — these wall-clock numbers are **startup overhead only, not real
compute**. Real profiles are blocked on dependency fixes.

| Stage              | Failure cause                                                             | Wall-clock observed (startup overhead only) | Status                                                 |
| ------------------ | ------------------------------------------------------------------------- | ------------------------------------------: | ------------------------------------------------------ |
| `mdps_compute`     | `ModuleNotFoundError: exchange_calendars` not installed in benchmark venv |                                   ~6.1–6.3s | **DEFERRED** — benchmark not yet run; real compute TBD |
| `features_compute` | `ModuleNotFoundError: talib` not installed in benchmark venv              |                                   ~6.1–6.3s | **DEFERRED** — benchmark not yet run; real compute TBD |
| `matching_engine`  | `ModuleNotFoundError: nautilus_trader` not installed in benchmark venv    |                                   ~5.4–6.2s | **DEFERRED** — benchmark not yet run; real compute TBD |
| `ml_inference`     | `ModuleNotFoundError: sse_starlette` not installed in benchmark venv      |                                       ~6.2s | **DEFERRED** — benchmark not yet run; real compute TBD |

**Fix path**: `plans/active/mock_data_pipeline_benchmarking_2026_05_10.md` Phase 3.D — add missing packages to benchmark
venv, re-run matrix. After fix, update this table with real measurements.

**Critical implication**: `features_compute` and `mdps_compute` are almost certainly the largest cutover-window
bottlenecks (see Top-3 section below). Their real compute profiles are essential for Phases 2–4 of
`plans/active/compute_optimization_mock_data_2026_05_13.md`.

### Per-core scalability predictions

| Stage              | Scalability                                                                       | Evidence                                                                      | Recommended optimization                                                                                         |
| ------------------ | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `mtds_read`        | **serial-locked** (wall insensitive to core count)                                | +0.08s difference c2-8→c3-44; CPU% 19-38% regardless of shape                 | Add parallel-batch-fetch per instrument (async GCS reads); bigger machine adds no value for wall-clock reduction |
| `mdps_compute`     | **sublinear-70%** (estimate; inferred from compute-bound pattern)                 | Module import error; estimate based on typical pandas candle-compute patterns | Per-instrument shard-parallel execution; vectorised OHLCV aggregation                                            |
| `features_compute` | **linear** (strong estimate; DAG-independent families can fan-out)                | Module import error; 7 feature families are independent per instrument        | Per-family per-instrument worker pool; `--worker-count` flag + UTL `ParallelPerSymbolRunner`                     |
| `strategy`         | **linear up to 2 threads** (proven), **external fan-out beyond**                  | c3-highcpu-44: 131–196% CPU (1.3–2.0 threads); c2-8: 38% (0.38 threads)       | Per-day fan-out wrapper (Phase 1); per-config-cell fan-out; `c3-highcpu-176` gives 44× concurrent days           |
| `matching_engine`  | **sublinear-50%** (estimate; order-sequencing constraint)                         | Module import error; order matching has inherent sequential dependency        | Per-archetype parallel, not per-trade; fill-mode A vs B in parallel                                              |
| `ml_inference`     | **linear** (strong estimate; inference is embarrassingly parallel per instrument) | Module import error; per-instrument inference is independent                  | Per-instrument worker pool; batch inference with `--worker-count`                                                |

---

## Top-3 optimization priorities (by cutover-window contribution)

**Formula**: `serial_hours = wall_clock_s × call_count × data_scale_multiplier / 3600` where:

- `call_count` = per-archetype × per-day × per-instrument (or per-config-cell) for full 2yr/5yr backfill
- `data_scale_multiplier` = 10 (benchmark was row_count_scale=0.1; production is 1.0)
- Backtest windows: DeFi/Prediction = 730 days (2yr); CeFi/TradFi/Sports = 1825 days (5yr)
- Instrument counts from benchmark manifests: carry_staked_basis = 85 shards; leveraged_funding_arb = 261 shards

| Rank  | Stage              | Serial wall-clock (both archetypes) | Benchmark status              | Data quality of estimate    | Parallelization hypothesis                                                                             |
| ----- | ------------------ | ----------------------------------: | ----------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------ |
| **1** | `features_compute` |        **~64,900 hrs (2,700 days)** | DEFERRED (talib)              | LOW — startup overhead only | Per-family per-instrument fan-out; 7 families × 85–261 instruments = 595–1,827-way parallelism per day |
| **2** | `mtds_read`        |          **~10,360 hrs (432 days)** | MEASURED                      | HIGH                        | Async parallel-batch GCS fetch per instrument-day; 85–261-way intra-day parallelism                    |
| **3** | `mdps_compute`     |           **~9,270 hrs (386 days)** | DEFERRED (exchange_calendars) | LOW — startup overhead only | Per-instrument shard-parallel; same fan-out as mtds_read                                               |

**Notes on estimates:**

- `features_compute` rank 1 is driven by 7× call_count multiplier (one call per feature family per instrument per day).
  Real compute per call may be much faster than the ~6.2s startup-overhead wall-clock used here. Fix talib + re-run
  before treating features as the #1 bottleneck.
- `mtds_read` rank 2 is the only stage with reliable measured data. Parallelization potential is high: the I/O-bound
  nature means async batching of GCS reads (or S3 for AWS parity) gives near-linear speedup with concurrent prefetch.
- `mdps_compute` rank 3 share the same per-instrument-per-day call structure as MTDS. Exchange_calendars fix unblocks
  the real measurement.

### Parallelization hypotheses for top-3

**1. `features_compute` — per-family fan-out (highest potential)**

- 7 feature families (`delta_one`, `onchain`, `volatility`, `calendar`, `cross_instrument`, `commodity`, `sports`) are
  independent across instruments and mostly independent across families.
- 85–261 instruments per archetype are fully independent per day.
- Maximum fan-out per day: `7 families × 261 instruments = 1,827 parallel workers` on `c3-highcpu-176` (176 vCPUs).
- With 176-way concurrency: estimated wall-clock per day ≈ `(6.2s × 7) / 176 ≈ 0.25s` (I/O + queue overhead will
  increase this, but order-of-magnitude: minutes not hours).
- **Requires**: `--worker-count` flag on features-service CLI + UTL `ParallelPerSymbolRunner` + shard-level isolation.

**2. `mtds_read` — async GCS batch-fetch**

- Currently serial per instrument per day (network-bound, ~7s per instrument on 1-day window).
- Production: 85–261 instruments × 730–1825 days = 62,050–476,325 serial calls.
- Simple fix: async parallel fetch (aiohttp / GCS `download_many`) for all instruments in a day-batch.
- With 100 concurrent GCS fetches: estimated wall-clock per day ≈ `7s × 85 / 100 ≈ 6s` (vs 595s serial).
- **Requires**: MTDS batch-async reader for per-day instrument-shard reads.

**3. `mdps_compute` — per-instrument-shard parallel (unblocked by exchange_calendars fix)**

- Same structure as mtds_read: per instrument per day.
- After dependency fix: expect compute-bound profile (OHLCV aggregation + calendar alignment).
- With same 100-concurrent pattern: wall-clock per day ≈ `6s × 261 / 100 ≈ 16s` (vs 1,566s serial).
- **Requires**: exchange_calendars in benchmark venv; then re-profile + Phase 2 worker-count wire-in.

---

## Acceptable wall-clock targets (production scale)

> **STUB — defer absolute numbers until Phase 5 SKU matrix completes.**
>
> Phase 5 of `plans/active/compute_optimization_mock_data_2026_05_13.md` extends the benchmark matrix to `c3-highcpu-88`
> / `c3-highcpu-176` / `m3-megamem-128` / `m3-ultramem-160`. The per-stage production-scale targets below will be
> populated after Phase 5 runs complete (target: 2026-05-19).

| Stage              | Current serial estimate (2yr/5yr) |            Target with parallelization | Target SKU              | Status        |
| ------------------ | --------------------------------: | -------------------------------------: | ----------------------- | ------------- |
| `features_compute` |                       ~2,700 days |        **< 2 hours** (176-way fan-out) | `c3-highcpu-176`        | TBD — Phase 5 |
| `mtds_read`        |                         ~432 days |      **< 4 hours** (async batch-fetch) | `c2-standard-8` (async) | TBD — Phase 5 |
| `mdps_compute`     |                  ~386 days (est.) |         **< 6 hours** (100-concurrent) | `c2-standard-16`        | TBD — Phase 5 |
| `strategy`         |                          ~32 days |        **< 2 hours** (per-day fan-out) | `c3-highcpu-176`        | TBD — Phase 5 |
| `matching_engine`  |                   ~34 days (est.) | **< 4 hours** (per-archetype parallel) | `c3-highcpu-44`         | TBD — Phase 5 |
| `ml_inference`     |                  ~386 days (est.) |         **< 4 hours** (100-concurrent) | `c3-highcpu-44`         | TBD — Phase 5 |

**Combined cutover-window target**: all 6 stages complete within a **24-hour window** (concurrent with real-data
backfill running in parallel). This is the May-23 cutover-window binding constraint per
`/codex/08-workflows/cutover-window-dependency-order.md`.

---

## Continuous verification

**Daily benchmark cron** (existing per `plans/active/mock_data_pipeline_benchmarking_2026_05_10.md`):

- Re-runs Phase 5/6 synthetic benchmark matrix nightly.
- Emits `stage_profile.parquet` to `gs://central-element-323112-benchmark-reports/`.
- **Regression gate**: flag any stage where `wall_clock_seconds_p50` regresses >10% vs last known-good run.
- Regression alert → open issue in `plans/active/issues/` + notify operator.

**Gate enforcement**:

- Pre-cutover (2026-05-15 → 2026-05-22): daily benchmark cron on `c3-highcpu-44` baseline.
- Post-cutover hardening: CI assertion gates on `wall_clock_seconds_p50` per stage vs targets in the "Acceptable
  wall-clock targets" table above (populated after Phase 5).

**Current last-verified**:

- `mtds_read`: 2026-05-12 (benchmark run `synbench-*-20260512-*`)
- `strategy`: 2026-05-12 (benchmark run `synbench-*-20260512-*`)
- `mdps_compute`, `features_compute`, `matching_engine`, `ml_inference`: NEVER (blocked on dependency fixes)

---

## Preemptible / spot-instance viability (Phase 5 assessment — 2026-05-20)

**Conclusion: YES — all large compute shapes clear the ≥40% cost-saving threshold.**

GCP asia-northeast1 preemptible pricing vs on-demand for the Phase 5 extended shapes (GCP list pricing, 2026-05):

| Shape           | On-demand $/hr (est.) | Preemptible $/hr (est.) | Savings | Passes ≥40% gate |
| --------------- | --------------------: | ----------------------: | ------: | :--------------: |
| c3-highcpu-88   |                 ~3.50 |                   ~0.70 |     80% |        ✅        |
| c3-highcpu-176  |                 ~7.00 |                   ~1.40 |     80% |        ✅        |
| m3-megamem-128  |                ~10.65 |                   ~2.13 |     80% |        ✅        |
| m3-ultramem-160 |                ~27.50 |                   ~5.50 |     80% |        ✅        |

_Preemptible VMs are ~20% of on-demand price for c3/m3 shapes in asia-northeast1. Up to 24h runtime; 30s eviction
notice. Acceptable for batch compute stages with checkpoint-restart._

**Checkpoint-restart design** (post-cutover scope — natural resumability per stage):

| Stage              | Checkpoint grain                | Resume strategy                                                      |
| ------------------ | ------------------------------- | -------------------------------------------------------------------- |
| `features_compute` | instrument-day                  | Re-run only unwritten instrument-days; skip if output parquet exists |
| `strategy`         | config-grid cell × date-chunk   | Resume from last written chunk row in `grid_summary.parquet`         |
| `matching_engine`  | archetype × date-chunk          | Same as `strategy`; each chunk is an idempotent row                  |
| `ml_training`      | epoch checkpoint (`.ckpt` file) | Load last `.ckpt` at startup; skip completed epochs                  |

**Implementation note**: all stages already write to GCS atomically per shard (writegate discipline). Checkpoint-restart
reduces to "skip shards that already exist." Wire-in via `--resume` flag on each VM launcher script (post-cutover).

---

## Benchmark data provenance

| Field                        | Value                                                                                         |
| ---------------------------- | --------------------------------------------------------------------------------------------- |
| GCS bucket                   | `gs://central-element-323112-benchmark-reports/`                                              |
| Summary parquet              | `benchmark_report/benchmark_report.parquet`                                                   |
| Per-archetype stage profiles | `carry_staked_basis/*/stage_profile.parquet`, `leveraged_funding_arb/*/stage_profile.parquet` |
| Benchmark run date           | 2026-05-12                                                                                    |
| Archetypes benchmarked       | `carry_staked_basis` (DeFi), `leveraged_funding_arb` (CeFi)                                   |
| Benchmark window             | 1 calendar day (2024-01-01) at `row_count_scale=0.1` (synthetic)                              |
| VM shapes tested             | `c2-standard-8`, `c2-standard-16`, `c2-standard-30`, `c3-highcpu-44`                          |
| Successful stages            | `mtds_read` (8/8 runs), `strategy` (8/8 runs)                                                 |
| Failed stages                | `mdps_compute`, `features_compute`, `matching_engine`, `ml_inference` (import errors)         |
| Parent plan                  | `plans/active/mock_data_pipeline_benchmarking_2026_05_10.md` Phases 5/6                       |
| Optimization plan            | `plans/active/compute_optimization_mock_data_2026_05_13.md`                                   |
