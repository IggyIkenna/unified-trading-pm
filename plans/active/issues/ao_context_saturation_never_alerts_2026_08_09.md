---
doc_type: issue
title: A saturated agent context pages nobody — main sat at 99% for hours and the operator found it by eye
summary: >-
  orch-agent-main held 99% context for hours on 2026-08-09 with every compaction threshold silently disarmed, and
  nothing alerted. The condition was visible the whole time in the dashboard and in AgentRow.context_used_pct, and it
  is exactly the class the AO alerting SSOT says should page (a failure, not a lifecycle event), but no detector
  exists. Detection came from the operator noticing a red bar. A "session above N% with no context_compact_observed
  for M minutes" detector would have caught it in minutes instead of hours, and would equally have caught the two
  prior incidents in this family (slot 3 sailing to the hard limit, slots 7/12 pinned at 100%).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, context, compaction, alerting, observability]
related:
  [
    /plans/active/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
    /plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
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
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Operator observation 2026-08-09 — the incident was found by looking at the dashboard, not by an alert.
depends_on: []
context_scope:
  [
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/notifications,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
---

# A saturated agent context pages nobody

## Why this matters more than the individual bug

The 2026-08-09 root cause (a poisoned learned context window) is fixed. But the *detection* story is the durable
lesson: the failure was a **silent disarm** — a safety net that reported nothing at all, in a system whose health
signal for that net is "events appear in the activity log". Zero events is indistinguishable from "nothing needed
doing" unless something is explicitly watching for the absence.

This family has now produced at least four incidents with the same detection gap:

- slot 3 sailing from 60% to the model's hard limit with the "unconditional" force silently latched off
  (`ao_worker_context_saturation_unrecoverable_2026_08_06`)
- slots 7/12 pinned at 100% for hours while `forced_compact` fired repeatedly
  (`ao_worker_context_lifecycle_gap_directive_gap`)
- orch-slot-21 taking five forced compacts, all reporting `submitted=True`, with context never falling
  (`/plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md`)
- orch-agent-main at 99% for hours with zero events logged (2026-08-09)

Every one was found by a human reading a dashboard or an activity dump.

Per `/codex/04-architecture/agent-orchestrator-alerting.md` the `agent-orchestrator-alerts` channel is
actionable-only: automatic lifecycle events (dispatches, respawns, recoveries) never page, but **failures do**. A
compaction safety net that cannot compact is a failure, not a lifecycle event.

## Todos

- [ ] [BACKEND] P1. Add a saturation detector to the keeper tick: any target (main, review or worker) whose
      `context_used_pct` has been at or above a configurable threshold (default: `resume_fresh_context_pct`) for
      longer than a configurable window with NO `context_compact_observed` in that window. Done-when: a unit test
      proves it fires for a target pinned high with no compaction, and does NOT fire for one that compacted inside the
      window.
- [ ] [BACKEND] P1. Route it to `agent-orchestrator-alerts` as a standing condition with state-transition dedup — fire
      on change, RESOLVED when it clears, re-remind on the standard cadence, never every tick — and give it the ✅
      CLOSE bookend the alerting SSOT requires for any actionable alert that paged an OPEN. Done-when: a test asserts
      one page per transition (not per tick) and an explicit resolve.
- [ ] [BACKEND] P2. Add the inverse detector for the silent-disarm shape specifically: no context-lifecycle activity
      event of ANY type for a given role for longer than a configurable window while that role has a live session.
      This is the check that would have caught 2026-08-09 directly (`role=main` logged 1 event in 4.3h against
      `role=worker`'s 132). Done-when: a unit test proves it fires on an all-quiet role with a live session.
- [ ] [DOCS] P2. Register both detectors in the alerting SSOT's failure-mode table with owner / cadence / verifier, per
      the runbook declaration rule. Done-when: `/codex/04-architecture/agent-orchestrator-alerting.md` lists them.

## Progress Log

- 2026-08-09 — Filed after the main-agent incident was found by eye rather than by an alert. The four prior incidents
  listed above were all found the same way, which is what makes this a detector gap rather than a one-off.
