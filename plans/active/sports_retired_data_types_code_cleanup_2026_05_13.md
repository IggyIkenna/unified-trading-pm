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

# Sports retired data_types — code cleanup follow-up

## Why

Slot 4 2026-05-13 manifest-cleanup completed:

- 88,779 manifest rows flipped to `empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE`
  (`migrate-sports-retired-20260513-160205` VM + `instruments-service@50346ed` script).
- GCS parquets for `entity=transfermarkt_leagues/` and `entity=sfi_leagues/` deleted.
- `entity=standings/` confirmed as api_football data (not SFI) — left intact.

**But** the orchestrator + data-status code paths still REFERENCE these retired data_types. While
the manifest is now honest, future runs of these code paths may attempt to re-emit rows that the
migration would have to flip again. Code cleanup is the durable fix.

Per CLAUDE.md "Honest absence" SSOT: docs are the intent → order doc → plan → code. The plan
intent says these are retired; code must reflect that.

## Pre-audit findings (2026-05-13 slot 4)

**instruments-service `engine/orchestrator.py`** (24 references):

| Line | Type | Action |
|------|------|--------|
| 156-160 | `_DATA_TYPE_TO_PIPELINE_MODE` mapping (3 entries) | DELETE — these data_types no longer exist |
| 1196 | `_tm_entity = None if _leagues_today else "TRANSFERMARKT_LEAGUES"` | Refactor — TM no longer fetches leagues; remove the conditional entirely |
| 1220 | `league_filter=... if _leagues_today and _tm_entity != "TRANSFERMARKT_LEAGUES" else None` | Refactor — collapse to `league_filter=_leagues_today` |
| 1292-1295 | Source-dispatch tuples (3 entries) | DELETE — `(TRANSFERMARKT_LEAGUES, TRANSFERMARKT)`, `(SFI_LEAGUES, SOCCER_FOOTBALL_INFO)`, `(SFI_STANDINGS, SOCCER_FOOTBALL_INFO)` |
| 1575-1577 | List entries (3 entries) | DELETE |
| 1975 | `_entity_wanted_zf("TRANSFERMARKT_LEAGUES")` | Refactor — drop the `TRANSFERMARKT_LEAGUES` check (PLAYER_VALUES still needed) |
| 2012-2013 | `_entity_wanted_zf("SFI_LEAGUES") or _entity_wanted_zf("SFI_STANDINGS")` | DELETE — SFI_PROGRESSIVE_STATS is the only live SFI entity |
| 2519 | Same as 1975 (`_entity_wanted` variant) | Refactor — drop TRANSFERMARKT_LEAGUES |
| 2551 | `_entity_wanted("SFI_LEAGUES") or _entity_wanted("SFI_STANDINGS") or _entity_wanted("SFI_PROGRESSIVE_STATS")` | Refactor — collapse to `_entity_wanted("SFI_PROGRESSIVE_STATS")` |
| 5454, 5480, 5728-5760, 5819 | Docstrings + comments noting retirement | KEEP — these are historical context (already documented as retired) |
| 5927-5951 | SFI_STANDINGS write path (3 callsites) | DELETE — write path should not exist for retired data_type |

**deployment-api `services/data_status_service.py`** (~6 references):

| Line | Type | Action |
|------|------|--------|
| 250, 265, 272, 667, 3809, 3813, 5471 | Various — comments noting retirement, `_is_transfer_window_venue` check, subsampled positions list | Audit each: if it's just historical comment, KEEP; if it's an active filter for the data-status panel, REMOVE the retired-type entry from the filter list so the panel doesn't render rows for them |

## Phases

**Phase 1 — instruments-service orchestrator.py cleanup** (~0.6 cal AI-days)

- [ ] [CODE] P2. Delete `_DATA_TYPE_TO_PIPELINE_MODE` entries for retired types (3 entries).
- [ ] [CODE] P2. Refactor TM entity dispatch (lines 1196, 1220, 1975, 2519): remove TRANSFERMARKT_LEAGUES;
      PLAYER_VALUES path unchanged.
- [ ] [CODE] P2. Refactor SFI entity dispatch (lines 2012-2013, 2551): keep only SFI_PROGRESSIVE_STATS.
- [ ] [CODE] P2. Delete source-dispatch tuples (lines 1292-1295) and list entries (1575-1577).
- [ ] [CODE] P2. Delete SFI_STANDINGS write callsites (5927-5951). Verify no downstream consumer.
- [ ] [QG] P2. `cd instruments-service && bash scripts/quality-gates.sh`. Push.

**Phase 2 — deployment-api data_status_service.py cleanup** (~0.4 cal AI-days)

- [ ] [CODE] P2. Audit each retired-type reference in `data_status_service.py`. Decide KEEP vs REMOVE
      per the pre-audit table.
- [ ] [CODE] P2. Update `_is_transfer_window_venue` check at line 1226 of `tests/unit/test_data_status_service.py`
      to remove TRANSFERMARKT_LEAGUES reference if no longer applicable.
- [ ] [QG] P2. `cd deployment-api && bash scripts/quality-gates.sh`. Push.

**Phase 3 — verification** (~0.2 cal AI-days)

- [ ] [VALIDATE] P2. Smoke-test instruments-service batch run for sports: verify no new manifest rows
      written for retired data_types. Re-run sports phantom audit dry-run; expect 0 new phantoms for
      TRANSFERMARKT_LEAGUES / SFI_LEAGUES / SFI_STANDINGS data_types.
- [ ] [VALIDATE] P2. Smoke-test deployment-api data-status panel for sports asset_group: verify
      retired-data-type rows render as `empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE` (clipped from
      denominator per codex SSOT).

## Success criteria

- `grep "TRANSFERMARKT_LEAGUES\|SFI_LEAGUES\|SFI_STANDINGS" instruments_service/engine/orchestrator.py`
  returns ONLY historical comments (no active code references).
- Next sports orchestrator batch run does NOT emit any new manifest rows for these data_types.
- Data-status panel for sports does NOT render rows for these data_types (or renders them as honest
  `empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE`).

## Cross-plan coordination

- This plan is a code-cleanup follow-up to `expected_unattempted_propagation_chain_2026_05_12.md`
  § "BIG FINDING 2026-05-13 slot 4". The manifest is already honest (no urgency); this plan
  prevents future drift.
- Composes with `manifest_migration_master_2026_05_07.md` § C.1 LEAGUES kill (the api_football
  LEAGUES code-removal was already shipped at `instruments-service@93efebf` per the parent plan;
  this is the same pattern applied to TM + SFI).

## Estimate notes

- `refactor` class, multiplier 0.4×. Pre-audit table makes the work mechanical.
- Risk: orchestrator is 6000+ lines with cross-cutting entity dispatch. Test coverage is what
  catches regressions; QG ratchet enforces that.
