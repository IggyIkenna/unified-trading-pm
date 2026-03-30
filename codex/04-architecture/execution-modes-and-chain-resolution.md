# Execution Modes & Chain Resolution

## Overview

The system operates in three modes: **batch** (historical backtest), **paper** (testnet simulation), and **live** (real
trading). The principle is **batch = live** — same service architecture, same code paths, different execution backends.
Paper mode bridges the gap by executing real smart contract calls on chain forks.

## Mode Matrix

| Aspect                | Batch                                   | Paper (Testnet)             | Live                         |
| --------------------- | --------------------------------------- | --------------------------- | ---------------------------- |
| **Config flag**       | `--mode batch`                          | `--mode paper`              | `--mode live`                |
| **RPC target**        | Tenderly fork (historical block)        | Tenderly fork (live block)  | Mainnet                      |
| **Smart contracts**   | Called on fork (same code path as live) | Called on fork (real-time)  | Called on mainnet            |
| **Execution**         | Real connectors → fork                  | Real connectors → fork      | Real connectors → mainnet    |
| **Signing**           | MockCustody (fork doesn't verify)       | MockCustody or sandbox      | Copper MPC                   |
| **Gas costs**         | Real from fork tx receipt               | Real from fork tx receipt   | Real from mainnet tx receipt |
| **Fill prices**       | Real execution price (fork)             | Real execution price (fork) | Real execution price         |
| **Data source**       | GCS (pre-downloaded features)           | Live feeds (real-time)      | Live feeds (real-time)       |
| **Position tracking** | GCS state files                         | GCS + on-chain (fork)       | On-chain + GCS               |
| **Speed**             | Fast (replay rate)                      | Real-time                   | Real-time                    |

**Lightweight fallback (batch only):** `BENCHMARK_FILL` skips contract calls for quick iteration. Not the production
batch path — use fork execution for production-grade backtesting.

## Strategy → Instruments → Chains Flow

### 1. Strategy Config Declares Intent (NOT Specific Instrument IDs)

Strategy config declares what it WANTS (base currencies, protocol, chain). Instruments-service resolves to specific IDs
based on what exists on each date.

```json
{
  "strategy_id": "DEFI_ETH_BASIS_MULTI_HUF_1H_V1",
  "chain": "ETHEREUM",
  "protocol": "HYBRID",
  "base_currencies": ["ETH"],
  "lending_basket": ["USDC", "USDT", "DAI"],
  "basis_coins": ["ETH", "BTC", "SOL", "AVAX"],
  "allowed_venues": ["UNISWAPV3-ETHEREUM", "CURVE-ETHEREUM"],
  "perp_venues": ["HYPERLIQUID", "BINANCE-FUTURES", "OKX", "BYBIT", "ASTER"]
}
```

The strategy config (GCS JSON) declares:

- **Which instruments** to trade (fixed list or dynamically selected from features)
- **Which chain** to operate on
- **Which venues** are allowed for SOR

Instruments-service resolves this intent to specific IDs:

```
AAVEV3-ETHEREUM:A_TOKEN:AUSDC@ETHEREUM
AAVEV3-ETHEREUM:A_TOKEN:AUSDT@ETHEREUM
HYPERLIQUID:PERPETUAL:ETH-USDC@LIN@HYPERLIQUID
BINANCE-FUTURES:PERPETUAL:ETHUSDT@LIN@BINANCE-FUTURES
```

The strategy never hardcodes instrument IDs. If instruments-service can't resolve what the strategy expects, that's an
error — not a silent skip.

### 2. Instruments-Service Discovers What Exists

```
instruments-service --operation instruments --category DEFI --start-date 2026-03-01
  └── Per venue adapter:
      ├── Uniswap V3 subgraph → pools with BOTH sides major, $100k TVL
      ├── Aave V3 subgraph → lending markets for major assets
      ├── Orca REST API → Solana pools, BOTH sides major, $10k TVL
      └── Writes to GCS: instruments-store/by_date/day={date}/instruments.parquet
```

### 3. Strategy Reads Features (Not Instruments Directly)

In batch: strategy reads pre-computed features from GCS (features-onchain-service output). In live: strategy subscribes
to feature events via Pub/Sub.

The strategy doesn't query instruments-service at runtime — it relies on the pipeline having already run instruments →
MTDS → MDPS → features before strategy evaluation.

### 4. Chain Resolution

```python
# In execution-service, when processing a DeFi instruction:
chain_id = CHAIN_NAME_TO_ID[instruction.chain]  # "ETHEREUM" → 1
api_key = get_secret("alchemy-api-key")
rpc_url = CHAIN_RPC_TEMPLATES[chain_id].format(api_key=api_key)
# → https://eth-mainnet.g.alchemy.com/v2/{key}
```

For testnet, the chain ID maps to a different endpoint:

```python
# Same code path, different chain_id from config:
chain_id = 11155111  # Sepolia (from CHAIN_ENV=testnet config)
rpc_url = CHAIN_RPC_TEMPLATES[chain_id].format(api_key=api_key)
# → https://eth-sepolia.g.alchemy.com/v2/{key}
```

## Strategy vs Execution Decision Boundary

Two layers of routing. Strategy handles slow-moving yield/rate decisions. Execution handles fast-moving price/gas
decisions.

| Decision                      | Owner         | Why                             | Example                               |
| ----------------------------- | ------------- | ------------------------------- | ------------------------------------- |
| Which chains to deploy on     | **Strategy**  | Yield comparison is slow-moving | "Arbitrum AAVE has 5% vs Ethereum 3%" |
| Which venues for perp leg     | **Strategy**  | Funding rates are slow-moving   | "Hyperliquid funding > Binance"       |
| Which lending token           | **Strategy**  | APY comparison, slow-moving     | "USDC 4.8% vs USDT 4.2%"              |
| Staking vs lending vs basis   | **Strategy**  | Capital allocation, slow-moving | "Recursive 20% APY > lending 4%"      |
| Treasury ↔ trading transfers | **Strategy**  | Threshold-based, slow           | "Treasury at 8%, need to rebalance"   |
| Which DEX for a SWAP          | **Execution** | Price + slippage, fast-moving   | SOR picks Uniswap vs Curve            |
| Gas price bidding             | **Execution** | Block-by-block, fast-moving     | Priority fee estimation               |
| Bridge protocol selection     | **Execution** | Cost + speed, medium-moving     | Across vs Socket vs LayerZero         |
| Multi-leg coordination        | **Execution** | Atomic sequencing               | Flash borrow → swap → lend → repay    |
| Slippage optimization         | **Execution** | Orderbook depth, fast-moving    | Split across pools                    |

**Rule of thumb:** If it's about yields/rates → strategy emits the intent. If it's about price execution → execution
resolves the specifics.

Strategy emits: `SWAP(ETH, amount=100, allowed_venues=[Uniswap, Curve, Balancer])` Execution resolves: "Uniswap V3
ETH/USDC 0.3% pool has best depth, splitting 60/40"

### Dynamic Instrument Subscription

Strategies subscribe to instrument updates via hot reload:

1. instruments-service writes new instruments to GCS per date
2. Config reloader detects new instruments matching strategy's intent
3. Strategy re-evaluates: new pool with better yield? → rebalance
4. Expiring instruments (futures) → strategy closes position before expiry

This is critical for:

- **Futures/options**: expire, new ones listed
- **New pool launches**: better yield opportunity
- **Protocol migrations**: Aave V3 → V4, Uniswap V3 → V4
- **Chain expansions**: new L2 deployed, Aave launches on new chain

## Key & Endpoint Resolution

### Secret Manager (Single Source for All Modes)

| Secret                   | Used By                          | Modes                               |
| ------------------------ | -------------------------------- | ----------------------------------- |
| `alchemy-api-key`        | All chain RPC calls              | All (same key, different endpoints) |
| `tardis-api-key`         | CeFi historical data             | Batch only                          |
| `thegraph-api-key`       | DeFi subgraph queries            | All                                 |
| `copper-api-key`         | Transaction signing (production) | Live only                           |
| `copper-sandbox-api-key` | Transaction signing (test)       | Paper only                          |

### RPC Endpoint Resolution

All RPC URLs are templates in UAC SSOT:

**EVM** (`CHAIN_RPC_TEMPLATES`): keyed by chain ID (int)

- 30 entries: 20 mainnets + 10 testnets
- Same `{api_key}` placeholder, same Alchemy key

**Solana** (`SOLANA_RPC_TEMPLATES`): keyed by provider name (str)

- Mainnet: `alchemy`, `helius`
- Devnet: `alchemy_devnet`, `helius_devnet`, `public_devnet`

**Bitcoin**: hardcoded in gas_fee_handler

- `https://bitcoin-mainnet.g.alchemy.com/v2/{api_key}`

### Mode-Specific Config

```bash
# Batch (local-batch.env):
CLOUD_PROVIDER=gcp
CLOUD_MOCK_MODE=false
CUSTODY_PROVIDER=mock        # No real signing in batch

# Paper (local-paper.env — TO BE CREATED):
CLOUD_PROVIDER=gcp
CLOUD_MOCK_MODE=false
CHAIN_ENV=testnet            # Use testnet chain IDs
CUSTODY_PROVIDER=mock        # Or copper-sandbox
TENDERLY_FORK=true           # Fork mainnet for execution

# Live (production):
CLOUD_PROVIDER=gcp
CLOUD_MOCK_MODE=false
CHAIN_ENV=mainnet
CUSTODY_PROVIDER=copper      # Real MPC signing
```

## Smart Contract & Atomic Transaction Handling

### Pipeline Stage: execution-service (L6b)

```
Strategy emits StrategyInstruction[]
  │
  ▼
execution-service InstructionRouter
  ├── is_atomic=True? → Execute all-or-nothing
  │     ├── FLASH_BORROW → FlashLoanHandler (Morpho/AAVE)
  │     ├── SWAP → SwapHandler (Uniswap/Curve via SOR)
  │     ├── LEND → LendHandler (Aave supply)
  │     ├── BORROW → BorrowHandler (Aave borrow)
  │     ├── FLASH_REPAY → FlashLoanHandler
  │     ├── TRANSFER → TransferHandler (wallet → venue)
  │     └── TRADE → TradeHandler (CeFi perp API)
  │
  └── is_atomic=False? → Execute sequentially
```

### Per-Mode Execution Backend

| Mode      | Backend                                  | Smart Contracts                                                 | Gas                          |
| --------- | ---------------------------------------- | --------------------------------------------------------------- | ---------------------------- |
| **Batch** | `non_trade_processor.py`                 | NOT called. Returns BENCHMARK_FILL at oracle price.             | Historical from GCS          |
| **Paper** | `TenderlyExecutionProvider` (to build)   | Called on Tenderly fork. Real contract interaction, fake chain. | Real from fork tx receipt    |
| **Live**  | `LiveExecutionProvider` + Copper signing | Called on mainnet. Real everything.                             | Real from mainnet tx receipt |

### Tenderly Integration

**Current state:** Integration test fixtures only.

```python
# execution-service/tests/integration/conftest.py
@pytest.fixture(scope="session")
def tenderly_fork():
    """Create a Tenderly mainnet fork for integration testing."""
    # Creates fork at latest block
    # Returns fork RPC URL

@pytest.fixture
def funded_wallet(tenderly_fork):
    """Fund a test wallet with ETH + tokens on the fork."""

@pytest.fixture
def aave_connector(tenderly_fork, funded_wallet):
    """AaveConnector connected to fork with funded wallet."""
```

**What needs building for paper trading:**

1. `TenderlyExecutionProvider` — productionized version of test fixtures
2. Fork management: create fork per day/hour, advance block time
3. Config switch: `TENDERLY_FORK=true` in env
4. Fork RPC URL injected into execution-service instead of mainnet RPC

### Code Path Alignment (Batch = Live)

| Component                  | Batch Code Path                   | Live Code Path                | Same?                                |
| -------------------------- | --------------------------------- | ----------------------------- | ------------------------------------ |
| Strategy signal generation | `generate_signal()`               | `generate_signal()`           | Yes                                  |
| Instruction emission       | `_collect_instructions()`         | `_collect_instructions()`     | Yes                                  |
| Instruction serialization  | Parquet to GCS                    | Pub/Sub event                 | **Different transport, same schema** |
| Execution routing          | `InstructionRouter`               | `InstructionRouter`           | Yes                                  |
| DeFi domain detection      | `if domain == "defi"`             | `if domain == "defi"`         | Yes                                  |
| Fill generation            | `non_trade_processor` (simulated) | Real connector (Aave/Uniswap) | **Different backend**                |
| Fill schema                | `FILLS_SCHEMA`                    | `FILLS_SCHEMA`                | Yes                                  |
| P&L computation            | `compute_pnl_breakdown()`         | `compute_pnl_breakdown()`     | Yes                                  |
| Risk computation           | `compute_health_factor()`         | `compute_health_factor()`     | Yes                                  |
| Position tracking          | GCS state                         | GCS + on-chain                | **GCS is common**                    |

The key insight: **strategy and analytics code is 100% shared**. Only the execution backend differs. This is by design —
the execution provider is pluggable.

## What Exists vs What Needs Building

### Data & Instruments Layer

| Component                                      | Status                                              |
| ---------------------------------------------- | --------------------------------------------------- |
| Instruments-service discovery (all chains)     | **Working** — 48 venues, EVM + Solana               |
| Instrument filtering (BOTH sides major + TVL)  | **Working** — consistent across all DEX adapters    |
| Solana creation timestamps (`available_since`) | **Working** — via Alchemy `getSignaturesForAddress` |
| Gas fee collection (12 EVM + Solana + BTC)     | **Working** — all chains via Alchemy                |
| All-chain RPC endpoints (mainnet + testnet)    | **Working** — 30 EVM + Solana in templates          |

### Strategy Layer

| Component                                    | Status                                                                   |
| -------------------------------------------- | ------------------------------------------------------------------------ |
| Strategy declares intent (not hardcoded IDs) | **Partially** — config has intent fields, resolution needs wiring        |
| Dynamic instrument subscription (hot reload) | **Needs building** — config_reloaders exist but not wired to instruments |
| Strategy ↔ execution decision boundary      | **Implemented in code** — SOR in execution, yields in strategy           |

### Execution Layer

| Component                                          | Status                                                 |
| -------------------------------------------------- | ------------------------------------------------------ |
| InstructionRouter (all DeFi operations)            | **Working** — LEND/BORROW/SWAP/TRADE/FLASH/TRANSFER    |
| BENCHMARK_FILL (lightweight batch)                 | **Working** — quick iteration mode                     |
| Tenderly fork fixtures (integration tests)         | **Exists** — aave_connector, uniswap_connector         |
| TenderlyExecutionProvider (production batch/paper) | **Needs building** — productionize test fixtures       |
| Copper MPC signing (live)                          | **Interface built** — CustodyProvider + mock + factory |
| Live execution monitoring (confirmation, retry)    | **Needs building**                                     |

### Pipeline Scripts

| Pipeline                                      | Status                        |
| --------------------------------------------- | ----------------------------- |
| `run-batch-pipeline.sh` (historical replay)   | **Working** — running now     |
| `run-paper-pipeline.sh` (real-time on fork)   | **Needs building**            |
| `run-live-pipeline.sh` (real-time on mainnet) | **Exists** — needs validation |

### Config Layer

| Component                                      | Status             |
| ---------------------------------------------- | ------------------ |
| `CHAIN_ENV` switch (mainnet/testnet chain IDs) | **Needs building** |
| Custodian wallet mapping (real vs testnet)     | **Needs building** |
| `local-paper.env` config                       | **Needs building** |

## References

- [Wallet Hierarchy](wallet-hierarchy-and-capital-flow.md) — treasury/trading wallet model
- [Copper Custody](copper-custody-integration.md) — MPC signing integration
- [Pipeline Layers](pipeline-service-layers.md) — L1-L7 service architecture
- [DeFi Execution](../../.claude/CLAUDE.md) — DeFi pipeline flow section
