---
scope: [engineer]
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

## SSOT — UAC `venue_trading_calendar` + session helpers

`unified_api_contracts.canonical.crosscutting.venue_trading_calendar` exposes:

```python
HALF_DAY_SESSIONS: dict[Venue, set[date]]                  # holiday-eve half-days
VENUE_SESSION_HOURS: dict[Venue, list[SessionWindow]]      # regular + extended sessions per venue
classify_session(venue: Venue, ts: datetime) -> SessionClass  # OPEN / CLOSED / HALF_DAY / PRE_MARKET / AFTER_HOURS
```

`SessionClass` is a closed enum. Calculators NEVER hand-roll session detection from clock time.

## The pattern

```python
class MyTradFiCalculator(BaseCalculator):
    def compute(self, target_ts: datetime, inputs: list[Tick]) -> Row:
        session_class = classify_session(self.venue, target_ts)

        if session_class == SessionClass.CLOSED:
            # No row written; manifest gets record_empty(reason=EXPECTED_PARTIAL_HALF_DAY|EXPECTED_HOLIDAY)
            return Row.empty(reason=self._reason_from_session(session_class))

        # Filter inputs to those that fall WITHIN the relevant session window.
        in_session = [t for t in inputs
                      if classify_session(self.venue, t.timestamp) == session_class]

        # Rolling-window denominators MUST adjust to the in-session bar count, not wall-clock minutes.
        return self._compute_session_aware(target_ts, in_session, session_class)
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

- Half-day sessions emit a row, but the row carries `session_class=HALF_DAY` so downstream consumers can choose to
  exclude or to scale.
- `available_at` is stamped at the session-close bar's timestamp (NOT wall-clock midnight), so live and batch agree.

## Cross-instrument calculation rule

Cross-instrument features (basis, spread, dispersion) span venues with potentially different sessions. The calculator
takes the **intersection** of session-open windows; if instrument A is OPEN but instrument B is CLOSED, the row is
emitted with the cross-instrument component set to NaN and a typed reason in honest-absence.

## Cross-references

- Honest absence + session-typed availability:
  [`../02-data/honest-absence-downstream-handling.md`](../02-data/honest-absence-downstream-handling.md) §
  "Session-typed availability"
- Availability semantics SSOT: `unified_api_contracts.canonical.crosscutting.availability_semantics`
- Venue trading calendar SSOT: `unified_api_contracts.canonical.crosscutting.venue_trading_calendar`
- Feature service pattern (BaseCalculator): [`feature-service-pattern.md`](feature-service-pattern.md)
- TradFi shard atom (per-root + half-day handling):
  [`../02-data/per-asset-group-bucket-layouts.md`](../02-data/per-asset-group-bucket-layouts.md)
