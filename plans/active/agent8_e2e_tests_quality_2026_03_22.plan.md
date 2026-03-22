---
name: agent8-e2e-tests-quality
overview: "Add Playwright E2E tests for every service, API integration tests, OpenAPI schema parity, fix quality gates"
type: mixed
epic: citadel-grade-2026-03-22
status: active
locked_by: live-defi-rollout
locked_since: 2026-03-22
completion_gates:
  code: C5
  deployment: D2
  business: none
depends_on:
  - agent5-api-service-layer
  - agent6-mock-data-quality
repos:
  - unified-trading-system-ui
  - unified-trading-api
vision_ref: CITADEL_VISION_2026_03_22.md
todos:
  # ── Phase 0: API Quality Gates ──
  - id: a8-p0-api-quality-gates
    content: |
      - [ ] [AGENT] P0. Ensure unified-trading-api has a proper `scripts/quality-gates.sh` that runs: ruff lint, ruff format check, basedpyright typecheck, pytest with coverage. Currently only 1 test file exists (test_health.py). After Agent 5 adds integration tests, this should run them all. Target: 80%+ coverage.
    status: todo

  - id: a8-p0-api-basedpyright
    content: |
      - [ ] [AGENT] P0. Fix all basedpyright errors in unified-trading-api. The service layer (Protocol classes, mock/live implementations) must pass strict type checking. No `# type: ignore` to hide architectural violations.
    status: todo

  # ── Phase 1: UI Quality Gates ──
  - id: a8-p1-ui-build
    content: |
      - [ ] [AGENT] P0. Ensure `NEXT_PUBLIC_MOCK_API=false npx next build` succeeds (UI always calls API now, no MSW). Fix any TypeScript strict mode errors. Fix any import errors from removed MSW code. Fix any broken references to deleted routes.
    status: todo

  - id: a8-p1-ui-vitest
    content: |
      - [ ] [AGENT] P0. Ensure vitest passes: `CI=true npm test -- --run`. Fix any broken component tests that relied on MSW handlers. Component tests should use the API hooks with mocked fetch (via vitest's mock capabilities) not MSW.
    status: todo

  # ── Phase 2: Playwright E2E Tests (Mock Mode) ──
  - id: a8-p2-playwright-setup
    content: |
      - [ ] [AGENT] P0. Set up Playwright test infrastructure for mock-mode E2E testing:
        1. playwright.config.ts should start both: unified-trading-api (port 8030, CLOUD_MOCK_MODE=true) and Next.js dev server (port 3000)
        2. Tests run against http://localhost:3000 with API at http://localhost:8030
        3. Before each test suite: call POST /admin/reset to ensure clean state
        4. Create test fixtures for: admin login, client-full login, client-data-only login
    status: todo

  - id: a8-p2-test-auth-flow
    content: |
      - [ ] [AGENT] P0. Playwright test: Auth & Persona Flow
        1. Navigate to / → redirected to /login
        2. Login as admin → lands on /dashboard
        3. Verify all 7 lifecycle stages visible in nav
        4. Switch persona to client-data-only → verify only Acquire visible, rest shows "Upgrade"
        5. Switch persona to client-full → verify Acquire/Build/Run/Observe/Report visible, Manage hidden
        6. Click logout → redirected to /login
    status: todo

  - id: a8-p2-test-trading-flow
    content: |
      - [ ] [AGENT] P0. Playwright test: Trading Service Flow
        1. Login as admin → navigate to Run > Trading Terminal
        2. Verify: candlestick chart renders, order book renders, order entry form visible
        3. Click Positions tab → verify positions table renders with data (15+ rows)
        4. Click Orders tab → verify orders table renders with data
        5. Toggle to batch mode → verify banner "Viewing Batch Data" appears
        6. Toggle back to live → verify banner disappears
        7. Click "Manual Trade" → verify drawer opens
        8. Navigate back to Command Center → verify dashboard renders
    status: todo

  - id: a8-p2-test-research-flow
    content: |
      - [ ] [AGENT] P0. Playwright test: Research Service Flow
        1. Navigate to Build > Research & Backtesting
        2. Verify Research Hub renders with KPI cards
        3. Click ML Models tab → verify model list renders
        4. Click Experiments sub-tab → verify experiments table renders
        5. Click Strategies tab → verify backtest table renders
        6. Click Promote > Review Queue → verify candidates list renders
    status: todo

  - id: a8-p2-test-data-flow
    content: |
      - [ ] [AGENT] P1. Playwright test: Data Service Flow
        1. Navigate to Acquire > Data
        2. Verify Pipeline Status tab renders with service health
        3. Click Coverage Matrix tab → verify grid renders
        4. Click Markets tab → verify market data renders
    status: todo

  - id: a8-p2-test-reports-flow
    content: |
      - [ ] [AGENT] P1. Playwright test: Reports Service Flow
        1. Navigate to Report > Reports
        2. Verify P&L Attribution tab renders with data
        3. Click Settlement tab → verify settlements table renders
        4. Click Reconciliation tab → verify drift analysis renders
    status: todo

  - id: a8-p2-test-manage-flow
    content: |
      - [ ] [AGENT] P1. Playwright test: Manage Service Flow
        1. Login as admin → navigate to Manage > Clients
        2. Verify client list renders
        3. Click Users tab → verify user list renders
        4. Switch to client persona → verify Manage is not accessible (redirected or hidden)
    status: todo

  - id: a8-p2-test-observe-flow
    content: |
      - [ ] [AGENT] P1. Playwright test: Observe Service Flow
        1. Navigate to Observe > Risk Dashboard
        2. Verify exposure data renders
        3. Click Alerts tab → verify alerts list renders
        4. Click System Health tab → verify service health grid renders
    status: todo

  - id: a8-p2-test-admin-flow
    content: |
      - [ ] [AGENT] P1. Playwright test: Admin/Ops Flow
        1. Login as admin → navigate to Admin
        2. Verify admin dashboard renders
        3. Navigate to DevOps → verify deployment form renders
        4. Switch to client persona → verify Admin is completely hidden
    status: todo

  - id: a8-p2-test-reset-demo
    content: |
      - [ ] [AGENT] P0. Playwright test: Reset Demo Flow
        1. Login as admin
        2. Place a manual trade (creates new order in mock store)
        3. Navigate to Orders tab → verify new order appears
        4. Click "Reset Demo" button in debug footer
        5. Navigate to Orders tab → verify new order is gone, only seed data remains
    status: todo

  # ── Phase 3: API Integration Tests ──
  - id: a8-p3-api-integration
    content: |
      - [ ] [AGENT] P0. Verify all API integration tests pass (created by Agent 5). Run `cd unified-trading-api && bash scripts/quality-gates.sh`. Ensure:
        1. Every route file has corresponding test file
        2. Tests cover: happy path, filtering, pagination, org scoping
        3. Coverage ≥ 80%
        4. basedpyright clean
    status: todo

  # ── Phase 4: OpenAPI Schema Parity ──
  - id: a8-p4-openapi-parity
    content: |
      - [ ] [AGENT] P1. Generate OpenAPI spec from unified-trading-api (`GET /openapi.json`). Verify:
        1. All routes are documented in the spec
        2. Response schemas match actual mock-mode responses
        3. UI TypeScript types (if generated from OpenAPI) are up to date
        4. Add a CI test that validates spec parity: start API in mock mode, call every endpoint, validate response against OpenAPI schema.
    status: todo

  # ── Phase 5: Cross-Service E2E Smoke ──
  - id: a8-p5-smoke-test
    content: |
      - [ ] [AGENT] P1. Create a smoke test script that validates the full stack works:
        1. Start unified-trading-api (port 8030, mock mode)
        2. Start Next.js dev (port 3000)
        3. Call POST /admin/reset
        4. Run all Playwright E2E tests
        5. Call POST /admin/reset (cleanup)
        This script should be runnable as `bash scripts/e2e-smoke.sh` from the unified-trading-system-ui repo.
    status: todo
isProject: false
---

# Notes & Context

## Absorbed from prior plans

- cicd_e2e_testing_master_2026_03_13: E2E testing plan (8% done) — superseded by this plan
- production_mock_e2e_plan_d90c8f20: Mock E2E plan (85% done) — absorb completed work
- plan_f_ui_quality_hardening: UI quality gates, TypeScript strict mode
- quality_gates_systemic_remediation_2026_03_16: Quality gate fixes

## Current test state

- unified-trading-api: 1 test file (test_health.py)
- unified-trading-system-ui: Jest config exists, Playwright config exists
- 3 satellite UIs missing vitest (trading-analytics-ui, execution-analytics-ui, batch-audit-ui) — no longer relevant
  since these are being archived

## Key constraint

- All E2E tests run against mock mode (CLOUD_MOCK_MODE=true, no real cloud services)
- POST /admin/reset is the test fixture — every test suite starts clean
- Playwright must use `pool: "forks"` (not threads) to prevent zombie processes
