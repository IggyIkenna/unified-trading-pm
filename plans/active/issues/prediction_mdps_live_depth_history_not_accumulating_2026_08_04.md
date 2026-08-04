---
doc_type: issue
title: >-
  Prediction live depth-history is NOT durably accumulating anywhere — raw book_snapshot_5 flushes still overwrite
  per-instrument, and the processed candle/book store has ZERO objects for any live-mode day sampled
summary: >-
  Executing `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 2 ("Verify END-TO-END MDPS prediction
  depth-history retention") produced a FAIL verdict, worse than the 2026-06-24 concern that spawned the todo. Two
  independent, compounding gaps, both live-verified via bounded (non-corpus-wide) reads: (1) the raw live flush path
  (`live_tick_blob_path()`, `market_tick_data_service/live/websocket_runner.py:95-145`) is keyed by day+instrument ONLY
  (`{instrument_id}.parquet`, no window/period key) — every window flush overwrites the prior one; a sampled KALSHI
  `book_snapshot_5` file held only 11 rows spanning ~16 minutes, consistent with rolling-overwrite. This contradicts a
  stale "RESOLVED... event-time-keyed" note in `prediction_live_clob_depth_capture_2026_07_24.md` (that fix was reverted
  2026-06-26 by `market-tick-data-service@3043f2dc`, which restored `LiveWebsocketTickSink` as the default sink to fix a
  worse InMemoryTransport data-loss bug — the revert was never reflected back into that earlier claim). (2) The
  processed prediction candle/book store
  (`market-data-tick-pred-prd-central-element-323112/processed_candles/by_date/day={D}/`) has ZERO objects for
  `pipeline_mode=live_*` on every one of 4 sampled days confirmed to have live raw data present (2026-06-23, 06-24,
  06-26, 06-28) — only `pipeline_mode=batch_kalshi` (daily 6am UTC batch cron) output exists recently. A structural
  cause explains half of this: MDPS's `CandleAdapterRegistry` has no `(PREDICTION, "book_snapshot_5")` adapter (only
  `(PREDICTION, "trades")` is registered) despite the global `NEEDS_CANDLE_PROCESSING["book_snapshot_5"] = True` — this
  silently (WARNING-log-only) skips book_snapshot_5 processing forever. It does NOT explain why `trades` (which DOES
  have a registered adapter, `PredictionTradesAdapter`) is also absent from live-mode processed output on every sampled
  day — that needs separate root-causing (most likely the MDPS live-mode continuous scan process was never
  deployed/launched for prediction against `pipeline_mode=live_*` prefixes, unconfirmed).
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [prediction, mdps, depth-history, live-data, book_snapshot_5, candle-adapter, data-correctness, big-finding]
related:
  [
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-04"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
source: >-
  Discovered live while executing `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 2 (a bounded, read-only
  depth-history-retention verification), dispatched via AO to slot 5 (2026-08-04, data_engineering). Verdict + full
  evidence recorded in `prediction_live_clob_depth_capture_2026_07_24.md`'s Progress Log — this doc is the
  actionable-fix companion per the CLAUDE.md findings-closure HARD RULE (verification tasks must not silently absorb
  remediation scope).
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
    market-data-processing-service/market_data_processing_service/app/adapters/prediction/trades_adapter.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
  ]
---

# Prediction live depth-history is not durably accumulating anywhere (2026-08-04)

## What I found (all read-only, no data mutation)

Full narrative + live GCS evidence is in `prediction_live_clob_depth_capture_2026_07_24.md`'s 2026-08-04 Progress Log
entry (the todo this verification executed). Summary of the two compounding gaps:

1. **Raw flush window still overwrites per instrument.** `live_tick_blob_path()`
   (`market_tick_data_service/live/websocket_runner.py:95-145`) builds
   `raw_tick_data/by_date/day={D}/pipeline_mode={live_mode}/.../data_type={dt}/{instrument_id}.parquet` — no
   window/period key in the path. `LiveWebsocketTickSink` (the currently-active default sink, restored 2026-06-26 by
   `market-tick-data-service@3043f2dc`) writes with no read-existing-concat, so every window flush for the same
   instrument on the same day overwrites the prior file. Live-sampled: a KALSHI `book_snapshot_5` file
   (`FEDHIKE-26DEC31`, day=2026-06-28 partition) held 11 rows spanning only ~16 minutes, single mtime matching the last
   row's timestamp.

2. **The processed prediction candle/book store has zero live-mode objects, any sampled day.** Bounded
   `gcloud storage ls` on `market-data-tick-pred-prd-central-element-323112/processed_candles/by_date/day={D}/` for
   2026-06-23, 06-24, 06-26, 06-28 (all confirmed via `raw_tick_data/` to have live raw data for both venues, both
   `trades` and `book_snapshot_5`) returned zero `pipeline_mode=live_*` objects on every day. Only
   `pipeline_mode=batch_kalshi` output exists recently (from the daily batch cron).

3. **Structural cause for the `book_snapshot_5` half of #2**: no `CandleAdapterRegistry` entry for
   `(MarketAssetGroup.PREDICTION, "book_snapshot_5")` exists in `market-data-processing-service` (only
   `(PREDICTION, "trades")` → `PredictionTradesAdapter`), while `NEEDS_CANDLE_PROCESSING["book_snapshot_5"] = True`
   globally (`unified-api-contracts`). This routes prediction `book_snapshot_5` into `orchestration_service.py:653`'s
   `"⚠️ No adapter for %s/%s"` WARNING branch on every scan cycle — silent, permanent skip. This does NOT explain why
   `trades` (adapter exists) is also absent from live-mode processed output — unconfirmed whether the MDPS live-mode
   continuous process even runs for prediction.

## Why this matters

The doc that owns this surface states the design intent explicitly: "durable history is MDPS's processed output, NOT the
rolling raw bucket" (per Live=Batch / `/codex/02-data/live-data-persistence-and-event-log.md`). Today, neither store
durably holds prediction depth history: raw overwrites every flush, and the processed store has none at all for live
mode. Any downstream consumer expecting multi-hour prediction book/depth history (the arb detector, microstructure
features which key off `book_snapshot_5` per `FEATURE_GROUP_DATA_TYPES`) is silently working with at most a ~15-30
minute rolling window, not real history — and for anything expecting _processed, candle-shaped_ book data, there is
currently nothing at all.

## What I did NOT do (and why)

- **Did not fix the adapter gap or the overwrite path.** The dispatching todo was scoped as read-only verification only
  ("no data mutation") — this issue doc is the follow-up per the findings-closure rule.
- **Did not root-cause why `trades` (adapter-complete) is also absent from live processed output.** That requires
  checking whether an MDPS live-mode worker (`--mode live --operation timer-candles`) is actually deployed/running for
  the prediction cluster at all — out of scope for a bounded verification pass; todo 1 below owns it.

## Todos

- [ ] [DATA] P1. **Root-cause why `pipeline_mode=live_*` processed-candle output is completely absent for PREDICTION
      `trades` (adapter exists) on every sampled day** (2026-06-23/24/26/28). Check whether an MDPS live-mode continuous
      worker (`--mode live --operation timer-candles`,
      `market_data_processing_service/cli/handlers/live_mode_handler.py`) is deployed/launched for the prediction
      cluster at all (`deployment-service/configs/clusters/prediction.yaml` only shows a batch cron, no explicit
      live-mode launch config found in this verification pass — confirm via deployment-service VM/Cloud Run inventory,
      not a fresh corpus walk). Repo: deployment-service (+ market-data-processing-service read-only). Done when: a
      definitive root cause is recorded (worker never deployed / deployed but erroring / deployed but scanning the wrong
      prefix) with evidence, in this doc's Progress Log.
- [ ] [BACKEND] P1. **Register a `CandleAdapterRegistry` entry for `(MarketAssetGroup.PREDICTION, "book_snapshot_5")`,
      or explicitly declare it a deliberate bypass.** Either (a) add a `PredictionBookSnapshotAdapter` (mirrors
      `CefiBookSnapshotAdapter`/`DefiBookSnapshotAdapter`) so book_snapshot_5 actually produces candle output once live
      processing runs, or (b) if book-candle output for prediction is genuinely not needed (a real product decision, not
      a default), flip `NEEDS_CANDLE_PROCESSING["book_snapshot_5"]` to a prediction-scoped False (the map is currently
      shared/global with CeFi — would need a per-asset-group override, check `needs_candle_processing()`'s signature) so
      the silent WARNING-only skip becomes an honest bypass log instead. Repo: market-data-processing-service (+
      unified-api-contracts if (b)). Done when: either a new adapter ships with tests + QG green, or an explicit bypass
      declaration ships with a one-line justification comment, and the "⚠️ No adapter for PREDICTION/book_snapshot_5"
      warning no longer fires on the next live scan.
- [ ] [DATA] P2. **Re-verify multi-hour processed accumulation once todos 1-2 land.** Re-run the same bounded
      GCS-timespan check this issue's parent verification did (`processed_candles/by_date/day={D}/pipeline_mode=live_*`
      for a fresh day post-fix) and confirm PASS. Repo: market-data-processing-service (read-only). Done when: a dated
      PASS verdict with the measured processed-store time span is recorded in
      `prediction_live_clob_depth_capture_2026_07_24.md`'s Progress Log, superseding the 2026-08-04 FAIL entry.

## Progress Log

- **2026-08-04 (slot-5, data_engineering)**: filed immediately after the FAIL verdict on the parent verification todo,
  per the CLAUDE.md findings-triage "big finding" rule (data-correctness, silent, production-live).
