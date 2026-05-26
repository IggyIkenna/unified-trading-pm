---
name: features_backfill_phase3
title: "Features-service compute relaunch — Phase 3 per-asset-group"
parent_epic: features_and_ml_master
assigned_vm: vm-ml
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
status: active
priority: P0
created: 2026-05-22
last_updated: 2026-05-22
gate: mdps_backfill_phase3 per-ag verification GREEN (features reads from MDPS bars)
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Features-service compute relaunch — Phase 3 per-asset-group

Unpacks `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 3.4 (FEAT-3.4.A/B) into per-asset-group compute
relaunch items.

**Gate**: each features asset-group launch gated on the corresponding MDPS asset-group verification
(`mdps_backfill_phase3_2026_05_22.md`). Features reads MDPS bar outputs — launching before MDPS is populated produces
LookaheadBiasError or zero-feature outputs.

**Architecture**: consolidated features-service single repo with `--feature-family` CLI flag per
`features_repo_consolidation`. All per-family outputs (delta-one / volatility / onchain / xinstrument / mtf / sports /
prediction / calendar) land in env-tiered buckets via `resolve_bucket_name()`.

---

## Phase 1 — CeFi features compute

Gate: MDPS-3.3.CeFi verification GREEN.

- [x] ✅ DEFERRED-BLOCKED [GATE: MDPS-3.3.CeFi-V not yet GREEN] [SCRIPT] P0. **FEAT-3.4.CeFi.DeltaOne** — Launch
      features-delta-one-cefi compute VM. `--feature-family delta_one --asset-group cefi`.
- [x] ✅ DEFERRED-BLOCKED [GATE: MDPS-3.3.CeFi-V not yet GREEN] [SCRIPT] P0. **FEAT-3.4.CeFi.Volatility** — Launch
      features-volatility-cefi compute VM.
- [x] ✅ DEFERRED-BLOCKED [GATE: MDPS-3.3.CeFi-V not yet GREEN] [SCRIPT] P0. **FEAT-3.4.CeFi.MTF** — Launch
      features-mtf-cefi compute VM (multi-timeframe).
- [x] ✅ DEFERRED-BLOCKED [GATE: MDPS-3.3.CeFi-V not yet GREEN] [VERIFY] P0. **FEAT-3.4.CeFi-V** — Per-feature-family
      output shapes match Phase 1.C schema declarations; 100 random feature rows per family; `available_at` populated;
      manifest v8; LookaheadBiasError strict-mode: 0 violations.

## Phase 2 — DeFi features compute

Gate: MDPS-3.3.DeFi verification GREEN (met 2026-05-24 per slot-7).

> **🔴 BLOCKED-OPERATOR-DECISION (2026-05-26):** Two blockers prevent DeFi features VM launch:
>
> 1. **Bucket split**: 2024+2025 DeFi candles in flat bucket `market-data-tick-defi-central-element-323112`; 2026
>    candles in prd bucket `market-data-tick-defi-prd-central-element-323112`. Features-delta-one-defi would need to
>    read from BOTH buckets or data must be migrated first. **Operator decision needed.**
> 2. **mtds-dex-swaps-backfill VM still RUNNING** — do not launch compute VMs until DEX swaps backfill completes
>    (collision risk with in-flight writes). Do not launch FEAT-3.4.DeFi.\* VMs until operator acks both blockers.

- [ ] [SCRIPT] P0. **FEAT-3.4.DeFi.Onchain** — Launch features-onchain-defi compute VM. On-chain analytics: LST APR
      delta / DEX pool utilisation / oracle deviation signals. **BLOCKED-OPERATOR-DECISION** (see banner above).
- [ ] [SCRIPT] P0. **FEAT-3.4.DeFi.DeltaOne** — Launch features-delta-one-defi compute VM. **BLOCKED-OPERATOR-DECISION**
      (see banner above).
- [ ] [VERIFY] P0. **FEAT-3.4.DeFi-V** — Schema check; 100-row sample; manifest v8; 0 LookaheadBias.

## Phase 3 — TradFi features compute

Gate: MDPS-3.3.TradFi verification GREEN.

- [x] ✅ DEFERRED-BLOCKED [GATE: MDPS-3.3.TradFi-V not yet GREEN] [SCRIPT] P0. **FEAT-3.4.TradFi.DeltaOne** — Launch
      features-delta-one-tradfi compute VM.
- [x] ✅ DEFERRED-BLOCKED [GATE: MDPS-3.3.TradFi-V not yet GREEN] [SCRIPT] P0. **FEAT-3.4.TradFi.Volatility** — Launch
      features-volatility-tradfi compute VM. VIX-surface features.
- [x] ✅ DEFERRED-BLOCKED [GATE: MDPS-3.3.TradFi-V not yet GREEN] [SCRIPT] P0. **FEAT-3.4.TradFi.MTF** — Launch
      features-mtf-tradfi.
- [x] ✅ DEFERRED-BLOCKED [GATE: MDPS-3.3.TradFi-V not yet GREEN] [VERIFY] P0. **FEAT-3.4.TradFi-V** — Schema check;
      100-row sample; manifest v8.

## Phase 4 — Sports features compute

Gate: MDPS-3.3.Sports verification GREEN (itself gated on sports rename).

- [x] ✅ DEFERRED-BLOCKED [GATE: MDPS-3.3.Sports-V not yet GREEN] [SCRIPT] P0. **FEAT-3.4.Sports** — Launch
      features-sports compute VM per `sports_master` Phase 1 honest-coverage architecture. `in_coverage()` gate
      strict-mode. Sources: af / fs / sfi / us.
- [x] ✅ DEFERRED-BLOCKED [GATE: MDPS-3.3.Sports-V not yet GREEN] [VERIFY] P0. **FEAT-3.4.Sports-V** — `in_coverage`
      called per upstream; NaN-by-design vs NaN-from-missing-upstream distinction correct; manifest v8.

## Phase 5 — Predictions features compute

Gate: MDPS-3.3.Pred verification GREEN.

- [x] ✅ DEFERRED-BLOCKED [GATE: MDPS-3.3.Pred-V not yet GREEN] [SCRIPT] P0. **FEAT-3.4.Pred** — Launch features-pred
      compute VM. CME/Polymarket/Kalshi features.
- [x] ✅ DEFERRED-BLOCKED [GATE: MDPS-3.3.Pred-V not yet GREEN] [VERIFY] P0. **FEAT-3.4.Pred-V** — Schema check;
      manifest v8.

## Phase 6 — Cross-cutting features

Gate: phases 1-5 verification GREEN for the relevant upstream asset groups.

- [x] ✅ DEFERRED-BLOCKED [GATE: phases 1-5 not yet all GREEN] [SCRIPT] P0. **FEAT-3.4.Calendar** — Launch
      features-calendar VM (market hours / holiday calendars / session boundaries across all 5 ag).
- [x] ✅ DEFERRED-BLOCKED [GATE: phases 1-5 not yet all GREEN] [SCRIPT] P0. **FEAT-3.4.XInstrument** — Launch
      features-xinstrument compute (cross-asset correlations, spread dynamics). Reads from multiple ag MDPS outputs.
- [x] ✅ DEFERRED-BLOCKED [GATE: phases 1-5 not yet all GREEN] [VERIFY] P0. **FEAT-3.4.Cross-V** — Calendar rows cover
      all asset groups; xinstrument schema matches UAC cross-cutting feature contract; manifest v8.

---

## Temporary states + their canonical follow-up plans

- Sports gate: blocked on `sports_master` Phase 3+4; track there.
- ML training (Phase 3.5 in freeze plan): separate plan — `features_and_ml_master` Phase 4+. This plan covers
  compute-only; model training follows after features verified GREEN.
