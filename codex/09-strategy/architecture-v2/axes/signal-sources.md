---
doc_type: codex-ssot
title: "Axis: Signal Sources"
summary:
  'Signal-source axis catalog — the mechanism that produces the raw decision trigger: ML models, rules engines,
  rate/yield monitors, orderbook/microstructure, price-dispersion scanners, DeFi protocol-state watchers, event
  calendars, vol metrics, spread models, mempool. Includes the "if primary alpha is X → use source Y" selection guide;
  every source is a versioned artifact feeding the edge-method axis.'
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [strategy, signal-sources, ml, features, market-making, book-microstructure]
related:
  [
    /codex/09-strategy/architecture-v2/axes/edge-methods.md,
    /codex/09-strategy/architecture-v2/axes/expression.md,
    /codex/09-strategy/architecture-v2/axes/venue-eligibility.md,
    /codex/09-strategy/architecture-v2/axes/staking-methods.md,
    ../../../04-architecture/artifact-versioning.md,
  ]
created: 2026-04-17
authoritative_for: [signal-source axis (raw decision-trigger catalog)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/axes/edge-methods.md,
    /codex/09-strategy/architecture-v2/axes/expression.md,
    /codex/09-strategy/architecture-v2/axes/hold-policy.md,
    /codex/09-strategy/architecture-v2/axes/staking-methods.md,
    /codex/09-strategy/architecture-v2/families/ml-directional.md,
    /codex/09-strategy/architecture-v2/families/rules-directional.md,
    /codex/09-strategy/architecture-v2/families/stat-arb-pairs.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Axis: Signal Sources

> **What it is:** The mechanism that produces the raw decision trigger — ML model output, rule firing, rate differential
> observation, orderbook event, etc.
>
> **How it relates to families:** Each family typically consumes 1-3 signal source types. Families are determined by the
> primary alpha source; signal source is HOW the alpha is produced.

## Catalog of signal sources

### ML models

Trained machine-learning models that produce predictions from features.

| Sub-type                  | Typical output                                               | Used by                                                 |
| ------------------------- | ------------------------------------------------------------ | ------------------------------------------------------- |
| Binary classifier         | P(up) / P(down)                                              | ML Directional (continuous + event-settled)             |
| Multi-class classifier    | P(class_i) for N classes                                     | ML Directional for 1X2 (sports), multi-category events  |
| Regression                | Predicted continuous value (e.g., closing odds, next return) | Odds-drift (ML Directional), vol forecast (Vol Trading) |
| Ranking (cross-sectional) | Rank scores across universe                                  | Stat Arb Cross-Sectional                                |
| Probability calibration   | Raw score → calibrated probability                           | Paired with any classifier                              |

Examples:

- `CRYPTO_BTC_CATBOOST_V4` (binary classifier on BTC direction)
- `SPORTS_EPL_1X2_CATBOOST_V3` (multi-class on 1X2 outcome)
- `EQUITY_CS_CATBOOST_V3` (cross-sectional ranking on Russell 1000)

### Rules engines

Hard-coded feature-threshold rules evaluating to fire/no-fire.

| Sub-type                | Used by                                |
| ----------------------- | -------------------------------------- |
| TA indicators           | Rules Directional Continuous           |
| Feature-condition rules | Rules Directional (both), sports rules |
| Regime classifiers      | Rules Directional Continuous           |
| Pattern match           | Rules Directional Continuous           |

### Rate / yield monitors

Continuous observation of rates.

| Sub-type                                 | Used by                                          |
| ---------------------------------------- | ------------------------------------------------ |
| Funding rate feeds                       | Carry & Yield (basis perp, funding carry)        |
| Lending APY feeds                        | Carry & Yield (yield rotation), recursive staked |
| Staking reward rates                     | Carry & Yield (simple staking, staked basis)     |
| Basis spread computation (future − spot) | Carry & Yield (basis dated)                      |

### Orderbook / microstructure

Real-time orderbook state.

| Sub-type                                        | Used by                       |
| ----------------------------------------------- | ----------------------------- |
| L2 bid/ask depth                                | Market Making (CLOB)          |
| Theo fair-value computer (mid, VWAP, consensus) | Market Making                 |
| Reference price (e.g., Smarkets for sports)     | Market Making (event-settled) |
| Inventory state (from PBMS + local shadow)      | Market Making                 |

### Price-dispersion scanners

Cross-venue / cross-instrument price comparisons.

| Sub-type                                              | Used by                |
| ----------------------------------------------------- | ---------------------- |
| Cross-venue same-instrument price comparison          | Arbitrage / Structural |
| Funding rate dispersion                               | Arbitrage / Structural |
| Vol dispersion (cross-venue or within-surface no-arb) | Arbitrage / Structural |
| Aggregated orderbook (for sports arb)                 | Arbitrage / Structural |

### Protocol state watchers (DeFi)

On-chain state monitoring.

| Sub-type               | Used by                                 |
| ---------------------- | --------------------------------------- |
| Health factor monitor  | Liquidation Capture                     |
| Pool TVL + volume      | Market Making (LP allocation decisions) |
| Oracle vs market price | Arbitrage, Liquidation Capture          |
| Gas price              | Multiple (execution cost awareness)     |

### Event calendars

Scheduled external events.

| Sub-type                                 | Used by                            |
| ---------------------------------------- | ---------------------------------- |
| Macro event calendar (FOMC, CPI, NFP)    | Event-Driven                       |
| Earnings calendar                        | Event-Driven                       |
| Sports fixture schedule                  | ML/Rules Directional Event-Settled |
| Crypto-specific (hard forks, governance) | Event-Driven                       |

### Vol metrics

Volatility observations.

| Sub-type                                                        | Used by                   |
| --------------------------------------------------------------- | ------------------------- |
| IV surface fitter (SVI, SSVI)                                   | Vol Trading               |
| Realized vol computer (close-to-close, Parkinson, Garman-Klass) | Vol Trading               |
| Historical vol percentiles                                      | Vol Trading (regime bets) |
| Skew computation                                                | Vol Trading               |

### Spread models (for stat arb)

Computed from paired underlyings.

| Sub-type                                     | Used by                  |
| -------------------------------------------- | ------------------------ |
| Rolling OLS hedge ratio                      | Stat Arb Pairs Fixed     |
| Kalman filter                                | Stat Arb Pairs Fixed     |
| Cointegration test (Engle-Granger, Johansen) | Stat Arb Pairs Fixed     |
| Cross-sectional factor model                 | Stat Arb Cross-Sectional |

### Mempool (DeFi-specific)

Pending transaction monitoring.

| Sub-type                 | Used by                                   |
| ------------------------ | ----------------------------------------- |
| Pending DEX swap watcher | MEV / Liquidation (competition awareness) |
| Oracle update pending    | Arbitrage (oracle front-running — niche)  |

## Signal source selection guide

| If primary alpha is...                      | Use signal source type          |
| ------------------------------------------- | ------------------------------- |
| Model-predicted probability vs implied      | ML model                        |
| Hand-crafted feature-threshold rule firing  | Rules engine                    |
| Rate/yield differential                     | Rate/yield monitor              |
| Bid-ask spread capture                      | Orderbook + theo computer       |
| Cross-venue price dispersion                | Price-dispersion scanner        |
| Protocol mechanic (liquidation, MEV)        | Protocol state watcher          |
| Scheduled event surprise                    | Event calendar + consensus feed |
| Vol dislocation                             | Vol metric (IV surface + RV)    |
| Spread mean-reversion on paired underlyings | Spread model                    |

## Not in this axis

- **Trade expression choice** (spot/perp/options/synthetic) — that's its own axis ([expression](expression.md))
- **Venue selection** — that's its own axis ([venue-eligibility](venue-eligibility.md))
- **Stake sizing method** — that's [staking-methods](staking-methods.md)
- **Edge method** (value vs momentum vs arb) — that's [edge-methods](edge-methods.md); signal source feeds into edge
  method
- **Execution algorithm** — that's a cross-cutting concern
  ([execution-policies](../cross-cutting/execution-policies.md))

## Artifact versioning

Every signal source is a versioned artifact (ML model version, rule registry version, event calendar version, surface
model version). Strategy configs reference by explicit version. Consumer-opt-in upgrade per
[artifact-versioning](../../../04-architecture/artifact-versioning.md).

## Cross-references

- Signal feeds into: [edge-methods.md](edge-methods.md)
- Families that use each signal type: [../families/](../families/)
- Feature groups (underlying data):
  [../../../04-architecture/artifact-versioning.md](../../../04-architecture/artifact-versioning.md)
