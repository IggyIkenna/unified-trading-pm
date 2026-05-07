---
title: Honest-Coverage Baseline (2026-05)
status: planned
created: 2026-05-07
authoritative_for: The May-2026 honest-coverage baseline — per-(asset_group, data_type) target coverage % + ratchet schedule. Feeds the workspace QG gate that prevents coverage-regression PRs from landing on `live-defi-rollout`.
referenced_by:
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.plan.md
related:
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/honest-absence-downstream-handling.md
  - codex/02-data/expected-absence-backfill-runbook.md
---

# Honest-Coverage Baseline (2026-05)

> **Status:** PLANNED — stub created 2026-05-07 to anchor forward-references from active plans. Body to be filled in
> as Tier 5 of writegate-honest-coverage ships.

## Purpose

A single, dated table of per-(asset_group, data_type) coverage % that any future change must not regress. This is the
input to the QG ratchet — a CI step compares the latest manifest's honest coverage against this baseline + raises a
hard-fail if the new value is lower (within tolerance).

"Honest coverage" here = `(captured + empty_confirmed_with_reason) / expected_universe`. Pure `captured/expected` ignores
the legitimate-absence cells; that's the dishonest version we are explicitly retiring.

## Scope

- All 5 asset_groups (cefi / defi / tradfi / sports / prediction).
- All canonical data_types per asset_group as of 2026-05-07.
- Ratchet schedule: when does the baseline tighten next? (e.g. monthly +1pp until 99%).
- Excluded: data_types that don't yet exist as of baseline date (added in subsequent baselines).

## Outline (planned sections)

1. **Baseline table** — `(asset_group, data_type, expected_universe_count, honest_coverage_pct, captured_count,
   empty_confirmed_with_reason_count, attempted_failed_count, baseline_date)`.
2. **Ratchet schedule** — how baseline updates over time; cadence + decision criteria (do we tighten, hold, or relax).
3. **Per-asset-group narrative** — context on why each asset_group's coverage is where it is + what blocks improvement.
4. **QG ratchet implementation** — CI step that reads the baseline + compares against latest manifest; tolerance
   (default ±0.5pp); hard-fail on regression beyond tolerance.
5. **Override procedure** — when a legitimate, intentional regression is needed (e.g. retired venue), how to update the
   baseline without ratchet rollback.
6. **Monthly review cadence** — who reviews, what evidence is required to ratchet up.

## Cross-references

- **Plan(s) implementing this:** [`writegate_honest_coverage_endtoend`](../../plans/active/writegate_honest_coverage_endtoend_2026_05_06.plan.md) Phase 5.
- **Related codex SSOTs:** [`availability-manifest-and-data-status`](./availability-manifest-and-data-status.md), [`honest-absence-downstream-handling`](./honest-absence-downstream-handling.md), [`expected-absence-backfill-runbook`](./expected-absence-backfill-runbook.md).
- **Code:** TBD ratchet check — likely `unified-trading-pm/scripts/qg/honest-coverage-ratchet.sh`.

## Open questions

- What is the tolerance band for "regression noise" — 0.1pp? 0.5pp? Per-asset-group different?
- Do we baseline + ratchet at the (asset_group, data_type) granularity or aggregate per asset_group? (recommend
  per-data-type — aggregate hides regressions in low-volume data_types).
- How is the expected universe sized exactly — current declared instrument count, or instrument count at baseline
  date frozen?
- Does the ratchet account for venue/source-coverage-start clipping, or is that already baked into `expected_universe`?
