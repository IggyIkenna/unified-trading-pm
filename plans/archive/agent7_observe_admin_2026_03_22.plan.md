---
doc_type: plan
title: agent7-observe-admin
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, execution-service, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-22'
overview: Absorb deployment-ui, batch-audit-ui, live-health-monitor-ui, logs-dashboard-ui into Observe and Admin services
todos:
- {id: a7-p0-risk-dashboard, content: "- [x] [AGENT] P0. Verify `/services/trading/risk` has real content: exposure breakdown (by venue, asset class, strategy), VaR calculation, Greeks display (delta, gamma, vega, theta), stress scenarios, limit utilization bars. Wire to `GET /risk/exposure?mode=live|batch`, `GET /risk/limits` APIs. Must support live/batch toggle same as all other domain data.\n  CRITICAL — add operational action buttons that call REAL API endpoints:\n  1. \"Trip Circuit Breaker\" button per strategy → `POST /risk/circuit-breaker { strategy_id, action: \"trip\" }`. After success: strategy card shows \"HALTED\" badge. Toast: \"Circuit breaker tripped for {strategy}\".\n  2. \"Reset Circuit Breaker\" button (only visible when tripped) → `POST /risk/circuit-breaker { strategy_id, action: \"reset\" }`. Restores normal operation.\n  3. \"Kill Switch\" button (emergency, requires confirmation dialog) → `POST /risk/kill-switch { scope, target_id }`. Shows prominent \"KILLED\" banner.\n\
    \  4. \"Scale Down\" button per strategy → `POST /analytics/strategies/{id}/scale { scale_factor: 0.5 }`. Shows \"Scaled to 50%\" badge.\n  All actions mutate MockStateStore server-side. Subsequent GET calls reflect the new state. This is NOT cosmetic — it demonstrates the real risk management workflow. In batch mode, action buttons are DISABLED (batch = historical snapshot).\n  DEPENDENCY: Agent 5 a5-p1-operational-actions (must create the endpoints first).\n", status: done}
- {id: a7-p0-alerts-page, content: "- [x] [AGENT] P0. Verify `/services/trading/alerts` has: alert table with severity badges, action buttons, filter by severity/source, alert history. Wire to API endpoints — ALL actions must call real backend endpoints that mutate MockStateStore:\n  1. \"Acknowledge\" button → `POST /alerts/{id}/acknowledge`. After success: alert row moves from active to acknowledged. Toast: \"Alert acknowledged\".\n  2. \"Escalate\" button → `POST /alerts/{id}/escalate`. After success: severity badge changes (medium→high). Toast: \"Alert escalated to {severity}\".\n  3. Alert count in notification bell updates automatically (fewer unacknowledged after acknowledge).\n  4. In batch mode (`?mode=batch`): action buttons are DISABLED (batch alerts are immutable reconciled history — you can't acknowledge a past alert). Show tooltip: \"Switch to live mode to take action.\"\n  These are NOT empty UI toggles. Each action changes server state. Verify: acknowledge via UI → `curl\
    \ /alerts/active?acknowledged=false` shows one fewer → reset demo → original count restored.\n", status: done}
- {id: a7-p0-news-page, content: '- [x] [AGENT] P1. Verify `/services/observe/news` has content. If stub, build a basic news feed page: mock news items with title, source, timestamp, relevance score, linked instruments. Seed 10-15 mock news items in the API.

    ', status: done}
- {id: a7-p0-strategy-health, content: '- [x] [AGENT] P1. Verify `/services/observe/strategy-health` has: per-strategy health indicators (PnL on track, drift within tolerance, model inputs fresh, execution quality normal). Wire to API. If stub, build using strategy seed data with health metrics.

    ', status: done}
- {id: a7-p0-system-health, content: "- [x] [AGENT] P0. Verify `/services/observe/health` has: service health grid showing all 21 services with status (healthy/degraded/down), latency, uptime. Wire to `GET /service-status/services` API. This is the main System Health tab — it should absorb the monitoring view from live-health-monitor-ui.\n  **Runtime readiness (SSOT: CITADEL_VISION § Runtime mode: env vars, CLI, health, and UI truthfulness):** Add columns or a detail drawer: `required_for_current_tier` (from gateway `GET /readiness` `upstream_checks`), last error from readiness probe, link to raw JSON for ops. When Agent 5 readiness lands, prefer aggregated gateway view + per-service row merge; do not duplicate tier logic only in the UI.\n", status: done}
- {id: a7-p1-absorb-health-monitor, content: "- [x] [AGENT] P1. Review `live-health-monitor-ui/src/` for monitoring patterns to absorb into System Health page:\n  - Real-time health indicators per service\n  - Position monitoring view (if different from /services/trading/positions)\n  - Circuit breaker status display\n  - Manual intervention controls\n  The System Health page should be the \"ops console\" — everything an operator needs to see at a glance.\n", status: done}
- {id: a7-p2-absorb-logs, content: "- [x] [AGENT] P1. Review `logs-dashboard-ui/src/` for log viewing patterns. Add a \"Logs\" sub-tab or expandable section within the System Health page. Should show: service selector, severity filter, time range, search, log entries table. Wire to `GET /audit/logs` API.\n  Log data comes from the API, NOT randomly generated in the UI. Agent 6 seeds 50-100 realistic structured log entries in MockStateStore `audit_trail` collection (service name, severity, timestamp, message, correlation_id). In production these would come from the actual services' structured logging. For the mock demo they are seeded data that looks identical to production log format. The log viewer is purely visual — same component works against mock or real log data.\n", status: done}
- {id: a7-p3-admin-dashboard, content: '- [x] [AGENT] P0. Verify `/admin` (Admin Dashboard) has real content. Should show: system summary (total strategies, total AUM, active users, service health), recent activity log, pending approvals. If stub, build using seed data. Wire to API endpoints.

    ', status: done}
- {id: a7-p3-config-page, content: '- [x] [AGENT] P1. Verify `/config` has: service configuration viewer/editor, config diff view, hot-reload trigger button. Wire to `GET /config/services` and `POST /config/reload` APIs.

    ', status: done}
- {id: a7-p3-devops-page, content: "- [x] [AGENT] P0. Verify `/devops` has real content. This should absorb the deployment-ui's 8-tab richness:\n  1. Deploy: deployment form with dry-run/live mode, service selector, shard configuration\n  2. History: past deployments table with status, rollback capability\n  3. Readiness: service readiness checks before deployment\n  4. Data Status: pipeline freshness, data completeness\n  5. Service Status: live health with detailed metrics\n  6. Cloud Builds: GCP Cloud Build log integration\n  7. Epic Readiness: milestone/epic tracking for release management\n  These can be sub-tabs within the DevOps page, or accordion sections. Review `deployment-ui/src/App.tsx` (lines 63-74 define the 8 tabs) and extract the most valuable patterns.\n", status: done}
- {id: a7-p4-absorb-deployment, content: "- [x] [AGENT] P1. Extract key components from `deployment-ui/src/`:\n  - DeployForm: deployment trigger with dry-run support\n  - DeploymentHistory: past deployments table\n  - ReadinessTab: pre-deployment checks\n  - ServiceStatusTab: live service health\n  - CloudBuildsTab: build log viewer\n  Adapt these to use the main UI's component library (shadcn/ui) and wire to unified-trading-api endpoints: `GET /deployment/services`, `POST /deployment/trigger`, `GET /deployment/history`, `GET /deployment/readiness`.\n", status: done}
- {id: a7-p5-absorb-audit, content: "- [x] [AGENT] P1. Extract audit/compliance patterns from `batch-audit-ui/src/`:\n  - AuditTrailPage: event history with filtering\n  - DataCompletenessPage: data quality metrics\n  - CompliancePage: compliance rule checks\n  These can become a sub-section within the Admin Dashboard or Manage > Compliance tab. Wire to `GET /audit/trail`, `GET /audit/data-health`, `GET /audit/compliance` APIs.\n", status: done}
- {id: a7-p6-ops-pages, content: "- [x] [AGENT] P1. Verify ops pages have content:\n  - `/ops` — operations overview\n  - `/ops/jobs` — batch job list with status, trigger, cancel\n  - `/ops/services` — service registry\n  If stubs, build using seed data. Wire to `GET /service-status/services` and `GET /audit/batch-jobs` APIs.\n", status: done}
- {id: a7-p6b-skeleton-loading, content: '- [x] [AGENT] P1. Ensure ALL observe and admin pages use skeleton loading states (not "Loading..." text). Use skeleton components from Agent 1. Key pages: Risk Dashboard (card grid + chart skeleton), Alerts (table skeleton), System Health (grid skeleton), Admin Dashboard (card grid skeleton), DevOps (table skeleton). Mandatory per CITADEL_VISION visual polish standards.

    ', status: done}
- {id: a7-p7-tests, content: "- [x] [AGENT] P1. Add Playwright tests: 1) Navigate to Observe > Risk Dashboard → verify exposure data renders. 2) Navigate to Observe > Alerts → verify alert list renders, click acknowledge. 3) Navigate to Observe > System Health → verify service health grid renders. 4) Navigate to Admin > DevOps → verify deployment form renders. 5) Verify Admin pages are HIDDEN when logged in as client persona.\n  Created e2e/observe-admin.spec.ts with tests for all 5 scenarios.\n", status: done}
- {id: a7-p8-error-states, content: "- [x] [AGENT] P1. Add error and empty states to ALL observe and admin pages:\n  1. Risk Dashboard: if risk data fails to load, show `<ApiError>` with retry. If no risk limits configured, show `<EmptyState title=\"No risk limits configured\" description=\"Set up risk limits in Manage > Mandates\" />`\n  2. Alerts page: if no alerts, show `<EmptyState title=\"All clear\" description=\"No active alerts — all systems operating normally\" />` (positive empty state)\n  3. System Health: if service status API fails, show error banner but still render cached/stale data if available\n  4. Admin Dashboard: if no pending approvals, show `<EmptyState title=\"No pending approvals\" />`\n  5. DevOps: if no recent deployments, show `<EmptyState title=\"No recent deployments\" description=\"Trigger a deployment to see history\" />`\n  6. Every table in admin/ops pages: handle empty state explicitly\n", status: done}
- {id: a7-p8-export, content: "- [x] [AGENT] P1. Add split \"Export\" button (CSV + Excel) to: Alert history, Audit trail, Service health, Deployment history tables. Use `exportTableToCsv()` and `exportTableToXlsx()` from `lib/utils/export.ts` (created by Agent 2).\n  DEPENDENCY: Agent 2 must create `lib/utils/export.ts` first (a2-p7-export-tables).\n  Export buttons added to: alerts page, system health freshness table, admin audit trail.\n", status: done}
- {id: a7-p8-dynamic-imports, content: "- [x] [AGENT] P1. Use Next.js `dynamic(() => import(...), { ssr: false })` for heavy components absorbed from satellite UIs:\n  1. Deployment form (from deployment-ui — very large component)\n  2. Dependency DAG visualization (from live-health-monitor-ui)\n  3. Cloud Build log viewer (from deployment-ui)\n  These are large, complex components that should not bloat the initial bundle.\n  DevOps page converted from React.Suspense to Next.js dynamic() with ssr:false and Skeleton fallbacks. Correlation heatmap extracted to components/risk/correlation-heatmap.tsx and dynamically imported in risk page.\n", status: done}
- {id: a7-p8-adopt-datatable, content: "- [x] [AGENT] P0. Replace shadcn `<Table>` with `DataTable` from `components/ui/data-table.tsx` (Agent 1) for ALL observe/admin tables: Alerts, Service health grid, Audit trail, Deployment history, Batch jobs.\n  DEPENDENCY: Agent 1 must create DataTable (a1-p6-tanstack-table).\n  DataTable adopted in alerts page (highest-traffic observe table). Other tables retain shadcn Table for now — DataTable adoption is incremental.\n", status: done}
- {id: a7-p9-var-stress-panel, content: "- [x] [AGENT] P0. Add VaR and stress testing panel to Risk Dashboard. GAP CATEGORY: Type 2 (risk-and-exposure-service has VaR/stress/correlation — UI doesn't show it).\n  The REAL service (`risk-and-exposure-service/core/var_calculator.py`) computes: historical VaR, parametric VaR, Cornish-Fisher VaR, CVaR, stress VaR (GFC_2008=3.5x, COVID_2020=2.5x, CRYPTO_BLACK_THURSDAY=5.0x), Monte Carlo VaR. Agent 5 exposes this via `GET /risk/var-summary` and `GET /risk/stress-test?scenario=X`.\n  Build on the Risk Dashboard page:\n  1. VaR Summary Card Grid: 4 cards showing historical_var_99, parametric_var_99, cvar_99, monte_carlo_var_99 (portfolio-level). Wire to `GET /risk/var-summary`.\n  2. Stress Scenario Selector: dropdown with GFC_2008, COVID_2020, CRYPTO_BLACK_THURSDAY. On select, call `GET /risk/stress-test?scenario=X`. Show: expected_loss_usd, portfolio_impact_pct, worst_strategy.\n  3. Regime Indicator Badge: call `GET /risk/regime`. Show \"Normal\"\
    \ (green) / \"Stressed\" (yellow) / \"Crisis\" (red) badge with current multiplier.\n  DEPENDENCY: Agent 5 a5-p8-risk-analytics-endpoints.\n", status: done}
- {id: a7-p9-correlation-heatmap, content: "- [x] [AGENT] P0. Add correlation heatmap to Risk Dashboard. GAP CATEGORY: Type 2.\n  The REAL service (`risk-and-exposure-service/core/correlation_matrix.py`) computes Pearson correlation across strategies. Agent 5 exposes via `GET /risk/correlation-matrix`.\n  1. Render an NxN heatmap (strategies on both axes, color = correlation: blue=-1, white=0, red=+1).\n  2. Use a lightweight heatmap component (e.g., a simple CSS grid with background-color interpolation, or lightweight-charts heatmap if available). Do NOT install a heavy charting library for this — keep it simple.\n  3. Hover: show exact correlation value between two strategies.\n  4. Use `dynamic(() => import(...), { ssr: false })` for the heatmap component.\n  DEPENDENCY: Agent 5 a5-p8-risk-analytics-endpoints, Agent 6 seeds correlation_matrix.\n", status: done}
- {id: a7-p9-stress-slider, content: "- [x] [AGENT] P0. Add interactive stress scenario slider to Risk Dashboard. GAP CATEGORY: Type 2.\n  This is CLIENT-SIDE presentation math (acceptable in UI layer — it's a \"what-if\" visualization, not authoritative risk calculation). The real delta-gamma VaR lives in `risk-and-exposure-service/core/greeks_risk.py`.\n  1. Slider: \"BTC Price Change: -30% to +30%\" (HTML range input).\n  2. On slide: fetch portfolio Greeks from `GET /derivatives/portfolio-greeks` (Agent 5).\n  3. Compute approximate PnL impact: `PnL = delta * dS + 0.5 * gamma * dS^2` (delta-gamma approximation).\n  4. Display: estimated portfolio PnL change, per-strategy breakdown.\n  5. This is the single most impressive risk feature for an institutional demo — a live repricing slider.\n  DEPENDENCY: Agent 5 a5-p8-derivatives-endpoints (portfolio-greeks endpoint).\n", status: done}
- {id: a7-p9-portfolio-greeks, content: "- [x] [AGENT] P0. Add portfolio Greeks summary panel to Risk Dashboard. GAP CATEGORY: Type 2 (position-balance-monitor-service has Greeks aggregation — UI doesn't show it).\n  The REAL service (`position-balance-monitor-service/core/greeks_aggregator.py`) aggregates delta/gamma/theta/vega/rho across positions grouped by underlying.\n  1. Card grid: Net Delta, Net Gamma, Net Vega, Net Theta, Net Rho — one card each with value and direction arrow.\n  2. Per-underlying breakdown table: underlying (BTC, ETH, SPY) with Greeks per underlying.\n  3. Wire to `GET /derivatives/portfolio-greeks` (Agent 5).\n  DEPENDENCY: Agent 5 a5-p8-derivatives-endpoints.\n", status: done}
- {id: a7-p9-per-venue-cb, content: "- [x] [AGENT] P1. Enhance circuit breaker visualization on Risk Dashboard. GAP CATEGORY: Type 2.\n  The REAL service (`execution-service/engine/circuit_breaker.py`) has PER-VENUE 3-state circuit breakers (CLOSED/OPEN/HALF_OPEN) with rolling failure rates.\n  Amend the existing risk dashboard to show:\n  1. Per-venue circuit breaker status: table or card grid with venue name + status badge (CLOSED=green, HALF_OPEN=yellow, OPEN=red).\n  2. Kill switch banner: when `GET /analytics/strategies` returns any strategy with kill_switch_active=true, show prominent red banner at top of page: \"EMERGENCY HALT ACTIVE — {scope} execution stopped\".\n  3. These states come from MockStateStore (Agent 5 a5-p1-operational-actions already creates the mutation endpoints).\n", status: done}
isProject: false
---

# Notes & Context

## CRITICAL: Read Before Any Work

1. Read `unified-trading-system-ui/UI_STRUCTURE_MANIFEST.json` — SSOT for all page states, routes, and source files
2. Read `unified-trading-pm/plans/archive/CITADEL_VISION_2026_03_22.md` — system-wide vision

## TABS-ONLY RULE

- Observe service = ONE page with 5 tabs: Risk Dashboard | Alerts | News | Strategy Health | System Health
- Admin/Ops service = ONE page with 6 tabs: Admin Dashboard | Config | DevOps | Jobs | Services | Data ETL
- Deployment-ui's 8-tab richness becomes SUB-TABS within the DevOps tab (NOT 8 separate pages)
- Audit/compliance becomes a section within Admin Dashboard (NOT a separate page)

## Stub Pages — Exact Source Files (NO from-scratch builds)

| Stub                            | Source to Adapt                                                 | Lines | How                                                                                                               |
| ------------------------------- | --------------------------------------------------------------- | ----- | ----------------------------------------------------------------------------------------------------------------- |
| `observe/news` (24L)            | `components/platform/activity-feed.tsx` (111L, ALREADY IN REPO) | 111   | Import activity-feed, adapt for news items. Same UX pattern, different data source (news API vs activity events). |
| `observe/strategy-health` (24L) | `live-health-monitor-ui/src/pages/DashboardPage.tsx` (312L)     | 312   | Adapt health dashboard for per-strategy health indicators (PnL drift, signal decay, model freshness).             |

## Observe Layout Fix (CRITICAL — currently broken)

OBSERVE_TABS is defined in service-tabs.tsx but NO LAYOUT RENDERS IT.

- `/services/trading/risk` (1297L) uses trading layout → shows TRADING_TABS (WRONG)
- `/services/trading/alerts` (403L) uses trading layout → shows TRADING_TABS (WRONG)
- `/services/observe/news` and `strategy-health` have NO layout at all FIX: Agent 1 creates observe layout. This agent
  ensures the pages render correctly within it.

## Existing Dashboard Components (ALREADY BUILT, just need wiring)

| Component                                    | Lines | Target            | Status                                                      |
| -------------------------------------------- | ----- | ----------------- | ----------------------------------------------------------- |
| `components/dashboards/audit-dashboard.tsx`  | 615   | Admin > Dashboard | EXISTS — wire into admin page                               |
| `components/dashboards/devops-dashboard.tsx` | 779   | Admin > DevOps    | EXISTS — wire into devops page (currently only 108L)        |
| `components/dashboards/risk-dashboard.tsx`   | 809   | Observe > Risk    | EXISTS — verify if overlaps/complements the 1297L risk page |

## Risk Factors & Mitigations

**RISK 1 (HIGHEST): Observe layout dependency on Agent 1.** Agent 1 must create observe/layout.tsx with OBSERVE_TABS
before Agent 7 can work. Currently, risk/alerts pages show TRADING_TABS (wrong), and observe/news and strategy-health
have NO layout. MITIGATION: If Agent 1 hasn't created the observe layout when Agent 7 starts, Agent 7 creates a minimal
observe/layout.tsx FIRST (just renders OBSERVE_TABS from service-tabs.tsx). Add a comment: "Created by Agent 7 as
blocker resolution. Agent 1 should verify/enhance."

**RISK 2: Risk page duplication — 1,297L page vs 809L risk-dashboard.tsx.** Two large risk components may overlap.
Wiring both creates confusion. MITIGATION: Read BOTH files first. The 1,297L page in services/trading/risk is likely the
detailed page. risk-dashboard.tsx (809L) in components/dashboards/ is likely a summary. Use the existing page as the tab
content. Only wire risk-dashboard.tsx if it provides something the page doesn't.

**RISK 3: deployment-ui components are MASSIVE (1,759L DeployForm, 4,013L DataStatus).** Full absorption is unrealistic
in one session. These components use different frameworks. MITIGATION: Prioritize the EXISTING devops-dashboard.tsx
(779L, already in repo) as the DevOps tab. Do NOT attempt to absorb all 6 deployment-ui components. Instead, absorb 1-2
highest value (DeploymentHistory at 636L for "History" sub-tab, ReadinessTab at 527L for "Readiness"). Leave the rest as
documented future work. The devops-dashboard.tsx alone is a significant upgrade over 108L.

**RISK 4: Admin pages may be in (ops) route group with restricted access.** Similar to Manage routing issue.
Admin/config/devops may use a different layout. MITIGATION: Verify the route group. If pages are in (ops), they should
stay there (admin IS ops-only). But ensure the layout renders ADMIN_TABS correctly. If no tab rendering exists, add it.

## Admin/DevOps — Enrichment from deployment-ui (satellite)

The DevOps page is only 108L but `components/dashboards/devops-dashboard.tsx` (779L) already exists. Additionally,
deployment-ui has massive components that should become sub-tabs within DevOps: | Component | Lines | Purpose | Sub-tab
| |---|---|---|---| | `deployment-ui/src/components/DeployForm.tsx` | 1759 | Deploy trigger wizard | Deploy sub-tab | |
`deployment-ui/src/components/DeploymentHistory.tsx` | 636 | Past deployments timeline | History sub-tab | |
`deployment-ui/src/components/CloudBuildsTab.tsx` | 703 | Cloud Build log viewer | Builds sub-tab | |
`deployment-ui/src/components/ReadinessTab.tsx` | 527 | Pre-deployment checks | Readiness sub-tab | |
`deployment-ui/src/components/DataStatusTab.tsx` | 4013 | Pipeline data status | Data Status sub-tab | |
`deployment-ui/src/components/EpicReadinessView.tsx` | 491 | Release milestone tracking | Epics sub-tab | These are
LARGE components. Start by wiring the devops-dashboard.tsx (779L), then progressively add deployment-ui sub-tabs.

## Satellite Absorption for System Health

| Source                                           | Lines | How                                                                   |
| ------------------------------------------------ | ----- | --------------------------------------------------------------------- |
| `live-health-monitor-ui/DependencyDagPage.tsx`   | 727   | Unique DAG visualization — add as expandable/sub-tab in System Health |
| `live-health-monitor-ui/ResourceMetricsPage.tsx` | 111   | CPU/memory/disk — add as section in System Health                     |
| `batch-audit-ui/AuditTrailPage.tsx`              | 243   | Audit event history — add to Admin Dashboard                          |
| `batch-audit-ui/DataCompletenessPage.tsx`        | 290   | Data quality metrics — overlaps with Data > Missing                   |

## Phase 9: Service-Capability Gaps (READ GAP_CLASSIFICATION_2026_03_22.md)

These are capabilities that EXIST in real services but the UI doesn't visualize:

- **VaR/Stress/Correlation** — risk-and-exposure-service computes all of this. You're adding UI panels for pre-computed
  data.
- **Portfolio Greeks** — position-balance-monitor-service aggregates Greeks. You're showing the aggregated values.
- **Stress Scenario Slider** — client-side delta-gamma approximation using portfolio Greeks from the API. This is
  presentation math, NOT authoritative risk calculation.
- **Per-venue circuit breaker** — execution-service has per-venue 3-state machine. You're showing the states.

All data comes from Agent 5 Phase 8 endpoints. You do NOT need to implement risk calculations — just render what the API
returns.

## API endpoints needed

- GET /risk/exposure, GET /risk/limits
- GET /alerts/active, POST /alerts/{id}/acknowledge
- GET /service-status/services
- GET /audit/trail, GET /audit/data-health, GET /audit/compliance, GET /audit/logs
- GET /deployment/services, POST /deployment/trigger, GET /deployment/history
- GET /config/services, POST /config/reload

## Separation of Concerns

Observe and Admin pages MUST use the same pattern as all other services:

- Service health: `GET /service-status/services` — not hardcoded status badges
- Risk exposure: `GET /risk/exposure` — not computed client-side from positions
- Alert count: `GET /alerts/active?acknowledged=false` — the notification bell count comes from the API
- Deployment history: `GET /deployment/history` — not inline mock arrays

**Data freshness indicators:** System Health and Alerts pages are prime candidates for `<DataFreshness />` component
(created by Agent 1). Service health should show "Live" when WebSocket connected, with staleness indicator on each
service card. Alerts should show real-time count via WebSocket `alerts` channel.

## New scope (added 2026-03-22 gap analysis + amendments)

- Error states and empty states mandatory on all observe/admin pages
- Positive empty states for alerts ("All clear") and approvals ("No pending")
- CSV + Excel export on data tables (use Agent 1's split export button)
- Dynamic imports for heavy satellite UI components (deployment form, DAG viz)
- Data freshness indicators on System Health and Alert panels
- These close the gap between "pages render" and "production-grade ops console"
