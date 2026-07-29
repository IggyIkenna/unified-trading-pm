---
doc_type: issue
title: MDPS liquidation-candle derivation has no UAC SchemaContract for instrument_type=FUTURE — 4 CeFi instruments fail
summary: >-
  Real-VM proof-sweep of `/plans/archive/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md` todo 3
  found `CEFI:BINANCE-FUTURES:liquidations` (day=2026-05-22, auto-day) 485/489 instruments succeeded (3,693,275 candles)
  but 4 FUTURE-instrument_type instruments (`ETH-USDT@LIN-20260925`, `BTC-USDT@LIN-20260925`, `BTCUSDT_260626`,
  `ETHUSDT_260626`) failed with "No SchemaContract registered for asset_group='cefi' instrument_type='FUTURE'
  data_type='liq_agg_1d' venue='BINANCE-FUTURES'". Distinct bug class from the original derivative_ticker
  missing-columns issue — this is a missing CONTRACT REGISTRATION entirely for one instrument_type dimension of the
  aggregated liquidation-candle data_type.
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, market-data-processing-service]
scope: [engineer, admin]
tags: [data-correctness, mdps, candles, schema, liquidations, contract-registry, futures]
related:
  [
    /plans/archive/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
  ]
created: 2026-07-27
last_updated: 2026-07-29
parent_epic: infrastructure_master
priority: P1
source:
  [
    "/plans/archive/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md todo 3, dispatched task
    mdps_derivative_ticker_candle_schema_violation-002, slot-10 2026-07-27, real VM
    mdps-backfill-cefi-pipelinecheck-20260727-113830-18d1f9",
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by: unified-api-contracts@bf1ecdb7, unified-api-contracts@f909e112
locked_by:
locked_since:
---

> **🟢 ARCHIVED 2026-07-29 — ACKED-INTO-CODE.** Both todos done: `liq_agg_{tf}` for `(cefi, future)` registered
> (`unified-api-contracts@bf1ecdb7`), and the follow-up audit found + fixed one more real gap (`book_snapshot_5`) plus
> shipped a generalized class-of-bug regression test (`unified-api-contracts@f909e112`). See
> `cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md` (also archived) for the sibling finding this
> same commit closed.

# MDPS liquidation candles — no SchemaContract for `instrument_type=FUTURE`

## What I found

Running
`/data-pipeline-check-mdps --asset-group CEFI --venue BINANCE-FUTURES --data-types liquidations --legs force --require-captured --auto-day`
on a real VM (`mdps-backfill-cefi-pipelinecheck-20260727-113830-18d1f9`, day slid to 2026-05-22 via `--auto-day`):
**485/489 instruments succeeded** (3,693,275 candles, exit_code=1 only because of the 4 failures below — the 485 passing
instruments prove the `liquidations` candle path itself is healthy, matching the already-fixed `mdps@d4052e20b` seam).
The 4 failures, all on `instrument_type=FUTURE`:

```
[liquidations] raw_tick_data/.../instrument_type=future/data_type=liquidations/BINANCE-FUTURES:FUTURE:ETH-USDT@LIN-20260925.parquet:
  No SchemaContract registered for asset_group='cefi' instrument_type='FUTURE' data_type='liq_agg_1d' venue='BINANCE-FUTURES'.
  Add a contract to unified_api_contracts.internal.schemas.contracts.CONTRACT_REGISTRY (and VENUE_CONTRACT_OVERRIDES
  if the schema is venue-specific) before rerunning the read/migration pipeline.
```

Same error for `BTC-USDT@LIN-20260925`, `BTCUSDT_260626`, `ETHUSDT_260626` — all 4 are dated/expiring futures contracts
(`@LIN-YYYYMMDD` / `_YYMMDD` naming), suggesting the registry has a contract for `instrument_type=PERPETUAL`
liquidations but never registered the equivalent for `instrument_type=FUTURE`.

## Why it matters

- This is a DIFFERENT defect class from
  `/plans/archive/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md` — that issue was missing
  DATAFRAME COLUMNS on an already-registered contract; this is a missing CONTRACT REGISTRATION entirely for one
  instrument_type dimension. The proof-sweep's job (confirm the derivative_ticker fix's seam generalizes) is satisfied
  for `liquidations` — 485/489 clean — but this surfaces a second, narrower gap the same sweep exists to catch.
- Blocks candle backfill for CeFi dated-futures liquidations specifically (perpetuals are unaffected — 485 passed).
- The error message names the exact fix location (`CONTRACT_REGISTRY` / `VENUE_CONTRACT_OVERRIDES`), so this is a
  scoped, low-risk registration addition, not a design question.

## Recommended decision

- [x] ✅ [SCRIPT] P1. **unified-api-contracts** — register a `liq_agg_1d` (and the other liquidation-candle timeframes,
      mirroring however `PERPETUAL` is currently registered) `SchemaContract` for
      `asset_group=cefi     instrument_type=FUTURE venue=BINANCE-FUTURES` in
      `unified_api_contracts.internal.schemas.contracts` (`CONTRACT_REGISTRY` + `VENUE_CONTRACT_OVERRIDES` if
      venue-specific). Add a regression test asserting the contract resolves for a `FUTURE`-instrument_type liquidation
      candle. Re-run the same scoped `/data-pipeline-check-mdps` cell to confirm all 489/489 instruments pass. —
      `unified-api-contracts@bf1ecdb7`: registered `cefi/future` `liq_agg_{tf}` (base `CONTRACT_REGISTRY`, not
      venue-specific — matches `PERPETUAL`'s unscoped registration; `BINANCE-FUTURES` needs no
      `VENUE_CONTRACT_OVERRIDES` entry) across all `MDPS_TIMEFRAMES_CEFI`; added `test_cefi_future_liq_aggregates`
      (parametrised over every CeFi timeframe) asserting `lookup_contract` resolves — full `quality-gates.sh` green.
      Real-VM `/data-pipeline-check-mdps` 489/489 re-confirmation is a follow-on VM run, not performed in this code-fix
      session.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-29 — unified-api-contracts@f909e112.** Audited `CONTRACT_REGISTRY` for
      `instrument_type=FUTURE` vs `PERPETUAL` coverage across CEFI: `perpetual` registers trades/book5/deriv/liq;
      pre-fix `future` registered only trades + liq_agg (this doc's own fix) — **book5 was the real, live gap**. Live
      GCS sampling (not assumed from the registry alone) — `market-data-tick-cefi-prd-central-element-323112`,
      `instrument_type=future/data_type=book_snapshot_5`, DERIBIT + OKX-FUTURES, 4 sample days
      (2026-06-15/07-01/07-10/07-19) — confirmed real, substantial, ongoing capture (33-104 shards/day per venue/day),
      i.e. the exact "No SchemaContract registered ... instrument_type='FUTURE' data_type='book5_ohlcv_...'" crash this
      doc's todo 1 fixed for `liq_agg_1d` was one VM run away from recurring for book5. `derivative_ticker` checked and
      confirmed genuinely absent (0 real objects, same 4-day/2-venue sample) — not a gap, so not added. Registered
      `book5_ohlcv_{tf}` for `(cefi, future)`, mirroring `perpetual`; new regression test
      `test_cefi_future_book5_candles` plus a generalized class-of-bug sweep
      `test_cefi_every_capturable_instrument_type_has_candle_contract` (cross-checks every CEFI leaf instrument_type's
      raw-tick-capturable data_types against `CONTRACT_REGISTRY`) so this audit doesn't need re-running by hand next
      time. Same commit also closes `cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md` todo 3.
      `quality-gates.sh --no-fix` green (398s), shipped via `quickmerge --agent`.
