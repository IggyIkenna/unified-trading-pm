---
doc_type: plan
title: AO held safety fixes — dispatch (liveness-by-progress gate + cross-role reply routing)
summary:
  The two safety-sensitive backend fixes held out of ao_remediation_a/B per operator ruling Q2 (2026-07-23), now
  dispatched per operator ruling 2026-07-24 — checked and confirmed to touch NO file any ao_remediation_b_code_chain
  todo touches, so they run in parallel now rather than waiting for Plan B to finish. Each already carries a stated
  regression-test gate in its own todo text, which the operator confirmed IS the review mechanism (a gate + green QG) —
  no extra PR-review ceremony required.
status: complete # (was: active) 2026-07-24 archival: all 2 todos [x], evidence cited inline on each checkbox
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, worker-liveness, cross-role-messaging, plan-reconcile]
related:
  [
    /plans/archive/2026_07/ao_issue_docs_consolidated_remediation_2026_07_23.md,
    /plans/archive/2026_07/ao_remediation_a_independent_fixes_2026_07_23.md,
    /plans/archive/2026_07/ao_remediation_b_code_chain_2026_07_23.md,
    /plans/archive/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md,
    /plans/archive/2026_08/issues/agent_reply_cannot_address_a_different_role_silent_cross_role_blind_spot_2026_07_22.md,
  ]
created: 2026-07-24
last_updated: 2026-07-24
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  "Split from ao_issue_docs_consolidated_remediation_2026_07_23's 'Held for operator review (Q2)' section per operator
  ruling 2026-07-24: no file collision with ao_remediation_b_code_chain_2026_07_23 -> dispatch now instead of waiting."
---

# AO held safety fixes — dispatch

> **Split from
> [`ao_issue_docs_consolidated_remediation_2026_07_23`](/plans/archive/2026_07/ao_issue_docs_consolidated_remediation_2026_07_23.md)'s
> "Held for operator review" section.** Operator ruling 2026-07-23 (Q2) held these out of the original dispatch because
> each touches machinery where a careless change is dangerous (at-least-once message delivery; genuine wedge detection).
> Operator ruling 2026-07-24: dispatch both now, without waiting for
> [`ao_remediation_b_code_chain_2026_07_23`](/plans/archive/2026_07/ao_remediation_b_code_chain_2026_07_23.md) to
> finish, **on the condition that neither collides with Plan B's file set** — checked at authoring (below) and confirmed
> clear. The stated regression-test gate on each todo, plus a green `quality-gates.sh`, IS the review mechanism; no
> separate PR-review step is required.

> **Parallel-safety proof (checked at authoring 2026-07-24):** todo 1 touches only
> `server/worker_liveness/_git_alerts.py`; todo 2 touches only `server/routes/agents.py` + `server/models/agents.py`.
> Plan B's 14 todos touch `scripts/dev/slot-git-status-report.sh`, `scripts/dev/slot-cron-ff-pull.sh`,
> `server/routes/git_health.py`, `orphan_reap.py`, worker-liveness-watchdog kick-escalation logic, and shared-doc
> recorders — no overlap with either file set here, and the two todos here don't share a file with each other either, so
> both run concurrently.

## Todos

- [x] ✅ [BACKEND] P2. Add a liveness-by-progress gate to `maybe_alert_git_staleness` and `maybe_nudge_on_red_repos` in
      `server/worker_liveness/_git_alerts.py` so a burst-committing worker is not classified as wedged. Suppress or
      soften when the worktree's last commit (`git log -1 --format=%ct`) is newer than the sustain window, or a live
      child process runs under it (`pgrep -f <worktree>`). Today these key purely on `dirty_files`/`ahead`/`behind` plus
      age, and `_git_surfaces_pass` runs unconditionally for every slot — its own docstring records that the 2026-07-14
      coverage-gap fix REMOVED the live-worker gate, so an actively-working slot has no exemption. **Gate**: a
      regression test where a recent-commit-but-still-dirty worker does NOT fire the staleness alert, with the
      genuinely-stale-slot tests still green. — **SHIPPED `agent-orchestrator@0757a75`**: new
      `_worktree_has_live_progress(worktree, now)` in `_git_alerts.py` checks `git -C <worktree> log -1 --format=%ct`
      against a `LIVENESS_PROGRESS_WINDOW_S` (10 min) window, falling back to `pgrep -f <worktree>` for a live child
      process; best-effort (missing worktree/binary/failure reads as False = original alerting behavior). Wired into
      both `maybe_alert_git_staleness` (after the red-summary build, before the throttle/page) and
      `maybe_nudge_on_red_repos` (before composing the nudge message). Regression coverage in
      `tests/test_git_staleness_alerting.py`: burst-committing-worker suppression for both the staleness page and the
      red-repo nudge, a control proving the genuinely-stale path still pages, plus direct unit coverage of the predicate
      (recent commit / old commit+no proc / live proc / no worktree at all) — full suite green (1606 passed, 1 skipped).
- [x] ✅ [BACKEND] P1. Route `agent_reply()` in `server/routes/agents.py` to the ORIGINATING role when the answered
      message came from a peer, instead of always the replier's own thread. It currently calls
      `post_agent_message_by_role` with `target_role=agent.role, direction="from_agent"` unconditionally, and
      `AgentReplyRequest` in `server/models/agents.py` has no cross-role target field — so a reply to a peer lands on
      the replier's own thread and the peer never sees it in its poll. When `in_reply_to` resolves to a message whose
      `from_role` differs, post `direction="to_agent"` to that `from_role` plus the tmux nudge. **Gate**: a regression
      test proving a cross-role reply lands in the target role's next `/poll` (not merely its `/history`), with the
      existing same-role reply-ack tests still green. — **SHIPPED `agent-orchestrator@738b2d3`**: `agent_reply()` now
      resolves `in_reply_to`'s origin message (new `ss.get_agent_message`); when its `from_role` is a genuine peer agent
      role (not `operator`, not the replier's own role) it posts `direction="to_agent"` to that role + a best-effort
      tmux nudge, else keeps the unchanged own-thread `from_agent` behavior. Regression coverage in
      `tests/test_agent_reply_cross_role_routing.py` (4 tests: cross-role lands in the peer's next `/poll`, operator
      replies stay own-thread, same-role `in_reply_to` isn't mistaken for cross-role, no-`in_reply_to` keeps default) —
      full suite green (1595 passed, 1 skipped).

## Progress Log

- **2026-07-24**: Authored by splitting the two Q2-held todos out of `ao_issue_docs_consolidated_remediation_2026_07_23`
  per operator ruling — dispatch now, confirmed no file collision with Plan B. Born `status: active`,
  `assigned_vm: planning` — dispatchable to the AO fleet.
- **2026-07-24**: Slot 4 shipped the P1 cross-role `/reply` routing fix — `agent-orchestrator@738b2d3`, full QG green
  (1595 passed, 1 skipped). Todo 2 flipped. The remaining P2 liveness-by-progress-gate todo and the P3 review sign-off
  are still open.
- **2026-07-24**: Slot 6 shipped the P2 liveness-by-progress gate — `agent-orchestrator@0757a75`, full QG green (1606
  passed, 1 skipped). Todo 1 flipped. Both of this plan's todos are now shipped, satisfying its stated
  regression-test-gate-is-the-review-mechanism contract. The source issue doc
  (`plans/active/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md`) still carries its own
  separate P2 `[DOCS]` todo (apply the same commit-recency/live-process check to the `agents/review.md` wedge heuristic)
  and P3 `[REVIEW]` operator-sign-off todo — those are out of this plan's scope and remain open there.
