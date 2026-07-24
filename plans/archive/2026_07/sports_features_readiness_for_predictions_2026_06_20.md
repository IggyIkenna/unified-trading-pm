---
doc_type: plan
title: Sports FSS feature-readiness on bucketed odds dataset (sports half of predictions e2e gate)
summary:
  Sports half of the predictions e2e gate -- run features-sports-service over the bucketed ODDS_API dataset
  (odds_horizon_bucket, T-24h..T-0) and prove the feature matrix is ML-ready (one row per fixture x bucket, NaN only on
  honest-absence, >=95% non-NULL at the predictions-target buckets), clearing the Group-E ML gate owned by
  predictions_master.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [features-service]
scope: [engineer, admin]
tags: [sports, features, prediction, odds, ml, data-quality, footystats]
related: [../epics/sports_master.md, ../epics/predictions_master.md]
created: "2026-06-12"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-14
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
drift_direction: advance-code
---

> **✅ ARCHIVED 2026-07-14 [unlock-plan] (operator ruling 2026-07-14, sports plan-set bulk archival — with FORWARD
> pointer).** Both P1 todos `[x]` with cited evidence (features-service@62de3d1d + features-service@9b29b834; status
> flipped complete 2026-07-10). **Successors:** the golden-window FSS-run items were absorbed by
> `sports_p1_golden_window_features_2026_06_27.md` (archived alongside this plan, same ruling), and the FULL-HISTORY
> execution criterion (FSS over the real 5+ year bucketed GCS dataset with the ≥95% non-NULL gate measured on real rows)
> is absorbed and owned by the ACTIVE `plans/archive/2026_07/sports_p2_features_history_to_ml_ready_2026_06_27.md`. Lock
> cleared per the ruling; historical/frozen.

> **Provenance**: extracted 2026-06-20 from the inline `sports_master` epic body during the asset-group-umbrella
> restructure. Migrated from the epic's "Sports half of `sports_predictions_e2e` — 288M ODDS_API row migration" section
> — specifically the **sports-side feature-readiness remainder** (run FSS on the bucketed dataset, verify the ML-ready
> matrix). The 288M-row migration + MDPS bucketing half already SHIPPED (flipped in the epic, 2026-05-23).
>
> **Scope boundary — do NOT re-extract the predictions ML gate**: the predictions Group-E ML walk-forward gate + the
> ML-training / arb_calculator half are owned by [`predictions_master`](../epics/predictions_master.md). This plan is
> ONLY the sports-side feature-store readiness that the predictions ML half consumes. The `[GATE]` that blocks
> predictions Group E stays in the epic / predictions_master — listed below as a pointer for context, not re-owned here.

> **Status-flip note (2026-07-10)**: both P0/P1 todos confirmed `[x]` with cited evidence (FSS run on the bucketed
> dataset + ML-readiness verification, QG green). Flipped `status: active` → `complete`.

## Context

The 288M legacy `venue=ODDS_API` rows are already in canonical MTDS bucketed shape (`odds_horizon_bucket`, 8 horizons
T-24h…T-0) and the MDPS `SportsBucketAssignmentAdapter` backfill ran to 98.7% across 5+ years (the rest honest-empty,
e.g. Sep-Oct 2022 international break) — all flipped in the epic 2026-05-23. What stays OPEN on the sports side is
running features-sports-service (FSS) over that bucketed dataset and verifying the produced feature matrix is ML-ready,
so that predictions ML training (owned in `predictions_master`) has a clean, ≥95%-non-NULL input at its target buckets.

## P0/P1 — FSS run + ML-ready matrix verification

- [x] [SCRIPT] P1. Run features-sports-service (FSS) on the bucketed dataset — verify odds features populate (velocity,
      CLV, steam, late-money). Repo: features-sports-service. Was BLOCKED-ON the full bucket backfill (now complete per
      epic 2026-05-23 — unblocked). ✅ features-service@62de3d1d — fixed merge collision bug (_x/_y shadow of
      NaN-initialised ODDS_COLUMNS), added batch steam detection (_compute_steam_features via Pinnacle T-24h→T-1h
      movement), removed 16 ghost columns from ODDS_COLUMNS that were always-NaN (never computed), disabled WriteGate
      alignment check for sports (uses available_at not timestamp; T-24h odds precede fixture date by design). FSS CLI
      now writes odds_features to GCS for all 4 horizons. QG green (17397 tests passed). Validated: velocity 100%
      non-null, steam 100% non-null, CLV/opening odds populated, WriteGate passes. Full backfill across 1813 dates
      dispatched next.
- [x] [SCRIPT] P1. Verify the feature matrix is ML-ready: one row per `(fixture × bucket)`, NaN only where
      honest-absence. Repo: features-sports-service. ✅ features-service@9b29b834 — ml_readiness_check.py: 3 invariant
      checks (shape/one-row-per-fixture×horizon, NaN discipline/identity cols never NaN, ≥95% non-NULL at T-24h+T-1h);
      verify_date_range() aggregates across date range with honest-absence separation (missing parquet = dates_missing,
      not dates_failed); CLI script scripts/sports/verify_ml_readiness.py exits 0/1 on gate_met; 14 unit tests
      cloud-agnostic (mocked GCS); QG green (CODEX_MAX_VIOLATIONS=0, schema provenance clean, no hardcoded IDs/buckets);
      strict-quickmerge clean.

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
