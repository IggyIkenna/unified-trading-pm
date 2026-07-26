---
doc_type: issue
title:
  TradFi MDPS→build-continuous→features pipeline — 2 of the 4 originally-diagnosed format mismatches still unfixed after
  the 2026-06-29 "resolution"; no tradfi features run has ever successfully landed; the archived resolution doc's own
  "Option A" label doesn't match what actually shipped
summary: >-
  Re-diagnosed `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`'s stale BLOCKED-OPERATOR-DECISION P0 items
  (2026-07-26, via /ag-closeout-audit follow-up tradfi_sp500_ml_stale_mdps_blocker_2026_07_26.md). The archived
  features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md diagnosed 4 format mismatches blocking the MDPS
  process→build-continuous→features-service pipeline for tradfi/ES and claims "RESOLVED 2026-06-29 via Option A (direct
  raw-MTDS read, bypass MDPS)" (mdps@cc63d1b + features-service@34a5d4ff + mdps@7d630a3). Live re-verification found:
  (1) mismatch 1 (data_type=trades vs ohlcv_1m) IS fixed (cc63d1b); the blank-instrument_id manifest bug IS fixed
  (34a5d4ff); (2) mismatch 2 (filename format: panama_core still emits Databento-date-format CME:FUTURE:{root}-{expiry},
  MDPS's canonical output is still the short-symbol form) is UNFIXED; (3) mismatch 4 (build-continuous's
  continuous_future output path vs features-service's _DERIVATIVE_DATA_TYPES read path, which still only lists
  options_chain/futures_chain) is UNFIXED; (4) NO successful tradfi features-delta-one or features-volatility run has
  EVER landed -- features-tradfi-prd-central-element-323112 has no _index/availability_index.parquet at all (404, not
  just empty); (5) the archived doc's own "Option A" (bypass MDPS entirely) label does not match the shipped code --
  TRADFI_DATA_TYPE_FALLBACKS / _try_one_tradfi_fallback in features_service/delta_one/app/core/data_loader.py still
  calls self.load_candles() against the SAME MDPS processed_candles/ path with an alternate data_type, not a raw-MTDS
  read; this looks like a partial Option-B- direction fix (fix MDPS's output format) rather than Option A (bypass MDPS).
  Filed so the real remaining engineering work (fix mismatches 2+4, or make and implement a definitive Option A/B call)
  is tracked as concrete work instead of the plan reverting to a vague "needs operator decision" state that already
  looked resolved once and wasn't.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [features-service, market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, mdps, features, build-continuous, es, pipeline-mismatch, plan-hygiene]
related:
  [
    /plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md,
    /plans/archive/issues/tradfi_sp500_ml_stale_mdps_blocker_2026_07_26.md,
    /plans/archive/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md,
  ]
created: 2026-07-26
parent_epic: tradfi_master
priority: P1
source: [tradfi_sp500_ml_stale_mdps_blocker-001, live code + GCS re-verification 2026-07-26]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-26
locked_since:
---

# TradFi MDPS build-continuous mismatches 2+4 still open; no successful run ever landed

## What I found

Re-checking `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`'s two P0 items that read
`BLOCKED-OPERATOR-DECISION` against the CURRENT code + live GCS state (not just the archived issue doc's prose claim of
resolution):

**Fixed** (verified in shipped commits):

- Mismatch 1 (MDPS output `data_type`): `market-data-processing-service@cc63d1b` makes `TradfiTradesAdapter` write
  `output_data_type=ohlcv_1m` instead of `trades`.
- Blank-`instrument_id` manifest-lookup bug: `features-service@34a5d4ff` (`dependency_checker.py`).

**Still unfixed** (verified by direct code read, 2026-07-26):

- Mismatch 2 (filename format): `market_data_processing_service/engine/panama_core.py:101-103`
  `contract_id_for_expiry()` still returns `f"CME:FUTURE:{root}-{expiry:%Y%m%d}"` (Databento date-format). MDPS's own
  process-step output filename convention (per the archived doc, `CME:FUTURES:{root}{month}{year}.parquet`, e.g.
  `CME:FUTURES:ESH0.parquet`) was not changed to match — no commit in the 2026-06-28/29 batch touches `panama_core.py`
  or the process-step filename builder.
- Mismatch 4 (read-path handling): `features_service/delta_one/app/core/data_loader.py:650`
  `_DERIVATIVE_DATA_TYPES = {"options_chain", "futures_chain"}` — still no `continuous_future` entry, so even if
  build-continuous ran and wrote correctly, features-service's `_build_blob_path` has no code path to find it.

**No successful run has ever landed**:
`GET features-tradfi-prd-central-element-323112/_index/availability_index.parquet` returns 404 (object does not exist),
not an empty/stale manifest — confirming zero tradfi features-delta-one or features-volatility captures have ever
completed, before OR after the 2026-06-29 fixes.

**Archived doc's "Option A" label is itself disputed**: `features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md`
summarizes its own resolution as "Option A (direct raw-MTDS read path, bypass MDPS entirely)." But the actual runtime
mechanism that would use the 2026-06-28/29 fixes -- `TRADFI_DATA_TYPE_FALLBACKS` / `_try_one_tradfi_fallback` in
`data_loader.py` -- calls `self.load_candles(instrument_id=..., data_type=fallback_dt, ...)`, which reads from the SAME
`processed_candles/` MDPS-output bucket path with an alternate `data_type`, not a raw `raw_tick_data/` MTDS read. This
is architecturally closer to a PARTIAL Option B (fix MDPS's output so an existing MDPS-reading fallback path can find
it) than Option A (bypass MDPS). Not resolved here whether the archived doc's summary is simply wrong, or whether a
genuine Option-A `TradfiDirectDataLoader` shipped elsewhere and was later removed/never wired in -- flagging for whoever
picks up the follow-up todos below to settle definitively (their fix work will settle it either way: implementing Option
A means adding the bypass loader; fixing mismatches 2+4 means committing to Option B).

## Why it matters

The sp500_ml plan's P0 items were re-worded 2026-07-26 from "needs an operator decision" to "blocked on unfixed
mismatches 2+4" (see the plan's own edit history same date) precisely because a stale "already resolved" belief would
otherwise cause a future VM launch attempt to repeat the exact same failure the 3 prior attempts hit
(`features-delta-one-tradfi-20260624-0556/0612/0618`, `mdps-backfill-tradfi-20260624-065912` killed). This is directly
on the critical path for the S&P ML training + backtest work (~4 estimated AI-days of downstream work), which cannot
start without real tradfi/ES feature parquets.

## Recommended decision

- [x] [AGENT] P1. Fix mismatch 2 (filename format): either change `panama_core.contract_id_for_expiry` to emit the
      short-symbol form MDPS actually writes, or change MDPS's process-step filename builder to emit the Databento
      date-format `contract_id_for_expiry` produces -- pick ONE canonical form and make both sides agree (per the
      archived doc's own "Cleaner Option B variant" suggestion). (repo: market-data-processing-service) — ✅ FIXED, but
      NOT as originally diagnosed: live GCS + parquet-content verification (per slot-14's `BLK-581b75aa` recommendation)
      confirmed `panama_core.contract_id_for_expiry`'s Databento-date-format (`CME:FUTURE:{root}-{expiry}`) ALREADY
      matches the `instrument_id` values MDPS actually writes — there is no short-symbol-vs-date-format disagreement in
      current production data (verified against real ES/MES per-contract parquets in the prod tradfi market-data bucket,
      Jan-Feb 2020). The REAL bug: some shards bundle multiple contracts' candles into one `ticks.parquet` (the
      chain-bundle-fallback filename `candle_leaf_filename` emits whenever a write carries `underlying=` but no single
      representative `instrument_id` — confirmed live: a 2020-02-05 `ticks.parquet` held 3 distinct ES expiries' rows,
      each already correctly tagged with the canonical instrument_id), and
      `build_continuous_engine._load_per_contract_candles_for_day` derived `contract_id` purely from the leaf filename,
      so a bundled file's data was silently invisible to build-continuous regardless of what it held. Mirrors the same
      filename-vs-data-column bug class already fixed once for the live read path
      (`LiveOrchestrationMixin._eager_preprocess_and_recover_metadata`, 2026-05-05,
      `tests/unit/test_per_instrument_pipeline.py`). Fixed by reading each bundle's `instrument_id` column instead of
      trusting the filename, with 4 new regression tests (`tests/unit/test_build_continuous_engine.py`, verified to fail
      without the fix) — market-data-processing-service@62a1255. Answers `BLK-581b75aa`'s open question: a real fix was
      needed and shipped (not a no-op close as "already resolved").
- [x] [AGENT] P1. Fix mismatch 4 (read-path handling): add `continuous_future` handling to
      `features_service/delta_one/app/core/data_loader.py`'s `_DERIVATIVE_DATA_TYPES` (or an equivalent dedicated
      branch) so `_build_blob_path` can locate build-continuous's
      `processed_candles/.../instrument_type=continuous_future/venue=CME/underlying=ES/ticks.parquet` output. (repo:
      features-service) — ✅ FIXED 2026-07-26 (`features-service@65606d26`), but NOT as originally diagnosed:
      `data_loader.py`'s `_DERIVATIVE_DATA_TYPES` was a misdirected diagnosis — that function is never actually called
      for continuous-future reads. The real, dedicated (and already-tested since
      `tradfi_futures_roll_adjuster_centralisation_2026_06_17`) read path is
      `features_service/delta_one/engine/orchestrator.py`'s `_load_continuous_series`, which hand-rolls its own blob
      path and was missing the `pipeline_mode=batch_databento/` segment that MDPS's `build-continuous` writer
      (`build_continuous_engine._continuous_output_path`) always inserts via `build_canonical_candle_path`
      (`pipeline_mode=PipelineMode.BATCH_DATABENTO.value`) — a read path missing that segment can never match a real
      written object, regardless of `_DERIVATIVE_DATA_TYPES`. Fixed by building the read path via the SAME
      `build_canonical_candle_path` UTL SSOT the writer uses; updated
      `tests/delta_one/unit/test_orchestrator_continuous_read_path.py` with a segment-order assertion + an exact-string
      parity test pinned to the MDPS write side. `quality-gates.sh` full green (17,836 passed, 209 pre-existing skips).
- [x] [AGENT] P1. Re-verify mismatch 3 (ES absent from Databento raw `ohlcv_1m`) is still accurate against the CURRENT
      raw MTDS bucket state
      (`raw_tick_data/.../pipeline_mode=batch_databento/.../futures_chain/data_type=ohlcv_1m/underlying=ES/`) -- the
      archived doc's finding is from 2026-06-24, over a month stale; TradFi data coverage moves fast. If ES ohlcv_1m now
      exists, this mismatch may already be moot. (repo: market-data-processing-service, verification only) — ✅ MOOT,
      not real: live `gcloud storage ls` on `market-data-tick-tradfi-prd-central-element-323112` shows ES/MES ohlcv_1m
      data DOES exist, but under `underlying=SP500` (a real non-trivial parquet file, e.g. 53,629 bytes at
      `raw_tick_data/by_date/day=2026-01-02/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/instrument_type=futures_chain/data_type=ohlcv_1m/underlying=SP500/quote=USD/margin=linear/ticks.parquet`),
      spot-confirmed present on 2020-01-02, 2022-06-15, 2024-03-01, 2026-01-02, and 2026-07-01 (consistent with the
      archived doc's own "8,997 captured rows for ES, 2020-01-01→2026-06-22" manifest claim). The archived doc's "ES
      absent" finding was itself a vocabulary-probe miss, not a real absence: UAC's `EXCHANGE_CODE_TO_NAME` registry
      (`unified_api_contracts/registry/tradfi_instrument_universe.py:600-601`, `"ES": "SP500", "MES": "SP500"`) is the
      live mapping the MTDS writer actually uses for the `underlying=` path segment (consumed by
      `market_tick_data_service/engine/orchestrator/partitioned_writer.py`,
      `.../adapters/tradfi/databento_enrichment.py`, `.../reader.py`) — this root-code→descriptive-underlying-name
      convention was introduced 2026-03-26 (`uac@e19b231d`), three months BEFORE the archived doc's 2026-06-24 check, so
      probing literal `underlying=ES`/`underlying=MES` was checking a path the writer has never emitted. No code change
      needed here: confirmed MDPS's process-step adapters (`app/adapters/tradfi/trades_adapter.py` et al.) delegate
      raw-candle reads to `market_tick_data_service/reader.py` (the documented SSOT per
      `orchestration_scheduling.py:184`, `orchestration_scanner.py:371`), which already applies the same
      `EXCHANGE_CODE_TO_NAME` mapping — so the process step correctly resolves root=ES/MES to raw `underlying=SP500`
      today; this is NOT a live bug, just a stale finding in the archived doc.
- [ ] [AGENT] P0. After mismatches 2+4 (+3 if still real) are fixed, launch the MDPS build-continuous run for
      `--root ES`, verify output lands at the expected canonical path, THEN launch features-delta-one-tradfi for ES and
      confirm real feature parquets land (check the manifest actually gains rows -- not just "job exit 0"). This closes
      `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`'s P0 items per the "Plans run to actual completion"
      HARD RULE. (repo: market-data-processing-service, features-service)
- [ ] [AGENT] P1. Investigate why MDPS build-continuous's `24h`/`1d` output has genuinely sparse real coverage
      (`total_rows=454` across `days=2398` on the shipped ES re-run, ~19% hit rate — a real single day near 2024-06-17
      only found 14/86 real prior days) even after the right-edge-timestamp date-filter fix
      (`market-data-processing-service@e9edb39`). Likely a `build_active_contracts_table`/`extract_roll_events` gap
      specific to daily granularity's single-bar-per-contract-per-day nature (no redundancy the way 1440 intraday bars
      provide) — confirm via direct GCS gap analysis before assuming a code fix. (repo: market-data-processing-service)
- [x] [AGENT] P1. `_TfClusterMixin._process_tf_clusters_date_range`'s per-date loop (`_process_one_date_for_cluster`
      returning `False` → `if not ok: return False`) aborts the ENTIRE multi-day range on the FIRST date that fails for
      ANY reason — including a genuine, expected absence (e.g. a market holiday). Any real multi-year backfill will
      eventually hit one. Needs per-date shard-level isolation (skip + record_empty/record_failed for that date,
      continue) per `/codex/04-architecture/shard-level-failure-isolation.md`'s own stated principle, rather than
      today's fail-fast semantics. Not roll-sensitive-specific — affects any feature-group batch run over a real range.
      (repo: features-service) — ✅ FIXED 2026-07-26 (`features-service@81ab1264`): confirmed
      `record_empty`/`record_failed` manifest recording ALREADY happens per-date, unconditionally, inside
      `process_feature_group_with_preloaded_candles` → `_run_feature_group_lifecycle` (every call writes an honest
      captured/empty_confirmed manifest row via `_write_feature_group_manifest`, success or not) — so the only real bug
      was the CONTROL FLOW: `if not ok: return False` inside the per-date `while` loop threw away every LATER date's
      chance to even be attempted, not just the failed one. Fixed by extracting the per-date iteration into
      `_process_one_date_tracked` (logs + reports `ok` without aborting) and changing the outer loop to track
      `any_attempted`/`any_succeeded` across the whole range instead of early-returning — mirrors the same isolation
      contract `_process_groups` already uses one level up (`delta_one/cli/handlers/batch_handler.py`: "return True if
      ANY unit succeeded"; only returns False if EVERY date across EVERY cluster failed). Extracted the helper to keep
      `_process_tf_clusters_date_range` under the 50-line method cap (QG 5.68). 2 new/rewritten regression tests in
      `tests/delta_one/unit/test_tf_cluster_helper.py` (`test_continues_past_a_failed_date` — 5-date range with one
      failing date now processes all 5 and returns `True`, replacing the old `test_stops_early_on_failure` which
      asserted the buggy abort-after-2 behavior; `test_returns_false_when_every_date_fails` — every date attempted, only
      returns `False` when none succeed). Full `quality-gates.sh` green (17,864 passed, 209 pre-existing skips, sentinel
      SHA-verified); `quickmerge --agent` landed clean on `live-defi-rollout`.

## Progress log

- 2026-07-26: Filed while working `tradfi_sp500_ml_stale_mdps_blocker-001` (itself filed by the daily
  `/ag-closeout-audit tradfi` run re-checking a Deferred citation). Live GCS + code re-verification found the underlying
  pipeline is still genuinely blocked, just by a different (partially-overlapping) set of issues than the
  operator-decision framing implied. Sp500_ml plan's P0 items re-worded to point here instead of re-requesting an
  already-answered operator decision.
- 2026-07-26 (slot-14, `defi_satellite_ao_dispatch_batch2-013` follow-up dispatch, todo 4 of this doc): the AO
  dispatcher handed me todo 4 ("after mismatches 2+4 fixed, launch + verify") directly — there is no per-todo prereq
  mechanism within one plan (only whole-plan `depends_on`/`sequential`), so it does not know todo 4 depends on todos 1-3
  in THIS SAME doc. Re-confirmed via direct code read that mismatch 2 (`panama_core.py:103`, still
  `f"CME:FUTURE:{root}-{expiry:%Y%m%d}"`) and mismatch 4 (`data_loader.py:650`, `_DERIVATIVE_DATA_TYPES` still
  `{"options_chain", "futures_chain"}`, no `continuous_future`) are genuinely still unfixed — todo 4 is premature. **New
  finding while scoping the mismatch-2 fix**: this doc's (and the archived doc's) claim that MDPS's process-step
  canonically writes short-symbol filenames (`CME:FUTURES:{root}{month}{year}.parquet`, e.g. `CME:FUTURES:ESH0.parquet`)
  could NOT be confirmed against CURRENT production code —
  `market_data_processing_service/app/core/output_path_helpers.py`'s `candle_output_filename`/`candle_leaf_filename` is
  a pure `f"{instrument_id}.parquet"` passthrough (no dedicated short-symbol builder found anywhere in the repo outside
  a `unified_api_contracts/internal/testing/` mock-data generator, which is test-only). More importantly,
  `canonical_writer.py`'s `write_candle_parquet` calls `_renormalize_legacy_instrument_ids` →
  `_renormalize_legacy_tradfi` (`canonical_writer_shaping.py:494-563`), which explicitly detects a legacy 2-segment id
  (e.g. `CME:ESH0`) and REBUILDS it into the canonical 3-segment `CME:FUTURE:ES-20240621` form via UAC's
  `build_instrument_id` — i.e. the SAME Databento-date-format shape `panama_core.contract_id_for_expiry` already
  produces. This raises real doubt that mismatch 2 is still an actual bug rather than something the renormalization
  layer already fixed since the archived doc was written (2026-06-24, over a month stale) — but I could NOT get a live
  GCS listing of the actual current `processed_candles/` filenames for ES within this session (bucket-name resolution
  needs the MDPS service venv set up, which wasn't done yet in my slot for this repo —
  `resolve_bucket_name(kind=..., asset_group="tradfi")`'s exact `kind` string for this bucket was not determined either;
  do NOT guess a bucket name, it 404s loudly instead of listing empty). **This is exactly the kind of
  live-verification-first step that should happen BEFORE trusting either doc's filename-format claim.** Separately, this
  doc's own text explicitly flags an unresolved architectural question (Option A: bypass MDPS entirely via a direct
  raw-MTDS read in features-service, vs Option B: fix MDPS's output format) that the ORIGINAL archived doc's author
  could not settle and left for whoever picks up these todos — picking the wrong side before a live-state check risks
  throwaway code on a live production TradFi data pipeline. Filed `/blocked` (`BLK-581b75aa`) rather than guessing;
  skipped todo 4 back to the queue as premature. **Recommended next step for whoever picks this up**: (1) set up the
  MDPS venv (`bash scripts/setup.sh` in `market-data-processing-service`), resolve the tradfi `processed_candles` bucket
  name (grep `cloud-providers.yaml` for the `market_data`/`processed_candles` kind key — I did not locate the exact yaml
  key in this session), (2) `gcloud storage ls` the real current ES filenames under `processed_candles/`, (3) compare
  against `panama_core.contract_id_for_expiry`'s output to settle whether mismatch 2 is real or already moot, (4) only
  then decide whether todo 1 (fix mismatch 2) is still needed, or whether the todo should instead be closed as "already
  resolved by the renormalization layer, doc was stale."
- 2026-07-26 (slot-8, todo 3 of this doc): Re-verified mismatch 3 against live GCS state on
  `market-data-tick-tradfi-prd-central-element-323112`. **MOOT** — ES/MES ohlcv_1m raw Databento data DOES exist; the
  archived doc's 2026-06-24 "ES absent" finding was a vocabulary-probe miss, not a real absence. The writer emits the
  `underlying=` path segment via UAC's `EXCHANGE_CODE_TO_NAME` registry (`"ES": "SP500", "MES": "SP500"`,
  `tradfi_instrument_universe.py:600-601`, live since `uac@e19b231d` 2026-03-26 — three months before the archived doc's
  check), so the real path is `underlying=SP500`, not `underlying=ES`. Spot-confirmed real parquet files (e.g. 53,629
  bytes) present on 2020-01-02, 2022-06-15, 2024-03-01, 2026-01-02, 2026-07-01 — consistent with the archived doc's own
  manifest-row date range. Also traced MDPS's process-step adapters (`app/adapters/tradfi/trades_adapter.py`) and
  confirmed they delegate raw-candle reads to `market_tick_data_service/reader.py` (documented SSOT), which already
  applies the same `EXCHANGE_CODE_TO_NAME` mapping — so no NEW mismatch was introduced by this naming convention; the
  process step already resolves root=ES to raw `underlying=SP500` correctly. Net effect on todo 4's blocker: it is now
  gated on mismatches 2+4 ONLY (3 is closed, not real). Verification-only todo — no code shipped, checkbox flipped in
  this doc.
- 2026-07-26 (slot-9, todo 1 of this doc): Did the live-verification-first work slot-14 recommended before touching
  `panama_core.py` — set up the MDPS venv, resolved the tradfi bucket (`batch.env`'s configured
  `PROTOCOL_DATA_SOURCE_BUCKET_TRADFI=uts-prod-market-data-tradfi` is itself STALE/404; the real bucket per
  `cloud-providers.yaml`'s env-tiered convention is `market-data-tick-tradfi-prd-central-element-323112` — noting this
  separately since it's a distinct config bug from mismatch 2, not fixed here as out of scope for this todo), then
  `gcloud storage ls` + downloaded real `processed_candles/` parquets for ES/MES. Confirmed
  `panama_core.contract_id_for_expiry`'s output (`CME:FUTURE:ES-20200320` etc.) IS the live `instrument_id` value MDPS
  writes — read the actual parquet bytes, not just filenames, via the MDPS venv's polars. So the ORIGINAL mismatch-2
  diagnosis (short-symbol vs Databento-date-format) is disproven by live evidence: there is no such disagreement to
  reconcile, and no separate "MDPS process-step filename builder" producing short-symbol names exists anywhere in
  current code (confirms slot-14's finding). Kept digging rather than closing as a no-op, since a real production
  symptom (build-continuous never landing a row) still needed an explanation: found that some
  `(day, tf, dt, underlying)` shards write a bundled `ticks.parquet` (multiple contracts' rows in one file, e.g.
  2020-02-05's ES shard held 3 expiries) instead of one file per contract, and `_load_per_contract_candles_for_day`
  matched contracts by parsing the leaf filename — so `ticks.parquet` (leaf minus `.parquet` = `"ticks"`) never matched
  any real `CME:FUTURE:...` contract id, silently dropping that shard's data from every build-continuous run regardless
  of its content. Verified via object `creation_time` that the bundled file and a coexisting properly-named file were
  written in the SAME 2026-07-23 run (19s apart) — ruling out "two different code versions from different points in
  time" as the explanation; this is current, live write behavior. Fixed `_load_per_contract_candles_for_day` to
  recognize the `ticks.parquet` sentinel (`output_path_helpers.CHAIN_BUNDLE_FILENAME`) and split its rows by the
  `instrument_id` column instead of the filename, mirroring the identical fix already shipped for the live
  per-instrument path (`live_workers.py`'s `_eager_preprocess_and_recover_metadata`, 2026-05-05). Added 4 regression
  tests; confirmed via `git stash` that exactly the 2 bundle-covering tests fail without the fix (the other 2 edge-case
  tests pass either way, as expected). Shipped market-data-processing-service@62a1255 (full `quality-gates.sh` green,
  `quickmerge --agent`). Todo 2 (mismatch 4, features-service `_DERIVATIVE_DATA_TYPES`) and the stale
  `PROTOCOL_DATA_SOURCE_BUCKET_TRADFI` config bug remain open — the latter is a new finding, not yet a todo in any doc;
  whoever picks up todo 4 (launch + verify) should fix the bucket env var first or the launch will 404 before ever
  reaching mismatch 2/4's code paths.
- 2026-07-26 (worker, slot 6): Fixed mismatch 4, but relocated the diagnosis. Grepped for the ONLY consumer of
  continuous-future candles in features-service (`orchestrator.py`'s `_maybe_roll_adjust`/`_load_continuous_series`,
  gating `futures_basis`/`technical_indicators`/`momentum` for TRADFI) and found it bypasses `data_loader.py`'s
  `_build_blob_path`/`_DERIVATIVE_DATA_TYPES` entirely — it hand-rolls its own path. `_DERIVATIVE_DATA_TYPES` is keyed
  by `data_type` (e.g. `options_chain`/`futures_chain` ARE data_type values there); continuous-future output's
  `data_type` is `ohlcv_1m` (per MDPS's `DEFAULT_DATA_TYPES`) with `instrument_type="continuous_future"` as a SEPARATE
  axis, so adding `"continuous_future"` to that data_type-keyed set would have been a no-op with no runtime effect.
  Comparing `_load_continuous_series`'s hand-rolled path against the MDPS writer's actual
  `build_canonical_candle_path(...)` call (`build_continuous_engine._continuous_output_path`) found the REAL bug: the
  read path omitted the `pipeline_mode=batch_databento/` segment the writer always inserts — a read that can never match
  a real written object regardless of `_DERIVATIVE_DATA_TYPES`. Fixed by routing the read through the same
  `build_canonical_candle_path` UTL builder the writer uses (never hand-roll this shape, mirroring the writer's own
  stated principle); extended the existing dedicated test file
  (`tests/delta_one/unit/test_orchestrator_continuous_read_path.py`) with a segment-order assertion and an exact-string
  parity test pinned to the writer's shape. `quality-gates.sh` full green (17,836 passed, 209 pre-existing skips,
  sentinel-verified). Shipped `features-service@65606d26`.
- 2026-07-26 (slot 3, todo 4 — launch + verify, IN PROGRESS): before attempting the launch, found
  `--operation build-continuous` was actually UNREACHABLE via the standard `python -m market_data_processing_service`
  CLI every launcher uses — `cli/main.py`'s `_build_legacy_argv` (the ServiceBootstrap→legacy-parser bridge) never
  threaded `--operation`/`--root` through at all, so every launch silently fell back to `process_candles_handler`
  regardless of intent. Fixed by adding `MDPS_OPERATION`/`MDPS_CONTINUOUS_ROOT`/`MDPS_ROLL_DAYS_BEFORE_EXPIRY` env-var
  bridges (`market-data-processing-service@4b96134`, full `quality-gates.sh` green + regression tests). While proving
  the fix locally against real prod GCS data (2020-02-04..06, root=ES, real ADC creds, dry-run), found + fixed TWO
  further live bugs in `_process_day_shard`'s empty/failed paths (same commit): `EmptyConfirmedReason.NO_DATA_FOR_DATE`
  does not exist (AttributeError) and `record_empty`/`record_failed` only accept shard-identity dims via `row_key`, not
  as top-level kwargs (TypeError) — every empty/failed build-continuous shard was silently dropping its honest-absence
  manifest row instead of recording one (2 new regression tests confirmed failing pre-fix, passing post-fix). Verified
  end-to-end locally: real continuous rows compute + real honest-absence rows record with valid manifest calls, no
  errors. No launcher existed for build-continuous (only process/backfill) — added
  `deployment-service/scripts/vm/launch-mdps-build-continuous-vm.sh` (`deployment-service@ab6a36b`, mirrors
  `launch-mdps-backfill-vm.sh`'s SPOT/tarball-pin/launch-params boilerplate, reuses the registered
  `mdps-backfill-tradfi-` VM name prefix). Launched prod VM `mdps-backfill-tradfi-buildcontinuous-es-20260726-082054`
  (`--root ES 2020-01-01..2026-07-25`, `LC_TARBALL_FRESHNESS=auto` confirmed tarball fresh @ `4b9613400a54`) —
  in-flight; will verify output lands at the canonical path, then launch features-delta-one-tradfi (existing
  `launch-features-vm.sh --feature-family delta_one --asset-group TRADFI`, no code change needed there per slot-6's fix)
  and confirm manifest rows before flipping this todo.
- 2026-07-26 (slot 3, todo 4 continued): THREE more real bugs found + fixed while actually landing the launch, each
  caught by watching the live VM rather than trusting a green launch log:
  1. **Tarball-SHA-pin race in the new launcher**: `launch-mdps-build-continuous-vm.sh` resolved
     `MDPS_TARBALL_SHA`/`UAC_TARBALL_SHA`/`UTL_TARBALL_SHA` via `lc_resolve_tarball_sha` BEFORE calling
     `lc_verify_tarball_freshness` (which auto-republishes a stale tarball) — so the VM metadata pinned whatever
     "latest" WAS before the republish. The first real launch auto-republished MDPS, printed "tarball fresh @
     4b9613400a54", but the VM downloaded and ran the STALE pre-fix code anyway (confirmed via
     `process_instrument_file`/`tbbo_15s` errors in the log — the OLD `process_candles_handler` path, not
     build-continuous). Killed the VM, fixed the ordering (resolve SHAs AFTER the freshness check) —
     `deployment-service@1eafa51`.
  2. **`record_captured` missing `source=`**: once dispatch was confirmed correct on relaunch, every REAL (non-dry-run)
     write failed with `MissingSourceError` — `(tradfi, ohlcv_1m)` is a multi-source `SOURCE_PRIORITY` cell (this
     validation only fires on real writes, which is why the earlier `--dry-run` local verification never caught it).
     Fixed via the same `resolve_candle_source_from_pipeline_mode` resolution the eager/streaming candle writers already
     use (`batch_databento` → `databento`) — `market-data-processing-service@9f615b4`.
  3. **`CONTINUOUS_FUTURE_WRITTEN` log_event bad kwarg**: passed `metadata=` where `log_event`'s real parameter is
     `details=` — this crashed AFTER `record_captured` had already written real data (confirmed: a genuine 72KB
     `ticks.parquet`, 1439 rows, landed for 2020-02-05), so the outer `except` then ALSO called `record_failed()` for
     the SAME shard, landing two conflicting manifest rows (`captured` row_count=1439 alongside `attempted_failed`
     row_count=0) in the prod per-VM manifest shard. Fixed in the same commit (`market-data-processing-service@9f615b4`,
     2 new regression tests, both confirmed failing pre-fix). The stale conflicting test-shard rows from the
     mid-diagnosis local verification run (`_index/per_vm/local-1319037-3517.parquet`) were left in place rather than
     deleted (prod-bucket deletes are human-only per codex) — they self-resolve because the manifest reader takes the
     LATEST `attempted_at` per shard key, and the real full VM run (below) reprocesses this same date with a later
     timestamp. Also hit and worked around a session-local issue (not a codebase bug): the `github-actions-deploy`
     gcloud account's WIF token expired mid-session ("job is already completed"), which made
     `gcloud compute instances describe` silently report `GONE` for a VM that was actually still `RUNNING` — switched
     the active account to `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` and hardened the watchdog
     to distinguish a real terminal VM state from an auth failure on the CHECKING side. Relaunched clean:
     `mdps-backfill-tradfi-buildcontinuous-es-20260726-084944` (`--root ES 2020-01-01..2026-07-25`, tarball fresh @
     `market-data-processing-service@4738ade8`) — in-flight as of this entry; next steps unchanged (verify output at the
     canonical path, launch features-delta-one-tradfi, confirm manifest rows, then flip this todo).
- 2026-07-26 (slot 3, todo 4 continued): a 4TH real bug on the SAME real VM run above — every real write failed with
  `record_captured: DataFrame missing required 'available_at' column`, reproduced across a wide span (2020-01-15,
  2021-01-04, 2021-03-21/23). Root cause: `apply_panama_canal_backadjust` only carries through whatever the per-contract
  INPUT candles happened to have, so a continuous series stitched from legacy per-contract parquets written before v9's
  `available_at` column existed inherited the gap, and `record_captured` hard-requires it. Killed the VM (widespread,
  not worth letting run partially-broken), fixed by stamping write-time via the same `_stamp_candle_available_at` the
  eager candle writer uses — `market-data-processing-service@e03e629` (new regression test asserts the captured
  DataFrame carries a fully-populated column; confirmed failing pre-fix). Before relaunching, spot-checked a wider
  spread locally (mid-June across 2020-2026 + a 2026-01 date): all clean, zero errors — the `total_rows=0` dates turned
  out to be genuine pre-existing per-contract data gaps (confirmed via GCS listing showing literally no objects for e.g.
  `day=2020-06-15/`), not a code bug, and correctly recorded as `empty_confirmed`. Relaunched clean:
  `mdps-backfill-tradfi-buildcontinuous-es-20260726-091215` (`--root ES 2020-01-01..2026-07-25`, tarball fresh @
  `market-data-processing-service@e03e6298d9ca`) — in-flight as of this entry. Running tally of bugs found+fixed while
  landing this ONE launch: CLI operation bridge unreachable, 2× manifest honest-absence signature mismatches, a launcher
  tarball-pin race, missing `source=`, a `log_event` bad kwarg, and this `available_at` gap — none of these were caught
  by the code's own test suite before this session; each was found by actually running the real pipeline against real
  prod data and watching it fail. Next steps unchanged (verify output at the canonical path, launch
  features-delta-one-tradfi, confirm manifest rows, then flip this todo).
- 2026-07-26 (slot 3, todo 4 continued): the relaunched VM (`...091215`) completed clean —
  `total_rows=1219168 days=2398 shards=16786`, zero errors, verified via direct GCS listing (2,222 real `ticks.parquet`
  objects at the canonical `instrument_type=continuous_future` path + the roll-schedule sidecar). Moved to the second
  half of this todo (launch features-delta-one-tradfi, confirm real feature parquets). Local `--dry-run` verification
  against real GCS data before committing to a full VM launch surfaced TWO MORE real, previously-undiscovered bugs —
  both in the same "24h vs 1d" timeframe-token family, one on the read side, one on the write side:
  1. **Features-service read side**: `OrchestrationService._load_continuous_series` passed delta_one's own timeframe
     vocabulary (`ALL_TIMEFRAMES`/`DEFAULT_TIMEFRAMES` use `"24h"` for daily bars) straight into
     `build_canonical_candle_path` with no normalisation, even though that function's own docstring (UTL
     `paths/registry.py`) requires the CALLER to pass `"1d"` ("timeframe is normalised (24h->1d) by the caller").
     `futures_basis` (a `TRADFI_ROLL_SENSITIVE_FEATURE_GROUPS` member) always needs a `"24h"` continuous read regardless
     of the CLI's `--timeframe` flag, so this fired on literally the first non-trivial test — a real, present shard read
     as absent because the read asked for `timeframe=24h` and MDPS writes daily bars under `timeframe=1d`. Fixed by
     normalising once at the top of `_load_continuous_series` (`features-service` — 1 new regression test in
     `test_orchestrator_continuous_read_path.py`, confirmed failing pre-fix).
  2. **MDPS write side — the deeper bug**: fixing #1 didn't resolve the absence, because MDPS build-continuous never
     actually wrote a `1d` (or `24h`) continuous shard for ES at all — confirmed via direct GCS listing:
     `instrument_type=continuous_future` exists at `timeframe∈{1m,5m,15m,1h}` for every checked day but at NEITHER
     `timeframe=1d` NOR `timeframe=24h`, even though `DEFAULT_TIMEFRAMES` includes `"24h"`. Root cause:
     `_process_day_shard`'s per-contract candle READ (`_load_per_contract_candles_for_day` → `candle_read_prefixes`)
     uses the SAME unnormalised `timeframe` value as the continuous-output WRITE (`_continuous_output_path`) — but the
     per-contract candle WRITER already normalises daily bars to `timeframe=1d`. So every `"24h"` shard's per-contract
     read found zero rows (0 objects under the literal `timeframe=24h` token) and silently wrote nothing via the
     existing empty-input handling, for every single day, for the entire already-completed ES production run. Fixed at
     the single funnel point in `run_build_continuous` (`market-data-processing-service`) — normalise the whole
     `_timeframes` list once, immediately after resolving `DEFAULT_TIMEFRAMES`, so every downstream use (read AND write)
     agrees with what the per-contract writer already persists under. 2 new regression tests in
     `test_build_continuous_engine.py` (`TestRunBuildContinuousTimeframeNormalisation`) confirm `"24h"` → `"1d"` before
     `_process_day_shard` is ever called, both failing pre-fix. `quality-gates.sh` running full-green verification on
     both repos before shipping. **Follow-up required after shipping**: the completed ES production build-continuous run
     needs a RE-LAUNCH (or a targeted `"1d"`-only re-run) to actually backfill the daily continuous shards this bug
     silently skipped for the whole 2020-2026 range — captured as this todo's next concrete action, not deferred to a
     separate issue since it's the direct blocker for `futures_basis`/verifying feature parquets land.
- 2026-07-26 (slot 3, todo 4 continued): shipped both fixes (`market-data-processing-service@3d26d7e`,
  `features-service@4d16023f`) and launched the targeted re-run
  (`launch-mdps-build-continuous-vm.sh --timeframes "24h" ES 2020-01-01 2026-07-25 full`). First launch attempt caught a
  REPEAT of the tarball-pin race (finding #1 above still applies to freshness-vs-resolve ordering at the CALLER level,
  not just inside the launcher) — the launcher printed "STALE tarball" warnings for both
  `market-data-processing-service` and `unified-api-contracts` but launched anyway (permissive default, no
  `LC_TARBALL_FRESHNESS` env set); killed the VM before it could run stale pre-fix code, republished both tarballs
  (`create-code-tarballs.sh`), relaunched with `LC_TARBALL_FRESHNESS=enforce` (confirmed
  `market-data-processing-service@3d26d7e12b30` fresh) — `mdps-backfill-tradfi-buildcontinuous-es-20260726-110048`. This
  run completed in ~2 minutes (`rc=0`) but with **`total_rows=0` across all 2398 days** — a FIFTH, deeper,
  previously-undiscovered bug, distinct from the timeframe-token normalisation just shipped:
  `panama_core.apply_panama_canal_backadjust` (+ `_close_on`, used by `extract_roll_events`) filtered per-contract rows
  via a naive `ts.dt.date() == active_date` comparison, but every MDPS candle is written
  `closed="right"`/`label="right"` (`fast_candle_aggregation.py`, deliberate + documented) — a bar's `timestamp` is its
  bin's END, not start. For a `"1d"` bar covering calendar day D this is ALWAYS midnight of `D+1` (confirmed on real
  prod data: the `day=2024-06-17` per-contract `1d` bundle's rows all carry `timestamp=2024-06-18`), so the
  date-equality check never matched a single-row-per-day daily bar, silently emptying `per_contract_today`'s
  date-filtered slice → `continuous.empty` → `record_empty(NO_INPUT_AVAILABLE)` for literally every shard. Sub-daily
  timeframes were never visibly broken by this because their far larger per-day row count means only the session's LAST
  bar hits the same edge (immaterial in a 1440-row day). Root-caused via direct real-data reproduction: confirmed the
  real `1d` per-contract candle file for `day=2024-06-17` legitimately contains 3 real ES contracts' rows (not a data
  gap), confirmed `_load_per_contract_candles_for_day` correctly finds/returns them (2 real contracts matched against
  the real `needed_contracts` set), then isolated the failure to `apply_panama_canal_backadjust`'s per-row date filter
  via a traced `_process_day_shard` call showing `per_contract_today` non-empty but `continuous.empty=True`. Fixed via a
  shared `_covered_date()` helper (`ts - 1 microsecond`, then `.dt.date()`) used by both `_close_on` and
  `apply_panama_canal_backadjust`'s date filter — correctly attributes a midnight-exact right-edge timestamp to the day
  it closes out. `market-data-processing-service`'s `tests/unit/test_panama_core.py`: fixed 2 pre-existing tests whose
  synthetic fixtures used same-day-midnight timestamps (the WRONG, pre-bug mental model) to instead use the real
  next-day-midnight convention (`_make_daily_candles` helper + 2 hand-rolled fixtures), added 1 new regression test
  pinned to the exact live-reproduced scenario; full `test_panama_core.py` + `test_build_continuous_engine.py` green (30
  passed). Locally re-verified via direct `_process_day_shard` call against real prod GCS data (`day=2024-06-17`,
  `timeframe=1d`): now returns 1 real row (was 0). `quality-gates.sh` running before shipping. **This is the SIXTH real,
  previously-undiscovered bug found while landing this one launch** (CLI operation bridge unreachable, 2× manifest
  honest-absence signature mismatches, a launcher tarball-pin race, missing `source=`, a `log_event` bad kwarg, an
  `available_at` gap, a 24h/1d timeframe-token mismatch on both read+write sides, and now this right-edge-timestamp
  date-filter bug) — underscoring that `build-continuous` had genuinely never produced a single correct row of ANY kind
  before this session, on ANY timeframe, until each of these was found by actually running the real pipeline against
  real prod data rather than trusting a passing test suite. Next: ship this fix, re-launch the targeted `"1d"` re-run,
  verify real continuous rows land, then proceed to the features-delta-one-tradfi launch this todo has been blocked on
  throughout.
- 2026-07-26 (slot 3, todo 4 continued): shipped `market-data-processing-service@e9edb39` and re-launched the targeted
  `"24h"` re-run — `mdps-backfill-tradfi-buildcontinuous-es-20260726-112134` completed clean,
  `total_rows=454 days=2398 shards=2398`, verified via direct GCS listing (287 real `timeframe=1d` continuous_future
  files for `2024-0*` alone) and parquet-content inspection (`close=5552.25` for `2024-06-18`-stamped ES-20240920,
  correctly matching the raw per-contract candle and carrying `active_contract_id`). MDPS's half of this todo is now
  genuinely, fully verified with real data. Moved to the features-delta-one-tradfi half. Launching the REAL production
  VM
  (`launch-features-vm.sh --feature-family delta_one --asset-group TRADFI --start-date 2020-01-01 --end-date 2026-07-25`)
  surfaced THREE MORE real, previously-undiscovered bugs, the last of which is arguably the actual root cause of this
  whole issue's original premise ("features-delta-one-tradfi has never successfully run"):
  1. **`--timeframe` CLI default is CEFI-only ("15s")**: `delta_one/cli/parser.py` defaults `--timeframe` to `"15s"`
     unconditionally — TradFi has no tick-level candle data at all (MDPS never writes it), so every TradFi launch
     without an explicit override tried "15s" first and the WHOLE feature group aborted on that single failure before
     any real timeframe was ever attempted. `launch-features-vm.sh` had no passthrough for this at all. Fixed by adding
     a `TIMEFRAME` env override to the launcher (`deployment-service@ca06015`, mirrors the existing
     `FEATURE_GROUP`/`INSTRUMENTS` pattern) plus using it (`TIMEFRAME=1m`).
  2. **`output_timeframes` also silently defaults to a CEFI-shaped ladder**: even with `--timeframe 1m` set, the BATCH
     loop separately iterates `output_timeframes` (config.py's `DEFAULT_TIMEFRAMES` — `15s/1m/5m/15m/1h/4h/24h` — since
     no `--output-timeframes` CLI flag is wired up anywhere in the codebase, `getattr(args, "output_timeframes", None)`
     is always `None`), so "15s" was STILL attempted first and STILL aborted the whole group. Fixed by adding
     `TRADFI_SUPPORTED_TIMEFRAMES = ["1m","5m","15m","1h","24h"]` (mirroring MDPS's `DEFAULT_TIMEFRAMES`) to
     `constants.py` and using it as the TRADFI-specific fallback in `_tf_cluster_helper.py._process_feature_group` —
     `features-service` (this + #3 below, same commit).
  3. **THE ROOT CAUSE — `buffer_days` never reaches the roll-sensitive short-circuit**: with #1+#2 fixed, every date
     STILL failed with "insufficient data" / NaN-threshold rejection, even for dates with hundreds of real prior days in
     GCS. Traced via a live-reproduced isolation: `process_feature_group_with_preloaded_candles` — the ONLY entry point
     the real batch pipeline ever calls (`_tf_cluster_helper.py`, both the single-date and date-range code paths) — had
     **no `buffer_days` parameter at all**, silently defaulting to `0` inside `_run_feature_group_lifecycle`.
     `TRADFI_ROLL_SENSITIVE_FEATURE_GROUPS`'s short-circuit in `_process_instrument` ignores `preloaded_candles`
     entirely and re-reads the persisted continuous series directly via `_load_continuous_series(..., buffer_days)`, so
     it ALWAYS read exactly 1 day of continuous history — regardless of the real, correctly-computed `max_buf` the
     TF-cluster mixin resolves for candle-LOADING purposes, and regardless of any `--lookback-buffer-days` CLI override
     (verified: passing 500 made zero difference to the observed "1/1 buffer day(s)" log line). This is the actual
     reason `futures_basis` (and by the same code path, `technical_indicators`/`momentum`) could never compute a real
     feature in this session until now, independent of every MDPS-side fix above. Fixed by adding `buffer_days: int = 0`
     to `process_feature_group_with_preloaded_candles` (threaded to `_run_feature_group_lifecycle`) and passing the
     already-computed `max_buf` at both `_tf_cluster_helper.py` call sites (`_process_tf_cluster` and
     `_process_one_date_for_cluster` — the latter needed a new `buffer_days` parameter threaded from
     `_process_tf_clusters_date_range`). Locally re-verified against real prod GCS data (`--skip-dependency-check`,
     `2024-06-17`): the `1h`-cluster output now genuinely succeeds —
     `Loaded persisted continuous series for ES/2024-06-17/1h: 259 rows from 14/86 buffer day(s)` (was 1/1), real
     features computed, "Wrote 1/1 daily partitions", a real manifest write logged. 5 new regression tests across
     `test_tf_cluster_helper.py` (3) and `test_orchestrator_continuous_read_path.py` (1) + `constants.py` fallback
     coverage; full `test_tf_cluster_helper.py`
     - `test_orchestrator_continuous_read_path.py` green (69 passed), full `tests/delta_one/` green modulo one confirmed
       PRE-EXISTING, unrelated failure (`test_get_output_bucket_formats_correctly`, fails identically on a clean
       `git stash` — DEFI bucket-naming, nothing to do with this fix). `quality-gates.sh` running before shipping. **Two
       remaining, DISTINCT, NOT-yet-fixed gaps found along the way — documented here for operator visibility rather than
       chased further in this already-large session (per the "big finding" triage rule)**:
  - **`24h`/`1d` sub-timeframe still has sparse real coverage**: even with buffer_days correctly threaded, the
    `1d`-continuous read for the SAME 86-day window only found 14/86 real days (vs. 1h's 259 rows/14 real days — same 14
    real days, just far fewer bars each). The just-shipped MDPS re-run only produced `total_rows=454` across `days=2398`
    (a ~19% hit rate) — genuinely sparse, not an artifact of this session's fixes. Given `futures_basis`'s rolling
    features need real CONSECUTIVE daily history, this sparsity means the `24h` output specifically may keep failing its
    NaN-threshold check even now, while `1h` (and likely `1m`/`5m`/`15m`) succeed cleanly. Root cause not yet
    investigated — likely a `build_active_contracts_table`/`extract_roll_events` gap specific to daily granularity's
    single-bar-per-contract-per-day nature (no redundancy the way 1440 intraday bars provide). Needs a dedicated
    investigation, not a same-session patch.
  - **Per-day loop aborts on the FIRST date's failure, not just-that-day**: `_process_tf_clusters_date_range`'s per-date
    loop (`if not ok: return False`) stops the ENTIRE multi-day range on the first day that fails for ANY reason —
    including a genuine, expected absence (e.g. 2020-01-01 is New Year's Day, a market holiday with zero real
    per-contract data). This is not roll-sensitive-specific; it affects any feature-group batch run. A real multi-year
    backfill will always eventually hit a holiday/weekend gap, so this needs shard-level (per-date) isolation — matching
    the codebase's own stated `/codex/04-architecture/shard-level-failure-isolation.md` principle — rather than today's
    fail-fast semantics. Not fixed this session (a real, separate, non-roll-sensitive-specific gap); worked around for
    verification by targeting a single known-good date instead of a multi-year range. **Running tally: NINE real,
    previously-undiscovered bugs found and fixed while landing this ONE todo** (MDPS: CLI operation bridge, 2× manifest
    signature mismatches, launcher tarball-pin race, missing `source=`, `log_event` bad kwarg, `available_at` gap,
    24h/1d write-side token mismatch, right-edge date-filter; features-service/deployment- service: 24h/1d read-side
    token mismatch, CLI `--timeframe` CEFI default, `output_timeframes` CEFI default, `buffer_days` never threaded to
    the roll-sensitive short-circuit) — none caught by the existing test suite before this session; every one found by
    actually running the real pipeline against real prod data. Next: ship, then launch one more real production VM for a
    realistic single-day/date window, verify real feature parquets + manifest rows land for at least the working
    timeframes (1h et al.), and flip this todo's checkbox with full evidence.
- 2026-07-26 (slot 3, todo 4 continued): shipped `features-service@2e7c2ca1` (buffer_days threading — the root-cause
  fix; also folds in the `--timeframe`/`output_timeframes` CEFI-default fixes, same commit) after fixing a function-size
  QG violation (extracted `_default_output_timeframes()` as a module-level helper in `_tf_cluster_helper.py`). Full
  `quality-gates.sh` green (exit 0; a transient interleaved `[FAIL]` block for an UNRELATED repo —
  `market-tick-data-service` contract-call baseline — appeared in one run's tail output but did not affect this repo's
  exit code, confirmed by a clean standalone re-run). `quickmerge` landed clean: `094a8b43..2e7c2ca1`. Added the two
  DISTINCT remaining gaps (24h/1d sparse coverage; per-date abort-on-first- failure) as tracked P1 todos above rather
  than leaving them as un-tracked prose, per the workspace rule that every deferral in a summary must already be a
  `- [ ]` todo.
- 2026-07-26 (slot 4): Fixed the per-date abort-on-first-failure gap (this doc's last open P1 todo).
  `features-service@81ab1264`, full `quality-gates.sh` green. See the flipped checkbox above for the fix detail; removed
  the now-redundant "New P1 todo" deferred-work row (superseded by the checkbox, which already carries the same fix).

## Deferred work after 2026-07-26

| Item                                                                                              | State / why deferred                                                                                                                                                                                                                                                                                                                                                                                                                  | Blocked on                                        |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| Todo 4 (this file, P0) — real features-delta-one-tradfi production launch + manifest verification | Not done — all blocking code bugs are now fixed and shipped (9 real bugs across market-data-processing-service, features-service, deployment-service); next session should launch a REAL production VM for a realistic single-day/narrow-range window (avoid 2020-01-01 — a market holiday with zero data, which would hit the untracked-until-now per-date abort-on-first-failure gap) and verify real parquets + manifest rows land | Nobody — pick up directly, no external dependency |
| New P1 todo — MDPS `24h`/`1d` sparse coverage investigation                                       | Not done — needs a dedicated GCS gap analysis, not chased this session (time-boxed per the "big finding" triage rule)                                                                                                                                                                                                                                                                                                                 | Nobody — real work, needs its own session         |

**Recommended next item**: todo 4 (P0) — launch the real production VM for a single realistic date (e.g. a 2024 weekday
already confirmed to have real MDPS continuous data, such as `2024-06-17`) with `TIMEFRAME=1m` set on the launcher, then
verify via direct GCS listing + manifest read that real feature parquet rows landed for at least the `1h` output. This
is the last remaining step to close this issue's original premise.
