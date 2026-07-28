---
doc_type: issue
title:
  The context-lifecycle compact_now directive did not fire for a worker slot at its configured threshold — slot 11 rode
  from ~90% to ~96% context_used across 3+ consecutive /progress polls with no compact_now directive ever delivered,
  distinct from the slot-4 "typed-but-wedged" failure class where the directive DID fire.
summary: >-
  On 2026-07-27, the review role (agt review checkpoint) observed slot 11 climb from context_used_pct≈90 to ≈96 across
  3+ successive /progress calls without the context-lifecycle compact_now directive ever being emitted to the slot. This
  is a DIFFERENT failure mode from
  /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md: there the guided
  compact directive fired and the pane wedged with `/compact` typed-but-un-submitted; here the directive appears never
  to have fired at all, so the slot rode well past the guidance threshold with no intervention until (near) the
  client-side auto-compact boundary. Candidate causes to investigate in agent-orchestrator server/context_lifecycle.py +
  worker_liveness: (a) the threshold check (context_compact_guidance_pct, default 50) not evaluating on this slot's
  /progress cadence; (b) a per-slot dedup/once-only guard suppressing re-emission after an earlier missed/dropped
  directive; (c) the slot's reported context_used_pct not being parsed/compared as expected at high values. Bounded
  impact (client auto-compact is the final safety net underneath), but a slot riding 90→96% unguided risks the
  typed-but-wedged class and wastes context headroom. P2.
status: open
assigned_vm:
resolved_by:
locked_by:
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, context-lifecycle, compact, compact-now-directive, worker-liveness, throughput]
related:
  [
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-27
last_updated: 2026-07-27
priority: P2
parent_epic: orchestrator_master
source:
  "review role pre-compact checkpoint (msg 2373 to main agt-498659) reported slot 11 riding 90→96% context_used across
  3+ /progress polls with no compact_now directive; main (agt-498659) captured it here so the finding survives
  compaction (review role never commits)."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## Observation

The review-role agent, running its own pre-compact checkpoint on 2026-07-27, reported that slot 11 rode from
`context_used_pct` ≈90 to ≈96 across **3+ consecutive `/progress` polls** without ever receiving the context-lifecycle
`compact_now` directive.

## Why this is distinct from the slot-4 wedge doc

`/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md` documents a case where
the guided compact directive **fired** and the pane then wedged with `/compact` typed but un-submitted. This finding is
the opposite failure: the directive appears to **never have fired**, so no `/compact` was typed at all and the slot
climbed unguided.

## Suggested investigation (agent-orchestrator, read-only first)

- `server/context_lifecycle.py` — confirm the Tier-1 guided-compact threshold (`context_compact_guidance_pct`,
  default 50) evaluates against this slot's reported `context_used_pct` on every `/progress`, at high values.
- Check for a per-slot once-only / dedup guard that could suppress re-emission after an earlier dropped directive.
- Confirm `context_used_pct` parsing/comparison holds near the top of the range.

## Status / next step

Captured only; **not yet diagnosed**. Needs an owner on the agent-orchestrator side to reproduce from `/progress`
history for slot 11 and confirm which of the candidate causes applies. Low-risk (client auto-compact is the safety net)
but a real throughput/robustness gap.

## Todos

- [ ] [ENGINEER] P2. **Diagnose why the `compact_now` directive never fired for slot 11** — reproduce from `/progress`
      history and confirm which candidate cause (threshold-eval gap, dedup guard, or high-value parsing bug) applies in
      agent-orchestrator's `context_lifecycle.py`; captured only, not yet diagnosed.
