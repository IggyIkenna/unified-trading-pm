---
doc_type: issue
title: WorkerLivenessWatchdog's unpushed-commits sweep auto-pushes commits held pending an open /blocked sign-off gate
summary: >-
  `_sweep_unpushed_slots` (worker_liveness_watchdog.py) reclaims and pushes ANY committed-but-unpushed HEAD left behind
  by a dead/reaped slot session, with zero awareness of an open task-linked `/blocked` question acting as a deliberate
  merge-time HOLD. This let a genuinely operator-sign-off-gated commit pair reach `live-defi-rollout` without the
  ratification its own guardrail required, purely because the holding session froze and was reaped before the operator
  answered.
status: superseded
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, watchdog, tooling-gap, governance, blocked-questions, worker-lifecycle]
related:
  [
    /plans/active/issues/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/active/issues/watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md,
  ]
created: 2026-07-26
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
drift_direction: worsening-slowly
depends_on: []
source:
  [
    "Found 2026-07-26 (slot-7, data_engineering) while picking up sports_satellite_ao_dispatch_batch5-026 -- the
    concurrent uac@b95012ed/features-service@0f90702e commits it had been holding pending BLK-ec018203's sign-off were
    already on live-defi-rollout (rebased as uac@5b57f6d2/features-service@332ea5d5) by the time this fresh session
    booted.",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by: watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26
---

> **SUPERSEDED 2026-07-26** — main-agent independently root-caused the same gap moments after this doc was filed and
> landed the canonical version first:
> `/plans/active/issues/watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md` (also answers `BLK-eccd3383`
> below with `disposition:partial` — Option A declined, operator paged with a revert recommendation). Kept here only for
> the investigation timeline; track the fix + `BLK-ec018203`/`BLK-eccd3383` disposition in the superseding doc.

# WorkerLivenessWatchdog's unpushed-commits sweep bypasses an open /blocked sign-off gate

## What I found

### Timeline (all times UTC, 2026-07-26, task `sports_satellite_ao_dispatch_batch5-026`)

1. **08:39:08** — slot-7 filed `BLK-ec018203`: "both repos QG-green, requesting the explicit operator sign-off the
   design doc's guardrail requires before quickmerge" (the guardrail in
   `sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`'s `[DESIGN] P1` explicitly reserves
   merge-time diff sign-off to the operator, separate from the direction decision).
2. **08:39:46** — slot-7 `/progress`: "local commits not yet pushed... Waiting."
3. **08:41:08** — `blocked_partial_answer`: **"C (HOLD) — interim, escalating upward. Do NOT quickmerge yet."** This is
   the only answer `BLK-ec018203` ever received — it is still one of the 12 entries in `/api/blocked/stats`'
   `unanswered` count as of this writing. No `blocked_answered` event for `BLK-ec018203` exists anywhere in
   `/api/activity`.
4. **08:43:05 – 09:13:30** — repeated `frozen_at_high_context` events (context_pct 70, one every ~45-75s) and several
   `worker_kicked` nudges ("check on it", "proceed now", "check on BLK-ec018203") — the holding session was wedged, not
   actively waiting.
5. **09:13:30** — `worker_polling_dead` / `slot_idle_stale` (silence 316s past the 300s threshold) — the
   WorkerLivenessWatchdog reclaimed the session as dead.
6. **09:19:21 / 09:18:53** — `slot_unpushed_commits_reclaimed`, `trigger: "watchdog_sweep"`, `pushed: true` for BOTH
   repos. This is `_sweep_unpushed_slots` (`worker_liveness_watchdog.py:1463-1542`) doing exactly what its docstring
   says: "Periodic reclaim-and-push sweep for a killed/idle slot whose worktree holds committed-but-unpushed work" —
   `push_or_preserve_ahead_commits` pushed the two locally-committed-but-unpushed HEADs straight to `live-defi-rollout`.
   Same content as `b95012ed`/`0f90702e`, rebased onto a newer LDR tip (now `5b57f6d2` / `332ea5d5`).

### The gap

`_sweep_unpushed_slots` iterates every slot whose tmux session is dead/gone and, for a clean-but-ahead-of-origin
worktree, unconditionally pushes. It has **no check for whether the task currently attached to that slot has an open,
unanswered `/blocked` entry that is specifically gating THIS merge** — the mechanism was built purely to stop a
predecessor's committed work from being silently lost (a legitimate, narrow goal per its own docstring, referencing
`ao_remediation_b_code_chain` item 9), and correctly doesn't special-case "ordinary" WIP. But some commits are not
"ordinary WIP sitting unpushed because nobody got around to it" — they are **deliberately held** pending an
operator-only ratification gate, and the holding agent's own `/blocked` question is right there in the same DB the
watchdog already queries every tick. The sweep currently cannot distinguish the two cases, so the safety net for one
failure mode (losing committed work) directly causes a different, more serious one (bypassing a designed human-sign-off
gate) whenever the holding session dies mid-wait — which is exactly the scenario a long HOLD is most likely to produce
(a frozen/high-context session sitting idle for tens of minutes is a much higher-risk window for the liveness watchdog
to reap than a session actively mid-edit).

## Why it matters

The specific instance here was assessed content-wise as "complete and correct" by main-agent's interim answer, so the
actual risk that materialized this time is low — but the MECHANISM defeats a governance control that exists specifically
because a class of change (cross-repo, leakage-safety-adjacent) is deemed too risky for a worker to self-approve. The
next occurrence might not be as benign, and the sweep gives no signal that it happened outside its own terse
activity-log line — nobody would notice unless they went looking (as this session did only because the same task got
re-dispatched and the investigator happened to check git history against the stale plan text).

## Recommended decision

- [ ] [BACKEND] P1. In `agent-orchestrator/server/worker_liveness_watchdog.py`'s `_sweep_unpushed_slots` (~line
      1502-1542), before calling `push_or_preserve_ahead_commits` for a given slot, query for any
      `status="open"`/unanswered `BlockedQuestion` row whose `task_id` matches that slot's current/last task. If one
      exists, **do not auto-push** — fall through to `push_or_preserve_ahead_commits`'s existing "preserve" path (stash
      or leave-committed-unpushed, whichever it already does for the non-push case) instead, and log a distinct activity
      event (e.g. `slot_unpushed_commits_held_open_blocker`) so this is visible rather than silently indistinguishable
      from a normal reclaim. Add a regression test mirroring `tests/test_watchdog_unpushed_sweep.py`'s existing pattern:
      a slot with an open BLK tied to its task must NOT get `slot_unpushed_commits_reclaimed`. (repo:
      agent-orchestrator)
- [ ] [OPERATOR] P2. Decide the disposition of `BLK-ec018203` / `BLK-eccd3383` (the CLV odds_targets merge that already
      landed on `live-defi-rollout` via this gap) — ratify after-the-fact or revert before the next LDR→main promote
      cycle. Tracked in `sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md` and
      `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s item (c); not duplicated here.

## Progress Log (append-only)

- 2026-07-26 (slot-7, `data_engineering`): filed while investigating why `sports_satellite_ao_dispatch_batch5-026`'s (c)
  sub-item read as still-blocked in the plan text but the commits it referenced were already on
  `origin/live-defi-rollout` — traced via `/api/activity` + git log/reflog per the timeline above. Filed `BLK-eccd3383`
  for the operator-ratification decision; this doc covers only the tooling-gap fix.
