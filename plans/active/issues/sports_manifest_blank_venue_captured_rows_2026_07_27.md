---
doc_type: issue
title:
  '2,490 captured sports manifest rows carry venue="" (blank string) — discovered during Track C venue re-stamp census'
summary: >-
  While sizing `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track C venue re-stamp todo, a corpus-wide
  read-only census of the sports availability_index (no filter, full history) found 2,498 manifest rows with `venue==""`
  (blank string), of which 2,490 carry `capture_status=captured` (real data, not honest-absence placeholders) — the
  remaining 8 are `empty_confirmed`. By `data_type`: `trades`=1,273, `odds_horizon_bucket`=1,106, `trades_inplay`=111,
  plus a handful of `ODDS_MOVEMENT`/`ODDS_SNAPSHOT`/`odds_movement`/`odds_snapshot` (2 each). This is a distinct axis
  from the Track C todo's own scope (LADBROKES_UK/SPORT888/footystats-ODDS_API/FOOTBALL/UNKNOWN) — not conflated with
  it, not fixed inline, filed separately per the Findings Closure hard rule.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, unified-trading-pm]
scope: [engineer]
tags: [data-correctness, sports, venue, manifest, blank-value]
related:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md,
  ]
created: 2026-07-27
priority: P2
parent_epic: sports_master
source: >-
  Measured directly against the live gs://market-data-tick-sports-prd-central-element-323112/_index/
  availability_index.parquet via unified_trading_library.read_availability_index (columns=[date, venue, pipeline_mode,
  instrument_type, data_type, row_count, capture_status], no filter, full history), 2026-07-27, during
  sports_consolidated_native_ao_extract_2026_07_25.md's Track C todo. Ad-hoc read-only query, not yet a saved script.
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md,
    market-data-processing-service/market_data_processing_service/app/core/canonical_writer_shaping.py,
  ]
assigned_vm: planning
assigned_role: data_engineering
resolved_by: unified-api-contracts@b27717b8, instruments-service@5573f817
---

# Sports manifest rows with a blank `venue` string

## What was measured (2026-07-27)

Corpus-wide, no date/venue filter, live prod bucket:

- Total blank-venue (`venue==""`) rows: **2,498**
- `capture_status` breakdown: `captured`=2,490, `empty_confirmed`=8
- `data_type` breakdown (blank-venue rows only): `trades`=1,273, `odds_horizon_bucket`=1,106, `trades_inplay`=111,
  `ODDS_MOVEMENT`=2, `ODDS_SNAPSHOT`=2, `odds_movement`=2, `odds_snapshot`=2

This is a REAL, non-trivial population of genuinely captured rows (not honest-absence placeholders) with no venue
identity recorded. 2,490 captured rows with an unrecoverable-from-the-manifest-alone venue is a real gap for any
per-venue coverage/completeness view, and a candidate for silent double-counting or under-counting depending on how
downstream consumers treat a blank string vs. a missing key.

## What this doc is NOT claiming

Not yet root-caused. A plausible (not confirmed) hypothesis, given the SAME-DAY parser-bug family already fixed in
`market-data-processing-service@51502c3` / `instruments-service@f46e553e`
(`sports_closeout_batch1_ao_ready_2026_07_24.md` todo 2): `canonical_writer_shaping.py`'s
`_venue_token_from_canonical_id(raw, asset_group=SPORTS)` returns `parts[1] if len(parts) >= 2 and parts[1] else ""` —
an instrument_id whose bookmaker segment (position 1) is itself an empty string between colons (e.g.
`FOOTBALL::MATCH_ODDS:...`) would legitimately produce `venue=""` even with the asset_group gate correctly applied (the
gate fixes WHICH position is read, not what happens when that position is empty). This is UNCONFIRMED — not verified
against real captured row content, and the `trades`/`trades_inplay` data_types are RAW MTDS capture (not MDPS
candle-derived), so a different root cause (MTDS-side, not the MDPS candle-write bug) is equally plausible for those.
`odds_horizon_bucket` — the largest single chunk (1,106 rows) — IS one of the 4 registered sports candle adapters, so
the MDPS-side hypothesis is more plausible for that data_type specifically.

## Root-cause finding (2026-08-03)

**Both prior hypotheses (MDPS `_venue_token_from_canonical_id` parsing bug / an MTDS-side raw-capture bug) are
DISPROVEN.** Confirmed via a live corpus read + independent code verification (all citations re-read directly, not taken
on trust): every one of the 2,490 captured blank-venue rows carries `service_name="instruments-service"`,
`source="instruments_service"`, `pipeline_mode="batch_instruments_service"`, `schema_version=9`, a real (non-blank)
`league_id`, and a real non-zero `row_count` — this population is `trades`=1,273 + `odds_horizon_bucket` =1,106 +
`trades_inplay`=111 = exactly 2,490, i.e. these 3 data_types fully account for every captured blank-venue row (the doc's
other 8 blank-venue rows, `ODDS_MOVEMENT`/`ODDS_SNAPSHOT` × 2 casings, are ALL `empty_confirmed`, not `captured` — a
separate, lower-severity honest-absence population, not investigated further here).

**Actual writer**: `instruments-service/scripts/backfill_orphan_class_e_sports.py::record_cells()` (line ~240-262), NOT
MTDS or MDPS. This is a standing (not one-time) IS-owned "orphan recorder" — its sibling
`migration_orphan_sweep_sports.py` walks the MTDS tick bucket for real, un-manifested `trades`/`trades_inplay`/
`odds_horizon_bucket` objects (grain: `(day, data_type, league_id)`, `data_type` = the raw lower-case GCS path segment)
and `backfill_orphan_class_e_sports.py` writes IS-provenance manifest rows to cover them. Confirmed run against prod:
`estate_orphan_assessment_2026_07_21.md:93` ("odds — 4 cells recorded", 2026-07-22) and it is explicitly recommended for
RE-RUN in still-open work as late as 2026-07-26 (`sports_prelaunch_cf5_verify_residual_2026_07_24.md:93`,
`sports_satellite_ao_dispatch_batch5_2026_07_26.md:659,665,681`) — every future re-run repeats this exact mis-stamp on
any newly-found orphan cell.

**Exact mechanism** (every observed field accounted for):

1. `build_cells()` (`:190-209`) groups orphan objects into
   `CellPlan(day, data_type, league_id, source= SPORTS_DATA_TYPE_TO_SOURCE.get(dt, ""), members=[...])` — `dt` is the
   raw lower-case path segment (`trades`/`trades_inplay`/`odds_horizon_bucket`). `SPORTS_DATA_TYPE_TO_SOURCE`
   (`unified_api_contracts/canonical/domain/sports/league_data.py:209-249`, verified directly) has NO entry for any of
   these 3 keys (it only covers IS-owned reference entities — MATCHES/ODDS/PREDICTIONS/XG/FIXTURES*/TEAMS/
   STANDINGS/etc.) — so `cell.source = ""`.
2. `footer_verify()` (`:211-219`) footer-reads every real member parquet and sums real row counts into `cell.row_count`
   — this is why `row_count` is a real, plausible non-zero integer (matches real MTDS tick data, not a sentinel).
3. `record_cells()` (`:240-262`) instantiates `ManifestWriter(service_name="instruments-service", ...)` — the source of
   the observed `service_name`. Per cell it calls `resolve_source_and_mode(cell.data_type, cell.source)` (`:98-119`,
   verified directly) then `writer.add(..., venue="", source=source, pipeline_mode=pipeline_mode)` (`:251-260`) —
   **`venue=""` is a hardcoded literal**; `instrument_id`/`instrument_type` are simply never passed (default blank/None
   in the writer).
4. `resolve_source_and_mode()` (`:98-119`, verified) calls `get_source_priority("sports", data_type)` — UAC's
   `SOURCE_PRIORITY` (`unified_api_contracts/canonical/crosscutting/_source_priority_data.py`, verified directly)
   registers `("sports","TRADES"): ["odds_api"]` (line 77) and
   `("sports","ODDS_HORIZON_BUCKET"): ["mdps_odds_horizon_bucket"]` (line 97) — **UPPER-CASE keys only**, and
   `TRADES_INPLAY` is not registered under ANY casing. `get_source_priority()` (`_source_priority_core.py:22-48`,
   verified) is an exact-string dict lookup (`key = (asset_group, data_type)`) with NO case normalization — so the
   lower-case `"trades"`/`"trades_inplay"`/ `"odds_horizon_bucket"` cell keys ALWAYS miss, raising `KeyError` → caught
   at `:116-117` → `allowed = []` → `source` resolves to `""` (line 118, since `fallback_source=""` and `not allowed`) →
   line 119 falls back `_SOURCE_TO_PIPELINE_MODE.get("", PipelineMode.BATCH_INSTRUMENTS_SERVICE)` →
   `BATCH_INSTRUMENTS_SERVICE`.
5. Inside UTL `ManifestWriter.add()`, the blank `source` + batch `pipeline_mode` trips the "universal-provenance
   fallback for PRODUCER (batch) captured rows" (`_stamp_producer_source()`), which auto-stamps
   `source_string_for(BATCH_INSTRUMENTS_SERVICE)` = `"instruments_service"` — exactly the observed
   `source="instruments_service"`.

**The cells themselves are legitimate** (real MTDS tick data, correctly grain-keyed) — only the
`service_name`/`source`/`pipeline_mode` PROVENANCE columns are wrong, corrupting any downstream per-source/ per-producer
coverage rollup (undercounts real `odds_api`/`mdps_odds_horizon_bucket` captures, inflates
`instruments-service`-attributed captures with data IS never fetched).

**Recommendation per data_type** (per the todo's own done-when):

- `trades`: **needs writer fix** in `resolve_source_and_mode()` — uppercase `data_type` before the
  `get_source_priority`/`SPORTS_DATA_TYPE_TO_SOURCE` probes (or probe both casings) so it resolves the
  already-registered `("sports","TRADES") → odds_api`/`BATCH_ODDS_API`. Then **re-stampable**: a small, bounded
  corrective backfill (find rows with `service_name="instruments-service" AND data_type="trades"`, re-stamp
  `source`/`pipeline_mode` to `odds_api`/`BATCH_ODDS_API`) once the fix ships — not a wholesale re-record
  (`venue`/`league_id`/`row_count` are already correct).
- `odds_horizon_bucket`: same writer fix (case-normalization) resolves the already-registered
  `("sports","ODDS_HORIZON_BUCKET") → mdps_odds_horizon_bucket`. **Re-stampable** the same way, targeting
  `mdps_odds_horizon_bucket`/`BATCH_MDPS_ODDS_HORIZON_BUCKET`.
- `trades_inplay`: **needs writer fix + a new UAC registration** — `TRADES_INPLAY` has no `SOURCE_PRIORITY` entry under
  any casing, so case-normalization alone won't fix it; a real vendor/source needs to be registered for it first (same
  vendor as `trades`, `odds_api`, is the obvious candidate — not confirmed here, needs a human/owner check since it's a
  new UAC registry entry, not a pure code fix). **Re-stampable** once that registration + the writer fix both ship.

Follow-up code-fix work is tracked as new todo 2 below (this todo's own scope was read-only root-cause per the doc's
stated done-when).

- [x] 1. ✅ [DIAG] P2. Root-cause the 2,490 captured `venue=""` sports manifest rows. **Done** — see "Root-cause finding
      (2026-08-03)" above: the actual writer is
      `instruments-service/scripts/backfill_orphan_class_e_sports.py::record_cells()` (a case-sensitivity gap in its
      `resolve_source_and_mode()` helper, `:98-119`), not MTDS/MDPS as originally hypothesized. All 3 affected
      data_types have a written finding + recommendation.
- [x] 2. ✅ [SCRIPT] P2. **Fix `resolve_source_and_mode()`'s case-sensitivity gap** in
      `instruments-service/scripts/backfill_orphan_class_e_sports.py` (uppercase `data_type` before the
      `get_source_priority`/`SPORTS_DATA_TYPE_TO_SOURCE` probes) so `trades`→`odds_api` and
      `odds_horizon_bucket`→`mdps_odds_horizon_bucket` resolve correctly on the next re-run. Register `TRADES_INPLAY` in
      UAC `SOURCE_PRIORITY` (owner/vendor TBD — likely `odds_api` matching `trades`, needs confirmation) so it also
      resolves. Then run a bounded corrective backfill re-stamping the 2,490 already-recorded rows'
      `source`/`pipeline_mode` columns (not `venue`/`league_id`/`row_count`, which are already correct) — see the
      per-data_type recommendation above. Repo: instruments-service (fix) + unified-api-contracts (TRADES_INPLAY
      registration). **Done — instruments-service@5573f817 + unified-api-contracts@b27717b8**, see Progress Log
      2026-08-03 entry below.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> `assigned_vm: planning` — the sole `[DIAG] P2` is a read-only
  root-cause with an explicit stated done-when ('a written root-cause finding for each affected data_type, with a
  re-stampable / needs-writer-fix / accept-as-is recommendation'), i.e. an audit whose outcome is determinable by the
  worker alone. Partial progress already recorded 2026-07-29; the remaining step (read the RAW parquet content behind
  one sampled shard atom) is bounded and touches no delete/VM-launch. Conflict-check CLEAR: the doc itself states this
  is a distinct axis from `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track C venue re-stamp, and no active
  planning doc claims the blank-`venue` root cause.
- **context-scout 2026-08-03**: re-read in full; existing context_scope (4 entries) still accurate — no new source
  target or SSOT surfaced beyond what's already listed. Refreshed marker only.
- **2026-08-03** (AO dispatch, slot 2) — Todo 1 done. Both prior hypotheses (MDPS candle-shaping parser bug / MTDS-side
  raw-capture bug) DISPROVEN — a live corpus read (5-6 wide columns, bounded read via `run-bounded-analysis.sh`) found
  every captured blank-venue row carries `service_name="instruments-service"`, `source="instruments_service"`,
  `pipeline_mode="batch_instruments_service"`, real `league_id`/`row_count`. Traced
  - independently re-verified (every file:line re-read directly, not taken on trust) to
    `instruments-service/scripts/backfill_orphan_class_e_sports.py::resolve_source_and_mode()` — a case-sensitivity gap:
    it probes UAC `SOURCE_PRIORITY`/`SPORTS_DATA_TYPE_TO_SOURCE` with the raw lower-case GCS path segment
    (`trades`/`trades_inplay`/`odds_horizon_bucket`) but both registries key on UPPER-CASE data_type strings, so the
    lookup always misses and falls through to the `instruments-service` producer-fallback.
    `TRADES`/`ODDS_HORIZON_BUCKET` ARE already registered (uppercase) with correct real sources
    (`odds_api`/`mdps_odds_horizon_bucket`) — only the case mismatch blocks resolution; `TRADES_INPLAY` has no
    registration at all under any casing. The underlying cells/row_counts are real and correct; only the provenance
    columns are wrong. Filed follow-up todo 2 (writer fix + UAC registration + bounded re-stamp backfill) since this
    todo's own scope was read-only root-cause.
- **2026-08-03** (AO dispatch, slot 14) — Todo 2 done. The case-sensitivity fix itself was already shipped
  (`instruments-service@d9994199`, a concurrent slot-12 dispatch of the same todo) — verified via `git log` before
  starting, not re-done. Remaining scope completed this turn: (1) registered `("sports", "TRADES_INPLAY"): ["odds_api"]`
  in UAC `SOURCE_PRIORITY` (`unified-api-contracts@b27717b8`) — same odds_api writer family as `TRADES`, confirmed via
  the market_data_categories.py "3 deliberate non-registrations" comment that `SPORTS_DATA_TYPE_TO_SOURCE` (the v2
  expected-universe enumerator's iteration axis) is a DIFFERENT registry than `SOURCE_PRIORITY`, so this addition does
  not reopen the expected-universe flood those non-registrations exist to prevent; also added the paired
  `AVAILABILITY_AT_SEMANTICS` entry and a `_SOURCE_PRIORITY_CASE_FALLBACK_KEY` reachability exclusion (both required by
  `test_validity_matrix_completeness.py`'s closed-set completeness tests, mirroring `TRADES`'s existing entries) — full
  QG green. (2) Ran the corrective backfill (new script
  `instruments-service/scripts/restamp_sports_orphan_source_provenance_2026_08_03.py`, reuses
  `resolve_source_and_mode()` directly so it can't drift from the writer's own resolution) against PROD
  `market-data-tick-sports-prd-central-element-323112`: dry-run matched exactly 2,490 rows split
  trades=1,273/odds_horizon_bucket=1,106/trades_inplay=111 (matching the root-cause finding's own counts exactly),
  snapshot taken before write, `--apply` restamped all 2,490, re-verified GREEN (0 remaining mis-stamped rows, total row
  count unchanged at 645,045). `venue`/`league_id`/`row_count` untouched, only `source`/`pipeline_mode`. Shipped:
  `unified-api-contracts@b27717b8`, `instruments-service@5573f817`.
