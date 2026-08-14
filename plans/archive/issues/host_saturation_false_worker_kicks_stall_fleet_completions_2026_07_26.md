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
status: resolved
nature: issue
asset_group: [ao]
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
    /plans/archive/issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md,
    /plans/archive/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md,
    /plans/archive/issues/watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-26
author: unknown
last_updated: 2026-08-06
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
  "AO issue-doc sweep 2026-08-06 — the standing [DEVOPS] P1 admission-semaphore todo found already shipped via
  unified-trading-pm's qg-host-governor.sh (flock-based, wired into base-service.sh/base-library.sh); checkbox had never
  been flipped."
locked_by:
context_scope:
  [
    /plans/archive/issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md,
    /plans/archive/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    scripts/quality-gates-base/base-service.sh,
  ]
depends_on: []
---

> **🗄️ ARCHIVED 2026-08-06** — fully resolved. All 3 todos verified `[x]` and live in code: the two-window/load-aware
> kick grace-shield (`agent-orchestrator@64b5310`), the SSOT doc cross-reference, and the shared-host QG admission
> semaphore (`unified-trading-pm`'s `qg-host-governor.sh`, found shipped-but-unflipped during this sweep). No open
> todos, no Deferred items. Surfaced by the 2026-08-06 AO issue-doc sweep.

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

**Priority ruling 2026-07-26** (resolved `autonomous_session_operator_decisions_2026_07_25.md` entry #21, option A):
this fix goes FIRST, ahead of `issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md`'s
hard-kill-escalation todo (that todo is now explicitly gated on this one landing) — the false-positive side has measured
active harm right now, the harden side's evidence is a single 5-day-old stuck slot, and hardening while the classifier
is known-wrong is actively dangerous.

- [x] ✅ [BACKEND] P1. **SHIPPED ELSEWHERE — `agent-orchestrator@64b5310` (citation fix by `/na-eligibility-audit ao`
      2026-07-30; the work landed, this checkbox was simply never flipped).** Executed as
      `/plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md`'s `[BACKEND] P1` todo, which cites this doc's spec
      verbatim. Implementation took the third of the three options this todo offered (progress-marker gating, not
      two-window or adaptive-window): `_progress_marker_shields_kick` + a new `kick_progress_grace_seconds` knob
      (default 90s) in `WorkerLivenessKicker._tick_once` — a worker whose `last_ping` advanced inside the grace window
      is never kicked even when the pane read classifies frozen. **This todo's own stated done-when is met**: regression
      test `test_pane_read_latency_with_advancing_progress_markers_produces_zero_kicks` simulates 4 ticks of a
      persistently- FROZEN pane read while `last_ping` keeps advancing and asserts ZERO
      `worker_kicked`/`worker_kick_failed` events; full local QG green (1993 passed, ruff/basedpyright clean). Note the
      shipping todo also corrected a location premise: the pane-classification path that actually emits `worker_kicked`
      is `server/worker_liveness/__init__.py`, not `worker_liveness_watchdog.py`. Original text follows. Make the
      liveness kick host-load-aware / require two-window confirmation. Before firing `worker_kicked`, require the
      ping/pane to be stale across TWO consecutive verify windows (not one), OR widen `verify_window_s` adaptively when
      host load average / swap pressure is high, OR gate the kick on a progress marker (don't kick a pane whose progress
      advanced within the last N seconds even if the latest read is stale). The point: a single transient pane-read
      delay under host thrash must NOT interrupt a genuinely-progressing worker. **Done when**: a regression test
      simulating pane-read latency > `verify_window_s` while progress markers keep advancing produces ZERO
      `worker_kicked` events. Repo: agent-orchestrator.
- [x] [DEVOPS] P1. **CLOSED 2026-08-06 — shipped, evidence found during the AO issue-doc sweep (checkbox was never
      flipped).** `unified-trading-pm/scripts/quality-gates-base/qg-host-governor.sh::qg_governor_acquire` implements a
      real `flock`-based token semaphore enforcing `K=max(2, floor(cores/4))` concurrent heavy QG phases host-wide,
      wired into both `base-service.sh` (~L788) and `base-library.sh` (L424) — the shared entry point every repo
      invokes. Matches this todo's own done-when exactly. Original text follows. **Enforce the shared-host QG cap as an
      actual admission gate.** Replace the advisory `max(2, floor(cores/4))` guidance with a real host-level
      semaphore/lock around full-suite QG launches so they cannot queue back-to-back and pin the host at saturation; a
      slot that wants to run QG waits for a slot rather than launching unconditionally. **Done when**: with N slots
      wanting QG simultaneously, at most `max(2, floor(cores/4))` run concurrently and the rest queue on the semaphore
      (verified by a launch test). Repo: agent-orchestrator (QG launcher) — coordinate with quality-gates.sh entry
      point.
- [x] ✅ [DOC] P2. Document the host-saturation → false-kick → completion-stall failure mode and the two-window /
      load-aware kick contract in the orchestrator watchdog SSOT
      (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`), so future liveness tuning treats "stale
      pane under host load" as distinct from "wedged agent." — unified-trading-pm. Added a cross-referenced note under
      the "Liveness" bullet describing the failure mode + the shipped `agent-orchestrator@64b5310` grace-shield fix, and
      pointing to `worker-liveness.md`'s existing full-detail section (which already documented the fix itself; this
      doc's own SSOT was the one still missing the cross-reference).

## Progress Log

- 2026-07-26 (main agent, agt-52bb99, ~15:08Z): **Second occurrence corroborated — the false-kick cascade recurred at a
  LOWER load peak (~11, vs 15.89 in the first incident).** Timeline (UTC): a spike peaked ~10.9 @15:00 drove a
  `worker_kicked`→`killed` cascade across slots 1/4/5/8 (all four reached `status=killed`; slots 1/4/5/8 each went fully
  dead `worker_alive=false AND tmux_alive=false` at peak) with their pings frozen at 14:58–15:00; load then briefly
  drained to 4.19 @15:01 before climbing again 5.80→9.32→12.94 @15:05–15:08 coincident with a large backlog ingest
  (`queued` 80→287 via `regen_backlog_from_plan.py`). `done` stayed pinned at 64 for ~16 min across the window even
  though dispatch kept flowing (`dispatched` 5→8; queued drained then surged on ingest) and AutoSpawn recovered every
  killed slot within ~4–6 min (slots 1/4/5/8 all back to working/idle by 15:07, slot 4 respawned onto a fresh task).
  **No WIP lost / no governance-bypass**: `/api/fleet/git-health` showed `ahead=0` fleet-wide throughout, and no dead
  slot's task sat behind an operator merge gate (slot 4's block was BLK-f28c0137, a _credentials_ gate with no commits;
  slots 5/8 tasks had no blocked entry) — so `_sweep_unpushed_slots` had nothing to auto-push and the merge-gate bypass
  path (see `watchdog_unpushed_sweep_defeats_operator_merge_gate`) did NOT fire. **Two reinforced fix signals**: (1) the
  cascade triggering at load ~11 (not just ~16) shows `verify_window_s=10s` is hit more easily than the first incident
  implied → strengthens the BACKEND two-window / load-aware-kick todo; (2) this load surge was ingest-driven (287-task
  backlog burst), not only back-to-back QG → the DEVOPS admission gate should throttle on measured host load, not merely
  concurrent-QG count. **Not operator-escalated**: self-healing (all slots recovered, no WIP at risk) and API responsive
  throughout (no `/api/state` timeouts this window, unlike the 10:34Z load-15.89 spike).
- 2026-07-26 (main agent, agt-52bb99, ~10:36Z): **New dimension — the timeout now reaches the DB/API layer, not just
  tmux pane reads.** Review role (msg 2145) reported load average 15.89/11.58/8.31 @10:34Z (climbing from 11.55 ten min
  prior) with DB-backed API endpoints (`POST /reviewed`, and `/api/state` for both of us) timing out at 25s+ while the
  server root still 404s in 2ms and the process stays alive — i.e. the process is up but its **SQLite write path /
  request queue backs up** under load ~16, distinct from (and worse than) the watchdog's `verify_window_s` pane-read lag
  in root cause layer (1). Consequence observed: 2 reviewed-clean `slot_done` commits (3f18fd91f, 8c2f3590) could not be
  written to the reviewed ledger until load drained (no data loss — the marks land once SQLite frees). This argues the
  DEVOPS admission gate (root-cause layer 2) should throttle on host load / DB latency, not only on concurrent-QG count,
  since even a brief saturation spike now degrades API _availability_, not just throughput. **Not escalated**:
  intermittent + self-healing (my `/api/state` recovered cleanly the same minute — done 72, 7 workers alive, blocked
  6/mine 0); no slot confirmed dead-with-unpushed-WIP (review role could not confirm, I saw none), so the unpushed-sweep
  governance-bypass trigger has not fired.
- 2026-07-26 (main agent, agt-52bb99): Filed per the watch threshold I stated to the review role — it graduated from
  transient host contention to a real finding once (a) the features-service QG cleared yet done stayed flat, (b) load
  worsened rather than drained, and (c) QGs were observed queuing back-to-back. Corroborated the "alive but not
  completing" signature cross-tick via read-only `/api/state` (dispatched climbing, queued draining, workers cycling
  with advancing pings, yet `done` pinned at 70 and last real `slot_done` >1h stale). NOT operator-escalated: nothing is
  dead and no WIP is at risk yet (consistent with the review role's own call) — this is a self-healing throughput
  degradation, not a hard-stop. Escalation trigger to watch: a slot going dead with committed-unpushed WIP while
  false-kicked, which would cross into the unpushed-sweep governance-bypass path. Fix is BACKEND/DEVOPS-owned; main is
  charter-barred from killing/capping QGs, reaping slots, or editing AO runtime state.
- **na-eligibility-audit 2026-07-30**: KEEP-NA-STALE (citation fixed, no reclassification) — the `[BACKEND] P1`
  two-window/load-aware kick todo was ALREADY SHIPPED as `agent-orchestrator@64b5310` via
  `/plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md`'s `[BACKEND] P1`, which cites this doc's spec
  verbatim; the checkbox was simply never flipped. Flipped `[x]` with the commit + the regression-test evidence its own
  done-when asked for. Doc stays `assigned_vm: NA`: its `[DOC] P2` sibling edits
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` (never autonomous), and the `[DEVOPS] P1`
  host-level QG admission semaphore remains genuinely open.
- **2026-07-30 (plans-corpus reduction marathon, wave 3)**: shipped `[DOC] P2` — added a cross-referenced note under the
  "Liveness" bullet in `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` describing this failure
  mode + the shipped grace-shield fix, pointing to `worker-liveness.md`'s existing full-detail section
  (unified-trading-pm only, no code/build). **`[DEVOPS] P1` (host-level QG admission semaphore) assessed and left open —
  genuinely out of bounded scope for this pass**: it requires a real semaphore/lock around every full-suite
  `quality-gates.sh` launch fleet-wide (not just agent-orchestrator's own QG), touching the shared `base-service.sh`/QG
  entry point every repo in the fleet invokes — per this workspace's own rule-11 blast-radius discipline ("a gate change
  is not done until proven across the fleet + all promotion branches"), this is exactly the kind of shared-infra change
  that needs fleet-wide verification, not a single-repo bounded fix. Left for a dedicated DEVOPS pass with room to
  verify across repos.
- **2026-07-31 (conflict-gated re-triage) — RECLASSIFIED, not actually conflict-gated.** This doc WAS one side of the
  watchdog kick+escalation contradiction, and that side is fully shipped (`@64b5310` + the `[DOC] P2` SSOT note). The
  remaining `[DEVOPS] P1` (fleet-wide QG admission semaphore) was never itself gated by the contradiction or by any
  other doc — it's genuinely open, standalone, large-blast-radius infra work that needs its own scoped implementation
  pass (touches `base-service.sh`/the QG entry point every repo invokes). Mis-filed into the conflict-gated bucket by
  association with its sibling item, not by an actual dependency.
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA, valid — the
  single open item is the fleet-wide QG-admission semaphore (`[DEVOPS] P1`), assessed and correctly left open by two
  prior audit passes (2026-07-30, 2026-07-31) as genuinely out-of-bounded-scope, large-blast-radius infra work touching
  the shared `base-service.sh`/QG entry point every repo invokes. Re-confirmed on independent re-read — no change.
- **context-scout 2026-08-03**: refreshed context_scope (5 entries — added `scripts/quality-gates-base/base-service.sh`,
  the shared QG entry point the sole remaining `[DEVOPS] P1` admission-semaphore todo must touch; dropped the archived
  `watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md` sibling to stay within the minimal-list cap).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
