---
doc_type: plan
title: granularity-per-category-config
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-data-processing-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-14'
overview: Declare base granularity per category/data_type in UAC; MDPS uses it for smart aggregation and timeframe validation
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-api-contracts, code: C2, deployment: none, business: none}
- {repo: market-data-processing-service, code: C2, deployment: none, business: none}
- {repo: unified-trading-library, code: C2, deployment: none, business: none}
depends_on: []
todos:
- {id: uac-base-granularity-registry, content: '- [x] [AGENT] P0. Add BASE_GRANULARITY_BY_DATA_TYPE dict to UAC registry/market_data_categories.py

    ', status: done, note: Added 22-entry dict + TIMEFRAME_SECONDS + get_valid_timeframes_for_data_type()}
- {id: uac-valid-timeframes-per-category, content: '- [x] [AGENT] P0. Add get_valid_timeframes_for_data_type() to UAC registry/market_data_categories.py

    ', status: done, note: Function filters TIMEFRAMES to only those >= base granularity}
- {id: mdps-adapter-base-granularity, content: '- [x] [AGENT] P1. Add base_granularity field to BaseCandleAdapter + get_base_granularity() + get_valid_output_timeframes()

    ', status: done, note: TradFi adapters set explicit base_granularity; others use UAC fallback via get_base_granularity()}
- {id: mdps-smart-aggregation-use-registry, content: '- [x] [AGENT] P1. Update _process_all_timeframes to filter via adapter.get_valid_output_timeframes()

    ', status: done, note: Skips timeframes finer than base granularity with log message}
- {id: mdps-timeframe-validation, content: '- [x] [AGENT] P1. Timeframe validation integrated into _process_all_timeframes

    ', status: done, note: Merged with smart-aggregation-use-registry — single call site}
- {id: utl-manifest-timeframe-field, content: '- [x] [AGENT] P2. Add timeframe field to AvailabilityRecord in UTL manifest_writer.py

    ', status: done, note: 'Added to AvailabilityRecord, add(), write(), and _merge_dataframes dedup key'}
- {id: mdps-incremental-timeframe-backfill, content: '- [x] [AGENT] P2. Support incremental timeframe addition — detect missing timeframes in existing shards

    ', status: done, note: 'Manifest writes per data_type:timeframe records; freshness check compares against requested timeframes'}
- {id: qg-validation, content: '- [x] [AGENT] P0. Run quality-gates.sh on all 3 affected repos

    ', status: done, note: 'MDPS: 1003 tests pass, 2 pre-existing violations (os.getenv, pip-audit). UTL: 1 pre-existing codex violation. UAC: pre-existing __all__ sort.'}
isProject: false
---

# Granularity-Per-Category Config

## Context

Currently, MDPS applies the same 7 timeframes (`15s, 1m, 5m, 15m, 1h, 4h, 24h`) globally to all categories. This is
incorrect: TradFi OHLCV data starts from 1m/15m/24h (no tick data), DeFi block times vary by chain (12s ETH, 2s
Arbitrum, 0.4s Solana), and CeFi/Prediction have sub-second ticks. Requesting 15s candles from `ohlcv_15m` source data
produces NaN-filled garbage.

Smart aggregation (compute base, aggregate up) was added in this session but hardcodes the assumption that the first
sorted timeframe is the base. It should use the adapter's declared base granularity.

### Current State (from audit)

| Component                                 | Current                                          | Gap                                  |
| ----------------------------------------- | ------------------------------------------------ | ------------------------------------ |
| UAC `TIMEFRAMES`                          | Global `["15s"..."24h"]`                         | No per-category/data_type variance   |
| UAC `DATA_TYPES_BY_CATEGORY`              | Lists data types per category                    | No granularity metadata              |
| `GranularityDetector._NATIVE_GRANULARITY` | Hardcoded dict for `ohlcv_*` types only          | Missing DeFi, Prediction, Sports     |
| `BaseCandleAdapter`                       | `supported_timeframes = ["15s"..."24h"]` for all | No `base_granularity` field          |
| `AvailabilityRecord`                      | `data_type` field, no `timeframe`                | Can't track per-timeframe completion |
| MDPS `_process_all_timeframes`            | Sorts timeframes, uses first as base             | Should use adapter.base_granularity  |

### Design

```
UAC (SSOT)                          MDPS (consumer)
+---------------------------------+ +----------------------------------+
| BASE_GRANULARITY_BY_DATA_TYPE   | | BaseCandleAdapter                |
|   trades -> 15s                 | |   base_granularity: str          |
|   ohlcv_1m -> 1m               | |   (from UAC or class override)   |
|   ohlcv_15m -> 15m             | |                                  |
|   prediction_trades -> 15s     | | _process_all_timeframes:         |
|   lending_indices -> 15m (ETH) | |   skip tf < base_granularity     |
|   oracle_prices -> 15m (ETH)   | |   compute base from ticks        |
|   sports_odds -> horizon       | |   aggregate up for larger tfs    |
+---------------------------------+ +----------------------------------+

UTL (manifest)
+---------------------------------+
| AvailabilityRecord              |
|   + timeframe: str              |
|   dedup key: (date, venue,      |
|     service, data_type,         |
|     timeframe)                  |
+---------------------------------+
```

### Execution DAG

```
Phase 1 (PARALLEL):
  [uac-base-granularity-registry] ─┐
  [uac-valid-timeframes-per-category] ─┤
                                       ├─ QG: unified-api-contracts
Phase 2 (PARALLEL, after Phase 1):     │
  [mdps-adapter-base-granularity] ─────┤
  [mdps-smart-aggregation-use-registry]─┤
  [mdps-timeframe-validation] ─────────┤
                                       ├─ QG: market-data-processing-service
Phase 3 (SEQUENTIAL, after Phase 2):   │
  [utl-manifest-timeframe-field] ──────┤
  [mdps-incremental-timeframe-backfill]─┤
                                       ├─ QG: unified-trading-library + MDPS
Phase 4:
  [qg-validation] ── all 3 repos
```

## Pre-Audit Manifest

| Repo                           | File                                        | Symbol/Pattern                           | Action                                                              |
| ------------------------------ | ------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------- |
| unified-api-contracts          | `registry/market_data_categories.py`        | `TIMEFRAMES` (global list)               | Add `BASE_GRANULARITY_BY_DATA_TYPE`, `VALID_TIMEFRAMES_BY_CATEGORY` |
| market-data-processing-service | `app/adapters/base_adapter.py`              | `BaseCandleAdapter.supported_timeframes` | Add `base_granularity: str` field                                   |
| market-data-processing-service | `app/adapters/cefi/trades_adapter.py`       | `CefiTradesAdapter`                      | Set `base_granularity = "15s"`                                      |
| market-data-processing-service | `app/adapters/prediction/trades_adapter.py` | `PredictionTradesAdapter`                | Set `base_granularity = "15s"`                                      |
| market-data-processing-service | `app/adapters/tradfi/ohlcv_passthrough.py`  | `TradfiOhlcv1mAdapter`                   | Set `base_granularity = "1m"`                                       |
| market-data-processing-service | `app/adapters/tradfi/ohlcv_passthrough.py`  | `TradfiOhlcv15mAdapter`                  | Set `base_granularity = "15m"`                                      |
| market-data-processing-service | `app/adapters/tradfi/ohlcv_passthrough.py`  | `TradfiOhlcv24hAdapter`                  | Set `base_granularity = "24h"`                                      |
| market-data-processing-service | `app/adapters/defi/*.py`                    | DeFi adapters                            | Set `base_granularity` per chain/protocol                           |
| market-data-processing-service | `app/core/live_workers.py`                  | `_process_all_timeframes`                | Use `adapter.base_granularity` instead of sorted_tfs[0]             |
| market-data-processing-service | `app/core/granularity_detector.py`          | `_NATIVE_GRANULARITY`                    | Extend or replace with adapter-declared values                      |
| unified-trading-library        | `manifest_writer.py`                        | `AvailabilityRecord`                     | Add `timeframe: str` field, update dedup key                        |
| unified-trading-library        | `manifest_writer.py`                        | `check_shard_freshness()`                | Support per-timeframe freshness checks                              |

## Success Criteria

- **Phase 1**: UAC QG passes. `BASE_GRANULARITY_BY_DATA_TYPE` has entries for all 15+ data types across 5 categories.
- **Phase 2**: MDPS QG passes. `_process_all_timeframes` skips timeframes finer than base. TradFi `ohlcv_15m` only
  generates `15m, 1h, 4h, 24h` (not 15s, 1m, 5m).
- **Phase 3**: UTL QG passes. Manifest tracks per-timeframe. Incremental backfill can add missing timeframes without
  reprocessing existing ones.
- **Phase 4**: All 3 repo QGs pass. No regressions.

## Impact

- **Prediction**: No change (already correct — ticks support all 7 timeframes)
- **CeFi**: No change (ticks support all 7 timeframes)
- **TradFi**: Stops generating garbage 15s/1m candles from 15m source. Only valid aggregations.
- **DeFi**: Declares per-chain base granularity. ETH ~12s blocks can support 15s candles; Arbitrum ~0.25s supports all.
- **Sports**: Uses horizon-based buckets, not standard timeframes. Validates correctly.
