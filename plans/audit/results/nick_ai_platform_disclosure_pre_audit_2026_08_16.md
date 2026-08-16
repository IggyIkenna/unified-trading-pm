---
doc_type: audit-result
title: Nick AI platform disclosure — full per-AG pre-audit detail (2026-08-16)
summary: >-
  Full per-venue coverage grids, full 19-step readiness tables, and exhaustive per-shard schemas for all 5 asset
  groups (cefi/defi/tradfi/sports/prediction), measured 2026-08-16 by 5 parallel sub-agents against the real
  deployment-api/UAC honest-coverage machinery and manifest. This is the durable home for detail too large for
  the owning plan's line cap — the AG-level summary and the client-artifact-facing conclusions live in
  /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md § PRE-AUDIT MEASUREMENTS, which this doc backs.
status: partial
nature: record
audited_scope: >-
  Honest coverage (Layer-1 instrument-denominator + Layer-2 download, all 4 capture states), the 19-step Venue
  Readiness Contract, and exhaustive per-shard schemas for 5 asset groups (cefi, defi, tradfi, sports, prediction)
  — measured against the live production coverage.json and UAC/manifest source, not re-implemented.
date: 2026-08-16
auditor: >-
  5 parallel general-purpose sub-agents (sonnet), dispatched from an interactive session.
severity: P1
parent_epic: infrastructure_master
resulting_plan: /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md
lib_version:
doc_versions_checked:
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [deployment-api, instruments-service, unified-api-contracts, market-tick-data-service, execution-service]
scope: [engineer, admin]
tags: [honest-coverage, venue-readiness, pre-audit, client-disclosure, nick-ai]
related:
  [
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-08-16
source: >-
  5 parallel general-purpose sub-agents (sonnet), dispatched from an interactive session against the Nick AI
  platform-disclosure pre-audit's 7 PRE-AUDIT todos. 4 of 5 hit a session rate limit mid-task and were resumed.
context_scope:
  [
    /codex/02-data/honest-coverage-model.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
  ]
---

# Nick AI platform disclosure — full per-AG pre-audit detail

> **Read `/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md` § PRE-AUDIT MEASUREMENTS first** — that's
> the AG-level summary with the client-artifact-facing conclusions (the ≈50%/≈99% verification, the venue-universe
> reconciliation, the external API surface finding). This doc is the exhaustive backing detail that didn't fit
> there: full per-venue coverage grids, full 19-step readiness tables, and every per-shard schema field. All figures
> dated 2026-08-16 unless stated otherwise; method = live reads of the real `coverage.json`
> (`gs://central-element-323112-honest-coverage/2026-08-16/`, `generated_at: 2026-08-16T00:43:09Z`) and UAC source,
> never a re-implementation.

## CeFi

### Per-venue coverage (22 of 25 declared venues have any manifest presence)

| Venue | captured | empty_confirmed | attempted_failed | expected_unattempted | total | reachable coverage_pct |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ASTER | 1,136,451 | 912,355 | 21,726 | 244,225 | 2,314,757 | 81.04% |
| HYPERLIQUID | 618,848 | 380,597 | 3,841 | 368,802 | 1,372,088 | 62.42% |
| EXTENDED-STARKNET | 80,274 | 160,733 | 0 | 62,645 | 303,652 | 56.17% |
| BITFINEX-FUTURES | 322,773 | 75,001 | 45,927 | 214,352 | 658,053 | 55.36% |
| OKX-SWAP | 1,300,926 | 396,550 | 62,566 | 1,032,507 | 2,792,549 | 54.30% |
| BINANCE-FUTURES | 2,046,778 | 501,032 | 170,837 | 1,089,309 | 3,807,956 | 61.89% |
| OKX-FUTURES | 54,901 | 47,795 | 12,908 | 42,471 | 158,075 | 49.78% |
| LIGHTER-ZKSYNC | 16,491 | 164,007 | 140 | 18,834 | 199,472 | 46.50% |
| BITGET-FUTURES | 657,080 | 584,912 | 97,951 | 673,612 | 2,013,555 | 45.99% |
| UPBIT | 255,182 | 138,651 | 5,088 | 308,256 | 707,177 | 44.88% |
| BYBIT | 1,175,992 | 769,221 | 114,808 | 1,360,765 | 3,420,786 | 44.35% |
| KRAKEN-FUTURES | 793,255 | 942,867 | 86,281 | 952,292 | 2,774,695 | 43.30% |
| BINANCE-SPOT | 505,930 | 237,238 | 1,147 | 956,051 | 1,700,366 | 34.58% |
| COINBASE-CDE | 1,448 | 51,315 | 0 | 2,892 | 55,655 | 33.36% |
| BITFINEX-SPOT | 127,570 | 62,845 | 3,234 | 313,730 | 507,379 | 28.70% |
| BITGET-SPOT | 106,609 | 235,185 | 65 | 345,510 | 687,369 | 23.58% |
| COINBASE-SPOT | 56,230 | 43,270 | 530 | 191,563 | 291,593 | 22.64% |
| DERIBIT | 58,039 | 90,743 | 118,913 | 125,466 | 393,161 | 19.19% |
| BYBIT-SPOT | 142,007 | 165,617 | 2,182 | 624,348 | 934,154 | 18.48% |
| KRAKEN-SPOT | 139,882 | 138,773 | 10,638 | 655,130 | 944,423 | 17.36% |
| OKX-SPOT | 151,944 | 268,094 | 5,411 | 1,181,731 | 1,607,180 | 11.35% |
| COINBASE-FUTURES | 7,983 | 70,237 | 66 | 115,260 | 193,546 | 6.47% |

**PACIFICA-SOLANA, KALSHI-PERP, POLYMARKET-PERP** are UAC-declared but have zero rows in any of the 4 states in the
`by_venue` rollup — Layer-1 `stray_tuples` proves real captured data exists for all three (8, 8, 1 strays
respectively) under a UAC↔writer contract gap the codex doc's own "CERTIFICATION CAVEAT" already names as a known
class of issue.

### Readiness — 19-step contract

| # | Step | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | Declared | PARTIAL | All 25 venues have `VENUE_TO_ADAPTER_KEY`; `VenueCapabilityRecord` lacks the instrument-type axis (fleet-wide gap) |
| 2 | Reference data | Unverified | Not independently invoked live |
| 3 | Market data — batch | Measured, partial | Layer-1 94.52% (69/73), Layer-2 reachable 45.59% |
| 4 | Market data — live | Unverified | Not checked |
| 5 | Features | Out of scope | ML/features excluded per brief |
| 6 | Position read | Unverified | Not checked |
| 7 | Slot eligibility | Unverified | `venue_universe` slot strings not a queryable SSOT yet |
| 8 | Execution — instruction | PARTIAL, measured | Native adapter for DERIBIT only; BYBIT/HYPERLIQUID/ASTER/PACIFICA-SOLANA under `defi_execution/protocols/`; generic CCXT path for the rest unverified |
| 9 | Execution — transfers | MEASURED gap | Only 7/25 venues have a `VENUE_WALLET_CAPABILITIES` entry under their canonical name |
| 10 | Error semantics | MEASURED gap | Only 9 venue-family keys in `VENUE_ERRORS_CEFI` (~14/25 venues covered by prefix) |
| 11 | Config | Unverified | Not checked |
| 12 | Reachability | Unverified | Not traced |
| 13 | Granularity declared | NOT BUILT | Fleet-wide gap, confirmed against umbrella plan's own open P1 |
| 14–16 | Derivation/trigger/matching class | Unverified | Not checked |
| 17 | Strategy consumability | Unverified by SSOT | Only 5/59 archetypes declared, none cefi |
| 18–19 | Data-type consumability / orthogonality | Not run | — |

**Rollup**: BACKTESTABLE is the only real floor, and even that has open gaps (step 1's instrument-type axis, step
3's Layer-1 holes). PAPER-READY/LIVE-READY not certifiable.

### Per-shard schemas (all 9 declared data types, exhaustive)

**`trades`** — `CanonicalTrade`: venue, symbol, trade_id, timestamp, price(Decimal>0), quantity(Decimal>0), side,
buyer_maker(bool?), venue_trade_id?, instrument_key?, is_liquidation(bool?), schema_version="1.0".

**`book_snapshot_5`** — `OrderBookSnapshot5`: instrument_key, ts_event(int), ts_init(int), bid_price_0..4,
bid_size_0..4, ask_price_0..4, ask_size_0..4 (20 flat float cols, all nullable). A richer `CanonicalOrderBook` class
also exists (venue/symbol/timestamp/bids:list[tuple]/asks/sequence_number/instrument_key/levels/schema_version) —
which one MTDS actually writes for cefi was not resolved.

**`derivative_ticker`** — `CanonicalDerivativeTicker`: instrument_key, venue, timestamp, last/mark/index/mid/
prev_day_price(Decimal?), funding_rate(Decimal?), predicted_funding_rate(Decimal?), next_funding_timestamp(?),
funding_timestamp(? — NOT the same field, documented Tardis-CSV sign gotcha), open_interest/open_interest_value/
day_ntl_volume(Decimal?), bid_price/ask_price(Decimal?), volume_24h(Decimal?), schema_version.

**`liquidations`** — `CanonicalLiquidation`: instrument_key, venue, timestamp, side, price(Decimal), size(Decimal),
order_id?, liquidated_account_value?, liquidated_ntl_pos?, liquidated_user?(pii:true), schema_version.

**`options_chain`** — two coexisting schemas: UAC canonical `CanonicalOptionsChainEntry` (17 fields: timestamp,
venue, symbol, underlying, strike, option_type, expiration(required), bid/ask_price/size, implied_volatility, delta/
gamma/theta/vega, instrument_key?); strategy-service-only `InternalOptionsChainSnapshot` (underlying, expiry, strike,
put_call, bid/ask/last/iv, delta/gamma/theta/vega/rho, open_interest/volume — no timestamp/venue/symbol). DERIBIT is
a bundle-grain data type, not per-leg.

**`futures_chain`** — schema class not located; `CanonicalFuturesContract` exists but its docstring scopes it to
TradFi (CME/ICE/CBOE physical-delivery fields) — unlikely to be cefi's. Reported not-found, not guessed.

**`ohlcv_1m`** — two coexisting candidates, write-path selection unresolved: `CanonicalOhlcvBar` (timestamp, venue,
symbol, OHLCV(Decimal), quote_volume?, count?, vwap?, session/phase); `CanonicalOHLCV` (instrument_key, venue,
timestamp, interval, OHLCV(Decimal), vwap?, trade_count?, source:OHLCVSource, schema_version).

**`perp_funding`** — `CanonicalFundingRate`: venue, symbol, rate(Decimal), timestamp, next_funding_timestamp?,
predicted_rate?.

**`volatility_index`** — DERIBIT-only: `DeribitVolatilityIndex`: index_name/currency?, timestamp(ms)?, value?,
open/high/low/close?, data(list of [ts,o,h,l,c])?, continuation?, info(dict)?.

**Undeclared writer-side stray**: `depth_of_book_10` appears as a real BINANCE-FUTURES row — not one of the 9
declared data types, schema not located (out of declared scope).

---

## DeFi

### Per-chain coverage (asset-group level, all 23 chains)

| Chain | Captured | Empty-conf. | Att.-failed | Exp.-unatt. | Total | Coverage % | All-shards % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ETHEREUM | 8,586,111 | 24,806,437 | 2,752,823 | 6,500,711 | 42,646,082 | 48.13 | 20.13 |
| SOLANA | 8,310,414 | 7,888,369 | 1,969 | 21,826,511 | 38,027,263 | 27.57 | 21.85 |
| ARBITRUM | 4,486,400 | 10,840,769 | 1,351,521 | 3,647,623 | 20,326,313 | 47.30 | 22.07 |
| BASE | 3,879,726 | 11,312,341 | 1,398,033 | 1,644,996 | 18,235,096 | 56.04 | 21.28 |
| POLYGON | 4,107,504 | 5,447,083 | 1,365,822 | 3,329,326 | 14,249,735 | 46.66 | 28.83 |
| AVALANCHE | 476,095 | 11,272,093 | 134,141 | 1,136,839 | 13,019,168 | 27.25 | 3.66 |
| OPTIMISM | 1,392,978 | 4,065,688 | 466,353 | 1,990,533 | 7,915,552 | 36.18 | 17.60 |
| BSC | 1,515,564 | 2,490,394 | 404,653 | 283,112 | 4,693,723 | 68.79 | 32.29 |
| ZKSYNC | 0 | 89,592 | 0 | 131,277 | 220,869 | 0.00 | 0.00 |
| LINEA | 6,543 | 199,426 | 0 | 124 | 206,093 | 98.14 | 3.17 |
| PLASMA | 36 | 198,100 | 0 | 0 | 198,136 | 100.00* | 0.02 |
| HYPERLIQUID | 193,211 | 0 | 0 | 0 | 193,211 | 100.00* | 100.00 |
| SCROLL | 0 | 122,053 | 0 | 127 | 122,180 | 0.00 | 0.00 |
| STARKNET | 0 | 6,210 | 0 | 22,530 | 28,740 | 0.00 | 0.00 |
| AURORA | 2,725 | 1,227 | 0 | 124 | 4,076 | 95.65 | 66.85 |
| MANTLE | 1,537 | 2,020 | 0 | 124 | 3,681 | 92.53 | 41.75 |
| BLAST/MODE/MOONBEAM/METIS/CELO/FANTOM/GNOSIS | 0 each | small | 0 | small | ≤2,377 each | 0.00 | 0.00 |

\* PLASMA/HYPERLIQUID ride tiny denominators (198K/193K vs ETHEREUM's 42.6M) — real but not comparable in weight.

### Layer-1 detail: 22 real missing tuples, all LST/restaking

`ETHERFI-ETHEREUM`(yield_bearing)×3 [lst_rates,oracle_prices,staking_yields] · `LIDO-ETHEREUM`(yield_bearing)×3 ·
`KELPDAO-ETHEREUM`(spot_asset)×3 · `PUFFER-ETHEREUM`(spot_asset)×3 · `RENZO-ARBITRUM`(spot_asset)×3 ·
`KARAK-ARBITRUM`(spot_asset)×2[oracle_prices,staking_yields] · `SYMBIOTIC-ETHEREUM`(spot_asset)×2 ·
`JITORESTAKING-SOLANA`(staking)×1[staking_yields] · `SANCTUM-SOLANA`(staking)×1[lst_rates] ·
`SOLBLAZE-SOLANA`(staking)×1[lst_rates].

**698 strays** by data_type (top): oracle_prices 46, lst_rates 41, rewards 41, staking_yields 41, governance_events
38, bridge_events 34, eigenlayer_rewards 33, gas_fees 33, mev_events 33, token_transfers 33, position_data 24,
vault_share_price 22, dex_pool_state 21, risk_params 20, dex_pool_swaps 19, flash_loan_events 19,
liquidation_events 19, lending_indices 18, utilization 17, perp_funding 17, liquidations 16, + a long tail. By venue:
ETHERFI 32, KELPDAO/PUFFER/RENZO 30 each, LIDO/SANCTUM/SOLBLAZE 27 each.

### Readiness — 19-step contract

| # | Step | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | Declared | PASS | `PROTOCOL_CAPABILITIES` + `VENUE_TO_ADAPTER_KEY`, no per-service copy |
| 2 | Reference data | Partial, unverified in full | Adapter classes exist for most protocols; `defi-venue-protocol-catalogue.md` is stale (last_reviewed 2026-05-12), not relied on |
| 3 | Market data — batch | Measured, partial | Layer-1 83.08% (108/130), Layer-2 reachable 40.52% |
| 4 | Market data — live | Documented PAUSED, not re-verified live | 3 `defi-fwd-*` crons paused per `defi_consolidated_closeout_2026_07_18.md`, dated 2026-07-18 |
| 5 | Features | Partial, real signal | 5/59 archetypes declared (`ARCHETYPE_FEATURE_GROUPS`), all 5 defi staking/lending |
| 6 | Position read | Unverified | Grep inconclusive, not read in full |
| 7 | Slot eligibility | Unverified | `venue_universe` not a queryable SSOT (umbrella plan's own open finding) |
| 8 | Execution — instruction | Measured, partial | `DEFI_VENUE_TO_CONNECTOR_CLASS`: 9 raw-venue entries → 5 connector classes; 26 protocol connector files exist in `defi_execution/protocols/`, most not in the reachability map |
| 9 | Execution — transfers | Partial signal | `bridge.py`/`cctp.py` exist; full `BusTransferType` matrix not built |
| 10 | Error semantics | Partial | `DefiErrorCode` confirmed to exist and be used; count not re-verified |
| 11 | Config | Partial | Single per-service `config.py` exists; hot-reload/schema specifics unverified |
| 12 | Reachability | Partial signal | Real AST-based `connector_supports_live()` check exists |
| 13 | Granularity declared | NOT BUILT | Fleet-wide gap |
| 14–15 | Derivation/trigger | Unverified | Stale 26-day-old signal only |
| 16 | Matching class | NOT POPULATED | Depends on step 13 |
| 17 | Strategy consumability | Mechanism confirmed, per-venue not executed | Only lending/LST-typed venues can plausibly pass |
| 18 | Data-type consumability | Unverified, real risk | ~34 data types cataloged, only lending/LST-typed have a confirmed consumer |
| 19 | Canonical orthogonality | Real findings | See below |

**Step 19 detail (proposals only, not merged)**: `lst_sol_rates` checked and ruled out (0 hits, doesn't exist).
`dex_swaps`→`dex_pool_swaps` rename already tracked (D14), 9 stray legacy occurrences still live. **New**:
`utilization` (documented-removed phantom) vs `utilisation` (real declared schema) — same concept, two spellings,
one supposedly retired but appearing anyway (17 stray occurrences). **New**: `("defi","pool","dex_pool_swaps")` and
`("defi","dex_pool","dex_pool_swaps")` declare identical columns (amount0/amount1/price) differing only in
instrument_type spelling. **New**: the 7-member perp-data cluster (perp_funding/perp_daily_ctx/perp_mark_price/
derivative_ticker/perp_trades/perp_mark_oracle/perp_open_interest) is self-documented in-source as mostly
sibling/derivable-from `perp_funding`. Lending-rate breakouts (supply_apy/borrow_apy/liquidation_threshold/
emode_params) are explicitly intentional finer-granularity, not flagged.

### Per-shard schemas (35 registrations, ~34 distinct data types, exhaustive)

Common columns on every contract: `instrument_id`, `venue`, `chain`, `ts_event` (omitted below for brevity).

| `(instrument_type, data_type)` | Extra columns | symbol_column | min rows |
| --- | --- | --- | --- |
| lending_position/lending_indices | supply_index:f64, borrow_index:f64 | symbol | 1 |
| a_token/lending_indices | liquidity_index:f64, variable_borrow_index:f64 | symbol | 1 |
| lending/lending_indices | supply_rate:f64?, borrow_rate:f64? | market_id | 1 |
| solana_lending/lending_indices | supply_apy?, reward_apy?, apy?, tvl_usd? (all f64) | symbol | 1 |
| debt_token/lending_indices | variable_borrow_rate:f64 | symbol | 1 |
| lending or a_token/liquidations | collateral_asset?, debt_asset?, collateral_amount?, debt_amount? | symbol | 1 |
| pool/dex_pool_state | liquidity?:f64, sqrt_price_x96?:string, price?:f64 | symbol | 1 |
| pool or dex_pool/dex_pool_swaps | amount0:f64, amount1:f64, price:f64 | symbol/pool_id | 1 |
| lst/lst_rates | exchange_rate:f64 | symbol | 1 |
| spot_asset/gas_fees | base_fee_gwei?, priority_fee_gwei? | symbol | 1 |
| spot_asset/oracle_prices | price:f64 | symbol | 1 |
| perpetual/perp_funding | funding_rate:f64 | symbol | 1 |
| perpetual/perp_daily_ctx | mark_price:f64, day_ntl_vlm?, open_interest? | symbol | 1 |
| perpetual/perp_mark_price | mark_price:f64 | symbol | 1 |
| perpetual/derivative_ticker | funding_rate?, open_interest?, mark_price?, index_price? | symbol | 1 |
| perpetual/perp_trades | base_asset_amount_filled:f64, quote_asset_amount_filled:f64, oracle_price? | symbol | 1 |
| perpetual/perp_mark_oracle | oracle_price_twap:f64, mark_price_twap:f64 | symbol | 1 |
| perpetual/perp_open_interest | base_asset_amount_with_amm:f64 | symbol | 1 |
| dex_pool/dex_orderbook | bid_price?/bid_size?/ask_price?/ask_size? (all f64) | symbol | 1 |
| dex_pool/dex_quote | input_amount:f64, output_amount:f64, price_impact_pct? | symbol | 1 |
| dex_pool/dex_trades | input_amount:f64, output_amount:f64, input_token?, output_token? | symbol | 1 |
| staking/eigenlayer_rewards | reward_amount:f64 | symbol | 1 |
| staking or yield_bearing/yield_snapshots | apy:f64 | symbol | 1 |
| staking/native_staking_rates | epoch:i64, validator_vote_account?, commission_pct?, base_apy:f64, mev_apy?, total_apy:f64 | symbol | 1 |
| yield_bearing/vault_share_price | share-price fields (not fully read) | symbol | — |
| lending/liquidation_events | collateral_asset, debt_asset, collateral_amount, debt_amount (all f64/str), liquidator?, user? | symbol | 0 |
| lending/flash_loan_events | asset:str, amount:f64, premium?, initiator?, borrower? | symbol | 0 |
| staking/staking_yields | apy:f64, total_staked? | symbol | 1 |
| spot_asset/token_transfers | token_address:str, from_address?, to_address?, amount:f64, tx_hash? | symbol | 1 |
| spot_asset/bridge_events | source_chain:str, dest_chain:str, token:str, amount:f64, depositor?, recipient? | symbol | 0 |
| lending/position_data | user?, supplied_usd?, borrowed_usd?, health_factor? | symbol | 1 |
| spot_asset/mev_events | relay:str, block_number?, builder_pubkey?, value_eth? | symbol | 0 |
| spot_asset/governance_events | proposal_id:str, event_type:str, voter?, support?, votes? | symbol | 0 |
| spot_asset/aggregator_route | token_in/out:str, amount_in/out:f64, route_kind:str, route_json:str, source:str, quote_block_number?, captured_at:datetime | instrument_id | 0 |
| lending/supply_apy | supply_apy:f64 | symbol | 1 |
| lending/borrow_apy | borrow_apy_variable:f64, borrow_apy_stable? | symbol | 1 |
| lending/utilisation | utilisation_rate:f64 | symbol | 1 |
| lending/liquidation_threshold | liquidation_threshold:f64, ltv? | symbol | 1 |
| lending/emode_params | emode_category:i64, emode_ltv:f64, emode_liquidation_threshold:f64 | symbol | 1 |

### Credentials/testnet (real, code-confirmed)

The Graph: 9-key round-robin GSM pool. Alchemy: single key. **AAVE**: real Sepolia testnet auto-resolution
(`get_testnet_contract_registry()`/`is_known_testnet()`). **Solana LST (Marinade/Jito/Solblaze)**: real public
devnet auto-routing in paper/backtest mode. **Symbiotic**: real live connector shipped 2026-08-16
(`SymbioticConnector`, `supports_live=True`). **Karak, Pendle**: connector files exist, not in the live
`DEFI_VENUE_TO_CONNECTOR_CLASS` map. CCTP (Circle cross-chain USDC bridge): connector file exists. ~20 other
connector files each carry a real, checkable `supports_live` attribute — only Symbiotic was spot-checked this pass.

---

## TradFi

### Per-venue rollup (all 9 venue keys incl. retired BARCHART)

| Venue | captured | empty_confirmed | attempted_failed | expected_unattempted | total | coverage_pct | all_shards_pct |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CME | 2,987,999 | 1,432,813 | 139,856 | 65,747 | 4,626,415 | 93.56% | 64.59% |
| NYSE | 4,517,118 | 1,394,694 | 106,016 | 133,719 | 6,151,547 | 94.96% | 73.43% |
| NASDAQ | 546,297 | 2,139,367 | 21,494 | 135,422 | 2,842,580 | 77.69% | 19.22% |
| CBOE | 37,392 | 86,343 | 36,534 | 67,058 | 227,327 | 26.52% | 16.45% |
| FRED | 17,264 | 2,342 | 75,033 | 0 | 94,639 | 18.70% | 18.24% |
| FX | 3,591 | 10,920 | 11,748 | 4,838 | 31,097 | 17.80% | 11.55% |
| KRX | 4,365 | 17,879 | 12,921 | 8,289 | 43,454 | 17.07% | 10.05% |
| ICE | 2,643 | 16,730 | 398,028 | 0 | 417,401 | 0.66%¹ | 0.63% |
| BARCHART (retired, inert) | 0 | 9,119 | 0 | 0 | 9,119 | 100.0%² | 0.0% |

¹ ICE's `FUTURE`/`COMBO` cells are ~100% `attempted_failed` — no ICE dataset is in the Databento subscription; every
request structurally fails, by design (fails loud, not silently skipped). Only the Yahoo-sourced DXY `INDEX` cell
has real captures. ² Formula artifact (0/0 denominator) — real read is `all_shards_pct=0.0%`, zero real data.

### Substantive (venue × instrument_type × data_type) cells — every cell with captured &gt; 0 (of 244 total cells)

| Venue | Instrument type | Data type | Captured | Empty-conf. | Att.-failed | Exp.-unatt. | Coverage % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| CME | FUTURE | ohlcv_1m | 424,765 | 16,235 | 21 | 0 | 100.0 |
| CME | FUTURE | ohlcv_1s | 435,234 | 120,601 | 78 | 0 | 99.98 |
| CME | FUTURE | trades | 6,043 | 20 | 96 | 0 | 98.44 |
| CME | FUTURE | tbbo | 507 | 0 | 0 | 0 | 100.0 |
| CME | FUTURE | ohlcv_15m | 696 | 0 | 860 | 0 | 44.73 |
| CME | COMBO | ohlcv_1m | 948,864 | 365 | 294 | 904 | 99.87 |
| CME | COMBO | ohlcv_1s | 859,393 | 601,830 | 0 | 763 | 99.91 |
| CME | combo | trades | 46,869 | 0 | 0 | 0 | 100.0 |
| CME | futures_chain | futures_chain (snapshot) | 2,095 | 0 | 0 | 0 | 100.0 |
| CME | futures_chain | ohlcv_1m | 75,227 | 114,062 | 2,012 | 24,009 | 74.30 |
| CME | futures_chain | ohlcv_1s | 74,936 | 118,687 | 1,931 | 23,214 | 74.88 |
| CME | futures_chain | tbbo | 40 | 2,281 | 0 | 135 | 22.86 |
| CME | futures_chain | trades | 1,870 | 1,954 | 0 | 135 | 93.27 |
| CME | options_chain | ohlcv_1m | 3,448 | 58,976 | 1,444 | 14,443 | 17.83 |
| CME | options_chain | ohlcv_1s | 3,386 | 0 | 1,450 | 0 | 70.02 |
| CME | options_chain | options_chain (snapshot) | 104,540 | 0 | 0 | 0 | 100.0 |
| CME | options_chain | trades | 67 | 18,957 | 0 | 2,144 | 3.03 |
| CBOE | FUTURE | ohlcv_15m | 5,004 | 0 | 0 | 0 | 100.0 (stray) |
| CBOE | FUTURE | ohlcv_1m | 9,145 | 30,275 | 0 | 28,371 | 24.38 |
| CBOE | FUTURE | ohlcv_1s | 9,163 | 29,920 | 0 | 26,737 | 25.52 |
| CBOE | FUTURE | ohlcv_24h | 1,192 | 0 | 0 | 0 | 100.0 |
| CBOE | INDEX | ohlcv_24h | 7,482 | 1,556 | 7,397 | 0 | 50.29 |
| CBOE | futures_chain | ohlcv_1m | 3,112 | 0 | 0 | 0 | 100.0 |
| CBOE | futures_chain | ohlcv_1s | 2,292 | 0 | 0 | 0 | 100.0 |
| CBOE | options_chain | ohlcv_1m | 2 | 0 | 0 | 0 | 100.0 |
| FRED | BOND | yield_curve | 14,399 | 0 | 0 | 0 | 100.0 |
| FRED | INDEX | ohlcv_1d | 2,865 | 0 | 0 | 0 | 100.0 |
| FX | SPOT_PAIR | ohlcv_24h | 3,272 | 1 | 643 | 0 | 83.58 |
| FX | nan | ohlcv_24h | 319 | 946 | 1,454 | 0 | 17.99 |
| ICE | INDEX | ohlcv_24h | 1,901 | 0 | 1,585 | 0 | 54.53 |
| ICE | futures_chain | futures_chain | 661 | 0 | 0 | 0 | 100.0 |
| ICE | futures_chain | ohlcv_1m | 81 | 9 | 0 | 0 | 100.0 |
| KRX | EQUITY | ohlcv_24h | 4,365 | 422 | 3,327 | 8,289 | 27.31 |
| NASDAQ | EQUITY | ohlcv_15m | 172,784 | 4,785 | 12,496 | 4,567 | 91.01 |
| NASDAQ | EQUITY | ohlcv_1m | 318,862 | 980,337 | 3,792 | 72,450 | 80.70 |
| NASDAQ | EQUITY | ohlcv_1s | 45,810 | 914,271 | 3,792 | 39,202 | 51.59 |
| NASDAQ | EQUITY | tbbo | 2,493 | 3,392 | 420 | 4,567 | 33.33 |
| NASDAQ | EQUITY | trades | 4 | 3,391 | 14 | 4,514 | 0.09 |
| NASDAQ | ETF | ohlcv_15m | 3,353 | 988 | 132 | 72 | 94.26 |
| NASDAQ | ETF | ohlcv_1m | 1,224 | 16,972 | 198 | 484 | 64.22 |
| NASDAQ | ETF | ohlcv_1s | 1,167 | 19,430 | 198 | 144 | 77.34 |
| NYSE | EQUITY | ohlcv_15m | 1,359,843 | 2,431 | 55,337 | 4,329 | 95.80 |
| NYSE | EQUITY | ohlcv_1m | 2,491,541 | 465,854 | 22,219 | 71,287 | 96.38 |
| NYSE | EQUITY | ohlcv_1s | 356,411 | 420,924 | 22,219 | 40,865 | 84.96 |
| NYSE | EQUITY | tbbo | 10,567 | 1,801 | 1,164 | 4,290 | 65.96 |
| NYSE | EQUITY | trades | 155 | 1,805 | 0 | 4,290 | 3.49 |
| NYSE | ETF | ohlcv_15m | 179,912 | 3,672 | 580 | 0 | 99.68 |
| NYSE | ETF | ohlcv_1m | 59,349 | 65,853 | 870 | 0 | 98.56 |
| NYSE | ETF | ohlcv_1s | 59,172 | 41,866 | 870 | 0 | 98.55 |

~180 of the remaining 244 cells are zero-captured: legacy/blank-instrument_type placeholder skeletons (harmless), or
cells 100% `attempted_failed`/`expected_unattempted` where the source structurally can't serve it (e.g. every
`mbp_10` cell across all 9 venues is captured=0 — CME mbp_10 is deferred to post-cutover scope, no working fetch
path exists today for any venue).

### Readiness — 19-step contract + granularity table

| # | Step | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | Declared | PASS | 8 venues, 1 entry each (ICE/KRX carry a `databento` label despite being Yahoo-sourced — flagged not fixed) |
| 2 | Reference data | Partial pass | Adapters reachable for all 8; a 9th (`ibkr.py`) exists but is confirmed dead code (unreached in production, 2026-07-31 audit) |
| 3 | Market data — batch | Measured | Layer-1 67.74% (21/31), Layer-2 reachable 86.96% |
| 4 | Market data — live | Unverified | Most recent confirmation dated 2026-06-21, with its own staleness caveat |
| 5 | Features | Out of scope | — |
| 6–9 | Position read/slot/instruction/transfers | Unverified | Real tradfi-specific code exists (VWAP/TWAP/IS algos, IBKR execution adapter) but not cross-referenced per-action/per-mode |
| 10 | Error semantics | Mechanism pass, completeness unverified | `VENUE_ERRORS_TRADFI` covers 7 sources (source-keyed not venue-keyed; `ecb`/`ofr` have no corresponding declared venue) |
| 11 | Config | Genuinely unsettled workspace-wide | Not tradfi-specific — the umbrella plan's own open `[OPERATOR]` design ruling |
| 12 | Reachability | Mixed | Databento data path reachable (real captures prove it); IBKR reference-data path dead; IBKR execution path unverified |
| 13 | Granularity declared | PASS (real per-venue start dates — see table below), but NOT the fidelity-tier declaration the contract's step 13 formally asks for | See table below |
| 14 | Derivation path | Partial pass | Real MDPS re-aggregation confirmed for future/equity/etf/futures_chain/index/options_chain; `combo` deliberately excluded (documented crash history) |
| 15 | Trigger frequency | Unverified | — |
| 16 | Matching class | Mechanism pass / zero production callers | `refuse_unservable` shipped fleet-wide 2026-08-16, no live caller passes `refuse_unservable=True` yet |
| 17–18 | Consumability | Mechanism confirmed, not run for tradfi | — |
| 19 | Orthogonality | Not run | Umbrella plan's own audit todo still unstarted |

**Granularity table** (real, per venue, `VENUE_DATA_TYPE_CAPABILITIES`):

| Venue | Data type | Start date | Note |
| --- | --- | --- | --- |
| CME | ohlcv_1s/ohlcv_1m | 2019-01-01 | Databento GLBX.MDP3, L0/free |
| NASDAQ | ohlcv_1m/ohlcv_1s | 2023-04-15 | Databento DBEQ.BASIC |
| NASDAQ | ohlcv_1h | 2026-01-01 | Yahoo interim (Databento billing-suspension workaround, added 2026-08-12) |
| NYSE | ohlcv_1m/ohlcv_1s | 2023-04-15 | Databento DBEQ.BASIC |
| NYSE | ohlcv_1h | 2026-01-01 | Yahoo interim, same reason |
| CBOE | ohlcv_1s/ohlcv_1m | 2018-11-04 | Databento XCBF.PITCH (VX futures) |
| CBOE | ohlcv_24h | 2000-01-03 | Yahoo, US Treasury yield tenors |
| ICE | ohlcv_24h | 2019-01-02 | Yahoo, DXY index — the only fetchable ICE instrument |
| FX | ohlcv_24h | 2020-01-01 | Yahoo, KRW/USD daily — no intraday |
| KRX | ohlcv_24h | 2019-01-02 | Yahoo `.KS` daily — no intraday |
| FRED | yield_curve/ohlcv_1d | 1962-01-02 | FRED API |

No venue declares trades/tbbo/mbp_10 in the CURRENT capability table (2026-05-15 MVP narrowing) — historical
captures of those exist as "strays," not gaps.

### Per-shard schemas (14 static + dynamic re-aggregated set, exhaustive)

**Trades**: future/equity/etf trades = price(f64,NN) + size(f64,NN). index/combo trades = price only, no size.
options_chain trades: symbol_column=underlying + price, size, strike(f64,NN), expiry_date(datetime,NN),
option_right(string,NN).

**Native OHLCV** (`future/ohlcv_1m` + 8 aliases incl. futures_chain/combo/UNKNOWN at 1m and 1s): open/high/low/close
(f64, non-nullable), volume(f64, nullable). Same shape for equity/etf.

**Snapshots** (carry `venue`, unlike trades contracts): `options_chain/options_chain`: instrument_id, venue,
underlying, ts_event, strike, expiry_date, option_right, bid/ask_price, bid/ask_size, last_price, open_interest,
volume (price/size fields f64 nullable). `futures_chain/futures_chain`: same minus strike/option_right, + expiry_date.

**Dynamically-registered re-aggregated candles** (`_candle_contracts.py` build loop, confirmed by reading the loop
directly): future/equity/etf/futures_chain at {5m,15m,1h,4h,1d}+ohlcv_24h; options_chain at {1m,15m,1h,1d}+ohlcv_24h;
index at {1m,5m,15m,1h,1d}+ohlcv_24h. **`combo` deliberately excluded from all re-aggregated timeframes** — a live
2026-08-03 MDPS run crashed ("No SchemaContract registered") on COMBO at every re-aggregated timeframe; UAC's
`VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[("tradfi","combo")]` deliberately excludes 15m/24h. Column shape:
instrument_id, symbol/underlying, ts_event, OHLC(f64 nullable — a bar can have zero trades), volume(f64 nullable),
trade_count(int64 nullable).

**Confirmed gaps — real captured data, NO registered schema** (zero-hit grep, re-verified): `tbbo` (real captures at
CME/NYSE/NASDAQ, up to 65.96% coverage) — no tradfi SchemaContract exists (cefi has one, tradfi doesn't). `mbp_10` —
zero real captures anywhere, consistent with deferred-to-post-cutover. `yield_curve` — **14,399 captured, 100%
coverage, FRED's flagship data type** — no SchemaContract exists anywhere for it. `macro_result` — zero real
captures; a code comment confirms this is dead/wrong vocabulary (the live FredAdapter never writes it).

**Reference-data schema** (`InstrumentRecord`, shared across all AGs): instrument_key, venue, instrument_type,
raw_symbol, base_asset, quote_asset, canonical_instrument_id, product_root, name, status, available_from/to_datetime,
asset_class, settle_asset, tick_size, min_size, contract_size, expiry, strike, option_type, exercise_style,
underlying, margin_type, legs (COMBO multi-leg), is_trading_day, 7 session-time cols, holiday_calendar, timezone,
source_archive_url_template, source_record_types, source_coverage_start/end, listed_at, delisted_at. Hard-enforced:
FUTURE/OPTION require non-null expiry (pydantic ValueError otherwise).

### Credentials/testnet

Databento (CME/NASDAQ/NYSE/CBOE-futures/KRX-label): single API key (`databento-api-key`); SSOT's own incident log
records a billing suspension discovered 2026-08-14 (live WS heartbeating with zero real ticks for ~50h, undetected
by liveness alone). FRED: needs its own key, exact secret name not found in 2 locations checked (0 hits ≠ missing).
Yahoo Finance: no credential needed (public endpoints). IBKR reference-data adapter: confirmed dead. IBKR execution
adapter: present, live-invocation unverified. **`/api/venue-credentials` only probes Tardis — zero live credential-
health coverage for any TradFi venue exists today.**

---

## Sports

### Venue-universe reconciliation detail

Requested Odds-API bookmaker scope: 23. Declared sports bookmaker venues (route=aggregator:ODDS_API): 31. Direct-
adapter exchange: 1 (BETFAIR). Reference-data sources: 5 (api_football, footystats, understat, transfermarkt,
soccer_football_info). Canonical total: 37. Physical manifest keys: 45 — the extra 8 are historically-observed
bookmakers no longer in current scope (BETANO_UK, BETFRED_UK, BETUS, BOYLESPORTS, FANATICS, GROSVENOR, LEOVEGAS,
LOWVIG, MYBOOKIEAG, WILLIAMHILL_US, SPORT888, LADBROKES_UK + bare LADBROKES) plus 3 data-quality artifacts: blank
venue (9 rows), "UNKNOWN" (3 rows), "FOOTBALL" (910 rows — see write-path bug below). KALSHI also appears (20,785
rows, 100% empty_confirmed) despite nominal exclusion from the sports-odds bookmaker scope — boundary case, not
resolved (Kalshi may have separate sports-contract markets distinct from Polymarket-style prediction markets).

**Bookmaker spelling drift confirmed live**: `SOCCER_EPL`/`SOCCER_ITALY_SERIE_A` (raw Odds-API `sport_key` values)
appear as stray `instrument_type` values in the live manifest, not just historically.

### Layer 1 — 13 missing tuples, full list

BETFAIR_EX_EU/odds/trades · BETOPENLY/odds/odds · BETOPENLY/odds/trades · BETSSON/odds/trades · NOVIG/odds/odds ·
NOVIG/odds/trades · ONEXBET/odds/odds · ONEXBET/odds/trades · PINNACLE/odds/trades · PROPHETX/odds/odds ·
PROPHETX/odds/trades · UNIBET/odds/trades · UNIBET_EU/odds/trades. 4 (BETOPENLY/NOVIG/ONEXBET/PROPHETX) are genuine
zero-coverage venues (confirmed via registry: batch=None, honestly declared). The other 9 (PINNACLE/BETSSON/UNIBET/
UNIBET_EU/BETFAIR_EX_EU showing missing "trades" alongside already-captured "odds") are very likely an artifact of
the in-flight `SPORTS_ODDS_DATA_TYPE_CANONICAL_FORM` trades→odds vocabulary collapse (contract landed, physical
re-stamp still P2-scope) — not fully confirmed.

**754 strays**: 10 distinct data_type tokens (arbitrage_opportunity, odds, odds_horizon_bucket[+4 window variants],
odds_movement, odds_snapshot, trades); **84 distinct instrument_type tokens** — the overwhelming majority are
per-market-line spreads (`ASIAN_HANDICAP_0_25`...`ASIAN_HANDICAP_M5_5` = 39 variants, `OVER_UNDER_0_5`...
`OVER_UNDER_8_5` = 27 variants) plus MATCH_ODDS/MATCH_ODDS_LAY/ODDS, the sport-key leak, venue-names-as-
instrument_type (PADDYPOWER/PINNACLE/SPORT), and 11 lowercase-bookmaker-as-instrument_type values under the FOOTBALL
artifact. 44 distinct stray venues. This is a genuine Step-19 orthogonality candidate: the writer captures at
per-market-line granularity (richer signal) while UAC's expected matrix only declares the coarse odds/trades cell.

### Per-data_type rollup (asset-group level)

| data_type | captured | empty_confirmed | attempted_failed |
| --- | ---: | ---: | ---: |
| odds | 546,947 | 21,181 | 0 |
| odds_horizon_bucket | 5,600,637 | 652 | 26,548 |
| trades | 1,599 | 5 | 0 |
| odds_movement | 17,834 | 2 | 4,106 |
| odds_snapshot | 17,951 | 2 | 2,397 |
| arbitrage_opportunity | 17,851 | 0 | 2,505 |
| odds_horizon_bucket_15m/1d/1h/4h (4 tokens) | 0 each | 177–207 each | 34–49 each |
| ARBITRAGE_OPPORTUNITY/ODDS_MOVEMENT/ODDS_SNAPSHOT (uppercase legacy) | 0 each | 2–3 each | 0 |

Worst-performing venues (real, not sampled): FOOTBALL 0.0% (artifact) · BETMGM 28.43% (1,126/3,960) · BOVADA 31.30%
(1,572/5,023) · BETWAY 36.87% (1,375/3,729) — all 3 are the 2025-07-31-onboarded cohort, consistent with in-progress
backfill. KALSHI 100% `coverage_pct` but 0.0% `all_shards_coverage_pct` (all 20,785 rows empty_confirmed). Everything
else ≥88% (most ≥99%).

### Readiness — 19-step contract

| # | Step | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | Declared | Partial pass | 754-stray finding shows declared grain ≠ writer grain |
| 2 | Reference data | PASS | Real, complete api_football-sourced `SPORTS_LEAGUES`/`SPORTS_TEAMS`/`SPORTS_VENUES`/`SPORTS_STANDINGS` |
| 3 | Market data — batch | Pass in substance, one clause unverified | 6.2M captured rows, 99.43% reachable (lower-bounded); per-data-type smoke test not run |
| 4 | Market data — live | Unverified | Interrupted before confirming |
| 5 | Features | Unverified (fails-open) | None of the 5 confirmed archetypes are sports-relevant; sports' 4 archetypes are among the 54 undeclared |
| 6 | Position read | Unverified | Not checked |
| 7 | Slot eligibility | PASS | Real, populated: 5 SPORTS_* slots + 4 PREDICTION_ARB_* slots in `archetype_slots_sports.py` |
| 8 | Execution — instruction | Contradictory signals, flagged not resolved | UAC says `NO_ADAPTER_YET` for nearly every bookmaker; execution-service has real adapters (betfair.py 747 lines, matchbook.py 519 lines, kalshi.py, polymarket_clob.py) wired through a real `SportsExecutionRouter` |
| 9 | Transfers | Unverified | Not checked |
| 10 | Error semantics | PASS | Real, comprehensive — 15 sources classified, coherent design (aggregator-routed bookmakers correctly have no individual entry) |
| 11 | Config | FAIL, mock-only | `sports_venues.py` live mode returns `{"venues":[], "status":"live_not_configured"}` verbatim on every endpoint |
| 12 | Reachability | Unverified | Not traced |
| 13 | Granularity declared | PASS, and richer than declared | Real measured `batch_start_date`s per venue; actual granularity is finer (per-market-line) |
| 14 | Derivation path | Pass in substance | Real schemas exist (SPORTS_ODDS_SNAPSHOT/MOVEMENT/HORIZON_BUCKET); consumer-tracing not done |
| 15 | Trigger frequency | Unverified | — |
| 16 | Matching class | Ruled (operator), code-encoding unverified | Umbrella plan already rules sports odds a distinct non-orderbook class |
| 17 | Strategy consumability | Cannot pass under the automated check | Same root cause as step 5 |
| 18 | Data-type consumability | Not run for sports specifically | — |
| 19 | Orthogonality | Evidenced gap, not fixed | 84-distinct-instrument_type stray finding is directly on point |

### Per-shard schemas — 22 registered `CONTRACT_REGISTRY` entries (21 in-scope + 1 features-adjacent, exhaustive)

**API-Football reference**: `leagues` (5 cols) · `teams` (16 cols, per-season) · `venues` (12 cols, singleton) ·
`standings` (29 cols).

**API-Football match-fact**: `fixtures` (45 cols — af_fixture_id, referee, date/timestamp, periods, venue,
status×3, af_league/season/round, af_home/away_id+name, scores×8 splits, 8 phase-timestamp cols, extra-time/
penalty splits×8, went_to_extra_time/penalties, match_result, day, available_at) · `fixture_events` (12 cols) ·
`fixture_stats` (22 cols) · `fixture_lineups` (12 cols) · `player_stats` (38 cols) · `injuries` (11 cols).

**Transfermarkt**: `player_values` (10 cols).

**SFI**: `sfi_progressive_stats` (~60 cols — timer/possession/attacks/shots/cards/dominance + 1X2/OU/AH/AC odds
incl. first-half equivalents).

**Derived/other providers**: `matches` (footystats, 54 cols) · `predictions` (footystats, 29 cols) · `xg`
(understat, 45 cols, mirrors matches minus canonical_fixture_id) · `xg_shots` (understat, 17 cols) · `weather`
(open_meteo, 72 cols — 3 forecast windows × 18 cols + 4 aggregates × 3) · `fixture_features` (26 cols,
features-adjacent, out of ML-exclusion scope, listed for completeness only).

**Sports odds/tick data (MTDS-grain)**: `trades`/`SPORTS_ODDS_TRADES` (base; exchange_odds/fixed_odds variants are
byte-identical, 8 cols: instrument_id, bookmaker_key, bm_time(raw ISO string), source, league_id, fixture_id,
market_key, outcome_name, price) · `odds_horizon_bucket` (same 8 + horizon str) · `sports_odds_snapshot` (10 cols) ·
`sports_odds_movement` (10 cols) · `sports_arbitrage` (11 cols).

### Cross-cutting findings (not fixed, flagged)

UAC-vs-execution-service adapter-registry drift (step 8). 754 Layer-1 strays, dominated by 84-token instrument_type
proliferation. **`FOOTBALL` venue artifact (910 rows) — instrument_type values are literally lowercase bookmaker
names, a write-path column-swap bug.** Blank/UNKNOWN venue keys (9+3 rows). `honest-coverage-model.md`'s sports
certification is stale (30.77% vs fresh 79.03%). KALSHI-under-sports 0% real data, boundary not resolved.

### Credentials/testnet

No live credential-probe surface for sports bookmakers exists (`venue_credentials.py` is Tardis/CeFi-only;
`sports_venues.py` is mock-scaffolded, live mode fully stubbed). Real typed credential-loading exists in
`SportsExecutionRouter` for Betfair/Polymarket/Odds-API/Matchbook/Kalshi — populated-in-prod status not checked.
**Kalshi**: real testnet (`demo-api.kalshi.co`), `data_fidelity="synthetic"` on testnet orders. Betfair/Pinnacle/
Matchbook/Odds-API/Polymarket: `supports_testnet=False`. Real `PaperBettingAdapter` class exists.

---

## Prediction

### Layer 1 — 100% complete, and why the codex figure is stale

`expected_tuples=4, present_tuples=4, missing_tuples=0, completeness_pct=100.0%`. Both venues 2/2. 4 strays
(`market_lifecycle`+`prediction_canonical_question_group` × 2 venues) are by-design cluster/market-id-grain
exclusions per the UAC source comment, not gaps.

**Root cause of the stale codex figure (66.67%/22.73%, 2026-07-03)**: the UAC matrix entry
`("prediction","prediction_market"): frozenset({"trades","book_snapshot_5"})` was deleted 2026-07-07 (4 days after
that measurement), causing `EXPECTED=0`/`denominator_status=UNDEFINED` from then until 2026-08-15, when it was
re-added. The cited figure predates the broken-measurement window entirely.

### Per-venue and per-cell Layer 2

| Venue | captured | empty_confirmed | attempted_failed | expected_unattempted | total | reachable coverage_pct | all_shards_pct |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| POLYMARKET | 265,198 | 1,999,742 | 15,801 | 3,864 | 2,284,605 | 93.10% | 11.61% |
| KALSHI | 213,440 | 283,482 | 15,679 | 2,306 | 514,907 | 92.23% | 41.45% |

| Venue | data_type | captured | empty_confirmed | attempted_failed | expected_unattempted | total | reachable coverage_pct |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| POLYMARKET | trades | 254,997 | 905,972 | 7,902 | 0 | 1,168,871 | 96.99% |
| POLYMARKET | book_snapshot_5 | 2,434 | 1,030,314 | 7,899 | 0 | 1,040,647 | 23.56% (thin) |
| POLYMARKET | prediction_canonical_question_group | 7,767 | 57,482 | 0 | 3,864 | 69,113 | 66.78% |
| POLYMARKET | market_lifecycle (lowercase) | 0 | 974 | 0 | 0 | 974 | 100.0%* |
| POLYMARKET | MARKET_LIFECYCLE (uppercase legacy) | 0 | 974 | 0 | 0 | 974 | 100.0%* |
| KALSHI | trades | 179,218 | 150,151 | 15,665 | 0 | 345,034 | 91.96% |
| KALSHI | book_snapshot_5 | 20,689 | 106,012 | 0 | 0 | 126,701 | 100.0% (reachable; all_shards only 16.33%) |
| KALSHI | prediction_canonical_question_group | 13,533 | 19,483 | 14 | 2,306 | 35,336 | 85.37% |
| KALSHI | market_lifecycle (lowercase) | 0 | 1,306 | 0 | 0 | 1,306 | 100.0%* |
| KALSHI | MARKET_LIFECYCLE (uppercase legacy) | 0 | 1,306 | 0 | 0 | 1,306 | 100.0%* |

\* 0/0 reachable-denominator formula artifact — real story is **0 captured rows across both venues, both casings**,
despite real writer code (`kalshi.py`/`polymarket/parsing.py`) explicitly designed to populate this data type.

**96.75% of the 2,283,224 POLYMARKET empty_confirmed rows carry no typed absence reason** ("unexplained") — the
largest single data-quality signal in this audit (only 3.25% are typed `out_of_window`, 0% `reference_only`).
Secondary/legacy bucket was unreachable this pass, so `expected_unattempted` may be a slight undercount relative to
a full merged view.

### Readiness — 19-step contract

| # | Step | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | Declared | VERIFIED | Full registry population for both venues |
| 2 | Reference data | VERIFIED | Real, substantial adapters (kalshi.py 1000+ lines, polymarket/) |
| 3 | Market data — batch | Verified substantively | Real captured rows both data types both venues; smoke-test-pass clause itself not run |
| 4 | Market data — live | Verified (existence) | Real WS connectors for both venues (trades/ws/clob_ws/perp_ws each) |
| 5 | Features | Verified at AG level, venue-parity unverified | 6 feature groups consume (prediction,trades); only 1 also consumes book_snapshot_5; all 6 Polymarket-named, KALSHI parity not traced |
| 6 | Position read | Unverified | Not traced per-mode |
| 7 | Slot eligibility | Unverified-by-SSOT, real code exists | Real 309-line archetype (`prediction_venue_dispersion.py`) exists; new formal SSOT declares 0 hits for polymarket/prediction |
| 8 | Execution — instruction | VERIFIED | `PredictionBetHandler`, `SUPPORTED_VENUES={POLYMARKET,KALSHI}`, real EIP-712/HMAC auth adapters |
| 9 | Transfers | Unverified | Only an adjacent instruction-validation fix found, not deposit/withdraw rails |
| 10 | Error semantics | Unverified | Not checked |
| 11 | Config | Unverified (0 hits, may be wrong vocabulary) | A GSM secret slot exists; no dedicated config.py-style schema module found |
| 12 | Reachability | Unverified | Not traced |
| 13 | Granularity declared | NOT DONE | Fleet-wide gap |
| 14–15 | Derivation/trigger | Unverified | Not checked |
| 16 | Matching class | Data shape answered (CLOB, not sports-style), formal registry declaration unverified | book_snapshot_5 carries real bid/ask JSON arrays up to 50 levels; connectors literally named clob_ws |
| 17 | Consumability | Same as step 7 | — |
| 18 | Data-type consumability | Partial | trades+book_snapshot_5 confirmed consumed; the 2 lifecycle/cluster types serve an operational role, neither formally declared-unused |
| 19 | Orthogonality | Real, named finding | `market_lifecycle`/`MARKET_LIFECYCLE` casing duplicate, acknowledged in source, still both live |

### Per-shard schemas — exhaustive, all 4 registered contracts + 1 dataclass

**`trades`** (`PREDICTION_PREDICTION_MARKET_TRADES`, symbol_column=condition_id, min rows 1): instrument_id, venue,
chain, ts_event, price(f64), size(f64), side(str), outcome(str — Yes/No/Up/Down/branded), outcome_index(i64),
condition_id(str), asset_id(str — per-outcome ERC-1155 token id), underlying(str, required), asset_group(str —
cross-venue market category), market_type(str — binary/scalar/categorical/ranked/range_bracket),
resolution_period(str).

**`book_snapshot_5`** (`PREDICTION_PREDICTION_MARKET_BOOK_SNAPSHOT`, symbol_column=condition_id): instrument_id,
ts_event, condition_id, asset_id, bids(str — JSON array [price,size], up to 50 levels), asks(same), venue, chain
(POLYGON for Polymarket, ETHEREUM for Kalshi), market_category(str — UAC taxonomy).

**`market_metadata`** (`PREDICTION_PREDICTION_MARKET_METADATA`, symbol_column=condition_id) — has a registered
schema but does NOT appear in the live capture vocabulary: instrument_id, condition_id, question(str), market_slug?,
event_slug?, end_date_iso?, active(bool), closed(bool), volume?(f64), liquidity?(f64), tokens(str — JSON array of
{token_id,outcome,price,winner}), ts_event.

**`fills`** (`PREDICTION_PREDICTION_MARKET_FILLS`, symbol_column=condition_id) — also schema-registered but not in
the live capture vocabulary: instrument_id, ts_event, fill_id, order_id, condition_id, asset_id, price, size, side,
fee?, maker?(wallet address), taker?, venue, chain.

**`market_lifecycle`/`MARKET_LIFECYCLE`** — no `SchemaContract`, a Python dataclass instead (`MarketLifecycle`):
market_id, venue, canonical_group(enum), market_created_at, resolution_time, settlement_time,
current_status(Literal["created","active","resolved","settled"]) — measured at zero captured rows (see above).

**`prediction_canonical_question_group`** — vocabulary confirmed (73-member `CanonicalQuestionGroup` StrEnum +
`CanonicalGroupMetadata`: group, cadence, expected_market_ids_per_day, resolution_basis, settlement_lag) — no
explicit column-level `SchemaContract` for the actual parquet rows was located, only the key vocabulary.

### Credentials/testnet

GSM slot reserved (`credentials-matrix.md`, "60d rotation" — populated status not verified). **Kalshi**: real coded
demo host (`demo-api.kalshi.co`), env param supports mainnet/testnet. **Polymarket**: 2-layer credential derivation
(L1 wallet key → EIP-712 → L2 CLOB creds); **no demo/testnet host found anywhere, and no written ruling exists on
how it would be paper-traded** — a real gap against the readiness contract's own "settled, recorded answer"
requirement. Fee model: Polymarket 2% on winnings, Kalshi ~1%/contract.

---

## Deliberately not preserved (regenerable from source, not durable-quality code)

The 5 sub-agents' throwaway measurement scripts and raw downloaded JSON snapshots (~17.5MB, in this session's
scratchpad) are NOT promoted here — they're fully reproducible from the live `coverage.json` in
`gs://central-element-323112-honest-coverage/2026-08-16/` (a durable system, not ephemeral) plus the UAC source
files cited throughout. Re-running the same 5-sub-agent dispatch against a later date would reproduce equivalent
output; the source data itself was never at risk.
