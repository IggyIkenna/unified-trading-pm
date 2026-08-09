---
doc_type: issue
title: A saturated agent context pages nobody — main sat at 99% for hours and the operator found it by eye
summary: >-
  orch-agent-main held 99% context for hours on 2026-08-09 with every compaction threshold silently disarmed, and
  nothing alerted. The condition was visible the whole time in the dashboard and in AgentRow.context_used_pct, and it is
  exactly the class the AO alerting SSOT says should page (a failure, not a lifecycle event), but no detector exists.
  Detection came from the operator noticing a red bar. A "session above N% with no context_compact_observed for M
  minutes" detector would have caught it in minutes instead of hours, and would equally have caught the two prior
  incidents in this family (slot 3 sailing to the hard limit, slots 7/12 pinned at 100%).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, context, compaction, alerting, observability]
related:
  [
    /plans/archive/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
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

The 2026-08-09 root cause (a poisoned learned context window) is fixed. But the _detection_ story is the durable lesson:
the failure was a **silent disarm** — a safety net that reported nothing at all, in a system whose health signal for
that net is "events appear in the activity log". Zero events is indistinguishable from "nothing needed doing" unless
something is explicitly watching for the absence.

This family has now produced at least four incidents with the same detection gap:

- slot 3 sailing from 60% to the model's hard limit with the "unconditional" force silently latched off
  (`ao_worker_context_saturation_unrecoverable_2026_08_06`)
- slots 7/12 pinned at 100% for hours while `forced_compact` fired repeatedly
  (`ao_worker_context_lifecycle_gap_directive_gap`)
- orch-slot-21 taking five forced compacts, all reporting `submitted=True`, with context never falling
  (`/plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md`)
- orch-agent-main at 99% for hours with zero events logged (2026-08-09)

Every one was found by a human reading a dashboard or an activity dump.

Per `/codex/04-architecture/agent-orchestrator-alerting.md` the `agent-orchestrator-alerts` channel is actionable-only:
automatic lifecycle events (dispatches, respawns, recoveries) never page, but **failures do**. A compaction safety net
that cannot compact is a failure, not a lifecycle event.

## Todos

- [x] ✅ [BACKEND] P1. Add a saturation detector to the keeper tick: any target (main, review or worker) whose
      `context_used_pct` has been at or above a configurable threshold (default: `resume_fresh_context_pct`) for longer
      than a configurable window with NO `context_compact_observed` in that window. Done-when: a unit test proves it
      fires for a target pinned high with no compaction, and does NOT fire for one that compacted inside the window. —
      `agent-orchestrator@bb81c7b`: pure predicate `_is_saturated_without_compaction` +
      `ContextLifecyclePolicy._tick_saturation_detector` (runs for every target — main/review/worker — every keeper
      tick, per the module's existing `_tick_target` loop), gated on new `TuningDefaults.context_saturation_alert_pct`
      (default 0 → falls back to `resume_fresh_context_pct`, per this todo's own instruction) +
      `context_saturation_alert_window_seconds` (default 1800s). Logs a state-transition-deduped
      `context_saturation_detected` / `context_saturation_detected_resolved` activity event pair (fires once per streak,
      not per tick); deliberately does NOT page Slack itself — that routing is todo 2 of this same issue, kept as a
      separate change to avoid two P1 todos racing on this same file under AO's concurrent-dispatch model. 6 new tests
      in `tests/test_context_lifecycle.py` cover both explicit done-when clauses plus the dedup/resolve transition.
- [x] ✅ [BACKEND] P1. Route it to `agent-orchestrator-alerts` as a standing condition with state-transition dedup —
      fire on change, RESOLVED when it clears, re-remind on the standard cadence, never every tick — and give it the ✅
      CLOSE bookend the alerting SSOT requires for any actionable alert that paged an OPEN. Done-when: a test asserts
      one page per transition (not per tick) and an explicit resolve. — `agent-orchestrator@e8818aa`:
      `notify_context_saturation_detected` / `notify_context_saturation_resolved` added to
      `server/notifications/slack.py` (mirrors the established `notify_git_staleness_red`/`_resolved` pattern — deep
      link, `is_reminder` distinguishes a persisting episode from a fresh page, RESOLVED bookend correlates via an
      `opened_at` "closes the saturation alert opened `<ts>`" line). `ContextLifecyclePolicy._tick_saturation_detector`
      now pages on first detection, re-reminds every `context_saturation_realert_seconds` (pre-added knob, default 4h)
      while still saturated via new `_TargetState.saturation_opened_at`/`saturation_last_paged_at` fields, and posts the
      CLOSE bookend only when the episode actually paged — todo 1's own `context_saturation_detected`/`_resolved`
      activity-log dedup latch is untouched (still fires exactly once per streak). 4 new tests: 2 in
      `tests/test_context_lifecycle.py` (one-page-per-transition + reminder-on-cadence; resolved bookend correlates to
      the original page and only fires after one) + 2 in `tests/test_alert_quality_overhaul.py` (direct `_post`-capture
      proof the notifiers actually page, mirroring `test_git_staleness_red_pages_with_summary`). All green;
      `basedpyright` clean on the 4 touched files. Todos 3-4 intentionally NOT touched — separate dispatch per this
      issue's own scope.
- [ ] [BACKEND] P2. Add the inverse detector for the silent-disarm shape specifically: no context-lifecycle activity
      event of ANY type for a given role for longer than a configurable window while that role has a live session. This
      is the check that would have caught 2026-08-09 directly (`role=main` logged 1 event in 4.3h against
      `role=worker`'s 132). Done-when: a unit test proves it fires on an all-quiet role with a live session.
- [x] ✅ [DOCS] P2. Register both detectors in the alerting SSOT's failure-mode table with owner / cadence / verifier,
      per the runbook declaration rule. Done-when: `/codex/04-architecture/agent-orchestrator-alerting.md` lists them. —
      `unified-trading-pm`: added a new "Self-monitoring detector registry — owner / cadence / verifier" section (per
      `/codex/15-runbooks/README.md`'s owner/cadence/verifier declaration rule) plus two new rows
      (`notify_context_saturation_detected`/`_resolved`) in the existing "Complete pager audit" table. Todo 1/2's
      detector is registered in full (owner, cadence = every `ContextLifecyclePolicy.tick` at
      `main_agent_interval_seconds`=60s, verifier = the 10 existing tests across `test_context_lifecycle.py` +
      `test_alert_quality_overhaul.py`, code_refs `@bb81c7b`/`@e8818aa`). Todo 3's detector doesn't exist in code yet
      (`ao_context_saturation_never_alerts-0c1b3343f4c1`, dispatched to slot 31 at 2026-08-09T19:22 UTC, still in flight
      at time of writing) — its row is registered now too (name, owner, trigger shape) with cadence/verifier honestly
      marked **PENDING** rather than fabricated, so the registry itself never silently omits a detector this issue says
      should exist. See todo 5 below for the backfill.
- [ ] [DOCS] P3. Backfill the context-activity-silence detector's cadence/verifier/code_refs in
      `/codex/04-architecture/agent-orchestrator-alerting.md` § "Self-monitoring detector registry" once
      `ao_context_saturation_never_alerts-0c1b3343f4c1` (todo 3) ships — replace the PENDING row with real values
      mirroring the completed detector-1 row. Done-when: the table has no PENDING cells left in that section.

## Progress Log

- 2026-08-09 — Filed after the main-agent incident was found by eye rather than by an alert. The four prior incidents
  listed above were all found the same way, which is what makes this a detector gap rather than a one-off.
- **2026-08-09 (backend_engineer, slot-12)** — ✅ Todo 1 shipped. Added `_is_saturated_without_compaction` (pure
  predicate, mirrors the existing `_is_effective_compaction_drop` pattern) + `_tick_saturation_detector`
  (`ContextLifecyclePolicy`), 2 new `TuningDefaults` knobs (`context_saturation_alert_pct`,
  `context_saturation_alert_window_seconds`) plus 2 more pre-added for todos 2/3 (`context_saturation_realert_seconds`,
  `context_activity_silence_alert_seconds`) so those follow-ups don't need a config-only re-touch of this same section.
  `_TargetState` gained `saturation_since`/`saturation_alert_logged`; a real compaction (the existing
  `_is_effective_compaction_drop` block) resets `saturation_since`, which is how a target that compacted mid-window
  correctly never fires even though `pct` itself never dropped. 6 new tests, all green; `basedpyright` clean on the 3
  touched files. Todos 2-4 intentionally NOT touched — left for their own separate dispatch per the task's own scope
  (todo 2 was still `queued`, not `dispatched`, at pickup time; same-file concurrent-dispatch risk).
- **2026-08-09 (backend_engineer, slot-20)** — ✅ Todo 2 shipped. `notify_context_saturation_detected` /
  `notify_context_saturation_resolved` added to `server/notifications/slack.py`, mirroring the established
  `notify_git_staleness_red`/`_resolved` pattern (deep link, `is_reminder` flag for a persisting episode, RESOLVED
  bookend with a "closes the saturation alert opened `<ts>`" correlation line). `_tick_saturation_detector` now pages on
  first detection and re-reminds every `context_saturation_realert_seconds` (the knob todo 1 pre-added, default 4h)
  while still saturated, via two new `_TargetState` fields (`saturation_opened_at`, `saturation_last_paged_at`) layered
  on top of — not replacing — todo 1's per-streak activity-log dedup latch, so `context_saturation_detected` itself
  still fires exactly once per streak. The CLOSE bookend only fires for an episode that actually paged (mirrors
  `notify_escalation_resolved`'s "no page, no bookend" rule). 4 new tests: 2 in `tests/test_context_lifecycle.py`
  (one-page-per-transition + reminder-on-cadence; resolved bookend correlates + only-after-a-page) and 2 in
  `tests/test_alert_quality_overhaul.py` (direct `_post`-capture proof the notifiers actually page). All green;
  `basedpyright` clean. Todos 3-4 intentionally NOT touched — separate dispatch per this issue's own scope.
- **2026-08-09 (backend_engineer, slot-30)** — ✅ Todo 4 shipped, ➕ todo 5 added. Registered detector 1 (todo 1/2's
  saturation-without-compaction detector) in full in `/codex/04-architecture/agent-orchestrator-alerting.md`: two new
  rows in the existing "Complete pager audit" table for `notify_context_saturation_detected`/`_resolved`, plus a new
  "Self-monitoring detector registry — owner / cadence / verifier" section applying the runbook declaration rule
  (`/codex/15-runbooks/README.md`) to both of this issue's detectors. Todo 3's detector (dispatched concurrently to slot
  31, `ao_context_saturation_never_alerts-0c1b3343f4c1`) had not landed in code as of this session — rather than
  fabricate its cadence/verifier or silently drop it from the registry, its row is registered now by name/owner/trigger
  shape with cadence and verifier honestly marked PENDING, and todo 5 tracks the backfill once todo 3 ships. This is the
  deliberate reading of "register both" given the two todos were dispatched without a `sequential`/`depends_on` gate
  between them (a plan-authoring gap worth noting for future same-issue todo chains) — todo 4's own done-when ("lists
  them") is satisfied literally; todo 5 closes the remaining gap.
