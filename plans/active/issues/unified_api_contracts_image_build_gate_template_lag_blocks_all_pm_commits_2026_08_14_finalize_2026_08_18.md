---
doc_type: issue
title: unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14 — finalize
summary: >-
  Gated closeout for the 2026-08-18 na-eligibility-audit retroactive reclassification (NA -> planning) of
  unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14.md. Self-contained
  single-todo doc (add a consumer-scoped `detect_template_drift.py --workflows --repo <self>` pre-commit/CI check
  to unified-api-contracts, mirroring the already-shipped STEP 5.108 pattern) — this finalize plan verifies the fix
  + evidence, then runs the standard 6-step archival ritual once the doc reaches zero open todos.
status: open
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts]
scope: [engineer]
tags: [ci, ao-dispatch, close-out, reclassification, na-audit, finalize]
related:
  [
    /plans/active/issues/unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-18"
last_updated: "2026-08-20"
parent_epic: ci_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.1
assigned_role: review
effort: low
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/issues/unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored
  by the ci-tranche /na-eligibility-audit run (dispatch agt-b10de6) in the same turn as the RECLASSIFY_WHOLE flip it
  finalizes.
---

# unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14 — finalize

> **Machine-gated on `/plans/active/issues/unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14.md`**
> (`depends_on` + `gate_on_depends: true`) — will not dispatch until that doc's sole open todo is `done`.

## Todos

- [ ] [REVIEW] P3. Once the `detect_template_drift.py --workflows --repo <self>` consumer-scoped check in
      `unified-api-contracts` is shipped with a real commit sha (verify it actually runs in that repo's own CI and
      catches a deliberately-injected drift case before merge, mirroring how
      `cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md`'s STEP 5.108 wiring was verified), flip the
      source doc's checkbox `[x]` with evidence, then run the standard 6-step archival ritual on that doc (flat
      `plans/archive/issues/` destination per its `doc_type: issue`) and archive this finalize plan alongside it.
      Done when: both docs are under `plans/archive/`, and `regenerate_active_plan_inventory.py` reports zero orphan
      referrers to either.

## Progress Log

- **2026-08-18 (na-eligibility-audit, ci tranche)**: authored alongside the source doc's RECLASSIFY_WHOLE flip.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
