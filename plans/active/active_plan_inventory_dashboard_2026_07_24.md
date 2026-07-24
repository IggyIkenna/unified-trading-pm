---
doc_type: plan
title: Active plan inventory + Done-vs-Left dashboard
summary: >-
  Workspace-wide auto-regenerated inventory of every plans/active/*.md plan's checkbox progress, calibrated AI-days
  remaining, and epic-orphan status. Extracted 2026-07-24 from master_to_live_defi_2026_05_23.md (archived that same day
  per the plan line-cap remediation) so the daily auto-regeneration keeps a live, non-archived host.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [inventory, dashboard, auto-tracked, plan-hygiene, workspace-wide]
related: [master_to_live_defi_2026_05_23]
created: "2026-07-24"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Relocated from master_to_live_defi_2026_05_23.md's "Active plan inventory + Done-vs-Left dashboard" section as part of
  plans/active/issues/plan_line_cap_remediation_2026_07_23.md operator decision #2 (close out master_to_live_defi
  entirely) -- that archival would have broken scripts/plans/regenerate_active_plan_inventory.py's hardcoded MASTER_FILE
  constant (Cloud-Scheduler-run twice daily), so the live dashboard section moves here instead of going stale inside a
  frozen archived doc.
drift_direction: advance-code
---

# Active plan inventory + Done-vs-Left dashboard

## Active plan inventory + Done-vs-Left dashboard (auto-tracked)

This section is **auto-regenerated** by
[`scripts/plans/regenerate_active_plan_inventory.py`](../../scripts/plans/regenerate_active_plan_inventory.py). It
solves two coupled problems: (1) "What's done vs left across the workspace?" — aggregate row + per-plan progress at a
glance; (2) "Which plans aren't wrapped by master/epics?" — orphan column visible inline so nothing hides.

Refresh cadence: main-orchestrator runs the script at morning ledger sweep + EOD. Numbers between regenerations are
stale — re-run before any planning decision that depends on this table.

<!-- AUTO-INVENTORY-START -->

_Auto-generated via `scripts/plans/regenerate_active_plan_inventory.py`. Sorted by `cal_left` desc. TBD = baseline not
yet filled by owner agent. Orphan = plan not referenced by master or any epic — should be folded into the appropriate
epic._

| Plan                                                                                                                                                        | Owner            | Class     | Checkboxes | % done       | Cal left | Deadline |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- | --------- | ---------- | ------------ | -------- | -------- |
| [`v2_engine_venue_buildout_2026_06_15`](./v2_engine_venue_buildout_2026_06_15.md)                                                                           | master           | research  | 14/51      | 27%          | 47.9     | —        |
| [`sports_consolidated_closeout_2026_07_19`](./sports_consolidated_closeout_2026_07_19.md)                                                                   | master           | infra     | 36/130     | 28%          | 26.6     | —        |
| [`deployment_registry_firestore_migration_2026_07_14`](./deployment_registry_firestore_migration_2026_07_14.md)                                             | master           | infra     | —          | —            | 13.0     | —        |
| [`crypto_alpha_research_2026_07_24`](./crypto_alpha_research_2026_07_24.md)                                                                                 | master           | research  | 11/33      | 33%          | 12.0     | —        |
| [`prediction_consolidated_closeout_2026_07_18`](./prediction_consolidated_closeout_2026_07_18.md)                                                           | master           | infra     | —          | —            | 9.6      | —        |
| [`org_migration_to_odumresearch_2026_06_07`](./org_migration_to_odumresearch_2026_06_07.md)                                                                 | master           | infra     | 0/27       | 0%           | 8.0      | —        |
| [`defi_consolidated_closeout_2026_07_18`](./defi_consolidated_closeout_2026_07_18.md)                                                                       | master           | infra     | 7/34       | 21%          | 7.6      | —        |
| [`deployment_ui_observability_ux_tracker_2026_07_17`](./deployment_ui_observability_ux_tracker_2026_07_17.md)                                               | master           | design    | 2/35       | 6%           | 6.8      | —        |
| [`defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17`](./defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md)             | master           | brand-new | 7/11       | 64%          | 6.5      | —        |
| [`data_pipeline_check_mdps_features_2026_07_20`](./data_pipeline_check_mdps_features_2026_07_20.md)                                                         | master           | infra     | 7/35       | 20%          | 5.1      | —        |
| [`artifact_pipeline_observability_2026_07_17`](./artifact_pipeline_observability_2026_07_17.md)                                                             | master           | infra     | 24/47      | 51%          | 4.9      | —        |
| [`deployment_durable_operational_data_bigquery_2026_07_21`](./deployment_durable_operational_data_bigquery_2026_07_21.md)                                   | master           | infra     | 0/22       | 0%           | 4.8      | —        |
| [`citadel_paper_batch_live_reconciliation_2026_06_19`](./citadel_paper_batch_live_reconciliation_2026_06_19.md)                                             | master           | infra     | 78/89      | 88%          | 4.7      | —        |
| [`cefi_consolidated_closeout_2026_07_18`](./cefi_consolidated_closeout_2026_07_18.md)                                                                       | master           | infra     | 10/31      | 32%          | 4.3      | —        |
| [`instruments_foundation_phase0_cross_cutting_2026_07_24`](./instruments_foundation_phase0_cross_cutting_2026_07_24.md)                                     | master           | design    | 2/15       | 13%          | 4.3      | —        |
| [`candle_canonical_path_migration_execution_2026_07_24`](./candle_canonical_path_migration_execution_2026_07_24.md)                                         | master           | infra     | 0/16       | 0%           | 4.0      | —        |
| [`cefi_ml_directional_continuous_live_2026_06_20`](./cefi_ml_directional_continuous_live_2026_06_20.md)                                                     | master           | brand-new | 6/9        | 67%          | 4.0      | —        |
| [`github_actions_ci_cost_reduction_2026_07_15`](./github_actions_ci_cost_reduction_2026_07_15.md)                                                           | master           | infra     | —          | —            | 4.0      | —        |
| [`github_actions_operator_gated_followups_2026_07_17`](./github_actions_operator_gated_followups_2026_07_17.md)                                             | master           | infra     | 0/9        | 0%           | 4.0      | —        |
| [`sports_legacy_bucket_cutover_2026_07_16`](./sports_legacy_bucket_cutover_2026_07_16.md)                                                                   | master           | infra     | —          | —            | 4.0      | —        |
| [`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`](./pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md)               | master           | infra     | 18/30      | 60%          | 3.8      | —        |
| [`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20`](./cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md)                                 | master           | brand-new | 14/36      | 39%          | 3.7      | —        |
| [`carry_staked_basis_funding_scan_experiment_2026_06_16`](./carry_staked_basis_funding_scan_experiment_2026_06_16.md)                                       | master           | research  | 0/28       | 0%           | 3.6      | —        |
| [`tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20`](./tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md)                                       | master           | brand-new | 1/10       | 10%          | 3.6      | —        |
| [`vol_dvol_backtestable_engines_2026_07_13`](./vol_dvol_backtestable_engines_2026_07_13.md)                                                                 | master           | brand-new | 2/7        | 29%          | 3.6      | —        |
| [`tradfi_manifest_content_recovery_completion_2026_07_24`](./tradfi_manifest_content_recovery_completion_2026_07_24.md)                                     | master           | infra     | 6/17       | 35%          | 3.1      | —        |
| [`codex_vs_repo_docs_ssot_audit_2026_06_01`](./codex_vs_repo_docs_ssot_audit_2026_06_01.md)                                                                 | master           | refactor  | 1/24       | 4%           | 3.1      | —        |
| [`bigquery_feature_ml_compute_engine_option_2026_06_08`](./bigquery_feature_ml_compute_engine_option_2026_06_08.md)                                         | master           | design    | 2/7        | 29%          | 3.0      | —        |
| [`colocated_feature_pipeline_in_memory_handoff_2026_06_21`](./colocated_feature_pipeline_in_memory_handoff_2026_06_21.md)                                   | master           | design    | 0/4        | 0%           | 3.0      | —        |
| [`data_status_cell_grid_rearchitecture_2026_07_18`](./data_status_cell_grid_rearchitecture_2026_07_18.md)                                                   | master           | design    | 0/7        | 0%           | 3.0      | —        |
| [`instruments_tradfi_g1_g5_gate_execution_2026_07_24`](./instruments_tradfi_g1_g5_gate_execution_2026_07_24.md)                                             | master           | design    | 12/30      | 40%          | 3.0      | —        |
| [`predictions_ml_walk_forward_and_arb_2026_06_20`](./predictions_ml_walk_forward_and_arb_2026_06_20.md)                                                     | master           | research  | 3/8        | 38%          | 3.0      | —        |
| [`sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24`](./sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md) | master           | design    | 17/28      | 61%          | 2.8      | —        |
| [`instruments_cefi_g1_g5_gate_execution_2026_07_24`](./instruments_cefi_g1_g5_gate_execution_2026_07_24.md)                                                 | master           | design    | 13/23      | 57%          | 2.6      | —        |
| [`utl_uac_reuse_consolidation_remediation_2026_06_10`](./utl_uac_reuse_consolidation_remediation_2026_06_10.md)                                             | master           | refactor  | 44/69      | 64%          | 2.6      | —        |
| [`cefi_4surface_migration_execution_log_2026_07_24`](./cefi_4surface_migration_execution_log_2026_07_24.md)                                                 | master           | infra     | 0/7        | 0%           | 2.4      | —        |
| [`data_source_provenance_enforcement_2026_07_24`](./data_source_provenance_enforcement_2026_07_24.md)                                                       | master           | infra     | 0/19       | 0%           | 2.4      | —        |
| [`docker_artifact_registry_cleanup_policy_2026_07_24`](./docker_artifact_registry_cleanup_policy_2026_07_24.md)                                             | master           | infra     | 0/17       | 0%           | 2.4      | —        |
| [`legacy_bucket_dual_write_decommission_2026_07_24`](./legacy_bucket_dual_write_decommission_2026_07_24.md)                                                 | master           | infra     | 0/14       | 0%           | 2.4      | —        |
| [`sports_consolidated_audit_2026_07_19`](./sports_consolidated_audit_2026_07_19.md)                                                                         | master           | research  | —          | —            | 2.4      | —        |
| [`carry_strategy_ensemble_productionization_2026_07_24`](./carry_strategy_ensemble_productionization_2026_07_24.md)                                         | master           | research  | 4/11       | 36%          | 2.3      | —        |
| [`defi_track01_per_instrument_and_canon_id_2026_07_24`](./defi_track01_per_instrument_and_canon_id_2026_07_24.md)                                           | master           | infra     | 9/27       | 33%          | 2.1      | —        |
| [`tradfi_consolidated_closeout_2026_07_18`](./tradfi_consolidated_closeout_2026_07_18.md)                                                                   | master           | infra     | 1/9        | 11%          | 2.1      | —        |
| [`cross_venue_funding_reversion_research_2026_07_24`](./cross_venue_funding_reversion_research_2026_07_24.md)                                               | master           | research  | 2/15       | 13%          | 2.1      | —        |
| [`prediction_phase_ab_residuals_2026_07_24`](./prediction_phase_ab_residuals_2026_07_24.md)                                                                 | master           | infra     | 5/14       | 36%          | 2.1      | —        |
| [`sports_catalog_league_grain_only_scope_2026_07_08`](./sports_catalog_league_grain_only_scope_2026_07_08.md)                                               | master           | research  | 3/7        | 43%          | 2.1      | —        |
| [`data_completion_prediction_2026_07_15`](./data_completion_prediction_2026_07_15.md)                                                                       | master           | infra     | 0/23       | 0%           | 2.0      | —        |
| [`defi_pipeline_e2e_and_coverage_validation_2026_06_20`](./defi_pipeline_e2e_and_coverage_validation_2026_06_20.md)                                         | master           | infra     | 3/6        | 50%          | 2.0      | —        |
| [`github_actions_cost_reduction_options_analysis_2026_07_15`](./github_actions_cost_reduction_options_analysis_2026_07_15.md)                               | master           | design    | —          | —            | 2.0      | —        |
| [`instruments_store_cf_canonicalization_single_walk_2026_07_24`](./instruments_store_cf_canonicalization_single_walk_2026_07_24.md)                         | master           | infra     | 5/26       | 19%          | 1.9      | —        |
| [`data_completion_cefi_2026_07_15`](./data_completion_cefi_2026_07_15.md)                                                                                   | master           | infra     | 1/27       | 4%           | 1.9      | —        |
| [`mtds_available_at_cross_asset_backfill_2026_07_13`](./mtds_available_at_cross_asset_backfill_2026_07_13.md)                                               | master           | infra     | 6/15       | 40%          | 1.9      | —        |
| [`deployment_registry_firestore_p3_cutover_2026_07_14`](./deployment_registry_firestore_p3_cutover_2026_07_14.md)                                           | master           | infra     | 1/5        | 20%          | 1.9      | —        |
| [`data_status_catalogue_true_source_phase2_2026_07_24`](./data_status_catalogue_true_source_phase2_2026_07_24.md)                                           | master           | design    | 0/1        | 0%           | 1.8      | —        |
| [`prediction_cross_venue_arb_and_coverage_2026_07_24`](./prediction_cross_venue_arb_and_coverage_2026_07_24.md)                                             | master           | brand-new | 31/40      | 78%          | 1.8      | —        |
| [`sports_arb_decay_window_and_alpha_gate_design_2026_07_21`](./sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md)                                 | master           | design    | 0/8        | 0%           | 1.8      | —        |
| [`data_pipeline_alert_substrate_residual_2026_07_24`](./data_pipeline_alert_substrate_residual_2026_07_24.md)                                               | master           | infra     | 4/16       | 25%          | 1.8      | —        |
| [`infra_ops_residual_migration_verification_2026_07_24`](./infra_ops_residual_migration_verification_2026_07_24.md)                                         | master           | design    | 0/9        | 0%           | 1.8      | —        |
| [`instruments_foundation_completeness_2026_06_24`](./instruments_foundation_completeness_2026_06_24.md)                                                     | master           | design    | 5/12       | 42%          | 1.8      | —        |
| [`repo_scripts_governance_audit_2026_06_18`](./repo_scripts_governance_audit_2026_06_18.md)                                                                 | master           | infra     | 3/11       | 27%          | 1.7      | —        |
| [`bucket_estate_consolidation_closeout_2026_07_24`](./bucket_estate_consolidation_closeout_2026_07_24.md)                                                   | master           | infra     | 0/6        | 0%           | 1.6      | —        |
| [`codex_violations_ratchet_to_five_2026_06_10`](./codex_violations_ratchet_to_five_2026_06_10.md)                                                           | master           | refactor  | 35/45      | 78%          | 1.6      | —        |
| [`lst_rate_honest_coverage_2026_07_21`](./lst_rate_honest_coverage_2026_07_21.md)                                                                           | master           | infra     | 14/21      | 67%          | 1.6      | —        |
| [`prediction_phase_c_data_status_ui_2026_07_24`](./prediction_phase_c_data_status_ui_2026_07_24.md)                                                         | master           | infra     | 0/4        | 0%           | 1.6      | —        |
| [`sports_odds_exchange_fixed_fork_2026_07_18`](./sports_odds_exchange_fixed_fork_2026_07_18.md)                                                             | master           | refactor  | 0/10       | 0%           | 1.6      | —        |
| [`sports_odds_feature_naming_canonicalization_2026_07_21`](./sports_odds_feature_naming_canonicalization_2026_07_21.md)                                     | master           | design    | 1/9        | 11%          | 1.6      | —        |
| [`bucket_fold_execution_strategy_2026_07_17`](./bucket_fold_execution_strategy_2026_07_17.md)                                                               | master           | infra     | 3/9        | 33%          | 1.6      | —        |
| [`mtds_file_size_refactor_2026_06_08`](./mtds_file_size_refactor_2026_06_08.md)                                                                             | master           | refactor  | 2/9        | 22%          | 1.6      | —        |
| [`prediction_capture_incident_remediation_2026_07_06`](./prediction_capture_incident_remediation_2026_07_06.md)                                             | master           | infra     | 11/20      | 55%          | 1.4      | —        |
| [`prediction_phase_e_football_arb_live_2026_07_24`](./prediction_phase_e_football_arb_live_2026_07_24.md)                                                   | master           | infra     | 2/5        | 40%          | 1.4      | —        |
| [`bucket_iam_write_protection_per_tier_2026_06_09`](./bucket_iam_write_protection_per_tier_2026_06_09.md)                                                   | master           | infra     | 5/12       | 42%          | 1.4      | —        |
| [`data_completion_to_100_all_ag_2026_06_21`](./data_completion_to_100_all_ag_2026_06_21.md)                                                                 | master           | infra     | 95/115     | 83%          | 1.4      | —        |
| [`canonical_id_builder_retrofit_checklist_2026_07_08`](./canonical_id_builder_retrofit_checklist_2026_07_08.md)                                             | master           | refactor  | 4/13       | 31%          | 1.4      | —        |
| [`tradfi_massive_dual_source_2026_05_28`](./tradfi_massive_dual_source_2026_05_28.md)                                                                       | master           | infra     | 41/51      | 80%          | 1.4      | —        |
| [`sports_master_closeout_2026_07_21`](./sports_master_closeout_2026_07_21.md)                                                                               | master           | infra     | 15/21      | 71%          | 1.4      | —        |
| [`infra_capture_and_devops_leftovers_2026_07_06`](./infra_capture_and_devops_leftovers_2026_07_06.md)                                                       | master           | infra     | 4/9        | 44%          | 1.3      | —        |
| [`l2_book_microstructure_capture_2026_07_13`](./l2_book_microstructure_capture_2026_07_13.md)                                                               | master           | brand-new | 6/8        | 75%          | 1.2      | —        |
| [`asset_class_to_asset_group_rename_2026_07_21`](./asset_class_to_asset_group_rename_2026_07_21.md)                                                         | master           | refactor  | 0/7        | 0%           | 1.2      | —        |
| [`is_daily_enum_capture_heal_2026_07_07`](./is_daily_enum_capture_heal_2026_07_07.md)                                                                       | master           | infra     | 0/3        | 0%           | 1.2      | —        |
| [`pipeline_mode_partition_migration_2026_06_01`](./pipeline_mode_partition_migration_2026_06_01.md)                                                         | master           | infra     | 0/2        | 0%           | 1.2      | —        |
| [`sports_group_c_execution_backtest_harness_2026_07_21`](./sports_group_c_execution_backtest_harness_2026_07_21.md)                                         | master           | infra     | 0/5        | 0%           | 1.2      | —        |
| [`sports_pipeline_to_100pct_golden_window_first_2026_06_27`](./sports_pipeline_to_100pct_golden_window_first_2026_06_27.md)                                 | master           | design    | —          | —            | 1.2      | —        |
| [`sports_predictions_live_mode_activation_readiness_2026_07_21`](./sports_predictions_live_mode_activation_readiness_2026_07_21.md)                         | master           | design    | 0/6        | 0%           | 1.2      | —        |
| [`ui_build_warm_cache_2026_06_17`](./ui_build_warm_cache_2026_06_17.md)                                                                                     | master           | infra     | 0/4        | 0%           | 1.2      | —        |
| [`mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24`](./mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md)                             | master           | infra     | 23/45      | 51%          | 1.2      | —        |
| [`stash_pile_workspace_cleanup_2026_06_03`](./stash_pile_workspace_cleanup_2026_06_03.md)                                                                   | master           | infra     | 1/18       | 6%           | 1.1      | —        |
| [`qg_host_adaptive_resource_governor_2026_07_14`](./qg_host_adaptive_resource_governor_2026_07_14.md)                                                       | master           | infra     | 21/29      | 72%          | 1.1      | —        |
| [`tradfi_backfill_throughput_followups_2026_07_24`](./tradfi_backfill_throughput_followups_2026_07_24.md)                                                   | master           | infra     | 13/24      | 54%          | 1.1      | —        |
| [`predictions_other_bucket_and_ui_drilldown_2026_06_20`](./predictions_other_bucket_and_ui_drilldown_2026_06_20.md)                                         | master           | brand-new | 8/11       | 73%          | 1.1      | —        |
| [`data_pipeline_ag_residual_backfill_decisions_2026_07_24`](./data_pipeline_ag_residual_backfill_decisions_2026_07_24.md)                                   | master           | infra     | 3/9        | 33%          | 1.1      | —        |
| [`l0_doc_index_generator_2026_06_24`](./l0_doc_index_generator_2026_06_24.md)                                                                               | master           | infra     | 1/3        | 33%          | 1.1      | —        |
| [`ao_open_issues_consolidated_close_out_2026_07_17`](./ao_open_issues_consolidated_close_out_2026_07_17.md)                                                 | master           | infra     | 32/41      | 78%          | 1.1      | —        |
| [`data_completion_tradfi_2026_07_15`](./data_completion_tradfi_2026_07_15.md)                                                                               | master           | infra     | 18/38      | 47%          | 1.1      | —        |
| [`bucket_fold_portfolio_state_2026_07_17`](./bucket_fold_portfolio_state_2026_07_17.md)                                                                     | master           | infra     | 4/7        | 57%          | 1.0      | —        |
| [`capability_wizard_client_lite_and_ci_regen_followup_2026_07_24`](./capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md)                     | master           | brand-new | 0/1        | 0%           | 1.0      | —        |
| [`instrument_record_schema_completeness_extra_forbid_2026_07_18`](./instrument_record_schema_completeness_extra_forbid_2026_07_18.md)                       | master           | refactor  | 0/6        | 0%           | 1.0      | —        |
| [`data_completion_defi_2026_07_15`](./data_completion_defi_2026_07_15.md)                                                                                   | master           | infra     | 28/54      | 52%          | 1.0      | —        |
| [`bucket_fold_ml_2026_07_17`](./bucket_fold_ml_2026_07_17.md)                                                                                               | master           | infra     | 4/10       | 40%          | 1.0      | —        |
| [`deployment_registry_firestore_p5_verify_2026_07_14`](./deployment_registry_firestore_p5_verify_2026_07_14.md)                                             | master           | infra     | 2/5        | 40%          | 1.0      | —        |
| [`features_service_e2e_pipeline_test_2026_05_26`](./features_service_e2e_pipeline_test_2026_05_26.md)                                                       | master           | brand-new | 37/44      | 84%          | 1.0      | —        |
| [`bucket_fold_features_2026_07_17`](./bucket_fold_features_2026_07_17.md)                                                                                   | master           | infra     | 5/7        | 71%          | 0.9      | —        |
| [`data_pipeline_self_healing_completion_residual_2026_07_24`](./data_pipeline_self_healing_completion_residual_2026_07_24.md)                               | master           | infra     | 11/20      | 55%          | 0.9      | —        |
| [`deployment_registry_firestore_p0_unblock_2026_07_14`](./deployment_registry_firestore_p0_unblock_2026_07_14.md)                                           | master           | infra     | 7/16       | 44%          | 0.9      | —        |
| [`prediction_cqg_residual_2026_07_24`](./prediction_cqg_residual_2026_07_24.md)                                                                             | master           | design    | 0/2        | 0%           | 0.9      | —        |
| [`sports_fixtures_browser_single_catalogue_source_2026_07_24`](./sports_fixtures_browser_single_catalogue_source_2026_07_24.md)                             | master           | design    | 0/3        | 0%           | 0.9      | —        |
| [`sports_prediction_mvp_writetime_precompute_2026_07_24`](./sports_prediction_mvp_writetime_precompute_2026_07_24.md)                                       | master           | design    | 0/1        | 0%           | 0.9      | —        |
| [`sports_prelaunch_cf5_verify_residual_2026_07_24`](./sports_prelaunch_cf5_verify_residual_2026_07_24.md)                                                   | master           | design    | 0/2        | 0%           | 0.9      | —        |
| [`data_pipeline_alerts_batch_remediation_2026_07_15`](./data_pipeline_alerts_batch_remediation_2026_07_15.md)                                               | master           | infra     | 2/4        | 50%          | 0.8      | —        |
| [`defi_strategy_pnl_axis_index_2026_07_24`](./defi_strategy_pnl_axis_index_2026_07_24.md)                                                                   | master           | infra     | —          | —            | 0.8      | —        |
| [`manifest_consolidator_dtype_at_source_fix_2026_07_07`](./manifest_consolidator_dtype_at_source_fix_2026_07_07.md)                                         | master           | infra     | 0/2        | 0%           | 0.8      | —        |
| [`sports_legacy_cutover_closeout_tasks_2026_07_24`](./sports_legacy_cutover_closeout_tasks_2026_07_24.md)                                                   | master           | infra     | 0/2        | 0%           | 0.8      | —        |
| [`sports_mtds_odds_trades_index_correctness_followup_2026_07_24`](./sports_mtds_odds_trades_index_correctness_followup_2026_07_24.md)                       | master           | infra     | 0/2        | 0%           | 0.8      | —        |
| [`instruments_completion_tracker_2026_07_06`](./instruments_completion_tracker_2026_07_06.md)                                                               | master           | infra     | 8/38       | 21%          | 0.8      | —        |
| [`aster_and_cefi_rolling_adv_feature_2026_07_21`](./aster_and_cefi_rolling_adv_feature_2026_07_21.md)                                                       | master           | brand-new | 4/8        | 50%          | 0.8      | —        |
| [`prediction_phase_d_formal_smoke_and_backfill_2026_07_24`](./prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md)                                   | master           | infra     | 5/8        | 62%          | 0.8      | —        |
| [`prediction_perps_kalshi_polymarket_parked_2026_07_24`](./prediction_perps_kalshi_polymarket_parked_2026_07_24.md)                                         | master           | brand-new | 10/11      | 91%          | 0.7      | —        |
| [`mvp_scope_catalogue_tagging_2026_06_08`](./mvp_scope_catalogue_tagging_2026_06_08.md)                                                                     | master           | design    | 8/10       | 80%          | 0.7      | —        |
| [`defi_lending_writer_retire_prerequisite_2026_07_20`](./defi_lending_writer_retire_prerequisite_2026_07_20.md)                                             | master           | refactor  | 9/14       | 64%          | 0.7      | —        |
| [`master_data_canonicalisation_migration_catalogue_2026_06_07`](./master_data_canonicalisation_migration_catalogue_2026_06_07.md)                           | master           | design    | 29/36      | 81%          | 0.7      | —        |
| [`cefi_deribit_binance_futures_bundle_verification_2026_06_20`](./cefi_deribit_binance_futures_bundle_verification_2026_06_20.md)                           | master           | infra     | 5/7        | 71%          | 0.7      | —        |
| [`coinbase_bare_name_migration_execution_service_2026_07_10`](./coinbase_bare_name_migration_execution_service_2026_07_10.md)                               | master           | refactor  | 0/3        | 0%           | 0.6      | —        |
| [`defi_venue_lst_rates_residual_2026_07_24`](./defi_venue_lst_rates_residual_2026_07_24.md)                                                                 | master           | design    | 0/2        | 0%           | 0.6      | —        |
| [`mdps_features_reduced_artifact_tracker_2026_06_28`](./mdps_features_reduced_artifact_tracker_2026_06_28.md)                                               | master           | design    | —          | —            | 0.6      | —        |
| [`instruments_mtds_consistency_remediation_residuals_2026_07_24`](./instruments_mtds_consistency_remediation_residuals_2026_07_24.md)                       | master           | infra     | 29/43      | 67%          | 0.5      | —        |
| [`defi_onchain_derivable_values_and_date_drift_2026_06_20`](./defi_onchain_derivable_values_and_date_drift_2026_06_20.md)                                   | master           | design    | 12/14      | 86%          | 0.5      | —        |
| [`deployment_redesign_cherrypicks_2026_07_20`](./deployment_redesign_cherrypicks_2026_07_20.md)                                                             | master           | refactor  | 2/5        | 40%          | 0.5      | —        |
| [`prediction_live_clob_depth_capture_2026_07_24`](./prediction_live_clob_depth_capture_2026_07_24.md)                                                       | master           | brand-new | 32/34      | 94%          | 0.5      | —        |
| [`data_feed_sla_registry_and_active_self_healing_2026_06_19`](./data_feed_sla_registry_and_active_self_healing_2026_06_19.md)                               | master           | design    | 11/13      | 85%          | 0.5      | —        |
| [`distinct_values_noncanonical_audit_2026_07_20`](./distinct_values_noncanonical_audit_2026_07_20.md)                                                       | master           | infra     | 17/21      | 81%          | 0.5      | —        |
| [`active_plan_inventory_dashboard_2026_07_24`](./active_plan_inventory_dashboard_2026_07_24.md)                                                             | master           | infra     | —          | —            | 0.4      | —        |
| [`ao_issue_docs_consolidated_remediation_2026_07_23`](./ao_issue_docs_consolidated_remediation_2026_07_23.md)                                               | master           | refactor  | 2/4        | 50%          | 0.4      | —        |
| [`mtds_retry_safe_default_audit_2026_07_14`](./mtds_retry_safe_default_audit_2026_07_14.md)                                                                 | master           | refactor  | 0/5        | 0%           | 0.4      | —        |
| [`tradfi_phase_d_terminal_gate_2026_07_24`](./tradfi_phase_d_terminal_gate_2026_07_24.md)                                                                   | master           | infra     | 3/4        | 75%          | 0.4      | —        |
| [`mvp_backfill_defi_onchain_v10_2026_06_27`](./mvp_backfill_defi_onchain_v10_2026_06_27.md)                                                                 | master           | infra     | 11/12      | 92%          | 0.4      | —        |
| [`defi_migration_audit_log_2026_07_24`](./defi_migration_audit_log_2026_07_24.md)                                                                           | master           | design    | 8/23       | 35%          | 0.4      | —        |
| [`bucket_estate_fold_design_2026_07_13`](./bucket_estate_fold_design_2026_07_13.md)                                                                         | master           | design    | 15/17      | 88%          | 0.4      | —        |
| [`ao_fleet_observability_kpis_2026_07_20`](./ao_fleet_observability_kpis_2026_07_20.md)                                                                     | master           | infra     | 7/8        | 88%          | 0.3      | —        |
| [`is_catalogue_g1_root_audit_log_2026_07_24`](./is_catalogue_g1_root_audit_log_2026_07_24.md)                                                               | master           | design    | 4/9        | 44%          | 0.3      | —        |
| [`data_pipeline_hardening_self_monitoring_2026_06_22`](./data_pipeline_hardening_self_monitoring_2026_06_22.md)                                             | master           | infra     | 57/58      | 98%          | 0.3      | —        |
| [`data_status_tab_and_downloads_remediation_2026_06_16`](./data_status_tab_and_downloads_remediation_2026_06_16.md)                                         | master           | refactor  | 23/31      | 74%          | 0.3      | —        |
| [`tradfi_multisource_backfill_2026_06_22`](./tradfi_multisource_backfill_2026_06_22.md)                                                                     | master           | infra     | 10/12      | 83%          | 0.3      | —        |
| [`agent_orchestrator_alert_channel_cleanup_2026_07_13`](./agent_orchestrator_alert_channel_cleanup_2026_07_13.md)                                           | master           | infra     | 18/20      | 90%          | 0.2      | —        |
| [`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24`](./tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md)                                         | master           | infra     | 0/1        | 0%           | 0.2      | —        |
| [`consolidator_throughput_backlog_monitor_2026_07_09`](./consolidator_throughput_backlog_monitor_2026_07_09.md)                                             | master           | design    | 23/26      | 88%          | 0.2      | —        |
| [`instruments_mtds_subset_consistency_remediation_2026_06_17`](./instruments_mtds_subset_consistency_remediation_2026_06_17.md)                             | master           | infra     | —          | —            | 0.2      | —        |
| [`data_completion_sports_2026_07_24`](./data_completion_sports_2026_07_24.md)                                                                               | master           | infra     | 38/42      | 90%          | 0.2      | —        |
| [`defi_dedicated_bucket_shared_migration_2026_07_13`](./defi_dedicated_bucket_shared_migration_2026_07_13.md)                                               | master           | infra     | 15/17      | 88%          | 0.2      | —        |
| [`cicd_mvp_ldr_to_main_pipeline_2026_06_30`](./cicd_mvp_ldr_to_main_pipeline_2026_06_30.md)                                                                 | master           | refactor  | 17/20      | 85%          | 0.2      | —        |
| [`monitoring_control_plane_master_2026_06_10`](./monitoring_control_plane_master_2026_06_10.md)                                                             | master           | design    | 35/41      | 85%          | 0.2      | —        |
| [`data_pipeline_reconciliation_skill_2026_07_20`](./data_pipeline_reconciliation_skill_2026_07_20.md)                                                       | master           | design    | 40/42      | 95%          | 0.2      | —        |
| [`canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08`](./canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md)                         | master           | refactor  | 9/11       | 82%          | 0.1      | —        |
| [`orchestrator_vm_e2e_hardening_2026_07_24`](./orchestrator_vm_e2e_hardening_2026_07_24.md)                                                                 | master           | design    | 27/30      | 90%          | 0.1      | —        |
| [`data_status_page_ux_and_canonicalisation_2026_07_16`](./data_status_page_ux_and_canonicalisation_2026_07_16.md)                                           | master           | design    | 62/63      | 98%          | 0.1      | —        |
| [`data_pipeline_alerts_batch_remediation_closeout_2026_07_24`](./data_pipeline_alerts_batch_remediation_closeout_2026_07_24.md)                             | master           | infra     | 14/14      | 100%         | 0.0      | —        |
| [`deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13`](./deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md)                     | master           | design    | 18/18      | 100%         | 0.0      | —        |
| [`deployment_ui_plain_routes_retire_cockpit_tabs_2026_07_17`](./deployment_ui_plain_routes_retire_cockpit_tabs_2026_07_17.md)                               | master           | refactor  | 12/12      | 100%         | 0.0      | —        |
| [`docs_retrieval_layer_reconcile_2026_07_23`](./docs_retrieval_layer_reconcile_2026_07_23.md)                                                               | master           | infra     | 7/7        | 100%         | 0.0      | —        |
| [`github_actions_staging_machinery_shutdown_2026_07_24`](./github_actions_staging_machinery_shutdown_2026_07_24.md)                                         | master           | infra     | 3/3        | 100%         | 0.0      | —        |
| [`migration_verification_orphan_safety_2026_06_10`](./migration_verification_orphan_safety_2026_06_10.md)                                                   | master           | design    | 25/25      | 100%         | 0.0      | —        |
| [`mvp_backfill_defi_onchain_v10_operational_log_2026_07_24`](./mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md)                                 | master           | infra     | 7/7        | 100%         | 0.0      | —        |
| [`sports_master_closeout_progress_log_2026_07_24`](./sports_master_closeout_progress_log_2026_07_24.md)                                                     | master           | infra     | —          | —            | 0.0      | —        |
| [`sports_odds_bookmaker_coverage_enumeration_2026_06_20`](./sports_odds_bookmaker_coverage_enumeration_2026_06_20.md)                                       | master           | brand-new | 3/3        | 100%         | 0.0      | —        |
| **TOTAL** (162 plans)                                                                                                                                       | 0 orphans, 0 TBD | —         | —          | **47% done** | **362**  | —        |

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
