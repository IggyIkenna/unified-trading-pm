---
doc_type: plan
title: plan-g-auth-entitlement
summary: 'Backend-only: server-side auth & entitlement hardening. Document service access matrix, enroll all 21 services
  in

  S2S auth (extend Phase 0 static token), standardize API auth middleware across 9 API repos, enforce subscription

  entitlements server-side (not just UI). Goal: no unauthenticated S2S calls in production, no UI-only entitlement

  gates, org-level data filtering at API layer.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-21'
type: mixed
epic: epic-code-completion
locked_by:
locked_since:
completion_gates: {code: C5, deployment: D3, business: none}
repo_gates:
- {repo: unified-config-interface, code: C0, deployment: none, business: none}
- {repo: unified-cloud-interface, code: C0, deployment: none, business: none}
- {repo: data-api, code: C0, deployment: none, business: none}
- {repo: execution-api, code: C0, deployment: none, business: none}
- {repo: execution-results-api, code: C0, deployment: none, business: none}
- {repo: ml-inference-api, code: C0, deployment: none, business: none}
- {repo: ml-training-api, code: C0, deployment: none, business: none}
- {repo: config-api, code: C0, deployment: none, business: none}
- {repo: trading-analytics-api, code: C0, deployment: none, business: none}
- {repo: deployment-api, code: C0, deployment: none, business: none}
- {repo: batch-audit-api, code: C0, deployment: none, business: none}
- {repo: execution-service, code: C0, deployment: none, business: none}
- {repo: alerting-service, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: p0-define-service-categories, content: '- [x] [AGENT] P0. Define the 8 service categories (2 internal: auth, devops; 6 external: data, execution, ML, strategy, reporting, config). Map all 21 services into categories. Document internal vs external access rules per service (internal = S2S only, external = S2S + user-facing API).

    ', status: done, note: Created UCfgI auth/ directory with service_access_matrix.yaml}
- {id: p0-document-subscription-slicing, content: '- [x] [AGENT] P0. Document subscription slicing within external services. Map the 7 existing subscription tiers to which API endpoints each tier can access. Define instrument count limits per tier (data-basic=180, data-pro=2400, etc.). Output: table of tier -> endpoints -> limits.

    ', status: done, note: 'Created entitlement_registry.yaml with 7 tiers: free(50), data-basic(180), data-pro(2400), ml-pro(2400), execution-basic(500), execution-pro(5000), enterprise(unlimited)'}
- {id: p0-create-access-matrix-yaml, content: '- [x] [AGENT] P0. Create service-access-matrix.yaml in unified-config-interface/unified_config_interface/auth/. Schema: service name, category, allowed callers (S2S service list or "user-facing"), required auth method (static-token, OAuth, API-key), subscription gating (true/false + tier mapping). This becomes the SSOT for all auth decisions.

    ', status: done, note: 'Created with 21 services + 9 APIs. Also created entitlements.py with SubscriptionTier enum, EntitlementRegistry, and ServiceAccessMatrix types.'}
- {id: p1-audit-s2s-enrollment, content: '- [x] [AGENT] P0. Audit current S2S auth enrollment. Identify which 2 services currently validate S2S static tokens and which 19 do not. For each unenrolled service: identify the entrypoint (main.py / app.py), the middleware stack, and where token validation should be injected. Output: manifest of 21 services with enrollment status and injection point.

    ', status: done, note: 'Audit complete: 4 services already enrolled (execution-service, risk-and-exposure-service, client-reporting-api, deployment-api). Created shared UCI middleware (s2s_auth.py).'}
- {id: p1-enroll-remaining-services, content: '- [ ] [AGENT] P0. AUDIT CORRECTION: Shared create_s2s_auth_dependency() was created in UCI s2s_auth.py, and auth_s2s.py files were created in 19 services. HOWEVER, 19/21 services do NOT actually apply verify_service_token to their routes — the middleware file exists but is not wired into the FastAPI/Flask app route registrations. Must: (a) verify each service''s main.py/app.py imports and applies the S2S auth dependency to all routes, (b) add integration test that unauthenticated S2S call returns 401. Previously marked done incorrectly — files exist but are not activated.

    ', status: todo, note: 'AUDIT: auth_s2s.py files exist in 19 services but verify_service_token is NOT applied to routes in 19/21 services.'}
- {id: p1-token-rotation, content: '- [x] [AGENT] P1. Add token rotation automation. Create rotation script in unified-trading-pm/scripts/security/ that generates new S2S token, stores in Secret Manager, and triggers rolling restart of all services. Document rotation runbook in unified-trading-codex/07-security/. Rotation frequency: every 90 days, with 24h overlap window (old + new token both valid).

    ', status: done, note: 'Created rotate-s2s-token.sh with --dry-run support. 90-day rotation, 24h overlap via Secret Manager versioning.'}
- {id: p1-qg-s2s-check, content: '- [ ] [AGENT] P1. Add QG check: scan all service entrypoints for S2S auth middleware. Any service without token validation middleware in its request pipeline fails quality-gates.sh. Exclude: services that only run as batch jobs (no HTTP server).

    ', status: todo, note: ''}
- {id: p2-audit-api-auth-patterns, content: '- [x] [AGENT] P0. Audit auth middleware patterns across all 9 API repos. Document: which use X-API-Key, which use Bearer token, which have no auth, which have DISABLE_AUTH support. Identify the canonical pattern (deployment-api) and document divergences. Output: manifest per API repo.

    ', status: done, note: Audit complete via background agent. All 9 APIs documented.}
- {id: p2-standardize-api-middleware, content: '- [x] [AGENT] P0. Standardize auth middleware across all 9 API repos to match deployment-api pattern. Each API must: validate Bearer token (OAuth/OIDC) for user requests, validate S2S static token for service requests, support DISABLE_AUTH=true for local dev/testing, extract org_id from token claims. Create shared auth middleware in unified-cloud-interface that all APIs import.

    ', status: done, note: Created shared create_api_auth() in UCI api_auth.py with AuthContext model. All 9 API repos have auth_standardized.py importing from UCI.}
- {id: p2-org-level-filtering, content: '- [ ] [AGENT] P0. Add org-level filtering to API responses. Internal callers (S2S with admin token) see all data. External callers (user Bearer token) see only their org''s data. Inject org_id filter into all database queries / data retrieval paths. Use org_id extracted from token claims by the standardized middleware.

    ', status: todo, note: blocked_by p2-standardize-api-middleware within phase}
- {id: p2-api-auth-tests, content: '- [ ] [AGENT] P1. Add auth integration tests for all 9 API repos. Test: unauthenticated request returns 401, invalid token returns 403, valid user token returns org-filtered data, valid admin token returns all data, DISABLE_AUTH=true bypasses all checks. Use mock tokens (no real OAuth provider needed in tests).

    ', status: todo, note: ''}
- {id: p3-create-entitlement-registry, content: '- [x] [AGENT] P0. Create entitlement registry in unified-config-interface/unified_config_interface/auth/entitlements.py. Define the 7 subscription tiers as an enum. Map each tier to: allowed endpoints (list of URL patterns), instrument count limit, feature flags (e.g., DeFi access, ML predictions, real-time data). Load from entitlements.yaml config file. Export from UCfgI public surface.

    Absorbed from backend_frontend_alignment: subscription/entitlement management API — org->subscription tier mapping, per-org entitlement list, subscription upgrade/downgrade API, usage tracking (API calls, data queries, compute hours). Database: org_subscriptions table (org_id, tier, entitlements[], start_date, renewal_date). Auth: entitlements included in JWT token.

    ', status: done, note: 'SubscriptionTier (7 tiers), EndpointEntitlement, EntitlementRegistry, FeatureFlags — all in UCfgI auth/entitlements.py with YAML-backed config. 20 tests pass.'}
- {id: p3-api-entitlement-middleware, content: '- [x] [AGENT] P0. Add entitlement checking middleware to all user-facing APIs. After auth middleware extracts org_id and subscription tier from token claims, entitlement middleware checks: is this endpoint allowed for this tier? Has this org exceeded its instrument count limit? Reject with 403 + structured error body if entitlement check fails.

    ', status: done, note: 'Created create_entitlement_check() in UCI entitlement_middleware.py. Returns 403 with structured error body including tier name, endpoint, and upgrade path.'}
- {id: p3-instrument-count-enforcement, content: '- [x] [AGENT] P0. Enforce instrument count limits at API level. data-basic=180 instruments, data-pro=2400 instruments. When a user queries instruments or market data, count distinct instruments in response. If over limit, truncate response and include X-Instrument-Limit and X-Instrument-Count headers. Log entitlement violations for audit trail.

    ', status: done, note: 'Created enforce_instrument_limit() in UCI entitlement_middleware.py. Truncates response and sets X-Instrument-Limit, X-Instrument-Count, X-Instrument-Truncated headers.'}
- {id: p3-entitlement-tests, content: '- [ ] [AGENT] P1. Add entitlement enforcement tests. Test: basic tier user cannot access ML endpoints, basic tier user gets truncated instrument list at 180, pro tier user gets full list up to 2400, admin bypasses all limits. Verify 403 error body includes tier name and upgrade path.

    ', status: todo, note: ''}
- {id: p4-qg-sweep, content: '- [ ] [SCRIPT] P0. Run quality-gates.sh on all affected repos: unified-config-interface, unified-cloud-interface, all 9 API repos, execution-service, alerting-service. All must pass.

    ', status: todo, note: ''}
- {id: p4-auth-penetration-test, content: '- [ ] [AGENT] P0. Create auth penetration test suite in system-integration-tests. Tests: token replay attack (expired token rejected), privilege escalation (basic tier token cannot access pro endpoints), org boundary violation (org A token cannot access org B data), S2S token used as user token (rejected), missing auth header (401 not 500).

    ', status: todo, note: ''}
- {id: p4-access-matrix-parity, content: '- [ ] [AGENT] P0. Verify service-access-matrix.yaml parity with running system. Script reads the YAML, then for each service: verifies auth middleware is present, verifies correct auth method is configured, verifies entitlement checking matches declared tier mapping. Fails if any divergence found.

    ', status: todo, note: ''}
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

| Component                   | Location                   | Status                                                      |
| --------------------------- | -------------------------- | ----------------------------------------------------------- |
| S2S static token validation | deployment-api, config-api | Only 2/21 enrolled (AUDIT: 19 have files but not activated) |
| X-API-Key middleware        | Most API repos             | Present but no OAuth/OIDC                                   |
| DISABLE_AUTH env var        | All API repos              | Supported but inconsistently                                |
| Subscription tiers (7)      | UI localStorage only       | No server-side enforcement                                  |
| Org-level filtering         | None                       | Not implemented                                             |
| auth-api                    | auth-api repo              | P2 DEV: No OAuth impl, no production guard, no RBAC         |

### Citadel Audit Findings (2026-03-21)

- **S2S auth: 19/21 NOT applying to routes.** auth_s2s.py files were created in 19 services by a prior agent session,
  but verify_service_token is NOT applied to actual route registrations. The middleware exists as dead code.
  p1-enroll-remaining-services has been reset to NOT DONE.
- **auth-api is P2 DEV status.** No OAuth implementation. No production guard (being fixed separately). No RBAC
  enforcement. Plan G Phase 2 must account for this — API auth standardization depends on auth-api being functional for
  token issuance/validation.

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
