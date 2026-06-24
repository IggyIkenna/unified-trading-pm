---
title: Sports canonical universe + API-Football reference expansion (curate, don't over-capture)
parent_epic: sports_master
assigned_vm: human-planning
created: 2026-06-24
estimate_class: design
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 7.2
execution_scope: local-only
locked_by: live-defi-rollout
locked_since: 2026-06-24
priority: P2
status: active
---

# Sports canonical universe + API-Football reference expansion

> Captures the operator architecture spec (2026-06-24) after the over-capture diagnosis. Refine the existing codex /
> UAC / code rather than reinvent — this is mostly cleanup + consolidation of forms we already have through migrations.

## The diagnosis (root cause of the "low coverage / numeric keys / failures")
The sports `_index` (4.6M rows) is NOT a numeric-vs-canonical schema split — it's **out-of-universe over-capture**: the
date-wide API-Football adapter calls return the provider's entire **~1,200–2,400-league** universe, but our canonical
trading universe is **94 leagues** (`get_expected_leagues_for_source("api_football")`) / 101 (`LEAGUE_REGISTRY`).
**1,676,612 rows (36%)** are out-of-universe leagues. The "numeric/blank league_id" rows are just the api-football-path
slice of this cross-provider over-capture; the resolvable in-universe numerics (215,881) all have a canonical twin
(100% dedup). Numeric rows are STILL being written (live writer pollution) until the write-gate ships + VMs relaunch.

## Operator decision (2026-06-24): HYBRID — curated reference expansion, then drop residual
- **94 stays the TRADING/downstream universe.** All non-API-Football sources + trading services stay bounded to 94 (or
  less, per each source's eligibility). NOT expanding what we predict/trade.
- **Expand the API-Football *reference* universe** to a curated **~300 leagues** (budget-justified below) — the leagues
  + cups worth holding for reference/features/arb: the 94 + the division below each country + continental cups
  (Champions League, UEFA/UECL, Copa Libertadores/Sudamericana, AFC/CAF equivalents) + major internationals (World Cup,
  Euros, Copa America…). Reference-only; downstream derives nothing new from them unless explicitly promoted.
- **DROP the rows STILL outside the curated set after expansion** (not drop-vs-94) — the truly-junk leagues with no
  prediction/arb/reference value. Snapshot-first; `--drop-out-of-universe` retargeted to "outside curated".

## 6M-call budget (why ~300)
~6M API-Football calls available over the coming weeks (300k/day quota). Per-fixture enrichment dominates:
lineups+stats+events+player_stats ≈ 4 calls/fixture; top league-season ≈380 fixtures → ~1,900 calls/league-season;
2019→2025 ≈7 seasons → ~13k/league full history. 6M ÷ 13k ≈ **~450 leagues** for full enrichment — effectively more
(we already hold many fixtures; lower/cup leagues have few fixtures + often no enrichment → gated honest-empty, no
call). So ~300 curated is comfortable + value-appropriate; ~2,400 would burn the budget on enrichment-less junk.

## Architecture (canonical-everything; mostly cleanup of existing forms in UAC)
1. **Canonical league + cup registry (UAC SSOT)** — every league/cup has: human-readable canonical name, API-Football
   id, other-source ids, **is-league-vs-cup**, **country**, **season start/end per year**, **transfer window**
   (transfermarkt consumes it; we need it for refresh timing + ML training windows). Annual league-id changes
   (footystats / SFI rotate ids per season) → per-season id mapping in UAC.
2. **Per-source league eligibility (UAC SSOT)** — each source's coverage, bounded by API-Football existence (can't get a
   source for a league API-Football doesn't have): understat ~6; footystats/T-stats ~50 (subscription cap); odds-API
   ~20 (+ per-bookmaker-league restriction); SFI its subset; weather = fixture/venue-location-based (bounded by 94).
   Every source CHECKS canonical eligibility + converts canonical→its-query-id. Honest coverage MUST bake these caps in
   so we never mislabel `empty_confirmed` when a source legitimately doesn't cover a league.
3. **Canonical teams / players / fixtures** — API-Football id → human-readable canonical name + other-source mappings.
   Fixture = canonical fixture/event id (instrument-id-like) derived from teams; odds-API derives its pulls from it.
4. **Honest coverage** consumes (1)-(3): denominator = only-eligible (league × source × data_type) cells; everything
   else honest-absence/out-of-window. No mislabeled gaps.

## Execution sequence (phased; fastest-but-safe)
- [x] ✅ [INFRA] P0. Stop live sports deployments (not trading; over-capture pollution) — `mtds-live-sports-*` terminated 2026-06-24.
- [x] ✅ [CODE] P0. **Write-gate to known/eligible leagues** (no random grab) — SHIPPED `instruments-service@0345ffc`
  (`_is_in_canonical_write_universe` gates the per-league capture-write loops to the 94-league
  `get_expected_leagues_for_source("api_football")` set; numeric/out-of-universe leagues never written as captured) +
  the `canonicalize_sports_league_id_schema_2026_06_24.py` migration. Landed on LDR, Tier-C drain → staging (v2-gated).
  Gated to **94 first**; widen to the curated set in the P1 step below.
- [ ] [INFRA] P0. **Tarball rebuild + relaunch + re-enable crons** — after `0345ffc` reaches the live image path
  (`create-code-tarballs.sh` from clean LDR), `gcloud scheduler jobs resume uts-prod-sports-scheduler-cron
  uts-prod-sports-fixtures-noon-t1-schedule` so relaunched VMs carry the write-gate (no more numeric pollution).
  **Do FIRST: the 94-league golden-window clean below, so the relaunch writes onto a clean canonical _index.**
- [x] ✅ [DATA] P0a. **`_index` canonicalize+dedup migration APPLIED 2026-06-24** — `canonicalize_sports_league_id_schema_2026_06_24.py --apply`:
  518,799 in-universe numeric+suffixed → canonical, 509,227 dedup-collapse, **in-universe numeric residual → 0**;
  4,599,952 → 4,090,725 rows; out-of-universe numeric (604,139) KEPT (hybrid — drop after curated expansion). Snapshot
  `_index/snapshots/pre_league_id_canonicalize_20260624T092926Z.parquet`. Consolidator
  `uts-prod-manifest-consolidator-instruments-sports-cron` PAUSED to prevent a re-merge race (see Temporary states).
  Re-measure: FIXTURES 93.9%→**100%**, golden-window in-window-gap 10,988→10,765, overall **65.2%** captured.
- [x] ✅ [DATA] P0b-seed. **Seed-canonicalized + consolidator resumed 2026-06-24** — the lone per-VM shard
  `_index/per_vm/_legacy_seed.parquet` (4.5M rows, 1.05M numeric) was overwritten with the clean canonical consolidated
  (lossless: consolidated ⊇ seed content) → seed now 4,090,725 rows, in-universe numeric=0 (snapshot
  `_index/snapshots/pre_seed_canonicalize_*_legacy_seed.parquet`). `uts-prod-manifest-consolidator-instruments-sports-cron`
  RESUMED — no re-pollution (canon + seed both canonical now).
### Per-league hive-partition architecture (VERIFIED 2026-06-24 — corrects an earlier wrong "league is just a column" claim)
The modern sports layout **IS per-league hive-partitioned with the CANONICAL league as the partition key** — UAC
`gcs_paths.py` SSOT: `sports_reference/by_date/day={D}/entity={F}/league={canonical}/{F}.parquet`
(`SportsLayout.PER_DAY_PER_LEAGUE`, the default for most entities). Three layouts: `PER_DAY_PER_LEAGUE` (most),
`PER_DAY_PER_SEASON` (bulk, e.g. player_values — intra-file `canonical_league` filter), `PER_DAY_BARE` (single-file/day
entities like XG/WEATHER, OR pre-per-league legacy). **This is exactly the design the operator described** and it
satisfies every requirement:
- **Query / train / predict per-league** → the `league=<canonical>` partition is a pushdown predicate (read one league's dir).
- **Add a new league over time** → a brand-new `league={canonical}/` dir; never appends-into / wipes / skips an existing
  league's parquet; its own manifest cell.
- **Parallel-VM safety** → league-A-VM writes `league=EPL/`, league-B-VM writes `league=LA_LIGA/` — DIFFERENT files, no
  same-parquet collision (the per-league split is precisely what removes the operator's parallel-write hazard). Shard
  atom = `(entity, league, day)`.
- **Skip-existing pre-flight** → `sports_reference_fixtures.py:390` reads the existing per-`(entity, league, day)`
  parquet, builds the set of already-captured `af_fixture_id`s, and skips them (per-league + per-fixture-within).
- **Coverage on a league basis** → data-status drill-down hierarchy is `data_type → league_id → date`
  (`codex/02-data/data-status-drilldown-hierarchy.md:23`); the `_index` carries `league_id` per row → per-league % is real.
- **Write path** → orchestrator writes `partition={"entity":…, "league": _canonical_league_id(…)}` (verified
  `sports_reference_core.py`). VERIFIED in GCS: 2018→69, 2020→107, 2023→115, 2025→80 **canonical** `league=` dirs;
  **0 in-universe numeric** across all years (only 2 out-of-universe `14231`/`315` in 2025).
- [x] ✅ [DATA] P0b-paths. **No in-universe path-move needed — VERIFIED already canonical** (0 in-universe numeric
  `league=` dirs across 2018-2025; the partition key is already `league=EPL` etc.). The earlier "no league partition"
  reasoning was WRONG (sampled a 2015 bare path); the conclusion holds because in-universe data is already canonical.
- [ ] [DATA] P0. **Eliminate the bare/legacy dual-layout (operator: "legacy needs canonicalising or deleting —
  that's the whole point")** — per-league entities that have BOTH a per-league split AND bare files for older days
  (`gcs_paths.py:96`) carry a stale parallel layout. For each: canonicalise the bare→per-league (in-retention) OR DELETE
  (pre-retention). Distinguish from the *by-design* bare entities (XG/WEATHER/player_values-bulk) which stay bare.
- [ ] [DATA] P0. **Retention floor = the EXISTING per-source genesis registry — NOT a blanket 2015 delete
  (corrected 2026-06-24).** The genesis SSOT already exists + is populated: UAC `canonical/domain/sports/league_data.py`
  `SOURCE_COVERAGE_START` = understat **2014-01-01**, api_football **2015-01-01**, footystats/transfermarkt/SFI
  **2019-01-01**, open_meteo 2019-03-02, odds_api/mdps_odds **2020-06-06**; + per-`(source,data_type)` overrides
  (SFI_PROGRESSIVE_STATS 2020-01-01) + per-`(source,league)` (UNDERSTAT_COVERED_LEAGUES, bookmaker-league). Consumed by
  honest coverage via `clip_dates_to_source_coverage()` / `is_before_source_ln`. **Implication: 2015-2017 is VALID
  understat(2014)/api_football(2015) history — KEEP it** (the operator's "don't need 2015" is overridden by the SSOT,
  which deliberately retains it for ML training). Earliest real day = 2015-01-01, **0 pre-2014 partitions**. So
  retention cleanup is SMALL, not a blanket delete:
  - **`day=all`** is NOT a stray to delete — it holds `entity=teams` + `entity=venues` (~974KiB), date-invariant
    REFERENCE data. But `teams` also appears per-day-per-league → possible dual storage. RECONCILE: canonical home for
    date-invariant reference is `SportsLayout.FLAT` (`sports_reference/{F}/{F}.parquet`); fold `day=all` into FLAT (or
    confirm which the readers use) + dedup — do NOT blind-delete (would break team/venue resolution).
  - Per-source pre-genesis ANOMALIES only (e.g. any footystats parquet before 2019, odds before 2020-06) — targeted
    check + delete/relabel; honest-absence clip already hides them from the denominator.
- [ ] [DATA] P0. **NICE-TO-HAVE / watch-item: odds-granularity (operator: "only add if needed")** — the odds-API
  granularity change (10-min → 5-min snapshots ~2024) + odds-types added over time are NOT captured at a
  per-`(source,data_type,effective-date)` grain today. Add a dated capability entry ONLY IF we find it mislabels
  coverage (e.g. pre-2024 10-min data read as missing 5-min). Same "add per-league/per-date granularity only on
  discovery" pattern as the existing registry.
- [x] ✅ [DOCS] P0b-codex. **Fixed `per-asset-group-bucket-layouts.md` 2026-06-24** (PM@6fc561a45) — SPORTS row now
  documents the per-league canonical hive partition + all 4 `SportsLayout` variants + `candidate_parquet_paths`.
  (`sports-adapter-dependency-order.md` still shows `entity=fixtures` shorthand without `league=` — minor, fold into the
  next sports-codex touch.)
- [ ] [DATA] P0. **2 out-of-universe numeric `league=` dirs** (`14231`/`315`) — fold into the hybrid residual-drop
  (P2 below) or drop now (snapshot-first).
- [ ] [DATA] P0. **94-league enrichment backfill** — the residual golden-window gap is now GENUINE missing enrichment
  (XG_SHOTS 0% / XG 13% / PLAYER_STATS 21% / MATCHES 35% / INJURIES 37%), NOT a schema artifact. API-Football fixtures
  (fast, already 100%) → enrichment for the 94, fix broken, be thorough → re-measure toward 100%. Needs the tarball
  rebuild (write-gate in image) below first.
- [ ] [CODE] P1. **UAC canonical registry build/refine** — league/cup canonical + ids + is-cup + country + season
  start/end + transfer window; per-source eligibility maps + annual-id-change handling; team/player/fixture canonical +
  mappings. Wire honest-coverage to consume them.
- [ ] [DATA] P1. **Define the curated ~300-league reference set** (94 + below-division + continental cups + majors) +
  widen the write-gate to it.
- [ ] [DATA] P2. **Curated-universe backfill** (API-Football fixtures + enrichment, 2019→, burn ~6M over weeks; gated +
  honest-empty for no-enrichment leagues).
- [ ] [DATA] P2. **DROP residual out-of-curated rows** (snapshot-first) once the curated set is backfilled.
- [ ] [SCRIPT] P3. Delete superseded-buggy `instruments-service/scripts/backfill_fixture_lineups_blank_reason.py`
  (env-less bucket + direct google.cloud SDK).

## Audit findings + verified enforcement (2026-06-24) — answers "how can we still have two SoT"
### Two-SoT root cause (why dual layout persists despite the migration plans)
`sports_manifest_canonicalisation_2026_06_01.md` is **code-complete + dry-run-green but its IRREVERSIBLE GCS object
`--apply` (E3→E8: fleet-drain → object-rewrite → legacy-delete) was gated on operator sign-off + fleet drain +
foundation gates and NEVER FIRED.** So the migration sits in a *pre-apply* state — the plans don't lie (they correctly
mark `--apply` PENDING), but the un-fired gated step is exactly why dual layout persists. Live `_index` audit
(4,047,452 rows, 2026-06-24):
- ✅ **schema_version: 100% v9** (the consolidator rebuild v9'd it; the plan's "100% v8" was its stale 2026-06-01
  pre-snapshot — so the V9 manifest migration effectively COMPLETED since).
- ✅ pipeline_mode: populated (batch_api_football 2.2M, batch_footystats 907k…).
- ❌ **source column: 1,465,986 BLANK (36%)** — the CF-4 source-stamp is INCOMPLETE.
- ❌ **asset_group: ~1.31M blank/empty (32%)** — the CF-2 stamp is INCOMPLETE.
- ⚠️ league_id: in-universe canonical; 604,139 out-of-universe numeric (hybrid); **55,884 blank**.
- ❌ **GCS object layout: dual on disk** (E-steps unfired) + a `date="all"` reference-row class bleeding into `_index`.
- ⏳ **Still un-audited**: `market-data-tick-sports` (MDPS odds) + `features-sports` bucket object layouts.

### VERIFIED enforced — enrichment-not-available ≠ attempted_failed (operator's "I hope it's enforced")
`is_league_entity_covered(league, entity)` (UAC `registry/sports_league_entity_coverage`, an OBSERVED-from-captured
map) gates the capture write (`sports_reference_core.py:115`): a league lacking an enrichment entity records
`EXPECTED_NO_PROVIDER_COVERAGE` (out_of_window, NON-counting, **NOT retried**) — DISTINCT from `attempted_failed` (a
fetch was attempted + errored → retried). This closed a ~72% `attempted_failed` over-count. **Hardening remaining**: the
map is built by the one-off `refresh_sports_league_entity_coverage_2026_06_21.py` → (a) refresh it AFTER the enrichment
backfill (records newly-observed enrichment), (b) promote it to a recurring CLI subcommand.

## Remaining program (operator 2026-06-24) — sequenced by unblock-value; action ASAP, parallel where independent
**[A] CODE HARDENING — no API quota; unblocks B/C/D correctness+efficiency (run in PARALLEL with B):**
- [x] ✅ [CODE] P0. **FIXTURES: switch per-(league,day) → per-(league,season) BULK fetch** — instruments-service@a241b84. Added `_season_fixture_cache` class-level dict keyed `(league_id, season_year)` and `_fetch_season_fixtures_with_raw` method (GET `/fixtures?league&season`, no `date=`, cached). `get_fixtures` and `get_fixtures_with_raw` use season cache when `league_ids` supplied, filter in-memory by date; no-league-ids path unchanged. Non-match days return `[]` with zero API calls. Cuts call count 5-10× for multi-date backfills and the 9-day repoll window. Tests: `TestApiFootballFetchSeasonFixturesWithRaw` (cache-miss, cache-hit, exception) + updated `TestApiFootballGetFixturesWithRaw` (cache isolation, date filter, fallback path).
- [x] ✅ [CODE] P0. **Season-window clip for downstream per-day sources** (weather, footystats, understat,
  soccer_football_info) — instruments-service@d651557. Wired `get_source_coverage_start` / `is_in_known_gap` guards into
  5 insertion points: weather.py (open_meteo/WEATHER), understat.py ×2 (XG + XG_SHOTS), footystats.py ×2
  (PREDICTIONS + MATCHES). Off-season cells emit `record_expected_empty("EXPECTED_PRE_SOURCE_COVERAGE_START")` without
  any API call. 5 new pre-cutoff tests + 2 footystats skip-path tests restore coverage above 88% floor; 3757 tests pass.
  **COMPLETED 2026-06-24 — true off-season clip added — instruments-service@1bb2324**: d651557 only did the
  genesis-floor (`EXPECTED_PRE_SOURCE_COVERAGE_START`); 1bb2324 adds the actual off-season season-window clip via UAC
  `footystats_season_status_for_day` — when EVERY expected league is in its off-season gap on a date, the source skips
  the API call and records per-league `record_expected_empty(EXPECTED_PRE_SEASON|EXPECTED_POST_SEASON)`. Wired into
  weather.py, understat.py ×2 (XG + XG_SHOTS), sfi.py (NEWLY added — d651557 had skipped sfi), footystats.py ×2
  (predictions + matches). 6 new `TestOffSeasonSeasonWindowGuard` tests; QG green.
- [x] ✅ [CODE] P0. **Transfermarkt = TRANSFER-WINDOW-aware** (NOT pure off-season — windows open mid-season + at
  start/end of season) — instruments-service@1bb2324. `_fetch_transfermarkt_data` now skips PLAYER_VALUES fetches on
  dates outside ALL expected leagues' transfer windows AND with no refresh-trigger for any league (conservative — never
  over-clips season-start/promotion refreshes; respects `force`), recording per-league
  `record_empty(EmptyConfirmedReason.EXPECTED_OUTSIDE_TRANSFER_WINDOW)` via UAC `is_transfer_window_open` +
  `get_leagues_needing_refresh`. 3 new `TestTransfermarktTransferWindowGuard` tests (outside-window skip / within-window
  fetch / force bypass); QG green.
- [ ] [CODE] P1. **Refresh `is_league_entity_covered` map post-enrichment + promote to a recurring CLI** (retire the
  one-off refresh script) — so newly-observed enrichment is annotated + treated as honest coverage, never retried.
- [x] ✅ [CODE] P0. **Golden-window denominator fix → VMs see FIXTURES 100%** for 2025-09..11 —
  instruments-service@f3a5447 + applied 2026-06-24. New
  `scripts/reclassify_golden_window_fixtures_no_match_2026_06_24.py` (in-place, snapshot-first, truth-set-gated)
  reclassified **223** golden-window FIXTURES no-match-day cells (blank/`SOURCE_RETURNED_ZERO`, NOT in the
  FIXTURES truth-set) → `empty_confirmed`/`EXPECTED_NO_FIXTURE`; **0 attempted_failed + 0 in-truth real failures
  touched**. Consolidator paused→apply→resumed; verified the reclassify **stuck across 2 merge cycles** (no
  re-pollution — incremental merge reads canonical + changed shards, not the settled seed). **Re-measured
  2025-09-01..11-30: FIXTURES = 3444 captured + 7770 EXPECTED_NO_FIXTURE, 0 failed, 0 expected_unattempted →
  data-type-aware coverage = 100.00% (11214/11214).** Pre-flight no longer retries (a241b84 season-cache already
  makes no-match days zero-call; now also denominator-correct). Snapshot:
  `_index/snapshots/pre_golden_fixture_reclass_20260624T194010Z.parquet`.

**[B] GCS MIGRATION `--apply` — operator-APPROVED 2026-06-24 ("time to run that"); ORPHAN-CHECK FIRST (pure-canonical):**
- [x] ✅ [DATA] P0. **GCS object migration `--apply` DONE + verified 2026-06-24** — `migrate_sports_canonical_v9.py
  --apply` both surfaces, 2015-2026, 0 orphans corpus-wide (dry-run gate). Transform = INSERT `pipeline_mode=` after
  `day=` (the `league=<canonical>` partition was already canonical). Result: instruments **652,062 copied** (+112k
  idempotent-skip = all 764,137 accounted), MDPS **8** (617k already canonical), **0 errors**. Verified: 1:1
  legacy↔canonical parity (2025-10-15: 82↔82), canonical readable
  (`pipeline_mode=batch_api_football/entity=…/league=BRASILEIRAO/`). Readers prefer canonical → **dual-SoT functionally
  resolved for reads.** Additive (legacy coexists, not deleted).
- [ ] [DATA] P1. **Legacy-delete (E8) — `--drop-stale` is an UNIMPLEMENTED stub** (line 886-891 raises). The legacy
  (no-`pipeline_mode`) objects remain as dead weight (not harmful; readers use canonical). Implement the per-surface
  delete (twin-verified: only delete a legacy object whose canonical `pipeline_mode=` twin exists + is readable) +
  operator gate (IRREVERSIBLE) — OR a separate `gcs_delete_object` sweep with the same twin-verification. NOT urgent.
  **`sports_reference_v1_archive/` VERIFIED SAFE-TO-DELETE 2026-06-24** (no migration needed): it's the v1
  wide-denormalized fixtures (398 days 2018-2026, bare layout, human-readable strings + `data_available_at`, xg/stats
  cols all NULL). Coverage check across 5 days 2018→2026: archive `af_fixture_id` ⊆ canonical `af_fixture_id`
  (**canon-only=0**; canonical equal-or-superset). The v2 canonical stores `af_*` ids + canonical `league=` path +
  derives human-readable via UAC registries (the by-design store-id/derive-name pattern), so the archive's data is fully
  represented. Delete it with the legacy sweep (snapshot-first).
- [x] ✅ [DATA] P0. **`_index` CF-2/3/4 stamp DONE — BOTH sports surfaces now CF-GREEN 2026-06-24** via the new
  `instruments-service/scripts/canonicalize_sports_index_cf234_2026_06_24.py` (in-place, preserves everything; source =
  `pipeline_mode` minus its `{mode}_` prefix, `expected_unattempted` source-exempt; asset_group=sports; pipeline_mode
  derived from source/data_type). **NOT the E5/E6 rebuild** — that REGRESSES source (drops it on empty re-emits, verified
  CF-4 1.4M→2.49M; the reason-relabel it does is already covered, CF-5 was green). Results, both consolidator-paused +
  snapshot-first + shard-reseeded + resumed:
  - instruments-store-sports (4,047,892 rows): asset_group 1.31M→0, pipeline_mode 88k→0, source 1.47M→0 (non-exempt) →
    **CF VERDICT GREEN**.
  - market-data-tick-sports / MDPS (1,760,262 rows): source 1.19M→0 → **CF VERDICT GREEN**.
  - **Manifest V9 is now ENTIRELY canonical (CF-1…CF-12) across both sports surfaces** — the gate for deleting all
    legacy data is met for the manifest. (Script needs shipping via quickmerge once the foreign-dirty IS tree clears.)

**[C] API-FOOTBALL FIXTURES backfill SINCE 2015 (94 leagues)** — needs [A] season-window for efficiency; ~35-50k
incremental calls no-force for 2019+, scaling modestly for 2015-2018. Unblocks [D]. (api_football genesis = 2015.)
- [ ] [DATA] P0. Fixtures backfill 2015→present, 94 leagues, no-force, season-window-gated.

**[D] ENRICHMENT backfill SINCE 2015** — needs [C] (fixtures first) + uses results to refresh [A]'s availability map.
The big quota sink (~4 calls/fixture: lineups/stats/events/players) + downstream (weather/footystats/understat/SFI per
eligibility + season/transfer windows).
- [ ] [DATA] P1. Enrichment backfill 2015→present for the 94 leagues, then annotate per-(league,entity) availability.

**SEQUENCING:** [A]+[B] now in parallel (code vs data-layer, independent) → [C] once [A] season-window lands → [D] after
[C]. Biggest single unblock = [B] (resolves dual-SoT + stamps) and [A] (correct+cheap backfills) — both start now.

## FINDING 2026-06-24: v2 canonical fixtures lack a STORED human-readable canonical fixture-id (operator-surfaced)
The v2 canonical `entity=fixtures` stores **`af_fixture_id` (numeric, the only fixture id)** + `af_home_name`/`af_away_name`
(AF-RAW names, not canonical-registry team names) + numeric `af_home_id`/`af_away_id`/`af_league_id` + canonical
`league=` in the PATH + date/scores/status. There is **NO stored composed human-readable canonical fixture-id** (the v1
archive HAD `fixture_id = LEAGUE:HOME_v_AWAY:DATE`); the `_index` `fixture_id` column is blank/unused. The human-readable
id is DERIVABLE (path league + home/away + date) but not materialized.
- Per the operator's design the human-readable canonical fixture-id is "almost an instrument/event/fixture ID" + the
  **cross-source join key** (fixtures ↔ odds ↔ footystats). Storing only `af_fixture_id` means cross-source joins bridge
  on the numeric AF id or re-derive the string each time; stored team names are AF-raw, not canonical.
- NOT a blocker for the archive delete (the id is derivable from what canonical stores). But a focused NEW canonicalization
  if we want it stored:
- [x] ✅ [CODE] P1. **RESOLVED — derive-at-read accepted (operator 2026-06-24).** The v2 fixtures keep `af_fixture_id`
  (numeric) as the stored key; the human-readable canonical fixture-id is **derived at read** via the global helper
  `unified_api_contracts.sports.build_fixture_id(league_id, home_team_id, away_team_id, date_str)` →
  `"EPL:ARSENAL_v_CHELSEA:2026-01-15"` (any service imports it). Cross-source joins build the SAME id from each source's
  league+teams+date (as `add_canonical_fixture_ids.py` already does for understat/footystats; same for odds-api). No
  stored column needed. Revisit only if cross-source joins prove fragile at scale.

## Codex SSOT updates
- `codex/02-data/sports-data-source-coverage-matrix.md` — the curated universe + per-source eligibility + caps.
- `codex/02-data/availability-manifest-and-data-status.md` — honest-coverage eligibility rules (per-source league caps).
- New: `codex/02-data/sports-canonical-league-cup-registry.md` — the canonical id/name/season/transfer-window SSOT.

## Operator verbatim directives (2026-06-24) — preserved in full (do NOT lose nuance to summary)

### Directive A — API-Football reference universe + canonical-everything + per-source eligibility
> essentially api football should have as many leagues including continental cups and world cup etc as it can that
> exist for football end of the day thats what exists - with canonical form for league and cup names. it should know
> whats a league and whats a cup i assume that's already there somewhere in leagues mappings/registry in UAC. Even
> though downstream we're not going to use a lot of them, it just allows us to add without always having to keep
> re-querying the API football. We have, like, twenty-something days' worth of 300k calls, so that's like 6 million
> calls to the API football. If you can work out roughly how many leagues and enrichment data we can realistically get
> from the API football with 6 million calls (since, whatever it is, 2019 is it?), then that will give us a good idea of
> how many leagues to include. Include the enrichment stats in that analysis so that we don't overcook it. Obviously, we
> already do have a bunch of fixtures in the API football, so it wouldn't be a full re-backfill. My guess is we can get
> to at least 90 something or 100, maybe even 200.
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
- **2026-06-24** — Operator architecture spec (Directives A/B/C above) preserved verbatim; plan registered in
  `sports_master` epic (related_plans + workstream-routing row). PM LDR `9ca66844c`.
- **2026-06-24 — LIVE SPORTS DEPLOYMENTS DROPPED (operator-authorized, Directive B "drop live deployments for sports
  whilst we fix the bad-data dumping").** Deleted the three running un-gated wide-universe writers
  (`instr-backfill-sports-odds-20260623-150204`, `instr-backfill-sports-predictions-20260623-150151`,
  `sports-scheduler-20260624-010804`) and **PAUSED** the recurring crons that relaunch them:
  `uts-prod-sports-scheduler-cron` (`*/5` live poller) + `uts-prod-sports-fixtures-noon-t1-schedule` (12:00 UTC). These
  wrote out-of-universe/numeric rows (the over-capture) + burned the 6M API-Football budget on the full ~2,400-league
  provider universe. They stay paused until the write-gate ships (see Temporary states).

## Temporary states + their canonical follow-up
- **PAUSED sports crons** (`uts-prod-sports-scheduler-cron`, `uts-prod-sports-fixtures-noon-t1-schedule`) — **named
  re-enable gate**: the write-gate SHIPPED (`instruments-service@0345ffc`); re-enable after the VM tarball is rebuilt
  from clean LDR (`create-code-tarballs.sh`) so relaunched VMs carry the gate. Re-enable with
  `gcloud scheduler jobs resume <job> --location=asia-northeast1`. Tracked by Execution-sequence P0 (tarball+relaunch).
- **PAUSED instruments-sports consolidator** (`uts-prod-manifest-consolidator-instruments-sports-cron`, was `*/1`) —
  paused 2026-06-24 so it can't re-merge the numeric-laden `_legacy_seed.parquet` shard back into the freshly
  canonicalized consolidated `_index`. **Re-enable gate**: resume ONLY after P0b (seed-canonicalize) is done. Resume:
  `gcloud scheduler jobs resume uts-prod-manifest-consolidator-instruments-sports-cron --location=asia-northeast1`.
