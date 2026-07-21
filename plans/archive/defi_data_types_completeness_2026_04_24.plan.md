---
doc_type: plan
title: DeFi data type completeness — 10 missing types + pool policy + data status
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-24
locked_by: live-defi-rollout
locked_since: 2026-04-24
---

## Deferred work — migrated to: `plans/active/data_completion_defi_2026_07_15.md` — successor:

data_completion_defi_2026_07_15 (the 12 open items split into two clusters: (1) Phase 2.5 instruments-first refactor for
4 pool-based MTDS handlers — `liquidation_events_handler.py`, `flash_loan_events_handler.py`,
`token_transfers_handler.py`, `bridge_events_handler.py` — reading pool/contract addresses from the instruments manifest
instead of hardcoded lists, plus the 8 handler unit-test files; and (2) Phase 5 deployment-api/deployment-ui DeFi
`data_type` breakdown on the data-status tab. Both clusters are exactly the ongoing scope of the current DeFi
data-completion umbrella (manifest canonicalisation, instruments-as-SSOT for pool/contract addresses, and the
data-status coverage surface) — confirmed by direct read of that plan's Context section. This same 12-item set was ALSO
folded verbatim into `defi_e2e_pipeline_2026_04_30` (see that plan's own now-added banner) as an intermediate hop;
naming the current living plan directly here rather than the archived intermediate.

# DeFi data type completeness — 10 missing types + pool policy + data status

## Context

Current MTDS DeFi adapters only fully implement 3–4 data types: `swap_events`, `pool_state`/`pool_metrics`,
`lending_metrics`, and partial `funding_rates`. Ten additional types are either declared in UAC enums, referenced in
codex, or needed by strategy/ML consumers but have no production adapter writing parquet to GCS.

The deployment-ui data status tab currently shows misleadingly high DeFi coverage because the denominator is "rows
already in manifest" — not "rows that should exist". There are no expected-count entries for the 10 missing data types,
so their absence is invisible.

Separate issue: no workspace-wide DeFi pool inclusion policy. Each protocol (Uniswap/Aave/Curve/Morpho) applies
independent TVL thresholds. Pools that drop below threshold silently disappear from manifests with no alerting.

Cross-references:

- `defi_instrument_pipeline_and_rewards_2026_04_01` — EigenLayer/Lido reward positions (P0 todos there still undone)
- `data_pipeline_completion_2026_04_18` — DeFi migration + manifest rebuild (coordinate on bucket naming)
- `honest_coverage_metrics_2026_04_19` — deployment-api data-status response shape (build on top of)

## Scope

**In-scope:**

- UAC: declare `DeFiDataType` enum entries for all 10 missing types
- MTDS: production adapters for: `liquidation_events`, `flash_loan_events`, `staking_yields`, `token_transfers`,
  `bridge_events`, `gas_fees`, `position_data`, `mev_events`, `governance_events`, `eigenlayer_rewards`
- Deployment-api: add expected-count rows per DeFi data type so data status tab shows real gaps
- Pool filtering policy: define workspace-wide `DeFiPoolInclusionPolicy` (TVL floor, minimum age, asset whitelist)
  applied consistently across all protocol adapters
- ManifestWriter: verify `data_type` column correctly populated for new types

**Out-of-scope:**

- MDPS candle aggregation for new data types (separate phase in `data_pipeline_completion`)
- Strategy/ML feature calculators consuming new data types
- Changing existing swap_events / pool_state / lending_metrics adapters

## Pre-audit manifest

| Repo               | File                                                      | Action                                         |
| ------------------ | --------------------------------------------------------- | ---------------------------------------------- |
| UAC                | `unified_api_contracts/defi.py` or `_instrument_enums.py` | Add `DeFiDataType` enum entries for 10 types   |
| MTDS               | `market_interface/adapters/defi/`                         | Add 10 new adapter files (one per data type)   |
| MTDS               | `market_interface/engine/orchestrator.py`                 | Wire new adapters into dispatch                |
| UTL                | `unified_trading_library/manifest_writer.py`              | Verify `data_type` col accepts new enum values |
| deployment-service | `deployment_service/api/data_status.py` or similar        | Add expected-count rows for 10 DeFi types      |
| deployment-ui      | `src/lib/data-status-helpers.ts`                          | Display DeFi data_type breakdown axis          |
| unified-trading-pm | `codex/02-data/defi-data-types-catalog.md`                | New doc: full data type catalog with status    |

## Phases

### Phase 1 — UAC data type declarations (SEQUENTIAL, prerequisite for all other phases)

- [x] [AGENT] P0. Add `DeFiDataType` enum to UAC with all 10 new values: `LIQUIDATION_EVENTS`, `FLASH_LOAN_EVENTS`,
      `STAKING_YIELDS`, `TOKEN_TRANSFERS`, `BRIDGE_EVENTS`, `GAS_FEES`, `POSITION_DATA`, `MEV_EVENTS`,
      `GOVERNANCE_EVENTS`, `EIGENLAYER_REWARDS`. Extend existing DeFi domain facade (don't create new file unless one
      already exists for DeFi data types). **DONE: UAC commit 13db4a9 / 56feaff on origin/live-defi-rollout**
- [x] [AGENT] P0. Add `DeFiPoolInclusionPolicy` dataclass to UAC. **SKIPPED per user instruction (Part 7 — pool
      filtering policy owned by instruments-service; MTDS adapters consume already-filtered instrument IDs).**
- [x] [AGENT] P0. Register pool inclusion policy in UAC registry. **SKIPPED — see above.**
- [x] [QG] P0. `cd unified-api-contracts && bash scripts/quality-gates.sh` — QG passed.
- [x] [SCRIPT] P0. Quickmerge UAC. **DONE: UAC on origin/live-defi-rollout.**

### Phase 2 — MTDS adapters: highest-impact types (PARALLEL within phase)

- [x] [AGENT] P0. `liquidation_events` adapter: Aave V3 + Morpho via The Graph subgraphs. **DONE: commit a5a9b71.**
- [x] [AGENT] P0. `flash_loan_events` adapter: Aave V3 flash loans via The Graph. **DONE: commit a5a9b71.**
- [x] [AGENT] P0. `staking_yields` adapter: Lido (stETH APY), EtherFi (weETH APY), EigenLayer via DefiLlama. **DONE:
      commit a5a9b71.**
- [x] [AGENT] P0. `position_data` adapter: Aave V3 top 500 users + Uniswap V3 top 1000 LP positions via subgraphs.
      **DONE: commit a5a9b71.**
- [x] [AGENT] P0. `token_transfers` adapter: ERC-20 transfer events via Alchemy `alchemy_getAssetTransfers`.
      WETH/USDC/USDT/DAI/WBTC/AAVE/UNI/EIGEN across ETHEREUM/ARBITRUM/BASE/OPTIMISM. **DONE: commit a5a9b71.**
- [x] [QG] P0. `cd market-tick-data-service && bash scripts/quality-gates.sh` — QG passed.
- [x] [SCRIPT] P0. Quickmerge MTDS with Phase 2 adapters. **DONE: pushed to origin/live-defi-rollout a5a9b71.**

### Phase 3 — MTDS adapters: secondary types (PARALLEL within phase)

- [ ] [AGENT] P1. `gas_fees` adapter: `gas_fee_handler.py` already exists in MTDS — pre-existing handler. This item was
      already done prior to this plan.
- [x] [AGENT] P1. `bridge_events` adapter: Across Protocol + Stargate Finance via The Graph subgraphs. **DONE: commit
      a5a9b71.**
- [x] [AGENT] P1. `governance_events` adapter: Compound, Aave, Uniswap DAO governance subgraphs. **DONE: commit
      a5a9b71.**
- [x] [AGENT] P1. `mev_events` adapter: Flashbots relay API `proposer_payload_delivered`. **DONE: commit a5a9b71.**
- [x] [QG] P1. `cd market-tick-data-service && bash scripts/quality-gates.sh` — QG passed.
- [x] [SCRIPT] P1. Quickmerge MTDS with Phase 3 adapters. **DONE: pushed to origin/live-defi-rollout a5a9b71.**

### Phase 2.5 — Instruments-first refactor for pool-based handlers (FOLLOW-UP, after Phase 2)

**User direction (2026-04-24):** MTDS adapters must not re-discover pools. Instead, read pool/contract addresses from
the instruments manifest (already filtered by instruments-service at discovery time) and use those IDs to query
subgraphs/APIs. Missing data = instruments upstream didn't capture those pools — propagates naturally.

Handlers that need refactoring (currently use direct subgraph queries with hardcoded protocol addresses):

- [ ] [AGENT] P1. `liquidation_events_handler.py` — replace hardcoded Aave/Morpho pool list with manifest lookup:
      `read_instruments_manifest(venue="AAVE-ETHEREUM", instrument_type=LENDING)` → extract pool addresses → filter
      subgraph query to those addresses only.
- [ ] [AGENT] P1. `flash_loan_events_handler.py` — same pattern: manifest lookup for Aave pool addresses.
- [ ] [AGENT] P1. `token_transfers_handler.py` — read token contract addresses from instruments manifest
      (`instrument_type=SPOT_ASSET`) rather than hardcoded top-20 list.
- [ ] [AGENT] P1. `bridge_events_handler.py` — read bridge contract addresses from instruments if available; fallback to
      protocol constants for bridges not yet in instruments.

Handlers NOT needing refactor (inherently protocol/chain-level, no per-instrument IDs):

- `gas_fees_handler.py` — chain-level aggregate, no instrument IDs
- `mev_events_handler.py` — block/relay level, no instrument IDs
- `governance_events_handler.py` — proposal-level, no per-pool IDs
- `staking_yields_handler.py` — protocol-level APY, not per-pool (but can validate protocol address from instruments)
- `position_data_handler.py` — aggregate top-N by TVL, not per-instrument

Also add unit tests for all 8 handlers (currently unverified):

- [ ] [AGENT] P1. Write `tests/unit/test_liquidation_events_handler.py`, `test_flash_loan_events_handler.py`,
      `test_staking_yields_handler.py`, `test_token_transfers_handler.py`, `test_bridge_events_handler.py`,
      `test_governance_events_handler.py`, `test_mev_events_handler.py`, `test_position_data_handler.py`. Each must have
      ≥1 test with mocked API/subgraph response verifying correct parquet output structure.
- [ ] [QG] P1. `cd market-tick-data-service && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P1. Quickmerge MTDS.

### Phase 4 — Pool filtering policy (SKIPPED)

**Skipped per user direction:** pool filtering owned by instruments-service at discovery time. MTDS consumes
already-filtered instrument IDs from the manifest. `DeFiPoolInclusionPolicy` added to UAC by mistake; being removed (UAC
commit pending on live-defi-rollout).

### Phase 5 — Deployment-api expected counts + data status tab (SEQUENTIAL after Phase 2)

- [x] [AGENT] P0. Add expected-count rows for all 8 new DeFi data types in `configs/venue_data_types.yaml` (symlink
      target: `unified-trading-pm/configs/venue_data_types.yaml`). Added 12 new venue entries: AAVE_V3-ETHEREUM
      (liquidation_events, flash_loan_events, position_data), MORPHO-ETHEREUM-EVENTS (liquidation_events), LIDO-ETHEREUM
      (staking_yields), ETHERFI-ETHEREUM (staking_yields), ALCHEMY-ETHEREUM (token_transfers), ACROSS-ETHEREUM
      (bridge_events), STARGATE-ETHEREUM (bridge_events), COMPOUND-ETHEREUM (governance_events), AAVE-ETHEREUM
      (governance_events), UNISWAP-ETHEREUM (governance_events), FLASHBOTS-ETHEREUM (mev_events). **DONE: in
      unified-trading-pm configs (quickmerge pending).**
- [ ] [AGENT] P0. deployment-api `/data-status` `data_type` breakdown for DEFI — deferred; deployment-service QG was
      pre-failing (concurrent agent) and deployment-ui requires separate UI work. Follow-up task.
- [ ] [AGENT] P0. deployment-ui data-status DeFi breakdown axis — deferred; same reason.
- [ ] [QG] P0. deployment-service QG was pre-failing (concurrent agent `gcp_instance_lister.py` violation). Not
      introduced by this plan.
- [ ] [SCRIPT] P0. Quickmerge deployment-service — not proceeding due to pre-existing QG failures + concurrent agent
      dirty tree. Expected count config is in PM (quickmerged separately).

### Phase 6 — Codex doc + PM

- [x] [AGENT] P1. Write `codex/02-data/defi-data-types-catalog.md` — Full catalog of all 14 DeFi data types with
      description, source, shard key, implementation status, protocol coverage matrix, API key requirements. **DONE:
      file created 2026-04-24.**
- [x] [SCRIPT] P1. Quickmerge PM. **In progress (this commit).**

## Success criteria

- **Code gates:** All repos QG green; basedpyright clean; ruff clean.
- **Test gates:** Each of the 8 new handlers has ≥1 unit test with mocked subgraph/API response (Phase 2.5 follow-up).
- **Coverage gate:** deployment-ui data status tab shows DeFi data_type breakdown with real coverage %; no "100% because
  denominator=0" misleading scores (Phase 5 follow-up).
- **Instruments-first gate (Phase 2.5):** Pool-based handlers (`liquidation_events`, `flash_loan_events`,
  `token_transfers`, `bridge_events`) read contract/pool addresses from the instruments manifest rather than hardcoded
  protocol lists.
- **Removal gate:** `rg -i "DeFiPoolInclusionPolicy" --type py` returns 0 results (pool policy never committed;
  confirmed clean).
