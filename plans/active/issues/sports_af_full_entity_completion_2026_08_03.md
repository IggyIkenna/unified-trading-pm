---
doc_type: issue
title:
  Full API-Football entity completion — every AF entity at its correct scope, so the API-Football plan can be downgraded
summary: >-
  Operator directive (2026-08-03): the sports satellite campaign's docs/plans must in aggregate cover EVERY API-Football
  (AF) entity without exception — all-383-league entities fully at 383, MVP-scoped entities fully at 96 — not just the 3
  entities (FIXTURE_EVENTS/FIXTURE_STATS/FIXTURE_LINEUPS) already tracked in
  `sports_fixture_events_refetch_progress_2026_07_25.md`. Explicit business goal: once genuinely complete, the operator
  wants to downgrade the API-Football subscription tier, so full completion here is the actual deliverable, not just
  data-quality hygiene. Censused the 5 previously-untracked AF entities (PLAYER_STATS/INJURIES/STANDINGS/TEAMS/LEAGUES)
  against their own SPORTS_ENTITY_LEAGUE_COVERAGE scope — all 5 show substantial genuine gaps (381,163 total needed
  shards), plausibly explained by the SAME unconditional-MVP-pre-filter bug already found + fixed this session (todo #3,
  `instruments-service` per-fixture task-queueing loop) — these entities were already declared `None` (all-383) in the
  coverage dict from day one, but the actual fetch loop silently capped them to MVP-96 until that fix landed.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer]
tags: [sports, api-football, entity-completion, downgrade-planning, mvp-scope]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/issues/sports_fixture_events_refetch_progress_2026_07_25.md,
    /codex/02-data/mvp-scope-canonical.md,
  ]
created: 2026-08-03
priority: P1
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: ["sports_satellite_ao_dispatch_batch2, autonomous continuation, 2026-08-03 — operator directive"]
drift_direction: advance-code
---

## Why this doc exists (not folded into the parent plan or the FIXTURE_EVENTS issue doc)

`sports_satellite_ao_dispatch_batch2_2026_07_24.md` is at 996/1000 lines (hard cap) — no room to add this scope there.
`sports_fixture_events_refetch_progress_2026_07_25.md` is at 897 lines and scoped specifically to FIXTURE_EVENTS — this
is a genuinely broader initiative (5 more entities, ~381k shards, a different completion criterion: "every AF entity
done" rather than "one entity's non-canonical count converges to 0"). Both existing docs are `related:` linked here.

## The operator's actual ask (verbatim intent, 2026-08-03)

"Ensure the docs/plans/issues you are going through in aggregate will do everything AF related without exception, so
that's finally done for all leagues where relevant and MVP-only leagues where relevant. Means we can then downgrade
API-Football." — i.e., this is not an open-ended data-quality nice-to-have; there is a concrete downstream action
(reducing vendor spend) gated on this campaign's genuine completion. Every AF entity, at its correct scope, or this doc
does not close.

## The full 9-entity picture

Per `unified_api_contracts.canonical.domain.sports.provider_league_ids.SPORTS_ENTITY_LEAGUE_COVERAGE`:

| Entity           | Scope                        | Status (2026-08-03)                                                                                                            |
| ---------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| FIXTURES         | all-383                      | **DONE** — confirmed complete `sports_fixture_events_refetch_progress_2026_07_25.md`                                           |
| FIXTURE_EVENTS   | MVP-96                       | pass-3 in flight (`af-backfill-20260803-070016`), same doc                                                                     |
| FIXTURE_STATS    | all-383 (widened 2026-07-28) | queued, not yet launched — census: 69,171 non-MVP shards needed (`census_fixture_stats_lineups_widening_volume_2026_07_31.py`) |
| FIXTURE_LINEUPS  | all-383 (widened 2026-07-28) | queued, not yet launched — census: 69,165 non-MVP shards needed                                                                |
| **PLAYER_STATS** | **MVP-96**                   | **NEW this doc** — 42,368 expected, 24,928 captured, **17,440 needed**                                                         |
| **INJURIES**     | **all-383**                  | **NEW this doc** — 110,739 expected, 9,994 captured, **100,745 needed**                                                        |
| **STANDINGS**    | **all-383**                  | **NEW this doc** — 110,739 expected, 25,792 captured, **84,947 needed**                                                        |
| **TEAMS**        | **all-383**                  | **NEW this doc** — 110,739 expected, 42,998 captured, **67,741 needed**                                                        |
| **LEAGUES**      | **all-383**                  | **NEW this doc** — 110,739 expected, 449 captured, **110,290 needed** (⚠️ see caveat below)                                    |

Denominator = distinct `(date, league_id)` pairs with a captured `FIXTURES`/`FIXTURES_SCHEDULE` row (a genuine fixture
existed that day), intersected with each entity's own `get_entity_league_coverage()` scope — mirrors
`emit_empty_gaps_for_entity`'s own expected-set logic (`sports_reference_core.py:338-341`), so "needed" here means the
same gap the writer's own empty-gap emission targets, not an invented denominator. Full census:
`instruments-service/scripts/census_all_af_entities_completion_2026_08_03.py` (single UTL-client manifest read, same
credential-safe pattern as the fixed `census_fixture_events_schema_variants_2026_07_25.py`).

**Grand total needed across these 5 entities: 381,163 shards.**

## ⚠️ Caveat before launching anything — two things NOT yet verified

1. **LEAGUES' near-total absence (449/110,739 = 0.4% captured) is different in KIND from the other 4** (which show 9-39%
   captured, consistent with "MVP-only was captured pre-fix, non-MVP wasn't"). This could mean either (a) LEAGUES is
   genuinely this far behind for the same MVP-pre-filter reason, just more severely, or (b) LEAGUES is actually captured
   at a coarser real-world cadence (once per league/season, not once per fixture-date) and the per-fixture-date shard
   atom this census assumes doesn't match how the writer actually stamps LEAGUES freshness — in which case 110,290 would
   be a significant overestimate of real work, not a genuine gap. **Do not launch a LEAGUES backfill VM until this is
   checked** (read a few seconds of the LEAGUES writer path, or spot-check 2-3 already-`captured` LEAGUES objects'
   actual GCS write cadence/content to see if they cover multiple dates).
2. **The "needed shards → API calls" conversion is UNKNOWN for TEAMS/STANDINGS/LEAGUES/INJURIES.** The
   4.5875-fixtures-per-shard ratio used to estimate FIXTURE_STATS/LINEUPS/EVENTS call volume was derived from
   FIXTURE_EVENTS specifically (a genuinely per-fixture entity — one event-list call per match). TEAMS/LEAGUES are
   observed in logs as one call per **league** (`Fetched 20 teams for league=39 season=2025`), not per fixture — so a
   single API call likely satisfies MANY `(date, league)` shard-rows at once (every date that league had a fixture
   inherits the same team-roster fetch). **Do not multiply these entities' needed-shard counts by 4.5875** — that would
   badly overstate their real API-call cost. INJURIES/STANDINGS are more plausibly per-fixture-date already (injury
   reports and standings snapshots genuinely change match-to-match), closer to the FIXTURE_EVENTS model, but this is
   also unverified.

## Todos

- [ ] [SCRIPT] P1. **Spot-check LEAGUES' real write cadence** before launching anything for it — read
      `_sports_ref_canonical_blob_path`/writer call sites for `LEAGUES`, or fetch 2-3 already-`captured` LEAGUES objects
      and check whether they're written per-date or per-season, to confirm or correct the 110,290 estimate above.
- [ ] [SCRIPT] P1. **Launch FIXTURE_STATS all-leagues backfill** (`--entity FIXTURE_STATS 2020-06-06 <today>`, daily
      stop-at-quota-exhaustion/resume-at-reset per operator's 2026-07-31 ruling) once the FIXTURE_EVENTS pass-3
      singleton lock clears. Already-staged census: `census_fixture_stats_lineups_widening_volume_2026_07_31.py`.
- [ ] [SCRIPT] P1. **Launch FIXTURE_LINEUPS all-leagues backfill** the same way, after FIXTURE_STATS converges.
- [ ] [SCRIPT] P1. **Launch PLAYER_STATS MVP-96 backfill** (`--entity PLAYER_STATS 2020-06-06 <today>`) once the
      singleton lock frees up — 17,440 needed shards, same MVP scope as FIXTURE_EVENTS (worth checking this entity's
      census script for the SAME fixture_id/af_fixture_id column bug already found + fixed in the FIXTURE_EVENTS census,
      if a dedicated recovery-style census is ever built for it).
- [ ] [SCRIPT] P2. **Launch INJURIES all-leagues backfill** (100,745 needed shards) — likely per-fixture-date cadence,
      apply the daily stop/resume discipline.
- [ ] [SCRIPT] P2. **Launch STANDINGS all-leagues backfill** (84,947 needed shards) — same discipline.
- [ ] [SCRIPT] P2. **Launch TEAMS all-leagues backfill** (67,741 needed shards, BUT likely 1 call/league not 1
      call/shard — confirm real call cost before estimating timeline; may complete far faster than the shard count
      implies).
- [ ] [SCRIPT] P2. **Launch LEAGUES all-leagues backfill** (110,290 needed shards, PENDING the spot-check todo above —
      do not launch blind).
- [ ] [SCRIPT] P0. **Re-census all 9 entities once every backfill above completes**, confirm every needed-count
      converges to ~0 (accounting for genuine honest-absence floors per entity, same pattern as FIXTURE_EVENTS'
      ~1,943-stub floor), and only then close this doc + notify the operator the full AF completion is genuinely done
      and the API-Football plan can be downgraded.

## Sequencing note

All of these share the SAME `af-backfill-*`/`af-audit-*` singleton lock (one API-Football-consuming VM at a time, shared
daily quota) as the already-in-flight FIXTURE_EVENTS pass-3 and the queued FIXTURE_STATS/FIXTURE_LINEUPS work — this is
a genuinely sequential, multi-day-to-multi-week campaign, not something to parallelize across VMs. Priority order above
(P1 before P2) reflects: entities already declared as "widened this session" (FIXTURE_STATS/LINEUPS/ PLAYER_STATS)
before the newly-discovered-but-not-yet-widened-in-conversation entities (INJURIES/STANDINGS/TEAMS/ LEAGUES), though all
are genuinely in scope for the operator's "no exceptions" directive.
