---
doc_type: issue
title:
  "cicd escalation worker's own mandated STEP-0 heartbeat auto-dispatches an unrelated backlog task onto the slot before
  any real work starts, and the escalation's one_shot AgentRow is gone by /done time — one_shot_complete 400s 'no active
  agent owns its session', a distinct trigger from the already-fixed
  /plans/archive/issues/ag_closeout_auditor_one_shot_complete_no_agentrow_2026_07_26.md"
summary: >-
  Reproduced live on slot 3, 2026-07-28, running escalation agt-5c9281 (repo=unified-trading-pm, wall_type=plan_health).
  Followed cicd.md's boot sequence exactly: STEP 0 `POST /api/slots/3/heartbeat` (mandatory liveness ping, before
  reading any role file) returned a full backlog-dispatch payload — `new_task` = an UNRELATED queued task
  (`capability_wizard_gap_discovery-013`) plus several `messages` addressed to a completely different escalation
  (`agt-52bb99`'s BLOCKED-question thread). The escalation's actual assignment (fix the plan_health wall) was correctly
  taken from the boot message's session variables per cicd.md's own STEP 2 ("no separate task-fetch call for this
  one-shot role") — the injected `new_task` was never acted on. The real wall was fixed and verified (clean
  `run_hygiene_sweep.sh --ci`, 0 hard failures) and pushed `unified-trading-pm@95217d1db` to `live-defi-rollout`. But
  `POST /api/slots/3/done {"task_id": "", "sha": "", "evidence": "", "one_shot_complete": true}` — the exact contract
  cicd.md's own STEP 3 documents — 400d: `"one_shot_complete on slot 3 but no active agent owns its session
  'orch-slot-3' — a Class-A worker must /done with a task_id."`. `GET /api/agents` confirms zero active/stale AgentRow
  rows for `agt-5c9281` or `tmux_session=orch-slot-3` at all — only the singleton `main` row is present.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, slot-lifecycle, one-shot, cicd, escalation, heartbeat, self-heal]
related:
  [
    /plans/archive/issues/ag_closeout_auditor_one_shot_complete_no_agentrow_2026_07_26.md,
    /plans/archive/issues/slot_stale_spawn_base_role_stuck_task_less_2026_07_25.md,
    /plans/archive/issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md,
  ]
created: 2026-07-28
parent_epic: agent_operating_framework_master
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend-engineer
source: "slot 3, cicd escalation agt-5c9281 (wall_type=plan_health, repo=unified-trading-pm), 2026-07-28"
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: agent-orchestrator@babba14
drift_direction: advance-code
---

## What I found

This is the SAME terminal symptom as
`/plans/archive/issues/ag_closeout_auditor_one_shot_complete_no_agentrow_2026_07_26.md` (`one_shot_complete` rejects
with "no active agent owns its session") but a **distinct trigger**, not yet covered by that doc's shipped fix
(`agent-orchestrator@a01aeae`, `boot_slot()`'s lazy-`AgentRow` construction gated on
`req.slot_role in PLAN_HEALTH_FAMILY_ROLES = {plan_health, plan_reconciler, docs_reconciler, ag_closeout_auditor, na_eligibility_auditor}`).
`cicd` is not in that set, and — unlike the precedent doc's case — this session was NOT booted directly via
`/api/slots/{N}/boot` bypassing a dispatch endpoint. It was spawned the documented way, through `POST /api/escalate` →
`server/escalation.py`'s `dispatch()`, which (verified by reading the code this session, `escalation.py:514-536`) DOES
call
`_register_agent(..., agent_id=escalation_id, agent_kind="cicd", lifecycle="one_shot", tmux_session=tmux_session_name, ...)`
at spawn time, before the worker ever gets control — so the `AgentRow` this doc's symptom is missing should have existed
from the very first moment of this session.

**Working hypothesis (unconfirmed against the live activity log this session — flagging rather than digging further, out
of this one-shot task's scope):** `cicd.md`'s own STEP 0 requires a liveness heartbeat (`POST /api/slots/{N}/heartbeat`)
as the FIRST action, before reading any role file or doing any real work. But `escalation.py`'s spawn path (unlike a
normal backlog dispatch via `assign_task_to_slot`) never sets `slot.current_task` — only the `AgentRow` carries the
escalation identity; the `SlotRow` itself is claimed via `claim_slot_for_typed_agent` (`escalation.py:543-551`), which
sets a descriptor + `spawn_base_role`, not `current_task`. `heartbeat_slot()` (`server/routes/slots_worker.py:473`)
branches on `slot.status == "paused" or slot.current_task is not None` to decide "already working, just refresh" vs.
"idle, try to dispatch something" (line 598: `pick_next_task(...)`). Since `current_task` was `None` for this escalation
slot, MY very first heartbeat call took the idle branch and dispatched a brand-new, wholly unrelated backlog task
(`capability_wizard_gap_discovery-013`) via `assign_task_to_slot`, which sets `slot.current_task`,
`slot.status = "working"`, **and `slot.spawn_base_role = None`** (`server/state_store/slots.py:103` — explicitly
clearing any prior typed-agent occupant's role marker). Whether THIS is what caused `find_active_agent_for_session`
(`AgentRow.status.in_(("active","stale"))` lookup by `tmux_session`) to stop finding my `AgentRow` — vs. some separate
reaper pass (`reap_orphan_agents`, `server/state_store/agents.py:372`) independently deciding the row was orphaned once
the slot's `current_task`/`spawn_base_role` no longer matched a typed-agent shape — was NOT traced to a specific line
this session; both are plausible and not mutually exclusive. What IS confirmed directly: (1) the `AgentRow` existed at
spawn per the code path read, (2) the very first heartbeat's response body proves the idle-dispatch branch fired and
bound an unrelated task to the slot, (3) by `/done` time, zero AgentRow rows exist for this agent/session anywhere.

## Why it matters

Every `cicd`/`conflict_resolver`/`data_pipeline_failure`-style escalation (the same `escalation.py` dispatch path, per
`_AGENT_KIND_BY_PROMPT_TEMPLATE`) has its own role file mandate a heartbeat as the very first action (liveness proof
before reading role rules) — and per this reproduction, that mandatory first call is itself what appears to knock the
slot out of "typed one-shot occupant" shape and into "normal Class-A worker mid-task" shape, before the worker has done
anything wrong. The worker then does its REAL job correctly (this session: wall fixed, verified, pushed clean) and is
contractually required to self-terminate via `one_shot_complete` — which is now permanently rejected, for reasons
entirely outside the worker's control or knowledge at call time. Same accounting-gap consequence the precedent doc
named: real, verified, shipped work has no way to register as "done" on the dashboard, and the tmux session either hangs
forever (re-nudged) or needs an operator to notice and manually reap it. Unlike the precedent's "manual/dev invocation
only, no production timer exposure" resolution, **this trigger IS the documented, standard production path**
(`POST /api/escalate` from GHA, per `cicd.md`'s own header) — every future `cicd`-family escalation that follows its own
boot contract verbatim is exposed, not just a dev/manual edge case.

## Recommended decision

- [x] ✅ [BACKEND] P2. **DONE 2026-07-28.** Confirmed via regression test (not activity-log trace) —
      `test_heartbeat_on_freshly_claimed_typed_slot_steals_it_into_normal_dispatch` reproduces the exact live mechanism:
      `heartbeat_slot`'s idle-vs-working branch has no `spawn_base_role`/`AgentRow`-lifecycle awareness (unlike
      `boot_slot`), so the escalation's mandated STEP-0 heartbeat on a freshly `claim_slot_for_typed_agent`'d slot
      (`current_task=None` by design) takes the idle branch and `assign_task_to_slot` overwrites `current_task` + wipes
      `spawn_base_role`. A second test, `test_heartbeat_steals_typed_slot_but_agentrow_lookup_still_succeeds`, directly
      answers the open question: the slot-field clobbering ALONE does NOT explain the live `/done` 400 —
      `find_active_agent_for_session` / `reap_orphan_agents` key only off `AgentRow.tmux_session`/`status`/`last_ping`,
      never `SlotRow.current_task`/`spawn_base_role`, so the AgentRow still resolves immediately after the steal. The
      slot-clobbering bug is real and confirmed but not sufficient by itself — a separate, still-open mechanism explains
      the AgentRow going missing by `/done` time (out of this task's scope; todo below still needs the fix for the
      confirmed clobbering bug). — agent-orchestrator@d59f1af.
- [x] ✅ [BACKEND] P2. **DONE 2026-07-28.** Shipped option (b): extracted `boot_slot()`'s existing typed-role liveness
      check (with its session-reused staleness self-heal) into a shared `_typed_occupant_liveness` helper and run it in
      `heartbeat_slot()` before the idle-dispatch fallthrough, mirroring `boot_slot()`'s own gate — so a freshly
      `claim_slot_for_typed_agent`'d slot's mandated STEP-0 heartbeat no longer falls through to `pick_next_task` and
      steals the slot into normal Class-A dispatch shape. — agent-orchestrator@babba14.
- [x] ✅ [BACKEND] P3. **DONE 2026-07-28 (same session that filed this doc).** `capability_wizard_gap_discovery-013` was
      confirmed still `status: dispatched, dispatched_to: 3` in the live backlog (never touched — this session's real
      work was the plan_health wall, not this task) — released via
      `POST /api/slots/3/skip-current-task     {"reason_code": "OTHER"}` (slot-scoped skip, no fleet cooldown/auto-park
      since this was never evidence the task itself is blocked). Confirmed response: `task_skipped`,
      `tmux_session_kept_alive: true`, task back to `queued` for any other slot. Did NOT require todo 1/2 (the actual
      mechanism fix) to land first — independent cleanup. Repo: agent-orchestrator.

## Current session status (informational, not part of the fix)

This escalation's assigned mandate (clear the `unified-trading-pm` `plan_health` wall) is fully complete:
`assigned_vm:NA` corpus ratchet root-caused (2 misclassified/genuinely-new NA docs identified, one reclassified
`NA→planning`, the reviewed remainder's baseline updated 397/1421→398/1424 per the ratchet's own sanctioned exception
path), `run_hygiene_sweep.sh --ci` re-verified clean twice (before and after a live rebase) — 0 hard failures, 1
pre-existing unrelated soft warning. Pushed `unified-trading-pm@95217d1db` to `live-defi-rollout`,
`git rev-list --count HEAD ^origin/live-defi-rollout` = 0 (fully pushed, working tree clean, branch
`live-defi-rollout`). No open `repo-blockers` needed fast-pathing. Messaged `main`
(`POST /api/agents/by-role/main/message`) with this same summary

- a note that slot 3 is safe to reclaim/reap. Unable to formally signal `/done` due to the gap above; ending this turn
  with this issue doc instead of polling a broken endpoint, per the workspace's own async-wait-discipline rule against
  retrying a call whose root cause is already understood.
