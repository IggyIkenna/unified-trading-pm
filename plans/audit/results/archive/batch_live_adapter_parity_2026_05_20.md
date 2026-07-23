---
doc_type: audit-result
title: Batch-Live Adapter Parity Audit — 2026-05-20
summary:
  Manual batch-vs-live adapter parity audit across MTDS (27 batch handlers, 18 live WSFeedConnectors) + IS
  reference-data adapters — ~66 P0 batch-only cells with no live equivalent, 8 BLOCKED-CREDENTIALS, 17 GREEN, 4 PARTIAL
  scaffolds; corrects the automated A6 script's GREEN undercount from compound-venue tokenization.
status: fail
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: [audit, mtds, instruments, reconciliation, defi, cefi, tradfi, live-trading]
related: [/plans/audit/results/archive/batch_live_adapter_parity_2026_05_20_summary.md]
created: 2026-05-20
audited_scope:
  MTDS batch handlers (27 files) + live connectors (18 WSFeedConnector modules) + defi_live adapters + UAC
  EXPECTED_COVERAGE_BY_ASSET_GROUP + instruments-service batch/live adapters, across cefi/defi/tradfi/sports/prediction;
  adapter existence + data_type coverage (not field-level schema parity)
date: 2026-05-20
auditor: slot-3 sub-agent (Sonnet 4.6)
parent_epic: batch_live_symmetry_master
severity: P0
resulting_plan:
lib_version:
doc_versions_checked:
---

# Batch-Live Adapter Parity Audit — 2026-05-20

_Author: slot-3 sub-agent (Sonnet 4.6) — Mega-audit Phase A6_ _Generated: 2026-05-20_

## Audit scope

### What was covered (exhaustive)

- **MTDS batch handlers**: all 27 Python files in `market_tick_data_service/cli/handlers/` — exhaustive read of
  data_type emission.
- **MTDS live connectors**: all 18 registered `WSFeedConnector` modules in `market_tick_data_service/live/connectors/` —
  exhaustive verification of `register_ws_feed_connector` calls + stream subscription types.
- **MTDS defi_live adapters**: `market_interface/adapters/defi/live/` (hyperliquid_ws.py, onchain_event_poller.py) —
  scope analysis.
- **MTDS defi_live_ws_adapters**: `market_interface/adapters/defi_live/` (alchemy_adapter.py, thegraph_ws_adapter.py) —
  scope analysis.
- **UAC EXPECTED_COVERAGE_BY_ASSET_GROUP**: authoritative scope policy for 160 (asset_group, venue, data_type) cells.
- **instruments-service**: batch adapter inventory across cefi/defi/tradfi/sports/prediction domains. Single live
  adapter confirmed: `tradfi_live.py` (GCS-first + Databento fallback for reference data).

### What was sampled (not exhaustive)

- Content of each adapter file was sampled (first 4000 chars) rather than fully read for every one. Full handler logic
  was read for the 5 primary DeFi batch handlers.
- Schema fields within each adapter were not verified for parity — this audit checks adapter _existence_ and _data_type_
  coverage, not field-level schema equivalence between batch and live.
- Market-data-processing-service (MDPS) was not independently audited — it is a downstream consumer of MTDS ticks, not a
  primary writer.

### Audit methodology

Manual code inspection + file system enumeration, not the heuristic regex approach in `a6_batch_live_adapter_parity.py`
(which had known false-negatives from compound venue name tokenization).

---

## MTDS batch adapters found

Live connectors registered via `register_ws_feed_connector`:

| domain                          | handler_file                                   | data_type(s)                                                                                     | asset_group                                       |
| ------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------- |
| tick_data_handler.py            | `cli/handlers/tick_data_handler.py`            | trades, book*snapshot_5, derivative_ticker, liquidations, options_chain, futures_chain, ohlcv*\* | cefi + tradfi                                     |
| perp_funding_handler.py         | `cli/handlers/perp_funding_handler.py`         | perp_funding                                                                                     | defi (HYPERLIQUID, ASTER, GMX, PACIFICA, LIGHTER) |
| lst_rates_handler.py            | `cli/handlers/lst_rates_handler.py`            | lst_rates                                                                                        | defi (Lido, EtherFi, etc.)                        |
| evm_defi_handler.py             | `cli/handlers/evm_defi_handler.py`             | lending_indices                                                                                  | defi (Aave, Compound, Morpho, Fluid)              |
| solana_defi_handler.py          | `cli/handlers/solana_defi_handler.py`          | perp_funding                                                                                     | defi Solana (Drift, Phoenix)                      |
| oracle_prices_handler.py        | `cli/handlers/oracle_prices_handler.py`        | oracle_prices                                                                                    | defi                                              |
| gas_fee_handler.py              | `cli/handlers/gas_fee_handler.py`              | gas_fees                                                                                         | defi                                              |
| dex_pools_handler.py            | `cli/handlers/dex_pools_handler.py`            | dex_pool_state                                                                                   | defi (Uniswap, Balancer, Curve)                   |
| dex_swaps_handler.py            | `cli/handlers/dex_swaps_handler.py`            | dex_pool_swaps                                                                                   | defi                                              |
| eigenlayer_rewards_handler.py   | `cli/handlers/eigenlayer_rewards_handler.py`   | eigenlayer_rewards                                                                               | defi                                              |
| liquidations_handler.py         | `cli/handlers/liquidations_handler.py`         | liquidations                                                                                     | defi lending                                      |
| lending_indices_handler.py      | `cli/handlers/lending_indices_handler.py`      | lending_indices                                                                                  | defi                                              |
| bridge_events_handler.py        | `cli/handlers/bridge_events_handler.py`        | bridge_events                                                                                    | defi                                              |
| token_transfers_handler.py      | `cli/handlers/token_transfers_handler.py`      | token_transfers                                                                                  | defi                                              |
| vault_share_price_handler.py    | `cli/handlers/vault_share_price_handler.py`    | vault_share_price                                                                                | defi                                              |
| position_data_handler.py        | `cli/handlers/position_data_handler.py`        | position_data                                                                                    | defi lending                                      |
| mev_events_handler.py           | `cli/handlers/mev_events_handler.py`           | mev_events                                                                                       | defi                                              |
| native_staking_handler.py       | `cli/handlers/native_staking_handler.py`       | native_staking                                                                                   | defi                                              |
| flash_loan_events_handler.py    | `cli/handlers/flash_loan_events_handler.py`    | flash_loan_events                                                                                | defi (Aave V3)                                    |
| governance_events_handler.py    | `cli/handlers/governance_events_handler.py`    | governance_events                                                                                | defi                                              |
| governance_proposals_handler.py | `cli/handlers/governance_proposals_handler.py` | governance_proposals                                                                             | defi                                              |
| staking_yields_handler.py       | `cli/handlers/staking_yields_handler.py`       | staking_yields                                                                                   | defi                                              |
| solana_lst_archival.py          | `cli/handlers/solana_lst_archival.py`          | lst_rates                                                                                        | defi Solana (Jito)                                |
| websocket_streaming_handler.py  | `cli/handlers/websocket_streaming_handler.py`  | trades (cefi+defi)                                                                               | all live mode                                     |

---

## MTDS live adapters found

All 18 live `WSFeedConnector` modules registered via `live/connectors/__init__.py → register_all()`:

| venue_key                                | file                                     | data_type (what it streams) | status              | asset_group |
| ---------------------------------------- | ---------------------------------------- | --------------------------- | ------------------- | ----------- |
| DRIFT-SOLANA                             | `live/connectors/drift_solana_ws.py`     | trades (perp)               | GREEN               | defi        |
| ASTER                                    | `live/connectors/aster_ws.py`            | trades (perp)               | GREEN               | cefi        |
| BINANCE-FUTURES                          | `live/connectors/binance_futures_ws.py`  | trades (perp)               | GREEN               | cefi        |
| BYBIT-FUTURES                            | `live/connectors/bybit_ws.py`            | trades (perp)               | GREEN               | cefi        |
| DERIBIT                                  | `live/connectors/deribit_ws.py`          | trades (perp + options)     | GREEN               | cefi        |
| HYPERLIQUID                              | `live/connectors/hyperliquid_ws.py`      | trades (perp)               | GREEN               | cefi        |
| KRAKEN-FUTURES                           | `live/connectors/kraken_futures_ws.py`   | trades (futures)            | GREEN               | cefi        |
| OKX-FUTURES                              | `live/connectors/okx_ws.py`              | trades (swap)               | GREEN               | cefi        |
| BINANCE-SPOT                             | `live/connectors/binance_spot_ws.py`     | trades (spot)               | GREEN               | cefi        |
| BYBIT-SPOT                               | `live/connectors/bybit_spot_ws.py`       | trades (spot)               | GREEN               | cefi        |
| COINBASE-SPOT                            | `live/connectors/coinbase_spot_ws.py`    | trades (spot)               | GREEN               | cefi        |
| KRAKEN-SPOT                              | `live/connectors/kraken_spot_ws.py`      | trades (spot)               | GREEN               | cefi        |
| OKX-SPOT                                 | `live/connectors/okx_spot_ws.py`         | trades (spot)               | GREEN               | cefi        |
| CME, ICE, NYSE, NASDAQ, CBOE, ARCA, BATS | `live/connectors/databento_tradfi_ws.py` | trades                      | BLOCKED-CREDENTIALS | tradfi      |
| odds_api                                 | `live/connectors/odds_api_ws.py`         | odds (live odds polling)    | BLOCKED-CREDENTIALS | sports      |
| phoenix                                  | `live/connectors/phoenix_ws.py`          | trades (Solana DEX)         | GREEN               | defi        |
| polymarket                               | `live/connectors/polymarket_ws.py`       | trades (prediction)         | GREEN               | prediction  |
| kalshi                                   | `live/connectors/kalshi_ws.py`           | trades (prediction)         | GREEN               | prediction  |

**Additional defi live adapters (wired into market_interface, not live/connectors):**

- `market_interface/adapters/defi/live/hyperliquid_ws.py` — HyperliquidWSFeed streaming funding rates + orderbook (used
  internally, not via WSFeedConnector registry)
- `market_interface/adapters/defi/live/onchain_event_poller.py` — Aave liquidations + Uniswap swaps event poller
- `market_interface/adapters/defi_live/alchemy_adapter.py` — Alchemy WS minedTxs / logs → DeFi events
- `market_interface/adapters/defi_live/thegraph_ws_adapter.py` — TheGraph WS → CanonicalLiquidityPool +
  CanonicalLendingRate

---

## IS batch adapters found

instruments-service is reference-data-only (InstrumentRecord catalog rows). It does NOT emit market ticks or market
data. The "batch" mode fetches instrument universe from source providers.

| domain                        | file                                                    | data_type(s) produced                                              |
| ----------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------ |
| cefi/aster.py                 | `reference_data/adapters/cefi/aster.py`                 | instruments (InstrumentRecord)                                     |
| cefi/ccxt_adapter.py          | `reference_data/adapters/cefi/ccxt_adapter.py`          | instruments                                                        |
| cefi/deribit_combo_adapter.py | `reference_data/adapters/cefi/deribit_combo_adapter.py` | instruments                                                        |
| cefi/hyperliquid.py           | `reference_data/adapters/cefi/hyperliquid.py`           | instruments                                                        |
| cefi/tardis.py                | `reference_data/adapters/cefi/tardis.py`                | instruments                                                        |
| defi/\*.py (40+ adapters)     | `reference_data/adapters/defi/`                         | instruments (pool records, lending markets)                        |
| tradfi/databento.py           | `reference_data/adapters/tradfi/databento.py`           | instruments (futures/options contracts)                            |
| tradfi/ibkr.py                | `reference_data/adapters/tradfi/ibkr.py`                | instruments                                                        |
| tradfi/polygon.py             | `reference_data/adapters/tradfi/polygon.py`             | instruments                                                        |
| sports/adapters/ (7 adapters) | `reference_data/adapters/sports/adapters/`              | FIXTURES, MATCHES, STANDINGS, XG, INJURIES, PLAYER_VALUES, WEATHER |
| prediction/kalshi.py          | `reference_data/adapters/prediction/kalshi.py`          | instruments (market catalog)                                       |
| prediction/polymarket.py      | `reference_data/adapters/prediction/polymarket.py`      | instruments                                                        |

---

## IS live adapters found

| domain | file                                            | status          | notes                                                                            |
| ------ | ----------------------------------------------- | --------------- | -------------------------------------------------------------------------------- |
| tradfi | `reference_data/adapters/tradfi/tradfi_live.py` | GREEN (partial) | GCS-first snapshot read + Databento T-3 fallback for instrument universe refresh |
| sports | `triggers/sports_fixtures_daily_repoll.py`      | GREEN           | Sports fixtures live re-poll trigger (Phase B.1); writes same GCS path as batch  |

**IS live mode is at Phase B.1 (sports trigger only).** Phases B.2–E (cefi/defi/tradfi/prediction live catalog refresh)
are planned but not yet implemented per `plans/epics/instruments_master.md`.

---

## Parity matrix — MTDS (CeFi)

The live `WSFeedConnector` framework only streams `trades` data_type. All other CeFi data_types (book_snapshot_5,
derivative_ticker, liquidations, options_chain, futures_chain) have batch adapters (via Tardis historical API) but NO
live equivalent connectors yet.

| venue           | data_type         | batch_adapter                        | live_adapter                                             | verdict      |
| --------------- | ----------------- | ------------------------------------ | -------------------------------------------------------- | ------------ |
| BINANCE-FUTURES | trades            | tick_data_handler.py (Tardis)        | binance_futures_ws.py                                    | GREEN        |
| BINANCE-FUTURES | book_snapshot_5   | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| BINANCE-FUTURES | derivative_ticker | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| BINANCE-FUTURES | liquidations      | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| BINANCE-FUTURES | futures_chain     | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| BINANCE-SPOT    | trades            | tick_data_handler.py (Tardis)        | binance_spot_ws.py                                       | GREEN        |
| BINANCE-SPOT    | book_snapshot_5   | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| BYBIT-FUTURES   | trades            | tick_data_handler.py (Tardis)        | bybit_ws.py                                              | GREEN        |
| BYBIT-FUTURES   | book_snapshot_5   | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| BYBIT-FUTURES   | derivative_ticker | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| BYBIT-FUTURES   | liquidations      | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| BYBIT-FUTURES   | futures_chain     | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| BYBIT-SPOT      | trades            | tick_data_handler.py (Tardis)        | bybit_spot_ws.py                                         | GREEN        |
| BYBIT-SPOT      | book_snapshot_5   | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| OKX-FUTURES     | trades            | tick_data_handler.py (Tardis)        | okx_ws.py                                                | GREEN        |
| OKX-FUTURES     | book_snapshot_5   | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| OKX-FUTURES     | derivative_ticker | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| OKX-FUTURES     | liquidations      | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| OKX-SPOT        | trades            | tick_data_handler.py (Tardis)        | okx_spot_ws.py                                           | GREEN        |
| OKX-SPOT        | book_snapshot_5   | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| DERIBIT         | trades            | tick_data_handler.py (Tardis)        | deribit_ws.py                                            | GREEN        |
| DERIBIT         | book_snapshot_5   | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| DERIBIT         | derivative_ticker | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| DERIBIT         | liquidations      | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| DERIBIT         | options_chain     | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| DERIBIT         | futures_chain     | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| HYPERLIQUID     | trades            | tick_data_handler.py (onchain)       | hyperliquid_ws.py                                        | GREEN        |
| HYPERLIQUID     | book_snapshot_5   | hyperliquid_s3.py                    | live/defi/hyperliquid_ws.py (internal only, no manifest) | PARTIAL      |
| HYPERLIQUID     | derivative_ticker | onchain_perps/hyperliquid_adapter.py | none                                                     | P0 GAP       |
| HYPERLIQUID     | liquidations      | hyperliquid_s3.py                    | none                                                     | P0 GAP       |
| ASTER           | trades            | onchain_perps/aster_adapter.py       | aster_ws.py                                              | GREEN        |
| ASTER           | book_snapshot_5   | none (MISSING_BOTH)                  | none                                                     | MISSING_BOTH |
| ASTER           | derivative_ticker | none (MISSING_BOTH)                  | none                                                     | MISSING_BOTH |
| ASTER           | liquidations      | onchain_perps/aster_adapter.py       | none                                                     | P0 GAP       |
| KRAKEN-FUTURES  | trades            | tick_data_handler.py (Tardis)        | kraken_futures_ws.py                                     | GREEN        |
| KRAKEN-FUTURES  | book_snapshot_5   | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| KRAKEN-FUTURES  | derivative_ticker | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| KRAKEN-FUTURES  | liquidations      | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| KRAKEN-FUTURES  | futures_chain     | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| KRAKEN-SPOT     | trades            | tick_data_handler.py (Tardis)        | kraken_spot_ws.py                                        | GREEN        |
| KRAKEN-SPOT     | book_snapshot_5   | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| COINBASE-SPOT   | trades            | tick_data_handler.py (Tardis)        | coinbase_spot_ws.py                                      | GREEN        |
| COINBASE-SPOT   | book_snapshot_5   | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| UPBIT           | trades            | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |
| UPBIT           | book_snapshot_5   | tick_data_handler.py (Tardis)        | none                                                     | P0 GAP       |

---

## Parity matrix — MTDS (DeFi)

The DeFi live connectors cover `trades` from DRIFT-SOLANA and PHOENIX. All deeper DeFi data_types (lending, LST, oracle,
etc.) are batch-only.

| venue/protocol            | data_type                                                                          | batch_adapter                                                                                                                    | live_adapter                                                  | verdict                         |
| ------------------------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------- |
| DRIFT-SOLANA              | trades (perp)                                                                      | solana_defi_handler.py                                                                                                           | drift_solana_ws.py                                            | GREEN                           |
| PHOENIX                   | trades (DEX)                                                                       | dex_swaps_handler.py                                                                                                             | phoenix_ws.py                                                 | GREEN                           |
| HYPERLIQUID               | perp_funding                                                                       | perp_funding_handler.py (HYPERLIQUID API)                                                                                        | live/defi/hyperliquid_ws.py (internal)                        | PARTIAL (no manifest recording) |
| ASTER                     | perp_funding                                                                       | perp_funding_handler.py                                                                                                          | none                                                          | P0 GAP                          |
| GMX-ARBITRUM/AVALANCHE    | perp_funding                                                                       | perp_funding_handler.py                                                                                                          | none                                                          | P0 GAP                          |
| PACIFICA-SOLANA           | perp_funding                                                                       | perp_funding_handler.py                                                                                                          | none                                                          | P0 GAP                          |
| LIGHTER-ZKSYNC            | perp_funding                                                                       | perp_funding_handler.py                                                                                                          | none                                                          | P0 GAP                          |
| LIDO-ETHEREUM             | lst_rates                                                                          | lst_rates_handler.py                                                                                                             | none                                                          | P0 GAP                          |
| JITO-SOLANA               | lst_rates                                                                          | solana_lst_archival.py                                                                                                           | none                                                          | P0 GAP                          |
| ETHERFI-ETHEREUM          | lst_rates, eigenlayer_rewards                                                      | lst_rates_handler.py, eigenlayer_rewards_handler.py                                                                              | none                                                          | P0 GAP                          |
| ETHENA-ETHEREUM           | lst_rates                                                                          | lst_rates_handler.py                                                                                                             | none                                                          | P0 GAP                          |
| LIDO-ETHEREUM             | staking_yields                                                                     | staking_yields_handler.py                                                                                                        | none                                                          | P0 GAP                          |
| AAVE_V3-\* (8 chains)     | lending_indices, liquidation_events, position_data, risk_params, flash_loan_events | evm_defi_handler.py, lending_indices_handler.py, liquidations_handler.py, position_data_handler.py, flash_loan_events_handler.py | onchain_event_poller.py (Aave liquidations only, no manifest) | PARTIAL                         |
| COMPOUND_V3-\* (5 chains) | lending_indices, liquidation_events, position_data, risk_params                    | lending_indices_handler.py, etc.                                                                                                 | none                                                          | P0 GAP                          |
| MORPHO-\* (5 chains)      | lending_indices, liquidation_events, position_data, risk_params                    | evm_defi_handler.py                                                                                                              | none                                                          | P0 GAP                          |
| FLUID-ETHEREUM            | lending_indices, liquidation_events, position_data, risk_params                    | lending_indices_handler.py                                                                                                       | none                                                          | P0 GAP                          |
| UNISWAP_V2/V3/V4-\*       | dex_pools, dex_swaps                                                               | dex_pools_handler.py, dex_swaps_handler.py                                                                                       | thegraph_ws_adapter.py (internal, no manifest)                | PARTIAL                         |
| CURVE-\*                  | dex_pools, dex_swaps                                                               | dex_pools_handler.py, dex_swaps_handler.py                                                                                       | none                                                          | P0 GAP                          |
| BALANCER-\*               | dex_pools, dex_swaps                                                               | dex_pools_handler.py, dex_swaps_handler.py                                                                                       | none                                                          | P0 GAP                          |
| (all chains)              | oracle_prices                                                                      | oracle_prices_handler.py                                                                                                         | none                                                          | P0 GAP                          |
| (all chains)              | gas_fees                                                                           | gas_fee_handler.py                                                                                                               | none                                                          | P0 GAP                          |

---

## Parity matrix — MTDS (TradFi)

| venue         | data_type              | batch_adapter                         | live_adapter           | verdict             |
| ------------- | ---------------------- | ------------------------------------- | ---------------------- | ------------------- |
| CME           | trades                 | tick_data_handler.py (Databento hist) | databento_tradfi_ws.py | BLOCKED-CREDENTIALS |
| CME           | ohlcv_1m               | tick_data_handler.py                  | databento_tradfi_ws.py | BLOCKED-CREDENTIALS |
| CME           | tbbo                   | tick_data_handler.py                  | databento_tradfi_ws.py | BLOCKED-CREDENTIALS |
| ICE           | trades, ohlcv_1m, tbbo | tick_data_handler.py                  | databento_tradfi_ws.py | BLOCKED-CREDENTIALS |
| NYSE          | ohlcv_1m               | tick_data_handler.py                  | databento_tradfi_ws.py | BLOCKED-CREDENTIALS |
| NASDAQ        | ohlcv_1m               | tick_data_handler.py                  | databento_tradfi_ws.py | BLOCKED-CREDENTIALS |
| CBOE          | ohlcv_15m              | tick_data_handler.py                  | databento_tradfi_ws.py | BLOCKED-CREDENTIALS |
| FX            | ohlcv_24h              | tick_data_handler.py                  | none                   | P0 GAP              |
| YAHOO_FINANCE | ohlcv_15m, ohlcv_24h   | tick_data_handler.py                  | none                   | P0 GAP              |

---

## Parity matrix — MTDS (Sports)

| venue      | data_type                    | batch_adapter          | live_adapter   | verdict             |
| ---------- | ---------------------------- | ---------------------- | -------------- | ------------------- |
| ODDS_API   | odds                         | odds_engine_adapter.py | odds_api_ws.py | BLOCKED-CREDENTIALS |
| PINNACLE   | odds_snapshot, odds_movement | batch adapter exists   | none           | P0 GAP              |
| BETFAIR    | odds_snapshot, odds_movement | betfair_adapter.py     | none           | P0 GAP              |
| DRAFTKINGS | odds_snapshot, odds_movement | none                   | none           | MISSING_BOTH        |
| FANDUEL    | odds_snapshot, odds_movement | none                   | none           | MISSING_BOTH        |
| BET365     | odds_snapshot, odds_movement | none                   | none           | MISSING_BOTH        |

---

## Parity matrix — MTDS (Prediction)

| venue      | data_type | batch_adapter         | live_adapter     | verdict |
| ---------- | --------- | --------------------- | ---------------- | ------- |
| POLYMARKET | trades    | polymarket_adapter.py | polymarket_ws.py | GREEN   |
| KALSHI     | trades    | kalshi_adapter.py     | kalshi_ws.py     | GREEN   |

---

## Parity matrix — IS (instruments-service)

IS is reference-data only (InstrumentRecord, not market ticks). The "batch=live" rule applies to IS in the sense that
the catalog refresh must work in both batch mode (daily full refresh) and live mode (intraday trigger-based refresh).

| domain                 | batch_adapter                                                                  | live_adapter                                    | verdict                        |
| ---------------------- | ------------------------------------------------------------------------------ | ----------------------------------------------- | ------------------------------ |
| cefi instruments       | ccxt_adapter.py, hyperliquid.py, aster.py, deribit_combo_adapter.py, tardis.py | planned (Phase B.2 – not yet shipped)           | P0 GAP (instruments_live plan) |
| defi instruments       | 40+ adapters (aave_v3.py, balancer.py, curve.py, etc.)                         | planned (Phase B.3 – not yet shipped)           | P0 GAP                         |
| tradfi instruments     | databento.py, ibkr.py, polygon.py                                              | tradfi_live.py (GCS-first + Databento fallback) | GREEN (partial)                |
| sports instruments     | api_football.py + 6 other providers                                            | sports_fixtures_daily_repoll.py (trigger-based) | GREEN (Phase B.1)              |
| prediction instruments | kalshi.py, polymarket.py                                                       | planned (Phase B.4 – not yet shipped)           | P0 GAP                         |

---

## P0 gaps — batch-only cells (need live adapter)

### CeFi — trades are GREEN, but all non-trades data_types are batch-only:

- BINANCE-FUTURES/SPOT: book_snapshot_5, derivative_ticker, liquidations, futures_chain
- BYBIT-FUTURES/SPOT: book_snapshot_5, derivative_ticker, liquidations, futures_chain
- OKX-FUTURES/SPOT: book_snapshot_5, derivative_ticker, liquidations
- DERIBIT: book_snapshot_5, derivative_ticker, liquidations, options_chain, futures_chain
- HYPERLIQUID: derivative_ticker, liquidations (book_snapshot_5 is PARTIAL — internal WS feed but no manifest recording)
- ASTER: liquidations (trades are GREEN)
- KRAKEN-FUTURES/SPOT: book_snapshot_5, derivative_ticker, liquidations, futures_chain
- COINBASE-SPOT: book_snapshot_5
- UPBIT: trades, book_snapshot_5 (NO live connector at all — P0)

### DeFi — all deeper data_types batch-only:

- perp_funding: ASTER, GMX-\*, PACIFICA, LIGHTER (HYPERLIQUID and DRIFT partial via internal feeds)
- lst_rates: LIDO, JITO, ETHERFI, ETHENA
- staking_yields: LIDO, ETHERFI, ETHENA, JITO
- eigenlayer_rewards: ETHERFI
- lending_indices, liquidation_events, position_data, risk_params: all COMPOUND_V3, MORPHO, FLUID chains (AAVE partial
  via onchain_event_poller)
- flash_loan_events: all AAVE_V3 chains (no manifest-recording live adapter)
- dex_pools, dex_swaps: CURVE (all chains), BALANCER (all chains), UNISWAP (partial via thegraph_ws)
- oracle_prices: all chains
- gas_fees: all chains

### TradFi:

- FX: ohlcv_24h (no live connector)
- YAHOO_FINANCE: ohlcv_15m, ohlcv_24h (no live connector)

### Sports:

- PINNACLE: odds_snapshot, odds_movement
- BETFAIR: odds_snapshot, odds_movement
- DRAFTKINGS, FANDUEL, BET365: all data_types (MISSING_BOTH)

### IS (instruments-service):

- cefi instruments: no live refresh (Phase B.2 planned)
- defi instruments: no live refresh (Phase B.3 planned)
- prediction instruments: no live refresh (Phase B.4 planned)

---

## P1 gaps — live-only cells (may be intentional, verify)

None found. All live connectors correspond to data_types that also have batch paths. The PARTIAL items (Hyperliquid
book_snapshot live WS, Aave onchain_event_poller, TheGraph WS) have no manifest recording wired — these are
infrastructure scaffolds only, not operational live capture.

---

## Summary counts

| asset_group | GREEN (both batch + live) | BATCH_ONLY (P0 gap)                          | BLOCKED-CREDENTIALS                                     | PARTIAL                                 | MISSING_BOTH                    |
| ----------- | ------------------------- | -------------------------------------------- | ------------------------------------------------------- | --------------------------------------- | ------------------------------- |
| cefi        | 13 (all trades)           | ~25 (non-trades DTs)                         | 0                                                       | 1 (HL book_snapshot_5)                  | 3 (ASTER DTs)                   |
| defi        | 2 (DRIFT+PHOENIX trades)  | ~35 (perp_funding, lst_rates, lending, etc.) | 0                                                       | 3 (HL funding, Aave liq, Uniswap pools) | 0                               |
| tradfi      | 0                         | 2 (FX, YAHOO_FINANCE)                        | 7 (CME/ICE/NYSE/NASDAQ/CBOE/ARCA/BATS — Databento Live) | 0                                       | 0                               |
| sports      | 0                         | 4 (PINNACLE, BETFAIR)                        | 1 (ODDS_API)                                            | 0                                       | 3 (DRAFTKINGS, FANDUEL, BET365) |
| prediction  | 2 (POLYMARKET, KALSHI)    | 0                                            | 0                                                       | 0                                       | 0                               |

**Total P0 gaps (batch-only, no live equivalent): ~66 venue × data_type cells** **Total BLOCKED-CREDENTIALS cells: 8**
**Total GREEN cells: 17** **Total PARTIAL cells (live scaffold exists, no manifest recording): 4**

---

## Key finding: The automated A6 script undercounts GREEN

The prior automated run (`a6_batch_live_adapter_parity.py` run at 11:28:40) found only 1 GREEN cell (binance trades).
Manual code inspection finds **13 GREEN cells for cefi trades alone** (BINANCE-FUTURES, BINANCE-SPOT, BYBIT-FUTURES,
BYBIT-SPOT, OKX-FUTURES, OKX-SPOT, DERIBIT, HYPERLIQUID, ASTER, KRAKEN-FUTURES, KRAKEN-SPOT, COINBASE-SPOT +
DRIFT-SOLANA DeFi, PHOENIX DeFi, POLYMARKET, KALSHI).

The discrepancy is because the automated script splits compound venue names (e.g. "BINANCE-FUTURES" → tokens "binance" +
"futures") then tries to match against a path regex pattern that misses the live/connectors/ module names.

**The automated script CSV must be treated as having false-negatives for GREEN and BATCH_ONLY classification for any
compound-name venue.**

---

## Caveats (sampling transparency)

1. **Exhaustiveness**: handler file enumeration was exhaustive; content was sampled for new handlers, fully read for
   primary DeFi handlers.
2. **Schema parity NOT checked**: this audit confirms adapter existence and data_type coverage. Field-level schema
   equivalence between batch and live output requires a runtime test (compare manifest rows from each mode).
3. **Wiring vs existence**: some "live" adapters in `market_interface/adapters/defi/live/` and `defi_live/` exist as
   infrastructure scaffolds but are NOT wired into the manifest-recording `WSFeedConnector` registry. These are marked
   PARTIAL.
4. **UPBIT**: has a batch adapter (`market_interface/adapters/cefi/upbit_adapter.py`) but NO live WS connector
   registered. P0 gap confirmed.
5. **Sports bookmakers** (PINNACLE, BETFAIR): have batch adapters in `market_interface/adapters/sports/` but no live WS
   connector.
6. **IS live phases B.2-E** (cefi/defi/prediction instrument catalog refresh): planned but not yet shipped per
   `plans/epics/instruments_master.md`.
