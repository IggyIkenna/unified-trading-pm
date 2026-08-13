---
doc_type: codex-ssot
title: "Archetype: `ML_DIRECTIONAL_CONTINUOUS`"
summary: >-
  `ML_DIRECTIONAL_CONTINUOUS` archetype — consumes ML P(up)/P(down) predictions, calibrates, computes edge =
  calibrated_P − implied_P, gates on `confidence_threshold` and `min_edge_threshold`, sizes via fractional Kelly, and
  emits target-state TRADEs across spot/perp/future/options expressions; `HOLD_UNTIL_FLIP` default.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [ml, strategy, kelly, live-trading, execution]
related:
  [
    ../families/ml-directional.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md,
    ../axes/expression.md,
    ../axes/hold-policy.md,
    ../cross-cutting/benchmark-fills.md,
  ]
created: 2026-04-17
authoritative_for: [ML_DIRECTIONAL_CONTINUOUS archetype specification]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/cefi/ml-directional.md,
    /codex/09-strategy/_archived_pre_v2/cefi/momentum.md,
    /codex/09-strategy/_archived_pre_v2/cross-cutting/ml-pipeline.md,
    /codex/09-strategy/_archived_pre_v2/tradfi/ml-directional.md,
    /codex/09-strategy/_archived_pre_v2/tradfi/tradfi-momentum.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-ml-lean.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md,
    /codex/09-strategy/architecture-v2/archetypes/rules-directional-continuous.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: ML_DIRECTIONAL_CONTINUOUS
family: ML_DIRECTIONAL
venue_universe: [BINANCE, OKX, BYBIT, HYPERLIQUID, DERIBIT, IBKR, CME, CBOE]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 150
  min_sla_tier: premium
---

# Archetype: `ML_DIRECTIONAL_CONTINUOUS`

> **Family:** [ML Directional](../families/ml-directional.md) **Settlement model:** Continuous P&L, positions can be
> closed any time. **Code module (target):** `strategy-service/engine/strategies/ml_directional_continuous_engine.py`

## What it does

Consumes probability predictions from an ML model (per direction, per instrument, at some frequency), compares to
market-implied probability, and emits target-state trade instructions when edge + confidence thresholds are met.

## Token / position flow

```
Start: BANKROLL in share_class currency (e.g., USDT, ETH, USD)

On signal tick (e.g., every N minutes or on each new candle):
  1. MODEL INFERENCE: ml-inference-service returns P(up), P(down), confidence
  2. CALIBRATION: apply saved calibration function → calibrated P
  3. IMPLIED FROM MARKET: compute from current venue mid + venue-specific adjustment
                          (funding, fees baked in)
  4. EDGE COMPUTE: edge = calibrated_P - implied_P
  5. CONFIDENCE GATE: skip if confidence < threshold
  6. EDGE GATE: skip if |edge| < min_edge_threshold
  7. STAKE SIZE: position = equity × kelly_fraction × confidence × sign(edge) / mid_price
  8. TARGET STATE: emit StrategyInstruction.TRADE with target_position_units=position
  9. EXECUTION: reconciles current → target via venue-appropriate algo
```

Position held until signal reverses (HOLD_UNTIL_FLIP) or time-box expires (SAME_CANDLE_EXIT if configured).

## Supported venues + instrument types

**Coverage matrix:** See
[`../category-instrument-coverage.md § 1. ML_DIRECTIONAL_CONTINUOUS`](../category-instrument-coverage.md#1-ml_directional_continuous)
for the authoritative table (venues × instrument types × status × go-live dates). Multi-venue SOR enabled where the
instrument is fungible across venues (cross-CEX perp).

## Expression options

- `spot` — buy/sell actual asset
- `perp` — perpetual future (default for crypto directional)
- `future` — dated future (TradFi index, commodity)
- `atm_call` — options ATM call as delta-1 expression
- `25d_call` — options 25-delta call (more gamma, less delta)
- `synthetic` — long call + short put at same strike (fully replicates delta-1 without linear-instrument funding)
- `auto` — execution chooses based on cost/liquidity

## Hold policies supported

- `HOLD_UNTIL_FLIP` (default) — position held until signal reverses
- `SAME_CANDLE_EXIT` — time-boxed exit at end of each candle window
- `ONE_SHOT` — enter + exit within a single candle; no holding

## Config schema (illustrative)

```yaml
model_id: CRYPTO_BTC_CATBOOST_V4
calibration_fn_ref: platt_v2
feature_group_refs:
  - cefi-crypto-candles-5m@v3
  - cefi-crypto-orderbook-depth@v2
timeframe: 5m
confidence_threshold: 0.58
min_edge_threshold: 0.01 # 1% edge after calibration
kelly_fraction: 0.25
max_position_pct_of_equity: 0.30
venues:
  - HYPERLIQUID
expression_preference: perp
hold_policy: HOLD_UNTIL_FLIP
execution_policy_ref: cefi-perp-default-v4
risk_constraints:
  max_adverse_move_atr_multiple: 5
  daily_loss_stop_pct: 0.05

# Leverage + net-delta controls (universal per StrategyInstanceDefinition; Stream D 2026-05-07):
target_leverage: 1.0 # [1, 10]; hard-clamped by per-instrument vol cap at entry
target_net_delta: 0.0 # net directional delta (0 = delta-neutral; model drives direction)
max_underlying_move_pct: 3.0 # vol-cap clamp: skip entry if realized move > X% in 1h window
instrument_volatility_registry_lookup: true # use realized_vol_20 (1h candles) from FSS
```

## Execution semantics

- Instructions emitted as `TRADE` action with target_position_units
- Execution-service picks algo per execution_policy_ref rule table
- Default for NORMAL urgency: PASSIVE_AGGRESSIVE_HYBRID over the candle timeframe
- Fill stream back → engine updates current_position → next tick reconciles
- Benchmark fill in batch mode: fill at signal_price at signal_ts (zero exec alpha)

## P&L attribution (per fill + rollup)

- **Directional P&L**: (exit_price - entry_price) × position_units × direction
- **Funding P&L** (perp): funding_rate × position_notional × holding_time
- **Fees**: explicit (commission, maker/taker fee per fill)
- **Execution alpha**: fill_price - benchmark_price per fill; summed over strategy life

## Risk profile

- Drawdown characteristic: 8-15% on crypto perps (moderate directional vol); lower on equities (3-8%)
- Typical Sharpe: 0.8-2.5 depending on model quality
- Kill switches: rapid price move (5× ATR), calibration breach (prediction error exceeds training residual), venue
  outage, daily-loss limit

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    if self.has_active_signal:
        new_target = (
            self.signal.direction
            × self.equity
            × self.config.kelly_fraction
            × self.signal.confidence
            / self.current_mid
        )
        emit TRADE with target_position_units=new_target
```

## Example instances

```
CEFI_ML_DIRECTIONAL@hyperliquid-btc-5m-usdt-prod
CEFI_ML_DIRECTIONAL@binance-eth-1h-usdt-prod
CEFI_ML_DIRECTIONAL@deribit-btc-atm-call-5m-usdt-prod   (options expression)
CEFI_ML_DIRECTIONAL@hyperliquid-btc-5m-eth-prod          (ETH share class)
CEFI_ML_DIRECTIONAL@multi-cex-perp-btc-5m-usdt-prod      (multi-venue SOR)
TRADFI_ML_DIRECTIONAL@ibkr-spy-5m-usd-prod
TRADFI_ML_DIRECTIONAL@cme-es-1h-usd-prod
TRADFI_ML_DIRECTIONAL@ibkr-eurusd-5m-usd-prod
```

## Migration from legacy

| Legacy                                                                                                                       | Notes                                                                                              |
| ---------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `tradfi/ml-directional.md`                                                                                                   | Exact match; TradFi-specific content becomes config                                                |
| `cefi/mean-reversion.md` (ML-based variants)                                                                                 | If signal is ML-derived, this is the archetype                                                     |
| Code: `tradfi_ml_swing_strategy.py`, `tradfi_ml_spy.py`, `tradfi_ml_fx.py`, `tradfi_ml_oil.py`, `tradfi_ml_directional_*.py` | All collapse into `MLDirectionalContinuousEngine`                                                  |
| Code: `options_ml_delta_btc_deribit.py`, `options_ml_delta_spy_cboe.py`                                                      | Delta-expression of ML directional (options as delta-1)                                            |
| Code: `options_ml_strike_btc_deribit.py`                                                                                     | Depends: if strike-selection is about directional view → here; if vol-driven → VOL_TRADING_OPTIONS |

## Not in this archetype

- **Event-settled ML** (sports value betting, prediction markets) — `ML_DIRECTIONAL_EVENT_SETTLED`
- **Rule-based signals** (z-score, mean reversion) — `RULES_DIRECTIONAL_CONTINUOUS`
- **Pair / basket relative value** — `STAT_ARB_PAIRS_FIXED` or `STAT_ARB_CROSS_SECTIONAL`
- **Calendar-driven directional bets** (FOMC / CPI reaction) — `EVENT_DRIVEN`
- **Funding-rate capture with delta-neutral hedging** — `CARRY_BASIS_PERP`
- **Options delta-1 expressions where the alpha is vol, not direction** — `VOL_TRADING_OPTIONS`

## See also

- Family: [ml-directional.md](../families/ml-directional.md)
- Paired event-settled variant: [ml-directional-event-settled.md](ml-directional-event-settled.md)
- Expression axis: [../axes/expression.md](../axes/expression.md)
- Hold-policy: [../axes/hold-policy.md](../axes/hold-policy.md)
- Benchmark fills: [../cross-cutting/benchmark-fills.md](../cross-cutting/benchmark-fills.md)
