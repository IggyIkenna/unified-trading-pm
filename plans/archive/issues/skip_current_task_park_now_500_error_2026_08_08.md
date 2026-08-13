---
doc_type: issue
title: "POST /api/slots/{N}/skip-current-task returns 500 when park_now:true — plain skip (park_now:false) works fine"
summary: >-
  Live-hit 2026-08-08 (slot 16) -- calling POST /api/slots/16/skip-current-task with reason_code=GATED and park_now=true
  against a real queued task (sports_af_full_entity_completion-018, backed by an active
  plans/archive/2026_08/issues/sports_af_full_entity_completion_2026_08_03.md checkbox row) returned a bare Internal
  Server Error / HTTP 500 on two consecutive attempts. The IDENTICAL call with park_now omitted (defaults false) against
  the SAME task succeeded (HTTP 200, task_skipped plus fleet_cooldown_armed=true), and the task remained the slot's
  current_task across both failed attempts (confirmed by the retry payload's task_id still matching) -- consistent with
  the exception being raised and the session_scope() transaction rolling back before ss.clear_slot_assignment ever ran.
  server/routes/slots_ops.py's skip_current_task calls auto_park.manual_park(...) only when park_now=True (the else
  branch, maybe_auto_park, is what the plain-skip path exercises and that one worked) -- narrows the fault to
  server/auto_park.py manual_park or something it calls (park_condition_name / ss.set_prerequisite / ss.mark_parked) for
  this specific task shape. No server log was reachable from the worker slot to capture the actual traceback (uvicorn
  process 2088889 on the shared host pipes to fds with no readable log-file path found from .tabs/16) -- a fix needs to
  run locally against the live DB/backlog to get the real stack trace, not guess from code reading alone.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, skip-current-task, park_now, auto_park, 500-error, bug]
related: [/plans/archive/2026_08/issues/sports_af_full_entity_completion_2026_08_03.md]
created: 2026-08-08
author: slot-16
last_updated: 2026-08-08
priority: P2
parent_epic: orchestrator_master
source:
  "Discovered incidentally while skipping sports_af_full_entity_completion-018 (INJURIES backfill queued behind the
  af-backfill-* singleton lock) — not this doc's own scope, filed per findings-triage."
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
drift_direction: advance-code
resolved_by: agent-orchestrator@55aedc9
locked_by:
depends_on: []
---

> **🟢 ARCHIVED 2026-08-08** — `status: resolved` with zero open todos; archived per
> [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md)'s
> archive-immediately rule. Root cause found + fixed: `resolved_by: agent-orchestrator@55aedc9`. See the Progress Log
> below for the full root-cause writeup.

# `skip-current-task` 500s when `park_now: true`

## What I found

`POST /api/slots/16/skip-current-task` with body `{"reason": "...", "reason_code": "GATED", "park_now": true}` against a
live, currently-dispatched task (`sports_af_full_entity_completion-018`) returned a bare `Internal Server Error`
(HTTP 500) — no JSON body, no detail — on two back-to-back attempts (identical payload). The exact same
reason/reason_code with `park_now` simply omitted (defaults to `false` per `SkipCurrentTaskRequest`) succeeded
immediately (HTTP 200):

```json
{
  "slot_id": 16,
  "task_skipped": "sports_af_full_entity_completion-018",
  "reason_code": "GATED",
  "fleet_cooldown_armed": true,
  "fleet_cooldown_next_check_at": "2026-08-08T17:29:23.157563Z",
  "park_now": false,
  "auto_parked_condition": null,
  ...
}
```

Reading `server/routes/slots_ops.py`'s `skip_current_task` (around line 990-1013): the `park_now=True` branch calls
`auto_park.manual_park(session, task_id, requested_by=..., reason=reason)` instead of `maybe_auto_park(...)` — the
`maybe_auto_park` path is what the successful plain-skip call exercised, so the fault is isolated to `manual_park`
(`server/auto_park.py:162`) or one of its calls: `park_condition_name(task_id)`, `save_backlog(...)`,
`ss.set_prerequisite(...)`, `ss.mark_parked(...)`. Nothing in a code read alone stood out as obviously wrong for this
task shape (`sports_af_full_entity_completion-018`, an issue-doc-checkbox-derived id) — needs a real traceback.

## Why it matters

`park_now=True` is the documented, intended mechanism for exactly this situation
(`external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25`, cited in the code's own docstring): "a
worker that hits an EXTERNAL gate... sets this so the task stays parked... rather than re-dispatching to a fresh worker
on every tick." Right now that path is unusable — any worker that legitimately needs a durable park (not just the
N-skip-threshold auto-park) will hit this 500 and has to fall back to a plain skip + fleet-cooldown instead, which is
weaker (cooldown expires; a durable park does not) and reintroduces the exact redispatch-churn risk the feature was
built to close (see the 2026-08-04 8-repeated-dispatch incident referenced in
`sports_af_full_entity_completion_2026_08_03.md`'s Progress Log for what that churn looks like in practice).

## Recommended decision

Reproduce locally against a real backlog task, get the actual traceback, and fix the root cause in `manual_park` (or
whatever it calls). Since the plain-skip path already covers the immediate need via `fleet_cooldown_armed`, this is not
urgent/blocking — but it's a real defect in a documented, intentionally-built recovery mechanism and should not silently
sit broken.

- [x] ✅ [BACKEND] P2. Reproduce `POST /api/slots/{N}/skip-current-task` with `park_now: true` against a live dispatched
      task, capture the actual traceback (run the server with stdout visible, or add temporary exception logging), and
      fix the root cause in `server/auto_park.py:manual_park` (or its callees `park_condition_name`/
      `ss.set_prerequisite`/`ss.mark_parked`) so a durable park via `skip-current-task {"park_now": true}` succeeds.
      (repo: agent-orchestrator) — agent-orchestrator@55aedc9

## Progress Log

**2026-08-08 (slot-18)**: Reproduced in an ISOLATED harness (own `.tabs/18` state.db + a scratch copy of `backlog.yaml`,
never the live production DB/backlog.yaml) that ran `register_cooldown()` immediately followed by
`auto_park.manual_park()` in the same DB transaction — exactly what `skip_current_task`'s `park_now=True` branch does.
Got the real traceback: `sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: dispatch_cooldowns.key`.

Root cause: `register_cooldown()` (`server/state_store/cooldown.py`) builds a brand-new `CooldownRow` and calls
`session.merge(merged)` but never flushes. The session factory runs `autoflush=False`, so on a task's FIRST
GATED/BLOCKED/PARKED decline (no prior row — exactly the case `park_now=True` is meant to handle, since it bypasses the
N-skip threshold), the merged row stays pending/unflushed and invisible to `session.get()`. Moments later in the SAME
transaction, `manual_park` → `mark_parked()` calls `session.get(CooldownRow, key)`, finds nothing, and falls back to
inserting a SECOND `CooldownRow` with the identical primary key — the commit-time `UNIQUE constraint failed` that
surfaced as a bare HTTP 500. The plain-skip (`park_now=False` → `maybe_auto_park`) path never hit this because it only
proceeds past its own `session.get()` check once `skip_count` crosses the auto-park threshold, by which point the row is
already committed from an earlier, separate request/transaction.

Fix: `register_cooldown()` now calls `session.flush()` right after the merge, so the row is immediately visible to any
same-transaction reader (`server/state_store/cooldown.py`). Added a regression test,
`test_park_now_true_parks_durably_on_the_first_decline` (`tests/test_skip_endpoint_cooldown_and_park.py`), covering the
exact first-decline `park_now=True` path — no existing test covered it. Full `quality-gates.sh` green (2792 passed).
Shipped `agent-orchestrator@55aedc9`.

Note: an earlier isolated-repro run against `maybe_auto_park`'s auto-threshold path (unrelated to the fix itself)
accidentally fired a REAL Slack notification to `agent-orchestrator-alerts` for `sports_closeout_track_s2_foldin-001`
("Task auto-parked") — the DB/backlog isolation didn't cover the Slack webhook credential. Verified via the live
`/api/backlog` that the real task's priority/prereqs were untouched (only the isolated copies were mutated), and posted
an immediate in-channel correction. No production state was affected.
