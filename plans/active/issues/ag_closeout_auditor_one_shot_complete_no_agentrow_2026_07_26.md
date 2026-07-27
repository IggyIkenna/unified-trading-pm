---
doc_type: issue
title:
  "ag_closeout_auditor (and likely other role-spawned) sessions booted directly via POST /api/slots/{N}/boot never get a
  lifecycle=one_shot AgentRow — one_shot_complete permanently rejects with 'no active agent owns its session', distinct
  from the already-fixed slot_stale_spawn_base_role_stuck_task_less_2026_07_25.md bug"
summary: >-
  Reproduced live on slot 8, 2026-07-26, running a fresh ag_closeout_auditor dispatch (tranche=tradfi). Session was
  spawned per the standard AGENT BOOT sequence (heartbeat -> read RULES.md/worker.md/ag_closeout_auditor.md -> POST
  /api/slots/8/boot with role/tranche in the body) — never through `POST /api/plan-health/dispatch {"mode":
  "ag_closeout", "tranche": "tradfi"}`, which `ag_closeout_auditor.md`'s own `triggers:` field names as this role's
  actual entry point. After completing the full audit (Phase 0-2, per-doc classification, one filed finding, shipped
  unified-trading-pm@77c9330fb) and following the role file's documented STEP 2 completion contract exactly (`POST
  /api/slots/8/done {"task_id": "", "sha": "", "evidence": "...", "one_shot_complete": true}`), the call was rejected:
  `{"detail": "one_shot_complete on slot 8 but no active agent owns its session 'orch-slot-8' — a Class-A worker must
  /done with a task_id."}`. This is the SAME error message documented in
  `slot_stale_spawn_base_role_stuck_task_less_2026_07_25.md`, but that bug's root cause (a stale `spawn_base_role` with
  no matching live `AgentRow`, fixed `agent-orchestrator@1e74784`/`@41840c1`) does NOT apply here: this session's
  `/boot` response showed `already_in_progress: true` with an UNRELATED Class-A backlog task
  (`slot_stale_spawn_base_role_stuck_task_less-004`, ironically the very task tracking the OTHER bug) already bound to
  the slot — releasing it via `POST /api/slots/8/skip-current-task` and re-`/boot`ing cleanly resolved that binding
  (`dispatch_reason` went from `"resume"` to `"no queued task available — prereqs/collisions block all candidates"`,
  `already_in_progress: false`), but `one_shot_complete` STILL rejected identically afterward. This means no live
  `AgentRow` with `lifecycle in ("one_shot", "scheduled")` was ever created for this session at all — `_done_one_off`
  (`server/routes/slots_worker.py:718`) has nothing to find regardless of `spawn_base_role`/task-binding state, because
  (hypothesis, unconfirmed against server code this session) the AgentRow for a `plan_health`-family role is only
  created by the `POST /api/plan-health/dispatch` handler itself, and this session's tmux/session lifecycle bypassed
  that endpoint entirely (spawned directly against a slot the same way any generic worker session is).
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, slot-lifecycle, one-shot, ag_closeout_auditor, plan_health, self-heal]
related: [/plans/active/issues/slot_stale_spawn_base_role_stuck_task_less_2026_07_25.md]
created: 2026-07-26
parent_epic: agent_operating_framework_master
priority: P2
estimate_class: refactor
source: "slot 8, ag_closeout_auditor (tranche=tradfi), 2026-07-26, discovered while completing the daily tradfi audit"
assigned_vm: planning
execution_scope: NA
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
---

## What I found

A `plan_health`-family role session (`ag_closeout_auditor`, one-shot/scheduled per its own frontmatter
`lifecycle: scheduled`) spawned and booted successfully via the generic `/api/slots/{N}/boot` path — same as any worker
— completed its full assigned task (a tradfi closeout-completeness audit, real work shipped:
`unified-trading-pm@77c9330fb`), then could not signal completion via its role file's own documented contract
(`one_shot_complete: true`). The rejection persisted across two independent recovery attempts (releasing an unrelated
stale task binding; a clean re-`/boot`), both of which resolved their own symptom (`already_in_progress` went
`true`→`false`) without resolving the underlying `one_shot_complete` rejection.

Working hypothesis: `POST /api/plan-health/dispatch` is the ONLY code path that constructs the `AgentRow` with
`lifecycle in ("one_shot", "scheduled")` that `_done_one_off` requires to archive the session. A session that reaches a
slot's tmux pane via any OTHER route (e.g. a manually-started tab, or a spawn mechanism that hands the role/tranche
straight to `/boot` instead of routing through `/plan-health/dispatch` first) has no such AgentRow to find, no matter
how many times `/boot`/`skip-current-task` are retried — because those calls don't create the missing row, they only
clear slot-level task/role bindings that were never the actual blocker.

## Why it matters

Every `plan_health`-family role (`ag_closeout_auditor`, and by the same mechanism likely `plan_health`,
`plan_reconciler`, `docs_reconciler` — all named in `ag_closeout_auditor.md`'s own "same B-block pattern" note) is
one-shot: it does real, sometimes substantial work (this session: a full corpus cross-reference audit + a filed, shipped
finding) and then is CONTRACTUALLY REQUIRED to signal completion and stop, per
`ao_uniform_agent_liveness_contract_2026_07_20` A1. If the session was spawned via any path other than
`/api/plan-health/dispatch`, it can complete all its real work correctly and still have no way to signal done — the tmux
session either sits alive forever (re-nudged indefinitely, per the role file's own warning: "ending your turn leaves
your tmux session alive and the backend re-nudges it forever") or an operator has to notice and manually kill it,
silently discarding the fact that the work actually finished successfully. This is a liveness/accounting gap, not just a
cosmetic error message.

## Recommended decision

- [x] ✅ [BACKEND] P2. **DONE 2026-07-26 (slot-14).** Option (a): `boot_slot()` now lazily constructs the missing
      `AgentRow` with `lifecycle="one_shot"` when a slot boots with `slot_role` matching a known `plan_health`-family
      role (`PLAN_HEALTH_FAMILY_ROLES`, newly exported from `plan_health.py`) and `spawn_base_role` isn't already a
      typed role — via the same `register_agent()` helper `plan_health.dispatch()` uses, then persists `spawn_base_role`
      so a subsequent `/boot` takes the existing (already-tested) resume branch instead of re-registering. 3 new
      regression tests in `test_boot_typed_role_gate.py`: the lazy-create fires + holds the slot `working`,
      `one_shot_complete` succeeds afterward (the exact live rejection this doc reproduced), and a second `/boot`
      doesn't double-register. `agent-orchestrator@a01aeae`, `quality-gates.sh` green (1749 backend + 137 dashboard
      tests).
- [ ] [OPERATOR] P3. Confirm whether slot 8's `ag_closeout_auditor` dispatch (dispatch_id `agt-9ddfc3`, 2026-07-26) was
      intentionally spawned outside the normal `/api/plan-health/dispatch` → daily-systemd-timer path (e.g. a manual
      test/dev invocation) — if so this may be a one-off rather than a live production gap; if the daily timer itself is
      capable of producing this same bypass, that's the more urgent half of this finding. This session's actual audit
      work is verified complete and shipped regardless of how the plumbing question resolves.
      **ANSWERED 2026-07-27 (slot-4) — this IS a live, recurring gap, not a one-off; see Update below for the precise
      residual condition the 2026-07-26 fix does not cover.**

## Update 2026-07-27 (slot-4, ag_closeout_auditor, tranche=defi) — reproduced AGAIN after the `agent-orchestrator@a01aeae` fix; identifies the exact residual condition

Hit the byte-identical rejection today, on a fresh dispatch (`dispatch_id agt-1c2932`, `TRANCHE=defi`), AFTER the
`DONE 2026-07-26` fix above had already shipped. Sequence observed:

1. STEP 0 boot-started heartbeat, BEFORE reading any role file, already returned `already_in_progress: true` with an
   UNRELATED Class-A backlog task (`data_pipeline_check_mdps_features-023`, `model: sonnet`, `assigned_role: infra`) —
   i.e. slot 4's session had pre-existing Class-A `spawn_base_role`/task-binding state from a PRIOR occupant BEFORE my
   `ag_closeout_auditor` dispatch's own `/boot` call ever ran.
2. Two full `/boot` attempts (both correctly including `slot_role`/role context after the required `read_files` 428
   round-trip) still resumed that same stale Class-A task (`dispatch_reason: "resume"`) instead of registering a fresh
   one-shot `AgentRow` — the lazy-create path this doc's fix describes never fired.
3. Completed the full audit anyway (65-doc defi Phase 0-3 triage, shipped `unified-trading-pm@af57cfcff` +
   `@f5fc5a067`), then hit the identical `one_shot_complete` rejection.
4. `POST /api/slots/4/skip-current-task` released the stale task — but the VERY NEXT `/heartbeat` immediately handed
   back ANOTHER unrelated Class-A task (`capability_wizard_gap_discovery-010`, then after a second skip,
   `cefi_tardis_write_schema_contract_column_mismatch-003`) rather than going idle or resolving to a one-shot
   registration. `/done` with `one_shot_complete: true` was retried 3 ways (empty `task_id`, `task_id` set to the
   session's own `DISPATCH_ID`, after clearing every stale task binding) — identical rejection every time:
   `"one_shot_complete on slot 4 but no active agent owns its session 'orch-slot-4' — a Class-A worker must /done with
   a task_id."`

**This precisely confirms and narrows the fix's stated condition** ("`boot_slot()` now lazily constructs the missing
`AgentRow`... when... `spawn_base_role` isn't already a typed role"): slot 4 already had a **typed Class-A
`spawn_base_role`** bound from its prior occupant BEFORE this `ag_closeout_auditor` dispatch's first `/boot` call —
so the lazy-create's own guard condition (`spawn_base_role isn't already a typed role`) is FALSE, and the fix
correctly, deliberately does NOT override it (per its own logic) — it only helps a slot that boots into `plan_health`
role territory with a genuinely EMPTY/untyped `spawn_base_role`. A slot inheriting a **stale but typed Class-A**
binding from whatever ran there immediately before is the exact case the fix does not cover, and — per this session's
repeated `skip-current-task` → immediately-rehanded-a-new-Class-A-task cycle — **clearing the stale task does NOT
clear the underlying `spawn_base_role` typing**, so no amount of `/skip-current-task` + re-`/boot`/`/heartbeat`
converges on a one-shot registration; the slot just keeps cycling through the Class-A backlog instead.

**Refined recommendation**: the lazy-create branch (or a new one) needs to also fire when a `plan_health`-family
`slot_role`/dispatch arrives at a slot whose `spawn_base_role` is ALREADY a typed Class-A role — i.e. the incoming
one-shot dispatch should be able to REPLACE a stale prior-occupant's typing, not just fill an empty one, since a slot
number is reused across arbitrary dispatch types over its lifetime and the previous occupant's `/done` may not have
(or, per `slot_dual_flip_pattern_violation`-style gaps elsewhere, sometimes cannot) clear its own typing before the
next dispatch lands. Practically: `POST /api/plan-health/dispatch` (or an equivalent explicit slot-role-assignment
call) should be authoritative over whatever `spawn_base_role` a slot currently holds, not deferential to it.

**This session's actual audit work is verified complete and shipped regardless** (`unified-trading-pm@af57cfcff`,
`@f5fc5a067`, `git rev-list --count HEAD ^origin/live-defi-rollout` = 0). Ending this turn with a clear final report
instead of a working `/done` call, per this doc's own 2026-07-26 precedent.

## Current session status (informational, not part of the fix)

This session's assigned mandate (the tradfi closeout audit) is fully complete: covering-plan set discovered and
cross-checked, 4 genuine non-batchable residual orphans identified (matching the taxonomy, no new batch drafted since
nothing would convert), one new finding filed and shipped (`issues/tradfi_sp500_ml_stale_mdps_blocker_2026_07_26.md`,
`unified-trading-pm@77c9330fb`). `git rev-list --count HEAD ^origin/live-defi-rollout` = 0 (fully pushed). Unable to
formally signal `/done` due to the gap above; ending this turn with a clear final status heartbeat instead so the
dashboard reflects real state.
