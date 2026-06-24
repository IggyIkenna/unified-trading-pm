---
title: Data-pipeline watchdog false-positives under heavy GCS load (transient probe/consolidator stalls)
created: 2026-06-24
author: ikennaigboaka [slot-main·human-planning]
source:
  - "Slack #data-pipeline-alerts 2026-06-24 18:03/18:16/18:17/18:31 (DP_CATALOG_NOT_RUNNING + DP_CRON_DID_NOT_FIRE, sports)"
locked_by: live-defi-rollout
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
- [ ] [CODE] P2. Watchdog probes (catalog freshness + cron-heartbeat) retry-with-backoff on transient GCS errors before
  declaring ABSENT/MISSED — a single timed-out read must not fire CRITICAL. (deployment-service / UTL lifecycle-events.)
- [ ] [CODE] P2. DP_CRON_DID_NOT_FIRE + DP_CATALOG_NOT_RUNNING require N consecutive misses (2-3) before CRITICAL, not a
  single transient window.
- [ ] [CODE] P3. Verify the manifest consolidator's GCS reads/writes retry on 429/503; if so, bump its Cloud Run job
  timeout OR cap concurrent backfill write-concurrency so it can't be starved past the */1 window during big backfills.
