---
name: frontend-backend-bilateral-plan4-strategy-type-completion
overview:
  Wire orphaned strategy code, complete DeFi/sports/ML type usage, export undocumented strategies, connect risk profiles
type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-api-contracts
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
  - repo: risk-and-exposure-service
    code: C0
    deployment: none
    business: none
  - repo: ml-inference-service
    code: C0
    deployment: none
    business: none
  - repo: ml-training-service
    code: C0
    deployment: none
    business: none
  - repo: features-sports-service
    code: C0
    deployment: none
    business: none
  - repo: features-onchain-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

depends_on: []

todos:
  - id: p4-0-pre-audit
    content: |
      - [ ] [AGENT] P0. Pre-audit: Build a manifest of every "dead" UAC/UIC type that maps to a planned strategy. For each dead type, determine:
        1. Is it referenced in a codex/09-strategy/ doc? → COMPLETE (wire it)
        2. Is it referenced in an active plan? → COMPLETE (wire it)
        3. Is it in representative_sample.py? → KEEP (test fixture)
        4. Is it from a venue that's been removed (Elysium, Arkham, Bloxroute, Pyth, Infura)? → DELETE
        5. Is it superseded by a canonical type? → DELETE
        6. Otherwise → review case by case
      Output: a table in the plan notes mapping each dead type to its disposition (COMPLETE/KEEP/DELETE).
    status: todo
  - id: p4-1-defi-protocol-types
    content: |
      - [ ] [AGENT] P0. Wire DeFi protocol parameter types that are dead but needed by documented strategies:
        1. **Aave V3**: AaveBorrowParams, AaveDepositParams, AaveFlashLoanParams, AaveRepayParams — used by DEFI_LENDING_AAVE_1H and DEFI_RECURSIVE_BASIS_ETH_1H strategies. Wire into execution-service DeFi connector so these types are actually used in the lend/borrow/flash-loan code paths.
        2. **Morpho**: MorphoBorrowParams, MorphoSupplyParams, MorphoRepayParams, MorphoFlashLoanParams, MorphoMarketParams — Morpho lending is documented in codex; wire into execution-service morpho connector.
        3. **Curve**: CurveSwapParams, CurveDepositParams, CurveWithdrawParams — Curve is a documented venue; wire into execution-service DEX routing.
        4. **Lido**: LidoSubmitParams, LidoSubmitResponse, LidoRequestWithdrawalsParams, LidoWstEthWrapResponse — staking strategy documented; wire into staking connector.
        5. **EtherFi**: EtherFiStakeResponse, EtherFiUnstakeResponse — wire into staking connector.
        6. **Uniswap V3**: UniswapV3PoolStateResponse, UniswapV3QuoteResponse, UniswapV3SwapTxReceipt — wire into Uniswap connector (may already be partially wired).
        Pre-audit each: search for existing usage, don't duplicate. If connector exists but doesn't use the type, update connector. If connector doesn't exist, create minimal connector using the type.
    status: todo
  - id: p4-2-defi-constants
    content: |
      - [ ] [AGENT] P1. Wire DeFi constants that are dead but needed:
        1. DEFI_INSTRUMENTS — ensure instruments-service DeFi adapters use this
        2. DEFI_LENDING_ASSETS — ensure lending strategies reference this
        3. DEFI_MAJOR_ASSET_ADDRESSES, DEFI_MAJOR_ASSET_SYMBOLS — ensure execution-service DeFi routing uses these
        4. DEX_VENUES, DEX_VENUE_KEYWORDS — ensure venue classification uses these
        If these are superseded by the new InstrumentDomainConfig.defi_major_assets pattern, update references to use the new pattern and mark old constants for deletion in Plan 5.
    status: todo
  - id: p4-3-sports-types
    content: |
      - [ ] [AGENT] P0. Wire sports types that are dead but needed by documented strategies:
        1. **Betfair**: BetfairCurrentOrderSummary, BetfairListCurrentOrdersResponse, BetfairMarketCatalogue, BetfairRunnerCatalog — needed by SPORTS_ARBITRAGE_CROSS_BOOK and SPORTS_MARKET_MAKING. Wire into execution-service sports adapters.
        2. **Sports betting**: CanonicalBetMarket, CanonicalBetOrder, CanonicalComboBet, CanonicalComboLeg — canonical types for the sports execution pipeline. Wire into sports strategy → execution flow.
        3. **Bookmaker**: BookmakerInfo, BookmakerRegistry, BucketMarket — needed by sports feature calculation and arb detection. Wire into features-sports-service.
        4. **AsterExchangeInfo** — Aster is a documented CeFi venue; if still supported, wire it.
        Cross-reference with active sports plans (sports_integration_01-06, sports_batch_pipeline, sports_e2e_validation).
    status: todo
  - id: p4-4-strategy-export-wiring
    content: |
      - [ ] [AGENT] P0. Wire orphaned strategy implementations in strategy-service:
        1. **Cross-exchange arb** (cross_exchange_strategy.py) — orphaned, documented in codex. Export and register in strategy manifest.
        2. **Relative vol** (rel_vol_strategy.py) — orphaned, documented. Export and register.
        3. **Statistical arb** (stat_arb_strategy.py) — orphaned, documented. Export and register.
        4. **Vol surface** (vol_surface_strategy.py) — orphaned, documented. Export and register.
        5. **Sports strategies** (sports/ directory) — backtest engine, venue allocator orphaned. Wire into sports execution flow.
        6. **Options market making** (options_market_making/) — orphaned, documented in codex. Export and register.
        7. **TradFi ML directional** (tradfi_ml/) — variant exists but not exported. Export.
        For each: (a) add to strategy-service `__init__.py` exports, (b) add to system-topology.json if missing, (c) verify the strategy can instantiate without import errors, (d) add minimal unit test.
    status: todo
  - id: p4-5-risk-profile-wiring
    content: |
      - [ ] [AGENT] P1. Wire StrategyRiskProfile from UIC into actual usage:
        1. The codex alignment doc says "risk subscriptions implicit in code" — make them explicit
        2. Each strategy config should declare a StrategyRiskProfile with: target return, max drawdown, max leverage, risk subscriptions
        3. Wire risk-and-exposure-service to read strategy risk profiles and enforce limits
        4. Ensure the risk API endpoints can return per-strategy risk status
    status: todo
  - id: p4-6-ml-monitoring-types
    content: |
      - [ ] [AGENT] P1. Wire ML monitoring types that are marked dead:
        1. MLModelScorecard — wire into ml-inference-service model evaluation pipeline
        2. MLPrediction — ensure this is used in the inference response path (not just training)
        3. Connect to the monitoring endpoint added in Plan 3 (p3-7)
        4. Ensure model drift detection uses proper typed schemas from UAC
    status: todo
  - id: p4-7-cefi-order-types
    content: |
      - [ ] [AGENT] P1. Wire CeFi order/position types that are dead in UIC:
        1. CeFiOpenOrder, CeFiOrderFill, CeFiOrderStatus, CeFiVenueOrderData, CeFiVenuePosition — these are internal types for CeFi execution state. Wire into execution-service CeFi adapters and position-balance-monitor-service.
        2. OptionContract, OrderBookSnapshot — wire into derivatives pipeline if options strategies use them.
        Pre-audit: check if these are superseded by canonical types (CanonicalOrder, CanonicalFill, etc.). If superseded, mark for deletion instead.
    status: todo
  - id: p4-8-trigger-subscriptions
    content: |
      - [ ] [AGENT] P2. Implement formal trigger subscription schema for strategies:
        1. The alignment doc says "engine passes ALL features through today" — wasteful
        2. Each strategy config should declare which feature groups it subscribes to (per codex docs)
        3. Wire strategy-service to filter features based on subscription before passing to strategy
        4. Use typed FeatureSubscription schema from UAC (create if it doesn't exist)
    status: todo
  - id: p4-9-codex-alignment-update
    content: |
      - [ ] [AGENT] P1. Update codex/09-strategy/ documentation:
        1. Update STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md with current state after wiring
        2. Add missing strategies to the README index (cross-exchange, rel-vol, stat-arb, vol-surface, options MM)
        3. Mark Solana/BTC/Multi-chain DeFi strategies as status: "Documented — not yet implemented" (don't pretend they're done)
        4. Update each strategy doc's status field to match reality
    status: todo
  - id: p4-10-tests-qg
    content: |
      - [ ] [AGENT] P0. Run QG on all affected repos. For each newly exported strategy, verify:
        1. Strategy class can be instantiated without import errors
        2. Strategy appears in `GET /analytics/strategies` response
        3. DeFi protocol types are used in at least one code path
        4. Sports types are used in at least one code path
        5. No regressions in existing tests
        QG: unified-api-contracts, strategy-service, execution-service, risk-and-exposure-service, ml-inference-service, ml-training-service, features-sports-service, features-onchain-service
    status: todo
---

## Context

### Problem

169 types are marked DEAD in the type usage audit. But many of these are needed by documented strategies that haven't
been fully wired:

- **30 DeFi protocol param types** (Aave, Morpho, Curve, Lido, EtherFi, Uniswap) — documented strategies exist in
  codex/09-strategy/ but execution connectors don't use the typed params
- **15 sports/betting types** — 6 sports strategies documented but types orphaned
- **7 strategy implementations** in strategy-service exist as code but aren't exported
- **ML monitoring types** exist but aren't wired to endpoints
- **Risk profile types** defined but not enforced
- **CeFi order types** may be superseded or needed

The audit revealed strategy-service has only 9 reachable modules out of 164 (5%!). Most strategy code is orphaned — not
because it's abandoned, but because only the lean orchestrator path is wired.

### Pre-Audit Manifest

Task p4-0 builds the definitive manifest mapping each dead type to COMPLETE/KEEP/DELETE disposition. This manifest is
the input to Plan 5 (cleanup) — Plan 5 only deletes types marked DELETE here.

### Execution DAG

```
Phase 1 (SEQUENTIAL):
  p4-0: Pre-audit manifest

Phase 2 (PARALLEL, depends on Phase 1):
  p4-1: DeFi protocol types wiring
  p4-3: Sports types wiring
  p4-4: Strategy export wiring
  p4-7: CeFi order types wiring

Phase 3 (PARALLEL, depends on Phase 2):
  p4-2: DeFi constants
  p4-5: Risk profile wiring
  p4-6: ML monitoring types
  p4-8: Trigger subscriptions

Phase 4 (PARALLEL, depends on Phase 3):
  p4-9: Codex alignment update

Phase 5 (SEQUENTIAL, depends on Phase 4):
  p4-10: QG on all repos
```

### Success Criteria

- **C2**: Every dead type has a disposition (COMPLETE/KEEP/DELETE). Completed types are used in at least one code path.
  Tests pass.
- **C3**: basedpyright + ruff clean
- **C4**: QG pass on all 9 repos
- **C5**: Quickmerged
