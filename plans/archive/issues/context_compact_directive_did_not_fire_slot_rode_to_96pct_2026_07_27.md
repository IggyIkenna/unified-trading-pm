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
status: resolved
assigned_vm: planning
resolved_by: slot-2
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
last_updated: 2026-07-30
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

> **🗄️ ARCHIVED 2026-07-30** — fully resolved. Root cause diagnosed (missing activity-log record in `progress_slot`'s
> `compact_now` emission, not a logic bug in the gate) and fixed (`agent-orchestrator@b36f5fa`,
> `progress_compact_directive_issued` activity event + regression test, `quality-gates.sh` green). No open todos, no
> Deferred items. Surfaced by `/ag-closeout-audit ao` (2026-07-30) as `assigned_vm: planning`/`status: resolved` but
> never archived. See `## Status / next step` below for the full diagnosis.

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

**Diagnosed + fixed 2026-07-30.** None of the three candidate causes applied — `server/context_lifecycle.py`'s
Tier-1/Tier-2 policy doesn't cover slot 11 at all (that module is scoped to main/review/large-plan-todo workers only;
slot 11 is a plain backlog worker). The actual `compact_now` directive lives in a separate, newer mechanism:
`ProgressResponse.directive` in `server/routes/slots_worker.py::progress_slot`, gated on
`tuning.context_worker_compact_gate_pct` (default 70%), shipped 2026-07-25 (`ao_worker_context_lifecycle_gap` todo 4).

Reproduced slot 11's actual `/progress` history via `GET /api/activity?slot=11` for 2026-07-27: context climbed from 65%
(01:34) to 96% (04:37) over ~3 hours while the slot was continuously stuck in a hot-branch quickmerge rebase/re-gate
retry loop, with no compaction until a manual "STOPPED per main directive" intervention at 04:37 and an actual
compaction at 04:48. The separate `context_burn_suspected` watchdog trigger DID fire correctly at 03:41 (pct=86, 4.85h
since session reset) — that mechanism worked as designed; its kill escalation never engaged because
`context_burn_kill_min_pct` (98%) was never reached before the manual intervention (peaked at 96%).

Root cause: `progress_slot`'s `compact_now` emission had **no activity-log record** — unlike `boot_slot`/
`heartbeat_slot`/`done_slot`, which all log `worker_compact_gated` when they gate on context, the `/progress` hot path
logged nothing when it set `directive="compact_now"`. The server-side gate computation itself was correct on every tick
(`context_worker_directive_repeat_gate` defaults `True`, so it's not a once-only dedup guard, and the threshold
comparison holds at high values) — but with zero audit trail, nobody (review, main, or this diagnosis) could distinguish
"directive sent, worker too deep in a retry loop to act on it" from "directive never sent". That observability gap — not
a logic bug in the gate itself — is what let this incident go undetected by anything except a review agent's manual pane
read.

Fix: `progress_slot` now logs a `progress_compact_directive_issued` activity event (mirroring `worker_compact_gated`)
every time it returns `directive="compact_now"`, closing the blind spot for future incidents.

## Todos

- [x] ✅ [ENGINEER] P2. **Diagnose why the `compact_now` directive never fired for slot 11** — reproduce from
      `/progress` history and confirm which candidate cause (threshold-eval gap, dedup guard, or high-value parsing bug)
      applies in agent-orchestrator's `context_lifecycle.py`; captured only, not yet diagnosed. — RESOLVED: diagnosed as
      a missing activity-log record in `progress_slot` (not any of the three candidate causes, which were framed around
      the wrong module — `context_lifecycle.py` doesn't cover plain workers). Fixed + shipped agent-orchestrator@b36f5fa
      (`progress_compact_directive_issued` activity log + regression test, `quality-gates.sh` green, 2003 passed).
