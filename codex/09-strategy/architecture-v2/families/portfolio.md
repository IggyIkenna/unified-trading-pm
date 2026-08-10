---
doc_type: codex-ssot
title: "Family: Portfolio"
summary:
  The Portfolio strategy family — 4 meta-allocation archetypes (multi-strategy, risk-parity, factor-allocation,
  tactical-overlay) that emit AllocationDirective events to re-weight child strategies rather than TRADE instructions;
  strategy instances (not the Portfolio Allocator service), run through the same risk/kill-switch gates.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, portfolio, allocation, risk-parity, meta-allocation]
related:
  [
    ../cross-cutting/portfolio-allocator.md,
    ../../../04-architecture/capital-flow-model.md,
    ../cross-cutting/risk-gates.md,
    ../archetypes/portfolio-multi-strategy.md,
  ]
created: 2026-05-18
authoritative_for: [Portfolio strategy family spec (4 meta-allocation archetypes)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-factor-allocation.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-multi-strategy.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-risk-parity.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-tactical-overlay.md,
    /codex/09-strategy/strategy-summary.md,
  ]
owner:
last_reviewed: 2026-05-18
code_refs:
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

## Latency Requirements

**Category: `High`** — minutes-scale, cadence-driven, live mode only (batch mode has no latency requirements; it replays
historical data at compute speed). Baseline: the archived
[`/codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md`](/codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md)
table — SUPERSEDED as a doc, but its **Yield Optimization** row (Tick-to-Signal <300 s / Signal-to-Order <30 s /
Order-to-Fill 12–24 s L1 / Total E2E <360 s, Category **High**) is the closest analog (scheduled, batch-adjacent
decision cadence). **Derivation reasoning** (per the 2026-08-10 audit rubric at
[`/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md`](/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md)):
the operator's ms-realm ruling did NOT name portfolio, and — decisive here — the doc's OWN content already declares the
category explicitly in the Alpha thesis: "**Latency profile:** Higher-latency-tolerant. Portfolio archetypes re-run on
scheduled cadences (daily / weekly / intraday for tactical overlay) — not on each market-data tick. `latency_budget_ms`
is set to 60 000 (1 min) for cadence-run strategies; tactical overlay may reduce to 10 000 ms for intraday reweights."
That is unambiguously the `High` pattern (minutes acceptable, batch-adjacent), consistent with the archived Yield
Optimization / Funding Rate Harvest High rows. The family's output is `AllocationDirective` events to re-weight child
strategies, not per-tick trade decisions — there is no tick-to-signal race by construction.

| Segment         | Budget          | Notes                                                                                                                                                                                                                                                                |
| --------------- | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tick-to-Signal  | < 60 s          | Portfolio-state snapshot (realized vols, factor loadings, regime indicators) → allocation re-weight. Cadence-run (daily/weekly); not per-tick. `latency_budget_ms` = 60 000 for cadence-run strategies (doc's Alpha thesis).                                         |
| Signal-to-Order | < 30 s          | `AllocationDirective` emission → child-strategy weight update. Child strategies execute the actual trades on their own latency profiles; portfolio's "order" is the directive event, seconds-scale is ample.                                                         |
| Order-to-Fill   | N/A (no direct) | Portfolio archetypes never emit `TRADE` instructions — instrument positions arise inside child strategies (doc's "No direct instrument positions"). There is no portfolio-level order-to-fill; the child families' Order-to-Fill segments apply to their own trades. |
| **Total E2E**   | **< 60 s**      | Cadence budget (`latency_budget_ms` = 60 000); tactical overlay may tighten to 10 000 ms for intraday reweights. Well inside the minutes-scale High envelope.                                                                                                        |

**Deployment implication:** `High` ⇒ the `distributed` deployment profile per the `/configs/runtime-topology.yaml`
`deployment_profiles` category mapping, referencing
[`/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md`](/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md)
§ 6. There is currently **no `PORTFOLIO` row in the § 6 `topology_requirements` table** — the paired deployment-profile
derivation todo
([`/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md`](/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md)
todo 8) should add one consistent with `distributed`: execution `isolated` (execution is always isolated), strategy
`shared OK`, co-location `no`, min SLA `basic`-or-`standard` (a cadence-driven meta-allocator has no latency guarantee
to sell; `basic` is the honest floor, `standard` is defensible). Nothing in this family needs co-location.

### Decision latency vs. inter-leg execution gap

Not applicable in the ms-realm sense. Portfolio archetypes emit `AllocationDirective` events to re-weight child
strategies on a scheduled cadence — there is no lead/lag leg pair whose inter-leg gap captures the edge, which is the
scenario the 2026-08-10 operator ruling ("lag leg followed by the lead leg is ms timing") targets. The family's
"execution" is a directive, not a two-sided trade. The only sub-archetype with a tighter window is
`PORTFOLIO_TACTICAL_OVERLAY` (intraday reweights, `latency_budget_ms` reduced to 10 000 ms) — still seconds-scale, well
outside the sub-second/low category, and its reweight still goes through a directive rather than paired instrument legs.

## Related documents

- Portfolio Allocator service: [`../cross-cutting/portfolio-allocator.md`](../cross-cutting/portfolio-allocator.md)
- Capital flow model: [`../../../04-architecture/capital-flow-model.md`](../../../04-architecture/capital-flow-model.md)
- Strategy-level risk gates: [`../cross-cutting/risk-gates.md`](../cross-cutting/risk-gates.md)
- Kill-switch:
  [`../../../04-architecture/kill-switch-circuit-breaker.md`](../../../04-architecture/kill-switch-circuit-breaker.md)
