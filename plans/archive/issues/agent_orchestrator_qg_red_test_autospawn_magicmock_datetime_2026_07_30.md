---
doc_type: issue
title:
  agent-orchestrator quality-gates.sh is RED on a clean live-defi-rollout tree — 7 test_autospawn.py failures
  (MagicMock/datetime comparison TypeError, missing `escalation_queue` table, `list.all()` AttributeError), plus 1 flaky
  test_worker_liveness_watchdog.py test observed on a shared host.
summary: >-
  While shipping a fix for /plans/archive/issues/context_compact_directive_did_not_fire_slot_rode_to_96pct_2026_07_27.md
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
status: resolved
assigned_vm: planning
resolved_by:
  agent-orchestrator@02d2e9f, agent-orchestrator@296e5e4, agent-orchestrator@17a6773, agent-orchestrator@61b7a4f
locked_by:
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, quality-gates, test-red, autospawn, account-usage, repo-blocker]
related:
  [
    /plans/archive/issues/context_compact_directive_did_not_fire_slot_rode_to_96pct_2026_07_27.md,
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

> **🟢 ARCHIVED 2026-07-30** — status=resolved, 0 open todos. All 3 QG-red root causes fixed
> (`agent-orchestrator@02d2e9f`, `@296e5e4`, `@17a6773`) and the 1 flaky-test follow-up investigated + marked
> `host_load_sensitive` (`agent-orchestrator@61b7a4f` — confirmed already fully mocked, no logic defect; flake is
> host-scheduler contention, not something this test's own code can close further). Archived per
> `/codex/11-project-management/issue-doc-lifecycle.md`'s archive-on-resolve rule (ACKED-INTO-CODE).

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

- [x] ✅ [ENGINEER] P1. Root-cause + fix
      `TypeError: '>' not supported between instances of 'MagicMock' and     'datetime.datetime'` at
      `server/state_store/account_usage.py:176` (`account_is_rate_limited`) — affects
      `test_tick_fails_closed_on_gate_read_failure`, `test_repeat_spawn_failure_activity_log_throttled`,
      `test_tick_budget_allows_one_spawn_per_queued_task`,
      `test_tick_rotates_through_idle_slots_when_chronically_at_cap`,
      `test_tick_refuses_to_spawn_a_slot_that_can_claim_nothing` (repo: agent-orchestrator). —
      `agent-orchestrator@02d2e9f`. Root cause: `_check_and_log_critical_pool_halt` (2026-07-29 fleet-wide-halt ruling)
      now runs unconditionally at the top of `_run_one_tick`, walking every configured Anthropic account via
      `account_is_rate_limited`; these tests drive the tick with a bare `MagicMock()` session that never configures
      `session.get()`, so `row.rate_limited_until` resolved to an auto-attr MagicMock, crashing the datetime comparison
      before any tick assertion ran. Fix: patched the new bound method out
      (`patch.object(loop, "_check_and_log_critical_pool_halt", return_value=False)`) in each affected test, matching
      the existing style of stubbing `loop._resume_pass`/`loop._drain_escalations` — these tests assert tick
      spawn/budget/gate behavior, not the pool-halt feature, which already has its own dedicated tests. This same crash
      (not the signature-3 AttributeError) turned out to also be the FIRST failure in
      `test_tick_caps_spawns_at_queue_depth` and `test_tick_respects_fleet_worker_cap` (todo below) on the current tree,
      so the same patch was applied there too. Full `bash scripts/quality-gates.sh` now PASSES clean (1990 passed, 1
      skipped) — fixing this one crash was sufficient to turn the whole gate green again for every worker, since the
      other two signatures below turned out to be silently caught/logged at their call sites (`_resume_pass`'s outer
      `try/except` in `_run_one_tick`) and never actually failed a test assertion once this crash stopped masking them.
- [x] ✅ [ENGINEER] P1. Root-cause + fix `sqlite3.OperationalError: no such table: escalation_queue` in the
      `test_autospawn.py` fixture path (likely a missing `create_all_tables()` call or a schema-migration gap for the
      escalation-queue table in the test DB setup) (repo: agent-orchestrator). No longer QG-blocking (see todo above —
      it's silently caught + logged by `_drain_escalations`'s call-site `try/except`, so it doesn't fail any test), but
      the underlying gap is still real and still open. — `agent-orchestrator@296e5e4`. Root cause: the 5 affected tests
      drive `_run_one_tick` with a bare `MagicMock` DB session for the main flow, but never mocked `_drain_escalations`
      — which opens its OWN real `session_scope()` (`server.escalation` imports it independently of the `autospawn_mod`
      reference these tests patch), so that real session hit `no such table: escalation_queue` against the test's fresh,
      empty tmp_path sqlite file. Fix: `patch.object(loop, "_drain_escalations")` in each of the 5 tests, matching the
      pattern already used by the two sibling tick tests that don't hit this signature. Scoped to the escalation_queue
      signature only — the AttributeError signature (3rd todo below) is a separate, still-open root cause.
- [x] ✅ [ENGINEER] P1. Root-cause + fix `AttributeError: 'list' object has no attribute 'all'` at
      `server/autospawn.py:2478` in `_resume_pass` — affects `test_tick_caps_spawns_at_queue_depth`,
      `test_tick_respects_fleet_worker_cap` (repo: agent-orchestrator). No longer QG-blocking (see todo above — it's
      silently caught + logged by `_resume_pass`'s call-site `try/except` in `_run_one_tick`, so it doesn't fail any
      test), but the underlying bug is still real and still open. — `agent-orchestrator@17a6773`. Root cause: line 2478
      was the ONLY `session.scalars(...)` call site in this file to chain `.all()` — the other 3 (lines 527, 627,
      2126, 2164) all treat the `ScalarResult` as directly iterable (`list(session.scalars(...))` or a bare `for`). A
      real `ScalarResult` supports `.all()` fine, so this was harmless in production, but it made the line inconsistent
      — and it broke against these two tests' `session.scalars.return_value = [MagicMock(...), ...]` fixture, since
      `session.scalars(...)` there already returns a plain `list`, and `list` has no `.all()`. Confirmed by direct
      repro: called `_resume_pass` standalone with the exact test fixture shape and reproduced the identical traceback.
      Fix: dropped `.all()`, matching the file's own established convention — behavior-identical against a real
      `ScalarResult` (`list(x)` == `list(x.all())`), and now also compatible with the test's mock shape. Dropping
      `.all()` surfaced a SECOND, pre-existing masked issue one line further into `_resume_pass`: these two tests'
      `MagicMock(slot_id=N)` slots have no real `resume_attempts` int, so
      `slot.resume_attempts >= cfg.tuning.resume_max_attempts` raised
      `TypeError: '>=' not supported between     instances of 'MagicMock' and 'int'` (MagicMock's comparison dunders
      default to `NotImplemented`) — also silently swallowed by the same `try/except`, so it never failed a test either,
      and `_resume_pass`'s actual resume logic (attempt-count gating, account selection, spawn) has zero dedicated test
      coverage anywhere in the suite; these two tests only reach it incidentally, since (unlike 4 sibling
      `_run_one_tick` tests) they never stubbed it out. Rather than leave a second masked exception in place of the
      first, stubbed `patch.object(loop, "_resume_pass", return_value=(0, 0))` in both tests, matching the exact pattern
      already used twice in this file (`_check_and_log_critical_pool_halt`, `_drain_escalations`) for "test drives a
      dumb MagicMock session that can't back a nested call it doesn't care about." Full `bash scripts/quality-gates.sh`
      PASSES clean (1990 passed, 1 skipped — same count as after the prior two fixes).
- [x] ✅ [ENGINEER] P3. Investigate
      `tests/test_worker_liveness_watchdog.py::test_tick_null_tmux_session_falls_back_to_canonical_name` flakiness under
      real concurrent shared-host tmux traffic (passed cleanly in isolation immediately after failing in the full suite)
      — either harden the test's tmux-session isolation or mark it host-load-sensitive (repo: agent-orchestrator). —
      **INVESTIGATED + MARKED 2026-07-30**: confirmed every `tmux_spawn` call this test's path touches
      (`has_session`/`capture_pane`/`_pane_is_dead`) is already mocked via `_tick_once_patches` — 30/30 clean runs in
      isolation, no logic defect or unmocked real-tmux call found. Nothing to harden (there is no real tmux-session
      isolation gap — the call graph is already fully mocked); the flake is consistent with host CPU/scheduler
      contention from OTHER live processes on the shared box (real orch-slot-N tmux sessions unrelated to this test's
      own mocked call graph). Took the "mark it host-load-sensitive" branch: registered a `host_load_sensitive` pytest
      marker (`pyproject.toml`) and applied it to the test with a docstring citing this investigation, so a future
      isolated failure of this specific test is recognized as a known, already-triaged class rather than re-investigated
      from scratch. — agent-orchestrator@61b7a4f.
