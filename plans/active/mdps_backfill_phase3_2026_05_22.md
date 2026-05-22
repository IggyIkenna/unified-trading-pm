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

Gate: MTDS-3.2.C DeFi verification GREEN.

- [ ] [SCRIPT] P0. **MDPS-3.3.DeFi** — Relaunch MDPS DeFi reprocessor. DEX prices + oracle prices + LST APR bars.
      `MDPS_ASSET_GROUP=defi`.
- [ ] [VERIFY] P0. **MDPS-3.3.DeFi-V** — 10-sample NaN check; manifest v8.

## Phase 3 — TradFi MDPS reprocessor

Gate: MTDS-3.2.B TradFi already DONE (data in prd).

- [ ] [SCRIPT] P0. **MDPS-3.3.TradFi** — Relaunch MDPS TradFi reprocessor. CME futures + NASDAQ/NYSE equities.
      `MDPS_ASSET_GROUP=tradfi`. VIX 15-min: Barchart preload + Yahoo rolling 60d per CLAUDE.md VIX-15m rule; honest gap
      for pre-data dates.
- [ ] [VERIFY] P0. **MDPS-3.3.TradFi-V** — VIX 15-min bar present; NaN check passes.

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
