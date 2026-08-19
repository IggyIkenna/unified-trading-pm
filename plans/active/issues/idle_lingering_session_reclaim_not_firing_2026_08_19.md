---
doc_type: issue
title: >-
  `_reclaim_idle_lingering_sessions` not firing — completed one-shot dispatches leave live
  tmux sessions running for hours, silently shrinking the scheduled-task slot reserve
summary: >-
  Confirmed live 2026-08-19: three scheduled-job (`ag_closeout_auditor`) dispatches on slots
  28/29/30 completed successfully hours earlier (results shipped to
  `unified-trading-pm@ae65a23c08`, each worker's own log says "Completion signaled to the
  orchestrator; slot freed") — the SlotRow status correctly flipped to `idle`, but the
  underlying tmux session was never torn down. `tmux list-sessions` shows all three sessions
  still alive 4+ hours later (created 13:22-13:24 UTC, observed live at ~17:40 UTC), each
  sitting at an interactive Claude Code prompt. This is NOT a missing-teardown bug — reading
  `server/routes/slots_worker.py::_done_one_off`'s own docstring, async teardown is deliberate
  design: "the agent stops on its own after this returns... it reaps the lingering session on
  its next tick." The dedicated reclaim mechanism for exactly this case,
  `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions` (`server/worker_liveness_watchdog.py`),
  already exists, is already generic across every one-shot dispatch family (its own docstring
  names review/escalate/conflict_resolver, and the query itself is un-filtered by agent_kind so
  scheduled/plan_health dispatches are in scope by construction) — but is confirmed NOT
  reclaiming these 3 within a timeframe that matters. Root cause not yet found — this is the
  open investigation.

  Operational impact discovered alongside: this is WHY the 4-slot scheduled-task reserve
  (`scheduled_task_reserved_slot_ids()`, slots 27-30 at time of writing) was only delivering 1
  effective slot (27) — `_pick_free_slot`'s live `tmux_spawn.has_session()` check correctly (from
  its own narrow view) treats 28/29/30 as occupied, so new scheduled-job dispatches fell through
  to the general slot pool instead (confirmed: `ag_closeout_auditor` tranches ao/ui/ci/sports
  landed on ordinary slots 1/4/7/14, competing with regular plan-task throughput instead of using
  the reserve built specifically to avoid that).
status: open
resolved_by:
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, tmux, slot-lifecycle, worker-liveness-watchdog, scheduled-jobs, orphaned-session]
related:
  [
    /plans/active/issues/worker_slot_account_exhaustion_no_rotation_2026_08_19.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/config.py,
    agent-orchestrator/server/plan_health.py,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Interactive session 2026-08-19 (slot 3) — surfaced while investigating why the scheduled-task
  slot reserve (27-30) wasn't being used for new `ag_closeout_auditor` dispatches; operator asked
  directly why the reserve wasn't working, which led to finding 3 of the 4 reserved slots had
  orphaned live sessions from earlier completed work.
assigned_role: infra
drift_direction: correct-codex
---

# `_reclaim_idle_lingering_sessions` not firing — orphaned sessions on completed dispatches

## What was measured

Live state as of 2026-08-19 ~17:40 UTC (SSM read-only queries against the orchestrator VM's
`state.db`, plus a direct `tmux list-sessions`/`capture-pane` check):

| slot | `SlotRow.status` | `tmux_session` (DB) | live tmux session? | session created | age at observation |
| ---- | ----------------- | -------------------- | ------------------- | ----------------- | ------------------- |
| 28   | `idle`            | `orch-slot-28`        | **yes**              | 13:22:18 UTC       | ~4h18m               |
| 29   | `idle`            | `orch-slot-29`        | **yes**              | 13:23:18 UTC       | ~4h17m               |
| 30   | `idle`            | `orch-slot-30`        | **yes**              | 13:24:57 UTC       | ~4h15m               |

`tmux capture-pane -t orch-slot-28` shows the worker's OWN log confirming a clean completion:

```
All three docs passed frontmatter/todo-format/line-cap/delete-safety/finalize-coverage
validation and shipped to unified-trading-pm@ae65a23c08. Completion signaled to the
orchestrator; slot freed.

✻ Baked for 35m 22s
────────────────────────────────────────────────────────────────
❯ check status
────────────────────────────────────────────────────────────────
  ⏵⏵ bypass permissions on (shift+tab to cycle) · ← for agents
```

The worker genuinely finished, genuinely signaled `/done`, and the SlotRow genuinely shows
`idle` — but the Claude Code CLI process is still running, sitting at an interactive prompt,
hours later.

## Why this isn't a "missing teardown" bug

`server/routes/slots_worker.py::_done_one_off` (the completion handler) documents the async
teardown as deliberate:

> It deliberately does NOT kill the tmux session synchronously: the agent stops on its own
> after this returns, and because the AgentRow is now `archived` the idle-lingering reclaim is
> no longer carve-out-exempted (`f641968`) — it reaps the lingering session on its next tick and
> AutoSpawn reuses the slot.

The catch-mechanism this refers to, `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions`
(`server/worker_liveness_watchdog.py:1452`), is real, already-shipped code:

- Queries every `SlotRow` with `status IN ('idle', 'stale')` — no `agent_kind`/dispatch-family
  filter, so review, escalate, conflict_resolver, AND scheduled/plan_health one-offs
  (`ag_closeout_auditor` etc.) are ALL in scope by construction, per its own docstring
  ("A one-shot review/escalate/conflict_resolver posts /done... the claude process does NOT
  exit").
- Skips review slots, the fresh-spawn boot-grace window, and (for `stale` only) a pane that's
  actively thinking.
- Increments a disk-persisted per-`(slot_id, last_spawned_at)` tick counter every time it finds
  the SAME lingering session; once the counter reaches `_IDLE_SESSION_RECLAIM_TICKS`, it calls
  `kill_session()` and resets the slot via `reset_slot_worker_state`.

Given slots 28/29/30's `last_spawned_at` has stayed constant across multiple checks spanning
over an hour (ruling out the key silently changing and resetting the counter), and given
4+ hours is far longer than any reasonable tick-count threshold should take to reach, this
points at one of a few real possibilities — **none confirmed yet**:

1. The `WorkerLivenessWatchdog` loop itself may not be ticking (a bigger, more urgent finding
   than a narrow function bug, if true).
2. `_IDLE_SESSION_RECLAIM_TICKS` may be set far higher than intended, or a per-tick interval
   change elsewhere may have silently stretched the effective wait far past what the
   original design assumed.
3. Something specific to `ag_closeout_auditor`/`plan_health`-family one-offs (as opposed to
   review/escalate) may exempt them from this reclaim despite the query itself being generic —
   e.g. `spawn_base_role` still being set (checked at `_pick_free_slot` time) is a DIFFERENT
   field with a DIFFERENT release-point set than what this reclaimer checks; worth confirming
   these don't interact unexpectedly.

## Operational impact

This is the confirmed root cause of a separate live symptom: the scheduled-task slot reserve
(`config.scheduled_task_reserved_slot_ids()`, currently resolving to slots 27-30) was only
delivering 1 of its 4 slots (27) to new scheduled-job dispatches. `_pick_free_slot`
(`server/plan_health.py`) already has a same-day fix (`ao_fleet_regression_triad_2026_08_16`
Finding 1) to PREFER the reserved pool when free — but 28/29/30 never look free to it, because
`tmux_spawn.has_session()` is a live, real-time check and these sessions are genuinely still
alive. New `ag_closeout_auditor` tranches (ao/ui/ci/sports) fell through to the general slot
pool instead — landing on slots 1/4/7/14, competing with ordinary plan-task throughput instead
of using the capacity specifically reserved to avoid that competition.

## Follow-up

- [ ] [BACKEND] P2. **Root-cause why `_reclaim_idle_lingering_sessions` has not reclaimed slots
      28/29/30 after 4+ hours.** Check first whether `WorkerLivenessWatchdog`'s tick loop is
      genuinely running at all (recent activity-log entries attributable to it, e.g. any
      `idle_lingering_session_reclaim` event fired recently for ANY slot) before assuming the
      bug is narrow to this function. If the loop is ticking, inspect the disk-persisted
      per-slot tick-counter state (`dedup_state.watchdog_idle_session_ticks_path`) directly for
      these 3 keys to see whether the counter is accumulating, stuck, or absent entirely.
- [ ] [BACKEND] P2. **Fix the confirmed root cause** once found. Add/extend test coverage in
      whichever test file already covers `_reclaim_idle_lingering_sessions`
      (`tests/test_worker_liveness_watchdog.py` or similar — locate via grep before assuming a
      new file is needed) for the specific failure mode found.
- [ ] [OPERATOR] P3. **Kill the 3 currently-orphaned sessions** (`orch-slot-28/29/30`) as
      immediate remediation, separate from the code fix — their work is confirmed already
      shipped (`unified-trading-pm@ae65a23c08`), nothing is lost by reclaiming them manually.
      Not done in this session — flagged for operator action or a follow-up session, since a
      manual `tmux kill-session` bypasses the reclaimer this issue is about auditing, and doing
      it silently would remove the live repro case before the root-cause todo above is done.
- [ ] [BACKEND] P3. **Once root-caused, sweep for any OTHER slots in the same state** (not just
      27-30) — this session only checked the 4 slots in the scheduled-task reserve because that
      is what surfaced the finding; the same gap, wherever it is, plausibly affects any
      completed one-shot dispatch fleet-wide (review/escalate/conflict_resolver included, per
      the reclaimer's own documented scope), not just `ag_closeout_auditor`.

## Codex SSOTs

- `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` — capacity sizing / reserve
  mechanism this bug's operational impact hits.
