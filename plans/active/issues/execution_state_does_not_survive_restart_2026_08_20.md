---
doc_type: issue
title: Execution-service cannot survive a restart with state intact — orders, positions, PnL and fills are all in-memory-only, and the one recovery component built for it is unwired
summary: >-
  Measured 2026-08-20: `InMemoryOrderPersistence` / in-memory position tracking are hardcoded in
  `engine/live/factory.py`, the `PostgreSQLOrderPersistence` alternative raises `NotImplementedError` from every real
  method and is not even offered by the factory, and `OrderRecoveryEngine` — the component built to reconcile surviving
  venue orders on startup — has zero production instantiations despite a `--skip-recovery` CLI flag and a docstring
  claiming it runs. A live process restart therefore loses the order book, positions, realised PnL and fee/funding
  accruals, with no venue reconciliation to rebuild them. This is a precondition for live capital, not a recovery-plane
  nicety.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    execution,
    durability,
    funds-safety,
    unwired-code,
    recovery,
    restart,
    reconciliation,
    epoch-fencing,
  ]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/04-architecture/cross-domain-state-fabric.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /plans/active/issues/health_factor_monitor_no_production_entrypoint_liquidation_unprotected_2026_08_19.md,
    /plans/epics/system_readiness_master.md,
  ]
context_scope:
  [
    execution-service/execution_service/engine/live/factory.py,
    execution-service/execution_service/engine/live/persistence/postgresql.py,
    execution-service/execution_service/engine/startup/order_recovery.py,
    execution-service/execution_service/pre_crash_checkpoint.py,
    execution-service/execution_service/services/account_history_client.py,
  ]
created: 2026-08-20
last_updated: "2026-08-20"
parent_epic: system_readiness_master
assigned_vm: NA
locked_by:
locked_since:
resolved_by:
execution_scope: local-only
priority: P0
severity: P0
source: >-
  Sonnet-5 sub-agent measurement audit dispatched 2026-08-20 against an external batch/paper/live recovery-plane
  architecture proposal. The audit was asked "what exists today" per claim; these findings are what it measured, with
  its own uncertainty flags preserved below.
drift_direction: advance-code
depends_on: []
---

# A restart loses the book

## The single sentence

**Kill an execution-service process today and the orders, positions, realised PnL, partial fills, fee and funding
accruals all go with it — and nothing queries the venue to rebuild them.**

## Measured 2026-08-20

| Finding                                                                                                              | Evidence                                                                                                                        |
| -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Order + position persistence is **in-memory only, and hardcoded**                                                     | `engine/live/factory.py:20-23 create_oms()` constructs `InMemoryOrderPersistence`; `factory.py:48-52` the same for positions       |
| The Postgres alternative is a **stub that would crash if selected**                                                    | `engine/live/persistence/postgresql.py` — every real method (`save_order`, `get_order`, `update_order_status`, `get_all_orders`, `get_orders_by_status`, `get_orders_by_strategy`, `save_position`, `get_position`, `get_all_positions`) raises `NotImplementedError`; the factory does not offer it as an option |
| `OrderRecoveryEngine` has **zero production call sites**                                                              | `rg 'OrderRecoveryEngine\('` → hits only in `tests/unit/engine/test_order_recovery.py` and `tests/unit/test_order_recovery.py`     |
| **CORRECTION 2026-08-21 (class-enumeration todo, batch21 item 4)**: this row is now STALE. `cli/handlers/live_execution_handler.py:209-212 _create_startup_order_recovery()` constructs `OrderRecoveryEngine(order_book=..., venue_adapter=_VenueAdapter())` and IS called from `_run_startup_order_recovery()` (line 214), which is itself called at line 136 — a real, reachable production call site, not a dead declaration. Left in place per this doc's own append-only convention rather than edited; see the full class-enumeration findings below for the mechanical check this correction came from. | verified 2026-08-21, direct read of `live_execution_handler.py:136,189-222` |
| Its default venue adapter is an **explicit stub**                                                                     | `engine/startup/order_recovery.py:136-168` — `fetch_open_orders` returns `[]`; `cancel_order`/`confirm_cancel` always return `True` |
| The `--skip-recovery` flag's attribute is **never read**                                                              | `cli/argument_parser.py:183` defines it; `rg skip_recovery` → 0 reads. `cli/main.py:10-12` docstring claims the engine runs in live mode |
| `pre_crash_checkpoint.py` contains **no state serialization**                                                          | 101 lines: a SIGTERM handler + an 85%-RSS watchdog, both converging on one `logger.critical`, one `log_event`, `sys.exit()`. Nothing reads it back |
| Funding reconciliation **can never succeed**                                                                          | `providers/account_history_client.py` — `get_fill_fees` / `get_funding_payments` unconditionally `return []`; no subclass override found. `services/funding_recon_engine.py` therefore always reports PENDING |
| **No epoch fencing** on the order path                                                                                | searched `epoch\|fenc(e\|ing)\|lease\|generation_id\|instance_generation` across `engine/`, `orders/`, `orchestration/`, `api/` → zero hits |

## Why this is P0 and not an architecture improvement

The recovery-plane work this audit was scoping is a **design** question. This is not. Real capital plus an
in-memory-only order book means an ordinary deploy, an OOM kill, or a preemption leaves live orders resting at a venue
that the restarted process does not know exist, cannot cancel, and will not reconcile. The
[autonomous recovery matrix](/codex/04-architecture/autonomous-recovery-matrix.md) explicitly warns that "simply
stopping downstream processing is dangerous if it leaves live orders resting" — that is precisely the state a restart
produces today.

**This is the FOURTH instance of one pattern**, and that is now the finding rather than a coincidence: substantial,
tested code with no production entry point, where a spot-check of the class itself looks healthy.
`TransferCoordinator`, `HealthFactorMonitor`, `QuoteHandler` (deleted 2026-08-15), and now `OrderRecoveryEngine` —
which is worse than the others because a CLI flag and a docstring both actively assert it runs.

## Todos

- [ ] [BACKEND] P0. **Make order and position state durable before any live capital.** Either implement
      `PostgreSQLOrderPersistence` properly and offer it from `create_oms()`, or replace the persistence protocol with
      something that is durable by construction. Do NOT leave a `NotImplementedError` stub reachable by config — a
      `USE_DATABASE=true` that crashes on first save is worse than no option at all.
- [ ] [BACKEND] P0. **Wire `OrderRecoveryEngine` into the live startup path with a real venue adapter.** A component
      that a CLI flag and a docstring both claim runs, and which does not, is worse than an absent one — it defeats the
      check a reader would make. **Deleting it is NOT an option** (operator ruling R20, 2026-08-20): removing the
      declaration would satisfy any gate while moving the platform further from target state. The same applies to
      `PostgreSQLOrderPersistence` and to the unused `RedisStreamTransport` — build what is declared.
- [ ] [BACKEND] P0. **Make `--skip-recovery` do something or remove it.** Its attribute is defined and never read.
- [ ] [BACKEND] P1. **Implement `AccountHistoryClient` per venue, or make its emptiness loud.** Returning `[]`
      unconditionally means funding reconciliation reports PENDING forever and never fails — the same silent-plausible
      -default shape as `get_venue_asset_group()` returning `"cefi"`.
- [ ] [BACKEND] P1. **Add epoch fencing to the order path** so a superseded instance cannot keep submitting. Nothing
      currently prevents two live instances both sending orders.
- [x] ✅ [REVIEW] P1. **EXTRACTED 2026-08-21** — rename or gut `pre_crash_checkpoint.py`. Extracted to
      `cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md` for AO dispatch (na-eligibility-audit,
      cross-cutting tranche, batch 2 of 3).
- [x] ✅ [AGENT] P1. **EXTRACTED 2026-08-21** — enumerate execution-service classes with tests but no non-test
      instantiation. Extracted to `cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md` for AO dispatch
      (na-eligibility-audit, cross-cutting tranche, batch 2 of 3).
- [ ] [REVIEW] P2. **Triage the ~155 untriaged rows in the 2026-08-21 class-enumeration findings** (above) —
      per-class verdict of genuinely declared-but-unwired vs. a false positive from dynamic construction (dispatch
      dict, `getattr`, DI, `.from_x()` classmethod) the AST call-site scan cannot see. Not done in the enumeration
      pass itself, which was scoped to report-only per its own source todo.
- [x] ✅ [REVIEW] P2. **EXTRACTED 2026-08-21** — close the audit's own open questions (read `engine/orphan_monitor.py`,
      `venue_failover.py`, `venue_cascade_monitor.py`, `manual_pending_queue.py`, `order_rejection_tracker.py`,
      `utils/fidelity_selector.py`, `trade_execution/adapters/_rate_limit.py`,
      `sports_execution/monitoring/venue_health.py:23 VenueHealthStatus` in full). Extracted to
      `cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md` for AO dispatch (na-eligibility-audit,
      cross-cutting tranche, batch 2 of 3).

## Findings — execution-service classes with tests but zero non-test instantiation (2026-08-21)

Batch21 item 4 (`cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md`), source: this doc's "Enumerate
execution-service classes with tests but no non-test instantiation" todo. Report only, per that todo's own scope — no
findings below were fixed.

**Method**: AST-based (not regex — avoids the workspace's banned `python3 << EOF`/backtracking-regex class of
failure), walking every `.py` file under `execution-service/` (excluding `.venv`/`node_modules`/`.git`/`__pycache__`/
`build`/`dist`/`.eggs`). A "production class" is any `class` definition appearing in at least one non-test file
(`tests/` anywhere in the path, or a `test_*.py`/`*_test.py` basename, counts as test). "Has tests" = the class is
the target of at least one `ast.Call` (constructor call) inside a test file. "Zero non-test instantiation" = zero
`ast.Call` sites (by bare name or attribute access) outside test files, repo-wide — this intentionally matches the
issue's own worked examples (`TransferCoordinator`, `HealthFactorMonitor`, `OrderRecoveryEngine` before its fix) where
the check that matters is "does anything besides a test construct this."

**Caveats (mechanical check, not a manual triage — read before acting on any single row)**:

- Dynamic construction the AST call-site scan cannot see (a dispatch/factory dict keyed by string, `getattr`-based
  construction, dependency injection via a framework) will show as "zero instantiation" even when the class is real
  and live. Confirm before treating any single entry as "genuinely unwired" — this list is a lead, not a verdict.
- Many `dataclass`/`NamedTuple`/exception/enum/`Protocol` entries are expected to show 0 non-test instantiation by
  design (a `Protocol` is never directly constructed; some dataclasses are only ever produced via `**dict` unpacking
  or `.from_x()` classmethods, which this scan does not attribute back to the class name).
- "Has tests" only requires a `Call` node targeting the class name somewhere under `tests/` — it does not confirm the
  test actually exercises meaningful behavior.
- `TransferCoordinator` and `QuoteHandler` (both cited in this doc's "fourth instance" framing) do not appear below:
  `TransferCoordinator` is not defined anywhere in `execution-service` (it lives in a different repo per
  `/codex/04-architecture/client-funds-isolation.md`), and `QuoteHandler` was deleted 2026-08-15 (confirmed absent).
  `OrderRecoveryEngine` also does not appear — see the CORRECTION row above the findings table: it now has a real
  production call site, so it correctly fails the "zero non-test instantiation" filter today.

**Totals**: 916 production classes found repo-wide; 629 have at least one test-side constructor call; 521 have at
least one non-test constructor call; **161 have tests but zero non-test instantiation** (full list below,
`ClassName  defined_at=<file>:<line>[; <file>:<line> for a duplicate name]  test_instantiation_sites=<count>`):

```
AccountHistoryClient	defined_at=execution_service/services/account_history_client.py:48	test_instantiation_sites=4
AdaptiveTWAPExecAlgorithm	defined_at=execution_service/algorithms/impl/adaptive_twap.py:66	test_instantiation_sites=1
AggregatorRouteMatcher	defined_at=execution_service/matching_engine/aggregator.py:100	test_instantiation_sites=5
AlgoComparisonRunner	defined_at=execution_service/algo_library/algo_comparison.py:85	test_instantiation_sites=6
AlgoConfig	defined_at=execution_service/algo_library/schemas.py:19	test_instantiation_sites=2
AlgorithmFactory	defined_at=execution_service/adapters/algorithm_factory.py:12; execution_service/engine/interfaces.py:43	test_instantiation_sites=5
AlmgrenChrissSweepResult	defined_at=execution_service/engine/backtest/almgren_chriss_sweep.py:28	test_instantiation_sites=1
AnalogExecutionGate	defined_at=execution_service/engine/risk/analog_execution_gate.py:93	test_instantiation_sites=13
AnalogRecord	defined_at=execution_service/engine/risk/analog_execution_gate.py:49	test_instantiation_sites=1
ApiFootballAdapter	defined_at=execution_service/sports_execution/adapters/bookmaker_api/api_football.py:148	test_instantiation_sites=8
AssetParameters	defined_at=execution_service/governance/proposal_simulator.py:53	test_instantiation_sites=3
AsterConnector	defined_at=execution_service/defi_execution/protocols/aster.py:158	test_instantiation_sites=26
AtomicBundleExecutor	defined_at=execution_service/algorithms/atomic_bundle_executor.py:24	test_instantiation_sites=15
BacktestDataError	defined_at=execution_service/cli/exceptions.py:14	test_instantiation_sites=3
BalancerBoostedPool	defined_at=execution_service/matching_engine/balancer.py:182	test_instantiation_sites=1
BalancerWeightedPool	defined_at=execution_service/matching_engine/balancer.py:42	test_instantiation_sites=1
BaseDataLoader	defined_at=execution_service/data/loaders/base.py:32	test_instantiation_sites=12
BatchAuctionEngine	defined_at=execution_service/algo_library/solver_auction.py:297	test_instantiation_sites=5
BatchDataSink	defined_at=execution_service/engine/modes/batch/data_sink.py:12	test_instantiation_sites=9
BatchDataSource	defined_at=execution_service/engine/modes/batch/data_source.py:60	test_instantiation_sites=6
BatchMatchingEngine	defined_at=execution_service/engine/modes/batch/matching_engine.py:28	test_instantiation_sites=12
BeefyConnector	defined_at=execution_service/defi_execution/protocols/beefy.py:80	test_instantiation_sites=16
BinanceOrderFeedHandler	defined_at=execution_service/trade_execution/ws_feeds.py:115	test_instantiation_sites=11
BorrowHandler	defined_at=execution_service/engine/handlers/borrow_handler.py:25	test_instantiation_sites=1
BybitOrderFeedHandler	defined_at=execution_service/trade_execution/ws_feeds.py:282	test_instantiation_sites=10
CCTPBridgeConnector	defined_at=execution_service/defi_execution/protocols/cctp.py:138	test_instantiation_sites=13
CandleBookSnapshot	defined_at=execution_service/matching_engine/candle_book_cols.py:70	test_instantiation_sites=5
CandleTrade	defined_at=execution_service/matching_engine/trade_matcher.py:62	test_instantiation_sites=16
ConcurrentVenueExecutor	defined_at=execution_service/sports_execution/core/concurrent_executor.py:37	test_instantiation_sites=8
ConvexConnector	defined_at=execution_service/defi_execution/protocols/convex.py:75	test_instantiation_sites=15
CostModelRegistry	defined_at=execution_service/v2/cost_models.py:109	test_instantiation_sites=2
CurveStablePool	defined_at=execution_service/matching_engine/curve.py:42	test_instantiation_sites=1
CustodyPreTradePinger	defined_at=execution_service/custody/pre_trade_pinger.py:152	test_instantiation_sites=3
CustomInstrumentProvider	defined_at=execution_service/instruments/instrument_provider.py:26	test_instantiation_sites=11
DataAvailabilityValidator	defined_at=execution_service/engine/validation/data_availability_validator.py:44	test_instantiation_sites=16
DeFiNautilusTraderVerifier	defined_at=execution_service/data/defi_nautilus_verification.py:37	test_instantiation_sites=12
DeFiPositionTracker	defined_at=execution_service/services/position_tracker.py:20; execution_service/defi_execution/position_tracker.py:44	test_instantiation_sites=31
DeFiTestDataGenerator	defined_at=execution_service/data/defi_test_data_generator.py:23	test_instantiation_sites=19
DefiCostAggregator	defined_at=execution_service/matching_engine/defi/cost_aggregator.py:112	test_instantiation_sites=10
DeltaProxyRepricer	defined_at=execution_service/engine/delta_proxy_repricer.py:107	test_instantiation_sites=29
DeribitAuthMixin	defined_at=execution_service/venues/deribit_auth.py:18	test_instantiation_sites=6
DustRouterRunner	defined_at=execution_service/algo_library/dust_router_runner.py:79	test_instantiation_sites=12
EigenLayerConnector	defined_at=execution_service/defi_execution/protocols/eigenlayer.py:258	test_instantiation_sites=22
Err	defined_at=execution_service/utils/result.py:21	test_instantiation_sites=2
ExchangeFillFee	defined_at=execution_service/services/account_history_client.py:22	test_instantiation_sites=2
ExchangeFundingPayment	defined_at=execution_service/services/account_history_client.py:36	test_instantiation_sites=3
ExecAlgorithmRegistry	defined_at=execution_service/algorithms/registry.py:28	test_instantiation_sites=1
ExecutionCostEstimator	defined_at=execution_service/services/execution_cost_estimator.py:102	test_instantiation_sites=6
ExecutionIntent	defined_at=execution_service/algo_library/solver_auction.py:43	test_instantiation_sites=1
ExecutionPolicyDomainConfig	defined_at=execution_service/v2/policy_spec.py:37	test_instantiation_sites=6
ExecutionStatus	defined_at=execution_service/trade_execution/execution.py:16	test_instantiation_sites=1
Fill	defined_at=execution_service/engine/execution/types.py:63	test_instantiation_sites=23
FillRecord	defined_at=execution_service/engine/pnl_monitor.py:41	test_instantiation_sites=2
FlashLoanHandler	defined_at=execution_service/engine/handlers/flash_loan_handler.py:21	test_instantiation_sites=3
FundingRateTracker	defined_at=execution_service/services/funding_rate_tracker.py:37	test_instantiation_sites=1
FundingReconEngine	defined_at=execution_service/services/funding_recon_engine.py:71	test_instantiation_sites=2
FuturesRollHandler	defined_at=execution_service/engine/handlers/futures_handler.py:20	test_instantiation_sites=7
GasTokenBalanceTracker	defined_at=execution_service/services/eth_balance_tracker.py:24	test_instantiation_sites=2
GridBuilder	defined_at=execution_service/config/grid_builder.py:148	test_instantiation_sites=1
HealthFactorMonitor	defined_at=execution_service/defi_execution/monitors/health_factor_monitor.py:42	test_instantiation_sites=2
HistoricalPoolState	defined_at=execution_service/models/rate_impact.py:34	test_instantiation_sites=1
HybridOptimalAlgorithm	defined_at=execution_service/engine/execution/algorithms/hybrid_optimal.py:7	test_instantiation_sites=6
IbkrTradFiAdapter	defined_at=execution_service/trade_execution/adapters/ibkr_tradfi.py:44	test_instantiation_sites=39
IcebergConfig	defined_at=execution_service/algo_library/schemas.py:49	test_instantiation_sites=5
IdleConnector	defined_at=execution_service/defi_execution/protocols/idle.py:81	test_instantiation_sites=21
JitoBundleProvider	defined_at=execution_service/defi_execution/mev/jito_bundle.py:67	test_instantiation_sites=12
JitoConnector	defined_at=execution_service/defi_execution/protocols/jito.py:128	test_instantiation_sites=19
JitoRestakingConnector	defined_at=execution_service/defi_execution/protocols/jito_restaking.py:77	test_instantiation_sites=17
KarakConnector	defined_at=execution_service/defi_execution/protocols/karak.py:60	test_instantiation_sites=14
KelpDAOConnector	defined_at=execution_service/defi_execution/protocols/kelpdao.py:49	test_instantiation_sites=14
KrakenBookWebSocketClient	defined_at=execution_service/trade_execution/adapters/kraken_ws_client.py:542	test_instantiation_sites=7
KrakenPrivateWebSocketClient	defined_at=execution_service/trade_execution/adapters/kraken_ws_client.py:337	test_instantiation_sites=4
KrakenWebSocketClient	defined_at=execution_service/trade_execution/adapters/kraken_ws_client.py:135	test_instantiation_sites=6
LSTCollateralResolver	defined_at=execution_service/services/lst_collateral_resolver.py:118	test_instantiation_sites=15
LatencyRecorder	defined_at=execution_service/engine/latency_recorder.py:12	test_instantiation_sites=7
LendHandler	defined_at=execution_service/engine/handlers/lend_handler.py:25	test_instantiation_sites=5
LiveConfigLoader	defined_at=execution_service/config/live_loader.py:11	test_instantiation_sites=8
LiveDataSink	defined_at=execution_service/engine/modes/live/data_sink.py:197	test_instantiation_sites=15
LiveDataSource	defined_at=execution_service/engine/modes/live/data_source.py:11	test_instantiation_sites=3
LiveTrigger	defined_at=execution_service/engine/modes/live/trigger.py:10	test_instantiation_sites=3
ManualInstructionRequest	defined_at=execution_service/api/manual_schemas.py:8	test_instantiation_sites=3
MatchingEngineQuoteSource	defined_at=execution_service/algo_library/dust_quote_sources.py:292	test_instantiation_sites=10
MevRouter	defined_at=execution_service/v2/mev_router.py:84	test_instantiation_sites=7
MonitoredOrder	defined_at=execution_service/engine/orphan_monitor.py:66	test_instantiation_sites=1
MtdsBookDataProvider	defined_at=execution_service/algo_library/mtds_book_provider.py:56	test_instantiation_sites=23
MulticallBatcher	defined_at=execution_service/algo_library/multicall_batcher.py:213	test_instantiation_sites=4
NoOpDataSink	defined_at=execution_service/engine/orchestrator.py:193	test_instantiation_sites=9
NotionalConverter	defined_at=execution_service/engine/backtest/actors/signal_driven_shared.py:19	test_instantiation_sites=26
OKXOrderFeedHandler	defined_at=execution_service/trade_execution/ws_feeds.py:434	test_instantiation_sites=15
Ok	defined_at=execution_service/utils/result.py:14	test_instantiation_sites=4
OnChainExecutionService	defined_at=execution_service/services/onchain_execution_service.py:114	test_instantiation_sites=2
OneInchRouteMatcher	defined_at=execution_service/matching_engine/aggregator.py:311	test_instantiation_sites=1
OneXBetAdapter	defined_at=execution_service/sports_execution/adapters/bookmaker_api/onexbet.py:49	test_instantiation_sites=1
OptionsComboHandler	defined_at=execution_service/engine/handlers/options_handler.py:20	test_instantiation_sites=4
OrcaConnector	defined_at=execution_service/defi_execution/protocols/orca.py:56	test_instantiation_sites=10
OrderTracker	defined_at=execution_service/trade_execution/oms/tracker.py:20; execution_service/orders/tracker.py:10; execution_service/orchestration/orchestrator.py:35	test_instantiation_sites=26
OrphanMonitor	defined_at=execution_service/engine/orphan_monitor.py:129	test_instantiation_sites=13
OutOfSessionOrderError	defined_at=execution_service/exceptions.py:51	test_instantiation_sites=1
POVDynamicExecAlgorithm	defined_at=execution_service/algorithms/impl/pov_dynamic.py:81	test_instantiation_sites=2
PacificaConnector	defined_at=execution_service/defi_execution/protocols/pacifica.py:262	test_instantiation_sites=22
PassiveAggressiveAlgorithm	defined_at=execution_service/engine/execution/algorithms/passive_aggressive.py:9; execution_service/algo_library/passive_aggressive.py:30	test_instantiation_sites=8
PassiveAggressiveConfig	defined_at=execution_service/algo_library/passive_aggressive.py:8	test_instantiation_sites=3
PersistentOrderManager	defined_at=execution_service/trade_execution/oms/persistent_oms.py:20	test_instantiation_sites=1
PnLCalculator	defined_at=execution_service/services/pnl_calculator.py:95	test_instantiation_sites=11
PolicyResolutionContext	defined_at=execution_service/v2/policy_resolver.py:93	test_instantiation_sites=16
PolymarketAdapter	defined_at=execution_service/trade_execution/adapters/polymarket_adapter.py:46	test_instantiation_sites=9
PolymarketAdapterConfig	defined_at=execution_service/sports_execution/prediction_markets/polymarket.py:40	test_instantiation_sites=8
PolymarketOrderRequest	defined_at=execution_service/sports_execution/prediction_markets/polymarket.py:79	test_instantiation_sites=4
PolymarketOrderResult	defined_at=execution_service/sports_execution/prediction_markets/polymarket.py:95	test_instantiation_sites=2
PoolSnapshot	defined_at=execution_service/providers/solana_amm_depth_provider.py:73	test_instantiation_sites=2
PositionSnapshot	defined_at=execution_service/engine/pnl_monitor.py:31	test_instantiation_sites=2
PredictionBetHandler	defined_at=execution_service/engine/handlers/prediction_handler.py:55	test_instantiation_sites=4
QuoteLevel	defined_at=execution_service/engine/delta_proxy_repricer.py:56	test_instantiation_sites=1
RaydiumConnector	defined_at=execution_service/defi_execution/protocols/raydium.py:57	test_instantiation_sites=12
ReconFreezeChecker	defined_at=execution_service/preflight/recon_freeze.py:36	test_instantiation_sites=1
ReconGate	defined_at=execution_service/engine/recon_gate.py:36	test_instantiation_sites=1
RenzoConnector	defined_at=execution_service/defi_execution/protocols/renzo.py:26	test_instantiation_sites=14
RiskChecker	defined_at=execution_service/engine/risk/risk_checker.py:26	test_instantiation_sites=3
RpcProviderFallback	defined_at=execution_service/providers/rpc_fallback.py:119	test_instantiation_sites=6
SORTwapAlgorithm	defined_at=execution_service/engine/execution/algorithms/sor_twap.py:7	test_instantiation_sites=8
SetupMixin	defined_at=execution_service/engine/backtest/engine/setup.py:49	test_instantiation_sites=2
SidecarConfig	defined_at=execution_service/sports_execution/adapters/unity/sidecar.py:46	test_instantiation_sites=2
SidecarProcess	defined_at=execution_service/sports_execution/adapters/unity/sidecar.py:106	test_instantiation_sites=9
SocketBridgeConnector	defined_at=execution_service/defi_execution/protocols/bridge.py:210	test_instantiation_sites=1
SolanaAMMPool	defined_at=execution_service/matching_engine/solana_clmm.py:37	test_instantiation_sites=2
SolanaCLMMPool	defined_at=execution_service/matching_engine/solana_clmm.py:31	test_instantiation_sites=1
SolidlyCLForkPool	defined_at=execution_service/matching_engine/solidly_fork.py:226	test_instantiation_sites=2
SolidlyForkPool	defined_at=execution_service/matching_engine/solidly_fork.py:49	test_instantiation_sites=2
SorTwapAlgorithm	defined_at=execution_service/algorithms/sor_twap.py:46; execution_service/algo_library/sor_twap.py:44	test_instantiation_sites=7
SportsHandler	defined_at=execution_service/engine/handlers/sports_handler.py:19	test_instantiation_sites=3
SportsRouter	defined_at=execution_service/adapters/sports_router.py:49	test_instantiation_sites=20
SpreadImbalanceTracker	defined_at=execution_service/engine/spread_imbalance_tracker.py:26	test_instantiation_sites=1
StakeHandler	defined_at=execution_service/engine/handlers/stake_handler.py:25	test_instantiation_sites=4
StopLimitOrder	defined_at=execution_service/trade_execution/order_types.py:37	test_instantiation_sites=14
StopMarketOrder	defined_at=execution_service/trade_execution/order_types.py:58	test_instantiation_sites=9
StrikeMapper	defined_at=execution_service/instruments/strike_mapping.py:25	test_instantiation_sites=13
SubCandleBar	defined_at=execution_service/matching_engine/sub_candle_vwap.py:47	test_instantiation_sites=5
SubCandleVWAPMatcher	defined_at=execution_service/matching_engine/sub_candle_vwap.py:75	test_instantiation_sites=8
SwapHandler	defined_at=execution_service/engine/handlers/swap_handler.py:36	test_instantiation_sites=5
SwapTwapAlgorithm	defined_at=execution_service/algorithms/swap_twap.py:47; execution_service/engine/execution/algorithms/swap_twap.py:7; execution_service/algo_library/swap_twap.py:44	test_instantiation_sites=21
TWAPExecAlgorithm	defined_at=execution_service/algorithms/impl/twap.py:82	test_instantiation_sites=4
TenderlyTx	defined_at=execution_service/providers/tenderly.py:34	test_instantiation_sites=7
TickDataLoader	defined_at=execution_service/data/loaders/tick_data.py:22	test_instantiation_sites=2
TradFiISAlgorithm	defined_at=execution_service/algorithms/tradfi/implementation_shortfall.py:41	test_instantiation_sites=2
TradFiTWAPAlgorithm	defined_at=execution_service/algorithms/tradfi/twap.py:30	test_instantiation_sites=2
TradFiTestDataGenerator	defined_at=execution_service/data/tradfi_test_data_generator.py:19	test_instantiation_sites=14
TradFiVWAPAlgorithm	defined_at=execution_service/algorithms/tradfi/vwap.py:20	test_instantiation_sites=2
TradeHandler	defined_at=execution_service/engine/handlers/trade_handler.py:25	test_instantiation_sites=5
TwoTierPnLMonitor	defined_at=execution_service/engine/pnl_monitor.py:58	test_instantiation_sites=2
UnderlyingTracker	defined_at=execution_service/engine/reference_pricing.py:53	test_instantiation_sites=32
UnityBridge	defined_at=execution_service/sports_execution/adapters/unity/bridge.py:90	test_instantiation_sites=6
VWAPExecAlgorithm	defined_at=execution_service/algorithms/impl/vwap.py:36	test_instantiation_sites=1
VWAPParentOrderState	defined_at=execution_service/algorithms/impl/vwap_execution.py:37	test_instantiation_sites=3
VenueCascadeMonitor	defined_at=execution_service/engine/venue_cascade_monitor.py:30	test_instantiation_sites=12
VenueFailoverRouter	defined_at=execution_service/engine/venue_failover.py:28	test_instantiation_sites=11
VenueHealthMonitor	defined_at=execution_service/sports_execution/monitoring/venue_health.py:47	test_instantiation_sites=19
WalletPreflightRegistry	defined_at=execution_service/engine/wallet_preflight_registry.py:27	test_instantiation_sites=13
WethConnector	defined_at=execution_service/defi_execution/protocols/weth.py:68	test_instantiation_sites=11
WrapPreprocessor	defined_at=execution_service/engine/preprocessors/wrap_preprocessor.py:68	test_instantiation_sites=2
YearnConnector	defined_at=execution_service/defi_execution/protocols/yearn.py:94	test_instantiation_sites=16
YieldReconEngine	defined_at=execution_service/services/yield_recon_engine.py:77	test_instantiation_sites=18
```

**Reading this list**: several rows here are ALREADY covered by this doc's other findings under a different lens
(`HealthFactorMonitor`, `FundingReconEngine`'s `AccountHistoryClient` dependency) — their presence here is the
mechanical check independently reproducing what direct reads already found, which is a good cross-check, not a new
discovery. The remaining ~155 rows are NOT yet triaged individually — that triage (which are genuinely
declared-but-unwired vs. false positives from dynamic construction) is follow-up work, not done in this pass per the
source todo's own "report the full list; do not fix any findings, just enumerate" scope.

## What was measured as PRESENT, so nobody re-audits it

- **One matching kernel with declared fidelity levels** — `matching_engine/engine.py:701 MatchingEngine` routes by
  `BookType` to `L0Matcher` / `L1Matcher` / `L2Matcher` / `AMMMatcher` / `BenchmarkMatcher`. No true L3/MBO matcher,
  and latency/reject/venue-priority models are not part of the `BookType` taxonomy.
- **Side-effect suppression is a substituted adapter, not a flag** — `LiveMatchingEngine` vs `PaperMatchingEngine` with
  separate factories (`modes/live/matching_engine.py:179-205, 208-221`). The primitive is sound; it is selected on
  credential availability, not on a recovery phase.
- **UTL `EventTransport` supports cursor replay** — `read(after=...)` on all three implementations.
  `RedisStreamTransport` and `PubSubTransport` are consumer-independent append-only logs; `InMemoryTransport` is a
  bounded 10,000-entry deque with durability equal to process lifetime, and it is the paper/backtest topology.

## Progress Log

**2026-08-20 — filed.** No code touched. Findings come from a scoped read-only measurement audit; its uncertainty flags
are preserved in the P2 todo above rather than dropped. `PubSubTransport`'s module docstring still calls it a "stub
pending Plan 03 infra" while the implementation looks complete — not resolved here, and it is unclear which of the doc
or the code is stale.

- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries); corrected 1 stale path —
  `account_history_client.py` lives under `execution_service/services/`, not `execution_service/providers/`.
- **2026-08-21 (batch21 item 4, slot 6, class-enumeration todo)**: AST-based scan over `execution-service` found 161
  classes with test-side constructor calls but zero non-test instantiation (full list + methodology in the new
  "Findings — execution-service classes with tests but zero non-test instantiation" section above). Also corrected
  this doc's own "OrderRecoveryEngine has zero production call sites" table row — it is now stale, per a direct read
  of `cli/handlers/live_execution_handler.py:136,189-222` (`_create_startup_order_recovery` constructs it and is
  reachably called). Added one follow-up REVIEW P2 todo to triage the untriaged rows.
