---
type: analysis
title: MTDS Global Ledger PricingLedger Audit
epic: global_ledger_pnl_attribution_master
auditor: slot-7-agent
date: "2026-05-23"
status: complete
source:
  - market-tick-data-service/market_tick_data_service/engine/orchestrator.py
  - market-tick-data-service/market_tick_data_service/market_interface/schemas.py
  - market-tick-data-service/market_tick_data_service/cli/handlers/perp_funding_handler.py
  - market-tick-data-service/market_tick_data_service/cli/handlers/lending_indices_handler.py
  - market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py
  - market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain_perps/hyperliquid_adapter.py
  - market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain_perps/aster_adapter.py
  - market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/aave_positions.py
  - unified-api-contracts/unified_api_contracts/canonical/domain/derivatives/__init__.py
  - unified-api-contracts/unified_api_contracts/canonical/domain/market/__init__.py
  - unified-api-contracts/unified_api_contracts/registry/schema_spec.py
  - unified-api-contracts/unified_api_contracts/registry/market_data_categories.py
parent_plan: plans/active/global_ledger_pnl_attribution_discovery_2026_05_21.md
---

# MTDS Global Ledger PricingLedger Audit — 2026-05-23

**Scope**: Read-only audit of market-tick-data-service (MTDS) as the designated PricingLedger writer. **Method**: Static
code reading of engine orchestrator, per-data-type handlers, adapter schemas, and UAC contracts. **Coverage note**: This
audit is exhaustive for code-level schema mapping. It does NOT sample actual GCS parquet files — runtime divergence
between code schema and on-disk data is a separate audit (A3/A4 mega-audit path).

---

## Data Types Written by MTDS (Pricing-Relevant)

| data_type           | Asset Group              | Venues / Protocols                                                                                                                | Key Fields Written                                                                                                                                                                                                     | Cadence                                                                                               |
| ------------------- | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `book_snapshot_5`   | CeFi                     | BINANCE-SPOT/FUTURES, BYBIT, OKX-SPOT/FUTURES/SWAP, DERIBIT, COINBASE, UPBIT, HYPERLIQUID, ASTER, BITFINEX-_, BITGET-_, KRAKEN-\* | `bid_price_0..4`, `ask_price_0..4`, `bid_size_0..4`, `ask_size_0..4`, `timestamp` (top-5 levels)                                                                                                                       | Per-tick via Tardis CSV; base granularity 15s → aggregated to 1m/5m/15m bars                          |
| `derivative_ticker` | CeFi                     | BINANCE-FUTURES, BYBIT, OKX-SWAP, DERIBIT, HYPERLIQUID, ASTER, KRAKEN-FUTURES, etc.                                               | `last_price`, `mark_price`, `index_price`, `mid_price` (nullable), `funding_rate`, `predicted_funding_rate`, `next_funding_timestamp`, `open_interest`, `bid_price`, `ask_price`, `volume_24h`                         | Per-tick; base 15s                                                                                    |
| `options_chain`     | CeFi (Deribit)           | DERIBIT                                                                                                                           | `symbol`, `underlying`, `strike`, `option_type`, `expiration`, `bid_price`, `ask_price`, `bid_size`, `ask_size`, `implied_volatility`, `delta`, `gamma`, `theta`, `vega`                                               | Daily bulk CSV via Tardis `OPTIONS.csv.gz`; the CanonicalOptionsChainEntry model includes full greeks |
| `futures_chain`     | CeFi (Deribit, CME)      | DERIBIT, CME, ICE                                                                                                                 | `symbol`, `underlying`, `expiry`, `bid`, `ask`, `last`, `volume` — partitioned as `options_chain` (merged path)                                                                                                        | Daily bulk via Tardis `FUTURES.csv.gz`                                                                |
| `trades`            | CeFi, TradFi, Prediction | All venues (20+ CeFi, 5 TradFi, POLYMARKET, KALSHI)                                                                               | `venue`, `symbol`, `trade_id`, `timestamp`, `price`, `quantity`, `side`, `buyer_maker`, `instrument_key`                                                                                                               | Per-tick 15s base                                                                                     |
| `ohlcv_1m`          | TradFi                   | NASDAQ, NYSE, CME, ICE                                                                                                            | `timestamp`, `open`, `high`, `low`, `close`, `volume`                                                                                                                                                                  | 1-minute bars via Databento                                                                           |
| `ohlcv_15m`         | TradFi                   | CBOE (VIX), BARCHART, YAHOO_FINANCE                                                                                               | `timestamp`, `open`, `high`, `low`, `close`, `volume`                                                                                                                                                                  | 15-minute bars                                                                                        |
| `ohlcv_24h`         | TradFi                   | FX, YAHOO_FINANCE                                                                                                                 | `timestamp`, `open`, `high`, `low`, `close`, `volume`                                                                                                                                                                  | Daily bars                                                                                            |
| `tbbo`              | TradFi                   | CME (deferred — TRADFI_TICK_DATA_WINDOWS = [])                                                                                    | `timestamp`, top-of-book bid/ask                                                                                                                                                                                       | 15s base — **CURRENTLY DEFERRED** per operator direction 2026-05-15                                   |
| `perp_funding`      | DeFi                     | HYPERLIQUID, ASTER, GMX (ARBITRUM/AVALANCHE), PACIFICA, LIGHTER                                                                   | `protocol`, `coin`, `funding_rate`, `premium`, `timestamp`, `mark_price` (Aster only)                                                                                                                                  | Per-funding-interval (8h for most; hourly for GMX); written as daily parquet                          |
| `lending_indices`   | DeFi                     | AAVE_V3 (multi-chain), SPARK, COMPOUND_V3                                                                                         | `instrument_id`, `venue`, `chain`, `symbol`, `timestamp`, `liquidity_index`, `variable_borrow_index`, `liquidity_rate`, `variable_borrow_rate`, `stable_borrow_rate`, `supply_rate`, `borrow_rate`, `utilization_rate` | Sub-daily snapshots per The Graph subgraph (multiple per day)                                         |
| `lst_rates`         | DeFi                     | LIDO, ROCKETPOOL, COINBASE-CBETH, KELPDAO, RENZO, PUFFER, ETHERFI, JITO, MARINADE + others                                        | `timestamp`, `exchange_rate`, `apy`, `symbol`, `venue`, `chain`                                                                                                                                                        | Daily snapshot at noon-UTC block                                                                      |
| `oracle_prices`     | DeFi                     | AAVE_V3, Chainlink feeds                                                                                                          | `instrument_id`, `venue`, `chain`, `oracle_price_usd`, `price_usd`, `timestamp`                                                                                                                                        | Per-protocol daily; sampled snapshots                                                                 |
| `dex_pools`         | DeFi                     | UNISWAP_V3, CURVE, BALANCER, SUSHI, PANCAKESWAP, etc.                                                                             | `instrument_id`, `venue`, `chain`, `pool_address`, TVL, liquidity depth, fee tier                                                                                                                                      | 15m pass-through (no candle)                                                                          |
| `dex_swaps`         | DeFi                     | UNISWAP_V3, CURVE, ORCA, RAYDIUM, etc.                                                                                            | `instrument_id`, `venue`, `chain`, `token0`, `token1`, `amount0`, `amount1`, `fee_tier_bps`, `tx_hash`, `block_number`                                                                                                 | Per-swap event                                                                                        |
| `odds_snapshot`     | Sports                   | ODDS_API, PINNACLE, BETFAIR                                                                                                       | `fixture_id`, `bookmaker`, `market`, `outcome`, `price` (decimal odds), `point`, `captured_at`                                                                                                                         | 15m base                                                                                              |

**Note**: `market_state` is a UAC domain type (`CanonicalMarketStateEvent`) but does NOT appear as a standalone
MTDS-written data_type. It is a live-event domain object (halt/auction transitions). `fx_rates` is captured as
`ohlcv_24h` under venue=FX/YAHOO_FINANCE, not as a separate data_type.

---

## Carry-Family Rates Coverage

| Rate Type                      | Status                | Venues / Protocols                                                                          | Fields Available                                                                                           | Notes                                                                                                                                                   |
| ------------------------------ | --------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `funding_rate` (CeFi perp)     | **PRESENT**           | BINANCE-FUTURES (in `derivative_ticker`), BYBIT, OKX-SWAP, DERIBIT, HYPERLIQUID, ASTER      | `funding_rate`, `predicted_funding_rate`, `next_funding_timestamp` in `derivative_ticker` parquet          | Also via dedicated `perp_funding` data_type for HYPERLIQUID, ASTER, GMX, PACIFICA, LIGHTER at 8h interval                                               |
| `funding_rate` (DeFi perp)     | **PRESENT**           | HYPERLIQUID, ASTER, GMX, PACIFICA, LIGHTER                                                  | `funding_rate`, `premium`, `mark_price` (Aster/Pacifica)                                                   | Written by `perp_funding_handler.py`; field name: `funding_rate`                                                                                        |
| `lending_rate` / `borrow_rate` | **PRESENT**           | AAVE_V3 (ETH, ARB, OPT, POLYGON, BASE, AVALANCHE), SPARK, COMPOUND_V3                       | `liquidity_rate` (=supply APR), `variable_borrow_rate`, `stable_borrow_rate`, `supply_rate`, `borrow_rate` | Written as `lending_indices` data_type; `supply_apr` / `borrow_apr` in SchemaSpec                                                                       |
| `dividend_rate`                | **MISSING**           | n/a                                                                                         | Not captured                                                                                               | No `dividend_rate` data_type exists in MTDS. TradFi dividend data would require a separate FRED/vendor adapter. Not in UAC `DATA_TYPES_BY_ASSET_GROUP`. |
| `staking_yield` / LST APY      | **PRESENT (partial)** | LIDO, ROCKETPOOL, COINBASE-CBETH, JITO, MARINADE, KELPDAO, RENZO, PUFFER, ETHERFI, SOLBLAZE | `exchange_rate`, `apy` in `lst_rates`                                                                      | APY is annualized growth rate. Direct staking APY (native ETH/SOL validators) in `native_staking_rates` data_type.                                      |
| `borrow_rate` (protocol-level) | **PRESENT**           | AAVE_V3, COMPOUND_V3, SPARK, MORPHO, FLUID                                                  | `variable_borrow_rate`, `stable_borrow_rate`, `borrow_rate` fields in `lending_indices`                    | Multiple protocols; includes utilization_rate as denominator signal                                                                                     |

**Key gap**: `dividend_rate` is completely absent. No MTDS handler, no UAC data_type registration, no adapter. This is
needed for equity-vs-futures carry calculations in the PricingLedger `carry_staked_basis` archetype when TradFi equities
are involved.

---

## Greeks Coverage

| Greek                     | data_type                      | Field Name                                                                    | Source                                                                               | Status                                                                                                                                        |
| ------------------------- | ------------------------------ | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `IV` (implied_volatility) | `options_chain` (CeFi/Deribit) | `implied_volatility` in `CanonicalOptionsChainEntry`                          | Tardis Deribit OPTIONS.csv.gz — Deribit publishes mark IV, bid IV, ask IV per strike | **PRESENT in schema**; whether Tardis CSV columns map correctly depends on the raw CSV field names (not validated in code — pass-through CSV) |
| `delta`                   | `options_chain`                | `delta` in `CanonicalOptionsChainEntry`                                       | Deribit OPTIONS.csv.gz                                                               | **PRESENT in schema**                                                                                                                         |
| `gamma`                   | `options_chain`                | `gamma` in `CanonicalOptionsChainEntry`                                       | Deribit OPTIONS.csv.gz                                                               | **PRESENT in schema**                                                                                                                         |
| `theta`                   | `options_chain`                | `theta` in `CanonicalOptionsChainEntry`                                       | Deribit OPTIONS.csv.gz                                                               | **PRESENT in schema**                                                                                                                         |
| `vega`                    | `options_chain`                | `vega` in `CanonicalOptionsChainEntry`                                        | Deribit OPTIONS.csv.gz                                                               | **PRESENT in schema**                                                                                                                         |
| `rho`                     | `options_chain`                | **NOT in CanonicalOptionsChainEntry**                                         | —                                                                                    | **MISSING from schema**. `rho` is not a field in the canonical UAC options chain schema.                                                      |
| `mid` (computed)          | `book_snapshot_5`              | `mid_price` computed in `l2_book_state.py` as `(bids[0][0] + asks[0][0]) / 2` | Live streaming book state                                                            | **PRESENT** in live book state; not stored as a separate column in parquet — consumers must derive from `bid_price_0` and `ask_price_0`       |

**Critical observation on greeks**: The `CanonicalOptionsChainEntry` in UAC
(`unified_api_contracts/canonical/domain/derivatives/__init__.py`) declares `delta`, `gamma`, `theta`, `vega`,
`implied_volatility` as nullable float fields. These are schema-level declarations. The TradFi
`_TRADFI_OPTIONS_CHAIN_COLUMNS` SchemaSpec in `schema_spec.py` also declares `iv`, `delta`, `gamma`, `vega`, `theta`.

**However**: The Tardis bulk download path for `options_chain` is a CSV pass-through — the orchestrator reads the Tardis
`OPTIONS.csv.gz` file and writes it as-is. Whether the actual Deribit CSV columns map to
`implied_volatility`/`delta`/`gamma`/`theta`/`vega` depends on what Tardis names those columns. Deribit OPTIONS CSVs
include `mark_iv`, `bid_iv`, `ask_iv`, `delta`, `gamma`, `theta`, `vega` — so **greeks are present in the raw data**.
The orchestrator's pass-through means these columns land in the parquet as Tardis-native column names (e.g., `mark_iv`
not `implied_volatility`).

**Gap**: No normalization layer maps Tardis `mark_iv` → `implied_volatility`. The `CanonicalOptionsChainEntry` model
exists in UAC but is not enforced at write time for the `options_chain` CSV path (the orchestrator uses
`validate_data_type_for_venue()` advisory only).

**Where greeks computation would land for non-options instruments**: Greeks (IV, delta, gamma) for the
`carry_staked_basis` / `arbitrage_price_dispersion` archetypes are **not computed in MTDS**. If a PricingLedger requires
greeks for non-Deribit-options instruments (e.g., synthetic IV from spot volatility, delta-hedging ratios for DeFi
positions), that computation belongs in **features-service** (features-onchain track) or a new dedicated module, not in
MTDS. MTDS is a raw data capture layer.

---

## Emission Semantics Compliance

**Status: PARTIAL — `QG-allow: emission-policy-not-applicable` exemptions in DeFi handlers**

### Main CeFi/TradFi path (orchestrator.py):

- Uses `record_captured_from_counts()` via `ManifestWriter` for all per-shard writes — **COMPLIANT**
- Uses `record_empty(reason=<EmptyConfirmedReason>)` for gap cases — **COMPLIANT**
- `classify_venue_error()` called on fetch failures → `ADAPTER_FETCH_FAILED` event emitted — **COMPLIANT**
- Does NOT use `_resolve_policy_output_data_type` or `_publish_emission_check` (these are service-output emission
  semantics from a different SSOT — MTDS is a raw-tick writer, not a derived-output service)

### DeFi handler path (per-handler in `cli/handlers/`):

- `perp_funding_handler.py`: Uses `write_defi_rows()` + `recorder.record_captured()` / `record_empty()` — **COMPLIANT**
- `lending_indices_handler.py`: Uses `write_defi_rows()` + `DefiManifestRecorder` — **COMPLIANT**
- `lst_rates_handler.py`: Uses `recorder.record_captured()` with `# QG-allow: emission-policy-not-applicable` annotation
  — **PARTIAL** (QG exemption noted; policy rationale should be reviewed)
- `position_data_handler.py`, `flash_loan_events_handler.py`, `liquidation_events_handler.py`,
  `governance_events_handler.py`, `token_transfers_handler.py`, `native_staking_handler.py`: All use `record_captured()`
  with `# QG-allow: emission-policy-not-applicable` — **PARTIAL**

### Key compliance finding:

The `# QG-allow: emission-policy-not-applicable` annotation appears across 8+ DeFi handlers. This bypasses the
`_resolve_policy_output_data_type` + `_publish_emission_check` gate described in
`codex/02-data/service-output-emission-semantics.md`. This is a pre-existing exemption — these handlers write directly
via `write_defi_rows()` rather than through the canonical emission-policy wrapper. Whether this exemption is correct or
represents a gap requires operator-level confirmation.

### Service infrastructure:

- `ServiceBootstrap` present in `cli/main.py` — **COMPLIANT**
- `make_health_router` in `api/main.py` — **COMPLIANT**
- `ApiKeyReloader` in `cli/handlers/tick_data_handler.py` — **COMPLIANT**

---

## Gap to PricingLedger Target Fields

| PricingLedger Field            | data_type in MTDS                                                   | Field Name on Disk                                                                                      | Status      | Gap Detail                                                                                                                                                                                                          |
| ------------------------------ | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mid`                          | `book_snapshot_5` (derived), `derivative_ticker`                    | `mid_price` (derivative_ticker, nullable); `bid_price_0`+`ask_price_0` in book_snapshot_5               | **PARTIAL** | `mid_price` in `derivative_ticker` is nullable and may be NULL in most rows. For `book_snapshot_5`, mid must be derived by consumer as `(bid_price_0 + ask_price_0) / 2`. No canonical `mid` field in spot parquet. |
| `bid`                          | `book_snapshot_5`, `derivative_ticker`, `options_chain`             | `bid_price_0` (book_snapshot), `bid_price` (derivative_ticker), `bid` (options_chain TradFi SchemaSpec) | **PRESENT** | Present across all three relevant data_types. Naming inconsistent (`bid_price_0` vs `bid_price` vs `bid`).                                                                                                          |
| `ask`                          | `book_snapshot_5`, `derivative_ticker`, `options_chain`             | `ask_price_0`, `ask_price`, `ask`                                                                       | **PRESENT** | Same naming inconsistency as `bid`.                                                                                                                                                                                 |
| `IV` (implied_volatility)      | `options_chain` (Deribit bulk)                                      | Tardis CSV native name likely `mark_iv`; UAC schema declares `implied_volatility`                       | **PARTIAL** | Field is in raw Tardis CSV as `mark_iv` (Deribit convention). Not normalized to `implied_volatility` in the write path. Consumer must handle column alias.                                                          |
| `delta`                        | `options_chain`                                                     | Tardis CSV column name `delta` (Deribit publishes `delta` directly)                                     | **PRESENT** | Deribit OPTIONS.csv has `delta` column; likely lands as-is.                                                                                                                                                         |
| `gamma`                        | `options_chain`                                                     | Tardis CSV column `gamma`                                                                               | **PRESENT** | Same as delta.                                                                                                                                                                                                      |
| `theta`                        | `options_chain`                                                     | Tardis CSV column `theta`                                                                               | **PRESENT** | Same as delta.                                                                                                                                                                                                      |
| `vega`                         | `options_chain`                                                     | Tardis CSV column `vega`                                                                                | **PRESENT** | Same as delta.                                                                                                                                                                                                      |
| `rho`                          | —                                                                   | —                                                                                                       | **MISSING** | Not in `CanonicalOptionsChainEntry`, not in `_TRADFI_OPTIONS_CHAIN_COLUMNS`, not in any Tardis CSV field mapping. Would need UAC schema addition + adapter column inclusion.                                        |
| `funding_rate`                 | `derivative_ticker` (CeFi perp), `perp_funding` (DeFi/onchain perp) | `funding_rate`                                                                                          | **PRESENT** | Present in both CeFi and DeFi paths. Consistent column name. CeFi: 8h funding rate from Tardis. DeFi: `perp_funding_handler` writes per-funding-interval rows.                                                      |
| `dividend_rate`                | —                                                                   | —                                                                                                       | **MISSING** | No data_type, no handler, no UAC registration. Completely absent from MTDS.                                                                                                                                         |
| `lending_rate` / `supply_rate` | `lending_indices`                                                   | `liquidity_rate`, `supply_rate`                                                                         | **PRESENT** | Available from Aave, Compound, Spark via `lending_indices`. Naming: `liquidity_rate` (Aave Graph) or `supply_rate` (Compound). PricingLedger consumers need field alias.                                            |
| `borrow_rate`                  | `lending_indices`                                                   | `variable_borrow_rate`, `borrow_rate`                                                                   | **PRESENT** | Available from Aave, Compound, Spark. Two name variants — `variable_borrow_rate` (Aave) and `borrow_rate` (Compound).                                                                                               |

---

## Snapshot vs Streaming — Cadence Summary

| data_type                 | Mode                               | Cadence / Granularity                                                                           |
| ------------------------- | ---------------------------------- | ----------------------------------------------------------------------------------------------- |
| `book_snapshot_5`         | Batch (Tardis CSV)                 | Per-tick; Tardis publishes 15s-sampled book snapshots                                           |
| `derivative_ticker`       | Batch (Tardis CSV)                 | Per-tick 15s; funding_rate populated per 8h funding interval                                    |
| `options_chain`           | Batch (Tardis OPTIONS.csv.gz bulk) | Daily bulk download; 1 file per underlying per day covering all strikes/expiries                |
| `trades`                  | Batch (Tardis CSV)                 | Per-tick; each row is a trade event                                                             |
| `perp_funding`            | Batch (REST)                       | Per-funding-interval (8h Hyperliquid/Aster, 1h GMX); written as 1 daily parquet per protocol    |
| `lending_indices`         | Batch (The Graph)                  | Sub-daily snapshots; Aave subgraph has `reserveParamsHistoryItems` at ~hourly to 4h granularity |
| `lst_rates`               | Batch (RPC)                        | 1 snapshot per token per day at noon-UTC block                                                  |
| `oracle_prices`           | Batch (RPC/Graph)                  | Sub-daily; Aave oracle prices sampled at Graph query granularity                                |
| `ohlcv_1m/15m/24h`        | Batch (Databento/Yahoo)            | Bar-level; TradFi 1-minute bars from Databento                                                  |
| `dex_pools` / `dex_swaps` | Batch (on-chain)                   | Per-block or per-event; base 15m aggregated                                                     |

---

## Key Findings Summary

1. **Greeks are present in schema but not normalized**: `delta`, `gamma`, `theta`, `vega` land from Tardis Deribit CSVs
   as pass-through column names. IV is Tardis `mark_iv` not `implied_volatility`. No normalization layer exists at write
   time. PricingLedger consumers must handle column aliasing.

2. **`rho` is absent from the entire stack**: Not in `CanonicalOptionsChainEntry`, not in schema_spec, not computed
   anywhere. Requires UAC addition + adapter inclusion.

3. **`dividend_rate` is entirely missing**: No data_type, no handler, no vendor source. For TradFi equity-vs-futures
   carry, this is a required PricingLedger input. Unblocking requires operator decision on vendor source (FRED,
   Refinitiv, Bloomberg dividend calendars).

4. **`mid` requires consumer derivation**: No canonical `mid` field in spot/book_snapshot parquets. Must be derived from
   `(bid_price_0 + ask_price_0) / 2`. `derivative_ticker.mid_price` exists but is nullable and sparsely populated
   (Tardis does not always populate it).

5. **`perp_funding` and `lending_indices` cover carry family adequately** for DeFi archetypes: Aave supply/borrow rates,
   Hyperliquid/Aster/GMX funding rates all captured.

6. **Emission semantics: 8+ DeFi handlers use `# QG-allow: emission-policy-not-applicable`** — these bypass the
   `_resolve_policy_output_data_type` + `_publish_emission_check` gate. Pre-existing; requires operator ack to determine
   if this is intended architecture or a latent compliance gap.

7. **Where greeks computation lands for non-options instruments**: MTDS does not compute greeks. For the PricingLedger
   to have greeks on non-Deribit instruments (e.g., synthetic volatility for spot, delta for DeFi LP positions),
   computation must live in **features-service** downstream. This is outside MTDS scope.

---

## Audit Coverage Transparency

- **Exhaustive**: schema-level field mapping from UAC Pydantic models, SchemaSpec registry, and handler output
  dictionaries.
- **Exhaustive**: data_type × venue capability matrix from `VENUE_DATA_TYPE_CAPABILITIES` in
  `market_data_categories.py`.
- **Exhaustive**: handler-level output column names from direct code reading.
- **NOT sampled**: actual GCS parquet files — on-disk column presence vs schema declaration may diverge. A3/A4 manifest
  divergence audits cover this.
- **NOT verified**: whether Tardis `options_chain` CSV pass-through actually lands
  `delta`/`gamma`/`theta`/`vega`/`mark_iv` columns correctly without truncation or type mismatches. Requires a sample
  GCS parquet inspection.
