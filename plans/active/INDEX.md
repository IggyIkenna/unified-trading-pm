# Active Plans Index

**Last Updated:** 2026-04-01

This is the canonical index of all active plans. Plans are organized by domain.

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

- defi_demo_e2e_workflow_2026_03_30.plan.md — End-to-end DeFi demo
- defi_ui_component_audit_2026_03_31.plan.md — UI component audit
- defi_phase3_infrastructure_2026_03_30.plan.md — Infrastructure completion
- defi_strategies_phase2_2026_03_29.plan.md — Phase 2 strategies

### Sports

- sports_live_streaming_viz_2026_04_15.plan.md — Sports live streaming, ML pipeline UI, promotion structure,
  frontend-backend parity
- features_sports_denormalisation_pipeline_2026_04_21.plan.md — **SHIPPED 2026-04-21** (UAC `ef1e89f` + FSS `c7a363d` +
  codex §9.1 `fa3e6c6a`). Per-fixture denormalisation pipeline: Transfermarkt team-value asof join + pre-match
  standings + kickoff-hour weather. `FixtureFeatures` Pydantic in UAC; `pipeline/fixture_features.py` + `_asof.py` +
  batch_handler wiring in FSS. 32 unit tests green. Locked-by `live-defi-rollout` pending human `[unlock-plan]`.
- features_sports_derived_data_crime_fixes_2026_04_21.plan.md — Follow-up to the denormalisation plan: remove two
  pre-existing data crimes in `features-sports-service` derived_features — (1) `squad_value_calculator.py`
  zero-default → NaN propagation, (2) `_compute_league_batch` lookahead (read standings from `day=kickoff_date - 1`
  not `day=kickoff_date`). Also resolves the `_normalize_standings` rank-column bug that surfaced in the parent
  plan's dry-run. Depends on the denormalisation plan (shipped).

### Data & Testing

- agent6_mock_data_quality_2026_03_22.plan.md — Mock data quality
- agent8_e2e_tests_quality_2026_03_22.plan.md — E2E testing
- sports_e2e_validation_2026_03_27.plan.md — Sports E2E validation
- mtds_per_instrument_sentinels_2026_04_21.plan.md — Phase 8 honest-coverage: per-instrument Tier-3 sentinels for MTDS
  `trades` / `book_snapshot_5` / `derivative_ticker` / `options_chain` / `futures_chain`. UAC accessor + MTDS
  orchestrator + deployment-api aggregator + codex matrix. MVP cap=50 rollout. 4 repos.

### Service Remediation

- citadel_per_service_remediation_2026_03_24.plan.md — Per-service fixes
- instruments_service_reorganisation_2026_03_27.plan.md — Instruments service

### Library Consolidation

- fold_uei_into_utl_2026_04_17.plan.md — Fold unified-trading-library into `unified_trading_library.events` (aggregate
  of both), migrate 30+ consumers, archive UEI repo

### Strategy Lifecycle & Catalogue (NEW 2026-04-21)

- strategy_lifecycle_maturity_model_2026_04_21.plan.md — UAC data model foundation. 9-phase `StrategyMaturityPhase`
  enum, `ProductRouting`, `ShareClass`, venue-set-variants registry (Elysium: base_3cex → premium_6cex → multi_evm →
  multi_evm_plus_sol), 5-dim `StrategyInstance`, `StrategyInstanceLifecycle` record, `odum-paper` + `odum-live`
  client-zero seed rows, UAC → UI propagation script extension, admin lifecycle-editor PATCH endpoint, UTL
  `LifecycleReloader`. Unblocks Plans B, C, D.
- strategy_catalogue_3tier_surface_2026_04_21.plan.md — `<StrategyCatalogueSurface>` shared primitive with 4 viewModes
  (admin-universe / admin-editor / client-reality / client-fomo). Rebuilds `/services/strategy-catalogue` as a 2-tab
  Reality + FOMO surface; adds admin universe + lifecycle-editor pages. Depends on Plan A.
- performance_overlay_continuous_timeline_2026_04_21.plan.md — `<PerformanceOverlay>` chart primitive rendering
  continuous backtest → paper → live timelines from odum-paper/live account series. 3 modes (overlay / stitched /
  split), per-venue slicing, allocator query support. Wired into FOMO tearsheets, DART terminal, Reports. Depends on
  Plan A.
- orphan_audit_policy_2026_04_21.plan.md — 3-phase (advisory → fix-all → blocking) scanner that diffs Next `app/` routes
  against all declared nav surfaces (lifecycle-nav, tile sub-routes, chip hrefs, breadcrumbs, transitive Link closure).
  Whitelist for intentional direct-URL-only pages. quickmerge + GHA gate in Phase 3.
- dart_exclusive_subscription_research_fork_2026_04_21.plan.md — Plan D: DART exclusive-subscription model
  (`StrategyInstanceSubscription` with `dart_exclusive`/`im_allocation`/`signals_in` types + exclusive-lock invariant),
  client-authored research fork lifecycle (`StrategyVersion` draft → pending_approval → approved → rolled_out), joint
  Odum-client version governance gated on `backtest_1yr` + admin approval, UTA subscribe/fork/approve/rollout endpoints,
  strategy-service `version_governance` module with canonical backtest-pipeline re-use, DART UI Subscribe/Fork/Admin
  Approvals surfaces. 6 phases across UAC + UTL + UTA + strategy-service + UI + PM. Depends on Plans A + B + C.

### UI & Admin Unification

- dashboard_services_grid_collapse_2026_04_21.plan.md — Collapse `/dashboard` tile grid 11 → 5 (DART · Odum Signals ·
  Reports · Investor Relations · Admin & Ops), per-persona sub-route chips under each tile, and family/archetype filter
  strip above grid. Sibling to Phase-11 nav 8→4 collapse. Depends on `ui_unification_v2_sanitisation_2026_04_20`.
- ui_unification_v2_sanitisation_2026_04_20.plan.md — Kill v1 StrategyFamily + old backtest, fold user-management-ui
  into `unified-trading-system-ui/(ops)/admin/*`, wire questionnaire → persona → filter cascade, deorphan 22 unreachable
  pages, add FamilyArchetypePicker platform-wide, canonicalise strategy naming (`FAMILY.ARCHETYPE.slot_id`), collapse
  8-stage lifecycle to 4 (Data / DART / Manage / Reports), ship CatalogueTruthinessAdapter + admin catalogue overview +
  per-user visibility editor. All implementation phases (1-8, 10, 11) green as of 2026-04-21; Phase 9 (workspace QG
  sweep + INDEX + unlock request) is the final gate. Spans 6 repos: UAC, UTL, strategy-service,
  unified-trading-system-ui, unified-trading-pm, user-management-ui (archived). **Wave 6 (2026-04-21)** closed the 6 v1
  equivalency gaps via architectural clarification (value-betting = EdgeMethod axis not archetype; treasury ETFs = spot
  not new "bond" instrument-type; Elysium rows = RETIRED not GAP). UAC `b7c15d2` + PM `533a732f` + UI `27c1d71`. v1
  strategy-registry.ts deletion + consumer migration tracked separately under
  `strategy_registry_v1_delete_and_consumer_migration_2026_04_21.plan.md` (below).
- strategy_registry_v1_delete_and_consumer_migration_2026_04_21.plan.md — Delete 7780-LOC
  `unified-trading-system-ui/lib/strategy-registry.ts` + `legacyFamilyToV2()` helper. Migrate 18 consumer files to
  v2-sourced data (coverage.ts + regenerated mock fixture from UAC STRATEGY_REGISTRY). Purge 3 Elysium rows from
  mock-data-seed.ts + positions-data-context.tsx + ui-reference-data.json. 7 phases, single-repo scope
  (unified-trading-system-ui). Depends on ui_unification_v2_sanitisation Wave 6 (gap closure done). **ALL 7 PHASES
  LANDED 2026-04-21 (Wave 7)** — new fixture `lib/mocks/fixtures/strategy-instances.ts` generated by
  `unified-trading-pm/scripts/propagation/generate-strategy-instances-fixture.py` from UAC STRATEGY_REGISTRY (99
  entries). 18/18 consumers migrated. v1 artefacts deleted. 969/969 vitest pass (baseline 984, -15 from deleted
  strategy-registry.test.ts). Awaiting `[unlock-plan]` human approval to archive.

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
