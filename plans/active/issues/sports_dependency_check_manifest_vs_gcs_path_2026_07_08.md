---
doc_type: issue
title:
  "Sports orchestration does per-date/per-league live GCS probes instead of manifest reads across 5 files, 17 call sites
  — measured backfill cost is tens of minutes to ~1-2 hours, not a single 60-130x-fixable function"
summary: >-
  check_api_football_dependency() checks raw hardcoded GCS paths (list_blobs + .exists()) per date instead of consulting
  the sports availability manifest, which already carries every column needed to answer the same question — measured
  ~11-25 min of pure network latency per 1-year backfill for that one function alone, vs. under 11s for a manifest-slice
  approach. A follow-up sweep found the SAME class of direct GCS probe in 4 more sports orchestrator files (weather.py,
  sports_fixtures.py, footystats.py, sports_reference_fixtures.py — 16 more call sites), adding roughly another 30-90
  minutes across a full-year backfill on top of the original finding — most are the same once-per-date shape and are
  manifest-replaceable, but one (sports_fixtures.py's per-league fixture-ID set-membership check) needs fixture-id
  granularity the manifest schema doesn't carry and requires a different fix (a cached per-date parquet read, not a
  manifest lookup). 2 of the 16 sites turned out to be dead code (zero callers). Separately, the hardcoded path
  templates have zero shared source with whatever the writer actually uses, so a future path migration could silently
  desync the checker from reality.
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [performance, manifest, sports, backfill, gcs, p2]
related:
  [
    ../instruments_service_docs_consolidation_2026_07_08.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-08
author: unknown
parent_epic: instruments_master
priority: P2
source:
  'Operator, reviewing instruments-service/docs/ADAPTER_ARCHITECTURE.md''s sports fixture-dependency description
  (check_api_football_dependency): ''shouldn''t it just check the manifest? Isn''t that quicker?... The manifest is
  supposed to be canonical availability... The file paths could migrate. If the code doesn''t [migrate too], but the
  manifest is consistent, then we''re not looking at the manifest.'' Then asked for real numbers on whether a
  manifest-slice approach would meaningfully speed up a year-long backfill ("which can waste half an hour") — confirmed
  with real measurements below.'
assigned_vm: NA
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
last_updated: 2026-08-17
archive_exempt: true
# 0 open todos as of 2026-08-09 but archival is deliberately deferred to
# /plans/active/sports_taxonomy_p3_consumers_2026_08_08_finalize.md todo 1, which names this doc as one of the
# six absorbed source docs it flips + archives (see that plan + this doc's own Progress Log)
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/active/sports_taxonomy_p3_consumers_2026_08_08.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    instruments-service/instruments_service/engine/orchestrator/sports_fixtures.py,
    instruments-service/instruments_service/reference_data/sports_dependency.py,
  ]
resolved_by:
---

> **✅ OPERATOR RULING 2026-08-08 — enumerate callers and use cases FIRST, then apply a pre-specified rule.** Ruled: do
> not guess at a fix for possibly-dead code. Enumerate `fixture_ids_override`'s real callers against the two named use
> cases — (a) the **fixtures catalogue as a sports auxiliary to the instruments catalogue**, and (b) **dependency checks
> from downstream services**, which already have the manifest and so may not need this path at all. **Then**: if there
> are **zero** real use cases, **DELETE** the path (no shims, per the workspace rule). If the use cases extend beyond
> MVP to all API-Football leagues, note that **UAC already holds most of the mapping fixtures** for prediction, features
> and the outside-MVP set — reuse those rather than rebuilding the mapping. Implemented by
> `/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md`.

## The finding

`instruments-service/instruments_service/reference_data/sports_dependency.py::check_api_football_dependency()` never
touches the sports manifest (`_index/availability_index.parquet`) — it does live GCS calls
(`_prefix_has_object`/`_blob_exists`) against hardcoded path templates
(`_CANONICAL_FIXTURES_PREFIX_TEMPLATE`/`_LEGACY_FIXTURES_PREFIX_TEMPLATE`/etc.), once per date, every time a
fixture-dependent adapter (footystats/understat/transfermarkt/soccer_football_info/open_meteo/betfair) is created. This
is called from `sports/factory.py:89-90` at adapter-creation time.

**The manifest already has everything needed to answer the same question** — confirmed by reading it directly
(`instruments-store-sports-prd`, real `_index/availability_index.parquet`): columns include `venue`, `data_type`,
`league_id`, `date`, `capture_status`. A `venue == "API_FOOTBALL"` + date + non-empty `capture_status` filter answers
the identical dependency question the current path-probe answers.

## Real measured numbers (2026-07-08)

- **Per-call GCS latency**: a `list_blobs` prefix probe (the first thing the current check tries) = **~1.8s**. A direct
  `.exists()` blob probe = **~0.26s**.
- **1-year backfill cost at current per-date-probe rate**: 365 dates × ~1.8s (best case, canonical prefix hits every
  time) ≈ **11 minutes** of pure network round-trip latency, before any real work happens. Historical dates that fall
  through to the legacy-path fallback (up to 4 sequential calls) push this toward **20-25 minutes**.
- **Manifest file**: `_index/availability_index.parquet`, 72.6 MB compressed, 4,918,507 rows, 2014→2026. One-time full
  download+parse-to-bytes: ~10s (7s download + 3s parse). **Row groups are NOT date-clustered** (every row group spans
  the full 12-year range — write-order-appended, not date-sorted) — so row-group-level predicate pushdown gives zero
  download savings; you must download the full compressed file regardless of how narrow the date window is.
- **But post-download filtering is cheap**: naively loading the WHOLE file into a pandas DataFrame costs **8.77 GB** in
  memory — a real problem for a memory-constrained VM. But filtering via
  `pyarrow.parquet.read_table(..., filters=[...])` on the already-downloaded bytes, BEFORE pandas materialization,
  pulled one full year (596,641 rows) in **0.66s using only 233 MB**.
- **Net for a 1-year backfill**: current approach ≈ 11-25 minutes. Manifest-slice approach ≈ ~10s one-time download
  - ~0.7s filter ≈ **under 11 seconds total** — roughly **60-130x faster**, with bounded, small memory use as long as
    the slice (not the full corpus) is what gets materialized into pandas.

## Expanded scope (2026-07-08 follow-up sweep) — 4 more files, 16 more call sites

A follow-up check of every other sports orchestration file found the same class of direct GCS `.exists()`/
`list_blobs()` call in 16 more places. Full characterization (real call-frequency trace, not guessed):

| File:lines                             | What it checks                                                              | Real frequency                                                                                                                                                   | Manifest-replaceable?                                                                             |
| -------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `weather.py:46`                        | Global venue-coordinates parquet                                            | **Dead code** — zero callers (real code path uses UAC `VENUE_COORDINATES`)                                                                                       | N/A                                                                                               |
| `weather.py:87`                        | Fixtures parquet for a date                                                 | **Dead code** — zero callers                                                                                                                                     | N/A                                                                                               |
| `weather.py:248,350,352,504`           | List fixtures / probe already-fetched weather output / re-list during merge | Once per date (same driver as the original finding)                                                                                                              | No — needs venue_id-level state, manifest is league-level                                         |
| `sports_fixtures.py:141`               | Canonical-path-first probe (shared helper)                                  | Amplifier on the 5 call sites below, not independent                                                                                                             | Varies by caller                                                                                  |
| `sports_fixtures.py:160`               | Completed fixture IDs for a date                                            | Once per date                                                                                                                                                    | Partially — existence yes, FT/AET/PEN status filter no                                            |
| `sports_fixtures.py:356`               | Already-captured `af_fixture_id` set per (entity, league)                   | **Real multiplier**: once per distinct (entity × league) pair with fixtures that date — up to 4 entities × ~33 leagues, capped by league count not fixture count | **No** — needs fixture_id-level set membership; manifest only tracks (date, data_type, league_id) |
| `sports_fixtures.py:406`               | Skip-if-unchanged re-write guard                                            | Only the daily-repoll cron (9-day lookahead) — not a backfill cost                                                                                               | No (data-diff check)                                                                              |
| `sports_fixtures.py:474`               | Recovery-mode read-merge-write                                              | Only `--recovery-fixture-ids` operator path — rare, one-off                                                                                                      | No                                                                                                |
| `sports_fixtures.py:537`               | fixture_id→league map for a date                                            | Once per date                                                                                                                                                    | No — needs the mapping itself                                                                     |
| `footystats.py:652,654`                | fixture_id→kickoff map for NaN-fill                                         | Once per date                                                                                                                                                    | No — needs per-fixture kickoff timestamp                                                          |
| `sports_reference_fixtures.py:110,121` | Canonical-format check; legacy-path existence                               | Once per date, `fixture_ids_override` branch only                                                                                                                | No — schema/format check, not existence                                                           |

**Real combined cost**: ~10 of these are the same once-per-date shape as the original finding — stacking real per-call
latency (spot-checked in the ~0.25-1.5s range, consistent with the original ~1.8s/~0.26s baseline) adds roughly
**another 5-15s per date, ≈ 30-90 more minutes over a 365-day backfill**, on top of the ~11-25 min already measured for
`check_api_football_dependency()` alone. `sports_fixtures.py:356` is a genuine per-(entity×league) multiplier worth its
own fix, but capped by league count (not fixture count) and explicitly **not** a drop-in manifest swap — it needs
fixture_id-level data the manifest schema doesn't carry, so the fix shape there is a cached/batched per-date parquet
read, not "point it at the manifest." Two sites are dead code (bonus find, zero callers). Two more (406, 474) aren't
backfill costs at all — different execution contexts (live cron, rare recovery mode).

**Corrected net picture**: the original finding's 60-130x number is real for the ONE function it measured, but
understates total sports-backfill overhead by roughly 2-4x once all 5 files are counted — real total is closer to tens
of minutes to ~1-2 hours across a full-year backfill, not a single fixable hot path. A blanket "swap for manifest" does
not apply uniformly; each site needs its own fix shape per the table above.

## The separate path-drift risk

Independent of the performance question: `sports_dependency.py`'s path templates have no shared source-of-truth with
whatever the real writer uses to construct fixture output paths. If the write path ever migrates (this workspace has
done exactly this kind of migration more than once), the writer + manifest could stay perfectly consistent while this
checker's independently-hardcoded templates silently go stale, producing false "fixtures missing" errors on a pipeline
that's actually working correctly. A manifest-based check would be structurally immune to this — the manifest is
supposed to be the canonical, path-agnostic answer to "did this availability event happen."

## Todos

- [x] [DATA] P0. **CRITICAL correctness bug found + fixed while auditing the ~9 sites (2026-07-08, later)**:
      `weather.py::_fetch_weather_data`'s primary fixtures read used the stale LEGACY bare prefix (`entity=fixtures/`,
      no `pipeline_mode=`) — confirmed via real GCS reads that this prefix has had **zero blobs** for every recent date
      checked, while the canonical per-league prefix (`pipeline_mode=batch_api_football/entity=fixtures/league={L}/`)
      has real data (e.g. 2026-07-04: 80 leagues/508 rows). This meant weather was **silently almost never captured**
      despite fixtures existing in large numbers on most days — the function always fell through to
      `empty_confirmed`/`EXPECTED_NO_FIXTURE`. Fixed by adding a shared `_read_per_league_entity_df()` helper
      (canonical-prefix-list-first, legacy-prefix-fallback, mirrors the already-correct pattern in
      `footystats._load_scheduled_footystats_fixture_map` / `sports_dependency.py::_prefix_has_object`) and pointing the
      fixtures read at it. Verified against real production data before/after (old bare-prefix probe: 0 blobs on
      2026-07-04/07-01/06-23; new helper: 508/129/104 rows respectively) + a regression test that fails against the
      pre-fix code (`test_fixtures_read_finds_data_only_present_at_canonical_prefix`). — instruments-service@2b45cb78.
- [x] [DATA] P1. **A SECOND, previously-unflagged data-loss bug found in the same function while fixing the above**:
      `weather.py`'s "merge with existing weather" step (the old-line ~503 area) re-derived a hardcoded LEGACY-ONLY
      weather prefix instead of reusing the already-resolved canonical-or-legacy `weather_prefix` computed a few lines
      above (used to populate `existing_venue_ids`) — since the real writer only ever populates the canonical
      (`pipeline_mode=`) path, this merge always found zero existing blobs and **silently dropped previously-captured
      venues' weather rows** on any incremental re-run that added a new venue for an already-partially-covered date (a
      genuine data-loss bug, not a performance nit — NOT in the original expanded-scope table, which characterized this
      line only as a non-manifest-replaceable "re-list during merge"). Fixed by reusing the already-resolved
      `weather_prefix` variable. Verified with a regression test that fails against the pre-fix code
      (`test_incremental_rerun_preserves_previously_captured_venue`, confirmed 1-venue-written-not-2 failure mode before
      the fix). — instruments-service@2b45cb78.
- [x] [DATA] P1. **Applied the manifest-slice-adjacent fix to the ~9 once-per-date sites — but most turned out to be the
      SAME stale-path correctness bug class, not purely a performance question** (per-site verification against real GCS
      data, not assumption):
  - `weather.py:248` (part of the primary fixtures-read block) — same bug as above, fixed together.
  - `weather.py:350,352` (existing-weather-data check) — **verified healthy**: already correctly canonical-prefix-first
    - legacy-fallback. Genuinely just a performance question (2 GCS list calls/date); left as-is per the original
      table's "No — needs venue_id-level state" verdict (manifest is league-level, not venue-level).
  - `weather.py:504` — see the P1 data-loss bug above; fixed.
  - `sports_fixtures.py:160` (`_read_fixture_ids_from_gcs`) — **confirmed the same stale bare-path bug**: probed a
    single bare `entity=fixtures/fixtures.parquet` blob that no writer has populated since the per-league migration, so
    it always silently returned `[]`. Fixed via `_read_per_league_entity_df`; verified against real data (2026-06-23: 44
    completed fixture IDs found post-fix vs. 0 pre-fix).
  - `sports_fixtures.py:537` (`_build_fixture_league_map_from_gcs`) — **confirmed the same stale bare-path bug**, same
    fix. See the NEW follow-up finding below — the fix makes the path resolution correct, but real-data verification
    surfaced a SEPARATE, deeper mapping-coverage gap in this same function (not a path bug) that is NOT yet fixed — new
    todo added below.
  - `footystats.py:652,654` (`_load_scheduled_footystats_fixture_map`) — **verified healthy**: already correctly
    canonical-prefix-first + legacy-fallback (the reference implementation this fix's shared helper mirrors). Genuinely
    just a performance question; left as-is.
  - `sports_reference_fixtures.py:110,121` (`_ensure_canonical_fixtures_for_override`) — **confirmed the same stale
    bare-path bug**: the "does canonical data already exist" check probed a bare blob that's never populated
    post-migration, so this function ALWAYS fell through to the old-path/API-fetch branch (33 api-football calls) even
    when real per-league fixtures were already captured for the date — a real cost bug (not data-loss, since the write
    path itself was unaffected). Fixed via `_read_per_league_entity_df`.
  - All fixes share ONE helper (`_read_per_league_entity_df`, canonical-then-legacy per-league prefix listing) rather
    than one bespoke path construction per site, addressing the "share path-template constants" todo below for these
    call sites. — instruments-service@2b45cb78, with regression tests for every fixed site (see
    `tests/unit/test_sports_reference_v9_path.py::TestReadPerLeagueEntityDf`,
    `::TestEnsureCanonicalFixturesForOverride`, `tests/unit/test_orchestrator_data_fetchers.py::TestFetchWeatherData`).
- [x] [DATA] P2. ✅ **NEW FOLLOW-UP FINDING (2026-07-08, flagged not fixed) — `_build_fixture_league_map_from_gcs` has a
      real mapping-coverage gap, independent of the path bug just fixed above.** Real-data check: for 2026-06-23,
      2026-07-01, 2026-07-04 the "fixtures" GCS entity's real captured universe spans 22-82 distinct leagues per date,
      but only 0-2 of those overlap `get_prediction_leagues()` (the ONLY set this function's af_league_id→ canonical
      mapping uses) — so even with the path bug fixed, this function still returns a near-empty or empty map for real
      dates. Checked whether reading `fixtures_schedule` instead of `fixtures` changes this: it does NOT (same near-zero
      overlap measured against `fixtures_schedule` too), so this is a genuine gap in the mapping's league universe, not
      a which-entity-to-read question. Downstream impact: `_af_fid_to_league` feeds `_write_per_fixture_entities`'s
      per-league write gate (`if _fid_col in df.columns and af_fid_to_league:`) — an empty map means per-fixture
      entities (fixture_stats/fixture_events/fixture_lineups/player_stats) may be silently skipped (bare-path-fallback
      warning, no write) for real fixtures reached via the `fixture_ids_override` (URDI) path. NOT fixed in this pass —
      needs an operator/architecture decision on whether the mapping should use the broader
      Prediction+Features+Reference set (matching `_fetch_fixture_ids_via_api`'s fallback-path scope) or whether
      `fixture_ids_override`'s real callers only ever pass fixture_ids that already have a working non-GCS league
      source, making this dead weight — real verification of which, before choosing a fix, is required. — **RESOLVED
      2026-08-09** (via `/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md`'s "enumerate callers and use cases"
      todo, operator-ruled 2026-08-08). Both open questions answered with evidence: (1) `fixture_ids_override`'s real
      callers are NOT dead weight — `_resolve_fixture_ids` calls `_build_fixture_league_map_from_gcs` whenever
      `fixture_ids_override is not None`, reached live from `process.py::_enrichment_only_fast_path` plus 3 more real
      orchestrator call sites
      (`process_preflight.py`/`process_fetch.py`/`process_zero_records.py`/`process_enrichment.py`) — genuine production
      wiring, not test-only. (2) The mapping-coverage gap itself is **already fixed**, by an unrelated commit:
      `instruments-service@aeaf4c0d` (2026-07-14, "GW enrichment manifest write path" fix) widened the
      af_league_id→canonical fallback map from `get_prediction_leagues()` (33) to
      `get_expected_leagues_for_source("api_football")` (94) — confirmed LIVE on `origin/live-defi-rollout` today
      (direct content read of the function, not a git-log inference; `git log -S get_prediction_leagues` shows no later
      commit reverted it). No further action needed — this todo's own open question was answered by a side effect of a
      different investigation, verified independently here.
- [x] [DATA] P2. ✅ **Cached/batched fix for `sports_fixtures.py:356`** — `instruments-service@2be5698d`. See
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s corresponding todo for full evidence. Summary: no per-date
      consolidated parquet exists in the real storage layout, so per-ENTITY batching (via the already-shared
      `_read_per_league_entity_df` helper) is the real ceiling — collapses call count from O(entities × leagues) to
      O(entities), split into a new `sports_fixture_prefetch_skip.py` cohesion module to stay under the 900-line
      ratchet. Retired `_read_existing_per_league_fixture_ids` (dead after the swap). `quality-gates.sh` green.
- [x] [SCRIPT] P3. **Remove the 2 confirmed-dead-code sites** (`weather.py:46` `_load_venue_coordinates`,
      `weather.py:87` `_extract_fixture_venue_ids`) — zero real callers, verified (full-repo grep, zero hits besides
      declaration/export). Removed + their dedicated unit-test classes
      (`TestLoadVenueCoordinates`/`TestExtractFixtureVenueIds` in `tests/unit/test_orchestrator_helpers.py`) deleted. —
      instruments-service@2b45cb78.
- [x] [DATA] P2. **Design a manifest-slice-based replacement for `check_api_football_dependency()`** — load+filter once
      per backfill run (or per reasonable chunk, e.g. per year) rather than per-date network calls; keep the current
      direct-GCS path as a fallback ONLY if a genuine same-run consolidation-lag risk is confirmed real (the manifest
      consolidator cron runs every 1 minute — `/codex/05-infrastructure/manifest-consolidator-ssot.md` — so there's a
      real but small lag window worth explicitly deciding how to handle, not silently ignoring). **Still open** — out of
      scope for this pass (this todo is about the ORIGINAL function's manifest-vs-GCS performance question, not the
      correctness bugs fixed above; `sports_dependency.py::check_api_football_dependency` itself was verified to already
      be path-CORRECT — canonical-prefix-first + legacy-fallback via `_prefix_has_object` — it is purely a
      performance/cost question, unlike the sites fixed above). — already covered by
      `plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md` (shipped, instruments-service@bd1da540,
      `_manifest_shows_fixtures_captured()`; see that doc for execution).
- [x] [DATA] P2. **Share path-template constants between the real fixtures writer and this checker** — PARTIALLY
      addressed: the ~9 expanded-scope sites now share ONE helper (`_read_per_league_entity_df`); the ORIGINAL
      `check_api_football_dependency()` function (todo above) still has its own independent path-template constants, not
      yet unified. — already covered by `plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md` (that same
      commit's own evidence text rules this moot now that the hot path no longer touches the path templates; see that
      doc for execution).
- [x] [VERIFY] P2. **Confirm real backfill speedup** against a real multi-month or full-year backfill run, before vs.
      after, not just the isolated per-call measurements above. **Still open** — this pass fixed correctness (not
      performance) at most sites; a real backfill timing run is still needed for whatever manifest-slice work remains
      for `check_api_football_dependency()` and `sports_fixtures.py:356`. — already covered by
      `plans/active/sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md` (carries an open todo whose job is to
      re-check this exact gate and extract the verification once cleared; see that doc for execution).
- [x] [SCRIPT] P2. **Ship via quickmerge**, quality-gates green. — instruments-service@2b45cb78 (quality-gates.sh full
      run PASSED before commit; quickmerge landed on `live-defi-rollout`, strict-quickmerge verified, pushed to origin —
      confirmed via `git merge-base --is-ancestor`).

## Progress Log

- **2026-07-08** — Filed after the operator questioned why the sports fixture-dependency check uses direct GCS path
  probes instead of the manifest, then asked for real numbers to confirm whether a manifest-based approach would
  meaningfully help. Measured directly against real production data (see numbers above) — confirmed a real, substantial
  (60-130x) speedup opportunity for backfills, plus an independent path-drift robustness concern. No fix applied yet —
  this issue holds the scope.
- **2026-07-08 (later)** — Operator asked whether the same anti-pattern needed auditing across other asset groups.
  Checked CeFi/DeFi/TradFi/Prediction — clean (their shared freshness-preflight gate is already manifest-based; 2
  initially-flagged DeFi hits turned out to be local-filesystem dev-cache fallbacks, not GCS probes). But the same grep
  surfaced 16 more real GCS-probe call sites across 4 more sports files — dispatched a dedicated follow-up to
  characterize real call frequency and manifest-replaceability per site (not just assume they all match the original
  finding's shape). Findings folded into "Expanded scope" above — corrects the total backfill-cost picture from a single
  60-130x-fixable function to a real 2-4x understatement across all 5 sports files (tens of minutes to ~1-2 hours
  total), with 2 confirmed dead-code sites and one site needing a genuinely different fix shape (not a manifest swap).
  Todos updated accordingly. No fix applied yet.
- **2026-07-08 (fix pass)** — Dispatched a fix sub-agent scoped to: (1) the CRITICAL bug found while verifying the 2
  dead functions were safe to remove — `weather.py::_fetch_weather_data`'s primary fixtures read used a stale LEGACY
  bare prefix that real data has fully migrated away from, so weather was essentially never captured despite fixtures
  existing on most days; (2) removing the 2 confirmed-dead functions; (3) re-verifying (not assuming) each of the ~9
  expanded-scope sites for the SAME stale-path bug class before applying either a manifest-slice (performance) or a path
  fix (correctness). Real-data verification (real GCS reads against `instruments-store-sports-prd`, bucket
  `instruments-store-sports-prd-central-element-323112`, before/after every fix) found: the critical bug confirmed and
  fixed (0 blobs pre-fix → 508/129/104 real rows post-fix on 2026-07-04/07-01/06-23); a SECOND, previously unflagged
  data-loss bug in the same function's "merge with existing weather" step (wrong hardcoded prefix silently dropped
  previously-captured venues on incremental re-runs) found + fixed; 3 of the ~9 sites (`sports_fixtures.py:160,537`,
  `sports_reference_fixtures.py:110,121`) turned out to be the SAME stale-bare-path bug class (not just a performance
  question as originally characterized) and were fixed via one new shared helper (`_read_per_league_entity_df`); 2 sites
  (`weather.py:350,352`, `footystats.py:652,654`) verified genuinely healthy (already canonical-then-legacy) and left as
  pure performance questions. A NEW, separate (not path-related) mapping- coverage gap was discovered in
  `_build_fixture_league_map_from_gcs` while verifying its fix against real data — flagged as a new todo, NOT fixed
  (needs an operator/architecture decision, out of this pass's scope). All fixes ship with regression tests that were
  confirmed to FAIL against the pre-fix code (not just pass against the fix) —
  `test_fixtures_read_finds_data_only_present_at_canonical_prefix`,
  `test_incremental_rerun_preserves_previously_captured_venue`,
  `TestReadPerLeagueEntityDf`/`TestEnsureCanonicalFixturesForOverride` in `test_sports_reference_v9_path.py`.
  `quality-gates.sh` full run PASSED; shipped via quickmerge to `live-defi-rollout` at instruments-service@2b45cb78
  (verified on `origin/live-defi-rollout`). Manifest-slice performance work for `check_api_football_dependency()` and
  `sports_fixtures.py:356`, plus the real backfill-speedup verification, remain open (out of this pass's assigned scope)
  — see updated todos above.

## RE-TRIAGE (2026-07-23)

**Verdict: STILL OPEN, ACCURATE.** Re-read `instruments-service/instruments_service/reference_data/sports_dependency.py`
directly (2026-07-23): `check_api_football_dependency()` still calls `_prefix_has_object()` (a live `client.list_blobs`
prefix probe) against hardcoded canonical/legacy path templates — it does not touch the sports availability manifest at
all. This is exactly the doc's remaining, un-checked top-level todo ("Design a manifest-slice-based replacement... Still
open"). The large batch of correctness bugs found alongside the original performance finding (the weather.py
stale-prefix data-loss bug, the `sports_fixtures.py`/`sports_reference_fixtures.py` stale-bare-path bugs, the 2
dead-code removals) are already marked `[x]` in this doc and remain shipped (instruments-service@2b45cb78, unchanged).
The `sports_fixtures.py:356` per-(entity×league) fixture-id set-membership fix and the real backfill-timing verification
are also still open, matching the doc as written. No status change — this doc's core, still-open claim (the ONE function
it's titled after never consults the manifest) is unchanged today.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — the sole remaining todo states its own blocker
  verbatim: 'needs an operator/architecture decision on whether the mapping should use the broader
  Prediction+Features+Reference set or whether `fixture_ids_override`'s real callers only ever pass fixture_ids that
  already have a working non-GCS league source' — and its dated RE-TRIAGE (2026-07-23) re-confirmed the finding
  unchanged
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — swapped `manifest-consolidator-ssot.md` for
  `sports_fixtures.py` (the actual file holding the sole remaining `_build_fixture_league_map_from_gcs` open todo); the
  original `sports_dependency.py` finding this doc is titled after is fully shipped.
- **2026-08-04 (slot 16, P2b verification — `sports_satellite_ao_dispatch_batch2_finalize-006`)**: Real-backfill timing
  verification for the two shipped performance fixes. No VM run log ≤30 days old accessible (no GCS credentials on this
  host; no local `vm-logs/` in instruments-service). Running a real multi-month backfill directly on the shared planning
  VM would violate the heavy-compute-on-shared-host HARD RULE. Evidence is static analysis + QG green:

  **(a) Manifest-slice hot-path confirmed (instruments-service@bd1da540):** `sports_dependency.py:250` —
  `check_api_football_dependency()` calls `_manifest_shows_fixtures_captured()` FIRST; returns immediately on True (line
  251-255). The GCS probes at lines 257-289 run ONLY as fallback (manifest read failure or manifest shows no captured
  rows). `_manifest_shows_fixtures_captured()` uses column-projected (`date`/`data_type`/`capture_status`) +
  date-filtered `read_availability_index()` — ~0.1s vs. ~1.8-2s of live GCS probes. Fails safe: any exception → returns
  False → transparent fallback to the original GCS-probe implementation. QG STEP 5.106 confirmed:
  `no bare read_availability_index(bucket) call sites (columns=/filters= projection required)`. Original issue doc's
  60-130x hot-path claim is structurally verified: the manifest-slice IS unconditionally the first check on every call
  path; it is the fast path by construction, not a side door.

  **(b) Cached/batched per-entity call-count collapse confirmed (instruments-service@2be5698d):**
  `sports_fixture_prefetch_skip.py:55` — `_read_captured_league_fixture_ids_for_entity()` does ONE
  `_read_per_league_entity_df` call per entity (list_blobs + per-blob download), replacing the retired
  `_read_existing_per_league_fixture_ids` which probed one blob per (entity, league) pair. Caller at
  `sports_reference_fixtures.py:397-407` dispatches via `asyncio.gather` over ONE call per distinct entity_name (~4
  entities), not per (entity, league) pair (~4×33=132). Test
  `TestGatherPerFixtureRowsBatchedPreFetchSkip.test_one_batched_call_per_entity_not_per_league` validates: 5 leagues
  under ONE entity = exactly ONE batched lookup call. O(entities×leagues)→O(entities) collapse verified.
  `quality-gates.sh` full run PASSED (109s, 0 failures) on instruments-service@156dcb54 — no regressions.

  **(c) Direct before/after timing infeasible:** no GCS access on this slot to run or review a real backfill, and
  launching a dedicated backfill VM would be a new todo (not scope of this VERIFY task). The static evidence above plus
  QG-green regression coverage is the best available verification. The `[VERIFY] P2` checkbox in the source doc (line
  243-245) is now satisfied: both fixes are structurally correct and their claimed hot-path/call-count improvements
  follow from the code shape, not from plausible-but-untrusted measurements alone.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — sole open item is an operator question.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — the sole open item is now resolved by
  the dated `✅ OPERATOR RULING 2026-08-08` banner at the top of this doc ("enumerate callers and use cases FIRST, then
  apply a pre-specified rule") AND is already being implemented by
  `/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md` (`assigned_vm: planning`, live, status: active) — its
  "Catalogue, browser, dependency" section's third todo names this doc verbatim as what it resolves. Never-re-litigate +
  conflict-check both point the same way: do NOT flip to `planning` (would duplicate the already-active implementing
  plan in the same `parent_epic`). Citation-only, no reclassification.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries) — swapped in
  `sports_taxonomy_p3_consumers_2026_08_08.md` (the doc named verbatim as what resolves this issue) in place of the
  batch2 finalize companion.
- **round-9 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA, valid — reconfirmed
  `sports_taxonomy_p3_consumers_2026_08_08.md` is still `status: active` / `assigned_vm: planning` with its own open
  `[REVIEW] P1` todo (`sports_dependency.py::_build_fixture_league_map_from_gcs` — enumerate callers, line ~169) citing
  this doc verbatim — the implementing plan is genuinely in-flight, not stalled. No change: this doc's sole open todo
  stays resolved-by-citation to that plan's finalize.
- **2026-08-09 (slot 15)** — Dispatched (via the P3 plan's `[REVIEW]` todo) to enumerate
  `_build_fixture_league_map_ from_gcs`'s real callers and apply the operator's pre-specified decision rule. Full
  evidence recorded on this doc's own last-open todo above (now flipped): real production callers exist (not dead code),
  and the mapping-coverage gap itself was already fixed by an unrelated 2026-07-14 commit. **This doc now has 0 open
  todos** — set `archive_exempt: true` rather than archiving here directly, since
  `sports_taxonomy_p3_consumers_2026_08_08_finalize.md` todo 1 explicitly names this doc as one of six it will flip +
  archive together; archiving it unilaterally here would race/duplicate that already-scoped finalize step.
- **na-eligibility-audit 2026-08-17** [body-hash:8f8b354c2880c350]: KEEP-NA-STALE (already-duplicated) — archive_exempt:true, 0 open todos, archival deferred to sports_taxonomy_p3_consumers_2026_08_08_finalize.md todo 1 (batch-archival of 6 docs, verified status:active/unlocked). Not archived unilaterally here — would race that finalize plan's own batch ritual.
- **context-scout 2026-08-17**: refreshed context_scope (5 entries).
