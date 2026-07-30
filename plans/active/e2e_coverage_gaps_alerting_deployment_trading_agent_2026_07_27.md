---
doc_type: plan
title: E2E coverage gaps — alerting-service, deployment-service, trading-agent-service
summary:
  Three services have no genuine end-to-end test coverage, surfaced by the 2026-07-27 pre-June-1 stale-plans audit while
  archiving the old plans/active/end-to-end-testing/ per-service checklist. alerting-service and deployment-service each
  have an existing "e2e" test file that does NOT actually exercise their own service code (false confidence);
  trading-agent-service has no e2e test directory at all.
status: active
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

# E2E coverage gaps — alerting-service, deployment-service, trading-agent-service

## Context

The 2026-07-27 pre-June-1 stale-plans audit archived 22 blank, never-executed test-matrix templates from
`plans/active/end-to-end-testing/` (002-023). A follow-up investigation checked whether the services those templates
targeted have since gained real E2E coverage some other way. Most have (data-pipeline-check-\* skills, ml-service's own
e2e suite, strategy-service's consolidated integration tests, the determinism-spine plans). Three do not — and two of
the three have an EXISTING file labeled "e2e" that gives false confidence because it doesn't actually exercise the
service's own code. That's worth fixing on its own, independent of building the coverage this plan tracks.

## Todos

- [ ] [CODE] P1. **alerting-service real E2E harness.** `alerting-service/tests/e2e/test_mock_replay_e2e.py` (178 lines)
      never imports `alerting_service.*` — it re-implements ad-hoc assertions over VCR cassette data instead of
      exercising the real pipeline. Build a real E2E test covering: (1) subscriber → `rules` → `notifiers` pipeline on a
      real injected event; (2) alert lifecycle (open/ack/resolve) via `persistence`; (3) `api/routes` query after an
      injected trigger; (4) multi-venue aggregation via the real `engine` code, not an inline reimplementation.
- [ ] [CODE] P1. **deployment-service real E2E harness.** `deployment-service/tests/e2e/test_deployment_e2e.py` (129
      lines, `@pytest.mark.e2e`) is import/config-existence smoke tests only (e.g. `test_catalog_module_import`) — not a
      real deploy/launch flow. Build a real E2E test covering: (1) `DataCatalog` aggregation against a real
      asset_group/venue producing the correct shard set; (2) dependency-graph _execution_, not just load; (3) VM
      launch-config resolution (`VM_PREFIX_TO_BUCKET`/`lifecycle_class`) without actually launching a VM; (4) a CLI
      invocation against a mocked backend asserting real side-effects into `services`.
- [ ] [CODE] P2. **trading-agent-service E2E harness (new — none exists today).** No `tests/e2e/` directory;
      `tests/integration/` only covers generic UAC/UIC dependency-contract checks, never the trading loop itself. Build:
      (1) a mock-driven loop test — `engine/orchestrator.py` + `mock_data_provider.py` → a strategy decision → a ledger
      fill, over a scripted signal sequence; (2) an `app/loops` tick-driven execution test; (3) a `replay/` test against
      a fixture dataset for deterministic output; (4) a `cli/main.py` one-full-cycle smoke test.

## Progress Log

- 2026-07-27: Plan created from the pre-June-1 stale-plans audit's e2e-testing archival follow-up investigation. No
  todos executed yet.
- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
  Companion gated finalize plan authored:
  `e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27_finalize_2026_07_30.md`.
