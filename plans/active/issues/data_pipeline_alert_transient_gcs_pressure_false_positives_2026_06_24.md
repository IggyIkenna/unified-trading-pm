---
doc_type: plan
title: Data-pipeline watchdog false-positives under heavy GCS load (transient probe/consolidator stalls)
created: 2026-06-24
source:
  - "Slack #data-pipeline-alerts 2026-06-24 18:03/18:16/18:17/18:31 (DP_CATALOG_NOT_RUNNING + DP_CRON_DID_NOT_FIRE, sports)"
locked_by: live-defi-rollout
priority: P2
status: active
summary: During the 2026-06-24 sports legacy-delete (728,890 objects) + 5 concurrent backfill VMs (sports-ref-v3-*), the data-pipeline watchdog fired CRITICAL `DP_CATALOG_NOT_RUNNING` (catalog "ABSENT") + `...
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

## What I found
During the 2026-06-24 sports legacy-delete (728,890 objects) + 5 concurrent backfill VMs (sports-ref-v3-*), the
data-pipeline watchdog fired CRITICAL `DP_CATALOG_NOT_RUNNING` (catalog "ABSENT") + `DP_CRON_DID_NOT_FIRE`
(manifest-consolidator-sports). BOTH were TRANSIENT false-positives caused by GCS API throttling under the heavy load:
- catalog `gs://instruments-store-sports-prd-…/prod/catalog.parquet` was PRESENT the whole time (mtime 01:01Z, written
  by the daily `lifecycle-catalogue-regen-sports-daily` cron, well within the 24h budget) — the probe got a transient
  GCS error and falsely reported "absent"; "recovered" = next probe succeeded (mtime unchanged, nothing recreated).
- the MDPS consolidator briefly stalled (Cloud Run GCS ops slowed past the */1 window) then recovered (verified firing
  every minute, `_index` fresh). Same class as a 14:50Z stall the same day.
Data was never at risk.

## Why it matters
Heavy-but-legitimate backfill load (exactly what we run to reach 100% coverage) reliably triggers CRITICAL pages that
are false. This trains operators to ignore the channel + masks any REAL catalog/consolidator failure during a backfill.

## Recommended decision (robustness — none urgent; data is fine)
- [x] ✅ [CODE] P2. Watchdog probes (catalog freshness + cron-heartbeat) retry-with-backoff on transient GCS errors
  before declaring ABSENT/MISSED — a single timed-out read must not fire CRITICAL. — `deployment-service`
  `meta_watchers.probe_freshness`: the in-sweep retry-before-fire now uses **growing-interval backoff (0.1/0.2/0.3s, 3
  retries)** to ride out a momentary read blip. Kept deliberately SHORT — a long per-probe sleep × many probes blows
  past pytest's 60s per-test budget (caught: a 15s backoff timed out the all-missing meta-sweep test). The split is
  intentional: the in-sweep retry handles a sub-second blip; a SUSTAINED heavy-load throttle window is covered by the
  cross-sweep consecutive-miss gate (Fix 2), NOT by sleeping longer in one sweep.
- [x] ✅ [CODE] P2. DP_CRON_DID_NOT_FIRE + DP_CATALOG_NOT_RUNNING require N consecutive misses before CRITICAL, not a
  single transient window. — `deployment-service` `meta_watchers.MissTracker` (GCS-persisted at
  `vm-census/dp-miss-counters.json`, keyed identically to `_alert_key`): a probe must be **genuinely stale for
  `DEFAULT_MIN_CONSECUTIVE_MISSES=2` consecutive */15 sweeps (~30m sustained)** before paging; a fresh OR
  suppressed-by-design (PAUSED / exec-history-fresh) probe resets its counter to 0, so a self-resolving blip never
  pages. Wired into `check_catalogue_freshness` + `check_cron_fired` + `check_monitor_crons_fired` and the cli meta
  sweep; back-compat preserved (no tracker ⇒ fire-on-first-stale, the prior behaviour). 6 new unit tests.
- [x] ✅ [CODE] P3. Verify the manifest consolidator's GCS reads/writes retry on 429/503. — **Already covered, no change
  needed**: the shared UCI GCS client (`unified_trading_library/cloud_interface/providers/gcp.py` `_GCS_RETRY`) already
  does exponential backoff on `429 TooManyRequests` + `503 ServiceUnavailable` (cap 60s, 600s deadline) on EVERY
  upload/download, and the consolidator inherits it via `get_storage_client()`. Cloud Run job timeouts are generous
  (300s default / 600s sports / 1800s heavy ≫ the 600s retry deadline), so no timeout bump / concurrency cap is
  warranted — the residual sub-window stall is absorbed by the P2 consecutive-miss gate above.

## Resolution (2026-06-24)
All three fixes shipped to `deployment-service`. The transient backfill-load false-positives (DP_CATALOG_NOT_RUNNING /
DP_CRON_DID_NOT_FIRE) are now gated: a single throttled probe is retried (backoff) and, if still stale, must persist for
2 consecutive sweeps before paging — so heavy backfills no longer page CRITICAL on a self-resolving GCS-pressure blip,
while a GENUINE 30m+ catalog/consolidator outage still pages. Fix 3 needed no code (the GCS client already retries
429/503). Issue resolved → archive on next sweep.
