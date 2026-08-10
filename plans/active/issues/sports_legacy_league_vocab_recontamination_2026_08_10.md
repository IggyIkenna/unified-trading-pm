---
doc_type: issue
title: >-
  The SEGUNDA_DIVISION→LA_LIGA_2 league-vocabulary migration is being RE-CONTAMINATED by live writers — SEGUNDA_DIVISION
  and LA_LIGA_2 are BOTH registered league keys, and the standings/teams + footystats write paths still emit
  SEGUNDA_DIVISION (evidence to 2026-08-07). Delete pass blocked under delete-safety Part 3.
summary: >-
  While completing the migration for `sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`
  (dispatched via `sports_closeout_track_x_hygiene-006`), this session established: (1) the migration COPY is largely
  complete — 12,988 of 13,916 contaminated `instruments-store-sports-prd` objects have byte-identical canonical twins
  (delete-eligible), 928 have differing twins (quarantine, no-migrate-first); but (2) the write path is NOT actually
  closed — `league=SEGUNDA_DIVISION` objects for standings/teams (batch_api_football) were written on 2026-08-06 AND
  2026-08-07, dual-written alongside `league=LA_LIGA_2` for the same league the same day, and footystats_matches carry
  `available_at=2026-08-07`. Root causes: `api_football_reference.py:165` still builds the league key via the raw
  `build_league_id(country, name)` slug (not the registry-first resolver shipped 2026-08-04),
  `FOOTYSTATS_HISTORICAL_SEASON_IDS` maps 15+ footystats competition ids to SEGUNDA_DIVISION, and the UAC league
  registry registers BOTH SEGUNDA_DIVISION and LA_LIGA_2 (identical season structure) so the write-universe gate accepts
  both. Because a live writer still emits the contaminated vocabulary, the delete pass is `no-migrate-first`
  (delete-safety protocol Part 3 fails) and the migration done-when cannot be durably met until the writers emit only
  LA_LIGA_2.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-api-contracts, unified-trading-pm, market-tick-data-service]
scope: [engineer]
tags: [sports, canonical, league-id, contamination, data-correctness, ssot-contradiction]
related:
  [
    /plans/active/issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md,
    /plans/active/sports_closeout_track_x_hygiene_2026_07_25.md,
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
  ]
created: "2026-08-10"
author: slot-22 worker (data_engineering)
source: sports_closeout_track_x_hygiene-006 migration completion attempt (2026-08-10)
resolved_by:
locked_by:
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

# Sports league-vocabulary migration re-contamination (SEGUNDA_DIVISION vs LA_LIGA_2)

## What I found

While completing the 9,733-object `instruments-store-sports-prd` migration (the plan-level P2 checkbox in
`sports_closeout_track_x_hygiene_2026_07_25.md`), a fresh census + twin-coverage + writer audit found the write path is
NOT actually closed for the `SEGUNDA_DIVISION` vocabulary. Migration state today:

**Census (2026-08-10, full-bucket streaming walk, `instruments-store-sports-prd-central-element-323112`):** 13,916
in-scope contaminated objects still present — `SEGUNDA_DIVISION` 13,893, `BRAZIL_SERIE_A` 3, `ENGLAND_PREMIER_LEAGUE` 20
(matches the 2026-08-09 dry-run's 13,911 plan size; essentially nothing deleted).

**Twin coverage (delete-pass dry-run, same-run `gcs_describe_object` size+crc32c vs canonical twin):**

- 12,988 / 13,916 have a byte-identical canonical twin (`SEGUNDA_DIVISION`→`LA_LIGA_2`, `BRAZIL_SERIE_A`→`BRASILEIRAO`,
  `ENGLAND_PREMIER_LEAGUE`→`EPL`) — delete-eligible under Parts 1/2/5.
- 928 / 13,916 have a twin that EXISTS but DIFFERS (src ~35KB vs twin ~14.5KB) — concentrated in `batch_footystats`
  `footystats_matches` (846) + `batch_api_football` (82: injuries 64, fixtures* 18, plus BRAZIL_SERIE_A 3 /
  ENGLAND_PREMIER_LEAGUE 15). **Quarantine / no-migrate-first — never delete.** Sampled pair
  (`day=2020-06-10 footystats_matches`): same match, but src carries an extra `league_api_football_id` column and
  `available_at=2026-08-07` (a re-capture), while the twin is the original 2020 capture — the canonical path does not
  hold the newer content.

**LIVE WRITER of `league=SEGUNDA_DIVISION` (the re-contamination):**

- `batch_api_football` `standings` + `teams` objects exist for day **2026-08-06 AND 2026-08-07**, dual-written with the
  SAME day's `LA_LIGA_2` standings/teams (verified by direct prefix listing). A writer emits BOTH keys for the same
  league on the same day, as of this week.
- `batch_footystats` `footystats_matches` carry `available_at=2026-08-07` (the footystats writer stamps
  `available_at = now(UTC)` at write time).
- **Code paths that still emit the raw `SEGUNDA_DIVISION` key:**
  1. `instruments-service/instruments_service/reference_data/adapters/sports/adapters/api_football_reference.py:165` —
     `canonical_league = build_league_id(league_country, league_name)` — the raw country/name slug, NOT the
     registry-first `_resolve_league_id` shipped in `unified-api-contracts@f3f1bbe0`. This feeds the
     standings/teams/reference write path.
  2. `unified-api-contracts/.../canonical/domain/sports/provider_league_ids.py` — `FOOTYSTATS_HISTORICAL_SEASON_IDS`
     maps 15+ footystats competition ids (39, 40, 41, 42, 43, 172, 1670, 2415, 4167, 4245, 4249, 6120, 7592, 9675,
     12467, 15066) → `SEGUNDA_DIVISION`; the footystats write path uses that as the league key.
  3. **Registry SSOT contradiction:** `unified-api-contracts/.../canonical/domain/sports/league_data.py:668-669`
     registers BOTH `LA_LIGA_2` and `SEGUNDA_DIVISION` (identical season structure, both `FOOTBALL`/`Prediction`).
     Because `SEGUNDA_DIVISION` is registered, `_canonical_league_id` passes it through non-lossy and
     `_is_in_canonical_write_universe` ACCEPTS it — the write-universe gate does not block the contamination.

**What was NOT re-verified:** the api_football FIXTURES write path is fixed (`unified-api-contracts@f3f1bbe0`
`_resolve_league_id` registry-first) and no recent-day SEGUNDA_DIVISION fixtures objects exist — but that fix does not
cover the reference-data (standings/teams) or footystats paths above.

## Why it matters

- The migration's core premise — "write path fixed, no longer re-contaminates" — is FALSE for the `SEGUNDA_DIVISION`
  population: a live writer still emits it (evidence to 2026-08-07, this week).
- The delete pass is blocked under `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`: Part 3 (no live writer
  still WRITES the location) fails → disposition `no-migrate-first` → **nobody deletes, fix first**.
- The done-when ("a fresh census returns 0 objects carrying the contaminated vocabulary") cannot be durably met — even
  if the 12,988 verified-twin objects are deleted, the writer re-creates `SEGUNDA_DIVISION` objects on the next
  capture/backfill.
- This is a data-correctness / SSOT-contradiction finding (two registered keys for one league; two writers using
  different keys), not a routine hygiene gap.

## Recommended decision

Fix the writers + registry FIRST, then run the delete pass:

1. **Reference-data (standings/teams) league key → registry resolution.** Replace the raw
   `build_league_id(league_country, league_name)` in `api_football_reference.py:165` with the registry-first resolution
   used elsewhere (`get_league_by_api_football_id` on the numeric api-football id, falling back non-lossy), so
   standings/teams writes land under `LA_LIGA_2`, not `SEGUNDA_DIVISION`.
2. **Resolve the registry duplicate.** Decide the single canonical key for the Spanish second division (`LA_LIGA_2` per
   the api-football-id resolution the migration already used) and reconcile the duplicate `SEGUNDA_DIVISION`/`LA_LIGA_2`
   entries in `league_data.py` (dedupe or alias), so the write-universe gate stops accepting `SEGUNDA_DIVISION`.
3. **Fix the footystats provider mapping.** `FOOTYSTATS_HISTORICAL_SEASON_IDS` should map the Spanish-2nd-division
   competition ids to the canonical key, not `SEGUNDA_DIVISION` (also verify the 15 ids all genuinely belong to that one
   league — a many-to-one collapse of 15 ids onto one key looks suspicious).
4. **Then run the gated delete pass** for the 12,988 verified-twin objects (tool ready:
   `market-tick-data-service/scripts/sports/league_id_relocation/delete_instruments_store_sports_league_vocabulary_2026_08_04.py`,
   dry-run exit 0, fresh §3a retention check passed = 604,800s) and confirm a fresh census returns 0 for the 3 mappings.
   The 928 differing-twin objects stay quarantined (no-migrate-first) pending a content-union decision.

## Todos

- [ ] [DATA] P1. Fix the reference-data league-key derivation so standings/teams write under `LA_LIGA_2`, not
      `SEGUNDA_DIVISION` — replace `build_league_id(league_country, league_name)` in
      `instruments-service/instruments_service/reference_data/adapters/sports/adapters/api_football_reference.py:165`
      with registry-first resolution (repo: instruments-service / unified-api-contracts).
- [ ] [DATA] P1. Reconcile the `SEGUNDA_DIVISION`/`LA_LIGA_2` duplicate registry entries in
      `unified-api-contracts/.../canonical/domain/sports/league_data.py` — decide the single canonical key and make
      `_is_in_canonical_write_universe` stop accepting the legacy key (repo: unified-api-contracts).
- [ ] [DATA] P1. Fix `FOOTYSTATS_HISTORICAL_SEASON_IDS` so the Spanish-2nd-division competition ids map to the canonical
      key, and confirm the 15 ids mapped to `SEGUNDA_DIVISION` genuinely belong to one league (repo:
      unified-api-contracts).
- [ ] [DATA] P2. After the writer/registry fixes land: run the gated delete pass
      (`market-tick-data-service/scripts/sports/league_id_relocation/delete_instruments_store_sports_league_vocabulary_2026_08_04.py`)
      for the 12,988 verified-twin objects + fresh census = 0 for the 3 mappings; 928 differing-twin objects stay
      quarantined pending a content-union decision (repo: market-tick-data-service / instruments-service).

## Progress Log

- **2026-08-10 (slot-22, data_engineering, `sports_closeout_track_x_hygiene-006`)**: full-bucket census (13,916
  contaminated objects still present), delete-pass dry-run (12,988 byte-identical twins / 928 differing twins
  quarantined), and writer audit. Confirmed live re-contamination: `SEGUNDA_DIVISION` standings/teams written
  2026-08-06/07 dual with `LA_LIGA_2`; footystats_matches `available_at=2026-08-07`; raw-slug + registry-duplicate root
  causes above. Delete pass blocked (Part 3). Filed this doc; the plan-level P2 checkbox stays open.
