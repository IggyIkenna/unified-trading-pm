---
doc_type: codex-ssot
title: "Family: ML Directional"
summary:
  The ML Directional strategy family — 2 archetypes (continuous vs event-settled) betting when calibrated model
  probability exceeds market-implied by a min-edge threshold; fractional-Kelly sized. The general-purpose directional
  family across crypto, equities, sports, options, and prediction markets.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, ml, prediction, odds, features, execution]
related:
  [
    /codex/09-strategy/architecture-v2/families/rules-directional.md,
    /codex/09-strategy/architecture-v2/families/stat-arb-pairs.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
    ../archetypes/ml-directional-continuous.md,
    ../axes/signal-sources.md,
  ]
created: 2026-04-17
authoritative_for: [ML Directional strategy family spec (alpha thesis + 2 archetypes)]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/cross-cutting/ml-pipeline.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-continuous.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md,
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/families/arbitrage-structural.md,
    /codex/09-strategy/architecture-v2/families/event-driven.md,
    /codex/09-strategy/architecture-v2/families/rules-directional.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Family: ML Directional

> **Alpha source:** Machine-learning model prediction of outcome probability vs. market-implied probability. When model
> probability exceeds implied by a threshold (and optionally satisfies calibration/confidence constraints), a bet is
> placed with stake sized by signal strength.
>
> **Primary edge method:** Value (model_prob > implied_prob + min_edge_threshold).
>
> **Typical hold policies:** HOLD_UNTIL_FLIP (tradeable instruments) or ONE_SHOT (event-settled bets).
>
> **Archetype count:** 2 — distinguished by settlement model (continuous vs event-settled).

## Alpha thesis

ML Directional strategies produce a _probability estimate_ per outcome, compare it to market-implied probability
(derived from odds or price), and take a directional position when the model's estimate is sufficiently higher than
implied (accounting for calibration error, confidence threshold, and minimum edge).

This is the most general-purpose directional strategy family. It covers:

- Crypto ML (BTC/ETH/SOL direction prediction on perps, spot, or options)
- Equity ML (SPY/QQQ/individual-stock prediction)
- Sports ML (outcome prediction on 1X2, O/U, BTTS markets)
- Options ML (delta direction, strike selection, vol surface exploitation)
- Binary prediction-market ML (Polymarket event prediction)

## 2 Archetypes

| Archetype                                                                       | Settlement model                                  | When to use                                                                    |
| ------------------------------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------ |
| [`ML_DIRECTIONAL_CONTINUOUS`](../archetypes/ml-directional-continuous.md)       | Continuous P&L, positions can be closed any time  | Tradeable instruments: spot, perp, futures, options, equities, FX, commodities |
| [`ML_DIRECTIONAL_EVENT_SETTLED`](../archetypes/ml-directional-event-settled.md) | Position resolves discretely on an external event | Sports matches, prediction-market outcomes                                     |

Why this split: continuous instruments have real-time P&L, risk management, and position-sizing that differs
fundamentally from event-settled bets (which have stake-out, win-loss-void, no intermediate P&L, different settlement
mechanics, different stake sizing semantics).

## Shared primitives (both archetypes)

The ML Directional family engine provides:

- **Probability calibration**: every raw model probability passes through a calibration function (Platt scaling,
  isotonic regression, or saved calibration curve from training) before being compared to implied
- **Confidence threshold**: minimum model confidence to even consider betting (filters low-quality signals)
- **Edge threshold**: minimum (model_prob - implied_prob) margin over implied, after calibration
- **Implied probability computation**: from decimal odds (sports), from orderbook mid (tradeable), from market price
  (prediction binary)
- **Kelly staking** (with fractional and capped variants): default sizing is fractional Kelly based on calibrated edge
- **Signal deduplication**: don't re-bet the same outcome multiple times on the same signal
- **Confidence-scaled stake**: optional sizing scaling by model confidence above threshold
- **Cross-venue best-odds selection**: for event-settled, find best odds across eligible venues per outcome

## Typical signal sources

| Signal source                                  | Typical archetype | Model class examples                          |
| ---------------------------------------------- | ----------------- | --------------------------------------------- |
| Supervised ML classifier (multi-class)         | Both              | CatBoost, LightGBM, XGBoost, neural net       |
| Cross-sectional ML (rank, then bet top/bottom) | Continuous        | → use `STAT_ARB_CROSS_SECTIONAL` instead      |
| Bayesian posterior (Dirichlet, Beta)           | Both              | Bayesian inference over recent outcomes       |
| Ensemble of ML models                          | Both              | Stacking, voting                              |
| Transformer / sequence model                   | Continuous        | For time-series prediction on crypto/equities |

**Not in this family:** rule-based triggers (→ `RULES_DIRECTIONAL_*`), funding rate capture (→ `CARRY_*`), pair spreads
(→ `STAT_ARB_*`).

## Typical edge methods

- **Value** (primary): `model_prob > implied_prob + min_edge_threshold`, where `min_edge_threshold` is config (typically
  2-5% for sports, 0.5-2% for tradeable, 3-5% for prediction markets)
- **Confidence-filtered value**: additionally require `model_prob > confidence_threshold` to filter low-conviction bets
- **Kelly-weighted edge**: Kelly criterion naturally sizes by edge magnitude; higher edge → bigger bet

## Position structure

- **Continuous**: single position per (instrument, direction). Can be long or short. Position size scales with Kelly +
  confidence. Hold-until-flip is standard.
- **Event-settled**: one stake per (event, outcome). Stake is placed; settles at event resolution. No intermediate P&L
  management.

## Typical staking methods (see [axes/staking-methods.md](../axes/staking-methods.md))

| Method                             | When used                                     |
| ---------------------------------- | --------------------------------------------- |
| Fractional Kelly (0.2-0.5 × Kelly) | Default — scales with edge magnitude          |
| Confidence-scaled Kelly            | When confidence varies widely across signals  |
| Fixed % equity                     | Conservative default; every bet same fraction |
| Fixed notional $                   | When capital budget is discrete per bet       |

## Venue patterns

- **Continuous**: CEFI (Binance, OKX, Bybit, Hyperliquid, Deribit), TRADFI (IBKR, CME, CBOE), DEFI perps (Drift).
  Single-venue typical, but multi-venue SOR supported.
- **Event-settled**: Unity (primary for sports), direct sports books, Polymarket (prediction). Unity enables cross-book
  best-odds per leg with no wallet friction.

## Expression options

- **Continuous**: spot, perp, dated future, options (ATM call, 25d call, synthetic = long call + short put)
- **Event-settled**: bet on outcome (back/lay on exchanges, direct on sportsbooks)

The same archetype + same underlying signal can be expressed differently. Example: a "BTC up" ML signal can be expressed
as:

- Long BTC perp on Hyperliquid
- Long ATM call on Deribit
- Synthetic = long call + short put on Deribit
- Long BTC spot on Binance

Each is a different strategy instance with different expression config; same archetype, same signal source, same edge
method.

## Risk profile

- **Drawdowns**: driven by directional exposure; 10-20% drawdowns typical for ML strategies on crypto (higher vol asset
  classes); 5-10% for equities; 15-25% for sports
- **Sharpe**: mid-range (0.8-2.5 depending on calibration quality and edge threshold)
- **Kill switches**: rapid adverse price move (configurable multiplier of recent ATR), model calibration breach
  (prediction error exceeds training residual), venue outage
- **Concentration risk**: managed via per-instrument max position + per-family gross exposure limits

## Latency Requirements

**Category: `Low`** — sub-second total E2E, live mode only (batch mode has no latency requirements; it replays
historical data at compute speed). Baseline: the archived
[`/codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md`](/codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md)
table has **no ML Directional row** — this family is greenfield here, not a correction of existing numbers. The closest
archived analogs (`Mean Reversion` < 3 s Medium, `Prediction Contrarian` < 75 s High) are **superseded for this family**
by the 2026-08-10 operator correction (ml-directional must be in the ms realm). The segment budgets below are derived
from the archived doc's own **internal** pipeline budgets instead: `features-*-service` < 100 ms per single-instrument
feature update, `ml-inference-api` < 50 ms per warm-model prediction, `strategy-service` < 20 ms per strategy
evaluation, and `execution-service` < 50 ms for a simple market/limit order — plus the archived sports/prediction
venue-latency table for the event-settled fill leg. The family's own
`Stale-signal rate (signals that expired before execution)` UI dashboard metric is the operational monitor that enforces
the decision-latency numbers: a signal that expires before execution IS a decision-latency breach, and a rising
stale-signal rate is the family-specific signal to tighten the pipeline.

| Expression                                                                              | Tick-to-Signal | Signal-to-Order | Order-to-Fill                                                                                      | Total E2E | Category |
| --------------------------------------------------------------------------------------- | -------------- | --------------- | -------------------------------------------------------------------------------------------------- | --------- | -------- |
| Continuous single-instrument (spot/perp/dated future)                                   | < 100 ms       | < 100 ms        | Venue-dep. (CeFi 20–50 ms order / 10–30 ms fill; TradFi FIX 1–10 ms; DeFi perp confirmation-bound) | < 200 ms  | Low      |
| Continuous options expression (ATM call / 25d call / synthetic = long call + short put) | < 100 ms       | < 100 ms        | Venue-dep. (Deribit 15–40 ms order / 10–25 ms fill)                                                | < 200 ms  | Low      |
| Event-settled (sports / prediction-market outcome)                                      | < 500 ms       | < 250 ms        | < 300 ms (odds-venue API 50–300 ms)                                                                | < 1 s     | Low      |

The tick-to-signal budget is dominated by the **model-inference leg**, which is what separates this family from
market-making: an ML signal has a feature-update + inference + calibration cost before any instruction can be emitted,
and the `< 100 ms` figure above is the sum of the archived per-stage budgets (feature update + warm inference + strategy
evaluation) with margin, not a decision-at-light-speed claim. Cold-start model loads (the archived < 500 ms cold-start
figure) are excluded from the live decision path — a cold model must not block a warm path that already has a signal.

**Deployment implication:** `Low` ⇒ the `co_located_vm` deployment profile per the `/configs/runtime-topology.yaml`
`deployment_profiles` category mapping (bundled services on one VM for low-latency handoff), matching the market-making
and arbitrage-structural families' derivation. Note this is NOT yet reflected in
[`/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md`](/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md)
§ 6's `ML_DIRECTIONAL_CONTINUOUS` / `ML_DIRECTIONAL_EVENT` `topology_requirements` rows (execution isolated / strategy
shared OK / co-location `no` / min SLA `standard`), which predate this latency categorization — those rows' `no`
co-location + `standard` SLA tier conflicts with the Low→`co_located_vm` rubric, a discrepancy this audit surfaces for
the derivation todo that writes `/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md`.

### Decision latency vs. inter-leg execution gap

The `< 200 ms` figures above are the **decision budget** — market tick → feature update → model inference → calibration
→ edge computation → a single `StrategyInstruction`. They are NOT the whole requirement for this family's multi-leg
expressions, where the binding constraint is the **inter-leg execution gap** (2026-08-10 operator ruling: "we are
executing two legs of a trade... how are we ensuring the lag leg followed by the lead leg is ms timing"):

- **Options expressions** (Deribit ATM call / 25d call / **synthetic = long call + short put**): a "BTC up" ML signal
  expressed as a synthetic is two legs, and the two must be entered together — a short put left naked because its paired
  call leg filled late is exactly the tail-risk directional exposure the Risk profile section warns about. An options
  position carried with a **delta hedge on the underlying** has the same requirement: the hedge leg must follow the fill
  at ms timing.
- **Cross-venue best-odds selection** (event-settled shared primitive): the stake is a single leg, but the odds
  comparison that picks the venue must be fresh — a stale best-odds read is a mispriced bet. Live/halftime markets are
  the tight case (Betfair streaming 50–500 ms odds-update cadence drives the < 1 s event-settled row); pre-game windows
  are seconds-to-minutes and relax toward the `Low` category's upper bound.

So for ML Directional, "Low" means the **inter-leg execution timing budget is ms-realm for every multi-leg expression**
(options synthetics + hedges), while single-leg continuous and pre-game event-settled bets are bounded by the (still
sub-second) decision budget.

## UI dashboard (shared across all ML Directional instances)

- Confusion matrix (per strategy + family aggregate)
- Calibration curve: predicted prob vs realized outcome frequency
- Edge histogram by bin
- Rolling accuracy (N-trade window)
- Rolling P&L
- P&L attribution: signal alpha + staking alpha + execution alpha (vs benchmark)
- Model prediction distribution over time
- Stale-signal rate (signals that expired before execution)

Strategy-specific pages overlay their own model_id, feature group subscription, thresholds, etc. on top of this shared
dashboard.

## Required subscriptions

Every ML Directional instance's config must reference:

- Exactly one **model_id** (versioned ML artifact) — the predictive model
- One or more **feature_group_ref** (versioned feature artifacts) — features consumed by the model
- Exactly one **execution_policy_ref** (versioned execution policy artifact) — how to execute the trades
- Optionally **calibration_function** (if calibration is strategy-specific; otherwise baked into the model)

Dependency changes bump config version. See [artifact-versioning](../../../04-architecture/artifact-versioning.md).

## Typical instance examples

```
CEFI perps:
  ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod
  ML_DIRECTIONAL_CONTINUOUS@binance-eth-1h-usdt-prod
  ML_DIRECTIONAL_CONTINUOUS@binance-multicoin-5m-usdt-prod   (multi-coin config)

Options expression:
  ML_DIRECTIONAL_CONTINUOUS@deribit-btc-atm-call-5m-usdt-prod
  ML_DIRECTIONAL_CONTINUOUS@deribit-btc-25d-call-1h-usdt-prod

TradFi continuous:
  ML_DIRECTIONAL_CONTINUOUS@ibkr-spy-5m-usd-prod
  ML_DIRECTIONAL_CONTINUOUS@ibkr-eurusd-5m-usd-prod
  ML_DIRECTIONAL_CONTINUOUS@ibkr-cl-futures-1h-usd-prod

Sports event-settled:
  ML_DIRECTIONAL_EVENT_SETTLED@unity-epl-1x2-usd-prod
  ML_DIRECTIONAL_EVENT_SETTLED@unity-la-liga-1x2-usd-prod
  ML_DIRECTIONAL_EVENT_SETTLED@unity-epl-1h-1x2-usd-prod      (first-half market)
  ML_DIRECTIONAL_EVENT_SETTLED@unity-epl-ht-2h-usd-prod       (halftime market)
  ML_DIRECTIONAL_EVENT_SETTLED@unity-nba-moneyline-usd-prod

Prediction markets:
  ML_DIRECTIONAL_EVENT_SETTLED@polymarket-binary-usdc-prod

Same archetype, different slot versions (model swaps):
  ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod       (v1: CATBOOST model)
  ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-v2-prod    (v2: TRANSFORMER model)
```

## Reaction to capital flow events

When Portfolio Allocator or client-deposit changes equity:

```python
def react_to_equity_change(self, new_equity_usd: Decimal) -> list[StrategyInstruction]:
    self.equity_usd = new_equity_usd
    self.max_position_usd = new_equity_usd * self.config.max_position_pct_of_equity
    # For ML Directional, target scales linearly with equity when signal is active
    if self.current_signal is None:
        return []  # no position to resize
    new_target_position_units = (
        self.current_signal.confidence
        * self.config.kelly_fraction
        * self.equity_usd
        / self.current_mid_price
    ) * (1 if self.current_signal.direction == LONG else -1)
    return self._emit_reconciliation(
        current=self.current_position_units,
        target=new_target_position_units,
    )
```

Default `max_position_pct_of_equity` is 15-30% for crypto perps, 5-15% for equities, 3-10% for sports event bets (lower
because multiple simultaneous bets can accumulate exposure).

## Rebalancing triggers

- New signal fires → recompute target → emit instruction
- Existing signal strength changes → recompute target → emit reconciliation
- Equity change (client deposit, PnL, Allocator weight change) → recompute target → emit reconciliation
- Hold-until-flip: signal reversal → close + open opposite position
- Same-candle-exit: hold horizon expiry → close position
- Kill-switch fired → close all positions immediately

## Migration from legacy docs

| Legacy doc                                            | Mapping                                                                                      | Enhancement                                                                                                 |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `cefi/mean-reversion.md`                              | `ML_DIRECTIONAL_CONTINUOUS` (if ML-based) or `RULES_DIRECTIONAL_CONTINUOUS` (if rules-based) | Archetype split based on signal source                                                                      |
| `cefi/momentum.md`                                    | `RULES_DIRECTIONAL_CONTINUOUS`                                                               | Moved to Rules Directional if TA-based                                                                      |
| `tradfi/ml-directional.md`                            | `ML_DIRECTIONAL_CONTINUOUS`                                                                  | Generic archetype; TradFi is just venue config                                                              |
| `tradfi/options-ml.md`                                | `ML_DIRECTIONAL_CONTINUOUS` (if alpha is delta) or `VOL_TRADING_OPTIONS` (if alpha is vol)   | Config disambiguates                                                                                        |
| `sports/value-betting.md`                             | `ML_DIRECTIONAL_EVENT_SETTLED` (generic)                                                     | Value betting is the edge method; generic ML-directional archetype covers all sports value-betting variants |
| `sports/pre-game-ml.md`                               | `ML_DIRECTIONAL_EVENT_SETTLED`                                                               | Market type = full match; config-level                                                                      |
| `sports/halftime-ml.md`                               | `ML_DIRECTIONAL_EVENT_SETTLED`                                                               | Market type = HT/2H; config-level                                                                           |
| `sports/first-half-prediction.md`                     | `ML_DIRECTIONAL_EVENT_SETTLED`                                                               | Market type = 1H; phase-1 capital reservation config                                                        |
| `sports/odds-drift.md`                                | `ML_DIRECTIONAL_EVENT_SETTLED` with drift signal source                                      | Drift is a signal source variant; edge is still value (current_odds > predicted_closing_odds)               |
| Code: `strategy-service/.../ml_sports_strategy.py`    | `MLDirectionalEventSettledEngine`                                                            | Generic engine                                                                                              |
| Code: `strategy-service/.../halftime_ml.py`           | `MLDirectionalEventSettledEngine`                                                            | Config distinguishes market type                                                                            |
| Code: `strategy-service/.../first_half_prediction.py` | `MLDirectionalEventSettledEngine`                                                            | Config distinguishes phase-1 capital cap                                                                    |
| Code: `strategy-service/.../odds_drift.py`            | `MLDirectionalEventSettledEngine`                                                            | Drift signal source                                                                                         |
| Code: `strategy-service/.../value_betting.py`         | `MLDirectionalEventSettledEngine`                                                            | Base class                                                                                                  |
| Code: `strategy-service/.../tradfi_ml_*.py`           | `MLDirectionalContinuousEngine`                                                              | Consolidated                                                                                                |

## Cross-references

- Archetypes: [ml-directional-continuous](../archetypes/ml-directional-continuous.md),
  [ml-directional-event-settled](../archetypes/ml-directional-event-settled.md)
- Signal source axis: [axes/signal-sources.md](../axes/signal-sources.md#ml-models)
- Edge method: [axes/edge-methods.md](../axes/edge-methods.md#value-betting)
- Staking: [axes/staking-methods.md](../axes/staking-methods.md)
- Expression (for options): [axes/expression.md](../axes/expression.md)
- Benchmark fills: [cross-cutting/benchmark-fills.md](../cross-cutting/benchmark-fills.md)
- Artifact versioning: [../../04-architecture/artifact-versioning.md](../../../04-architecture/artifact-versioning.md)
