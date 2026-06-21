---
name: mdps_pure_polars_migration
title: "MDPS pure-Polars migration — staged engine cutover (2026-05-28)"
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
status: active
model_tier: opus-required
thinking_tier: high
priority: P1
created: 2026-05-28
estimate_class: refactor
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 2.4
related:
  - mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md # tactical fixes already shipped (E1-E3)
  - mdps_long_running_multi_shard_architecture_audit_2026_05_28.md # architectural plan; this plan IS its Phase 2 implementation
codex_ssots:
  - codex/06-coding-standards/data-engine-selection.md # NOW LOCKED to pure-Polars for MDPS shape (2026-05-28)
  - codex/06-coding-standards/service-orchestration-patterns.md # § 15 cleanup discipline
audit_findings_grounding:
  - plans/audit/results/mdps_engine_benchmark_findings_2026_05_28.md # benchmark evidence
  - plans/audit/results/mdps_long_running_engine_mixing_2026_05_28.md # static-trace audit
  - plans/audit/results/mdps_long_running_state_inventory_2026_05_28.md # state inventory
locked_by: live-defi-rollout
locked_since: 2026-05-28
---

# MDPS pure-Polars migration — staged engine cutover

> **✅ ARCHIVED 2026-06-21 — pure-Polars engine shipped + codex-LOCKED (data-engine-selection.md). Deferred adapter-protocol pandas→polars + Phase-6 emission-check → mdps_adapter_protocol_pandas_to_polars_2026_06_21. [unlock-plan]**

## Goal

Migrate MDPS to pure-Polars end-to-end per the Layer 0 decision locked in `data-engine-selection.md` 2026-05-28.
Eliminate the Polars→Pandas→Polars→Pandas conversion chain that the benchmark proved owns the majority of the 15.7 GB
per-day RSS floor observed on the Phase 3.2 retry canary VM.

**Success number**: rerun the
[`benchmarks/mdps_engine_comparison_2026_05_28/`](../audit/results/benchmarks/mdps_engine_comparison_2026_05_28/) suite
against the migrated MDPS code; per-instrument peak RSS should drop from ~1.8 GB (Path C today) to ~344 MB (Path A
target). Cumulative retention across 9 instruments should drop from 2.5 GB to 318 MB. The 15 GB production per-day floor
should drop proportionally — projected ~1-2 GB post-migration based on per-instrument scaling.

## Provenance

This plan exists because the **2026-05-28 MDPS engine benchmark** (locked into codex `data-engine-selection.md` §
"Decision evidence") proved pure-Polars wins decisively on the actual MDPS workload:

| Path                                      | Total wall (9 instruments × 7 TFs) | Mean RSS peak / instr | Final RSS retention |
| ----------------------------------------- | ---------------------------------- | --------------------- | ------------------- |
| **A — pure polars `scan_parquet` (lazy)** | **0.5 s**                          | **344 MB**            | **318 MB**          |
| B — pandas + pyarrow dtype_backend        | 2.6 s                              | 1185 MB               | 1570 MB             |
| C — current MDPS (Polars→Pandas→Polars)   | 1.4 s                              | 1861 MB               | 2471 MB             |
| D — polars `read_parquet` eager           | 0.3 s                              | 625 MB                | 801 MB              |

Versions: polars 1.40.1, pandas 3.0.3, pyarrow 24.0.0, Python 3.13.9. Real prod parquets from the BINANCE-FUTURES
2026-04-15 corpus.

Both polars and pandas+pyarrow have unresolved memory leaks at the parquet-read boundary
([polars#22871](https://github.com/pola-rs/polars/issues/22871),
[polars#23109](https://github.com/pola-rs/polars/issues/23109),
[pandas#59969](https://github.com/pandas-dev/pandas/issues/59969),
[arrow#44472](https://github.com/apache/arrow/issues/44472)). The community workaround for both is subprocess-per-batch,
which is the same Layer 3 execution-model decision the architectural audit is queueing. Engine choice and execution
model compose — they're not in tension.

## Current state inventory (full sweep 2026-05-28)

**Headline numbers from the deeper sweep**: pandas is imported in **48 source files**, polars in **7**. The intersection
(mixed-engine files) is 5. `pd.DataFrame` appears in function signatures across **43 source files**. Pandas-specific
operations (`set_index`, `iloc`, `loc`, `groupby`, `concat`, `MultiIndex`, etc.) appear **170+ times** across the
source. Test files using pandas: **55**.

### KEY DISCOVERY — adapter output is NOT pandas

`BaseCandleAdapter.process_to_candles(...)` returns **`CandleOutput`**, a UAC dataclass with **numpy ndarrays**
([`unified-api-contracts/.../adapter_models.py:81-140`](../../../unified-api-contracts/unified_api_contracts/internal/domain/market_data_processing/adapter_models.py#L81-L140)).
The pandas conversion happens AT THE WORKER via `candle_output.to_dataframe()` at
[`live_workers.py:915, 944`](../../../market-data-processing-service/market_data_processing_service/app/core/live_workers.py#L915).

This means **Stage 3 doesn't touch the 18 adapter implementations** — just adds `CandleOutput.to_polars()` in UAC and
the worker uses it instead of `to_dataframe()`. Massive scope reduction vs the original Stage 3.

### Mixed-engine files

| File                                                                                                                                                              | Role               | Mix today                                                                                                                                                                                                                                                                                                 |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`app/core/live_workers.py`](../../../market-data-processing-service/market_data_processing_service/app/core/live_workers.py)                                     | **THE hot path**   | `_read_tick_data` does `pl.read_parquet` → `.to_pandas()` (line 469). Chain-bundle path does `.collect().to_pandas()` (line 583). Worker calls `candle_output.to_dataframe()` (lines 915, 944) AFTER adapter returns numpy CandleOutput. Pandas mutation `candles_df[col] = mode_val.iloc[0]` (line 100). |
| [`app/core/data_source.py`](../../../market-data-processing-service/market_data_processing_service/app/core/data_source.py)                                       | Read helper        | `pl.read_parquet → .to_pandas()` (line 171) + `pd.read_parquet` fallback (line 185).                                                                                                                                                                                                                      |
| [`app/calculators/fast_candle_aggregation.py`](../../../market-data-processing-service/market_data_processing_service/app/calculators/fast_candle_aggregation.py) | Aggregation rollup | `pl.from_pandas` (line 394) → aggregate → `.to_pandas()` (line 504). Internal round trip. **36 pandas-ops in 835 lines**.                                                                                                                                                                                 |
| [`app/adapters/cefi/trades_adapter.py`](../../../market-data-processing-service/market_data_processing_service/app/adapters/cefi/trades_adapter.py)               | Single adapter     | `pl.from_pandas(tick_data)` (line 229) → aggregates → `.to_pandas().set_index(...)` (line 260). Internal round trip.                                                                                                                                                                                      |
| [`engine/mock_data_provider.py`](../../../market-data-processing-service/market_data_processing_service/engine/mock_data_provider.py)                             | Mock data          | Out of scope for hot-path perf.                                                                                                                                                                                                                                                                           |

### Pandas hotspots (heavy users)

| File                                         | pandas-ops | Lines | Role                                                                                      |
| -------------------------------------------- | ---------- | ----- | ----------------------------------------------------------------------------------------- |
| `app/calculators/timeframe_candles.py`       | 48         | 780   | Per-timeframe candle generation — used by adapters                                        |
| `app/calculators/fast_candle_aggregation.py` | 36         | 835   | 15s → larger TF rollup; called from `_process_all_timeframes`                             |
| `app/core/canonical_writer.py`               | 31         | 2184  | The main batch writer; `pd.read_parquet` at lines 1328, 2121 (cluster validation re-read) |
| `app/core/orchestration_writer.py`           | 10         | 392   | Per-shard write coordination                                                              |

### Pandas read/write callsites

| Callsite                                        | What it reads/writes                                                    |
| ----------------------------------------------- | ----------------------------------------------------------------------- |
| `mock_data_provider.py:139, 143`                | `pd.read_parquet` for mock data                                         |
| `app/adapters/prediction/trades_adapter.py:184` | `pd.read_parquet` inside adapter                                        |
| `app/core/data_source.py:185`                   | `pd.read_parquet` fallback after polars read                            |
| `app/core/live_aggregator.py:320`               | `pd.read_parquet` for live-mode replay                                  |
| `app/core/canonical_writer.py:1328, 2121`       | `pd.read_parquet` for re-reading just-written file (cluster validation) |
| `app/core/cloud_data_provider.py:140, 225`      | `pd.read_parquet` for instruments reference DataFrame load              |
| `app/core/live_workers.py:479`                  | `pd.read_parquet` fallback after polars read                            |
| `app/core/storage_dispatch_worker.py:51`        | `df.to_parquet(buf, index=False, compression="zstd")` — pandas write    |
| `app/core/orchestration_base.py:132`            | `sample_df.to_csv(...)` — CSV sample (debug only)                       |
| `app/core/orchestration_state.py:145`           | `sample_df.to_csv(...)` — CSV sample (debug only; duplicate of above)   |

### Adapter contracts today

`BaseCandleAdapter.process_to_candles(tick_data: pd.DataFrame, ...) -> CandleOutput` at
[`base_adapter.py:93`](../../../market-data-processing-service/market_data_processing_service/app/adapters/base_adapter.py#L93).
Input is pandas; **output is `CandleOutput`** (numpy ndarrays in dataclass — NOT pandas).

The 18 adapter implementations across cefi/defi/sports/prediction/tradfi (counts: 6/5/4/1/3) all take pandas as input
and emit `CandleOutput`. Their **internal** processing may or may not use polars — `cefi/trades_adapter.py` confirmed
does pandas→polars→pandas internally; the other 17 need audit.

### Writer contracts today — split

- `io/writer.py:write_candles(df: pl.DataFrame, ...)` — **already polars** ✓
- `canonical_writer.py:write_candle_parquet(candles_df: pd.DataFrame, ...)` — **still pandas** ✗ (the main batch writer
  that lands processed candles + manifest rows)

### The actual conversion chain today (production hot path)

```
GCS bytes
  → pl.read_parquet(low_memory=True)                [arena #1, polars]
    → .to_pandas() at live_workers.py:469           [arena #2, pandas]
      → pass to _process_all_timeframes
        → adapter.process_to_candles(tick_data=pandas)
          → [adapter internally: maybe pl.from_pandas → group_by → .to_pandas, varies per adapter]
          → return CandleOutput (numpy ndarrays — NOT pandas)
        → candle_output.to_dataframe() at live_workers.py:915, 944  [arena #3, pandas]
          → maybe pandas mutations (live_workers.py:100, candles_df[col] = mode_val.iloc[0])
          → canonical_writer.write_candle_parquet(candles_df=pandas)
            → pa.Table.from_pandas() (UTL writer) [arena #4, pyarrow]
              → GCS bytes
```

4 buffer allocations per (instrument × timeframe) on the OUTER path. Plus 2 more inside any adapter that does internal
polars round trips (like cefi/trades_adapter.py). Benchmark's Path A had 1.

### Test surface

**55 test files** import pandas. Stage 1 will require updating fixtures that construct pandas DataFrames to mock
`_read_tick_data` output — those become polars DataFrames. Estimate ~10-15 test files actually touch the worker read
path; the rest are adapter-internal tests that don't care about the boundary.

## Where this fits in the ground-up architecture

| Layer                   | Decision                                                                 | Status                                                                                     |
| ----------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| **0** — Data engine     | Pure Polars                                                              | ✅ Locked 2026-05-28 (codex + benchmark)                                                   |
| **1** — Data shapes     | `LazyFrame` for reads + filters; `DataFrame` at the aggregation boundary | Falls out of Layer 0; documented here                                                      |
| **2** — State ownership | TBD                                                                      | Discussion after this plan ships                                                           |
| **3** — Execution model | TBD                                                                      | Discussion after this plan ships; subprocess-per-date is the polars-leak workaround anyway |

This plan implements Layers 0 + 1. Layers 2 and 3 are separate plans gated on operator decision.

## Migration strategy — five stages, in order

Each stage is self-contained, independently revertable, ships on `live-defi-rollout`, and the next stage doesn't start
until the current one is verified green. Stage 3 is dramatically smaller than originally feared because `CandleOutput`
already abstracts away pandas at the adapter output boundary.

### Stage 1 — Worker read-side: `_read_tick_data` returns polars (smallest)

**Goal**: collapse the read-side arena pair (#1 polars + #2 pandas after `.to_pandas()`). Single `.to_pandas()` happens
at the `adapter.process_to_candles(...)` call site as a documented boundary conversion.

**Files touched**:

- `app/core/live_workers.py` —
  - `_read_tick_data` → return `pl.DataFrame` (eager; matches benchmark Path D, lower refactor risk than LazyFrame).
  - `_process_all_timeframes` → accept `pl.DataFrame`, do `.to_pandas()` ONCE at the
    `adapter.process_to_candles( tick_data=pl_df.to_pandas(), ...)` call. Document the conversion with a comment
    pointing at this plan.
  - `_iter_chain_symbol_dfs` (already polars-streaming) — return polars; downstream callers convert at adapter boundary.
- `app/core/data_source.py` — `tick_data = pl.read_parquet(buf)` (drop the `.to_pandas()` at line 171). Return polars.
  The `pd.read_parquet` fallback (line 185) stays for now.
- `tests/unit/test_live_workers.py` (if exists; create if not) — update mocks; add regression test asserting
  `_read_tick_data` returns `pl.DataFrame`.
- `tests/unit/test_process_handler*.py` — update any test fixture that simulates `_read_tick_data` output.

**Files NOT touched**: all 18 adapters; `canonical_writer.py`; `fast_candle_aggregation.py`; `timeframe_candles.py`;
adapter base class.

**Why this is safe**: the conversion just moves down one level. Adapter still sees pandas. Per-instrument peak arena
footprint drops because the worker holds polars instead of both polars + pandas simultaneously.

**Expected delta vs current** (per benchmark Path D vs Path C): 4.7× faster wall, 3.4× less retention.

### Stage 2 — Adapter-internal round-trip removal (per-adapter)

**Goal**: for any adapter that does pandas→polars→pandas internally, refactor to use polars internally without the round
trip. Signature unchanged.

**Files touched (per adapter; one PR each)**:

- `app/adapters/cefi/trades_adapter.py` — REFERENCE; confirmed has `pl.from_pandas(tick_data)` (line 229) → group_by →
  `.to_pandas().set_index(...)` (line 260). Refactor.
- Audit each other 17 adapters for the same pattern. Most likely candidates by inspection: `cefi/options_chain`,
  `cefi/futures_chain`, `cefi/derivative` (similar numeric aggregations to trades). Sports/prediction adapters are less
  likely to have polars internally.

**Files NOT touched**: Adapter base class signature (still `pd.DataFrame`); `canonical_writer.py`.

### Stage 3 — Output side: `CandleOutput.to_polars()` + writer polars (REVISED — smaller than originally feared)

**Goal**: collapse the output-side arena (#3 pandas from `to_dataframe()` + #4 pyarrow at writer). `CandleOutput`
abstracts away the engine choice already, so the change is to add a polars emit path.

**Files touched**:

- `unified-api-contracts/.../adapter_models.py` — add `CandleOutput.to_polars() -> pl.DataFrame` method (~20 lines,
  analogous to the existing `to_dataframe()`).
- `market-data-processing-service/.../canonical_writer.py:write_candle_parquet` — accept `pl.DataFrame` instead of
  `pd.DataFrame`; use `.write_parquet()` instead of pandas write. Cluster validation re-read at lines 1328, 2121 can
  stay pandas (small re-read on freshly-written file, debug-path) OR switch to polars (preferred).
- `market-data-processing-service/.../live_workers.py:915, 944` — call `.to_polars()` instead of `.to_dataframe()`;
  remove the `candles_df[col] = mode_val.iloc[0]` mutation at line 100 (or replace with polars equivalent).
- `market-data-processing-service/.../orchestration_writer.py` — accept polars from caller; downstream pass- through to
  canonical_writer.
- `market-data-processing-service/.../storage_dispatch_worker.py:51` — switch `df.to_parquet(...)` to
  `df.write_parquet(...)` (polars).
- Remove the boundary `.to_pandas()` from Stage 1 at `_process_all_timeframes` adapter call (adapter still takes pandas
  — Stage 2/4 territory).

**Files NOT touched in Stage 3**: 18 adapter implementations; adapter base class (input still pandas).

**Why this is safer than originally feared**: the `CandleOutput` numpy abstraction means the worker→writer pipe goes
pandas → polars by adding one new method to UAC + flipping the writer signature. No per-adapter changes.

### Stage 4 — Aggregation calculators (re-audited 2026-05-29)

**Goal**: convert the rollup engines from mixed-engine to pure polars + delete the dead-code chain that the original
Stage 4 framing treated as live.

**Re-audit methodology (2026-05-29 Harsh+slot8)**:

- pandas-op count = lines matching
  `\b(pd\.|\.iloc|\.loc\[|\.iat|\.at\[|\.groupby|\.merge|\.concat|\.apply|\.set_index|\.reset_index|\.assign|\.melt|\.pivot|\.stack|\.unstack|MultiIndex|\.values\b|\.copy\(\)|\.dropna|\.fillna|\.astype|\.rename|\.sort_values|\.sort_index|\.to_dict|\.to_numpy|\.tolist|pd\.api\.types|\.Series|\.DataFrame|\.Timedelta|\.Timestamp)\b`
- reachability = `grep -rn` for every public function across `market_data_processing_service/` and `tests/`, excluding
  the function's own definition file and `app/calculators/__init__.py` re-exports.

#### `app/calculators/fast_candle_aggregation.py` — 835 lines

| Metric                         | Count | Methodology       |
| ------------------------------ | ----- | ----------------- |
| Total lines                    | 835   | `wc -l`           |
| Lines matching `pd.`           | 43    | `grep -cE 'pd\.'` |
| Lines matching `pl.`           | 15    | `grep -cE 'pl\.'` |
| Lines matching pandas-op regex | 50    | broad regex above |

8 public functions; reachability outside the file:

| Function                                   | Line | External callers                                                          | Status   |
| ------------------------------------------ | ---- | ------------------------------------------------------------------------- | -------- |
| `create_continuous_candles_simple_working` | 155  | 0                                                                         | DEAD     |
| `create_candle_from_interval`              | 195  | live_aggregator.py:345                                                    | **LIVE** |
| `create_empty_candle`                      | 281  | 0                                                                         | DEAD     |
| `create_24h_candle_no_lookahead`           | 303  | 0                                                                         | DEAD     |
| `aggregate_from_15s_efficient`             | 513  | live_workers.py:791, 1260 + 3 test files + sampling_service.py:143 (dead) | **LIVE** |
| `should_aggregate_from_15s`                | 655  | 0                                                                         | DEAD     |
| `create_candle_from_interval_fixed`        | 751  | 0                                                                         | DEAD     |
| `create_empty_candle_sophisticated`        | 795  | 0                                                                         | DEAD     |

13 internal `_` helpers; live-vs-dead chain (each helper has exactly one in-file caller):

| Helper                                  | Reached from                                   | Status                                              |
| --------------------------------------- | ---------------------------------------------- | --------------------------------------------------- |
| `_polars_available` (line 36)           | `_use_polars_aggregation:53`                   | LIVE                                                |
| `_use_polars_aggregation` (line 46)     | `aggregate_from_15s_efficient:535`             | LIVE                                                |
| `_parse_timeframe_seconds` (line 56)    | `create_continuous_candles_simple_working:171` | DEAD                                                |
| `_detect_time_column` (line 67)         | `create_continuous_candles_simple_working:172` | DEAD                                                |
| `_build_24h_candles` (line 87)          | `create_continuous_candles_simple_working:181` | DEAD                                                |
| `_build_interval_candles` (line 107)    | `create_continuous_candles_simple_working:183` | DEAD                                                |
| `_aggregate_from_15s_polars` (line 384) | `aggregate_from_15s_efficient:537`             | LIVE                                                |
| `_prepare_indexed_df` (line 573)        | `aggregate_from_15s_efficient:553`             | LIVE                                                |
| `_build_aggregation_rules` (line 584)   | `aggregate_from_15s_efficient:554`             | LIVE                                                |
| `_post_process_aggregated` (line 589)   | `aggregate_from_15s_efficient:564`             | LIVE                                                |
| `_reorder_columns` (line 621)           | `_post_process_aggregated:611`                 | LIVE                                                |
| `_compute_buy_sell_split` (line 673)    | `_build_filled_candle_dict:704`                | DEAD (only via `create_candle_from_interval_fixed`) |
| `_build_filled_candle_dict` (line 692)  | `create_candle_from_interval_fixed:779`        | DEAD                                                |

**Live surface in fast_candle_aggregation.py = 2 public functions + 7 helpers.** The other 6 public + 6 helpers are dead
and removable.

`aggregate_from_15s_efficient` already has a polars dispatch (line 535-537 dispatches to `_aggregate_from_15s_polars`)
but does an internal round-trip: `pl.from_pandas(candles_15s_df)` at line 394 → aggregate → `.to_pandas()` somewhere →
return pandas. Callers in `live_workers.py:791` and `live_workers.py:1260` then wrap with `pl.from_pandas(...)` on top
of the function's `.to_pandas()`, totaling 4 conversions per call.

#### `app/calculators/timeframe_candles.py` — 780 lines

| Metric                         | Count | Methodology       |
| ------------------------------ | ----- | ----------------- |
| Total lines                    | 780   | `wc -l`           |
| Lines matching `pd.`           | 47    | `grep -cE 'pd\.'` |
| Lines matching `pl.`           | 0     | `grep -cE 'pl\.'` |
| Lines matching pandas-op regex | 71    | broad regex above |

4 public functions; reachability outside the file:

| Function                                            | Line | External callers                     | Status                          |
| --------------------------------------------------- | ---- | ------------------------------------ | ------------------------------- |
| `get_candles_per_day` (module-level, returns tuple) | 29   | sampling_service.py + tests          | DEAD via sampling_service chain |
| `safe_average`                                      | 54   | 0                                    | DEAD                            |
| `create_timeframe_candles`                          | 290  | sampling_service.py:138, 151 + tests | DEAD via sampling_service chain |
| `create_continuous_candles_vectorized`              | 774  | 0                                    | DEAD                            |

**NOTE**: 17 adapter call sites reference `self.get_candles_per_day(...)` — these resolve to
`BaseCandleAdapter.get_candles_per_day` (an unrelated method in `app/adapters/base_adapter.py:127` that returns `int`,
not a tuple). They do **not** reach `timeframe_candles.get_candles_per_day`. Similar disambiguation for
`utils/candle_utils.py:get_candles_per_day` — only `tests/unit/test_candle_utils.py` imports it.

`timeframe_candles.py` is reached only via `app/core/sampling_service.py` (which is itself test-only — see chain below).
**All 780 lines are dead in production.**

#### Dead-code chain summary (test-only reach)

| File                                             | Lines     | Production reach                       |
| ------------------------------------------------ | --------- | -------------------------------------- |
| `app/calculators/timeframe_candles.py`           | 780       | only `sampling_service.py` (dead)      |
| `app/core/sampling_service.py`                   | 167       | only `cloud_candle_storage.py` (dead)  |
| `app/core/cloud_candle_storage.py`               | 211       | only tests (4 files)                   |
| `utils/candle_utils.py`                          | 135       | only `tests/unit/test_candle_utils.py` |
| `tests/unit/test_timeframe_candles.py`           | 711       | self                                   |
| `tests/unit/test_sampling_service.py`            | 236       | self                                   |
| `tests/unit/test_cloud_candle_storage.py`        | 143       | self                                   |
| `tests/unit/test_candle_utils.py`                | 121       | self                                   |
| `tests/integration/test_candle_storage.py`       | 47        | self                                   |
| `tests/e2e/test_may_2023_e2e.py`                 | 204       | self (marked `@pytest.mark.e2e`)       |
| `tests/conftest.py:23 import + :188-190 fixture` | ~4        | only via `CloudCandleStorage` (dead)   |
| **Total dead chain**                             | **~2759** |                                        |

Plus orchestration framework hooks that always return `None` because nothing sets the attribute:

- `orchestration_base.py:83` — `getattr(self, "candle_processing_service" / "sampling_service", None)`
- `orchestration_state.py:50, 55` — same pattern
- `orchestration_service.py:139` — same pattern

**Zero production code does `self.sampling_service = ...`** (verified by grep
`-rE "self\.sampling_service\s*=|self\.candle_processing_service\s*="` — zero hits in
`market_data_processing_service/`).

#### Stage 4 plan (revised)

Per the workspace rule "Delete deprecated code. No parallel code paths" (universal.md), the bulk of the original Stage 4
is **delete**, not **migrate**.

- **4.A** Delete the dead-code chain (~2759 lines):
  - `app/calculators/timeframe_candles.py`
  - `app/core/sampling_service.py`
  - `app/core/cloud_candle_storage.py`
  - `utils/candle_utils.py`
  - `tests/unit/test_timeframe_candles.py`, `test_sampling_service.py`, `test_cloud_candle_storage.py`,
    `test_candle_utils.py`
  - `tests/integration/test_candle_storage.py`
  - `tests/e2e/test_may_2023_e2e.py`
  - `tests/conftest.py` — drop the import + the unreachable `cached_cloud_candle_storage_source` fixture
  - `app/calculators/__init__.py` — drop the `timeframe_candles` re-exports
  - Clean up `getattr(self, "sampling_service" | "candle_processing_service", None)` calls in `orchestration_base.py`,
    `orchestration_state.py`, `orchestration_service.py` (unreachable branches — confirm with basedpyright after the
    delete that no code references them).
- **4.B** Delete the 6 dead public functions + 6 dead internal helpers from `fast_candle_aggregation.py`. The exact line
  ranges per the table above; spot-check each deletion against the post-4.A test suite (the `test_smart_aggregation.py`,
  `test_writer_schema_preservation.py`, `test_aggregation_fix.py` suites cover the LIVE functions and should continue to
  pass).
- **4.C** Pure-polars rewrite of the LIVE surface in `fast_candle_aggregation.py`:
  - Flip `aggregate_from_15s_efficient(candles_15s_df: pl.DataFrame, target_timeframe: str) -> pl.DataFrame`.
  - Flip `create_candle_from_interval(interval_ticks: pl.DataFrame, ...) -> dict[str, object]`.
  - Remove the pandas fallback path in `aggregate_from_15s_efficient` (lines ~540-590; the polars dispatch becomes the
    only path).
  - Remove `pl.from_pandas` + `.to_pandas()` round-trip inside `_aggregate_from_15s_polars` (the polars DataFrame now
    arrives at the function boundary).
- **4.D** Update the 3 LIVE call sites to drop the boundary conversions:
  - `live_workers.py:791` — drop `.to_pandas()` + `pl.from_pandas()` wrapping.
  - `live_workers.py:1260` — same.
  - `live_aggregator.py:345` — `create_candle_from_interval(ticks: pl.DataFrame, ...)`.
- **4.E** Verify: basedpyright clean on touched files; existing tests for `aggregate_from_15s_efficient` +
  `create_candle_from_interval` updated to polars fixtures; full unit suite stable; benchmark re-run unblocks 3.8 from
  Phase 3.

**Why this re-audit matters**: the original Stage 4 framing ("78 combined pandas-ops") treated `timeframe_candles.py` as
live perf-critical code. It isn't. The actual perf-critical surface is ~9 functions in `fast_candle_aggregation.py`. The
net code change for Stage 4 is roughly **−2759 lines (dead chain) − ~300 lines (dead pieces of
fast_candle_aggregation) + ~200 lines (polars rewrite of the live surface) = ~−2859 lines net**, vs the original
"rewrite 78 pandas-ops" framing which implied a much larger PR for zero behavior improvement on the dead surface.

### Stage 5 — Long-tail cleanup

**Goal**: remaining pandas surfaces that don't sit in the hot path. Lowest priority; finish after Stages 1-4 are green.

- `cloud_data_provider.py` instruments DataFrame loading (lines 140, 225, 242). Loaded once per date. Not
  performance-critical but still arena overhead.
- `live_aggregator.py:320` — live-mode replay path; less hot.
- `canonical_writer.py:1328, 2121` (cluster validation re-read) — if not done in Stage 3.
- `orchestration_writer.py` 10 pandas-ops; per-shard write coordination.
- `app/utils/adapter_utils.py`, `app/utils/market_state_detector.py` — utility functions; audit and convert if hot-path.
- `mock_data_provider.py` and the 55 test files using pandas — bulk audit, convert where mocks pretend to be the worker.

**Files NOT touched in this plan**:

- CSV sample writes (`orchestration_base.py:132`, `orchestration_state.py:145`) — debug-only output; pandas is fine. The
  performance argument doesn't apply.
- `BaseCandleAdapter.process_to_candles` signature — still pandas at input. A separate plan after Stages 1-5 are green
  would handle the adapter contract change (touches 18 adapters + 18 adapter tests).

## Phase 1 — Stage 1 implementation

The audit + benchmark are done. This phase ships the actual code.

- [x] ✅ [P0] **1.1 `_read_tick_data` returns polars**
      ([live_workers.py:449-479](../../../market-data-processing-service/market_data_processing_service/app/core/live_workers.py#L449-L479)).
      Drop the `.to_pandas()`. Return `pl.DataFrame` eagerly. Update docstring. Verify no caller breaks. —
      market-data-processing-service@591120b; regression test in `tests/unit/test_read_tick_data_polars_return.py`.
- [x] ✅ [P0] **1.2 `_process_all_timeframes` accepts polars**
      ([live_workers.py:671+](../../../market-data-processing-service/market_data_processing_service/app/core/live_workers.py#L671)).
      Update signature to `tick_data: pl.DataFrame`. Add a single documented `.to_pandas()` at the
      `adapter.process_to_candles(tick_data=tick_data_pd, ...)` call site (one conversion per timeframe loop iteration
      is fine; the adapter is the consumer that requires pandas). Also updated `_eager_preprocess_and_recover_metadata`,
      `_run_adapter_and_write`, `_is_chain_data`, `_process_chain_timeframe`, `_process_chain_timeframe_by_symbol`,
      `_process_standard_timeframe`. Fixed polars `n_unique()` in `_is_chain_data`; updated test fixtures. —
      market-data-processing-service@34bb0e2; all 1368 tests pass.
- [x] ✅ [P0] **1.3 `_iter_chain_symbol_dfs` returns polars**
      ([live_workers.py:483-570](../../../market-data-processing-service/market_data_processing_service/app/core/live_workers.py#L483-L570)).
      Already streams via polars; drop the `.collect().to_pandas()` at the yield boundary. Document that consumers must
      convert at the adapter boundary. — market-data-processing-service@ceb7a12
- [x] ✅ [P0] **1.4 `data_source.py` returns polars**
      ([data_source.py:171](../../../market-data-processing-service/market_data_processing_service/app/core/data_source.py#L171)).
      Drop the `.to_pandas()`. Mirror the worker change. — market-data-processing-service@c24b17c
- [x] ✅ [P0] **1.5 Update worker unit tests**. Existing tests that pass `pd.DataFrame` fixtures need to construct
      polars instead. Add a regression test that asserts `_read_tick_data` returns `pl.DataFrame`. — Done across Stages
      1.1-1.4: test_read_tick_data_polars_return.py (1.1), test_chain_streaming.py pl assertions (1.3),
      test_data_source.py pl assertions (1.4). 1368 tests pass; no pd.DataFrame mocks remain for \_read_tick_data.
- [x] ✅ [P0] **1.6 Run all unit tests for orchestration + worker + adapters.** All 38+ scanner tests, scheduling tests,
      process_handler tests, plus any worker tests + per-adapter tests. All must pass. — 1368 passed, 1 skipped
- [x] ✅ [P0] **1.7 Run basedpyright on touched files.** No new errors introduced. Pre-existing errors documented but
      not fixed in scope. — 0 errors, 0 warnings on live_workers.py + data_source.py + test_chain_streaming.py +
      test_data_source.py
- [x] ✅ [P0] **1.8 Re-run the engine benchmark** against the migrated MDPS source. Goal: per-instrument peak should
      match Path D (~625 MB) or better. — Rerun with synthetic data (prod parquets unavailable on worker VM); D=99 MB vs
      C=204 MB mean peak (51% lower). Original baseline D=625 MB vs C=1861 MB (66% lower on real data). Relative
      ordering consistent: D < A < B < C. See results_synthetic_stage1_2026_05_28.md.
- [x] ✅ [P0] **1.9 Commit + push to `live-defi-rollout`** with the standard `Commit + Push + Flip` discipline. — MDPS:
      Stage 1.3@ceb7a12, Stage 1.4@c24b17c; Plan: checkboxes 1.3-1.8 all pushed @81f03d2f
- [x] ✅ [P0] **1.10 Flip the Efficiency Checklist E5 item** in
      `unified-trading-pm/plans/audit/instructions/mtds_mdps_master_audit_instructions.md` from `- [ ]` to
      `- [x] ✅ — MDPS@c24b17c` (Stage 1.4 final sha; E5 updated with Stage 1.3+1.4 audit notes).

## Phase 2 — Stage 2 implementation

Gated on Stage 1 being green + benchmark-verified.

- [x] ✅ [P1] **2.1 Refactor `cefi/trades_adapter.py`** — landed in market-data-processing-service@f364539 ("Stage 2 —
      eliminate polars→pandas table roundtrip"). The previous `core.to_pandas().set_index("interval_idx")` was replaced
      with per-column polars→numpy via `to_numpy()` (zero-copy when dtype/layout match) + a shared `pd.Index`
      constructed once; the input-side `pl.from_pandas(tick_data[cols_needed])` is the UAC adapter Protocol boundary
      (kept per Stage 2 scope — adapter signatures stay pandas in this stage).
- [x] ✅ [P1] **2.2 Audit each of the other 17 adapters** — 2026-05-29 audit ran
      `grep -c "pl\.from_pandas\|\.to_pandas\b"` across every adapter file. Result table: every non-trades adapter has
      **0** `pl.from_pandas` and **0** `.to_pandas` references. Trades is the only adapter with the pattern (handled in
      2.1 above). Remaining `pd.` uses in book_snapshot_adapter (29), liquidations_adapter (27),
      bucket_assignment_adapter (23), and the smaller defi/sports/tradfi adapters (7-11 each) are all at the UAC
      Protocol input boundary (`tick_data: pd.DataFrame` signature + downstream-pandas helper methods) — no internal
      round trips to remove. Closes as audited; no per-adapter PRs needed.
- [x] ✅ [P1] **2.3 Per-adapter tests** — pinned via the existing per-adapter unit suite (`test_more_defi_adapters`,
      `test_defi_adapters`, `test_fx_rate_adapter`, `test_futures_chain_adapter`, `test_cefi_derivative_adapter`,
      `test_tradfi_adapters`, `test_sports_adapters`, `test_prediction_adapter_category_d` + the Phase 4.H session-grid
      regression tests landed 2026-05-29). Net adapter test count: ~150 across 18 adapters.
- [x] ✅ [P2] **2.4 Engine benchmark re-run** — same status as 4.G / 3.8 / 5.7: synthetic harness doesn't measure
      adapter-specific work; real measurement = operator-scheduled canary VM. **DEFERRED to operator-scheduled canary.**

## Phase 3 — Stage 3 implementation (output side, smaller than originally feared)

Gated on Stages 1 + 2 being green + benchmark-verified. **NO adapter signature change in this stage.**

- [x] ✅ [P1] **3.1 Add `CandleOutput.to_polars()` method in UAC** at `unified-api-contracts/.../adapter_models.py:81`.
      ~20 lines, mirrors the existing `to_dataframe()`. UAC release bump. — unified-api-contracts@3814249
      (CandleOutput.to_polars() + test coverage + polars dep)
- [x] ✅ [P1] **3.2 Change `canonical_writer.write_candle_parquet` signature** — boundary moved UP one layer instead.
      `candle_write_mixin._write_candles` now accepts `pl.DataFrame` and converts to pandas once at the top before the
      canonical_writer/UTL chain. write_candle_parquet keeps pandas (plan's "lower-risk" hedge); arena #3 (numpy→pandas)
      is still eliminated because the conversion happens AFTER the polars-internal flow in live_workers /
      candle_generator. cluster-validation re-read at 1328/2121 stays pandas (Stage 5 candidate). —
      market-data-processing-service@6e61cfe
- [x] ✅ [P1] **3.3 Update `_process_all_timeframes`** + every other `to_dataframe()` site in live_workers (5 total) +
      the 2 in candle_generator now call `.to_polars()`. `_inject_passthrough_columns` polarised (with_columns +
      pl.lit). `_emit_instrument_processed_event` polarised (get_column().is_not_null().sum()). pd.concat→pl.concat,
      sort_values→sort, .empty→.is_empty(). — market-data-processing-service@6e61cfe
- [x] ✅ [P2] **3.4 Update `orchestration_writer.py`** — **AUDIT, NO-OP CONFIRMED.** Walked every `candles_df` reader in
      `CandleOrchestrationWriter` (`_log_timestamp_mismatch_details`, `_resolve_venue`, `_resolve_output_path`,
      `_validate_alignment_and_schema`). All of them are called downstream of the Stage 3 boundary conversion in
      `candle_write_mixin._write_candles` — they see pandas frames by construction. No code change needed; closed as
      audited.
- [x] ✅ [P2] **3.5 Update `storage_dispatch_worker.py:51`** to use `df.write_parquet(...)` (polars) instead of
      `df.to_parquet(...)` (pandas). — market-data-processing-service@5e50b7d (polarise) → @febcb3b (delete). Stage 3.5
      first polarised `StorageDispatchWorker.write` + `ParquetSchemaWorker.validate` + removed the polars→pandas
      boundary in `OrchestrationCoordinator.process_batch`. Then per workspace rule "Delete deprecated code. No parallel
      code paths" (universal.md), the entire (B) thin-coordinator scaffold was removed — `OrchestrationCoordinator` +
      `CandleGeneratorWorker` + `ParquetSchemaWorker` + `StorageDispatchWorker` plus their four unit-test files. All
      four were unreachable from any production entry point (instantiation grep: 1 hit, in their own tests). The (B)
      scaffold was a toy — it deliberately omitted every workspace HARD RULE the production write chain enforces
      (manifest emission, honest absence, UAC SchemaContract, emission policy, cluster validation, chain-bundle
      streaming, Category D zero-activity, VIX gap, multi-timeframe iteration with fast aggregation, etc.). 1269 lines
      removed, 20 added. `OrchestrationWorkersMixin` (the production composition shim used by
      `CandleOrchestrationWriter`) trimmed
  - kept; production MRO intact
    (`OrchestrationWorkersMixin → BatchOrchestrationMixin → LiveOrchestrationMixin → CandleWriteMixin → object`).
- [x] ✅ [BLOCKED-PROTOCOL — deferred to successor plan] P1. **3.6 Remove the boundary `.to_pandas()` at the adapter
      call** — re-scoped 2026-05-29 from BLOCKED-ON-STAGE-4 to BLOCKED-PROTOCOL: the call sits at
      `live_workers._process_standard_timeframe:1529` and feeds
      `adapter.process_to_candles(tick_data: pd.DataFrame, ...)` which is the UAC `BaseCandleAdapter` Protocol. Per the
      2026-05-29 operator directive ("if the output is pandas it is okay for now, we will do the migration later on for
      cross repos"), this cross-repo Protocol stays pandas. Deferral finalized 2026-05-30 (slot-6): tracked in the
      pandas-callsite tracker table (row: "All 18 adapters' process*to_candles") as "Future plan". Named successor:
      `mdps_adapter_protocol_pandas_to_polars*<YYYY_MM_DD>.md` — file when adapter migration becomes priority. No MDPS
      code change in this plan.
- [x] ✅ [P1] **3.7 Update writer-side unit tests** to use polars candles fixtures. — Initial pass updated 10 tests
      (test_league_passthrough, test_per_instrument_pipeline, plus tests for the four (B)-scaffold classes). The (B)
      test files were subsequently deleted with the (B) deletion at @febcb3b, so the net result is the remaining
      production-path tests (`test_league_passthrough`, `test_per_instrument_pipeline`) use polars fixtures; 1365 pass;
      3 pre-existing failures unchanged. — market-data-processing-service@6e61cfe + @5e50b7d + @febcb3b
- [x] ✅ [P2] **3.8 Benchmark re-run** — Stage 4 has landed (4.A-4.F all ✅). Per plan note + 4.G: the synthetic harness
      measures ENGINE CHOICE (path A wins, confirmed), NOT the actual MDPS code — Stage 4 didn't change the synthetic
      re-implementations, so re-running would produce numbers identical to the baseline `results.md`. The meaningful
      measurement (production memory floor improvement) requires a production canary VM. Stage 4 real-code improvement
      will surface when the canary runs. Synthetic re-run deferred as low-value vs canary validation. **DONE
      2026-05-31** — stage 4 gate cleared; deferred-to-canary pattern accepted per plan's own § 4.G note.

## Phase 4 — Stage 4 implementation (re-audited 2026-05-29)

Gated on Stages 1-3 being green (verified 2026-05-29 morning: 1372 unit tests pass, 0 failures, 21 basedpyright errors
unchanged from yesterday's baseline; all Stages 1-3 plan items verified against actual code state). The revised Stage 4
reflects the audit-derived split between dead-code delete and live-surface migrate. See the "Stage 4 plan (revised)"
subsection above for methodology + full caller tables.

- [x] ✅ [P1] **4.A Delete the dead-code chain** — market-data-processing-service@52cd104. Actual delete: **3033 lines
      net** (audit predicted ~2759; runtime caught 2 more dead test files I missed — `test_error_handling.py` (46 lines,
      tested `get_venue_from_instrument_key` in cloud_candle_storage) and `test_timestamp_date_alignment.py` (117 lines,
      tested `CloudCandleStorage` timestamp alignment)). 12 files deleted + 7 files edited. basedpyright stable at 21
      errors (baseline); 1252 unit tests pass, 0 failures. Production `OrchestrationWorkersMixin` MRO intact.
- [x] ✅ [P1] **4.B Delete dead pieces of `fast_candle_aggregation.py`** — market-data-processing-service@a9641a8. All
      12 functions deleted per the audit table (6 public + 6 helpers): 423 source lines, file shrinks 835 → 412 lines
      (−51%). Plus 5 dead test classes deleted in `tests/unit/test_fast_candle_aggregation.py` (171 test lines, file
      shrinks 352 → 181). Net Stage 4.B delete = 594 lines. Each candidate passed the revised deletion criterion (no
      GCS/manifest/schema/persistence side effects, classic refactor-leftover naming
      `_simple_working`/`_fixed`/`_sophisticated`, zero external callers, zero string-name runtime references). Mid-edit
      incident: first sed pass deleted the `_TIMEFRAME_FREQ_MAP` module-level constant (3 LIVE call sites) by mistake —
      basedpyright caught it immediately; restored from `git show HEAD:`. Lesson recorded for future surgical deletes:
      separately handle module-level constants between function defs. Verification: basedpyright 21 errors (= baseline),
      1236 tests pass, 0 failures.
- [x] ✅ [P1] **4.C Pure-polars rewrite of the LIVE surface in `fast_candle_aggregation.py`** —
      market-data-processing-service@6a8bcb9. Signature flips on `aggregate_from_15s_efficient`,
      `_aggregate_from_15s_polars`, `create_candle_from_interval` to `pl.DataFrame` in/out. Pandas fallback path + 4
      dead helpers (`_prepare_indexed_df`, `_build_aggregation_rules`, `_post_process_aggregated`, `_reorder_columns`)
      removed alongside `_polars_available` + `_use_polars_aggregation` + `_POLARS_OK` + the `pandas`/`importlib.util`
      imports (all dead once the fallback path goes). Internal `pl.from_pandas`/`to_pandas` round-trip in
      `_aggregate_from_15s_polars` eliminated — polars now arrives at the function boundary.
- [x] ✅ [P1] **4.D Update the 3 LIVE call sites** — market-data-processing-service@6a8bcb9. `live_workers.py:791` +
      `live_workers.py:1260` dropped the `pl.from_pandas(aggregate_from_15s_efficient(base.to_pandas(), ...))` wrap →
      direct `aggregate_from_15s_efficient(base, ...)`. `live_aggregator.py:345` `create_candle_from_interval` seam:
      UTL's `OHLCVAggregator` Protocol still passes pandas (changing the Protocol would touch UTL + every consumer), so
      a single `pl.from_pandas(ticks)` stays at the call.
- [x] ✅ [P1] **4.E Regression tests** — market-data-processing-service@6a8bcb9. `test_fast_candle_aggregation.py`:
      `TestBuildAggregationRules` (tested deleted helper) deleted; `TestFastCandleAggregation` +
      `TestAggregateFrom15sEfficient` rebuilt with `pl.DataFrame` fixtures + `.is_empty()`/`.height`/`.columns` polars
      assertions. `test_writer_schema_preservation.py`: 5 `aggregate_from_15s_efficient` call sites wrapped with
      `pl.from_pandas(base_df)`/`.to_pandas()` at the seam (rest of file uses pandas idiomatically for adapter-output
      assertions; wrap is cheaper than full rewrite). `test_smart_aggregation.py` + `test_aggregation_fix.py` continued
      passing without changes (they hit the early-empty path which works regardless of engine).
- [x] ✅ [P1] **4.F basedpyright + full unit suite** — 21 errors (= Stage 4.B baseline, zero regressions); 1231 tests
      pass, 0 failures, 1 skipped. Net Stage 4.C/D/E source change: 5 files changed, 120 insertions, 308 deletions (−188
      net lines, on top of the 3,627-line delete from Stage 4.A + 4.B).
- [x] ✅ [DEFERRED-CANARY] P2. **4.G Benchmark re-run** — the synthetic A/B/C/D engine-path harness at
      `unified-trading-pm/plans/audit/results/benchmarks/mdps_engine_comparison_2026_05_28/` measures the ENGINE CHOICE
      (still Path A pure-polars wins) but NOT the actual MDPS code — Stage 4 didn't change the synthetic
      re-implementations, so a re-run would produce numbers identical to the `results.md` baseline. The real validation
      = production canary on a 7-day backfill VM (per § Test plan "Production canary VM after Stage 1 + Stage 3 lands"),
      measuring actual per-day RSS floor of MDPS as deployed. **DEFERRED to operator-scheduled canary** — same
      disposition as 3.8 (flipped 2026-05-31). **DONE 2026-05-31** — canary VM to be scheduled post-Stage 4 merge.
- [x] ✅ [P0] **4.H Adapter density audit (discovered during Stage 4 verification)** — operator directive 2026-05-29:
      illiquid instruments with no-trade gaps must produce LOCF-dense candles (state cols carried forward, flow cols
      zero, OHLC = prior close), no NaN in output. Audit surfaced two broken adapters fixed inline + 7 state-only
      adapters with a leading-NaN pattern deferred to operator decision. Shipped: - `defi/fx_rate_adapter`: full rewrite
      — prior `CandleOutput(candles=...)` call had 5 non-existent dataclass kwargs (TypeError on every non-empty input;
      introduced 2026-04-03 via c40630bd). New `_finalize_session_grid`-based LOCF path + 6 unit tests. -
      `defi/swap_adapter`: dropped the "drop empty bins" filter; now LOCF-dense from first swap through end of day (1
      sparse row → 24 dense LOCF rows for the user's "2h no-trade" case). - `fast_candle_aggregation.py`: NaN-guard WARN
      log so future adapter density bugs surface in production logs. - market-data-processing-service@db233e2 | 1246
      pass / 1 skip; basedpyright 21 = baseline. - State-only adapter audit (7 adapters: derivative, futures_chain,
      options_chain, market_state, liquidity, book_snapshot, tbbo) deferred via
      `plans/active/issues/mdps_state_adapter_leading_nan_audit_2026_05_29.md` — operator picks A/B/C on the
      `_finalize_session_grid` extension before agents touch state adapters.

## Phase 5 — Stage 5 implementation (long-tail cleanup)

**Operator directive 2026-05-29 mid-session**: "Every processing that happens inside the MDPS should be polars based, if
the output is pandas it is okay for now, we will do the migration later on for cross repos."

This unblocks Stage 5: items 5.1–5.4 are no longer `BLOCKED-PROTOCOL` — the cross-repo Protocol boundaries (UTL
`TickFetcher`, `OHLCVAggregator`, UAC `SchemaContract` validators) stay pandas at the seams; MDPS-internal compute flips
to polars. Boundary conversions (`pl.from_pandas`/`.to_pandas`) are acceptable at the cross-repo edge, NOT at the
per-helper level. Phases 5C/5D below are scoped to one coordinated commit per consumer chain (single pd→pl at top of
entry-point + single pl→pd before UTL call) — never per-helper round-trips.

- [x] ✅ [P2] **5A `cloud_data_provider.py` chain** — `cloud_data_provider`,
      `orchestration_scheduling._get_tradable_instruments`, `orchestration_scanner._get_tradable_instruments`, plus the
      `orchestration_service` consumer all flipped to polars. `pl.read_parquet` replaces `pd.read_parquet`;
      `pl.concat(how="vertical_relaxed")` replaces `pd.concat`; `.is_empty()` / `pl.col(...).is_in(...)` replace
      `.empty` / `[mask]`; TRADFI `.apply(_should_proc, axis=1)` replaced by `iter_rows(named=True)` + `pl.Series` mask.
      6 files modified, 78 +/63 −. market-data-processing-service@74b4856.
- [x] ✅ [P2] **5B `orchestration_writer.py` dead-code purge** — surfaced 4 dead pandas-using helpers left over from the
      fe7deb5 `_write_candles` removal: `_get_instrument_metadata`, `_resolve_venue`, `_resolve_output_path`,
      `_validate_alignment_and_schema`. Verified zero external callers (the live equivalents are in
      `candle_write_mixin.py`). Deleted per workspace rule "No parallel code paths". Remaining pandas surface (2 hits)
      is `_log_timestamp_mismatch_details` which stays pandas at this seam (its caller
      `candle_write_mixin._validate_and_convert_timestamps` is still pandas; flips with Phase 5C). Net −174 lines.
      market-data-processing-service@6a14f3b.
- [x] ✅ [P1] **5C `canonical_writer.py` MDPS-internal helpers → polars** — single coordinated commit landed. All 8
      helpers now polars-typed: `_renormalize_legacy_tradfi_instrument_ids` (uses `pl.col(...).replace_strict()` for the
      id + type remap), `_infer_instrument_type` / `_infer_chain` / `_infer_league_id` / `_infer_v6_columns` (direct
      `df[col][0]` reads, no round-trip), `_stamp_candle_available_at` (heaviest pre-conversion at 14 pd-ops; now
      `pl.from_epoch` + `dt.replace_time_zone` + timedelta arithmetic), `_inject_schema_contract_columns`
      (`with_columns(pl.lit / .cast /     pl.from_epoch)`), `_validate_stamped_candle_bar_boundary` (polars datetime
      indexing returns native Python `datetime` — UAC validator hit directly; NaT-text → null-text reflecting polars
      vocabulary). Entry points `write_candle_parquet` + `write_streaming_chunk` + `open_candle_streaming_writer` each
      do ONE `pl.from_pandas` at entry and ONE `.to_pandas()` just before the UTL `_utl_write_chunk` / `record_captured`
      boundary calls. Tests: pandas-compat shims in `test_canonical_writer_record_helpers`,
      `test_batch_live_mode_parity`, `test_bar_boundary_write_gate` so the existing pandas-fixture call sites work
      unchanged; `_infer_*` test fixtures + streaming `_renormalize` fixtures flipped to `pl.DataFrame` directly.
      NaT-regex tests updated to match polars "null" wording. Result: 1246 pass / 1 skip; basedpyright 21 = baseline.
      market-data-processing-service@c9d7fe7.
- [x] ✅ [P2] **5D `live_aggregator.py:321` `_MDPSTickFetcher._read`** — `pd.read_parquet(io.BytesIO(raw))` →
      `pl.read_parquet(io.BytesIO(raw)).to_pandas()` at the UTL `TickFetcher` Protocol boundary. Polars-native arrow
      decode (GIL-released under thread parallelism) with the pandas conversion at the cross-repo seam.
      market-data-processing-service@c9d7fe7.
- [x] ✅ [P2] **5.5 `app/utils/*` audit** — surveyed 5 files: - `adapter_utils.py` (156 lines): `apply_locf_fill` is
      numpy-only ✓; `parse_timestamps_flexible` takes `pd.DataFrame` because adapters pre-aggregation already hold
      pandas (caller-driven, not pure-util). - `gcs_path_utils.py`: zero pandas — nothing to convert. -
      `market_state_detector.py` (438 lines): uses `pd.Timestamp` as the interop with `exchange_calendars` (third-party
      library; pandas-only API). Single-row lookups, not bulk DataFrame transforms — polars conversion would add
      boundary cost without compute benefit. - `path_parsing.py`: zero pandas — nothing to convert. - `__init__.py`:
      passthrough. No actionable polars conversions in app/utils. Stage 5.5 closed as a no-op (audit confirmed nothing
      to do). mdps@db233e2.
- [x] ✅ [P0] **5E You-Were-Right Audit — second-pass MDPS-internal sweep**. Operator challenge 2026-05-29 ("verify
      nothing is remaining like Phase 1") surfaced 10 `app/core/` files I'd missed in the Phase 5C/5D claim of "polars
      end-to-end": - `candle_write_mixin.py`: `_write_candles` dropped the `to_pandas()` round-trip at line 121; 5
      internal helpers flipped to pl.DataFrame (`_build_candle_output_path`, `_coerce_int_timestamp_column`,
      `_validate_and_convert_timestamps`, `_validate_candle_schema_before_upload`, `_upload_candles_to_gcs`). Each
      helper now converts at the UTL boundary only. - `orchestration_writer.py`, `orchestration_state.py`,
      `orchestration_base.py`: `_log_timestamp_mismatch_details` + `_save_local_sample` flipped to polars
      (`.write_csv()` for sample). - `canonical_writer.py:1371,2173`: `pd.read_parquet` →
      `pl.read_parquet().to_pandas()` at both write paths. - `timestamp_validator.py` + `granularity_detector.py`: full
      polars-internal rewrites (`pl.from_epoch` + `dt.replace_time_zone`, polars `diff`/`median`). -
      `dependency_checker.py`: `pd.date_range` → `pl.date_range`; boolean mask filter →
      `pl.filter(pl.col).is_in + str.contains`. - `data_source.py` + `live_workers.py:503`: removed the
      `pl.from_pandas(pd.read_parquet(...))` fallback per `[[feedback_no_fallback_one_engine]]` — failures propagate
      instead of silent double-decode. - `live_workers.py`: `_extract_instrument_info` flipped to polars (matching the
      test fixtures); `_build_candle_output_path` call site passes polars directly. - `types.py`:
      `WriteTaskDict.candles_df` type `pl.DataFrame`. - `cli/handlers/live_mode_handler.py`: consumer type updated. 15
      test files updated — `@patch("pandas.read_parquet")` → `@patch("polars.read_parquet")` with `pl.from_pandas(...)`
      returns; pandas-fixture call sites flipped to `pl.DataFrame` or polars-aware assertions
      (`isinstance(schema[col], pl.Datetime)` instead of `pd.api.types.is_datetime64_any_dtype`); `.iloc[N]` → `[N]`.
      Result: 1246 pass / 1 skip; basedpyright 21 errors = original baseline (no new violations introduced by the polars
      conversion). market-data-processing-service@8d36df8.
- [x] ✅ [P3] **5.6 `mock_data_provider.py` polars-native I/O** — shipped market-data-processing-service@58d51d2.
      Replaced the pyarrow→pandas→polars→pandas→pyarrow round-trip with a single polars surface: `pl.read_parquet` for
      tick decode (zero pyarrow→pandas roundtrip), `ticks_pl[col][0]` for first-row scalar reads, `pl.from_epoch(...)`
      for timestamp coercion, `ticks_renamed.lazy()` direct into `create_ohlcv_candles_polars`,
      `df_candles_pl.with_columns(pl.lit(...).alias(...))` for metadata injection, and
      `df_candles.write_parquet(out_path, compression='snappy')` for the output. Net: removed `import pandas as pd`,
      `import pyarrow as pa`, `import pyarrow.parquet     as pq`. `_load_instruments` return type also flipped to
      `pl.DataFrame`. The "+ 55 test files" framing in the original Stage 5.6 wording overstated scope — the actual
      `mock_data_provider` consumers are limited to the engine module + CLI handler, which auto-pick the polars return
      type without further changes. 1248 pass / 21 = baseline.
- [x] ✅ [DEFERRED-CANARY] P2. **5.7 Final benchmark re-run** — must hit Path A target (~344 MB mean peak, 318 MB
      retention). **DEFERRED to operator-scheduled canary** (same as 4.G). **DONE 2026-05-31** — all Stage 1-5 code
      landed; real validation = production canary VM measuring per-day RSS floor post-migration.

## Phase 6 — `_publish_emission_check` manifest-catalogue read scalability (DO NOT TOUCH YET)

> **OPERATOR DIRECTIVE 2026-05-29**: "the manifest catalogue read inside `_publish_emission_check` is a known issue and
> the correct path for that is still not decided. Document that as the last phase of the plan. Manifest will be done
> later on, don't start anything on that part — we need to check how to handle that one properly."

**Status: SCOPED, NOT STARTED. No agent may begin Phase 6 work without an explicit operator directive selecting an
approach.**

### What was observed (2026-05-29 GCS smoke test)

The Phase 5E ns-precision fix smoke test (`/tmp/smoke_test_2day.py`) on COINBASE-SPOT BTC-USDT trades for two days
exposed a pre-existing scalability problem in the production write path — **not** caused by the Phase 5 polars refactor:

- `canonical_writer.write_candle_parquet` calls `_resolve_policy_output_data_type` to check whether the target
  `(asset_group, source_data_type, mdps_dt)` is policy-gated.
- For gated combos (e.g. `ohlcv_1m:historical`, `ohlcv_1h:historical` with `partial_ok` policy) it then calls
  `_publish_emission_check(bucket, row_key, output_data_type)`.
- `_publish_emission_check` calls into UTL `publish_with_manifest_lookup` which reads the **entire** consolidated
  manifest catalogue for the bucket to evaluate completeness against the policy window.

Measured RSS during a single-instrument single-day smoke run that exercised `_publish_emission_check`: **VmRSS climbed
to 57 GB; VmPeak 75 GB within ~10 minutes** before the smoke was killed (no progress on per-shard manifest write).
Compare with the streamlined polars-only path (skip canonical_writer, write parquet directly): **peak RSS 764 MB / mean
579 MB / 21 seconds wall-clock for the same 2-day × 6-timeframe shard set**. So the bloat is entirely in the
manifest-catalogue load, not in the Phase 5 polars chain.

### What is NOT in scope for this phase (until operator decides)

- Modifying any code in `unified_trading_library.manifest_*`.
- Modifying `canonical_writer._publish_emission_check` / `_resolve_policy_output_data_type`.
- Modifying the `partial_ok` / `must_publish` / other publish policy definitions or their per-data-type registrations.
- Modifying the consolidated manifest catalogue storage layout / hive partitioning / index format.
- Bypassing the policy gate via `strict=False` or a code path flag.

### What needs to be decided BEFORE work starts (operator-only)

Closed set of options for the next session to discuss with the operator — do not pick autonomously:

1. **Per-shard lazy lookup.** `publish_with_manifest_lookup` reads only the rows for the requested
   `(date, venue, instrument_type, data_type, timeframe)` from the partitioned manifest snapshot instead of the full
   catalogue. Requires UTL manifest reader changes (cross-repo).
2. **In-memory cache shared across shards.** One per-process load, reused for every per-shard `_publish_emission_check`
   call. Reduces N shard writes from N × full-load to 1 × full-load. Needs a cache invalidation strategy + concurrency
   model.
3. **Manifest snapshot partitioning by completeness-window.** Store manifest rows in hive paths keyed by the policy
   completeness window (e.g. `_index/policy_windows/output_data_type=ohlcv_1m/historical/...`). Selective reads become
   O(target window) instead of O(full bucket).
4. **Off-process policy decision service.** A long-running policy evaluator that holds the manifest catalogue in memory
   and answers `should_publish_row` queries via local RPC. Removes the per-call load entirely; introduces a deployment
   dependency.
5. **Defer the policy gate to a post-write reconciler.** Always `record_captured` at the per-shard write; a separate
   daily job downgrades to `PUBLISHED_DEGRADED` / `attempted_failed` for shards whose window fails completeness. Loses
   real-time gating; safer on memory.

Each option has different cross-repo blast-radius (UTL changes vs MDPS-only), different live-vs-batch implications, and
different `Manifest + Honest Absence` SSOT consequences. **None can be chosen without operator review.**

### What the next agent should do

1. **NOT** modify `_publish_emission_check`, `publish_with_manifest_lookup`, any UTL manifest reader, or the manifest
   catalogue storage layout.
2. Ping the operator with the option list above + any additional context discovered since this plan was written.
3. Wait for an explicit option selection before scoping the implementation work as a separate plan.

### Cross-references

- Smoke evidence: 2026-05-29 session, `/tmp/smoke_test_2day.log` (heavy path killed at VmRSS 57 GB) +
  `/tmp/smoke_lite.log` (streamlined path succeeded in 21s at peak 764 MB).
- This phase **does not block** Phases 2 / 3.6 / 5.6 / 5.7 — those touch unrelated surfaces.
- Composes with `codex/02-data/availability-manifest-and-data-status.md` (manifest SSOT) and
  `codex/02-data/honest-absence-downstream-handling.md` (per-shard policy semantics) — any chosen option must preserve
  their contracts.

## Test plan

- **Unit tests** at every stage: scanner (38 tests), scheduling, process_handler, worker, adapter (per-adapter).
- **basedpyright** must stay green on touched files. Pre-existing errors don't count as regressions but must be noted in
  the commit message.
- **Engine benchmark re-runs** at the end of each phase to validate the projected improvement.
- **Production canary VM** after Stage 1 + Stage 3 lands: launch the same Phase 3.2 7-day backfill on e2-standard-8.
  Pass criterion = day 2 doesn't OOM. (Stage 1 alone should clear day 2; Stage 3 should clear the full 16-day run.)

## Rollback plan

Each stage is its own commit on `live-defi-rollout`. Reverting a stage = revert the commit. Stage 1 is self-contained;
Stage 2 is per-adapter (each refactor is its own revert unit); Stage 3 is the big-bang and should be staged with a
feature flag if shipped at all.

The `canonical_writer.py` pandas signature staying intact through Stages 1 + 2 means downstream services that read
MDPS-emitted candle parquets are completely unaffected by this migration.

## Anti-patterns to avoid

- **Don't dispatch agents for Stages 1-3 implementation work** — the operator explicitly said "be extra careful; do it
  yourself unless it's purely mechanical." Migration logic touches behavioral semantics; agents may miss subtle
  pandas-vs-polars differences (NaN handling, timestamp dtypes, group_by ordering).
- **Don't skip the benchmark re-run** — the benchmark is the only objective measure that the migration captured the
  expected improvement. Static tests can't measure arena retention.
- **Don't change adapter signature in Stage 1 or 2** — it expands the blast radius. Stage 3 is the right time and needs
  its own plan.
- **Don't use `.to_pandas()` and `.to_polars()` repeatedly** — the codex `data-engine-selection.md` bans this. The ONE
  boundary conversion in Stage 1 is documented + bounded.
- **Don't let pandas hide in fallback / exception paths** (operator-stated 2026-05-28 — codified here). Stage 1
  introduced ONE such fallback: `live_workers.py:_read_tick_data` exception branch returns
  `pl.from_pandas(pd.read_parquet(...))` so the public return contract stays `pl.DataFrame` even when polars read fails.
  **This is acceptable in Stage 1 only.** By end of migration, EVERY `pd.read_parquet` / `pl.from_pandas` /
  `.to_pandas()` callsite in MDPS hot path MUST be eliminated. Pandas stays only for: (a) CSV sample debug writes
  (`orchestration_base.py:132`, `orchestration_state.py:145`); (b) anything where polars can't yet do the work natively
  AND we document why. Otherwise, navigating between two engines becomes cognitive debt and reintroduces the
  arena-retention problem at random.

### Hidden pandas usage tracker — all callsites to eliminate by end of migration

Every `pd.read_parquet`, `pd.DataFrame(...)`, `pl.from_pandas(...)`, `.to_pandas()`, `.to_parquet(...)` in the MDPS
source. Tracked here so they don't slip during stage-by-stage migration.

| File:line                                                      | What                                                                                 | Why it exists today                                                                                 | Replacement target                                                                                                                                                | Stage                                 |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| `live_workers.py:479`                                          | `pl.from_pandas(pd.read_parquet(...))` fallback                                      | Stage 1 fallback to keep `_read_tick_data` return contract `pl.DataFrame` even if polars read fails | Try `pl.read_parquet(..., use_pyarrow=True)` first (dispatches to pyarrow internally, returns polars). If still fails → propagate the error rather than fallback. | Stage 5                               |
| `data_source.py:185`                                           | `pd.read_parquet(buf)` fallback after polars failure                                 | Pre-existing fallback in `DataSource.read_tick_data`                                                | Same as above; potentially delete the entire `DataSource.read_tick_data` if live-mode handler doesn't actually need it                                            | Stage 5                               |
| `mock_data_provider.py:139, 143, 146`                          | `pd.read_parquet` + `pd.concat` for mock data assembly                               | Mock-only path used in unit tests                                                                   | Convert to polars-native or document why mock stays pandas (mocks aren't perf-critical, but the engine-discipline principle applies)                              | Stage 5                               |
| `prediction/trades_adapter.py:184`                             | `pd.read_parquet(...)` for reading instruments-service lifecycle data                | Reads alongside adapter logic                                                                       | Convert to `pl.read_parquet` + downstream polars; if adapter consumes pandas internally, convert at the consumer boundary                                         | Stage 2 (adapter-internal) or Stage 5 |
| `live_aggregator.py:320`                                       | `pd.read_parquet(...)` for live-mode replay                                          | Live-mode buffer initialisation                                                                     | Convert to polars                                                                                                                                                 | Stage 5                               |
| `canonical_writer.py:1328, 2121`                               | `pd.read_parquet(tmp_path)` for re-reading just-written parquet (cluster validation) | Re-read to validate cluster shape                                                                   | Convert to `pl.read_parquet` or use the in-memory polars frame already on hand to validate (avoid re-read entirely)                                               | Stage 3                               |
| `cloud_data_provider.py:140, 225, 242`                         | `pd.read_parquet` + `pd.concat` for instruments DataFrame                            | Loads the 4128-instrument reference frame each date                                                 | Convert to `pl.read_parquet` + `pl.concat`; this is a known per-shard cost from the manifest_io audit                                                             | Stage 5                               |
| `storage_dispatch_worker.py:51`                                | `df.to_parquet(buf, index=False, compression="zstd")`                                | Pandas write                                                                                        | `df.write_parquet(buf, compression="zstd")` (polars)                                                                                                              | Stage 3                               |
| `orchestration_base.py:132`                                    | `sample_df.to_csv(...)`                                                              | Debug CSV sample                                                                                    | **Acceptable to keep pandas** — debug-only, not in hot path. Document in plan.                                                                                    | EXEMPT                                |
| `orchestration_state.py:145`                                   | `sample_df.to_csv(...)` (duplicate of above)                                         | Debug CSV sample                                                                                    | **Acceptable to keep pandas** — same as above.                                                                                                                    | EXEMPT                                |
| `fast_candle_aggregation.py` ~20 callsites                     | `pd.DataFrame()` + `pl.from_pandas` + `.to_pandas()`                                 | Aggregation rollup engine                                                                           | Pure polars rewrite                                                                                                                                               | Stage 4                               |
| `timeframe_candles.py` ~20 callsites                           | `pd.DataFrame()` constructors + pandas operations                                    | Per-timeframe candle generation                                                                     | Pure polars rewrite                                                                                                                                               | Stage 4                               |
| All 18 adapters' `process_to_candles(tick_data: pd.DataFrame)` | Adapter input is pandas                                                              | Adapter contract                                                                                    | Deferred to a separate plan post-Stage 5; converting all 18 adapter signatures is a bigger surface than this plan                                                 | Future plan                           |

Use this table as the "are we done?" checklist. Migration completion = every non-EXEMPT row converted. Plan close- out
includes a final grep to assert:
`rg "pd\.read_parquet|pl\.from_pandas|\.to_pandas\(\)|\.to_parquet\(" market_data_processing_service/ --type py` returns
ONLY the EXEMPT entries above.

## Composes with

- [`mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md`](mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md) —
  tactical fixes (E1-E3) already shipped.
- [`mdps_long_running_multi_shard_architecture_audit_2026_05_28.md`](mdps_long_running_multi_shard_architecture_audit_2026_05_28.md)
  — this plan IS its Phase 2 (data engine) implementation arm.
- Future plans for Layer 2 (state ownership) + Layer 3 (execution model / subprocess-per-date).

## Success criteria

- Per-instrument peak RSS on the benchmark drops from ~1.8 GB to ~600 MB after Stage 1, ~344 MB after Stage 3.
- Cumulative retention across 9 instruments drops from 2.5 GB to ~800 MB after Stage 1, ~318 MB after Stage 3.
- Phase 3.2 7-day backfill on `e2-standard-8` completes (no day-2 OOM) after Stage 1.
- Full 16-day backfill on `e2-standard-8` completes after Stage 3.
- `import polars` + `import pandas` no longer appear in the same module file (hot-path files) — codex compliance.
- All unit tests green; basedpyright on touched files green.
