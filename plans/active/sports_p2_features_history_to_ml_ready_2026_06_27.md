---
doc_type: plan
title: "Sports P2c — derived features history to ML-ready (2015→present)"
summary:
  "Compute derived sports features over full history (2015→present) to ML-ready after upstream history reaches
  zero-missing."
nature: process
stage: [feature-eng]
repos: []
scope: [engineer, admin]
tags: [sports, features, history, ml-ready, feature-engineering, 2015-present]
related: []
created: 2026-06-27
parent_epic: sports_master
priority: P1
status: active
assigned_vm: planning
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-27
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on:
  - sports_p0_spot_vm_launchers_2026_06_27
  - sports_p2_history_apifootball_2015_to_present_2026_06_27
  - sports_p2_history_reference_and_odds_2015_to_present_2026_06_27
related_plans:
  - plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md
  - plans/active/sports_features_readiness_for_predictions_2026_06_20.md
asset_group: cross-asset
---

> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 2). Computes the **derived
> features** (R2) over full history to ML-ready, AFTER the upstream history is zero-missing (P2a+P2b). One agent,
> `data_engineering` (Sonnet/high). Same recipe proved in P1d, generalized to 2015→present.

# Sports P2c — derived features history to ML-ready

## Scope

Compute the three feature groups over 2015→present where upstream exists; pre-source-coverage cells inherit honest
absence (the feature coverage gate propagates the upstream `EXPECTED_*`):

- `fixture_features` — from 2015 fixtures (full FIXTURES history); enrichment-derived features only from 2020-06.
- `derived_features` — within footystats/understat/SFI/transfermarkt/weather coverage windows.
- `odds_features` — within odds-api coverage (2020-06→present), bookmaker-league subset.

ML-ready = one row per `(fixture × bucket)`; NaN only where honest-absence (`OUT_OF_COVERAGE`/`UPSTREAM_MISSING`).

> **SPOT VMs (HARD)** — launch every VM in this plan as **spot/preemptible** (the cloud can reclaim + kill it at any
> moment) per [`sports_p0_spot_vm_launchers_2026_06_27`](sports_p0_spot_vm_launchers_2026_06_27.md); the features VMs
> default to SPOT. Compute is idempotent/skip-existing, so a reclaimed VM relaunches + resumes — and a preemption must
> NOT raise a false `DP_VM_GONE_NO_CAPTURE` (R5).

## Codex SSOTs

- `codex/02-data/feature-formula-versioning.md` — sports feature versioning
- `codex/02-data/availability-manifest-and-data-status.md` — features share the 4-state manifest
- `codex/02-data/honest-absence-downstream-handling.md` — NaN classification propagates upstream `EXPECTED_*`

## Mechanics

- `python3 -m features_service.sports --operation compute --mode batch --asset-group SPORTS --start-date <Y>-01-01 --end-date <Y>-12-31 --skip-existing`
  (year-chunked, resumable); or `launch-features-sports-parallel-backfill-vm.sh`.
- `features-service/scripts/sports/check_pipeline_completeness.py` to verify per-range.
- Asserts upstream manifest health first → P2a/P2b must be GREEN (the `depends_on` edge).

## Todos

- [ ] [DATA] P0. **Compute features 2015→present** (year-chunked, skip-existing) for all three groups within their
      coverage windows. **Gate**: `sports_features/by_date/day=*/feature_group=*/features.parquet` exists for every
      in-coverage day with fixtures; features manifest `captured`; runs `exit_code=0`.
- [ ] [VERIFY] P0. **ML-ready over history.** **Gate**: `check_pipeline_completeness.py` per era → ≥95% non-NULL on
      in-coverage cells; every NaN traces to a typed upstream honest-absence (sampled proof across eras 2015-2019 /
      2020-2023 / 2024-present).
- [ ] [DATA] P1. **Features manifest clean over history** — 0 blank-reason, 0 un-evidenced failed. **Gate**:
      full-history features-manifest query mirrors the IS/MTDS cleanliness.

**Full-execution criterion**:

- ✅ The sports feature matrix is ML-ready across 2015→present within coverage windows, manifest-verified.
  - **What ran**: year-chunked sports FSS compute against `features-sports-prd-central-element-323112`.
  - **Verification**: `check_pipeline_completeness.py` per-era output (non-NULL %, NaN→honest-absence trace) in the
    Progress Log.

## Success criteria

- Features computed + ML-ready across all in-coverage history; NaN only honest-absence; features manifest clean.

## Dependencies

- **Upstream (prereq)**: P2a, P2b (upstream history zero-missing).
- **Feeds**: P2d (final gate).

## References

- `sports_features_readiness_for_predictions_2026_06_20.md` — FSS-run items (absorbed)

## Progress Log

### 2026-06-27 — slot 4

**Todo 2 (ML-ready verify)**: BLOCKED-PREREQ (BLK-497e5765)
- P2a (`sports_p2_history_apifootball_2015_to_present_2026_06_27`): 0 of 6 todos complete. Upstream api-football history not yet zero-missing.
- P2b (`sports_p2_history_reference_and_odds_2015_to_present_2026_06_27`): 0 of 7 todos complete. Reference + odds history not zero-missing.
- `check_pipeline_completeness.py` cannot be run. Features Todo 1 (compute features 2015→present) also blocked on P2a+P2b.
- Checkbox NOT flipped. Both upstream plans must reach 100% before feature compute + ML-ready verify can proceed.
