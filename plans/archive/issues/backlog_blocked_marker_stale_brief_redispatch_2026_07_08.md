---
doc_type: issue
title:
  BLOCKED-* in-text marker doesn't stop re-dispatch — stale `brief` reconcile-miss + 30-min prune tick lets a skipped
  task loop back within minutes
summary: |
  Filed 2026-07-08 after `footystats_matches_predictions_fetch_gaps-004` was dispatched at least 5 times
  (slot-12, slot-8, slot-4, slot-11, all in the ~20 minutes between 22:01 and 22:13 UTC) despite an in-text
  `BLOCKED-PREREQUISITES` marker slot-8 added to the todo at ~21:58 UTC specifically to stop this. Root-caused
  by slot-11 (this filing) by reading `server/regen_backlog_from_plan.py` + `server/dispatch.py`: the marker
  DOES work at ingestion time (`_NON_DISPATCHABLE_RE`, regen_backlog_from_plan.py:749), but the reconcile pass
  that would otherwise update an EXISTING queued task in place keys the match on an EXACT string match of the
  todo's current parsed `description` against the task's stored `brief`
  (`plan_tasks_by_brief = {t.brief: t ...}`, regen_backlog_from_plan.py ~line 1020; lookup
  `plan_tasks_by_brief.get(description)` ~line 1054). Once the marker text is ADDED to the todo, the new
  `description` string no longer matches the OLD stored `brief` — so the reconcile branch silently misses (the
  task row is left with its stale, pre-marker `brief`), and because the now-non-dispatchable todo is filtered
  out of `_parse_open_todos`'s returned `todos` list entirely, nothing else touches that row either. The row is
  only removed by the SEPARATE `prune_stale=True` orphan-prune, which only runs on the 1800s
  `PlanRegenLoop` tick (`plan_regen_interval_seconds`, server/config.py:554-556) and only touches rows that are
  `status='queued' AND dispatched_to IS NULL` at that instant. `pick_next_task`
  (server/dispatch.py:80-127) has no knowledge of the marker at all — it reads `TaskRow`/`BacklogTask` state,
  never the live plan text, so as long as the stale row exists as `queued`, it is a normal dispatch candidate.
  Net effect: every time a slot boots/heartbeats and picks up the stale row, works it for ~2-10 min, discovers
  the in-doc marker, and calls `/skip-current-task` (row → `queued`, `dispatched_to=NULL`), the row is
  IMMEDIATELY re-offered to the next slot's boot/heartbeat (dispatch runs continuously; the orphan-prune runs
  at most once per 30 min) — a live race the marker was specifically introduced to prevent, that it does not
  actually prevent. Confirmed independently by 4 slots on the same task instance in one evening.
status: resolved
nature: notes
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [dispatch, backlog-regen, orphan-prune, race-condition, blocked-marker, worker-lifecycle]
related:
  [
    /plans/active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md,
    /plans/archive/issues/craft_scoped_slot7_ui_dispatch_mismatch_2026_07_08.md,
  ]
created: 2026-07-08
last_updated: 2026-07-08
parent_epic: agent_operating_framework_master
priority: P2
source:
  footystats_matches_predictions_fetch_gaps-004 (slot-11, re-surfacing slot-4's + slot-8's + slot-12's identical skips)
assigned_vm: planning
resolved_by: agent-orchestrator@3995384
locked_by:
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: advance-code
locked_since:
depends_on:
supersedes:
superseded_by:
---

## What I found

`footystats_matches_predictions_fetch_gaps-004`'s todo text already carries the taxonomy's own `BLOCKED-PREREQUISITES`
marker (added by slot-8 at ~21:58 UTC 2026-07-08, matching `_NON_DISPATCHABLE_RE = r"BLOCKED-[A-Z]|..."` in
`regen_backlog_from_plan.py:749`), which the doc comments say exists precisely so "a future `PlanRegenLoop` prune tick
will stop re-offering it." In practice the task was still dispatched to slot-12 (22:01:32), slot-8 (22:03:44 — a SECOND
time, after already closing todo #1 earlier), slot-4 (22:05:54), and slot-11/this session (22:13:49) — 4 dispatches in
12 minutes, each ending in an immediate `/skip-current-task` once the worker read the plan and found the marker. See the
Root cause in the summary above (exact-string `brief` reconcile-miss + 1800s prune-tick cadence << dispatch cadence).
Confirmed by reading `server/dispatch.py` `pick_next_task` (no live-plan-text awareness, only DB row state) and
`server/regen_backlog_from_plan.py` (`_NON_DISPATCHABLE_RE`, `_parse_open_todos`, the `plan_tasks_by_brief` reconcile
keying, and `plan_regen_interval_seconds` default 1800 in `server/config.py:554`).

## Why it matters

- Direct cost: every dispatch burns a slot's boot → fresh-pull → read-plan → discover-marker → skip cycle (observed
  ~2-10 min each) for zero forward progress — 4+ wasted cycles on this one task in one evening, and the pattern will
  recur on ANY future todo that gets a BLOCKED-\* marker added post-hoc while already `queued` (not just this footystats
  task).
- The taxonomy comment in the code (`regen_backlog_from_plan.py:812-819`) explicitly documents the prune-based
  auto-clear as the mechanism that's supposed to make this safe — it is not reliable under the fleet's actual dispatch
  cadence (near-continuous vs. 30-min prune), so the documented guarantee is false today.
- `footystats_matches_predictions_fetch_gaps_2026_07_08.md`'s own Progress Log (slot-8, 2026-07-08) already predicted
  this exact failure mode ("if this task gets dispatched a THIRD time... that's a P2 dispatcher/regen-prune-cadence
  issue worth its own issue doc") — this doc is that filing, now with the precise code-level root cause instead of just
  the symptom.

## Recommended decision

A backend-engineer-craft worker (agent-orchestrator repo, Python service code) should pick ONE of these
(smallest-blast-radius first):

1. **(Preferred, smallest change)** In `skip_current_task` (`server/routes/slots_ops.py:586-645`), after recording the
   skip, re-parse ONLY this task's own plan file (`server/regen_backlog_from_plan.py`'s `_parse_open_todos`, single
   small file read — not a corpus walk) and check whether the CURRENT todo text for this task's `plan_order` position
   now matches `_NON_DISPATCHABLE_RE` or has disappeared entirely. If so, delete/orphan the `TaskRow` immediately
   instead of leaving it `queued` — this closes the race at the exact moment it's created, independent of the 1800s
   tick.
2. Lower `plan_regen_interval_seconds` (server/config.py:554, default 1800) substantially (e.g. 120-300s) as a blunter
   mitigation — reduces the race window but does not eliminate it, and adds regen load fleet-wide.
3. Fix the reconcile match in `regen()` (regen_backlog_from_plan.py ~line 1020-1075) to key on `(plan_ref, plan_order)`
   instead of exact `brief` string equality, so an in-place text edit (like adding a BLOCKED-\* marker) updates the
   EXISTING row's `brief` in place on the very next regen tick — then a cheap `_NON_DISPATCHABLE_RE` check added to
   `pick_next_task` (dispatch.py, alongside the existing `_DEFERRED_PREFIXES` check at line 98-104) would catch it
   immediately without any file re-read at dispatch time. Larger change (touches the general reconcile-matching
   semantics), but fixes the deeper issue behind this symptom too.

- [x] ✅ [BACKEND] P2. Implement option 1 (skip-time re-check) or option 3 (reconcile-by-position + dispatch-time marker
      check) from the Recommended decision above so a `BLOCKED-*`-marked todo stops being re-offered within the SAME
      dispatch cycle it's skipped in, not up to 30 minutes later (repo: agent-orchestrator). Add a regression test: task
      marked `BLOCKED-*` post-hoc while `dispatched` → skip → assert `pick_next_task` does NOT return it on the very
      next call (no sleep/tick wait). — agent-orchestrator@3995384

## Progress Log

- **2026-07-08** — Filed by slot-11 (data_engineering craft) after `footystats_matches_predictions_fetch_gaps-004` was
  dispatched to it as (at least) the 5th slot in ~20 minutes despite the BLOCKED-PREREQUISITES marker. Root-caused via
  direct code read (not guessed) — see summary. Not fixing in this session: the fix is Python backend/dispatcher logic
  in agent-orchestrator, out of this slot's data_engineering craft scope (per RULES.md — craft-scoped slots escalate
  mis-scoped work rather than cross craft lines). Releasing `footystats_matches_predictions_fetch_gaps-004` back to the
  queue via `/skip-current-task`.
- **2026-07-08** — Implemented option 1 (skip-time re-check) by slot-2 (backend-engineer craft):
  `task_still_dispatchable()` added to `regen_backlog_from_plan.py` (re-reads only the one task's own plan file, no
  corpus walk) and wired into `skip_current_task()` (`server/routes/slots_ops.py`) — when the todo is no longer
  dispatchable (BLOCKED-\*/stretch marker added, checked off, or removed) the `TaskRow` is deleted immediately instead
  of being requeued, closing the race independent of the 1800s prune tick. Regression tests added
  (`tests/test_skip_stale_marker_orphan.py`): unit coverage for `task_still_dispatchable` (unchanged / marker-added /
  checked-off / missing-file / issues-subdir) plus an end-to-end test asserting a stale-marker task is orphaned on skip
  and `pick_next_task` never hands it back out. Full `quality-gates.sh` green; shipped via
  `quickmerge agent-orchestrator@3995384`.
