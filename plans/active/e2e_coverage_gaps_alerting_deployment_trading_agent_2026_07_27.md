---
doc_type: plan
title: E2E coverage gaps — alerting-service, deployment-service, trading-agent-service
summary:
  Three services have no genuine end-to-end test coverage, surfaced by the 2026-07-27 pre-June-1 stale-plans audit while
  archiving the old plans/active/end-to-end-testing/ per-service checklist. alerting-service and deployment-service each
  have an existing "e2e" test file that does NOT actually exercise their own service code (false confidence);
  trading-agent-service has no e2e test directory at all.
status: complete
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [alerting-service, deployment-service, trading-agent-service]
scope: [engineer]
tags: [e2e-testing, coverage-gap, alerting, deployment, trading-agent, hygiene]
related: []
created: 2026-07-27
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.5
last_updated: 2026-07-27
supersedes: []
superseded_by:
locked_by:
locked_since:
depends_on:
source:
  [
    plans/archive/2026_07/e2e_testing_020_alerting_service_2026_03_22.md,
    plans/archive/2026_07/e2e_testing_022_deployment_service_2026_03_22.md,
    plans/archive/2026_07/e2e_testing_023_trading_agent_service_2026_03_22.md,
  ]
assigned_role: backend_engineer
drift_direction: none
---

> **🗄️ ARCHIVED 2026-07-30** — status=complete, 0 open todos (3/3 done). Closed out + verified by
> `plans/archive/2026_07/e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27_finalize_2026_07_30.md`.
> Archived per /codex/12-agent-workflow/plan-completion-and-archival-discipline.md.

# E2E coverage gaps — alerting-service, deployment-service, trading-agent-service

## Context

The 2026-07-27 pre-June-1 stale-plans audit archived 22 blank, never-executed test-matrix templates from
`plans/active/end-to-end-testing/` (002-023). A follow-up investigation checked whether the services those templates
targeted have since gained real E2E coverage some other way. Most have (data-pipeline-check-\* skills, ml-service's own
e2e suite, strategy-service's consolidated integration tests, the determinism-spine plans). Three do not — and two of
the three have an EXISTING file labeled "e2e" that gives false confidence because it doesn't actually exercise the
service's own code. That's worth fixing on its own, independent of building the coverage this plan tracks.

## Todos

- [x] ✅ [CODE] P1. **alerting-service real E2E harness.** — alerting-service@d35647ad. Replaced
      `alerting-service/tests/e2e/test_mock_replay_e2e.py` with real pipeline coverage:
      `AlertSubscriber.dispatch_event()` → `router.route_event()` (real UAC rule matching, dedup, channel resolution) →
      `AlertStorageStore` persistence (real on-disk `LocalStorageProvider`); open/ack/resolve alert lifecycle
      round-tripped through real persistence methods; the real `/alerts/delivery-status/{alert_id}` FastAPI route
      querying that persisted state; multi-service health aggregation via the real
      `core.system_health_aggregator.get_system_health()`. Only the true external boundary (Slack/health-check HTTP
      calls) stubbed via respx.
- [x] ✅ [CODE] P1. **deployment-service real E2E harness.** — deployment-service@0baf65c. Replaced
      `deployment-service/tests/e2e/test_deployment_e2e.py`'s import/config-existence smoke tests with 4 test classes
      exercising real production code against real configs (venues.yaml, dependencies.yaml,
      sharding.instruments-service.yaml, configs/clusters/cefi.yaml, `VM_PREFIX_TO_BUCKET`) with only the GCS boundary /
      process-launch backend faked: (1) `DataCatalog.catalog_service()` against real CEFI venues -> asserts the produced
      shard set matches venues.yaml 1:1; (2) `DependencyGraph.check_dependencies()` executed (not just loaded) against
      the real market-tick-data-service<-instruments-service edge, pass + fail cases via `MockCloudClient`; (3)
      `classify_deployment_target`/`umbrella_for_vm_name` resolution against real `VM_PREFIX_TO_BUCKET` prefixes (no VM
      launched, no silent-default on an unregistered prefix); (4) a `CliRunner` invocation of
      `cluster bootstrap --cluster cefi` with only `_start_local_service` mocked, asserting real
      `ClusterStatus.services` side-effects in real dependency order. Writing (4) surfaced every `log_event()` call in
      `cluster.py` used a retired kwargs-passthrough signature — every real bootstrap/teardown/batch/schedule/service
      call currently raised `TypeError` in production; migrated all 13 call sites to the current `details={...}`
      signature in the same commit. Also added `MockCloudClient.file_exists()` (only `list_files` was overridden),
      needed for a passing single-file dependency check without real GCS. Full repo QG green
      (`.qg_last_passed_sha=5ec3eb9`, verified via quickmerge --agent sentinel).
- [x] ✅ [CODE] P2. **trading-agent-service E2E harness (new — none exists today).** — trading-agent-service@bf95e1f.
      Added `tests/e2e/test_trading_agent_e2e.py` (+`tests/e2e/__init__.py`), stubbing only the true external-network
      boundary (execution-service/risk-service HTTP calls) — the queue + kill-switch storage boundaries run the real
      `LocalQueueProvider`/`LocalStorageProvider` via the real `get_queue_client()`/`get_storage_client()` code paths:
      (1) `TestMockDrivenLoopToLedgerFill` — a real `MicroLoopOrchestrator` drives real L2/L3/L6 loops, seeded with
      `mock_data_provider.py`'s own synthetic BTC signal/catalog builders, over a scripted weak-then-strong signal
      sequence published to a real local queue → strategy decision → ledger fill (FILLED, real fill price). (2)
      `TestL2SignalLoopTickDrivenExecution` — `BaseLoop.run_forever()`'s real scheduling (not a hand-called
      `run_once()`, which is all the existing unit tests ever do), proving the loop survives a malformed message and
      converges across real elapsed ticks. (3) `TestReplayFixtureDeterministicOutput` — `InferenceCache` +
      `DirectiveLog` + `clamp_to_cutoff` driven together (not in isolation, unlike
      `tests/unit/test_replay_infrastructure.py`) by one fixture dataset: live record → persisted-fixture →
      backtest-continuation replay is byte-identical with no recompute, and a forward-looking row is clamped in backtest
      but passes through in live. (4) `TestCliMainOneFullCycleSmoke` — the real `cli/main.py` `main()` entry point, one
      full mock-mode cycle, asserting the real risk-gate + ranker output on disk. Full repo QG green
      (`.qg_last_passed_sha=ecb362c`, verified via quickmerge --agent sentinel; 146 tests passed, coverage 71.50%).

## Progress Log

- 2026-07-27: Plan created from the pre-June-1 stale-plans audit's e2e-testing archival follow-up investigation. No
  todos executed yet.
- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
  Companion gated finalize plan authored:
  `e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27_finalize_2026_07_30.md`.
- **2026-07-30 (slot 16, backend_engineer)** — Companion finalize plan verified all 3 harnesses actually exercise their
  claimed coverage (real test classes + real suite pass output — alerting-service 907 passed, deployment-service 2968
  passed/5 skipped, trading-agent-service 146 passed). Zero remaining `- [ ]` items. Archived per the standard 6-step
  ritual; see the finalize plan's Progress Log for the full referrer-fix detail.
