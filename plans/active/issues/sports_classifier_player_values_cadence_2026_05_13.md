---
title: "Sports classifier — transfermarkt PLAYER_VALUES needs cadence-aware rule (weekly, not daily)"
created: 2026-05-13
author: slot-4-ikenna
source:
  - expected_unattempted_propagation_chain_2026_05_12
  - sports_classifier_extension_followup_2026_05_13 (parent — discovered the gap)
severity: P1
status: DONE — slot 4 (2026-05-14)
locked_by: live-defi-rollout
locked_since: 2026-05-13
routing:
  primary_owner: slot-4-ikenna (2026-05-13)
  composes_with:
    - sports_classifier_sfi_footystats_fixture_pin_2026_05_13.md (sibling P1)
    - sports_classifier_weather_no_fixture_2026_05_13.md (sibling P1)
---

## What I found

`_classify_sports` in `unified_trading_library/legacy_reason_classifier.py:191` explicitly EXCLUDES PLAYER_VALUES from
the transfer-window rule (per line 211 docstring: "Player-values / squad data is year-round; the 'transfer' in data_type
guard keeps this branch off it.").

The current behaviour for PLAYER_VALUES empty days is `SOURCE_RETURNED_ZERO` (confirmed by test
`test_sports_transfermarkt_player_values_is_year_round_not_window_bounded`).

**But this is wrong** — transfermarkt scrapes player values on a NON-DAILY cadence (typically weekly when transfer fees
update). Daily empty days are NOT honest "source returned zero" — they are EXPECTED non-scrape days. The classifier
should reflect this.

## Why it matters

Without a cadence-aware rule, ~6 out of every 7 days for PLAYER_VALUES will be misclassified as `SOURCE_RETURNED_ZERO`
(real failure) when they're actually expected non-scrape days. This:

- Inflates phantom counts.
- Triggers spurious alerts on "data missing" when it's expected.
- Blocks Script 3 apply-flips that depend on correct classifications.

## Operator direction (2026-05-13 Ikenna)

> "Make the cadence aware rule then for weekly if we know the day or check neighbour days whatever is best."

## Implementation

Two options; pick the more reliable empirically:

**Option A — explicit cadence constant (preferred if cadence is stable)**

1. Empirically determine transfermarkt PLAYER_VALUES update cadence by sampling production manifest: group rows by
   `weekday(date)`, count rows per weekday. If 1-2 weekdays dominate (e.g., `Tuesday` ≫ others), that's the canonical
   update day.
2. Add to UAC `unified_api_contracts.canonical.domain.sports.refdata_cadence` (NEW or extension):
   ```python
   TRANSFERMARKT_PLAYER_VALUES_UPDATE_WEEKDAYS: frozenset[int] = frozenset({1, 2})  # Tue, Wed
   ```
3. In `_classify_sports` for `(source == "transfermarkt", data_type == "PLAYER_VALUES")`:
   ```python
   from datetime import datetime
   day_dt = datetime.strptime(day, "%Y-%m-%d")
   if day_dt.weekday() not in TRANSFERMARKT_PLAYER_VALUES_UPDATE_WEEKDAYS:
       return "EXPECTED_REFDATA_CADENCE_CHANGE"
   ```

**Option B — neighbour-day heuristic (fallback if cadence varies)**

In `_classify_sports`, for PLAYER_VALUES:

1. Check the same-source same-`(league_id, instrument_id)` parquet for `day ± 3` days.
2. If any neighbour parquet exists with the same `instrument_id` → this empty day is between scrapes →
   `EXPECTED_REFDATA_CADENCE_CHANGE`.
3. Else fall through to `SOURCE_RETURNED_ZERO` (genuine missing data).

Note: requires a UTL helper `has_neighbour_parquet(bucket, league_id, instrument_id, day, window=3)` that does cheap
GCS-blob existence checks (no full read).

**Option C — combined (recommended for production)**

Try Option A first; if cadence constant is missing or empirical sampling is inconclusive, fall back to Option B. Emit a
one-shot warning at startup logging which path was taken.

## Verification

- Empirical sampling: `bq query` or local pandas on the transfermarkt PLAYER_VALUES manifest rows; group by
  `weekday(date)`, count. Expect 1-2 dominant weekdays if Option A is viable.
- After implementation: re-run Script 3 dry-run for sports. Expect proposed-upgrades to shift from
  "SOURCE_RETURNED_ZERO" → "EXPECTED_REFDATA_CADENCE_CHANGE" for PLAYER_VALUES off-day rows.

## Files affected

- `unified-api-contracts/unified_api_contracts/canonical/domain/sports/refdata_cadence.py` (NEW or extension) —
  `TRANSFERMARKT_PLAYER_VALUES_UPDATE_WEEKDAYS` constant.
- `unified-trading-library/unified_trading_library/legacy_reason_classifier.py` — extend `_classify_sports` with
  PLAYER_VALUES branch.
- `unified-trading-library/tests/unit/test_legacy_reason_classifier.py` — ≥4 new tests covering: on-cadence-day → falls
  through; off-cadence-day → EXPECTED_REFDATA_CADENCE_CHANGE; transfer data still flows through transfer-window rule (no
  regression); non-PLAYER_VALUES transfermarkt data unchanged.

## Resolution — 2026-05-14 slot 4

**Option A chosen.** Weekday set: `frozenset({1, 2})` (Tue+Wed) per `refdata_cadence.py`.

- `uac@17a0f82` — consolidated `refdata_cadence.py`: added `is_player_values_update_day(day)` helper. Removed duplicate
  `player_values_cadence.py` (was `uac@042c81c`). Exports via sports `__init__`.
- `utl@79c72bad` — `_classify_sports` imports from `refdata_cadence`; PLAYER_VALUES cadence branch fires. 5 new tests
  (Wednesday passes, Monday/Saturday → EXPECTED_REFDATA_CADENCE_CHANGE, transfer-window regression, no-league-id falls
  through). 62/62 tests pass.

## Composes with

- `sports_classifier_extension_followup_2026_05_13.md` (parent audit)
- `sports_classifier_sfi_footystats_fixture_pin_2026_05_13.md` (sibling)
- `sports_classifier_weather_no_fixture_2026_05_13.md` (sibling)
