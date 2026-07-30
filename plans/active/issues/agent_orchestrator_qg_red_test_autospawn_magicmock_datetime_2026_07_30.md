---
doc_type: issue
title:
  agent-orchestrator quality-gates.sh is RED on a clean live-defi-rollout tree — 7 test_autospawn.py failures
  (MagicMock/datetime comparison TypeError, missing `escalation_queue` table, `list.all()` AttributeError), plus 1 flaky
  test_worker_liveness_watchdog.py test observed on a shared host.
summary: >-
  While shipping a fix for /plans/active/issues/context_compact_directive_did_not_fire_slot_rode_to_96pct_2026_07_27.md
  (progress_slot's compact_now directive had no activity-log record), `bash scripts/quality-gates.sh` failed on
  agent-orchestrator with 7 pre-existing failures entirely unrelated to that change. Verified pre-existing via the
  RULES.md §4b protocol: stashed the fix, re-ran the exact failing tests on a byte-identical clean HEAD (commit at time
  of filing — live-defi-rollout tip), and got the SAME failures with SAME tracebacks; restored the fix afterward. Three
  distinct root causes across the 7 tests: (1) `TypeError: '>' not supported between instances of 'MagicMock' and
  'datetime.datetime'` at `server/state_store/account_usage.py:176` inside `account_is_rate_limited` — a fixture/mock
  now yields a MagicMock where a concrete datetime is expected; (2) `sqlite3.OperationalError: no such table:
  escalation_queue` — a test DB fixture is missing a table `server/autospawn.py`'s `_run_one_tick` now queries; (3)
  `AttributeError: 'list' object has no attribute 'all'` at `server/autospawn.py:2478` in `_resume_pass` —
  `session.scalars(...).all()` chained onto something that's already a list (a mock or a changed SQLAlchemy call shape).
  A 2nd, separate full run additionally showed
  `tests/test_worker_liveness_watchdog.py::test_tick_null_tmux_session_falls_back_to_canonical_name` fail once, then
  pass cleanly in isolation immediately after — flaky under this shared host's real concurrent tmux-session traffic
  (many live orch-slot-N sessions), not a code defect; captured for awareness but NOT one of the 7 tracked fix todos
  below.
status: open
assigned_vm: planning
resolved_by:
locked_by:
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, quality-gates, test-red, autospawn, account-usage, repo-blocker]
related:
  [
    /plans/active/issues/context_compact_directive_did_not_fire_slot_rode_to_96pct_2026_07_27.md,
    /codex/12-agent-workflow/pre-task-plan-conflict-check.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
priority: P1
parent_epic: orchestrator_master
source: "slot 2 (data_engineering), verifying quality-gates.sh before shipping an unrelated progress_slot fix"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

`bash scripts/quality-gates.sh` in `agent-orchestrator` at live-defi-rollout tip fails its pytest stage with:

```
FAILED tests/test_autospawn.py::test_tick_fails_closed_on_gate_read_failure
FAILED tests/test_autospawn.py::test_repeat_spawn_failure_activity_log_throttled
FAILED tests/test_autospawn.py::test_tick_caps_spawns_at_queue_depth - TypeErr...
FAILED tests/test_autospawn.py::test_tick_budget_allows_one_spawn_per_queued_task
FAILED tests/test_autospawn.py::test_tick_respects_fleet_worker_cap - TypeErr...
FAILED tests/test_autospawn.py::test_tick_rotates_through_idle_slots_when_chronically_at_cap
FAILED tests/test_autospawn.py::test_tick_refuses_to_spawn_a_slot_that_can_claim_nothing
```

Three distinct failure signatures across those 7:

1. `TypeError: '>' not supported between instances of 'MagicMock' and 'datetime.datetime'` at
   `server/state_store/account_usage.py:176` (`account_is_rate_limited`'s
   `_ss.to_utc(row.rate_limited_until) > _ss.utcnow()` comparison).
2. `sqlite3.OperationalError: (sqlite3.OperationalError) no such table: escalation_queue` — a SELECT against
   `escalation_queue` fails because the test's in-memory/tmp DB schema doesn't have that table.
3. `AttributeError: 'list' object has no attribute 'all'` at `server/autospawn.py:2478` inside `_resume_pass`:
   `session.scalars(select(SlotRow).where(SlotRow.resume_pending_session_id.is_not(None))).all()` — something upstream
   is already returning a `list`, not a `ScalarResult`.

## Why it matters

This is a fleet-wide blocker: `quality-gates.sh` is the mandatory pre-commit gate (CLAUDE.md § "Quality gates BEFORE
COMMIT — the commit is the per-repo quality boundary (HARD RULE)"), and it's currently RED on a clean tree for
`agent-orchestrator` — meaning no worker can ship ANY change to this repo via the normal Pass-1/Pass-2 flow without
hitting this same red, regardless of what they're actually working on. It also means the `agentkeeper`/orchestrator's
own CI-facing signal is unreliable right now for autospawn + account-usage + escalation-queue behavior specifically.

## Verification (pre-existing, not caused by my in-flight change)

```
git stash push --include-untracked -m "verify"
uv run python -m pytest tests/test_autospawn.py -k "test_tick_fails_closed_on_gate_read_failure or test_tick_caps_spawns_at_queue_depth" -q
# same 2 failures, same tracebacks, on clean HEAD
git stash pop
```

## Recommended decision

Root-cause and fix each of the 3 failure signatures in `agent-orchestrator`. This is scoped enough to be one plan; not
something I should absorb into my unrelated task (per CLAUDE.md findings triage — outside-plan work that isn't
small+clear gets its own issue doc).

## Todos

- [ ] [ENGINEER] P1. Root-cause + fix
      `TypeError: '>' not supported between instances of 'MagicMock' and     'datetime.datetime'` at
      `server/state_store/account_usage.py:176` (`account_is_rate_limited`) — affects
      `test_tick_fails_closed_on_gate_read_failure`, `test_repeat_spawn_failure_activity_log_throttled`,
      `test_tick_budget_allows_one_spawn_per_queued_task`,
      `test_tick_rotates_through_idle_slots_when_chronically_at_cap`,
      `test_tick_refuses_to_spawn_a_slot_that_can_claim_nothing` (repo: agent-orchestrator).
- [ ] [ENGINEER] P1. Root-cause + fix `sqlite3.OperationalError: no such table: escalation_queue` in the
      `test_autospawn.py` fixture path (likely a missing `create_all_tables()` call or a schema-migration gap for the
      escalation-queue table in the test DB setup) (repo: agent-orchestrator).
- [ ] [ENGINEER] P1. Root-cause + fix `AttributeError: 'list' object has no attribute 'all'` at
      `server/autospawn.py:2478` in `_resume_pass` — affects `test_tick_caps_spawns_at_queue_depth`,
      `test_tick_respects_fleet_worker_cap` (repo: agent-orchestrator).
- [ ] [ENGINEER] P3. Investigate
      `tests/test_worker_liveness_watchdog.py::test_tick_null_tmux_session_falls_back_to_canonical_name` flakiness under
      real concurrent shared-host tmux traffic (passed cleanly in isolation immediately after failing in the full suite)
      — either harden the test's tmux-session isolation or mark it host-load-sensitive (repo: agent-orchestrator).
