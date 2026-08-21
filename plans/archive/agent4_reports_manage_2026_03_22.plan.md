---
doc_type: plan
title: agent4-reports-manage
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [client-reporting-api, execution-service, unified-trading-api, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-22'
overview: Absorb settlement-ui, client-reporting-ui, onboarding-ui, user-management-ui into Reports and Manage services
todos:
- {id: a4-p0-reports-overview, content: '- [x] [AGENT] P0. Verify `/services/reports/overview` (P&L Attribution tab) has real content. Should show: aggregated P&L by strategy, attribution breakdown (funding, carry, basis, delta, greeks, slippage, fees), time series. Wire to `GET /analytics/pnl` and `GET /reporting/pnl-attribution` APIs. The Dashboard already has `PnLAttributionPanel` — reuse that component here with more detail.

    ', status: done}
- {id: a4-p0-reports-executive, content: '- [x] [AGENT] P1. Verify `/services/reports/executive` has: AUM overview, performance summary (MTD/QTD/YTD), top/bottom strategies, risk utilization, client-level breakdowns. Wire to `GET /reporting/executive-summary` API.

    ', status: done}
- {id: a4-p0-reports-settlement, content: '- [x] [AGENT] P0. Verify `/services/reports/settlement` has real content. If stub, build it by absorbing patterns from `settlement-ui/src/pages/Settlements.tsx` (settlement tracking table with status: pending/matched/disputed/settled) and `settlement-ui/src/pages/Invoices.tsx` (invoice list with generation, download, send actions). Wire to `GET /analytics/settlements` and `GET /reporting/invoices` APIs.

    ', status: done}
- {id: a4-p0-reports-reconciliation, content: '- [x] [AGENT] P1. Verify `/services/reports/reconciliation` has: batch vs live reconciliation view showing drift, unmatched trades, position breaks. This is related to the DriftAnalysisPanel on the Dashboard — share that component.

    ', status: done}
- {id: a4-p0-reports-regulatory, content: '- [x] [AGENT] P1. Verify `/services/reports/regulatory` has: MiFID II transaction reporting, FCA best execution reporting, EMIR derivative reporting. Wire to `GET /reporting/regulatory` API.

    ', status: done}
- {id: a4-p1-absorb-client-reporting, content: "- [x] [AGENT] P1. Review `client-reporting-ui/src/components/` for patterns to absorb:\n  - `GenerateTab.tsx` — report generation workflow (select client, date range, report type → generate PDF/CSV)\n  - `PerformanceTab.tsx` — performance metrics visualization\n  - `ReportsTab.tsx` — report list with download links\n  Extract these patterns and integrate into Reports service tabs. The report generation workflow should be a \"Generate Report\" button on the P&L tab that opens a modal with client/date/type selection.\n", status: done}
- {id: a4-p1-absorb-invoicing, content: '- [x] [AGENT] P1. Review `_reference/versa-invoicing/` for invoicing patterns. Review `_reference/versa-client-reporting/` for client-facing reporting patterns. Incorporate fee calculation display (from client-reporting-api''s fee_calculator.py) into the Settlement tab.

    ', status: done}
- {id: a4-p2-manage-clients, content: '- [x] [AGENT] P0. Verify `/services/manage/clients` has: client list table with columns (name, org, status, strategies, AUM, last activity). Should have "Onboard Client" button. Wire to `GET /users/organizations` API. If stub, build using mock data.

    ', status: done}
- {id: a4-p2-manage-mandates, content: '- [x] [AGENT] P1. Verify `/services/manage/mandates` has: mandate list (investment mandates defining strategy allocation, risk limits, fee structure per client). Wire to `GET /config/mandates` API.

    ', status: done}
- {id: a4-p2-manage-fees, content: '- [x] [AGENT] P1. Verify `/services/manage/fees` has: fee schedule management (management fee %, performance fee %, hurdle rate, high-water mark). Wire to `GET /config/fee-schedules` API.

    ', status: done}
- {id: a4-p2-manage-users, content: '- [x] [AGENT] P0. Verify `/services/manage/users` has: user list with roles, status, last login. Should have "Add User" button. Wire to `GET /users/list` API. If stub, build by absorbing patterns from `user-management-ui/src/` — particularly the user lifecycle management (onboard, modify roles, deactivate).

    ', status: done}
- {id: a4-p2-manage-compliance, content: '- [x] [AGENT] P1. Verify `/services/manage/compliance` has: compliance rules, violations log, audit trail. Wire to `GET /audit/compliance` API.

    ', status: done}
- {id: a4-p3-absorb-onboarding, content: "- [x] [AGENT] P1. Review `onboarding-ui/src/pages/` for patterns to absorb:\n  - `VenueConnectionPage.tsx` — venue API key entry, connection testing\n  - `RiskConfiguration.tsx` — risk limit setup per strategy/client\n  - `CredentialStatusPage.tsx` — credential health dashboard\n  - `StrategyOnboarding.tsx` — strategy activation workflow\n  - `StrategyListPage.tsx` — strategy selection during onboarding\n  These should become modals/drawers triggered from the Clients and Mandates tabs. \"Onboard Client\" button on Clients tab should open a multi-step flow: 1) Client details → 2) Strategy selection → 3) Venue connection → 4) Risk config → 5) Review & activate.\n", status: done}
- {id: a4-p4-absorb-user-mgmt, content: '- [x] [AGENT] P1. Review `user-management-ui/src/` for patterns to absorb. Key feature: single-click user provisioning (GitHub, Slack, M365, GCP, portal access per role). This should become the "Add User" workflow on the Users tab. In mock mode, adding a user should update MockStateStore and be visible immediately in the user list.

    ', status: done}
- {id: a4-p5-document-management, content: '- [x] [AGENT] P1. Add a "Documents" sub-section accessible from Reports service (either as a 6th tab or a panel within Settlement). Should show: uploaded documents list, upload button (calls `GET /documents/upload-url` then uploads to the returned URL), download links (calls `GET /documents/download-url`). In mock mode, upload should add a record to MockStateStore "documents" domain; download URL returns a mock URL.

    ', status: done}
- {id: a4-p5b-skeleton-loading, content: '- [x] [AGENT] P1. Ensure ALL reports and manage pages use skeleton loading states (not "Loading..." text). Use skeleton components from Agent 1. Key pages: P&L Attribution (table + chart skeleton), Settlement (table skeleton), Client List (table skeleton), User List (table skeleton). Mandatory per CITADEL_VISION visual polish standards.

    ', status: done}
- {id: a4-p5b-reporting-api-routing, content: '- [x] [AGENT] P1. Verify that Reports service pages route API calls correctly. Per CITADEL_VISION, unified-trading-api proxies `/reporting/*` to client-reporting-api (port 8014) in real mode, and serves from MockStateStore in mock mode. The UI should NOT need separate base URLs — everything goes through port 8030. Verify: `hooks/api/use-reports.ts` calls `/reporting/*` endpoints and these work in mock mode. If Agent 5 has not yet set up the proxy, document this as a dependency.

    ', status: done}
- {id: a4-p6-tests, content: '- [x] [AGENT] P1. Add Playwright tests: 1) Navigate to Reports > P&L → verify attribution table renders. 2) Navigate to Reports > Settlement → verify settlements table renders. 3) Navigate to Manage > Clients → verify client list renders. 4) Navigate to Manage > Users → verify user list renders. 5) Click "Onboard Client" → verify workflow opens.

    ', status: done}
- {id: a4-p7-export, content: "- [x] [AGENT] P0. Add split \"Export\" button (CSV + Excel) to ALL data tables in Reports and Manage:\n  1. P&L Attribution, Settlement, Reconciliation, Regulatory tables\n  2. Client list, User list, Mandate list, Fee schedule list\n  3. Use `exportTableToCsv()` and `exportTableToXlsx()` from `lib/utils/export.ts` (created by Agent 2)\n  4. Reports Excel: multi-sheet workbook — P&L on sheet 1, positions on sheet 2, orders on sheet 3\n  DEPENDENCY: Agent 2 must create `lib/utils/export.ts` first (a2-p7-export-tables).\n", status: done}
- {id: a4-p7-pdf-generation, content: "- [x] [AGENT] P0. Add \"Generate PDF Report\" capability to Reports > P&L and Reports > Executive:\n  1. Add \"Generate Report\" button that opens a modal: select client, date range, report type (P&L Attribution / Executive Summary / Regulatory)\n  2. On submit: call `POST /reporting/generate` with { type, client_id, date_range, format: \"pdf\" }\n  3. Show spinner while \"generating\"\n  4. On success: show \"Download Ready\" toast with download link\n  5. In mock mode, the API returns a pre-generated sample PDF. Create a minimal sample PDF (even 1-page with title + table) in `unified-trading-api/unified_trading_api/mock_data/sample_reports/executive_report.pdf`\n  6. For the download: API serves file via `GET /reporting/download/{report_id}` which returns the sample PDF with correct Content-Type headers\n", status: done}
- {id: a4-p7-error-states, content: "- [x] [AGENT] P1. Add error and empty states to ALL reports and manage pages:\n  1. Every page using useQuery: `if (isError) return <ApiError error={error} onRetry={refetch} />`\n  2. Settlement table empty: `<EmptyState title=\"No settlements\" description=\"Settlements appear after trades are reconciled\" />`\n  3. Client list empty: `<EmptyState title=\"No clients\" description=\"Onboard your first client\" action={{ label: \"Onboard Client\", onClick: openOnboardingModal }} />`\n  4. User list empty: `<EmptyState title=\"No users\" description=\"Add your first team member\" action={{ label: \"Add User\", onClick: openAddUserModal }} />`\n  5. Report generation error: toast with \"Report generation failed — please try again\"\n", status: done}
- {id: a4-p8-print-css, content: "- [x] [AGENT] P0. Add print-optimized styles for Reports service pages:\n  1. Add `@media print` block in `globals.css`: hide nav, debug footer, filters, buttons. Full-width tables with borders. Page breaks between sections (`break-before: page`). Company logo header + timestamp footer.\n  2. Add \"Print Report\" button on P&L Attribution and Executive tabs (next to \"Generate PDF\"). Calls `window.print()`.\n  3. Charts rendered at print resolution (set chart container to fixed width in print media).\n  DEPENDENCY: None — can start immediately.\n", status: done}
- {id: a4-p8-adopt-datatable, content: "- [x] [AGENT] P0. Replace shadcn `<Table>` with `DataTable` from `components/ui/data-table.tsx` (Agent 1) for ALL reports and manage tables: P&L, settlements, clients, users, mandates, fees, compliance.\n  DEPENDENCY: Agent 1 must create DataTable (a1-p6-tanstack-table).\n", status: done}
- {id: a4-p8-scheduled-reports, content: "- [x] [AGENT] P1. Add scheduled report configuration UI (mock-only, demonstrates the capability):\n  1. \"Schedule Report\" button on P&L and Executive tabs → opens modal\n  2. Fields: frequency (daily/weekly/monthly), recipients (email), report type, format (PDF/Excel)\n  3. On submit: creates record in MockStateStore \"scheduled_reports\" — shows in a \"Scheduled\" sub-section\n  4. In mock mode, does NOT actually send emails — just persists the configuration\n  5. This demonstrates institutional workflow capability for client demos\n  DEPENDENCY: Agent 5 must add POST /reporting/schedules endpoint.\n", status: done}
- {id: a4-p9-regulatory-page, content: "- [x] [AGENT] P1. Build `/services/reports/regulatory` page (currently 24-line stub). GAP CATEGORY: Type 2+3 (execution-service has MiFID II/FCA/EMIR compliance reporter — UI is a stub, mock doesn't simulate it).\n  The REAL implementation lives in:\n  - `execution-service/compliance/mifid_reporter.py` — MiFIDReporter with best execution checks, Article 26/27 reporting\n  - `execution-service/compliance/compliance_reporter.py` — EU_MIFID_II and UK_FCA jurisdiction\n  Agent 5 adds `GET /reporting/regulatory` endpoint (a5-p8-regulatory-reports). Agent 6 seeds 8-10 report records.\n  Build the page with:\n  1. Regulatory report list table (DataTable): report_type (MiFID II / FCA / EMIR), jurisdiction, status badge (submitted=green, pending=yellow, overdue=red), filing_date, next_due_date\n  2. Status summary cards: X submitted, Y pending, Z overdue\n  3. Click row → detail panel: instruments covered, best execution metrics summary, filing reference\n\
    \  4. Export button (CSV + Excel) using shared export utility\n  5. NOT interactive filing (that requires real service) — display and export only\n  DEPENDENCY: Agent 5 a5-p8-regulatory-reports endpoint. Agent 6 seeds regulatory_reports.\n", status: done}
isProject: false
---

# Notes & Context

## CRITICAL: Read Before Any Work

1. Read `unified-trading-system-ui/UI_STRUCTURE_MANIFEST.json` — SSOT for all page states, routes, and source files
2. Read `unified-trading-pm/plans/archive/CITADEL_VISION_2026_03_22.md` — system-wide vision

## TABS-ONLY RULE

- Reports service = ONE page with 5 tabs: P&L Attribution | Executive | Settlement | Reconciliation | Regulatory
- Manage service = ONE page with 5 tabs: Clients | Mandates | Fees | Users | Compliance
- Report generation, client onboarding, user provisioning are MODALS/DRAWERS triggered from buttons within tabs.
- Document upload is a panel/section within Settlement tab — NOT a separate page.

## Stub Pages — Exact Source Files (NO from-scratch builds)

| Stub                           | Source to Adapt                                                                                                  | Lines | How                                                                                                                                           |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------- | ----- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `reports/settlement` (24L)     | `settlement-ui/src/pages/Settlements.tsx`                                                                        | 522   | Direct adaptation as tab content. Has settlement table, status filters, venue breakdown. Also grab `Invoices.tsx` (120L) for invoice section. |
| `reports/reconciliation` (24L) | `components/trading/drift-analysis-panel.tsx` (ALREADY IN REPO) + `settlement-ui/src/pages/Positions.tsx` (122L) | 122+  | Reuse DriftAnalysisPanel from Dashboard. Add batch/live position comparison.                                                                  |
| `reports/regulatory` (24L)     | `_reference/versa-audit-ui/src/pages/CompliancePage.tsx`                                                         | 346   | Adapt compliance/regulatory patterns for MiFID II / FCA / EMIR.                                                                               |
| `reports/executive` (7L)       | `components/dashboards/executive-dashboard.tsx` (717L)                                                           | 717   | ALREADY WIRED — the 7L page delegates to this component. NOT a stub. Just verify it renders.                                                  |

## Manage Pages — All REAL, some need API wiring

| Page                | Lines | Status      | Action                                                                             |
| ------------------- | ----- | ----------- | ---------------------------------------------------------------------------------- |
| `manage/clients`    | 495   | WIRED       | Keep. Add "Onboard Client" modal from `onboarding-ui/ClientOnboarding.tsx` (503L). |
| `manage/mandates`   | 107   | INLINE MOCK | Wire to API. Expand with `onboarding-ui/RiskConfiguration.tsx` (344L) patterns.    |
| `manage/fees`       | 369   | WIRED       | Keep as-is.                                                                        |
| `manage/users`      | 353   | WIRED       | Keep. Add "Add User" modal from `user-management-ui/OnboardUserPage.tsx` (225L).   |
| `manage/compliance` | 157   | INLINE MOCK | Wire to API. Absorb `_reference/versa-audit-ui/CompliancePage.tsx` (346L).         |

## Satellite Absorption Map (as modals/drawers, NOT new pages)

| Source                                         | Lines | Target Tab                                  | How                                            |
| ---------------------------------------------- | ----- | ------------------------------------------- | ---------------------------------------------- |
| `settlement-ui/Settlements.tsx`                | 522   | Reports > Settlement                        | Direct tab content adaptation                  |
| `settlement-ui/Invoices.tsx`                   | 120   | Reports > Settlement                        | Invoice section within same tab                |
| `client-reporting-ui/GenerateTab.tsx`          | 107   | Reports > P&L                               | "Generate Report" button → modal               |
| `onboarding-ui/ClientOnboarding.tsx`           | 503   | Manage > Clients                            | "Onboard Client" button → multi-step modal     |
| `onboarding-ui/ClientDetail.tsx`               | 545   | Manage > Clients                            | Expand client detail (click row → detail view) |
| `onboarding-ui/RiskConfiguration.tsx`          | 344   | Manage > Mandates                           | Expand mandate config                          |
| `user-management-ui/OnboardUserPage.tsx`       | 225   | Manage > Users                              | "Add User" button → modal                      |
| `user-management-ui/UserDetailPage.tsx`        | 255   | Manage > Users                              | Click user row → detail drawer                 |
| `_reference/versa-audit-ui/CompliancePage.tsx` | 346   | Reports > Regulatory OR Manage > Compliance | Adapt compliance patterns                      |

## Risk Factors & Mitigations

**RISK 1 (HIGHEST): Manage routing is broken — pages in (ops), need (platform).** MANAGE_TABS exists in service-tabs.tsx
but no layout renders it. Pages are in app/(ops)/manage/\* which uses a different layout that enforces admin-only
access. MITIGATION: Coordinate with Agent 1. If Agent 1 resolves routing (move pages to platform or add redirect), Agent
4 works within the resolved structure. If Agent 1 hasn't resolved it, Agent 4 MUST fix routing first (Phase 0 blocker).
Option A (move to platform) is preferred — add entitlement check in the manage layout instead of relying on the (ops)
route group.

**RISK 2: Satellite UI components use different frameworks.** settlement-ui, onboarding-ui, user-management-ui are
Vite + potentially different component libraries. Direct copy will fail. MITIGATION: Same as Agent 3 — extract LOGIC and
LAYOUT, rebuild with shadcn/ui. For settlement-ui/ Settlements.tsx (522L), extract the table columns, status filters,
and data flow. Rebuild the UI with shadcn Table + Badge + Select. Don't import the entire 522-line component.

**RISK 3: Reports proxy verification depends on Agent 5.** Reports API calls go to port 8030 which proxies to
client-reporting-api (8014). If Agent 5 hasn't set up the proxy, reports pages show errors. MITIGATION: Wire hooks to
/reporting/\* paths on port 8030. If proxy isn't ready, unified-trading-api already serves reporting data from
MockStateStore in mock mode. The proxy only matters in real mode. Verify mock mode works independently.

**RISK 4: Onboarding multi-step modal is complex to get right.** The onboarding flow (Client → Strategy → Venue → Risk →
Review) is 5 steps with validation. Doing this as a modal is harder than a full page. MITIGATION: Use shadcn Dialog +
internal step state (useState for currentStep). Each step is a form section. Don't try to replicate onboarding-ui's full
page routing — just 5 sequential forms in one Dialog. If it's too complex, reduce to 3 steps (Client → Strategy →
Review) for MVP.

## MANAGE ROUTING FIX

Manage pages currently live in `app/(ops)/manage/*` but should be accessible via the platform shell at
`/services/manage/*`. The (ops) layout enforces admin-only access, but Manage should be visible to internal traders too
(just not to clients). Either:

- OPTION A: Move pages from (ops) to (platform)/services/manage/ (preferred — tabs work correctly)
- OPTION B: Fix (ops) layout to allow internal-trader role, add MANAGE_TABS rendering

## New scope (added 2026-03-22 gap analysis)

- PDF report generation is a NEW P0 requirement — must have downloadable reports for demo
- CSV export on every data table
- Error states and empty states mandatory on all pages
- These close the gap between "data on screen" and "production workflow"
- **Regulatory reporting (Gap Classification):** execution-service has MiFID II/FCA compliance reporter. Agent 5 adds
  mock endpoint. Build the regulatory tab with real data shape.

## New API endpoints for PDF generation

- POST /reporting/generate — accepts { type, client_id, date_range, format }
- GET /reporting/download/{report_id} — serves generated report file
- Agent 5 must add these endpoints. In mock mode, return sample PDFs from mock_data/sample_reports/

## API endpoints needed

- GET /analytics/pnl, GET /reporting/pnl-attribution
- GET /reporting/executive-summary, GET /reporting/invoices
- GET /analytics/settlements, GET /reporting/regulatory
- GET /users/organizations, GET /users/list, POST /users
- GET /config/mandates, GET /config/fee-schedules
- GET /audit/compliance
- GET /documents/upload-url, GET /documents/download-url, GET /documents/list
