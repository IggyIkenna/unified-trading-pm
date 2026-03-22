# 8 Agent Prompts for Citadel-Grade System Refactor

Each prompt below is self-contained. Copy-paste one prompt per agent session. Every agent gets the full vision context +
their specific workstream.

---

## SHARED PREAMBLE (included in every prompt below)

```
You are executing one workstream of an 8-agent parallel refactor of the Unified Trading System.

BEFORE ANY CODE: Read these files in order:
1. unified-trading-pm/plans/active/CITADEL_VISION_2026_03_22.md — the complete system vision
2. Your specific plan file (identified below) — your detailed todos
3. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md — mandatory coding rules
4. .cursorrules — workspace standards

WORKSPACE: /Users/ikennaigboaka/Code/unified-trading-system-repos/
Each subdirectory is an INDEPENDENT git repo. Only commit to repos you modify.

KEY RULES:
- `uv pip install` not `pip install`
- `bash scripts/quality-gates.sh` for tests (never pytest directly)
- `basedpyright` not `pyright`
- No `os.getenv()` — use `UnifiedCloudConfig`
- Flat deps only in pyproject.toml (no optional-dependencies)
- Do NOT run `bash scripts/quickmerge.sh` unless explicitly told to
- Do NOT run `git reset --hard` under any circumstances

THE BIG PICTURE:
- ONE UI: unified-trading-system-ui (Next.js) — all 13 satellite UIs are being archived
- THREE APIs: auth-api (port 8200, SSO/tokens), client-reporting-api (port 8014, client reports/invoices), unified-trading-api (port 8030, trading system)
- 9 SERVICES: Data, Research, Promote, Trading, Execution, Observe, Manage, Reports, Admin/Ops
- DIRECT-TO-TABS: No card landing pages. Lifecycle nav → first tab of service
- 90% CODE SHARING: Mock and real modes share same route handlers + service layer
- NO MSW: UI always calls real APIs. APIs handle mock/real via service layer internally
- REPORTS → client-reporting-api (port 8014), everything else → unified-trading-api (port 8030)
- VISIBLE UX: Every function has a visible button. Reset Demo, Live/Batch toggle, persona switcher all visible in shell

SSOT CODEGEN PIPELINES (run when you change schemas/registries):
- After UAC registry changes: `cd unified-api-contracts && .venv/bin/python scripts/generate_ui_reference_data.py --output ../unified-trading-system-ui/lib/registry/ui-reference-data.json`
- After API route changes: fetch OpenAPI spec from running API, then `cd unified-trading-system-ui && npm run generate:types`
- See CITADEL_VISION_2026_03_22.md "SSOT Codegen Pipeline" section for full details.

7 OTHER AGENTS are working in parallel on other workstreams. Do not touch files outside your scope unless absolutely necessary. If you need something from another agent's scope, document it as a dependency.
```

---

## PROMPT 1: Shell & Navigation Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 1 — Shell & Navigation
YOUR PLAN: unified-trading-pm/plans/active/agent1_shell_navigation_2026_03_22.plan.md

YOUR SCOPE:
- unified-trading-system-ui only
- Shell components: components/shell/*, components/platform/*
- Routing: app/(platform)/services/[key]/, app/(platform)/portal/*, app/(platform)/services/overview/
- Navigation: lib/lifecycle-mapping.ts, lib/reset-demo.ts
- Stores: lib/stores/global-scope-store.ts

YOUR MISSION:
1. DELETE the card-based service landing page (app/(platform)/services/[key]/page.tsx)
2. DELETE all /portal/* redirect pages (8 files)
3. DELETE /services/overview hub page
4. WIRE orphaned components: batch-live-rail.tsx, filter-bar.tsx, candidate-basket.tsx, live-asof-toggle.tsx
5. CREATE debug-footer.tsx with Reset Demo button, persona display, mock mode indicator
6. FIX lifecycle-nav links to go direct-to-tab (no intermediate landings)
7. FIX breadcrumbs to show Home > Service > Tab
8. VERIFY every service has a layout.tsx with correct ServiceTabs
9. FIX build: NEXT_PUBLIC_MOCK_API=true npx next build must pass
10. ADD Playwright tests for navigation flows

DO NOT TOUCH: page content within service tabs (that's Agent 2-4, 7's job)
DO NOT TOUCH: API code (that's Agent 5-6's job)

Read your plan file for detailed todos with acceptance criteria.
Execute todos in order (Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4).
Mark each todo as done in the plan file when complete (change - [ ] to - [x]).
```

---

## PROMPT 2: Trading Service Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 2 — Trading Service (Run)
YOUR PLAN: unified-trading-pm/plans/active/agent2_trading_service_2026_03_22.plan.md

YOUR SCOPE:
- unified-trading-system-ui: app/(platform)/dashboard/, app/(platform)/services/trading/*, app/(platform)/services/execution/*
- unified-trading-system-ui: components/trading/*
- unified-trading-system-ui: hooks/api/use-positions.ts, use-orders.ts, use-market-data.ts, use-alerts.ts, use-trading.ts
- live-health-monitor-ui (read-only — restore ManualTradingPanel from git history)

YOUR MISSION:
1. Wire Dashboard ↔ Terminal navigation (prominent buttons both ways)
2. RESTORE ManualTradingPanel from git (commit 5c24fa2 in live-health-monitor-ui) as drawer in Terminal
3. VERIFY all 6 Trading tabs have real content (Terminal, Positions, Orders, Execution, Accounts, Markets)
4. WIRE batch/live mode switching on Terminal (banner, different data based on global scope mode)
5. VERIFY strategy detail and list pages work
6. ADD Playwright tests for trading flows

DO NOT TOUCH: Shell/navigation components (Agent 1's scope)
DO NOT TOUCH: API route handlers (Agent 5's scope)
DO NOT TOUCH: Seed data (Agent 6's scope)

Key files to read first:
- app/(platform)/dashboard/page.tsx (460 lines — the Command Center)
- app/(platform)/services/trading/overview/page.tsx (818 lines — the Terminal)
- components/trading/ (31 components)
- hooks/api/ (14 API hook files)

Read your plan file for detailed todos. Execute in phase order.
```

---

## PROMPT 3: Research & Build Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 3 — Research & Build + Promote Services
YOUR PLAN: unified-trading-pm/plans/active/agent3_research_build_2026_03_22.plan.md

YOUR SCOPE:
- unified-trading-system-ui: app/(platform)/services/research/*, app/(platform)/services/execution/*
- strategy-ui (read-only — extract wizard patterns)
- ml-training-ui (read-only — extract experiment tracking patterns)
- _reference/versa-execution-analytics-ui/ (read-only — reference patterns)

YOUR MISSION:
1. VERIFY all Research Hub, ML sub-tabs, Strategy sub-tabs have real content (not placeholders)
2. Wire all pages to API hooks (GET /ml/*, GET /execution/backtests, etc.)
3. ABSORB strategy-ui wizard as modal/drawer within Strategies tab
4. ABSORB ml-training-ui experiment tracking into ML Models tab
5. VERIFY Promote service (candidates, handoff) works with approve/reject actions
6. ADD Playwright tests for research flows

DO NOT TOUCH: Shell/navigation (Agent 1), Trading pages (Agent 2), API code (Agent 5-6)

Key repos to reference:
- strategy-ui/src/components/wizard/ — multi-step wizard with CSV upload
- ml-training-ui/src/ — experiment tracking UI
- _reference/versa-execution-analytics-ui/ — execution analytics patterns

Read your plan file for detailed todos. Execute in phase order.
```

---

## PROMPT 4: Reports & Manage Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 4 — Reports & Manage Services
YOUR PLAN: unified-trading-pm/plans/active/agent4_reports_manage_2026_03_22.plan.md

YOUR SCOPE:
- unified-trading-system-ui: app/(platform)/services/reports/*, app/(platform)/services/manage/*
- settlement-ui (read-only — extract settlement/invoice patterns)
- client-reporting-ui (read-only — extract reporting patterns)
- onboarding-ui (read-only — extract onboarding flow patterns)
- user-management-ui (read-only — extract user management patterns)
- _reference/versa-client-reporting/, versa-invoicing/, versa-onboarding/ (read-only)

YOUR MISSION:
1. VERIFY all 5 Reports tabs have real content (P&L, Executive, Settlement, Reconciliation, Regulatory)
2. VERIFY all 5 Manage tabs have real content (Clients, Mandates, Fees, Users, Compliance)
3. ABSORB settlement-ui pages into Reports > Settlement
4. ABSORB client-reporting-ui patterns into Reports > P&L
5. ABSORB onboarding-ui flows as modals in Manage > Clients
6. ABSORB user-management-ui into Manage > Users
7. ADD document upload/download section in Reports
8. ADD Playwright tests

DO NOT TOUCH: Shell (Agent 1), Trading (Agent 2), Research (Agent 3), API code (Agent 5-6)

Read your plan file for detailed todos. Execute in phase order.
```

---

## PROMPT 5: API Service Layer Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 5 — Backend API Service Layer
YOUR PLAN: unified-trading-pm/plans/active/agent5_api_service_layer_2026_03_22.plan.md

YOUR SCOPE:
- unified-trading-api (primary — full write access)
- unified-trading-library (read MockStateStore, may need minor imports)

YOUR MISSION:
1. CREATE services/ directory with Protocol interfaces for all 15 domains
2. CREATE services/mock/ with MockStateStore-backed implementations
3. CREATE services/live/ with stub implementations (NotImplementedError)
4. CREATE services/factory.py with Depends() factories
5. REFACTOR all 15 route files to use service layer (eliminate if/else mock checks)
6. REPLACE local state_store.py with UTL MockStateStore (JSONL persistence)
7. ADD POST /admin/reset endpoint
8. ADD POST /execution/orders endpoint (for manual trading)
9. ADD new API endpoints needed by UI agents (GET /ml/experiments, etc.)
10. ADD integration tests for every route (mock mode)
11. ENSURE quality-gates.sh passes

DO NOT TOUCH: UI code (Agents 1-4, 7), seed data content (Agent 6)

Current state of unified-trading-api:
- 16 domain routers, ~1,538 lines
- Every route: `if mock_mode: return mock_store.list(domain)` else `return NOT_IMPLEMENTED`
- Simple state_store.py (69 lines, in-memory only, no persistence)
- 1 test file (test_health.py)

The service layer pattern is explained in CITADEL_VISION_2026_03_22.md.
Read your plan file for detailed todos. Execute in phase order.
```

---

## PROMPT 6: Mock Data Quality Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 6 — Mock Data Quality & Migration
YOUR PLAN: unified-trading-pm/plans/active/agent6_mock_data_quality_2026_03_22.plan.md

YOUR SCOPE:
- unified-trading-api: mock_data/seed.py, mock_data/personas.py (create)
- unified-trading-system-ui: lib/mocks/ (delete), lib/trading-data.ts (reference for alignment)
- auth-api: mock_data.py (reference for persona alignment)

YOUR MISSION:
1. CREATE personas.py as SSOT for org/persona definitions (matching auth-api and UI)
2. ENHANCE seed.py with comprehensive, realistic data across ALL domains
3. ADD org_id to every seed record for persona-based scoping
4. ALIGN seed strategies with UI's trading-data.ts (same IDs, names, asset classes)
5. SEED batch vs live data variants
6. ADD seed versioning and CI/deterministic mode
7. REMOVE MSW from the UI (lib/mocks/ directory, ~1,411 lines)
8. MIGRATE Dashboard from client-side trading-data.ts to API hooks
9. ADD seed data quality tests

CRITICAL CONSTRAINT: The seed data MUST produce visually identical results to the current
client-side trading-data.ts when rendered on the Dashboard. Same strategy names, similar PnL
ranges, same 4 organizations. The user should not notice a difference after migration.

DEPENDENCY: Agent 5 must create the service layer first. Your seed data feeds into their
MockStateStore. Coordinate: your seed.py structure must match Agent 5's service method expectations.

Read your plan file for detailed todos. Execute in phase order.
```

---

## PROMPT 7: Observe & Admin Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 7 — Observe & Admin/Ops Services
YOUR PLAN: unified-trading-pm/plans/active/agent7_observe_admin_2026_03_22.plan.md

YOUR SCOPE:
- unified-trading-system-ui: app/(platform)/services/observe/*, app/(ops)/*
- deployment-ui (read-only — extract 8-tab patterns)
- batch-audit-ui (read-only — extract audit patterns)
- live-health-monitor-ui (read-only — extract monitoring patterns)
- logs-dashboard-ui (read-only — extract log viewer patterns)
- _reference/versa-audit-ui/, versa-admin-ui/, deployment-ui/ (read-only)

YOUR MISSION:
1. VERIFY all 5 Observe tabs have real content (Risk, Alerts, News, Strategy Health, System Health)
2. ABSORB live-health-monitor-ui monitoring into System Health
3. ABSORB logs-dashboard-ui log viewer into System Health
4. VERIFY Admin dashboard has real content
5. ABSORB deployment-ui's 8-tab richness into Admin > DevOps
6. ABSORB batch-audit-ui audit trail into Admin > Audit/Compliance
7. VERIFY ops pages have content (Jobs, Services)
8. ADD Playwright tests

DO NOT TOUCH: Shell (Agent 1), Trading (Agent 2), Research (Agent 3), Reports/Manage (Agent 4), API (Agent 5-6)

deployment-ui has the RICHEST satellite UI (9/10 score, 8 tabs). Its patterns are the gold
standard for what the DevOps page should look like.

Read your plan file for detailed todos. Execute in phase order.
```

---

## PROMPT 8: E2E Tests & Quality Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 8 — E2E Tests & Quality Gates
YOUR PLAN: unified-trading-pm/plans/active/agent8_e2e_tests_quality_2026_03_22.plan.md

YOUR SCOPE:
- unified-trading-api: scripts/quality-gates.sh, tests/
- unified-trading-system-ui: playwright.config.ts, e2e/, scripts/

YOUR MISSION:
1. FIX unified-trading-api quality-gates.sh (ruff, basedpyright, pytest with coverage ≥ 80%)
2. FIX unified-trading-system-ui build (TypeScript strict, no MSW references)
3. SET UP Playwright E2E infrastructure (start API + UI, POST /admin/reset before each suite)
4. WRITE Playwright tests for EVERY service: Auth flow, Trading flow, Research flow, Data flow, Reports flow, Manage flow, Observe flow, Admin flow, Reset Demo flow
5. VERIFY API integration tests cover all routes
6. ADD OpenAPI schema parity test
7. CREATE smoke test script (bash scripts/e2e-smoke.sh)

DEPENDENCY: This agent depends on Agents 5-6 (API + data) being substantially complete.
Start with Phases 0-1 (quality gates, build fixes) which can run immediately.
Phases 2-5 (Playwright, integration tests) should run after API service layer is in place.

DO NOT TOUCH: Page content, API route logic, seed data — only tests and quality infrastructure.

Read your plan file for detailed todos. Execute in phase order.
```

---

## Execution Order & Dependencies

```
PARALLEL GROUP 1 (start immediately):
  Agent 1: Shell & Navigation (UI only, no API dependency)
  Agent 3: Research & Build (UI only, can verify/build pages independently)
  Agent 4: Reports & Manage (UI only, can verify/build pages independently)
  Agent 5: API Service Layer (backend only, no UI dependency)
  Agent 7: Observe & Admin (UI only, can verify/build pages independently)

PARALLEL GROUP 2 (after Agent 5 service layer is scaffolded):
  Agent 2: Trading Service (needs API endpoints for hook wiring)
  Agent 6: Mock Data Quality (needs Agent 5's MockStateStore integration)

PARALLEL GROUP 3 (after Agents 1-7 substantially complete):
  Agent 8: E2E Tests & Quality (needs all services to have content)
```
