---
scope: [engineer, admin]
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
used for live mode -- connectors talk directly to Alchemy/Infura RPCs. Custody provider (Copper) handles transaction
signing.

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

## References

- [Execution Modes and Chain Resolution](execution-modes-and-chain-resolution.md) -- CHAIN_ENV config
- [DeFi Execution Overview](defi-execution-overview.md) -- pipeline flow
- [Interface Credential Convention](interface-credential-convention.md) -- how services get API keys
- [Custody Providers](custody-providers.md) -- transaction signing layer
- [Flash Loan Receiver](flash-loan-receiver.md) -- Aave flash loans on forks
