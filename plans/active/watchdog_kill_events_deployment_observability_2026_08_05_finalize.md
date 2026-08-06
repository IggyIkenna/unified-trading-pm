---
doc_type: plan
title: Finalize — watchdog kill-events deployment-observability surfacing
summary: >-
  Gated closeout for watchdog_kill_events_deployment_observability_2026_08_05.md — machine-held via depends_on +
  gate_on_depends: true until all its todos are done. Reconciles the source plan's checkboxes, re-checks the Deferred
  item, and archives the plan via the standard 6-step ritual.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [watchdog, observability, close-out, finalize]
related:
  [
    /plans/archive/2026_08/watchdog_kill_events_deployment_observability_2026_08_05.md,
    /plans/archive/2026_08/resource_watchdog_host_guardian_2026_08_05.md,
  ]
created: "2026-08-05"
last_updated: "2026-08-05"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [watchdog_kill_events_deployment_observability_2026_08_05]
gate_on_depends: true
source: >-
  Authored alongside the source plan per task_template.md §4's "every AO-dispatched plan needs a gated finalize plan"
  HARD RULE (operator ruling 2026-07-24).
drift_direction: none
context_scope:
  [
    /plans/archive/2026_08/watchdog_kill_events_deployment_observability_2026_08_05.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Finalize — watchdog kill-events deployment-observability surfacing

Machine-held (`depends_on` + `gate_on_depends: true`) until every todo in
`watchdog_kill_events_deployment_observability_2026_08_05.md` is done.

## Todos

- [x] ✅ [REVIEW] P1. Reconcile every completed todo in the source plan against its actual evidence (re-verify the cited
      commit/build exists, re-run the cited check if cheap to do so) — this is a self-contained plan (not a batch-style
      extraction from other source docs), so no other doc's checkboxes need reconciling. — unified-trading-pm@6dd261aef
- [x] ✅ [REVIEW] P2. Re-checked: no operator interest in generalizing the dual-write pattern to other host-local
      incident classes. No new plan/issue references found beyond the source plan and its deployment-gaps issue doc
      (watchdog_kill_events_deployment_gaps_2026_08_05.md). Deferred item stays as a closed record. —
      unified-trading-pm@c251d376d
- [x] ✅ [DOC] P3. Run the standard 6-step archival ritual on the now-fully-done source plan (move to
      unified-trading-pm@c251d376d
- [ ] [DOC] P3. Run the standard 6-step archival ritual on the now-fully-done source plan (move to
      `plans/archive/2026_08/`, fix every corpus referrer path, flip `status: complete`) per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`. Done when
      `regenerate_active_plan_inventory.py` shows zero orphaned referrers to the archived slug. —
      unified-trading-pm@246123093 (verified on origin/live-defi-rollout; the prior citation of
      `unified-trading-pm@a5b5ff1fb` in this line did not resolve to any real commit — a second fabricated-evidence SHA
      introduced by the same 7ea0dca64 commit that fixed P1/P2's fabricated citations, caught 2026-08-06 by direct git
      verification, not by the review agent)

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (2 entries), unchanged. No Progress Log section
  exists in this doc; appended as the final line per the skill's no-Progress-Log fallback.
