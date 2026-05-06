---
scope: [engineer, admin]
topology_requirements:
  isolation:
    execution-service: isolated
  co_location: []
  latency_budget_ms: 500
  min_sla_tier: basic
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# Archetype: `RULES_DIRECTIONAL_CONTINUOUS`

> **Family:** [Rules Directional](../families/rules-directional.md) **Settlement model:** Continuous P&L, positions can
> be closed any time. **Code module (target):**
> `strategy-service/engine/strategies/rules_directional_continuous_engine.py`

## What it does

Evaluates a registry of explicit if-else rules on features. When a rule fires (feature conditions met), emit a
directional signal. Stake size is rule-specific (fixed % equity per rule or calibrated from backtested hit rate).

## Token / position flow

```
On signal tick:
  1. FEATURE READ: pull current values of all features the rule registry depends on
  2. RULE EVAL: evaluate each rule against current features → list of (rule_id, fires, confidence)
  3. CONFLICT RESOLUTION: if multiple rules fire with conflicting direction, apply policy
     (priority order, unanimity required, highest-confidence wins)
  4. POSITION DECISION: resolve into target (direction, size)
  5. STAKE: rule-specific stake_fraction × equity
  6. EMIT: StrategyInstruction.TRADE with target_position_units
```

## Rule registry (versioned artifact)

Each strategy instance subscribes to a `rule_registry_ref` — a versioned YAML catalog:

```yaml
# Example: tradfi-spy-ta-v3.yaml
rules:
  - rule_id: SPY_MEAN_REV_ENTRY
    description: "Enter long when z-score < -2 and volume > 1.2x avg"
    when:
      - feature: z_score_20d
        op: less_than
        value: -2.0
      - feature: volume_ratio_20d
        op: greater_than
        value: 1.2
    emit:
      direction: LONG
      stake_fraction_of_equity: 0.02
      hold_until: z_score_20d >= -0.5 # exit rule
      max_hold_bars: 20
  - rule_id: SPY_MOMENTUM_ENTRY
    description: "Enter long on 20d breakout with volume confirmation"
    when:
      - feature: close
        op: greater_than
        value_ref: rolling_high_20d
      - feature: volume_ratio_5d
        op: greater_than
        value: 1.3
    emit:
      direction: LONG
      stake_fraction_of_equity: 0.015
      hold_until: close < sma_10
      max_hold_bars: 40
```

## Supported venues + instrument types

**Coverage matrix:** See
[`../category-instrument-coverage.md § 3. RULES_DIRECTIONAL_CONTINUOUS`](../category-instrument-coverage.md#3-rules_directional_continuous)
for the authoritative TradFi / CeFi / DeFi venue × instrument coverage.

## Expression options

- spot, perp, future, options (delta-1 expression)

## Hold policies

- HOLD_UNTIL_FLIP — hold until exit rule fires
- Time-box (via `max_hold_bars`) — force exit after N bars if no exit rule fires
- Rule-specific (each rule defines its own exit condition)

## Config schema (illustrative)

```yaml
rule_registry_ref: tradfi-spy-ta-v3
feature_group_refs:
  - tradfi-equity-candles-5m@v2
  - tradfi-equity-volume@v2
venues: [IBKR]
instruments: [SPY]
timeframe: 5m
share_class: USD
conflict_resolution: priority_order # or unanimity / highest_confidence
execution_policy_ref: tradfi-equity-default-v3
max_concurrent_rules_fired: 3
```

## Execution semantics

- Rule fires → emit TRADE with target_position_units
- Rule flips → emit TRADE with target_position_units = 0 (or opposite direction)
- Time-box expiry → emit TRADE with target_position_units = 0

## P&L attribution

- Per rule: track which rule fired for each position; attribute P&L to rule_id
- Per strategy instance: aggregate across rules
- Execution alpha vs benchmark: per-fill

## Risk profile

- Drawdowns: 5-15% depending on asset class
- Typical Sharpe: 0.5-1.5 (lower than best ML, but more stable)
- Kill switches: daily-loss limit, rule hit-rate collapse (rule's rolling hit rate < threshold → auto-retire)

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    # Rescale all active rule-positions to new equity proportion
    return [
        TRADE(target_position_units=new_size(rule), instrument=rule.instrument)
        for rule in self.active_rules
    ]
```

## Example instances

```
RULES_DIRECTIONAL_CONTINUOUS@ibkr-spy-5m-usd-prod
RULES_DIRECTIONAL_CONTINUOUS@ibkr-eurusd-5m-usd-prod
RULES_DIRECTIONAL_CONTINUOUS@ibkr-cl-futures-1d-usd-prod        (daily mean-reversion)
RULES_DIRECTIONAL_CONTINUOUS@ibkr-cl-regime-1h-usd-prod          (regime-switching rules)
RULES_DIRECTIONAL_CONTINUOUS@binance-btc-5m-usdt-prod
RULES_DIRECTIONAL_CONTINUOUS@hyperliquid-eth-1h-usdt-prod
```

## Migration from legacy

| Legacy                                                          | Notes                                                                              |
| --------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `cefi/momentum.md`                                              | TA-based momentum rules                                                            |
| `cefi/mean-reversion.md`                                        | TA-based mean-rev rules (if ML-based, use ML_DIRECTIONAL_CONTINUOUS)               |
| Code: `momentum.py`, `mean_reversion.py`, `commodity_regime.py` | Collapse into `RulesDirectionalContinuousEngine` with different rule_registry_refs |

## Not in this archetype

- **ML-driven signals** (even if the rule wraps a model output) — `ML_DIRECTIONAL_CONTINUOUS`
- **Event-settled rule triggers** (sports, prediction markets) — `RULES_DIRECTIONAL_EVENT_SETTLED`
- **Cointegrated pair z-score trades** — `STAT_ARB_PAIRS_FIXED` (different archetype so pair-specific risk gates fire)
- **Basis-carry with delta-neutral hedge** — `CARRY_BASIS_PERP`
- **Calendar-event reaction rules** (FOMC surprise direction) — `EVENT_DRIVEN`

## See also

- Family: [rules-directional.md](../families/rules-directional.md)
- Rule registry as artifact:
  [../../../04-architecture/artifact-versioning.md](../../../04-architecture/artifact-versioning.md)
- Event-settled variant: [rules-directional-event-settled.md](rules-directional-event-settled.md)
