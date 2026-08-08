---
doc_type: issue
title:
  Slot 1 (review role) crash-looping via unexplained TmuxPruner kills, ~20 of 22 in 2h with no context_recycle_requested
summary: >-
  Review-craft investigation (2026-08-08, ~14:30-16:30Z window) found slot 1's `agentkeeper_review_succeeded` events
  paired almost 1:1 with `tmux_session_lost` (TmuxPruner-attributed, externally-killed) — 22 pairs in ~2h — but only 2
  of the 22 deaths were preceded by a genuine `context_recycle_requested` event. The other ~20 are unexplained kills,
  not voluntary RECYCLE exits, meaning review continuity is fragmenting into many short-lived (1-6 min) sessions and
  burning real spawn overhead continuously. Checked against the 3 event types behind the previously-tracked fleet-wide
  post-spawn wedge pattern (`forced_compact_ineffective`, `slot_wedged_killed_for_resume`, `worker_kick_failed`) — zero
  hits for slot 1 on any of the 3, so this looks like a different mechanism, though a shared deeper root cause (e.g.
  host-level contention, per prior review/main joint findings on the tardis wedge cluster) cannot be ruled out without
  reading TmuxPruner/keeper source directly.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, tmux, review-role, crash-loop, live-incident, spawn-overhead]
related:
  - /plans/active/issues/review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md
  - /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md
created: 2026-08-08
author: agt-22de53 (main), relaying a review-craft finding (msg 4310, from_role review)
parent_epic: infrastructure_master
priority: P1
source: >-
  Review-craft session, dispatched on unrelated work, independently noticed the pattern while investigating slot 1's own
  boot history and reported it to main via chat (msg 4310, 2026-08-08T16:36:22Z) rather than filing directly —
  doc-authoring/backlog is outside review's scope per its own role definition.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-08
locked_since:
context_scope: [agent-orchestrator/server/routes/slots_worker.py, agent-orchestrator/server/state_store/cooldown.py]
---

# Slot 1 (review role) crash-looping via unexplained TmuxPruner kills

## What was found

Reporter (review craft, slot unspecified in the message, investigating slot 1's own history) queried
`GET /api/activity?slot=1` for the window 14:30-16:30Z on 2026-08-08 and found:

- 22x `agentkeeper_review_succeeded` events, paired almost 1:1 with 22x `tmux_session_lost` events (TmuxPruner
  attribution — externally-killed, not a voluntary exit).
- Of those 22 death events, only **2** were immediately preceded by a genuine `context_recycle_requested` event (the
  sanctioned self-compact/RECYCLE exit path). The remaining **~20** have no such precursor — unexplained kills.
- Cross-checked against the 3 event types known to drive the separately-tracked fleet-wide post-spawn wedge pattern
  (`forced_compact_ineffective`, `slot_wedged_killed_for_resume`, `worker_kick_failed`): **zero hits** for slot 1 on any
  of the 3 in this window. This suggests a distinct mechanism from that cluster, not a re-occurrence of it — though a
  shared deeper root cause (e.g. host-level resource contention) has not been ruled out; nobody has read
  TmuxPruner/keeper source or captured a live pane at the moment of death yet.

**Compounding, likely-related bug found in the same investigation**: ~6 of ~14 `slot_boot` cycles for slot 1 in the same
window hit `boot_read_unconfirmed` (428, missing `worker.md`) on the first `/boot` attempt — see
`/plans/active/issues/review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md` (Progress Log updated 2026-08-08 with
this same finding). Net effect of both bugs together: review continuity is fragmenting into many short-lived (often 1-6
min) sessions, which also explains the volume of distinct short-lived agent ids seen in `review-agent-checkpoint.md`'s
own Tick history.

## Why it matters

- Continuous spawn overhead: ~22 kill/respawn cycles in 2h on a single slot is real, ongoing waste (compute + boot
  round-trips), not a one-off.
- Degrades review quality/continuity: short-lived sessions cannot build up the multi-hour context a thorough review pass
  benefits from, and each restart re-pays the (separately buggy) boot-read-confirmation cost above.
- Unknown root cause: without keeper/TmuxPruner source inspection or a live pane capture at the moment of death, it is
  not yet known whether this is a liveness-probe false-positive, a resource-pressure kill, or something else.

## Todos

- [ ] [BACKEND] P1. Read `TmuxPruner`'s kill logic (and whatever emits `tmux_session_lost`) in the agent-orchestrator
      server source and determine why it is concluding slot 1's tmux session is lost roughly every 5-10 minutes when the
      session is, in the large majority of cases, not exiting voluntarily (no preceding `context_recycle_requested`).
      Check specifically whether this is a liveness-probe timing/false-positive issue (e.g. a heartbeat threshold too
      tight for review-craft's actual work cadence) versus a genuine external kill (resource pressure, OOM, a supervisor
      restart). Repo: agent-orchestrator.
- [ ] [BACKEND] P2. If the root cause is a false-positive liveness probe: fix the threshold/detection logic. If it is a
      genuine resource-pressure kill: correlate against host memory/CPU metrics for the same window and file/link to the
      appropriate host-capacity issue if one already exists (check
      `/plans/active/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md` first for a possible match
      before filing new). Repo: agent-orchestrator.
- [ ] [REVIEW] P3. Once a fix lands, independently re-verify via `GET /api/activity?slot=1` (or whichever slot is
      currently the review role) over a fresh 2h+ window that `tmux_session_lost` without a preceding
      `context_recycle_requested` has dropped to near-zero. Repo: unified-trading-pm (verification + checkbox flip
      only).

## Progress log

- 2026-08-08 (main agt-22de53): Filed from a review-craft chat report (msg 4310) that review declined to file itself
  (doc-authoring is outside review's scope). Not independently re-verified against `/api/activity` by main before filing
  — relaying the reporter's evidence as given, since it was already a direct, timestamped `/api/activity` query result,
  not a self-report needing corroboration. Cross-linked the compounding `boot_read_unconfirmed` finding into the
  existing `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md` doc instead of duplicating it here.
- 2026-08-08 ~17:36Z (main agt-22de53): Live corroborating data point, NOT slot 1 — during a routine stale-slot check,
  slots 11 and 13 both independently hit the same `forced_precompact`→`forced_compact`→`worker_kick_failed` sequence
  within the same ~5min window (slot 11: kicks failed 17:33:54Z and 17:35:50Z, ~4min after its 17:31:53Z compact; slot
  13: one failed kick at 17:36:03Z, ~4min after its 17:31:55Z compact). This broadens the pattern from "review role /
  slot 1 only" to a fleet-wide post-compact respawn issue — same `worker_kick_failed` signature the todo above already
  asks to investigate. Slot 11 escalated via `reassign kill_worker:true` per standing policy (2 failed kicks, no
  recovery) — task `solana_dex_pool_swaps_indexer-002` returned to queue cleanly. Slot 13 held one more tick (only 1
  failed kick so far) before escalating. Does not change scope/priority of the existing todos, just adds evidence that
  the root-cause investigation (todo 1) should look at the post-compact respawn path generally, not review-role-specific
  logic.
- 2026-08-08 ~17:47Z (main agt-22de53): Possible task-affinity angle, worth todo-1's attention —
  `solana_dex_pool_swaps_ indexer-002` (the same task released from slot 11 above) was picked up by autospawn on slot 9
  at 17:41:55Z, then hit the identical
  `forced_compact_ineffective`(17:42:22Z)→`forced_precompact`→`forced_compact`(17:43:28Z) sequence, then went silent
  (`worker_alive` flipped false, `context_reading_stale` true, no further activity) for 5+ min with no explicit
  `worker_kick_failed` event ever logging — escalated on the `worker_alive:false` + staleness signal alone since the
  wedge was otherwise unambiguous. This is the SECOND consecutive wedge on this exact task across two different slots
  (11, then 9) — same as the standing `tardis_impossible_combinations` mitigation note (see
  `tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`), a repeat-wedge on the same task across
  slots can mean `reassign`'s `affinity=high` re-poisons the next slot rather than the slot itself being at fault. Used
  `reassign kill_worker:true` again here (task returned to queue, `released_task_affinity:"high"`) — if this task wedges
  a THIRD slot, switch to `skip-current-task` instead of `reassign` per the tardis precedent, and consider filing a
  dedicated task-specific issue rather than continuing to treat it as generic fleet evidence here.
- 2026-08-08 ~17:49Z (main agt-22de53): Rate observation — since the 17:36Z entry above, the same confirmed signature
  (`slot_boot`→`forced_precompact`→`forced_compact`→silent/`worker_alive:false`, no recovery) has now hit slots 9, 24,
  25, and 26 across 5 consecutive ~60s ticks (17:36-17:49Z), i.e. roughly one new wedge per tick, each on a different
  task/slot with no task-family overlap between them (solana indexer, 2x sports_taxonomy, ao_satellite, citadel
  satellite) except the one same-task repeat already logged above. This reads as a genuine fleet-wide acceleration, not
  sporadic noise — every wedge escalated cleanly via `reassign kill_worker:true` with the task returned to queue, so
  there is no user-visible stall, but the respawn/compact churn rate is real and climbing. Not paging the operator
  separately (this doc is already P1 with a BACKEND todo assigned and the rate itself doesn't change root-cause scope),
  but flagging the acceleration here so whoever picks up todo 1 has the full frequency picture, not just the original
  3-instance sample.
- 2026-08-08 ~19:49Z (main agt-22de53, relaying review msg 4345): New evidence narrowing todo 1's liveness-probe-vs-
  genuine-kill question, specific to review-role (slot 1) sessions. Review's own live session logged a
  `tmux_session_lost` (`killed`) activity event at 19:37:43Z despite being continuously alive throughout — single agent
  registration, no respawn, review-tick work continuing uninterrupted both before and after the event, and `tmux_alive`
  staying `true` the whole time. Review's hypothesis: `worker_alive` tracks **backlog-worker heartbeat cadence**, which
  a review-tick session legitimately does not follow (review polls/ticks on its own cadence, not the standard
  dispatched-worker heartbeat) — so the kill classification may be a false positive specific to the review role's
  different heartbeat shape, not a genuine external kill or resource-pressure event. This is a concrete, first-party
  data point supporting the "liveness-probe timing/false-positive" branch of todo 1 (vs. the "genuine external kill"
  branch) — whoever reads the TmuxPruner/keeper source for todo 1 should specifically check whether the liveness check
  is worker-heartbeat-based (and thus structurally mismatched for the review role) rather than tmux-session-based.
  Review flagged but did not chase further this tick; not independently re-verified by main beyond relaying the report.
- 2026-08-08 ~20:22Z (main agt-22de53): Possible server-restart correlation, worth todo 1's attention. Observed a brief
  AO server connection-refused blip around ~20:15Z (uvicorn process PID changed between checks — 2920882 -> 3694559,
  `ss -tlnp` confirmed the new PID bound port 8765; recovered within ~15s, no fleet-visible gap). Shortly after, 3 slots
  (4, 7, 8) that all booted within the same ~5s window (20:17:23-20:17:28Z, autospawn_succeeded/task_dispatched/
  slot_boot all clustered) went completely silent afterward — no `forced_compact`, no `slot_progress`, nothing at all
  for 4:40+ min, a DIFFERENT failure signature from the tracked `forced_precompact`->`forced_compact`->silent pattern
  (no compact ever fired here). All 3 escalated cleanly via `reassign kill_worker:true`, tasks returned to queue, no
  user-visible stall. Hypothesis for whoever picks up todo 1: sessions that were mid-boot at the moment of the server
  restart may have had their initial heartbeat/registration silently dropped (server-side connection reset mid-boot),
  producing dead-on-arrival sessions with no compact signature since they never got far enough to need one — distinct
  from, but possibly a variant of, the main tracked pattern. Not independently confirmed (no access to server-side
  connection logs from main's vantage point), just flagging the timing correlation as a data point.
