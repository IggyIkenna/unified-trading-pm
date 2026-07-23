---
doc_type: issue
title: PRIMERA_DIVISION (Chile) Odds-API team names miss team_mappings.py alias dict — 43% of real fixtures unresolvable
summary: |
  While shipping the odds-tick af_fixture_id row-level join (operator decision, option A of the E1 finding —
  instruments-service/docs/SPORTS_INSTRUMENTS.md § "odds<->instruments row-level join-key gap"), measured the real
  match rate against 4 real recent days of already-captured production odds ticks (2026-06-13/14/19/20, the most
  recent days with real batch_odds_api data as of 2026-07-09). Of 180 distinct real fixtures observed, 119 matched
  (66.1%); the ENTIRE 61-fixture gap is PRIMERA_DIVISION (Chile Primera, AF league_id 265) — 81/142 matched (57.0%),
  every miss classified UNRESOLVED_TEAM_NAME (zero NO_FIXTURE_DATA misses, i.e. instruments-service's own fixture
  data was present and correct for every case). SEGUNDA_DIVISION was 38/38 (100%) in the same window. Root cause:
  Odds-API-sourced Chilean club names (e.g. "Coquimbo Unido", "O'Higgins", "Deportes Concepción", "Universidad
  Católica (CHI)") are not present in unified-api-contracts'
  unified_api_contracts/external/api_football/team_mappings.py alias dict (API_FOOTBALL_TO_CANONICAL /
  _UNIVERSAL_REVERSE), so validate_team_resolution() raises TeamResolutionError for them — this is a PRE-EXISTING
  team-name-coverage gap, not a bug in the new join code (the join code correctly reports the honest
  UNRESOLVED_TEAM_NAME status rather than silently mismatching or guessing). Not fixed as part of the join-key task
  because the correct alias additions need per-team verification against API-Football's own official names (a
  guessed rewrite risks new, differently-wrong aliases — same caution as the sibling league_id="UNKNOWN" issue doc).
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [unified-api-contracts, instruments-service, market-tick-data-service]
scope: [engineer]
tags: [sports, team-mappings, alias-coverage, data-correctness, odds-api, api-football, chile, primera-division]
related:
  [
    instruments-service/docs/SPORTS_INSTRUMENTS.md,
    plans/active/issues/sports_manifest_unknown_league_id_2026_07_08.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-09
last_updated: 2026-07-09
parent_epic: sports_master
priority: P2
source:
  SUB_AGENT_MANDATORY_RULES dispatch (this session) — discovered while measuring the real af_fixture_id match rate for
  the odds<->instruments row-level join-key fix (instruments-service/docs/SPORTS_INSTRUMENTS.md).
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# PRIMERA_DIVISION (Chile) Odds-API team names miss the team_mappings.py alias dict

## How I found this

Shipping the odds-tick → instruments-service `af_fixture_id` row-level join (see
`instruments-service/docs/SPORTS_INSTRUMENTS.md` § "odds↔instruments row-level join-key gap"), the task asked for a real
measured match rate against real, already-captured production data — not a synthetic estimate. I read the real
`market-data-tick-sports-prd-central-element-323112` and `instruments-store-sports-prd-central-element-323112` buckets
directly (real GCP credentials, `central-element-323112`) for the 4 most recent days with real captured
`pipeline_mode=batch_odds_api` odds ticks as of 2026-07-09 (`2026-06-13`, `2026-06-14`, `2026-06-19`, `2026-06-20` —
most European leagues are off-season in June, so only 2 of the 33 Prediction leagues had real captured odds data in this
window), and ran the exact shipped `FixtureIdResolver` logic against them.

## What I found

| League                     | Matched | Total | Rate  |
| -------------------------- | ------- | ----- | ----- |
| `SEGUNDA_DIVISION` (Spain) | 38      | 38    | 100%  |
| `PRIMERA_DIVISION` (Chile) | 81      | 142   | 57.0% |

All 61 PRIMERA_DIVISION misses are `UNRESOLVED_TEAM_NAME` (not `NO_FIXTURE_DATA`) — instruments-service's own
`sports_reference/.../entity=fixtures/league=PRIMERA_DIVISION/fixtures.parquet` for these days DOES have the correct
API-Football fixture rows (I confirmed this directly — the resolver never hit a missing-fixtures-file case for this
league). The failure is 100% on the Odds-API side: `validate_team_resolution(name, provider="odds_api")` raises
`TeamResolutionError` for these real team-name strings because they are not present in
`unified_api_contracts/external/api_football/team_mappings.py`'s `API_FOOTBALL_TO_CANONICAL` / `_UNIVERSAL_REVERSE`
alias index at all — not a normalisation miss (accent/case), a genuinely absent entry.

Sample real unresolved (home, away) pairs seen across the 4-day window:

- `Coquimbo Unido` vs `O'Higgins`
- `Deportes Concepción` vs `Deportes Limache`
- `Universidad Católica (CHI)` vs `Universidad de Concepción`

(Not exhaustive — re-run the measurement script against a fuller date range to get the complete unresolved-team roster
before doing the alias-dict fix, since only ~5 real Chile Primera fixtures were captured in this 4-day sample.)

## Why it matters

This is a real, currently-active data-quality gap, independent of the new join feature: `validate_team_resolution()` is
also used by `_build_fixture_rows()` itself to build the odds tick's own `instrument_id` (`home_id`/`away_id`) — so
PRIMERA_DIVISION odds ticks that hit this gap ALSO fall back to `build_team_id()` (a raw slug, not the validated
canonical id) for their `instrument_id`'s HOME/AWAY segment, a pre-existing, separate symptom of the same root cause,
already tracked via `unresolved_teams` warnings in `download_batch()`'s logs (grep `MAPPING GAP` in MTDS's sports
adapter logs to see the live count). The new `af_fixture_id` join surfaces this gap MORE visibly (a structured
`af_fixture_match_status` column, not just a log line), which is what led to this finding.

## Recommended decision

Add the missing Chilean club name aliases to `unified_api_contracts/external/api_football/team_mappings.py`'s
`_CROSS_PROVIDER_ALIASES` (per that module's own `TeamResolutionError` message: "Add it to `_CROSS_PROVIDER_ALIASES` in
team_mappings.py"). Requires a full pull of API-Football's own official Chile Primera team-name list (via
`/teams?league=265`) to verify the correct canonical spelling per team before adding aliases — a guessed rewrite risks
introducing a different, silently-wrong mapping (same caution the sibling
`sports_manifest_unknown_league_id_2026_07_08.md` issue applied). Scope this as its own small UAC-repo task; it is NOT
part of the af_fixture_id join-key work (that work is complete and correctly reports the honest `UNRESOLVED_TEAM_NAME`
status for these fixtures rather than masking the gap).

## Evidence

Real production GCS read, 2026-07-09, `central-element-323112`, buckets `market-data-tick-sports-prd-*` +
`instruments-store-sports-prd-*`. Verification script logic mirrors the shipped
`market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/fixture_id_resolver.py`
(`FixtureIdResolver`) exactly — no separate/divergent matching heuristic was used to produce these numbers.

## RE-TRIAGE (2026-07-23)

**Verdict: STILL OPEN, ACCURATE — re-measured live, essentially unchanged.** Re-read the same 4 real production days
(`2026-06-13/14/19/20`) directly from `market-data-tick-sports-prd-central-element-323112` and re-ran
`validate_team_resolution()` (current code) against every real PRIMERA_DIVISION team name observed (06-20 had zero
PRIMERA_DIVISION objects this time; 06-13/14/19 yielded 21,322 rows / 7 distinct fixtures): **4/7 fixtures fully resolve
(57.1%)** — statistically the same as the original 57.0% (81/142 team-instance rate). Unresolved fixtures today:
`Coquimbo Unido` vs `O'Higgins`, `Deportes Concepción` vs `Deportes Limache`, `Universidad Católica (CHI)` vs
`Universidad de Concepción` — the EXACT SAME 3 sample pairs this doc originally cited.

**Notable, worth flagging**: a related fix DID land in the interim —
`unified_api_contracts/external/api_football/team_mappings.py` now has a `CHILE_PRIMERA_TEAM_ALIASES` dict (15 teams,
dated "Phase-E L2a, 2026-07-18" in code comments, filed for a different SA odds-join gap, not this doc) that added
`OHIGGINS` and `UNIVERSIDAD_CATOLICA` aliases — which is exactly why `O'Higgins` and `Universidad Católica (CHI)` now
resolve. But it did NOT add `Coquimbo Unido`, `Deportes Concepción`, `Deportes Limache`, or `Universidad de Concepción`
— the counterpart teams in this doc's own named sample — so every one of the 3 originally-cited unresolved fixtures is
STILL unresolved today, just for the other side of each pairing. Confirmed live:
`validate_team_resolution("Coquimbo Unido", provider="odds_api")` / `"Deportes Concepción"` / `"Deportes Limache"` /
`"Universidad de Concepción"` all still raise `TeamResolutionError` ("not in any alias dict"). No status change — this
is a real, still-open, precisely-unchanged gap; the fix that landed happened to miss exactly this doc's cited teams.
