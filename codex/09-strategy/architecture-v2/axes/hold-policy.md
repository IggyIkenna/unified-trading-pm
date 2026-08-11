---
doc_type: codex-ssot
title: "Axis: Hold Policy"
summary:
  "Hold-policy axis catalog — how long a position lives and what exits it: SAME_CANDLE_EXIT (CeFi/TradFi ML only, never
  DeFi), HOLD_UNTIL_FLIP (DeFi default), CONTINUOUS, ONE_SHOT, EXPIRY_DRIVEN, CONVERGENCE_DRIVEN, REBALANCE_DRIVEN.
  Defines the per-policy exit-triggers config contract and the hold-policy×family table; drives P&L time-in-position and
  batch/live parity."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [strategy, hold-policy, reconciliation, defi, execution, backtest]

  [
    /codex/09-strategy/architecture-v2/axes/staking-methods.md,
    /codex/09-strategy/architecture-v2/axes/signal-sources.md,
    ../cross-cutting/execution-policies.md,
    ../cross-cutting/benchmark-fills.md,
  ]
created: 2026-04-17
authoritative_for: [hold-policy axis (position lifetime + exit-trigger catalog)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-continuous.md,
    /codex/09-strategy/architecture-v2/axes/edge-methods.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Axis: Hold Policy

> **What it is:** How long a position lives, and what triggers its exit. This axis is orthogonal to edge method, signal
> source, and expression.
>
> **Why it matters:** Hold policy drives P&L attribution (time-in-position), determines whether batch and live can be
> validly compared, and fixes which exit mechanics the strategy must emit (take-profit, stop, horizon, flip,
> convergence, expiry).

## Catalog of hold policies

### `SAME_CANDLE_EXIT`

Position entered and exited within the same bar/candle window (e.g., 1m, 5m, 1h).

- **Used by:** ML Directional Continuous (SCE ML strategies), some Rules Directional short-horizon
- **Exits:** take-profit, stop-loss, or end-of-candle forced exit
- **Benchmark:** OHLC within the bar
- **Rule:** DeFi strategies are NEVER SCE (gas + confirmation latency). SCE is only for CeFi/TradFi ML strategies with
  explicit TP/SL.

### `HOLD_UNTIL_FLIP`

Position held until signal flips sign or signal-specific exit condition. No time limit.

- **Used by:** ML Directional Continuous (flip), Rules Directional Continuous (trend-following), Carry & Yield (most),
  Stat Arb (spread converges)
- **Exits:** signal-driven (new signal says opposite/neutral), cointegration breakdown, z-score mean-reversion, funding
  flip, APY crosses cost
- **Default for:** all DeFi strategies

### `CONTINUOUS`

Always-on quoting / market making; no notion of "entry" and "exit" — instead, inventory tilts around a target.

- **Used by:** Market Making (both archetypes), LP provision
- **Exits:** explicit kill-switch, inventory over-concentration, or operator command
- **P&L is captured via:** realized fills per trade + inventory mark-to-market

### `ONE_SHOT`

Position entered to capture a defined event; closes on fixed rule (arbitrage unwind, liquidation settlement, event
resolution).

- **Used by:** Arbitrage Price Dispersion, Liquidation Capture, Event-Driven (pre/post-event), ML Directional
  Event-Settled, Rules Directional Event-Settled, sports bets
- **Exits:**
  - Arbitrage: when spread closes to cost
  - Liquidation: on successful settlement (same tx)
  - Event-driven: at fixed post-event horizon
  - Sports: at fixture settlement
  - Event-settled ML: at event settlement

### `EXPIRY_DRIVEN`

Position lives until instrument expires; unwind may happen before if greeks degrade or opposite signal.

- **Used by:** Vol Trading Options, Carry Basis Dated, dated options strategies
- **Exits:** expiry roll, delta/vega threshold, explicit unwind

### `CONVERGENCE_DRIVEN`

Position closes when a spread / residual converges to a defined band.

- **Used by:** Stat Arb Pairs Fixed, Stat Arb Cross-Sectional (per-position basis), some Arbitrage variants (basis
  trades)
- **Exits:** z-score below exit threshold, spread within band, cointegration breakdown (forced)

### `REBALANCE_DRIVEN`

Position is a moving target — on each rebalance tick, the position is reconciled to the current target, which may be
zero or may have rotated.

- **Used by:** Stat Arb Cross-Sectional, portfolio-allocator directed rebalances, Yield Rotation Lending, LP allocation
  rebalancing
- **Exits:** implicitly on rebalance when target weight falls to zero

## Hold policy × family table

| Family                          | Typical hold policies                                |
| ------------------------------- | ---------------------------------------------------- |
| ML Directional Continuous       | SAME_CANDLE_EXIT or HOLD_UNTIL_FLIP                  |
| ML Directional Event-Settled    | ONE_SHOT                                             |
| Rules Directional Continuous    | HOLD_UNTIL_FLIP                                      |
| Rules Directional Event-Settled | ONE_SHOT                                             |
| Carry & Yield (all)             | HOLD_UNTIL_FLIP (signal: carry no longer profitable) |
| Carry Basis Dated               | EXPIRY_DRIVEN                                        |
| Arbitrage Price Dispersion      | ONE_SHOT                                             |
| Liquidation Capture             | ONE_SHOT                                             |
| Market Making (both)            | CONTINUOUS                                           |
| Event-Driven                    | ONE_SHOT                                             |
| Vol Trading Options             | EXPIRY_DRIVEN + greek-threshold unwind               |
| Stat Arb Pairs Fixed            | CONVERGENCE_DRIVEN                                   |
| Stat Arb Cross-Sectional        | REBALANCE_DRIVEN                                     |

## Exit mechanics contract

Strategy config declares exit triggers explicitly:

```yaml
hold_policy: SAME_CANDLE_EXIT
exit_triggers:
  - take_profit_pct: 0.008 # 80 bps
  - stop_loss_pct: 0.004 # 40 bps
  - time_forced: END_OF_CANDLE
```

```yaml
hold_policy: HOLD_UNTIL_FLIP
exit_triggers:
  - signal_sign_flipped
  - signal_confidence_below: 0.55
  - optional_stop_loss_pct: 0.03 # circuit breaker only
```

```yaml
hold_policy: CONVERGENCE_DRIVEN
exit_triggers:
  - z_score_abs_below: 0.3
  - cointegration_pvalue_above: 0.15
  - max_hold_bars: 720
  - stop_z_score: 3.5
```

```yaml
hold_policy: ONE_SHOT
exit_triggers:
  - event_settled
  - post_event_horizon_seconds: 3600
```

```yaml
hold_policy: EXPIRY_DRIVEN
exit_triggers:
  - days_to_expiry_below: 2
  - delta_abs_above: 0.85
  - vega_below_min: true
```

```yaml
hold_policy: CONTINUOUS
inventory_policy:
  target_inventory: 0
  max_inventory_abs: 500_000_usd
  skew_on_inventory: true
```

## Time-in-position and P&L attribution

P&L is attributed per-position with entry/exit timestamps. Hold policy is metadata on each position for downstream
reporting.

## Batch vs live parity

For batch (historical) runs to be comparable with live:

- Same exit triggers must fire in batch as would in live
- `END_OF_CANDLE` semantics must use the same bar boundary definitions
- Event-settled strategies need event timestamps + settlement timestamps from reference data

Batch and live use the SAME code path. See
[../../../04-architecture/backtest-groups.md](../../../04-architecture/backtest-groups.md).

## Not in this axis

- **Staking / sizing** — [staking-methods.md](staking-methods.md)
- **When to flip a HOLD_UNTIL_FLIP signal** — that's the signal source / edge method
- **Whether to roll an EXPIRY_DRIVEN position** — that's a config choice, not this axis
- **Global kill switch** — [../cross-cutting/risk-gates.md](../cross-cutting/risk-gates.md)

## Cross-references

- Execution-policies for how exits are physically placed:
  [../cross-cutting/execution-policies.md](../cross-cutting/execution-policies.md)
- Benchmark-fills for batch/live parity: [../cross-cutting/benchmark-fills.md](../cross-cutting/benchmark-fills.md)
- SCE rules (ML-driven same-candle only): feedback in memory `sce_mode_rules.md`
