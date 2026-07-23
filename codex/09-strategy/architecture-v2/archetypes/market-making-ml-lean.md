---
doc_type: codex-ssot
title: "Archetype: `MARKET_MAKING_ML_LEAN`"
summary: >-
  `MARKET_MAKING_ML_LEAN` archetype — extends inventory-skew MM with a gradient-boosting model predicting 1-5min
  direction; tilts quotes by `ml_lean_factor` × direction_signal (capped at `max_lean_pct`) on top of inventory skew;
  guards on live Brier score (`max_live_brier_score` → disable lean) and feature NaN; daily retrain.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [market-making, ml, inventory-skew, book-microstructure, clob]
related:
  [
    ../families/market-making.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-inventory-skew.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-passive-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-queue-microstructure.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-continuous.md,
  ]
created: 2026-05-19
authoritative_for: [MARKET_MAKING_ML_LEAN archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/market-making-inventory-skew.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-passive-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-queue-microstructure.md,
    /codex/09-strategy/architecture-v2/families/market-making.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: MARKET_MAKING_ML_LEAN
family: MARKET_MAKING
venue_universe: [BINANCE, OKX, BYBIT, HYPERLIQUID, DERIBIT]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 30
  min_sla_tier: premium
---

# Archetype: `MARKET_MAKING_ML_LEAN`

> **Family:** [Market Making](../families/market-making.md) **Settlement model:** Continuous — ML model predicts
> short-term direction; quotes tilted asymmetrically on each refresh. **Code module (target):**
> `strategy-service/engine/strategies/v2/market_making/ml_lean_engine.py`

## What it does

ML-guided market making extends the inventory-skew framework by adding a short-term directional prediction layer. A
gradient boosting model trained on order book features, trade flow imbalance, and recent momentum predicts the 1-5
minute price direction with a calibrated probability. This prediction is used to tilt the bid/ask quotes: if the model
predicts upward movement, the ask is narrowed (more competitive sell) and the bid is widened (less competitive buy) —
monetising the informational edge without taking outright directional positions. The ML lean is combined with inventory
skew so that both signal sources contribute to quote placement.

## Token / position flow

```
1. FEATURE COMPUTATION (per quote refresh):
   Order book features:
   - bid_ask_imbalance = (bid_size_5 - ask_size_5) / (bid_size_5 + ask_size_5)
   - book_pressure_ratio = bid_depth_bps_10 / ask_depth_bps_10
   - top_of_book_size_ratio = best_bid_size / best_ask_size
   Trade flow features:
   - trade_imbalance_30s = (buy_vol_30s - sell_vol_30s) / total_vol_30s
   - trade_count_30s, avg_trade_size_30s
   Momentum:
   - price_return_1m, price_return_5m, price_return_15m

2. ML PREDICTION:
   - model.predict_proba(features) → p_up, p_down, p_flat
   - direction_signal = p_up - p_down  ∈ [-1, 1]
   - Only act if |direction_signal| > min_signal_threshold

3. QUOTE TILT (combined ML + inventory):
   - reservation_price = mid + ml_lean_factor × direction_signal × base_half_spread
   - Apply inventory skew on top of reservation_price (same as INVENTORY_SKEW)
   - Final quotes: post_bid = reservation_price - adjusted_half_spread
                   post_ask = reservation_price + adjusted_half_spread

4. QUOTE LIFECYCLE: identical to MARKET_MAKING_INVENTORY_SKEW

5. MODEL REFRESH:
   - Inference: per quote cycle (every refresh_interval_ms)
   - Retrain: daily on last 7d of order book snapshots + labelled outcomes
   - Feature drift monitor: alert if feature distribution shifts > drift_threshold

6. EXIT: same inventory hard cap + daily stop loss as inventory skew archetype
```

## Entry conditions + signal

- ML model loaded and passing calibration check (brier_score < max_brier_score, default 0.25)
- Feature pipeline producing valid values (no NaN in input features)
- `|direction_signal| > min_signal_threshold` for lean to apply (otherwise fall back to symmetric quotes)
- Same spread + latency conditions as passive spread

## Risk management

- ML model degradation kill switch: if live brier score > max_live_brier_score over last 1h, disable ML lean and fall
  back to pure inventory-skew quoting
- Feature NaN guard: any NaN in model input → skip ML lean this cycle; log alert
- Max lean magnitude: ml_lean_factor × max_direction_signal capped at max_lean_pct of base spread (prevents ML from
  moving quote to adverse side of book)
- Inventory hard cap: same as inventory-skew archetype (market-order exit if breached)
- Daily P&L stop: daily_stop_loss_usd

## Config parameters

- `venue`: target exchange
- `instrument`: instrument ID
- `ml_model_ref`: model artifact reference (GCS path or model registry ID)
- `ml_lean_factor`: amplification of ML signal into quote offset (default 0.3)
- `min_signal_threshold`: minimum |direction_signal| to apply ML lean (default 0.1)
- `max_lean_pct`: cap on ML quote offset as fraction of base_half_spread (default 0.5)
- `max_brier_score`: model calibration threshold for startup check (default 0.25)
- `max_live_brier_score`: live performance threshold; disable lean if exceeded (default 0.28)
- `feature_lookback_seconds`: rolling window for trade flow features (default 30)
- `model_retrain_cadence`: how often to retrain model on new data (default daily)
- `drift_threshold`: feature distribution shift threshold for alert (default 0.20)
- `half_spread_ticks`: base half-spread before ML + inventory adjustments (default 1)
- `skew_factor`: inventory skew amplification (default 0.4)
- `gamma`: Avellaneda-Stoikov risk-aversion for inventory (default 0.1)
- `order_size_base`: base order size per side
- `max_inventory_base`: inventory target for skew maximisation
- `inventory_hard_cap`: forced market-order exit threshold
- `refresh_interval_ms`: quote refresh cadence (default 200)
- `daily_stop_loss_usd`: daily loss limit (default 750)
- `share_class`: USDT | USD
- `execution_policy_ref`: mm-ml-v1

## When to use / market regime

- **Use when**: ML model shows demonstrated predictive edge on the target instrument; order book features are stable and
  informative; instrument has sufficient trade flow to feed the model with quality signal
- **Best regime**: high-activity markets with consistent order flow patterns; microstructure predictable enough for
  short-horizon models (major CEX spot markets, liquid perp markets)
- **Avoid**: very thin order books where features are noisy; new instruments with insufficient training data;
  high-volatility regime where 1-5 minute prediction is dominated by macro events
- **Upgrade path from**: MARKET_MAKING_INVENTORY_SKEW — add ML layer when inventory-skew P&L plateaus

## Example instances

```
MARKET_MAKING_ML_LEAN@binance-btc-usdt-spot-mm-prod
MARKET_MAKING_ML_LEAN@okx-eth-usdt-perp-mm-prod
MARKET_MAKING_ML_LEAN@hyperliquid-sol-usdt-perp-mm-prod
```

## Not in this archetype

- Symmetric spread with no ML or skew → [`MARKET_MAKING_PASSIVE_SPREAD`](market-making-passive-spread.md)
- Inventory-only skew without ML prediction layer → [`MARKET_MAKING_INVENTORY_SKEW`](market-making-inventory-skew.md)
- Queue-position and VPIN-aware posting decision →
  [`MARKET_MAKING_QUEUE_MICROSTRUCTURE`](market-making-queue-microstructure.md)
- Outright directional position from a strong ML signal → [`ML_DIRECTIONAL_CONTINUOUS`](ml-directional-continuous.md)
- DEX concentrated-liquidity LP fee capture → [`DEFI_LP_CONCENTRATED`](defi-lp-concentrated.md)

## See also

- Family: [market-making.md](../families/market-making.md)
- Simpler inventory-skewed variant: [market-making-inventory-skew.md](market-making-inventory-skew.md)
- Queue position model: [market-making-queue-microstructure.md](market-making-queue-microstructure.md)
