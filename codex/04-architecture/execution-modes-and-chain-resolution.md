---
doc_type: codex-ssot
title: Execution Modes & Chain Resolution
summary:
  Batch/paper/live execution-mode matrix (batch=live principle, Tenderly-fork paper), strategy→instruments→chain intent
  resolution, CHAIN_ENV chain-id/RPC lookup (21 chains), and the strategy-vs-execution decision boundary.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [e2e-testing, execution-service, features-service, instruments-service, strategy-service]
scope: [engineer, admin]
tags: [defi, execution, strategy, tenderly, mvp, live-trading]
related:
  [
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/chain-environment-resolution.md,
    /codex/04-architecture/tenderly-execution-provider.md,
    /codex/04-architecture/custody-providers.md,
    /codex/04-architecture/wallet-hierarchy-and-capital-flow.md,
  ]
created: 2026-03-30
authoritative_for: [three execution modes (batch/paper/live) matrix, strategy-vs-execution decision boundary]
referenced_by:
  [
    /codex/04-architecture/chain-environment-resolution.md,
    /codex/04-architecture/flash-loan-receiver.md,
    /codex/04-architecture/mev-protection.md,
    /codex/04-architecture/tenderly-execution-provider.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Execution Modes & Chain Resolution

## Overview

The system operates in three modes: **batch** (historical backtest), **paper** (testnet simulation), and **live** (real
trading). The principle is **batch = live** — same service architecture, same code paths, different execution backends.
Paper mode bridges the gap by executing real smart contract calls on chain forks.

## Mode Matrix

| Aspect                | Batch                                   | Paper (Testnet)             | Live                                                                                                         |
| --------------------- | --------------------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Config flag**       | `--mode batch`                          | `--mode paper`              | `--mode live`                                                                                                |
| **RPC target**        | Tenderly fork (historical block)        | Tenderly fork (live block)  | Mainnet                                                                                                      |
| **Smart contracts**   | Called on fork (same code path as live) | Called on fork (real-time)  | Called on mainnet                                                                                            |
| **Execution**         | Real connectors → fork                  | Real connectors → fork      | Real connectors → mainnet                                                                                    |
| **Signing**           | MockCustody (fork doesn't verify)       | MockCustody or sandbox      | CLOUD_KMS_ENCRYPTED (May-23 cutover default) → Copper MPC / CEFFU MirrorX / Fireblocks (June-1 flip targets) |
| **Gas costs**         | Real from fork tx receipt               | Real from fork tx receipt   | Real from mainnet tx receipt                                                                                 |
| **Fill prices**       | Real execution price (fork)             | Real execution price (fork) | Real execution price                                                                                         |
| **Data source**       | GCS (pre-downloaded features)           | Live feeds (real-time)      | Live feeds (real-time)                                                                                       |
| **Position tracking** | GCS state files                         | GCS + on-chain (fork)       | On-chain + GCS                                                                                               |
| **Speed**             | Fast (replay rate)                      | Real-time                   | Real-time                                                                                                    |

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
  "allowed_venues": ["UNISWAP_V3-ETHEREUM", "CURVE-ETHEREUM"],
  "perp_venues": ["HYPERLIQUID", "BINANCE-FUTURES", "OKX", "BYBIT", "DERIBIT", "ASTER"]
}
```

> **6-perp-venue master-plan parity (codex audit EX-11 2026-05-12)**: CLAUDE.md § "Master Plan" + the master-plan
> readiness checklist name Bybit, Deribit, Binance, OKX, Hyperliquid, Aster as the **6 perp venues** for hedge legs.
> DERIBIT added to the example above 2026-05-12 — earlier 5-venue list omitted Deribit. Operators wiring `perp_venues`
> lists in strategy configs MUST include all 6 unless explicitly scoped down.

The strategy config (GCS JSON) declares:

- **Which instruments** to trade (fixed list or dynamically selected from features)
- **Which chain** to operate on
- **Which venues** are allowed for SOR

Instruments-service resolves this intent to specific IDs:

```
AAVE_V3-ETHEREUM:A_TOKEN:AUSDC@ETHEREUM
AAVE_V3-ETHEREUM:A_TOKEN:AUSDT@ETHEREUM
HYPERLIQUID:PERPETUAL:ETH-USDC@LIN@HYPERLIQUID
BINANCE-FUTURES:PERPETUAL:ETHUSDT@LIN@BINANCE-FUTURES
```

The strategy never hardcodes instrument IDs. If instruments-service can't resolve what the strategy expects, that's an
error — not a silent skip.

### 2. Instruments-Service Discovers What Exists

```
instruments-service --operation instruments --asset-group DEFI --start-date 2026-03-01
  └── Per venue adapter:
      ├── Uniswap V3 subgraph → pools with BOTH sides major, $100k TVL
      ├── Aave V3 subgraph → lending markets for major assets
      ├── Orca REST API → Solana pools, BOTH sides major, $10k TVL
      └── Writes to GCS: instruments-store/by_date/day={date}/instruments.parquet
```

### 3. Strategy Reads Features (Not Instruments Directly)

In batch: strategy reads pre-computed features from GCS (features-service (onchain family) output). In live: strategy
subscribes to feature events via Pub/Sub.

The strategy doesn't query instruments-service at runtime — it relies on the pipeline having already run instruments →
MTDS → MDPS → features before strategy evaluation.

### 4. Chain Resolution (CHAIN_ENV)

Implemented in UAC `registry/chain_env.py`. The `CHAIN_ENV` environment variable (read via
`UnifiedCloudConfig.chain_env`) controls which chain IDs the system resolves to. Three values: `mainnet`, `testnet`,
`fork`.

```python
# UAC registry/chain_env.py — 21 chains mapped for both mainnet and testnet.
# Chain-count internal-consistency note (codex audit EX-12 2026-05-12): downstream sections cite
# "30 EVM + Solana in templates" (line 363 below) + "30 entries: 20 mainnets + 10 testnets" (line 250).
# All three are consistent: 21 chains × 2 envs = 42 chain-id slots in registry; 30 EVM RPC URL templates
# in CHAIN_RPC_TEMPLATES (mainnet+testnet); the registry-vs-RPC-templates split is intentional.
from unified_api_contracts.registry import resolve_chain_id, resolve_rpc_url

# Strategy says "ETHEREUM" — system resolves based on CHAIN_ENV:
chain_id = resolve_chain_id("ETHEREUM", env="mainnet")   # → 1
chain_id = resolve_chain_id("ETHEREUM", env="testnet")   # → 11155111 (Sepolia)
chain_id = resolve_chain_id("ETHEREUM", env="fork")      # → 1 (same as mainnet, different RPC)

# Full RPC URL resolution:
rpc_url = resolve_rpc_url("ETHEREUM", env="mainnet", alchemy_api_key=key)
# → https://eth-mainnet.g.alchemy.com/v2/{key}

rpc_url = resolve_rpc_url("ETHEREUM", env="testnet", alchemy_api_key=key)
# → https://eth-sepolia.g.alchemy.com/v2/{key}

rpc_url = resolve_rpc_url("ETHEREUM", env="fork")
# → "" (empty — caller provides Tenderly fork URL)
```

**Chain coverage** (21 chains in both `MAINNET_CHAIN_IDS` and `TESTNET_CHAIN_IDS`):

| Chain     | Mainnet ID  | Testnet ID  | Testnet Name     |
| --------- | ----------- | ----------- | ---------------- |
| ETHEREUM  | 1           | 11155111    | Sepolia          |
| ARBITRUM  | 42161       | 421614      | Arbitrum Sepolia |
| OPTIMISM  | 10          | 11155420    | Optimism Sepolia |
| BASE      | 8453        | 84532       | Base Sepolia     |
| POLYGON   | 137         | 80002       | Polygon Amoy     |
| AVALANCHE | 43114       | 43113       | Avalanche Fuji   |
| BSC       | 56          | 97          | BSC Testnet      |
| LINEA     | 59144       | 59141       | Linea Sepolia    |
| SCROLL    | 534352      | 534351      | Scroll Sepolia   |
| ZKSYNC    | 324         | 300         | zkSync Sepolia   |
| MANTLE    | 5000        | 5003        | Mantle Sepolia   |
| BLAST     | 81457       | 168587773   | Blast Sepolia    |
| MODE      | 34443       | 919         | Mode Testnet     |
| GNOSIS    | 100         | 10200       | Gnosis Chiado    |
| FANTOM    | 250         | 4002        | Fantom Testnet   |
| CELO      | 42220       | 44787       | Celo Alfajores   |
| AURORA    | 1313161554  | 1313161555  | Aurora Testnet   |
| METIS     | 1088        | 599         | Metis Goerli     |
| MOONBEAM  | 1284        | 1287        | Moonbase Alpha   |
| SOLANA    | 0 (non-EVM) | 0 (non-EVM) | Devnet           |
| BITCOIN   | 0 (non-EVM) | 0 (non-EVM) | Testnet          |

`FORK_CHAIN_IDS` is aliased to `MAINNET_CHAIN_IDS` — fork mode uses mainnet chain IDs but routes transactions to the
Tenderly fork RPC URL instead of mainnet.

**Consumers updated:** `bridge_cost_model.py`, `sor_cross_chain.py`, and `uniswap.py` in execution-service all import
`resolve_chain_id` from UAC instead of using hardcoded `CHAIN_NAME_TO_ID` mappings.

## Strategy vs Execution Decision Boundary

Two layers of routing. Strategy handles slow-moving yield/rate decisions. Execution handles fast-moving price/gas
decisions.

| Decision                     | Owner         | Why                             | Example                               |
| ---------------------------- | ------------- | ------------------------------- | ------------------------------------- |
| Which chains to deploy on    | **Strategy**  | Yield comparison is slow-moving | "Arbitrum AAVE has 5% vs Ethereum 3%" |
| Which venues for perp leg    | **Strategy**  | Funding rates are slow-moving   | "Hyperliquid funding > Binance"       |
| Which lending token          | **Strategy**  | APY comparison, slow-moving     | "USDC 4.8% vs USDT 4.2%"              |
| Staking vs lending vs basis  | **Strategy**  | Capital allocation, slow-moving | "Recursive 20% APY > lending 4%"      |
| Treasury ↔ trading transfers | **Strategy**  | Threshold-based, slow           | "Treasury at 8%, need to rebalance"   |
| Which DEX for a SWAP         | **Execution** | Price + slippage, fast-moving   | SOR picks Uniswap vs Curve            |
| Gas price bidding            | **Execution** | Block-by-block, fast-moving     | Priority fee estimation               |
| Bridge protocol selection    | **Execution** | Cost + speed, medium-moving     | Across vs Socket vs LayerZero         |
| Multi-leg coordination       | **Execution** | Atomic sequencing               | Flash borrow → swap → lend → repay    |
| Slippage optimization        | **Execution** | Orderbook depth, fast-moving    | Split across pools                    |

**Rule of thumb:** If it's about yields/rates → strategy emits the intent. If it's about price execution → execution
resolves the specifics.

Strategy emits: `SWAP(ETH, amount=100, allowed_venues=[Uniswap, Curve, Balancer])` Execution resolves: "Uniswap V3
ETH/USDC 0.3% pool has best depth, splitting 60/40"

### Dynamic Instrument Subscription

Implemented in `strategy_config_loader.py` (discovery + expiry filtering) and `colocated_engine.py` (date boundary
re-discovery with change detection).

**Batch flow:**

1. On each date boundary, `discover_instruments()` re-reads GCS `instrument_availability/by_date/`
2. `available_to_datetime` filtering excludes expired instruments (e.g., expired futures, delisted pools)
3. `detect_instrument_changes()` computes added/removed instruments vs previous date
4. Added instruments → `INSTRUMENTS_ADDED` event (strategy can evaluate new pool yields)
5. Removed instruments → `INSTRUMENTS_REMOVED` event (strategy should close positions)

**Live flow:**

1. `get_active_instruments()` from `config_reloaders.py` returns hot-reloaded `InstrumentDomainConfig`
2. `DomainConfigReloader` polls ConfigStore for changes (Pub/Sub-triggered)
3. On reload: `CONFIG_CHANGED` event emitted with updated instrument/venue counts

**Expiry handling:**

- `discover_instruments()` filters on `available_to_datetime >= query_date`
- Expired instruments are excluded from the returned list
- Strategy sees position in expired instrument → emits CLOSE/WITHDRAW instructions

This is critical for:

- **Futures/options**: expire, new ones listed
- **New pool launches**: better yield opportunity
- **Protocol migrations**: Aave V3 → V4, Uniswap V3 → V4
- **Chain expansions**: new L2 deployed, Aave launches on new chain

### Continuous Mode (Paper/Live)

The colocated engine supports `--continuous` mode for paper and live trading. Instead of generating a finite tick list
from GCS features, the engine runs an infinite loop generating ticks at `--tick-interval` (default: 3600s = 1 hour).

```bash
# Paper: continuous on Tenderly fork, hourly ticks
bash run-paper.sh --strategy AAVE_LENDING --continuous --tick-interval 3600

# Live: continuous on mainnet, 15-minute ticks
bash run-live.sh --strategy AAVE_LENDING --continuous --tick-interval 900
```

Each tick: load live features → strategy → execution → position → P&L → risk. Ctrl+C to stop gracefully.

### Fork Time Advancement (Batch)

In batch mode with Tenderly execution, the engine advances the fork's block timestamp by 24 hours on each date boundary
via `provider.advance_time(86400)`. This ensures time-dependent DeFi operations (interest accrual, oracle updates, epoch
boundaries) behave correctly across multi-day backtests.

## Key & Endpoint Resolution

### Secret Manager (Single Source for All Modes)

| Secret                   | Used By                                  | Modes                                                                                      |
| ------------------------ | ---------------------------------------- | ------------------------------------------------------------------------------------------ |
| `alchemy-api-key`        | All chain RPC calls                      | All (same key, different endpoints)                                                        |
| `tardis-api-key`         | CeFi historical data                     | Batch only                                                                                 |
| `thegraph-api-key`       | DeFi subgraph queries                    | All                                                                                        |
| Cloud KMS CMK (GCP/AWS)  | Transaction signing (May-23 default)     | Live only — `CLOUD_KMS_ENCRYPTED` signing surface per `interface-credential-convention.md` |
| `copper-api-key`         | Transaction signing (June-1 flip target) | Live only — MPC flip post client cred delivery                                             |
| `copper-sandbox-api-key` | Transaction signing (test)               | Paper only                                                                                 |
| `ceffu-api-key`          | Transaction signing (June-1 flip target) | Live only — CEFFU MirrorX flip post client cred delivery                                   |
| `fireblocks-api-key`     | Transaction signing (June-1 flip target) | Live only — Fireblocks MPC flip post client cred delivery                                  |

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
CHAIN_ENV=mainnet            # Mainnet chain IDs (fork uses mainnet IDs)
CUSTODY_PROVIDER=mock        # No real signing in batch

# Paper (local-paper.env):
CLOUD_PROVIDER=gcp
CLOUD_MOCK_MODE=false
CHAIN_ENV=fork               # Fork mode — mainnet chain IDs, Tenderly RPC
CUSTODY_PROVIDER=mock        # Fork doesn't verify signatures
TENDERLY_FORK=true           # Create Tenderly VNet fork for execution

# Live (local-live.env / production):
CLOUD_PROVIDER=gcp
CLOUD_MOCK_MODE=false
CHAIN_ENV=mainnet            # Real mainnet chain IDs and RPC URLs
CUSTODY_PROVIDER=cloud_kms   # May-23 cutover default — CLOUD_KMS_ENCRYPTED signing surface
                             # June-1 flip targets: copper / ceffu / fireblocks per client cred delivery
                             # SSOT: interface-credential-convention.md (2026-05-12 refresh)
```

## Smart Contract & Atomic Transaction Handling

### Pipeline Stage: execution-service (L6b)

```
Strategy emits StrategyInstruction[]
  │
  ▼
execution-service InstructionRouter
  ├── is_atomic=True? → Execute all-or-nothing
  │     ├── FLASH_BORROW → FlashLoanHandler (Aave V3 — only flash-loan connector in scope as of 2026-05-12; the
  │     │                  earlier "Morpho/AAVE" framing was aspirational per slot 8 exec audit EX-12, Morpho out
  │     │                  of scope until Phase 2-4 DeFi catalogue buildout)
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

| Mode      | Backend                                        | Smart Contracts                                               | Gas                          |
| --------- | ---------------------------------------------- | ------------------------------------------------------------- | ---------------------------- |
| **Batch** | `BenchmarkFillProvider` (lightweight fallback) | NOT called. Returns BENCHMARK_FILL at oracle price.           | Historical from GCS          |
| **Batch** | `TenderlyExecutionProvider` (production)       | Called on Tenderly fork at historical block. Real code paths. | Real from fork tx receipt    |
| **Paper** | `TenderlyExecutionProvider`                    | Called on Tenderly fork at latest block. Real-time execution. | Real from fork tx receipt    |
| **Live**  | Mainnet RPC + `CopperCustodyProvider`          | Called on mainnet. Real everything.                           | Real from mainnet tx receipt |

### Execution Provider Architecture

Location: `execution-service/execution_service/providers/`

The `ExecutionProvider` protocol (defined in `providers/base.py`) abstracts where on-chain transactions execute. Two
implementations exist:

1. **`TenderlyExecutionProvider`** -- creates a Tenderly VNet fork per run. Supports `create_fork()`, `fund_wallet()`,
   `advance_time()`, and `cleanup()`. Used for both batch (historical block) and paper (latest block) modes.
2. **`BenchmarkFillProvider`** -- lightweight no-op provider. All fills computed at oracle price with zero slippage.
   Used when `--benchmark-fill` is set or Tenderly credentials are unavailable.

Factory: `get_execution_provider(mode, ...)` in `providers/factory.py` routes `"fork"`/`"tenderly"` to
`TenderlyExecutionProvider` (with `BenchmarkFillProvider` fallback if no API key), anything else to
`BenchmarkFillProvider`.

See [Tenderly Execution Provider](tenderly-execution-provider.md) for full API details.

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
| Strategy declares intent (not hardcoded IDs) | **Working** — `StrategyInstrumentIntent` schema in UAC, resolution wired |
| Dynamic instrument subscription (hot reload) | **Partially** — config_reloaders exist but not wired to instruments      |
| Strategy ↔ execution decision boundary       | **Implemented in code** — SOR in execution, yields in strategy           |

### Execution Layer

| Component                                          | Status                                                                        |
| -------------------------------------------------- | ----------------------------------------------------------------------------- |
| InstructionRouter (all DeFi operations)            | **Working** — LEND/BORROW/SWAP/TRADE/FLASH/TRANSFER                           |
| BenchmarkFillProvider (lightweight batch)          | **Working** — `providers/benchmark.py`, quick iteration mode                  |
| TenderlyExecutionProvider (production batch/paper) | **Working** — `providers/tenderly.py`, VNet fork creation/fund/advance/delete |
| ExecutionProvider protocol + factory               | **Working** — `providers/base.py` + `providers/factory.py`                    |
| Tenderly fork fixtures (integration tests)         | **Working** — aave_connector, uniswap_connector                               |
| CopperCustodyProvider (live MPC signing)           | **Working** — `custody/copper.py`, HMAC-SHA256, full signing flow             |
| LocalKeyCustodyProvider (dev signing)              | **Working** — `custody/local_key.py`, Web3.py signing                         |
| MockCustodyProvider (test/batch)                   | **Working** — `custody/mock.py`, deterministic SHA256                         |
| Custody factory                                    | **Working** — `custody/factory.py`, routes on `config.provider`               |
| Live execution monitoring (confirmation, retry)    | **Needs building**                                                            |

### Pipeline Scripts

| Pipeline                                                                                                                                                        | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `run-data-prep.sh` (instruments, ticks, process, features)                                                                                                      | **Working** — positional subcommands for each pipeline stage                                                                                                                                                                                                                                                                                                                                                                                                   |
| `run-batch.sh` (historical replay)                                                                                                                              | **Working** — `--strategy`, `--strategies`, `--asset-group`, `--skip-data`                                                                                                                                                                                                                                                                                                                                                                                     |
| `run-paper.sh` (real-time on Tenderly fork)                                                                                                                     | **Working** — creates Tenderly fork, uses `local-paper.env`                                                                                                                                                                                                                                                                                                                                                                                                    |
| `run-live.sh` (real-time on mainnet)                                                                                                                            | **Working** — Copper custody, interactive safety confirmation                                                                                                                                                                                                                                                                                                                                                                                                  |
| `colocated_engine.py` (shared memory; strategy count is registry-driven, **not** the stale 44 figure cited prior to slot 8 exec audit EX-21 refresh 2026-05-12) | **Working** — async GCS sink, shared-memory architecture. **QG-wiring caveat**: per CLAUDE.md § "Peripheral Script Directories Under Primary-Consumer QG", `e2e-testing/scripts/defi/colocated_engine.py` MUST be wired into `strategy-service/scripts/quality-gates.sh` so symbol-removal incidents (2026-05-01 → 2026-05-08 silent rot of `get_strategy_factories` import) surface at PR time. Cross-reference: O-1 ops-area finding owns the QG-wiring fix. |

### Config Layer

| Component                                      | Status                                                                     |
| ---------------------------------------------- | -------------------------------------------------------------------------- |
| `CHAIN_ENV` switch (mainnet/testnet/fork)      | **Working** — UAC `registry/chain_env.py`, 21 chains, `resolve_chain_id()` |
| `chain_env` on UnifiedCloudConfig              | **Working** — env var `CHAIN_ENV`, validates against `CHAIN_ENVS`          |
| WalletMappingConfig (custodian wallet mapping) | **Working** — UAC `internal/domain/defi/wallet_config.py`                  |
| `local-batch.env` (CHAIN_ENV=mainnet)          | **Working**                                                                |
| `local-paper.env` (CHAIN_ENV=fork)             | **Working**                                                                |
| `local-live.env` (CHAIN_ENV=mainnet + copper)  | **Working**                                                                |

## References

- [Wallet Hierarchy](wallet-hierarchy-and-capital-flow.md) — treasury/trading wallet model
- [Custody Providers](custody-providers.md) — MPC signing integration (Copper + CEFFU + LocalKey + Mock)
- [Pipeline Layers](runtime-deployment-topology.md) — L1-L7 service architecture
- [DeFi Execution](../../.claude/CLAUDE.md) — DeFi pipeline flow section
