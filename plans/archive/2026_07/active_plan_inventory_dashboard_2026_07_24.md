---
doc_type: plan
title: Active plan inventory + Done-vs-Left dashboard
summary: >-
  Workspace-wide auto-regenerated inventory of every plans/active/*.md plan's checkbox progress, calibrated AI-days
  remaining, and epic-orphan status. Extracted 2026-07-24 from master_to_live_defi_2026_05_23.md (archived that same day
  per the plan line-cap remediation) so the daily auto-regeneration keeps a live, non-archived host.
status:
  complete # (was: active) 2026-07-28 plan-hygiene sweep: verified auto-regenerated inventory table, no
  # Todos section, no unfinished work of its own -- regeneration continues in place at this archived path
  # (twice-daily Cloud-Scheduler job re-pointed; scripts/plans/regenerate_active_plan_inventory.py MASTER_FILE
  # updated accordingly).
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [inventory, dashboard, auto-tracked, plan-hygiene, workspace-wide]
related: [master_to_live_defi_2026_05_23]
created: "2026-07-24"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P0
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

## Deferred work -- migrated to:

**None** -- doc verified fully complete at archival: auto-regenerated inventory table, no Todos section of its own, no
prose-only remaining work found. The regeneration job itself is NOT deferred work -- it is the doc's permanent function
and continues unchanged at this new path.

> **🗄️ ARCHIVED 2026-07-28 (plan-hygiene sweep)** -- role fulfilled as a completed extraction; the auto-regeneration
> this doc hosts is unaffected and continues in place at this archived path (see
> scripts/plans/regenerate_active_plan_inventory.py's MASTER_FILE).

# Active plan inventory + Done-vs-Left dashboard

## Active plan inventory + Done-vs-Left dashboard (auto-tracked)

This section is **auto-regenerated** by
[`scripts/plans/regenerate_active_plan_inventory.py`](../../scripts/plans/regenerate_active_plan_inventory.py). It
solves two coupled problems: (1) "What's done vs left across the workspace?" — aggregate row + per-plan progress at a
glance; (2) "Which plans aren't wrapped by master/epics?" — orphan column visible inline so nothing hides.

Refresh cadence: main-orchestrator runs the script at morning ledger sweep + EOD. Numbers between regenerations are
stale — re-run before any planning decision that depends on this table.

<!-- AUTO-INVENTORY-START -->
_Auto-generated via `scripts/plans/regenerate_active_plan_inventory.py`. Sorted by `cal_left` desc. TBD = baseline not yet filled by owner agent. Orphan = plan not referenced by master or any epic — should be folded into the appropriate epic._

| Plan | Owner | Class | Checkboxes | % done | Cal left | Deadline |
|---|---|---|---|---|---|---|
| [`code_readiness_five_agent_coordinator_2026_08_19`](./code_readiness_five_agent_coordinator_2026_08_19.md) | master | refactor | 5/9 | 56% | 37.3 | — |
| [`v2_engine_venue_buildout_2026_06_15`](./v2_engine_venue_buildout_2026_06_15.md) | master | research | 28/51 | 55% | 29.8 | — |
| [`issues_corpus_completion_dispatch_2026_08_21`](./issues_corpus_completion_dispatch_2026_08_21.md) | **orphan** | infra | 1/18 | 6% | 15.1 | — |
| [`ao_ci_aws_to_ionos_migration_2026_08_18`](./ao_ci_aws_to_ionos_migration_2026_08_18.md) | master | infra | 2/34 | 6% | 13.2 | — |
| [`issues_corpus_executable_queue_2026_08_21`](./issues_corpus_executable_queue_2026_08_21.md) | **orphan** | infra | 1/352 | 0% | 12.0 | — |
| [`crypto_alpha_research_2026_07_24`](./crypto_alpha_research_2026_07_24.md) | master | research | 13/33 | 39% | 10.9 | — |
| [`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11`](./elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md) | master | infra | 19/107 | 18% | 10.5 | — |
| [`state_fabric_artefacts_2026_08_20`](./state_fabric_artefacts_2026_08_20.md) | master | brand-new | 4/31 | 13% | 10.5 | — |
| [`cross_cutting_consolidated_closeout_2026_07_25`](./cross_cutting_consolidated_closeout_2026_07_25.md) | master | infra | 0/1 | 0% | 9.6 | — |
| [`mtds_sports_live_arb_feeds_sharpapi_oddsapiio_unity_2026_08_14`](./mtds_sports_live_arb_feeds_sharpapi_oddsapiio_unity_2026_08_14.md) | master | brand-new | 4/20 | 20% | 9.6 | — |
| [`venue_e2e_wiring_2026_08_16`](./venue_e2e_wiring_2026_08_16.md) | master | infra | 2/5 | 40% | 9.6 | — |
| [`state_fabric_uac_foundation_2026_08_20`](./state_fabric_uac_foundation_2026_08_20.md) | master | design | 0/16 | 0% | 9.0 | — |
| [`solana_lst_carry_jupiter_perps_and_kamino_borrow_2026_08_12`](./solana_lst_carry_jupiter_perps_and_kamino_borrow_2026_08_12.md) | master | infra | 4/28 | 14% | 8.2 | — |
| [`code_readiness_t3_features_ml_strategy_2026_08_19`](./code_readiness_t3_features_ml_strategy_2026_08_19.md) | master | refactor | 33/55 | 60% | 8.0 | — |
| [`sports_features_calculator_correctness_audit_2026_08_12`](./sports_features_calculator_correctness_audit_2026_08_12.md) | master | research | 0/11 | 0% | 7.2 | — |
| [`na_docs_validity_and_ao_eligibility_audit_2026_07_26`](./na_docs_validity_and_ao_eligibility_audit_2026_07_26.md) | master | research | 13/25 | 52% | 6.9 | — |
| [`code_readiness_t5_readiness_observability_presentations_2026_08_19`](./code_readiness_t5_readiness_observability_presentations_2026_08_19.md) | master | refactor | 34/49 | 69% | 6.7 | — |
| [`venue_smoke_test_bar_2026_08_16`](./venue_smoke_test_bar_2026_08_16.md) | master | infra | 3/10 | 30% | 6.7 | — |
| [`sports_consolidated_closeout_2026_07_19`](./sports_consolidated_closeout_2026_07_19.md) | master | infra | 57/69 | 83% | 6.4 | — |
| [`code_readiness_t2_refdata_marketdata_2026_08_19`](./code_readiness_t2_refdata_marketdata_2026_08_19.md) | master | refactor | 34/52 | 65% | 6.2 | — |
| [`venue_websocket_resilience_and_error_code_mapping_2026_08_21`](./venue_websocket_resilience_and_error_code_mapping_2026_08_21.md) | system_readiness_master | brand-new | 14/27 | 52% | 5.8 | — |
| [`sports_live_arb_strategy_and_execution_routing_2026_08_14`](./sports_live_arb_strategy_and_execution_routing_2026_08_14.md) | master | refactor | 3/19 | 16% | 4.0 | — |
| [`elysium_carveout_stubbed_strategy_service_2026_08_12`](./elysium_carveout_stubbed_strategy_service_2026_08_12.md) | master | design | 5/22 | 23% | 3.7 | — |
| [`defi_consolidated_closeout_2026_07_18`](./defi_consolidated_closeout_2026_07_18.md) | master | infra | 16/26 | 62% | 3.7 | — |
| [`cefi_ml_directional_continuous_live_2026_06_20`](./cefi_ml_directional_continuous_live_2026_06_20.md) | master | brand-new | 7/10 | 70% | 3.6 | — |
| [`multi_provider_context_billing_reconciliation_2026_08_16`](./multi_provider_context_billing_reconciliation_2026_08_16.md) | master | research | 14/32 | 44% | 3.4 | — |
| [`sports_taxonomy_p4_backfill_2026_08_08`](./sports_taxonomy_p4_backfill_2026_08_08.md) | master | infra | 4/10 | 40% | 3.4 | — |
| [`carry_staked_basis_funding_scan_experiment_2026_06_16`](./carry_staked_basis_funding_scan_experiment_2026_06_16.md) | master | research | 2/28 | 7% | 3.3 | — |
| [`producer_silence_flatten_protocol_2026_08_14`](./producer_silence_flatten_protocol_2026_08_14.md) | master | design | 2/23 | 9% | 3.3 | — |
| [`ao_dispatch_plans_operator_item_separation_sweep_2026_08_16`](./ao_dispatch_plans_operator_item_separation_sweep_2026_08_16.md) | master | infra | 0/12 | 0% | 3.2 | — |
| [`bigquery_feature_ml_compute_engine_option_2026_06_08`](./bigquery_feature_ml_compute_engine_option_2026_06_08.md) | master | design | 2/7 | 29% | 3.0 | — |
| [`instruments_catalogue_definitions_and_field_history_2026_08_17`](./instruments_catalogue_definitions_and_field_history_2026_08_17.md) | master | design | 2/11 | 18% | 2.9 | — |
| [`strategy_service_expansion_overlays_config_and_wizard_2026_08_12`](./strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md) | master | refactor | 8/29 | 28% | 2.9 | — |
| [`defi_track5_coverage_mvp_backfill_2026_07_24`](./defi_track5_coverage_mvp_backfill_2026_07_24.md) | master | infra | 2/5 | 40% | 2.9 | — |
| [`codex_luna_flex_bridge_2026_08_14`](./codex_luna_flex_bridge_2026_08_14.md) | master | brand-new | 6/14 | 43% | 2.9 | — |
| [`data_pipeline_completion_2026_08_21`](./data_pipeline_completion_2026_08_21.md) | master | infra | 14/21 | 67% | 2.7 | — |
| [`tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20`](./tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md) | master | brand-new | 4/11 | 36% | 2.5 | — |
| [`w14_execution_service_exchange_version_pinning_and_cassette_drift_2026_08_20`](./w14_execution_service_exchange_version_pinning_and_cassette_drift_2026_08_20.md) | **orphan** | design | 4/13 | 31% | 2.5 | — |
| [`strategy_service_centralization_fixes_2026_08_16`](./strategy_service_centralization_fixes_2026_08_16.md) | master | infra | 20/29 | 69% | 2.5 | — |
| [`citadel_paper_batch_live_reconciliation_2026_06_19`](./citadel_paper_batch_live_reconciliation_2026_06_19.md) | master | infra | 43/46 | 93% | 2.5 | — |
| [`infra_consolidated_closeout_2026_07_25`](./infra_consolidated_closeout_2026_07_25.md) | master | infra | 1/4 | 25% | 2.4 | — |
| [`tradfi_satellite_ao_dispatch_batch15_2026_08_17`](./tradfi_satellite_ao_dispatch_batch15_2026_08_17.md) | master | infra | 2/8 | 25% | 2.4 | — |
| [`cross_cutting_closeout_observability_and_monitoring_2026_08_09`](./cross_cutting_closeout_observability_and_monitoring_2026_08_09.md) | master | infra | — | — | 2.4 | — |
| [`defi_satellite_ao_dispatch_batch14_2026_08_16`](./defi_satellite_ao_dispatch_batch14_2026_08_16.md) | master | infra | 0/8 | 0% | 2.4 | — |
| [`defi_satellite_ao_dispatch_batch18_2026_08_19`](./defi_satellite_ao_dispatch_batch18_2026_08_19.md) | master | infra | 0/9 | 0% | 2.4 | — |
| [`deployment_service_api_integration_cleanup_2026_08_18`](./deployment_service_api_integration_cleanup_2026_08_18.md) | master | infra | 5/12 | 42% | 2.3 | — |
| [`deployment_network_egress_ingress_observability_2026_08_18`](./deployment_network_egress_ingress_observability_2026_08_18.md) | master | infra | 9/14 | 64% | 2.3 | — |
| [`ui_consolidated_closeout_2026_07_30`](./ui_consolidated_closeout_2026_07_30.md) | master | infra | 2/7 | 29% | 2.3 | — |
| [`w15_execution_service_venue_adaptor_security_audit_2026_08_20`](./w15_execution_service_venue_adaptor_security_audit_2026_08_20.md) | master | research | 50/61 | 82% | 2.2 | — |
| [`predictions_ml_walk_forward_and_arb_2026_06_20`](./predictions_ml_walk_forward_and_arb_2026_06_20.md) | master | research | 5/9 | 56% | 2.1 | — |
| [`tradfi_satellite_ao_dispatch_batch16_2026_08_17`](./tradfi_satellite_ao_dispatch_batch16_2026_08_17.md) | master | infra | 1/8 | 12% | 2.1 | — |
| [`cross_venue_funding_reversion_research_2026_07_24`](./cross_venue_funding_reversion_research_2026_07_24.md) | master | research | 2/15 | 13% | 2.1 | — |
| [`tradfi_satellite_ao_dispatch_batch19_2026_08_19`](./tradfi_satellite_ao_dispatch_batch19_2026_08_19.md) | master | infra | 0/12 | 0% | 2.1 | — |
| [`sports_catalog_league_grain_only_scope_2026_07_08`](./sports_catalog_league_grain_only_scope_2026_07_08.md) | master | research | 3/7 | 43% | 2.1 | — |
| [`code_readiness_t4_execution_settlement_2026_08_19`](./code_readiness_t4_execution_settlement_2026_08_19.md) | master | refactor | 42/48 | 88% | 2.0 | — |
| [`instruments_foundation_phase0_cross_cutting_2026_07_24`](./instruments_foundation_phase0_cross_cutting_2026_07_24.md) | master | design | 9/15 | 60% | 2.0 | — |
| [`tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30`](./tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md) | master | brand-new | 4/8 | 50% | 2.0 | — |
| [`deployment_registry_firestore_p3_cutover_2026_07_14`](./deployment_registry_firestore_p3_cutover_2026_07_14.md) | master | infra | 1/5 | 20% | 1.9 | — |
| [`sports_satellite_ao_dispatch_batch14_2026_08_16`](./sports_satellite_ao_dispatch_batch14_2026_08_16.md) | master | infra | 0/10 | 0% | 1.9 | — |
| [`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`](./pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md) | master | infra | 24/30 | 80% | 1.9 | — |
| [`w22_strategy_execution_messaging_external_api_2026_08_20`](./w22_strategy_execution_messaging_external_api_2026_08_20.md) | master | brand-new | 13/17 | 76% | 1.9 | — |
| [`venue_readiness_and_registry_hardening_2026_08_16`](./venue_readiness_and_registry_hardening_2026_08_16.md) | master | infra | 21/26 | 81% | 1.8 | — |
| [`cross_cutting_strategy_execution_determinism_2026_07_26`](./cross_cutting_strategy_execution_determinism_2026_07_26.md) | master | research | 1/2 | 50% | 1.8 | — |
| [`data_status_catalogue_true_source_phase2_2026_07_24`](./data_status_catalogue_true_source_phase2_2026_07_24.md) | master | design | 0/1 | 0% | 1.8 | — |
| [`defi_cf2_cf3_legacy_canonical_backfill_2026_08_08`](./defi_cf2_cf3_legacy_canonical_backfill_2026_08_08.md) | master | research | 0/6 | 0% | 1.8 | — |
| [`defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17`](./defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md) | master | brand-new | 9/10 | 90% | 1.8 | — |
| [`defi_distinct_values_canonical_cleanup_2026_08_21`](./defi_distinct_values_canonical_cleanup_2026_08_21.md) | **orphan** | infra | 5/18 | 28% | 1.7 | — |
| [`anthropic_per_task_actual_spend_and_account_calibration_2026_08_10`](./anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md) | master | infra | 24/51 | 47% | 1.7 | — |
| [`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20`](./cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md) | master | brand-new | 27/37 | 73% | 1.6 | — |
| [`venue_e2e_wiring_finalize_2026_08_16`](./venue_e2e_wiring_finalize_2026_08_16.md) | master | infra | 0/6 | 0% | 1.6 | — |
| [`code_readiness_t1_contracts_library_externalapi_2026_08_19`](./code_readiness_t1_contracts_library_externalapi_2026_08_19.md) | master | refactor | 32/40 | 80% | 1.6 | — |
| [`data_completion_to_100_all_ag_2026_06_21`](./data_completion_to_100_all_ag_2026_06_21.md) | master | infra | 36/45 | 80% | 1.6 | — |
| [`ci_satellite_ao_dispatch_batch15_2026_08_16`](./ci_satellite_ao_dispatch_batch15_2026_08_16.md) | master | refactor | 14/25 | 56% | 1.6 | — |
| [`data_source_provenance_enforcement_2026_07_24`](./data_source_provenance_enforcement_2026_07_24.md) | master | infra | 7/19 | 37% | 1.5 | — |
| [`instruments_foundation_completeness_2026_06_24`](./instruments_foundation_completeness_2026_06_24.md) | master | design | 6/12 | 50% | 1.5 | — |
| [`infra_satellite_ao_dispatch_batch17_2026_08_16`](./infra_satellite_ao_dispatch_batch17_2026_08_16.md) | master | infra | 7/13 | 54% | 1.5 | — |
| [`legacy_bucket_dual_write_decommission_2026_07_24`](./legacy_bucket_dual_write_decommission_2026_07_24.md) | master | infra | 5/13 | 38% | 1.5 | — |
| [`service_config_ownership_and_instruction_contract_2026_08_12`](./service_config_ownership_and_instruction_contract_2026_08_12.md) | master | refactor | 33/46 | 72% | 1.4 | — |
| [`sports_closeout_track_s2_foldin_2026_07_25`](./sports_closeout_track_s2_foldin_2026_07_25.md) | master | infra | 6/12 | 50% | 1.4 | — |
| [`defi_compute_gcp_migration_2026_08_08`](./defi_compute_gcp_migration_2026_08_08.md) | master | infra | 12/18 | 67% | 1.3 | — |
| [`infra_satellite_ao_dispatch_batch18_2026_08_17`](./infra_satellite_ao_dispatch_batch18_2026_08_17.md) | master | infra | 5/11 | 45% | 1.3 | — |
| [`repo_scripts_governance_audit_2026_06_18`](./repo_scripts_governance_audit_2026_06_18.md) | master | infra | 5/11 | 45% | 1.3 | — |
| [`qg_host_adaptive_resource_governor_2026_07_14`](./qg_host_adaptive_resource_governor_2026_07_14.md) | master | infra | 27/40 | 68% | 1.3 | — |
| [`cefi_chain_relabel_migration_options_futures_2026_08_15`](./cefi_chain_relabel_migration_options_futures_2026_08_15.md) | master | design | 9/14 | 64% | 1.3 | — |
| [`sports_satellite_ao_dispatch_batch9_2026_08_04`](./sports_satellite_ao_dispatch_batch9_2026_08_04.md) | master | infra | 22/31 | 71% | 1.3 | — |
| [`data_completion_prediction_2026_07_15`](./data_completion_prediction_2026_07_15.md) | master | infra | 9/23 | 39% | 1.2 | — |
| [`defi_live_poller_phased_build_2026_08_15`](./defi_live_poller_phased_build_2026_08_15.md) | master | design | 3/4 | 75% | 1.2 | — |
| [`deployment_api_true_catalogue_expected_universe_projection_ao_dispatch_2026_08_16`](./deployment_api_true_catalogue_expected_universe_projection_ao_dispatch_2026_08_16.md) | master | infra | 0/2 | 0% | 1.2 | — |
| [`infra_satellite_ao_dispatch_batch1_2026_08_21`](./infra_satellite_ao_dispatch_batch1_2026_08_21.md) | **orphan** | infra | 0/2 | 0% | 1.2 | — |
| [`sports_taxonomy_p2_consumer_inventory_2026_08_12`](./sports_taxonomy_p2_consumer_inventory_2026_08_12.md) | master | research | — | — | 1.2 | — |
| [`strategy_service_centralization_fixes_finalize_2026_08_16`](./strategy_service_centralization_fixes_finalize_2026_08_16.md) | master | infra | 0/4 | 0% | 1.2 | — |
| [`ui_satellite_ao_dispatch_batch5_2026_08_21`](./ui_satellite_ao_dispatch_batch5_2026_08_21.md) | **orphan** | infra | 0/1 | 0% | 1.2 | — |
| [`venue_smoke_test_bar_finalize_2026_08_16`](./venue_smoke_test_bar_finalize_2026_08_16.md) | master | infra | 0/6 | 0% | 1.2 | — |
| [`epic_taxonomy_restructure_and_html_reconcile_2026_08_18`](./epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md) | README | brand-new | 24/28 | 86% | 1.1 | — |
| [`sports_satellite_ao_dispatch_batch15_2026_08_17`](./sports_satellite_ao_dispatch_batch15_2026_08_17.md) | master | infra | 4/11 | 36% | 1.1 | — |
| [`nick_ai_platform_disclosure_artifact_2026_08_16`](./nick_ai_platform_disclosure_artifact_2026_08_16.md) | master | design | 9/13 | 69% | 1.1 | — |
| [`cefi_consolidated_closeout_2026_07_18`](./cefi_consolidated_closeout_2026_07_18.md) | master | infra | 30/36 | 83% | 1.1 | — |
| [`defi_satellite_ao_dispatch_batch16_2026_08_17`](./defi_satellite_ao_dispatch_batch16_2026_08_17.md) | master | infra | 3/9 | 33% | 1.1 | — |
| [`tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16`](./tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md) | master | infra | 1/3 | 33% | 1.1 | — |
| [`prediction_satellite_ao_dispatch_batch12_2026_08_17`](./prediction_satellite_ao_dispatch_batch12_2026_08_17.md) | master | research | 1/4 | 25% | 1.0 | — |
| [`asset_class_to_asset_group_rename_2026_07_21`](./asset_class_to_asset_group_rename_2026_07_21.md) | master | refactor | 1/7 | 14% | 1.0 | — |
| [`prediction_capture_incident_remediation_2026_07_06`](./prediction_capture_incident_remediation_2026_07_06.md) | master | infra | 15/22 | 68% | 1.0 | — |
| [`cross_ag_live_capture_parity_2026_08_14`](./cross_ag_live_capture_parity_2026_08_14.md) | master | infra | 13/19 | 68% | 1.0 | — |
| [`w14_execution_service_exchange_version_pinning_and_cassette_drift_2026_08_20_finalize`](./w14_execution_service_exchange_version_pinning_and_cassette_drift_2026_08_20_finalize.md) | **orphan** | infra | 0/4 | 0% | 1.0 | — |
| [`w15_execution_service_venue_adaptor_security_audit_2026_08_20_finalize`](./w15_execution_service_venue_adaptor_security_audit_2026_08_20_finalize.md) | master | infra | 0/3 | 0% | 1.0 | — |
| [`w22_strategy_execution_messaging_external_api_2026_08_20_finalize`](./w22_strategy_execution_messaging_external_api_2026_08_20_finalize.md) | master | infra | 0/4 | 0% | 1.0 | — |
| [`w_execution_orchestrator_oms_persistence_impl_2026_08_21_finalize`](./w_execution_orchestrator_oms_persistence_impl_2026_08_21_finalize.md) | **orphan** | infra | 0/4 | 0% | 1.0 | — |
| [`cefi_satellite_ao_dispatch_batch20_2026_08_16`](./cefi_satellite_ao_dispatch_batch20_2026_08_16.md) | master | refactor | 5/16 | 31% | 1.0 | — |
| [`deployment_registry_firestore_p5_verify_2026_07_14`](./deployment_registry_firestore_p5_verify_2026_07_14.md) | master | infra | 2/5 | 40% | 1.0 | — |
| [`prediction_phase_e_football_arb_live_2026_07_24`](./prediction_phase_e_football_arb_live_2026_07_24.md) | master | infra | 3/5 | 60% | 1.0 | — |
| [`tradfi_satellite_ao_dispatch_batch20_2026_08_21`](./tradfi_satellite_ao_dispatch_batch20_2026_08_21.md) | **orphan** | infra | 0/2 | 0% | 1.0 | — |
| [`walkthrough_feedback_remediation_2026_08_21`](./walkthrough_feedback_remediation_2026_08_21.md) | **orphan** | refactor | 31/38 | 82% | 0.9 | — |
| [`prediction_phase_d_formal_smoke_and_backfill_2026_07_24`](./prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md) | master | infra | 6/11 | 55% | 0.9 | — |
| [`prediction_satellite_ao_dispatch_batch15_2026_08_19`](./prediction_satellite_ao_dispatch_batch15_2026_08_19.md) | master | design | 0/3 | 0% | 0.9 | — |
| [`sports_prediction_mvp_writetime_precompute_2026_07_24`](./sports_prediction_mvp_writetime_precompute_2026_07_24.md) | master | design | 0/1 | 0% | 0.9 | — |
| [`bucket_fold_portfolio_state_2026_07_17`](./bucket_fold_portfolio_state_2026_07_17.md) | master | infra | 5/8 | 62% | 0.9 | — |
| [`infra_satellite_ao_dispatch_batch2_2026_08_21`](./infra_satellite_ao_dispatch_batch2_2026_08_21.md) | **orphan** | refactor | 0/15 | 0% | 0.9 | — |
| [`sports_venue_smoke_batch1_2026_08_20`](./sports_venue_smoke_batch1_2026_08_20.md) | **orphan** | infra | 2/5 | 40% | 0.9 | — |
| [`tradfi_venue_smoke_batch1_2026_08_20`](./tradfi_venue_smoke_batch1_2026_08_20.md) | **orphan** | infra | 2/5 | 40% | 0.9 | — |
| [`cross_cutting_satellite_ao_dispatch_batch14_2026_08_17`](./cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md) | master | infra | 8/14 | 57% | 0.9 | — |
| [`cefi_venue_smoke_batch1_2026_08_20_finalize`](./cefi_venue_smoke_batch1_2026_08_20_finalize.md) | **orphan** | infra | 0/3 | 0% | 0.8 | — |
| [`cross_cutting_satellite_ao_dispatch_batch19_2026_08_19`](./cross_cutting_satellite_ao_dispatch_batch19_2026_08_19.md) | master | infra | 0/6 | 0% | 0.8 | — |
| [`defi_satellite_ao_dispatch_batch19_2026_08_21`](./defi_satellite_ao_dispatch_batch19_2026_08_21.md) | **orphan** | infra | 0/3 | 0% | 0.8 | — |
| [`defi_venue_smoke_batch1_2026_08_20_finalize`](./defi_venue_smoke_batch1_2026_08_20_finalize.md) | **orphan** | infra | 0/3 | 0% | 0.8 | — |
| [`deployment_service_api_integration_cleanup_finalize_2026_08_18`](./deployment_service_api_integration_cleanup_finalize_2026_08_18.md) | master | infra | 0/3 | 0% | 0.8 | — |
| [`prediction_venue_smoke_batch1_2026_08_20_finalize`](./prediction_venue_smoke_batch1_2026_08_20_finalize.md) | **orphan** | infra | 0/3 | 0% | 0.8 | — |
| [`sports_venue_smoke_batch1_2026_08_20_finalize`](./sports_venue_smoke_batch1_2026_08_20_finalize.md) | **orphan** | infra | 0/3 | 0% | 0.8 | — |
| [`tradfi_venue_smoke_batch1_2026_08_20_finalize`](./tradfi_venue_smoke_batch1_2026_08_20_finalize.md) | **orphan** | infra | 0/3 | 0% | 0.8 | — |
| [`lazy_scoped_loading_refactor_2026_08_16`](./lazy_scoped_loading_refactor_2026_08_16.md) | master | refactor | 6/8 | 75% | 0.8 | — |
| [`mdps_adapter_protocol_polars_migration_2026_08_22`](./mdps_adapter_protocol_polars_migration_2026_08_22.md) | **orphan** | refactor | 0/10 | 0% | 0.8 | — |
| [`prediction_phase_c_data_status_ui_2026_07_24`](./prediction_phase_c_data_status_ui_2026_07_24.md) | master | infra | 2/4 | 50% | 0.8 | — |
| [`prediction_satellite_ao_dispatch_batch14_2026_08_19`](./prediction_satellite_ao_dispatch_batch14_2026_08_19.md) | master | infra | 0/4 | 0% | 0.8 | — |
| [`sports_taxonomy_p3_consumers_2026_08_08`](./sports_taxonomy_p3_consumers_2026_08_08.md) | master | infra | 16/18 | 89% | 0.8 | — |
| [`sports_venue_vocab_and_league_id_delete_ao_dispatch_2026_08_16`](./sports_venue_vocab_and_league_id_delete_ao_dispatch_2026_08_16.md) | master | infra | 1/2 | 50% | 0.8 | — |
| [`bucket_fold_execution_strategy_2026_07_17`](./bucket_fold_execution_strategy_2026_07_17.md) | master | infra | 6/9 | 67% | 0.8 | — |
| [`cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28`](./cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md) | master | infra | 4/6 | 67% | 0.8 | — |
| [`defi_venue_smoke_batch1_2026_08_20`](./defi_venue_smoke_batch1_2026_08_20.md) | **orphan** | infra | 7/15 | 47% | 0.8 | — |
| [`cross_repo_duplication_cleanup_2026_08_21`](./cross_repo_duplication_cleanup_2026_08_21.md) | **orphan** | refactor | 17/46 | 37% | 0.8 | — |
| [`colocated_feature_pipeline_in_memory_handoff_2026_06_21`](./colocated_feature_pipeline_in_memory_handoff_2026_06_21.md) | master | design | 3/4 | 75% | 0.8 | — |
| [`cross_cutting_satellite_ao_dispatch_batch22_2026_08_21`](./cross_cutting_satellite_ao_dispatch_batch22_2026_08_21.md) | **orphan** | infra | 1/4 | 25% | 0.8 | — |
| [`data_status_cell_grid_rearchitecture_2026_07_18`](./data_status_cell_grid_rearchitecture_2026_07_18.md) | master | design | 6/8 | 75% | 0.8 | — |
| [`grok_gemini_translation_proxy_2026_08_14`](./grok_gemini_translation_proxy_2026_08_14.md) | master | brand-new | 13/16 | 81% | 0.8 | — |
| [`execution_service_policy_and_fill_model_gaps_2026_08_19`](./execution_service_policy_and_fill_model_gaps_2026_08_19.md) | master | refactor | 8/15 | 53% | 0.7 | — |
| [`data_completion_tradfi_2026_07_15`](./data_completion_tradfi_2026_07_15.md) | master | infra | 24/38 | 63% | 0.7 | — |
| [`prediction_venue_smoke_batch1_2026_08_20`](./prediction_venue_smoke_batch1_2026_08_20.md) | **orphan** | infra | 3/6 | 50% | 0.7 | — |
| [`slot0_self_cleaning_daemon_2026_08_18`](./slot0_self_cleaning_daemon_2026_08_18.md) | master | infra | 4/10 | 40% | 0.7 | — |
| [`tradfi_registry_coverage_and_ao_readiness_2026_07_25`](./tradfi_registry_coverage_and_ao_readiness_2026_07_25.md) | master | infra | 4/15 | 27% | 0.7 | — |
| [`tradfi_chain_bundle_reverse_derivation_ao_dispatch_2026_08_16`](./tradfi_chain_bundle_reverse_derivation_ao_dispatch_2026_08_16.md) | master | infra | 0/1 | 0% | 0.7 | — |
| [`prediction_phase_ab_residuals_2026_07_24`](./prediction_phase_ab_residuals_2026_07_24.md) | master | infra | 15/19 | 79% | 0.7 | — |
| [`defi_pipeline_e2e_and_coverage_validation_2026_06_20`](./defi_pipeline_e2e_and_coverage_validation_2026_06_20.md) | master | infra | 5/6 | 83% | 0.7 | — |
| [`github_actions_operator_gated_followups_2026_07_17`](./github_actions_operator_gated_followups_2026_07_17.md) | master | infra | 20/24 | 83% | 0.7 | — |
| [`mtds_is_rate_limit_pagination_2026_08_21`](./mtds_is_rate_limit_pagination_2026_08_21.md) | **orphan** | brand-new | 1/3 | 33% | 0.7 | — |
| [`live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31`](./live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md) | master | infra | 8/11 | 73% | 0.7 | — |
| [`venue_capability_route_axis_and_cross_ag_declarations_2026_08_14`](./venue_capability_route_axis_and_cross_ag_declarations_2026_08_14.md) | master | infra | 19/22 | 86% | 0.7 | — |
| [`instruments_store_cf_canonicalization_single_walk_2026_07_24`](./instruments_store_cf_canonicalization_single_walk_2026_07_24.md) | master | infra | 19/26 | 73% | 0.6 | — |
| [`cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize`](./cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize.md) | master | infra | 0/4 | 0% | 0.6 | — |
| [`defi_instruments_store_v9_gate_c_apply_write_2026_08_16`](./defi_instruments_store_v9_gate_c_apply_write_2026_08_16.md) | master | infra | 0/3 | 0% | 0.6 | — |
| [`sports_taxonomy_p3_consumers_2026_08_08_finalize`](./sports_taxonomy_p3_consumers_2026_08_08_finalize.md) | master | infra | 0/6 | 0% | 0.6 | — |
| [`l2_book_microstructure_capture_2026_07_13`](./l2_book_microstructure_capture_2026_07_13.md) | master | brand-new | 7/8 | 88% | 0.6 | — |
| [`infra_ops_residual_migration_verification_2026_07_24`](./infra_ops_residual_migration_verification_2026_07_24.md) | master | design | 6/9 | 67% | 0.6 | — |
| [`artifact_pipeline_observability_2026_07_17`](./artifact_pipeline_observability_2026_07_17.md) | master | infra | 47/50 | 94% | 0.6 | — |
| [`cefi_track2_coverage_backfill_checkpoints_2026_07_25`](./cefi_track2_coverage_backfill_checkpoints_2026_07_25.md) | master | infra | 3/6 | 50% | 0.6 | — |
| [`cross_cutting_satellite_ao_dispatch_batch20_2026_08_19`](./cross_cutting_satellite_ao_dispatch_batch20_2026_08_19.md) | master | infra | 0/4 | 0% | 0.6 | — |
| [`solana_dex_pool_swaps_indexer_2026_08_08`](./solana_dex_pool_swaps_indexer_2026_08_08.md) | master | brand-new | 2/5 | 40% | 0.6 | — |
| [`sports_league_alias_dispatch_anomaly_investigation_ao_dispatch_2026_08_16`](./sports_league_alias_dispatch_anomaly_investigation_ao_dispatch_2026_08_16.md) | master | research | 0/1 | 0% | 0.6 | — |
| [`data_completion_defi_2026_07_15`](./data_completion_defi_2026_07_15.md) | master | infra | 39/55 | 71% | 0.6 | — |
| [`tradfi_manifest_content_recovery_completion_2026_07_24`](./tradfi_manifest_content_recovery_completion_2026_07_24.md) | master | infra | 22/25 | 88% | 0.6 | — |
| [`prediction_cross_venue_arb_and_coverage_2026_07_24`](./prediction_cross_venue_arb_and_coverage_2026_07_24.md) | master | brand-new | 26/28 | 93% | 0.6 | — |
| [`data_pipeline_ag_residual_backfill_decisions_2026_07_24`](./data_pipeline_ag_residual_backfill_decisions_2026_07_24.md) | master | infra | 6/9 | 67% | 0.5 | — |
| [`ao_consolidated_closeout_2026_08_12`](./ao_consolidated_closeout_2026_08_12.md) | master | infra | 4/6 | 67% | 0.5 | — |
| [`data_pipeline_alert_storm_ops_ao_dispatch_2026_08_15`](./data_pipeline_alert_storm_ops_ao_dispatch_2026_08_15.md) | master | infra | 4/6 | 67% | 0.5 | — |
| [`sports_odds_writer_flip_and_trades_path_retirement_2026_08_15`](./sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md) | master | infra | 10/12 | 83% | 0.5 | — |
| [`empty_confirmed_and_coverage_correctness_audit_2026_08_15`](./empty_confirmed_and_coverage_correctness_audit_2026_08_15.md) | master | research | 26/28 | 93% | 0.5 | — |
| [`capability_wizard_client_lite_and_ci_regen_followup_2026_07_24`](./capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md) | master | brand-new | 1/2 | 50% | 0.5 | — |
| [`ci_satellite_ao_dispatch_batch15_2026_08_16_finalize`](./ci_satellite_ao_dispatch_batch15_2026_08_16_finalize.md) | master | infra | 0/3 | 0% | 0.5 | — |
| [`cross_cutting_satellite_ao_dispatch_batch15_2026_08_17_finalize`](./cross_cutting_satellite_ao_dispatch_batch15_2026_08_17_finalize.md) | master | infra | 0/4 | 0% | 0.5 | — |
| [`infra_satellite_ao_dispatch_batch17_finalize_2026_08_16`](./infra_satellite_ao_dispatch_batch17_finalize_2026_08_16.md) | master | infra | 0/3 | 0% | 0.5 | — |
| [`cross_cutting_satellite_ao_dispatch_batch18_2026_08_19`](./cross_cutting_satellite_ao_dispatch_batch18_2026_08_19.md) | master | infra | 4/10 | 40% | 0.5 | — |
| [`ao_satellite_ao_dispatch_batch4_2026_08_21`](./ao_satellite_ao_dispatch_batch4_2026_08_21.md) | **orphan** | infra | 0/2 | 0% | 0.5 | — |
| [`cefi_chain_drop_root_cause_and_heavy_io_vm_rule_finalize_2026_08_08`](./cefi_chain_drop_root_cause_and_heavy_io_vm_rule_finalize_2026_08_08.md) | master | infra | 0/2 | 0% | 0.5 | — |
| [`ci_satellite_ao_dispatch_batch17_2026_08_21`](./ci_satellite_ao_dispatch_batch17_2026_08_21.md) | **orphan** | infra | 0/1 | 0% | 0.5 | — |
| [`defi_satellite_ao_dispatch_batch11_2026_08_09_finalize`](./defi_satellite_ao_dispatch_batch11_2026_08_09_finalize.md) | master | infra | 0/3 | 0% | 0.5 | — |
| [`sports_closeout_track_s2_foldin_2026_07_25_finalize`](./sports_closeout_track_s2_foldin_2026_07_25_finalize.md) | master | infra | 0/3 | 0% | 0.5 | — |
| [`sports_taxonomy_p4_backfill_2026_08_08_finalize`](./sports_taxonomy_p4_backfill_2026_08_08_finalize.md) | master | infra | 0/6 | 0% | 0.5 | — |
| [`tradfi_satellite_ao_dispatch_batch9_2026_08_09`](./tradfi_satellite_ao_dispatch_batch9_2026_08_09.md) | master | infra | 1/2 | 50% | 0.5 | — |
| [`lst_rate_honest_coverage_2026_07_21`](./lst_rate_honest_coverage_2026_07_21.md) | master | infra | 19/21 | 90% | 0.5 | — |
| [`mtds_file_size_refactor_2026_06_08`](./mtds_file_size_refactor_2026_06_08.md) | master | refactor | 7/9 | 78% | 0.4 | — |
| [`mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24`](./mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md) | master | infra | 31/38 | 82% | 0.4 | — |
| [`fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06`](./fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md) | master | infra | 10/11 | 91% | 0.4 | — |
| [`test_impact_fleet_wide_measurement_and_rollout_2026_08_03`](./test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md) | master | research | 9/11 | 82% | 0.4 | — |
| [`sports_odds_bookmaker_coverage_enumeration_2026_06_20`](./sports_odds_bookmaker_coverage_enumeration_2026_06_20.md) | master | brand-new | 6/7 | 86% | 0.4 | — |
| [`walkthrough_feedback_checkpoint_2026_08_21`](./walkthrough_feedback_checkpoint_2026_08_21.md) | **orphan** | refactor | 4/7 | 57% | 0.4 | — |
| [`deepseek_claude_blended_provider_routing_2026_07_28`](./deepseek_claude_blended_provider_routing_2026_07_28.md) | master | infra | 42/51 | 82% | 0.4 | — |
| [`cefi_satellite_ao_dispatch_batch20_2026_08_16_finalize`](./cefi_satellite_ao_dispatch_batch20_2026_08_16_finalize.md) | master | infra | 0/3 | 0% | 0.4 | — |
| [`ci_satellite_ao_dispatch_batch13_2026_08_13_finalize`](./ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md) | master | infra | 0/3 | 0% | 0.4 | — |
| [`ci_satellite_ao_dispatch_batch16_2026_08_21_finalize`](./ci_satellite_ao_dispatch_batch16_2026_08_21_finalize.md) | **orphan** | infra | 0/3 | 0% | 0.4 | — |
| [`cross_cutting_satellite_ao_dispatch_batch13_2026_08_13_finalize`](./cross_cutting_satellite_ao_dispatch_batch13_2026_08_13_finalize.md) | master | infra | 0/3 | 0% | 0.4 | — |
| [`cross_cutting_satellite_ao_dispatch_batch14_2026_08_17_finalize`](./cross_cutting_satellite_ao_dispatch_batch14_2026_08_17_finalize.md) | master | infra | 0/3 | 0% | 0.4 | — |
| [`defi_satellite_ao_dispatch_batch14_2026_08_16_finalize`](./defi_satellite_ao_dispatch_batch14_2026_08_16_finalize.md) | master | infra | 0/3 | 0% | 0.4 | — |
| [`infra_satellite_ao_dispatch_batch2_finalize_2026_08_21`](./infra_satellite_ao_dispatch_batch2_finalize_2026_08_21.md) | **orphan** | infra | 0/3 | 0% | 0.4 | — |
| [`prediction_satellite_ao_dispatch_batch11_2026_08_13_finalize`](./prediction_satellite_ao_dispatch_batch11_2026_08_13_finalize.md) | master | infra | 0/3 | 0% | 0.4 | — |
| [`prediction_satellite_ao_dispatch_batch16_2026_08_21`](./prediction_satellite_ao_dispatch_batch16_2026_08_21.md) | **orphan** | refactor | 0/3 | 0% | 0.4 | — |
| [`sports_venue_e2e_batch1_2026_08_16_finalize`](./sports_venue_e2e_batch1_2026_08_16_finalize.md) | master | infra | 0/3 | 0% | 0.4 | — |
| [`tradfi_satellite_ao_dispatch_batch13_2026_08_13_finalize`](./tradfi_satellite_ao_dispatch_batch13_2026_08_13_finalize.md) | master | infra | 0/3 | 0% | 0.4 | — |
| [`ao_satellite_ao_dispatch_batch14_2026_08_09`](./ao_satellite_ao_dispatch_batch14_2026_08_09.md) | master | infra | — | — | 0.4 | — |
| [`cefi_chain_relabel_migration_options_futures_2026_08_15_finalize`](./cefi_chain_relabel_migration_options_futures_2026_08_15_finalize.md) | master | infra | 0/4 | 0% | 0.4 | — |
| [`cefi_consolidated_closeout_aggregated_sources_2026_07_24`](./cefi_consolidated_closeout_aggregated_sources_2026_07_24.md) | master | infra | 0/1 | 0% | 0.4 | — |
| [`cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25`](./cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md) | master | infra | 0/4 | 0% | 0.4 | — |
| [`codex_mcp_tool_use_bridge_2026_08_18`](./codex_mcp_tool_use_bridge_2026_08_18.md) | master | brand-new | 9/10 | 90% | 0.4 | — |
| [`data_pipeline_alerts_batch_remediation_2026_07_15`](./data_pipeline_alerts_batch_remediation_2026_07_15.md) | master | infra | 3/4 | 75% | 0.4 | — |
| [`defi_compute_gcp_migration_2026_08_08_finalize_2026_08_08`](./defi_compute_gcp_migration_2026_08_08_finalize_2026_08_08.md) | master | infra | 0/4 | 0% | 0.4 | — |
| [`defi_distinct_values_zero_noncanonical_dispatch_2026_08_04_finalize`](./defi_distinct_values_zero_noncanonical_dispatch_2026_08_04_finalize.md) | master | infra | 0/2 | 0% | 0.4 | — |
| [`defi_hyperliquid_kprefix_coin_casing_fix_ao_dispatch_2026_08_16`](./defi_hyperliquid_kprefix_coin_casing_fix_ao_dispatch_2026_08_16.md) | master | infra | 0/1 | 0% | 0.4 | — |
| [`infra_satellite_ao_dispatch_batch20_2026_08_18`](./infra_satellite_ao_dispatch_batch20_2026_08_18.md) | master | infra | 0/1 | 0% | 0.4 | — |
| [`nick_ai_platform_readiness_remediation_finalize_2026_08_16`](./nick_ai_platform_readiness_remediation_finalize_2026_08_16.md) | master | infra | 2/4 | 50% | 0.4 | — |
| [`sports_track_h_denominator_prereqs_2026_07_28`](./sports_track_h_denominator_prereqs_2026_07_28.md) | master | infra | 1/2 | 50% | 0.4 | — |
| [`sports_venue_rename_attempted_at_trace_ao_dispatch_2026_08_16`](./sports_venue_rename_attempted_at_trace_ao_dispatch_2026_08_16.md) | master | research | 0/1 | 0% | 0.4 | — |
| [`tradfi_satellite_ao_dispatch_batch15_2026_08_17_finalize`](./tradfi_satellite_ao_dispatch_batch15_2026_08_17_finalize.md) | master | infra | 0/4 | 0% | 0.4 | — |
| [`tradfi_satellite_ao_dispatch_batch16_2026_08_17_finalize`](./tradfi_satellite_ao_dispatch_batch16_2026_08_17_finalize.md) | master | infra | 0/4 | 0% | 0.4 | — |
| [`ci_satellite_ao_dispatch_batch16_2026_08_21`](./ci_satellite_ao_dispatch_batch16_2026_08_21.md) | **orphan** | refactor | 1/3 | 33% | 0.4 | — |
| [`daily_trading_analyst_llm_job_design_2026_07_29`](./daily_trading_analyst_llm_job_design_2026_07_29.md) | master | design | 2/6 | 33% | 0.4 | — |
| [`pipeline_mode_partition_migration_2026_06_01`](./pipeline_mode_partition_migration_2026_06_01.md) | master | infra | 2/3 | 67% | 0.4 | — |
| [`sports_predictions_live_mode_activation_readiness_2026_07_21`](./sports_predictions_live_mode_activation_readiness_2026_07_21.md) | master | design | 4/6 | 67% | 0.4 | — |
| [`tradfi_satellite_ao_dispatch_batch13_2026_08_13`](./tradfi_satellite_ao_dispatch_batch13_2026_08_13.md) | master | refactor | 17/20 | 85% | 0.4 | — |
| [`bucket_fold_features_2026_07_17`](./bucket_fold_features_2026_07_17.md) | master | infra | 8/9 | 89% | 0.4 | — |
| [`ci_pipeline_speed_and_cost_redesign_2026_08_05`](./ci_pipeline_speed_and_cost_redesign_2026_08_05.md) | master | infra | 8/9 | 89% | 0.4 | — |
| [`ag_closeout_audit_rollout_2026_07_25`](./ag_closeout_audit_rollout_2026_07_25.md) | master | research | 13/14 | 93% | 0.3 | — |
| [`ao_satellite_ao_dispatch_batch22_2026_08_16`](./ao_satellite_ao_dispatch_batch22_2026_08_16.md) | master | infra | 2/3 | 67% | 0.3 | — |
| [`manifest_v9_residual_2026_08_15`](./manifest_v9_residual_2026_08_15.md) | master | infra | 1/6 | 17% | 0.3 | — |
| [`mvp_could_exist_rollup_dual_scope_2026_08_12`](./mvp_could_exist_rollup_dual_scope_2026_08_12.md) | master | design | 8/9 | 89% | 0.3 | — |
| [`stash_pile_workspace_cleanup_2026_06_03`](./stash_pile_workspace_cleanup_2026_06_03.md) | master | infra | 13/18 | 72% | 0.3 | — |
| [`bucket_fold_ml_2026_07_17`](./bucket_fold_ml_2026_07_17.md) | master | infra | 8/10 | 80% | 0.3 | — |
| [`defi_archetype_catalog_identity_extension_ao_dispatch_2026_08_16`](./defi_archetype_catalog_identity_extension_ao_dispatch_2026_08_16.md) | master | refactor | 4/5 | 80% | 0.3 | — |
| [`prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize`](./prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize.md) | master | infra | 0/3 | 0% | 0.3 | — |
| [`quality_gates_quickmerge_timing_baseline_2026_07_31_finalize_2026_08_08`](./quality_gates_quickmerge_timing_baseline_2026_07_31_finalize_2026_08_08.md) | master | infra | 0/2 | 0% | 0.3 | — |
| [`sports_satellite_ao_dispatch_batch15_2026_08_17_finalize`](./sports_satellite_ao_dispatch_batch15_2026_08_17_finalize.md) | master | infra | 0/3 | 0% | 0.3 | — |
| [`tradfi_satellite_ao_dispatch_batch18_2026_08_19`](./tradfi_satellite_ao_dispatch_batch18_2026_08_19.md) | master | infra | 0/2 | 0% | 0.3 | — |
| [`tradfi_satellite_ao_dispatch_batch9_2026_08_09_finalize`](./tradfi_satellite_ao_dispatch_batch9_2026_08_09_finalize.md) | master | infra | 0/3 | 0% | 0.3 | — |
| [`ao_human_fleet_integration_2026_08_15`](./ao_human_fleet_integration_2026_08_15.md) | master | infra | 35/38 | 92% | 0.3 | — |
| [`strategy_archetype_latency_deployment_profile_execution_2026_08_10`](./strategy_archetype_latency_deployment_profile_execution_2026_08_10.md) | master | brand-new | 12/13 | 92% | 0.3 | — |
| [`instruments_tradfi_g1_g5_gate_execution_2026_07_24`](./instruments_tradfi_g1_g5_gate_execution_2026_07_24.md) | master | design | 31/33 | 94% | 0.3 | — |
| [`deployment_api_unauthenticated_prod_p0_2026_08_10`](./deployment_api_unauthenticated_prod_p0_2026_08_10.md) | master | infra | 10/16 | 62% | 0.3 | — |
| [`cefi_satellite_ao_dispatch_batch23_2026_08_21`](./cefi_satellite_ao_dispatch_batch23_2026_08_21.md) | **orphan** | refactor | 0/1 | 0% | 0.3 | — |
| [`infra_satellite_ao_dispatch_batch18_2026_08_17_finalize`](./infra_satellite_ao_dispatch_batch18_2026_08_17_finalize.md) | master | infra | 0/3 | 0% | 0.3 | — |
| [`sports_fixtures_browser_single_catalogue_source_2026_07_24`](./sports_fixtures_browser_single_catalogue_source_2026_07_24.md) | master | design | 2/3 | 67% | 0.3 | — |
| [`tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16`](./tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16.md) | master | infra | 0/1 | 0% | 0.3 | — |
| [`ao_death_diagnostics_compaction_kpis_and_sequential_carveout_2026_08_15`](./ao_death_diagnostics_compaction_kpis_and_sequential_carveout_2026_08_15.md) | master | infra | 9/11 | 82% | 0.3 | — |
| [`data_pipeline_self_healing_completion_residual_2026_07_24`](./data_pipeline_self_healing_completion_residual_2026_07_24.md) | master | infra | 18/21 | 86% | 0.3 | — |
| [`w_execution_orchestrator_oms_persistence_impl_2026_08_21`](./w_execution_orchestrator_oms_persistence_impl_2026_08_21.md) | system_readiness_master | infra | 13/14 | 93% | 0.3 | — |
| [`sports_satellite_ao_dispatch_batch14_2026_08_16_finalize`](./sports_satellite_ao_dispatch_batch14_2026_08_16_finalize.md) | master | infra | 0/11 | 0% | 0.3 | — |
| [`defi_satellite_ao_dispatch_batch11_2026_08_09`](./defi_satellite_ao_dispatch_batch11_2026_08_09.md) | master | infra | 12/13 | 92% | 0.3 | — |
| [`bucket_estate_consolidation_closeout_2026_07_24`](./bucket_estate_consolidation_closeout_2026_07_24.md) | master | infra | 5/6 | 83% | 0.3 | — |
| [`cefi_4surface_migration_execution_log_2026_07_24`](./cefi_4surface_migration_execution_log_2026_07_24.md) | master | infra | 8/9 | 89% | 0.3 | — |
| [`ci_vm_exposure_remediation_2026_08_06`](./ci_vm_exposure_remediation_2026_08_06.md) | master | infra | 2/3 | 67% | 0.3 | — |
| [`is_catalogue_g1_root_audit_log_2026_07_24`](./is_catalogue_g1_root_audit_log_2026_07_24.md) | master | design | 5/9 | 56% | 0.3 | — |
| [`master_data_canonicalisation_migration_catalogue_2026_06_07`](./master_data_canonicalisation_migration_catalogue_2026_06_07.md) | master | design | 26/28 | 93% | 0.3 | — |
| [`sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24`](./sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md) | master | design | 27/28 | 96% | 0.3 | — |
| [`defi_track01_per_instrument_and_canon_id_2026_07_24`](./defi_track01_per_instrument_and_canon_id_2026_07_24.md) | master | infra | 23/25 | 92% | 0.3 | — |
| [`citadel_satellite_ao_dispatch_batch2_2026_08_19`](./citadel_satellite_ao_dispatch_batch2_2026_08_19.md) | master | infra | 1/2 | 50% | 0.2 | — |
| [`cross_cutting_satellite_ao_dispatch_batch18_2026_08_19_finalize`](./cross_cutting_satellite_ao_dispatch_batch18_2026_08_19_finalize.md) | master | infra | 0/1 | 0% | 0.2 | — |
| [`cross_cutting_satellite_ao_dispatch_batch19_2026_08_19_finalize`](./cross_cutting_satellite_ao_dispatch_batch19_2026_08_19_finalize.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`cross_cutting_satellite_ao_dispatch_batch20_2026_08_19_finalize`](./cross_cutting_satellite_ao_dispatch_batch20_2026_08_19_finalize.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`cross_cutting_satellite_ao_dispatch_batch21_2026_08_21_finalize`](./cross_cutting_satellite_ao_dispatch_batch21_2026_08_21_finalize.md) | **orphan** | infra | 0/1 | 0% | 0.2 | — |
| [`cross_cutting_satellite_ao_dispatch_batch22_2026_08_21_finalize`](./cross_cutting_satellite_ao_dispatch_batch22_2026_08_21_finalize.md) | **orphan** | infra | 0/1 | 0% | 0.2 | — |
| [`defi_satellite_ao_dispatch_batch2_2026_07_26_finalize`](./defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md) | master | infra | 2/4 | 50% | 0.2 | — |
| [`mvp_could_exist_rollup_dual_scope_2026_08_12_finalize`](./mvp_could_exist_rollup_dual_scope_2026_08_12_finalize.md) | **orphan** | infra | 0/2 | 0% | 0.2 | — |
| [`w_state_recovery_real_wiring_2026_08_20_finalize`](./w_state_recovery_real_wiring_2026_08_20_finalize.md) | **orphan** | infra | 3/4 | 75% | 0.2 | — |
| [`content_derived_backlog_task_ids_2026_08_08`](./content_derived_backlog_task_ids_2026_08_08.md) | master | refactor | 17/20 | 85% | 0.2 | — |
| [`ao_satellite_ao_dispatch_batch25_finalize_2026_08_19`](./ao_satellite_ao_dispatch_batch25_finalize_2026_08_19.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`cefi_satellite_ao_dispatch_batch21_2026_08_17_finalize`](./cefi_satellite_ao_dispatch_batch21_2026_08_17_finalize.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`cefi_venue_smoke_batch1_2026_08_20`](./cefi_venue_smoke_batch1_2026_08_20.md) | **orphan** | infra | 5/6 | 83% | 0.2 | — |
| [`compute_flexible_cud_sizing_analysis_2026_08_16`](./compute_flexible_cud_sizing_analysis_2026_08_16.md) | master | research | 0/2 | 0% | 0.2 | — |
| [`data_status_cell_grid_rearchitecture_finalize_2026_08_21`](./data_status_cell_grid_rearchitecture_finalize_2026_08_21.md) | **orphan** | infra | 0/3 | 0% | 0.2 | — |
| [`deployment_api_unauthenticated_prod_p0_2026_08_10_finalize`](./deployment_api_unauthenticated_prod_p0_2026_08_10_finalize.md) | master | infra | 0/4 | 0% | 0.2 | — |
| [`prediction_satellite_ao_dispatch_batch12_2026_08_17_finalize`](./prediction_satellite_ao_dispatch_batch12_2026_08_17_finalize.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`prediction_satellite_ao_dispatch_batch14_2026_08_19_finalize`](./prediction_satellite_ao_dispatch_batch14_2026_08_19_finalize.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`prediction_satellite_ao_dispatch_batch15_2026_08_19_finalize`](./prediction_satellite_ao_dispatch_batch15_2026_08_19_finalize.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`sports_satellite_ao_dispatch_batch16_2026_08_17`](./sports_satellite_ao_dispatch_batch16_2026_08_17.md) | master | infra | 1/2 | 50% | 0.2 | — |
| [`sports_satellite_ao_dispatch_batch16_2026_08_17_finalize`](./sports_satellite_ao_dispatch_batch16_2026_08_17_finalize.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`sports_satellite_ao_dispatch_batch17_2026_08_21`](./sports_satellite_ao_dispatch_batch17_2026_08_21.md) | **orphan** | infra | 0/1 | 0% | 0.2 | — |
| [`sports_satellite_ao_dispatch_batch9_2026_08_04_finalize`](./sports_satellite_ao_dispatch_batch9_2026_08_04_finalize.md) | master | infra | 0/2 | 0% | 0.2 | — |
| [`sports_track_h_denominator_gated_2026_07_28`](./sports_track_h_denominator_gated_2026_07_28.md) | master | infra | 0/1 | 0% | 0.2 | — |
| [`tradfi_registry_coverage_and_ao_readiness_2026_07_25_finalize`](./tradfi_registry_coverage_and_ao_readiness_2026_07_25_finalize.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`tradfi_satellite_ao_dispatch_batch12_2026_08_10`](./tradfi_satellite_ao_dispatch_batch12_2026_08_10.md) | master | infra | 1/2 | 50% | 0.2 | — |
| [`tradfi_satellite_ao_dispatch_batch12_2026_08_10_finalize`](./tradfi_satellite_ao_dispatch_batch12_2026_08_10_finalize.md) | master | infra | 0/2 | 0% | 0.2 | — |
| [`w_state_recovery_real_wiring_2026_08_20`](./w_state_recovery_real_wiring_2026_08_20.md) | **orphan** | design | 12/13 | 92% | 0.2 | — |
| [`pacifica_solana_perp_reintegration_2026_08_14`](./pacifica_solana_perp_reintegration_2026_08_14.md) | master | infra | 28/29 | 97% | 0.2 | — |
| [`sports_taxonomy_p2_migration_2026_08_08_finalize`](./sports_taxonomy_p2_migration_2026_08_08_finalize.md) | master | infra | 4/6 | 67% | 0.2 | — |
| [`codex_vs_repo_docs_ssot_audit_2026_06_01`](./codex_vs_repo_docs_ssot_audit_2026_06_01.md) | master | refactor | 29/31 | 94% | 0.2 | — |
| [`ao_satellite_ao_dispatch_batch22_finalize_2026_08_16`](./ao_satellite_ao_dispatch_batch22_finalize_2026_08_16.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`ao_satellite_ao_dispatch_batch23_finalize_2026_08_17`](./ao_satellite_ao_dispatch_batch23_finalize_2026_08_17.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`ao_satellite_ao_dispatch_batch24_finalize_2026_08_18`](./ao_satellite_ao_dispatch_batch24_finalize_2026_08_18.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`cefi_satellite_ao_dispatch_batch22_2026_08_19_finalize`](./cefi_satellite_ao_dispatch_batch22_2026_08_19_finalize.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`content_derived_backlog_task_ids_2026_08_08_finalize`](./content_derived_backlog_task_ids_2026_08_08_finalize.md) | master | refactor | 0/6 | 0% | 0.2 | — |
| [`tradfi_phase_d_terminal_gate_2026_07_24_finalize_2026_08_16`](./tradfi_phase_d_terminal_gate_2026_07_24_finalize_2026_08_16.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`ao_satellite_ao_dispatch_batch1_2026_08_21`](./ao_satellite_ao_dispatch_batch1_2026_08_21.md) | **orphan** | research | 0/1 | 0% | 0.2 | — |
| [`codex_vs_repo_docs_ssot_audit_2026_06_01_finalize_2026_07_27`](./codex_vs_repo_docs_ssot_audit_2026_06_01_finalize_2026_07_27.md) | master | infra | 0/1 | 0% | 0.2 | — |
| [`cross_cutting_satellite_ao_dispatch_batch15_2026_08_17`](./cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md) | master | infra | 15/16 | 94% | 0.2 | — |
| [`data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27`](./data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27.md) | master | infra | 0/1 | 0% | 0.2 | — |
| [`defi_archetype_catalog_identity_extension_ao_dispatch_2026_08_16_finalize`](./defi_archetype_catalog_identity_extension_ao_dispatch_2026_08_16_finalize.md) | master | refactor | 0/1 | 0% | 0.2 | — |
| [`defi_pipeline_e2e_and_coverage_validation_2026_06_20_finalize_2026_07_27`](./defi_pipeline_e2e_and_coverage_validation_2026_06_20_finalize_2026_07_27.md) | master | infra | 0/1 | 0% | 0.2 | — |
| [`deployment_api_true_catalogue_expected_universe_projection_ao_dispatch_2026_08_16_finalize`](./deployment_api_true_catalogue_expected_universe_projection_ao_dispatch_2026_08_16_finalize.md) | master | infra | 0/1 | 0% | 0.2 | — |
| [`prediction_satellite_ao_dispatch_batch11_2026_08_13`](./prediction_satellite_ao_dispatch_batch11_2026_08_13.md) | master | refactor | 0/2 | 0% | 0.2 | — |
| [`sports_satellite_ao_dispatch_batch5_2026_07_26_finalize`](./sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md) | master | infra | 2/4 | 50% | 0.2 | — |
| [`tradfi_manifest_content_recovery_completion_2026_07_24_finalize_2026_07_27`](./tradfi_manifest_content_recovery_completion_2026_07_24_finalize_2026_07_27.md) | master | infra | 0/1 | 0% | 0.2 | — |
| [`tradfi_phase_d_terminal_gate_2026_07_24`](./tradfi_phase_d_terminal_gate_2026_07_24.md) | master | infra | 7/8 | 88% | 0.2 | — |
| [`cross_cutting_satellite_ao_dispatch_batch21_2026_08_21`](./cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md) | **orphan** | infra | 10/12 | 83% | 0.2 | — |
| [`data_pipeline_alert_storm_root_cause_batch_2026_08_10`](./data_pipeline_alert_storm_root_cause_batch_2026_08_10.md) | master | refactor | 30/36 | 83% | 0.2 | — |
| [`manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16`](./manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md) | master | infra | 17/20 | 85% | 0.2 | — |
| [`sports_venue_e2e_batch1_2026_08_16`](./sports_venue_e2e_batch1_2026_08_16.md) | master | infra | 7/8 | 88% | 0.2 | — |
| [`aster_and_cefi_rolling_adv_feature_2026_07_21`](./aster_and_cefi_rolling_adv_feature_2026_07_21.md) | master | brand-new | 8/9 | 89% | 0.2 | — |
| [`anthropic_per_task_actual_spend_and_account_calibration_2026_08_10_finalize_2026_08_10`](./anthropic_per_task_actual_spend_and_account_calibration_2026_08_10_finalize_2026_08_10.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`ao_satellite_ao_dispatch_batch8_finalize_2026_08_08`](./ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md) | master | infra | 3/6 | 50% | 0.2 | — |
| [`cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08_finalize_2026_08_08`](./cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08_finalize_2026_08_08.md) | master | infra | 0/2 | 0% | 0.2 | — |
| [`codex_violations_ratchet_to_five_2026_06_10`](./codex_violations_ratchet_to_five_2026_06_10.md) | master | refactor | 44/45 | 98% | 0.2 | — |
| [`data_pipeline_check_mdps_features_2026_07_20`](./data_pipeline_check_mdps_features_2026_07_20.md) | master | infra | 39/40 | 98% | 0.2 | — |
| [`defi_satellite_ao_dispatch_batch18_2026_08_19_finalize`](./defi_satellite_ao_dispatch_batch18_2026_08_19_finalize.md) | master | refactor | 0/2 | 0% | 0.2 | — |
| [`infra_satellite_ao_dispatch_batch1_2026_08_21_finalize`](./infra_satellite_ao_dispatch_batch1_2026_08_21_finalize.md) | **orphan** | refactor | 0/3 | 0% | 0.2 | — |
| [`live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize`](./live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize.md) | master | infra | 0/2 | 0% | 0.2 | — |
| [`slot0_self_cleaning_daemon_2026_08_18_finalize_2026_08_18`](./slot0_self_cleaning_daemon_2026_08_18_finalize_2026_08_18.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`tradfi_satellite_ao_dispatch_batch18_2026_08_19_finalize`](./tradfi_satellite_ao_dispatch_batch18_2026_08_19_finalize.md) | master | infra | 0/3 | 0% | 0.2 | — |
| [`ui_satellite_ao_dispatch_batch3_finalize_2026_08_09`](./ui_satellite_ao_dispatch_batch3_finalize_2026_08_09.md) | master | infra | 0/2 | 0% | 0.2 | — |
| [`ui_satellite_ao_dispatch_batch5_finalize_2026_08_21`](./ui_satellite_ao_dispatch_batch5_finalize_2026_08_21.md) | **orphan** | infra | 0/2 | 0% | 0.2 | — |
| [`june_2026_vintage_audit_findings_2026_07_27`](./june_2026_vintage_audit_findings_2026_07_27.md) | master | refactor | 36/39 | 92% | 0.2 | — |
| [`ao_satellite_ao_dispatch_batch1_2026_08_21_finalize`](./ao_satellite_ao_dispatch_batch1_2026_08_21_finalize.md) | **orphan** | infra | 0/3 | 0% | 0.1 | — |
| [`cefi_satellite_ao_dispatch_batch22_2026_08_19`](./cefi_satellite_ao_dispatch_batch22_2026_08_19.md) | master | refactor | 0/1 | 0% | 0.1 | — |
| [`cefi_satellite_ao_dispatch_batch23_2026_08_21_finalize`](./cefi_satellite_ao_dispatch_batch23_2026_08_21_finalize.md) | **orphan** | infra | 0/3 | 0% | 0.1 | — |
| [`citadel_satellite_ao_dispatch_batch2_2026_08_19_finalize`](./citadel_satellite_ao_dispatch_batch2_2026_08_19_finalize.md) | master | infra | 0/1 | 0% | 0.1 | — |
| [`data_pipeline_alert_storm_ops_ao_dispatch_2026_08_15_finalize`](./data_pipeline_alert_storm_ops_ao_dispatch_2026_08_15_finalize.md) | master | infra | 0/1 | 0% | 0.1 | — |
| [`deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11_finalize`](./deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11_finalize.md) | master | infra | 1/2 | 50% | 0.1 | — |
| [`defi_hyperliquid_kprefix_coin_casing_fix_ao_dispatch_2026_08_16_finalize`](./defi_hyperliquid_kprefix_coin_casing_fix_ao_dispatch_2026_08_16_finalize.md) | master | infra | 0/1 | 0% | 0.1 | — |
| [`defi_instruments_store_v9_gate_c_apply_write_2026_08_16_finalize`](./defi_instruments_store_v9_gate_c_apply_write_2026_08_16_finalize.md) | master | research | 0/1 | 0% | 0.1 | — |
| [`sports_league_alias_dispatch_anomaly_investigation_ao_dispatch_2026_08_16_finalize`](./sports_league_alias_dispatch_anomaly_investigation_ao_dispatch_2026_08_16_finalize.md) | master | research | 0/1 | 0% | 0.1 | — |
| [`sports_venue_rename_attempted_at_trace_ao_dispatch_2026_08_16_finalize`](./sports_venue_rename_attempted_at_trace_ao_dispatch_2026_08_16_finalize.md) | master | research | 0/1 | 0% | 0.1 | — |
| [`sports_venue_vocab_and_league_id_delete_ao_dispatch_2026_08_16_finalize`](./sports_venue_vocab_and_league_id_delete_ao_dispatch_2026_08_16_finalize.md) | master | infra | 0/1 | 0% | 0.1 | — |
| [`tradfi_chain_bundle_reverse_derivation_ao_dispatch_2026_08_16_finalize`](./tradfi_chain_bundle_reverse_derivation_ao_dispatch_2026_08_16_finalize.md) | master | infra | 0/1 | 0% | 0.1 | — |
| [`tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16_finalize`](./tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16_finalize.md) | master | infra | 0/1 | 0% | 0.1 | — |
| [`tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16_finalize`](./tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16_finalize.md) | master | infra | 0/1 | 0% | 0.1 | — |
| [`tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16_finalize`](./tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16_finalize.md) | master | infra | 0/1 | 0% | 0.1 | — |
| [`tradfi_satellite_ao_dispatch_batch17_2026_08_18`](./tradfi_satellite_ao_dispatch_batch17_2026_08_18.md) | master | research | 1/2 | 50% | 0.1 | — |
| [`cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26`](./cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md) | master | infra | 18/19 | 95% | 0.1 | — |
| [`cefi_tardis_date_concurrency_2026_08_16`](./cefi_tardis_date_concurrency_2026_08_16.md) | master | infra | 20/22 | 91% | 0.1 | — |
| [`client_artefact_remediation_nickai_finalize_2026_08_18`](./client_artefact_remediation_nickai_finalize_2026_08_18.md) | master | infra | 2/5 | 40% | 0.1 | — |
| [`defi_migration_audit_log_2026_07_24`](./defi_migration_audit_log_2026_07_24.md) | master | design | 19/25 | 76% | 0.1 | — |
| [`consolidator_throughput_backlog_monitor_2026_07_09`](./consolidator_throughput_backlog_monitor_2026_07_09.md) | master | design | 24/26 | 92% | 0.1 | — |
| [`features_service_e2e_pipeline_test_2026_05_26`](./features_service_e2e_pipeline_test_2026_05_26.md) | master | brand-new | 44/45 | 98% | 0.1 | — |
| [`multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01_finalize_2026_08_08`](./multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01_finalize_2026_08_08.md) | master | infra | 2/3 | 67% | 0.1 | — |
| [`venue_readiness_ao_dispatch_batch1_finalize_2026_08_16`](./venue_readiness_ao_dispatch_batch1_finalize_2026_08_16.md) | master | infra | 5/6 | 83% | 0.1 | — |
| [`instruments_completion_tracker_2026_07_06`](./instruments_completion_tracker_2026_07_06.md) | master | infra | 34/39 | 87% | 0.1 | — |
| [`defi_satellite_ao_dispatch_batch3_2026_07_26_finalize`](./defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md) | master | infra | 3/4 | 75% | 0.1 | — |
| [`ui_satellite_ao_dispatch_batch1_finalize_2026_08_06`](./ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md) | master | infra | 3/4 | 75% | 0.1 | — |
| [`ci_satellite_ao_dispatch_batch13_2026_08_13`](./ci_satellite_ao_dispatch_batch13_2026_08_13.md) | master | refactor | 23/24 | 96% | 0.1 | — |
| [`ao_satellite_ao_dispatch_batch2_2026_08_21`](./ao_satellite_ao_dispatch_batch2_2026_08_21.md) | **orphan** | refactor | 0/10 | 0% | 0.1 | — |
| [`ao_satellite_ao_dispatch_batch3_2026_08_21`](./ao_satellite_ao_dispatch_batch3_2026_08_21.md) | **orphan** | refactor | 0/1 | 0% | 0.1 | — |
| [`defi_satellite_ao_dispatch_batch16_2026_08_17_finalize`](./defi_satellite_ao_dispatch_batch16_2026_08_17_finalize.md) | master | refactor | 0/2 | 0% | 0.1 | — |
| [`defi_satellite_ao_dispatch_batch17_2026_08_18_finalize`](./defi_satellite_ao_dispatch_batch17_2026_08_18_finalize.md) | master | refactor | 0/2 | 0% | 0.1 | — |
| [`meta_plan_corpus_hygiene_ao_dispatch_batch1_finalize_2026_08_10`](./meta_plan_corpus_hygiene_ao_dispatch_batch1_finalize_2026_08_10.md) | master | refactor | 0/4 | 0% | 0.1 | — |
| [`sports_consolidated_native_ao_extract_2026_07_25_finalize`](./sports_consolidated_native_ao_extract_2026_07_25_finalize.md) | master | infra | 3/4 | 75% | 0.1 | — |
| [`tradfi_satellite_ao_dispatch_batch19_2026_08_19_finalize`](./tradfi_satellite_ao_dispatch_batch19_2026_08_19_finalize.md) | master | infra | 0/3 | 0% | 0.1 | — |
| [`tradfi_satellite_ao_dispatch_batch9_2026_08_16_finalize`](./tradfi_satellite_ao_dispatch_batch9_2026_08_16_finalize.md) | master | infra | 0/2 | 0% | 0.1 | — |
| [`cross_cutting_satellite_ao_dispatch_batch13_2026_08_13`](./cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md) | master | refactor | 94/95 | 99% | 0.1 | — |
| [`ui_satellite_ao_dispatch_batch3_2026_08_09`](./ui_satellite_ao_dispatch_batch3_2026_08_09.md) | master | infra | 2/3 | 67% | 0.1 | — |
| [`instruments_mtds_consistency_remediation_residuals_2026_07_24_finalize`](./instruments_mtds_consistency_remediation_residuals_2026_07_24_finalize.md) | master | refactor | 0/2 | 0% | 0.1 | — |
| [`solana_dex_pool_swaps_indexer_2026_08_08_finalize`](./solana_dex_pool_swaps_indexer_2026_08_08_finalize.md) | master | refactor | 0/2 | 0% | 0.1 | — |
| [`tradfi_satellite_ao_dispatch_batch17_2026_08_18_finalize`](./tradfi_satellite_ao_dispatch_batch17_2026_08_18_finalize.md) | master | infra | 0/1 | 0% | 0.1 | — |
| [`w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive`](./w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md) | **orphan** | refactor | — | — | 0.1 | — |
| [`cefi_satellite_ao_dispatch_batch21_2026_08_17`](./cefi_satellite_ao_dispatch_batch21_2026_08_17.md) | master | refactor | 2/3 | 67% | 0.1 | — |
| [`tradfi_backfill_throughput_followups_2026_07_24`](./tradfi_backfill_throughput_followups_2026_07_24.md) | master | infra | 23/24 | 96% | 0.1 | — |
| [`data_completion_sports_2026_07_24`](./data_completion_sports_2026_07_24.md) | master | infra | 39/41 | 95% | 0.1 | — |
| [`review_agent_evidence_gated_write_capability_2026_08_09`](./review_agent_evidence_gated_write_capability_2026_08_09.md) | master | design | 6/7 | 86% | 0.1 | — |
| [`ao_satellite_ao_dispatch_batch25_2026_08_19`](./ao_satellite_ao_dispatch_batch25_2026_08_19.md) | master | refactor | 9/11 | 82% | 0.1 | — |
| [`anthropic_per_task_actual_spend_and_account_calibration_2026_08_10_operator_items_2026_08_19`](./anthropic_per_task_actual_spend_and_account_calibration_2026_08_10_operator_items_2026_08_19.md) | master | infra | 0/1 | 0% | 0.1 | — |
| [`ao_satellite_ao_dispatch_batch23_2026_08_17`](./ao_satellite_ao_dispatch_batch23_2026_08_17.md) | master | refactor | 4/6 | 67% | 0.1 | — |
| [`client_artefact_remediation_siblings_finalize_2026_08_18`](./client_artefact_remediation_siblings_finalize_2026_08_18.md) | master | infra | 2/3 | 67% | 0.1 | — |
| [`deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11_operator_items_2026_08_19`](./deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11_operator_items_2026_08_19.md) | master | infra | 0/1 | 0% | 0.1 | — |
| [`defi_kamino_lending_blazestake_regrowth_after_retirement_finalize_2026_08_17`](./defi_kamino_lending_blazestake_regrowth_after_retirement_finalize_2026_08_17.md) | master | infra | 0/1 | 0% | 0.1 | — |
| [`defi_migration_dedicated_bucket_architecture_retired_2026_08_14_finalize_2026_08_16`](./defi_migration_dedicated_bucket_architecture_retired_2026_08_14_finalize_2026_08_16.md) | master | infra | 0/2 | 0% | 0.1 | — |
| [`infra_satellite_ao_dispatch_batch19_2026_08_18_finalize_2026_08_20`](./infra_satellite_ao_dispatch_batch19_2026_08_18_finalize_2026_08_20.md) | **orphan** | refactor | 1/2 | 50% | 0.1 | — |
| [`tradfi_satellite_ao_dispatch_batch9_2026_08_16`](./tradfi_satellite_ao_dispatch_batch9_2026_08_16.md) | master | infra | 0/1 | 0% | 0.1 | — |
| [`ui_satellite_ao_dispatch_batch4_finalize_2026_08_17`](./ui_satellite_ao_dispatch_batch4_finalize_2026_08_17.md) | master | infra | 1/2 | 50% | 0.1 | — |
| [`quality_gates_quickmerge_timing_baseline_2026_07_31`](./quality_gates_quickmerge_timing_baseline_2026_07_31.md) | master | research | 15/16 | 94% | 0.1 | — |
| [`data_status_tab_and_downloads_remediation_2026_06_16`](./data_status_tab_and_downloads_remediation_2026_06_16.md) | master | refactor | 31/33 | 94% | 0.1 | — |
| [`meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10`](./meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md) | master | refactor | 16/18 | 89% | 0.1 | — |
| [`prediction_satellite_ao_dispatch_batch6_2026_07_29`](./prediction_satellite_ao_dispatch_batch6_2026_07_29.md) | master | infra | 19/22 | 86% | 0.1 | — |
| [`canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08`](./canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md) | master | refactor | 12/13 | 92% | 0.1 | — |
| [`ao_satellite_ao_dispatch_batch24_2026_08_18`](./ao_satellite_ao_dispatch_batch24_2026_08_18.md) | master | refactor | 4/5 | 80% | 0.1 | — |
| [`ao_satellite_ao_dispatch_batch2_finalize_2026_08_21`](./ao_satellite_ao_dispatch_batch2_finalize_2026_08_21.md) | **orphan** | refactor | 0/3 | 0% | 0.1 | — |
| [`defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04_finalize_2026_08_08`](./defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04_finalize_2026_08_08.md) | master | refactor | 1/2 | 50% | 0.1 | — |
| [`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24`](./tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md) | master | infra | 3/4 | 75% | 0.1 | — |
| [`ao_satellite_ao_dispatch_batch21_finalize_2026_08_16`](./ao_satellite_ao_dispatch_batch21_finalize_2026_08_16.md) | master | infra | 3/4 | 75% | 0.1 | — |
| [`ao_satellite_ao_dispatch_batch14_finalize_2026_08_09`](./ao_satellite_ao_dispatch_batch14_finalize_2026_08_09.md) | master | infra | 4/5 | 80% | 0.0 | — |
| [`ao_satellite_ao_dispatch_batch3_2026_08_21_finalize`](./ao_satellite_ao_dispatch_batch3_2026_08_21_finalize.md) | **orphan** | refactor | 0/2 | 0% | 0.0 | — |
| [`orchestrator_vm_e2e_hardening_2026_07_24`](./orchestrator_vm_e2e_hardening_2026_07_24.md) | master | design | 29/30 | 97% | 0.0 | — |
| [`prediction_satellite_ao_dispatch_batch6_2026_07_29_progresslog`](./prediction_satellite_ao_dispatch_batch6_2026_07_29_progresslog.md) | master | refactor | — | — | 0.0 | — |
| [`sports_satellite_ao_dispatch_batch10_2026_08_06_finalize`](./sports_satellite_ao_dispatch_batch10_2026_08_06_finalize.md) | master | infra | 4/5 | 80% | 0.0 | — |
| [`instruments_mtds_consistency_remediation_residuals_2026_07_24`](./instruments_mtds_consistency_remediation_residuals_2026_07_24.md) | master | infra | 46/47 | 98% | 0.0 | — |
| [`sports_satellite_ao_dispatch_batch12_2026_08_09_finalize`](./sports_satellite_ao_dispatch_batch12_2026_08_09_finalize.md) | master | infra | 4/5 | 80% | 0.0 | — |
| [`ao_open_work_consolidated_tracker_2026_08_14`](./ao_open_work_consolidated_tracker_2026_08_14.md) | master | infra | 70/71 | 99% | 0.0 | — |
| [`ao_satellite_ao_dispatch_batch21_2026_08_16`](./ao_satellite_ao_dispatch_batch21_2026_08_16.md) | master | infra | 7/7 | 100% | 0.0 | — |
| [`ao_satellite_ao_dispatch_batch8_2026_08_08`](./ao_satellite_ao_dispatch_batch8_2026_08_08.md) | master | research | 4/4 | 100% | 0.0 | — |
| [`cefi_deribit_binance_futures_bundle_verification_2026_06_20`](./cefi_deribit_binance_futures_bundle_verification_2026_06_20.md) | master | infra | 7/7 | 100% | 0.0 | — |
| [`cefi_deribit_binance_futures_bundle_verification_2026_06_20_finalize_2026_07_27`](./cefi_deribit_binance_futures_bundle_verification_2026_06_20_finalize_2026_07_27.md) | master | infra | 1/1 | 100% | 0.0 | — |
| [`ci_consolidated_closeout_2026_07_25`](./ci_consolidated_closeout_2026_07_25.md) | master | infra | 1/1 | 100% | 0.0 | — |
| [`client_artefact_remediation_nickai_2026_08_18`](./client_artefact_remediation_nickai_2026_08_18.md) | master | infra | 16/16 | 100% | 0.0 | — |
| [`client_artefact_remediation_siblings_2026_08_18`](./client_artefact_remediation_siblings_2026_08_18.md) | master | infra | 6/6 | 100% | 0.0 | — |
| [`code_readiness_t1_progress_history_2026_08_20`](./code_readiness_t1_progress_history_2026_08_20.md) | **orphan** | refactor | — | — | 0.0 | — |
| [`code_readiness_t2_progress_history_2026_08_20`](./code_readiness_t2_progress_history_2026_08_20.md) | **orphan** | refactor | — | — | 0.0 | — |
| [`code_readiness_t3_progress_history_2026_08_20`](./code_readiness_t3_progress_history_2026_08_20.md) | **orphan** | refactor | — | — | 0.0 | — |
| [`code_readiness_t5_progress_history_2026_08_21`](./code_readiness_t5_progress_history_2026_08_21.md) | **orphan** | refactor | — | — | 0.0 | — |
| [`data_pipeline_e2e_milestones_gate_2026_07_24`](./data_pipeline_e2e_milestones_gate_2026_07_24.md) | master | research | 65/65 | 100% | 0.0 | — |
| [`data_pipeline_reconciliation_skill_2026_07_20`](./data_pipeline_reconciliation_skill_2026_07_20.md) | master | design | 48/48 | 100% | 0.0 | — |
| [`deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11`](./deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md) | master | infra | 18/18 | 100% | 0.0 | — |
| [`defi_distinct_values_zero_noncanonical_dispatch_2026_08_04`](./defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md) | master | refactor | 3/3 | 100% | 0.0 | — |
| [`defi_satellite_ao_dispatch_batch17_2026_08_18`](./defi_satellite_ao_dispatch_batch17_2026_08_18.md) | master | research | 2/2 | 100% | 0.0 | — |
| [`defi_satellite_ao_dispatch_batch2_2026_07_26`](./defi_satellite_ao_dispatch_batch2_2026_07_26.md) | master | infra | 22/22 | 100% | 0.0 | — |
| [`defi_strategy_pnl_axis_index_2026_07_24`](./defi_strategy_pnl_axis_index_2026_07_24.md) | master | infra | 1/1 | 100% | 0.0 | — |
| [`defi_venue_lst_rates_residual_2026_07_24`](./defi_venue_lst_rates_residual_2026_07_24.md) | master | design | 4/4 | 100% | 0.0 | — |
| [`deployment_registry_firestore_migration_2026_07_14`](./deployment_registry_firestore_migration_2026_07_14.md) | master | infra | 1/1 | 100% | 0.0 | — |
| [`doc_body_link_checker_blind_to_backtick_citations_2026_08_02_finalize_2026_08_08`](./doc_body_link_checker_blind_to_backtick_citations_2026_08_02_finalize_2026_08_08.md) | master | infra | 3/3 | 100% | 0.0 | — |
| [`infra_satellite_ao_dispatch_batch19_2026_08_18`](./infra_satellite_ao_dispatch_batch19_2026_08_18.md) | master | infra | 2/2 | 100% | 0.0 | — |
| [`infra_satellite_ao_dispatch_batch7_finalize_2026_08_04`](./infra_satellite_ao_dispatch_batch7_finalize_2026_08_04.md) | master | infra | 3/3 | 100% | 0.0 | — |
| [`instruments_cefi_g1_g5_gate_execution_2026_07_24`](./instruments_cefi_g1_g5_gate_execution_2026_07_24.md) | master | design | 24/24 | 100% | 0.0 | — |
| [`nick_ai_platform_readiness_remediation_2026_08_16`](./nick_ai_platform_readiness_remediation_2026_08_16.md) | master | brand-new | 11/11 | 100% | 0.0 | — |
| [`prediction_consolidated_closeout_2026_07_18`](./prediction_consolidated_closeout_2026_07_18.md) | master | infra | 1/1 | 100% | 0.0 | — |
| [`prediction_live_clob_depth_capture_2026_07_24`](./prediction_live_clob_depth_capture_2026_07_24.md) | master | brand-new | 34/34 | 100% | 0.0 | — |
| [`sports_consolidated_native_ao_extract_2026_07_25`](./sports_consolidated_native_ao_extract_2026_07_25.md) | master | infra | 33/33 | 100% | 0.0 | — |
| [`sports_satellite_ao_dispatch_batch10_2026_08_06`](./sports_satellite_ao_dispatch_batch10_2026_08_06.md) | master | infra | 5/5 | 100% | 0.0 | — |
| [`sports_satellite_ao_dispatch_batch12_2026_08_09`](./sports_satellite_ao_dispatch_batch12_2026_08_09.md) | master | infra | 4/4 | 100% | 0.0 | — |
| [`sports_satellite_ao_dispatch_batch5_2026_07_26`](./sports_satellite_ao_dispatch_batch5_2026_07_26.md) | master | infra | 2/2 | 100% | 0.0 | — |
| [`sports_taxonomy_p2_migration_2026_08_08`](./sports_taxonomy_p2_migration_2026_08_08.md) | master | infra | 26/26 | 100% | 0.0 | — |
| [`strategy_service_reference_constants_inventory_2026_08_21`](./strategy_service_reference_constants_inventory_2026_08_21.md) | **orphan** | research | — | — | 0.0 | — |
| [`tradfi_consolidated_closeout_2026_07_18`](./tradfi_consolidated_closeout_2026_07_18.md) | master | infra | 2/2 | 100% | 0.0 | — |
| [`ui_satellite_ao_dispatch_batch1_2026_08_06`](./ui_satellite_ao_dispatch_batch1_2026_08_06.md) | master | infra | 3/3 | 100% | 0.0 | — |
| [`ui_satellite_ao_dispatch_batch4_2026_08_17`](./ui_satellite_ao_dispatch_batch4_2026_08_17.md) | master | infra | 1/1 | 100% | 0.0 | — |
| **TOTAL** (434 plans) | 58 orphans, 0 TBD | — | — | **61% done** | **507** | — |
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
