---
doc_type: plan
title: Layer-1 re-measure + certify (Stage 3) — the honest denominator, all AGs (AO Plan 4)
summary:
  Re-measure and certify the Layer-1 instrument denominator per asset_group on the corrected catalogue + seeded
  manifests, then record the fresh numbers so any Layer-2 capture percentage becomes trustworthy. The 2026-06-29
  certified numbers are stale (predate v12, the incremental-rollup switch, the cefi ghost-dupe fix, D2a, and the defi
  seeding). This plan is gated (gate_on_depends) on Plans 1-3 landing — you cannot certify a denominator that is still
  being corrected. Two cross-plan prerequisites also apply, called out on the re-measure task (the KALSHI-PERP purge and
  the unregistered-handler audit). Closes the last honest_coverage_v2 measurement items.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, unified-api-contracts, market-tick-data-service]
scope: [engineer]
tags: [honest-coverage, layer-1, denominator, re-measure, certify, stage-3, instruments-completion]
related:
  [
    instruments_completion_tracker_2026_07_06.md,
    honest_coverage_v2_instrument_denominator_2026_06_28.md,
    honest_coverage_smoke_harness_2026_06_28.md,
    issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md,
    ../../codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-06
last_updated: 2026-07-06
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
model_tier: opus-required
thinking_tier: max
drift_direction: advance-code
depends_on:
  [cefi_layer1_denominator_gaps_2026_07_03, tradfi_v9_stage1_finish_2026_07_06, is_catalogue_completion_2d_2026_07_06]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source:
---

# Layer-1 re-measure + certify (Stage 3) — all AGs (AO Plan 4)

> **🤖 AO PLAN 4 of the instruments-completion set.** Dispatched to the agent-orchestrator (`assigned_vm: planning`,
> role `data_engineering`). **Dispatch tier (frontmatter-driven, EVERY task): Opus / max.** Coordinator =
> `instruments_completion_tracker_2026_07_06.md` (Stage 3).
>
> **⛔ GATED (machine-enforced):** `depends_on` Plans 1 (cefi denominator), 2 (tradfi Stage-1 finish), 3 (IS-catalogue
> completion) with **`gate_on_depends: true`** — the orchestrator holds every task here until all three upstream plans'
> tasks are done. Re-measuring a denominator that is still being corrected produces a number nobody can trust. **The one
> law:** Layer-1 gates Layer-2 — only after this certifies is any capture % meaningful.
>
> **Two cross-plan PREREQs on the re-measure (NOT owned here — this plan waits on them):** (1) **KALSHI-PERP
> contamination purge** — 25,473 fake `KALSHI-PERP` `PERPETUAL` rows (wrong-host `kalshi_perp` adapter) must be purged
> from the cefi catalogue first or the cefi Layer-2 numbers are polluted. Owned by
> `issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md` Phase 0 (slot-2 / the 4da6fe8 author). (2)
> **Unregistered-handler audit** (Plan 5) — run it BEFORE this re-measure so a built-but-unwired handler (`captured=0`,
> the Deribit C5 class) is not mislabelled as a real coverage gap in the certified numbers.
>
> **Worker guards (HARD):** (1) **run it, don't read it** — cite the actual `measure_honest_coverage` run output, not a
> stale snapshot. (2) record the fresh numbers in BOTH this Progress Log AND the tracker's Snapshot before declaring
> certified. (3) if a certified number moves the WRONG direction (denominator shrinks when it should grow), STOP and
> diagnose — do not certify a suspicious measure.

## Codex SSOTs (read before touching)

- `codex/02-data/honest-coverage-model.md` — two-layer model; Layer-1 gates Layer-2; do NOT derive the expected universe
  from the manifest (circular).

## Re-measure + certify (the gate is machine-enforced; certify in this order)

- [ ] [SCRIPT] P0. **Re-run `measure_honest_coverage`** on the corrected catalogue + seeded manifests (all AGs). The
      06-29 numbers are stale — they predate v12, the incremental-rollup switch, the cefi 122-row ghost-dupe fix
      (07-04), D2a (cefi 84.09→73.61), and the defi +1.38M seeding. **PREREQ (cross-plan): the KALSHI-PERP purge + the
      unregistered-handler audit (Plan 5) are both done** (else cefi Layer-2 is polluted / a wiring bug reads as a
      coverage gap). Gate: a fresh `coverage.json` produced from a real run; run id recorded.
- [ ] [VERIFY] P0. **Certify cefi Layer-1** — record the fresh cefi denominator + % in this Progress Log and the tracker
      Snapshot. Gate: cefi number recorded; denominator grew, % dropped vs 79.55 (the honest direction).
- [ ] [VERIFY] P0. **Certify defi Layer-1** — post the +1.38M seeding, record the fresh defi denominator + %. Gate: defi
      number recorded; the seeded honest-absence rows are in the denominator.
- [ ] [VERIFY] P0. **Certify tradfi Layer-1** — post the v9 migration + rebuild + IS catalogue (Plan 2), record the
      fresh tradfi denominator + %. Gate: tradfi number recorded; all 5 AGs now canonical-and-measured.
- [ ] [VERIFY] P0. **Certify prediction Layer-1** — post the KALSHI-PERP purge, record the fresh prediction
      denominator + %. Gate: prediction number recorded; no fake KALSHI-PERP rows in the measure.
- [ ] [VERIFY] P1. **Reconcile the certified Layer-1 set against the Layer-2 lower bounds** — flag any AG where the
      handler audit (Plan 5) changed capture so Layer-2 is re-read too. Gate: a single certified snapshot table (all 5
      AGs, both layers) with provenance.
- [ ] [VERIFY] P2. **`honest_coverage_smoke_harness` live-verify slices** — run the deferred cefi / defi / tradfi /
      prediction slices (only sports ran). Gate: each AG's smoke slice green or its discrepancy filed.
- [ ] [CODE] P1. **Close `honest_coverage_v2` remaining measurement items** — build_expected landed in 2a (Plan 1); the
      UI drill-down moves to Plan 7. Flip the honest_coverage_v2 measurement checkboxes with evidence. Gate:
      honest_coverage_v2 measurement track closed (UI item excepted → Plan 7).

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-06** — Plan authored + dispatched to AO (Plan 4 of the instruments-completion set). Gated (gate_on_depends)
  on Plans 1-3; two cross-plan prereqs (KALSHI-PERP purge + unregistered-handler audit) called out on the re-measure.
  This is the Stage-3 all-AG Layer-1 certification that makes capture % trustworthy.
