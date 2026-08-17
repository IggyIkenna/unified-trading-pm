---
doc_type: issue
title: Finalize — subgraph-health-probe 28/50 alert-rate triage close-out
summary: >-
  Gated finalize companion for issues/subgraph_health_probe_28_of_50_alerted_after_fix_2026_08_16.md (reclassified
  NA→planning, na-eligibility-audit 2026-08-17) — re-verifies the stabilized alert-rate evidence, confirms the
  close-vs-follow-up branch was taken correctly, then archives both docs per plan-completion-and-archival-discipline.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [data-pipeline, defi, subgraph, finalize, archival]
related:
  [
    /plans/active/issues/subgraph_health_probe_28_of_50_alerted_after_fix_2026_08_16.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: data_engineering
effort: low
thinking_tier: mechanical
depends_on: [subgraph_health_probe_28_of_50_alerted_after_fix_2026_08_16]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/issues/subgraph_health_probe_28_of_50_alerted_after_fix_2026_08_16.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
source: >-
  na-eligibility-audit 2026-08-17 — every reclassified NA->planning doc needs a gated finalize companion
  (/plans/active/task_template.md §4).
drift_direction: advance-code
---

# Finalize — subgraph-health-probe 28/50 alert-rate triage close-out

Machine-held (`gate_on_depends: true`) until the todo in
`issues/subgraph_health_probe_28_of_50_alerted_after_fix_2026_08_16.md` is done. Do not start manually before then.

## Todos

- [ ] [REVIEW] P2. Re-verify the source doc's own close-vs-follow-up branch was taken correctly: independently
      re-check the stabilized alert rate against `#data-pipeline-alerts` / the alerting-service logs (don't trust the
      source doc's own citation alone) — confirm the cited rate and which branch (close as cold-start noise / file a
      dedicated per-protocol triage plan) was actually followed, and that the evidence supports it.
- [ ] [DOC] P2. Once the REVIEW todo above is done: run the standard 6-step plan-completion-and-archival-discipline
      ritual on `issues/subgraph_health_probe_28_of_50_alerted_after_fix_2026_08_16.md` and this finalize doc itself —
      archive both to `plans/archive/2026_08/issues/`, fix every corpus referrer path. Done-when:
      `regenerate_active_plan_inventory.py` shows zero orphan referrers to the archived paths.

## Progress Log

- **2026-08-17 (na-eligibility-audit, defi tranche)**: finalize plan authored alongside the RECLASSIFY flip of the
  source issue doc, per `task_template.md`'s finalize-plan-coverage rule.
