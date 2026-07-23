---
doc_type: codex-ssot
title: "Axis: Staking Methods (Position Sizing)"
summary:
  'Position-sizing axis ("staking methods") — how much to bet once the edge method says yes: fractional Kelly,
  confidence-scaled, fixed % of equity, fixed notional $, vol-scaled, delta-neutral paired, inventory-skewed, vega/gamma
  notional cap, tier-based, rank-weighted / equal-weight. Final size = min(method output, per-instrument cap, family
  cap, venue headroom, kill-switch reduction); folds in legacy sports staking (Martingale/Roll-up retired).'
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [strategy, staking-methods, sizing, sports, market-making]
related:
  [
    /codex/09-strategy/architecture-v2/axes/edge-methods.md,
    /codex/09-strategy/architecture-v2/axes/signal-sources.md,
    /codex/09-strategy/architecture-v2/axes/venue-eligibility.md,
    ../cross-cutting/risk-gates.md,
  ]
created: 2026-04-17
authoritative_for: [position-sizing axis (staking / stake-sizing method catalog)]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/sports/kelly.md,
    /codex/09-strategy/_archived_pre_v2/sports/staking-methods.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md,
    /codex/09-strategy/architecture-v2/axes/edge-methods.md,
    /codex/09-strategy/architecture-v2/axes/expression.md,
    /codex/09-strategy/architecture-v2/axes/hold-policy.md,
    /codex/09-strategy/architecture-v2/axes/signal-sources.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Axis: Staking Methods (Position Sizing)

> **What it is:** How a strategy decides how much to bet / trade given the edge method has said "yes, bet."
>
> **How it relates:** Orthogonal to edge method. Same edge method can be staked different ways; same staking method can
> serve different edge methods.

## Catalog of staking methods

### Fractional Kelly

Size scales with edge magnitude. `stake_fraction = kelly_fraction × edge / odds_minus_1` (for bets) or similar for
trades.

- **Pros:** mathematically optimal long-run growth
- **Cons:** aggressive; sensitive to calibration error (over-Kelly = ruin)
- **Common multipliers:** 0.25 × Kelly (conservative), 0.5 × Kelly (aggressive), 1.0 × Kelly (risky)
- **Used by:** ML Directional (both), sometimes Carry, Vol Trading

### Confidence-scaled

Stake scales with model confidence above threshold. `stake = base_stake × (confidence - threshold) / (1 - threshold)`.

- **Pros:** ties sizing to signal quality
- **Cons:** requires well-calibrated confidence; can over-size noisy high-confidence signals
- **Used by:** ML Directional (with calibrated models)

### Fixed % of equity

Every bet / trade is the same fraction of current equity.

- **Pros:** simple, equity-scaling, predictable
- **Cons:** ignores edge magnitude — bets of different quality sized the same
- **Typical:** 1-3% for sports bets, 5-15% for continuous ML positions, 10-25% for carry
- **Used by:** Rules Directional, Carry & Yield, many default configurations

### Fixed notional $

Same dollar amount per opportunity regardless of equity.

- **Pros:** simple absolute accounting; works well for fixed-capital-budget strategies
- **Cons:** doesn't scale with equity; requires manual resizing as equity grows
- **Used by:** Arbitrage (per-opp), some Carry variants

### Vol-scaled

Size inversely proportional to realized vol or ATR.

- **Pros:** normalizes risk across vol regimes
- **Cons:** lags vol regime changes; can under-size in calm markets
- **Used by:** Rules Directional, TradFi equity strategies

### Delta-neutral paired

Dollar-notional equal on both legs (or beta-adjusted / cointegration-weighted).

- **Pros:** hedged exposure
- **Cons:** requires careful hedge-ratio maintenance
- **Used by:** Carry basis (all archetypes), Stat Arb Pairs

### Inventory-skewed

Quote size adjusts based on current inventory; widen/shrink based on skew.

- **Pros:** manages inventory risk
- **Cons:** can reduce fill rate if over-skewed
- **Used by:** Market Making (both archetypes)

### Vega / Gamma notional cap

For options strategies: size by greek exposure rather than dollar notional.

- **Pros:** bounds the correct risk metric (vol exposure, not cash)
- **Cons:** requires real-time greeks
- **Used by:** Vol Trading, Options MM

### Tier-based scaled (confidence × edge)

Combines confidence + edge; tier into size buckets (small / medium / large).

- **Pros:** simple interpretable size distribution
- **Cons:** discrete tiers lose information vs continuous scaling
- **Used by:** Some ML Directional variants, Rules Directional

### Rank-weighted (cross-sectional)

Each basket member sized by its rank within the basket.

- **Pros:** higher-confidence names get larger allocation
- **Cons:** concentrates in extreme-ranked names; sensitive to rank stability
- **Used by:** Stat Arb Cross-Sectional

### Equal-weight (cross-sectional)

Each basket member gets equal allocation regardless of score.

- **Pros:** simple, diversified
- **Cons:** ignores score magnitude
- **Used by:** Stat Arb Cross-Sectional (baseline)

## Staking method selection guide

| Strategy characteristic                                     | Suggested staking                         |
| ----------------------------------------------------------- | ----------------------------------------- |
| Well-calibrated ML with reliable edge estimates             | Fractional Kelly (0.25-0.5 ×)             |
| ML with confidence but uncertain calibration                | Confidence-scaled with conservative cap   |
| Rules with backtested hit rate                              | Fixed % or tier-based                     |
| Arbitrage (each opp sized to min(equity cap, opp capacity)) | Fixed $ notional per opp                  |
| Carry / basis (delta-neutral)                               | Delta-neutral paired at target allocation |
| Market making                                               | Inventory-skewed                          |
| Vol trading                                                 | Vega/gamma notional cap                   |
| Stat arb pairs                                              | Delta-neutral paired (beta-adjusted)      |
| Stat arb cross-sectional                                    | Rank-weighted or equal-weight             |

## Staking × risk limits

Staking method produces a _desired_ position size. Final size is always capped by:

- `max_position_pct_of_equity` (per instrument)
- Family-level gross exposure limit
- Venue-account margin availability (from R&E pre-flight)
- Kill-switch reductions (if active)

So: final_size = min(staking_method_output, per_instrument_cap, family_cap, venue_account_headroom,
post_kill_switch_reduction).

## Sports-specific staking note

Legacy `sports/staking-methods.md` covered 7 methods for sports betting:

- Fixed Dollar
- Fixed Percentage
- Kelly / Fractional Kelly
- Adaptive Daily
- Confidence-scaled
- Martingale (not recommended — retired)
- Roll-up (not recommended — retired)

These map directly into the catalog above. Sports strategies typically use Fractional Kelly (for ML), Fixed % (for
rules), or Confidence-scaled. Martingale and Roll-up are explicitly not supported due to ruin risk.

## Not in this axis

- **Edge method** (when to bet) — [edge-methods](edge-methods.md)
- **Signal source** (raw data / prediction) — [signal-sources](signal-sources.md)
- **Venue selection** — [venue-eligibility](venue-eligibility.md)
- **Risk limit enforcement** (per-instrument caps, gross exposure limits) — cross-cutting:
  [../cross-cutting/risk-gates.md](../cross-cutting/risk-gates.md)
- **Post-fill rebalancing** — covered by strategy engine's target-state reconciliation; not a staking method

## Cross-references

- Edge method drives stake magnitude input: [edge-methods.md](edge-methods.md)
- Risk gates cap output size: [../cross-cutting/risk-gates.md](../cross-cutting/risk-gates.md)
- Legacy sports staking (Kelly, fractional Kelly, flat-stake, level-stake, percentage-of-bankroll) was previously
  documented separately under `09-strategy/sports/` and has been folded into this axis doc.
