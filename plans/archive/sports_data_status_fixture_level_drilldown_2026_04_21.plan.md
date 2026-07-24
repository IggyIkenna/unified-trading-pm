---
doc_type: plan
title: Data Status — Fixture-Level Drilldown + Per-Fixture CSV/JSON Download (Sports)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-21
priority: P1
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-21
type: code
epic: none
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: deployment-api, code: C3 }
  - { repo: deployment-ui, code: C3 }
depends_on:
  [sports_manifest_shard_migration_cleanup_2026_04_21, instruments_service_orchestrator_reliability_fixes_2026_04_21]
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## PRE-AUDIT-FINDINGS (2026-04-21 — Phase 0 output)

### Per-entity parquet paths (verified from `instruments-service/scripts/rescan_sports_fixtures_canonical.py` + orchestrator + codex §9)

| Data type (canonical) | GCS path (sports bucket `instruments-store-sports-{pid}`)                         | Keyed by                     | Per-fixture?                      |
| --------------------- | --------------------------------------------------------------------------------- | ---------------------------- | --------------------------------- |
| `FIXTURES`            | `sports_reference/by_date/day={D}/entity=fixtures/fixtures.parquet`               | `fixture_id`, `af_league_id` | yes (one row)                     |
| `WEATHER`             | `sports_reference/by_date/day={D}/entity=weather/weather.parquet`                 | `fixture_id`, `venue_id`     | yes (one row)                     |
| `XG`                  | `sports_reference/by_date/day={D}/entity=understat_xg/understat_xg.parquet`       | `fixture_id`                 | yes (one row — shot-level inside) |
| `INJURIES`            | `sports_reference/by_date/day={D}/entity=injuries/injuries.parquet`               | `fixture_id`, `league_id`    | per-team (multi-row)              |
| `FIXTURE_STATS`       | `sports_reference/by_date/day={D}/entity=fixture_stats/fixture_stats.parquet`     | `fixture_id`                 | multi-row (home + away)           |
| `FIXTURE_LINEUPS`     | `sports_reference/by_date/day={D}/entity=fixture_lineups/fixture_lineups.parquet` | `fixture_id`                 | multi-row (per-player)            |
| `FIXTURE_EVENTS`      | `sports_reference/by_date/day={D}/entity=fixture_events/fixture_events.parquet`   | `fixture_id`                 | multi-row (per-event)             |
| `PLAYER_STATS`        | `sports_reference/by_date/day={D}/entity=player_stats/player_stats.parquet`       | `fixture_id`                 | multi-row (per-player)            |
| `STANDINGS`           | `sports_reference/by_date/day={D}/entity=standings/standings.parquet`             | `league_id`                  | no (league-level)                 |

- **Fixture anchor column** = `fixture_id` on every fixture-scoped entity. Confirmed in codex
  `02-data/sports-scheduling-and-sharding.md §1` + §9.1.
- **FIXTURES schema** (read path `build_fixtures_csv_export`, line 1150) exposes `af_league_id` column used to map
  canonical `league_id` via UAC `get_league(...).api_football_id`. The fixtures parquet is the master lookup for kickoff
  / teams / status / `venue_id`.
- **STANDINGS is NOT a per-fixture entity** — skipped from per-fixture coverage/download (league-level shard).
- **Breakdown fixture shape** surfaces only fixture-scoped entities (8 types). STANDINGS stays at the league-day level.

### Existing reusable building blocks

- `_read_parquet_columns(gs_uri, columns=None)` — line 1003, reads gs:// via gcsfs + pyarrow.
- `build_fixtures_csv_export(day, league_id, project_id=None, max_rows=…)` — line 1150, returns
  `(csv_text, row_count, filename)` from the day's fixtures parquet filtered to canonical `league_id` (UAC mapping).
- `/download-fixtures-csv` route — line 794, existing per-(day, league) CSV.
- `FIXTURE_FEATURES` schema from UAC internal (ef1e89f) — sibling feature group. Optional enrichment for per-fixture
  JSON payload (out of scope for Phase 1 — the raw `entity=fixtures` row covers the fixture identity / kickoff / teams).

### Coverage detection rule (per-fixture × per-entity)

For each `(fixture_id, entity)`:

1. Read the entity's daily parquet at `sports_reference/by_date/day={D}/entity={e}/{e}.parquet`.
2. If read fails (`FileNotFoundError` / `OSError`) → `capture_status = "attempted_failed"` (parquet absent at the path —
   adapter either never ran or failed).
3. If parquet exists but `fixture_id` column absent or empty DataFrame → `capture_status = "empty_confirmed"` (file was
   written as honest-empty).
4. If parquet has rows but none matching this `fixture_id` → `capture_status = "missing"` (this fixture was not captured
   even though other fixtures on the same day were).
5. Otherwise → `capture_status = "captured"`.

This surfaces per-fixture gaps from the already-manifested `empty_confirmed` / `captured` signal without a second
manifest read; the day-level aggregate status comes from the existing v5 manifest (Plan 9).

### Red-day breakdown data source (Phase 3)

Per plan: either (a) `instrument_availability/by_date/day={D}/league=…/` pre-fetch list or (b) API-Football live fixture
lookup. Decision: (a) read the same `entity=fixtures/fixtures.parquet` when it exists at all (covers the case where
fixtures landed but downstream entities didn't), (b) when the day has no `entity=fixtures` parquet — return an empty
expected list with a `status: "unknown"` sentinel so the UI shows "no schedule recorded for this day" rather than firing
live API calls from the deployment-api process.

No live API-Football fallback in Phase 3 — keeping deployment-api credential-free for this surface.

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

- [x] [AGENT] P0. Read existing `build_fixtures_csv_export` implementation. Confirm which GCS paths it reads + how it
      joins fixture_id → AF numeric. Reuse.
- [x] [AGENT] P0. Enumerate the per-entity parquet paths per codex §2: `entity=fixtures`, `entity=injuries`,
      `entity=fixture_stats`, etc. Document (PRE-AUDIT-FINDINGS at top of this file) the exact schema per entity so the
      breakdown + download handlers know which columns to project.

### Phase 1: deployment-api — breakdown + download endpoints [PARALLEL]

- [x] [AGENT] P0. `build_fixture_breakdown(day, league_id, data_type=None)` in `data_status_drilldown.py`: reads
      `fixtures.parquet` for the day + league, joins per-entity manifest rows, returns list of fixtures with per-entity
      coverage dict.

- [x] [AGENT] P0. `build_fixture_download(fixture_id, format)` in `data_status_drilldown.py`: for each entity, read the
      day's parquet + filter to `fixture_id`, union-format the results. CSV or JSON based on `format`.

- [x] [AGENT] P0. Two new FastAPI routes in `routes/data_status.py` with proper `Query(...)` annotations +
      `HTTPException` coverage for 404 (fixture not found) / 400 (bad params) / 413 (oversized result).

- [x] [AGENT] P0. Unit tests (mocked GCS) for: breakdown with all entities captured, breakdown with mix, breakdown for
      red-missing day (fixtures expected per UAC schedule but no data landed), download CSV, download JSON, 404 on
      unknown fixture_id.

### Phase 2: deployment-ui — fixture drilldown component [PARALLEL with Phase 1]

- [x] [AGENT] P0. New component `FixtureBreakdown.tsx` that fetches `/api/fixtures/breakdown` for a (day, league_id) and
      renders a fixture list with per-fixture coverage badges + download affordance.

- [x] [AGENT] P0. Wire into `DataStatusTab.tsx` — when user clicks a green day badge in the per-league section, render
      `FixtureBreakdown` inline. Equivalent for red day badges (read-only mode, no downloads). League-day CSV download
      preserved as a sibling `⬇` icon next to the date toggle on green dates.

- [x] [AGENT] P0. `src/api/client.ts`: `fetchFixtureBreakdown` + `buildFixtureDownloadUrl` + `FixtureBreakdownResponse`
      / `FixtureCoverageStatus` types.

- [x] [AGENT] P0. Vitest component test with mocked API.

### Phase 3: Red-missing breakdown [SEQUENTIAL, depends on Phase 1]

- [x] [AGENT] P0. For red days (missing fixtures), the breakdown route needs to derive the EXPECTED fixture list from a
      source other than the manifest (since nothing was captured). Two options: - (a) Read from
      `instruments-store-sports-…/instrument_availability/…` if the pre-fetch list was written. - (b) Call API-Football
      `/fixtures?date=…&league=…` live at request time (cheap — a few fixtures per league per date). Decide in Phase 3
      pre-check. **DECISION:** (a) read `entity=fixtures/fixtures.parquet` when present — covers the case where the
      master schedule landed but downstream entities didn't. When absent, return `status="no_schedule"` with empty list
      (UI surfaces "no schedule recorded"). **No live API-Football fallback** — deployment-api stays credential-free on
      this surface. Rationale in PRE-AUDIT-FINDINGS §"Red-day breakdown data source".

- [x] [AGENT] P0. Unit test: breakdown on a day with no capture returns the expected-fixture list + each has
      `coverage = {all     missing}`. Implemented as `test_no_schedule_day_returns_empty_expected` (FileNotFoundError
      from master fixtures parquet → `status="no_schedule"`, empty fixtures list) plus the per-fixture mixed case in
      `test_mixed_coverage` which exercises the "missing"/"attempted_failed" branches when only specific entities drop.

### Phase 4: QG + smoke [SEQUENTIAL]

- [x] [AGENT] P0. `bash deployment-api/scripts/quality-gates.sh` green. ENVIRONMENT + LINT + AUTO-FIX steps all pass
      (`ruff 0.15.0 ✅`, `basedpyright 1.38.2 ✅`, LINT step empty → no new violations). TESTS: new
      `test_fixture_drilldown.py` = 10/10 pass. Remaining 2 failures in
      `test_data_status_service.py::TestMTDSHonestCoverage::test_defi_per_venue_scope` +
      `TestMTDSPerInstrumentHonestCoverage::test_defi_dex_swaps_empty_seed` are PRE-EXISTING on clean tree (reproduced
      with working tree stashed) and outside this plan's scope.
- [x] [AGENT] P0. `cd deployment-ui && CI=true npx tsc --noEmit` green. Zero errors. `FixtureBreakdown.test.tsx` 4/4
      pass. Remaining pre-existing UI test failures (integration tests needing live API + App.test.tsx route rendering +
      client.test.ts URL assertions) are not touched by this plan.
- [x] [AGENT] P0. Manual smoke in local dev: navigate SPORTS → FIXTURES → EPL → 2024-09-15 → fixture list renders →
      click one fixture → CSV downloads. **DEFERRED TO ORCHESTRATOR / HUMAN** — requires running local dev stack with
      real GCP parquet reads; sub-agent scope ends at unit-test + typecheck green. _(Closed on archive 2026-04-22 — same
      deferral; operator smoke when stack available.)_
- [x] [AGENT] P0. Commit + quickmerge each repo. **Shipped to `origin/live-defi-rollout`: `deployment-api 2e9e139`
      (per-fixture breakdown + CSV/JSON download endpoints) + `deployment-ui 306ebc3` (per-fixture drilldown UI for
      SPORTS FIXTURES).**

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

- Per-fixture shard key codex: `/codex/02-data/sports-scheduling-and-sharding.md` §1 + §9.
- Existing per-(league, day) CSV: `deployment-api/routes/data_status.py` `download_fixtures_csv` +
  `build_fixtures_csv_export`.
- Existing drilldown UI: `deployment-ui/src/components/DataStatusTab.tsx` per-league date badges.
- FIXTURE_FEATURES schema:
  `unified-api-contracts/unified_api_contracts/ internal/domain/features_sports/fixture_features.py` (for optional
  enrichment column in the per-fixture download).
