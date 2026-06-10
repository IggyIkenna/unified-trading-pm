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

## Canonical-form coverage CF-20 — deployment-api/UI renders the v9 manifest (added 2026-06-10)

> Concrete re-runnable steady-state check for the migration-verification CF-20 added by
> `migration_verification_orphan_safety_2026_06_10.md` (V7). deployment-api + deployment-ui own the proof that
> data-status renders coverage from a CLEAN read of the canonical (or projected) v9 `_index` — no re-derived
> genesis/launch denominator. SSOT: `canonical_form_cross_service_audit_checklist.md` CF-20.

- [ ] (CF-20) **data-status / deployment-UI render the v9 manifest correctly** — point data-status at the canonical (or
      the projected `--beta-manifest-out`) v9 `_index`; run
      `bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --api` (with `DEPLOYMENT_ENV_SHORT=dev` for a
      projected `_index`) and assert that coverage %, the 4-state breakdown
      (`captured`/`empty_confirmed`/`attempted_failed`/`expected_unattempted`), the could-exist denominator, and the
      `pipeline_mode` / `source` drilldowns ALL render from a clean read of the `_index`. Assert the denominator COUNTS
      the materialised `expected_unattempted` 4-state
      (`% = captured / (captured + empty + failed + expected_unattempted)`) — it does NOT re-derive genesis/launch per
      consumer. Composes with the G3 UNION view. Green: coverage %, 4-state, could-exist denominator, and drilldowns
      match the manifest with no re-derived genesis/launch; the projected dev `_index` is deleted after the eyeball.

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
