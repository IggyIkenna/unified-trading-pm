---
doc_type: plan
title: DeFi live-poller phased build — 39 BLOCKED-BUILD venues
summary: >-
  Enumerates the 39 DeFi venues still resolving to a BLOCKED-BUILD live-poller scaffold
  (dex_swap_scaffold_ws.py + defi_lending_scaffold_ws.py) and phases a real-connector build across
  4 tranches by chain footprint, gated on first extracting the two already-proven connector
  patterns into reusable, config-driven base classes so each tranche is N config rows, not N
  hand-written files.
status: draft
nature: design
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, live-capture, wsfeedconnector, phased-build, connector-pattern]
related:
  [
    /plans/active/defi_operator_ruling_ao_dispatch_2026_08_15.md,
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "defi_operator_ruling_ao_dispatch_2026_08_15.md todo 3, operator-approved DeFi live capture 2026-08-15"
locked_by:
context_scope:
  [
    /plans/active/defi_operator_ruling_ao_dispatch_2026_08_15.md,
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
  ]
locked_since:
resolved_by:
---

# DeFi live-poller phased build — 39 BLOCKED-BUILD venues

> This plan is the deliverable for `defi_operator_ruling_ao_dispatch_2026_08_15.md` todo 3
> ("produce a phased build plan"). It does not build pollers itself — done-when is this plan
> existing and reviewed. `status: draft` on purpose: each tranche below needs an operator
> priority sign-off before its todos are extracted into an AO-dispatchable batch (mirroring the
> `<ag>_satellite_ao_dispatch_batchN` pattern), same as any other draft-gated phase chain.

## Current state (measured, not the ~40 estimate)

Two scaffold registries in `market_tick_data_service/live/connectors/` currently register 41
canonical UAC venue keys behind `DexSwapPlaceholderWSFeedConnector` /
`DefiLendingPlaceholderWSFeedConnector`, whose `connect()` raises `NotImplementedError` with a
`BLOCKED-BUILD` message (honest-absence, not a runtime failure):

- `dex_swap_scaffold_ws.py` — 22 keys (`DEX_SWAP_SCAFFOLD_VENUES`)
- `defi_lending_scaffold_ws.py` — 19 keys (`DEFI_LENDING_SCAFFOLD_VENUES`)

Two of those 41 have already been taken over by real connectors (`overwrite=True` re-registration,
confirmed in `connectors/__init__.py` import order):

- `UNISWAP_V3-ETHEREUM` → `dex_swap_uniswap_v3_ws.py` (subgraph-polling pattern)
- `AAVE_V3-ETHEREUM` → `aave_liquidations_ethereum_ws.py` (on-chain-event-log pattern)

**39 venues remain BLOCKED-BUILD today** (21 dex-swap + 18 lending) — matching the `~40` estimate
in Finding D of `cross_ag_live_capture_parity_2026_08_14.md`.

## Shared connector patterns already proven — the per-venue-cost lever

Both real connectors built so far are hand-written, single-venue modules, but each already
demonstrates a pattern that generalizes across most of the remaining 39:

1. **Subgraph-polling pattern** (`dex_swap_uniswap_v3_ws.py`) — polls the SAME Graph subgraph the
   batch adapter reads (via the existing `SubgraphService`), guaranteeing
   `paper(W) == batch-rerun(W)` by construction. This is the correct pattern for every DEX-swap
   venue in `DEX_SWAP_SCAFFOLD_VENUES` — all 10 protocol families are Uniswap-V2/V3-shaped AMMs or
   Balancer-shaped pools, each with an existing Graph subgraph (the batch adapters already read
   them; `curve_defi_ws.py` / `morpho_defi_ws.py` / `orca_defi_ws.py` / `raydium_defi_ws.py` are
   prior art for the same polling shape on other protocols).
2. **On-chain-event-log pattern** (`aave_liquidations_ethereum_ws.py`, wraps
   `OnChainEventPoller`/`eth_getLogs`) — correct pattern for lending-protocol liquidation streams
   (`AAVE_V3-*`, `COMPOUND_V3-*`), which are indexed by contract event topic, not a subgraph swap
   feed.

**The actual per-venue build cost today is inflated by duplication, not by novel design work**:
`aave_liquidations_ethereum_ws.py` hardcodes one chain's RPC URL + contract address in the module
itself — the same shape repeated 17 more times (9 more AAVE_V3 chains + 6 more COMPOUND_V3 chains
+ MORPHO-BASE) is 17 near-duplicate files. Same for the subgraph pattern across 20 more DEX
venues. **Tranche 0 below is the lever**: extract each pattern into one config-driven class
(protocol/chain/subgraph-id or protocol/chain/RPC-key/contract-address/event-topic as data), so
every subsequent tranche's "build" is a config row + a factory registration, not a new file.

## Tranches

Ordered by chain footprint (Ethereum mainnet first, then the two largest L2s by DEX/lending
volume, then the remaining established L2s/alt-L1s, then the smallest long-tail chains) — a proxy
for TVL priority, not a measured TVL ranking. **Follow-up needed before Tranche 3/4 dispatch**:
pull a real per-chain TVL snapshot (DefiLlama or equivalent) to confirm this ordering before
committing agent time to the lower tranches — see todo below.

### Tranche 0 — connector-pattern extraction (prerequisite, unlocks all tranches)

- [ ] [DATA] P2. Extract `SubgraphPollingConnector`, a config-driven `WSFeedConnector` parameterized
      by `(protocol, chain, subgraph_id, swap_query_template, pool_query_template)`, generalizing
      `dex_swap_uniswap_v3_ws.py`'s implementation. DoD: `UNISWAP_V3-ETHEREUM` re-implemented on
      top of the new base class with zero behavior change (regression: existing unit tests still
      pass unmodified). (repo: market-tick-data-service)
- [ ] [DATA] P2. Extract `OnChainLiquidationPoller`, a config-driven `WSFeedConnector` parameterized
      by `(protocol, chain, rpc_resolver_key, contract_address, event_topic, log_parser)`,
      generalizing `aave_liquidations_ethereum_ws.py`'s implementation. DoD: `AAVE_V3-ETHEREUM`
      re-implemented on top of the new base class with zero behavior change. (repo:
      market-tick-data-service)

### Tranche 1 — Ethereum-mainnet gaps (7 venues)

`UNISWAP_V2-ETHEREUM`, `UNISWAP_V4-ETHEREUM`, `BALANCER-ETHEREUM`, `PANCAKESWAP_V3-ETHEREUM`
(subgraph pattern); `AAVE_V3` (bare umbrella), `COMPOUND_V3` (bare umbrella),
`COMPOUND_V3-ETHEREUM` (event-log pattern). Same chain as the two already-built connectors —
lowest incremental risk, reuses the same RPC/subgraph infra already proven live.

### Tranche 2 — Arbitrum + Base (13 venues)

`UNISWAP_V3-ARBITRUM`, `UNISWAP_V3-BASE`, `SUSHISWAP-ARBITRUM`, `BALANCER-ARBITRUM`,
`BALANCER-BASE`, `PANCAKESWAP_V3-ARBITRUM`, `PANCAKESWAP_V3-BASE`, `CAMELOT_V3-ARBITRUM`,
`AERODROME_V3-BASE` (subgraph pattern); `AAVE_V3-ARBITRUM`, `AAVE_V3-BASE`,
`COMPOUND_V3-ARBITRUM`, `COMPOUND_V3-BASE` (event-log pattern). The two largest L2s by DEX/lending
volume.

### Tranche 3 — Optimism + Polygon + BSC + Avalanche (15 venues)

`UNISWAP_V3-OPTIMISM`, `UNISWAP_V3-POLYGON`, `BALANCER-OPTIMISM`, `BALANCER-POLYGON`,
`BALANCER-AVALANCHE`, `PANCAKESWAP_V3-BSC`, `TRADER_JOE_V2-AVALANCHE`, `VELODROME_V2-OPTIMISM`
(subgraph pattern); `AAVE_V3-OPTIMISM`, `AAVE_V3-POLYGON`, `AAVE_V3-AVALANCHE`, `AAVE_V3-BSC`,
`COMPOUND_V3-OPTIMISM`, `COMPOUND_V3-POLYGON`, `MORPHO-BASE` (event-log pattern).

### Tranche 4 — long-tail chains (4 venues)

`AAVE_V3-LINEA`, `AAVE_V3-SCROLL`, `AAVE_V3-ZKSYNC`, `COMPOUND_V3-SCROLL` (event-log pattern).
Newest/smallest-TVL rollout deployments in the scaffold set — lowest priority under the
chain-footprint proxy.

## Follow-up todos

- [ ] [OPERATOR] P2. Confirm the chain-footprint tranche ordering above against a real per-chain
      TVL snapshot (DefiLlama or equivalent) before Tranche 3/4 are extracted into an
      AO-dispatchable batch — the ordering above is a proxy, not measured data. DoD: ordering
      confirmed or Tranches 3/4 re-sequenced, recorded here.
- [ ] [OPERATOR] P2. Review this phased plan and rule on dispatch cadence — one
      `defi_live_poller_ao_dispatch_batchN` extraction per tranche (mirroring the
      `sports_satellite_ao_dispatch_batchN` pattern), or a different cadence. DoD: ruling recorded
      here, then this plan's `status:` flips from `draft` and the first batch is extracted.

## Progress Log

- **2026-08-15 (data_engineering, slot 10, task `defi_operator_ruling_ao_dispatch-656d2e5acbf7`)**:
  plan created. Enumerated the scaffold registries directly (not the `~40` estimate) — 41
  registered, 2 already taken over by real connectors, 39 currently BLOCKED-BUILD. Identified the
  two proven connector patterns (subgraph-polling, on-chain-event-log) and the duplication they'd
  produce at 39x scale without extraction — Tranche 0 exists specifically to avoid that. Chain-
  footprint tranche ordering is a stated proxy, not measured TVL; follow-up todo filed to confirm
  before later tranches dispatch.
