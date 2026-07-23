---
doc_type: codex-ssot
title: "Family: Event-Driven"
summary:
  The Event-Driven strategy family — 1 archetype (EVENT_DRIVEN) trading scheduled macro/earnings announcements (FOMC,
  CPI, NFP, OPEC, earnings); edge is surprise-magnitude vs consensus × model-predicted direction within a time-bounded
  post-event window, flattened on time-box exit.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, event-driven, tradfi, cefi, ml, execution]
related:
  [
    ml-directional.md,
    /codex/09-strategy/architecture-v2/families/rules-directional.md,
    ../archetypes/event-driven.md,
    ../cross-cutting/execution-policies.md,
  ]
created: 2026-04-17
authoritative_for: [Event-Driven strategy family spec (alpha thesis + EVENT_DRIVEN archetype)]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/cross-cutting/event-driven-macro.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/event-driven.md,
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/families/rules-directional.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Family: Event-Driven

> **Alpha source:** Scheduled external events with measurable surprise. When an event releases (FOMC, CPI, NFP,
> earnings, OPEC announcement), the event's _surprise relative to consensus_ produces a measurable, time-bounded
> reaction in targeted instruments.
>
> **Primary edge method:** Surprise magnitude × model-predicted direction > threshold, within a bounded time window
> around the event.
>
> **Typical hold policies:** Short-duration ONE_SHOT or time-boxed (minutes to hours post-event).
>
> **Archetype count:** 1 — `EVENT_DRIVEN`.

## Alpha thesis

Event-Driven captures market reactions to scheduled announcements that have **consensus forecasts** (and therefore
measurable surprise) and **known timing** (so we can pre-position in the entry window and exit before vol normalizes).

Examples:

- FOMC rate decisions (± dot plot shift) → crypto + equities + FX reaction
- US CPI, PPI, PCE releases → crypto + equities + FX reaction
- US Non-Farm Payrolls → crypto + equities + FX + rates reaction
- OPEC / OPEC+ meetings → oil + commodity reaction
- EIA crude inventory release → oil reaction
- Corporate earnings → single-stock + sector reaction
- ECB / BoE / BoJ rate decisions → FX + rates + index reaction
- China economic data → CNY, commodities, global risk-on/off

Key properties distinguishing event-driven from other families:

- **Schedule-aware**: strategy knows the exact tick when an event releases
- **Surprise-measurable**: event has a consensus forecast, so realized - expected is a computable surprise
- **Time-bounded**: reaction has a reasonable window (e.g., 30-60 minutes for macro; longer for earnings); exit before
  regime-normalize

**Not in this family:**

- Unscheduled news reactions without consensus forecast — no measurable surprise, treated as directional (ML or Rules)
- Earnings-driven stat arb (long cheap earnings vs short expensive) — that's `STAT_ARB_CROSS_SECTIONAL` or
  `STAT_ARB_PAIRS_FIXED`
- Vol-of-vol around events (buying pre-event straddle, unwinding post) — if alpha is vol view on the event's implied vol
  crush, goes to `VOL_TRADING_OPTIONS`
- Sports events (match kickoff / result) — these are event-settled bets, not surprise-vs-consensus; go to
  `ML_DIRECTIONAL_EVENT_SETTLED` or `RULES_DIRECTIONAL_EVENT_SETTLED`
- Chain-level events (hard forks, governance votes) — tracked separately; if tradeable, usually via directional families
  with event flag

## 1 Archetype

[`EVENT_DRIVEN`](../archetypes/event-driven.md) — schedule + surprise → directional position in targeted instruments for
a time-bounded window.

Why a single archetype: the code structure is the same across different event types (FOMC, CPI, earnings, OPEC). What
differs is the event calendar source, the instruments targeted, the consensus feed, and the surprise → direction model —
all config.

## Shared primitives

- **Event calendar registry**: versioned registry of upcoming events with (event_id, release_timestamp, consensus_value,
  target_instruments)
- **Consensus feed subscriber**: Bloomberg / Reuters / ECB econ-consensus data
- **Surprise computer**: `surprise = (realized - consensus) / std_dev_of_forecasts`
- **Direction model**: per event type, mapping surprise → expected instrument direction (e.g., CPI surprise high → USD
  up → crypto down)
- **Entry-window manager**: pre-event positioning (if signal fires from pre-announcement features)
- **Exit-window manager**: flatten at window-close (time-boxed); or vol-normalized (when realized vol drops to
  pre-event)
- **Dead-man switch**: hard cut position if event release is delayed or malformed

## Typical signal sources

| Signal                      | Source                                                                            |
| --------------------------- | --------------------------------------------------------------------------------- |
| Event calendar              | ForexFactory, Bloomberg, ECB calendar                                             |
| Consensus forecast          | Bloomberg consensus, TradingEconomics, Refinitiv                                  |
| Realized value (on release) | Official release via fastest low-latency feed (e.g., US BLS direct press release) |
| Surprise magnitude          | Computed from (realized - consensus) / σ(forecasts)                               |
| Instrument-response model   | ML or regression trained on historical event × surprise → instrument returns      |

## Typical edge methods

- **Surprise-magnitude threshold**: trigger if |surprise| > 1.5σ (configurable)
- **Direction-model confidence**: ML or regression model predicts direction given surprise + regime + pre-event
  conditions
- **Time-bounded realization**: capture move within a window; exit before window close

## Position structure

- Single position per (event, instrument) — usually long or short across 2-5 targeted instruments
- Typically high-leverage within the window (because move is expected)
- Multi-leg (e.g., long BTC + short equity index on dovish FOMC) — paired for expected correlation

## Typical staking methods

| Method                                  | When used                                                    |
| --------------------------------------- | ------------------------------------------------------------ |
| Fixed notional per event                | Baseline — each event gets allocated capital                 |
| Surprise-scaled                         | Bigger surprise → bigger stake (proportional to σ)           |
| 2× scaled during high-conviction events | FOMC rate decisions get 2× baseline; lower-conviction get 1× |

## Venue patterns

- **Crypto**: Binance, Hyperliquid, Bybit, Deribit for both spot and perp exposure
- **TradFi equities**: IBKR equity futures (ES, NQ) or SPY
- **TradFi rates**: CME rates futures (ZN, ZB)
- **TradFi FX**: IBKR FX spot or CME FX futures
- **Commodities**: CME crude, gold, NG futures

Cross-asset instances (trade multiple markets on one event) are common.

## Expression options

- Directional: spot, perp, futures, options (delta-focused or straddle for uncertainty)
- Paired: long-short across correlated asset classes to express the directional thesis while hedging beta

## Risk profile

- **Drawdowns**: can be sharp (wrong side of FOMC costs a lot quickly); managed via hard time-exit
- **Tail risks**:
  - Event delay or cancellation (rare but happens)
  - Non-standard release (e.g., clerical error)
  - Cross-asset correlation breaks (pair trade breaks down)
  - Prior-release whipsaw (price moves against expected direction first, then snaps back)
- **Sharpe**: event-specific; can be high on a per-event basis but events are infrequent
- **Kill switches**: event release delay > N minutes, realized vol post-event > pre-event × 5, unexpected simultaneous
  event

## UI dashboard

- Event calendar (upcoming events within N days)
- Pre-event positioning status
- Post-event P&L per event — scatter plot (surprise vs realized return)
- Direction-model hit rate (correct direction predicted / total events)
- Time-window adherence (did we exit by the deadline?)
- Per-event-type aggregate (FOMC cumulative, CPI cumulative, etc.)

## Required subscriptions

Config references:

- **event_calendar_ref** — versioned event calendar source
- **consensus_feed_refs** — consensus data sources
- **direction_model_ref** — per-event-type surprise-to-direction model
- **venue_capability_refs** — eligible execution venues
- **execution_policy_ref** — likely fast-urgency + market-order preference during event window

## Typical instance examples

```
Crypto macro:
  EVENT_DRIVEN@multi-cex-macro-crypto-usdt-prod        (BTC/ETH reaction to FOMC/CPI/NFP)
  EVENT_DRIVEN@binance-btc-macro-usdt-prod

TradFi macro:
  EVENT_DRIVEN@cme-es-macro-usd-prod                   (S&P E-mini on FOMC/CPI)
  EVENT_DRIVEN@ibkr-eurusd-macro-usd-prod              (FX on FOMC/ECB)
  EVENT_DRIVEN@cme-zn-rates-macro-usd-prod             (10Y rates on FOMC/NFP)

Commodity events:
  EVENT_DRIVEN@cme-cl-inventory-usd-prod               (crude oil on EIA)
  EVENT_DRIVEN@cme-cl-opec-usd-prod                    (crude oil on OPEC)

Equity earnings (future):
  EVENT_DRIVEN@ibkr-aapl-earnings-usd-prod             (single-stock earnings)
```

## Reaction to capital flow events

```python
def react_to_equity_change(self, new_equity_usd: Decimal) -> list[StrategyInstruction]:
    self.equity_usd = new_equity_usd
    self.max_per_event_capital = new_equity_usd * self.config.max_pct_per_event
    # Event-driven doesn't hold continuous positions between events
    # Only resize if currently in an event window
    if self.in_active_event_window:
        return self._rescale_active_position()
    return []
```

## Rebalancing triggers

- Event calendar tick: entering pre-event window → position in direction predicted by model
- Event release: update surprise + direction → hold or flip
- Event window close: flatten position (time-box exit)
- Event delay: reset, don't position
- Equity change: only relevant if currently in-window

## Migration from legacy docs

| Legacy                                             | Mapping             | Notes                                             |
| -------------------------------------------------- | ------------------- | ------------------------------------------------- |
| Code: `strategy-service/.../event_driven_macro.py` | `EventDrivenEngine` | Shared engine across crypto + TradFi macro events |

No dedicated legacy doc for event-driven strategy; primarily a code-level feature. This v2 doc introduces explicit
event-driven family formalization.

## Cross-references

- Archetype: [event-driven](../archetypes/event-driven.md)
- Event calendar as artifact:
  [../../../04-architecture/artifact-versioning.md](../../../04-architecture/artifact-versioning.md)
- Time-bounded execution + fast-urgency policy:
  [../cross-cutting/execution-policies.md](../cross-cutting/execution-policies.md)
