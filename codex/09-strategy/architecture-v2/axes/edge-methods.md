---
doc_type: codex-ssot
title: "Axis: Edge Methods"
summary:
  Edge-method axis catalog — the rule that turns a raw signal into a bet decision ("when should this fire?"). Enumerates
  value (model>implied), threshold-crossed, rate-differential-sustained, spread-capture, arbitrage (dispersion>cost),
  structural-bonus, z-score/mean-reversion, momentum/trend, vol-metric-dislocation, surprise×direction — plus the
  primary/alternative edge method per family.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [strategy, edge-methods, signal-sources, arbitrage, market-making, stat-arb]

  [
    /codex/09-strategy/architecture-v2/axes/signal-sources.md,
    /codex/09-strategy/architecture-v2/axes/staking-methods.md,
    /codex/09-strategy/architecture-v2/axes/expression.md,
    /codex/09-strategy/architecture-v2/axes/hold-policy.md,
    ../cross-cutting/benchmark-fills.md,
  ]
created: 2026-04-17
authoritative_for: [edge-method axis (signal-to-bet-decision rule catalog)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/axes/signal-sources.md,
    /codex/09-strategy/architecture-v2/axes/staking-methods.md,
    /codex/09-strategy/architecture-v2/cross-cutting/benchmark-fills.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Axis: Edge Methods

> **What it is:** The way a strategy converts a raw signal into a bet decision — the rule for "when should this fire?"
>
> **How it relates to signal source:** Signal source produces raw data; edge method decides whether/how to act on it.

## Catalog of edge methods

### Value (model_prob > implied_prob)

Strategy produces a probability estimate; market implies a probability from prices/odds. Bet when model exceeds implied
by a threshold.

- **Used by:** ML Directional (both archetypes), Rules Directional (when rule confidence can be mapped to probability)
- **Config:** `min_edge_threshold`, `min_confidence_threshold`, calibration function
- **Variants:**
  - Vig-free value (sports): strip bookmaker overround before computing implied
  - Kelly-scaled: edge drives stake size via Kelly criterion

### Threshold-crossed

Rule fires when a feature crosses a configured threshold. Implicit claim that the rule has positive EV when firing.

- **Used by:** Rules Directional (both)
- **Config:** per-rule threshold values, feature references
- **Variants:**
  - AND-composition: multiple features all cross thresholds
  - OR-composition: any single feature crosses
  - Multi-rule consensus: N rules must fire

### Rate differential sustained

Observed rate spread between venues/protocols exceeds cost threshold with some persistence.

- **Used by:** Carry & Yield (all variants)
- **Config:** `min_funding_rate`, `min_apy_differential`, persistence window
- **Variants:**
  - Cross-venue funding (basis perp)
  - Cross-protocol APY (yield rotation)
  - Staking + basis combined (staked basis)

### Spread capture

Post liquidity; earn bid-ask spread on fills minus adverse selection + fees + inventory risk.

- **Used by:** Market Making (both)
- **Config:** `half_spread`, `min_spread_edge`, `inventory_skew`
- **Variants:**
  - CLOB spread capture
  - AMM fee capture (LP)
  - Event-settled spread on exchanges

### Arbitrage (dispersion > cost)

Price / IV / odds dispersion across venues exceeds total costs. Mechanical, near-risk-free conditional on execution.

- **Used by:** Arbitrage / Structural
- **Config:** `min_edge_bps`, cost model (fees, gas, slippage, commission)
- **Variants:**
  - Cross-venue price dispersion (same instrument)
  - Cross-venue IV dispersion (same option)
  - Within-surface no-arb violations (butterfly, calendar, parity)
  - Funding-rate dispersion

### Structural bonus

Protocol or venue pays a bonus for a specific service. Alpha = bonus after execution cost.

- **Used by:** Liquidation Capture
- **Config:** `min_profit_usd`, liquidation bonus per asset from venue capability registry

### Z-score / mean-reversion

Spread deviates from historical mean by N standard deviations; expect reversion.

- **Used by:** Stat Arb / Pairs (both), Rules Directional (when mean-rev rules are used)
- **Config:** `entry_z_score`, `exit_z_score`, `stop_z_score`, lookback window
- **Variants:**
  - Z on price spread
  - Z on ratio
  - Z on cointegration residual
  - Cross-sectional rank (top/bottom N by score)

### Momentum / trend

Directional continuation on measured trend strength.

- **Used by:** Rules Directional (momentum variants), occasionally Stat Arb (spread momentum)
- **Config:** lookback, momentum threshold
- **Variants:**
  - Simple moving-average crossover
  - Z-score based
  - Breakout (high-of-N-period)

### Vol-metric dislocation

IV/RV divergence, skew extreme, term structure bowed, soft surface residual.

- **Used by:** Vol Trading
- **Config:** divergence threshold, persistence window, percentile reference
- **Variants:**
  - IV/RV divergence
  - Skew percentile extreme
  - Term structure
  - Soft surface residual

### Surprise-magnitude × direction model

Event release surprise crosses sigma threshold; direction model predicts instrument reaction.

- **Used by:** Event-Driven
- **Config:** `min_surprise_sigma`, direction model ref

## Edge method selection per family

| Family                 | Primary edge method                                           | Alternative edge methods         |
| ---------------------- | ------------------------------------------------------------- | -------------------------------- |
| ML Directional         | Value                                                         | Rule-validation combinations     |
| Rules Directional      | Threshold-crossed                                             | Multi-rule consensus             |
| Carry & Yield          | Rate-differential-sustained                                   | Spread-convergence (basis dated) |
| Arbitrage / Structural | Arbitrage (dispersion > cost), Structural-bonus (liquidation) | —                                |
| Market Making          | Spread-capture                                                | —                                |
| Event-Driven           | Surprise × direction                                          | —                                |
| Vol Trading            | Vol-metric-dislocation                                        | —                                |
| Stat Arb / Pairs       | Z-score / mean-reversion                                      | Cross-sectional rank             |

## Not in this axis

- **How size is set** (Kelly / fixed / etc.) — that's [staking-methods](staking-methods.md); edge method only decides
  "should we bet?" not "how much?"
- **Which venues are eligible** — [venue-eligibility](venue-eligibility.md)
- **How the trade is expressed** (spot/perp/options) — [expression](expression.md)
- **How long to hold** — [hold-policy](hold-policy.md)
- **The data source itself** — [signal-sources](signal-sources.md) produces the inputs; edge method consumes them

## Artifact versioning

Edge method parameters (thresholds, windows) are part of strategy config and versioned with config hash. If the edge
method itself changes (different algorithm), that's a slot-version bump or new archetype depending on magnitude.

## Cross-references

- Signal source produces raw data: [signal-sources.md](signal-sources.md)
- Staking method follows edge method: [staking-methods.md](staking-methods.md)
- Benchmark fills contract (edge measurement in batch vs live):
  [../cross-cutting/benchmark-fills.md](../cross-cutting/benchmark-fills.md)
