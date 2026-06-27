---
doc_type: plan
title: CeFi free-venue (HYPERLIQUID/ASTER) historical re-fetch has no working batch mechanism
created: 2026-06-21
source:
  - plans/active/data_completion_to_100_all_ag_2026_06_21.md
  - market-tick-data-service/market_tick_data_service/engine/orchestrator/__init__.py
  - market-tick-data-service/market_tick_data_service/adapters/umi_tick_provider.py
  - market-tick-data-service/market_tick_data_service/adapters/hyperliquid_s3.py
locked_by: live-defi-rollout
priority: P2
status: active
summary: "The 48,510 cefi `attempted_failed` cells with `source ∈ {hyperliquid, aster}` (HL 30,835 / ASTER 17,675; data_types trades / book_snapshot_5 / derivative_ticker / liquidations; HL 2023→26, ASTER 20..."
nature: process
asset_group: cross-asset
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

# CeFi HYPERLIQUID/ASTER historical re-fetch — no working batch launcher

## What I found

The 48,510 cefi `attempted_failed` cells with `source ∈ {hyperliquid, aster}` (HL 30,835 / ASTER 17,675; data_types
trades / book_snapshot_5 / derivative_ticker / liquidations; HL 2023→26, ASTER 2024→26) are the only non-Tardis-gated
slice of the cefi 802k failed set. The 2026-06-21 dispatch assumed `launch-cefi-onchain-forward-poll.sh` re-fetches them
for free. **It does not — it is a no-op for these venues:**

1. **The cefi `--operation download` orchestrator STRIPS HL/ASTER.** `VENUE_TO_ASSET_GROUP` maps `HYPERLIQUID` and
   `ASTER` to `defi`, and `engine/orchestrator/__init__.py::_filter_active_venues` drops all `defi` venues ("Skipping N
   DeFi venues (use collect-\* handlers)") — **even when passed explicitly via `--venues`**. A live launch of
   `launch-cefi-onchain-forward-poll.sh --venue HYPERLIQUID 2023-01-01 2026-06-20` logged `No active venues` for every
   date and wrote nothing (VMs deleted, no fire-and-forget).
2. **The real HL batch source is requester-pays S3, not "free".** `adapters/hyperliquid_s3.py::HyperliquidS3Downloader`
   (used by `umi_tick_provider::_fetch_hyperliquid_s3`) pulls HL historical from requester-pays S3 buckets, auth via the
   `aws-hyperliquid-s3` Secret-Manager key (**which EXISTS**). ASTER historical is via REST (`umi_tick_provider` ASTER
   branch). Both live in `umi_tick_provider`, but reaching them requires a path that bypasses the orchestrator
   defi-strip — and **no launcher drives them** (no HL/ASTER S3/REST batch launcher in deployment-service).
3. **These data_types are live-WS-primary.** trades / book_snapshot_5 / derivative_ticker for HL/ASTER are produced by
   the live websocket connectors — and the launched `mtds-live-cefi-hyperliquid-trades` VM now captures HL **forward**.
   The historical batch is a secondary backfill, not the live source.

## Why it matters

"CeFi honest-cov maxed for non-Tardis data" (dispatch end-state) needs these 48.5k cells either captured or honestly
classified. Right now there is no runnable mechanism to move them: the download path skips the venues, and the S3/REST
batch path has no launcher. This is not a credentials block (the secret exists) — it is a **missing launcher + an
orchestrator venue-classification tension** (HL/ASTER are tagged `defi` for the download-strip yet their failed cells
sit in the **cefi** manifest with `source=hyperliquid/aster`).

## Recommended decision

P0 follow-up (deployment-service + market-tick-data-service): build a dedicated **HL-S3 / ASTER-REST batch backfill
launcher** (year-sharded, requester-pays S3 via `aws-hyperliquid-s3`; minor egress cost, within infra-ops authority)
that invokes the `umi_tick_provider` HL/ASTER branches directly (or a `collect-*` op) **without** the orchestrator
defi-strip — then year-shard the HL 2023→26 / ASTER 2024→26 failed ranges. Resolve in the same change whether HL/ASTER
belong to `cefi` or `defi` in `VENUE_TO_ASSET_GROUP` so the manifest tag and the download-strip agree (currently they
disagree — failed cells are cefi-tagged but the venue is defi-classified). Expect a portion to resolve
`attempted_failed → empty_confirmed` where no historical data exists (honest absence). The live-WS stream already covers
HL forward, so this only backfills history.
