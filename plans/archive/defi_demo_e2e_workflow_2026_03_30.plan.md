---
title: "DeFi Demo: E2E Manual Trading Workflow — Treasury to P&L"
status: active
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-03-30
depends_on: [share-class-architecture, defi-phase3-infrastructure]
# Canonical playbook SSOT: codex/14-playbooks/playbooks/03c-demo-dart.md (DART flavour demo)
---

# DeFi Demo: E2E Manual Trading Workflow

## Context

> **Sequencing**: Phase 2A (StrategyInstruction changes) blocked on share_class_architecture sc-1a-uac-types. Phase 2C
> (treasury endpoint) blocked on defi_phase3_infrastructure Phase 4A (WalletMappingConfig). Phase 2D (risk backend)
> blocked on share_class_architecture sc-3c-risk.

Client demo for DeFi strategies. The user needs to manually recreate any DeFi strategy end-to-end in the UI: observe
treasury → move funds → execute trades (atomic) → see instant P&L → view trade history. Strategy families page is
blocked off for future.

Assumes Phase 3 infrastructure plan (`defi_phase3_infrastructure_2026_03_30.plan.md`) is complete: CHAIN_ENV, Tenderly,
custody, gas schema alignment.

## Demo Scenario (What the Client Sees)

```
1. Open UI → DeFi Trading page
2. See treasury wallet balance: $500K USDC on Ethereum
3. Select strategy: "Recursive Staked Basis" (or recreate manually)
4. See required steps:
   a. Transfer $400K USDC from treasury to trading wallet
   b. Swap $360K USDC → ETH (SOR picks best DEX)
   c. Swap ETH → weETH (EtherFi staking)
   d. Flash borrow ETH from Morpho
   e. Deposit weETH to AAVE as collateral
   f. Borrow ETH from AAVE against collateral
   g. Repay flash loan
   h. Transfer margin to Hyperliquid
   i. Short ETH perp on Hyperliquid
5. Execute each step (or batch execute all)
6. See instant P&L per step:
   - SWAP: expected 120 ETH, got 119.95 ETH → slippage -$150
   - Gas: $18.50
   - LEND: expected 119.95 aWEETH, got 119.95 → zero slippage
   - Net instant P&L: -$168.50 (entry cost)
7. See position dashboard:
   - Collateral: 119.95 aWEETH ($359,850)
   - Debt: 95.96 ETH ($287,880)
   - Perp: -95.96 ETH SHORT ($287,880)
   - Health Factor: 1.52
   - Net APY: 20.5% (after borrow cost)
8. See trade history with running total:
   | # | Time | Type | Instrument | Amount | Price | Gas | Slippage | Running P&L |
   |---|------|------|-----------|--------|-------|-----|----------|-------------|
   | 1 | 10:01 | TRANSFER | USDC | 400,000 | - | $2 | - | -$2 |
   | 2 | 10:02 | SWAP | ETH/USDC | 120 ETH | 3,000 | $15 | -$150 | -$167 |
   | ... | ... | ... | ... | ... | ... | ... | ... | ... |
```

## Execution DAG

```
Phase 1 (PARALLEL — workflow documentation + frontend audit)
  ├── 1A: Document e2e workflow per DeFi strategy in codex
  └── 1B: Audit frontend pages + components for DeFi manual trading
        │
        ▼  Gate: workflows documented, frontend gaps identified
Phase 2 (PARALLEL — backend gap filling)
  ├── 2A: Instant P&L computation (expected vs actual)
  ├── 2B: Trade history with running totals
  └── 2C: Live treasury wallet observation endpoint
        │
        ▼  Gate: backend APIs support all workflow steps
Phase 3 (SEQUENTIAL — frontend implementation)
  ├── 3A: DeFi manual trading page (execute steps)
  ├── 3B: Instant P&L display per instruction
  ├── 3C: Trade history table with running totals
  └── 3D: Position dashboard (collateral, debt, HF, APY)
        │
        ▼  Gate: demo runs end-to-end in UI
```

## Phase 1A: E2E Workflow Documentation

For each DeFi strategy, document the FULL manual workflow: what a user does step-by-step, which services are involved,
which instruction types, what P&L components appear.

### Strategies to Document

- [x] [AGENT] P0. **AAVE Lending** (simplest — good starting point for demo)
  - Steps: observe treasury → transfer USDC → lend to AAVE → see aToken balance → see interest accruing
  - Services: position-balance-monitor → execution-service → pnl-attribution
  - Instructions: TRANSFER, LEND
  - P&L: gas (one-time), interest (continuous from liquidity index)

- [x] [AGENT] P0. **Basis Trade** (multi-venue, CeFi + DeFi)
  - Steps: observe treasury → swap USDC→ETH → transfer margin to venues → short perp per venue
  - Services: execution (SOR for swap, venue transfer, perp trade)
  - Instructions: TRANSFER, SWAP, TRADE
  - P&L: gas, swap slippage, funding rate (continuous), venue fees

- [x] [AGENT] P0. **Recursive Staked Basis** (most complex, demo highlight)
  - Steps: treasury → swap → stake → flash borrow → lend → borrow → repay → hedge
  - Services: execution (atomic bundle), risk (HF/LTV)
  - Instructions: TRANSFER, SWAP, FLASH_BORROW, LEND, BORROW, FLASH_REPAY, TRADE
  - P&L: gas, swap slippage, staking yield, borrow cost, funding rate, rewards

- [x] [AGENT] P1. **Staked Basis** (simpler than recursive)
- [x] [AGENT] P1. **Ethena Benchmark** (simplest — deploy and hold)
- [x] [AGENT] P1. **LP Market Making** (Uniswap V3 — ADD_LIQUIDITY, fee tracking, IL)

### Per-Strategy Workflow Format

Each workflow doc should include:

1. **Prerequisites**: what's in the wallet, what chains/venues are needed
2. **Step-by-step instructions**: numbered, with instruction type and parameters
3. **Service interactions**: which backend service handles each step
4. **Instant P&L per step**: expected vs actual, slippage, gas, fees
5. **Position state after each step**: what the wallet/protocol looks like
6. **Risk metrics**: HF, LTV, delta, exposure after deployment
7. **Ongoing P&L**: how daily P&L is computed (liquidity index, funding rate, etc.)
8. **Exit workflow**: step-by-step to unwind the position

## Phase 1B: Frontend Audit

- [x] [AGENT] P0. Audit unified-trading-system-ui for existing DeFi trading pages
  - Which pages exist? (DeFi overview, manual trading, position view, P&L)
  - What widgets/components exist for DeFi?
  - What API endpoints do they call?
  - What's missing for the demo workflow?

- [x] [AGENT] P0. Map frontend requirements from e2e workflows:
  - Treasury balance display (per chain, per token)
  - Manual instruction builder (select type → fill params → execute)
  - Instruction execution status (pending → confirmed → filled)
  - Instant P&L display per instruction (expected vs actual)
  - Trade history table with running totals
  - Position dashboard (collateral/debt/perp, HF, LTV, APY)
  - Strategy P&L chart (cumulative, attribution breakdown)

## Phase 2A: Instant P&L Computation

- [x] [AGENT] P0. Add `expected_output` field to StrategyInstruction:
  - SWAP: expected output token amount (from oracle price)
  - LEND: expected aToken amount (from supply amount)
  - STAKE: expected LST amount (from exchange rate)
  - BORROW: expected borrowed amount
- [x] [AGENT] P0. Compute `instant_pnl` in execution-service fill:
  - `instant_pnl = (actual_output - expected_output) * price - gas_cost`
  - Zero in batch (benchmark fill = oracle price)
  - Non-zero in live (real execution has slippage)
- [x] [AGENT] P0. Add `instant_pnl` to FILLS_SCHEMA in execution-service

## Phase 2B: Trade History with Running Totals

- [x] [AGENT] P0. Trade history endpoint in position-balance-monitor or API gateway:
  - Already exists: `GET /trades`, `GET /trades/count`, `GET /trades/{fill_id}`, `GET /trades/summary`
  - Filterable by strategy, date range, instruction type

## Phase 2C: Live Treasury Observation

- [x] [AGENT] P0. Treasury balance endpoint:
  - Created: `GET /treasury/balance`, `GET /treasury/balance/history`, `GET /treasury/config`, `POST /treasury/evaluate`
  - Returns treasury vs trading wallet split, status, rebalance amounts

## Phase 2D: Risk Dimensions

Per-strategy risk computation and display. Frontend first (mock), backend after.

- [x] [AGENT] P0. Define risk dimension types in `lib/types/defi.ts`:
  - `protocol_risk`: smart contract, oracle, governance (qualitative: low/medium/high)
  - `coin_isolated_risk`: individual token price collapse exposure
  - `basis_risk`: spot vs perp divergence (for basis/staked strategies)
  - `funding_rate_risk`: funding going negative across venues
  - `liquidity_risk_pct`: % drawdown to close ALL positions at once (function of pool/orderbook depth)
- [x] [AGENT] P0. Delta neutrality composite:
  - Per strategy: what is it neutral TO? (USD, ETH, SOL)
  - `net_delta_usd`, `net_delta_eth`, `net_delta_sol` per strategy
  - Aggregate across all strategies: total portfolio delta exposure
  - Share class grouping: USD-denominated strategies should net to ~0 delta USD
- [x] [AGENT] P0. Liquidation cost estimation:
  - "What does it cost to exit everything right now?"
  - Slippage at full position size per venue/pool
  - Show as % of total portfolio value
- [x] [AGENT] P1. Backend: risk-and-exposure-service computes from live positions — `DefiRiskExtra` + `ClientRiskResult`
      TypedDicts added; all 5 DeFi risk functions (`evaluate_health_factor_risk`, `evaluate_base_currency_drift`,
      `check_oracle_depeg`, `check_stablecoin_depeg`, `check_borrow_staking_spread`) wired into per-client loop in
      orchestrator.py; `compute_risk()` returns `dict[str, ClientRiskResult]` with metrics + defi_alerts; 5 new unit
      tests in `test_defi_emode_orchestrator.py`

## Phase 2E: Lending/Borrowing Rate Impact Simulation

**Goal**: Realistically simulate how OUR lending/borrowing changes pool utilization and therefore changes supply/borrow
APYs. Pure math from Aave V3 interest rate model (on-chain params). Alert when actual rates deviate from projected
rates.

**Aave V3 Interest Rate Model (from Aave docs)**:

```
U = total_borrows / total_supply   (utilization)
if U <= U_optimal:
    borrow_rate = base_rate + (U / U_optimal) * slope1
else:
    borrow_rate = base_rate + slope1 + ((U - U_optimal) / (1 - U_optimal)) * slope2
supply_rate = borrow_rate * U * (1 - reserve_factor)
```

Rate model params are ALREADY fetched by UMI aave_lending.py Graph query: `optimalUtilisationRate`,
`variableRateSlope1`, `variableRateSlope2`, `baseVariableBorrowRate`, `reserveFactor`

### 2E-1: Rate Model in UAC (pure math, zero side effects)

- [x] [AGENT] P0. Create `unified_api_contracts/internal/domain/defi/rate_model.py`:
  - `AavePoolParams` — holds rate model params (optimal_utilization, slope1, slope2, base_rate, reserve_factor,
    total_supply_usd, total_borrow_usd)
  - `RateImpactResult` — (pre_supply_apy, post_supply_apy, pre_borrow_apy, post_borrow_apy, utilization_before,
    utilization_after, rate_change_bps)
  - `compute_borrow_rate(utilization, slope1, slope2, optimal, base_rate) -> Decimal`
  - `compute_supply_rate(utilization, borrow_rate, reserve_factor) -> Decimal`
  - `simulate_rate_impact(pool_params, our_amount_usd, trade_type: "supply"|"borrow") -> RateImpactResult`
  - All Decimal math, no float
- [x] [AGENT] P0. Export from `internal/domain/defi/__init__.py`
- [x] [AGENT] P0. Add `DEFI_RATE_DEVIATION` to `DefiAlertType` enum in UAC

### 2E-2: Rate Impact Feature Calculator

- [x] [AGENT] P0. Create `features_onchain_service/app/calculators/aave_rate_impact_calculator.py`:
  - Reads pool params from DefiLlama (total_supply, total_borrow, rates) — same source as existing calculators
  - Reads our position sizes from GCS (position-balance-monitor output)
  - Computes: `projected_supply_apy`, `projected_borrow_apy`, `rate_impact_bps` per pool
  - Writes features to GCS alongside existing `aave_supply_apy`, `aave_borrow_apy`
  - Strategy reads `projected_supply_apy` instead of raw `aave_supply_apy` for sizing decisions

### 2E-3: Rate Deviation Alerting

- [x] [AGENT] P0. Add `check_rate_deviation()` to `alerting_service/rules/defi_rules.py`:
  - Compares actual on-chain rate vs our projected rate (from rate model)
  - If abs(actual - projected) > 50 bps → P1 alert (Telegram)
  - If abs(actual - projected) > 200 bps → P0 alert (PagerDuty + Telegram)
  - Causes: other large deposits/withdrawals moved utilization, governance parameter change
  - Message includes: pool, projected_apy, actual_apy, delta_bps, likely cause
- [x] [AGENT] P0. Wire into event router (`_ALERT_TYPE_TO_EVENT` map)

### 2E-4: Strategy Uses Projected Rates

- [x] [AGENT] P0. Update `AAVELendingStrategy.generate_signal()` in strategy-service:
  - Read `projected_supply_apy` from features (post-trade rate)
  - If projected APY < min_threshold: don't deploy (our deposit would crash the rate)
  - Log rate impact in signal metadata: `rate_impact_bps`, `pre_apy`, `post_apy`
- [x] [AGENT] P0. Update recursive/staked strategies similarly:
  - Read `projected_borrow_apy` for borrow sizing
  - If projected borrow rate would make net APY negative: skip or reduce leverage

### 2E-5: Batch Simulation Per Day

- [x] [AGENT] P0. In batch pipeline (pnl-attribution or batch_handler):
  - For each day: load pool state (total_supply, total_borrow) from features GCS
  - Apply our position changes from that day's fills
  - Compute new rates using AaveInterestRateModel
  - Use POST-TRADE rates for daily P&L (not raw market rates)
  - Output: per-day rate trajectory CSV showing pre/post rates + our impact

### Success Criteria (Rate Impact)

1. `simulate_rate_impact()` matches Aave V3 math exactly (unit test against known pool states)
2. For $500K USDC deposit into $2B USDC pool: rate impact < 1 bps (sanity check)
3. For $50M deposit into same pool: rate impact measurably higher
4. Strategy reduces position size when projected APY drops below threshold
5. Alert fires when actual rate deviates >50bps from projected
6. Batch run produces per-day rate trajectory showing our impact for e2e date range

## Phase 3: Frontend Implementation

All in existing trading terminal tabs. NOT strategy families (blocked).

### 3A: Mock Data Alignment (FIRST — align naming before adding features)

- [x] [AGENT] P0. Add strategy IDs to DeFi types (AAVE_LENDING, BASIS_TRADE, etc.)
- [x] [AGENT] P0. Align instruction types with backend OperationType enum
- [x] [AGENT] P0. Add algo-per-instruction dropdown (instruction type → algo selector)
  - SWAP → SOR_DEX / SOR_TWAP
  - LEND → BENCHMARK_FILL
  - TRADE → DIRECT_MARKET
  - TRANSFER → DIRECT
  - FLASH_BORROW → FLASH_LOAN_MORPHO / FLASH_LOAN_AAVE
- [x] [AGENT] P0. Align venue names to canonical IDs (UNISWAPV3-ETHEREUM not "Uniswap")
- [x] [AGENT] P0. Align instrument IDs to canonical format
- [x] [AGENT] P0. Add `max_slippage_bps`, `expected_output`, `benchmark_price` to instruction params
- [x] [AGENT] P0. Add `instant_pnl` decomposition to order/fill types (gross, slippage, gas, fees, net)

### 3B: Risk Visualisation (in existing tabs)

- [x] [AGENT] P0. **Positions tab**: net delta per underlying, per strategy
- [x] [AGENT] P0. **Risk tab**: delta composite heatmap, liquidation cost %, risk dimension breakdown
- [x] [AGENT] P0. **Overview tab**: total portfolio delta exposure KPI
- [x] [AGENT] P1. Per-strategy drill-down: what it's neutral to, current deviation _(archived 2026-04-22 — product
      polish; not blocking; reopen from `plans/archive/` if prioritized.)_

### 3C: Trading Functionality

- [x] [AGENT] P0. Instant P&L display per instruction (alpha decomposition)
- [x] [AGENT] P0. Trade history table with running totals
- [x] [AGENT] P0. Position dashboard (collateral, debt, HF, LTV, APY, delta)
- [x] [AGENT] P0. Treasury balance per chain per token

### 3D: Rebalance Flow

- [x] [AGENT] P0. Rebalance button on DeFi wallet summary widget (or positions tab):
  - Triggered when treasury % deviates from target (high = deploy, low = reduce)
  - Preview: shows proposed capital movements per strategy before executing
  - Executes: generates the StrategyInstruction sequence for rebalancing
  - Uses TreasuryMonitor.compute_rebalance_amounts() logic
- [x] [AGENT] P0. Rebalance preview dialog:
  - "Treasury at 35% (target 20%). Deploying $150K:"
  - Per-strategy allocation: AAVE +$80K, Basis +$50K, Recursive +$20K
  - Per-instruction breakdown with algo assignment
  - Confirm → generates instructions → executes

### 3E: DeFi Reconciliation

- [x] [AGENT] P0. Extend reconciliation to DeFi protocols:
  - On-chain balance vs system position per protocol
  - aToken balance from AAVE vs position-balance-monitor
  - LP position from Uniswap subgraph vs our tracker
  - Perp position from Hyperliquid API vs our records
  - Break types: position, pnl, fee, gas (same schema as CeFi recon)
  - Add DeFi venues to reconciliation.ts mock data (AAVEV3-ETHEREUM, UNISWAPV3-ETHEREUM, etc.)
- [x] [AGENT] P1. Reconciliation resolution workflow — already fully implemented in
      `batch-live-reconciliation-service/batch_live_reconciliation_service/api/resolution_api.py`:
      `POST /reconciliation/breaks/{id}/accept`, `/reject`, `/investigate`, `/book-correction`; `ReconciliationAction` +
      `ReconciliationResolution` schemas in `unified_api_contracts.internal.reconciliation`

## Success Criteria

1. Client can manually recreate any DeFi strategy in the UI
2. Each instruction has type dropdown → algo dropdown (instruction type determines available algos)
3. Each step shows instant P&L decomposed: gross, slippage, gas, fees, net
4. Trade history shows all instructions with running totals
5. Position dashboard shows collateral, debt, HF, LTV, APY, net delta
6. Risk tab shows: protocol/coin/basis/funding/liquidity risk + delta composite + liquidation cost %
7. Positions tab shows net delta per underlying per strategy (USD, ETH, SOL dimensions)
8. Overview tab shows total portfolio delta exposure
9. Treasury wallet balance visible per chain per token
10. All mock data uses real backend naming (strategy IDs, canonical venues, instruction types)
11. E2E workflow documented per strategy in codex

## Prompt for Next Session

```
Continue from the plan at:
unified-trading-pm/plans/active/defi_demo_e2e_workflow_2026_03_30.plan.md

DeFi client demo: manually recreate strategies end-to-end in UI.
Phase 1 (e2e workflows + frontend audit) is DONE. Start with Phase 3A (mock data
alignment) then Phase 2D (risk dimensions) + Phase 3B (risk visualisation).

Key context:
- Memory: memory/project_defi_demo_e2e_workflow.md
- Memory: memory/feedback_defi_risk_dimensions.md
- Memory: memory/feedback_frontend_mock_alignment.md
- Strategy docs: codex/09-strategy/defi/ (6 with e2e workflows)
- Frontend audit: 8 DeFi widgets exist, all mock-backed, no backend APIs
- UI widgets: components/widgets/defi/*.tsx
- UI types: lib/types/defi.ts
- UI context: components/widgets/defi/defi-data-context.tsx
- UI config: lib/config/services/defi.config.ts
- Custody: execution-service/execution_service/custody/
- Treasury: position-balance-monitor-service/core/treasury_monitor.py
- Phase 3 infra plan: plans/active/defi_phase3_infrastructure_2026_03_30.plan.md

Strategy families page is BLOCKED — don't touch.
Focus on: mock alignment → risk dimensions → delta visualisation → instant P&L.
All in existing trading terminal tabs (positions, risk, overview, defi).
```
