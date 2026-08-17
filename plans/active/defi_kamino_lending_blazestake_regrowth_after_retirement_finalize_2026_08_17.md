---
doc_type: plan
title: Finalize — DeFi KAMINO_LENDING/BLAZESTAKE regrowth root-cause
summary: Gated finalize companion for defi_kamino_lending_blazestake_regrowth_after_retirement_2026_08_17.md.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service]
scope: [engineer]
tags: [defi, finalize]
related:
  [
    /plans/active/issues/defi_kamino_lending_blazestake_regrowth_after_retirement_2026_08_17.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
assigned_role: review
drift_direction: advance-code
depends_on: [defi_kamino_lending_blazestake_regrowth_after_retirement_2026_08_17]
gate_on_depends: true
supersedes:
superseded_by:
source: "na-eligibility-audit defi tranche, 2026-08-17 (dispatch agt-f4fef7)"
locked_by:
context_scope:
  [
    /plans/active/issues/defi_kamino_lending_blazestake_regrowth_after_retirement_2026_08_17.md,
    /plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md,
    /plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md,
  ]
locked_since:
---

# Finalize — DeFi KAMINO_LENDING/BLAZESTAKE regrowth root-cause

- [ ] [REVIEW] P3. Confirm the root-cause diagnosis landed (which mechanism — rebuild-rescan class like dex_pools,
      or a live-writer casing/dedup defect like POOL — was identified for the small KAMINO_LENDING (80 rows) and
      BLAZESTAKE (1 row) regrowth), flip the source `[DIAG] P3` todo to done with evidence, and archive this plan
      once done and unlocked.

## Progress Log

- **na-eligibility-audit 2026-08-17 (defi tranche, dispatch agt-f4fef7)**: authored as the gated finalize companion
  for the source doc's RECLASSIFY (whole-doc, conflict-clear — see that doc's own Progress Log entry).
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries) -- added the two sibling recurrence
  docs (`dex_pools` rebuild-rescan class, `POOL`-uppercase live-writer class) the source issue doc's own todo names
  as the two mechanism classes to compare this regrowth against.
