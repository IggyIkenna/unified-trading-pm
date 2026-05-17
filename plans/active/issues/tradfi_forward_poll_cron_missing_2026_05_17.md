---
title: "TradFi forward-poll cron missing — continuous-verification gap"
type: issue
status: open
created: 2026-05-17
author: slot-5
priority: P1
source:
  - plans/active/master_to_live_defi_2026_05_23.md (Group B row 4)
  - deployment-service/scripts/vm/launch-tradfi-forward-poll.sh
  - Cloud Scheduler asia-northeast1
locked_by: live-defi-rollout
---

# TradFi forward-poll cron missing — continuous-verification gap

## What I found

Master plan `master_to_live_defi_2026_05_23.md` Group B row #4 declares the continuous-verification path for "data
correctness" as `cron:cefi-fwd-` + `defi-fwd-` + `tradfi-fwd-` + `sports-fwd-` + `prediction-fwd-` forward-poll VMs.

Audit 2026-05-17 (slot-5-ikenna, post-OHLCV-Phase-7 drain):

- ✅ **cefi**: `market-tick-cefi-daily-download` Cloud Scheduler @ 09:00 UTC → `trigger-market-tick-cefi-job` Cloud Run
  service (last fired 2026-05-17 09:00:01 UTC).
- ❌ **tradfi**: NO `tradfi-fwd-` cron exists in asia-northeast1. The launcher script
  `deployment-service/scripts/vm/launch-tradfi-forward-poll.sh` is shipped + functional (one-shot human-invokable, sets
  VM prefix `tradfi-fwd-<TS>`), but there is no daily scheduler hitting it. Manual operator-invocation only.
- (defi / sports / prediction: out of scope for this audit — slot 5 is TradFi.)

Filter result:

```
$ gcloud scheduler jobs list --location=asia-northeast1 --format='value(name)' | grep -i "tradfi\|fwd"
uts-prod-manifest-consolidator-market-data-tradfi-cron   ← manifest consolidator only, NOT forward-poll
uts-prod-manifest-consolidator-instruments-tradfi-cron
```

```
$ gcloud run services list --region=asia-northeast1 --format='value(metadata.name)' | grep -i "tradfi\|trigger"
trigger-instruments-job
trigger-market-tick-cefi-job                              ← cefi trigger exists; tradfi trigger does NOT
```

## Why it matters

- Master plan Group B row 4 `Last verified` should NOT be marked green for tradfi without a daily forward-poll firing.
  The Phase 7 backfill landed historical 2019..today data successfully, but TODAY+1 won't get captured automatically
  without operator action; the manifest will silently drift behind real-time.
- Operator will have to either manually launch `launch-tradfi-forward-poll.sh` daily (toil) or accept that tradfi
  manifest stops at 2026-05-17 until cron lands.
- For May-23 cutover: ML/strategy backtests reading from TradFi manifest assume daily-fresh data. Without the cron the
  data goes stale, and the readiness signal becomes "true until next trading day".

## Recommended decision

Two paths:

1. **Deploy `trigger-market-tick-tradfi-job` Cloud Run service** + matching Cloud Scheduler @ 09:00 UTC (mirror the cefi
   pattern). Cost: ~30-60 LOC of Terraform/yaml + container image build. Owner: deployment-service (likely harsh-side or
   slot 6 — the deployment-stack owner).
2. **Cron-VM pattern**: skip the Cloud Run layer; Cloud Scheduler invokes a Cloud Workflow that runs
   `gcloud compute instances create` for the forward-poll VM directly. Simpler but less observable.

Option 1 matches the existing cefi pattern (lowest cognitive load for ops). Operator should pick.

## Workaround until shipped

Operator can run `bash deployment-service/scripts/vm/launch-tradfi-forward-poll.sh` daily to forward-poll yesterday's
data. Singleton-lock matches `^tradfi-fwd-` so duplicate invocations are safe.

## Status taxonomy

`BLOCKED-OPERATOR-DECISION` — operator needs to (a) pick Option 1 vs 2, (b) approve the cost (Cloud Run service is
~$0.50/month idle + per-invocation), (c) dispatch to deployment-stack owner. Filing for visibility; not blocking May-23
cutover (backfill landed 2019..today already; gap is "today+1 onwards" which operator can manually trigger for a few
days post-cutover).

## Cross-links

- Composes with `plans/active/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md` — that plan only declared backfill, not the
  continuous-verification path. This issue is the natural follow-up.
- See `unified_api_contracts/registry/expected_coverage.py` — NASDAQ + NYSE were also missing from `_TRADFI` scope
  (fixed at uac@`f47e37d` same day); this is the sister missing-piece on the operational/cron axis.
