---
doc_type: codex-ssot
title: "Cross-Cutting: Trade Expression"
summary:
  "Runtime machinery that composes/decomposes a view into instrument legs: ATOMIC bundle, LEADER_HEDGE, continuous
  delta-hedge attachment, paced basket, on-chain protocol composite, and synthetic decomposition — shared handlers
  across every strategy family. Partial atomic fills are never permitted; decomposition lives in execution
  `expression_library`."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [strategy, execution, expression, defi, options]
related:
  [
    ../axes/expression.md,
    /codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md,
    /codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md,
    ../archetypes/carry-recursive-staked.md,
  ]
created: 2026-04-17
authoritative_for:
  [
    runtime trade-expression composition machinery (ATOMIC/LEADER_HEDGE/delta-hedge/basket/protocol-composite +
    synthetic decomposition),
  ]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/cross-cutting/strategy-instruction-bus.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/axes/expression.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Cross-Cutting: Trade Expression

> **What it is:** The per-instruction mechanics of translating a directional/vol/carry view into a specific set of
> instrument legs. The [expression axis](../axes/expression.md) catalogs _what expressions exist_; this cross-cutting
> doc covers _how expressions are composed and decomposed at runtime_ — particularly synthetic composites, multi-leg
> atomicity, delta-hedge attachment, and cross-family re-use.
>
> **Overlap note:** The expression _axis_ is a per-strategy config choice (strategies pin their expression type). This
> cross-cutting concern is about the _runtime machinery_ that turns a chosen expression into fills — shared across all
> strategies regardless of family.

## When expression is a cross-cutting concern

Single-leg expressions (spot, perp, single-strike call) don't need composition machinery — the StrategyInstruction
targets one instrument. The cross-cutting concern kicks in for:

1. **Synthetics** — the view is "long perp" but expressed as `long call + short put`
2. **Multi-leg** — the view is "long vol" → `straddle = long ATM call + long ATM put`
3. **Delta-hedged** — the view is vol → `option + delta hedge on underlying`
4. **Paired / basket** — stat arb pairs, cross-sectional baskets
5. **Cross-venue assemblies** — basis (spot at A + perp at B), leader-hedge
6. **Protocol composites** — recursive staking (stake + borrow + swap + re-stake), leveraged lending loops

All of these need runtime orchestration that the basic TRADE-per-leg primitive doesn't provide on its own.

## Composition primitives

### ATOMIC bundle

Multiple legs bound into a single atomic instruction:

```yaml
action: ATOMIC
client_id: client_A_fund
strategy_instance_id: VOL_TRADING_OPTIONS@deribit-btc-vol-usdt-prod
legs:
  - { side: BUY, instrument: "DERIBIT:OPT:BTC-25APR25-60000-C", size_units: 10 }
  - { side: BUY, instrument: "DERIBIT:OPT:BTC-25APR25-60000-P", size_units: 10 }
execution_mode: ATOMIC # native multi-leg where supported
venue_hint: DERIBIT
max_price_each: [<call_max>, <put_max>]
```

Execution-service resolves to venue's native multi-leg order (Deribit multi-leg, Binance OCO, IBKR combo, etc.) when
supported.

### LEADER_HEDGE bundle

Cross-venue legs where atomic isn't supported; one leg leads, other is hedge with deadline + compensation policy.

```yaml
action: ATOMIC
execution_mode: LEADER_HEDGE
leader_leg: 0
hedge_deadline_ms: 5000
compensation_policy: CLOSE_LEADER_IF_HEDGE_FAILS # or HOLD_LEG_AND_ALERT
legs:
  - { side: BUY, instrument: "BINANCE:SPOT:BTC/USDT", size_units: 1 }
  - { side: SELL, instrument: "HYPERLIQUID:PERP:BTC", size_units: 1 }
```

See [../families/arbitrage-structural.md](../families/arbitrage-structural.md) for leader-hedge mechanics.

### Delta-hedge attachment

For any option-bearing expression, the strategy can declare a continuous delta-hedge rider:

```yaml
expression: STRADDLE
delta_hedge:
  hedge_venue: BINANCE
  hedge_instrument: "BINANCE:PERP:BTC-PERP"
  rebalance_threshold_delta: 0.05 # re-hedge when |delta| > 5% of notional
  hedge_algo: MARKET_SWEEP # or LIMIT_BEST
```

Execution-service spawns a continuous delta-hedge process bound to the option position's lifetime. The delta-hedge emits
its own TRADE instructions tagged to the parent option strategy_instance_id.

### Basket composition

For stat arb cross-sectional and basket trades:

```yaml
action: ATOMIC
execution_mode: SEQUENCED_WITH_PACING
pacing: TWAP
window_seconds: 600
legs:
  - { side: BUY,  instrument: "IBKR:EQUITY:GOOG", weight: 0.02 }
  - { side: BUY,  instrument: "IBKR:EQUITY:META", weight: 0.02 }
  - { side: SELL, instrument: "IBKR:EQUITY:AAPL", weight: -0.02 }
  ... (hundreds of legs)
balance_mode: MAINTAIN_NEUTRAL_DELTA_THROUGH_EXECUTION
```

Execution-service paces entries to preserve dollar-neutral / factor-neutral throughout the slice, not just at the end.

### Protocol composite

Recursive staking / leveraged lending loops:

```yaml
action: ATOMIC
execution_mode: ATOMIC_ON_CHAIN # single tx with multiple protocol calls
chain: ETHEREUM
legs:
  - { action: STAKE, protocol: LIDO, asset: ETH, amount: 100 }
  - { action: LEND, protocol: AAVE, asset: wstETH, amount: 100 }
  - { action: BORROW, protocol: AAVE, asset: ETH, amount: 60 }
  - { action: STAKE, protocol: LIDO, asset: ETH, amount: 60 }
  - { action: LEND, protocol: AAVE, asset: wstETH, amount: 60 }
```

Execution-service composes into a single chain transaction via multicall / router contract. All-or-nothing. See
[../archetypes/carry-recursive-staked.md](../archetypes/carry-recursive-staked.md).

## Synthetic decomposition

A strategy can express a view in a "high-level" primitive (SYNTHETIC_PERP_FROM_OPTIONS,
SYNTHETIC_SPOT_FROM_PERP_FUNDING) and execution-service decomposes into the leg set:

```
SYNTHETIC_PERP_FROM_OPTIONS
  ↓
  long call (strike K) + short put (strike K), same expiry
```

Benefits: strategy code is agnostic to decomposition; execution can swap the decomposition (use a different strike set,
use a box spread, etc.) given cost considerations. Decomposition logic lives in `execution-service/expression_library/`.

## Expression × execution policy interaction

Each expression has associated execution policies per action type:

```yaml
expression: STRADDLE
execution_policy_refs:
  multi_leg: deribit-atomic-options-v2
  delta_hedge: cefi-perp-small-size-v3
  close: deribit-close-options-v1
```

## Fail semantics

- **Partial atomic fills not permitted** — if ATOMIC can't fully execute, all legs cancel
- **Leader-hedge leader filled but hedge failed** → per `compensation_policy`
- **Delta-hedge failure during option hold** → alert; strategy may continue with stale delta or force close
- **Basket partial fill acceptable** — with pacing policy tracking executed-vs-target per leg

## Cross-family expression sharing

The same expression primitives are used across families:

| Expression                  | Used by                                                                       |
| --------------------------- | ----------------------------------------------------------------------------- |
| STRADDLE                    | Vol Trading, Event-Driven (pre-event gamma)                                   |
| SYNTHETIC_PERP_FROM_OPTIONS | Carry & Yield (perp synth), ML Directional (when option market better priced) |
| PAIRED_SPREAD               | Stat Arb, Carry Basis                                                         |
| ATOMIC multi-leg            | Arbitrage, Vol, Stat Arb (pair enter/exit)                                    |
| DELTA_HEDGED_OPTION         | Vol, Event-Driven, ML Directional (with hedge)                                |
| LP_ACTIVE                   | Market Making                                                                 |
| LEVERAGED_LENDING_LOOP      | Carry Recursive Staked, Carry Staked Basis                                    |

Because the same primitives are re-used, the execution machinery is shared — one `ATOMIC` handler, one `LEADER_HEDGE`
handler, one `DELTA_HEDGE_CONTINUOUS` handler. Adding a new family doesn't require new expression code.

## Versioning of expression library

Expression decomposition is an artifact (in `execution-service/expression_library/`). Consumer-opt-in versioned. See
[../../../04-architecture/artifact-versioning.md](../../../04-architecture/artifact-versioning.md).

## Not in this doc

- **Catalog of expressions** — [../axes/expression.md](../axes/expression.md)
- **Algo implementations** — [execution-policies.md](execution-policies.md)
- **Venue-specific multi-leg mechanics** — execution-service/adapters/
- **Benchmark fills per expression** — [benchmark-fills.md](benchmark-fills.md)
- **Per-family common expressions** — individual family docs

## Cross-references

- Expression axis: [../axes/expression.md](../axes/expression.md)
- Execution policies: [execution-policies.md](execution-policies.md)
- Venue-account coordination (ATOMIC across shared account):
  [venue-account-coordination.md](venue-account-coordination.md)
- Recursive staking archetype: [../archetypes/carry-recursive-staked.md](../archetypes/carry-recursive-staked.md)
- Arbitrage / leader-hedge: [../families/arbitrage-structural.md](../families/arbitrage-structural.md)
