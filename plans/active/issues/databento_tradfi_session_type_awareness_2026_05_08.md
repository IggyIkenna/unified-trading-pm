---
title:
  "Databento TradFi candles session-agnostic — pre/post-market + auction periods indistinguishable from regular session,
  contaminating every downstream feature"
created: 2026-05-08
author: ikenna
source:
  - unified-api-contracts/unified_api_contracts/registry/session_times.py:1-238 (SessionWindow SSOT — aggregate windows
    only, no session-type taxonomy)
  - market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/databento_classifier.py:235-279
    (DatabentoClassification dataclass — no session_type field)
  - market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/databento_adapter.py (no session
    classification at write time)
  - market-data-processing-service/market_data_processing_service/market_state_detector.py (MDPS-only session awareness;
    not propagated upstream)
  - features-volatility-service/features_volatility_service/core/volatility_orchestration.py:107-140 (mentions excluded
    states in comments only — calculator code does NOT consume session_type)
  - plans/active/tradfi_master_2026_05_07.plan.md (no session-type todos)
  - plans/active/mtds_databento_path_streaming_2026_05_07.plan.md (no session-type todos)
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Databento TradFi candles session-agnostic — every downstream contaminated by pre/post-market

> **Severity**: P1 — blocks honest TradFi feature compute; until session-type-aware, every TradFi feature/strategy
> silently mixes thin-liquidity pre/post-market bars with regular-session bars. Doesn't strictly block May 23
> paper-trade if first DeFi archetypes don't trade TradFi-derived signals, but blocks any TradFi strategy graduation.
> **Blast radius**: UAC (session-type taxonomy + per-venue session schedule) + MTDS Databento adapter (write-time
> classification) + MDPS / features-\* / strategy-service / execution-service / risk-and-exposure-service (consumer
> filtering). **Suggested owner**: `tradfi_master_2026_05_07.plan.md` Phase X (new) OR new sibling plan
> `tradfi_session_type_awareness_2026_05_08.plan.md`.

## What I found

**Five-question audit; complete blind spot across the workspace except partial MDPS labelling that doesn't propagate.**

### Q1 — UAC session-type taxonomy: GAP

[session_times.py:1-238](../../../unified-api-contracts/unified_api_contracts/registry/session_times.py) defines
`SessionWindow(open_time, close_time, timezone)` and `get_session_times()` returning
`SessionTimes(exchange, date, open_utc, close_utc, is_24_7, timezone_name)`. **Aggregate windows only — no session-type
enum.** No `MarketSession` / `pre_market` / `post_market` / `regular_session` / `extended_hours` / `opening_auction` /
`closing_auction` taxonomy exists. CLAUDE.md TradFi shard-key matrix doesn't include `session_type`.

### Q2 — Databento adapter classifies instruments but not session-of-day: COMPLETE GAP

[databento_classifier.py:235-279](../../../market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/databento_classifier.py#L235-L279)
`DatabentoClassification` captures
`instrument_type, underlying, expiry_date, strike, option_right, is_continuous, combo metadata`. No `session_type`
field. The Databento adapter parses each candle but writes them as unmarked OHLCV rows. **A 04:00 ET pre-market candle
is parquet-indistinguishable from a 10:30 ET regular candle.**

### Q3 — Downstream consumer filtering: PARTIAL (only MDPS, doesn't propagate)

- `market-data-processing-service/.../market_state_detector.py` uses `pre_market_open_utc` / `post_market_close_utc`
  cached from instruments-service to detect market state per timestamp. **Local label only — not written back to
  parquet.**
- [volatility_orchestration.py:107-140](../../../features-volatility-service/features_volatility_service/core/volatility_orchestration.py#L107-L140)
  docstrings + tests enumerate states `(pre_market, post_market, closed, halted, auction, normal)` with comments like
  `# Excluded: closed, pre_market, post_market` — but **the actual calculator code does NOT consume a `session_type`
  field from the input parquet.** Comment-only enforcement; no runtime gate.
- features-cefi-service / features-cross-instrument / strategy-service / execution-service / risk-and-exposure-service:
  zero grep hits for session-type filtering.

### Q4 — Plan coverage: COMPLETE ABSENCE

Searched `tradfi_master_2026_05_07.plan.md`, `mtds_databento_path_streaming_2026_05_07.plan.md`,
`manifest_migration_master_2026_05_07.plan.md`, `infrastructure_master_2026_05_07.plan.md` for "session", "pre-market",
"post-market", "extended hours", "opening auction", "closing auction" → **zero hits**. Not on any roadmap.

### Q5 — CME futures + options session structure handling: PARTIAL

`session_times.py:54-60` `_CME_SESSION` collapses Globex into a single `open=17:00 Sun → close=16:00 Fri` window. **No
distinction** between pre-open / main session / post-close / daily settlement / maintenance break. ES.OPT trades
08:30-15:00 CT regular + extended; codebase treats options identically to underlying futures' Globex window — wrong by
hours.

## Why it matters

Concrete failure modes silently contaminating every TradFi feature:

- **Volatility features**: pre-market (04:00-09:30 ET) thin-liquidity wide-spread prints look like high realised
  volatility. RV / IV calculators ingest these as regular candles → false volatility signals.
- **Open / close features**: closing auction (16:00 ET single bar with massive volume) is a fundamentally different
  liquidity event from regular intraday trading. Treating it as a regular bar conflates auction price discovery with
  order-flow signals.
- **Microstructure features (spread, depth, kyle's lambda)**: completely meaningless during pre/post-market — spreads
  are 5-10x normal, market makers absent.
- **CME futures arb features**: maintenance break (~16:00-17:00 CT daily) has zero liquidity by design. Treated as
  "session quiet" by current zero-volume-bar logic; should be `record_empty(reason=MAINTENANCE_BREAK)` (a typed reason
  in EMPTY_CONFIRMED_REASONS closed set).
- **Live execution**: strategy fires an order at 04:30 ET in pre-market — execution-service has no signal that liquidity
  is thin; could fill at terrible price or hang on partial fill.
- **`Live = batch` violation**: live-mode would naturally see pre-market as "different liquidity regime" via
  spread/depth signals; batch silently smooths it out.

## Recommended decision

### Phase 1 — UAC session-type taxonomy SSOT

New module: `unified_api_contracts.canonical.crosscutting.market_sessions`

```python
class MarketSession(StrEnum):
    PRE_MARKET = "pre_market"
    OPENING_AUCTION = "opening_auction"
    REGULAR = "regular"
    LUNCH_BREAK = "lunch_break"        # JPX, HKEX have midday breaks
    CLOSING_AUCTION = "closing_auction"
    POST_MARKET = "post_market"
    EXTENDED_HOURS = "extended_hours"
    OVERNIGHT = "overnight"             # Globex futures off-hours
    SETTLEMENT_PERIOD = "settlement_period"
    MAINTENANCE_BREAK = "maintenance_break"
    CLOSED = "closed"

@dataclass(frozen=True)
class SessionPhase:
    venue: VenueName
    asset_class: AssetClass  # equity / etf / future / option (different schedules per asset class within same venue)
    session: MarketSession
    start_time_local: time
    end_time_local: time
    timezone: str
    weekdays_active: list[int]  # 0=Mon … 6=Sun

VENUE_SESSION_SCHEDULE: dict[(VenueName, AssetClass), list[SessionPhase]] = {
    (NASDAQ, EQUITY): [
        SessionPhase(NASDAQ, EQUITY, PRE_MARKET, time(4, 0), time(9, 30), "America/New_York", [0,1,2,3,4]),
        SessionPhase(NASDAQ, EQUITY, OPENING_AUCTION, time(9, 30), time(9, 30, 1), "America/New_York", [0,1,2,3,4]),
        SessionPhase(NASDAQ, EQUITY, REGULAR, time(9, 30), time(16, 0), "America/New_York", [0,1,2,3,4]),
        SessionPhase(NASDAQ, EQUITY, CLOSING_AUCTION, time(16, 0), time(16, 0, 1), "America/New_York", [0,1,2,3,4]),
        SessionPhase(NASDAQ, EQUITY, POST_MARKET, time(16, 0), time(20, 0), "America/New_York", [0,1,2,3,4]),
    ],
    (CME, FUTURE): [
        SessionPhase(CME, FUTURE, OVERNIGHT, time(17, 0), time(8, 30), "America/Chicago", [6,0,1,2,3]),  # Sun→Fri 17:00 → 08:30
        SessionPhase(CME, FUTURE, REGULAR, time(8, 30), time(16, 0), "America/Chicago", [0,1,2,3,4]),
        SessionPhase(CME, FUTURE, MAINTENANCE_BREAK, time(16, 0), time(17, 0), "America/Chicago", [0,1,2,3,4]),
    ],
    (CME, OPTION): [...],  # ES.OPT 08:30-15:00 CT regular + extended; different from underlying future
    ...
}

def classify_timestamp(venue: VenueName, asset_class: AssetClass, ts_utc: datetime) -> MarketSession:
    """Return the MarketSession for a given (venue, asset_class, timestamp)."""
```

### Phase 2 — Databento adapter writes session_type column

At parquet finalize in databento_adapter, every OHLCV row gets a `session_type: MarketSession` column populated via
`classify_timestamp(venue, asset_class, ts_event)`. Schema migration via one-time backfill walking captured Databento
parquets + classifying retrospectively (`classify_timestamp` is deterministic given UAC SSOT, so re-run is safe).

### Phase 3 — Downstream consumer wiring

Each consumer adds an explicit session-type filter:

- **features-volatility / features-cross-instrument**: default to
  `session_type IN (REGULAR, OPENING_AUCTION, CLOSING_AUCTION)`. Calculators that genuinely want pre/post-market signal
  opt-in explicitly.
- **strategy-service**: archetype declares its `allowed_sessions: list[MarketSession]`; signals fired during disallowed
  sessions emit `STRATEGY_BLOCKED_OUTSIDE_SESSION` events (no execution).
- **execution-service**: per-venue + per-asset-class allowed_sessions check at order-submission time; out-of-session
  orders rejected with typed error `OutOfSessionOrderError`.
- **risk-and-exposure-service**: position-mark prices use session-aware close (closing-auction price, not last
  post-market print).

### Phase 4 — Replace zero-volume-bar default during non-trading sessions

CME futures `MAINTENANCE_BREAK` periods today get category-D zero-volume-bars per
`mdps_liquidity_baseline_and_live_tick_staleness_2026_05_08.md` semantics — that's wrong. Should be
`record_empty(reason=EXPECTED_MAINTENANCE_BREAK)` instead. Add to `EMPTY_CONFIRMED_REASONS` closed set:
`EXPECTED_PRE_MARKET`, `EXPECTED_POST_MARKET`, `EXPECTED_MAINTENANCE_BREAK`, `EXPECTED_LUNCH_BREAK`. The MDPS write-gate
consults `classify_timestamp(...)` for the period; non-tradeable session phases route to typed empty rather than
zero-volume-bar.

## Acceptance criteria

- [ ] `MarketSession` enum + `SessionPhase` + `VENUE_SESSION_SCHEDULE` + `classify_timestamp` SSOT shipped in UAC.
- [ ] Databento adapter writes `session_type` column on every OHLCV row.
- [ ] One-time backfill reclassifies all captured Databento parquets to add `session_type`.
- [ ] features-\* default-filter to regular + auction sessions; non-default sessions opt-in.
- [ ] strategy-service archetype declares `allowed_sessions`; out-of-session signals blocked.
- [ ] execution-service `OutOfSessionOrderError` for out-of-session orders.
- [ ] MDPS write-gate: maintenance-break / pre-market / post-market periods get typed `record_empty(reason=EXPECTED_*)`
      instead of category-D zero-volume-bar.
- [ ] Smoke test: feed Databento parquet with mixed-session candles through the full pipeline; verify only REGULAR +
      auction bars reach the strategy compute path.

## Open questions

- Holidays / half-days (e.g. NYSE Christmas Eve early-close 13:00 ET): handle via `venue_trading_calendar` overrides on
  top of standard schedule? Plan reference: existing `KNOWN_COVERAGE_GAPS` + `is_non_trading_day` precedent.
- DST transitions: NASDAQ 09:30 ET in winter is 14:30 UTC; in summer 13:30 UTC. `classify_timestamp` must use TZ-aware
  logic (Python `pytz` or `zoneinfo`) — explicit acceptance criterion.
- For tick-grain (not just OHLCV bars): session_type column also needed on tick-level parquets, OR derived at read-time
  via classify_timestamp? Recommend: store on bar-grain (low cost), derive at read-time on tick-grain (storage cost).
- Crypto perp venues: 24/7, single REGULAR session by default. Still need taxonomy for "scheduled maintenance" (Bybit,
  OKX have weekly upgrade windows). Same architecture extends naturally.
- Coordination with `mdps_liquidity_baseline_and_live_tick_staleness_2026_05_08.md`: the liquidity baseline must be
  per-(venue, instrument, period, **session_type**) — pre-market baseline is inherently lower than regular-session
  baseline, so a single rolling baseline conflating sessions is wrong. Update that issue's Phase 1 to include
  session_type as a baseline axis.
