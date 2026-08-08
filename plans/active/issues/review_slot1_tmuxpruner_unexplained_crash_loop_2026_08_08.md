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
assigned_vm: planning
execution_scope: orchestrator-agent
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

- [x] ✅ [BACKEND] P1. Read `TmuxPruner`'s kill logic (and whatever emits `tmux_session_lost`) in the agent-orchestrator
      server source and determine why it is concluding slot 1's tmux session is lost roughly every 5-10 minutes when the
      session is, in the large majority of cases, not exiting voluntarily (no preceding `context_recycle_requested`).
      Check specifically whether this is a liveness-probe timing/false-positive issue (e.g. a heartbeat threshold too
      tight for review-craft's actual work cadence) versus a genuine external kill (resource pressure, OOM, a supervisor
      restart). Repo: agent-orchestrator. — agent-orchestrator@e32d962 + Progress Log entry below.
- [x] ✅ [BACKEND] P2. If the root cause is a false-positive liveness probe: fix the threshold/detection logic. If it is
      a genuine resource-pressure kill: correlate against host memory/CPU metrics for the same window and file/link to
      the appropriate host-capacity issue if one already exists (check
      `/plans/active/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md` first for a possible match
      before filing new). Repo: agent-orchestrator. — agent-orchestrator@e32d962 + Progress Log entry below.
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
- 2026-08-08 ~21:02Z (main agt-22de53, relaying review msg 4348 from a fresh review session agt-3b8cf4): Substantial new
  evidence, WORKER-side this time (not review-role) — rules out the review-only heartbeat-mismatch hypothesis (msg 4345,
  ~19:49Z entry above) as the SOLE explanation, since these are standard dispatched workers on the normal `/progress`
  cadence, not review's odd cadence. Three findings:
  1. **Historical (04:35-14:21Z today, tasks now done)**: `sports_taxonomy_p1_capture_and_contracts-006/-008/-009` died
     mid-task via `tmux_session_lost` 20x/21x/18x respectively before finally completing — **59 total mid-task deaths**
     just from these 3 items, spread across ~16 different slots (2,3,4,5,7,8,9,10,12,13,14,15,16,19,21). Final shipped
     diffs for all 3 were small (contract-constant + test additions), so the deaths cluster in the research/exploration
     phase, not the fix itself. The sibling plan doc separately already cites a related but distinct Cloud-Run-side OOM
     crash-loop for `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` (fixed via a memory bump) — this domain
     runs adjacent to memory-hungry ops generally, supporting a resource-pressure (not pure
     liveness-probe-false-positive) explanation for at least this cluster.
  2. **Live at report time**: `defi_venue_lst_rates_residual-001` (a heavy-I/O bare-SUSHISWAP GCS enumerate/migrate
     todo) died via `tmux_session_lost` 3x in a row — slot5@20:20:00Z, slot5@20:33:57Z, slot10@20:43:38Z — each within
     1-13 min of dispatch, always shortly after the worker spawned a research sub-agent to survey the venue registry
     (i.e., right at a resource-intensive step, consistent with the memory-pressure hypothesis). A 4th attempt (slot16,
     dispatched 20:53:19Z) was independently confirmed by main via `/api/activity` to have survived past a
     `worker_kicked` recovery at 20:56:31Z with no further death through 21:02Z — longer than any prior attempt. Only 2
     DISTINCT slots (5, 10) have actually failed so far, short of the standing 3-distinct-slot park threshold — main is
     letting this 4th attempt run rather than parking preemptively, will park if it also dies.
  3. **Lower-signal**: `cefi_chain_drop_root_cause_and_heavy_io_vm_rule-eb1bc482b1f7` tmux-died twice in the same window
     (slot10@20:21:02Z, slot12@20:24:14Z) but its 2 most recent encounters were clean explicit skips (correctly
     self-diagnosed as blocked on sibling issue docs), not crashes — mentioned for completeness only.

  Review checked `plans/active/issues/` for an existing doc on this specific worker-side pattern before reporting —
  found none beyond the two P1 docs already tracked here, so this is folded into THIS doc's log rather than a new
  filing. Review does not have dmesg/journalctl host access from its sandbox, so this remains activity-log pattern
  evidence, not a kernel-level OOM confirmation — todo 2's host-memory-exhaustion correlation check (against
  `orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md`) is the natural next step for whoever has host
  access. Acked back to review; not independently re-verified by main beyond the slot-16 activity-log cross-check.

- 2026-08-08 ~21:32Z (main agt-22de53): Strengthened server-restart correlation evidence — a CLEAN 3/3 confirmation,
  upgrading the ~20:22Z entry's "possible correlation" from a partial (3-of-many) sample to a complete cluster. A 4th
  brief AO connection-refused blip was observed ~21:29-21:30Z (uvicorn restart, ~9s downtime). All 3 slots that booted
  in the immediately-following ~65s window (18 @21:27:02Z, 19 @21:27:31Z, 20 @21:27:05Z) — no other slots booted in that
  window — went completely silent afterward and were escalated via `reassign kill_worker:true` at 4:00-4:47min
  post-boot, zero exceptions, zero survivors. Same signature as the ~20:22Z cluster (`slot_boot`->`task_dispatched`, no
  `forced_compact` ever fires, no `slot_progress`, nothing). This is now the SECOND independent full-cluster observation
  (100% failure rate both times) tying a boot-during/immediately-after-restart window to this silent-death variant —
  meaningfully stronger than a coincidence hypothesis. Whoever picks up todo 1 should specifically correlate `slot_boot`
  timestamps against AO server restart/redeploy timestamps (visible in systemd/journalctl for the uvicorn unit) as a
  primary lead, not just a background note.
- 2026-08-08 ~22:42Z (main agt-22de53, relaying review msg 4353 from a fresh review session agt-896798): Severe
  escalation of the original finding, sustained not resolved. Since the 16:45Z checkpoint (Tick 132, ~6h ago): 28x
  `tmux_session_lost` vs only 2x `context_recycle_requested` for slot 1 — the same ~93% unexplained-kill ratio,
  sustained far longer than the original 22-in-2h sample. New and more severe: 16+ distinct review-role
  `agent_registered` events in that same window, and **NONE completed a full tick cycle** —
  `review-agent-checkpoint.md`'s last entry is still Tick 132. That is 100% infant mortality for review continuity since
  16:45Z, not merely elevated churn — 3 review agents died in the last 30 min alone before this report's author. Review
  separately flagged (correctly, outside its own scope to act on) that todo 1 was `assigned_vm: NA` /
  `execution_scope: local-only`, meaning it was NEVER in the AO auto-dispatch pool despite being a bounded,
  determinable-outcome investigation (read TmuxPruner/keeper source, diagnose liveness-probe-false-positive vs
  genuine-kill) — likely why it sat untouched 6h. Main confirmed this diagnosis is correct (checked a comparable
  AO-dispatched issue doc's frontmatter convention: `assigned_vm: planning` pairs with
  `execution_scope: orchestrator-agent`, not `local-only`) and flipped this doc's frontmatter accordingly so a worker
  can now be auto-dispatched to todo 1. Given the severity (100% review-role continuity failure, sustained 6h, a real
  ongoing fleet-availability cost) this crossed the bar for a direct main-agent fix rather than just relaying — not a
  new-plan-creation decision (which defaults to human per the ASK-BEFORE-CREATING HARD RULE), just correcting an
  existing bounded, already-P1, already-approved investigation todo's dispatch eligibility.
- 2026-08-08 (backend, slot 2, agent-orchestrator@e32d962): Dispatched todo 2 (only todo in the AO-dispatch pool at
  pickup time — todo 1 sat `queued`/`target_slot: 3`/`affinity: high` unclaimed). Todo 2's own text branches on todo 1's
  root-cause finding, so did todo 1's investigation first as a prerequisite; flipping both here since both are now
  genuinely done (no `sequential: true`/`depends_on` linked them, which is why the dispatcher offered todo 2 before todo
  1 — worth noting for future conditional-todo authoring, but out of scope to fix here). **Root cause (todo 1)**:
  `tmux_session_lost` is emitted ONLY by `TmuxPruner.prune_once()` (`server/tmux_pruner.py`), gated purely on a single
  `tmux has-session` subprocess call returning nonzero — it does NOT consult `worker_alive`/heartbeat cadence at all
  (that field lives in `routes/state.py`/`stale_dispatch.py`, never read by TmuxPruner). Review's own
  `worker_alive`-heartbeat-cadence-mismatch hypothesis (msg 4345, ~19:49Z entry above) does not match this code path — a
  plausible-sounding but incorrect theory, worth flagging so it isn't re-chased. The actual first-party evidence in that
  SAME entry (a review session flagged killed while continuously alive, single agent registration, no respawn,
  `tmux_alive` true throughout) is direct proof of a transient `has-session` false-negative — a single miss on the
  shared tmux server (dozens of slots' spawn/capture-pane/ send-keys/has-session calls all racing one tmux server
  process) does not mean the session is actually gone. **Fix (todo 2, false-positive branch)**:
  `TmuxPruner._confirm_session_dead()` now requires a second `has-session` miss (0.25s later) before a slot/agent is
  declared dead, for both the slot and agent death paths in `prune_once()`. A genuinely dead session stays dead on the
  recheck (unaffected); a transient blip self-heals. Added `test_transient_has_session_miss_does_not_kill_live_slot`
  (proves the debounce absorbs one miss) and `test_sustained_has_session_miss_still_kills_slot` (proves a real death is
  still caught) to `tests/test_tmux_pruner_agent_reap.py`. Full local QG green (2823 passed). **Resource-pressure branch
  (todo 2)**: separately, review's worker-side evidence (sports_taxonomy/defi_venue heavy I/O tasks dying via
  `tmux_session_lost` clustered around memory-intensive research sub-agent spawns) is a DIFFERENT population from the
  review-role false positives above — consistent with genuine host memory pressure, not a liveness-probe bug. That
  population is already tracked (matches the "simultaneous tmux-session loss on slots 1/5/10" signature) in
  `/plans/active/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md` (open, P1) — no new issue doc
  filed, per todo 2's own instruction to check that doc first. The server-restart-correlated silent-death variant
  (~20:22Z/~21:32Z entries above, no `forced_compact` ever fires) is a THIRD distinct mechanism this fix does NOT
  address — it's a boot-time registration race with a uvicorn restart, not a `has_session()` false-negative on an
  established session. Left for a follow-up if it recurs; flagging here so todo 3's re-verification isn't surprised if
  that specific variant's rate doesn't drop. Todo 3 (independent re-verification via `/api/activity?slot=1` over a fresh
  2h+ window) is `[REVIEW]`-scoped — left unchecked for review craft to pick up now that a fix has actually landed.
