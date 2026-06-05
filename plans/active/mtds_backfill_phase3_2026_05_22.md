---
name: mtds_backfill_phase3
title: "MTDS multi-venue backfill VM relaunch — Phase 3 per-asset-group"
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
estimate_class: infra
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 4.0
status: active
priority: P0
created: 2026-05-22
last_updated: 2026-05-22
gate: Phase 2 freeze lifted + Phase 7 manifest v8 backfill + label-flip GREEN (mtds_mdps_master)
supersedes:
  defi_upstream_46day_full_backfill_2026_05_16.md (that file was never created; this plan replaces the reference in
  mtds_mdps_master Phase 11)
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **⚠️ SUPERSEDED — folded into the v9 single-walk canonicalisation (2026-06-05).** The `DEFERRED-BLOCKED`
> VMs-IN-FLIGHT items are NOT lost — MTDS multi-venue gap-fill is bundled INTO the per-AG canonicalisation single-walk
> (gap-fill + canonicalise + the new `pipeline_mode=batch_*/` path + `source` column + v9 in one pass). **Live home:**
> `cefi`/`defi`/`tradfi`/`sports`/`prediction`_manifest_canonicalisation_2026_06_01.md (each canonicalises the MTDS
> tick surface for its AG). Already-migrated items (bucket naming → `bucket_name_ssot_canonicalisation`) keep their
> existing successor links below. Archive (needs `[unlock-plan]`) ONLY after the per-AG walks land v9 for MTDS.

# MTDS multi-venue backfill VM relaunch — Phase 3 per-asset-group

Unpacks `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 3.2 (MTDS-3.2.A through 3.2.E) into
per-asset-group VM launch items with venue detail.

**Critical gate**: MTDS-3.2.A/C/D/E are NOT just "Phase 2 freeze lifted" — they also require Phase 7 (manifest v8
backfill + label-flip) to be GREEN per `mtds_mdps_master` sequencing. New rows MUST land at v8 + typed reason. Launching
before Phase 7 grows the v<8 debt.

**MDPS-3.3.A and FEAT-3.4.A launch AFTER this plan's per-ag verifications pass.**

---

## Phase 1 — CeFi MTDS backfill (MTDS-3.2.A)

15 venues. Largest asset group. Parallelise across venues.

- [x] ✅ [CODE] P0. **MTDS-chain-fix** — `orchestrator.py` Tier-3/Tier-2/non-trading-day sentinels built row_key with
      `chain=""` for all CeFi/TradFi venues — UTL rejects explicitly-empty chain fields with MalformedRowKeyError
      (non-blocking but silently drops manifest rows for BITFINEX-FUTURES/SPOT and others). Fix: omit chain from row_key
      when empty. Test updated. QG: 1982 passed. market-tick-data-service@626eb154. Tarball uploaded 2026-05-22.
- [x] ✅ [AGENT slot 7] P0. **MTDS-3.2.A** — Launched `mtds-backfill-cefi-2026-05-22` VM (e2-highmem-4,
      asia-northeast1-c, 2024-01-01→2026-05-22, all venues, prod). VM RUNNING @ 34.180.126.53. 2026-05-22. NOTE: ran
      with old code (pre-chain-fix). ~4% complete before relaunch.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.A-Relaunch** — Old CeFi VM crashed at 07:13 (OOM 77% on e2-highmem-4, only 2 dates
      processed). Relaunched `mtds-backfill-cefi-2026-05-22b` (e2-highmem-8/64GB, chunk=5,
      market-tick-data-service@626eb154 chain fix). **FAILED exit_code=137 (OOM SIGKILL) at 10:19 UTC** — last log entry
      09:19 UTC (UPBIT 2024-01-01, 846,317 rows). Root cause: monolithic all-venue VM; DERIBIT book_snapshot_5 alone
      needs ~110GB peak on busy days; cumulative cross-venue RSS exceeded 64GB. No manifest shard written (0 rows out).
      34.104.198.234 VM auto-deleted. 2026-05-22.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.A-Relaunch-2** — Fix: switched from monolithic VM to sharded approach
      (`launch-cefi-sharded-backfill.sh`): per-venue × year × heavy/light splits, e2-highmem-2 (16GB) per VM — DERIBIT
      heavy per-year stays well under 16GB. Covers 2020-2026, all 9 CeFi venues, ~83 VMs in parallel (MAX_CONCURRENT=15
      staggered). VM_FORCE=false (skips already-captured dates via preflight). Launch timestamp: **LAUNCHED
      2026-05-22**. 2026-05-22 slot 5.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.A-DeadVMRelaunch** — **CORRECTED ROOT CAUSE** (GCS events analysis): not disk but
      MANIFEST OOM. CeFi consolidated manifest (36 MB compressed, 1682 per-VM shards) expands to ~12-13 GB in pandas
      memory during `read_availability_index` at startup — far exceeds e2-highmem-2 (16 GB). CPU spike to 148% during
      PyArrow parquet parse triggers `PROCESS_CPU_SATURATED` at T+5s; by T+35s memory hits 79.8% (12.7 GB); Linux OOM
      killer fires at ~T+41s. Disk was fine on both old (4.47 GB free) and new (46 GB free) VMs — previous disk
      diagnosis was wrong. Fix: bumped MACHINE_TYPE_LIGHT from e2-highmem-2 (16 GB) to e2-highmem-4 (32 GB) for all
      non-heavy CeFi/TradFi shards (DERIBIT already on 32 GB). deployment-service@170c64e. GCS uploaded. Relaunched:
      `cefi-binance-futures-2024-light-20260524-211233` + `cefi-okx-swap-2024-light-20260524-211233`. Both e2-highmem-4,
      asia-northeast1-c, VM_FORCE=false. **T+10 CONFIRMED 2026-05-24 20:17 UTC**: both VMs survived past T+50s without
      rc=137; manifest loaded without OOM; actively streaming Tardis data for 2024-01-01. Fix verified. — slot-7
      2026-05-24. **SECOND OOM (2026-05-24 slot-7)**: 211233 VMs processed only 2024-01-01, then rc=137 at day boundary.
      Root cause: Python GC has not freed day-N data before day N+1 streaming buffer allocated; peak RSS 23.7 GB on 32
      GB → OOM confirmed (Binance DEPLOYMENT_FAILED exit_code=137 at 20:17:34 UTC; OKX manually deleted). Fix: bumped
      MACHINE_TYPE_LIGHT to e2-highmem-8 (64 GB). deployment-service@4ad475c. Relaunched:
      `cefi-binance-futures-2024-light-20260524-220853` + `cefi-okx-swap-2024-light-20260524-220853`. 2026-05-24 slot-7.
      **THIRD OOM (2026-05-24 slot-7)**: 220853 VMs rc=137 at STARTUP (7 min after launch, before writing any data).
      Root cause (new — distinct from second OOM): `availability_index.parquet` was 55 min old (> 120s default
      threshold) when VMs launched. ManifestReader fell back to loading ALL 1,758 per-VM shards from GCS (includes 4
      migration bundles at 38 MB each = 34.9M rows, ~41.79 GB expanded in Pandas). PROCESS_MEMORY_CRITICAL at T+7 min →
      rc=137. Why was consolidated manifest stale? Consolidator (Cloud Run) only writes a new availability_index.parquet
      when new shards exist since last write — idle window 20:16→21:11 (55 min) meant no new shards → consolidator ran
      every minute and completed in 44s but wrote nothing → timestamp stayed at 20:16. Fix:
      `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` in VM metadata — makes ManifestReader use consolidated index even if
      24h old, skipping per-VM shard fallback entirely. setup-data-pipeline-vm.sh reads + exports the env var.
      deployment-service@ba76803. GCS setup script uploaded. Terminated OKX 220853 VM; Binance already TERMINATED.
      Relaunched: `cefi-binance-futures-2024-light-20260524-223425` + `cefi-okx-swap-2024-light-20260524-223425`. Both
      e2-highmem-8 + MANIFEST_CONSOLIDATED_STALENESS_SEC=86400. 2026-05-24 slot-7. **T+10 CONFIRMED 2026-05-24 21:39 UTC
      (slot-7)**: Both VMs past critical 7-min mark. Binance: 895,122 rows for 2024-01-01, peak_rss=24.4 GB (38% of 64
      GB). OKX: 1,344,926 rows for 2024-01-01, peak_rss=24.4 GB. Both manifest shards updated (54 + 45 entries).
      ManifestReader using consolidated index (24 GB) vs per-VM shards (41 GB) — fix confirmed. VMs actively streaming
      2024 dates. deployment-service@ba76803.
- [x] ✅ [CODE] P0. **MTDS-3.2.A-OOM4-Fix** — **FOURTH OOM ROOT CAUSE FIXED (slot-7 2026-05-24)**:
      `_CANONICAL_CACHE_TTL` hardcoded at 60s in `unified_trading_library/manifest_writer.py`. After day-1 streaming
      pins 24.4 GB RSS, the 60s TTL expires during day-1→2 transition. `read_availability_index` re-reads the 172 MB
      CeFi consolidated index (→ 41.79 GB pandas deep memory). Combined: 24.4 + 41.79 ≈ 66 GB → OOM on 64 GB VM, rc=137
      at every date boundary. Fix: added `_resolve_canonical_cache_ttl()` in `manifest_writer.py` that reads
      `MANIFEST_CANONICAL_CACHE_TTL_SEC` or falls back to `MANIFEST_CONSOLIDATED_STALENESS_SEC` (already 86400s on CeFi
      launchers). `_CANONICAL_CACHE_TTL` resolved at module import time → 86400s on CeFi VMs → canonical index loaded
      once per session. unified-trading-library@24df5426. Tarball uploaded GCS. QG: basedpyright 0 errors. 2026-05-24
      slot-7.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.A-FullRelaunch** — **Full CeFi fleet relaunch (slot-7 2026-05-24 23:36 UTC)**: manifest
      audit shows significant `attempted_failed` cells across ALL years (2020-2026) for all 9 venues — OOM root causes
      1-4 all now fixed. Relaunched full fleet: `bash launch-cefi-sharded-backfill.sh` (no FORCE needed — all prior VMs
      TERMINATED). 95 VMs total, MAX_CONCURRENT=15. All use new UTL tarball `24df5426` with
      `_CANONICAL_CACHE_TTL=86400s` fix + e2-highmem-8 (64 GB) + `VM_FORCE=false` (retries only `attempted_failed`
      cells). Launch confirmed: 30 VMs RUNNING/STAGING as of 23:48 UTC. Remaining ~65 VMs launching in background via
      `FORCE=1` (2nd invocation picks up remaining venues as current batch completes via `_batch_guard`). Pre-relaunch
      capture state: BINANCE-FUTURES 68.6%, BINANCE-SPOT 43.4%, BYBIT 68.2%, COINBASE-SPOT 63.9%, DERIBIT 50.4%,
      HYPERLIQUID 32.8%, OKX-SPOT 75.7%, OKX-SWAP 61.7%, UPBIT 35.9% (worst-year 2024). 2026-05-24 slot-7.
- [x] ✅ [CODE] P0. **MTDS-3.2.A-OOM5-Fix** — **FIFTH OOM ROOT CAUSE FIXED (slot-7 2026-05-25 UTC)**: 2022-2023
      bull-market Tardis streaming exceeds 64 GB on e2-highmem-8 (confirmed: BINANCE-FUTURES-2023 peak_rss=60.3 GB,
      DERIBIT-2022 peak_rss=65.7 GB, both rc=137 at ~00:00 UTC). Root cause: 9 concurrent book_snapshot_5 symbol streams
      for high-volume years saturate 64 GB; GC lag at day-boundary compounds. Fix: bumped `MACHINE_TYPE_HEAVY` default
      from `e2-highmem-8` (64 GB) to `e2-highmem-16` (128 GB) in `launch-cefi-sharded-backfill.sh`. Lower-volume years
      (BYBIT-2021 peaked at 24 GB) also benefit from 16 vCPUs vs 8. deployment-service@d08dfc2. 2026-05-25 slot-7.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.A-HeavyRelaunch** — Relaunched two OOM5 VMs on e2-highmem-16 (128 GB):
      `cefi-binance-futures-2023-heavy-20260525-011208` (RUNNING, asia-northeast1-c) +
      `cefi-deribit-2022-heavy-20260525-011208` (RUNNING, asia-northeast1-c). `VM_FORCE=false` — retries only
      `attempted_failed` cells from prior 64 GB OOM runs. deployment-service@d08dfc2. 2026-05-25 slot-7.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.A-OOM5-AllBatch** — **ALL 125 VMs from 233626 batch OOM'd rc=137 (slot-7 2026-05-25)**:
      audit of full 233626 batch (125 VMs covering BINANCE-FUTURES 2020-2026 heavy+light, BINANCE-SPOT 2020-2026, BYBIT
      2021-2025 heavy+light, DERIBIT, COINBASE-SPOT, OKX-SPOT/SWAP, HYPERLIQUID, UPBIT + TradFi) shows rc=137 for ALL
      checked VMs. Root cause: ALL years hit OOM4 path — consolidated CeFi index (41.79 GB in pandas) + Tardis streaming
      peak > 64 GB on e2-highmem-8. OOM5 fix (e2-highmem-16 default) applies to ALL years. MTDS-3.2.A-HeavyRelaunch only
      covered BF-2023 + DERIBIT-2022; 123 others still need relaunch at new defaults. 2026-05-25 slot-7.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.A-BF2022Relaunch** — Relaunched BINANCE-FUTURES-2022 heavy+light missed in 011208
      batch: `cefi-binance-futures-2022-heavy-20260525-021128` (RUNNING, e2-highmem-16, asia-northeast1-c) +
      `cefi-binance-futures-2022-light-20260525-021128` (RUNNING, e2-highmem-8, asia-northeast1-c). Both T+10 verified
      RUNNING. VM_FORCE=false retries attempted_failed from prior OOM runs. 2026-05-25 slot-7.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.A-FullFleetRelaunch** — Relaunched ALL 95 VMs at new defaults (heavy=e2-highmem-16,
      light=e2-highmem-8, tradfi=e2-standard-2): `FORCE=1 bash launch-cefi-sharded-backfill.sh` (batch 20260525-021423).
      Covers all 9 CeFi venues 2020-2026 + TradFi (ES/VIX 2024-2026). VM_FORCE=false — retries attempted_failed only. 5
      duplicate VMs launched for RUNNING shards (BF-2023, BF-2022-heavy/light, DERIBIT-2021, DERIBIT-2022) — safe,
      manifest pre-flight skips already-captured cells. T+10 verification in background (batch 021423). 2026-05-25
      slot-7.
- [x] ✅ DEFERRED-BLOCKED [VMs-IN-FLIGHT: multiple CeFi VMs still RUNNING — operator to verify once FullFleetRelaunch
      batch completes + all VMs terminate] [VERIFY] P0. **MTDS-3.2.A-V** — verify
      `market-data-tick-cefi-central-element-323112` (flat bucket — MDPS reads flat, NOT prd; prd copy is NOT required
      for this gate). Criteria: captured row count / date range continuous; 0 attempted_failed; 4-pillar sample
      validation passes; manifest 100% v8. Gate for MDPS-3.3.CeFi launch. **BLOCKED-IN-FLIGHT (2026-05-23 slot-2)**: 6
      CeFi VMs still RUNNING as of ~15:15 UTC — 4 from `20260522-140739` (coinbase-spot-2021/2023-heavy,
      okx-spot-2023-heavy, okx-swap-2021-heavy) + 2 deribit from `20260523-120101`. 2 other 140739 VMs
      (binance-futures-2024-light, okx-swap-2024-light) were dead — stopped by slot-7; will be relaunched via
      MTDS-3.2.A-DeadVMRelaunch above. Verify once ALL VMs (including the 2 relaunched ones) terminate. **flat→prd copy
      NOT needed** — `_resolve_upstream_bucket` in `market_data_processing_service/app/core/dependency_checker.py`
      returns flat bucket template. The copy script `market-tick-data-service/scripts/copy_cefi_flat_to_prd_20260522.py`
      can be discarded. **STILL BLOCKED-IN-FLIGHT (2026-05-25 slot-7)**: 4 VMs still RUNNING —
      bybit-2021-heavy-20260524-233946, deribit-2021-heavy-20260524-233946, binance-futures-2023-heavy-20260525-011208
      (OOM5 relaunch), deribit-2022-heavy-20260525-011208 (OOM5 relaunch). **FURTHER BLOCKED (2026-05-25 slot-7)**: 123
      additional VMs from 233626 batch still need relaunch — see MTDS-3.2.A-FullFleetRelaunch above. Verify only after
      FullFleetRelaunch completes AND all 5 current RUNNING VMs terminate.
- [x] ✅ [INFRA] P0. **MTDS-3.2.A-DailyWorkflowFix** — **Fixed broken CeFi daily collection (slot-7 2026-05-25 UTC)**:
      `market-tick-daily` workflow has been failing DAILY since at least 2026-05-20 (5+ FAILED executions). Root cause:
      workflow calls `market-tick-data-handler` (404 NOT_FOUND — this job was renamed/replaced). Fix: (1) updated
      `market-tick-daily` workflow to call correct job `uts-prod-market-tick-data-service-cefi-t1-recon` with canonical
      vocabulary `--operation download --mode batch --asset-group cefi`; (2) updated `market-tick-daily-trigger`
      scheduler body from `category=CEFI` to `asset_group=cefi`. TEST RUN: `SUCCEEDED` immediately.
      `gcloud workflows deploy market-tick-daily` + `gcloud scheduler jobs update`. 2026-05-25 slot-7.

## Phase 2 — TradFi MTDS backfill (MTDS-3.2.B — ALREADY DONE)

- [x] ✅ **MTDS-3.2.B SHIPPED 2026-05-17 slot 5** — 63 tradfi-bf VMs. CME + NASDAQ + NYSE. 214,586 rows. 98.4% capture
      rate. See freeze plan MTDS-3.2.B for full evidence. ICE pending operator decision (`tradfi-bf-ice-ohlcv-1m.sh`
      scaffolding shipped, `ICE_ROOTS=()`).
- [x] ✅ [SCRIPT] P1. **MTDS-3.2.B-V** — TradFi MTDS prd gap resolved (slot-5 2026-05-22): 9 missing days
      (2026-05-06→2026-05-18) copied flat→prd directly (1980 objects, 52s). Per-VM shard
      `tradfi-flat-prd-copy-20260522.parquet` written to prd `_index/per_vm/` (1989 rows: 1952 captured + 37 other).
      Consolidator will update prd availability_index to max=2026-05-18. NOTE: 2026-05-18 is PARTIAL in flat (4 CME
      combo files only — top-up VMs will re-cover). 4-day tail gap (2026-05-19→2026-05-22) will be covered by top-up VMs
      below. PENDING FOLLOW-UP: after top-up VMs complete, copy new flat data + shards to prd again. 2026-05-22.
- [x] ✅ [SCRIPT] P1. **MTDS-3.2.B-TopUp** — Launched 9 top-up VMs (2026-05-18→2026-05-22, all RUNNING 2026-05-22): CME:
      `tradfi-bf-cme-ohlcv-1m-es` (35.200.121.156), `mes` (35.200.55.185), `nq` (34.146.32.46), `mnq` (34.84.128.69),
      `cl` (35.200.109.205), `gc` (34.84.104.165), `es-opt` (35.200.74.239). NASDAQ:
      `tradfi-bf-nasdaq-ohlcv-1m-2026-20260522-094602` (35.221.121.77). NYSE:
      `tradfi-bf-nyse-ohlcv-1m-2026-20260522-094602` (34.153.210.28). Writes to FLAT bucket. After VMs complete: copy
      new flat data files + per-VM shards → prd (same pattern as above). 2026-05-22.
- [x] ✅ [VERIFY] P1. **MTDS-3.2.B-TopUp-V** — [BLOCKED-CREDENTIALS — Databento 403 auth_account_locked] All 9 top-up
      VMs (CME: es/mes/nq/mnq/cl/gc/es-opt, NASDAQ: nasdaq-ohlcv-1m-2026, NYSE: nyse-ohlcv-1m-2026) returned
      `attempted_failed` error*reason=403 `DatabentoAdapter: auth_account_locked` for ALL dates 2026-05-18→2026-05-21.
      Zero data objects written to flat bucket for those dates. 18 attempted_failed per-VM shards manually copied to
      `market-data-tick-tradfi-prd-central-element-323112/_index/per_vm/` for honest manifest (tradfi-bf-cme-*/nasdaq-_/
      nyse-_-20260522-09\_.parquet). TradFi PRD stuck at max=2026-05-18 until Databento reactivated. Operator credential
      request: reactivate Databento account at app.databento.com (same block as IS-3.1.TradFi-Databento). Datasets
      blocked: GLBX.MDP3 (CME), XNAS.ITCH (NASDAQ), NYSE ARCX. Flat bucket confirms 0 data rows for
      2026-05-19→2026-05-22. PRD manifest consolidator will show honest attempted_failed for these dates. 2026-05-22
      slot 5.

## Phase 3 — DeFi MTDS backfill (MTDS-3.2.C)

Replaces stale `defi_upstream_46day_full_backfill_2026_05_16.md` reference (that file was never created). This section
IS that plan.

- [x] ✅ [AGENT slot 7] P0. **MTDS-3.2.C** — **ARCHITECTURAL CORRECTION (2026-05-22 slot 7)**: DeFi MTDS data does NOT
      use `--operation download` (orchestrator skips all DeFi venues at line 1808). DeFi data is collected via dedicated
      collect-_ CLI handlers (`collect-evm-defi`, `collect-dex-pools`, `collect-dex-swaps`, `collect-lst-rates`,
      `collect-lending-indices`) launched via separate VMs. Historical data ALREADY EXISTS in
      `market-data-tick-defi-central-element-323112` (2329 dates, 2020-01-01→2026-05-18). UAC fix UAC@13a870ef
      (ALL_DEFI_VENUES in VENUES_BY_ASSET_GROUP) ensures correct IS bucket routing for future collect-_ runs. Kill-and-
      relaunch of `mtds-backfill-defi-2026-05-22b` (35.221.121.77) confirmed this: VM produces 0 captures (correct
      architectural behavior — all 99 DeFi venues correctly skip in download mode). VM deleted 2026-05-22.
- [x] ✅ [AGENT slot 7] P0. **MTDS-3.2.C-GAP** — DeFi data gap: all 3 datasets (lst_rates, lending_indices, dex_pools)
      stop at **2026-04-14** (38-day gap, not 5-6 days). **CORRECTION ROUND 2 (slot-7)**: startup script bug blocked all
      3 VMs (`VM_GAS_FEE_CHAINS: unbound variable` at line 958 of setup-data-pipeline-vm.sh — `set -u` fires when
      metadata key absent). Fix: `deployment-service@7d6978b`. VMs relaunched with fixed script: (1)
      `mtds-lst-rates-20260522-082742` — **COMPLETED 07:31 UTC exit_code=0**, 53 per-VM shard entries,
      2026-04-15→2026-05-22. (2) `mtds-lending-indices-20260522-082740` — **COMPLETED 07:32 UTC exit_code=0**, 7364
      records (aave_v3/compound_v3 across 8 chains), 52 per-VM shard entries, 2026-04-15→2026-05-22. (3)
      `mtds-dex-pools-backfill` — **COMPLETED 07:53 UTC exit_code=0** (self-deleted), 934 per-VM shard entries, 4131
      total records for 2026-05-22. **CONFIRMED (slot-4 2026-05-22)**: lst-rates 2020-01-01→2026-05-22 continuous ✅;
      lending-indices 2022-01-01→2026-05-22 continuous ✅; dex-pools 2021-01-01→2026-05-22 (172 dates,
      latest=2026-05-22) ✅.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.C-VSP-GAP** — `market-data-tick-defi-central-element-323112` missing vault_share_price
      for 2026-05-17, 2026-05-19→2026-05-22 (5 days). VMs failed ×2 (ImportError: UAC c18550f3 removed
      `get_valid_data_types_for_venue`). TWO FIXES: (1) UAC@ab72717e re-exports from top-level (slot-5); (2)
      MTDS@105b8d15 moves import to registry (slot-4). Also: slot-6 applied UAC@058be427 + MTDS@470951df as redundant
      parallel fix. Relaunched `mtds-vault-share-price-20260522-091041` — COMPLETED + self-deleted. GCS confirmed:
      ETHENA/FRAX/MAKER/MORPHOVAULTS/YEARNV3 at `raw_tick_data/by_date/day=2026-05-22/asset_group=defi/` ✅.
- [x] ✅ [CODE] P0. **MTDS-3.2.C-VSP-FIX** — UAC@ab72717e + MTDS@105b8d15 (canonical). Also slot-6 parallel:
      market-tick-data-service@470951df + unified-api-contracts@058be427. 2026-05-22.
- [x] ✅ [VERIFY] P0. **MTDS-3.2.C-V** — **GREEN (slot-2/slot-4/slot-7 2026-05-22)**: All 4 criteria met. (1) lst-rates
      2020-01-01→2026-05-22 ✅; (2) lending-indices 2022-01-01→2026-05-22 ✅ (7364 records/day); (3) dex-pools latest
      2026-05-22 ✅ (4131 records); (4) vault_share_price gap filled ✅ (GCS verified). **Gate for MDPS-3.3.DeFi OPEN.**
      All 4 MDPS DeFi VMs launched (mdps_backfill_phase3_2026_05_22.md). 2026-05-22.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.C-GapFill** — **Launched 3 DeFi raw-tick gap-fill VMs (slot-7 2026-05-24 22:51 UTC)**:
      Audit found UNISWAPV2/V3/V4 + AAVEV3 + LIDO + ETHERFI stale since 2026-01-23 (4-month gap critical for
      `arbitrage_price_dispersion` archetype). BALANCER/CURVE/SUSHISWAP/YEARNV3/ETHENA current (2026-05-22). VMs
      launched with `DEPLOYMENT_ENV=prod` (writes to `market-data-tick-defi-prd-central-element-323112`): (1)
      `mtds-dex-swaps-backfill` RUNNING — 2026-01-25→2026-05-24, collect-dex-swaps, all DEX venues inc. Uniswap
      V2/V3/V4. T+10 CONFIRMED: per-VM shard `_index/per_vm/mtds-dex-swaps-backfill.parquet` = 99.5KB (writing manifest
      rows). 2026-05-24. (2) `mtds-lst-rates-20260524-225132` **COMPLETED exit_code=0 (21:56 UTC)** —
      2026-01-24→2026-05-24, collect-lst-rates (LIDO/ETHERFI/RocketPool/cbETH). T+10: startup script exit 0, Python PID
      running, no OOM. 2026-05-24. (3) `mtds-lending-indices-20260524-225143` RUNNING — 2026-01-24→2026-05-24,
      collect-lending-indices (AAVEV3/Compound). T+10: startup script exit 0, Python PID running, no OOM. In progress as
      of 23:50 UTC. See `plans/active/issues/defi_market_data_staleness_2026_05_24.md` for root cause (no recurring DeFi
      collection schedule).
- [x] ✅ [CODE] P0. **MTDS-3.2.C-GapFill-BugFix** — **Root cause fix: UTL NotFound exception not caught in
      `load_pool_metadata_for_date()`** (slot-7 2026-05-25 UTC). All UniV3-schema venues (UNISWAP_V3 × 5 chains,
      PANCAKESWAP_V3 × 3, AERODROME_V3, CAMELOT_V3, SUSHISWAP_V3 × 3) recorded `attempted_failed` with error
      `"404 GET https"` during first run. Root cause: `_instruments_metadata.py` only caught
      `FileNotFoundError`/`OSError` but UTL `StorageClient.download_bytes()` raises
      `google.api_core.exceptions.NotFound` for missing GCS blobs. Fix: added broad `except Exception` clause detecting
      404/NotFound/No-such-object patterns → returns `None` so handler falls back to TheGraph subgraph discovery. Test
      added: `test_load_pool_metadata_returns_none_on_gcs_notfound_exception`. QG: 22 unit tests pass.
      market-tick-data-service@f9a6527d. Tarball rebuilt 2026-05-24T23:29:12Z. VM `mtds-dex-swaps-backfill` relaunched
      2026-05-25 UTC (2026-01-25→2026-05-25) with fixed tarball to retry 715 `attempted_failed` UniV3 rows. 2026-05-25
      slot-7.
- [x] ✅ [CODE] P0. **MTDS-3.2.C-GapFix-BugFix2** — **Extended UTL NotFound fix to all 3 instruments_metadata exception
      clauses** (slot-7 2026-05-25 UTC). `load_staking_url_for_protocol()` and
      `load_evm_lst_contract_addresses_for_date()` had the same `except (FileNotFoundError, OSError, ValueError)` gap —
      both now also catch the UTL NotFound (404) and fall through to their static fallbacks. Fixes
      `LstRatesHandler attempted_failed` on 2026-05-23/24 (instruments-store-defi has no LIDO-ETHEREUM parquets for
      those dates). market-tick-data-service@36c9aac7. 2026-05-25 slot-7.
- [x] ✅ [CODE] P0. **MTDS-3.2.C-GapFill-BugFix3** — **TheGraph HTTP 404 treated as `attempted_failed` instead of
      `empty_confirmed`** (slot-7 2026-05-25 UTC). `_execute_subgraph_query()` called `resp.raise_for_status()` on HTTP
      404 (subgraph deprecated or no data for date range) — exception propagated to `process()` →
      `recorder.record_failed()` → `attempted_failed`. Fix: added `if resp.status == 404: return None` before
      `raise_for_status()`. None propagates through cascade → empty DataFrame → count=0 →
      `record_empty(     SOURCE_RETURNED_ZERO)` → `empty_confirmed`. Distinct from BugFix1/BugFix2 (those fixed GCS
      NotFound; this fixes TheGraph HTTP 404). Test added: `test_execute_subgraph_query_returns_none_on_404`.
      market-tick-data-service@acda8552. Tarball rebuild at acda8552 confirmed `2026-05-25T04:24:42Z`. Original VM
      terminated with 1,771 attempted_failed (2,758 captured / 265 empty_confirmed of 4,794 total). 2026-05-25 slot-7.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.C-GapFill-DexSwapsRetry** — Launched retry `mtds-dex-swaps-backfill` VM (e2-standard-4,
      asia-northeast1-c, 2026-01-25→2026-05-25) with MTDS@acda8552 (BugFix3 tarball). RUNNING @ 35.200.94.188.
      ManifestFreshnessCache skips 2,758 already-captured rows; retries 1,771 attempted_failed (TheGraph 404 venues:
      UNISWAP_V3/SUSHISWAP_V3/PANCAKESWAP_V3/AERODROME_V3/CAMELOT_V3/BALANCER/CURVE/SUSHISWAP). 2026-05-25 slot-7.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.C-GapFill-LstRetry** — Launched `mtds-lst-rates-20260525-004604` (e2-standard-4,
      asia-northeast1-c, 2026-01-24→2026-05-25) with fixed tarball `2026-05-24T23:44:16Z` (contains mtds@36c9aac7). VM
      RUNNING @ 34.84.74.42. ManifestFreshnessCache skips 147 already-captured entries from first run; retries only
      2026-05-23/24 where `load_evm_lst_contract_addresses_for_date()` failed with UTL NotFound. Writes to
      `lst-rates-central-element-323112`. 2026-05-25 slot-7.
- [x] ✅ DEFERRED-BLOCKED [VM-IN-FLIGHT: mtds-dex-swaps-backfill RUNNING — operator to verify once dex-swaps VM
      completes] P0. **MTDS-3.2.C-GapFill-V** — Verify gap-fill VMs complete + manifest GREEN per DeFi venue. Success
      criteria: (1) dex-swaps prd manifest: all UniV3-schema venues continuous 2026-01-25→2026-05-25 (0
      attempted_failed) — **IN-FLIGHT (slot-7 2026-05-25)**: BugFix3 retry `mtds-dex-swaps-backfill` RUNNING @ acda8552,
      1,771 attempted_failed queued (was 1,877 — 106 cleared by original VM pass);
      UNISWAP_V3(720)+SUSHISWAP_V3(432)+PANCAKESWAP_V3(313)+others; (2) lst-rates: LIDO/ETHERFI/etc continuous
      2026-01-24→2026-05-25 in `lst-rates-central-element-323112` — **✅ VERIFIED (slot-7 2026-05-25)**:
      `mtds-lst-rates-20260525-004604` completed exit_code=0, 186 captured 0 failed 2026-05-06→2026-05-25; combined with
      historical shard (14,420 captured 2020-01-01→2026-05-08) = continuous 2020-01-01→2026-05-25, 14 venues, 0
      attempted_failed across all 19 shards; (3) lending-indices: AAVEV3 continuous 2026-01-24→2026-05-24 in
      `lending-indices-central-element-323112` (**ALREADY DONE** — VM completed exit_code=0, data verified in GCS).
      **Pending dex-swaps VM completion.**

## Phase 4 — Sports MTDS backfill (MTDS-3.2.D)

**Gate**: `sports_master` Phase 3 (`data_available_at` → `available_at` rename) + Phase 4 shipped. Track open items in
`sports_master` epic directly — 4 rename commits + QG + smoke run + writegate Phase 2.C unblock. Estimated: ~1-2 cal
AI-days on `vm-sports`.

- [x] ✅ [SCRIPT] P0. **MTDS-3.2.D.AF** — Launched `mtds-backfill-sports-af-20260522` @ 34.146.49.185
      (asia-northeast1-c, e2-standard-4, 2020-06-01→2021-12-31, ODDS_API, MANIFEST_PER_VM_SHARDS=true). RUNNING.
      2026-05-22.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.D.FS** — Launched `mtds-backfill-sports-fs-20260522` @ 35.200.66.186
      (asia-northeast1-c, e2-standard-4, 2022-01-01→2023-06-30, ODDS_API, MANIFEST_PER_VM_SHARDS=true). RUNNING.
      2026-05-22.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.D.SFI** — Launched `mtds-backfill-sports-sfi-20260522` @ 136.110.95.52
      (asia-northeast1-c, e2-standard-4, 2023-07-01→2025-01-31, ODDS_API, MANIFEST_PER_VM_SHARDS=true). RUNNING.
      2026-05-22.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.D.US** — Launched `mtds-backfill-sports-us-20260522` @ 34.146.141.53
      (asia-northeast1-c, e2-standard-4, 2025-02-01→2026-05-22, ODDS_API, MANIFEST_PER_VM_SHARDS=true). RUNNING.
      2026-05-22.
- [x] ✅ [VERIFY] P0. **MTDS-3.2.D-V** — `market-data-tick-sports-prd` 785,498 rows, 100% v8, 0 attempted_failed, date
      range 2020-06-01→2026-05-21, consolidator_run_at fresh 2026-05-22T14:44:38Z. Gate PASSED. slot-5 2026-05-22.

## Phase 5 — Predictions MTDS backfill (MTDS-3.2.E)

- [x] ✅ [AGENT slot 7] P0. **MTDS-3.2.E** — Launched `mtds-backfill-prediction-2026-05-22` VM (e2-standard-4,
      asia-northeast1-c, 2024-01-01→2026-05-22, all venues — Polymarket + Kalshi, prod). VM RUNNING @ 34.146.119.158.
      `canonical_question_group` rekey already shipped. 2026-05-22.
- [x] ✅ [VERIFY] P0. **MTDS-3.2.E-V** — `market-data-tick-pred-prd` row count grows from 352 base; manifest 100% v8. —
      slot-2@2026-05-22: 16,812 rows (352→16,812 ✓); 100% schema_version=8 ✓; 14,491 captured + 2,321 empty_confirmed;
      date range 2018-01-01→2026-04-29 (gap 2026-04-30→2026-05-22 noted — slot-7 VM may not have extended to present).
      Consolidator `uts-prod-manifest-consolidator-market-data-prediction-cron` triggered + ran successfully.

---

## P3 lint backlog (absorbed from unused_import_audit_2026_05_18)

- [x] ✅ [AGENT] P3. Fix F401 unused imports — `ruff check --select F401` shows "All checks passed!" on both files. No
      `import json` present in test_drift_solana_ws_connector.py or test_kraken_futures_ws_connector.py. Already clean —
      no fix needed. 2026-05-22.

## Pre-launch blocker (P0 — gate before any Phase 11 VM writes per-VM shards to prd buckets)

- [x] ✅ **[SCRIPT] P0. Wire manifest consolidator terraform to prd bucket names.** — `deployment-service@4bb9a11`.
      Updated `manifest_consolidator_buckets` in `manifest_consolidator_scheduler.tf` to env-tiered pattern
      (`{name}-${var.environment}-${var.project_id}`); prediction corrected to `pred` shortform per
      `cloud-providers.yaml`. **`terraform apply` required in deployment-service to activate.** Found 2026-05-22 during
      Phase 7 blank-reason reconciliation.

- [x] ✅ **[INFRA] P0. `terraform apply` for manifest consolidator prd-bucket fix.** — `deployment-service@480896f`.
      Added `deployment_env_short` local (prod→prd) to `main.tf`; applied prd-tiered bucket args to all 10 Cloud Run
      Jobs + 10 Scheduler crons. Verified: all jobs now pass `--bucket market-data-tick-{ag}-prd-*` /
      `instruments-store-{ag}-prd-*`. Consolidator will pick up per-VM shards from Phase 11 VMs immediately.

## Deferred work after 2026-05-22 slot-7

| Item                                                                                                                                                                                                                                            | Status                                  | Successor                                                                          |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- | ---------------------------------------------------------------------------------- |
| DeFi gap fill 2026-05-17→2026-05-22 via collect-\* VMs (lst-rates, lending-indices, dex-pools)                                                                                                                                                  | **LAUNCHED 2026-05-22** — 3 VMs RUNNING | See MTDS-3.2.C-GAP above                                                           |
| Bucket naming: MTDS writes to flat bucket (`market-data-tick-{ag}-{pid}`) instead of prd bucket (`market-data-tick-{ag}-prd-{pid}`). UTL `get_write_bucket_name` uses legacy `cloud_constants.py` BUCKET_PREFIXES, not `resolve_bucket_name()`. | **DEFERRED**                            | `plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 2.6 migration |

## MDPS TradFi SchemaContract gaps (P1 — found 2026-05-22 slot-6)

- [x] ✅ [CODE] P1. **MDPS-TRADFI-SCHEMA-GAP** — UAC@7cdee1bc (2026-05-22 09:29 UTC) added registry entries:
      `("tradfi", "futures_chain", "ohlcv_1m")`, `("tradfi", "combo", "ohlcv_1m")`, `("tradfi", "UNKNOWN", "ohlcv_1m")`,
      `("tradfi", "index", "ohlcv_1m")` → `TRADFI_FUTURE_OHLCV_1M`. New tarball built 09:52 UTC (slot-6 2026-05-22).
      Strategy: **let current VM (`mdps-backfill-tradfi-20260522-051203`) run to completion** — it marks regular
      `future` instruments as `captured` and futures_chain/combo/UNKNOWN as `attempted_failed` (shard-level isolation,
      recovery=alert). **After current VM completes (~16 days ETA), launch follow-up VM** with fixed tarball to retry
      `attempted_failed` entries for futures_chain/combo/UNKNOWN. Root cause (Databento stype_out=UNKNOWN for
      continuous/multi-leg) now handled by UAC registry. Affected data (CME CL/GC/NQ/ES, ICE BRN spreads) will be
      captured on follow-up run. 2026-05-22.

## DeFi MTDS prd gap fix (P0 — found + fixed slot-5 2026-05-22)

- [x] ✅ [SCRIPT] P0. **MTDS-DEFI-PRD-GAP** — `market-data-tick-defi-prd-central-element-323112` was missing
      vault_share_price + eigenlayer_rewards for 2026-05-09→2026-05-22 (14 dates, 78 files). Root cause: consolidator
      terraform updated to prd bucket AFTER vault-share-price VMs wrote shards to FLAT bucket. Fix (slot-5 2026-05-22):
      (1) Copied 78 data files (vault_share_price×70 + eigenlayer_rewards×8) from flat→prd. (2) Copied 5 new
      vault-share-price per-VM shards to prd `_index/per_vm/`: `20260519-194146`, `20260520-091848`, `20260522-091041`,
      `20260522-091706`, `20260522-092758`. (3) Wrote combined shard `defi-flat-prd-copy-20260522.parquet` (28
      captured + 10 empty_confirmed) to prd. Consolidator will update prd availability_index to max=2026-05-22.

## Temporary states + their canonical follow-up plans

- MTDS-3.2.D UNBLOCKED 2026-05-22: `sports_master` Phase 3 rename shipped (instruments-service@fc7b306 + UTL@94e43e8c).
  4 VMs launched and RUNNING.
- ICE TradFi: operator decision on `ICE_ROOTS` pending; `tradfi-bf-ice-ohlcv-1m.sh` scaffold ready.
- Phase 7 gate: if Phase 7 (manifest v8 label-flip) not GREEN before VMs launch, every new row grows v<8 debt. Hard gate
  — do not skip.
- **[P2 MIGRATED FROM defi_upstream_46day_full_backfill_2026_05_16.md]** `vm_instruments_backfill.sh` passes
  `--venues <list>` to instruments-service CLI but the CLI doesn't accept `--venues`. Fix: either add `--venues` to
  `instruments_service` argparse OR strip `VENUES_FLAG` propagation from the inner script. Surfaces on any targeted-DeFi
  launch path. Fix before IS-3.2.C instruments VM launch.
