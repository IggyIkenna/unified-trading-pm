---
title: "Upcoming Fixtures UI — Per-League Next-7-Days View"
priority: P2
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
  - repo: unified-trading-system-ui
    code: C0
depends_on: []
isProject: false
---

## Context

The rolling forward-poll (codex §4) now lands `sports_reference/by_date/day={D}/entity=fixtures/fixtures.parquet` for
[today, today+7] every 6h. Each parquet has kickoff_utc, home/away team, league_id, venue — everything needed to render
an "Upcoming Fixtures" card grid.

No UI consumes this data today. This plan surfaces upcoming fixtures in both UIs that touch sports:

- **deployment-ui** — operator view (data status drilldown currently shows missing dates per league; add an "Upcoming"
  section alongside).
- **unified-trading-system-ui** — client-facing sports/betting surface. Useful for dashboards showing "next 7 days of
  markets".

## Blast radius

- **deployment-api**:
  - New endpoint `GET /api/fixtures/upcoming?days=7&league_id=EPL` (optional filter). Reads
    `sports_reference/by_date/day={D}/entity=fixtures/` parquets for [today, today+days]. Returns JSON array of fixtures
    sorted by kickoff_utc.
- **deployment-ui**:
  - New component `UpcomingFixtures.tsx` — card grid grouped by day + league. Uses existing DataStatusDrilldown styling.
- **unified-trading-system-ui**:
  - Same shape — may belong under the sports/markets tab. Check existing structure first.

## Pre-audit manifest

| File                                                              | Purpose                                                                 |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `deployment-api/deployment_api/routes/data_status.py`             | Reference pattern for GCS-parquet-backed endpoints + response shaping.  |
| `deployment-api/deployment_api/services/data_status_drilldown.py` | `_read_parquet_columns` helper — reuse for fixtures read.               |
| `deployment-ui/src/api/client.ts`                                 | API client — add `fetchUpcomingFixtures` + types.                       |
| `deployment-ui/src/components/DataStatusTab.tsx`                  | Where to slot the new UpcomingFixtures component (or sibling route).    |
| `unified-trading-system-ui/src/`                                  | Audit: does a sports/markets tab exist? If yes, add here. If no, defer. |
| `codex/02-data/sports-scheduling-and-sharding.md` §4              | Contract on what dates are available in the forward-poll window.        |

## Data shape

Each fixtures.parquet row (from API-Football adapter):

- `fixture_id: str`
- `kickoff_utc: datetime`
- `league_id: str` (canonical)
- `home_team_id: str`, `away_team_id: str`
- `home_team_name: str`, `away_team_name: str`
- `venue_id: str`, `venue_name: str`
- `status: str` (NS = not-started, TBD, POSTPONED, etc.)
- `round: str` (e.g. "Regular Season - 10")

UI renders: day-grouped → league-grouped → per-fixture card with kickoff time

- teams + venue + status badge.

## Success criteria

- `GET /api/fixtures/upcoming?days=7` returns sorted-by-kickoff JSON array.
- Optional `league_id` filter.
- Returns dates with no parquet as empty — do NOT 500 on future dates with no file yet.
- Component renders correctly in deployment-ui; integrates with existing drilldown UX.
- Client-facing UI (unified-trading-system-ui) renders if target page exists.
- UI typecheck clean (`npx tsc --noEmit`).
- API QG (`bash deployment-api/scripts/quality-gates.sh`) green.

## Phases

### Phase 1: deployment-api endpoint [PARALLEL]

- [x] [AGENT] P0. Add `GET /api/fixtures/upcoming` route. Query params: `days: int = 7`, `league_id: str | None = None`.
- [x] [AGENT] P0. Build response model `UpcomingFixture` with canonical columns from fixtures.parquet. Validate via
      pydantic.
- [x] [AGENT] P0. Implement `list_upcoming_fixtures(days, league_id)` helper reading parquets from
      `gs://instruments-store-sports-{pid}/     sports_reference/by_date/day={D}/entity=fixtures/fixtures.parquet` for D
      in [today, today+days]. Concat + filter + sort by kickoff_utc.
- [x] [AGENT] P0. Unit tests (mocked GCS).

### Phase 2: deployment-ui component [PARALLEL]

- [x] [AGENT] P0. `src/api/client.ts`: add `fetchUpcomingFixtures(opts)` + `UpcomingFixture` type.
- [x] [AGENT] P0. `src/components/UpcomingFixtures.tsx`: card grid component. Grouped-by-day details/summary blocks,
      league sub-groups, per-fixture card with kickoff (local time), teams, venue, status.
- [x] [AGENT] P0. Add to DataStatusTab as a new section OR new tab route.
- [x] [AGENT] P0. Vitest unit test with mocked API client.

### Phase 3: unified-trading-system-ui integration [PARALLEL, optional]

- [x] [AGENT] P1. Audit if sports-markets tab exists. If yes, add UpcomingFixtures there using the deployment-api
      endpoint. If no, SKIP this phase with a note + close plan at C5 for the two repos actually changed.

### Phase 4: QG + smoke [SEQUENTIAL]

- [ ] [AGENT] P0. `bash deployment-api/scripts/quality-gates.sh` green.
- [ ] [AGENT] P0. `cd deployment-ui && CI=true npx tsc --noEmit && CI=true     npm test -- --run` green.
- [ ] [AGENT] P0. Smoke: launch dev server, visit the new page, confirm 7 days of fixtures render.
- [ ] [AGENT] P0. Commit + quickmerge each repo.

## Dependency graph

```
Phase 1 (api) ┐
Phase 2 (dep-ui) ├─► Phase 4 (QG + smoke)
Phase 3 (uts-ui) ┘
```

Phases 1/2/3 are independent — run in parallel.

## Out of scope

- Match-state live updates (in-play score ticker) — separate work, lives in market-tick-data-service live feed, not this
  plan.
- Odds snapshots per fixture — shown on a separate odds page.
- Backfill of fixtures.parquet — assumes the forward-poll VM runs daily (Plan F: cron activation).
