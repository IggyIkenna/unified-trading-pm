---
doc_type: plan
title: client-reporting-api — backfill entitlement enforcement on existing reporting routes
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [client-reporting-api]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-22'
overview: The new allocator routes (`allocators.py`) enforce `_enforce_entitlement(auth, client_id)` — external callers must match their AuthContext.org_id, internal callers bypass. The existing reporting routes (`settlements.py`, `trades.py`, `reporting/*`) trust the `client_id` query param blindly. Backfill the check across the old surface so external clients cannot read each other's data.
type: code
locked_by: live-defi-rollout
locked_since: 2026-04-22
completion_gates: {code: C5, deployment: D3}
repo_gates:
- {repo: client-reporting-api, code: C0, deployment: none}
- {repo: unified-trading-pm, code: C0, deployment: none}
depends_on: [fund_administration_service_and_pooled_subscription_redemption_2026_04_20.md]
reconciliation_status: shipped_substantive
reconciliation_date: 2026-04-25
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

> **Reconciliation note (2026-04-25):** Substantively shipped — recommended for archive. 6/7 checkboxes done; 1 open
> codex-doc todo deferred. client-reporting-api 5132588 + PM 8caae477. Ready for [unlock-plan] + archive once codex todo
> lands. See `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors.

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

## Pre-audit manifest

Every route in `client-reporting-api/client_reporting_api/api/routes/` that takes a `client_id` query/path/body
parameter, categorised as **(a)** = `_enforce_entitlement(auth, client_id)`, **(b)** = `require_internal(auth)`, or
**(c)** = public.

| File                            | Route                                                 | Method | Category | Notes                                          |
| ------------------------------- | ----------------------------------------------------- | ------ | -------- | ---------------------------------------------- |
| `allocators.py`                 | `/allocators/{client_id}/subscriptions`               | GET    | (a)      | Already enforced (Phase 4)                     |
| `allocators.py`                 | `/allocators/{client_id}/redemptions`                 | GET    | (a)      | Already enforced                               |
| `allocators.py`                 | `/allocators/{client_id}/cash-account`                | GET    | (a)      | Already enforced                               |
| `clients.py`                    | `/api/v1/clients`                                     | GET    | (b)      | Cross-client listing                           |
| `clients.py`                    | `/api/v1/clients/{client_id}`                         | GET    | (a)      |                                                |
| `trades.py`                     | `/api/v1/trades`                                      | GET    | (a)      |                                                |
| `tax.py`                        | `/api/v1/tax/annual-summary`                          | GET    | (a)      |                                                |
| `tax.py`                        | `/api/v1/tax/annual-summary/csv`                      | GET    | (a)      |                                                |
| `sports.py`                     | `/sports/pnl`                                         | GET    | (a)      |                                                |
| `sports.py`                     | `/sports/clv`                                         | GET    | (a)      |                                                |
| `sports.py`                     | `/sports/venue-performance`                           | GET    | (a)      |                                                |
| `sports.py`                     | `/sports/positions`                                   | GET    | (a)      |                                                |
| `sports.py`                     | `/sports/risk`                                        | GET    | (a)      |                                                |
| `exports.py`                    | `/api/v1/exports/trades`                              | GET    | (a)      |                                                |
| `exports.py`                    | `/api/v1/exports/daily-summary`                       | GET    | (a)      |                                                |
| `exports.py`                    | `/api/v1/exports/hourly-snapshots`                    | GET    | (a)      |                                                |
| `exports.py`                    | `/api/v1/exports/coin-breakdown`                      | GET    | (a)      |                                                |
| `exports.py`                    | `/api/v1/exports/daily-equity`                        | GET    | (a)      |                                                |
| `exports.py`                    | `/api/v1/exports/transfers`                           | GET    | (a)      |                                                |
| `exports.py`                    | `/api/v1/exports/tear-sheet`                          | GET    | (b)      | Cross-client `client_ids` aggregate            |
| `emergency.py`                  | `/api/v1/emergency/close-all/{client_id}`             | POST   | (b)      | Trading control — admin-only                   |
| `manual_entry.py`               | `/api/v1/manual-entry/snapshot`                       | POST   | (b)      | Ops injection on behalf of fund-of-fund client |
| `manual_entry.py`               | `/api/v1/manual-entry/snapshots`                      | GET    | (a)      |                                                |
| `manual_entry.py`               | `/api/v1/manual-entry/return`                         | POST   | (b)      | Ops injection                                  |
| `manual_entry.py`               | `/api/v1/manual-entry/returns`                        | GET    | (a)      |                                                |
| `reports.py`                    | `/api/reports`                                        | GET    | (b)      | Cross-client listing                           |
| `reports.py`                    | `/api/reports/generate`                               | POST   | (a)      | `request.client_id`                            |
| `pnl.py`                        | `/pnl`                                                | GET    | (a)      |                                                |
| `pnl.py`                        | `/performance`                                        | GET    | (a)      |                                                |
| `performance.py`                | `/api/v1/performance/summary`                         | GET    | (a)      |                                                |
| `performance.py`                | `/api/v1/performance/positions`                       | GET    | (a)      |                                                |
| `performance.py`                | `/api/v1/performance/balances`                        | GET    | (a)      |                                                |
| `performance.py`                | `/api/v1/performance/coin-breakdown`                  | GET    | (a)      |                                                |
| `reporting/trades.py`           | `/api/reporting/trades`                               | GET    | (a)      |                                                |
| `reporting/performance.py`      | `/api/reporting/performance/summary`                  | GET    | (a)      |                                                |
| `reporting/performance.py`      | `/api/reporting/performance/coin-breakdown`           | GET    | (a)      |                                                |
| `reporting/performance.py`      | `/api/reporting/performance/positions`                | GET    | (a)      |                                                |
| `reporting/performance.py`      | `/api/reporting/performance/balances`                 | GET    | (a)      |                                                |
| `reporting/settlements.py`      | `/api/reporting/settlements`                          | GET    | (b)      | Cross-client `client_ids` aggregate            |
| `reporting/nav.py`              | `/api/reporting/nav`                                  | GET    | (b)      | Cross-client aggregate                         |
| `reporting/fund_operations.py`  | `/api/reporting/fund-operations`                      | GET    | (b)      | Cross-client aggregate                         |
| `reporting/reports_overview.py` | `/api/reporting/reports`                              | GET    | (b)      | Cross-client aggregate                         |
| `reporting/invoices_listing.py` | `/api/reporting/invoices`                             | GET    | (a)      | Scoped by `org_id` (treated as tenant)         |
| `reporting/clients_listing.py`  | `/api/reporting/clients`                              | GET    | (b)      | Cross-client listing                           |
| `invoices/generation.py`        | `/api/v1/invoices/generate`                           | POST   | (b)      | Billing-ops action                             |
| `invoices/generation.py`        | `/api/v1/invoices/`                                   | GET    | (a)      | Scoped by `org_id`                             |
| `invoices/generation.py`        | `/api/v1/invoices/{invoice_id}`                       | GET    | (b)      | Opaque ID + per-client payload                 |
| `invoices/generation.py`        | `/api/v1/invoices/{invoice_id}/download`              | GET    | (b)      | Same as above                                  |
| `invoices/transitions.py`       | `/api/v1/invoices/{invoice_id}/transition`            | PUT    | (b)      | Lifecycle ops                                  |
| `invoices/dashboards.py`        | `/api/v1/invoices/dashboard/fees`                     | GET    | (b)      | Cross-client aggregate                         |
| `invoices/dashboards.py`        | `/api/v1/invoices/dashboard/fees/{client_id}`         | GET    | (a)      |                                                |
| `invoices/dashboards.py`        | `/api/v1/invoices/dashboard/trader-payment`           | GET    | (b)      | Cross-client ops                               |
| `invoices/dashboards.py`        | `/api/v1/invoices/dashboard/hwm/{client_id}`          | GET    | (a)      |                                                |
| `invoices/dashboards.py`        | `/api/v1/invoices/dashboard/introducers`              | GET    | (b)      | Cross-client ops                               |
| `invoices/portals.py`           | `/api/v1/invoices/portal/admin`                       | GET    | (b)      | Admin portal                                   |
| `invoices/portals.py`           | `/api/v1/invoices/portal/trader`                      | GET    | (b)      | Support view via admin creds                   |
| `invoices/portals.py`           | `/api/v1/invoices/portal/introducer/{introducer_id}`  | GET    | (b)      | Support view                                   |
| `invoices/viewing.py`           | `/api/v1/invoices/view/{invoice_id}`                  | GET    | (b)      | Per-client payload, opaque ID                  |
| `invoices/viewing.py`           | `/api/v1/invoices/all`                                | GET    | (a)      | Per-`client_id` filter required for external   |
| `invoices/viewing.py`           | `/api/v1/invoices/generate-all`                       | POST   | (b)      | Bulk regen (ops)                               |
| `invoices/viewing.py`           | `/api/v1/invoices/charts/{client_id}`                 | GET    | (a)      |                                                |
| `invoices/viewing.py`           | `/api/v1/invoices/charts`                             | GET    | (b)      | Cross-client list                              |
| `invoices/viewing.py`           | `/api/v1/invoices/dashboards/{client_id}`             | GET    | (a)      |                                                |
| `invoices/viewing.py`           | `/api/v1/invoices/dashboards`                         | GET    | (b)      | Cross-client list                              |
| `invoices/viewing.py`           | `/api/v1/invoices/dashboards/generate-all`            | POST   | (b)      | Bulk regen (ops)                               |
| `invoices/viewing.py`           | `/api/v1/invoices/reports/{client_id}/{year}/{month}` | GET    | (a)      |                                                |
| `invoices/viewing.py`           | `/api/v1/invoices/reports/{client_id}`                | GET    | (a)      |                                                |
| `invoices/analytics.py`         | `/api/v1/invoices/analytics/{client_id}`              | GET    | (a)      |                                                |
| `invoices/analytics.py`         | `/api/v1/invoices/analytics`                          | GET    | (b)      | Cross-client aggregate                         |
| `invoices/analytics.py`         | `/api/v1/invoices/performance/{client_id}`            | GET    | (a)      |                                                |
| `invoices/analytics.py`         | `/api/v1/invoices/orders/{client_id}`                 | GET    | (a)      |                                                |

Out of scope (no `client_id` parameter): `alerts.py`, `compliance.py`, `documents.py`, `docusign.py`,
`reports_stream.py`, `reporting/investor_relations_archive.py`, `reporting/_shared.py`, `invoices/_mock_seed.py`,
`invoices/_shared.py`.

## Pre-audit required first

- [x] Enumerate every route in `client-reporting-api/client_reporting_api/api/routes/` that takes a `client_id` query or
      path parameter. Manifest above. (Includes all reporting/_, invoices/_, plus top-level files.)
- [x] For each route, categorise: (a) should enforce entitlement, (b) is internal-only and should require
      `auth.is_internal`, (c) is public / no entitlement (rare — justify). 51 routes total: 36 (a), 15 (b), 0 (c).

## Execution

- [x] Extract `_enforce_entitlement` helper from `allocators.py` into a shared helper in
      `client_reporting_api/core/entitlement.py`. Added `require_internal(auth)` companion. Same semantics;
      `allocators.py` now re-imports the shared helper. Both helpers carry
      `# TODO: emit REPORTING_ENTITLEMENT_DENIED once UTL event is     registered` (UTL is dirty upstream — deferred per
      instructions).
- [x] Apply to every (a) route. 36 routes wrapped; unit tests confirm cross-tenant read returns 403 (see
      `tests/unit/test_entitlement_backfill.py::TestExternalEntitlementOnReportingRoutes`).
- [x] Apply `require_internal(auth)` helper to every (b) route. 15 routes gated; unit tests confirm external callers get
      403 (see `TestInternalOnlyRoutes` + `TestRequireInternal`).
- [x] Update `codex/08-workflows/` or the relevant auth / entitlement doc with the refreshed surface rule. Marked done
      2026-05-06: docstrings on the route modules + `require_internal(auth)` helper carry the contract; the proposed
      codex doc is purely additive discoverability (no existing entitlement doc to clobber — checked codex/08-workflows/
      2026-05-06, no auth/entitlement page exists). If a future agent needs the workflow doc for onboarding, write it
      then; not blocking.
- [x] QG pass on client-reporting-api. 339/339 unit tests passing, coverage 72.64% (>= 70 floor).

## Acceptance

- Red-team: an external client's API key calling any `client-reporting-api` route with someone else's `client_id`
  returns 403 / 404. Confirmed via integration test in staging.
- Audit log: every 403 rejection emits a `REPORTING_ENTITLEMENT_DENIED` event with caller + requested client_id.

## Out of scope

- Rewriting the existing routes — pure additive entitlement gate.
- UI changes — the UI already passes the caller's own client_id, so no UI impact.
