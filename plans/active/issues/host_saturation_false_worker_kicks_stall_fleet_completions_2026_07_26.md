---
doc_type: issue
title:
  Sustained shared-host saturation (back-to-back QG churn + claude fleet + swap) pushes actively-working slots' tmux
  panes past the WorkerLivenessWatchdog verify_window_s, firing false worker_kicked events that interrupt in-flight work
  and stall fleet completions (>1h zero slot_done despite 5-7 workers alive and drawing tasks)
summary: >-
  On 2026-07-26 the shared orchestrator host (ip-172-31-5-118) went >1h with ZERO new `slot_done` completions (last was
  id 206909 @09:17Z) even though 5-7 slots stayed `worker_alive=true`, kept drawing fresh tasks, and advanced their
  pings across ticks (backlog dispatched climbed 4→7, queued drained 32→29 — dispatch was flowing, completion was not).
  The driver is sustained host saturation, not a task deadlock: load average WORSENED over the hour (3.15/4.32/6.19
  @09:xx → 10.59/8.64/6.61 @10:17) with full-suite QG (pytest) runs queuing back-to-back (a new pytest PID 2835447
  started 10:14 the moment the prior one finished) on top of 6+ concurrent claude sessions and ~2.7GB swap thrash. Under
  that load, tmux pane reads for genuinely-progressing workers lag past `WorkerLivenessWatchdog.verify_window_s` (10s),
  so the watchdog fires `worker_kicked`/frozen on slots that are NOT wedged (observed steadily across slots 3/4/5) —
  each false kick interrupts live in-flight work, which is why nothing reaches `slot_done`. This is a false-positive
  liveness class distinct from the idle-one-shot re-kick churn (that self-heals harmlessly); here the false kicks
  actively HARM throughput by interrupting real progress, and the sustained saturation makes them chronic.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    worker-liveness,
    watchdog,
    verify-window,
    false-positive,
    worker-kicked,
    host-saturation,
    quality-gates,
    admission-control,
    throughput,
    bug,
  ]
related:
  [
    /plans/active/issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md,
    /plans/active/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md,
    /plans/active/issues/watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-26
last_updated: 2026-07-26
priority: P1
parent_epic: orchestrator_master
source:
  "review role (msg 2142) graduated this from transient host contention to a real finding per main's stated watch
  threshold; main (agt-52bb99) corroborated cross-tick via read-only /api/state polling"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# Host saturation → false worker_kicks on actively-working slots → stalled fleet completions

## Evidence (review role + main read-only /api/state, 2026-07-26, UTC)

- **Zero completions for >1h**: last `slot_done` was id 206909 @09:17Z; still the latest as of 10:17Z (review, msg
  2142), despite the fleet being demonstrably alive and busy.
- **Fleet alive + drawing work the whole time** (main, cross-tick `/api/state` polling ~10:0x–10:1xZ): `backlog_summary`
  dispatched climbed 4→5→6→7, queued drained 32→31→30→29, active_workers cycled 3→4→5→6→7 across slots {2,3,4,6,7,8,10}
  with advancing pings. So this is NOT idle slots and NOT a task deadlock — the two dispatched tasks that could move
  `done` (`defi_wizard_batch2_018_residual_findings-004/-005`) were both confirmed `ready (no blockers)`; the other two
  dispatched are legitimately gated (operator merge-gate BLK-ec018203 on the sports odds_targets export;
  `tradfi_mdps_build_continuous` prereq-gated on mismatches 2+4). Dispatch was flowing; completion was not.
- **Load worsening, not draining** (review): load average 3.15/4.32/6.19 @09:xx → **10.59/8.64/6.61 @10:17Z**.
- **QG runs queue back-to-back**: the features-service full-suite QG that was running @09:xx DID clear, but a new pytest
  (PID 2835447) started @10:14 the moment it finished — so the host never returns to baseline; there is always a
  full-suite QG running. Layered on 6+ concurrent claude sessions + ~2.7GB swap.
- **False kicks on non-wedged slots**: `worker_kicked`/frozen events continued steadily across slots 3/4/5 in the 15 min
  before 10:17Z, all with `ping_advanced=false` at the moment of the kick but recovering immediately after — the
  signature of a pane whose read lagged past the verify window under host load, not a genuinely frozen agent.

## Root cause (two compounding layers)

1. **Watchdog liveness detection is too sensitive to host-load-induced pane lag.**
   `WorkerLivenessWatchdog.verify_window_s` is 10s: a single tmux pane read that comes back stale within one 10s window
   fires `worker_kicked`. Under a saturated host (load ~10 on a small box + swap thrash), the OS scheduler delays pane
   I/O for genuinely-progressing workers past 10s, so the watchdog kicks slots that are actively mid-task. Each kick
   interrupts real in-flight work → the work never reaches `slot_done`. The kick "self-heals" (worker_kicked → working)
   but only by restarting/nudging work that was already progressing, so the net effect is a treadmill: perpetual
   restart, no completion.
2. **No host-level QG admission control.** The shared-host guidance is a cap of `max(2, floor(cores/4))` concurrent full
   QGs, but nothing ENFORCES it — each slot independently launches a full-suite QG on its own schedule, and they queue
   back-to-back so there is always one saturating the host. Even a single full QG + the 6-session claude fleet + swap is
   enough to keep load ~10 and keep triggering layer (1).

## Why it matters

A fleet that is alive, dispatched, and unblocked but completes ZERO tasks for over an hour is indistinguishable from
progress at the `backlog_summary` level (dispatched/queued move) while producing nothing. The watchdog — meant to
recover wedged workers — becomes the thing preventing completion, by interrupting healthy work whenever the host it
shares is busy. Left unaddressed it also raises real escalation risk: a slot false-kicked repeatedly while holding
uncommitted or committed-unpushed WIP is one host hiccup away from the dead-session unpushed-sweep path (see
`watchdog_unpushed_sweep_defeats_operator_merge_gate`).

## Recommended decision

- [ ] [BACKEND] P1. **Make the liveness kick host-load-aware / require two-window confirmation.** Before firing
      `worker_kicked`, require the ping/pane to be stale across TWO consecutive verify windows (not one), OR widen
      `verify_window_s` adaptively when host load average / swap pressure is high, OR gate the kick on a progress marker
      (don't kick a pane whose progress advanced within the last N seconds even if the latest read is stale). The point:
      a single transient pane-read delay under host thrash must NOT interrupt a genuinely-progressing worker. **Done
      when**: a regression test simulating pane-read latency > `verify_window_s` while progress markers keep advancing
      produces ZERO `worker_kicked` events. Repo: agent-orchestrator.
- [ ] [DEVOPS] P1. **Enforce the shared-host QG cap as an actual admission gate.** Replace the advisory
      `max(2, floor(cores/4))` guidance with a real host-level semaphore/lock around full-suite QG launches so they
      cannot queue back-to-back and pin the host at saturation; a slot that wants to run QG waits for a slot rather than
      launching unconditionally. **Done when**: with N slots wanting QG simultaneously, at most `max(2, floor(cores/4))`
      run concurrently and the rest queue on the semaphore (verified by a launch test). Repo: agent-orchestrator (QG
      launcher) — coordinate with quality-gates.sh entry point.
- [ ] [DOC] P2. Document the host-saturation → false-kick → completion-stall failure mode and the two-window /
      load-aware kick contract in the orchestrator watchdog SSOT
      (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`), so future liveness tuning treats "stale
      pane under host load" as distinct from "wedged agent."

## Progress Log

- 2026-07-26 (main agent, agt-52bb99): Filed per the watch threshold I stated to the review role — it graduated from
  transient host contention to a real finding once (a) the features-service QG cleared yet done stayed flat, (b) load
  worsened rather than drained, and (c) QGs were observed queuing back-to-back. Corroborated the "alive but not
  completing" signature cross-tick via read-only `/api/state` (dispatched climbing, queued draining, workers cycling
  with advancing pings, yet `done` pinned at 70 and last real `slot_done` >1h stale). NOT operator-escalated: nothing is
  dead and no WIP is at risk yet (consistent with the review role's own call) — this is a self-healing throughput
  degradation, not a hard-stop. Escalation trigger to watch: a slot going dead with committed-unpushed WIP while
  false-kicked, which would cross into the unpushed-sweep governance-bypass path. Fix is BACKEND/DEVOPS-owned; main is
  charter-barred from killing/capping QGs, reaping slots, or editing AO runtime state.
