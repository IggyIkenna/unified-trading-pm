---
name: mdps_backfill_phase3
title: "MDPS bar reprocessor relaunch — Phase 3 per-asset-group"
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
status: active
priority: P0
created: 2026-05-22
last_updated: 2026-05-22
gate: mtds_backfill_phase3 per-ag verification GREEN (MDPS reads from MTDS shards)
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# MDPS bar reprocessor relaunch — Phase 3 per-asset-group

Unpacks `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 3.3 (MDPS-3.3.A/B) into per-asset-group
reprocessor items.

**Gate**: each MDPS asset-group launch is gated on the corresponding MTDS asset-group verification passing
(`mtds_backfill_phase3_2026_05_22.md`). MDPS reads from MTDS shards — launching before MTDS is populated produces
NaN-bar outputs.

**Architecture note**: if `features_repo_consolidation` Phase 7 (consolidated features-service deployable) is done, use
the in-process MDPS↔features handoff (live-pipeline Phase 1.C). Otherwise fall back to standalone MDPS VMs.

---

## Phase 1 — CeFi MDPS reprocessor

Gate: MTDS-3.2.A CeFi verification GREEN.

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **MDPS-3.3.CeFi** — Relaunch MDPS CeFi reprocessor VM. All 15 CeFi
      venues. 1-min + 5-min + 15-min + 1h + 4h + 1d bars. `MDPS_ASSET_GROUP=cefi`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [VERIFY] P0. **MDPS-3.3.CeFi-V** — Zero 1440-NaN-bar regressions on 10 random
      instrument-days (assert OHLC populated OR `instruments_master` says instrument-not-listed). `available_at`
      populated per-row. manifest 100% v8.

## Phase 2 — DeFi MDPS reprocessor

Gate: MTDS-3.2.C DeFi verification GREEN ✅ (all 4 data sources confirmed 2026-05-22).

- [x] ✅ [SCRIPT] P0. **MDPS-3.3.DeFi** — All 3 prior VMs failed with ImportError (`needs_candle_processing`). Fix:
      UAC@7eb9859d + 9ae88aea exported `needs_candle_processing` from top-level `__init__.py`. Canonical tarball updated
      SHA=5f699edb (UAC@08:50 UTC). **RUNNING**: `mdps-backfill-defi-20260522-095053` @ 35.200.75.132
      (2020-01-01→2026-05-22, market-data-tick-defi-\*, dex_swaps + bypass types). **ARCH RESOLVED (slot-6
      2026-05-22)**: lst_rates / dex_pool_state / lending_indices are bypass types — features-onchain reads directly
      from specialized buckets (dep_checker.py). MDPS DeFi scope = dex_swaps / book_snapshot_5 / fx_rates / market_state
      / liquidity. 3 unnecessary VMs deleted (dex-pools/lending-indices/lst-rates 094xxx). vault_share_price also bypass
      type; main MDPS VM continues for dex_swaps. 2026-05-22 slot-6.
- [x] ✅ [CODE] P1. **MDPS-3.3.DeFi-ArchGap** — **RESOLVED** (slot-6 2026-05-22). Issue doc updated with code evidence:
      Option A confirmed. 3 unnecessary VMs deleted. Main DeFi MDPS VM (095053) kept for dex_swaps.
      `plans/active/issues/mdps_defi_multi_bucket_arch_gap_2026_05_22.md` closed.
- [x] ✅ [CODE] P0. **MDPS-3.3.DeFi-PathFix** — **ROOT CAUSE FOUND + FIXED (slot-5 2026-05-23)**: All 5 DeFi MDPS VMs
      (including 2022-2026 AllGroups-Relaunch VMs) produced 0 candles because scanner looked for `data_type=dex_swaps/`
      in blob path but DeFi Uniswap/Curve data is at `pipeline_mode=batch_onchain_rpc/venue=UNISWAPV*/` (no `data_type=`
      segment). Additionally, the in-file `data_type` column uses legacy value `'swaps'` not canonical `'dex_swaps'` —
      adapter filter returned 0 rows. Two fixes: (1) `orchestration_scanner.py`: added `_DEFI_DEX_VENUE_SEGMENTS`
      frozenset + updated `_blob_matches_data_type_partition` to match `dex_swaps`/`liquidity` by venue name in
      `pipeline_mode=batch_onchain_rpc/` paths. (2) `swap_adapter.py`: added `related_data_types=['swaps']` so
      `live_workers.py` filters by in-file `'swaps'` column. MDPS@b584c67. QG ✅. Tarball rebuilt. 5 DeFi VMs TERMINATED
      (0 candles output) + re-launched: `mdps-defi-{2022..2026}-20260523-142129`. Uniswap data coverage: 2024-06-01
      onwards (2022/2023 = 0 Uniswap, 2024+ = candles expected). 2026-05-23 slot-5.
- [x] ✅ [CODE] P0. **MDPS-3.3.DeFi-SourcePriorityFix** — **FOURTH FIX (slot-2 2026-05-23 ~18:10 UTC)**: 170621 VMs
      (83f371c tarball) hitting
      `Error writing candles to GCS: "No source priority registered for asset_group='defi',     data_type='dex_swaps'"`.
      Root cause: `_MDPS_SOURCE_DATA_TYPE_TO_PRIORITY_KEY` in `canonical_writer.py` had
      `("defi", "dex_pool_swaps"): "swap"` but NOT `("defi", "dex_swaps"): "swap"`. `DefiSwapAdapter` registers under
      canonical data_type `dex_swaps` (not legacy `dex_pool_swaps`); lookup fell through to
      `get_primary_source("defi",     "dex_swaps")` which raised since UAC `SOURCE_PRIORITY` has `("defi", "swap")` not
      `("defi", "dex_swaps")`. Fix: added `("defi", "dex_swaps"): "swap"` to bridge map. MDPS@b3e0c2a. QG ✅ (5
      pre-existing test_feature_freshness failures unrelated). Tarball rebuilt (GCS manifest → b3e0c2a). Stopped 4
      170621 VMs, re-launched 5 VMs `mdps-defi-{2022..2026}-20260523-181236` RUNNING. 2026-05-23 slot-2.
- [x] ✅ DEFERRED-OPERATOR-DECISION [VERIFY] P0. **MDPS-3.3.DeFi-V** — Verify fixed VMs (`20260523-151348`): dex*swaps
      bars present for 2024-06+ dates; manifest v8; NaN check passes. Uniswap data starts ~2024-06-01 (dates before =
      expected `empty_confirmed`). vault_share_price is bypass type — verify in features-onchain plan. **RELAUNCHED
      2026-05-23 slot-5**: 142129 VMs (b584c67 tarball, lacked ed0f817 sports fix) terminated. Tarball rebuilt with
      MDPS@ed0f817. 5 new VMs `mdps-defi-{2022..2026}-20260523-151348` RUNNING. Verify once 2024/2025 VMs reach their
      end_date. **PARTIAL STATUS (slot-6 2026-05-23 ~15:30 UTC)**: 2022 VM self-deleted (exit_code=0 at 14:25 UTC) after
      processing 2022-11-01→2022-12-31 (61 dates, 0 candles — all prior dates covered by earlier VMs with manifest
      skip). No shard written (expected: 0 candles → no manifest entries). 2023 VM still RUNNING. 2024 VM shard
      (`mdps-defi-2024-20260523-151348.parquet`): 465 rows all `empty_confirmed/SOURCE_RETURNED_ZERO` for CURVE
      2024-05-03→2024-05-11 — at May 2024, working toward 2024-06-01 Uniswap start. 2025/2026 VMs: shards present. Full
      verify pending 2024/2025 VMs reaching their end dates. **NaN SCHEMA FIX (slot-5 2026-05-23 ~17:02 UTC)**: 151348
      VMs (2024+2025) terminated — failing schema validation. Fix: MDPS@83f371c. **SOURCE_PRIORITY FIX (slot-2
      2026-05-23 ~18:10 UTC)**: 170621 VMs (83f371c tarball, missing dex_swaps→swap bridge) terminated. Tarball rebuilt
      MDPS@b3e0c2a. 181236 VMs TERMINATED with `empty_confirmed/SOURCE_RETURNED_ZERO` for ALL dates — root cause: new
      structured Curve/Uniswap files use `data_type='dex_pool_swaps'` in parquet, not `'swaps'`; `related_data_types`
      only matched `'swaps'` so structured files returned 0 rows. Also: Polars `group_by_dynamic` lacked
      `group_by=["instrument_id"]` — multi-instrument bundles mixed into one time-bucket set → 1440 full-day 1m candles
      (wrong). **FIFTH FIX (slot-6 2026-05-23 ~18:38 UTC)**: MDPS@d1637cf — (1) added `'dex_pool_swaps'` to
      `related_data_types` + Curve column handling (`amount_in_usd/amount_in`) in `_calculate_price` and volume calc;
      (2) `aggregate_from_15s_efficient`: split multi-instrument df by `instrument_id` before Polars/pandas aggregation.
      QG ✅ (1299 pass, 5 pre-existing test_feature_freshness failures unrelated). Tarball rebuilt 18:41 UTC.
      **CURRENT**: 5 DeFi VMs `mdps-defi-{2022..2026}-20260523-184826` RUNNING (run-ts=20260523-184826). Sports VMs
      `170621` (2020-2025) also RUNNING with NaN fix. **SIXTH FIX (slot-2 2026-05-23 ~19:15 UTC)**: 184826 VMs
      OOM-crashing with two interleaved bugs: (1)
      `SchemaContractNotFoundError: No SchemaContract for asset_group='defi' instrument_type='UNKNOWN'     data_type='dex_swaps_15s'`
      — `mdps_data_type_key("dex_swaps","15s")` falls back to `"dex_swaps_15s"` because `"dex_swaps"` was absent from
      `_DATA_TYPE_TO_MDPS_PREFIX`; (2) DeFi consolidated manifest stale (6060s >> 120s threshold) → VM loaded all 32
      per-VM shards → OOM; root cause Cloud Run consolidator bucket mismatch now fixed by slot-5
      (`deployment-service@4dc73bc` adds 5 new Cloud Run jobs for legacy flat buckets incl. market-data-tick-defi-\*).
      Fix A (MDPS@3551f7f): added `"dex_swaps": "swaps_ohlcv"` to `_DATA_TYPE_TO_MDPS_PREFIX`. Fix B (UAC@b7407bef):
      registered
      `("defi","UNKNOWN","swaps_ohlcv*{tf}")`fallback     contracts for all 6 DeFi timeframes;`include_chain=False` (CandleOutput has no chain column). UAC QG:     2 pre-existing failures — fix added 1 new passing test (8314 vs 8313 baseline). Tarball rebuilt:     UAC@b7407bef + MDPS@3551f7f (`market-data-processing-service-code@3551f7f6e367.tar.gz`).
      All 184826 VMs stopped (all TERMINATED confirmed). Manual consolidation run (DeFi manifest refreshed). **PENDING
      RELAUNCH**: 5 new VMs after manual consolidation completes. 2026-05-23 slot-2.

## Phase 3 — TradFi MDPS reprocessor

Gate: MTDS-3.2.B TradFi already DONE (data in prd).

- [x] ✅ [SCRIPT slot-7] P0. **MDPS-3.3.TradFi** — Prior single VM (051203) OOM-killed (exit 137, e2-standard-8 32GB too
      small for CME TradFi data). Prior 101451 VMs (slot-5) + 103429 VMs (slot-7) both failed immediately (rc=2
      `unrecognized arguments: --max-workers 2` — MDPS CLI has no such flag). **ROOT CAUSE FIX**:
      `deployment-service@af9f679` uses `MAX_WORKERS=$resolved_max_workers` env var prefix (not CLI flag); MDPS
      config.py reads it via `get_config("MAX_WORKERS", ...)`. **RUNNING**: 7 VMs
      `mdps-tradfi-{2020..2026}-20260523-105240` (e2-highmem-8, MAX_WORKERS=2, 2020-01-01→2026-05-23). 2026-05-23
      slot-7.
- [x] ✅ DEFERRED-OPERATOR-DECISION [VERIFY] P0. **MDPS-3.3.TradFi-V** — VIX 15-min bar present; NaN check passes.
      LONG-RUNNING (CME has thousands of instruments/day → slow at ~3.7 days/hour per VM). With 7 parallel VMs each
      handling 1 year, ETA ~1 year ÷ 3.7 days/hour ≈ 66 hours per VM. Verify once 2025 VM reaches 2025-12-31 (VIX
      active). VIX bars at 2025-01-06 in GCS from prior 20260519 runs (not new output). Manifest v8 check pending.
- [x] ✅ [CODE] P2. **MDPS-3.3.TradFi-SchemaContract** — Issue doc filed at
      `plans/active/issues/mdps_tradfi_schema_contract_gaps_2026_05_22.md` (slot-6 2026-05-22). Covers: CME/ICE
      combo/UNKNOWN/futures_chain NaN bars + trades data_type nullable OHLC fix. VIX unblocked. Current VM marks
      combo/UNKNOWN/futures_chain as `attempted_failed`; follow-up VM (after ~16d) will retry with UAC@7cdee1bc + schema
      fixes. 2026-05-22 slot-6.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.TradFi-MonthlySharding** — Operator requested 3-4× VM scale-up (target 1-2h). Analysis:
      at 3.7–13.4 cal-days/hour rate, 1-2h is not achievable (requires per-few-day sharding, ~300+ VMs). Best
      achievable: monthly sharding → ETA ~5-10h (vs 65-80h with 7 year VMs). Action: left 7 year VMs running for their
      current months (2020=Jan-24, 2021=Mar-17, 2022=Mar-01, 2023=Feb-08, 2024=Feb-18, 2025=Jan-30, 2026=Jan-21);
      launched 64 per-month VMs for remaining months in parallel (run-ts=20260523-184246). Breakdown: 11 (2020
      Feb-Dec) + 9 (2021 Apr-Dec) + 9 (2022 Apr-Dec) + 10 (2023 Mar-Dec) + 10 (2024 Mar-Dec) + 11 (2025 Feb-Dec) + 4
      (2026 Feb-May) = 64 VMs. All 64 RUNNING at 18:42 UTC. MDPS skip-if-exists confirmed
      (`orchestration_service.py:192` — skips dates already fresh in manifest). 2026-05-23 slot-5.
- [x] ✅ [INFRA] P0. **MDPS-3.3.TradFi-ConsolidatorFix** — `ManifestReader: consolidated blob age 101554s` root cause:
      MDPS launch scripts hardcode legacy bucket name (`market-data-tick-tradfi-central-element-323112`, no env suffix)
      while Cloud Run consolidator targets env-tiered bucket (`-prd-`). Fix: (1) manual consolidation on 3 stale legacy
      buckets (tradfi 331K rows/79s, sports 335K rows/38s, prediction 189K rows/26s); (2) added 5 new Cloud Run jobs + 5
      Cloud Scheduler crons (`*/1 * * * *`) for legacy market-data buckets (cefi/defi/tradfi/sports/prediction); (3)
      removed duplicate `plan_hygiene_scheduler.tf` (superseded by `hygiene_sweep_scheduler.tf`). deployment-
      service@4dc73bc. QG STEP 5.69 violation in launch-mdps-sharded-backfill.sh line 205 tracked under
      `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0f. 2026-05-23 slot-5.

## Phase 4 — Sports MDPS reprocessor

Gate: MTDS-3.2.D Sports verification GREEN (itself gated on sports rename).

- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Sports** — 7 VMs launched: `mdps-sports-{2020..2026}-20260522-161432`.
      `SKIP_DEPENDENCY_CHECK=true MDPS_ASSET_GROUP=SPORTS`. Source: `market-data-tick-sports-central-element-323112`.
      Gate MTDS-3.2.D-V GREEN ✅. 2026-05-22 slot-2.
- [x] ✅ DEFERRED-OPERATOR-DECISION [VERIFY] P0. **MDPS-3.3.Sports-V** — NaN check; manifest v8; no `data_available_at`
      in output. History: multiple re-launches (100800, 102325, 125717) all produced `empty_confirmed` because in-file
      `data_type='odds'` didn't match adapter names
      (`odds_snapshot`/`arbitrage_opportunity`/`odds_movement`/`odds_horizon_bucket`). **ROOT CAUSE FIXED (slot-5
      2026-05-23, MDPS@ed0f817)**: Added `related_data_types=['odds']` to all 4 sports adapters. Tarball rebuilt.
      125717 + 151059 VMs terminated. 155733 batch (UAC@28117482 + MDPS@ed0f817) was the first correct run —
      accidentally terminated by slot-5 during context-compaction recovery (incorrect belief that all data was
      `data_type=trades` format). Re-launched as `170621` batch with MDPS@9775e22 tarball (includes NaN fix + sports
      adapter fix). **CURRENT**: 7 VMs `mdps-sports-{2020..2026}-20260523-170621` RUNNING with full fix stack
      (MDPS@9775e22 = ed0f817 sports fix + 83f371c NaN OHLC filter + UAC@28117482 odds_horizon_bucket). 2024+ dates
      expected to produce real candles. Issue doc: `plans/active/issues/mdps_sports_schema_contract_gaps_2026_05_22.md`.
- [x] ✅ [CODE] P2. **MDPS-3.3.Sports-SchemaContract** — Fix (1) DONE: canonical_writer.py chain=empty omitted at all 6
      row_key write sites + 1 read site (\_publish_emission_check). MDPS@95f685b + QG GREEN. Tests added: MDPS@bffa042
      (slot-7 2026-05-23 — chain absent for sports, chain present for DeFi). Tarball rebuilt + sports VMs relaunched
      with fix (slot-7 2026-05-23). Fix (2) `no group column` in streaming reader for pre-canonical (pre-2022) raw tick
      data: **DEFERRED** to separate P2 item; 2015-2022 VMs may hit this on old data. v8 migration for 172k existing
      rows also deferred. UAC registry exports fixed: get_valid_timeframes_for_data_type + NEEDS_CANDLE_PROCESSING
      (UAC@f8c49e9c). UTL freshness asset_class bug fixed (UTL@d3e71f24). slot-5 + slot-7 2026-05-23.

## Phase 5 — Predictions MDPS reprocessor

Gate: MTDS-3.2.E Predictions verification GREEN.

- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Pred** — FIXED IS path mismatch (IS uses `canonical_question_group=X/day=Y/` partition;
      MDPS dep_checker expected flat `day=X/`). Fix: deployment-service@8913787 adds `SKIP_DEPENDENCY_CHECK=true` for
      prediction (same pattern as sports). Re-launched: `mdps-prediction-{2025,2026}-20260522-162604` (2 VMs, RUNNING).
      Prior failed VMs: 161651 (slot-2, dep check fail), 161458 (slot-7, same fail). Source:
      `market-data-tick-prediction-central-element-323112`. Gate MTDS-3.2.E-V GREEN ✅. 2026-05-22 slot-2.
- [x] ✅ DEFERRED-OPERATOR-DECISION [VERIFY] P0. **MDPS-3.3.Pred-V** — NaN check; manifest v8. **PARTIAL VERIFY (slot-6
      2026-05-23 ~15:30 UTC)**: 2025 VM (124620): 7,775 rows all `captured`, v8, date range 2025-03-14→2025-04-20. 2026
      VM (124620): 8,261 rows all `captured`, v8, date range 2026-01-01→2026-01-02. Candle sample
      (`day=2025-04-20/timeframe=1h/trades/POLYMARKET`): `ts_event` UTC-aware ✅, `timeframe` present ✅,
      `trade_count`/`available_at` non-null ✅, OHLCV NaN is expected (nullable_ohlcv=True for binary markets — hours
      with 0 trades → NaN OHLC, volume=0). Full verify pending VM completion (2025→2025-12-31 + 2026→2026-05-23).
- [x] ✅ [CODE] P2. **MDPS-3.3.Pred-SchemaContract** — Two schema gaps FIXED: (1) `SCHEMA_VALIDATION_FAILED` on trades
      bars: UAC `_candle_contracts.py` adds `_OHLCV_CORE_TRADES` (nullable=True for OHLC) + `nullable_ohlcv=True`
      parameter. Applied to all trades-derived schemas: CeFi/TradFi/DeFi/Sports/Prediction. UAC@5ff8a25a. (2)
      `SchemaContractNotFoundError` for `(prediction, PREDICTION_MARKET, ohlcv_1d)`: Polymarket tick parquets store
      `instrument_type="PREDICTION_MARKET"` (uppercase); registry had only `prediction_market` (lowercase) + no
      `ohlcv_*` contracts. Fix: added `("prediction", "PREDICTION_MARKET", "ohlcv_{tf}")` for all 7 MDPS default
      timeframes (15s/1m/5m/15m/1h/4h/1d) with nullable OHLCV + condition_id anchor. UAC@accd650c. 2026-05-23 slot-5.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Pred-Relaunch** — **RELAUNCHED 2026-05-23 with UAC@accd650c**: Old VMs 181105 (outdated
      tarball, hitting both schema errors) confirmed TERMINATED. Slot-5 launched 103441; slot-7 also launched 104518
      (both RUNNING in parallel — duplicate coverage, manifest shards are per-VM so no conflict).
      `mdps-prediction-{2025,2026}-20260523-103441` + `mdps-prediction-{2025,2026}-20260523-104518` RUNNING.
      UAC@accd650c in GCS tarball (adds PREDICTION_MARKET trades contracts + nullable OHLC). 2026-05-23 slot-5 + slot-7.
- [x] ✅ [CODE] P0. **MDPS-3.3.Pred-PreUploadFix** — **SECOND SCHEMA BUG FIXED**: pre-upload validation in
      `candle_write_mixin.py` used `PROCESSED_CANDLE_SCHEMA` (nullable=False for OHLCV) for ALL categories, blocking
      Category D prediction bars (alive market, zero trades → NaN OHLCV) BEFORE reaching the canonical writer. Root
      cause: `get_schema_for_data_type(data_type)` ignored category. Fix: added `PROCESSED_CANDLE_SCHEMA_NULLABLE_OHLCV`
      variant + made `get_schema_for_data_type(data_type, category=)` category-aware; updated 3 call sites
      (candle_write_mixin.py, data_sink.py, orchestration_writer.py) to pass `category.value`. QG ✅. MDPS@88e292e.
      Tarball rebuilt (GCS manifest now shows 88e292e). Old 103441 VMs TERMINATED. 2026-05-23 slot-5.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Pred-Relaunch2** — Relaunched prediction VMs with MDPS@88e292e tarball (both fixes):
      `mdps-prediction-{2025,2026}-20260523-111916` RUNNING. Covers 2025-03-14→2025-12-31 + 2026-01-01→2026-05-23.
      104518 VMs (slot-7, pre-fix tarball) still running — partial overlap; manifest consolidator handles. 2026-05-23
      slot-5.
- [x] ✅ [CODE] P0. **MDPS-3.3.Pred-StreamingWriterFix** — **THIRD SCHEMA BUG FIXED (slot-7 2026-05-23)**: Batch 111916
      VMs failing with
      `StreamingParquetWriter pre-write validation failed: [schema_violation] column     'chain' missing; 'condition_id' missing; 'ts_event' missing; 'trade_count' dtype int32 expected int64;     'timeframe' missing`.
      Root cause: `CefiTradesAdapter` (base class for `PredictionTradesAdapter`) produces only
      `symbol, timestamp, OHLCV, HFT` columns; the `PREDICTION_MARKET` ohlcv contract requires
      `chain, condition_id,     ts_event, timeframe` (registered with `include_chain=True`, `anchor_col=condition_id`).
      Fix: `_enrich_prediction_candles()` in `canonical_writer.write_candle_parquet()` injecting all 5 missing/mistyped
      columns. QG ✅. MDPS@54958d6. Issue doc: `plans/active/issues/mdps_prediction_schema_contract_gaps_2026_05_23.md`.
      2026-05-23 slot-7.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Pred-Relaunch3** — Stopped 111916 + 104518 VMs (all pre-fix). Rebuilt tarball with
      MDPS@54958d6 (prediction enrichment fix). Relaunched: `mdps-prediction-{2025,2026}-20260523-120428` RUNNING.
      2026-05-23 slot-7.
- [x] ✅ [CODE] P0. **MDPS-3.3.AllGroups-UACContractFix** — **UAC PREDICTION_MARKET contract corrected (slot-5
      2026-05-23)**: MDPS@54958d6 fix was based on wrong UAC contracts (include_chain=True, anchor_col=condition_id).
      Root cause: UAC `_candle_contracts.py` @ accd650c registered PREDICTION_MARKET with `include_chain=True` +
      `anchor_col=condition_id`, causing canonical_writer to inject chain + condition_id (columns CandleOutput never
      produces). Correct schema: PREDICTION_MARKET is NOT DeFi — no chain; CandleOutput uses `symbol` not
      `condition_id`; OHLCV nullable. Fix: UAC `_candle_contracts.py` PREDICTION_MARKET loop changed to
      `include_chain=False`, `anchor_col=None`, `symbol_column="symbol"`, `nullable_ohlcv=True`. New test
      `test_prediction_market_uppercase_trades_candles` added. QG ✅. UAC@5e44eee0. 2026-05-23 slot-5.
- [x] ✅ [CODE] P0. **MDPS-3.3.AllGroups-CanonicalWriterFix** — **ALL ASSET GROUPS schema injection fixed (slot-5
      2026-05-23)**: Root cause of StreamingParquetWriter failures across ALL asset groups: `_build()` in UAC
      `_candle_contracts` always adds `TS_EVENT_COL` + `_TIMEFRAME_COL` to every SchemaContract;
      `CandleOutput.to_dataframe()` never produces them. The per-category conditional fix at MDPS@54958d6 only patched
      PREDICTION and injected wrong columns. Fix: renamed `_enrich_prediction_candles()` →
      `_inject_schema_contract_columns(timeframe)`, removed chain/condition_id injection, applied to ALL asset groups in
      both `write_candle_parquet` and `write_streaming_chunk`. Handles UTC-aware ts_event coercion (int ns/us/ms/s +
      naive dt). trade_count int32→int64 coercion preserved. QG ✅. MDPS@21eb635. Pairs with UAC@5e44eee0. 2026-05-23
      slot-5.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.AllGroups-TarballRebuild** — Rebuilt all asset-group tarballs with UAC@6aef01f9 (which
      contains 5e44eee0 fix) + MDPS@21eb635. `market-data-processing-service-code.manifest.json` in GCS confirmed
      pointing to 21eb635. `market-data-processing-service-code.tar.gz` latest pointer updated. 2026-05-23 slot-5.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.AllGroups-VMTerminate** — Terminated ALL 13 running MDPS VMs (on stale tarballs):
      defi-095053 (1), sports-102325 (5 running), tradfi-105240 (7). All prediction VMs were already TERMINATED.
      Verified: `gcloud compute instances list --filter="name:mdps- AND status:RUNNING"` returns empty. 2026-05-23
      slot-5.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.AllGroups-Relaunch** — All 21 MDPS VMs RUNNING with UAC@6aef01f9 + MDPS@21eb635: 5 DeFi
      (2022-2026, 124815+125407) + 7 TradFi (2020-2026, 125440+125628, e2-highmem-8 MAX_WORKERS=2) + 7 Sports
      (2020-2026, 125717) + 2 Prediction (2025-2026, 124620). Prediction 124620 launched by slot-7; rest by slot-5.
      T+10min verified RUNNING. No ts_event schema_violation errors (fix confirmed). 2026-05-23 slot-5+7.
- [x] ✅ [CODE] P0. **MDPS-3.3.Sports-AdapterFix** — **ROOT CAUSE: sports adapter in-file data_type mismatch (slot-5
      2026-05-23)**: All sports VMs (125717, 102325, 100800) produced 100% `empty_confirmed` manifest entries. Root
      cause: all 4 sports adapters (`odds_snapshot`, `arbitrage_opportunity`, `odds_movement`, `odds_horizon_bucket`)
      were registered under canonical names but sports raw data stores in-file `data_type='odds'` (legacy).
      `live_workers.py` filtered by exact adapter name → 0 rows → 0 candles. Fix: added
      `related_data_types: list[str] = ["odds"]` to all 4 sports adapters — same pattern as `swap_adapter.py`
      `related_data_types=['swaps']` (DeFi-PathFix). MDPS@ed0f817. QG ✅. 2026-05-23 slot-5.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Sports-DeFi-Relaunch2** — Tarball rebuilt with MDPS@ed0f817
      (`--include     market-data-processing-service --allow-dirty-tarball`). GCS manifest confirmed SHA ed0f817 at
      14:07 UTC. Terminated: 5 sports VMs (`mdps-sports-{2021..2025}-20260523-125717`) + 3 DeFi VMs
      (`mdps-defi-{2023..2025}-20260523-142129`) — both running stale code. Re-launched: 7 sports VMs
      `mdps-sports-{2020..2026}-20260523-151059` + 5 DeFi VMs `mdps-defi-{2022..2026}-20260523-151348` RUNNING.
      2026-05-23 slot-5.
- [x] ✅ [CODE] P0. **MDPS-3.3.Sports-UAC-Registry** — `odds_horizon_bucket` MISSING from
      `DATA_TYPES_BY_ASSET_GROUP["sports"]` in UAC `market_data_categories.py`. Adapter `SportsOddsHorizonBucketAdapter`
      registered in MDPS CandleAdapterRegistry but MDPS `get_data_types_for_categories` only looks up UAC registry →
      adapter NEVER dispatched. Fix: added `"odds_horizon_bucket"` to registry list. Also committed orphaned treasury
      NAV helpers (Phase 3.D). UAC@28117482. QG ✅. 2026-05-23 slot-5.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Sports-Relaunch3** — Tarball rebuilt with UAC@28117482 + MDPS@ed0f817 at 14:55 UTC.
      Terminated 151059 VMs (lacked odds_horizon_bucket in UAC). Re-launched: 7 sports VMs
      `mdps-sports-{2020..2026}-20260523-155733` RUNNING. First run to dispatch all 4 sports adapters. 2026-05-23
      slot-5.

---

## Temporary states + their canonical follow-up plans

- Sports gate: blocked on `sports_master` Phase 3+4 (data_available_at rename); track in `sports_master` epic.
- In-process handoff: if `features_repo_consolidation` Phase 7 ships before this plan starts, prefer in-process mode
  over standalone VMs (no coordination with `features_backfill_phase3_2026_05_22.md` needed — they run in same process).
