---
title: "Venue Availability SSOT + Historical Instrument Accuracy"
created: 2026-03-25
status: active
locked_by: live-defi-rollout
locked_since: 2026-03-25
priority: P0
---

# Venue Availability SSOT + Historical Instrument Accuracy

## Problem

1. **Venue launch dates are hardcoded in instruments-service** (`_VENUE_LAUNCH_DATES` dict in orchestrator.py) instead of
   being in UAC as SSOT. Different services could use different dates.

2. **Venue names are inconsistent across repos** — UAC VenueMapping uses `UNISWAPV3-ETH`, URDI uses
   `UNISWAPV3-ETHEREUM`, instruments-service uses the URDI format. No validation prevents mismatches.

3. **DeFi adapters return current state, not historical snapshots** — UniswapV3 returns its current 500 top pools
   regardless of the requested date. `available_since` and `available_to` fields on InstrumentRecord are `None` for all
   DeFi instruments. The date filter only gates at venue level, not instrument level.

4. **Downstream services trust instrument definitions blindly** — market-tick-data-service, features-onchain-service etc.
   process whatever instruments-service outputs without cross-checking against the start date registry.

## Solution

### 1. Move venue launch dates to UAC VenueMapping (SSOT)

- [ ] [AGENT] P0. Add `venue_launch_dates` dict to UAC `VenueMapping` using canonical `PROTOCOL-ETHEREUM` format
- [ ] [AGENT] P0. Update all VenueMapping venue name lists to use canonical format (not `-ETH` suffix)
- [ ] [AGENT] P0. Delete `_VENUE_LAUNCH_DATES` from instruments-service orchestrator — read from UAC
- [ ] [AGENT] P0. Delete `venue_start_dates` from VenueMapping (old format) — replace with canonical

### 2. Add venue name validation to UTL ServiceBootstrap

- [ ] [AGENT] P0. Create `validate_venue_names(venues: list[str])` in UTL startup_validation
- [ ] [AGENT] P0. Validation checks venues against UAC `CANONICAL_VENUE_TO_ADAPTER` registry
- [ ] [AGENT] P0. ServiceBootstrap calls this during preflight for any service that declares venues
- [ ] [AGENT] P0. Unit test: all venue names in all services match canonical registry

### 3. DeFi adapters: populate available_since from on-chain creation timestamps

The Graph subgraphs expose `createdAtTimestamp` on pools/markets. Each adapter needs to extract this.

| Adapter | Source for available_since | Verified |
|---------|--------------------------|----------|
| UniswapV2 | `pair.createdAtTimestamp` from The Graph | Needs check |
| UniswapV3 | `pool.createdAtTimestamp` from The Graph | **Confirmed** (tested) |
| UniswapV4 | `pool.createdAtTimestamp` from The Graph | Needs check |
| AaveV3 | `reserve.createdTimestamp` from The Graph | Needs check |
| Balancer | `pool.createTime` from Balancer API v3 | Needs check |
| Morpho | Market creation event timestamp | Needs check |
| Curve | Pool deployment block → timestamp | Needs check (REST API may not have it) |
| Euler | Market creation timestamp | Needs check |
| Fluid | Market creation timestamp | Needs check |
| Lido | Contract deployment date (fixed: 2020-12-18) | Static |
| EtherFi | Contract deployment date (fixed: 2023-11-01) | Static |
| Ethena | Contract deployment date (fixed: 2024-02-19) | Static |

- [ ] [AGENT] P1. Update UniswapV3 adapter: add `createdAtTimestamp` to GraphQL query, set `available_since`
- [ ] [AGENT] P1. Update UniswapV2 adapter: same
- [ ] [AGENT] P1. Update UniswapV4 adapter: same
- [ ] [AGENT] P1. Update AaveV3 adapter: same
- [ ] [AGENT] P1. Update Balancer adapter: add `createTime` to query, set `available_since`
- [ ] [AGENT] P1. Update Morpho adapter: extract creation timestamp
- [ ] [AGENT] P1. Update Curve adapter: use pool deployment data if available
- [ ] [AGENT] P1. Update Euler, Fluid, Lido, EtherFi, Ethena: set static `available_since` from known deployment dates

### 4. Instruments-service: validate available_since is populated

- [ ] [AGENT] P1. Add DomainValidationService rule: `available_since` must not be None for DeFi instruments
- [ ] [AGENT] P1. Date filter uses `available_since` for per-instrument filtering (not just venue-level)
- [ ] [AGENT] P1. Log warning for any instrument missing `available_since` (data quality issue)

### 5. Downstream two-way validation

Downstream services (market-tick-data, features-onchain, etc.) should:
1. **Check instrument definitions exist** for the requested date (instruments-service has run)
2. **Cross-check against venue start date registry** (UAC) — if venue wasn't launched, don't process

- [ ] [AGENT] P2. Add `validate_upstream_instruments(date, category)` to UTL startup_validation
- [ ] [AGENT] P2. Wire into market-tick-data-service preflight (already partially done)
- [ ] [AGENT] P2. Wire into features-onchain-service preflight
- [ ] [AGENT] P2. Data status dashboard checks against same SSOT

### 6. Balancer minTvl fix

- [ ] [AGENT] P1. Balancer adapter: remove minTvl filter (or make it date-aware via snapshots API)
- [ ] [AGENT] P1. Use `poolGetSnapshots` for historical TVL if querying past dates

## Success Criteria

- Running instruments-service for 2021-03-01 DEFI should show UniswapV2 pools that existed in March 2021
  (with correct `available_since` dates), NOT the current top 500
- All venue names across UAC, URDI, instruments-service, VenueMapping are identical (canonical format)
- `validate_venue_names()` catches any service using a non-canonical venue name
- Downstream services refuse to process dates before venue launch (cross-checked against UAC SSOT)
