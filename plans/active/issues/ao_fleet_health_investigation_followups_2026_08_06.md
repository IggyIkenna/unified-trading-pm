---
doc_type: issue
title: AO fleet-health investigation (2026-08-06 interactive session) — 4 open follow-ups
summary: >-
  An interactive operator session audited live AO fleet health (worker dispatch, scheduled-job reliability, CI
  escalation behavior, billing) and shipped 3 fixes directly (agent-orchestrator@ce2915f scheduled-job duration
  visibility, @0aa641e ao-self-pull dirty-check gitignore fix, unified-trading-pm@7031856873 Kalshi/Polymarket operator
  ruling). This doc tracks what the session found but did NOT finish before running low on context.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [ao, fleet-health, billing, ci, scheduled-jobs, follow-up]
related:
  [
    /plans/active/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md,
    /plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md,
    /plans/active/issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md,
  ]
created: 2026-08-06
author: unknown
parent_epic: orchestrator_master
priority: P2
source: ["interactive operator session, 2026-08-06"]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

## Context

While auditing why AO wasn't dispatching more workers, the session went deep on scheduled-job reliability (shipped),
then the operator asked 5 more open-ended questions about AO health in one message. The session started investigating
but ran low on context before finishing. This doc is the handoff.

## Already answered (no todo needed — recorded here so nobody re-derives it)

- **CI escalation `still_red_past_deadline` does NOT loop forever and does NOT bloat the backlog with duplicates.**
  `escalation.py`'s `MAX_REESCALATIONS = 1`: a wall gets exactly one re-queue-and-retry after its first 90-min deadline
  miss, then lands as terminal `unresolved`/`still_red_past_deadline` with `register_cooldown()` armed on
  `_wall_cooldown_key(repo, pr_number, wall_type)` — an identical-context re-fire of the SAME failure backs off instead
  of spawning a new worker. This is a deliberate, working dedup mechanism, not a bug.
- **Scheduled-job output IS already persisted outside the repo, and does not need gitignoring.** Live-verified this
  session: the full Claude Code session transcript (JSONL) for a scheduled worker persists at
  `~/.claude-configs/orch-slot-<n>/projects/*/<claude_session_id>.jsonl` on the VM — already outside
  `agent-orchestrator`'s git checkout entirely. What's still genuinely missing (already tracked, not duplicated here) is
  an API/dashboard path to it — see `ao_scheduled_job_reserve_and_staggering_2026_08_04.md`'s open todo "no durable
  transcript... decide between pipe-pane and indexing the Claude session JSONL, then wire it."
- **Most scheduled-job issues ARE auto-resolved by the same worker that found them** (ag_closeout_auditor /
  na_eligibility_auditor's own Phase 3 "apply" step), not a separate sweep-up skill. Genuinely unresolvable ones already
  become `plans/active/issues/<slug>_<date>.md` docs per the workspace's findings-triage HARD RULE — this already
  matches what the operator asked for.

## Open follow-ups

- [ ] [DATA] P2. **Root-cause why slots 4/5/6 briefly showed `status=killed` around 2026-08-06T15:30-16:10Z before
      self-healing on their own.** First attempt this session (activity-log query for `slot_id in (4,5,6)` around that
      window) returned zero rows — likely a field-name mismatch in the query (activity rows use `ts`/`event_type`, not
      `timestamp`/`slot_id` nested in `details`; the correct top-level `slot_id` field wasn't checked). Re-run against
      `/api/activity?limit=500` filtered on `e["slot_id"] in (4,5,6)` and `"2026-08-06T15:"` / `"16:"` in `e["ts"]`,
      looking for `watchdog_slot_killed` / `tmux_session_lost` events specifically. May turn out to be routine churn
      (the fleet showed `tmux_session_lost` firing 300-750×/day as "normal" per a related 2026-08-04 finding in
      `ao_scheduled_job_reserve_and_staggering_2026_08_04.md`) — or the same session-collision class already tracked
      there. (repo: agent-orchestrator)
- [ ] [DATA] P2. **`/api/backlog/usage/windows` returns `spend_usd: null` for every rolling window (1h/5h/24h), despite
      real non-zero token counts in the same windows** — live-verified 2026-08-06 (this is the "Task Token Usage billing
      breakdown looks stuck" the operator flagged). Confirmed the recent `spend_usd`-poisoning fixes
      (`fff23c5`/`796ebf8`/`d81b05f`/`7d73ded`/`0e750c7`, all already merged onto `live-defi-rollout` and deployed to
      the VM as of this session) did NOT clear it. Leading hypothesis, NOT YET CONFIRMED: these fixes are
      DeepSeek-specific (per-token pricing registered for `deepseek-v4-pro`/`-flash`), and Anthropic/Claude tasks may
      have no per-token price registered at all — if `window_task_usage_totals` (`server/state_store/`, exact module not
      yet located) nulls the WHOLE window's `spend_usd` the moment any task in it lacks pricing (matching the documented
      "never a misleading partial sum" convention used elsewhere for `SlotView.session_spend_usd`), then a window
      containing even one Claude task (the vast majority of current fleet activity — `primary_account_id: sub-a-ikenna`
      at ~49%) would ALWAYS read null, by design, not by bug. If confirmed, the real fix is a UI/labeling one (show a
      Claude-tasks-excluded partial sum, or say "DeepSeek-only, N Claude tasks excluded" instead of a bare `null` that
      reads as broken) — NOT a data-pipeline bug. Find the aggregation function and confirm before touching anything.
      (repo: agent-orchestrator)
- [ ] [DATA] P3. **agent-orchestrator PR #813 ("chore(promote): LDR → main (Option-B direct)") appears stale/stuck**:
      `mergeStateStatus=DIRTY`, `mergeable=CONFLICTING`, `updatedAt` unchanged since creation (`2026-08-06T13:07:19Z`,
      ~5.5h+ stale as of this session), and zero GitHub Actions runs of any kind exist on its head branch
      (`promote/agent-orchestrator/dd259b30ccc8`) — meaning `quality-gates-v2` (the required promotion check) has never
      even been triggered against it, not merely failed. This was surfaced answering a concurrent session's handoff ask
      ("confirm 4a77bfe/9c7d55c went green on quality-gates-v2") — the honest answer is it hasn't run at all, and the PR
      itself looks wedged. Not investigated further: whether the standing LDR→main promotion automation
      (`ldr-to-main-promote-fleet.yml`-equivalent; no matching workflow file found in this repo via `gh workflow list`,
      so it likely lives/runs from elsewhere, e.g. unified-trading-pm or a fleet-wide script) is itself stuck, or this
      is expected staleness that a periodic drain will clear on its own. Check
      `main_ci_red_promotion_blocked_by_plan_hygiene_backlog_2026_08_06.md` and
      `promote_ref_orphaned_on_manual_pr_close_2026_08_06.md` first — may already cover this exact class. (repo:
      agent-orchestrator, unified-trading-pm)
- [ ] [DATA] P3. **Re-verify operator-blocked-question → backlog-status transition against CURRENT code**, not this
      session's stale read. `TaskStatus` already has a distinct `"blocked"` value (not folded into queued/dispatched) —
      confirmed via `dashboard/src/types.ts`. But 3 commits landed on `live-defi-rollout` THIS session that directly
      touch this area (`a83050b` operator-gated blocked answers now materialize as real dispatchable tasks, `c290bc5`
      stamp last_ping on answer so the watchdog doesn't race a just-unblocked slot, `18444f5` nudge the worker's tmux
      pane after an operator answer is recorded, `365e18e` scope blocked-answer message delivery to the task it was
      raised for, `cc5961e` let a worker self-declare blocked-question authority) — read those diffs directly rather
      than reasoning from the pre-2026-08-06 behavior. Specifically answer: does the task's status flip
      `blocked -> queued` (needs re-pickup) or `blocked -> dispatched` (same agent resumes) the instant an operator
      answers, and does it matter if the ORIGINAL agent has since been respawned onto a different task (i.e., does the
      answer route to whoever now owns the slot, or to the specific agent_id that asked)? (repo: agent-orchestrator)

## Already executed by a concurrent session (no action needed — recorded so this doc doesn't re-trigger it)

- The cefi coverage-backfill VM relaunch (option-b ruling: non-SPOT) — DONE.
  `cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md` now shows an ON_DEMAND VM
  (`cefi-queue-heavy-binancefutu-x17-20260806-163512`) running, plus a real launcher bug found
  - fixed (`deployment-service@b83256f` — `ON_DEMAND` env var was being unconditionally overridden to `false`).

## Progress Log

- **2026-08-06 (interactive session)**: Shipped 3 fixes directly (scheduled-job dispatched-vs-done + duration
  visibility, ao-self-pull dirty-check gitignore fix, both deployed live to the orchestrator VM and verified working
  end-to-end). Recorded the operator's Kalshi/Polymarket ruling in
  `defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md` (`unified-trading-pm@7031856873`). Ran low on
  context mid-investigation of the operator's 5 follow-up questions; this doc captures what's answered vs still open so
  the next session doesn't restart from zero.
