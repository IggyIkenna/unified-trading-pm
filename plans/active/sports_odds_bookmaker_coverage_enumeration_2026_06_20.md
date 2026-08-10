---
doc_type: plan
title: Sports ODDS bookmaker × market coverage enumeration + NaN-fill + cluster validation
summary:
  Enumerate expected bookmaker × market sets per league tier, perform NaN-fill on ODDS coverage blanks, and validate
  odds cluster configurations for the sports vertical.
status: active
nature: process
asset_group:
  [sports] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine mistag:
  # title/summary say "the sports vertical" explicitly, parent_epic is sports_master -- content is sports-only

stage: [meta]
repos: [instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [sports, odds, bookmaker, coverage, nan-fill, enumeration, validation]
related:
  [
    ../epics/sports_master.md,
    ../archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md,
    ./sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-06-12"
parent_epic: sports_master
assigned_vm: NA
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
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /codex/02-data/honest-absence-downstream-handling.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_honest_coverage_clusters.py,
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/issues/sports_plan_and_docs_reconcile_findings_2026_07_24.md,
  ]
---

> **🔒 NOT a clean auto-archive candidate (flagged 2026-07-24, plan-reconcile audit)** — do not archive this doc, do not
> change its `locked_by:`, and do not run an `[unlock-plan]` step against it without an explicit operator ruling. Two
> reasons: (1) frontmatter `locked_by: live-defi-rollout` (`locked_since: 2026-06-20`) contradicts the "unlocked"
> premise a prior archive-check assumed; (2) as of 2026-07-24 the "Gap analysis from P1c Todo 4" section's four
> follow-ups are now tracked as todos under "P1 — gap-analysis follow-ups" near the end of this doc (previously orphaned
> prose, now checkbox-tracked) and remain OPEN / unaddressed — plus a flagged regression-test-deletion discrepancy on
> Todo 2/Todo 3 below (P0 section) that also needs an operator call before those checkboxes can be trusted at face
> value. See `plans/active/issues/sports_plan_and_docs_reconcile_findings_2026_07_24.md` for the full audit findings.

> **⚠️ SCOPE OVERLAP — read `sports_consolidated_closeout_2026_07_19.md` before acting on any league_id work in this
> doc** (flagged 2026-07-23, orphan-plan reconciliation audit): this plan's own text (see "Input from P1c golden-window
> audit" and "Gap analysis from P1c Todo 4" below) labels raw manifest strings like `PREMIER_LEAGUE`, `BUNDESLIGA`,
> `SERIE_A`, `LA_LIGA` as the "canonical namespace" — this is the OPPOSITE of the closeout's registry-resolution target,
> which treats those raw manifest strings as NON-canonical and the UAC registry form (e.g. `EPL`) as canonical. This
> plan's own open gap-analysis follow-ups (a `LEAGUE_ID_TO_TIER` / league-tier mapping, the 28 unmapped league_ids) also
> overlap the closeout's unresolved league_id migration work (Track C / Track V /
> `issues/sports_league_id_namespace_migration_2026_07_20.md`). **Do not resolve this conflict unilaterally from this
> doc** — check the closeout's current Track sections (Track C, Track V) for the latest state before acting on either
> doc.
>
> **MERGED 2026-07-27** (`/plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md` todo 2): the convention
> conflict this banner flags is already decided elsewhere in the closeout (UAC registry form is canonical) — this todo
> only propagates that, it does not re-litigate it. This plan's `LEAGUE_ID_TO_TIER` mapping + 28-unmapped-league_id gap
> analysis (the P1 todos below) are now also tracked in `issues/sports_league_id_namespace_migration_2026_07_20.md` §
> "MERGED TRACKING 2026-07-27" — that section is the single settled location cross-referenced from Track V; this plan's
> own P1 todos below remain the execution home (not duplicated, not moved). See that section's "Vocabulary flag" for why
> this plan's "canonical namespace" label (below) is scoped to this plan's own golden-window audit only.

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

- [x] ✅ [AGENT] P1. Empirical audit per league tier: which bookmakers + markets are expected to be present per
      (fixture, league_tier)? Output: UAC
      `EXPECTED_BOOKMAKER_MARKET_SETS: dict[LeagueTier, dict[BookmakerKey, list[MarketType]]]`. League tiers:
      TIER_1_DOMESTIC (EPL/LaLiga/SerieA/Bundesliga/Ligue1), TIER_2_DOMESTIC, TIER_1_INTERNATIONAL (UCL/UEL), etc.
      Empirical baseline: 2-week sample of fully-covered fixtures per tier. Repo: unified-api-contracts. —
      unified-api-contracts@702478cb | 5 new tests (test_honest_coverage.py) | 3 tiers defined: tier_1_domestic
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

> **⚠️ Regression-test discrepancy flagged 2026-07-24** (plan-reconcile audit; NOT auto-corrected — needs operator
> judgment, checkboxes intentionally left as-is): Todo 2's cited `TestFootystatsOddsNanFill` (4 tests, added
> instruments-service@33c0796c) and Todo 3's cited `SP-10-ODDS regression guard` (added instruments-service@e1a3988b)
> were BOTH deleted from `tests/unit/test_orchestrator_sports.py` by instruments-service@6404abd6 ("feat(sports): #6
> ODDS=MTDS removal — remove footystats odds fetch from IS orchestrator", 2026-06-25). When the ODDS fetch path was
> later restored by instruments-service@3d4f1a19 ("feat: restore footystats ODDS capture path (operator reversal
> 2026-06-27)"), it added back `TestFetchFootystatsOdds` / `TestLoadScheduledFootystatsFixtureMap` but NOT
> `TestFootystatsOddsNanFill` or the SP-10-ODDS test under the same or an equivalent name — confirmed absent from
> `tests/unit/test_orchestrator_sports.py` as of 2026-07-24 (`grep` for both markers returns zero hits). The underlying
> FUNCTIONALITY did survive: the "FootyStats odds NaN-fill" logic and the `expected_root_clusters=` cluster-validation
> kwargs are still present in current `instruments_service/engine/orchestrator/footystats.py` — only the dedicated
> regression-test coverage is gone. The one adjacent test that does exist,
> `tests/unit/test_footystats_odds_kickoff_serialization.py`, covers a narrower `kickoff_utc` string-serialization bug
> fix, not a restoration of the original 4-test class or the cluster-validation regression. A human should decide
> whether to (a) restore equivalent regression tests under the original names/scope, or (b) accept current coverage and
> update the citations — do NOT flip Todo 2 / Todo 3 back to `- [ ]` without that decision.

> **Already shipped (downstream consumer guidance) — flipped in the epic, NOT re-opened here**: features-sports
> arbitrage/odds-movement NaN-row handling + the `/codex/02-data/honest-absence-downstream-handling.md` § "ODDS NaN-fill
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

51 distinct league_ids observed in MTDS golden window (2025-09-01..2025-11-30, odds_api source, 18,194 captured trades
rows). Two naming conventions present (SOCCER_* and canonical). P1 empirical audit should cover at minimum these
league-tiers:

*_SOCCER__ namespace (odds_api native names)**: SOCCER_EPL, SOCCER_GERMANY_BUNDESLIGA, SOCCER_ITALY_SERIE_A,
SOCCER_SPAIN_LA_LIGA, SOCCER_FRANCE_LIGUE_ONE, SOCCER_NETHERLANDS_EREDIVISIE, SOCCER_PORTUGAL_PRIMEIRA_LIGA,
SOCCER_BELGIUM_FIRST_DIV, SOCCER_TURKEY_SUPER_LEAGUE, SOCCER_DENMARK_SUPERLIGA, SOCCER_SWITZERLAND_SUPERLEAGUE,
SOCCER_AUSTRIA_BUNDESLIGA, SOCCER_UEFA_CHAMPS_LEAGUE, SOCCER_CHINA_SUPERLEAGUE, SOCCER_RUSSIA_PREMIER_LEAGUE,
SOCCER_ARGENTINA_PRIMERA_DIVISION, SOCCER_AUSTRALIA_ALEAGUE, SOCCER_GREECE_SUPER_LEAGUE, SOCCER_JAPAN_J_LEAGUE,
SOCCER_KOREA_KLEAGUE1, SOCCER_MEXICO_LIGAMX, SOCCER_NORWAY_ELITESERIEN, SOCCER_POLAND_EKSTRAKLASA,
SOCCER_SWEDEN_ALLSVENSKAN, SOCCER_USA_MLS

**"Canonical namespace" (27 more) — ⚠️ this plan's own golden-window-audit label only, NOT this closeout's canonical
form** (flagged 2026-07-23, merged into the single settled location 2026-07-27 — see the SCOPE OVERLAP banner +
`issues/sports_league_id_namespace_migration_2026_07_20.md` § "MERGED TRACKING 2026-07-27"; the closeout's actual
canonical form is the UAC `LEAGUE_REGISTRY` slug, e.g. `EPL`, not these raw display strings): PREMIER_LEAGUE,
BUNDESLIGA, SERIE_A, LA_LIGA, LIGUE_1, CHAMPIONSHIP, PRIMERA_DIVISION, SEGUNDA_DIVISION, SERIE_B, LIGUE_2, SUPERLIGA,
SUPER_LIG, SUPER_LEAGUE, EREDIVISIE, EKSTRAKLASA, ELITESERIEN, ALLSVENSKAN, PREMIERSHIP, FIRST_DIVISION_A,
2._BUNDESLIGA, A-LEAGUE, J1_LEAGUE, K_LEAGUE_1, MLS, LIGA_MX, PRIMEIRA_LIGA

**Additional blocker noted**: `fixture_id=NULL` for all golden window trades rows — the P1 audit must also confirm that
fixture IDs are propagated to odds rows before per-fixture cluster validation (gate of P1c Todo 4) can proceed.

## Gap analysis from P1c Todo 4 cluster validation — 2026-06-27 (slot-4)

Static cluster validation performed against `sports_bookmaker_league_coverage.json` (27 bookmakers × 51 leagues).

**Coverage mapping result (23 mapped / 51 total)**:

- `tier_1_domestic` (10 leagues): BUNDESLIGA, LA_LIGA, LIGUE_1, PREMIER_LEAGUE, SERIE_A, SOCCER_EPL,
  SOCCER_FRANCE_LIGUE_ONE, SOCCER_GERMANY_BUNDESLIGA, SOCCER_ITALY_SERIE_A, SOCCER_SPAIN_LA_LIGA — expected bookmakers
  (pinnacle, betfair_ex_uk, williamhill, unibet_uk) ALL PRESENT ✅
- `tier_1_international` (1 league): SOCCER_UEFA_CHAMPS_LEAGUE — expected bookmakers (pinnacle, betfair_ex_uk,
  williamhill) ALL PRESENT ✅
- `tier_2_domestic` (12 leagues): 2._BUNDESLIGA, CHAMPIONSHIP, EREDIVISIE, FIRST_DIVISION_A, LIGUE_2, PRIMEIRA_LIGA,
  PRIMERA_DIVISION, SEGUNDA_DIVISION, SERIE_B, SOCCER_BELGIUM_FIRST_DIV, SOCCER_NETHERLANDS_EREDIVISIE,
  SOCCER_PORTUGAL_PRIMEIRA_LIGA — expected bookmakers (pinnacle, betfair_ex_uk) ALL PRESENT ✅

**28 league_ids with NO tier definition in `EXPECTED_BOOKMAKER_MARKET_SETS` (GAPS TO FILE)**: A-LEAGUE, ALLSVENSKAN,
EKSTRAKLASA, ELITESERIEN, J1_LEAGUE, K_LEAGUE_1, LIGA_MX, MLS, PREMIERSHIP, SOCCER_ARGENTINA_PRIMERA_DIVISION,
SOCCER_AUSTRALIA_ALEAGUE, SOCCER_AUSTRIA_BUNDESLIGA, SOCCER_CHINA_SUPERLEAGUE, SOCCER_DENMARK_SUPERLIGA,
SOCCER_GREECE_SUPER_LEAGUE, SOCCER_JAPAN_J_LEAGUE, SOCCER_KOREA_KLEAGUE1, SOCCER_MEXICO_LIGAMX,
SOCCER_NORWAY_ELITESERIEN, SOCCER_POLAND_EKSTRAKLASA, SOCCER_RUSSIA_PREMIER_LEAGUE, SOCCER_SWEDEN_ALLSVENSKAN,
SOCCER_SWITZERLAND_SUPERLEAGUE, SOCCER_TURKEY_SUPER_LEAGUE, SOCCER_USA_MLS, SUPERLIGA, SUPER_LEAGUE, SUPER_LIG

**Required follow-up actions (for empirical P1 audit to enable P1c gate)**:

1. Add a `LEAGUE_ID_TO_TIER` mapping function (or direct dict) to UAC that routes each of the 51 observed league_ids to
   a LeagueTier key in `EXPECTED_BOOKMAKER_MARKET_SETS` — without it, runtime cluster validation code cannot determine
   which expected bookmaker set applies to a given manifest row.
2. Extend `EXPECTED_BOOKMAKER_MARKET_SETS` to cover the 28 unmapped league_ids above (or add a `tier_3_global` /
   `no_expectation` tier for non-EU leagues that the empirical audit determines have inconsistent bookmaker coverage).
3. Fix `fixture_id=NULL` propagation in the odds_api backfill path — golden window `trades` data has all fixture_ids as
   NULL, preventing per-fixture cluster validation.
4. Note: `data_type=trades` is NOT in `BUNDLED_DATA_TYPES` (see `_honest_coverage_clusters.py`) — cluster validation at
   `record_captured` does not fire for historical `trades` data; only `odds_snapshot`, `odds_movement`,
   `arbitrage_opportunity` are enforced. The validation gate for `trades` relies on this static audit path.

## P1 — gap-analysis follow-ups (tracked 2026-07-24)

> **Scope-overlap caveat**: these four todos formalize the "Required follow-up actions" prose in the Gap Analysis
> section above (P1c Todo 4 cluster validation, 2026-06-27) — no new technical detail invented, just made
> checkbox-tracked. Per the SCOPE OVERLAP banner near the top of this doc, the league_id-mapping todos below (1-2)
> overlap `sports_consolidated_closeout_2026_07_19.md` Track C / Track V — check that doc's current Track state before
> executing them, since it may already own this work or resolve the canonical-namespace question differently.
>
> **Merged 2026-07-27**: todos 1-2's mapping + gap list are cross-tracked (not duplicated) in
> `issues/sports_league_id_namespace_migration_2026_07_20.md` § "MERGED TRACKING 2026-07-27" — the single settled
> location Track V now cites. Execute here as before; that section is visibility only.

- [x] ✅ [SCRIPT] P1. **Add a `LEAGUE_ID_TO_TIER` mapping (function or dict) to UAC that routes each of the 51 observed
      league_ids to a `LeagueTier` key in `EXPECTED_BOOKMAKER_MARKET_SETS`** — without it, runtime cluster-validation
      code cannot determine which expected bookmaker set applies to a given manifest row. **DONE** —
      unified-api-contracts@53f2e48f. Added LEAGUE_ID_TO_TIER dict mapping 23 league_ids that cleanly fit the existing 3
      tiers (tier_1_domestic, tier_1_international, tier_2_domestic). Both naming conventions included (odds_api
      SOCCER_* prefix + canonical slugs). 28 non-EU leagues left unmapped per next todo. Quality gates green.
- [ ] [AGENT] P1. **Extend `EXPECTED_BOOKMAKER_MARKET_SETS` to cover the 28 unmapped league_ids** (A-LEAGUE,
      ALLSVENSKAN, EKSTRAKLASA, ELITESERIEN, J1_LEAGUE, K_LEAGUE_1, LIGA_MX, MLS, PREMIERSHIP,
      SOCCER_ARGENTINA_PRIMERA_DIVISION, SOCCER_AUSTRALIA_ALEAGUE, SOCCER_AUSTRIA_BUNDESLIGA, SOCCER_CHINA_SUPERLEAGUE,
      SOCCER_DENMARK_SUPERLIGA, SOCCER_GREECE_SUPER_LEAGUE, SOCCER_JAPAN_J_LEAGUE, SOCCER_KOREA_KLEAGUE1,
      SOCCER_MEXICO_LIGAMX, SOCCER_NORWAY_ELITESERIEN, SOCCER_POLAND_EKSTRAKLASA, SOCCER_RUSSIA_PREMIER_LEAGUE,
      SOCCER_SWEDEN_ALLSVENSKAN, SOCCER_SWITZERLAND_SUPERLEAGUE, SOCCER_TURKEY_SUPER_LEAGUE, SOCCER_USA_MLS, SUPERLIGA,
      SUPER_LEAGUE, SUPER_LIG) — or add a `tier_3_global` / `no_expectation` tier for non-EU leagues the empirical audit
      determines have inconsistent bookmaker coverage.
- [x] ✅ [SCRIPT] P0. **Fix `fixture_id=NULL` propagation in the odds_api backfill path** — golden window `trades` data
      has all fixture_ids as NULL, which blocks per-fixture cluster validation entirely (this is the P1c Todo 4 gate
      blocker). **DONE (na-eligibility-audit 2026-08-03)** — `sports_satellite_ao_dispatch_batch2_2026_07_24.md:344`:
      `market-tick-data-service@3401c0ab` (slot 7, 2026-07-25). Confirmed ownership is market-tick-data-service, not
      instruments-service; root cause was `_build_fixture_rows()` never emitting a key literally named `fixture_id`
      (only `af_fixture_id`), so `venue_fetch.py`'s shard-grouping normalisation forced it to `""` for every row,
      collapsing odds_api into league-level shards. Fixed by also emitting `fixture_id` alongside `af_fixture_id`; 6/6
      tests pass (`test_odds_api_fixture_id_join.py` extended), `quality-gates.sh --no-fix` green.
- [ ] [AGENT] P2. **Decide + implement the `trades` cluster-validation gap**: `data_type=trades` is not in
      `BUNDLED_DATA_TYPES` (see `_honest_coverage_clusters.py`), so cluster validation at `record_captured` does not
      fire for historical `trades` data — only `odds_snapshot`, `odds_movement`, `arbitrage_opportunity` are enforced.
      Either register `trades` in `BUNDLED_DATA_TYPES` for live enforcement, or formally accept that the validation gate
      for `trades` relies on this static audit path instead.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — carries a 🔒 'NOT a clean auto-archive
  candidate' banner explicitly forbidding an `[unlock-plan]` without an operator ruling, `locked_by: live-defi-rollout`,
  and a flagged regression-test-deletion discrepancy on todos 2/3 that 'needs an operator call before those checkboxes
  can be trusted at face value'
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — was thin/codex-only; added the source file both
  remaining open todos actually touch (`_honest_coverage_clusters.py`), the merged league_id-tracking issue, and the
  regression-test-discrepancy audit the 🔒 banner says to check before trusting todos 2/3.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — re-verified live: the 🔒
  `locked_by: live-defi-rollout` lock + its explicit "do not archive, do not unlock without an operator ruling" banner
  are both still present, unchanged. No 2026-08-08 operator ruling touches this doc's 2 open todos (extend
  `EXPECTED_BOOKMAKER_MARKET_SETS` to 28 unmapped league_ids OR add a `tier_3_global` tier; decide+implement the
  `trades` cluster-validation gap) — both remain genuine either/or design forks with no evidence-based tiebreaker, per
  every prior pass's reasoning, and neither matches any of today's cheat-sheet precedents (not an IAM/permission issue,
  not a script-flag-parity gap, not a reversibility-qualified delete). Doc stays NA, unchanged.

- **round11 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA, valid — re-confirmed via
  `plans/active/issues/ag_closeout_audit_sports_parked_2026_08_09.md`'s "Parked — operator-gated" entry (today): the
  same 2 genuine either/or design forks remain (extend `EXPECTED_BOOKMAKER_MARKET_SETS` vs. a `tier_3_global` tier;
  restore deleted regression tests vs. accept current coverage), plus the standing `locked_by: live-defi-rollout` +
  do-not-archive-without-ruling banner. No evidence-based tiebreaker exists. No flip.
