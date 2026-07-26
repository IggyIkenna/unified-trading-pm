---
doc_type: issue
title: "Escalation: odds_api raw ingestion wrote only sport meta-snapshots, zero real odds trades, 2026-06-21..24"
summary: >-
  4 consecutive days (2026-06-21, 06-22, 06-23, 06-24) where the odds_api raw ingestion pipeline wrote only
  `instrument_type=sport` meta-snapshot parquet files under both `pipeline_mode=batch_odds_api` and
  `pipeline_mode=live_odds_api` for sports — zero `instrument_type=odds` `data_type=trades` objects for either
  pipeline_mode, on any of the 4 days. Directly re-verified via a scoped `gcloud storage ls -r` on the exact 4
  date/pipeline_mode prefixes (no whole-corpus walk). Surfaced as a `RAW_ODDS_SHAPE_UNRECOGNIZED` / `attempted_failed`
  classification during the MDPS `odds_horizon_bucket` league_id-casing-migration reprocess — the reprocessor correctly
  refused to fabricate output rather than treat the meta-only shape as real odds data. This is escalation/documentation
  only; no backfill or re-derivation was attempted.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [sports, odds-api, raw-ingestion, upstream-gap, attempted-failed, escalation]
related:
  [
    /plans/active/issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
  ]
created: 2026-07-26
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
source: sports_satellite_ao_dispatch_batch5_2026_07_26.md, escalation todo
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# Escalation: odds_api raw ingestion 4-day meta-only gap, 2026-06-21..24

## What I found

`mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`'s shard4 reprocess (2025-01-01..2026-07-25) hit 4
dates classified `RAW_ODDS_SHAPE_UNRECOGNIZED` / `attempted_failed`: **2026-06-21, 2026-06-22, 2026-06-23, 2026-06-24**.
Re-verified live (2026-07-26) via a scoped `gcloud storage ls -r` on exactly the 4 dates' raw prefixes (no whole-corpus
walk) in `gs://market-data-tick-sports-prd-central-element-323112`, both `pipeline_mode` variants:

```
raw_tick_data/by_date/day={D}/pipeline_mode=batch_odds_api/asset_group=sports/venue=ODDS_API/
raw_tick_data/by_date/day={D}/pipeline_mode=live_odds_api/asset_group=sports/venue=ODDS_API/
```

For **all 4 dates, both pipeline_mode variants**, the only objects present are:

- `.../instrument_type=sport/data_type=trades/ODDS_API:SPORT:soccer_epl.parquet`
- `.../instrument_type=sport/data_type=trades/ODDS_API:SPORT:soccer_italy_serie_a.parquet`

**Zero `instrument_type=odds` objects exist for any of the 4 dates, on either pipeline_mode.** Every other date in the
shard4 range (2025-01-01..2026-07-25, 571 dates, only 26 residual) has the expected `instrument_type=odds`
`data_type=trades` shape — this 4-consecutive-day gap is the only occurrence of the meta-only shape in that entire
window.

This was surfaced as a `RAW_ODDS_SHAPE_UNRECOGNIZED` classification during the MDPS `odds_horizon_bucket` reprocess
(`launch-mdps-sports-bucket-vm.sh`, `force` mode, shard4 `2025-01-01..2026-07-25`) — the reprocessor correctly
identified the meta-only shape as non-consumable and refused to fabricate bucketed output from it, recording
`attempted_failed` (a retriable state) rather than a false `empty_confirmed`. **This is a raw-ingestion-pipeline
symptom, not a reprocess-script defect** — the reprocessor's refusal-to-fabricate behavior is exactly correct.

## Why it matters

4 consecutive days of only-metadata-no-real-odds-data is unusual (every other day in a 571-day window has the expected
shape) and may indicate a real, ongoing problem in whatever process feeds `venue=ODDS_API`'s raw ingestion for both the
batch and live pipeline_mode paths on those specific dates — worth a look by whoever owns that ingestion path,
independent of the sports reprocess work that surfaced it.

## Owner / next step

Whoever owns the odds_api raw-ingestion pipeline (upstream of `market-tick-data-service`'s raw
`venue=ODDS_API`/`instrument_type=odds` writer) should investigate why 2026-06-21..24 wrote only the sport meta-snapshot
shape and not real odds trades, on both the batch and live paths. **No backfill or re-derivation is being attempted
here** — this doc is escalation/documentation only, per its own scope.

`mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`'s P2 shard4 retry todo (re-run shard4's range in
`full` mode to pick up the 22 `attempted_failed` + 4 `LOSS_GUARD_BLOCKED` dates) stays open/time-gated on this gap
resolving upstream — retrying the reprocess won't produce real bucketed odds for these 4 dates until the raw ingestion
pipeline actually writes real `instrument_type=odds` data for them.

## Todos

- [ ] [OPERATOR] P3. Route this escalation to the odds_api raw-ingestion pipeline owner (or file against whatever
      team/on-call owns that upstream fetch) for investigation — why did 2026-06-21..24 write only sport meta-snapshots,
      on both `batch_odds_api` and `live_odds_api`, with zero real odds trades. Done when: the owner has either
      root-caused + fixed the upstream gap (and the 4 dates can be re-backfilled) or confirmed it's a permanent, honest
      upstream absence (no action possible).
