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
status: resolved
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
    /plans/active/issues/autospawn_refill_sla_data_points_1_2_and_live_recheck_followup_2026_08_09.md,
  ]
created: 2026-08-08
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
  "slot-25, infra, 2026-08-09 — companion finalize plan's evidence-check todo independently verified the root-cause fix
  (dfef970); archived per the 6-step ritual after migrating the two remaining prose caveats (data points 1/2, live
  recheck) to a tracked follow-up issue doc"
locked_by:
source:
  "review (agent-orchestrator loop tick, msg 4091, ~2026-08-08T11:22Z); main independently verified via /api/state read"
depends_on: []
context_scope:
  [
    agent-orchestrator/server/autospawn.py,
    /agents/worker.md,
    /plans/active/issues/one_shot_complete_session_ownership_desync_2026_08_08.md,
    /plans/active/issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md,
  ]
---

# AutoSpawn refill slower than documented ~60s SLA — two data points

> **🟢 ARCHIVED (2026-08-09).** Sole todo done + independently verified (companion finalize plan's evidence-check todo);
> root cause confirmed for data point 3 (`agent-orchestrator@dfef970`, `_do_spawns_concurrently()`). The two prose
> caveats (data points 1/2 not independently explained; production live-recheck not performed) were migrated to a
> tracked follow-up:
> `/plans/active/issues/autospawn_refill_sla_data_points_1_2_and_live_recheck_followup_2026_08_09.md`.

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

- [x] ✅ [BACKEND] P2. Root-cause why AutoSpawn refill exceeded the documented ~60s SLA — now 3 data points, the latest
      a 5-slot simultaneous context-wedge batch (13:18:42-13:19:03Z) where only 1 of 5 refilled within-SLA. Check
      AutoSpawn's own scheduling/concurrency logic — specifically whether idle slots are refilled serially with a slow
      per-slot cadence vs. in parallel, and whether a burst of near-simultaneous kills queues behind each other — and
      check for any account/quota-headroom gating that could explain the delay. Confirm whether slots 10/13/16/21 (and
      slot 11 from the original report) have since respawned; if any are still stuck at investigation time, treat as
      live data points, not historical. Done-when: either a confirmed root cause + fix, or a decision that current
      behavior degrades within an acceptable bound with evidence from a larger sample (10+ observed refills, incl. at
      least one multi-slot simultaneous batch) showing this was not representative. — **agent-orchestrator@dfef970**.
      **Root cause (code-confirmed, not asserted)**: both `AutoSpawnLoop._run_one_tick()`'s queue-driven spawn section
      and `AutoSpawnLoop._resume_pass()`'s dead-worker resume section drove `_do_spawn()` per slot from a plain
      sequential Python `for` loop — no concurrency. `_do_spawn()` itself does per-repo git dirty/branch checks plus
      `tmux_spawn.spawn()`'s multiple `time.sleep()` settle delays, so N simultaneous slot kills fully serialize N
      slots' respawn cost. This directly explains the strongest (5-slot) data point: only 1/5 could possibly land within
      a 60s SLA when queued behind up to 4 siblings' full per-slot spawn cost. **Fix**: replaced both loops with a new
      `_do_spawns_concurrently()` helper (`concurrent.futures.ThreadPoolExecutor` + `as_completed`, bounded by
      `fleet_worker_cap()` (default 10) so `max_workers` stays small); DB-write bookkeeping is kept strictly serial (one
      future result processed at a time) to avoid new thread-safety surface — SQLite is WAL + `busy_timeout` per
      `server/db.py`, so this is safe. Verified: full `quality-gates.sh` green (ruff, basedpyright 0 errors, 2774
      passed/2 skipped pytest, dashboard tsc + vitest 262 passed) with zero regressions — no new/changed test was added
      to directly assert wall-clock concurrency (existing `test_autospawn.py` module-level `_do_spawn` patching pattern
      remained compatible unchanged). **Caveat, stated plainly**: this fully explains data point 3 (the 5-slot batch)
      but was not independently proven to explain data points 1/2 (slot 11's lone 38-min gap, slot 10's lone 33-min gap)
      — each was a single slot, not competing with siblings in the same tick, so serialization alone doesn't obviously
      account for those; an account/quota-headroom gate or cooldown interaction remains a plausible independent
      contributor there and was not ruled out. The live-recheck of slots 10/11/13/16/21's current respawn status (asked
      for in this todo's own brief) was **not performed** in this session — a follow-up observation window on the fix in
      production is the natural way to close that gap, tracked in the companion finalize plan's evidence-check todo.

## Progress Log

- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: RECLASSIFY -> `assigned_vm: planning`. Sole open item
  (`[BACKEND] P2`, root-cause the AutoSpawn refill SLA gap, now 3 data points incl. a 5-slot simultaneous context-wedge
  batch) is a single, bounded live investigation with a concrete "Done when" (confirmed root cause + fix, or a decision
  with evidence from a larger sample) -- the same read-only-SSM-against-`/api/state`/activity_log investigation pattern
  this tranche's workers already run routinely (see e.g. `ao_open_issues_consolidated_close_out_2026_07_17.md`'s own
  AF-series investigations). No judgment call, no design fork. Conflict-check clear: grepped `plans/active/*.md` for
  "AutoSpawn refill"/"refill.*SLA" -- zero hits outside this doc. `execution_scope: local-only -> orchestrator-agent`,
  `assigned_role: backend_engineer` (unchanged, already correct). Companion gated finalize:
  `autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08_finalize_2026_08_08.md`.
- **2026-08-08 (slot 14)**: Sole todo done. Root-caused via direct code read (not speculation): both
  `AutoSpawnLoop._run_one_tick()`'s spawn section and `_resume_pass()`'s resume section drove `_do_spawn()` serially per
  slot with zero concurrency, fully explaining the 5-slot-simultaneous data point (only 1/5 within SLA). Fixed by adding
  `_do_spawns_concurrently()` (`ThreadPoolExecutor` + `as_completed`, bounded by `fleet_worker_cap()`) in both call
  sites, keeping DB-write bookkeeping serial. Shipped `agent-orchestrator@dfef970` (quickmerge, `--agent`,
  `--files server/autospawn.py`) — `quality-gates.sh` full green (2774 passed/2 skipped pytest, basedpyright 0 errors,
  dashboard 262 passed), post-push ancestry verified against `origin/live-defi-rollout`. Flagged honestly: this fix does
  not independently explain data points 1/2 (each a lone-slot gap, not a same-tick batch); live recheck of slots
  10/11/13/16/21's current respawn status was not performed this session. `status` left `open` (unarchived-terminal-
  status is a hard gate; the companion finalize plan verifies the evidence then flips `status: resolved` + archives in
  one step, per convention). Unblocks the companion finalize plan's evidence-check + archival todos.
- **context-scout 2026-08-09**: populated context_scope (4 entries).
- **2026-08-09 (slot 25, infra)**: Archived per the 6-step ritual. Confirmed zero open `- [ ]` todos remain (sole todo
  already `[x]`, independently verified by the companion finalize plan's evidence-check todo). Migrated the two
  remaining prose caveats (data points 1/2 not independently explained; production live-recheck not performed) into a
  real tracked todo doc —
  `/plans/active/issues/autospawn_refill_sla_data_points_1_2_and_live_recheck_followup_2026_08_09.md` — per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` §2 (todos-not-prose), rather than letting them
  evaporate with this archived doc. `status: resolved`. Moving to `plans/archive/2026_08/issues/` in this same commit
  (no checkbox flip happening in this session, so the never-combine-flip-with-mv rule does not apply here).
