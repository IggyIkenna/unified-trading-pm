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
  - id: a4-p6-tests
    content: |
      - [ ] [AGENT] P1. Add Playwright tests: 1) Navigate to Reports > P&L → verify attribution table renders. 2) Navigate to Reports > Settlement → verify settlements table renders. 3) Navigate to Manage > Clients → verify client list renders. 4) Navigate to Manage > Users → verify user list renders. 5) Click "Onboard Client" → verify workflow opens.
    status: todo
isProject: false
---

# Notes & Context

## Key source repos for absorption

- `settlement-ui/src/pages/` — Settlements, Invoices, Positions, Reports pages
- `client-reporting-ui/src/components/` — GenerateTab, PerformanceTab, ReportsTab
- `onboarding-ui/src/pages/` — VenueConnectionPage, RiskConfiguration, CredentialStatusPage
- `user-management-ui/src/` — User lifecycle management
- `_reference/versa-client-reporting/` — Client vs internal view patterns
- `_reference/versa-invoicing/` — Invoicing workflow patterns
- `_reference/versa-onboarding/` — Onboarding flow patterns

## Absorbed from prior plans

- plan_i_client_reporting_docs: Document infrastructure, P&L reporting, invoicing, DocuSign
- user_management_platform_2026_03_13: User lifecycle management
- plan_g_auth_entitlement: Entitlement enforcement (manage service internal-only)

## API endpoints needed

- GET /analytics/pnl, GET /reporting/pnl-attribution
- GET /reporting/executive-summary, GET /reporting/invoices
- GET /analytics/settlements, GET /reporting/regulatory
- GET /users/organizations, GET /users/list, POST /users
- GET /config/mandates, GET /config/fee-schedules
- GET /audit/compliance
- GET /documents/upload-url, GET /documents/download-url, GET /documents/list
