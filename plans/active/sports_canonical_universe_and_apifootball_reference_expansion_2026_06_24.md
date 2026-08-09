---
doc_type: plan
title: Sports canonical universe + API-Football reference expansion (curate, don't over-capture)
summary:
  Curate the sports canonical trading universe (94 leagues) and expand the API-Football reference universe to ~300
  leagues to eliminate out-of-universe over-capture in instruments-service.
status: active
nature: process
asset_group: [sports]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: [sports, canonical-universe, api-football, reference, over-capture, instruments, league-registry]
related: [/plans/active/sports_consolidated_closeout_2026_07_19.md]
created: 2026-06-24
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 7.2
last_updated: 2026-07-24
locked_by: live-defi-rollout
locked_since: 2026-06-24
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
drift_direction: correct-codex
context_scope:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/02-data/sports-data-source-coverage-matrix.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    instruments-service/instruments_service/engine/orchestrator/sports_reference_core.py,
    market-tick-data-service/market_tick_data_service/scripts/_migrate_drop_stale.py,
  ]
---

# Sports canonical universe + API-Football reference expansion

> **🟡 STATUS CHECK (2026-07-24, `/plan-reconcile` audit)**: This plan is `status: active` with real open work below —
> it is **NOT** archived or superseded. Track V of `/plans/active/sports_consolidated_closeout_2026_07_19.md` (the
> canonical, single actionable sports execution plan) previously carried a false "both archived/superseded into this
> closeout" claim about this doc — corrected 2026-07-24 (see
> `/plans/archive/issues/sports_plan_and_docs_reconcile_findings_2026_07_24.md`). This doc's own ~9-11 open `- [ ]`
> todos (UAC canonical registry build/refine, the curated ~300-league reference set + backfill
>
> - residual drop, bare/legacy dual-layout cleanup, retention-floor cleanup, the E8 legacy-delete stub, etc.) are NOT
>   duplicated inside the closeout — this remains a satellite plan the closeout references (see this doc in the
>   closeout's `related:` list + its Track V reconciliation todo) rather than folds in. Do not re-archive this doc
>   without first migrating/tracking this open work.

> Captures the operator architecture spec (2026-06-24) after the over-capture diagnosis. Refine the existing codex / UAC
> / code rather than reinvent — this is mostly cleanup + consolidation of forms we already have through migrations.

## The diagnosis (root cause of the "low coverage / numeric keys / failures")

The sports `_index` (4.6M rows) is NOT a numeric-vs-canonical schema split — it's **out-of-universe over-capture**: the
date-wide API-Football adapter calls return the provider's entire **~1,200–2,400-league** universe, but our canonical
trading universe is **94 leagues** (`get_expected_leagues_for_source("api_football")`) / 101 (`LEAGUE_REGISTRY`).
**1,676,612 rows (36%)** are out-of-universe leagues. The "numeric/blank league_id" rows are just the api-football-path
slice of this cross-provider over-capture; the resolvable in-universe numerics (215,881) all have a canonical twin (100%
dedup). Numeric rows are STILL being written (live writer pollution) until the write-gate ships + VMs relaunch.

## Operator decision (2026-06-24): HYBRID — curated reference expansion, then drop residual

- **94 stays the TRADING/downstream universe.** All non-API-Football sources + trading services stay bounded to 94 (or
  less, per each source's eligibility). NOT expanding what we predict/trade.
- **Expand the API-Football _reference_ universe** to a curated **~300 leagues** (budget-justified below) — the leagues
  - cups worth holding for reference/features/arb: the 94 + the division below each country + continental cups
    (Champions League, UEFA/UECL, Copa Libertadores/Sudamericana, AFC/CAF equivalents) + major internationals (World
    Cup, Euros, Copa America…). Reference-only; downstream derives nothing new from them unless explicitly promoted.
- **DROP the rows STILL outside the curated set after expansion** (not drop-vs-94) — the truly-junk leagues with no
  prediction/arb/reference value. Snapshot-first; `--drop-out-of-universe` retargeted to "outside curated".

## 6M-call budget (why ~300)

~6M API-Football calls available over the coming weeks (300k/day quota). Per-fixture enrichment dominates:
lineups+stats+events+player_stats ≈ 4 calls/fixture; top league-season ≈380 fixtures → ~1,900 calls/league-season;
2019→2025 ≈7 seasons → ~13k/league full history. 6M ÷ 13k ≈ **~450 leagues** for full enrichment — effectively more (we
already hold many fixtures; lower/cup leagues have few fixtures + often no enrichment → gated honest-empty, no call). So
~300 curated is comfortable + value-appropriate; ~2,400 would burn the budget on enrichment-less junk.

## Architecture (canonical-everything; mostly cleanup of existing forms in UAC)

1. **Canonical league + cup registry (UAC SSOT)** — every league/cup has: human-readable canonical name, API-Football
   id, other-source ids, **is-league-vs-cup**, **country**, **season start/end per year**, **transfer window**
   (transfermarkt consumes it; we need it for refresh timing + ML training windows). Annual league-id changes
   (footystats / SFI rotate ids per season) → per-season id mapping in UAC.
2. **Per-source league eligibility (UAC SSOT)** — each source's coverage, bounded by API-Football existence (can't get a
   source for a league API-Football doesn't have): understat ~6; footystats/T-stats ~50 (subscription cap); odds-API ~20
   (+ per-bookmaker-league restriction); SFI its subset; weather = fixture/venue-location-based (bounded by 94). Every
   source CHECKS canonical eligibility + converts canonical→its-query-id. Honest coverage MUST bake these caps in so we
   never mislabel `empty_confirmed` when a source legitimately doesn't cover a league.
3. **Canonical teams / players / fixtures** — API-Football id → human-readable canonical name + other-source mappings.
   Fixture = canonical fixture/event id (instrument-id-like) derived from teams; odds-API derives its pulls from it.
4. **Honest coverage** consumes (1)-(3): denominator = only-eligible (league × source × data_type) cells; everything
   else honest-absence/out-of-window. No mislabeled gaps.

## Execution sequence (phased; fastest-but-safe)

- [x] ✅ [INFRA] P0. Stop live sports deployments (not trading; over-capture pollution) — `mtds-live-sports-*`
      terminated 2026-06-24.
- [x] ✅ [CODE] P0. **Write-gate to known/eligible leagues** (no random grab) — SHIPPED `instruments-service@0345ffc`
      (`_is_in_canonical_write_universe` gates the per-league capture-write loops to the 94-league
      `get_expected_leagues_for_source("api_football")` set; numeric/out-of-universe leagues never written as
      captured) + the `canonicalize_sports_league_id_schema_2026_06_24.py` migration. Landed on LDR, Tier-C drain →
      staging (v2-gated). Gated to **94 first**; widen to the curated set in the P1 step below.
- [x] ✅ [INFRA] P0. **Tarball rebuild + relaunch + re-enable crons** — instruments-service tarball rebuilt at
      `a4b1bd032d9c` (write-gate `0345ffc` is ancestor); both crons resumed 2026-06-25: `uts-prod-sports-scheduler-cron`
      ENABLED (\*/5) + `uts-prod-sports-fixtures-noon-t1-schedule` ENABLED (noon daily).
- [x] ✅ [DATA] P0a. **`_index` canonicalize+dedup migration APPLIED 2026-06-24** —
      `canonicalize_sports_league_id_schema_2026_06_24.py --apply`: 518,799 in-universe numeric+suffixed → canonical,
      509,227 dedup-collapse, **in-universe numeric residual → 0**; 4,599,952 → 4,090,725 rows; out-of-universe numeric
      (604,139) KEPT (hybrid — drop after curated expansion). Snapshot
      `_index/snapshots/pre_league_id_canonicalize_20260624T092926Z.parquet`. Consolidator
      `uts-prod-manifest-consolidator-instruments-sports-cron` PAUSED to prevent a re-merge race (see Temporary states).
      Re-measure: FIXTURES 93.9%→**100%**, golden-window in-window-gap 10,988→10,765, overall **65.2%** captured.
- [x] ✅ [DATA] P0b-seed. **Seed-canonicalized + consolidator resumed 2026-06-24** — the lone per-VM shard
      `_index/per_vm/_legacy_seed.parquet` (4.5M rows, 1.05M numeric) was overwritten with the clean canonical
      consolidated (lossless: consolidated ⊇ seed content) → seed now 4,090,725 rows, in-universe numeric=0 (snapshot
      `_index/snapshots/pre_seed_canonicalize_*_legacy_seed.parquet`).
      `uts-prod-manifest-consolidator-instruments-sports-cron` RESUMED — no re-pollution (canon + seed both canonical
      now).

### Per-league hive-partition architecture (VERIFIED 2026-06-24 — corrects an earlier wrong "league is just a column" claim)

The modern sports layout **IS per-league hive-partitioned with the CANONICAL league as the partition key** — UAC
`gcs_paths.py` SSOT: `sports_reference/by_date/day={D}/entity={F}/league={canonical}/{F}.parquet`
(`SportsLayout.PER_DAY_PER_LEAGUE`, the default for most entities). Three layouts: `PER_DAY_PER_LEAGUE` (most),
`PER_DAY_PER_SEASON` (bulk, e.g. player_values — intra-file `canonical_league` filter), `PER_DAY_BARE` (single-file/day
entities like XG/WEATHER, OR pre-per-league legacy). **This is exactly the design the operator described** and it
satisfies every requirement:

- **Query / train / predict per-league** → the `league=<canonical>` partition is a pushdown predicate (read one league's
  dir).
- **Add a new league over time** → a brand-new `league={canonical}/` dir; never appends-into / wipes / skips an existing
  league's parquet; its own manifest cell.
- **Parallel-VM safety** → league-A-VM writes `league=EPL/`, league-B-VM writes `league=LA_LIGA/` — DIFFERENT files, no
  same-parquet collision (the per-league split is precisely what removes the operator's parallel-write hazard). Shard
  atom = `(entity, league, day)`.
- **Skip-existing pre-flight** → `sports_reference_fixtures.py:390` reads the existing per-`(entity, league, day)`
  parquet, builds the set of already-captured `af_fixture_id`s, and skips them (per-league + per-fixture-within).
- **Coverage on a league basis** → data-status drill-down hierarchy is `data_type → league_id → date`
  (`/codex/02-data/data-status-drilldown-hierarchy.md:23`); the `_index` carries `league_id` per row → per-league % is
  real.
- **Write path** → orchestrator writes `partition={"entity":…, "league": _canonical_league_id(…)}` (verified
  `sports_reference_core.py`). VERIFIED in GCS: 2018→69, 2020→107, 2023→115, 2025→80 **canonical** `league=` dirs; **0
  in-universe numeric** across all years (only 2 out-of-universe `14231`/`315` in 2025).
- [x] ✅ [DATA] P0b-paths. **No in-universe path-move needed — VERIFIED already canonical** (0 in-universe numeric
      `league=` dirs across 2018-2025; the partition key is already `league=EPL` etc.). The earlier "no league
      partition" reasoning was WRONG (sampled a 2015 bare path); the conclusion holds because in-universe data is
      already canonical.
- [x] ✅ [DATA] P0. **Eliminate the bare/legacy dual-layout (operator: "legacy needs canonicalising or deleting — that's
      the whole point")** — per-league entities that have BOTH a per-league split AND bare files for older days
      (`gcs_paths.py:96`) carry a stale parallel layout. For each: canonicalise the bare→per-league (in-retention) OR
      DELETE (pre-retention). Distinguish from the _by-design_ bare entities (XG/WEATHER/player_values-bulk) which stay
      bare. **DONE (na-eligibility-audit 2026-08-03)** — `sports_satellite_ao_dispatch_batch2_2026_07_24.md:118`:
      VERIFIED CLEAN 2026-07-25 (slot 2) — the dual-layout condition does not currently exist for any of the 15
      `PER_DAY_PER_LEAGUE` entities; zero canonicalize/delete action needed. Full census in that plan's Progress Log.
- [x] ✅ [DATA] P0. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — this bullet's own nested
      2026-07-25 banner already says the premise is superseded by the 2026-07-21 2020-06-06 data-floor ruling; the
      checkbox here just never got updated to match. The real remaining blocker is a genuine human-only hard-stop for an
      irreversible prod GCS delete (the `day=all` fold), tracked in
      `sports_day_all_teams_venues_fold_key_scheme_mismatch_2026_07_25.md` / the AO-dispatched copy in
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md` — confirmed still the correct `[OPERATOR]` hard-stop in
      `sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md` item (8), not IAM/credential. Remaining work lives in
      those docs, not here.** **Retention floor = the EXISTING per-source genesis registry — NOT a blanket 2015 delete
      (corrected 2026-06-24).** The genesis SSOT already exists + is populated: UAC
      `canonical/domain/sports/league_data.py` `SOURCE_COVERAGE_START` = understat **2014-01-01**, api_football
      **2015-01-01**, footystats/transfermarkt/SFI **2019-01-01**, open_meteo 2019-03-02, odds_api/mdps_odds
      **2020-06-06**; + per-`(source,data_type)` overrides (SFI_PROGRESSIVE_STATS 2020-01-01) + per-`(source,league)`
      (UNDERSTAT_COVERED_LEAGUES, bookmaker-league). Consumed by honest coverage via `clip_dates_to_source_coverage()` /
      `is_before_source_ln`. **Implication: 2015-2017 is VALID understat(2014)/api_football(2015) history — KEEP it**
      (the operator's "don't need 2015" is overridden by the SSOT, which deliberately retains it for ML training).
      Earliest real day = 2015-01-01, **0 pre-2014 partitions**. So retention cleanup is SMALL, not a blanket delete:
  - **`day=all`** is NOT a stray to delete — it holds `entity=teams` + `entity=venues` (~974KiB), date-invariant
    REFERENCE data. But `teams` also appears per-day-per-league → possible dual storage. RECONCILE: canonical home for
    date-invariant reference is `SportsLayout.FLAT` (`sports_reference/{F}/{F}.parquet`); fold `day=all` into FLAT (or
    confirm which the readers use) + dedup — do NOT blind-delete (would break team/venue resolution).
  - Per-source pre-genesis ANOMALIES only (e.g. any footystats parquet before 2019, odds before 2020-06) — targeted
    check + delete/relabel; honest-absence clip already hides them from the denominator.
  - > **🟡 2026-07-25 status**: this bullet's premise is stale — see
    > `/plans/archive/2026_08/sports_day_all_teams_venues_fold_key_scheme_mismatch_2026_07_25.md`. The `day=all` fold is
    > not mechanically executable as described (TEAMS has no FLAT layout; the legacy vs. live venue key spaces have zero
    > overlap) and is now `BLOCKED-OPERATOR-DECISION` in the AO-dispatched copy of this todo
    > (`sports_satellite_ao_dispatch_batch2_2026_07_24.md`). The per-source genesis dates quoted above are also
    > superseded by the 2026-07-21 uniform 2020-06-06 floor ruling (`/codex/02-data/sports-2020-06-data-floor.md`), and
    > the pre-genesis anomaly check is already covered by that doc's tracked phantom-row-prune item — no separate action
    > needed for part (b).
- [x] ✅ [DATA] P0. **NICE-TO-HAVE / watch-item: odds-granularity** — unified-api-contracts@a32ceb87. Checked; not
      confirmed, documented as checked-no-issue (no dated capability entry needed — no code path anywhere computes an
      expected-snapshot-count from a cadence constant, so the mislabeling this watches for cannot occur today). Full
      resolution in `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s matching todo.
- [x] ✅ [DOCS] P0b-codex. **Fixed `per-asset-group-bucket-layouts.md` 2026-06-24** (PM@6fc561a45) — SPORTS row now
      documents the per-league canonical hive partition + all 4 `SportsLayout` variants + `candidate_parquet_paths`.
      (`sports-adapter-dependency-order.md` still shows `entity=fixtures` shorthand without `league=` — minor, fold into
      the next sports-codex touch.)
- [x] ✅ [DATA] P0. **2 out-of-universe numeric `league=` dirs** (`14231`/`315`) — dropped now, snapshot-first. Full
      resolution in `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s matching todo — instruments-service@2c4fa059.
- [x] ✅ [DATA] P0. **94-league enrichment backfill** — re-measured + closed. Full resolution + evidence in
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s matching todo — unified-trading-pm@(this commit).
- [x] ✅ [CODE] P1. **UAC canonical registry build/refine** — league/cup canonical + ids + is-cup + country + season
      start/end + transfer window; per-source eligibility maps + annual-id-change handling; team/player/fixture
      canonical + mappings. Wire honest-coverage to consume them. **DONE (na-eligibility-audit 2026-08-03)** —
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md:165`: `unified-api-contracts@ce18ff15` audited every clause
      against current code (most already canonical: name/ids/country/season dates, transfer windows, team cross-source
      mapping, fixture/player canonical ids, annual footystats-id rotation via `check_footystats_season_drift.py`); 2
      genuine gaps closed (`LeagueDefinition.is_cup` added; `is_sports_structural_gap()` wired into
      `get_expected_leagues_for_source()`). 4 new regression tests, `quality-gates.sh` green.
- [x] ✅ [DATA] P1. **Define the curated ~300-league reference set** (94 + below-division + continental cups + majors) +
      widen the write-gate to it. — CLOSED via `sports_satellite_ao_dispatch_batch2_2026_07_24.md` (batch-2 combined
      todo): continental-majors slice shipped (`unified-api-contracts@7b13196e`); domestic-selection slice decomposed
      into 11 confederation-batch todos, all landed; final residual drop `instruments-service@0877f849` (2026-08-04,
      slot 16).
- [x] ✅ [DATA] P2. **Curated-universe backfill** (API-Football fixtures + enrichment, 2019→, burn ~6M over weeks;
      gated + honest-empty for no-enrichment leagues). — CLOSED via `sports_satellite_ao_dispatch_batch2_2026_07_24.md`
      (batch-2 combined todo): fixtures backfill verified complete 2026-07-28 (`af-backfill-20260728-091755`, all 25/25
      chunks clean, exit_code=0); enrichment gated on the curated-universe expansion (above).
- [x] ✅ [DATA] P2. **DROP residual out-of-curated rows** (snapshot-first) once the curated set is backfilled. — CLOSED
      via `sports_satellite_ao_dispatch_batch2_2026_07_24.md` (batch-2 combined todo): `instruments-service@0877f849`
      (2026-08-04, slot 16), snapshot-first drop of 8,937 rows; full evidence in
      `issues/sports_curated_universe_domestic_selection_remaining_2026_07_25.md`.
- [x] ✅ [SCRIPT] P3. Delete superseded-buggy `instruments-service/scripts/backfill_fixture_lineups_blank_reason.py`
      (env-less bucket + direct google.cloud SDK) — instruments-service@a4b1bd0

## Audit findings + verified enforcement (2026-06-24) — answers "how can we still have two SoT"

### Two-SoT root cause (why dual layout persists despite the migration plans)

`sports_manifest_canonicalisation_2026_06_01.md` is **code-complete + dry-run-green but its IRREVERSIBLE GCS object
`--apply` (E3→E8: fleet-drain → object-rewrite → legacy-delete) was gated on operator sign-off + fleet drain +
foundation gates and NEVER FIRED.** So the migration sits in a _pre-apply_ state — the plans don't lie (they correctly
mark `--apply` PENDING), but the un-fired gated step is exactly why dual layout persists. Live `_index` audit (4,047,452
rows, 2026-06-24):

- ✅ **schema_version: 100% v9** (the consolidator rebuild v9'd it; the plan's "100% v8" was its stale 2026-06-01
  pre-snapshot — so the V9 manifest migration effectively COMPLETED since).
- ✅ pipeline_mode: populated (batch_api_football 2.2M, batch_footystats 907k…).
- ❌ **source column: 1,465,986 BLANK (36%)** — the CF-4 source-stamp is INCOMPLETE.
- ❌ **asset_group: ~1.31M blank/empty (32%)** — the CF-2 stamp is INCOMPLETE.
- ⚠️ league_id: in-universe canonical; 604,139 out-of-universe numeric (hybrid); **55,884 blank**.
- ❌ **GCS object layout: dual on disk** (E-steps unfired) + a `date="all"` reference-row class bleeding into `_index`.
- ⏳ **Still un-audited**: `market-data-tick-sports` (MDPS odds) + `features-sports` bucket object layouts.

### VERIFIED enforced — enrichment-not-available ≠ attempted_failed (operator's "I hope it's enforced")

`is_league_entity_covered(league, entity)` (UAC `registry/sports_league_entity_coverage`, an OBSERVED-from-captured map)
gates the capture write (`sports_reference_core.py:115`): a league lacking an enrichment entity records
`EXPECTED_NO_PROVIDER_COVERAGE` (out_of_window, NON-counting, **NOT retried**) — DISTINCT from `attempted_failed` (a
fetch was attempted + errored → retried). This closed a ~72% `attempted_failed` over-count. **Hardening remaining**: the
map is built by the one-off `refresh_sports_league_entity_coverage_2026_06_21.py` → (a) refresh it AFTER the enrichment
backfill (records newly-observed enrichment), (b) promote it to a recurring CLI subcommand.

## Remaining program (operator 2026-06-24) — sequenced by unblock-value; action ASAP, parallel where independent

**[A] CODE HARDENING — no API quota; unblocks B/C/D correctness+efficiency (run in PARALLEL with B):**

- [x] ✅ [CODE] P0. **FIXTURES: switch per-(league,day) → per-(league,season) BULK fetch** —
      instruments-service@a241b84. Added `_season_fixture_cache` class-level dict keyed `(league_id, season_year)` and
      `_fetch_season_fixtures_with_raw` method (GET `/fixtures?league&season`, no `date=`, cached). `get_fixtures` and
      `get_fixtures_with_raw` use season cache when `league_ids` supplied, filter in-memory by date; no-league-ids path
      unchanged. Non-match days return `[]` with zero API calls. Cuts call count 5-10× for multi-date backfills and the
      9-day repoll window. Tests: `TestApiFootballFetchSeasonFixturesWithRaw` (cache-miss, cache-hit, exception) +
      updated `TestApiFootballGetFixturesWithRaw` (cache isolation, date filter, fallback path).
- [x] ✅ [CODE] P0. **Season-window clip for downstream per-day sources** (weather, footystats, understat,
      soccer_football_info) — instruments-service@d651557. Wired `get_source_coverage_start` / `is_in_known_gap` guards
      into 5 insertion points: weather.py (open_meteo/WEATHER), understat.py ×2 (XG + XG_SHOTS), footystats.py ×2
      (PREDICTIONS + MATCHES). Off-season cells emit `record_expected_empty("EXPECTED_PRE_SOURCE_COVERAGE_START")`
      without any API call. 5 new pre-cutoff tests + 2 footystats skip-path tests restore coverage above 88% floor; 3757
      tests pass. **COMPLETED 2026-06-24 — true off-season clip added — instruments-service@1bb2324**: d651557 only did
      the genesis-floor (`EXPECTED_PRE_SOURCE_COVERAGE_START`); 1bb2324 adds the actual off-season season-window clip
      via UAC `footystats_season_status_for_day` — when EVERY expected league is in its off-season gap on a date, the
      source skips the API call and records per-league
      `record_expected_empty(EXPECTED_PRE_SEASON|EXPECTED_POST_SEASON)`. Wired into weather.py, understat.py ×2 (XG +
      XG_SHOTS), sfi.py (NEWLY added — d651557 had skipped sfi), footystats.py ×2 (predictions + matches). 6 new
      `TestOffSeasonSeasonWindowGuard` tests; QG green.
- [x] ✅ [CODE] P0. **Transfermarkt = TRANSFER-WINDOW-aware** (NOT pure off-season — windows open mid-season + at
      start/end of season) — instruments-service@1bb2324. `_fetch_transfermarkt_data` now skips PLAYER_VALUES fetches on
      dates outside ALL expected leagues' transfer windows AND with no refresh-trigger for any league (conservative —
      never over-clips season-start/promotion refreshes; respects `force`), recording per-league
      `record_empty(EmptyConfirmedReason.EXPECTED_OUTSIDE_TRANSFER_WINDOW)` via UAC `is_transfer_window_open` +
      `get_leagues_needing_refresh`. 3 new `TestTransfermarktTransferWindowGuard` tests (outside-window skip /
      within-window fetch / force bypass); QG green.
- [x] ✅ [CODE] P1. **Refresh `is_league_entity_covered` map post-enrichment + promote to a recurring CLI** (retire the
      one-off refresh script) — instruments-service@f3a5447 (+@ab4210a) + UAC@308037cd, run 2026-06-24. Promoted the
      one-off `refresh_sports_league_entity_coverage_2026_06_21.py` to a recurring CLI verb
      `instruments-service --operation refresh-league-entity-coverage` (early-branch in `cli/main.py`, mirrors
      `--operation=status`); one-off **deleted**. Made it **additive-UNION by default** (+`--prune` for post-backfill)
      so it is safe mid-backfill — a not-yet-captured league stays covered instead of being falsely flipped to
      out-of-coverage. **Ran `--write`**: regenerated the UAC observed-coverage map **615→728 (entity,league) pairs,
      +113 newly-observed** (PLAYER_VALUES/WEATHER/INJURIES from the running 2014-2026 backfill), **0 dropped
      (superset-verified)**. Newly-observed enrichment is now annotated → `is_league_entity_covered` treats it as honest
      coverage (`EXPECTED_NO_PROVIDER_COVERAGE`), never retried. Re-run anytime as the backfill captures more.
- [x] ✅ [CODE] P0. **Golden-window denominator fix → VMs see FIXTURES 100%** for 2025-09..11 —
      instruments-service@f3a5447 + applied 2026-06-24. New
      `scripts/reclassify_golden_window_fixtures_no_match_2026_06_24.py` (in-place, snapshot-first, truth-set-gated)
      reclassified **223** golden-window FIXTURES no-match-day cells (blank/`SOURCE_RETURNED_ZERO`, NOT in the FIXTURES
      truth-set) → `empty_confirmed`/`EXPECTED_NO_FIXTURE`; **0 attempted_failed + 0 in-truth real failures touched**.
      Consolidator paused→apply→resumed; verified the reclassify **stuck across 2 merge cycles** (no re-pollution —
      incremental merge reads canonical + changed shards, not the settled seed). **Re-measured 2025-09-01..11-30:
      FIXTURES = 3444 captured + 7770 EXPECTED_NO_FIXTURE, 0 failed, 0 expected_unattempted → data-type-aware coverage =
      100.00% (11214/11214).** Pre-flight no longer retries (a241b84 season-cache already makes no-match days zero-call;
      now also denominator-correct). Snapshot: `_index/snapshots/pre_golden_fixture_reclass_20260624T194010Z.parquet`.

**[B] GCS MIGRATION `--apply` — operator-APPROVED 2026-06-24 ("time to run that"); ORPHAN-CHECK FIRST
(pure-canonical):**

- [x] ✅ [DATA] P0. **GCS object migration `--apply` DONE + verified 2026-06-24** —
      `migrate_sports_canonical_v9.py --apply` both surfaces, 2015-2026, 0 orphans corpus-wide (dry-run gate). Transform
      = INSERT `pipeline_mode=` after `day=` (the `league=<canonical>` partition was already canonical). Result:
      instruments **652,062 copied** (+112k idempotent-skip = all 764,137 accounted), MDPS **8** (617k already
      canonical), **0 errors**. Verified: 1:1 legacy↔canonical parity (2025-10-15: 82↔82), canonical readable
      (`pipeline_mode=batch_api_football/entity=…/league=BRASILEIRAO/`). Readers prefer canonical → **dual-SoT
      functionally resolved for reads.** Additive (legacy coexists, not deleted).
- [ ] [DATA] P1. **Legacy-delete (E8) — `--drop-stale` is an UNIMPLEMENTED stub** (line 886-891 raises). The legacy
      (no-`pipeline_mode`) objects remain as dead weight (not harmful; readers use canonical). Implement the per-surface
      delete (twin-verified: only delete a legacy object whose canonical `pipeline_mode=` twin exists + is readable) +
      operator gate (IRREVERSIBLE) — OR a separate `gcs_delete_object` sweep with the same twin-verification. NOT
      urgent. **`sports_reference_v1_archive/` VERIFIED SAFE-TO-DELETE 2026-06-24** (no migration needed): it's the v1
      wide-denormalized fixtures (398 days 2018-2026, bare layout, human-readable strings + `data_available_at`,
      xg/stats cols all NULL). Coverage check across 5 days 2018→2026: archive `af_fixture_id` ⊆ canonical
      `af_fixture_id` (**canon-only=0**; canonical equal-or-superset). The v2 canonical stores `af_*` ids + canonical
      `league=` path + derives human-readable via UAC registries (the by-design store-id/derive-name pattern), so the
      archive's data is fully represented. Delete it with the legacy sweep (snapshot-first). **DONE-FOR-CODE
      2026-06-26** (via `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s AO-dispatched copy of this todo, full
      evidence in `plans/archive/2026_07/sports_satellite_ao_dispatch_batch5_completed_todos_2026_07_26.md`):
      `--drop-stale` implemented+unit-tested+dry-run-verified twin-safe on both surfaces
      (`market-tick-data-service@08439787` + `@236d945e`, verified real commits). Checkbox stays unchecked — the actual
      irreversible `--apply`/`--drop-stale` firing remains **BLOCKED-OPERATOR** pending explicit sign-off (a 2026-07-27
      re-check flagged it's likely just a finding-T/U soft-delete-retention re-tag away from qualifying, not yet
      re-tagged). Re-run once the operator authorizes the delete. **Partial progress 2026-07-29 (credential/self-service
      re-triage pass)**: ran the fresh same-run `gcs_bucket_soft_delete_retention_seconds()`-equivalent check
      (`gcloud storage buckets describe ...     softDeletePolicy.retentionDurationSeconds`) on both target buckets —
      `instruments-store-sports-prd-central-element-323112` = 604800s,
      `market-data-tick-sports-prd-central-element-323112` = 604800s — **both meet the ≥604800s finding-T/§3a
      threshold**. This clears ONE of the two conditions the 2026-07-27 re-check named. **NOT clearing the operator gate
      myself**: this is delete-safety hard-stop #2 (legacy-delete-after-copy), and per the still-open contradiction
      filed in `plans/active/issues/cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md` (codex says
      hard-stop #2 is §3a-qualifiable once Part 5's 100%-twin-coverage proof clears; a sibling CeFi plan explicitly
      reaffirmed "no carve-out... regardless of pre-checks" for the same hard-stop class), the reversibility-qualified
      path is not being treated as settled workspace-wide yet. Also unverified here: whether Part 5's PROOF (100%
      canonical-twin coverage, content-verified corpus-wide, not the tool's dry-run-correctness) has actually been
      measured for this full corpus, vs. just the delete mechanism being unit/dry-run tested. Recommend: operator
      resolves the hard-stop #2 contradiction once (it blocks this AND the CeFi sweep identically), then this specific
      delete needs its own Part-5 100%-coverage measurement before either a human or an agent fires `--apply`.

      **RE-CHECKED 2026-08-07 (operator: "does need sign off if its been checked as safe which you can do now")**: the
                  hard-stop #2 contradiction cited above IS now resolved —
                  `cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md` (archived, `status: resolved`) ruled
                  2026-08-03 that codex's reading is correct: §3a DOES extend to hard-stop #2 once Part 5's proof is measured for
                  real (not just dry-run-tested), confirmed by actually running the CeFi equivalent (`cefi-drop-stale`,
                  `cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` Phase B — 287,074/287,074 deleted, 0 errors,
                  twin-verified per-object). **BUT this specific delete cannot re-use that precedent directly**:
                  `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` has NO `sports-drop-stale` category registered
                  (only `cefi-drop-stale` exists in the launcher's category list) — there is nothing to dry-run against yet. Per
                  CLAUDE.md's VM-launcher rule ("grep the registry FIRST, never hand-roll a name — unregistered silently vanishes
                  from deployment-ui/cockpit/Slack"), this needs a real code change (add a `sports-drop-stale` category mirroring
                  `cefi-drop-stale`'s exact pattern, line ~1229) before any dry-run census can even run — genuinely more than "a
                  check," this is its own scoped piece of engineering, not done this pass. Bucket-retention condition (a) is
                  still confirmed met (604800s both buckets, 2026-07-29); condition (b) (Part 5 100% twin-coverage) remains
                  unmeasured for the real sports target population pending that launcher work.

- [x] ✅ [DATA] P0. **`_index` CF-2/3/4 stamp DONE — BOTH sports surfaces now CF-GREEN 2026-06-24** via the new
      `instruments-service/scripts/canonicalize_sports_index_cf234_2026_06_24.py` (in-place, preserves everything;
      source = `pipeline_mode` minus its `{mode}_` prefix, `expected_unattempted` source-exempt; asset_group=sports;
      pipeline_mode derived from source/data_type). **NOT the E5/E6 rebuild** — that REGRESSES source (drops it on empty
      re-emits, verified CF-4 1.4M→2.49M; the reason-relabel it does is already covered, CF-5 was green). Results, both
      consolidator-paused + snapshot-first + shard-reseeded + resumed:
  - instruments-store-sports (4,047,892 rows): asset_group 1.31M→0, pipeline_mode 88k→0, source 1.47M→0 (non-exempt) →
    **CF VERDICT GREEN**.
  - market-data-tick-sports / MDPS (1,760,262 rows): source 1.19M→0 → **CF VERDICT GREEN**.
  - **Manifest V9 is now ENTIRELY canonical (CF-1…CF-12) across both sports surfaces** — the gate for deleting all
    legacy data is met for the manifest. (Script needs shipping via quickmerge once the foreign-dirty IS tree clears.)

**[C] API-FOOTBALL FIXTURES backfill SINCE 2015 (94 leagues)** — needs [A] season-window for efficiency; ~35-50k
incremental calls no-force for 2019+, scaling modestly for 2015-2018. Unblocks [D]. (api_football genesis = 2015.)

- [x] ✅ [DATA] P0. Fixtures backfill 2015→present, 94 leagues, no-force, season-window-gated. (was: unchecked)
      **[2026-07-12 — finding 257, §A2 B-queue ruling]** COMPLETED elsewhere — this exact scope was picked up + shipped
      in `sports_p2_history_apifootball_2015_to_present_2026_06_27.md` Todo 4 (its own References section frames itself
      as "94 only here", disclaiming just the ~300-league expansion part of this doc): FIXTURES backfilled + verified
      2018→present, gate PASSED with audit evidence (instruments-service@97ccf8d:
      `run_fixture_completeness_audit_2026_06_25.py` → 0 pending-fetch, 0 blank-reason, depth 100.10%). 2015-2017 is now
      a confirmed subscription floor (`SOURCE_COVERAGE_START["api_football"] = date(2018,1,1)`, UAC-shipped, was
      `date(2015,1,1)`), typed `EXPECTED_PRE_SOURCE_COVERAGE_START` — honest absence, not a gap. Do NOT re-dispatch this
      todo (scarce 6M API-Football call budget).

**[D] ENRICHMENT backfill SINCE 2015** — needs [C] (fixtures first) + uses results to refresh [A]'s availability map.
The big quota sink (~4 calls/fixture: lineups/stats/events/players) + downstream (weather/footystats/understat/SFI per
eligibility + season/transfer windows).

- [x] ✅ [DATA] P1. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — the note below cites
      `sports_p2_history_apifootball_2015_to_present_2026_06_27.md` Todo 9 as "correctly unflipped/BLOCKED-OPERATOR-
      DECISION", but that archived plan's Todo 9 was actually flipped GREEN on 2026-07-14 (see its line 87 banner "Todo
      9 GW gate GREEN, checkbox flipped" and its line 199 `[x]` checkbox) — 2 weeks before this note was written.
      Separately, the pre-2020-06-06 portion of "2015→present" is moot per the 2026-07-21 data-floor ruling, and the
      post-floor portion is tracked elsewhere (5/6 sources VERIFIED DONE per
      `sports_closeout_track_s2_foldin_2026_07_25.md`, odds_api gap tracked in
      `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`).** Enrichment backfill 2015→present for the 94 leagues,
      then annotate per-(league,entity) availability. **[2026-07-12 note — finding 257, §A2 B-queue ruling]** A nominal
      counterpart of this item is checked `[x]` in `sports_p2_history_apifootball_2015_to_present_2026_06_27.md` (Todo
      5, "Backfill enrichment + core 2020-06→present"), but that checkbox represents LAUNCH not gate-passed — its own
      defined gate was still FAILING as of that plan's most recent Progress Log entry (2026-07-06 session 19: Total EU
      415,064, "Gate: FAILS"). The real enrichment-completion tracker there is its Todo 9 (BLOCKED-OPERATOR-DECISION,
      correctly unflipped). Do not treat either as evidence this [D] item is done; check `sports_p2_history...` Todo 9
      status before dispatching.

**SEQUENCING:** [A]+[B] now in parallel (code vs data-layer, independent) → [C] once [A] season-window lands → [D] after
[C]. Biggest single unblock = [B] (resolves dual-SoT + stamps) and [A] (correct+cheap backfills) — both start now.

## FINDING 2026-06-24: v2 canonical fixtures lack a STORED human-readable canonical fixture-id (operator-surfaced)

The v2 canonical `entity=fixtures` stores **`af_fixture_id` (numeric, the only fixture id)** +
`af_home_name`/`af_away_name` (AF-RAW names, not canonical-registry team names) + numeric
`af_home_id`/`af_away_id`/`af_league_id` + canonical `league=` in the PATH + date/scores/status. There is **NO stored
composed human-readable canonical fixture-id** (the v1 archive HAD `fixture_id = LEAGUE:HOME_v_AWAY:DATE`); the `_index`
`fixture_id` column is blank/unused. The human-readable id is DERIVABLE (path league + home/away + date) but not
materialized.

- Per the operator's design the human-readable canonical fixture-id is "almost an instrument/event/fixture ID" + the
  **cross-source join key** (fixtures ↔ odds ↔ footystats). Storing only `af_fixture_id` means cross-source joins bridge
  on the numeric AF id or re-derive the string each time; stored team names are AF-raw, not canonical.
- NOT a blocker for the archive delete (the id is derivable from what canonical stores). But a focused NEW
  canonicalization if we want it stored:
- [x] ✅ [CODE] P1. **RESOLVED — derive-at-read accepted (operator 2026-06-24).** The v2 fixtures keep `af_fixture_id`
      (numeric) as the stored key; the human-readable canonical fixture-id is **derived at read** via the global helper
      `unified_api_contracts.sports.build_fixture_id(league_id, home_team_id, away_team_id, date_str)` →
      `"EPL:ARSENAL_v_CHELSEA:2026-01-15"` (any service imports it). Cross-source joins build the SAME id from each
      source's league+teams+date (as `add_canonical_fixture_ids.py` already does for understat/footystats; same for
      odds-api). No stored column needed. Revisit only if cross-source joins prove fragile at scale.

## Codex SSOT updates

- `/codex/02-data/sports-data-source-coverage-matrix.md` — the curated universe + per-source eligibility + caps.
- `/codex/02-data/availability-manifest-and-data-status.md` — honest-coverage eligibility rules (per-source league
  caps).
- New: `/codex/02-data/sports-canonical-league-cup-registry.md` — the canonical id/name/season/transfer-window SSOT.

## Operator verbatim directives (2026-06-24) — preserved in full (do NOT lose nuance to summary)

### Directive A — API-Football reference universe + canonical-everything + per-source eligibility

> essentially api football should have as many leagues including continental cups and world cup etc as it can that exist
> for football end of the day thats what exists - with canonical form for league and cup names. it should know whats a
> league and whats a cup i assume that's already there somewhere in leagues mappings/registry in UAC. Even though
> downstream we're not going to use a lot of them, it just allows us to add without always having to keep re-querying
> the API football. We have, like, twenty-something days' worth of 300k calls, so that's like 6 million calls to the API
> football. If you can work out roughly how many leagues and enrichment data we can realistically get from the API
> football with 6 million calls (since, whatever it is, 2019 is it?), then that will give us a good idea of how many
> leagues to include. Include the enrichment stats in that analysis so that we don't overcook it. Obviously, we already
> do have a bunch of fixtures in the API football, so it wouldn't be a full re-backfill. My guess is we can get to at
> least 90 something or 100, maybe even 200.
>
> as much league id mapping that can be done from this canonical to all the other data sources should happen in uac -
> where for some providers league ids change annually we should account for that. i think it was footystats or sfi that
> did that. that way we know all the other data sources can just check canonical league eligibility and convert to the
> query they need to get all the leagues for their data source that are eligible for them. The league to data source
> mapping eligibility, again, should be in UAC.
>
> For Understat, it's simple. We take all the leagues of Understat. We just know that all the leagues of Understat are
> way less than the leagues in API Football, so we're taking fewer leagues. I think it's six that are available. That's
> it. UAC guardrails that. For T-Stats [footystats], we have a hardcoded list of, I think, fifty leagues that we're able
> to use on our subscription because it caps out at fifty... it's around 50, and that's just the max we can do... the
> coverage needs to account for that. For weather, that's more on a fixture basis than league basis, so you can hold off
> on that for a sec. For soccer football info, I think there's a league availability... it should be cut down, and we
> can't be getting something from API Football [we don't have] — can't be trying to get soccer football info for a
> league that doesn't exist in API Football. Same with the odds API, which I think covers twenty leagues also for
> football... that's again just a hard rule.
>
> Everything else with respect to fixtures, teams, players, etc., follows the same concept — it filters from the top and
> it's based on what's actually available. There is this concept of prediction leagues, [and] features leagues. Given
> that we need ultimately odds for a prediction, we pretty much narrow down our prediction leagues to the ones that the
> odds API has data for. The concept of features leagues was just to understand the context around a particular league,
> so cups that might have been played around that league... what teams were relegated/promoted, history in other
> leagues. We try to get the leagues above and beyond... a wider universe of leagues around just the ones we have: world
> cups, euros, champions league, uefa, and the equivalents all over the world, as well as the league above and below the
> leagues we care about. Usually not much above (we take the top league + below for each country), but the one below
> that the odds API has data for is supposed to be included so we have a few extra leagues. That's how we get to an API
> Football baseline. There is a reason to have even more API Football — for arbitrage and things live, where we might
> not have the odds API data but try to pull live odds. Not a primary concern; we can always add leagues.
>
> leagues need info like which country they are in and the season start and end date each year and the transfer window —
> this should be canonical as transfermarket uses it to understand when transfer season is. We need it to understand
> when we need to refresh certain information about those leagues over their seasons. We'll need it to understand
> training windows for our machine learning.
>
> then we need to know which teams are in a league - again, there's canonical and there's matching/conversion. API
> Football gives us canonical in API Football ID, but we have converted that into human-readable canonical team names.
> For all the other data sources, team info we derive from the canonical. We have the mappings.
>
> then for fixtures - API Football gives basic fixture info (kickoff, who's playing, home, away). Since we have the
> teams, we derive the human-readable canonical fixture ID format (almost an instrument/event/fixture ID — canonical),
> and from there the Odds API works out which odds it can pull for those fixtures for the leagues it concerns. The Odds
> API has an extra restriction — certain bookmakers don't cover certain leagues, so there's a bookmaker-league
> restriction. All supposed to be baked into honest coverage so we don't keep assuming we don't have data when we do.

### Directive B — curate (not 2.4k), hybrid drop, drop live, cleanup posture

> i think where i'm at is that 1.2-2.4k leagues is way too much, but since we have 6m api football calls i wanna use
> them so figure out what interesting leagues for prediction and arb we can get for reach this cap over the coming
> weeks. The nice thing is, in the meantime, it doesn't change the fact that 96 [94] remains the universe that other
> data sources care about, or the rest of our services. I'm not suggesting we increase the scope of what we are
> predicting now. I'm suggesting we just, for reference, have a wider universe. As long as our honest coverage,
> denominators, numerators, manifest are set up properly, it doesn't matter — they're just going to expect to be
> deriving from those leagues and the fixtures that come from them. We will need leagues and fixtures... it's not just
> fixtures; basically all the API football enrichment stats around those leagues need to be covered — that's the basic
> starting point, reference information. When it comes to footy stats, soccer football info, understat, weather (mostly
> location-based once we know the home team), that's bounded by the 94 universe. API football would just be more
> exhaustive, burning the 6m credits for its coverage, so they only expect what they expect given all the rules above.
> You don't need to reinvent the wheel. We got a lot of documentation around this already, but you might need to refine
> it in the docs and in the code — codex, PM plans, the code itself, UAC. Let's finally get to the point where we don't
> need to do this as much. I don't know if it costs less API credits to get API football just for 94 leagues fixtures
> rather than more fixtures. If so, then just start with the 94. You've been doing 2.5k+, hence burning a lot of API
> calls. Get the golden window down. If the golden window is not already done, then get API football going for the rest
> for those 94 leagues. Fixtures should be fairly quick, then get the enrichment stats going for the 94 leagues, fix any
> broken... Be thorough. See if [it's] your call/query star and get order mappings in shape so that when things are
> working off those 94 leagues and their own rules (which make it less than 94, like odds API is much less), we're not
> badly labelling it empty confirmed. We are checking that we have good name mappings: leagues, fixtures, players, teams
> — everything should have canonical forms (yes, the API football ID as well as the other data source IDs) — and
> human-readable makes merging/mapping much easier. You have most of the data, it's just been through migrations,
> different canonical forms, different universe denominators over different iterations. A lot of it is just cleanup. We
> can drop live deployments for sports (not trading anything) whilst we fix the bad-data dumping, and migrate them so
> even live we stick to our known league universe — we should know a league we pull from rather than randomly grabbing
> and hoping the code knows about it. (Branding our leagues, tracking/identifiers, and making sure we have the relevant
> info around them in the registry, for use of that 6 million credits if we go to like 2 or 3 or 400 leagues.)

### Directive C — hybrid drop

> so its hybrid we would drop the ones that are left out of universe after universe expansion outside the 94 (api
> football only expansion as mentioned and just to burn those 6m credits)

## Progress Log

- **2026-06-24 — [A] code fixes ROLLED OUT to the running backfill (operator-requested).** Rebuilt the VM code tarballs
  (instruments-service@b0750369 + UAC@13ff387d, both carrying tasks 1-4) and **relaunched all 5 `sports-ref-v3-*`
  backfill VMs** (delete+recreate via `launch-sports-instruments-reference-vm.sh`). All 5 RUNNING on fresh instances
  (created 20:37-20:46 UTC, AFTER the 20:34 tarball upload), `DEPLOYMENT_STARTED` + heartbeating + Chunk 1 progress
  confirmed — extract-grep verified the uploaded tarball contains the off-season import (×2), transfer-window guard
  (×1), CLI verb (×3), and 728-pair coverage map. **The backfill now runs with the off-season/transfer-window
  skip-guards + new coverage map** (cheaper API-quota use on off-season/off-window days). Tarball-build gotcha (recorded
  for next time): the SPORTS bundle build aborts on ANY dirty bundle repo (mtds had foreign WIP) AND on a full `/tmp`
  (2G tmpfs) — surgically tar+upload only the needed clean repos with a disk-backed `TMPDIR`. NOTE: the LIVE-poller
  crons (`uts-prod-sports-scheduler-cron`, `uts-prod-sports-fixtures-noon-t1-schedule`) remain PAUSED — re-enabling live
  sports is a separate operator decision, not part of this backfill rollout.
- **2026-06-24** — Operator architecture spec (Directives A/B/C above) preserved verbatim; plan registered in
  `sports_master` epic (related_plans + workstream-routing row). PM LDR `9ca66844c`.
- **2026-06-24 — LIVE SPORTS DEPLOYMENTS DROPPED (operator-authorized, Directive B "drop live deployments for sports
  whilst we fix the bad-data dumping").** Deleted the three running un-gated wide-universe writers
  (`instr-backfill-sports-odds-20260623-150204`, `instr-backfill-sports-predictions-20260623-150151`,
  `sports-scheduler-20260624-010804`) and **PAUSED** the recurring crons that relaunch them:
  `uts-prod-sports-scheduler-cron` (`*/5` live poller) + `uts-prod-sports-fixtures-noon-t1-schedule` (12:00 UTC). These
  wrote out-of-universe/numeric rows (the over-capture) + burned the 6M API-Football budget on the full ~2,400-league
  provider universe. They stay paused until the write-gate ships (see Temporary states).
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — swapped the parent epic for the write-gate source
  (`sports_reference_core.py`) and the open E8 legacy-delete stub source (`_migrate_drop_stale.py`), the two remaining
  open-todo targets.

## Temporary states + their canonical follow-up

- **PAUSED sports crons** (`uts-prod-sports-scheduler-cron`, `uts-prod-sports-fixtures-noon-t1-schedule`) — **named
  re-enable gate**: the write-gate SHIPPED (`instruments-service@0345ffc`); re-enable after the VM tarball is rebuilt
  from clean LDR (`create-code-tarballs.sh`) so relaunched VMs carry the gate. Re-enable with
  `gcloud scheduler jobs resume <job> --location=asia-northeast1`. Tracked by Execution-sequence P0 (tarball+relaunch).
  **[2026-07-12 correction — finding 255, §A2 B-queue ruling]** RESOLVED — per the Execution-sequence P0 item above
  (`both crons resumed 2026-06-25`, tarball `a4b1bd032d9c`, write-gate `0345ffc` ancestor), both crons were ENABLED on
  2026-06-25. (Was: this bullet, unedited since, still framed them as PAUSED awaiting the same gate that already
  shipped + was already used to re-enable them.) Current live state: `uts-prod-sports-scheduler-cron` ENABLED (`*/5`)
  - `uts-prod-sports-fixtures-noon-t1-schedule` ENABLED (noon daily) — do not attempt to "re-enable" an already-running
    cron off this bullet's stale framing. **[2026-07-12 deploy outcome — operator-authorized prod deploy, escalation ii;
    see `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §Progress Log "sports prod deploy,
    escalation ii COMPLETE"]** Despite "ENABLED since 2026-06-25" above, both crons were **silently inert** for the
    entire window from resume (2026-06-25) until 2026-07-12: `uts-prod-sports-scheduler`'s Cloud Run Job fired every 5
    minutes but never dispatched (a scheduler local-backend/args bug — the Terraform fix `deployment-service@bb880b6`
    was committed but never `tofu apply`'d, so the job ran on a stale generation-1 container); the fixtures job
    (`uts-prod-instruments-service-sports-fixtures`) did not exist in prod at all (NOT_FOUND for all 4 schedules). Both
    fixed + verified 2026-07-12: scheduler args applied via a targeted single-resource OpenTofu plan (generation 2,
    state file unfroze); fixtures job CREATED via gcloud (mirroring dev, corrected to 8cpu/32Gi after an OOM at
    2cpu/4Gi), 3 consecutive successes incl. real unattended cron ticks. The FIXTURES freshness gap tracked elsewhere in
    this plan should start closing now that the 4 daily fixture-job runs are live.
- **PAUSED instruments-sports consolidator** (`uts-prod-manifest-consolidator-instruments-sports-cron`, was `*/1`) —
  paused 2026-06-24 so it can't re-merge the numeric-laden `_legacy_seed.parquet` shard back into the freshly
  canonicalized consolidated `_index`. **Re-enable gate**: resume ONLY after P0b (seed-canonicalize) is done. Resume:
  `gcloud scheduler jobs resume uts-prod-manifest-consolidator-instruments-sports-cron --location=asia-northeast1`.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — `locked_by: live-defi-rollout` (archival
  blocked) plus a 🟡 do-not-re-archive banner; among the 6 open todos, the E8 legacy-delete is explicitly
  BLOCKED-OPERATOR pending sign-off and is entangled in the still-open hard-stop-#2 carve-out contradiction
  (`cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md`), 'define the curated ~300-league reference set'
  is a design call, and the curated backfill is a deliberate ~6M-API-call budget burn
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — sole open item remains dependency-blocked. Note: `locked_by`
  carries a branch name rather than an agent/slot id — a tooling anomaly worth a separate check, not blocking.

- **round11 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA, valid — the sole open E8 legacy-delete todo is split: the
  safe prep half (register a `sports-drop-stale` launcher category + run a real dry-run census) was already extracted
  into `sports_satellite_ao_dispatch_batch12_2026_08_09.md` (today) with its finalize twin's own reconciliation todo
  (`sports_satellite_ao_dispatch_batch12_2026_08_09_finalize.md`); the actual `--drop-stale`/`--apply` firing remains a
  genuine operator sign-off residual per `plans/active/issues/ag_closeout_audit_sports_parked_2026_08_09.md`'s "Parked
  — operator-gated" entry (hard-stop #2, reversibility-qualified per §3a but not yet exercised for this specific
  population — needs the dry-run census's Part-5 twin-coverage proof first). No flip, no further extraction (would
  duplicate batch12).
