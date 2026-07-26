---
doc_type: issue
title:
  Per-fixture sports ENRICHMENT (stats/events/lineups/player-stats) silently followed the wider FIXTURES
  curated-universe denominator (383 leagues) instead of MVP scope (96 leagues) — root cause, fix shipped
summary: >-
  Operator flagged (2026-07-26, mid-monitoring of the FIXTURES curated-universe backfill): "for the enrichment features
  we only care about mvp leagues so the 94 not the 300+... else its way too many api football queries." Traced the
  actual per-fixture enrichment call path (`sports_reference.py::_fetch_sports_reference_data` →
  `sports_reference_fixtures.py::_run_per_fixture_enrichment`) and confirmed the concern was real and unenforced: when
  `fixture_ids` comes from `fixture_ids_override` (the URDI-sourced primary path), it spans whatever FIXTURES already
  captured — now 383 leagues post the 2026-07-24 curated-universe widening — with NO league filter before the 4
  expensive per-fixture calls (FIXTURE_STATS/FIXTURE_EVENTS/FIXTURE_LINEUPS/PLAYER_STATS). The UAC
  `SPORTS_ENTITY_LEAGUE_COVERAGE` "expected" registry for these same 4 entities also declared `None` (all leagues)
  instead of the MVP set. Both fixed and shipped same-session.
status: resolved
resolved_by: unified-api-contracts@f674033f, instruments-service@b00e4433
nature: issue
asset_group: [sports]
stage: [data, features]
repos: [unified-api-contracts, instruments-service]
scope: [engineer]
tags: [mvp-scope, sports, api-football, enrichment, quota, curated-universe, cost]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md,
    /codex/02-data/mvp-scope-canonical.md,
  ]
created: 2026-07-26
last_updated: 2026-07-26
priority: P1
parent_epic: infrastructure_master
source: >-
  Operator, mid-session while monitoring the FIXTURES curated-universe backfill VM (af-backfill-20260726-110610): "for
  the nerichment features we only care about mvp leagues so the 94 not the 300+ right else its way too many api football
  queries to get all that data. check the plans and code and codex to enforce this."
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
locked_by:
depends_on: []
---

# Sports enrichment MVP-scope leak — root cause + fix

## Root cause

Two independent gaps, both traced by reading the actual code path (not assumed):

1. **`sports_reference.py::_fetch_sports_reference_data`** — the per-fixture enrichment call
   (`_run_per_fixture_enrichment`) received `fixture_ids` straight from `_resolve_fixture_ids()` with only a
   `recovery_fixture_ids` allowlist filter (a targeted-recovery feature, not a standing MVP gate). When
   `fixture_ids_override` is supplied (the common path — fixture IDs already resolved by the URDI instruments fetch),
   those IDs span whatever FIXTURES already captured, which is now the full curated-universe denominator
   (`get_expected_leagues_for_source("api_football")`, 383 leagues) — NOT the 96-league MVP/prediction-scope set. The
   fallback API-fetch path (`_fetch_fixture_ids_via_api`, only used when URDI returns 0 instruments) happened to already
   enumerate the 94/96-league classification tiers directly, so it was NOT exposed to this leak — the primary path was.
2. **UAC `SPORTS_ENTITY_LEAGUE_COVERAGE`** (`provider_league_ids.py`) declared `FIXTURE_STATS` / `FIXTURE_EVENTS` /
   `FIXTURE_LINEUPS` / `PLAYER_STATS` as `None` ("expected on all fixture dates" = all leagues in the full denominator),
   the same value as genuinely all-leagues-expected entities like TEAMS/STANDINGS/INJURIES. This meant the preflight
   freshness check (`process_preflight.py`) never had a reason to skip these entities on days whose only fixtures were
   non-MVP leagues.

Neither gap was a regression — both predate the 2026-07-24 curated-universe widening but were latent (94→96 vs the
non-MVP tiers being empty back then). The widening (94/96 → 383 leagues) is what turned a latent scoping gap into a real
~4x API-Football quota multiplier for per-fixture enrichment.

## Fix shipped

- **`unified-api-contracts@f674033f`**: new public SSOT `get_mvp_football_league_ids()`
  (`canonical/domain/sports/league_data.py`) — the single implementation (the pre-existing private
  `_mvp_scope_rules._mvp_football_league_ids()` now delegates to it). `SPORTS_ENTITY_LEAGUE_COVERAGE` for the 4
  per-fixture enrichment entities now uses this MVP set instead of `None`. 3 new/updated test files verify the accessor
  matches `MVP_SCOPE["sports"].leagues` and that a non-MVP widened-universe-only league is excluded from coverage.
- **`instruments-service@b00e4433`**: `_fetch_sports_reference_data` now filters `fixture_ids` to the MVP league set
  (unconditionally, both `fixture_ids_override` and fallback paths) immediately before calling
  `_run_per_fixture_enrichment`, logging the skip count in the same style as the existing recovery-filter log line. A
  fixture with NO resolved league mapping is KEPT, not dropped (the filter can only prove a fixture is out of scope,
  never assume it from a missing mapping — fail-open to avoid silently losing legitimate MVP data on a mapping gap). 2
  new regression tests (non-MVP fixture excluded from all 4 adapter calls; unmapped fixture kept). Full sports
  orchestrator suite re-run clean (218 passed, 0 regressions).

**Verified NOT affected**: the currently-running FIXTURES backfill VM (`af-backfill-20260726-110610`,
`sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s curated-universe backfill) is a FIXTURES-only run
(`sports-entity=FIXTURES`, 0 per-fixture enrichment entities requested per its own run.log —
`"Per-fixture enrichment: N fixtures x 0 entities = 0 calls queued"`). FIXTURES-level schedule/existence data is
CORRECTLY meant to span the full 383-league curated universe — only per-fixture ENRICHMENT is MVP-restricted. No
relaunch of that VM was needed for this fix.

## Deferred follow-up (NOT fixed this session — separate, riskier concern)

**Carried forward to `/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md` § O on
archive of this doc (2026-07-26)** — tracked there, not lost with this archive.

- [ ] [DATA] P2. **`emit_empty_gaps_for_entity`** (`instruments-service/.../sports_reference_core.py`) — the
      honest-absence gap emitter for these same 4 per-fixture entities — still hardcodes
      `get_expected_leagues_for_source("api_football")` (383 leagues) as its "expected" denominator, independent of
      `SPORTS_ENTITY_LEAGUE_COVERAGE`. This means completeness/coverage tracking for FIXTURE_STATS/FIXTURE_EVENTS/
      FIXTURE_LINEUPS/PLAYER_STATS will show the ~287 non-MVP widened leagues as permanently `expected_unattempted`
      (since capture now deliberately never touches them) rather than an honest "out of scope by policy" absence. This
      is a coverage/reporting-accuracy concern, NOT a call-volume bug (this session's fix already stops the API calls) —
      deliberately NOT touched here because `emit_empty_gaps_for_entity` is a shared function whose honest-absence
      semantics have been the subject of multiple past incidents this session's context surfaced (several "RETRACTED"
      analyses in `sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`). **Done when**: either
      `emit_empty_gaps_for_entity` branches its expected-denominator by data_type (MVP set for the 4 enrichment
      entities, full set otherwise), or an operator decision accepts the wider denominator as intentional for these
      entities and documents why.
