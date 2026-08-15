---
doc_type: issue
title: AO fleet-health investigation (2026-08-06 interactive session) — follow-ups + PR #813/#791 CI wedge
summary: >-
  An interactive operator session audited live AO fleet health (worker dispatch, scheduled-job reliability, CI
  escalation behavior, billing) and shipped 5 fixes directly (agent-orchestrator@ce2915f scheduled-job duration
  visibility, @0aa641e ao-self-pull dirty-check gitignore fix, @ff12b96 Task Token Usage null-spend explanation,
  @5872b3e5 main->LDR backmerge resolving PR #791/#813's CI wedge, unified-trading-pm@7031856873 Kalshi/Polymarket
  operator ruling). ALL 4 original follow-up investigations plus the PR #791 remediation it surfaced are now closed:
  billing root-caused + fixed; slot 4/5/6 "kills" confirmed routine self-heal churn, not a bug; blocked-question status
  transition re-verified against live code; PR #791's real main<->LDR git conflict resolved (12 files, one real
  auto-merge regression caught + stripped) and merged, PR #791 now `state: MERGED`. RESOLVED — archiving.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [ao, fleet-health, billing, ci, scheduled-jobs, follow-up, ci-wedge, backmerge-conflict]
related:
  [
    /plans/archive/2026_08/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md,
    /plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md,
    /plans/active/issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md,
  ]
created: 2026-08-06
author: unknown
parent_epic: orchestrator_master
priority: P1
source: ["interactive operator session, 2026-08-06"]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    agent-orchestrator/.github/workflows/main-backmerge-to-ldr.yml,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/issues/main_backmerge_to_ldr_silent_failure_2026_08_02.md,
    /plans/archive/2026_08/issues/agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md,
  ]
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

- [x] [DATA] P2. **Root-cause why slots 4/5/6 briefly showed `status=killed` around 2026-08-06T15:30-16:10Z — CONFIRMED
      routine self-healing churn, NOT a bug, no code change needed.** Re-ran the corrected query
      (`GET /api/activity?slot=<n>&since=...&until=...&exclude=<noise-types>`, top-level `slot_id`/`ts`/`event_type`
      fields, per the earlier field-mismatch fix) against all 3 slots for the exact window. Result: **zero**
      `watchdog_slot_killed` events for slot 4, 5, or 6 anywhere in 2026-08-06T15:20-16:20Z (the only
      `watchdog_slot_killed` hits that day for these 3 slots were slot 4 @01:18Z and slot 6 @07:57Z — both hours
      earlier, already long-recovered). Every apparent "death" in the window was the well-known
      `context_saturated_session_lost_task_requeued` + `tmux_session_lost` pair (a worker's Claude session hit its
      context limit mid-task), immediately followed within 1-3 minutes by `autospawn_succeeded` → `task_dispatched` →
      `slot_boot` — i.e. the fleet's autospawn self-heal working exactly as designed, not a watchdog kill. This matches
      the already-documented "`tmux_session_lost` fires 300-750×/day as normal churn" finding in
      `ao_scheduled_job_reserve_and_staggering_2026_08_04.md` — whatever `status: killed` the operator saw on the
      dashboard was almost certainly a brief live-snapshot read during that 1-3 min self-heal gap, not a standing
      failure. No follow-up action. (repo: agent-orchestrator)
- [x] [DATA] P2. **`/api/backlog/usage/windows` returns `spend_usd: null` for every rolling window — CONFIRMED
      by-design, not a bug; fixed as a UI/labeling gap.** Root cause: `server/deepseek_usage.py`'s `_PRICE_PER_MILLION`
      registers ONLY `deepseek-v4-pro`/`deepseek-v4-flash` — Anthropic/Claude has no price-table entry at all, so
      `price_usage()` returns `None` for every Claude turn, and `window_task_usage_totals`'s
      `spend_known = all(r.spend_usd     is not None for r in in_window)` rule (deliberate, matches
      `deepseek_usage.compute_task_usage`'s own "never a partial/misleading sum" convention) nulls the WHOLE window's
      `spend_usd` the instant one Claude task is inside it — and Claude is ~49% of fleet activity, so it always is. Fix
      (not a partial-sum reversal — that convention stays intact per the codebase's own documented rationale): added
      `unpriced_row_count` to `TaskUsageWindowTotals`/`TaskUsageWindowView`, threaded through `window_task_usage_totals`
      → `/api/backlog/usage/windows` → dashboard, so a null Spend/Avg-$/$-per-turn cell now carries a tooltip ("N tasks
      in this window used a model with no registered $ price (e.g. Anthropic/Claude) — spend is intentionally left
      blank...") instead of a bare dash that reads as broken. `quality-gates.sh` green (full suite incl. dashboard
      tsc+vitest). Evidence: agent-orchestrator@ff12b96. (repo: agent-orchestrator)
- [x] [DATA] P1 (escalated from P3 — CONFIRMED a real, worsening, unaddressed wedge, not staleness).
      **agent-orchestrator PR #813 ("chore(promote): LDR → main (Option-B direct)") is genuinely stuck, root-caused to
      an unresolved backmerge conflict PR #791 that has sat untouched for 24h+.** Checked the two candidate docs first —
      NEITHER covers this: `main_ci_red_promotion_blocked_by_plan_hygiene_backlog_2026_08_06.md` is a different repo
      (unified-trading-pm) with a different root cause (plan-hygiene corpus gate);
      `promote_ref_orphaned_on_manual_pr_close_2026_08_06.md` is a low-severity cosmetic orphan-ref issue on an
      already-CLOSED PR — #813 is still OPEN. This is a new finding.

      **Evidence chain:**
                      1. #813: `mergeStateStatus=DIRTY`, `mergeable=CONFLICTING`, `updatedAt` frozen at creation
                         (`2026-08-06T13:07:19Z`) — now 24h+ stale. `gh run list --branch promote/agent-orchestrator/dd259b30ccc8`
                         returns **zero** runs of any workflow, ever — `quality-gates-v2` never triggered, not merely failed. The legacy
                         commits-status API shows only `sit-gate/fleet-green` and `semver-agent/label-check` posted (both success,
                         both at PR-open time) — `quality-gates-v2` and `quickmerge-provenance` (2 of the 3 real required gates per
                         codex) never ran at all.
                      2. `gh api repos/.../compare/main...live-defi-rollout` → main is **5 commits ahead of what LDR has merged**, i.e.
                         main has moved past the tree #813's promote branch was built from — this IS the conflict.
                      3. Root cause: PR #791 ("[backmerge] main → live-defi-rollout (CONFLICT — needs resolution)"), the
                         `main-backmerge-to-ldr.yml`-opened auto-backmerge PR, has been **OPEN since 2026-08-05T16:42:19Z with ZERO
                         comments and no further activity** — over a day unaddressed. Until main's divergent commits land back on LDR
                         via #791, every fresh LDR→main promote PR (like #813) will keep conflicting against main's newer state.
                      4. `gh run list --workflow main-backmerge-to-ldr.yml` shows its last run was the exact one that opened #791
                         (2026-08-05T16:41:56Z, `conclusion=success` — opening the conflict-PR + escalating IS its designed success
                         path, confirmed by the archived `main_backmerge_to_ldr_silent_failure_2026_08_02.md` fix). **Zero runs since**,
                         despite main moving 5 commits further ahead — strongly suggesting the workflow short-circuits (skip re-opening)
                         once a conflict PR already exists, so main's drift is silently accumulating, not retriggering new attempts.
                      5. **Not confirmed**: whether that 2026-08-05 run's `escalate-to-orchestrator` dispatch (which per the archived
                         doc's fix should spawn an opus conflict_resolver worker) actually fired for #791 specifically — #791 has 0
                         comments, which is consistent with either "dispatch never fired" (a possible regression) or "it fired,
                         dispatched, and the resolution is simply still queued/in-progress elsewhere." Whoever picks this up next
                         should check the backlog/activity log for a conflict_resolver task tied to PR #791 or SHA `main` before
                         resolving the conflict by hand.

                      **Next step**: resolve PR #791's actual conflict (main↔LDR divergence) — this is real judgment-heavy conflict
                      work, not something to blind-fix here. Once #791 merges, close/re-verify whether #813 auto-clears or needs a
                      fresh promote PR. (repo: agent-orchestrator)

- [x] [INFRA] P1. **Resolved PR #791's conflict by hand — merged, main↔LDR fully reconciled.** Never found an existing
      `conflict_resolver` escalation for it (checked backlog/activity, none tied to this PR), so resolved directly: for
      each of the 12 conflicting files, read both sides' actual diverged commits rather than blind-picking — LDR (831+
      commits ahead) had independently superseded every one of main's 5 divergent commits, so the correct resolution was
      byte-identical to LDR's own tip in every file. One real bug caught along the way: the auto-merge's non-conflicting
      hunks in `server/main_agent_keeper.py` silently reintroduced a hand-rolled
      `pick_headroom_account(..., provider="deepseek")` fallback at two call sites that LDR's
      `main_agent_keeper_deepseek_routing_gap_2026_08_06` fix had deliberately removed (delegating to
      `select_account_for_spawn`'s own policy instead) — stripped both reintroduced blocks so the merge didn't silently
      revert a shipped fix. `quality-gates.sh` green (2595 pytest + 230 vitest) before push. A concurrent push moved LDR
      forward mid-resolution (rejected the first push attempt); re-applied the identical, already-verified resolution
      against the new tip and pushed clean. Evidence: agent-orchestrator@5872b3e5 (merge commit, parents = LDR tip
      `42cba859` + main tip `38ef77e`). Verified: PR #791 shows `state: MERGED`; `compare/main...live-defi-rollout` now
      reads `ahead_by: 834, behind_by: 0` (main fully absorbed into LDR). Did not chase a separate, unrelated
      `main-backmerge-to-ldr.yml` failure observed against a `wip-preserve/orchestrator-slot-10-*` ref shortly after —
      different failure class (wip-preserve branch mistrigger, not a main↔LDR content conflict), out of this todo's
      scope. The stale PR #816 (built from LDR's pre-fix tip) should self-clear via the fleet bot's normal per-SHA
      promote churn now that main and LDR are reconciled — not manually intervened on. (repo: agent-orchestrator)
- [x] [DATA] P3. **Re-verified operator-blocked-question → backlog-status transition against CURRENT code — answer
      differs by WHICH kind of "blocked" is meant; both confirmed by reading the live diffs, not reasoning from stale
      pre-2026-08-06 behavior.** There are two distinct mechanisms:

      1. **`[OPERATOR]`-gated task (the synthetic `BLK-op-<task_id>` sentinel, no worker ever dispatched to it)**:
                         created directly as backlog `TaskRow.status="blocked"` (`routes/backlog.py:658`,
                         `new_status = "blocked" if new_task.operator_gated else "queued"`) — it never passes through queued/dispatched
                         first. Answering it with a structured ruling does NOT flip that same row's status at all: `regen`'s
                         `_materialize_operator_ruling_tasks` (`regen_backlog_from_plan.py:2662`) creates a brand-NEW, independent
                         sibling task `<task_id>--ruling` on the next tick, `operator_gated=False` → fresh `status="queued"` — an
                         ordinary dispatchable task ANY available worker can claim. The original task's own row just sits `"blocked"`
                         until the worker's plan-doc edit removes its brief, at which point both tasks become ordinary orphans
                         together (`_is_live_ruling_task`). **Agent/slot respawn is a non-issue here by construction** — the new task
                         was never tied to any specific slot or agent_id in the first place.
                      2. **A live worker's own in-flight blocked question** (`authority="operator"` on a REAL dispatched task, a
                         genuinely different code path — `answer_blocked_endpoint`, not the ruling path): the TASK stays
                         `"dispatched"` the whole time; it's the **SLOT** that flips `status: "blocked" → "working"` on answer
                         (`routes/backlog.py` — `if slot is not None and slot.status == "blocked": slot.status = "working"`), and the
                         answer is delivered as a queued `SlotMessageRow` keyed by `slot_id`. **Respawn DOES matter here, and there was
                         a real, just-fixed bug in exactly this spot**: `365e18e` (2026-08-06T18:37, THIS SAME DAY —
                         `ao_blocked_answer_message_cross_delivered_after_slot_reassign_2026_08_06`) — if the slot got force-reassigned
                         to a genuinely different task between the question and the answer, the old session-scoping (protects only a
                         respawn of the SAME dispatch) did nothing, so the answer could silently deliver into the wrong, unrelated
                         task. Fix (shipped, live): `SlotMessageRow` now carries an optional `task_id` stamped from
                         `BlockedRow.task_id` at enqueue time; `take_pending_messages` now requires the slot's CURRENT task to still
                         match before delivering, and **orphans** (never delivers, logs `blocked_message_orphaned_by_reassign`) a
                         message whose task no longer matches, instead of misdelivering it. `c290bc5`/`18444f5` (last_ping stamp +
                         tmux nudge) and `cc5961e` (authority-field wiring) are orthogonal reliability/plumbing fixes in the same
                         area, not additional status-transition changes. (repo: agent-orchestrator)

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
- **2026-08-07 (continuation session)**: Closed all 4 remaining follow-ups. (1) Billing `spend_usd: null` — root-caused
  (Anthropic/Claude has no price-table entry, poisoning any window containing a Claude task by the existing
  never-partial-sum rule) and fixed as a UI/labeling gap: added `unpriced_row_count` end-to-end
  (`agent-orchestrator@ff12b96`, full quality-gates.sh green). (2) Slot 4/5/6 "kills" — re-ran the corrected
  `/api/activity` query (top-level `slot_id`/`ts`/`event_type`, server-side `since`/`until`/`exclude` filters); found
  zero `watchdog_slot_killed` events in the claimed window for any of the 3 slots — every apparent death was routine
  `tmux_session_lost`-then-`autospawn_succeeded` self-heal within 1-3 minutes. Not a bug; closed with no code change.
  (3) PR #813 — investigated deeper than expected and found a genuine, still-open, worsening CI wedge:
  agent-orchestrator's main↔LDR backmerge PR #791 has sat conflicted, untouched, and un-commented for 24h+, blocking
  every LDR→main promote PR from ever getting a `quality-gates-v2` run. Filed as a new `[INFRA] P1` remediation todo
  (not resolved here — real conflict-resolution judgment work). (4) Operator-blocked-question status transition —
  re-verified against the 5 live commits: two distinct mechanisms exist ([OPERATOR]-gated sentinel materializes an
  independent fresh-queued sibling task, agent/slot respawn irrelevant by construction; a live worker's own blocked
  question flips SLOT status and delivers via a `SlotMessageRow`, where respawn previously WAS a real bug — `365e18e`,
  shipped the same day, now scopes delivery to the message's stamped `task_id` and orphans a stale cross-task message
  instead of misdelivering it).
- **context-scout 2026-08-07**: populated/refreshed context_scope (4 entries) — the doc's fleet-health investigations
  are all closed; the sole remaining open item (`[INFRA] P1`, resolve PR #791) is pure cross-repo CI/backmerge-conflict
  work, so the list covers the workflow whose behavior is central, the CI/CD SSOT, and the archived doc describing the
  `escalate-to-orchestrator` dispatch mechanism this todo says to check first. **Step-4a fingerprint match, confirmed**:
  `agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md` (same date, same repo) independently
  investigates the SAME `agent-orchestrator` PR #813 and finds it is ALSO blocked by a dangling PM-workflow reference
  AND a genuine unrelated 7-file code conflict vs `live-defi-rollout` — complementary root-cause info neither doc
  currently cross-references (this doc attributes the stall to PR #791/backmerge never landing; that doc shows #813 has
  independent blockers on top). Added here; the reverse direction is being added to that doc's own `context_scope` too.
- **2026-08-07 (resolution)**: Resolved PR #791's conflict — see this doc's own PR #791 todo above for the full evidence
  chain (12 files, LDR-supersedes-main pattern confirmed per-file, one real auto-merge regression caught + stripped in
  `main_agent_keeper.py`). `quality-gates.sh` green before push (2595 pytest + 230 vitest); pushed as
  `agent-orchestrator@5872b3e5` after a concurrent push moved LDR mid-resolution (re-applied the identical, verified
  resolution against the new tip). PR #791 confirmed `state: MERGED`; `compare/main...live-defi-rollout` reads
  `ahead_by: 834, behind_by: 0`. Following the `agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md`
  cross-reference surfaced a SECOND, independent blocker on the same pipeline (agent-orchestrator@main's own CI workflow
  files still pointed at the deleted `unified-trading-pm` reusable workflows) — fixed that too via PR #817
  (`fix/repoint-main-ci-to-unified-trading-ci`), tracked in that doc's own todos, not duplicated here. ALL 4 of this
  doc's own follow-ups are now closed; archiving.
