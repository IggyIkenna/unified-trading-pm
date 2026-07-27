---
doc_type: issue
title: MDPS liquidation-candle derivation has no UAC SchemaContract for instrument_type=FUTURE — 4 CeFi instruments fail
summary: >-
  Real-VM proof-sweep of `mdps_derivative_ticker_candle_schema_violation_2026_07_20.md` todo 3 found
  `CEFI:BINANCE-FUTURES:liquidations` (day=2026-05-22, auto-day) 485/489 instruments succeeded (3,693,275 candles) but 4
  FUTURE-instrument_type instruments (`ETH-USDT@LIN-20260925`, `BTC-USDT@LIN-20260925`, `BTCUSDT_260626`,
  `ETHUSDT_260626`) failed with "No SchemaContract registered for asset_group='cefi' instrument_type='FUTURE'
  data_type='liq_agg_1d' venue='BINANCE-FUTURES'". Distinct bug class from the original derivative_ticker
  missing-columns issue — this is a missing CONTRACT REGISTRATION entirely for one instrument_type dimension of the
  aggregated liquidation-candle data_type.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, market-data-processing-service]
scope: [engineer, admin]
tags: [data-correctness, mdps, candles, schema, liquidations, contract-registry, futures]
related:
  [
    /plans/active/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
priority: P1
source:
  [
    "mdps_derivative_ticker_candle_schema_violation_2026_07_20.md todo 3, dispatched task
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
resolved_by:
locked_by:
locked_since:
---

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

- This is a DIFFERENT defect class from `mdps_derivative_ticker_candle_schema_violation_2026_07_20.md` — that issue was
  missing DATAFRAME COLUMNS on an already-registered contract; this is a missing CONTRACT REGISTRATION entirely for one
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
- [ ] [SCRIPT] P2. Audit whether the SAME `instrument_type=FUTURE` gap exists for OTHER candle data_types beyond
      `liquidations` (the derivative_ticker fix + this proof-sweep only checked `book_snapshot_5`/`liquidations` on
      CEFI:BINANCE-FUTURES) — grep `CONTRACT_REGISTRY` for `instrument_type=FUTURE` entries across all registered
      data_types and compare against `instrument_type=PERPETUAL`'s coverage.
