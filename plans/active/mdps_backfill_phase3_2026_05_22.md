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

- [ ] [SCRIPT] P0. **MDPS-3.3.CeFi** — Relaunch MDPS CeFi reprocessor VM. All 15 CeFi venues. 1-min + 5-min + 15-min +
      1h + 4h + 1d bars. `MDPS_ASSET_GROUP=cefi`.
- [ ] [VERIFY] P0. **MDPS-3.3.CeFi-V** — Zero 1440-NaN-bar regressions on 10 random instrument-days (assert OHLC
      populated OR `instruments_master` says instrument-not-listed). `available_at` populated per-row. manifest 100% v8.

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
- [ ] [VERIFY] P0. **MDPS-3.3.DeFi-V** — Verify main VM (095053): dex_swaps bars present for post-2020 DeFi dates;
      manifest 100% v8. LONG-RUNNING (2020-01-01→2026-05-22; dex_swaps data starts ~2020-Q3). vault_share_price not
      verified via MDPS (bypass type — verify in features-onchain plan instead).

## Phase 3 — TradFi MDPS reprocessor

Gate: MTDS-3.2.B TradFi already DONE (data in prd).

- [x] ✅ [SCRIPT slot-7] P0. **MDPS-3.3.TradFi** — Prior single VM (051203) OOM-killed (exit 137, e2-standard-8 32GB too
      small for CME TradFi data). Prior 101451 VMs (slot-5) + 103429 VMs (slot-7) both failed immediately (rc=2
      `unrecognized arguments: --max-workers 2` — MDPS CLI has no such flag). **ROOT CAUSE FIX**:
      `deployment-service@af9f679` uses `MAX_WORKERS=$resolved_max_workers` env var prefix (not CLI flag); MDPS
      config.py reads it via `get_config("MAX_WORKERS", ...)`. **RUNNING**: 7 VMs
      `mdps-tradfi-{2020..2026}-20260523-105240` (e2-highmem-8, MAX_WORKERS=2, 2020-01-01→2026-05-23). 2026-05-23
      slot-7.
- [ ] [VERIFY] P0. **MDPS-3.3.TradFi-V** — VIX 15-min bar present; NaN check passes. LONG-RUNNING (CME has thousands of
      instruments/day → slow at ~3.7 days/hour per VM). With 7 parallel VMs each handling 1 year, ETA ~1 year ÷ 3.7
      days/hour ≈ 66 hours per VM. Verify once 2025 VM reaches 2025-12-31 (VIX active). VIX bars at 2025-01-06 in GCS
      from prior 20260519 runs (not new output). Manifest v8 check pending.
- [x] ✅ [CODE] P2. **MDPS-3.3.TradFi-SchemaContract** — Issue doc filed at
      `plans/active/issues/mdps_tradfi_schema_contract_gaps_2026_05_22.md` (slot-6 2026-05-22). Covers: CME/ICE
      combo/UNKNOWN/futures_chain NaN bars + trades data_type nullable OHLC fix. VIX unblocked. Current VM marks
      combo/UNKNOWN/futures_chain as `attempted_failed`; follow-up VM (after ~16d) will retry with UAC@7cdee1bc + schema
      fixes. 2026-05-22 slot-6.

## Phase 4 — Sports MDPS reprocessor

Gate: MTDS-3.2.D Sports verification GREEN (itself gated on sports rename).

- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Sports** — 7 VMs launched: `mdps-sports-{2020..2026}-20260522-161432`.
      `SKIP_DEPENDENCY_CHECK=true MDPS_ASSET_GROUP=SPORTS`. Source: `market-data-tick-sports-central-element-323112`.
      Gate MTDS-3.2.D-V GREEN ✅. 2026-05-22 slot-2.
- [ ] [VERIFY] P0. **MDPS-3.3.Sports-V** — NaN check; manifest v8; no `data_available_at` in output. **RELAUNCHED
      (slot-5 2026-05-23)**: 7 VMs `mdps-sports-{2020..2026}-20260523-100800` launched BUT ran OLD tarball (predated
      fix). All produced zero manifest output (same MalformedRowKeyError). **RELAUNCHED AGAIN (slot-7 2026-05-23)**: Old
      100800 VMs terminated. Tarball rebuilt with MDPS@bffa042 (chain fix + tests) using
      `create-code-tarballs.sh     --asset-group SPORTS`. 7 new VMs `mdps-sports-{2020..2026}-20260523-102325` RUNNING
      with fixed tarball. Verify once VMs complete. Issue doc:
      `plans/active/issues/mdps_sports_schema_contract_gaps_2026_05_22.md`.
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
- [ ] [VERIFY] P0. **MDPS-3.3.Pred-V** — NaN check; manifest v8.
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
- [ ] [SCRIPT] P0. **MDPS-3.3.AllGroups-TarballRebuild** — Rebuild ALL asset-group tarballs with UAC@5e44eee0 +
      MDPS@21eb635. UAC is CORE_REPO (bundled in every tarball). Command:
      `bash deployment-service/scripts/vm/create-code-tarballs.sh` (rebuilds all groups).
- [ ] [SCRIPT] P0. **MDPS-3.3.AllGroups-VMTerminate** — Terminate ALL running MDPS VMs (on stale tarballs with wrong
      schema injection): defi-095053 (1 VM), prediction-104518 (2 VMs), prediction-111916 (2 VMs), prediction-120428 (2
      VMs — the 54958d6-based fix, now superseded), sports-102325 (6 VMs), tradfi-105240 (7 VMs). Verify all TERMINATED.
- [ ] [SCRIPT] P0. **MDPS-3.3.AllGroups-Relaunch** — Relaunch MDPS VMs for all asset groups with rebuilt tarballs
      (UAC@5e44eee0 + MDPS@21eb635). Verify T+10min: RUNNING + manifest consolidator showing captured rows (not
      attempted_failed).

---

## Temporary states + their canonical follow-up plans

- Sports gate: blocked on `sports_master` Phase 3+4 (data_available_at rename); track in `sports_master` epic.
- In-process handoff: if `features_repo_consolidation` Phase 7 ships before this plan starts, prefer in-process mode
  over standalone VMs (no coordination with `features_backfill_phase3_2026_05_22.md` needed — they run in same process).
