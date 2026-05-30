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

> **🟢 BOTH GATES GREEN (2026-05-28 verified harsh-main) — Phase 2 unblocked, awaiting launch decision:**
>
> 1. **✅ Bucket split — DECIDED: features run on prd, no full-history dependency.** Verified split (2026-05-27): it is
>    **candle-only** and a clean chronological cutover at **2026-01-24/25** — `processed_candles` flat
>    `market-data-tick-defi-central-element-323112` covers **2024-05-03 → 2026-01-24 (323 days)**; prd
>    `market-data-tick-defi-prd-central-element-323112` covers **2026-01-25 → 2026-05-22 (118 days)**; **zero overlap**.
>    `dex_swaps`/`vault_share_price` (onchain inputs) are **already prd-only** (flat has none — the running backfill
>    consolidates them into prd), so only the candle path is split. **Operator decision: features compute proceeds on
>    prd sample data now — we do NOT need full 2024-25 history for this pass.** The 323-day flat→prd `processed_candles`
>    copy is **deferred (non-blocking)** to the post-backfill fleet-drain window per the pre-migration drain HARD RULE
>    (`code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 2.0 Stage 0 — all GCP+AWS VMs stopped + manifest
>    consolidated + snapshot first); when run it is a bounded candle-only copy via `gcs_copy_object` (no API re-fetch).
> 2. **✅ mtds-dex-swaps-backfill COMPLETED 2026-05-27 10:10:30Z (exit_code=0)** — verified 2026-05-28 by harsh-main
>    background subagent (`aeb00f1502e7967f5`). Deployment registry:
>    `gs://deployment-scripts-central-element-323112/deployments/archive/2026-05-27/80552415-519d-48c6-b7b2-4fd3db009f3c.json`
>    (`status: completed`, `last_event: DEPLOYMENT_COMPLETED`). VM self-deleted after completion
>    (`VM_SHUTDOWN_ON_COMPLETION=true`). Per-chain freshness (target_date 2026-05-25, 3 days behind 2026-05-28): ETH /
>    ARBITRUM / BASE / POLYGON / OPTIMISM / AVALANCHE all GREEN; BSC pancakeswap_v3 = 0 rows (separate gap, not blocking
>    onchain features-compute). Final batch summary in run log: `Batch complete: 1241 results collected` across 23
>    venue×chain shards. **Collision risk cleared** — no active dex-swaps writer; FEAT-3.4.DeFi.\* launches are safe.
>
> **⚠️ LAUNCH DECISION OWNED BY IKENNA-MAIN** (`features_and_ml_master` plan owner). harsh-main verified the gate but
> has NOT launched. Cross-side ping filed 2026-05-28 in `plans/active/_agent_pings.md`. The 3 P0 items below are
> launch-and-verify (~1-2 hrs end-to-end); harsh-main can execute if delegated.

- [x] ✅ [SCRIPT] P0. **FEAT-3.4.DeFi.Onchain** — Launch features-onchain-defi compute VM. On-chain analytics: LST APR
      delta / DEX pool utilisation / oracle deviation signals. **Gate cleared 2026-05-28** (banner #2 — dex-swaps
      backfill COMPLETED 2026-05-27); bucket-split decision resolved (banner #1 — runs on prd).
      VM launched 2026-05-30: features-onchain-defi-20260530-025827 (FAILED rc=2 — empty INSTALL_ARGS_NODEPS bug)
      VM re-launched 2026-05-30: features-onchain-defi-20260530-032606 (asia-northeast1-c, e2-standard-8) — fixed setup script
      cmd: python -m features_service --feature-family onchain --operation compute --mode batch --start-date 2026-01-25 --end-date 2026-05-22 --asset-group DEFI --feature-group ALL
- [x] ✅ [SCRIPT] P0. **FEAT-3.4.DeFi.DeltaOne** — Launch features-delta-one-defi compute VM (reads prd
      `processed_candles`, 118 days 2026-01-25→2026-05-22 — sample-data pass per operator). **Gate cleared 2026-05-28**
      (banner #2 — dex-swaps backfill COMPLETED 2026-05-27); bucket-split decision resolved (banner #1).
      VM launched 2026-05-30: features-delta-one-defi-20260530-025907 (FAILED rc=2 — empty INSTALL_ARGS_NODEPS bug)
      VM re-launched 2026-05-30: features-delta-one-defi-20260530-032619 (asia-northeast1-c, e2-standard-8) — fixed setup script + UAC export fix
      cmd: python -m features_service --feature-family delta_one --operation compute --mode batch --start-date 2026-01-25 --end-date 2026-05-22 --asset-group DEFI --feature-group ALL
- [ ] [VERIFY] P0. **FEAT-3.4.DeFi-V** — Schema check; 100-row sample; manifest v8; 0 LookaheadBias.
      **Root cause identified 2026-05-30 (slot-1):** rc=2 bug in setup-data-pipeline-vm.sh —
        `INSTALL_ARGS_NODEPS` array has no `-e` entries for VM_TASK=features-backfill, causing
        `uv pip install --no-sources --no-deps` (no packages) → rc=2. Fixed with guard: only run
        NODEPS install when array has >2 elements. Also: UAC missing export of
        `resolve_data_type_for_feature_group` fixed (commit eb9c0b2). Both tarballs rebuilt.
      Re-launched VMs (2026-05-30 03:26): features-onchain-defi-20260530-032606 + features-delta-one-defi-20260530-032619.
      Awaiting VM completion for final verification.

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
