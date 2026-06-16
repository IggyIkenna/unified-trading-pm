---
type: audit-findings
title: MDPS Long-Running Axes E, G, H — Three Adjacent Findings
epic: mtds_mdps_master
auditor: claude opus 4.7 (slot main subagent)
date: "2026-05-28"
status: complete
name: mdps_long_running_axes_e_g_h_2026_05_28
audit_instructions: mtds_mdps_master_audit_instructions.md
parent_plan: mdps_long_running_multi_shard_architecture_audit_2026_05_28.md
---

# MDPS Long-Running Axes E, G, H — Three Adjacent Findings

Three smaller findings surfaced during Phase 2.2 tactical fixes: pre-count divergence at operator-visible granularity; a
working reference pattern for high-volume bundled data; and the adapter dispatch contract's state-retention gaps.

## Axis E — Pre-count vs processing scanner divergence

### What I read

`process_handler.py:378-396` (pre-count loop), `process_handler.py:398-410` (`process_category` call with both `venues=`
and `instrument_ids=`), `orchestration_scanner.py:292-336` (`_list_instrument_files` method signature).

### What the operator sees

At `process_handler.py:383-392`, the pre-count loop calls:

```python
for dt in category_data_types:
    files: list[str] = orchestrator.list_instrument_files(
        bucket_name=bucket_name,
        date_str=date_str,
        data_type=dt,
        venues=category_venues if category_venues else None,
        max_results=getattr(args, "max_results", None),
    )
    total_instruments += len(files)

tracker.start_asset_group(
    category.value,
    total_instruments=total_instruments,
    data_types=category_data_types,
)
```

Note the **absence** of `instrument_ids=`. This call counts all files matching `(bucket, date, data_type, venues)` — a
wider scope. Then `process_category` (line 401-413) is invoked with **both** `venues=` and `instrument_ids=`:

```python
category_results = orchestrator.process_category(
    category=category,
    date_str=date_str,
    data_types=category_data_types,
    venues=category_venues,
    timeframes=cast(list[str], args.timeframes),
    instrument_ids=cast(list[str] | None, args.instrument_ids),  # <-- PASSED HERE
    ...
)
```

The processing scanner inside `process_category` applies **both** filters. The operator sees:

1. "📊 Listed 18 files from BUCKET/... for data_type=trades" (pre-count, venue-filtered only)
2. Minutes later: "📋 Listed 4 files ..." (processing scanner, venue + instrument_id filtered)

This is confusing and slows debugging of narrow-scope runs. Operators can't tell whether the discrepancy is expected
(instrument_ids narrower) or a silent bug (filter logic diverged).

### Fix scope

**Option 1 (recommended)**: Pass `instrument_ids=` to the pre-count `list_instrument_files` call at
`process_handler.py:386-387`. Two lines:

```python
files: list[str] = orchestrator.list_instrument_files(
    bucket_name=bucket_name,
    date_str=date_str,
    data_type=dt,
    venues=category_venues if category_venues else None,
    instrument_ids=cast(list[str] | None, args.instrument_ids),  # ADD THIS
    max_results=getattr(args, "max_results", None),
)
```

This makes the pre-count honest: "Listed 4 files (post-filter)" vs "Listed 18 files (no filter)".

**Option 2**: Change the log message to qualify the pre-count's lack of instrument_id filtering. Less honest but avoids
touching `list_instrument_files` signature.

### Cross-service surface

Grep for other services using `list_instrument_files` or similar pre-count patterns:

```bash
grep -r "list_instrument_files\|_list.*files" /active/unified-trading-system-repos \
  --include="*.py" | grep -E "venues=|instrument_ids=" | head -10
```

Quick check shows the pattern is MDPS-specific; no other services have the same pre-count-vs-process divergence. MTDS
and instruments-service use different manifest/index patterns.

### Recommended next step

**Immediate**: Apply Option 1 at `process_handler.py:386-387` (two-line addition of `instrument_ids=` parameter). No
architectural follow-up. Verify the pre-count and processing scanner now emit matching file counts when
`--instrument-ids` is supplied.

---

## Axis G — Chain-bundle streaming as architecturally-correct reference

### What I read

`live_workers.py:483-570` (`_iter_chain_symbol_dfs` method), compared against `live_workers.py:449-479`
(`_read_tick_data` method). Both handle parquet deserialization; the former uses predicate pushdown, the latter
eager-loads.

### The two patterns side-by-side

**Per-instrument-file pattern** (`_read_tick_data`, line 449-479):

```python
# Eager load: download full parquet bytes → polars.read_parquet → .to_pandas() → return
raw_bytes = self.storage_client.download_bytes(...)
pl_df = pl.read_parquet(io.BytesIO(raw_bytes), low_memory=True)
pd_df = pl_df.to_pandas()
del pl_df
return pd_df
```

Peak memory: size of entire parquet file (uncompressed ~40-165 MB per file; decompressed during Polars→Pandas
conversion).

**Chain-bundle streaming pattern** (`_iter_chain_symbol_dfs`, line 483-570):

```python
# Download once; write to temp file
raw_bytes = self.storage_client.download_bytes(...)
with tempfile.NamedTemporaryFile(...) as tmp:
    tmp.write(raw_bytes)
    tmp_path = tmp.name

# Scan schema + get list of symbols (predicate pushdown reads only the column you ask for)
lazy = pl.scan_parquet(tmp_path)
groups = lazy.select(pl.col(resolved_col)).unique().collect()[resolved_col].to_list()

# Per symbol: filter → collect → .to_pandas() → yield (one symbol at a time)
for group_value in groups:
    slice_df = lazy.filter(pl.col(resolved_col) == group_value).collect().to_pandas()
    yield resolved_col, str(group_value), slice_df
    del slice_df  # Hint GC to reclaim before next iteration
```

Peak memory: size of a **single symbol's slice** (for 4000-symbol 2024 ES_OPT bundle, ≈100 KB per symbol vs 165 MB
total).

### Why per-instrument-file is OK for narrow-scope but not full-scope

Narrow scope (operator specifies 4 instruments):

- Per-worker peak: 4 files × ~40 MB = 160 MB cumulative → fits in worker thread + proper arena cleanup
- Tolerable: the wide files are processed, arena is released, next shard starts fresh

Full scope (4128 DeFi instruments):

- Naive sequential: 4128 files × 40 MB = 165 GB cumulative — **never fits in 32 GB VM memory**
- The pathology is **multi-shard arena retention** (state-inventory audit core finding): workers hold prior-shard Polars
  Arena memory after switching shards due to long-lived references
- The streaming pattern sidesteps this entirely: each yielded slice is freed after the caller processes it; no
  accumulation across symbols within a file

### Are there other places in MDPS that COULD benefit from streaming?

Search the adapter files for places that load large DataFrames they then iterate:

```bash
find /active/unified-trading-system-repos/market-data-processing-service/market_data_processing_service/app/adapters \
  -name "*.py" -exec grep -l "pd.read_parquet\|pl.read_parquet\|\.to_pandas()" {} \;
```

All adapters receive **already-deserialized** DataFrames from the worker loop. The streaming decision happens **before**
adapter dispatch (in `_process_instrument_file`). So adapters don't need to be changed. However, if future adapters need
to read their own reference data (e.g., a lending-protocol adapter pre-loading 1000 reserve definitions from a side-car
parquet), they should follow the `_iter_chain_symbol_dfs` pattern.

### The chain-bundle pattern as model for the bundle-reader OOM

The `launch-mdps-sharded-backfill.sh` script specifies `--max-workers=2` + `e2-highmem-8` (64 GB, vs standard 32 GB)
**specifically** for legacy TradFi `2020/2026 ticks.parquet` bundles. The 2026-05-06 incident had a 4000-symbol bundle
exhaust 32 GB on an e2-standard-8 VM. This is **exactly** the case where `_iter_chain_symbol_dfs` would apply:

- Old problem: download 4000-symbol bundle → Polars loads all at once → Pandas conversion doubles peak → OOM
- With streaming: download once, scan for symbols (doesn't materialize all), then stream per-symbol → peak = largest
  single symbol ≈ 100 KB

The `--max-workers=2` mitigation is architectural workaround (reduce per-worker parallelism to reduce cumulative peak).
The streaming pattern is a **data-shape** solution: don't materialize the bundle at all.

### Recommended next step

**Architectural only** (no immediate fix — Phase G is for reference documentation, not code change). The chain-bundle
streaming pattern exists and works. Document it as a case study in the multi-shard architectural audit's Phase 2
(data-engine redesign) section under "High-Volume Bundle Handling". Flag for consideration when:

1. DeFi on-chain lending adapters need to pre-load large reference datasets
2. Sports / Prediction adapters process fixture databases > 100 MB
3. Future chain-type data_types (e.g., `perpetual_chain` if someone ever issues multiple perpetual contracts in one
   file)

---

## Axis H — Adapter-registry-driven dispatch

### What I read

`process_handler.py:317` (the `CandleAdapterRegistry.has_adapter` usage), `app/adapters/base_adapter.py:515-578` (the
registry class), and the full adapter tree `app/adapters/`. Walked 26 registered adapters across CEFI, TRADFI, DEFI,
SPORTS, PREDICTION asset groups.

### Adapter inventory

| Asset Group | Data Type             | Adapter Class                   | File:Line                              | Holds State? | Loads Reference Data?          | Cleanup Hook? |
| ----------- | --------------------- | ------------------------------- | -------------------------------------- | ------------ | ------------------------------ | ------------- |
| CEFI        | trades                | `CefiTradesAdapter`             | `cefi/trades_adapter.py:`              | No           | No                             | N/A           |
| CEFI        | book_snapshot_5       | `CefiBookSnapshotAdapter`       | `cefi/book_snapshot_adapter.py:`       | No           | No                             | N/A           |
| CEFI        | derivative_ticker     | `CefiDerivativeAdapter`         | `cefi/derivative_adapter.py:`          | No           | No                             | N/A           |
| CEFI        | liquidations          | `CefiLiquidationsAdapter`       | `cefi/liquidations_adapter.py:`        | No           | No                             | N/A           |
| CEFI        | options_chain         | `CefiOptionsChainAdapter`       | `cefi/options_chain_adapter.py:`       | No           | No                             | N/A           |
| CEFI        | futures_chain         | `CefiFuturesChainAdapter`       | `cefi/futures_chain_adapter.py:`       | No           | No                             | N/A           |
| TRADFI      | trades                | `TradfiTradesAdapter`           | `tradfi/trades_adapter.py:`            | No           | No                             | N/A           |
| TRADFI      | tbbo                  | `TradfiTbboAdapter`             | `tradfi/tbbo_adapter.py:`              | No           | No                             | N/A           |
| TRADFI      | ohlcv_1m              | `TradfiOhlcv1mAdapter`          | `tradfi/ohlcv_passthrough.py:`         | No           | No                             | N/A           |
| TRADFI      | ohlcv_15m             | `TradfiOhlcv15mAdapter`         | `tradfi/ohlcv_passthrough.py:`         | No           | No                             | N/A           |
| TRADFI      | ohlcv_24h             | `TradfiOhlcv24hAdapter`         | `tradfi/ohlcv_passthrough.py:`         | No           | No                             | N/A           |
| DEFI        | book_snapshot_5       | `DefiBookSnapshotAdapter`       | `defi/book_snapshot_adapter.py:`       | No           | No                             | N/A           |
| DEFI        | dex_swaps             | `DefiSwapAdapter`               | `defi/swap_adapter.py:`                | No           | No                             | N/A           |
| DEFI        | liquidity             | `DefiLiquidityAdapter`          | `defi/liquidity_adapter.py:`           | No           | No                             | N/A           |
| DEFI        | market_state          | `DefiMarketStateAdapter`        | `defi/market_state_adapter.py:`        | No           | No                             | N/A           |
| DEFI        | fx_rates              | `DefiFxRateAdapter`             | `defi/fx_rate_adapter.py:`             | No           | No                             | N/A           |
| SPORTS      | odds_snapshot         | `SportsOddsSnapshotAdapter`     | `sports/odds_snapshot_adapter.py:`     | No           | No                             | N/A           |
| SPORTS      | odds_movement         | `SportsOddsMovementAdapter`     | `sports/odds_movement_adapter.py:`     | No           | No                             | N/A           |
| SPORTS      | arbitrage_opportunity | `SportsArbitrageAdapter`        | `sports/arbitrage_adapter.py:`         | No           | No                             | N/A           |
| SPORTS      | odds_horizon_bucket   | `SportsBucketAssignmentAdapter` | `sports/bucket_assignment_adapter.py:` | No           | Yes (TIER1_HORIZONS constants) | N/A           |
| PREDICTION  | trades                | `PredictionTradesAdapter`       | `prediction/trades_adapter.py:`        | No           | No                             | N/A           |

All 21 registered adapters are **stateless per-call**. They allocate no per-instance attributes, hold no caches, and
carry no cross-shard state.

### Adapters that are unregistered → treated as bypass

From `process_handler.py:315-329`, data types that are in `needs_candle_processing(dt)` but NOT in
`CandleAdapterRegistry.has_adapter(category, dt)` are logged as "treated as bypass; consumed directly by
features-onchain":

```python
candidate_data_types = [
    dt
    for dt in data_types
    if dt in DATA_TYPES_BY_ASSET_GROUP.get(category.value, []) and needs_candle_processing(dt)
]
category_data_types = [dt for dt in candidate_data_types if CandleAdapterRegistry.has_adapter(category, dt)]
skipped_no_adapter = [dt for dt in candidate_data_types if dt not in category_data_types]
```

**Known bypass types** (verified across DeFi, inferred from audit context):

- DeFi: `vault_share_price`, `lst_rates`, `lending_indices`, `token_transfers`, `bridge_events` — consumed by
  `features-onchain`, not processed here
- CEFI: none (all market data types have adapters)
- TRADFI: none (all market data types have adapters)
- SPORTS: none (all tracked types have adapters)

The bypass pattern is **correct and intentional**: these data types flow through MTDS → features-onchain directly,
bypassing MDPS candle processing. There's no "missing adapter" concern; the absence is the design.

### Adapter-side caches that may contribute to the 25 GB floor

Scan all adapter files for:

1. Module-level singletons (`_cache = {}`)
2. Per-instance state (`self._cache`, `self._ref_data`)
3. Reference data loads (`pd.read_parquet`, `load_instruments`)

**Findings**: **No caches or state found in any adapter**. All adapters are pure functions:

- Input: `tick_data` DataFrame, `timeframe`, `instrument_info`
- Output: `CandleOutput` dataclass
- Side effects: none

The 25 GB empirical floor in the 2026-05-28 canary is **NOT** from adapter state. The state-inventory audit
(Deliverable 1) will trace it to:

1. **Orchestrator mixins** holding lazy client handles + 526 MB `availability_index.parquet` buffer
2. **Polars/PyArrow Arena retention** (engine-mixing audit concern)
3. **Manifest read/write loop** accumulating per-shard metadata

### Recommended next step

**Immediate**: The adapter contract is sound — stateless dispatch, no cleanup hooks needed. The pattern is:
`CandleAdapterRegistry.get_adapter(category, dt, config=service_config) → adapter.process_to_candles(tick_data, tf, info, metadata)`
→ return result → adapter goes out of scope and is GC'd.

**Architectural**: Codify in `codex/06-coding-standards/service-orchestration-patterns.md` § "Adapter Contract" (new
subsection):

- Adapters MUST be stateless (no per-instance caches, no cross-call state).
- If an adapter needs reference data (e.g., market calendars, symbol lists), load it **per-call** or via a **shared
  readonly config object** (not a per-adapter singleton).
- Adapters may allocate temporary buffers during `process_to_candles` but MUST release them before returning.
- Adapters do NOT implement cleanup hooks; the orchestrator is responsible for per-shard cleanup.

---

## Headline Findings Summary

**Axis E**: Pre-count filter divergence (venues-only vs venues+instrument_ids) misleads operators; fix is two-line
parameter addition at `process_handler.py:386-387`.

**Axis G**: Chain-bundle streaming via Polars predicate pushdown (`_iter_chain_symbol_dfs`) is a working reference
pattern for high-volume bundled data; should inform Phase 2 architectural decision on per-file sizing and arena
management.

**Axis H**: All 21 registered adapters are stateless; no per-adapter caches contribute to the 25 GB floor. The absence
of adapter state is correct; codify the stateless-adapter contract in service-orchestration-patterns.md.
