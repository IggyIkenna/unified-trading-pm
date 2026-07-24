---
doc_type: audit-result
title: A6 — Batch-live adapter parity summary
summary:
  A6 automated batch-live adapter parity scan (573 adapter files, 160 in-scope tuples) — 13 BATCH_ONLY review-blocking
  cells (4 defi resolved 2026-05-21 via curve/jito/morpho _defi_ws.py) + 146 MISSING_BOTH silent gaps + 0 LIVE_ONLY;
  regex/path heuristic with known compound-venue false-negatives.
status: fail
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-data-processing-service, market-tick-data-service]
scope: [engineer, admin]
tags: [audit, mtds, mdps, reconciliation, defi, cefi, live-trading]
related: [/plans/audit/results/archive/batch_live_adapter_parity_2026_05_20.md]
created: 2026-05-20
audited_scope:
  573 adapter files across MTDS + MDPS + IS; 160 (asset_group, venue_token, data_type) tuples classified
  GREEN/BATCH_ONLY/LIVE_ONLY/MISSING_BOTH via path + first-4000-char regex
date: 2026-05-20
auditor: semver
parent_epic: batch_live_symmetry_master
severity: P0
resulting_plan:
lib_version:
doc_versions_checked:
---

# A6 — Batch-live adapter parity summary

_Generated: 2026-05-20T11:28:40.848987+00:00_

_Updated: 2026-05-21 — slot-11 Phase 12 remediation: all 4 defi BATCH_ONLY cells resolved via curve_defi_ws.py +
jito_defi_ws.py + morpho_defi_ws.py (live-defi-rollout branch)._

Adapter files scanned: 573 across 3 repos. In-scope (asset_group, venue_token, data_type) tuples checked: 160.

## Parity status per asset_group

| asset_group | GREEN | BATCH_ONLY | LIVE_ONLY | MISSING_BOTH |
| ----------- | ----: | ---------: | --------: | -----------: |
| cefi        |     1 |          7 |         0 |           31 |
| defi        |     4 |          0 |         0 |           89 |
| prediction  |     0 |          2 |         0 |            0 |
| sports      |     0 |          0 |         0 |           12 |
| tradfi      |     0 |          0 |         0 |           14 |

## BATCH_ONLY cells (live equivalent MUST be built per CLAUDE.md Batch = Live)

Total BATCH_ONLY cells: **13** (review-blocking — every batch adapter MUST have a live equivalent)

| asset_group | venue       | data_type           | batch file count | sample                                                                                                             |
| ----------- | ----------- | ------------------- | ---------------: | ------------------------------------------------------------------------------------------------------------------ |
| cefi        | aster       | liquidations        |                1 | `market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain_perps/aster_adapter.py`       |
| cefi        | aster       | trades              |                2 | `market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain_perps/aster_adapter.py`       |
| cefi        | deribit     | trades              |                1 | `market-tick-data-service/market_tick_data_service/market_interface/adapters/deribit_ws_mixin.py`                  |
| cefi        | hyperliquid | book_snapshot_5     |                1 | `market-tick-data-service/market_tick_data_service/adapters/hyperliquid_s3.py`                                     |
| cefi        | hyperliquid | derivative_ticker   |                1 | `market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain_perps/hyperliquid_adapter.py` |
| cefi        | hyperliquid | liquidations        |                1 | `market-tick-data-service/market_tick_data_service/adapters/hyperliquid_s3.py`                                     |
| cefi        | hyperliquid | trades              |                2 | `market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain_perps/hyperliquid_adapter.py` |
| ~~defi~~    | ~~curve~~   | ~~dex_pools~~       |                1 | ✅ RESOLVED 2026-05-21 — `curve_defi_ws.py` (live-defi-rollout branch)                                             |
| ~~defi~~    | ~~curve~~   | ~~dex_swaps~~       |                1 | ✅ RESOLVED 2026-05-21 — `curve_defi_ws.py` (live-defi-rollout branch)                                             |
| ~~defi~~    | ~~jito~~    | ~~lst_rates~~       |                2 | ✅ RESOLVED 2026-05-21 — `jito_defi_ws.py` (live-defi-rollout branch)                                              |
| ~~defi~~    | ~~morpho~~  | ~~lending_indices~~ |                1 | ✅ RESOLVED 2026-05-21 — `morpho_defi_ws.py` (live-defi-rollout branch)                                            |
| prediction  | kalshi      | trades              |                2 | `market-data-processing-service/market_data_processing_service/app/adapters/prediction/trades_adapter.py`          |
| prediction  | polymarket  | trades              |                2 | `market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/polymarket_adapter.py`         |

## MISSING_BOTH cells (no adapter detected — silent gap)

Total MISSING_BOTH cells: **146**

| asset_group | venue    | data_type          |
| ----------- | -------- | ------------------ |
| cefi        | aster    | book_snapshot_5    |
| cefi        | aster    | derivative_ticker  |
| cefi        | binance  | book_snapshot_5    |
| cefi        | binance  | derivative_ticker  |
| cefi        | binance  | futures_chain      |
| cefi        | binance  | liquidations       |
| cefi        | bybit    | book_snapshot_5    |
| cefi        | bybit    | derivative_ticker  |
| cefi        | bybit    | futures_chain      |
| cefi        | bybit    | liquidations       |
| cefi        | bybit    | trades             |
| cefi        | coinbase | book_snapshot_5    |
| cefi        | coinbase | trades             |
| cefi        | deribit  | book_snapshot_5    |
| cefi        | deribit  | derivative_ticker  |
| cefi        | deribit  | futures_chain      |
| cefi        | deribit  | liquidations       |
| cefi        | deribit  | options_chain      |
| cefi        | futures  | book_snapshot_5    |
| cefi        | futures  | derivative_ticker  |
| cefi        | futures  | futures_chain      |
| cefi        | futures  | liquidations       |
| cefi        | futures  | trades             |
| cefi        | okx      | book_snapshot_5    |
| cefi        | okx      | derivative_ticker  |
| cefi        | okx      | liquidations       |
| cefi        | okx      | trades             |
| cefi        | spot     | book_snapshot_5    |
| cefi        | spot     | trades             |
| cefi        | upbit    | book_snapshot_5    |
| cefi        | upbit    | trades             |
| defi        | aavev3   | flash_loan_events  |
| defi        | aavev3   | lending_indices    |
| defi        | aavev3   | liquidation_events |
| defi        | aavev3   | position_data      |
| defi        | aavev3   | risk_params        |
| defi        | arbitrum | dex_pools          |
| defi        | arbitrum | dex_swaps          |
| defi        | arbitrum | flash_loan_events  |
| defi        | arbitrum | lending_indices    |

_(showing first 40 of 146 MISSING_BOTH cells)_

## LIVE_ONLY cells (suspicious — usually intentional only for derived/streaming-only data_types)

Total LIVE_ONLY cells: **0**

## Caveats (sampling transparency)

- Venue + data_type extraction is **regex-based on file paths + first 4000 chars**. Adapters that don't put
  venue/data_type in their path or module header are missed.
- Path classification `is_batch` / `is_live` based on path tokens (`/handlers/`, `/live/`, `/stream/`, etc.). Ambiguous
  files default to batch.
- An adapter may exist in code but not be wired into the orchestrator scope — A6 only checks _adapter file existence_,
  not whether it's enumerated.
- A6 does not check schema parity between batch + live adapters (would require running them). Operator may want to
  follow up with a runtime parity test (cross-checking manifest rows from each mode).
- Tokens collapsed (e.g. `OKX` and `okx` and `binance-futures` → split into `binance` + `futures`). Per-token false
  positives possible — see CSV `venue_token` column for exact match.
