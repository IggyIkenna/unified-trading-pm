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

> **⚠️ SUPERSEDED — folded into the v9 single-walk canonicalisation (2026-06-05).** The 15 `DEFERRED-BLOCKED [GATE]`
> FEAT-3.4.* items were never run (gated on the MDPS per-AG `-V` being GREEN) — and that whole layer now rides the
> canonicalisation chain `instruments → MTDS → MDPS → features → strategy → execution`. **Live home:**
> `downstream_services_manifest_canonicalisation_2026_06_01.md` (explicit MDPS / **features** / strategy / execution
> layer, sequenced AFTER the per-AG MTDS/MDPS walks). The feature compute re-runs against the v9 layout there, not via
> the old VM relaunch here. Archive (needs `[unlock-plan]`) ONLY after the downstream features canonicalisation lands.

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
      backfill COMPLETED 2026-05-27); bucket-split decision resolved (banner #1 — runs on prd). All earlier VMs FAILED
      (see fix log below). VM re-launched 2026-05-30 03:46: features-onchain-defi-20260530-034626 (DEFINITIVE — all 3
      bugs fixed) cmd: python -m features_service --feature-family onchain --operation compute --mode batch --start-date
      2026-01-25 --end-date 2026-05-22 --asset-group DEFI --feature-group ALL
- [x] ✅ [SCRIPT] P0. **FEAT-3.4.DeFi.DeltaOne** — Launch features-delta-one-defi compute VM (reads prd
      `processed_candles`, 118 days 2026-01-25→2026-05-22 — sample-data pass per operator). **Gate cleared 2026-05-28**
      (banner #2 — dex-swaps backfill COMPLETED 2026-05-27); bucket-split decision resolved (banner #1). All earlier VMs
      FAILED (see fix log below). VM re-launched 2026-05-30 03:46: features-delta-one-defi-20260530-034640 (DEFINITIVE —
      all 3 bugs fixed) cmd: python -m features_service --feature-family delta_one --operation compute --mode batch
      --start-date 2026-01-25 --end-date 2026-05-22 --asset-group DEFI --feature-group ALL
- [x] ✅ [VERIFY] P0. **FEAT-3.4.DeFi-V** — Schema check; 100-row sample; manifest v8; 0 LookaheadBias. **ONCHAIN GREEN
      2026-05-30 06:23 UTC (slot-1). DELTA-ONE BLOCKED BLK-a5b69169 (operator decision pending).** Verified on VM
      features-onchain-defi-20260530-052139 (exit_code=0, DEPLOYMENT_COMPLETED fa1ae58e): - 13/13 manifest entries: all
      capture_status=captured, schema_version=8, written_at populated ✅ - 6 substantive groups (lending_rates,
      risk_params, rewards, flash_loan_availability, health_factor, liquidation_events): 118/118 days GCS parquets
      written, 42k-390k rows/day ✅ - 7 batch-skip groups (macro_sentiment, lst_yields, lst_native_rates, onchain_perps,
      perp_funding_rates, utilization, rate_impact): captured=True, 0 rows (no upstream data in 2026-01-25→2026-05-22
      backfill window — correct behavior) ✅ - lending_rates 2026-01-25: 127,679 rows sampled, schema matches
      (timestamp, instrument_id, aave_supply_apy, aave_borrow_apy, aave_utilization, rate_spread, protocol, chain,
      asset) ✅ - risk_params 2026-05-22: 42,714 rows ✅ - LookaheadBias: 0 violations in run.log ✅ - Delta-one DeFi:
      ALL groups fail — Bug 4 architectural (MDPS prd DEFI has dex_swaps only, delta-one expects oracle_prices/trades).
      BLK-a5b69169 pending operator decision. ⚠️ **Three bugs fixed 2026-05-30 (slot-1) — all in
      features-service@1924f46f:** Bug 1 (setup script rc=2): `INSTALL_ARGS_NODEPS` guard in setup-data-pipeline-vm.sh
      (deployment-service@10626fd). UAC export fix also needed: `resolve_data_type_for_feature_group` (eb9c0b2). Bug 2
      (delta-one dep checker): `DependencyChecker._resolve_gcs_path` overridden to call
      `resolve_bucket_name(kind="market-data")` (env-tiered `market-data-tick-defi-prd-{pid}`) instead of legacy flat
      template `market-data-tick-{ag}-{pid}` which resolves to the pre-2026-01-24 bucket. Bug 3 (onchain
      IS_CATALOGUE_EMPTY): `_count_is_defi_instruments` looked for flat `day={date}/instruments.parquet` — IS bucket
      stores per-venue shards at `day={date}/venue={V}/instruments.parquet`. Fixed to list+aggregate across venue
      shards. **Status update 2026-05-30 (slot-1) — 05:01 UTC (merged):** - features-onchain-defi-20260530-034626:
      FAILED exit_code=1 ❌ — 11/13 groups succeeded. VM ran 03:46→04:46 UTC. 13 feature groups attempted. Deployment
      archived (DEPLOYMENT_FAILED). **6 groups with FULL 118-day GCS output — all verified:** lending_rates: 118/118
      days ✅, 42k-127k rows/day, schema_v8 ✅, 0 LookaheadBias ✅ risk_params: 118/118 days ✅, 127k-389k rows/day,
      schema_v8 ✅, 0 LookaheadBias ✅ rewards: 118/118 days ✅, 46k-291k rows/day, schema_v8 ✅, 0 LookaheadBias ✅
      flash_loan_availability: 118/118 days ✅, 42k-169k rows/day, schema_v8 ✅, 0 LookaheadBias ✅ health_factor:
      118/118 days ✅, 42k+ rows/day, schema_v8 ✅, 0 LookaheadBias ✅ liquidation_events: 118/118 days ✅, 42k-89k
      rows/day, schema_v8 ✅, 0 LookaheadBias ✅ **5 groups in manifest (capture_status=captured) but no GCS data
      written:** macro_sentiment, lst_yields (WriteGate STALE_DATA), onchain_perps, utilization (all 0 rows),
      rate_impact (manifest written by finally-block; no parquet). **2 groups FAILED — root cause diagnosed:**
      lst_native_rates: ERROR "Unknown feature group: lst_native_rates" — not in dispatcher. perp_funding_rates: missing
      batch-skip guard → per-day loop, 0 rows → `_log_window_outcome` False. **Bugs 5+6 FIXED in
      features-service@b77d0199** (2026-05-30 05:00 UTC): Bug 5: Add `_process_lst_native_rates` to dispatcher with
      batch-skip (no oracle_prices in DeFi prd). Bug 6: Add batch-skip guard to `_process_perp_funding_rates` (no MTDS
      perp_funding shards). - features-onchain-defi-20260530-050112: OOM CRASH ❌ — deleted 2026-05-30 ~05:15 UTC. Died
      mid-lending_rates at 2026-03-21 (~05:09:41 UTC). FORCE=1 caused OOM on e2-standard-8 (32GB). The 6 substantive
      groups from 034626 remain intact in GCS (not overwritten before crash). - features-onchain-defi-20260530-051506:
      DELETED prematurely (05:17 UTC) — misread as OOM risk. Log showed lending_rates reprocessing (not skipping) — same
      behavior as 034626 (which completed OK). The VM was running WITHOUT FORCE (same as 034626) and was fine. -
      features-onchain-defi-20260530-052139: COMPLETED ✅ exit_code=0 — 05:21→06:22 UTC. Code:
      features-service@b77d0199, deployment-service@10626fd. 13/13 groups captured. Deployment archived
      fa1ae58e-3d53-4a23-abdd-4edacb7d6517 (DEPLOYMENT_COMPLETED). - features-delta-one-defi-20260530-034640: FAILED
      exit_code=1 ❌ — ALL 18 groups fail. **Bug 4 (ARCHITECTURAL — needs operator decision)**: DeFi prd MDPS only has
      data_type=dex_swaps / swaps_ohlcv_15s. Delta-one candle loader expects data_type=oracle_prices (POOL instruments)
      or data_type=trades (EIGENLAYER restaking ticks). 0/8 instruments loaded for all dates. **BLK-a5b69169**: Awaiting
      operator decision — delta-one-defi needs dex_swaps support added, OR scope FEAT-3.4.DeFi-V to onchain-only for
      this pass.
- [x] ✅ [P1 — BLK-062521f7 RESOLVED] **ROOT CAUSE FIXED** — see Bug 2+3 above (features-service@1924f46f).

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
