# Active Plans Index

**Last Updated:** 2026-04-29 (instrument catalogue + availability matrix plan added)

This is the canonical index of all active plans. Plans are organized by domain.

---

## Cross-cutting SSOT (priority — data plane + agents)

**Read first** when touching venue routing, buckets, or market-data category maps:

- [instrument_catalogue_availability_matrix_2026_04_29.plan.md](instrument_catalogue_availability_matrix_2026_04_29.plan.md)
  — Joins **static shard-dynamics SSOT** (bucket → partition layout → schema → coverage-start → retention/cutoff →
  live/batch capability per `(asset_group × data_type × venue × instrument_type)`) with **live availability-manifest
  aggregation** (capture_status → coverage %). Publishes `instrument-catalogue.{json,md}` + `shard-dynamics.json`
  nightly to `gs://strategy-store-cefi-{pid}/catalogue/instrument/`. New UI matrix widget cross-links existing
  data-status drilldown. Pulls bucket-naming + partition-layout + coverage-start + capability registries into UAC
  (sports already SSOT, others scattered). Depends on shard-dimension naming + venue-axis vocabulary plans.

- [deployment_ui_lifecycle_tabs_2026_05_08.plan.md](deployment_ui_lifecycle_tabs_2026_05_08.plan.md) — **Cross-cutting
  6-tab restructure** of deployment-UI organised around four orthogonal axes: lifecycle class (EPHEMERAL_BATCH /
  EPHEMERAL_EXPERIMENT / SCHEDULED_RECURRING / LONG_LIVED_LIVE), cloud target (GCP / AWS), environment tier (DEV /
  STAGING / PROD — resolved by domain, never an in-UI toggle), service / asset_group. Tabs: Deploy (fresh deployments
  only) / Monitor (renamed from History; sub-tabs Backfill / Experiments / Live / Scheduled — runtime state of every
  job, cluster, scheduler with re-deploy / stop / start / pause / drain / stream-logs / attach-events actions on each
  row using the SAME row-template) / Data Status (scoped to data + pricing only — instruments / MTDS / MDPS /
  features-\*; with Batch / Scheduled-Today / Live mode toggle) / Builds / Readiness / Config. Header carries
  cloud-toggle (slow refresh) + env badge (read-only). Cross-Monitor-sub-tab navigation is INSTANT (prefetch context);
  cloud-toggle pays network round-trip; env switch happens by changing domain. Auth always-available (UnifiedCloudConfig
  loads both clouds at api-boot). NEW UAC SSOTs: `LifecycleClass` enum (4 members), `EnvironmentTier` enum +
  domain-resolver, scheduler registry (env-scoped), live-cluster registry (env-scoped), experiment registry. NEW UTL
  helper `experiment_tracker.py` (run_id / metric / step / artifact emission for ML / strategy / execution research
  jobs). NEW codex docs: `deployment-ui-architecture.md` (UX SSOT) + `deployment-ui-environment-tiers.md`
  (dev/staging/prod hosting, mirrors trading-system-UI pattern + firebase-split-topology). NEW deployment-api routes:
  `/api/monitor/{backfill,experiments,live,scheduled}`, `/api/logs/stream/{target_ref}`. Most infrastructure already
  exists (SSE event-stream, CloudProviderContext, deploy-missing, data-status drilldown, vm-launcher registry); plan is
  mostly re-shape + wire-in with one greenfield slice (Experiments tracker) and one infra slice (env-tier hosting of
  deployment-UI/API itself). Sibling-of `instruments_live_master_2026_05_08`; Phase G of that plan delegates UI scope
  here.

- [instruments_live_master_2026_05_08.plan.md](instruments_live_master_2026_05_08.plan.md) — **Activation surface for
  instruments-live across all 5 asset_groups** (cefi 15-min CCXT replacing Tardis-T+1; tradfi 15-min Polygon/Yahoo
  replacing Databento for live; sports trigger-driven — daily fixture re-poll + per-league season-roll → teams /
  mappings + annual transfer-window → players + weather cascade pre-kickoff; predictions 15-min market-discovery). Live
  writes to SAME GCS path as batch (no separate live path); T+1 is retrospective audit / comparison job, NOT a backfill.
  Cloud Scheduler activation per-trigger + new deployment-UI "Scheduled Jobs" tab listing every cron invocation with
  last-run / next-fire / recent events / Telegram-alert-on-fail. Critical Phase A.9–A.11 codifies the preflight DAG
  (downstream-needs-upstream-first) as a UAC SSOT + UTL helper invoked identically by live and batch — typed
  `INSTRUMENTS_LIVE_PREFLIGHT_FAILED` + `INSTRUMENTS_LIVE_UPSTREAM_STALE` events route to Telegram with the specific
  missing-upstream named in the message. References (does NOT duplicate) the existing codex SSOTs
  (`batch-live-symmetry`, `backfill-and-live-startup`, `live-deployment-monitoring`, `alerting-batch-live`,
  `sports-live-odds-connectivity`, `runtime-tiers-and-deployment`) and 8 active issues for data-correctness deltas.
  Sibling-of (NOT child-of) `master_to_live_defi_2026_05_23` — only Phase D (cefi 15-min CCXT) + Phase F.3 (AWS
  EventBridge mirror) are on the May-23 critical path; the rest is post-cutover.

---

## DeFi Strategy Testing & Automation (NEW)

**⭐ START HERE:** [defi-strategy-testing-quickstart.md](defi-strategy-testing-quickstart.md) — Quick reference +
examples for testing any DeFi strategy

**Detailed Plans:**

- [defi-strategy-ui-verification.plan.md](defi-strategy-ui-verification.plan.md) — Phase 1: Verify UI widgets with
  mocked data
- [defi-strategy-e2e-automation.plan.md](defi-strategy-e2e-automation.plan.md) — Full pipeline: UI verification → test
  generation → execution → regression protection

---

## Currently Active Plans

### Infrastructure & Setup

- agent1_shell_navigation_2026_03_22.plan.md — Shell navigation framework
- agent2_trading_service_2026_03_22.plan.md — Trading service setup
- agent5_api_service_layer_2026_03_22.plan.md — API service layer

### DeFi Strategy Rollout

- defi_ui_component_audit_2026_03_31.plan.md — UI component audit
- defi_phase3_infrastructure_2026_03_30.plan.md — Infrastructure completion
- defi_strategies_phase2_2026_03_29.plan.md — Phase 2 strategies

### Sports

- sports_predictions_e2e_2026_05_05.plan.md — Drives sports predictions running end-to-end: feature-service-sports →
  ml-training (Model 2A walk-forward) → strategy-service paper trade (ArbitrageStrategy + MLSportsStrategy) →
  execution-service paper fills + matching-engine for execution alpha → upcoming-fixtures-ui shows predictions. Path:
  re-key existing 288M Odds-API rows (`migrate_sports_canonical.py`, idempotent, no API) + MDPS 8-bucket horizon adapter
  (`SportsBucketAssignmentAdapter`, no API) → FSS feature compute → ML → strategy → UI. Folds
  `sports_e2e_validation_2026_03_27` Phases 2/3/5; Phase 4 re-collection budget dropped (predictions don't need it).
  Depends on master roadmap Phase 6, UTL base-image rebuild, and features_sports_honest_coverage_2026_05_05.
- run_lifecycle_events_ssot_2026_05_05.plan.md — Cross-cutting observability fix per the 2026-05-05 CLAUDE.md "No
  fire-and-forget VM launches" rule. 4 phases: (1) UTL helper `run_lifecycle(service_name, details=...)` context
  manager + unit tests in `unified_trading_library.events`; (2) audit every long-running entry-point in the workspace;
  (3) rollout to MTDS migrates / MDPS / instruments-service / deployment-service / FSS / strategy / execution; (4)
  base-service.sh STEP 5.63 QG enforcement. Closes the gap where 11 audited scripts emit `setup_events` but no
  RUN_STARTED + terminal RUN_COMPLETED|FAILED. Reference incident: migrate_sports_canonical patched ad-hoc in MTDS
  ce9b069; this plan rolls the helper into UTL so every script gets the same shape.
- instruments_service_write_gate_validation_2026_04_22.plan.md — Close the architectural gap where raw-data sinks in
  instruments-service bypass UTL's point-in-time validators entirely. Every `sink.write(...)` gates through
  `InstrumentsWriteGate.validate_and_write(df, partition, batch_date, mode='strict'|'warn')` asserting
  `value.date() <= batch_date` for every as-of column candidate. Warn-mode rollout measures violation volume; flip to
  strict once adapters clean. Motivated by the 2026-04-22 TM-VM incident (bugs fixed in instruments-service `cdded95`)
  which existed undetected on HEAD because zero UTL validators fire at raw-data write time. 3 repos (UTL +
  instruments-service + PM).

### Data & Testing

- [instruments_to_100pct_eod_2026_05_04.plan.md](instruments_to_100pct_eod_2026_05_04.plan.md) — instruments-service to
  ≥99% honest coverage across all 5 asset groups (sibling to MTDS plan; epic: data-pipeline-completion).
- [market_tick_data_to_100pct_2026_05_05.plan.md](market_tick_data_to_100pct_2026_05_05.plan.md) —
  market-tick-data-service raw download to ≥99% honest coverage across all 5 asset groups. **GCS-truth-first**: Phase
  0.1 inverse-phantom audit (parquet-on-disk-no-manifest-row) is a mandatory gate before any backfill VM launches —
  prevents wasted Tardis/Databento/DeFi-RPC/odds-API spend on data we already have. Per-AG decision: manifest rebuild
  (cheap) vs backfill (paid). Phase 2 launchers: `launch-cefi-sharded-backfill.sh`, `launch-tradfi-backfill-vm.sh`,
  `launch-mtds-prediction-backfill-vm.sh`, MTDS DeFi data-type launchers. Depends on instruments plan above.
- agent6_mock_data_quality_2026_03_22.plan.md — Mock data quality
- agent8_e2e_tests_quality_2026_03_22.plan.md — E2E testing
- ui_full_site_link_crawler_e2e_2026_04_22.plan.md — Full-site Playwright link crawler in `unified-trading-system-ui`
  (bounded BFS, shadow-DOM link harvest, nav flyouts, tier0 registry fill, optional external HEAD/GET probes); harden
  `webServer` for Tier 0 (`PLAYWRIGHT_SKIP_API_WEBSERVER`, `/login` readiness); document wall-clock presets + optional
  CI/nightly.

### Service Remediation

- citadel_per_service_remediation_2026_03_24.plan.md — Per-service fixes
- instruments_service_reorganisation_2026_03_27.plan.md — Instruments service

### Library Consolidation

- fold_uei_into_utl_2026_04_17.plan.md — Fold unified-trading-library into `unified_trading_library.events` (aggregate
  of both), migrate 30+ consumers, archive UEI repo

### Strategy Lifecycle & Catalogue (NEW 2026-04-21)

- performance_overlay_pbms_pnl_series_2026_04_22.plan.md — Ship PBMS `GET /api/v1/accounts/{account_id}/pnl-series` +
  UTA `HttpPbmPerformanceClient` so `<PerformanceOverlay>` uses real odum-paper / odum-live P&L streams (synth fallback
  unchanged). Depends on archived performance overlay primitive plan.
- dart_exclusive_subscription_research_fork_2026_04_21.plan.md — Plan D: DART exclusive-subscription model
  (`StrategyInstanceSubscription` with `dart_exclusive`/`im_allocation`/`signals_in` types + exclusive-lock invariant),
  client-authored research fork lifecycle (`StrategyVersion` draft → pending_approval → approved → rolled_out), joint
  Odum-client version governance gated on `backtest_1yr` + admin approval, UTA subscribe/fork/approve/rollout endpoints,
  strategy-service `version_governance` module with canonical backtest-pipeline re-use, DART UI Subscribe/Fork/Admin
  Approvals surfaces. 6 phases across UAC + UTL + UTA + strategy-service + UI + PM. Depends on Plans A + B + C.

### UI & Admin Unification

- dashboard_services_grid_collapse_2026_04_21.plan.md — Collapse `/dashboard` tile grid 11 → 5 (DART · Odum Signals ·
  Reports · Investor Relations · Admin & Ops), per-persona sub-route chips under each tile, and family/archetype filter
  strip above grid. Sibling to Phase-11 nav 8→4 collapse. Depends on archived
  [`ui_unification_v2_sanitisation_2026_04_20.plan.md`](../archive/ui_unification_v2_sanitisation_2026_04_20.plan.md).

### Deployment Topology & Client Isolation

- deployment_topology_and_client_isolation_2026_04_17.plan.md — Per-service isolation policy (shared vs isolated), SLA
  tiers (basic/standard/premium) with cost passthrough, runtime profiles (backtest/paper/mock-live/staging/prod)
  collapsing 5 mode env vars, chaos + kill-switch primitives. runtime-topology.yaml v6→v7, UAC schemas, UTL readers,
  deployment-service/api/ui materialisation, downstream service wiring. 13 repos. **Progress as of 2026-04-17
  live-defi-rollout:** Phases 1 (SSOT), 2a/2b (deployment-service/api), 3a/3b/3c (UTL ChaosController + KillSwitchBus +
  ServiceBootstrap wiring + strategy/exec/risk subscribers), 4a (deployment-api runtime_profile env var fanout), 5 (18
  archetype topology_requirements frontmatter + strategy-service enforcement module), 6 (PBM/R&E/PnL/execution isolation
  policy modules), 7 (8 e2e chaos scenarios), 4b (deployment-ui /client-subscriptions, /chaos pages, runtime_profile
  dropdown on DeployForm + 6 vitest cases) all committed locally. Phase 8 workspace QG sweep pending.

---

## How to Use This Index

1. **To find a plan:** Search this file for keywords or domain
2. **To run a plan:** Click the link and follow the plan's execution steps
3. **To create a new plan:** Add it to this INDEX with a one-line description, then update
   `[plan-placement.mdc](../../.cursor/rules/core/plan-placement.md)`

---

## Archive

For completed or superseded plans, see `archive/` directory.

### Bulk archive (2026-04-22)

The following 52 plans were moved from `active/` to [`archive/`](../archive/) with all Markdown checkboxes closed
(including residual items recorded as archive notes). Use the archive copy as the historical SSOT.

- [`autonomous_recovery_and_transfer_architecture_2026_04_16.plan.md`](../archive/autonomous_recovery_and_transfer_architecture_2026_04_16.plan.md)
- [`client_lifecycle_platform_2026_04_05.plan.md`](../archive/client_lifecycle_platform_2026_04_05.plan.md)
- [`defi_data_pipeline_e2e_2026_04_08.plan.md`](../archive/defi_data_pipeline_e2e_2026_04_08.plan.md)
- [`defi_demo_e2e_workflow_2026_03_30.plan.md`](../archive/defi_demo_e2e_workflow_2026_03_30.plan.md)
- [`defi_full_data_coverage_2026_04_09.plan.md`](../archive/defi_full_data_coverage_2026_04_09.plan.md)
- [`defi_pipeline_dedup_2026_04_11.plan.md`](../archive/defi_pipeline_dedup_2026_04_11.plan.md)
- [`features_sports_denormalisation_pipeline_2026_04_21.plan.md`](../archive/features_sports_denormalisation_pipeline_2026_04_21.plan.md)
- [`features_sports_derived_data_crime_fixes_2026_04_21.plan.md`](../archive/features_sports_derived_data_crime_fixes_2026_04_21.plan.md)
- [`granularity_per_category_config_2026_04_06.plan.md`](../archive/granularity_per_category_config_2026_04_06.plan.md)
- [`identity_registry_and_shard_enrichment_2026_04_16.plan.md`](../archive/identity_registry_and_shard_enrichment_2026_04_16.plan.md)
- [`institutional_feature_engineering_2026_04_11.plan.md`](../archive/institutional_feature_engineering_2026_04_11.plan.md)
- [`instruments_service_rolling_window_cli_flags_2026_04_21.plan.md`](../archive/instruments_service_rolling_window_cli_flags_2026_04_21.plan.md)
- [`marketing_site_restructure_2026_04_20.plan.md`](../archive/marketing_site_restructure_2026_04_20.plan.md)
- [`ml_pipeline_complete_2026_04_11.plan.md`](../archive/ml_pipeline_complete_2026_04_11.plan.md)
- [`mtds_per_instrument_sentinels_2026_04_21.plan.md`](../archive/mtds_per_instrument_sentinels_2026_04_21.plan.md)
- [`multichain_defi_expansion_2026_03_28.plan.md`](../archive/multichain_defi_expansion_2026_03_28.plan.md)
- [`orphan_audit_policy_2026_04_21.plan.md`](../archive/orphan_audit_policy_2026_04_21.plan.md)
- [`performance_overlay_continuous_timeline_2026_04_21.plan.md`](../archive/performance_overlay_continuous_timeline_2026_04_21.plan.md)
- [`permission_catalogue_2026_03_23.plan.md`](../archive/permission_catalogue_2026_03_23.plan.md)
- [`position_reconciliation_and_cost_preview_2026_04_16.plan.md`](../archive/position_reconciliation_and_cost_preview_2026_04_16.plan.md)
- [`recovery_and_transfer_completion_2026_04_16.plan.md`](../archive/recovery_and_transfer_completion_2026_04_16.plan.md)
- [`refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.plan.md`](../archive/refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.plan.md)
- [`refactor_g1_11_service_family_scope_rules_2026_04_20.plan.md`](../archive/refactor_g1_11_service_family_scope_rules_2026_04_20.plan.md)
- [`refactor_g1_12_public_site_ia_and_briefings_polish_2026_04_20.plan.md`](../archive/refactor_g1_12_public_site_ia_and_briefings_polish_2026_04_20.plan.md)
- [`refactor_g1_13_demo_upsell_overlay_tempt_logic_2026_04_20.plan.md`](../archive/refactor_g1_13_demo_upsell_overlay_tempt_logic_2026_04_20.plan.md)
- [`refactor_g1_14_presentation_deck_refresh_2026_04_20.plan.md`](../archive/refactor_g1_14_presentation_deck_refresh_2026_04_20.plan.md)
- [`refactor_g1_1_phase_unification_2026_04_20.plan.md`](../archive/refactor_g1_1_phase_unification_2026_04_20.plan.md)
- [`refactor_g1_2_instruction_schema_validation_service_2026_04_20.plan.md`](../archive/refactor_g1_2_instruction_schema_validation_service_2026_04_20.plan.md)
- [`refactor_g1_3_locked_visible_ui_service_tile_mode_2026_04_20.plan.md`](../archive/refactor_g1_3_locked_visible_ui_service_tile_mode_2026_04_20.plan.md)
- [`refactor_g1_4_persona_combinatorial_expansion_2026_04_20.plan.md`](../archive/refactor_g1_4_persona_combinatorial_expansion_2026_04_20.plan.md)
- [`refactor_g1_5_ml_catalogue_broken_hrefs_cleanup_2026_04_20.plan.md`](../archive/refactor_g1_5_ml_catalogue_broken_hrefs_cleanup_2026_04_20.plan.md)
- [`refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md`](../archive/refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md)
- [`refactor_g1_7_restriction_profile_engine_2026_04_20.plan.md`](../archive/refactor_g1_7_restriction_profile_engine_2026_04_20.plan.md)
- [`refactor_g1_8_uac_archetype_capability_v2_2026_04_20.plan.md`](../archive/refactor_g1_8_uac_archetype_capability_v2_2026_04_20.plan.md)
- [`refactor_g1_9_codex_scope_registry_2026_04_20.plan.md`](../archive/refactor_g1_9_codex_scope_registry_2026_04_20.plan.md)
- [`refactor_g3_6_visibility_slicing_e2e_expansion_2026_04_20.plan.md`](../archive/refactor_g3_6_visibility_slicing_e2e_expansion_2026_04_20.plan.md)
- [`reg_umbrella_questionnaire_and_onboarding_docs_2026_04_21.plan.md`](../archive/reg_umbrella_questionnaire_and_onboarding_docs_2026_04_21.plan.md)
- [`share_class_architecture_2026_04_01.plan.md`](../archive/share_class_architecture_2026_04_01.plan.md)
- [`sports_data_status_fixture_level_drilldown_2026_04_21.plan.md`](../archive/sports_data_status_fixture_level_drilldown_2026_04_21.plan.md)
- [`sports_scheduler_periodic_tier_dispatch_2026_04_21.plan.md`](../archive/sports_scheduler_periodic_tier_dispatch_2026_04_21.plan.md)
- [`strategy_architecture_v2_2026_04_17.plan.md`](../archive/strategy_architecture_v2_2026_04_17.plan.md)
- [`strategy_catalogue_3tier_surface_2026_04_21.plan.md`](../archive/strategy_catalogue_3tier_surface_2026_04_21.plan.md)
- [`strategy_docs_vs_system_audit_2026_04_15.plan.md`](../archive/strategy_docs_vs_system_audit_2026_04_15.plan.md)
- [`strategy_lifecycle_maturity_model_2026_04_21.plan.md`](../archive/strategy_lifecycle_maturity_model_2026_04_21.plan.md)
- [`strategy_registry_v1_delete_and_consumer_migration_2026_04_21.plan.md`](../archive/strategy_registry_v1_delete_and_consumer_migration_2026_04_21.plan.md)
- [`structured_error_handling_2026_03_22.plan.md`](../archive/structured_error_handling_2026_03_22.plan.md)
- [`ui_sync_hardening_2026_03_23.plan.md`](../archive/ui_sync_hardening_2026_03_23.plan.md)
- [`ui_unification_v2_sanitisation_2026_04_20.plan.md`](../archive/ui_unification_v2_sanitisation_2026_04_20.plan.md)
- [`umi_mtds_merger_2026_04_11.plan.md`](../archive/umi_mtds_merger_2026_04_11.plan.md)
- [`upcoming_fixtures_ui_view_2026_04_21.plan.md`](../archive/upcoming_fixtures_ui_view_2026_04_21.plan.md)
- [`utl_manifest_migration_primitives_2026_04_21.plan.md`](../archive/utl_manifest_migration_primitives_2026_04_21.plan.md)
- [`vm_observability_codex_update_2026_04_21.plan.md`](../archive/vm_observability_codex_update_2026_04_21.plan.md)
