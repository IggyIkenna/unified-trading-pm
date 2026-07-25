---
doc_type: issue
title: Instruments-Service Plan Reconciliation — Section B triage roster (extracted 2026-07-25)
summary:
  "Line-cap extraction: Section B (Triage — the cluster-agent roster + zero-hit set-aside list + the wave 1/2 coverage
  accounting) verbatim-moved out of instruments_service_plan_reconciliation_2026_06_29.md to bring it back under the
  1000-line hard cap. Pure process/scoping record — how the 67-plan reconciliation sweep was clustered and covered, not
  a live decision or open item. The parent doc's Section C/D/E/F/G findings stand on their own without this table."
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-api-contracts]
scope: [admin]
tags: [reconciliation, ssot-audit, plan-hygiene, instruments-service, honest-coverage, venue-registry, history-extract]
related: [/plans/active/issues/instruments_service_plan_reconciliation_2026_06_29.md]
created: 2026-07-25
parent_epic: instruments_master
priority: P3
source: [line-cap extraction from instruments_service_plan_reconciliation_2026_06_29.md, 2026-07-25]
assigned_vm: NA
resolved_by: "verbatim extraction, no content change"
locked_by:
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
last_updated: 2026-07-25
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

# Instruments-Service Plan Reconciliation — Section B triage roster (history extract, 2026-07-25)

> Extracted verbatim from `plans/active/issues/instruments_service_plan_reconciliation_2026_06_29.md` § "Section B —
> Triage" to bring the parent doc back under the 1000-line hard cap. No content changed.

## Section B — Triage (contested-token signal across the 67 plans)

Signal = grep hits across 7 token-groups (venue-registry · OKX-split · perp · defi-MVP · enumeration · honest-coverage ·
coverage-numbers). All plans below are **subjects** (no date exemption). 17 zero-hit plans are set aside (don't touch
the SSOT axes at all). Deep-read clustered into 12 read-only agents (C1–C12).

**Deep-read roster (HIGH/MED — by theme):**

| Cluster | Plans                                                                                                   |
| ------- | ------------------------------------------------------------------------------------------------------- |
| C1      | cefi_manifest_canonicalisation · prediction_manifest_canonicalisation                                   |
| C2      | tradfi_manifest_canonicalisation · defi_manifest_canonicalisation                                       |
| C3      | sports_manifest_canonicalisation · downstream_services_manifest_canonicalisation                        |
| C4      | master_data_canonicalisation_migration_catalogue                                                        |
| C5      | mvp_backfill_defi_onchain_v10 · mvp_catalogue_finalization_v10 · mvp_reconciliation_closeout_v10        |
| C6      | mvp_backfill_cefi_tick_v10 · mvp_backfill_tradfi_ohlcv1m_v10 · mvp_scope_catalogue_tagging              |
| C7      | prediction_venue_perps_and_live_clob_depth · cryptovenue_equity_perps_and_tokenized_stocks              |
| C8      | data_completion_to_100_all_ag · path_to_100pct_backfill_mtds_is · data_pipeline_hardening_self_monitor  |
| C9      | instruments_foundation_completeness · instruments_mtds_subset_consistency · migration_verif_orphan      |
| C10     | solana_defi_legacy_migration · master_to_live_defi · v2_engine_venue_buildout                           |
| C11     | cefi_deribit_binance_futures_bundle_verification · tradfi_multisource_backfill · tradfi_massive_dual    |
| C12     | sports_odds_bookmaker_coverage_enum · data_status_tab_downloads · capability_wizard · pipeline_mode_src |

**Set aside — 17 zero-hit (no contested-surface signal; logged, not deep-read):** bar_edge_left_vs_right_remediation,
cicd_sit_full_coverage_handoff, data_source_provenance_all_asset_groups, codex_vs_repo_docs_ssot_audit,
predictions_other_bucket_and_ui_drilldown, defi_onchain_derivable_values_and_date_drift, stash_pile_workspace_cleanup,
cicd_consolidated_remaining, pipeline_mode_partition_migration, doc_frontmatter_schema_and_validator,
sports_reference_backfill_oom, orchestrator_strict_vm_matching_and_plan_frontmatter_governance,
scripts_lifecycle_marker_rollout, mtds_file_size_refactor, test_fleet_image_builds_from_current_code,
tradfi_cme_event_contract_backfill, utl_uac_reuse_consolidation_remediation.

**Coverage correction (2026-06-29):** the first deep-read wave (C1–C12) covered **31** subject plans, not all
contested-signal subjects. **14 contested-signal plans were uncovered** (initially mis-bucketed as date-trusted before
the no-date-exemption model was locked). Now covered by a **follow-up wave C13–C15**: _sports (10)_ —
`sports_p2_history_reference_and_odds` (32 sig), `sports_p2_history_apifootball` (24),
`sports_p1_golden_window_apifootball` (14), `sports_pipeline_to_100pct_golden_window_first` (7),
`sports_p2_daily_forward_catalogue_and_final_gate` (4), `sports_canonical_universe_and_apifootball_reference_expansion`
(3), `sports_fixtures_schema_split_completion` (2), `sports_p1_golden_window_e2e_gate` (2),
`sports_p2_features_history_to_ml_ready` (1), `sports_p0_sourcing_and_honest_coverage_correctness` (1); _misc (4)_ —
`unified_deployment_health_cockpit` (5), `codex_violations_ratchet_to_five` (4), `work_split_2026_05_22_ikenna` (3),
`repo_scripts_governance_audit` (1). **Subject coverage after C13–C15 = 45/62 deep-read + 17 set-aside = 62/62
accounted.**
