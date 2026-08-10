---
doc_type: issue
title:
  "pipeline_e2e_check.py's SPORTS-wide `_MEASURED_SPORTS_ROOT` assumption doesn't match `odds_horizon_bucket`'s actual
  (correct) candle write path, producing false skipped/failed verdicts despite genuinely successful writes"
summary: >-
  Re-running Finding 5's prescribed verification (day=2026-04-14, SPORTS, odds_horizon_bucket, force+skip, VM
  mdps-backfill-sports-pipelinecheck-20260809-234808-d0c755) confirmed 0 `[partition_mismatch]` rejects (this issue
  doc's own fix, market-data-processing-service@53344df + a sibling streaming-path fix @e4fc0fd, is verified working —
  see mdps_sports_chain_bundle_multi_venue_partition_mismatch_2026_08_09.md). However the checker's own report still
  shows total=8 passed=0 failed=2 ambiguous=0 skipped=6: `_MEASURED_SPORTS_ROOT = "processed/by_date/"` (a
  league_id=/bucketed.parquet-leaf shape, per the checker's module docstring) is applied unconditionally to every SPORTS
  shard, but `odds_horizon_bucket` genuinely writes CANDLE-shaped output at the STANDARD
  `processed_candles/by_date/day={D}/pipeline_mode={pm}/timeframe={tf}/data_type=odds_horizon_bucket/
  instrument_type={IT}/venue={V}/{leaf}.parquet` template (verified live: 15m/1h objects exist under this root with real
  per-bookmaker `venue=` segments — SPORT888, BETONLINEAG, CORAL, UNIBET, BETSSON, MATCHBOOK, PINNACLE, DRAFTKINGS,
  VIRGINBET, CASUMO, etc. — matching this issue doc's own fix). The checker never looks there for SPORTS, so it reports
  `non_canonical_object_path`/skipped for 15m+1h (data exists, just off the checker's expected root) and
  `no_candle_under`/failed for 4h+24h (nothing found under either root — genuinely no candle written or found, separate
  open question, not chased further here).
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [sports, pipeline-e2e-check, checker-template, candle-write, odds-horizon-bucket]
related:
  [
    /plans/archive/2026_08/issues/mdps_sports_chain_bundle_multi_venue_partition_mismatch_2026_08_09.md,
    /plans/active/issues/mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md,
  ]
created: "2026-08-10"
author: mdps_sports_chain_bundle_multi_venue_partition_mismatch-05aa5ad81aad (slot-31, data_engineering)
source: >-
  Discovered while re-running Finding 5's prescribed verification (todo 2 of
  mdps_sports_chain_bundle_multi_venue_partition_mismatch_2026_08_09.md), 2026-08-10, VM
  mdps-backfill-sports-pipelinecheck-20260809-234808-d0c755 (force leg).
resolved_by:
locked_by:
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
sequential: false
context_scope:
  [
    market-data-processing-service/scripts/pipeline_e2e_check.py,
    market-data-processing-service/market_data_processing_service/app/core/candle_write_mixin.py,
  ]
---

# pipeline_e2e_check.py's SPORTS measured-root assumption doesn't match `odds_horizon_bucket`'s real write shape

## What I found

Re-ran `pipeline_e2e_check.py --day 2026-04-14 --asset-group SPORTS --data-types odds_horizon_bucket --legs force,skip`
(VM `mdps-backfill-sports-pipelinecheck-20260809-234808-d0c755`, `EXIT_STATUS=0`, run.log: 90/90 candle-write cells
succeeded, 0 errors, 14,790 candles, **0 `[partition_mismatch]` hits** — confirming the sibling issue's fix). The
checker's own written report (`plans/audit/results/data_pipeline_e2e_check_mdps_2026_04_14.md`) nonetheless shows
`total=8 passed=0 failed=2 skipped=6`:

- 15m/1h (force leg): `skipped` / `non_canonical_object_path: unexpected_root=processed_candles/by_date/` — the checker
  found the data, just not on the root it expects for SPORTS.
- 4h/24h (force leg): `failed` / `no_candle_under:gs://.../processed/by_date/day=2026-04-14/` — nothing found under
  either measured root (open question, see below).
- skip leg (all 4 cells): `skipped` / `duplicate_in_flight` (an artifact of the force leg's own VM still being visible
  when the skip leg ran moments later — not a real problem).

**Root cause of the 15m/1h false verdict**: `scripts/pipeline_e2e_check.py`'s
`_MEASURED_SPORTS_ROOT = "processed/by_date/"` (module docstring §3A) is applied to EVERY sports shard via
`_measured_root()` / `_is_sports()`, on the stated assumption that sports "derive into a legitimately DIFFERENT shape
under their own root... a league_id= axis and a bucketed.parquet leaf, with the timeframe= segment carrying an
ODDS-HORIZON token". That is true for whatever data_type actually produces `league_id=.../bucketed.parquet` (likely the
pre-match horizon-bucket-assignment pipeline referenced elsewhere in this doc chain, `bucket_assignment_adapter`), but
NOT for `odds_horizon_bucket` itself — confirmed live:
`gsutil ls gs://market-data-tick-sports-test-central-element-323112/processed_candles/by_date/day=2026-04-14/ pipeline_mode=batch_footystats/`
returns `timeframe=15m/` and `timeframe=1h/` subdirs, i.e. the STANDARD `processed_candles/` candle template every other
asset_group uses, with real per-bookmaker `venue=` segments (SPORT888, BETONLINEAG, CORAL, UNIBET, BETSSON, MATCHBOOK,
PINNACLE, DRAFTKINGS, VIRGINBET, CASUMO all observed in this run's object paths) — exactly the multi-venue-split shape
`mdps_sports_chain_bundle_multi_venue_partition_mismatch_2026_08_09.md`'s fix produces. The checker's SPORTS
special-case is over-broad: it should only apply to sports data_types that genuinely use the horizon-bucketed shape, not
`odds_horizon_bucket` (which despite its name is a real per-timeframe candle output).

**Open, not-chased-further question — 4h/24h**: neither `processed_candles/by_date/.../timeframe=4h/` nor
`timeframe=24h/` (nor `1d/`) exist under the standard root for this day, despite the run.log claiming 90/90 succeeded
across all 7 valid timeframes (`15s, 1m, 5m, 15m, 1h, 4h, 24h`). The run.log does show scattered
`recording as empty_confirmed (honest absence)` lines for some bookmaker/fixture combos (unrecognized `market_key`
rows), which may fully explain a genuine empty 4h/24h output — or may not; this needs a dedicated read of the manifest
capture_status rows for the 4h/24h cells before concluding either way. Flagging as a distinct open item rather than
asserting a verdict.

## Why it matters

The checker is the fleet's proof mechanism that SPORTS candle writes work — a template mismatch that makes it report
`failed`/`skipped` for GENUINELY CORRECT writes is itself a defect: it masks the signal a real regression (e.g. a
`partition_mismatch` reintroduction) would need to stand out against, and it wastes future re-verification passes
re-litigating an already-fixed bug because the checker's own pass/fail bit never goes green for this shard family.

## Recommended decision

- **A (recommended)**: Scope `_MEASURED_SPORTS_ROOT` to the specific sports data_type(s) that actually use the
  horizon-bucketed shape (name them precisely — likely the pre-match bucket-assignment output, not
  `odds_horizon_bucket`/`odds_snapshot`/`odds_movement`), and route sports candle data_types through the STANDARD
  `_MEASURED_CANDLE_ROOT` like every other asset_group. `_is_sports()`/`_measured_root()` would then take the shard's
  `data_type` into account, not just `asset_group`.
- **B**: If genuinely ambiguous which sports data_types use which shape, add a `--dry-enumerate`-driven audit pass first
  that lists every sports data_type actually observed in prod under each root, before changing the checker logic.

## Todos

- [ ] [DIAG] P2. Determine why no `processed_candles/.../timeframe=4h/` or `timeframe=24h/` (or `1d/`) objects exist for
      `odds_horizon_bucket` day=2026-04-14 despite the run.log reporting 90/90 succeeded — read the per-VM manifest
      shard
      (`market-data-tick-sports-test-central-element-323112/_index/per_vm/     mdps-backfill-sports-pipelinecheck-20260809-234808-d0c755.parquet`)
      for the 4h/24h capture_status rows and determine honest-absence vs genuine gap. (repo:
      market-data-processing-service)
- [ ] [CODE] P2. Fix `scripts/pipeline_e2e_check.py`'s `_measured_root()`/`_MEASURED_SPORTS_ROOT` so it only applies the
      horizon-bucketed-shape template to the sports data_type(s) that genuinely use it, and routes `odds_horizon_bucket`
      (and any other candle-shaped sports data_type) through the standard `_MEASURED_CANDLE_ROOT`. Done-when: a
      from-scratch `pipeline_e2e_check.py --day 2026-04-14 --asset-group SPORTS     --data-types odds_horizon_bucket`
      force run reports `passed` (not `skipped`/`non_canonical_object_path`) for the 15m/1h cells. (repo:
      market-data-processing-service)

## Progress Log

- 2026-08-10 (slot-31, data_engineering, `mdps_sports_chain_bundle_multi_venue_partition_mismatch-05aa5ad81aad`): filed
  while re-running Finding 5's prescribed verification — the partition_mismatch bug itself is confirmed fixed (0
  rejects), but the checker's own pass/fail bit for this shard is unreliable due to this separate template-root
  mismatch. Did not fix inline (needs the 4h/24h diagnosis first, and touches the shared checker script other
  asset_groups also rely on).
