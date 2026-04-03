---
title: "DeFi Strategies Phase 2: Multi-Coin, LP, SOR, Recursive Staking"
status: active
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-03-29
depends_on: [share-class-architecture, defi-instrument-pipeline-and-rewards]
---

# DeFi Strategies Phase 2

## Context

> **Sequencing**: Phase 2B/2C/2D strategy files (defi_base.py, defi_basis.py etc.) must run AFTER share_class sc-2a
> (adds share_class to config) and defi_instrument_pipeline ip-3a/ip-5a (adds reward/lido fields). These 4 plans edit
> the same strategy files — strict order: share_class → defi_instrument → client_config → defi_strategies_phase2.

Phase 1 (2026-03-28/29) built the production-grade DeFi pipeline with batch=live parity:

- Aave USDC lending: fully working (2.1% APY, real gas, daily P&L from liquidity index)
- Multi-venue basis trade: 4 perp venues with funding-rate-proportional weighting
- Infrastructure: GCS configs, position tracking, TRANSFER pairs, hourly orchestrator

Phase 2 expands to the full DeFi strategy suite.

## Phase 2A: Multi-Coin Funding Rate Data (PARALLEL)

**Goal**: Download spot prices + funding rates for 20 MVP coins across 5 venues (incl. Aster).

- [x] [AGENT] P0. Get MVP coin list from UAC registry — VenueMapping.hyperliquid_aster_mvp_base_assets (21 coins)
- [x] [AGENT] P0. Download Hyperliquid funding rates for all coins via S3 archive + REST fallback
- [x] [AGENT] P0. Download Binance Futures funding rates via Tardis derivative_ticker
- [x] [AGENT] P1. Download OKX/Bybit funding rates via Tardis (okex-swap, bybit exchanges)
- [x] [AGENT] P0. Download Aster funding rates via REST API (Binance-compatible /fapi/v1/fundingRate)
- [x] [AGENT] P0. Write to GCS features bucket: per-venue onchain_perps feature group (batch_orchestrator
      --download-data)
- [x] [AGENT] P1. Basis trade strategy: select_top_coins_by_funding() — top N coins by avg rate across venues

## Phase 2B: LP Market Making — Uniswap V3 (SEQUENTIAL after 2A)

**Goal**: Concentrated liquidity positions on Uniswap V3. Strategy manages range, rebalances on price drift.

- [x] [AGENT] P0. Strategy: UniswapV3LPStrategy with \_collect_instructions()
  - Implemented as `AmmLPStrategy` in `strategy_service/engine/strategies/defi_amm_lp.py`
  - Instruction types: ADD_LIQUIDITY, REMOVE_LIQUIDITY, REBALANCE_RANGE all implemented
  - Config: pair, fee tier, range width (in ticks), rebalance threshold
  - P&L: fees earned (from swap volume \* position share) - impermanent loss (compute_impermanent_loss_v2)
- [x] [AGENT] P0. Execution: LP handlers in InstructionRouter for ADD_LIQUIDITY/REMOVE_LIQUIDITY
  - Instructions defined in execution-service `defi_execution/instructions.py`
- [x] [AGENT] P1. Features: pool volume, TVL, fee APY from Uniswap subgraph data
  - AmmLPStrategy reads pool_volume, pool_tvl, fee_apy, current_tick from features
- [x] [AGENT] P1. Risk: impermanent loss tracking, range utilization %
  - `_range_utilization()` and `compute_pnl_breakdown()` with IL tracking in defi_amm_lp.py

## Phase 2C: Multi-Chain SOR for Swaps (PARALLEL with 2B)

**Goal**: Smart Order Router that splits swaps across chains for best execution.

- [x] [AGENT] P0. Read available liquidity per chain from features (Uniswap, Curve, Balancer pools)
  - `CrossChainSORStrategy` in `cross_chain_sor.py` reads per-chain pool liquidity from features
- [x] [AGENT] P0. SOR algorithm: minimize slippage by splitting across venues/chains
  - Implemented as `CrossChainSORStrategy` with bridge cost + time factored in via `is_bridge_worthwhile()`
  - Generates TRANSFER + SWAP instruction sequences for cross-chain moves
- [x] [AGENT] P1. Bridge integration: Socket/LayerZero transfer instructions
  - `SocketBridgeConnector` with live Socket v2 API (`https://api.socket.tech/v2`) implemented in
    `execution_service/defi_execution/protocols/bridge.py`
- [x] [AGENT] P1. Gas comparison across chains (L2s much cheaper than L1)
  - L1/L2 gas differentials reflected in bridge cost model within CrossChainSORStrategy

## Phase 2D: Recursive Staking (SEQUENTIAL after 2A + 2C)

**Goal**: Leveraged yield: supply collateral → borrow → re-supply → repeat.

- [x] [AGENT] P0. Strategy: RecursiveStakedBasisStrategy already fully implemented
  - 8-step atomic deploy (flash borrow → swap → lend → borrow → repay → hedge)
  - 7-step atomic exit (flash borrow → repay → withdraw → swap → close hedge)
  - Config: target_leverage, max_leverage, min_health_factor, flash_loan_provider
  - Deleverage: partial exit when HF drops below target (20% reduction)
- [x] [AGENT] P0. Risk: HF/LTV tracking via compute_health_factor() in UAC defi_reserve_params.py
  - Dynamic AAVE LTV/liquidation threshold from features
  - Max safe leverage = 1/(1-ltv) \* 0.85
- [x] [AGENT] P0. P&L: net*apy = (staking + funding + rewards) * leverage - borrow \_ (leverage - 1)
  - Example: (3% + 5% + 2%) _ 2.5x - 3% _ 1.5x = 25% - 4.5% = 20.5% net
- [x] [AGENT] P1. Flash loan optimization: already implemented — Morpho (0% fee) or AAVE V3 (0.05%)
  - FlashLoanReceiver contract in deployment-service, validated by execution-service connect()

## Phase 2E: Omnichain Transfers (PARALLEL)

**Goal**: Move assets across chains via bridge protocols.

- [x] [AGENT] P1. TRANSFER instruction with chain routing (Ethereum → Arbitrum → Base)
  - Implemented in `multichain_lending.py` `_build_cross_chain_transfer()` and `cross_chain_sor.py`
- [x] [AGENT] P1. Bridge cost model: gas + bridge fee + time estimate
  - `_DEFAULT_BRIDGE_COSTS` static table + `BridgeCostEstimate` dataclass with bridge_cost_pct() in cross_chain_sor.py
- [x] [AGENT] P1. Cross-chain position tracking: same wallet, multiple chains
  - Confirmed in `position_balance_monitor_service/core/defi_health_aggregator.py` — `per_chain_health` field and
    `_compute_per_chain_health()` method track positions per chain

## Phase 2F: Clean Run + Plots (AFTER all above)

- [ ] [AGENT] P0. Clean GCS state (delete stale fills from old runs)
  - No clean-state script found in e2e-testing/scripts/defi/ — needs implementation
- [ ] [AGENT] P0. Full 7-day run: lending + basis trade + recursive staking
  - run-batch.sh exists but no 7-day orchestration script confirmed
- [ ] [AGENT] P0. Generate plots: positions, P&L attribution, HF/LTV, funding rates, venue allocation
  - No plot generation script found in e2e-testing
- [ ] [AGENT] P0. Compare strategy returns: lending vs basis vs recursive
  - Dependent on 7-day run completing first

## Success Criteria

1. Multi-coin basis trade selects top coins by funding rate and allocates accordingly
2. LP strategy generates ADD_LIQUIDITY/REMOVE_LIQUIDITY instructions, P&L includes fees - IL
3. Recursive staking reaches target LTV with proper HF monitoring
4. Cross-chain SOR produces split execution across venues with bridge instructions
5. All strategies run through the same batch=live pipeline (hourly orchestrator)
6. P&L attribution breaks down: interest, funding, fees, gas, slippage, IL per strategy

## Prompt for Next Session

```
Continue the DeFi strategies work from the plan at:
unified-trading-pm/plans/active/defi_strategies_phase2_2026_03_29.plan.md

Phase 1 is done (lending + basis trade pipeline, batch=live parity).
Start with Phase 2A: download multi-coin funding rate data for 20 coins
across Hyperliquid/Binance/OKX/Bybit. Then Phase 2D: recursive staking
strategy (most impactful — leveraged yield with proper HF/LTV tracking).

Key context:
- Memory: memory/defi_pipeline_session_2026_03_29.md
- Feedback: memory/feedback_batch_live_parity_defi.md
- Strategy config pattern: GCS at strategy-store-.../configs/strategies/{id}.json
- Position tracking: batch_handler._position_state persists across days
- Instruction pairs: TRANSFER+LEND, WITHDRAW+TRANSFER (explicit steps)
- P&L: daily from liquidity index, real gas from GCS
- Risk: compute_health_factor() in UAC defi_reserve_params.py
- Batch orchestrator: e2e-testing/scripts/defi/batch_orchestrator.py --mode hourly
```
