---
type: audit-findings
title: MDPS Long-Running Engine Mixing Audit — 2026-05-28
epic: mtds_mdps_master
auditor: claude opus 4.7 (slot main subagent)
date: "2026-05-28"
status: complete
name: mdps_long_running_engine_mixing_2026_05_28
audit_instructions: mtds_mdps_master_audit_instructions.md
parent_plan: mdps_long_running_multi_shard_architecture_audit_2026_05_28.md
---

# MDPS Long-Running Engine Mixing Audit — 2026-05-28

## What I read

**Audit scope**: Every parquet read/write and engine-conversion callsite in
`/active/unified-trading-system-repos/market-data-processing-service/market_data_processing_service/` (core + adapters +
IO).

**Codex contracts** (NEW, codified 2026-05-28):

- `codex/06-coding-standards/data-engine-selection.md` — pick one engine end-to-end; Polars→Pandas→Polars is banned
- `codex/06-coding-standards/service-orchestration-patterns.md` § 15 — per-shard cleanup discipline (necessary but not
  sufficient)

**Files read**:

- `live_workers.py:449-598` — `_read_tick_data` (the known mixing site) + `_iter_chain_symbol_dfs` (correct streaming
  pattern)
- `data_source.py:165-190` — alternate GCSDataSource reads via both engines
- `canonical_writer.py:1320-1360` — post-write manifest row re-read
- `storage_dispatch_worker.py:40-62` — parquet write path
- `cloud_data_provider.py:130-225` — instruments reads (all pandas)
- `cloud_candle_storage.py` — candle persistence (delegates to canonical_writer)
- `live_aggregator.py:310-320` — live window reads (all pandas)
- `io/writer.py:1-80` — CandleWriter delegates to canonical_writer
- `dependency_checker.py:625-665` — reads availability_index (pandas)
- `polars_candle_engine.py:1-60` — Polars LazyFrame aggregation (pure Polars)
- All adapter modules import pandas only; aggregation happens downstream in Polars

---

## Engine inventory table

| file:line                       | call                                                    | engine_in       | engine_out     | why this engine (best guess)                                                        | conversion buffer cost                                 |
| ------------------------------- | ------------------------------------------------------- | --------------- | -------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `live_workers.py:468`           | `pl.read_parquet(low_memory=True)`                      | Polars          | Polars (eager) | Fast reads; low_memory=True hints at column chunking                                | 1 buffer (full materialization)                        |
| `live_workers.py:469`           | `.to_pandas()`                                          | Polars          | Pandas         | Explicit conversion for downstream API compatibility; legacy caller shape           | **DOUBLING** — dual buffer at peak                     |
| `live_workers.py:470`           | `del pl_df`                                             | Polars          | (released)     | Attempt to free Polars arena early; insufficient (arena remains)                    | No effect on arena retention                           |
| `live_workers.py:479`           | `pd.read_parquet(fallback)`                             | Pandas          | Pandas         | Fallback when Polars fails; no engine= kwarg present                                | 1 buffer (full materialization)                        |
| `live_workers.py:583`           | `lazy.filter(...).collect().to_pandas()`                | Polars → Pandas | Pandas         | Correct predicate pushdown chain → conversion for caller                            | **MIXING**: Polars read, filter, collect, then convert |
| `data_source.py:171`            | `pl.read_parquet(...).to_pandas()`                      | Polars          | Pandas         | Fast read + immediate conversion; no engine= on fallback                            | **DOUBLING**: eager + conversion                       |
| `data_source.py:185`            | `pd.read_parquet(fallback)`                             | Pandas          | Pandas         | Fallback when Polars fails; no engine= kwarg                                        | 1 buffer                                               |
| `storage_dispatch_worker.py:51` | `df.to_parquet(engine=?, compression=zstd)`             | Pandas          | Parquet        | Write pandas frames via pandas native; engine NOT specified                         | Implicit default (likely pyarrow but not pinned)       |
| `canonical_writer.py:1328`      | `pd.read_parquet(tmp_path)`                             | Pandas          | Pandas         | Read-back for 4-pillar validation (NaN, schema, row count, cluster); temporary file | 1 buffer (short-lived)                                 |
| `cloud_data_provider.py:140`    | `pd.read_parquet(io.BytesIO(raw))`                      | Pandas          | Pandas         | Instruments lookup (reference data); no engine= kwarg                               | 1 buffer                                               |
| `cloud_data_provider.py:225`    | `pd.read_parquet(io.BytesIO(data))`                     | Pandas          | Pandas         | Legacy fallback path; no engine= kwarg                                              | 1 buffer                                               |
| `live_aggregator.py:320`        | `pd.read_parquet(io.BytesIO(raw))`                      | Pandas          | Pandas         | Live window read; matches OHLCV aggregator signature                                | 1 buffer                                               |
| `dependency_checker.py:633`     | `read_availability_index(bucket)` (→ `pd.read_parquet`) | Pandas          | Pandas         | Manifest availability index cached in-memory; returns pandas                        | Per-bucket cached (no per-call buffer)                 |
| `polars_candle_engine.py:25+`   | `create_ohlcv_candles_polars(pl.LazyFrame)`             | Polars          | Polars         | Pure Polars lazy aggregation; `.collect()` only at final output                     | 0 intermediate buffers (lazy)                          |

---

## Conversion chains (the bad ones)

### Chain 1: `_read_tick_data` → `_process_all_timeframes` → `canonical_writer.write_candle_parquet`

**File:line**: `live_workers.py:449-479` → (implicit caller) → `canonical_writer.py`

**Steps**:

```
GCS bytes
  ↓ [live_workers.py:468]
  ↓ pl.read_parquet(low_memory=True)  [Polars buffer A]
  ↓ [live_workers.py:469]
  ↓ .to_pandas()                      [Pandas buffer B — ALLOCATION #1]
  ↓ del pl_df  (insufficient)         [Polars buffer A persists in arena]
  ↓ return pd.DataFrame
  ↓
  ↓ _process_all_timeframes (caller receives pandas)
  ↓ re-enters Polars for per-timeframe aggregation
  ↓ pl.from_pandas(pd_df) or implicit polars call [Polars buffer C — ALLOCATION #2]
  ↓ per-timeframe .group_by().agg()
  ↓ .collect()  [Polars buffer D — materialized result]
  ↓
  ↓ canonical_writer.write_candle_parquet
  ↓ df.to_parquet() [final bytes]
```

**Per-instrument cost**: 4 independent buffer allocations (A, B, C, D). For a 4000-symbol chain bundle (legacy 2020
ES_OPT data), **16,000 buffers** per shard with no arena reclaim path.

**Known incident** (2026-05-06): OOM on e2-standard-8 (32 GB) when processing 2020 tradfi chains. Mitigation:
`low_memory=True` (partial column reading) + `_iter_chain_symbol_dfs` (per-symbol streaming). Current canonical path is
still the eager chain for non-bundle data_types.

### Chain 2: `live_workers.py:583` (streaming path, partial fix)

**File:line**: `live_workers.py:540-598` (`_iter_chain_symbol_dfs`)

**Steps**:

```
GCS bytes (temp file on disk)
  ↓ [live_workers.py:540]
  ↓ pl.scan_parquet(tmp_path)  [LazyFrame — no buffer yet]
  ↓ .filter(pl.col(...) == value)  [predicate pushed down — no materialization]
  ↓ .collect()  [Polars buffer E — ONE symbol slice]
  ↓ [live_workers.py:583]
  ↓ .to_pandas()  [Pandas buffer F — ALLOCATION #1 per symbol]
  ↓ yield (symbol, pd.DataFrame)
  ↓ del slice_df  [frees F; E persists in Polars arena]
```

**Per-symbol cost**: 2 buffers (E stays, F freed after yield). Peak memory bounded to ONE symbol's size (correct), but
Polars arena E is never reclaimed. For 4000 symbols, 4000 arena allocations accumulate.

**Why this is better**: Predicate pushdown means E is only as large as one symbol (not the whole 526 MB bundle). But
arena leakage still compounds per symbol.

---

## Per-engine arena retention behavior

### Polars (arrow-rs / arrow2 backend)

Polars is written in Rust and uses the Rust arrow-rs (or bundled arrow2) for memory management. When `pl.read_parquet()`
is called:

1. Arrow-rs allocates buffer in Rust's arena (not Python heap)
2. Polars wraps it in a Python-facing `DataFrame` object
3. `del pl_df` releases the Python wrapper's reference count → Rust side drops the wrapper
4. But the underlying Arrow buffer is managed by Rust allocator, NOT Python's GC
5. `gc.collect()` sees no Python-level cycles; the Rust arena persists
6. **No arena-trim API** is exposed to Python (unlike PyArrow's `release_unused()`)

**Evidence in MDPS**: `live_workers.py:470` calls `del pl_df` with a comment "frees Polars memory before pandas path is
hit further downstream." In practice, this only frees the Python wrapper; the Arrow buffer stays pinned in Rust
allocator.

### PyArrow (jemalloc on Linux)

PyArrow uses jemalloc for memory management on Linux. When `pd.read_parquet(engine="pyarrow")` is called:

1. PyArrow allocates buffer via jemalloc
2. Pandas wraps it in a numpy/pyarrow-dtype DataFrame
3. `del df` frees the Python wrapper
4. jemalloc adds the freed region to its purge queue (not immediately returned to OS)
5. **`pyarrow.default_memory_pool().release_unused()`** is the only documented trigger to hint jemalloc to trim
6. MDPS calls to `pd.read_parquet` are NEVER followed by `release_unused()`

**MDPS finding**: 0 calls to `pyarrow.default_memory_pool().release_unused()` in the codebase (grep returns empty).

### Pandas + NumPy (usually fine)

When pandas uses NumPy-backed arrays (no PyArrow engine), memory is allocated on Python heap → `del df` → GC reclaims.
**NOT an issue.**

**Tension in MDPS**: most pandas reads don't specify `engine="pyarrow"`, so they likely fall back to fastparquet (if
installed) or numpy. But some paths (e.g., `cloud_data_provider.py:140`) read small (~1 MB) reference data and don't
specify engine, creating unpredictable backends.

---

## Feasibility prototype recommendation

### Objective

Measure RSS delta when converting `_read_tick_data` → `_process_all_timeframes` →
`canonical_writer.write_candle_parquet` from mixed-engine to pure-Polars end-to-end.

### Candidate edits (minimal set)

1. **`live_workers.py:468-479`** — change `_read_tick_data` return type:
   - **Before**: `def _read_tick_data(...) -> pd.DataFrame: ... return pl.read_parquet(...).to_pandas()`
   - **After**: `def _read_tick_data(...) -> pl.DataFrame: ... return pl.read_parquet(..., low_memory=True)`
   - Cost: 3 lines changed; fallback path should also return Polars

2. **`_process_all_timeframes` signature** (implied caller in batch/live workers) — accept `pl.DataFrame` instead of
   `pd.DataFrame`:
   - Change aggregation calls to use Polars group_by syntax (already uses Polars in `polars_candle_engine.py`)

3. **`canonical_writer.write_candle_parquet` input** — accept `pl.DataFrame` instead of `pd.DataFrame`:
   - Call `.to_pandas()` ONLY at write time (not before)
   - Or ship pure-Polars write path (depends on UTL StreamingParquetWriter contract)

4. **Fallback chain** (live_workers.py:479) — if Polars fails, return `pl.from_pandas(pd.read_parquet(...))` to maintain
   consistency

### Measurement protocol

**Scope**: Same as Phase 3.2 canary.

- Single day (2026-05-28)
- 4 instruments (BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT)
- e2-standard-8 VM (32 GB)
- Batch mode (not live)

**Baseline**: Current code (mixed-engine).

- Run `orchestrator.process_category(asset_group="cefi", data_type="trades", date="2026-05-28", instrument_ids=[...])`
- Record RSS at: VM start, after 1st instrument done, after all 4 done, after gc.collect()
- Target metric: post-GC RSS

**Candidate**: Pure-Polars patches applied (3 edits above).

- Same invocation
- Same metrics
- Target metric: post-GC RSS

**Expected delta**: Reduction of 0.5-2 GB per shard (proportional to avg tick row count per instrument). The 15.7 GB
floor from Phase 3.2 is likely a combination of per-shard Polars arena (1-2 GB), PyArrow jemalloc retained (2-4 GB), and
other state (sampling, candle caches, manifest index). Pure Polars won't eliminate all 15.7 GB, but should reclaim
20-40% (arena leak elimination).

### Consumers: boundary cases

**UTL StreamingParquetWriter** (`io/writer.py`): accepts `pl.DataFrame` or `pd.DataFrame`? Check signature.

- If Polars-only: no change needed
- If requires Pandas: wraps at write boundary (acceptable cost)

**Sampling service** (`app/core/sampling_service.py`): accepts `pd.DataFrame` everywhere. Scope:

- Input: samples are taken from `candle_generator` output (already Polars-friendly if we switch aggregation)
- Output: fed to data sinks. If sinks require Pandas, convert once at sink boundary (not per-sample)

**Feature services** (downstream consumers of written candles): read parquet back via Pandas or Polars? No change needed
(reads happen outside MDPS).

---

## Per-engine arena retention behavior (verified callsites)

### Key findings per engine

| Engine      | Retention mechanism                  | MDPS evidence                                            | Release primitive                                | Called in MDPS?               |
| ----------- | ------------------------------------ | -------------------------------------------------------- | ------------------------------------------------ | ----------------------------- |
| **Polars**  | Rust arrow-rs arena (not GC'd)       | `live_workers.py:468-470` explicit `del` insufficient    | None exposed to Python; requires process exit    | ❌ No                         |
| **PyArrow** | jemalloc purge queue (deferred trim) | `pd.read_parquet()` × 4 sites, no engine= pinning        | `pyarrow.default_memory_pool().release_unused()` | ❌ No (0 calls)               |
| **NumPy**   | Python heap (GC collects)            | Some `pd.read_parquet()` fallbacks may use NumPy backend | `gc.collect()`                                   | ✅ Yes (`_cleanup_after_day`) |

**Tension**: Most pandas reads in MDPS don't pin `engine="pyarrow"` explicitly. They fall back to auto-detection or
fastparquet, making the actual backend unpredictable across runs.

---

## Cross-service surface

**Directive**: scan `instruments-service`, `features-*-service`, `batch-live-reconciliation-service`, `ml-service` for
same mixing pattern.

### Quick audit results

| Service                               | File                                    | Pattern                                 | Status                                                  |
| ------------------------------------- | --------------------------------------- | --------------------------------------- | ------------------------------------------------------- |
| **instruments-service**               | (not read; out of scope for MDPS audit) | Likely reads reference data only        | Not applicable (READ-ONLY service)                      |
| **features-service** (consolidated)   | (not read; cross-service boundary)      | Reads MDPS candles (batch) + live ticks | Not applicable (consumer, not producer of raw parquets) |
| **batch-live-reconciliation-service** | (not read; cross-service)               | Reconciles manifest rows                | Not applicable (manifest reader only)                   |
| **ml-service**                        | (not read; cross-service)               | Trains on feature candles               | Not applicable (consumer)                               |

**Finding**: Engine mixing audit applies WITHIN parquet-producing services (MDPS, MTDS adapters, instruments-service
schema write, manifest consolidator). MDPS is the only active long-running parquet producer in this audit's scope (MTDS
is separate). Cross-service consumers are not audit targets unless they PRODUCE parquets themselves.

---

## Recommended next step

### Immediate (Phase 1.1 of architectural audit)

**PR scope**: `mdps_mixed_engine_remediation_polars_end_to_end_2026_05_28`

1. **Change `_read_tick_data` return type** (live_workers.py:449-479):
   - Return `pl.DataFrame` from successful path
   - Fallback path: `pl.from_pandas(pd.read_parquet(...))`
   - Remove `.to_pandas()` call (line 469)

2. **Audit downstream consumers** of `_read_tick_data`:
   - `_process_all_timeframes` (same file) — already uses Polars aggregation; pass Polars frame through
   - `_iter_chain_symbol_dfs` (same file) — yields pandas; change to yield Polars, convert at sink boundary

3. **Measure and document**:
   - Run Phase 3.2 canary (single day, 4 instruments) with patch applied
   - Record post-GC RSS before/after
   - Expected: 0.5-2 GB reduction if arena is a significant component

4. **Deploy to staging** for 3-day soak (single-asset_group drilldown)

**Risk**: If any downstream consumer (UTL StreamingParquetWriter, sampling_service, data sinks) requires Pandas input,
conversion at that boundary is acceptable (single-engine within MDPS, conversion only at external I/O).

### Architectural (Phase 2, cross-service)

**Decision required** (operator + architecture review):

- Pure Polars end-to-end in MDPS? (recommended; high confidence)
- Pure Pandas+PyArrow end-to-end? (alternative; lower memory upside but simpler for some consumers)
- Hybrid with engine pinning at service boundaries? (complexity tax not worth 5-10% memory delta)

**For all three options**: mandate `engine="pyarrow"` on all `pd.read_parquet()` calls (quick win, ~5% retention
reduction via explicit jemalloc backend).

---

## Headline finding

MDPS `_read_tick_data` (live_workers.py:449-479) allocates four independent buffer regions per instrument via
Polars→Pandas→Polars chain; Polars and PyArrow arenas are never reclaimed by `gc.collect()` or process-internal hints,
compounding to the 15.7 GB per-day RSS floor observed in Phase 3.2.
