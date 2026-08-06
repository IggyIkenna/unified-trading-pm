---
doc_type: plan
title: HYPERLIQUID + ASTER asset_group migration — finalize (reconcile D15 + archive)
summary: >-
  Gated closeout for hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md — machine-held via depends_on +
  gate_on_depends: true until all 5 phases of that plan are done. Reconciles D15 in defi_code_codex_drift_2026_05_27.md
  and the two codex SSOTs the source plan's own Phase 5 names, then archives both docs. Authored `status: active` (not
  draft) per the no-double-gate finding — `gate_on_depends` alone already machine-holds every task here until the source
  plan's todos land, regardless of the source plan's own status.
status: active
nature: process
asset_group: [cefi, defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [migration, asset-group, cefi, defi, hyperliquid, aster, archival]
related:
  [
    /plans/active/hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md,
    /plans/active/issues/defi_code_codex_drift_2026_05_27.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-06"
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02]
gate_on_depends: true
source: >-
  Drafted alongside the operator's 2026-08-06 activation ruling on
  hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md (governance sweep), per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched multi-todo plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md,
    /plans/active/issues/defi_code_codex_drift_2026_05_27.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# HYPERLIQUID + ASTER asset_group migration — finalize

> **Machine-gated on `hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 5 phases of that plan are `done`.
> `sequential: true` because todo 2 (archival) must run after todo 1 (reconciliation).

## Todos

- [x] ✅ [REVIEW] P2. **Reconcile D15 + the codex SSOTs.** Confirm the source plan's Phase 5 closed D15 in
      `defi_code_codex_drift_2026_05_27.md` (flip to ✅ RESOLVED citing the migration's completion evidence) and that
      `/codex/02-data/defi-data-pipeline.md` / `defi-canonical-naming-ssot.md` no longer document HYPERLIQUID/ASTER as
      dual-classified or `asset_group=defi`-resident, per Phase 5's own todo. **Done when**: the reconciliation is
      recorded in this plan's own Progress Log with the exact commit citation.

- [ ] [DOC] P2. **Archive the source plan + this finalize plan.** Once all 5 phases (including the Phase 4 delete) and
      this plan's todo 1 are done, archive both `hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md` and
      this finalize doc to `plans/archive/2026_08/` per the 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) — update every referrer (this doc's own
      `related:`, `defi_code_codex_drift_2026_05_27.md`'s D15 reference). **Done when**: both files are in
      `plans/archive/2026_08/` and `regenerate_active_plan_inventory.py` shows 0 orphaned referrers.

## Progress Log

- 2026-08-06 (slot 9, task `hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02_finalize-001`): **Todo 1
  DONE — reconciliation complete.** Confirmed source plan all-5-phases-done (all checkboxes `[x] ✅`). Codex SSOT check:
  (1) `defi-canonical-naming-ssot.md` — CLEAN, has explicit "On-chain perp CLOBs are CeFi, NOT DeFi" section (lines
  132-145) classifying HYPERLIQUID/ASTER as CeFi with no defi-resident claim. (2) `defi-data-pipeline.md` — Phase 5
  claimed "already updated" but had 3 stale references: lines 157/172/207 still listed Hyperliquid/Aster as active DeFi
  perp sources without the "MOVED TO CEFI" notation (unlike GMX/Drift which had "(REMOVED)" notes). Updated all 3 to
  document "No DeFi perp venue currently live" + HYPERLIQUID/ASTER MOVED TO CEFI 2026-06-21 note. D15 in
  `defi_code_codex_drift_2026_05_27.md` was already `[x] ✅` but had stale text "NOT executed yet" — appended migration
  completion addendum citing market-tick-data-service@55d88025. Shipped: unified-trading-pm@75f1105f8 (D15 addendum +
  defi-data-pipeline.md 3 stale-ref fixes + this Progress Log + checkbox flip).

- 2026-08-06 (governance sweep, interactive session): drafted alongside the operator's activation ruling on the source
  plan, per the finalize-plan-coverage rule (`check_finalize_plan_coverage.py`). `status: active` from the start —
  `gate_on_depends: true` already fully holds both todos above until every phase of the source plan is `done`, so no
  second manual flip is needed later (2026-07-30 no-double-gate finding).
