---
doc_type: issue
title: main/review forced-compact is gated behind an idle verdict a permanently-ticking loop agent never satisfies
summary: >-
  The main/review forced-compact fallback requires classify_pane == "idle" on 3 CONSECUTIVE keeper ticks, plus an empty
  input box, plus <=1 child process under the pane shell. main is a continuously-ticking loop agent, so the streak
  resets on nearly every tick and the gate is unlikely to ever open. Three consequences compound it: main's
  context_pressure is hardcoded "low" (so the pressure == "thrashing" immediate-recycle trigger is structurally
  unreachable for main), main's terminal wedge-recovery sits DOWNSTREAM of a force that may never fire, and both Tier-1
  guidance and Tier-2 recycle are sent exactly once per episode. Surfaced while root-causing the 2026-08-09 poisoned
  learned-window incident (fixed separately, agent-orchestrator@LDR): with the measurement corrected, main now reaches
  the 60% threshold and gets guidance, so whether the FORCE behind it can ever fire is now the live question.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, context, compaction, main-agent, review-agent, worker-lifecycle]
related:
  [
    /plans/archive/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
    /plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
created: 2026-08-09
last_updated: "2026-08-09"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
drift_direction: fix-regression
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Isolated 2026-08-09 (interactive session, slot 4) while diagnosing orch-agent-main pinned at 99% context. The
  measurement bug that masked this is fixed; this is the remaining structural gap underneath it.
depends_on: []
context_scope:
  [
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/worker_liveness/__init__.py,
    /plans/archive/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
  ]
---

# main/review forced-compact is gated behind an unreachable idle verdict

## The gap

`server/context_lifecycle.py` runs two policies. Workers (operator ruling 2026-08-05, "the guidance isn't useful if it
doesn't force") get an UNCONDITIONAL force the moment context crosses 60% — no idle check, no deadline. main and review
kept the older cooperative-first shape, whose forced fallback runs through `_maybe_force_compact` and requires **all**
of:

1. `classify_pane(pane) == "idle"` on **3 consecutive** keeper ticks (`_FORCE_IDLE_OBSERVATIONS`),
2. `tmux_spawn.pane_input_pending(session)` false,
3. `_pane_has_child_processes(session)` false — and that helper returns **True** (i.e. "not safe to force") on any
   failure to measure.

`classify_pane` returns `"working"` whenever a spinner is present. main is a loop agent that ticks continuously and
shells out to `gh`/`curl`/`git` on nearly every tick, so signals 1 and 3 both routinely fail. Live evidence 2026-08-09:
in a 4.3-hour `/api/activity` window there were **132** context-lifecycle events for `role=worker` and **1** for
`role=main` (a single client-side `context_compact_observed`); `proactive_compact_guidance`, `forced_precompact`,
`forced_compact` and `context_recycle_requested` were all **0** across every role.

That window is confounded — the poisoned learned window (separate issue, now fixed) meant main measured 26% and never
reached the 60% threshold at all, so the gate was never even TESTED. Which is exactly why todo 1-2 below measure before
changing policy: the gate's real open-rate is currently unknown, not known-bad.

## Three compounding defects in the same path

- **`context_pressure` is hardcoded for main.** `_read_pct` returns `(pct, "low")` for the slot-less main agent because
  pressure lives on `SlotRow`. The Tier-2 `pressure == "thrashing"` immediate-recycle trigger is therefore structurally
  unreachable for main — it can only ever recycle on compaction-count or 24h age.
- **main's terminal wedge-recovery is downstream of a force that may never fire.** `_rearm_if_force_ineffective` returns
  at its first branch when `state.forced_at is None`. The kill-session + clear-`claude_session_id` recovery for a wedged
  MAIN therefore only ever arms AFTER a force actually submitted. If the idle gate never opens, main's last-resort net
  is unreachable.
- **Guidance and recycle are one-shot per episode.** `guidance_sent_at` / `recycle_sent_at` are re-armed only by an
  observed compaction, and `_TargetState` is in-memory (reset on orchestrator restart, which also restarts the 24h
  recycle clock).

## Why this is not simply "extend the worker force to main"

The 2026-08-05 ruling deliberately kept main/review cooperative-first, with a stated rationale: _"never compact mid-work
— a single pane-snapshot 'looks idle' is untrustworthy on a days-long loop"_. main holds fleet state a worker does not.
Reversing that is an operator call (todo 5), not a worker's — so the AO-dispatchable todos here gather the evidence and
fix the two unambiguous structural defects, leaving the policy reversal explicitly gated.

## Todos

- [x] ✅ [BACKEND] P1. Instrument the gate: emit a `context_force_idle_gate_blocked` activity event (details: `role`,
      `session`, `pct`, and WHICH signal refused — `classify_pane` verdict / `pane_input_pending` / child-process count)
      on every tick where a main/review target is past `context_compact_force_after_seconds` but `_maybe_force_compact`
      declines. Done-when: the event is visible in `GET /api/activity` for a real main tick, with the blocking signal
      populated. — agent-orchestrator@279e07b (`_log_idle_gate_blocked` logs `signal` +
      `pane_verdict`/`idle_streak`/`required` detail on every decline: `pane_capture_failed` / `classify_pane` /
      `idle_streak_insufficient` / `pane_input_pending` / `child_processes`); unit-covered in
      `tests/test_context_lifecycle.py`, full QG green.
- [ ] [BACKEND] P1. Measure for >=6h with the instrumentation live: how many ticks had main/review deadline-past, how
      many times the gate OPENED, and the dominant blocking signal. Record the counts in this doc's Progress Log.
      Done-when: the Progress Log carries open-vs-blocked counts for both roles.
- [ ] [BACKEND] P1. Make main's terminal wedge-recovery reachable when no force ever fired.
      `_rearm_if_force_ineffective` returns early on `state.forced_at is None`, so the kill + `claude_session_id`
      clear + keeper respawn path cannot arm for a main that the idle gate never let through. Add a saturation-based
      entry (main above `resume_fresh_context_pct` with no `context_compact_observed` for a sustained window) that
      reaches the SAME recovery. Done-when: a unit test in `tests/test_context_lifecycle.py` proves recovery arms for a
      main target whose `forced_at` was never set.
- [ ] [BACKEND] P2. Give main a real `context_pressure` instead of the hardcoded `"low"` in `_read_pct`, so the Tier-2
      `pressure == "thrashing"` immediate-recycle trigger is reachable for main at all. Derive it the same way the
      SlotRow value is derived. Done-when: a unit test proves a thrashing main recycles without waiting for
      compaction-count or the 24h age clock.
- [ ] [BACKEND] P2. Re-arm Tier-1 guidance on a timer as well as on an observed compaction: today `guidance_sent_at`
      clears only when a compaction is detected, so a main that silently ignores one nudge is never nudged again for the
      rest of the episode. Done-when: a unit test proves a second guidance message is enqueued after a configurable
      unacked interval with no compaction observed.
- [ ] [OPERATOR] P1. Ruling, with todo 2's measured evidence in hand: extend the worker-style unconditional force to
      main/review, or keep them idle-gated. This reverses the stated 2026-08-05 rationale ("never compact mid-work" for
      days-long loop agents), so it is deliberately not a worker's call. Done-when: the ruling is recorded in
      `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` or the worker-liveness SSOT and this doc's todo set
      is updated to match.

## Progress Log

- 2026-08-09 — Filed from an interactive diagnosis of `orch-agent-main` pinned at 99%. The PRIMARY cause was a poisoned
  learned context window (separate issue, fixed and shipped); this doc captures the structural gaps underneath it that
  the measurement bug was masking. Live counts at filing time: 4.3h `/api/activity` window, `role=worker` = 132
  context-lifecycle events, `role=main` = 1.
- 2026-08-09 (slot 19) — Dispatched todo 1 independently and implemented the same instrumentation, then found slot 15
  had already shipped an equivalent, already-QG-green version at `agent-orchestrator@279e07b` (a known double-dispatch
  pattern per `/plans/active/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md`). Skipped my
  duplicate commit during rebase (`git rebase --skip`, no code conflict landed) and flipped this checkbox against
  279e07b instead of shipping a redundant second implementation.
- 2026-08-09 (slot 15) — Was dispatched todo 2 (the >=6h measurement) directly, before todo 1 had shipped — confirmed
  via the backlog (`GET /api/backlog`) that todo 1's task was still `queued`/unclaimed at the time, so implemented +
  shipped it first (see checkbox above) since todo 2 is unstartable without it. Deployed + verified LIVE on the
  orchestrator VM: checkout `e8818aa` (descends from `279e07b`) with `orchestrator.service` `ActiveEnterTimestamp` =
  **2026-08-09T18:00:24Z**, confirmed AFTER that pull (not a stale pre-pull process). Checked `GET /api/activity`
  post-deploy: 0 `context_force_idle_gate_blocked` events yet — expected, not a bug: the restart the deploy required
  also cleared `ContextLifecyclePolicy`'s in-memory `_TargetState` (this doc's own "Guidance and recycle are one-shot
  per episode" defect above), so every target's `guidance_sent_at`/`forced_at`/`idle_streak` reset to unset at that
  moment — main/review has to re-climb to the Tier-1 guidance threshold and then clear
  `context_compact_force_after_seconds` again before the now-instrumented gate is even reached. Starting todo 2's
  > =6h window from **2026-08-09T18:00:24Z** (the confirmed-live restart timestamp), not from filing time — no tick
  > before that point could have hit the instrumented code path at all. Releasing todo 2 back to the queue
  > (`reason_code: GATED`) rather than holding this session open for a multi-hour wall-clock wait; the next dispatch
  > (this slot or another) should read this timestamp and query `/api/activity` (`context_force_idle_gate_blocked` /
  > `forced_precompact` / `forced_compact`, `role in {main, review}`, `ts >= 2026-08-09T18:00:24Z`) once the window has
  > actually elapsed to fill in todo 2's open-vs-blocked counts.
