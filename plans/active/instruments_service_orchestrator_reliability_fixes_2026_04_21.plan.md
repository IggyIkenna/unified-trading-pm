---
title: "instruments-service Orchestrator Reliability Fixes (Pydantic None-Goals / UnboundLocal / Future-Date 404)"
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
    code: C0
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

### Phase 4: End-to-end smoke [SEQUENTIAL, after Phases 1-3]

- [ ] [AGENT] P0. Launch a fresh forward-poll VM:
      `bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh     --entity FIXTURES 2026-04-28 2026-05-05`.
- [ ] [AGENT] P0. Tail the VM GCS log. Assert zero warnings/errors of the three classes above.

### Phase 5: QG [SEQUENTIAL]

- [ ] [AGENT] P0. `bash instruments-service/scripts/quality-gates.sh` green.
- [ ] [AGENT] P0. Commit + quickmerge (`--agent`). Separate commits per bug recommended for cleaner revert.

## Dependency graph

```
Phase 1 (Bug 1) ┐
Phase 2 (Bug 2) ├─► Phase 4 (smoke) ─► Phase 5 (QG + merge)
Phase 3 (Bug 3) ┘
```

## Out of scope

- Broader schema provenance audit of api-football.py adapter models — narrow to these three bugs.
- Logging level hygiene across the orchestrator — separate sweep.
