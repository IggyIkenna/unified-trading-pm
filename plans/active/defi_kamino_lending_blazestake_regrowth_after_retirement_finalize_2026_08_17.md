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
last_updated: "2026-08-20"
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

- [ ] [REVIEW] P3. Confirm the root-cause diagnosis landed, flip the source `[DIAG] P3` todo to done with evidence, THEN archive this plan (only once unlocked) — corrected 2026-08-19 (`/plan-reconcile manifest_master`, line-1-completeness fix: the flip+archive actions were previously stranded on lines 2-3, invisible to a worker's brief).
      Mechanism to confirm is either a rebuild-rescan class defect (like `dex_pools`) or a live-writer casing/dedup
      defect (like `POOL`) for the small KAMINO_LENDING (80 rows) and BLAZESTAKE (1 row) regrowth — see
      `context_scope` for the two comparison docs.

## Progress Log

- **na-eligibility-audit 2026-08-17 (defi tranche, dispatch agt-f4fef7)**: authored as the gated finalize companion
  for the source doc's RECLASSIFY (whole-doc, conflict-clear — see that doc's own Progress Log entry).
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries) -- added the two sibling recurrence
  docs (`dex_pools` rebuild-rescan class, `POOL`-uppercase live-writer class) the source issue doc's own todo names
  as the two mechanism classes to compare this regrowth against.
- **plan-reconcile 2026-08-19 (epic-scoped, AO-dispatch-readiness hunter)**: line-1-completeness fix on the one open
  todo — the flip-source-todo and archive-once-unlocked actions were on physical lines 2-3, invisible to a worker's
  brief (`regen_backlog_from_plan.py::_parse_open_todos` only captures line 1). Rewrote so all three actions (confirm,
  flip, archive) are on line 1; mechanism-comparison detail moved to a continuation line. Also added this doc's own
  entry to the epic hub's "Assigned active plans" P3 section (it was missing entirely — the hub instead still listed a
  different, already-archived Kamino finalize doc). Working-tree-only, not shipped.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
