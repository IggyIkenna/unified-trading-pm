---
name: features_backfill_phase3
title: "Features-service compute relaunch — Phase 3 per-asset-group"
parent_epic: features_and_ml_master
assigned_vm: vm-ml
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
status: archived
priority: P0
created: 2026-05-22
last_updated: 2026-05-22
archived: 2026-05-23
gate: mdps_backfill_phase3 per-ag verification GREEN (features reads from MDPS bars)
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

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **FEAT-3.4.CeFi.DeltaOne** — Launch features-delta-one-cefi compute VM.
      `--feature-family delta_one --asset-group cefi`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **FEAT-3.4.CeFi.Volatility** — Launch features-volatility-cefi compute
      VM.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **FEAT-3.4.CeFi.MTF** — Launch features-mtf-cefi compute VM
      (multi-timeframe).
- [x] ✅ DEFERRED-OPERATOR-DECISION [VERIFY] P0. **FEAT-3.4.CeFi-V** — Per-feature-family output shapes match Phase 1.C
      schema declarations; 100 random feature rows per family; `available_at` populated; manifest v8; LookaheadBiasError
      strict-mode: 0 violations.

## Phase 2 — DeFi features compute

Gate: MDPS-3.3.DeFi verification GREEN.

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **FEAT-3.4.DeFi.Onchain** — Launch features-onchain-defi compute VM.
      On-chain analytics: LST APR delta / DEX pool utilisation / oracle deviation signals.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **FEAT-3.4.DeFi.DeltaOne** — Launch features-delta-one-defi compute VM.
- [x] ✅ DEFERRED-OPERATOR-DECISION [VERIFY] P0. **FEAT-3.4.DeFi-V** — Schema check; 100-row sample; manifest v8; 0
      LookaheadBias.

## Phase 3 — TradFi features compute

Gate: MDPS-3.3.TradFi verification GREEN.

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **FEAT-3.4.TradFi.DeltaOne** — Launch features-delta-one-tradfi compute
      VM.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **FEAT-3.4.TradFi.Volatility** — Launch features-volatility-tradfi
      compute VM. VIX-surface features.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **FEAT-3.4.TradFi.MTF** — Launch features-mtf-tradfi.
- [x] ✅ DEFERRED-OPERATOR-DECISION [VERIFY] P0. **FEAT-3.4.TradFi-V** — Schema check; 100-row sample; manifest v8.

## Phase 4 — Sports features compute

Gate: MDPS-3.3.Sports verification GREEN (itself gated on sports rename).

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **FEAT-3.4.Sports** — Launch features-sports compute VM per
      `sports_master` Phase 1 honest-coverage architecture. `in_coverage()` gate strict-mode. Sources: af / fs / sfi /
      us.
- [x] ✅ DEFERRED-OPERATOR-DECISION [VERIFY] P0. **FEAT-3.4.Sports-V** — `in_coverage` called per upstream;
      NaN-by-design vs NaN-from-missing-upstream distinction correct; manifest v8.

## Phase 5 — Predictions features compute

Gate: MDPS-3.3.Pred verification GREEN.

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **FEAT-3.4.Pred** — Launch features-pred compute VM.
      CME/Polymarket/Kalshi features.
- [x] ✅ DEFERRED-OPERATOR-DECISION [VERIFY] P0. **FEAT-3.4.Pred-V** — Schema check; manifest v8.

## Phase 6 — Cross-cutting features

Gate: phases 1-5 verification GREEN for the relevant upstream asset groups.

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **FEAT-3.4.Calendar** — Launch features-calendar VM (market hours /
      holiday calendars / session boundaries across all 5 ag).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **FEAT-3.4.XInstrument** — Launch features-xinstrument compute
      (cross-asset correlations, spread dynamics). Reads from multiple ag MDPS outputs.
- [x] ✅ DEFERRED-OPERATOR-DECISION [VERIFY] P0. **FEAT-3.4.Cross-V** — Calendar rows cover all asset groups;
      xinstrument schema matches UAC cross-cutting feature contract; manifest v8.

---

## Temporary states + their canonical follow-up plans

- Sports gate: blocked on `sports_master` Phase 3+4; track there.
- ML training (Phase 3.5 in freeze plan): separate plan — `features_and_ml_master` Phase 4+. This plan covers
  compute-only; model training follows after features verified GREEN.

## Deferred work — migrated to:

All 18 items DEFERRED-OPERATOR-DECISION (compute VMs need operator launch authorization post-cutover). Migrated to
`features_and_ml_master` § post-cutover backlog:

- **FEAT-3.4.CeFi VMs (DeltaOne, Volatility, MTF, +V) (P0, DEFERRED-OPERATOR-DECISION)**: Migrated to:
  features_and_ml_master § post-cutover compute launch. Gate: operator VM launch authorization.
- **FEAT-3.4.DeFi VMs (Onchain, DeltaOne, +V) (P0, DEFERRED-OPERATOR-DECISION)**: Migrated to: features_and_ml_master §
  post-cutover compute launch.
- **FEAT-3.4.TradFi VMs (DeltaOne, Volatility, MTF, +V) (P0, DEFERRED-OPERATOR-DECISION)**: Migrated to:
  features_and_ml_master § post-cutover compute launch.
- **FEAT-3.4.Sports VMs (P0, DEFERRED-OPERATOR-DECISION)**: Gate: sports_master Phase 3+4 + operator authorization.
- **FEAT-3.4.Pred VMs (P0, DEFERRED-OPERATOR-DECISION)**: Migrated to: features_and_ml_master § post-cutover backlog.
- **FEAT-3.4.Calendar + XInstrument cross-cutting (P0, DEFERRED-OPERATOR-DECISION)**: Gate: phases 1-5 GREEN.
