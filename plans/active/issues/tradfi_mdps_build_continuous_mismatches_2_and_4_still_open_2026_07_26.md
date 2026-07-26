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

- [ ] [AGENT] P1. Fix mismatch 2 (filename format): either change `panama_core.contract_id_for_expiry` to emit the
      short-symbol form MDPS actually writes, or change MDPS's process-step filename builder to emit the Databento
      date-format `contract_id_for_expiry` produces -- pick ONE canonical form and make both sides agree (per the
      archived doc's own "Cleaner Option B variant" suggestion). (repo: market-data-processing-service)
- [ ] [AGENT] P1. Fix mismatch 4 (read-path handling): add `continuous_future` handling to
      `features_service/delta_one/app/core/data_loader.py`'s `_DERIVATIVE_DATA_TYPES` (or an equivalent dedicated
      branch) so `_build_blob_path` can locate build-continuous's
      `processed_candles/.../instrument_type=continuous_future/venue=CME/underlying=ES/ticks.parquet` output. (repo:
      features-service)
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
