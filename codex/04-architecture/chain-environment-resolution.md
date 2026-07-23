---
doc_type: codex-ssot
title: Chain Environment Resolution
summary:
  Resolves canonical chain names (ETHEREUM/ARBITRUM) to chain IDs + RPC URLs via CHAIN_ENV (mainnet/testnet/fork);
  resolve_chain_id/resolve_rpc_url in the UAC registry; 19 EVM chains + Solana + Bitcoin.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [e2e-testing]
scope: [engineer, admin]
tags: [chain-resolution, defi, uac, execution, rpc, configuration]
related:
  [
    /codex/04-architecture/execution-modes-and-chain-resolution.md,
    /codex/04-architecture/wallet-hierarchy-and-capital-flow.md,
    /codex/04-architecture/defi-execution-overview.md,
  ]
created: 2026-03-30
authoritative_for: [canonical chain-name to chain-id and RPC-URL resolution]
referenced_by:
  [
    /codex/04-architecture/defi-phase3-infrastructure.md,
    /codex/04-architecture/execution-modes-and-chain-resolution.md,
    /codex/05-infrastructure/per-venue-paper-policy.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Chain Environment Resolution

## Overview

Strategies declare intent using canonical chain names ("ETHEREUM", "ARBITRUM"). The system resolves these to actual
chain IDs and RPC URLs based on the `CHAIN_ENV` configuration.

## Environment Modes

| CHAIN_ENV | Chain ID (ETH) | RPC Target        | Use Case              |
| --------- | -------------- | ----------------- | --------------------- |
| mainnet   | 1              | Alchemy mainnet   | Live trading          |
| testnet   | 11155111       | Alchemy Sepolia   | Integration testing   |
| fork      | 1 (\*)         | Tenderly fork URL | Batch + paper trading |

(\*) Fork uses mainnet chain IDs but routes to Tenderly fork RPC.

## API

```python
from unified_api_contracts.registry import resolve_chain_id, resolve_rpc_url

# Strategy says "ETHEREUM", system resolves per env
chain_id = resolve_chain_id("ETHEREUM", env="testnet")  # -> 11155111
rpc_url = resolve_rpc_url("ETHEREUM", env="mainnet", alchemy_api_key="...")
```

## Supported Chains

19 EVM chains + Solana + Bitcoin. Full list in: `unified_api_contracts/registry/chain_env.py`

## Configuration

Set via `UnifiedCloudConfig.chain_env` (not env var directly). Default: "mainnet".

E2E testing configs:

- `e2e-testing/configs/defi/local-batch.env` -> CHAIN_ENV=mainnet (batch uses historical data)
- `e2e-testing/configs/defi/local-paper.env` -> CHAIN_ENV=fork (paper uses Tenderly)

## Relationship to Existing Docs

This document focuses narrowly on chain name -> chain ID -> RPC URL resolution. For broader execution mode architecture
(batch/paper/live), strategy-to-execution decision boundary, and smart contract handling, see:

- [Execution Modes & Chain Resolution](execution-modes-and-chain-resolution.md) -- full mode matrix and pipeline details
- [Wallet Hierarchy](wallet-hierarchy-and-capital-flow.md) -- treasury/trading wallet model per chain
- [DeFi Execution Overview](defi-execution-overview.md) -- connector and adapter architecture
