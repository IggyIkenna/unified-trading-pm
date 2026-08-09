---
doc_type: plan
title:
  Cross-cutting satellite AO batch 7 — agent_operating_framework_master bounded residual (escalation false-resolution
  historical-sample audit) extracted from the round9 2026-08-09 sweep
summary: >-
  Seventh AO-dispatch batch for the cross-cutting tranche, produced by the round9 2026-08-09 RECLASSIFY +
  satellite-extraction sweep. Pulls 1 bounded item out of
  `escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md` (`agent_operating_framework_master`):
  a bounded historical-sample audit of escalation rows auto-closed by the now-fixed `_poll_wall_resolution`
  false-resolution bug, now that the code fix has landed (`agent-orchestrator@884a9bfe1`). The doc's whole-doc
  RECLASSIFY bar stays unmet — its sibling `[OPERATOR] P1` todo (confirm/relaunch the DP-VM-003 stalled backfill VM)
  is a genuine operator-tagged item, not extracted here.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-7, satellite-docs, agent-operating-framework-master, escalation]
related:
  [
    /plans/active/issues/escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch7_2026_08_09.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md,
    agent-orchestrator/server/escalation.py,
  ]
source: >-
  round9 RECLASSIFY + satellite-batch-extraction sweep 2026-08-09 (cross-cutting tranche).
assigned_role: backend_engineer
effort: medium
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 7 (agent_operating_framework_master) — bounded-item extraction

> **Status: active.** Single-todo batch — exempt from the finalize-twin requirement per
> `check_finalize_plan_coverage.py`'s single-open-todo carve-out; archival folds into this todo's own done-when.

## Todos

- [ ] [BACKEND] P2. **Bounded historical-sample audit of escalations auto-closed by the now-fixed
      `_poll_wall_resolution` false-resolution bug.** Source:
      `escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md` (its 3rd todo). The bug
      (`server/escalation.py:1660-1753`'s unconditional QG-green fallthrough for non-QG-signal wall types) is
      confirmed fixed and shipped (`agent-orchestrator@884a9bfe1`, gated to `_QG_SIGNAL_WALLS =
      {"ldr_qg_failure", "main_ci_red"}`). Before this fix, historical auto-close rates via this path were:
      `data_pipeline_failure` 599/604 (99%), `provenance_blocked` 80/80 (100%), `sit_failure` 39/39 (100%),
      `plan_health` 221/222 (99.5%). Spot-check a bounded sample (the last 30 days per `wall_type`, not a full
      1000+-row audit) of these auto-closed rows for any other still-live, still-unaddressed problem masquerading as
      resolved — beyond the 2 specific escalations (DP-VM-003, DP-FETCH-009) the source doc's own todos already
      track. Query the orchestrator's `escalation_queue` table directly (read-only, via the sanctioned SSM path) for
      rows with `resolution="qg_v2_green"` and `wall_type` in the 4 affected types, cross-reference each against
      whether the underlying condition (stalled VM / provenance gap / SIT failure / plan-health finding) was actually
      independently fixed around the same time, or whether it's a genuine miss. File any genuine miss as its own
      dated issue doc per the findings-triage HARD RULE; if the sample turns up nothing beyond what's already
      tracked, record that (with the query + row count) as the audit's own conclusion — do not expand to a full
      corpus audit unless the sample finds a real live miss. Done when: the sample is run, every hit is either
      confirmed independently-resolved or filed as a fresh finding, and the source doc's own todo is flipped citing
      the evidence. Repo: agent-orchestrator (read-only query) + unified-trading-pm (the audit record + any filed
      findings).

## Progress Log

- **2026-08-09**: Batch authored via the round9 cross-cutting RECLASSIFY + satellite-extraction sweep. 1 item
  extracted — the doc's own text already frames it as bounded ("Scope this as a bounded sample... not a full
  1000+-row audit") and the code fix it depends on has landed, clearing the prerequisite this item was implicitly
  waiting on.
