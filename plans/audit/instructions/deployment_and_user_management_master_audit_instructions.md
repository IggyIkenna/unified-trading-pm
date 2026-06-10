---
name: deployment_and_user_management_master_audit_instructions
type: audit-instructions
epic: deployment_and_user_management_master
assigned_vm: vm-operator-ops
tier: L3
last_updated: 2026-05-22
---

# Deployment + User Management Master — Audit Instructions

## Epic Scope

deployment-api, deployment-ui (consolidated UI), user-management-ui, GCS shard detail API, health endpoints,
`ServiceBootstrap` compliance, API key hot-reload. GCS-locked code is a technical debt tracked item (Phase B
post-cutover; ratchet baseline from 27 → 0 cloud-locked references).

## Triggers

- Weekly (minimum cadence)
- After any deployment-stack change (new endpoint, middleware, auth change)
- After any GCS shard detail code refactor
- When deployment-stack restart script (`restart-deployment-stack.sh`) fails

## Checklist

- [ ] (a) **ServiceBootstrap in every service — QG STEP 5.61**: `ServiceBootstrap(...)` present in deployment-api,
      deployment-ui backend, and user-management-ui backend source. Grep:
      `rg "ServiceBootstrap" deployment-service/ unified-trading-system-ui/ --include="*.py"`

- [ ] (b) **make_health_router from UTL — QG STEP 5.62**: `api/main.py` uses `make_health_router` with `data_freshness`
      callback in each service. Grep: `rg "make_health_router" deployment-service/ --include="*.py"`

- [ ] (c) **ApiKeyReloader hot-reload**: API key loading uses `ApiKeyReloader` from UTL (not one-shot
      `validate_api_keys_for_venues()`). Grep: `rg "ApiKeyReloader" --include="*.py"` vs
      `rg "validate_api_keys_for_venues" --include="*.py"` — latter should not be in main service code

- [ ] (d) **Deployment stack starts cleanly**: `restart-deployment-stack.sh --api` exits 0. Run:
      `bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --api` — verify ports 8004/5183 healthy

- [ ] (e) **GCS cloud-locked references ratcheting**: count of cloud-locked GCS path references in deployment-api has
      not increased from the last audit baseline. Grep: `rg "gs://" deployment-service/ --include="*.py"` — count hits;
      compare to prior baseline (27 at 2026-05-17)

- [ ] (f) **Health endpoint returns data_freshness**: deployment-api `/health` endpoint includes `data_freshness` field
      in response. Test: `curl http://localhost:8004/health` after stack start

### E2E Flow Verification

- (e2e-promote) **Promote flow audit**: run a paper-to-live promote end-to-end (paper_1d → live_early) using a test
  strategy. Confirm ManualTradeGateDialog fires. If promote can't run against prod, verify the code path with a dry-run
  or staging environment.
- (mock-upstream) **Staging-only audit**: deployment and promote workflows MUST be auditable on staging without
  affecting prod. Document the staging invocation.

## Success Criteria

- All 6 checklist items GREEN
- Deployment stack ports 8004/5183 healthy after restart
- GCS cloud-locked reference count ≤ prior baseline (ratcheting toward 0)
- deployment-api QG exits 0

## Output Format

Result file at `plans/audit/results/deployment_and_user_management_master_audit_YYYY_MM_DD.md`. Same structure as per
`../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
