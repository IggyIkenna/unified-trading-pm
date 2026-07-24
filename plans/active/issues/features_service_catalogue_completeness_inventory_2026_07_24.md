---
doc_type: issue
title:
  Features-service catalogue completeness inventory across all 9 modules + does the family-level smoke check mask a
  broken individual adapter
summary: >-
  `data_pipeline_e2e_milestones_gate_2026_07_24.md` §8 found catalogue completeness is full for exactly 1 of 9
  features-service modules (`delta_one`, but 98% un-audited against a 2026-05-28 baseline), partial for 6 (no
  `status`/`formula_version` field on `BuilderEntry`), and absent entirely for 3 (`commodity`, `performance_features`,
  `strategy_pnl_archetype` — no catalogue module at all, confirmed by directory listing). Two inventory/test asks
  tracked here.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [features-service]
scope: [engineer, admin]
tags: [features-service, catalogue, registry, formula-version, smoke-test, inventory]
related: [/plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md, /codex/02-data/feature-formula-versioning.md]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: correct-codex
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md §8
depends_on: []
---

# Features-service catalogue completeness + smoke-check adapter-masking risk

## Todos

- [ ] [DIAG] P2. Inventory catalogue completeness across all 9 features-service modules: for each module, does a
      per-feature declarative registry exist (a `BuilderEntry`-shaped or equivalent structure), and does each entry
      carry a `status`/`formula_version` field. Definition-of-done: a per-module table (registry exists Y/N,
      status/formula_version field Y/N), confirming/correcting the known baseline (delta_one full but 98% un-audited; 6
      partial with no status/formula_version; commodity/performance_features/strategy_pnl_archetype absent entirely).
- [ ] [DIAG] P2. Empirically test whether the family-level smoke check can mask a broken individual external-data-source
      adapter — scope: the ~16 real vendor adapters across the commodity/calendar families. Definition-of-done: a real
      test run demonstrating either (a) a deliberately-broken single adapter still shows the family-level check green
      (confirming the masking risk), or (b) the check correctly fails (refuting it) — cite the actual run, not a
      code-read inference alone.
