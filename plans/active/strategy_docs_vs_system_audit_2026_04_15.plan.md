---
name: strategy-docs-vs-system-audit
overview:
  Full audit of codex/09-strategy docs against backend system — close all gaps in both directions, implement new
  strategies, add centralised on-chain primitives
type: mixed
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
  - repo: execution-service
    code: C0
    deployment: none
    business: none
  - repo: features-onchain-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-system-ui
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-api
    code: C0
    deployment: none
    business: none

depends_on: []

todos:
  # ──────────────────────────────────────────────────────────────────────
  # PHASE 0 — INDEX + CATALOG (prerequisite for everything)
  # ──────────────────────────────────────────────────────────────────────
  - id: p0-index
    content: |
      - [ ] [AGENT] P0. Update codex/09-strategy/README.md — strategy count 37→65+, add all missing entries, update domain tables, add new strategy families
    status: todo
  - id: p0-catalog
    content: |
      - [ ] [AGENT] P0. Update STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md — add all missing families (CrossExchange, StatArb, RelVol, VolSurface, OptionsMM, PredictionArb, UnhedgedRecursive, EthenaBenchmark, LendingProtocolArb, LiquidationCapture, ActiveDeFiMM, OmnichainTransfer, EventDrivenMacro, CommodityRegime), add 13+ execution algos, reference 7 feature services and 150+ calculators
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 1 — COMPLETE STUBS (3 files, PARALLEL)
  # ──────────────────────────────────────────────────────────────────────
  - id: p1a-cefi-momentum
    content: |
      - [ ] [AGENT] P0. DOC: Complete cefi/momentum.md from TODO stub — CeFiMomentumStrategy (BTC/ETH/SOL), read strategy class for actual signal logic, features consumed, risk profile
    status: todo
  - id: p1b-cefi-meanrev
    content: |
      - [ ] [AGENT] P0. DOC: Complete cefi/mean-reversion.md from TODO stub — MeanReversionStrategy (BTC/ETH/SOL Z-score), read strategy class for thresholds, mean window, features
    status: todo
  - id: p1c-sports-arb
    content: |
      - [ ] [AGENT] P0. DOC: Complete sports/arbitrage.md from stub — ArbitrageStrategy with 6 venue adapters (Betfair, Smarkets, Matchbook, Betdaq, Polymarket, Kalshi), cross-bookmaker odds detection
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 2 — WRITE MISSING DOCS FOR EXISTING STRATEGIES (10 files, PARALLEL)
  # ──────────────────────────────────────────────────────────────────────
  - id: p2a-cefi-ml
    content: |
      - [ ] [AGENT] P1. DOC: Write cefi/ml-directional.md — CeFiMLDirectionalStrategy (BTC/ETH/SOL ML price prediction), 6 model families, swing_high/swing_low targets
    status: todo
  - id: p2b-cefi-crossex
    content: |
      - [ ] [AGENT] P1. DOC: Write cefi/cross-exchange.md — CrossExchangeStrategy (venue spread arb, Binance config exists)
    status: todo
  - id: p2c-cefi-statarb
    content: |
      - [ ] [AGENT] P1. DOC: Write cefi/stat-arb.md — StatArbStrategy (BTC-ETH cointegration, config exists)
    status: todo
  - id: p2d-tradfi-momentum
    content: |
      - [ ] [AGENT] P1. DOC: Write tradfi/tradfi-momentum.md — TradFiMomentumStrategy (SPY)
    status: todo
  - id: p2e-tradfi-relvol
    content: |
      - [ ] [AGENT] P1. DOC: Write tradfi/relative-volatility.md — RelVolStrategy (BTC-ETH relative vol)
    status: todo
  - id: p2f-tradfi-volsurf
    content: |
      - [ ] [AGENT] P1. DOC: Write tradfi/volatility-surface.md — VolSurfaceStrategy (Deribit BTC)
    status: todo
  - id: p2g-tradfi-optionsmm
    content: |
      - [ ] [AGENT] P1. DOC: Write tradfi/market-making-options.md — OptionsMMStrategy (delta-neutral quoting)
    status: todo
  - id: p2h-sports-kelly
    content: |
      - [ ] [AGENT] P1. DOC: Write sports/kelly.md — KellyCriterionStrategy (pure Kelly-sized utility maximisation)
    status: todo
  - id: p2i-sports-halftime
    content: |
      - [ ] [AGENT] P1. DOC: Write sports/halftime-ml.md — HalftimeMLStrategy (pre-game + HT windows, NFL/NBA/Soccer configs)
    status: todo
  - id: p2j-prediction-arb
    content: |
      - [ ] [AGENT] P1. DOC: Create prediction/ directory and write prediction/prediction-arb.md — PredictionArbStrategy (Kalshi/Polymarket, config exists)
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 3 — WRITE MISSING DEFI VARIANT DOCS (12 files, PARALLEL)
  # ──────────────────────────────────────────────────────────────────────
  - id: p3a-ethena
    content: |
      - [ ] [AGENT] P1. DOC: Write defi/ethena-benchmark.md — EthenaBenchmarkStrategy (sUSDe buy-and-hold benchmark)
    status: todo
  - id: p3b-btc-basis
    content: |
      - [ ] [AGENT] P1. DOC: Write defi/btc-basis-trade.md — BtcBasisTradeStrategy
    status: todo
  - id: p3c-btc-lending
    content: |
      - [ ] [AGENT] P1. DOC: Write defi/btc-lending-yield.md — BtcLendingStrategy
    status: todo
  - id: p3d-sol-basis
    content: |
      - [ ] [AGENT] P1. DOC: Write defi/sol-basis-trade.md — SolBasisTradeStrategy
    status: todo
  - id: p3e-sol-staked
    content: |
      - [ ] [AGENT] P1. DOC: Write defi/sol-staked-basis.md — SolStakedBasisStrategy (rebalancing, Kamino)
    status: todo
  - id: p3f-sol-lending
    content: |
      - [ ] [AGENT] P1. DOC: Write defi/sol-lending-yield.md — KaminoLendingStrategy (Solana native)
    status: todo
  - id: p3g-sol-lp
    content: |
      - [ ] [AGENT] P1. DOC: Write defi/sol-concentrated-lp.md — SolConcentratedLPStrategy (Raydium/Orca)
    status: todo
  - id: p3h-multichain-lending
    content: |
      - [ ] [AGENT] P1. DOC: Write defi/multi-chain-lending-yield.md — MultiChainLendingStrategy (SOR across chains)
    status: todo
  - id: p3i-crosschain-yield
    content: |
      - [ ] [AGENT] P1. DOC: Write defi/cross-chain-yield-arb.md — CrossChainYieldArbStrategy (yield differential)
    status: todo
  - id: p3j-crosschain-sor
    content: |
      - [ ] [AGENT] P1. DOC: Write defi/cross-chain-sor-rebalancing.md — CrossChainSORStrategy (meta strategy)
    status: todo
  - id: p3k-l2-basis
    content: |
      - [ ] [AGENT] P1. DOC: Write defi/l2-basis-trade.md — L2BasisTradeStrategy (Arbitrum, Optimism, Base)
    status: todo
  - id: p3l-unhedged
    content: |
      - [ ] [AGENT] P1. DOC: Write defi/unhedged-recursive.md — UnhedgedRecursiveStrategy (leverage without hedge)
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 4 — UPDATE CROSS-CUTTING DOCS (8 files, PARALLEL)
  # ──────────────────────────────────────────────────────────────────────
  - id: p4a-ml-pipeline
    content: |
      - [ ] [AGENT] P1. DOC: Update cross-cutting/ml-pipeline.md — add 6 model families (LightGBM, XGBoost, CatBoost, Huber, Ridge, Poisson), 6 inference modes (batch, live, ensemble, cascade, meta-signal, SHAP), walk-forward validation, model promotion
    status: todo
  - id: p4b-config-arch
    content: |
      - [ ] [AGENT] P1. DOC: Update cross-cutting/config-architecture.md — add all 13+ execution algos (TWAP, VWAP, Iceberg, POV, SOR-CeFi, SOR-DEX, AdaptiveTWAP, AlmgrenChriss, PassiveAggressive, SOR-TWAP, Swap-TWAP, Batch Auction, Intent Engine), 5 matching engine types (L0/L1/L2/AMM/Benchmark)
    status: todo
  - id: p4c-margin-health
    content: |
      - [ ] [AGENT] P1. DOC: Update cross-cutting/margin-health.md — add full VaR suite (Historical, Parametric, Cornish-Fisher, CVaR, Stress VaR, Regime-adjusted), pre-trade check engine, circuit breaker + kill switch
    status: todo
  - id: p4d-pnl-attribution
    content: |
      - [ ] [AGENT] P1. DOC: Update cross-cutting/pnl-attribution.md — verify 12 canonical factors match 9+ implemented components, update share class conversion details
    status: todo
  - id: p4e-prediction-markets
    content: |
      - [ ] [AGENT] P1. DOC: Update cross-cutting/prediction-markets.md — promote PredictionArbStrategy to full strategy, document Polymarket CLOB + Kalshi adapters
    status: todo
  - id: p4f-cost-modeling
    content: |
      - [ ] [AGENT] P2. DOC: Update cross-cutting/cost-modeling.md — cross-reference execution-service GasCostModel, BridgeCostModel, InstructionAlphaCalculator
    status: todo
  - id: p4g-latency
    content: |
      - [ ] [AGENT] P2. DOC: Update cross-cutting/latency-profiles.md — add AlgoComparisonRunner benchmarking
    status: todo
  - id: p4h-rate-impact
    content: |
      - [ ] [AGENT] P1. DOC: Update cross-cutting/rate-impact-model.md — document dual-mode design: live simulation (like slippage preview for swaps) + batch mode (defines actual execution prices). Must use actual protocol logic per chain/protocol (Aave interest rate curves, Compound utilisation models, Morpho matching, etc.)
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 5 — SYSTEM: PROMOTE EXISTING STRATEGIES + FACTORY FIX
  # (strategy-service, SEQUENTIAL after Phase 0)
  # ──────────────────────────────────────────────────────────────────────
  - id: p5a-factory-promote
    content: |
      - [ ] [AGENT] P1. CODE: Promote 6 non-default strategies into primary strategy factory in strategy-service — CrossExchangeStrategy, StatArbStrategy, RelVolStrategy, VolSurfaceStrategy, OptionsMMStrategy, PredictionArbStrategy must be discoverable via create_strategy_instance() and --strategies CLI arg
    status: todo
  - id: p5b-omnichain-strategy
    content: |
      - [ ] [AGENT] P1. CODE: Implement OmnichainTransferStrategy in strategy-service wrapping BridgeConnector — on-chain cross-chain transfer as composable strategy primitive. Update defi/omnichain-transfers.md doc in parallel
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 6 — SYSTEM: CENTRALISED PRIMITIVES + EXECUTION HARDENING
  # Architecture: services/modules that ANY strategy can compose
  # ──────────────────────────────────────────────────────────────────────

  # 6A-6D: On-chain primitives
  - id: p6a-rate-impact-engine
    content: |
      - [ ] [AGENT] P0. CODE: Implement RateImpactEngine as centralised service in execution-service (or UTL). Dual-mode: (1) live simulation — given a deposit/borrow amount, return projected rate impact using actual protocol math per chain/protocol (Aave V3 interest rate model, Compound V3 utilisation curve, Morpho Blue matching, Kamino leverage curves). Like slippage preview for swaps but for lending. (2) batch — defines actual execution prices for backtesting. Must import protocol-specific rate curves from UAC or protocol connectors. Every lending/borrowing strategy should call this before execution.
    status: todo
  - id: p6b-lst-collateral-resolver
    content: |
      - [ ] [AGENT] P0. CODE: Implement LSTCollateralResolver as centralised module in execution-service. Given a venue + coin, resolves: (a) does the venue accept LST (stETH, wstETH, mSOL, etc.) as collateral? (b) what's the collateral factor/haircut? (c) decision tree: buy spot on-chain → stake → LST → use as collateral for basis short, OR buy spot → transfer to exchange → use as margin. This affects basis trade capital efficiency (100% collateral utilisation vs 50% or whatever the leverage allows). All basis/staked-basis/recursive strategies must call this resolver. Data source: UAC VenueMapping + protocol reserve configs.
    status: todo
  - id: p6c-onchain-sor-service
    content: |
      - [ ] [AGENT] P1. CODE: Elevate on-chain SOR to a centralised composable service that any strategy can invoke for on-chain execution. Currently SmartOrderRouter is in execution-service algo_library — ensure it's exposed as a strategy-callable service (not just an internal algo). Strategies should be able to say "execute this swap via SOR" or "transfer this on-chain" as atomic instructions without reimplementing routing logic. Cover: DEX swaps, lending deposits/withdrawals, staking, bridging. The execution-service orchestrator may already do this — audit and formalise the interface.
    status: todo
  - id: p6d-strategy-instruction-bus
    content: |
      - [ ] [AGENT] P1. CODE: Formalise strategy instruction types in UAC — strategies emit typed instructions (SWAP, LEND, BORROW, STAKE, BRIDGE, HEDGE_BASIS, REBALANCE_LP, etc.) that execution-service interprets. This decouples strategy logic from execution mechanics. Audit what ExecutionPlan/ExecutionStep/Intent/IntentType already exist in the intent engine and extend to cover all on-chain primitives. Doc: write cross-cutting/strategy-instruction-bus.md
    status: todo

  # 6E-6H: Multi-leg execution hardening
  - id: p6e-liquidity-leg-ordering
    content: |
      - [ ] [AGENT] P0. CODE: Add automatic liquidity-based leg ordering to multi-leg orchestrator in execution-service. For spread/basis/arb strategies: illiquid leg executes first (leader), liquid leg hedges after fill confirmation. Currently LEADER_FOLLOWER mode requires manual leader_leg_index — add a LIQUIDITY_AWARE mode that resolves ordering automatically. Resolution logic: query order book depth or AMM liquidity for each leg's venue+instrument, assign the thinner side as leader. Strategy instructions should be able to tag legs as PRIMARY (illiquid, initiating) vs HEDGE (liquid, compensating) as a hint, but automatic detection should work without hints. Affects: MultiLegInstruction, MultiLegExecutionMode enum, multi_leg_orchestrator. Doc: update or write cross-cutting/multi-leg-execution.md
    status: todo
  - id: p6f-compensation-unwind
    content: |
      - [ ] [AGENT] P0. CODE: Implement compensation/unwind logic for non-atomic multi-leg failures in execution-service. Current gap: if leg 1 fills on Binance but leg 2 fails on Bybit, leg 1's position sits unhedged with no automatic response. Required: (1) On follower failure after leader fill, emit UNHEDGED_POSITION_ALERT event immediately. (2) Auto-retry follower if error is retryable (ErrorAction.RETRY) — configurable max_retries + backoff. (3) If retries exhausted and still unhedged: execute compensation trade to unwind leader leg (market order, same venue, opposite side). (4) If compensation also fails: escalate to kill switch / circuit breaker + CRITICAL alert. Config: max_retry_attempts, retry_backoff_ms, auto_unwind_enabled (default true), max_unwind_slippage_bps. Flash loan legs are already atomic on-chain — this only applies to CeFi/cross-venue non-atomic multi-leg.
    status: todo
  - id: p6g-retry-in-multileg
    content: |
      - [ ] [AGENT] P1. CODE: Wire ErrorAction.RETRY into multi-leg orchestrator in execution-service. Currently classify_venue_error() returns RETRY/SKIP/FAIL but the multi-leg orchestrator doesn't retry — it just cancels followers or stops. Required: (1) On RETRY classification, retry the failed leg with configurable backoff (exponential, capped). (2) On SKIP, mark leg skipped and continue to next (for non-critical legs). (3) On FAIL, trigger compensation logic from p6f. (4) Network errors (timeout, connection reset, RPC unavailable) must always be retryable. (5) Venue-specific errors (insufficient margin, rate limit) get classified per-venue via UAC classify_venue_error(). Affects: multi_leg_orchestrator, instruction_router. Test: add integration test for retry-then-succeed and retry-then-exhaust-then-unwind scenarios.
    status: todo
  - id: p6h-multileg-doc
    content: |
      - [ ] [AGENT] P1. DOC: Write cross-cutting/multi-leg-execution.md — document all 4 execution modes (SEQUENTIAL, LEADER_FOLLOWER, PARALLEL, LIQUIDITY_AWARE), leg tagging (PRIMARY/HEDGE), partial fill thresholds, retry policy, compensation/unwind logic, flash loan atomicity vs CeFi non-atomicity. Reference the strategy instruction bus (p6d) for how strategies declare multi-leg trades.
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 7 — NEW STRATEGIES (backend + docs + UI, PARALLEL)
  # Each item = strategy class + config + doc + UI integration
  # ──────────────────────────────────────────────────────────────────────

  # 7A: Lending Protocol Arb
  - id: p7a-lending-arb-backend
    content: |
      - [ ] [AGENT] P1. CODE: Implement LendingProtocolArbStrategy in strategy-service. Arbs APY spreads across Aave/Morpho/Compound on same chain — borrow cheap on one, lend expensive on another. Must use RateImpactEngine (Phase 6a) for pre-trade simulation. Must support flash-loan-assisted rebalancing. Must compose with recursive staking strategies (deposit LST as collateral, borrow stablecoin, lend elsewhere). Multi-venue SOR for lending (not just swaps). Config: lending_arb_eth.yaml, lending_arb_arbitrum.yaml
    status: todo
  - id: p7a-lending-arb-doc
    content: |
      - [ ] [AGENT] P1. DOC: Write defi/lending-protocol-arb.md — cross-protocol APY arbitrage, flash-loan rebalancing, composable with recursive staking and multi-venue SOR
    status: todo
  - id: p7a-lending-arb-ui
    content: |
      - [ ] [AGENT] P2. UI: Add lending protocol arb to unified-trading-system-ui strategy dashboard — show per-protocol APY spreads, simulated rate impact, rebalancing history. API endpoint in unified-trading-api
    status: todo

  # 7B: Liquidation Cascade Capture
  - id: p7b-liquidation-backend
    content: |
      - [ ] [AGENT] P1. CODE: Implement LiquidationCaptureStrategy in strategy-service. Monitors liquidation_clusters features for cascade risk zones. When cascade triggers, snipes discounted assets post-liquidation. Must use features-cross-instrument liquidation_cluster + liquidation_band_prediction calculators as signal. Execution via SOR (buy discounted assets on DEX or CEX). Risk: position sizing must account for cascade continuation. Config: liquidation_capture_eth.yaml
    status: todo
  - id: p7b-liquidation-doc
    content: |
      - [ ] [AGENT] P1. DOC: Write defi/liquidation-cascade-capture.md — cascade detection, post-liquidation sniping, risk controls
    status: todo
  - id: p7b-liquidation-ui
    content: |
      - [ ] [AGENT] P2. UI: Add liquidation monitoring to unified-trading-system-ui — real-time liquidation heatmap/cascade risk zones, position entry/exit overlay. API endpoint in unified-trading-api
    status: todo

  # 7C: Enhanced Basis Trade (cross-venue + cross-coin + LST collateral)
  - id: p7c-enhanced-basis-backend
    content: |
      - [ ] [AGENT] P1. CODE: Enhance BasisTradeStrategy (and variants) in strategy-service to support: (1) cross-coin basket — select coins by funding rate across BTC/ETH/SOL/etc., rank by yield. (2) cross-venue basket — select venues by funding rate for same coin (Binance vs Bybit vs Hyperliquid vs Drift). (3) LST collateral decision via LSTCollateralResolver (Phase 6b) — automatically decide whether to stake spot → LST → use as collateral vs direct spot margin. (4) Bidirectional funding — handle both positive and negative funding, long or short basis depending on direction. Config: basis_trade_multi_venue.yaml, basis_trade_multi_coin.yaml
    status: todo
  - id: p7c-enhanced-basis-doc
    content: |
      - [ ] [AGENT] P1. DOC: Update defi/basis-trade.md — add cross-venue, cross-coin, LST collateral decision tree, bidirectional funding sections. This is NOT a new strategy but an enhancement to the existing one
    status: todo
  - id: p7c-enhanced-basis-ui
    content: |
      - [ ] [AGENT] P2. UI: Enhance basis trade dashboard in unified-trading-system-ui — funding rate heatmap (coin × venue matrix), LST collateral utilisation indicator, cross-venue allocation view. API endpoint in unified-trading-api
    status: todo

  # 7D: Active DeFi Market Making (ML-driven LP rebalancing)
  - id: p7d-active-lp-backend
    content: |
      - [ ] [AGENT] P1. CODE: Implement ActiveDeFiMMStrategy in strategy-service (or enhance AmmLPStrategy). ML-driven concentrated LP rebalancing on Uniswap V3 / Raydium / Orca. ML model predicts optimal rebalance timing to minimise impermanent loss — uses features from features-delta-one (momentum, microstructure) + features-volatility (vol regime, VRP) + features-onchain (pool state, TVL). Rebalance decisions: widen/narrow range, shift range, full exit. Must use on-chain SOR for rebalancing execution. Config: active_lp_eth_usdc.yaml, active_lp_sol_usdc.yaml
    status: todo
  - id: p7d-active-lp-doc
    content: |
      - [ ] [AGENT] P1. DOC: Write defi/active-defi-mm.md — ML-driven LP rebalancing, impermanent loss minimisation, concentrated liquidity range management
    status: todo
  - id: p7d-active-lp-ui
    content: |
      - [ ] [AGENT] P2. UI: Add active LP dashboard to unified-trading-system-ui — LP position ranges visualisation, IL tracking, rebalance history, ML confidence for rebalance decisions. API endpoint in unified-trading-api
    status: todo

  # 7E: Event-Driven Macro
  - id: p7e-event-macro-backend
    content: |
      - [ ] [AGENT] P1. CODE: Implement EventDrivenMacroStrategy in strategy-service. Consumes features-calendar-service outputs (CPI, FOMC, NFP, earnings) as trade triggers. Pre-event positioning based on ML predictions of event impact. Post-event momentum capture. Must work across CeFi (BTC/ETH reaction to macro) and TradFi (SPY, FX, commodities). Already input to ML features — this strategy makes it the primary signal rather than one of many. Config: event_macro_crypto.yaml, event_macro_tradfi.yaml
    status: todo
  - id: p7e-event-macro-doc
    content: |
      - [ ] [AGENT] P1. DOC: Write cross-cutting/event-driven-macro.md — event calendar triggers, pre/post-event positioning, cross-domain (crypto + tradfi)
    status: todo
  - id: p7e-event-macro-ui
    content: |
      - [ ] [AGENT] P1. UI: Add news/events feed to unified-trading-system-ui — economic calendar with countdown timers, event impact predictions, manual trade placement based on signals/analytics/news. News feed panel (economic events, earnings, on-chain governance proposals). API: events endpoint in unified-trading-api serving features-calendar-service data
    status: todo

  # 7F: Commodity Regime Trading
  - id: p7f-commodity-backend
    content: |
      - [ ] [AGENT] P1. CODE: Implement CommodityRegimeStrategy in strategy-service. Uses features-commodity-service HMM regime detector + 5 factors (rig count, COT positioning, storage, price momentum, weather). Regime-conditional positioning: trend-follow in trending regimes, mean-revert in range. Execution via IBKR CME adapter for commodity futures. Config: commodity_regime_oil.yaml, commodity_regime_natgas.yaml
    status: todo
  - id: p7f-commodity-doc
    content: |
      - [ ] [AGENT] P1. DOC: Write tradfi/commodity-regime.md — HMM regime detection, 5-factor model, regime-conditional execution
    status: todo
  - id: p7f-commodity-ui
    content: |
      - [ ] [AGENT] P2. UI: Add commodity regime dashboard to unified-trading-system-ui — regime state indicator, factor decomposition chart, COT positioning heat map. API endpoint in unified-trading-api
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 8 — QUALITY GATES
  # ──────────────────────────────────────────────────────────────────────
  - id: p8a-qg-pm
    content: |
      - [ ] [AGENT] P0. Run quality-gates.sh on unified-trading-pm after all doc changes
    status: todo
  - id: p8b-qg-strategy
    content: |
      - [ ] [AGENT] P0. Run quality-gates.sh on strategy-service after factory promotion + new strategies
    status: todo
  - id: p8c-qg-execution
    content: |
      - [ ] [AGENT] P0. Run quality-gates.sh on execution-service after centralised primitives
    status: todo
  - id: p8d-qg-features
    content: |
      - [ ] [AGENT] P0. Run quality-gates.sh on features-onchain-service after rate impact engine
    status: todo
  - id: p8e-qg-uac
    content: |
      - [ ] [AGENT] P0. Run quality-gates.sh on unified-api-contracts after instruction types
    status: todo
  - id: p8f-qg-ui
    content: |
      - [ ] [AGENT] P0. Run quality-gates.sh on unified-trading-system-ui after all UI additions
    status: todo
  - id: p8g-qg-api
    content: |
      - [ ] [AGENT] P0. Run quality-gates.sh on unified-trading-api after all API additions
    status: todo

isProject: false
---

# Strategy Docs vs System Audit — 2026-04-15

## Context

Full audit of `codex/09-strategy/` documentation against the actual backend system. The system has **59 strategy
implementations** across 4 domains; the docs cover **37 strategies** with many stubs and missing files. This plan closes
every gap in both directions, adds new strategies for untapped potential, and introduces centralised on-chain primitives
that any strategy can compose.

## Audit Findings Summary

| Category      | Docs                                        | System                                    | Gap                                         |
| ------------- | ------------------------------------------- | ----------------------------------------- | ------------------------------------------- |
| DeFi          | 6 real docs + 11 referenced-no-file         | 18 strategies + 21 protocol connectors    | 12 docs to write + 4 new strategies         |
| CeFi          | 1 real doc + 2 stubs                        | 12 strategies (9 default + 3 non-default) | 3 stubs to complete + 3 new docs            |
| TradFi        | 1-2 real docs + 4 referenced-no-file        | 8 strategies + IBKR (6 venues)            | 4 docs to write + 1 new strategy            |
| Sports        | 3 real docs + 1 stub + 2 referenced-no-file | 6 strategies + 6 betting venues           | 1 stub + 2 new docs                         |
| Prediction    | 1 cross-cutting mention                     | 1 strategy + 2 venues                     | 1 new directory + doc                       |
| Cross-cutting | 15 docs (all substantive)                   | Full risk/ML/execution/PnL infra          | 9 docs to update + 4 centralised primitives |

## Human Decisions (2026-04-15, all resolved)

1. **Omnichain transfers** → Implement OmnichainTransferStrategy wrapping BridgeConnector
2. **Rate impact model** → Dual-mode: live simulation (like slippage preview for swaps) + batch (actual execution
   prices). Must use actual protocol math per chain/protocol
3. **Lending protocol arb** → Yes. Must compose with recursive staking + multi-venue SOR
4. **Liquidation cascade capture** → Yes
5. **Cross-exchange funding rate arb** → Not a new strategy. Enhance existing basis trade to support cross-venue +
   cross-coin baskets + LST collateral decision
6. **Active DeFi MM** → Yes. ML-driven rebalancing to minimise impermanent loss
7. **Event-driven macro** → Yes. UI needs news/events feed for manual trading on signals. Backend uses calendar features
   as primary trigger
8. **Commodity regime trading** → Yes. HMM regime + 5 factors. IBKR CME execution

## Architectural Principle: Centralised Primitives

**Key insight 1:** On-chain operations (SOR, transfers, LST collateral resolution, rate impact simulation) must be
**centralised services** that any strategy can compose, not reimplemented per strategy.

**Key insight 2:** Multi-leg execution must be safe by default. Illiquid leg first, liquid hedge after. Retries for
transient errors. Automatic compensation/unwind if hedge leg fails after primary fills. No unhedged positions left
silently.

| Primitive                              | Location                                 | Used by                                                              |
| -------------------------------------- | ---------------------------------------- | -------------------------------------------------------------------- |
| RateImpactEngine                       | execution-service or UTL                 | All lending/borrowing strategies                                     |
| LSTCollateralResolver                  | execution-service                        | All basis/staked-basis/recursive strategies                          |
| On-chain SOR service                   | execution-service (formalise existing)   | All DeFi strategies needing swaps/transfers                          |
| Strategy Instruction Bus               | UAC types + execution-service            | All strategies (typed instructions: SWAP, LEND, STAKE, BRIDGE, etc.) |
| Liquidity-aware leg ordering           | execution-service multi-leg orchestrator | All spread/basis/arb strategies                                      |
| Compensation/unwind on partial failure | execution-service multi-leg orchestrator | All non-atomic multi-leg trades                                      |
| Retry policy in multi-leg              | execution-service multi-leg orchestrator | All multi-leg trades                                                 |

## Multi-Leg Execution: Current State vs Target

**What exists:**

- 3 execution modes: SEQUENTIAL, LEADER_FOLLOWER (configurable leader index + partial fill threshold), PARALLEL
- DeFi flash loan atomicity (all-or-nothing on-chain tx revert)
- Error classification: RETRY/SKIP/FAIL via UAC `classify_venue_error()`
- 13 DeFi error codes from revert reasons
- Intent engine with `depends_on` dependency DAG + `multicall_group` batching

**What's missing (Phase 6E-6H):**

- No automatic liquidity-based leg ordering (strategy must manually set leader_leg_index)
- No compensation/unwind when leg 1 fills but leg 2 fails in non-atomic (CeFi) mode
- Retry classification exists but isn't wired into multi-leg orchestrator flow
- No PRIMARY/HEDGE leg tagging in strategy instructions

## Execution DAG

```
Phase 0: Index + Catalog update ──────────────────────────────────────────────┐
    │                                                                          │
Phase 1: Complete 3 stubs ─── PARALLEL                                        │
Phase 2: Write 10 missing docs ─── PARALLEL                                   │
Phase 3: Write 12 DeFi variant docs ─── PARALLEL                              │
Phase 4: Update 9 cross-cutting docs ─── PARALLEL                             │
    │                                                                          │
    ├── All doc phases are PARALLEL with each other AND with Phase 5/6 ────────┘
    │
Phase 5: Promote 6 strategies + implement OmnichainTransferStrategy ─── strategy-service
    │
Phase 6: Centralised primitives + execution hardening ─── MIXED
    │   6a: RateImpactEngine (prerequisite for 7a, 7c)
    │   6b: LSTCollateralResolver (prerequisite for 7c)
    │   6c: On-chain SOR service formalisation
    │   6d: Strategy Instruction Bus (UAC types, prerequisite for 6e leg tagging)
    │   6e: Liquidity-aware leg ordering (PARALLEL with 6a-6c)
    │   6f: Compensation/unwind on partial failure (depends on 6g for retry)
    │   6g: Retry policy wired into multi-leg orchestrator (PARALLEL with 6e)
    │   6h: Doc: cross-cutting/multi-leg-execution.md (after 6e-6g)
    │
Phase 7: New strategies (backend + doc + UI per strategy) ─── PARALLEL
    │   7a: LendingProtocolArb (depends on 6a)
    │   7b: LiquidationCascadeCapture
    │   7c: Enhanced Basis Trade (depends on 6a, 6b, 6e for leg ordering)
    │   7d: ActiveDeFiMM
    │   7e: EventDrivenMacro (+ UI news feed)
    │   7f: CommodityRegime
    │
Phase 8: Quality gates — all affected repos
```

**Phases 1-4 + Phase 5 + Phase 6 run in PARALLEL** (doc writes don't block code). **Phase 6e-6g are PARALLEL** with
6a-6d (different parts of execution-service). **Phase 7 items are PARALLEL** except 7a depends on 6a, 7c depends on
6a+6b+6e.

## Repos Affected

| Repo                      | Change type                                                  | Phase |
| ------------------------- | ------------------------------------------------------------ | ----- |
| unified-trading-pm        | ~35 doc files in codex/09-strategy/                          | 0-4   |
| strategy-service          | Factory promotion + 7 new strategy classes                   | 5, 7  |
| execution-service         | RateImpactEngine, LSTCollateralResolver, SOR formalisation   | 6     |
| unified-api-contracts     | Strategy instruction types (IntentType extensions)           | 6d    |
| unified-trading-library   | RateImpactEngine if placed here instead of execution-service | 6a    |
| features-onchain-service  | Rate impact live mode if needed                              | 6a    |
| unified-trading-system-ui | 6+ new dashboard panels, news/events feed                    | 7     |
| unified-trading-api       | 6+ new API endpoints for strategy dashboards                 | 7     |

## Doc Writing Guidelines

All new strategy docs MUST follow `templates/strategy-description-template.md` (20-section template). Key sections:

- Overview, Token/Position Flow, Instruments table, Key Features Consumed, PnL Attribution, Risk Profile
- **Source content from the actual strategy class implementation** — read the code, don't guess
- Cross-reference execution adapters, feature services, risk checks, and centralised primitives
- For new strategies (Phase 7): write doc concurrently with implementation, doc describes target state
