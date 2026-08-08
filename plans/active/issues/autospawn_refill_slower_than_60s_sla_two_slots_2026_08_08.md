---
doc_type: issue
title: "AutoSpawn refill observed slower than documented ~60s SLA — 2 data points, one slot idle 38+ min"
summary: >-
  Review-flagged, main-verified (2026-08-08 ~11:22Z): slot 11 completed task f722906f3 cleanly at 10:42:44
  (slot_done_verified=true), correctly went through the designed one-task-per-session reset
  (worker_one_task_per_session_reset, next_task_id staged as sports_taxonomy_p1_capture_and_contracts-014), old tmux
  torn down at 10:44:15 — then had ZERO respawn activity for 38+ minutes (still status=killed, worker_alive=false,
  tmux_alive=false as of 11:23Z verification) despite a specific claimable next_task sitting unclaimed and 166 claimable
  backlog tasks overall (not a demand problem). Separately, slot 10's context-saturation reap at 10:48:25 took 33
  minutes to self-heal (autospawn_succeeded 11:21:29), well past the ~60s figure in worker.md. Both eventually
  self-healed / are expected to (slot 10 confirmed recovered; slot 11 still pending at filing time) — bounded blast
  radius (idle capacity, not lost work), but a real, measurable SLA gap worth root-causing given AutoSpawn is the
  fleet's core self-healing mechanism.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, autospawn, sla, worker-liveness, capacity, one-shot-reset]
related:
  [
    /plans/archive/issues/orchestrator_ready_p1_task_undispatched_no_matching_worker_autospawn_gap_2026_07_25.md,
    /plans/active/issues/one_shot_complete_session_ownership_desync_2026_08_08.md,
    /plans/active/issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md,
  ]
created: 2026-08-08
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P3
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
locked_by:
source:
  "review (agent-orchestrator loop tick, msg 4091, ~2026-08-08T11:22Z); main independently verified via /api/state read"
---

# AutoSpawn refill slower than documented ~60s SLA — two data points

## Evidence

- **Slot 11**: finished task `f722906f3` cleanly at `10:42:44` (`slot_done_verified=true`), went through the designed
  one-task-per-session reset (`worker_one_task_per_session_reset`,
  `next_task_id=sports_taxonomy_p1_capture_and_contracts-014` staged), old tmux torn down at `10:44:15`. Main
  independently confirmed via `/api/state` at `~11:23Z`: still `status=killed`, `current_task=null`,
  `worker_alive=false`, `tmux_alive=false`, `last_ping=10:42:44` — i.e. ~38+ minutes with zero respawn activity and a
  specific claimable next-task sitting unclaimed. This is the designed reset-and-handoff path, not a crash — there is
  nothing to "recover", just a fresh spawn that never happened in the expected window.
- **Slot 10**: context-saturation reap fired at `10:48:25`; main independently confirmed via `/api/state` it had
  self-healed by `11:22Z` (`status=working`, `last_spawned_at=11:21:29`, resumed
  `sports_taxonomy_p1_capture_and_contracts-008`) — a 33-minute gap, well past the ~60s SLA figure documented in
  `worker.md`.
- Backlog had 166 claimable tasks at the time on both counts — ruled out as a demand-side (no-work-to-assign) cause.

## Not yet established

Only two data points; root cause not chased. Open question (per review, unconfirmed): whether AutoSpawn processes the
idle-slot queue serially with a slow per-slot cadence rather than in parallel, or something else entirely (e.g. an
account/quota headroom gate, a scheduling-lock contention, or a startup-cost outlier). No live-trading or data-loss
impact — both are self-healing idle-capacity gaps, not silent failures.

## Todos

- [ ] [BACKEND] P3. Root-cause why AutoSpawn refill exceeded the documented ~60s SLA in these two cases (33min and
      38+min). Check AutoSpawn's own scheduling/concurrency logic — specifically whether idle slots are refilled
      serially with a slow per-slot cadence vs. in parallel — and check for any account/quota-headroom gating that could
      explain the delay. Confirm whether slot 11 has since respawned (if still stuck at investigation time, treat as a
      third live data point, not just historical). Done-when: either a confirmed root cause + fix, or a decision that
      current behavior degrades within an acceptable bound with evidence from a larger sample (10+ observed refills)
      showing this was not representative.
