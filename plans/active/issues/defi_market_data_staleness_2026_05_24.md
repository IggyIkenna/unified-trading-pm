---
title: "DeFi market-data collection appears stalled ~1 month — all DEX/lending/LST buckets latest ≈ April"
created: 2026-05-24
source:
  - "GCS data-state audit while diagnosing mtds_defi_datatype_alias_drift_2026_05_24.md"
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found

While auditing the DeFi data_type partitions (Q2 of `mtds_defi_datatype_alias_drift_2026_05_24.md`) I checked the latest
`day=` partition in every DeFi market-data bucket on `central-element-323112`. **All are ~1 month stale** (today is
2026-05-24):

| bucket            | latest `day=`                   |
| ----------------- | ------------------------------- |
| `dex-swaps[-prd]` | 2026-04-14                      |
| `dex-pools[-prd]` | 2026-04-22                      |
| `lending-indices` | 2026-04-14                      |
| `lst-rates`       | 2026-04-29                      |
| `evm-defi[-prd]`  | non-`day=` layout (not checked) |

**Scheduler/VM scan → ROOT CAUSE CONFIRMED**: `market-tick-daily-trigger` fires the `market-tick-daily` workflow with
body `{"argument":"{\"category\":\"CEFI\",\"trigger\":\"scheduled\"}"}` — i.e. **the recurring daily collection is
hardcoded to `category=CEFI` only**. There is **no recurring DeFi (DEX/lending/LST) market-data collection schedule** in
Cloud Scheduler (asia-northeast1) — only CeFi daily + `features-onchain-service-*` (which is feature _computation_, not
raw DeFi market-data collection) + manifest-consolidator crons. All DeFi compute VMs are TERMINATED; the recent ones are
the 2026-05-19 `gcs-migration-bundle-defi-*` (Phase 2.2 single-walk migration) + a 2026-05-23 `mdps-defi-2023` backfill
— i.e. one-off migration/backfill, not ongoing collection.

So DeFi market data has only ever been collected via **manual one-off VM backfills**; after the last (~April) nothing
re-collects it. (Bonus drift: the trigger body uses the legacy `category` key, not `asset_group` — another incomplete
2026-04-25 vocabulary migration.)

## Sampling transparency (per Data-Pipeline-Correctness rule)

- **Sampled, not exhaustively walked**: I read only the latest `day=` partition per bucket (one `gcloud storage ls`
  each), not a full manifest count. The "latest day" is reliable; per-venue/per-day completeness within the window is
  NOT assessed here.
- I did **not** confirm the root cause (collection genuinely stopped vs. data relocated by the 2026-05-19 bundled
  migration vs. a different env-tiered bucket). That is the first task below.

## Why it matters

- DeFi DEX prices + LST/lending rates are the MVP data for `arbitrage_price_dispersion` + `carry_staked_basis` — the two
  live-DeFi archetypes (target launch 2026-05-23, i.e. yesterday). A ~1-month hole directly undercuts paper/live DeFi
  readiness and any "test it on staging/current data" step.
- Composes with `mtds_defi_datatype_alias_drift_2026_05_24.md`: that data is ALSO under the legacy `category=` hive key
  - non-canonical `data_type=dex_pool_swaps`/`dex_pool_state` — so the DeFi pipeline has both a **freshness** gap and a
    **schema/partition** divergence.

## Recommended decision (route to mtds_mdps_master)

1. **Schedule recurring DeFi collection (P0)**: add a DeFi equivalent of `market-tick-daily-trigger` — fire
   `market-tick-daily` with `asset_group=defi` (NOT a one-off VM). Mirror the CeFi daily cadence. **Operator-aware**:
   this is a new recurring infra job (cost + correctness) — confirm cadence + venue scope before arming. Decide whether
   DEX/lending/LST share one trigger or get separate ones.
2. **Backfill the gap (P0, per Data-Pipeline-Correctness "every cell")**: backfill 2026-04-14 → present for every DeFi
   venue × data_type. Fold any GCS rewrite into the next scheduled walk (single-walk discipline).
3. Track under `plans/epics/mtds_mdps_master.md` (the data-pipeline migration/coverage coordinator); reconcile the
   trigger's legacy `category` key with `asset_group`.

## Status

- [x] Surfaced 2026-05-24 (latest-day census across DeFi buckets)
- [x] **Root cause confirmed**: no recurring DeFi collection schedule — `market-tick-daily-trigger` is `category=CEFI`
      only; DeFi has only ever been manual one-off VM backfills
- [x] **Refined finding (slot-7 2026-05-24)**: UNISWAPV2/V3/V4 stale since 2026-01-23; AAVEV3/LIDO/ETHERFI stale since
      2026-01-23. BALANCER/CURVE/SUSHISWAP/YEARNV3/ETHENA are current (2026-05-22). Gap is 4 months for Uniswap
      (critical for `arbitrage_price_dispersion` archetype).
- [x] **Gap-fill VMs launched (slot-7 2026-05-24 22:51 UTC)**: - `mtds-dex-swaps-backfill` RUNNING
      (2026-01-25→2026-05-24, DEX swaps inc. Uniswap) - `mtds-lst-rates-20260524-225132` RUNNING (2026-01-24→2026-05-24,
      LST/LRT rates) - `mtds-lending-indices-20260524-225143` RUNNING (2026-01-24→2026-05-24, Aave V3 lending) T+10
      check pending. See `mtds_backfill_phase3_2026_05_22.md` MTDS-3.2.C-GapFill item.
- [x] ✅ [INFRA] P0. **DeFi recurring collection schedule deployed (slot-7 2026-05-25 UTC)**:
      `terraform apply -target=module.defi_collect_job -target=google_cloud_scheduler_job.defi_collect_cron` — 11 Cloud
      Run Jobs (`uts-prod-mtds-collect-*`) + 11 Cloud Scheduler crons (staggered 00:00–02:05 UTC, ENABLED).
      deployment-service@terraform. Resolves root cause (no recurring DeFi schedule — only CeFi daily was wired).
- [ ] P0 verify gap-fill VMs complete + manifest GREEN for 2026-01-24→2026-05-24 per venue
- [ ] Reconcile with the data_type/partition canonicalization in `mtds_defi_datatype_alias_drift_2026_05_24.md` +
      `category`→`asset_group` on the trigger
