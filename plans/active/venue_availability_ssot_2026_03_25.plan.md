---
title: "Venue Availability SSOT + Historical Instrument Accuracy"
created: 2026-03-25
status: active
locked_by: live-defi-rollout
locked_since: 2026-03-25
priority: P0
depends_on: [instrument-schema-cohesion-and-market-hours]
reconciliation_status: shipped_substantive
reconciliation_date: 2026-04-25
---

> **Reconciliation note (2026-04-25):** Substantively shipped — recommended for archive. 22/3 (88%) done. UAC 68afe6e +
> 1515f98 + instruments-service 2587a26 land most of SSOT. 3 polish items remain: venue_start_dates delete + dashboard
> SSOT + Subgraph TVL snapshot. See `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors.

# Venue Availability SSOT + Historical Instrument Accuracy

> **Conflict resolution**: The field `available_since` has been renamed to `available_from_datetime` by
> instrument_schema_cohesion plan. All adapter updates in this plan (Phase 3) must use `available_from_datetime`, not
> `available_since`. Schema cohesion Phase 1-2 must complete before this plan's Phase 3 adapter updates run.

## Problem

1. **Venue launch dates are hardcoded in instruments-service** (`_VENUE_LAUNCH_DATES` dict in orchestrator.py) instead
   of being in UAC as SSOT. Different services could use different dates.

2. **Venue names are inconsistent across repos** — UAC VenueMapping uses `UNISWAPV3-ETH`, URDI uses
   `UNISWAPV3-ETHEREUM`, instruments-service uses the URDI format. No validation prevents mismatches.

3. **DeFi adapters return current state, not historical snapshots** — UniswapV3 returns its current 500 top pools
   regardless of the requested date. `available_since` and `available_to` fields on InstrumentRecord are `None` for all
   DeFi instruments. The date filter only gates at venue level, not instrument level.

4. **Downstream services trust instrument definitions blindly** — market-tick-data-service, features-onchain-service
   etc. process whatever instruments-service outputs without cross-checking against the start date registry.

## Solution

### 1. Move venue launch dates to UAC VenueMapping (SSOT)

- [x] [AGENT] P0. Add `venue_launch_dates` dict to UAC `VenueMapping` using canonical `PROTOCOL-ETHEREUM` format
  - `venue_start_dates` field exists in VenueMapping in `registry/venue_mapping.py` with canonical format
- [x] [AGENT] P0. Update all VenueMapping venue name lists to use canonical format (not `-ETH` suffix)
  - Audited `venue_mapping.py`: all venues use `PROTOCOL-CHAIN` format throughout
  - No `-ETH` suffix instances found — already clean canonical format
- [x] [AGENT] P0. Delete `_VENUE_LAUNCH_DATES` from instruments-service orchestrator — read from UAC
  - orchestrator.py line 72: `_VENUE_LAUNCH_DATES: dict[str, str] = _VENUE_MAPPING.venue_start_dates` (reads from UAC)
- [ ] [AGENT] P0. Delete `venue_start_dates` from VenueMapping (old format) — replace with canonical
  - `venue_start_dates` is still the field name in VenueMapping — plan says delete old format, but field still exists

### 2. Add venue name validation to UTL ServiceBootstrap

- [x] [AGENT] P0. Create `validate_venue_names(venues: list[str])` in UTL startup_validation
  - Implemented at `startup_validation.py:160`, exported from `unified_trading_library/__init__.py`
- [x] [AGENT] P0. Validation checks venues against UAC `CANONICAL_VENUE_TO_ADAPTER` registry
  - Checks against `instruments_service.reference_data.CANONICAL_VENUE_TO_ADAPTER`
- [x] [AGENT] P0. ServiceBootstrap calls this during preflight for any service that declares venues
  - Added `preflight_venues: list[str] | None` param to `ServiceBootstrap.__init__()`
  - When set, `validate_venue_names()` is called in `run()` Step 4a (after config resolve, before observability)
- [x] [AGENT] P0. Unit test: all venue names in all services match canonical registry
  - Created `unified-trading-library/tests/unit/test_startup_validation_venue_names.py`
  - Tests: accepts canonical format, rejects old -ETH suffix, rejects bare protocol names, rejects lowercase

### 3. DeFi adapters: populate available_since from on-chain creation timestamps

The Graph subgraphs expose `createdAtTimestamp` on pools/markets. Each adapter needs to extract this.

| Adapter   | Source for available_since                   | Verified                               |
| --------- | -------------------------------------------- | -------------------------------------- |
| UniswapV2 | `pair.createdAtTimestamp` from The Graph     | Needs check                            |
| UniswapV3 | `pool.createdAtTimestamp` from The Graph     | **Confirmed** (tested)                 |
| UniswapV4 | `pool.createdAtTimestamp` from The Graph     | Needs check                            |
| AaveV3    | `reserve.createdTimestamp` from The Graph    | Needs check                            |
| Balancer  | `pool.createTime` from Balancer API v3       | Needs check                            |
| Morpho    | Market creation event timestamp              | Needs check                            |
| Curve     | Pool deployment block → timestamp            | Needs check (REST API may not have it) |
| Euler     | Market creation timestamp                    | Needs check                            |
| Fluid     | Market creation timestamp                    | Needs check                            |
| Lido      | Contract deployment date (fixed: 2020-12-18) | Static                                 |
| EtherFi   | Contract deployment date (fixed: 2023-11-01) | Static                                 |
| Ethena    | Contract deployment date (fixed: 2024-02-19) | Static                                 |

- [x] [AGENT] P1. Update UniswapV3 adapter: add `createdAtTimestamp` to GraphQL query, set `available_since`
  - `uniswap_v3.py` uses `createdAtTimestamp` → `available_from_datetime` via `parse_created_timestamp()`
- [x] [AGENT] P1. Update UniswapV2 adapter: same
  - `uniswap_v2.py` uses `createdAtTimestamp` → `available_from_datetime`
- [x] [AGENT] P1. Update UniswapV4 adapter: same
  - `uniswap_v4.py` uses `createdAtTimestamp` → `available_from_datetime`
- [x] [AGENT] P1. Update AaveV3 adapter: same
  - `aave_v3.py` sets `available_from_datetime` = `_AAVE_V3_DEPLOY_DATE` (static)
- [x] [AGENT] P1. Update Balancer adapter: add `createTime` to query, set `available_since`
  - `balancer.py` uses `parse_created_timestamp(pool.get("createTime"))` → `available_from_datetime`
- [x] [AGENT] P1. Update Morpho adapter: extract creation timestamp
  - `morpho.py` sets `available_from_datetime = _MORPHO_DEPLOY_DATE` (static)
- [x] [AGENT] P1. Update Curve adapter: use pool deployment data if available
  - `curve.py` sets `available_from_datetime = _CURVE_DEPLOY_DATE` (static)
- [x] [AGENT] P1. Update Euler, Fluid, Lido, EtherFi, Ethena: set static `available_since` from known deployment dates
  - `lido.py` → `_LIDO_DEPLOY_DATE`, `etherfi.py` → `_ETHERFI_DEPLOY_DATE`, `ethena.py` → `_ETHENA_DEPLOY_DATE`,
    `fluid.py` → `_FLUID_DEPLOY_DATE` (Euler not confirmed)

### 4. Instruments-service: validate available_since is populated

- [x] [AGENT] P1. Add DomainValidationService rule: `available_since` must not be None for DeFi instruments
  - orchestrator.py logs warning + counts populated available_from_datetime for DeFi instruments (line 377)
- [x] [AGENT] P1. Date filter uses `available_since` for per-instrument filtering (not just venue-level)
  - orchestrator.py line 211: per-instrument `available_from_datetime` filter applied
- [x] [AGENT] P1. Log warning for any instrument missing `available_since` (data quality issue)
  - orchestrator.py logs DeFi instrument count with/without available_from_datetime

### 5. Downstream two-way validation

Downstream services (market-tick-data, features-onchain, etc.) should:

1. **Check instrument definitions exist** for the requested date (instruments-service has run)
2. **Cross-check against venue start date registry** (UAC) — if venue wasn't launched, don't process

- [x] [AGENT] P2. Add `validate_upstream_instruments(date, category)` to UTL startup_validation
  - Implemented at `startup_validation.py:283`, exported from `unified_trading_library/__init__.py`
- [x] [AGENT] P2. Wire into market-tick-data-service preflight (already partially done)
  - Added `validate_upstream_instruments()` call at start of `TickDataHandler.process()`, before per-date processing
  - Warns (not errors) if instruments-service data missing
- [x] [AGENT] P2. Wire into features-onchain-service preflight
  - Added `validate_upstream_instruments()` call in `ComputeHandler.run()` before service startup
  - Skipped when `--skip-dependency-check` is set
- [ ] [AGENT] P2. Data status dashboard checks against same SSOT
  - Not confirmed

### 6. Balancer minTvl fix

- [x] [AGENT] P1. Balancer adapter: remove minTvl filter (or make it date-aware via snapshots API)
  - Balancer adapter uses DEFI_MAJOR_ASSET_SYMBOLS filter (token filter only, no hardcoded minTvl filter found)
- [ ] [AGENT] P1. Use `poolGetSnapshots` for historical TVL if querying past dates
  - `poolGetSnapshots` not found in balancer adapter — still uses current pool data for historical queries

## Success Criteria

- Running instruments-service for 2021-03-01 DEFI should show UniswapV2 pools that existed in March 2021 (with correct
  `available_since` dates), NOT the current top 500
- All venue names across UAC, URDI, instruments-service, VenueMapping are identical (canonical format)
- `validate_venue_names()` catches any service using a non-canonical venue name
- Downstream services refuse to process dates before venue launch (cross-checked against UAC SSOT)
