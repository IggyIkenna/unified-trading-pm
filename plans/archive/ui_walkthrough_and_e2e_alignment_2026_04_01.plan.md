---
doc_type: plan
title: ui-walkthrough-and-e2e-alignment
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, execution-service, strategy-service, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-03"
remaining_todos_consolidated_into: consolidated_strategy_and_ui_2026_04_15
superseded_by: [consolidated_strategy_and_ui_2026_04_15.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
overview:
  UI full strategy walkthrough capability (all strategies manually executable in mock), E2E testing for all modes,
  batch=live alignment
type: code
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-01
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: unified-trading-system-ui, code: C0, deployment: none, business: none }
  - { repo: e2e-testing, code: C0, deployment: none, business: none }
  - { repo: strategy-service, code: C0, deployment: none, business: none }
  - { repo: execution-service, code: C0, deployment: none, business: none }
  - { repo: pnl-attribution-service, code: C0, deployment: none, business: none }
  - { repo: position-balance-monitor-service, code: C0, deployment: none, business: none }
  - { repo: risk-and-exposure-service, code: C0, deployment: none, business: none }
depends_on:
  [
    share-class-architecture,
    defi-instrument-pipeline-and-rewards,
    token-wrapping-venue-collateral,
    client-config-and-defi-risk,
    ui-sync-hardening,
    platform-strategy-families-and-haruko-gaps,
  ]
todos:
  - { id: ui-1a-walkthrough-audit, content: "- [ ] [AGENT] P0. Audit UI for every strategy walkthrough — can client
        manually execute each step?

        ", status: todo, note: Every strategy must be walkable in mock mode }
  - { id: ui-1b-lending-walkthrough, content: "- [x] [AGENT] P0. Ensure AAVE lending strategy is fully walkable
        (deposit, monitor yield, withdraw)

        ", status: done, note: "" }
  - { id: ui-1c-staking-walkthrough, content: "- [x] [AGENT] P0. Ensure staking strategy is fully walkable (stake,
        monitor weETH, claim rewards, sell rewards)

        ", status: done, note: "" }
  - { id: ui-1d-basis-walkthrough, content: "- [x] [AGENT] P0. Ensure basis trade is fully walkable (spot buy, perp
        short, funding collection, rebalance, unwind)

        ", status: done, note: "" }
  - { id: ui-1e-recursive-walkthrough, content: "- [x] [AGENT] P0. Ensure recursive staking is fully walkable (flash
        loan bundle, HF monitoring, emergency exit)

        ", status: done, note: "" }
  - { id: ui-2a-batch-live, content: "- [ ] [AGENT] P0. Verify batch=live alignment across all services for all
        strategies

        ", status: todo, note: "" }
  - { id: ui-2b-e2e-all-strategies, content: "- [ ] [AGENT] P0. Create E2E test suite covering all strategies in all
        modes (batch/paper/live)

        ", status: todo, note: "" }
  - { id: ui-3a-demo-scripts, content: "- [ ] [AGENT] P1. Create demo walkthrough scripts for client presentations

        ", status: todo, note: "" }
  - { id: ui-4a-docs, content: "- [ ] [AGENT] P1. Update codex + handover docs

        ", status: todo, note: "" }
isProject: false
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_strategy_and_ui_2026_04_15.md](./consolidated_strategy_and_ui_2026_04_15.md).** Original scope retained
> for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit formalises it as
> canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.

# UI Strategy Walkthrough & E2E Testing Alignment

> **Conflict resolution**: Phase 1D (HF monitoring card) overlaps with ui_sync_hardening p7b (HF chart fix). This plan
> owns the dedicated HF card — ui_sync_hardening should defer HF UI to this plan. Execution order: ui_sync_hardening
> (fixes existing pages) → platform_strategy_families (adds new pages/tabs) → this plan (DeFi-specific walkthrough
> flows).

## Context

The UI must allow a client to **manually walk through every strategy step-by-step** as if executing it in the real
system. Even though data is mock, the full functionality must be present. A client demo should show:

1. **I have money in my treasury** → see treasury balance
2. **I want to do lending** → select strategy, see expected yield, click deploy, see position
3. **I want to do staking** → stake ETH, see weETH, see staking yield accumulating, see EIGEN rewards, claim rewards,
   sell rewards
4. **I want to do basis trade** → see funding rates per venue, select coins, see weighted allocation, deploy spot+perp,
   see funding P&L
5. **I want to do recursive staking** → see flash loan bundle preview, approve atomic execution, see leveraged position,
   monitor health factor, see emergency exit option

Every action the system can do must be demonstrable in the UI. Mock data fills in the numbers, but the UI components,
forms, and flows must be real.

Additionally, **batch = live** alignment: the same strategy code runs in batch (historical backtest), paper (Tenderly
fork), and live (mainnet). They must produce the same types of outputs, use the same instruction types, and flow through
the same services.

## Pre-Audit: UI Walkthrough Gaps

| Strategy          | Step                            | Current UI State                             | Gap                                                          |
| ----------------- | ------------------------------- | -------------------------------------------- | ------------------------------------------------------------ |
| **AAVE Lending**  | Deploy (deposit)                | Lending widget exists with protocol selector | Verify deposit flow works end-to-end in mock                 |
| **AAVE Lending**  | Monitor yield                   | Rates overview widget exists                 | Verify yield accrual shows in P&L over time                  |
| **AAVE Lending**  | Withdraw                        | Lending widget has withdraw                  | Verify withdrawal reflects in positions                      |
| **Staking**       | Stake ETH→weETH                 | Staking widget exists                        | Verify staking flow with protocol selector (Lido vs EtherFi) |
| **Staking**       | Monitor weETH yield             | Rates overview has staking                   | Verify weETH/ETH rate change shows in P&L                    |
| **Staking**       | Claim EIGEN rewards             | **GAP**                                      | No claim button or reward status display                     |
| **Staking**       | Sell EIGEN→USDT                 | **GAP**                                      | No reward selling flow in UI                                 |
| **Staking**       | View reward P&L                 | **GAP**                                      | No breakdown of staking vs restaking vs seasonal P&L         |
| **Basis Trade**   | View funding rates              | **PARTIAL**                                  | Rates overview shows some, needs per-coin-per-venue matrix   |
| **Basis Trade**   | See venue weights               | **GAP**                                      | No two-waterfall weight visualisation                        |
| **Basis Trade**   | Deploy spot+perp                | Flash loans widget has bundle builder        | Verify basis-specific flow                                   |
| **Basis Trade**   | View funding P&L                | Trade history has running P&L                | Verify funding rate income shows separately                  |
| **Basis Trade**   | Rebalance                       | Rebalance dialog exists                      | Verify rebalance with cost-benefit display                   |
| **Basis Trade**   | Unwind                          | **PARTIAL**                                  | Need full unwind flow with cost estimate                     |
| **Recursive**     | Preview flash loan bundle       | Flash loans widget exists                    | Verify 8-step atomic bundle preview                          |
| **Recursive**     | Monitor health factor           | **PARTIAL**                                  | HF in positions table, but no dedicated HF dashboard         |
| **Recursive**     | Emergency exit                  | **GAP**                                      | No emergency exit button with cost estimate                  |
| **Cross-cutting** | Share class selector            | **GAP**                                      | No share class switching in UI (Plan 1 covers this)          |
| **Cross-cutting** | Token wrapping visibility       | **GAP**                                      | User doesn't see auto-wrap/unwrap steps                      |
| **Cross-cutting** | Expected costs before execution | **GAP**                                      | No pre-execution cost estimate popup                         |

## Execution DAG

```
Phase 1 (PARALLEL — UI walkthrough completion)
  ├── 1A: Audit and fix lending walkthrough
  ├── 1B: Audit and fix staking walkthrough (+ reward lifecycle UI)
  ├── 1C: Audit and fix basis trade walkthrough (+ funding rate matrix)
  └── 1D: Audit and fix recursive staking walkthrough (+ HF dashboard + emergency exit)
        │
        ▼  Gate: all 4 strategies fully walkable in mock mode
Phase 2 (PARALLEL — batch=live alignment + E2E)
  ├── 2A: Verify batch=live output parity across all services
  └── 2B: Create comprehensive E2E test suite
        │
        ▼  Gate: E2E suite runs all strategies in batch + paper mode
Phase 3 (Demo scripts + Docs)
  ├── 3A: Demo walkthrough scripts
  └── 3B: Codex + handover docs
```

## Phase 1: UI Walkthrough Completion (PARALLEL)

### 1A: Lending Walkthrough

**Repo**: unified-trading-system-ui

- [ ] [AGENT] P0. Verify lending deposit flow:
  1. User selects AAVE protocol, selects asset (USDT/USDC/DAI/WETH/WBTC)
  2. User enters amount
  3. Mock shows: expected APY, estimated gas cost, expected output (aToken amount)
  4. User clicks "Deploy" → position appears in positions table
  5. P&L starts accumulating (interest income factor)

- [ ] [AGENT] P0. Verify lending monitor flow:
  1. Position shows: current value, accrued interest, APY, utilisation %
  2. P&L tab shows: CARRY factor increasing over time
  3. Alert if utilisation >95% (withdrawal risk)

- [ ] [AGENT] P0. Verify lending withdraw flow:
  1. User clicks "Withdraw" on position
  2. Mock shows: amount to receive, gas cost
  3. Position removed, P&L finalised

- [ ] [AGENT] P0. Add mock data for multi-asset lending (USDT + USDC + DAI basket showing different APYs)

### 1B: Staking Walkthrough (+ Reward Lifecycle)

**Repo**: unified-trading-system-ui

- [ ] [AGENT] P0. Verify staking flow:
  1. User selects protocol (EtherFi or Lido via dropdown)
  2. User enters ETH amount to stake
  3. Mock shows: expected weETH/stETH output, staking APY, estimated gas
  4. User clicks "Stake" → position shows weETH/stETH in positions table

- [ ] [AGENT] P0. Add reward tracking UI components:

  ```
  ┌─────────────────────────────────────────┐
  │ Staking Rewards                          │
  │                                          │
  │ EIGEN Rewards                            │
  │   Accrued (unclaimed): 12.5 EIGEN ($42)  │
  │   Next payout: Mon 2026-04-07            │
  │   [Claim] [Claim & Sell]                 │
  │                                          │
  │ ETHFI Seasonal                           │
  │   Next airdrop: ~Jun 2026               │
  │   Est. amount: TBD                       │
  │                                          │
  │ Staking Yield                            │
  │   weETH/ETH rate: 1.0352                 │
  │   30d yield: +0.3% ($1,050)              │
  └─────────────────────────────────────────┘
  ```

- [ ] [AGENT] P0. Add "Claim Rewards" button:
  - Shows: claimable amount, estimated gas cost, net value after gas
  - Emits: CLAIM_REWARD mock instruction
  - After claim: rewards move from "accrued" to "claimed" status

- [ ] [AGENT] P0. Add "Sell Rewards" button:
  - Shows: amount to sell, estimated price (EIGEN/USDT), expected output, gas + slippage
  - Emits: SELL_REWARD mock instruction
  - After sell: rewards move to realised P&L

- [ ] [AGENT] P0. Add reward P&L breakdown to P&L tab:
  - STAKING_YIELD: weETH/ETH appreciation
  - RESTAKING_REWARD: EIGEN claimed and sold
  - SEASONAL_REWARD: ETHFI airdrop (when applicable)
  - REWARD_UNREALISED: M2M of unclaimed

- [ ] [AGENT] P0. Add mock data:
  - Pending EIGEN rewards (accrued over simulated weeks)
  - Historical claim + sell transactions
  - Lido variant mock (stETH, no EIGEN rewards)

### 1C: Basis Trade Walkthrough (+ Funding Rate Matrix)

**Repo**: unified-trading-system-ui

- [ ] [AGENT] P0. Add funding rate matrix widget:

  ```
  ┌─────────────────────────────────────────────────────────┐
  │ Funding Rates (Annualised)                                │
  │                                                           │
  │ Coin    │ HyperLiq │  OKX   │ Bybit  │ Binance │ Aster  │
  │ ────────┼──────────┼────────┼────────┼─────────┼────────│
  │ ETH     │  6.2%    │  5.1%  │  4.8%  │  5.5%   │  4.3%  │
  │ BTC     │  5.8%    │  4.9%  │  4.5%  │  5.2%   │  4.1%  │
  │ SOL     │  8.1%    │  6.2%  │  5.9%  │  7.1%   │  5.5%  │
  │ DOGE    │ 12.3%    │  9.8%  │  8.5%  │ 10.2%   │    -   │
  │                                                           │
  │ Floor: 2.5% annual    Coins below floor: greyed out       │
  └─────────────────────────────────────────────────────────┘
  ```

- [ ] [AGENT] P0. Add two-waterfall weight visualisation:

  ```
  ┌───────────────────────────────────────┐
  │ Allocation Weights                     │
  │                                        │
  │ Coin Weights (Pillar 1):              │
  │   ETH: 35% ████████                   │
  │   SOL: 30% ███████                    │
  │   DOGE: 20% █████                     │
  │   BTC: 15% ████                       │
  │                                        │
  │ ETH Venue Weights (Pillar 2):         │
  │   HyperLiquid: 30% ███               │
  │   Binance: 25% ██                     │
  │   OKX: 20% ██                         │
  │   Bybit: 15% █                        │
  │   Aster: 10% █                        │
  │                                        │
  │ [Patrick: restricted to OKX/Bybit/BIN]│
  └───────────────────────────────────────┘
  ```

- [ ] [AGENT] P0. Add basis trade deploy flow:
  1. User sees: coin allocation, venue weights, total notional, expected APY
  2. User sees: estimated execution cost (gas + slippage for spot leg, exchange fees for perp legs)
  3. User clicks "Deploy" → spot buy + perp shorts appear in positions
  4. Funding P&L starts accumulating

- [ ] [AGENT] P0. Add basis trade unwind flow:
  1. User clicks "Unwind" on basis position
  2. Mock shows: estimated unwind cost (close perps + sell spot), expected P&L after costs
  3. Positions closed, P&L finalised

- [ ] [AGENT] P0. Add mock data:
  - Funding rates for 5+ coins across 5 venues
  - Two-waterfall weights computed
  - Running funding P&L over time
  - Rebalance events with cost-benefit log

### 1D: Recursive Staking Walkthrough (+ HF Dashboard + Emergency Exit)

**Repo**: unified-trading-system-ui

- [ ] [AGENT] P0. Enhance flash loan bundle preview:

  ```
  ┌───────────────────────────────────────────┐
  │ Atomic Bundle Preview (8 steps)            │
  │                                            │
  │ 1. FLASH_BORROW 400 WETH from Morpho (0%) │
  │ 2. SWAP 450 WETH → 450 weETH              │
  │ 3. LEND 450 weETH → Aave (collateral)     │
  │ 4. BORROW 400 WETH from Aave              │
  │ 5. FLASH_REPAY 400 WETH to Morpho         │
  │ 6. TRANSFER USDC to HyperLiquid           │
  │ 7. SHORT 450 ETH on HyperLiquid           │
  │                                            │
  │ Result:                                    │
  │   Leverage: 2.5x                           │
  │   Health Factor: 1.38                      │
  │   Est. Net APY: 12.5%                      │
  │   Est. Gas Cost: $45                       │
  │                                            │
  │ [Execute Atomic Bundle]                    │
  └───────────────────────────────────────────┘
  ```

- [ ] [AGENT] P0. Add dedicated Health Factor monitoring card:

  ```
  ┌───────────────────────────────────────┐
  │ Health Factor Monitor                  │
  │                                        │
  │ Current HF: 1.38  🟢                  │
  │ Liquidation at: 1.0                   │
  │ Warning at: 1.3                       │
  │ Buffer: 0.38 (27.5%)                  │
  │                                        │
  │ weETH/ETH oracle: 1.0352              │
  │ weETH/ETH market: 1.0348              │
  │ Oracle-market gap: 0.04% 🟢           │
  │                                        │
  │ Borrow rate: 2.1%                     │
  │ Staking rate: 3.2%                    │
  │ Net spread: +1.1% (×2.5 = 2.75%)     │
  │                                        │
  │ Monitoring: every 5 minutes           │
  └───────────────────────────────────────┘
  ```

- [ ] [AGENT] P0. Add Emergency Exit button:

  ```
  ┌───────────────────────────────────────┐
  │ ⚠ Emergency Exit                      │
  │                                        │
  │ Estimated cost to fully unwind:        │
  │   Gas: $85                             │
  │   Slippage: $320                       │
  │   Exchange fees: $45                   │
  │   Total: $450 (0.3% of NAV)           │
  │   Time: ~15 minutes                   │
  │                                        │
  │ Steps:                                │
  │ 1. Close perp shorts (HyperLiquid)    │
  │ 2. Repay WETH debt (Aave)            │
  │ 3. Withdraw weETH collateral (Aave)   │
  │ 4. Unwrap weETH → ETH                │
  │ 5. Transfer to treasury               │
  │                                        │
  │ [Confirm Emergency Exit]              │
  └───────────────────────────────────────┘
  ```

- [ ] [AGENT] P0. Add mock data for recursive staking:
  - 8-step atomic bundle with realistic amounts
  - Health factor history (time series)
  - Oracle vs market price comparison
  - Borrow-staking spread history
  - Emergency exit cost estimate

## Phase 2: Batch=Live Alignment + E2E (PARALLEL)

### 2A: Batch=Live Output Parity

**Repos**: strategy-service, execution-service, pnl-attribution-service, position-balance-monitor-service,
risk-and-exposure-service

- [ ] [AGENT] P0. For each DeFi strategy, verify that batch and live modes produce identical output schemas:

  | Service                  | Output              | Batch Source                | Live Source                  | Must Match                              |
  | ------------------------ | ------------------- | --------------------------- | ---------------------------- | --------------------------------------- |
  | strategy-service         | StrategyInstruction | GCS features → instructions | Live features → instructions | Same instruction types, same fields     |
  | execution-service        | Fill                | Tenderly fork execution     | Mainnet execution            | Same fill schema (gas, slippage, price) |
  | pnl-attribution-service  | PnLBreakdown        | GCS fills → P&L             | Live fills → P&L             | Same factors, same decomposition        |
  | position-balance-monitor | PositionReport      | GCS fills → positions       | Live positions               | Same position schema                    |
  | risk-and-exposure        | RiskMetrics         | Computed from positions     | Computed from positions      | Same risk types, same thresholds        |

- [ ] [AGENT] P0. Verify instruction types are consistent:
  - Batch must emit TRANSFER, LEND, BORROW, STAKE, SWAP, TRADE, FLASH_BORROW, FLASH_REPAY, CLAIM_REWARD, SELL_REWARD
  - Paper mode must handle same instruction types on Tenderly fork
  - Live mode must handle same instruction types on mainnet

- [ ] [AGENT] P0. Verify gas costs are tracked consistently:
  - Batch: real gas from Tenderly fork receipt
  - Paper: real gas from Tenderly fork receipt
  - Live: real gas from mainnet receipt
  - All modes: same `GasCostRecord` schema

- [ ] [AGENT] P0. Verify reward lifecycle works in batch:
  - Batch features include `eigen_claimable_amount` (from historical features)
  - Strategy emits CLAIM_REWARD + SELL_REWARD in batch
  - P&L attributes rewards in batch

### 2B: Comprehensive E2E Test Suite

**Repo**: e2e-testing

- [ ] [AGENT] P0. Create `e2e-testing/scripts/defi/run-all-strategies.sh`:

  ```bash
  #!/bin/bash
  # Run all DeFi strategies in specified mode
  MODE=${1:-batch}  # batch, paper, live

  STRATEGIES=(
      DEFI_LENDING_AAVE_1H
      DEFI_BASIS_ETH_1H
      DEFI_STAKED_BASIS_ETH_1H
      DEFI_RECURSIVE_BASIS_ETH_1H
  )

  for strategy in "${STRATEGIES[@]}"; do
      echo "Running $strategy in $MODE mode..."
      bash scripts/defi/run-${MODE}.sh --strategy "$strategy" --days 7
      # Validate outputs
      bash scripts/defi/validate-outputs.sh --strategy "$strategy" --mode "$MODE"
  done
  ```

- [ ] [AGENT] P0. Create `validate-outputs.sh` that checks:
  1. Instructions parquet exists and has correct schema
  2. Fills parquet exists with gas costs
  3. P&L breakdown has all expected factors
  4. Positions include all expected instrument types
  5. Risk metrics include health factor (for leveraged strategies)
  6. Reward instructions present (for staking strategies)

- [ ] [AGENT] P0. Create per-strategy acceptance criteria files:

  ```yaml
  # e2e-testing/configs/defi/acceptance/DEFI_LENDING_AAVE_1H.yaml
  expected_instruction_types: [TRANSFER, LEND, WITHDRAW]
  expected_pnl_factors: [CARRY, FEES]
  expected_positions: [A_TOKEN]
  min_instructions_per_day: 1
  expected_gas_per_instruction_usd: [1, 50] # range
  ```

  ```yaml
  # e2e-testing/configs/defi/acceptance/DEFI_RECURSIVE_BASIS_ETH_1H.yaml
  expected_instruction_types: [FLASH_BORROW, SWAP, LEND, BORROW, FLASH_REPAY, TRANSFER, TRADE]
  expected_pnl_factors: [STAKING_YIELD, FUNDING, CARRY, FEES, SLIPPAGE]
  expected_positions: [A_TOKEN, DEBT_TOKEN, LST, PERPETUAL]
  health_factor_tracked: true
  atomic_bundle_expected: true
  ```

  ```yaml
  # e2e-testing/configs/defi/acceptance/DEFI_STAKED_BASIS_ETH_1H.yaml
  expected_instruction_types: [TRANSFER, STAKE, TRADE, CLAIM_REWARD, SELL_REWARD]
  expected_pnl_factors: [STAKING_YIELD, FUNDING, RESTAKING_REWARD, FEES]
  expected_positions: [LST, PERPETUAL, WALLET_SPOT]
  reward_lifecycle_expected: true
  ```

- [ ] [AGENT] P0. Create mode parity test:
  ```bash
  # Run same strategy in batch and paper, compare output schemas
  bash scripts/defi/run-batch.sh --strategy DEFI_LENDING_AAVE_1H --days 1
  bash scripts/defi/run-paper.sh --strategy DEFI_LENDING_AAVE_1H --days 1
  bash scripts/defi/compare-outputs.sh --batch-dir /tmp/batch --paper-dir /tmp/paper
  # Should match: instruction types, fill schema, P&L factors, position types
  # May differ: actual amounts (fork vs historical may have different rates)
  ```

## Phase 3: Demo Scripts + Docs

### 3A: Demo Walkthrough Scripts

**Repo**: e2e-testing

- [ ] [AGENT] P1. Create `e2e-testing/docs/defi/DEMO_WALKTHROUGH.md`:

  ```markdown
  # DeFi Client Demo Walkthrough

  ## Prerequisites

  - Start UI: `cd unified-trading-system-ui && npm run dev`
  - Login as Patrick: patrick@bankelysium.com / demo

  ## Demo 1: AAVE Lending (5 min)

  1. Navigate to DeFi tab → Lending widget
  2. Select: Protocol=Aave V3, Asset=USDT, Amount=$100K
  3. Show: Expected APY (4.2%), gas estimate ($12)
  4. Click Deploy → position appears in Positions tab
  5. Switch to P&L tab → show interest accruing
  6. Show risk tab → no liquidation risk (supply only)

  ## Demo 2: Staking with Rewards (8 min)

  1. Navigate to DeFi tab → Staking widget
  2. Select: Protocol=EtherFi, Amount=50 ETH
  3. Show: Expected staking APY (3.2%) + EIGEN rewards
  4. Click Stake → weETH position appears
  5. Show: Rewards panel with accrued EIGEN
  6. Click "Claim & Sell" → reward realised in P&L
  7. Switch to P&L tab → show staking yield + restaking reward breakdown

  ## Demo 3: Basis Trade (10 min)

  ...

  ## Demo 4: Recursive Staking (12 min)

  ...
  ```

- [ ] [AGENT] P1. Create `e2e-testing/scripts/defi/run-demo-local.sh`:
  ```bash
  # Start all services in mock mode for local demo
  # Uses dev-tiers.sh tier 2 + mock data
  ```

### 3B: Documentation Updates

- [ ] [AGENT] P1. Update `unified-trading-system-ui/docs/DEFI_DEMO_HANDOVER.md`:
  - Add walkthrough for each strategy
  - Add new UI components (reward lifecycle, funding matrix, HF dashboard, emergency exit)
  - Add share class switching instructions
  - Add mock data descriptions

- [ ] [AGENT] P1. Create `/codex/08-workflows/defi-demo-runbook.md`:
  - Full demo script from start to finish
  - What to show for each strategy
  - How to handle questions about gaps (strategy rotation = future, documented)
  - Emergency scenarios to demonstrate (HF drop, depeg)

- [ ] [AGENT] P1. Update `/codex/08-workflows/local-dev.md`:
  - Add DeFi-specific local dev instructions
  - E2E testing setup
  - Demo mode vs full mode

## Success Criteria

1. All 4 DeFi strategies fully walkable in UI mock mode (deposit→monitor→claim→unwind)
2. Reward lifecycle visible in UI (claim button, sell button, reward P&L breakdown)
3. Funding rate matrix shows per-coin-per-venue rates with floor indicator
4. Two-waterfall weight visualisation shows coin + venue allocation
5. Health factor dashboard with oracle-market gap and borrow-staking spread
6. Emergency exit button with cost estimate
7. Batch=live output parity verified (same schemas, same instruction types)
8. E2E test suite runs all 4 strategies with per-strategy acceptance criteria
9. Mode parity test compares batch vs paper outputs
10. Demo walkthrough script covers all 4 strategies in 35 minutes
11. All 7 repos pass `quality-gates.sh`

## Prompt for Next Session

```
Continue from the plan at:
unified-trading-pm/plans/active/ui_walkthrough_and_e2e_alignment_2026_04_01.md

Key context:
- UI has 12 DeFi widgets already (defi-*-widget.tsx)
- Patrick's demo user exists (patrick@bankelysium.com, defi-trading entitlement)
- DeFi mock data exists in lib/mocks/fixtures/defi-*.ts
- E2E testing has run-batch.sh, run-paper.sh, run-live.sh scripts
- colocated_engine.py handles multi-service batch execution
- Key new UI needs: reward claim/sell, funding rate matrix, HF dashboard, emergency exit

Start with Phase 1 (walkthrough audit), one strategy at a time.
Depends on Plans 1-4 for share class, rewards, token wrapping, and risk enhancements.
```
