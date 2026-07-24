---
doc_type: issue
title:
  Code-read whether the paper/live strategy universe resolver actually restricts itself to UAC's MVP_SCOPE canonical
  definition
summary: >-
  `data_pipeline_e2e_milestones_gate_2026_07_24.md` §14 found none of the 5 asset-group plans' own "MVP universe"
  sections state which MVP cells have actually been proven wired through backfill=paper=live, vs. just declared
  in-scope. A precondition for answering that per-AG question is confirming, by direct code read (not assumption), that
  the paper/live strategy universe resolver genuinely restricts itself to UAC's `MVP_SCOPE` canonical definition in the
  first place.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [mvp-scope, strategy-universe, paper-live, batch-live-paper, code-read]
related:
  [
    /codex/02-data/mvp-scope-canonical.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: correct-codex
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md §14
depends_on: []
---

# MVP_SCOPE resolver code-read

## Todos

- [ ] [BACKEND] P1. Code-read (not assumption) whether strategy-service's paper/live strategy universe resolver actually
      restricts its instrument/venue universe to UAC's `MVP_SCOPE` canonical definition, or whether it silently includes
      non-MVP cells. Definition-of-done: a cited code path (file + function) confirming or refuting the restriction,
      with any found gap filed as its own follow-up todo (not fixed in this pass).
