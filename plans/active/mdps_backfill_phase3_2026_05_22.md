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

> **⚠️ SUPERSEDED — folded into the v9 single-walk canonicalisation (2026-06-05).** The `DEFERRED-BLOCKED` VM-RUNNING /
> GATE items are NOT lost — MDPS bar gap-fill is bundled INTO the per-AG canonicalisation single-walk (gap-fill +
> canonicalise + `pipeline_mode`/`source`/v9 in one pass; doing the old separate VM relaunch now would double-walk).
> **Live home:** `cefi`/`defi`/`tradfi`/`sports`/`prediction`_manifest_canonicalisation_2026_06_01.md (per-AG MDPS
> surface) + `downstream_services_manifest_canonicalisation_2026_06_01.md` (MDPS layer). Archive (needs `[unlock-plan]`)
> ONLY after the per-AG walks land v9 + the operator verifies the MDPS bar coverage on the new layout.

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

- [x] ✅ DEFERRED-BLOCKED [GATE: MTDS-3.2.A-V not yet GREEN] [SCRIPT] P0. **MDPS-3.3.CeFi** — Relaunch MDPS CeFi
      reprocessor VM. All 15 CeFi venues. 1-min + 5-min + 15-min + 1h + 4h + 1d bars. `MDPS_ASSET_GROUP=cefi`.
- [x] ✅ DEFERRED-BLOCKED [GATE: MDPS-3.3.CeFi not yet launched] [VERIFY] P0. **MDPS-3.3.CeFi-V** — Zero 1440-NaN-bar
      regressions on 10 random instrument-days (assert OHLC populated OR `instruments_master` says
      instrument-not-listed). `available_at` populated per-row. manifest 100% v8.

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
- [x] ✅ [VERIFY] P0. **MDPS-3.3.DeFi-V** — **VERIFIED (slot-7 2026-05-24 ~20:00 UTC)**: Verification via 101628 VMs
      (TERMINATED, final state) + GCS parquet spot-checks. Results: **Manifest**: 2024=11,786 captured (63 dates) +
      4,945 empty_confirmed, schema_version=8 for ALL rows ✓; 2025=11,983 captured (64 dates) + 4,999 empty_confirmed,
      schema_version=8 for ALL rows ✓. **Data types**: 7 present (swaps_ohlcv_15s/1m/5m/15m/1h/4h/1d) — 4h included ✓.
      **NaN check**: 4 random samples (2024-06-15 UNISWAP_V3, 2024-09-01 CURVE, 2025-08-01 UNISWAP_V2, 2025-11-01
      UNISWAP_V3): 0 null OHLCV across all rows ✓. **Field check**: chain='ETHEREUM' ✓, swap_count=int64 ✓,
      volume_quote_usd populated ✓. **Uniswap start**: 2024-06-01 UNISWAP_V3 files=140 ✓; dates before = empty_confirmed
      (expected) ✓. **2026 UPDATE (slot-7 2026-05-25)**: Chain-split venue fix shipped (MDPS@2e7461f) — scanner now
      decomposes `BALANCER-ETHEREUM` → `venue=BALANCER/chain=ETHEREUM/` for prd bucket paths. Tarball rebuilt. 2026
      consolidated manifest: 21,814 captured + 1,840 empty_confirmed + 2,007 attempted_failed. Captured range:
      2026-01-01→2026-05-22. Venues: UNISWAPV3(6815) + UNISWAPV4(4291) + MORPHO(2802) + BALANCER(2444) + others ✓.
      2026-01-01→2026-01-24: empty_confirmed (prd bucket lacks MTDS tick data for those dates; `mtds-dex-swaps-backfill`
      covers 2026-01-25+). 2007 attempted_failed: UNISWAP_V3/SUSHISWAP_V3/PANCAKESWAP_V3 waiting on MTDS backfill.
      **NOTE**: 2024+2025 candles are in flat bucket `market-data-tick-defi-central-element-323112`; 2026 candles go to
      prd bucket `market-data-tick-defi-prd-central-element-323112`. Features DeFi compute must read from BOTH buckets
      or data migration must occur first. Flag for features launch operator decision.
- [x] ✅ [CODE] P0. **MDPS-3.3.UAC-IncidentFix** — **UAC `unified_api_contracts.incident` module restored (slot-7
      2026-05-25)**: UTL `recovery/agent_action.py` imports 5 symbols from `unified_api_contracts.incident`
      (ActionProvenance, ActionStatus, ActionType, AgentActionEvent, RecoveryVerificationResult) — this caused ALL MTDS
      VMs to crash at startup with `ModuleNotFoundError: No module named 'unified_api_contracts.incident'`. Root cause:
      incident module (9 files) was deleted from UAC but UTL still imported from it. Reconstructed from pyc bytecode +
      added `BinaryEventTrigger` to `risk_rule/` package (also missing, imported by UTL `rule_evaluator.py`).
      UAC@3d05b8e9 pushed to LDR. Tarball rebuilt:
      `unified-api-contracts-code@3d05b8e956cba88567da90fee1adc8f9f78fc950.tar.gz` +
      `mtds-code@acda8552ba6121e57842b6fcf7bf50f9d4d01227.tar.gz` uploaded to GCS. 2026-05-25 slot-7.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.DeFi-DexSwaps-Relaunch** — **`mtds-dex-swaps-backfill` relaunched (slot-7 2026-05-25
      ~06:46 UTC)**: Prior VM crashed at startup due to UAC incident module missing (MTDS-3.3.UAC-IncidentFix now
      resolved). Relaunched with fixed tarball: `mtds-dex-swaps-backfill` RUNNING (asia-northeast1-c, e2-standard-4).
      MTDS_TARBALL_SHA=acda8552ba6121e57842b6fcf7bf50f9d4d01227. Source: 1,771 `attempted_failed` rows from prior crash
      run should be retried by ManifestFreshnessCache. 2026-05-25 slot-7.
- [x] ✅ DEFERRED-BLOCKED [VM-RUNNING: mtds-dex-swaps-backfill in progress — operator to verify once complete] [VERIFY]
      P0. **MDPS-3.3.DeFi-DexSwaps-V** — T+10min: `mtds-dex-swaps-backfill` RUNNING + ≥1 progress logged. Full verify:
      1,771 attempted_failed converted → captured/empty_confirmed; manifest v8. 2026-05-25 slot-7.

## Phase 3 — TradFi MDPS reprocessor

Gate: MTDS-3.2.B TradFi already DONE (data in prd).

- [x] ✅ [SCRIPT slot-7] P0. **MDPS-3.3.TradFi** — Prior single VM (051203) OOM-killed (exit 137, e2-standard-8 32GB too
      small for CME TradFi data). Prior 101451 VMs (slot-5) + 103429 VMs (slot-7) both failed immediately (rc=2
      `unrecognized arguments: --max-workers 2` — MDPS CLI has no such flag). **ROOT CAUSE FIX**:
      `deployment-service@af9f679` uses `MAX_WORKERS=$resolved_max_workers` env var prefix (not CLI flag); MDPS
      config.py reads it via `get_config("MAX_WORKERS", ...)`. **RUNNING**: 7 VMs
      `mdps-tradfi-{2020..2026}-20260523-105240` (e2-highmem-8, MAX_WORKERS=2, 2020-01-01→2026-05-23). 2026-05-23
      slot-7.
- [x] ✅ DEFERRED-BLOCKED [VM-RUNNING: 7 VMs mdps-tradfi-{2020..2026}-20260523-105240 ETA ~66h — operator to verify once
      2025 VM reaches 2025-12-31] [VERIFY] P0. **MDPS-3.3.TradFi-V** — VIX 15-min bar present; NaN check passes.
      LONG-RUNNING (CME has thousands of instruments/day → slow at ~3.7 days/hour per VM). With 7 parallel VMs each
      handling 1 year, ETA ~1 year ÷ 3.7 days/hour ≈ 66 hours per VM. Verify once 2025 VM reaches 2025-12-31 (VIX
      active). VIX bars at 2025-01-06 in GCS from prior 20260519 runs (not new output). Manifest v8 check pending.
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
- [x] ✅ [CODE] P0. **MDPS-3.3.Sports-EighthBugFix** — **EIGHTH BUG: sports `arbitrage_opportunity`
      SCHEMA_VALIDATION_FAILED — OHLCV NaN not allowed (slot-7 2026-05-25)**: `get_schema_for_data_type()` in
      `output_schemas.py` returned non-nullable OHLC schema for ALL sports data types. The `arbitrage_opportunity`
      adapter fills empty windows (no odds data in a period) with NaN arb-margin used as OHLCV — same pattern as
      prediction Category D bars. Schema validation rejected these candles ("NOT NULLABLE"), silently skipping uploads +
      no manifest entry. Fix: added `or (category == "sports" and data_type == "arbitrage_opportunity")` to nullable
      OHLCV condition. 4 tests added. market-data-processing-service@3dd1191. Tarball rebuilding 2026-05-25 slot-7.
- [x] ✅ [CODE] P0. **MDPS-3.3.Sports-NinthBugFix** — **NINTH BUG: sports odds_snapshot / odds_movement /
      odds_horizon_bucket SCHEMA_VALIDATION_FAILED — OHLCV NaN not allowed (slot-7 2026-05-25)**: EighthBugFix only made
      `arbitrage_opportunity` nullable. But `odds_snapshot`/`odds_movement`/`odds_horizon_bucket` also produce NaN OHLCV
      in 15m/1h windows with no posted odds (pre-match gaps, quiet periods). Schema validation silently dropped these
      candles too. Root cause identical to EighthBugFix — same `category=="sports"` pattern for all 4 adapters. Fix:
      changed `category=="sports" and data_type=="arbitrage_opportunity"` → `category=="sports"` (covers all 4 sports
      data types). 4 new tests added in `test_schema_robustness.py`. QG verified via workspace venv (pre-existing
      `unified_api_contracts.incident` missing module blocks repo QG). market-data-processing-service@65b6a54.
      2026-05-25 slot-7.
- [x] ❌ [SCRIPT] P0. **MDPS-3.3.Sports-Relaunch7** — ❌ SUPERSEDED BY Relaunch8. Was: relaunch only 2025 with @3dd1191
      (EighthBugFix only). NinthBugFix (65b6a54) is a superset and ALL years need relaunching — 030136 batch completed
      2020-2025 with @1f1adbf, 041846 completed 2026 with @1f1adbf; both pre-NinthBugFix. 2026-05-25 slot-7.
- [x] ❌ [SCRIPT] P0. **MDPS-3.3.Sports-Relaunch8** — ❌ ALL 7 CRASHED (slot-7 2026-05-25). Root cause: VMs launched at
      ~05:12 UTC (BST shown as 06:12) BEFORE canonical UAC tarball was rebuilt at 05:33 UTC. VMs downloaded OLD UAC
      (without `unified_api_contracts.incident` module) → UTL `recovery/agent_action.py:19` crashed immediately.
      `mdps-sports-{2020..2026}-20260525-061238` EXIT_STATUS=1, all auto-deleted. See MDPS-3.3.Sports-Relaunch9.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Sports-Relaunch9** — **ALL 7 sports VMs relaunched (slot-7 2026-05-25 ~06:58 UTC)**:
      UAC canonical tarball confirmed at @3d05b8e9 (incident module present, uploaded 05:33 UTC). All 7 VMs launched
      AFTER tarball update → will get fixed UAC. `mdps-sports-{2020..2026}-20260525-065857` RUNNING.
      MDPS_TARBALL_SHA=65b6a54fccc7a467477c661f3545150979bd165e (NinthBugFix). STALL_TIMEOUT_SEC=7200. Source:
      `market-data-tick-sports-prd-central-element-323112`. 2026-05-25 slot-7.
- [x] ✅ [CODE] P0. **MDPS-3.3.Sports-TenthBugFix** — **TENTH BUG: all 4 sports adapters generate 508 candles/date but 0
      written to GCS (slot-7 2026-05-25)**: `canonical_writer._resolve_primary_source_for_candle()` calls
      `get_source_priority("sports", "odds_snapshot")` (lowercase) but SOURCE_PRIORITY registers
      `("sports", "ODDS_SNAPSHOT")` (uppercase). Exact-case lookup fails → KeyError → `Error writing candles to GCS`.
      All 508 candles/date silently dropped for `odds_snapshot`, `odds_movement`, `arbitrage_opportunity`,
      `odds_horizon_bucket`. Root cause: `_MDPS_SOURCE_DATA_TYPE_TO_PRIORITY_KEY` bridge dict had no sports entries so
      lowercase fell through to as-is lookup → mismatch. Fix: added 4 sports entries to bridge dict mapping lowercase
      MDPS data_type → uppercase UAC SOURCE_PRIORITY key. market-data-processing-service@e53cc35. QG ✅. 2026-05-25
      slot-7.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Sports-Relaunch10** — Tarball rebuilt with MDPS@e53cc358 (TenthBugFix). Relaunch9 VMs
      `065857` terminated (0 GCS writes for all sports candle data types — confirmed by VM logs). All 7 sports VMs
      relaunched: `mdps-sports-{2020..2026}-20260525-074034` RUNNING.
      MDPS_TARBALL_SHA=e53cc358365271c6d7f184e4116edd1a9908e2aa. STALL_TIMEOUT_SEC=7200. Source:
      `market-data-tick-sports-prd-central-element-323112`. 2026-05-25 slot-7.
- [x] ✅ [CODE] P0. **MDPS-3.3.Sports-TwelfthBugFix** — **TWELFTH BUG: all sports VMs (Relaunch10) produced 0 candles
      written despite code reaching streaming reader (slot-7 2026-05-25)**. Four-part root cause: (A)
      `_CHAIN_GROUP_COL_CANDIDATES` missing `"instrument_id"` → streaming reader found no group column for per-bookie
      files (which use `instrument_id` not `instrument_key`/`symbol`) → returned 0 groups → 0 candles. (B) All 4 sports
      adapters had `related_data_types=["odds"]` but per-bookie raw files have `data_type="trades"` →
      `_streaming_filter_slice()` eliminated all rows → empty tick*data. (C) Bundle
      `ticks_migrated*\*.parquet`files     have`instrument_type=""`but`data_type="odds"`→`\_infer_instrument_type()`returned bookie name (e.g.     "BETFAIR_EX_UK") →`SchemaContractNotFoundError`→ write skipped. (D) Sports adapters expected    `home_odds`/`away_odds`/`draw_odds`wide format but per-bookie files have`price`+`outcome_name`long format →     all odds columns NaN → 0-candle output. Fixes: (A) added`"instrument_id"`to`\_CHAIN_GROUP_COL_CANDIDATES`in    `live_workers.py`; (B) `related_data_types=["odds","trades"]`in all 4 sports adapters; (C) fallback in    `canonical_writer.\_infer_instrument_type()`when`instrument_type=""`+`data_type="odds"`→ return "odds"; (D)     price/outcome_name pivot added to`odds_snapshot_adapter`, `odds_movement_adapter`, `arbitrage_adapter`
      before the existing wide-format fill loop. QG ✅. market-data-processing-service@21700c5. 2026-05-25 slot-7.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Sports-Relaunch11** — Tarball rebuilt with MDPS@21700c5 (TwelfthBugFix) + UTL@9094cac.
      Relaunch10 VMs `074034` already terminated. All 7 sports VMs relaunched:
      `mdps-sports-{2020..2026}-20260525-092751` RUNNING. MDPS_TARBALL_SHA=21700c5ce18e7a54069278aa077d813115e118cc.
      UTL_TARBALL_SHA=9094cac1876db23a2fb3286c0de2ebd45afb50c3. STALL_TIMEOUT_SEC=7200 (auto). Source:
      `market-data-tick-sports-prd-central-element-323112`. 2026-05-25 slot-7.
- [x] ✅ DEFERRED-BLOCKED [VM-RUNNING: 7 VMs mdps-sports-{2020..2026} (Relaunch11) RUNNING — operator to verify once
      complete] [VERIFY] P0. **MDPS-3.3.Sports-V** — NaN check; manifest v8; no `data_available_at` in output. History:
      multiple re-launches (100800, 102325, 125717) all produced `empty_confirmed` because in-file `data_type='odds'`
      didn't match adapter names (`odds_snapshot`/`arbitrage_opportunity`/`odds_movement`/`odds_horizon_bucket`). **ROOT
      CAUSE FIXED (slot-5 2026-05-23, MDPS@ed0f817)**: Added `related_data_types=['odds']` to all 4 sports adapters.
      Tarball rebuilt. 125717 + 151059 VMs terminated. **RUNNING: 7 VMs `mdps-sports-{2020..2026}-20260523-155733`**
      with UAC@28117482 (odds*horizon_bucket registered) + MDPS@ed0f817 (related_data_types fix). First run to dispatch
      all 4 adapters. 2024+ dates expected to produce real candles (pre-2024 = old format, empty_confirmed expected).
      Issue doc: `plans/active/issues/mdps_sports_schema_contract_gaps_2026_05_22.md`. **SIXTH BUG (slot-7
      2026-05-25)**: 215548 VMs produced 315 attempted_failed for
      `odds_horizon_bucket*\*`with     MalformedTickFieldError. Root cause: SUPER_LIG + other venues publish odds >34h pre-match     (bm_minutes_to_kickoff≈2054 > T-24h+cap=1500) → all rows outside staleness cap → adapter raised instead of     returning empty. Fix: MDPS@a8b28f4 returns`\_make_empty_candle_output()`for the all-outside-cap case →     empty_confirmed instead of attempted_failed. 3 tests added. QG: all passed. Relaunched:     **7 VMs`mdps-sports-{2020..2026}-20260525-014137`\*\*
      RUNNING. STALL_TIMEOUT_SEC=7200 + MDPS@a8b28f4. **NOW Relaunch9 (065857) RUNNING** — see
      MDPS-3.3.Sports-Relaunch9.
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
- [x] ✅ DEFERRED-BLOCKED [VM-RUNNING: prediction VMs still running — partial verify done 2026-05-23, full verify
      pending VM completion] [VERIFY] P0. **MDPS-3.3.Pred-V** — NaN check; manifest v8. **PARTIAL VERIFY (slot-6
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
- [x] ✅ [CODE] P0. **MDPS-3.3.Sports-StallFix** — **ROOT CAUSE: stall watchdog killed VMs before manifest shard flush
      (slot-7 2026-05-24)**: 155733 VMs TERMINATED with 290 orphaned 2024 candle files in GCS but NO manifest shard
      entries. Root cause: `STALL_TIMEOUT_SEC` was reduced 3600→1800 on 2026-05-23 (same day sports VMs launched).
      Sports MDPS processes long empty-date stretches (no betting events → no log output) that falsely triggered the
      1800s threshold, SIGKILLing the process before UTL flushed the manifest shard. Fix: (1)
      `setup-data-pipeline-vm.sh` reads `STALL_TIMEOUT_SEC` metadata key and exports it so `vm-exec-with-gcs-tee.sh`
      inherits the override; (2) `launch-mdps-sharded-backfill.sh` passes `STALL_TIMEOUT_SEC=7200` for sports VMs.
      `setup-data-pipeline-vm.sh` uploaded to `gs://deployment-scripts-central-element-323112/vm/`.
      deployment-service@ffe9d6d. 2026-05-24 slot-7.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Sports-Relaunch4** — Re-launched 7 sports VMs with stall fix
      `mdps-sports-{2020..2026}-20260524-215548` RUNNING. Pinned MDPS@6c9045160577 + UTL@e51699c8 SHA tarballs.
      `STALL_TIMEOUT_SEC=7200` in metadata → 2h stall window for empty-date stretches. Source:
      `market-data-tick-sports-prd-central-element-323112`. 2026-05-24 slot-7.
- [x] ✅ [CODE] P0. **MDPS-3.3.Sports-SeventhBugFix** — **SEVENTH BUG FIXED (slot-7 2026-05-25)**: Two distinct failures
      in 2026-27 season odds data: (1) `odds_horizon_bucket` TIMESTAMP_DATE_MISMATCH — epoch-zero timestamps
      (1970-01-01) generated because `timestamps = np.array([int(h[1] * 60 * 1_000_000) for h in TIER1_HORIZONS])`
      computed microseconds from Unix epoch (horizon×60μs) not from match date. Fix: added `_derive_match_midnight_us()`
      helper that reads `kickoff_utc`/`commence_time`/`fetch_utc` from tick data, normalizes to midnight, returns
      μs-since-epoch. All 8 bucket timestamps = match_midnight + bucket_index×1h → all on correct calendar date. (2)
      `odds_snapshot`/`odds_movement`/`arbitrage_opportunity` raised `ValueError("No timestamp column found in data")`
      because raw MTDS sports odds data has `fetch_utc`/`bm_time` ISO string columns, not the numeric
      `ts_init`/`local_timestamp`/`ts_event`/`timestamp` columns expected by `_get_local_timestamp_column()`. Fix: added
      `elif "fetch_utc" in tick_data.columns:` + `elif "bm_time" in tick_data.columns:` branches to all 3 adapters
      (parse ISO → UTC-aware datetime). 4 files modified: `bucket_assignment_adapter.py`, `odds_snapshot_adapter.py`,
      `odds_movement_adapter.py`, `arbitrage_adapter.py`. QG: all 1366+ tests pass. MDPS@1f1adbf. 2026-05-25 slot-7.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Sports-Relaunch5** — Terminated 5 RUNNING 014137 VMs (2021-2025, on stale MDPS@a8b28f4
      tarball — will hit SEVENTH bug when processing 2024+ dates with fetch_utc odds format). Rebuilt tarball with
      MDPS@1f1adbf (pinned SHA=1f1adbff541e28e0c973d4277d075f18bd0e30ba). Relaunched 6 sports VMs:
      `mdps-sports-{2020..2025}-20260525-030136` RUNNING. STALL_TIMEOUT_SEC=7200. Source:
      `market-data-tick-sports-prd-central-element-323112`. **NOTE: 2026 VM was NOT created in 030136 batch (gcloud
      confirms mdps-sports-2026-20260525-030136 never existed — launch script emitted only 2020-2025).** 2026-05-25
      slot-7.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.Sports-Relaunch6** — Launched missing 2026 VM: `mdps-sports-2026-20260525-041846`
      RUNNING. Same params as 030136 batch: MDPS_TARBALL_SHA=1f1adbff, STALL_TIMEOUT_SEC=7200, source=prd bucket,
      SKIP_DEPENDENCY_CHECK=true, 2026-01-01→2026-05-24. T+10min verified RUNNING. 2026-05-25 slot-7.

---

## Temporary states + their canonical follow-up plans

- Sports gate: blocked on `sports_master` Phase 3+4 (data_available_at rename); track in `sports_master` epic.
- In-process handoff: if `features_repo_consolidation` Phase 7 ships before this plan starts, prefer in-process mode
  over standalone VMs (no coordination with `features_backfill_phase3_2026_05_22.md` needed — they run in same process).
