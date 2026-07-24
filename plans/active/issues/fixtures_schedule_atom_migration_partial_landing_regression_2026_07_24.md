---
doc_type: issue
title:
  "PARTIAL landing of the FIXTURES→FIXTURES_SCHEDULE atom migration has already broken schedule-empty resolution in
  PRODUCTION, not just deployment-api's tests — UAC's SCHEDULE_DEFINING_DATA_TYPES changed today but the writer
  (instruments-service) has not"
summary: >-
  [BACKEND] While shipping an unrelated P0 (`deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md`), a
  full `quality-gates.sh` run on `deployment-api` surfaced 4 failing tests in `tests/unit/data_status/
  test_oow_denominator.py`, all asserting that a sports `FIXTURES` + `SOURCE_RETURNED_ZERO` empty cell is
  out-of-coverage-window (resolved, not a gap). Root cause: `unified-api-contracts`'s
  `_honest_coverage_logic.py::SCHEDULE_DEFINING_DATA_TYPES` was changed TODAY (`FIXTURES` literal → `FIXTURES_SCHEDULE`
  constant) as PART of the still-OPEN `[CODE] P0` todo 1 in `plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md`
  ("Migrate the fixtures manifest atom from the hardcoded `"FIXTURES"` literal to
  `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` across every writer/reader call site"). That todo's own scope list is
  instruments-service's writer/reader call sites (`sports_reference_fixtures.py`, `process_write.py`, `writers.py`,
  `catalogue.py`, `process_completeness.py`, `process_preflight.py`, `process_zero_records.py`,
  `sports_fixtures_daily_repoll.py`) PLUS the UAC constant — but the UAC-side change has landed while the
  instruments-service writer-side call sites have NOT (todo 1 is still `- [ ]`, unchecked). Since
  `unified_api_contracts.canonical.crosscutting._honest_coverage_logic.is_resolved_schedule_empty()` now requires
  `data_type == "FIXTURES_SCHEDULE"` to resolve a `SOURCE_RETURNED_ZERO` empty as out-of-window, and the real manifest
  rows written by instruments-service TODAY still carry `data_type="FIXTURES"` (writer not yet migrated), **every real
  "no matches that day" FIXTURES cell captured RIGHT NOW is misclassified as an in-window gap again** — reintroducing
  the exact ~93.7%-understated-coverage bug the 2026-06-23 fix (`cc69eef`) was written to solve. This is NOT just a
  stale-test problem; it is a live data-status/coverage-percent regression for the sports asset_group for as long as the
  writer-side half of the migration remains unshipped.
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-api-contracts, instruments-service, deployment-api]
scope: [engineer]
tags: [data-correctness, cross-repo, sports, honest-coverage, migration, regression]
related: [sports_closeout_batch1_ao_ready_2026_07_24, deployment_registry_reaper_not_draining_stale_entries_2026_07_24]
created: 2026-07-24
priority: P0
parent_epic: sports_master
source:
  "[BACKEND] slot-2, surfaced by a `quality-gates.sh` run on deployment-api while shipping an unrelated P0 (reaper-drain
  cancellation-timeout fix); confirmed via git blame + reading `_honest_coverage_logic.py` + the open migration todo
  itself."
execution_scope: orchestrator-agent
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# FIXTURES→FIXTURES_SCHEDULE atom migration: UAC changed, writer didn't — live regression window (2026-07-24)

## What I found

- `unified-api-contracts/unified_api_contracts/canonical/crosscutting/_honest_coverage_logic.py:302`:
  `SCHEDULE_DEFINING_DATA_TYPES: Final[frozenset[str]] = frozenset({FIXTURES_SCHEDULE})` — no longer accepts the literal
  `"FIXTURES"`.
- This is cited, in the code's OWN comment (lines 295-299), as part of
  `plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md` todo 1, which is **still open** (`- [ ]`, not `[x]`) and
  whose scope explicitly lists ONLY instruments-service writer/reader call sites (`sports_reference_fixtures.py`,
  `process_write.py`, `writers.py`, `catalogue.py`, `process_completeness.py`, `process_preflight.py`,
  `process_zero_records.py`, `sports_fixtures_daily_repoll.py`) as the remaining work — i.e. the UAC half of this todo
  has shipped, the instruments-service writer half has not.
- Effect: `is_resolved_schedule_empty(data_type, reason)` (`_honest_coverage_logic.py:316`) now returns `False` for
  every REAL manifest row with `data_type="FIXTURES"` (what instruments-service is still actually writing) even when
  `reason="SOURCE_RETURNED_ZERO"` — so `is_out_of_coverage_window()` → `compute_out_of_window_count()` →
  `compute_capture_status_counts()` all now count these cells as in-window gaps again.
- Confirmed via deployment-api's own test suite: 4 tests in `tests/unit/data_status/test_oow_denominator.py`
  (`TestScheduleDefiningFixturesEmptyResolved` and `TestComputeCaptureStatusCountsPopulatesOOW`) fail on a clean
  `live-defi-rollout` HEAD (verified via `git stash` — pre-existing, not introduced by my session's changes), all
  asserting the OLD (correct-until-today) `"FIXTURES"`-literal behavior.
- I did NOT change `_honest_coverage_logic.py`, `SCHEDULE_DEFINING_DATA_TYPES`, or any instruments-service writer — this
  is squarely the still-open todo 1's scope, actively owned elsewhere; fixing it myself risks colliding with whoever
  picks that todo up next; I only fixed a SEPARATE, unrelated, low-risk drift in the same deployment-api QG run
  (`EMPTY_REASON_KEYS` missing the new `EXPECTED_SUBGRAPH_DEINDEXED` UAC reason — a well-precedented one-line sync, same
  pattern as `8691f293`/`593327a`).

## Why it matters

- This is a **live data-correctness regression** for the sports asset_group's honest-coverage/completion-% numbers — per
  CLAUDE.md's data-pipeline-correctness HARD RULE, this is exactly the class of finding that should NOT wait for routine
  triage.
- It also means `deployment-api`'s full `quality-gates.sh` is currently RED for every slot (not just this task) until
  either (a) todo 1 finishes (writer side ships, self-healing this), or (b) `SCHEDULE_DEFINING_DATA_TYPES`/
  `is_resolved_schedule_empty` is made to accept BOTH atoms during the transition window, or (c) deployment-api's own
  reader path is migrated in lockstep. I declared a `qg_red` repo-blocker for `deployment-api` citing this doc so other
  slots' unrelated work isn't silently stuck without visibility.

## Recommended decision

Escalating to the operator/main given severity. Two options, either resolves it:

- **(A) Fastest fix — finish todo 1's writer-side migration** (instruments-service call sites) so real manifest rows
  start carrying `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` — this self-heals both the regression and the 4 deployment-api
  test failures with zero code change on the deployment-api side. Preferred if the writer-side migration is close to
  ready.
- **(B) Stop-gap — make `SCHEDULE_DEFINING_DATA_TYPES`/`is_resolved_schedule_empty` accept the OLD `"FIXTURES"` literal
  ALSO, for the duration of the transition**, so today's still-`"FIXTURES"`-tagged manifest rows keep resolving
  correctly until the writer migration ships, then drop the old literal once the corpus census (the todo's own "done
  when" criterion) confirms zero remaining `"FIXTURES"` rows. Preferred if the writer-side migration will take longer
  than an acceptable regression window.

Either way, deployment-api's `test_oow_denominator.py` 4 failing tests should NOT be "fixed" by simply updating their
fixtures to `"FIXTURES_SCHEDULE"` — that would hide the fact that production data still says `"FIXTURES"` today.
