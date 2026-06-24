---
title: Sports fixture-completeness oracle — the depth_coverage Tier-B denominator for sports
created: 2026-06-24
parent_epic: sports_master
assigned_vm: planning
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
locked_by: live-defi-rollout
status: active
priority: P2
---

> **Operator directive 2026-06-24:** "Fixtures are really where we can nail down all these details, because if we get
> them wrong there, they're just going to be wrong later." For sports, **fixtures ARE the instruments** — and unlike
> cefi/defi we cannot run `_enforce_defi_monotonicity` on daily fixtures, but we CAN validate captured fixtures against
> **known per-league season structure** (external truth). This is the sports realisation of the codex §2.1
> expected-universe ORACLE (`instruments-foundation-and-catalogue-completeness.md` — the Tier-B "did we get everything"
> denominator). It is a **first-class G2 deliverable**, not a footnote: a league/season is not "complete" until this is
> green.

## Why
`depth_coverage` (captured / expected) is only as honest as the EXPECTED denominator. For sports, the expected fixture
set per (league, season) is **external truth** (the league's known structure), NOT our own capture (using
first-seen-in-our-data is circular — if we missed fixtures, our denominator hides the gap). Get fixtures right and
everything downstream (xG/odds/stats enrichment, MTDS capture, features) is anchored; get them wrong and every later
layer inherits the error.

## The season-structure REGISTRY (external truth, lives in UAC alongside `league_data.py` / `season_dates.py`)
Per (league_id, season), versioned by effective season (rules change over time):
- `n_teams` — e.g. EPL 20, Bundesliga 18, Championship 24, Eredivisie 18, MLS (per conference), Liga MX (apertura/clausura).
- `format` — `double_round_robin` | `split` (Scottish Prem 38) | `conference` (MLS) | `apertura_clausura` (Liga MX) | …
- `expected_fixtures` — DERIVED from format: double round-robin = `n_teams × (n_teams − 1)` (20→380, 18→306, 24→552);
  + format-specific adjustments (splits, group stages).
- `season_window` — (start_date, end_date) per league. **Partially EXISTS**: `season_dates.py`
  `get_season_window/get_season_start/get_season_end` + `_is_in_season` + `footystats_season_status_for_day` (off-season
  signal the off-season-guard agent already uses). Extend to authoritative per-league start/end.
- `expected_breaks` — the gaps that are OK: winter break (Bundesliga mid-Dec→mid-Jan), international breaks, mid-season /
  end-of-season splits. An UNEXPLAINED gap (not a break) = a capture gap to flag.
- `promotion_relegation` — extra fixtures: Championship playoffs (+3), relegation playoffs, etc.

## The VALIDATOR (instruments-service, a G2 completeness check over the captured fixtures catalogue)
Per (league, season), assert against the registry:
1. **Fixture count** — captured distinct fixtures == `expected_fixtures` (± playoffs). A shortfall = missing fixtures
   (capture gap); an excess = duplicates / wrong-league leakage.
2. **Team count** — distinct teams == `n_teams`. And **each team plays the expected number of games** (`(n_teams−1)×2`
   home+away for double round-robin) — catches a team with missing fixtures even when the total is right.
3. **Promotion / relegation** — account for the known extra playoff fixtures (don't false-flag them as excess).
4. **Season window + gaps** — captured fixtures' first/last dates ≈ `season_window`; every gap in the fixture calendar
   maps to an `expected_break` (transfer window / off-season / mid-season). An unexplained gap, or a season start/end
   materially off the expected window per league, = a defect to flag.
5. **Reschedule correctness (HARD)** — when a fixture is rescheduled/postponed, the catalogue records the **FINAL
   scheduled kickoff time**, not the initial. The "available fixture start time" that everything downstream keys off
   (odds horizon buckets, enrichment windows) is the **current** scheduled time; capturing the original time for a moved
   match is a correctness bug.

## Composes with (don't reinvent)
- `season_dates.py` (season windows — extend, don't duplicate) · `footystats_season_status_for_day` (off-season) ·
  `is_league_entity_covered` (per-SOURCE coverage subset — orthogonal: this oracle is the FIXTURE truth; coverage is
  which sources enrich which leagues) · `SOURCE_COVERAGE_START` (genesis) · the MVP ~94-league universe (scope the
  oracle to MVP first) · codex §2.1 (the registry lives in UAC so MTDS / catalogue roll-up / coverage all read the same
  truth — no per-consumer re-derivation).

## Phases (DAG)
- [ ] [DESIGN] P1. Season-structure registry schema in UAC (per league_id × season: n_teams, format, expected_fixtures,
  window, breaks, promotion_relegation). Seed the MVP ~94 leagues from api_football league/season metadata
  (teams + rounds) as the ground truth, reconciled against known structure.
- [ ] [CODE] P1. Fixture-completeness validator in instruments-service (the 5 checks) — reads the captured fixtures
  catalogue + the registry; emits a per-(league,season) completeness report + typed defects (MISSING_FIXTURES,
  TEAM_COUNT_MISMATCH, UNEXPECTED_GAP, SEASON_WINDOW_DRIFT, RESCHEDULE_STALE_TIME).
- [ ] [CODE] P1. Reschedule rule: confirm the fixtures writer records the FINAL kickoff (current scheduled time) and the
  catalogue/manifest available_at reflects it; add a guard/test that a postponed fixture is keyed to its new time.
- [ ] [CODE] P2. Wire the validator into the sports `depth_coverage` denominator (codex §2.1 Tier-B) so the deployment-UI
  shows the real "did we get every fixture the league played" number per (league, season), not a proxy.
- [ ] [INFRA] P2. Run it over the golden window + the 2014→2026 backfill; every league/season shortfall becomes a
  targeted fixture re-fetch (not a blanket re-run).

## Notes
- This is the sports analog of the cefi futures expiry-schedule oracle (codex §2.1.2) — both are "encode the external
  listing/structure truth, versioned by effective date, so any historical day is honestly scored."
- Scope MVP-first (~94 leagues), then expand. Lower divisions / cups have irregular structure — handle via `format`.
