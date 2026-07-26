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

## Current session status (informational, not part of the fix)

This session's assigned mandate (the tradfi closeout audit) is fully complete: covering-plan set discovered and
cross-checked, 4 genuine non-batchable residual orphans identified (matching the taxonomy, no new batch drafted since
nothing would convert), one new finding filed and shipped (`issues/tradfi_sp500_ml_stale_mdps_blocker_2026_07_26.md`,
`unified-trading-pm@77c9330fb`). `git rev-list --count HEAD ^origin/live-defi-rollout` = 0 (fully pushed). Unable to
formally signal `/done` due to the gap above; ending this turn with a clear final status heartbeat instead so the
dashboard reflects real state.
