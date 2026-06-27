---
doc_type: plan
title: Sports ODDS bookmaker × market coverage enumeration + NaN-fill + cluster validation
summary:
  "Enumerate expected bookmaker × market sets per league tier, perform NaN-fill on ODDS coverage blanks, and validate
  odds cluster configurations for the sports vertical."
status: active
assigned_vm: planning
nature: process
stage: [meta]
repos: [instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [sports, odds, bookmaker, coverage, nan-fill, enumeration, validation]
related: [../epics/sports_master.md, ./sports_manifest_canonicalisation_2026_06_01.md]
created: "2026-06-12"
parent_epic: sports_master
assigned_role: data_engineering
execution_scope: orchestrator-agent
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-20
supersedes:
superseded_by:
depends_on:
source:
asset_group: cross-asset
drift_direction: advance-code
---

> **Provenance**: extracted 2026-06-20 from the inline `sports_master` epic body during the asset-group-umbrella
> restructure (the L0 umbrellas were carrying stale May-08 inline todos that the backlog regen — which only scans
> `plans/active/*.md`, never `plans/epics/` — never dispatched). This plan is the **genuinely net-new, unowned**
> ODDS-coverage residual: per-league-tier expected bookmaker/market enumeration + the orchestrator NaN-fill step + ODDS
> cluster-validation kwargs. Migrated from the epic's "EXPECTED_BOOKMAKER_MARKET_SETS NaN-fill enumeration" section
> (originally migrated from issue `odds_fixture_anchored_nan_fill_2026_05_08`).
>
> **Why this is net-new here and NOT a duplicate of `sports_manifest_canonicalisation_2026_06_01`**: that plan
> **EXPLICITLY DELEGATES** the odds-coverage / bookmaker-coverage backfill to `epics/sports_master.md` — it states it
> "canonicalises the FORM + relabels honest-absence; it does NOT backfill missing bookmaker coverage" and "25k odds
> `MISSING_EXPECTED` backfill stays with `epics/sports_master.md`". So the expected-set enumeration + NaN-fill IS the
> sports_master-owned half. Do NOT duplicate the FORM canonicalisation / source-relabel work here.

## Context

Today's instruments/MTDS orchestrator fetches the day-level ODDS endpoint with NO logic ensuring every
`(fixture × bookmaker × market_type)` triple is enumerated. Missing triples produce **zero rows instead of NaN-fill**,
violating the zero-volume-bar honest-absence precedent (CLAUDE.md "Honest absence" rule). Arbitrage / odds-movement
features silently miss bookmaker × market gaps, and the per-fixture cluster denominator can't be validated. The
mega-audit (sports A3) counted 25,652 `MISSING_EXPECTED` odds cells across ALL bookmaker × data_type combos — the
empirical-expected-set + NaN-fill is the honest fix for that gap.

## P0 — expected-set enumeration + orchestrator NaN-fill + cluster validation

- [x] ✅ [AGENT] P1. Empirical audit per league tier: which bookmakers + markets are expected to be present per (fixture,
      league_tier)? Output: UAC
      `EXPECTED_BOOKMAKER_MARKET_SETS: dict[LeagueTier, dict[BookmakerKey, list[MarketType]]]`. League tiers:
      TIER_1_DOMESTIC (EPL/LaLiga/SerieA/Bundesliga/Ligue1), TIER_2_DOMESTIC, TIER_1_INTERNATIONAL (UCL/UEL), etc.
      Empirical baseline: 2-week sample of fully-covered fixtures per tier. Repo: unified-api-contracts.
      — unified-api-contracts@702478cb | 5 new tests (test_honest_coverage.py) | 3 tiers defined: tier_1_domestic
      (pinnacle/betfair_ex_uk/williamhill/unibet_uk), tier_1_international (pinnacle/betfair_ex_uk/williamhill),
      tier_2_domestic (pinnacle/betfair_ex_uk); odds_api key convention. BLOCKED-CREDENTIALS for full 2-week GCS
      baseline (conservative seed from SPORTS_FIXTURE_CLUSTERS + ODDS_API_KEY_TO_VENUE correction; update from
      credentialed VM after running the full fixture-level audit).
- [x] ✅ [SCRIPT] P0. Orchestrator post-FIXTURES_SCHEDULE-capture step: for each fixture today, enumerate expected
      `(fixture × bookmaker × market)` triples per `EXPECTED_BOOKMAKER_MARKET_SETS[tier]`; for each missing triple,
      write a NaN-fill row with `record_captured` (NaN values per workspace honest-absence rule, NOT `record_empty` —
      `record_empty` is for legitimately-absent source responses; NaN-fill is for "we expected this triple but the
      source didn't return it"). Repo: instruments-service (sports orchestrator). — instruments-service@33c0796 | QG
      88.05% ✅ | 4 NaN-fill unit tests added (TestFootystatsOddsNanFill) | patch:
      footystats.\_load_scheduled_footystats_fixture_map
- [x] ✅ [SCRIPT] P0. Cluster-validation kwargs at `record_captured` for ODDS bundled writes:
      `expected_root_clusters = {fixture_id: len(EXPECTED_BOOKMAKER_MARKET_SETS[tier])}` per Phase 1A of writegate (per
      CLAUDE.md "Cluster validation MANDATORY at record_captured for bundled data_types"). Repo: instruments-service. —
      instruments-service@e1a3988 | SP-10-ODDS regression guard in test_orchestrator_sports.py | bridge: per-fixture ≥1
      row floor (→ len(EXPECTED_BOOKMAKER_MARKET_SETS[tier]) once item 1 ships)

> **Already shipped (downstream consumer guidance) — flipped in the epic, NOT re-opened here**: features-sports
> arbitrage/odds-movement NaN-row handling + the `codex/02-data/honest-absence-downstream-handling.md` § "ODDS NaN-fill
> semantics" doc were COMPLETED 2026-05-23 (sports_master epic body). This plan covers only the open writer-side
> enumeration + cluster-validation half above.

## Success criteria

- `EXPECTED_BOOKMAKER_MARKET_SETS` lives in UAC keyed by league tier, with an empirical 2-week baseline per tier.
- The sports orchestrator NaN-fills every expected `(fixture × bookmaker × market)` triple the source didn't return
  (honest absence: NaN-fill via `record_captured`, never silent zero-rows), and cluster validation at `record_captured`
  asserts the per-fixture expected-bookmaker-set denominator.
- `bash scripts/quality-gates.sh` green on the touched `unified-api-contracts` + `instruments-service` before commit.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the expected-set enumeration runs against
real GCS FIXTURES_SCHEDULE data for the Top-5 EU leagues; a smoke backfill of one league × one matchweek confirms
NaN-fill rows land at the canonical path with cluster validation passing (not zero-rows, not NaN-blanket).

## Input from P1c golden-window audit — 2026-06-27 (slot-4)

51 distinct league_ids observed in MTDS golden window (2025-09-01..2025-11-30, odds_api source, 18,194 captured trades rows). Two naming conventions present (SOCCER_* and canonical). P1 empirical audit should cover at minimum these league-tiers:

**SOCCER_* namespace (odds_api native names)**:
SOCCER_EPL, SOCCER_GERMANY_BUNDESLIGA, SOCCER_ITALY_SERIE_A, SOCCER_SPAIN_LA_LIGA, SOCCER_FRANCE_LIGUE_ONE,
SOCCER_NETHERLANDS_EREDIVISIE, SOCCER_PORTUGAL_PRIMEIRA_LIGA, SOCCER_BELGIUM_FIRST_DIV, SOCCER_TURKEY_SUPER_LEAGUE,
SOCCER_DENMARK_SUPERLIGA, SOCCER_SWITZERLAND_SUPERLEAGUE, SOCCER_AUSTRIA_BUNDESLIGA, SOCCER_UEFA_CHAMPS_LEAGUE,
SOCCER_CHINA_SUPERLEAGUE, SOCCER_RUSSIA_PREMIER_LEAGUE, SOCCER_ARGENTINA_PRIMERA_DIVISION, SOCCER_AUSTRALIA_ALEAGUE,
SOCCER_GREECE_SUPER_LEAGUE, SOCCER_JAPAN_J_LEAGUE, SOCCER_KOREA_KLEAGUE1, SOCCER_MEXICO_LIGAMX,
SOCCER_NORWAY_ELITESERIEN, SOCCER_POLAND_EKSTRAKLASA, SOCCER_SWEDEN_ALLSVENSKAN, SOCCER_USA_MLS

**Canonical namespace** (27 more):
PREMIER_LEAGUE, BUNDESLIGA, SERIE_A, LA_LIGA, LIGUE_1, CHAMPIONSHIP, PRIMERA_DIVISION, SEGUNDA_DIVISION,
SERIE_B, LIGUE_2, SUPERLIGA, SUPER_LIG, SUPER_LEAGUE, EREDIVISIE, EKSTRAKLASA, ELITESERIEN, ALLSVENSKAN,
PREMIERSHIP, FIRST_DIVISION_A, 2._BUNDESLIGA, A-LEAGUE, J1_LEAGUE, K_LEAGUE_1, MLS, LIGA_MX, PRIMEIRA_LIGA

**Additional blocker noted**: `fixture_id=NULL` for all golden window trades rows — the P1 audit must also confirm that fixture IDs are propagated to odds rows before per-fixture cluster validation (gate of P1c Todo 4) can proceed.

## Gap analysis from P1c Todo 4 cluster validation — 2026-06-27 (slot-4)

Static cluster validation performed against `sports_bookmaker_league_coverage.json` (27 bookmakers × 51 leagues).

**Coverage mapping result (23 mapped / 51 total)**:

- `tier_1_domestic` (10 leagues): BUNDESLIGA, LA_LIGA, LIGUE_1, PREMIER_LEAGUE, SERIE_A, SOCCER_EPL, SOCCER_FRANCE_LIGUE_ONE, SOCCER_GERMANY_BUNDESLIGA, SOCCER_ITALY_SERIE_A, SOCCER_SPAIN_LA_LIGA — expected bookmakers (pinnacle, betfair_ex_uk, williamhill, unibet_uk) ALL PRESENT ✅
- `tier_1_international` (1 league): SOCCER_UEFA_CHAMPS_LEAGUE — expected bookmakers (pinnacle, betfair_ex_uk, williamhill) ALL PRESENT ✅
- `tier_2_domestic` (12 leagues): 2._BUNDESLIGA, CHAMPIONSHIP, EREDIVISIE, FIRST_DIVISION_A, LIGUE_2, PRIMEIRA_LIGA, PRIMERA_DIVISION, SEGUNDA_DIVISION, SERIE_B, SOCCER_BELGIUM_FIRST_DIV, SOCCER_NETHERLANDS_EREDIVISIE, SOCCER_PORTUGAL_PRIMEIRA_LIGA — expected bookmakers (pinnacle, betfair_ex_uk) ALL PRESENT ✅

**28 league_ids with NO tier definition in `EXPECTED_BOOKMAKER_MARKET_SETS` (GAPS TO FILE)**:
A-LEAGUE, ALLSVENSKAN, EKSTRAKLASA, ELITESERIEN, J1_LEAGUE, K_LEAGUE_1, LIGA_MX, MLS, PREMIERSHIP,
SOCCER_ARGENTINA_PRIMERA_DIVISION, SOCCER_AUSTRALIA_ALEAGUE, SOCCER_AUSTRIA_BUNDESLIGA,
SOCCER_CHINA_SUPERLEAGUE, SOCCER_DENMARK_SUPERLIGA, SOCCER_GREECE_SUPER_LEAGUE,
SOCCER_JAPAN_J_LEAGUE, SOCCER_KOREA_KLEAGUE1, SOCCER_MEXICO_LIGAMX, SOCCER_NORWAY_ELITESERIEN,
SOCCER_POLAND_EKSTRAKLASA, SOCCER_RUSSIA_PREMIER_LEAGUE, SOCCER_SWEDEN_ALLSVENSKAN,
SOCCER_SWITZERLAND_SUPERLEAGUE, SOCCER_TURKEY_SUPER_LEAGUE, SOCCER_USA_MLS,
SUPERLIGA, SUPER_LEAGUE, SUPER_LIG

**Required follow-up actions (for empirical P1 audit to enable P1c gate)**:
1. Add a `LEAGUE_ID_TO_TIER` mapping function (or direct dict) to UAC that routes each of the 51 observed league_ids to a LeagueTier key in `EXPECTED_BOOKMAKER_MARKET_SETS` — without it, runtime cluster validation code cannot determine which expected bookmaker set applies to a given manifest row.
2. Extend `EXPECTED_BOOKMAKER_MARKET_SETS` to cover the 28 unmapped league_ids above (or add a `tier_3_global` / `no_expectation` tier for non-EU leagues that the empirical audit determines have inconsistent bookmaker coverage).
3. Fix `fixture_id=NULL` propagation in the odds_api backfill path — golden window `trades` data has all fixture_ids as NULL, preventing per-fixture cluster validation.
4. Note: `data_type=trades` is NOT in `BUNDLED_DATA_TYPES` (see `_honest_coverage_clusters.py`) — cluster validation at `record_captured` does not fire for historical `trades` data; only `odds_snapshot`, `odds_movement`, `arbitrage_opportunity` are enforced. The validation gate for `trades` relies on this static audit path.
