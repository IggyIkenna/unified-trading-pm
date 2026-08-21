---
doc_type: plan
title: plan-d-testnet-stress-testing
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, system-integration-tests, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-21"
overview: "Backend-only: seed determinism (seed=42), scenario expansion (BAD_SCHEMA, ERROR_STORM, FLASH_CRASH), error
  code

  stress tests (all 18 canonical + 13 DeFi codes), performance regression gates (PerformanceGate/MemoryGate in CI),

  synthetic load generator (45->1K->10K instruments), and error classification re-audit (aave_plasma bug, missing

  venue maps, QG enforcement). Goal: no meaningful difference between testing mock and live.

  "
type: mixed
epic: epic-code-completion
locked_by:
locked_since:
completion_gates: { code: C5, deployment: none, business: B3 }
repo_gates:
  - { repo: unified-internal-contracts, code: C0, deployment: none, business: none }
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: unified-trading-library, code: C0, deployment: none, business: none }
  - { repo: execution-service, code: C0, deployment: none, business: none }
  - { repo: system-integration-tests, code: C0, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
  - { repo: deployment-service, code: C0, deployment: none, business: none }
depends_on: [plan-c-domain-data-api]
todos:
  - { id: p0-audit-seed-determinism, content: "- [x] [AGENT] P0. Audit all seed_mock_data.py scripts (13 services) for
        determinism. Each must accept --seed flag (default=42), pass it to random.seed() and numpy random generator.
        Verify: running seed twice produces byte-identical output. Files: instruments-service,
        market-data-processing-service, features-delta-one-service, features-sports-service,
        features-multi-timeframe-service, features-cross-instrument-service, execution-service, strategy-service,
        alerting-service, pnl-attribution-service, position-balance-monitor-service, risk-and-exposure-service,
        trading-agent-service, ml-training-service, ml-inference-service. Output: manifest of which scripts already have
        seed support and which need fixing.

        ", status: done, note: All 15 scripts exist with --seed flag. Use InstrumentGenerator(seed=) or
        SyntheticDataGenerator(seed=) for determinism. }
  - { id: p0-fix-seed-scripts, content: "- [x] [AGENT] P0. Fix all seed scripts identified in p0-audit-seed-determinism
        that lack seed=42 determinism. Add --seed CLI arg, wire into all RNG sources (random, numpy, uuid generation).
        Verify: `python seed_mock_data.py --seed 42 | md5` produces same hash on consecutive runs.

        ", status: done, note: No fixes needed — all scripts already have seed support via UIC generators. }
  - { id: p0-document-seed-vs-logic, content: "- [ ] [AGENT] P1. Document which services need seeding (data generators)
        vs which use real logic (execution-service order matching, strategy-service signal generation). Add table to
        unified-trading-/codex/08-workflows/local-dev.md.

        ", status: todo, note: "" }
  - { id: p0-aws-mock-data-upload, content: "- [ ] [AGENT] P1. Upload mock data to AWS S3 dev buckets. Run
        generate-mock-data.sh --env dev with CLOUD_PROVIDER=aws. The SeedWriter CloudWriter already supports S3 — just
        needs AWS credentials and bucket bootstrap.

        ", status: todo, note: "" }
  - { id: p0-live-streaming-mock, content: "- [ ] [AGENT] P1. Wire live streaming mock in unified-trading-api WebSocket.
        In mock mode, generate synthetic ticks every 1-5 seconds using SyntheticDataGenerator, push via WebSocket
        channels. This simulates the live data feed without real exchange connections.

        ", status: todo, note: "" }
  - { id: p1-add-new-scenarios, content: "- [x] [AGENT] P0. Extend MockScenario enum in UIC modes.py with: BAD_SCHEMA,
        ERROR_STORM, FLASH_CRASH, HIGH_LATENCY. Add corresponding YAML configs in
        unified_internal_contracts/testing/scenarios/. BAD_SCHEMA: 10% of records have corrupted fields. ERROR_STORM:
        every adapter returns errors for 30s bursts. FLASH_CRASH: 50% price drop in 5 minutes then recovery.
        HIGH_LATENCY: 2-5s artificial delay on all responses.

        ", status: done, note: "" }
  - { id: p1-scenario-config-api, content: "- [ ] [AGENT] P0. Add POST /api/v1/scenarios/activate endpoint to config-api
        (or system-admin API route in BFF). Accepts {scenario: MockScenario, seed: int}. Updates MOCK_SCENARIO env var
        for all running services via shared state in MockStateStore. Only available when CLOUD_MOCK_MODE=true.

        ", status: todo, note: Depends on Plan C BFF being available }
  - { id: p1-scenario-propagation, content: "- [ ] [AGENT] P0. Wire scenario change propagation: when scenario is
        activated via API, all services with seed_mock_data.py re-seed with the new scenario config. Use PubSub topic
        (via UCI get_pubsub_client) to broadcast scenario changes. In mock mode, use emulator.

        ", status: todo, note: "" }
  - { id: p1-sit-scenario-tests, content: "- [ ] [AGENT] P1. Add SIT tests for scenario switching:
        test_mock_scenarios.py already exists in system-integration-tests. Extend with tests for BAD_SCHEMA (verify
        error handling), ERROR_STORM (verify circuit breakers fire), FLASH_CRASH (verify alerts trigger). Each test
        activates scenario via API, then asserts downstream effects.

        ", status: todo, note: "" }
  - { id: p2-error-reaudit-venue-map, content: "- [x] [AGENT] P0. Re-audit VENUE_ERROR_MAP completeness. Current state:
        cefi.py has binance maps, defi.py has balancer/aave_v3/uniswap_v3, sports.py/tradfi.py/onchain_perps.py exist.
        Cross-reference against VENUE_REGISTRY (33 venues: 9 CeFi + 9 TradFi + 14 DeFi + 1 Onchain Perps) in UMI
        factory.py. Identify all venues with adapters but missing from VENUE_ERROR_MAP. Output: gap manifest with venue
        name, adapter file, and count of error codes needing classification.

        ", status: done, note: "" }
  - { id: p2-fix-aave-plasma-bug, content: "- [x] [AGENT] P0. Fix aave_plasma missing from VENUE_ERROR_MAP. UTL
        instrument_date_filter.py references aave_plasma (available_from: 2024-03-01) but VENUE_ERRORS_DEFI only has
        aave_v3. Add aave_plasma entry to defi.py VENUE_ERRORS_DEFI with same error classifications as aave_v3 (they
        share the same Aave V3 protocol).

        ", status: done, note: "" }
  - { id: p2-add-missing-venue-maps, content: "- [x] [AGENT] P0. Add VENUE_ERROR_MAP entries for all active adapters
        identified in p2-error-reaudit-venue-map. Priority: venues with URDI/UTEI adapters that call
        classify_venue_error(). Each venue needs at minimum: rate-limit, auth-failure, timeout, and unknown-error
        classifications. Use ErrorAction.RETRY for transient, ErrorAction.FAIL for permanent.

        ", status: done, note: No missing entries — all 32 venues with adapters have error maps. }
  - { id: p2-wire-classify-into-execution, content: "- [ ] [AGENT] P0. Wire classify_venue_error() into
        execution-service error routing. Execution-service should call classify_venue_error(venue, raw_error_code) on
        every adapter error, then route based on ErrorAction: RETRY = re-queue with backoff, FAIL = dead-letter + alert,
        SKIP = log + continue. Verify: execution-service imports classify_venue_error from UAC (not self-declared).

        ", status: todo, note: "" }
  - { id: p2-error-storm-scenario, content: "- [ ] [AGENT] P0. Create ERROR_STORM scenario test suite. Exercises all 18
        canonical error codes (from VENUE_ERROR_MAP across cefi/defi/tradfi/sports/onchain_perps/infra) + all 13
        DefiErrorCode values through the pipeline. Test: inject each error code via mock adapter, verify
        classify_venue_error() returns correct classification, verify execution-service routes correctly
        (RETRY/FAIL/SKIP), verify alerting-service emits correct alert type.

        ", status: todo, note: "" }
  - { id: p2-qg-venue-error-coverage, content: '- [ ] [AGENT] P1. Add QG check to UAC quality-gates.sh: every adapter
        that calls classify_venue_error() must have its venue present in VENUE_ERROR_MAP. Script: grep all
        classify_venue_error("venue_name" calls across workspace, extract venue names, verify each exists as a key in
        VENUE_ERROR_MAP. Fail QG if any venue is missing.

        ', status: todo, note: "" }
  - { id: p3-perf-gate-ci-integration, content: "- [ ] [AGENT] P0. Integrate PerformanceGate + MemoryGate from UTL into
        CI for critical services. AUDIT CORRECTION: PerformanceGate and MemoryGate classes EXIST in UTL (correcting
        earlier audit mistake that said they were missing), and tests/perf/ directories were created in 5 services.
        However, these tests are NOT activated in any service's quality-gates.sh script — they exist as dead test files
        that CI never runs. Must: add explicit perf test invocation to each service's quality-gates.sh.

        ", status: todo, note: Tests exist but not activated in QG scripts. Gates exist in UTL but are dead code in CI. }
  - { id: p3-memory-gate-ci, content: "- [ ] [AGENT] P0. Add MemoryGate tests for services with known memory pressure.
        AUDIT CORRECTION: MemoryGate test files were created but are NOT invoked by quality-gates.sh in any service.
        Must activate in QG scripts.

        ", status: todo, note: Test files exist but not activated in QG scripts. }
  - { id: p3-perf-baselines, content: "- [ ] [AGENT] P1. Establish performance baselines for all services. AUDIT:
        baselines not recorded because perf tests not activated in CI. Must activate tests first, then record baselines.

        ", status: todo, note: Depends on p3-perf-gate-ci-integration activation. }
  - { id: p4-synthetic-load-generator, content: "- [x] [AGENT] P0. Create synthetic load generator script in
        unified-trading-pm/scripts/load-testing/. Configurable: instrument count (45, 1000, 5000, 10000), tick rate per
        instrument (1/s, 10/s), concurrent users (1, 10, 50), scenario (any MockScenario). Uses SyntheticDataGenerator
        from UIC with seed=42. Outputs: throughput (msgs/s), P50/P95/P99 latency, error rate, memory usage.

        ", status: done, note: "" }
  - { id: p4-instrument-scaling, content: "- [ ] [AGENT] P0. Test instrument scaling path: 45 (current mock) -> 1000 ->
        5000 -> 10000 instruments. Verify: instruments-service seed_mock_data.py can generate N instruments
        deterministically. market-data-processing-service can process ticks for N instruments within P99 threshold.
        features-delta-one-service can compute features for N instruments within P99 threshold. Document: at what N does
        each service exceed its PerformanceGate threshold.

        ", status: todo, note: "" }
  - { id: p4-response-time-baselines, content: "- [ ] [AGENT] P1. Establish response time baselines for all API
        endpoints under load. Use load generator with 1000 instruments, 10 concurrent users. Record: GET
        /api/instruments (< 200ms), GET /api/positions (< 100ms), GET /api/market-data/ticks (< 50ms), POST
        /api/execution/orders (< 100ms). Store baselines in PM configs. CI load test runs weekly, alerts on >20%
        regression.

        ", status: todo, note: "" }
  - { id: p4-stress-test-ci, content: "- [ ] [AGENT] P2. Add stress test CI job (weekly schedule, not on every push).
        Runs load generator with 5000 instruments, HEAVY scenario, 50 concurrent users for 5 minutes. Asserts: zero OOM
        kills, error rate < 1%, P99 < 2x baseline. Uses GHA scheduled workflow with emulators.

        ", status: todo, note: "" }
  - { id: p5-deployment-seed-mock-data, content: "- [x] [AGENT] P0. Create deployment-service/scripts/seed_mock_data.py
        (missing — only service without one). Generate mock VM records, shard configs, deployment history. Accept --seed
        flag (default=42) for determinism. Consistent with all other seed_mock_data.py scripts.

        ", status: done, note: "" }
  - { id: p5-mock-vm-lifecycle, content: "- [ ] [AGENT] P0. Add mock VM lifecycle state machine
        (STAGING->RUNNING->TERMINATED, with configurable failure injection). States transition on timer or API trigger.
        Failure injection: configurable probability of STAGING->FAILED transition. Wire into MockStateStore for
        interactive mode persistence.

        ", status: todo, note: "" }
  - { id: p5-mock-shard-failure, content: "- [ ] [AGENT] P0. Add mock shard failure scenarios (individual shard FAILED
        while others SUCCEEDED). Configurable: which shard index fails, failure reason (OOM, timeout, crash). Verify:
        deployment-ui shows mixed shard states correctly. Shard-level failure isolation rules apply (no raise inside
        per-shard loop).

        ", status: todo, note: "" }
  - { id: p5-mock-health-gate-timeout, content: "- [ ] [AGENT] P1. Add mock health gate timeout scenarios (slow-start
        simulation). Configurable delay before health endpoint returns 200. Test: deployment orchestrator correctly
        waits up to timeout, then marks deployment as FAILED if health gate never passes. Verify alerting-service
        receives health-gate-timeout event.

        ", status: todo, note: "" }
  - { id: p5-mock-quota-exhaustion, content: "- [ ] [AGENT] P1. Add mock quota exhaustion (quota broker returns denial).
        QuotaBrokerClient mock returns DENIED for configurable resource types (CPU, GPU, memory). Verify:
        deployment-service handles denial gracefully, queues deployment for retry, emits QUOTA_DENIED event.

        ", status: todo, note: "" }
  - { id: p5-mock-cross-region-failover, content: "- [ ] [AGENT] P1. Add mock cross-region failover (primary fails,
        secondary activates). Simulate: primary region health check fails, failover triggers to secondary region,
        traffic reroutes. Verify: deployment state reflects region switch, no data loss during failover window.

        ", status: todo, note: "" }
  - { id: p5-mock-orphan-cleanup-retry, content: "- [ ] [AGENT] P2. Add mock orphan cleanup retry scenarios. Simulate:
        orphan VMs detected by cleanup job, first cleanup attempt fails (transient error), retry succeeds. Verify:
        cleanup job retries with backoff, orphan is eventually terminated, audit log records all attempts.

        ", status: todo, note: "" }
  - { id: p6-qg-sweep, content: "- [ ] [SCRIPT] P0. Run quality-gates.sh on all affected repos:
        unified-internal-contracts, unified-api-contracts, unified-trading-library, execution-service,
        system-integration-tests, deployment-service. All must pass.

        ", status: todo, note: "" }
  - { id: p6-mock-live-parity-test, content: "- [ ] [AGENT] P0. Create mock-vs-live parity test in
        system-integration-tests. Run full pipeline (instruments -> market-data -> features -> strategy -> execution) in
        mock mode with seed=42. Record outputs. Run same pipeline against staging with real data. Compare: schema shapes
        must match, field types must match, value ranges must be plausible. Document any delta.

        ", status: todo, note: "" }
  - { id: p6-end-to-end-scenario-test, content: "- [ ] [AGENT] P0. End-to-end scenario test: activate BUST scenario via
        API, verify all downstream effects: price drops in market-data, risk alerts in alerting-service, position
        liquidation warnings in execution-service, UI shows circuit breaker state. All within 30 seconds of scenario
        activation.

        ", status: todo, note: "" }
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
    |                           |                    |
    v                           v                    v
Phase 4 (Load Testing) ←───────┘    Phase 5 (Deployment Mocks) [PARALLEL with Phase 3]
    |                                     |
    v                                     v
Phase 6 (Final Validation) ←─────────────┘
```

NOTE: UI scenario panel (selector dropdown, status indicator, real-time switching, custom scenario builder) and external
testnet deployment (testnet.odum.io) have been moved to Plan E (UI Backend Integration). This plan now covers
backend-only testing infrastructure.

## Phase Gate Criteria

- **Phase 0 exit:** All 15 seed scripts produce deterministic output with --seed 42
- **Phase 1 exit:** 4 new scenarios in MockScenario enum, scenario API works, SIT tests pass
- **Phase 2 exit:** All 33 venues have VENUE_ERROR_MAP entries, aave_plasma fixed, execution-service routes on
  ErrorAction, QG check enforces coverage
- **Phase 3 exit:** PerformanceGate + MemoryGate in CI for 4 critical services, baselines recorded
- **Phase 4 exit:** Load generator runs, instrument scaling tested to 10K, response baselines recorded
- **Phase 5 exit:** deployment-service seed_mock_data.py works, VM lifecycle state machine operational, shard failure
  scenarios work, health gate timeout / quota exhaustion / failover / orphan cleanup scenarios all functional
- **Phase 6 exit:** All QG pass (including deployment-service), mock-live parity verified, end-to-end scenario test
  passes

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
- Local dev guide: `unified-trading-/codex/08-workflows/local-dev.md`
- VENUE_REGISTRY (33 venues): `unified-market-interface/unified_market_interface/factory.py`
