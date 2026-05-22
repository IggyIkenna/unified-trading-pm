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

- [ ] [SCRIPT] P0. **MTDS-3.2.A.Binance** — Launch cefi-binance-bf VM. OHLCV + funding.
- [ ] [SCRIPT] P0. **MTDS-3.2.A.Bybit** — Launch cefi-bybit-bf VM. OHLCV + funding.
- [ ] [SCRIPT] P0. **MTDS-3.2.A.OKX** — Launch cefi-okx-bf VM. OHLCV + funding.
- [ ] [SCRIPT] P0. **MTDS-3.2.A.Deribit** — Launch cefi-deribit-bf VM. Options pricing + IV surface.
- [ ] [SCRIPT] P0. **MTDS-3.2.A.Hyperliquid** — Launch cefi-hyperliquid-bf VM. Perp funding + marks.
- [ ] [SCRIPT] P0. **MTDS-3.2.A.Others** — Launch remaining CeFi venues (Bitfinex / Bitget / Kraken / Aster + others per
      `cefi_master` Phase 1A) as batched VMs.
- [ ] [VERIFY] P0. **MTDS-3.2.A-V** — `market-data-tick-cefi-prd` partition count ≥ flat bucket; 0 attempted_failed;
      4-pillar sample validation passes; manifest 100% v8.

## Phase 2 — TradFi MTDS backfill (MTDS-3.2.B — ALREADY DONE)

- [x] ✅ **MTDS-3.2.B SHIPPED 2026-05-17 slot 5** — 63 tradfi-bf VMs. CME + NASDAQ + NYSE. 214,586 rows. 98.4% capture
      rate. See freeze plan MTDS-3.2.B for full evidence. ICE pending operator decision (`tradfi-bf-ice-ohlcv-1m.sh`
      scaffolding shipped, `ICE_ROOTS=()`).

## Phase 3 — DeFi MTDS backfill (MTDS-3.2.C)

Replaces stale `defi_upstream_46day_full_backfill_2026_05_16.md` reference (that file was never created). This section
IS that plan.

- [ ] [SCRIPT] P0. **MTDS-3.2.C.Pyth** — Launch mtds-gas-fees-solana-bf VM (or new mtds-defi-pyth-bf). Pyth Solana
      on-chain price feeds. Per CLAUDE.md "Pyth UNBANNED 2026-05-06 for Solana".
- [ ] [SCRIPT] P0. **MTDS-3.2.C.Chainlink** — EVM oracle prices (ETH/AVAX/Polygon/Arbitrum/Optimism). Chainlink
      per-chain price feeds. `mtds-backfill-odds-*` launcher pattern adapted for EVM RPCs.
- [ ] [SCRIPT] P0. **MTDS-3.2.C.DEX** — DEX-perp forward-poll: Hyperliquid + Aster + Lighter + Pacifica + Extended
      replay per `defi_master` Phase 9. DEX mark prices + funding from Uniswap V3 / Curve / Balancer.
- [ ] [SCRIPT] P0. **MTDS-3.2.C.LST** — LST APR feeds: Lido stETH / RocketPool rETH / Coinbase cbETH / Solana JitoSOL /
      mSOL. Aave/Compound base rates.
- [ ] [VERIFY] P0. **MTDS-3.2.C-V** — `market-data-tick-defi-prd` partition count ≥ flat; 4-pillar validation; manifest
      100% v8; DeFi archetype `carry_staked_basis` data cells GREEN.

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

- [ ] [SCRIPT] P0. **MTDS-3.2.E.Polymarket** — Launch mtds-prediction-polymarket-bf VM. `canonical_question_group` rekey
      already shipped.
- [ ] [SCRIPT] P0. **MTDS-3.2.E.Kalshi** — Launch mtds-prediction-kalshi-bf VM.
- [ ] [VERIFY] P0. **MTDS-3.2.E-V** — `market-data-tick-pred-prd` row count grows from 352 base; manifest 100% v8.

---

## Temporary states + their canonical follow-up plans

- MTDS-3.2.D BLOCKED: `sports_master` Phase 3+4 rename must ship first. Track in `sports_master` epic.
- ICE TradFi: operator decision on `ICE_ROOTS` pending; `tradfi-bf-ice-ohlcv-1m.sh` scaffold ready.
- Phase 7 gate: if Phase 7 (manifest v8 label-flip) not GREEN before VMs launch, every new row grows v<8 debt. Hard gate
  — do not skip.
