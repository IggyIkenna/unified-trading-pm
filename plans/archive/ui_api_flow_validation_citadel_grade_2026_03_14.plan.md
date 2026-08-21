---
doc_type: plan
title: ui-api-flow-validation-citadel-grade
summary: 'Citadel-grade 3-layer testing framework: UI mock tests validate UX behavior, API mock-mode tests validate endpoint
  contracts, real-flow tests validate end-to-end wiring. No critical UI interaction exists without executable test evidence.
  Mock-only passes cannot represent production readiness.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-14'
type: mixed
epic: epic-code-completion
completion_gates: {code: C4, deployment: D2, business: none}
repo_gates:
- {repo: unified-trading-pm, code: C0, deployment: none, business: none, readiness_note: 'Checker script, manifest template, CI integration.'}
- {repo: system-integration-tests, code: C0, deployment: none, business: none, readiness_note: Real-flow E2E tests for critical journeys.}
depends_on: [ui-api-alerting-observability-2026-03-14]
supersedes: []
todos:
- {id: ph1-manifest-template, content: '- [x] [AGENT] P0. Create ui-api-flow-test-manifest.yaml template in PM root. Columns: repo, journey_id, page_or_route, control_id, interaction_type, expected_request, expected_response_contract, expected_ui_update, required_layers, criticality. Pre-populate deployment-ui + logs-dashboard-ui.

    ', status: done}
- {id: ph1-critical-journey-mapping, content: '- [x] [AGENT] P0. Map critical journeys for all 12 UIs. Source from ui-api-mapping.json + Playwright test files. Manual override for criticality only. Output: populated manifest rows per UI repo.

    ', status: done}
- {id: ph1-severity-taxonomy, content: '- [x] [AGENT] P1. Define severity taxonomy: critical (blocks trading/deploy), high (degrades UX, data staleness), medium (cosmetic, non-blocking). Tie to real-flow cadence: critical = every staging deploy, high = nightly, medium = weekly.

    ', status: done}
- {id: ph2-checker-script, content: '- [x] [AGENT] P0. Create check_ui_api_flow_coverage.py in PM scripts/checkers/. Reads manifest, scans repos for Playwright/vitest/pytest files, scores against COV-001 through COV-003, BEH-001 through BEH-004, SEP-001 through SEP-003. Outputs JSON + markdown report.

    ', status: done}
- {id: ph2-ci-warning, content: '- [x] [AGENT] P1. Wire checker into PM quality flow as WARNING (non-blocking). Run in SIT validation. Output scorecard to GCS artifacts.

    ', status: done}
- {id: ph2-auto-discovery, content: '- [x] [AGENT] P1. Auto-discovery mode: checker scans ui-api-mapping.json + Playwright test directories. No manual manifest entry required for discovered journeys. Manual override only for criticality escalation.

    ', status: done}
- {id: ph3-network-evidence, content: '- [x] [AGENT] P0. Network evidence parser: extract request/response pairs from Playwright HAR or page.route() intercepts. Validate against UAC/UIC contract models. Flag mock fixtures that drift from API mock-mode responses.

    ', status: done}
- {id: ph3-triad-assertions, content: '- [x] [AGENT] P0. Request/response/ui-update triad assertions. Every critical journey must prove: (1) correct request sent, (2) contract-valid response received, (3) UI state updated. No-op controls (click with no effect) flagged as BEH-004.

    ', status: done}
- {id: ph3-fixture-drift, content: '- [x] [AGENT] P1. Fixture drift prevention: UI mock fixtures must be generated from API mock-mode responses (one source of truth). Build-time validation that mock fixture schemas match UIC/UAC contract models. Fail on schema mismatch.

    ', status: done}
- {id: ph3-critical-gap-blocking, content: '- [x] [AGENT] P1. Critical-gap blocking: if a critical journey has zero real-flow tests, checker emits BLOCK (not just WARNING). Prevents promotion to staging.

    ', status: done}
- {id: ph4-blocking-gate, content: '- [ ] [AGENT] P0. Promote checker from WARNING to BLOCKING gate in PM quality flow. Score < 75 = FAIL (blocks merge). Score 75-89 = WARNING. Score >= 90 = PASS (citadel-grade).

    ', status: todo}
- {id: ph4-sit-linkage, content: '- [ ] [AGENT] P1. Wire real-flow tests into SIT suite. Critical journeys run on every staging deploy. High journeys in nightly SIT. Medium journeys in weekly SIT.

    ', status: todo}
- {id: ph4-scorecard-trends, content: '- [ ] [AGENT] P2. Scorecard trend tracking. Persist scores to GCS on each run. Show delta in PR comments. Block regression (score drop > 5 points).

    ', status: todo}
- {id: ph1-5-mock-state-store, content: '- [x] [AGENT] P0. MockStateStore in UTL: seed data + mutations + JSONL persistence. deterministic mode (CI, no persistence) vs interactive mode (UAT, persists to .local-dev-cache/). MOCK_STATE_MODE env var. Thread-safe. Reset on dev-stop --clean.

    ', status: done}
- {id: ph1-5-wire-apis, content: '- [ ] [AGENT] P0. Wire MockStateStore into all 9 APIs. POST/PUT/DELETE mutate state, GET returns seed + mutations. Per-UI stateful scenarios: deployment-api (deploy→status→logs), alerting (trigger→route→deliver), trading-analytics (trade→settle→report), execution-results (submit→fill→reconcile), batch-audit (event→log→summary), ml-training (train→evaluate→deploy model).

    ', status: partial}
- {id: ph1-5-mode-axis, content: '- [ ] [AGENT] P1. Add 5th mode axis (MOCK_STATE_MODE=deterministic|interactive) to dev-start.sh presets. CI preset uses deterministic. Mock preset uses interactive. Update dev-status.sh to show 5th axis. Update codex local-dev.md.

    ', status: partial}
- {id: ph1-5-gitignore, content: '- [x] [AGENT] P0. Add .local-dev-cache/ to workspace .gitignore and all repo .gitignores. Add --clean flag to dev-stop.sh. Add --reset flag to dev-start.sh.

    ', status: done}
isProject: false
---

# Citadel-Grade UI/API Flow Validation Testing

## Context

The unified trading system has 12 UIs, 9+ APIs, and 22 services. Current testing validates individual layers in
isolation: vitest for UI components, pytest for API endpoints, Playwright for smoke tests. But no systematic framework
validates that a user interaction on a UI page actually triggers the correct API call, receives a contract-valid
response, and updates the UI state accordingly. Mock-only test suites can pass while real flows are broken.

This plan establishes a 3-layer testing framework that closes that gap. It depends on Plan 7
(UI/API/Alerting/Observability) for `createApiClient`, mock data infrastructure, and integration test patterns.

---

## Five Principles

**P1: UI mock tests validate UX behavior, not backend truth.** Vitest + jsdom tests prove that components render,
respond to user input, and display expected states. They use mock fixtures and cannot claim API correctness.

**P2: API mock-mode tests validate endpoint behavior and response contracts.** pytest with `CLOUD_MOCK_MODE=true` proves
that API routes accept valid requests, return contract-compliant responses (validated against UIC/UAC models), and
handle error cases. They cannot claim UI rendering correctness.

**P3: Real-flow tests validate interaction wiring and live/staging data movement.** Playwright tests against running
services (local or staging) prove that clicking a button sends the correct HTTP request, receives a real response, and
the UI updates accordingly. These are the only tests that prove end-to-end correctness.

**P4: Promotion requires all three layers to pass for critical journeys.** A journey rated "critical" cannot be promoted
to staging unless it has passing tests in all three layers. Mock-only coverage is necessary but not sufficient.

**P5: Mock fixture schemas must be validated against UIC/UAC contract models at build time.** UI mock fixtures drift
from real API responses over time. Build-time validation catches this drift before it reaches test execution.

---

## Non-Overlap Contract

Each test layer has a defined scope. Violations are flagged by the checker.

| Layer       | Can Claim                                        | Cannot Claim                           |
| ----------- | ------------------------------------------------ | -------------------------------------- |
| `ui_mock`   | Component renders, user input handled, state set | API correctness, data freshness        |
| `api_mock`  | Endpoint accepts request, returns valid contract | UI renders result, real data moves     |
| `real_flow` | Full interaction works end-to-end                | Component-level edge cases, unit logic |

**Overlap violations:**

- A `ui_mock` test that asserts on API response body content (should be `api_mock` or `real_flow`)
- An `api_mock` test that renders a React component (should be `ui_mock`)
- A `real_flow` test that mocks the HTTP layer (defeats the purpose; should be `api_mock`)

---

## Test Layer Policy Matrix

| Layer       | Tool           | Mandatory Assertions                                         | Fixture Source                               |
| ----------- | -------------- | ------------------------------------------------------------ | -------------------------------------------- |
| `ui_mock`   | vitest + jsdom | Component mounts, user event fires, DOM state updates        | Mock fixtures (generated from API mock-mode) |
| `api_mock`  | pytest + mock  | Status code, response schema validates against UIC/UAC model | `CLOUD_MOCK_MODE=true`                       |
| `real_flow` | Playwright     | Request sent, response received, UI element updated (triad)  | Live/staging services                        |

---

## Checker Rules

### Coverage Rules (COV)

| Rule    | Description                                                          | Severity |
| ------- | -------------------------------------------------------------------- | -------- |
| COV-001 | Every critical journey has at least one test in each of the 3 layers | BLOCK    |
| COV-002 | Every high journey has at least `ui_mock` + `api_mock` tests         | WARNING  |
| COV-003 | Every medium journey has at least one test in any layer              | INFO     |

### Behavior Rules (BEH)

| Rule    | Description                                                                    | Severity |
| ------- | ------------------------------------------------------------------------------ | -------- |
| BEH-001 | `real_flow` tests must assert on network request (HAR or page.route intercept) | BLOCK    |
| BEH-002 | `real_flow` tests must assert on response status and at least one body field   | BLOCK    |
| BEH-003 | `real_flow` tests must assert on UI state change after response                | WARNING  |
| BEH-004 | No-op controls detected (click handler with no observable effect)              | WARNING  |

### Separation Rules (SEP)

| Rule    | Description                                              | Severity |
| ------- | -------------------------------------------------------- | -------- |
| SEP-001 | `ui_mock` tests must not make real HTTP calls            | BLOCK    |
| SEP-002 | `api_mock` tests must not import React/Vue/DOM libraries | BLOCK    |
| SEP-003 | `real_flow` tests must not mock the HTTP transport layer | WARNING  |

---

## Scoring Model

**Total: 100 points.** Citadel-grade >= 90, warning 75-89, fail < 75.

| Category                    | Points | Breakdown                                                               |
| --------------------------- | ------ | ----------------------------------------------------------------------- |
| Coverage (COV-001..003)     | 40     | Critical: 20pts (all-or-nothing per journey), High: 12pts, Medium: 8pts |
| Interaction Behavior (BEH)  | 40     | BEH-001: 15pts, BEH-002: 10pts, BEH-003: 10pts, BEH-004: 5pts           |
| Separation Compliance (SEP) | 20     | SEP-001: 8pts, SEP-002: 7pts, SEP-003: 5pts                             |

**Scoring logic:**

- BLOCK violations in any category: category score = 0
- WARNING violations: deduct proportional points (e.g., 1 of 5 journeys missing BEH-003 = -2pts)
- INFO violations: no point deduction, reported only

---

## Fixture Drift Prevention

UI mock fixtures must be generated from API mock-mode responses to prevent drift:

```
API mock-mode response (pytest) --> fixture generator --> UI mock fixture (vitest)
                                                     --> schema validator (UIC/UAC models)
```

Build-time check: if a UI mock fixture's schema does not match the corresponding UIC/UAC model, the build fails. This
ensures that UI tests always use structurally valid data, even though the values are synthetic.

---

## Auto-Discovery

The checker auto-discovers journeys by scanning:

1. `ui-api-mapping.json` for declared UI-to-API relationships
2. Playwright test files (`*.spec.ts`, `*.test.ts` in `e2e/` or `tests/`) for `page.goto()` + `page.route()` pairs
3. vitest files for component-level interaction tests

Manual override: the manifest `criticality` field can be set to escalate a journey (e.g., from auto-detected "medium" to
manually declared "critical"). Auto-detected journeys default to "medium" unless escalated.

---

## Real-Flow Cadence

| Criticality | When                 | Example                                     |
| ----------- | -------------------- | ------------------------------------------- |
| critical    | Every staging deploy | Deploy service, kill switch, order execute  |
| high        | Nightly SIT          | Log filtering, alert routing, config save   |
| medium      | Weekly SIT           | Branding, tooltips, non-critical navigation |

---

## 5th Mode Axis: Mock State Persistence

Beyond the 4 existing mode axes (UI data, UI auth, API data, API auth), stateful mock testing requires a 5th axis:

| Axis           | Env Var | Values | Purpose                                    |
| -------------- | ------- | ------ | ------------------------------------------ |
| **Mock state** |         | /      | Whether mutations persist between requests |

**Deterministic (CI/smoke):** Same seed, same responses every time. POST returns success but state resets on next GET.
Assertions compare against known seed values. No disk writes. Idempotent — run 100 times, same result.

**Interactive (UAT/dev):** Mutations persist to . POST a deployment, see it on subsequent GET. Toggle a kill switch, see
the status change. State persists within session, resets on .

### Presets

| Preset | UI data | UI auth | API data | API auth | Mock state        |
| ------ | ------- | ------- | -------- | -------- | ----------------- |
|        | mock    | skip    | mock     | disabled | **deterministic** |
|        | mock    | skip    | mock     | disabled | **interactive**   |
|        | mock    | skip    | real     | disabled | N/A               |
|        | live    | real    | real     | enabled  | N/A               |

### Per-UI Stateful Scenarios

Each UI has domain-specific flows that require state persistence in interactive mode:

| UI                                    | Key Stateful Flow                       | What persists                                        |
| ------------------------------------- | --------------------------------------- | ---------------------------------------------------- |
| deployment-ui                         | Deploy → status updates → logs          | deployment state machine (pending→building→deployed) |
| execution-analytics-ui                | Submit instruction → fill events → P&L  | instruction status, fill records                     |
| logs-dashboard-ui                     | Events stream in → filter → search      | lifecycle event log grows over time                  |
| live-health-monitor-ui                | Toggle kill switch → status change      | kill switch state, circuit breaker state             |
| trading-analytics-ui                  | Execute trade → settlement → report     | trade records, settlement positions                  |
| ml-training-ui                        | Start training → progress → model ready | training run status, model registry                  |
| ml-inference-ui (via ml-training-ui)  | Deploy model → serve predictions        | model deployment status                              |
| alerting (via live-health-monitor-ui) | Alert fires → routes → delivery record  | alert history, delivery status                       |
| batch-audit-ui                        | Batch job runs → audit trail grows      | job records, audit events                            |
| settlement-ui                         | Position opens → invoice generates      | positions, invoices                                  |
| onboarding-ui                         | Configure venue → save → confirm        | venue configuration state                            |
| client-reporting-ui                   | Generate report → download              | generated reports list                               |
| strategy-ui                           | Create strategy → backtest → results    | strategy configs, backtest results                   |

---

## Coordination Note

This plan depends on Plan 7 (UI/API/Alerting/Observability) for:

- `createApiClient` in `@unified-admin/core` (P0.4 done)
- Mock data infrastructure in each UI (vitest fixtures)
- Integration test template (P5.12)
- `ui-api-mapping.json` as the source of truth for UI-to-API relationships

Phase 1 of this plan can begin once Plan 7 P0.4 (createApiClient) and P6.4 (smoke tests) are complete.
