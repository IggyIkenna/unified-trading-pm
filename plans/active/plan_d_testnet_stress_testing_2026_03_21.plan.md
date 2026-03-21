---
name: plan-d-testnet-stress-testing
overview: |
  Testnet and stress testing infrastructure. Seed determinism (seed=42), scenario expansion (BAD_SCHEMA, ERROR_STORM,
  FLASH_CRASH), error code stress tests (all 18 canonical + 13 DeFi codes), performance regression gates
  (PerformanceGate/MemoryGate in CI), UI scenario selector panel, synthetic load generator (45->1K->10K instruments),
  external testnet (testnet.odum.io), and error classification re-audit (aave_plasma bug, missing venue maps, QG
  enforcement). Goal: no meaningful difference between testing mock and live.
type: mixed
epic: epic-code-completion
status: active
locked_by: live-defi-rollout
locked_since: 2026-03-21

completion_gates:
  code: C5
  deployment: D3
  business: B3

repo_gates:
  - repo: unified-internal-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-system-ui
    code: C0
    deployment: none
    business: none
  - repo: execution-service
    code: C0
    deployment: none
    business: none
  - repo: system-integration-tests
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

depends_on:
  - plan-c-domain-data-api

todos:
  # ── Phase 0: Seed Hardening ── PARALLEL ──────────────────────────────────
  - id: p0-audit-seed-determinism
    content: |
      - [ ] [AGENT] P0. Audit all seed_mock_data.py scripts (13 services) for determinism. Each must accept --seed flag (default=42), pass it to random.seed() and numpy random generator. Verify: running seed twice produces byte-identical output. Files: instruments-service, market-data-processing-service, features-delta-one-service, features-sports-service, features-multi-timeframe-service, features-cross-instrument-service, execution-service, strategy-service, alerting-service, pnl-attribution-service, position-balance-monitor-service, risk-and-exposure-service, trading-agent-service, ml-training-service, ml-inference-service. Output: manifest of which scripts already have seed support and which need fixing.
    status: todo
    note: ""
  - id: p0-fix-seed-scripts
    content: |
      - [ ] [AGENT] P0. Fix all seed scripts identified in p0-audit-seed-determinism that lack seed=42 determinism. Add --seed CLI arg, wire into all RNG sources (random, numpy, uuid generation). Verify: `python seed_mock_data.py --seed 42 | md5` produces same hash on consecutive runs.
    status: todo
    note: "blocked_by p0-audit-seed-determinism within phase"
  - id: p0-document-seed-vs-logic
    content: |
      - [ ] [AGENT] P1. Document which services need seeding (data generators) vs which use real logic (execution-service order matching, strategy-service signal generation). Add table to unified-trading-codex/08-workflows/local-dev.md.
    status: todo
    note: ""

  # ── Phase 1: Scenario Infrastructure ── SEQUENTIAL after Phase 0 ────────
  - id: p1-add-new-scenarios
    content: |
      - [ ] [AGENT] P0. Extend MockScenario enum in UIC modes.py with: BAD_SCHEMA, ERROR_STORM, FLASH_CRASH, HIGH_LATENCY. Add corresponding YAML configs in unified_internal_contracts/testing/scenarios/. BAD_SCHEMA: 10% of records have corrupted fields. ERROR_STORM: every adapter returns errors for 30s bursts. FLASH_CRASH: 50% price drop in 5 minutes then recovery. HIGH_LATENCY: 2-5s artificial delay on all responses.
    status: todo
    note: ""
  - id: p1-scenario-config-api
    content: |
      - [ ] [AGENT] P0. Add POST /api/v1/scenarios/activate endpoint to config-api (or system-admin API route in BFF). Accepts {scenario: MockScenario, seed: int}. Updates MOCK_SCENARIO env var for all running services via shared state in MockStateStore. Only available when CLOUD_MOCK_MODE=true.
    status: todo
    note: "Depends on Plan C BFF being available"
  - id: p1-scenario-propagation
    content: |
      - [ ] [AGENT] P0. Wire scenario change propagation: when scenario is activated via API, all services with seed_mock_data.py re-seed with the new scenario config. Use PubSub topic (via UCI get_pubsub_client) to broadcast scenario changes. In mock mode, use emulator.
    status: todo
    note: ""
  - id: p1-sit-scenario-tests
    content: |
      - [ ] [AGENT] P1. Add SIT tests for scenario switching: test_mock_scenarios.py already exists in system-integration-tests. Extend with tests for BAD_SCHEMA (verify error handling), ERROR_STORM (verify circuit breakers fire), FLASH_CRASH (verify alerts trigger). Each test activates scenario via API, then asserts downstream effects.
    status: todo
    note: ""

  # ── Phase 2: Error Code Stress Testing ── PARALLEL with Phase 1 ─────────
  - id: p2-error-reaudit-venue-map
    content: |
      - [ ] [AGENT] P0. Re-audit VENUE_ERROR_MAP completeness. Current state: cefi.py has binance maps, defi.py has balancer/aave_v3/uniswap_v3, sports.py/tradfi.py/onchain_perps.py exist. Cross-reference against VENUE_REGISTRY (33 venues: 9 CeFi + 9 TradFi + 14 DeFi + 1 Onchain Perps) in UMI factory.py. Identify all venues with adapters but missing from VENUE_ERROR_MAP. Output: gap manifest with venue name, adapter file, and count of error codes needing classification.
    status: todo
    note: ""
  - id: p2-fix-aave-plasma-bug
    content: |
      - [ ] [AGENT] P0. Fix aave_plasma missing from VENUE_ERROR_MAP. UTL instrument_date_filter.py references aave_plasma (available_from: 2024-03-01) but VENUE_ERRORS_DEFI only has aave_v3. Add aave_plasma entry to defi.py VENUE_ERRORS_DEFI with same error classifications as aave_v3 (they share the same Aave V3 protocol).
    status: todo
    note: ""
  - id: p2-add-missing-venue-maps
    content: |
      - [ ] [AGENT] P0. Add VENUE_ERROR_MAP entries for all active adapters identified in p2-error-reaudit-venue-map. Priority: venues with URDI/UTEI adapters that call classify_venue_error(). Each venue needs at minimum: rate-limit, auth-failure, timeout, and unknown-error classifications. Use ErrorAction.RETRY for transient, ErrorAction.FAIL for permanent.
    status: todo
    note: "blocked_by p2-error-reaudit-venue-map within phase"
  - id: p2-wire-classify-into-execution
    content: |
      - [ ] [AGENT] P0. Wire classify_venue_error() into execution-service error routing. Execution-service should call classify_venue_error(venue, raw_error_code) on every adapter error, then route based on ErrorAction: RETRY = re-queue with backoff, FAIL = dead-letter + alert, SKIP = log + continue. Verify: execution-service imports classify_venue_error from UAC (not self-declared).
    status: todo
    note: ""
  - id: p2-error-storm-scenario
    content: |
      - [ ] [AGENT] P0. Create ERROR_STORM scenario test suite. Exercises all 18 canonical error codes (from VENUE_ERROR_MAP across cefi/defi/tradfi/sports/onchain_perps/infra) + all 13 DefiErrorCode values through the pipeline. Test: inject each error code via mock adapter, verify classify_venue_error() returns correct classification, verify execution-service routes correctly (RETRY/FAIL/SKIP), verify alerting-service emits correct alert type.
    status: todo
    note: ""
  - id: p2-qg-venue-error-coverage
    content: |
      - [ ] [AGENT] P1. Add QG check to UAC quality-gates.sh: every adapter that calls classify_venue_error() must have its venue present in VENUE_ERROR_MAP. Script: grep all classify_venue_error("venue_name" calls across workspace, extract venue names, verify each exists as a key in VENUE_ERROR_MAP. Fail QG if any venue is missing.
    status: todo
    note: ""

  # ── Phase 3: Performance Regression Gates ── PARALLEL with Phase 1 ──────
  - id: p3-perf-gate-ci-integration
    content: |
      - [ ] [AGENT] P0. Integrate PerformanceGate + MemoryGate from UTL into CI for critical services. Services: execution-service (P99 < 50ms order routing), market-data-processing-service (P99 < 100ms tick processing), strategy-service (P99 < 200ms signal generation), features-delta-one-service (P99 < 500ms feature calc). Add pytest fixtures that create PerformanceGate with threshold, run operation N times, assert PerformanceGateResult.passed. Add to each service's quality-gates.sh.
    status: todo
    note: ""
  - id: p3-memory-gate-ci
    content: |
      - [ ] [AGENT] P0. Add MemoryGate tests for services with known memory pressure: market-data-processing-service (< 512MB for 10K ticks), features-delta-one-service (< 256MB for feature calc batch), ml-inference-service (< 1GB for model load + inference). Use MemoryGate from UTL. Fail CI if memory exceeds threshold.
    status: todo
    note: ""
  - id: p3-perf-baselines
    content: |
      - [ ] [AGENT] P1. Establish performance baselines for all services. Run PerformanceGate benchmarks with seed=42 data, record P50/P95/P99 latencies, store in unified-trading-pm/configs/performance-baselines.json. CI compares against baselines, fails on >20% regression.
    status: todo
    note: ""
  - id: p3-perf-dashboard
    content: |
      - [ ] [AGENT] P2. Add performance trend page to unified-trading-system-ui admin section. Shows historical P99 latencies per service from CI runs. Visual regression indicator (green/yellow/red). Data source: performance-baselines.json committed to PM.
    status: todo
    note: "Depends on Plan C BFF for API routing"

  # ── Phase 4: UI Scenario Panel ── SEQUENTIAL after Phase 1 ──────────────
  - id: p4-scenario-selector-ui
    content: |
      - [ ] [AGENT] P0. Add scenario selector dropdown to admin/devops page in unified-trading-system-ui. Dropdown lists all MockScenario values (NORMAL, HEAVY, LIGHT, BIG_RANGES, BUST, NO_SYSTEM_OVERLOAD, MISSING_DATA, DELAYED_DATA, BAD_SCHEMA, ERROR_STORM, FLASH_CRASH, HIGH_LATENCY). Selection calls POST /api/v1/scenarios/activate via BFF. Only visible when VITE_MOCK_API=true.
    status: todo
    note: "Depends on p1-scenario-config-api and Plan C BFF"
  - id: p4-scenario-status-indicator
    content: |
      - [ ] [AGENT] P0. Add current scenario indicator to UI header/status bar. Shows active scenario name + seed number. Color-coded: NORMAL=green, BUST/FLASH_CRASH=red, ERROR_STORM=orange, others=yellow. Updates via WebSocket when scenario changes (depends on Plan C WebSocket).
    status: todo
    note: ""
  - id: p4-scenario-realtime-switch
    content: |
      - [ ] [AGENT] P1. Real-time scenario switching without page reload. When scenario changes via dropdown, WebSocket pushes new scenario to all connected clients. SyntheticDataGenerator adjusts tick patterns immediately. UI components react to scenario change event (e.g., trading page shows price crash animation during FLASH_CRASH).
    status: todo
    note: ""
  - id: p4-custom-scenario-builder
    content: |
      - [ ] [AGENT] P2. Add custom scenario builder modal on admin page. Adjustable parameters: volatility multiplier (0.1x-10x), volume multiplier (0.1x-10x), missing data rate (0-50%), error injection rate (0-100%), instrument count (45-10000), tick frequency (0.1-100 Hz). Saves as custom ScenarioConfig YAML, selectable in dropdown.
    status: todo
    note: ""

  # ── Phase 5: Load Testing Infrastructure ── SEQUENTIAL after Phase 3 ────
  - id: p5-synthetic-load-generator
    content: |
      - [ ] [AGENT] P0. Create synthetic load generator script in unified-trading-pm/scripts/load-testing/. Configurable: instrument count (45, 1000, 5000, 10000), tick rate per instrument (1/s, 10/s), concurrent users (1, 10, 50), scenario (any MockScenario). Uses SyntheticDataGenerator from UIC with seed=42. Outputs: throughput (msgs/s), P50/P95/P99 latency, error rate, memory usage.
    status: todo
    note: ""
  - id: p5-instrument-scaling
    content: |
      - [ ] [AGENT] P0. Test instrument scaling path: 45 (current mock) -> 1000 -> 5000 -> 10000 instruments. Verify: instruments-service seed_mock_data.py can generate N instruments deterministically. market-data-processing-service can process ticks for N instruments within P99 threshold. features-delta-one-service can compute features for N instruments within P99 threshold. Document: at what N does each service exceed its PerformanceGate threshold.
    status: todo
    note: ""
  - id: p5-response-time-baselines
    content: |
      - [ ] [AGENT] P1. Establish response time baselines for all API endpoints under load. Use load generator with 1000 instruments, 10 concurrent users. Record: GET /api/instruments (< 200ms), GET /api/positions (< 100ms), GET /api/market-data/ticks (< 50ms), POST /api/execution/orders (< 100ms). Store baselines in PM configs. CI load test runs weekly, alerts on >20% regression.
    status: todo
    note: ""
  - id: p5-stress-test-ci
    content: |
      - [ ] [AGENT] P2. Add stress test CI job (weekly schedule, not on every push). Runs load generator with 5000 instruments, HEAVY scenario, 50 concurrent users for 5 minutes. Asserts: zero OOM kills, error rate < 1%, P99 < 2x baseline. Uses GHA scheduled workflow with emulators.
    status: todo
    note: ""

  # ── Phase 6: External Testnet ── SEQUENTIAL after Phases 4+5 ────────────
  - id: p6-testnet-deployment-config
    content: |
      - [ ] [HUMAN] P1. Create testnet.odum.io deployment config in deployment-service. Same infrastructure as production but with CLOUD_MOCK_MODE=true, MOCK_SCENARIO=NORMAL, seed=42. Data isolation: separate GCS bucket prefix (testnet-*), separate PubSub topic prefix (testnet-*). Cloud Run services with min-instances=0 (scale to zero when unused).
    status: todo
    note: ""
  - id: p6-testnet-demo-preset
    content: |
      - [ ] [AGENT] P1. Create demo preset for external users. Read-only access (no POST/PUT/DELETE on execution endpoints). Rate limiting: 60 req/min per IP. No auth required (DISABLE_AUTH=true, VITE_SKIP_AUTH=true). Scenario locked to NORMAL (no scenario switching for external users). Add demo mode detection in BFF: if TESTNET_MODE=demo, enforce read-only.
    status: todo
    note: ""
  - id: p6-testnet-monitoring
    content: |
      - [ ] [AGENT] P2. Add testnet-specific monitoring. Track: external user sessions (count, duration), API usage by endpoint, error rates, scenario health. Emit to Prometheus metrics. Add testnet health page at testnet.odum.io/health showing system status, active scenario, data freshness.
    status: todo
    note: ""
  - id: p6-testnet-data-refresh
    content: |
      - [ ] [AGENT] P2. Scheduled daily data refresh for testnet. Cron job runs seed_mock_data.py --seed 42 for all services. Ensures testnet data stays fresh (timestamps within 24h) while maintaining determinism. GHA scheduled workflow or Cloud Scheduler.
    status: todo
    note: ""

  # ── Phase 7: Final Validation ── SEQUENTIAL after all phases ────────────
  - id: p7-qg-sweep
    content: |
      - [ ] [SCRIPT] P0. Run quality-gates.sh on all affected repos: unified-internal-contracts, unified-api-contracts, unified-trading-library, execution-service, system-integration-tests. All must pass.
    status: todo
    note: ""
  - id: p7-mock-live-parity-test
    content: |
      - [ ] [AGENT] P0. Create mock-vs-live parity test in system-integration-tests. Run full pipeline (instruments -> market-data -> features -> strategy -> execution) in mock mode with seed=42. Record outputs. Run same pipeline against staging with real data. Compare: schema shapes must match, field types must match, value ranges must be plausible. Document any delta.
    status: todo
    note: ""
  - id: p7-end-to-end-scenario-test
    content: |
      - [ ] [AGENT] P0. End-to-end scenario test: activate BUST scenario via API, verify all downstream effects: price drops in market-data, risk alerts in alerting-service, position liquidation warnings in execution-service, UI shows circuit breaker state. All within 30 seconds of scenario activation.
    status: todo
    note: ""
isProject: false
---

# Notes & Context

## Execution DAG

```
Phase 0 (Seed Hardening)
    |
    v
Phase 1 (Scenario Infra)  ←── Phase 2 (Error Codes) [PARALLEL]
    |                           |
    |                      Phase 3 (Perf Gates) [PARALLEL with Phase 1]
    v                           |
Phase 4 (UI Scenario)          |
    |                           v
    |                      Phase 5 (Load Testing)
    v                           |
Phase 6 (External Testnet) ←───┘
    |
    v
Phase 7 (Final Validation)
```

## Phase Gate Criteria

- **Phase 0 exit:** All 15 seed scripts produce deterministic output with --seed 42
- **Phase 1 exit:** 4 new scenarios in MockScenario enum, scenario API works, SIT tests pass
- **Phase 2 exit:** All 33 venues have VENUE_ERROR_MAP entries, aave_plasma fixed, execution-service routes on
  ErrorAction, QG check enforces coverage
- **Phase 3 exit:** PerformanceGate + MemoryGate in CI for 4 critical services, baselines recorded
- **Phase 4 exit:** UI scenario selector works, status indicator shows active scenario
- **Phase 5 exit:** Load generator runs, instrument scaling tested to 10K, response baselines recorded
- **Phase 6 exit:** testnet.odum.io accessible, demo preset enforces read-only, monitoring live
- **Phase 7 exit:** All QG pass, mock-live parity verified, end-to-end scenario test passes

## Pre-Audit Manifest

### Existing Infrastructure (no changes needed)

| Component              | Location                                                                                   | Status              |
| ---------------------- | ------------------------------------------------------------------------------------------ | ------------------- |
| MockScenario enum      | `unified-internal-contracts/unified_internal_contracts/modes.py:93`                        | 8 scenarios defined |
| ScenarioConfig         | `unified-internal-contracts/unified_internal_contracts/testing/scenario_config.py`         | Loads from YAML     |
| VENUE_ERROR_MAP        | `unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/__init__.py:21` | 6 sub-maps merged   |
| classify_venue_error() | `unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/__init__.py:32` | Working             |
| DefiErrorCode          | `unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/defi.py:23`     | 13 codes            |
| PerformanceGate        | `unified-trading-library/unified_trading_library/`                                         | Exported from UTL   |
| MemoryGate             | `unified-trading-library/unified_trading_library/`                                         | Exported from UTL   |
| SyntheticDataGenerator | `unified-internal-contracts/unified_internal_contracts/testing/synthetic.py`               | Tick generation     |

### Known Bugs

| Bug                                      | Location                     | Fix                                               |
| ---------------------------------------- | ---------------------------- | ------------------------------------------------- |
| aave_plasma missing from VENUE_ERROR_MAP | `defi.py` has only `aave_v3` | Add `aave_plasma` entry with same classifications |
| Seed scripts without --seed flag         | Multiple seed_mock_data.py   | Add --seed CLI arg + deterministic RNG            |

### Downstream Consumers of Changes

| Change                             | Consumers                                                    | Impact                             |
| ---------------------------------- | ------------------------------------------------------------ | ---------------------------------- |
| New MockScenario values in UIC     | All 13 seed_mock_data.py scripts, system-integration-tests   | Must handle new enum values        |
| New VENUE_ERROR_MAP entries in UAC | execution-service, all adapters calling classify_venue_error | No code change needed (map lookup) |
| PerformanceGate CI fixtures        | Each service's test suite                                    | New test files only                |

## B3 KPI Targets

| Domain      | KPI                      | Target                |
| ----------- | ------------------------ | --------------------- |
| Execution   | Order routing P99        | < 50ms                |
| Market data | Tick processing P99      | < 100ms               |
| Strategy    | Signal generation P99    | < 200ms               |
| Features    | Feature calc P99         | < 500ms               |
| Load        | Error rate under stress  | < 1%                  |
| Load        | Instrument scale ceiling | 10,000 instruments    |
| Testnet     | Data freshness           | < 24 hours            |
| Determinism | Seed reproducibility     | byte-identical output |

## References

- ScenarioConfig YAML: `unified-internal-contracts/unified_internal_contracts/testing/scenarios/`
- Error classification: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/`
- UTL performance gates: `unified-trading-library/unified_trading_library/`
- SIT scenario tests: `system-integration-tests/tests/smoke/test_mock_scenarios.py`
- SIT error tests: `system-integration-tests/tests/integration/test_error_normalisation.py`
- Local dev guide: `unified-trading-codex/08-workflows/local-dev.md`
- VENUE_REGISTRY (33 venues): `unified-market-interface/unified_market_interface/factory.py`
