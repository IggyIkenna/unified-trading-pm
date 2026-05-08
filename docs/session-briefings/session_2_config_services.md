# Session 2: Config & Service Hardening

> **2026-03-24:** Historical session charter. API names below were updated to the **consolidated** surface
> (**`unified-trading-api`**, **`auth-api`**) where they referred to standalone repos now under **`archive/`**. See
> **`archive/README.md`** and **`scripts/dev/ui-api-mapping.json`**.

## Services & Repos Affected

> **DO NOT work on these repos in other sessions -- they are owned by this session.**

| Repo                             | What Changes                                                                     | Risk |
| -------------------------------- | -------------------------------------------------------------------------------- | ---- |
| unified-config-interface         | 5 domain config schemas (Risk, AlertRule, RateLimit, FeatureFlag, Strategy)      | MED  |
| unified-trading-library          | ConfigReloader / DomainConfigReloader enhancements if needed                     | LOW  |
| unified-trading-api (config)     | POST /config/publish endpoint, CLI command, --dry-run flag                       | MED  |
| market-tick-data-service         | 8 config placement violations + hot-reload callback                              | HIGH |
| market-data-processing-service   | Hot-reload callback wiring                                                       | LOW  |
| features-technical-service       | Hot-reload callback wiring                                                       | LOW  |
| features-microstructure-service  | Hot-reload callback wiring                                                       | LOW  |
| features-orderflow-service       | Hot-reload callback wiring                                                       | LOW  |
| features-alternative-service     | Hot-reload callback wiring                                                       | LOW  |
| features-cross-sectional-service | Hot-reload callback wiring                                                       | LOW  |
| features-sentiment-service       | Hot-reload callback wiring                                                       | LOW  |
| features-onchain-service         | Hot-reload callback wiring                                                       | LOW  |
| features-sports-service          | Hot-reload callback wiring                                                       | LOW  |
| strategy-service                 | Hot-reload callback wiring (StrategyDomainConfig)                                | MED  |
| trading-agent-service            | Hot-reload callback wiring                                                       | LOW  |
| risk-management-service          | Hot-reload callback (RiskDomainConfig -- atomic swap critical)                   | HIGH |
| position-balance-monitor-service | Hot-reload callback wiring                                                       | LOW  |
| pnl-attribution-service          | Hot-reload callback wiring                                                       | LOW  |
| alerting-service                 | Hot-reload callback (AlertRuleDomainConfig)                                      | MED  |
| reconciliation-service           | Hot-reload callback wiring                                                       | LOW  |
| ml-training-service              | Hot-reload callback wiring                                                       | LOW  |
| ml-inference-service             | Hot-reload callback wiring                                                       | LOW  |
| deployment-api                   | Mock mode audit + response schema standardization (Plan C)                       | LOW  |
| unified-trading-api              | Mock mode audit + OpenAPI/schema parity (Plan C; supersedes archived split APIs) | LOW  |
| market-data-api                  | Mock mode audit + response schema standardization (Plan C)                       | LOW  |
| risk-management-service          | Mock mode audit + health endpoints (Plan C)                                      | LOW  |

### Shared Repo Boundaries

- **unified-config-interface**: Session 2 OWNS domain config schemas (risk, alert, rate-limit, feature-flag, strategy
  config files). Session 3 OWNS auth/ directory (entitlement_registry.yaml, service_access_matrix.yaml). Session 4 OWNS
  nothing in UCfgI.
- **unified-trading-library**: Session 2 OWNS ConfigReloader/DomainConfigReloader only. Session 4 OWNS
  PerformanceGate/MemoryGate only.
- **execution-service**: Session 2 OWNS hot-reload callback wiring only. Session 1 OWNS engine/ error classification.
  Session 4 OWNS performance gate fixtures.
- **strategy-service**: Session 2 OWNS hot-reload callback wiring only. Session 4 OWNS grid config refactor.
- **ml-training-service**: Session 2 OWNS hot-reload callback only. Session 4 OWNS grid config refactor.
- **ml-inference-service**: Session 2 OWNS hot-reload callback only. Session 4 OWNS grid config refactor.
- **alerting-service**: Session 2 OWNS hot-reload callback. Session 3 OWNS S2S auth enrollment.
- **unified-trading-api (config routes)**: Session 2 OWNS config publish surface (was standalone config-api; archived).
- **9 API repos** (mock mode/response schema): Session 2 OWNS mock mode completeness and response schema
  standardization. Session 3 OWNS auth middleware standardization on these same repos. No file overlap -- Session 2
  touches mock_data.py/models.py/health endpoints; Session 3 touches middleware/auth.py.
- **client-reporting-api**: Session 2 OWNS mock mode and response schema only. Session 3 OWNS business features (P&L,
  invoicing, DocuSign).
- **unified-trading-api**: Session 2 OWNS mock mode completeness. Session 1 OWNS OpenAPI spec addition.

## Plans Covered

| Plan                              | Phases            | Todos Remaining                  | Reference                                                    |
| --------------------------------- | ----------------- | -------------------------------- | ------------------------------------------------------------ |
| Plan B: Config Hot-Reload         | Phase 0-3         | ~28 todos                        | plans/active/plan_b_config_hot_reload_2026_03_21.md     |
| Plan C: Domain Data API Readiness | Phase 0-3         | ~11 todos                        | plans/active/plan_c_domain_data_api_2026_03_21.md       |
| full_system_audit_resolution      | Phase 3 residuals | ~2 todos (P3-05, P3-06)          | plans/active/full_system_audit_resolution_2026_03_18.md |
| live_batch_alignment_audit        | Phase 6B residual | ~2 todos (QG sweep)              | plans/active/live_batch_alignment_audit_2026_03_18.md   |
| mock_data_rollout                 | Phase 4-5         | ~5 todos                         | plans/active/mock_data_rollout_2026_03_18.md            |
| production_mock_e2e               | Phases 5-6        | ~2 todos (sandbox mode, rollout) | plans/active/production_mock_e2e_plan_d90c8f20.md       |

## What's Already Done (Don't Redo)

- **Plan B infrastructure**: ConfigReloader, DomainConfigReloader, and FieldFilteredCallbackRegistry already exist in
  UTL. instruments-service is the ONLY fully wired service with a working hot-reload callback (reference
  implementation). 20 other services have the plumbing (PubSub subscription, callback registration) but log-only
  callbacks.
- **mock_data_rollout Phases 1-3**: All library foundation done (APY->index converter, SyntheticDataGenerator,
  InstrumentGenerator, get_event_sink factory, cloud_mock_mode deprecation). All 21 seed scripts created. data_mode
  migration complete across 22 repos.
- **full_system_audit_resolution Phases 0-2**: All P0 (10 items), P1 (8 items), and P2 (12 items) are DONE. Only P3-05
  (46 USEI sports browser stubs) and P3-06 (30 UMI adapter stubs) remain.
- **live_batch_alignment Phases 0-5**: All done. Phase 6B QG sweep across ~30 repos remains.
- **production_mock_e2e Phases 1-4**: VCR consolidation, service mock replay, API integration tests, UI smoke tests all
  done. Phase 5 sandbox mode and Phase 6 rollout remain.

## Execution Order

1. **Plan B Phase 0** (PARALLEL, no dependencies):
   - Add RiskDomainConfig, AlertRuleDomainConfig, RateLimitDomainConfig, FeatureFlagDomainConfig, StrategyDomainConfig
     to unified-config-interface
   - QG gate: unified-config-interface

2. **Plan C Phase 0** (PARALLEL with Plan B Phase 0):
   - Audit all 9 API repos + 3 service HTTP APIs for mock mode completeness
   - Audit all 12 APIs for health endpoints

3. **Plan B Phases 1A-1E** (PARALLEL groups, after Phase 0):
   - Group A: market-tick-data, market-data-processing (2 services)
   - Group B: 8 feature services (all PARALLEL)
   - Group C: strategy, execution, trading-agent (3 services)
   - Group D: risk, position-balance, pnl-attribution, alerting, reconciliation (5 services)
   - Group E: ml-training, ml-inference (2 services)
   - QG gate: all 21 services

4. **Plan C Phase 1** (PARALLEL with Plan B Phase 1, after Plan C Phase 0):
   - Fix unified-trading-api mock mode + OpenAPI coverage
   - Fix mock mode gaps in remaining APIs
   - Fix health endpoint gaps

5. **Plan B Phase 2** (after Phase 1):
   - POST /config/publish endpoint on unified-trading-api
   - CLI command: `unified-trading-api config publish --domain risk --file risk-config.yaml`
   - --dry-run flag
   - QG gate: unified-trading-api

6. **Plan C Phase 2** (after Phase 1):
   - Standardize error response shape across all 12 APIs
   - Standardize pagination response shape
   - Add data granularity labelling
   - OpenAPI schema parity verification

7. **Plan B Phase 3** (after Phase 2):
   - Fix 8 config placement violations in market-tick-data-service
   - Fix remaining 4 violations across other services
   - Final QG gate

8. **Closeout items** (PARALLEL, after main work):
   - full_system_audit P3-05: resolve 46 USEI sports browser stubs
   - full_system_audit P3-06: resolve 30 UMI adapter stubs
   - live_batch_alignment Phase 6B QG sweep
   - mock_data_rollout Phase 4: run generate-mock-data.sh, align API seed data
   - mock_data_rollout Phase 5: SIT smoke test, workspace QG
   - production_mock_e2e Phase 5: define CLOUD_SANDBOX_MODE/VITE_SANDBOX_MODE
   - production_mock_e2e Phase 6: rollout checklist

## Key Rules

- `uv pip install` not `pip install`
- Never run pytest directly -- use `bash scripts/quality-gates.sh`
- Do NOT run quickmerge -- only `git add` + `git commit`
- `basedpyright` not `pyright` (with `run_timeout 120`)
- Follow instruments-service as the reference implementation for hot-reload callbacks
- Config swap must be ATOMIC -- no partial updates (especially critical for risk thresholds)
- No `os.getenv()` -- use `UnifiedCloudConfig`
- Shard-level failure isolation -- no `raise` inside per-venue/per-shard loops
- `logger.warning("%s", _err.message)` not `logger.warning(_err.message)`

## CITADEL AUDIT FINDINGS (2026-03-21)

This session needs to address the following honest status corrections:

1. **Config hot-reload: 18/21 services are hollow stubs.** A prior agent session created boilerplate callback files in
   20 services but: (a) 18/21 do NOT call start_domain_config_reloaders() in their startup path, (b) 0/21 services read
   the domain config getters at runtime. The callbacks are dead code. All Phase 1A-1E todos have been reset to NOT DONE.
   Each service needs: (1) add start_domain_config_reloaders() to main.py/app.py, (2) make the service engine consume
   the getter functions instead of reading static config once at startup.

2. **18/21 service mock providers are hollow stubs.** mock_data.py files exist in services but return trivial/empty data
   that does not exercise real service logic. Plan C Phase 1 p1-fix-api-mock-gaps has been reset to NOT DONE. Each mock
   provider must return realistic data matching Pydantic response models.

3. **Plan B Phase 0 (UCfgI schemas) IS genuinely done.** The 5 domain config schemas were correctly added. Do not re-do
   this work.

4. **Plan C Phase 0 (audits) ARE genuinely done.** Health endpoints and mock mode audits were completed. The issue is
   Phase 1 execution quality, not Phase 0 audit accuracy.

## Success Criteria

- [ ] All QGs pass on: unified-config-interface, unified-trading-library, unified-trading-api, all 21 services
- [ ] 5 domain config schemas added to UCfgI (Risk, AlertRule, RateLimit, FeatureFlag, Strategy)
- [ ] All 21 services have working hot-reload callbacks (not log-only stubs)
- [ ] unified-trading-api has POST /config/publish with schema validation and dry-run mode
- [ ] Zero config placement violations across all services
- [ ] All 12 APIs have complete mock mode and consistent response schemas
- [ ] Standard error shape and pagination across all APIs
- [ ] Health/ready endpoints on all 12 APIs/services
- [ ] live_batch_alignment QG sweep complete
- [ ] mock_data_rollout Phase 4-5 complete
- [ ] full_system_audit P3-05 and P3-06 resolved
