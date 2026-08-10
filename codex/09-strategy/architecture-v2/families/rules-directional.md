---
doc_type: codex-ssot
title: "Family: Rules Directional"
summary:
  The Rules Directional strategy family — 2 archetypes (continuous vs event-settled) firing hard-coded if-else rules on
  features (TA, statistical thresholds, sports-timing) via a versioned YAML rule registry + evaluator; edge is
  threshold-crossed with per-rule hit-rate monitoring that auto-retires stale rules.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, strategy-service]
scope: [engineer, admin]
tags: [strategy, rules, features, odds, execution, cefi, tradfi]
related:
  [
    /codex/09-strategy/architecture-v2/families/ml-directional.md,
    /codex/09-strategy/architecture-v2/families/event-driven.md,
    ../archetypes/rules-directional-continuous.md,
    ../axes/signal-sources.md,
  ]
created: 2026-04-17
authoritative_for: [Rules Directional strategy family spec (alpha thesis + 2 archetypes)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/rules-directional-continuous.md,
    /codex/09-strategy/architecture-v2/archetypes/rules-directional-event-settled.md,
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/families/arbitrage-structural.md,
    /codex/09-strategy/architecture-v2/families/event-driven.md,
    /codex/09-strategy/architecture-v2/families/ml-directional.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Family: Rules Directional

> **Alpha source:** Hard-coded if-else rules on features that produce discrete fire/no-fire signals. Each rule encodes a
> specific behavioural or statistical hypothesis about the underlying market / event.
>
> **Primary edge method:** Threshold-crossed (rule fires when feature values meet condition). Each rule implicitly
> claims positive EV when it fires.
>
> **Typical hold policies:** HOLD_UNTIL_FLIP, ONE_SHOT, or time-boxed hold.
>
> **Archetype count:** 2 — distinguished by settlement model (continuous vs event-settled).

## Alpha thesis

Rules Directional captures patterns that are easier to express as explicit rules than to learn via ML. The alpha source
is the _existence of the pattern itself_ — the rule claims that a specific combination of feature values indicates a
tradeable edge.

Examples:

- **TradFi TA**: "when 20-day z-score > 2.0 and volume > 1.2x average, go long"
- **Crypto TA**: "when RSI < 30 and MACD crosses up, buy; when RSI > 70 and MACD crosses down, sell"
- **Sports behavioural**: "when home team scores first within 20 min, back away team for HT draw"
- **Sports timing**: "when HT score is 0-0 and both teams have ≥0.5 xG, back over 0.5 goals 2H"
- **Commodity regime**: "when realized vol > 30% annualized and oil futures curve is in backwardation, go long
  front-month"

This family complements ML Directional: ML learns latent patterns from data; Rules encodes patterns we already know and
want to test explicitly. Rules strategies are often used as:

- Benchmarks for ML strategies (if rules beat random, they're a baseline)
- Feature inputs to ML (rule-hit events as predictor columns)
- Interpretable alternatives when ML black-box outputs are undesirable
- Early strategies before sufficient ML training data

**Not in this family:**

- Rules that evaluate a model output (e.g., "fire if model_prob > 0.6") — that's using the rule as a confidence filter
  on ML Directional, not a primary rule signal
- Funding-rate rules ("go long funding when > X%") — alpha is rate capture, goes to `CARRY_*`
- Price-dispersion rules ("buy if A < B - threshold") — alpha is mechanical arb, goes to `ARBITRAGE_PRICE_DISPERSION`
- Two-legged spread rules ("z-score entry on GOOG-META") — alpha is spread mean-reversion, goes to
  `STAT_ARB_PAIRS_FIXED`
- Vol-metric rules ("long straddle if IV percentile < 20") — directional vol view, goes to `VOL_TRADING_OPTIONS`
- Schedule-triggered rules ("at FOMC release time if surprise > X") — event-driven, goes to `EVENT_DRIVEN`
- Order-book imbalance rules (microstructure-level quoting adjustments) — covered under `MARKET_MAKING_CONTINUOUS`
  rather than rules directional

## 2 Archetypes

| Archetype                                                                             | Settlement model                                  | When to use                                                                      |
| ------------------------------------------------------------------------------------- | ------------------------------------------------- | -------------------------------------------------------------------------------- |
| [`RULES_DIRECTIONAL_CONTINUOUS`](../archetypes/rules-directional-continuous.md)       | Continuous P&L, positions can be closed any time  | TradFi TA, crypto TA, regime-switching, mean-reversion on continuous instruments |
| [`RULES_DIRECTIONAL_EVENT_SETTLED`](../archetypes/rules-directional-event-settled.md) | Position resolves discretely on an external event | Sports rule-based betting (in-play + pre-game), prediction-market rule-based     |

## Shared primitives (both archetypes)

The Rules Directional family engine provides:

- **Rule registry**: YAML-defined rule catalog, each rule keyed by unique rule_id
- **Rule evaluator**: given current feature values, evaluates all rules in registry, returns list of (rule_id, fires:
  bool, confidence: float)
- **Rule conflict resolution**: if multiple rules fire with conflicting directions, policy to pick (priority order,
  highest-confidence, unanimity-required, etc.)
- **Feature dependency tracking**: each rule declares which feature columns it requires; engine verifies feature
  availability before evaluation
- **Rule hit-rate tracking**: rolling statistics per rule_id for monitoring
- **Rule deprecation path**: retired rules continue to be evaluated (for historical comparison) but don't generate new
  signals

## Typical signal sources

| Signal source                      | Examples                                                                             |
| ---------------------------------- | ------------------------------------------------------------------------------------ |
| Technical indicators               | RSI, MACD, Bollinger Bands, Stochastic, ATR, VWAP, moving-average crossovers         |
| Statistical thresholds             | Z-score, percentile rank, rolling vol, cointegration residual                        |
| Feature-threshold combinations     | Multi-feature AND/OR conditions on any FSS / features-service (sports family) output |
| Regime classifiers (rule-based)    | "Trending" vs "mean-reverting" regime based on hurst exponent or vol threshold       |
| Event-timing rules (sports)        | "scored_first_home AND minute < 20"                                                  |
| Pattern match (candlestick, chart) | Head-and-shoulders, double-top, etc.                                                 |

## Typical edge methods

- **Threshold crossed**: a rule fires → implicit claim of positive EV
- **Rule hit-rate-confirmed**: rule must have positive backtested hit rate to be eligible (backtest-validated rules
  only)
- **Multi-rule consensus**: aggregate multiple rules; fire when ≥N agree
- **Edge from rule-backtest**: each rule has a backtested expected return; use that as staking input

## Position structure

- **Continuous**: single position per (instrument, direction). Entry on rule-fire; exit on rule-flip, time-box, or
  stop-loss.
- **Event-settled**: one stake per (event, outcome). Rule fires on feature conditions pre-game or in-play; bet placed;
  settles at event resolution.

## Typical staking methods

| Method                                                | When used                                                                        |
| ----------------------------------------------------- | -------------------------------------------------------------------------------- |
| Fixed % equity                                        | Default for rules (simpler than Kelly because rule edges are harder to quantify) |
| Rule-specific sizing                                  | Each rule has its own stake_fraction config — empirically calibrated             |
| Confidence-scaled (if rule provides confidence)       | E.g., regime-switching rules scale by regime confidence                          |
| Fractional Kelly (if backtest provides edge estimate) | When rule's historical edge is well-characterised                                |

## Venue patterns

- **Continuous**: CEFI (Binance, OKX, Bybit, Hyperliquid), TRADFI (IBKR equities/futures/FX, CME), DEFI perps (Drift)
- **Event-settled**: Unity (primary for sports), direct sports books, Polymarket (prediction)

## Expression options

- **Continuous**: spot, perp, dated future, options (directional expression)
- **Event-settled**: bet on outcome

Rules strategies default to simpler expressions (spot / perp); the framework supports every expression available to the
archetype.

## Risk profile

- **Drawdowns**: comparable to ML Directional; interpretability is the structural advantage — when a rule stops working
  the failing rule is identifiable and retirable
- **Sharpe**: 0.5–1.5. Lower ceiling than best ML strategies; stability is higher because rule-level hit-rate monitoring
  auto-retires stale rules
- **Kill switches**: same as ML Directional (rapid price move, venue outage)
- **Concentration**: managed via per-rule max-position + per-family gross exposure

## Latency Requirements

**Category: `Low`** — sub-second total E2E, live mode only (batch mode has no latency requirements; it replays
historical data at compute speed). Baseline: the archived
[`/codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md`](/codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md)
table has **no Rules Directional row** — this family is greenfield here, not a correction of existing numbers. The
closest archived analogs are `Momentum` (< 7 s Medium) and `Mean Reversion` (< 3 s Medium) — the two pre-v2 strategy
docs (`cefi/momentum.md`, `cefi/mean-reversion.md`) that this family's Migration table maps to
`RULES_DIRECTIONAL_CONTINUOUS` — both **superseded for this family** by the 2026-08-10 operator correction
(rules-directional must be in the ms realm, the same correction that set ml-directional). The segment budgets below are
derived from the archived doc's own **internal** pipeline budgets instead: `features-*-service` < 100 ms per
single-instrument feature update, `strategy-service` < 20 ms per strategy evaluation (the rule-evaluator leg), and
`execution-service` < 50 ms for a simple market/limit order — plus the archived sports/prediction venue-latency table
for the event-settled fill leg. Unlike ML Directional, this family has **no model-inference leg** in the decision path:
a rule fires directly off feature values, so the tick-to-signal budget is dominated by the feature-update leg with the
rule-evaluator pass on top, not by an inference call. The family's `Rule firing timeline` + `Feature-condition heatmap`
UI dashboard metrics, backed by the archived **Feature Freshness** circuit breaker (feature age > 2× expected → WARN,

> 5× expected → strategy emits no signals), are the operational monitors that enforce the decision-latency numbers: a
> rule firing on a stale feature IS a decision-latency breach, and a rising stale-feature rate is the family-specific
> signal to tighten the pipeline.

| Expression                                                                      | Tick-to-Signal | Signal-to-Order | Order-to-Fill                                                                                      | Total E2E | Category |
| ------------------------------------------------------------------------------- | -------------- | --------------- | -------------------------------------------------------------------------------------------------- | --------- | -------- |
| Continuous single-instrument (spot/perp/dated future)                           | < 100 ms       | < 100 ms        | Venue-dep. (CeFi 20–50 ms order / 10–30 ms fill; TradFi FIX 1–10 ms; DeFi perp confirmation-bound) | < 200 ms  | Low      |
| Continuous options expression (directional — synthetic = long call + short put) | < 100 ms       | < 100 ms        | Venue-dep. (Deribit 15–40 ms order / 10–25 ms fill)                                                | < 200 ms  | Low      |
| Event-settled (sports / prediction-market rule-based)                           | < 500 ms       | < 250 ms        | < 300 ms (odds-venue API 50–300 ms)                                                                | < 1 s     | Low      |

The tick-to-signal budget is dominated by the **feature-update leg**, which is what separates this family's decision
path from ML Directional's: a rule signal needs a feature refresh + rule-evaluator pass before any instruction can be
emitted, and the `< 100 ms` figure above is the archived feature-update budget plus the rule-evaluator's `< 20 ms`
strategy-evaluation budget with margin — not a decision-at-light-speed claim. Cold rule-registry loads (a new rule
version pulling in a fresh YAML registry) are excluded from the live decision path — a loading rule must not block a
warm path that already has a signal.

**Deployment implication:** `Low` ⇒ the `co_located_vm` deployment profile per the `/configs/runtime-topology.yaml`
`deployment_profiles` category mapping (bundled services on one VM for low-latency handoff), matching the market-making,
arbitrage-structural, carry-and-yield, and ml-directional families' derivation. Note this is NOT yet reflected in
[`/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md`](/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md)
§ 6's `RULES_DIRECTIONAL` `topology_requirements` row (execution isolated / strategy shared OK / co-location `no` / min
SLA `basic`), which predates this latency categorization — that row's `no` co-location + `basic` SLA tier (the weakest
of any latency-relevant family, below the `standard` tier the other `Low` families were given) conflicts with the
Low→`co_located_vm` rubric, a discrepancy this audit surfaces for the derivation todo that writes
`/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md`.

### Decision latency vs. inter-leg execution gap

The `< 200 ms` figures above are the **decision budget** — market tick → feature update → rule-evaluator pass → edge
check → a single `StrategyInstruction`. They are NOT the whole requirement for this family's multi-leg expressions,
where the binding constraint is the **inter-leg execution gap** (2026-08-10 operator ruling: "we are executing two legs
of a trade... how are we ensuring the lag leg followed by the lead leg is ms timing"):

- **Options expressions** (Deribit directional, **synthetic = long call + short put**): a rule signal expressed as a
  synthetic is two legs that must be entered together — a short put left naked because its paired call leg filled late
  is the same directional tail risk the Risk profile section warns about. An options position carried with a **delta
  hedge on the underlying** has the same requirement: the hedge leg must follow the fill at ms timing.
- **In-play event-settled rules** (sports rule-based betting): the stake is a single leg, but the rule fires on _live_
  feature conditions and odds — an in-play rule computing against a stale odds or feature read is a mispriced bet. Live
  in-play markets are the tight case (Betfair streaming 50–500 ms odds-update cadence + live feature updates drive the
  `< 1 s` event-settled row); pre-game windows are seconds-to-minutes and relax toward the `Low` category's upper bound.

So for Rules Directional, "Low" means the **inter-leg execution timing budget is ms-realm for every multi-leg
expression** (options synthetics + hedges), while single-leg continuous and pre-game event-settled rules are bounded by
the (still sub-second) decision budget.

## UI dashboard (shared)

- Rule hit-rate (all active rules, rolling window)
- Rule-by-rule P&L attribution
- Rule firing timeline
- Feature-condition heatmap (which conditions are most frequently met)
- Rolling accuracy per rule
- Rolling P&L (family aggregate + per rule)
- Rule deprecation candidates (rules with declining hit rate or P&L)

## Required subscriptions

Every Rules Directional instance's config references:

- One or more **feature_group_ref** — features consumed by rules
- One **rule_registry_ref** — versioned YAML catalog of rules
- One **execution_policy_ref** — execution policy
- Optionally **rule_hit_rate_artifact_ref** — backtested hit rates for confidence weighting

## Typical instance examples

```
CEFI TA:
  RULES_DIRECTIONAL_CONTINUOUS@binance-btc-5m-usdt-prod
  RULES_DIRECTIONAL_CONTINUOUS@hyperliquid-eth-1h-usdt-prod

TradFi TA:
  RULES_DIRECTIONAL_CONTINUOUS@ibkr-spy-5m-usd-prod
  RULES_DIRECTIONAL_CONTINUOUS@ibkr-eurusd-5m-usd-prod
  RULES_DIRECTIONAL_CONTINUOUS@ibkr-cl-futures-1d-usd-prod        (daily mean-reversion)
  RULES_DIRECTIONAL_CONTINUOUS@ibkr-cl-regime-1h-usd-prod          (regime-switching)

Sports rule-based:
  RULES_DIRECTIONAL_EVENT_SETTLED@unity-epl-scored-first-usd-prod  (scored-first rules)
  RULES_DIRECTIONAL_EVENT_SETTLED@unity-epl-ht-scorelines-usd-prod (HT-scorelines rules)
  RULES_DIRECTIONAL_EVENT_SETTLED@unity-la-liga-comeback-usd-prod  (comeback bets)
```

## Reaction to capital flow events

```python
def react_to_equity_change(self, new_equity_usd: Decimal) -> list[StrategyInstruction]:
    self.equity_usd = new_equity_usd
    # Per-rule stake fractions scale with equity
    for rule in self.active_rules:
        rule.current_max_stake = new_equity_usd * rule.stake_fraction_of_equity
    # Rescale active positions to new max
    return self._rescale_active_positions()
```

Default `stake_fraction_of_equity` per rule is 1-3% — rules tend to be smaller-conviction than ML, and you run many
rules in parallel.

## Rebalancing triggers

- Rule fires → open new position (subject to concentration check)
- Rule flips → close + flip position
- Time-box expiry → close position
- Rule retired via config bump → gracefully close remaining positions on that rule
- Equity change → rescale all active positions

## Migration from legacy docs

| Legacy                                           | Mapping                                                      | Notes                                                                                                     |
| ------------------------------------------------ | ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `cefi/momentum.md`                               | `RULES_DIRECTIONAL_CONTINUOUS`                               | TA-based momentum                                                                                         |
| `cefi/mean-reversion.md`                         | `RULES_DIRECTIONAL_CONTINUOUS` (if TA-based)                 | Archetype depends on signal source                                                                        |
| No legacy sports rules doc exists                | New archetype                                                | `RULES_DIRECTIONAL_EVENT_SETTLED` is a new capability; previously these rules would have been ad-hoc code |
| Code: `strategy-service/.../momentum.py`         | `RulesDirectionalContinuousEngine`                           | Rule registry + evaluator                                                                                 |
| Code: `strategy-service/.../mean_reversion.py`   | `RulesDirectionalContinuousEngine`                           | Same engine                                                                                               |
| Code: `strategy-service/.../commodity_regime.py` | `RulesDirectionalContinuousEngine` (regime-switching config) | Regime-classifier as a rule                                                                               |

## Cross-references

- Archetypes: [rules-directional-continuous](../archetypes/rules-directional-continuous.md),
  [rules-directional-event-settled](../archetypes/rules-directional-event-settled.md)
- Signal sources: [axes/signal-sources.md](../axes/signal-sources.md#rules-and-ta)
- Edge methods: [axes/edge-methods.md](../axes/edge-methods.md#threshold-crossed)
- Comparison with ML Directional: [ml-directional.md](ml-directional.md) — rules produce discrete fire/no-fire, ML
  produces continuous probability; both feed value-betting edge method
