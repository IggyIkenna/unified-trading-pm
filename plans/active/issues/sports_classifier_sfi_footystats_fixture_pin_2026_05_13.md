---
title: "Sports classifier — SFI_PROGRESSIVE_STATS + FOOTYSTATS_* should pin to fixture availability"
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
    - sports_classifier_player_values_cadence_2026_05_13.md (sibling P1)
    - sports_classifier_weather_no_fixture_2026_05_13.md (sibling P1)
---

## What I found

`_classify_sports` in `unified_trading_library/legacy_reason_classifier.py:191` lacks a
fixture-availability check for `soccer_football_info` (SFI_PROGRESSIVE_STATS) and `footystats`
(FOOTYSTATS_MATCHES / FOOTYSTATS_ODDS / FOOTYSTATS_PREDICTIONS) sources.

- **SFI_PROGRESSIVE_STATS**: SFI only emits progressive stats during a live match. Without a
  scheduled fixture for `(league_id, day)`, no progressive stats can exist. Current behaviour:
  rows fall through to `SOURCE_RETURNED_ZERO` (treated as honest failure) when they're actually
  expected empties.
- **FOOTYSTATS**: Same logic. Footystats' coverage is fixture-driven for matches/odds/predictions.
  Current behaviour has season-status as the only check, which is coarser-grained than fixture
  existence (in-season but no-fixture days are still incorrectly classified).

## Why it matters

The `api_football_fixtures` manifest IS the canonical SSOT for "what matches exist on a given
(league, day)". Without pinning these sources to the fixtures manifest, the reconciler's
classification of empties is wrong — we lose the ability to distinguish:

- Legitimate no-fixture day (✅ honest empty, no action needed)
- Real source failure (🔴 needs operator triage)

This compounds with the Script 3 sports apply-flips that are already held — we need correct
classifications BEFORE we can flip them.

## Operator direction (2026-05-13 Ikenna)

> "SFI only covers matchdays — can't have stats without a fixture. Should be pinned to fixtures.
> Same with footystats — the api_football fixtures IS the rule for what's available apart from
> known leagues that sfi or footystats don't cover (or aren't supposed to as they aren't in the
> prediction leagues in UAC)."

## Implementation

1. **UAC**: Add `EXPECTED_NO_FIXTURE` to `EmptyConfirmedReason` StrEnum +
   `EMPTY_CONFIRMED_REASONS` frozenset in
   `unified_api_contracts/canonical/crosscutting/honest_coverage.py`. Description: "No fixture
   scheduled for this (league_id, day) per api_football fixtures manifest — fixture-pinned
   sources cannot emit data without a fixture."

2. **UTL helper** (NEW): `unified_trading_library/sports_fixtures.py` with
   `is_fixture_scheduled(league_id: str, day: str) -> bool`. Reads the api_football fixtures
   manifest (instruments-service catalogue bucket). LRU cache + 60s TTL per manifest concurrency
   principle.

3. **UTL classifier extension**: In `_classify_sports` at
   `unified_trading_library/legacy_reason_classifier.py:191`, BEFORE the existing season-status
   check, add:
   ```python
   if source in {"soccer_football_info", "footystats"} and league_id and day_dt is not None:
       if not is_fixture_scheduled(league_id, day):
           return "EXPECTED_NO_FIXTURE"
   ```
   Ordering: the source-coverage-matrix check (understat-doesn't-cover-league pattern) MUST run
   first so out-of-coverage leagues short-circuit before we hit the fixtures lookup (waste).

4. **Tests** (≥4 unit tests): scheduled fixture → falls through; no fixture → EXPECTED_NO_FIXTURE;
   league not covered by source → EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE (overrides fixture check);
   pre-coverage-start date → EXPECTED_PRE_SOURCE_COVERAGE_START (overrides fixture check).

## Verification

- After implementation, re-run Script 3 dry-run for sports. Expect: candidates count unchanged
  (~1.87M), but the proposed-upgrades classification shifts from "SOURCE_RETURNED_ZERO" → mix of
  "EXPECTED_NO_FIXTURE" + "EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE" + "SOURCE_RETURNED_ZERO" (the
  real failures).

## Resolution — 2026-05-14 slot 4

- `uac@435abae` — `EXPECTED_NO_FIXTURE` already in `EmptyConfirmedReason` (pre-existing).
- `utl@330864f6` — `is_fixture_scheduled(league_id, day)` helper already in `sports_fixtures.py` (pre-existing).
- `utl@79c72bad` — `_classify_sports` fixture-pin branch: `source in {"soccer_football_info", "footystats", "open_meteo"}`
  + `not is_fixture_scheduled(league_id, day)` → `EXPECTED_NO_FIXTURE`. 5 fixture-pin tests added
  (SFI/footystats/open_meteo no-fixture, SFI with fixture falls through, api_football not pinned). 62/62 tests pass.

**NOTE**: The fixture-pin rule also covers `open_meteo` (weather), so `sports_classifier_weather_no_fixture_2026_05_13.md`
read-side is resolved by the same commit. Weather write-side prevention in instruments-service is deferred.

## Composes with

- `sports_classifier_extension_followup_2026_05_13.md` (parent audit — partial finding)
- `sports_classifier_player_values_cadence_2026_05_13.md` (sibling, same operator direction)
- `sports_classifier_weather_no_fixture_2026_05_13.md` (sibling, same operator direction)
- `classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md` (sibling P1 on Script 3 — both
  gate sports apply-flips)
