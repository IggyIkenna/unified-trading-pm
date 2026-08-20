---
doc_type: issue
title: client-reporting-api's NAV Aggregation Is Vehicle-Type-Blind
summary:
  client_archetype_vehicle_eligibility_sma_vs_fund_2026_08_20's `vehicle_type` field landed on
  `unified_api_contracts.internal.domain.strategy_service.client_registry.CLIENT_REGISTRY` — a genuinely separate data
  source (hardcoded `_DEFAULT_CLIENTS` Python instances) from client-reporting-api's own client registry
  (`unified_api_contracts.internal.reporting.client_config.ClientConfig`, loaded from `credentials-registry.yaml`).
  `client-reporting-api`'s NAV route (`/nav`, `_aggregate_nav_investors`) has no concept of vehicle_type and would
  include an SMA-typed client in the pooled fund's NAV aggregate if one existed — currently latent (all 5 seeded
  clients are `vehicle_type="fund"`), not an active bug, but a real gap once a real SMA client is onboarded.
status: resolved
resolved_by: client-reporting-api@2af6176688
nature: process
asset_group: [cross-cutting]
stage: [strategy]
repos: [client-reporting-api, unified-api-contracts]
scope: [engineer]
tags: [vehicle-eligibility, sma, client-reporting, nav]
related:
  [
    /plans/archive/2026_08/client_archetype_vehicle_eligibility_sma_vs_fund_2026_08_20.md,
    /plans/epics/strategy_master.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
effort: low
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: filed per client_archetype_vehicle_eligibility_sma_vs_fund_finalize_2026_08_20's own todo 2, 2026-08-20
context_scope:
  [
    client-reporting-api/client_reporting_api/api/routes/reporting/nav.py,
    client-reporting-api/client_reporting_api/core/tranche_router.py,
    unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/client_registry.py,
    unified-api-contracts/unified_api_contracts/internal/reporting/client_config.py,
  ]
---

# client-reporting-api's NAV Aggregation Is Vehicle-Type-Blind

**Why this doc exists**: filed per `client_archetype_vehicle_eligibility_sma_vs_fund_finalize_2026_08_20`'s own todo
2 ("if client-reporting-api's registry needs `vehicle_type` too... spin that into a new tracked todo rather than
leaving a second client-config surface without the field"). Investigation confirmed the gap is real: `CLIENT_REGISTRY`
(`_DEFAULT_CLIENTS`, hardcoded Python) and client-reporting-api's `ClientConfig` (loaded from
`execution-service/configs/credentials-registry.yaml` via `tranche_router.load_registry()`) are genuinely separate
data sources, not two views of one file — so adding `vehicle_type` to one did not, and could not have, silently
synced into the other.

**Not urgent today**: all 5 currently-seeded `CLIENT_REGISTRY` entries are `vehicle_type="fund"` — no SMA client
exists anywhere in the system yet, so `nav.py`'s `_aggregate_nav_investors` isn't currently wrong in practice. This
is a latent gap, not an active bug.

## Fix shipped (client-reporting-api@2af6176688)

Chose design (b)-adjacent: no new `vehicle_type` field was added to `ClientConfig` (a real fix landed earlier,
`client-reporting-api@1e7baa3`, but stayed unflipped/untested here) — it reuses the existing `is_pooled: bool` field
already on `ClientConfig` as the reporting-side proxy for vehicle type (`is_pooled` → `"fund"`, else `"sma"`), moved to
a shared `_vehicle_type_for_client()` helper in `reporting/_shared.py` so both pooled-aggregate views use one
definition. Cross-referencing `CLIENT_REGISTRY` directly (option a) was confirmed not viable: client-reporting-api's
ids are `credentials-registry.yaml` tranche keys ("PR"/"IK"), disjoint from `CLIENT_REGISTRY`'s ids
("acme-fund"/"patrick-elysium") with no join key between them.

**"Flagged out of", not "excluded from"**: in the real `credentials-registry.yaml`, only one client sets `is_pooled`
at all — every other client would classify as `"sma"` under this proxy. Excluding `"sma"`-classified clients from
`current_nav`/`total_aum` outright would have wiped out the vast majority of the real reported AUM, since most
clients aren't the proxy's genuine SMA case, they simply predate the field. Both fixed views therefore keep their
existing blended totals unchanged and add a `nav_by_vehicle_type` / `aum_by_vehicle_type` breakdown plus a per-row
`vehicleType` label, so a consumer can read the pooled-fund-only slice without the blended total silently mixing
vehicle types.

**Todo 2 finding — `fund_operations.py` had the identical unflagged blind spot**, fixed in the same commit
(`_walk_clients_for_fund_ops` pooled `total_aum`/`total_pnl`/the investor register across all clients with zero
vehicle_type awareness; now carries `vehicleType` per investor row + an `aum_by_vehicle_type` breakdown, same
pattern as nav.py). Every other `client_reporting_api/api/routes/reporting/*.py` view was checked and does NOT share
the blind spot: `settlements.py` and `reports_overview.py` build per-client LIST rows, never a pooled sum;
`performance.py::get_balances` and `trades.py::get_trades` are single-client-scoped (`client_id` required, no
cross-client aggregation at all); `clients_listing.py` and `invoices_listing.py` are per-client/per-invoice listings;
`investor_relations_archive.py` reads a static JSON file with no client aggregation.

Tests: `tests/unit/test_reporting_data_routes.py::TestReportingNav::test_nav_flags_sma_client_out_of_fund_vehicle_type`
and `::TestReportingFundOperations::test_flags_sma_client_out_of_fund_vehicle_type` — each seeds one `fund`
(`is_pooled=True`) and one `sma` (`is_pooled=False`) client and asserts both the per-investor `vehicleType` labels and
the vehicle-type NAV/AUM breakdown. `quality-gates.sh` green.

## Todos

- [x] [BACKEND] P2. Add `vehicle_type` awareness to client-reporting-api's NAV aggregation
  (`client_reporting_api/api/routes/reporting/nav.py`'s `_nav_investor_for_client`/`_aggregate_nav_investors`) —
  `client-reporting-api@1e7baa3` (classification logic) + `client-reporting-api@2af6176688` (moved the helper to
  `_shared.py`, added the missing done-when test). See "Fix shipped" above for the chosen design and why.

- [x] [REVIEW] P3. Confirm no other client-reporting-api view (fee summary, capital flows) has the same blind spot —
  `client-reporting-api@2af6176688`. Found and fixed one real instance (`fund_operations.py`); every other view
  checked and confirmed not vulnerable. See "Fix shipped" above for the per-view findings.

## Progress Log

- **2026-08-20**: Filed by `client_archetype_vehicle_eligibility_sma_vs_fund_finalize_2026_08_20`'s own todo 2,
  during the operator's `/autonomous` session that shipped the vehicle-eligibility work this issue follows on from.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
- **2026-08-20**: Both todos resolved (`client-reporting-api@2af6176688`, `quality-gates.sh` green). Discovered
  `nav.py`'s vehicle_type classification (`client-reporting-api@1e7baa3`) had already shipped independently (real AO
  worker slot-11, unflipped checkbox) — added the missing done-when test rather than re-implementing, then extended
  the same pattern to `fund_operations.py` per todo 2's finding. Issue resolved.
