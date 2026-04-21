---
title: "instruments-service Orchestrator Reliability + Per-League Shard Uniformity Fixes"
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
  - repo: instruments-service
    code: C1
depends_on: []
isProject: false
---

## Context

Today's API-Football forward-poll (VM `af-backfill-20260421-142640`) surfaced three separate reliability bugs in the
instruments-service orchestrator. Each is non-fatal (the VM completed rc=0 and wrote parquets for every date) but
noisy + two are latent correctness risks.

### Bug 1 — Pydantic validation on future-fixture goals

```
WARNING Failed to parse fixture response item: 2 validation errors for ApiFootballFixture
goals.home  Input should be a valid integer [type=int_type, input_value=None, input_type=NoneType]
goals.away  Input should be a valid integer [type=int_type, input_value=None, input_type=NoneType]
```

Fires on every unplayed future fixture (status=NS). The score fields are legitimately null before kickoff. The adapter's
`ApiFootballFixture` model declares `goals.home / goals.away: int` — should be `int | None`. Without this fix,
fixtures.parquet dumps every row that's unplayed with a warning. Log noise today; tomorrow when a downstream consumer
relies on strict schema validation, it's a skip.

### Bug 2 — UnboundLocalError on `get_leagues_needing_refresh`

```
WARNING Handler InstrumentsHandler failed on payload 8: cannot access local
variable 'get_leagues_needing_refresh' where it is not associated with
a value
```

Fired for 1 of 8 payloads (12.5% failure rate). A conditional import that didn't execute for the specific code path.
Deterministic by payload state — intermittent from the outside but 100% reproducible given the same inputs.

Located at `instruments-service/instruments_service/engine/orchestrator.py:821` area (I grepped this during a prior
session).

### Bug 3 — 404 on instrument_availability for future dates

```
ERROR [CRITICAL] unknown error in instruments-service.fixture_mapping_write:
404 ... No such object: instrument_availability/by_date/day=2026-04-28/
venue=API_FOOTBALL/instruments.parquet (recovery=alert, correlation=9d1f8a49)
```

Future dates with zero fixtures legitimately have no instruments.parquet. The orchestrator's fixture-mapping-write path
treats this as CRITICAL. Expected behaviour: fall through gracefully (log INFO, skip) when the date is in the
forward-poll horizon and no fixtures were fetched.

### Bug 4 — OpenMeteo WEATHER emits one date-level row, no per-league shard — **SHIPPED 2026-04-21 `8a91324`**

2026-04-21 provider smoke (VM `om-smoke-20260421-162003`) showed WEATHER manifest = 1 row per date. Data-status UI can't
render per-league WEATHER completion because every league shares the single unsharded row. Bug was in two paths: (a)
success path at ex-line 4898 emitted `manifest.add(..., data_type="WEATHER")` with no `league_id=`; (b) "all venues
already covered" skip path at ex-line 4807 exited without touching the manifest.

**Fixed in `instruments-service 8a91324`**: success path now computes `venue_id → league_id` via `fixtures_df` join,
emits per-league `manifest.add(league_id=lid)` for each captured league + per-league `record_empty` for in-season
expected leagues with no captures. Skip path back-fills per-league rows from `fixtures_df` (idempotent). Date-level
aggregate row retained for backwards compat.

### Bug 5 — Understat XG short-circuit on unsharded row_key bypasses per-league loop — **SHIPPED 2026-04-21 `8a91324`**

Same smoke surfaced XG manifest = 1 row per date. The existing per-league `record_empty` loop at line 3982 was already
correct BUT the short-circuit check at line 3875 used `row_key={"date": date, "data_type": "XG"}` (no `league_id`). If a
pre-sharding-era run wrote that unsharded row, the short-circuit fires on every subsequent run and skips the per-league
loop. Legacy data stays un-sharded.

**Fixed in `instruments-service 8a91324`**: short-circuit now checks that EVERY expected Prediction-classified Understat
league has its own per-league row. Legacy date-aggregate row ignored, so pre-sharding shards back-fill on next adapter
run.

### Bugs 6-7 — AF enrichment entities + SFI STANDINGS emit single-row manifest (not yet fixed)

The 2024-09-15 manifest audit showed the same single-row-per-date bug on: `FIXTURE_STATS`, `FIXTURE_EVENTS`,
`FIXTURE_LINEUPS`, `PLAYER_STATS`, `INJURIES`, `STANDINGS`. Each data_type has exactly 1 manifest row for 2024-09-15.
These paths live in the AF enrichment branches of `engine/orchestrator.py` and need the same per-league loop pattern my
1682 fix introduced for FIXTURES (and that Transfermarkt PLAYER_VALUES + Understat already use at lines 4239 + 3982
respectively).

Phases 4-5 below cover these. **Not yet shipped.**

## Blast radius

- **instruments-service** (only):
  - `instruments_service/reference_data/adapters/sports/adapters/api_football.py` — Pydantic model update (Bug 1).
  - `instruments_service/engine/orchestrator.py` — UnboundLocal fix (Bug 2), 404 handling (Bug 3).

## Pre-audit manifest

| Bug | File                                                      | Line                                                | Action                                                  |
| --- | --------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------- |
| 1   | `reference_data/adapters/sports/adapters/api_football.py` | `class ApiFootballFixture` goals sub-model          | Change `home: int → int \| None`, same for `away`.      |
| 2   | `engine/orchestrator.py` ≈821                             | conditional import of `get_leagues_needing_refresh` | Hoist import to module-level OR add defensive fallback. |
| 3   | `engine/orchestrator.py` fixture_mapping_write path       | catches wrong error or treats 404 as critical       | Downgrade 404-on-future-date to INFO + skip.            |

## Success criteria

- Forward-poll VM log shows zero `validation errors for ApiFootballFixture` warnings on future-date runs.
- Forward-poll VM log shows zero `cannot access local variable` errors.
- Forward-poll VM log shows zero `CRITICAL unknown error` for absent instrument_availability parquets on future dates.
- Unit tests for each bug:
  - Bug 1: synthetic API-Football response with `{"goals": {"home": null, "away": null}}` → model validates + produces
    row with None.
  - Bug 2: payload 8 shape (or the handler dispatch that triggered it) → runs without UnboundLocalError.
  - Bug 3: synthetic fixture-mapping-write call on a date with no parquet → returns gracefully (no raise, INFO log).
- `bash instruments-service/scripts/quality-gates.sh` green.
- Re-run forward-poll VM for 2026-04-21..2026-04-28 → log clean.

## Phases

### Phase 1: Bug 1 — Pydantic goals None [PARALLEL]

- [ ] [AGENT] P0. Update `ApiFootballFixture.goals` sub-model: `home: int | None`, `away: int | None`.
- [ ] [AGENT] P0. Check all consumers (grep `goals.home|goals.away` in instruments-service + downstream). Update any
      `int` assumption.
- [ ] [AGENT] P0. Unit test covering unplayed-fixture payload.

### Phase 2: Bug 2 — UnboundLocalError [PARALLEL]

- [ ] [AGENT] P0. Locate the `get_leagues_needing_refresh` reference at orchestrator.py ≈821. Inspect: is it a deferred
      import under an `if` block? Hoist to module-level OR add the missing branch.

- [ ] [AGENT] P0. Unit test: call the handler path that triggered payload 8's failure. Assert no UnboundLocalError.

### Phase 3: Bug 3 — graceful 404 on future dates [PARALLEL]

- [ ] [AGENT] P0. In the fixture-mapping-write path, catch the 404 explicitly. If the date is in `[today, today+N]`
      (N=forward-poll horizon per codex §4) AND no fixtures were fetched, log INFO and skip. Otherwise retain ERROR
      behaviour (missing parquet for a past date IS a problem).

- [ ] [AGENT] P0. Unit test: mock GCS 404 for a future date; assert INFO log + no exception.

### Phase 4: Bugs 4-5 — WEATHER + XG per-league shard — **SHIPPED 2026-04-21 `8a91324`**

- [x] [AGENT] P0. OpenMeteo WEATHER success path: compute per-league row_count from `fixtures_df` × captured
      `venue_id`s, emit `manifest.add(league_id=lid)` per league + `record_empty(league_id=lid)` for in-season expected
      leagues with no captures. **Done.**
- [x] [AGENT] P0. OpenMeteo WEATHER "all covered" skip path: back-fill per-league captured rows from `fixtures_df`
      (idempotent — ManifestWriter dedups). **Done.**
- [x] [AGENT] P0. Understat XG short-circuit: check per-league row existence, not date-level. **Done.**
- [ ] [AGENT] P0. Re-smoke: `bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh` can't test these
      (WEATHER + XG are not AF). Instead, fire om-smoke + us-smoke with `--force-window` or
      `VM_SPORTS_ENTITY=WEATHER/XG` on a date with EPL matches (e.g. 2024-09-15). Verify post-VM manifest has ≥6
      per-league rows for XG and ≥N per-league rows for WEATHER where N = leagues-with-fixtures that day.

### Phase 5: Bugs 6-7 — AF enrichment entities + STANDINGS per-league shard

- [ ] [AGENT] P0. Apply the per-league empty-loop pattern (my 1682 fix for FIXTURES) to AF enrichment entities in
      `engine/orchestrator.py`: - `FIXTURE_STATS` success + skip paths - `FIXTURE_EVENTS` ditto - `FIXTURE_LINEUPS`
      ditto - `PLAYER_STATS` ditto - `INJURIES` ditto - `STANDINGS` (per-league by definition — fix may be trivial) Each
      path must iterate `get_expected_leagues_for_source("api_football", classifications=[...])` and emit per-league
      `manifest.record_empty` for leagues in-season but not captured.

- [ ] [AGENT] P0. Unit tests per entity: synthetic adapter response covering 2 in-season leagues out of 6 expected →
      assert 2 captured + 4 empty_confirmed manifest rows.

- [ ] [AGENT] P0. End-to-end smoke: fire
      `launch-api-football-backfill-vm.sh --entity FIXTURE_STATS 2024-09-15 2024-09-15`, verify manifest rows > 20 for
      FIXTURE_STATS on that date.

### Phase 6: End-to-end smoke [SEQUENTIAL, after Phases 1-5]

- [ ] [AGENT] P0. Launch a fresh forward-poll VM:
      `bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh --entity FIXTURES 2026-04-28 2026-05-05`.
- [ ] [AGENT] P0. Tail the VM GCS log. Assert zero warnings/errors of the three classes above.

### Phase 7: QG [SEQUENTIAL]

- [ ] [AGENT] P0. `bash instruments-service/scripts/quality-gates.sh` green.
- [ ] [AGENT] P0. Commit + quickmerge (`--agent`). Separate commits per bug recommended for cleaner revert.

## Dependency graph

```
Phase 1 (Bug 1) ┐
Phase 2 (Bug 2) ├─► Phase 6 (smoke) ─► Phase 7 (QG + merge)
Phase 3 (Bug 3) ┤
Phase 4 (WX + XG) ┤       ← SHIPPED `8a91324`, re-smoke pending
Phase 5 (AF enr + STND) ┘
```

## Out of scope

- Broader schema provenance audit of api-football.py adapter models — narrow to these bugs.
- Logging level hygiene across the orchestrator — separate sweep.
- FootyStats per-league sharding — already correct (per-league sub-dir sharding confirmed by smoke; 26 manifest rows per
  entity for 2024-09-15).
- Transfermarkt per-league sharding — already correct (55 PLAYER_VALUES rows per smoke).
