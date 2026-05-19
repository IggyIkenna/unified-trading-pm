---
scope: [engineer, admin]
last_reviewed: 2026-05-18
---

# Family: Portfolio

> **Alpha source:** Meta-allocation across instances of the other 8 families. Portfolio archetypes do NOT generate
> per-trade signals — they produce `AllocationDirective` events that re-weight or activate/deactivate child strategy
> instances based on portfolio-level objectives.
>
> **Primary edge method:** Allocator-driven (risk-parity, factor-exposure, regime-detection, or operator mandate at the
> strategy level, not the instrument level).
>
> **Typical hold policies:** HOLD_UNTIL_DIRECTIVE (cadence-triggered rebalance).
>
> **Archetype count:** 4

## Alpha thesis

Portfolio archetypes capture meta-level portfolio construction alpha: the performance difference between a naively
equal-weighted strategy basket versus an intelligently re-weighted one. The "signal" is portfolio state (realized
volatilities, factor loadings, regime indicators, operator mandate) rather than per-instrument price/rate data.

**Portfolio archetypes are strategy instances, not the Portfolio Allocator service.** The distinction:

| Concept                          | What it is                                                                                                                                                                                                                                                                                              |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Portfolio Allocator service**  | A dedicated service ABOVE all strategies; allocates equity to strategy instances per client; runs allocator algorithms (FIXED, SHARPE_WEIGHTED, RISK_PARITY, KELLY, etc.). See [`../cross-cutting/portfolio-allocator.md`](../cross-cutting/portfolio-allocator.md).                                    |
| **Portfolio archetype strategy** | A strategy INSTANCE that itself receives equity, emits `AllocationDirective` events to child strategies, and runs through risk-gate / kill-switch / share-class machinery like any other strategy. Composable: a Portfolio strategy can itself be allocated capital by the Portfolio Allocator service. |

**Why a family, not a cross-cutting concern:** Portfolio archetypes run through the same framework as ML Directional or
Carry strategies — they receive equity, declare `StrategyInstanceDefinition`, get risk-gated, and are subject to
kill-switch. The only difference is their output is `AllocationDirective` events rather than per-instrument `TRADE`s.

**Latency profile:** Higher-latency-tolerant. Portfolio archetypes re-run on scheduled cadences (daily / weekly /
intraday for tactical overlay) — not on each market-data tick. `latency_budget_ms` is set to 60 000 (1 min) for
cadence-run strategies; tactical overlay may reduce to 10 000 ms for intraday reweights.

## 4 Archetypes

| Archetype                                                                     | Allocation rule                                                     | Rebalance cadence        |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------ |
| [`PORTFOLIO_MULTI_STRATEGY`](../archetypes/portfolio-multi-strategy.md)       | Fixed operator-mandated weights across N child strategies           | Daily / weekly / monthly |
| [`PORTFOLIO_RISK_PARITY`](../archetypes/portfolio-risk-parity.md)             | Inverse-vol weighting; equal risk contribution across children      | Daily                    |
| [`PORTFOLIO_FACTOR_ALLOCATION`](../archetypes/portfolio-factor-allocation.md) | Factor-exposure targeting; allocates to children by factor loadings | Weekly                   |
| [`PORTFOLIO_TACTICAL_OVERLAY`](../archetypes/portfolio-tactical-overlay.md)   | Regime-classifier or operator-command multiplier on a base weight   | Intraday to daily        |

## What Portfolio archetypes share

- **Input**: equity allocation from Portfolio Allocator service (or operator manual injection).
- **Output**: `AllocationDirective` events to child strategy instances (via strategy-service event bus).
- **State**: tracks child equity targets, realized weights, rebalance timestamps.
- **Risk machinery**: subject to the same kill-switch, position-limit, and drawdown gates as non-portfolio strategies —
  at the portfolio-strategy level (aggregate equity), not at individual child level.
- **Share class**: always USD\* (meta-allocation is denominated in base currency; child strategies handle own
  share-class accounting).
- **No direct instrument positions**: Portfolio strategies never emit `TRADE` instructions. Any instrument-level
  position arises inside child strategies.

## Related documents

- Portfolio Allocator service: [`../cross-cutting/portfolio-allocator.md`](../cross-cutting/portfolio-allocator.md)
- Capital flow model: [`../../../04-architecture/capital-flow-model.md`](../../../04-architecture/capital-flow-model.md)
- Strategy-level risk gates: [`../cross-cutting/risk-gates.md`](../cross-cutting/risk-gates.md)
- Kill-switch:
  [`../../../04-architecture/kill-switch-circuit-breaker.md`](../../../04-architecture/kill-switch-circuit-breaker.md)
