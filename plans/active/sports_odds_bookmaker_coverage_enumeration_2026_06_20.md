---
title: "Sports ODDS bookmaker × market coverage enumeration + NaN-fill + cluster validation"
parent_epic: sports_master
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: brand-new
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3
locked_by: live-defi-rollout
locked_since: 2026-06-20
related_plans:
  - ../epics/sports_master.md
  - ./sports_manifest_canonicalisation_2026_06_01.md
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

- [ ] [AGENT] P1. Empirical audit per league tier: which bookmakers + markets are expected to be present per (fixture,
      league_tier)? Output: UAC
      `EXPECTED_BOOKMAKER_MARKET_SETS: dict[LeagueTier, dict[BookmakerKey, list[MarketType]]]`. League tiers:
      TIER_1_DOMESTIC (EPL/LaLiga/SerieA/Bundesliga/Ligue1), TIER_2_DOMESTIC, TIER_1_INTERNATIONAL (UCL/UEL), etc.
      Empirical baseline: 2-week sample of fully-covered fixtures per tier. Repo: unified-api-contracts.
- [ ] [SCRIPT] P0. Orchestrator post-FIXTURES_SCHEDULE-capture step: for each fixture today, enumerate expected
      `(fixture × bookmaker × market)` triples per `EXPECTED_BOOKMAKER_MARKET_SETS[tier]`; for each missing triple,
      write a NaN-fill row with `record_captured` (NaN values per workspace honest-absence rule, NOT `record_empty` —
      `record_empty` is for legitimately-absent source responses; NaN-fill is for "we expected this triple but the
      source didn't return it"). Repo: instruments-service (sports orchestrator).
- [ ] [SCRIPT] P0. Cluster-validation kwargs at `record_captured` for ODDS bundled writes:
      `expected_root_clusters = {fixture_id: len(EXPECTED_BOOKMAKER_MARKET_SETS[tier])}` per Phase 1A of writegate (per
      CLAUDE.md "Cluster validation MANDATORY at record_captured for bundled data_types"). Repo: instruments-service.

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
