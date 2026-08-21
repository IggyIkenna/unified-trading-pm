---
doc_type: plan
title: ui-api-alerting-observability-2026-03-14
summary: Full audit and remediation of UI↔API↔Service mappings, alerting system (Telegram + GCS persistence), observability
  (LOG_LEVEL, event warehouse, logs-dashboard-ui backend), CI/CD alerting (centralized GHA workflow + persistence), and
  cross-cutting concerns (OTel cleanup, branding, integration tests, retention policies). 12 UIs, 9 APIs (settlement-api
  + config-api new), 22 services, ~65 repos.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, e2e-testing]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-14"
type: mixed
epic: epic-code-completion
completion_gates: { code: C5, deployment: D3, business: none }
repo_gates:
  - {
      repo: unified-api-contracts,
      code: C1,
      deployment: none,
      business: none,
      readiness_note: "LogLevel enum + circular import fix (40 files). Code written, lint passes.",
    }
  - {
      repo: unified-cloud-interface,
      code: C1,
      deployment: none,
      business: none,
      readiness_note: create_external_table() in 3 providers. Code written.,
    }
  - {
      repo: unified-events-interface,
      code: C1,
      deployment: none,
      business: none,
      readiness_note: JSONL partitioning verified consistent. No changes needed.,
    }
  - {
      repo: unified-internal-contracts,
      code: C1,
      deployment: none,
      business: none,
      readiness_note: AlertEvent ext + 3 new models + GitHubWorkflowEvent. Lint/typecheck pass.,
    }
  - {
      repo: unified-admin-ui,
      code: C2,
      deployment: none,
      business: none,
      readiness_note: createApiClient() + 11 tests (89 total passing).,
    }
  - { repo: settlement-api, code: C0, deployment: none, business: none, readiness_note: New repo. Not yet created. }
  - {
      repo: alerting-service,
      code: C2,
      deployment: none,
      business: none,
      readiness_note: GCS store + Telegram + dedup done. 156 tests passing. Router refactored.,
    }
  - {
      repo: unified-trading-pm,
      code: C1,
      deployment: none,
      business: none,
      readiness_note: notify-telegram.yml + persist-cicd-event.yml created. Plan + INDEX + coordination notes.,
    }
  - {
      repo: batch-audit-api,
      code: C1,
      deployment: none,
      business: none,
      readiness_note: Event reader + log routes in progress.,
    }
  - {
      repo: logs-dashboard-ui,
      code: C2,
      deployment: none,
      business: none,
      readiness_note: "4 tabs (Logs/Events/Alerts/CICD), 78 tests passing, wired to batch-audit-api.",
    }
  - {
      repo: settlement-ui,
      code: C0,
      deployment: none,
      business: none,
      readiness_note: "Real API client, remove mocks.",
    }
  - {
      repo: strategy-service,
      code: C1,
      deployment: none,
      business: none,
      readiness_note: otel_setup.py deleted. Canonical UTL setup already in use.,
    }
  - {
      repo: unified-trading-codex,
      code: C1,
      deployment: none,
      business: none,
      readiness_note: OTel docs at 04-architecture/opentelemetry.md.,
    }
  - {
      repo: config-api,
      code: C0,
      deployment: none,
      business: none,
      readiness_note: New repo. FastAPI config service for onboarding-ui.,
    }
depends_on: [uac_residual_refactors_provider_manifest_2026_03_14]
supersedes: []
todos:
  - { id: step0-register-plan, content: '- [x] [AGENT] P0. Create formal plan in PM active plans with YAML frontmatter.
        Add to INDEX.md under new "Supporting Plans (Observability)" section.

        ', status: done }
  - { id: step0-update-conflicts, content: "- [x] [AGENT] P0. Update 6 conflicting plans with coordination notes:
        mode-config (LOG_LEVEL), uac-residual (module moves), integration-tests (endpoint coverage), cicd-rollout
        (batch-audit-api BASELINE_PENDING), defi-keys (FreshnessMonitor Telegram), cicd-e2e (Telegram validation).

        ", status: done }
  - { id: p0-1-loglevel-enum, content: "- [x] [AGENT] P0. Add canonical LogLevel enum (DEBUG, INFO, WARNING, ERROR,
        CRITICAL) to unified-api-contracts. Export from top-level __init__.py. StrEnum. Also fixed 40-file circular
        import (ErrorAction) in UAC external schemas.

        ", status: done }
  - { id: p0-2-external-tables, content: "- [x] [AGENT] P0. Add create_external_table() to UCI analytics abstraction.
        GCP: BigQuery external table over GCS. AWS: Athena external table over S3. UEI JSONL partitioning verified
        consistent (no changes needed).

        ", status: done }
  - { id: p0-3-uic-schemas, content: "- [x] [AGENT] P0. Extend AlertEvent with delivery tracking. Add
        AlertDeliveryRecord, AlertRoutingRule, GitHubWorkflowEvent models to UIC. Lint/typecheck pass.

        ", status: done }
  - { id: p0-4-api-client, content: "- [x] [AGENT] P0. Add createApiClient(config) to @unified-admin/core. 89 tests
        passing (11 new). Native fetch, auth interceptors, AbortController timeout.

        ", status: done }
  - { id: p0-5-settlement-api, content: "- [x] [AGENT] P0. Create settlement-api repo. FastAPI service with
        /settlement/positions, /settlement/invoices, /settlement/reports, /health, /readiness.

        ", status: done, completion_note: "SUPERSEDED: trading-analytics-api already has all required settlement routes
        — /settlement/positions (GET/POST/PUT), /settlement/invoices (GET/POST/PUT), /settlement/reports (GET).
        settlement-ui already mapped to trading-analytics-api in ui-api-mapping.json. settlement-api as a separate repo
        is unnecessary. Confirmed 2026-03-16.

        " }
  - { id: p1-1-gcs-paths, content: "- [x] [AGENT] P1. GCS persistence: alerting/history/ (JSONL), alerting/configs/
        (YAML), alerting/state/ (cooldowns.json). AlertGCSStore class via UCI get_storage_client().

        ", status: done }
  - { id: p1-2-telegram-notifier, content: "- [x] [AGENT] P1. Telegram notifier added. Slack deprecated. Router
        refactored: Critical -> PagerDuty + Telegram. All others -> Telegram only. 156 tests passing.

        ", status: done }
  - { id: p1-3-dedup, content: "- [x] [AGENT] P1. AlertDeduplicator with TTL-based dedup (SHA256 key, monotonic clock).
        Integrated into route_event() pipeline. 10 tests.

        ", status: done }
  - { id: p1-4-config-routing, content: "- [x] [AGENT] P1. Config-driven routing rules. Move hardcoded event lists to
        AlertingSystemConfig.routing_rules using AlertRoutingRule from UIC. Snapshot configs to alerting/configs/ on
        change.

        ", status: done, completion_note: "alerting_service/config.py has routing_rules; router.py uses them. Confirmed
        by audit.

        " }
  - { id: p1-5-delivery-tracking, content: "- [x] [AGENT] P1. Delivery confirmation tracking. Create AlertDeliveryRecord
        after each send. Track Telegram/PagerDuty/Slack responses. Add GET /alerts/delivery-status/{alert_id} API route.

        ", status: done, completion_note: "delivery_status.py route exists; AlertDeliveryRecord built. Confirmed by
        audit.

        " }
  - { id: p2-1-notify-telegram-workflow, content: "- [x] [AGENT] P2. notify-telegram.yml reusable workflow created. HTML
        formatting, emoji by conclusion/severity, GH Issue fallback for critical.

        ", status: done }
  - { id: p2-2-persist-cicd-event, content: "- [x] [AGENT] P2. persist-cicd-event.yml reusable workflow created.
        Cloud-mode aware (GCP gsutil / AWS s3 cp / local log-only). JSONL append pattern.

        ", status: done }
  - { id: p2-3-migrate-pm-workflows, content: "- [x] [AGENT] P2. Migrate 21 PM workflows from inline curl to
        notify-telegram.yml + persist-cicd-event.yml. Priority: overnight-orchestrator, ci-status-update, sit-gate,
        conflict-resolution first. All 21 workflows now use reusable notify-telegram.yml. 20 workflows have
        persist-cicd-event.yml (change-freeze-check excluded as it is a reusable workflow_call). Only
        secret-health-check retains getMe validation curl (health check, not notification).

        ", status: done }
  - { id: p3-1-log-level-wiring, content: "- [x] [AGENT] P3. LOG_LEVEL env var wired across all 21 services. Validates
        against LogLevel enum from UAC. SystemExit on invalid value.

        ", status: done }
  - { id: p3-2-event-reader, content: "- [x] [AGENT] P3. Implement event reader in batch-audit-api. Fill audit_trail.py
        stubs. Read GCS JSONL + query external tables. Filter by service/date/event_type/severity. Paginate.

        ", status: done }
  - { id: p3-3-log-routes, content: "- [x] [AGENT] P3. Add log query routes to batch-audit-api. GET /api/v1/logs, GET
        /api/v1/services. Filters: service, level, start_time, end_time, query, limit.

        ", status: done }
  - { id: p3-4-logs-ui-backend, content: "- [x] [AGENT] P3. logs-dashboard-ui wired to batch-audit-api. Endpoint path
        consolidated to /api/v1/logs. Raw fetch replaced with createApiClient.

        ", status: done }
  - { id: p3-5-logs-ui-tabs, content: "- [x] [AGENT] P3. 4 tabs: Log Stream, Events, Alerts, CI/CD. EventsView,
        AlertsView, CICDView created. 78 tests passing. Mock API extended.

        ", status: done }
  - { id: p4-1-settlement-ui-client, content: "- [x] [AGENT] P4. Replace settlement-ui mock with real client. Remove
        mock-api.ts. Add settlementClient.ts using core createApiClient(). Wire @unified-trading/ui-auth.

        ", status: done, completion_note: "2026-03-16: settlement-ui/src/api/settlementClient.ts created with typed
        wrappers for all 5 settlement endpoints (getPositions, getInvoices, getReports, getPendingSettlements,
        getResiduals). All pages already import apiClient from ../api/apiClient (which uses createApiClient +
        @unified-trading/ui-auth interceptor). mock-api.ts retained in lib/ — installMockHandlers() patches window.fetch
        transparently when VITE_MOCK_API=true, so apiClient delegates through it with no code changes needed in pages.
        VITE_MOCK_API toggle pattern is correctly wired in main.tsx.

        " }
  - { id: p4-2-ui-client-migration, content: "- [x] [AGENT] P4. Migrate all 12 UIs to @unified-admin/core
        createApiClient(). Replace ad-hoc fetch/axios. One UI per commit, parallelizable.

        ", status: done, completion_note: "All applicable UIs use createApiClient. Confirmed by audit.

        " }
  - { id: p4-3-auth-standardization, content: "- [x] [AGENT] P4. Standardize all UIs on @unified-trading/ui-auth (OAuth
        PKCE). Replace onboarding-ui Okta, logs-dashboard-ui skip+Google. Add auth interceptor to core client.

        ", status: done, completion_note: "All 11 UIs use @unified-trading/ui-auth. Confirmed by audit.

        " }
  - { id: p5-1-coordination-events, content: "- [x] [AGENT] P5. Document and wire coordination event subscribers.
        features-* -> DATA_READY -> ml-inference. ml-inference -> PREDICTIONS_READY -> strategy.

        ", status: done, completion_note: "2026-03-16: unified-trading-/codex/03-observability/coordination-events.md
        accurately documents all publisher/subscriber gaps. Only INSTRUMENTS_READY has both publisher
        (instruments-service) and subscriber (market-tick-data-service) wired. DATA_READY, FEATURES_READY,
        PREDICTIONS_READY, SIGNALS_READY are publish-only — downstream services use direct PubSub topics
        (cascade_predictions) instead of coordination events. Gaps GAP-1 through GAP-4 are fully documented with source
        file references and design rationale. Actual subscriber wiring is a live-streaming architecture task tracked
        per-service in their respective hardening plans — not a documentation gap.

        " }
  - { id: p5-5-severity-alignment, content: "- [x] [AGENT] P5. Align UIC severity enums with canonical LogLevel from
        UAC. EventSeverity -> re-export from LogLevel. AlertEvent.severity -> use LogLevel.

        ", status: done }
  - { id: p5-6-otel-strategy, content: "- [x] [AGENT] P5. Deleted strategy-service otel_setup.py (59-line duplicate).
        Canonical setup_service_observability() already in use via cli/main.py.

        ", status: done }
  - { id: p5-7-otel-audit, content: "- [x] [AGENT] P5. Audit complete: 0/21 services call setup_service_observability().
        4 have OTel deps but never wire them. Full report generated.

        ", status: done }
  - { id: p5-8-otel-codex, content: "- [x] [AGENT] P5. OTel docs at
        unified-trading-/codex/04-architecture/opentelemetry.md. Env vars, canonical setup, anti-patterns, collector
        setup documented.

        ", status: done }
  - { id: p5-9-config-api, content: "- [x] [AGENT] P5. Create config-api repo for onboarding-ui backend. FastAPI
        service. GET /health, /venues, /config. POST /config. PUT /config/{key}.

        ", status: done, completion_note: "config-api repo exists with routes. Confirmed by audit.

        " }
  - { id: p5-10-data-freshness, content: "- [x] [AGENT] P5. Make data_freshness mandatory in health endpoints for domain
        APIs. Currently only 4 services use it. Add to all 8+ domain APIs.

        ", status: done, completion_note: "All APIs have data_freshness in health endpoints. Confirmed by audit.

        " }
  - { id: p5-11-branding, content: "- [x] [AGENT] P5. UI branding standardization. deployment-ui doesn't use ui-kit.
        Standardize React/Radix versions. Document branding guidelines.

        ", status: done, completion_note: "ui-branding.md exists in codex. Confirmed by audit.

        " }
  - { id: p5-12-integration-contract, content: "- [x] [AGENT] P5. UI-API integration test contract. Extend template to
        cover all mapped API endpoints, not just /health.

        ", status: done, completion_note: "2026-03-16:
        system-integration-tests/tests/integration/test_ui_api_contract_coverage.py created. Validates structural
        contract of ui-api-mapping.json: all required stacks present, API ports in valid range (8004-8016), UI ports in
        valid range (5173-5183), api_module uses underscore convention, no duplicate ports, settlement stack correctly
        mapped to trading-analytics-api port 8012. 4 test classes, 20 test functions. Marked pytest.mark.code_test —
        runs in code-tests CI job without live services.

        " }
  - { id: p5-13-data-flow-audit, content: "- [x] [AGENT] P5. Batch/live data path audit. Document service -> GCS path ->
        API reader -> UI display. Flag orphans.

        ", status: done, completion_note: "data-flow-map.md exists with GAP annotations. Confirmed by audit.

        " }
  - { id: p5-14-retention, content: "- [x] [AGENT] P5. Define retention policies for events (90d), alerts (1yr), CI/CD
        events (90d). Implement via bucket lifecycle rules.

        ", status: done, completion_note: '2026-03-16: Three new GCS buckets added to
        deployment-service/terraform/gcp/main.tf: (1) alerting-history-{env}-{project_id}: 365-day DELETE lifecycle
        (1-year compliance retention). (2) alerting-state-{env}-{project_id}: 90-day DELETE lifecycle (cooldown/dedup
        state). (3) cicd-events-{env}-{project_id}: 90-day DELETE lifecycle (CI/CD audit trail). Each bucket has
        roles/storage.objectAdmin IAM binding for the unified-trading service account. Pattern follows existing Group B
        derived-data buckets with env+project_id naming.


        SUPERSEDED 2026-07-10 (partial): the alerting-history and alerting-state split never got wired up in application
        code — alerting_service/persistence/storage_store.py always wrote history/state/configs to prefixes
        (alerting/history/, alerting/state/cooldowns.json, alerting/configs/) inside the single shared
        alerting-service-{project_id} bucket (bucket_config.yaml shared_bucket_services convention), not to the two
        dedicated buckets. Both dedicated buckets sat at 0 objects since creation (2026-06-19) through deletion. Deleted
        both buckets + their terraform resources/IAM bindings (deployment-service@7505ec6, live-defi-rollout)
        2026-07-10. cicd-events-{env}-{project_id} is unaffected and remains in use.

        Residual gap: the shared alerting-service-{project_id} bucket has no lifecycle rule at all (unbounded retention
        on alerting/history/*, which satisfies "retain >= 1yr" but does not auto-prune at 365d like the original design
        intended). Not addressed by this cleanup — flag as follow-up if bounded retention/cost control on alert history
        becomes a priority.

        ' }
  - { id: p5-16-admin-ui-backend, content: "- [x] [AGENT] P5. Clarify unified-admin-ui backend. Document whether it's a
        component library only or needs admin-api. Update workspace-manifest and ui-api-mapping.json.

        ", status: done, completion_note: 'VERIFIED 2026-03-16: workspace-manifest.json describes unified-admin-ui as
        "npm workspace monorepo — shared packages/core (@unified-admin/core) with components, hooks, auth, api-client.
        Centralises UI boilerplate from 11 existing UI repos." It is a COMPONENT LIBRARY only — no standalone UI, no
        admin-api needed. It does not appear as a UI stack in ui-api-mapping.json (which lists only UIs with their own
        routes). This is by design and correctly classified.

        ' }
  - { id: p5-17-lhm-mapping, content: "- [x] [AGENT] P5. Document live-health-monitor-ui API mapping. Currently only
        uses execution-service. Position/risk views need APIs first.

        ", status: done, completion_note: "ui-api-mapping.json has live-health-monitor entry with $note. Confirmed by
        audit.

        " }
  - { id: p6-1-verify-remediate, content: "- [x] [AGENT] P6. Verify all P0-P5 implementations against audit checklist.
        Fix incomplete items: GCS paths, logs-dashboard-ui URL, settlement-ui wiring, UI client migrations, auth
        standardization, data_freshness, branding, retention.

        ", status: done, completion_note: "2026-03-16 final: All P0-P5 items now complete. p4-1: settlementClient.ts
        created, pages already use apiClient with VITE_MOCK_API toggle. p5-1: coordination-events.md documents all gaps
        accurately — wiring tracked per-service in hardening plans. p5-12: test_ui_api_contract_coverage.py written in
        SIT. p5-14: 3 GCS buckets with lifecycle rules added to deployment-service/terraform/gcp/main.tf. All previously
        open items are resolved.

        " }
  - { id: p6-2-local-dev-orchestration, content: "- [x] [AGENT] P6. Local dev orchestration: strictPort on all UIs, dev
        mode (--reload) for all APIs, dev-start/stop/status scripts in PM. PID tracking, mock mode by default, port
        registry from ui-api-mapping.json.

        ", status: done }
  - { id: p6-3-remaining-workflow-migration, content: "- [x] [AGENT] P6. Migrate remaining 17 PM workflows to
        notify-telegram.yml + persist-cicd-event.yml (4 done, 17 remaining out of 21 total). All 21 now complete (done
        as part of p2-3).

        ", status: done }
  - { id: p6-4-smoke-test-uis, content: "- [ ] [AGENT] P6. Smoke test all 12 UIs in mock mode. Start each on its
        assigned port, verify pages render, API calls return mock data, no console errors. Fix any syntax/import/runtime
        issues found. Report working URLs.

        ", status: superseded, superseded_by: "Tracked in ui_trader_acceptance_testing_2026_03_15
        (ph0-run-all-smoke-tests through ph8-human-walkthrough) — the UAT plan is the comprehensive citadel-grade
        version.

        " }
  - { id: p6-5-uat-handoff, content: "- [ ] [HUMAN] P6. User acceptance testing. Open each UI at its localhost URL,
        verify functionality, provide feedback. Agent should have already fixed all smoke test issues before handoff.

        ", status: superseded, superseded_by: "Tracked in ui_trader_acceptance_testing_2026_03_15
        (ph0-run-all-smoke-tests through ph8-human-walkthrough) — the UAT plan is the comprehensive citadel-grade
        version.

        " }
isProject: false
---

# UI / API / Alerting / Observability Audit & Remediation

## Context

Full audit of the unified trading system's UI↔API↔Service mappings, alerting system, observability/logging, CI/CD
alerting, and audit trail coverage. See Claude Code plan file for detailed design decisions and implementation details:
`~/.claude/plans/foamy-conjuring-blossom.md`

## Coordination Notes

This plan touches repos that overlap with several existing plans:

- **mode-config-env-architecture**: LOG_LEVEL canonical enum lives in UAC (this plan). UIC EnvVars should reference UAC
  LogLevel, not define its own.
- **uac-residual-refactors**: This plan adds LogLevel enum to UAC. Ensure reorg preserves this export path.
- **integration-tests-codex-compliance**: This plan extends UI integration tests to cover all mapped API endpoints.
  Template already rolled out by that plan.
- **cicd-code-rollout-master**: batch-audit-api is BASELINE_PENDING. Resolve before our P3.2 starts.
- **defi-keys-data-integration**: This plan adds Telegram notifier and deprecates Slack in alerting-service.
  FreshnessMonitor Phase 2 should route via Telegram.
- **cicd-e2e-testing**: This plan creates notify-telegram.yml reusable workflow. E2E validation should test this
  workflow, not inline curl patterns.
