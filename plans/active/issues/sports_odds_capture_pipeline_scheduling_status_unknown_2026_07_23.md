---
doc_type: issue
title:
  "Sports MTDS odds (TRADES) capture: no active Cloud Run job / scheduler / VM found -- pipeline scheduling status
  UNKNOWN, zero manifest activity for ~13h at time of check"
summary:
  "Surfaced while verifying whether a SOURCE_PRIORITY fix (uac@44623d25, fixing a wrong-source mislabel bug) had reached
  running MTDS instances -- found the sports manifest had ZERO writes of any kind since 2026-07-22 19:48 (checked again
  2026-07-23 08:11, ~13h gap). Investigated the actual production entrypoints: the historical Cloud Run jobs
  `oddspapi-w01`/`w02`/`w03` (europe-west2/west4/north1 -- presumably the geo-distributed ODDS_API fetch workers, given
  the naming and that they're the only odds-api-adjacent Cloud Run jobs found) last executed 2026-03-29 -- almost 4
  months ago. No Cloud Scheduler entry for sports/odds found in any checked GCP region (asia-northeast1, us-central1,
  europe-west1, europe-west2). No currently-running GCE VM is doing sports ODDS_API capture
  (`af-backfill-20260722-033350` is running but is instruments-service-side api-football FIXTURE backfill, a different
  pipeline). Could NOT check AWS-side scheduling (EventBridge/ECS) -- IAM denied (`ecs:ListClusters`/`events:ListRules`)
  for the current role. Could NOT rule out a persistent always-on VM with its own internal crontab not distinguishable
  by name in `gcloud compute instances list`. Net: genuinely UNKNOWN whether sports TRADES capture (the raw odds-tick
  pipeline K1/K2 this session made canonical, and the pipeline the api_football wrong-source rows were masquerading as)
  is scheduled/running AT ALL right now, or has been dormant for some unknown period up to and including ~4 months."
status: open
nature: issue
asset_group: [sports]
stage: [data, live]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [sports, mtds, odds-api, scheduling, deployment, data-freshness, dormant-pipeline]
related:
  [
    plans/archive/2026_07/sports_master_closeout_2026_07_21.md,
    plans/active/issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md,
    plans/active/issues/sports_mdps_derived_odds_products_zero_prod_objects_2026_07_23.md,
  ]
created: 2026-07-23
parent_epic: sports_master
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: unknown
assigned_vm: NA
execution_scope: local-only
source: [operator Q&A on sports honest coverage, verifying uac@44623d25 deploy status, 2026-07-23]
resolved_by:
locked_by:
depends_on: []
---

## Why this is P1, not P2

If sports odds TRADES capture has genuinely gone dormant, every day since it stopped is a real, growing coverage gap for
the asset_group this whole session's work (K1/K2 casing canonicalization, the api_football wrong-source cleanup) was
trying to make honest — fixing the LABEL correctness of data that has stopped arriving is much less valuable than it
looks if nothing new is landing. This is a bigger question than either of the two other issues filed today (both of
which are about correctness of what's already there, not whether new data keeps arriving at all).

Also directly relevant to `mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md`'s open item #3
(verify the SOURCE_PRIORITY fix reached running instances) — that item could only be answered via deployable-ARTIFACT
freshness (tarball rebuild timestamps), not by observing an actual run, precisely because nothing has run recently
enough to observe.

## What to check next (not attempted in this pass — this needs its own dedicated investigation)

1. Find the ACTUAL current production mechanism for sports ODDS_API fetch (if `oddspapi-w01/02/03` are retired, what
   replaced them? Check `deployment-service/scripts/vm/launch-mtds-live.sh` and any sports-specific launcher for a
   currently-scheduled invocation route).
2. Check AWS EventBridge/ECS scheduling (needs elevated IAM — the `uts-orchestrator-epic-role` used this session lacks
   `ecs:ListClusters`/`events:ListRules`).
3. Check for a persistent always-on VM (not distinguishable by name alone) with an internal crontab driving sports
   capture — `gcloud compute instances list` shows names/status only; would need to inspect instance
   metadata/startup-scripts or SSH in.
4. Once the real mechanism is found: confirm its last successful run, and whether it errored out / was manually stopped
   / was deprecated without a replacement ever being stood up.
5. If genuinely dormant: this is an operator-level decision on whether/how to resume sports odds capture — not something
   to restart autonomously without understanding why it stopped.

## Evidence (measured 2026-07-23)

```
Sports manifest (market-data-tick-sports-prd) global max attempted_at: 2026-07-22 19:48:58 UTC
Time of this check:                                                    2026-07-23 08:11:09 UTC
Gap:                                                                    ~12h 22m with zero writes

Cloud Run jobs checked (name -> last execution):
  oddspapi-w01 (europe-west2):  2026-03-29T02:22:15Z .. 02:24:30Z  (last known execution)
  oddspapi-w02 (europe-west4):  not individually checked, same age class as w01/w03
  oddspapi-w03 (europe-north1): not individually checked, same age class as w01/w02
  uts-prod-mdps-odds-horizon-bucket (asia-northeast1): runs reprocess_sports_odds.py
    (MDPS-side aggregation, not the raw TRADES fetch itself)

Cloud Scheduler jobs matching sports|odds: 0 (checked asia-northeast1, us-central1,
  europe-west1, europe-west2)

GCE instances currently RUNNING matching sports|odds|mtds: only af-backfill-20260722-033350
  (instruments-service api-football FIXTURE backfill -- different pipeline, not MTDS odds ticks)
```
