---
name: Phase 3 — Service Hardening & Integration
overview: |
  REQUIRES: Phase 1 (T0–T1 green, deployment structure split, system-integration-tests repo) AND
  Phase 2 (T2–T3 green, CI/CD live, event contracts validated) fully complete.

  This phase hardens all 14 T4 services, 3 T5 API services, and 11 T6 UIs in strict DAG pipeline
  order, runs cross-cutting auth + codex work throughout, then closes with a strictly ordered
  post-refactor validation sequence (L2 → L3a → L3b → healthy declaration).

  ## DAG Pipeline Order

  IS (instruments-service) gates ALL other services — it must be green before any other T4 work.
  After IS:
    BATCH B: MTDH → MDPS (2 parallel)
    BATCH C: FCS / FDS / FVS / FOS (4 parallel, after MTDH+MDPS green)
    BATCH D: MLTR / MLIN (2 parallel, after features green)
    BATCH E: STR / EXEC (2 parallel, after ML green)
    BATCH F: PBS / PNL / RES / AS (4 parallel, after EXEC green)
  T5 (ERA / MDA / CRA) starts only after ALL T4 green.
  T6 (11 UIs) starts only after ALL T5 green.

  ## INVARIANT

  Never touch tier N until tier N-1 is FULLY green (D5 full quickmerge with act simulation passes).
  Full quickmerge with act simulation (D5) is the FINAL gate before declaring any tier healthy —
  not --quick, not --unit-only. D5 is the only gate that counts.

  ## Integration Layers

  | Layer | Where | When |
  |-------|-------|------|
  | Layer 0 — Contract alignment | unified-api-contracts, UMI, URDI | Phase 2 T0 STEP B (done) |
  | Layer 1 — Schema robustness  | Per service, tests/unit/test_schema_robustness.py | Folded into each tier STEP B |
  | Layer 2 — Infra verification | deployment-service/scripts/verify_infra.py → /infra/health | Post-deploy sandbox |
  | Layer 3a — Pipeline smoke    | system-integration-tests pytest -m smoke (<5 min) | After L2 passes |
  | Layer 3b — Full E2E          | system-integration-tests pytest -m full_e2e (15–30 min) | After L3a passes |

  Post-refactor sequence is STRICTLY ORDERED: L2 → L3a → L3b → declare healthy.
  Never skip a layer. Never run L3a before L2 passes. Never run L3b before L3a passes.

  ## Cross-references
  - Phase 1: phase1_foundation_prep.plan.md
  - Phase 2: phase2_library_tier_hardening.plan.md
todos:
  - id: t4a-instruments-service
    content: "T4 BATCH A — INSTRUMENTS-SERVICE (IS) [gates all other services]: STEP A: lib-phase4-connectivity-audit (IS as pilot — verify zero os.getenv(API_KEY), hardcoded URLs, direct requests/aiohttp to venues; all connectivity via UDC/UMI/UTEI/URDI); lib-phase7-instruments-service-validation (IS validation gate: uv pip install -e .[dev]; quality-gates.sh; verify imports from unified_trading_services + unified_domain_client; document patterns for remaining 13 services). STEP B: Tests — verify IS import smoke test (python -c 'import instruments_service' exits 0); VCR cassettes via URDI. STEP C: lib-phase6-service-code-adjustment (IS); exec-svc-cross-svc-deps (fix IS service→service dep — IS currently declares instruments-service as dep from market-tick-data-service; fix: extract shared schemas to AC or UIC_INT); lib-phase3-instruments-service-urdi-wire (replace direct exchange REST calls with get_reference_adapter(venue).get_instruments()); qg-upload-events-legacy (IS cloud_instrument_storage.py: UPLOAD_STARTED/UPLOAD_COMPLETED → PERSISTENCE_STARTED/PERSISTENCE_COMPLETED). STEPS D→E: quickmerge --lint-only → --unit-only → --qg-only → --quick → full (D5 = IS green gate)."
    status: pending
  - id: t4b-data-pipeline
    content: "T4 BATCH B — DATA PIPELINE (MTDH=market-tick-data-service, MDPS=market-data-processing-service) [2 agents PARALLEL, after IS green]: STEP A: Deploy structure both repos. STEP B: Tests first (unit tests; batch/live seam tests). STEP C: p0-strategy-live-mode (live seams for MDPS: live_data_source.py Pub/Sub subscriber + broadcast_sink.py Pub/Sub publisher; engine stays mode-agnostic); qg-upload-events-legacy (MDPS: data_sink.py + orchestration_service.py + live_mode_handler.py); lib-phase6-service-code-adjustment (MTDH, MDPS); exec-svc-cross-svc-deps (remove market-tick-data-service→instruments-service dep; extract shared schemas to AC); topology-timestamp-ordering (MTDH published messages); topology-mdps-rolling-window (MDPS ~1yr rolling window in Redis). STEPS D→E: quickmerge --lint-only → --unit-only → --qg-only → --quick → full [2 agents PARALLEL]. Both must pass D5 before Batch C starts."
    status: pending
  - id: t4c-features-layer
    content: "T4 BATCH C — FEATURES LAYER [7 agents PARALLEL, after MTDH+MDPS green]: FCS=features-calendar-service, FDS=features-delta-one-service, FVS=features-volatility-service, FOS=features-onchain-service, FSS=features-sports-service, FCIS=features-cross-instrument-service, FMTS=features-multi-timeframe-service. NOTE: features-cross-instrument-service and features-multi-timeframe-service are in WORKSPACE_MANIFEST_DAG.svg L4 layer (aggregates L3). STEP A: Deploy structure all 7; STEP A naming check: verify none use old names in pyproject.toml/imports/cloudbuild/AR. STEP B: Tests; ic-feature-contracts (UIC_INT feature schemas: FeatureStalenessConfig, FeatureDriftAlert, FeatureParityReport). STEP C: vcr-enhanced-error-remaining (FDS 20, FVS 12, FOS 13 bare excepts → EnhancedError); features-sports-service-full (after USEI v1 ready; P2 priority); lib-phase6-service-code-adjustment (all 7); qg-fds-uncommitted-changes (FDS has uncommitted staged changes — commit them first); topology-features-mdps-event-chain (features trigger on MDPS completion PubSub); FCIS+FMTS: verify they consume from L3 features via GCS/PubSub (not direct import from lower feature services). STEPS D→E: quickmerge --lint-only → --unit-only → --qg-only → --quick → full [7 agents PARALLEL]. All 7 must pass D5 before Batch D."
    status: pending
  - id: t4d-ml-pipeline
    content: "T4 BATCH D — ML PIPELINE (MLTR=ml-training-service, MLIN=ml-inference-service) [2 agents PARALLEL, after features green]: STEP A: Deploy structure. STEP B: Tests; ic-ml-training-contracts (CrossValidationResult, ModelDegradationAlert schemas); ic-portfolio-risk-contracts (PortfolioVaR, PortfolioAllocation). STEP C: p0-ml-bare-except (ml-training-service/cli/main.py:212,218,299 — replace bare except Exception: pass with proper logging+reraise); lib-phase6-service-code-adjustment (MLTR, MLIN); dag-ml-inference-bigquery-to-pubsub (refactor ML inference to use PubSub subscription for live features instead of BigQuery polling); dag-ml-inference-remove-training-dep (remove ml-training-service from ml-inference-service pyproject.toml — both share via unified-ml-interface only); qg-backtest-engine-reportany; ui-ml-training-config-wire (MLTrainingConfig UIC into ml-training-service). STEPS D→E: quickmerge --lint-only → --unit-only → --qg-only → --quick → full [2 agents PARALLEL]. Both must pass D5 before Batch E."
    status: pending
  - id: t4e-strategy-execution
    content: "T4 BATCH E — STRATEGY + EXECUTION + VALIDATION (STR=strategy-service, EXEC=execution-service, SVS=strategy-validation-service) [3 agents PARALLEL, after ML green]: NOTE: strategy-validation-service is in WORKSPACE_MANIFEST_DAG.svg as a service; it validates strategy configs and should be co-deployed with strategy-service. STEP A naming check: strategy-validation-service must use canonical name at all levels (repo, pyproject.toml, imports, AR, cloudbuild). STEP A: Deploy structure. STEP B: Tests; ic-strategy-domain-event-validation (wrap all event constructors in Pydantic model_validate); p0-cdc-tests (consumer tests for strategy+execution). STEP C: p0-strategy-live-mode (strategy-service live mode seams: live_data_source.py Pub/Sub subscriber + broadcast_sink.py Pub/Sub publisher); lib-phase6-service-code-adjustment; qg-strategy-service-gitignore (add .coverage* + logs/**/*.jsonl to .gitignore; unset ENVIRONMENT before quickmerge); qg-strategy-service-print-pdf (replace print() in export_to_pdf.py with logger.info()); qg-strategy-service-tier2-dep (identify T2 import, use public top-level API only); qg-strategy-domain-adapter-type (CloudTarget type mismatch — fix root cause); qg-exec-import-error-remaining (25 remaining except ImportError in execution-service production code → fail-loud); qg-exec-services-codex-18 (18 codex violations — fix after qg-pip-audit-exec-services); qg-pip-audit-exec-services (install pip-audit in execution-service + all service venvs); qg-exec-services-smoke-import (update smoke test to use get_storage_client() from unified-cloud-interface); qg-central-element-test-code (replace central-element-323112 with test-project in 5 test files); vcr-enhanced-error-high-priority (execution-service 201 bare excepts); quality-importerror-fallbacks (execution-service); quality-large-file-splits (engine.py 2826L — split by SRP); quality-type-ignore-arch-violations (67 ARCHITECTURAL_VIOLATION suppressions); ci-arch-violations-fix; exec-svc-cross-svc-deps (remove execution-service service→service deps: market-tick-data-service, risk-and-exposure-service, instruments-service); topology-execution-order-lifecycle (full order lifecycle PubSub); topology-t1-execution-recon (execution T+1 recon). SVS STEP C: lib-phase6-service-code-adjustment (SVS); ic-strategy-domain-event-validation (SVS: wrap all event constructors in Pydantic model_validate); verify SVS only imports from strategy-service via HTTP/PubSub — not direct Python import (no service→service Python deps). STEPS D→E: quickmerge --lint-only → --unit-only → --qg-only → --quick → full [3 agents PARALLEL]. All 3 must pass D5 before Batch F."
    status: pending
  - id: t4f-monitoring-pipeline
    content: "T4 BATCH F — MONITORING PIPELINE (PBS=position-balance-monitor-service, PNL=pnl-attribution-service, RES=risk-and-exposure-service, AS=alerting-service) [4 agents PARALLEL, after EXEC green]: STEP A: Deploy structure. STEP B: Tests; ic-pnl-breakdown-schema (PnLBreakdown schema); ic-greeks-position-schema (GreeksExposure schema); ic-circuit-breaker-schema (CircuitBreakerEvent schema); ic-eod-settlement-contract (EODSettlementTrigger + EOD_SETTLEMENT PubSub topic); ic-risk-service-complete (risk-and-exposure-service full implementation: VaR, portfolio Greeks, DeFi LTV, circuit breaker). STEP C: ic-pnl-attribution-complete (6-dimension PnL breakdown: delta/funding/basis/interest rate/Greeks/mark-to-market); obs-metrics-aggregator-api (GET /api/system/metrics in alerting-service: fan-out to Prometheus endpoints, cache 15s); lib-phase6-service-code-adjustment (monitoring); qg-asyncio-run-audit (fix asyncio.run() inside async def in monitoring services — replace with await); topology-circuit-breaker-impl (alerting-service publish CIRCUIT_BREAKER_OPEN to circuit-breaker-commands PubSub); topology-kill-switch-propagation (deployment-api /kill-switch activate → PubSub → execution-service + strategy-service); topology-pbm-exchange-bootstrap (PBM exchange REST on startup). STEPS D→E: quickmerge --lint-only → --unit-only → --qg-only → --quick → full [4 agents PARALLEL]. All 4 must pass D5 before T5 starts."
    status: pending
  - id: t5-api-services
    content: "T5 — API SERVICES (ERA=execution-results-api, MDA=market-data-api, CRA=client-reporting-api) [3 agents PARALLEL, REQUIRES all T4 green]: STEP A: dag-orphan-repos-manifest (ensure all 3 in manifest with correct type/tier — already done 2026-02-28 ✅); dag-api-services-cluster (confirm standalone repos, FastAPI only, no engine code). STEP B: Tests; p0-cdc-tests (CDC tests for ERA/MDA/CRA). STEP C: p0-exec-results-api-types (replace all dict[str,Any] at API boundaries with TypedDict/Pydantic); vcr-execution-results-api-uic (full UIC adoption: EnhancedError on all exception handlers, lifecycle log_events, typed Pydantic response models); p0-ui-sse (add SSE endpoints via sse-starlette to ERA + health-monitor-api; wire live-health-monitor-ui and trading-analytics-ui as SSE clients); ssot-service-to-service-auth-implement (Google OAuth SA tokens for inter-service calls); auth-credentials-registry (expand to system-wide coverage of all API services); obs-health-probes (add /health + /readiness to all API services). STEPS D→E: quickmerge --lint-only → --unit-only → --qg-only → --quick → full [3 agents PARALLEL]. All 3 must pass D5 before T6 starts."
    status: pending
  - id: t6-ui-setup
    content: "T6 SETUP — UI LOCAL DEV [1 agent, REQUIRES all T5 green]: ui-local-dev-setup: add .env.local.example to all 11 UI repos with correct VITE_API_URL + VITE_ENV=local. Port assignments: 8001=deployment-api, 8002=execution-results-api, 8003=client-reporting-api, 8004=market-data-api. See UI-DEPENDENCY-MATRIX.md for full port table. Must complete before T6 implementation batch."
    status: pending
  - id: t6-ui-implementation
    content: "T6 — UIs [11 agents PARALLEL, after setup]: Agent 1: auth-trading-analytics-ui (Google OAuth TRADER + /positions /pnl /executions /risk /orderbook /latency); Agent 2: ui-orderbook-viz (OrderBookDepthChart, OrderBookTable, TradeTimeline, SSE from market-data-api) + ui-latency-plots (ExecutionLatencyHistogram, SlippageScatter, P50/P95/P99); Agent 3: ui-system-health-page (ServiceStatusGrid, CPUMemoryTimeSeries, PubSubLagBars, DLQDepthBadges, Alerts SSE); Agent 4: auth-onboarding-ui-gaps (AMLScreening, FeeStructureConfig, HWMInitialization, APIKeyManagement, AuditLog, VenueOnboarding, StrategyOnboarding — Google OAuth ADMIN) + auth-onboarding-ui-complete (API key CRUD with SM backend, connection test, strategy-account mapping); Agent 5: auth-manual-trading-consolidate (live-health-monitor-ui; add submitted_by OAuth, reason, cancel/amend endpoints); Agent 6: auth-config-promotion-workflow (BacktestGridResult → StrategyConfig promotion; POST /api/v1/config/promote; ConfigStore; deployed_by from OAuth); Agent 7: auth-ml-training-ui (build ml-training-ui: /experiments, /experiments/:runId/deploy, /models, /training-runs — Google OAuth; CANONICAL NAME IS ml-training-ui per WORKSPACE_MANIFEST_DAG.svg — old name ml-training-ui is WRONG at all levels); Agent 8: auth-ai-report-summaries (add ai_summary.py: Anthropic claude-3-5-haiku for executive summaries; API key via SM anthropic-api-key); Agent 9: deployment-ui-implement (full implementation after T5 split: orchestrator run status dashboard SSE, Cloud Build trigger buttons, shard calculator viz, Cloud Run health panel, IBKR Gateway config UI); Agent 10: obs-grafana-export (export Grafana dashboards trading-overview.json + system-health.json) + obs-prometheus-codex (create 03-observability/prometheus-metrics.md: metric catalog, alert rules, triage guide); Agent 11: ui-skeleton-assess (assess execution-analytics-ui [CANONICAL — was execution-analytics-ui, old name is WRONG everywhere], client-reporting-ui, settlement-ui, logs-dashboard-ui, batch-audit-ui — what data schemas they need vs what's available; scope SSE integration; RENAME any repo/package/import/AR/cloudbuild still using old execution-analytics-ui name). STEPS D→E: quickmerge --unit-only then full [batched in groups of 4]."
    status: pending
  - id: p3-cross-cutting-auth
    content: "AUTH + CREDENTIALS (starts at T4, completes across tiers as services green): auth-credentials-registry (system-wide unified-trading-pm/credentials-registry.yaml covering ALL services + secret types); auth-setup-secret-script (generalize setup-secret-manager.sh → unified-trading-pm/scripts/setup_secret.sh); auth-secret-manager-naming (enforce canonical SM naming: exec-{client}-{venue}-{account_type}); auth-three-tranche-data-wiring (tranche_router.py: A=manual CSV, B=SM exec-odum-{venue}-{account_type}, C=PBS+PNL APIs); ssot-checklist-auth-alignment (add auth_setup block to all 19 deployment checklists); ssot-success-criteria-update (update checklist success_criteria for new arch goals); auth-ibkr-corp-actions (P1: URDI IBKR CorporateAction adapter; PENDING_CASSETTE_AWAITING_AUTH); auth-sports-migration-batch1 (auth status fixes in endpoint_registry + UIC sports canonical schemas); auth-sports-migration-batch2 (sports UMI adapters completion)."
    status: pending
  - id: p3-cross-cutting-codex
    content: "CODEX + SSOT DOCS (update as each tier completes): codex-service-pair-flows-doc (DONE ✅ — 08-workflows/service-pair-flows.md created); codex-quality-gates-aws-parity (add AWS CodeBuild parity section to quality-gates.md); codex-s2s-auth-phase0-impl (implement Phase 0 SA OAuth; auth_smoke_test.py validates SA token env var per service; update 07-security/service-to-service-auth.md). Topology tasks: topology-ssot-index-update (DONE ✅), topology-venue-replay-unified-api-contracts, topology-kill-switch-propagation (in T4 Batch F), topology-circuit-breaker-impl (in T4 Batch F), topology-with-retry-decorator (implement @with_retry in UTS — T1), topology-timestamp-ordering (MTDH published messages — T4 Batch B), topology-mdps-rolling-window (MDPS ~1yr rolling window in Redis — T4 Batch B), topology-t1-strategy-recon (strategy-validation-service), topology-t1-execution-recon (execution T+1 recon), topology-pbm-exchange-bootstrap (PBM exchange REST on startup), topology-features-mdps-event-chain (features trigger on MDPS completion PubSub), topology-execution-order-lifecycle (full order lifecycle PubSub). Observability: obs-health-probes (add /health + /readiness to all API services), obs-audit-trail-enforcement, obs-correlation-id-propagation (end-to-end correlation_id), obs-pre-crash-checkpoint (pre-crash state dump at 85% memory), obs-compliance-reporting-wiring (MiFID/FCA reporting)."
    status: pending
  - id: p3-final-qg-sweep
    content: "FINAL QG SWEEP (after all tiers T0–T6 green, before post-refactor): p0-reportany-error-all-repos [10 agents] (upgrade reportAny from 'warning' to 'error' in ALL repos; fix ALL Any-type violations); vcr-quality-gates (run QG on unified-api-contracts, UMI, URDI — verify all new VCR tests pass); ci-per-repo-status-run (run QG on all 30 repos; record final pass/fail + coverage % in manifest ci_status); ci-arch-violations-fix (any remaining ARCHITECTURAL_VIOLATION suppressions); qg-type-ignore-audit (reduce to <10 documented exceptions); qg-venue-name-canonicalization (binance/okx/deribit/bybit → UCI venue constants)."
    status: pending
  - id: p3-integration-layer1
    content: "INTEGRATION LAYER 1 — SCHEMA ROBUSTNESS (per service, folded into each tier's STEP B): Each repo tests/unit/test_schema_robustness.py — required field missing → ValidationError; optional absent → passes; wrong type → fails. Written as part of STEP B at each tier for every repo that defines or consumes Pydantic schemas. No separate todos — folded into T4/T5/T6 STEP B work. Note: Layer 0 ran in Phase 2 T0 STEP B."
    status: pending
  - id: p3-integration-layer2
    content: "INTEGRATION LAYER 2 — INFRASTRUCTURE VERIFICATION (post-deploy, NOT in quickmerge): Add verify_infra.py to deployment-service/scripts/ (DONE in Phase 1 integration-layer2-infra-verify). Exposed as GET /infra/health in deployment-api. Tests: GCS buckets exist + IAM, PubSub topics + subscriptions, Secret Manager entries. Runs during post-refactor sandbox deploy. REQUIRES: deployment-service extracted (Phase 1 STREAM B) + all tiers green."
    status: pending
  - id: p3-integration-layer3
    content: "INTEGRATION LAYER 3 — PIPELINE SMOKE + E2E (system-integration-tests/ repo, post-deploy): Layer 3a (smoke, @pytest.mark.smoke, <5 min): happy path, one date, one venue, one instrument through full pipeline. Layer 3b (full, @pytest.mark.full_e2e, 15–30 min): corner cases, auth, multi-date, perf baseline. Sequential: 3a must pass before 3b. Zero Python imports from services — HTTP/GCS/PubSub interaction only. REQUIRES: system-integration-tests repo (Phase 1 STREAM B) + ALL tiers green + Layer 2 passes."
    status: pending
  - id: p3-postrefactor-sandbox-deploy
    content: "POST-REFACTOR STEP 1 — SANDBOX DEPLOY: REQUIRES all T0–T6 green + final QG sweep done. postrefactor-sandbox-deploy — deploy all T4 services to GCP sandbox project via deployment-service CLI. deployment-api must start cleanly on Cloud Run. Do not proceed to Layer 2 until deploy is stable."
    status: pending
  - id: p3-postrefactor-layer2-run
    content: "POST-REFACTOR STEP 2 — INFRASTRUCTURE VERIFY: REQUIRES sandbox deploy complete. postrefactor-layer2-run — run GET /infra/health on deployment-api. All checks must pass (buckets, topics, IAM, secrets). If Layer 2 fails: fix infrastructure before proceeding. DO NOT skip to Layer 3."
    status: pending
  - id: p3-postrefactor-layer3a-run
    content: "POST-REFACTOR STEP 3 — PIPELINE SMOKE: REQUIRES Layer 2 passes. postrefactor-layer3a-run — run pytest -m smoke in system-integration-tests. Happy path: one date, one venue, one instrument through full pipeline. If 3a fails: debug wire mismatches, fix, re-run. Do NOT proceed to 3b until 3a is green."
    status: pending
  - id: p3-postrefactor-layer3b-run
    content: "POST-REFACTOR STEP 4 — FULL E2E: REQUIRES Layer 3a passes. postrefactor-layer3b-run — run pytest -m full_e2e in system-integration-tests. Corner cases, auth flows, multi-date, performance baseline. If 3b fails: investigate, fix, re-run. Do NOT declare healthy until 3b is fully green."
    status: pending
  - id: p3-postrefactor-declare-healthy
    content: "POST-REFACTOR STEP 5 — DECLARE HEALTHY: REQUIRES all 4 layers pass (L2 + L3a + L3b + final QG sweep). deployment-api marks deployment status as 'healthy'. Merge staging → main. GitHub Action bumps all versions to 1.0.0 (first stable). This is the final act of Phase 3. Full quickmerge with act simulation (D5) is the FINAL gate — not --quick alone."
    status: pending
isProject: true
---

## NAMING CHANGE MANDATE — Zero Technical Debt

> **SSOT: `unified-trading-pm/WORKSPACE_MANIFEST_DAG.svg`** (57 repos, 11 levels).
> Any service, API, or UI name that does not match the SVG is wrong and must be fixed at ALL levels.

At every STEP A (connectivity audit) for each service/API/UI, verify no old name appears in:

| Level                              | Check                                                                        |
| ---------------------------------- | ---------------------------------------------------------------------------- |
| **Repo GitHub name**               | Must match `workspace-manifest.json` `name` field                            |
| `**pyproject.toml` `name`\*\*      | Must match canonical name                                                    |
| **Python package dir**             | `market_tick_data_handler/` is wrong; `market_tick_data_service/` is correct |
| **All imports in this repo**       | `rg old_name .` — must return zero hits after fix                            |
| **All imports in dependent repos** | Every consumer must be updated in same `--dep-branch` cascade                |
| `**cloudbuild.yaml` image tag\*\*  | `gcr.io/…/<service-name>:$TAG` must use canonical name                       |
| **Cloud Build trigger**            | Name must match repo name                                                    |
| **Artifact Registry**              | Package name must match canonical name                                       |
| `**runtime-topology.yaml`\*\*      | Service name in topology config must match                                   |
| `**workspace-manifest.json`\*\*    | `name`, `github_url`, `artifact_registry_url`, `package_name`                |
| **Deployment checklists**          | `unified-trading-deployment-v3/configs/checklist.*.yaml`                     |
| **Cursor rules + codex docs**      | `rg` for old names; fix every hit                                            |
| **PubSub topic names**             | Any topic named after old service name must be renamed                       |
| **Secret Manager**                 | Any secret keyed to old service name                                         |

### Known Renames Still Pending Code-Level Fix at Phase 3 Start

| Old                                                                   | Canonical  | Fix where         |
| --------------------------------------------------------------------- | ---------- | ----------------- |
| `market-tick-data-handler` → `**market-tick-data-service`\*\*         | All levels | T4 Batch B STEP A |
| `client-reporting-api` → `**client-reporting-api`\*\*                 | All levels | T5 STEP A         |
| `alerting-service` → `**alerting-service`\*\*                         | All levels | T4 Batch F STEP A |
| `position-balance-monitor` → `**position-balance-monitor-service`\*\* | All levels | T4 Batch F STEP A |
| `ml-training-ui` → `**ml-training-ui**`                               | All levels | T6 Agent 7        |
| `execution-analytics-ui` → `**execution-analytics-ui**`               | All levels | T6 Agent 11       |

### NEVER

- Leave old name in any file as alias, comment, or fallback
- Rename only the Python package dir without renaming the repo, AR package, and trigger
- Merge a service PR without verifying `rg old_name .` returns zero hits

---

## Phase 3 — Service Hardening & Integration Testing

**REQUIRES:** Phase 1 complete (T0–T1 green, deployment structure split, system-integration-tests repo, deployment-service extracted) AND Phase 2 complete (T2–T3 green, CI/CD live, event contracts validated, all library tiers passing D5).

---

### DAG Pipeline Order

IS (instruments-service) is the single gate for all T4 work. No other service may start until IS passes D5 (full quickmerge with act simulation).

```
T4 BATCH A:  IS
T4 BATCH B:  MTDH  MDPS                           (parallel, after IS)
T4 BATCH C:  FCS  FDS  FVS  FOS  FSS  FCIS  FMTS  (parallel, after BATCH B)
             FCS=features-calendar-service
             FDS=features-delta-one-service
             FVS=features-volatility-service
             FOS=features-onchain-service
             FSS=features-sports-service
             FCIS=features-cross-instrument-service   [in SVG L4]
             FMTS=features-multi-timeframe-service    [in SVG L4]
T4 BATCH D:  MLTR  MLIN                           (parallel, after BATCH C)
T4 BATCH E:  STR   EXEC  SVS                      (parallel, after BATCH D)
             SVS=strategy-validation-service
T4 BATCH F:  PBS   PNL   RES  AS                  (parallel, after BATCH E)
T5:          ERA   MDA   CRA                       (parallel, after ALL T4)
T6:          11 UIs                                (parallel, after ALL T5)
             (batch-audit-ui, client-reporting-ui, deployment-ui,
              execution-analytics-ui, live-health-monitor-ui, logs-dashboard-ui,
              ml-training-ui, onboarding-ui, settlement-ui, strategy-ui,
              trading-analytics-ui)
```

> **Total T4 services: 19** (per `WORKSPACE_MANIFEST_DAG.svg` — not 14; the plan previously omitted FCIS, FMTS, FSS, SVS).

---

### INVARIANT

> Never touch tier N until tier N-1 is FULLY green (D5 passes).
> Full quickmerge with act simulation is the FINAL gate — `--quick` alone is not sufficient.

---

### Per-Service Step Pattern

Every service follows the same 5-step progression:

- **STEP A** — Connectivity audit + validation gate (import smoke test, QG, pattern documentation)
- **STEP B** — Tests first: unit + schema robustness (Layer 1) + batch/live seam tests
- **STEP C** — Code adjustments: service code adjustment, event naming fixes, cross-service dep removal, topology wiring
- **STEP D** — Quickmerge progression: `--lint-only` → `--unit-only` → `--qg-only` → `--quick` → full
- **STEP E (D5)** — Full quickmerge with act simulation = tier green gate

---

### Integration Layers Summary

| Layer                        | Scope                                 | Trigger             | Owner                        |
| ---------------------------- | ------------------------------------- | ------------------- | ---------------------------- |
| Layer 0 — Contract alignment | unified-api-contracts, UMI, URDI      | Phase 2 T0 STEP B   | Phase 2                      |
| Layer 1 — Schema robustness  | Per-service test_schema_robustness.py | Each tier STEP B    | Folded into T4/T5/T6         |
| Layer 2 — Infra verification | GCS, PubSub, SM, IAM                  | Post-sandbox-deploy | deployment-api /infra/health |
| Layer 3a — Pipeline smoke    | system-integration-tests -m smoke     | After L2 passes     | <5 min                       |
| Layer 3b — Full E2E          | system-integration-tests -m full_e2e  | After L3a passes    | 15–30 min                    |

---

### Post-Refactor Sequence (strictly ordered)

```
ALL TIERS GREEN (T0–T6, D5 each)
  → Final QG sweep (reportAny + arch violations + venue names)
    → STEP 1: Sandbox deploy
      → STEP 2: Layer 2 infra verify (/infra/health)
        → STEP 3: Layer 3a smoke (pytest -m smoke)
          → STEP 4: Layer 3b full E2E (pytest -m full_e2e)
            → STEP 5: Declare healthy → merge staging → main → v1.0.0
```

If any step fails: fix and re-run **that step**. Never skip forward.

---

### Cross-references

- [Phase 1](phase1_foundation_prep.plan.md) — T0–T1, deployment structure, system-integration-tests repo
- [Phase 2](phase2_library_tier_hardening.plan.md) — T2–T3, CI/CD, event contracts
