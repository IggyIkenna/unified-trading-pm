---
doc_type: plan
title: AO fleet throughput collapse — quarantine-refill + dormant-slot audit
summary: >-
  Live incident 2026-07-25: fleet dropped from ~12 active slots earlier today to 4 (out of 15 capacity) despite 25
  genuinely queued/dispatchable backlog tasks and zero backlog-level blocking — this is NOT a backlog-starvation
  problem. Confirmed via read-only SSM telemetry pull that AutoSpawn's branch-state quarantine
  (`_MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN` in worktree_clean_check/_branch_state.py, FM5/FM7) refused to refill
  slots 4, 5, 9 within the last ~10 minutes of the pull, each citing a recent-commit age just under its cooldown — a
  KNOWN, already-alerted mechanism (`notify_slot_quarantined` in autospawn.py) whose starvation alert needs verifying it
  actually fired for this exact episode. Separately, slots 13/14/15/0 show ZERO AutoSpawn activity for 378min-27168min
  despite tmux_alive=false — an unexplained dormancy distinct from the quarantine mechanism. Complements
  ao_worker_context_lifecycle_gap_2026_07_25.md (context-saturation crashes are ONE trigger of the session deaths behind
  this, not the only one — this plan is the fleet-capacity-refill side, that plan is the context-root-cause side;
  independent file surfaces, dispatch concurrently).
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, autospawn, incident, fleet-capacity, branch-quarantine, observability]
related: [/plans/active/ao_worker_context_lifecycle_gap_2026_07_25.md, /plans/epics/orchestrator_master.md]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Operator observation 2026-07-25 (dashboard screenshot: 15 slots, only 4 working, slot #9 KILLED, most others idle
  despite a claimed 33-task backlog) — "seems like we have 4 slots showing anything despite capacity for 15, backlog of
  33 tasks and we had at least earlier today up to 12 slots in action." Diagnosed live via read-only SSM pulls against
  the orchestrator VM (i-0c9b283b31d6b5ca7): GET /api/state (all 17 slot rows), GET /api/backlog (142 tasks: 6
  dispatched, 25 queued with blocked_reason=null on every one, 109 done, 2 cancelled — BLOCKED_COUNT=0), GET
  /api/activity (2000-row window 2026-07-24T21:42-2026-07-25T04:43 UTC: 27 tmux_session_lost, 51 orphan_process_reaped,
  3 autospawn_failed all citing "branch-state quarantine (FM5/FM7)").
assigned_role: infra
drift_direction: advance-code
sequential: true
---

# AO fleet throughput collapse — quarantine-refill + dormant-slot audit

> **Why `sequential: true`**: all 3 todos below plausibly touch `server/autospawn.py` (todo 1 verifies/fixes its
> existing alert path; todo 2 audits/fixes its spawn-target logic; todo 3 re-reads its live behavior) — same-file risk
> across concurrent workers, serialize instead of splitting further for a 3-todo plan.
>
> **Live baseline this plan is diagnosing against** (2026-07-25T04:43 UTC snapshot, cite in every todo's evidence):
> slots working=5 (#2 95% ctx, #3 100% ctx, #6 5%, #7 44%, #11 0%/thrashing), idle=6 (#4,5,10,13,14,15), killed=1 (#9),
> stale=1 (#12), paused=2 (#0,#16). `autospawn_failed` fired for slots 4 (04:35:04), 5 (04:36:40), 9 (04:42:45), all
> `"branch-state quarantine (FM5/FM7), auto-heal failed: ... N-commit(s)-too-recent(4XXs-old)-REFUSED-kept-quarantined"`.
> Slots 13/14/15/0 have zero `autospawn_succeeded`/`autospawn_failed` events anywhere in the returned 2000-row/~7h
> activity window despite `tmux_alive: false`, with `last_ping` 378min/4327min/4323min/27168min stale respectively.

## Todos

- [ ] [INFRA] P0. **Verify the branch-quarantine starvation alert actually fired for this episode, fix if not.**
      `_alert_branch_quarantine` (`server/autospawn.py:1112-1160`) is designed to page via `notify_slot_quarantined`
      specifically when a slot sits quarantined WHILE queued work exists ("walls queued → this quarantine is starving
      dispatch → error-pointer page", `autospawn.py:1140`) — exactly the condition observed at 2026-07-25T04:35-04:43
      UTC (slots 4/5/9 quarantined, 25 tasks genuinely `queued`). Check the alerting-service / Slack `ci-failures` or
      `agent-orchestrator-alerts` channel history for a `notify_slot_quarantined` page in that window; also check
      `dedup_state.escalation_branch_quarantine_path()`'s persisted dedup state to see if a PRIOR still-active dedup
      entry silently suppressed this episode's alert (the dedup exists to stop re-paging a still-quarantined slot across
      a central-VM restart — confirm it isn't ALSO suppressing a genuinely NEW starvation episode on the same slot). If
      the alert did not fire when it should have, fix the gap (either the dedup logic or the "walls queued" condition
      check) with a regression test. **Done when**: either a cited Slack message ID / activity-log entry proving the
      alert fired correctly for slots 4/5/9's 2026-07-25 quarantine, or a fix + a new test in `tests/` reproducing this
      exact scenario (quarantined slot + nonzero queued count → alert fires).
- [ ] [INFRA] P0. **Audit why slots 13, 14, 15, and 0 show zero AutoSpawn activity across the entire observed window**
      despite `tmux_alive: false`. Read `AutoSpawnLoop`'s spawn-candidate selection (`server/autospawn.py`, the
      `_should_spawn` method and whatever iterates slot candidates each tick) to determine: (a) does AutoSpawn target
      only a concurrency CAP below the full slot count (e.g. spawns onto the first N free slots per tick and never
      reaches the rest), (b) is there a per-slot cooldown/backoff counter that can get stuck indefinitely after repeated
      failures, or (c) something else entirely. This is a bounded fact-finding audit, not a judgment call — the
      determinable question is "which of (a)/(b)/(c), cite the exact code." Only implement a fix if the cause is a
      genuine bug (e.g. a stuck backoff counter, an off-by-one in candidate selection); if it's an intentional
      concurrency cap working as designed, state that finding plainly instead — do not invent a fix for intended
      behavior. **Done when**: a written finding citing the exact function/branch responsible for slots 13/14/15/0's
      dormancy, plus (only if a bug) a fix with a regression test that a long-dormant free slot gets an AutoSpawn
      attempt within one normal tick interval.
- [ ] [REVIEW] P1. **Post-fix live re-verification against the same baseline.** Re-run the same read-only telemetry pull
      this plan's `source` field describes (`GET /api/state`, `GET /api/backlog`, `GET /api/activity` via the read-only
      SSM pattern in `agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh` — READ-ONLY, do not restart or
      mutate anything on the VM) against the live orchestrator VM (`i-0c9b283b31d6b5ca7`, `ap-northeast-1`) after todos
      1-2 ship and reach production. Confirm: (a) the active-slot fraction has recovered toward the ~12/15 baseline the
      operator observed earlier on 2026-07-25 (or state plainly if it hasn't, with the new blocking cause), (b) slots
      13/14/15/0 either now show fresh AutoSpawn attempts or the audit's "intended cap" finding is confirmed still
      correct, (c) a fresh branch-quarantine episode (if one occurs naturally, or induced in a test env) produces a
      verified alert. **Done when**: a written verification note citing the actual re-pulled slot/activity data,
      attached to this plan's Progress Log.
