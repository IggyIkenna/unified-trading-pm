---
name: plan-g-auth-entitlement
overview: |
  Backend-only: server-side auth & entitlement hardening. Document service access matrix, enroll all 21 services in
  S2S auth (extend Phase 0 static token), standardize API auth middleware across 9 API repos, enforce subscription
  entitlements server-side (not just UI). Goal: no unauthenticated S2S calls in production, no UI-only entitlement
  gates, org-level data filtering at API layer.
type: mixed
epic: epic-code-completion
status: active
locked_by: null
locked_since: null

completion_gates:
  code: C5
  deployment: D3
  business: none

repo_gates:
  - repo: unified-config-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-cloud-interface
    code: C0
    deployment: none
    business: none
  - repo: data-api
    code: C0
    deployment: none
    business: none
  - repo: execution-api
    code: C0
    deployment: none
    business: none
  - repo: execution-results-api
    code: C0
    deployment: none
    business: none
  - repo: ml-inference-api
    code: C0
    deployment: none
    business: none
  - repo: ml-training-api
    code: C0
    deployment: none
    business: none
  - repo: config-api
    code: C0
    deployment: none
    business: none
  - repo: trading-analytics-api
    code: C0
    deployment: none
    business: none
  - repo: deployment-api
    code: C0
    deployment: none
    business: none
  - repo: batch-audit-api
    code: C0
    deployment: none
    business: none
  - repo: execution-service
    code: C0
    deployment: none
    business: none
  - repo: alerting-service
    code: C0
    deployment: none
    business: none

depends_on: []

# NOTE: AUTH_FAILURE events (full_system_audit P0-04) and S2S auth events (full_system_audit P0-05) are already done.
# These were completed in the 2026-03-11 full audit remediation (execution-service + alerting-service).
# Plan G Phase 1 S2S enrollment should build on that existing work, not redo it.

todos:
  # ── Phase 0: Service Access Matrix ── PARALLEL ─────────────────────────────
  - id: p0-define-service-categories
    content: |
      - [ ] [AGENT] P0. Define the 8 service categories (2 internal: auth, devops; 6 external: data, execution, ML, strategy, reporting, config). Map all 21 services into categories. Document internal vs external access rules per service (internal = S2S only, external = S2S + user-facing API).
    status: todo
    note: ""
  - id: p0-document-subscription-slicing
    content: |
      - [ ] [AGENT] P0. Document subscription slicing within external services. Map the 7 existing subscription tiers to which API endpoints each tier can access. Define instrument count limits per tier (data-basic=180, data-pro=2400, etc.). Output: table of tier -> endpoints -> limits.
    status: todo
    note: ""
  - id: p0-create-access-matrix-yaml
    content: |
      - [ ] [AGENT] P0. Create service-access-matrix.yaml in unified-config-interface/unified_config_interface/auth/. Schema: service name, category, allowed callers (S2S service list or "user-facing"), required auth method (static-token, OAuth, API-key), subscription gating (true/false + tier mapping). This becomes the SSOT for all auth decisions.
    status: todo
    note: ""

  # ── Phase 1: S2S Auth Enrollment ── SEQUENTIAL after Phase 0 ──────────────
  - id: p1-audit-s2s-enrollment
    content: |
      - [ ] [AGENT] P0. Audit current S2S auth enrollment. Identify which 2 services currently validate S2S static tokens and which 19 do not. For each unenrolled service: identify the entrypoint (main.py / app.py), the middleware stack, and where token validation should be injected. Output: manifest of 21 services with enrollment status and injection point.
    status: todo
    note: ""
  - id: p1-enroll-remaining-services
    content: |
      - [ ] [AGENT] P0. Enroll remaining 19 services in S2S static token auth. Use the same middleware pattern as the 2 currently enrolled services. Token sourced from Secret Manager via UnifiedCloudConfig (not env vars). In mock mode (CLOUD_MOCK_MODE=true), accept any token or skip validation. All services must reject unauthenticated S2S calls when CLOUD_MOCK_MODE=false.
    status: todo
    note: "blocked_by p1-audit-s2s-enrollment within phase"
  - id: p1-token-rotation
    content: |
      - [ ] [AGENT] P1. Add token rotation automation. Create rotation script in unified-trading-pm/scripts/security/ that generates new S2S token, stores in Secret Manager, and triggers rolling restart of all services. Document rotation runbook in unified-trading-codex/07-security/. Rotation frequency: every 90 days, with 24h overlap window (old + new token both valid).
    status: todo
    note: ""
  - id: p1-qg-s2s-check
    content: |
      - [ ] [AGENT] P1. Add QG check: scan all service entrypoints for S2S auth middleware. Any service without token validation middleware in its request pipeline fails quality-gates.sh. Exclude: services that only run as batch jobs (no HTTP server).
    status: todo
    note: ""

  # ── Phase 2: API Auth Standardization ── SEQUENTIAL after Phase 1 ─────────
  - id: p2-audit-api-auth-patterns
    content: |
      - [ ] [AGENT] P0. Audit auth middleware patterns across all 9 API repos. Document: which use X-API-Key, which use Bearer token, which have no auth, which have DISABLE_AUTH support. Identify the canonical pattern (deployment-api) and document divergences. Output: manifest per API repo.
    status: todo
    note: ""
  - id: p2-standardize-api-middleware
    content: |
      - [ ] [AGENT] P0. Standardize auth middleware across all 9 API repos to match deployment-api pattern. Each API must: validate Bearer token (OAuth/OIDC) for user requests, validate S2S static token for service requests, support DISABLE_AUTH=true for local dev/testing, extract org_id from token claims. Create shared auth middleware in unified-cloud-interface that all APIs import.
    status: todo
    note: "blocked_by p2-audit-api-auth-patterns within phase"
  - id: p2-org-level-filtering
    content: |
      - [ ] [AGENT] P0. Add org-level filtering to API responses. Internal callers (S2S with admin token) see all data. External callers (user Bearer token) see only their org's data. Inject org_id filter into all database queries / data retrieval paths. Use org_id extracted from token claims by the standardized middleware.
    status: todo
    note: "blocked_by p2-standardize-api-middleware within phase"
  - id: p2-api-auth-tests
    content: |
      - [ ] [AGENT] P1. Add auth integration tests for all 9 API repos. Test: unauthenticated request returns 401, invalid token returns 403, valid user token returns org-filtered data, valid admin token returns all data, DISABLE_AUTH=true bypasses all checks. Use mock tokens (no real OAuth provider needed in tests).
    status: todo
    note: ""

  # ── Phase 3: Backend Entitlement Enforcement ── SEQUENTIAL after Phase 2 ──
  - id: p3-create-entitlement-registry
    content: |
      - [ ] [AGENT] P0. Create entitlement registry in unified-config-interface/unified_config_interface/auth/entitlements.py. Define the 7 subscription tiers as an enum. Map each tier to: allowed endpoints (list of URL patterns), instrument count limit, feature flags (e.g., DeFi access, ML predictions, real-time data). Load from entitlements.yaml config file. Export from UCfgI public surface.
      Absorbed from backend_frontend_alignment: subscription/entitlement management API — org->subscription tier mapping, per-org entitlement list, subscription upgrade/downgrade API, usage tracking (API calls, data queries, compute hours). Database: org_subscriptions table (org_id, tier, entitlements[], start_date, renewal_date). Auth: entitlements included in JWT token.
    status: todo
    note: ""
  - id: p3-api-entitlement-middleware
    content: |
      - [ ] [AGENT] P0. Add entitlement checking middleware to all user-facing APIs. After auth middleware extracts org_id and subscription tier from token claims, entitlement middleware checks: is this endpoint allowed for this tier? Has this org exceeded its instrument count limit? Reject with 403 + structured error body if entitlement check fails.
    status: todo
    note: "blocked_by p3-create-entitlement-registry within phase"
  - id: p3-instrument-count-enforcement
    content: |
      - [ ] [AGENT] P0. Enforce instrument count limits at API level. data-basic=180 instruments, data-pro=2400 instruments. When a user queries instruments or market data, count distinct instruments in response. If over limit, truncate response and include X-Instrument-Limit and X-Instrument-Count headers. Log entitlement violations for audit trail.
    status: todo
    note: "blocked_by p3-api-entitlement-middleware within phase"
  - id: p3-entitlement-tests
    content: |
      - [ ] [AGENT] P1. Add entitlement enforcement tests. Test: basic tier user cannot access ML endpoints, basic tier user gets truncated instrument list at 180, pro tier user gets full list up to 2400, admin bypasses all limits. Verify 403 error body includes tier name and upgrade path.
    status: todo
    note: ""

  # ── Phase 4: Final Validation ── SEQUENTIAL after all phases ──────────────
  - id: p4-qg-sweep
    content: |
      - [ ] [SCRIPT] P0. Run quality-gates.sh on all affected repos: unified-config-interface, unified-cloud-interface, all 9 API repos, execution-service, alerting-service. All must pass.
    status: todo
    note: ""
  - id: p4-auth-penetration-test
    content: |
      - [ ] [AGENT] P0. Create auth penetration test suite in system-integration-tests. Tests: token replay attack (expired token rejected), privilege escalation (basic tier token cannot access pro endpoints), org boundary violation (org A token cannot access org B data), S2S token used as user token (rejected), missing auth header (401 not 500).
    status: todo
    note: ""
  - id: p4-access-matrix-parity
    content: |
      - [ ] [AGENT] P0. Verify service-access-matrix.yaml parity with running system. Script reads the YAML, then for each service: verifies auth middleware is present, verifies correct auth method is configured, verifies entitlement checking matches declared tier mapping. Fails if any divergence found.
    status: todo
    note: ""
isProject: false
---

# Notes & Context

## Execution DAG

```
Phase 0 (Service Access Matrix) [PARALLEL within phase]
    |
    v
Phase 1 (S2S Auth Enrollment) [SEQUENTIAL]
    |
    v
Phase 2 (API Auth Standardization) [SEQUENTIAL]
    |
    v
Phase 3 (Backend Entitlement Enforcement) [SEQUENTIAL]
    |
    v
Phase 4 (Final Validation)
```

## Phase Gate Criteria

- **Phase 0 exit:** service-access-matrix.yaml created, all 21 services categorized, subscription slicing documented
- **Phase 1 exit:** all 21 services validate S2S tokens, rotation script exists, QG check enforces enrollment
- **Phase 2 exit:** all 9 API repos use standardized auth middleware, org-level filtering works, auth tests pass
- **Phase 3 exit:** entitlement registry created, API middleware enforces tier limits, instrument count caps work
- **Phase 4 exit:** all QG pass, penetration tests pass, access matrix parity verified

## Pre-Audit Manifest

### Current Auth State

| Component                   | Location                   | Status                       |
| --------------------------- | -------------------------- | ---------------------------- |
| S2S static token validation | deployment-api, config-api | Only 2/21 enrolled           |
| X-API-Key middleware        | Most API repos             | Present but no OAuth/OIDC    |
| DISABLE_AUTH env var        | All API repos              | Supported but inconsistently |
| Subscription tiers (7)      | UI localStorage only       | No server-side enforcement   |
| Org-level filtering         | None                       | Not implemented              |

### Downstream Consumers of Changes

| Change                        | Consumers                    | Impact                            |
| ----------------------------- | ---------------------------- | --------------------------------- |
| Shared auth middleware in UCI | All 9 API repos              | Must adopt new middleware         |
| Entitlement registry in UCfgI | All user-facing APIs         | Must add entitlement middleware   |
| S2S token validation          | All 21 services              | Must add middleware to entrypoint |
| service-access-matrix.yaml    | QG checks, penetration tests | New SSOT for auth decisions       |

## References

- deployment-api auth pattern (canonical): `deployment-api/deployment_api/middleware/auth.py`
- Current S2S token handling: `unified-cloud-interface/unified_cloud_interface/auth.py`
- Subscription tier definitions (UI-only): check existing UI repos for localStorage persona handling
- Security standards: `unified-trading-codex/07-security/`
