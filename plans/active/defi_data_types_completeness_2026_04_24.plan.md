---
title: "DeFi data type completeness — 10 missing types + pool policy + data status"
status: active
created: 2026-04-24
locked_by: live-defi-rollout
locked_since: 2026-04-24
---

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

- [ ] [AGENT] P0. Add `DeFiDataType` enum to UAC with all 10 new values: `LIQUIDATION_EVENTS`, `FLASH_LOAN_EVENTS`,
      `STAKING_YIELDS`, `TOKEN_TRANSFERS`, `BRIDGE_EVENTS`, `GAS_FEES`, `POSITION_DATA`, `MEV_EVENTS`,
      `GOVERNANCE_EVENTS`, `EIGENLAYER_REWARDS`. Extend existing DeFi domain facade (don't create new file unless one
      already exists for DeFi data types).
- [ ] [AGENT] P0. Add `DeFiPoolInclusionPolicy` dataclass to UAC: `min_tvl_usd: float`, `min_age_days: int`,
      `asset_whitelist: list[str] | None`, `max_pools_per_protocol: int`. Default: `min_tvl_usd=500_000`,
      `min_age_days=7`, `asset_whitelist=None`, `max_pools=2000`.
- [ ] [AGENT] P0. Register pool inclusion policy in UAC registry keyed by protocol name. Protocol-specific overrides
      (Aave curated whitelist, Curve TVL>$1M) expressed as policy instances in the registry.
- [ ] [QG] P0. `cd unified-api-contracts && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P0. Quickmerge UAC.

### Phase 2 — MTDS adapters: highest-impact types (PARALLEL within phase)

- [ ] [AGENT] P0. `liquidation_events` adapter: Aave V3 (ETHEREUM, ARBITRUM, POLYGON), Morpho. Fetch on-chain
      liquidation call events via subgraph. Write parquet per `venue × chain × date`. ManifestWriter:
      `data_type=LIQUIDATION_EVENTS, instrument_type=LENDING`.
- [ ] [AGENT] P0. `flash_loan_events` adapter: Aave V3 flash loans. Fetch from subgraph `FlashLoan` entities. Write
      parquet per `venue × chain × date`. Include: borrower, token, amount, premium, initiator.
- [ ] [AGENT] P0. `staking_yields` adapter: Lido (stETH APY, daily rate), EigenLayer (restaking APY per operator).
      Requires `defi_instrument_pipeline_and_rewards` EigenLayer work to be merged first — add dependency gate. Write
      `venue=LIDO-ETHEREUM, data_type=STAKING_YIELDS` and `venue=EIGENLAYER-ETHEREUM, data_type=EIGENLAYER_REWARDS`
      rows.
- [ ] [AGENT] P0. `position_data` adapter: Aave V3 user positions (top 500 by supplied_usd), Uniswap V3 LP positions
      (top 1000 by liquidity). Use subgraph for historical. Write per `venue × chain × date`.
- [ ] [AGENT] P0. `token_transfers` adapter: ERC-20 transfer events for top 20 DeFi tokens (WETH, USDC, USDT, DAI, WBTC,
      stETH, AAVE, UNI, CRV, BAL, COMP, MKR, SNX, LDO, RETH, cbETH, EIGEN, ETHFI, OP, ARB). Fetch from Alchemy/Infura
      event logs or TheGraph. One shard = token × chain × date.
- [ ] [QG] P0. `cd market-tick-data-service && bash scripts/quality-gates.sh` (all Phase 2 adapters).
- [ ] [SCRIPT] P0. Quickmerge MTDS with Phase 2 adapters.

### Phase 3 — MTDS adapters: secondary types (PARALLEL within phase)

- [ ] [AGENT] P1. `gas_fees` adapter: daily aggregate gas stats per chain (mean/median/P95/P99 gas price, total gas
      used, EIP-1559 base fee). Source: Etherscan API or on-chain block headers. One shard = chain × date.
      `instrument_type=SPOT_ASSET, venue=ETHEREUM (or ARBITRUM, etc.)`.
- [ ] [AGENT] P1. `bridge_events` adapter: top 5 bridges (Across, Stargate, Hop, Synapse, Wormhole). Fetch bridge
      transfer events from each bridge's subgraph. Shard = bridge × source_chain × dest_chain × date.
- [ ] [AGENT] P1. `governance_events` adapter: Compound, Aave, Uniswap DAO. Fetch proposal + vote events from Tally API
      or governance subgraphs. Shard = protocol × date. `data_type=GOVERNANCE_EVENTS`.
- [ ] [AGENT] P1. `mev_events` adapter: MEV-Boost relay data (Flashbots, BloXroute MEV-Boost). Fetch builder/relay stats
      per block. Shard = relay × date. Scope: summary stats only (not per-tx MEV).
- [ ] [QG] P1. `cd market-tick-data-service && bash scripts/quality-gates.sh` (all Phase 3 adapters).
- [ ] [SCRIPT] P1. Quickmerge MTDS with Phase 3 adapters.

### Phase 4 — Pool filtering policy enforcement (SEQUENTIAL after Phase 1)

- [ ] [AGENT] P0. Update Uniswap V2/V3/V4 adapter to call `DeFiPoolInclusionPolicy` from UAC registry instead of inline
      TVL logic. Replace ad-hoc top-N with policy-gated fetch.
- [ ] [AGENT] P0. Update Aave adapter: convert curated whitelist to policy instance in UAC registry. Min borrow
      threshold expressed as `min_tvl_usd` in policy.
- [ ] [AGENT] P0. Update Curve, Balancer, Morpho adapters: apply workspace policy.
- [ ] [AGENT] P0. Add manifest sentinel: after each protocol fetch, write `empty_confirmed` row if 0 pools returned —
      distinguishes "no pools today" from "fetch failed". Alert if pool count drops >20% vs 30d avg.
- [ ] [QG] P0. `cd market-tick-data-service && bash scripts/quality-gates.sh`.
- [ ] [SCRIPT] P0. Quickmerge MTDS.

### Phase 5 — Deployment-api expected counts + data status tab (SEQUENTIAL after Phase 2)

- [ ] [AGENT] P0. Add expected-count rows for all 10 DeFi data types in deployment-api expectation config. Use
      `expected > 0` so absence flags as gap. Set per-protocol minimums based on Phase 2/3 delivery.
- [ ] [AGENT] P0. deployment-api `/data-status` response: add `data_type` breakdown for DEFI (mirrors existing SPORTS
      `breakdown_axis: data_type` pattern). Return per-(venue, chain, data_type, date) rows.
- [ ] [AGENT] P0. deployment-ui data-status page: show DeFi by `data_type` in the breakdown axis selector (currently
      only `venue` for DeFi). Wire to updated deployment-api response.
- [ ] [QG] P0. `cd deployment-service && bash scripts/quality-gates.sh`.
- [ ] [AGENT] P0. `cd deployment-ui && CI=true npm test -- --run` green.
- [ ] [SCRIPT] P0. Quickmerge deployment-service and deployment-ui.

### Phase 6 — Codex doc + PM

- [ ] [AGENT] P1. Write `codex/02-data/defi-data-types-catalog.md` (scope: [engineer]): Full table of all 14 DeFi data
      types with: name, description, source (subgraph/API/on-chain), shard key, implementation status, protocol
      coverage.
- [ ] [SCRIPT] P1. Quickmerge PM.

## Success criteria

- **Code gates:** All repos QG green; basedpyright clean; ruff clean.
- **Test gates:** Each new adapter has ≥1 unit test with mocked subgraph response.
- **Coverage gate:** deployment-ui data status tab shows 14 DeFi data types with real coverage %; no "100% because
  denominator=0" misleading scores.
- **Pool policy gate:** Uniswap/Aave/Curve/Balancer/Morpho all read policy from UAC registry; no inline TVL logic
  remaining in adapter source.
