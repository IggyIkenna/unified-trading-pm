---
doc_type: codex-ssot
title: "Archetype: `EVENT_DRIVEN`"
summary: >-
  `EVENT_DRIVEN` archetype — schedules positioning around known scheduled events (FOMC / CPI / NFP / OPEC / EIA /
  earnings); computes surprise = (realized − consensus) / σ, emits directional TRADEs when `|surprise|` >
  `min_surprise_sigma` (default 1.5) and flattens at `exit_after_minutes`; per-event notional cap + post-event vol-exit.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [event-driven, strategy, macro, tradfi, ml]
related:
  [
    ../families/event-driven.md,
    ../category-instrument-coverage.md,
    ../cross-cutting/execution-policies.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md,
  ]
created: 2026-04-17
authoritative_for: [EVENT_DRIVEN archetype specification]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/cross-cutting/event-driven-macro.md,
    /codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md,
    /codex/09-strategy/architecture-v2/families/event-driven.md,
    plans/epics/sports_master.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: EVENT_DRIVEN
family: EVENT_DRIVEN
venue_universe: [BINANCE, OKX, HYPERLIQUID, IBKR, CME]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `EVENT_DRIVEN`

> **Family:** [Event-Driven](../families/event-driven.md) **Settlement model:** Time-bounded ONE_SHOT or short-hold
> window around a scheduled event. **Code module (target):** `strategy-service/engine/strategies/event_driven_engine.py`

## What it does

Schedules positioning around known external events (FOMC, CPI, NFP, OPEC, earnings, EIA). Consumes consensus forecast +
realized release data, computes surprise, emits directional trades in targeted instruments, then flattens at a
configured post-event window close.

## Token / position flow

```
Schedule: event calendar (release_ts, consensus, target_instruments) loaded from event_calendar_ref

T - pre_event_minutes:
  Pre-position if pre_event_signal fires (e.g., historical pattern on this event type)

T - release_second:
  Capture realized value from official feed
  Compute surprise = (realized - consensus) / σ_forecasts

Event fire (|surprise| > threshold):
  Direction model maps surprise → expected direction per instrument
  EMIT TRADE instructions with target_position_units across target_instruments
  Pre-flight check with urgency=HIGH or EMERGENCY
  Execution uses MARKET orders typically (speed priority)

T + event_window_minutes:
  Emit TRADE with target=0 for all positions (time-box exit)

T + vol_normalize:
  Optional: hold beyond time-box if realized vol hasn't normalized; alternatively
  exit at time-box regardless
```

**Venue × instrument coverage:** See
[`../category-instrument-coverage.md § 15. EVENT_DRIVEN`](../category-instrument-coverage.md#15-event_driven). The table
below enumerates eligible events — orthogonal to venue coverage.

## Supported events

| Event category  | Specific events                                                              | Instruments affected                               |
| --------------- | ---------------------------------------------------------------------------- | -------------------------------------------------- |
| Macro US        | FOMC rate decision, FOMC minutes, CPI, PPI, PCE, NFP, GDP, retail sales, ISM | US equities, US rates, USD FX, crypto (correlated) |
| Macro EU        | ECB rate decision, HICP, German IFO                                          | EUR FX, European equities                          |
| Macro UK        | BoE rate decision, UK CPI                                                    | GBP FX, UK equities                                |
| Macro JP        | BoJ rate decision, Japanese CPI                                              | JPY FX, Nikkei                                     |
| Commodity       | OPEC+ meetings, EIA crude inventories, Baker Hughes rig count                | Crude oil futures, energy equities                 |
| Crypto-specific | Major hard forks, governance votes, exchange-listing events                  | Specific crypto assets                             |
| Corporate       | Earnings (future)                                                            | Single stocks, sector ETFs                         |

## Config schema

```yaml
event_calendar_ref: macro-events-q4-2026@v2
consensus_feed_refs:
  - bloomberg-econ-consensus@v1
  - tradingeconomics-consensus@v1
monitored_events:
  - FOMC_RATE_DECISION
  - US_CPI_YOY
  - US_NFP
direction_model_ref: TRADFI_MACRO_CRYPTO_direction_GBM_90d_V2
pre_event_minutes: 10
event_window_minutes: 30
exit_after_minutes: 45
min_surprise_sigma: 1.5
max_notional_per_event_usd: 500_000
event_size_multiplier_fomc: 2.0 # FOMC 2x standard size
volatility_exit_multiplier: 3.0 # exit if post-event vol > 3x pre-event
share_class: USDT
venues:
  - BINANCE
  - HYPERLIQUID
instruments_eligible:
  - "BINANCE:SPOT:BTC-USDT"
  - "BINANCE:SPOT:ETH-USDT"
  - "HYPERLIQUID:PERPETUAL:BTC-USD"
execution_policy_ref: event-driven-fast-v2

# Leverage + net-delta controls (universal per StrategyInstanceDefinition; Stream D 2026-05-07):
target_leverage: 1.0 # [1, 10]; hard-clamped by per-instrument vol cap at entry
target_net_delta: 0.0 # net directional delta (0 = delta-neutral post-event)
max_underlying_move_pct: 3.0 # vol-cap clamp: skip entry if realized move > X% in 1h window
instrument_volatility_registry_lookup: true # use realized_vol_20 (1h candles) from FSS
```

## Execution semantics

- `TRADE` actions per instrument with target_position_units
- Urgency HIGH or EMERGENCY around event release (fast fills needed)
- MARKET or AGGRESSIVE_LIMIT algos typical
- Post-event flatten: urgency HIGH, market orders

## P&L attribution

- **Event-window P&L**: entry → exit within window
- **Pre-event positioning P&L**: separate accounting for early-entry positions
- **Execution alpha**: vs benchmark (fill at release_ts price)
- **Attribution by event type**: rollup per (event_type, surprise_bucket) to understand which events are most profitable

## Risk profile

- Drawdowns: sharp on wrong-direction surprises (hedge with stop or exit-only-at-window)
- Typical Sharpe: event-specific; cumulative annualized depends on event frequency
- Kill switches: event release delayed > N min, realized vol post-event > pre × 5, simultaneous unexpected event

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    self.max_notional_per_event = new_equity * self.config.max_pct_per_event
    if self.in_active_event_window:
        return self._rescale_active_positions()
    return []
```

## Example instances

```
EVENT_DRIVEN@multi-cex-macro-crypto-usdt-prod
EVENT_DRIVEN@binance-btc-macro-usdt-prod
EVENT_DRIVEN@cme-es-macro-usd-prod
EVENT_DRIVEN@ibkr-eurusd-macro-usd-prod
EVENT_DRIVEN@cme-cl-inventory-usd-prod
EVENT_DRIVEN@cme-cl-opec-usd-prod
```

## Not in this archetype

- **Unscheduled news reactions** (tweets, breaking news) — no consensus → no surprise → directional ML/rules, not
  event-driven
- **Earnings long-short** (relative value between earnings beats/misses) — stat arb cross-sectional
- **Event-driven vol trades** where the alpha is the IV crush pre/post event, not the direction — `VOL_TRADING_OPTIONS`
  (calendar / event-vol)
- **Sports match result bets** — those are event-settled but don't match the surprise-vs-consensus pattern; goes to
  `ML_DIRECTIONAL_EVENT_SETTLED` or `RULES_DIRECTIONAL_EVENT_SETTLED`
- **Continuous intraday strategies** that happen to hold positions across event release — they're ML/rules with
  event-awareness as a config toggle, not event-driven as primary alpha

## Migration from legacy

| Legacy                                                 | Notes                 |
| ------------------------------------------------------ | --------------------- |
| Code: `event_driven_macro.py`, `event_macro_crypto.py` | → `EventDrivenEngine` |

No dedicated legacy family doc; v2 formalizes.

## See also

- Family: [event-driven.md](../families/event-driven.md)
- Execution policy for fast-urgency releases:
  [../cross-cutting/execution-policies.md](../cross-cutting/execution-policies.md)
