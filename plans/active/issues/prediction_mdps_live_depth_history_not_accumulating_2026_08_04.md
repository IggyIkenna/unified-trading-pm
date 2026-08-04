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

- [x] ✅ [DATA] P1. **Root-cause why `pipeline_mode=live_*` processed-candle output is completely absent for PREDICTION
      `trades` (adapter exists) on every sampled day** (2026-06-23/24/26/28). Check whether an MDPS live-mode continuous
      worker (`--mode live --operation timer-candles`,
      `market_data_processing_service/cli/handlers/live_mode_handler.py`) is deployed/launched for the prediction
      cluster at all (`deployment-service/configs/clusters/prediction.yaml` only shows a batch cron, no explicit
      live-mode launch config found in this verification pass — confirm via deployment-service VM/Cloud Run inventory,
      not a fresh corpus walk). Repo: deployment-service (+ market-data-processing-service read-only). Done when: a
      definitive root cause is recorded (worker never deployed / deployed but erroring / deployed but scanning the wrong
      prefix) with evidence, in this doc's Progress Log. — **VERDICT: worker never deployed, fleet-wide (not
      prediction-specific)** — full evidence + 2 new follow-up todos in the 2026-08-04 Progress Log entry below.
- [x] ✅ [BACKEND] P2. **Fix the MDPS `--mode live --operation timer-candles` CLI dispatch — currently crashes for EVERY
      asset_group if invoked, confirmed live.** `market_data_processing_service/cli/parser.py:71-74`
      (`_mode_dispatch_handler`) does `live_handler_cls()` (zero args) then `handler.run(args)` (passes an
      `argparse.Namespace`), but the real `LiveModeHandler.__init__(self, config: MarketDataProcessingServiceConfig)`
      requires `config`, and `.run()`'s real signature is `(interval: int, categories, venues, timeframes)`, not
      `(args)`. Confirmed via direct execution (`uv run python3 -c "LiveModeHandler()"` →
      `TypeError: LiveModeHandler.__init__() missing 1 required positional argument: 'config'`). Masked from CI because
      `tests/unit/test_cli_parser_coverage.py` fully mocks `LiveModeHandler`, and every other test constructs
      `LiveModeHandler(cfg)` directly, bypassing the parser dispatch entirely — add a regression test that exercises the
      REAL `_mode_dispatch_handler(args)` path with `mode=live`/`operation=timer-candles` (a thin config + mocked
      orchestration is enough) so this can't silently regress again. Separately, `LiveModeHandler.run()`
      (`live_mode_handler.py:76`) defaults `categories` to `["CEFI", "TRADFI", "DEFI"]` when the caller passes none —
      PREDICTION (and SPORTS) are excluded from the default, so even a fixed dispatcher would silently skip prediction
      unless a caller explicitly passes `categories=["PREDICTION", ...]`. Fix both: (1) correct the dispatcher to
      `live_handler_cls(config)` + call `.run(interval=..., categories=..., venues=..., timeframes=...)` derived from
      `args` instead of passing `args` itself: (2) either default `categories` to `list(MarketAssetGroup)` or make the
      omission an explicit, documented choice (comment) rather than a silent gap. Repo: market-data-processing-service.
      Done when: QG-green with the new dispatch-path regression test, and PREDICTION is reachable via
      `--mode live --operation timer-candles` with no `--categories` override. — **DONE 2026-08-04 (slot-11,
      backend_engineer)**: `market-data-processing-service@558b5b7`. `_mode_dispatch_handler` now constructs
      `get_service_config()` and calls `live_handler_cls(config)`, then
      `handler.run(interval=..., categories=...,     venues=..., timeframes=...)` — all four derived from `args` (added
      a new `--interval` CLI flag; venues/timeframes reuse the existing `--venues`/`--timeframes` flags; categories
      reuse `get_categories_from_args()`, the same helper the batch path already uses, so an omitted
      `--CEFI/.../--PREDICTION` filter resolves to every `MarketAssetGroup`). Also fixed `LiveModeHandler.run()`'s own
      categories default from `["CEFI", "TRADFI", "DEFI"]` to `list(MarketAssetGroup)` so any other caller gets full
      coverage too. Added `test_live_mode_dispatch_constructs_real_live_mode_handler_with_config` — exercises the REAL
      `LiveModeHandler` class (not a fully-mocked stand-in) through the real dispatch path, so the
      construction/call-signature mismatch can't silently regress; updated the two pre-existing fully-mocked dispatch
      tests to assert the new call contract. Evidence: `bash scripts/quality-gates.sh` full run green (2342 passed, 0
      skipped-relevant, sentinel `.qg_last_passed_sha=558b5b788d2ab8ca9164f6c6683b9b792d06c034`); verified `558b5b7` is
      an ancestor of `origin/live-defi-rollout` post-quickmerge.
- [ ] [OPS] P2. **Operationally launch (or explicitly decide not to) the `mdps-features-live-{asset_group}` VM cluster —
      currently launched for NO asset_group, fleet-wide, not just prediction.**
      `deployment-service/scripts/vm/     launch-mdps-features-live.sh --asset-group <cefi|defi|tradfi|sports|prediction>`
      is code-ready (shipped 2026-05-11/12) and is the ONLY launcher wired to MDPS's real production live path
      (`--operation streaming-aggregation` → `MDPSStreamingAggregator`, the Live=Batch event-driven architecture per
      `live_persist_05_mdps_cutover_2026_06_26.md` Phase 5) — but its own header comment says operational launch was
      deferred to "Phase 15" of `plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md`, and that
      archived plan's own Phase 15 entry (status: `complete` at the plan level, but 15.2 "7-day live smoke" explicitly
      marked `DEFERRED-POST-CUTOVER` → successor plan, never named/found). Confirmed LIVE on 2026-08-04:
      `gcloud compute     instances list --project=central-element-323112` returns **zero** `mdps-features-live-*`
      instances, running or terminated, for any of the 5 asset_groups; zero terraform/Cloud Scheduler/cron references to
      `mdps-features-live` or `streaming-aggregation` anywhere in deployment-service. The ACTUALLY-running prediction
      live VMs (`prediction-live-{kalshi,polymarket}-{trades,book_snapshot_5}-*`, confirmed RUNNING) launch MTDS
      raw-tick capture only (`launch-prediction-live.sh` → `VM_SERVICE=market_tick_data_service`) — never MDPS. Same
      true for CEFI's real live VM (`mtds-live-cefi-consolidated-*` — MTDS websocket-streaming only, zero MDPS). Repo:
      deployment-service (+ operator decision on which asset_groups to launch first). Done when: EITHER the VM cluster
      is launched for prediction (+ ideally the rest of the fleet) with a T+10 verify per the no-fire-and-forget rule,
      OR an operator ruling explicitly defers it with a named successor plan/owner (not a second silent drop).
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

- **2026-08-04 (slot-6, data_engineering) — todo 1 root-cause, VERDICT: worker never deployed (fleet-wide, not
  prediction-specific).** Two independent MDPS live-mode code paths exist, and NEITHER is operationally running for
  PREDICTION — or for any other asset_group:
  1. **`--mode live --operation timer-candles`** (the default, the path this todo names) → `LiveModeHandler`. No
     launcher in `deployment-service` invokes it at all (`grep -rn "timer-candles"` / `grep -rln "live_mode_handler"`
     against the whole repo: zero hits). It is effectively dead code from a deployment standpoint. It is ALSO currently
     broken if anyone tried to invoke it: `market_data_processing_service/cli/parser.py:71-74`
     (`_mode_dispatch_handler`) calls `live_handler_cls()` with no `config` arg, then `handler.run(args)` passing a raw
     `argparse.Namespace` — but the real `LiveModeHandler.__init__` requires `config: MarketDataProcessingServiceConfig`
     and `.run()`'s real signature is `(interval, categories, venues, timeframes)`. Confirmed by direct execution
     (read-only, no GCS I/O):
     `cd market-data-processing-service && uv run python3 -c "from market_data_processing_service.cli.handlers.live_mode_handler import LiveModeHandler; LiveModeHandler()"`
     → `TypeError: LiveModeHandler.__init__() missing 1 required positional argument: 'config'`. This bug is masked from
     CI because `test_cli_parser_coverage.py` fully mocks `LiveModeHandler` and every other test constructs
     `LiveModeHandler(cfg)` directly (bypassing the real parser dispatch). Separately, `live_mode_handler.py:76`
     defaults `categories` to `["CEFI", "TRADFI", "DEFI"]` when none are supplied — PREDICTION (and SPORTS) are excluded
     from the default, a third, independent gap.
  2. **`--mode live --operation streaming-aggregation`** → `MDPSStreamingAggregator` (event-driven via the UTL
     `EventTransport`/Redis-Stream facade — the real "Live = Batch" architecture per
     `plans/archive/2026_06/live_persist_05_mdps_cutover_2026_06_26.md` Phase 5). This IS the intended production live
     path, and its launcher —
     `deployment-service/scripts/vm/launch-mdps-features-live.sh --asset-group <cefi|defi|tradfi|sports|prediction>` —
     is code-ready (shipped 2026-05-11/12, registered identically for all 5 asset_groups in `vm_prefix_registry.py` +
     `launcher_registry.py`, no prediction-specific exclusion) but was **never operationally invoked**. Its own header
     comment says so explicitly ("operational launch awaits Harsh slot 5 per-service consumer wiring + Phase 12
     reconciliation gate green"), and the archived plan that owns Phase 15
     (`plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md`, `status: complete` at the plan level)
     explicitly marks its own "15.2 7-day live smoke" sub-item `DEFERRED-POST-CUTOVER` to a named successor
     (`Phase 3.5 per-venue rollouts → cluster bootstrap → 7-day smoke`) that this investigation found no evidence of
     ever having executed.
  - **Live confirmation (2026-08-04, read-only):** `gcloud compute instances list --project=central-element-323112` (68
    total instances, all zones) returns **zero** instances matching `mdps-features-live-*`, running OR terminated, for
    any of the 5 asset_groups. Zero terraform/Cloud Scheduler/cron references to `mdps-features-live` or
    `streaming-aggregation` anywhere in `deployment-service`. The prediction live VMs that ARE actually running
    (`prediction-live-{kalshi,polymarket}-{trades,book_snapshot_5}-20260803-*`, confirmed RUNNING) are MTDS raw-tick
    capture producers only (`launch-prediction-live.sh` → `VM_SERVICE=market_tick_data_service`) — they never invoke
    MDPS. The same is true of CEFI's actual live VM (`mtds-live-cefi-consolidated-20260802-*`, confirmed RUNNING) — MTDS
    websocket-streaming only, zero MDPS. Cloud Run's MDPS deployment
    (`deployment-service/configs/cloud-run/market-data-processing-service.yaml`) is a health-check-only FastAPI app
    (`market_data_processing_service/api/main.py` wires `/health`+`/readiness` via UTL `make_health_router` — no
    candle-processing code runs there despite the yaml's stale "streaming processor runs as background thread" comment).
  - **Verdict**: the MDPS live-mode continuous worker was never deployed/launched for PREDICTION — but this is a
    **fleet-wide gap** (confirmed identically absent for CEFI, DEFI, TRADFI, SPORTS), not a prediction-specific defect.
    `deployment-service/configs/clusters/prediction.yaml`'s batch-cron-only shape is therefore CORRECT/consistent with
    the rest of the fleet, not an omission specific to prediction. 2 new follow-up todos filed above: fixing the
    `timer-candles` CLI dispatch bug (dead-but-broken code, low urgency since nothing invokes it) and the actual
    operational-launch decision (higher-leverage — it's the one gap that, if closed, would give prediction AND every
    other asset_group real live-mode processed candle output). Independently cross-verified by a parallel Explore
    sub-agent dispatched from this session against the same two repos — findings matched exactly, plus it additionally
    confirmed CEFI's real live VM also skips MDPS, strengthening the fleet-wide (not prediction-specific) conclusion.
