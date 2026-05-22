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
      UAC@7eb9859d + 9ae88aea (slot-5 + slot-4 duplicate fixes) exported `needs_candle_processing` from top-level
      `__init__.py`. Canonical GCS tarball at `code/unified-api-contracts-code.tar.gz` updated to SHA=5f699edb
      (UAC@08:50 UTC). **RUNNING**: (a) `mdps-backfill-defi-20260522-095053` @ 35.200.75.132 (2020-01-01→2026-05-22,
      market-data-tick-defi-\*, vault_share_price only); (b) `mdps-backfill-defi-dex-pools-20260522-094538` reading from
      `dex-pools-central-element-323112`; (c) `mdps-backfill-defi-lending-indices-20260522-094523` from
      `lending-indices-central-element-323112`; (d) `mdps-backfill-defi-lst-rates-20260522-094503` from
      `lst-rates-central-element-323112`. **FINDING**: MDPS DeFi only processes vault_share_price from main DeFi bucket.
      LST rates/lending_indices/dex_pool_state in separate buckets — architecture gap filed in issue doc. 2026-05-22.
- [x] ✅ [CODE] P1. **MDPS-3.3.DeFi-ArchGap** — Issue doc filed at
      `plans/active/issues/mdps_defi_multi_bucket_arch_gap_2026_05_22.md` (slot-7 2026-05-22). Documents 3 options: (A)
      features-onchain reads directly from separate buckets (bypass MDPS), (B) multi-bucket MDPS support, (C)
      consolidation step. Awaiting operator/slot-1 direction. 2026-05-22 slot-6 cross-ref.
- [ ] [VERIFY] P0. **MDPS-3.3.DeFi-V** — Verify slot-2 VM (vault_share_price): 10-sample NaN check; manifest 100% v8.
      LONG-RUNNING (2020-01-01→2026-05-22, vault_share_price only from main DeFi bucket).

## Phase 3 — TradFi MDPS reprocessor

Gate: MTDS-3.2.B TradFi already DONE (data in prd).

- [x] ✅ [AGENT slot 6] P0. **MDPS-3.3.TradFi** — Launched `mdps-backfill-tradfi-20260522-051203` VM (e2-standard-8,
      asia-northeast1-c, 2020-01-01→2026-05-22, prod). VM RUNNING @ 136.110.98.249. `MDPS_ASSET_GROUP=TRADFI`.
      `PROTOCOL_DATA_SOURCE_BUCKET_TRADFI=market-data-tick-tradfi-central-element-323112`. 2026-05-22.
- [ ] [VERIFY] P0. **MDPS-3.3.TradFi-V** — VIX 15-min bar present; NaN check passes. NOTE: VM at 2020-01-14 after 3.5h
      running (very slow — ~10 min/day × 2333 days = ~16 days ETA). VIX bars at 2020-01-01+ will eventually appear.
      LONG-RUNNING — verify once VM reaches 2026-05-22.
- [x] ✅ [CODE] P2. **MDPS-3.3.TradFi-SchemaContract** — Issue doc filed at
      `plans/active/issues/mdps_tradfi_schema_contract_gaps_2026_05_22.md` (slot-6 2026-05-22). Covers: CME/ICE
      combo/UNKNOWN/futures_chain NaN bars + trades data_type nullable OHLC fix. VIX unblocked. Current VM marks
      combo/UNKNOWN/futures_chain as `attempted_failed`; follow-up VM (after ~16d) will retry with UAC@7cdee1bc + schema
      fixes. 2026-05-22 slot-6.

## Phase 4 — Sports MDPS reprocessor

Gate: MTDS-3.2.D Sports verification GREEN (itself gated on sports rename).

- [ ] [SCRIPT] P0. **MDPS-3.3.Sports** — Relaunch MDPS Sports reprocessor. Odds / match stats bars.
      `MDPS_ASSET_GROUP=sports`.
- [ ] [VERIFY] P0. **MDPS-3.3.Sports-V** — NaN check; manifest v8; no `data_available_at` in output.

## Phase 5 — Predictions MDPS reprocessor

Gate: MTDS-3.2.E Predictions verification GREEN.

- [ ] [SCRIPT] P0. **MDPS-3.3.Pred** — Relaunch MDPS Predictions reprocessor. Polymarket + Kalshi market bars.
      `MDPS_ASSET_GROUP=pred`.
- [ ] [VERIFY] P0. **MDPS-3.3.Pred-V** — NaN check; manifest v8.

---

## Temporary states + their canonical follow-up plans

- Sports gate: blocked on `sports_master` Phase 3+4 (data_available_at rename); track in `sports_master` epic.
- In-process handoff: if `features_repo_consolidation` Phase 7 ships before this plan starts, prefer in-process mode
  over standalone VMs (no coordination with `features_backfill_phase3_2026_05_22.md` needed — they run in same process).
