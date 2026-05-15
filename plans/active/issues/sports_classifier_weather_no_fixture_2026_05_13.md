---
title: "Sports classifier — open_meteo WEATHER should be no-op on no-fixture days (write + read side)"
created: 2026-05-13
author: slot-4-ikenna
source:
  - expected_unattempted_propagation_chain_2026_05_12
  - sports_classifier_extension_followup_2026_05_13 (parent — discovered the gap)
severity: P2
status: PARTIAL — read-side DONE (2026-05-14); write-side DEFERRED
locked_by: live-defi-rollout
locked_since: 2026-05-13
routing:
  primary_owner: slot-4-ikenna (2026-05-13)
  composes_with:
    - sports_classifier_sfi_footystats_fixture_pin_2026_05_13.md (sibling P1 — same fixture helper)
    - sports_classifier_player_values_cadence_2026_05_13.md (sibling P1)
---

## What I found

`_classify_sports` in `unified_trading_library/legacy_reason_classifier.py:191` has NO per-source rule for `open_meteo`
WEATHER data. Empty days fall through to `SOURCE_RETURNED_ZERO`.

That's technically correct for weather (it's universal — every day everywhere has weather, so an empty day really is a
failure). **But** there's a bigger upstream issue: instruments-service is fetching weather for days with no fixtures,
which is a waste of API calls + storage. We don't need weather data if no match is scheduled.

## Why it matters

- **API call waste**: open_meteo has rate limits; fetching weather for ~365 days/year/(league, stadium) when only ~50
  fixture days/year exist per stadium is ~7× over-fetch.
- **Storage waste**: parquets written for no-fixture days are inert (no consumer reads them).
- **Manifest noise**: phantom-recon sees the no-fixture WEATHER captured rows and may flag them as phantoms if the
  parquets get cleaned up out of band.

## Operator direction (2026-05-13 Ikenna)

> "We don't need weather if there is no fixture so it's a waste of api calls and data — there should be ignored."

## Implementation (two sides)

### Write-side prevention (upstream — saves API calls + storage)

1. Locate instruments-service WEATHER adapter (likely
   `instruments-service/instruments_service/adapters/weather_open_meteo.py` or similar — needs audit).
2. Gate the fetch loop on `is_fixture_scheduled(league_id, day)` BEFORE calling open_meteo. If no fixture → skip +
   record `record_empty(reason=EXPECTED_NO_FIXTURE)`.
3. This naturally aligns with the SFI/footystats fixture-pin rule (same helper).

### Read-side classification (for legacy WEATHER rows already in the manifest)

1. In `_classify_sports`, for `source == "open_meteo"`:
   ```python
   if league_id and day_dt is not None:
       if not is_fixture_scheduled(league_id, day):
           return "EXPECTED_NO_FIXTURE"
   ```
2. Else fall through (weather IS expected on fixture days; empty = honest failure → `SOURCE_RETURNED_ZERO`).

## Verification

- Audit instruments-service weather adapter: count API calls per day before/after gate. Expect ~7× reduction.
- Re-run Script 3 dry-run for sports. Expect WEATHER empty rows on no-fixture days to flip from `SOURCE_RETURNED_ZERO` →
  `EXPECTED_NO_FIXTURE`.

## Files affected

- `unified-trading-library/unified_trading_library/legacy_reason_classifier.py` — extend `_classify_sports` with
  open_meteo branch.
- `unified-trading-library/tests/unit/test_legacy_reason_classifier.py` — ≥4 new tests covering: fixture day + WEATHER
  missing → SOURCE_RETURNED_ZERO (legit failure); no-fixture day + WEATHER missing → EXPECTED_NO_FIXTURE;
  pre-source-coverage-start still wins; no league_id falls through.
- `instruments-service/instruments_service/adapters/weather_open_meteo.py` (or actual path — audit pending) — gate fetch
  on `is_fixture_scheduled`.

## Composes with

- `sports_classifier_extension_followup_2026_05_13.md` (parent audit)
- `sports_classifier_sfi_footystats_fixture_pin_2026_05_13.md` (sibling — SHARES the `is_fixture_scheduled` helper)
- `sports_classifier_player_values_cadence_2026_05_13.md` (sibling)

## Resolution — 2026-05-14 slot 4 (partial)

**Read-side DONE**: `utl@79c72bad` — `open_meteo` added to the fixture-pin set in `_classify_sports`. Empty WEATHER rows
on no-fixture days now return `EXPECTED_NO_FIXTURE`. Covered by 5 fixture-pin tests.

**Write-side DEFERRED**: instruments-service weather adapter gate (`is_fixture_scheduled` pre-fetch) not yet
implemented. File this as a follow-up in `instruments-service` weather adapter. **DEFERRED**: instruments-service
`weather_open_meteo` adapter write-side prevention. Successor: file a new issue
`weather_adapter_fixture_gate_YYYY_MM_DD.md` in instruments-service cleanup cycle.

## Notes

- P2 (not P1) because the read-side classification gap is cosmetic (rows are already `SOURCE_RETURNED_ZERO` which is
  technically correct for "weather data missing"). The real win is the write-side prevention which is operational
  efficiency, not data correctness.
- Could be deferred to a follow-up cycle without blocking apply-flips.
