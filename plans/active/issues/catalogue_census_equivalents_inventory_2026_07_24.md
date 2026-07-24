---
doc_type: issue
title:
  Does an equivalent distinct-values census exist for the strategy catalogue, features catalogue, fixtures catalogue,
  and UAC registries beyond the 4 axes _distinct_values.py/_axis_census.py already cover?
summary:
  Written-inventory ask (no code changes) from `data_pipeline_e2e_milestones_gate_2026_07_24.md` §2 — the manifest's
  distinct-values census (venues/instrument_types/data_types/chains) is well-established, but it's unclear whether an
  analogous drift-detection census exists for other catalogues (strategy registry, features-service's per-family
  registries, sports fixtures catalogue) or UAC registries beyond those 4 axes.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-api, strategy-service, features-service, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [census, distinct-values, catalogue, drift-detection, inventory]
related:
  [
    /plans/active/distinct_values_noncanonical_audit_2026_07_20.md,
    /codex/02-data/reconciliation-census-and-compute-tiers.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
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
source: /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md §2
depends_on: []
---

# Census equivalents beyond the 4 manifest axes

## Todos

- [ ] [REVIEW] P2. Written inventory (no code changes): for each of the strategy catalogue (strategy-service registry),
      the features catalogue (features-service's per-family declarative registries), the sports fixtures catalogue, and
      any UAC registry not already covered by `_distinct_values.py`/`_axis_census.py`'s 4 axes
      (venues/instrument_types/data_types/chains) — determine whether an equivalent drift-detection census (comparing
      live registered values against a canonical set) exists today. Definition-of-done: a stated yes/no per catalogue,
      with a code citation for "yes" or a gap note for "no" — file each "no" as its own follow-up todo here rather than
      building anything in this pass.
