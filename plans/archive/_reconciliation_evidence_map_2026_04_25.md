---
title: Plans Reconciliation Evidence Map
date: 2026-04-25
status: audit-record
type: audit
scope: 143 plans in plans/active/ as of 2026-04-25
audit_passes: [evidence-map, classification, duplication-scan, orphan-integration, sports-register-drift]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Reconciliation Evidence Map — 2026-04-25

Read-only audit of every file in `plans/active/` (143 plan files + 6 meta files) against committed code state on
`origin/live-defi-rollout`. Each plan classified into one of:

- `shipped` — substantially all phases done with cited commit/file evidence
- `partial` — some phases shipped, others genuinely open
- `superseded` — scope now lives in another plan (cite which one)
- `orphan` — scope unconnected to any active surface, no commits, no integration
- `live` — actively-tracked work in progress, normal state
- `unclear` — needs human review (state the question)

This document drives the surgical plan-file edit pass that follows (commit 2:
`chore(plans): reconciliation pass — flip shipped checkboxes + superseded_by + flag orphans/duplicates`).

## Sports SSOT — register location correction

The dispatch prompt referenced `/codex/09-strategy/cross-cutting/12-sports-trading.md` as the canonical sports register.
**That file does NOT exist.** The canonical sports register is
[`/codex/02-data/sports-scheduling-and-sharding.md`](/codex/02-data/sports-scheduling-and-sharding.md) §12.0 "Live
progress register". Last register audit: 2026-04-22 late.

### §12.0 register vs plans/active/ checkbox state (verified 2026-04-25)

| § Plan                                               | Register claim (2026-04-22) | Actual checkbox state (2026-04-25)                                                        | Drift                         |
| ---------------------------------------------------- | --------------------------- | ----------------------------------------------------------------------------------------- | ----------------------------- |
| 1 utl_manifest_migration_primitives                  | 17/0 DONE                   | not in active/ — already promoted to §12.1                                                | none                          |
| 2 apifootball_enrichment_historical_backfill         | 3/7 in-flight               | done=7 open=3 (post-2026-04-22 commits flipped)                                           | register stale; plan correct  |
| 3 non_apifootball_provider_backfill_launchers        | 5/2 near-C5                 | unverified — chunk AE retry pending                                                       | tbd                           |
| 4 instruments_service_orchestrator_reliability_fixes | 12/8 half-way               | unverified — chunk AC retry pending                                                       | tbd                           |
| 5 sports_scheduler_cron_activation                   | 7/4 live via VM-daemon      | unverified — chunk AE retry pending                                                       | tbd                           |
| 6 features_sports_pipeline_deployment                | 11/3 near-C5                | done=11 open=3                                                                            | none                          |
| 9 sports_manifest_shard_migration_cleanup            | 11/5 half-way               | unverified — chunk AE retry pending                                                       | tbd                           |
| 11 transfermarkt_sfi_team_mapping_cache              | 20/2 near-C5                | done=20 open=2                                                                            | none                          |
| 12 deployment_service_build_infrastructure_repair    | 0/9 authored (BLOCKER)      | done=0 open=0 (uses YAML `todos:` block, not markdown checkboxes — plan-format violation) | format drift; not state drift |
| 13 utl_base_image_rebuild_and_workflow_unblock       | 0/17 authored (BLOCKER)     | done=0 open=17                                                                            | none                          |

**Per-prompt reconciliation rule:** Plans 12+13 are **classified `live`**, NOT orphan. They are known active blockers
gating Plans 5+6 Cloud Run activation. Plan 13 has 5 in-flight UTL commits (`fb677546`, `9be20d88`, `6bfaa9f5`,
`1d63189d`, `ccdc6c8c`) attempting the rebuild — partial work shipping.

## Plans with explicit `remaining_todos_consolidated_into:` frontmatter (21 plans, 6 consolidator targets)

These have unambiguous superseder declarations already in their frontmatter — Pass 2 will add the canonical
`superseded_by:` field to formalise the redirect.

| Source plan                                                       | Consolidator target                                |
| ----------------------------------------------------------------- | -------------------------------------------------- |
| client_config_and_defi_risk_2026_04_01                            | consolidated_strategy_and_ui_2026_04_15            |
| cross_domain_alpha_execution_intelligence_2026_04_11              | consolidated_strategy_and_ui_2026_04_15            |
| defi_instrument_pipeline_and_rewards_2026_04_01                   | consolidated_defi_data_pipeline_2026_04_15         |
| domain_agnostic_ml_framework_2026_04_11                           | consolidated_ml_advanced_pipeline_2026_04_15       |
| instruments_service_template_refactor_8e653acc                    | consolidated_operational_validation_2026_04_15     |
| manual_trade_booking_reconciliation_2026_03_22                    | consolidated_operational_validation_2026_04_15     |
| mev_protection_and_execution_enhancements_2026_04_01              | consolidated_defi_data_pipeline_2026_04_15         |
| ml_pipeline_revolution_2026_04_11                                 | consolidated_ml_advanced_pipeline_2026_04_15       |
| mtds_defi_data_normalization_2026_04_14                           | consolidated_defi_data_pipeline_2026_04_15         |
| polymarket_prediction_pipeline_2026_03_25                         | consolidated_sports_prediction_pipeline_2026_04_15 |
| remove_data_types_field_2026_04_10                                | consolidated_operational_validation_2026_04_15     |
| sports_batch_pipeline_end_to_end_2026_03_25                       | consolidated_sports_prediction_pipeline_2026_04_15 |
| sports_integration_01_reference_data_pipeline_2026_03_25          | consolidated_sports_prediction_pipeline_2026_04_15 |
| sports_integration_02_odds_market_data_pipeline_2026_03_25        | consolidated_sports_prediction_pipeline_2026_04_15 |
| sports_integration_03_features_provider_integration_2026_03_25    | consolidated_sports_prediction_pipeline_2026_04_15 |
| sports_integration_04_feature_calculators_full_2026_03_25         | consolidated_sports_prediction_pipeline_2026_04_15 |
| sports_integration_05_ml_training_pipeline_2026_03_25             | consolidated_sports_prediction_pipeline_2026_04_15 |
| sports_integration_06_strategy_execution_gcs_migration_2026_03_25 | consolidated_sports_prediction_pipeline_2026_04_15 |
| strategy_lifecycle_visibility_ui_2026_04_11                       | consolidated_strategy_and_ui_2026_04_15            |
| ui_walkthrough_and_e2e_alignment_2026_04_01                       | consolidated_strategy_and_ui_2026_04_15            |
| unified_pipeline_scheduling_and_triggers_2026_04_15               | consolidated_operational_validation_2026_04_15     |

## G1 / G2 / G3 baseline (2026-04-25)

- **G1 (14 plans)**: ALL ARCHIVED on a prior pass — `plans/archive/refactor_g1_*.md`. None present in `plans/active/`.
- **G2 (11 plans, 185 total todos)**: 6 done (3.2%) per raw checkbox grep. Full evidence in chunk-AD agent output.
- **G3 (5 plans, 58 total todos)**: 5 done (8.6%) per raw checkbox grep. Full evidence in chunk-AE agent output.

## Per-plan evidence (assembled from 6 parallel evidence-map agents)

> Each block is the structured output of one of 6 parallel evidence-map agents (chunks AA / AB / AC / AD / AE / AF —
> 25/24/24/25/25/20 plans respectively). Format is consistent: frontmatter / checkboxes / scope / evidence /
> classification / supersedes / superseded_by / duplication_partners / [register_drift if sports] / recommended_action /
> evidence_notes.

## Chunk AA (25 plans — meta + apifootball through data_catalogue_cleanup)

### CITADEL_VISION_2026_03_22.md

- frontmatter: none (vision doc)
- checkboxes: 0/0
- candidate_classification: shipped (vision doc — descriptive, not actionable)
- duplication_partners: GAP_CLASSIFICATION_2026_03_22.md, PLAN_AMENDMENTS_2026_03_22.md
- recommended_action: no edit; consider `plans/reference/`

### GAP_CLASSIFICATION_2026_03_22.md

- frontmatter: none
- checkboxes: 0/0
- candidate_classification: shipped (companion analysis doc)
- candidate_superseded_by: dart_ui_strategy_filtering_and_onboarding_2026_04_24
- recommended_action: no edit; consider `plans/reference/`

### PLAN_AMENDMENTS_2026_03_22.md

- frontmatter: none
- checkboxes: 0/0
- candidate_classification: shipped (amendments folded into newer 2026-04 plans)
- candidate_superseded_by: dart_ui_strategy_filtering_and_onboarding_2026_04_24, consolidated_strategy_and_ui_2026_04_15
- recommended_action: no edit; consider `plans/reference/`

### apifootball_enrichment_historical_backfill_2026_04_21.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 7/3 (70%)
- evidence: 815e5465 (Phase 0+1 launch), 5599f9e8 (Plan 2 INJURIES), afbc8aec (4 HUMAN P1)
- candidate_classification: live (active VM scheduling)
- register_drift (sports): yes — register says 3/7 in-flight; checkboxes show 7/3 (post-2026-04-22 commits flipped).
  Plan correct, register stale.
- recommended_action: no edit (plan tracks live state)

### availability_manifest_v4_and_data_status_2026_04_13.md

- frontmatter: status=active
- checkboxes: 0/96 (0%)
- evidence: SUPERSEDED — schema progressed past v4. UAC bba284f, MTDS 0b8ab42, PM 3d041d81, 4297379f, bff343c
- candidate_classification: superseded
- candidate_superseded_by: manifest_schema_v6_quote_margin_combo_2026_04_23,
  data_status_institutional_drilldown_2026_04_24, honest_coverage_metrics_2026_04_19
- duplication_partners: manifest_schema_v6_quote_margin_combo_2026_04_23, honest_coverage_metrics_2026_04_19
- recommended_action: add superseded_by marker; archive after [unlock-plan]

### canonical_team_mapping_propagation_2026_03_30.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/44 (0%)
- evidence: instruments-service 9bf23d8 (TM+SFI cache + drift events); UAC 36bed50; PM 8f65b7e4
- candidate_classification: partial
- register_drift (sports): yes — TM+SFI cache+drift shipped but checkboxes still all open
- duplication_partners: features_sports_upstream_coverage_gaps_2026_04_21,
  consolidated_sports_prediction_pipeline_2026_04_15
- recommended_action: flip checkboxes for cache + drift items per `9bf23d8`/`e5d941e1`

### cefi_tradfi_tick_data_backfill_2026_04_10.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 11/19 (37%)
- evidence: PM a5d7203a, 5fce9f28, 44b1553e, a3501b13, f6627cd3, a6bc816e (P2.A/P2.B all flipped); MTDS 81f0fa4,
  5ec195f, 1364211
- candidate_classification: live (95-VM fleet active)
- recommended_action: no edit

### citadel_per_service_remediation_2026_03_24.md

- frontmatter: parent_plan=citadel_service_remediation
- checkboxes: 0/149 (0%)
- candidate_classification: partial
- candidate_superseded_by: citadel_service_remediation_2026_03_24 (parent), full_qg_sweep_all_services
- recommended_action: unclear — needs human review (149 untouched while parent shows 19/30)

### citadel_service_remediation_2026_03_24.md

- frontmatter: status=active, parent of per-service plan
- checkboxes: 19/11 (63%)
- evidence: 8f6e33c (architecture-v2 fence), 28fc19b (factory cutover)
- candidate_classification: live
- recommended_action: no edit

### client_config_and_defi_risk_2026_04_01.md

- frontmatter: status=active, **remaining_todos_consolidated_into: consolidated_strategy_and_ui_2026_04_15**
- checkboxes: 25/5 (83%)
- candidate_classification: superseded
- candidate_superseded_by: consolidated_strategy_and_ui_2026_04_15
- recommended_action: add canonical superseded_by; archive after [unlock-plan]

### cme_sp_ml_signal_preaudit_2026_04_20.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/23 (0%)
- evidence: PM dacb02d2, bfad662f (codex sync); core continuous-series builder + ES roll + VM launcher pending
- candidate_classification: live (CME Sept 2026 deliverable per Path-to-$100M)
- recommended_action: no edit

### consolidated_defi_data_pipeline_2026_04_15.md

- frontmatter: status=active, source_plans=[6 DeFi plans]
- checkboxes: 0/0 (uses YAML status); 33 todo IDs all status: todo
- candidate_classification: partial
- candidate_superseded_by: defi_data_types_completeness_2026_04_24
- recommended_action: flip statuses for shipped Solana collectors + Phase 2.5 instruments-first

### consolidated_ml_advanced_pipeline_2026_04_15.md

- frontmatter: status=active, source_plans=[ml_pipeline_revolution, domain_agnostic_ml_framework]
- checkboxes: 0/0 (24 todo IDs)
- candidate_classification: partial
- candidate_superseded_by: cme_sp_ml_signal_preaudit_2026_04_20
- recommended_action: flip "PARTIALLY_DONE" items where inline note already qualifies

### consolidated_operational_validation_2026_04_15.md

- frontmatter: status=active, depends_on=[consolidated-sports-prediction, consolidated-defi-data]
- checkboxes: 0/0 (13 todo IDs)
- candidate_classification: partial
- duplication_partners: instruments_service_orchestrator_reliability_fixes_2026_04_21,
  full_qg_sweep_all_services_2026_03_28
- recommended_action: flip cleared QG items

### consolidated_sports_prediction_pipeline_2026_04_15.md

- frontmatter: status=active, source_plans=[8 sports plans]
- checkboxes: 0/0 (52 todo IDs)
- evidence: Plan 6 write-gate `c1987760`+`c397ab56`+`454cca3`; sports register `63e4e040`; fixture denormalisation
  `fa3e6c6a`; sports-scheduling SSOT `494c2544`
- candidate_classification: partial
- candidate_superseded_by: codex sports-scheduling-and-sharding §12.0 register replaces this consolidator's tracking
  role
- duplication_partners: features_sports_pipeline_deployment_2026_04_21,
  instruments_service_write_gate_validation_2026_04_22, apifootball_enrichment_historical_backfill_2026_04_21
- register_drift (sports): yes — /codex/02-data/sports-scheduling-and-sharding.md is live SSOT; this consolidator never
  updated
- recommended_action: superseded marker pointing at sports register codex + 5 active sports plans

### consolidated_strategy_and_ui_2026_04_15.md

- frontmatter: status=active, source_plans=[5 strategy/UI plans]
- checkboxes: 0/0 (36 todo IDs)
- evidence: Plan A archived; DART exclusive Plan D `d373c4b7`; DART UI Phases 9-11 `f70926cf`/`2a9aa7c7`/`e11a4145`
- candidate_classification: partial
- candidate_superseded_by: dart_ui_strategy_filtering_and_onboarding_2026_04_24,
  dart_exclusive_subscription_research_fork_2026_04_21, dashboard_services_grid_collapse_2026_04_21
- recommended_action: superseded marker pointing at DART UI/exclusive/dashboard plans

### coverage_ratchet_policy_2026_04_19.md

- frontmatter: status=active
- checkboxes: 30/11 (73%)
- candidate_classification: partial (Phase 1 done; mid-tier walk-up open)
- duplication_partners: coverage_uplift_bottom5, honest_coverage_metrics, proper_coverage_roadmap
- recommended_action: no edit

### coverage_uplift_bottom5_2026_04_19.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/46 (0%)
- evidence: MTDS migration tests `bfa9086`, `0e04263`
- candidate_classification: partial
- duplication_partners: coverage_ratchet_policy, proper_coverage_roadmap, honest_coverage_metrics
- recommended_action: flip MTDS migration-script todos; audit per-repo coverage delta

### cra_entitlement_backfill_existing_reporting_routes_2026_04_22.md

- frontmatter: status=active, locked_by=live-defi-rollout, depends_on=[fund_administration_service]
- checkboxes: 6/1 (86%)
- evidence: client-reporting-api 5132588; PM 8caae477
- candidate_classification: shipped (1 open = codex doc deferred)
- recommended_action: archive after 1 codex todo lands; ready for [unlock-plan]

### cross_domain_alpha_execution_intelligence_2026_04_11.md

- frontmatter: status=active, **remaining_todos_consolidated_into: consolidated_strategy_and_ui_2026_04_15**
- checkboxes: 0/0
- candidate_classification: superseded
- candidate_superseded_by: consolidated_strategy_and_ui_2026_04_15
- recommended_action: archive (frontmatter consolidation marker is canonical)

### dart_exclusive_subscription_research_fork_2026_04_21.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 13/19 (41%)
- evidence: PM 9f4992c7, e42475b1, 9c5af7b0; UI 148f044b; strategy-service 7e0b6a4
- candidate_classification: live (Phase 3 worker + Phase 4 UI deferred)
- recommended_action: no edit

### dart_ui_strategy_filtering_and_onboarding_2026_04_24.md

- frontmatter: status=in_progress, locked_by=live-defi-rollout
- checkboxes: 0/78 (0%) — many DONE annotations inline
- evidence: MASSIVE — UI 40ab5186, ce22ba42, 12f51cad, 148f044b; UAC bba284f, 9a9242d, 34a1bb3; PM f70926cf, 2a9aa7c7,
  e11a4145, c184bd0c, 8d43fae4, 20c45322
- candidate_classification: live
- candidate_supersedes: GAP_CLASSIFICATION_2026_03_22, PLAN_AMENDMENTS_2026_03_22
- duplication_partners: dart_exclusive_subscription_research_fork, dashboard_services_grid_collapse,
  consolidated_strategy_and_ui_2026_04_15
- recommended_action: substantial flip-pass needed — most work shipped per commit log

### dashboard_services_grid_collapse_2026_04_21.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 23/3 (88%)
- evidence: PM b428117d, ed1f4a2d, 28e96f21, 5bd01b9b, 85c43998
- candidate_classification: shipped
- recommended_action: archive after final 3 todos land; ready for [unlock-plan]

### data_canonicalisation_mvp_2026_04_17.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 33/34 (49%)
- evidence: UAC 89b360d, MTDS 1fa0a8a8/1fd756c, instruments-service 4197d16, bff343c
- candidate_classification: partial
- candidate_superseded_by: manifest_schema_v6_quote_margin_combo_2026_04_23 (continuing work)
- recommended_action: no edit (live MVP execution); cross-ref to manifest v6

### data_catalogue_cleanup_2026_04_24.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/23 (0%)
- evidence: SUBSTANTIAL — UAC 13db4a9, c8191bb, 56feaff; MTDS 2095d1b; instruments-service 4197d16+2f42924;
  strategy-service c1a99f5; UI 40ab5186, 9a9242d
- candidate_classification: partial (most removal/guard shipped; combo-adapter wiring partial; codex pending)
- duplication_partners: defi_data_types_completeness, mtds_per_instrument_download_api,
  manifest_schema_v6_quote_margin_combo
- recommended_action: heavy flip-pass — Phase 1 (remove vendors) + Phase 2 (Hyperliquid/Aster guard) + Phase 4 (DERIBIT
  combo) substantially shipped

## Chunk AB (24 plans — data_pipeline through fund_administration_persistence_swap_in)

### data_pipeline_completion_2026_04_18.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 7/139 (4.8%)
- candidate_classification: live (mega-plan, 20 repos)
- duplication_partners: consolidated_defi_data_pipeline, manifest_schema_v6_quote_margin_combo
- recommended_action: no edit

### data_status_institutional_drilldown_2026_04_24.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 29/0 (100%)
- evidence: c50027a, 0caf2cc, f4a8e4e, e3c0d970, baaacb2c, 3e797631
- candidate_classification: shipped
- recommended_action: archive with [unlock-plan]

### defi-strategy-e2e-automation.md

- frontmatter: none (no YAML)
- checkboxes: 0/0 (446-line workflow guide)
- candidate_classification: orphan
- duplication_partners: defi-strategy-testing-quickstart, defi-strategy-ui-verification
- recommended_action: relocate to `codex/14-playbooks/` or `codex/08-workflows/`

### defi-strategy-testing-quickstart.md

- frontmatter: none
- checkboxes: 0/0 (301-line guide)
- candidate_classification: orphan
- duplication_partners: defi-strategy-e2e-automation, defi-strategy-ui-verification
- recommended_action: relocate to `codex/08-workflows/`

### defi-strategy-ui-verification.md

- frontmatter: none
- checkboxes: 0/67 (0%)
- candidate_classification: partial (aave-lending DONE in prose only)
- duplication_partners: defi-strategy-e2e-automation, defi-strategy-testing-quickstart
- recommended_action: flip aave-lending checkboxes; needs per-strategy execution sweep

### defi_data_types_completeness_2026_04_24.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 20/12 (62.5%)
- evidence: f92645cb, a5a9b71, 9ea51af, d42ffc99
- candidate_classification: partial
- recommended_action: no edit

### defi_full_coverage_expansion_2026_04_09.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 25/4 (86.2%)
- candidate_classification: partial
- recommended_action: review 4 open P1 items

### defi_instrument_pipeline_and_rewards_2026_04_01.md

- frontmatter: status=active, **remaining_todos_consolidated_into: consolidated_defi_data_pipeline_2026_04_15**
- checkboxes: 21/30 (41.2%)
- candidate_classification: superseded
- recommended_action: add superseded_by; archive

### defi_phase3_infrastructure_2026_03_30.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 43/13 (76.8%)
- candidate_classification: partial (P0 batch + P1 Copper sandbox open)
- recommended_action: no edit

### defi_strategies_phase2_2026_03_29.md

- frontmatter: status=active, locked_by=live-defi-rollout, depends_on=[share-class-architecture,
  defi-instrument-pipeline-and-rewards]
- checkboxes: 22/4 (84.6%)
- candidate_classification: partial
- recommended_action: no edit (close to done)

### defi_ui_component_audit_2026_03_31.md

- frontmatter: status=active, owner=hk
- checkboxes: 1/101 (1.0%)
- evidence: UI 8e2007ec (DeFi widget mock cleanup), 44bad44f (strategy-registry v1 deletion)
- candidate_classification: partial
- duplication_partners: ui_unification_v2_sanitisation_2026_04_20 (likely covers same ground)
- recommended_action: human review — Elysium retired, Patrick scope still relevant

### deployment_service_build_infrastructure_repair_2026_04_22.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/0 (YAML `todos:` block, not markdown)
- candidate_classification: live (sports register Plan 12 — known live blocker)
- recommended_action: convert YAML todos to markdown checkboxes

### deployment_topology_and_client_isolation_2026_04_17.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/0 (uses prose phase markers)
- evidence: 77a6a6fb, c0da761, 0d5d450e, 635925fb
- candidate_classification: partial
- candidate_superseded_by: refactor_g2_6_staging_firebase_provisioning_2026_04_20 (folded per G2.6 frontmatter)
- recommended_action: convert phase markers to checkboxes; flip Phase 1+1b complete

### deployment_ui_e2e_uat_2026_04_01.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 11/86 (11.3%)
- evidence: c50027a, e5d2355, f4a8e4e, c9f426d, 9b24eed, 7b1490f
- candidate_classification: partial
- recommended_action: human review — sweep for shipped items

### domain_agnostic_ml_framework_2026_04_11.md

- frontmatter: status=active, **remaining_todos_consolidated_into: consolidated_ml_advanced_pipeline_2026_04_15**
- checkboxes: 0/0
- candidate_classification: superseded
- recommended_action: add superseded_by; archive

### environment_mode_philosophy_audit_2026_04_23.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 4/23 (14.8%)
- evidence: 5584c3de, 8115daa2, ad2a7dfb, d206015e
- candidate_classification: partial
- recommended_action: no edit

### features_sports_pipeline_deployment_2026_04_21.md

- frontmatter: status=active, locked_by=live-defi-rollout, depends_on=[features_sports_denormalisation_pipeline]
- checkboxes: 11/3 (78.6%)
- evidence: 35f18c7, cba6e22, 1a6fb02, d5cae363
- candidate_classification: partial (sports register §12.0 Plan 6 — accurate)
- register_drift (sports): no
- recommended_action: no edit

### features_sports_upstream_coverage_gaps_2026_04_21.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 16/3 (84.2%)
- evidence: 77e7512c, d21e49f, 885131e, 0d6e589
- candidate_classification: partial (1 open = HUMAN unlock)
- register_drift (sports): no — commit-evidence aligns with checkbox state
- recommended_action: no edit

### firestore_security_rules_for_questionnaires_2026_04_21.md

- frontmatter: status=active, locked_by=live-defi-rollout, depends_on=[refactor_g1_10, refactor_g2_6,
  ui_unification_v2_sanitisation]
- checkboxes: 0/6 (0%)
- evidence: UI firestore.rules has /questionnaires/{doc} rule; backend deployment-service rules + Cloud Function +
  Playwright spec missing
- candidate_classification: partial
- duplication_partners: refactor_g2_6_staging_firebase_provisioning
- recommended_action: flip questionnaires-rule checkbox

### five_space_ia_audit_matrix_2026_04_17.md

- frontmatter: none
- checkboxes: 0/0 (audit worksheet)
- candidate_classification: orphan
- duplication_partners: five_space_ia_execution_child_plan
- recommended_action: relocate to `codex/05-infrastructure/` or `plans/audits/`

### five_space_ia_execution_child_plan_2026_04_17.md

- frontmatter: none (table-driven backlog)
- checkboxes: 0/0
- candidate_classification: partial (P0 items 1-11 self-reported "Shipped"; P1 gates on G2.6)
- duplication_partners: five_space_ia_audit_matrix, refactor_g2_6_staging_firebase_provisioning
- recommended_action: convert to canonical checkboxes

### fold_uei_into_utl_2026_04_17.md

- frontmatter: status=active
- checkboxes: 0/0 (prose narrative)
- evidence: STRONG — UTL events sub-package shipped; UEI repo absent; CLAUDE.md canonical import path; MTDS/FSS
  pyproject cleansed
- candidate_classification: shipped
- recommended_action: archive plan

### full_qg_sweep_all_services_2026_03_28.md

- frontmatter: status=active, owner=human, locked_by=live-defi-rollout
- checkboxes: 0/30 (0%)
- candidate_classification: partial
- duplication_partners: coverage_ratchet_policy, coverage_uplift_bottom5, honest_coverage_metrics,
  proper_coverage_roadmap
- recommended_action: human review

### fund_administration_persistence_swap_in_2026_04_22.md

- frontmatter: status=active, locked_by=live-defi-rollout,
  depends_on=[fund_administration_service_and_pooled_subscription_redemption]
- checkboxes: 0/11 (0%)
- candidate_classification: live
- recommended_action: no edit

## Chunk AC (24 plans — fund_administration_phase6 through mtds_multi_dimensional_shard_architecture)

### fund_administration_phase6_plus_followups_FINISHER_DISPATCH_PROMPT.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/0 (prompt-only meta file)
- candidate_classification: orphan
- duplication_partners: fund_administration_service_and_pooled_subscription_redemption_2026_04_20,
  fund_administration_signoff_walkthrough_2026_04_22
- recommended_action: archive (work largely shipped; CRA `8caae477`)

### fund_administration_service_and_pooled_subscription_redemption_2026_04_20.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/0 (YAML todos)
- evidence: PM 8caae477 (CRA backfill - workstream C); ed1f4a2d (disk-artifact audit)
- candidate_classification: partial (Workstream C done; A/D/E operator-gated)
- recommended_action: convert YAML to checkboxes

### fund_administration_signoff_walkthrough_2026_04_22.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/27 (0%)
- candidate_classification: live (gated on Cloud Run staging deploy)
- recommended_action: no edit

### honest_coverage_metrics_2026_04_19.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 5/6 (45%)
- evidence: UTL 8763fab5 (Phase A capture_status); MTDS 84c43ab; instruments-service bff343c
- candidate_classification: partial
- duplication_partners: institutional_smoke_matrix, manifest_429_per_vm_sharding
- recommended_action: flip Phase A done; verify remaining 6

### hybrid_sampler_5s_resolution_2026_03_30.md

- frontmatter: status=active (no lock)
- checkboxes: 1/8 (11%)
- evidence: none found — no recent commits matching sampler/oddspapi
- candidate_classification: orphan (stalled since 2026-03-30)
- recommended_action: add orphan flag; consider archive

### institutional_smoke_matrix_2026_04_20.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/0 (YAML todos / pivot note)
- evidence: PM 1fce53d3, 939726c3, 47c5fd7a, 4d599b72, 0852d0be (Phase 1-5); 9a39ebef (coverage-matrix smoke);
  instruments-service 5e2e141
- candidate_classification: shipped (pivoted; canonical gate now in system-integration-tests)
- recommended_action: convert YAML to checkboxes; archive

### instrument_schema_cohesion_and_market_hours_2026_03_31.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 36/14 (72%)
- evidence: instruments-service cdded95, 9bf23d8, 7f2cbf0; PM 4297379f
- candidate_classification: partial
- duplication_partners: mtds_canonical_sharding_alignment, manifest_schema_v6
- recommended_action: audit remaining 14

### instruments_service_orchestrator_reliability_fixes_2026_04_21.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 12/8 (60%)
- evidence: instruments-service 7f2cbf0 (Bug 4), 80b9b21 (Bugs 2+3+AF), 8a91324 (WEATHER+XG); PM bb507330
- candidate_classification: partial (sports register §12.0 Plan 4 — exact match)
- register_drift (sports): no
- recommended_action: flip remaining shipped items; verify Bugs 7-8

### instruments_service_template_refactor_8e653acc.md

- frontmatter: **remaining_todos_consolidated_into: consolidated_operational_validation_2026_04_15**
- checkboxes: 0/0 (YAML todos with status: completed inline)
- candidate_classification: superseded
- recommended_action: add canonical superseded_by + status=superseded

### instruments_service_write_gate_validation_2026_04_22.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 13/5 (72%)
- evidence: UTL c1987760+c397ab56, instruments-service 454cca3+d049d8b, PM 7005c26d
- candidate_classification: partial (warn-mode live; Phase 3a + strict flip pending)
- recommended_action: flip remaining shipped items

### live_frontend_integration_e2e_audit_2026_04_15.md

- frontmatter: status=active (no lock)
- checkboxes: 0/0 (YAML todos)
- evidence: PM ad2a7dfb + 5584c3de; tier-based dev-tiers.sh; UI strategy-eval/admin
- candidate_classification: partial
- duplication_partners: ml_pipeline_ui_integration_2026_04_16
- recommended_action: convert YAML to checkboxes

### manifest_429_per_vm_sharding_2026_04_25.md

- frontmatter: status=active, locked_by=live-defi-rollout, related_plans=[availability_manifest_v4, manifest_schema_v6]
- checkboxes: 9/14 (39%)
- evidence: UTL c95480de, d8d5f22c, 31a5bef7, f40481d7
- candidate_classification: partial (created 2026-04-25; UTL primitives landed)
- duplication_partners: manifest_schema_v6_quote_margin_combo, honest_coverage_metrics
- recommended_action: flip Phase 1+3 done

### manifest_schema_v6_quote_margin_combo_2026_04_23.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/15 (0%)
- evidence: UTL 7c6f155a (Schema v6); MTDS 1fc, 0b8ab42, 1fd756c (v6 settlement-dimension threading + chain-bundle);
  4197d16 deribit_combo_adapter
- candidate_classification: partial (v6 substantially shipped; checkboxes severely behind)
- duplication_partners: manifest_429_per_vm_sharding (related_plans)
- recommended_action: flip many shipped items — UTL + MTDS implementing v6

### manual_trade_booking_reconciliation_2026_03_22.md

- frontmatter: status=active, **remaining_todos_consolidated_into: consolidated_operational_validation_2026_04_15**
- checkboxes: 0/0 (YAML todos)
- candidate_classification: superseded
- recommended_action: add canonical superseded_by

### marketing_homepage_old_hero_migration_2026_04_22.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 17/6 (74%)
- evidence: PM 4fa2f158, cf786114
- candidate_classification: partial
- duplication_partners: marketing_site_audit_manifest_2026_04_20
- recommended_action: flip more shipped items

### marketing_site_audit_manifest_2026_04_20.md

- frontmatter: status=active, locked_by=live-defi-rollout, companion_to=marketing_site_restructure_2026_04_20.md
- checkboxes: 0/0 (manifest)
- evidence: parent unlock per d2aa8c42; PM 8835a271, a7f970b1
- candidate_classification: shipped (companion manifest, parent already unlocked)
- recommended_action: archive

### mev_protection_and_execution_enhancements_2026_04_01.md

- frontmatter: status=active, **remaining_todos_consolidated_into: consolidated_defi_data_pipeline_2026_04_15**
- checkboxes: 13/17 (43%)
- candidate_classification: superseded
- recommended_action: add canonical superseded_by + status=superseded

### ml_pipeline_revolution_2026_04_11.md

- frontmatter: status=active, **remaining_todos_consolidated_into: consolidated_ml_advanced_pipeline_2026_04_15**
- checkboxes: 0/0 (YAML todos)
- evidence: ml-training d53c2ea (architecture-v2 phase 10 walk-forward); ml-inference d6744d0 (calibration)
- candidate_classification: superseded
- recommended_action: add canonical superseded_by

### ml_pipeline_ui_e2e_browser_validation_AGENT_PROMPT.md

- frontmatter: none
- checkboxes: 0/5 (0%)
- candidate_classification: orphan (validation prompt)
- recommended_action: archive prompt file

### ml_pipeline_ui_integration_2026_04_16.md

- frontmatter: status=active (no lock)
- checkboxes: 0/0 (YAML todos)
- evidence: ml-training d53c2ea; ml-inference 8b4fb8b, aac5cee, a1bb6b2
- candidate_classification: partial
- duplication_partners: ml_pipeline_revolution, live_frontend_integration_e2e_audit
- recommended_action: convert YAML to checkboxes

### ml_pipeline_ui_integration_2026_04_16_AGENT_PROMPT.md

- frontmatter: none
- checkboxes: 0/0
- candidate_classification: orphan
- recommended_action: archive prompt file

### mtds_canonical_sharding_alignment_2026_03_31.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 14/9 (61%)
- evidence: MTDS 4cac3f1, 2947dd2, 553b8b9, ab6338b; PM 2e739e90, ca0ad498
- candidate_classification: partial
- duplication_partners: mtds_multi_dimensional_shard_architecture, manifest_schema_v6
- recommended_action: flip Phase 2 + per-instrument shipped items

### mtds_defi_data_normalization_2026_04_14.md

- frontmatter: status=active, **remaining_todos_consolidated_into: consolidated_defi_data_pipeline_2026_04_15**
- checkboxes: 0/0 (YAML todos)
- candidate_classification: superseded
- recommended_action: add canonical superseded_by

### mtds_multi_dimensional_shard_architecture_2026_04_12.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/16 (0%)
- evidence: UTL d8d5f22c, 31a5bef7, f40481d7, 7c6f155a, 8763fab5; MTDS 1fc, 0b8ab42
- candidate_classification: partial (heavily overlaps manifest_schema_v6 + manifest_429)
- duplication_partners: manifest_schema_v6_quote_margin_combo, manifest_429_per_vm_sharding,
  mtds_canonical_sharding_alignment, honest_coverage_metrics
- recommended_action: flip many done items

## Chunk AD (25 plans — mtds_per_instrument through refactor_g3_1)

### mtds_per_instrument_download_api_2026_04_24.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/14 (0%)
- evidence: dc3357f2 (plan added)
- candidate_classification: live (1 day old; new public API not yet shipped)
- recommended_action: no edit

### non_apifootball_provider_backfill_launchers_2026_04_21.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 5/2 (71%)
- evidence: d2d94cde, 36b75bf9
- candidate_classification: partial (sports register §12.0 Plan 3 — exact match)
- register_drift (sports): no
- recommended_action: no edit

### path_to_100m_finalization_2026_04_20.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout, depends_on=playbook_ssot_stage_2
- checkboxes: 0/51 (0%)
- evidence: 81202a77 (creation); /our-story essay ffedd63 + /story timeline a14efed; competitive landscape 372-line
- candidate_classification: partial
- duplication_partners: playbook_ssot_stage_2
- recommended_action: no edit (large multi-domain; many adjacent commits)

### platform_strategy_families_and_haruko_gaps_2026_03_28.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout
- checkboxes: 26/4 (87%)
- evidence: f5c9d80a (folded into G2.10 explicitly)
- candidate_classification: superseded
- candidate_superseded_by: refactor_g2_10_allocator_ui_split_2026_04_20
- recommended_action: add superseded_by=refactor_g2_10

### playbook_ssot_stage_1_rules_2026_04_19.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout, blocks=stage_2+stage_3
- checkboxes: 4/21 (16%)
- evidence: a7aa782c (initial 3-stage plan), 26a87c64 (Stage 1 rules 01/02/05/06/07/09/10 + IM template)
- candidate_classification: partial (substantial Stage 1 ship not reflected)
- recommended_action: flip checkboxes for rules 01/02/05/06/07/09/10 + IM template + README per 26a87c64

### playbook_ssot_stage_2_doc_rewrite_2026_04_19.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout, depends_on=stage_1
- checkboxes: 0/51 (0%)
- candidate_classification: live (blocked on Stage 1 progress)
- recommended_action: no edit

### playbook_ssot_stage_3_infra_spec_2026_04_19.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout,
  supersedes_on_completion=/codex/14-customer-journeys/roadmap/next-waves.md
- checkboxes: 0/25 (0%)
- evidence: a7aa782c; G1.6 derivation-engine ship per Option-X memory; G2.x refactor wave (eef08911, f5c9d80a, 0bed08bc)
- candidate_classification: partial
- recommended_action: no edit (downstream G2.x plans are the actual carriers)

### pod_crypto_administrator_integration_2026_04_22.md

- frontmatter: status=active, locked_by=live-defi-rollout, depends_on=tradfi_fund_administrator_selection sibling
- checkboxes: 0/28 (0%)
- evidence: 9d2384ad (plan expanded), df749751 (POD crypto-only); ed1f4a2d
- candidate_classification: partial
- duplication_partners: tradfi_fund_administrator_selection_2026_04_22
- recommended_action: no edit

### polymarket_prediction_pipeline_2026_03_25.md

- frontmatter: status=active, **remaining_todos_consolidated_into: consolidated_sports_prediction_pipeline_2026_04_15**
- checkboxes: 0/0 (YAML status: done=10/17)
- candidate_classification: superseded
- recommended_action: add canonical superseded_by

### portal_local_smoke_checklist_2026_04_19.md

- frontmatter: none (no YAML)
- checkboxes: 3/19 (using ☐/☑ glyphs)
- candidate_classification: orphan (repeatable checklist, not .md)
- recommended_action: add orphan flag — relocate to codex/14-playbooks/ or scripts/

### presentation_service_alignment_2026_04_13.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 1/46 (2%)
- evidence: 50f1b5ec (drift cleanup); marketing USP overhaul session memory (uncommitted)
- candidate_classification: partial
- duplication_partners: path_to_100m_finalization
- recommended_action: no edit

### proper_coverage_roadmap_2026_04_20.md

- frontmatter: status=active, locked_by=live-defi-rollout, depends_on=honest_coverage_metrics
- checkboxes: 0/0 (YAML id-list; 14 todo blocks)
- evidence: 6059a153, a2b1ea21, 35bf7077; manifest v6 3d041d81
- candidate_classification: partial
- duplication_partners: honest_coverage_metrics_2026_04_19
- recommended_action: no edit

### questionnaire_response_sync_script_2026_04_22.md

- frontmatter: status=active, P2, locked_by=live-defi-rollout
- checkboxes: 3/5 (37%)
- evidence: 9249f0da, 3e4e11ee
- candidate_classification: partial (script not yet shipped per memory)
- recommended_action: no edit

### refactor_g2_10_allocator_ui_split_2026_04_20.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout, depends_on=stage-3e+G2.1+G2.8+platform_strategy_families
  (folded)
- checkboxes: 0/17 (0%)
- evidence: f5c9d80a, 0c779475, 02b68d2d, eef08911, DART UI Phase 9-10 f70926cf/2a9aa7c7
- candidate_classification: partial (DART UI Phase 9-10 shipped per memory)
- candidate_supersedes: platform_strategy_families_and_haruko_gaps_2026_03_28 (folded)
- recommended_action: add supersedes; review DART UI evidence per todo

### refactor_g2_11_account_intelligence_record_crm_2026_04_20.md

- frontmatter: status=active, P1, locked_by=live-defi-rollout, depends_on=stage-3e+ui_unification_v2 phase 6
- checkboxes: 0/12 (0%)
- evidence: a4b7ae26 (signup-signin codex)
- candidate_classification: live (codex foundations laid; admin surface not yet built)
- duplication_partners: refactor_g2_1
- recommended_action: no edit

### refactor_g2_1_org_scoped_jwt_claims_2026_04_20.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout, depends_on=stage-3e+G2.6+user_management_merge (folded)
- checkboxes: 0/17 (0%)
- evidence: a4b7ae26, aff540df, 53a5e915
- candidate_classification: partial (codex shipped; backend JWT not yet)
- candidate_supersedes: user_management_merge_2026_03_23 (folded)
- recommended_action: no edit (operator-gated on Firebase staging G2.6)

### refactor_g2_2_per_client_api_key_issuance_2026_04_20.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout, depends_on=stage-3e+G2.1+G2.6+user_management_merge
  (folded)
- checkboxes: 0/17 (0%)
- candidate_classification: live
- candidate_supersedes: user_management_merge_2026_03_23 (folded)
- recommended_action: no edit (operator-gated on G2.6)

### refactor_g2_3_data_catalogue_refactor_2026_04_20.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout, depends_on=stage-3e+G1.6+G2.9 gap #5
- checkboxes: 0/14 (0%)
- evidence: 8d43fae4 (regen-catalogue.sh), bba284f UAC envelope, manifest v6 3d041d81; DART UI Phase 11 deferred per
  memory
- candidate_classification: partial
- duplication_partners: refactor_g2_4, refactor_g2_5
- recommended_action: no edit (catalogue artefacts shipped; UI rendering deferred)

### refactor_g2_4_ml_model_catalogue_refactor_2026_04_20.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout, depends_on=stage-3e+G1.6+G1.8+G2.9 gaps#6+#11+G1.5
  (absorbed)
- checkboxes: 0/16 (0%)
- evidence: 32ccd727 (G1.5 5 broken hrefs), DART UI Phase 11 5-dim catalogue e11a4145 + UAC envelope bba284f
- candidate_classification: partial
- candidate_supersedes: refactor_g1_5_ml_catalogue_broken_hrefs_cleanup_2026_04_20 (absorbed)
- recommended_action: add supersedes=refactor_g1_5

### refactor_g2_5_execution_algo_catalogue_refactor_2026_04_20.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout, depends_on=stage-3e+G1.6+G2.9 gaps#7+#10
- checkboxes: 0/19 (0%)
- candidate_classification: live (refactor pending)
- duplication_partners: refactor_g2_3, refactor_g2_4
- recommended_action: no edit

### refactor_g2_6_staging_firebase_provisioning_2026_04_20.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout, depends_on=stage-3e+deployment_topology
  (folded)+five_space ticket #12 (folded)
- checkboxes: 0/17 (0%)
- evidence: 952dc4f3 (naming-convention reference table); env-mode ad2a7dfb + QG gate 5584c3de
- candidate_classification: partial (operator-blocked — 5-plan blocker)
- candidate_supersedes: deployment_topology_and_client_isolation_2026_04_17 (folded),
  five_space_ia_execution_child_plan_2026_04_17 ticket #12 (folded)
- recommended_action: add supersedes=deployment_topology_and_client_isolation

### refactor_g2_7_demo_provisioning_automation_2026_04_20.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout, depends_on=stage-3e+G2.1+G2.6+G1.7+defi_demo_e2e (folded)
- checkboxes: 0/15 (0%)
- evidence: 1baea733, 9b048896, 7a4b90f2 (restriction-profile)
- candidate_classification: partial (Resend + restriction-profile foundations shipped)
- candidate_supersedes: defi_demo_e2e_workflow_2026_03_30 (folded)
- recommended_action: add supersedes=defi_demo_e2e_workflow

### refactor_g2_8_fund_business_unit_registry_2026_04_20.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout, depends_on=stage-3e+share_class_architecture (folded)
- checkboxes: 6/8 (43%)
- evidence: eef08911 (Phases A+B shipped; Phase C deferred to G2.10); UAC 48bf6ee
- candidate_classification: partial (most-progressed G2 plan)
- candidate_supersedes: share_class_architecture_2026_04_01 (folded)
- recommended_action: add supersedes=share_class_architecture

### refactor_g2_9_uac_remaining_gaps_2026_04_20.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout, depends_on=stage-3e+UAC e6f7c6d V2 drop
- checkboxes: 0/33 (0%)
- evidence: 3e4e11ee (V2 drop), 48bf6ee
- candidate_classification: partial
- duplication_partners: refactor_g2_3, refactor_g2_4, refactor_g2_5, refactor_g2_8
- recommended_action: no edit

### refactor_g3_1_pricing_engine_service_2026_04_20.md

- frontmatter: status=active, P1, locked_by=live-defi-rollout, depends_on=stage-3e+G1.6+G3.2+G2.2
- checkboxes: 0/14 (0%)
- evidence: 0bed08bc (plan added); no pricing-engine code grep hits
- candidate_classification: live
- recommended_action: no edit

## Chunk AE (25 plans — refactor_g3_2 through sports_scheduler_cron_activation)

### refactor_g3_2_pricing_numbers_from_finance_2026_04_20.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 5/7 (42%)
- evidence: 89c8982c (flips A/B/C/D), 0b647cdf, eacd2f8f
- candidate_classification: partial (commit anchor claims A/B/C/D done — checkbox state may have been re-opened by
  concurrent agent)
- recommended_action: verify 4 phase parents; Phase C finance-led may legitimately remain open

### refactor_g3_3_briefings_cms_migration_2026_04_20.md

- frontmatter: status=active, locked_by=live-defi-rollout, depends_on=stage-3e+g1_12
- checkboxes: 0/12 (0%)
- candidate_classification: orphan (zero progress; briefings still hardcoded markdown)
- recommended_action: no edit (verify still-relevant)

### refactor_g3_4_dart_rebrand_trademark_check_2026_04_20.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/14 (0%)
- candidate_classification: orphan (operator/marketing work, no code)
- recommended_action: no edit (operator-gated)

### refactor_g3_5_codex_sync_consistency_agents_2026_04_20.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/11 (0%)
- candidate_classification: orphan (anchors c9e38326/c184bd0c don't match scope — those are strategy lifecycle work)
- recommended_action: no edit

### remove_data_types_field_2026_04_10.md

- frontmatter: status=active, locked_by=live-defi-rollout, **remaining_todos_consolidated_into:
  consolidated_operational_validation_2026_04_15**
- checkboxes: 0/0
- candidate_classification: superseded
- recommended_action: archive ([unlock-plan])

### resend_email_architecture_2026_04_23.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/14 (0%)
- evidence: 2367f803 ("Resend email arch"), 0e2c8db2, 42861841, 7b024e6a, ecf28934, 148f044b, 1a10bed6, a8394b5c,
  66f3c7fc
- candidate_classification: shipped (matches MEMORY's 2026-04-25 14-commit DDQ session)
- recommended_action: flip Phase 1, 2a/b/c/d, 3a/b, 4a/b — all shipped; biggest checkbox gap

### sfi_chunk_parallel_backfill_2026_04_22.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 7/9 (44%)
- evidence: 0d6e589 (Option 2 shipped), c1987760+c397ab56 (UTL InstrumentsWriteGate)
- candidate_classification: partial (Option 2 shipped; Option 1 GCS-lease deferred)
- register_drift (sports): n/a (not in §12.0)
- recommended_action: flip Phase 0+3

### signal_leasing_broadcast_architecture_2026_04_20.md

- frontmatter: status=active, P0, depends_on=path_to_100m_finalization
- checkboxes: 85/0 (100%)
- evidence: ee122a0, 4d5b73f, 84bc169, 3078c4a, 6e6fd8d, 1fa2557, 4fe8e02, 07ac1f7
- candidate_classification: shipped (header explicitly says "All 8 phases complete")
- recommended_action: no edit (awaiting human [unlock-plan])

### smoke_dep_chain_tactical_fixes_2026_04_20.md

- frontmatter: status=active, locked_by=live-defi-rollout, depends_on=institutional_smoke_matrix
- checkboxes: 0/0 (narrative)
- evidence: instruments-service e6e50c7, UTL 4ee91009, deployment-service 2163ec3, MTDS 1363e3f, 81b1b6f
- candidate_classification: shipped (Phase A bucket-naming fixes shipped per body text)
- candidate_superseded_by: universe_ssot_fix_2026_04_20 (Phase B)
- duplication_partners: institutional_smoke_matrix_2026_04_20
- recommended_action: archive Phase A as shipped + add superseded_by=universe_ssot_fix for Phase B

### sports_batch_pipeline_end_to_end_2026_03_25.md

- frontmatter: status=active, locked_by=live-defi-rollout, **remaining_todos_consolidated_into:
  consolidated_sports_prediction_pipeline_2026_04_15**
- checkboxes: 0/0
- candidate_classification: superseded
- register_drift (sports): NOT in §12.0
- recommended_action: archive ([unlock-plan])

### sports_data_completeness_2026_04_14.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout
- checkboxes: 3/23 (12%)
- evidence: indirectly covered by §12.0 Plans 2/4/9/11 work
- candidate_classification: partial
- candidate_superseded_by: candidate sports_data_pipeline_comprehensive_2026_04_16
- duplication_partners: sports_data_pipeline_comprehensive_2026_04_16, sports_feature_completion_2026_04_10, register
  Plans 2/4/9/11
- register_drift (sports): yes — work shipped via Plans 4/9/11 but checkbox state 12%
- recommended_action: add superseded_by=sports_data_pipeline_comprehensive_2026_04_16

### sports_data_migration_mapping_plan_2026_03_26.md

- frontmatter: status=active, locked_by=live-defi-rollout, depends_on=sports-integration-01/02 + sports-batch-pipeline
- checkboxes: 5/27 (16%)
- candidate_classification: partial / candidate orphan (deps consolidated/superseded)
- candidate_superseded_by: candidate consolidated_sports_prediction_pipeline_2026_04_15
- register_drift (sports): yes — not in §12.0
- recommended_action: add superseded_by=consolidated_sports_prediction_pipeline_2026_04_15

### sports_data_pipeline_comprehensive_2026_04_16.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout
- checkboxes: 0/67 (0%)
- evidence: massive overlap with §12.0 Plans 2/4/6/9/11
- candidate_classification: partial (umbrella; concrete work tracked in §12.0)
- candidate_supersedes: sports_data_completeness_2026_04_14, sports_data_migration_mapping_plan_2026_03_26
- candidate_superseded_by: candidate sports_roadmap_master_execution_2026_04_21
- duplication_partners: sports_data_completeness, sports_data_migration_mapping, sports_roadmap_master_execution, §12.0
  Plans 2/4/6/9/11
- register_drift (sports): yes — 0/67 but huge §12.0 evidence
- recommended_action: add superseded_by=sports_roadmap_master_execution_2026_04_21

### sports_e2e_validation_2026_03_27.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout
- checkboxes: 9/23 (28%)
- candidate_classification: partial
- candidate_supersedes: sports_batch_pipeline_end_to_end (per body text)
- register_drift (sports): not in §12.0
- recommended_action: add supersedes=[sports_batch_pipeline_end_to_end] formally

### sports_feature_completion_2026_04_10.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout
- checkboxes: 0/41 (0%)
- evidence: §12.0 Plan 6 + denormalisation §12.1 (ef1e89f + c7a363d) cover some
- candidate_classification: partial / orphan
- candidate_superseded_by: candidate sports_data_pipeline_comprehensive_2026_04_16 OR sports_integration_04
- register_drift (sports): not in §12.0 but overlaps Plan 6
- recommended_action: add superseded_by=sports_data_pipeline_comprehensive_2026_04_16

### sports_integration_01_reference_data_pipeline_2026_03_25.md

- frontmatter: **remaining_todos_consolidated_into: consolidated_sports_prediction_pipeline_2026_04_15**
- checkboxes: 0/0 (frontmatter notes C4 DONE)
- candidate_classification: superseded
- register_drift (sports): NOT in §12.0
- recommended_action: archive

### sports_integration_02_odds_market_data_pipeline_2026_03_25.md

- frontmatter: same consolidation marker
- checkboxes: 0/0
- candidate_classification: superseded
- recommended_action: archive

### sports_integration_03_features_provider_integration_2026_03_25.md

- frontmatter: same
- checkboxes: 0/0
- candidate_classification: superseded
- recommended_action: archive

### sports_integration_04_feature_calculators_full_2026_03_25.md

- frontmatter: same
- checkboxes: 0/0
- candidate_classification: superseded
- recommended_action: archive

### sports_integration_05_ml_training_pipeline_2026_03_25.md

- frontmatter: same
- checkboxes: 0/0
- candidate_classification: superseded
- recommended_action: archive

### sports_integration_06_strategy_execution_gcs_migration_2026_03_25.md

- frontmatter: same
- checkboxes: 0/0
- candidate_classification: superseded
- recommended_action: archive

### sports_live_streaming_viz_2026_04_15.md

- frontmatter: status=active, NO locked_by
- checkboxes: 0/0
- candidate_classification: orphan (no checkboxes, no lock, no evidence)
- recommended_action: flag for review (may need restructure or archive)

### sports_manifest_shard_migration_cleanup_2026_04_21.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout,
  depends_on=instruments_service_orchestrator_reliability_fixes
- checkboxes: 11/5 (69%)
- evidence: utl_manifest_migration_primitives DONE (b2ad7d0c); 5f2cae3, d194288
- candidate_classification: partial (matches §12.0 Plan 9: 11/5 half-way)
- register_drift (sports): no — exact §12.0 match
- recommended_action: no edit

### sports_roadmap_master_execution_2026_04_21.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout
- checkboxes: 18/3 (86%)
- candidate_classification: partial (orchestrator complete; Phase 6 gated on Plans 12+13)
- candidate_supersedes: candidate sports_data_pipeline_comprehensive_2026_04_16
- register_drift (sports): no (register is materialised view of this plan)
- recommended_action: no edit

### sports_scheduler_cron_activation_2026_04_21.md

- frontmatter: status=active, P0, locked_by=live-defi-rollout, depends_on=sports_scheduler_periodic_tier_dispatch
- checkboxes: 7/4 (64%)
- evidence: 48af45c (sports-scheduler VM-daemon launcher); §12.0 Plan 5 marked "live via VM-daemon ✅"
- candidate_classification: live (Cloud Run gated on Plans 12+13)
- duplication_partners: Plans 12+13
- register_drift (sports): no — exact §12.0 match (7/4)
- recommended_action: no edit

## Chunk AF (20 plans — sports_uac_schema through vm_deployment_registry)

### sports_uac_schema_contracts_registration_2026_04_24.md

- frontmatter: status=active, completed=2026-04-25
- checkboxes: 20/0 (100%)
- evidence: UAC 4810ced, cbd8047, a7eb167, cf79d54
- candidate_classification: shipped
- register_drift (sports): no
- recommended_action: flip status to complete; archive

### strategy_architecture_v2_finalization_2026_04_19.md

- frontmatter: status=active, locked_by=live-defi-rollout, supersedes=strategy_architecture_v2_2026_04_17.md
- checkboxes: 50/46 (52%)
- evidence: 28fc19b, 0b94e8c, d51f54c (Tier-2 cutover); 9cba8cf, 542f058 (Phase 10 catalogue); 62721e7, 740f2ba, d2c9780
  (Phase 5/11); a7b63ce (legacy v1 backtest delete); 8f6e33c (legacy fence)
- candidate_classification: partial
- duplication_partners: strategy_architecture_v2_phase3_11_handoff_2026_04_17.md
- recommended_action: flip Tier-2 cutover, ledger persistence, Phase 10 catalogue, Phase 5/11, legacy v1 backtest

### strategy_architecture_v2_phase3_11_handoff_2026_04_17.md

- frontmatter: status=active, locked_by=live-defi-rollout, depends_on=strategy_architecture_v2_2026_04_17.md
- checkboxes: 20/60 (25%)
- evidence: ec4ea26, 96aae04, 05a916e (Phase 3); 5525188, 27de78c, 13fa4e7 (Phase 5); 3326f9d, a656f91 (Phase 7);
  aa3c6c0 (Phase 10); 62721e7, 740f2ba (Phase 11); 7bf7b6e, 62e69f3 (Phase 1d/1f)
- candidate_classification: partial
- duplication_partners: strategy_architecture_v2_finalization_2026_04_19
- recommended_action: flip Phase 3, 5, 7, 10, 11; keep Phase 4 + 53-strategy migration open

### strategy_lifecycle_visibility_ui_2026_04_11.md

- frontmatter: status=active, locked_by=live-defi-rollout, **remaining_todos_consolidated_into:
  consolidated_strategy_and_ui_2026_04_15**
- checkboxes: 0/0
- evidence: Plan A archived (07efcb5d [unlock-plan])
- candidate_classification: superseded
- recommended_action: add canonical superseded_by; request [unlock-plan]

### strategy_registry_v1_delete_consumer_audit.md

- frontmatter: NOT YAML (top-of-file declares completion)
- checkboxes: 0/0 (manifest doc)
- evidence: parent plan archived; UI Wave 7 done per memory
- candidate_classification: superseded
- candidate_superseded_by: strategy_registry_v1_delete_and_consumer_migration_2026_04_21.md (already archived)
- recommended_action: move to archive/ alongside parent OR convert to codex SSOT

### tardis_canonical_path_full_streaming_2026_04_22.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 18/0 (100%)
- evidence: MTDS 5ec195f; PM a3501b13, 920c9ec0
- candidate_classification: shipped
- recommended_action: flip to status=complete; remove locked_by per [unlock-plan]; archive

### tardis_iter_chunked_streaming_p2a_2026_04_23.md

- frontmatter: status=complete, no locked_by
- checkboxes: 9/2 (82%)
- evidence: MTDS 81f0fa4; PM a6bc816e, f6627cd3
- candidate_classification: shipped (frontmatter already complete; 2 stragglers test-only)
- recommended_action: flip 2 test checkboxes if landed; archive

### tiered_help_chatbot_2026_03_22.md

- frontmatter: status=active, P1, locked_by=live-defi-rollout
- checkboxes: 0/0 (YAML todos)
- evidence: unified-trading-api/routes/chat.py exists matching plan; UI ChatWidget NOT FOUND
- candidate_classification: partial
- recommended_action: convert YAML to checkboxes; flip backend, mark UI open

### tradfi_fund_administrator_selection_2026_04_22.md

- frontmatter: status=active, locked_by=live-defi-rollout, depends_on=fund_administration_service
- checkboxes: 0/7 (0%)
- evidence: PM 9cb1232b, dacb02d2, 501ed974 — touch upstream but selection pending
- candidate_classification: live (operator-blocked)
- recommended_action: no edit

### trading_widget_merge_audit_2026_04_22.md

- frontmatter: status=complete
- checkboxes: 0/0
- evidence: 30+ widget refactor commits
- candidate_classification: shipped
- recommended_action: archive

### transfermarkt_sfi_team_mapping_cache_and_drift_detection_2026_04_22.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 20/2 (91%)
- evidence: instruments-service 9bf23d8; UAC 36bed50; instruments-service cdded95; PM e5d941e1, f7302102
- candidate_classification: shipped (with 2 polish items; matches §12.0 Plan 11)
- register_drift (sports): no
- recommended_action: review remaining 2; archive when done

### trigger_based_reference_data_2026_04_13.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 2/18 (10%)
- evidence: instruments-service 930fead, d5dfa3db, 638aca2; UAC 36bed50
- candidate_classification: partial
- duplication_partners: transfermarkt_sfi_team_mapping_cache_and_drift_detection
- recommended_action: re-audit 18 open todos against shipped commits

### ui_walkthrough_and_e2e_alignment_2026_04_01.md

- frontmatter: status=active, locked_by=live-defi-rollout, **remaining_todos_consolidated_into:
  consolidated_strategy_and_ui_2026_04_15**
- checkboxes: 0/32 (0%)
- candidate_classification: superseded
- recommended_action: add canonical superseded_by; request [unlock-plan]

### unified_backtest_pipeline_wiring_2026_04_16.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/0
- evidence: strategy-service a7b63ce, aa3c6c0, 2d05e58 (Phase 10 backtest unification)
- candidate_classification: partial
- candidate_superseded_by: strategy_architecture_v2_phase3_11_handoff_2026_04_17.md Phase 10
- recommended_action: convert to checkboxes OR mark superseded_by

### unified_pipeline_scheduling_and_triggers_2026_04_15.md

- frontmatter: status=active, **remaining_todos_consolidated_into: consolidated_operational_validation_2026_04_15**
- checkboxes: 0/0
- candidate_classification: superseded
- recommended_action: add canonical superseded_by

### universe_ssot_fix_2026_04_20.md

- frontmatter: status=active, locked_by=live-defi-rollout, depends_on=smoke_dep_chain_tactical_fixes
- checkboxes: 0/0
- evidence: instruments-service 2587a26; PM 39c93177; d049d8b
- candidate_classification: partial
- duplication_partners: venue_availability_ssot_2026_03_25
- recommended_action: convert to checkboxes

### user_management_merge_2026_03_23.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 49/5 (91%)
- evidence: ARCHIVED user-management-ui dir (only ARCHIVED.md + Dockerfile remain); UTSU (ops)/admin/\* carries 14+
  admin pages
- candidate_classification: shipped
- recommended_action: flip 5 remaining; mark complete; request [unlock-plan]

### utl_base_image_rebuild_and_workflow_unblock_2026_04_22.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/17 (0%)
- evidence: UTL fb677546, 9be20d88, 6bfaa9f5, 1d63189d, ccdc6c8c (5 commits attempting fix)
- candidate_classification: live (sports register Plan 13 — known live blocker)
- recommended_action: re-audit 17 open todos against the 5 UTL commits

### venue_availability_ssot_2026_03_25.md

- frontmatter: status=active, locked_by=live-defi-rollout, depends_on=instrument-schema-cohesion-and-market-hours, P0
- checkboxes: 22/3 (88%)
- evidence: instruments-service 2587a26; UAC 68afe6e, 1515f98
- candidate_classification: shipped (with 3 polish items)
- duplication_partners: universe_ssot_fix_2026_04_20
- recommended_action: flip venue_start_dates deletion if completed

### vm_deployment_registry_reaper_and_ssot_2026_04_21.md

- frontmatter: status=active, locked_by=live-defi-rollout
- checkboxes: 0/19 (0%)
- evidence: deployment-service 1c2282f, 7a73d72 (partial scaffolding)
- candidate_classification: live
- recommended_action: no edit

## Pass 3 — Cross-plan duplication scan (top duplication clusters)

| Cluster                                              | Plans                                                                                                                                                                                                                                                                                                                                                                                                                 | Authoritative                                                                                                                          | Notes                                                                                                                       |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Manifest / sharding (UTL ManifestWriter surface)** | manifest_schema_v6_quote_margin_combo_2026_04_23, manifest_429_per_vm_sharding_2026_04_25, mtds_multi_dimensional_shard_architecture_2026_04_12, mtds_canonical_sharding_alignment_2026_03_31, honest_coverage_metrics_2026_04_19, instrument_schema_cohesion_and_market_hours_2026_03_31                                                                                                                             | **manifest_schema_v6_quote_margin_combo** + **manifest_429_per_vm_sharding** (newer focused carve-outs)                                | mtds_multi_dimensional_shard is the parent umbrella those two carved out; should be marked `superseded_by` both newer plans |
| **DeFi data pipeline**                               | consolidated_defi_data_pipeline_2026_04_15, defi_data_types_completeness_2026_04_24, defi_full_coverage_expansion_2026_04_09, defi_instrument_pipeline_and_rewards_2026_04_01, mtds_defi_data_normalization_2026_04_14, mev_protection_and_execution_enhancements_2026_04_01                                                                                                                                          | **consolidated_defi_data_pipeline_2026_04_15** (designated consolidator) + **defi_data_types_completeness_2026_04_24** (newest active) | 4 source plans declare `remaining_todos_consolidated_into: consolidated_defi_data_pipeline`                                 |
| **ML pipeline**                                      | consolidated_ml_advanced_pipeline_2026_04_15, ml_pipeline_revolution_2026_04_11, domain_agnostic_ml_framework_2026_04_11, ml_pipeline_ui_integration_2026_04_16, live_frontend_integration_e2e_audit_2026_04_15                                                                                                                                                                                                       | **consolidated_ml_advanced_pipeline_2026_04_15**                                                                                       | 2 source plans declare consolidation marker                                                                                 |
| **Coverage / QG**                                    | coverage_ratchet_policy_2026_04_19, coverage_uplift_bottom5_2026_04_19, honest_coverage_metrics_2026_04_19, proper_coverage_roadmap_2026_04_20, full_qg_sweep_all_services_2026_03_28                                                                                                                                                                                                                                 | **proper_coverage_roadmap_2026_04_20** (most recent + most comprehensive)                                                              | full_qg_sweep is owner=human and pre-dates the wave                                                                         |
| **Sports prediction pipeline**                       | consolidated_sports_prediction_pipeline_2026_04_15, sports_batch_pipeline_end_to_end_2026_03_25, sports_integration_01-06 (6 plans), polymarket_prediction_pipeline_2026_03_25                                                                                                                                                                                                                                        | **consolidated_sports_prediction_pipeline_2026_04_15** + /codex/02-data/sports-scheduling-and-sharding.md §12.0 register               | 8 source plans declare consolidation marker; codex §12.0 has now superseded the consolidator's tracking role                |
| **Sports comprehensive umbrellas**                   | sports_data_completeness_2026_04_14, sports_data_pipeline_comprehensive_2026_04_16, sports_data_migration_mapping_plan_2026_03_26, sports_feature_completion_2026_04_10, sports_e2e_validation_2026_03_27                                                                                                                                                                                                             | **sports_roadmap_master_execution_2026_04_21** (live SSOT for §12.0)                                                                   | None of these are in §12.0 register; roadmap_master is the carrier                                                          |
| **DART UI**                                          | dart_ui_strategy_filtering_and_onboarding_2026_04_24, dart_exclusive_subscription_research_fork_2026_04_21, dashboard_services_grid_collapse_2026_04_21, consolidated_strategy_and_ui_2026_04_15                                                                                                                                                                                                                      | **dart_ui_strategy_filtering_and_onboarding** (live in_progress, biggest scope)                                                        | consolidated_strategy_and_ui is now superseded by these 3 child plans                                                       |
| **DeFi strategy testing trio**                       | defi-strategy-e2e-automation, defi-strategy-testing-quickstart, defi-strategy-ui-verification                                                                                                                                                                                                                                                                                                                         | **defi-strategy-ui-verification** (only one with checkboxes)                                                                           | Other 2 are workflow guides → relocate to codex/                                                                            |
| **Five-space IA worksheet pair**                     | five_space_ia_audit_matrix_2026_04_17, five_space_ia_execution_child_plan_2026_04_17                                                                                                                                                                                                                                                                                                                                  | **five_space_ia_execution_child_plan** (delivery plan)                                                                                 | audit_matrix is input worksheet → relocate                                                                                  |
| **Fund admin**                                       | fund_administration_service_and_pooled_subscription_redemption_2026_04_20, fund_administration_phase6_plus_followups_FINISHER_DISPATCH_PROMPT, fund_administration_signoff_walkthrough_2026_04_22, cra_entitlement_backfill_existing_reporting_routes_2026_04_22, tradfi_fund_administrator_selection_2026_04_22, pod_crypto_administrator_integration_2026_04_22, fund_administration_persistence_swap_in_2026_04_22 | **fund_administration_service_and_pooled_subscription_redemption_2026_04_20** (parent)                                                 | DISPATCH_PROMPT is meta; signoff_walkthrough is a runbook                                                                   |
| **Citadel remediation**                              | citadel_service_remediation_2026_03_24, citadel_per_service_remediation_2026_03_24, full_qg_sweep_all_services_2026_03_28                                                                                                                                                                                                                                                                                             | **citadel_service_remediation** (parent tracker)                                                                                       | per-service plan has 0/149 untouched while parent shows 19/30                                                               |
| **Marketing**                                        | marketing_homepage_old_hero_migration_2026_04_22, marketing_site_audit_manifest_2026_04_20, presentation_service_alignment_2026_04_13, path_to_100m_finalization_2026_04_20                                                                                                                                                                                                                                           | **marketing_homepage_old_hero_migration_2026_04_22** (live USP work) + **path_to_100m_finalization** (commercial framing)              | site_audit_manifest is consumed companion                                                                                   |

## Pass 4 — Orphan integration check (13 orphan candidates)

| Plan                                                                  | Orphan reason                                       | Better home?                                                |
| --------------------------------------------------------------------- | --------------------------------------------------- | ----------------------------------------------------------- |
| defi-strategy-e2e-automation.md                                       | 446-line workflow guide, no checkboxes/frontmatter  | codex/14-playbooks/ or codex/08-workflows/                  |
| defi-strategy-testing-quickstart.md                                   | 301-line quickstart guide, no checkboxes            | codex/08-workflows/                                         |
| five_space_ia_audit_matrix_2026_04_17.md                              | 64-line audit table input                           | codex/05-infrastructure/ or plans/audits/                   |
| portal_local_smoke_checklist_2026_04_19.md                            | Repeatable checklist with ☐/☑ glyphs                | codex/14-playbooks/ or scripts/                             |
| hybrid_sampler_5s_resolution_2026_03_30.md                            | Stalled since 2026-03-30; no commits matching scope | candidate archive                                           |
| ml_pipeline_ui_e2e_browser_validation_AGENT_PROMPT.md                 | Pure agent dispatch prompt                          | archive                                                     |
| ml_pipeline_ui_integration_2026_04_16_AGENT_PROMPT.md                 | Pure agent dispatch prompt                          | archive                                                     |
| fund_administration_phase6_plus_followups_FINISHER_DISPATCH_PROMPT.md | Pure agent dispatch prompt; work shipped via parent | archive                                                     |
| refactor_g3_3_briefings_cms_migration_2026_04_20.md                   | 0/12, gated on G1.12; no progress                   | keep open (verify still relevant given marketing site work) |
| refactor_g3_4_dart_rebrand_trademark_check_2026_04_20.md              | 0/14, no code work; legal/marketing                 | keep open (operator-gated)                                  |
| refactor_g3_5_codex_sync_consistency_agents_2026_04_20.md             | 0/11, agent-build work not started                  | keep open                                                   |
| sports_live_streaming_viz_2026_04_15.md                               | No checkboxes, no lock, no evidence                 | candidate archive or restructure                            |
| strategy_registry_v1_delete_consumer_audit.md                         | Manifest doc whose parent already in archive/       | move to archive/                                            |
| (also) marketing_site_audit_manifest_2026_04_20.md                    | Companion manifest, parent unlocked                 | move to archive/ alongside parent                           |

## "Needs human review" (unclear classifications)

| Plan                                                | Question to resolve                                                                                             |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| citadel_per_service_remediation_2026_03_24.md       | 0/149 untouched while parent shows 19/30 — retire as superseded by per-repo work, or audit each of 20 services? |
| sports_live_streaming_viz_2026_04_15.md             | Restructure with checkboxes + locked_by, or archive?                                                            |
| refactor_g3_3_briefings_cms_migration_2026_04_20.md | Still relevant given marketing site already iterates on briefings?                                              |

## Real state-of-G2-G3 table

| Plan                                  | Raw checkboxes | Evidence-based reality                                                           | Recommendation                                      |
| ------------------------------------- | -------------- | -------------------------------------------------------------------------------- | --------------------------------------------------- |
| g2.1 org_scoped_jwt_claims            | 0/17           | Codex shipped (a4b7ae26); JWT claims wiring pending; operator-gated G2.6         | live                                                |
| g2.2 per_client_api_key_issuance      | 0/17           | API key UI exists in (ops)/admin/; runtime issuance pending                      | live                                                |
| g2.3 data_catalogue                   | 0/14           | Catalogue artefacts shipped (8d43fae4, bba284f, 3d041d81); UI rendering deferred | partial — flip artefact phases                      |
| g2.4 ml_model_catalogue               | 0/16           | Phase 11 5-dim catalogue shipped (e11a4145); G1.5 absorbed (32ccd727)            | partial — flip absorbed scope; add supersedes       |
| g2.5 execution_algo_catalogue         | 0/19           | algo_library code substrate exists; refactor pending                             | live                                                |
| g2.6 staging_firebase_provisioning    | 0/17           | Naming-convention table (952dc4f3); env-mode (ad2a7dfb); operator-blocked        | partial — add supersedes                            |
| g2.7 demo_provisioning_automation     | 0/15           | Resend (1baea733, 9b048896) + restriction-profile (7a4b90f2) shipped             | partial — add supersedes=defi_demo_e2e              |
| g2.8 fund_business_unit_registry      | 6/8            | Phases A+B shipped (eef08911); Phase C → G2.10                                   | partial — add supersedes=share_class_architecture   |
| g2.9 uac_remaining_gaps               | 0/33           | V2 drop (3e4e11ee), 48bf6ee; per-gap progress unclear                            | partial                                             |
| g2.10 allocator_ui_split              | 0/17           | DART UI Phase 9-10 shipped (f70926cf, 2a9aa7c7)                                  | partial — add supersedes=platform_strategy_families |
| g2.11 account_intelligence_record_crm | 0/12           | Codex foundations (a4b7ae26); admin surface not built                            | live                                                |
| g3.1 pricing_engine_service           | 0/14           | 0bed08bc (plan added); no code                                                   | live                                                |
| g3.2 pricing_numbers_from_finance     | 5/7            | 89c8982c (flips A/B/C/D); checkbox state may be re-opened by concurrent agent    | partial — verify                                    |
| g3.3 briefings_cms_migration          | 0/12           | None                                                                             | orphan candidate                                    |
| g3.4 dart_rebrand_trademark_check     | 0/14           | Operator/marketing work, no code                                                 | orphan (operator-gated)                             |
| g3.5 codex_sync_consistency_agents    | 0/11           | Anchors don't match scope                                                        | orphan candidate                                    |

**Net G2 reality:** 6/185 raw checkboxes, but ~50-60 phases substantially shipped via sibling plans (DART UI,
signup-signin, Resend, env-mode, manifest v6, UAC fund/business-unit). G2 plans are mostly tracking under-acknowledged
shipped work.

**Net G3 reality:** 5/58 raw checkboxes, mostly operator-gated or pending finance/legal sign-off. Genuinely-pending
technical work concentrated in g3.1 (pricing-engine REST surface).
