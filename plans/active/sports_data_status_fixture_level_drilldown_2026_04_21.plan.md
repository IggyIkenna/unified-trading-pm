---
title: "Data Status — Fixture-Level Drilldown + Per-Fixture CSV/JSON Download (Sports)"
priority: P1
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
  - repo: deployment-api
    code: C0
  - repo: deployment-ui
    code: C0
depends_on:
  - sports_manifest_shard_migration_cleanup_2026_04_21
  - instruments_service_orchestrator_reliability_fixes_2026_04_21
isProject: false
---

## Context

The SPORTS data-status drilldown today renders **Category → Data Type → League → Day** with green (captured /
empty_confirmed) and red (missing / attempted_failed) badges at each level. My earlier session work added a per-(league,
day) CSV download button for FIXTURES only.

Sports is **fixture-anchored** — every piece of data ultimately associates with a single `fixture_id`. The natural
navigation leaf for sports is therefore one level deeper than other categories:

```
Category (SPORTS)
  └── Data Type (FIXTURES / INJURIES / FIXTURE_STATS / XG / WEATHER / …)
      └── League (EPL / LA_LIGA / …)
          └── Day (2024-09-15)
              └── Fixture (ARS_v_LIV_2024-09-15)  ← NEW LEAF
                  └── Download CSV / JSON
```

Compared to CeFi/TradFi, where instrument is the leaf and day hosts many instruments, sports fixtures are denser per-day
but better keyed by `fixture_id`. This plan surfaces the fixture leaf in the UI and wires per-fixture download.

### What operators should see

At the **Day** level in the drilldown (SPORTS path, any data type):

- **Green (available)** — click expands to a fixture list with each fixture's coverage status. Click a fixture →
  download CSV/JSON of all entities captured for that fixture.
- **Red (missing)** — click expands to the expected-but-absent fixture list (from API-Football schedule). Display only;
  no download (data doesn't exist).

This is purely a **reorganisation + augmentation** — no new data ingestion. All the per-fixture data is already on GCS
(after the shard-uniformity + rescan plans complete); this plan exposes it.

## Blast radius

- **deployment-api**:
  - `routes/data_status.py` — new route `GET /api/fixtures/breakdown?day=...&league_id=...&data_type=...` returning a
    list of fixtures with per-entity coverage status.
  - `routes/data_status.py` — new route `GET /api/fixtures/download?fixture_id=...&format=csv|json` that reads every
    entity parquet (FIXTURES, FIXTURE_STATS, EVENTS, LINEUPS, PLAYER_STATS, INJURIES, XG, WEATHER) and returns the
    per-fixture union.
  - `services/data_status_drilldown.py` — new helper `build_fixture_breakdown(day, league_id, data_type)` and
    `build_fixture_download(fixture_id, format)`.
- **deployment-ui**:
  - `src/components/DataStatusTab.tsx` — extend the existing per-day drilldown (around the "click date to download CSV"
    affordance shipped in `c9f426d`) with a **new fixture-list panel** expanded on day click. Uses Green (captured),
    Amber (partial), Red (missing).
  - `src/api/client.ts` — add `fetchFixtureBreakdown(...)` + `buildFixtureDownloadUrl(fixture_id, format)`.
- **UAC**: no new schemas — fixture_id is already canonical.

## Pre-audit manifest

| File                                                              | Status                                                                                    | Action                                                                   |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `deployment-api/deployment_api/routes/data_status.py`             | Existing `/download-csv` + `/download-fixtures-csv` routes (`739d4fe` + `1051133` today). | Add 2 new routes + reuse existing parquet-read helpers.                  |
| `deployment-api/deployment_api/services/data_status_drilldown.py` | Existing `build_fixtures_csv_export` (today's session).                                   | Add `build_fixture_breakdown` + `build_fixture_download`.                |
| `deployment-ui/src/components/DataStatusTab.tsx`                  | Per-day green/red date badges already clickable for FIXTURES (`c9f426d`).                 | Expand that affordance into a full fixture-list sub-component.           |
| `deployment-ui/src/api/client.ts`                                 | Existing `buildFixturesCsvDownloadUrl(day, league_id)`.                                   | Add fixture-level siblings.                                              |
| FIXTURE_FEATURES schema                                           | From `unified-api-contracts ef1e89f`.                                                     | Reusable as part of the per-fixture JSON download (optional enrichment). |

## Per-fixture coverage model

For each fixture_id on a given day-league, the breakdown API returns:

```jsonc
{
  "fixture_id": "ARS_v_LIV_2024-09-15",
  "kickoff_utc": "2024-09-15T14:00:00Z",
  "home_team": "Arsenal",
  "away_team": "Liverpool",
  "status": "FT", // from fixtures.parquet
  "coverage": {
    "FIXTURES": "captured",
    "FIXTURE_LINEUPS": "captured",
    "FIXTURE_STATS": "captured",
    "FIXTURE_EVENTS": "captured",
    "PLAYER_STATS": "captured",
    "INJURIES": "empty_confirmed",
    "XG": "captured", // 6-league subset
    "WEATHER": "captured",
    "ODDS_SNAPSHOTS": "captured", // FootyStats
    // etc.
  },
  "coverage_summary": {
    "captured": 8,
    "empty_confirmed": 1,
    "missing": 0,
    "failed": 0,
  },
}
```

Colour rule for the UI fixture badge:

- **Green**: all expected entities captured or empty_confirmed
- **Amber**: some captured, some missing/failed (partial)
- **Red**: nothing captured + all missing/failed (data not there)

## Per-fixture download shape

**CSV**: one row per entity × per-fixture output row. Denormalised — flatten each parquet's columns into a
`entity,fixture_id,col1,col2,...` shape OR a wide union of all columns per entity (decide in Phase 1).

**JSON**: `{fixture_id: X, entities: {FIXTURES: {...}, FIXTURE_STATS: {...}, ...}}` — easier for programmatic consumers.

Both formats include `capture_status` per entity so downstream code can detect empty_confirmed vs captured without a
second API call.

## Success criteria

- `GET /api/fixtures/breakdown?day=2024-09-15&league_id=EPL` returns ~10 fixture entries for EPL Matchday 5 with
  coverage per entity.
- `GET /api/fixtures/download?fixture_id=<id>&format=csv` returns a valid CSV with header row + one row per entity.
- `GET /api/fixtures/download?fixture_id=<id>&format=json` returns structured JSON.
- UI: click green date → fixture list expands → green/amber/red badges per fixture → click fixture → CSV downloads.
- UI: click red date → expected-fixture list expands (from API-Football schedule for that day+league) → no download
  button.
- `bash deployment-api/scripts/quality-gates.sh` green.
- UI typecheck clean.

## Phases

### Phase 0: pre-audit [SEQUENTIAL]

- [ ] [AGENT] P0. Read existing `build_fixtures_csv_export` implementation. Confirm which GCS paths it reads + how it
      joins fixture_id → AF numeric. Reuse.
- [ ] [AGENT] P0. Enumerate the per-entity parquet paths per codex §2: `entity=fixtures`, `entity=injuries`,
      `entity=fixture_stats`, etc. Document (PRE-AUDIT-FINDINGS at top of this file) the exact schema per entity so the
      breakdown + download handlers know which columns to project.

### Phase 1: deployment-api — breakdown + download endpoints [PARALLEL]

- [ ] [AGENT] P0. `build_fixture_breakdown(day, league_id, data_type=None)` in `data_status_drilldown.py`: reads
      `fixtures.parquet` for the day + league, joins per-entity manifest rows, returns list of fixtures with per-entity
      coverage dict.

- [ ] [AGENT] P0. `build_fixture_download(fixture_id, format)` in `data_status_drilldown.py`: for each entity, read the
      day's parquet + filter to `fixture_id`, union-format the results. CSV or JSON based on `format`.

- [ ] [AGENT] P0. Two new FastAPI routes in `routes/data_status.py` with proper `Query(...)` annotations +
      `HTTPException` coverage for 404 (fixture not found) / 400 (bad params) / 413 (oversized result).

- [ ] [AGENT] P0. Unit tests (mocked GCS) for: breakdown with all entities captured, breakdown with mix, breakdown for
      red-missing day (fixtures expected per UAC schedule but no data landed), download CSV, download JSON, 404 on
      unknown fixture_id.

### Phase 2: deployment-ui — fixture drilldown component [PARALLEL with Phase 1]

- [ ] [AGENT] P0. New component `FixtureBreakdown.tsx` that fetches `/api/fixtures/breakdown` for a (day, league_id) and
      renders a fixture list with per-fixture coverage badges + download affordance.

- [ ] [AGENT] P0. Wire into `DataStatusTab.tsx` — when user clicks a green day badge in the per-league section, render
      `FixtureBreakdown` inline. Equivalent for red day badges (read-only mode, no downloads).

- [ ] [AGENT] P0. `src/api/client.ts`: `fetchFixtureBreakdown` + `buildFixtureDownloadUrl` + `FixtureBreakdownResponse`
      / `FixtureCoverageStatus` types.

- [ ] [AGENT] P0. Vitest component test with mocked API.

### Phase 3: Red-missing breakdown [SEQUENTIAL, depends on Phase 1]

- [ ] [AGENT] P0. For red days (missing fixtures), the breakdown route needs to derive the EXPECTED fixture list from a
      source other than the manifest (since nothing was captured). Two options: - (a) Read from
      `instruments-store-sports-…/instrument_availability/…` if the pre-fetch list was written. - (b) Call API-Football
      `/fixtures?date=…&league=…` live at request time (cheap — a few fixtures per league per date). Decide in Phase 3
      pre-check.

- [ ] [AGENT] P0. Unit test: breakdown on a day with no capture returns the expected-fixture list + each has
      `coverage = {all     missing}`.

### Phase 4: QG + smoke [SEQUENTIAL]

- [ ] [AGENT] P0. `bash deployment-api/scripts/quality-gates.sh` green.
- [ ] [AGENT] P0. `cd deployment-ui && CI=true npx tsc --noEmit` green.
- [ ] [AGENT] P0. Manual smoke in local dev: navigate SPORTS → FIXTURES → EPL → 2024-09-15 → fixture list renders →
      click one fixture → CSV downloads.
- [ ] [AGENT] P0. Commit + quickmerge each repo.

## Dependency graph

```
Phase 0 (audit) ─► Phase 1 (api endpoints) ┐
                                            ├─► Phase 4 (QG + smoke)
                  Phase 2 (ui component) ──┤
                  Phase 3 (red breakdown) ──┘
```

## Hard dependencies

- **`sports_manifest_shard_migration_cleanup_2026_04_21`** — per-league manifest rows need to exist for all entities.
  Without that, the breakdown endpoint can't tell if a league's XG for a day is captured vs missing.
- **`instruments_service_orchestrator_reliability_fixes_2026_04_21` Bugs 6-7** — per-league sharding for AF
  enrichments + STANDINGS. Same reason.

## Out of scope

- Upcoming-fixtures forward view — covered by `upcoming_fixtures_ui_view_2026_04_21` (different concern: forward
  schedule visualisation, not coverage drilldown).
- New ingestion code — this plan purely re-organises how existing data surfaces.
- Non-sports categories — CeFi / TradFi / DeFi use (venue, instrument, day) as their natural leaf. Sports'
  fixture-anchored model is the reason this plan exists.

## Cross-refs

- Per-fixture shard key codex: `codex/02-data/sports-scheduling-and-sharding.md` §1 + §9.
- Existing per-(league, day) CSV: `deployment-api/routes/data_status.py` `download_fixtures_csv` +
  `build_fixtures_csv_export`.
- Existing drilldown UI: `deployment-ui/src/components/DataStatusTab.tsx` per-league date badges.
- FIXTURE_FEATURES schema:
  `unified-api-contracts/unified_api_contracts/ internal/domain/features_sports/fixture_features.py` (for optional
  enrichment column in the per-fixture download).
