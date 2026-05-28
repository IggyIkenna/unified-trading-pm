---
scope: [engineer]
---

# Data Engine Selection — Polars vs Pandas vs PyArrow

Codified 2026-05-28 per the operator-driven MDPS architecture audit (sibling plan:
[`plans/active/mdps_long_running_multi_shard_architecture_audit_2026_05_28.md`](../../plans/active/mdps_long_running_multi_shard_architecture_audit_2026_05_28.md)
§ "Finding D"). Workspace-wide rule for batch services that read/write parquet at non-trivial scale (≥ a few MB per
file, ≥ tens of files per shard).

## Rule

**Pick one data engine per service and stay in it end-to-end.** A service that reads parquet via Polars MUST also
aggregate, transform, and write via Polars. A service that reads parquet via Pandas with `engine="pyarrow"` MUST also
process and write via Pandas. **Mixing engines mid-pipeline is banned** — each conversion (`pl.DataFrame.to_pandas()`,
`pd.DataFrame.to_polars()`, `pa.Table.from_pandas()`) allocates a fresh buffer that is not returned to the OS by `del`,
`gc.collect()`, or process-internal arena-trim hints.

## Why

The three engines (Polars, Pandas+PyArrow, pure PyArrow) each manage their own memory arena. Allocations made inside an
arena live until the entire arena is dropped (process exit, or an engine-specific shutdown call). A `del` of the Python
wrapper releases the wrapper's reference; the underlying arena allocation persists. `gc.collect()` collects Python-level
reference cycles; it has no view into the C-extension arenas.

A pipeline that does:

```
GCS bytes  →  pl.read_parquet  →  pl.DataFrame
              ↓ .to_pandas()
              pd.DataFrame
              ↓ pl.from_pandas()
              pl.DataFrame   (← aggregate here)
              ↓ .to_pandas()
              pd.DataFrame
              ↓ .to_parquet()
              GCS bytes
```

allocates **four** independent buffer regions for one shard's data. Even after the function returns, three of them
remain pinned in their respective arenas. For a long-running multi-shard VM (see
[`vm-tarball-deployment.md`](../05-infrastructure/vm-tarball-deployment.md) § "Per-shard cleanup discipline"), this
compounds shard-over-shard regardless of any per-shard cleanup hook the service wires — the cleanup hook can `del` the
Python wrappers but cannot reach the arenas.

The [`service-orchestration-patterns.md`](service-orchestration-patterns.md) § 15 cleanup discipline is a necessary but
not sufficient condition for stable multi-shard RSS. Single-engine discipline is the other half.

## The decision tree

```
Does the service do aggregation / transformation / grouping in-process?
├── YES → pick pure Polars end-to-end (read + aggregate + write all via polars).
│         Polars supports every operation Pandas supports for batch data work and
│         has the better memory characteristics for high-volume parquet workflows.
│
└── NO  → service is I/O-only (read a parquet, slice, write a parquet, no aggregation):
          pick pure Pandas with engine="pyarrow":
            pd.read_parquet(..., engine="pyarrow")
            ...
            df.to_parquet(..., engine="pyarrow")
          Avoids the Polars dep for services that don't need its aggregation
          features. PyArrow is the underlying engine for both libraries; using
          pandas-on-pyarrow is the simplest end-to-end Python idiom.
```

**Pure PyArrow (no pandas wrapper)** is the lowest-level option. It's appropriate for migration scripts, schema-only
operations, and any code that doesn't need DataFrame semantics. Workspace services should not default to it for new code
— the operational ergonomics of Polars or pandas-on-pyarrow are better.

## Banned anti-patterns

1. **Polars → Pandas → Polars** (the MDPS 2026-05-28 shape). Reading via `pl.read_parquet`, immediately calling
   `.to_pandas()`, then later re-converting back to polars for aggregation. Allocates two buffers; arenas of both
   engines retain.
2. **Polars + `pd.read_parquet` in the same function.** If you find yourself importing both libraries in one module, a
   conversion is hiding somewhere downstream. Audit and pick one.
3. **`engine="pyarrow"` flag forgotten on pandas reads.** `pd.read_parquet(path)` defaults to `engine="auto"` which
   resolves to pyarrow if installed but falls back to fastparquet if pyarrow is absent. Pin it explicitly. The fall-
   back path produces different schema-coercion behavior in edge cases.
4. **`low_memory=True` on Polars followed by `.to_pandas()`.** The `low_memory=True` flag tells Polars to stream the
   parquet in chunks rather than slurping the whole file. The benefit is negated as soon as the result is materialized
   via `.to_pandas()` — pandas always materializes fully. Pick one engine; don't pair contradictory flags.

## Per-engine memory-bound checklist

When the chosen engine is **Polars**:

- Use `pl.scan_parquet()` (LazyFrame) for reads whose result will be filtered/aggregated. Avoid eager `pl.read_parquet`
  unless you actually need every row materialized.
- Aggregate via `LazyFrame.group_by(...).agg(...)` then `.collect()` once at the end. Avoid intermediate `.collect()`s
  inside the aggregation chain.
- Configure the Polars thread pool size via the `POLARS_MAX_THREADS` env var, matched to the VM's CPU count (the default
  polars behavior is to spawn one thread per CPU, which is usually fine but worth pinning explicitly in QG- tested
  envs).

When the chosen engine is **Pandas + PyArrow**:

- Pass `engine="pyarrow"` and `dtype_backend="pyarrow"` on `read_parquet` to keep PyArrow types throughout the pipeline.
  Standard NumPy-backed pandas types defeat half the memory benefit.
- For row-filtering work, use `pa.dataset.Dataset` directly (skip the pandas wrapper) — filter at the pyarrow layer
  before pandas materialization.

When the chosen engine is **pure PyArrow**:

- Use `pa.parquet.ParquetFile` for incremental row-group iteration. Avoid `pa.Table.from_batches` for very large files —
  it materializes the whole table at once.
- Schema operations only — no DataFrame semantics. If you need DataFrame ops, switch to Polars or pandas+pyarrow.

## Reference incident

**2026-05-28** — MDPS narrow-scope smoke. `_read_tick_data`
([`live_workers.py:449-479`](../../../market-data-processing-service/market_data_processing_service/app/core/live_workers.py#L449-L479))
called `pl.read_parquet(..., low_memory=True)`, then `.to_pandas()`, then `del`'d the polars frame, returned the pandas
frame to `_process_all_timeframes`
([`live_workers.py:671+`](../../../market-data-processing-service/market_data_processing_service/app/core/live_workers.py#L671)),
which re-entered polars for the per-timeframe aggregation (the `POLARS AGGREGATED:` log lines). Four buffer allocations
per instrument. On the 7-day backfill VM (32 GB), even after wiring the per-shard cleanup hook
(orchestration_service.py:132+, MDPS@dcd7416), RSS held at 25.1 GB per-day floor — arenas don't reclaim from
`gc.collect()`. The service-side fix (pick pure Polars end-to-end) lives in the architectural audit plan Phase 2.

### Decision evidence — MDPS engine benchmark 2026-05-28

A 4-path benchmark on 9 real BINANCE-FUTURES perp trades parquets locked the engine pick for MDPS as **pure Polars**.
Polars 1.40.1 vs pandas 3.0.3 + pyarrow 24.0.0 + Python 3.13.9, each path in its own subprocess, 9 instruments processed
in single process per path so cross-instrument arena retention is measurable. Full doc:
[`plans/audit/results/mdps_engine_benchmark_findings_2026_05_28.md`](../../plans/audit/results/mdps_engine_benchmark_findings_2026_05_28.md);
raw code + JSON:
[`plans/audit/results/benchmarks/mdps_engine_comparison_2026_05_28/`](../../plans/audit/results/benchmarks/mdps_engine_comparison_2026_05_28/).

| Path                                      | Total wall | Mean RSS / instr | Final RSS retention |
| ----------------------------------------- | ---------- | ---------------- | ------------------- |
| **A — pure polars `scan_parquet` (lazy)** | **0.5 s**  | **344 MB**       | **318 MB**          |
| B — pandas + pyarrow dtype_backend        | 2.6 s      | 1185 MB          | 1570 MB             |
| C — current MDPS (Polars→Pandas→Polars)   | 1.4 s      | 1861 MB          | 2471 MB             |
| D — polars `read_parquet` eager           | 0.3 s      | 625 MB           | 801 MB              |

Pure-Polars beat the current shape 3× on wall, 5× on peak per instrument, 7.8× on cumulative retention. Pandas+ PyArrow
was 1.9× _slower_ than the current mixed shape — so "use pandas to fix arena retention" is also a wall-clock regression.
Both polars and pandas+pyarrow have unresolved memory leaks at the parquet-read boundary
([polars#22871](https://github.com/pola-rs/polars/issues/22871),
[polars#23109](https://github.com/pola-rs/polars/issues/23109),
[pandas#59969](https://github.com/pandas-dev/pandas/issues/59969),
[arrow#44472](https://github.com/apache/arrow/issues/44472)) — the workaround is subprocess-per-batch, which composes
with the Layer 3 execution-model decision rather than competing with it.

**Lock-in**: services with the MDPS pipeline shape (read parquet → aggregate per timeframe → write parquet, in a
long-running multi-shard VM) MUST pick pure Polars. Pandas + PyArrow is reserved for I/O-only services where no
aggregation occurs in-process.

## How to migrate an existing service off the mixed-engine pattern

1. **Inventory every parquet read/write callsite.** Tabulate `(file:line, engine, why this engine was chosen)`. The
   `why` column often surfaces accidental drift — "we used polars here because the previous developer used polars above
   and they used polars because of someone earlier".
2. **Pick the target engine per the decision tree above.** Document the choice in the service's `README.md` and in a
   plan checkbox.
3. **Migrate one function at a time, bottom-up.** Start at the lowest-level I/O functions (`_read_tick_data`,
   `_write_candle`); make them return native types in the chosen engine. Then update each caller to consume that type.
4. **Add a CI check** that fails if both `import polars` and `import pandas` appear in the same module after migration.
   The fail message should cite this codex doc.
5. **Land the change in one PR per module.** Mixed-engine cleanup is mechanical but error-prone — small PRs let
   reviewers catch the subtle behavioral differences (NaN handling, timezone defaults, group_by-vs-groupby semantics).

## Composes with

- [`service-orchestration-patterns.md`](service-orchestration-patterns.md) § 15 "Batch Service Lifecycle: Setup, Work,
  Cleanup" — the per-shard cleanup hook handles Python-level state; single-engine discipline handles C-extension arena
  state. Both are required for stable multi-shard RSS.
- [`vm-tarball-deployment.md`](../05-infrastructure/vm-tarball-deployment.md) § "Per-shard cleanup discipline for
  multi-shard VMs" — the VM-lifecycle side of the same rule.
- [`cli-convention.md`](cli-convention.md) § "Instrument Identity and CLI Granularity" — single-shard drilldown runs
  must still exercise the chosen engine end-to-end; conversion churn is a multi-shard problem but a single-shard
  drilldown is the cleanest test bed for measuring per-shard arena footprint.
- [`dependency-management.md`](dependency-management.md) — both `polars>=1.0.0` and `pandas>=2.2.3,<3.0.0` remain in the
  workspace dep set; this rule is about which to USE in a given service, not which to declare as a dep.
