---
scope: [engineer, admin]
---

# Event-Driven Macro Strategy

Cross-domain strategy that uses economic calendar events as the PRIMARY trade trigger rather than a supplementary
feature. Consumes features-calendar-service outputs (FOMC, CPI, NFP, earnings, ECB, GDP) and positions around event
windows using ML-predicted impact direction and magnitude.

## Thesis

Macro events create predictable volatility spikes and directional dislocations across asset classes. By making calendar
features the dominant signal (not just another input), the strategy captures two distinct alpha sources:

1. **Pre-event positioning** -- ML predictions of event impact allow entering positions N candles before the event when
   implied vol is still building.
2. **Post-event momentum** -- After the event release, directional momentum persists for a known decay period. The
   strategy rides this momentum with confidence-scaled sizing.

## Cross-Domain Coverage

| Domain | Instrument Example       | Event Sensitivity                                          |
| ------ | ------------------------ | ---------------------------------------------------------- |
| CeFi   | BINANCE-FUTURES BTC-USDT | FOMC/CPI/NFP -> BTC vol spike 2-3x, directional on USD     |
| TradFi | NASDAQ SPY               | FOMC/CPI/NFP/earnings -> equity reaction, structured decay |
| TradFi | CME 6E (Euro FX)         | ECB/NFP -> USD pairs directional                           |
| TradFi | NYMEX CL (Crude Oil)     | GDP/ISM/retail sales -> commodity demand signal            |

## Event Types and Impact Profiles

Each event type has a configurable impact profile: `(vol_multiplier, directional_bias_weight, decay_candles)`.

| Event          | Default Vol Mult | Bias Weight | Decay (candles) | Typical Impact                              |
| -------------- | ---------------- | ----------- | --------------- | ------------------------------------------- |
| FOMC           | 2.5              | 0.80        | 24              | Rate decisions -> BTC vol, USD pairs move   |
| CPI            | 2.0              | 0.70        | 12              | Inflation -> bond yields -> equity/crypto   |
| NFP            | 1.8              | 0.60        | 8               | Jobs data -> USD strength/weakness          |
| ECB            | 2.0              | 0.70        | 16              | European rates -> EUR/USD, equity spillover |
| EARNINGS       | 3.0              | 0.90        | 6               | Per-stock -> concentrated equity movement   |
| GDP            | 1.5              | 0.50        | 8               | Growth signal -> broad market               |
| PPI            | 1.3              | 0.40        | 6               | Producer prices -> forward CPI signal       |
| RETAIL_SALES   | 1.4              | 0.50        | 6               | Consumer demand -> equity + USD             |
| ISM            | 1.3              | 0.40        | 4               | Manufacturing -> growth proxy               |
| JOBLESS_CLAIMS | 1.1              | 0.30        | 4               | Weekly labour -> modest USD impact          |

Overrides per strategy instance via `event_config.event_impacts` in YAML.

## Signal Pipeline

```
features-calendar-service
  |
  v
[event_type, event_countdown_candles, event_surprise_zscore, ...]
  |
  v
EventDrivenMacroStrategy.generate_signal()
  |
  +-- 1. ML swing predictions (swing_high/swing_low) -> direction
  +-- 2. Event phase gating (pre_event / post_event / no_event)
  +-- 3. Position sizing: scale with ML confidence + event countdown
  +-- 4. Vol multiplier from event type
  |
  v
Signal dict (direction, confidence, event_phase, position_scale, vol_multiplier)
```

## Position Sizing Logic

- **No event nearby**: no signal emitted (strategy sits out entirely).
- **Pre-event**: ramp from 60% to 100% of confidence-scaled size as countdown progresses. Within 1 candle of event: cut
  to 50% (vol spike risk).
- **Post-event**: full confidence-scaled size.

All sizes capped by `risk_config.max_position_size_usd`.

## Configuration

Two factory functions with corresponding YAML configs:

| Factory                              | Config YAML               | Domain | Instrument       |
| ------------------------------------ | ------------------------- | ------ | ---------------- |
| `create_event_macro_crypto_strategy` | `event_macro_crypto.yaml` | CeFi   | BTC-USDT Binance |
| `create_event_macro_tradfi_strategy` | `event_macro_tradfi.yaml` | TradFi | SPY NASDAQ       |

Registered in `batch_utils.py` as `EVENT_MACRO_CRYPTO` (CEFI) and `EVENT_MACRO_TRADFI` (TRADFI).

## Execution Modes

- **SCE** (Same Candle Exit): enter and exit within the same candle -- captures the event-window spread.
- **HUF** (Hold Until Flip): hold position until ML signal flips direction -- rides post-event momentum.

Crypto default: HUF (events create sustained trends in crypto). TradFi default: SCE (more structured, faster mean
reversion).

## Feature Subscriptions

Calendar features from features-calendar-service:

- `event_type` -- enum of current/next event
- `event_countdown_candles` -- candles until event (negative = post-event)
- `event_surprise_zscore` -- historical surprise magnitude
- `event_consensus_deviation` -- actual vs consensus
- `event_implied_vol_ratio` -- current IV vs pre-event IV
- `event_ml_impact_pred` -- ML-predicted directional impact
- `event_ml_direction_conf` -- ML confidence for direction
- `event_phase` -- pre_event / post_event / no_event

Plus domain-specific: `funding_rate`, `open_interest` (crypto); `macd`, `rsi`, `atr` (TradFi).

## Risk Controls

- Stop loss / take profit per factory (crypto wider: 2.5%/5%; TradFi tighter: 1.5%/3%)
- Max drawdown cap (crypto 10%, TradFi 8%)
- Position scale automatically reduces near event boundary (uncertainty spike)
- No signal emitted outside event windows -- inherent risk control

## Source Files

- Strategy: `strategy_service/engine/strategies/event_driven_macro.py`
- Configs: `strategy_service/configs/event_macro_crypto.yaml`, `strategy_service/configs/event_macro_tradfi.yaml`
- Registration: `strategy_service/cli/handlers/batch_utils.py`
