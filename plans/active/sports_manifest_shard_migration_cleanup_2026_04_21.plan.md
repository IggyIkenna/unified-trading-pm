---
title: "Sports Manifest — Per-Entity Rescan + Legacy-Row Cleanup Migration"
priority: P0
status: active
owner: agent
created: 2026-04-21
locked_by: live-defi-rollout
locked_since: 2026-04-21
type: code
epic: none
completion_gates:
  code: C5
  deployment: none
  business: none
repo_gates:
  - repo: instruments-service
    code: C0
  - repo: deployment-api
    code: C0
depends_on:
  - instruments_service_orchestrator_reliability_fixes_2026_04_21
isProject: false
---

## Context

The 2026-04-21 per-league shard fixes (instruments-service `8a91324` for WEATHER + XG; Plans 6-7 of the
reliability-fixes plan still open for AF enrichments + STANDINGS) create a **three-state manifest** problem:

1. **Legacy unsharded rows** — dates captured before the fix have ONE row per (date, data_type) with no `league_id`.
   Example: 2024-09-15 has exactly 1 row for `WEATHER`, `XG`, `FIXTURE_STATS`, etc.
2. **Post-fix rows** — dates captured AFTER the fix have N per-league rows + 1 backwards-compat date-aggregate row. Same
   date → N+1 rows for one data_type.
3. **Never captured** — dates with no adapter run have 0 rows.

Without cleanup, the deployment-api `/api/data-status/manifest` aggregator either double-counts (if it sums both
unsharded + per-league) OR ignores post-fix rows entirely (if it queries only unsharded). The UI's per-league drilldown
would show inconsistent coverage depending on which dates each league happened to be captured in.

GCS parquet layout is **unchanged** by the fixes — only manifest rows are affected. This plan migrates manifest rows
without touching raw data.

## Three actions needed

### Action 1 — per-entity rescan (cheap alternative to re-running adapters)

`rescan_sports_fixtures_canonical.py` (instruments-service `c20bf59` + `7886dc0` chunk-safe modes) already reads
existing fixtures.parquet files on GCS and emits per-league manifest rows WITHOUT hitting API-Football. Extend (or write
siblings) to do the same for every other entity:

- **WEATHER** — read `entity=weather/weather.parquet` (columns venue_id, league_id, etc.), group by league_id, emit
  per-league rows.
- **XG** — read `entity=understat_xg/understat_xg.parquet`, group by league_id.
- **FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / PLAYER_STATS** — read each entity's parquet (already
  league-partitioned per sports-data- migration plan), emit per-league.
- **INJURIES** — read `entity=injuries/injuries.parquet`, group by league_id.
- **STANDINGS** — read `entity=standings/standings.parquet`, group by league_id.

Cost: ~5 min per entity per year of history (list + read + groupby + write). Total ~30-60 min vs multi-hour adapter
re-runs.

### Action 2 — drop the backwards-compat date-aggregate row

My fix at `8a91324` kept `manifest.add(data_type="WEATHER")` with no `league_id` for "backwards compat". But nobody
consumes that row — it's a self-inflicted wound. Remove it.

Similarly for `_record_weather_empty`, `_record_weather_failed` — currently emit BOTH unsharded AND per-league rows.
Keep only per-league.

### Action 3 — one-time legacy-row purge migration

One script, one run: scan `_index/availability_index.parquet`, for each (date, data_type) where per-league rows exist,
delete the row without `league_id` (the legacy unsharded one).

## Blast radius

- **instruments-service**:
  - `scripts/rescan_sports_fixtures_canonical.py` — extend to optionally handle entity = WEATHER / XG / FIXTURE_STATS /
    etc. via `--entity` flag.
  - `instruments_service/engine/orchestrator.py` — drop backwards-compat unsharded emission from
    `_record_weather_empty`, `_record_weather_failed`, and WEATHER success path. Similar for any other entity that
    currently dual-emits.
- **deployment-api**:
  - `services/data_status_service.py` — audit `SPORTS_DATA_TYPE_META` + `_sports_honest_coverage`: verify the aggregator
    prefers per-league rows and ignores unsharded rows when both exist. If not, fix.
- **New**: `instruments-service/scripts/purge_legacy_unsharded_manifest_rows.py` — one-time migration.

## Pre-audit manifest

| File                                              | Action                                                                                            |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `scripts/rescan_sports_fixtures_canonical.py`     | Extend with entity parameter; factor out FIXTURES-specific logic; add scanner helpers per entity. |
| `engine/orchestrator.py` WEATHER paths            | Remove unsharded `manifest.add(data_type="WEATHER")`; keep only per-league.                       |
| `engine/orchestrator.py` XG paths                 | Same treatment where applicable.                                                                  |
| `deployment-api/data_status_service.py`           | Audit `_sports_honest_coverage` aggregation logic.                                                |
| `scripts/purge_legacy_unsharded_manifest_rows.py` | New. Reads manifest, deletes unsharded rows where per-league equivalents exist.                   |

## Success criteria

- After the rescan runs: every `(date, data_type, league_id)` combo that has a parquet on GCS also has a manifest row.
- After the purge migration: zero `{date, data_type, league_id=""}` rows exist in the manifest for entities that support
  per-league sharding (FIXTURES, WEATHER, XG, INJURIES, STANDINGS, FIXTURE_STATS, etc.).
- Aggregator + UI consistency: pick any historical date, browse the SPORTS drilldown, every data_type shows per-league
  completion percentages (not single-row-per-date).
- Zero double-counting: the same `(date, league_id)` never shows 2× coverage because both unsharded and sharded rows
  exist.

## Phases

### Phase 0: deployment-api aggregator audit [SEQUENTIAL — do first]

- [ ] [AGENT] P0. Read `deployment-api/deployment_api/services/data_status_service.py` `_sports_honest_coverage`
      end-to-end. Document (in PRE-AUDIT-FINDINGS at top of this file) whether the aggregator prefers per-league rows vs
      unsharded, or sums both. If it sums both → urgent fix needed BEFORE the rescan runs or we'll double-count
      coverage.

### Phase 1: Extend rescan script for all entities [PARALLEL sub-tasks]

- [ ] [AGENT] P0. Refactor `rescan_sports_fixtures_canonical.py` to accept `--entity-type <NAME>` and dispatch to
      per-entity scanner. Factor FIXTURES-specific logic into `_scan_fixtures_blob`; new `_scan_weather_blob`,
      `_scan_xg_blob`, etc. for each entity.

- [ ] [AGENT] P0. Per-entity scanner per GCS parquet schema. Each scanner: read parquet, groupby league_id (or derive
      from venue × fixtures join for WEATHER), emit per-league manifest rows.

- [ ] [AGENT] P0. CLI smoke tests per entity — 1 date, verify expected per-league row count.

### Phase 2: Orchestrator — drop backwards-compat unsharded rows [SEQUENTIAL, depends on Phase 1]

- [ ] [AGENT] P0. Remove `manifest.add(data_type="WEATHER")` (no league_id) from success path + from
      `_record_weather_empty` / `_record_weather_failed`. Similar for any other entity with dual emission.

- [ ] [AGENT] P0. Unit tests: adapter run emits ONLY per-league rows.

### Phase 3: Purge migration script [SEQUENTIAL, depends on Phase 2]

- [ ] [AGENT] P0. Write `scripts/purge_legacy_unsharded_manifest_rows.py` — read `_index/availability_index.parquet`,
      for each (date, data_type) where per-league rows exist AND an unsharded row also exists, delete the unsharded row.

- [ ] [AGENT] P0. Dry-run mode (`--dry-run`) prints the delete set without writing.

- [ ] [AGENT] P0. Run on staging / or one-shot against production after review. Writes via ManifestWriter's usual
      read-modify-write pattern (chunk-safe-manifest-migrations.md doesn't apply — this is a one-off).

### Phase 4: End-to-end validation [SEQUENTIAL]

- [ ] [AGENT] P0. Launch rescans in serial for each entity (cheap — ~5 min each).
- [ ] [AGENT] P0. Run purge migration in dry-run, review, apply.
- [ ] [AGENT] P0. Query `/api/data-status/manifest` — verify every SPORTS data_type shows per-league completion for
      historical dates.
- [ ] [AGENT] P0. Spot-check: pick 3 random historical dates × 3 leagues × 3 data_types = 27 cells in UI. Every one
      should show per-league green/empty/red (no "1 shard total" fallback).

### Phase 5: QG [SEQUENTIAL]

- [ ] [AGENT] P0. `bash instruments-service/scripts/quality-gates.sh` green.
- [ ] [AGENT] P0. `bash deployment-api/scripts/quality-gates.sh` green.
- [ ] [AGENT] P0. Commit + quickmerge each repo.

## Dependency graph

```
Phase 0 (audit aggregator) ─► Phase 1 (rescan extends) ─► Phase 2 (drop BC) ─► Phase 3 (purge) ─► Phase 4 (validate) ─► Phase 5 (QG)
```

Hard dependency on `instruments_service_orchestrator_reliability_fixes` Bugs 4-5 shipping (done: 8a91324) and Bugs 6-7
(FIXTURE_STATS / EVENTS / LINEUPS / PLAYER_STATS / INJURIES / STANDINGS per-league) shipping before the purge can safely
run — otherwise we'd purge rows that no sharded equivalent exists for.

## Out of scope

- Changes to the raw parquet file layouts — purely manifest-side.
- Chunk-safe coordinator pattern — the purge is a one-off, not a multi-year migration.
- New adapter features — this is cleanup after sharding-uniformity fixes, not new capability.
