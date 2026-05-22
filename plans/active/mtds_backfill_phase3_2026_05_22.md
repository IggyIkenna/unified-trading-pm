---
name: mtds_backfill_phase3
title: "MTDS multi-venue backfill VM relaunch — Phase 3 per-asset-group"
type: active
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
---

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
- [x] ✅ [CODE] P0. **MTDS-QG-fix** — UAC c18550f3 removed `get_valid_data_types_for_venue` +
      `validate_data_type_for_venue` from root facade (today); moved both to `unified_api_contracts.registry` import in
      orchestrator.py. Also fixed 3 pre-existing test failures: HYPERLIQUID/ASTER → defi reclassification; onchain CeFi
      perp dual-classification exclusion in routing tests; `expected_coverage` oracle mock in lending_indices test. QG:
      all tests pass, exit 0. market-tick-data-service@105b8d15. 2026-05-22.
- [x] ✅ [AGENT slot 7] P0. **MTDS-3.2.A** — Launched `mtds-backfill-cefi-2026-05-22` VM (e2-highmem-4,
      asia-northeast1-c, 2024-01-01→2026-05-22, all venues, prod). VM RUNNING @ 34.180.126.53. 2026-05-22. NOTE: ran
      with old code (pre-chain-fix). ~4% complete before relaunch.
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.A-Relaunch** — Old CeFi VM crashed at 07:13 (OOM 77% on e2-highmem-4, only 2 dates
      processed). Relaunched `mtds-backfill-cefi-2026-05-22b` (e2-highmem-8/64GB, chunk=5,
      market-tick-data-service@626eb154 chain fix). VM RUNNING @ 34.104.198.234. 2026-05-22.
- [ ] [VERIFY] P0. **MTDS-3.2.A-V** — `market-data-tick-cefi-prd` partition count ≥ flat bucket; 0 attempted_failed;
      4-pillar sample validation passes; manifest 100% v8.

## Phase 2 — TradFi MTDS backfill (MTDS-3.2.B — ALREADY DONE)

- [x] ✅ **MTDS-3.2.B SHIPPED 2026-05-17 slot 5** — 63 tradfi-bf VMs. CME + NASDAQ + NYSE. 214,586 rows. 98.4% capture
      rate. See freeze plan MTDS-3.2.B for full evidence. ICE pending operator decision (`tradfi-bf-ice-ohlcv-1m.sh`
      scaffolding shipped, `ICE_ROOTS=()`).
- [ ] [VERIFY] P1. **MTDS-3.2.B-V** — TradFi MTDS prd bucket gaps discovered (slot 5 audit 2026-05-22):
      `market-data-tick-tradfi-prd` max=2026-05-05 vs flat max=2026-05-18. 9 missing days (2026-05-06→2026-05-18 trading
      days) being copied flat→prd (background copy). 4-day tail gap (2026-05-19→2026-05-22) needs top-up VMs:
      `launch-tradfi-bf-cme-ohlcv-1m.sh --start-floor 2026-05-19 --no-force-window` +
      `launch-tradfi-bf-nasdaq-ohlcv-1m.sh` + `launch-tradfi-bf-nyse-ohlcv-1m.sh`. Singleton lock currently clear. NOTE:
      P1 not P0 — TradFi MTDS not on critical path for May-23 DeFi archetypes.
- [ ] [SCRIPT] P1. **MTDS-3.2.B-TopUp** — Launch CME/NASDAQ/NYSE top-up VMs for 2026-05-19→2026-05-22 after flat→prd
      copy completes. Use `--no-force-window` to skip manifest-pre-checked dates.

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
      `mtds-dex-pools-backfill` @ 136.110.98.16 — RUNNING (at ~2026-04-19 as of slot-6 confirm). **CONFIRMED (slot-6
      2026-05-22)**: lst-rates 2020-01-01→2026-05-22 continuous ✅; lending-indices 2022-01-01→2026-05-22 continuous ✅;
      dex-pools IN PROGRESS (target 2026-05-22).
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.C-VSP-GAP** — `market-data-tick-defi-central-element-323112` missing vault_share_price
      for 2026-05-17, 2026-05-19→2026-05-22 (5 days). Previous VM `mtds-vault-share-price-20260522-083932` FAILED
      (exit_code=1). Relaunched `mtds-vault-share-price-20260522-090541` @ 35.221.121.77 with fresh tarball
      (mtds@626eb154 + uac@a5079dbd rebuilt 2026-05-22T08:01Z). VM RUNNING. 2026-05-22 slot-4.
- [ ] [VERIFY] P0. **MTDS-3.2.C-V** — **CRITERION CORRECTED (slot-2 2026-05-22)**: DeFi collect-\* VMs write to SEPARATE
      buckets (not market-data-tick-defi). Verify: (1) `lst-rates-central-element-323112` latest date ≥ 2026-05-22 ✅
      DONE (2020-01-01→2026-05-22 continuous); (2) `lending-indices-central-element-323112` latest date ≥ 2026-05-22 ✅
      DONE (2022-01-01→2026-05-22 continuous, 7364 records/day); (3) `dex-pools-central-element-323112` latest date ≥
      2026-05-22 — IN PROGRESS (mtds-dex-pools-backfill @ 136.110.98.16 running, target 2026-05-22); (4)
      `market-data-tick-defi-central-element-323112` vault_share_price gap fixed —
      mtds-vault-share-price-20260522-090541 RUNNING for 2026-05-17→2026-05-22; pending final date ≥ 2026-05-22
      verification.

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
- [ ] [VERIFY] P0. **MTDS-3.2.D-V** — `market-data-tick-sports-prd` partition count 1836 maintained; no
      `data_available_at` stragglers; manifest 100% v8.

## Phase 5 — Predictions MTDS backfill (MTDS-3.2.E)

- [x] ✅ [AGENT slot 7] P0. **MTDS-3.2.E** — Launched `mtds-backfill-prediction-2026-05-22` VM (e2-standard-4,
      asia-northeast1-c, 2024-01-01→2026-05-22, all venues — Polymarket + Kalshi, prod). VM RUNNING @ 34.146.119.158.
      `canonical_question_group` rekey already shipped. 2026-05-22.
- [ ] [VERIFY] P0. **MTDS-3.2.E-V** — `market-data-tick-pred-prd` row count grows from 352 base; manifest 100% v8.

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
