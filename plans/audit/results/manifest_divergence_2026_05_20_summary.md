# A3 — Manifest divergence summary

_Generated: 2026-05-20T10:27:50.349615+00:00_

Window: 2020-01-01 → 2026-05-20

Total joined cells: 1,229,844

Output parquet: `plans/audit/results/manifest_divergence_2026_05_20.parquet` (0.48 MiB)

## Classification breakdown (workspace-wide)

| Classification | Cells | % | Status |
|---|---:|---:|---|
| `OK_OUT_OF_SCOPE` | 800,756 | 65.11% | ✅ honest |
| `MISSING_EXPECTED` | 236,892 | 19.26% | ❌ review-blocking (silent gap) |
| `OK_NOT_YET_LIVE` | 118,999 | 9.68% | ✅ honest |
| `OK_CAPTURED` | 44,955 | 3.66% | ✅ honest |
| `ATTEMPTED_FAILED` | 18,753 | 1.52% | ⚠️ review per-row |
| `OK_HONEST_EMPTY` | 6,796 | 0.55% | ✅ honest |
| `UNEXPECTED_CAPTURED` | 1,928 | 0.16% | ⚠️ data on a date the oracle said empty |
| `DIVERGENT_EMPTY` | 765 | 0.06% | ❌ review-blocking (Drift-bug class) |

## Per-asset-group breakdown


### cefi

| Classification | Cells |
|---|---:|
| `OK_OUT_OF_SCOPE` | 89,651 |
| `OK_CAPTURED` | 33,954 |
| `ATTEMPTED_FAILED` | 17,207 |
| `MISSING_EXPECTED` | 16,171 |
| `OK_NOT_YET_LIVE` | 11,956 |

### defi

| Classification | Cells |
|---|---:|
| `OK_OUT_OF_SCOPE` | 651,944 |
| `MISSING_EXPECTED` | 184,512 |
| `OK_NOT_YET_LIVE` | 106,223 |
| `DIVERGENT_EMPTY` | 765 |

### prediction

| Classification | Cells |
|---|---:|
| `MISSING_EXPECTED` | 3,442 |
| `OK_NOT_YET_LIVE` | 820 |
| `OK_OUT_OF_SCOPE` | 404 |
| `OK_CAPTURED` | 402 |

### sports

| Classification | Cells |
|---|---:|
| `OK_OUT_OF_SCOPE` | 33,034 |
| `MISSING_EXPECTED` | 25,652 |

### tradfi

| Classification | Cells |
|---|---:|
| `OK_OUT_OF_SCOPE` | 25,723 |
| `OK_CAPTURED` | 10,599 |
| `MISSING_EXPECTED` | 7,115 |
| `OK_HONEST_EMPTY` | 6,796 |
| `UNEXPECTED_CAPTURED` | 1,928 |
| `ATTEMPTED_FAILED` | 1,546 |

## Top divergent (venue, data_type) per asset_group (review-blocking list)


### cefi

| Venue | Data type | Classification | Cells |
|---|---|---|---:|
| OKX | derivative_ticker | `MISSING_EXPECTED` | 2,332 |
| OKX | book_snapshot_5 | `MISSING_EXPECTED` | 2,332 |
| COINBASE | book_snapshot_5 | `MISSING_EXPECTED` | 2,332 |
| COINBASE | trades | `MISSING_EXPECTED` | 2,332 |
| OKX | trades | `MISSING_EXPECTED` | 2,332 |
| OKX | liquidations | `MISSING_EXPECTED` | 2,332 |
| BINANCE-FUTURES | futures_chain | `ATTEMPTED_FAILED` | 2,309 |
| DERIBIT | futures_chain | `ATTEMPTED_FAILED` | 2,286 |
| DERIBIT | options_chain | `ATTEMPTED_FAILED` | 2,283 |
| BYBIT | futures_chain | `ATTEMPTED_FAILED` | 2,083 |
| DERIBIT | liquidations | `ATTEMPTED_FAILED` | 1,819 |
| HYPERLIQUID | liquidations | `ATTEMPTED_FAILED` | 916 |
| BINANCE-FUTURES | book_snapshot_5 | `ATTEMPTED_FAILED` | 669 |
| BYBIT | book_snapshot_5 | `ATTEMPTED_FAILED` | 589 |
| ASTER | trades | `ATTEMPTED_FAILED` | 563 |
| ASTER | liquidations | `ATTEMPTED_FAILED` | 563 |
| ASTER | derivative_ticker | `ATTEMPTED_FAILED` | 563 |
| ASTER | book_snapshot_5 | `ATTEMPTED_FAILED` | 563 |
| UPBIT | book_snapshot_5 | `MISSING_EXPECTED` | 450 |
| UPBIT | trades | `MISSING_EXPECTED` | 450 |

### defi

| Venue | Data type | Classification | Cells |
|---|---|---|---:|
| FLUID-ETHEREUM | position_data | `MISSING_EXPECTED` | 2,332 |
| FLUID-ETHEREUM | risk_params | `MISSING_EXPECTED` | 2,332 |
| FLUID-ETHEREUM | liquidation_events | `MISSING_EXPECTED` | 2,332 |
| FLUID-ETHEREUM | lending_indices | `MISSING_EXPECTED` | 2,332 |
| MORPHO-ETHEREUM | lending_indices | `MISSING_EXPECTED` | 2,332 |
| MORPHO-ETHEREUM | liquidation_events | `MISSING_EXPECTED` | 2,332 |
| MORPHO-ETHEREUM | position_data | `MISSING_EXPECTED` | 2,332 |
| MORPHO-ETHEREUM | risk_params | `MISSING_EXPECTED` | 2,332 |
| CURVE-ETHEREUM | dex_swaps | `MISSING_EXPECTED` | 2,314 |
| CURVE-ETHEREUM | dex_pools | `MISSING_EXPECTED` | 2,314 |
| BALANCER-ETHEREUM | dex_pools | `MISSING_EXPECTED` | 2,242 |
| BALANCER-ETHEREUM | dex_swaps | `MISSING_EXPECTED` | 2,242 |
| UNISWAPV2-ETHEREUM | dex_pools | `MISSING_EXPECTED` | 2,207 |
| UNISWAPV2-ETHEREUM | dex_swaps | `MISSING_EXPECTED` | 2,207 |
| BALANCER-POLYGON | dex_pools | `MISSING_EXPECTED` | 2,182 |
| MORPHO-POLYGON | lending_indices | `MISSING_EXPECTED` | 2,182 |
| MORPHO-POLYGON | liquidation_events | `MISSING_EXPECTED` | 2,182 |
| MORPHO-POLYGON | position_data | `MISSING_EXPECTED` | 2,182 |
| MORPHO-POLYGON | risk_params | `MISSING_EXPECTED` | 2,182 |
| BALANCER-POLYGON | dex_swaps | `MISSING_EXPECTED` | 2,182 |

### prediction

| Venue | Data type | Classification | Cells |
|---|---|---|---:|
| KALSHI | trades | `MISSING_EXPECTED` | 1,756 |
| POLYMARKET | trades | `MISSING_EXPECTED` | 1,686 |

### sports

| Venue | Data type | Classification | Cells |
|---|---|---|---:|
| BET365 | odds_movement | `MISSING_EXPECTED` | 2,332 |
| BET365 | odds_snapshot | `MISSING_EXPECTED` | 2,332 |
| BETFAIR | odds_movement | `MISSING_EXPECTED` | 2,332 |
| BETFAIR | odds_snapshot | `MISSING_EXPECTED` | 2,332 |
| DRAFTKINGS | odds_movement | `MISSING_EXPECTED` | 2,332 |
| DRAFTKINGS | odds_snapshot | `MISSING_EXPECTED` | 2,332 |
| FANDUEL | odds_movement | `MISSING_EXPECTED` | 2,332 |
| FANDUEL | odds_snapshot | `MISSING_EXPECTED` | 2,332 |
| ODDS_API | odds | `MISSING_EXPECTED` | 2,332 |
| PINNACLE | odds_movement | `MISSING_EXPECTED` | 2,332 |
| PINNACLE | odds_snapshot | `MISSING_EXPECTED` | 2,332 |

### tradfi

| Venue | Data type | Classification | Cells |
|---|---|---|---:|
| ICE | tbbo | `MISSING_EXPECTED` | 1,254 |
| ICE | trades | `MISSING_EXPECTED` | 1,238 |
| CME | tbbo | `MISSING_EXPECTED` | 1,188 |
| YAHOO_FINANCE | ohlcv_15m | `MISSING_EXPECTED` | 938 |
| NYSE | ohlcv_1m | `MISSING_EXPECTED` | 839 |
| NASDAQ | ohlcv_1m | `MISSING_EXPECTED` | 839 |
| YAHOO_FINANCE | ohlcv_24h | `ATTEMPTED_FAILED` | 830 |
| YAHOO_FINANCE | ohlcv_24h | `MISSING_EXPECTED` | 754 |
| YAHOO_FINANCE | ohlcv_15m | `ATTEMPTED_FAILED` | 667 |
| CME | tbbo | `ATTEMPTED_FAILED` | 22 |
| ICE | ohlcv_1m | `MISSING_EXPECTED` | 14 |
| NYSE | ohlcv_1m | `ATTEMPTED_FAILED` | 14 |
| CBOE | ohlcv_15m | `MISSING_EXPECTED` | 14 |
| FX | ohlcv_24h | `MISSING_EXPECTED` | 13 |
| CME | ohlcv_1m | `MISSING_EXPECTED` | 12 |
| FX | ohlcv_24h | `ATTEMPTED_FAILED` | 12 |
| CME | trades | `MISSING_EXPECTED` | 12 |
| NASDAQ | ohlcv_1m | `ATTEMPTED_FAILED` | 1 |

## Notes

- A2 oracle has known gaps (sports off-seasons + DeFi protocol pauses not yet encoded). Cells classified as `SHOULD_HAVE_DATA` in those domains may actually be honest empties.
- `DIVERGENT_EMPTY` is the highest-priority class — these are likely silent adapter bugs (the Drift S3 class). Each (venue, data_type) row above should be inspected for the source of the empty.
- `MISSING_EXPECTED` indicates a silent gap (the adapter never emitted a manifest row at all). Either the venue's date enumerator skipped these cells, or the orchestrator scope doesn't enumerate them.
- `ATTEMPTED_FAILED` is per-row noise unless concentrated on specific (venue, data_type) pairs — check the `error_reason` column in the parquet for the failure taxonomy.
- Buckets read: `market-data-tick-{cefi,defi,tradfi,sports,pred}-prd-central-element-323112` (one `_index/availability_index.parquet` each — single-walk discipline).
