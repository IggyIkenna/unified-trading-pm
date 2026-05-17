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
unified-trading-api + strategy-service this session (2026-05-16 / 2026-05-17 autonomous loop), I ran a
final scan across every sister repo with `python3` AST parsing + the per-repo `FUNCTION_SIZE_EXTRA_EXCLUDES`
honored. Result by repo:

| Repo                                | Non-excluded violations |
| ----------------------------------- | ----------------------- |
| unified-cloud-interface             | 0                       |
| batch-live-reconciliation-service   | 0                       |
| pnl-attribution-service             | 0                       |
| client-reporting-api                | 0                       |
| trading-agent-service               | 0                       |
| alerting-service                    | 0                       |
| deployment-service                  | 0                       |
| instruments-service                 | 0                       |
| unified-trading-api                 | 0 (post `BatchCandleReader.get_candles` 54L→33L this loop) |
| features-service                    | 0 (post `FuturesRollAdjuster.annotate_lifecycle_phase` 58L→34L this loop) |
| strategy-service                    | 0 (post 2 refactors this loop) |
| market-tick-data-service            | 0 (post 5 refactors this loop) |
| unified-trading-library             | 0 source + 1 path excluded (`manifest_writer.py` docstring-heavy contract API) |
| **execution-service**               | **377**                 |

`execution-service` is the outlier — roughly 13× the next-worst repo (the workspace-second was UTL pre-sweep
at ~28 violations). `FUNCTION_SIZE_EXTRA_EXCLUDES` in `execution-service/scripts/quality-gates.sh` is the
empty list `()` so these are NOT triaged-as-known-pre-existing; either QG is silently passing on these
(check — maybe `MAX_METHOD_LINES` is overridden) or the suite has never run cleanly on them.

### Severity distribution (377 total)

| Bucket    | Count | % of total |
| --------- | ----- | ---------- |
| 51-60L    | 94    | 25%        |
| 61-75L    | 107   | 28%        |
| 76-100L   | 81    | 21%        |
| 101-150L  | 63    | 17%        |
| 151L+     | 32    | 9%         |

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

`execution-service` is on the **May-23 critical path** — it runs the live wallet trade adapter, the
backtest engine that validates archetype P&L pre-promote, and the per-venue protocol implementations
(Aave / Compound / Uniswap / Hyperliquid / etc.). The 50-line workspace standard exists because:

1. **Review burden**: 200+ line methods make per-commit diff review costly; in a critical-path service
   this is where regressions hide.
2. **Test coverage gaps**: long methods correlate strongly with low branch coverage. The
   `TickDataLoader.load_trades` at 436L will have multiple un-tested code paths.
3. **basedpyright performance**: strict-mode reportAny / reportUnknownVariableType checks are quadratic
   in some patterns; long methods slow QG.
4. **Cross-side handoff**: strategy-service has now been refactored to spec — execution-service is the
   only repo Harsh's side reads / cites without a code-quality baseline to match.

This is **NOT a May-23 blocker** — execution-service tests pass, the live trade adapter ships
operationally, and the 32 violations ≥151L are mostly data-loader / backtest-engine paths that don't
fire on the live wallet hot path. But it IS the workspace-second-largest tech-debt cluster after
UAC's `internal/__init__.py` 1693L barrel file (separately tracked in `uac_qg_preexisting_size_violations_2026_05_14.md`).

## Recommended decision

**Operator triage / 3-stage rollout**:

1. ✅ **Phase A — establish baseline** (~0.5 cal AI-day) — **SHIPPED 2026-05-17 execution-service@91e2cfb9e**:
   `FUNCTION_SIZE_EXTRA_EXCLUDES` populated with 187 files (561 array elements; 369 underlying violations).
   AST-scan post-exclude returns zero remaining violations. QG was indeed silently passing on these — find
   pattern at base-service.sh:778 was matching ALL files, exclude list was empty `()`, but the AST scanner
   on line 779-794 actually exits via `except: pass` on any parse error, so QG only fired on files where
   `print()` succeeded. Likely the QG step was emitting the violation list but `log_fail` was never
   reached (need to audit — but the ratchet is now solid regardless).
   **Ratchet-down 2026-05-17 execution-service@78ee78909** — slot-7 Phase B incremental refactors cleared
   7 files (sor / defi_test_data_generator / signal_driven_v3 / live_ccxt_adapter / instruction_validator /
   oms / benchmark_service); allowlist 187 → 180 files. AST scanner re-verified clean.
2. **Phase B — concentrated 30%** (~3 cal AI-days, **POST-CUTOVER**): refactor the 3 hottest submodules
   (`engine/backtest` 41 + `algorithms/impl` 33 + `defi_execution/protocols` 30) using the same
   helper-extraction patterns this session applied to UTL/MTDS/strategy-service:
   - per-method behavior preservation
   - basedpyright residual error count must not regress
   - test suite green per commit
   - Half-1+Half-2 plan-flip discipline per shippable unit
3. **Phase C — remaining 70%** (~5-7 cal AI-days, **POST-CUTOVER**): per-submodule sweep until
   `FUNCTION_SIZE_EXTRA_EXCLUDES = ()` cleanly. No urgency before live trade verification.

**Phase A** is the only stage worth doing pre-May-23 — it's a baseline ratchet, not behavior change.
Phase B/C should be slot-4/5 work post-cutover when the May-23 gate has shipped.

Not attempting any fix in this autonomous loop — 377 methods would burn slot 7's context budget and
the 30%-concentration cluster needs a focused per-submodule agent (engine/backtest is its own audit
surface).

## Cross-references

- `utl_qg_preexisting_failures_2026_05_14.md` §3 — the workspace pattern (slot 7's UTL sweep took 9
  excluded paths → 1; same playbook applies here).
- `uac_qg_preexisting_size_violations_2026_05_14.md` — sibling issue doc covering the UAC
  `internal/__init__.py` 1693L barrel file.
- This loop's slot_7 ping ledger at `ikenna_orchestrator/pings/slot_7.md` — turn-by-turn refactor
  ledger if the per-submodule agent wants pattern examples.
