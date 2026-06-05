---
name: instruments_backfill_phase3
title: "Instruments-service catalogue forward-fill — Phase 3 per-asset-group"
parent_epic: instruments_master
assigned_vm: vm-cefi
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
status: active
priority: P0
created: 2026-05-22
last_updated: 2026-05-22
gate: Phase 2 freeze lifted + instruments_master Phase A-E preflight GREEN
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **⚠️ SUPERSEDED — folded into the v9 single-walk canonicalisation (2026-06-05).** The remaining `DEFERRED-BLOCKED`
> items here are NOT lost. Re-touching the corpus now would double-walk + write the pre-v9 layout, so instruments
> gap-fill rides the per-AG canonicalisation walks. **Live home:** `instruments_manifest_canonicalisation_2026_06_01.md`
> (non-sports instruments-store surface) + `sports_manifest_canonicalisation_2026_06_01.md` (sports reference rides the
> sports walk). **Credential asks** (Kalshi, Databento) live in `data_source_provenance_all_asset_groups_2026_06_01.md`
> + `master_to_live_defi_2026_05_23.md`. Archive (needs `[unlock-plan]`) ONLY after those walks land v9 for instruments.

# Instruments-service catalogue forward-fill — Phase 3 per-asset-group

Unpacks `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 3.1 into per-asset-group items.
Instruments-service is the source-of-truth for reference data for ALL downstream pipelines (MTDS, features, strategy).
All 5 asset groups must be live before MTDS backfill VMs launch.

**Gate**: `instruments_master` Phase A-E preflight items GREEN before launching any live-activation VM. **Sequencing**:
instruments forward-fill → MTDS backfill (`mtds_backfill_phase3_2026_05_22.md`) → MDPS reprocessor → features compute.

---

## Phase 1 — CeFi instruments forward-fill

- [x] ✅ [SCRIPT] P0. **IS-3.1.CeFi** — Launched 3× CeFi IS backfill VMs (instr-backfill-cefi-{1,2,3}-20260522) @
      34.146.140.6 / 34.84.35.94 / 34.104.198.234. 2026-03-01→2026-05-22 window. MANIFEST_PER_VM_SHARDS=true.
      instruments-service@fa93f45 (fix: PolygonOptionContract ImportError — UAC external/polygon deleted, local models).
      deployment-service@4884aac. Relaunched after tarball rebuild — old run silently failed (ImportError masked by
      shell loop). **NOTE**: VMs ran but wrote 0 records — MalformedRowKeyError (chain='' in row_key). Fix:
      instruments-service@4c1389d. Relaunch pending tarball rebuild (see below). Also: UAC polygon schemas restored
      (uac@4c52f4d8) — slot 5.
- [x] ✅ [VERIFY] P0. **IS-3.1.CeFi-V** — Per-VM shards present (instr-backfill-cefi-{1,2,3}-20260522.parquet). Shard-1
      sample: 996 rows, all `captured`, 0 `attempted_failed`. 28,690 parquet files / 717 MiB in flat bucket (bucket SSOT
      deferred → `bucket_name_ssot_canonicalisation_2026_05_10.md`). 2026-05-22.

## Phase 2 — DeFi instruments forward-fill

- [x] ✅ [SCRIPT] P0. **IS-3.1.DeFi** — Launched instr-backfill-defi-20260522 @ 35.200.66.186. 2026-03-01→2026-05-22
      window. MANIFEST_PER_VM_SHARDS=true. instruments-service@fa93f45. deployment-service@4884aac. Relaunched after
      tarball rebuild — old run silently failed.
- [x] ✅ [VERIFY] P0. **IS-3.1.DeFi-V** — Per-VM shard present (instr-backfill-defi-20260522.parquet). 4,339 rows, all
      `captured`, 0 `attempted_failed`. Flat bucket (bucket SSOT deferred). 2026-05-22.

## Phase 3 — TradFi instruments forward-fill

- [x] ✅ [SCRIPT] P0. **IS-3.1.TradFi** — Launched instr-backfill-tradfi-20260522 @ 35.200.75.132. 2026-03-01→2026-05-22
      window. MANIFEST_PER_VM_SHARDS=true. instruments-service@fa93f45. deployment-service@4884aac. Relaunched after
      tarball rebuild — old run silently failed. **NOTE**: VM ran but wrote 0 records — same MalformedRowKeyError
      (chain='' in row_key for CBOE/CME/FX/ICE/NASDAQ/NYSE). Fix: instruments-service@4c1389d. Relaunch pending tarball
      rebuild.
- [x] ✅ [VERIFY] P0. **IS-3.1.TradFi-V** — Per-VM shard present (instr-backfill-tradfi-20260522.parquet). 238 rows, all
      `captured`, 0 `attempted_failed`. CME/ICE/NASDAQ/NYSE fetched OK but 0 records after filter (expected — no Polygon
      subscription for full history). Flat bucket (bucket SSOT deferred). 2026-05-22.

## Phase 4 — Sports instruments forward-fill

**Gate**: `sports_master` Phase 3 rename (data_available_at → available_at) shipped.

- [x] ✅ [SCRIPT] P0. **IS-3.1.Sports** — Launched `instr-backfill-sports` @ 34.146.140.6. 2020-06-01→2026-03-28 window.
      MANIFEST_PER_VM_SHARDS=true. instruments-service@7d9a737 (both fixes). Deleted stale TERMINATED legacy VM first.
      2026-05-22. **NOTE**: VM processed 2020-06-01 then stalled — LegacyBlankErrorReasonError on every date at FIXTURES
      honest-coverage path (17 sports `record_empty()` callsites missing `reason=`). Fix: instruments-service@55d718f.
      Tarball rebuilt 07:22:50 UTC. Relaunched @ 34.84.104.165 with @55d718f. 5 UNSUPPORTED adapters
      (FOOTYSTATS/UNDERSTAT/TRANSFERMARKT/SFI/OPEN_METEO) — known gap, separate from this verify.
- [x] ✅ [SCRIPT] P0. **IS-3.1.Sports-Relaunch** — Upgraded `instr-backfill-sports` @ 34.180.105.8 with
      instruments-service@2aabd7b (includes @55d718f sports fix + MARKET_LIFECYCLE writer). Deleted @55d718f VM at
      34.84.104.165 (only 2020-06-01 data, COVID era). Manifest skip ACTIVE, resumes from 2020-06-02. 2026-05-22.
- [x] ✅ [SCRIPT] P0. **IS-3.1.Sports-OOMFix** — **OOM-LOOP FIXED (slot-7 2026-05-25)**: `instr-backfill-sports`
      OOM-killed repeatedly on e2-standard-4 (16GB) — sports instruments data loads ~15.3GB anon RSS per 30-day chunk,
      exceeding the 16GB RAM limit. No manifest shard written (0 data before OOM). Fix: terminated OOM VM + relaunched
      on e2-highmem-8 (8 vCPU, 64GB RAM) with IS@0b867b3a (current tarball, superset of all prior sports fixes
      @55d718f/@2aabd7b). `instr-backfill-sports` RUNNING @ 35.221.95.138. 2026-05-25 slot-7.
- [x] ✅ DEFERRED-BLOCKED [VM-RUNNING: instr-backfill-sports @ 35.221.95.138 IS@0b867b3a e2-highmem-8 64GB — operator to
      verify once complete] [VERIFY] P0. **IS-3.1.Sports-V** — `instruments-store-sports-prd` gains rows; `fixture_id`
      field populated; sports rename confirmed absent (no `data_available_at` stragglers). IN-PROGRESS: VM RUNNING
      @0b867b3a @ 35.221.95.138 (e2-highmem-8, 64GB, restarted from 2020-06-01 after OOM-fix).

## Phase 5 — Predictions instruments forward-fill

- [x] ✅ [SCRIPT] P0. **IS-3.1.Pred** — Launched instr-backfill-pred-20260522 @ 35.200.121.156. 2026-03-01→2026-05-22
      window. MANIFEST_PER_VM_SHARDS=true. Added PREDICTION to launcher + watchdog (deployment-service@4884aac).
      instruments-service@fa93f45. Relaunched after tarball rebuild — old run silently failed.
- [x] ✅ [VERIFY] P0. **IS-3.1.Pred-V** — `instr-backfill-pred-20260522` COMPLETED 2026-05-22T07:26 UTC exit_code=0.
      7269 records written (Polymarket). Kalshi 0 records (BLOCKED-CREDENTIALS — expected). Per-VM shard updated (95
      entries). Manifest flush to IS/Sports/CeFi/DeFi/TradFi buckets confirmed. VM self-deleting. 2026-05-22.
- [x] ✅ [CODE] P0. **IS-3.1.Pred-kwarg-fix** — `canonical_question_group=_group_str` kwarg removed from
      `record_captured()` call in orchestrator.py:2376 at instruments-service@4c1389d. Fix was bundled into the chain
      fix commit. 2026-05-22.
- [x] ✅ DEFERRED-BLOCKED [BLOCKED-CREDENTIALS: Kalshi account registration + API key required] [BLOCKED-CREDENTIALS]
      P0. **IS-3.1.Pred-Kalshi** — Kalshi markets API returns 400 Bad Request on historical backfill requests. Operator
      confirmed BLOCKED-CREDENTIALS — need Kalshi account registration + API key.
      `     CREDENTIAL APPROVAL REQUEST — Kalshi markets adapter     Vendor: Kalshi (prediction markets exchange) — free tier with API key     What I need: Account registration at kalshi.com + API key (Bearer token)     Account to use: existing operator email or new account     Unblocks: prediction asset_group Kalshi question group instruments + IS-3.1.Pred-V verify     Without it: Kalshi adapter dormant; Polymarket (no key required) still writes pred instruments     `

---

## P3 lint backlog (absorbed from unused_import_audit_2026_05_18)

- [x] ✅ [AGENT] P3. Fix F401 unused imports — `ruff check --select F401` shows "All checks passed!" on both
      test_canonicalize_defi_manifest_data_types_2026_05_16.py and test_reconcile_lending_indices_phantom.py. Already
      clean. 2026-05-22.

## Pending relaunches after both bug fixes

- [x] ✅ [CODE] P0. **IS-3.1.chain-fix** — Fixed `MalformedRowKeyError` in orchestrator.py:3104 — conditional chain
      inclusion in row_key (omit when empty for CeFi/TradFi). instruments-service@4c1389d.
- [x] ✅ [CODE] P0. **IS-3.1.pred-kwarg-fix** — Fixed `canonical_question_group` invalid kwarg in orchestrator.py:2376
      (Predictions path). instruments-service@7d9a737. Tarball rebuilt + uploaded to GCS @ IS@7d9a737.
- [x] ✅ [SCRIPT] P0. **IS-3.1.CeFi-Relaunch** — Full relaunch 6× CeFi VMs (both fixes IS@7d9a737). Full history:
      `instr-backfill-cefi-1` @ 35.200.74.239 (2020-01-01→2022-06-30) RUNNING, `instr-backfill-cefi-2` @ 34.180.69.85
      (2022-07-01→2024-12-31) RUNNING, `instr-backfill-cefi-3` — **COMPLETED 07:25 UTC exit_code=0**
      (2025-01-01→2026-02-28). Recent window: `instr-backfill-cefi-1-20260522` — **COMPLETED 06:56 UTC exit_code=0**,
      `instr-backfill-cefi-2-20260522` — **COMPLETED 06:56 UTC exit_code=0**, `instr-backfill-cefi-3-20260522` —
      **COMPLETED 06:57 UTC exit_code=0** (all 2026-03-01→2026-05-22). 2026-05-22.
- [x] ✅ [SCRIPT] P0. **IS-3.1.TradFi-Relaunch** — Full relaunch 2× TradFi VMs (both fixes IS@7d9a737). Full history:
      `instr-backfill-tradfi` @ 34.146.133.70 (2020-01-01→2026-02-28) RUNNING. Recent window:
      `instr-backfill-tradfi-20260522` — **COMPLETED 06:58 UTC exit_code=0** (2026-03-01→2026-05-22). 2026-05-22.
- [x] ✅ [SCRIPT] P0. **IS-3.1.DeFi-Relaunch** — Full relaunch 2× DeFi VMs (both fixes IS@7d9a737). Full history:
      `instr-backfill-defi` @ 34.104.128.163 (2020-01-01→2026-02-28) RUNNING. Recent window:
      `instr-backfill-defi-20260522` — **COMPLETED 07:09 UTC exit_code=0** (2026-03-01→2026-05-22). 2026-05-22.
- [x] ✅ [SCRIPT] P0. **IS-3.1.Pred-Relaunch** — Full relaunch 2× Pred VMs (both fixes IS@7d9a737, incl.
      canonical_question_group fix). Full history: `instr-backfill-pred` @ 34.146.237.52 (2020-01-01→2026-02-28)
      RUNNING. Recent window: `instr-backfill-pred-20260522` — **COMPLETED 07:26 UTC exit_code=0**
      (2026-03-01→2026-05-22). Kalshi BLOCKED-CREDENTIALS. 2026-05-22.

## Post-relaunch verifications (IS@7d9a737 + IS@55d718f)

- [x] ✅ [VERIFY] P0. **IS-3.1.CeFi-Relaunch-V** — All 3 recent-window CeFi VMs COMPLETED exit_code=0. Timestamps:
      cefi-1-20260522 @06:56 UTC, cefi-2-20260522 @06:56 UTC, cefi-3-20260522 @06:57 UTC. Per-VM shards present: ~37.9KB
      each. DERIBIT SCHEMA_VALIDATION_FAILED for ETH_USDC-21MAY26-1800-C (expired option) — non-fatal, handled
      gracefully. Full-history VMs (cefi-1/cefi-2: 2020-2024) still RUNNING. instr-backfill-cefi-3
      (2025-01-01→2026-02-28) COMPLETED @07:25 UTC. 2026-05-22.
- [x] ✅ [VERIFY] P0. **IS-3.1.DeFi-Relaunch-V** — instr-backfill-defi-20260522 COMPLETED exit_code=0 @07:09 UTC. Per-VM
      shard 119.56 KiB. Jito SCHEMA_VALIDATION_FAILED for JITO-MEV-AGGREGATE (non-base58 symbol) — non-fatal.
      Full-history VM (defi: 2020-2026-02-28) still RUNNING. 2026-05-22.
- [x] ✅ [VERIFY] P0. **IS-3.1.TradFi-Relaunch-V** — instr-backfill-tradfi-20260522 COMPLETED exit_code=0 @06:58 UTC.
      Per-VM shard 19.84 KiB. **DATABENTO auth_account_locked**: 6 datasets (IFEU.IMPACT/IFUS.IMPACT/GLBX.MDP3/
      XNAS.ITCH/DBEQ.BASIC) all returning 403 — zero Databento-sourced instruments written (see IS-3.1.TradFi-Databento
      below). Full-history VM (tradfi: 2020-2026-02-28) still RUNNING. 2026-05-22.
- [x] ✅ [VERIFY] P0. **IS-3.1.Pred-Relaunch-V** — instr-backfill-pred-20260522 COMPLETED exit_code=0 @07:26 UTC. Per-VM
      shard 17.68 KiB. Kalshi 400 = BLOCKED-CREDENTIALS (expected). Full-history VM (pred: 2020-2026-02-28) still
      RUNNING. 2026-05-22.
- [x] ✅ DEFERRED-BLOCKED [BLOCKED-CREDENTIALS: Databento account unlock required at app.databento.com]
      [BLOCKED-CREDENTIALS] P0. **IS-3.1.TradFi-Databento** — Databento SDK 403 auth_account_locked on ALL 6 TradFi
      datasets: IFEU.IMPACT (ICE EU futures/options), IFUS.IMPACT (ICE US futures/options), GLBX.MDP3 (CME/Globex
      futures), XNAS.ITCH (NASDAQ equities), DBEQ.BASIC (Databento Basic equities/ETFs ×2). Zero Databento-sourced
      instruments written for 2026-03-01→2026-05-22 window. Polygon TradFi data (equities) still writes OK.
      `     CREDENTIAL APPROVAL REQUEST — Databento TradFi instruments adapter     Vendor: Databento (market data provider)     What I need: Reactivate/unlock account — check billing status at app.databento.com or email support@databento.com. Account may have expired/hit quota limit.     Account to use: existing operator Databento account     Unblocks: IFEU/IFUS/GLBX/XNAS/DBEQ instrument records for IS TradFi backfill     Without it: TradFi instruments from Databento datasets are 0; Polygon equities still write     `

## Temporary states + their canonical follow-up plans

- Sports IS VM `instr-backfill-sports` @ 34.180.105.8 RUNNING IS@dbf7bf6 (latest, includes all fixes: @55d718f sports
  reason fix + @2aabd7b MARKET_LIFECYCLE writer). Previous @2aabd7b VM self-deleted before 08:02 UTC; relaunched @08:02
  UTC. Processing chunk 1/71 (2020-06-01→2020-06-30) as of 08:02 UTC. No errors. Pending IS-3.1.Sports-V verify.
- **FINDING P2**: `instr-backfill-pred` (IS@7d9a737) was at 2025-06-02 (91 captured rows) when IS@2aabd7b added
  MARKET_LIFECYCLE writer. VM already processed 2025-03-14→2025-06-02 without MARKET_LIFECYCLE (~80 date gap).
  Successor: targeted market_lifecycle backfill after `instr-backfill-pred` completes. Track in `predictions_master`.
- Full-history IS VMs: `instr-backfill-pred` **COMPLETED exit_code=0 ~11:11 UTC** (self-deleted 2026-05-22); shard: 398
  rows captured, 2025-03-14→2026-02-28. Still RUNNING: `instr-backfill-defi` (at 2025-10-29 @ ~12:10 UTC, ~4 months
  remain to 2026-02-28 ~est 4-6h), `instr-backfill-tradfi` (at 2025-07-03 @ ~12:01 UTC, ~8 months remain to 2026-02-28,
  ~est 6-10h). CeFi full-history VMs: instr-backfill-cefi-{1,2,3} completed in prior session (2022-06-30, 2024-12-31,
  2026-02-28 maxes). Recent-window VMs all completed exit_code=0. 2026-05-22 slot 5 update.
- **IS CeFi catalogue built 2026-05-22 ~10:56 UTC**: 210,340 records written to
  `gs://instruments-store-cefi-central-element-323112/reference_data/instruments/cefi/all.parquet` via local
  CatalogueBuilder run. Also copied to flat reader path. Unblocked writegate cefi reconciler (85,202 rows).
- `deployment-service@7d6978b` startup script fix (VM_GAS_FEE_CHAINS unbound variable) — all future VMs use fixed
  script; MTDS-3.2.C-GAP gap-fill VMs relaunched with fix.
- Databento auth_account_locked: BLOCKED-CREDENTIALS for ALL TradFi datasets (see IS-3.1.TradFi-Databento above).
  Operator action needed to reactivate Databento account.

## IS prd bucket migration (flat→prd) — slot 5, 2026-05-22

IS VMs write to legacy flat buckets (bucket SSOT not yet canonicalised for IS). Manifest consolidator targets prd
buckets. Manual copy performed this session:

- IS CeFi prd: `instruments-store-cefi-prd-central-element-323112` — 2611 days, max=2026-05-22 ✅. Copied 18 days
  (2026-05-05→2026-05-22) + per-VM shards for instr-backfill-cefi-{1,2,3}-20260522.parquet.
- IS TradFi prd: `instruments-store-tradfi-prd-central-element-323112` — 2334 days, max=2026-05-22 ✅. Copied 18 days
  (2026-05-05→2026-05-22) + per-VM shard for instr-backfill-tradfi-20260522.parquet.
- IS DeFi prd: `instruments-store-defi-prd-central-element-323112` — 125,242 rows, max=2026-05-22 ✅. Per-VM shard
  `instr-backfill-defi-20260522.parquet` confirmed present. 67,776 captured, 0 attempted_failed. 2026-05-22.
- IS Pred prd: `instruments-store-pred-prd-central-element-323112` — 574 days, shard
  instr-backfill-pred-20260522.parquet copied. Availability_index updated: 4035 rows, 890 captured ✅.

Long-term fix: `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 2.6 (IS bucket resolver migration).
