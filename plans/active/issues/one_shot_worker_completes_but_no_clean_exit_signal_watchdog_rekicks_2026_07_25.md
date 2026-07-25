---
doc_type: issue
title:
  A one-shot worker agent that has FINISHED its task does not exit / signal completion cleanly, so the
  WorkerLivenessWatchdog keeps classifying its still-alive-but-idle pane as frozen/idle and re-kicks it repeatedly (slot
  2 auto-kicked 5+ times in ~30min; one kick input_snippet was literally "Stop nudging — this session's task is
  complete"). Each kick self-heals (worker_kicked -> working) so it is non-blocking, but it is wasted kick churn that
  masks true idleness and suggests the one_shot lifecycle exit-signal has a gap.
summary: >-
  On 2026-07-25 (~21:20-21:50Z) the operator flagged that slot 2 froze + was auto-kicked 5+ times in ~30 minutes (21:20,
  21:22, 21:26, 21:47, 21:48, 21:50), each self-healing fine via WorkerLivenessWatchdog (worker_kicked -> working, no
  manual action needed per its own remediation text). One kick's `input_snippet` was literally "Stop nudging — this
  session's task is complete" — i.e. the pane's own agent was telling the kicker it was DONE while the watchdog kept
  treating it as frozen/idle and re-kicking. This points at the one-shot (escalation / single-task) worker lifecycle:
  the agent finishes its task but does not exit its tmux session or emit a clean completion signal the watchdog
  recognises, so the still-alive-but-idle pane looks like a wedged worker and gets re-kicked each liveness tick. Main
  (agt-52bb99) inspected slot 2 read-only at 21:51Z: `status=stale`, `current_task=null`, `last_msg="idle: 14 task(s)
  blocked on ... batch2-001 ..."`, `last_spawned_at=21:04:55Z`, `last_ping=21:34:51Z` — i.e. the churning one-shot has
  since gone quiet/idle-blocked, consistent with a completed-but-not-cleanly-exited agent whose pane the watchdog was
  repeatedly poking. Blast radius is low (every kick self-healed, nothing was blocked), but it is real kick churn that
  (a) wastes watchdog cycles, (b) masks whether the slot is genuinely free for redispatch, and (c) risks re-nudging an
  agent that has explicitly declared completion. Distinct root cause from the context_pct≈75 compact-confirmation wedge
  (that is a compact-submission wedge on slot 4; this is a one-shot completion-exit-signal gap on slot 2).
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
    one-shot,
    lifecycle,
    completion-signal,
    exit-signal,
    re-kick,
    churn,
    throughput,
  ]
related:
  [
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
    /plans/active/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md,
    /plans/active/issues/orchestrator_ready_p1_task_undispatched_no_matching_worker_autospawn_gap_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
priority: P3
parent_epic: orchestrator_master
source:
  "operator (agt-52bb99 msg 2039) pattern-note from review; main (agt-52bb99) inspected slot 2 state read-only,
  2026-07-25 ~21:51Z"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# One-shot worker finishes but does not exit/signal completion cleanly → watchdog re-kicks it

## Evidence (operator-reported + main read-only inspection, 2026-07-25)

- Operator (msg 2039): slot 2 froze + was auto-kicked 5+ times in ~30min (**21:20, 21:22, 21:26, 21:47, 21:48, 21:50**),
  each self-healed via `WorkerLivenessWatchdog` (`worker_kicked -> working`, no manual action needed per its own
  remediation text).
- One kick's `input_snippet` was literally **"Stop nudging — this session's task is complete"** — the pane's agent was
  declaring completion while the watchdog kept treating it as frozen/idle and re-kicking.
- Main inspected slot 2 read-only at 21:51Z via `/api/state`: `status=stale`, `current_task=null`,
  `last_msg="idle: 14 task(s) blocked on task sports_satellite_ao_dispatch_batch2-001 (3), ...batch2-011 (3), defi_dex_pool_symbol_fix_backfill_purge-001 (2)"`,
  `last_spawned_at=2026-07-25T21:04:55Z`, `last_ping=2026-07-25T21:34:51Z`. The churning one-shot has since gone
  quiet/idle-blocked.

## Hypothesis (needs owner confirmation)

A one-shot (single-task / escalation) worker completes its task but does **not exit its tmux session or emit a
completion signal the watchdog recognises as "done, stop watching"**. The still-alive-but-idle pane therefore reads as a
wedged/idle worker to the liveness kicker, which re-kicks it every tick. The agent even types a natural-language "task
is complete" reply, but that is not a signal the watchdog consumes — so the kicking continues until the pane is
reclaimed/re-derived to idle-blocked (as observed by 21:51Z). Contrast a persistent slot worker, which is _supposed_ to
keep polling and so should be kicked when silent; a **one-shot** worker that has done its job should be transitioned to
terminated/idle, not re-kicked.

## Todos

- [ ] [BACKEND] P3. Give a one-shot worker a **clean completion exit path** the watchdog recognises: on task completion
      the agent should signal done (exit its tmux session or post a terminal completion state) and the liveness kicker
      should treat a completed-and-declared one-shot pane as **terminated/idle, not frozen** — so it is not re-kicked.
      **Done when**: a one-shot worker that finishes its task and declares completion is transitioned to
      terminated/idle-free and receives zero further liveness kicks (verified by a lifecycle test simulating "one-shot
      task done, pane still alive").
- [ ] [BACKEND] P3. Have the watchdog **recognise the "task is complete" / "stop nudging" self-declaration** (or a
      structured completion marker) as a completion signal rather than kick-fodder — at minimum, stop re-kicking a pane
      whose own last output declares completion, and instead route it to the completion/redispatch check. **Done when**:
      a pane emitting a completion declaration is not re-kicked on the next liveness tick.

## Triage / charter note

Filed by main (agt-52bb99) per the big-finding triage rule (recurring cross-cutting agent-orchestrator lifecycle
pattern, operator-flagged, 5+ recurrences in ~30min on one slot). Main diagnosed via a **read-only** `/api/state`
inspection of slot 2 and is charter-barred from tmux send-keys to worker panes, from spawning/killing/respawning slots,
and from editing AO runtime state — so the fix is **BACKEND/DEVOPS-owned**. Severity **P3**: every kick self-healed and
nothing was blocked (bounded blast radius = wasted kick churn + masked idleness on one slot), but the pattern is
confirmed, recurrence-prone, and points at a real one-shot-lifecycle exit-signal gap worth closing when cycles allow.
