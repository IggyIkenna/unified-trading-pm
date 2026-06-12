---
title: "Sports FSS feature-readiness on bucketed odds dataset (sports half of predictions e2e gate)"
parent_epic: sports_master
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by: live-defi-rollout
locked_since: 2026-06-20
related_plans:
  - ../epics/sports_master.md
  - ../epics/predictions_master.md
---

> **Provenance**: extracted 2026-06-20 from the inline `sports_master` epic body during the asset-group-umbrella
> restructure. Migrated from the epic's "Sports half of `sports_predictions_e2e` — 288M ODDS_API row migration" section
> — specifically the **sports-side feature-readiness remainder** (run FSS on the bucketed dataset, verify the ML-ready
> matrix). The 288M-row migration + MDPS bucketing half already SHIPPED (flipped in the epic, 2026-05-23).
>
> **Scope boundary — do NOT re-extract the predictions ML gate**: the predictions Group-E ML walk-forward gate + the
> ML-training / arb_calculator half are owned by [`predictions_master`](../epics/predictions_master.md). This plan is
> ONLY the sports-side feature-store readiness that the predictions ML half consumes. The `[GATE]` that blocks
> predictions Group E stays in the epic / predictions_master — listed below as a pointer for context, not re-owned here.

## Context

The 288M legacy `venue=ODDS_API` rows are already in canonical MTDS bucketed shape (`odds_horizon_bucket`, 8 horizons
T-24h…T-0) and the MDPS `SportsBucketAssignmentAdapter` backfill ran to 98.7% across 5+ years (the rest honest-empty,
e.g. Sep-Oct 2022 international break) — all flipped in the epic 2026-05-23. What stays OPEN on the sports side is
running features-sports-service (FSS) over that bucketed dataset and verifying the produced feature matrix is ML-ready,
so that predictions ML training (owned in `predictions_master`) has a clean, ≥95%-non-NULL input at its target buckets.

## P0/P1 — FSS run + ML-ready matrix verification

- [ ] [SCRIPT] P1. Run features-sports-service (FSS) on the bucketed dataset — verify odds features populate (velocity,
      CLV, steam, late-money). Repo: features-sports-service. Was BLOCKED-ON the full bucket backfill (now complete per
      epic 2026-05-23 — unblocked).
- [ ] [SCRIPT] P1. Verify the feature matrix is ML-ready: one row per `(fixture × bucket)`, NaN only where
      honest-absence. Repo: features-sports-service.

> **Pointer — predictions ML gate (NOT owned here; owned by `predictions_master`)**: the `[GATE] P0` that blocks
> predictions Group E until FSS produces ≥95% non-NULL features for the trained universe at the buckets predictions ML
> targets is an ACTIVE cross-epic gate. It is satisfied BY the two FSS items above but is asserted/owned on the
> predictions side. Do NOT re-implement the ML walk-forward / arb_calculator here.

## Success criteria

- FSS runs end-to-end on the bucketed odds dataset; odds features (velocity / CLV / steam / late-money) populate.
- The feature matrix is ML-ready (one row per fixture × bucket; NaN only where honest-absence), with ≥95% non-NULL
  features for the trained universe at the predictions-target buckets — clearing the (predictions-owned) Group-E gate.
- `bash scripts/quality-gates.sh` green on `features-sports-service` before commit.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the FSS run executes on the real bucketed
GCS dataset (5+ years), and the produced feature matrix's non-NULL ratio is measured on real rows at the
predictions-target buckets (not a smoke sample) to confirm the ≥95% gate is genuinely met.
