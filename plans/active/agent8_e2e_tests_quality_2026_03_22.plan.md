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

# Finish line (executive)

**Epic close-out SSOT:** `CITADEL_VISION_2026_03_22.md` § **Completion path — finishing the Citadel epic**.

Until all items below are **done**, the epic is **not** archive-eligible at C5.

1. **P1 — UI quality** — `a8-p1-ui-build`, `a8-p1-ui-vitest` (production-style build + vitest green).
2. **P8 — Verification** — `a8-p8-qg-unified-trading-api`, `a8-p8-qg-unified-trading-system-ui`, `a8-p8-verify-no-redundant-impl`.
3. **P8 — Tier / demo hardening** — `a8-p8-sit-tier-readiness` (Playwright readiness + smoke).
4. **Any other `status: todo`** in this file — grep `status: todo` and burn down; refresh counts before each sprint.

Phase 0–2 items are largely **done**; remaining work is **UI QG**, **repo-wide verification**, and **readiness/tier E2E**.

todos:
  # ── Phase 0: API Quality Gates ──
  - id: a8-p0-api-quality-gates
    content: |
      - [x] [AGENT] P0. Ensure unified-trading-api has a proper `scripts/quality-gates.sh` that runs: ruff lint, ruff format check, basedpyright typecheck, pytest with coverage. Currently only 1 test file exists (test_health.py). After Agent 5 adds integration tests, this should run them all. Target: 80%+ coverage.
    status: done

  - id: a8-p0-api-basedpyright
    content: |
      - [x] [AGENT] P0. Fix all basedpyright errors in unified-trading-api. The service layer (Protocol classes, mock/live implementations) must pass strict type checking. No `# type: ignore` to hide architectural violations.
    status: done

  # ── Phase 1: UI Quality Gates ──
  - id: a8-p1-ui-build
    content: |
      - [ ] [AGENT] P0. Ensure `NEXT_PUBLIC_MOCK_API=false npx next build` succeeds (UI always calls API now, no MSW). Fix any TypeScript strict mode errors. Fix any import errors from removed MSW code. Fix any broken references to deleted routes.
    status: todo

  - id: a8-p1-ui-vitest
    content: |
      - [ ] [AGENT] P0. Ensure vitest passes: `CI=true npm test -- --run`. Fix any broken component tests that relied on MSW handlers. Component tests should use the API hooks with mocked fetch (via vitest's mock capabilities) not MSW.
    status: todo

  # ── DEPENDENCY GATE: Phase 2 requires Agents 1, 5, 6 ──────────────────────
  # STOP HERE if these are not complete:
  #   - Agent 1: shell navigation working (lifecycle nav, tab routing, debug footer)
  #   - Agent 5: API service layer working (all routes return data in mock mode)
  #   - Agent 6: seed data comprehensive (at least positions, orders, strategies, alerts)
  # CHECK: Start API with CLOUD_MOCK_MODE=true → curl http://localhost:8030/health returns ok
  # CHECK: Start UI → navigate to /dashboard → page renders with data (not empty/error)
  # CHECK: Click lifecycle nav → lands on service first tab (not card landing)
  # If upstream agents aren't done, stay on Phase 0-1 (quality gates, build fixes) and wait.
  # Phase 0-1 have NO upstream deps and can run immediately.
  # ─────────────────────────────────────────────────────────────────────────────
  # ── Phase 2: Playwright E2E Tests (Mock Mode) ──
  - id: a8-p2-playwright-setup
    content: |
      - [x] [AGENT] P0. Set up Playwright test infrastructure for mock-mode E2E testing:
        1. playwright.config.ts should start both: unified-trading-api (port 8030, CLOUD_MOCK_MODE=true) and Next.js dev server (port 3000)
        2. Tests run against http://localhost:3000 with API at http://localhost:8030
        3. Before each test suite: call POST /admin/reset to ensure clean state
        4. Create test fixtures for: admin login, client-full login, client-data-only login
    status: done

  - id: a8-p2-test-auth-flow
    content: |
      - [x] [AGENT] P0. Playwright test: Auth & Persona Flow
        1. Navigate to / → redirected to /login
        2. Login as admin → lands on /dashboard
        3. Verify all 7 lifecycle stages visible in nav
        4. Switch persona to client-data-only → verify only Acquire visible, rest shows "Upgrade"
        5. Switch persona to client-full → verify Acquire/Build/Run/Observe/Report visible, Manage hidden
        6. Click logout → redirected to /login
    status: done

  - id: a8-p2-test-trading-flow
    content: |
      - [x] [AGENT] P0. Playwright test: Trading Service Flow
        1. Login as admin → navigate to Run > Trading Terminal
        2. Verify: candlestick chart renders, order book renders, order entry form visible
        3. Click Positions tab → verify positions table renders with data (15+ rows)
        4. Click Orders tab → verify orders table renders with data
        5. Toggle to batch mode → verify banner "Viewing Batch Data" appears
        6. Toggle back to live → verify banner disappears
        7. Click "Manual Trade" → verify drawer opens
        8. Navigate back to Command Center → verify dashboard renders
    status: done

  - id: a8-p2-test-research-flow
    content: |
      - [x] [AGENT] P0. Playwright test: Research Service Flow
        1. Navigate to Build > Research & Backtesting
        2. Verify Research Hub renders with KPI cards
        3. Click ML Models tab → verify model list renders
        4. Click Experiments sub-tab → verify experiments table renders
        5. Click Strategies tab → verify backtest table renders
        6. Click Promote > Review Queue → verify candidates list renders
    status: done

  - id: a8-p2-test-data-flow
    content: |
      - [x] [AGENT] P1. Playwright test: Data Service Flow
        1. Navigate to Acquire > Data
        2. Verify Pipeline Status tab renders with service health
        3. Click Coverage Matrix tab → verify grid renders
        4. Click Markets tab → verify market data renders
    status: done

  - id: a8-p2-test-reports-flow
    content: |
      - [x] [AGENT] P1. Playwright test: Reports Service Flow
        1. Navigate to Report > Reports
        2. Verify P&L Attribution tab renders with data
        3. Click Settlement tab → verify settlements table renders
        4. Click Reconciliation tab → verify drift analysis renders
    status: done

  - id: a8-p2-test-manage-flow
    content: |
      - [x] [AGENT] P1. Playwright test: Manage Service Flow
        1. Login as admin → navigate to Manage > Clients
        2. Verify client list renders
        3. Click Users tab → verify user list renders
        4. Switch to client persona → verify Manage is not accessible (redirected or hidden)
    status: done

  - id: a8-p2-test-observe-flow
    content: |
      - [x] [AGENT] P1. Playwright test: Observe Service Flow
        1. Navigate to Observe > Risk Dashboard
        2. Verify exposure data renders
        3. Click Alerts tab → verify alerts list renders
        4. Click System Health tab → verify service health grid renders
    status: done

  - id: a8-p2-test-admin-flow
    content: |
      - [x] [AGENT] P1. Playwright test: Admin/Ops Flow
        1. Login as admin → navigate to Admin
        2. Verify admin dashboard renders
        3. Navigate to DevOps → verify deployment form renders
        4. Switch to client persona → verify Admin is completely hidden
    status: done

  - id: a8-p2-test-reset-demo
    content: |
      - [x] [AGENT] P0. Playwright test: Reset Demo Flow
        1. Login as admin
        2. Place a manual trade (creates new order in mock store)
        3. Navigate to Orders tab → verify new order appears
        4. Click "Reset Demo" button in debug footer
        5. Navigate to Orders tab → verify new order is gone, only seed data remains
    status: done

  # ── Phase 3: API Integration Tests ──
  - id: a8-p3-api-integration
    content: |
      - [x] [AGENT] P0. Verify all API integration tests pass (created by Agent 5). Run `cd unified-trading-api && bash scripts/quality-gates.sh`. Ensure:
        1. Every route file has corresponding test file
        2. Tests cover: happy path, filtering, pagination, org scoping
        3. Coverage ≥ 80%
        4. basedpyright clean
    status: done

  # ── Phase 4: OpenAPI Schema Parity & Codegen Pipeline ──
  - id: a8-p4-openapi-parity
    content: |
      - [x] [AGENT] P1. Generate OpenAPI spec from unified-trading-api (`GET /openapi.json`). Verify:
        1. All routes are documented in the spec
        2. Response schemas match actual mock-mode responses
        3. UI TypeScript types (if generated from OpenAPI) are up to date
        4. Add a CI test that validates spec parity: start API in mock mode, call every endpoint, validate response against OpenAPI schema.
    status: todo
  - id: a8-p4-codegen-pipeline-run
    content: |
      - [x] [AGENT] P0. Run the SSOT codegen pipelines AFTER Agents 5-6 have finished their work. This is critical — without it, the UI will have stale types and reference data.

        Pipeline 1: API → UI TypeScript types
        ```bash
        cd unified-trading-api && CLOUD_MOCK_MODE=true .venv/bin/python -m unified_trading_api.main &
        sleep 3
        curl http://localhost:8030/openapi.json > ../unified-trading-system-ui/lib/registry/openapi.json
        cd ../unified-trading-system-ui && npm run generate:types
        kill %1
        ```

        Pipeline 2: UAC → UI reference data
        ```bash
        cd unified-api-contracts
        .venv/bin/python scripts/generate_ui_reference_data.py --output ../unified-trading-system-ui/lib/registry/ui-reference-data.json
        ```

        Pipeline 3: Persona alignment verification
        - Compare auth-api `mock_data.py` org IDs with unified-trading-api `personas.py` org IDs
        - Compare UI `hooks/use-auth.ts` persona definitions with both APIs
        - All three MUST use identical org_id, persona name, and entitlement key values

        If any pipeline fails, FIX the source and re-run. Do NOT proceed to E2E tests with stale types.
    status: done
  - id: a8-p4-auth-alignment-test
    content: |
      - [x] [AGENT] P0. Add a test that verifies persona/org alignment across all 3 APIs:
        1. Start auth-api (port 8200) and unified-trading-api (port 8030) in mock mode
        2. Login as each persona via auth-api `POST /auth/login` → get JWT
        3. Call unified-trading-api `GET /positions/active` with that JWT
        4. Verify: admin sees all data, client-full sees only acme data, client-data-only sees only beta data
        5. Verify: auth-api org IDs match unified-trading-api org_id filtering
        This catches the case where the two APIs have different persona definitions that silently break filtering.
    status: done

  - id: a8-p4-test-realtime-feed
    content: |
      - [x] [AGENT] P0. Playwright test: Real-Time Trading Feed
        1. Login as admin → navigate to Trading Terminal
        2. Wait 3 seconds → verify at least one price update has occurred (chart or ticker value changed)
        3. Verify order book has bid/ask levels populated
        4. Switch instrument → verify prices update for new instrument
        5. This test validates the WebSocket mock feed is working end-to-end.
    status: done
  - id: a8-p4-test-batch-live-switch
    content: |
      - [x] [AGENT] P0. Playwright test: Batch/Live Data Switch
        1. Login as admin → navigate to Trading Terminal in live mode
        2. Note the current positions count and PnL value
        3. Toggle to batch mode → verify "Viewing Batch Data" banner appears
        4. Verify positions count or PnL value has CHANGED (batch data is different from live)
        5. Toggle back to live → verify banner disappears and original values return
        6. This validates the batch/live collection separation works end-to-end.
    status: done
  # ── Phase 5: Cross-Service E2E Smoke ──
  - id: a8-p5-smoke-test
    content: |
      - [x] [AGENT] P1. Create a smoke test script that validates the full stack works:
        1. Start unified-trading-api (port 8030, mock mode)
        2. Start Next.js dev (port 3000)
        3. Call POST /admin/reset
        4. Run all Playwright E2E tests
        5. Call POST /admin/reset (cleanup)
        This script should be runnable as `bash scripts/e2e-smoke.sh` from the unified-trading-system-ui repo.
    status: done
  # ── Phase 6: Org Isolation Matrix, Codegen Pipelines, Performance (Gap-Closing) ──
  - id: a8-p6-org-isolation-matrix
    content: |
      - [x] [AGENT] P0. Playwright test: Full Org Isolation Matrix — this is CRITICAL for demo credibility. BlackRock-grade means clients NEVER see each other's data.
        1. Login as client-full (org: acme) → navigate to every service → verify ALL data has org_id matching "acme"
        2. Login as client-data-only (org: beta) → verify only data service accessible, all data has org_id "beta"
        3. Login as client-premium (org: vertex) → verify data + execution accessible, all data org_id "vertex"
        4. Login as admin → verify ALL data visible across all orgs
        5. For EACH service: Positions, Orders, Strategies, Alerts, PnL — verify org filtering works
        6. Test cascading: select org "acme" in global scope → all pages filter to acme. Change to "vertex" → all pages update.
        7. This test catches the case where one service page shows unfiltered data — a demo-killing bug.
    status: todo
  - id: a8-p6-codegen-pipeline-create
    content: |
      - [x] [AGENT] P0. Verify and CREATE codegen pipeline scripts if they don't exist:
        1. Check `unified-api-contracts/scripts/generate_ui_reference_data.py` — if missing, create it:
           - Read UAC registry Python modules (venue registry, instrument types, error codes, enums)
           - Output structured JSON to `--output` path
           - Must be runnable as `.venv/bin/python scripts/generate_ui_reference_data.py --output <path>`
        2. Check `unified-trading-system-ui/package.json` for `"generate:types"` script — if missing:
           - `npm install -D openapi-typescript`
           - Add script: `"generate:types": "openapi-typescript lib/registry/openapi.json -o lib/types/api-generated.ts"`
        3. Check `unified-trading-api/scripts/verify_persona_alignment.py` — if missing, create it:
           - Compare org IDs between auth-api mock_data.py and unified-trading-api personas.py
           - Compare persona names and entitlements
           - Exit 0 if aligned, exit 1 with diff on mismatch
        4. Run ALL three pipelines and verify output is valid
    status: done
  - id: a8-p6-error-state-tests
    content: |
      - [x] [AGENT] P1. Playwright tests for error states:
        1. Block API endpoint (intercept /positions/active → 500) → verify error boundary shows "Something went wrong" with Retry button
        2. Click Retry → verify data loads successfully
        3. Login as client-data-only → navigate to /services/trading/overview → verify "Upgrade" card shown (not blank page or 403)
        4. Login as client-full → navigate to /admin → verify redirect to /dashboard
    status: done
  - id: a8-p6-responsive-tests
    content: |
      - [x] [AGENT] P1. Playwright tests for responsive layout:
        1. Set viewport to 768x1024 (tablet) → verify hamburger menu appears, lifecycle nav is hidden
        2. Click hamburger → verify slide-out drawer with service navigation
        3. Navigate to Trading Terminal at tablet viewport → verify chart renders, layout stacks vertically
        4. Verify data tables have horizontal scroll (no broken layouts)
    status: todo
  - id: a8-p6-bundle-size
    content: |
      - [ ] [AGENT] P1. Performance validation:
        1. Run `NEXT_PUBLIC_MOCK_API=true npx next build` and capture output
        2. Parse chunk sizes from build output
        3. Flag any chunk > 500KB as a warning
        4. Verify charting components use dynamic imports (not in initial bundle)
        5. Add this as a CI check in the smoke test script
    status: todo
  - id: a8-p6-latency-test
    content: |
      - [ ] [AGENT] P1. Playwright test: Latency simulation makes skeletons visible:
        1. Start API with MOCK_LATENCY_MS=300
        2. Navigate to any service page
        3. Verify skeleton placeholder is visible for at least 200ms before data appears
        4. This validates that the skeleton loading components actually work visually
    status: todo
  - id: a8-p6-export-tests
    content: |
      - [ ] [AGENT] P1. Playwright tests for export functionality:
        1. Navigate to Positions table → click "Export" → select "CSV" → verify download triggers
        2. Navigate to Positions table → click "Export" → select "Excel" → verify .xlsx download triggers
        3. Navigate to Reports > P&L → click "Generate Report" → verify modal → submit → verify download toast
        4. Navigate to Reports > P&L → click "Print Report" → verify print dialog opens (or print-friendly layout renders)
    status: todo
  # ── Phase 7: Full Registry Coverage Tests & Sync Pipeline (Gap-Closing) ──
  - id: a8-p7-sync-pipeline-run
    content: |
      - [ ] [AGENT] P0. Run the FULL SSOT sync pipeline AFTER Agents 5-6 complete. This is the critical integration step:
        1. Run `python unified-trading-pm/scripts/openapi/generate_ui_reference_data.py` — sync UAC registries to UI
        2. Verify output has ALL instruments from representative_sample.py (~40 specs)
        3. Start unified-trading-api, fetch OpenAPI spec, generate TypeScript types:
           `curl http://localhost:8030/openapi.json > ../unified-trading-system-ui/lib/registry/openapi.json`
           `cd ../unified-trading-system-ui && npm run generate:types`
        4. Run `python unified-trading-pm/scripts/validation/validate-strategy-manifest.py` — verify 50+ strategies
        5. Run `python unified-trading-pm/scripts/manifest/check-strategy-instruments.py` — verify instrument refs
        6. Run `python unified-trading-pm/scripts/checkers/check_ui_api_flow_coverage.py` — verify UI→API coverage
        7. Run `python unified-trading-pm/scripts/validation/check-import-patterns.py` — verify no import violations
        8. If ANY pipeline fails, FIX the source and re-run. Do NOT proceed to E2E tests with stale data.
        DEPENDENCY: Agents 5 and 6 must be substantially complete.
    status: todo
  - id: a8-p7-indicator-tests
    content: |
      - [ ] [AGENT] P1. Playwright test: Technical indicators on Trading Terminal:
        1. Navigate to Trading Terminal → verify candlestick chart renders
        2. Click "SMA" indicator toggle → verify SMA overlay line appears on chart
        3. Click "BB" (Bollinger Bands) → verify upper/lower bands appear
        4. Click "SMA" again → verify SMA overlay disappears (toggle off)
        DEPENDENCY: Agent 2 must implement indicators (a2-p7-technical-indicators).
    status: todo
  - id: a8-p7-full-instrument-tests
    content: |
      - [ ] [AGENT] P0. Playwright test: Full instrument coverage:
        1. Navigate to Trading Terminal → open instrument selector dropdown
        2. Verify instruments are grouped by category (CeFi Spot, CeFi Perps, TradFi, DeFi)
        3. Verify at least 30 instruments are listed (from ui-reference-data.json)
        4. Select a TradFi instrument (e.g., AAPL) → verify chart loads with candle data
        5. Select a DeFi instrument (e.g., WETH-USDC) → verify chart loads
        DEPENDENCY: Agents 5-6 must seed data for all instruments. Agent 2 must wire instrument selector.
    status: todo
  - id: a8-p7-strategy-scale-tests
    content: |
      - [ ] [AGENT] P0. Playwright test: 50+ strategy scale:
        1. Navigate to Dashboard → verify strategy performance table shows 50+ rows
        2. Verify table is virtualized (no lag with 50+ rows — TanStack Table handles this)
        3. Navigate to Research > Strategies → verify 50+ strategies listed
        4. Filter by asset class "DeFi" → verify only DeFi strategies shown
        5. Navigate to Promote > Candidates → verify candidates from multiple asset classes
        DEPENDENCY: Agent 6 must expand strategies to 50+. Agent 1 must create DataTable.
    status: todo
  - id: a8-p7-realtime-pnl-test
    content: |
      - [x] [AGENT] P0. Playwright test: Real-time PnL propagation (validates server-side calculation end-to-end):
        1. Login as admin → navigate to Dashboard
        2. Note the current total PnL value displayed
        3. Wait 5 seconds (WebSocket ticks update prices → server recalculates PnL → emits on analytics channel)
        4. Verify the PnL value has CHANGED (even slightly — Brownian motion ensures movement)
        5. Navigate to Positions tab → verify unrealized_pnl column values update in real-time
        6. This validates the FULL flow: tick → server PnL recalc → WebSocket emit → UI render
        CRITICAL: If PnL doesn't update, the server-side calculation (Agent 5 a5-p4-realtime-pnl) is broken. The UI should NOT have its own PnL calculation fallback.
        DEPENDENCY: Agent 5 a5-p4-realtime-pnl, Agent 2 a2-p6b-realtime-pnl-dashboard.
    status: done
  - id: a8-p7-data-freshness-test
    content: |
      - [ ] [AGENT] P1. Playwright test: Data freshness indicators:
        1. Navigate to Trading Terminal → verify "Live" badge with green dot is visible
        2. Navigate to Positions → verify "Live" indicator on positions panel
        3. Toggle to batch mode → verify "As of {date}" badge appears (no "Live" indicator)
        4. Toggle back to live → verify "Live" indicator returns
        DEPENDENCY: Agent 1 a1-p7-data-freshness (DataFreshness component).
    status: todo
  - id: a8-p7-no-client-side-mock-data
    content: |
      - [ ] [AGENT] P0. Verification test: No client-side mock data sources remain:
        1. Verify `lib/mocks/` directory does NOT exist (removed by Agent 6)
        2. Verify `lib/trading-data.ts` is NOT imported by any page in `app/` (grep for imports)
        3. Verify `lib/ml-mock-data.ts`, `lib/execution-platform-mock-data.ts`, `lib/data-service-mock-data.ts`, `lib/strategy-platform-mock-data.ts` are NOT imported by any page
        4. Verify NO page has `const mockData = [` or `const MOCK_` inline arrays
        5. Every data table must get its data from a `useQuery` hook calling the API
        This enforces the separation of concerns: the UI is visual only, all data comes from the API.
        DEPENDENCY: Agent 6 Phase 4 (MSW removal + trading-data.ts migration).
    status: todo
  - id: a8-p7-guided-tour-test
    content: |
      - [ ] [AGENT] P1. Playwright test: Guided tour:
        1. Clear localStorage → login as admin (simulates first login)
        2. Verify tour overlay appears highlighting first step (Global scope filters)
        3. Click "Next" → verify tour advances to lifecycle navigation
        4. Click "Skip" → verify tour closes and doesn't reappear on page reload
        DEPENDENCY: Agent 1 must implement guided tour (a1-p6-guided-tour).
    status: todo
  # ── Phase 8: Quality Gates & SIT (Post-Audit Citadel Gate) ──
  - id: a8-p8-qg-unified-trading-api
    content: |
      - [x] [AGENT] P0. Run `cd unified-trading-api && bash scripts/quality-gates.sh` and fix all failures. This validates:
        1. ruff lint + format clean
        2. basedpyright typecheck passes
        3. pytest passes with coverage ≥ 80% (actual: 94%)
        4. No security violations
        ALL QUALITY GATES PASSED. 232 unit tests, 101 integration tests.
    status: done
  - id: a8-p8-qg-unified-trading-system-ui
    content: |
      - [ ] [AGENT] P0. Run quality gates on unified-trading-system-ui:
        1. `VITE_MOCK_API=true npx vite build` — smoke build must succeed
        2. `CI=true npm test -- --run` — vitest must pass
        3. Fix any TypeScript errors, broken imports, or test failures
        This was NOT executed during the agent audit — it must pass before we can declare Agents 1-4 done.
    status: todo
  - id: a8-p8-sit-tier-readiness
    content: |
      - [x] [AGENT] P1. Add SIT or smoke scenarios that encode tier + readiness validation:
        1. Create `e2e/tier-readiness.spec.ts` — Playwright test that:
           a. Starts API in mock mode (Tier 1) → verifies `GET /readiness` returns `effective_runtime_tier: 1`
           b. Verifies runtime strip in UI shows correct tier badge
           c. Verifies "Mock Mode" indicator visible in debug footer
        2. Create `e2e/smoke-full-stack.spec.ts` — End-to-end smoke covering all 9 services:
           a. Login → Dashboard renders with data
           b. Navigate each lifecycle stage → first tab renders
           c. POST /admin/reset → verify clean state
        3. These encode the Citadel quality bar without using the word "citadel" in test names
    status: todo
  - id: a8-p8-verify-no-redundant-impl
    content: |
      - [ ] [AGENT] P0. Verify no redundant implementations remain across the codebase:
        1. Check `mock_data/state_store.py` is removed (Agent 5 a5-p9-quarantine-legacy-state-store)
        2. Check `lib/mocks/` directory is removed (Agent 6 a6-p4-remove-msw)
        3. Check no page imports from `lib/trading-data.ts` (Agent 6 a6-p4-migrate-trading-data)
        4. Check `lib/ml-mock-data.ts`, `lib/execution-platform-mock-data.ts`, `lib/data-service-mock-data.ts`, `lib/strategy-platform-mock-data.ts` are not imported by any page
        5. Grep for any `const mockData = [` or `const MOCK_` inline arrays in `app/` pages
        6. If any redundant implementations found, either delete them or document as explicit TODOs
    status: todo
isProject: false
---

# Notes & Context

## CRITICAL: Read Before Any Work

1. Read `unified-trading-pm/plans/active/CITADEL_VISION_2026_03_22.md` — system-wide vision
2. Read `unified-trading-system-ui/UI_STRUCTURE_MANIFEST.json` — use per-service tab lists to verify every tab renders
   in Playwright tests

## TABS-ONLY VERIFICATION

Every Playwright test should verify: clicking a lifecycle stage → lands on first tab → tab bar is visible → all tabs are
clickable → NO card-based sub-pages appear. If any test encounters a card grid instead of tabs, that's a FAILURE.

## Risk Factors & Mitigations

**RISK 1 (HIGHEST): Depends on ALL 7 other agents — fragile integration point.** If ANY agent is incomplete (stub pages,
missing endpoints, broken auth), E2E tests fail. Agent 8 can't distinguish "test is wrong" from "upstream agent didn't
finish." MITIGATION: Structure tests in 3 tiers:

- Tier 1 (run always): Navigation tests — verify routes exist, tabs render, no 404s. These work even if data is missing
  (skeleton/empty states should appear).
- Tier 2 (run after Agent 5+6): Data tests — verify tables have rows, charts have data.
- Tier 3 (run after ALL agents): Flow tests — full user journeys (login → trade → reset). Run Tier 1 first. If it
  passes, proceed to Tier 2. This gives useful feedback even if some agents lag.

**RISK 2: Starting 3 servers in Playwright config is complex.** auth-api (8200) + unified-trading-api (8030) + Next.js
(3000) all need to be up before tests run. Server startup order matters (auth-api must be up before unified-trading-api
validates JWTs). MITIGATION: Use Playwright's `webServer` config array with dependencies:

```js
webServer: [
  { command: "cd ../auth-api && .venv/bin/python -m auth_api.app", port: 8200, timeout: 30000 },
  { command: "cd ../unified-trading-api && .venv/bin/python -m unified_trading_api.main", port: 8030, timeout: 30000 },
  { command: "npm run dev", port: 3000, timeout: 60000 },
];
```

Add health check retries: don't start tests until GET /health returns 200 on all 3 ports.

**RISK 3: Codegen pipeline may fail if API has errors.** If unified-trading-api has basedpyright errors or won't start,
codegen can't fetch OpenAPI spec. MITIGATION: Run `bash scripts/quality-gates.sh` on unified-trading-api FIRST (Phase
0). Only proceed to codegen (Phase 4) after API quality gates pass.

**RISK 4: Auth alignment test is brittle — JWTs expire, formats change.** Testing cross-API auth requires live JWTs that
may have short expiry. MITIGATION: In mock mode, auth-api JWTs should have long expiry (1h minimum). The alignment test
should login → immediately use token → all within 30 seconds. No token caching between tests.

**RISK 5: Tests may be flaky due to timing (WebSocket, latency simulation).** WebSocket ticks arrive at random
intervals. Asserting "price changed" may fail if tick hasn't arrived. MITIGATION: Use Playwright's
`expect().toPass({ timeout: 5000 })` or `page.waitForFunction()` for time-dependent assertions. Don't use fixed sleeps.
Wait for DOM changes.

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

## New scope (added 2026-03-22 gap analysis)

- SSOT codegen pipelines MUST run after Agents 5-6 finish (OpenAPI → TypeScript, UAC → reference data)
- Auth alignment test: verify persona org IDs match across auth-api and unified-trading-api
- Real-time feed E2E test: verify WebSocket ticks update the Trading Terminal
- Batch/live switch E2E test: verify data actually changes when toggling modes
- E2E tests must start BOTH auth-api (port 8200) and unified-trading-api (port 8030)

## Additional scope (added 2026-03-22 gap analysis)

- Org isolation matrix: test that every service correctly filters by org_id per persona — demo-critical
- Codegen pipeline scripts: must be CREATED if they don't exist, not just run
- Error state E2E tests: verify error boundaries, upgrade cards, and access denied flows
- Responsive E2E tests: verify tablet layout works (hamburger, stacked panels)
- Bundle size check: verify dynamic imports keep chunks under 500KB
- Latency simulation test: verify skeletons are actually visible with MOCK_LATENCY_MS
- CSV/PDF export tests: verify download functionality works end-to-end
