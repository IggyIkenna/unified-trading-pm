---
doc_type: issue
title: client-reporting-api NAV aggregation was blind to vehicle_type (pooled fund vs direct SMA)
status: active
assigned_vm: planning
created: 2026-08-20
author: worker-slot-11
source: [client-reporting-api]
tags: [client-reporting-api, nav, vehicle_type, reporting]
---

# client-reporting-api NAV aggregation was blind to `vehicle_type`

## What I found

`GET /nav` (`client_reporting_api/api/routes/reporting/nav.py`) aggregated every client's equity-curve NAV into a flat
`investors` list with no distinction between a **pooled fund vehicle** (one execution account whose NAV is actually
shared across several underlying investors) and a **direct SMA-style managed account** (one execution account, one
investor).

UAC's domain-layer `ClientDefinition` (`unified_api_contracts/internal/domain/strategy_service/client_registry.py`)
already models this distinction as a required `vehicle_type: Literal["fund", "sma"]` field (see
`/plans/active/client_archetype_vehicle_eligibility_sma_vs_fund_2026_08_20.md` for why it lives there). But
`client-reporting-api`'s client universe is a **disjoint id namespace** — its `ClientConfig` registry
(`client-reporting-api/configs/credentials-registry.yaml`, loaded via `tranche_router.load_registry()`) keys clients by
tranche-desk ids ("PR", "NN", "IK", …), not UAC's client_ids ("acme-fund", "patrick-elysium", …), so there is no direct
join to `ClientRegistry.vehicle_type`.

The reporting-side equivalent signal was already present but unused for NAV purposes: `ClientConfig.is_pooled` +
`ClientConfig.pool_investors` (`unified_api_contracts/internal/reporting/client_config.py`) — e.g. client `IK` is
`is_pooled: true` with `pool_investors: {jihane: 0.253, amaka: 0.216, ik: 0.531}`, a genuine pooled-fund vehicle, but
`nav.py` reported it as one undifferentiated investor row identical in shape to a single-investor SMA client like `PR`
or `NN`. A grep confirmed `is_pooled`/`pool_investors` had **zero consumers anywhere in the codebase** before this fix.

## Why it matters

NAV/investor-register consumers of `/nav` (UI, downstream reporting) could not tell a pooled-fund NAV line from a
direct-managed-account NAV line — the vehicle-type axis UAC now treats as load-bearing for the client model was
invisible in the reporting aggregation layer.

## Recommended decision

Surface vehicle type in the NAV response using the already-present `is_pooled` signal as the reporting-side analogue of
UAC's `vehicle_type` (mapping: `is_pooled: true` → `"fund"`, else → `"sma"`) rather than attempting a cross-namespace
join to UAC's `ClientRegistry` (the two client-id spaces don't overlap). Scope kept to NAV aggregation per the task
brief — splitting a pooled client's NAV row into one row per underlying `pool_investors` entry (which would need
display names for "jihane"/"amaka"/etc. that don't exist anywhere in this codebase today) is a materially bigger,
separate change and is flagged below as a follow-up rather than folded in here.

## Todos

- [x] [BACKEND] P2. Add `vehicle_type` awareness to client-reporting-api's NAV aggregation — `nav.py`:
  `_vehicle_type_for_client()` classifies each client `"fund"` (pooled) / `"sma"` (direct) from `ClientConfig.is_pooled`;
  each investor row now carries `vehicleType`; `_aggregate_nav_investors()` returns and `GET /nav` exposes a new
  `nav_by_vehicle_type: {"fund": ..., "sma": ...}` breakdown. (repo: client-reporting-api) — ✅
  client-reporting-api@1e7baa3383
- [ ] [BACKEND] P3. Split a pooled client's NAV investor row (e.g. `IK`) into one row per `pool_investors` entry
  (weighted by their pool share) instead of one blended row per execution account — needs display names for pool
  sub-investors (none exist today; `CLIENT_NAMES` only maps execution-account ids). (repo: client-reporting-api)

## Progress Log

- 2026-08-20 (slot 11): Filed + fixed inline. `is_pooled`/`pool_investors` were unused fields on `ClientConfig` prior to
  this change (confirmed via grep — zero call sites). Implemented `vehicle_type` mapping in `nav.py` only, per the
  task's `context_scope`. Follow-up (per-pool-investor NAV split) tracked as a separate P3 todo above, left open.
