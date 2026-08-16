---
doc_type: codex-ssot
title: "Axis: Expression"
summary:
  Expression axis catalog — how a strategy view is translated into traded instruments (independent of signal source and
  edge method). Covers cash-equivalent (SPOT/PERP/DATED_FUTURE/MARGIN), options structures, DeFi (DEX_SWAP/LP/LEND/
  STAKE/loops), sports/prediction bets, synthetics; selection drivers, expression×family compatibility, and multi-leg
  ATOMIC/LEADER_HEDGE execution-mode declaration.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [strategy, expression, options, defi, execution, sports]
related:
  [
    /codex/09-strategy/architecture-v2/axes/venue-eligibility.md,
    /codex/09-strategy/architecture-v2/axes/staking-methods.md,
    /codex/09-strategy/architecture-v2/axes/signal-sources.md,
    ../cross-cutting/execution-policies.md,
    ../cross-cutting/trade-expression.md,
  ]
created: 2026-04-17
authoritative_for: [expression axis (view-to-instrument translation catalog)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-continuous.md,
    /codex/09-strategy/architecture-v2/axes/edge-methods.md,
    /codex/09-strategy/architecture-v2/axes/signal-sources.md,
    /codex/09-strategy/architecture-v2/cross-cutting/trade-expression.md,
    /codex/09-strategy/architecture-v2/families/ml-directional.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Axis: Expression

> **What it is:** How the strategy's view is _translated into instruments_ that actually get traded. A single
> directional or vol view can be expressed as spot, perp, dated future, option, basket, LP position, or synthetic — each
> with different capital, margin, funding, and greek implications.
>
> **How it relates:** Edge method decides "should we act?"; expression decides "in which instrument(s)?" Expression is
> independent of both the signal source and the edge method — a value-edge ML directional view can be expressed as spot
> _or_ perp _or_ ATM call _or_ 25-delta call.

## Catalog of expressions

### Cash-equivalent directional

| Expression     | Venues                                 | Notes                                        |
| -------------- | -------------------------------------- | -------------------------------------------- |
| `SPOT`         | CEX spot, DEX swap                     | Simplest; consumes full notional; no funding |
| `PERP`         | Binance, OKX, Bybit, Hyperliquid, dYdX | Leveraged; funding rate P&L; no expiry       |
| `DATED_FUTURE` | CME, Deribit quarterly                 | Settles at expiry; basis ≠ funding           |
| `MARGIN`       | IBKR, select CEXes                     | Leveraged spot on borrow                     |

### Options

| Expression                   | Config                                | Notes                                 |
| ---------------------------- | ------------------------------------- | ------------------------------------- |
| `ATM_CALL` / `ATM_PUT`       | tenor, closest-to-ATM                 | Pure directional with convexity       |
| `NDD_CALL` / `NDD_PUT`       | delta target (e.g., 25d, 10d)         | Delta-targeted expression             |
| `OTM_CALL` / `OTM_PUT`       | strike as % of spot                   | Lottery-style or crash-hedge          |
| `STRADDLE`                   | strike=ATM, call+put                  | Pure vol expression                   |
| `STRANGLE`                   | call_delta, put_delta                 | Cheaper vol; wider                    |
| `CALL_SPREAD` / `PUT_SPREAD` | long_delta, short_delta               | Capped directional with reduced theta |
| `CALENDAR`                   | front_tenor, back_tenor, strike       | Term-structure bet                    |
| `BUTTERFLY`                  | three strikes                         | Pinning / range bet                   |
| `RISK_REVERSAL`              | long call + short put (or vice versa) | Skew / synthetic-delta                |
| `IRON_CONDOR`                | four strikes                          | Range-bound vol sell                  |

### DeFi / on-chain specific

| Expression               | Venues                                                        | Notes                                               |
| ------------------------ | ------------------------------------------------------------- | --------------------------------------------------- |
| `DEX_SWAP`               | Uniswap V2/V3/V4, Curve, Balancer, PancakeSwap, Orca, Raydium | Spot-equivalent on-chain                            |
| `LP_PASSIVE`             | Uniswap V2/Curve/Balancer stable/Aerodrome stable             | Full-range LP                                       |
| `LP_ACTIVE`              | Uniswap V3, Orca CLMM, Joe V2, V4 hooks                       | Concentrated range LP                               |
| `LEND`                   | Aave, Compound, Morpho, Spark, Kamino                         | Principal + variable APY                            |
| `BORROW`                 | same                                                          | Costs variable APY; requires collateral             |
| `STAKE_LIQUID`           | Lido, Rocket Pool, Jito, Marinade                             | Receives liquid staking token (stETH, jitoSOL etc.) |
| `STAKE_NATIVE`           | native chain validators                                       | Locked; no LST                                      |
| `LEVERAGED_LENDING_LOOP` | Aave + Pendle/LST                                             | Multi-leg recursive position                        |

### Sports / prediction

| Expression                     | Venues                                                    | Notes                                   |
| ------------------------------ | --------------------------------------------------------- | --------------------------------------- |
| `BET_BACK`                     | Smarkets, Betfair (back), VX, SharpBet, Unity child books | Bet on outcome                          |
| `BET_LAY`                      | Betfair only                                              | Bet against outcome (exchange mechanic) |
| `BET_BACK_ARB_SET`             | 2+ bookmakers across outcomes                             | Arb bet set (multi-outcome lock)        |
| `BET_CLOB_YES` / `BET_CLOB_NO` | Polymarket, Kalshi                                        | Binary CLOB share                       |

### Synthetic / structured

| Expression                         | Composition                          | Use                                     |
| ---------------------------------- | ------------------------------------ | --------------------------------------- |
| `SYNTHETIC_PERP_FROM_OPTIONS`      | long call + short put at same strike | Replicate perp from options             |
| `SYNTHETIC_SPOT_FROM_PERP_FUNDING` | short perp + hedge = -funding rate   | Funding carry                           |
| `BASKET`                           | N legs with weights                  | Stat arb cross-sectional, sector trades |
| `DELTA_HEDGED_OPTION`              | option + delta-hedge in spot/perp    | Vol trading core                        |
| `PAIRED_SPREAD`                    | leg_A + leg_B with hedge ratio       | Stat arb pairs                          |

### Auto (deferred)

`AUTO` — strategy doesn't pick; execution-service picks optimal expression given current conditions. Used when multiple
expressions are equivalent and execution can optimize on liquidity/cost (rare; most strategies pin expression
explicitly).

## Expression selection drivers

A given view is expressed based on:

1. **Capital efficiency** — perp uses less capital than spot for the same directional exposure
2. **Funding/borrow cost** — spot may win over perp in high-funding regimes
3. **Convexity needs** — options give convexity that linear instruments cannot
4. **Share class match** — if share class is USDT, prefer USDT-margined perps to avoid FX basis
5. **Venue availability** — not every venue offers every expression
6. **Regulatory** — US accounts can't trade certain perps; retail options access varies
7. **Expiry alignment** — event-driven strategies pick tenors spanning the event
8. **Greek profile** — vol trading picks expression by vega/gamma footprint

## Expression × family compatibility

| Family            | Common expressions                                                                           |
| ----------------- | -------------------------------------------------------------------------------------------- |
| ML Directional    | SPOT, PERP, ATM_CALL, NDD_CALL, CALL_SPREAD                                                  |
| Rules Directional | SPOT, PERP, CALL_SPREAD                                                                      |
| Carry & Yield     | SPOT+PERP (basis), STAKE_LIQUID+PERP (staked basis), LEND, BORROW, LEVERAGED_LENDING_LOOP    |
| Arbitrage         | SPOT on two venues (price disp), DATED_FUTURE+SPOT (basis), STRADDLE triangulation (IV disp) |
| Market Making     | SPOT quotes, PERP quotes, LP_PASSIVE, LP_ACTIVE, BET_BACK/BET_LAY                            |
| Event-Driven      | SPOT, PERP, STRADDLE, CALL_SPREAD (pre-event gamma)                                          |
| Vol Trading       | STRADDLE, STRANGLE, CALENDAR, BUTTERFLY, RISK_REVERSAL, DELTA_HEDGED_OPTION                  |
| Stat Arb          | SPOT+SPOT (fixed pair), BASKET (cross-sectional), PERP+PERP                                  |

## Multi-leg expressions and ATOMIC execution

Any multi-leg expression (straddle, calendar, basis, paired spread, arb set, basket) declares whether legs must be
ATOMIC, LEADER_HEDGE, or sequential. See
[../cross-cutting/execution-policies.md](../cross-cutting/execution-policies.md).

```yaml
expression: STRADDLE
legs:
  - { side: BUY, instrument: "DERIBIT:OPT:BTC-25APR25-60000-C", weight: 1 }
  - { side: BUY, instrument: "DERIBIT:OPT:BTC-25APR25-60000-P", weight: 1 }
execution_mode: ATOMIC # same venue → native multi-leg order
```

```yaml
expression: BASIS_DATED
legs:
  - { side: BUY, instrument: "BINANCE:SPOT:BTC/USDT", weight: 1 }
  - { side: SELL, instrument: "CME:FUT:BTC-MAR25", weight: 1 }
execution_mode: LEADER_HEDGE # cross-venue → sequence with hedge alert
leader_leg: 0
hedge_deadline_ms: 5000
```

## Expression greeks + risk

When expression has greeks (options, LP V3, structured), the strategy config declares:

- **Target portfolio greeks** (delta, gamma, vega, theta, rho) after the trade
- **Delta-hedging policy** — continuous re-hedge threshold, hedge venue, hedge expression (usually perp)
- **Vega/gamma decay schedule** — reduce position as expiry approaches
- **Greek limits** — per [../cross-cutting/risk-gates.md](../cross-cutting/risk-gates.md)

## Reference price for options

Strategies don't compute greeks locally — they reference a pricing engine (Deribit's pass-through initially, our fitted
surface later). Execution receives a reference price and market-makes around it per
[../cross-cutting/execution-policies.md](../cross-cutting/execution-policies.md).

## Not in this axis

- **Which venue hosts the expression** — [venue-eligibility.md](venue-eligibility.md)
- **How the expression is sized** — [staking-methods.md](staking-methods.md)
- **Delta-hedge mechanics** — execution-policy for the delta-hedge strategy leg
- **IV surface fitting** — [signal-sources.md](signal-sources.md) (vol-metrics)
- **How the synthetic is decomposed into fills** — execution-service

## Cross-references

- Staking: [staking-methods.md](staking-methods.md)
- Venue eligibility: [venue-eligibility.md](venue-eligibility.md)
- Execution policies: [../cross-cutting/execution-policies.md](../cross-cutting/execution-policies.md)
- Trade expression cross-cutting (cross-family synthetics):
  [../cross-cutting/trade-expression.md](../cross-cutting/trade-expression.md)
