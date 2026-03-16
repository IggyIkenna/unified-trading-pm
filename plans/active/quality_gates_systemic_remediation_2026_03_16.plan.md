---
name: ""
overview: ""
todos: []
isProject: false
---

---

name: Quality Gates Systemic Remediation — Full Workspace Audit 2026-03-16 overview: > Full QG audit of all 69 repos (26
libraries/PM/codex, 22 services, 9 APIs, 12 UIs). Results: 28 PASS, 41 FAIL. Identified 6 systemic patterns affecting
40+ repos. This plan tracks all remaining fixes not completed in the audit session.

Phase 1 (Libraries): 18/26 PASS — 5 fixed in-session, 3 remain Phase 2 (Services): 0/22 PASS — all systemic failures
Phase 3 (APIs): 0/9 PASS — mix of systemic + repo-specific Phase 4 (UIs): 10/12 PASS — 3 fixed in-session, 2 remain

Fixed in-session: - unified-sports-execution-interface: refactored \_parse_period_odds() (54→16L) -
unified-api-contracts: split **init**.py (917→896L), venue_constants.py (909→756L) - unified-trading-pm: \_cluster
prefix fix (F841) - unified-trading-library: quality-gates.sh unclosed array fix - deployment-service: added
deployment-api dep - system-integration-tests: relaxed UCI/UAC InstrumentType parity test - client-reporting-ui: removed
unused Rocket import - live-health-monitor-ui: split oversized test describe block - settlement-ui: added test files to
ESLint override isProject: true readiness: code: C0 deployment: D1 business: B1 todos:

# ═══════════════════════════════════════════════════════════════

# SYSTEMIC FIX 1: QG base-service.sh os.environ false positive

# ═══════════════════════════════════════════════════════════════

- id: systemic-os-environ-bootstrap content: >
  - [AGENT] P0. Fix QG base-service.sh to exclude lines with `# config-bootstrap:` annotation from os.environ/os.getenv
    violations. Currently ~18 services and ~6 APIs fail because
    `os.environ.get("LOG_LEVEL", "INFO")  # config-bootstrap: pre-UCC init` is flagged despite being the documented
    approved bootstrap exception. Also exclude `__main__.py` PORT reads (Cloud Run bootstrap pattern). Fix in
    unified-trading-pm/scripts/quality-gates/base-service.sh. status: open priority: P0 notes: | Affected repos (at
    minimum): alerting-service, batch-live-reconciliation-service, features-calendar-service,
    features-commodity-service, features-cross-instrument-service, features-delta-one-service,
    features-multi-timeframe-service, features-onchain-service, features-sports-service, features-volatility-service,
    instruments-service, market-data-processing-service, market-tick-data-service, ml-inference-service,
    ml-training-service, pnl-attribution-service, position-balance-monitor-service, risk-and-exposure-service,
    execution-results-api, market-data-api, ml-inference-api, ml-training-api

# ═══════════════════════════════════════════════════════════════

# SYSTEMIC FIX 2: asyncio.run() in loop

# ═══════════════════════════════════════════════════════════════

- id: systemic-asyncio-run content: >
  - [AGENT] P1. Replace `asyncio.run()` with `asyncio.gather()` in ~15 service CLI entry points. This is a codex
    compliance violation across most services. Each service's `cli/main.py` or `cli/handlers/live_handler.py` uses
    asyncio.run() inside a loop context. status: open priority: P1 notes: | Affected repos: alerting-service
    (cli/main.py), elysium-defi-system (runner/main.py), execution-service (strategy_instructions/gcs_klines.py),
    features-calendar-service, features-delta-one-service, features-multi-timeframe-service, features-onchain-service,
    features-sports-service, features-volatility-service, instruments-service (defi_processor.py),
    market-data-processing-service (live_mode_handler.py), position-balance-monitor-service, risk-and-exposure-service,
    strategy-service (live_handler.py), trading-agent-service (**main**.py)

# ═══════════════════════════════════════════════════════════════

# SYSTEMIC FIX 3: pip-audit CVEs

# ═══════════════════════════════════════════════════════════════

- id: systemic-pip-audit-cves content: >
  - [AGENT] P0. Upgrade pyjwt>=2.12.0 (CVE-2026-32597) and starlette>=0.46.3 (PYSEC-2025-21) across all affected repos.
    pyjwt is transitive (likely from google-auth or unified-cloud-interface). starlette affects
    market-tick-data-service. Pin in upstream library pyproject.toml where possible. status: open priority: P0 notes: |
    pyjwt CVE repos: pnl-attribution-service, position-balance-monitor-service, client-reporting-api, ml-training-api (+
    likely more) starlette CVE: market-tick-data-service

# ═══════════════════════════════════════════════════════════════

# SYSTEMIC FIX 4: RUN_INTEGRATION=false

# ═══════════════════════════════════════════════════════════════

- id: systemic-integration-tests-disabled content: >
  - [AGENT] P1. Many repos have tests/integration/test_library_deps_integration.py that verify internal dep imports, but
    RUN_INTEGRATION=false in their quality-gates.sh means these tests never run during QG. Evaluate whether to enable
    RUN_INTEGRATION=true or move these import-smoke tests to tests/unit/ so they always run. status: open priority: P1
    notes: | Affected repos: all feature services (calendar, commodity, cross-instrument, delta-one, multi-timeframe,
    onchain, sports, volatility), ml-inference-api, ml-training-api, ml-inference-service, ml-training-service

# ═══════════════════════════════════════════════════════════════

# SYSTEMIC FIX 5: Integration test depth — import-only smoke tests

# ═══════════════════════════════════════════════════════════════

- id: systemic-integration-test-depth content: >
  - [HUMAN] P2. Most repos' test_library_deps_integration.py only assert importability (e.g.,
    `assert GracefulShutdownHandler is not None`), not functional behavior. Key untested internal deps across the
    workspace: unified_cloud_interface (get_storage_client, get_pubsub_client, get_secret_client) and
    unified_config_interface (UnifiedCloudConfig). These are the two most commonly untested deps. status: open priority:
    P2 notes: | Worst gaps:
  - batch-live-reconciliation-service: ZERO unified-\* imports in tests
  - elysium-defi-system: ZERO unified-\* imports in tests
  - execution-service: 5 major deps untested (UCI, UDEI, UDC, USEI, UTEI)
  - trading-agent-service: 6/8 internal deps untested
  - risk-and-exposure-service: UCI, UAC, UTL, UCfgI untested

# ═══════════════════════════════════════════════════════════════

# REPO-SPECIFIC: Function/method size violations

# ═══════════════════════════════════════════════════════════════

- id: function-size-umi content: >
  - [AGENT] P2. unified-market-interface: 60+ functions exceed 50-line codex limit across DeFi adapters (uniswap,
    balancer, curve, euler, morpho, aave, lido, instadapp), CeFi/TradFi adapters (deribit, databento, tardis, ibkr),
    factory.py, ws_manager.py. Major refactoring needed — extract adapter-specific helpers. status: open priority: P2
- id: function-size-services content: >
  - [AGENT] P2. Multiple services have severely oversized methods: execution-service: generate_multi_leg_config() 424L,
    TimelineBuilder.build_timeline() 402L, DeribitOrdersMixin.submit_order() 266L; instruments-service:
    CeFiInstrumentProcessor.process_exchange_instruments() 342L, fetch_defi_instruments() 287L,
    SymbolParser.parse_symbol_components() 234L; strategy-service: compute_signal() 128L, generate_defi_signal() 102L,
    30+ methods over 50L; features-delta-one-service: MarketStructure.\_calculate_breakout_reversion() 208L, 27 methods;
    risk-and-exposure-service: PreTradeCheckEngine.\_check_capital_limit() 100L; market-data-processing-service: 24
    methods over 50L; market-tick-data-service: 23 methods over 50L status: open priority: P2

# ═══════════════════════════════════════════════════════════════

# REPO-SPECIFIC: Stale mock tests

# ═══════════════════════════════════════════════════════════════

- id: fix-config-api-tests content: >
  - [AGENT] P1. config-api: 4 unit tests fail because they set CLOUD_MOCK_MODE=true but assert against GCS code path
    that is now bypassed in mock mode (uses MockStateStore instead). Fix: either set CLOUD_MOCK_MODE=false in tests to
    exercise real GCS path with patched storage, or rewrite tests to assert against MockStateStore behavior. Coverage at
    59.9% (needs 70%). status: open priority: P1 notes: | Files: tests/unit/test_config_routes.py Failing:
    test_get_config_returns_stored_config, test_get_config_returns_empty_when_no_config, test_update_config_succeeds,
    test_update_single_key
- id: fix-deployment-api-tests content: >
  - [AGENT] P1. deployment-api: 5 unit tests fail because they mock google.cloud.compute_v1 via sys.modules but code now
    calls unified_cloud_interface.get_compute_engine_client(). Fix: patch
    unified_cloud_interface.get_compute_engine_client (or the local \_build_vm_map_for_service helper) instead of
    sys.modules. One passing test already demonstrates the correct approach. status: open priority: P1 notes: | File:
    tests/unit/test_deployment_processor.py (TestProcessDeploymentsBatchExtended) Failing:
    test_vm_compute_type_triggers_vm_status_path, test_vm_aggregated_list_error_continues,
    test_vm_type_all_shards_terminal_uses_completed_pending_delete,
    test_completed_pending_delete_vm_aggregated_list_error,
    test_completed_pending_delete_vm_with_running_vms_fires_orphan_deletes

# ═══════════════════════════════════════════════════════════════

# REPO-SPECIFIC: Coverage gaps

# ═══════════════════════════════════════════════════════════════

- id: fix-coverage-gaps content: >
  - [AGENT] P1. Three repos below coverage threshold: batch-audit-api: 48.77% < 70% (mock_data.py 0%, mock_state.py 0%,
    logs.py 56%); trading-analytics-api: 69.49% < 70% (fee_schedule_store.py at 23%); strategy-ui: 31.04% < 70% (12 page
    components at 0%) status: open priority: P1

# ═══════════════════════════════════════════════════════════════

# REPO-SPECIFIC: Remaining Phase 1 issues

# ═══════════════════════════════════════════════════════════════

- id: fix-utl-codex content: >
  - [AGENT] P2. unified-trading-library: QG script now runs (syntax fixed in-session) but fails at codex compliance step
    with 1 pre-existing violation. Investigate and fix. status: open priority: P2
- id: fix-pm-typecheck content: >
  - [AGENT] P2. unified-trading-pm: lint fixed in-session but QG still fails at typecheck due to pre-existing
    basedpyright errors in check-data-availability.py and network_evidence_parser.py. status: open priority: P2
- id: fix-execution-analytics-ui content: >
  - [AGENT] P1. execution-analytics-ui: ESLint max-lines-per-function error in src/lib/mock-api.ts — handleDataRoutes()
    is 54 lines (limit 50). Split into sub-handlers. status: open priority: P1

# ═══════════════════════════════════════════════════════════════

# REPO-SPECIFIC: Other codex violations

# ═══════════════════════════════════════════════════════════════

- id: fix-elysium-violations content: >
  - [AGENT] P2. elysium-defi-system: 8 codex violations including non-canonical env keys (THEGRAPH_API_KEY,
    RPC_URL_ETHEREUM not in EnvVars), empty string/dict/list fallbacks, imports inside functions, 8 oversized functions.
    status: open priority: P2
- id: fix-execution-service-violations content: >
  - [AGENT] P2. execution-service: 8 codex violations including 9 broad except Exception, 30+ local schemas, imports
    inside functions, pip-audit vulnerabilities. status: open priority: P2
- id: fix-market-tick-data-violations content: >
  - [AGENT] P2. market-tick-data-service: GCP_PROJECT_ID usage (non-canonical name), 6 bandit B608 SQL injection
    findings, 3 files over 600L, starlette CVE. status: open priority: P2
