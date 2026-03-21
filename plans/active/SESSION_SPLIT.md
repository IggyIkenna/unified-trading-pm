# Session Split — 4 Parallel Backend Sessions

**Created:** 2026-03-21 **Context:** All plans merged, archives done. 4 independent backend sessions can run
simultaneously. **UI Plans (E+F):** Deferred — start after all 4 sessions complete.

---

## Session 1: Registry + API Foundation

**Plans:** A (phases 1-3), H (all phases) **Estimated todos:** ~60 **Repos touched:** unified-api-contracts,
unified-internal-contracts, unified-trading-api (new), unified-trading-pm

**What to do:**

1. Plan A Phase 1: Enhance `generate_ui_reference_data.py` — add 9 missing registries (error classifications,
   instruction constraints, DeFi protocol registry, venue rate limits, risk taxonomy, market data categories, chain RPC
   templates, subgraph IDs, capabilities). Add tests.
2. Plan A Phase 2: Fix OpenAPI spec — add execution-results-api (50 endpoints), fix 66 empty schemas. Restore
   `openapi-typescript` codegen.
3. Plan A Phase 3: CI triggers — UAC/UIC commit → regenerate spec + types → PR on UI repo.
4. Plan H Phase 0: Scaffold `unified-trading-api` repo — FastAPI, pyproject.toml, quality-gates.sh, health endpoint,
   entitlement middleware, MockStateStore.
5. Plan H Phase 1: Migrate 16 domain route modules (PARALLEL) from 9 existing API repos.
6. Plan H Phase 2: WebSocket endpoint — channel multiplexing (market-data, positions, alerts, health, execution).
7. Plan H Phase 3-6: Seed data, OpenAPI generation, deprecate old repos, QG sweep.

**Key rule:** Plan H unified-trading-api should be a NEW repo. Route modules absorb logic from existing API repos.
WebSocket endpoint uses SyntheticDataGenerator in mock mode.

**Start command:** Read plans/active/plan_a_registry_schema_sync_2026_03_21.plan.md and
plans/active/plan_h_api_consolidation_2026_03_21.plan.md

---

## Session 2: Config + Service Hardening

**Plans:** B (all phases), C (all phases), close out 4 nearly-done plans **Estimated todos:** ~55 **Repos touched:**
unified-config-interface, unified-trading-library, all 21 services, 9 API repos

**What to do:**

1. Plan B Phase 0: Add 5 missing domain config schemas to UCfgI (RiskDomainConfig, AlertRuleDomainConfig,
   RateLimitDomainConfig, FeatureFlagDomainConfig, StrategyDomainConfig).
2. Plan B Phase 1: Wire callback bodies in 20 log-only services (5 parallel groups):
   - Group A: market-tick-data, market-data-processing
   - Group B: 8 feature services (all PARALLEL)
   - Group C: strategy, execution, trading-agent
   - Group D: risk, position-balance, pnl-attribution, alerting, recon
   - Group E: ml-training, ml-inference
3. Plan B Phase 2: Config publish API endpoint + CLI.
4. Plan B Phase 3: Config placement remediation (12 violations, 8 in market-tick-data-service).
5. Plan C: Audit all API repos for mock mode completeness, fix gaps, standardize response schemas.
6. Close out: full_system_audit_resolution (4 items), live_batch_alignment (2 items), mock_data_rollout (5 items),
   production_mock_e2e (2 items).

**Key rule:** Fixing callbacks fixes BOTH live AND batch config replay (replay_at()). Test both modes.

**Start command:** Read plans/active/plan_b_config_hot_reload_2026_03_21.plan.md and
plans/active/plan_c_domain_data_api_2026_03_21.plan.md

---

## Session 3: Auth + Client Reporting + Instruments

**Plans:** G (phases 1-3), I (all phases), instrument_data_source_separation, instruments_service_batch_validation,
instruments_service_completion **Estimated todos:** ~80 **Repos touched:** unified-config-interface,
unified-cloud-interface, client-reporting-api, 9 API repos, execution-service, alerting-service, instruments-service,
unified-api-contracts

**What to do:**

1. Plan G Phase 1: Enroll remaining 19 services in S2S static token auth.
2. Plan G Phase 2: Standardize auth middleware across all 9 API repos, add org-level filtering.
3. Plan G Phase 3: Backend entitlement enforcement — server-side checking, instrument count limits.
4. Plan I Phase 0: Document management infrastructure — schemas, pre-signed URLs, bucket registry.
5. Plan I Phase 1-2: Client reporting enhancement, invoicing endpoints + templates.
6. Plan I Phase 3-4: MiFID compliance, DocuSign integration.
7. Plan I Phase 5-6: Document API routes, mock data + QG.
8. instrument_data_source_separation: Split TRADFI_VENUE_MAPPINGS, generalize data_source_continuity.
9. instruments_service_batch_validation: Remaining B2, C, B4, A, D, E items.
10. instruments_service_completion: Phases 3-6 (sports data wiring, live mode, QG).

**Key rule:** Auth (Plan G) must be done before entitlement-gated endpoints in Plan I.

**Start command:** Read plans/active/plan_g_auth_entitlement_2026_03_21.plan.md and
plans/active/plan_i_client_reporting_docs_2026_03_21.plan.md

---

## Session 4: Testing + ML/Strategy

**Plans:** D (all phases), fixed_grid_config_refactor, uniform_ml_pipeline remaining, sports plans remaining **Estimated
todos:** ~70 **Repos touched:** unified-api-contracts, unified-trading-library, unified-internal-contracts,
system-integration-tests, execution-service, deployment-service, ml-training-service, strategy-service,
features-sports-service

**What to do:**

1. Plan D Phase 0: Seed hardening — audit all 15 seed scripts for determinism.
2. Plan D Phase 1: Scenario infrastructure — add BAD_SCHEMA, ERROR_STORM, FLASH_CRASH, HIGH_LATENCY scenarios. API for
   scenario switching.
3. Plan D Phase 2: Error code stress tests — exercise all 18+13 error codes. ERROR_STORM scenario.
4. Plan D Phase 3: PerformanceGate + MemoryGate CI integration for critical services.
5. Plan D Phase 4: Synthetic load generator (45→10K instruments), response time baselines.
6. Plan D Phase 5: Deployment service mock scenarios (VM lifecycle, shard failures, quota exhaustion).
7. Plan D Phase 6: Final validation — QG sweep, mock-live parity test.
8. fixed_grid_config_refactor: Fixed vs Grid two-tier config across ML/strategy/execution.
9. uniform_ml_pipeline: Remaining items from ML pipeline plan.
10. sports plans: sports_hub_residual_actions, sports_schema_allocation remaining Phase 8.

**Key rule:** Testing validates what the other 3 sessions build. Can start immediately on seed hardening and scenario
infrastructure.

**Start command:** Read plans/active/plan_d_testnet_stress_testing_2026_03_21.plan.md and
plans/active/fixed_grid_config_refactor_2026_03_21.plan.md
