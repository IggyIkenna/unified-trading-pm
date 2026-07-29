---
doc_type: issue
title:
  "one_shot_complete still rejects with 'no active agent owns its session' for a directly-/boot-spawned
  ag_closeout_auditor session even after passing slot_role — a recurrence of, or an uncovered edge case in,
  /plans/archive/issues/ag_closeout_auditor_one_shot_complete_no_agentrow_2026_07_26.md's fix
  (agent-orchestrator@a01aeae)"
summary: >-
  Reproduced live on slot 7, 2026-07-29, running a scheduled ag_closeout_auditor dispatch (tranche=ci). Session was
  spawned per the standard AGENT BOOT sequence handed in the boot prompt (heartbeat -> read RULES.md/
  ag_closeout_auditor.md -> POST /api/slots/7/boot) — the boot prompt's own JSON did NOT include a `slot_role` field.
  After completing the full audit (Phase 0-3, drafted ci_satellite_ao_dispatch_batch2_2026_07_29.md + its finalize + a
  script-bug issue doc, shipped unified-trading-pm@b8a45042f) and calling `POST /api/slots/7/done {"task_id": "", "sha":
  "", "evidence": "...", "one_shot_complete": true}` per the role file's documented STEP 2 contract, the call was
  rejected with the SAME error message the 2026-07-26 doc already reported and marked resolved: `{"detail":
  "one_shot_complete on slot 7 but no active agent owns its session 'orch-slot-7' — a Class-A worker must /done with a
  task_id."}`. Every `/boot`/`/heartbeat` call in this session offered an UNRELATED generic Class-A backlog task (first
  `mtds_available_at_cross_asset_backfill-006`, then after `/skip-current-task` + re-`/boot`,
  `sports_stats_delayed_live_capture_still_dead_post_fix-004`) — i.e. `already_in_progress` kept flipping true/false
  exactly like the 2026-07-26 reproduction, and clearing it via `/skip-current-task` + re-`/boot` again did NOT resolve
  the underlying rejection, also matching that doc's finding that the symptom and the root cause are different things.
  **What's NEW this time**: the 2026-07-26 doc's shipped fix (`agent-orchestrator@a01aeae`) added lazy `AgentRow`
  construction on direct `/boot` of a `plan_health`-family role, gated on "slot_role matching a known plan_health-family
  role AND spawn_base_role isn't already a typed role." This session's FIRST `/boot` call never passed `slot_role` at
  all (the boot prompt template that spawned this session doesn't include it in the payload it hands the agent) —
  plausibly why the lazy-create guard's first condition never matched. Re-`/boot`ing with `"slot_role":
  "ag_closeout_auditor"` added explicitly did NOT change the outcome (`already_in_progress` still true, `/done` still
  rejected identically) — consistent with the guard's SECOND condition ("spawn_base_role isn't already a typed role")
  already being false by the time the explicit `slot_role` was supplied, i.e. some earlier dispatch (before this agent's
  first `/boot` call, or the missing-`slot_role` first `/boot` itself) had already stamped a typed `spawn_base_role`
  (evidenced by the Class-A tasks offered carrying `assigned_role: "data_engineering"` then `"infra"` — neither is
  `ag_closeout_auditor`) that the fix's guard then correctly refuses to clobber.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, slot-lifecycle, one-shot, ag_closeout_auditor, plan_health, self-heal, recurrence]
related:
  [
    /plans/archive/issues/ag_closeout_auditor_one_shot_complete_no_agentrow_2026_07_26.md,
    /plans/archive/issues/slot_stale_spawn_base_role_stuck_task_less_2026_07_25.md,
    /plans/active/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
  ]
created: "2026-07-29"
last_updated: "2026-07-29"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
assigned_role: backend_engineer
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
locked_by:
resolved_by:
  "agent-orchestrator@bb13e93 (release stray Class-A task on plan_health-family boot correction + skip pick_next_task
  entirely for plan_health-family slot_roles) + 2 regression tests in test_boot_typed_role_gate.py — both P2 todos DONE
  2026-07-29 (slot-15)"
depends_on: []
source: >-
  slot 7, ag_closeout_auditor (tranche=ci), 2026-07-29, discovered while completing the daily ci audit — the exact same
  failure class as /plans/archive/issues/ag_closeout_auditor_one_shot_complete_no_agentrow_2026_07_26.md, whose fix
  (agent-orchestrator@a01aeae) did not close this instance.
---

> **🟢 ARCHIVED 2026-07-29** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule.

# `one_shot_complete` recurrence — `spawn_base_role` was already typed before this session's own `/boot` ever ran

## What I found

Same error, same role family, three days after the prior doc's fix shipped and was archived `status: resolved`:

```
{"detail":"one_shot_complete on slot 7 but no active agent owns its session 'orch-slot-7' — a Class-A worker must /done with a task_id."}
```

Sequence this session:

1. `POST /api/slots/7/boot` with the boot prompt's exact JSON (account_id/branch/dispatch_id/effort/model/operator/
   pm_repo_path/server_url/slot_id/thinking/tranche/worktree/read_files — **no `slot_role` key at all**, since the
   dispatch prompt template handed to this agent never included one). Response: `already_in_progress: false`, offered an
   unrelated Class-A task (`mtds_available_at_cross_asset_backfill-006`, `assigned_role: "data_engineering"`).
2. Completed the full ci-tranche audit, shipped `unified-trading-pm@b8a45042f`.
3. `POST /api/slots/7/done {"one_shot_complete": true, "task_id": "", "sha": ""}` → rejected with the quoted error.
4. Per the 2026-07-26 doc's documented recovery: `POST /api/slots/7/skip-current-task` (released the stray task) →
   re-`POST /api/slots/7/boot` (same payload). Response: `already_in_progress: false` initially, then a 428 requiring
   `worker.md` in `read_files` (a NEW requirement not present on the FIRST boot call of this session — read it,
   re-`/boot`ed) → offered a DIFFERENT unrelated Class-A task
   (`sports_stats_delayed_live_capture_still_dead_post_fix-004`, `assigned_role: "infra"`).
5. `/done {"one_shot_complete": true}` again → identical rejection.
6. Re-`/boot`ed a THIRD time, this time adding `"slot_role": "ag_closeout_auditor"` explicitly to the payload. Response:
   `already_in_progress: true`, `dispatch_reason: "resume"`, same `sports_stats_...` task still bound.
7. `/done {"one_shot_complete": true}` a third time → **identical rejection**, even with `slot_role` now explicit.

## Why this is not simply "the 2026-07-26 fix didn't ship" or "the same bug, unfixed"

`agent-orchestrator@a01aeae`'s guard was two-part: `slot_role` matches a known `plan_health`-family role **AND**
`spawn_base_role` isn't already a typed role. This session's reproduction is consistent with the SECOND half of that AND
already being false by the time `slot_role` was supplied — i.e. by step 6, `spawn_base_role` had already been stamped to
something typed (circumstantial evidence: the two Class-A tasks offered across steps 1 and 4 carry DIFFERENT
`assigned_role` values, `data_engineering` then `infra` — neither is `ag_closeout_auditor` — meaning whatever dispatcher
logic is choosing candidate tasks for this slot is matching against a typed, non-`ag_closeout_auditor`
`spawn_base_role`, not against nothing). The original fix correctly protects an already-legitimately-typed slot from
being silently reclassified — but that means a slot whose `spawn_base_role` got typed BEFORE its `ag_closeout_auditor`
boot call ever ran (e.g. by a default/generic dispatch that claimed the slot first, or by this session's own first
`/boot` call itself, which had no `slot_role` field and may have been treated as a plain `worker` per `worker.md`'s own
boot example showing `slot_role: ""` for a generic worker) is left in exactly this stuck state — the lazy-create guard's
protective condition and the actual failure mode collide.

## Why it matters

Identical framing to the 2026-07-26 doc: this session did real, complete, shipped work (a full ci-tranche closeout
audit, two drafted AO-dispatch plans, one filed script-bug issue) and cannot signal `/done` per its own role contract.
Per `ao_uniform_agent_liveness_contract_2026_07_20` A1, a one-shot session that cannot signal done either sits alive
being re-nudged forever, or requires an operator to notice and manually kill it — silently discarding the fact that the
work finished. This is the SAME liveness/accounting gap the 2026-07-26 doc described, now with the narrower repro detail
(the offered Class-A tasks' differing `assigned_role`) that should let a fix distinguish "genuinely already typed by a
prior legitimate dispatch" from "typed only because THIS session's own boot call lacked `slot_role` and got defaulted."

## Recommended decision

> **✅ Shipped (2026-07-29, slot-15) — supersedes the abandoned `b1fa85d` recovery note below.** slot-15 diagnosed this
> independently (root cause below) and shipped `agent-orchestrator@bb13e93` before finding the stale banner. The
> preserved `origin/wip-preserve/orchestrator-slot-11-b1fa85d` branch attempted the SAME idea (release a stray
> current_task binding when `req.slot_role` is plan_health-family) but was **incomplete**: it left `pick_next_task()`
> unguarded, so on the very same `/boot` call that released the stray task, `pick_next_task()` could immediately re-bind
> a DIFFERENT Class-A task before ever reaching the `PLAN_HEALTH_FAMILY_ROLES` lazy-create gate — it never shipped, so
> this gap was never exercised live. `bb13e93` closes both halves (see root-cause note + todo 1 below) and was NOT
> cherry-picked from `b1fa85d` (no reimplementation risk — independently verified equivalent-or-better via a direct diff
> of the two). `b1fa85d` is now safely dead — no action needed on that branch.
>
> **Root cause, precisely** (differs from this doc's own hypothesis above): the live repro's "spawn_base_role already
> typed" framing was a red herring. `assign_task_to_slot()` (`server/state_store/slots.py:81`) explicitly sets
> `slot.spawn_base_role = None` whenever a Class-A task is bound — it does NOT leave a stale typed value behind. The
> actual blocker was structural: `boot_slot()`'s very first check,
> `if slot.current_task is not None: ... return already_in_progress=True, dispatch_reason="resume"`, runs BEFORE the
> `req.slot_role in PLAN_HEALTH_FAMILY_ROLES` gate `a01aeae` added further down (that gate lives only inside the
> `if picked is None:` branch). Once ANY `/boot` call — typed or not — bound a foreign Class-A task via
> `assign_task_to_slot`, every SUBSEQUENT `/boot`, even one supplying the correct `slot_role`, short-circuited on that
> top-of-function resume check and never reached the lazy-AgentRow gate at all.

- [x] ✅ [BACKEND] P2. **DONE 2026-07-29 (slot-15), `agent-orchestrator@bb13e93`.** Two changes to `boot_slot()`
      (`server/routes/slots_worker.py`): (1) when a bound `current_task` is found on a boot declaring a
      `PLAN_HEALTH_FAMILY_ROLES` `slot_role`, release it back to the queue (`ss.release_task_to_queue` +
      `ss.clear_slot_assignment`) and fall through to normal dispatch instead of resuming it — self-heals an
      already-poisoned slot, regardless of whether `backlog.get()` still resolves the stray task (a stricter guard than
      `b1fa85d`'s, which left a ghost pointer unreleased when `existing is None`); (2) force `picked = None` (skip
      `pick_next_task()` entirely) whenever `slot_role` is plan_health-family, so these roles can never bind a Class-A
      task in the first place — including the case `b1fa85d` didn't cover (an unassigned `assigned_role=None` task,
      which the existing `_blocks_craft_role` craft-scoping filter deliberately lets through to ANY slot regardless of
      `slot_role`). Answers this todo's own question: boot-prompt-template correction (option 2) is NOT sufficient alone
      — even a clean first boot with `slot_role` declared from the start was still exposed to the unassigned-task leak,
      so the code-side gate (option 1, generalized) is the real fix; the template gap remains a good defense-in-depth
      follow-up but isn't required to close this bug. `quality-gates.sh` green (1968 backend tests).
- [x] ✅ [TEST] P2. **DONE 2026-07-29 (slot-15), same commit.** Two new regression tests in
      `tests/test_boot_typed_role_gate.py`:
      `test_direct_boot_first_call_missing_slot_role_then_correct_role_releases_stray_task` reproduces the EXACT live
      sequence (first `/boot` with no `slot_role` binds a stray Class-A task → second `/boot` with the correct
      `plan_health`-family `slot_role` releases it + lazily creates the AgentRow → `one_shot_complete` succeeds) and
      `test_plan_health_family_role_never_dispatched_a_generic_class_a_task` covers the unassigned-task-leak case found
      while fixing todo 1.

## Current session status (informational, not part of the fix)

This session's assigned mandate (the ci-tranche closeout audit, `/ag-closeout-audit ci` autonomous mode) is fully
complete: covering-plan set re-derived (batch1 archived-closeout-doc wrinkle handled), a real script bug found + filed
(`generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md`), 9 new
orphan candidates classified via a Workflow, batch1's Deferred items re-triaged, and
`ci_satellite_ao_dispatch_batch2_2026_07_29.md` + its gated finalize drafted (both `status: draft`, validated clean
against every plan-hygiene checker). `git rev-list --count HEAD ^origin/live-defi-rollout` = 0 (fully pushed,
`unified-trading-pm@b8a45042f`). Unable to formally signal `/done` due to the gap above; ending this turn with a clear
final status heartbeat instead so the dashboard reflects real state, per the 2026-07-26 precedent's own closing move.
