---
doc_type: plan
title: AO issue-docs remediation — held + blocked residual (the parts NOT dispatched to AO)
summary:
  The 2026-07-23 /plan-reconcile AO-scope sweep produced 22 dispatchable todos, which were offloaded 2026-07-23 into two
  child plans — ao_remediation_a_independent_fixes (8, parallel) and ao_remediation_b_code_chain (14, sequential, gated
  behind A). What remains here is only the work that is NOT ready for the fleet — 2 safety-sensitive backend todos held
  for operator review (operator ruling Q2) and 4 operator-decision / upstream-blocked items. assigned_vm is NA so none
  of it dispatches; each becomes an AO todo only once the operator rules or the blocker clears.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, held, blocked, plan-reconcile]
related:
  [
    /plans/active/ao_remediation_a_independent_fixes_2026_07_23.md,
    /plans/active/ao_remediation_b_code_chain_2026_07_23.md,
    /plans/active/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md,
    /plans/active/issues/agent_reply_cannot_address_a_different_role_silent_cross_role_blind_spot_2026_07_22.md,
  ]
created: 2026-07-23
last_updated: 2026-07-23
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: "/plan-reconcile AO-scope run 2026-07-23"
---

# AO issue-docs remediation — held + blocked residual

> The 22 dispatchable todos from the 2026-07-23 `/plan-reconcile` sweep were offloaded into two child plans:
> [`ao_remediation_a_independent_fixes_2026_07_23`](/plans/active/ao_remediation_a_independent_fixes_2026_07_23.md) (8
> parallel) and [`ao_remediation_b_code_chain_2026_07_23`](/plans/active/ao_remediation_b_code_chain_2026_07_23.md) (14
> sequential, gated behind A). **This doc holds only the work that is NOT dispatchable yet** — `assigned_vm: NA`, so
> regen never ingests it. Each item below moves to a child plan (or a new one) once the operator rules or its blocker
> clears.

## Held for operator review (operator ruling Q2, 2026-07-23)

> Both are real, code-verified backend fixes, deliberately NOT dispatched: each touches machinery where a careless
> change is dangerous — at-least-once message delivery, and genuine wedge detection — so the operator holds the gate at
> PR-review time. Dispatch these (move to Plan B or a new plan) only after that review mechanism is decided.

- [ ] [BACKEND] P2. Add a liveness-by-progress gate to `maybe_alert_git_staleness` and `maybe_nudge_on_red_repos` in
      `server/worker_liveness/_git_alerts.py` so a burst-committing worker is not classified as wedged. Suppress or
      soften when the worktree's last commit (`git log -1 --format=%ct`) is newer than the sustain window, or a live
      child process runs under it (`pgrep -f <worktree>`). Today these key purely on `dirty_files`/`ahead`/`behind` plus
      age, and `_git_surfaces_pass` runs unconditionally for every slot — its own docstring records that the 2026-07-14
      coverage-gap fix REMOVED the live-worker gate, so an actively-working slot has no exemption. **Gate**: a
      regression test where a recent-commit-but-still-dirty worker does NOT fire the staleness alert, with the
      genuinely-stale-slot tests still green.
- [ ] [BACKEND] P1. Route `agent_reply()` in `server/routes/agents.py` to the ORIGINATING role when the answered message
      came from a peer, instead of always the replier's own thread. It currently calls `post_agent_message_by_role` with
      `target_role=agent.role, direction="from_agent"` unconditionally, and `AgentReplyRequest` in
      `server/models/agents.py` has no cross-role target field — so a reply to a peer lands on the replier's own thread
      and the peer never sees it in its poll. When `in_reply_to` resolves to a message whose `from_role` differs, post
      `direction="to_agent"` to that `from_role` plus the tmux nudge. **Gate**: a regression test proving a cross-role
      reply lands in the target role's next `/poll` (not merely its `/history`), with the existing same-role reply-ack
      tests still green.

## Non-dispatchable — operator decision / upstream-blocked

> `[OPERATOR]` and `BLOCKED-` items. Kept here as the record; none is AO-eligible until resolved.

- [ ] [OPERATOR] P2. Rule on the epic-VM code artifacts — `deployment-service/scripts/vm/launch-epic-vm.sh`,
      `launch-epic-vm-aws.sh`, and the ten `agent-orch-vm-*` prefixes registered `LONG_LIVED_LIVE` in
      `vm_prefix_registry.py`. Per-epic VMs were deprecated 2026-06-27 and CLAUDE.md says delete deprecated code with no
      shims, but the failover module received an explicit KEEP ruling on the multi-VM-may-return argument, so this is a
      judgment call rather than a cleanup. Operator direction 2026-07-23 was to file it and decide later. **Gate**: a
      recorded keep-or-delete ruling; if KEEP, the named single-VM scenario that still needs it.
- [ ] [OPERATOR] P3. Spot-check the live fleet for a slot dirty over 24h with no live session, to rank the periodic
      dirty-resolution sweep. If none exists this is a structural gap with no active incident — a reason to sequence it
      behind P1 work, NOT a reason to close it. **Gate**: the one-line finding recorded in the issue doc.
- [ ] [BACKEND] P2. BLOCKED-OPERATOR-DECISION — resolve the `/api/escalate` versus proposed `/api/escalation/{id}` route
      collision before ANY escalation code is written. `/api/escalate` already exists as the GHA-to-orchestrator CI-wall
      judgment dispatch; the proposed route is operator escalation. Whoever implements the second without noticing the
      first will either collide or wire operator escalations into the CI judgment path. Blocked on the
      `escalation_and_disaster_recovery_master` epic being un-paused. **Gate**: one of the two is renamed, or a recorded
      decision explains why the near-collision is acceptable.
- [ ] [UI] P3. BLOCKED-UPSTREAM-DESIGN — build the backlog-relations view once a design lands. The brief plus real data
      and a 100-task synthetic fixture were handed to the design agent on 2026-07-17; re-checked 2026-07-23 with no
      movement, no `GET /api/backlog/graph` endpoint and no relations UI commit. The model is a cross-cutting GRAPH, not
      a hierarchy, which is why three table/tree attempts were rejected. **Gate**: design received, implemented, and the
      relation a table cannot express — one prereq gating tasks in multiple plans — is visible in one view.

## Parked decisions — not in any plan (judgment calls, per task_template section 4)

Two swept todos are open design questions with no chosen target, so they are not AO-eligible and were never brought into
this plan. They stay in their own issue docs until resolved interactively:

- **`auto_park_no_flipper_rule_not_mechanism_enforced`** — "decide and build, or decline, mechanism-level enforcement".
- **`regen_positional_task_ids_not_content_stable`** — content-derived task ids, deferred until a new incident forces
  it.

## Progress Log

- **2026-07-23**: Authored from the `/plan-reconcile` AO-scope sweep as one draft plan of 28 todos, then split per
  operator rulings: Q1 (split for parallelism) moved the 22 dispatchable todos into child plans A + B; Q2 (hold the 2
  safety-sensitive backend todos) kept them here. This doc was flipped `draft` -> `active` + `assigned_vm: planning` ->
  `NA` so it now tracks only the held/blocked residual without dispatching it.
