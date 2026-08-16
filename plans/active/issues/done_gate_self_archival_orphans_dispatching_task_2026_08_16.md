---
doc_type: issue
title: /done M3 gate keeps rejecting a genuinely-complete task after its own archival commit self-cancels the TaskRow
summary: >-
  Completing a plan/issue doc's LAST open todo via a same-commit checkbox-flip + `git mv` archival (the mandatory
  6-step archival ritual) causes the backlog regen loop to mark the dispatching TaskRow `status=cancelled` while the
  worker is still mid-session, BEFORE the worker's own `/done` call. `/done`'s M3 gate then keeps rejecting with
  `cross_repo_pm_file_touched_no_checkbox_flip` (checked 3x, ~1min apart) instead of detecting the already-cancelled
  status and short-circuiting cleanly. The existing `reconcile_done_gate_rejections.py` recovery tool does not cover
  this case either — it only scans `status="dispatched"` rows, not `status="cancelled"` ones — so a worker whose real
  work is genuinely complete and verifiably on origin has no automated recovery path and must fall back to
  `/skip-current-task`.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, done-gate, m3-verify, plan-archival, self-cancel, backlog-regen]
related: [/plans/active/ao_consolidated_closeout_2026_08_12.md]
priority: P2
created: 2026-08-16
author: slot-30 (data_engineering)
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by:
resolved_by:
source: [agent-orchestrator/server/routes/slots_worker.py, agent-orchestrator/server/verify.py, agent-orchestrator/scripts/orchestrator/reconcile_done_gate_rejections.py]
depends_on: []
---

# /done M3 gate vs. self-archival-cancelled TaskRow (2026-08-16)

## What I found

Working `utl_shared_clone_commits_repeatedly_reset-2a5bc33031bd` (todo 9 of
`plans/active/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md`), I shipped the actual code work
(`unified-trading-pm@aff23df235`), then flipped the todo's checkbox. That was the doc's LAST open todo, so per the
`plan-completion-and-archival-discipline.md` HARD RULE I archived it in the same commit (single-repo mode-1 sanctioned
shape): `git mv plans/active/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md
plans/archive/2026_08/issues/...`, shipped as `unified-trading-pm@5c725d68da`, verified on origin (no create-only
duplicate, clean rename).

Calling `/done` with that sha then failed 3 times (03:55:40Z, 03:56:27Z, 03:58:36Z — `activity_log` confirms), every
time with the identical rejection:

```
{"detail":{"msg":"commit '5c725d68da' does not touch the plan checkbox at
'plans/active/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md' — flip the checkbox...",
"reason":"cross_repo_pm_file_touched_no_checkbox_flip","sha":"5c725d68da"}}
```

Direct DB inspection (`agent-orchestrator/data/state/state.db`, `tasks` table) revealed the actual state:

```
{'task_id': 'utl_shared_clone_commits_repeatedly_reset-2a5bc33031bd', 'status': 'cancelled',
 'dispatched_to': 30, 'done_sha': None, 'done_at': None, ...}
```

The `activity_log` shows `task_dispatched` at 03:23:55Z, then three `slot_done_rejected_no_plan_flip` events — no
`task_cancelled`-shaped event in between was visible in the window I queried, but the TaskRow's `status` had already
flipped to `cancelled` by the time of my first `/done` call. The most likely mechanism: the backlog regen loop
(`regen_backlog_from_plan.py` / `PlanRegenLoop`) re-scanned `plans/active/**` after my archival commit landed, found
todo 9's `- [ ]` line no longer present anywhere under `plans/active/` (correctly — it's `- [x]` now, inside
`plans/archive/2026_08/issues/...`), and marked the still-dispatched TaskRow `cancelled` — a live race between "the
worker's own completion archives the source doc" and "the regen loop reacts to the doc moving," landing entirely
within the same worker session, before `/done` was ever called.

## Why it matters

Two gaps compound here, both worth fixing:

1. **`/done`'s M3 verification path (`slots_worker.py`'s `done_slot` → `verify.check_plan_flip`) does not check
   `TaskRow.status` before running the checkbox-flip verification.** A task that is already `cancelled` should almost
   certainly short-circuit (either accept the already-verified-complete work cleanly, mirroring
   `_maybe_close_orphaned_done_task`'s pattern, or explicitly tell the worker to `/skip-current-task` instead of
   silently re-running M3 checks that were never going to resolve differently on retry).
2. **`reconcile_done_gate_rejections.py`'s own scope (`status="dispatched"` only) misses this exact case.** Its
   docstring explicitly anticipates the sibling failure mode ("its plan was archived + regenerated out from under
   it... the live `/done` route's own orphan-closure path resolves it on the task's next `/done` call") and says
   that's "a DIFFERENT, already-handled failure class" — but `_maybe_close_orphaned_done_task` only fires when
   `task_def is None` (the task_id is absent from `backlog.yaml`/the in-memory `Backlog` entirely), not when the
   TaskRow's own `status` column already reads `cancelled` while `task_def` still resolves (a regen-timing gap: the
   TaskRow status flipped before the NEXT `PlanRegenLoop` tick actually dropped the backlog.yaml entry). So neither
   the live M3 gate nor the standing recovery script closes this specific timing window — a worker whose work is
   genuinely done and verifiably on origin gets stuck retrying a rejection that can never succeed, with no
   documented signal telling them to stop retrying and no automated cleanup path.

This is the EXACT shape the archival-ritual authors already worried about
(`ao_done_gate_checkbox_flip_blind_to_self_archived_plan_ref_2026_07_26.md`,
`plan_ref_self_archived_with_marker` resolution in `verify._archival_rename_disposition`) but that resolution tier
apparently still didn't fire for this task — worth a live repro to confirm whether `_archival_rename_disposition`
itself has a bug for this exact commit shape, or whether the `status=cancelled` short-circuit gap above is the sole
cause (my working hypothesis, not confirmed with a debugger — I stopped once I found the DB-level cancellation,
since that alone fully explains "3 retries, always resolves identically" regardless of what `_archival_rename_disposition`
would otherwise return).

## What I did instead

Confirmed the actual work is correct and complete on origin (`unified-trading-pm@aff23df235` — STAGE-5 guard bats
coverage; `unified-trading-pm@5c725d68da` — checkbox flip + archival, verified clean rename via `git show`). Since
the TaskRow is genuinely `cancelled` (not a false read — confirmed via direct SQLite query, not just the API
response), followed `worker.md`'s documented handling for a cancelled-mid-session task: did not force another
`/done` retry, called `/skip-current-task` with an accurate reason instead.

## Todos

- [x] [BACKEND] P2. Add a `TaskRow.status == "cancelled"` (and/or `"idle"`, any non-`dispatched` terminal state) check
      early in `done_slot` (`agent-orchestrator/server/routes/slots_worker.py`), before the task_def-dependent M3
      verification pipeline runs — either accept a cancelled-but-verifiably-shipped `/done` call cleanly (mirroring
      `_maybe_close_orphaned_done_task`'s release-slot + log-and-return pattern) or return a distinct, actionable
      reason (e.g. `task_cancelled_mid_session`) instead of repeating `cross_repo_pm_file_touched_no_checkbox_flip`
      on every retry. Repo: agent-orchestrator. — ✅ agent-orchestrator@a9b04f85c0 (new
      `_maybe_close_non_dispatched_task` helper, folded into `_resolve_task_def_for_done` alongside the existing
      orphan-task check so `done_slot`'s own cyclomatic complexity is unchanged; short-circuits for ANY
      `TaskRow.status != "dispatched"` reached there, returns `dispatch_reason="task_<status>_mid_session"`, and
      leaves the row intact for todo 2's widened `reconcile_done_gate_rejections.py` scan. 5 new/updated regression
      tests, full local QG green: 3985 pytest + dashboard tsc/vitest.)
- [x] [BACKEND] P2. Extend `reconcile_done_gate_rejections.py`'s candidate scan to also cover `status="cancelled"`
      rows with an unresolved `slot_done_rejected_no_plan_flip` event and a verifiably-on-origin cited sha — same
      verification/flip logic, just widen the `WHERE status = ...` scope past the current `"dispatched"`-only filter.
      Repo: agent-orchestrator. — ✅ agent-orchestrator@d75732a1f9
- [ ] [BACKEND] P3. Live-repro `verify._archival_rename_disposition` against this exact commit shape (same-commit
      checkbox flip + `git mv`, single-repo mode-1) in an isolated scratch repo to confirm whether it resolves
      correctly on its own once the `status=cancelled` short-circuit gap above is fixed, or whether it has a
      SEPARATE bug for this case — this issue's own investigation stopped at the DB-level cancellation finding and
      didn't need to determine which. Repo: agent-orchestrator.

## Progress Log

- 2026-08-16 (slot-30, data_engineering) — filed from a live `/done` rejection loop hit while completing
  `utl_shared_clone_commits_repeatedly_reset-2a5bc33031bd`. See "What I found" above for the full evidence chain.
- 2026-08-16 (slot-3, backend_engineer) — todo 2 shipped (`agent-orchestrator@d75732a1f9`): widened
  `find_candidates()`'s `WHERE status = ...` to `("dispatched", "cancelled")`, added a `task_status` field on
  `Candidate` for report visibility, and updated the module/function docstrings to match. Also fixed a real
  correctness gap this widening would otherwise have introduced: `_mark_done()`'s unconditional
  `clear_slot_assignment(candidate.slot_id)` call is safe for the existing `dispatched` population (the slot is
  presumably still stuck retrying the same task) but NOT for `cancelled` rows — a cancelled task's `dispatched_to`
  slot has very likely already moved to different live work by the time this script runs (the ORM's own
  `SlotRow.current_task` comment says it's "cleared on done/cancel"), so blindly clearing it could rip a live,
  unrelated task assignment out from under the slot. Guarded it to only clear when `slot.current_task ==
  candidate.task_id` still holds. Added 3 new tests (cancelled candidate discovery + the two clear/no-clear slot
  guard cases) plus the pre-existing suite; full `quality-gates.sh --no-fix` green (3981 passed, 2 skipped).
