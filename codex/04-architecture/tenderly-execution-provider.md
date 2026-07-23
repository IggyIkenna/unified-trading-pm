---
doc_type: codex-ssot
title: Tenderly Execution Provider
summary:
  Pluggable ExecutionProvider protocol for on-chain execution — TenderlyExecutionProvider spins a Tenderly VNet fork per
  batch/paper run so those modes exercise the exact same contract code paths as live (only the RPC URL differs);
  BenchmarkFillProvider is the no-op oracle-price fallback; the factory routes on mode and falls back if creds are
  absent.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [defi, execution, tenderly, batch-live, simulation, fork, provider]
related:
  [
    /codex/04-architecture/execution-modes-and-chain-resolution.md,
    /codex/04-architecture/defi-execution-overview.md,
    /codex/04-architecture/interface-credential-convention.md,
    /codex/04-architecture/custody-providers.md,
    /codex/04-architecture/amm-slippage-simulation.md,
  ]
created: 2026-03-30
authoritative_for: [Tenderly VNet execution provider + BenchmarkFillProvider]
referenced_by:
  [
    /codex/04-architecture/amm-slippage-simulation.md,
    /codex/04-architecture/custody-providers.md,
    /codex/04-architecture/defi-phase3-infrastructure.md,
    /codex/04-architecture/execution-modes-and-chain-resolution.md,
    /codex/04-architecture/mev-protection.md,
    /codex/05-infrastructure/chain-rpc-mev-tenderly.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Tenderly Execution Provider

## Overview

The execution-service uses a pluggable `ExecutionProvider` protocol to abstract where on-chain transactions execute. The
primary implementation is `TenderlyExecutionProvider`, which creates Tenderly Virtual TestNet (VNet) forks for batch and
paper trading modes. This ensures batch and paper runs exercise the exact same smart contract code paths as live -- the
only difference is the RPC URL.

Location: `execution-service/execution_service/providers/`

## ExecutionProvider Protocol

Defined in `providers/base.py`. All execution targets implement this protocol.

```python
@runtime_checkable
class ExecutionProvider(Protocol):
    async def get_rpc_url(self, chain: str) -> str: ...
    async def fund_wallet(self, address: str, tokens: dict[str, str]) -> None: ...
    async def advance_time(self, seconds: int) -> None: ...
    async def cleanup(self) -> None: ...

    @property
    def provider_type(self) -> str: ...
```

| Method          | Purpose                                                  |
| --------------- | -------------------------------------------------------- |
| `get_rpc_url`   | Return JSON-RPC endpoint for the target chain            |
| `fund_wallet`   | Inject test tokens into a wallet (fork/testnet only)     |
| `advance_time`  | Advance block timestamp by N seconds (batch replay only) |
| `cleanup`       | Delete fork / release resources                          |
| `provider_type` | String identifier (`"tenderly"`, `"benchmark"`)          |

## Implementations

### TenderlyExecutionProvider

Creates a Tenderly VNet fork per run. Constructor parameters:

| Parameter      | Type          | Default  | Description                                 |
| -------------- | ------------- | -------- | ------------------------------------------- |
| `api_key`      | `str`         | required | Tenderly API key from Secret Manager        |
| `account_slug` | `str`         | required | Tenderly account slug                       |
| `project_slug` | `str`         | required | Tenderly project slug                       |
| `chain_id`     | `int`         | `1`      | Target chain EVM ID (1 = Ethereum mainnet)  |
| `block_number` | `int \| None` | `None`   | Pin fork to specific block; `None` = latest |

Internal state:

- `_fork_id` -- VNet ID returned by the Tenderly API (used for deletion)
- `_rpc_url` -- Public HTTPS RPC URL for standard calls
- `_admin_rpc_url` -- Admin HTTPS RPC URL for `tenderly_setBalance` and other privileged methods

### BenchmarkFillProvider

Lightweight no-op provider. Returns empty strings and performs no chain interaction. All fills are computed at oracle
(arrival) price with zero slippage. Used when `--benchmark-fill` is set or when Tenderly credentials are unavailable.

All protocol methods are no-ops:

- `get_rpc_url()` returns `""`
- `fund_wallet()`, `advance_time()`, `cleanup()` do nothing
- `provider_type` returns `"benchmark"`

## Provider Factory

`get_execution_provider()` in `providers/factory.py` routes on the `mode` parameter:

```python
def get_execution_provider(
    mode: str,
    *,
    tenderly_api_key: str = "",
    tenderly_account: str = "",
    tenderly_project: str = "",
    chain_id: int = 1,
    block_number: int | None = None,
) -> TenderlyExecutionProvider | BenchmarkFillProvider:
```

| `mode` value             | Provider                    | Fallback                                                             |
| ------------------------ | --------------------------- | -------------------------------------------------------------------- |
| `"fork"` or `"tenderly"` | `TenderlyExecutionProvider` | Falls back to `BenchmarkFillProvider` if `tenderly_api_key` is empty |
| anything else            | `BenchmarkFillProvider`     | N/A                                                                  |

## Pipeline Mode Behaviour

### Batch Mode

Fork at a historical block. The orchestrator calls `advance_time()` per candle interval to simulate time progression.
Smart contract state (Aave health factor, Uniswap pool prices, etc.) reflects the historical block but advances
deterministically.

```
1. get_execution_provider(mode="fork", block_number=19_500_000, ...)
2. provider.create_fork()        -- VNet pinned to block 19500000
3. provider.fund_wallet(...)     -- seed test tokens
4. [per candle]:
     provider.advance_time(3600) -- advance 1 hour
     connector.execute(...)      -- real Aave/Uniswap calls on fork
5. provider.cleanup()            -- delete VNet
```

### Paper Mode

Fork at the latest block. No time advancement -- transactions execute against current on-chain state in real time. Same
code path as live, but gas costs are zero and state is isolated.

```
1. get_execution_provider(mode="fork", block_number=None, ...)
2. provider.create_fork()        -- VNet at latest block
3. provider.fund_wallet(...)     -- seed capital
4. [on signal]:
     connector.execute(...)      -- real smart contract calls on fork
5. provider.cleanup()            -- delete VNet on shutdown
```

### Live Mode

No fork. DeFi connectors receive the real chain RPC URL from `CHAIN_RPC_TEMPLATES` in UAC. The execution provider is not
used for live mode -- connectors talk directly to Alchemy RPCs (+ Helius for Solana). Custody routing: **May-23 cutover
default = CLOUD_KMS_ENCRYPTED (CloudKmsCustodyProvider)** per
[`interface-credential-convention.md`](interface-credential-convention.md) 2026-05-12 refresh. **June-1 flip targets** =
Copper MPC / CEFFU MirrorX / Fireblocks per client cred availability. Cross-ref:
[`plans/archive/issues/venue_chain_custody_routing_matrix_2026_05_12.md`](../../plans/archive/issues/venue_chain_custody_routing_matrix_2026_05_12.md).

## Tenderly VNet API

The provider uses the VNet API (`/vnets`), not the deprecated Fork API.

### Create VNet

```
POST https://api.tenderly.co/api/v1/account/{account}/project/{project}/vnets
Headers:
  X-Access-Key: {api_key}
  Content-Type: application/json

Body:
{
  "slug": "exec-provider-{chain_id}-{timestamp}",
  "display_name": "Execution Provider Chain {chain_id} {timestamp}",
  "fork_config": {
    "network_id": {chain_id},
    "block_number": {block_number | "latest"}
  },
  "virtual_network_config": {
    "chain_config": {"chain_id": {chain_id}}
  },
  "sync_state_config": {"enabled": false}
}
```

Response includes an `rpcs` array. The provider extracts:

- Admin RPC (name contains "admin") -- for `tenderly_setBalance`, `tenderly_setErc20Balance`
- Public RPC -- for standard `eth_call`, `eth_sendTransaction`

### Fund Wallet

Uses custom Tenderly RPC methods on the admin endpoint:

| Token type                          | RPC method                 | Params                                        |
| ----------------------------------- | -------------------------- | --------------------------------------------- |
| Native ETH                          | `tenderly_setBalance`      | `[[address], hex_amount_wei]`                 |
| ERC20 (USDC, USDT, DAI, WETH, WBTC) | `tenderly_setErc20Balance` | `[token_address, wallet_address, hex_amount]` |

Token addresses and decimals are hardcoded in `tenderly.py`:

- USDC/USDT: 6 decimals
- DAI/WETH/WBTC and all others: 18 decimals

### Advance Time

Two sequential RPC calls:

1. `evm_increaseTime` with hex-encoded seconds
2. `evm_mine` to apply the time change to the next block

### Snapshot and Revert

For state rollback during batch replay:

- `evm_snapshot` -- returns a snapshot ID
- `evm_revert` with the snapshot ID -- rolls back all state changes

### Delete VNet

```
DELETE https://api.tenderly.co/api/v1/account/{account}/project/{project}/vnets/{fork_id}
Headers:
  X-Access-Key: {api_key}
```

Called by `cleanup()`. Logs `TENDERLY_FORK_DELETED` event on success.

## Configuration

Credentials are fetched from Secret Manager at runtime (per the interface credential convention):

| Secret                  | Description                        |
| ----------------------- | ---------------------------------- |
| `tenderly-api-key`      | API key for VNet creation/deletion |
| `tenderly-account-slug` | Account slug (e.g. `anneki90`)     |
| `tenderly-project-slug` | Project slug (e.g. `project`)      |

The factory receives these as keyword arguments -- the calling service is responsible for Secret Manager lookup.

## Events

| Event                   | When                                                                 |
| ----------------------- | -------------------------------------------------------------------- |
| `TENDERLY_FORK_CREATED` | VNet created successfully (includes fork_id, chain_id, block_number) |
| `TENDERLY_FORK_DELETED` | VNet deleted successfully (includes fork_id)                         |

## Downstream consumers

Beyond live-trade execution, Tenderly forks back simulation use-cases that NEED a fork-state mutator + state-reader
combo:

- **Governance proposal simulation** (`defi_simulation_realism_2026_05_10` Phase 4B / codex
  [`amm-slippage-simulation.md`](amm-slippage-simulation.md) § "Governance proposal simulation harness"): apply
  `governor.execute(proposalId)` on a fork pinned at the proposal-execution block; read affected protocol params
  before + after; output per-asset parameter delta. Budget ~10 sims/day per `defi_simulation_realism_2026_05_10.md` Risk
  register. Caller: `execution-service/execution_service/governance/proposal_simulator.py` (Phase 4B NEW).
- **AMM matching-engine fidelity validation** (`defi_simulation_realism_2026_05_10` Phase 2 + Phase 8C / codex
  [`amm-slippage-simulation.md`](amm-slippage-simulation.md) § "Golden test set harness"): replay historical swaps
  against Tenderly fork pinned at swap block; compare matcher-computed fill vs on-chain `Swap` event. Per-shape
  validation thresholds (≥ 100 V3 swaps within 5 bps; ≥ 50 Curve; ≥ 20 Balancer + Velodrome + Aerodrome; etc.). Caller:
  `execution-service/tests/defi_execution/integration/test_amm_golden_swaps.py` (Phase 3C NEW; conftest path corrected
  2026-05-12 per TS-12 audit — Tenderly fork fixtures live in
  `execution-service/tests/defi_execution/integration/conftest.py`, not the legacy `tests/integration/conftest.py`).
- **High-impact swap pre-flight check** (`defi_simulation_realism_2026_05_10` Phase 4 implementation — Harsh slot 4
  scope): for live swaps where size > N% of pool TVL, run a pre-flight `.quote()` against Tenderly fork of upstream RPC
  state before broadcasting tx — protects against pool-state drift between strategy decision and tx inclusion.

## References

- [Execution Modes and Chain Resolution](execution-modes-and-chain-resolution.md) -- CHAIN_ENV config
- [DeFi Execution Overview](defi-execution-overview.md) -- pipeline flow
- [Interface Credential Convention](interface-credential-convention.md) -- how services get API keys
- [Custody Providers](custody-providers.md) -- transaction signing layer
- [Flash Loan Receiver](flash-loan-receiver.md) -- Aave flash loans on forks
- [AMM Slippage Simulation](amm-slippage-simulation.md) -- governance sim harness + matching-engine fidelity validation
  downstream consumers
- [Concentrated Liquidity](concentrated-liquidity.md) -- tick-math reference for V3/V4 fork-state interpretation
