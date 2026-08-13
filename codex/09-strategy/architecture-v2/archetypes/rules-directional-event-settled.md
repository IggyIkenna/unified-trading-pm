---
doc_type: codex-ssot
title: "Archetype: `RULES_DIRECTIONAL_EVENT_SETTLED`"
summary: >-
  `RULES_DIRECTIONAL_EVENT_SETTLED` archetype — evaluates explicit sports/prediction rule registries (behavioural /
  statistical patterns, e.g. scored-first-home → back HT draw) on features-service sports family, firing one-shot stakes
  at rule `stake_fraction_of_equity` on the best-odds venue via Unity; per-rule hit-rate attribution.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, strategy-service]
scope: [engineer, admin]
tags: [rules, sports, odds, prediction, registry]
related:
  [
    ../families/rules-directional.md,
    /codex/09-strategy/architecture-v2/archetypes/rules-directional-continuous.md,
    ../../../04-architecture/artifact-versioning.md,
    ../../../02-venues/unity-integration.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md,
  ]
created: 2026-04-17
authoritative_for: [RULES_DIRECTIONAL_EVENT_SETTLED archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md,
    /codex/09-strategy/architecture-v2/archetypes/rules-directional-continuous.md,
    /codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md,
    /codex/09-strategy/architecture-v2/families/rules-directional.md,
    plans/epics/sports_master.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: RULES_DIRECTIONAL_EVENT_SETTLED
family: RULES_DIRECTIONAL
venue_universe: [UNITY, BETFAIR, SMARKETS, MATCHBOOK, POLYMARKET]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 500
  min_sla_tier: premium
---

# Archetype: `RULES_DIRECTIONAL_EVENT_SETTLED`

> **Family:** [Rules Directional](../families/rules-directional.md) **Settlement model:** Event-settled (sports,
> prediction markets). **Code module (target):**
> `strategy-service/engine/strategies/rules_directional_event_settled_engine.py`

## What it does

Evaluates explicit rules on sports / prediction features to fire bets on specific markets when conditions are met. Rules
encode behavioural / statistical patterns known to produce edges in sports betting (e.g., "when home team scores first
within 20 min, back away team in HT draw").

## Token / position flow

```
Pre-game or in-play tick:
  1. FEATURE READ: features-service (sports family) provides current feature values for fixture
  2. RULE EVAL: apply rule registry → list of (rule_id, fires, target_market, target_outcome, stake)
  3. MARKET CHECK: verify target market is available + open on eligible venues
  4. ODDS CHECK: verify decimal_odds <= max_odds (skip longshots)
  5. STAKE: rule-specific stake_fraction × equity
  6. EMIT: StrategyInstruction.TRADE with stake on best-odds venue

On event settlement:
  - Standard sports bet settlement (WON / LOST / VOID)
```

## Rule examples (sports)

```yaml
# sports-epl-behavioural-v2.yaml
rules:
  - rule_id: SCORED_FIRST_HOME_EARLY_BACK_AWAY_HT_DRAW
    description: "When home scores first within 20 min, back away team for HT draw"
    when:
      - feature: scored_first_home
        op: equals
        value: 1
      - feature: minute_of_first_goal
        op: less_than
        value: 20
      - feature: minutes_remaining_to_ht
        op: greater_than
        value: 15
    emit:
      market: 1H_1X2
      outcome: draw
      stake_fraction_of_equity: 0.015
      max_odds: 4.0

  - rule_id: BOTH_XG_HIGH_NO_GOAL_BACK_OVER_15_2H
    description: "If both teams have xG > 0.5 at HT with 0-0 score, back over 1.5 goals 2H"
    when:
      - feature: ht_score_home
        op: equals
        value: 0
      - feature: ht_score_away
        op: equals
        value: 0
      - feature: xg_home_at_ht
        op: greater_than
        value: 0.5
      - feature: xg_away_at_ht
        op: greater_than
        value: 0.5
    emit:
      market: 2H_OVER_UNDER_1_5
      outcome: over
      stake_fraction_of_equity: 0.02
      max_odds: 3.5

  - rule_id: TRAILING_AT_HT_COMEBACK_FAVORITE
    description: "If favourite (by pre-game odds) trails at HT, back favourite to come back"
    when:
      - feature: pre_game_favourite_team
        op: equals
        value_ref: trailing_team_at_ht
      - feature: ht_goal_differential
        op: equals
        value: -1
    emit:
      market: FT_1X2
      outcome: favourite
      stake_fraction_of_equity: 0.015
      max_odds: 3.0
```

## Supported markets

All event-settled markets available on configured venues:

- 1X2 (full match, 1H, HT, 2H)
- Over/Under (0.5, 1.5, 2.5, 3.5 goals — full match and 1H/2H specific)
- BTTS (full match and 1H)
- Asian Handicap
- Correct Score
- HT/FT combinations
- Prediction markets (binary Yes/No)

## Venue patterns

**Coverage matrix:** See
[`../category-instrument-coverage.md § 4. RULES_DIRECTIONAL_EVENT_SETTLED`](../category-instrument-coverage.md#4-rules_directional_event_settled)
for the authoritative venue table (Unity meta-broker primary; direct access to Betfair, Smarkets, Matchbook; Polymarket
for binary prediction markets).

## Hold policies

- ONE_SHOT (default — bet placed, wait for settlement)

## Config schema (illustrative)

```yaml
rule_registry_ref: sports-epl-behavioural-v2
feature_group_refs:
  - sports-fixture-stats@v4
  - sports-in-play-progressive@v3
  - sports-odds-pregame@v2
league: EPL
venues: [UNITY, BETFAIR_DIRECT]
share_class: USD
conflict_resolution: priority_order
max_concurrent_rules_fired_per_fixture: 2
execution_policy_ref: unity-primary-v4

# Leverage + net-delta controls (universal per StrategyInstanceDefinition; Stream D 2026-05-07):
target_leverage: 1.0 # [1, 10]; always 1.0 for sports event-settled (stakes = capital)
target_net_delta: 0.0 # net directional delta (0 = balanced back/lay per rule)
max_underlying_move_pct: 3.0 # vol-cap clamp: skip entry if odds move > X% in 1h window
instrument_volatility_registry_lookup: true # use realized_vol_20 (1h candles) from FSS
```

## Execution semantics

- TRADE instruction per fired rule → stake on best-odds venue
- Instruction is one-shot (place bet, wait for settlement)
- Unity or direct book adapter handles placement

## P&L attribution

- Per rule_id: track bets and P&L per rule → rule hit-rate + rule P&L time series
- Per strategy instance: aggregate across rules

## Risk profile

- Drawdowns: 10-20% typical for rule-based sports strategies
- Typical Sharpe: 0.5-1.5 (rules are often lower-edge than ML but more interpretable)
- Kill switches: daily loss limit, per-rule hit rate degradation (rolling window), rule retirement

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    # Sports bets are already placed; can't resize. New bets use new max.
    for rule in self.rules:
        rule.current_max_stake = new_equity * rule.stake_fraction_of_equity
    return []
```

## Example instances

```
RULES_DIRECTIONAL_EVENT_SETTLED@unity-epl-scored-first-usd-prod
RULES_DIRECTIONAL_EVENT_SETTLED@unity-epl-xg-rules-usd-prod
RULES_DIRECTIONAL_EVENT_SETTLED@unity-la-liga-comeback-usd-prod
RULES_DIRECTIONAL_EVENT_SETTLED@unity-nba-quarter-rules-usd-prod
RULES_DIRECTIONAL_EVENT_SETTLED@unity-champions-league-rules-usd-prod
```

## Migration from legacy

No legacy docs. This is a new archetype formalization of sports rules-based betting that previously existed only as
ad-hoc code or wasn't yet implemented.

## Not in this archetype

- **ML-predicted sports edges** (value betting from model probability) — `ML_DIRECTIONAL_EVENT_SETTLED`
- **Sports market making** (passive back+lay inventory) — `MARKET_MAKING_EVENT_SETTLED`
- **Cross-book arb** — `ARBITRAGE_PRICE_DISPERSION`
- **Continuous-instrument rules** (crypto perps, equities) — `RULES_DIRECTIONAL_CONTINUOUS`

## See also

- Family: [rules-directional.md](../families/rules-directional.md)
- Continuous variant: [rules-directional-continuous.md](rules-directional-continuous.md)
- Rule registry as artifact:
  [../../../04-architecture/artifact-versioning.md](../../../04-architecture/artifact-versioning.md)
- Unity integration: [../../../02-venues/unity-integration.md](../../../02-venues/unity-integration.md)
