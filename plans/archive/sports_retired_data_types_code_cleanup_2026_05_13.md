---
name: sports-retired-data-types-code-cleanup-2026-05-13
type: plan
plan_type: refactor
asset_group: sports
owner: ikenna
status: active
priority: P2
created: 2026-05-13
last_updated: 2026-05-13
deadline: 2026-05-20
parent: expected_unattempted_propagation_chain_2026_05_12
related_plans:
  - expected_unattempted_propagation_chain_2026_05_12
  - manifest_migration_master_2026_05_07
migrated_from: |
  Discovered during slot 4 retired-data-type manifest cleanup (2026-05-13). Manifest rows
  successfully flipped to empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE; GCS parquets deleted.
  Code-level cleanup (stopping the emission path) was OUT OF SCOPE for that work but is
  needed to prevent future code paths from re-creating the same legacy rows.
locked_by: live-defi-rollout
locked_since: 2026-05-13
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
effective_concurrent_slots: 1
model_tier: sonnet-doable
thinking: medium
---

> **ARCHIVED 2026-05-18 (slot 10)** — 100% complete (12/12 checkboxes flipped). Preserved for archaeology. No deferred
> work outstanding — the single "Deferred discovery" item (TRANSFERMARKT_VALUES alias) was migrated + SHIPPED 2026-05-15
> (IS@2a024ab + UAC@5662ff5) in this same plan body. No successor required.

# Sports retired data_types — code cleanup follow-up

## Why

Slot 4 2026-05-13 manifest-cleanup completed:

- 88,779 manifest rows flipped to `empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE`
  (`migrate-sports-retired-20260513-160205` VM + `instruments-service@50346ed` script).
- GCS parquets for `entity=transfermarkt_leagues/` and `entity=sfi_leagues/` deleted.
- `entity=standings/` confirmed as api_football data (not SFI) — left intact.

**But** the orchestrator + data-status code paths still REFERENCE these retired data_types. While the manifest is now
honest, future runs of these code paths may attempt to re-emit rows that the migration would have to flip again. Code
cleanup is the durable fix.

Per CLAUDE.md "Honest absence" SSOT: docs are the intent → order doc → plan → code. The plan intent says these are
retired; code must reflect that.

## Pre-audit findings (2026-05-13 slot 4)

**instruments-service `engine/orchestrator.py`** (24 references):

| Line                        | Type                                                                                                          | Action                                                                                                                            |
| --------------------------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| 156-160                     | `_DATA_TYPE_TO_PIPELINE_MODE` mapping (3 entries)                                                             | DELETE — these data_types no longer exist                                                                                         |
| 1196                        | `_tm_entity = None if _leagues_today else "TRANSFERMARKT_LEAGUES"`                                            | Refactor — TM no longer fetches leagues; remove the conditional entirely                                                          |
| 1220                        | `league_filter=... if _leagues_today and _tm_entity != "TRANSFERMARKT_LEAGUES" else None`                     | Refactor — collapse to `league_filter=_leagues_today`                                                                             |
| 1292-1295                   | Source-dispatch tuples (3 entries)                                                                            | DELETE — `(TRANSFERMARKT_LEAGUES, TRANSFERMARKT)`, `(SFI_LEAGUES, SOCCER_FOOTBALL_INFO)`, `(SFI_STANDINGS, SOCCER_FOOTBALL_INFO)` |
| 1575-1577                   | List entries (3 entries)                                                                                      | DELETE                                                                                                                            |
| 1975                        | `_entity_wanted_zf("TRANSFERMARKT_LEAGUES")`                                                                  | Refactor — drop the `TRANSFERMARKT_LEAGUES` check (PLAYER_VALUES still needed)                                                    |
| 2012-2013                   | `_entity_wanted_zf("SFI_LEAGUES") or _entity_wanted_zf("SFI_STANDINGS")`                                      | DELETE — SFI_PROGRESSIVE_STATS is the only live SFI entity                                                                        |
| 2519                        | Same as 1975 (`_entity_wanted` variant)                                                                       | Refactor — drop TRANSFERMARKT_LEAGUES                                                                                             |
| 2551                        | `_entity_wanted("SFI_LEAGUES") or _entity_wanted("SFI_STANDINGS") or _entity_wanted("SFI_PROGRESSIVE_STATS")` | Refactor — collapse to `_entity_wanted("SFI_PROGRESSIVE_STATS")`                                                                  |
| 5454, 5480, 5728-5760, 5819 | Docstrings + comments noting retirement                                                                       | KEEP — these are historical context (already documented as retired)                                                               |
| 5927-5951                   | SFI_STANDINGS write path (3 callsites)                                                                        | DELETE — write path should not exist for retired data_type                                                                        |

**deployment-api `services/data_status_service.py`** (~6 references):

| Line                                 | Type                                                                                               | Action                                                                                                                                                                                              |
| ------------------------------------ | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 250, 265, 272, 667, 3809, 3813, 5471 | Various — comments noting retirement, `_is_transfer_window_venue` check, subsampled positions list | Audit each: if it's just historical comment, KEEP; if it's an active filter for the data-status panel, REMOVE the retired-type entry from the filter list so the panel doesn't render rows for them |

## Phases

**Phase 1 — instruments-service orchestrator.py cleanup** (~0.6 cal AI-days)

- [x] [CODE] P2. Delete `_DATA_TYPE_TO_PIPELINE_MODE` entries for retired types (3 entries).
      (`instruments-service@a0a720e`)
- [x] [CODE] P2. Refactor TM entity dispatch (lines 1196, 1220, 1975, 2519): remove TRANSFERMARKT_LEAGUES; PLAYER_VALUES
      path unchanged. (`instruments-service@a0a720e`)
- [x] [CODE] P2. Refactor SFI entity dispatch (lines 2012-2013, 2551): keep only SFI_PROGRESSIVE_STATS.
      (`instruments-service@a0a720e`)
- [x] [CODE] P2. Delete source-dispatch tuples (lines 1292-1295) and list entries (1575-1577).
      (`instruments-service@a0a720e`)
- [x] [CODE] P2. Delete SFI_STANDINGS write callsites (5927-5951). Verify no downstream consumer.
      (`instruments-service@a0a720e` — was already unreachable, dead code deleted)
- [x] [QG] P2. `cd instruments-service && bash scripts/quality-gates.sh`. Push. (✅ ALL QUALITY GATES PASSED — pushed to
      LDR)

**Phase 2 — deployment-api data_status_service.py cleanup** (~0.4 cal AI-days)

- [x] [CODE] P2. Audit each retired-type reference in `data_status_service.py`. Decide KEEP vs REMOVE per the pre-audit
      table. (deployment-api@5e19878 — removed from \_SPARSE_SPORTS_ENTITIES; historical comments at lines
      250/265/272/667/5478 preserved per plan)
- [x] [CODE] P2. Update `_is_transfer_window_venue` check at line 1226 of `tests/unit/test_data_status_service.py` to
      remove TRANSFERMARKT_LEAGUES reference if no longer applicable. (deployment-api@5e19878 — removed
      TRANSFERMARKT_LEAGUES assertion from TestTransferWindowAwareness; 128/128 tests pass)
- [x] [QG] P2. `cd deployment-api && bash scripts/quality-gates.sh`. Push. (✅ 2822/2822 pass baseline; 128/128 pass for
      test_data_status_service.py; pushed deployment-api@5e19878 to LDR)

**Phase 3 — verification** (~0.2 cal AI-days)

- [x] [VALIDATE] P2. Smoke-test instruments-service batch run for sports: verify no new manifest rows written for
      retired data_types. Re-run sports phantom audit dry-run; expect 0 new phantoms for TRANSFERMARKT_LEAGUES /
      SFI_LEAGUES / SFI_STANDINGS data_types. — ✅ VERIFIED 2026-05-15: manifest query (2,626,648 total rows) found
      88,779 historical empty_confirmed rows for SFI_LEAGUES / TRANSFERMARKT_LEAGUES / SFI_STANDINGS, all pre-dating
      IS@a0a720e deployment (2026-05-14). Most recent: 2026-04-27 (SFI_LEAGUES/TM) + 2026-04-14 (SFI_STANDINGS). Zero
      new rows post-cleanup — validated by direct manifest query since GCS listing timed out.
- [x] [VALIDATE] P2. Smoke-test deployment-api data-status panel for sports asset_group: verify retired-data-type rows
      render as `empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE` (clipped from denominator per codex SSOT). — ✅ VERIFIED
      2026-05-15 via live deployment-api on :8004: (a) `/api/data-status/coverage-summary` returned sports
      `latest_day_instruments` for 2026-05-15 = `{FIXTURES: 28, VENUES: 1}` — zero retired data_types in the latest-day
      denominator; (b) `/api/data-status/honest-coverage` (294KB response, sports rolled up to 157,174 captured + 326
      empty_confirmed + 0 attempted_failed = 99.79%) returned 0 occurrences of `TRANSFERMARKT_LEAGUES`, `SFI_LEAGUES`,
      `SFI_STANDINGS`, or `EXPECTED_DEPRECATED_DATA_TYPE` across the entire payload — retired types clipped from both
      numerator and denominator at panel-aggregation. Combined with Phase 2 unit test
      `test_capture_status_filter_excludes_empty_confirmed` (proves `empty_confirmed` never counts in `shards_found`) +
      Phase 3 item 1 manifest scan (88,779 historical retired rows all `empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE`,
      0 new post-cleanup) the surface is honest. **Later code-level re-verification 2026-05-30 (merged 2026-06-05 from
      the stale `plans/active/` duplicate during migration-completion — no evidence discarded):** code-level audit
      confirms `EXPECTED_DEPRECATED_DATA_TYPE` is in `_EMPTY_REASON_KEYS` taxonomy; `ok_mask` treats `empty_confirmed`
      rows as OK (not missing from denominator); `TestRetiredDataTypesHonestCoverage` +
      `test_each_registered_reason_routes_to_correct_bucket` pass (21/21 tests, QG green). Also deployment-api@c328334
      (slot 2) adds `TestSportsRetiredDataTypeFiltering` — verifies `SPORTS_DATA_TYPE_META` excludes retired types and
      `_build_data_type_grouping` clips them from the denominator; QG green 252s.

## Deferred discovery — TRANSFERMARKT_VALUES alias (2026-05-14 slot 4 sports_master audit)

**FINDING**: `TRANSFERMARKT_VALUES` appears in `instruments-service/instruments_service/engine/orchestrator.py:1420`
inside the `_sports_per_league_entities` set. This is a stale alias — the TM handler at line 2532 checks
`_entity_wanted("PLAYER_VALUES")`, and the manifest writer at line 5548 uses `data_type="PLAYER_VALUES"`.
`entity_filter="TRANSFERMARKT_VALUES"` would be a silent no-op (no manifest rows written).

- [x] **DEFERRED → SHIPPED 2026-05-15** — [CODE] P1. Remove `"TRANSFERMARKT_VALUES"` from `_sports_per_league_entities`
      in orchestrator.py:1420 (IS@2a024ab) and `SPORTS_DATA_TYPE_TO_SOURCE` in UAC `league_data.py` (UAC@5662ff5). Safe
      to remove: handler never dispatches on it + manifest never writes it.

Also: `SPORTS_DATA_TYPE_TO_SOURCE` in UAC `league_data.py` had both entries — TRANSFERMARKT_VALUES (stale alias) and
PLAYER_VALUES (canonical). Both removals shipped together (2026-05-15).

## Success criteria

- `grep "TRANSFERMARKT_LEAGUES\|SFI_LEAGUES\|SFI_STANDINGS" instruments_service/engine/orchestrator.py` returns ONLY
  historical comments (no active code references).
- Next sports orchestrator batch run does NOT emit any new manifest rows for these data_types.
- Data-status panel for sports does NOT render rows for these data_types (or renders them as honest
  `empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE`).

## Cross-plan coordination

- This plan is a code-cleanup follow-up to `expected_unattempted_propagation_chain_2026_05_12.md` § "BIG FINDING
  2026-05-13 slot 4". The manifest is already honest (no urgency); this plan prevents future drift.
- Composes with `manifest_migration_master_2026_05_07.md` § C.1 LEAGUES kill (the api_football LEAGUES code-removal was
  already shipped at `instruments-service@93efebf` per the parent plan; this is the same pattern applied to TM + SFI).

## Estimate notes

- `refactor` class, multiplier 0.4×. Pre-audit table makes the work mechanical.
- Risk: orchestrator is 6000+ lines with cross-cutting entity dispatch. Test coverage is what catches regressions; QG
  ratchet enforces that.
