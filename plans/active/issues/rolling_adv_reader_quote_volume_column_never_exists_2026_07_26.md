---
doc_type: issue
title:
  "features-service's RollingAdvReader returns NO_DATA for every real instrument — MDPS candles have never carried a
  quote_volume column"
summary: >-
  Discovered while executing cefi_satellite_ao_dispatch_batch1-001 (extending MDPS candle-building to on-chain-perp CeFi
  venues). features-service's RollingAdvReader.compute_rolling_adv() (shipped features-service@8608ea5d,
  aster_and_cefi_rolling_adv_feature_2026_07_21.md Phase 1, 19 passing unit tests) hard-codes reading a `quote_volume`
  column from MDPS processed_candles. Live-tested against REAL, freshly-backfilled, verified non-zero-volume HYPERLIQUID
  candle data: returns AdvStatus.NO_DATA, days_observed=0. Root cause: NO processed_candles/ file — checked both a
  brand-new HYPERLIQUID trades candle AND an established, long-running BITGET-FUTURES trades candle AND a
  BITFINEX-FUTURES derivative_ticker candle — has ever carried a `quote_volume` column. The actual schema is
  `volume`/`buy_volume`/`sell_volume` (base-asset-denominated), not `quote_volume` (USD-denominated). This is a
  pre-existing, universal defect that predates and is unrelated to the on-chain-perp venue extension — it would return
  NO_DATA for ANY venue/instrument, always, since the feature shipped.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [features-service, market-data-processing-service]
scope: [engineer]
tags: [features-service, mdps, adv, quote-volume, schema-mismatch, cross-repo, data-correctness]
related:
  [
    /plans/active/aster_and_cefi_rolling_adv_feature_2026_07_21.md,
    /plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.75
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Discovered 2026-07-26 while verifying cefi_satellite_ao_dispatch_batch1-001's ADV-reader Done-when criterion against
  real backfilled data (slot 6). Measured live, not inferred: a real `compute_rolling_adv()` call against real prod GCS
  data.
locked_by:
locked_since:
resolved_by:
depends_on: []
---

# RollingAdvReader: quote_volume column has never existed on any real MDPS candle

## What I found

1. Backfilled real HYPERLIQUID `trades` candles for `day=2026-07-19` (BTC/ETH), confirmed non-zero real data:
   `HYPERLIQUID:PERPETUAL:BTC-USD@LIN` `timeframe=1d` candle has `volume=28140.06352`, `open=64828.0`, `high=64959.0`,
   `low=64275.0`, `close=64718.0` — genuinely real, not empty/placeholder.
2. Ran
   `features_service.cross_instrument.app.calculators.adv.compute_rolling_adv(venue='HYPERLIQUID', instrument_id='HYPERLIQUID:PERPETUAL:BTC-USD@LIN', asset_group='cefi', as_of_date=date(2026,7,19), window_days=7, data_type='trades')`
   against this real data. Result: `RollingAdvReader: zero 7-day candles observed ... NO_DATA` / `status=no_data` /
   `days_observed=0` / `adv_usd=None` / `is_tradeable=False`.
3. Root cause: `adv.py`'s `_QUOTE_VOLUME_COL = "quote_volume"` — `_read_one_day_quote_volume` returns `None` whenever
   `"quote_volume" not in df.columns` (line ~279). Checked the ACTUAL column list of:
   - The new HYPERLIQUID `trades` `1d` candle (just backfilled): no `quote_volume`.
   - An established `BITGET-FUTURES` `trades` `1d` candle (`day=2026-05-03`, long-running tardis-sourced venue): no
     `quote_volume`.
   - An established `BITFINEX-FUTURES` `derivative_ticker` `1d` candle (`day=2026-05-03`, the reader's own DEFAULT
     `data_type`): no `quote_volume`.

   All three carry `volume` (base-asset-denominated) instead. **No candle file this session found, across 3 distinct
   venues and 2 distinct data_types, has ever had a `quote_volume` column.**

4. The Phase-1 unit tests (`tests/cross_instrument/unit/test_adv.py`, 19 passing) evidently mock a DataFrame that DOES
   include `quote_volume` — so the tests pass while the real integration has never worked. Classic
   tests-mock-a-schema-that-does-not-exist gap.

## Why it matters

- `features-service@8608ea5d`'s rolling-ADV feature (position-size caps, min-history-to-trade gate — the whole point of
  `aster_and_cefi_rolling_adv_feature_2026_07_21.md`) has been non-functional against real data since it shipped, for
  EVERY CeFi venue, not just the 4 on-chain-perp ones this session targeted. It will return
  `NO_DATA`/`is_tradeable=False` for every instrument, always, until this is fixed — silently defeating the intended
  volume-cap / illiquidity-gate strategy use case.
- This blocks `cefi_satellite_ao_dispatch_batch1-001`'s own "Done when" criterion #2 ("ADV reader returns
  non-`NO_DATA`") — not because that todo's own candle-backfill work is wrong (it verifiably produced real, correct
  `volume` data), but because the CONSUMER expects a column the PRODUCER never writes. This is a pre-existing cross-repo
  integration gap, not a regression introduced by the backfill work.

## Recommended decision

- [ ] [DATA] P1. **Reconcile the `quote_volume` vs `volume` naming between MDPS's candle writer and features-service's
      `RollingAdvReader`.** Two candidate fixes (pick one, don't guess — needs a design call): (a) rename/alias the
      column the ADV reader reads to `volume` if base-asset volume is an acceptable proxy for the USD-cap use case
      (simplest, but changes the semantic from "USD volume" to "base-asset volume" — may need a price multiply to get
      true USD notional), or (b) have MDPS's candle writer additionally emit a real `quote_volume` (= `volume × vwap` or
      `sum(price × qty)` at aggregation time) alongside `volume`. Repos: features-service (+
      market-data-processing-service if (b) is chosen). **Done when**: `compute_rolling_adv()` called against a real,
      already-backfilled candle (e.g. the HYPERLIQUID BTC 2026-07-19 candle from this session, or any established
      venue's) returns a non-`NO_DATA` `AdvStatus` with a real `adv_usd` value, and the existing 19 unit tests are
      updated/still pass against the corrected schema assumption.
