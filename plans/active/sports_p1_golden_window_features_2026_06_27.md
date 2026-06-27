---
title: "Sports P1d — golden-window derived features to ML-ready"
parent_epic: sports_master
priority: P0
status: active
assigned_vm: vm-sports
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
  - sports_p1_golden_window_apifootball_2026_06_27
  - sports_p1_golden_window_reference_sources_2026_06_27
  - sports_p1_golden_window_mtds_odds_2026_06_27
related_plans:
  - plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md
  - plans/active/sports_features_readiness_for_predictions_2026_06_20.md
---

> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 1). Computes the **derived
> features** (R2) on the golden window to ML-ready, AFTER all upstream sources are 100% on the window (P1a+P1b+P1c). One
> agent, `data_engineering` (Sonnet/high). Absorbs the open FSS-run items from
> `sports_features_readiness_for_predictions_2026_06_20.md`.

# Sports P1d — golden-window derived features to ML-ready

## Scope

Run features-service sports over the golden window (**2025-09-01 .. 2025-11-30**) for the three feature groups and
verify the matrix is ML-ready:

- `fixture_features` (`PipelineMode.BATCH_API_FOOTBALL`) — from the P1a fixtures+enrichment
- `derived_features` (`PipelineMode.BATCH_FOOTYSTATS`) — from P1b reference
  (footystats/understat/SFI/transfermarkt/weather)
- `odds_features` (`PipelineMode.BATCH_ODDS_API`) — from the P1c MTDS odds (velocity, CLV, steam, late-money)

ML-ready = one row per `(fixture × bucket)`; NaN ONLY where honest-absence (the `CoverageVerdict.OUT_OF_COVERAGE` /
`UPSTREAM_MISSING` gates), not where upstream simply wasn't computed.

> **SPOT VMs (HARD)** — launch every VM in this plan as **spot/preemptible** (the cloud can reclaim + kill it at any
> moment) per [`sports_p0_spot_vm_launchers_2026_06_27`](sports_p0_spot_vm_launchers_2026_06_27.md); the features VMs
> default to SPOT. Compute is idempotent/skip-existing, so a reclaimed VM relaunches + resumes — and a preemption must
> NOT raise a false `DP_VM_GONE_NO_CAPTURE` (R5).

## Codex SSOTs

- `codex/02-data/feature-formula-versioning.md` — sports feature versioning (`CURRENT_FEATURE_VERSION`)
- `codex/02-data/availability-manifest-and-data-status.md` — features use the SAME 4-state manifest; per-feature
  honest-coverage gate
- `codex/02-data/honest-absence-downstream-handling.md` — NaN classification (`OUT_OF_COVERAGE` vs `UPSTREAM_MISSING`)

## Mechanics

- **Compute**:
  `python3 -m features_service.sports --operation compute --mode batch --asset-group SPORTS --start-date 2025-09-01 --end-date 2025-11-30 [--tables fixture_features,derived_features,odds_features] [--skip-existing]`;
  or the parallel VM `launch-features-sports-parallel-backfill-vm.sh`.
- **Verify**: `features-service/scripts/sports/check_pipeline_completeness.py`.
- Asserts upstream manifest health first (`assert_upstream_manifest_healthy("sports")`) — so the P1a/b/c gates must be
  green before this runs (the `depends_on` edge).

## Todos

- [ ] [DATA] P0. **Compute all three feature groups on the window.** Run the sports FSS compute for
      2025-09-01..2025-11-30 (skip-existing). **Gate**: `sports_features/by_date/day=*/feature_group=*/features.parquet`
      exists for every in-window day with fixtures; the features manifest shows `captured` for those cells; VM/run
      `exit_code=0`.
- [ ] [VERIFY] P0. **Odds features populate** (velocity / CLV / steam / late-money) — these were the explicitly-open FSS
      items in `sports_features_readiness_for_predictions_2026_06_20`. **Gate**: `check_pipeline_completeness.py`
      reports odds_features non-NULL for the odds-api-covered fixtures on the window.
- [ ] [VERIFY] P0. **Matrix is ML-ready.** One row per `(fixture × bucket)`; NaN only where honest-absence (typed
      upstream `EXPECTED_*`), not where a calculator silently skipped. **Gate**: `check_pipeline_completeness.py` → ≥95%
      non-NULL on the in-coverage cells; every NaN traces to a typed upstream honest-absence (sampled proof).
- [ ] [DATA] P1. **Feature manifest clean on the window** — 0 blank-reason empties, 0 un-evidenced `attempted_failed` in
      the features manifest slice. **Gate**: window query on the features manifest mirrors the IS/MTDS cleanliness.

**Full-execution criterion**:

- ✅ The sports feature matrix is ML-ready on 2025-09-01..2025-11-30, manifest-verified.
  - **What ran**: the sports FSS compute on the window (CLI/VM above) against
    `features-sports-prd-central-element-323112`.
  - **Verification**: `check_pipeline_completeness.py` output (non-NULL %, NaN→honest-absence trace) pasted into the
    Progress Log.

## Success criteria

- All three feature groups computed on the window; ML-ready matrix (≥95% non-NULL on in-coverage cells; NaN only
  honest-absence).
- Features manifest is as clean as the upstream IS/MTDS manifests on the window.

## Dependencies

- **Upstream (prereq)**: P1a, P1b, P1c (features assert upstream manifest health).
- **Feeds**: P1e (gate).

## References

- `sports_features_readiness_for_predictions_2026_06_20.md` — the FSS-run items absorbed here (no `assigned_vm` there)
