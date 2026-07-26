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
status: resolved
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
resolved_by: "sports_satellite_ao_dispatch_batch5_2026_07_26.md item 6 (2026-07-26, slot 8, data_engineering)"
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

## Addendum 2026-07-24 (`/data-pipeline-reconciliation sports` raw-tick dispatch) — the pipeline is NOT dormant; the manifest signal used above was reading the architecturally non-authoritative bucket

**This answers the open question with an unambiguous NO, but reframes the real defect.** A same-day
`/data-pipeline-reconciliation --asset-group sports` run (report:
`plans/audit/results/data_pipeline_reconciliation_sports_2026_07_24.md`, finding F1) independently confirmed the gap
this doc measured is real and has GROWN (from ~12h22m on 2026-07-23 to a full 2026-07-20→2026-07-24 span, ~4-5 days, by
the time of this addendum) — but also found:

1. **Real GCS writes ARE landing daily**, including `day=2026-07-24` (the day this addendum was written): populated,
   real-content parquet objects with genuine bookmaker prices exist at
   `raw_tick_data/by_date/day=2026-07-24/pipeline_mode=batch_odds_api/asset_group=sports/venue=DRAFTKINGS/league_id=ALLSVENSKAN/instrument_type=ODDS/data_type=TRADES/ticks.parquet`
   — 24 rows, non-null `instrument_id`, real `price`/`point`/`outcome_name` columns. **The fetch+GCS-write side of the
   pipeline is alive**, contradicting this doc's working framing that the pipeline might be fully dormant.
2. **The `market-data-tick-sports-prd` manifest this doc's evidence was read from is NOT receiving new rows for ANY
   sports pipeline_mode since 2026-07-20** (not just `batch_odds_api` — confirmed across the whole manifest). A reused
   2026-07-21 whole-corpus orphan sweep independently found **20,443** raw-tick objects in this exact bucket with no
   covering manifest row at all, back to 2021-05-16.
3. **Cross-checked the live `day=2026-07-24`/`DRAFTKINGS`/`ALLSVENSKAN` sample against the sibling
   `instruments-store-sports-prd` manifest**: a matching captured row EXISTS there (41 `DRAFTKINGS` rows for that day;
   935 total `batch_odds_api` rows for `2026-07-24`, plus 42/84/1,121 for 07-21/22/23 — the exact dates
   `market-data-tick-sports-prd`'s own manifest shows zero for). This strongly suggests the data is tracked, just via a
   different bucket's manifest than the one this doc's 2026-07-23 measurement (and `market-data-tick-sports-prd`'s own
   consolidator/orphan-sweep tooling) checks.

**Revised framing**: the "is sports odds capture scheduled/running at all" question this doc opened is answered — **it
is running** — but the manifest-recording half of that pipeline appears to have (fully or partially) relocated to
`instruments-store-sports-prd` around 2026-07-20/21, leaving `market-data-tick-sports-prd`'s own index stale for new
writes while still correctly receiving the parquet bytes. This is consistent with the pre-existing
`sports_phantom_audits_reference_not_marketdata_2026_07_14.md` architecture note (_"routed ALL of sports' availability
manifest to the instruments-store bucket while the actual tick BYTES ... correctly stay in the per-asset_group
market-data-tick bucket"_), now shown to also cover the raw odds/TRADES lane, not only the reference domain that issue
was scoped to. **Only ONE shard was cross-checked** — this is a strong lead, not a closed investigation across the full
20,443-object population, and the 2026-07-21→07-23 GCS-side gap (zero venue prefixes at all under
`raw_tick_data/.../pipeline_mode=batch_odds_api/` for those three dates) is a separate, real, unexplained 3-day writer
gap that predates the day=2026-07-24 resumption — worth its own investigation.

### New todos

- [x] ✅ 6. [DATA] P1. Confirm whether `market-data-tick-sports-prd`'s manifest writes for `batch_odds_api` (and every
      other sports `pipeline_mode`) were DELIBERATELY re-routed to `instruments-store-sports-prd` around 2026-07-20/21
      (a code/config change), or whether this is an unintended regression — grep+READ the manifest-write target
      resolution in the sports capture path (same class of `_resolve_manifest_bucket()` logic already documented in
      `sports_phantom_audits_reference_not_marketdata_2026_07_14.md`), not just the two data points this addendum
      measured (repo: market-tick-data-service). **RESOLVED 2026-07-26: DELIBERATE, not a regression.**
      `market_tick_data_service/engine/orchestrator/_manifest_bucket.py::_resolve_manifest_bucket()` docstring confirms:
      the 2026-06-07 sports-manifest-canonicalisation decision moved sports' canonical availability manifest to
      `instruments-store-sports-prd` while raw tick BYTES correctly stay in `market-data-tick-sports-prd`; this was
      CODE-ENFORCED 2026-07-13 (`sports_data_sources_canonical_completion_2026_07_13.md`) and refined 2026-07-21
      (cross-AG prediction-bleed fix, commit `5581dcf9`) — both BEFORE the "around 2026-07-20/21" observation window,
      confirming the routing itself didn't change then; someone just noticed the effect around then. Independently
      cross-confirmed by `sports_phantom_audits_reference_not_marketdata_2026_07_14.md`'s 2026-07-15 addendum, which
      reached the identical conclusion from the phantom-audit angle. No code change needed — this is working as
      designed.
- [x] ✅ 7. [DATA] P2. Investigate the separate 2026-07-21→2026-07-23 GCS-side gap for
      `pipeline_mode=batch_odds_api/asset_group=sports/` (zero venue prefixes on disk for those 3 dates, confirmed by
      direct listing) — distinct from the manifest-routing question above; this is a real fetch/write gap on the writer
      side, not just a manifest-recording gap (repo: market-tick-data-service). **RESOLVED 2026-07-26: same root cause
      as `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`'s future-date-guard bug
      (`TickDataHandler._check_early_exit`, fixed `market-tick-data-service@410d7569`) — NOT a separate writer defect,
      and the gap NO LONGER EXISTS.** Direct GCS listing today (2026-07-26) shows real, populated objects for all three
      previously-empty dates (42/84/40 objects for 07-21/22/23 respectively, matching the correct manifest's
      captured-row counts almost exactly). Cross-checked `written_at` in `instruments-store-sports-prd`: each date's
      rows were written in a SINGLE BATCH ~24-25h after the fixture date, just after UTC midnight of date+1
      (`date=2026-07-21` written 2026-07-22T00:57Z, etc.) — the exact fingerprint of the future-date guard rejecting the
      date all day then clearing at midnight, not a distinct fetch/write-side gap. The "zero venue prefixes" observation
      in the 2026-07-24 addendum was a snapshot taken before the T+1-day catch-up write had landed for those dates, not
      a persistent gap. Full detail (including the GCS bucket-density correction this also forced) in
      `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`.
- [x] ✅ 8. [DATA] P2. If todo 6 confirms the manifest target moved, decide whether `market-data-tick-sports-prd`'s own
      `_index/` should be (a) left as a stale historical artifact and documented as such, or (b) backfilled/repointed so
      single-bucket tools (orphan sweep, this skill's default Phase-0 methodology, any future
      `market-data-tick-sports-prd`-scoped reconciliation) stop producing a false orphan signal for sports specifically
      (repo: unified-trading-library / market-tick-data-service, decision needed first). **RESOLVED 2026-07-26:
      disposition (a) — leave `market-data-tick-sports-prd`'s `_index/` as a documented, INTENTIONALLY stale-for-
      manifest-purposes artifact.** Since todo 6 confirms the instruments-store routing is deliberate architecture (not
      a bug), disposition (b) — backfilling/repointing `market-data-tick-sports-prd`'s own index — would be ACTIVELY
      WRONG: it would reintroduce the exact manifest-routing split-brain the 2026-07-13 fix eliminated. No code change
      needed. Documentation note for future single-bucket sports reconciliation tooling: sports' canonical availability
      manifest lives in `instruments-store-sports-prd`, NOT `market-data-tick-sports-prd`, even though sports' raw tick
      bytes live in the latter — any tool assuming manifest-bucket == data-bucket for sports will read a false
      "orphan"/"stale" signal there by design. This mirrors the existing phantom-audit
      `_BUCKET_KIND_MAP["sports"] = ("instruments-store", "sports")` convention already in place for the reference-data
      phantom check.

## Resolution (2026-07-26, slot 8, data_engineering)

All three todos closed while working `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s follow-up item on the same
pipeline (dispatched right after that plan's fix for the future-date-guard bug shipped
`market-tick-data-service@410d7569`). Summary: the manifest-routing "regression" is not a regression (deliberate,
documented, code-enforced since 2026-07-13); the GCS-side writer gap and the future-date-guard bug are the SAME
mechanism, already fixed; and `market-data-tick-sports-prd`'s own manifest index should stay a documented stale artifact
by design, never repointed. This investigation also forced a correction to
`sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`'s original density claim, which had checked the
now-non-authoritative `market-data-tick-sports-prd` bucket instead of `instruments-store-sports-prd` — see that doc's
correction banner for the full, re-verified picture (including direct confirmation the fix has already reached
production and same-day capture is writing successfully as of this resolution).
