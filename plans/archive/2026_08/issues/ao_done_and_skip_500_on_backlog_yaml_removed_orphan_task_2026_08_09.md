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
status: resolved
resolved_by: agent-orchestrator@8db0b29 (2026-08-09) — all 3 todos done, non-prod e2e reproduction confirms both fixes
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
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
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

- [x] ✅ [BACKEND] P2. In `server/routes/slots_worker.py::done_slot`, add an explicit early check: if
      `backlog.get(req.task_id)` is `None` AND the task is not a `one_shot_complete` / sentinel-sha case, short-circuit
      to the same orphan-cleanup behavior `/reassign` + `DELETE` currently require manually — release the task, delete
      the dead `TaskRow`, and return a clean response (not a 500) telling the worker the task was orphaned and closed
      out, no further action needed. (repo: agent-orchestrator) — agent-orchestrator@3147392. Extracted into
      `_maybe_close_orphaned_done_task`/`_resolve_task_def_for_done` (called from `done_slot`) to keep `done_slot`'s
      C901 complexity within the 26-point gate; `verify._is_sentinel_sha` made public (`is_sentinel_sha`) so the new
      helper can consult it. Regression tests: `tests/test_done_orphan_task_closed.py` (real-sha orphan closes cleanly +
      sentinel-sha still falls through to normal completion), plus
      `tests/test_done_empty_sha_gate.py::test_done_proper_sentinel_sha_not_rejected` extended to cover the sentinel-sha
      carve-out against an empty backlog. Full `quality-gates.sh` green (2935 passed).
- [x] ✅ [BACKEND] P2. Fix `skip_current_task`'s `task_orphaned` predicate in `server/routes/slots_ops.py` to also treat
      `backlog_task is None` (fully absent from `backlog.yaml`, not just present-but-undispatchable) as orphaned — route
      it through the existing `session.delete(row)` + `backlog.tasks = [...]` cleanup branch instead of falling into the
      normal release path that appears to throw. (repo: agent-orchestrator) — agent-orchestrator@4f78629. Also guarded
      the orphan-delete against a `done`/`cancelled` `TaskRow` (a stale `slot.current_task` pointer to an
      already-completed task is normal — its regen-dropped backlog.yaml absence must NOT be treated as an orphan-to-
      delete, or it silently clobbers the existing terminal-status 409 guard from
      `ao_backlog_done_row_disappearance_2026_07_25.md`). Regression tests:
      `tests/test_skip_stale_marker_orphan.py::test_skip_orphans_task_fully_absent_from_backlog_yaml` (new) + 2
      pre-existing tests (`test_content_id_migration_wiring.py`,
      `test_release_task_to_queue_guard.py::test_skip_current_task_409s_on_a_stale_pointer_to_a_done_task`) that had
      encoded the old buggy fallthrough as their expectation, updated to match. Full `quality-gates.sh` green (2936
      passed, 2 skipped).
- [x] ✅ [VERIFY] P3. Once both fixes land, reproduce this exact scenario in a non-prod/test harness (dispatch a task,
      delete its plan out from under it, regen backlog, confirm `/done` now returns a clean orphan-closed response
      instead of 500) to close this out with evidence. (repo: agent-orchestrator) — agent-orchestrator@8db0b29 (see
      Progress Log for the new end-to-end test + evidence).

## Progress Log

- **2026-08-09 (slot 33)**: Filed. Root-caused via source read (no server log access from this worker slot) to
  `backlog.get(task_id) is None` not being handled the same way across `/done` (no explicit handling found, 500) vs
  `/skip-current-task` (explicit but inverted-condition handling, still 500) vs `/reassign` (no `backlog.get()`
  dependency at all, worked cleanly). Worked around live via `/reassign` + `DELETE /api/backlog/<id>` — slot freed,
  orphan row gone, task's underlying work (already complete + archived by a prior session) unaffected.
- **2026-08-09 (slot 3)**: Shipped todo 1. `done_slot` now short-circuits a `backlog.get() is None` + non-sentinel-sha
  `/done` to an inline orphan-close (release slot to idle, delete the dead `TaskRow`, log
  `slot_done_orphan_task_closed`, return a clean 200) instead of falling through into the task_def-dependent
  verification pipeline that previously 500'd. Excludes sentinel-sha calls per the todo's own scoping — those still
  complete normally even with no backlog entry (a handful of pre-existing tests relied on that permissive fallthrough
  for unrelated reasons, e.g. sha-gate tests using `Backlog()` as a cheap no-op fixture; verified none of those broke).
  agent-orchestrator@3147392, quality-gates.sh green (2935 passed, 2 skipped). Todos 2 (`skip_current_task`'s inverted
  `task_orphaned` predicate) and 3 (end-to-end verify) are separate backend/verify todos, not touched by this task.
- **2026-08-09 (slot 3, fresh session)**: Shipped todo 2. `skip_current_task`'s `task_orphaned` predicate now treats
  `backlog_task is None` as orphaned (was `backlog_task is not None and not task_still_dispatchable(...)`, which
  evaluated False for a fully-removed backlog entry and fell into the `release_task_to_queue` else-branch that 500'd).
  While implementing, caught a real regression risk two pre-existing tests had baked in as their expectation: a
  `slot.current_task` stale pointer to an already-`done` task is ALSO commonly absent from `backlog.yaml` (regen drops
  finished todos too), and naively treating `backlog_task is None` as orphaned would have made the orphan-delete branch
  unconditionally delete that already-`done` `TaskRow` instead of hitting the existing terminal-status 409 guard in
  `release_task_to_queue` — added an explicit `row_already_terminal` check (status in `("done", "cancelled")`) so
  `task_orphaned` stays False for that case and the 409 guard still fires. agent-orchestrator@4f78629, quality-gates.sh
  green (2936 passed, 2 skipped). Todo 3 (end-to-end non-prod verify) remains open, separate from this todo.
- **2026-08-09 (slot 6)**: Shipped todo 3 — the end-to-end non-prod reproduction. `test_done_orphan_task_closed.py` /
  `test_skip_stale_marker_orphan.py` (from todos 1/2) already cover the fix at the unit level with a hand-substituted
  empty `Backlog()`; this drives the REAL plan-file → `regen()` → `backlog.yaml` pipeline instead: writes a real plan
  file with one open todo, regenerates the backlog from it (a real `regen()`-minted task_id, not a synthetic one),
  inserts a real `SlotRow`+`TaskRow(status="dispatched")` simulating an actual dispatch, archives (deletes) the owning
  plan file exactly as a completed-plan archival would (not merely checkbox-flipped), then regenerates again
  (`prune_stale=True, db_path=None` — a yaml-only prune) to reproduce the documented live-incident precondition
  verbatim: the `TaskRow` survives `status=dispatched` in state.db while `backlog.yaml` has no entry for it at all.
  Confirmed this precondition holds (asserted inline before exercising the fix) — then called the REAL
  `done_slot()`/`skip_current_task()` route functions directly and confirmed both close the orphan cleanly: no
  exception, dead `TaskRow` deleted, slot released to `idle`, `resp.dispatch_reason`/`orphaned_stale_marker` both
  correctly flag the orphan-close path. 2 new tests
  (`tests/test_orphan_task_e2e_regen_reproduction.py::test_done_closes_regen_orphaned_dispatched_task_cleanly` /
  `::test_skip_current_task_closes_regen_orphaned_dispatched_task_cleanly`), both pass; full existing orphan/regen suite
  (31 tests: `test_done_orphan_task_closed.py` + `test_skip_stale_marker_orphan.py` + `test_regen_reconcile.py` + the 2
  new) green alongside them. Full repo `quality-gates.sh` green (2938 passed, 2 skipped). agent-orchestrator@8db0b29.
  **All 3 todos on this issue doc are now done** — archival-eligible (no `locked_by`).
- **2026-08-10 (slot 30, review)**: Live confirmation of the orphan-close path + one gotcha worth recording. Working
  `ao_satellite_ao_dispatch_batch2_finalize-001`, the dispatcher hands the worker the SHORT positional id (`-001`), but
  by the time the worker's plan-flip lands, regen has re-minted the row to a CONTENT-DERIVED id (`-719c86780478`) and
  cancelled/removed the old short-id row — so `/done` with the short id returns a hard 404
  (`task ... not found in backlog`) BEFORE reaching `_resolve_task_def_for_done`'s orphan-close helper (the B1 TaskRow
  lookup at slots_worker.py ~2018 404s first). `/reassign` also refuses (task already terminal/missing). **Fix (working,
  this session): query the live `state.db` `tasks` table for the row whose `plan_ref` matches + `dispatched_to` = your
  slot, take its ACTUAL `task_id`, and `/done` with that — `_maybe_close_orphaned_done_task` then fires, releases the
  slot to idle, deletes the dead row. No need to touch the plan (the checkbox flip already cancelled the derived task).
