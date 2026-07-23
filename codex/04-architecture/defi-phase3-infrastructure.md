---
doc_type: codex-ssot
title: DeFi Phase 3 Infrastructure
summary:
  DeFi paper-to-live infra pillars — CHAIN_ENV chain switch, unified gas-cost schema (DeFiFillRecord), Tenderly-fork
  paper execution, and CustodyProvider treasury/trading wallet abstraction.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    execution-service,
    features-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: [defi, execution, infrastructure, custody, tenderly, gas]
related:
  [
    /codex/04-architecture/tenderly-execution-provider.md,
    /codex/04-architecture/flash-loan-receiver.md,
    /codex/04-architecture/custody-providers.md,
    /codex/04-architecture/chain-environment-resolution.md,
    /codex/04-architecture/wallet-hierarchy-and-capital-flow.md,
  ]
created: 2026-04-03
authoritative_for: [DeFi Phase 3 paper-to-live infrastructure pillars]
referenced_by: [/codex/04-architecture/defi-risk-monitoring.md, /codex/04-architecture/flash-loan-receiver.md]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# DeFi Phase 3 Infrastructure

## Overview

Phase 3 covers the infrastructure additions required to take DeFi strategies from paper/batch mode to live production.
The four main pillars are:

1. **CHAIN_ENV config switch** — deterministic chain selection (testnet/mainnet/fork) by env
2. **Gas schema alignment** — unified gas cost representation across all modes
3. **Tenderly fork integration** — pre-simulation and paper execution on a live mainnet fork
4. **Custody provider abstraction** — treasury and trading wallet hierarchy with custodian backend

## 1. CHAIN_ENV Config Switch

**Problem**: Services hard-coded `chain_id=1` (Ethereum mainnet). Switching to testnet or a Tenderly fork required
environment variable hacks.

**Solution**: `CHAIN_ENV` config field resolved at startup via `UnifiedCloudConfig`. SSOT:
`unified_api_contracts/registry/capability_declarations/_defi.py`

```python
CHAIN_RPC_TEMPLATES: dict[str, dict[str, str]] = {
    "ETHEREUM": {
        "mainnet": "https://eth-mainnet.g.alchemy.com/v2/{api_key}",
        "testnet": "https://eth-sepolia.g.alchemy.com/v2/{api_key}",
        "fork":    "https://virtual.mainnet.rpc.tenderly.co/{fork_id}",
    },
    "ARBITRUM": {
        "mainnet": "https://arb-mainnet.g.alchemy.com/v2/{api_key}",
        "testnet": "https://arb-sepolia.g.alchemy.com/v2/{api_key}",
        "fork":    "https://virtual.arbitrum.rpc.tenderly.co/{fork_id}",
    },
    ...
}
```

Resolution order:

1. `execution_service/config/chain_config.yaml` — `chain_env: mainnet`
2. Override via `CHAIN_ENV` environment variable
3. Tenderly fork connector overrides to `fork` automatically in paper mode

Connector usage:

```python
rpc_url = resolve_rpc_url(chain="ETHEREUM", env=chain_env, api_key=api_key)
connector.connect(config={"rpc_url": rpc_url, "wallet_private_key": pk})
```

## 2. Gas Schema Alignment

All DeFi fills include gas cost information for accurate P&L attribution. The canonical schema is
`unified_api_contracts.internal.fills.DeFiFillRecord`:

```python
@dataclass
class DeFiFillRecord:
    instruction_id: str
    tx_hash: str
    gas_used: int               # actual gas units consumed
    gas_price_wei: int          # actual gas price (wei)
    gas_cost_eth: Decimal       # gas_used × gas_price_wei / 1e18
    gas_cost_usd: Decimal       # gas_cost_eth × eth_price_usd
    block_number: int
    chain_id: int
    ...
```

**Paper mode**: Gas is simulated using Tenderly fork `eth_estimateGas` + `eth_gasPrice`. Values are close to mainnet but
not identical (fork state may differ from live state).

**Batch mode**: Gas costs are loaded from the historical fill record if the batch is a replay, or estimated from the
`GasPriceAdapter` using historical gas data from `eth_feeHistory`.

**Live mode**: Gas is the actual on-chain value from the transaction receipt.

### Gas Cost Estimation (Batch/Paper)

```python
from execution_service.defi_execution.gas_price_adapter import GasPriceAdapter

adapter = GasPriceAdapter(rpc_url=rpc_url)
estimate = adapter.estimate_gas_cost(
    tx_params=tx_params,
    eth_price_usd=eth_price,
)
# Returns: GasCostEstimate(gas_units=210000, gas_price_gwei=30, cost_usd=18.50)
```

## 3. Tenderly Fork Integration

Tenderly virtual testnets provide a live-state Ethereum fork for:

- Pre-flight simulation before mainnet submission
- Paper trading execution (real contract state, no real money)
- Integration tests (funded wallet, deployed contracts)

### Architecture

```
Tenderly Dashboard → fork_id stored in UAC config/testnet_contracts.yaml
    │
    ▼
execution_service/defi_execution/protocols/tenderly_fork.py
    │  TenderlyForkConnector.connect(fork_id=fork_id)
    │  simulate_transaction(tx_params) → SimulationResult
    │  execute_transaction(tx_params) → DeFiTxResult (paper mode)
    ▼
AaveConnector / UniswapConnector / EigenLayerConnector
    │  Use TenderlyForkConnector as the underlying Web3 provider
    │  in paper mode (EXECUTION_MODE=paper)
```

### Fork Fixtures (Integration Tests)

```python
# execution-service/tests/integration/conftest.py
@pytest.fixture(scope="session")
def tenderly_fork(request) -> TenderlyFork:
    """Session-scoped Tenderly fork. Skipped if SM credentials unavailable."""
    ...

@pytest.fixture
def funded_wallet(tenderly_fork) -> str:
    """Returns a funded wallet address on the fork."""
    tenderly_fork.fund_wallet(address=TEST_WALLET, eth_amount=100)
    return TEST_WALLET
```

Tests marked `@pytest.mark.allow_network` — skipped in CI without credentials.

### Paper vs Live Mode

| Aspect  | Paper                 | Live               |
| ------- | --------------------- | ------------------ |
| RPC     | Tenderly fork URL     | Alchemy mainnet    |
| Gas     | Fork `estimateGas`    | Actual receipt     |
| Tx Hash | Simulation hash       | Real on-chain hash |
| Funds   | Fork state            | Real wallet        |
| Fills   | `paper_fill_*` prefix | Real tx hash       |

## 4. Custody Provider Abstraction

### Wallet Hierarchy

```
Treasury Wallet (client deposits)
    │  Receives: client fund inflows
    │  Controlled by: CustodyProvider (Copper default)
    │  Allocation: 20% → DeFi trading wallet, 80% retained
    ▼
Trading Wallet (per-strategy, per-chain)
    │  e.g. trading_wallet_defi_ethereum_staked_basis
    │  Controlled by: execution-service (private key in Secret Manager)
    │  Monitored by: TreasuryMonitor
```

### CustodyProvider Interface

`execution_service/defi_execution/custody/custody_provider.py`:

```python
class CustodyProvider(Protocol):
    def get_wallet_address(self, wallet_id: str) -> str: ...
    def sign_transaction(self, wallet_id: str, tx: dict) -> str: ...
    def get_balance(self, wallet_id: str, token: str) -> Decimal: ...
```

Implementations:

- `MockCustodyProvider` — for tests/paper mode (in-memory)
- `CopperCustodyProvider` — Copper.co MPC custody (production)
- Factory: `create_custody_provider(mode=chain_env)` — returns Mock in non-mainnet modes

### TreasuryMonitor

`position_balance_monitor_service/core/treasury_monitor.py` tracks the treasury wallet balance across chains and emits
alerts when:

- Treasury balance drops below `min_treasury_balance_eth` (default 5 ETH)
- Trading wallet balance drops below `min_trading_balance_eth` (default 0.5 ETH)
- Pending withdrawals exceed `max_pending_withdrawal_pct` (default 20%)

## Deployment Topology (DeFi Services)

```
Tier 1 (always on):
    instruments-service     — instrument definitions
    market-tick-data-service — MTDS tick data

Tier 2 (data pipeline):
    market-data-processing-service — MDPS candles
    features-service (onchain family)       — on-chain features

Tier 3 (strategy + execution):
    strategy-service          — signal generation
    execution-service         — on-chain execution
    position-balance-monitor  — position tracking
    pnl-attribution-service   — P&L
    risk-and-exposure-service — risk limits
```

For local development, all tiers run via mock mode with no credentials:

```bash
bash unified-trading-pm/scripts/demo-mode.sh --seed
```

## Key Files

| File                                                              | Purpose                                |
| ----------------------------------------------------------------- | -------------------------------------- |
| `unified_api_contracts/registry/capability_declarations/_defi.py` | `CHAIN_RPC_TEMPLATES` SSOT             |
| `execution_service/defi_execution/gas_price_adapter.py`           | Gas price estimation                   |
| `execution_service/defi_execution/protocols/tenderly_fork.py`     | Tenderly fork connector                |
| `execution_service/defi_execution/custody/custody_provider.py`    | Custody provider interface             |
| `position_balance_monitor_service/core/treasury_monitor.py`       | Treasury balance monitoring            |
| `unified_api_contracts/config/testnet_contracts.yaml`             | Fork IDs + deployed contract addresses |

## Related Docs

- `/codex/04-architecture/tenderly-execution-provider.md` — Tenderly deep-dive
- `/codex/04-architecture/flash-loan-receiver.md` — Flash loan contract deployment
- `/codex/04-architecture/custody-providers.md` — Copper / CEFFU / LocalKey / Mock custody providers (single SSOT)
- `/codex/04-architecture/chain-environment-resolution.md` — CHAIN_ENV resolution
- `/codex/04-architecture/wallet-hierarchy-and-capital-flow.md` — Treasury wallet structure
