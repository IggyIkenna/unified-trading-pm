---
doc_type: codex-ssot
title: Canonical Schema Groups
summary:
  Catalogue of the UAC canonical normaliser-output schema groups (CanonicalTrade / OrderBook / OHLCV / Liquidation /
  OptionsChainEntry, derivatives, DeFi, fixed-income, positions, risk, orders, regulatory) and the canonical-vs-internal
  split, with the missing-field=Optional rule.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [uac, canonicalisation, catalogue, instruments, data-pipeline]
related: [/codex/02-data/contracts-scope-and-layout.md, /codex/02-data/data-catalogue-schema.md]
created: 2026-03-27
authoritative_for: [canonical schema group catalogue (Canonical* field tables)]
referenced_by:
  [
    /codex/02-data/contracts-scope-and-layout.md,
    /codex/02-data/data-catalogue-schema.md,
    /codex/06-coding-standards/documentation-standards.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Canonical Schema Groups

> **Canonical vs internal split (clarified 2026-05-12)** — per
> [`contracts-scope-and-layout.md`](contracts-scope-and-layout.md):
>
> - **Canonical types** (`CanonicalTrade`, `CanonicalOrderBook`, `CanonicalOHLCV`, `CanonicalLiquidation`,
>   `CanonicalOptionsChainEntry` — the "Group 1/2/…" tables below) live in `unified_api_contracts.canonical/domain/`.
>   These are the output of normalizers — the cross-venue normalised shape every consumer reads.
> - **Internal types** (service-internal pydantic models, dataclasses, TypedDicts used inside one repo as it processes
>   canonical inputs) live in `unified_api_contracts.internal/domain/<service>/`. These are NOT shared cross-service;
>   they exist so a service's `__init__` / `runner.py` / `cli/handlers/` agree on a single shape without each module
>   re-deriving it.
>
> The legacy phrasing "all internal canonical schemas are in `unified_api_contracts.internal`" was wrong — it conflated
> canonical (cross-service output of normalizers) with internal (per-service intermediate). Each table below is
> annotated `(canonical)` or `(internal)` at the top of the group.

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

| Schema                     | Purpose                                                                                             |
| -------------------------- | --------------------------------------------------------------------------------------------------- |
| `InstrumentRecord`         | Single SSOT; replaces retired unified-reference-data-interface + instruments-service custom schemas |
| `ExpiryCalendar`           | Venue expiry dates                                                                                  |
| `UniverseSnapshot`         | As-of instruments + `venue_availability` dict                                                       |
| `IndexCompositionSnapshot` | Perp index basket constituents                                                                      |

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

> **Refresh provenance (2026-05-12 codex audit D-10):** regenerated from
> `ls unified-api-contracts/unified_api_contracts/internal/`. Earlier table listed `positions/` / `risk/` / `orders.py`
> / `regulatory/` at the top level; actual top-level subpackages + modules below. Per the canonical-vs-internal split
> banner at the top of this doc, "internal" types live in `unified_api_contracts/internal/`; canonical normaliser-output
> types (CanonicalTrade / CanonicalOrderBook / CanonicalOHLCV / CanonicalLiquidation / CanonicalOptionsChainEntry) live
> under `unified_api_contracts/canonical/` per [`contracts-scope-and-layout.md`](./contracts-scope-and-layout.md) §
> "Canonical type ownership".

Internal-side top-level subpackages + modules (`unified-api-contracts/unified_api_contracts/internal/`):

- `architecture_v2/` — strategy registry / family / archetype enums (StrategyFamily, StrategyArchetype,
  InstructionActionV2)
- `connectivity/` — venue + transport capability declarations
- `domain/` — domain-typed records (instruments, sports, prediction, etc.)
- `events/` — internal event payloads
- `execution.py` — `BatchExecutionMode` + execution-side internal types
- `features/` — feature-row contracts
- `inter_service_events.py` — cross-service event payloads
- `instrument_volatility.py` — internal vol surface payloads
- `manual_audit_paths.py` — audit-trail surfaces
- `market_category.py` + `market_data/` — internal market-data + asset-group enums
- `ml.py` — ML training / inference internal contracts
- `position_protocol.py` + `position_types.py` + `positions/` — internal position-shape contracts
- `pubsub.py` — Pub/Sub topic registry
- `reconciliation.py` — reconciliation event contracts
- `reference/` — internal reference-data shapes
- `registry/` — registry-side schemas
- `reporting/` — internal reporting contracts
- `risk.py` — internal risk types
- `schema_definition.py` — `SchemaDefinition` / `ColumnSchema` (per `schema-governance.md`)
- `schemas/` — additional internal schema definitions
- `sports.py` — internal sports contracts
- `testing/` — internal testing helpers

For canonical (normaliser-output) types, see `unified-api-contracts/unified_api_contracts/canonical/` —
`domain/market_data/`, `domain/sports/`, `crosscutting/` etc.
