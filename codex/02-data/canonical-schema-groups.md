---
scope: [engineer, admin]
---

# Canonical Schema Groups

> **Canonical vs internal split (clarified 2026-05-12)** — per
> [`contracts-scope-and-layout.md`](contracts-scope-and-layout.md):
>
> - **Canonical types** (`CanonicalTrade`, `CanonicalOrderBook`, `CanonicalOHLCV`, `CanonicalLiquidation`,
>   `CanonicalOptionsChainEntry` — the "Group 1/2/…" tables below) live in `unified_api_contracts.canonical/domain/`.
>   These are the output of normalizers — the cross-venue normalised shape every consumer reads.
> - **Internal types** (service-internal pydantic models, dataclasses, TypedDicts used inside one repo as it
>   processes canonical inputs) live in `unified_api_contracts.internal/domain/<service>/`. These are NOT shared
>   cross-service; they exist so a service's `__init__` / `runner.py` / `cli/handlers/` agree on a single shape
>   without each module re-deriving it.
>
> The legacy phrasing "all internal canonical schemas are in `unified_api_contracts.internal`" was wrong — it
> conflated canonical (cross-service output of normalizers) with internal (per-service intermediate). Each table
> below is annotated `(canonical)` or `(internal)` at the top of the group.

**External raw → normalised mapping:** [unified-api-contracts](https://github.com/central-element/unified-api-contracts)
holds raw external schemas (`unified_api_contracts.external`) and normalised canonicals
(`unified_api_contracts.canonical`). An auto-generated **schema audit matrix**
(`unified-api-contracts/docs/SCHEMA_AUDIT_MATRIX.md`) lists what data is available per provider per schema type (✓ =
raw + normalizer, ~ = raw only, — = neither) and the canonical target. Regenerate via
`python scripts/generate_schema_audit_matrix.py`. Use for auditing usage, orphaned schemas, import errors, and missing
functionality in downstream consumers.

---

## Rule: Missing Field = Optional

**Never omit a field from the schema.** If a venue does not provide a field, use `Optional[...] = None`. Explicit
absence is part of the contract.

---

## 1. Market Data — Spot / TradFi

| Schema                       | Purpose                                                                 |
| ---------------------------- | ----------------------------------------------------------------------- |
| `CanonicalTrade`             | Trades, tick data; includes `is_liquidation`                            |
| `CanonicalOrderBook`         | L2 orderbook; bids/asks as `list[tuple[Decimal, Decimal, int \| None]]` |
| `CanonicalOHLCV`             | Candles; includes `source` enum (NATIVE_CANDLE \| COMPUTED_FROM_TICKS)  |
| `CanonicalLiquidation`       | Liquidation events                                                      |
| `CanonicalOptionsChainEntry` | Options chain; strike, put/call, delta, gamma, theta, vega, rho         |

---

## 2. Market Data — Derivatives

| Schema                      | Purpose                                                                                                                                                                                                                      |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CanonicalDerivativeTicker` | `funding_rate`, `predicted_funding_rate`, `open_interest`, `mark_price`, `index_price`, `borrow_long_rate`, `borrow_short_rate` (Deribit/Binance margin), Hyperliquid extras (`oracle_price`, `mid_price`, `day_ntl_volume`) |

---

## 3. Market Data — DeFi

| Schema                   | Purpose                                                                             |
| ------------------------ | ----------------------------------------------------------------------------------- |
| `CanonicalLiquidityPool` | V2/V3/V4 compatible; V3-specific fields (`tick_current`, `sqrt_price_x96`) Optional |
| `CanonicalLendingRate`   | Supply/borrow APY, utilization, Morpho extras                                       |
| `CanonicalStakingRate`   | Staking APY, rewards                                                                |
| `CanonicalOraclePrice`   | Oracle price feeds (e.g. Chainlink)                                                 |

---

## 4. Market Data — Fixed Income

| Schema                | Purpose                                 |
| --------------------- | --------------------------------------- |
| `CanonicalBondData`   | Bid/ask, YTM, duration, convexity, DV01 |
| `CanonicalYieldCurve` | FRED/ECB/IBKR yield curves              |

---

## 5. Reference Data

| Schema                     | Purpose                                                         |
| -------------------------- | --------------------------------------------------------------- |
| `InstrumentRecord`         | Single SSOT; replaces URDI + instruments-service custom schemas |
| `ExpiryCalendar`           | Venue expiry dates                                              |
| `UniverseSnapshot`         | As-of instruments + `venue_availability` dict                   |
| `IndexCompositionSnapshot` | Perp index basket constituents                                  |

---

## 6. Positions

| Schema                | Purpose                                  |
| --------------------- | ---------------------------------------- |
| `CeFiPosition`        | Spot, perps, futures positions           |
| `DeFiLPPosition`      | LP positions; `in_range` Optional for V3 |
| `DeFiLendingPosition` | Aave/Morpho/Compound positions           |
| `DeFiStakingPosition` | Staking positions                        |

---

## 7. Risk / Margin / Fees

| Schema            | Purpose                                                      |
| ----------------- | ------------------------------------------------------------ |
| `MarginState`     | Total collateral, debt, available margin, maintenance margin |
| `FeeSchedule`     | Maker/taker, funding, gas estimate                           |
| `GasCostEstimate` | DeFi gas estimate per action                                 |
| `ExposureSummary` | Portfolio-level exposure                                     |

---

## 8. Orders / Execution

| Schema              | Purpose                                                                  |
| ------------------- | ------------------------------------------------------------------------ |
| `CanonicalOrder`    | Order state                                                              |
| `CanonicalFill`     | Fill events                                                              |
| `OrderState`        | PENDING_NEW, NEW, PARTIALLY_FILLED, FILLED, CANCELLED, REJECTED, EXPIRED |
| `OrderTransition`   | State machine transitions                                                |
| `VenueCapabilities` | Per-venue supported order types, TIF, data types                         |

---

## 9. Regulatory

| Schema                    | Purpose                            |
| ------------------------- | ---------------------------------- |
| `MiFID2TransactionReport` | MiFID II transaction report fields |
| `EMIRTradeReport`         | EMIR trade report fields           |

---

## Module Location

All schemas live in `unified_api_contracts/internal/`:

- `market_data/` — trade, orderbook, ohlcv, derivative_ticker, liquidation, options_chain, defi, fixed_income
- `reference/` — instrument, expiry_calendar, universe_snapshot, index_composition
- `positions/` — cefi, defi_lp, defi_lending, defi_staking
- `risk/` — margin, fees
- `orders.py` — CanonicalOrder, CanonicalFill, OrderState, OrderTransition, VenueCapabilities
- `regulatory/` — mifid2, emir
