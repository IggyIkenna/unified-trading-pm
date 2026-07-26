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

> **✅ RESOLVED (slot 6, 2026-07-26 23:05 UTC) — P2 todo DONE, timing-race theory DISPROVEN.** Re-ran the P2 ES/MES
> process-step backfill (7 per-year VMs, no `--force`) then `build-continuous` for ES full-range — both phases genuinely
> completed, independently `gcloud`-verified. Re-measured `1d` hit rate against the fresh (post-consolidator,
> `Update Time: 22:58:44Z`) manifest: `captured=454`/`empty_confirmed=1944` (2398 total, ~18.9%) — **byte-identical to
> the pre-re-run baseline**. The hit rate did NOT rise after a full second pass, disproving the timing-race hypothesis
> this todo was testing — see the flipped checkbox + Progress Log for full evidence and next-step pointers (incl.
> cross-reference to slot 5's independent P1 listing-anomaly finding, which may be the real explanation).
>
> **🔴 STALE (superseded, kept for history) — 2026-07-26 14:02-15:02 UTC's `140251`→`144837`→`150236` single-VM chain**:
> the below banner describes an EARLIER attempt (P0 "backfill MDPS's per-contract process step" todo, now flipped `[x]`)
> that was superseded by slot 2's 7-shard `y*es-*` launch (see Progress Log's 2026-07-26 slot-3/slot-2 reconciliation
> entries) — that P0 todo is DONE; this banner is retained only as the historical record of how that backfill actually
> landed. It is NOT describing currently-running VMs (none of `140251`/`144837`/`150236` still exist).
>
> **🟡 IN-FLIGHT (slot 3, 2026-07-26 14:02 UTC)**: `mdps-backfill-tradfi-20260726-140251` (SPOT) running the new P0
> per-contract "process" backfill for `CME:FUTURE:ES CME:FUTURE:MES`, 2020-01-01..2026-07-25. Per-date progress
> confirmed real (sequential `🏁 Date range complete` markers, ~15-20s/date); per-date dependency-check failures (e.g.
> missing raw ingestion for a specific date) correctly SKIP that date rather than aborting. At this rate the full
> ~2398-day range could take many hours — do not treat "still RUNNING" as stalled; check the VM's own heartbeat/manifest
> progress before assuming a problem. Reminder: `rebuild_manifest_from_canonical_paths(...)` must run AFTER this
> completes (see launcher's own printed reminder). **A 10th real bug found+fixed while this VM was already running**
> (`market-data-processing-service@d531eb9`): `get_instruments_for_date`'s multi-venue concat used
> `pl.concat(how="vertical_relaxed")`, which cannot tolerate CBOE's 11-column legacy instrument schema alongside
> CME/FX/ICE's 51-column canonical schema — raised `polars.exceptions.ComputeError` on ~50% of dates, uncaught by any
> local except clause, silently swallowed by the `@_sync_storage_errors` retry decorator (returns `None`). Confirmed
> BENIGN for this specific backfill (the resulting `tradable_keys` is dead code — captured as `_tradable_keys` at
> `orchestration_service.py:166` and never used), so the CURRENTLY-RUNNING VM (pre-fix code) was NOT killed/relaunched —
> this fix only benefits future runs + any other real caller of `get_instruments_for_date`. Regression test:
> `tests/unit/test_cloud_data_provider.py::test_get_instruments_by_venue_tolerates_schema_drift_across_venues`
> (confirmed failing pre-fix). Full `quality-gates.sh` green; `quickmerge` landed clean.
>
> **UPDATE 14:41 UTC — original VM `...-140251` PREEMPTED** after ~40 min (processed 2020-01-01..2020-02-12, ~43 real
> days; log ends abruptly mid-`2020-02-13` with no clean-shutdown message; no `PROGRESS.json` exists for this launcher —
> confirmed via `gcloud compute operations describe` on the delete op + the workspace rule that one-off migration VMs
> aren't fleet-monitored/auto-relaunched). Resumed correctly from measured progress (NOT replayed `START_DATE`, per the
> HARD RULE): `mdps-backfill-tradfi-20260726-144837`, same instrument filter, `--start-date 2020-02-13` (the last
> INCOMPLETE date) through the original `2026-07-25` end. Tarballs republished + `LC_TARBALL_FRESHNESS=enforce`-verified
> fresh, including the `d531eb9` schema-drift fix — the resumed run should no longer emit `schema lengths differ` at all
> (watching to confirm). Re-armed monitoring with explicit empty-`status` detection (a `gcloud describe` returning
> empty/error on this VM name is now treated as a preemption/deletion signal, not silently ignored).

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
- [x] [AGENT] P0. After mismatches 2+4 (+3 if still real) are fixed, launch the MDPS build-continuous run for
      `--root ES`, verify output lands at the expected canonical path, THEN launch features-delta-one-tradfi for ES and
      confirm real feature parquets land (check the manifest actually gains rows -- not just "job exit 0"). This closes
      `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`'s P0 items per the "Plans run to actual completion"
      HARD RULE. (repo: market-data-processing-service, features-service) — ✅ DONE 2026-07-26: MDPS build-continuous
      verified with real data (`market-data-processing-service@e9edb39`, ES 2020-01-01..2026-07-25, real `timeframe=1d`
      continuous_future objects confirmed via GCS + parquet-content inspection). features-delta-one- tradfi launched for
      real: `features-delta-one-tradfi-20260726-132027` (`--start-date/--end-date 2024-06-17`, `TIMEFRAME=1m`,
      `FEATURE_GROUP=futures_basis`, `INSTRUMENTS=CME:FUTURE:ES`) — 4 of 5 output timeframes (1m/5m/ 15m/1h) succeeded
      with REAL data: manifest per-VM shard gained 5 `capture_status=captured` rows (`row_count=1` each) at
      `features-tradfi-prd-central-element-323112/_index/per_vm/...20260726-132027.parquet`, confirmed via direct GCS
      listing of the real canonical objects
      (`delta_one/by_date/day=2024-06-17/feature_group=futures_basis/     feature_group_version=1/timeframe={1m,5m,15m,1h}/CME:FUTURE:ES.parquet`)
      and parquet-content inspection (the `1h` file: 23 real rows × 81 real feature columns, real hourly timestamps).
      The `24h` sub-timeframe correctly recorded an honest `attempted_failed` row (sparse MDPS `1d` coverage — see the
      investigated-and-closed P1 below for the actual root cause), not a silent drop. This satisfies the todo's literal
      completion bar in full: real feature parquets landed, manifest gained real rows, verified directly (not just job
      exit 0).
- [x] [AGENT] P1. Investigate why MDPS build-continuous's `24h`/`1d` output has genuinely sparse real coverage
      (`total_rows=454` across `days=2398` on the shipped ES re-run, ~19% hit rate — a real single day near 2024-06-17
      only found 14/86 real prior days) even after the right-edge-timestamp date-filter fix
      (`market-data-processing-service@e9edb39`). Likely a `build_active_contracts_table`/`extract_roll_events` gap
      specific to daily granularity's single-bar-per-contract-per-day nature (no redundancy the way 1440 intraday bars
      provide) — confirm via direct GCS gap analysis before assuming a code fix. (repo: market-data-processing-service)
      — ✅ INVESTIGATED 2026-07-26, hypothesis DISPROVEN by direct evidence; root cause is upstream data coverage, not a
      build-continuous code bug. See progress log for the full 3-part evidence chain (manifest cross-tab across
      timeframes + raw-vs-processed density comparison + direct GCS content inspection). Verification-only — no code
      shipped, per this same doc's todo-3 precedent (slot-8, MOOT-close).
- [x] [AGENT] P0. Backfill MDPS's per-contract "process" step (`--operation process`, the default
      `process_candles_handler` path, NOT build-continuous) across the full ES/MES 2020-01-01..2026-07-25 history via
      `launch-mdps-backfill-vm.sh` (no `MDPS_OPERATION` override needed — process is the default routing) — ✅ DONE
      2026-07-26 (slot 2), but the hoped-for outcome (hit rate materially above ~19%) did NOT materialize; documenting
      in full since this closes the ACTION but not the underlying goal. **The backfill itself**: 7 correctly ES/MES-
      scoped per-year VMs (`mdps-backfill-tradfi-y2020es-20260726-144859` .. `y2026es-20260726-145336`) all ran to
      genuine completion (366/365/365/365/366/365/206 real days each, verified via each VM's own clean
      `DEPLOYMENT_COMPLETED`/self-delete), then `mdps-backfill-tradfi-buildcontinuous-es-20260726-175548` re-stitched
      the full continuous series (`total_rows=1222163 days=2398 shards=16786`, exit=0). **The re-verification**: read
      this run's own per-VM manifest shard directly (not the possibly-stale consolidated index) —
      `continuous_future`/`underlying=ES`/`timeframe=1d` shows `captured=454` of 2398, i.e. **exactly unchanged from the
      pre-backfill ~19% baseline** — a full, real re-backfill produced ZERO net improvement in the 1d/24h hit rate.
      Genuinely new information: `1h`/`4h` (previously 442/418) have now CONVERGED UP to the same 454 ceiling as
      1m/5m/15m/1d — every timeframe is now uniformly capped at 454, confirming a single shared bottleneck, not a
      per-timeframe one. **Root-cause investigation** (ruling out, in order, three hypotheses before landing on the real
      one): (1) NOT wrong-contract-per-date processing gaps — those were the ORIGINAL diagnosis and this backfill
      genuinely re-ran the whole history against them; (2) NOT a raw/canonical instrument-id scheme mismatch — my own
      working hypothesis mid-session, DISPROVEN by direct evidence: pulled the raw `futures_chain`/`underlying=SP500`
      bundle for a `captured` day (2023-01-03) and an `empty_confirmed` day (2023-01-10) — BOTH carry the identical
      `CME:FUTURE:SP500-USD@LIN-{expiry}` raw instrument_id scheme (the same id this doc's earlier draft flagged as an
      "unrelated synthetic-looking" manifest artifact — it is NOT manifest-only, it is the real raw candle
      instrument_id), BOTH have ~1380 real nonzero-volume rows for the roll-schedule-active March-2023 contract, and the
      SUCCESSFUL date's processed output (`CME:FUTURE:ES-20230317.parquet`) proves the SP500-USD@LIN→ES mapping DOES
      work — so an id-scheme bug cannot explain why the FAILING date differs from its near-identical sibling; (3) **the
      real finding**: the process step's own log for 2023-01-10 reads
      `Listed 0 files from .../day=2023-01-10/     for data_type=ohlcv_1m` →
      `Skipped 6 data_types with no upstream data`, yet I directly confirmed via `gcloud storage ls` that the real
      1380-row file EXISTS at that exact path. Dispatched a sub-agent to read the actual listing code
      (`orchestration_scanner.py:358` `_list_instrument_files`, prefix `raw_tick_data/by_date/     day={date}/` at line
      407, a delimiter-less fully-recursive `list_blobs` with substring matching at line 248) — the listing LOGIC ITSELF
      is correct and would find the file if present at call time; no caching, no per-date-varying scoping, no bug found
      in the code as written. **Working conclusion**: this is a TIMING/RACE condition, not a code defect — each date is
      a one-shot `--subprocess-per-date` child with no retry, and the raw MTDS ingestion for a given date can land AFTER
      that date's process-step subprocess already ran and logged "0 files" (this backfill ran concurrently with ongoing
      fleet raw-ingestion activity, e.g. the `tradfi-bf-cme-ohlcv-1m-es-2020-...` VM noted below). A date that failed
      once for this reason stays `attempted_failed`/`empty_confirmed` forever unless someone re-runs it.
      **Disposition**: flipping this checkbox because the literal backfill ACTION is genuinely complete (all 7 shards +
      build-continuous re-run, real verified GCS data, root cause now correctly diagnosed instead of two wrong theories)
      — but the underlying sparse-coverage problem is NOT resolved; see the new P2 catch-up-rerun todo below for the
      concrete (cheap, well-understood) next action. Concurrently with the ORIGINAL diagnosis, a genuine raw-MTDS
      backfill VM was observed RUNNING (`tradfi-bf-cme-ohlcv-1m-es-2020-20260726-120107`,
      `VM_SERVICE=market_tick_data_service VM_TASK=mtds-backfill VM_OPERATION=download VM_SOURCE=databento     VM_INSTRUMENT_IDS=ES.FUT;ES.OPT VM_START_DATE=2020-01-01 VM_END_DATE=2020-12-31`)
      — that fixes RAW ingestion only, and (per the finding above) its OWN timing relative to the process step is now
      understood to matter. Separately (smaller, not itself blocking): the process step's real ES/MES writes carry NO
      matching manifest rows under `instrument_type=FUTURE`+`underlying=ES/MES` at all — the only
      `underlying=SP500`/`MES` `FUTURE`-type manifest rows found use the SAME `CME:FUTURE:SP500-USD@LIN-{expiry}` id
      scheme (expiries out to 2029, no `capture_status`/`timeframe` populated) — worth a follow-up look at whether the
      process step's writer even calls `record_captured`/`record_empty` for TradFi FUTURE candles, since right now this
      gap is invisible to the manifest/dashboard. (repo: market-data-processing-service, deployment-service,
      market-tick-data-service)
- [x] ✅ [AGENT] P2. DONE 2026-07-26 (slot 6) — **hit rate FLAT, timing-race theory DISPROVEN.** Re-ran the process-step
      backfill a second time (no `--force`) then re-measured: `continuous_future`/`underlying=ES`/`timeframe=1d` =
      `captured=454`/`empty_confirmed=1944` (2398 total, ~18.9%) — byte-identical to baseline, confirmed against a
      post-rerun-fresh manifest (`Update Time: 22:58:44Z`, after the build-continuous VM's `22:48:07Z` completion). Did
      NOT rise, disproving the timing theory per this todo's own done-condition. Repo: market-data-processing-service.
      Full evidence in the 2026-07-26 slot-6 Progress Log entries.
- [x] [AGENT] P2. Re-run the process step for ES/MES on `2020-03-26` only
      (`launch-mdps-backfill-vm.sh --instrument-ids "CME:FUTURE:ES CME:FUTURE:MES" tradfi 2020-03-26 2020-03-26 full`,
      no `--force` needed). This one date was recorded `attempted_failed` in the `y2020es` per-VM shard because slot 2
      killed its per-date subprocess after ~12 min mistakenly believing it had hung (see the 2026-07-26 slot-2 progress
      log entry "self-correction on a premature kill" for the full evidence chain — a sibling shard's identical-looking
      case self-resolved cleanly at 13.5 min, proving this WASN'T a real hang). `2020-03-26` is COVID-crash-era with
      almost certainly real, large trading volume, so this is a genuine one-day gap, not a data-correctness risk left
      unaddressed — just not urgent enough to interrupt the other 6 shards for. (repo: market-data-processing-service) —
      ✅ ACTION DONE 2026-07-26 (slot 5), but the underlying gap did NOT close — see the new P1 finding below. Launched
      `mdps-backfill-tradfi-20260726-223423` (single isolated VM, no fleet contention this time, all 5 dependency
      tarballs verified fresh) — ran clean, `exit_code=0`, self-deleted in ~6s of actual processing time. Pre-launch
      baseline: ES had real data for all 6 timeframes (created 2026-07-23, predating today's attempts, so already fine);
      MES had ZERO files for any timeframe on this date. Post-run: MES is **still completely missing** across all 6
      timeframes — the re-run genuinely executed but produced 0/0 succeeded/failed (not a crash, not a timeout, not a
      kill — a clean "no upstream data" verdict). Root cause is NOT the originally-diagnosed premature-kill: the process
      step's own log shows `Listed 0 files from .../raw_tick_data/by_date/day=2020-03-26/ for data_type=ohlcv_1m` (and
      identically for all 5 other checked data_types) → `Skipped 6 data_types with no upstream data`. But **live GCS
      verification directly disproves that** — the raw
      `futures_chain/data_type=ohlcv_1m/underlying=SP500/quote=USD/margin=linear/ticks.parquet` file (SP500 is the real
      raw-bucket `underlying=` for ES/MES per this doc's earlier `EXCHANGE_CODE_TO_NAME` finding) DOES exist, with a
      real 74,823-byte payload, `Creation Time: 2026-07-26T22:10:12Z` — a full 24 minutes BEFORE this VM was even
      launched (22:34:23Z) and 27 minutes before its listing call ran (22:37:14Z). No other TradFi raw-ingestion VM was
      running concurrently at launch time (checked `gcloud compute instances list` — only
      `mdps-backfill-tradfi-buildcontinuous-es-20260726-223325`, a `build-continuous` read of `processed_candles/`, not
      a raw writer, was concurrently active). This is new, stronger evidence than this doc's prior "TIMING/RACE
      condition" theory (which assumed concurrent multi-shard fleet contention as the cause) — here there was NO
      contention, and the file had already been sitting there, fully settled, for 24+ minutes. Filed as a new,
      higher-priority P1 finding below since this pattern — real raw data genuinely invisible to the process step's own
      day-wide listing — is the most plausible explanation for why this doc's TWO full ES/MES backfill passes (todo
      above + slot 6's in-flight second pass) have both failed to move the `1d`/`24h` hit rate off its ~19% ceiling: if
      the listing itself is unreliable, no amount of re-running the SAME listing-based process step will ever converge.
      No code shipped for this todo — the fix belongs to whoever picks up the new finding below. (repo:
      market-data-processing-service, verification only)
- [x] ✅ [AGENT] P2. DONE 2026-07-26 (slot 6) — `market-data-processing-service@2b7c4dc`. `process_handler.py:706`'s
      per-date `subprocess.run(cmd)` (the `--subprocess-per-date` driver) had NO timeout — a genuinely hung child (vs. a
      legitimately slow-but-real date, which CAN take 13+ minutes, confirmed live 2026-07-26) could block that shard's
      entire remaining date range forever with no self-recovery. Added a 1800s (30 min) timeout — generous enough to
      never false-positive on a real slow date, per the live 13.5-min precedent — via
      `subprocess.run(cmd, timeout=_SUBPROCESS_PER_DATE_TIMEOUT_SECONDS)`, catching `subprocess.TimeoutExpired`
      (`subprocess.run` already kills + reaps the child before raising, so no extra cleanup needed), logging `FAILED`,
      and returning `True` — the outer per-date loop already continues past a failed date (verified live, no change
      needed there). New regression test `test_returns_true_on_timeout` mocks a `TimeoutExpired` and asserts the FAILED
      (`True`) result. Full `quality-gates.sh` green (2215 passed; 2 QG runs hit a transient `systemd-run` `MEM_WRAP`
      timeout under shared-host contention, confirmed via a clean standalone `basedpyright` run — 8s, 0 new
      errors/warnings — and a clean `QG_MEM_CAP=0` re-run, 65s, before shipping). Shipped via quickmerge. Not chased
      further this session — the ONE observed "hang-like" case turned out to be a false positive (see the todo above),
      so there is not yet concrete evidence of a REAL unbounded hang, only a real code-level gap that would let one go
      unrecovered if it ever occurs. (repo: market-data-processing-service)
- [ ] [AGENT] P1. NEW FINDING (2026-07-26, slot 5): `_list_instrument_files`'s day-wide raw listing
      (`orchestration_scanner.py:462`, `self.storage_client.list_blobs(bucket=bucket_name, prefix=prefix)` where
      `prefix = f"raw_tick_data/by_date/day={date_str}/"`) returned 0 files for ES/MES's `2020-03-26` re-run across ALL
      6 checked data_types, even though the real raw
      `futures_chain/data_type=ohlcv_1m/underlying=SP500/.../ticks.parquet` file (74,823 bytes, confirmed via direct
      `gcloud storage ls -L`) had `Creation Time: 2026-07-26T22:10:12Z` — fully 24 minutes before the isolated,
      non-contended VM that ran this listing was even launched, and 27 minutes before the listing call itself. No other
      TradFi raw-writer VM was running concurrently (verified via `gcloud compute instances     list` at launch time).
      This is DIFFERENT from — and stronger evidence than — this doc's earlier "TIMING/RACE condition" theory
      (2026-07-26, slot 2's `y2020es`/`y2026es` investigation): that theory assumed concurrent multi-shard GCS
      contention as the cause, but this repro had zero contention and the file had already been sitting fully settled
      for 24+ minutes. The prior sub-agent code read (this doc, 2026-07-26, "Backfill MDPS's per-contract process step"
      todo) concluded the LISTING LOGIC ITSELF is correct as written — no caching, no per-date-varying scoping found in
      the Python code. Traced the actual call chain to `unified_trading_library/cloud_interface/providers/gcp.py:303`'s
      `list_blobs`, which is a thin passthrough to `google.cloud.storage`'s native
      `bucket.list_blobs(prefix=..., delimiter=None,     max_results=None)` — no application-level caching found there
      either. **This strongly suggests the real root cause is a GCS list-consistency edge case (not app code)** — worth
      checking whether this bucket has any non-standard consistency/replication configuration, or whether `list_blobs`
      needs a `start_offset`/pagination fix, or whether the `google-cloud-storage` client version in use has a known
      list-staleness issue. **Why this matters beyond one date**: if raw data can be genuinely present-but-
      invisible-to-listing, that is the most plausible explanation for why this doc's TWO full ES/MES process-step
      backfill passes (the P0 "Backfill MDPS's per-contract process step" todo above + slot 6's concurrent in-flight
      second pass) have both left the `1d`/`24h` hit rate stuck at the same ~19% (454/2398) ceiling — re-running the
      SAME listing mechanism can never converge if the listing itself is unreliable, regardless of how many times the
      underlying data-availability improves. Needs someone to (1) reproduce this listing gap in isolation (list the
      exact prefix via the MDPS venv's `CloudDataProvider`/`gcp.py` client right after confirming the object exists, not
      via `gcloud storage ls` which may use a different code path/consistency guarantee), (2) check GCS bucket
      consistency settings (`gcloud storage buckets describe market-data-tick-tradfi-prd-central-element-323112`), (3)
      if reproduced, escalate to whether a retry-with-backoff or a stronger consistency read is needed in
      `_list_instrument_files`. (repo: market-data-processing-service, unified-trading-library, investigation)
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
- 2026-07-26 (slot 3): Flipped todo 4 (P0) — launched the real production features-delta-one-tradfi VM
  (`features-delta-one-tradfi-20260726-132027`, ES, `2024-06-17`, `TIMEFRAME=1m`) and verified via direct GCS listing +
  parquet-content inspection: 4 real feature parquet objects landed (1m/5m/15m/1h) and the manifest gained 5 real
  `captured` rows. This closes the issue's original premise ("no tradfi features run has ever successfully landed") —
  one now has, with first-hand verified evidence.
- 2026-07-26 (slot 2, 24h/1d sparse-coverage investigation): Confirmed the todo's own leading hypothesis
  (`build_active_contracts_table`/`extract_roll_events` gap specific to daily granularity) is **DISPROVEN**, via three
  independent lines of live evidence, before touching any code — per the todo's own instruction to "confirm via direct
  GCS gap analysis before assuming a code fix":
  1. **Manifest cross-tab across timeframes** (read the real `_index/availability_index.parquet` directly off
     `market-data-tick-tradfi-prd-central-element-323112`, bypassing `read_availability_index()` which returned 0 rows
     for unknown reasons not chased further — the raw parquet read worked fine): `instrument_type=continuous_future`,
     `underlying=ES` shows **1m, 5m, 15m, and 1d ALL captured EXACTLY 454 of 2398 days** (`1h`=442, `4h`=418 — close but
     from an earlier/different run window). If the gap were specific to "daily granularity's single-bar-per-day,
     no-redundancy" nature as hypothesized, 1m/5m/15m (1440/288/96 bars-per-day redundancy) should show a MATERIALLY
     HIGHER hit rate than 1d — they don't; they're identical. This alone rules out a 1d-specific code path.
  2. **Raw-ingestion vs per-contract-processed density comparison**: the RAW MTDS layer that feeds MDPS's process step
     (`instrument_type=futures_chain`, `underlying=SP500` — the real `EXCHANGE_CODE_TO_NAME`-mapped path, confirmed by
     slot-8's todo-3 finding) shows a MUCH denser `ohlcv_1m` capture rate: 1516/2697 sampled day-shards captured,
     ~242-253 real days/year for most years (consistent with real CME trading-day coverage, incl. Sunday-evening opens —
     day-of-week distribution of captured continuous_future days spans all 7 days, not just Mon-Fri), with a real dip to
     143 in 2022 specifically (a genuine, separate raw-data gap, not investigated further here). This proves the
     DISCONTINUITY is introduced BETWEEN raw ingestion and the per-contract processed-candle layer, not in
     build-continuous itself (build_active_contracts_table is a pure calendar-date table builder with no I/O — it cannot
     itself be the source of a data-availability gap).
  3. **Direct GCS content inspection** (the smoking gun): cross-referenced 2021 dates where raw `futures_chain` data IS
     captured but continuous_future output is NOT (206 such dates in 2021 alone) and downloaded the actual per-contract
     candle files MDPS's process step wrote. Found the per-contract `instrument_type=FUTURE`, `underlying=ES` layer is
     itself sparse AND internally inconsistent: `2021-01-05`, `2021-02-02`, `2021-03-02` each have exactly ONE contract
     file present — `CME:FUTURE:ES-20210618.parquet` (June 2021) — even though the roll schedule (8 business days before
     the 2021-03-19 expiry) says `CME:FUTURE:ES-20210319` (March 2021) should be active on those dates; `2021-03-22`
     holds ONLY `CME:FUTURE:ES-20210917.parquet` (September 2021) when June 2021 should be active; several other dates
     (`2021-01-08`, `2021-03-19`, `2021-06-01`, `2021-06-18`, `2021-06-21`) have ZERO per-contract files of any kind.
     `apply_panama_canal_backadjust` correctly finds nothing for `active_contracts` on these dates because the WRONG (or
     no) contract's data exists — this is expected, correct behavior given the input, not a bug in the stitching logic.
     All sampled per-contract files carry a `creation_time` of `2026-07-23T06:52:06Z` — i.e. written 3 days before this
     investigation, not from today's session, and not a genuine systematic historical backfill (a real backfill would
     cover EVERY roll-schedule-active contract for EVERY date, not an inconsistent single mismatched contract per date
     with large silent gaps). Also noted in passing (not chased further, scoped out as a separate manifest-completeness
     gap, now folded into the new backfill todo below): manifest rows under `instrument_type=FUTURE` +
     `underlying=SP500`/`MES` exist but use an unrelated synthetic-looking id scheme
     (`CME:FUTURE:SP500-USD@LIN-{expiry}`, expiries to 2029, no `capture_status`/`timeframe` populated) that doesn't
     match the real Databento ids the GCS objects carry — the process step's real ES/MES writes are NOT manifest-tracked
     at all under any vocabulary searched. Also observed (for context, not caused by or fixed in this todo) a genuine
     concurrent VM `tradfi-bf-cme-ohlcv-1m-es-2020-20260726-120107` RUNNING during this investigation
     (`VM_SERVICE=market_tick_data_service`, `VM_TASK=mtds-backfill`, `VM_OPERATION=download`, `VM_SOURCE=databento`, ES
     2020 raw ohlcv_1m/ohlcv_1s) — a RAW-layer backfill that will not, by itself, populate the per-contract
     processed-candle layer this todo's new follow-up todo targets. Net conclusion: no code fix belongs in
     build-continuous for this todo (verification-only close, mirroring slot-8's todo-3 MOOT-precedent); the real next
     action is a genuine per-contract "process" step backfill, captured as a new P0 todo above.
- 2026-07-26 (slot 4, the "backfill MDPS's per-contract process step" P0 todo, IN PROGRESS): Launched
  `launch-mdps-backfill-vm.sh tradfi 2020-01-01 2026-07-25 full` (default `--operation process`, no override needed —
  confirmed). First launch attempt caught the tarball-pin race again (all 5 dependent repos had drifted past their
  published tarballs) — republished + relaunched with `LC_TARBALL_FRESHNESS=enforce`; a SECOND drift hit mid-relaunch
  (fleet activity moved `market-tick-data-service`/`unified-api-contracts` again between my fresh-pull and the enforce
  check) — re-synced + republished those two, relaunch landed with all 5 tarballs verified fresh
  (`mdps-backfill-tradfi-20260726-140301`). **Live confirmation of this doc's own open finding**: watched the VM's
  per-VM manifest shard in real time — `market-data-processing-service` has written **zero** `instrument_type=FUTURE`
  manifest rows in the ENTIRE prod tradfi manifest (checked directly: `availability_index.parquet`, 5,887,069 rows,
  403,493 `instrument_type=FUTURE` rows total, but `service_name` on every non-blank-id FUTURE row is
  `instruments-service` or `market-tick-data-service` — NEVER `market-data-processing-service`). The synthetic
  `CME:FUTURE:{root}-USD@LIN- {expiry}` id scheme this doc previously flagged as "unrelated" is now IDENTIFIED: it's
  written by `instruments-service`/MTDS as reference-data/empty_confirmed placeholder rows (broad —
  GBP/NATGAS/BRL/SILVER/COPPER/ DOW/JPY/LIVECATTLE/etc, not SP500-specific), NOT an MDPS artifact. **Root cause is NOT a
  silent `record_captured` swallow** — `write_candle_parquet` (canonical_writer.py:528) unconditionally calls
  `record_captured` for every non-empty write; confirmed via the live per-VM shard that manifest writes DO land
  (`ManifestWriter: per-VM shard updated`). The REAL reason MDPS has never produced a `FUTURE` row: this launched VM's
  per-VM shard rows are so far 100% `attempted_failed`/`instrument_type=UNKNOWN` — raw MTDS tick data for 2020-01-01
  carries a large volume of malformed `{symbol}_migrated_{timestamp}` instrument_ids (options strikes AND at least one
  bare future, `ESM0_migrated_20260418T131054Z`) that `_infer_instrument_type` correctly can't classify, so every one of
  these rows gets rejected pre-write (honest `attempted_failed`, not silently dropped) rather than ever reaching a
  `FUTURE`-tagged `record_captured` call. **This is an ALREADY-TRACKED corpus, not a new bug**: the `_migrated_`
  suffix + garbage ids are the exact target of the existing
  `market-tick-data-service/market_tick_data_service/scripts/recover_tradfi_garbage_underlying_2026_07.py` one-off
  recovery tool (see `plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md`) — not duplicating that
  workstream here; noting the connection so whoever runs that recovery next understands it should also reduce this
  backfill's per-day malformed-id churn. **Efficiency finding + correction**: the first single-VM full-range launch
  (2020-01-01..2026-07-25, 2,398 days) took ~7 minutes to clear ONLY day 2020-01-01 (dominated by malformed-id churn,
  ~175ms/instrument × thousands of garbage strikes) before its `subprocess-per-date` driver correctly moved on to day 2
  — SSH-verified the process was NOT stuck, just slow (a `gcloud storage cat` read of the GCS-teed `run.log` lagged real
  execution by minutes, causing a false "stalled" read before I checked `ps` on the VM directly). At that rate the full
  2,398-day range would take on the order of a week on one VM (impractical for a single SPOT VM + this todo's scope).
  Re-sharded as 7 parallel per-year VMs instead (the sanctioned "per-VM shards" pattern, zero code changes,
  `mdps-backfill-tradfi-y2020-20260726-141819` .. `mdps-backfill-tradfi-y2026-20260726-142028`, each its own
  `_index/per_vm/<vm>.parquet` shard) — cuts expected wall-clock roughly 7×. All 7 launched clean (tarballs verified
  fresh on the retry), confirmed RUNNING. A 60-hour background watchdog is tracking real per-VM manifest row growth (not
  log activity) across all 7 shards; this todo stays open/in-progress pending real completion + a re-verified hit-rate
  improvement (todo 1's ~19% baseline) per the "plans run to actual completion" HARD RULE.
- 2026-07-26 (slot 2, this same "backfill MDPS's per-contract process step" P0 todo, continued): Picked up from slot 4's
  IN-FLIGHT state. Found a real scope-mismatch bug in the just-launched 7 per-year shards: slot 4's resharding
  invocation (`launch-mdps-backfill-vm.sh tradfi 2020-01-01 2026-07-25 full`) dropped the
  `MDPS_INSTRUMENT_IDS='CME:FUTURE:ES CME:FUTURE:MES'` scope that the FIRST single-VM attempt
  (`mdps-backfill-tradfi-20260726-140251`, launched separately — banner-attributed to slot 3, still RUNNING alongside
  the 7 shards) had. Confirmed via direct parquet-content inspection of two of the 7 shards' per-VM manifest files:
  `y2020` had written 2,652 rows, 380 distinct `instrument_id`s, ALL malformed `_migrated_`/garbage strike ids (the
  already-tracked garbage corpus); `y2025` had written 1,651 rows, 414 distinct `instrument_id`s, ALL `NYSE:EQUITY:*`
  tickers (`ABBV`, `ABT`, `ACN`, ... — real S&P 500 equities, `instrument_type=EQUITY`, `data_type=ohlcv_15m`). Neither
  shard had produced a SINGLE ES/MES futures row — the 7 VMs were processing the ENTIRE TradFi instrument universe
  (equities + options + garbage ids), not the ES/MES futures this todo targets, a real billing-waste + scope-creep bug
  (7× the compute, mostly on out-of-scope data, defeating the whole point of resharding for speed). **Fix**: killed all
  7 mis-scoped shards. Separately verified the surviving correctly- scoped `140251` VM directly via its GCS-teed
  `run.log`: real invocation confirmed `--instrument-ids CME:FUTURE:ES CME:FUTURE:MES`, genuine per-date progress
  (`🏁 Date range complete` markers), clean (zero errors on tradfi so far). Investigated whether its `VM_FORCE=false`
  (no `--force`) would prevent it from ever fixing the documented wrong-contract-per-date bug (e.g. `2021-01-05` holding
  only June-2021's file when March-2021 should be active) — dispatched a sub-agent to read the actual
  `--operation process` batch-mode skip path (NOT the live/streaming `candle_write_mixin.blob_exists` path, which is a
  different code path and not what this CLI invocation uses): `orchestration_service._filter_existing_outputs` →
  `orchestration_scanner._check_existing_outputs` (`orchestration_scanner.py:650-701`) keys the skip check on
  `(timeframe, instrument_id)` extracted from the RAW INPUT blob path via `extract_instrument_id_from_blob_path`; for
  TradFi FUTURE the raw MTDS input is a chain-bundle (`.../underlying={U}/ticks.parquet`) which extracts to an
  EMPTY-STRING sentinel (`gcs_path_utils.py:105-110`), never a real contract id — so it can never collide with an
  existing real-contract-named OUTPUT, meaning the day is NOT skipped and gets reprocessed; `write_candle_parquet`
  itself (`canonical_writer.py`) has no existence check at all, it always overwrites. Conclusion: `--force` is NOT
  needed — the backfill will correctly add the missing correct-contract file even without it (the confirmed remaining
  gap is upstream RAW MTDS coverage for that contract/date, not a skip-if-fresh false-positive). Flagged one adjacent,
  NOT-yet-hit latent bug for visibility (not chased further): if a STALE existing OUTPUT were itself an unnamed
  `ticks.parquet` bundle (the `candle_leaf_filename` fallback), its extracted key would ALSO be the empty-string
  sentinel and WOULD collide with a bundle-shaped raw input, silently skipping regardless of content — worth a follow-up
  look if a future backfill shows anomalously-low real hit rates on a bundle-heavy shard. **Efficiency re-fix**: even
  correctly scoped, `140251`'s real steady-state rate (spot-measured via consecutive `🏁 Date range complete`
  timestamps, ~18-20s/date with occasional multi-minute outliers on malformed-id-heavy dates) projects to ~12-20+ hours
  for the full 2,398-day range on one VM — genuinely too slow for this todo's critical-path urgency. Killed `140251`
  (idempotent skip-if-fresh means the ~43 already-processed early-2020 days are re-skipped near- instantly on relaunch,
  not redone) and relaunched the SAME per-year-sharding idea slot 4 had, this time WITH the ES/MES filter preserved:
  `MDPS_INSTRUMENT_IDS='CME:FUTURE:ES CME:FUTURE:MES' bash launch-mdps-backfill-vm.sh --vm-name mdps-backfill-tradfi-y<YEAR>es-<ts> tradfi <year-start> <year-end> full`
  for each of 2020-2026. Hit the SAME tarball-drift race documented earlier TWICE more during this relaunch (once
  needing a fresh `create-code-tarballs.sh` for
  `market-data-processing-service`/`unified-api-contracts`/`deployment-service` — the deployment-service repo clone in
  this slot had no `.venv` yet, `bash scripts/setup.sh` first — and once mid-batch for `market-tick-data-service` after
  a concurrent fleet push moved its HEAD again); re-synced + republished each time. All 7 launched clean
  (`mdps-backfill-tradfi-y2020es-20260726-144859` .. `y2026es-20260726-145338`), confirmed RUNNING, confirmed via VM
  metadata + a live `run.log` spot-check that the ES/MES instrument filter is actually present in the running command
  this time. This todo stays open/in-progress pending real completion + a re-verified `24h`/`1d` hit-rate improvement
  (todo 1's ~19% baseline) per the "plans run to actual completion" HARD RULE — whoever picks this up next should check
  real per-VM manifest row growth across all 7 `y*es-*` shards (not log activity), and once all 7 have stopped (VM
  `VM_SHUTDOWN_ON_COMPLETION=true`), re-run `build-continuous` for ES and re-measure the `24h`/`1d` hit rate before
  flipping this todo's checkbox.
- 2026-07-26 (slot 2, reconciliation note): after pushing the above, a rebase pulled in slot 3's concurrent commits —
  `140251` was genuinely SPOT-preempted (not killed by my earlier delete; the timing coincided) and slot 3 had already
  correctly resumed it from measured progress as a single VM (`mdps-backfill-tradfi-20260726-144837`,
  `--start-date 2020-02-13` through `2026-07-25`, same ES/MES filter). That VM fully overlapped in scope with my 7
  freshly-launched `y*es-*` shards (same instrument filter, same remaining date range, just split 7 ways). Killed
  `144837` to avoid two concurrent efforts covering the identical range — the 7-way split is strictly faster for the
  same correct scope, so no work/coverage is lost, only the redundant single-VM compute. If slot 3's session finds its
  `144837` VM gone, this is why: superseded by the `y*es-*` shards, not a preemption or an untracked deletion.
- 2026-07-26 (slot 6, P2 "re-run the SAME ES/MES process-step backfill a second time" todo, BOTH VM PHASES DONE,
  measurement BLOCKED): Re-confirmed the 454/2398 (~18.9%) `1d` baseline live before launching. Launched the 7 per-year
  `y{2020..2026}es` VMs (no `--force`), fixed 2 tarball-drift races before all 7 ran with verified-fresh code — **all 7
  confirmed self-deleted 22:24:37Z**, independently `gcloud`-verified (not just trusting the monitor). Hit the
  fleet-wide disk-full condition (`BLK-37401b23`-class ENOSPC) TWICE mid-session; the monitor process itself stayed
  alive and its readings were re-verified accurate once disk cleared each time — no false-completion signal. Also
  resolved an unrelated `unified-trading-pm` dirty-repo alert (`workspace-manifest.json` locally regenerated to a state
  matching 3 already-pushed origin commits; `git restore` + `git pull --ff-only`, no work lost).

  Re-ran `build-continuous` for ES over `2020-01-01..2026-07-25` (one more MDPS tarball-drift race fixed) — **confirmed
  self-deleted 22:48:07Z**, independently `gcloud describe`'d NOT_FOUND, ~15 min (slower than the doc's ~2 min
  precedent, likely more per-contract data to stitch post-backfill; real `[[VM_PROGRESS]]` advancing mid-run, not
  stalled).

  Hit the SAME ENOSPC a third time (`cf_manifest_audit._read_index()` returned an unexpected 9-column tuple, filed
  separately as `/plans/archive/issues/cf_manifest_audit_read_index_inconsistent_return_shape_2026_07_26.md` (resolved
  2026-07-26 — confirmed intentional, not a bug); a direct `gcloud storage cp` also failed). **Root cause found**:
  `/tmp` is a SEPARATE, tiny 2GB tmpfs (100% full, shared host-wide), distinct from `/home` (78G free the whole time) —
  `gcloud storage cp`'s default staging path lands in `/tmp` regardless of `/home`'s real headroom. Fix: an explicit
  `/home`-rooted destination — downloaded cleanly at 485 MiB/s on the first retry.

  **RESULT: `1d` hit rate = `captured=454`/`empty_confirmed=1944` (2398 total, ~18.9%) — BYTE-IDENTICAL to baseline.**
  Verified against a FRESH read (consolidated index `Update Time: 22:58:44Z`, after the build-continuous VM's own
  22:48:07Z completion — not stale). A full second pass of BOTH phases produced ZERO net change in the hit rate — **this
  disproves the timing-race theory**: raw data landing late does NOT explain the stuck ~19% ceiling, since a second full
  pass had every chance to catch it and didn't move the number. Corroborates slot 5's separate P1 finding
  (`_list_instrument_files` returning 0 despite the target existing 24+ min prior, zero contention) — the real cause is
  more likely a listing/consistency issue than a timing race. Checkbox flipped `[x]` — the done-condition (re-measure +
  interpret) is satisfied by this negative result, mirroring this doc's precedent for closing an investigation on a
  disproven hypothesis. **Next step**: pursue slot 5's P1 finding, not another timing-race re-run — this todo's own
  remediation mechanism (periodic re-run) is now empirically ruled out.

## Deferred work after 2026-07-26

| Item                                                                                                                         | State / why deferred                                                                                                                                                                                                                                                                                                | Blocked on                                                                                                         |
| ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Todo 4 (this file, P0) — real features-delta-one-tradfi production launch + manifest verification                            | ✅ DONE 2026-07-26 (slot 3) — real feature parquets + real manifest `captured` rows verified via direct GCS listing + parquet-content inspection                                                                                                                                                                    | N/A — closed                                                                                                       |
| New P1 todo — MDPS `24h`/`1d` sparse coverage investigation                                                                  | ✅ DONE 2026-07-26 (slot 2) — root cause found (upstream per-contract processed-candle data gap, not a build-continuous code bug); see progress log for the 3-part evidence chain                                                                                                                                   | N/A — closed                                                                                                       |
| New P0 todo — backfill MDPS's per-contract "process" step for ES/MES full history                                            | ✅ DONE 2026-07-26 (slot 2) — all 7 shards + build-continuous re-run completed with real verified data, BUT the hit rate did NOT improve (still 454/2398≈19%, unchanged); real root cause diagnosed (raw-ingestion/process-step timing race, not a code bug — 2 wrong hypotheses ruled out first, see progress log) | N/A — closed as an action; the underlying sparse-coverage goal is NOT resolved, see the new P2 catch-up-rerun todo |
| New P2 todo — re-run process step for ES/MES on `2020-03-26` only                                                            | ✅ ACTION DONE 2026-07-26 (slot 5) — clean re-run, but MES still fully missing; root cause is NOT the premature-kill theory — new P1 listing-anomaly finding filed below                                                                                                                                            | N/A — closed as an action; underlying gap reopened as the new P1 listing-anomaly finding                           |
| New P1 todo — `_list_instrument_files` returned 0 raw files despite the target file existing 24+ min prior, zero contention  | Not done — new finding (slot 5, 2026-07-26); disproves the earlier timing/race theory; likely explains the stuck ~19% hit-rate ceiling across BOTH full backfill passes; needs isolated repro + GCS consistency check                                                                                               | Nobody — needs someone with time to reproduce the listing call in isolation and check bucket consistency config    |
| New P2 todo — add a generous timeout to `process_handler.py:706`'s `subprocess.run(cmd)`                                     | ✅ DONE 2026-07-26 (slot 6) — `market-data-processing-service@2b7c4dc`, 1800s timeout + regression test, QG green                                                                                                                                                                                                   | N/A — closed                                                                                                       |
| New P2 todo — re-run the SAME process-step backfill a SECOND time to catch up on late-landing raw data (timing-race finding) | ✅ DONE 2026-07-26 (slot 6) — hit rate FLAT (454/2398, byte-identical to baseline) after a full second pass; timing-race theory DISPROVEN. Corroborates slot 5's P1 listing-anomaly finding as the more likely real cause.                                                                                          | N/A — closed; see the new P1 listing-anomaly finding for the promising next lead                                   |

**Recommended next item**: the backfill + build-continuous re-run + hit-rate re-verification all genuinely happened
(2026-07-26) — the surprising result is that the hit rate did NOT move (still ~19%), and the real root cause turned out
to be a raw-ingestion/process-step TIMING RACE (not a code bug, not a data-density gap, not the id-scheme mismatch
initially suspected — see the flipped todo's full evidence chain). The concrete next action is the new P2 "re-run the
SAME backfill a second time" todo: a plain, cheap, idempotent re-run to pick up raw data that landed after the first
pass already gave up on a date. All 3 remaining P2 todos in this doc are small and can be picked up independently by
anyone, any time — none are blocking.

- 2026-07-26 (slot 3, reconciliation): confirmed via the operations log that my `140251`→`144837` resume chain was
  genuinely KILLED by slot 2 (not SPOT-preempted as I'd diagnosed from an empty `gcloud describe` alone — a real gap in
  my own monitoring: I should have checked `operations list`'s `user` field sooner, which showed the same
  `github-actions-deploy` service account both slots share, not a GCE-internal preemption actor). Relaunched a THIRD
  single-VM attempt (`...150236`, resuming from `2020-02-21`) before spotting slot 2's 7 `y*es-*` shards already running
  the identical correctly-scoped range — killed my own redundant VM immediately on discovering the overlap. Net effect:
  zero real work lost (idempotent skip-if-fresh + slot 2's shards already cover this scope), but ~15 min of my own
  avoidable relaunch churn. Deferring fully to slot 2's 7-shard effort from here — not launching further VMs against
  this todo myself. **Correction to my own earlier reasoning**: I had briefly suspected the `--instrument-ids` filter
  itself was silently failing to scope output (based on seeing non-ES/MES underlyings' files under `day=2020-02-13`) —
  those files carried `Creation Time: 2026-07-23`, i.e. 3 days old, predating EVERY VM launched today (mine and slot
  2's/4's). The filter was never actually broken; I was comparing against stale, unrelated pre-existing data. The REAL
  scoping bug slot 2 found was in a DIFFERENT, earlier set of 7 shards (slot 4's, which omitted the filter entirely) —
  already killed before I looked into it.
- 2026-07-26 (slot 2, self-correction on a premature kill): while monitoring the 7 `y*es-*` shards, `y2020es` and
  `y2026es` both went ~12-13 min with zero visible log progress on the SAME calendar date (`2020-03-26` / `2026-03-06`),
  which I initially read as a genuine hang — SSH-confirmed 0% incremental CPU over an 8s window plus several stale
  `CLOSE-WAIT` TCP sockets on both, and confirmed (via `grep subprocess.run` in `process_handler.py:706`) that the
  per-date driver's `subprocess.run(cmd)` call has NO timeout, so a truly hung child would block that shard's date-range
  loop forever with no self-recovery. Killed `y2020es`'s subprocess (pid 25214, date `2020-03-26`) to unblock it.
  **Turned out to be premature**: `y2026es`'s identical-looking "hang" self-resolved ~2 minutes later with a clean
  `rc=0` and a genuine `Total Duration: 13.5m` completion (all-zero result — a real, fully-processed empty date, not a
  crash) — proving a single date CAN legitimately take 13+ minutes under current conditions, most likely GCS API
  contention from running 7 backfill shards concurrently PLUS my own repeated monitoring `gcloud storage cat`/SSH calls
  hitting the same project simultaneously (a self-inflicted load factor I hadn't accounted for). Confirmed the outer
  per-date loop correctly treats a killed/failed date as non-fatal (log `subprocess-per-date: date=%s rc=%d (FAILED)`,
  loop continues — verified `y2020es` moved on to `2020-03-27`..`2020-03-30` normally after the kill), so no OTHER dates
  were affected, but `2020-03-26` itself — a COVID-crash-era date that almost certainly has real, large trading volume,
  not an empty one — is now recorded `attempted_failed` in that shard's manifest instead of a genuine result.
  **Follow-up needed**: after this backfill's 7 shards all complete, a targeted single-date re-run of `2020-03-26` for
  ES/MES
  (`launch-mdps-backfill-vm.sh --instrument-ids "CME:FUTURE:ES CME:FUTURE:MES" tradfi 2020-03-26 2020-03-26 full`, no
  `--force` needed — the failed manifest entry won't block a clean re-attempt) is needed to backfill this one real gap;
  not urgent enough to interrupt the other 6 shards for. **Corrective action going forward**: raised my own
  stall-investigation threshold from ~10min to ~20+ min of true flatness before SSH-diagnosing (this session's own
  monitoring was adding to the exact GCS contention it was trying to diagnose) — not adding a code-level timeout to
  `subprocess.run(cmd)` on the strength of this one instance alone, since a naive timeout short enough to catch a real
  hang risks falsely killing legitimately-slow-but-real dates like `y2026es`'s 13.5-minute one; flagging the
  missing-timeout gap here for whoever next has time to design a properly generous (30+ min) one with its own regression
  test, rather than rushing a fix under this same premature-judgment pressure.
- 2026-07-26 (slot 6, the P2 "re-run the SAME ES/MES process-step backfill a second time" todo, IN PROGRESS): Re-read
  baseline directly off the live manifest before launching (not trusting the doc's stated number blind):
  `market-data-tick-tradfi-prd-central-element-323112`'s `continuous_future`/`underlying=ES` rows show, per timeframe,
  identical `captured=454`/`empty_confirmed=1944` for `1m`/`5m`/`15m`/`1h`/`4h`/`1d`, and
  `captured=0`/`empty_confirmed=2398` for the literal `24h`/`15s` tokens (expected — MDPS writes `1d`, not `24h`, per
  this doc's own earlier finding) — confirms the 454/2398 (~18.9%) baseline is current, no drift since the last
  measurement. Launched the 7 per-year `y*es-*` VMs exactly mirroring slot 2's established pattern
  (`MDPS_INSTRUMENT_IDS='CME:FUTURE:ES CME:FUTURE:MES'`, no `--force`, no code change). Hit the SAME two tarball-drift
  races this doc has now documented on every single launch attempt: (1) stale `unified-trading-library` on the first
  pass (non-blocking warning, not caught by default `LC_TARBALL_FRESHNESS`) — killed all 7 (each <2 min old, negligible
  lost work under idempotent skip-if-fresh) and relaunched with `LC_TARBALL_FRESHNESS=enforce`; (2) mid-batch,
  `market-tick-data-service` drifted again (fleet activity moved its HEAD between my fresh-pull and the 2023-2026
  launches), correctly BLOCKED by `enforce` this time rather than silently running stale code — republished MTDS,
  relaunched the remaining 4. All 7 now confirmed RUNNING with every dependent tarball
  (`market-data-processing-service`, `market-tick-data-service`, `unified-api-contracts`, `unified-trading-library`,
  `deployment-service`) verified fresh at launch time — no VM in this batch ever ran stale code (unlike several of this
  doc's earlier launches). Armed a `run_in_background` monitor watchdog (5-min poll interval, `/api/slots/6/progress`
  heartbeat each tick, up to ~8.3h ceiling) rather than blind-waiting or polling the harness. Next: once all 7
  self-delete, re-run `build-continuous` for ES (existing `launch-mdps-build-continuous-vm.sh`, no timeframe restriction
  needed now that the 24h/1d normalisation fix is already shipped), then re-measure the `1d` hit rate against the
  454/2398 baseline and record whether it rose (confirms the timing-race diagnosis) or held flat (reopens the
  investigation, per this todo's own instruction).
- 2026-07-26 (slot 5, the P2 "re-run ES/MES on `2020-03-26` only" todo, DONE + new finding): pre-launch baseline check
  found ES already had real data for all 6 timeframes (created 2026-07-23, predating today's activity) while MES had
  ZERO files for any timeframe — confirming the gap was real, not already fixed by slot 6's broader in-flight re-run.
  Launched `mdps-backfill-tradfi-20260726-223423` per the todo's exact command; all 5 dependency tarballs verified
  fresh, ran clean with zero fleet contention (only concurrent VM was slot 6's `build-continuous` read, not a raw
  writer), completed `exit_code=0` in ~6s of real processing and self-deleted. Post-run: MES is STILL completely missing
  across all 6 timeframes — not because of a crash/timeout/kill this time, but because the process step's own log shows
  a clean "no upstream data" verdict (`Listed 0 files ... for data_type=ohlcv_1m` etc. across all 6 checked data_types →
  `Skipped 6 data_types with no upstream data`). Directly falsified that verdict against live GCS: the raw
  `futures_chain/underlying=SP500/.../ohlcv_1m/ticks.parquet` file (SP500 is ES/MES's real raw-bucket `underlying=`, per
  this doc's earlier `EXCHANGE_CODE_TO_NAME` finding) genuinely exists, 74,823 real bytes,
  `Creation Time: 2026-07-26T22:10:12Z` — 24 minutes before this VM was even launched and 27 minutes before its listing
  ran, with no concurrent raw-writer VM active. This DISPROVES this doc's own prior "TIMING/RACE condition" theory for
  at least this case (that theory required concurrent fleet contention as the cause; here there was none, and the file
  had already been fully settled for 24+ minutes) — traced the call chain to confirm the listing code itself
  (`orchestration_scanner.py` → `unified_trading_library/cloud_interface/providers/gcp.py`'s `list_blobs`) is a thin
  passthrough to the native GCS client with no app-level caching, pointing toward a GCS list-consistency edge case
  rather than an application bug. Filed as a new, higher-priority P1 finding (this doc, above) since — if raw data can
  be genuinely present-but-listing-invisible — this is the most plausible explanation for why BOTH of this doc's full
  ES/MES backfill passes (the completed P0 todo + slot 6's concurrent second pass) have left the `1d`/`24h` hit rate
  stuck at the same ~19% ceiling: re-running an unreliable listing mechanism cannot converge no matter how many times
  the underlying raw data improves. Flipped this todo's own checkbox (the literal re-run ACTION is complete and was
  executed correctly) but the underlying `2020-03-26` MES gap remains open, now tracked under the new P1 finding rather
  than the original (disproven) premature-kill theory. No code shipped — verification + new finding only.
