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
status: open
resolved_by:
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

## Todos

- [ ] [BACKEND] P2. Add `vehicle_type` awareness to client-reporting-api's NAV aggregation
  (`client_reporting_api/api/routes/reporting/nav.py`'s `_nav_investor_for_client`/`_aggregate_nav_investors`) —
  either (a) cross-reference the client_id against `CLIENT_REGISTRY` and exclude/flag any `sma`-typed client from
  the pooled-fund NAV aggregate, or (b) if `credentials-registry.yaml`'s own `ClientConfig` should instead carry its
  OWN `vehicle_type` field (avoiding a cross-registry lookup from client-reporting-api into strategy-service's UAC
  domain), state that as the chosen design and implement it there instead. Either path is acceptable; picking one and
  stating why is the deliverable. Done-when: a test seeds one `fund` and one `sma` client, and asserts the `sma`
  client is excluded from (or clearly flagged out of) the NAV aggregate `investors`/`current_nav` totals.

- [ ] [REVIEW] P3. Confirm no other client-reporting-api view (fee summary, capital flows) has the same blind spot —
  state the finding as a fact per view checked, not just the NAV route.

## Progress Log

- **2026-08-20**: Filed by `client_archetype_vehicle_eligibility_sma_vs_fund_finalize_2026_08_20`'s own todo 2,
  during the operator's `/autonomous` session that shipped the vehicle-eligibility work this issue follows on from.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
