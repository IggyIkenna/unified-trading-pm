---
doc_type: issue
title:
  "MDPS sports: odds_movement/odds_snapshot/arbitrage_opportunity adapters registered + SOURCE_PRIORITY-wired but ZERO
  production objects found -- dead code or a live silent-empty bug, unconfirmed"
summary:
  "Found answering an operator question about sports MDPS honest-coverage tracking. `market-data-processing-service`
  registers 4 sports candle adapters in `CandleAdapterRegistry`: `odds_horizon_bucket` (`bucket_assignment_adapter.py`),
  `odds_movement`, `odds_snapshot`, `arbitrage_opportunity`. All 4 are listed in UAC
  `DATA_TYPES_BY_ASSET_GROUP['sports']` and `SOURCE_PRIORITY` (all -> odds_api), so `get_data_types_for_categories()`
  includes all 4 in the work-list for any unfiltered SPORTS MDPS run. A live GCS check (2026-07-23) found:
  `odds_horizon_bucket` has real objects under the legacy `processed/by_date/.../data_type=
  odds_horizon_bucket/bucketed.parquet` tree (sampled 2020-06-06 and 2026-01-15, non-empty both times) -- this is the
  only one confirmed live. `odds_movement`/`odds_snapshot`/`arbitrage_opportunity` returned ZERO objects under BOTH
  candidate path shapes (`processed_candles/by_date/.../data_type={dt}/...` -- the CEFI/TRADFI/DEFI single-derivation
  shape these 3 are wired to use per canonical_writer.py's row_key construction -- AND the legacy `processed/by_date/
  .../data_type={dt}/` shape) at a sampled date (2026-01-15). NOT root-caused in this pass: could be (a) genuinely dead
  code -- nothing in the batch/live orchestration actually requests these 3 data_types despite them being registered +
  in the vocabulary list, or (b) live-dispatched but silently producing zero rows every time (a writegate
  emission-policy skip, an upstream read returning empty every call, or a schema/contract lookup failure swallowed by
  shard-level isolation) -- or (c) written somewhere neither sampled path shape covers. Each is a meaningfully different
  fix."
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags: [mdps, sports, candle-adapter, honest-coverage, dead-code, silent-empty, odds-movement, odds-snapshot, arbitrage]
related:
  [
    plans/archive/2026_07/sports_master_closeout_2026_07_21.md,
    plans/active/issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md,
  ]
created: 2026-07-23
parent_epic: sports_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: unknown
assigned_vm: NA
execution_scope: local-only
source: [operator Q&A on sports MDPS honest coverage, 2026-07-23]
resolved_by: root-caused 2026-07-23, no code change (see Resolution below)
locked_by:
depends_on: []
---

> **✅ ARCHIVED 2026-07-25** — `status: resolved`, root-caused with no code change required, 0 open todos, unlocked.
> Moved to `plans/archive/issues/` per the issue-doc-lifecycle archival ritual.

## Why this matters

Not urgent (P2, not a data-correctness regression -- these products have apparently NEVER produced real data, so there's
no denominator dishonesty from a coverage that used to work and silently stopped). But it means three data_types that
`SOURCE_PRIORITY`/`DATA_TYPES_BY_ASSET_GROUP`/the manifest schema all treat as real, trackable sports products
(`odds_movement` OHLC candles, `odds_snapshot` LOCF+implied-probability, `arbitrage_opportunity` cross-bookmaker margin
detection) are either entirely unbuilt in practice or silently broken since inception. Either way, any downstream
consumer (features-sports-service, a strategy expecting arbitrage signals, honest-coverage % dashboards) reading these
data_types today is reading nothing, and nothing is currently flagging that as a gap.

## What to check next (not attempted in this pass)

1. Find what actually drives a live/scheduled sports MDPS run's `--data-types` argument (or lack thereof) -- does any
   cron/launcher/orchestrator config explicitly request `odds_movement`/`odds_snapshot`/`arbitrage_opportunity`, or does
   everything only ever request `odds_horizon_bucket`? Check `deployment-service/scripts/vm/launch-*mdps*sports*` and
   any sports-scoped cron/schedule config.
2. If they ARE dispatched: instrument or replay one call to `SportsOddsMovementAdapter.process_to_candles()` /
   `SportsArbitrageAdapter` / `SportsOddsSnapshotAdapter` against real recent raw TRADES input and see whether it
   produces a genuinely empty `CandleOutput` (Path A in `odds_movement_adapter.py` -- "source legitimately returned zero
   rows") for every real input, which would point at an upstream read/filter bug rather than dispatch.
3. Check MDPS logs (Cloud Run / VM) for `MDPS emission policy skipped record_captured` (the writegate log line in
   `canonical_writer.py`) filtered to these 3 data_types -- would confirm dispatch-but-policy-skip as the mechanism.
4. If genuinely dead (never dispatched): decide whether to wire them into a real schedule (if the product is still
   wanted) or retire the registration + SOURCE_PRIORITY/DATA_TYPES_BY_ASSET_GROUP entries (if abandoned) -- do not leave
   them in a state where they LOOK live to anyone reading the vocabulary/priority registries.

## Evidence (measured 2026-07-23, live GCS read against market-data-tick-sports-prd)

```
processed/by_date/day=2020-06-06/data_type=odds_horizon_bucket/...    5 sample objects (real data)
processed/by_date/day=2026-01-15/data_type=odds_horizon_bucket/...    2 sample objects (real data)
processed/by_date/day=2026-01-15/data_type=odds_movement/...          0 objects
processed/by_date/day=2026-01-15/data_type=odds_snapshot/...          0 objects
processed/by_date/day=2026-01-15/data_type=arbitrage_opportunity/...  0 objects
processed_candles/  (any prefix, whole bucket)                        0 objects at all
processed_candles/.../data_type=odds_movement/...                     0 objects
processed_candles/.../data_type=odds_snapshot/...                     0 objects
processed_candles/.../data_type=arbitrage_opportunity/...             0 objects
```

## RESOLUTION (2026-07-23) — root-caused: dead code, not a silent bug

Checked what actually drives live sports MDPS processing rather than guessing. The ONLY Cloud Run job for sports MDPS is
`uts-prod-mdps-odds-horizon-bucket` (asia-northeast1), whose entrypoint is a STANDALONE script —
`market-data-processing-service/scripts/reprocess_sports_odds.py` — that does NOT go through
`CandleAdapterRegistry`/`get_data_types_for_categories()` at all. It hardcodes
`_MANIFEST_DATA_TYPE = "odds_horizon_bucket"` (grepped the whole file: zero mentions of
odds_movement/odds_snapshot/arbitrage anywhere). No other Cloud Run job, GCP Cloud Scheduler entry (checked
asia-northeast1/us-central1/europe-west1/europe-west2), or currently-running GCE VM invokes the generic MDPS CLI
(`process_handler.py --SPORTS`) — the only path that would ever reach
`SportsOddsMovementAdapter`/`SportsOddsSnapshotAdapter`/`SportsArbitrageAdapter`.

**Verdict: (a) dead code**, not (b) silently-empty-but-dispatched or (c) written elsewhere. Registered in
`CandleAdapterRegistry` + `SOURCE_PRIORITY` + `DATA_TYPES_BY_ASSET_GROUP` (aspirational/ planned), never actually wired
into a production schedule.

**Caveat — not 100% certain**: no IAM access to check AWS-side EventBridge/ECS scheduling
(`ecs:ListClusters`/`events:ListRules` both denied for the current role) — if a scheduling mechanism exists there, it
wasn't checked. Also did not check persistent-VM-internal crontabs (only `gcloud compute instances list` — an always-on
VM with its own crontab wouldn't necessarily show a distinguishing name). High confidence, not exhaustive.

**Decision needed (operator-owned, not made here)**: per action item 4 above — wire these 3 into a real schedule if the
product is still wanted, or retire the registrations if abandoned. Left open as a P2 decision; this issue is resolved
insofar as the "why zero objects" question is answered.
