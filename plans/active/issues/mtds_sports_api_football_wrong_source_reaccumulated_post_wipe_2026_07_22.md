---
doc_type: issue
title:
  "MTDS sports: 1,266,874 pipeline_mode=batch_api_football rows (incl. 7,248 genuinely `captured`) present in the
  raw-tick manifest today, 2026-07-22 -- ~19+ days after the 2026-06-24 operator-ruled wipe, writer never disabled"
summary:
  "Found while scoping K1/K2 casing-migration completeness (sports_master_closeout_2026_07_21.md, sixth wave) -- a broad
  manifest query for lowercase data_type=trades/instrument_type=odds rows in the MTDS sports raw-tick index
  (market-data-tick-sports-prd) turned up 1,286,319 rows, far exceeding K1/K2's real batch_odds_api scope (373,296).
  Investigated before assuming anything: 1,265,534 of those are pipeline_mode=batch_api_football. Per
  market-tick-data-service/scripts/wipe_api_football_sports_odds_2026_06_24.py's own docstring, api_football is NOT a
  sanctioned bookmaker-odds source for MTDS ('no MTDS odds adapter, no SOURCE_PRIORITY key... every source=api_football
  row in the MTDS sports manifest is odds-like wrong-source data') and the operator ruled 2026-06-24 to WIPE EVERYTHING
  source=api_football from the MTDS sports manifest+GCS (that run dropped 1,398,423 rows + deleted 231,532 objects).
  Today's population (1,266,874 total batch_api_football rows in the same manifest, of which 1,265,534 sit at the exact
  wiped shape data_type=trades/instrument_type=odds) has `attempted_at`/`written_at` reaching 2026-07-13 -- 19+ days
  after the wipe cutoff -- meaning whatever writer produced the original 1.4M-row population was never disabled, and has
  been re-accumulating rows for nearly 3 weeks. capture_status breakdown of the lowercase trades/odds subset:
  empty_confirmed=1,200,270 (94.8%), attempted_failed=58,016 (4.6%), captured=7,248 (0.57%, real data, data-dates
  2020-08-24..2025-04-11 -- i.e. backfill-shaped, not new-day captures). Exact writer call site NOT pinpointed in this
  pass (grep for the literal pipeline_mode/source string across market_tick_data_service/ turned up only READERS
  (sports_catalog_reader.py, for a DIFFERENT bucket/surface -- instruments-service fixtures_schedule reference data, not
  MTDS raw tick) and league-ID-resolution helpers, not a manifest-writing call site) -- flagged as the concrete next
  step, not resolved here. Likely related to (but a DISTINCT manifest surface from) the already-tracked
  sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md, which documents an
  analogous nightly-re-seeded api_football population on the INSTRUMENTS-SERVICE (IS) sports index -- that doc's
  127,018-row finding is IS-side (instruments-store-sports); this finding is MTDS-side (market-data-tick-sports-prd), a
  different bucket, different capture_status distribution (mostly empty_confirmed/attempted_failed, not
  expected_unattempted), and a materially different scale on the `captured` (real-data) tail. Possibly the same root
  cause (an api_football cron/writer never disabled after the ruling), possibly two independent leaks -- unconfirmed."
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [api-football, wrong-source, sports, mtds, manifest, operator-ruling, data-correctness, re-accumulation]
related:
  [
    plans/active/sports_master_closeout_2026_07_21.md,
    plans/active/issues/sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md,
    plans/active/issues/mtds_sports_api_football_blank_source_2026_06_28.md,
    plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md,
  ]
created: 2026-07-22
parent_epic: sports_master
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: unknown
assigned_vm: NA
execution_scope: local-only
source: [sports_master_closeout_2026_07_21.md sixth wave, 2026-07-22]
resolved_by: unified-api-contracts@44623d25, market-tick-data-service@e9d9dec0
locked_by:
depends_on: []
---

## Why this is NOT a K1/K2 scope item

K1 ("emit UPPER at the LIVE writer") named a single, specific writer function -- `_build_sports_shard_path`
(`venue_fetch.py:871-900`) -- as "the currently-running writer" to fix; it is the ODDS_API adapter's shard-path builder,
`pipeline_mode=batch_odds_api`. K2 ("migrate the historical lower-case rows") inherits that same writer's scope by
construction (the migration tool + manifest-swap report are keyed off objects `migrate_sports_casing_ 2026_07_22.py`
actually copied -- all `batch_odds_api`). Both are now fully shipped and verified complete for that scope: 0 remaining
lowercase rows, 373,297 canonical rows, in `pipeline_mode=batch_odds_api` (verified 2026-07-22, see the sixth-wave
Progress Log in `sports_master_closeout_2026_07_21.md`).

The original 2026-07-19/20 K2 scope estimate ("~1.8M `trades` rows, 91.5% of the bucket") did not filter by
`pipeline_mode` and so conflated the true `batch_odds_api` population with this `batch_api_football` population (and a
small `batch_polymarket_clob` population, 20,785 rows, ALL `capture_status=empty_confirmed` -- zero real data, almost
certainly the already-tracked cross-AG prediction-bleed residual documented elsewhere in
`sports_master_closeout_2026_07_21.md`, not a new finding). Casing-fixing a population that is (a) a different,
unidentified writer, (b) 99.4% non-data bookkeeping rows, and (c) already operator-ruled OUT of the canonical sports
odds model entirely would be pointless at best and would mask this actual finding at worst. This issue exists so that
"decide explicitly" question from the original K2 todo has an honest, evidence-based answer instead of a silent scope
narrowing.

## ROOT CAUSE FOUND + FIX SHIPPED (2026-07-23)

Not a live rogue writer -- diffed the current `source=api_football` population against the wipe's own pre-wipe snapshot
(`_index/snapshots/pre_api_football_wipe_2026_06_24.parquet`): 686,124/1,266,874 keys are the EXACT SAME
`(date,venue,league_id,data_type,instrument_type)` tuples as before the wipe (stale reassertion, not new activity),
timestamped in a single ~2-minute burst (2026-07-13 23:54:39-23:56:48 UTC) -- the signature of a bulk expected-
universe/sentinel regeneration pass, not per-row live fetching. Only 8,787 keys are genuinely new (7,250 `captured`, a
real but much smaller tail, spread May-July not bursted).

Traced the mechanism: MTDS's sentinel fan-out (`sentinels.py:228`) correctly requests
`_resolve_pipeline_mode_for_sentinel(venue, "trades", default=PipelineMode.BATCH_ODDS_API)` -- but that function calls
UTL's `derive_pipeline_mode_for_row()` FIRST, and returns whatever it gives back before ever consulting the caller's
`default`. `derive_pipeline_mode_for_row()` tried `SOURCE_PRIORITY[("sports","trades")]` / `[("sports","TRADES")]` --
**neither existed** (confirmed: `("sports","ODDS_SNAPSHOT"/"ODDS_MOVEMENT"/"ARBITRAGE")` all correctly map to
`["odds_api"]`, but there was no `TRADES` sibling) -- so it fell through to
`_ASSET_GROUP_FALLBACKS["sports"] = PipelineMode.BATCH_API_FOOTBALL`
(`unified_trading_library/pipeline_mode_resolver.py:364`), silently shadowing the correct caller-supplied default for
EVERY sports TRADES sentinel row. Confirmed end-to-end before/after:
`derive_pipeline_mode_for_row(venue="PINNACLE", asset_group="sports", data_type="trades")` returned `batch_api_football`
pre-fix, `batch_odds_api` post-fix. This is almost certainly the SAME underlying gap that produced the sibling IS-side
finding in `sports_odds_ownership_registry_split_brain_and_bogus_api_football_ denominator_2026_07_15.md` (127,018 rows,
"re-seeded nightly") -- one missing SOURCE_PRIORITY entry, two surfaces.

**Fix shipped**: `unified-api-contracts@44623d25` -- added `("sports","TRADES"): ["odds_api"]` to `SOURCE_PRIORITY`
(`_source_priority_data.py`), plus the two registries the test suite enforces symmetry with:
`AVAILABILITY_AT_SEMANTICS[("sports","TRADES")] = "publication_time"` (matching its `ODDS_SNAPSHOT`/`ODDS_MOVEMENT`
siblings) and `DATA_TYPES_BY_ASSET_GROUP["sports"]` gained the `"TRADES"` vocabulary member (mirroring how `"ODDS"` was
already registered alongside `"odds"`). Also extended `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[("sports", "odds")]`
to `frozenset({"trades","TRADES"})` -- the instrument_type axis is case-normalized before lookup, so this had to go into
the VALUE set, not a separate uppercase key (a first attempt at a separate `("sports","ODDS")` key was dead code, caught
by the reachability test). Full UAC QG green after 3 iterations chasing companion-registry symmetry requirements the
test suite enforces.

## What actually needs doing (root cause fixed; this is now cleanup + deploy verification)

1. ~~Find the write-path~~ -- DONE, see above.
2. ~~Fix the root cause~~ -- DONE, `uac@44623d25`.
3. **Verify the fix has reached RUNNING MTDS instances before wiping** -- MTDS depends on UAC via a local path
   (`pyproject.toml`: `unified-api-contracts>=0.33.0,<1.0.0`, `[tool.uv.sources] path = "../unified-api-contracts"`),
   not a registry-pinned version, so this fix does NOT auto-propagate to deployed VMs/Cloud Run instances -- they need
   their next tarball rebuild / redeploy cycle. **Wiping before that happens would just let the next sentinel- emission
   cycle re-pollute the same 1.26M rows** (exactly what happened to the original 2026-06-24 wipe, whether via this same
   mechanism or the shard-reassertion route below). Check `deployment-observability` / the sports sentinel cron's
   last-run timestamp against the UAC version it has loaded before running the wipe.
4. **Wipe the re-accumulated population, this time CAS-safe** -- the original
   `wipe_api_football_sports_odds_ 2026_06_24.py` does a non-CAS, unprotected read-modify-write directly on
   `_index/availability_index.parquet` (its own docstring: "Run with the manifest consolidator PAUSED to avoid a
   read-modify-write race" -- an operational-discipline dependency, not a structural guarantee) and never touches the
   underlying `_index/per_vm/*.parquet` shards, which is plausibly a SECOND contributing mechanism (shard-reassertion)
   on top of the sentinel-mislabeling root cause -- both may need addressing. Reuse this session's
   `manifest_swap_ 2026_07_22.py`-style snapshot+CAS-remove pattern (already proven working) rather than the old script,
   scoped to `source=="api_football"` in the MTDS sports bucket (confirmed: api_football has zero legitimate business
   writing into `market-data-tick-sports-prd` at all -- its sanctioned writes are fixtures/reference data in the
   `instruments-store-sports` bucket).
5. Decide the fate of the 7,248 (now 7,250, +2 since) genuinely `captured` rows specifically (real data, data-dates
   2020-08-24..2025-04-11) -- wipe with the rest per the standing 2026-06-24 ruling, or carve out if there's a reason
   they're legitimate. No evidence found suggesting they're legitimate; default is wipe-with-the-rest.

## Evidence (measured 2026-07-22, live MTDS sports index read)

```
pipeline_mode=batch_api_football total rows:                1,266,874
  lowercase data_type=trades/instrument_type=odds subset:    1,265,534
    capture_status=empty_confirmed:                          1,200,270  (94.8%)
    capture_status=attempted_failed:                             58,016  (4.6%)
    capture_status=captured (REAL DATA):                          7,248  (0.57%)
  attempted_at / written_at range:                    2026-05-05 .. 2026-07-13
  captured-subset data-date range:                    2020-08-24 .. 2025-04-11
  rows with data-date AFTER the 2026-06-24 wipe cutoff:              120

pipeline_mode=batch_polymarket_clob total rows:                 20,785
  ALL capture_status=empty_confirmed, venue=KALSHI, source=polymarket_clob
  -- zero real data; almost certainly cross-AG prediction-bleed residual, not this issue's scope.
```

## RESOLVED (2026-07-23) — deploy verified, manifest wiped

**#3 (deploy verification)**: could not empirically observe the fix firing (zero sports manifest activity of ANY kind
since 2026-07-22 19:48 — no cron/job/VM currently running for sports odds capture at all, see the new dormant-pipeline
finding below). Verified the DEPLOYABLE ARTIFACTS instead: `unified-api-contracts-code.tar.gz` rebuilt
2026-07-23T07:31:17Z and `mtds-code.tar.gz` rebuilt 2026-07-23T08:00:57Z — both AFTER the fix (`uac@44623d25`,
06:55:15Z). Any future VM/Cloud-Run deploy picks up the fix; risk of re-pollution on the next real run is now low.

**#4 (wipe)**: EXECUTED. `market-tick-data-service@e9d9dec0`
(`scripts/sports/wipe_api_football_sports_manifest_2026_07_23.py`, new CAS-safe tool — snapshot

- generation-matched remove, unlike the original unprotected script). Result: 1,266,874/1,266,874 `source=api_football`
  rows removed (base 1,830,258 → 563,384), VERIFY PASSED (0 remaining). Snapshot:
  `gs://market-data-tick-sports-prd-central-element-323112/_index/snapshots/ pre_api_football_manifest_wipe_2026_07_23_20260723T081810Z.parquet`.
  Also caught a small population my earlier narrower query missed — `data_type=odds_horizon_bucket` (1,337 rows) and
  `data_type=ARBITRAGE_OPPORTUNITY` (3 rows) also carried `source=api_football`; the new tool filters on `source` alone
  (matching the original wipe's full scope) so these were correctly included.

**#5 (captured-cells fate)**: manifest rows wiped (with the rest, per the standing ruling — no carve-out found). The
underlying **GCS objects for the ~7,251 captured cells are NOT deleted** — that is a separate, operator-gated step
(prod-bucket delete = human-only), matching the K1/K2 old-object delete precedent. Evidence for that follow-up:
`source=api_football`, `pipeline_mode=batch_api_football/` prefix, `market-data-tick-sports-prd` bucket, ~7,251 objects.

**New, bigger finding surfaced while verifying #3**: no Cloud Run job, scheduler, or VM appears to be currently driving
sports ODDS_API capture at all (`oddspapi-w01/w02/w03` last ran 2026-03-29; no scheduler entries found for sports/odds
in any checked GCP region; AWS-side scheduling not checked, no IAM access). See
`issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md` — this is a plausibly bigger operational
question than this issue, filed separately, P1.
