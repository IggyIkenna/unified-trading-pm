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

- [x] ✅ [AGENT slot 7] P0. **MTDS-3.2.A** — Launched `mtds-backfill-cefi-2026-05-22` VM (e2-highmem-4,
      asia-northeast1-c, 2024-01-01→2026-05-22, all venues, prod). VM RUNNING @ 34.180.126.53. 2026-05-22.
- [ ] [VERIFY] P0. **MTDS-3.2.A-V** — `market-data-tick-cefi-prd` partition count ≥ flat bucket; 0 attempted_failed;
      4-pillar sample validation passes; manifest 100% v8.

## Phase 2 — TradFi MTDS backfill (MTDS-3.2.B — ALREADY DONE)

- [x] ✅ **MTDS-3.2.B SHIPPED 2026-05-17 slot 5** — 63 tradfi-bf VMs. CME + NASDAQ + NYSE. 214,586 rows. 98.4% capture
      rate. See freeze plan MTDS-3.2.B for full evidence. ICE pending operator decision (`tradfi-bf-ice-ohlcv-1m.sh`
      scaffolding shipped, `ICE_ROOTS=()`).

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
- [x] ✅ [AGENT slot 7] P0. **MTDS-3.2.C-GAP** — DeFi data gap 2026-05-17→2026-05-22 (5 days missing from code freeze)
      filled via 3 collect-\* VMs launched 2026-05-22 slot-7: `mtds-lst-rates-20260522-060607` RUNNING @ 35.200.59.184
      (lst_rates, 6 days), `mtds-lending-indices-20260522-060759` RUNNING @ 34.85.27.215 (lending_indices, 6 days,
      MANIFEST_PER_VM_SHARDS fix deployment-service@020841c), `mtds-dex-pools-backfill` RUNNING @ 136.110.113.253
      (dex_pools, 6 days). UAC non-pinned tarball updated to 13a870ef (ALL_DEFI_VENUES fix). T+10 all RUNNING.
- [ ] [VERIFY] P0. **MTDS-3.2.C-V** — `market-data-tick-defi-central-element-323112` has ≥2329 dates; latest date ≥
      2026-05-22; 4-pillar sample passes; DeFi archetype `carry_staked_basis` data cells GREEN.

## Phase 4 — Sports MTDS backfill (MTDS-3.2.D)

**Gate**: `sports_master` Phase 3 (`data_available_at` → `available_at` rename) + Phase 4 shipped. Track open items in
`sports_master` epic directly — 4 rename commits + QG + smoke run + writegate Phase 2.C unblock. Estimated: ~1-2 cal
AI-days on `vm-sports`.

- [ ] [SCRIPT] P0. **MTDS-3.2.D.AF** — Launch mtds-sports-af-bf VM (American Football).
- [ ] [SCRIPT] P0. **MTDS-3.2.D.FS** — Launch mtds-sports-fs-bf VM (Football/Soccer).
- [ ] [SCRIPT] P0. **MTDS-3.2.D.SFI** — Launch mtds-sports-sfi-bf VM (SFI odds).
- [ ] [SCRIPT] P0. **MTDS-3.2.D.US** — Launch mtds-sports-us-bf VM (US sports).
- [ ] [VERIFY] P0. **MTDS-3.2.D-V** — `market-data-tick-sports-prd` partition count 1836 maintained; no
      `data_available_at` stragglers; manifest 100% v8.

## Phase 5 — Predictions MTDS backfill (MTDS-3.2.E)

- [x] ✅ [AGENT slot 7] P0. **MTDS-3.2.E** — Launched `mtds-backfill-prediction-2026-05-22` VM (e2-standard-4,
      asia-northeast1-c, 2024-01-01→2026-05-22, all venues — Polymarket + Kalshi, prod). VM RUNNING @ 34.146.119.158.
      `canonical_question_group` rekey already shipped. 2026-05-22.
- [ ] [VERIFY] P0. **MTDS-3.2.E-V** — `market-data-tick-pred-prd` row count grows from 352 base; manifest 100% v8.

---

## P3 lint backlog (absorbed from unused_import_audit_2026_05_18)

- [ ] [AGENT] P3. Fix F401 unused imports in `market-tick-data-service/tests/unit/test_drift_solana_ws_connector.py`
      (`json`) and `market-tick-data-service/tests/unit/test_kraken_futures_ws_connector.py` (`json`). Run
      `ruff check --select F401 --fix <files>` after verifying git status is clean. Issue:
      `plans/archive/issues/unused_import_audit_2026_05_18.md`.

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

- MTDS-3.2.D BLOCKED: `sports_master` Phase 3+4 rename must ship first. Track in `sports_master` epic.
- ICE TradFi: operator decision on `ICE_ROOTS` pending; `tradfi-bf-ice-ohlcv-1m.sh` scaffold ready.
- Phase 7 gate: if Phase 7 (manifest v8 label-flip) not GREEN before VMs launch, every new row grows v<8 debt. Hard gate
  — do not skip.
- **[P2 MIGRATED FROM defi_upstream_46day_full_backfill_2026_05_16.md]** `vm_instruments_backfill.sh` passes
  `--venues <list>` to instruments-service CLI but the CLI doesn't accept `--venues`. Fix: either add `--venues` to
  `instruments_service` argparse OR strip `VENUES_FLAG` propagation from the inner script. Surfaces on any targeted-DeFi
  launch path. Fix before IS-3.2.C instruments VM launch.
