---
doc_type: issue
title:
  Sports G1 non-canonical-league NOISE population does NOT match either the plan's cited 1,437-league/~106k-row figure
  or §U's approved 489-pair/10,869-row purge — live census shows a different, larger, and partly-dangerous population;
  `delete_noncanonical_sports_leagues_2026_06_25.py` has a scope bug that would also delete un-migrated canonical-league
  market data
summary: >-
  Dispatched to check whether the G1 "non-canonical-league NOISE wipe" population (~1,437 leagues/~106k rows, per
  `sports_closeout_track_s2_foldin_2026_07_25.md` and `instruments_foundation_completeness_2026_06_24.md`) is the SAME
  population as the already-operator-approved §U purge (489 league-seasons/10,869 rows,
  `sports_consolidated_closeout_2026_07_19.md` Track V). A live read-only census against the production
  `availability_index.parquet` (instruments-store-sports-prd) shows NEITHER figure matches current reality, under any of
  3 canonical-set definitions tried. Worse: the naive full-registry-canonical cut (268,094 rows / 780 league_ids)
  contains 5 of the exact symbolic league_id aliases (`PREMIER_LEAGUE`, `CHAMPIONSHIP`, `PRIMERA_DIVISION`,
  `2._BUNDESLIGA`, `FIRST_DIVISION_A`) already flagged as a P0 catastrophic-delete risk in
  `sports_league_id_namespace_migration_2026_07_20.md` — because `delete_noncanonical_sports_leagues_2026_06_25.py`
  defines a `_FOOTBALL_DATA_TYPES` constant but never actually uses it to filter, so it would also delete 250,327
  `trades`/`odds_horizon_bucket` rows that are real, un-migrated (not yet casing-final) canonical-league market data
  belonging to a SEPARATE, still-in-flight Track V/K1-K2 migration — not out-of-universe NOISE. Per this todo's own
  instruction ("If the census shows a genuinely different population, STOP and report the discrepancy — do not purge an
  unapproved population"), NO purge was executed. This doc records the census and the newly-found script bug as
  actionable follow-ups.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-trading-pm]
scope: [engineer]
tags: [sports, league-id, canonical, noise-wipe, census, discrepancy, delete-safety]
related:
  [
    /plans/active/sports_closeout_track_s2_foldin_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
  ]
created: "2026-07-27"
source:
  sports_closeout_track_s2_foldin_2026_07_25.md todo "Sports P2a sub-item (a) — G1 non-canonical-league NOISE wipe"
resolved_by:
locked_by:
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: data_engineering
drift_direction: advance-code
---

# Sports G1 NOISE population mismatch + `delete_noncanonical_sports_leagues_2026_06_25.py` scope bug

## What I found

**The dispatched todo** (`sports_closeout_track_s2_foldin_2026_07_25.md`, "Sports P2a sub-item (a)") asked: is the
~1,437-league/~106k-row G1 NOISE population the SAME as (or a strict superset of) the already-operator-approved
489-pair/10,869-row §U purge? If yes, execute the §U purge on the residual. If genuinely different, stop and report.

I ran a live, read-only census against the production `instruments-store-sports-prd-central-element-323112` bucket's
consolidated `_index/availability_index.parquet` (6,860,486 rows, single read — no new whole-corpus GCS walk) using the
exact canonical-set derivation the G1 delete script
(`instruments-service/scripts/delete_noncanonical_sports_leagues_2026_06_25.py`) already uses
(`unified_api_contracts.sports.get_expected_leagues_for_source("api_football")`).

**Neither cited figure matches current reality, under any canonical-set cut**:

| Canonical set used                                    | Non-canonical rows | Unique league_ids |
| ----------------------------------------------------- | -----------------: | ----------------: |
| Plan's G1 figure (as originally measured, 2026-06-27) |           ~106,000 |             1,437 |
| §U's approved purge (Track V, 2026-07-20)             |             10,869 |               489 |
| **Live: FULL registry (383 leagues) as canonical**    |        **268,094** |           **780** |
| **Live: MVP-scope (96 leagues) as canonical**         |      **1,476,781** |         **1,067** |
| **Live: FULL registry, football data_types only**     |         **17,767** |           **734** |

(MVP-scope is the wrong cut for a "not in registry" wipe — it also flags genuinely-registered, just non-MVP leagues, so
it over-counts by design; included for completeness only.)

**Critical safety finding — the full-registry non-canonical set contains real, in-scope canonical-league data under
stale symbolic names.** The 5 exact aliases already named as a P0 delete risk in
`sports_league_id_namespace_migration_2026_07_20.md` (`PREMIER_LEAGUE`, `CHAMPIONSHIP`, `PRIMERA_DIVISION`,
`2._BUNDESLIGA`, `FIRST_DIVISION_A`) are STILL present in the live index under those raw names — 160,909 rows total,
100% split between `trades` (125,704) and `odds_horizon_bucket` (35,205). These are NOT football reference/fixture rows;
per `sports_consolidated_closeout_2026_07_19.md` Track V, `trades`/`odds_horizon_bucket` casing migration is a SEPARATE,
still-in-flight effort ("TRADES stable but NOT casing-final...`odds_horizon_bucket`/`batch_footystats` still
un-migrated"). They are real, current, un-migrated canonical-league market data — not out-of-universe NOISE — and would
be silently destroyed by an `--apply` run of the G1 delete script as currently written.

**Root cause of the safety gap**: `delete_noncanonical_sports_leagues_2026_06_25.py` defines a `_FOOTBALL_DATA_TYPES`
frozenset (lines 52-78) that is never referenced anywhere else in the file — dead code. `_delete_noncanonical_rows()`
filters ANY row with a non-blank `league_id`, regardless of `data_type`, so it inadvertently also catches
`trades`/`odds_horizon_bucket` rows that happen to carry a football-style `league_id` value from the pre-canonical write
path. The script's own docstring/intent ("Non-canonical league IDs are identified as: football leagues...") was never
actually enforced in code.

**Restricting to football-only data_types** (excluding `trades`/`odds_horizon_bucket`) gives 17,767 rows / 734
league_ids — closer in order of magnitude to both cited figures but still not an exact or provable match to either. Of
those, 632 league_ids (14,538 rows) are pure numeric junk IDs (e.g. `1`, `10`, `1000` — never valid league identifiers),
and 102 are real alpha league names genuinely absent from the registry (lower-tier/reserve/youth/ continental
competitions, e.g. `ENGLAND_NATIONAL_LEAGUE`, `GERMANY_OBERLIGA_BAYERN_NORD`, `WORLD_CONMEBOL_LIBERTADORES`) — none of
which are symbolic aliases of an in-scope canonical league.

I could not mechanically PROVE the football-only 17,767/734 cut is a strict superset of §U's 10,869/489 cut: §U's
population was defined over raw FIXTURES parquet CONTENT (`af_league_id`, a NUMERIC field, filtered to blank-`round`
rows specifically — see `instruments-service/scripts/derive_sports_fixture_round_2026_07_18.py` for the only place
`af_league_id`+`round` co-occur in this codebase), while my census reads the consolidated MANIFEST index (`league_id`, a
STRING field, no `round`/season columns exist at the manifest level). Confirming strict-superset would require a
corpus-wide read of the raw FIXTURES parquet content joined against the registry's numeric `api_football_id` — a
materially larger, separate operation, not something to do inside this 1-hour-scoped todo without flagging it first.

## Why it matters

- Per this todo's own explicit instruction, a genuinely-different (and partly numerically-unverifiable) population must
  NOT be purged against an approval that was scoped to a different, smaller population. No purge was executed.
- The `_FOOTBALL_DATA_TYPES`-defined-but-unused bug means the EXISTING delete script is unsafe to run as-is against the
  CURRENT live index — it would delete 250,327 non-football rows outside G1's own stated scope, 160,909 of them provably
  real canonical-league data (the 5 confirmed aliases) still pending the separate Track V casing migration. This is a
  live landmine: the plan's own checkbox history shows this exact script was already checked `[x]` once
  (`sports_p2_history_apifootball_2015_to_present_2026_06_27.md` todo 1) with the honest caveat "WIPE STILL NEEDS RUN" —
  if any future worker runs `--apply` without re-reading this finding, it silently destroys real trading data.
- Neither historical population figure (106k/1,437 or 10,869/489) is reproducible from the live index today, meaning the
  plan corpus's own tracked scale for this population has drifted and needs re-baselining once the fix below ships.

## Recommended decision / next steps

1. [x] ✅ **[CODE] P1 — Fix the scope bug — DONE 2026-07-27, `instruments-service@7409c5b1`.** Wired
       `_FOOTBALL_DATA_TYPES` into `_delete_noncanonical_rows()`'s mask so the non-canonical-league deletion only ever
       considers rows whose `data_type` is a football data type, never `trades`/`odds_horizon_bucket`/other MTDS types
       (a row with no `data_type` column at all, e.g. the legacy seed shape, falls back to the prior behavior). 4 new
       unit tests in `tests/unit/scripts/test_delete_noncanonical_sports_leagues_2026_06_25.py`, all passing; full QG
       green. (repo: instruments-service)
2. **[DATA] P2 — Operator/judgment**: decide which canonical-set definition is authoritative for a "not in registry"
   wipe (full 383-league registry, not MVP-96 — MVP-scope incorrectly flags valid non-MVP registered leagues) and
   re-baseline the G1 NOISE population's tracked figure in the plan corpus against a fresh, football-only, fixed-script
   dry-run once (1) ships.
3. **[DIAG] P2 — Reconcile §U's exact population**: a fresh read of raw FIXTURES parquet content (`af_league_id` +
   `round`), scoped and single-walk, to determine whether §U's 10,869/489 population is in fact a subset of the
   football-only 17,767/734 manifest-index cut measured here, before treating §U's original approval as covering any
   part of the current residual.
4. **[REVIEW] P3 — Corpus hygiene**: the plan's own text ("§U... already-approved... the scale differs by ~10x, so this
   must not be assumed") anticipated exactly this outcome; once (1)-(3) land, update
   `sports_closeout_track_s2_foldin_2026_07_25.md`'s G1 sub-item with the corrected figures and this doc's citation.

## Census script (read-only, no writes)

Ran from `instruments-service/` venv, `GCP_PROJECT_ID=central-element-323112`, single read of
`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet` via `gcsfs`, canonical sets
loaded via `unified_api_contracts.sports.get_expected_leagues_for_source("api_football")`. No `--apply` of any delete
script was run; no snapshots, no writes, no GCS deletes.
