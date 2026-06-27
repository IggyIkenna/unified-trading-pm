---
title: "Sports P1c — golden-window MTDS odds to 100% (odds-api + bookmaker-league honest absence)"
parent_epic: sports_master
priority: P0
status: active
assigned_vm: planning
assigned_vm: human-planning
assigned_role: data_engineering
drift_direction: advance-code
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on:
  - sports_p0_spot_vm_launchers_2026_06_27
  - sports_p0_sourcing_and_honest_coverage_correctness_2026_06_27
related_plans:
  - plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md
  - plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md
  - plans/active/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md
---

> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 1). Drives **MTDS** sports odds
> (the canonical odds source = **odds-api**, NOT api-football) to 100% honest coverage on the golden window
> (**2025-09-01 .. 2025-11-30**). PREREQ: **P0 shipped** (api-football odds wipe done in #3; IS-ODDS removed in #6 —
> odds lives in MTDS only). One agent, `data_engineering` (Sonnet/high). The bookmaker-league restriction is the
> honest-coverage crux: odds coverage is a strict SUBSET of the 94 leagues.

# Sports P1c — golden-window MTDS odds to 100%

## Scope

MTDS sports odds (`trades` / `odds_horizon_bucket` via `batch_odds_api`) on the golden window. Post-P0, `trades` is
odds-api-only (211,299 captured / 0 failed at the 2026-06-24 measure). The remaining honest-coverage work:

- **3 leagues odds-api does not carry** (`soccer_uefa_champs_league`, `soccer_china_superleague`,
  `soccer_russia_premier_league`, 2025-H2) → these MUST be typed honest-absence (`EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE`
  / `EXPECTED_NO_PROVIDER_COVERAGE`), NOT pending-fetch / failed.
- **Gap-dates** behind the former 112,653 api_football failures → backfill via odds-api (the canonical source).
- **ODDS blank-reason relabel** (~3,062 cells) → `SOURCE_RETURNED_ZERO` or the correct typed reason.
- **`EXPECTED_BOOKMAKER_MARKET_SETS` denominator** — the per-(league_tier, bookmaker, market) expected set that makes
  "which bookmaker×market is expected per fixture" honest (owned by
  `sports_odds_bookmaker_coverage_enumeration_2026_06_20` — reference it; this plan consumes the enumeration to type the
  window's odds cells, and surfaces any league-tier the enumeration is missing back to that plan).

> **SPOT VMs (HARD)** — launch every VM in this plan as **spot/preemptible** (the cloud can reclaim + kill it at any
> moment) per [`sports_p0_spot_vm_launchers_2026_06_27`](sports_p0_spot_vm_launchers_2026_06_27.md); the sports
> launchers default to SPOT. Backfills are idempotent/skip-existing, so a reclaimed VM relaunches + resumes — and a
> preemption must NOT raise a false `DP_VM_GONE_NO_CAPTURE` (R5).

## Codex SSOTs

- `codex/02-data/honest-absence-downstream-handling.md` — bookmaker-league coverage subset = honest absence;
  `EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE`
- `codex/02-data/availability-manifest-and-data-status.md` — sports ODDS cluster validation;
  `expected_unattempted_pending_fetch == 0`
- `codex/02-data/pipeline-mode-partition.md` — `batch_odds_api` source-aware partition

## Todos

- [ ] [DATA] P0. **odds-api backfill the gap-dates on the window** (behind the former api_football failures) via the
      MTDS sports-odds backfill path (`launch-mtds-sports-odds-backfill-vm.sh`), gap-fill only. **Gate**: window query →
      `(odds_api, trades)` 0 `expected_unattempted_pending_fetch` for the leagues odds-api DOES cover; VM run.log
      `exit_code=0`.
- [ ] [DATA] P0. **Type the 3 uncovered leagues as honest absence** on the window — UEFA CL / China SL / Russia PL get
      `EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE` (or `EXPECTED_NO_PROVIDER_COVERAGE`), never pending/failed. Encode the
      coverage restriction in the UAC odds-api league map if not already there. **Gate**: window query → those 3
      leagues' odds cells are typed `EXPECTED_*` (0 pending/failed); the restriction is in the UAC SSOT (a re-run keeps
      them typed, not re-fetched).
- [ ] [DATA] P0. **Relabel the ~3,062 blank-reason ODDS empties** to the correct typed reason on the window. **Gate**:
      window `(odds_api)` `_index` slice has 0 `empty_confirmed` with blank/null `error_reason`.
- [ ] [VERIFY] P0. **Consume `EXPECTED_BOOKMAKER_MARKET_SETS`** to validate the per-fixture odds cluster on the window;
      file any missing league-tier back to `sports_odds_bookmaker_coverage_enumeration_2026_06_20` (do not invent the
      set here — that plan owns the empirical audit). **Gate**: every captured fixture's odds cluster validates against
      the expected bookmaker×market set; gaps in the expected-set map are filed (not silently NaN-filled).

**Full-execution criterion**:

- ✅ MTDS sports odds reads 100% honest coverage on 2025-09-01..2025-11-30 for the odds-api-covered subset of the 94
  universe.
  - **What ran**: the MTDS odds-api gap-fill VM on the window; `read_availability_index` on
    `market-data-tick-sports-prd-central-element-323112`.
  - **Verification**: window query — `pending_fetch=0` for covered leagues, uncovered-league cells typed `EXPECTED_*`,
    `blank_reason=0` — pasted into the Progress Log.

## Success criteria

- 100% honest coverage for odds-api-covered leagues on the window; the bookmaker-league restriction (incl. the 3
  uncovered leagues) is encoded in UAC so it stays honest absence on every re-run.
- 0 blank-reason ODDS empties; per-fixture odds cluster validates against the expected bookmaker×market denominator.

## Dependencies

- **Upstream (prereq)**: P0.
- **Feeds**: P1d (odds_features), P1e (gate). Runs concurrently with P1a, P1b.
- **Coordinates with**: `sports_odds_bookmaker_coverage_enumeration_2026_06_20` (owns `EXPECTED_BOOKMAKER_MARKET_SETS`).

## References

- `issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md` (#3 wipe done, odds-api gap list)
- `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` — the bookmaker×market expected-set audit
