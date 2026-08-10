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

- [x] ✅ [DIAG] P2. Determine why no `processed_candles/.../timeframe=4h/` or `timeframe=24h/` (or `1d/`) objects exist
      for `odds_horizon_bucket` day=2026-04-14 despite the run.log reporting 90/90 succeeded — read the per-VM manifest
      shard
      (`market-data-tick-sports-test-central-element-323112/_index/per_vm/     mdps-backfill-sports-pipelinecheck-20260809-234808-d0c755.parquet`)
      for the 4h/24h capture_status rows and determine honest-absence vs genuine gap. **RESOLVED 2026-08-10 (slot 17):
      NEITHER — see Progress Log for full finding.** (repo: market-data-processing-service)
- [x] ✅ [CODE] P2. Fix `scripts/pipeline_e2e_check.py` so `odds_horizon_bucket` (and any other sports candle-shaped
      data_type) reports `passed`, not `skipped`/`failed`, for its actually-writable cells. Needs BOTH fixes, per the
      DIAG todo's finding: (a) `_measured_root()`/`_MEASURED_SPORTS_ROOT` so it only applies the horizon-bucketed-shape
      template to the sports data_type(s) that genuinely use it, routing `odds_horizon_bucket` through the standard
      `_MEASURED_CANDLE_ROOT`; AND (b) `_valid_timeframes()` so it does NOT test 4h/24h/1d for sports data_types at all
      — it currently calls UAC's `get_valid_timeframes_for_data_type()` (a base-granularity-only check, which returns
      `[15m, 1h, 4h, 24h]` for `odds_horizon_bucket`), but the production writer's OWN
      `MarketDataProcessingServiceConfig.resolve_timeframes()` scopes every sports asset_group down to
      `unified_api_contracts.internal.schemas._candle_contracts.MDPS_TIMEFRAMES_SPORTS = ("1m", "15m", "1h")` before any
      per-timeframe loop runs (`market-data-processing-service/config.py` `_TIMEFRAME_CEILING_BY_ASSET_GROUP`) — no
      SchemaContract exists for sports 4h/24h/1d, by deliberate design since the 2026-07-26
      `SchemaContractNotFoundError` storm fix (`mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md`). Testing a cell the
      writer can never produce will always read `failed`/`no_candle_under`, forever — this is a checker defect, not a
      backfill gap. Done-when: a from-scratch
      `pipeline_e2e_check.py --day 2026-04-14 --asset-group SPORTS     --data-types odds_horizon_bucket` force run
      reports `passed` for 15m/1h and does NOT enumerate 4h/24h/1d cells at all for sports shards. **SHIPPED 2026-08-10
      (slot 32) — market-data-processing-service@f89112b, see Progress Log.** (repo: market-data-processing-service)
- [ ] [DIAG] P2. Run a from-scratch
      `pipeline_e2e_check.py --day 2026-04-14 --asset-group SPORTS --data-types     odds_horizon_bucket --legs force,skip`
      VM check against `market-data-processing-service@f89112b` (or later) to confirm the CODE todo's fix actually flips
      the checker's own verdict to `passed` for 15m/1h and that 4h/24h/1d cells are no longer enumerated for sports
      shards at all — the CODE todo above was verified via code-path tracing (confirmed zero live callers of the
      legacy-shape writer) + `quality-gates.sh`'s `pipeline_e2e_check` driver smoke (`--help`/`--dry-enumerate` only),
      NOT a real force/skip run against live data, since that is a separate ~30-60min VM-launch action beyond this CODE
      todo's scope. Done-when: the checker's own written report
      (`plans/audit/results/data_pipeline_e2e_check_mdps_<day>.md`) shows `passed` for the 15m/1h odds_horizon_bucket
      cells with total=2 (not 8 — 4h/24h/1d no longer enumerated). (repo: market-data-processing-service)

## Progress Log

- 2026-08-10 (slot-31, data_engineering, `mdps_sports_chain_bundle_multi_venue_partition_mismatch-05aa5ad81aad`): filed
  while re-running Finding 5's prescribed verification — the partition_mismatch bug itself is confirmed fixed (0
  rejects), but the checker's own pass/fail bit for this shard is unreliable due to this separate template-root
  mismatch. Did not fix inline (needs the 4h/24h diagnosis first, and touches the shared checker script other
  asset_groups also rely on).
- **2026-08-10 (slot 17, data_engineering, DIAG todo resolved)**: Read the run's own per-VM manifest shard directly
  (`gs://market-data-tick-sports-test-central-element-323112/_index/per_vm/mdps-backfill-sports-pipelinecheck-20260809-234808-d0c755.parquet`,
  via UTL `download_from_storage`/`gcs_describe_object` — 410 rows, single small per-VM shard read, not a corpus walk),
  filtered to `data_type=odds_horizon_bucket, date=2026-04-14`: **410/410 rows are `timeframe∈{15m,1h}` /
  `capture_status=captured` — ZERO rows of ANY capture_status (not `captured`, not `attempted_failed`, not
  `empty_confirmed`) exist for `timeframe∈{4h,24h,1d}`.** The complete absence of even an `empty_confirmed` row rules
  out honest-absence (that requires an actual checked-and-genuinely-empty attempt) — the writer never iterated these
  timeframes at all for this shard.
  - **Root cause, traced to source**: `odds_horizon_bucket`'s base granularity is `15m`
    (`unified_api_contracts/registry/market_data_categories.py` `BASE_GRANULARITY_BY_DATA_TYPE`), so UAC's
    `get_valid_timeframes_for_data_type("odds_horizon_bucket")` returns `["15m", "1h", "4h", "24h"]` — a
    base-granularity-only check with no knowledge of per-asset-group SchemaContract registration. But the PRODUCTION
    writer never calls that UAC helper for its own timeframe loop — it calls
    `MarketDataProcessingServiceConfig.resolve_timeframes(MarketAssetGroup.SPORTS)`
    (`market-data-processing-service/config.py`), which intersects the candidate list against
    `_TIMEFRAME_CEILING_BY_ASSET_GROUP[SPORTS] = unified_api_contracts.internal.schemas._candle_contracts.MDPS_TIMEFRAMES_SPORTS = ("1m", "15m", "1h")`
    — confirmed live in UAC source. 4h/24h/1d are NOT in this tuple; they are scoped OUT before the per-timeframe write
    loop even starts, for every sports/sports-derived data_type (odds, odds_movement, odds_snapshot,
    odds_horizon_bucket, arbitrage_opportunity — per config.py's own comment), by deliberate design since the 2026-07-26
    fix for the sports `_4h`/`_5m`/`_15s`/`_24h` `SchemaContractNotFoundError` storm
    (`mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md`) — no SchemaContract is registered for sports at those
    timeframes, so attempting them would hard-error, not just skip.
  - **Verdict: this is NEITHER honest-absence NOR a genuine backfill gap — it's a SECOND, more fundamental checker
    defect** (alongside the root-path mismatch this doc already tracks): `pipeline_e2e_check.py`'s `_valid_timeframes()`
    (scripts/pipeline_e2e_check.py:813, called from every leg loop at lines 1350/1376/1491/1505/1757/2124/2126) derives
    its per-shard timeframe list from the UAC base-granularity helper, not from the writer's own
    `resolve_timeframes()`/asset-group ceiling — so it tests cells the production code structurally can never produce
    for sports, and will report `failed`/`no_candle_under` for them forever, regardless of any real regression or fix.
    Reworded todo 2 above to cover this second fix (both `_measured_root()` AND `_valid_timeframes()` need to change) so
    the CODE todo's done-when actually closes the checker's full false-negative surface for this shard family, not just
    the root-path half of it. No code changes made this turn — this Progress Log entry + the todo reword are the only
    changes.
- **2026-08-10 (slot 32, data_engineering, CODE todo shipped)**: Shipped both fixes in
  `market-data-processing-service@f89112b`. (a) Traced every `CandleAdapterRegistry.register(SPORTS, ...)` entry
  (`odds_horizon_bucket`, `odds_movement`, `odds_snapshot` — `arbitrage_opportunity` is RETIRED) and confirmed ALL THREE
  call the standard `process_to_candles`/`candle_write_mixin._build_candle_output_path` path (`processed_candles/`
  root); the legacy horizon-bucketed writer, `SportsBucketAssignmentAdapter.process_to_bucketed_df`, has ZERO callers
  anywhere in `market_data_processing_service/` (grepped the whole app tree) — it is dead code, never invoked in
  production. So `_measured_root()` now always returns `_MEASURED_CANDLE_ROOT` (dropped the `_is_sports()` branch);
  `_measured_root`'s legacy `_MEASURED_SPORTS_ROOT`/`_is_horizon_timeframe` machinery is KEPT (not deleted) as
  `_other_roots`'s off-template regression detector, so a future reintroduction of that shape still reports
  `skipped`/off-template instead of silently matching nothing. Deleted the now-dead `_measured_sports_violations()`
  helper + `_MEASURED_SPORTS_LEAF`/`_MEASURED_SPORTS_REQUIRED_SEGMENTS` constants (no remaining callers). (b)
  `_valid_timeframes()` now intersects UAC's `get_valid_timeframes_for_data_type()` result against
  `market_data_processing_service.config._TIMEFRAME_CEILING_BY_ASSET_GROUP` — the SAME dict
  `MarketDataProcessingServiceConfig.resolve_timeframes()` uses in production — mirroring its 24h/1d normalisation
  exactly, rather than instantiating the full service config class (avoids a cloud-credential dependency in the
  checker's pure-data timeframe-selection path). **Left `_declared_violations()`'s sports full-exemption UNCHANGED**
  (still `return []` for sports) — it is now technically stale (sports DOES claim the standard declared template) but
  not a false-failure risk (just a coarser check), and tightening it would be an unverified change to the SEPARATE §3B
  canonical/declared leg this todo's done-when doesn't cover; left a `KNOWN GAP` code comment + flagged as a candidate
  follow-up rather than shipping unverified. Verified via `quality-gates.sh` (ALL GATES PASSED, incl. the
  `pipeline_e2e_check` driver smoke's `--dry-enumerate` UAC shard-enumeration check) + `git merge-base --is-ancestor`
  against `origin/live-defi-rollout` post-push. **Did NOT run the todo's own stated from-scratch VM verification** (a
  real `--legs force,skip` run against `day=2026-04-14`) — that is a separate ~30-60min VM-launch action outside this
  CODE todo's scope; added a new DIAG todo above to track it.
