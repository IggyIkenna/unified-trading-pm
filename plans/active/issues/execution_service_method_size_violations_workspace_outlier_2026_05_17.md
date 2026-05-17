---
title: "execution-service has 377 method-size violations (workspace outlier; ~13× the next-worst repo)"
created: 2026-05-17
author: slot-7-ikenna
source:
  - execution-service@f871ffad7 (post-cutover snapshot)
  - workspace-wide method-size sweep 2026-05-16 → 2026-05-17 (slot 7 autonomous loop)
severity: P2 (post-cutover hygiene; not blocking May-23)
status: phase-a-shipped (baseline ratchet live; phases B+C post-cutover)
locked_by: live-defi-rollout
locked_since: 2026-05-17
routing:
  primary_owner: operator triage (size = per-area sprint, not single-owner)
  composes_with: utl_qg_preexisting_failures_2026_05_14.md §3 (workspace pattern)
---

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

   **Slot-4 cumulative across batches 1+2+3+4+5+6+7**: 31 files cleared (187→141 baseline-equivalent; slot 4
   contribution: -31 files; allowlist now 141). **Slot-2 cumulative across batches 3+4+5**: 8 files cleared (187→168,
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

2. **Phase B — concentrated 30%** (~3 cal AI-days, **POST-CUTOVER**): refactor the 3 hottest submodules
   (`engine/backtest` 41 + `algorithms/impl` 33 + `defi_execution/protocols` 30) using the same helper-extraction
   patterns this session applied to UTL/MTDS/strategy-service:
   - per-method behavior preservation
   - basedpyright residual error count must not regress
   - test suite green per commit
   - Half-1+Half-2 plan-flip discipline per shippable unit
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
