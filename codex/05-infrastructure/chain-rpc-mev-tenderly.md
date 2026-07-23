---
doc_type: codex-ssot
title: Chain RPC + MEV protection + Tenderly + Gas oracles
summary:
  Per-chain operational matrix — for every chain in CHAIN_GENESIS_DATES, the RPC primary/fallback providers,
  MEV-protection endpoints (Flashbots / MEV-Blocker / Jito), gas-oracle source, Tenderly account + bundle-simulation
  gating policy, oracle-price source, and historical gas/oracle backfill bucket paths.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [defi, execution, mev, tenderly, gas-oracle, mtds]
related:
  [
    /codex/04-architecture/mev-protection.md,
    /codex/04-architecture/tenderly-execution-provider.md,
    /codex/02-data/defi-venue-protocol-catalogue.md,
    /codex/02-data/defi-data-type-taxonomy.md,
  ]
created: 2026-05-10
authoritative_for:
  [
    per-chain RPC provider redundancy + MEV-protection endpoint registry + gas-oracle sources + Tenderly
    bundle-simulation gating policy,
  ]
referenced_by:
  [
    /codex/02-data/defi-venue-protocol-catalogue.md,
    /codex/04-architecture/mev-protection.md,
    /codex/07-security/mev-protection.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Chain RPC + MEV protection + Tenderly + Gas oracles

> SSOT for chain-level infrastructure: per-chain RPC providers (primary + fallback), MEV-protection RPC endpoints,
> Tenderly account/project + bundle-simulation gating policy, gas oracle sources, historical gas/oracle capture bucket
> paths. Last updated 2026-05-10 (defi_catalogue_chain_primitives Phase 5D).

This doc complements [`mev-protection.md`](/codex/04-architecture/mev-protection.md) (which covers the protection
mechanism) and [`tenderly-execution-provider.md`](/codex/04-architecture/tenderly-execution-provider.md) (which covers
the execution provider abstraction). This doc is the **per-chain operational matrix** — for every chain in
`CHAIN_GENESIS_DATES`, what RPC providers + MEV protection + gas oracle + Tenderly setup we use.

## Per-chain matrix (in scope for May-23 cutover)

| Chain          | Genesis    | RPC primary                 | RPC fallback                | MEV protection                                                                                               | Gas oracle                                                                            | Tenderly chain_id                          | Backfill bucket                                        |
| -------------- | ---------- | --------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------ |
| **Ethereum**   | 2015-07-30 | Alchemy                     | QuickNode (Phase 5B)        | Flashbots Protect (`rpc.flashbots.net`); MEV Blocker (`rpc.mevblocker.io`); Manifold                         | EIP-1559 base + priority via `gas_fee_client.py:316`                                  | 1                                          | `gs://gas-fees-central-element-323112/chain=ethereum/` |
| **Arbitrum**   | 2021-08-31 | Alchemy                     | public RPC                  | Sequencer-only (centralised; structural MEV reduction)                                                       | sequencer RPC                                                                         | 42161                                      | `.../chain=arbitrum/`                                  |
| **Base**       | 2023-08-09 | Alchemy                     | public RPC                  | Sequencer-only                                                                                               | sequencer RPC                                                                         | 8453                                       | `.../chain=base/`                                      |
| **Optimism**   | 2021-12-16 | Alchemy                     | public RPC                  | Sequencer-only                                                                                               | sequencer RPC                                                                         | 10                                         | `.../chain=optimism/`                                  |
| **Polygon**    | 2020-05-30 | Alchemy                     | public RPC                  | (no Flashbots equivalent yet — operator decision: accept public mempool exposure or skip Polygon for May-23) | EIP-1559                                                                              | 137                                        | `.../chain=polygon/`                                   |
| **Avalanche**  | 2020-09-22 | Alchemy                     | public RPC                  | (no Flashbots equivalent)                                                                                    | EIP-1559                                                                              | 43114                                      | `.../chain=avalanche/`                                 |
| **BSC**        | 2020-08-29 | Alchemy                     | public RPC                  | (no Flashbots equivalent)                                                                                    | EIP-1559                                                                              | 56                                         | `.../chain=bsc/`                                       |
| **Linea**      | 2023-07-11 | Alchemy                     | public RPC                  | Sequencer-only                                                                                               | sequencer                                                                             | 59144                                      | `.../chain=linea/`                                     |
| **Scroll**     | 2023-10-17 | Alchemy / public Scroll RPC | public RPC                  | Sequencer-only                                                                                               | sequencer                                                                             | 534352                                     | `.../chain=scroll/`                                    |
| **ZkSync Era** | 2023-03-24 | Alchemy / public ZK RPC     | public RPC                  | Sequencer-only                                                                                               | sequencer                                                                             | 324                                        | `.../chain=zksync/`                                    |
| **Solana**     | 2020-03-16 | Helius                      | Alchemy + public Solana RPC | **Jito bundle submission** (Phase 5A `JitoBundleProvider`)                                                   | priority-fees-lamports + compute-unit-price + Jito tip via `solana_gas_client.py:277` | n/a (Solana-specific Tenderly support TBD) | `.../chain=solana/`                                    |
| **StarkNet**   | n/a (L2)   | Voyager / Alchemy           | public RPC                  | Sequencer-only                                                                                               | n/a (StarkNet fee model)                                                              | n/a                                        | `.../chain=starknet/`                                  |

Other chains in `CHAIN_GENESIS_DATES` (Celo / Aurora / Fantom / Mantle / Gnosis / Metis / Moonbeam / Blast / Mode):
declared in UAC but no DeFi protocols catalogued for May-23. RPC providers TBD if scope expands post-cutover.

## RPC provider redundancy

Per CLAUDE.md "C6 — RPC provider redundancy" finding: every chain in scope has ≥ 2 independent RPC providers per
[`defi_catalogue_chain_primitives` Phase 5B]. Implementation:

```yaml
# execution-service/execution_service/config/chain_config.yaml
rpc_providers:
  ethereum:
    primary: alchemy
    fallbacks: [quicknode, public]
    fallback_policy: auto-failover-on-5xx-or-429
    retry_budget: 3
  arbitrum:
    primary: alchemy
    fallbacks: [quicknode, public]
    fallback_policy: auto-failover-on-5xx-or-429
    retry_budget: 3
  solana:
    primary: helius
    fallbacks: [alchemy_solana, public_solana]
    fallback_policy: auto-failover-on-5xx-or-429
    retry_budget: 3
  # ... per-chain
```

`RpcProviderFallback` class (Phase 5B) handles fail-over deterministically + emits `RPC_PROVIDER_FAILOVER` events (per
CLAUDE.md "No fire-and-forget VM launches" event-stream contract).

## MEV protection per chain

Per [`mev-protection.md`](/codex/04-architecture/mev-protection.md) — 5 layers of MEV protection across the system. This
section is the **per-chain endpoint registry**.

| MevSubmissionMode        | Endpoint ref (UCI/Secret Manager)                     | Supported chains                                 | Auth signer                                                | Status                                                                                                                                                                                                                          |
| ------------------------ | ----------------------------------------------------- | ------------------------------------------------ | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PUBLIC_MEMPOOL`         | `chain_rpc_default`                                   | Ethereum, Arbitrum, Optimism, Base, Polygon, BSC | none                                                       | always available                                                                                                                                                                                                                |
| `FLASHBOTS_PROTECT`      | `flashbots_protect_rpc` (`https://rpc.flashbots.net`) | Ethereum                                         | none (free)                                                | ✅ wired via `PrivateMempoolProvider`                                                                                                                                                                                           |
| `MEV_BLOCKER`            | `mev_blocker_rpc` (`https://rpc.mevblocker.io`)       | Ethereum                                         | none (free)                                                | ✅ wired via `PrivateMempoolProvider`                                                                                                                                                                                           |
| `MANIFOLD`               | `manifold_finance_rpc`                                | Ethereum                                         | TBD                                                        | ◐ partially wired                                                                                                                                                                                                               |
| `FLASHBOTS_BUNDLE_RELAY` | `relay.flashbots.net` (`eth_sendBundle`)              | Ethereum                                         | required (paid auth signer)                                | ✗ STUBBED. Not needed for May-23 cutover (Aave flash loans are single-tx atomic; cross-chain carry legs can't bundle). Out of scope per operator 2026-05-10. Post-cutover if needed.                                            |
| `JITO_BUNDLE` (Phase 5A) | `jito_block_engine_rpc`                               | Solana                                           | required (paid Jito subscription OR free with rate limits) | ◐ enum + `_DEFAULT_POLICIES[JITO_BUNDLE]` policy shipped 2026-05-12 (UAC@`5241fad0` + execution-service@`38710bef`); `JitoBundleProvider` class implementation pending Harsh-side per `defi_catalogue` Phase 5A remaining scope |

> **[DELTA 2026-05-22]** **Current state:** `JitoBundleProvider` class implementation is PENDING (Phase 5A Harsh-side
> work). Enum + default policy shipped. `MANIFOLD` is partially wired. **Planned delta:** `JitoBundleProvider` full
> implementation tracked under `plans/epics/defi_master.md` § MEV. **Target architecture:** All `MevSubmissionMode`
> variants fully implemented with provider classes in `execution_service/defi_execution/mev/`.

Per-chain MEV story:

- **Ethereum**: Flashbots Protect + MEV Blocker (private RPC, free, sandwich-protected). Manifold partial. Bundle Relay
  stubbed but not needed (see above).
- **Arbitrum / Optimism / Base / Linea / Scroll / ZkSync**: centralised sequencers eliminate mempool MEV. No Flashbots
  equivalent because the protection is structural (single sequencer = no public mempool to attack).
- **Polygon / Avalanche / BSC**: public mempool, no Flashbots equivalent. Operator decision: accept exposure with
  tighter slippage tolerance + L2 routing preference where archetype allows; OR skip these chains for May-23 if exposure
  unacceptable.
- **Solana**: Jito bundle submission via `JitoBundleProvider` for prioritised + MEV-protected inclusion. Composes with
  `JITO_BUNDLE` MevSubmissionMode.

## Tenderly setup

Per [`tenderly-execution-provider.md`](/codex/04-architecture/tenderly-execution-provider.md). This section is the
operational policy.

**Account / project**:

- API key: Secret Manager `tenderly_api_key`
- Account slug + project slug: UCI config + Secret Manager
- Plan: paid tier with bundle-simulation API access

**Per-archetype daily simulation budget** (provisional defaults; operator can override):

| Archetype               | Daily budget    | Sims per live order | Bundle sims/day |
| ----------------------- | --------------- | ------------------- | --------------- |
| `carry_staked_basis`    | $50/day         | 1 per order         | ~50/day         |
| `leveraged_funding_arb` | $50/day         | 1 per order         | ~50/day         |
| Other archetypes        | $25/day default | 1 per order         | ~25/day         |

Budget tracked via Tenderly billing API + execution-service usage counter. Budget exhaustion downgrades to advisory-
only (alert fires; live order placement continues without sim gate).

**Bundle-simulation gating policy** (provisional default per Phase 5C; operator can soften):

- **Every live order goes through bundle-sim**.
- **BLOCK on revert**: if simulated bundle reverts, order rejected + `DefiErrorCode.TX_REVERTED` event emitted.
- **Advisory-log on slippage > threshold**: if simulated bundle succeeds but realized slippage > expected by N bps,
  log + alert but proceed.
- **Soft-fall to advisory-only** when daily budget exhausted.

**Simulation API endpoints used**:

- `POST /api/v1/account/{slug}/project/{slug}/vnets` — create Virtual TestNet fork.
- `POST /api/v1/account/{slug}/project/{slug}/simulate-bundle` — bundle simulation (Phase 5C).
- `POST /api/v1/account/{slug}/project/{slug}/simulate` — single-tx simulation.

## Gas oracles per chain

| Chain                     | Live gas client                                                                                  | Historical capture                                   | Backfill span                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Ethereum + L2s (EIP-1559) | `gas_fee_client.py:316` (`eth_feeHistory` poll)                                                  | `gs://gas-fees-central-element-323112/chain=<x>/`    | ≥ 2 years per master plan (last backfill 2026-05-04 covers 2021-01-01 → 2026-05-03) |
| Solana                    | `solana_gas_client.py:277` (priority-fees-lamports distribution + compute-unit-price + Jito tip) | `gs://gas-fees-central-element-323112/chain=solana/` | ≥ 2 years                                                                           |

`GAS_FEE_CHAIN_START_DATES` SSOT (Phase 1F of cross_asset_group_catalogue_audit) declares per-chain Alchemy archival RPC
coverage start (distinct from `CHAIN_GENESIS_DATES`).

**Pre-flight gas-budget enforcement** (CLAUDE.md "C2 — pre-flight gas-budget enforcement" finding): execution-service
caps `maxPriorityFeePerGas` at 3 gwei for non-urgent transactions per
[`mev-protection.md`](/codex/04-architecture/mev-protection.md) § 3 Gas Price Strategy. Per-archetype gas-budget
enforcement (refuse tx if expected gas cost > X% of expected PnL) location: TBD — flag for follow-up audit
(`cross_asset_group_catalogue_audit` Phase 6).

## Oracle prices per chain

Per [`defi-data-type-taxonomy.md`](/codex/02-data/defi-data-type-taxonomy.md) — `oracle_prices` data_type captured by
`oracle_prices_handler.py` for every chain in scope.

| Chain                                           | Oracle source                                                                   | Captured                                                                             | Coverage start                                           |
| ----------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------- |
| Ethereum + Arbitrum + Base + Optimism + Polygon | Chainlink (eth_call `latestRoundData`)                                          | ✅                                                                                   | per-feed launch dates per UAC `_defi_oracle_coverage.py` |
| Solana                                          | Pyth Hermes (REST API at `hermes.pyth.network/v2/updates/price/{publish_time}`) | ✅ batch via Hermes pull                                                             | 2023-10-01 per UAC `_defi_oracle_coverage.py:36`         |
| Solana (live)                                   | PythNet RPC subscription                                                        | ◐ batch wired via Hermes; live PythNet RPC not yet wired — post-cutover P1 follow-up | n/a                                                      |
| Cross-chain Pyth on EVM via Wormhole            | not in scope; Solana-only Pyth boundary                                         | ✗                                                                                    | n/a                                                      |

**Protocol-internal oracles** (Uniswap V3 TWAP / Curve EMA / Aave price oracle): Aave's internal oracle IS Chainlink
with fallback; existing Chainlink capture covers it. Uniswap TWAP + Curve EMA NOT explicitly captured. Gap (P2 per
question doc finding).

**Off-chain feeds (CoinGecko / CMC / venue mid)**: OUT OF SCOPE per operator decision 2026-05-10 — arb-vs-oracle
reconciliation is implied by any price-arb strategy itself.

## Cross-references

- [`mev-protection.md`](/codex/04-architecture/mev-protection.md) — MEV protection mechanism details (canonical post-
  consolidation per `cross_asset_group_catalogue_audit_2026_05_10` Phase 4).
- [`tenderly-execution-provider.md`](/codex/04-architecture/tenderly-execution-provider.md) — Tenderly provider
  abstraction.
- [`defi-venue-protocol-catalogue.md`](/codex/02-data/defi-venue-protocol-catalogue.md) — protocol catalogue (cross-
  references this doc's per-chain matrix).
- UAC: [`registry/chain_env.py`](../../../unified-api-contracts/unified_api_contracts/registry/chain_env.py)
  (`CHAIN_GENESIS_DATES` + `CHAIN_RPC_TEMPLATES` + `resolve_rpc_url`).
- UAC:
  [`registry/capability_declarations/_defi_oracle_coverage.py`](../../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_oracle_coverage.py)
  (oracle coverage start dates).
- execution-service:
  [`execution_service/v2/mev_router.py`](../../../execution-service/execution_service/v2/mev_router.py)
  (MevSubmissionPolicy registry).
- execution-service:
  [`execution_service/defi_execution/mev/`](../../../execution-service/execution_service/defi_execution/mev/) (Flashbots
  / private mempool / Jito bundle providers).
- execution-service:
  [`execution_service/providers/tenderly.py`](../../../execution-service/execution_service/providers/tenderly.py)
  (TenderlyExecutionProvider).
- MTDS:
  [`market_interface/clients/gas_fee_client.py`](../../../market-tick-data-service/market_tick_data_service/market_interface/clients/gas_fee_client.py)
  - [`solana_gas_client.py`](../../../market-tick-data-service/market_tick_data_service/market_interface/clients/solana_gas_client.py).
- MTDS:
  [`cli/handlers/oracle_prices_handler.py`](../../../market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py)
  (Chainlink + Pyth Hermes capture handler).

## Update protocol

When adding a new chain:

1. Add to `CHAIN_GENESIS_DATES` in UAC.
2. Add RPC template to `CHAIN_RPC_TEMPLATES`.
3. Add row to "Per-chain matrix" + "RPC provider redundancy" + "MEV protection" + "Gas oracles" sections of this doc.
4. Provision `chain_config.yaml` rpc_providers entry with primary + fallbacks.
5. Add MEV-protection RPC if available (else document "no Flashbots equivalent").
6. Backfill gas + oracle history per chain (≥ 2 years per master plan).
7. Add to `defi-venue-protocol-catalogue.md` per-chain coverage row.

When adding a new MEV submission mode:

1. Add to UAC `MevSubmissionMode` enum.
2. Add policy to `mev_router.py:_DEFAULT_POLICIES`.
3. Implement provider class in `defi_execution/mev/`.
4. Update "MEV protection per chain" table here.
