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

## Investigation attempt 2026-07-27 (classification sweep, no root cause found — log retention expired)

Attempted to root-cause via live GCP Cloud Logging before leaving the `[OPERATOR]` tag as-is (per the operator's
2026-07-27 instruction that even audits should be agent-driven where feasible). Confirmed
`uts-prod-market-tick-data-service-fast-t1-recon` (the same job class as
`sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`'s future-date-guard finding) DID fire at
~00:30-00:32 UTC on all 4 affected dates (2026-06-21..24), and its Cloud Run Job execution genuinely **failed** (exit
code 1, `protoPayload.status.message`: "... has failed to complete, 0/1 tasks were a success"). However, this is
**business-as-usual, not unique to the 4 problem dates** — the same job fails with the identical message on 2026-06-20,
2026-06-25, and 2026-06-26 too (checked for comparison), so it is very likely an unrelated pre-existing retry/exit-code
quirk, not the cause of the meta-only-write anomaly. The actual container stdout/stderr for these executions (which
would show the real per-league fetch path / `odds_api_adapter.py` error, if any) is **no longer retained** — only the
`cloudaudit.googleapis.com%2Fsystem_event` audit-log entry survives; the project's `_Default` logging bucket retention
is 2 days, and these dates are 33-36 days old at investigation time. **Conclusion: further root-cause from this
session's tooling is infeasible — the direct evidence has already expired.** Leaving the `[OPERATOR]` tag in place is
correct here not because of an authority/credential gate, but because the remaining path (if any) is either a
longer-retention log export this session didn't find, or contacting Odds-API's vendor-side incident history directly —
both need a human decision on how much effort to spend chasing a month-old, already-cold gap versus accepting it as
permanent honest absence.
