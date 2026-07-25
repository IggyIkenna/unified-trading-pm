---
doc_type: codex-ssot
title: Strategy Architecture v2 — Restriction Policy
summary:
  SSOT for the per-strategy-family restriction matrix driving (1) default catalogue lock-state
  (INVESTMENT_MANAGEMENT_RESERVED default; only STAT_ARB_PAIRS_FIXED×CEFI×spot|perp is PUBLIC), (2) the 6-axis
  questionnaire demo filtering, and (3) the per-persona allowed venues/instrument-types/data-types derivation.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: [strategy, catalogue, restriction, uac, ui, mvp]
related:
  [
    /codex/09-strategy/architecture-v2/block-list.md,
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/dashboard-services-grid.md,
    ../../14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md,
  ]
created: 2026-04-20
authoritative_for: [per-family strategy restriction matrix + catalogue lock-state + questionnaire demo filtering]
referenced_by:
  [
    /codex/09-strategy/README.md,
    /codex/09-strategy/architecture-v2/block-list.md,
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/dart-tab-structure.md,
    /codex/09-strategy/architecture-v2/dashboard-services-grid.md,
    /codex/09-strategy/architecture-v2/strategy-questionnaire-mapping.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Strategy Architecture v2 — Restriction Policy

> **Purpose:** Declare the per-strategy-family × restriction matrix that drives
>
> 1. default lock-state for catalogue cells (commercial IM reserve vs public catalogue),
> 2. questionnaire-based demo filtering for prospect audiences, and
> 3. the derivation surface (allowed venues, allowed instrument types, allowed data types) the UI uses to render the
>    catalogue under a given persona.
>
> **SSOTs consumed:**
>
> - Family metadata: `unified-trading-system-ui/lib/architecture-v2/families.ts`.
> - Coverage cells (auto-generated from UAC `archetype_capability_manifest.json`):
>   `unified-trading-system-ui/lib/architecture-v2/coverage.ts`.
> - Initial lock-state seed: `unified-trading-system-ui/lib/architecture-v2/initial-lock-state.ts`.
> - Questionnaire axes / enums: `unified-trading-system-ui/lib/questionnaire/types.ts`
>   - `unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py`
>     (`QuestionnaireResponse`).
> - Commercial SSOT: `unified-trading-pm/codex/14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md`.

## 1. Why restrictions exist

Odum runs a deliberately restrictive default on strategy visibility. Two axes drive the restrictions:

- **Commercial reserve (IM forward plan).** Most of the ~200 `SUPPORTED` / `PARTIAL` cells in the coverage matrix are
  reserved for Odum's Investment Management desk — they are either running for IM clients today, slated for an IM
  mandate in the forward plan, or represent capacity-bound capabilities we do not intend to open to the public
  catalogue. The default lock-state is therefore `INVESTMENT_MANAGEMENT_RESERVED`.
- **Audience slicing.** Unauthenticated marketing traffic, post-call prospects running questionnaire-driven demos, and
  authenticated IM / DART clients see different subsets of the same catalogue. The restriction policy is what the
  visibility-slicing layer (UAC `restriction_profiles`) applies on top of the raw `CoverageStatus`.

Hard blocks (`CoverageStatus = BLOCKED`) are separate — those are architectural / venue gaps, not commercial reserves,
and they are described in [`block-list.md`](block-list.md).

## 2. Per-family restriction axes

Derived from `ARCHETYPE_COVERAGE` cells in `coverage.ts` (union of all archetypes belonging to a family). Cells with
status `BLOCKED` or `NOT_APPLICABLE` are excluded from the allowed sets; `SUPPORTED` and `PARTIAL` cells contribute.
Venue IDs mirror `representativeVenueIds` on the coverage cells verbatim.

### 2.1 `ML_DIRECTIONAL` family

**Archetypes:** `ML_DIRECTIONAL_CONTINUOUS`, `ML_DIRECTIONAL_EVENT_SETTLED`.

| Axis                  | Allowed values                                                                                                                                                                                       |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Venue categories      | `CEFI`, `DEFI`, `TRADFI`, `SPORTS`, `PREDICTION`                                                                                                                                                     |
| Instrument types      | `spot`, `perp`, `dated_future`, `option`, `event_settled`                                                                                                                                            |
| Representative venues | `binance`, `okx`, `bybit`, `hyperliquid`, `deribit`, `uniswap_v3`, `balancer`, `drift`, `ibkr`, `cme`, `ice`, `cboe`, `unity`, `betfair_direct`, `smarkets_direct`, `matchbook_direct`, `polymarket` |
| Data types            | tick / candle / L2 order-book / event feed — driven by the signal variant (`price`, `delta_as_expression`, `odds`)                                                                                   |
| Blocked combos        | DEFI × option (BL-1), DEFI × dated_future (BL-2), PREDICTION × event_settled via Kalshi (BL-5)                                                                                                       |

### 2.2 `RULES_DIRECTIONAL` family

**Archetypes:** `RULES_DIRECTIONAL_CONTINUOUS`, `RULES_DIRECTIONAL_EVENT_SETTLED`.

| Axis                  | Allowed values                                                                                                                                               |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Venue categories      | `CEFI`, `DEFI`, `TRADFI`, `SPORTS`, `PREDICTION`                                                                                                             |
| Instrument types      | `spot`, `perp`, `dated_future`, `event_settled`                                                                                                              |
| Representative venues | `binance`, `okx`, `bybit`, `hyperliquid`, `deribit`, `uniswap_v3`, `drift`, `ibkr`, `cme`, `ice`, `unity`, `betfair_direct`, `smarkets_direct`, `polymarket` |
| Data types            | tick / candle + computed technicals (MACD, Donchian, VWAP, funding snapshot) — signal variant `price` or `funding_rate` or `odds`                            |
| Blocked combos        | CEFI × option and TRADFI × option (BL-4), TRADFI × dated_future requires roll service (BL-10)                                                                |

### 2.3 `CARRY_AND_YIELD` family

**Archetypes:** `CARRY_BASIS_DATED`, `CARRY_BASIS_PERP`, `CARRY_STAKED_BASIS`, `CARRY_RECURSIVE_STAKED`,
`YIELD_ROTATION_LENDING`, `YIELD_STAKING_SIMPLE`.

| Axis                  | Allowed values                                                                                                                                                                                                           |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Venue categories      | `CEFI`, `DEFI`, `TRADFI`                                                                                                                                                                                                 |
| Instrument types      | `perp`, `dated_future`, `option`, `staking`, `lending`                                                                                                                                                                   |
| Representative venues | `binance`, `okx`, `bybit`, `hyperliquid`, `deribit`, `coinbase`, `uniswap_v3`, `lido`, `rocketpool`, `etherfi`, `jito`, `marinade`, `aave_v3`, `compound_v3`, `euler`, `morpho`, `kamino`, `drift`, `ibkr`, `cme`, `ice` |
| Data types            | funding / basis / rate / staking-yield snapshots (signal variants `funding_rate`, `basis`, `rate_spread`, `staking_yield`)                                                                                               |
| Blocked combos        | CEFI × lending (BL-3, policy exclusion), DEFI × dated_future (BL-2), TRADFI × dated_future requires roll service (BL-10)                                                                                                 |

### 2.4 `ARBITRAGE_STRUCTURAL` family

**Archetypes:** `ARBITRAGE_PRICE_DISPERSION`, `LIQUIDATION_CAPTURE`.

| Axis                  | Allowed values                                                                                                                                                                                                              |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Venue categories      | `CEFI`, `DEFI`, `TRADFI`, `SPORTS`, `PREDICTION`                                                                                                                                                                            |
| Instrument types      | `spot`, `perp`, `dated_future`, `option`, `lending`, `lp`, `event_settled`                                                                                                                                                  |
| Representative venues | `binance`, `okx`, `bybit`, `hyperliquid`, `deribit`, `uniswap_v3`, `balancer`, `curve`, `sushiswap`, `drift`, `aave_v3`, `kamino`, `ibkr`, `cme`, `ice`, `cboe`, `unity`, `betfair_direct`, `smarkets_direct`, `polymarket` |
| Data types            | cross-venue price ticks, liquidation feed, IV surface (signal variants `price`, `iv_dispersion`, `liquidation_bonus`, `funding_rate`)                                                                                       |
| Blocked combos        | DEFI × option (BL-1)                                                                                                                                                                                                        |

### 2.5 `MARKET_MAKING` family

**Archetypes:** `MARKET_MAKING_CONTINUOUS`, `MARKET_MAKING_EVENT_SETTLED`.

| Axis                  | Allowed values                                                                                                                                                                                                                               |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Venue categories      | `CEFI`, `DEFI`, `TRADFI`, `SPORTS`, `PREDICTION`                                                                                                                                                                                             |
| Instrument types      | `spot`, `perp`, `option`, `lp`, `event_settled`                                                                                                                                                                                              |
| Representative venues | `binance`, `okx`, `bybit`, `hyperliquid`, `deribit`, `uniswap_v3`, `uniswap_v4`, `uniswap_v2`, `orca`, `raydium`, `curve`, `balancer`, `ibkr`, `cme`, `betfair_direct`, `smarkets_direct`, `matchbook_direct`, `betdaq_direct`, `polymarket` |
| Data types            | L2 order book, LP tick, odds ladder (signal variants `spread_capture`, `vol_metric`, `funding_rate`, `odds`)                                                                                                                                 |
| Blocked combos        | DEFI × perp (BL-7, protocol design), DEFI × option (BL-1), SPORTS × event_settled via Unity (BL-6)                                                                                                                                           |

### 2.6 `EVENT_DRIVEN` family

**Archetypes:** `EVENT_DRIVEN`.

| Axis                  | Allowed values                                                                                                                     |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Venue categories      | `CEFI`, `DEFI`, `TRADFI`, `SPORTS`, `PREDICTION`                                                                                   |
| Instrument types      | `spot`, `perp`, `dated_future`, `option`, `lending`, `staking`, `event_settled`                                                    |
| Representative venues | `binance`, `okx`, `bybit`, `hyperliquid`, `deribit`, `uniswap_v3`, `aave_v3`, `lido`, `ibkr`, `cme`, `cboe`, `unity`, `polymarket` |
| Data types            | economic calendar, governance calendar, news / slashing feed (signal variant `event_surprise`)                                     |
| Blocked combos        | TRADFI × dated_future requires roll service (BL-10)                                                                                |

### 2.7 `VOL_TRADING` family

**Archetypes:** `VOL_TRADING_OPTIONS`.

| Axis                  | Allowed values                                                                      |
| --------------------- | ----------------------------------------------------------------------------------- |
| Venue categories      | `CEFI`, `TRADFI`                                                                    |
| Instrument types      | `option`                                                                            |
| Representative venues | `deribit`, `okx`, `cboe` (via IBKR)                                                 |
| Data types            | full option surface, IV, skew, term (signal variants `vol_metric`, `iv_dispersion`) |
| Blocked combos        | DEFI × option (BL-1)                                                                |

### 2.8 `STAT_ARB_PAIRS` family

**Archetypes:** `STAT_ARB_PAIRS_FIXED`, `STAT_ARB_CROSS_SECTIONAL`.

| Axis                  | Allowed values                                                                                                                     |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Venue categories      | `CEFI`, `DEFI`, `TRADFI`                                                                                                           |
| Instrument types      | `spot`, `perp`, `dated_future`                                                                                                     |
| Representative venues | `binance`, `okx`, `bybit`, `hyperliquid`, `drift`, `uniswap_v3`, `ibkr`, `cme`, `ice`                                              |
| Data types            | paired underlying ticks + co-integration diagnostics (signal variants `zscore_reversion`, `momentum_ranking`)                      |
| Blocked combos        | DEFI × spot cross-sectional (BL-8), TRADFI × dated_future cross-sectional (BL-9), TRADFI × dated_future pairs roll service (BL-10) |

## 3. Lock-state policy (default vs explicit)

Lock-state values (from UAC `LockState`):

- `PUBLIC` — visible on unauthenticated marketing surfaces + post-call prospect demos.
- `INVESTMENT_MANAGEMENT_RESERVED` — visible only to Odum IM desk / admin audiences.
- `CLIENT_EXCLUSIVE` — reserved for a single client (`exclusive_client_id` required).
- `BUSINESS_UNIT_RESERVED` — reserved for an internal business unit (`reserving_business_unit_id` required).

Policy as of the **2026-04-20 snapshot** (SSOT: `initial-lock-state.ts` + `strategy-allocation-lock-matrix.md`):

### 3.1 Default rule

Every cell in the coverage matrix that is not `BLOCKED` / `NOT_APPLICABLE` defaults to `INVESTMENT_MANAGEMENT_RESERVED`
with `reservingBusinessUnitId = "odum-im"`.

### 3.2 PUBLIC cells (explicit allowlist)

Only the `STAT_ARB_PAIRS_FIXED` cells under `CEFI × spot|perp` are `PUBLIC`:

- `STAT_ARB_PAIRS_FIXED / CEFI / spot`
- `STAT_ARB_PAIRS_FIXED / CEFI / perp`

Rationale: existing live IM mandate with 1-yr+ track record, no exclusivity signed with any client, offerable to DART
prospects as a public-catalogue capability.

### 3.3 IM-live cells (explicitly documented, same default lock-state)

The following `INVESTMENT_MANAGEMENT_RESERVED` cells carry non-default `StrategyMaturity` values in the initial seed
because they are already running / imminently going live (2026-04-20 snapshot):

| Cell                                                    | Maturity                  | Reason                                                 |
| ------------------------------------------------------- | ------------------------- | ------------------------------------------------------ |
| `ML_DIRECTIONAL_CONTINUOUS / CEFI / spot`               | `LIVE_ALLOCATED`          | BTC ML IM — 10 clients from Jun 2026                   |
| `ML_DIRECTIONAL_CONTINUOUS / CEFI / perp`               | `LIVE_ALLOCATED`          | BTC ML IM — 10 clients from Jun 2026                   |
| `ML_DIRECTIONAL_CONTINUOUS / TRADFI / dated_future`     | `PAPER_TRADING_VALIDATED` | CME S&P co-invest — Sept 2026 go-live                  |
| `VOL_TRADING_OPTIONS / TRADFI / option`                 | `PAPER_TRADING_VALIDATED` | India Options delta-trading — Oct 2026 go-live         |
| `ML_DIRECTIONAL_EVENT_SETTLED / SPORTS / event_settled` | `LIVE_ALLOCATED`          | Sports ML — 2 IM clients from Jun 2026, capacity-bound |

All other cells fall back to `BACKTESTED` maturity under the default `INVESTMENT_MANAGEMENT_RESERVED` lock-state.

### 3.4 `BTC Fund of Funds`

External to the v2 catalogue — not declared in the archetype enum, not seeded. Managed separately.

## 4. Questionnaire-driven filtering

The public `/questionnaire` page (`app/(public)/questionnaire/page.tsx`) collects a 6-axis `QuestionnaireResponse`
(SSOT: `unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py`). The UAC overlay
logic applies the response on top of the family restriction axes in § 2 and the lock-state policy in § 3 to produce the
demo's visible cell set.

### 4.1 The 6 axes

| Axis               | Type / values                                                                                                                             |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `categories`       | subset of `{CeFi, DeFi, TradFi, Sports, Prediction}` (mixed case in questionnaire; maps to `VenueCategoryV2` upper-case).                 |
| `instrument_types` | subset of `{spot, perp, dated_future, option, lending, staking, lp, event_settled}` (matches `InstrumentTypeV2`).                         |
| `venue_scope`      | `"all"` or `string[]` of explicit venue IDs (CSV input; matched against `representativeVenueIds`).                                        |
| `strategy_style`   | subset of `{ml_directional, rules_directional, stat_arb, arbitrage, carry, event_driven, market_making, vol_trading}` (maps to families). |
| `service_family`   | one of `{IM, DART, RegUmbrella, combo}`.                                                                                                  |
| `fund_structure`   | one of `{SMA, Pooled, NA}`.                                                                                                               |

### 4.2 "User answers X → visible cells Y" mini-table

The table below describes the **filter composition** applied to the default PUBLIC + `INVESTMENT_MANAGEMENT_RESERVED`
sets when a prospect completes the questionnaire. Rules compose with AND across axes; within an axis, `any` means "do
not filter on this axis".

| User answer                                          | Cell filter applied                                                                                                                 |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `categories = ["CeFi"]`                              | `cell.category == CEFI`                                                                                                             |
| `categories = ["CeFi", "DeFi"]`                      | `cell.category in {CEFI, DEFI}`                                                                                                     |
| `categories = []`                                    | no category filter (base profile fallback)                                                                                          |
| `instrument_types = ["spot", "perp"]`                | `cell.instrumentType in {spot, perp}`                                                                                               |
| `venue_scope = "all"`                                | no venue filter                                                                                                                     |
| `venue_scope = ["binance", "cme"]`                   | `any(v in cell.representativeVenueIds for v in user_scope)`                                                                         |
| `strategy_style = ["stat_arb"]`                      | `familyOf(cell.archetype) == STAT_ARB_PAIRS`                                                                                        |
| `strategy_style = ["ml_directional", "vol_trading"]` | `familyOf(cell.archetype) in {ML_DIRECTIONAL, VOL_TRADING}`                                                                         |
| `service_family = "DART"`                            | restrict to `lock_state == PUBLIC` cells only (no IM-reserved content visible)                                                      |
| `service_family = "IM"`                              | keep both PUBLIC and `INVESTMENT_MANAGEMENT_RESERVED` cells, but flag the IM-reserved subset as "talk to us" in the UI              |
| `service_family = "RegUmbrella"`                     | restrict to cells with `RegUmbrellaCompatible` flag (Reg Umbrella matrix is a codex gate, not a catalogue axis) — treated as `DART` |
| `service_family = "combo"`                           | union of DART + IM filters                                                                                                          |
| `fund_structure = "SMA"`                             | no cell filter (SMA is an execution-path axis, not a catalogue axis) — used downstream for pricing copy                             |
| `fund_structure = "Pooled"`                          | same — pooled fund mechanics are an onboarding axis, not a catalogue filter                                                         |

### 4.3 Strategy-style → family mapping

| Questionnaire `strategy_style` | `StrategyFamily`       |
| ------------------------------ | ---------------------- |
| `ml_directional`               | `ML_DIRECTIONAL`       |
| `rules_directional`            | `RULES_DIRECTIONAL`    |
| `stat_arb`                     | `STAT_ARB_PAIRS`       |
| `arbitrage`                    | `ARBITRAGE_STRUCTURAL` |
| `carry`                        | `CARRY_AND_YIELD`      |
| `event_driven`                 | `EVENT_DRIVEN`         |
| `market_making`                | `MARKET_MAKING`        |
| `vol_trading`                  | `VOL_TRADING`          |

### 4.4 Base profile (vague or empty response)

If every axis is empty (the user submits without selecting anything), the overlay returns the base profile — i.e. the
unfiltered PUBLIC-only slice. This is the same surface an unauthenticated marketing visitor sees. No IM-reserved content
is exposed without an explicit `service_family = IM` answer.

## 5. Interaction with hard blocks

Hard-BLOCKED combos (see [`block-list.md`](block-list.md)) are always hidden regardless of questionnaire answers or
audience. The restriction policy in this file layers on top of the BLOCKED filter — it cannot re-enable a BLOCKED cell.

If a prospect's questionnaire answer would otherwise expose a BLOCKED combo (e.g. "DeFi + option" under vol_trading),
the UI should surface the BL entry's rationale + remediation inline so the prospect understands why that combo is not
available.

## See also

- [`block-list.md`](block-list.md) — hard-blocked combos + remediation.
- [`category-instrument-coverage.md`](category-instrument-coverage.md) — full coverage matrix.
- [`../../14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md`](../../14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md)
  — commercial SSOT for the lock-state policy.
- `unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py` — UAC overlay logic.
- `unified-trading-system-ui/lib/architecture-v2/initial-lock-state.ts` — runtime seed of the lock-state registry.
