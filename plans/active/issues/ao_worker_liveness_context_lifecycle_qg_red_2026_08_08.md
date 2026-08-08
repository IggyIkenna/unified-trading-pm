---
doc_type: issue
title: "agent-orchestrator quality-gates.sh RED on live-defi-rollout — 6 test failures in worker_liveness/context_lifecycle, pre-existing (not caused by this session's change)"
summary: >-
  `bash scripts/quality-gates.sh --no-fix` on a freshly-pulled `live-defi-rollout` HEAD (agent-orchestrator@3d4abba)
  fails with 6 test failures, all in `tests/test_context_lifecycle.py` and `tests/test_worker_liveness.py`. Verified
  pre-existing (not caused by this session's own commit, `feat(plan-hygiene): expose _parse_open_todos via cross-repo
  subprocess wrapper` — a single new, isolated file with zero overlap with `server/worker_liveness/` or
  `server/context_lifecycle.py`) by reproducing `test_working_spinner_not_kicked` standalone with no other diff
  present. Two distinct bugs in `server/worker_liveness/__init__.py`: (1) line 661 compares
  `derived_ctx_pct > slot_row.context_used_pct` where a test's `MagicMock` slot row leaks through untyped, causing
  `TypeError: '>' not supported between instances of 'int' and 'MagicMock'`; (2) line 520's `_git_surfaces_pass`
  does `int(sid) for sid in rows` where `rows` yields `types.SimpleNamespace` objects instead of int-coercible
  values, causing `TypeError: int() argument must be a string, a bytes-like object or a real number, not
  'types.SimpleNamespace'` (logged as a caught/swallowed error each test run, so it fires quietly on every tick, not
  just in tests). Recent commits to `server/worker_liveness/__init__.py` (`c6e6d98 fix(context): measure worker
  context from transcripts, learn window per model`, and 3 preceding same-day context-lifecycle commits) are the
  likely introduction point — the mock/fixture shape the tests use appears to predate a recent refactor of the
  context-probe integration.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, qg-red, worker-liveness, context-lifecycle, test-failure]
related: []
created: "2026-08-08"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by:
source: "slot-24, hit while running quality-gates.sh before quickmerging an unrelated plan-hygiene change"
depends_on: []
---

# agent-orchestrator QG red — worker_liveness/context_lifecycle test failures

## Evidence

`bash scripts/quality-gates.sh --no-fix` on `agent-orchestrator@3d4abba` (live-defi-rollout HEAD, 2026-08-08):

```
FAILED tests/test_context_lifecycle.py::test_worker_force_rearms_after_an_observed_compaction
FAILED tests/test_context_lifecycle.py::test_ineffective_force_rearms_after_retry_window
FAILED tests/test_context_lifecycle.py::test_observed_compaction_resets_ineffective_counter
FAILED tests/test_context_lifecycle.py::test_repeated_ineffective_forces_recover_the_wedged_session
FAILED tests/test_context_lifecycle.py::test_sub_threshold_session_still_gets_its_full_retry_budget
FAILED tests/test_worker_liveness.py::TestWorkerLivenessKicker::test_working_spinner_not_kicked
6 failed, 2744 passed, 2 skipped, 2 warnings in 230.92s
```

Reproduced `test_working_spinner_not_kicked` in complete isolation (`pytest tests/test_worker_liveness.py::
TestWorkerLivenessKicker::test_working_spinner_not_kicked -x`), same traceback, confirming this is not an artifact
of the full-suite run order.

**Pre-existing, not caused by this session**: `git diff --name-only HEAD~1 HEAD` on the commit that hit this
(`3d4abba feat(plan-hygiene): expose _parse_open_todos via cross-repo subprocess wrapper`) shows exactly one new
file (`scripts/plan_hygiene/dump_dispatchable_todos.py`), zero overlap with `server/worker_liveness/` or
`server/context_lifecycle.py`.

## Root cause (two distinct bugs, same module)

1. `server/worker_liveness/__init__.py:661` — `if derived_ctx_pct is not None and derived_ctx_pct > slot_row.context_used_pct:`
   compares against `slot_row.context_used_pct`, which in the failing test is a `MagicMock` attribute, not an int —
   the test's fixture never set a concrete value, and the comparison isn't guarded.
2. `server/worker_liveness/__init__.py:520` (`_git_surfaces_pass`) — `git_slot_ids = [int(sid) for sid in rows]`
   assumes `rows` yields int-coercible values; the actual rows are `types.SimpleNamespace` objects. This is caught
   and logged (`ERROR git surfaces pass: slot enumeration failed (skipping this tick)`) rather than crashing the
   whole pass, so it fires silently on every real tick too, not just in tests — a live-VM behavior gap worth fixing
   even though it isn't itself failing the test suite (the crash is bug 1).

## Recommended decision

- [ ] [BACKEND] P1. **Fix `server/worker_liveness/__init__.py:661`** — either guard the comparison
      (`isinstance(slot_row.context_used_pct, int)` / coerce with a default) or fix the test fixtures in
      `tests/test_worker_liveness.py` / `tests/test_context_lifecycle.py` to set a concrete
      `context_used_pct` on their mock `SlotRow` objects, whichever matches the intended contract (read
      `git log -p` on `c6e6d98` and the 3 preceding same-day context commits to see whether the mock shape
      changed or the comparison's assumption changed). **Done when**: all 6 currently-failing tests pass and
      `quality-gates.sh` is green on a fresh pull.
- [ ] [BACKEND] P2. **Fix `server/worker_liveness/__init__.py:520`'s `_git_surfaces_pass`** so `rows` yields
      int-coercible slot ids (or extract `.slot_id`/equivalent from the `SimpleNamespace` before `int()`) — this is
      silently swallowed on every real orchestrator tick (not just tests), which means the git-surfaces liveness
      pass has been a no-op in production since whatever commit introduced the `SimpleNamespace` shape. Grep
      recent `server/worker_liveness/` and `server/context_probe.py` commits for where `rows` is produced.

## Progress Log

- **2026-08-08 (slot-24)**: Filed + declared repo-blocker `RB-<id>` per RULES.md §4b after confirming the red is
  pre-existing (verified via isolated single-test reproduction with no other diff present) so my own unrelated
  plan-hygiene commit (`agent-orchestrator@3d4abba`) isn't blocked from shipping on someone else's red.
