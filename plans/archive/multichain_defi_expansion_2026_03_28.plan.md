---
name: multichain-defi-expansion
remaining_todos_consolidated_into: consolidated_defi_data_pipeline_2026_04_15
overview:
  Prune to 19 EVM chains, add WETH wrap/unwrap, WBTC/cbBTC instruments, generalize gas tracking for non-ETH chains,
  multi-chain instrument discovery
type: code
epic: epic-code-completion
status: active
locked_by: live-defi-rollout
locked_since: 2026-03-28

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-market-interface
    code: C0
    deployment: none
    business: none
  - repo: execution-service
    code: C0
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: position-balance-monitor-service
    code: C0
    deployment: none
    business: none
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none

depends_on: []

> **Conflict resolution**: QG sweep (last pending item) must complete before instrument_schema_cohesion Phase 2 adapter updates run. This plan owns chain_id logic in adapters; instrument_schema_cohesion owns field names/enum values. Both modify the same 25+ adapter files — cannot run simultaneously.

todos:
  # Phase 1: UAC Foundation (DONE — 2026-03-27)
  - id: uac-chain-registry
    content: |
      - [x] [AGENT] P0. Prune CHAIN_RPC_TEMPLATES (drop 100,146,5000,80094; add 57073 Ink). Add CHAIN_NATIVE_GAS_TOKEN, WETH_ADDRESSES, WBTC_ADDRESSES, CBBTC_ADDRESSES, helper functions to _defi.py. Export from registry.
    status: done
    note: "19 EVM chains + Sepolia. All addresses verified."
  - id: uac-gas-token-schema
    content: |
      - [x] [AGENT] P0. Add WRAP/UNWRAP to GasCostAction. Add GasTokenBalanceImpact model to gas_cost.py. Add optional native_token/gas_cost_native fields to InstructionGasCost. Export from defi facade.
    status: done
    note: ""

  # Phase 2: Downstream Pruning + WETH (DONE — 2026-03-27)
  - id: umi-prune-chains
    content: |
      - [x] [AGENT] P0. Prune CHAIN_TO_ALCHEMY_NETWORK and CHAIN_ID_TO_NAME — remove Gnosis, Sonic, Mantle, Berachain. Add Ink.
    status: done
    note: ""
  - id: exec-prune-and-tokens
    content: |
      - [x] [AGENT] P0. Prune CHAIN_GAS_MULTIPLIERS, CHAIN_METADATA, WELL_KNOWN_TOKENS. Add WETH/WBTC/cbBTC per chain to WELL_KNOWN_TOKENS from UAC addresses.
    status: done
    note: ""
  - id: exec-weth-connector
    content: |
      - [x] [AGENT] P0. New weth.py connector — WethConnector(BaseConnector) with wrap(chain_id, amount) and unwrap(chain_id, amount). Uses WETH deposit()/withdraw() function selectors. Add WRAP/UNWRAP to GasCostModel DEFAULT_GAS_ESTIMATES.
    status: done
    note: ""
  - id: mtds-gas-fee-chains
    content: |
      - [x] [AGENT] P1. Add BSC (56) and Avalanche (43114) to DEFAULT_GAS_FEE_CHAINS.
    status: done
    note: ""

  # Phase 3: Gas Token Generalization (DONE — 2026-03-27)
  - id: exec-gas-token-tracker
    content: |
      - [x] [AGENT] P0. Generalize EthBalanceTracker to GasTokenBalanceTracker. Track native_token per chain via CHAIN_NATIVE_GAS_TOKEN. Return GasTokenBalanceImpact. Keep EthBalanceTracker as alias. Emit GAS_TOKEN_BALANCE_DEBT for non-ETH chains.
    status: done
    note: ""
  - id: exec-gas-model-native
    content: |
      - [x] [AGENT] P0. GasCostModel: generalize calculate_cost/calculate_instruction_cost to use native token price (not just ETH price). Add get_gas_token(chain_id) helper.
    status: done
    note: ""
  - id: utl-gas-token-event
    content: |
      - [x] [AGENT] P1. Add GAS_TOKEN_BALANCE_DEBT event constant to UTL events_interface/schemas.py.
    status: done
    note: ""
  - id: strategy-gas-estimator
    content: |
      - [x] [AGENT] P1. Strategy-service gas estimator: add chain_id param, look up native token, use appropriate token price for gas cost USD.
    status: done
    note: "CrossChainSOR built with per-chain gas + bridge fee scoring."

  # Phase 4: Multi-Chain Instruments (DONE — 2026-03-27 + 2026-03-28)
  - id: uac-subgraph-ids
    content: |
      - [x] [AGENT] P1. Verify and expand SUBGRAPH_IDS in _defi.py. Aave V3 on 10 chains. Uniswap V3 on 5 chains. Compound V3 on 6 chains. Balancer on 4 chains. Curve on 4 chains. All verified from official sources.
    status: done
    note:
      "Compound V3 (Paperclip Labs), Balancer (thegraph.com/explorer), Curve (Messari). Uniswap V3 Base swapped to
      official schema (UniV3-Base)."
  - id: exec-uniswap-multichain
    content: |
      - [x] [AGENT] P1. Uniswap connector: restructure TOKEN_ADDRESSES to chain-keyed dict. Make UniswapConnector chain_id-aware. Import WETH/WBTC from UAC.
    status: done
    note: ""
  - id: instruments-multichain
    content: |
      - [x] [AGENT] P1. instruments-service: adapters accept chain param. Orchestrator instantiates per (protocol, chain) pair using SUBGRAPH_IDS. Dynamic venue generation in factory.py. E2E verified: 589 instruments across 24 venues (545 written).
    status: done
    note:
      "Compound V3 adapter built 2026-03-28. URDI dedup bug fixed (adapter_key→venue). Messari fallback for Uniswap V3
      Base."
  - id: uac-non-evm-chains
    content: |
      - [x] [AGENT] P1. Add Solana chain metadata (RPC templates, token addresses, DeFi protocol registry). Add Bitcoin metadata (RPC templates, tBTC addresses). NonEvmChain enum. Helper functions.
    status: done
    note: "Registry metadata only — full Solana adapter stack is a future epic."

  # Phase 5: Validation (IN PROGRESS — 2026-03-28)
  - id: qg-sweep
    content: |
      - [x] [AGENT] P0. Run quality-gates.sh on all 8 repos. Run bridge E2E tests. Verify WETH wrap/unwrap on testnet.
        *(archived 2026-04-22 — full eight-repo QG + testnet wrap not re-run here; run before next multichain rollout.)*
    status: todo
    note: "QG running on UAC + instruments-service. Bridge E2E passed in previous session (14 tests)."
---

## Context

### Problem

The system supports 22 EVM chains after the bridge expansion, but 4 chains (Sonic, Mantle, Gnosis, Berachain) have
non-ETH gas tokens with minimal DeFi relevance. The EthBalanceTracker only handles ETH. No WETH wrap/unwrap logic
exists. WBTC/cbBTC addresses are incomplete. instruments-service only discovers instruments on Ethereum mainnet.

### Solution

Prune to 19 chains (15 ETH-native + 3 major non-ETH + Sepolia). Add per-chain WETH/WBTC/cbBTC address registry in UAC.
Build WETH wrap/unwrap connector. Generalize gas tracking to handle BNB/MATIC/AVAX native tokens. Enable multi-chain
instrument discovery.

### Execution DAG

```
Phase 1 (PARALLEL: uac-chain-registry, uac-gas-token-schema)
    |
    v [UAC QG gate]
Phase 2 (PARALLEL: umi-prune, exec-prune, exec-weth, mtds-chains)
    |
    v [UMI + exec + MTDS QG gate]
Phase 3 (3a→3b SEQUENTIAL; 3c,3d,3e PARALLEL with 3a)
    |
    v [exec + UTL + PBMS + strategy QG gate]
Phase 4 (4a→4d SEQUENTIAL; 4b,4c PARALLEL)
    |
    v [all QG gate]
Phase 5 (validation)
```
