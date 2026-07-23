---
doc_type: codex-ssot
title: Session-aware feature calculator pattern
summary: >-
  TradFi session-aware feature-calculator pattern — calculators classify each bar via UAC
  market_session.classify_session() (never hand-roll from clock time), adjust rolling-window denominators to the
  in-session bar count, and honour session-typed manifest reasons (EXPECTED_WEEKEND / HOLIDAY / OUTSIDE_TRADING_HOURS);
  half-day + holiday calendars are DEFERRED.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, unified-api-contracts]
scope: [engineer]
tags: [features, tradfi, honest-coverage, session, uac, data-quality]
related:
  [
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/06-coding-standards/feature-service-pattern.md,
    /codex/02-data/per-asset-group-bucket-layouts.md,
  ]
created: 2026-05-08
authoritative_for:
  [session-aware feature calculator pattern (TradFi market-session classification + session-adjusted rolling windows)]
referenced_by: [/codex/02-data/honest-absence-downstream-handling.md]
owner:
last_reviewed:
code_refs:
---

# Session-aware feature calculator pattern

## Why this pattern exists

TradFi instruments trade in sessions, not 24/7. CME futures have regular-hours / extended-hours / globex windows; equity
options and ETFs follow NYSE / NASDAQ session bounds; many TradFi venues observe partial half-day sessions on holiday
eves. A feature calculator that ignores session structure produces three classes of bug:

1. Rolling-window features compute over wall-clock minutes that span session-closed periods, smearing the close-bar.
2. Same-day features compute against a fragmentary day (half-day session) as if it were a full day, distorting daily
   aggregates.
3. The honest-absence layer can't tell "session was closed" from "data was missing" — both look like zero rows.

## SSOT — UAC `market_session` (shipped UAC@37f6dfd, 2026-05-13)

`unified_api_contracts.canonical.crosscutting.market_session` exposes:

```python
class MarketSession(StrEnum):
    REGULAR = "regular"
    PRE_MARKET = "pre_market"
    POST_MARKET = "post_market"
    OVERNIGHT = "overnight"
    HALTED = "halted"
    CLOSED = "closed"

class SessionPhase(StrEnum):
    OPEN_AUCTION = "open_auction"
    CONTINUOUS = "continuous"
    CLOSE_AUCTION = "close_auction"
    AFTER_HOURS_AUCTION = "after_hours_auction"
    NONE = "none"

@dataclass(frozen=True, slots=True)
class SessionWindow:
    session: MarketSession
    phase: SessionPhase
    weekday_mask: frozenset[int]   # 0=Monday, 6=Sunday
    start_time: time
    end_time: time
    tz: str                         # IANA timezone (e.g. "America/Chicago")

VENUE_SESSION_SCHEDULE: dict[str, list[SessionWindow]]
# Keys (shipped 2026-05-13): "CME", "NYSE", "NASDAQ", "ICE", "CBOE"
# More venues added iteratively per-venue PR cycles.

def classify_session(venue: str, dt: datetime) -> tuple[MarketSession, SessionPhase]:
    """First-match-wins cascade over the venue's SessionWindow list.
    Accepts any tz-aware datetime; handles cross-midnight windows + DST +
    UTC↔local conversion. Returns (CLOSED, NONE) when no window matches."""
```

`MarketSession` + `SessionPhase` are closed enums. Calculators NEVER hand-roll session detection from clock time.

**Half-day / holiday / ICE Brent calendars are DEFERRED** per operator direction (per-venue iteration; the enum SSOT
ships first, schedules backfill behind it). The regular-week schedule is correct for the 5 registered venues; non-
regular-week deviations require either an explicit calendar or caller-side adjustment.

> **[DELTA 2026-05-22]** **Current state:** 5 venues (CME, NYSE, NASDAQ, ICE, CBOE) ship with regular-week schedule
> only. `classify_session()` returns `(CLOSED, NONE)` for US market holidays, CME half-day sessions, and ICE Brent
> window deviations — these are NOT distinguished from ordinary closed periods. **Planned delta:**
> `plans/epics/features_and_ml_master.md` — per-venue calendar additions backfilling holidays + half-day sessions.
> **Target:** `classify_session()` returns correct CLOSED / HALTED for US market holidays, CME half-day sessions, and
> ICE Brent window.

## The pattern

```python
from unified_api_contracts.canonical.crosscutting.market_session import (
    MarketSession,
    classify_session,
)

class MyTradFiCalculator(BaseCalculator):
    def compute(self, target_ts: datetime, inputs: list[Tick]) -> Row:
        session, phase = classify_session(self.venue, target_ts)

        if session == MarketSession.CLOSED:
            # No row written; manifest gets record_empty(reason=EXPECTED_PARTIAL_HALF_DAY|EXPECTED_HOLIDAY)
            return Row.empty(reason=self._reason_from_session(session))

        # Filter inputs to those that fall WITHIN the same session regime.
        in_session = [
            t for t in inputs
            if classify_session(self.venue, t.timestamp)[0] == session
        ]

        # Rolling-window denominators MUST adjust to the in-session bar count, not wall-clock minutes.
        return self._compute_session_aware(target_ts, in_session, session, phase)
```

## Rolling-window rule

For a rolling-window feature with window size `W` (e.g. 20-bar SMA on 1-min OHLCV):

- The window stays **N bars wide** (e.g. 20).
- The lookback period in wall-clock seconds **expands** to span session boundaries (so a 20-bar window crossing an
  overnight close pulls bars from yesterday's close + today's open, not 20 wall-clock minutes that span 16 hours of
  closed market).
- The denominator (volume-weighted avg, etc.) is over the N bars, not over wall-clock minutes.

## Same-day feature rule

For features that aggregate "today" (VWAP, OHLC, daily_return):

- Half-day sessions emit a row with `session=REGULAR` (the session enum doesn't currently distinguish half-day from
  full-day — half-day calendar is DEFERRED). Downstream consumers detect half-day via the absent-row gap or the separate
  half-day calendar (TBD).
- `available_at` is stamped at the session-close bar's timestamp (NOT wall-clock midnight), so live and batch agree.

## Cross-instrument calculation rule

Cross-instrument features (basis, spread, dispersion) span venues with potentially different sessions. The calculator
takes the **intersection** of session-open windows; if instrument A is OPEN but instrument B is CLOSED, the row is
emitted with the cross-instrument component set to NaN and a typed reason in honest-absence.

## Session-typed manifest reasons (writegate Phase 2.E.2 — MTDS@038a611)

The MTDS orchestrator emits `record_expected_empty` for every `(venue, data_type)` it pre-skips due to a non-trading
day. Feature calculators MUST read and honour these manifest reasons — not re-derive them from the clock.

### Three reasons a calculator sees

| Manifest reason                  | Meaning for the calculator                                                                                                                                  |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `EXPECTED_WEEKEND`               | Whole-day closed for this TradFi venue. Do NOT include in rolling-window denominator. Emit `record_empty` for any calc output targeting this day.           |
| `EXPECTED_HOLIDAY`               | Same as weekend — whole-day US market holiday.                                                                                                              |
| `EXPECTED_OUTSIDE_TRADING_HOURS` | Intra-day: this bar falls outside the venue's published session. Drop from rolling window. Omit from same-day aggregates. Emit NaN for the calc output bar. |

### Rolling-window rule (session-adjusted denominator)

For a W-bar rolling feature over a TradFi venue:

```python
from unified_api_contracts.canonical.crosscutting.honest_coverage import (
    EXPECTED_WEEKEND, EXPECTED_HOLIDAY, EXPECTED_OUTSIDE_TRADING_HOURS,
)

_SESSION_CLOSED_REASONS = frozenset({
    EXPECTED_WEEKEND, EXPECTED_HOLIDAY, EXPECTED_OUTSIDE_TRADING_HOURS,
})

def is_session_closed(manifest_reason: str | None) -> bool:
    return manifest_reason in _SESSION_CLOSED_REASONS

# In the rolling-window loop:
valid_bars = [
    bar for bar in window_bars
    if not is_session_closed(manifest.get_reason(bar.row_key, bar.day))
]
# Denominator = len(valid_bars), not W.
# Emit n_valid as a sibling column.
```

**Key invariant**: weekend / holiday bars excluded from the denominator are NOT treated as NaN-data — they are calendar
vacuums. Including them in the denominator would produce a 5-day SMA over 7 calendar days, which is wrong.

## Cross-references

- Honest absence + session-typed availability:
  [`/codex/02-data/honest-absence-downstream-handling.md`](/codex/02-data/honest-absence-downstream-handling.md) §
  "Session-typed availability"
- Availability semantics SSOT: `unified_api_contracts.canonical.crosscutting.availability_semantics`
- Market-session SSOT (shipped UAC@37f6dfd 2026-05-13): `unified_api_contracts.canonical.crosscutting.market_session`
- Feature service pattern (BaseCalculator): [`feature-service-pattern.md`](feature-service-pattern.md)
- TradFi shard atom (per-root + half-day handling):
  [`/codex/02-data/per-asset-group-bucket-layouts.md`](/codex/02-data/per-asset-group-bucket-layouts.md)
- TradFi futures lifecycle (`CanonicalFuturesContract` + `FuturesContractLifecyclePhase`, shipped UAC@2ac74e2
  2026-05-13): `unified_api_contracts.canonical.domain.derivatives.futures`
