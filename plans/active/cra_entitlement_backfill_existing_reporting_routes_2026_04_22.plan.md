---
name: client-reporting-api — backfill entitlement enforcement on existing reporting routes
overview:
  The new allocator routes (`allocators.py`) enforce `_enforce_entitlement(auth, client_id)` — external callers must
  match their AuthContext.org_id, internal callers bypass. The existing reporting routes (`settlements.py`, `trades.py`,
  `reporting/*`) trust the `client_id` query param blindly. Backfill the check across the old surface so external
  clients cannot read each other's data.
type: code
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-22

completion_gates:
  code: C5
  deployment: D3

repo_gates:
  - repo: client-reporting-api
    code: C0
    deployment: none
  - repo: unified-trading-pm
    code: C0
    deployment: none

depends_on:
  - fund_administration_service_and_pooled_subscription_redemption_2026_04_20.plan.md
---

# Context

Phase 4 of the fund-administration plan shipped `allocators.py` with entitlement enforcement:

```python
def _enforce_entitlement(auth: AuthContext, client_id: str) -> None:
    if not auth.is_internal and auth.org_id != client_id:
        raise HTTPException(status_code=403, detail="entitlement denied")
```

The Phase 4 sub-agent flagged that the existing reporting routes (`settlements.py`, `trades.py`, `clients.py`,
`reporting/*`) do NOT enforce this — they accept the `client_id` query parameter and return data for whatever client_id
is passed, as long as the caller has a valid API key. This is a cross-tenant data-leak risk.

# Scope

## Pre-audit required first

- [ ] Enumerate every route in `client-reporting-api/client_reporting_api/api/routes/` that takes a `client_id` query or
      path parameter. Expected targets: `settlements.py`, `trades.py`, `clients.py`, every file under `reporting/`.
      Capture the list into a pre-audit manifest.
- [ ] For each route, categorise: (a) should enforce entitlement, (b) is internal-only and should require
      `auth.is_internal`, (c) is public / no entitlement (rare — justify).

## Execution

- [ ] Extract `_enforce_entitlement` helper from `allocators.py` into a shared helper in
      `client_reporting_api/core/entitlement.py` (or equivalent). Same semantics.
- [ ] Apply to every (a) route. Tests confirm cross-tenant read returns 403.
- [ ] Apply `require_internal(auth)` helper to every (b) route. Tests confirm external callers get 403.
- [ ] Update `codex/08-workflows/` or the relevant auth / entitlement doc with the refreshed surface rule.
- [ ] QG pass on client-reporting-api.

## Acceptance

- Red-team: an external client's API key calling any `client-reporting-api` route with someone else's `client_id`
  returns 403 / 404. Confirmed via integration test in staging.
- Audit log: every 403 rejection emits a `REPORTING_ENTITLEMENT_DENIED` event with caller + requested client_id.

## Out of scope

- Rewriting the existing routes — pure additive entitlement gate.
- UI changes — the UI already passes the caller's own client_id, so no UI impact.
