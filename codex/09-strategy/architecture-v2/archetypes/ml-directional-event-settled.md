---
doc_type: codex-ssot
title: "Archetype: `ML_DIRECTIONAL_EVENT_SETTLED`"
summary: >-
  `ML_DIRECTIONAL_EVENT_SETTLED` archetype — event-settled ML value betting: model P(outcome) vs vig-free implied odds,
  gates on `model_confidence_threshold` / `max_odds` / `min_edge_threshold`, stakes fractional Kelly (capped at
  `max_stake_fraction`), routes to best odds via Unity; covers 1X2 / O-U / BTTS / 1H / HT-FT + binary prediction.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [ml, sports, odds, prediction, kelly]
related:
  [
    ../families/ml-directional.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-continuous.md,
    ../../../02-venues/unity-integration.md,
    ../axes/staking-methods.md,
    /codex/09-strategy/architecture-v2/archetypes/rules-directional-event-settled.md,
  ]
created: 2026-04-17
authoritative_for: [ML_DIRECTIONAL_EVENT_SETTLED archetype specification]
referenced_by:
  [
    /codex/02-venues/unity-integration.md,
    /codex/09-strategy/_archived_pre_v2/sports/first-half-prediction.md,
    /codex/09-strategy/_archived_pre_v2/sports/halftime-ml.md,
    /codex/09-strategy/_archived_pre_v2/sports/odds-drift.md,
    /codex/09-strategy/_archived_pre_v2/sports/pre-game-ml.md,
    /codex/09-strategy/_archived_pre_v2/sports/value-betting.md,
    /codex/09-strategy/architecture-v2/archetypes/event-driven.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-prediction.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: ML_DIRECTIONAL_EVENT_SETTLED
family: ML_DIRECTIONAL
venue_universe: [UNITY, BETFAIR, SMARKETS, MATCHBOOK, BETDAQ, POLYMARKET]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 150
  min_sla_tier: premium
---

# Archetype: `ML_DIRECTIONAL_EVENT_SETTLED`

> **Family:** [ML Directional](../families/ml-directional.md) **Settlement model:** Event-settled — position resolves
> discretely on an external event (match result, prediction market resolution). **Code module (target):**
> `strategy-service/engine/strategies/ml_directional_event_settled_engine.py`

## What it does

Consumes probability predictions from an ML model for each outcome of an event (sports 1X2, O/U, BTTS, 1H, halftime;
prediction-market binary), compares to market-implied probability, and places stakes on outcomes with sufficient edge +
confidence. Stakes settle at event resolution.

## Token / position flow

```
Start: BANKROLL in share_class currency (e.g., USD, GBP, EUR, USDC)

Pre-event (or in-play, depending on market type):
  1. MODEL INFERENCE: ml-inference-service returns P(home), P(draw), P(away) for 1X2
                       (or P(over), P(under) for O/U, or P(yes), P(no) for BTTS / binary)
  2. CALIBRATION: apply calibration function
  3. IMPLIED FROM ODDS: 1/decimal_odds → implied probability (optionally vig-free via sum-normalization)
  4. EDGE COMPUTE: edge = calibrated_P - implied_P per outcome
  5. CONFIDENCE GATE: skip outcomes where calibrated_P < model_confidence_threshold
  6. ODDS GATE: skip longshots where decimal_odds > max_odds
  7. EDGE GATE: skip if edge < min_edge_threshold
  8. BEST ODDS: across eligible books (typically Unity routes to best available odds per outcome)
  9. STAKE: fractional Kelly × equity per outcome, capped at max_stake_fraction
  10. EMIT: StrategyInstruction.TRADE with stake on best-odds book

On event settlement:
  - WON: returned = stake × decimal_odds; realized_pnl = returned - stake
  - LOST: realized_pnl = -stake
  - VOID: returned = stake (push)
```

## Supported markets

- **Full match**: 1X2, Double Chance, Asian Handicap, Over/Under total goals, BTTS
- **First half (1H)**: 1X2, O/U, BTTS — reserves capital for phase-2 halftime bets
- **Halftime/Fulltime (HT/FT)**: joint distribution of HT and FT results
- **Halftime-only**: bet after HT using half-time odds (secondary of 1H + HT/2H window)
- **Prediction markets**: binary Yes/No, categorical multi-outcome

## Venue patterns

**Coverage matrix:** See
[`../category-instrument-coverage.md § 2. ML_DIRECTIONAL_EVENT_SETTLED`](../category-instrument-coverage.md#2-ml_directional_event_settled)
for the authoritative venue table (Unity meta-broker with 10 child books; direct access to Betfair, Smarkets, Matchbook,
Betdaq; Polymarket for binary prediction markets).

## Expression options

- **Back** (take odds): buy the outcome at a price; pays out if outcome resolves true
- **Lay** (give odds): sell the outcome at a price on an exchange; pays out if outcome does NOT resolve true
- **Synthetic multi-outcome**: combine back/lay to construct custom payoff (e.g., back home + lay draw to create "home
  or away" payoff)

## Hold policies supported

- `ONE_SHOT` (default) — place bet, wait for event settlement
- Pre-event vs in-play is a timing flag in config, not a hold-policy change

## Config schema (illustrative)

```yaml
model_id: SPORTS_EPL_1X2_CATBOOST_V3
calibration_fn_ref: platt_sports_v2
feature_group_refs:
  - sports-fixture-stats@v4
  - sports-odds-velocity@v3
  - sports-xg-ensemble@v2
market_type: "1X2" # or 1H_1X2, HT_FT, OVER_UNDER, BTTS, BINARY
league: EPL # config dimension
model_confidence_threshold: 0.45 # lower for sports (more uniform priors)
min_edge_threshold: 0.03 # 3% edge after calibration
max_odds: 10.0 # skip longshots > 10.0
kelly_fraction: 0.25
max_stake_fraction: 0.03 # 3% cap per bet
execution_policy_ref: unity-primary-v4
venues:
  - UNITY # primary; routes to best child book
  - BETFAIR_DIRECT # fallback for books not in Unity
hold_policy: ONE_SHOT

# Leverage + net-delta controls (universal per StrategyInstanceDefinition; Stream D 2026-05-07):
target_leverage: 1.0 # [1, 10]; always 1.0 for sports betting (stakes are capital, not leverage)
target_net_delta: 0.0 # net directional delta (0 = model-neutral; back/lay balanced)
max_underlying_move_pct: 3.0 # vol-cap clamp: skip entry if odds move > X% in 1h window
instrument_volatility_registry_lookup: true # use realized_vol_20 (1h candles) from FSS
```

## Execution semantics

- `TRADE` instruction with target = bet (not position_units)
- Single-shot execution: submit, confirm placement, await settlement
- On Unity: API routes to specified child_book (or best-odds if unspecified); single wallet; no inter-book transfer
- On direct books: one wallet per book; strategy config declares eligible books

## P&L attribution

- **Bet outcome**: win/loss/void on settlement
- **Commission**: subtract per-child-book commission on winning bets
- **Execution alpha**: difference between submitted odds and fill odds (exchange MM can give better prices; odds can
  drift before fill)
- **Timing alpha**: for odds-drift signal source, P&L attributable to CLV (closing line value) capture

## Risk profile

- Drawdowns: 15-25% range for well-calibrated sports ML (high-variance outcomes)
- Typical Sharpe: 1.0-2.5 for top sports strategies
- Kill switches: daily-loss limit, per-event max stake breach, model calibration degradation (recent predictions failing
  against actuals), venue outage

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    self.max_stake_usd = new_equity * self.config.max_stake_fraction
    # Event-settled — existing bets are already placed and cannot be resized
    # Only future bets get the new sizing
    return []
```

## Example instances

```
ML_DIRECTIONAL_EVENT_SETTLED@unity-epl-1x2-usd-prod                 (pre-game 1X2)
ML_DIRECTIONAL_EVENT_SETTLED@unity-epl-1h-1x2-usd-prod              (first-half 1X2)
ML_DIRECTIONAL_EVENT_SETTLED@unity-epl-ht-2h-usd-prod               (halftime / second-half)
ML_DIRECTIONAL_EVENT_SETTLED@unity-epl-over-under-usd-prod          (totals)
ML_DIRECTIONAL_EVENT_SETTLED@unity-la-liga-1x2-usd-prod
ML_DIRECTIONAL_EVENT_SETTLED@unity-champions-league-1x2-usd-prod
ML_DIRECTIONAL_EVENT_SETTLED@unity-nba-moneyline-usd-prod
ML_DIRECTIONAL_EVENT_SETTLED@unity-nfl-spread-usd-prod
ML_DIRECTIONAL_EVENT_SETTLED@unity-epl-drift-usd-prod               (odds-drift signal)
ML_DIRECTIONAL_EVENT_SETTLED@polymarket-binary-usdc-prod            (prediction market)
```

## Migration from legacy

| Legacy                                                                                                           | Notes                                                                          |
| ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `sports/pre-game-ml.md`                                                                                          | Market type = full match                                                       |
| `sports/halftime-ml.md`                                                                                          | Market type = HT/2H                                                            |
| `sports/first-half-prediction.md`                                                                                | Market type = 1H; phase-1 capital reservation config                           |
| `sports/odds-drift.md`                                                                                           | Drift signal source variant; edge still computed as value                      |
| `sports/value-betting.md`                                                                                        | Generic base; this archetype covers all value-betting on event-settled markets |
| Code: `ml_sports_strategy.py`, `halftime_ml.py`, `first_half_prediction.py`, `odds_drift.py`, `value_betting.py` | All collapse into `MLDirectionalEventSettledEngine`                            |

## Not in this archetype

- **Continuous-bar ML** (candle-by-candle directional) — `ML_DIRECTIONAL_CONTINUOUS`
- **Sports market making** (passive quoting around reference odds) — `MARKET_MAKING_EVENT_SETTLED`
- **Cross-book arbitrage** (simultaneous back+lay across venues for structural edge) — `ARBITRAGE_PRICE_DISPERSION`
- **Rule-based sports staking** (fixed-stake or threshold-crossing rules) — `RULES_DIRECTIONAL_EVENT_SETTLED`
- **Odds-drift CLV capture** where the rule is "drift exceeded X bps" — `RULES_DIRECTIONAL_EVENT_SETTLED`

## See also

- Family: [ml-directional.md](../families/ml-directional.md)
- Continuous variant: [ml-directional-continuous.md](ml-directional-continuous.md)
- Unity integration: [../../../02-venues/unity-integration.md](../../../02-venues/unity-integration.md)
- Staking (Kelly for event bets): [../axes/staking-methods.md](../axes/staking-methods.md)
