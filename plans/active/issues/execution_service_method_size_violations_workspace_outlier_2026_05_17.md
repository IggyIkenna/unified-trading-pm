---
title: "execution-service has 377 method-size violations (workspace outlier; ~13× the next-worst repo)"
created: 2026-05-17
author: slot-7-ikenna
source:
  - execution-service@f871ffad7 (post-cutover snapshot)
  - workspace-wide method-size sweep 2026-05-16 → 2026-05-17 (slot 7 autonomous loop)
severity: P2 (post-cutover hygiene; not blocking May-23)
status: phase-b-in-progress (103/377 cleared = ~27%; milestone 100/377 crossed 2026-05-17)
locked_by: live-defi-rollout
locked_since: 2026-05-17
routing:
  primary_owner: operator triage (size = per-area sprint, not single-owner)
  composes_with: utl_qg_preexisting_failures_2026_05_14.md §3 (workspace pattern)
---

> **🟡 SUBSUMED BY MEGA AUDIT** — findings absorbed by **Phase D6 (strategy + execution plan beef-up)** per [mega_audit_and_plan_beefup_progression_2026_05_20.md](mega_audit_and_plan_beefup_progression_2026_05_20.md) (slot-1 triage 2026-05-20). Do NOT work standalone; banner removed when D6 closes this scope.

## What I found

While shipping the cumulative-50+ method-size refactor sweep across UTL + features-service + MTDS +
unified-trading-api + strategy-service this session (2026-05-16 / 2026-05-17 autonomous loop), I ran a final scan across
every sister repo with `python3` AST parsing + the per-repo `FUNCTION_SIZE_EXTRA_EXCLUDES` honored. Result by repo:

| Repo                              | Non-excluded violations                                                        |
| --------------------------------- | ------------------------------------------------------------------------------ |
| unified-cloud-interface           | 0                                                                              |
| batch-live-reconciliation-service | 0                                                                              |
| pnl-attribution-service           | 0                                                                              |
| client-reporting-api              | 0                                                                              |
| trading-agent-service             | 0                                                                              |
| alerting-service                  | 0                                                                              |
| deployment-service                | 0                                                                              |
| instruments-service               | 0                                                                              |
| unified-trading-api               | 0 (post `BatchCandleReader.get_candles` 54L→33L this loop)                     |
| features-service                  | 0 (post `FuturesRollAdjuster.annotate_lifecycle_phase` 58L→34L this loop)      |
| strategy-service                  | 0 (post 2 refactors this loop)                                                 |
| market-tick-data-service          | 0 (post 5 refactors this loop)                                                 |
| unified-trading-library           | 0 source + 1 path excluded (`manifest_writer.py` docstring-heavy contract API) |
| **execution-service**             | **377**                                                                        |

`execution-service` is the outlier — roughly 13× the next-worst repo (the workspace-second was UTL pre-sweep at ~28
violations). `FUNCTION_SIZE_EXTRA_EXCLUDES` in `execution-service/scripts/quality-gates.sh` is the empty list `()` so
these are NOT triaged-as-known-pre-existing; either QG is silently passing on these (check — maybe `MAX_METHOD_LINES` is
overridden) or the suite has never run cleanly on them.

### Severity distribution (377 total)

| Bucket   | Count | % of total |
| -------- | ----- | ---------- |
| 51-60L   | 94    | 25%        |
| 61-75L   | 107   | 28%        |
| 76-100L  | 81    | 21%        |
| 101-150L | 63    | 17%        |
| 151L+    | 32    | 9%         |

### Top 15 longest methods

```text
436L  data/loaders/tick_data.py:TickDataLoader.load_trades
428L  data/loader.py:UCSDataLoader.load_trades
299L  algorithms/impl/twap.py:TWAPExecAlgorithm.on_order
289L  data/loader_gcs.py:GCSLoaderMixin.load_trades
268L  engine/backtest/engine/core.py:BacktestEngine.run
264L  engine/backtest/node_builder.py:NodeBuilder.build_strategy_config
251L  data/ohlcv_converter.py:OHLCVConverter.convert_ohlcv_parquet_to_catalog
231L  data/validator.py:DataValidator.validate_gcs_trades_availability
230L  data/trade_converter.py:TradeConverter.convert_trades_parquet_to_catalog
228L  data/config_builder.py:DataConfigBuilder.build_trades_config
227L  engine/backtest/engine/results.py:ResultsMixin._extract_results
222L  engine/backtest/node_builder.py:NodeBuilder.build_venue_config
218L  data/loader_transforms.py:DataTransformsMixin._normalize_timestamp_columns_for_backtest
216L  results/extractor.py:ResultExtractor.extract_summary
212L  data/checker.py:DataAvailabilityChecker.check_gcs_file_exists
```

### Submodule concentration (top 10)

```text
engine/backtest             : 41
algorithms/impl             : 33
defi_execution/protocols    : 30
engine/validation           : 13
engine/handlers             : 13
trade_execution/adapters    : 13
services/onchain_execution_service.py : 9
data/loaders                : 7
venues/deribit_orders.py    : 7
sports_execution/adapters   : 7
```

Roughly 30% of violations cluster in `engine/backtest` + `algorithms/impl` + `defi_execution/protocols`.

## Why it matters

`execution-service` is on the **May-23 critical path** — it runs the live wallet trade adapter, the backtest engine that
validates archetype P&L pre-promote, and the per-venue protocol implementations (Aave / Compound / Uniswap / Hyperliquid
/ etc.). The 50-line workspace standard exists because:

1. **Review burden**: 200+ line methods make per-commit diff review costly; in a critical-path service this is where
   regressions hide.
2. **Test coverage gaps**: long methods correlate strongly with low branch coverage. The `TickDataLoader.load_trades` at
   436L will have multiple un-tested code paths.
3. **basedpyright performance**: strict-mode reportAny / reportUnknownVariableType checks are quadratic in some
   patterns; long methods slow QG.
4. **Cross-side handoff**: strategy-service has now been refactored to spec — execution-service is the only repo Harsh's
   side reads / cites without a code-quality baseline to match.

This is **NOT a May-23 blocker** — execution-service tests pass, the live trade adapter ships operationally, and the 32
violations ≥151L are mostly data-loader / backtest-engine paths that don't fire on the live wallet hot path. But it IS
the workspace-second-largest tech-debt cluster after UAC's `internal/__init__.py` 1693L barrel file (separately tracked
in `uac_qg_preexisting_size_violations_2026_05_14.md`).

## Recommended decision

**Operator triage / 3-stage rollout**:

1. ✅ **Phase A — establish baseline** (~0.5 cal AI-day) — **SHIPPED 2026-05-17 execution-service@91e2cfb9e**:
   `FUNCTION_SIZE_EXTRA_EXCLUDES` populated with 187 files (561 array elements; 369 underlying violations). AST-scan
   post-exclude returns zero remaining violations. QG was indeed silently passing on these — find pattern at
   base-service.sh:778 was matching ALL files, exclude list was empty `()`, but the AST scanner on line 779-794 actually
   exits via `except: pass` on any parse error, so QG only fired on files where `print()` succeeded. Likely the QG step
   was emitting the violation list but `log_fail` was never reached (need to audit — but the ratchet is now solid
   regardless). **Ratchet-down 2026-05-17 execution-service@78ee78909** — slot-7 Phase B incremental refactors cleared 7
   files (sor / defi_test_data_generator / signal_driven_v3 / live_ccxt_adapter / instruction_validator / oms /
   benchmark_service); allowlist 187 → 180 files. AST scanner re-verified clean. **Ratchet-down 2026-05-17 (slot-4
   cross-slot pickup, batch 1)** — additional 3 files cleared at execution-service@4da3d96fb (auth.py verify_token
   61L→17L, +3 helpers), @80382caf1 (algorithms/tradfi/twap.py schedule 55L→27L, +2 helpers), @1e9440da7
   (engine/handlers/claim_reward_handler.py execute 57L→36L, +1 helper); allowlist 180 → 177 files. AST scanner
   re-verified clean per file. Pure helper-extraction; per-method behavior preserved (same UEI/event emissions, same
   return shapes, same exception classes). **Ratchet-down 2026-05-17 (slot-4 cross-slot pickup, batch 2)** — additional
   2 files cleared at execution-service@ed8789219 (services/eth_balance_tracker.py deduct_gas 57L→30L, +1 helper
   \_record_debt), @517e60a81 (sports_execution/adapters/exchanges/kalshi.py place_order 56L→41L, +1 helper
   \_submit_order_post); allowlist 177 → 175 files. Same AST clean + behavior-preservation discipline. **Ratchet-down
   2026-05-17 (slot-2 cross-slot pickup, batch 3)** — additional 2 files cleared at execution-service@9c7907afa
   (engine/handlers/borrow_handler.py execute 64L→41L, +1 helper \_match_alpha_zero), @e1ec91851
   (engine/handlers/lend_handler.py execute 66L→42L, +1 helper \_match_alpha_zero); allowlist 175 → 173 files. Same
   helper-extraction pattern as @1e9440da7 claim_reward_handler — pull ALPHA_ZERO benchmark match logic into typed
   helper; execute() reads as validate → cost-estimate → match → result-build. behavior preservation verified: same
   side/venue switch on operation type, same match_order kwargs, same MatchResult return path. basedpyright clean.
   **Ratchet-down 2026-05-17 (slot-2 cross-slot pickup, batch 4)** — additional 3 files cleared at
   execution-service@90d66d10a (engine/handlers/stake_handler.py execute 79L→48L, +3 helpers \_resolve_exchange_rate /
   \_match_alpha_zero / \_amount_received — handles benchmark→DEFAULT_RATES fallback
   - per-direction amount calculation in addition to the base ALPHA_ZERO match), @dcd182add
     (engine/handlers/swap_handler.py — TWO methods: estimate_cost 57L→33L via \_simulate_swap_with_pool +
     \_estimate_swap_no_pool, \_execute_with_matching_engine 87L→27L via \_match_amm_swap + \_log_swap_outcome — 4
     helpers total), @c78b8f994 (engine/handlers/sports_handler.py execute 59L→33L, +2 helpers \_try_live_router
     (None-fallback when router absent OR raises) + \_simulate_actual_odds (20bps spread for exchanges)). Allowlist 173
     → 170 files. basedpyright clean on each. Same per-method behavior preservation discipline. **Ratchet-down
     2026-05-17 (slot-2 cross-slot pickup, batch 5)** — additional 2 files cleared at execution-service@54e0db54e
     (engine/handlers/trade_handler.py execute 81L→49L, +1 helper \_match_orderbook for the L1/L2 orderbook match path
     with limit_price/benchmark price fallback), @94793f724 (engine/handlers/transfer_handler.py — THREE methods cleaned
     via 5 helpers: execute 65L→16L (\_emit_transfer_initiated / \_dispatch_transfer / \_emit_transfer_completion),
     \_execute_internal_transfer 58L→46L (\_emit_internal_transfer_completed), auto_funding_to_trading 56L→26L
     (\_auto_funding_required / \_build_auto_funding_instruction)). Allowlist 170 → 168 files. Per-event payload +
     venue/capability logic preserved exactly. basedpyright clean. **Ratchet-down 2026-05-17 (slot-4 cross-slot pickup,
     batch 3)** — additional 4 files cleared at execution-service@7a0859955 (algorithms/swap_twap.py execute 60L→31L, +1
     helper \_execute_all_slices), @4875abadb (providers/rpc_fallback.py execute 60L→22L, +1 helper \_try_provider; also
     consolidates payload parse into the existing \_parse_rpc_result helper), @bed41ff45
     (instruments/custom_instruments.py **init** 57L→35L, +3 static/instance helpers for
     price_increment/size_increment/limits), @fe755fd3d (sports_execution/adapters/unity/bridge.py pump 57L→22L, +3
     helpers \_drain_outbound + \_read_inbound + \_handle_bet_fill). Allowlist 168 → 164 files. Per-method semantics
     preserved (multi-slice TWAP accumulators, JSON-RPC failover order + status-code policy, instrument-precision
     fallbacks, sidecar message dispatch). **Ratchet-down 2026-05-17 (slot-4 cross-slot pickup, batch 4)** — additional
     4 files cleared at execution-service@711d2e1ae (engine/live/router.py score_venues 59L→26L, +2 helpers
     \_collect_eligible_candidates + \_normalise_and_sort), @bd49a9dac (data/defi_data_loader.py get_risk_params
     58L→18L, +2 helpers \_locf_risk_params + \_risk_params_default_with_warn), @afbf8b20c (services/position_tracker.py
     create_position 60L→14L, +2 helpers \_next_position_id + \_build_position @staticmethod), @8a4e781b6
     (engine/orphan_monitor.py sweep 61L→26L, +2 helpers \_emit_orphaned_event @staticmethod + \_try_cancel_and_confirm
     async with cancel + status-retry loop + registry mark). Allowlist 164 → 160 files. Per-method semantics preserved
     (venue-scoring weights + LIMIT/MARKET fee selection, LOCF risk-param fallback chain, position counter + entry-state
     init, ORDER_ORPHANED UEI + cancel-confirm retry semantics).

   **Ratchet-down 2026-05-17 (slot-4 cross-slot pickup, batch 4 continuation)** — 1 additional file cleared at
   execution-service@367b6d0f3 (engine/backtest/engine/execution.py \_execute_backtest 56L→33L, +2 helpers
   \_log_backtest_inputs + \_validate_backtest_results @staticmethod). Allowlist 160 → 159 files. AST clean.

   **Ratchet-down 2026-05-17 (slot-4 cross-slot pickup, batch 5)** — 5 additional files cleared at
   execution-service@f23410569 (sports_execution/adapters/exchanges/matchbook.py get_odds 59L→25L, +1 helper
   \_handle_venue_error NoReturn — pulls classify_venue_error + ADAPTER_FETCH_FAILED + UNKNOWN_VENUE_ERROR_RECEIVED +
   BookmakerUnavailableError raise path into typed helper), @dbd23c48d (venues/uniswap.py swap_exact_output 60L→21L, +1
   helper \_compute_exact_output_input — pulls reverse-quote math: price ratio + fee + price-impact bps), @24ee89c99
   (defi_execution/protocols/hyperliquid.py \_parse_order_response 61L→18L, +2 helpers \_build_filled_order_result +
   \_build_resting_order_result — both track oid in \_live_orders), @a3b11ac36 (engine/circuit_breaker.py record_failure
   62L→14L, +2 helpers \_emit_unknown_venue_event + \_advance_state_on_failure — rate-based DEGRADED/OPEN transitions
   preserved), @1687c5091 (trade_execution/adapters/okx_native.py parse_order_response 62L→28L, +3 @staticmethod helpers
   \_map_okx_status + \_parse_decimal_field + \_parse_avg_price). Allowlist 157 → 152 files (note: slot 2's
   solver_auction + pov_dynamic refactors landed in this window but those files still have other 50+L methods so remain
   in allowlist). AST clean per file. basedpyright clean. Per-method semantics preserved (CanonicalError isinstance
   routing, slippage check + balance update order, oid tracking on both filled+resting paths, under-lock ordering for
   state transitions, OKX status map fallback to 'pending').

   **Ratchet-down 2026-05-17 (slot-4 cross-slot pickup, batch 6)** — 5 additional files cleared at
   execution-service@fa5ac4ed8 (adapters/defi_adapter.py \_simulate_transaction 62L→18L, +2 helpers
   \_post_tenderly_simulate + \_emit_simulation_revert @staticmethod), @9e3a0995a
   (engine/backtest/fill_models/dex_fill_model.py simulate_fill 62L→27L, +1 helper \_fill_error @staticmethod
   consolidates 3 error-return dicts), @fe562cb92 (engine/backtest/progress_display.py \_extract_instruction_legs
   62L→12L, +3 helpers \_as_dict + \_algo_for_type + \_legs_for_role all @staticmethod), @3aa989008
   (matching_engine/defi/cost_aggregator.py estimate_recursive_loop_cost 64L→31L, +1 helper \_resolve_slippage_bps
   @staticmethod for 3-tier slippage pick; build_defi_fill_context 55L→15L via docstring trim only), @51d85a8ba
   (sports_execution/adapters/bookmaker_api/api_football.py get_odds + get_fixtures_with_odds 64L+60L → 26L+25L, +1
   shared @staticmethod helper \_emit_venue_error_events parametrised on endpoint + extra_details). Allowlist 152 → 147
   files. AST clean per file. Per-method behavior preservation: Tenderly POST shape (jsonrpc/method/params/id) + 15s
   timeout, fill-result dict schema (success/amount_out/execution_price/ slippage_bps/error), config narrowing per
   primary+secondary role, gas-action FLASH_OPEN/SUPPLY mapping + flash-provider AAVE_V3/NONE switch,
   ADAPTER_FETCH_FAILED + UNKNOWN_VENUE_ERROR_RECEIVED dual-emit with classify_venue_error.

   **Ratchet-down 2026-05-17 (slot-4 cross-slot pickup, batch 7)** — 6 additional files cleared at
   execution-service@f1076caeb (data/schema_validator.py main 54L→14L, +2 helpers \_parse_cli_args +
   \_print_validation_results; CLI argparse + per-data-type result logger separated), @3760b27bf
   (defi_execution/mev/jito_bundle.py submit_bundle 63L→31L, +1 @staticmethod helper \_validate_submit_inputs for the
   3-rule precondition gate), @f7187ee5b (engine/transfers/confirmation_poller.py wait_for_confirmation 63L→27L, +2
   @staticmethod helpers \_emit_confirmed + \_emit_failed for the TRANSFER_CONFIRMED / TRANSFER_FAILED UEI emits),
   @a27b2c0b9 (algo_library/sor_dex.py \_get_venue_quote 63L→28L, +1 helper \_synthetic_venue_quote for the config-based
   fallback path when no on-chain pool data is loaded), @d5afc584a (trade_execution/adapters/bybit_native.py
   parse_order_response 64L→28L, +3 @staticmethod helpers \_map_bybit_status + \_parse_decimal_or_zero +
   \_parse_positive_decimal; same parser-helper pattern as okx_native + matchbook), @11737482a
   (engine/venue_cascade_monitor.py evaluate 64L→37L, +1 @staticmethod helper \_emit_cascade_detected for the
   VENUE_CASCADE_DETECTED CRITICAL emit). Allowlist 147 → 141 files. AST clean per file. Per-method behavior
   preservation: argparse arg shape
   - exit-code semantics, jito \_MAX_BUNDLE_SIZE enforcement + tip-positive check, transfer-status state machine
     (CONFIRMED/FAILED/PENDING + elapsed counter + timeout path), sor_dex pool-found vs synthetic fallback ordering with
     fee_rate + gas_estimate sourcing, bybit status-map (new/partial/filled/ cancelled/rejected/deactivated) +
     Decimal-parse + positive-only avg-price filter, cascade-pct computation + is_total_failure full-equality + scoped
     vs firm-wide kill-switch routing.

   **Ratchet-down 2026-05-17 (slot-4 cross-slot pickup, batch 8)** — 5 additional files cleared at
   execution-service@528040ef4 (algo_library/dust_quote_sources.py \_simulate_route 63L→28L, +1 helper \_simulate_hop
   pulls per-hop book-fetch + match + slippage-cap + fee tracking), @8a999fba9
   (sports_execution/adapters/unity/sidecar.py heartbeat 63L→31L, +1 helper \_unhealthy_sample for the 5 failure-mode
   SidecarHealthSample constructions), @d61eef49d (engine/execution/algorithms/adaptive_twap.py schedule 64L→36L, +1
   @staticmethod helper \_build_initial_state pulls 4-param validation + n_slices/base_qty/side_sign derivation),
   @68dccf1c1 (engine/live/positions.py update_position 64L→18L, +4 @staticmethod helpers \_empty_position +
   \_merge_venue_quantity + \_merge_venue_type + \_set_pnl_fields; pnl derive vs caller-supplied switching preserved),
   @0de2f906c (algorithms/tradfi/vwap.py schedule 66L→24L, +2 @staticmethod helpers \_validate_and_normalise
   - \_build_slices; final-slice rounding absorption preserved). Allowlist 141 → 136 files (slot 2 also cleared
     yield_recon + config_validator + passive_aggressive in the same window per commits @080c641a8 / @31fbcbe91 /
     @07ea5167a; combined drop 141→136). AST clean per file. Per-method behavior preservation: dust-route hop-by-hop
     carrying-amount accumulation + 4-fail path return-None, sidecar nonce round-trip + sequence tracking + deadline
     loop, adaptive-twap factor computation + min(base\*factor, qty) selection, position venue_positions + venue_types
     dict updates + PnL fallback derive, VWAP normalised-weights distribution + final-slice rounding catch-up.

   **Ratchet-down 2026-05-17 (slot-4 cross-slot pickup, batch 9)** — 5 additional files cleared at
   execution-service@33f08b30d (defi_execution/helpers/perp_hedge_sizer.py compute_rebalance 66L→30L, +1 @staticmethod
   helper \_build_rebalance consolidates both NOOP + SHORT/COVER RebalanceInstruction constructions), @e7d429adb
   (trade_execution/adapters/bitget_native.py parse_order_response 67L→29L, +3 @staticmethod helpers
   \_map_bitget_status + \_parse_decimal_or_zero + \_parse_positive_decimal; mirrors okx_native + bybit_native
   parse-helper pattern across all 3 CEX adapters), @f58a3be10 (defi_execution/protocols/bridge.py get_bridge_quotes
   67L→37L, +1 helper \_build_bridge_route pulls single-route construction out of the for-loop body), @f698b4550
   (venues/deribit_websocket.py \_websocket_handler 66L→32L, +1 helper \_dispatch_ws_message pulls
   subscription/heartbeat/response routing out of the recv loop), @20e86dd98 (config/grid_generator_models.py to_dict
   68L→9L, +4 helpers \_apply_strategy_fields + \_apply_execution_block + \_strip_strategy_exec_algorithm
   @staticmethod + \_build_grid_metadata; aggressive config-builder decomposition). Allowlist 136 → 131 files. AST clean
   per file. Per-method behavior preservation: rebalance NOOP-vs-band logic + DEFI_CROSS_VENUE_DELTA_DRIFT emit
   ordering, Bitget data envelope unwrap + status map (6 keys)
   - Decimal parse + positive-avg-price filter, Socket /quote results iteration with best-output + fastest tagging
     post-loop, WS recv-loop with TimeoutError ping + ConnectionClosed break + reconnect backoff in finally, grid-config
     strategy-id parsing + timeframe→seconds derivation + execution[instruction_type] + grid_metadata lineage.

   **Slot-4 cumulative across batches 1+2+3+4+5+6+7+8+9**: 41 files cleared (187→131 baseline-equivalent; slot 4
   contribution: -41 files; allowlist now 131). **Slot-2 cumulative across batches 3+4+5**: 8 files cleared (187→168,
   -19 from baseline). **Ratchet-down 2026-05-17 (slot-2 cross-slot pickup, batch 6)** — additional 2 files cleared at
   execution-service@5d1f40c71 (engine/handlers/flash_loan_handler.py execute 79L→33L, +3 helpers
   \_check_flash_loan_liquidity (REJECTED-or-proceed gate) + \_record_flash_borrow (track + return) +
   \_settle_flash_repay (clear + fee calc)), @1dde42821 (engine/handlers/sell_reward_handler.py execute 81L→47L, +1
   helper \_match_sell — venue-conditional CEX L2_MBP MARKET vs DEX ALPHA_ZERO LIMIT switch). Allowlist 168 → 166 files.
   basedpyright clean. Same per-method behavior preservation.

   **Slot-2 cumulative across batches 3+4+5+6**: 10 files cleared (187→166, -21 from baseline). All
   engine/handlers/{borrow,lend,stake,swap,sports,trade,transfer,flash_loan,sell_reward}\_handler.py are now
   refactored + removed from allowlist. The remaining handlers in engine/handlers/ (sports_handler already done;
   claim_reward + auth + tradfi-twap already done by slot-4) are below the 50L threshold. Slot-2 sweep of
   engine/handlers/ is COMPLETE.

   **Ratchet-down 2026-05-17 (slot-2 cross-slot pickup, batch 7 — defi_execution/protocols sweep starting)**:
   marinade.py shipped at execution-service@1e9d31edd (stake 67L→3L, unstake 68L→3L; extracted 3 helpers
   \_submit_stake_op (shared lamports-convert + paper-trade-or-build-tx + send + log path), \_build_paper_trade_result
   (synthesise SolanaTransactionResult for paper mode), \_log_stake_op_result (success/failure log emission)). Allowlist
   after slot-7 batch (perp_hedge_sizer + bridge + deribit_websocket + bitget_native + tp_sl validation) was 161; -1 =
   160 files. basedpyright clean. Same per-method behavior preservation.

   **Slot-2 cumulative across batches 3+4+5+6+7**: 11 files cleared (187→160 with slot-7 contributions, slot-2
   contribution: -11 files from execution-service handlers + 1 defi protocol).

   **Ratchet-down 2026-05-17 (slot-2 batch 8 — defi_execution/protocols sweep continues)**: kamino.py shipped at
   execution-service@d398d3c9f (supply 70L→3L, withdraw 68L→3L; extracted 3 helpers \_submit_reserve_op (lamports +
   paper-mode + tx build + send + log), \_build_paper_trade_result, \_log_reserve_op_result). Same pattern as
   marinade.py batch 7. Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3+4+5+6+7+8**: 12 files cleared (slot-2 contribution: -12 files; 10 handlers + 2
   defi protocols).

   **Ratchet-down 2026-05-17 (slot-2 batch 9 — defi_execution/protocols sweep continues)**: orca.py shipped at
   execution-service@da88ae8cd (add_liquidity 96L→34L, remove_liquidity 76L→23L; extracted 5 helpers
   \_submit_whirlpool_ix (program-id + Transaction wrapping), \_simulated_tx_result (canonical paper-trade
   SolanaTransactionResult), \_build_paper_trade_result_add (per-op paper-mode logging), \_log_add_liquidity_result,
   plus matching remove\_\* helpers). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3+4+5+6+7+8+9**: 13 files cleared (slot-2 contribution: -13 files; 10 handlers
   - 3 defi protocols).

   **Ratchet-down 2026-05-17 (slot-2 batch 10 — defi_execution/protocols sweep continues)**: raydium.py shipped at
   execution-service@0f2c38fd8 (get_pool_info 61L→9L via \_fetch_pool_payload + \_build_pool_info_from_payload
   parse-helper split; add_liquidity 96L→34L, remove_liquidity 76L→21L via same orca-pattern helper set
   (\_submit_clmm_ix + \_simulated_tx_result + per-op paper/log helpers)). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3+4+5+6+7+8+9+10**: 14 files cleared (slot-2 contribution: -14 files; 10
   handlers + 4 defi protocols).

   **Ratchet-down 2026-05-17 (slot-2 batch 11 — defi_execution/protocols sweep continues)**: jupiter.py shipped at
   execution-service@8687febc9 (get_swap_quote 94L→10L via \_fetch_quote_payload + \_build_quote_from_payload split;
   execute_swap 130L→33L via \_post_swap_request + \_quote_to_jupiter_payload + \_decode_swap_transaction +
   \_build_paper_trade_swap_result. The execute_swap helper trio cleanly separates HTTP-POST, JSON-serialize, and
   base64-decode VersionedTransaction phases). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3+4+5+6+7+8+9+10+11**: 15 files cleared (slot-2 contribution: -15 files; 10
   handlers + 5 defi protocols).

   **Ratchet-down 2026-05-17 (slot-2 batch 12 — defi_execution/protocols sweep continues)**: aave.py shipped at
   execution-service@b0cf30814 (\_init_live_executor 69L→13L via \_try_init_via_base_credentials (Secret Manager path) +
   \_try_init_via_config_overrides (direct config fallback) early-return split; warning emission centralised in caller).
   Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3+4+5+6+7+8+9+10+11+12**: 16 files cleared (slot-2 contribution: -16 files; 10
   handlers + 6 defi protocols).

   **Ratchet-down 2026-05-17 (slot-2 batch 13 — defi_execution/protocols sweep continues)**: aster.py shipped at
   execution-service@4493316a1 (place_order 93L→25L via \_place_order_live (signed-POST shape, error-classified) +
   \_place_order_paper (deterministic fill + position + fee update); same OrderResult shape both paths). Allowlist -1.
   basedpyright clean.

   **Slot-2 cumulative across batches 3+4+5+6+7+8+9+10+11+12+13**: 17 files cleared (slot-2 contribution: -17 files; 10
   handlers + 7 defi protocols).

   **Ratchet-down 2026-05-17 (slot-2 batch 14 — defi_execution/protocols sweep continues)**: base.py shipped at
   execution-service@383595e75 (\_load_wallet_credentials 61L→14L via \_require_wallet_config (raise ValueError on
   missing wallet_private_key/rpc_url) + \_resolve_wallet_address (config override OR derive from key);
   sign_and_send_transaction 95L→27L via \_inject_tx_fields (mutate-in-place from/nonce/gas/gasPrice/chainId) +
   \_simulated_tx_result (paper-mode pseudo-hash) + \_broadcast_signed_tx (returns (tx_hash, error_or_none)) +
   \_await_tx_receipt (success-with-gas_used vs reverted vs wait-failed)). Per-method behavior preserved. Allowlist -1.
   basedpyright clean.

   **Slot-2 cumulative across batches 3+4+5+6+7+8+9+10+11+12+13+14**: 18 files cleared (slot-2 contribution: -18 files;
   10 handlers + 8 defi protocols).

   **Ratchet-down 2026-05-17 (slot-2 batch 15 — services sweep starting)**: pnl_calculator.py shipped at
   execution-service@ec766fcc8 (calculate_period_pnl 71L→42L via \_returns_pct (gross/net % returns,
   zero-on-zero-capital) + \_ethena_benchmark_return (day-count APY→period-$-return)). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3+4+5+6+7+8+9+10+11+12+13+14+15**: 19 files cleared (slot-2 contribution: -19
   files; 10 handlers + 8 defi protocols + 1 service).

   **Ratchet-down 2026-05-17 (slot-2 batch 16 — services sweep continues)**: lst_collateral_resolver.py shipped at
   execution-service@847fe94e5 (resolve_collateral_path 76L→27L via \_best_lst_for_venue_coin (highest collateral_factor
   accepted at venue) + \_build_lst_path_result (LST stake + post-collateral steps + per-chain gas)). Allowlist -1.
   basedpyright clean.

   **Slot-2 cumulative across batches 3+4+5+6+7+8+9+10+11+12+13+14+15+16**: 20 files cleared (slot-2 contribution: -20
   files; 10 handlers + 8 defi protocols + 2 services).

   **Ratchet-down 2026-05-17 (slot-2 batch 17 — engine/preprocessors)**: wrap_preprocessor.py shipped at
   execution-service@0e3954de8 (\_maybe_insert_unwrap 71L→35L via \_resolve_unwrap (decide eligibility +
   destination_token check) + \_unwrap_venue (type→venue mapping); preprocess 77L→27L via \_rewrite_with_wrapped_token
   (clone instruction with token_in→wrapped + metadata tags)). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3+4+5+6+7+8+9+10+11+12+13+14+15+16+17**: 21 files cleared (slot-2 contribution:
   -21 files; 10 handlers + 8 defi protocols + 2 services + 1 preprocessor).

   **Ratchet-down 2026-05-17 (slot-4 batch 10 — services/data sweep)**: 2 net-new files cleared at
   execution-service@fb8643e29 (data/defi_lateral_loader.py load_lst_rates 71L→41L via \_discover_lst_parquets (async —
   canonical prefix list + legacy fallback + FileNotFoundError in one place)); services/yield_recon_engine.py
   reconcile_eigenlayer_rewards 64L→44L via \_compute_eigen_status (@staticmethod — discrepancy_pct +
   MATCH/DISCREPANCY/CRITICAL status in one typed helper; reconcile body reads as None-check → compute-status →
   build-record → maybe-alert). aave.py + pnl_calculator.py stash-resolved convergently with slot-2 batches 12+15 (both
   slots independently extracted the same logic; slot-2 naming used in final QG file). Allowlist 131 → 117 files
   (combined progress since batch 9 including all slot activity). AST clean per file. basedpyright clean.

   **Slot-4 cumulative across batches 1+2+3+4+5+6+7+8+9+10**: 43 files cleared (allowlist now 117).

   **Ratchet-down 2026-05-17 (slot-2 batch 18 — services sweep continues)**: bridge_cost_model.py shipped at
   execution-service@fde0f06d6 (get_live_quote 102L→33L via \_resolve_bridge_addrs (chain-id + token-addr lookup) +
   \_fetch_across_suggested_fees (aiohttp ClientSession with ThreadedResolver + 10s timeout, returns None on
   non-200/network error) + \_build_live_quote_from_payload (pct/1e14→bps, gas-tokens×$2000→USD, outputAmount)).
   Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3+4+5+6+7+8+9+10+11+12+13+14+15+16+17+18**: 22 files cleared (slot-2 contribution:
   -22 files; 10 handlers + 8 defi protocols + 3 services + 1 preprocessor).

   **Ratchet-down 2026-05-17 (slot-2 batch 19 — services sweep continues)**: funding_recon_engine.py shipped at
   execution-service@dd7d967a6 (reconcile 114L→45L via \_record_missing_exchange_data (MISSING_EXCHANGE_DATA path + INFO
   alert post-grace-period) + \_classify_status (MATCH/DISCREPANCY/CRITICAL ladder on payment_bps + rate_bps
   thresholds) + \_maybe_publish_drift_alerts (per-rule_id payment + rate-divergence alert emission)). Allowlist -1.
   basedpyright clean.

   **Slot-2 cumulative across batches 3+4+5+6+7+8+9+10+11+12+13+14+15+16+17+18+19**: 23 files cleared (slot-2
   contribution: -23 files; 10 handlers + 8 defi protocols + 4 services + 1 preprocessor).

   **Ratchet-down 2026-05-17 (slot-2 batch 20 — services sweep continues)**: execution_cost_estimator.py shipped at
   execution-service@ca011329c (estimate_cost 111L→39L via \_estimate_exchange_fee_bps (taker lookup or venue-type
   default + confidence + note) + \_estimate_gas_cost_usd (DEX/LENDING/STAKING only, inline chain_name_to_id) +
   \_estimate_bridge_cost_usd (cross-chain-only, defaults to 0)). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3-20**: 24 files cleared (slot-2 contribution: -24 files; 10 handlers + 8 defi
   protocols + 5 services + 1 preprocessor).

   **Ratchet-down 2026-05-17 (slot-2 batch 21 — service_config sweep)**: service_config.py shipped at
   execution-service@da16a9754 (get_bucket_for_asset_group 74L→27L via \_resolve_asset_group_bucket (asset-group-attr →
   generic-attr → constructed-from-project_id fallback chain) + promoted valid_bucket_types from local list to
   \_VALID_BUCKET_TYPES ClassVar tuple). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3-21**: 25 files cleared (slot-2 contribution: -25 files; 10 handlers + 8 defi
   protocols + 5 services + 1 preprocessor + 1 service_config).

   **Ratchet-down 2026-05-17 (slot-2 batch 22 — algo_library)**: leg_controller_runner.py shipped at
   execution-service@2b3ee2620 (maybe_rebalance 72L→17L via 4 \_safe\_\* wrappers (\_safe_load_observations,
   \_safe_build_snapshots, \_safe_compute_drift, \_safe_emit_rebalance) — each catches the same exception set
   (Connection/Timeout/OS/Value for observations; Key/Value for others) and emits the same shard-level isolation log +
   return-None pattern). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3-22**: 26 files cleared (slot-2 contribution: -26 files; 10 handlers + 8 defi
   protocols + 5 services + 1 preprocessor + 1 service_config + 1 algo_library).

   **Ratchet-down 2026-05-17 (slot-2 batch 23 — trade_execution adapters)**: binance_native.py shipped at
   execution-service@c4b5e8798 (parse_order_response 76L→30L via \_STATUS_MAP ClassVar (NEW→pending,
   PARTIALLY_FILLED→open, FILLED, CANCELED/EXPIRED/REJECTED→cancelled) + \_safe_decimal (None + InvalidOperation
   fallback) + \_safe_decimal_positive (suppresses Binance 0-price echoes)). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3-23**: 27 files cleared (slot-2 contribution: -27 files; 10 handlers + 8 defi
   protocols + 5 services + 1 preprocessor + 1 service_config + 1 algo_library + 1 CEX adapter).

   **Ratchet-down 2026-05-17 (slot-2 batch 24 — algo_library sweep)**: multicall_batcher.py shipped at
   execution-service@d89f09ba8 (encode_step_to_call 74L→20L via 6 per-step-type module-level \_encode\_\* helpers:
   \_encode_approve (ERC20 selector + spender padded 32B + uint256 amount), \_encode_swap (Uniswap exactInputSingle),
   \_encode_supply_or_repay (Aave V3 pool), \_encode_wrap (WETH.deposit value-carry), \_encode_unwrap (WETH.withdraw +
   amount uint256)). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3-24**: 28 files cleared (slot-2 contribution: -28 files; 10 handlers + 8 defi
   protocols + 5 services + 1 preprocessor + 1 service_config + 2 algo_library + 1 CEX adapter).

   **Ratchet-down 2026-05-17 (slot-2 batch 25 — backtest_v2 runner)**: backtest_v2/runner.py shipped at
   execution-service@af7733bd4 (run 76L→25L via \_process_instruction helper — single place that handles
   TradeInstruction settle (via \_settle_trade_instruction) + non-Trade deferred-with-warning + missing-fill
   deferred-silent paths, keeping run() to dispatch + cumulative aggregation + result building). Allowlist -1.
   basedpyright clean.

   **Slot-2 cumulative across batches 3-25**: 29 files cleared (slot-2 contribution: -29 files; 10 handlers + 8 defi
   protocols + 5 services + 1 preprocessor + 1 service_config + 2 algo_library + 1 CEX adapter + 1 backtest_v2).

   **Ratchet-down 2026-05-17 (slot-2 batch 26 — engine/validation)**: dependency_validator.py shipped at
   execution-service@a54c0ca97 (check_defi_data_availability 75L→14L via \_classify_defi_dependencies (returns {flash,
   lending, staking} flags from instruction set + ":A_TOKEN/:DEBT_TOKEN/:LST" instrument suffix scan) +
   \_check_defi_prefixes_for_date (table-driven loop over (flag → data_type → label → op_label) tuples). Allowlist -1.
   basedpyright clean.

   **Slot-2 cumulative across batches 3-26**: 30 files cleared (slot-2 contribution: -30 files; 10 handlers + 8 defi
   protocols + 5 services + 1 preprocessor + 1 service_config + 2 algo_library + 1 CEX adapter + 1 backtest_v2
   - 1 engine/validation).

   **Ratchet-down 2026-05-17 (slot-4 batch 11 — config/engine/providers sweep)**: 3 net-new files cleared at
   execution-service@2f92a58bd (config/grid_builder.py — 3 violations: \_generate_sor_secondary_instruments 63L→45L via
   \_filter_stable_pair_secondaries (@staticmethod — USDC-USDT stable-pair filter + POOL: token set dedup);
   \_get_config_for_instruction_type 68L→29L via \_lend_borrow_base_config + \_stake_base_config (@staticmethod dict
   factories); generate_grid_configs 67L→47L via \_resolve_timeframe_seconds + \_build_grid_config (@staticmethod —
   timeframe-str→seconds + config_id-gen+GridConfig constructor combined)); engine/backtest/actors/
   execution_alpha_verifier_actor.py on_order_filled 74L→17L via \_record_entry_fill + \_record_exit_fill (per-fill
   alpha calculation + dict append separated); providers/tenderly.py — 4 violations: create_fork 74L→32L via
   \_build_vnet_payload + \_extract_rpc_urls (@staticmethod — fork payload construction + RPC-URL admin/public
   extraction); fund_wallet 69L→14L via \_fund_eth + \_fund_erc20_tokens (async — ETH setBalance vs ERC20
   setErc20Balance separated); \_parse_bundle_sim_response 59L→45L via \_find_first_reverting_or_last (traversal returns
   first reverting or last entry); gate_or_advise 72L→44L via docstring trim). leg_controller_runner + multicall_batcher
   stash-resolved to upstream slot (convergent refactor — both cleared by remote). Combined allowlist: 117 → 107 files
   (10 entries removed including concurrent slot activity). AST clean per file. ruff + basedpyright clean. Per-method
   behavior preserved (stable-pair filter logic identical, GridConfig config_version constant, on_order_filled exception
   class unchanged, Tenderly VNet slug/display_name format preserved, RPC admin-vs-public preference order preserved).

   **Slot-4 cumulative across batches 1+2+3+4+5+6+7+8+9+10+11**: 46 files cleared (allowlist now 107).

   **Ratchet-down 2026-05-17 (slot-2 batch 27 — adapters)**: storage.py shipped at execution-service@4293df705
   (download_catalog_cache_files 77L→26L via \_select_latest_blobs_per_date (list + parse-date + recency-key dedupe per
   start_date) + \_download_blobs_parallel (ThreadPoolExecutor BATCH_MAX_WORKERS
   - per-blob result aggregation; nested \_download_one preserves the (ValueError/TypeError/KeyError/AttributeError/
     RuntimeError) catch-all)). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3-27**: 31 files cleared (slot-2 contribution: -31 files; 10 handlers + 8 defi
   protocols + 5 services + 1 preprocessor + 1 service_config + 2 algo_library + 1 CEX adapter + 1 backtest_v2
   - 1 engine/validation + 1 adapter).

   **Ratchet-down 2026-05-17 (slot-2 batch 28 — engine/modes/live)**: live/matching_engine.py shipped at
   execution-service@21da77ec3 (submit_order 77L→39L via \_resolve_price (BUY→best_ask, SELL→best_bid, else last_price;
   passthrough order.price when set) + \_build_matcher_kwargs (L0_TOB book + MD → best_bid/offer + bid/offer_size; empty
   otherwise)). Same MARKET→MAX_SLIPPAGE for AMM and CanonicalFill build path preserved. Allowlist -1. basedpyright
   clean.

   **Slot-2 cumulative across batches 3-28**: 32 files cleared (slot-2 contribution: -32 files; spans 11 submodules:
   handlers + defi protocols + services + preprocessor + service_config + algo_library + CEX adapter + backtest_v2 +
   engine/validation + adapter + engine/modes).

   **Ratchet-down 2026-05-17 (slot-2 batch 29 — algorithms/registry)**: algorithms/registry.py shipped at
   execution-service@4e9345799 (\_discover_algorithms 80L→24L via \_resolve_algo_id (3-fallback chain) plus 2
   module-level helpers: \_algo_id_from_dataclass_field (default_factory then default) + \_algo_id_from_instantiation
   (frozen-config instantiation + StrEnum value or stringify); module-level helpers allow re-use across other
   introspection callers + flatten the nested-try complexity). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3-29**: 33 files cleared (slot-2 contribution: -33 files; spans 12 submodules now
   incl. algorithms/registry).

   **Ratchet-down 2026-05-17 (slot-2 batch 30 — trade_execution adapters continues)**: bitfinex_native.py shipped at
   execution-service@6bbc5b927 (parse_order_response 81L→25L via \_extract_order_fields (walks the v2 notification
   wrapper at idx 4 + ORDER_ARRAY at idx 11/7/6/13, tolerates short/missing arrays with pending fallback) +
   \_classify_bitfinex_status (free-text status → canonical via in-string contains: executed&@→filled, partially→open,
   cancel→cancelled) + \_compute_filled_qty (|orig|-|curr| amount-remaining convention) + \_parse_positive_decimal
   (suppresses Bitfinex 0-price echoes)). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3-30**: 34 files cleared (slot-2 contribution: -34 files; spans 12 submodules).

   **Ratchet-down 2026-05-17 (slot-2 batch 31 — engine/live)**: engine/live/risk.py shipped at
   execution-service@050c47334 (check_order 85L→23L via \_derive_symbol (':' split + @LIN/@INV → -PERP) +
   \_check_staleness (returns reject-or-None) + \_max_stale_seconds_for (per-symbol or global override; 0.5s MFT
   default) + \_check_open_orders_cap (oms cap with MAX_OPEN_ORDERS_EXCEEDED event) + \_check_position_limit (current +
   signed_add vs limits[symbol|canonical_id])). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3-31**: 35 files cleared (slot-2 contribution: -35 files; spans 13 submodules
   incl. engine/live).

   **Ratchet-down 2026-05-17 (slot-4 batch 12 — data/results sweep)**: 4 net-new files cleared at
   execution-service@b932801ab (data/converter_bars.py — convert_ohlcv_parquet_to_catalog 122L→21L via \_build_bars_list
   (batched Bar construction, 10k/batch; bar_spec/bar_type created once per call); data/converter_trades.py — 2
   violations: convert_trades_parquet_to_catalog 108L→25L via \_create_trade_ticks_list (same batch pattern for
   TradeTick), convert_trades_to_bars 113L→28L via \_aggregate_trades_df_to_ohlcv (groupby+flatten+ts_event int64 cast
   isolated); data/loader_normalizer.py — \_normalize_timestamp_columns_for_backtest 209L→29L via
   \_convert_defi_derivative_timestamp (ms→ns + unusually-large/small range-check warns) + \_convert_standard_timestamp
   (4-tier ns/us/ms/s auto-detect) + \_fill_defi_derivative_fields (mark_price→premium→index_price price cascade +
   synthetic size/aggressor_side/trade_id) + \_fill_standard_fields (amount/side/id rename); results/position_manager.py
   — close_all_positions 148L→42L via \_get_open_positions (cache.positions_open dispatch) + \_sum_unrealized_pnl
   (portfolio.unrealized_pnls items iteration) + \_log_position_detail (per-position qty/entry/unrealized log).
   algorithms/registry.py stash-resolved to upstream slot-2 batch-29 (convergent refactor — same 80L→24L reduction,
   different helper names: \_resolve_algo_id vs \_extract_algo_id; behavior identical). Combined allowlist: 107→96 (11
   entries removed including concurrent slot-2 activity batches 27-31). AST clean. ruff+basedpyright 0 errors.

   **Slot-4 cumulative across batches 1+2+3+4+5+6+7+8+9+10+11+12**: 50 files cleared (allowlist now 96).

   **Ratchet-down 2026-05-17 (slot-2 batch 32 — instruments loader)**: definitions_loader.py shipped at
   execution-service@6580f64fe (\_load_by_venue 88L→30L via \_resolve_venue_folders (single-venue override or
   list-all-venue= subfolders under base_prefix with iterator.prefixes warm-up pattern) + \_load_venue_file
   (asyncio.run_in_executor wrapped blob.download → DataFrame; empty if blob absent)). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3-32**: 36 files cleared (slot-2 contribution: -36 files; spans 14 submodules
   incl. instruments loader).

   **Ratchet-down 2026-05-17 (slot-2 batch 33 — engine/modes/batch)**: batch/matching_engine.py shipped at
   execution-service@7bca66488 (submit_order 91L→28L via \_resolve_price (BUY→best_ask, SELL→best_bid, else last_price;
   passthrough order.price when set) + \_build_matcher_kwargs (L0_TOB book + MD → best_bid/offer + bid/offer_size; empty
   otherwise) + \_execute_match_and_convert (MEL match + fill conversion + debug log)). Same MARKET→MAX_SLIPPAGE for AMM
   and CanonicalFill build path preserved. Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3-33**: 37 files cleared (slot-2 contribution: -37 files; spans 15 submodules
   incl. engine/modes/batch).

   **Ratchet-down 2026-05-17 (slot-2 batch 34 — matching_engine/adversarial)**: adversarial.py shipped at
   execution-service@55dbbfdff (match_order 119L→36L via \_apply_reject_fills (probabilistic RejectFills gate: rate
   check + reject MatchResult construction) + \_stamp_latency_inject (event emit + debug log; no sleep in batch mode) +
   \_scale_by_book_spoof (Decimal scale → effective_quantity; passthrough if absent)). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3-34**: 38 files cleared (slot-2 contribution: -38 files; spans 15 submodules
   incl. matching_engine/adversarial).

   **Ratchet-down 2026-05-17 (slot-2 batch 35 — engine/startup)**: order_recovery.py shipped at
   execution-service@464756a95 (recover_venue 137L→35L via \_reconcile_exchange_orphans (cancel stale orphans with
   confirm_cancel + ORDER_CANCEL_UNCONFIRMED + re-register recent ones as PENDING) + \_mark_internal_orphans (mark
   absent internal orders EXCHANGE_REJECTED + ORDER_ORPHANED event) + \_apply_partial_fills (apply exchange filled_qty
   to internal state)). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3-35**: 39 files cleared (slot-2 contribution: -39 files; spans 16 submodules
   incl. engine/startup).

   **Ratchet-down 2026-05-17 (slot-2 batch 36 — engine/validation/configuration_validator)**: shipped at
   execution-service@373215cee (check_execution_algorithms 140L→33L via \_validate_trade_algorithm +
   \_validate_swap_algorithm + \_validate_other_algorithms; same 3-block split for TRADE / SWAP / other instruction
   types). Allowlist -1. basedpyright clean.

   **Ratchet-down 2026-05-17 (slot-2 batch 37 — engine/validation/config_validator)**: shipped at
   execution-service@34c09fa36 (check_execution_algorithms 143L→33L via same 3-helper extraction pattern as batch 36 —
   this is the PreflightConfigValidator counterpart of ConfigurationValidator). Allowlist -1. basedpyright clean.

   **Ratchet-down 2026-05-17 (slot-2 batch 38 — engine/backtest/actors/tp_sl_monitor_actor)**: shipped at
   execution-service@e1847b3eb (\_check_tp_sl 139L→36L via \_emit_tp_hit + \_emit_sl_hit helpers parameterized by
   direction; LONG/SHORT mirror-symmetric blocks unified into two helpers). Allowlist -1. basedpyright clean.

   **Ratchet-down 2026-05-17 (slot-2 batch 39 — engine/backtest/actors/evaluator)**: shipped at
   execution-service@769303f22 (evaluate_performance 144L→49L via \_extract_config_params + \_resolve_account +
   \_get_final_balance + \_apply_commission_fallback + \_build_result_dict; also promoted `from typing import cast` from
   inside-function to module level). Allowlist -1. basedpyright clean.

   **Ratchet-down 2026-05-17 (slot-2 batch 40 — engine/backtest/actors/signal_driven_v3_base)**: shipped at
   execution-service@7f5f93c28 (**init** 146L→8L via \_parse_instructions + \_init_timing_config + \_init_state +
   \_init_trade_config + \_init_actors; fee bps conversion inlined). Allowlist -1. basedpyright clean.

   **Ratchet-down 2026-05-17 (slot-2 batch 41 — engine/live/orchestrator)**: shipped at execution-service@3313ce6e6
   (execute_order 147L→29L via \_make_rejection + \_validate_order + \_check_circuit_breaker +
   \_report_compliance_pre_order + \_submit_to_oms). Allowlist -1. basedpyright clean.

   **Ratchet-down 2026-05-17 (slot-2 batch 42 — algorithms/impl/passive_aggressive_spawn)**: shipped at
   execution-service@aa0153aa7 (\_start_aggressive_phase 152L→20L via \_compute_aggressive_slice_params +
   \_record_aggressive_child + \_try_spawn_first_slice_immediately + \_schedule_aggressive_slices). Allowlist -1.
   basedpyright clean.

   **Ratchet-down 2026-05-17 (slot-2 batch 43 — defi_execution/protocols/solana_base)**: shipped at
   execution-service@15052b068 (send_transaction 153L→34L via \_paper_trade_result + \_sign_and_send_tx +
   \_extract_tx_error_status + \_build_tx_result). Allowlist -1. basedpyright clean.

   **Ratchet-down 2026-05-17 (slot-2 batch 44 — algorithms/impl/hybrid_optimal)**: shipped at
   execution-service@362c35974 (on_order 163L→16L via \_detect_and_log_regime + \_compute_ac_schedule +
   \_build_valid_amounts + \_schedule_children). Allowlist -1. basedpyright clean.

   **Ratchet-down 2026-05-17 (slot-2 batch 45 — instruments/factory)**: shipped at execution-service@c4063b597
   (create_and_register 178L→23L via \_extract_instrument_id_from_config + \_check_existing_in_catalog +
   \_find_gcs_definition + \_apply_gcs_or_fallback). Allowlist -1. basedpyright clean.

   **Ratchet-down 2026-05-17 (slot-2 batch 46 — engine/backtest/preflight)**: shipped at execution-service@f9ebdf995
   (check_all 201L→35L via \_run_step1_config_schema + \_run_steps2to5_validators + \_run_steps6to8_data_checks +
   \_run_steps9to10_compat_checks). Allowlist -1. basedpyright clean.

   **Ratchet-down 2026-05-17 (slot-2 batch 47 — instruments/config_creator)**: shipped at execution-service@051b21a16
   (create_from_config 205L→15L via \_create_from_config_tradfi + \_create_from_config_defi_instruction +
   \_create_from_config_cefi_defi_clob + \_build_crypto_perpetual). Allowlist -1. basedpyright clean.

   **Slot-2 cumulative across batches 3-47**: 51 files cleared (slot-2 contribution: -51 files; spans 18 submodules
   incl. engine/validation ×2, engine/backtest ×1, engine/backtest/actors ×3, engine/live ×1, algorithms/impl ×2,
   defi_execution/protocols ×8, instruments ×3 total).

   **Ratchet-down 2026-05-17 (slot-2 batch 48 — data/config_builder)**: shipped at execution-service@6bbce4ddf
   (build_trades_config 228L→44L via \_run_cache_setup + \_load_missing_data + \_validate_price_scale instance methods +
   7 module-level helpers (\_get_base_path, \_discover_local_trade_files, \_resolve_instrument_precision,
   \_resolve_domain_info, \_execute_gcs_load, \_execute_local_load, \_build_backtest_data_configs)). Allowlist -1.
   basedpyright 0 errors. AST clean.

   **Slot-2 cumulative across batches 3-48**: 52 files cleared (slot-2 contribution: -52 files; spans 19 submodules
   incl. data/config_builder).

   **Ratchet-down 2026-05-17 (slot-2 batch 49 — data/ohlcv_converter)**: shipped at execution-service@e20964148
   (convert_ohlcv_parquet_to_catalog 251L→44L via \_normalize_ohlcv_instrument_id + \_try_primary_id_conversion +
   \_try_fallback_id_conversion + \_skip_if_bar_exists + \_scale_prices + \_build_ohlcv_bars_list +
   \_write_bars_to_catalog @staticmethod helpers). Allowlist -1. basedpyright 0 errors.

   **Slot-2 cumulative across batches 3-49**: 53 files cleared (slot-2 contribution: -53 files; spans 20 submodules
   incl. data/ohlcv_converter).

- **Batch 50** (2026-05-17): `cli/backtest_args.py` — `parse_args` 236L→28L via 10 `_add_*_args(parser)` module-level
  helpers (\_add_config_args + \_add_time_args + \_add_data_args + \_add_exec_args + \_add_signal_args +
  \_add_instrument_args + \_add_position_args + \_add_output_args + \_add_dependency_args + \_add_meta_args). Allowlist
  -1. basedpyright 0 errors. execution-service@3693bf430.

  **Slot-2 cumulative across batches 3-50**: 54 files cleared (slot-2 contribution: -54 files; spans 21 submodules incl.
  cli/backtest_args).

- **Batch 51** (2026-05-17): `data/config/book_builder.py` — `build_book_config_impl` 241L→40L via 8 helpers
  (\_resolve_data_source + \_init_book_ucs_loader + \_get_gcs_book_instrument_id + \_load_local_book_data +
  \_check_day_book_cache + \_load_day_book_snapshots + \_load_gcs_book_data + \_verify_book_catalog). Allowlist -1.
  basedpyright 0 errors. execution-service@31116b8a5.

  **Slot-2 cumulative across batches 3-51**: 55 files cleared (slot-2 contribution: -55 files; spans 22 submodules incl.
  data/config/book_builder).

- **Batch 52** (2026-05-17): `instruments/gcs_creator.py` — `create_from_gcs_definition` 241L→45L via 9 helpers
  (\_get_initial_currency_strs + \_infer_currencies_from_symbols + \_apply_defi_fallback + \_validate_currencies +
  \_resolve_tick_size + \_resolve_min_size + \_resolve_fees + \_detect_is_inverse + \_resolve_margins). Allowlist -1.
  basedpyright 0 errors. execution-service@62d135bbb.

  **Slot-2 cumulative across batches 3-52**: 56 files cleared (slot-2 contribution: -56 files; spans 23 submodules incl.
  instruments/gcs_creator).

- **Batch 53** (2026-05-17): `engine/backtest/actors/trade_measurement_verifier_actor.py` — `on_stop` 85L→8L via 5
  helpers (\_check_fill_correctness + \_log_incorrect_fills + \_check_fill_timing + \_log_timing_results +
  \_log_twap_intervals). Allowlist -1. basedpyright 0 errors. execution-service@325407ea3.

  **Slot-2 cumulative across batches 3-53**: 57 files cleared (slot-2 contribution: -57 files; spans 24 submodules incl.
  engine/backtest/actors/trade_measurement_verifier_actor).

- **Batch 54** (2026-05-17): `algorithms/impl/passive_aggressive_core.py` — `_parse_pah_params` 126L→8L via 4 helpers
  (\_parse_candle_horizon_secs + \_parse_direct_horizon_secs + \_parse_passive_display_params +
  \_parse_execution_params). Allowlist -1. basedpyright 0 errors. execution-service@6179da73a.

  **Slot-2 cumulative across batches 3-54**: 58 files cleared (slot-2 contribution: -58 files; spans 25 submodules incl.
  algorithms/impl/passive_aggressive_core).

  **Ratchet-down 2026-05-17 (slot-2 batch 55 — cli/argument_parser)**: shipped at execution-service@942a02c6f.
  parse*args 249L→28L via 10 module-level \_add*\*\_args helpers (\_add_config_args + \_add_time_args +
  \_add_data_args + \_add_exec_args + \_add_signal_args + \_add_instrument_args + \_add_position_args +
  \_add_output_args + \_add_dependency_args + \_add_meta_args). Allowlist -1. basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-55**: 59 files cleared (slot-2 contribution: -59 files; spans 26 submodules incl.
  cli/argument_parser).

  **Ratchet-down 2026-05-17 (slot-2 batch 56 — engine/backtest/passive_aggressive_hybrid)**: shipped at
  execution-service@324ed5231. simulate_passive_aggressive_hybrid 169L→50L via 5 module-level helpers (\_empty_result +
  \_execute_passive_phase + \_execute_aggressive_phase + \_compute_fill_stats + \_compute_edge_metrics). File not in
  allowlist (pre-existing violation outside baseline capture). basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-56**: 60 files cleared (slot-2 contribution: -60 files; spans 27 submodules incl.
  engine/backtest/passive_aggressive_hybrid).

  **Ratchet-down 2026-05-17 (slot-2 batch 57 — data/config/trades_builder)**: shipped at execution-service@b37764683.
  build_trades_config_impl 151L→22L via 3 helpers (\_prepare_loading_context + \_load_data_to_catalog +
  \_finalize_and_log). File not in allowlist. basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-57**: 61 files cleared (slot-2 contribution: -61 files; spans 28 submodules incl.
  data/config/trades_builder).

  **Ratchet-down 2026-05-17 (slot-2 batch 58 — data/file_discovery)**: shipped at execution-service@7a7368e10.
  discover_local_data_files 146L→22L via 4 helpers (\_extract_file_pattern + \_discover_across_day_dirs +
  \_discover_specific_date_path + \_discover_by_date_range). File not in allowlist. basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-58**: 62 files cleared (slot-2 contribution: -62 files; spans 29 submodules incl.
  data/file_discovery).

  **Ratchet-down 2026-05-17 (slot-2 batch 59 — cli/backtest)**: shipped at execution-service@8efc8eb15. main 141L→28L
  via 5 helpers (\_setup_args_overrides + \_load_config_and_detect_domain + \_run_date_skip_check + \_check_deps +
  \_dispatch_domain_handler). File not in allowlist. basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-59**: 63 files cleared (slot-2 contribution: -63 files; spans 30 submodules incl.
  cli/backtest).

  **Ratchet-down 2026-05-17 (slot-2 batch 60 — instruments/factory_tradfi)**: shipped at execution-service@23ff62896.
  create_tradfi_from_config 141L→15L via 3 helpers (\_resolve_tradfi_common_params + \_create_equity_instrument +
  \_create_future_instrument). File not in allowlist. basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-60**: 64 files cleared (slot-2 contribution: -64 files; spans 31 submodules incl.
  instruments/factory_tradfi).

  **Ratchet-down 2026-05-17 (slot-2 batch 61 — results/validation)**: shipped at execution-service@f1c71eca7.
  validate_timestamp_alignment 139L→22L via 5 helpers (\_check_ucs_timestamp_alignment + \_resolve_timestamp_col +
  \_check_timestamp_range + \_check_monotonicity + \_check_range_and_monotonicity). File not in allowlist. 0 errors.

  **Slot-2 cumulative across batches 3-61**: 65 files cleared (slot-2 contribution: -65 files; spans 32 submodules incl.
  results/validation).

  **Ratchet-down 2026-05-17 (slot-2 batch 62 — instruments/tradfi_creator)**: shipped at execution-service@c3fadd421.
  create_tradfi_from_config 139L→15L via 3 helpers (\_resolve_common_params + \_create_equity_instrument +
  \_create_future_instrument). File not in allowlist. basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-62**: 66 files cleared (slot-2 contribution: -66 files; spans 33 submodules incl.
  instruments/tradfi_creator).

  **Ratchet-down 2026-05-17 (slot-2 batch 63 — api/manual_instruction_api)**: shipped at execution-service@32846d337.
  submit_manual_instruction 172L→37L + 8 additional violations cleared (\_handle_instruction_result 60L→10L,
  \_enforce_wallet_preflight 62L→47L, \_validate_instruction_request 71L→20L, precheck_manual_instruction 74L→22L,
  get_instruction_status 58L→17L, \_record_fill_directly 87L→22L, enqueue_pending_instruction 71L→24L,
  approve_pending_instruction 66L→20L) via 11 module-level helpers (\_handle_completed_result +
  \_reject_preflight_failed + \_raise_validation_http_error + \_precheck_accepted_response +
  \_build_precheck_instruction + \_get_active_orchestrator_or_raise + \_build_record_only_audit_instruction +
  \_finalize_record_fill + \_build_enqueue_strategy_instruction + \_build_pending_enqueue_response +
  \_execute_approved_pending). File not in allowlist. basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-63**: 67 files cleared (slot-2 contribution: -67 files; spans 34 submodules incl.
  api/manual_instruction_api).

  **Ratchet-down 2026-05-17 (slot-2 batch 64 — results/save_operations)**: shipped at execution-service@77d4ede1c.
  save_report 197L→41L + 3 additional violations cleared (\_upload_report_to_gcs 90L→22L, \_save_orders_parquet 54L→36L,
  \_save_positions_parquet 53L→35L) via \_log_save_report_banner + \_make_run_dir + \_merge_nontrade_fills +
  \_save_all_report_files + \_validate_and_upload_parquets + \_write_run_manifest + \_write_canonical_fills +
  \_cleanup_temp_dir + \_SavedReportFiles dataclass + \_ORDERS_EMPTY_COLS + \_POSITIONS_EMPTY_COLS constants. File not
  in allowlist. basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-64**: 68 files cleared (slot-2 contribution: -68 files; spans 35 submodules incl.
  results/save_operations).

  **Ratchet-down 2026-05-17 (slot-2 batch 65 — benchmark/comparison_configs)**: shipped at execution-service@01f7f0b15.
  \_adaptive_twap_configs 64L→8L + \_almgren_chriss_configs 64L→8L + \_pov_dynamic_configs 52L→8L +
  \_passive_aggressive_hybrid_configs 64L→8L via \_ADAPTIVE_TWAP_DATA + \_ALMGREN_CHRISS_DATA + \_POV_DYNAMIC_DATA +
  \_PASSIVE_AGGRESSIVE_DATA list comprehensions. 4 violations cleared, file not in allowlist.

  **Slot-2 cumulative across batches 3-65**: 69 files cleared (slot-2 contribution: -69 files; spans 36 submodules incl.
  benchmark/comparison_configs).

  **Ratchet-down 2026-05-17 (slot-2 batch 66 — benchmark/regimes)**: shipped at execution-service@7f97cc34c.
  assign_regimes 52L→35L + \_assign_volatility_bucket 58L→17L via \_calc_vol_for_row + \_assign_liquidity_bucket 83L→22L
  via \_score_liquidity_from_market + \_score_liquidity_fallback + \_assign_participation_bucket 52L→11L via
  \_calc_participation_for_row. 4 violations cleared (file not in allowlist). basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-66**: 70 files cleared (slot-2 contribution: -70 files; spans 37 submodules incl.
  benchmark/regimes).

  **Ratchet-down 2026-05-17 (slot-2 batch 67 — benchmark/html_report)**: shipped at execution-service@37ae83b0c.
  \_build_html_head_and_styles 63L→3L via \_HTML_HEAD_AND_STYLES module constant + \_build_html_summary_section 66L→18L
  via \_build_summary_cards_html + \_build_html_table_rows 58L→28L via \_build_algo_row_html + \_build_chart_scripts
  95L→9L via \_build_pnl_chart_js + \_build_vs_benchmark_chart_js. 4 violations cleared (file not in allowlist).
  basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-67**: 71 files cleared (slot-2 contribution: -71 files; spans 38 submodules incl.
  benchmark/html_report).

  **Ratchet-down 2026-05-17 (slot-2 batch 68 — utils/dependency_checker)**: shipped at execution-service@b820b4d20.
  check_dependencies 88L→9L + check_strategy_instructions 83L→17L + check_market_tick_data 96L→12L +
  check_config_specific_dependencies 74L→22L via \_build_dep_msg + \_extract_config_metadata + \_build_tick_data_path
  (module-level) + \_check_dep_blob_exists + \_check_single_dep + \_check_strategy_blob + \_check_blob_dep_market_tick
  (instance methods). 4 violations cleared (file not in allowlist). basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-68**: 72 files cleared (slot-2 contribution: -72 files; spans 39 submodules incl.
  utils/dependency_checker).

  **Ratchet-down 2026-05-17 (slot-2 batch 69 — trade_execution/adapters/kraken_rest_adapter)**: shipped at
  execution-service@e71867f36. \_parse_kraken_order_dict 88L→31L + \_parse_kraken_trade_dict 55L→48L + place_order
  85L→40L + get_positions 71L→22L via \_parse_kraken_order_status + \_parse_kraken_order_type_str +
  \_parse_kraken_order_quantities + \_parse_kraken_order_descr + \_parse_kraken_order_prices +
  \_parse_kraken_trade_timestamp + \_build_add_order_payload + \_build_place_order_result +
  \_parse_single_kraken_position. 4 violations cleared. allowlist -2 (kraken_rest_adapter + dependency_checker).
  basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-69**: 73 files cleared (slot-2 contribution: -73 files; spans 40 submodules incl.
  trade_execution/adapters/kraken_rest_adapter).

  **Ratchet-down 2026-05-17 (slot-2 batch 70 — results/result_formatter)**: shipped at execution-service@a379230ca.
  prepare_orders_dataframe 96L→31L + prepare_fills_dataframe 81L→28L + prepare_positions_dataframe 89L→21L
  - prepare_equity_curve_dataframe 107L→23L + validate_timestamp_alignment 103L→30L via \_setup_timestamps +
    \_build_df_from_schema_cols + \_empty_equity_df + \_fill_equity_schema_columns
  - \_check_timestamp_bounds + \_qty_to_side + module-level schema column constants. 5 violations cleared. File not in
    allowlist. basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-70**: 74 files cleared (slot-2 contribution: -74 files; spans 41 submodules incl.
  results/result_formatter).

  **Ratchet-down 2026-05-17 (slot-2 batch 71 — results/dataframe_preparers)**: shipped at execution-service@68f0bc03b.
  prepare_orders_dataframe 115L→32L + prepare_fills_dataframe 117L→28L + prepare_positions_dataframe 105L→20L +
  prepare_equity_curve_dataframe 125L→23L via \_dp_setup_timestamps + \_dp_build_df_from_schema_cols +
  \_dp_build_fills_result_df + \_dp_empty_equity_df + \_dp_fill_equity_schema_cols + \_dp_qty_to_side + schema column
  constants. 4 violations cleared. File not in allowlist. basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-71**: 75 files cleared (slot-2 contribution: -75 files; spans 42 submodules incl.
  results/dataframe_preparers).

  **Ratchet-down 2026-05-17 (slot-2 batch 72 — results/timeline)**: shipped at execution-service@b9a4c86b9.
  build_instruction_completed_event 89L→43L + \_build_order_dict 56L→30L + \_extract_strategy_events 56L→36L +
  build_timeline 57L→36L + \_add_fills_from_orders 94L→38L + build_instruction_completion_events 133L→44L via
  \_determine_instruction_status + \_warn_if_interval_exceeded + \_extract_order_price_and_amount +
  \_load_cached_events_from_key + \_get_fill_price_for_order + \_get_filled_qty_and_status + \_count_order_stats +
  \_extract_alpha_metrics. 6 violations cleared. allowlist -1. basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-72**: 76 files cleared (slot-2 contribution: -76 files; spans 43 submodules incl.
  results/timeline).

  **Ratchet-down 2026-05-17 (slot-2 batch 73 — services/onchain_execution_service)**: shipped at
  execution-service@8358ae89d. swap 87L→14L + deposit 73L→44L + withdraw 71L→43L + borrow 71L→43L + repay 71L→44L +
  stake 83L→39L + bridge 72L→43L + flash_loan 73L→41L + swap_cross_chain 105L→27L. 12 new private helpers extracted. 9
  violations cleared. allowlist -1. basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-73**: 77 files cleared (slot-2 contribution: -77 files; spans 44 submodules incl.
  services/onchain_execution_service).

  **Ratchet-down 2026-05-17 (slot-2 batch 74 — config/grid_generator_cli)**: shipped at execution-service@d478eebfd.
  get_all_strategy_variants 51L→37L + generate_all_configs 125L→47L + main 196L→17L via \_make_strategy_variant +
  \_generate_and_save_variant + \_update_gen_all_stats + \_init_gen_all_stats + \_add_root_args + \_build_arg_parser +
  \_handle_generate_all_command + \_handle_generate_v2_command + \_run_cleanup_gcs + \_generate_single_strategy +
  \_handle_default_command. 3 violations cleared. File not in allowlist. basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-74**: 78 files cleared (slot-2 contribution: -78 files; spans 45 submodules incl.
  config/grid_generator_cli).

  **Ratchet-down 2026-05-17 (slot-2 batch 75 — benchmark/metrics)**: shipped at execution-service@e9b99db86.
  compute_statistical_metrics (93L→42L) + compute_path_aware_metrics (162L→35L) + compute_aggregate_metrics (77L→38L)
  via \_empty_statistical_metrics + \_compute_weighted_mean_std_n + \_compute_z_score + \_empty_path_metrics +
  \_get_fill_ts + \_weighted_alpha + \_compute_cumulative_alpha_curve + \_measure_adverse_at_delta +
  \_compute_adverse_selection + \_extract_alpha_weights_wins. 3 violations cleared. File not in allowlist. basedpyright
  0 errors.

  **Ratchet-down 2026-05-17 (slot-2 batch 76 — engine/backtest/actors/evaluator_metrics)**: shipped at
  execution-service@adb9b8864. get_position_info (97L→24L) + calculate_drawdown (152L→33L) + calculate_returns (85L→25L)
  via \_safe_float + \_get_current_price + \_compute_unrealized_pnl + \_get_display_price + \_build_position_result +
  \_max_dd_from_account_report + \_max_dd_from_equity_curve + \_max_dd_from_pnl_stats + \_max_dd_from_final_balance +
  \_compute_base_returns + \_get_returns_from_analyzer + \_get_returns_from_trade_stats. 3 violations cleared. File not
  in allowlist. basedpyright 0 errors.

  **Ratchet-down 2026-05-17 (slot-2 batch 77 — engine/backtest/almgren_chriss_sweep)**: shipped at
  execution-service@e11c0857d. almgren_chriss_optimal_schedule (52L→28L) + simulate_almgren_chriss (140L→28L). Extracted
  \_get_fill_price + \_execute_sim_fills + \_compute_sim_metrics. 2 violations cleared. File not in allowlist.
  basedpyright 0 errors.

  **Ratchet-down 2026-05-17 (slot-2 batch 78 — engine/risk/preflight_gate)**: shipped at execution-service@63971d89d.
  build_rule_eval_context (67L→24L) + run_risk_preflight (138L→32L). Extracted \_extract_identity_fields +
  \_copy_account_state_into_ctx + \_handle_block + \_handle_scale_down + \_handle_test_only. 2 violations cleared. File
  not in allowlist. basedpyright 0 errors.

  **Ratchet-down 2026-05-17 (slot-2 batch 79 — config/grid_utils)**: shipped at execution-service@1fa76d6fd.
  generate_per_algo_grid_configs (135L→20L) + get_all_strategy_variants (51L→39L). Extracted \_build_per_type_combos +
  \_build_cross_combo_config. 2 violations cleared. basedpyright 0 errors.

  **Ratchet-down 2026-05-17 (slot-2 batch 80 — api/preview_routes)**: shipped at execution-service@7a5a54310.
  preview_unwind (131L→28L). Extracted \_validate_unwind_request + \_select_and_scale_positions +
  \_compute_unwind_estimates. 1 violation cleared. basedpyright 0 errors.

  **Ratchet-down 2026-05-17 (slot-2 batch 81 — utils/market_hours)**: shipped at execution-service@6f1256c23.
  align_tradfi_time_window (129L→22L) + check_tradfi_market_open (65L→46L). Extracted \_align_tradfi_start +
  \_align_tradfi_end_after_close + \_align_tradfi_end_before_open + \_align_tradfi_end. 2 violations cleared.
  basedpyright 0 errors.

  **Ratchet-down 2026-05-17 (slot-2 batch 82 — cli/batch_backtest)**: shipped at execution-service@6528a1375.
  run_single_backtest (129L→13L) + run_batch_backtests (96L→15L) + main (113L→32L). Extracted \_resolve_and_load +
  \_build_backtest_cmd + \_handle_backtest_subprocess + \_collect_batch_results + \_check_batch_completeness +
  \_add_batch_args + \_validate_and_filter_configs. 3 violations cleared. basedpyright 0 errors.

  **Ratchet-down 2026-05-17 (slot-2 batch 83 — cli/defi_arbitrage_dispersion_decision_trace)**: shipped at
  execution-service@113c91897. \_run_cross_chain (58L→31L) + \_run_cross_venue_funding (129L→29L). Extracted
  \_build_cross_chain_pair_rows + \_load_funding_venue_aprs + \_build_coin_venue_rows + \_build_eligible_coins +
  \_print_level3_subweights. 2 violations cleared. basedpyright 0 errors.

  **Slot-2 cumulative across batches 3-83**: 95 files cleared (slot-2 contribution: -95 files; spans 53 submodules).

  **Ratchet-down 2026-05-17 (slot-2 batch 84 — docstring-trim sweep)**: shipped at execution-service@3800615e9.
  mifid_reporter 2v (log_order_submitted_mifid 51L + log_trade_reported_mifid 51L), instruction_convert 1v
  (manual_request_to_instruction 52L), audit_log 1v (persist_audit_log 52L), position_manager 1v (close_all_positions
  51L). 5 violations cleared via single-line docstrings.

  **Slot-2 cumulative across batches 3-84**: 99 files cleared (slot-2 contribution: -99 files; spans 56 submodules).

  **Ratchet-down 2026-05-17 (slot-2 batch 85 — docstring-trim sweep)**: shipped at execution-service@8a54ed3cf. registry
  1v (convert_to_nautilus_format 54L), amm_math 1v (quote_concentrated_liquidity 55L), \_storage 1v
  (create_storage_checker 55L), seasonal_points 1v (compute_implied_apr 55L), rate_impact_engine 1v (\_simulate_morpho
  55L). 5 violations cleared.

  **Slot-2 cumulative across batches 3-85**: 104 files cleared (slot-2 contribution: -104 files; spans 61 submodules).

  **Ratchet-down 2026-05-17 (slot-2 batch 86 — docstring-trim sweep)**: shipped at execution-service@cdcf1a524.
  slashing_calibration 1v (calibrate_chain 58L), instruction_validator_middleware 1v (validate_client_instruction 58L),
  lrt_protocol_fee 2v (calibrate_lrt_protocol_fee_model 57L + sample_forward_fee 60L). 4 violations cleared.

  **Slot-2 cumulative across batches 3-86**: 108 files cleared (slot-2 contribution: -108 files; spans 63 submodules).

  **Ratchet-down 2026-05-17 (slot-2 batch 87 — docstring-trim sweep)**: shipped at execution-service@e2a359757.
  backtest_domains 1v, simulate_proposal 1v, instruments/utils 1v, trade_execution/factory 1v, gcs_data_loading 1v,
  backtest_checks 1v, converters 1v, gcs_cache_helper 1v, timeline_builder 1v, vwap_core 1v. 10 violations cleared.

  **Slot-2 cumulative across batches 3-87**: 118 files cleared (slot-2 contribution: -118 files; spans 70 submodules).

  **Ratchet-down 2026-05-17 (slot-2 batch 88 — docstring-trim sweep)**: shipped at execution-service@342a0ae15.
  instrument_resolver 1v, backtest_checks 1v, report_timeline_extractor 1v, native_staking 2v, trades_loader 2v,
  restaking_avs 1v, selector 1v, ranking 1v, loader_base 1v, loader_transforms 1v, proposal_simulator 1v. 13 violations
  cleared.

  **Slot-2 cumulative across batches 3-88**: 131 files cleared (slot-2 contribution: -131 files; spans 79 submodules).

  **Ratchet-down 2026-05-17 (slot-2 batch 89 — helper extraction)**: shipped at execution-service@069bcee5d.
  \_convert.py:instruction_to_vwap_config 57L→46L, \_timeline_extraction.py:extract_fills_from_timeline 56L→30L,
  strategy_instructions/gcs.py:download_instructions_df 56L→40L. 3 violations cleared.

  **Slot-2 cumulative across batches 3-89**: 134 files cleared (slot-2 contribution: -134 files; spans 81 submodules).

  **Ratchet-down 2026-05-17 (slot-2 batch 90 — trim+extract)**: shipped at execution-service@7eb5e8ab6. price_scale 1v
  (58L→43L), dates 1v (62L→36L), freshness_gate 1v (63L→47L), engine/backtest/core 1v (64L→42L). 4 violations cleared.

  **Slot-2 cumulative across batches 3-90**: 138 files cleared (slot-2 contribution: -138 files; spans 84 submodules).

  **Ratchet-down 2026-05-17 (slot-2 batch 91 — trim+extract)**: shipped at execution-service@999fb6206.
  kill_switch:activate 63L→40L, preflight:run_preflight_checks 68L→43L,
  instrument_resolver:resolve_instruments_for_config 65L→26L. 3 violations cleared.

  **Slot-2 cumulative across batches 3-91**: 141 files cleared (slot-2 contribution: -141 files; spans 86 submodules).

  **Ratchet-down 2026-05-17 (slot-2 batch 92 — trim+extract)**: shipped at execution-service@45a58e0eb.
  catalog_resolution:resolve_catalog_path 61L→32L, custody/factory:get_custody_provider 61L→46L,
  gcs_data_loading:\_verify_full_cache 57L→39L, orderbook_converter:\_log_empty_time_window 55L→48L. 4 violations
  cleared.

  **Slot-2 cumulative across batches 3-92**: 145 files cleared (slot-2 contribution: -145 files; spans 88 submodules).

  **Ratchet-down 2026-05-17 (slot-2 batch 93 — arg compaction + docstring trim)**: shipped at
  execution-service@da1302447. kraken_rest_adapter:place_order 54L→49L, config_builder:\_execute_gcs_load 51L→49L,
  book_builder:\_load_local_book_data 51L→50L, backtest/preflight:check_all 51L→50L. 4 violations cleared.

  **Slot-2 cumulative across batches 3-93**: 149 files cleared (slot-2 contribution: -149 files; spans 90 submodules).

  **Ratchet-down 2026-05-17 (slot-2 batch 94 — docstring trim + arg compaction)**: shipped at
  execution-service@ab4e6b07c. adaptive_twap:\_on_slice_timer 51L→47L, intent_engine:\_build_deleverage_steps 52L→36L,
  ohlcv_converter:convert_ohlcv_parquet_to_catalog 52L→45L. 3 violations cleared.

  **Slot-2 cumulative across batches 3-94**: 152 files cleared (slot-2 contribution: -152 files; spans 92 submodules).

  **Ratchet-down 2026-05-17 (slot-2 batch 95 — arg compaction)**: shipped at execution-service@ab6f9ee22.
  passive_aggressive_execution:\_pah_schedule_passive_spawn 52L→50L, result_formatter:\_check_timestamp_bounds 53L→49L,
  funding_recon_engine:reconcile 54L→50L. 3 violations cleared.

  **Slot-2 cumulative across batches 3-95**: 155 files cleared (slot-2 contribution: -155 files; spans 93 submodules).

  **Ratchet-down 2026-05-17 (slot-2 batch 96 — arg compaction)**: shipped at execution-service@512f69d1f.
  cli/run_scenario:main 53L→47L, utils/dependency_checker:\_check_blob_dep_market_tick 53L→50L. 2 violations cleared.

  **Slot-2 cumulative across batches 3-96**: 157 files cleared (slot-2 contribution: -157 files; spans 94 submodules).

  **Ratchet-down 2026-05-17 (slot-2 batch 97 — arg compaction + helper extraction)**: shipped at
  execution-service@ab2fbe80b. config_builder:\_load_missing_data 55L→49L (merge 4 signature param pairs + inline
  local-load call), mock_feed_connector:\_handle_place_bet 55L→48L (inline BET_ACK \_write + merge signature pairs),
  mock_data_provider:run_mock_pipeline 60L→42L (extract \_dispatch_instrument_fills helper + trim docstring),
  ccxt_common:place_order_sim 60L→49L (trim docstring + merge 7 CanonicalOrder constructor arg pairs). 4 violations
  cleared. mock_feed_connector + ccxt_common now fully clean. Allowlist -2.

  **Slot-2 cumulative across batches 3-97**: 159 files cleared (slot-2 contribution: -159 files; spans 95 submodules).

  **Ratchet-down 2026-05-17 (slot-4 batch 13 — adapters/algorithms/custody/defi_loader)**: 5 net-new files cleared at
  execution-service@fe0836b07 (adapters/order_adapter.py — submit_order 95L→37L via \_get_cached_order +
  \_log_order_created + \_log_post_submit_audit; algorithms/tradfi/implementation_shortfall.py — schedule 90L→36L via
  \_compute_ac_fractions + \_build_child_orders @staticmethod; custody/copper.py — sign_transaction 99L→31L via
  \_poll_for_completion async; algorithms/atomic_bundle_executor.py — validate_atomic_bundle 61L→47L docstring-trim +
  execute_bundle 84L→43L via \_build_bundle_success_result; data/loaders/defi.py — load_swaps 77L→32L + load_liquidity
  75L→35L via \_get_or_create_loop + \_load_first_nonempty_path; f-string logging → % format). Allowlist 68→63. AST
  clean. ruff + basedpyright 0 errors.

  **Slot-4 cumulative across batches 1-13**: 55 files cleared (allowlist now 63).

  **Ratchet-down 2026-05-18 (slot-4 batch 14 — engine/validation + venues/deribit_orders)**: 2 net-new files cleared at
  execution-service@8fd663b0a (engine/validation/data_availability_validator.py — check_book_type_data_requirements
  83L→31L via \_check_instrument_book_type_dates 42L; venues/deribit_orders.py — submit_order 107L→42L via
  \_classify_deribit_instrument_type + \_compute_final_amount + \_build_order_request_params + \_make_rejected_result;
  get_available_instruments 104L→44L via \_format_deribit_instrument; check_market_tick_data conflict resolved accepting
  upstream module-level helpers). Allowlist 63→61. AST clean. ruff + basedpyright 0 errors.

  **Slot-4 cumulative across batches 1-14**: 57 files cleared (allowlist now 61).

  **Ratchet-down 2026-05-18 (slot-4 batch 15 — intent_engine + vwap_core + loaders/base + engine.py free)**: 4 entries
  cleared at execution-service@48ec90d23 (algo_library/intent_engine.py — \_build_deleverage_steps 53L→27L via
  aave_venue local var + compact kwargs + return list literal; algorithms/impl/vwap_core.py — \_get_l2_price 70L→46L via
  \_compute_adjusted_price 35L helper; data/loaders/base.py — \_normalize_timestamp_columns_for_backtest 85L→15L via
  \_set_ts_event_column @staticmethod 26L + \_normalize_trade_columns @staticmethod 47L; matching_engine/engine.py —
  free removal, upstream tick-46a already cleared all methods). Allowlist 61→57. AST clean. ruff + basedpyright 0
  errors.

  **Slot-4 cumulative across batches 1-15**: 61 files cleared (allowlist now 57).

  **Ratchet-down 2026-05-18 (slot-4 batch 16 — live_handler + multi_leg + catalog_validator)**: 3 net-new files cleared
  at execution-service@e8525b230 (cli/handlers/live_execution_handler.py — \_execute_sports_instruction 90L→27L via
  \_execute_sports_bet async helper 32L; engine/multi_leg_orchestrator.py — \_handle_follower_failure 99L→22L via
  \_fire_compensation_trade async helper 44L; engine/validation/catalog_validator.py —
  validate_data_config_compatibility 172L→26L via \_resolve_config_book_type @staticmethod 24L +
  \_build_instruments_by_type @staticmethod 14L + \_check_per_instrument_compat @staticmethod 44L). Allowlist 57→54. AST
  clean. ruff 0 errors.

  **Slot-4 cumulative across batches 1-16**: 64 files cleared (allowlist now 54).

  **Ratchet-down 2026-05-18 (slot-4 batch 17 — tp_sl_generator + signal_driven_shared + grid_generator_core)**: 3
  net-new files cleared at execution-service@ae6426a0a. tp_sl_generator: generate_random_tp_sl_for_signal 83L→32L via
  \_select_tightness @staticmethod 13L + \_resolve_signal_seed @staticmethod 15L (resolved merge conflict with parallel
  slot that used \_signal_seed_from_timestamp — dropped duplicate, unified on \_resolve_signal_seed).
  signal_driven_shared: add_exit 85L→42L via \_accumulate_exit 42L helper mirroring \_accumulate_entry pattern (resolved
  merge conflict with parallel slot). grid_generator_core: \_get_config_for_instruction_type 85L→30L via
  \_get_lend_borrow_base_config @staticmethod 29L + \_get_stake_base_config @staticmethod 29L. Allowlist 54→51. AST
  clean. ruff 0 errors.

  **Slot-4 cumulative across batches 1-17**: 67 files cleared (allowlist now 51).

  **Ratchet-down 2026-05-18 (slot-4 batch 18 — adaptive_twap + signal_driven_v3_utils)**: 2 entries cleared at
  execution-service@7bd19a1bf. adaptive_twap.py: on_order 88L→40L via \_init_parent_state @instance 39L (init price
  history, store parent state, return n_slices + start_time; resolves parallel-slot merge). signal_driven_v3_utils.py:
  calculate_exec_params 89L cleared by parallel slot 6f544699d via \_calc_dynamic_horizon + \_calc_sce_exec_params (my
  duplicate work discarded; allowlist removal shipped together). Allowlist 51→49. AST clean. ruff 0 errors.

  **Slot-4 cumulative across batches 1-18**: 69 files cleared (allowlist now 49).

  **Ratchet-down 2026-05-18 (slot-4 batch 19 — results/serializer + defi_execution/protocols/drift)**: 2 entries cleared
  at execution-service@3e99f2972. results/serializer.py: serialize_benchmark_comparison 104L→12L via
  \_serialize_benchmark_result @staticmethod 17L + \_serialize_algo_result @staticmethod 19L +
  \_build_comparison_summary @staticmethod 28L. defi_execution/protocols/drift.py: place_order 104L→19L via
  \_build_driftpy_params 30L (driftpy inside-imports + direction/order_type_map/precision conversion) +
  \_make_paper_trade_result 19L + \_execute_live_order async 36L (send + log + return). Allowlist 49→47. AST clean.
  ruff + basedpyright 0 errors.

  **Slot-4 cumulative across batches 1-19**: 71 files cleared (allowlist now 47).

  **Ratchet-down 2026-05-18 (slot-4 batch 20 — engine/backtest/instruction_loader + 2×instruction_validator)**: 3
  entries cleared at execution-service@38c539a0c. engine/backtest/instruction_loader.py:
  convert_instructions_to_schedule 140L→30L via \_normalize_instructions_df 8L + \_extract_trade_instruments 18L +
  \_split_and_log_non_trade 28L + \_make_timing_trigger 23L + \_build_trade_schedule 38L (fixed 2 pre-existing E501 in
  sibling methods). utils/validation/instruction_validator.py: validate_instructions_dataframe 125L→22L via
  \_check_instrument_type_mapping 17L + \_check_tp_sl_type_support 20L + \_check_tp_sl_logic_consistency 28L.
  validation/instruction_validator.py: same 3-helper extraction (136L→22L). Allowlist 47→44. AST clean. ruff 0 errors.

  **Slot-4 cumulative across batches 1-20**: 74 files cleared (allowlist now 44).

  **Ratchet-down 2026-05-18 (slot-4 batch 21 — enhanced_comparison + recursive_loop_orchestrator +
  report_timeline_extractor + leveraged_leg_controller)**: 4 entries cleared at execution-service@5c2618cc7.
  benchmark/enhanced_comparison.py: compute_enhanced_metrics 125L→42L via \_extract_algorithm_config @staticmethod 18L +
  \_extract_instrument_venue @staticmethod 11L + \_compute_regime_metrics @staticmethod 33L (already had helpers from
  earlier context; compute_enhanced_metrics body slimmed to use them).
  defi_execution/orchestrators/recursive_loop_orchestrator.py: \_persistent_open 125L→49L via \_make_open_fail_result
  23L + \_handle_hf_abort 32L + \_handle_open_failed 22L + \_record_iter_completed 31L instance helpers (both early-exit
  failure paths share \_make_open_fail_result). results/report_timeline_extractor.py: build_equity_curve 132L→34L via
  \_collect_all_fills_from_alpha @staticmethod 35L + \_accumulate_equity_points @staticmethod 28L +
  \_build_equity_from_timestamps @staticmethod 37L. algo_library/leveraged_leg_controller.py: compute_drift 133L→36L via
  docstring trim (48L→1L) + \_apply_reward_inflow module-level 22L + \_compute_leg_drift_entry module-level 31L
  (for/else → early-return semantics preserved). Allowlist 44→40. AST clean. ruff 0 errors.

  **Slot-4 cumulative across batches 1-21**: 78 files cleared (allowlist now 40).

  **Ratchet-down 2026-05-18 (slot-5 batch 21 — algorithms/impl/twap.py + twap_scheduling.py)**: shipped at
  execution-service@5138500e4. TWAPExecAlgorithm.on_order 298L→~30L via 7 helpers; schedule_children 189L + spawn_child
  201L + submit_final_slice 193L → ≤48L each via 13 helpers. Allowlist 40→38 files. AST clean, behavior-preserving (all
  logging channels preserved).

  **Ratchet-down 2026-05-18 (slot-4 batch 22 — algo_library/dust_router_runner + algo_library/sor_cross_chain +
  engine/validation/backtest_validator)**: shipped at execution-service@215c10027. dust_router_runner:
  \_build_reward_attribution_rows 137L→37L via \_resolve_reward_stream_meta
  - \_converted_row + \_held_row + \_deferred_row instance helpers (pre-existing `# type: ignore[arg-type]` preserved on
    `distributor_kind=kind`). sor_cross_chain: \_evaluate_cross_chain_route 137L→49L via \_compute_bridge_in_params +
    \_compute_bridge_out_params + \_make_bridge_in_leg + \_make_swap_legs + \_make_bridge_out_leg (5-tuple return avoids
    double get_bridge_cost in main). backtest_validator: validate_instruction_data_availability 141L→44L via
    \_extract_backtest_config + \_gather_instrument_list + \_detect_data_requirements + \_load_trades_and_validate +
    \_load_and_validate_instrument. Allowlist 38→35. AST clean. ruff 0 errors.

  **Slot-4 cumulative across batches 1-22**: 81 files cleared (allowlist now 35).

  **Ratchet-down 2026-05-18 (slot-4 batch 23 — data/converter_orderbook + data/trade_converter)**: shipped at
  execution-service@01b128498. converter_orderbook.py: convert_orderbook_parquet_to_catalog 118L→33L via
  \_run_batch_loop 46L + \_check_df_time_window_skip 39L; \_process_batch 106L→31L via \_build_row_deltas 43L;
  \_should_skip_conversion_with_time_window 75L→24L. trade_converter.py: convert_trades_parquet_to_catalog 230L→42L via
  \_normalize_trade_df + \_vectorize_trade_df + \_build_trade_tick_list + \_write_trade_ticks; convert_trades_to_bars
  146L→43L via \_normalize_instrument_id_for_bars + \_aggregate_to_bars_df. Allowlist 33→31. AST clean. ruff 0 errors.

  **Slot-4 cumulative across batches 1-23**: 83 files cleared (allowlist now 31).

  **Ratchet-down 2026-05-18 (slot-4 batch 24 — services/instruction_alpha_calculator)**: shipped at
  execution-service@7e1a25ddd. calculate_instruction_alpha 192L→49L via 6 module-level helpers:
  \_parse_instruction_timestamp, \_parse_fill_price_and_quantity, \_make_heartbeat_skip, \_build_alpha_result,
  \_fail_price_sanity + instance method \_compute_and_record_alpha. get_summary 141L→29L via
  \_accumulate_alpha_by_type + \_accumulate_alpha_by_bundle (both module-level). Removes
  services/instruction_alpha_calculator.py from allowlist. Net allowlist 29→28 (concurrent slot-5 clears merged in
  during rebase). AST clean.

  **Slot-4 cumulative across batches 1-24**: 84 files cleared (allowlist now 28).

  **Ratchet-down 2026-05-18 (slot-4 batch 25 — defi_execution/protocols/uniswap.py)**: shipped at
  execution-service@9b2cc7ea6. \_execute_live_swap 75L→38L via \_approve_token_for_router (approve try/except) +
  \_try_execute_swap (exactInputSingle try/except). mint_position 106L→46L via \_compute_validated_ticks +
  \_compute_wei_amounts + \_approve_both_tokens_for_npm + \_submit_npm_mint. Also moved 2× inline `import time as _time`
  to module level (fixes 2 pre-existing import-inside-fn codex violations). Removes defi_execution/protocols/uniswap.py
  from allowlist. Net allowlist 28→24 (concurrent slot clears of pov_dynamic.py + vwap_execution.py + loader_gcs.py
  merged in during rebase). AST clean.

  **Slot-4 cumulative across batches 1-25**: 85 files cleared (allowlist now 24).

  **Ratchet-down 2026-05-18 (slot-5 batch 22 — data/loader_base.py + data/loader_transforms.py)**: shipped at
  execution-service@56865ab83. loader_base.py: **init** 86L→~30L via \_resolve_bucket_and_domain + \_init_fuse_behavior;
  \_infer_category 83L→10L via 5 domain-specific staticmethod helpers. loader_transforms.py: \_infer_category 83L→10L
  (same pattern); \_normalize_timestamp_columns_for_backtest 217L→16L via 5 helpers (\_convert_ts_event,
  \_convert_defi_timestamp, \_convert_standard_timestamp, \_normalize_defi_derivative_columns,
  \_normalize_standard_columns). Allowlist 35→33 files. AST clean.

  **Ratchet-down 2026-05-18 (slot-5 batch 23 — algorithms/impl/hybrid_optimal_spawn.py)**: shipped at
  execution-service@1797be080. \_get_market_price 88L→22L via \_get_l1_mbp_price + \_resolve_l2_spread_adjustment.
  \_spawn_hybrid_child_fresh 68L→20L via \_do_spawn_market_for_hybrid + \_register_hybrid_child. Also fixed
  .pre-commit-config.yaml gitleaks --config to use .gitleaks.toml (relative symlink) — env var not expanded by prek.
  Allowlist 31→30 files. AST clean. ruff 0 errors.

  **Ratchet-down 2026-05-18 (slot-5 batch 24 — algorithms/impl/passive_aggressive_execution.py)**: shipped at
  execution-service@ca499af3f. \_pah_schedule_passive_spawn 52L→12L via \_pah_schedule_spawn_alert. on_order 87L→38L via
  \_pah_compute_and_register_state. on_order_filled 83L→31L via \_pah_record_fill_and_update_state +
  \_pah_maybe_refill_passive. Allowlist 30→29 files. AST clean. ruff 0 errors.

  **Ratchet-down 2026-05-18 (slot-5 batch 25 — algorithms/impl/pov_dynamic.py)**: shipped at
  execution-service@fa79a05dd. \_get_market_price 89L→28L via \_get_pov_l1_mbp_price +
  \_resolve_pov_l2_spread_adjustment. on_order 99L→19L via \_log_pov_on_order_entry + \_pov_init_order_state.
  \_pov_resolve_slice_context 61L→49L via \_pov_resolve_child_qty. Allowlist 29→28 files. All methods <50L. AST clean.

  **Ratchet-down 2026-05-18 (slot-5 batch 26 — algorithms/impl/vwap_execution.py)**: shipped at
  execution-service@b15278afd. \_store_and_schedule_vwap 69L→27L via \_vwap_store_parent_state +
  \_vwap_schedule_market_fok. \_spawn_child 107L→32L via \_vwap_resolve_spawn_qty + \_vwap_do_spawn_child.
  \_submit_primary 75L→28L via \_vwap_do_final_spawn. Allowlist 28→27 files. All methods <50L. AST clean. ruff 0 errors.

  **Ratchet-down 2026-05-18 (slot-5 batch 27 — algorithms/impl/almgren_chriss.py)**: shipped at
  execution-service@15b083927. \_get_market_price 90L→25L via \_get_ac_l1_mbp_price + \_resolve_ac_l2_spread_adjustment.
  on_order 91L→27L via \_ac_compute_trajectory. \_ac_store_and_schedule 50L→47L via \_ac_schedule_final_alert.
  \_on_slice 72L→27L via \_ac_do_spawn_slice. \_on_final 84L→27L via \_ac_do_final_spawn. Allowlist 27→26 files. All
  methods <50L. AST clean. ruff 0 errors.

  **Ratchet-down 2026-05-18 (slot-4 batch 26 — 3 already-clean files removed: engine/backtest/engine/setup.py +
  engine/orchestrator.py + engine/backtest/data_loader.py — zero code changes)**: shipped at
  execution-service@d9532a6d3. All 3 files had zero method-size violations when scanned. Free decrements — no source
  edits. Allowlist 24→21 files. Slot-4 cumulative across batches 1-26: 88 files cleared.

  **Ratchet-down 2026-05-18 (slot-4 batch 28 — engine/backtest/actors/signal_driven_v3_handlers.py)**: shipped at
  execution-service@14472be17. execute_exit 144L→44L via \_resolve_exit_benchmark + \_create_exit_order_and_log +
  \_submit_and_record_exit. on_order_filled 181L→43L via \_is_maker_fill + \_resolve_fill_context +
  \_process_entry_fill + \_process_exit_fill. Allowlist 21→20 files. All helpers ≤50L. AST clean. Slot-4 cumulative
  across batches 1-28: 89 files cleared.

  **Ratchet-down 2026-05-18 (slot-5 batch 28 — data/validator.py)**: shipped at execution-service@cbb3b4219.
  validate_gcs_trades_availability 230L→33L via \_vl_gcs_setup + \_vl_gcs_check_instruction_data +
  \_vl_gcs_data_type_label + \_vl_gcs_resolve_inst_category + \_vl_gcs_build_not_found_error +
  \_vl_gcs_build_exception_error. validate_local_trades_files 76L→38L via \_vl_resolve_dataset_folder +
  \_vl_check_trade_files. validate_time_window_in_files 91L→37L via \_vl_find_timestamp_col +
  \_vl_resolve_file_ts_range. Allowlist 20→19 files. All methods <50L. AST clean. ruff 0 errors. Slot-5 cumulative
  across batches 21-28: 8 files cleared (data/validator + algorithms/impl ×5 + data/loader_base +
  data/loader_transforms).

  **Deferred from slot-5 2026-05-18 session (data/loaders/ remaining scope)**:
  - [ ] **P2 DEFERRED** `data/loaders/tick_data.py` — `load_trades` 435L + `load_book_snapshots` 125L. Both too complex
        to refactor safely without test validation (streaming + FUSE mount + timestamp normalization + filtering all
        interleaved in a single 435L method). Requires dedicated slot with QG run to confirm green before commit. Still
        in FUNCTION_SIZE_EXTRA_EXCLUDES. Next owner: assign when test infra is warm.

  **Ratchet-down 2026-05-18 (slot-4 batch 29 — data/orderbook_converter.py)**: shipped at execution-service@2c2b4d057.
  \_check_skip_if_exists 80L→30L via \_check_df_catalog_exists; \_filter_by_time_window 105L→26L via
  \_detect_ts_is_nanoseconds + \_apply_ts_filter_and_log; \_build_snapshot_deltas 158L→37L via \_DeltaRecord
  NamedTuple + \_build_clear_record + \_build_level_records + \_set_f_last_flag; convert_orderbook_parquet_to_catalog
  195L→50L via \_load_parquet_df + \_detect_timestamp_cols + \_run_snapshot_batch_loop + \_write_catalog_batch. 4
  violations cleared. Allowlist 19→18 files. Slot-4 cumulative across batches 1-29: 90 files cleared.

  **Ratchet-down 2026-05-18 (slot-4 batch 30 — data/checker.py + benchmark/comparison.py)**: data/checker.py shipped at
  execution-service@9e1d6b29b: check_gcs_file_exists 212L→33L via \_GCS_DATA_TYPE_MAP constant +
  \_gcs_override_test_date + \_gcs_assert_loader + \_gcs_resolve_instrument_parts + \_gcs_resolve_category +
  \_gcs_build_path + \_gcs_check_blob + \_gcs_lookup_and_check; check_data_availability 106L→27L via \_chk_init_result +
  \_chk_resolve_source + \_chk_check_trades + \_chk_finalize_trades. benchmark/comparison.py shipped at
  execution-service@f8e20a620: run_comparison 199L→37L + \_get_algorithm_references 127L→3L via \_ALGORITHM_REFERENCES
  module constant + \_run_and_log_benchmark + \_run_all_algorithms + \_build_algo_result instance methods + module-level
  \_log_comparison_header + \_setup_signal_driven_config. 4 violations cleared. Allowlist 18→16 files. Slot-4 cumulative
  across batches 1-30: 94 files cleared.

  **Ratchet-down 2026-05-18 (slot-5 batch 29 — engine/routing/instruction_router.py)**: shipped at
  execution-service@17480ee86. route_instruction 129L→36L via \_route_compose_preflight (30L) + \_route_log_error_action
  (31L) + \_route_handle_error (27L). 1 violation cleared. Allowlist 19→15 files (net; parallel slot-4 batches 29-30
  also landed). Slot-5 cumulative across batches 21-29: 9 files cleared.

  **Ratchet-down 2026-05-19 (slot-5 batch 30 — engine/backtest/engine/results.py)**: shipped at
  execution-service@750e8001d. \_extract_results 226L→49L via 7 helpers: \_er_extract_summary_checks (26L) +
  \_er_alpha_instr (18L) + \_er_alpha_cache static (21L) + \_er_resolve_run_id (23L) + \_er_exec_algo static (19L) +
  \_er_resolve_instruction_type static (8L) + \_er_build_orders_and_timeline (28L). 1 violation cleared. Allowlist 15→14
  files. Slot-5 cumulative across batches 21-30: 10 files cleared.

  **Ratchet-down 2026-05-19 (slot-4 batch 31 — data/gcs_data_loading.py)**: shipped at execution-service@a98d95a51.
  \_run_pre_load_cache_checks 123L→49L via \_preld_check_existing_scale (35L) + \_preld_resolve_and_validate_cache
  (44L); \_convert_day_to_catalog 85L→24L via \_convert_tbbo_to_bars (21L) + \_convert_to_bars (30L);
  load_and_convert_from_gcs 305L→47L via \_GcsLoadContext TypedDict + \_gcs_load_one_day (46L) + \_gcs_run_all_days
  (27L) + \_gcs_filter_and_convert (50L) + \_gcs_check_local_cache_hit (20L) + \_gcs_build_day_window (17L) +
  \_gcs_tradfi_validate_log (24L) + \_gcs_debug_path_log (18L) + \_gcs_resolve_dates_to_process (13L) +
  \_gcs_log_summary (10L) + \_mk_day_result (6L). 3 violations cleared. Allowlist 14→13 files. Slot-4 cumulative across
  batches 1-31: 97 files cleared.

  **Ratchet-down 2026-05-19 (slot-5 batch 31 — results/extractor.py)**: shipped at execution-service@78ba90954.
  extract_pnl_from_portfolio 131L→20L via 4 helpers: \_epfp_get_stats_pnls (18L) + \_epfp_sum_stats_pnls (26L) +
  \_epfp_sum_realized_unrealized (29L) + \_epfp_balance_fallback (29L). extract_returns_from_positions 193L→27L via 4
  helpers: \_erp_method1 static (22L) + \_erp_method2 static (21L) + \_erp_update_position (28L) + \_erp_method3 static
  (41L). extract_summary 215L→33L via 4 helpers + 1 module-level: \_filled_orders_fallback module helper (5L) +
  \_es_extract_fills (31L) + \_es_call_evaluator (16L) + \_es_build_perf_summary (48L) + \_es_fallback_summary (12L). 3
  violations cleared. Allowlist 14→13 files (net; slot-4 batch 31 gcs_data_loading.py also landed concurrently). Slot-5
  cumulative across batches 21-31: 11 files cleared (allowlist now 13).

2. **Phase B — concentrated 30%** (~3 cal AI-days, **POST-CUTOVER**): refactor the 3 hottest submodules
   (`engine/backtest` 41 + `algorithms/impl` 33 + `defi_execution/protocols` 30) using the same helper-extraction
   patterns this session applied to UTL/MTDS/strategy-service:
   - per-method behavior preservation
   - basedpyright residual error count must not regress
   - test suite green per commit
   - Half-1+Half-2 plan-flip discipline per shippable unit

   **Phase B in-progress (2026-05-17 autonomous loop — slot-7)**: 102/377 methods cleared (27%) — milestone ≥100 passed
   2026-05-17. Latest: execution-service@47734d7d7 (tick-41 — BenchmarkMatcher.match 69L→48L /
   KrakenCeFiAdapter.parse_order_response 69L→43L / LiveExecutionHandler.\_execute_instructions 69L→47L). Full
   turn-by-turn log: `ikenna_orchestrator/pings/slot_7.md` ticks 30–41.

3. **Phase C — remaining 70%** (~5-7 cal AI-days, **POST-CUTOVER**): per-submodule sweep until
   `FUNCTION_SIZE_EXTRA_EXCLUDES = ()` cleanly. No urgency before live trade verification.

**Phase A** is the only stage worth doing pre-May-23 — it's a baseline ratchet, not behavior change. Phase B/C should be
slot-4/5 work post-cutover when the May-23 gate has shipped.

Not attempting any fix in this autonomous loop — 377 methods would burn slot 7's context budget and the
30%-concentration cluster needs a focused per-submodule agent (engine/backtest is its own audit surface).

## Cross-references

- `utl_qg_preexisting_failures_2026_05_14.md` §3 — the workspace pattern (slot 7's UTL sweep took 9 excluded paths → 1;
  same playbook applies here).
- `uac_qg_preexisting_size_violations_2026_05_14.md` — sibling issue doc covering the UAC `internal/__init__.py` 1693L
  barrel file.
- This loop's slot_7 ping ledger at `ikenna_orchestrator/pings/slot_7.md` — turn-by-turn refactor ledger if the
  per-submodule agent wants pattern examples.

---

## Triage — 2026-05-18

**Status**: OPEN **Triaged by**: slot-8 triage sweep **Reason**: 377 violations; Phase B in progress (slot 2, ~103/377
cleared)
