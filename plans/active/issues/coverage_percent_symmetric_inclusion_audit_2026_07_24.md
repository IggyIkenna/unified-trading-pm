---
doc_type: issue
title:
  Audit every coverage-percent computation across repos against the symmetric-inclusion invariant (empty_confirmed in
  numerator+denominator together, or neither)
summary: >-
  `/codex/02-data/honest-coverage-model.md` now states the symmetric-inclusion invariant explicitly (added 2026-07-24
  per `data_pipeline_e2e_milestones_gate_2026_07_24.md` §10) — the 2 SSOT formulas (`reachable_coverage`,
  `all_shards_coverage`) satisfy it by construction, but a 3rd, undocumented coverage-percent formula was found live in
  deployment-api during this same audit. This doc tracks the corpus-wide grep + classification needed to find any other
  asymmetric violation.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-api, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [honest-coverage, empty_confirmed, coverage-percent, audit, invariant]
related: [/codex/02-data/honest-coverage-model.md, /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: correct-codex
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md §10
depends_on: []
---

# Symmetric-inclusion invariant audit — every coverage-percent formula

## Todos

- [ ] [AUDIT] P2. Grep every repo (start with deployment-api, given a 3rd undocumented formula site was already found
      there) for coverage-percent computations referencing `empty_confirmed`; classify each against the
      symmetric-inclusion invariant stated in `/codex/02-data/honest-coverage-model.md` § "Coverage formula".
      Definition-of-done: every found formula site listed with a PASS/VIOLATION verdict; each VIOLATION filed as its own
      bounded fix todo (not fixed in this audit pass).
