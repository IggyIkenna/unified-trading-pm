---
doc_type: issue
title: "AutoSpawn refill observed slower than documented ~60s SLA — now 3 data points incl. a 5-slot simultaneous batch"
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
  fleet's core self-healing mechanism. **2026-08-08 ~13:22Z update (main, independently root-caused a review-flagged
  "tmux_session_lost" batch, msg 4196)**: 5 slots (3/10/13/16/21) hit `auto-respawn: reason=context-wedged` (97-100%
  context, /compact could not run) within a 21s window (13:18:42-13:19:03) — NOT a restart-cascade or OOM/cgroup issue
  (ruled out: resource-watchdog showed pressure=normal/cgroup_mem 10-13GB throughout, well under caps). Only slot 3
  recovered promptly (~2min); slots 10/13/16/21 were still status=killed/worker_alive=false 4-5min later at check time —
  strengthens the "serial refill, slow per-slot cadence" hypothesis below, since only 1 of 5 simultaneous kills refilled
  within-SLA. Priority raised P3->P2 given the larger simultaneous blast radius.
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
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
locked_by:
source:
  "review (agent-orchestrator loop tick, msg 4091, ~2026-08-08T11:22Z); main independently verified via /api/state read"
depends_on: []
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
- **Third data point, 2026-08-08 ~13:22Z (5-slot simultaneous batch)**: review flagged a cluster of `tmux_session_lost`
  events across slots 21/16/13/10/3 (detected together at `13:19:29`, `last_ping` clustered `13:17:44-13:18:11Z`) plus a
  distinct slot 7 case at `13:20:29`, and hypothesized collateral damage from the `13:10:48Z` orchestrator restart. Main
  independently root-caused via `journalctl -u orchestrator.service` on the host: the real trigger was AO's own
  context-wedge auto-respawn firing on 5 slots nearly simultaneously —
  `auto-respawn: slot=3 reason=context-wedged at 97%` (13:18:42), `slot=10 ... 100%` (13:19:02), `slot=13 ... 100%`
  (13:19:02), `slot=16 ... 100%` (13:19:02), `slot=21 ... 99%` (13:19:03) — all "/compact could not run (session over
  the model's hard limit); killed + fresh respawn". `TmuxPruner cleared 5 stale tmux_session reference(s)` at `13:19:29`
  is just the cleanup pass over these same 5 kills, not an independent event. Ruled out restart-collateral:
  `resource- watchdog` showed `pressure=normal cgroup_mem=10-13GB` continuously through the window, well under the
  23G/26G caps — no OOM, no cgroup teardown. Recovery was uneven: slot 3 respawned within ~2min (`13:20:40`); slots
  10/13/16/21 were still `status=killed`/`worker_alive=false` as of `13:22:52Z` — 4-5 minutes past detection, well past
  the ~60s SLA, and a stronger signal than the prior 2 data points that refill may be serialized rather than parallel
  when multiple slots need respawning at once.

## Not yet established

Only two data points; root cause not chased. Open question (per review, unconfirmed): whether AutoSpawn processes the
idle-slot queue serially with a slow per-slot cadence rather than in parallel, or something else entirely (e.g. an
account/quota headroom gate, a scheduling-lock contention, or a startup-cost outlier). No live-trading or data-loss
impact — both are self-healing idle-capacity gaps, not silent failures.

## Todos

- [ ] [BACKEND] P2. Root-cause why AutoSpawn refill exceeded the documented ~60s SLA — now 3 data points, the latest a
      5-slot simultaneous context-wedge batch (13:18:42-13:19:03Z) where only 1 of 5 refilled within-SLA. Check
      AutoSpawn's own scheduling/concurrency logic — specifically whether idle slots are refilled serially with a slow
      per-slot cadence vs. in parallel, and whether a burst of near-simultaneous kills queues behind each other — and
      check for any account/quota-headroom gating that could explain the delay. Confirm whether slots 10/13/16/21 (and
      slot 11 from the original report) have since respawned; if any are still stuck at investigation time, treat as
      live data points, not historical. Done-when: either a confirmed root cause + fix, or a decision that current
      behavior degrades within an acceptable bound with evidence from a larger sample (10+ observed refills, incl. at
      least one multi-slot simultaneous batch) showing this was not representative.

## Progress Log

- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: RECLASSIFY -> `assigned_vm: planning`. Sole open
  item (`[BACKEND] P2`, root-cause the AutoSpawn refill SLA gap, now 3 data points incl. a 5-slot simultaneous
  context-wedge batch) is a single, bounded live investigation with a concrete "Done when" (confirmed root cause +
  fix, or a decision with evidence from a larger sample) -- the same read-only-SSM-against-`/api/state`/activity_log
  investigation pattern this tranche's workers already run routinely (see e.g.
  `ao_open_issues_consolidated_close_out_2026_07_17.md`'s own AF-series investigations). No judgment call, no
  design fork. Conflict-check clear: grepped `plans/active/*.md` for "AutoSpawn refill"/"refill.*SLA" -- zero hits
  outside this doc. `execution_scope: local-only -> orchestrator-agent`, `assigned_role: backend_engineer`
  (unchanged, already correct). Companion gated finalize:
  `autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08_finalize_2026_08_08.md`.
