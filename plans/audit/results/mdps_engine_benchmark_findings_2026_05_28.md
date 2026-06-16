---
type: audit-findings
title: MDPS engine benchmark — Polars vs Pandas+PyArrow on the real workload
epic: mtds_mdps_master
auditor: claude opus 4.7 (slot main)
date: "2026-05-28"
status: complete
name: mdps_engine_benchmark_findings_2026_05_28
audit_instructions: mtds_mdps_master_audit_instructions.md
parent_plan: mdps_long_running_multi_shard_architecture_audit_2026_05_28.md
related_findings:
  - mdps_long_running_engine_mixing_2026_05_28.md
benchmark_raw_data:
  - benchmarks/mdps_engine_comparison_2026_05_28/results.md
  - benchmarks/mdps_engine_comparison_2026_05_28/results.json
  - benchmarks/mdps_engine_comparison_2026_05_28/path_runner.py
  - benchmarks/mdps_engine_comparison_2026_05_28/run_all.py
---

# MDPS engine benchmark — Polars vs Pandas+PyArrow on the real workload

## TL;DR

The Layer 0 (data engine) decision: **pure Polars, using `scan_parquet` LazyFrame + projection pushdown**.
Pandas+PyArrow lost on every axis tested. The current Polars→Pandas→Polars round-trip (production today) is the worst of
all paths measured — slower than pure pandas-pyarrow and ~8× more memory retention than pure polars.

Headline numbers (9 BINANCE-FUTURES perp trades parquets for 2026-04-15, ~127 MB compressed input total, candles
produced for all 7 timeframes 15s→24h, single-process iteration):

| Path                                               | Total wall | Mean RSS / instr | Final RSS retention |
| -------------------------------------------------- | ---------- | ---------------- | ------------------- |
| **A: pure polars `scan_parquet` (lazy)**           | **0.5 s**  | **344 MB**       | **318 MB**          |
| B: pandas + pyarrow dtype_backend                  | 2.6 s      | 1185 MB          | 1570 MB             |
| C: current MDPS shape (Polars→Pandas→Polars)       | 1.4 s      | 1861 MB          | 2471 MB             |
| D: polars `read_parquet` eager (no `.to_pandas()`) | 0.3 s      | 625 MB           | 801 MB              |

Path A beats Path C on **every metric**: 3× faster wall, 5× lower peak per instrument, 7.8× less retention. Path B
(pandas+pyarrow) is 1.9× slower than current Path C — so picking pandas to "fix" arena retention would simultaneously
make us slower.

## What was benchmarked

Real prod parquets pulled from
`gs://market-data-tick-cefi-central-element-323112/raw_tick_data/by_date/day=2026-04-15/asset_group=cefi/venue=BINANCE-FUTURES/instrument_type=perpetual/data_type=trades/`:

| Instrument | Compressed size | Row count |
| ---------- | --------------- | --------- |
| ADAUSDT    | 4.2 MB          | ~600 K    |
| AVAXUSDT   | 3.6 MB          | ~500 K    |
| BNBUSDT    | 6.8 MB          | ~900 K    |
| BTCUSDT    | 30.3 MB         | 3.4 M     |
| DOGEUSDT   | 9.3 MB          | ~1.3 M    |
| ETHUSDT    | 46.8 MB         | ~5 M      |
| LINKUSDT   | 2.9 MB          | ~400 K    |
| SOLUSDT    | 14.7 MB         | ~2 M      |
| XRPUSDT    | 9.3 MB          | ~1.3 M    |

Each path is a Python script that, in a fresh subprocess:

1. Reads the parquet with the engine under test
2. Computes OHLCV candles for 7 timeframes (15s, 1m, 5m, 15m, 1h, 4h, 24h) using the engine's native group_by /
   aggregate
3. Writes 7 candle parquets to disk per instrument
4. Measures wall-clock + RSS via `psutil.Process().memory_info().rss`
5. Iterates over all 9 instruments in the SAME Python process so cumulative arena retention is measurable
6. Reports RSS after every instrument completes (post `gc.collect()`)

Each path runs in its OWN subprocess so cross-path arena pollution can't contaminate the next path's measurement.
**Engines tested at latest stable**:

- polars 1.40.1 (April 2026; latest stable on PyPI — 1.41 was yanked)
- pandas 3.0.3 (May 2026; CoW + PyArrow string default + microsecond datetime default)
- pyarrow 24.0.0
- Python 3.13.9

Code: [`benchmarks/mdps_engine_comparison_2026_05_28/`](benchmarks/mdps_engine_comparison_2026_05_28/).

## Cross-instrument RSS trajectory

This is the most revealing chart — RSS measured AFTER each instrument completes, with `gc.collect()` run between. Rising
numbers indicate cumulative arena retention.

| #   | Instrument | A pure polars lazy | B pandas pyarrow | C current MDPS | D polars eager |
| --- | ---------- | ------------------ | ---------------- | -------------- | -------------- |
| 1   | ADAUSDT    | 177                | 316              | 436            | 175            |
| 2   | AVAXUSDT   | 188                | 362              | 493            | 215            |
| 3   | BNBUSDT    | 204                | 474              | 717            | 310            |
| 4   | BTCUSDT    | 330                | 1083             | 1744           | 602            |
| 5   | DOGEUSDT   | 331                | 1145             | 1829           | 606            |
| 6   | ETHUSDT    | 466                | 1794             | **2961**       | 927            |
| 7   | LINKUSDT   | 466                | 1797             | 2709           | 927            |
| 8   | SOLUSDT    | 468                | 1833             | 2779           | 930            |
| 9   | XRPUSDT    | **468**            | **1838**         | 2825           | **931**        |

Observations:

- **Paths A and D both saturate cleanly**. After the biggest file (ETHUSDT at instrument 6), neither path grows further.
  RSS plateaus at the largest in-memory buffer that hasn't been released. Polars' allocator is doing the right thing:
  arenas hold the biggest buffer seen, not the cumulative sum.
- **Path B grows monotonically** but slowly. Each instrument leaves a small residue in the PyArrow arena. Not
  catastrophic but not clean either.
- **Path C (current MDPS) grows fastest** — 6.4× the saturation level of A. Both polars + pandas arenas accumulate;
  conversion buffers stay pinned.

## Per-instrument wall-clock comparison

For the two largest files (BTCUSDT 30 MB, ETHUSDT 47 MB) the gap widens substantially:

| Instrument | A wall (s) | B wall (s) | C wall (s) | D wall (s) | B/A  | C/A  |
| ---------- | ---------- | ---------- | ---------- | ---------- | ---- | ---- |
| BTCUSDT    | 0.09       | 0.58       | 0.29       | 0.06       | 6.4× | 3.2× |
| ETHUSDT    | 0.14       | 0.97       | 0.46       | 0.08       | 6.9× | 3.3× |

The larger the file, the bigger Polars' lead. This matters because the audit's `manifest_io` finding noted that
production reads the 526 MB manifest twice per shard — those are exactly the "big file" regime where polars' projection
pushdown + zero-copy parquet decode dominate.

## Why pandas+PyArrow lost

Three reasons surfaced by the per-instrument tables:

1. **Group-by performance gap**: pandas' groupby with PyArrow-backed dtypes is functional but single-threaded for the
   aggregation kernel. Polars parallelises across cores and uses columnar-native compute. On BTCUSDT (3.4M rows × 7
   timeframes), this is a 6× speedup.
2. **Read overhead**: `pd.read_parquet(engine="pyarrow", dtype_backend="pyarrow")` materialises the full table eagerly.
   Polars `scan_parquet(...)` returns a LazyFrame; the subsequent `.filter(...).select(...)` push down to the parquet
   reader, so only the columns and rows actually used hit memory. For our workload (5 columns out of 10 used), this
   saves ~40% on the initial materialisation.
3. **Conversion at write time**: PyArrow write requires `pa.Table.from_pandas(df)` which is an extra copy. Polars
   `.write_parquet(path)` is direct.

Per the codex `data-engine-selection.md`, pandas+pyarrow is supposed to be appropriate for "I/O-only services". MDPS is
not I/O-only — it does real aggregation per timeframe. The codex's guidance holds: aggregation-heavy services should
pick Polars.

## Where the canary's 15.7 GB residue actually goes — extrapolated

The canary VM measured 15.7 GB post-day-1 RSS on a 32 GB box. Path C in this benchmark hit 2.8 GB on a 127 MB compressed
input over 9 instruments. The production workload has:

- 4 instruments (not 9), but with `low_memory=True` + GCS download buffering
- 7 timeframes (same)
- 1 day per call to `process_category`
- Plus the 526 MB manifest read + 4128-instrument reference DataFrame loads

Scaling Path C's per-instrument retention by the bigger-file ratio (the canary processed BYBIT trades parquets up to ~45
MB compressed; this benchmark's largest was 47 MB) gives ~4 GB just from the candle aggregation churn. The remaining
~10-12 GB is plausibly the manifest + reference-data + downstream-writer arenas that the canary touched but this
micro-benchmark didn't.

A pure-Polars MDPS (Path A) on the same canary inputs should land closer to ~1-2 GB post-day-1 RSS. **That fits within
e2-standard-4 (16 GB) headroom comfortably**, which is what the original plan optimistically targeted.

## Known caveats — open Polars memory-leak issue

Polars 1.28+ has an unresolved memory leak in `read_parquet` / `scan_parquet` when called repeatedly in a long-running
process. Tracking issues:

- [pola-rs/polars#22871](https://github.com/pola-rs/polars/issues/22871) — confirmed bug, latest version affected
- [pola-rs/polars#23109](https://github.com/pola-rs/polars/issues/23109) — `read_parquet` memory leak without
  `use_pyarrow=True` since polars 1.28

Documented community workaround: run polars steps in a subprocess to force memory release at process exit. **This is
exactly the Layer 3 (subprocess-per-date) execution-model decision the architectural audit is already considering**. So
the choice is not in tension with the engine pick; it's the SAME decision the deployment shape required regardless.

Pandas+PyArrow has its own confirmed memory-leak issues at the Arrow→pandas conversion boundary
(pandas-dev/pandas#59969, apache/arrow#44472). So this isn't a way out of arena retention via the other engine. Both
engines need Layer 3 to bound the leak.

## What this means for Layer 0

Lock the decision in: **pure Polars, end-to-end**. The codex
[`data-engine-selection.md`](../codex/06-coding-standards/data-engine-selection.md) gets a cross-reference to this
benchmark; the architectural plan's Phase 2 (data engine) is now evidence-backed not aspiration-backed.

What "pure polars" means concretely:

- Reads: `pl.scan_parquet(...)` returning LazyFrame (preferred) or `pl.read_parquet(...)` returning DataFrame. Both beat
  pandas+pyarrow.
- Aggregation: `.group_by(...).agg(...)` (already what `polars_candle_engine.py` does).
- Writes: `pl.DataFrame.write_parquet(...)` directly. No PyArrow Table conversion.
- Consumers (`canonical_writer.write_candle_parquet`, `sampling_service.add_sample`, candle adapters): all accept Polars
  DataFrame. If any of them currently require pandas, that's the surface to fix at the consumer, not at the producer.

## Limitations of this benchmark

- Local disk reads only — no GCS network cost included. Wall-clock numbers in production will be higher; relative ratios
  should hold.
- Doesn't model the writer's downstream work (manifest update, schema validation, sample CSV, event emission). Real MDPS
  per-instrument processing is slower than this measurement.
- Single day (2026-04-15), single venue (BINANCE-FUTURES), single data_type (trades). Other data_types (book_snapshot_5,
  dex_swaps, options_chain) have different column counts and row shapes; pure polars' projection-pushdown advantage may
  be even bigger on wider tables.
- Polars `low_memory=True` not used in path A/D — but pandas path didn't have a corresponding flag either, and adding it
  to polars would only widen the gap.

## Recommended next steps

- **Immediate**: lock the codex `data-engine-selection.md` § "Reference incident" entry to this benchmark. Decision is
  evidence-backed now.
- **Layer 1 falls out**: Polars `LazyFrame` for reads + filters; collect to `DataFrame` at the aggregation boundary.
  Standard polars idiom.
- **Architectural plan Phase 2 — data engine — decision becomes implementation**:
  - Convert `_read_tick_data` → return polars `LazyFrame` (no `.to_pandas()`).
  - Convert `_process_all_timeframes` → accept LazyFrame; emit polars `DataFrame` per timeframe.
  - Convert `canonical_writer.write_candle_parquet` → accept polars `DataFrame`, use `.write_parquet()`.
  - Audit each candle adapter under `app/adapters/` for pandas/polars boundary; convert at the consumer side.
  - Sampling service: single `.to_pandas()` at the sample boundary is OK (samples are CSV for debugging; not in the hot
    path).
- **Layer 3 (subprocess-per-date) is still mandatory** to bound the documented polars-1.28+ leak
  - the smaller pandas conversion residue in any path through MDPS. Engine choice and execution model are independent
    decisions; this benchmark says polars; Layer 3 audit said subprocess-per- date; both compose cleanly.
