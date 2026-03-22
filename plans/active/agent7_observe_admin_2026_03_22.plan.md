---
name: agent7-observe-admin
overview:
  Absorb deployment-ui, batch-audit-ui, live-health-monitor-ui, logs-dashboard-ui into Observe and Admin services
todos:
  - id: a7-p0-risk-dashboard
    content: |
      - [ ] [AGENT] P0. Verify `/services/trading/risk` has real content: exposure breakdown (by venue, asset class, strategy), VaR calculation, Greeks display (delta, gamma, vega, theta), stress scenarios, limit utilization bars. Wire to `GET /risk/exposure`, `GET /risk/limits` APIs. If stub, build using seed data.
    status: todo
  - id: a7-p0-alerts-page
    content: |
      - [ ] [AGENT] P0. Verify `/services/trading/alerts` has: alert table with severity badges, acknowledge button, filter by severity/source, alert history. Wire to `GET /alerts/active` and `POST /alerts/{id}/acknowledge` APIs. In mock mode, acknowledging should update MockStateStore.
    status: todo
  - id: a7-p0-news-page
    content: |
      - [ ] [AGENT] P1. Verify `/services/observe/news` has content. If stub, build a basic news feed page: mock news items with title, source, timestamp, relevance score, linked instruments. Seed 10-15 mock news items in the API.
    status: todo
  - id: a7-p0-strategy-health
    content: |
      - [ ] [AGENT] P1. Verify `/services/observe/strategy-health` has: per-strategy health indicators (PnL on track, drift within tolerance, model inputs fresh, execution quality normal). Wire to API. If stub, build using strategy seed data with health metrics.
    status: todo
  - id: a7-p0-system-health
    content: |
      - [ ] [AGENT] P0. Verify `/services/observe/health` has: service health grid showing all 21 services with status (healthy/degraded/down), latency, uptime. Wire to `GET /service-status/services` API. This is the main System Health tab — it should absorb the monitoring view from live-health-monitor-ui.
    status: todo
  - id: a7-p1-absorb-health-monitor
    content: |
      - [ ] [AGENT] P1. Review `live-health-monitor-ui/src/` for monitoring patterns to absorb into System Health page:
        - Real-time health indicators per service
        - Position monitoring view (if different from /services/trading/positions)
        - Circuit breaker status display
        - Manual intervention controls
        The System Health page should be the "ops console" — everything an operator needs to see at a glance.
    status: todo
  - id: a7-p2-absorb-logs
    content: |
      - [ ] [AGENT] P1. Review `logs-dashboard-ui/src/` for log viewing patterns. Add a "Logs" sub-tab or expandable section within the System Health page. Should show: service selector, severity filter, time range, search, log entries table. Wire to `GET /audit/logs` API. In mock mode, seed 50-100 mock log entries across multiple services.
    status: todo
  - id: a7-p3-admin-dashboard
    content: |
      - [ ] [AGENT] P0. Verify `/admin` (Admin Dashboard) has real content. Should show: system summary (total strategies, total AUM, active users, service health), recent activity log, pending approvals. If stub, build using seed data. Wire to API endpoints.
    status: todo
  - id: a7-p3-config-page
    content: |
      - [ ] [AGENT] P1. Verify `/config` has: service configuration viewer/editor, config diff view, hot-reload trigger button. Wire to `GET /config/services` and `POST /config/reload` APIs.
    status: todo
  - id: a7-p3-devops-page
    content: |
      - [ ] [AGENT] P0. Verify `/devops` has real content. This should absorb the deployment-ui's 8-tab richness:
        1. Deploy: deployment form with dry-run/live mode, service selector, shard configuration
        2. History: past deployments table with status, rollback capability
        3. Readiness: service readiness checks before deployment
        4. Data Status: pipeline freshness, data completeness
        5. Service Status: live health with detailed metrics
        6. Cloud Builds: GCP Cloud Build log integration
        7. Epic Readiness: milestone/epic tracking for release management
        These can be sub-tabs within the DevOps page, or accordion sections. Review `deployment-ui/src/App.tsx` (lines 63-74 define the 8 tabs) and extract the most valuable patterns.
    status: todo
  - id: a7-p4-absorb-deployment
    content: |
      - [ ] [AGENT] P1. Extract key components from `deployment-ui/src/`:
        - DeployForm: deployment trigger with dry-run support
        - DeploymentHistory: past deployments table
        - ReadinessTab: pre-deployment checks
        - ServiceStatusTab: live service health
        - CloudBuildsTab: build log viewer
        Adapt these to use the main UI's component library (shadcn/ui) and wire to unified-trading-api endpoints: `GET /deployment/services`, `POST /deployment/trigger`, `GET /deployment/history`, `GET /deployment/readiness`.
    status: todo
  - id: a7-p5-absorb-audit
    content: |
      - [ ] [AGENT] P1. Extract audit/compliance patterns from `batch-audit-ui/src/`:
        - AuditTrailPage: event history with filtering
        - DataCompletenessPage: data quality metrics
        - CompliancePage: compliance rule checks
        These can become a sub-section within the Admin Dashboard or Manage > Compliance tab. Wire to `GET /audit/trail`, `GET /audit/data-health`, `GET /audit/compliance` APIs.
    status: todo
  - id: a7-p6-ops-pages
    content: |
      - [ ] [AGENT] P1. Verify ops pages have content:
        - `/ops` — operations overview
        - `/ops/jobs` — batch job list with status, trigger, cancel
        - `/ops/services` — service registry
        If stubs, build using seed data. Wire to `GET /service-status/services` and `GET /audit/batch-jobs` APIs.
    status: todo
  - id: a7-p7-tests
    content: |
      - [ ] [AGENT] P1. Add Playwright tests: 1) Navigate to Observe > Risk Dashboard → verify exposure data renders. 2) Navigate to Observe > Alerts → verify alert list renders, click acknowledge. 3) Navigate to Observe > System Health → verify service health grid renders. 4) Navigate to Admin > DevOps → verify deployment form renders. 5) Verify Admin pages are HIDDEN when logged in as client persona.
    status: todo
isProject: false
---

# Notes & Context

## Key source repos for absorption

- `deployment-ui/src/App.tsx` — 8-tab structure (lines 63-74)
- `deployment-ui/src/components/` — DeployForm, DeploymentHistory, ReadinessTab, etc.
- `batch-audit-ui/src/pages/` — AuditTrailPage, DataCompletenessPage, CompliancePage
- `live-health-monitor-ui/src/` — health monitoring patterns
- `logs-dashboard-ui/src/` — log viewing patterns
- `_reference/deployment-ui/` — additional deployment patterns
- `_reference/versa-audit-ui/` — audit trail patterns
- `_reference/versa-admin-ui/` — admin surface patterns

## Absorbed from prior plans

- full_system_audit_resolution_2026_03_18: System audit findings and remediations
- cicd_code_rollout_master_2026_03_13: CI/CD pipeline improvements
- quality_gates_systemic_remediation_2026_03_16: Quality gate fixes

## API endpoints needed

- GET /risk/exposure, GET /risk/limits
- GET /alerts/active, POST /alerts/{id}/acknowledge
- GET /service-status/services
- GET /audit/trail, GET /audit/data-health, GET /audit/compliance, GET /audit/logs
- GET /deployment/services, POST /deployment/trigger, GET /deployment/history
- GET /config/services, POST /config/reload
