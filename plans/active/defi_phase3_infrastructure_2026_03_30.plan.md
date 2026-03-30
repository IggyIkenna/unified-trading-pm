---
title: "DeFi Phase 3: Infrastructure Alignment — Chain Config, Tenderly, Pipelines, Custody"
status: active
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-03-30
---

# DeFi Phase 3: Infrastructure Alignment

## Context

Phase 2 (2026-03-30) built all DeFi strategies (15+ variants), multi-chain data pipeline, LP with real IL math,
cross-chain SOR, and wallet/custody architecture. This phase aligns the infrastructure so batch/paper/live use the same
code paths, same schemas, and same config structure.

Key principle: **batch calls contracts on a Tenderly fork** (same code path as live). The only difference between modes
is which chain the transaction hits (fork vs testnet vs mainnet).

## Execution DAG

```
Phase 1 (PARALLEL — config + schema alignment)
  ├── 1A: CHAIN_ENV config switch
  ├── 1B: Gas schema alignment
  └── 1C: Intent-based instrument resolution
        │
        ▼  QG gate: UAC + instruments-service pass
Phase 2 (SEQUENTIAL — Tenderly execution)
  ├── 2A: TenderlyExecutionProvider
  └── 2B: Dynamic instrument subscription
        │
        ▼  QG gate: execution-service + strategy-service pass
Phase 3 (PARALLEL — pipeline scripts)
  ├── 3A: Paper trading pipeline (run-paper-pipeline.sh)
  └── 3B: Live trading pipeline validation
        │
        ▼  Gate: paper pipeline runs end-to-end
Phase 4 (PARALLEL — wallet + custody)
  ├── 4A: Custodian wallet mapping config
  └── 4B: Copper MPC implementation
        │
        ▼  Gate: execution-service signs on Tenderly fork via mock custody
Phase 5 (SEQUENTIAL — clean run)
  └── 5A: Full data gathering (instruments + MTDS, 1 month)
  └── 5B: Clean run + comparison plots across all strategies
        │
        ▼  Gate: P&L plots for all strategies, compare vs Ethena benchmark
Phase 6 (DOCS — after each build phase)
  └── 6A: Update codex + strategy docs to reflect all changes
```

## Phase 1: Config & Schema Alignment (PARALLEL)

### 1A: CHAIN_ENV Config Switch

**Goal**: Strategy says `"ETHEREUM"`, system resolves to chain_id=1 (mainnet) or 11155111 (Sepolia) based on
`CHAIN_ENV`.

**Repos**: unified-api-contracts, unified-config-interface

- [ ] [AGENT] P0. Create `CHAIN_NAME_TO_ENV_ID` mapping in UAC:
  ```python
  MAINNET_CHAIN_IDS = {"ETHEREUM": 1, "ARBITRUM": 42161, "BASE": 8453, ...}
  TESTNET_CHAIN_IDS = {"ETHEREUM": 11155111, "ARBITRUM": 421614, "BASE": 84532, ...}
  def resolve_chain_id(chain_name: str, env: str = "mainnet") -> int
  ```
- [ ] [AGENT] P0. Add `CHAIN_ENV` to UnifiedCloudConfig (defaults to "mainnet")
- [ ] [AGENT] P0. Update all consumers of `CHAIN_NAME_TO_ID` to use `resolve_chain_id()`
- [ ] [AGENT] P0. Update execution-service bridge_cost_model.py + sor_cross_chain.py
- [ ] [AGENT] P1. Update `local-batch.env` and create `local-paper.env` with `CHAIN_ENV=testnet`
- [ ] [AGENT] P1. DOC: Update execution-modes-and-chain-resolution.md with final implementation

### 1B: Gas Schema Alignment

**Goal**: Same schema fields for gas costs across batch/live. Only the source differs (GCS vs tx receipt).

**Repos**: unified-api-contracts, pnl-attribution-service

- [ ] [AGENT] P0. Define canonical `GasCostRecord` schema in UAC internal:
  ```
  chain_id, chain_name, gas_price_gwei, gas_used, gas_cost_eth, gas_cost_usd,
  priority_fee_gwei, timestamp, source ("gcs_historical" | "tx_receipt" | "fork_receipt")
  ```
- [ ] [AGENT] P0. Update MTDS gas_fee_handler to write this schema
- [ ] [AGENT] P0. Update pnl-attribution to read this schema (same code path regardless of source)
- [ ] [AGENT] P1. Add Solana gas fields: `priority_fee_lamports`, `compute_units`
- [ ] [AGENT] P1. Add BTC gas fields: `sat_per_vbyte`, `fee_rate_btc_per_kb`
- [ ] [AGENT] P1. DOC: Update cost-modeling.md with unified gas schema

### 1C: Intent-Based Instrument Resolution

**Goal**: Strategy declares intent (protocol, chain, base_currencies), instruments-service resolves to specific IDs.

**Repos**: strategy-service, instruments-service, unified-api-contracts

- [ ] [AGENT] P0. Define `StrategyInstrumentIntent` schema in UAC:
  ```
  protocol, chain, base_currencies[], instrument_types[], venue_filter[]
  ```
- [ ] [AGENT] P0. Add `resolve_instruments(intent, date)` to instruments-service client API
- [ ] [AGENT] P0. Update strategy batch_handler to call resolve_instruments() instead of hardcoded lists
- [ ] [AGENT] P1. Validate resolved instruments against strategy expectations (error if missing)
- [ ] [AGENT] P1. DOC: Update execution-modes-and-chain-resolution.md instrument resolution section

## Phase 2: Tenderly Execution (SEQUENTIAL after Phase 1)

### 2A: TenderlyExecutionProvider

**Goal**: Batch + paper use Tenderly fork for smart contract execution. Same connector code, different RPC URL.

**Repos**: execution-service

- [ ] [AGENT] P0. Create `execution_service/providers/tenderly.py`:
  - `create_fork(chain_id, block_number)` → fork RPC URL
  - `fund_wallet(fork_rpc, address, tokens)` → seed test wallet
  - `advance_time(fork_rpc, seconds)` → for batch replay
- [ ] [AGENT] P0. Create `execution_service/providers/base.py` — `ExecutionProvider` protocol:
  - `get_rpc_url(chain, env)` → mainnet / fork / testnet URL
  - `sign_and_submit(tx, wallet_id)` → signed tx hash
- [ ] [AGENT] P0. Wire `TenderlyExecutionProvider` as default for batch mode
- [ ] [AGENT] P0. Keep `BenchmarkFillProvider` as lightweight fallback (`--benchmark-fill` flag)
- [ ] [AGENT] P1. Batch creates fork per day, advances block time, replays candles
- [ ] [AGENT] P1. DOC: Update execution-modes doc + DeFi execution architecture in CLAUDE.md

### 2B: Dynamic Instrument Subscription

**Goal**: Strategy hot-reloads when instrument universe changes (new pools, expiries).

**Repos**: strategy-service, unified-trading-library

- [ ] [AGENT] P1. Wire instruments-service GCS output to strategy config_reloaders
- [ ] [AGENT] P1. Strategy re-evaluates on instrument change: new pool with better yield → rebalance
- [ ] [AGENT] P1. Handle expiring instruments: close position before expiry date
- [ ] [AGENT] P1. DOC: Update strategy docs with dynamic subscription behavior

## Phase 3: Pipeline Scripts (PARALLEL after Phase 2)

### 3A: Paper Trading Pipeline

**Goal**: Real-time trading on Tenderly fork with live data feeds.

**Repos**: e2e-testing

- [ ] [AGENT] P0. Create `run-paper-pipeline.sh`:
  - Same service architecture as batch
  - `CHAIN_ENV=testnet` + Tenderly fork
  - Live data feeds (not GCS historical)
  - Real-time event loop (not replay)
- [ ] [AGENT] P0. Create `local-paper.env` config
- [ ] [AGENT] P1. Paper mode runs continuously (not per-date)
- [ ] [AGENT] P1. DOC: Document paper trading setup and usage

### 3B: Live Trading Pipeline Validation

**Goal**: Validate `run-live-pipeline.sh` against paper, identify divergences.

**Repos**: e2e-testing

- [ ] [AGENT] P1. Audit existing `run-live-pipeline.sh` against paper pipeline
- [ ] [AGENT] P1. Document all code path differences between paper and live
- [ ] [AGENT] P1. Create convergence checklist: what must be identical vs what differs
- [ ] [AGENT] P1. DOC: Document live trading requirements + go-live checklist

## Phase 4: Wallet & Custody (PARALLEL after Phase 2)

### 4A: Custodian Wallet Mapping Config

**Goal**: Real vs testnet wallet addresses, same config structure, custodian-agnostic.

**Repos**: unified-api-contracts, unified-config-interface

- [ ] [AGENT] P0. Define `WalletMappingConfig` schema in UAC:
  ```
  custodian, chain_env, treasury_wallet_id, treasury_address,
  trading_wallets: {strategy_id: {wallet_id, address}}
  ```
- [ ] [AGENT] P0. GCS config path: `wallet-config/{chain_env}/wallet_mapping.json`
- [ ] [AGENT] P0. Testnet config uses Sepolia/devnet addresses
- [ ] [AGENT] P1. DOC: Update wallet-hierarchy-and-capital-flow.md with config schema

### 4B: Copper MPC Implementation

**Goal**: Real Copper API calls for transaction signing.

**Repos**: execution-service

- [ ] [AGENT] P1. Implement `CopperCustodyProvider` in `execution_service/custody/copper.py`:
  - HMAC-SHA256 authentication
  - `POST /platform/orders` → create transfer/sign order
  - `POST /platform/orders/{id}/sign` → initiate MPC signing
  - Poll for completion (~1-2 seconds)
- [ ] [AGENT] P1. Implement `LocalKeyCustodyProvider` in `custody/local_key.py`:
  - Signs with raw private key from Secret Manager
  - For development only (not production)
- [ ] [AGENT] P1. Integration test against Copper sandbox
- [ ] [AGENT] P1. DOC: Update copper-custody-integration.md with implementation details

## Phase 5: Clean Run + Plots (SEQUENTIAL after all above)

### 5A: Data Gathering (1 month)

- [ ] [AGENT] P0. Run instruments-service for all categories (CEFI + DEFI) for March 2026
- [ ] [AGENT] P0. Run MTDS for all venues + gas fee collection for March 2026
- [ ] [AGENT] P0. Run MDPS + features-onchain for March 2026
- [ ] [AGENT] P0. Verify GCS has complete data for all target instruments

### 5B: Clean Run + Comparison Plots

- [ ] [AGENT] P0. Run all strategies: AAVE_LENDING, BASIS_TRADE, RECURSIVE_STAKED_BASIS, STAKED_BASIS, ETHENA_BENCHMARK,
      UNHEDGED_RECURSIVE, BTC_BASIS, AMM_LP
- [ ] [AGENT] P0. Generate plots: P&L per strategy, P&L attribution, HF/LTV, funding rates, venue allocation
- [ ] [AGENT] P0. Compare strategy returns vs Ethena benchmark
- [ ] [AGENT] P0. P&L breakdown: interest, funding, gas, slippage, IL, unexplained (<2%)

## Phase 6: Documentation (AFTER each build phase)

- [ ] [AGENT] P0. After Phase 1: update codex architecture docs with CHAIN_ENV, gas schema, instrument resolution
- [ ] [AGENT] P0. After Phase 2: update DeFi execution docs with Tenderly provider, instrument subscription
- [ ] [AGENT] P0. After Phase 3: document paper + live pipeline setup and convergence
- [ ] [AGENT] P0. After Phase 4: update custody + wallet docs with real implementation
- [ ] [AGENT] P0. After Phase 5: create results summary doc with strategy comparison

## Success Criteria

1. `CHAIN_ENV=mainnet` and `CHAIN_ENV=testnet` both resolve correctly for all 30+ chains
2. Gas schema identical across batch/live — `GasCostRecord` used everywhere
3. Batch executes on Tenderly fork with real contract calls (not BENCHMARK_FILL)
4. Paper pipeline runs end-to-end in real-time on fork
5. Paper and live pipelines have documented convergence (same code paths except RPC target)
6. Custody provider is pluggable — mock/local_key/copper all work via factory
7. All strategies produce valid 30-day P&L with <2% unexplained
8. Every build phase has corresponding codex documentation

## Prompt for Next Session

```
Continue from the plan at:
unified-trading-pm/plans/active/defi_phase3_infrastructure_2026_03_30.plan.md

Phase 2 strategies are done (15+ variants). Phase 3 is infrastructure alignment:
CHAIN_ENV, gas schema, Tenderly execution, pipelines, custody.

Key context:
- Memory: memory/feedback_instrument_resolution_and_mode_alignment.md
- Memory: memory/feedback_wallet_architecture.md
- Architecture: codex/04-architecture/execution-modes-and-chain-resolution.md
- Architecture: codex/04-architecture/wallet-hierarchy-and-capital-flow.md
- Architecture: codex/04-architecture/copper-custody-integration.md
- Batch pipeline: e2e-testing/scripts/defi/run-batch-pipeline.sh
- Tenderly fixtures: execution-service/tests/integration/conftest.py
- Custody interface: execution-service/execution_service/custody/
- Treasury monitor: position-balance-monitor-service/core/treasury_monitor.py

User is running instruments pipeline now. Start with Phase 1 (CHAIN_ENV + gas schema + intent resolution).
```
