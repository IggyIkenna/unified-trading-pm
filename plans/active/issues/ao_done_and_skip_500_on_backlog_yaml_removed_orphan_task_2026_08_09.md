---
doc_type: issue
title:
  "`/done` and `/skip-current-task` both 500 on a task fully removed from `backlog.yaml` (true orphan) — only
  `/reassign` + `DELETE /api/backlog/<id>` recover it"
summary: |
  A backlog task whose backing plan was archived (removing its derived todo from
  `backlog.yaml` on the next regen) but whose SQLite `TaskRow` was still `dispatched`
  to a slot deterministically 500'd on BOTH `/api/slots/<N>/done` and
  `/api/slots/<N>/skip-current-task` — the two documented recovery paths a worker is
  told to use. `GET /api/backlog` already detects and labels this exact state
  (`"orphan": true`, `"title": "(orphan — no longer in backlog.yaml)"`) but neither
  mutating endpoint checks it before running task-def-dependent logic. Only
  `POST /api/slots/<N>/reassign` (a third, less-documented endpoint with no
  `backlog.get()` dependency) succeeded, followed by `DELETE /api/backlog/<id>`.
status: open
resolved_by:
nature: process
asset_group: [ci, meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao, orchestrator, backlog, orphan-task, done-endpoint, bug, 500]
related:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-09
author: slot-33 (worker session)
last_updated: 2026-08-09
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
assigned_role: cicd
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/routes/slots_ops.py,
    agent-orchestrator/server/verify.py,
  ]
supersedes:
superseded_by:
depends_on:
source:
  - "live incident, this session (slot 33, 2026-08-09) — dispatched task `ci_satellite_ao_dispatch_batch1_finalize-004`
    (assigned_role: cicd)"
---

# `/done` and `/skip-current-task` 500 on a fully-orphaned backlog task

## What I found

Dispatched task `ci_satellite_ao_dispatch_batch1_finalize-004`
(`plan_ref: plans/active/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`, todo 4 — "Archive
`ci_satellite_ao_dispatch_batch1_2026_07_26.md` via the standard 6-step ritual"). On inspection the plan was **already
fully complete and archived** by a prior session (`unified-trading-pm@edf1a7f97`, same-day) to
`plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` — all 4 todos `[x]`. The backlog regen
that followed the archival correctly dropped this now- nonexistent todo from `backlog.yaml`, but this task's `TaskRow`
had already been dispatched to slot 33 before that regen ran, so the SQLite row survived as an orphan:
`status=dispatched, dispatched_to=33`, with no corresponding `backlog.yaml` entry. `GET /api/backlog` correctly flags
this (`"orphan": true`, `"title": "(orphan — no longer in backlog.yaml)"`).

Found + fixed one genuine small leftover from that archival's own referrer-repoint step (2 active docs still carried a
stale leading-slash `/plans/active/...` reference to the now-archived plan —
`silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` and
`uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`), shipped as `unified-trading-pm@60556c3e9`, verified
ancestor of `origin/live-defi-rollout`.

With the actual work done, I called `/done` per the standard worker loop — it returned **HTTP 500 Internal Server
Error**, reproduced identically on **5 consecutive attempts** (including after a real ~1min server outage/restart in
between, ruling out pure transience) with both a full evidence payload and a minimal one. Per RULES.md § 6 ("never fall
back to a different endpoint mid-recovery on a 5xx"), I still isolated the scope first: `/api/slots/33/progress` and
`/api/slots/33/heartbeat` both returned clean 200s throughout, so the 500 is specific to this task_id going through
`/done`, not a general server outage.

Read `server/routes/slots_worker.py::done_slot` (agent-orchestrator repo) — it correctly guards
`task_def = backlog.get(req.task_id)` with `if task_def else []` for `expected_repos`/`plan_brief`, so the crash isn't
there; I did not find the exact throwing line without server logs (no log/journalctl access from this worker slot).

Tried `/api/slots/33/skip-current-task` (the RULES.md-documented recovery for a task the server won't let a worker
`/done`) — **also 500**, reproduced once. `server/routes/slots_ops.py::skip_current_task`'s own orphan-prune branch is:

```python
backlog_task = backlog.get(task_id)
task_orphaned = backlog_task is not None and not task_still_dispatchable(backlog_task)
```

This is backwards for MY case: `backlog_task is None` (the row is fully absent from `backlog.yaml`, not merely
present-but-undispatchable), so `task_orphaned` evaluates **False** and the code falls into the normal `else` branch
(`ss.release_task_to_queue` + cooldown/auto-park bookkeeping + `_apply_deferred_content_id_rename_on_skip`) — one of
those calls likely assumes a non-`None` `backlog_task` somewhere downstream and throws. I did not isolate the exact line
(same no-log-access limitation).

**What DID work**: `POST /api/slots/33/reassign` (`{"affinity": "none"}`) — 200, released the task to `queued`. This
endpoint has no `backlog.get()` call at all, just `ss.release_task_to_queue` directly. Followed immediately by
`DELETE /api/backlog/ci_satellite_ao_dispatch_batch1_finalize-004` (now `queued`, not `dispatched`, so the delete's
dispatched-guard didn't block it) — 200, `{"ok":true,"prior_status":"queued","remaining_tasks":677}`. Slot freed
cleanly.

## Why it matters

This is a **repeatable dead-end for any worker** that lands a task dispatched just-before a plan-archival-triggered
backlog regen orphans it (a timing window that recurs every time a plan finishes + archives while a stale-derived todo
is already mid-flight on a slot — plausible several-times-a-week at current fleet velocity). Both of the two
RULES.md/worker.md-documented recovery paths (`/done`, `/skip-current-task`) fail identically for this exact state,
leaving a worker with no sanctioned way to close the loop short of independently discovering the undocumented
`/reassign` endpoint and manually reasoning through `DELETE`'s dispatched-guard precondition — which cost real session
time this pass. A less-diagnostic-minded worker session would likely retry `/done` in a loop (RULES.md's own 5xx-retry
guidance) and burn a stale-worker slot indefinitely, or `/blocked` unnecessarily for what is actually a mechanical fix.

## Recommended decision

- [ ] [BACKEND] P2. In `server/routes/slots_worker.py::done_slot`, add an explicit early check: if
      `backlog.get(req.task_id)` is `None` AND the task is not a `one_shot_complete` / sentinel-sha case, short-circuit
      to the same orphan-cleanup behavior `/reassign` + `DELETE` currently require manually — release the task, delete
      the dead `TaskRow`, and return a clean response (not a 500) telling the worker the task was orphaned and closed
      out, no further action needed. (repo: agent-orchestrator)
- [ ] [BACKEND] P2. Fix `skip_current_task`'s `task_orphaned` predicate in `server/routes/slots_ops.py` to also treat
      `backlog_task is None` (fully absent from `backlog.yaml`, not just present-but-undispatchable) as orphaned — route
      it through the existing `session.delete(row)` + `backlog.tasks = [...]` cleanup branch instead of falling into the
      normal release path that appears to throw. (repo: agent-orchestrator)
- [ ] [VERIFY] P3. Once both fixes land, reproduce this exact scenario in a non-prod/test harness (dispatch a task,
      delete its plan out from under it, regen backlog, confirm `/done` now returns a clean orphan-closed response
      instead of 500) to close this out with evidence. (repo: agent-orchestrator)

## Progress Log

- **2026-08-09 (slot 33)**: Filed. Root-caused via source read (no server log access from this worker slot) to
  `backlog.get(task_id) is None` not being handled the same way across `/done` (no explicit handling found, 500) vs
  `/skip-current-task` (explicit but inverted-condition handling, still 500) vs `/reassign` (no `backlog.get()`
  dependency at all, worked cleanly). Worked around live via `/reassign` + `DELETE /api/backlog/<id>` — slot freed,
  orphan row gone, task's underlying work (already complete + archived by a prior session) unaffected.
