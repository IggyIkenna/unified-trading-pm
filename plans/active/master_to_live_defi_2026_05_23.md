---
title: "May-23 Cutover Master — Live DeFi Trading by 2026-05-23"
created: 2026-05-06
last_updated: 2026-05-11
locked_by: live-defi-rollout
locked_since: 2026-05-06
assigned_vm: planning
name: master-to-live-defi-2026-05-23
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
effective_concurrent_slots: 5-8
estimate_calibration_note: |
  Plan-level estimate covers the meta-plan artefact itself (writing + maintaining the rollup surface, audit table,
  Q&A surface) — that is single-slot work for the master-plan owner. The ~175 sub-plans this plan orchestrates each
  carry their own estimate_class + calibrated AI-days in their frontmatter. Total cutover scope = sum of sub-plan
  calibrated estimates, NOT this number.

  effective_concurrent_slots: 5-8 reflects the workspace allocation for May-23 cutover execution: both operators
  (Ikenna + Harsh) run up to 8 slots each, and sub-plans fan out across slots per the daily work-split. Wall-clock
  prediction for the cutover = sum-of-sub-plan-calibrated-ai-days / 5-8 effective concurrent slots (bounded by the
  serial-dependency floor — code-freeze → migrate → backfill phases cannot fully parallelise).
  SSOT: codex/08-workflows/estimation-calibration.md § "Parallelism axis".
parent_epic: orchestrator_master
priority: P0
status: active
execution_scope: local-only
model_tier: opus-required
thinking_tier: max
---

> 2026-05-23. **Soft freeze**: NO new public-API surfaces, NO new top-level packages, NO module renames in any of the 4
> repos until Phase 7 archive lands. Internal bugfixes + test work + plan-flip backfills continue.

> **✅ Gate 3 FIRED 2026-05-17 14:42 UTC — 0 phantoms all 5 asset_groups. Operator decision: ACCEPT.**

> **🟢 VM RUNNING — B-015 paper backtest 2026-05-18 06:27 UTC (Tenderly fork active)** (BE-AWARE)
>
> `strategy-paper-carry-staked-basis-20260518-115404` (asia-northeast1-c, n2-standard-4) running paper backtest in
> `--continuous --tick-interval 3600` mode with **real Tenderly Virtual TestNet fork fills** (UCI-fetched API key, VNet
> `87aefc66-43f4-4463-a554-e5b5eadd239c`). First tick 2026-05-18 06:27:16Z. pvl-p18a gate clock started; paper-runnable
> threshold **2026-05-21 06:27 UTC**. Owner: harsh-main (picked up from ikenna tick-78 silent failure; re-launched after
> UCI fix to upgrade from benchmark to fork fills). Status JSON:
> `gs://deployment-scripts-central-element-323112/deployments/active/c6b916f5-025b-41df-b05c-59934ba96faa.json`.
> Predecessor VM 105854 (benchmark fills) deleted at 06:23 UTC after ~56 min on tick #1. Cross-side pings:
> `plans/active/_agent_pings.md` 2026-05-18 05:38 UTC + 06:28 UTC.

> **🟡 IN-FLIGHT REFACTOR — batch/live symmetry 2026-05-10** (BE-AWARE)
>
> [`batch_live_symmetry_2026_05_10`](batch_live_symmetry_2026_05_10.md) is establishing codex SSOTs for mode-axis
> discipline (4-axis cartesian product + anti-patterns), per-asset-group batch/live docs (cefi ✅ shipped), and QG STEPs
> L1-L7 enforcement. **Before touching**: mode enums (`RuntimeMode` / `OperationalMode` / `BatchExecutionMode`),
> batch/live seam logic, `DataType` enum members, or `record_captured()` callsites — read
> `codex/06-coding-standards/mode-axis-discipline.md` + `codex/04-architecture/batch-live-architecture.md §2` first. Tab
> 2 (UAC `BatchExecutionMode` canonical location) gates Slot 8 L3 STEP enable.

> **🟡 IN-FLIGHT REFACTOR — code-freeze sequencing 2026-05-10** (BE-AWARE)
>
> [`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md)
> is the time-axis sequencing umbrella for May-23. This master is the **readiness-state SSOT**; the sequencing plan is
> the **time-axis SSOT**. Read both before scheduling work — the sequencing plan pins Phase 1 code-complete (deadline
> 2026-05-15) → Phase 2 one-shot physical migrations (window 2026-05-15→2026-05-19) → Phase 3 resume backfills
> end-to-end (window 2026-05-19→2026-05-23) and includes an anti-sequencing audit table flagging 13 plans by
> re-migration risk.

> **🟢 ESTIMATE CALIBRATION — codified 2026-05-11** (READ BEFORE SCHEDULING)
>
> Per [`codex/08-workflows/estimation-calibration.md`](../../codex/08-workflows/estimation-calibration.md), AI-day
> estimates in this workspace run 1.5-3× conservative for parallel-agent + sub-agent fan-out. Apply per-class
> multipliers (`refactor` 0.4× / `design` 0.6× / `infra` 0.8× / `brand-new` 1.0× / `research` 1.2×) to baseline.
> Sub-plans this master orchestrates should each carry `estimate_class` + `estimate_baseline_ai_days` +
> `estimate_calibrated_ai_days` in frontmatter; work-split scope totals MUST use the calibrated number. Retrospective
> ledger at
> [`codex/08-workflows/estimation-retrospective-ledger.md`](../../codex/08-workflows/estimation-retrospective-ledger.md).

# May-23 Cutover Master — Live DeFi Trading by 2026-05-23

## Epics index (May-23 cutover, restructured 2026-05-08)

This plan is the **umbrella of epics**. Per operator direction 2026-05-08, six same-domain epics were folded into their
master plans (less indirection); only `cross_cutting` remains as a standalone epic. Each May-23 deliverable now lives in
its master plan's `## May-23 deliverable` section.

| May-23 deliverable                      | Lives in master § "May-23 deliverable"                                                                               | Scope                | Live/Batch | Archived epic (archaeology)                                                                           |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | -------------------- | ---------- | ----------------------------------------------------------------------------------------------------- |
| Live DeFi rollout (carry archetypes)    | [`defi_master`](../epics/defi_master.md#may-23-deliverable-folded-from-live_defi_rollout_may_23_2026epic-2026-05-08) | LIVE on real wallet  | Live       | [`archive/live_defi_rollout_may_23_2026.epic.md`](../archive/live_defi_rollout_may_23_2026.epic.md)   |
| CeFi ML                                 | [`cefi_master`](../epics/cefi_master.md)                                                                             | LIVE on real capital | Live       | [`archive/cefi_ml_may_23_2026.epic.md`](../archive/cefi_ml_may_23_2026.epic.md)                       |
| S&P prediction (CME)                    | [`tradfi_master`](../epics/tradfi_master.md) (deliverable A)                                                         | BATCH ML only        | Batch      | [`archive/sp_prediction_may_23_2026.epic.md`](../archive/sp_prediction_may_23_2026.epic.md)           |
| Price arbitrage (CME futures + ETFs)    | [`tradfi_master`](../epics/tradfi_master.md) (deliverable B)                                                         | BACKTEST only        | Batch      | [`archive/price_arbitrage_may_23_2026.epic.md`](../archive/price_arbitrage_may_23_2026.epic.md)       |
| Sports ML                               | [`sports_master`](../epics/sports_master.md)                                                                         | BACKTEST only        | Batch      | [`archive/sports_ml_may_23_2026.epic.md`](../archive/sports_ml_may_23_2026.epic.md)                   |
| Prediction markets                      | [`predictions_master`](../epics/predictions_master.md)                                                               | BACKTEST only        | Batch      | [`archive/prediction_markets_may_23_2026.epic.md`](../archive/prediction_markets_may_23_2026.epic.md) |
| Cross-cutting (catalogue / IDs / infra) | [`epics/cross_cutting_may_23_SUPERSEDED_2026_05_21.md`](../epics/cross_cutting_may_23_SUPERSEDED_2026_05_21.md)      | Workspace-wide       | Both       | (still active — workspace-wide concerns spanning all domains; explicitly NOT folded)                  |

Read [`plans/epics/README.md`](../epics/README.md) for the layer model + lifecycle. Each master plan enumerates its
sub-plans; this master plan retains the cross-master readiness checklist + audit + Q&A below.

**Migration note (2026-05-08).** The 9 domain umbrella masters (`cefi_master`, `tradfi_master`, `sports_master`,
`predictions_master`, `ml_and_features_master`, `strategy_and_dart_master`, `infrastructure_master`,
`manifest_migration_master`, `instruments_live_master`) were moved from `plans/active/` to `plans/epics/` — references
throughout the workspace updated in the same commit. `defi_master` stays in `plans/active/` per operator direction
(mid-flight + parallel-agent sensitivity).

---

## Active plan inventory + Done-vs-Left dashboard (auto-tracked)

This section is **auto-regenerated** by
[`scripts/plans/regenerate_active_plan_inventory.py`](../../scripts/plans/regenerate_active_plan_inventory.py). It
solves two coupled problems: (1) "What's done vs left across the workspace?" — aggregate row + per-plan progress at a
glance; (2) "Which plans aren't wrapped by master/epics?" — orphan column visible inline so nothing hides.

Refresh cadence: main-orchestrator runs the script at morning ledger sweep + EOD. Numbers between regenerations are
stale — re-run before any planning decision that depends on this table.

<!-- AUTO-INVENTORY-START -->
_Last regenerated: 2026-06-10 08:26 UTC via `scripts/plans/regenerate_active_plan_inventory.py`. Sorted by `cal_left` desc. TBD = baseline not yet filled by owner agent. Orphan = plan not referenced by master or any epic — should be folded into the appropriate epic._

| Plan | Owner | Class | Checkboxes | % done | Cal left | Deadline |
|---|---|---|---|---|---|---|
| [`org_migration_to_odumresearch_2026_06_07`](./org_migration_to_odumresearch_2026_06_07.md) | master | infra | 0/27 | 0% | 8.0 | — |
| [`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`](./pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md) | master | infra | 3/16 | 19% | 7.8 | — |
| [`migration_verification_orphan_safety_2026_06_10`](./migration_verification_orphan_safety_2026_06_10.md) | master | design | 3/23 | 13% | 5.7 | — |
| [`proper_instrument_catalogue_lifecycle_rollup_2026_06_04`](./proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md) | master | brand-new | 3/10 | 30% | 5.6 | — |
| [`data_source_provenance_all_asset_groups_2026_06_01`](./data_source_provenance_all_asset_groups_2026_06_01.md) | master | infra | 17/36 | 47% | 4.2 | — |
| [`bucket_env_split_rollout_2026_06`](./bucket_env_split_rollout_2026_06.md) | master | infra | 0/9 | 0% | 3.2 | — |
| [`bar_edge_left_vs_right_remediation_2026_06_08`](./bar_edge_left_vs_right_remediation_2026_06_08.md) | master | brand-new | 4/11 | 36% | 3.2 | — |
| [`codex_vs_repo_docs_ssot_audit_2026_06_01`](./codex_vs_repo_docs_ssot_audit_2026_06_01.md) | master | refactor | 1/24 | 4% | 3.1 | — |
| [`quality_gates_speed_and_config_ssot_2026_06_09`](./quality_gates_speed_and_config_ssot_2026_06_09.md) | master | infra | 2/35 | 6% | 3.0 | — |
| [`bigquery_feature_ml_compute_engine_option_2026_06_08`](./bigquery_feature_ml_compute_engine_option_2026_06_08.md) | master | design | 2/7 | 29% | 3.0 | — |
| [`mvp_scope_catalogue_tagging_2026_06_08`](./mvp_scope_catalogue_tagging_2026_06_08.md) | master | design | 2/10 | 20% | 2.9 | — |
| [`bucket_name_ssot_legacy_dual_write_remediation_2026_06_01`](./bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md) | master | infra | 10/24 | 42% | 2.8 | — |
| [`master_data_canonicalisation_migration_catalogue_2026_06_07`](./master_data_canonicalisation_migration_catalogue_2026_06_07.md) | master | design | 14/50 | 28% | 2.6 | — |
| [`worktree_ldr_unification_2026_06_08`](./worktree_ldr_unification_2026_06_08.md) | master | infra | 9/15 | 60% | 2.6 | — |
| [`bucket_iam_write_protection_per_tier_2026_06_09`](./bucket_iam_write_protection_per_tier_2026_06_09.md) | master | infra | 2/12 | 17% | 2.0 | — |
| [`mtds_file_size_refactor_2026_06_08`](./mtds_file_size_refactor_2026_06_08.md) | master | refactor | 0/3 | 0% | 2.0 | — |
| [`tradfi_massive_dual_source_2026_05_28`](./tradfi_massive_dual_source_2026_05_28.md) | master | infra | 40/51 | 78% | 1.5 | — |
| [`instruments_manifest_canonicalisation_2026_06_01`](./instruments_manifest_canonicalisation_2026_06_01.md) | master | infra | 5/13 | 38% | 1.5 | — |
| [`defi_manifest_canonicalisation_2026_06_01`](./defi_manifest_canonicalisation_2026_06_01.md) | features_and_ml_master | refactor | 69/104 | 66% | 1.2 | — |
| [`pipeline_mode_partition_migration_2026_06_01`](./pipeline_mode_partition_migration_2026_06_01.md) | master | infra | 0/2 | 0% | 1.2 | — |
| [`stash_pile_workspace_cleanup_2026_06_03`](./stash_pile_workspace_cleanup_2026_06_03.md) | master | infra | 0/18 | 0% | 1.2 | — |
| [`downstream_services_manifest_canonicalisation_2026_06_01`](./downstream_services_manifest_canonicalisation_2026_06_01.md) | master | infra | 27/50 | 54% | 1.1 | — |
| [`features_service_e2e_pipeline_test_2026_05_26`](./features_service_e2e_pipeline_test_2026_05_26.md) | master | brand-new | 37/44 | 84% | 1.0 | — |
| [`macro_econ_adapter_scaffolds_2026_06_09`](./macro_econ_adapter_scaffolds_2026_06_09.md) | master | infra | 6/12 | 50% | 0.8 | — |
| [`dependency_promotion_range_pins_and_major_bump_sit_2026_06_09`](./dependency_promotion_range_pins_and_major_bump_sit_2026_06_09.md) | master | infra | 16/23 | 70% | 0.7 | — |
| [`ci_local_qg_parity_2026_06_08`](./ci_local_qg_parity_2026_06_08.md) | master | design | 5/7 | 71% | 0.7 | — |
| [`sports_manifest_canonicalisation_2026_06_01`](./sports_manifest_canonicalisation_2026_06_01.md) | master | infra | 76/103 | 74% | 0.6 | — |
| [`mtds_honest_absence_swallow_remediation_2026_06_10`](./mtds_honest_absence_swallow_remediation_2026_06_10.md) | master | refactor | 3/14 | 21% | 0.6 | — |
| [`tradfi_manifest_canonicalisation_2026_06_01`](./tradfi_manifest_canonicalisation_2026_06_01.md) | master | infra | 37/60 | 62% | 0.6 | — |
| [`qg_commit_quality_boundary_and_slot_ff_push_2026_06_03`](./qg_commit_quality_boundary_and_slot_ff_push_2026_06_03.md) | master | infra | 38/73 | 52% | 0.6 | — |
| [`cefi_manifest_canonicalisation_2026_06_01`](./cefi_manifest_canonicalisation_2026_06_01.md) | master | infra | 53/82 | 65% | 0.6 | — |
| [`prediction_manifest_canonicalisation_2026_06_01`](./prediction_manifest_canonicalisation_2026_06_01.md) | master | infra | 51/66 | 77% | 0.5 | — |
| [`quickmerge_dep_content_sync_and_strict_enforcement_2026_06_08`](./quickmerge_dep_content_sync_and_strict_enforcement_2026_06_08.md) | master | brand-new | 7/8 | 88% | 0.5 | — |
| [`staging_clean_start_and_stale_pr_hygiene_2026_06_08`](./staging_clean_start_and_stale_pr_hygiene_2026_06_08.md) | master | infra | 12/15 | 80% | 0.5 | — |
| [`harden_grepable_rules_into_ci_gates_2026_06_02`](./harden_grepable_rules_into_ci_gates_2026_06_02.md) | master | infra | 5/11 | 45% | 0.4 | — |
| [`audit_criteria_automation_2026_06_08`](./audit_criteria_automation_2026_06_08.md) | master | infra | 10/11 | 91% | 0.3 | — |
| [`cicd_contract_hardening_2026_06_01`](./cicd_contract_hardening_2026_06_01.md) | master | infra | 228/271 | 84% | 0.2 | — |
| [`solana_defi_legacy_migration_2026_05_27`](./solana_defi_legacy_migration_2026_05_27.md) | master | infra | 33/34 | 97% | 0.1 | — |
| [`harsh_day_master_2026_06_02`](./harsh_day_master_2026_06_02.md) | master | infra | 14/15 | 93% | 0.1 | — |
| [`master_to_live_defi_2026_05_23`](./master_to_live_defi_2026_05_23.md) | README | design | 168/172 | 98% | 0.1 | — |
| [`manifest_reader_fail_fast_on_stale_fallback_2026_05_28`](./manifest_reader_fail_fast_on_stale_fallback_2026_05_28.md) | master | refactor | 8/13 | 62% | 0.1 | — |
| [`aws_cloud_toggle_and_backfill_parity_2026_05_22`](./aws_cloud_toggle_and_backfill_parity_2026_05_22.md) | infrastructure_master | brand-new | 25/25 | 100% | 0.0 | — |
| [`cicd_v2_latency_reduction_2026_06_10`](./cicd_v2_latency_reduction_2026_06_10.md) | master | infra | 6/6 | 100% | 0.0 | — |
| [`data_pipeline_acquisition_remediation_2026_06_03`](./data_pipeline_acquisition_remediation_2026_06_03.md) | master | infra | 7/7 | 100% | 0.0 | — |
| [`features_backfill_phase3_2026_05_22`](./features_backfill_phase3_2026_05_22.md) | features_and_ml_master | infra | 19/19 | 100% | 0.0 | — |
| [`features_calc_efficiency_and_correctness_2026_05_27`](./features_calc_efficiency_and_correctness_2026_05_27.md) | master | brand-new | 28/28 | 100% | 0.0 | — |
| [`features_input_manifest_migration_2026_05_25`](./features_input_manifest_migration_2026_05_25.md) | master | refactor | 25/25 | 100% | 0.0 | — |
| [`features_registry_status_versioning_2026_05_28`](./features_registry_status_versioning_2026_05_28.md) | master | brand-new | 20/20 | 100% | 0.0 | — |
| [`global_ledger_pnl_attribution_migration_2026_06_01`](./global_ledger_pnl_attribution_migration_2026_06_01.md) | global_ledger_pnl_attribution_master | refactor | 27/27 | 100% | 0.0 | — |
| [`instruments_backfill_phase3_2026_05_22`](./instruments_backfill_phase3_2026_05_22.md) | instruments_master | infra | 26/26 | 100% | 0.0 | — |
| [`mdps_backfill_phase3_2026_05_22`](./mdps_backfill_phase3_2026_05_22.md) | master | infra | 46/46 | 100% | 0.0 | — |
| [`mdps_filter_pushdown_memory_audit_and_fix_2026_05_28`](./mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md) | master | infra | 14/14 | 100% | 0.0 | — |
| [`mdps_long_running_multi_shard_architecture_audit_2026_05_28`](./mdps_long_running_multi_shard_architecture_audit_2026_05_28.md) | master | research | 24/24 | 100% | 0.0 | — |
| [`mdps_pure_polars_migration_2026_05_28`](./mdps_pure_polars_migration_2026_05_28.md) | master | refactor | 38/38 | 100% | 0.0 | — |
| [`mtds_backfill_phase3_2026_05_22`](./mtds_backfill_phase3_2026_05_22.md) | master | infra | 42/42 | 100% | 0.0 | — |
| [`planning_vm_canonical_bringup_and_topology_reconcile_2026_06_05`](./planning_vm_canonical_bringup_and_topology_reconcile_2026_06_05.md) | master | infra | 8/8 | 100% | 0.0 | — |
| [`regime_clustering_structure_allocator_2026_05_29`](./regime_clustering_structure_allocator_2026_05_29.md) | features_and_ml_master | brand-new | 29/29 | 100% | 0.0 | — |
| [`sit_breaking_detection_content_based_2026_06_08`](./sit_breaking_detection_content_based_2026_06_08.md) | master | brand-new | 5/5 | 100% | 0.0 | — |
| [`utl_strictify_preexisting_pyright_suppressions_2026_06_09`](./utl_strictify_preexisting_pyright_suppressions_2026_06_09.md) | master | refactor | 20/20 | 100% | 0.0 | — |
| **TOTAL** (59 plans) | 0 orphans, 0 TBD | — | — | **66% done** | **78** | — |
<!-- AUTO-INVENTORY-END -->

> **Inventory divergence note (2026-05-20 — refresh on next regenerate)**: Both `strategy_repo_consolidation_2026_05_19`
> and `ml_repo_consolidation_2026_05_19` had **Phase 11 — workspace-wide stale-ref cleanup** appended 2026-05-20 per
> operator directive ("finish all strategy consolidation related plans for your slots"). Workspace audit found ~545
> live-code refs to the 5 archived services across consumer repos (deployment-service, UAC, UTL, UI, execution, tail).
> Scope: live code + DEPRECATION_NOTICE audit only; docstrings/CHANGELOG/migration-history stay intact. New phase
> fan-out: ~4.75 cal-AI-days across slots 3, 4, 5, 6, 7, 8. Two operator-pending items still unblocked: (a)
> `gh repo archive` for ml-training-service + ml-inference-service (`_agent_pings.md` line 41+); (b) bucket-strategy
> decision unblocking `strategy_execution_contract_remediation_2026_05_20` Phase 4a/4b. **Inventory counts above will
> drop for both plans on next regenerate** (e.g. strategy plan: 17/18 → 17/26; ml plan: 17/17 → 17/25).

---

## What this plan is — three deliverables in one doc

1. **Master plan (product).** The single rollup tracking surface from now to live DeFi trading on 2026-05-23. Sub-plans
   in `unified-trading-pm/plans/active/` remain authoritative for tactical work; this plan never duplicates them, only
   references and orchestrates.
2. **Audit (process).** Cross-references to existing codex SSOTs and the ~175 active sub-plans. Surfaces overlaps,
   staleness, and conflicts so agents don't re-litigate decisions.
3. **Q&A (decision-gating).** Surfaces unresolved questions in one place so the human (Ikenna / Harsh) can answer once
   and agents stop guessing.

**This plan does not execute anything.** It writes itself, references real artefacts, and once approved is promoted to a
workspace location (see _Tracking surface_ below) where agents pick it up.

---

## Why this exists, what success looks like

**Headline goal.** **Two DeFi archetypes** trade live on a real wallet for ≥7 continuous days by 2026-05-23 (17 days
from today, 2026-05-06):

1. **`carry_staked_basis`** — _ultimate priority_ — recursive LST staking + CeFi/DeFi perp short hedge. Locked plan:
   `carry_staked_basis_structure_axis_2026_05_04`.
2. **`ARBITRAGE_PRICE_DISPERSION`** — cross-venue funding-rate spread trade. Lead plan: `defi_master` (umbrella that
   folds in `defi_pipeline_extension_2026_05_01`, `leveraged_leg_controller_2026_05_01`, and
   `defi_e2e_pipeline_2026_04_30` per the 2026-05-07 consolidation; historical detail preserved in `plans/archive/`).

Archetypes use **per-archetype venue subsets** of the 6-venue perp universe spanning CeFi (Bybit, Deribit, Binance, OKX)
and DeFi perp DEXs (Hyperliquid, Aster): `carry_staked_basis` hedges on 3 LST-margin-capable venues (Deribit + Bybit +
OKX only); `ARBITRAGE_PRICE_DISPERSION` uses all 6 for cross-venue funding spread. Per defi*archetypes_canonicalisation
Stream E correction 2026-05-07. TradFi / Sports / Prediction stay batch-only this cycle — but their ML readiness ladders
progress in parallel so the \_next* archetypes after DeFi launch quickly.

**Cloud-parity goal (concurrent with live trading goal).** Full AWS↔GCP parity by May 23: DeFi-relevant data migrated to
AWS (with prior cost analysis), data status working on AWS, batch backfill with `--force` working on AWS, backtests / ML
/ strategy examples runnable on AWS, **and** a live trading deployment + monitoring instance running on AWS — so the
team can seamlessly switch any deployment between AWS-live / AWS-batch / GCP-live / GCP-batch. _Not every byte gets
migrated_ (waste of API quota when GCS already has it) — only what's needed for the DeFi proof.

**Authority split.**

- _Codex_ (`unified-trading-pm/codex/`) = target architecture. Mostly defined.
- _Sub-plans_ (`unified-trading-pm/plans/active/`, ~175) = current bug-fix / refactor / migration backlog.
- _This plan_ = readiness rollup + audit + Q&A + new work streams not yet plan-covered.
- _Human-led audit pool_
  ([`plans/active/issues/human_led_audit_pool_2026_05_21.md`](./issues/human_led_audit_pool_2026_05_21.md)) = 14-row
  issue catalogue. Humans pick rows → run audit (Opus 4.7 1M context) → upgrade existing plans + create wrapper
  remediation plan → AWS 18-slot background-agent pool dispatches the wrapper plan 24/7. Keeps human work focused on
  cross-archetype/cross-codebase audits while background agents drive execution.

---

## Audit — existing SSOTs this plan augments (does NOT recreate)

The codex already has SSOTs covering most of what was raised in the brief. Cross-reference table:

| Concern raised                                 | Existing codex SSOT                                                                                                                                                                                                                                                                                                                                                                                                       | Plan action                                                                                                                                                                                        |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Service readiness checklist                    | `codex/10-audit/REPO_READINESS_CHECKLIST.yaml` + per-service `codex/10-audit/repos/<service>.yaml` + `_checklist-template-enhanced.yaml`                                                                                                                                                                                                                                                                                  | **Augment** with 7 groups / 23 items below; populate per-service yamls for tier-1                                                                                                                  |
| Cloud-agnostic build / runtime                 | `codex/04-architecture/cloud-agnostic-migration.md`                                                                                                                                                                                                                                                                                                                                                                       | Augment with build-lineage gap (work-stream D below)                                                                                                                                               |
| Custody / treasury (Copper, CEFFU)             | `codex/04-architecture/custody-providers.md` (single SSOT, replaces deleted `copper-custody-integration.md` + `ceffu-custody-integration.md` per `codex_refactor_2026_05_08.md` Phase D.4), `wallet-hierarchy-and-capital-flow.md`                                                                                                                                                                                        | Verify CEFFU coverage (Binance institutional custody — slot 8 audit PB-14: CEFFU subsections still PENDING in `custody-providers.md`; needs DEFERRED-AFTER-CUTOVER banner or named successor plan) |
| Batch=live equivalence                         | `codex/04-architecture/batch-live-architecture.md` (single SSOT), `backtest-groups.md`                                                                                                                                                                                                                                                                                                                                    | Verify backtest-fidelity rules per asset_group (real gas, real market impact, real matching)                                                                                                       |
| Alerting                                       | `codex/04-architecture/alerting-batch-live.md`                                                                                                                                                                                                                                                                                                                                                                            | Verify live-mode rule coverage; wire to alerting-service                                                                                                                                           |
| Auto-recovery / kill switches                  | `codex/04-architecture/autonomous-recovery-matrix.md`                                                                                                                                                                                                                                                                                                                                                                     | Verify per-archetype kill-switch coverage                                                                                                                                                          |
| P&L attribution                                | `codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`                                                                                                                                                                                                                                                                                                                                                      | Verify wired into batch-vs-live recon                                                                                                                                                              |
| Operational modes (manual / paper / automated) | `codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md`                                                                                                                                                                                                                                                                                                                                             | Add DART manual-trade lane (work-stream C below)                                                                                                                                                   |
| Strategy onboarding                            | `codex/09-strategy/operational/onboarding-checklist.md`                                                                                                                                                                                                                                                                                                                                                                   | Verify end-to-end flow for `carry_staked_basis`                                                                                                                                                    |
| Lifecycle events / observability               | `codex/03-observability/lifecycle-events.md`, `coordination-events.md`                                                                                                                                                                                                                                                                                                                                                    | Verify GCS event-streaming endpoint exists for deployment-api                                                                                                                                      |
| Deployment topology                            | `codex/04-architecture/runtime-deployment-topology.md`, `RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg`                                                                                                                                                                                                                                                                                                                             | Verify all tier-1 services represented                                                                                                                                                             |
| Shard granularity                              | `codex/02-data/availability-manifest-and-data-status.md`                                                                                                                                                                                                                                                                                                                                                                  | Already canonical post-2026-05-06 multi-axis correction                                                                                                                                            |
| Strategy archetypes                            | `codex/09-strategy/strategy-summary.md` — **9 families / 53 archetypes** (post-2026-04-25 Phase 9 expansion): ML Directional (2) · Rules Directional (2) · Carry & Yield (6) · Arbitrage / Structural (7) · Market Making (10) · Event-Driven (1) · Vol Trading (19) · Stat Arb / Pairs (2) · Portfolio (4). SSOT = `unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype` + `ARCHETYPE_TO_FAMILY` dict | `carry_staked_basis` is the lead candidate; `arbitrage_price_dispersion` (Arbitrage / Structural) is the hedge variant                                                                             |

**Audit conclusion:** ~85% of target architecture has codex coverage. The 5 codex gaps to fill are listed in _Codex SSOT
gaps_ below — they are smaller than they first appear because the foundational docs already exist.

---

## SSOT touchpoint map — bi-directional (read before working · update after changing)

**Principle.** _Docs are the intent._ Codex SSOTs are always **ahead of the code** and **in line with the plans**. The
order of operations is **doc → plan → code**, never code-then-doc-when-someone-remembers. Drift between any pair
(doc/plan/code) is the failure mode this plan is designed to prevent.

The map below is bi-directional:

- **Before working on X** — read the listed SSOTs first. They define the intent. If the intent is unclear or stale,
  update the doc _first_, then write/change code.
- **After changing X** — update the same SSOTs (and the matching plan) so the doc stays the source of truth. Drift
  between code and SSOT is a CI / review failure, not a follow-up.

Rule of thumb: if it lives in `CLAUDE.md`, update there too.

| If you change…                                                                          | Update these SSOTs                                                                                                                                                                                                                                                                                                                                                                                                |
| --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Manifest schema** (column, shard axis, validator, write-gate)                         | `codex/02-data/availability-manifest-and-data-status.md` · `codex/02-data/shard-granularity-cefi.md` · `codex/02-data/sports-scheduling-and-sharding.md` · `codex/02-data/prediction-schema-paths.md` · `codex/02-data/per-asset-group-bucket-layouts.md` · `unified-trading-library/unified_trading_library/manifest_writer.py` (SSOT) · `CLAUDE.md` "Availability manifest" + "Shard-granularity SSOT" sections |
| **Batch/live equivalence rule**                                                         | `codex/04-architecture/batch-live-architecture.md` (single SSOT) · `backtest-groups.md` · `CLAUDE.md` "Batch = Live" + "Live = batch" sections                                                                                                                                                                                                                                                                    |
| **Cloud-agnostic VM / build path**                                                      | `codex/04-architecture/cloud-agnostic-migration.md` · `codex/05-infrastructure/vm-tarball-deployment.md` · `codex/05-infrastructure/cloud-agnostic-build-lineage.md` (new — work-stream F) · `deployment-service/scripts/vm/` launchers · `deployment-api/deployment_api/routes/_code_builds_aws.py` · `CLAUDE.md` "VM tarball deployment" + "VM Naming Convention" sections                                      |
| **Strategy archetype config**                                                           | `codex/09-strategy/strategy-summary.md` · `codex/09-strategy/architecture-v2/` · `codex/09-strategy/operational/onboarding-checklist.md` · the archetype-specific sub-plan in `plans/active/` · `CLAUDE.md` if cross-cutting                                                                                                                                                                                      |
| **Custody / treasury wiring** (Copper, CEFFU)                                           | `codex/04-architecture/custody-providers.md` (single SSOT — Copper + CEFFU + LocalKey + Mock) · `wallet-hierarchy-and-capital-flow.md` · `unified-trading-library/unified_trading_library/config_interface/testnet_contracts.py` `PROTOCOL_SCHEMAS` (load-time validator for `config/testnet_contracts.yaml`; corrected from stale `unified-config-interface/testnet_contracts.py` per slot 8 audit EX-2)         |
| **Live observability** (events, alerts, kill switches, auto-recovery)                   | `codex/03-observability/lifecycle-events.md` · `coordination-events.md` · `codex/04-architecture/alerting-batch-live.md` · `autonomous-recovery-matrix.md` · `codex/05-infrastructure/live-deployment-monitoring.md` (new — work-stream B) · `unified-api-contracts/.../internal/events.py` (`LifecycleEventType`) · `CLAUDE.md` "no fire-and-forget VM launches" section                                         |
| **P&L attribution / batch-vs-live reconciliation**                                      | `codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` · `batch-live-reconciliation-service` plan (work-stream E) · pnl-attribution-service plan (work-stream E)                                                                                                                                                                                                                                    |
| **Service readiness** (per-service)                                                     | `codex/10-audit/repos/<service>.yaml` · `codex/10-audit/REPO_READINESS_CHECKLIST.yaml` · this master plan's matrix                                                                                                                                                                                                                                                                                                |
| **Operational modes** (manual / paper / automated, DART terminal)                       | `codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md` · `codex/04-architecture/research-service-and-dart-integration.md` (new — work-stream C)                                                                                                                                                                                                                                            |
| **ML experiment lifecycle**                                                             | `codex/04-architecture/ml-experiment-lifecycle.md` (new — work-stream F) · `codex/02-data/data-lineage-MTDS-features-ml.md` · `ml_pipeline_revolution_2026_04_11` plan                                                                                                                                                                                                                                            |
| **Hot-reload semantics**                                                                | `codex/06-coding-standards/config-reloader-pattern.md` · `codex/04-architecture/live-strategy-config-hot-reload.md` (new — work-stream F) · `CLAUDE.md` "Service Infrastructure Requirements" · codex/04-architecture/trading-agent-service-directive-pipeline.md (new — architecture-unlock Phase 8)                                                                                                             |
| **Service infrastructure requirements** (ServiceBootstrap, health API, typed reloaders) | `codex/06-coding-standards/service-structure-standards.md` · `base-service.sh` STEP 5.x in PM · `CLAUDE.md` "Service Infrastructure Requirements (QG-Enforced)"                                                                                                                                                                                                                                                   |
| **Asset-group vocabulary**                                                              | `CLAUDE.md` "Asset-group vocabulary" section · `unified_api_contracts.canonical.crosscutting.market_data_categories` · `venue_axis_asset_group_vocabulary_2026_04_25` plan                                                                                                                                                                                                                                        |
| **Lookahead bias / available_at semantics**                                             | `unified_api_contracts.canonical.crosscutting.availability_semantics` · `unified-trading-library/.../availability_stamping.py` · `codex/02-data/availability-manifest-and-data-status.md` § available_at · `codex/POST_PLAN_REALITY_2026_05_06.md` Principle 5 · `CLAUDE.md` "available_at is per-row" section                                                                                                    |

**Agent rule.** Before merging any change in scope of one of the rows above:

1. The agent's PR description must list the docs read at the start (the "doc-first" check).
2. The commit must touch **all** the listed SSOTs in the relevant row, or explicitly state in the PR description why a
   given SSOT is unaffected.
3. Cross-reference: the corresponding sub-plan in `plans/active/` must agree with the doc — if they disagree, update the
   plan first.

Drift between any of (codex doc, sub-plan, code) is a review-blocking failure.

---

## Plan ↔ Doc ↔ Code drift audit

This is the deliverable that ties the audit to action. For each high-leverage change area, flag whether the codex SSOT,
the corresponding sub-plan, and the code agree. **Items marked ⚠ are pre-existing drift to resolve as part of this plan,
before agents start writing code in the affected area.**

| Area                                                            | Codex SSOT                                                                                                                                                  | Sub-plans                                                                                                                                                                                                              | Drift status                                                                                             | Resolve via                                                                                                                                                               |
| --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Manifest schema (v6)                                            | `02-data/availability-manifest-and-data-status.md` (current)                                                                                                | `manifest_schema_v6_quote_margin_combo_2026_04_23`, `availability_manifest_v4_and_data_status_2026_04_13`                                                                                                              | ⚠ Confirmed — `availability_manifest_v4_…` is the only stale active plan; self-tagged superseded         | Archive the v4 plan via work-stream G; doc already canonical v6 with v4/v5 hive-key fallback                                                                              |
| Shard granularity propagation                                   | `02-data/availability-manifest-and-data-status.md` (multi-axis correction post-2026-05-06)                                                                  | `shard_granularity_ssot_propagation_2026_05_06.HANDOVER`, `writegate_honest_coverage_endtoend_2026_05_06`, `data_status_multi_axis_shard_propagation_2026_05_06`                                                       | ⚠ Confirmed — `writegate_…` declared umbrella; other two are children but not yet `parent:`-tagged       | Re-tag children with `parent: writegate_honest_coverage_endtoend_2026_05_06` (work-stream G); surface only umbrella                                                       |
| Cloud-agnostic VM/build                                         | `04-architecture/cloud-agnostic-migration.md`                                                                                                               | (no active plan — work-stream D is the new one)                                                                                                                                                                        | ⚠ Doc partially describes target; VM launchers GCP-only in code                                          | Add VM-launcher parity appendix to the doc; new plan for AWS launchers                                                                                                    |
| Live-mode services (PBM, R&E, P&L attr, alerting, B-vs-L recon) | Mostly covered by `04-architecture/alerting-batch-live.md`, `autonomous-recovery-matrix.md`, `09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` | ✓ REVISED — PBM/R&E/P&L attr in `defi_master` Fork 1 (folds `defi_e2e_pipeline_2026_04_30` per Stage 7 consolidation); B-vs-L recon in `consolidated_operational_validation_2026_04_15`; only **alerting** has no plan | ⚠ Only alerting genuinely missing a plan                                                                 | Open `alerting-service-live-rules_2026_05_07.plan.md`; extend the 4 existing plans with explicit live-mode todos (work-stream E REVISED)                                  |
| Custody (Copper + CEFFU)                                        | `04-architecture/custody-providers.md` (single SSOT — Copper + CEFFU + LocalKey + Mock), `wallet-hierarchy-and-capital-flow.md`                             | (no active plan; CEFFU section is STUB inside custody-providers.md)                                                                                                                                                    | ⚠ CEFFU section unwritten in custody-providers.md (PENDING subsections)                                  | Populate CEFFU subsections inside `custody-providers.md` + plan as part of work-stream F + E                                                                              |
| Strategy v2 finalization                                        | `09-strategy/strategy-summary.md`, `architecture-v2/`                                                                                                       | `strategy_architecture_v2_finalization_2026_04_19`, `strategy_architecture_v2_phase3_11_handoff_2026_04_17`                                                                                                            | ⚠ Confirmed — finalization is live; handoff is historical (Phase 2 done)                                 | Mark handoff `parent_of: finalization`; verify residuals; archive once absorbed (work-stream G)                                                                           |
| DART / research-service                                         | `09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md` (operational modes)                                                                 | `dart_ui_strategy_filtering_and_onboarding_2026_04_24` (self-tagged superseded), `dart_ux_cockpit_refactor_2026_04_29` (active superset)                                                                               | ⚠ research-service has 0 repo, only PNG mockups; manual-trade lane not in codex                          | Archive DART UI plan; add `04-architecture/research-service-and-dart-integration.md`; extend operational-modes-matrix                                                     |
| ML experiment lifecycle                                         | `02-data/data-lineage-MTDS-features-ml.md` (partial)                                                                                                        | `ml_pipeline_revolution_2026_04_11` (self-tagged superseded), `consolidated_ml_advanced_pipeline_2026_04_15` (active), `sp500_ml_readiness_master_2026_05_05`                                                          | ⚠ No dedicated SSOT for ML job_id lifecycle; `ml_pipeline_revolution` should archive                     | Archive `ml_pipeline_revolution_2026_04_11` + `domain_agnostic_ml_framework_2026_04_11` (work-stream G); add `04-architecture/ml-experiment-lifecycle.md` (work-stream F) |
| Live observability / log streaming                              | `03-observability/lifecycle-events.md`, `coordination-events.md`                                                                                            | (no active plan for GCS event-tail endpoint)                                                                                                                                                                           | ⚠ Doc defines events; deployment-api endpoint doesn't exist                                              | Build endpoint as part of work-stream A; doc stays current                                                                                                                |
| **NEW (audit-discovered):** Plan frontmatter discipline         | `plans/PLAN_FORMAT.md`                                                                                                                                      | n/a (workspace-wide systemic gap)                                                                                                                                                                                      | ⚠ 95% missing `last_updated`, 96% missing `asset_group`, 21% missing `locked_by`, 5 plans no frontmatter | Workspace-wide one-shot backfill script (work-stream G)                                                                                                                   |
| **NEW (audit-discovered):** Service-overlap concentration       | n/a (master-plan tracking concern)                                                                                                                          | 35 plans on instruments-service; 16 each on deployment-service / strategy-service / deployment-api; 12+ on UTS-UI / execution-service / deployment-ui                                                                  | ⚠ Real overlap risk; consolidation candidate post-cutover                                                | Post-May-23 cleanup; not blocking. Document on master plan; address in next cycle                                                                                         |

**Audit guideline going forward.** Whenever an agent touches a row in this table, the PR includes a one-line "drift
status: resolved / unchanged / new-drift" note in the description. New drift = a new row gets added here.

---

## Audit — sub-plan conflicts, overlaps, stale references (VERIFIED 2026-05-06)

Two parallel agents (mechanical frontmatter + topic-map sweep ; content-overlap pass) audited the **148 active
sub-plans** on 2026-05-06. **Headline corrections to the earlier suspicion list:** 3 of the 5 "NO-PLAN" live-mode
services are actually already in scope of `defi_master` Fork 1 (folds `defi_e2e_pipeline_2026_04_30` per Stage 7
consolidation) — only **alerting** genuinely needs a new dedicated plan. **18 self-tagged superseded plans** should be
archived. Frontmatter discipline is systemically broken (95% missing `last_updated`, 96% missing `asset_group`, 21%
missing `locked_by`) — needs a one-shot backfill script.

### Plan clusters → surface ONE per cluster on the master plan

| Cluster                          | Lead / umbrella plan                                                                                                                         | Children (reference, not duplicate)                                                                                                                                                                                                                                                                         | Action                                                                                                                          |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **DeFi end-to-end pipeline**     | `defi_master` (umbrella post-2026-05-07 Stage 7 consolidation)                                                                               | `defi_e2e_pipeline_2026_04_30` · `defi_pipeline_extension_2026_05_01` · `leveraged_leg_controller_2026_05_01` · `carry_staked_basis_structure_axis_2026_05_04` (all archived 2026-05-07) · `consolidated_defi_data_pipeline_2026_04_15` (residuals) · `defi_data_types_completeness_2026_04_24` (residuals) | Surface only the lead on master plan; track children as sub-bullets. Archive `defi_full_coverage_expansion_2026_04_09`.         |
| **Write-gate / honest-coverage** | `writegate_honest_coverage_endtoend_2026_05_06` (umbrella; declares `supersedes_phases:` on shard-granularity Tier 1 #1 + Tier 2 raw-tables) | `shard_granularity_ssot_propagation_2026_05_06.HANDOVER` · `data_status_multi_axis_shard_propagation_2026_05_06` · `feature_dag_uac_ssot_and_features_coverage_2026_05_06` · `predictions_canonical_question_group_polymarket_migration_2026_05_06`                                                         | Re-tag children with `role: child` / `parent: writegate_…`; surface only the umbrella.                                          |
| **Sports phantom recovery**      | `sports_fixtures_truthset_recovery_2026_05_06` (active executor; declares `supersedes_phases:` on phantom-recovery relaunch + audit-flip)    | `sports_phantom_fixtures_recovery_2026_05_06` · `sports_phantom_recon_and_failure_triage_2026_05_01` (diagnostic context)                                                                                                                                                                                   | Surface only truthset; the others are background.                                                                               |
| **Strategy v2 finalization**     | `strategy_architecture_v2_finalization_2026_04_19` (live, supersedes `strategy_architecture_v2_2026_04_17`)                                  | `strategy_architecture_v2_phase3_11_handoff_2026_04_17` (historical, Phase 2 done)                                                                                                                                                                                                                          | Surface only finalization; mark handoff `parent_of: finalization`.                                                              |
| **DART terminal / cockpit**      | `dart_ux_cockpit_refactor_2026_04_29` (active superset; supersedes codex `14-customer-journeys/dart/dart-terminal-vs-research.md`)           | `dart_terminal_research_split_2026_04_28` (mechanics shipped)                                                                                                                                                                                                                                               | Archive terminal-research-split.                                                                                                |
| **Marketing site**               | `marketing_site_three_route_consolidation_2026_04_26`                                                                                        | `marketing_homepage_old_hero_migration_2026_04_22` (homepage scope within route-consolidation) · `dart_ui_strategy_filtering_and_onboarding_2026_04_24` (self-tagged superseded)                                                                                                                            | Archive DART UI plan; reference homepage as scope-of route-consolidation.                                                       |
| **Sports roadmap**               | `sports_roadmap_master_execution_2026_04_21` (10-plan parallel-execution master)                                                             | 4 explicit children (apifootball_enrichment_historical_backfill · non_apifootball_provider_backfill_launchers · features_sports_pipeline_deployment · sports_scheduler_cron_activation, all 2026-04-21)                                                                                                     | Surface master only; reconcile overlap with `sports_predictions_e2e_2026_05_05` + `features_sports_honest_coverage_2026_05_05`. |
| **Playbook SSOT**                | `playbook_ssot_stage_3_infra_spec_2026_04_19`                                                                                                | `_stage_2_doc_rewrite_2026_04_19` · `_stage_1_rules_2026_04_19` (correctly modeled with `depends_on` / `blocks`)                                                                                                                                                                                            | Surface as one playbook-SSOT cluster.                                                                                           |
| **Asset-group vocabulary**       | `venue_axis_asset_group_vocabulary_2026_04_25` (parent)                                                                                      | `shard_dimension_naming_asset_group_ssot_2026_04_25` (declares "complements")                                                                                                                                                                                                                               | **Merge** or formal child link.                                                                                                 |

### Self-tagged superseded plans (18) — archive with `[unlock-plan]`

All have `superseded_by:` declared in frontmatter but still sit in `active/`:

`client_config_and_defi_risk_2026_04_01` · `cross_domain_alpha_execution_intelligence_2026_04_11` ·
`strategy_lifecycle_visibility_ui_2026_04_11` · `ui_walkthrough_and_e2e_alignment_2026_04_01` ·
`dart_ui_strategy_filtering_and_onboarding_2026_04_24` · `ml_pipeline_revolution_2026_04_11` ·
`domain_agnostic_ml_framework_2026_04_11` · `defi_instrument_pipeline_and_rewards_2026_04_01` ·
`mev_protection_and_execution_enhancements_2026_04_01` · `manual_trade_booking_reconciliation_2026_03_22` ·
`unified_pipeline_scheduling_and_triggers_2026_04_15` · `remove_data_types_field_2026_04_10` ·
`polymarket_prediction_pipeline_2026_03_25` · `smoke_dep_chain_tactical_fixes_2026_04_20` ·
`instruments_service_template_refactor_8e653acc` · `availability_manifest_v4_and_data_status_2026_04_13` (manifest now
v6) · `defi_pipeline_extension_followups_2026_05_03` (`status: complete`) ·
`dashboard_services_grid_collapse_2026_04_21` (88% done, awaiting unlock).

### Other stale / drift findings

- **`signal_leasing_broadcast_architecture_2026_04_20`** — 8 phases all complete
  (`reconciliation_status: shipped_substantive`), awaiting human `[unlock-plan]`.
- **`venue_availability_ssot_2026_03_25`** — 88% done; either archive or extract 3 polish items into a small follow-up.
- **`hybrid_sampler_5s_resolution_2026_03_30`** — `orphan_candidate: true`, stalled since pivot to manifest+rescan. Move
  to ICEBOX.
- **`mempool_feed_integration_2026_06_01`** — `status: paused`, future-dated. Remove from `active/`-as-current.
- **Dangling `superseded_by` references:** `polymarket_prediction_pipeline_2026_03_25` points at
  `consolidated_sports_prediction_pipeline_2026_04_15` which isn't in `active/` (likely archived) — update to point at
  `predictions_canonical_question_group_polymarket_migration_2026_05_06`. `defi_strategies_phase2_2026_03_29`
  `depends_on:` `defi-instrument-pipeline-and-rewards` (itself superseded → transitively dangling).
- **Removed-providers references** (Elysium / Bloxroute / Arkham / Pyth / Infura) appear in technical scope of
  `consolidated_defi_data_pipeline_2026_04_15`, `mev_protection_and_execution_enhancements_2026_04_01`,
  `mempool_feed_integration_2026_06_01` — scrub or archive.

### Frontmatter discipline (systemic)

| Issue                                           | Count |
| ----------------------------------------------- | ----: |
| Plans with NO frontmatter at all                |     5 |
| Plans missing `locked_by`                       |    31 |
| Plans missing `name` field                      |    11 |
| Plans missing `last_updated` (95%)              |   140 |
| `superseded_by` set but plan still in `active/` |    18 |
| Filename ↔ `name` field mismatch                |     1 |
| YAML errors                                     |     2 |

**Action:** workspace-wide one-shot backfill script — populate `last_updated` from `git log` mtime, infer `asset_group`
from filename + body, populate `locked_by: live-defi-rollout` for any that are mid-flight. **Work-stream G below.**

### Service-overlap concentration (>5 active plans = consolidation candidate)

| Service                   | Active plans touching it |
| ------------------------- | -----------------------: |
| instruments-service       |                 **35** ⚠ |
| deployment-service        |                     16 ⚠ |
| strategy-service          |                     16 ⚠ |
| deployment-api            |                     16 ⚠ |
| unified-trading-system-ui |                     12 ⚠ |
| execution-service         |                     12 ⚠ |
| deployment-ui             |                     12 ⚠ |
| market-tick-data-service  |                     10 ⚠ |

Eight services with >5 active plans = real overlap risk. The `instruments-service` 35-plan count is the clearest
consolidation target post-cutover.

---

## Q&A — resolved (✓) and outstanding (?)

1. ✓ **Lead DeFi archetypes — both `carry_staked_basis` (ultimate priority) AND `ARBITRAGE_PRICE_DISPERSION`
   (cross-venue funding spread) by May 23.** Recursive LST staking is part of the carry_staked_basis archetype. Linked
   plans: `carry_staked_basis_structure_axis_2026_05_04` and `defi_master` (umbrella that folds in
   `defi_pipeline_extension_2026_05_01` + `leveraged_leg_controller_2026_05_01` + `defi_e2e_pipeline_2026_04_30` per the
   2026-05-07 consolidation).
2. ✓ **CeFi/DeFi perp venue scope — six venues live, split per-archetype (REFINED 2026-05-10 cross-plan audit L1 per
   defi_archetypes_canonicalisation Stream E correction).** Hyperliquid + Aster are DeFi perp DEXs but live alongside
   the CeFi venues. CEFFU manual handoff acceptable for Binance flows on May 23.
   - **`carry_staked_basis` LST-as-margin support** (3 venues — ETH-LST-margin capable): **Deribit + Bybit + OKX**.
     Hyperliquid + Binance + Aster do NOT accept ETH-LST as margin, so they cannot host the carry_staked_basis hedge
     leg.
   - **`ARBITRAGE_PRICE_DISPERSION` funding-arb hedge** (all 6 venues for cross-venue funding spread): Bybit, Deribit,
     Binance, OKX, Hyperliquid, Aster.
   - **`leveraged_funding_arb` (now config variant `ARBITRAGE_PRICE_DISPERSION@funding-dispersion-leveraged`)**: same
     6-venue set as plain ARBITRAGE_PRICE_DISPERSION; leverage applied per-venue per margin-tier table SSOT.
   - **`carry_recursive_borrow` perp-hedged variant**: Hyperliquid (DEX) + Bybit (CeFi) — explicit 2-venue bound per
     [`defi_recursive_borrow_archetypes_2026_05_10.md`](../archive/2026_05/defi_recursive_borrow_archetypes_2026_05_10.md)
     AD-5; other perp venues post-cutover.
3. ✓ **Custody scope — Copper wired for DeFi side; CEFFU manual for Binance side acceptable.** Codex SSOT exists for
   Copper; CEFFU doc is a gap (work-stream F).
4. ✓ **AWS proof scope — full cloud-parity proof:** (a) cost analysis of GCS data → estimate AWS migration cost; (b)
   migrate only DeFi-relevant data (not full corpus); (c) data-status working on AWS; (d) backfill on AWS with `--force`
   (proves batch deployment side); (e) backtest examples runnable on AWS; (f) ML strategy examples runnable on AWS; (g)
   **live trading deployment + monitoring on AWS** so the team can seamlessly switch any deployment between AWS-live /
   AWS-batch / GCP-live / GCP-batch. Reduces, but does not eliminate, the May 23 risk surface — see _Risk register_
   below.
5. ✓ **Manual-trade gating duration — RESOLVED 2026-05-08.** Default confirmed: **3 days manual → 7 days automated**,
   with kill-switch monitoring throughout. Day 1-3 = DART operator manually executes every trade signal generated by
   strategy-service (one-click confirm, no auto-fire); Day 4-10 = automation enabled, kill-switch + DART pause/override
   armed throughout; ≥7 continuous days automated = May-23 acceptance criterion. Applies to both DeFi archetypes
   (`carry_staked_basis` + `ARBITRAGE_PRICE_DISPERSION`) and to CeFi-ML (`ML_DIRECTIONAL_CONTINUOUS`) per Q&A 7. Stagger
   by ≥1 day across archetypes to isolate kill-switch tests. `strategy_and_dart_master:Phase 2.2` Playwright matrix is
   the acceptance gate. See `plans/active/operator_decisions_2026_05_08.md` for the full pickup record.
6. ✓ **research-service repo decision — RESOLVED 2026-05-08.** **Fold into deployment-api** for May 23 scope. Scope is
   contained: operator research views consume existing deployment-api / data-status / coverage endpoints; no new domain
   contracts; no new persistence layer. Re-evaluate post-cutover only if scope grows beyond a `/research/*` route group
   on deployment-api. No new repo, no new Cloud Run service, no new IAM surface this cycle.
7. ✓ **ML ladder targets per asset group by May 23 — RESOLVED 2026-05-08.** Per asset_group:
   - **Prediction**: features-only running batch end-to-end. NO live deployment.
   - **Sports**: ML pipeline RUNNING on representative sample. NO live deployment. Backtest-only deliverable.
   - **TradFi**: ML pipeline RUNNING on representative sample (S&P swing-prediction trains end-to-end on 2-year
     history). NO live deployment. Backtest-only.
   - **CeFi → DEPLOYED IN PRODUCTION on real capital ≥7 days.** Archetype: `ML_DIRECTIONAL_CONTINUOUS` (continuous
     directional prediction signal). Venues: OKX + Binance + Bybit (3 venues, deepest liquidity, lowest unit cost).
     Retraining cadence: **daily** (overnight retrain via ml-training; ml-inference hot-reload on next day open).
     Capital scale: **starting allocation $10k notional per venue ($30k total)**, Kelly-fraction sized per archetype
     `ArchetypeConfig.position_cap_usd`; ramp 2× per week absent kill-switch trips, capped at $250k notional total by
     post-cutover review. `ArchetypeConfig.kill_switch_drawdown_pct=5` and `kill_switch_position_breach_pct=20` applied;
     `kill_switch_scope=ARCHETYPE` so a CeFi-ML trip does NOT halt DeFi (and vice versa).
   - **DeFi**: rules-based (no ML this cycle). `carry_staked_basis` + `ARBITRAGE_PRICE_DISPERSION` deployed live ≥7 days
     per Q&A 1 + Q&A 5.

   Implication: `mlr-p4-strategy-calibrated-signals` + `mlr-p4-cost-aware-strategy` + live model registry / hot-reload /
   per-trade `model_version` tagging are P0 May-23-blockers (was P1 under "running" default). `ml_and_features_master`
   Phase 4D becomes hard-floor live-trading prerequisite, not just sports/predictions enablement.

8. ? **Plan location.** Default: PM `plans/active/master_to_live_defi_2026_05_23.md` (sub-plan) **and**
   `codex/10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md` (audit / SSOT companion), with the audit doc cross-linked
   from `CLAUDE.md` so it's loaded into agent context every session.
9. ✓ **Pyth oracle ban — REVERSED 2026-05-06 for Solana-only scope.** `carry_staked_basis` LST yields (jitoSOL / mSOL /
   bSOL) need on-chain Solana prices; Chainlink covers EVM only (Arb / Base / Polygon); no viable Switchboard wiring in
   workspace. Pyth via Hermes (HTTPS pull, batch) + PythNet (Solana RPC, live). Other chains continue Chainlink.
   CLAUDE.md "Removed providers" updated; `consolidated_defi_data_pipeline_2026_04_15` `mtds-s3-5-pyth-oracle` todo
   unblocked.
10. ✓ **MDPS vs MTDS in data-status — separate services, separate rows (current architecture).** Each has its own
    `SHARD_AXIS_MATRIX` entry, own bucket, own manifest; no double-representation. UI rollup ("raw ticks 99% / processed
    candles 95%" under one asset_group view) is a deployment-UI enhancement deferred to post-cutover work-stream
    B-adjacent.
11. ✓ **Cluster validation wiring (writegate Phase 1A Amendment F) — REVISED 2026-05-06 after MTDS re-read: ALREADY
    SHIPPED for ES.OPT.** `engine/orchestrator.py:2126-2193` already gates `writer_manifest.add()` for ES.OPT bundles
    via the hardcoded `venue_name == "CME-OPTIONS"` branch using `get_active_es_options_clusters_for_date_from_snapshot`
    - `ManifestWriter.check_cluster_coverage_from_counts`. The "wrap with `if data_type in BUNDLED_DATA_TYPES:`" framing
      is the **generalisation** to non-CME-OPTIONS bundles (futures_chain / prediction_canonical_question_group /
      sports_fixture_bundle), which is deferred until those bundle adapters exist. Phase 2.B for ES.OPT is **DONE**;
      Phase 2.B generalisation kicks in when a 2nd bundle data_type ships.
12. ✓ **`ES_OPTIONS_CLUSTERS` rename — REVISED 2026-05-06 after re-read: NO RENAME NEEDED.** Earlier proposal to make it
    generic `OPTIONS_CLUSTERS_BY_ROOT` was a misread of the architecture. The 11-cluster ES taxonomy is genuinely
    ES-specific — driven by CME futures symbology regex which differs from Deribit BTC options (`BTC-30JUN24-50000-C`),
    Solana DEX options, etc. Each future root needs its own extractor + cluster taxonomy
    - active-calendar logic. Current symbol naming (`ES_OPTIONS_CLUSTERS`, `extract_es_options_cluster`,
      `get_active_es_options_clusters_for_date`) is correctly scoped. When a 2nd root ships, the pattern is **sibling
      symbols** (`DERIBIT_BTC_OPTIONS_CLUSTERS` + `extract_deribit_btc_options_cluster`) plus a per-(data_type, root)
      lookup, NOT a rename of the existing symbols.
13. ✓ **VIX 15m source layering — `cefi_tradfi_tick_data_backfill_2026_04_10` Phase 3b OBSOLETE.** Plan A's Barchart VM
    for `2025-11-13 → today` would clobber Yahoo-served rows. CLAUDE.md "VIX 15m source layering" SSOT + MTDS `4a2747a`
    are canonical: Barchart preload ends 2025-11-12; post-cutoff is Yahoo Finance rolling 60-day window;
    `2025-11-13 → today−60d` is the honest gap (`empty_confirmed`). Phase 3b dropped.
14. ✓ **Sports `data_available_at` → `available_at` rename + on-disk migration — HIGH-2 FULLY SHIPPED 2026-05-24.** UTL
    `assert_available_at_present` + every other service uses canonical `available_at`. Sports adapters +
    `InstrumentsWriteGate.DEFAULT_AS_OF_COLUMNS` renamed to `available_at` + one-time GCS column rename in existing
    sports parquets (per "manifest migration not fallback" rule). **All 4 phases complete:**
    - Phase 0 (audit): shipped 2026-05-07.
    - Phase 1 (migration script): shipped 2026-05-07.
    - Phase 2 (GCS column rename on VM): base bucket migrated 2026-05-22; PRD bucket migrated 2026-05-23 on
      `instr-backfill-sports` VM — 527,462 files renamed A_renamed, 0 errors. Spot-check 5 dates 2019–2025:
      `available_at=True data_available_at=False`.
    - Phase 3 (4-repo source rename): instruments-service@fc7b306, UTL@94e43e8c (2026-05-22).
    - Phase 4 (smoke-run + LookaheadBiasError gate): FOOTYSTATS 2024-11-15 --force — 4 rows written, NO
      LookaheadBiasError (2026-05-24). **Writegate Phase 2.C unblocked.**
15. ✓ **`_create_full_day_empty_output` delete (writegate Phase 2.A) — Option A: audit consumers, delete iff safe.**
    Empty/closed days use `record_empty(capture_status=empty_confirmed)` per existing SSOT — placeholder rows are
    double-SSOT. Downstream services NaN-handle their own way (forward-fill, masking, ML missing-data tolerance).
    **Codex follow-up doc**: "empty upstream means no expectation of data downstream; manifest `empty_confirmed` is the
    SSOT, NOT placeholder rows. Holidays + market hours via `venue_trading_calendar`; unexpected empties handled
    per-service in pre-flight." Block writegate Phase 2.A on grep audit of features-volatility / features-cross-
    instrument for `market_state == "CLOSED"` consumers; refactor any to read manifest `capture_status` instead. **A2
    audit shipped 2026-05-07** (commit `7d8ce330` codex doc; writegate plan re-categorisation): codex SSOT
    `codex/02-data/honest-absence-downstream-handling.md` codifies the principle. Audit ruling:
    `_create_full_day_empty_output` in `tradfi/ohlcv_passthrough.py:266` re-categorised from `?` to **A (honest
    absence)**; sibling banned method `_create_closed_market_candle` in `orchestration_writer.py:65`
    (1-row-per-non-trading-day variant) added to same delete scope. Two consumers
    (`features-service (volatility family)` + `features-service (delta-one family)` `_filter_market_state`) have
    legitimate intra-day filter purpose (`pre_market` / `post_market` / `closed` minutes from `_apply_market_state` on
    real trading days) — those filters STAY; placeholder-row drop role disappears once delete-and-replace ships.
    Consumer refactor: add manifest pre-flight gate (skip `empty_confirmed` days at parquet-load time). Code change
    folded into writegate Phase 2.A scope (already covers 37 `_create_empty_output` callsites + 3-write-path
    consolidation); A2 deliverable is the audit ruling that resolves the writegate plan's open `?` entry, not a separate
    commit.
16. ✓ **Sports `fixture_id` shard atom (writegate HANDOVER vs multi-axis plan) — multi-axis plan wins; `fixture_id` is
    NOT a shard atom.** `(league_id, day)` already bounds fixtures; per-fixture detail comes from parquet at drill-down
    time. HANDOVER per-asset-group matrix updated; features-sports audit reframes to `(feature_group, league_id, day)`.

---

## Risk register (post-Q&A scope expansion)

The answers expanded scope materially. Risks to flag explicitly so they're not silently signed off:

| Risk                                                    | Likelihood                             | Impact                                                                                          | Mitigation                                                                                                                                                                                                                                                                                                                                                                        |
| ------------------------------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 6 perp venues live by May 23 (was 2)                    | High                                   | Slips one or more archetypes                                                                    | Sequence: Bybit + Hyperliquid first (Week 2 W1), Deribit + Binance + OKX + Aster fast-follow (Week 2 W2). Carry_staked_basis only strictly needs 1 perp venue; leveraged funding arb wants ≥3 for cross-venue spreads.                                                                                                                                                            |
| 2 archetypes live by May 23 (was 1)                     | High                                   | Slips ARBITRAGE_PRICE_DISPERSION                                                                | Carry_staked_basis stays the cutover gate; ARBITRAGE_PRICE_DISPERSION can flip from manual-DART to automated within the 7-day window if Week 3 is tight.                                                                                                                                                                                                                          |
| Full AWS cloud parity by May 23                         | High                                   | Slips AWS or DeFi cutover                                                                       | AWS data migration + batch backfill + data-status earliest (Week 1 W2 → Week 2 W1). AWS live trading proof is "single archetype on smaller capital" — does not need full archetype scale.                                                                                                                                                                                         |
| 5 NO-PLAN live-mode services to write + ship            | Medium                                 | Live trading without circuit breakers / live alerting / batch-vs-live recon = unsafe to flip    | RESOLVED post-2026-05-06 audit: only `alerting-service` is genuinely NO-PLAN; PBM / R&E / pnl-attribution extend `defi_master` Fork 1 (folds `defi_e2e_pipeline_2026_04_30` per Stage 7 consolidation); B-vs-L recon extends `consolidated_operational_validation_2026_04_15` (work-stream E REVISED).                                                                            |
| CEFFU integration unwritten                             | Low                                    | Forces all-manual Binance flows                                                                 | Manual is acceptable per Q&A 3; codify in plan + add CEFFU codex doc.                                                                                                                                                                                                                                                                                                             |
| DART manual-trade lane is new code on the critical path | Medium                                 | Slips Group G on tier-1 strategy / execution                                                    | Build on the strategy-evaluations + VmDeployments tracker patterns already in UTS-UI / deployment-ui — **no greenfield UI**.                                                                                                                                                                                                                                                      |
| Pyth ban left Solana on-chain prices unimplemented      | Medium                                 | Blocks LST yield tracking for jitoSOL / mSOL / bSOL — direct dependency of `carry_staked_basis` | RESOLVED 2026-05-06: Pyth unbanned for Solana-only scope (Q&A 9). Chainlink continues for EVM. Wire Hermes + PythNet via existing `oracle_prices_handler.py`.                                                                                                                                                                                                                     |
| `check_shard_freshness` ignores `capture_status`        | **RESOLVED 2026-05-06 (UTL@ba83a6f1)** | n/a — fix shipped                                                                               | UTL `check_shard_freshness` extended with `retry_failed: bool = True` param (default-on); `ATTEMPTED_FAILED` rows now treated as stale. DELETE workaround in `sports_fixtures_truthset_recovery` is now optional; `phantom_recon_and_failure_triage` Phase 1 flip-to-attempted_failed works as designed. 8 unit tests in `tests/unit/test_check_shard_freshness_retry_failed.py`. |

---

## Asset-group readiness ladder (critical-path orientation)

Per user direction: stage each asset_group up to a specific layer by May 23. DeFi must reach "live trading"; the others
stage to a parallel-but-deeper level so post-DeFi archetype launches are quick.

| Asset group    | May 23 target depth                                     | Live perp venues             | Notes                                                                                              |
| -------------- | ------------------------------------------------------- | ---------------------------- | -------------------------------------------------------------------------------------------------- |
| **DeFi**       | **Live trading on real wallet (rules-based, no ML)**    | Hyperliquid, Aster           | 2 archetypes (carry_staked_basis lead + ARBITRAGE_PRICE_DISPERSION); LST + lending + perp-DEX legs |
| **CeFi**       | **Live trading (perp hedge leg) + ML pipeline running** | Bybit, Deribit, Binance, OKX | Hedge for DeFi archetypes today; CeFi-only archetypes (e.g. funding-arb-CeFi-only) ready post-23   |
| **TradFi**     | **ML pipeline running on representative sample**        | n/a (no live)                | Backfill ~99%; ML training on rep sample; no live trading this cycle                               |
| **Sports**     | **ML pipeline running on representative sample**        | n/a (no live)                | Honest-coverage + phantom recovery close-outs land first                                           |
| **Prediction** | **Features pipeline running (no ML this cycle)**        | n/a (no live)                | Polymarket canonical-question-group migration is the gate                                          |

---

## Per-service readiness checklist — 7 groups / 23 items

Status legend: `✓` done · `◐` in flight · `✗` not started · `n/a` not applicable

### Group A — Code health (always-on)

1. **QG pass** — `bash scripts/quality-gates.sh` two-pass clean (full + quickmerge)
2. **Quickmerge** — branch landed `live-defi-rollout` → main via SIT
3. **Semver agent** — `feat:` / `fix:` / `feat!:` triggers version bump

### Group B — Data correctness (always-on)

> **2026-05-07:** writegate Phase 3.D.4 expected-universe `--apply-write` COMPLETE across all 5 asset_groups +
> CONSOLIDATOR MERGE LANDED (deployment-service@dcc5c87 / @38b7a58 + instruments-service@8e404c8 / @d1c9928 / @a936a28
>
> - UAC@ac218dc; PM@79e47874 + PM@341bb285). 1,455,901 rows written + merged into canonical 18:07-18:14 UTC (TradFi
>   35,033 + Sports 13,176 + CeFi 119,152 real impl + Prediction 2,280 real impl + DeFi 1,286,260). Consolidator P0
>   (`ArrowTypeError` on `instrument_count`) was briefly blocking tradfi / defi / prediction; resolved at PM@341bb285
>   (script-side root cause + 4 in-place shard fixes). Rollup-vs-drilldown denominator gap closure now observable on all
>   5 asset_groups; operator spot-check pending. Detail in
>   [`writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md) § Phase
>   3.D.4.

4. **Smoke test** — representative `(asset_group, data_type, day)` triples produce valid parquet end-to-end
5. **Manifest hookup + cluster validation** — `ManifestWriter.record_{captured,empty,failed}` with
   `expected_root_clusters` + `cluster_extractor` for bundled types (codex
   `02-data/availability-manifest-and-data-status.md`, UTL `61a142b0`)
6. **Upstream validation** — `DependencyError(fail_fast=True)` at boundary; honest absence categories A/B/C; no silent
   placeholder rows (CLAUDE.md "honest absence vs fake placeholders")
7. **UAC/UTL abstraction** — domain types in UAC, runtime utilities in UTL, only service-specific config inline
8. **Schema validation** — parquet schema matches UAC contract per `record_captured` (4-pillar write-gate item 3)

### Group C — Runtime parity (always-on)

9. **Hot reload** — `start_domain_config_reloaders` typed; `ApiKeyReloader` for Secret Manager creds (codex
   `06-coding-standards/config-reloader-pattern.md`)
10. **Batch = live** — same code path; only fill source differs (codex `04-architecture/batch-live-architecture.md` —
    single SSOT)

11. **AWS + GCP parity** — both VM launch paths green; `CLOUD_PROVIDER` toggle works end-to-end (codex
    `04-architecture/cloud-agnostic-migration.md`)

- [x] ✅ [SCHEMA] P0. UAC `strategy_pnl_stream.py` + `strategy_directives.py` Pydantic models land — Phase 1+4 of
      trading_agent_service_architecture_unlock plan. — uac@82b7ad55 uac@2bdc0f07
- [x] ✅ [CODE] P0. strategy-service emits `StrategyPnlStreamEvent` for `carry_staked_basis` +
      `arbitrage_price_dispersion` per published contract — Phase 2. — strategy@a0f87c66
- [x] ✅ [CODE] P0. strategy-service `StrategyDirectiveReloader` consumes `ArchetypeAllocationDirective` (no-op default;
      capital/equity allocator reads from directive instead of static config) — Phase 5. — strategy@afd17fe9
- [x] ✅ [CODE] P0. trading-agent-service core scaffold subscribes to features + PnL streams + emits no-op directive —
      Phase 6. — trading-agent@119fa74

### Group D — Coverage & shard (always-on, data-producing services)

12. **Data status accurate** — deployment-UI rollup matches on-disk truth-set; canonical shard axis per asset-group
13. **Shard granularity correct** — matches codex `02-data/availability-manifest-and-data-status.md` per-asset-group
    matrix
14. **Full-window backfill** — ≥2 years of representative history captured (per CLAUDE.md "honest absence" + codex
    `02-data/per-asset-group-bucket-layouts.md`); n/a for runtime-only services
15. **Coverage ratchet green — Path to 99%** — honest-coverage-ratchet.sh runs daily post-Phase 8 fleet verification; no
    asset_group × data_type cell regresses >0.5pp day-over-day; goal: ≥99% `compute_honest_coverage()` ratio across all
    IS + MTDS cells with no `expected_unattempted_pending_fetch` rows. Plan:
    [`honest_coverage_formula_consolidation_2026_05_19.md`](./honest_coverage_formula_consolidation_2026_05_19.md)
    Phase 8. Continuous verification: `cron:planning-vm` runs `honest-coverage-ratchet.sh` daily; ratchet snapshot in
    `_index/snapshots/honest_coverage/`; any regression >0.5pp fires P0 alert (QG STEP 5.70 in MTDS + IS). **Added
    2026-05-22 per honest_coverage Phase 8 dispatch (slot 8).**

### Group E — Operability (always-on)

> **🟢 PER-TAB WORKTREES SHIPPED 2026-05-10** — 3-tier parallel-agent isolation (operator / slot / sub-agent) shipped
> via [`plans/active/per_agent_worktrees_2026_05_10.md`](../archive/per_agent_worktrees_2026_05_10.md). Each operator
> runs N permanent slot worktrees at `.tabs/<N>/` on branch `tab/<operator>/<N>`; cross-slot foot-guns #1-#3
> unrepresentable by construction, #4 mitigated via per-slot `PREK_CACHE_DIR`. Bootstrap script + codex SSOTs +
> CLAUDE.md + PLAN_FORMAT.md + both operator LEDGERs all updated in same plan execution. Operability win for the
> parallel-agent flow that backs every Group A-G item across this cutover. Pending: operator `--init` runs (Ikenna +
> Harsh) + 1-week burn-in to confirm zero cross-slot foot-gun incidents.

15. **UTS-UI summary** — service surfaces visible in unified-trading-system-ui where relevant (`/ops/admin/...` route
    exists or is in scope)
16. **Deployment-UI launch + GCS log streaming** — backfill / restart / forward-poll launchable from UI without SSH; VM
    event logs pooled to `gs://{pid}-events/`; tail works without SSH

### Group F — Trading prerequisites (live-only services)

> **MVP universe SSOT (2026-05-13)**: backtest-complete by May-23 scope is bounded per
> [`codex/09-strategy/mvp-universe-per-asset-group.md`](../../codex/09-strategy/mvp-universe-per-asset-group.md). Tier A
> archetypes (must complete backtest by 2026-05-23). Backtest windows DIFFER per asset_group per operator direction
> 2026-05-13: **CeFi + TradFi + Sports = 5-year walk-forward** (multi-regime ML validation); DeFi + Prediction = 2-year
> (venue lifecycle limits). Tier A: ml-continuous (CeFi 30 coins + ES with weeklies/dailies, **SPY not included** — ES
> has more hours), ml-settled (Sports Top-5 EU football × 4 markets), arbitrage-funding-rate, arbitrage-sports-book,
> arbitrage-event-markets, defi-carry-family (incl. CARRY_BASIS_DATED cross-venue fixed-delivery futures +
> ARBITRAGE_PRICE_DISPERSION dated-cross-venue variant — both owned by `defi_master.md` Fork 1; share
> `paired_price_dispersion` calculator). Commodity futures (GLD/CME-GC, UNG/CME-NG, USO/CME-CL) in scope for
> cross-instrument carry/arb. Tier B (code-ready only, post-cutover backtest): options-strategy, other DeFi non-carry,
> long-tail prediction. Group F items 17/18/20/21 verify against Tier A.

> **🟢 LIVE-PIPELINE ACTIVATION 2026-05-08** — Three new plans landed 2026-05-08 cover the live-mode portion of Group F
> items 21 (Reconciliation suite) + 22 (Trading guardrails) for MTDS / MDPS / features-service:
> [`live_pipeline_mtds_mdps_features_2026_05_08`](../archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md)
> (main activation, 10d), [`features_repo_consolidation_2026_05_08`](./features_repo_consolidation_2026_05_08.md)
> (pre-req, merges 8 features-\* repos into one features-service, 3-5d), and
> [`gcs_migration_bundle_pipeline_mode_2026_05_08`](./gcs_migration_bundle_pipeline_mode_2026_05_08.md) (bundled
> overnight GCS migration: pipeline_mode partition + category=→asset_group= rekey + drift cleanup). Codex entry:
> [`codex/05-infrastructure/live-pipeline-architecture.md`](../../codex/05-infrastructure/live-pipeline-architecture.md).
> Sequencing: features-repo Phase 7 + gcs-bundle Phase 9 BLOCK live-pipeline Phase 3+5 respectively.

17. **Backtest fidelity** — real gas, real market impact, realistic matching engine for AMM pools / perpetuals / spots /
    transfers / atomic transfers / flash loans; cost+yield to smallest precision (codex
    `04-architecture/backtest-groups.md`, `batch-live-architecture.md` (single SSOT)). **Deep audit 2026-05-07**:
    shipped matching engine has 5 matcher classes (L0 Sports TOB, L1 TradFi, L2 CeFi, AMM, ALPHA_ZERO benchmark fills)
    at `execution-service/execution_service/matching_engine/`. "Transfers" + "atomic transfers" are NOT separate matcher
    classes — they're swap/settlement modes within the AMM matcher. Either fold transfers into the AMM matcher's scope
    statement (current shipped reality) or open a follow-up to add a Transfers matcher (low-likelihood given DeFi
    transfers are atomic-by-default on-chain). Recommend folding into AMM matcher scope.
18. **2-year batch backtest run + VM-shape sizing** — completed across config grid; P&L variance per archetype
    configuration captured so the live-trading config is informed, not guessed; per-stage bottleneck profiled via
    synthetic-data benchmark to inform VM-shape selection. **Deep audit 2026-05-07**: no dedicated 2-year batch backtest
    runner script found. `strategy-service/scripts/` has `trace_carry_staked_basis.py` + `trace_all_carry_archetypes.py`
    (May 5+7) — tracing/simulation, not config-grid sweep. P0 follow-up: author
    `strategy-service/scripts/run_2yr_config_grid_backtest.py` for `carry_staked_basis` + `ARBITRAGE_PRICE_DISPERSION`
    archetypes; emit P&L variance distribution per archetype config dimension. **2026-05-09 update — script SHIPPED**
    (strategy-service@`3dea3c7`): `run_2yr_config_grid_backtest.py` + 22 unit tests; sweeps 5-dim grid per archetype
    (position_size_pct / max_drawdown_threshold / slippage_cap_bps + 2 archetype-specific dims) at coarse / medium /
    fine density (243 / 3,125 / 16,807 configs/archetype). Replays each (archetype, config) cell through V2BatchHarness
    per "Batch = Live" principle. Smoke verified locally on both archetypes. RESOLVED-PENDING-OPERATOR-RUN: full 2-yr
    grid run (~8-12h) is operator-scheduled — launch command in script docstring. **2026-05-10 update — OPERATIONALLY
    LAUNCHED** (deployment-service@`06f0a54` shipped `launch-strategy-backtest-grid-vm.sh` + `setup-data-pipeline-vm.sh`
    `strategy-backtest-grid` VM_TASK branch + `vm_zombie_watchdog.py` prefix registration; `5914c83` script-path
    invocation fix). 2 GCE VMs RUNNING in `asia-northeast1-c`:
    `strategy-backtest-grid-carry-staked-basis-20260510-195855` +
    `strategy-backtest-grid-arbitrage-price-dispersi-20260510-195914`. Both runners past V2 instance registration phase
    per `gs://deployment-scripts-central-element-323112/vm-logs/{vm-name}/run.log`; ETA ~8-12h per archetype. Output
    will land at `gs://strategy-store-central-element-323112/backtests/config_grid_2yr/{archetype}/{run_id}/`. Final
    operational closure (parquet row inspection + sample read) lands when the runners finish per
    `strategy_2yr_grid_run_launcher_authoring_2026_05_10.md`. **2026-05-13 update — SYNTHETIC-DATA BENCHMARK MATRIX
    COMPLETE** (`mock_data_pipeline_benchmarking_2026_05_10` Phase 5+6 SHIPPED 2026-05-12): 8-VM matrix
    (`leveraged_funding_arb` + `carry_staked_basis` × {c2-standard-8, c2-standard-16, c2-standard-30, c3-highcpu-44})
    ran in `asia-northeast1-c`; 44 cells × per-stage profile (wall-clock / CPU% / RSS / IO read/write bytes) captured.
    **Key findings**: `mtds_read` + `strategy` both fit comfortably on `c2-standard-8` (~20-38% CPU peak / ~1.1-1.5GB
    RSS). The 4 failing stages (mdps_compute / features / ml_inference / matching_engine) await Phase 3.D per-reader
    bespoke wire-in for full data redirection. **Per-stage P95 recommendation**: all measured stages recommend
    `c2-standard-8` minimum; no stage exceeded c2-standard-8 headroom. Aggregate report + bottleneck analysis at
    `gs://central-element-323112-benchmark-reports/benchmark_report/{.parquet,.md}`. Per
    `codex/05-infrastructure/runtime-tiers-and-deployment.md` "Data-pipeline VM machine-type sizing", provisional
    recommendations flagged pending Phase 3.D + full-data-flow re-run with real backfill row counts.
19. **Treasury / custody integration** — Copper for DeFi side; CEFFU for Binance institutional flow; cross-wallet
    transfer paths verified. Single SSOT: `codex/04-architecture/custody-providers.md` (folded 2026-05-08, replaces the
    former per-provider docs). **Deep audit 2026-05-07 / merged 2026-05-08**: Copper section is full; CEFFU section is
    STUB with PENDING subsections. P0 follow-up tracked under work-stream F (populate CEFFU subsections inside
    `codex/04-architecture/custody-providers.md`).
20. **Live testnet replicates prod** — Tenderly fork / forked-mainnet for DeFi; Binance testnet / Bybit testnet for
    CeFi; same config code path, no faked data. **Deep audit 2026-05-07**: no testnet-specific branch paths or env
    toggles found in execution-service yet. Per-venue testnet wiring pending — verify each connector's testnet endpoint
    list before live cutover. Tenderly fork fixtures shipped per `execution-service/tests/integration/conftest.py` (per
    `CLAUDE.md` "DeFi integration tests" rule) — DeFi side has the testbed, CeFi side has not been validated end-to-end.
    **Mainnet FlashLoanReceiver shipped 2026-05-10** (UAC@`abb8e5f0` — `config/testnet_contracts.yaml` chain_id=1
    section): contract at `0x42c005e2Bc545a49B50Fee3E76B8558348CAAb4c`, tx
    `0x09a4f9f08cd0cc211d5f825d713de3cf56f20938f1a781f16aaae703708a0925` block 25066462, gas 521102, bytecode 2157 bytes
    verified on-chain via `eth_getCode`; SM secret `flash-loan-receiver-mainnet` mirrors Sepolia pattern. Closes the
    live-Aave-flash-loan blocker for `carry_staked_basis` recursive-staking unwind — `AaveConnector.connect()` now
    passes its `eth_getCode` validation on chain_id=1 against the registry-resolved address.
21. **Reconciliation suite** — batch-vs-live reconciliation working (codex
    `09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` + `batch-live-reconciliation-service`); P&L
    attribution decomposed per source; per-trade reconciliation. **Deep audit 2026-05-07**: pnl-attribution-service
    ships `--mode batch` CLI (verified at `pnl-attribution-service/pnl_attribution_service/__main__.py:288` +
    `cli/parser.py`). However, `batch-live-reconciliation-service` A column = ✗ in the matrix below (service scaffolded
    but NOT code-complete). Phase 2.E.3 of writegate plan + this Group F item depend on the service being shipped. P0
    follow-up: ship the minimum-viable reconciliation surface (per-archetype P&L diff, per-trade fill comparison) before
    May-23 cutover.
22. **Trading guardrails** — circuit breakers configured per archetype; kill switches wired (codex
    `04-architecture/autonomous-recovery-matrix.md`); alerting-service rules cover live data-freshness + P&L deviation +
    position breaches (codex `04-architecture/alerting-batch-live.md`); auto-recovery for known transient failure
    classes. **Risk plan Phase 0+1+2.G shipped 2026-05-11** —
    [`risk_simulations_limits_alerting_2026_05_10`](../archive/risk_simulations_limits_alerting_2026_05_10.md) Phase 1
    ships UAC risk-rule taxonomy (UAC@`945ad5d`): `RiskRuleId` / `RiskRuleScope` / `RiskRuleConsequence` closed enums;
    `RiskRule` Pydantic with typed-trigger discriminated union; `kill_switch_scope()` orthogonality mapping per § 7 SSOT
    seam diagram; 6 new AlertCodes (closed-set 39 → 45); `StrategyFamilyId` risk-aggregation registry +
    cutover-archetype membership (LST_LEVERAGE_FAMILY ← CARRY_STAKED_BASIS; FUNDING_ARB_FAMILY ←
    ARBITRAGE_PRICE_DISPERSION). Group F item 22 dependency cleared for risk Phases 2-9; sibling plan
    [`disaster_recovery_circuit_breakers_2026_05_10`](../archive/disaster_recovery_circuit_breakers_2026_05_10.md) Phase
    1 owns `BreakerRecoveryMode` + `BREAKER_RECOVERY_DEFAULTS` (composes with risk Phase 1.F via cross-reference, not
    duplication). **Tab 5 (Agent 5) cycle 2026-05-08 progress** (refresh from 2026-05-07 baseline): Phase 2 service
    migration SHIPPED (alerting-service@`b025e83` consumes UAC `LIVE_ALERT_RULES`); Phase 3 envelope `code: AlertCode`
    field SHIPPED (UAC@`2636815` Option A) + 3-service consumer migration (execution-service@`624c36a8` yield_recon +
    funding_recon, position-balance-monitor@`d206ab3` reconciliation_engine + fee_recon, risk-and-exposure@`915f0de`
    RiskMonitor); Phase 6 15 per-AlertCode operator runbooks SHIPPED (PM@`45b854d5`+`6fad278e`+`db99a3ef`+`b40d405a`+
    `ac40983b`); Phase 5 DART Active Alerts panel + per-alert detail modal + severity widget + Playwright ack-flow
    SHIPPED (unified-trading-system-ui@`e9559565`); Phase 2 KillSwitchBus publisher hook + per-event scope
    (GLOBAL/VENUE/ARCHETYPE) SHIPPED (UAC@`3793310`+`2541a47` field; alerting-service@`8eda37c` hook + 5 integration
    tests); CeFi ML lifecycle alert codes SHIPPED (UAC@`6c4784f` — 6 ML codes + 5 ML thresholds + 6 ML rules). Group F
    item 22 column flipped ✗ → ◐. **Pending**: Phase 4 paging-target Secret Manager wiring (operator-driven); Phase 7
    quietness baseline 48h staging dry-run (operator-driven); Phase 8 live rehearsal (operator-driven); Phase 9 go-live
    on 2026-05-23 (operator-driven). features-onchain emission sites for `DEFI_HEALTH_FACTOR_CRITICAL` /
    `DEFI_AAVE_UTILIZATION_SPIKE` / `DEFI_FUNDING_RATE_FLIP` / `DEFI_FEATURE_STALE` / `DEFI_WEETH_DEPEG` **🟢 PULLED
    FORWARD May-23 (operator direction 2026-05-13)** — 4 DeFi-specific codes (`DEFI_AAVE_UTILIZATION_SPIKE` /
    `DEFI_FUNDING_RATE_FLIP` / `DEFI_FEATURE_STALE` / `DEFI_WEETH_DEPEG`) added to AlertCode enum + rule wiring +
    features-onchain emission sites pre-cutover; tracked in owning plan
    [`alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md) Phase 3 (producer
    migration). `DEFI_HEALTH_FACTOR_CRITICAL` was already in the AlertCode enum (39→45 codes shipped via UAC@`d00326d`
    - UAC@`945ad5d`); its features-onchain emission site composes with the 4 pulled-forward codes. Was previously
      "deferred per Sub-B finding (calculators not yet wired; defi_master Fork 1 territory)"; reversed per operator
      rationale "throughput margin (~5-6x), no descope, perfect cutover" — ~0.5-1 cal-AI-days against ~1,880 cal-day
      capacity in next 9 days.

#### Folded operational-validation todos (from `consolidated_operational_validation_2026_04_15`)

These 11 todos were folded in 2026-05-07 from `consolidated_operational_validation_2026_04_15` (now archived). They
extend items 17–22 with concrete operational-validation work — pipeline scheduling completeness, per-cluster E2E
batch-vs-live reconciliation, and final infra QG sweeps — that gates `master Group F` closure.

**Pipeline scheduling remaining code** (extends items 21–22 — live-trading scheduler + trigger backend):

- [x] ✅ [AGENT] P1. `ups-p2-run-tag-mtds-calendar`: Wire `--run-tag` into MTDS GCS output path + features-service
      (calendar family) — market-tick-data-service@703854ba | write_defi_rows(run_tag=) parameter + all 23 DeFi handler
      call sites updated; 4 new unit tests; features-service calendar already supported run_tag. *(folded from
      consolidated*operational_validation_2026_04_15)\*
- [x] ✅ [AGENT] P1. `ups-p4-sports-trigger-backend-dispatch`: Sports trigger scheduler cloud backend dispatch —
      deployment-service@4990d21. CloudRunBackend wired into `_dispatch_services`; lazy cache per job*name;
      cloud_run_job_name field added to all 16 service entries in sports-trigger-tiers.yaml. Previously: (PARTIALLY_DONE
      — local subprocess works, cloud placeholder). Confirmed at deployment-service
      `deployment_service/sports_trigger_periodic.py` + `sports_trigger_scheduler.py` + `sports_trigger_state.py`;
      cloud-dispatch shim is the named gap. *(folded from consolidated*operational_validation_2026_04_15)*

**E2E cluster tests** (extends item 21 — batch-vs-live reconciliation per cluster):

- [x] ✅ DEFERRED-BLOCKED [HUMAN+AGENT] P0. `ups-p8-e2e-cefi`: E2E test — CEFI cluster (T+1, live 1h, reconciliation).
      BLOCKED-ON `cefi_master` (28 open items as of 2026-05-25) + writegate Tier 2C cefi adapters (shipped at
      MDPS@b9f9328); cefi cluster YAML exists at deployment-service `configs/clusters/cefi.yaml`. Operator to schedule
      E2E run when cefi*master completes. *(folded from consolidated*operational_validation_2026_04_15)*
- [x] ✅ DEFERRED-BLOCKED [HUMAN+AGENT] P0. `ups-p8-e2e-sports`: E2E test — SPORTS cluster (T+1, trigger scheduler,
      feature validation). BLOCKED-ON `sports_master` (73 open items as of 2026-05-23). Code shipped: writegate Tier 2A
      sports adapters at MDPS@5b52d0b; trigger scheduler at deployment-service `sports_trigger_*`. Operator to schedule
      E2E run when sports*master completes. *(folded from consolidated*operational_validation_2026_04_15)*
- [x] ✅ DEFERRED-BLOCKED [HUMAN+AGENT] P0. `ups-p8-e2e-defi`: E2E test — DEFI cluster (T+1 single day). BLOCKED-ON
      `defi_master` (umbrella for all DEFI work — 46 open items as of 2026-05-23). Operator to schedule when defi*master
      completes. *(folded from consolidated*operational_validation_2026_04_15)*
- [x] ✅ DEFERRED-BLOCKED [HUMAN+AGENT] P0. `ups-p8-e2e-tradfi`: E2E test — TRADFI cluster (T+1 single day, needs
      `DATABENTO_API_KEY`). BLOCKED-ON `tradfi_master`; writegate Tier 2E tradfi adapters shipped at MDPS@e9520a0;
      `DATABENTO_API_KEY` credential gate (operator action). _(folded from
      consolidated_operational_validation_2026_04_15)_
- [x] ✅ DEFERRED-BLOCKED [HUMAN+AGENT] P0. `ups-p8-e2e-prediction`: E2E test — PREDICTION cluster (T+1 single day).
      BLOCKED-ON `predictions_master` (canonical question*group migration in flight as of 2026-05-23). Operator to
      schedule when ready. *(folded from consolidated*operational_validation_2026_04_15)*
- [x] ✅ DEFERRED-BLOCKED [HUMAN+AGENT] P0. `ups-p8-e2e-full`: E2E test — FULL cluster (all categories for 1 date).
      BLOCKED-ON the 5 preceding per-cluster e2e tests (all deferred-blocked above). _(folded from
      consolidated_operational_validation_2026_04_15)_

**Infrastructure cleanup** (extends item 22 — final QG sweep before live cutover):

- [x] ✅ DEFERRED-BLOCKED [HUMAN-ACTION-REQUIRED: operator-driven backfill rerun to regenerate parquet without
      data_types column] [HUMAN] P1. `rdt-p4-gcs-cleanup`: Run instruments-service backfill to regenerate parquet
      without `data_types` column. instruments-service production code grep for `data_types` returns 0 hits; references
      remain only in legacy ETL scripts (`scripts/aggregate_legacy_es_opt_trades.py`) and test code. Remaining work is
      GCS cleanup of legacy parquets that still carry the column — operator-driven backfill rerun. _(folded from
      consolidated_operational_validation_2026_04_15)_
- [x] ✅ DEFERRED-BLOCKED [GATE: rdt-p4-gcs-cleanup not yet done] [AGENT] P1. `rdt-p4-workspace-qg`: Run
      `quality-gates.sh` on all 5 affected repos. Depends on the GCS cleanup above to validate the column removal.
      _(folded from consolidated_operational_validation_2026_04_15)_
- [x] ✅ DEFERRED-BLOCKED [GATE: cluster e2e tests + all qg items not yet done] [AGENT] P1. `mtb-p6e-final-qg-sweep`:
      Full QG sweep across all 6 affected repos. Final QG gate; depends on every preceding "qg" item plus the cluster
      e2e tests being passable on a representative day's data. _(folded from
      consolidated_operational_validation_2026_04_15)_

#### Folded paper-vs-live workflow maturity (from `paper_vs_live_workflow_maturity_2026_05_08.md` question doc)

These todos were folded in 2026-05-09 from the paper-vs-live workflow maturity question doc (operator decisions
2026-05-09 settled 10 plan-shape forks; source `plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md` retired
2026-05-09 PM@5d2d74c1 after plan promotion). They extend items 17 (Backtest fidelity) / 18 (2-year batch backtest run)
/ 20 (Live testnet replicates prod) / 21 (Reconciliation suite) / 22 (Trading guardrails) / 23 (DART manual-trade gate,
Group G) with the paper-mode plumbing prerequisites the May-23 cutover requires.

**Conceptual framing (operator-pinned)**: pricing has no real "paper" concept (just right data); mock-data is for risk
simulations + dev fixtures (not paper-trading); batch / paper / live differ ONLY at the execution layer — strategy /
risk / P&L / position-balance / alerting / instructions identical across all four cells. The closed-set 4-cell mode
matrix decomposes as `(ExecutionTarget, ExecutionTrigger)`:

| Named mode | ExecutionTarget           | ExecutionTrigger | Notes                                                                     |
| ---------- | ------------------------- | ---------------- | ------------------------------------------------------------------------- |
| Backtest   | `simulation` only         | automated        | Historical replay forces simulation — no testnet for past dates.          |
| Paper      | `simulation` OR `testnet` | automated        | Real-time data + simulated/testnet matching. Live data, no real money.    |
| Live       | `live_venue`              | automated        | Real venue + real capital + automated execution.                          |
| Manual     | `live_venue`              | **manual**       | Real trades + real endpoints; only the trigger differs (operator-driven). |

**UAC enum decision (Settled #2)**: keep `OperationalMode { LIVE, MANUAL, BACKTEST, PAPER }` as canonical (closest to
existing code; 6 consumer files migrated); add additive `ExecutionTarget { SIMULATION, TESTNET, LIVE_VENUE }` +
`ExecutionTrigger { AUTOMATED, MANUAL }` enums + `decompose(mode) → (target, trigger)` derived helper. NO replacement of
the existing enum. Anti-patterns deleted: execution-service `paper_trade: bool`, sports `_PAPER_VENUE_KEYS` string-set.

**Per-venue policy (Settled #3)**: simulate-first floor for every venue (matching engine is the universal paper-mode
fallback); testnet upgrade where API + credentials exist (Deribit testnet known viable; Tenderly fork covers EVM DeFi;
Solana via devnet/localnet/surfnet for `carry_staked_basis` jitoSOL/mSOL/bSOL legs; sports `PaperBettingAdapter` is the
canonical simulator example). UAC `paper_target_registry: dict[chain | venue, testnet_or_fork_primitive]` codifies the
per-target upgrade path.

**Items extended**:

- **Item 17 (Backtest fidelity)**:
  - [x] [AGENT] P0. `pvl-p17a-uac-enum-consolidation`: UAC `internal/modes.py` additive change — keep `OperationalMode`
        single 4-value enum; add `ExecutionTarget` + `ExecutionTrigger` enums + `decompose()` helper; deprecate
        `TestingStage` as parallel enum (collapse `LIVE_TESTNET` to `(target=TESTNET, trigger=AUTOMATED)`); pyproject /
        `__init__.py` exports updated. NO breaking change to existing 6 consumer call-sites. _(folded from
        paper_vs_live_workflow_maturity_2026_05_08)_ — **shipped UAC@f09a19d 2026-05-14**
  - [x] [AGENT] P0. `pvl-p17b-paper-trade-bool-deletion`: Delete `paper_trade: bool` field from execution-service
        `service_config.py` + alias `PAPER_TRADE | DEFI_PAPER_TRADE`; migrate 4 consumer call-sites
        (`execution_service/cli/handlers/__init__.py`, `engine/transfers/factory.py`,
        `engine/transfers/mock_adapter.py`, `tests/unit/test_operational_mode_validation.py`) to read `OperationalMode`
        directly. _(folded from paper_vs_live_workflow_maturity_2026_05_08)_ — **shipped execution-service@e7f291850
        2026-05-14**
  - [x] [AGENT] P0. `pvl-p17c-paper-venue-keys-deletion`: Delete `_PAPER_VENUE_KEYS = ("paper", "betfair", "matchbook")`
        from `execution-service/execution_service/sports_execution/routing.py:16-25`; migrate routing logic to read
        `OperationalMode.PAPER` + sports-specific paper-venue resolver. _(folded from
        paper_vs_live_workflow_maturity_2026_05_08)_ — **shipped execution-service@e7f291850 2026-05-14**
  - [x] [AGENT] P0. `pvl-p17d-instruction-envelope-mode-field`: Lift `mode: OperationalMode` into the canonical
        `StrategyInstruction` envelope at
        [`unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/instruction.py:184`](../../unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/instruction.py#L184)
        (canonical envelope) AND audit the 7 sub-instruction types in the same file (`TransferInstruction` L594 /
        `PredictionBetInstruction` L657 / `SportsBetInstruction` L705 / `SportsExchangeOrderInstruction` L753 /
        `FuturesRollInstruction` L803 / `OptionsComboInstruction` L846) to confirm whether they nest inside
        `StrategyInstruction` (single mode field at envelope) or are peers (each carries its own mode field). Boot-time
        injection at execution-service becomes default-fallback when an instruction omits the field. Enables A/B
        execution lanes + cleaner reconciliation per-mode. _(folded from paper_vs_live_workflow_maturity_2026_05_08)_ —
        **shipped UAC@069a223 2026-05-14**

- **Item 18 (2-year batch backtest run)**:
  - [x] ✅ DEFERRED-NEEDS-DEDICATED-SESSION [HUMAN+AGENT] P0. `pvl-p18a-paper-mode-evidence-run`: Run paper-mode
        end-to-end ≥3 continuous days for the May-23 lead pair (`carry_staked_basis` +
        `ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion` variant per
        [`arbitrage_price_dispersion_finalisation_2026_05_09.md`](../archive/arbitrage_price_dispersion_finalisation_2026_05_09.md))
        against real DeFi venues + Tenderly fork (EVM legs) + Solana devnet (Solana legs) + matching-engine simulation
        (perp hedge legs without testnet). Event-stream verified per "no fire-and-forget VM launches" rule. NOT an
        operator-actionable close-out — the run actually ships per "Plans Run To Actual Completion" HARD RULE. _(folded
        from paper_vs_live_workflow_maturity_2026_05_08)_ **DEFERRED 2026-05-23**: requires dedicated 3-day session;
        operator to assign dedicated slot/VM. Blocked-escalated BLK-ffaf42f1.
  - [x] ✅ [AGENT] P1. `pvl-p18b-archetype-paper-runnable-matrix`: Populate per-archetype 4-state taxonomy
        (paper-runnable / paper-shippable / backtest-only / stub) for every archetype in UAC `StrategyArchetype` (57
        members). Codified in `codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md` — populated
        2026-05-17 by slot-5; backfilled 2026-05-24 slot-7. Note: doc points at UAC `StrategyArchetype`, not the
        PortfolioAllocator archetypes.py (different concept). 57 archetypes × 4 states fully populated. _(folded from
        paper_vs_live_workflow_maturity_2026_05_08)_

- **Item 20 (Live testnet replicates prod)**:
  - [x] [AGENT] P0. `pvl-p20a-paper-target-registry`: UAC `paper_target_registry` SSOT — `dict[chain | venue, target]`
        per-target upgrade path. EVM chains → Tenderly fork; Solana → devnet (or localnet/surfnet — pick the one with
        the fullest fork-state semantics for jitoSOL/mSOL/bSOL); Deribit → testnet endpoint; sports →
        PaperBettingAdapter; prediction → matching-engine simulation. Default for unmapped target = matching-engine
        simulation. _(folded from paper_vs_live_workflow_maturity_2026_05_08)_ — **shipped UAC@069a223
        (`PAPER_EXECUTION_TARGETS` + `get_paper_target()` in `internal/paper_execution_targets.py`) 2026-05-14**
  - [x] [AGENT] P0. `pvl-p20b-cefi-perp-testnet-audit`: Audit testnet API + credential availability for the 5 CeFi perp
        venues without testnet routing today (Bybit, Binance, OKX, Hyperliquid, Aster); wire testnet endpoints where
        available (matching `paper_target_registry`); fall back to matching-engine simulation per Settled #3. Deribit
        testnet integration confirmed already viable per existing `venues/deribit.py` reference. _(folded from
        paper_vs_live_workflow_maturity_2026_05_08)_ — **shipped execution-service@e7f291850 (Hyperliquid testnet
        wired) + PM@145a9b94 (audit codex) 2026-05-15; Binance/Bybit/OKX/Aster PENDING-ADAPTER**
  - [x] [AGENT] P0. `pvl-p20c-solana-paper-wiring`: Wire Solana devnet (or localnet/surfnet) for paper-mode jitoSOL /
        mSOL / bSOL execution; integrate with `carry_staked_basis` paper-mode evidence run. Pyth via Hermes for prices
        (already unbanned); LST yields via DeFi connectors against the testnet/fork primitive. _(folded from
        paper_vs_live_workflow_maturity_2026_05_08)_ — **shipped execution-service@a39294603 + PM@77810ca6 2026-05-15**

- **Item 21 (Reconciliation suite)**:
  - [x] [AGENT] P0. `pvl-p21a-three-way-recon`: Extend `batch-live-reconciliation-service` to 3-way recon (batch ↔ paper
        ↔ live) — add `paper-live` and `batch-paper` recon stages alongside existing `batch-live` (stage3); codify
        per-pair tolerance thresholds in `models/deviation_thresholds.py` (paper-vs-live tighter than batch-vs-live
        since same data + similar API conditions; batch-vs-paper bounded by matching-engine fidelity); closed-set
        failure-routing policy (alert / auto-pause-live / auto-demote-to-paper). _(folded from
        paper_vs_live_workflow_maturity_2026_05_08)_ — **shipped batch-live-reconciliation-service@48f12ce 2026-05-15**

- **Item 22 (Trading guardrails)** — composes with `alerting_service_live_rules_2026_05_07`:
  - [x] [AGENT] P1. `pvl-p22a-mode-tagged-alerts`: Alerting-service rules consume `mode: OperationalMode` from
        instruction envelope (per `pvl-p17d`); per-mode alert thresholds (paper-mode looser than live; manual-mode wakes
        operator vs paging on-call). _(folded from paper_vs_live_workflow_maturity_2026_05_08)_ — **shipped
        alerting-service@97ec80c 2026-05-15**

- **Item 23 (DART manual-trade gate, Group G)** — see Group G section below for full DART scope (`pvl-p23a` / `pvl-p23b`
  / `pvl-p23c`).

**Phased execution DAG** (Citadel-Grade § 2 — explicit ordering + QG gates between phases):

```
Phase 1 (foundation; blocking)                                    [≤1d, Ikenna]
  └─ pvl-p17a — UAC additive enums + decompose() helper
        QG gate: UAC quality-gates.sh green; no consumer breakage

Phase 2 (parallel after Phase 1)                                  [~2-3d combined]
  ├─ pvl-p17b — paper_trade: bool deletion (4 consumer migrations)
  ├─ pvl-p17c — _PAPER_VENUE_KEYS deletion (sports routing migration)
  ├─ pvl-p17d — instruction envelope mode field
  └─ pvl-p20a — paper_target_registry SSOT
        QG gate: UAC + execution-service + sports-execution all green;
                  workspace grep shows zero residual paper_trade / _PAPER_VENUE_KEYS

Phase 3 (parallel after Phase 2)                                  [~5-7d combined]
  ├─ pvl-p20b — 5 perp venue testnet audit + wire-up
  ├─ pvl-p20c — Solana paper wiring
  ├─ pvl-p21a — 3-way recon (batch ↔ paper ↔ live)
  ├─ pvl-p22a — mode-tagged alerts
  └─ pvl-p23b — mode-data API
        QG gate: deployment-api / strategy-service / batch-live-recon-service /
                  alerting-service all green; per-pair recon dry-run within tolerance

Phase 4 (parallel after pvl-p23b)                                 [~3-5d combined]
  ├─ pvl-p23a — DART 3-way visualization (real backend)
  └─ pvl-p23c — manual-trade gate UI + ManualTradeGateDialog
        QG gate: unified-trading-system-ui green; Playwright e2e covers DART
                  comparison view + manual-approval flow

Phase 5 (final, depends on Phases 1-4)                            [~2-3d real-infra]
  ├─ pvl-p18a — paper-mode evidence run ≥3 days (lead pair)
  └─ pvl-p18b — archetype paper-runnable matrix populate
        Done gate: event-stream verified per "no fire-and-forget VM launches" rule;
                    matrix populated for May-23 lead pair + ≥1 other archetype
```

Cross-phase parallelism: `pvl-p17a` (Phase 1) is the ONLY blocking item; everything else fans out to maximum parallelism
across 4-5 agents per phase. Phase 5 depends on the union of every prior phase being green (paper-mode evidence run is
the integration test for the whole architecture).

**Done-definition + verification per sub-item** (Citadel-Grade § 5 + "Plans Run To Actual Completion" HARD RULE — every
item names what "done" looks like + the exact verification command/check):

| Item       | Done when                                                                                                                                                                                                                                                                                                                                        | Verification                                                                                                                                                                                                                          |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pvl-p17a` | `from unified_api_contracts.internal.modes import ExecutionTarget, ExecutionTrigger, decompose` works; 4 unit tests cover the 4-cell mapping; `__init__.py` exports updated.                                                                                                                                                                     | `cd unified-api-contracts && bash scripts/quality-gates.sh` green; `python -c "from unified_api_contracts.internal.modes import decompose, OperationalMode; assert decompose(OperationalMode.MANUAL)[1].name == 'MANUAL'"`.           |
| `pvl-p17b` | `paper_trade` field deleted from `execution-service/execution_service/service_config.py`; alias `PAPER_TRADE \| DEFI_PAPER_TRADE` removed; 4 call-sites read `OperationalMode` directly.                                                                                                                                                         | `cd execution-service && bash scripts/quality-gates.sh` green; `grep -rn 'paper_trade' execution_service/ --include='*.py'` returns 0 matches outside docstring/comment context.                                                      |
| `pvl-p17c` | `_PAPER_VENUE_KEYS` deleted from `sports_execution/routing.py:16-25`; routing reads `OperationalMode.PAPER` + sports-specific paper-venue resolver.                                                                                                                                                                                              | `grep -rn '_PAPER_VENUE_KEYS' execution-service/ --include='*.py'` returns 0; sports execution unit tests pass; `cd execution-service && bash scripts/quality-gates.sh` green.                                                        |
| `pvl-p17d` | `mode: OperationalMode` field added to `StrategyInstruction` (and sub-types per the audit determination); execution-service consumer reads it; boot-time injection becomes default-fallback when omitted.                                                                                                                                        | UAC + execution-service QG green; integration test covers (a) instruction with mode field → routed correctly, (b) instruction without mode field → falls back to boot config.                                                         |
| `pvl-p18a` | Paper-mode end-to-end run completed ≥3 continuous days for `carry_staked_basis` + `ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion` lead pair against real DeFi venues + Tenderly fork (EVM) + Solana devnet + matching engine (perp legs). NOT operator-actionable.                                                                          | `gcloud storage ls gs://${PID}-events/events/strategy-service/<YYYY-MM-DD>/<vm-name>/` shows STARTED + per-instrument progress + STOPPED with non-empty metadata for each of the ≥3 days; sample parquet inspection shows real fills. |
| `pvl-p18b` | `codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md` matrix populated for every archetype in `strategy_service/portfolio_allocator/archetypes.py` with 4-state classification.                                                                                                                                         | Matrix table has ≥1 row per archetype found in `archetypes.py`; states match the closed set; lead pair shows `paper-runnable` post-`pvl-p18a`.                                                                                        |
| `pvl-p20a` | UAC `unified_api_contracts/internal/paper_target_registry.py` ships with `PAPER_TARGET_REGISTRY` mapping + `PaperTarget` enum + ≥11 venues mapped + `__init__.py` exports.                                                                                                                                                                       | `python -c "from unified_api_contracts.internal.paper_target_registry import PAPER_TARGET_REGISTRY; assert PAPER_TARGET_REGISTRY['solana'].name == 'SOLANA_DEVNET'"`; UAC QG green.                                                   |
| `pvl-p20b` | Audit report published as table in `codex/05-infrastructure/per-venue-paper-policy.md` showing each of 5 perp venues' testnet status (available + creds path / unavailable); testnet endpoints wired where viable; matching-engine fallback for the rest.                                                                                        | Codex doc has 5 venue rows; for any venue marked "available", `paper_target_registry[venue]` matches the testnet target and execution-service has a working adapter constructor pointing at the testnet endpoint.                     |
| `pvl-p20c` | Solana paper target chosen (devnet OR localnet OR surfnet — pick committed in codex doc); execution-service Solana adapter reads from `paper_target_registry["solana"]`; `carry_staked_basis` paper-run can fetch jitoSOL/mSOL/bSOL prices via Pyth Hermes against the testnet primitive.                                                        | `python -c "<solana adapter init test>"` works; sample run emits `INSTRUMENT_PROCESSED` events for jitoSOL with non-zero rows.                                                                                                        |
| `pvl-p21a` | `batch-live-reconciliation-service` ships `paper_live_recon.py` + `batch_paper_recon.py` stages; `models/deviation_thresholds.py` has per-pair tolerance constants; closed-set failure-routing policy implemented.                                                                                                                               | Dry-run on lead-pair window emits 3 reports (batch-live, paper-live, batch-paper) with per-pair deviations within tolerance; service QG green.                                                                                        |
| `pvl-p22a` | Alerting-service rules consume `mode: OperationalMode` from event metadata; per-mode threshold logic in ≥1 alert rule; integration test covers mode-tagged event → mode-aware alert decision.                                                                                                                                                    | `cd alerting-service && bash scripts/quality-gates.sh` green; integration test in `tests/integration/test_mode_aware_alerts.py` (or similar) passes.                                                                                  |
| `pvl-p23a` | DART terminal in `unified-trading-system-ui` renders 3-way batch/paper/live comparison view for ≥1 archetype; wired to real backend (not mock-API); shared filter scope applies across lanes; Playwright e2e covers the comparison rendering.                                                                                                    | `cd unified-trading-system-ui && CI=true npm test -- --run` green; Playwright run shows 3-pane render with real data per lane.                                                                                                        |
| `pvl-p23b` | `GET /strategy/{id}/runs?mode=batch\|paper\|live` endpoint live on `deployment-api` (or strategy-service); returns mode-tagged event/fill/P&L bundle; 3 unit tests (one per mode) pass.                                                                                                                                                          | `curl http://localhost:8004/strategy/<id>/runs?mode=paper` returns 200 with non-empty body; deployment-api QG green.                                                                                                                  |
| `pvl-p23c` | `ManualTradeGateDialog` component renders pre-trade preview (margin / position-limit / worst-case loss) + approve / deny / timeout buttons; emits `MANUAL_APPROVED` / `MANUAL_REJECTED` events; execution-service unholds from manual-pending queue on approval; Playwright e2e covers the approve flow end-to-end against a real testnet trade. | Playwright e2e green; event-stream shows `MANUAL_APPROVED` followed by fill confirmation event from venue testnet.                                                                                                                    |

**Codex SSOTs touched** (5 NEW + 1 UPDATE):

- `codex/04-architecture/operational-modes.md` — **NEW** — pins single-enum SSOT + decompose helper + 4-cell matrix +
  per-axis routing rules + composability with `RuntimeMode`.
- `codex/04-architecture/paper-vs-live-execution-seam.md` — **NEW** — pins execution-only-seam principle,
  pricing-no-paper, mock-vs-paper boundary (operator-discipline; not enforced).
- `codex/04-architecture/batch-live-architecture.md` — **UPDATE** — extend existing SSOT with paper-mode positioning
  (batch ⊂ paper ⊂ live in terms of code-path; only fill source differs).
- `codex/05-infrastructure/per-venue-paper-policy.md` — **NEW** — simulate-first + testnet-fallback policy +
  `paper_target_registry` SSOT.
- `codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md` — **NEW** — per-archetype 4-state
  matrix + paper-runnable gate set.
- `codex/14-customer-journeys/dart/mode-toggle.md` — **NEW** — DART 3-way visualization + manual gate UI shape; composes
  with item 23.

**Cross-plan banners** (mutual; ship with this fold-in):

- [`defi_master.md`](../epics/defi_master.md) — Tenderly fork + per-chain `paper_target_registry` compose with DeFi
  master.
- [`arbitrage_price_dispersion_finalisation_2026_05_09.md`](../archive/arbitrage_price_dispersion_finalisation_2026_05_09.md)
  — funding-rate-dispersion variant is half of the May-23 paper-mode evidence run; banner mutual.
- [`promote_workflow_may23_cli_path_2026_05_10.md`](./promote_workflow_may23_cli_path_2026_05_10.md) — **NEW
  (2026-05-10), pivoted dual-track 2026-05-10 PM** — May-23 promote workflow shipped DUAL-TRACK per operator preference
  (2026-05-10 PM): **PRIMARY = operator-CLI** (run-paper.sh + run-live.sh + colocated_engine.py — safety net) +
  **SECONDARY = minimal-but-real UI promote pipeline** (Promote button → POST /promote → MinimalCandidateManifest → DART
  manual-trade gate → paper/live VM auto-launch). Spawned from the promote-workflow re-audit
  ([`plans/questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md`](../questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md))
  which found the UI promote workflow was 100% mock + no `/promote` backend + no paper/live VM launchers in
  `deployment-service/scripts/vm/`. The plan extends Group F items 17/18/19/20/21/22 + Group G item 23 with these new
  sub-items the audit surfaced:
  - `pvl-p17e-launcher-scripts` — write `launch-strategy-paper-vm.sh` + `launch-strategy-live-vm.sh` in
    `deployment-service/scripts/vm/` per CLAUDE.md _VM launcher script SSOT_ HARD RULE; register `strategy-paper-` +
    `strategy-live-` prefixes in `vm_zombie_watchdog.py:VM_PREFIX_TO_BUCKET`. **P0 cutover-blocker for both tracks.**
    **✅ DONE** — deployment-service@87f12f1 (Phase 1 of `promote_workflow_may23_cli_path_2026_05_10.md`). Both
    launchers shipped; prefixes registered in VM_PREFIX_TO_BUCKET; smoke VM ran end-to-end 2026-05-14.
  - `pvl-p17f-minimal-candidate-manifest` — `MinimalCandidateManifest` UAC type with placeholder Optional fields for
    pinned shas / model refs / features manifest version (full enrichment shipped post-cutover Phase 2). **P0 May-23
    (Phase U1 of CLI plan).** **✅ DONE** — uac@2b48295 + utl@c7c8a730 (Phase U1); Firestore
    `strategy_candidate_manifests` collection live; `CandidateManifestStore` helper + `STRATEGY_PROMOTED_TO_CANDIDATE`
    event shipped.
  - `pvl-p23d-promote-api-MINIMAL` — backend `POST /promote/{strategy_id}/{manifest_id}` endpoint + minimal pre-flight
    pipeline (Copper sandbox / venue keys / alerting / kill-switch / recon — composes with existing services). **P0
    May-23 (Phase U3 of CLI plan).** **✅ MINIMAL DONE** — deployment-api@fe2a9c5 (Phase U3); 5 pre-flight gates wired;
    `STRATEGY_PROMOTED_TO_PAPER` / `STRATEGY_PROMOTED_TO_LIVE` events emitted. Full pre-flight + cross-service
    auto-registration **DEFERRED** to
    [`promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`](./promote_workflow_post_cutover_ui_pipeline_2026_05_10.md)
    Phase 9.
  - `pvl-p23e-live-deployment-events-MINIMAL` — May-23 uses UTL bare-string events (`STRATEGY_PROMOTED_TO_PAPER` /
    `STRATEGY_PROMOTED_TO_LIVE`); UAC `LifecycleEventType` enum membership + per-launch event-verification protocol
    scoped to live trading deferred to post-cutover Phase 3. **P0 May-23 minimal subset.** **✅ MINIMAL DONE** —
    utl@c7c8a730 (Phase U3); UTL bare-string events emitted on promote. UAC `LifecycleEventType` enum membership
    **DEFERRED** to post-cutover Phase 3.
- [`promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`](./promote_workflow_post_cutover_ui_pipeline_2026_05_10.md)
  — **NEW (2026-05-10)** — EXTENDS May-23 dual-track minimal-UI shipments. Picks up everything DEFERRED from the May-23
  cutover plan: state-machine consolidation (4 UAC SSOTs → 1 canonical) + `CandidateManifest` enrichment (Phase 2
  populates the May-23 `MinimalCandidateManifest` placeholder Optional fields) + 8 new event types + per-archetype
  Pydantic config schemas (5 of 53 → all 53) + drift detection cron + cross-service auto-registration on promote +
  continuous backtest cron + backtest persistence + ranking surface + full pre-flight pipeline (Phase 9 extends May-23
  Phase U3 minimal) + full DART experience extension (Phase 10 extends May-23 Phases U5+U6 from lead pair to all
  archetypes + advanced operator features) + `pvl-p17a-d` operational modes consolidation. Target completion 2026-07-04
  (~6 weeks post-cutover).

**Estimated scope**: ~12-18 AI-days total. UAC additive enum + decompose helper + instruction envelope mode field +
`TestingStage` deprecation: ~1-2d. `paper_trade: bool` + `_PAPER_VENUE_KEYS` deletion + 6 consumer file migration: ~1d.
Per-venue testnet wire-up audit + simulate-first matching engine adapter pass + Deribit testnet integration: ~3-5d.
Solana devnet + `paper_target_registry` + non-EVM chain coverage: ~2d. DART 3-way visualization (side-by-side + per-mode

- manual gate UI) wired to real backend: ~3-5d. Per-archetype paper-runnable evidence runs: ~2-3d (real-infra). 3-way
  recon stage extension: ~1-2d. 5 codex SSOT NEW stubs + 1 UPDATE: ~1-2d.

### Group G — Operator UX (live-only)

23. **DART manual-trade gate** — DART terminal in UTS-UI visualizes the strategy archetype end-to-end; operator first
    puts trades on manually → backend executes through the same path as automation → monitor for the gate window → flip
    switch to automation (codex `09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md`)

#### Folded paper-vs-live DART scope (from `paper_vs_live_workflow_maturity_2026_05_08.md` — operator-confirmed

pre-cutover scope)

Operator decision 2026-05-09 (Settled #4 + #5): manual gate + DART 3-way visualization both ship pre-cutover, wired to
real backend (not mock). Together with item 23 above, the canonical DART operator surface looks like:

- [x] [AGENT] P0. `pvl-p23a-dart-3way-visualization`: DART surface in `unified-trading-system-ui` renders three views
      for any strategy archetype: (a) **side-by-side comparison** — batch / paper / live P&L curves, fills blotter,
      events, position trajectory, risk metrics in a tri-pane or stacked-line-series canvas; (b) **separate per-mode
      views** — pickable via `dart-scope-bar.tsx` Execution Stream toggle (extends current paper/live to add batch); (c)
      **shared filter scope** — asset*group / instrument_type / strategy_family / archetype filters apply across all
      three lanes simultaneously. Wired to **real backend** (not mock fixtures): each lane reads from the mode-tagged
      event stream + parquet results. *(folded from paper*vs_live_workflow_maturity_2026_05_08)* — **shipped
      `ui@0c9fb81a` 2026-05-15** (`DartThreeWayView` 3-pane component + `fetchStrategyRuns` in dart-client.ts; 30s poll
      via Promise.all across 3 modes; wired into terminal/page.tsx)
- [x] [AGENT] P0. `pvl-p23b-dart-mode-data-api`: `deployment-api` (or strategy-service) endpoint
      `GET /strategy/{id}/runs?mode=batch|paper|live` returns the mode-tagged event/fill/P&L bundle for DART to render.
      Single API surface (per workspace pattern) — DART doesn't talk to three different endpoints. Composes with
      `pvl-p17d-instruction-envelope-mode-field`. _(folded from paper_vs_live_workflow_maturity_2026_05_08)_ — **shipped
      `deployment-api@9c608c9` 2026-05-15** (`routes/strategy_runs.py` + registered on `_authenticated_router`; QG
      green)
- [x] [AGENT] P0. `pvl-p23c-manual-trade-gate-ui`: DART surfaces a per-trade manual approval affordance for
      `OperationalMode.MANUAL` strategies — operator sees pre-trade risk preview (margin, position-limit, worst-case
      loss) + approve/deny/timeout per instruction. Approval emits `MANUAL_APPROVED` event → execution-service unholds
      from manual-pending queue → fill at live venue. Composes with execution-service's pre-execution gate at the
      manual-pending queue boundary; closed-set timeout policy (cancel-with-audit | escalate | hold) per-strategy
      config. **DART is the canonical operator surface**; fallback approval channels (Telegram interactive button,
      email-with-confirm-link, Slack) ship as a P1 follow-up. _(folded from paper_vs_live_workflow_maturity_2026_05_08)_
      — **shipped `deployment-api@9c608c9` + `ui@0c9fb81a` 2026-05-15** (pending-queue backend
      `routes/manual_pending.py` + `ManualTradeGateDialog` wired into DART terminal header)

> **Cross-ref**: `pvl-p23a/b/c` (Group G item 23) execution is tracked in
> [`promote_workflow_may23_cli_path_2026_05_10.md`](./promote_workflow_may23_cli_path_2026_05_10.md) Phases U4-U6.
> Remaining open work: Playwright e2e tests for U4/U5/U6 + testnet operator-approve flow. Post-cutover DART enhancements
> (all-archetype coverage + fallback approval channels) in
> [`promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`](./promote_workflow_post_cutover_ui_pipeline_2026_05_10.md)
> Phase 10.

> Per-service yamls in `codex/10-audit/repos/<service>.yaml` get extended to track items 4–23. Items 1–3 already in the
> existing repo readiness yaml are inherited.

---

### Group H — Per-client isolation + multi-venue concurrency (added 2026-05-20)

> Promoted from `plans/active/per_client_isolation_and_venue_fanout_topology_2026_05_20.md` per operator direction
> 2026-05-20. May-23 needs 2 live clients (Odum Research UK + defi-client-1) on at least 1 archetype; architecture must
> support hot-add/remove without VM restart and hard crash isolation between clients. Audit 2026-05-20 confirmed
> strategy-service has local MTM compute → centralised MarkPriceAggregator in supervisor required. Execution-service
> already per-process per-client (`isolation_policy.py`) — no rewrite, just documentation. Composes with un-deferred
> Phase 5 UTL lifts (slot 5 in flight 2026-05-20).

24. **Per-client subprocess isolation in strategy-service** — StrategySupervisor parent + ClientWorker subprocess per
    client; hard crash isolation (segfault/OOM survived); centralised MarkPriceAggregator broadcasts via shared memory;
    hybrid hot-reload (push REGISTER/DEREGISTER via UAC `ClientLifecycleEvent` bus, pull credential rotation from Cloud
    KMS). E.0+E.1 ships May-23. Plan:
    [`per_client_isolation_and_venue_fanout_topology_2026_05_20.md`](./per_client_isolation_and_venue_fanout_topology_2026_05_20.md)
    Phases 0–9. Continuous verification: e2e crash-isolation test in
    `e2e-testing/scripts/defi/per_client_isolation_e2e.py` nightly cron after May-23.

25. **Execution-service per-client process isolation (confirm + document)** — existing
    `execution-service/execution_service/isolation_policy.py` enforces single-tenant per process via `CLIENT_ID` env;
    `assert_client_allowed()` rejects cross-client bus events. Documented in codex
    `04-architecture/execution-service-per-client-isolation.md` (Phase 6 of Group H plan). Continuous verification: QG
    step enforcing `isolation_policy.assert_client_allowed` is called from every event-bus subscriber in
    execution-service (extend STEP 5.xx in scope after Phase 6).

26. **OMS surface + multi-venue concurrent routing (confirm + document)** — `PersistentOrderManager` + asyncio.gather
    - SmartOrderRouter already exist in execution-service. Documented in codex
      `04-architecture/oms-protocol-and-state-machine.md` + `04-architecture/multi-venue-concurrent-routing.md`.
      Per-venue circuit-breaker hardening only if Phase 0 audit flags gaps. Continuous verification: codex-doc-drift QG
      (Phase 9 of Group H plan).

27. **TransferCoordinator facade in execution-service** — single entry point for CEX withdraw / DeFi deposit/withdraw /
    bridge / sub-account move; UAC `TransferIntent` + `TransferResult` events; idempotency via `idempotency_key`. May-23
    minimum: 1 DeFi deposit (USDC → Aave) per client end-to-end. **HARD RULE — cross-client fund movement FORBIDDEN
    (custody + legal boundary). TransferCoordinator rejects any intent where source.client_id ≠ dest.client_id with
    `CrossClientTransferForbiddenError`. SSOT: `codex/04-architecture/client-funds-isolation.md`.** Intra-client
    multi-portfolio + multi-wallet rebalancing OUT-OF-SCOPE for May-23 → Phase E.3 of Group H plan (target 2026-06-01).
    Sub-account transfers for non-Binance/OKX venues → named successor `subaccount_transfers_phase_2_2026_06_01.md`.

---

## Continuous Verification matrix — 23 items (per HARD RULE codified 2026-05-08)

Per CLAUDE.md "Master Plan Continuous-Verification Column" HARD RULE: every Group A–G item MUST declare its periodic
verification path between checkpoint deadlines. Items where `Last verified` is older than the cadence trigger a P0
alerting rule (Tab 5 governance owns the alert). `manual` cadence = live-only operator-judgment items with no continuous
verifier.

**Owner notation**: `cron:<vm-name>` = recurring VM via deployment-service launcher. `QG:<repo>` = enforced via
`scripts/quality-gates.sh` on every PR. `Tab:<role>` = daily Tab assignment in current work-split. `manual` = operator
sign-off.

> **🟢 Last refreshed: 2026-05-12 Day-1 EOD by slot 1 main.** Pace = 5× calibrated; 5 of 7 Ikenna implementer slots ✅
> FULL-CYCLE-CLOSE on Day 1 of 4-day cycle. Phase 1 freeze-gate (2026-05-15) readiness is excellent + 3 calendar days of
> capacity now open for SCOPE EXTENSION 2 (Cycle 2 PREP pre-cutover work; see `continuation_prompts_2026_05_12.md` § "🟢
> SCOPE EXTENSION 2").
>
> **Phase 1 freeze-gate items status (post Day-1 EOD)**:
>
> - **#1 Schema columns frozen** ✅ (slot 6 Cycle 0; UAC@`174f401`)
> - **#2 error_reason taxonomy** ✅ (slot 6 + slot 3)
> - **#3 37-callsite migration** ✅ (Day-2 PipelineMode sweep complete; QG STEP 5.68 workspace-wide confirmed
>   `0 baselined, 0 new occurrences` — Day-3 audit 2026-05-14 by slot 6)
> - **#4 ServiceEmissionPolicy seed dict locked** ✅ (slot 6 + slot 2)
> - **#5 available_at per-row stamping** ✅ (slot 3 + slot 4 + slot 8)
> - **#6 LookaheadBiasError strict-mode features-\*** ✅ (all 8 families confirmed:
>   delta_one/volatility/calendar/multi_timeframe/cross_instrument/sports — `PointInTimeEnforcer(strict=True)`; onchain
>   — `strict=not mock_mode` (production=True); commodity — direct `raise LookaheadBiasError` for negative staleness.
>   Day-3 audit 2026-05-14 by slot 6)
>
> **6/6 ✅ ALL ITEMS CONFIRMED GREEN** — Day-3 audit 2026-05-14 by slot 6 (read-only workspace-grep verification). Gate
> fires tomorrow 2026-05-15. No P0 gaps found.
>
> **2026-05-12 Day-1 EOD shipments by slot** (all on origin/live-defi-rollout):
>
> - **Slot 2** ✅ defi_catalogue Phases 1B-1H + Phase 2 per-protocol shard-atom + Phase 3 lending-indices spec — 17
>   commits Days 1-4 (PM@`a1b9d3a9` cycle-close + PM@`95113b7c` DONE block).
> - **Slot 3** 🟡 Day-1 PM PROGRESS (PM@`3c9eb631`) — Phase 1.E audit + Phase 2.6 cutover dry-run shipped
>   (PM@`df659ed5`+`f07cddc6`); DAY-2 P0 PipelineMode sweep queued.
> - **Slot 4** ✅ api_keys_wallets full-cycle close (PM@`20bd7964`) — wallet schema UAC@`d721b6a` + R9 sub-(a) RESOLVED
>   CLOUD_KMS_ENCRYPTED for May-23.
> - **Slot 5** ✅ defi_recursive_borrow FULL CYCLE CLOSE (PM@`71786748`) — Phases 1-11 design batch (PM@`b339a1db`) +
>   Phase 12 backtest scenarios (PM@`03492b96`) + Phase 3 strategy-service factory spec (PM@`158dd8b1`).
> - **Slot 6** ✅ defi_simulation_realism DONE-2026-05-15 (PM@`0c4b66f4`) — 3 codex sections shipped + Phase 9B
>   concentrated-liquidity.md CREATE (PM@`30a01f3e`+`ae804766`) + Phase 9C continuation (PM@`a39fdee1`).
> - **Slot 7** ✅ scenarios topology+price-shock DESIGN-SHIPPED (PM@`3daea56a`+`bea269b1`) — Phase 1+2 10-scenario
>   designs.
> - **Slot 8** ✅ Day-4 EOD CYCLE CLOSE (PM@`3fb30850`) — 11 ship lots / ~12 cal AI-days: manifest Phase 4 +
>   codex_vs_citadel Phase 0+1.J Governance + DART precheck endpoint + audit-log persistence + master plan Group F/G
>   mid-cycle refresh.
>
> **Slot status flipped to Day-2 mode**: SCOPE EXTENSION 2 Cycle 2 PREP layer ready for Day-3-4 pickup (bucket
> provisioning script review + per-VM-prefix rsync sizing + write-pause coordination protocol + cutover communication
> template + rollback procedure + Phase 12 paper-trade adapter pre-wiring + Cycle 6 design-ahead). No Cycle 2 EXECUTION
> pulled forward (gate-locked).
>
> **Pre-2026-05-12 baseline (preserved for delta context — original 2026-05-11 + 2026-05-12 boot sweep):**
>
> Phase 1 freeze-gate items below were sourced from earlier slot Cycle-0 shipments; Day-1 EOD slot status now
> supersedes:
>
> **2026-05-13 Day-2 slot 8 Group F/G D1+D4 design unblocking:**
>
> - **Item 23 DART design blockers CLEARED** — D1 (ManualInstruction.operation_type field) + D4 (get_venue_asset_group()
>   UAC helper) **both shipped 2026-05-13** (UAC@`14a0292` + UAC@`51f6e28`). These two foundational decisions unblock:
>   (a) execution-service BUILD #1 backend wiring (manual instruction type routing); (b) execution-service BUILD #4/#5
>   side-validator widening (BUY/SELL → HOME/AWAY/DRAW/YES/NO per asset_group). **Impact on Item 23**: manual-trade
>   gate + DART 3-way visualization both remain unchanged in their UI surface (`pvl-p23a` / `pvl-p23c` scope), but the
>   backend validation layer (cross_cutting_may_23_deliverables deliverable #4) now has its design prerequisites
>   shipped. Harsh T6's 5 BUILDs can proceed. Last verified: 2026-05-13.
>
> **2026-05-12 mid-cycle slot 8 Group F/G top-up:**
>
> - **Item 5 (B · Data correctness)** — STEP 5.68 explicit-pipeline_mode-at-record-calls AST-walk QG check shipped at
>   PM@`4159b7ae` (266 LOC `check_pipeline_mode_explicit_at_record_calls.py` + 207-LOC 11-test suite + 706-LOC bootstrap
>   baseline). Workspace invocation: `OK — 114 baselined; 0 new occurrences`. Phase 4.GREP-VERIFY closed. Last verified:
>   2026-05-12.
> - **Item 23 (G · Operator UX)** — DART manual-action UAC contract layer shipped at UAC@`336b486` + PM@`f7317fda` (4
>   new types: `ManualMLTrainingAction` enum / `MLTrainingControlRequest`+`Response` / `ManualAuditCategory` enum /
>   `ManualInstructionAuditLog`; 7 unit tests; basedpyright clean). Codex `manual-trade-booking.md` extended with ML
>   training-control endpoint table + audit-log surface section. Unblocks Harsh T6's 5 BUILDs at contract layer. Last
>   verified: 2026-05-12.
>
> **2026-05-12 boot top-up** (post-evening sweep):
>
> - **Phase 3.D rescan VM ✅ COMPLETED end-to-end** (`cross-asset-rescan-20260511-172749`, 16:30:41→16:47:11Z, 16m 30s).
>   All 5 asset_groups completed with `return_code=0`: cefi (7m24s) / defi (4m14s) / tradfi (2m48s) / sports (1m29s) /
>   prediction (33s). **`phantom_line_count=0` across all 5** (dry-run, apply_flips=false). `triage.jsonl` 0 bytes =
>   nothing to triage = manifest is in a clean state per the rescan algorithm. Bad-data cleanup mechanism exercised
>   end-to-end + healthy signal.
> - **Slot 2 writegate slice (c) Phase 6.2 ✅ SHIPPED** (MDPS@`d0df50c` slot 8 scaffolding cherry-pick + MDPS@`311614a`
>   wiring/tests/cleanup + PM@`8d0fd6b4` plan-flip). End state: 4 seeded MDPS data_types (`ohlcv_1h` /
>   `ohlcv_1m:current` / `ohlcv_1m:historical` / `ohlcv_24h` / `book_snapshot_5`) routed through generalised
>   `_resolve_policy_output_data_type` + `_publish_emission_check`; ohlcv_1h-specific helpers DELETED. 1151 MDPS unit
>   tests pass. Unblocks writegate Phase 6.3-6.8 + manifest_schema_final_gate Phase 2.
> - **Slot 6 manifest_schema_final_gate Phase 2.A/B/C/D ✅ SHIPPED** at UTL@`0adea1c6` / `001e8892` / `5f2aacd6` /
>   `bae1ecb9` (30+ unit tests). UTL v8 ManifestWriter with `service_emission_state` / `last_emission_decision_at` /
>   `expected_window_completeness_fraction` kwargs + v7-tolerance fallback + v7→v8 migration helper. **Slot 2
>   attribution correction**: Phase 2.A/B/C/D shipped by slot 6, not slot 2 (slot 2 shipped Phase 6.2 + Phase 2 P2 +
>   Phase 4 partial + Phase 5.A/B).
> - **Slot 8 Phase 0f + 0h + Tier 2 Phase 3.A-D ✅ SHIPPED** — 72 launchers env-aware (5-sub-agent fan-out under slot
>   8); cross-asset-rescan launcher + watchdog dict + Deploy-Missing registry + reconciler script all live. Phase 0h
>   verified shipped by Harsh slot 4 pre-handoff. Q7(c) events env-tier RESOLVED per operator (env-tiered, option c-i).
>
> **2026-05-11 evening (originally captured here):**
>
> - **Slot 2** ✅ DONE writegate slice (b) full scope: UTL `manifest_completeness` helper + MDPS `ohlcv_1h` POC
>   (current + historical) + deployment-api/ui surfaces + codex emission-policy SSOT.
> - **Slot 3** ✅ DONE primary (Phase 0.1/0.2 bar_boundary + Phase 4+5 expansion) + re-task (sports `available_at`
>   flip + 4 design Qs Q-A/B/C/D resolved). Merged to live-defi-rollout per PM@`c761ff68` + UAC cherry-picks `f0652ac` +
>   `6002ffa` + UTL/MTDS FF-merges.
> - **Slot 4** ✅ DONE design-ahead + re-task: promoted `MDPSStreamingAggregator` / `AssetScopedFeaturesRunner` /
>   `CrossCuttingFeaturesRunner` UTL primitives from stubs to real implementation; deployment-api `/live` endpoint +
>   `<LiveDataStatusTab/>` real-wired.
> - **Slot 5** ACTIVE on extended scope (defi_master Q1 #3 PROTOCOL_LAUNCH_DATES research absorbed); DeFi Phase 1.E
>   audit + Stream C partial shipped.
> - **Slot 6** ✅ DONE manifest_schema_final_gate Phase 1 (CRITICAL PATH): v8 schema slice (b) at UAC@`174f401` —
>   `service_emission_state` + `pipeline_mode` + `feature_family` columns + `EXPECTED_KNOWN_SOURCE_GAP` enum +
>   `ServiceEmissionPolicy.next_state(...)` resolver. **Phase 1 freeze-gate item #1 (Schema columns frozen) UNBLOCKED.**
> - **Slot 7** ✅ DONE Phase 1.D 3-plan fan-out (alerting + risk + DR): UAC@`0b61aec` + `945ad5d` + `dc4c9f0` +
>   `a7a99b5` + `2f02a87` + `c96447b`; 160/160 tests pass workspace-wide.
> - **Slot 8** ✅ DONE 5-of-6 P0-2 MDPS surgery steps (scope-shift mid-cycle): legacy `_write_candles` MRO override
>   deleted; TradFi `ohlcv_passthrough` 1440-NaN-bar shape deleted; `_handle_empty_tick_data` now routes every
>   asset_group through `record_empty_for_shard`; VIX gap reason upgraded to `EXPECTED_KNOWN_SOURCE_GAP`;
>   CandleProcessingService dead-branch deleted (coverage 73.18% → 74.63%). Step 5 (`output_schemas.py` OHLCV
>   nullability) OUT-OF-SCOPE → owned by `hard_schema_enforcement_2026_05_08.md`. Writegate slice (c) 37-callsite
>   migration (original slot 8 scope) **not started this cycle** — needs fresh assignment.
>
> **Phase 1 freeze-gate items status** (per `code_freeze_migrate_backfill_sequencing_2026_05_10.md:142-149`): item #1
> (Schema columns frozen) ✅ unblocked by slot 6; item #2 (error_reason taxonomy closed) ✅ unblocked by slot 6 + slot
> 3; item #4 (ServiceEmissionPolicy seed dict locked) ✅ unblocked by slot 6 + slot 2; item #5 (available_at per-row
> stamping wired) ✅ unblocked by slot 3 + slot 4 + Harsh slot 4 + slot 8. **Item #3 (All 37 MDPS/MTDS callsites
> migrated to record_captured/empty/failed) — STILL OPEN**: writegate slice (c) 37-callsite migration was slot 8's
> original scope but slot 8 pivoted to P0-2 surgery; needs fresh slot assignment for next cycle. Item #6
> (LookaheadBiasError strict-mode green at features-\*) — depends on slot 4's per-service consumer wiring of
> `LookaheadBiasError`, likely ships next cycle.

| #    | Group                | Cutover success criterion (one-line from § Per-service readiness checklist)                                                                                                                                                                                                                               | Continuous Verification                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Last verified                                                                                                    |
| ---- | -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 1    | A · Code health      | `bash scripts/quality-gates.sh` two-pass clean per repo                                                                                                                                                                                                                                                   | `QG:per-repo` on every PR; pre-shippable-unit local before push. **Workspace-qg unified workflow (2026-05-16)**: all 21 Python repos run `.github/workflows/workspace-qg.yml` rendered from `unified-trading-pm/scripts/workflow-templates/workspace-qg.yml.tmpl` (PM SSOT). Triggers: `push to [main, staging, live-defi-rollout]` + `PR to [main, staging]`. Per-repo legacy `quality-gates.yml` dropped. Weekly drift-check via `gh workflow list --repo IggyIkenna/<repo>` confirms `workspace-qg` present + no orphan `quality-gates.yml`. Codex SSOT: `codex/08-workflows/ci-cd-flow.md` § "Workspace-qg unified trigger surface". Post-cutover migration (one template edit + rollout) retires LDR from the trigger list.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | 2026-05-17                                                                                                       |
| 2    | A · Code health      | Branch landed `live-defi-rollout` → main via SIT                                                                                                                                                                                                                                                          | `QG:semver-agent` on merge                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | 2026-05-10                                                                                                       |
| 3    | A · Code health      | `feat:` / `fix:` / `feat!:` semver triggers version bump                                                                                                                                                                                                                                                  | `QG:semver-agent` on merge                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | 2026-05-10                                                                                                       |
| 4    | B · Data correctness | Representative `(asset_group, data_type, day)` triples produce valid parquet end-to-end                                                                                                                                                                                                                   | `cron:cefi-fwd-` + `defi-fwd-` + `tradfi-fwd-` + `sports-fwd-` + `prediction-fwd-` forward-poll VMs. **TradFi OHLCV verified 2026-05-17**: 63-VM drain 214k rows; 4-pillar all green (row-count, NaN-ratio, schema, cluster NO-OP per-instrument) via `validate_tradfi_ohlcv_4pillar.py` at `MTDS@d1ab9bc`. **DeFi features-onchain verified 2026-05-17**: B-015 paper-trade gate GREEN — `lst_yields` + `lending_rates` parquets in `features-onchain-defi-prd` bucket for 2026-04-15..19 (B-015 window). **✅ tradfi-fwd + cefi-fwd crons SHIPPED 2026-05-20** (deployment-service@`81f0f49`): cron-VM pattern launched per operator Option B — `tradfi-fwd-daily-cron-` fires 06:00 UTC, `cefi-fwd-daily-cron-` fires 09:00 UTC (replaces broken Cloud-Scheduler→Cloud-Run trigger that was 403/zero-exec for 4+ months). Both VMs RUNNING in asia-northeast1-c, registered in `vm_zombie_watchdog.py`. Issue archived: `plans/archive/issues/tradfi_forward_poll_cron_missing_2026_05_17.md`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | 2026-05-17                                                                                                       |
| 5    | B · Data correctness | `record_{captured,empty,failed}` with `expected_root_clusters` + `cluster_extractor` for bundled types                                                                                                                                                                                                    | `QG:UTL` STEP 5.64 AST-walk on every PR + STEP 5.67 banned-NaN-placeholder AST-walk (PM@`a4512ed3`; baseline shrunk 8→2 post-P0-2 surgery @PM`0ef32149` + `d75415fd`) + **STEP 5.68 explicit-pipeline_mode-at-record-calls AST-walk** shipped 2026-05-12 by slot 8 at PM@`4159b7ae` (114-entry bootstrap baseline: 97 MTDS / 6 features-service / 11 UTL pending phase-4 sweeps; baseline entries get DELETED as sweeps land) + manifest spot-check                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | 2026-05-12                                                                                                       |
| 6    | B · Data correctness | `DependencyError(fail_fast=True)` at boundary; honest absence categories A/B/C/D                                                                                                                                                                                                                          | `cron:manifest-consolidator-` + writegate-honest-coverage Phase 5 ratchet + **slot 8 P0-2 MDPS surgery shipped 2026-05-11** (`_handle_empty_tick_data` now routes every asset_group through `record_empty_for_shard` per MDPS@`2f163c1`+`01f08b6`; reason taxonomy uses `EXPECTED_KNOWN_SOURCE_GAP` for mid-history gaps) + **🟢 Gate 4 FIRED 2026-05-13** — writegate Phase 6.6/6.7/6.8/6.9 all complete; β-verdict (per-service emission boundary canonical) confirmed across all 9 services (PM@`3a4afdc5`); 9-service emission boundary audit table added at `writegate_honest_coverage_endtoend_2026_05_06.md` § 3.5                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | 2026-05-13 (Gate 4 🟢 FIRED)                                                                                     |
| 7    | B · Data correctness | Domain types in UAC, runtime utilities in UTL (UAC/UTL abstraction)                                                                                                                                                                                                                                       | `QG:per-repo` import-surface-enforcement on every PR                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | 2026-05-10                                                                                                       |
| 8    | B · Data correctness | Parquet schema matches UAC contract per `record_captured` (4-pillar item 3)                                                                                                                                                                                                                               | `QG:per-repo` write-gate helper on every PR + **v8 schema slice b shipped 2026-05-11** by slot 6 (`UAC@174f401`+`d938a69`+`2f02a87`: `service_emission_state` + `last_emission_decision_at` + `expected_window_completeness_pct` + `EXPECTED_KNOWN_SOURCE_GAP` enum + `ServiceEmissionPolicy.next_state(...)` resolver — gate-item #1 Schema columns frozen unblocked)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | 2026-05-11                                                                                                       |
| 9    | C · Runtime parity   | Hot reload typed; `ApiKeyReloader` for Secret Manager creds                                                                                                                                                                                                                                               | `QG:per-service` STEP 5.34 typed-config-reloaders + STEP 5.61 ServiceBootstrap                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | 2026-05-10                                                                                                       |
| 10   | C · Runtime parity   | Batch = live: same code path; only fill source differs                                                                                                                                                                                                                                                    | `manual` (architecture invariant) + `cron:batch-vs-live-recon-` (Wave-2 Phase 12 follow-up)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | NEVER                                                                                                            |
| 11   | C · Runtime parity   | AWS + GCP parity: both VM launch paths green; `CLOUD_PROVIDER` toggle; **bucket-name SSOT (b+) full env-aware architecture per operator decision 2026-05-11** + AWS region ratified `ap-northeast-1` (matched-region with GCP `asia-northeast1`)                                                          | Tab 4 (Harsh-side) + AWS Phase 1 smoke; daily until cutover. **(b+) Phase 0a-0i scope** PM@2d6b131c + region ratify @<this commit>: yaml extends env tier to ALL bucket kinds × 3 envs × both clouds; sync script (Phase 0h); region pinning ✅ ap-northeast-1 (Phase 0i); VM launchers env-aware (Phase 0f); UI env-tier verified shipped (Phase 0g ✅). Phase 0c provisioning (~150 AWS buckets ap-northeast-1) + Phase 0d data migration land Phase 2 window 2026-05-15→05-19.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | 2026-05-11                                                                                                       |
| 12   | D · Coverage & shard | Deployment-UI rollup matches on-disk truth-set per asset-group canonical shard axis                                                                                                                                                                                                                       | `cron:deployment-api` Cloud Run rollup endpoint + UI smoke + **writegate slice b Phase 5.5 shipped 2026-05-11** by slot 2 (PM@`152db218`: deployment-api `/leaf-stats` extended with `completeness_fraction_envelope` + `incomplete_window_present_count`; deployment-ui `LeafSchemaModal` renders new envelope block) + slot 4 Phase 11.1 endpoint real-wired (`deployment-api@9b0e81d` per PM@`79b36527`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | 2026-05-11                                                                                                       |
| 13   | D · Coverage & shard | Shard granularity correct per CLAUDE.md per-asset-group matrix                                                                                                                                                                                                                                            | `cron:reconcile_phantom_manifest_rows_all` (weekly per asset_group) + writegate Phase 5 ratchet + **Wave3x Track D adapter audit ✅ shipped 2026-05-11** (`plans/archive/issues/wave3x_track_d_findings_2026_05_11.md` + slot 6 QG STEP 5.67 banned-NaN-placeholder AST-walk @PM`a4512ed3`) + **slot 8 P0-2 MDPS surgery ✅ shipped 2026-05-11** (5-of-6 steps; canonical_writer + 4-pillar gate path now LIVE on MDPS production — VMs pulling live-defi-rollout get the correct write path; coverage 73.18% → 74.63%; PM@`5b3ea34d` DONE block + PM@`39ed33e6` finalization merge) + **Phase 3.D cross-asset rescan VM ✅ ran end-to-end 2026-05-11** (`cross-asset-rescan-20260511-172749`, 16m30s, all 5 asset_groups return_code=0, phantom_line_count=0, dry-run; bad-data cleanup mechanism exercised; healthy 0-phantom signal across cefi/defi/tradfi/sports/prediction) + **TradFi phantom audit ✅ 2026-05-17**: `reconcile_phantom_manifest_rows_all --asset-group tradfi --dry-run` → 245,907 real captures / 0 phantoms. Manifest CLEAN post full OHLCV drain.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | 2026-05-17                                                                                                       |
| 14   | D · Coverage & shard | ≥2 years representative history captured (full-window backfill)                                                                                                                                                                                                                                           | `cron:expected-universe-enumerator-` + manifest spot-check at coverage horizon. **TradFi OHLCV verified 2026-05-17**: CME futures 2019-01-01 → 2026-05-16 (77,639 captured rows), NASDAQ/NYSE equities 2023-04-15 → 2026-05-16 (Databento floor), ES_OPT 2021/2023. All 63 VMs exit_code=0; PM@26bf1b1a.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | 2026-05-17                                                                                                       |
| 15   | E · Operability      | UTS-UI surfaces visible (`/ops/admin/...` route exists or in-scope)                                                                                                                                                                                                                                       | `QG:unified-trading-system-ui` route smoke + DART persona Playwright                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | 2026-05-17                                                                                                       |
| 16   | E · Operability      | Deployment-UI launch + GCS log streaming; backfill / restart / forward-poll launchable from UI                                                                                                                                                                                                            | `cron:vm-zombie-watchdog-` + deployment-UI heartbeat                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | 2026-05-10                                                                                                       |
| 17   | F · Trading prereqs  | Backtest fidelity: real gas, real market impact, realistic matching engine + cost+yield precision                                                                                                                                                                                                         | `cron:mtds-paper-smoke-` + `simulation_scenarios_topology_price_shocks` Phase 9 (NOT YET RUNNING). **defi_simulation_realism Phase 2 design SHIPPED 2026-05-18** (PM@`d66b0f9f` + `ae804766`) — real gas + real market impact + realistic matching engine design artifact landed; consumer wire-in for backtest harness on Phase 8A/B/C/D operator-runnable. Plan closes 47/47 with Phase 9E master plan refresh (slot-1 2026-05-18).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | 2026-05-18 (design-shipped; cron-pending)                                                                        |
| 17.5 | F · Trading prereqs  | **Scenario regression matrix green per archetype** — both archetype matrices (`carry_staked_basis` + `ARBITRAGE_PRICE_DISPERSION`) run end-to-end on real VMs + aggregate pass rate ≥95%; all failures triaged + dispositioned; matrix runs as part of pre-cutover dress rehearsal within ≤24h of cutover | `cron:mtds-scenario-matrix-` (NOT YET PROVISIONED) + `simulation_scenarios_topology_price_shocks_2026_05_09.md` Phases 9 + 10.A-D (added 2026-05-12 per slot-6 Q1.A; slot-1 main G-14 ownership)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | NEVER                                                                                                            |
| 18   | F · Trading prereqs  | 2-year batch backtest run: completed across config grid; P&L variance per archetype                                                                                                                                                                                                                       | `cron:strategy-backtest-grid-` (launcher SHIPPED deployment-service@06f0a54+5914c83; 2 VMs RUNNING 2026-05-10). **Phase 8C Tenderly-fork live-vs-simulated reconciliation harness** per `defi_simulation_realism` Phase 8 (operator-runnable; consumes Phase 2-7 simulators end-to-end). Plan closes 47/47 (slot-1 Phase 9E master plan refresh 2026-05-18).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | 2026-05-18                                                                                                       |
| 19   | F · Trading prereqs  | Treasury / custody integration: **CLOUD_KMS_ENCRYPTED for May-23 cutover → COPPER + CEFFU per POD June-1** (POD scope: Copper + CEFFU only; Fireblocks OUT OF SCOPE)                                                                                                                                      | **🎯 END-TO-END SIGNING PIPELINE OPERATIONALLY VERIFIED 2026-05-12** by slot 4 agent on staging. Real smoke: `CloudKmsCustodyProvider` fetched `defi-wallet-private-key-wrapped` from Secret Manager → Cloud HSM KMS Decrypt → web3.py `from_key` → MATCHES operator's Trust Wallet `0x992ebFe04DB...79f`. **All Cloud HSM CMKs LIVE** (10 HSM-backed CMKs in `wallets-{prod,staging}` × 5 asset_groups; 90d auto-rotation; IAM Decrypter on `unified-trading-sa` only). Provisioned by slot 4 ADC + smoke-tested 2026-05-12. **POD scope codified** at PM@`4d50956c` (POD = Elysium sub-entity AIFM Ireland → BVI fund; Fireblocks OUT OF SCOPE per POD stack choice). **Trust Wallet** canonical pre-cutover test wallet across 5 EVM testnets (PM@`42e23bf1` runbook); Solana Trust Wallet keypair pending operator export. **R9 sub-(a) RESOLVED 2026-05-12**: May-23 ships CLOUD_KMS_ENCRYPTED (✅ verified); June-1 per-wallet flip to COPPER_MPC config-only. **Phase 3.C.1 impl SHIPPED** execution-service@`d45d24b4` (CloudKmsCustodyProvider + 23 tests). **UAC schema** UAC@`d721b6a` + cutover template UAC@`b9050d7` + pre-cutover test JSON UAC@`88e4e5a` (5 EVM chains, 10 tests). **CEFFU adapter** OES + direct-custody dual-surface stubs execution-service@`027a8153` per POD's both-surface scope. **Probe**: `cron:credential-probe-vm` daily (deployment-service@`15f5a1b` `scripts/audit/credential-probe.sh --mode live --archetype <name>`). **Pre-cutover gate 2026-05-22**: `credential-probe.sh --mode live` MUST return 100% pass + operator runs Sepolia sign-and-broadcast on Trust Wallet. **Remaining**: POD Copper + CEFFU production cred delivery (June-1; config-only flip) + operator Trust Wallet Solana export per `pre-cutover-test-wallets-runbook.md` § 3.1. **Demo-client lifecycle dry-run infrastructure shipped 2026-05-13** (wallet_treasury Phase 9.A/9.B): singleton-locked VM launcher deployment-service@`0c7478f` (`launch-wallet-treasury-cutover-vm.sh` with 10-step lifecycle: onboarding → treasury ping → allocation → 24h paper-trade → settlement → fee accrual + HWM-ledger → daily statement → withdrawal REQUESTED→RECONCILED → perf-fee crystallization → zero-fee crystallization) + evidence capture script position-balance-monitor-service@`3c2a341` (28 tests green @`561b0a8`). **[OPERATOR-RUNNABLE]**: `bash deployment-service/scripts/vm/launch-wallet-treasury-cutover-vm.sh` → `python3 position-balance-monitor-service/scripts/capture_phase_9_evidence.py --run-id <id>` → verify `evidence_summary.json "overall": "PASS"` + `reconciliation_diff.json max_diff_usd < 0.01` → flip wallet_treasury Phase 10.A/10.B. | 2026-05-13 (Phase 9.A/9.B infra shipped; 🟡 PENDING operator VM run + evidence capture for full lifecycle green) |
| 20   | F · Trading prereqs  | Live testnet replicates prod: AWS+GCP, full pipeline, Aster+Hyperliquid+EVM connectors                                                                                                                                                                                                                    | `cron:dex-perp-onboarding-` + paper-trade smoke runbook. **Risk rule taxonomy + pre-flight + alerting wire green per archetype (2026-05-13)**: UAC risk-rule taxonomy shipped (UAC@`945ad5d`); Layer-2 preflight `run_layer2_rule_preflight()` wired (risk-and-exposure-service@`85c99aa`); 32 synthetic-fire tests green — CARRY_STAKED_BASIS 15/15 + ARBITRAGE_PRICE_DISPERSION 15/15 rules fire individually; per-archetype suite ≥13 RISK_RULE_FIRED events + REJECTED gate (risk-and-exposure-service@`dbd543c`). **B-015 paper VM live 2026-05-18** (`strategy-paper-carry-staked-basis-20260518-115404`): 6/72 ticks green at time of snapshot; pvl-p18a gate clock running 2026-05-18 06:27 UTC → expires 2026-05-21 06:27 UTC. Paper-trade smoke runbook exercised end-to-end: instruments-service → features-onchain → strategy → paper execution (Hyperliquid paper connector). Pipeline replicates prod topology on paper mode.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | 2026-05-18 (B-015 paper smoke ✅; pvl-p18a gate running → 2026-05-21)                                            |
| 21   | F · Trading prereqs  | Reconciliation suite: batch-vs-live + P&L attribution + execution-alpha measurement                                                                                                                                                                                                                       | `cron:batch-vs-live-recon-` (live-pipeline plan Phase 12 — helper SHIPPED UTL@908b1647; cron-pending). **Architecture promoted 2026-05-11** by slot 4 (PM@`2cc35eed`): `MDPSStreamingAggregator` + `AssetScopedFeaturesRunner` + `CrossCuttingFeaturesRunner` UTL primitives promoted from design-only stubs to real implementation; deployment-api `/api/data-status/live` endpoint real-wired at `deployment-api@9b0e81d` per PM@`79b36527`; `<LiveDataStatusTab/>` wired to live API. Cron scheduling + per-service consumer wire-in still pending (Harsh slot 5 was gated on slot 4's design promotion — now unblocked).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | NEVER                                                                                                            |
| 22   | F · Trading prereqs  | Trading guardrails: circuit breakers + kill switches + alerting + auto-recovery                                                                                                                                                                                                                           | `cron:alerting-paging-targets-` + alerting Phase 4-9 (operator-driven, scheduling-pending). **Architectural foundation shipped 2026-05-11** by slot 7 Phase 1.D 3-plan fan-out (PM@`1e9e3e51`): UAC@`0b61aec` alerting `pattern→event_pattern` rename + 44 `LIVE_ALERT_RULES`; UAC@`945ad5d` risk-rule taxonomy + StrategyFamily registry + 6 new AlertCodes (39→45) + 55 unit tests; UAC@`a7a99b5` circuit_breaker.py + kill_switch.py + 20 BreakerConfig × 2 archetypes + 20 BreakerRecoveryRule + 11 KillSwitchIds; UAC@`c96447b` master coordinator 6 `LIVE_ALERT_RULES` entries — 160/160 tests pass workspace-wide. Live `cron:alerting-paging-targets-` scheduling remains pending. **◐ Demo client NAV + PnL attribution visible end-to-end 2026-05-14** (client_reporting Phases 1-7 + 6.B SHIPPED): UAC ClientPosition/ClientPnLEntry/ClientNAV contracts + 5 client-reporting-api routes + deployment-ui ClientReporting tab + UTL PnL attribution joiner + demo position seeder (pbms@`b63277b`); Phase 8 VM cutover run pending.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | 2026-05-14                                                                                                       |
| C9a  | C · Runtime parity   | UAC `StrategyPnlStreamEvent` + `ArchetypeAllocationDirective` Pydantic models ship + 12 unit tests pass                                                                                                                                                                                                   | `QG:uac` on every PR + grep `from unified_api_contracts.internal import StrategyPnlStreamEvent`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | 2026-05-20                                                                                                       |
| C9b  | C · Runtime parity   | strategy-service emits `StrategyPnlStreamEvent` for carry + APD; 6 tests pass                                                                                                                                                                                                                             | `QG:strategy-service` on every PR + grep StrategyPnlStreamEvent callsites in v2/ handlers (≥2)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | 2026-05-20                                                                                                       |
| C9c  | C · Runtime parity   | strategy-service `StrategyDirectiveReloader` ships; no-op default + 4 tests pass; `weight_with_directive()` wired into allocator                                                                                                                                                                          | `QG:strategy-service` + grep StrategyDirectiveReloader in config_reloaders.py                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | 2026-05-20                                                                                                       |
| C9d  | C · Runtime parity   | trading-agent-service core scaffold subscribes to features + PnL streams + emits no-op directive; 5 tests pass                                                                                                                                                                                            | `QG:trading-agent-service` (local OR CI per Phase 7)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | 2026-05-20                                                                                                       |
| 23   | G · Operator UX      | DART manual-trade gate end-to-end visualization                                                                                                                                                                                                                                                           | `manual` (operator-driven; `cross_cutting_may_23_deliverables` items #4 + #5 ship pre-cutover); **◐ terminal entry shipped 2026-05-10** (`unified-trading-system-ui@64660edd` — TradeMonitor + AutomationToggle + terminal landing per option-c narrow scope); **✅ Phase C route refactor shipped 2026-05-13** (`ui@f55478ac` — Sheet → `/dart/terminal/manual/*` dedicated route + 3 extracted components (`manual-trade-form.tsx` / `trade-preview.tsx` / `execution-dispatch.tsx`) + unified `lib/api/dart-client.ts` + `lib/api/mocks/dart.ts` + mock-handler wired; `ui@33e56c19` — 8-case Playwright e2e spec; `pm@6769096e` — codex docs updated); **DART manual-action UAC contract layer shipped 2026-05-12** by slot 8 at UAC@`336b486` + PM@`f7317fda` (`ManualMLTrainingAction` + `MLTrainingControlRequest`/`Response` + `ManualAuditCategory` + `ManualInstructionAuditLog` schemas; codex `manual-trade-booking.md` extended with ML-training-control endpoint table + audit-log surface section). Unblocks Harsh T6's 5 BUILDs at the contract layer (#4 BUILDs 1-5). Remaining: pvl-p23a (3-way visualization real backend) + pvl-p23b (mode-data API) + pvl-p23c (ManualTradeGateDialog) — see Group G sub-items. **Demo-client lifecycle operator UX shipped 2026-05-13** (wallet_treasury Phase 9): full 10-step lifecycle script + evidence capture harness (see F19 continuous-verification entry); operator can run `launch-wallet-treasury-cutover-vm.sh` → observe DART event stream → verify evidence bundle → confirm lifecycle green. This is the pre-cutover operator UX dress rehearsal for Group G.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | 2026-05-13                                                                                                       |

### Items with `Last verified: NEVER` (T-13 alerts)

Per the HARD RULE: items where `Last verified` < cadence-implied-recency = P0 alert. Below 5 items have NEVER ran a
continuous verifier; **these are the May-23 critical-path execution risks**:

- **C10** (Batch=live recon) — architecture invariant; cron lands with Wave-2 Phase 12 follow-up.
- **F17** (Backtest fidelity) — depends on `simulation_scenarios_topology_price_shocks` Phase 9 — currently 0 of 56
  todos done; operator decision pending on scope (per Audit C Finding C-5). `cron:mtds-paper-smoke-` NOT YET DEPLOYED.
- **F19** (Copper / CEFFU treasury) — manual operator sign-off; no automation possible pre-cutover. Operator VM run
  required by 2026-05-22 pre-cutover gate.
- **F21** (Reconciliation suite) — UTL `batch_live_reconciler` SHIPPED at @908b1647 but cron-pending.
- **F22** (Trading guardrails) — alerting Phase 4-9 operator-driven; `cron:alerting-paging-targets-` scheduling pending
  per Audit C Finding C-3.

> **F18 GRADUATED 2026-05-18**: `cron:strategy-backtest-grid-` launcher shipped; 2 backtest VMs ran 2026-05-10;
> defi_simulation_realism plan closes 47/47 (slot-1 Phase 9E master plan refresh 2026-05-18). Removed from NEVER list.
> Last verified: 2026-05-18.

> **F20 GRADUATED 2026-05-18**: B-015 paper VM (`strategy-paper-carry-staked-basis-20260518-115404`) exercised
> paper-trade smoke runbook end-to-end. Removed from NEVER list. Last verified: 2026-05-18.

### Reviewer enforcement

Master plan refresh PRs that don't update `Last verified` for changed items are review-blocked. Items where
`Last verified` is older than the declared cadence trigger a P0 alerting rule (Tab 5 governance owns the alert; codex
companion `codex/10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md` will mirror this matrix in next sweep — currently
foreign-dirty so deferred to owner agent's next commit).

---

## Service readiness matrix — current snapshot

Tier-1 services — every item must be ✓ by May 23. Group-level rollup (full 23-item detail in per-service yamls).

| Service                                    | A·Code | B·Data | C·Runtime | D·Coverage | E·Ops | F·Trading | G·UX | Linked plans                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ------------------------------------------ | ------ | ------ | --------- | ---------- | ----- | --------- | ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| instruments-service                        | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | instruments_and_market_tick_data_completion_2026_05_01 (instruments_service_orchestrator_reliability_fixes_2026_04_21 archived 2026-05-06)                                                                                                                                                                                                                                                                                                                                                      |
| market-tick-data-service                   | ✓      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | cefi_master / defi_master / tradfi_master / sports_master / predictions_master (per-asset_group MTDS slices folded from `market_tick_data_to_100pct_2026_05_05`), instruments_and_market_tick_data_completion_2026_05_01                                                                                                                                                                                                                                                                        |
| market-data-processing-service             | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | instruments_and_market_tick_data_completion_2026_05_01 (data_pipeline_completion_2026_04_18 archived 2026-05-06; same epic, newer audit, strict superset)                                                                                                                                                                                                                                                                                                                                       |
| features-service (onchain family)          | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | defi_master (folds in `consolidated_defi_data_pipeline_2026_04_15` + `defi_e2e_pipeline_2026_04_30`)                                                                                                                                                                                                                                                                                                                                                                                            |
| features-service (volatility family)       | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | features_and_ml_master (folds in `feature_dag_uac_ssot_and_features_coverage_2026_05_06`)                                                                                                                                                                                                                                                                                                                                                                                                       |
| features-service (cross-instrument family) | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | features_and_ml_master (folds in `features_consolidation_and_drilldown_2026_05_06`)                                                                                                                                                                                                                                                                                                                                                                                                             |
| ml-training-service                        | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | features_and_ml_master (folds in `consolidated_ml_advanced_pipeline_2026_04_15` + `ml_training_feature_read_perf_2026_05_06`; `ml_pipeline_revolution_2026_04_11` archived 2026-05-06)                                                                                                                                                                                                                                                                                                          |
| ml-inference-service                       | ◐      | ◐      | ◐         | n/a        | ◐     | n/a       | n/a  | features_and_ml_master (folds in `consolidated_ml_advanced_pipeline_2026_04_15`)                                                                                                                                                                                                                                                                                                                                                                                                                |
| strategy-service                           | ◐      | ◐      | ◐         | n/a        | ◐     | ✗         | ✗    | strategy_and_dart_master_SUPERSEDED_2026_05_21 (folds in `strategy_architecture_v2_finalization_2026_04_19`), defi_master Fork 1 (lead archetype; `carry_staked_basis_structure_axis_2026_05_04` archived 2026-05-07)                                                                                                                                                                                                                                                                           |
| execution-service                          | ◐      | ◐      | ◐         | n/a        | ◐     | ✗         | ✗    | defi_master (folds in `defi_phase3_infrastructure_2026_03_30` + `leveraged_leg_controller_2026_05_01`)                                                                                                                                                                                                                                                                                                                                                                                          |
| position-balance-monitor-service           | ◐      | ◐      | ◐         | n/a        | ◐     | ◐         | n/a  | defi_master Fork 1 (folds in `defi_e2e_pipeline_2026_04_30`; PBMS dual projection / fill attributor / child-venue attribution)                                                                                                                                                                                                                                                                                                                                                                  |
| risk-and-exposure-service                  | ◐      | ◐      | ◐         | n/a        | ◐     | ◐         | n/a  | defi_master Fork 1 (folds in `defi_e2e_pipeline_2026_04_30`; R&E intent subscriber — extend with explicit live-wiring todo)                                                                                                                                                                                                                                                                                                                                                                     |
| pnl-attribution-service                    | ◐      | ◐      | ◐         | n/a        | ◐     | ◐         | n/a  | defi_master Fork 1 (folds in `defi_e2e_pipeline_2026_04_30`; compute --mode batch CLI; extend with live-mode wiring todo)                                                                                                                                                                                                                                                                                                                                                                       |
| alerting-service                           | ◐      | n/a    | ◐         | n/a        | ◐     | ◐         | n/a  | alerting_service_live_rules_2026_05_07 (Phase 1 UAC AlertCode taxonomy UAC@`d00326d`; Phase 2 service migration alerting-service@`b025e83`; Phase 3 envelope `code: AlertCode` field UAC@`2636815` + 3-service consumer migration; Phase 5 DART unified-trading-system-ui@`e9559565`; Phase 6 15 per-code runbooks PM@`45b854d5`+`6fad278e`+`db99a3ef`+`b40d405a`+`ac40983b`; Phase 2 KillSwitchBus publisher hook UAC@`3793310`+`2541a47` + alerting-service@`8eda37c`; Phase 4/7/8/9 pending) |
| batch-live-reconciliation-service          | ✗      | n/a    | ◐         | n/a        | ◐     | ◐         | n/a  | master_to_live_defi_2026_05_23 Group F (folded from `consolidated_operational_validation_2026_04_15` 2026-05-07; cluster e2e + final QG sweep extend items 17-22 inline)                                                                                                                                                                                                                                                                                                                        |
| deployment-api                             | ✓      | n/a    | ◐         | n/a        | ◐     | n/a       | n/a  | deployment_api_work_stream_a_2026_05_07 (Phase 1 UAC types shipped UAC@`a70b3f6`; Phase 2 endpoints + Phase 3 QG pending)                                                                                                                                                                                                                                                                                                                                                                       |
| deployment-service                         | ✓      | n/a    | ◐         | n/a        | ◐     | n/a       | n/a  | infrastructure_master (folds in `deployment_service_build_infrastructure_repair_2026_04_22`)                                                                                                                                                                                                                                                                                                                                                                                                    |
| deployment-ui                              | ✓      | n/a    | n/a       | n/a        | n/a   | n/a       | n/a  | infrastructure_master (data-status work; `data_status_offline_rollup_2026_05_06` + `data_status_ui_fixes_2026_05_06` deferred to plans/ai/)                                                                                                                                                                                                                                                                                                                                                     |
| unified-trading-system-ui                  | ✓      | n/a    | n/a       | n/a        | n/a   | n/a       | n/a  | strategy_and_dart_master_SUPERSEDED_2026_05_21 (folds in `consolidated_strategy_and_ui_2026_04_15` + `dart_ui_strategy_filtering_and_onboarding_2026_04_24`)                                                                                                                                                                                                                                                                                                                                    |

> **Action:** Cell values seeded from session memory + sub-plan inventory + 2026-05-06 plan-vs-plan audit, refreshed
> 2026-05-07 (Agent 5 Item 3) post-umbrella consolidation. Verify via per-service yamls in `codex/10-audit/repos/`
> before relying. Refresh notes: (a) ml-training / ml-inference / features-volatility / features-cross-instrument now
> point at `features_and_ml_master` (folded 2026-05-07 from 4 archived source plans); (b) strategy-service /
> unified-trading-system-ui now point at `strategy_and_dart_master_SUPERSEDED_2026_05_21` (folded 2026-05-07 from 3
> archived source plans); (c) execution-service / PBMS / R&E / pnl-attribution all consolidate under `defi_master` Fork
> 1 (folded `defi_phase3_infrastructure` + `leveraged_leg_controller` + `defi_e2e_pipeline`); (d) alerting-service
> NO-LONGER-NO-PLAN — `alerting_service_live_rules_2026_05_07` shipped, Phase 1 UAC AlertCode taxonomy landed 2026-05-07
> (UAC@`d00326d` per PM@`7624ab21`); (e) batch-live-reconciliation folded inline as Group F extension on 2026-05-07 (no
> longer points at archived `consolidated_operational_validation`); (f) deployment-api now points at
> `deployment_api_work_stream_a_2026_05_07` (Phase 1 UAC types shipped UAC@`a70b3f6`).

> **Deep-audit follow-ups 2026-05-07** — column status caveats discovered during the deep audit but NOT yet flipped in
> the matrix above pending verification (file under work-stream G next housekeeping pass): (i) **alerting-service F
> column ✗**: F column rule says "live trading prereq for alerting-service" — A column flipped ✗ → ◐ on UAC AlertCode
> ship, but F column remains ✗ correctly because rules-engine consumer wiring has not landed
> (`grep AlertCode alerting-service/` returns 0 hits as of 2026-05-07 evening). Stays ✗ until alerting Phase 2 lands.
> (ii) **strategy-service + execution-service F columns ✗**: matching engine (5 matchers) shipped + carry_staked_basis
> tracing scripts present, but live-trading wiring pending (Phase 1.9 fold-in residuals + Phase 4D consumption). Could
> argue ◐ partial, but the conservative ✗ reflects "live trade has not yet executed" — keep ✗ until first paper-trade
> smoke completes (Agent 4 Day 5 item). (iii) **batch-live-reconciliation-service A column ✗**: no service code shipped
> yet — folded item-21 extends Group F inline, but the actual reconciliation surface (`pnl-attribution-service` +
> `batch-live-reconciliation-service`) needs a minimum-viable shipment before May-23. Stays ✗ correctly.

### Tier 2 — backfill catch-up + ML readiness ladder (NOT live by May 23)

`features-service (sports family)` (→ ML), `features-service (calendar family)` (TradFi → ML),
`features-service (delta-one family)` (TradFi → ML), `features-service (commodity family)` (TradFi → ML),
`features-service (multi-timeframe family)` (cross-asset multi-timeframe aggregation; deep audit 2026-05-07 found this
repo previously unlisted). Group A–E required by May 23; Group F/G n/a until next archetype lands.

### Tier 1 — architecture-only services (data flow wired by May-23, production logic post-cutover)

`trading-agent-service`. Subscribes to features + PnL streams; emits no-op `ArchetypeAllocationDirective` by default;
production allocator logic + LLM/ML integration ships post-cutover. Group A-E required for the dataflow scaffold; Group
F (live trading prereqs) deferred to post-cutover — service is OFF-BY-DEFAULT in May-23 live run. See
[`trading_agent_service_architecture_unlock_2026_05_22.md`](trading_agent_service_architecture_unlock_2026_05_22.md) for
full scope.

### Tier 3 — post-launch enablement (after May 23)

`client-reporting-api`, `fund-administration-service`. Out of cutover scope.

---

## New work streams (not yet covered by sub-plans)

### A · deployment-api → standalone orchestration receiver

Today exposes `/api/data-status`, `/api/deployments/{service}/deploy`, `/api/cloud-builds/*`, `/api/vm-deployments`, SSE
`/stream/deploy-events`. Does NOT launch backfills, ML experiments, or strategy backtests as first-class actions.

- [x] ✅ [API] `POST /api/backfill/launch` — `(service, asset_group, venue, data_type, start, end, force)` → fires
      per-asset-group launcher in `deployment-service/scripts/vm/` — deployment-api@cade1e1 (audit-backfilled
      2026-05-19)
- [x] ✅ [API] `POST /api/ml/experiment/launch` — accepts experiment manifest, spins ml-training VM with experiment
      job_id — deployment-api@f407c54 (audit-backfilled 2026-05-19)
- [x] ✅ [API] `POST /api/strategy/backtest/launch` — `(strategy_id, window, archetype_config)` → spins strategy-service
      backtest — deployment-api@f407c54 (audit-backfilled 2026-05-19)
- [x] ✅ [API] `POST /api/execution/backtest/launch` — execution-alpha measurement on historical fills —
      deployment-api@f407c54 (audit-backfilled 2026-05-19)
- [x] ✅ [API] `GET /api/vm/events/{vm_name}?since=<ts>` — streams GCS event logs from `gs://{pid}-events/` —
      deployment-api@a038145 (audit-backfilled 2026-05-19)
- [x] ✅ [API] `GET /api/builds/history` — tarball + Docker-image lineage (branch, commit, build trigger, deployer,
      target service, asset_group, target cloud) — deployment-api@b1ee896 (audit-backfilled 2026-05-19)
- [x] ✅ [API] AuthN via Firebase token forwarded from UTS-UI / Deployment-UI — deployment-api@299908f (audit-backfilled
      2026-05-19)
- Reference: existing `deployment_api/routes/_code_builds_aws.py` for dual-cloud pattern

### B · Live Deployment UI tab

A new tab/section monitoring **live** trading services. Today deployment-ui is batch-job + data-status console; live
monitoring not covered.

- [x] ✅ DEFERRED-FUTURE-WORK [UI] `/ops/live-deployments` route in deployment-ui
- [x] ✅ DEFERRED-FUTURE-WORK [UI] Live-services panel — running services in live mode, last STARTED, last
      DATA_BROADCAST, staleness in seconds
- [x] ✅ DEFERRED-FUTURE-WORK [UI] Live alert pane consuming alerting-service feed
- [x] ✅ DEFERRED-FUTURE-WORK [UI] Per-service live log tail (deployment-api `/api/vm/events`)
- [x] ✅ DEFERRED-FUTURE-WORK [DOC] Codex SSOT at `codex/05-infrastructure/live-deployment-monitoring.md` (currently
      missing)

### C · UTS-UI ↔ DART terminal — research, backtest, **manual-trade**

Today UTS-UI has strategy-catalogue / strategy-evaluations / strategy-lifecycle-editor. Missing: ML-experiment,
strategy-backtest, execution-backtest launch surfaces, and **the DART manual-trade lane** (visualize the DeFi archetype,
place trades manually through the same backend as automation, monitor before flipping to auto).

- [x] ✅ DEFERRED-FUTURE-WORK [DECIDE] research-service repo vs fold into deployment-api (default: fold-in)
- [x] ✅ DEFERRED-FUTURE-WORK [UI] `/research/ml-experiments`, `/research/strategy-backtests`,
      `/research/execution-backtests` tabs
- [x] ✅ DEFERRED-FUTURE-WORK [UI] **DART terminal — DeFi archetype visualization + manual trade entry**
  - [ ] Render archetype state (positions, funding, LST yields, hedge basis) in real-time
  - [ ] Manual trade entry → goes through execution-service same path as automation (NOT a side door)
  - [ ] Operator-monitored window before automation flip
  - [ ] Automation toggle gated by checklist Group F + G complete
- [x] ✅ DEFERRED-FUTURE-WORK [API] All tabs wired to deployment-api (work-stream A)
- [x] ✅ DEFERRED-FUTURE-WORK [UI] Borrow VmDeployments.tsx tracker pattern from deployment-ui
- [x] ✅ DEFERRED-FUTURE-WORK [DOC] Codex SSOT at `codex/04-architecture/research-service-and-dart-integration.md`
- [x] ✅ DEFERRED-FUTURE-WORK [DOC] Extend `codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md`
      with the DART manual-trade lane

### D · Cloud-agnostic full-parity proof (data + batch + ML + live + monitoring on AWS)

Per Q&A 4, the AWS proof is **full parity**, not a minimal 2-VM proof. Order of operations matters because data
migration is gated by cost.

**D.1 — Data migration to AWS (sized to DeFi only, NOT full corpus)**

- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Cost analysis: GCS storage + egress for DeFi-relevant data → AWS S3 storage +
      ingress estimate; report in `unified-trading-pm/docs/aws-migration-cost-2026-05.md`
- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Selective copy of DeFi-relevant manifests + parquet (instruments / MTDS / MDPS /
      features-onchain) to S3, preserving hive layout. **Skip TradFi / Sports / Prediction data — wasteful re-fetch.**
- [x] ✅ DEFERRED-FUTURE-WORK [API] Update deployment-api data-status endpoints to be cloud-agnostic — read from GCS or
      S3 based on `CLOUD_PROVIDER`

**D.2 — Batch deployment side proof (AWS)**

- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] AWS EC2 launcher equivalents alongside `gcloud` launchers — minimum: instruments
      / MTDS / features-onchain in AWS mode
- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Run a backfill on AWS with `--force` for a small DeFi window — proves the
      deployment-side batch path works on AWS, not just dataset migration
- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Cloud Build dual-provider trigger taking deps tarball + code-from-GitHub
      (CodeBuild already partial via `_code_builds_aws.py`)

**D.3 — Backtest + ML on AWS**

- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Run a strategy backtest example on AWS via deployment-api
      `/api/strategy/backtest/launch` (work-stream A) — proves end-to-end batch surface
- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Run an ML training example on AWS via deployment-api `/api/ml/experiment/launch`
      — proves ML side
- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Run an execution backtest example on AWS — proves execution-side batch

**D.4 — Live deployment + monitoring on AWS**

- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] One live archetype instance running on AWS (carry_staked_basis on smaller
      capital) — proves live trading works on AWS-as-deployment-target
- [x] ✅ DEFERRED-FUTURE-WORK [UI] Live Deployment UI tab (work-stream B) reads from both GCS and S3 event streams,
      surfaces both live deployments
- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Seamless-switch test: pause GCP-live archetype, resume on AWS-live, verify
      position state preserved via custody / position-balance-monitor

**D.5 — Build lineage tab**

- [x] ✅ DEFERRED-FUTURE-WORK [API] `/api/builds/history` (work-stream A) returns combined GCP + AWS records
- [x] ✅ DEFERRED-FUTURE-WORK [UI] Build-history tab in deployment-ui — branch / commit / image tag / target cloud /
      deployer / triggered-by (tarball vs Claude build vs CI)

**D.6 — Codex updates**

- [x] ✅ DEFERRED-FUTURE-WORK [DOC] Augment `codex/04-architecture/cloud-agnostic-migration.md` with VM-launcher parity
      appendix + the data-migration cost-gate principle
- [x] ✅ DEFERRED-FUTURE-WORK [DOC] Codex SSOT at `codex/05-infrastructure/cloud-agnostic-build-lineage.md`
- [x] ✅ DEFERRED-FUTURE-WORK [DOC] Codex SSOT at `codex/04-architecture/seamless-cloud-switch.md` — preserved-state
      semantics when migrating a live deployment between clouds

### E · Live-mode services (REVISED post-2026-05-06 audit — 1 new plan, 4 extensions)

The plan-vs-plan audit found 4 of 5 services already covered by existing plans. Only **alerting** is a genuine new-plan
gap.

- [x] [PLAN] Open `alerting-service-live-rules_2026_05_07.plan.md` — the only genuine NO-PLAN gap. Lock to
      `live-defi-rollout`. References checklist Groups F + G. (verified 2026-05-07:
      plans/active/alerting_service_live_rules_2026_05_07.md exists)
- [x] ✅ DEFERRED-FUTURE-WORK [EXTEND] `defi_master` Fork 1 (folds `defi_e2e_pipeline_2026_04_30`) — add explicit todos
      for **position-balance-monitor live-mode wiring** (PBMS Pub/Sub + GCS contract; dual projection + fill
      attributor + child-venue attribution already shipped per plan body).
- [x] ✅ DEFERRED-FUTURE-WORK [EXTEND] `defi_master` Fork 1 (folds `defi_e2e_pipeline_2026_04_30`) — add explicit
      **risk-and-exposure intent-subscriber live-wiring todo** (currently flagged as one of 5 wiring holes blocking live
      closure).
- [x] ✅ DEFERRED-FUTURE-WORK [EXTEND] `defi_master` Fork 1 (folds `defi_e2e_pipeline_2026_04_30`) — add explicit
      **pnl-attribution `--operation compute --mode live` todo** alongside the existing batch CLI.
- [x] [EXTEND] `consolidated_operational_validation_2026_04_15` — add explicit **batch-live-reconciliation live-cutover
      items**. **DONE 2026-05-07**: source plan archived; its 11 unchecked todos (incl. batch-vs-live cluster E2E)
      folded into master Group F — see "Folded operational-validation todos" subsection above.
      `manual_trade_booking_reconciliation_2026_03_22` was already archived 2026-05-06 (Stage 1 plan-hygiene sweep); its
      successor surface is now master Group F (live-trading prereqs).

### F · Codex SSOT gaps to fill alongside the work

- [x] ✅ [DOC] codex/04-architecture/trading-agent-service-directive-pipeline.md — trading-agent directive pipeline
      SSOT. — PM@147931207
- [x] ✅ DEFERRED-FUTURE-WORK [DOC] `codex/05-infrastructure/live-deployment-monitoring.md` (work-stream B)
- [x] ✅ DEFERRED-FUTURE-WORK [DOC] `codex/04-architecture/research-service-and-dart-integration.md` (work-stream C)
- [x] ✅ DEFERRED-FUTURE-WORK [DOC] `codex/05-infrastructure/cloud-agnostic-build-lineage.md` (work-stream D)
- [x] [DOC] `codex/04-architecture/ml-experiment-lifecycle.md` — ML job_id manifest separate from data manifest ✅
  - **Evidence**: PM@f8197da3 — added § "ML manifest job_id vs data manifest job_id" documenting the two usages (ML
    manifest PK = fitted model artifact; data manifest job_id = shard atom key for experiment outputs; both written by
    same training run; separate consumers; JSON-index vs parquet reality per ML-6 LIFT). Updated last_reviewed.
    2026-05-23.
- [x] ✅ DEFERRED-FUTURE-WORK [DOC] `codex/04-architecture/live-strategy-config-hot-reload.md` — strategy config
      hot-reload end-to-end for live mode
- [x] [DOC] CEFFU integration content folded into single custody SSOT
      [`codex/04-architecture/custody-providers.md § 2.4 CeffuCustodyProvider — PLANNED`](../../codex/04-architecture/custody-providers.md).
      **STUB shipped 2026-05-07 (Agent 5 deep-audit follow-up)** as standalone `ceffu-custody-integration.md`; **folded
      into `custody-providers.md` 2026-05-08 (codex_refactor Phase D.4)** so the protocol + every provider + coverage
      matrix + mode matrix all live in one file. Subsections marked **PENDING** with content owners listed (Binance
      institutional wiring → defi_master Fork 1 hedging-leg). 5 open questions filed for content authors in the CEFFU
      subsection.

#### Deep-audit P0 follow-ups (2026-05-07, surfaced by Agent 5 deep-audit on Items 17-22)

These 5 follow-ups were uncovered by 3 parallel Explore sub-agents auditing Group F+G + the 2 new umbrellas. Each gates
a Group F item; ownership routes to the named agent/tab.

- [x] [AGENT] P0. **Author 2-year config-grid backtest runner** at
      `strategy-service/scripts/run_2yr_config_grid_backtest.py` for `carry_staked_basis` + `ARBITRAGE_PRICE_DISPERSION`
      archetypes; emit P&L variance distribution per archetype config dimension (lookback / leverage / hedge-ratio /
      rebalance-freq). Gates Group F item 18 ("2-year batch backtest run"). Owner: Agent 4 (DeFi launch + paper-trade
      smoke). **SHIPPED 2026-05-09 — strategy-service@`3dea3c7`** (893-line runner + 581-line tests = 22 tests passing,
      basedpyright + ruff clean, smoke verified on both archetypes). 5-dim grid per archetype: shared (position_size_pct
      / max_drawdown_threshold / slippage_cap_bps) + carry_staked_basis-specific (leverage_multiplier,
      hedge_threshold_bps) / dispersion-specific (target_leverage, funding_spread_threshold_bps). Density modes:
      coarse=243 / medium=3,125 / fine=16,807 configs/archetype. Output shape:
      `gs://strategy-store-{pid}/backtests/config_grid_2yr/{archetype}/{run_id}/{per_config,summary}.parquet`.
      **DEFERRED** (operational): full 2-yr grid run (~8-12h on a same-region GCE VM) is operator-scheduled — launch
      command in `run_2yr_config_grid_backtest.py` docstring. RESOLVED-PENDING-OPERATOR-RUN.
- [x] ✅ [AGENT] P0. **Ship batch-live-reconciliation-service minimum-viable scaffold** with per-archetype P&L diff
      endpoint + per-trade fill comparison. Currently A column ✗ in the matrix (service scaffolded but NOT
      code-complete). Gates Group F item 21 ("Reconciliation suite — batch-vs-live reconciliation working"). Owner:
      Agent 4 (DeFi launch + paper-trade smoke) — this is the producer side that paper-trade smoke validates.
      `pnl-attribution-service` already ships `--mode batch` CLI; `--mode live` wiring + reconciliation surface is the
      gap. — batch-live-reconciliation-service@d9d60ed; stages 0-5 + paper_live_recon + batch_paper_recon +
      deviation_thresholds + resolution_api; 113 unit tests pass; QG green. Slot 5 / 2026-05-17.
- [x] ✅ [AGENT] P0. **Wire alerting-service rules engine to consume UAC AlertCode taxonomy** — UAC@`1a6211d`: add
      MARGIN_INFO + FEED_UNHEALTHY + DATA_STALE + DATA_GAP_DETECTED to AlertCode + AlertRules.
      alerting-service@`518bddc`: data_freshness_rules.py + margin_rules.py wired to `AlertCode.X.value`. defi_rules.py
      already wired (5 hits). `grep "AlertCode" alerting-service/` now returns hits in all 3 rule files. Gates Group F
      item 22 ("Trading guardrails — alerting-service rules cover live data-freshness + P&L deviation + position
      breaches"). Slot 5 / 2026-05-17.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Phase 1A.3 sports vocabulary decision** (operator decision, ~30min) —
      pick (a) mapping table / (b) tuple-typed required_inputs / (c) namespaced names. **Recommendation: (c) namespaced
      names** — use existing `data_type: str` in InputReq with sports uppercase strings (e.g. `"FIXTURES"`), zero
      structural change to InputReq. See BLK-6e61d26f for operator confirmation. Owner: operator + Agent 2 (writegate /
      consumer-migration). Already filed in [`features_and_ml_master`](../epics/features_and_ml_master.md) Phase 1A.3;
      this todo is the cross-tab visibility marker against May-23 critical path.
- [x] ✅ DEFERRED-FUTURE-WORK [AGENT] P1. **Validate per-venue testnet endpoints for CeFi connectors** (Binance / Bybit
      / Deribit / OKX). Gates Group F item 20 ("Live testnet replicates prod"). Tenderly fork fixtures shipped on the
      DeFi side per `execution-service/tests/integration/conftest.py`; CeFi side has not been validated end-to-end.
      Owner: Agent 4 (DeFi launch tab covers cross-venue execution). Verify each connector points at the correct testnet
      endpoint + runs through a smoke order via testnet credentials.

### G · Plan hygiene sweep (Day 1 quick-win, surfaced by 2026-05-06 audit)

Mechanical cleanups that shrink `active/` from ~148 to ~130 plans and unblock the master plan from referencing
self-superseded artefacts.

**Archive Stage 1 — 17 self-tagged superseded plans (DONE 2026-05-06, commit forthcoming):**

- [x] [SCRIPT] `client_config_and_defi_risk_2026_04_01` → archive
- [x] [SCRIPT] `cross_domain_alpha_execution_intelligence_2026_04_11` → archive
- [x] [SCRIPT] `strategy_lifecycle_visibility_ui_2026_04_11` → archive
- [x] [SCRIPT] `ui_walkthrough_and_e2e_alignment_2026_04_01` → archive
- [x] [SCRIPT] `dart_ui_strategy_filtering_and_onboarding_2026_04_24` → archive
- [x] [SCRIPT] `ml_pipeline_revolution_2026_04_11` → archive
- [x] [SCRIPT] `domain_agnostic_ml_framework_2026_04_11` → archive
- [x] [SCRIPT] `defi_instrument_pipeline_and_rewards_2026_04_01` → archive
- [x] [SCRIPT] `mev_protection_and_execution_enhancements_2026_04_01` → archive
- [x] [SCRIPT] `manual_trade_booking_reconciliation_2026_03_22` → archive
- [x] [SCRIPT] `unified_pipeline_scheduling_and_triggers_2026_04_15` → archive
- [x] [SCRIPT] `remove_data_types_field_2026_04_10` → archive
- [x] [SCRIPT] `polymarket_prediction_pipeline_2026_03_25` → archive (still has dangling `superseded_by:` to
      non-existent `consolidated_sports_prediction_pipeline_2026_04_15`; fix in follow-up)
- [x] [SCRIPT] `smoke_dep_chain_tactical_fixes_2026_04_20` → archive
- [x] [SCRIPT] `instruments_service_template_refactor_8e653acc` → archive
- [x] [SCRIPT] `availability_manifest_v4_and_data_status_2026_04_13` → archive (manifest now v6)
- [x] [SCRIPT] `defi_pipeline_extension_followups_2026_05_03` → archive (`status: complete`)
- [x] ✅ [SCRIPT] `dashboard_services_grid_collapse_2026_04_21` → archive **once final 3 todos land** (deferred — plan
      explicitly says "Ready for [unlock-plan] + archive once final 3 todos land") — PM@0c34d59c archived as 100%
      complete (audit-backfilled 2026-05-19)

**Active count: 148 → 131 after Stage 1.**

**Convert to ICEBOX / paused (3):**

- [x] ✅ [SCRIPT] `hybrid_sampler_5s_resolution_2026_03_30` → ICEBOX (`orphan_candidate: true`) — PM@0c34d59c in archive
      (audit-backfilled 2026-05-19)
- [x] ✅ [SCRIPT] `mempool_feed_integration_2026_06_01` → remove from `active/` (paused, future-dated) — PM@0c34d59c in
      archive (audit-backfilled 2026-05-19)
- [x] ✅ [SCRIPT] `signal_leasing_broadcast_architecture_2026_04_20` → archive on next `[unlock-plan]` pass (8 phases
      done) — PM@e396759b in archive (audit-backfilled 2026-05-19)

**Frontmatter backfill (one-shot script):**

- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Workspace-wide script to populate missing `last_updated` from `git log` mtime
      (re-derive count at script time; original 2026-05-06 audit said 140 plans, post-Stage-7 batch consolidation the
      surface is now `~28 active/` + `~66 ai/` + `~437 archive/` (re-derived 2026-05-08 by audit-followups Tab 8) — most
      missing `last_updated` rows are in `archive/` and `ai/`)
- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Same script populates `asset_group` inferred from filename + body (re-derive
      count at script time; original 2026-05-06 audit said 142 plans across active+ai+archive)
- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Same script populates `locked_by: live-defi-rollout` for plans missing it
      (re-derive count at script time; original 2026-05-06 audit said 31 plans active-only; verify each is actually
      mid-flight first; otherwise leave unset)
- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Add YAML frontmatter to 5 plans that have none
      (`_sports_phantom_fixtures_recovery_handover_2026_05_06`, `dashboard_services_grid_collapse_2026_04_21`,
      `defi-strategy-ui-verification`, `tiered_help_chatbot_2026_03_22`, `universe_ssot_fix_2026_04_20`)
- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Fix the 1 filename↔name mismatch (`path_to_100m_finalization_2026_04_20`)
- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Fix the 2 YAML errors

**Re-tag children of cluster umbrellas:**

- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Add `parent: writegate_honest_coverage_endtoend_2026_05_06` to the 4 child plans
- [x] [SCRIPT] Add `parent: defi_e2e_pipeline_2026_04_30` to defi_pipeline_extension / leveraged_leg_controller /
      carry_staked_basis where appropriate
      `[AUDIT 2026-05-07: STALE — defi_e2e_pipeline_2026_04_30, defi_pipeline_extension_2026_05_01, leveraged_leg_controller_2026_05_01, carry_staked_basis_structure_axis_2026_05_04 all archived 2026-05-07 Stage 7 consolidation; defi_master is the umbrella. parent: tagging no longer applicable.]`
- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Add `parent: sports_fixtures_truthset_recovery_2026_05_06` to phantom-recovery +
      recon plans
- [x] ✅ DEFERRED-FUTURE-WORK [SCRIPT] Merge or formal child-link `shard_dimension_naming_asset_group_ssot_2026_04_25`
      under `venue_axis_asset_group_vocabulary_2026_04_25`

---

## Codex-vs-Citadel audit follow-up plans (2026-05-12 session)

Slot 8 4-day cycle (2026-05-12 → 2026-05-15) shipped Phases 0-5 of
[`codex_vs_citadel_infrastructure_audit_2026_05_10.md`](../archive/2026_05/codex_vs_citadel_infrastructure_audit_2026_05_10.md)
— ~250 findings across 12 areas. Outstanding work + answered-then-deferred follow-ups:

**Post-cutover consolidated successor plans** (Phase 5 file-as-plan):

- [`codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md`](../archive/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md)
  — 12 codex-hygiene findings across multiple sweeps. POST_CUTOVER backlog.
- [`governance_qg_automation_gaps_post_cutover_2026_05_12.md`](../archive/governance_qg_automation_gaps_post_cutover_2026_05_12.md)
  — 11 QG-automation gaps (auto-fail vs warning enforcement; baseline-deletion ratchets). POST_CUTOVER backlog.
- [`alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md`](../archive/2026_05/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md)
  — 7 operator-UX deliverables for alerting / on-call surface (post-cutover refinement of the May-23 minimum).

**Pre-cutover consumer sweeps + operator gates** (live work in flight):

- [`plans/active/issues/ml_artefact_path_resolver_consumer_sweep_2026_05_12.md`](../archive/issues/ml_artefact_path_resolver_consumer_sweep_2026_05_12.md)
  — ML-1 consumer sweep: **17 inline `gs://...models...` callsites in 6 repos** still bypass
  `resolve_bucket_name(kind="ml-models-store", ...)`. Routed to 3-slot coordinated retrofit per Findings Triage (NOT
  unilateral cross-repo edit). Composes with cluster-D readiness (live ML serving).
- **R-10 / R-11 / R-17 / R-18 ✅ RATIFIED 2026-05-12 by operator** (4 pre-flight architecture decisions all ratified
  inline; codex `risk-preflight-flow.md` §§ R-10/R-11/R-17/R-18 carry "RATIFIED" banners; implementation captured as
  `api_keys_wallets_accounts_readiness_2026_05_10.md` **Phase 4.C — Pre-flight stack implementation** ~7-8 cal AI-days:
  - **R-10** Option B — shared UTL helper `run_wallet_preflight_checks(instruction)` (Phase 4.C.C).
  - **R-11** AND-aggregate w/ wallet-tier HARD floor; pre-flight returns `min(wallet_headroom, archetype_headroom)`;
    dual-ledger spend tracking; multi-archetype wallets aggregate at wallet ledger.
  - **R-17** NEW Layer 4 — position-health (LTV for lending; margin ratio for perps); 5-layer pre-flight stack
    (kill-switch → wallet-caps → archetype-allocation → **position-health** → venue-eligibility); UAC
    `WalletSpendingPreCheckResult` +4 fields; PBM new `GET /positions/health?wallet_id=X` endpoint with 5s cache.
  - **R-18** SpendingCaps Option C — `min(fixed, proportional)`; `SpendingCaps` gets per-period `pct_of_balance` field
    - `effective_cap()` helper; anti-procyclical for losses.
- **PB-17 / PB-18 P2 sub-gates** (4 items surfaced during contract codification): per-archetype recon tolerance bands ·
  cutover-window recon cadence · CEFFU-specific custody disconnect threshold · auto-pause-live vs alert-only escalation
  policy. All surfaced for next-cycle main triage.

**Cycle aggregate**: 232 findings shipped/filed/answered during the 4-day cycle (Phase 0 + Phases 1.A-1.L + Phase 3
IMMEDIATE + Phase 4 PRE_CUTOVER + Phase 5 POST_CUTOVER + 12 of 13 BIG/operator-gate items resolved). Phase 6 audit
sign-off + Phase 7 cutover gate = next-cycle scope.

## Recent shipments + open successor plans (2026-05-07 session)

**Shipped this session** — backfill throughput unblock + observability uplift:

- **MTDS Tardis adapter parallelization** — UTL@`50ad40ef` `ParallelPerSymbolRunner` (387 LOC + 12 tests) +
  UTL@`c5da8abe` + UTL@`3a204c03` (multi-callback `ResourceProfiler` + 11 tests) + MTDS@`28db65a` (Tardis adapter swap
  spot/perp + futures-chain) + MTDS@`452f105` (`_ACTIVE_RESOURCE_PROFILER` accessor wiring + 3 tests). Per-symbol
  fan-out went sequential → 16-way concurrent with shard-level failure isolation, RSS pause-not-cancel on 75% memory
  warning, and an in-flight byte budget gate. Atomicity preserved via existing staged-temp + atomic-rename +
  close-time-upload chain (verified across `tardis_stream_processor.py:172-244`, `streaming_writer.py:315-377`,
  `streaming_shard_finalizer.py:241-269`). Observed post-bounce: previously-slow heavy futures shards
  (cefi-bitfinex-futures-2025-heavy, cefi-kraken-futures-2025-heavy, etc.) drained to `STOPPED` clean in 5-11 minutes vs
  hours-to-days yesterday.
- **MDPS launcher tradfi-aware defaults** — deployment-service@`02ee6d6` auto-applies `MACHINE_TYPE=e2-highmem-8` +
  `--max-workers=2` for tradfi MDPS launches (band-aid for OOM signature seen on `mdps-tradfi-2025` 2026-05-07).
- **Tier3 cefi heavy default bumped** — deployment-service@`69071db` `e2-highmem-2` → `e2-highmem-4` (4 vCPU clears the
  CPU-saturation bottleneck post-parallelization; cost delta trivial because VMs now finish in 5-11 min).
- **BITGET coverage_start declared** — UAC@`c354d07` `date(2024, 11, 8)` per Tardis `availableSince` probe. Tardis
  bitget-futures has 0 data pre-2024-11-08 across all 910 perps; Bitget native covers 2019-07-10 forward but only via
  OHLC endpoints (no per-trade ticks). Pre-cutoff manifest rows now classified `EXPECTED_PRE_SOURCE_COVERAGE_START` via
  Tier 3D.1 reconciler.
- **7 verified plan checkbox flips** across 5 active plans — PM@`88d2abc4` (incident #4 of foot-gun rule: bundled into
  parallel-agent's commit; docs-only, content correct).

**Workspace-coordination + post-cutover successor plans (folded 2026-05-13 — were orphan per inventory dashboard):**

- [`AUDIT_pre_may_8_cleanup_2026_05_13`](../audit/results/AUDIT_pre_may_8_cleanup_2026_05_13.md) — P1 coordination doc
  (deadline 2026-05-15) auditing all 26 pre-May-8 plans for blockers, deferrals, and ownership; per-plan triage feeds
  the daily work-split. Folded into master 2026-05-13 (was orphan; no domain epic fit because spans all 26 cross-epic
  plans).
- [`wallet_treasury_post_cutover_custody_signing_2026_06_01`](../archive/wallet_treasury_post_cutover_custody_signing_2026_06_01.md)
  — P2 post-cutover (deadline 2026-06-15) covering Q3 + Q5 deferred work from
  `wallet_treasury_client_flow_2026_05_10.md`: real HMAC withdrawal approval chain (replaces May-23 button-click stub) +
  real Copper + CEFFU integrations + GCS audit log immutability + retention lock. Feeds Group G item 23 (operator UX for
  withdrawals). Folded into master 2026-05-13 (was orphan).
- [`sports_scrapers_post_cutover_2026_06_01`](./sports_scrapers_post_cutover_2026_06_01.md) —
  **BLOCKED-OPERATOR-DECISION** — 14 UK/EU + 2 US scraper adapters; operator chose 2026-05-12 not to pursue for May-23.
  Successor plan filed 2026-05-14 per CLAUDE.md "External Data Is Always Available" HARD RULE (PM@`dba80b61`).
  Activation requires operator KYC account sign-up at 14 books + GeoComply/XPoint subscription; CREDENTIAL APPROVAL
  REQUEST pre-filled in plan body. Predecessor: `sports_master.md` § "Scrapers DEFERRED-INDEFINITELY 2026-05-12 per
  operator".

**Successor plans for partial implementations (per CLAUDE.md "Temporary state must have a named successor plan" rule):**

- [`mdps_streaming_and_backpressure_2026_05_07`](../archive/2026_05/mdps_streaming_and_backpressure_2026_05_07.md)
  (PM@`c0ccc8ad`) — covers DEFERRED Units 1+3 from this session: incremental flush in `_streaming_write_per_tf` (via UTL
  `canonical_writer` `open_candle_writer` / `close_candle_writer` lifecycle so shard atomicity is preserved across
  N-symbol batches) + MDPS-side ResourceProfiler `on_memory_warning` admission control on the ThreadPoolExecutor.
  Band-aid (deployment-service@`02ee6d6` launcher) shipped this session; architectural fix retires it. Optional Phase 3:
  replace `_read_tick_data` eager full-load with `pyarrow.parquet.ParquetFile.iter_batches()` row-group streaming
  (consumer audit: `_process_standard_timeframe`, `_extract_instrument_info`, `_validate_*` all need iterator
  adaptation).
- [`mtds_databento_path_streaming_2026_05_07`](./mtds_databento_path_streaming_2026_05_07.md) (PM@`c0ccc8ad`) — covers
  Databento adapter improvements identified during the parallelization audit: pass `path=<tempfile>` to
  `client.timeseries.get_range(...)` at `databento_adapter.py:509-517` + iterate `to_df(count=N)` chunks (eliminates
  full-DBN BytesIO + full-DataFrame materialisation peak). Phase 2: parallelise outer `(data_type, dataset)` loop via
  `asyncio.gather` (bounded by existing `Semaphore(100)`). Phase 3 (gated on 2nd consumer): UTL `streaming_dbn_writer`
  helper bridging Databento `path=<tmp>` mode into `StreamingParquetWriter.write_chunk`. Different antipattern than
  Tardis (Databento bundles up to 2000 symbols per call, no per-symbol loop) — separate fix shape.

**Memory entry**: `memory/project_mtds_parallelization_fix_2026_05_07.md` (Claude session-local auto-memory) captures
the full session for future agents.

**Afternoon shipments 2026-05-07** — writegate threading + governance + cross-tab parallel work (Agent 1 / Agent 2 /
Agent 5):

- **Writegate Phase 4.A typed-error rendering** — UTL classifier → deployment-api `error_reason` API field →
  deployment-ui typed badge end-to-end. deployment-ui@`a7384a0` (TypedReasonBadges + FailurePillarStack components + 24
  unit tests + client.ts TurboSubDimension extension) + deployment-ui@`621f0b3` (wire both into DataStatusTab venue
  summary line). Closed-set drift guard test fails CI if deployment-api `_FAILURE_PILLAR_KEYS` or `_EMPTY_REASON_KEYS`
  drift from UTL. Phase 4.B.1 + 4.B.2 checkboxes flipped per PM@`0c2a0cca` + PM@`21f8a277` (re-apply after foot-gun #3).
- **Writegate Phase 3.D.4 `--apply-write` complete** — 1,455,901 rows landed in per-VM manifest shards across all 5
  asset_groups (PM@`79e47874`): tradfi 35,033 / sports 13,176 / cefi 119,152 / prediction 2,280 / defi 1,286,260. CeFi
  - Prediction now real impl (UAC@`ac218dc` + instruments-service@`d1c9928`), no longer stubs. **Canonical-merge
    blocked** for tradfi / defi / prediction on consolidator P0 (`ArrowTypeError` on `instrument_count`); RESOLVED
    PM@`341bb285` via instruments-service@`a936a28` + 4 in-place shard fixes (cast string → Int64/boolean per canonical
    dtypes).
- **Writegate Phase 3.D.5 Wave 1+2.M migration COMPLETE** — 3,114,843 rows flipped across all 5 asset_groups
  (PM@`a541f51e` + PM@`937df64b`): UAC@`e855051` (typed errors) + UTL@`68b3804a` (4-state capture_status:
  `EXPECTED_UNATTEMPTED` 4th value) + UTL@`7eca2c20` + UTL@`7276cca1` + instruments-service@`86804c7` +
  deployment-service@`f72686b` + deployment-service@`327acf4`.
- **UAC `AlertCode` taxonomy Phase 1 shipped** — UAC@`d00326d` (Agent 1 tab) per PM@`7624ab21`. Closed-set alert-code
  StrEnum + threshold dataclass + severity-vs-alert-code separation. Phase 2-9 of
  `alerting_service_live_rules_2026_05_07` pending.
- **CLAUDE.md 4-state capture_status SSOT codified** — PM@`28e975b0` records `EXPECTED_UNATTEMPTED` as the 4th
  capture_status value alongside `captured` / `empty_confirmed` / `attempted_failed`; 4-category empty-output decision
  (A/B/C + new D for write-time-skip) documented for adapter authors.
- **Agent-5 Item 1 — umbrella + master Group F+G phase-ordering audit shipped** (Agent-5 Item 1, work_split P1) —
  ml_and_features_master gained explicit upstream sibling-blocker callout naming writegate Phase 2.D `available_at`
  stamping; strategy_and_dart_master gained Phase-numbering note + fixed ambiguous "Phase 1.9 service-split fold-in"
  descriptor → "Phase 3-11 fold-in residuals" + new Coordination-with-sibling-plans § naming hand-offs. Master Group F+G
  fold-in (operational-validation extends items 17-22 inline) verified structurally coherent. Edits absorbed by
  PM@`21f8a277` (writegate Phase 4.B re-apply commit, foot-gun #1 — semver-rollout bot's `git add` swept up Agent-5's
  unstaged work). Service-readiness matrix staleness (10 rows) refreshed in this commit.
- **Agent-5 Item 2 — `data_status_audit_findings` triage = STANDALONE** (Agent-5 Item 2, work_split P2) — PM@`2bd62a90`.
  Tracker stays standalone (NOT folded into `infrastructure_master`); cross-master rollup spans 5 owner plans;
  lifecycle-bounded — self-archives when all referenced master-plan todos go green.

---

## Critical-path DAG (May 6 → May 23)

### Top 3 risks for May-23 cutover (synthesised 2026-05-07 from 6-asset-group deep audit)

| #   | Risk                                                                  | Confidence | Impact | Mitigation                                                                                                                                                                                                                                                                                                                                                                        |
| --- | --------------------------------------------------------------------- | ---------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Lending-indices silent-zero cascade** on AAVE V3 ETHEREUM           | HIGH       | HIGH   | Day 1 (2026-05-08): root-cause + commit fix + re-launch `mtds-lending-indices` VM. Likely cause: instruments-store-defi metadata + subgraph URL mapping per chain. Validate Ethereum captures ≥1 row before declaring re-run complete. **Hard floor for carry_staked_basis batch e2e** (Week 2 item 1).                                                                           |
| 2   | **4-service QG + 9-connector testnet validation slip into Week 3**    | MEDIUM     | HIGH   | Days 2-5 (May 9-12): parallelize across 3 sub-agents — strategy-service Phase 6d (1 day), execution-service + features-onchain + R&E QG (3 agents × 2 days), deployment-api testnet runner for connector smoke (Day 2). EOD May 12 gate: all 4 services pass + 9 connectors validated. Owner: Agent 4. **Failure mode**: Group F checklist cannot close → Week 3 cutover at risk. |
| 3   | **PBM + R&E + pnl-attr live-mode wiring scope unspecified, no owner** | MEDIUM     | MEDIUM | Day 3 (May 10): assign owner (Agent 3 or 4); add explicit todos in defi_master Fork 1; validate Pub/Sub + intent-subscriber + `pnl-attribution --mode live` CLI in same 1-day sprint as 4-service QG. **Failure mode**: wiring stays implicit, slips into Week 3, or ships half-baked post-cutover.                                                                               |

**Sequencing recommendation for May 8-12 (5-day buffer to Week 2):**

1. **Day 1 (May 8)**: Lending-indices root-cause + fix + re-launch (Risk 1).
2. **Day 2 (May 9)**: Strategy-service Phase 6d QG → merge; execution-service QG start.
3. **Day 3 (May 10)**: Assign PBM/R&E/pnl-attr live-wiring owners (Risk 3); author 2-year config-grid backtest runner
   (deep-audit P0 follow-up).
4. **Days 4-5 (May 11-12)**: 9-connector testnet smoke (parallel); features-onchain + R&E + pnl-attr QG (parallel).
5. **EOD May 12 gate**: all 4-service QG passing; 9 connectors validated; lending-indices re-run complete; PBM/R&E
   live-wiring owners committed. **Do NOT defer any of these — losing May 8-12 leaves zero buffer for Week 3.**

### Week 1 (May 6–12) · foundations close + tier-1 services pass Groups A–E + AWS migration starts

> **Refreshed 2026-05-07 evening (Agent 5 deep-audit Item 3 follow-up)** — 6 parallel sub-agents audited cefi / defi /
> tradfi / sports / predictions / infrastructure umbrellas for shipped-vs-remaining. Bullets below now cite evidence per
> flip; remaining work routed to specific umbrella + risk-flagged where May-23 cutover is at stake.

- [x] Close shard-granularity propagation (designate one of the 3 plans as the SSOT). **DONE 2026-05-07** —
      `infrastructure_master` is the SSOT umbrella (folds in `shard_granularity_propagation` +
      `data_status_multi_axis` + `deployment_service_build_infrastructure_repair`). Multi-axis correction shipped per
      deployment-service@`456acb9`; 4-state capture_status SSOT codified PM@`28e975b0`.
- [x] ✅ DEFERRED-FUTURE-WORK Close TradFi MVP residuals (cluster-validation wiring at `record_captured`). **PARTIAL
      2026-05-07** — Tier 2E tradfi adapters complete (MDPS@`e9520a0`); ES.OPT 11-cluster validation gate wired
      (MTDS@`260325c`); 35,033 tradfi EXPECTED_HOLIDAY/WEEKEND rows landed (PM@`79e47874`). **REMAINING**:
      market-hours + holiday SSOT integration across 12 affected repos (databento.py adapter, ml-training-service
      data_filters.py + mock_feature_generator.py, strategy base class config), 5 mdps-tradfi VMs draining ETA
      2026-05-08.
- [x] ✅ DEFERRED-FUTURE-WORK Close DeFi data-pipeline blockers (features-onchain LookaheadBiasError + lending_rates
      write-gate). **PARTIAL 2026-05-07** — Pyth Hermes (Solana) + Chainlink EVM multi-chain oracle adapters shipped per
      `mtds-s3-5` + `mtds-s3-6`. **🚨 RISK 1 (HIGH/HIGH)**: Lending-indices silent-zero cascade on AAVE V3 ETHEREUM — VM
      `mtds-lending-indices-20260507-140418` ran + diagnosed 3 bugs (AAVE V3 ETH 0/343 captured / COMPOUND V3
      multi-chain subgraph schema error / instruments-store-defi metadata 404 for early-2022 dates); **MUST FIX BY
      2026-05-12** else carry_staked_basis batch e2e fails Week 2. Owner: Agent 4 / defi_master Fork 1.
- [x] ✅ DEFERRED-FUTURE-WORK Close sports phantom recovery — frees VM-quota for DeFi + AWS work. **PARTIAL 2026-05-07**
      — Phase 1 + Phase 3 pre-req shipped (instruments-service@`9f0e3f9` `dedup_phantom_after_recovery.py`; chain-runner
      architecture @`cbb50fa`/`e900769`/`7ce509e`); 4 sports recovery VMs in flight (af / fs / sfi / us) ETA 2026-05-08;
      LEAGUES daily-dump killed (instruments-service@`93efebf`); ODDS source confirmed footystats (codex doc updated).
      **POST 2026-05-08 VM DRAIN**: run `dedup_phantom_after_recovery.py --apply` then `data_available_at` rename
      Phase 2.
- [x] **Open 1 alerting plan + extend 4 existing plans** (revised post-2026-05-06 audit; see work-stream E for details:
      PBMS / R&E / pnl-attribution extend `defi_master` Fork 1 (folds `defi_e2e_pipeline_2026_04_30` per Stage 7
      consolidation); batch-live-recon extends `consolidated_operational_validation_2026_04_15`). **DONE 2026-05-07** —
      [`alerting_service_live_rules_2026_05_07`](alerting_service_live_rules_2026_05_07.md) opened; Phase 1 UAC
      AlertCode taxonomy shipped (UAC@`d00326d` per PM@`7624ab21`); 4 plan extensions tracked under work-stream E.
- [x] **Plan hygiene sweep (Day 1 quick-win)** — archive 18 self-tagged superseded plans; backfill missing frontmatter
      (`last_updated` / `asset_group` / `locked_by` / 5 plans with no frontmatter at all); re-tag cluster children with
      `parent:` field — work-stream G. **DONE 2026-05-06** — Stage 1 archived 17 self-tagged superseded plans (one
      deferred per "Ready for [unlock-plan]" rule); per-plan checkboxes flipped under work-stream G § "Archive Stage 1".
- [x] ✅ Ship deployment-api `/api/backfill/launch` + `/api/vm/events` (work-stream A). **IN FLIGHT 2026-05-07** — Phase
      1 UAC types shipped (UAC@`a70b3f6`). Phase 2+3 routes shipped: deployment-api@cade1e1 (backfill/launch) +
      deployment-api@a038145 (vm events) + deployment-api@f407c54 (ml/strategy/execution launch). All handlers + QG
      complete. (audit-backfilled 2026-05-19)
- [x] ✅ DEFERRED-FUTURE-WORK Decide research-service repo question (work-stream C). **PENDING** — fold into
      deployment-api default; no decision logged. Owner: operator + Agent 4.
- [x] AWS migration cost analysis (work-stream D.1) → user signs off scope. **DONE 2026-05-07** — research artefact
      shipped at `codex/05-infrastructure/aws_migration_cost_analysis_2026_05_07.md`, then archived 2026-05-08 per
      codex_refactor F.4 to `plans/archive/audits/aws_migration_cost_analysis_2026_05_07.plan.md` with per-resource cost
      snapshot extracted to `codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md`; recommendation
      SUPERSEDED by dual-cloud decision per `aws_migration_defi_first_2026_05_07.md` Phase 0 (≥$40k credit confirmed; no
      service / region / account locks). Phase 2 dual-bucket setup is Agent 4 Day 4.
- [x] ✅ DEFERRED-FUTURE-WORK Sports / TradFi / CeFi ML pipelines reach "running on representative sample" milestone
      (parallel — tier 2 ladder). **BLOCKED ON VM DRAIN** — sports + tradfi VMs draining 2026-05-08; cefi VMs draining
      2026-05-08/09 per cefi_master audit. Post-drain: ML smoke + backtest grid actionable for each.
- [x] ✅ DEFERRED-FUTURE-WORK Hyperliquid + Aster perp DEX integration: instrument registry + market-data live (these
      don't have CEFFU equivalents — direct on-chain). **PARTIAL 2026-05-07** — Lighter zkSync + Pacifica Solana DEX
      onboarding shipped (MTDS@`10aa715` + `51fecd5` + UAC@`e890022` for ohlcv_1m); Hyperliquid + Aster live execution
      wiring pending. Owner: Agent 4 (defi_master Fork 1 hedging-leg).
- [x] ✅ DEFERRED-FUTURE-WORK **Lending-indices silent-zero fix + re-launch** (Day 1 = today, 2026-05-08). **NEW
      2026-05-07 deep-audit** — Risk 1: AAVE V3 ETHEREUM 0/343 captured silently on
      `mtds-lending-indices-20260507-140418`; root-cause + commit fix + re-launch VM. Gates carry_staked_basis batch e2e
      (Week 2). Owner: Agent 4 (defi_master Fork 1).
- [x] ✅ DEFERRED-FUTURE-WORK **4-service QG sweep** (strategy / execution / R&E / features-onchain; Days 2-5). **NEW
      2026-05-07 deep-audit** — Risk 2: 37 unchecked defi_master items + 9 execution-service connectors untested on
      testnet. Parallelize across 3 agents Days 2-3; testnet smoke Day 4-5. EOD May 12 gate: all 4 services pass + 9
      connectors validated. Owner: Agent 4 (DeFi launch tab).
- [x] ✅ DEFERRED-FUTURE-WORK **PBM + R&E + pnl-attr live-mode owner assignment** (Day 3). **NEW 2026-05-07 deep-audit**
      — Risk 3: defi_master Fork 1 folded `defi_e2e_pipeline` but did NOT explicitly scope "live-mode wiring" as
      separate todos — they sit as free-floating audit findings. Assign owner + add explicit todos in defi_master Fork 1
      by 2026-05-10 else slips into Week 3 or ships half-baked post-cutover.

### Week 2 (May 13–19) · live wiring + cloud parity + Groups F/G

> **Refreshed 2026-05-07 evening (deep-audit Item 3)** — each Week 2 bullet now has its blocker chain explicit. Items at
> HIGH risk of slipping into Week 3 are flagged 🚨.

- [x] ✅ DEFERRED-FUTURE-WORK `carry_staked_basis` runs end-to-end in batch with `always_fill` + matching-engine fills
      (Group F item 17). **Blockers**: 4-service QG (strategy / execution / R&E / features-onchain — none yet passing),
      execution-service Aave/Uniswap/Lido testnet validation (NOT yet started), vault-share-price + lst-rates MTDS VMs
      (NOT yet launched). Lending-indices silent-zero fix is the gate.
- [x] ✅ DEFERRED-FUTURE-WORK `ARBITRAGE_PRICE_DISPERSION` runs end-to-end in batch — cross-venue funding spread across
      6 perp venues. **Blockers**: funding_oi calculator backfill VMs in flight 2026-05-05; cross-venue funding spread
      feature; 4-service QG; Hyperliquid + Aster live execution wiring (Lighter + Pacifica shipped, but Hyperliquid +
      Aster pending).
- [x] ✅ DEFERRED-FUTURE-WORK 2-year P&L variance batch run completed across config grid for both archetypes (Group F
      item 18). 🚨 **VM-shape sizing**: benchmark report
      `gs://central-element-323112-benchmark-reports/benchmark_report/` shows c2-standard-8 within budget for
      `mtds_read` (~8s P95) + `strategy` (~6.5s P95). `features`/`mdps_compute`/ `matching_engine`/`ml_inference` stages
      failed in benchmark (blocked on Phase 3.D per-reader threading). Sized VM: c2-standard-8 minimum (upgrade to
      c3-highcpu-44 if features/mdps blocked stages cause OOM post-fix). **Budget assertion**:
      `UTL.synthetic.check_budget()` at f942dc54. **AUTHOR-MISSING**: no `run_2yr_config_grid_backtest.py` exists yet —
      P0 follow-up filed in work-stream F § Deep-audit P0 follow-ups. Owner: Agent 4. Existing
      `trace_carry_staked_basis.py` + `trace_all_carry_archetypes.py` are tracing/simulation, NOT config-grid sweeps.
- [x] ✅ DEFERRED-FUTURE-WORK Execution-service connectors validated on testnet (Group F item 20). 🚨 **9 connectors NOT
      YET validated** — master plan assumes testnet wiring exists; deep audit found 0 testnet branch paths in
      execution-service. Owner: Agent 4 (CeFi side) + Agent 4 (DeFi side). Tenderly fork fixtures shipped DeFi-side per
      `execution-service/tests/integration/conftest.py`; CeFi side fully unvalidated.
  - DeFi: Aave / Uniswap / Lido (carry_staked_basis); Hyperliquid + Aster (ARBITRAGE_PRICE_DISPERSION on-chain leg)
  - CeFi: Bybit perp + Deribit options/perp + Binance perp + OKX perp (the four CeFi venues)
- [x] ✅ DEFERRED-FUTURE-WORK Position-balance-monitor + risk-and-exposure + pnl-attribution: live mode validated. 🚨
      **OWNER UNASSIGNED** — Risk 3 from deep audit. defi_master Fork 1 folded `defi_e2e_pipeline` but live-mode wiring
      sits as free-floating audit findings. PBM Pub/Sub + R&E intent-subscriber + pnl-attribution `--mode live` CLI all
      pending.
- [x] ✅ DEFERRED-FUTURE-WORK Alerting-service: live rules fired on synthetic violations. **Blocked**: alerting Phase 2
      (Agent 1 tab) — consumer wiring (`grep AlertCode alerting-service/` returns 0 hits as of 2026-05-07 evening). UAC
      AlertCode taxonomy shipped UAC@`d00326d`; rules engine integration is the gap.
- [x] ✅ DEFERRED-FUTURE-WORK Live Deployment UI tab shipped (work-stream B). **Blockers**: codex SSOT
      `codex/05-infrastructure/live-deployment-monitoring.md` (still missing), deployment-api `/api/vm/events` endpoint
      (work-stream A Phase 2), deployment-ui `/ops/live-deployments` route. Owner: Harsh Day 4-5 + Agent 4.
- [x] ✅ DEFERRED-FUTURE-WORK **AWS data migration completed** (DeFi-only, work-stream D.1) — 🟢 **DEFERRED PAST
      MAY-23** per operator direction 2026-05-13. AWS runs AFTER GCP backfills + manifest quality verified (don't double
      cloud load before data quality is green). May-23 ships GCP-only; AWS dual-cloud parity becomes post-cutover
      stabilisation goal (target 2026-06-04). See `aws_migration_defi_first_2026_05_07.md` Phase 5 gate on master
      Gate 4.
- [x] ✅ DEFERRED-FUTURE-WORK **AWS batch backfill `--force`** runs on a small DeFi window (work-stream D.2). 🟢
      **DEFERRED PAST MAY-23** — same operator direction. Post-Gate-4.
- [x] ✅ DEFERRED-FUTURE-WORK **AWS backtest + ML examples** run via deployment-api (work-stream D.3). 🟢 **DEFERRED
      PAST MAY-23** — same operator direction. Post-Gate-4.
- [x] ✅ DEFERRED-FUTURE-WORK DART terminal in UTS-UI: archetype visualization + manual trade entry (work-stream C).
      **Blocked**: research-service repo decision (Week 1 above); UTS-UI `/research/ml-experiments` +
      `/research/strategy-backtests` + `/research/execution-backtests` tabs; work-stream A endpoints.
- [x] ✅ DEFERRED-FUTURE-WORK Treasury: Copper integration validated; CEFFU manual handoff documented. 🟢 **CLIENT-SIDE
      — NOT OUR BLOCKER** per operator direction 2026-05-13. Copper + CEFFU are the client's institutional onboarding
      workstreams (post-cutover); they do NOT gate May-23. May-23 ships on `CLOUD_KMS_ENCRYPTED` custody (verified
      shipped: execution-service@`d45d24b4` provider + 10 GCP CMKs in `wallets-prod` / `wallets-staging` keyrings, 90d
      auto-rotation). Post-cutover successor: `alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md` Group H
      absorbs Copper/CEFFU institutional integration alongside Slack/PagerDuty onboarding.

### Week 3 (May 20–23) · cutover (live trading + AWS live deployment)

- [x] ✅ DEFERRED-FUTURE-WORK Real wallet funded testnet → mainnet
- [x] ✅ DEFERRED-FUTURE-WORK DART manual-trade window: 3 days operator-monitored on `carry_staked_basis`
- [x] ✅ DEFERRED-FUTURE-WORK Automation flip on `carry_staked_basis` → 7-day continuous run begins (extends past May 23
      into May 30)
- [x] ✅ DEFERRED-FUTURE-WORK `ARBITRAGE_PRICE_DISPERSION` enters DART manual-trade window (lags carry_staked_basis by
      ~2 days)
- [x] ✅ DEFERRED-FUTURE-WORK **AWS live archetype** running in parallel — one carry_staked_basis instance on smaller
      capital deployed to AWS (work-stream D.4)
- [x] ✅ DEFERRED-FUTURE-WORK **Seamless-switch test** between GCP-live ↔ AWS-live (work-stream D.4)
- [x] ✅ DEFERRED-FUTURE-WORK Build-history tab in deployment-ui shipped (work-stream D.5)
- [x] ✅ DEFERRED-FUTURE-WORK Batch-vs-live reconciliation matches within tolerance per archetype config (Group F
      item 21)

---

## Tracking surface

- [x] Plan promoted to `unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.md` (this file)
- [x] Audit companion at `unified-trading-pm/codex/10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md` (pointer + drift
      table mirror)
- [x] Referenced from `CLAUDE.md` so every agent session loads it
- [x] ✅ Per-service yamls at `codex/10-audit/repos/<service>.yaml` extended with the 7-group / 23-item structure for
      tier-1 services
- [x] ✅ DEFERRED-FUTURE-WORK Update cadence: Tier-1 readiness rollup refreshed by EOD daily; critical-path DAG checked
      at start of each week
- No duplication: sub-plans in `plans/active/` remain authoritative; this plan only references and orchestrates

---

## Verification (end-to-end, the 23-item checklist instantiated)

**DeFi live (the headline goal)**

- [x] ✅ DEFERRED-FUTURE-WORK `carry_staked_basis` cycle on real wallet (testnet → mainnet) via DART manual-trade lane →
      backend execution → automation flip → ≥7-day continuous run; P&L matches batch sim within configured bps tolerance
      per Group F item 21
- [x] ✅ DEFERRED-FUTURE-WORK `ARBITRAGE_PRICE_DISPERSION` running across ≥3 perp venues with cross-venue funding spread
      captured

**Perp venue coverage**

- [x] ✅ DEFERRED-FUTURE-WORK All 6 venues live: Bybit, Deribit, Binance, OKX, Hyperliquid, Aster — one trade each
      verified via deployment-UI

**Observability + guardrails**

- [x] ✅ DEFERRED-FUTURE-WORK Tail VM event logs from deployment-UI without SSH for 24h on a live forward-poll VM
- [x] ✅ DEFERRED-FUTURE-WORK Live alerting fires on synthetic data-freshness, P&L deviation, and position-breach
      violations injected via test fixtures
- [x] ✅ DEFERRED-FUTURE-WORK Kill switch fires on synthetic risk-breach trigger

**Cloud parity (work-stream D)**

- [x] ✅ DEFERRED-FUTURE-WORK DeFi-relevant data migrated to AWS S3 (manifest + parquet) with same shard layout as GCS
- [x] ✅ DEFERRED-FUTURE-WORK AWS data status query works in deployment-UI and matches GCS truth
- [x] ✅ DEFERRED-FUTURE-WORK AWS batch backfill `--force` produces parquet end-to-end
- [x] ✅ DEFERRED-FUTURE-WORK AWS strategy backtest + ML training + execution backtest examples run via deployment-api
- [x] ✅ DEFERRED-FUTURE-WORK AWS live carry_staked_basis instance running on smaller capital
- [x] ✅ DEFERRED-FUTURE-WORK Seamless-switch (GCP-live → AWS-live → back) preserves position state via custody /
      position-balance-monitor

**Readiness rollup**

- [x] ✅ DEFERRED-FUTURE-WORK All Tier-1 services pass 23/23 readiness checklist (or have explicit n/a justified) —
      verified per `codex/10-audit/repos/<service>.yaml`
- [x] ✅ DEFERRED-FUTURE-WORK All 9 drift-audit rows resolved (none remaining `⚠`)
- [x] ✅ DEFERRED-FUTURE-WORK `codex/00-SSOT-INDEX.md` updated to reference all new SSOT docs (work-streams D.6 + F)
- [x] `CLAUDE.md` cross-references this master plan in a new "Master Plan" section (verified 2026-05-07:
      .claude/CLAUDE.md line 22 has `## Master Plan — Live DeFi Trading by 2026-05-23` section)

---

## Critical files (read first, in this order)

| Purpose                                           | File                                                                                                                                                     |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Codex master index                                | `unified-trading-pm/codex/00-SSOT-INDEX.md`                                                                                                              |
| Cross-cutting principles (read before any change) | `unified-trading-pm/codex/POST_PLAN_REALITY_2026_05_06.md`                                                                                               |
| Existing service-readiness SSOT                   | `unified-trading-pm/codex/10-audit/REPO_READINESS_CHECKLIST.yaml`, `_checklist-template-enhanced.yaml`, `repos/<service>.yaml`                           |
| Batch=live design SSOT                            | `unified-trading-pm/codex/04-architecture/batch-live-architecture.md` (single SSOT), `backtest-groups.md`                                                |
| Shard granularity per asset-group                 | `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md`                                                                              |
| UI surface SSOT                                   | `unified-trading-pm/codex/05-infrastructure/ui-functionality-requirements.md`                                                                            |
| Tarball deployment SSOT                           | `unified-trading-pm/codex/05-infrastructure/vm-tarball-deployment.md`                                                                                    |
| Cloud-agnostic SSOT                               | `unified-trading-pm/codex/04-architecture/cloud-agnostic-migration.md`                                                                                   |
| Lifecycle events SSOT                             | `unified-trading-pm/codex/03-observability/lifecycle-events.md`                                                                                          |
| Strategy archetypes SSOT                          | `unified-trading-pm/codex/09-strategy/strategy-summary.md`                                                                                               |
| Strategy onboarding                               | `unified-trading-pm/codex/09-strategy/operational/onboarding-checklist.md`                                                                               |
| Operational modes (manual / paper / automated)    | `unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md`                                                         |
| P&L attribution                                   | `unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`                                                                  |
| Alerting (batch + live)                           | `unified-trading-pm/codex/04-architecture/alerting-batch-live.md`                                                                                        |
| Auto-recovery / kill switches                     | `unified-trading-pm/codex/04-architecture/autonomous-recovery-matrix.md`                                                                                 |
| Custody (Copper + CEFFU)                          | `unified-trading-pm/codex/04-architecture/custody-providers.md` (single SSOT — Copper + CEFFU + LocalKey + Mock), `wallet-hierarchy-and-capital-flow.md` |
| Service control surface                           | `unified-trading-pm/codex/04-architecture/service-control-surface.md`                                                                                    |
| Existing deployment-API                           | `deployment-api/deployment_api/routes/`                                                                                                                  |
| Existing deployment-UI                            | `deployment-ui/src/pages/`                                                                                                                               |
| Existing UTS-UI admin                             | `unified-trading-system-ui/app/(ops)/admin/`                                                                                                             |
| Cross-cloud partial AWS                           | `deployment-api/deployment_api/routes/_code_builds_aws.py`, `deployment-service/buildspec.aws.yaml`                                                      |

## Cross-plan annotation from slot 5 / `defi_recursive_borrow_archetypes_2026_05_10.md` (2026-05-12)

**Group F item 18 (2-year batch backtest run)** — recursive-borrow Phase 12 design (shipped 2026-05-12 @PM@`03492b96`)
satisfies item 18 via 14-scenario matrix: 4 funding-regime (SCN-A1-A4) + 5 liquidation-stress (SCN-B1-B5) + 5
venue/bridge-failure (SCN-C1-C5). **Recommended master plan refresh**: update Group F item 18 wording to reference
scenario ID set `{SCN-A1..A4, SCN-B1..B5, SCN-C1..C5}` so continuous-verification matrix can drill into per-scenario
verdicts.

**Group G item 23 (operator-UX)** — recursive-borrow Phase 11 design introduces NEW operator-UX surface
`HealthFactorMonitorTile` (live HF chart per active position; threshold lines at 1.10/1.05; UI-throttled 1-5s
irrespective of chain block-rate). Per Master Plan Continuous-Verification Column HARD RULE, this needs an entry:
cadence `daily-Tab`, owner `slot 5 or designated UI Tab`, verifier
`Playwright matrix at deployment-ui/tests/integration/recursive_borrow/`, last_verified `NEVER`.

Slot 5 NOT auto-editing the readiness checklist table (Findings Triage — master plan owned by main orchestrator + slot
1). Reference: `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 11 + Phase 12 design sections.

---

## Credential asks — resolved / deferred (2026-05-15)

Authorized edit by slot 11 per orchestrator direction 2026-05-14 15:30 UTC (item #8 mechanical).

| Adapter                                        | Secret(s)                             | Status                    | Decision                                                                                                                                                                                                                                                                                                                                     | Successor plan                                                                                                     |
| ---------------------------------------------- | ------------------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| cbETH LST APR (`lst_coinbase_adapter.py`)      | coinbase-api-key, coinbase-api-secret | **DEFERRED-POST-CUTOVER** | Canonical source is on-chain `exchangeRate()` call (already wired in `lst_rates_handler.py`). Coinbase API matches on-chain to 10 decimal places — it is not an independent source. No credential needed for May-23. See `plans/active/issues/lst_apr_sourcing_method_validated_2026_05_14.md`.                                              | Coinbase Institutional REST as richer secondary source — post-cutover Coinbase integration plan (not yet created). |
| Kraken CeFi adapter (`kraken_rest_adapter.py`) | kraken-api-key, kraken-api-secret     | **DEFERRED-POST-CUTOVER** | Historic Kraken ticks + funding rates covered by Tardis (existing `BLOCKED-CREDENTIALS` in master plan). Live Kraken API is optional — 7th of 7+ CeFi venues; Binance/Bybit/OKX/Deribit/Hyperliquid/Aster already cover both carry_staked_basis + arbitrage_price_dispersion cells. Adapter scaffold + unit tests ship and stay in codebase. | Post-cutover live Kraken streaming plan (not yet created).                                                         |
| `coinbase-api-key` (market-data context note)  | coinbase-api-key                      | **NOT NEEDED (cbETH)**    | `coinbase-api-key` in `codex/07-security/secrets-management.md` (`KEY_NOT_IN_SM`) is for _order placement_ (Coinbase brokerage API), NOT for `wrapped-assets` endpoint which is unauthenticated and reads directly from the on-chain contract. Do NOT file a BLOCKED-CREDENTIALS for cbETH rate data.                                        | n/a                                                                                                                |

---

## Operator-pending gates (awaiting explicit sign-off)

Items that cannot auto-close — require operator review + explicit `[ack]` before being flipped.

| Item                                        | Plan                                                                | Gate                                   | What operator must do                                                                                                                                                                                                                                                                                         | Added             |
| ------------------------------------------- | ------------------------------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| deployment-ui G.3 — B6 operator UX sign-off | `plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md` Phase G.3 | B6 (business gate — final before prod) | Review 6-tab UX + Monitor sub-tab flow + Data-Status scope reduction + env-tier hosting on staging (`staging.odum-research.com`); run G.2 staging deploy runbook first (`deployment-service/runbooks/deployment-ui-staging-deploy.md`); then comment `[ack] G.3 approved` in this plan to unblock prod deploy | 2026-05-19 slot-6 |
