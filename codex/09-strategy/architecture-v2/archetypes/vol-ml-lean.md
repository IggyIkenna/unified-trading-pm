---
doc_type: codex-ssot
title: "Archetype: `VOL_ML_LEAN`"
summary:
  "Archetype spec for `VOL_ML_LEAN` — a rolling random forest forecasts 5d realized vol and the predicted-RV vs IV gap
  directs and sizes delta-hedged straddle/strangle positions, with rolling retrain and an OOS-accuracy guard;
  Deribit/OKX/CBOE."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, ml, features, delta-hedge]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-arb-rv-iv.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-continuous.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-straddle.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_ML_LEAN archetype spec"]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/tradfi/options-ml.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-arb-rv-iv.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-straddle.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_ML_LEAN
family: VOL_TRADING
venue_universe: [DERIBIT, OKX_OPTIONS, CBOE]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 500
  min_sla_tier: standard
---

# Archetype: `VOL_ML_LEAN`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Continuous — vol positions sized and
> directioned by rolling ML forecast; positions rolled at expiry. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_ml_lean_engine.py`

## What it does

Uses a trained machine learning model to forecast near-term realized volatility, then tilts option position sizing and
direction based on the model's prediction versus current implied vol. The core signal is the gap between model-predicted
RV and market-implied IV: when the model forecasts RV below current IV, the archetype sells vol (short straddle or
strangle); when it forecasts RV above IV, it buys vol (long straddle). The model is a rolling random forest trained on
vol features — lagged realized vol across windows, VIX or crypto IV term structure, perp funding rates, and options
order flow imbalance. Position sizing scales with model confidence (prediction margin over IV) and model accuracy on
recent out-of-sample windows. The archetype re-trains the model on a rolling basis to avoid regime staleness.

## Token / position flow

```
1. FEATURE CONSTRUCTION (per inference cycle):
   - Lagged RV: RV_1d, RV_5d, RV_10d, RV_20d (annualised, close-to-close)
   - IV term structure: IV_7d, IV_14d, IV_30d ATM from surface fitter
   - IV-RV spread at each tenor
   - Perp funding rate (1h EMA and 24h rolling mean)
   - Options order flow: put/call volume ratio, net vega flow (last 4h)
   - Underlying return features: momentum_1h, momentum_4h, momentum_24h
   - Macro: VIX spot and 1m futures (for BTC/ETH cross-asset signal)

2. MODEL INFERENCE:
   - Load trained model from model_registry_ref (random forest, n_estimators=200)
   - Predict: predicted_rv_5d (5-day forward realized vol, annualised)
   - Compute prediction_margin = IV_7d − predicted_rv_5d (positive → sell vol signal)

3. SIGNAL GENERATION:
   - prediction_margin > sell_threshold_vp AND model_confidence > min_confidence:
       → direction = SHORT_VOL; size_multiplier = f(prediction_margin)
   - prediction_margin < -buy_threshold_vp AND model_confidence > min_confidence:
       → direction = LONG_VOL; size_multiplier = f(|prediction_margin|)
   - |prediction_margin| < flat_zone_vp: → no position (flat zone)
   - model_confidence < min_confidence → suppress all signals

4. POSITION SIZING:
   - base_vega_notional_usd × size_multiplier (capped at max_vega_notional_usd)
   - size_multiplier = tanh(prediction_margin / scaling_factor) × max_multiplier

5. ENTRY: ATOMIC TRADE — straddle or strangle per direction and expression_config
   - SHORT_VOL: sell straddle / strangle
   - LONG_VOL: buy straddle / strangle

6. HOLD + REHEDGE:
   - Delta-hedge via underlying perp when |net_delta| > delta_hedge_band_pct
   - Re-run inference every inference_interval_min; update position direction + size if signal flips
   - On signal flip: ATOMIC close current position + ATOMIC open new direction

7. MODEL RETRAINING:
   - Rolling retrain every retrain_interval_days on last training_window_days of data
   - Validate on OOS window before deploying new model version
   - If OOS accuracy < min_oos_accuracy: keep prior model; alert operator

8. EXIT:
   - Signal exits flat zone: close position
   - Stop loss: P&L < -stop_loss_pct × initial_premium
   - Model drift alert: OOS accuracy degraded; operator review required
   - Roll at roll_before_expiry_dte DTE
```

## Entry conditions + signal

- `|prediction_margin| > threshold_vp` AND `model_confidence > min_confidence` (random forest probability of correct
  direction class)
- Model OOS accuracy on last eval_window_days >= min_oos_accuracy (e.g. 0.58 directional accuracy)
- IV within normal range: suppress if IV > iv_regime_upper_cap (model not trained on extremes)
- No binary event within tenor unless event_mode_enabled = true (model has event features)

## Risk management

- Short-vol stop: vega loss > stop_loss_vega_pct × initial_premium
- Long-vol stop: cumulative theta bleed > max_theta_bleed_pct without signal strengthening
- Model staleness guard: if retrain fails or OOS accuracy < floor, halt signal generation
- Delta hedge continuously; same band as `VOL_CARRY`
- Position flip (signal reversal) uses ATOMIC close-then-open to avoid naked intermediate state
- Ensemble fallback: if primary model unavailable, fall back to rule-based IV-RV spread (vol_arb_rv_iv logic)

## Config parameters

- `underlying`: BTC | ETH | SPX (etc.)
- `venue`: DERIBIT | OKX_OPTIONS | CBOE
- `model_registry_ref`: model version key for feature-service model registry
- `inference_interval_min`: how often to re-run inference and potentially resize (e.g. 60)
- `retrain_interval_days`: rolling retrain cadence (e.g. 7)
- `training_window_days`: lookback for model training (e.g. 365)
- `min_oos_accuracy`: minimum directional accuracy on OOS validation (e.g. 0.57)
- `sell_threshold_vp`: prediction_margin threshold for short vol entry (e.g. 3.0)
- `buy_threshold_vp`: |prediction_margin| threshold for long vol entry (e.g. 3.0)
- `flat_zone_vp`: no-trade zone around zero prediction_margin (e.g. 1.5)
- `min_confidence`: minimum model confidence score (e.g. 0.60)
- `max_multiplier`: max position size multiplier (e.g. 2.0)
- `scaling_factor`: tanh scaling for size_multiplier (e.g. 5.0 vol points)
- `max_vega_notional_usd`: hard cap on vega exposure
- `target_dte_entry`: options DTE at entry (e.g. 14)
- `roll_before_expiry_dte`: 3
- `delta_hedge_band_pct`: rehedge threshold
- `stop_loss_vega_pct`: short vol stop (e.g. 0.75)
- `max_theta_bleed_pct`: long vol stop (e.g. 0.40)
- `expression`: straddle | strangle
- `iv_regime_upper_cap`: suppress entry if ATM IV above this (e.g. 1.20 = 120%)

## When to use / market regime

- **Best regime**: markets with persistent IV-RV autocorrelation patterns; periods where order flow and funding
  imbalances reliably predict near-term realized vol
- **Avoid**: extreme novelty regimes (black-swan events, exchange hacks) where the model is out of distribution; also
  avoid during data gaps that corrupt feature windows
- **Model maintenance**: requires regular monitoring — retrain validation, OOS accuracy tracking, and feature drift
  alerting are operational requirements, not optional
- **Asset fit**: BTC, ETH (rich feature set); cross-asset features (VIX) require TradFi data pipeline

## Example instances

```
VOL_ML_LEAN@deribit-btc-straddle-14dte-usdt-prod
VOL_ML_LEAN@deribit-eth-straddle-14dte-usdt-prod
VOL_ML_LEAN@cboe-spx-straddle-weekly-usd-prod
```

## Not in this archetype

- Rule-based IV-RV spread trade (threshold-entry, no ML model, no rolling retrain) → [`VOL_ARB_RV_IV`](vol-arb-rv-iv.md)
- Structural short-vol carry (always short vol for theta, no model signal required) → [`VOL_CARRY`](vol-carry.md)
- ML model predicting underlying direction (alpha is price, not realized vol) →
  [`ML_DIRECTIONAL_CONTINUOUS`](ml-directional-continuous.md)
- ATM straddle sized for a specific binary event catalyst (event calendar, not model forecast) →
  [`VOL_STRADDLE`](vol-straddle.md)

## See also

- RV vs IV arb (rule-based version): [vol-arb-rv-iv.md](vol-arb-rv-iv.md)
- Vol carry: [vol-carry.md](vol-carry.md)
- ML directional (underlying, not vol): [ml-directional-continuous.md](ml-directional-continuous.md)
- Family: [vol-trading.md](../families/vol-trading.md)
