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
last_reviewed: 2026-09-09
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
| `OrderStatus`       | PENDING, OPEN, PARTIALLY_FILLED, FILLED, CANCELLED, REJECTED, EXPIRED    |
| `OrderTransition`   | State machine transitions                                                |
| `VenueCapabilities` | Per-venue supported order types, TIF, data types                         |

> **Naming corrected 2026-07-31:** this row read `OrderState` with members `PENDING_NEW` / `NEW`. The shipped UAC enum
> is `OrderStatus` (`canonical/domain/execution/base.py`) with `PENDING` / `OPEN`. See
> [`/codex/04-architecture/order-state-machine.md`](/codex/04-architecture/order-state-machine.md) for the open
> design-vs-shipped delta (that doc's `FAIL_OUTBOUND` / `RECONCILED` states are not in UAC).

---

## 9. Regulatory

| Schema                    | Purpose                            |
| ------------------------- | ---------------------------------- |
| `MiFID2TransactionReport` | MiFID II transaction report fields |
| `EMIRTradeReport`         | EMIR trade report fields           |

---

## Module Location

> **Refresh provenance (re-verified 2026-07-31):** regenerated from
> `ls unified-api-contracts/unified_api_contracts/internal/`. Per the canonical-vs-internal split banner at the top of
> this doc, "internal" types live in `unified_api_contracts/internal/`; canonical normaliser-output types
> (CanonicalTrade / CanonicalOrderBook / CanonicalOHLCV / CanonicalLiquidation / CanonicalOptionsChainEntry) live under
> `unified_api_contracts/canonical/` per [`contracts-scope-and-layout.md`](./contracts-scope-and-layout.md) §
> "Canonical type ownership".
>
> Drift corrected at this re-review: `ml.py` is now the `ml/` package (with a separate `ml_backup.py`); `events/` and
> `features/` are modules (`events.py`, `features.py`), not packages; `orders.py` and `regulatory/` do not exist at this
> level — the order/regulatory schema groups tabled above live under `canonical/domain/` and `domain/` respectively.
> Seventeen modules/packages that had never been listed are added below.

Internal-side top-level subpackages (`unified-api-contracts/unified_api_contracts/internal/`):

- `alerting/` — internal alert payload contracts
- `architecture_v2/` — strategy registry / family / archetype enums (StrategyFamily, StrategyArchetype,
  InstructionActionV2)
- `connectivity/` — venue + transport capability declarations
- `domain/` — domain-typed records (instruments, sports, prediction, etc.)
- `market_data/` — internal market-data shapes (pairs with `market_category.py`)
- `ml/` — ML training / inference internal contracts
- `positions/` — internal position-shape contracts (with `position_protocol.py` + `position_types.py`)
- `reference/` — internal reference-data shapes
- `registry/` — registry-side schemas
- `reporting/` — internal reporting contracts
- `schemas/` — additional internal schema definitions
- `testing/` — internal testing helpers
- `validation/` — internal validation contracts

Internal-side top-level modules:

- `agent_inference_cache.py` · `base.py` · `defi.py` · `deployment.py` · `env_canon.py` · `event_topics.py` ·
  `events.py` — internal event payloads · `execution.py` — `BatchExecutionMode` + execution-side internal types ·
  `features.py` — feature-row contracts · `index_utils.py` · `instrument_volatility.py` — internal vol surface payloads
- `inter_service_events.py` — cross-service event payloads · `manual_audit_paths.py` — audit-trail surfaces ·
  `market_category.py` — asset-group enums · `messaging.py` · `ml_backup.py` · `modes.py` ·
  `paper_execution_targets.py` · `pubsub.py` — Pub/Sub topic registry · `reconciliation.py` — reconciliation event
  contracts · `risk.py` — internal risk types
- `schema_definition.py` — `SchemaDefinition` / `ColumnSchema` (per `schema-governance.md`) · `sports.py` — internal
  sports contracts · `strategy_directives.py` · `strategy_pnl_stream.py` · `timeframes.py` · `unity_child_books.py` ·
  `unity_commercial_terms.py`

For canonical (normaliser-output) types, see `unified-api-contracts/unified_api_contracts/canonical/` — top-level
`gcs_paths.py`, `instrument_key.py`, `partition_paths.py`, `asset_group_registry.py`, `canonical_mappings.py`,
`coverage_exclusions.py`, `coverage_starts.py`, `quarantine.py`, plus `crosscutting/` and `domain/`
(`market/`, `sports/`, `derivatives/`, `execution/`, `features/`, `onchain/`, `position/`, `prediction/`,
`predictions/`, `reference/`, `strategy/`, `infrastructure/`).
