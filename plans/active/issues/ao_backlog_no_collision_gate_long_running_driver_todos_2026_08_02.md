---
doc_type: issue
title:
  Backlog regen re-dispatches a checkbox-derived todo repeatedly with zero collision/liveness gate when its own
  done_definition depends on a multi-hour external background driver (8+ wasted re-dispatches on one todo pair)
summary: >-
  `sports_track_k_is_pipeline_check_progress-008`/`-012` (the mid/final IS pipeline-check checkpoints) each require a
  multi-hour local driver process that sequentially launches 21 per-leg VMs -- no single dispatch can complete them
  inline. Since 2026-08-02T19:33Z, at least 8 separate slot dispatches across 7 different slots have picked up these
  same two backlog task ids (or their sibling flip/verify tasks) while the owning drivers (slot-7 PID 283424, slot-16
  PID 921523) were still alive and progressing, each spending a full re-verification cycle (ps aux + report-file check +
  VM liveness check) before releasing via `/skip-current-task` with zero incremental progress. The tracker doc's own
  Progress Log documents this exact pattern being flagged for main 5+ times already, with no fix landing.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, backlog, dispatch-thrash, collision, prerequisites, long-running-driver]
related:
  [
    /plans/archive/issues/sports_track_k_is_pipeline_check_progress_2026_08_02.md,
    /plans/active/issues/backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md,
  ]
created: 2026-08-02
author: unknown
priority: P2
parent_epic: orchestrator_master
source:
  "slot-4, data_engineering -- 9th+ dispatch of sports_track_k_is_pipeline_check_progress-008, re-verified ground truth
  (both drivers still alive at 283424/921523, no report yet), found no dedicated issue doc existed for a pattern flagged
  7+ times in-doc by prior slots (6, 7, 8, 10, 12, 13, 15, 16)"
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
context_scope: [/plans/archive/issues/sports_track_k_is_pipeline_check_progress_2026_08_02.md, /agents/RULES.md, agent-orchestrator/server/regen_backlog_from_plan.py, agent-orchestrator/server/auto_park.py, /plans/active/issues/backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md]
---

# AO backlog regen has no collision/liveness gate for a todo whose completion depends on a multi-hour external driver -- 2026-08-02

## What I found

`plans/active/issues/sports_track_k_is_pipeline_check_progress_2026_08_02.md` tracks 3 dated checkpoints of a
21-leg-per-checkpoint IS pipeline check. Each checkpoint is kicked off by ONE worker launching a local driver process
(`pipeline_e2e_check.py`) that runs for hours, sequentially launching per-leg VMs. Once launched, the checkpoint's own
backlog todo (`-008` for mid, `-012` for final) has NOTHING left for a subsequent dispatch to productively do until the
driver finishes and writes its report -- yet the backlog keeps offering these same todos (and the downstream flip/verify
todos gated on them) to every idle worker every cycle, with no dispatch-time signal that a driver already owns the work.

Directly observed via this session's own live filesystem access to the orchestrator host's
`agent-orchestrator/data/config/backlog.yaml` (this session happens to run on the same host as the orchestrator server
-- `uvicorn server.server:app` PID 1511693, confirmed via `ps aux`):

- `-008` (mid, 2025-12-24) and `-012` (final, 2025-12-18) both carry `prereqs: {completed_tasks: [], prerequisites: []}`
  -- no gate of any kind, despite both being tied to a currently-alive, multi-hour driver process the tracker doc's own
  Progress Log has documented at every prior dispatch.
- The tracker doc's Progress Log records at least 8 releases via `/skip-current-task` against these exact task ids (or
  the sibling flip task `sports_consolidated_native_ao_extract-029` / `-005`, which is transitively gated on the same
  two checkpoints) since the mid driver was launched at 19:33Z: slot-8 (x2, 19:56Z/20:00Z), slot-13 (19:45Z), slot-10
  (~20:27Z), slot-15 (~20:25Z/20:30Z/21:00Z), slot-12 (~20:40Z), slot-6 (20:45Z), slot-4 (~21:15Z/~21:20Z, and this
  dispatch makes a 3rd for slot-4 alone). Every single one independently ran the SAME re-verification sequence (`ps aux`
  for the driver PID, `ls`/`grep` for the report file, `gcloud compute instances list` for the VMs) and found the same
  "still in flight, nothing to do" answer.
- Each of those cycles is a full worker dispatch -- boot, re-read the (very long, ~560-line) tracker doc, run the
  verification commands, write a Progress Log entry, release -- burning real agent-turns and wall-clock for zero
  incremental progress toward the actual goal.

## Why it matters

- This is the exact "wasteful-not-harmful" dispatch-thrash class the codebase already has ONE fix for
  (`backlog_regen_drops_handtuned_prereqs_2026_07_12.md`, the `park` mechanism documented in `RULES.md` § 4) -- but that
  mechanism requires a WORKER to notice the pattern and manually apply a park, which none of the 8+ prior dispatches did
  (each one only left a prose flag in the Progress Log asking "for main" to fix it -- which is itself the Findings
  Closure HARD RULE violation this doc exists to close: a flagged pattern that never became a tracked, actionable todo).
- Unlike the sibling issue `backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md` (where a park WAS applied;
  that doc's own later investigation traced the code and did NOT reproduce a durability bug there, so the two cases
  don't share a mechanism regardless), this case never had a park attempted at all -- the gap here is dispatch-time
  collision detection, not park durability.
- At fleet scale, any multi-hour-driver-shaped todo (a common pattern in this craft -- backfills, VM-launching checks,
  manifest consolidations) will hit the identical thrash. This is not sports/IS-specific.

## Recommended decision

Two options, not mutually exclusive -- deliberately NOT applied by this session as a manual park (see the deadlock risk
below), left for `main`/a `[BACKEND]` dispatch to choose and implement:

(a) **Manual park** (existing mechanism, `RULES.md` § 4): any worker with live host filesystem access to `backlog.yaml`
(this session has it) can set `prereqs.prerequisites` on the specific task id, gated on a manually-created condition
(`POST /api/prerequisites/<name>`). **Deadlock risk**: if the condition is never flipped true -- e.g. the session that
set it up rotates/ends before the driver finishes, which this exact tracker doc has ALREADY documented happening to the
driver processes themselves (`nohup`/`run_in_background`-doesn't-survive-session-end, see that doc's "Final checkpoint
-- driver died" section) -- the checkbox permanently stops being dispatched even once genuinely ready, which is WORSE
than today's wasteful-but-self-correcting status quo (today, every dispatch at least re-verifies and would catch a
freshly-completed driver). Not applied in this session for that reason. (b) **Backend fix (recommended)**:
`regen_backlog_from_plan.py` / the dispatcher auto-detects a likely collision before offering a checkbox-derived todo --
e.g. a self-expiring cooldown: if the last N dispatches of the SAME todo slug (matched by title-prefix/plan_ref, since
task ids rotate on doc edits) all returned `/skip-current-task` with a collision-shaped reason within a short window,
auto-apply a short TIME-BOUNDED deprioritization (e.g. 15-30 min, self-expiring -- not a hard external condition) before
re-offering it. This bounds the waste without the deadlock risk in (a), since the cooldown always expires on its own
even if nobody revisits it.

## Todos

- [ ] [BACKEND] P2. Design + implement a self-expiring dispatch cooldown in `regen_backlog_from_plan.py` / the
      dispatcher: when N (e.g. 3) consecutive dispatches of the same todo (matched by plan_ref + todo text, since ids
      rotate) return `/skip-current-task` with a collision/no-op-shaped reason within a short window, apply an
      automatic, TIME-BOUNDED priority demotion (self-expiring, not a hard `prerequisites` gate -- avoid the deadlock
      risk documented above) before the same todo is offered again. Add a regression test: simulate 3 skip-current-task
      releases for one task id within N minutes, assert the 4th dispatch cycle does not offer it again until the
      cooldown window elapses. (repo: agent-orchestrator)
- [ ] [BACKEND] P3. Consider surfacing the todo's own most-recent Progress-Log-derived status (if the plan_ref doc has
      one) in the task brief returned by `/boot`, so a picking worker's first re-verification pass can start from "as of
      the last dispatch, driver X was alive at elapsed Y" instead of re-deriving it from scratch by reading the full
      tracker doc every time. (repo: agent-orchestrator)

## Progress Log

- 2026-08-02T21:03Z (slot 4, data_engineering): filed while releasing this slot's 3rd dispatch against this exact
  pattern (`sports_track_k_is_pipeline_check_progress-008`, mid checkpoint). Re-verified ground truth first (both
  drivers -- mid PID 283424 at 1:29:34 elapsed, final PID 921523 at 38:46 elapsed -- still alive, no report file for
  either day yet, no orphan/duplicate VMs). Considered a manual park (this session has live filesystem access to
  `agent-orchestrator/data/config/backlog.yaml`, since the orchestrator server runs on this same host) but declined due
  to the deadlock risk documented above. No code shipped this entry -- pure findings-closure doc per `RULES.md` § 4.5,
  converting 7+ prior slots' prose flags into a tracked, actionable pair of todos.

- **na-eligibility-audit 2026-08-03** (ao tranche): KEEP-NA, valid — first marker (no prior; doc filed 2026-08-02). Both
  items touch agent-orchestrator's core dispatcher/`/boot` machinery with real unresolved design details (the matching
  heuristic, state-storage choice, free-form Progress-Log-parsing approach) rather than fully-specified, mechanically
  bounded tasks. Checked for prior art: `server/auto_park.py` implements a related but materially different mechanism
  (durable auto-park via the hard-gate `prereqs.prerequisites` primitive this doc's own risk analysis explicitly steers
  away from) — so item 1 requires a genuine build-vs-extend judgment call, not a mechanical follow of established
  precedent.

- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries) — added the actual source-code target
  (`regen_backlog_from_plan.py`, the file todo 1 modifies), the prior-art mechanism (`auto_park.py`, already cross-
  referenced by the na-eligibility-audit note above), and the sibling park-durability issue doc alongside the
  existing 2.
- **context-scout 2026-08-03 (re-pass)**: re-verified under the updated methodology, unchanged (5 entries) — all still
  resolve and remain the right minimal set for both open todos.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (5 entries) -- still the right minimal set for both
  open todos (dispatch cooldown design in `regen_backlog_from_plan.py`; surface Progress-Log status at `/boot`).
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — Prior verdict re-verified — content unchanged since the
  2026-08-06 marker. Both open items remain genuine build-vs-extend design calls per the 2026-08-03 marker's analysis
  (matching heuristic, state-storage choice, free-form Progress-Log-parsing approach).
- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — checked against the round7-10 precedent set; none
  apply (this is a dispatcher-internals design fork, not a credential/plan-destination/delete-safety question).
  Corroborated same-day: `/ag-closeout-audit ao` batch12 independently lists this doc under operator-gated (22).
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — content unchanged since
  round11. Both open items remain genuine build-vs-extend dispatcher-design forks (matching heuristic, state-storage
  choice) per the 2026-08-03 marker's original analysis, still not mechanically specified.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-21 (ao tranche)**: KEEP-NA, valid — reaffirmed, content unchanged since the
  2026-08-10 marker. Both open items remain genuine build-vs-extend dispatcher-design forks (self-expiring cooldown
  matching heuristic, state-storage choice) per the 2026-08-03 marker's original analysis — 7 prior audit rounds
  agree. Doc stays `assigned_vm: NA`.
