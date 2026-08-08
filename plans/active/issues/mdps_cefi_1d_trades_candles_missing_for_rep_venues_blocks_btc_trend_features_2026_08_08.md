---
doc_type: issue
title:
  MDPS stopped producing `data_type=trades` (OHLC) daily candles for the CEFI perp venues `feature_perp_representative`
  picks — blocks the BTC-trend feature recompute (P2.11.16) from ever landing non-null data
summary: >-
  While executing `citadel_satellite_ao_dispatch_batch1_2026_08_08.md` todo P2.11.16 (features-service: recompute the
  delta_one `returns` feature group at `--timeframe 24h` for CEFI so `btc_trailing_return_{1,3,6,12}m` +
  `btc_realized_vol` land non-null), a dry-run VM
  (`features-delta-one-cefi-20260808-171347`, `python -m features_service --feature-family delta_one --operation
  compute --mode batch --start-date 2020-01-01 --end-date 2026-08-08 --asset-group CEFI --feature-group returns
  --timeframe 24h --dry-run`) logged `perp_collapse: retained 2/130` (the returns group narrows CEFI to one
  volume-chosen representative perp per base — cheap, as expected) then `No data found for
  DERIBIT:PERPETUAL:BTC-USD@INV in date range` / `No candles for DERIBIT:PERPETUAL:BTC-USD@INV at 24h — skipping` for
  the ENTIRE queried range (2019-09-03 buffered start through 2026-08-08), not just a recent gap.

  Direct GCS inspection of `gs://market-data-tick-cefi-prd-central-element-323112/processed_candles/by_date/` confirms
  the root cause is upstream, not a features-service bug: `pipeline_mode=batch_tardis/timeframe=1d/data_type=trades`
  DID carry `venue=DERIBIT` (+ BINANCE-FUTURES/BYBIT/OKX-FUTURES/KRAKEN-FUTURES/BITFINEX) candles historically
  (confirmed present 2023-01-01, 2024-06-01), narrowed to `venue=ASTER` only by 2026-05-12/14/15, and DISAPPEARED
  ENTIRELY by 2026-08-03 (`timeframe=1d` dir doesn't exist under `batch_tardis` that day at all — only
  15s/15m/1m/5m/1h/4h are still produced; `1h`'s `data_type=` set that day is `book_snapshot_5`/`derivative_ticker`
  only, no `trades`). By contrast, `pipeline_mode=batch_hyperliquid/timeframe=1d/data_type=trades/venue=HYPERLIQUID`
  DOES have current 24h trades candles for `HYPERLIQUID:PERPETUAL:BTC-USD@LIN` as of 2026-08-01 — a working
  BTC-perp trades/1d source exists in the corpus today, just not on the venue `feature_perp_representative` currently
  resolves to for BTC.

  Net effect: `btc_trailing_return_{1,3,6,12}m` + `btc_realized_vol` (features-service@653cf158, spec-shipped, GREEN
  QG) can NEVER be populated for BTC via a straight recompute while (a) the representative-venue selector keeps
  resolving BTC to DERIBIT and (b) DERIBIT/BINANCE/etc. no longer emit `data_type=trades` daily candles at all — this
  is the CRITICAL-PATH gate for the `TSMOM_BTC_CTA` non-null paper run (source doc
  `citadel_paper_batch_live_reconciliation_2026_06_19.md` P2.11.16/P2.11.14). Did not launch the full (non-dry-run)
  backfill VM — it would burn real SPOT compute producing an all-null corpus, not a genuine fix. Deleted the dry-run
  validation VM (`features-delta-one-cefi-20260808-171347`) after capturing this evidence; no other cloud resources
  touched.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service, unified-api-contracts, features-service]
scope: [engineer]
tags:
  [data-correctness, mdps, tardis, candle-derivation, perp-representative, btc-trend, tsmom-btc-cta, honest-absence]
related:
  [
    /plans/active/citadel_satellite_ao_dispatch_batch1_2026_08_08.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /codex/02-data/pipeline-mode-partition.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
author: ikennaigboaka [slot-33]
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.72
assigned_role: data_engineering
drift_direction: correct-code
---

# MDPS CEFI 1d/trades candles missing for `feature_perp_representative`-chosen venues

## What I found

`market-data-processing-service`'s `pipeline_mode=batch_tardis` derivation of `timeframe=1d`, `data_type=trades`
candles for CEFI perpetuals has regressed to the point of non-existence for every major venue
(DERIBIT/BINANCE-FUTURES/BYBIT/OKX/KRAKEN-FUTURES/BITFINEX-FUTURES all had it in 2023/2024; only `ASTER` still had it
by mid-May 2026; NOTHING has it by August 2026 — the `timeframe=1d` partition is absent from `batch_tardis` entirely
on recent sampled days). `unified-api-contracts`'s `feature_perp_representative(base="BTC", "cefi", venue_volumes)`
still resolves BTC to `DERIBIT` — a venue with zero recent 1d/trades coverage — so `features-service`'s
`returns` calculator's `_calculate_btc_trend_features` can never receive a `close` series to compute from. A
DIFFERENT venue, `HYPERLIQUID` (source `pipeline_mode=batch_hyperliquid`), DOES have current `1d`/`trades` candles
for `HYPERLIQUID:PERPETUAL:BTC-USD@LIN` as of 2026-08-01, so working data exists in the corpus but isn't the one the
representative selector points at.

## Why it matters

This is the CRITICAL-PATH gate cited in `citadel_paper_batch_live_reconciliation_2026_06_19.md` P2.11.16 for a
non-null `TSMOM_BTC_CTA` paper run (P2.11.14, already shipped and waiting on this). No amount of re-running the
features-service backfill fixes it — the upstream candle source for the resolved venue doesn't exist. Per
`codex/02-data/data-pipeline-correctness-hard-rule.md`, this is a RED data-correctness finding on the CEFI candle
pipeline that should freeze/inform any other work depending on daily-cadence CEFI candles for the affected venues,
not just this one feature pair.

## Recommended decision

Two independent fixes, not mutually exclusive — do the diagnostic first, it determines whether (b) is even the right
long-term answer or whether HYPERLIQUID-only is the intended sourcing going forward:

- [ ] [DIAG] P1. **Diagnose why `market-data-processing-service`'s `batch_tardis` 1d/trades candle derivation for CEFI
      perpetuals (DERIBIT/BINANCE-FUTURES/BYBIT/OKX-FUTURES/KRAKEN-FUTURES/BITFINEX-FUTURES) stopped producing output**
      — check the MDPS derivation job's own logs/manifest around the 2026-05-15 to 2026-05-20 transition (last
      confirmed `venue=ASTER`-only day sampled: 2026-05-15; first confirmed empty day: 2026-05-16) for a config
      change, upstream Tardis feed change, or a silent job failure. Repo: market-data-processing-service. Done when: a
      root cause is identified (deliberate sourcing migration vs. genuine regression) and written into this doc's
      Progress Log with the exact commit/config change (or dated evidence of an unexplained silent failure) found.
- [ ] [DATA] P1. **Either restore `data_type=trades` 1d candle derivation for the affected CEFI venues in
      market-data-processing-service, OR (if DIAG above finds the migration to `book_snapshot_5`/`derivative_ticker`
      was deliberate) update `features-service`'s delta_one `returns` calculator to derive `close` from
      `book_snapshot_5`/`derivative_ticker` mid/mark price instead of requiring `data_type=trades`** — whichever the
      diagnosis indicates is the intended long-term source. Repo: market-data-processing-service (or features-service
      if the fix is calculator-side). Done when: a 24h/1d `close` series is derivable end-to-end for at least
      DERIBIT:PERPETUAL:BTC-USD@INV (or the venue `feature_perp_representative` resolves to post-fix) for the current
      paper-trading window, verified via a manifest-row check (not job exit code alone). Blocked on the DIAG todo
      above (needs its root-cause finding to pick the right fix).
- [ ] [DATA] P2. **Audit `feature_perp_representative`'s BTC (and other-base) venue selection against ACTUAL candle
      availability, not just historical volume** — `HYPERLIQUID:PERPETUAL:BTC-USD@LIN` has current 1d/trades data
      today; DERIBIT (the currently-resolved rep venue) does not. Either the selector needs a
      data-availability filter alongside its volume ranking, or this specific base needs a manual override, so the
      "representative" venue chosen for a feature computation is one that can actually produce output. Repo:
      unified-api-contracts. Done when: `feature_perp_representative("BTC", "cefi", ...)` resolves to a venue with
      verified current 1d/trades coverage, with a regression test pinning the expectation. Depends on the DIAG +
      first DATA todo above (don't repoint until you know whether DERIBIT's gap is temporary or permanent).
- [ ] [DATA] P2. **Once the above land, re-run the P2.11.16 features-service delta_one `returns` recompute** (
      `FEATURE_GROUP=returns TIMEFRAME=24h python -m features_service --feature-family delta_one --operation compute
      --mode batch --asset-group CEFI --start-date 2020-01-01 --end-date <today> --feature-group returns` via
      `deployment-service/scripts/vm/launch-features-vm.sh`), verify via a manifest-row check that
      `btc_trailing_return_{1,3,6,12}m` + `btc_realized_vol` are non-null for the current paper-trading window, and
      flip `citadel_satellite_ao_dispatch_batch1_2026_08_08.md`'s P2.11.16 checkbox. Repo: features-service.
      Depends on all three todos above.

## Progress Log

- **slot-33 2026-08-08**: Discovered while executing `citadel_satellite_ao_dispatch_batch1_2026_08_08.md` P2.11.16.
  Dry-run VM `features-delta-one-cefi-20260808-171347` launched + deleted after capturing evidence (no full/write
  backfill run, no data mutated). Left P2.11.16's checkbox UNCHECKED in the source plan (the recompute genuinely
  cannot succeed yet) with a note pointing here.
