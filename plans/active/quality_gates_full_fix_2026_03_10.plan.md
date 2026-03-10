---
name: Quality Gates Full Fix — All Repos Pass Unit Tests + Coverage
overview: >
  Systematically run unit tests (RUN_INTEGRATION=false) across all repos, fix every failing test and coverage gap
  properly. No bypasses. No type:ignore hacks. No test exemptions. Fix root causes.

  Coverage targets:
    - T0–T3 libraries: >= 80%
    - Services / APIs: >= 70%
    - Exceptions (exactly 4 repos, designated below): allowed below 70%
    - UIs: no Python coverage target; smoke tests required

  Permitted < 70% repos (real-time / tick-level repos with tiny unit-test surface):
    1. market-tick-data-service    (live-tick ingestion, integration-only meaningful tests)
    2. execution-service           (1200+ tests but heavy integration surface; 26% placeholder)
    3. features-commodity-service  (early-stage, <15 tests currently)
    4. market-data-processing-service (pipeline throughput service)

  All other repos must meet targets above. Fix tests — do not lower thresholds.
isProject: true
todos:
  - id: baseline-run
    content: >
      Run RUN_INTEGRATION=false bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --test
      --skip-alignment --skip-setup  from workspace root. Capture full output to plans/active/work/qg_run_baseline.log.
      Parse FAIL lines → issue log.
    status: completed
    notes: |
      Running in background. Output written to work/qg_run_baseline.log.
      Issue log appended to work/qg_issues.md as results arrive.

  - id: issue-log
    content: >
      Maintain plans/active/work/qg_issues.md — canonical issue tracker. Columns: repo | issue_type
      (test_fail|coverage|import_error) | details | agent_id | status. Never delete rows — only update status (open →
      in_progress → fixed → verified).
    status: in_progress
    notes: See work/qg_issues.md

  - id: fix-t0-libraries
    content: >
      Fix all T0 libraries failing QG (tests + coverage >= 80%): unified-internal-contracts, matching-engine-library,
      execution-algo-library, unified-api-contracts. Spawn one agent per failing repo.
    status: pending

  - id: fix-t1-libraries
    content: >
      Fix all T1 libraries failing QG (tests + coverage >= 80%): unified-events-interface, unified-config-interface,
      unified-trading-library (currently 78% — needs +2%).
    status: pending

  - id: fix-t2-libraries
    content: >
      Fix all T2 libraries failing QG (tests + coverage >= 80%): unified-market-interface (40% — major gap),
      unified-trade-execution-interface, unified-ml-interface, unified-position-interface,
      unified-reference-data-interface, unified-defi-execution-interface, unified-feature-calculator-library,
      unified-sports-execution-interface (76% — below 80%).
    status: pending
    notes: |
      unified-market-interface at 40% is the biggest library gap.
      unified-sports-execution-interface at 76% needs ~4% more.
      unified-trading-library at 78% needs ~2% more.
      execution-algo-library at 72% needs ~8% more.

  - id: fix-t3-libraries
    content: >
      Fix all T3 libraries failing QG (tests + coverage >= 80%): unified-domain-client (84% — already passing).
    status: pending

  - id: fix-service-repos
    content: >
      Fix all service/API repos failing QG (tests + coverage >= 70%, except 4 exempt repos): alerting-service,
      client-reporting-api (18%!), deployment-api, deployment-service, execution-results-api (66%),
      features-calendar-service, features-cross-instrument-service (65%), features-delta-one-service,
      features-multi-timeframe-service (57%), features-onchain-service (39%), features-sports-service,
      features-volatility-service (35%), instruments-service (53%), market-data-api, ml-inference-service,
      ml-training-service (35%), pnl-attribution-service (46%), position-balance-monitor-service,
      risk-and-exposure-service, strategy-service, strategy-validation-service, trading-agent-service (50%),
      ml-inference-api, ml-training-api, trading-analytics-api (new repos — unknown coverage).
    status: pending
    notes: |
      Spawn one agent per repo. Agent must:
      1. cd <repo> && .venv/bin/pytest tests/unit/ -v --cov=<pkg> --cov-report=xml --cov-report=term-missing
      2. Identify all failing tests + coverage gaps
      3. Fix root causes (no mocks that bypass logic, no skip markers)
      4. Re-run to verify >= 70% and 0 test failures
      5. Commit with "test: fix unit tests in <repo>"

  - id: fix-ui-smoke-tests
    content: >
      Verify UI repos have thorough smoke tests (vitest + Playwright where applicable). Repos: deployment-ui,
      execution-analytics-ui, live-health-monitor-ui, logs-dashboard-ui, ml-training-ui, onboarding-ui, settlement-ui,
      strategy-ui, trading-analytics-ui, client-reporting-ui, batch-audit-ui, unified-trading-ui-auth.
    status: pending
    notes: |
      UIs have testing_level=unit. Check that quality-gates.sh runs vitest + coverage.
      If vitest coverage < reasonable threshold (60% statements), improve smoke coverage.

  - id: verify-no-bypasses
    content: >
      After all fix agents complete: run full QG scan to confirm no bypass patterns introduced. Check: no
      pytest.mark.skip without reason, no # type: ignore, no || true in QG scripts, no coverage threshold lowered below
      target, no test deleted (only fixed).
    status: pending

  - id: update-manifest-coverage
    content: >
      After verified green: run coverage-audit.py to update workspace-manifest.json with real coverage_pct values per
      repo. Commit to unified-trading-pm.
    status: pending

  - id: final-qg-run
    content: >
      Run full QG one last time to confirm all repos pass. RUN_INTEGRATION=false bash
      unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --test --skip-alignment --skip-setup Expected:
      0 FAIL rows.
    status: pending
---

# Quality Gates Full Fix — 2026-03-10

**Goal:** Every repo passes unit tests with zero failures and meets coverage targets. No bypasses.

---

## Coverage Targets

| Category        | Target      | Exempt repos                                                                                            |
| --------------- | ----------- | ------------------------------------------------------------------------------------------------------- |
| T0–T3 libraries | >= 80%      | none                                                                                                    |
| Services / APIs | >= 70%      | market-tick-data-service, execution-service, features-commodity-service, market-data-processing-service |
| UIs             | smoke tests | no Python coverage                                                                                      |
| Codex / PM      | no tests    | testing_level=none                                                                                      |

---

## Issue Log

See [work/qg_issues.md](work/qg_issues.md) — updated live as agents complete.

---

## Agent Orchestration Protocol

1. **Master agent** (this Claude session): runs QG script, reads output, spawns fix agents, tracks log.
2. **Fix agents**: one per failing repo. Each agent:
   - Reads existing tests carefully before touching anything
   - Checks git log to see if other agents recently committed (wait 5 min if so)
   - Fixes root cause of each failing test (not the test expectation unless expectation is provably wrong)
   - Adds tests to close coverage gap — real tests that cover real logic paths
   - Re-runs `pytest tests/unit/ -v --cov=<pkg> --cov-report=xml` to verify
   - Commits with `git add` + `git commit` (NO quickmerge, NO git push without explicit instruction)
3. **No destructive git ops**: never `git reset --hard`, `git push --force`, `git branch -D` without user confirmation.
4. **Conflict avoidance**: if agent sees another agent's recent commit (within 5 min), it stages its own work with
   `git stash`, waits, then applies.

---

## Known Issues from Last Run (2026-03-09)

| Repo                               | Issues                           | Root Cause                                                          |
| ---------------------------------- | -------------------------------- | ------------------------------------------------------------------- |
| unified-market-interface           | 40% coverage, 15 test failures   | RC-A/B: stale wheel (IBKR `ib=` kwarg) + missing aave_utils exports |
| unified-trade-execution-interface  | 89% cov, 5 failures              | RC-B: stale wheel IbkrTradFiAdapter                                 |
| unified-trading-library            | 78% coverage                     | Below 80% threshold                                                 |
| execution-algo-library             | 72% coverage                     | Below 80% threshold                                                 |
| unified-sports-execution-interface | 76% coverage                     | Below 80% threshold                                                 |
| features-multi-timeframe-service   | 57% coverage, 1 env-leak failure | RC-C: CLOUD_PROVIDER env leak in test                               |
| features-onchain-service           | 39% coverage                     | Coverage gap                                                        |
| features-volatility-service        | 35% coverage                     | Coverage gap                                                        |
| ml-training-service                | 35% coverage                     | Coverage gap                                                        |
| pnl-attribution-service            | 46% coverage                     | Coverage gap + 1 env-leak failure                                   |
| position-balance-monitor-service   | 77% coverage, 1 env-leak         | RC-C: CLOUD_PROVIDER env leak                                       |
| alerting-service                   | 87% coverage, 2 failures         | RC-D: setup_events() not called before log_event() in test          |
| client-reporting-api               | 18% coverage                     | Major coverage gap                                                  |
| execution-results-api              | 66% coverage                     | Below 70% threshold                                                 |
| features-cross-instrument-service  | 65% coverage                     | Below 70% threshold                                                 |
| instruments-service                | 53% coverage                     | Coverage gap                                                        |
| trading-agent-service              | 50% coverage                     | Coverage gap                                                        |

All items above must be fully fixed. No threshold lowering. No skipping.
