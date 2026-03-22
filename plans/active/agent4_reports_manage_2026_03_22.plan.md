---
name: agent4-reports-manage
overview: Absorb settlement-ui, client-reporting-ui, onboarding-ui, user-management-ui into Reports and Manage services
todos:
  - id: a4-p0-reports-overview
    content: |
      - [ ] [AGENT] P0. Verify `/services/reports/overview` (P&L Attribution tab) has real content. Should show: aggregated P&L by strategy, attribution breakdown (funding, carry, basis, delta, greeks, slippage, fees), time series. Wire to `GET /analytics/pnl` and `GET /reporting/pnl-attribution` APIs. The Dashboard already has `PnLAttributionPanel` — reuse that component here with more detail.
    status: todo
  - id: a4-p0-reports-executive
    content: |
      - [ ] [AGENT] P1. Verify `/services/reports/executive` has: AUM overview, performance summary (MTD/QTD/YTD), top/bottom strategies, risk utilization, client-level breakdowns. Wire to `GET /reporting/executive-summary` API.
    status: todo
  - id: a4-p0-reports-settlement
    content: |
      - [ ] [AGENT] P0. Verify `/services/reports/settlement` has real content. If stub, build it by absorbing patterns from `settlement-ui/src/pages/Settlements.tsx` (settlement tracking table with status: pending/matched/disputed/settled) and `settlement-ui/src/pages/Invoices.tsx` (invoice list with generation, download, send actions). Wire to `GET /analytics/settlements` and `GET /reporting/invoices` APIs.
    status: todo
  - id: a4-p0-reports-reconciliation
    content: |
      - [ ] [AGENT] P1. Verify `/services/reports/reconciliation` has: batch vs live reconciliation view showing drift, unmatched trades, position breaks. This is related to the DriftAnalysisPanel on the Dashboard — share that component.
    status: todo
  - id: a4-p0-reports-regulatory
    content: |
      - [ ] [AGENT] P1. Verify `/services/reports/regulatory` has: MiFID II transaction reporting, FCA best execution reporting, EMIR derivative reporting. Wire to `GET /reporting/regulatory` API.
    status: todo
  - id: a4-p1-absorb-client-reporting
    content: |
      - [ ] [AGENT] P1. Review `client-reporting-ui/src/components/` for patterns to absorb:
        - `GenerateTab.tsx` — report generation workflow (select client, date range, report type → generate PDF/CSV)
        - `PerformanceTab.tsx` — performance metrics visualization
        - `ReportsTab.tsx` — report list with download links
        Extract these patterns and integrate into Reports service tabs. The report generation workflow should be a "Generate Report" button on the P&L tab that opens a modal with client/date/type selection.
    status: todo
  - id: a4-p1-absorb-invoicing
    content: |
      - [ ] [AGENT] P1. Review `_reference/versa-invoicing/` for invoicing patterns. Review `_reference/versa-client-reporting/` for client-facing reporting patterns. Incorporate fee calculation display (from client-reporting-api's fee_calculator.py) into the Settlement tab.
    status: todo
  - id: a4-p2-manage-clients
    content: |
      - [ ] [AGENT] P0. Verify `/services/manage/clients` has: client list table with columns (name, org, status, strategies, AUM, last activity). Should have "Onboard Client" button. Wire to `GET /users/organizations` API. If stub, build using mock data.
    status: todo
  - id: a4-p2-manage-mandates
    content: |
      - [ ] [AGENT] P1. Verify `/services/manage/mandates` has: mandate list (investment mandates defining strategy allocation, risk limits, fee structure per client). Wire to `GET /config/mandates` API.
    status: todo
  - id: a4-p2-manage-fees
    content: |
      - [ ] [AGENT] P1. Verify `/services/manage/fees` has: fee schedule management (management fee %, performance fee %, hurdle rate, high-water mark). Wire to `GET /config/fee-schedules` API.
    status: todo
  - id: a4-p2-manage-users
    content: |
      - [ ] [AGENT] P0. Verify `/services/manage/users` has: user list with roles, status, last login. Should have "Add User" button. Wire to `GET /users/list` API. If stub, build by absorbing patterns from `user-management-ui/src/` — particularly the user lifecycle management (onboard, modify roles, deactivate).
    status: todo
  - id: a4-p2-manage-compliance
    content: |
      - [ ] [AGENT] P1. Verify `/services/manage/compliance` has: compliance rules, violations log, audit trail. Wire to `GET /audit/compliance` API.
    status: todo
  - id: a4-p3-absorb-onboarding
    content: |
      - [ ] [AGENT] P1. Review `onboarding-ui/src/pages/` for patterns to absorb:
        - `VenueConnectionPage.tsx` — venue API key entry, connection testing
        - `RiskConfiguration.tsx` — risk limit setup per strategy/client
        - `CredentialStatusPage.tsx` — credential health dashboard
        - `StrategyOnboarding.tsx` — strategy activation workflow
        - `StrategyListPage.tsx` — strategy selection during onboarding
        These should become modals/drawers triggered from the Clients and Mandates tabs. "Onboard Client" button on Clients tab should open a multi-step flow: 1) Client details → 2) Strategy selection → 3) Venue connection → 4) Risk config → 5) Review & activate.
    status: todo
  - id: a4-p4-absorb-user-mgmt
    content: |
      - [ ] [AGENT] P1. Review `user-management-ui/src/` for patterns to absorb. Key feature: single-click user provisioning (GitHub, Slack, M365, GCP, portal access per role). This should become the "Add User" workflow on the Users tab. In mock mode, adding a user should update MockStateStore and be visible immediately in the user list.
    status: todo
  - id: a4-p5-document-management
    content: |
      - [ ] [AGENT] P1. Add a "Documents" sub-section accessible from Reports service (either as a 6th tab or a panel within Settlement). Should show: uploaded documents list, upload button (calls `GET /documents/upload-url` then uploads to the returned URL), download links (calls `GET /documents/download-url`). In mock mode, upload should add a record to MockStateStore "documents" domain; download URL returns a mock URL.
    status: todo
  # ── Phase 5B: Visual Polish + Reporting API ──
  - id: a4-p5b-skeleton-loading
    content: |
      - [ ] [AGENT] P1. Ensure ALL reports and manage pages use skeleton loading states (not "Loading..." text). Use skeleton components from Agent 1. Key pages: P&L Attribution (table + chart skeleton), Settlement (table skeleton), Client List (table skeleton), User List (table skeleton). Mandatory per CITADEL_VISION visual polish standards.
    status: todo
  - id: a4-p5b-reporting-api-routing
    content: |
      - [ ] [AGENT] P1. Verify that Reports service pages route API calls correctly. Per CITADEL_VISION, unified-trading-api proxies `/reporting/*` to client-reporting-api (port 8014) in real mode, and serves from MockStateStore in mock mode. The UI should NOT need separate base URLs — everything goes through port 8030. Verify: `hooks/api/use-reports.ts` calls `/reporting/*` endpoints and these work in mock mode. If Agent 5 has not yet set up the proxy, document this as a dependency.
    status: todo
  - id: a4-p6-tests
    content: |
      - [ ] [AGENT] P1. Add Playwright tests: 1) Navigate to Reports > P&L → verify attribution table renders. 2) Navigate to Reports > Settlement → verify settlements table renders. 3) Navigate to Manage > Clients → verify client list renders. 4) Navigate to Manage > Users → verify user list renders. 5) Click "Onboard Client" → verify workflow opens.
    status: todo
  # ── Phase 7: PDF/CSV Export & Error States (Gap-Closing) ──
  - id: a4-p7-csv-export
    content: |
      - [ ] [AGENT] P0. Add "Export CSV" button to ALL data tables in Reports and Manage:
        1. P&L Attribution table, Settlement table, Reconciliation table, Regulatory table
        2. Client list, User list, Mandate list, Fee schedule list
        3. Use the shared `exportTableToCsv(data, columns, filename)` utility from `lib/utils/csv-export.ts` (created by Agent 2)
        4. Button placement: top-right of each table, consistent with other services
    status: todo
  - id: a4-p7-pdf-generation
    content: |
      - [ ] [AGENT] P0. Add "Generate PDF Report" capability to Reports > P&L and Reports > Executive:
        1. Add "Generate Report" button that opens a modal: select client, date range, report type (P&L Attribution / Executive Summary / Regulatory)
        2. On submit: call `POST /reporting/generate` with { type, client_id, date_range, format: "pdf" }
        3. Show spinner while "generating"
        4. On success: show "Download Ready" toast with download link
        5. In mock mode, the API returns a pre-generated sample PDF. Create a minimal sample PDF (even 1-page with title + table) in `unified-trading-api/unified_trading_api/mock_data/sample_reports/executive_report.pdf`
        6. For the download: API serves file via `GET /reporting/download/{report_id}` which returns the sample PDF with correct Content-Type headers
    status: todo
  - id: a4-p7-error-states
    content: |
      - [ ] [AGENT] P1. Add error and empty states to ALL reports and manage pages:
        1. Every page using useQuery: `if (isError) return <ApiError error={error} onRetry={refetch} />`
        2. Settlement table empty: `<EmptyState title="No settlements" description="Settlements appear after trades are reconciled" />`
        3. Client list empty: `<EmptyState title="No clients" description="Onboard your first client" action={{ label: "Onboard Client", onClick: openOnboardingModal }} />`
        4. User list empty: `<EmptyState title="No users" description="Add your first team member" action={{ label: "Add User", onClick: openAddUserModal }} />`
        5. Report generation error: toast with "Report generation failed — please try again"
    status: todo
isProject: false
---

# Notes & Context

## CRITICAL: Read Before Any Work

1. Read `unified-trading-system-ui/UI_STRUCTURE_MANIFEST.json` — SSOT for all page states, routes, and source files
2. Read `unified-trading-pm/plans/active/CITADEL_VISION_2026_03_22.md` — system-wide vision

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
