---
doc_type: issue
title: Review agents' context signal has no fresh source — they never heartbeat and are excluded from the out-of-band sample
summary: >-
  A review agent's context_used_pct comes from its SlotRow, but review agents never post to
  /api/slots/<N>/heartbeat at all (worker_liveness says so explicitly), so the column only advances via the
  separately-scheduled, spinner-gated pane sample in WorkerLivenessKicker. The 2026-08-08 out-of-band same-tick pane
  read that fixed exactly this latency class for workers was deliberately NOT extended to review, and review's force
  path is idle-gated on top. Live 2026-08-09: a 4.3h /api/activity window held ZERO context-lifecycle events for
  role=review — the same silence that preceded the main-agent incident, and with the same shape of cause (no fresh,
  self-owned measurement source).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, context, compaction, review-agent, worker-lifecycle]
related:
  [
    /plans/active/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
    /plans/active/issues/ao_main_review_force_compact_idle_gate_unreachable_2026_08_09.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
created: 2026-08-09
last_updated: "2026-08-09"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: fix-regression
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Surfaced 2026-08-09 while root-causing the main-agent poisoned-window incident (slot 4 interactive session); review
  was the third role in the same activity census and was equally silent.
depends_on: []
context_scope:
  [
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/worker_liveness/__init__.py,
    /plans/active/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
  ]
---

# Review agents' context signal has no fresh, self-owned source

## The gap

`context_lifecycle._read_pct` treats review as slot-bound and reads `SlotRow.context_used_pct` straight from the DB.
For a task worker that value is genuinely self-reported (every `/progress`, `/done`, `/heartbeat` posts it). For a
review agent it is not: `server/worker_liveness/__init__.py` states in its own comment that a slot-bound review agent
*"never posts to `/api/slots/<N>/heartbeat` at all"*. So review's column can only ever advance through
`WorkerLivenessKicker`'s separately-scheduled, spinner-gated pane sample.

The 2026-08-08 fix (`ao_worker_context_force_compact_blind_to_tool_heavy_stretches`) added a same-tick, out-of-band
pane read inside `_read_pct` precisely because depending on another subsystem's cadence let a session climb
un-compacted. That fix was scoped to workers on purpose — `_read_pct`'s docstring says *"Review is deliberately NOT
extended here — its force path stays idle-gated and already has no lower-latency need for this; keeping the blast
radius to exactly the diagnosed gap."*

That reasoning is now questionable for two measured reasons:

1. The main-agent incident (2026-08-09) showed exactly what happens to a role whose only context signal is a
   second-hand one — 4.3 hours of silence and a run to the model's hard limit.
2. In the same 4.3h census, `role=review` logged **zero** context-lifecycle events, versus 132 for workers. As with
   main, that silence is currently AMBIGUOUS — it may mean review never crossed 60%, or that its signal never moved.
   Nothing distinguishes those today, which is itself the defect.

## Todos

- [ ] [BACKEND] P1. Measure the staleness directly: for every review slot, compare `SlotRow.context_used_pct` against
      a fresh `context_probe` read of the same session, and record both plus the age of the last write to the column.
      Done-when: the Progress Log carries the DB-vs-measured delta for each review slot over at least 3 samples an
      hour apart.
- [ ] [BACKEND] P1. Give review a fresh, self-owned source on the policy's own cadence — extend `_read_pct`'s
      same-tick out-of-band read to `role == "review"` (a plain context%% parse, never `classify_pane` /
      `_pane_has_child_processes`, so review's idle-VERDICT contract is untouched), persisting ratchet-up only exactly
      as the worker path does. Done-when: a unit test proves a review target whose SlotRow is stale still reads the
      measured value, and `tests/test_context_lifecycle.py`'s idle-check ban still passes.
- [ ] [BACKEND] P2. Emit a `context_signal_stale` activity event when any target's stored pct has not moved for longer
      than a configurable window while its transcript shows the session growing. Done-when: the event fires in a unit
      test for a frozen-column target and is visible in `GET /api/activity`.

## Progress Log

- 2026-08-09 — Filed alongside the main-agent poisoned-window incident. Review was the third role in that census and
  logged zero context-lifecycle events over 4.3 hours; the cause is unconfirmed (todo 1 disambiguates) but the missing
  fresh source is structural and independent of whether review happened to cross a threshold in that window.
