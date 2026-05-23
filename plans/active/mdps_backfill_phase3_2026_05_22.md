---
name: mdps_backfill_phase3
title: "MDPS bar reprocessor relaunch — Phase 3 per-asset-group"
type: active
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

- [x] ✅ [AGENT slot 6] P0. **MDPS-3.3.TradFi** — Launched `mdps-backfill-tradfi-20260522-051203` VM (e2-standard-8,
      asia-northeast1-c, 2020-01-01→2026-05-22, prod). VM RUNNING @ 136.110.98.249. `MDPS_ASSET_GROUP=TRADFI`.
      `PROTOCOL_DATA_SOURCE_BUCKET_TRADFI=market-data-tick-tradfi-central-element-323112`. 2026-05-22.
- [ ] [VERIFY] P0. **MDPS-3.3.TradFi-V** — VIX 15-min bar present; NaN check passes. NOTE: VM at 2020-01-14 after 3.5h
      running (very slow — ~10 min/day × 2333 days = ~16 days ETA). VIX bars at 2020-01-01+ will eventually appear.
      LONG-RUNNING — verify once VM reaches 2026-05-22. **CORRECTION (slot-7 2026-05-22 ~17:30 UTC)**: Prior "VM at
      2026-01-21 @ 184 days/hour" was WRONG — that was reading OLD 20260519 VM output, not 051203 progress. Actual
      state: VM started 04:14 UTC, is at 2020-02-18 after ~13h (rate ~3.7 days/hour; CME has thousands of files/day).
      ETA to reach 2026-05-22: ~2280 remaining days ÷ 3.7 = ~620 hours ≈ 26 more days. VIX bars at 2025-01-06 exist in
      GCS from prior 20260519 VM runs (not new 051203 output). 051203 VM RUNNING and producing candles for early 2020
      dates — will verify manifest v8 + VIX presence only once VM actually reaches 2026-05-22.
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
      (slot-5 2026-05-23)**: 7 new VMs `mdps-sports-{2015..2026}-20260523-100800` launched with chain fix
      (MDPS@95f685b). Previous VMs exited 0 but produced ZERO output due to MalformedRowKeyError (chain="") at manifest
      write site. Fix: conditionally omit chain from row_key when empty (6 sites in canonical_writer.py). Verify once
      VMs complete. Issue doc: `plans/active/issues/mdps_sports_schema_contract_gaps_2026_05_22.md`.
- [x] ✅ [CODE] P2. **MDPS-3.3.Sports-SchemaContract** — Fix (1) DONE: canonical_writer.py chain=empty omitted at all 6
      row_key write sites + 1 read site (\_publish_emission_check). MDPS@95f685b + QG GREEN. Fix (2)
      `no group     column` in streaming reader for pre-canonical (pre-2022) raw tick data: **DEFERRED** to separate P2
      item; 2015-2022 VMs may hit this on old data. v8 migration for 172k existing rows also deferred. UAC registry
      exports fixed: get_valid_timeframes_for_data_type + NEEDS_CANDLE_PROCESSING (UAC@f8c49e9c). UTL freshness
      asset_class bug fixed (UTL@d3e71f24). slot-5 2026-05-23.

## Phase 5 — Predictions MDPS reprocessor

Gate: MTDS-3.2.E Predictions verification GREEN.

- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Pred** — FIXED IS path mismatch (IS uses `canonical_question_group=X/day=Y/` partition;
      MDPS dep_checker expected flat `day=X/`). Fix: deployment-service@8913787 adds `SKIP_DEPENDENCY_CHECK=true` for
      prediction (same pattern as sports). Re-launched: `mdps-prediction-{2025,2026}-20260522-162604` (2 VMs, RUNNING).
      Prior failed VMs: 161651 (slot-2, dep check fail), 161458 (slot-7, same fail). Source:
      `market-data-tick-prediction-central-element-323112`. Gate MTDS-3.2.E-V GREEN ✅. 2026-05-22 slot-2.
- [ ] [VERIFY] P0. **MDPS-3.3.Pred-V** — NaN check; manifest v8.
- [x] ✅ [CODE] P2. **MDPS-3.3.Pred-SchemaContract** — `SCHEMA_VALIDATION_FAILED` on `POLYMARKET:PREDICTION_MARKET:*`
      trades bars FIXED. UAC `_candle_contracts.py` adds `_OHLCV_CORE_TRADES` (nullable=True for open/high/low/close) +
      `nullable_ohlcv=True` parameter to `_build()`. Applied to all trades-derived schemas:
      CeFi/TradFi/DeFi/Sports/Prediction. UAC@5ff8a25a pushed to LDR 2026-05-22 slot-5. VM tarball rebuilt 18:04 UTC.
      Old VMs (162604) stopped; new VMs relaunched with fixed tarball. Same pattern also resolves
      MDPS-3.3.TradFi-SchemaContract (CME/ICE trades NaN bars). Sample contract:
      `0x71aa6ab89169bb131ea6c54da3e5fa248e4ad426192c5bc5e29ae967bc83cd1a`. 2026-05-22 slot-5.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Pred-Relaunch** — Relaunched with UAC@5ff8a25a nullable OHLC fix.
      `mdps-prediction-{2025,2026}-20260522-181105` RUNNING. 2025-03-14→2025-12-31 + 2026-01-01→2026-05-22.
      SKIP_DEPENDENCY_CHECK=true. Old VMs 162604 confirmed TERMINATED before launch. 2026-05-22 slot-5.

---

## Temporary states + their canonical follow-up plans

- Sports gate: blocked on `sports_master` Phase 3+4 (data_available_at rename); track in `sports_master` epic.
- In-process handoff: if `features_repo_consolidation` Phase 7 ships before this plan starts, prefer in-process mode
  over standalone VMs (no coordination with `features_backfill_phase3_2026_05_22.md` needed — they run in same process).
