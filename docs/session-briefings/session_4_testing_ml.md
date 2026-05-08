# Session 4: Testing & ML/Strategy

> **2026-03-24:** Historical session charter. API names below were updated to the **consolidated** surface
> (**`unified-trading-api`**, **`auth-api`**) where they referred to standalone repos now under **`archive/`**. See
> **`archive/README.md`** and **`scripts/dev/ui-api-mapping.json`**.

## Services & Repos Affected

> **DO NOT work on these repos in other sessions -- they are owned by this session.**

| Repo                                                                      | What Changes                                                                                                                                                                                                                                                           | Risk |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- |
| unified-internal-contracts (domain/ml/ + testing/)                        | TargetTypeParams, StrategyModeParams, FixedConfig/GridDimensions schemas, TrainingPhase/TargetType/ModelType enums, HyperparameterConfig discriminated union, TrainingPipelineConfig, ScenarioConfig enhancements (BAD_SCHEMA, ERROR_STORM, FLASH_CRASH, HIGH_LATENCY) | HIGH |
| unified-ml-interface                                                      | ModelVariantConfig refactor (target_params), ModelMetadata delegation, HyperparameterConfig generic wrapper, sports categories/model types/target types/timeframes, sports metrics                                                                                     | HIGH |
| unified-trading-library (PerformanceGate/MemoryGate only)                 | CI activation of PerformanceGate + MemoryGate, performance baseline recording                                                                                                                                                                                          | MED  |
| system-integration-tests (scenarios + perf only)                          | SIT tests for BAD_SCHEMA/ERROR_STORM/FLASH_CRASH scenarios, mock-vs-live parity test, end-to-end scenario test                                                                                                                                                         | MED  |
| deployment-service                                                        | seed_mock_data.py (missing), mock VM lifecycle state machine, shard failure scenarios, health gate timeout, quota exhaustion, cross-region failover, orphan cleanup                                                                                                    | MED  |
| ml-training-service                                                       | Grid config refactor (TrainingGridConfig -> fixed + grid), variant generation, TargetGenerator, CLI handlers, ModelTrainerFactory, UniformTrainingPipeline, sports target generators, ensemble training                                                                | HIGH |
| ml-inference-service                                                      | Grid config, ensemble inference, sports inference adapter, multi-model-type loading                                                                                                                                                                                    | MED  |
| strategy-service (grid_generator.py + batch/live handlers)                | StrategyGridConfig, per-strategy-mode grid, strategy mode param validation                                                                                                                                                                                             | MED  |
| execution-service (grid generation only)                                  | ExecutionGridConfig, per-algo param grids, config_loader.py update                                                                                                                                                                                                     | MED  |
| unified-config-interface (ml_config.py + strategy/execution grid configs) | MLTrainingConfig refactor (target_type_params), StrategyGridConfig, ExecutionGridConfig schemas                                                                                                                                                                        | MED  |
| unified-domain-client                                                     | ModelVariantConfig.swing_lookback_window -> target_params access pattern                                                                                                                                                                                               | LOW  |
| unified-sports-reference-interface                                        | competition_phase.py (classify_competition_phase)                                                                                                                                                                                                                      | LOW  |
| unified-feature-orchestration-library                                     | anti_leakage.py (validate_no_leakage)                                                                                                                                                                                                                                  | LOW  |
| features-sports-service                                                   | Weather calculator, anti-leakage wiring, enriched calculators (odds, poisson_xg, h2h, halftime, team_form)                                                                                                                                                             | MED  |
| matching-engine-library                                                   | SportsMatchingEngine (bet placement, settlement)                                                                                                                                                                                                                       | MED  |

### Shared Repo Boundaries

- **unified-internal-contracts**: Session 4 OWNS domain/ml/ (schemas.py, enums), domain/strategy_service/,
  testing/scenarios/ (new YAML configs), testing/scenario_config.py (ScenarioConfig enhancements), modes.py
  (MockScenario enum). Session 1 OWNS openapi/ directory. No overlap.
- **unified-config-interface**: Session 4 OWNS ml_config.py (MLTrainingConfig refactor), strategy_grid_config.py (new),
  execution_config_schema.py (ExecutionGridConfig). Session 2 OWNS domain config schemas. Session 3 OWNS auth/
  directory. No overlap.
- **unified-trading-library**: Session 4 OWNS PerformanceGate/MemoryGate CI activation. Session 2 OWNS ConfigReloader.
  No overlap.
- **execution-service**: Session 4 OWNS grid generation and config_loader.py for ExecutionGridConfig, and performance
  gate fixtures. Session 1 OWNS engine/ error classification. Session 2 OWNS hot-reload callback. No file overlap.
- **strategy-service**: Session 4 OWNS grid_generator.py, batch_handler.py, live_handler.py for StrategyGridConfig.
  Session 2 OWNS hot-reload callback. No overlap.
- **ml-training-service**: Session 4 OWNS entirely (grid refactor, pipeline, trainers, target generators). Session 2
  OWNS only hot-reload callback (different file).
- **ml-inference-service**: Session 4 OWNS entirely (ensemble inference, sports adapter, model loader). Session 2 OWNS
  only hot-reload callback (different file).
- **system-integration-tests**: Session 4 OWNS tests/smoke/test_mock_scenarios.py, tests for performance/load,
  mock-vs-live parity. Session 3 OWNS auth penetration tests and document flow tests. No overlap.
- **deployment-service**: Session 4 OWNS entirely for this session (seed_mock_data.py, mock VM lifecycle, shard
  failures).
- **features-sports-service**: Session 4 OWNS calculator enrichment and anti-leakage wiring. Session 2 OWNS hot-reload
  callback only. Session 3 OWNS data source wiring (USRI/UFI). Calculators vs data-loading are separate code paths -- no
  overlap.

## Plans Covered

| Plan                                 | Phases    | Todos Remaining | Reference                                                            |
| ------------------------------------ | --------- | --------------- | -------------------------------------------------------------------- |
| Plan D: Testnet & Stress Testing     | Phase 0-6 | ~26 todos       | plans/active/plan_d_testnet_stress_testing_2026_03_21.md        |
| fixed_grid_config_refactor           | Phase 1-5 | ~25 todos       | plans/active/fixed_grid_config_refactor_2026_03_21.md           |
| uniform_ml_pipeline_sports_migration | Phase 1-5 | ~40+ todos      | plans/active/uniform_ml_pipeline_sports_migration_2026_03_20.md |

## What's Already Done (Don't Redo)

- **PerformanceGate + MemoryGate**: Built in UTL, exported. Need CI activation (not built yet).
- **Fault injection**: Wired into 2 services. Framework exists but services don't consume FaultConfig from
  ScenarioConfig YAML.
- **MockScenario enum**: 8 scenarios already defined in UIC modes.py. Need 4 new ones (BAD_SCHEMA, ERROR_STORM,
  FLASH_CRASH, HIGH_LATENCY).
- **ScenarioConfig**: Loads from YAML, 8 scenarios exist in unified-internal-contracts/testing/scenarios/.
- **SyntheticDataGenerator**: Tick generation working. Seed data pipeline complete (21 services).
- **70 SIT tests**: Existing in system-integration-tests. Extend, don't rewrite.
- **Full mock data pipeline**: 21 services, 11GB -- Phase 3 of mock_data_rollout is DONE.
- **L0Matcher, sports routing, CanonicalFill convergence**: All done in live_batch_alignment Phase 0.
- **SportsMatchingEngine**: NOT yet built (part of uniform_ml_pipeline Phase 2c).
- **Matching engine wired into execution-service**: DONE (live_batch_alignment Phase 1A).
- **Strategy FillSource protocol**: DONE (live_batch_alignment Phase 1B).

## Execution Order

1. **Plan D Phase 0: Seed Hardening** (PARALLEL, no dependencies):
   - Audit all seed_mock_data.py scripts for --seed determinism
   - Fix scripts lacking seed=42 support
   - Document seed vs logic services in codex

2. **Grid Config Refactor Phase 1: UIC Schemas** (PARALLEL with Plan D Phase 0):
   - Add TargetTypeParams, StrategyModeParams, FixedConfig/GridDimensions to UIC domain/ml/schemas.py
   - Update **init**.py exports + tests
   - QG gate: unified-internal-contracts

3. **Uniform ML Pipeline Phase 1: UIC Contracts** (PARALLEL with Phase 2 above):
   - Add TrainingPhase, extend TargetType/ModelType enums
   - Generalize HyperparameterConfig -> discriminated union
   - Add EnsembleConfig, TrainingPipelineConfig
   - QG gate: unified-internal-contracts

4. **Plan D Phase 1: Scenario Infrastructure** (SEQUENTIAL after Phase 0):
   - Extend MockScenario enum with BAD_SCHEMA, ERROR_STORM, FLASH_CRASH, HIGH_LATENCY
   - Add scenario YAML configs
   - Scenario activation API endpoint
   - Scenario propagation via PubSub
   - SIT scenario tests

5. **Grid Config Refactor Phases 2a/2b** (PARALLEL, after Phase 1 UIC):
   - Phase 2a: unified-ml-interface -- ModelVariantConfig target_params, ModelMetadata delegation
   - Phase 2b: unified-config-interface -- MLTrainingConfig refactor, StrategyGridConfig, ExecutionGridConfig

6. **Uniform ML Pipeline Phases 2a-2d** (PARALLEL groups, after Phase 1):
   - 2a: unified-ml-interface -- sports categories, metrics, model types
   - 2b: USRI competition_phase, UFOL anti_leakage, UCI sports configs
   - 2c: matching-engine-library SportsMatchingEngine
   - 2d: features-sports-service calculator enrichment + anti-leakage wiring

7. **Plan D Phase 2: Error Code Stress Testing** (PARALLEL with Phase 1):
   - Re-audit VENUE_ERROR_MAP completeness
   - Add missing venue error maps
   - Wire classify_venue_error into execution-service error routing
   - ERROR_STORM scenario test suite
   - QG check for venue error coverage

8. **Plan D Phase 3: Performance Regression Gates** (PARALLEL with Phase 1):
   - Integrate PerformanceGate + MemoryGate into CI for 4 critical services
   - MemoryGate tests for 3 memory-pressure services
   - Establish performance baselines in PM configs

9. **Grid Config Refactor Phases 3a/3b/3c** (PARALLEL, after Phase 2):
   - 3a: ml-training-service grid refactor (TrainingGridConfig, variant generation, TargetGenerator, CLI)
   - 3b: strategy-service grid refactor (StrategyGridConfig, per-mode params)
   - 3c: execution-service grid refactor (ExecutionGridConfig, per-algo params)

10. **Uniform ML Pipeline Phase 3: ml-training-service** (after Phase 2):
    - ModelTrainerFactory, UniformTrainingPipeline, sports target generators
    - Season-based walk-forward validation
    - Ensemble training

11. **Plan D Phase 4: Load Testing** (SEQUENTIAL after Phase 3):
    - Synthetic load generator script in PM scripts/load-testing/
    - Instrument scaling test (45 -> 1K -> 5K -> 10K)
    - Response time baselines
    - Weekly stress test CI job

12. **Plan D Phase 5: Deployment Service Mock Scenarios** (PARALLEL with Phase 3):
    - deployment-service seed_mock_data.py
    - Mock VM lifecycle state machine
    - Mock shard failure scenarios
    - Health gate timeout, quota exhaustion, cross-region failover, orphan cleanup

13. **Grid Config Refactor Phase 4 + ML Pipeline Phases 4-5** (after Phase 3):
    - Update unified-domain-client, ml-inference-service
    - Ensemble inference, sports adapter
    - Full QG sweep on all affected repos
    - Codex documentation

14. **Plan D Phase 6: Final Validation** (SEQUENTIAL after all):
    - QG sweep on all affected repos
    - Mock-vs-live parity test
    - End-to-end scenario test

## Key Rules

- `uv pip install` not `pip install`
- Never run pytest directly -- use `bash scripts/quality-gates.sh`
- Do NOT run quickmerge -- only `git add` + `git commit`
- `basedpyright` not `pyright` (with `run_timeout 120`)
- Shard-level failure isolation -- no `raise` inside per-venue/per-shard loops
- No `# type: ignore` to hide architectural violations -- fix the root cause
- No `try/except ImportError` around library imports -- fail loud
- HyperparameterConfig discriminated union requires EXPLICIT model_type -- no implicit default
- ModelVariantConfig: swing_lookback_window/std_dev_threshold/breakout_threshold move to target_params dict
- Backwards compat: old flat configs must still deserialize via `@model_validator(mode="before")`
- Grid only explodes within relevant parameter space -- swing_high grid never applies odds_time_bucket

## CITADEL AUDIT FINDINGS (2026-03-21)

This session needs to address the following honest status corrections:

1. **PerformanceGate/MemoryGate exist in UTL but NOT activated in QG scripts.** A prior audit incorrectly claimed these
   classes did not exist — they DO exist and are exported from UTL. Test files (tests/perf/) were created in 5 services.
   HOWEVER, these perf tests are NOT invoked by any service's quality-gates.sh script. They exist as dead test files
   that CI never runs. Plan D Phase 3 todos have been reset to NOT DONE. Must: add explicit perf test invocation to each
   service's quality-gates.sh, then record baselines.

2. **Plan D Phase 0 (seed hardening) IS genuinely done.** All 15 seed scripts have --seed support. Do not re-do.

3. **Plan D Phase 2 (error code audit) Phase 0 items ARE genuinely done.** VENUE_ERROR_MAP has 32/33 venues covered.

4. **18/21 service mock providers are hollow stubs** — this affects Plan D scenario testing since scenarios depend on
   mock mode producing realistic data. Coordinate with Session 2 on mock provider quality.

## Success Criteria

- [ ] All QGs pass on all 16 affected repos
- [ ] All seed scripts produce deterministic output with --seed 42
- [ ] 4 new MockScenario values work end-to-end (BAD_SCHEMA, ERROR_STORM, FLASH_CRASH, HIGH_LATENCY)
- [ ] PerformanceGate + MemoryGate active in CI for 4 critical services
- [ ] Synthetic load generator runs, instruments scale to 10K
- [ ] deployment-service has working seed_mock_data.py + VM lifecycle + shard failure scenarios
- [ ] TrainingGridConfig accepts per-target-type param bags (not flat cartesian)
- [ ] StrategyGridConfig accepts per-strategy-mode param bags
- [ ] ExecutionGridConfig accepts per-algo param bags
- [ ] Backwards compat: old flat configs still deserialize
- [ ] Sports 5-phase training pipeline produces CLV/xG/HT models
- [ ] Financial 3-phase pipeline still works (no regressions)
- [ ] SportsMatchingEngine simulates bet placement/settlement
- [ ] Anti-leakage enforcement active in features-sports-service
- [ ] Mock-vs-live parity test passes in SIT
