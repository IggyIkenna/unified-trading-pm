---
doc_type: plan
title: defi-rollout-backend-2026-03-21
summary: 'Consolidated backend remediation plan aggregating all open items from 25 active plans (2026-03-21 audit).

  Excludes frontend-only, presentation, and website plans. Excludes prod-only items (marked BLOCKED).

  Covers: library foundation (UTL ServiceRuntime, UCI schemas, UAC registries), service migrations (13 services

  to ServiceRuntime, 21 services hot-reload, 22 repos mock mode migration), ML pipeline (uniform training,

  sports migration, grid config refactor), API hardening (mock mode, health endpoints, consolidation),

  auth/entitlement, cross-cutting infra, and testing/validation sweeps.

  Organized by dependency tier: T0 libraries -> T1 interfaces -> T2 services -> T3 cross-cutting -> T4 testing.

  ~355 actionable items for dev/staging; ~15 blocked (prod/human-only).'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, instruments-service, market-tick-data-service, strategy-service, unified-api-contracts, unified-trading-api]
scope: [engineer, admin]
tags: []
related: []
created:
type: mixed
epic: epic-code-completion
locked_by:
locked_since:
completion_gates: {code: C5, deployment: D2, business: none}
repo_gates:
- {repo: unified-trading-library, code: C0, deployment: none, business: none, readiness_note: 'ServiceRuntime, startup_validation, config source resolution, FreshnessMonitor'}
- {repo: unified-internal-contracts, code: C0, deployment: none, business: none, readiness_note: 'TrainingPhase, TargetType, ModelType, EnsembleConfig, TargetTypeParams, FixedConfig, document schemas'}
- {repo: unified-config-interface, code: C0, deployment: none, business: none, readiness_note: '5 domain config schemas, entitlement registry, MLTrainingConfig refactor, SportsMLConfig, slice subscriptions'}
- {repo: unified-cloud-interface, code: C0, deployment: none, business: none, readiness_note: 'GCSDataSink, S3DataSink, get_data_sink(), RUNTIME_MODE unification, ServiceCLI updates'}
- {repo: unified-api-contracts, code: C0, deployment: none, business: none, readiness_note: 'aave_plasma fix, 18 venue error maps, PredictionMarketMapping, data source separation, registry extractor'}
- {repo: unified-ml-interface, code: C0, deployment: none, business: none, readiness_note: 'config_schema updates, ModelVariantConfig refactor, sports metrics'}
- {repo: unified-sports-reference-interface, code: C0, deployment: none, business: none, readiness_note: competition_phase.py}
- {repo: unified-feature-orchestration-library, code: C0, deployment: none, business: none, readiness_note: anti_leakage.py}
- {repo: matching-engine-library, code: C0, deployment: none, business: none, readiness_note: SportsMatchingEngine}
- {repo: unified-reference-data-interface, code: C0, deployment: none, business: none, readiness_note: KalshiReferenceDataAdapter}
- {repo: instruments-service, code: C0, deployment: none, business: none, readiness_note: 'ServiceRuntime, UAC imports, config generation, live mode, data source separation, PredictionMarketResolver'}
- {repo: market-tick-data-service, code: C0, deployment: none, business: none, readiness_note: 'ServiceRuntime, hot-reload, config placement fixes'}
- {repo: market-data-processing-service, code: C0, deployment: none, business: none, readiness_note: 'ServiceRuntime, UAC imports, hot-reload'}
- {repo: features-sports-service, code: C0, deployment: none, business: none, readiness_note: 'Calculator parity, USRI/UFI wiring, anti_leakage, live mode, hot-reload'}
- {repo: features-onchain-service, code: C0, deployment: none, business: none, readiness_note: 'ServiceRuntime, hot-reload'}
- {repo: features-delta-one-service, code: C0, deployment: none, business: none, readiness_note: 'ServiceRuntime, UAC imports, hot-reload'}
- {repo: strategy-service, code: C0, deployment: none, business: none, readiness_note: 'ServiceRuntime, grid config, hot-reload'}
- {repo: execution-service, code: C0, deployment: none, business: none, readiness_note: 'ServiceRuntime, strategy-agnostic, classify_venue_error, grid config, hot-reload'}
- {repo: ml-training-service, code: C0, deployment: none, business: none, readiness_note: 'ServiceRuntime, UniformTrainingPipeline, ModelTrainerFactory, grid config refactor, hot-reload'}
- {repo: ml-inference-service, code: C0, deployment: none, business: none, readiness_note: 'ServiceRuntime, ensemble inference, hot-reload'}
- {repo: risk-management-service, code: C0, deployment: none, business: none, readiness_note: 'ServiceRuntime, seed_mock_data, hot-reload'}
- {repo: alerting-service, code: C0, deployment: none, business: none, readiness_note: 'ServiceRuntime, seed_mock_data, hot-reload'}
- {repo: pnl-attribution-service, code: C0, deployment: none, business: none, readiness_note: 'ServiceRuntime, seed_mock_data, hot-reload'}
- {repo: position-balance-monitor-service, code: C0, deployment: none, business: none, readiness_note: 'ServiceRuntime, seed_mock_data, hot-reload'}
- {repo: reconciliation-service, code: C0, deployment: none, business: none, readiness_note: 'seed_mock_data, hot-reload'}
- {repo: trading-agent-service, code: C0, deployment: none, business: none, readiness_note: 'seed_mock_data, hot-reload'}
- {repo: client-reporting-api, code: C0, deployment: none, business: none, readiness_note: 'P&L, invoicing, compliance, document CRUD'}
- {repo: config-api, code: C0, deployment: none, business: none, readiness_note: 'POST /config/publish, CLI command, --dry-run'}
- {repo: unified-trading-api, code: C0, deployment: none, business: none, readiness_note: 'New consolidated API repo — 16 domains, 61 endpoints, WebSocket'}
- {repo: unified-sports-execution-interface, code: C0, deployment: none, business: none, readiness_note: Resolve 50 browser adapter stubs}
- {repo: unified-market-interface, code: C0, deployment: none, business: none, readiness_note: 'Resolve 59 adapter stubs, 50+ line function refactoring, sports metrics'}
- {repo: unified-trading-pm, code: C0, deployment: none, business: none, readiness_note: 'service-access-matrix.yaml, readiness YAMLs, credential audit script'}
depends_on: []
isProject: true
todos:
- {id: p0-commit-sweep, content: '- [ ] [AGENT] P0. QG sweep + commit uncommitted changes across ~15 repos with pending defi/pipeline work.

    Source: defi_operation_capability_and_pipeline (item 96/96), live_batch_alignment_audit (item 27/27).

    Repos: unified-api-contracts, unified-defi-execution-interface, unified-internal-contracts, execution-service,

    plus ~11 others with uncommitted topology/alignment changes.

    Run `bash scripts/quality-gates.sh` per repo, then `git add` + `git commit`.

    ', status: todo, note: IMMEDIATE — unblocks all downstream work. Do NOT quickmerge yet.}
---

 UTL (unified-trading-library) ---
  - id: t0-utl-service-runtime
    content: |
      - [ ] [AGENT] P0. Build ServiceRuntime class in UTL.
      Source: service_protocol_resolution Phase 2.
      ServiceRuntime holds resolved config: cloud_provider, runtime_mode, testnet_mode, category, operation.
      All 13 services will construct from CLI args + env vars.
    status: todo
    note: "CRITICAL — unblocks T2-1 (13 service migrations)"
  - id: t0-utl-startup-validation
    content: |
      - [ ] [AGENT] P0. Build startup_validation.py in UTL.
      Source: service_protocol_resolution Phase 2.
      Validates ServiceRuntime at boot: checks env vars, topology, config sources. Emits STARTUP_VALIDATION_FAILED on error.
    status: todo
  - id: t0-utl-config-resolution
    content: |
      - [ ] [AGENT] P1. Config source resolution in UTL.
      Source: service_protocol_resolution Phase 2.
      Resolves config source (local file, GCS, S3) based on ServiceRuntime.cloud_provider + runtime_mode.
    status: todo
  - id: t0-utl-freshness-monitor
    content: |
      - [ ] [AGENT] P1. Implement FreshnessMonitor base class in UTL.
      Source: defi_keys_data_integration Phase 4.
      Base class for per-venue data freshness SLA tracking. Services subclass with their SLA config.
    status: todo
  - id: t0-utl-service-cli-runtime
    content: |
      - [ ] [AGENT] P0. ServiceCLI constructs ServiceRuntime from parsed args + env vars.
      Source: service_protocol_resolution Phase 3.
      ServiceCLI reads --mode, --asset-group, --operation, CLOUD_PROVIDER, TESTNET_MODE, constructs ServiceRuntime.
    status: todo

  # --- UIC (unified-internal-contracts) ---
  - id: t0-uic-ml-schemas
    content: |
      - [ ] [AGENT] P0. Add TrainingPhase StrEnum, extend TargetType + ModelType enums in UIC ml.py.
      Source: uniform_ml_pipeline Phase 1.
      TrainingPhase: DATA_PREP, FEATURE_ENG, SPLIT, TRAIN, EVALUATE. TargetType: add MATCH_RESULT, GOAL_TOTAL, etc.
      ModelType: add ENSEMBLE, STACKING, etc.
    status: todo
  - id: t0-uic-ensemble-config
    content: |
      - [ ] [AGENT] P0. Add EnsembleConfig + EnsembleMember + TrainingPipelineConfig Pydantic models to UIC.
      Source: uniform_ml_pipeline Phase 1.
    status: todo
  - id: t0-uic-grid-schemas
    content: |
      - [ ] [AGENT] P0. Add TargetTypeParams, StrategyModeParams, FixedConfig / GridDimensions to UIC.
      Source: fixed_grid_config Phase 1.
      Refactor ModelVariantConfig to use TargetTypeParams.
    status: todo
  - id: t0-uic-startup-error
    content: |
      - [ ] [AGENT] P1. Add STARTUP_VALIDATION_FAILED error code to UIC.
      Source: service_protocol_resolution Phase 1.
    status: todo
  - id: t0-uic-document-schemas
    content: |
      - [ ] [AGENT] P0. Add document metadata schema + document categories enum to UIC.
      Source: plan_i_client_reporting_docs Phase 0.
    status: todo

  # --- UCI (unified-config-interface) ---
  - id: t0-uci-domain-configs
    content: |
      - [ ] [AGENT] P0. Add 5 domain config schemas to UCI: RiskDomainConfig, AlertRuleDomainConfig,
      RateLimitDomainConfig, FeatureFlagDomainConfig, StrategyDomainConfig.
      Source: plan_b_config_hot_reload Phase 0.
    status: todo
  - id: t0-uci-data-sinks
    content: |
      - [ ] [AGENT] P0. Add GCSDataSink + S3DataSink to UCI. get_data_sink() auto-derives provider from ServiceRuntime.
      Source: service_protocol_resolution Phase 2.
    status: todo
  - id: t0-uci-runtime-mode
    content: |
      - [ ] [AGENT] P0. Unify SERVICE_MODE -> RUNTIME_MODE in UCI factory.py.
      Source: service_protocol_resolution Phase 2.
    status: todo
  - id: t0-uci-entitlement-registry
    content: |
      - [ ] [AGENT] P0. Create entitlement registry in UCI.
      Source: plan_g_auth_entitlement Phase 3.
    status: todo
  - id: t0-uci-slice-subscription
    content: |
      - [ ] [AGENT] P1. Add slice-based subscription to DomainConfigReloader.
      Source: strategy_system_citadel_master.
    status: todo
  - id: t0-uci-doc-helpers
    content: |
      - [ ] [AGENT] P0. Add pre-signed URL helpers + documents GCS bucket to UCI bucket registry.
      Source: plan_i_client_reporting_docs Phase 0.
    status: todo

  # --- UAC (unified-api-contracts) ---
  - id: t0-uac-error-maps
    content: |
      - [ ] [AGENT] P0. Fix aave_plasma bug in UAC error classifier + add 18 missing venue error maps.
      Source: plan_a_registry_schema_sync Phase 0, plan_d_testnet_stress_testing Phase 2.
    status: todo
  - id: t0-uac-data-source-split
    content: |
      - [ ] [AGENT] P0. Split TRADFI_VENUE_MAPPINGS into instrument identity + provider bindings.
      Source: instrument_data_source_separation Phase 1.
      Update VENUE_TO_DATA_SOURCE to 1:N with use_for field.
      Generalize data_source_continuity.py temporal resolution pattern.
    status: todo
  - id: t0-uac-prediction-market
    content: |
      - [ ] [AGENT] P0. Create PredictionMarketMapping type in UAC.
      Add Polymarket + Kalshi sports/crypto/macro mapping data.
      Source: sports_schema_allocation Phase 3.
    status: todo
  - id: t0-uac-registry-extractor
    content: |
      - [ ] [AGENT] P0. Enhance generate_ui_reference_data.py for all 13 registries + add tests.
      Source: plan_a_registry_schema_sync Phase 1.
    status: todo
  - id: t0-uac-polymarket-lint
    content: |
      - [ ] [AGENT] P0. Fix pre-existing polymarket lint errors in UAC.
      Source: instrument_data_source_separation Phase 1.
    status: todo

  # --- Other T0 Libraries ---
  - id: t0-usri-competition-phase
    content: |
      - [ ] [AGENT] P0. Create competition_phase.py in USRI.
      Source: uniform_ml_pipeline Phase 3.
    status: todo
  - id: t0-ufol-anti-leakage
    content: |
      - [ ] [AGENT] P0. Create anti_leakage.py in UFOL.
      Source: uniform_ml_pipeline Phase 3.
    status: todo

  # --- Phase 1 QG Gate ---
  - id: t0-qg-gate
    content: |
      - [ ] [SCRIPT] P0. QG gate: UTL, UIC, UCI, UAC, USRI, UFOL all pass quality-gates.sh.
    status: todo
    note: "GATE — Phase 2 cannot start until this passes."

  # ============================================================
  # PHASE 2: TIER 1 — Interface & Shared Library Updates (PARALLEL)
  # Depends on: Phase 1 QG gate.
  # ============================================================
  - id: t1-umi-config-schema
    content: |
      - [ ] [AGENT] P0. Update UMI config_schema.py: VALID_CATEGORIES, VALID_MODEL_TYPES, VALID_TARGET_TYPES, VALID_TIMEFRAMES.
      Update models.py: HyperparameterConfig generalization, ModelVariantConfig + _detect_category().
      Update config_schema.py generate_model_id().
      Source: uniform_ml_pipeline Phase 4.
    status: todo
  - id: t1-umi-grid-refactor
    content: |
      - [ ] [AGENT] P0. Refactor ModelVariantConfig + ModelMetadata in UMI models.py for grid config.
      Source: fixed_grid_config Phase 3.
    status: todo
  - id: t1-umi-sports-metrics
    content: |
      - [ ] [AGENT] P1. Create metrics/sports.py in UMI.
      Source: uniform_ml_pipeline Phase 4.
    status: todo
  - id: t1-mel-sports-matching
    content: |
      - [ ] [AGENT] P0. Create SportsMatchingEngine in matching-engine-library + tests.
      Source: uniform_ml_pipeline Phase 5.
    status: todo
  - id: t1-urdi-kalshi
    content: |
      - [ ] [AGENT] P1. Create KalshiReferenceDataAdapter in URDI.
      Source: sports_schema_allocation Phase 3.
    status: todo
  - id: t1-uac-openapi
    content: |
      - [ ] [AGENT] P0. Add execution-results-api to OpenAPI spec, fix empty schemas, restore TS codegen.
      Source: plan_a_registry_schema_sync Phase 2.
    status: todo
  - id: t1-pm-credential-audit
    content: |
      - [ ] [AGENT] P1. Build credential audit script in PM.
      Source: defi_keys_data_integration Phase 2.
    status: todo
  - id: t1-qg-gate
    content: |
      - [ ] [SCRIPT] P0. QG gate: UMI, MEL, URDI all pass quality-gates.sh.
    status: todo
    note: "GATE — Phase 3 cannot start until this passes."

  # ============================================================
  # PHASE 3: TIER 2 — Service-Level Changes (PARALLEL within groups)
  # Depends on: Phase 2 QG gate.
  # 5 parallel workstreams: ServiceRuntime, MockData, HotReload, ML, API.
  # ============================================================

  # --- Workstream A: ServiceRuntime Migration (13 services, PARALLEL) ---
  - id: t2-ws-a-service-runtime
    content: |
      - [ ] [AGENT] P0. Migrate 13 services to use ServiceRuntime: instruments, market-tick-data,
      features-onchain, features-delta-one, features-volatility, strategy, execution,
      ml-training, ml-inference, alerting, risk, pnl-attribution, position-balance.
      Each service: update CLI handler to construct ServiceRuntime, replace ad-hoc env reads, run QG.
      Source: service_protocol_resolution Phase 4.
    status: todo
    note: "PARALLEL per service. Each service is independent."
  - id: t2-ws-a-remove-protocol-envs
    content: |
      - [ ] [AGENT] P1. Remove all redundant PROTOCOL_* env vars across all services.
      Source: service_protocol_resolution Phase 5.
    status: todo

  # --- Workstream B: Mock Data Seed Scripts (PARALLEL) ---
  - id: t2-ws-b-seed-ml
    content: |
      - [ ] [AGENT] P1. ml-training-service + ml-inference-service seed_mock_data.py.
      Source: mock_data_rollout Phase 3 L4.
    status: todo
  - id: t2-ws-b-seed-strategy-exec
    content: |
      - [ ] [AGENT] P0. strategy-service + execution-service seed_mock_data.py.
      Source: mock_data_rollout Phase 3 L5.
    status: todo
  - id: t2-ws-b-seed-risk-pnl
    content: |
      - [ ] [AGENT] P1. risk + position-balance + pnl-attribution seed_mock_data.py.
      Source: mock_data_rollout Phase 3 L6.
    status: todo
  - id: t2-ws-b-seed-alerting
    content: |
      - [ ] [AGENT] P2. alerting + reconciliation + trading-agent seed_mock_data.py.
      Source: mock_data_rollout Phase 3 L7.
    status: todo
  - id: t2-ws-b-mock-mode-migration
    content: |
      - [ ] [AGENT] P0. Migrate ALL 22 repos from cloud_mock_mode to is_mock_mode().
      Source: mock_data_rollout Phase 3.
    status: todo
  - id: t2-ws-b-seed-cloud-writes
    content: |
      - [ ] [AGENT] P0. Upgrade all 21 seed scripts to support cloud storage writes.
      Source: mock_data_rollout Phase 4.
    status: todo

  # --- Workstream C: Config Hot-Reload (21 services, PARALLEL) ---
  - id: t2-ws-c-hot-reload
    content: |
      - [ ] [AGENT] P1. Wire hot-reload in 21 services: market-tick-data, market-data-processing,
      features-technical, features-microstructure, features-orderflow, features-alternative,
      features-cross-sectional, features-sentiment, features-onchain, features-sports,
      strategy, execution, trading-agent, risk-management, position-balance-monitor,
      pnl-attribution, alerting, reconciliation, ml-training, ml-inference.
      Source: plan_b_config_hot_reload Phase 1.
    status: todo
    note: "PARALLEL per service."
  - id: t2-ws-c-config-publish-api
    content: |
      - [ ] [AGENT] P0. Add POST /config/publish endpoint to config-api + CLI command + --dry-run.
      Source: plan_b_config_hot_reload Phase 2.
    status: todo
  - id: t2-ws-c-config-placement-fixes
    content: |
      - [ ] [AGENT] P1. Fix 12 config placement violations (8 in MTDS + 4 others).
      Source: plan_b_config_hot_reload Phase 3.
    status: todo

  # --- Workstream D: ML Pipeline + Sports ---
  - id: t2-ws-d-ml-training-pipeline
    content: |
      - [ ] [AGENT] P0. Create ModelTrainerFactory, rename ModelTrainer -> LightGBMTrainer,
      create EnsembleTrainer, create UniformTrainingPipeline.
      Add season-based split_strategy, sports_target_generator.py, generalize HyperparameterTuner.
      Source: uniform_ml_pipeline Phase 6.
    status: todo
  - id: t2-ws-d-ml-inference
    content: |
      - [ ] [AGENT] P0. Create ensemble_inference.py, sports inference adapter, generalize model loader.
      Source: uniform_ml_pipeline Phase 7.
    status: todo
  - id: t2-ws-d-features-sports
    content: |
      - [ ] [AGENT] P1. Features-sports-service: calculator field parity, wire USRI/UFI loaders,
      batch handler, Understat scraping, wire anti_leakage, enrich 7 calculators, weather_calculator.
      Source: instruments_service_completion Phase 3, uniform_ml_pipeline Phase 6.
    status: todo
  - id: t2-ws-d-grid-config-training
    content: |
      - [ ] [AGENT] P0. Refactor ml-training-service: MLTrainingConfig, training_orchestrator,
      TargetGenerator, CLI handlers, grid_search_handler, train_handler, 57+ test files.
      Source: fixed_grid_config Phase 4.
    status: todo
  - id: t2-ws-d-grid-config-strategy
    content: |
      - [ ] [AGENT] P0. Extend strategy-service grid_generator with per-strategy-mode support + validation.
      Source: fixed_grid_config Phase 5.
    status: todo
  - id: t2-ws-d-grid-config-execution
    content: |
      - [ ] [AGENT] P0. Extend execution-service backtest grid + config_loader for ExecutionGridConfig.
      Source: fixed_grid_config Phase 6.
    status: todo

  # --- Workstream E: Instruments + Data Source ---
  - id: t2-ws-e-instruments-uac-imports
    content: |
      - [ ] [AGENT] P0. Update instruments-service: delete duplicates, import from UAC.
      Update MDPS + features-delta-one: import from UAC.
      Source: instruments_service_batch_validation Phase B2.
    status: todo
  - id: t2-ws-e-instruments-config
    content: |
      - [ ] [AGENT] P0. Create instruments-service config generation script + wire cloud storage loading.
      Source: instruments_service_batch_validation Phase C.
    status: todo
  - id: t2-ws-e-instruments-data-source
    content: |
      - [ ] [AGENT] P0. Update instruments-service venue_config.py for new data source bindings.
      Source: instrument_data_source_separation Phase 2.
    status: todo
  - id: t2-ws-e-instruments-live
    content: |
      - [ ] [AGENT] P0. Implement instruments-service live mode handler + ConfigReloader hot-reload + PubSub wiring.
      Source: instruments_service_completion Phase 4.
    status: todo
  - id: t2-ws-e-prediction-market-resolver
    content: |
      - [ ] [AGENT] P0. Create PredictionMarketResolver in instruments-service.
      Source: sports_schema_allocation Phase 3.
    status: todo

  # --- Workstream F: Execution + Strategy ---
  - id: t2-ws-f-exec-strategy-agnostic
    content: |
      - [ ] [AGENT] P0. Make execution-service strategy-agnostic.
      Audit and migrate all StrategyInstruction/ExecutionResult schemas.
      Source: strategy_system_citadel_master.
    status: todo
  - id: t2-ws-f-classify-venue-error
    content: |
      - [ ] [AGENT] P0. Wire classify_venue_error() into execution-service.
      Source: plan_a_registry_schema_sync Phase 0.
    status: todo

  # --- Workstream G: API Hardening ---
  - id: t2-ws-g-api-mock-health
    content: |
      - [ ] [AGENT] P0. Audit + fix mock mode gaps across 12 APIs. Fix health endpoint gaps.
      Standardize error + pagination response shape. Verify OpenAPI parity.
      Source: plan_c_domain_data_api Phases 0-2.
    status: todo
  - id: t2-ws-g-client-reporting
    content: |
      - [ ] [AGENT] P0. Client-reporting-api: P&L reporting, client returns, settlement,
      invoice generation/delivery/billing, trade reporting (MiFID II), best execution,
      compliance, document management CRUD, seed_mock_data.
      Source: plan_i_client_reporting_docs Phases 1-5.
    status: todo

  # --- Phase 3 QG Gate ---
  - id: t2-qg-gate
    content: |
      - [ ] [SCRIPT] P0. QG gate: all 30+ affected service repos pass quality-gates.sh.
    status: todo
    note: "GATE — Phase 4 cannot start until this passes."

  # ============================================================
  # PHASE 4: TIER 3 — Cross-Cutting / Auth / API Consolidation (SEQUENTIAL)
  # Depends on: Phase 3 QG gate.
  # ============================================================
  - id: t3-auth-access-matrix
    content: |
      - [ ] [AGENT] P0. Define 8 service categories + document subscription slicing.
      Create service-access-matrix.yaml in PM.
      Source: plan_g_auth_entitlement Phase 0.
    status: todo
  - id: t3-auth-s2s-enrollment
    content: |
      - [ ] [AGENT] P0. Enroll remaining 19 services in S2S auth + standardize auth middleware across 9 APIs.
      Source: plan_g_auth_entitlement Phase 1-2.
    status: todo
  - id: t3-auth-entitlement-middleware
    content: |
      - [ ] [AGENT] P0. Add entitlement checking middleware + enforce instrument count limits at API level.
      Source: plan_g_auth_entitlement Phase 3.
    status: todo
  - id: t3-api-consolidation-scaffold
    content: |
      - [ ] [AGENT] P0. Create unified-trading-api repo: pyproject.toml (flat deps), quality-gates.sh,
      /health, entitlement middleware, MockStateStore integration.
      Source: plan_h_api_consolidation Phase 0.
    status: todo
  - id: t3-api-consolidation-routes
    content: |
      - [ ] [AGENT] P0. Migrate 14 route modules (PARALLEL): market-data, execution, positions,
      trading/analytics, ml, reporting, audit, config, alerts, risk, instruments, documents,
      deployment, service-status.
      Source: plan_h_api_consolidation Phase 1.
    status: todo
  - id: t3-api-consolidation-ws
    content: |
      - [ ] [AGENT] P0. Add /ws WebSocket endpoint + channels + mock/real mode.
      Source: plan_h_api_consolidation Phase 2.
    status: todo
  - id: t3-api-consolidation-mock-openapi
    content: |
      - [ ] [AGENT] P0. Seed mock data for all 16 domains. Auto-generate unified OpenAPI spec + TS codegen.
      Source: plan_h_api_consolidation Phases 3-4.
    status: todo
  - id: t3-readiness-yamls
    content: |
      - [ ] [AGENT] P0. Create readiness YAMLs for all repos.
      Source: full_system_audit_resolution P0-10.
    status: todo
  - id: t3-usei-stubs
    content: |
      - [ ] [AGENT] P1. Resolve 50 USEI sports browser adapter stubs (implement or remove).
      Source: full_system_audit_resolution P3-05.
    status: todo
  - id: t3-umi-stubs
    content: |
      - [ ] [AGENT] P1. Resolve 59 UMI adapter stubs (implement or remove).
      Source: full_system_audit_resolution P3-06.
    status: todo
  - id: t3-sandbox-mode
    content: |
      - [ ] [AGENT] P1. Define CLOUD_SANDBOX_MODE + VITE_SANDBOX_MODE + rollout across all 60+ repos.
      Source: production_mock_e2e_plan.
    status: todo
  - id: t3-vcr-cassettes
    content: |
      - [ ] [AGENT] P1. Record VCR cassettes: Tardis, 7 HTTP vendors, 16 DeFi endpoints, 3 flagged repos.
      Source: defi_keys_data_integration Phase 3.
    status: todo
  - id: t3-freshness-monitor-wiring
    content: |
      - [ ] [AGENT] P2. Wire FreshnessMonitor into 10 data-producing services.
      Source: defi_keys_data_integration Phase 4.
    status: todo
  - id: t3-qg-refactoring
    content: |
      - [ ] [AGENT] P2. Refactor 50+ line functions in UMI. Refactor execution/instruments/strategy services.
      Source: quality_gates_systemic_remediation.
    status: todo
  - id: t3-ci-triggers
    content: |
      - [ ] [AGENT] P1. Create GHA workflows for UAC registry regen + UIC OpenAPI codegen.
      Add QG check for classify_venue_error venue key parity.
      Source: plan_a_registry_schema_sync Phase 3.
    status: todo
  - id: t3-qg-gate
    content: |
      - [ ] [SCRIPT] P0. QG gate: unified-trading-api, all auth-affected repos, PM pass quality-gates.sh.
    status: todo
    note: "GATE — Phase 5 cannot start until this passes."

  # ============================================================
  # PHASE 5: TIER 4 — Testing & Validation (SEQUENTIAL after Phase 4)
  # ============================================================
  - id: t4-defi-pipeline-e2e
    content: |
      - [ ] [AGENT] P0. Run DeFi pipeline end-to-end via service CLIs:
      instruments-service --asset-group DEFI -> market-tick-data-service --asset-group DEFI -> features-onchain-service --asset-group DEFI.
      Source: defi_operation_capability_and_pipeline (item 95/96).
    status: todo
  - id: t4-qg-sweep-30-repos
    content: |
      - [ ] [SCRIPT] P0. Run QG on all 30 repos affected by live/batch alignment.
      Source: live_batch_alignment_audit (item 27/27).
    status: todo
  - id: t4-mock-data-generate
    content: |
      - [ ] [HUMAN+AGENT] P0. Run generate-mock-data.sh against dev GCS bucket + validate.
      Source: mock_data_rollout Phase 4.
    status: todo
  - id: t4-service-protocol-e2e
    content: |
      - [ ] [AGENT] P0. End-to-end pipeline tests: CLOUD_PROVIDER=gcp --mode batch,
      CLOUD_MOCK_MODE=true, TESTNET_MODE=true DeFi execution.
      Source: service_protocol_resolution Phase 5.
    status: todo
  - id: t4-ml-integration-tests
    content: |
      - [ ] [AGENT] P0. Integration tests: sports 5-phase pipeline, financial 3-phase pipeline.
      Source: uniform_ml_pipeline Phase 8.
    status: todo
  - id: t4-stress-testing
    content: |
      - [ ] [AGENT] P1. Testnet stress testing: seed determinism, scenario infrastructure,
      error code stress, performance gates, load testing, deployment mock scenarios.
      Source: plan_d_testnet_stress_testing (33 items).
    status: todo
  - id: t4-cicd-e2e
    content: |
      - [ ] [AGENT] P1. CI/CD E2E testing: workflow validation, cascade testing, failure modes,
      agent validation, golden path test.
      Source: cicd_e2e_testing_master (57 items).
    status: todo
  - id: t4-t0-t1-qg-quickmerge
    content: |
      - [ ] [SCRIPT] P0. T0 (6 repos) + T1 (3 repos): QG pass + quickmerge to main.
      Source: cicd_code_rollout_master.
    status: todo
  - id: t4-codex-docs
    content: |
      - [ ] [AGENT] P1. Write codex docs: service-control-surface.md, fixed-grid-config.md.
      Update SSOT-INDEX. Codify 6-stage testing progression.
      Source: service_protocol_resolution, fixed_grid_config, cicd_code_rollout_master.
    status: todo
  - id: t4-final-qg-sweep
    content: |
      - [ ] [SCRIPT] P0. Final QG sweep on ALL repos touched by this plan.
    status: todo
    note: "FINAL GATE — plan archivable when this passes."

  # ============================================================
  # BLOCKED — Prod-Only / Human-Only (tracked but not actionable now)
  # ============================================================
  - id: blocked-1-0-0
    content: |
      - [ ] [HUMAN] P0. 1.0.0 promotion for all repos.
      Source: cicd_code_rollout_master.
    status: blocked
    note: "BLOCKED — deliberate human decision, not automatable."
  - id: blocked-prod-audit
    content: |
      - [ ] [HUMAN] P0. Full 28-section production readiness audit.
      Source: cicd_code_rollout_master.
    status: blocked
    note: "BLOCKED — prod only."
  - id: blocked-sit-main
    content: |
      - [ ] [HUMAN] P0. Final SIT validation on main.
      Source: cicd_code_rollout_master.
    status: blocked
    note: "BLOCKED — prod only."
  - id: blocked-ibkr
    content: |
      - [ ] [HUMAN+AGENT] P2. IBKR gateway credentials + adapter consolidation.
      Source: cicd_code_rollout_master.
    status: blocked
    note: "BLOCKED — credential + infra setup."
  - id: blocked-vendor-keys
    content: |
      - [ ] [HUMAN] P1. Load WS vendor credentials, Phase 3/4 vendor keys, DeFi testnet secrets, CI bootstrap.
      Source: defi_keys_data_integration.
    status: blocked
    note: "BLOCKED — human key procurement."
  - id: blocked-sports-keys
    content: |
      - [ ] [HUMAN] P2. Rotate OddsAPI key, Pinnacle API credentials.
      Source: instruments_service_completion.
    status: blocked
    note: "BLOCKED — human key management."
  - id: blocked-api-archive
    content: |
      - [ ] [HUMAN] P2. Archive old API repos after unified-trading-api is live.
      Source: plan_h_api_consolidation.
    status: blocked
    note: "BLOCKED — human decision."
---

# Notes & Context

## Audit Source (2026-03-21)

This plan was generated by auditing all 25 backend-relevant active plans and extracting every unchecked `- [ ]` item.
Plans audited:

| Plan                                        | Done/Total | Status                                  |
| ------------------------------------------- | ---------- | --------------------------------------- |
| registry_completeness_implementation_detail | 30/30      | ARCHIVE CANDIDATE                       |
| quality_gates_full_fix                      | paused     | ARCHIVE CANDIDATE (superseded)          |
| live_batch_alignment_audit                  | 26/27      | 1 QG sweep remaining                    |
| defi_operation_capability_and_pipeline      | 94/96      | 2 items: pipeline run + commit sweep    |
| full_system_audit_resolution                | 24/27      | 3 items: readiness YAMLs + 109 stubs    |
| cicd_code_rollout_master                    | 98/110     | 12 items (mix of infra/testing/blocked) |
| instruments_service_completion              | 13/25      | 12 open                                 |
| instruments_service_batch_validation        | 8/20       | 12 open                                 |
| mock_data_rollout                           | 12/24      | 12 open                                 |
| strategy_system_citadel_master              | 40/48      | 8 open                                  |
| sports_schema_allocation_restructuring      | 16/24      | 8 open                                  |
| quality_gates_systemic_remediation          | 9/14       | 5 open                                  |
| defi_keys_data_integration                  | 6/28       | 22 open                                 |
| production_mock_e2e_plan                    | 12/14      | 2 open                                  |
| cicd_e2e_testing_master                     | 5/62       | 57 open                                 |
| fixed_grid_config_refactor                  | 0/38       | 38 open                                 |
| uniform_ml_pipeline_sports_migration        | 0/62       | 62 open                                 |
| service_protocol_resolution                 | 2/29       | 27 open                                 |
| plan_a_registry_schema_sync                 | 0/16       | 16 open                                 |
| plan_b_config_hot_reload                    | 0/34       | 34 open                                 |
| plan_c_domain_data_api                      | 0/11       | 11 open                                 |
| plan_d_testnet_stress_testing               | 0/33       | 33 open                                 |
| plan_g_auth_entitlement                     | 0/18       | 18 open                                 |
| plan_h_api_consolidation                    | 0/45       | 45 open                                 |
| plan_i_client_reporting_docs                | 0/35       | 35 open                                 |

## Execution DAG

```
Phase 0: Commit Sweep (~15 repos)
    |
Phase 1: T0 Libraries (PARALLEL: UTL, UIC, UCI, UAC, USRI, UFOL)
    |--- QG GATE ---
Phase 2: T1 Interfaces (PARALLEL: UMI, MEL, URDI)
    |--- QG GATE ---
Phase 3: T2 Services (5 PARALLEL workstreams)
    |  A: ServiceRuntime (13 services)
    |  B: Mock Data (seed scripts + migration)
    |  C: Config Hot-Reload (21 services)
    |  D: ML Pipeline + Sports
    |  E: Instruments + Data Source
    |  F: Execution + Strategy
    |  G: API Hardening
    |--- QG GATE ---
Phase 4: T3 Cross-Cutting (SEQUENTIAL)
    |  Auth -> API Consolidation -> Readiness -> Stubs -> Sandbox
    |--- QG GATE ---
Phase 5: T4 Testing & Validation
    |  DeFi E2E -> QG Sweep -> Mock Data -> Protocol E2E -> ML Integration -> Stress -> CI/CD E2E
    |--- FINAL QG GATE ---
```

## Parallelization Strategy

- **Phase 1**: 6 library repos can be worked on by 6 parallel agents (UTL, UIC, UCI, UAC, USRI, UFOL)
- **Phase 3**: 7 workstreams (A-G) are independent and can run in parallel
- **Phase 3A**: 13 service migrations within workstream A are independent
- **Phase 3C**: 21 hot-reload wirings within workstream C are independent
- **Phase 4**: Auth must complete before API consolidation (entitlement middleware dependency)

## Success Criteria

- **Phase 0**: All defi-related repos have clean git status
- **Phase 1**: All T0 libraries pass `bash scripts/quality-gates.sh`
- **Phase 2**: All T1 libraries pass QG
- **Phase 3**: All 30+ services pass QG
- **Phase 4**: unified-trading-api passes QG, auth integration tests pass
- **Phase 5**: DeFi pipeline runs E2E, mock data generates successfully, all integration tests pass

## Key Dependencies Between Source Plans

- `service_protocol_resolution` -> blocks `instruments_service_completion` (live mode needs ServiceRuntime)
- `instrument_data_source_separation` -> blocks `instruments_service_batch_validation` (venue_config.py changes)
- `plan_a_registry_schema_sync` -> blocks `plan_d_testnet_stress_testing` (error map completeness)
- `plan_g_auth_entitlement` -> blocks `plan_h_api_consolidation` (entitlement middleware)
- `uniform_ml_pipeline` -> blocks `fixed_grid_config_refactor` (ModelVariantConfig changes overlap)
- `mock_data_rollout` -> blocks `plan_d_testnet_stress_testing` (seed determinism)
