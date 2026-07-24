---
doc_type: audit-result
title: A3 — Manifest divergence summary
summary:
  A3 divergence join of the expected_coverage() oracle against 5 MTDS prod manifest indexes (1,211,278 cells) — 214,344
  MISSING_EXPECTED (17.70%, silent gaps) + 765 DIVERGENT_EMPTY (Drift-bug class); top offenders are DeFi lending/dex
  venues (MORPHO/FLUID/CURVE), all sports bookmakers, and OKX/COINBASE cefi.
status: fail
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [audit, manifest, data-correctness, honest-coverage, single-walk, defi, data-status]
related:
  [
    /plans/audit/results/archive/expected_coverage_dump_2026_05_20_summary.md,
    /plans/audit/results/archive/manifest_divergence_all_services_2026_05_20_summary.md,
    /plans/audit/results/archive/phase7c_divergent_empty_triage_2026_05_21_summary.md,
  ]
created: 2026-05-20
audited_scope:
  Full join of expected_coverage() oracle vs the 5 MTDS prod _index/availability_index.parquet manifests
  (cefi/defi/tradfi/sports/pred), 2020-01-01→2026-05-20; per-cell classification + top divergent (venue, data_type) per
  asset_group (single-walk, one index each)
date: 2026-05-20
auditor: semver
parent_epic: manifest_master
severity: P0
resulting_plan:
lib_version:
doc_versions_checked:
---

# A3 — Manifest divergence summary

_Generated: 2026-05-21T07:07:18.277355+00:00_

Window: 2020-01-01 → 2026-05-20

Total joined cells: 1,211,278

Output parquet: `plans/audit/results/manifest_divergence_2026_05_20.parquet` (0.48 MiB)

## Classification breakdown (workspace-wide)

| Classification        |   Cells |      % | Status                                  |
| --------------------- | ------: | -----: | --------------------------------------- |
| `OK_OUT_OF_SCOPE`     | 791,518 | 65.35% | ✅ honest                               |
| `MISSING_EXPECTED`    | 214,344 | 17.70% | ❌ review-blocking (silent gap)         |
| `OK_NOT_YET_LIVE`     | 117,557 |  9.71% | ✅ honest                               |
| `OK_CAPTURED`         |  54,193 |  4.47% | ✅ honest                               |
| `ATTEMPTED_FAILED`    |  18,753 |  1.55% | ⚠️ review per-row                       |
| `OK_HONEST_EMPTY`     |  12,220 |  1.01% | ✅ honest                               |
| `UNEXPECTED_CAPTURED` |   1,928 |  0.16% | ⚠️ data on a date the oracle said empty |
| `DIVERGENT_EMPTY`     |     765 |  0.06% | ❌ review-blocking (Drift-bug class)    |

## Per-asset-group breakdown

### cefi

| Classification     |  Cells |
| ------------------ | -----: |
| `OK_OUT_OF_SCOPE`  | 89,651 |
| `OK_CAPTURED`      | 33,954 |
| `ATTEMPTED_FAILED` | 17,207 |
| `MISSING_EXPECTED` | 16,171 |
| `OK_NOT_YET_LIVE`  | 11,956 |

### defi

| Classification     |   Cells |
| ------------------ | ------: |
| `OK_OUT_OF_SCOPE`  | 651,944 |
| `MISSING_EXPECTED` | 181,290 |
| `OK_NOT_YET_LIVE`  | 104,781 |
| `OK_HONEST_EMPTY`  |   4,664 |
| `DIVERGENT_EMPTY`  |     765 |

### prediction

| Classification     | Cells |
| ------------------ | ----: |
| `MISSING_EXPECTED` | 3,442 |
| `OK_NOT_YET_LIVE`  |   820 |
| `OK_OUT_OF_SCOPE`  |   404 |
| `OK_CAPTURED`      |   402 |

### sports

| Classification     |  Cells |
| ------------------ | -----: |
| `OK_OUT_OF_SCOPE`  | 23,796 |
| `OK_CAPTURED`      |  9,238 |
| `MISSING_EXPECTED` |  6,326 |
| `OK_HONEST_EMPTY`  |    760 |

### tradfi

| Classification        |  Cells |
| --------------------- | -----: |
| `OK_OUT_OF_SCOPE`     | 25,723 |
| `OK_CAPTURED`         | 10,599 |
| `MISSING_EXPECTED`    |  7,115 |
| `OK_HONEST_EMPTY`     |  6,796 |
| `UNEXPECTED_CAPTURED` |  1,928 |
| `ATTEMPTED_FAILED`    |  1,546 |

## Top divergent (venue, data_type) per asset_group (review-blocking list)

### cefi

| Venue           | Data type         | Classification     | Cells |
| --------------- | ----------------- | ------------------ | ----: |
| OKX             | book_snapshot_5   | `MISSING_EXPECTED` | 2,332 |
| OKX             | trades            | `MISSING_EXPECTED` | 2,332 |
| OKX             | liquidations      | `MISSING_EXPECTED` | 2,332 |
| COINBASE        | book_snapshot_5   | `MISSING_EXPECTED` | 2,332 |
| COINBASE        | trades            | `MISSING_EXPECTED` | 2,332 |
| OKX             | derivative_ticker | `MISSING_EXPECTED` | 2,332 |
| BINANCE-FUTURES | futures_chain     | `ATTEMPTED_FAILED` | 2,309 |
| DERIBIT         | futures_chain     | `ATTEMPTED_FAILED` | 2,286 |
| DERIBIT         | options_chain     | `ATTEMPTED_FAILED` | 2,283 |
| BYBIT           | futures_chain     | `ATTEMPTED_FAILED` | 2,083 |
| DERIBIT         | liquidations      | `ATTEMPTED_FAILED` | 1,819 |
| HYPERLIQUID     | liquidations      | `ATTEMPTED_FAILED` |   916 |
| BINANCE-FUTURES | book_snapshot_5   | `ATTEMPTED_FAILED` |   669 |
| BYBIT           | book_snapshot_5   | `ATTEMPTED_FAILED` |   589 |
| ASTER           | book_snapshot_5   | `ATTEMPTED_FAILED` |   563 |
| ASTER           | trades            | `ATTEMPTED_FAILED` |   563 |
| ASTER           | liquidations      | `ATTEMPTED_FAILED` |   563 |
| ASTER           | derivative_ticker | `ATTEMPTED_FAILED` |   563 |
| UPBIT           | book_snapshot_5   | `MISSING_EXPECTED` |   450 |
| UPBIT           | trades            | `MISSING_EXPECTED` |   450 |

### defi

| Venue               | Data type          | Classification     | Cells |
| ------------------- | ------------------ | ------------------ | ----: |
| MORPHO-ETHEREUM     | lending_indices    | `MISSING_EXPECTED` | 2,332 |
| MORPHO-ETHEREUM     | liquidation_events | `MISSING_EXPECTED` | 2,332 |
| MORPHO-ETHEREUM     | position_data      | `MISSING_EXPECTED` | 2,332 |
| MORPHO-ETHEREUM     | risk_params        | `MISSING_EXPECTED` | 2,332 |
| FLUID-ETHEREUM      | risk_params        | `MISSING_EXPECTED` | 2,332 |
| FLUID-ETHEREUM      | position_data      | `MISSING_EXPECTED` | 2,332 |
| FLUID-ETHEREUM      | liquidation_events | `MISSING_EXPECTED` | 2,332 |
| FLUID-ETHEREUM      | lending_indices    | `MISSING_EXPECTED` | 2,332 |
| CURVE-ETHEREUM      | dex_swaps          | `MISSING_EXPECTED` | 2,314 |
| CURVE-ETHEREUM      | dex_pools          | `MISSING_EXPECTED` | 2,314 |
| BALANCER-ETHEREUM   | dex_swaps          | `MISSING_EXPECTED` | 2,242 |
| BALANCER-ETHEREUM   | dex_pools          | `MISSING_EXPECTED` | 2,242 |
| UNISWAP_V2-ETHEREUM | dex_pools          | `MISSING_EXPECTED` | 2,207 |
| UNISWAP_V2-ETHEREUM | dex_swaps          | `MISSING_EXPECTED` | 2,207 |
| MORPHO-POLYGON      | liquidation_events | `MISSING_EXPECTED` | 2,182 |
| MORPHO-POLYGON      | lending_indices    | `MISSING_EXPECTED` | 2,182 |
| MORPHO-POLYGON      | position_data      | `MISSING_EXPECTED` | 2,182 |
| MORPHO-POLYGON      | risk_params        | `MISSING_EXPECTED` | 2,182 |
| BALANCER-POLYGON    | dex_swaps          | `MISSING_EXPECTED` | 2,182 |
| BALANCER-POLYGON    | dex_pools          | `MISSING_EXPECTED` | 2,182 |

### prediction

| Venue      | Data type | Classification     | Cells |
| ---------- | --------- | ------------------ | ----: |
| KALSHI     | trades    | `MISSING_EXPECTED` | 1,756 |
| POLYMARKET | trades    | `MISSING_EXPECTED` | 1,686 |

### sports

| Venue         | Data type | Classification     | Cells |
| ------------- | --------- | ------------------ | ----: |
| BETFAIR_EX_EU | trades    | `MISSING_EXPECTED` | 1,427 |
| BETFAIR_EX_UK | trades    | `MISSING_EXPECTED` | 1,407 |
| BETFAIR_SB_UK | trades    | `MISSING_EXPECTED` | 1,399 |
| PINNACLE      | trades    | `MISSING_EXPECTED` |   708 |
| FANDUEL       | trades    | `MISSING_EXPECTED` |   627 |
| DRAFTKINGS    | trades    | `MISSING_EXPECTED` |   554 |
| ODDS_API      | ODDS      | `MISSING_EXPECTED` |   204 |

### tradfi

| Venue         | Data type | Classification     | Cells |
| ------------- | --------- | ------------------ | ----: |
| ICE           | tbbo      | `MISSING_EXPECTED` | 1,254 |
| ICE           | trades    | `MISSING_EXPECTED` | 1,238 |
| CME           | tbbo      | `MISSING_EXPECTED` | 1,188 |
| YAHOO_FINANCE | ohlcv_15m | `MISSING_EXPECTED` |   938 |
| NASDAQ        | ohlcv_1m  | `MISSING_EXPECTED` |   839 |
| NYSE          | ohlcv_1m  | `MISSING_EXPECTED` |   839 |
| YAHOO_FINANCE | ohlcv_24h | `ATTEMPTED_FAILED` |   830 |
| YAHOO_FINANCE | ohlcv_24h | `MISSING_EXPECTED` |   754 |
| YAHOO_FINANCE | ohlcv_15m | `ATTEMPTED_FAILED` |   667 |
| CME           | tbbo      | `ATTEMPTED_FAILED` |    22 |
| NYSE          | ohlcv_1m  | `ATTEMPTED_FAILED` |    14 |
| CBOE          | ohlcv_15m | `MISSING_EXPECTED` |    14 |
| ICE           | ohlcv_1m  | `MISSING_EXPECTED` |    14 |
| FX            | ohlcv_24h | `MISSING_EXPECTED` |    13 |
| CME           | ohlcv_1m  | `MISSING_EXPECTED` |    12 |
| FX            | ohlcv_24h | `ATTEMPTED_FAILED` |    12 |
| CME           | trades    | `MISSING_EXPECTED` |    12 |
| NASDAQ        | ohlcv_1m  | `ATTEMPTED_FAILED` |     1 |

## Notes

- A2 oracle has known gaps (sports off-seasons + DeFi protocol pauses not yet encoded). Cells classified as
  `SHOULD_HAVE_DATA` in those domains may actually be honest empties.
- `DIVERGENT_EMPTY` is the highest-priority class — these are likely silent adapter bugs (the Drift S3 class). Each
  (venue, data_type) row above should be inspected for the source of the empty.
- `MISSING_EXPECTED` indicates a silent gap (the adapter never emitted a manifest row at all). Either the venue's date
  enumerator skipped these cells, or the orchestrator scope doesn't enumerate them.
- `ATTEMPTED_FAILED` is per-row noise unless concentrated on specific (venue, data_type) pairs — check the
  `error_reason` column in the parquet for the failure taxonomy.
- Buckets read: `market-data-tick-{cefi,defi,tradfi,sports,pred}-prd-central-element-323112` (one
  `_index/availability_index.parquet` each — single-walk discipline).
