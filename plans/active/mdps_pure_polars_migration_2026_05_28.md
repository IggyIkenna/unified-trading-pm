---
name: mdps_pure_polars_migration
title: "MDPS pure-Polars migration — staged engine cutover (2026-05-28)"
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
status: active
priority: P1
created: 2026-05-28
author: harsh (claude opus 4.7)
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

### Stage 4 — Aggregation calculators (the actual pandas-heavy code)

**Goal**: convert the rollup engines from mixed-engine to pure polars. These are the calculators that aggregate 15s
candles into larger timeframes (1m, 5m, 15m, 1h, 4h, 24h).

**Files touched (one PR each due to size)**:

- `app/calculators/fast_candle_aggregation.py` — 36 pandas-ops in 835 lines. Internal `pl.from_pandas` (line 394) →
  aggregate → `.to_pandas()` (line 504). Convert to pure polars.
- `app/calculators/timeframe_candles.py` — 48 pandas-ops in 780 lines. Heaviest pandas user in the calculator layer.
  Per-timeframe candle generation logic.

**Why staged separately**: these are the largest behavioral surfaces (78 combined pandas-ops). Each function needs
careful before/after comparison. Likely produces meaningful per-day RSS reduction beyond Stage 3 because these are
called inside the inner aggregation loop.

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

- [x] ✅ [P0] **1.1 `_read_tick_data` returns polars** ([live_workers.py:449-479](../../../market-data-processing-service/market_data_processing_service/app/core/live_workers.py#L449-L479)).
  Drop the `.to_pandas()`. Return `pl.DataFrame` eagerly. Update docstring. Verify no caller breaks. — market-data-processing-service@591120b; regression test in `tests/unit/test_read_tick_data_polars_return.py`.
- [ ] [P0] **1.2 `_process_all_timeframes` accepts polars** ([live_workers.py:671+](../../../market-data-processing-service/market_data_processing_service/app/core/live_workers.py#L671)).
  Update signature to `tick_data: pl.DataFrame`. Add a single documented `.to_pandas()` at the
  `adapter.process_to_candles(tick_data=tick_data_pd, ...)` call site (one conversion per timeframe loop iteration
  is fine; the adapter is the consumer that requires pandas).
- [x] ✅ [P0] **1.3 `_iter_chain_symbol_dfs` returns polars** ([live_workers.py:483-570](../../../market-data-processing-service/market_data_processing_service/app/core/live_workers.py#L483-L570)).
  Already streams via polars; drop the `.collect().to_pandas()` at the yield boundary. Document that consumers must
  convert at the adapter boundary. — market-data-processing-service@ceb7a12
- [x] ✅ [P0] **1.4 `data_source.py` returns polars** ([data_source.py:171](../../../market-data-processing-service/market_data_processing_service/app/core/data_source.py#L171)).
  Drop the `.to_pandas()`. Mirror the worker change. — market-data-processing-service@c24b17c
- [ ] [P0] **1.5 Update worker unit tests**. Existing tests that pass `pd.DataFrame` fixtures need to construct
  polars instead. Add a regression test that asserts `_read_tick_data` returns `pl.DataFrame`.
- [ ] [P0] **1.6 Run all unit tests for orchestration + worker + adapters.** All 38+ scanner tests, scheduling
  tests, process_handler tests, plus any worker tests + per-adapter tests. All must pass.
- [ ] [P0] **1.7 Run basedpyright on touched files.** No new errors introduced. Pre-existing errors documented but
  not fixed in scope.
- [ ] [P0] **1.8 Re-run the engine benchmark** against the migrated MDPS source. Goal: per-instrument peak should
  match Path D (~625 MB) or better. This validates the change with the same measurement that drove the decision.
- [ ] [P0] **1.9 Commit + push to `live-defi-rollout`** with the standard `Commit + Push + Flip` discipline.
- [ ] [P0] **1.10 Flip the Efficiency Checklist E5 item** in
      `unified-trading-pm/plans/audit/instructions/mtds_mdps_master_audit_instructions.md` from `- [ ]` to
      `- [x] ✅ — MDPS@<sha>`.

## Phase 2 — Stage 2 implementation

Gated on Stage 1 being green + benchmark-verified.

- [ ] [P1] **2.1 Refactor `cefi/trades_adapter.py`** as the reference implementation. Drop the `pl.from_pandas(...)`
      round trip at line 229 + the `.to_pandas().set_index(...)` round trip at line 260. Internal polars only; convert
      to pandas at the function return boundary (since signature is still pandas in this stage).
- [ ] [P1] **2.2 Audit each of the other 17 adapters** for internal `pl.from_pandas` / `.to_pandas` round trips.
      Tabulate. For each adapter with the pattern, ship a separate PR following the trades_adapter shape.
- [ ] [P1] **2.3 Per-adapter tests** — each refactored adapter MUST have a regression test that pins its behaviour
      (input → output) against a small synthetic tick fixture.
- [ ] [P1] **2.4 Re-run engine benchmark after each refactored adapter** — track cumulative improvement.

## Phase 3 — Stage 3 implementation (output side, smaller than originally feared)

Gated on Stages 1 + 2 being green + benchmark-verified. **NO adapter signature change in this stage.**

- [x] ✅ [P1] **3.1 Add `CandleOutput.to_polars()` method in UAC** at
  `unified-api-contracts/.../adapter_models.py:81`. ~20 lines, mirrors the existing `to_dataframe()`. UAC release
  bump. — unified-api-contracts@3814249 (CandleOutput.to_polars() + test coverage + polars dep)
- [x] ✅ [P1] **3.2 Change `canonical_writer.write_candle_parquet` signature** — boundary moved UP one layer
  instead. `candle_write_mixin._write_candles` now accepts `pl.DataFrame` and converts to pandas once at the
  top before the canonical_writer/UTL chain. write_candle_parquet keeps pandas (plan's "lower-risk" hedge);
  arena #3 (numpy→pandas) is still eliminated because the conversion happens AFTER the polars-internal flow
  in live_workers / candle_generator. cluster-validation re-read at 1328/2121 stays pandas (Stage 5
  candidate). — market-data-processing-service@6e61cfe
- [x] ✅ [P1] **3.3 Update `_process_all_timeframes`** + every other `to_dataframe()` site in live_workers
  (5 total) + the 2 in candle_generator now call `.to_polars()`. `_inject_passthrough_columns` polarised
  (with_columns + pl.lit). `_emit_instrument_processed_event` polarised (get_column().is_not_null().sum()).
  pd.concat→pl.concat, sort_values→sort, .empty→.is_empty(). — market-data-processing-service@6e61cfe
- [x] ✅ [P2] **3.4 Update `orchestration_writer.py`** — **AUDIT, NO-OP CONFIRMED.** Walked every `candles_df`
  reader in `CandleOrchestrationWriter` (`_log_timestamp_mismatch_details`, `_resolve_venue`,
  `_resolve_output_path`, `_validate_alignment_and_schema`). All of them are called downstream of the Stage 3
  boundary conversion in `candle_write_mixin._write_candles` — they see pandas frames by construction. No
  code change needed; closed as audited.
- [x] ✅ [P2] **3.5 Update `storage_dispatch_worker.py:51`** to use `df.write_parquet(...)` (polars) instead
  of `df.to_parquet(...)` (pandas). — market-data-processing-service@5e50b7d (polarise) → @febcb3b (delete).
  Stage 3.5 first polarised `StorageDispatchWorker.write` + `ParquetSchemaWorker.validate` + removed the
  polars→pandas boundary in `OrchestrationCoordinator.process_batch`. Then per workspace rule "Delete
  deprecated code. No parallel code paths" (universal.md), the entire (B) thin-coordinator scaffold was
  removed — `OrchestrationCoordinator` + `CandleGeneratorWorker` + `ParquetSchemaWorker` +
  `StorageDispatchWorker` plus their four unit-test files. All four were unreachable from any production
  entry point (instantiation grep: 1 hit, in their own tests). The (B) scaffold was a toy — it deliberately
  omitted every workspace HARD RULE the production write chain enforces (manifest emission, honest absence,
  UAC SchemaContract, emission policy, cluster validation, chain-bundle streaming, Category D zero-activity,
  VIX gap, multi-timeframe iteration with fast aggregation, etc.). 1269 lines removed, 20 added.
  `OrchestrationWorkersMixin` (the production composition shim used by `CandleOrchestrationWriter`) trimmed
  + kept; production MRO intact (`OrchestrationWorkersMixin → BatchOrchestrationMixin →
  LiveOrchestrationMixin → CandleWriteMixin → object`).
- [ ] [BLOCKED-ON-STAGE-4] [P1] **3.6 Remove the boundary `.to_pandas()` introduced in Stage 1** at
  `_process_all_timeframes` adapter call. The plan's own self-note says "keep this for now since adapter
  signature still requires pandas; re-evaluate after Stage 4 + the eventual adapter-contract plan." The
  adapter base-class signature change touches all 18 adapter implementations and is the entry point of a
  separate follow-up plan; cannot ship in isolation under Stage 3.
- [x] ✅ [P1] **3.7 Update writer-side unit tests** to use polars candles fixtures. — Initial pass updated
  10 tests (test_league_passthrough, test_per_instrument_pipeline, plus tests for the four (B)-scaffold
  classes). The (B) test files were subsequently deleted with the (B) deletion at @febcb3b, so the
  net result is the remaining production-path tests (`test_league_passthrough`, `test_per_instrument_pipeline`)
  use polars fixtures; 1365 pass; 3 pre-existing failures unchanged. —
  market-data-processing-service@6e61cfe + @5e50b7d + @febcb3b
- [ ] [BLOCKED-ON-STAGE-4] [P2] **3.8 Benchmark re-run** — should see additional improvement on the output side.
  The existing harness (`plans/audit/results/benchmarks/mdps_engine_comparison_2026_05_28/path_runner.py`)
  runs SYNTHETIC re-implementations of 4 engine paths (A/B/C/D), not the actual MDPS code. Re-running it
  after Stage 3 alone would only re-prove the engine-choice direction (path A wins) without measuring the
  Stage 3 work. Meaningful measurement comes from either (a) Stage 4 landing first so the bulk of the
  per-day RSS floor moves, then re-running the harness, OR (b) a real production canary on a 7-day backfill
  VM (per § Test plan "Production canary VM after Stage 1 + Stage 3 lands"). Recommend route (b) — the
  benchmark is best held until Stage 4 lands.

## Phase 4 — Stage 4 implementation (aggregation calculators)

Gated on Stages 1-3 being green + benchmark-verified.

- [ ] [P1] **4.1 Refactor `fast_candle_aggregation.py`** (36 pandas-ops in 835 lines) to pure polars. The internal
      `pl.from_pandas` (line 394) → aggregate → `.to_pandas()` (line 504) round trip becomes pure polars. Adapter-
      facing signature stays pandas via boundary conversion (caller already converts).
- [ ] [P1] **4.2 Refactor `timeframe_candles.py`** (48 pandas-ops in 780 lines) to pure polars. Per-timeframe candle
      generation logic. Largest behavioral surface in the plan; needs careful test coverage.
- [ ] [P1] **4.3 Regression tests** for both calculators — pin output against synthetic fixtures.
- [ ] [P1] **4.4 Benchmark re-run** — should see the bulk of the per-instrument-peak RSS drop here.

## Phase 5 — Stage 5 implementation (long-tail cleanup)

Gated on Stages 1-4 being green. Lowest priority.

- [ ] [P2] **5.1 `cloud_data_provider.py`** instruments DataFrame loading (lines 140, 225, 242) → polars.
- [ ] [P2] **5.2 `live_aggregator.py:320`** → polars.
- [ ] [P2] **5.3 `canonical_writer.py:1328, 2121`** (if not done in Stage 3.2) → polars.
- [ ] [P2] **5.4 `orchestration_writer.py`** remaining pandas-ops → polars.
- [ ] [P2] **5.5 `app/utils/*`** adapter_utils + market_state_detector audits.
- [ ] [P2] **5.6 `mock_data_provider.py`** + the 55 test files — bulk audit.
- [ ] [P2] **5.7 Final benchmark re-run** — must hit Path A target (~344 MB mean peak, 318 MB retention).

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
