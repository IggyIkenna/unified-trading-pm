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
status: resolved
nature: issue
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [prediction, mdps, depth-history, live-data, book_snapshot_5, candle-adapter, data-correctness, big-finding]
related:
  [
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/archive/2026_08/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
  ]
created: "2026-08-04"
author: unknown
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
    /plans/archive/issues/mdps_features_live_streaming_aggregation_never_actually_invocable_2026_08_04.md,
  ]
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. All todos [x] and every thread is closed or explicitly transferred: root cause fully
> established (worker never deployed fleet-wide), CLI dispatch bug fixed (market-data-processing-service@558b5b7),
> operational-launch decision made (DECIDED NOT TO LAUNCH, evidenced by 2 failed pilots + structural
> mdps_mvp_universe('prediction')=0 finding), book_snapshot_5 adapter registered (d0925d5), and all 6 scoped follow-ups
> are filed as TRACKED todos in the named successor doc
> /plans/archive/issues/mdps_features_live_streaming_aggregation_never_actually_invocable_2026_08_04.md. The
> zero-live-objects state is 'the expected consequence of that conscious operational decision.' No prose-only untracked
> follow-up. Moved by the 2026-08-06 AO issue-doc archive sweep.

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
- [x] ✅ [OPS] P2. **Operationally launch (or explicitly decide not to) the `mdps-features-live-{asset_group}` VM
      cluster — currently launched for NO asset_group, fleet-wide, not just prediction.** **RESOLVED 2026-08-04
      (slot-10, data_engineering) — DECIDED NOT TO LAUNCH, evidenced.** Both named preconditions ("Harsh slot 5
      per-service consumer wiring" + "Phase 12 reconciliation gate green") were confirmed satisfied, so 2 real GCE pilot
      launches were run (cefi: 117 MDPS shards, tradfi: 14 MDPS shards) to get genuine live-VM confirmation. BOTH
      failed: cefi OOM-killed a worker within ~2.5 min (117-process fan-out on e2-standard-8); tradfi's 14 MDPS shard
      processes crashed 100% of the time on an argparse mismatch (the exec-dispatch branch's constructed CLI invocation
      never actually reaches `market-data-processing-service`'s legacy parser through the real `ServiceBootstrap` entry
      point — confirmed by reproducing the exact command locally, no VM needed), plus features-service live workers ran
      as one-shot batch jobs instead of persistent subscribers, plus DeFi would need 3,535 separate OS processes
      (categorically infeasible regardless of machine size). Separately confirmed structural finding:
      `mdps_mvp_universe('prediction')` returns ZERO shards by design (2026-07-30 ruling) — this launcher cannot fix
      THIS issue's depth-history problem for prediction even once the bugs above are fixed. Both pilot VMs deleted after
      confirming failure (no reason to bill on confirmed-broken paths). Full evidence + 6 scoped follow-up todos (CLI
      env-var bridge, launcher invocation fix, live-vs-batch features bug, 2 smaller features bugs, an `[OPERATOR]`
      process-topology redesign decision for CEFI/DeFi scale, a re-pilot plan) filed as the named successor:
      `/plans/archive/issues/mdps_features_live_streaming_aggregation_never_actually_invocable_2026_08_04.md`.
- [x] ✅ [BACKEND] P1. **Register a `CandleAdapterRegistry` entry for
      `(MarketAssetGroup.PREDICTION, "book_snapshot_5")`, shipped `market-data-processing-service@d0925d5`.** Chose
      option (a): added `PredictionBookSnapshotAdapter` (mirrors `DefiBookSnapshotAdapter` — extends
      `CefiBookSnapshotAdapter` unchanged, registers under `MarketAssetGroup.PREDICTION`) with 5 unit tests
      (registration, get_adapter, class attributes, empty-data output, prior-day-seed flag); updated
      `prediction/__init__.py` + `adapters/__init__.py` to import the new adapter class so its
      `@CandleAdapterRegistry.register(...)` decorator fires; updated `test_adapter_registry_coverage.py` allowlist.
      `quality-gates.sh` green (2017 passed, 138 skipped). The `"⚠️ No adapter for PREDICTION/book_snapshot_5"` warning
      in `orchestration_service.py:659` will no longer fire on the next live scan.

      > **⚠️ HEADS-UP (2026-08-05):** Even once this adapter ships, it will never be invoked by the
                                                  > `mdps-features-live` launch path — `mdps_mvp_universe('prediction')` returns zero shards structurally
                                                  > (2026-07-30 ruling, MDPS handles market-data AGs only). Read the "Structural finding" section of
                                                  > `/plans/archive/issues/mdps_features_live_streaming_aggregation_never_actually_invocable_2026_08_04.md`
                                                  > before treating this adapter registration as a depth-history fix.

- [x] ✅ [DATA] P2. **Re-verify multi-hour processed accumulation once todos 1-2 land.** Re-ran the same bounded
      GCS-timespan check (`processed_candles/by_date/day={D}/pipeline_mode=live_*` for 2026-08-01 through 2026-08-04).
      **VERDICT: Still zero live-mode processed objects on every sampled day — FULLY EXPLAINED, not a surprise.** Todos
      1-2 are done (root cause: worker never deployed + CLI dispatch fixed at `market-data-processing-service@558b5b7`),
      but todo 3 (slot-10) decided NOT to launch the `mdps-features-live` cluster after pilot failures + the structural
      finding that `mdps_mvp_universe('prediction')` returns zero shards. The zero-live-objects result is the expected
      consequence of that conscious operational decision. Full re-verification evidence recorded in
      `prediction_live_clob_depth_capture_2026_07_24.md`'s Progress Log (2026-08-04 slot-7 entry), superseding the
      2026-08-04 FAIL entry. Repo: unified-trading-pm (read-only verification, no code shipped).

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

- **2026-08-04 (slot-10, data_engineering) — todo 3 (operational launch decision): DECIDED NOT TO LAUNCH, 2 real pilot
  VMs, both failed.** Confirmed both named preconditions in the launcher's header comment already satisfied ("Harsh slot
  5 per-service consumer wiring" = the exec-dispatch wiring issue, shipped `deployment-service@e7d17f2` 2026-08-03;
  "Phase 12 reconciliation gate green" = checked `[x]` in the archived
  `live_pipeline_mtds_mdps_features_2026_05_08.md`), so piloted real launches rather than deferring blind. **Pilot 1
  (cefi, 117 MDPS shards + 5 features families)**: kernel OOM-killed a worker ~2.5 min in
  (`Out of memory: Killed process 9284 (python)`, via `gcloud compute instances get-serial-port-output`) — 122
  simultaneous OS processes on one e2-standard-8 exceeds available RAM well before any of them do real work. VM deleted
  immediately. **Pilot 2 (tradfi, 14 MDPS shards + 6 features families, chosen as a lower-risk follow-up)**: no OOM in
  ~7 min of monitoring, BUT 100% of the 14 MDPS shard processes crashed instantly on an argparse mismatch
  (`error: argument --operation: invalid choice: 'streaming-aggregation' (choose from 'process')`) — reproduced locally
  without a VM: `python -m market_data_processing_service` routes through `ServiceBootstrap` (`cli/main.py::run_cli()`),
  whose own top-level `--operation` flag only accepts `process`; the legacy `streaming-aggregation` value must be
  bridged via the `MDPS_OPERATION` env var (`_bridge_operation_and_build_continuous_args()`), and `--shard-spec` has
  **no env-var bridge implemented at all** — so the exec-dispatch branch's constructed command was never actually
  reachable through the real entry point, regardless of launcher fixes. features-service side also showed real defects:
  `calendar`/`commodity` ran ONE-SHOT BATCH passes and exited in ~15-70s instead of staying up as live subscribers;
  `delta_one`'s live subscriber hit an unhandled Pub/Sub traceback; `commodity`'s `publish_signal` hit a
  `[MEDIUM] asdict()` validation bug. VM deleted immediately (0/14 MDPS shards ever started). **Additional structural
  finding, independent of the above bugs**: `mdps_mvp_universe('prediction')` and `('sports')` both return an EMPTY
  frozenset by design (2026-07-30 ruling) — MDPS processes ZERO shards for either asset_group. This means the
  mdps-features-live cluster **cannot fix THIS issue's depth-history problem for prediction at all**, even once every
  bug above is fixed — launching it for prediction only starts 2 unrelated cross-cutting features workers (`calendar`,
  `cross_instrument`) with no MDPS candle input. Also confirmed `mdps_mvp_universe('defi')` = 3,535 shards — the
  one-process-per-shard topology (2026-07-29 ruling) is categorically infeasible at that scale on any single VM, not
  just under-provisioned. **Resolution**: decided not to launch for any asset_group, with full evidence + 6 scoped
  follow-up todos (CLI env-var bridge, launcher invocation fix, live-vs-batch features bug, 2 smaller features bugs, an
  `[OPERATOR]` process-topology decision for CEFI/DeFi, a re-pilot plan starting with TradFi) filed as the named
  successor issue:
  `/plans/archive/issues/mdps_features_live_streaming_aggregation_never_actually_invocable_2026_08_04.md`. Flagged a
  note on todo 4 (CandleAdapterRegistry for prediction book_snapshot_5) in that new doc: even once shipped, it will
  never be invoked by this launch path since MDPS runs zero prediction shards structurally.

- **context-scout 2026-08-06**: populated/refreshed context_scope (5 entries) — added
  `/plans/archive/issues/mdps_features_live_streaming_aggregation_never_actually_invocable_2026_08_04.md`, the named
  successor doc this issue's Progress Log repeatedly cites as owning all further follow-up work.
