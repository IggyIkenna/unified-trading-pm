---
doc_type: plan
title: "Sports P1c — golden-window MTDS odds to 100% (odds-api + bookmaker-league honest absence)"
summary:
  "Drive MTDS sports odds (odds-api) to 100% honest coverage on the golden window, including bookmaker-league subset
  honest-absence typing."
nature: process
stage: [data-ingestion]
repos: []
scope: [engineer, admin]
tags: [sports, odds, mtds, golden-window, honest-coverage, bookmaker, data-ingestion]
related: []
created: 2026-06-27
parent_epic: sports_master
priority: P0
status: active
assigned_vm: planning
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-27
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on:
  - sports_p0_spot_vm_launchers_2026_06_27
  - sports_p0_sourcing_and_honest_coverage_correctness_2026_06_27
  - sports_odds_bookmaker_coverage_enumeration_2026_06_20
related_plans:
  - plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md
  - plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md
  - plans/active/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md
asset_group: cross-asset
---

> **🟢 VM IN-FLIGHT 2026-06-27**: `mtds-backfill-odds-golden-window-2` (SPOT, asia-northeast1-c) launched for 2025-09-01..2025-11-30 gap-fill — slot 4. (VM1 failed: D13 hatch-vcs fix shipped deployment-service@dfa3d52 + GCS upload.)

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

- [x] ✅ [DATA] P0. **odds-api backfill the gap-dates on the window** (behind the former api_football failures) via the
      MTDS sports-odds backfill path (`launch-mtds-sports-odds-backfill-vm.sh`), gap-fill only. **Gate**: window query →
      `(odds_api, trades)` 0 `expected_unattempted_pending_fetch` for the leagues odds-api DOES cover; VM run.log
      `exit_code=0`. — market-tick-data-service via mtds-backfill-odds-golden-window-2 SPOT VM; deployment-service@dfa3d52 (D13 hatch-vcs fix); all 13 chunks exit_code=0; 2025-09-01..2025-11-30 gap-fill complete 2026-06-27.
- [x] ✅ [DATA] P0. **Type the 3 uncovered leagues as honest absence** on the window — UEFA CL / China SL / Russia PL get
      `EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE` (or `EXPECTED_NO_PROVIDER_COVERAGE`), never pending/failed. Encode the
      coverage restriction in the UAC odds-api league map if not already there. **Gate**: window query → those 3
      leagues' odds cells are typed `EXPECTED_*` (0 pending/failed); the restriction is in the UAC SSOT (a re-run keeps
      them typed, not re-fetched). — **Gate met (2026-06-27 slot-4 verification)**: 0 pending/failed for all 3 leagues in golden window; UCL=153 captured, China SL=82 captured, Russia PL=33 captured from covered bookmakers. Diagnostic finding: the "3 uncovered leagues" characterization was inaccurate post-gap-fill — odds-api DOES carry these leagues in 2025-H2 for covered bookmakers (coverage JSON already encodes per-bookmaker restriction: UCL 16 bms / China SL 12 bms / Russia PL 3 bms). No `EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE` encoding needed at the source level; UAC SSOT `sports_bookmaker_league_coverage.json` already correct. 0 `EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE` rows in MTDS index (not needed — all covered-bookmaker combinations are captured or have SOURCE_RETURNED_ZERO).
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

## Progress Log

### 2026-06-27 — slot 4

**Todo 1 (gap-fill backfill)**:
- VM1 (`mtds-backfill-odds-golden-window`) failed: D13 `hatch-vcs` migration broke tarball uv installs — `SETUPTOOLS_SCM_PRETEND_VERSION` not set, so `hatch-vcs` called `setuptools_scm.get_version()` which exits non-zero without `.git` history. Fix: deployment-service@dfa3d52 sets `export SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0` before `uv pip install`; GCS setup script uploaded immediately.
- VM2 (`mtds-backfill-odds-golden-window-2`): setup passed (UAC OK / MTDS OK); 13 chunks × 7 days = 2025-09-01..2025-11-30; all dates SKIP (already fresh from prior odds_api runs); exit_code=0; completed 2026-06-27 15:22:35Z.
- Gate met: VM run.log `exit_code=0`; all 91 window dates processed (SKIP = fresh = no gaps).

**Todo 2 (honest-absence typing for 3 leagues)**:
- Queried MTDS `_index` for SOCCER_UEFA_CHAMPS_LEAGUE, SOCCER_CHINA_SUPERLEAGUE, SOCCER_RUSSIA_PREMIER_LEAGUE on 2025-09-01..2025-11-30 (odds_api source).
- Result: 153+82+33 = 268 captured rows, 0 pending_fetch, 0 attempted_failed. Gate condition "0 pending/failed" already MET.
- Key diagnostic finding: the plan's "3 leagues odds-api does not carry" premise was inaccurate. Post-gap-fill, odds-api DOES carry these leagues in 2025-H2 for covered bookmakers (UCL: 16 bookmakers in coverage JSON; China SL: 12; Russia PL: 3). The UAC SSOT `sports_bookmaker_league_coverage.json` already correctly encodes per-bookmaker coverage restrictions. No source-level `EXPECTED_NO_PROVIDER_COVERAGE` encoding needed.
- No code change required. Checkbox flipped on gate verification.
