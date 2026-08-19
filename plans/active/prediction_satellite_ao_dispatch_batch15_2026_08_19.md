---
doc_type: plan
title: prediction satellite AO dispatch batch 15 — 2026-08-19 (gated)
summary: >-
  Sibling of `prediction_satellite_ao_dispatch_batch14_2026_08_19.md`, split out per CLAUDE.md's "partial parallelism
  isn't expressible in one plan -> SPLIT" rule: these 3 items are conflict-clear and bounded, but genuinely GATED —
  2 (from `prediction_phase_c_data_status_ui_2026_07_24.md`) only need `prediction_phase_ab_residuals_2026_07_24`
  to reach 0 open todos (mirroring that source doc's own `depends_on`), the 3rd (from
  `prediction_phase_e_football_arb_live_2026_07_24.md`) needs BOTH that AND
  `prediction_phase_d_formal_smoke_and_backfill_2026_07_24` (mirroring ITS source doc's own `depends_on`). This
  plan's `depends_on` is the UNION of both — a deliberate, slightly conservative choice over splitting into 3
  single-purpose plans: items 1-2 could in principle dispatch as soon as phase_ab alone clears, but co-gating them
  with item 3 avoids 2 extra plan/finalize pairs for +/-1 dependency's difference; if phase_d lags materially behind
  phase_ab after phase_ab clears, split items 1-2 out into their own immediately-dispatchable batch16 at that time
  (this is flagged as this batch's own finalize todo 2, not left to be silently forgotten). `depends_on` is set now
  to document the real ordering (CLAUDE.md: this alone "does NOT affect dispatch"), but `gate_on_depends` is
  deliberately `false` WHILE DRAFT — `status: draft` already blocks 100% of dispatch on its own
  (`regen_backlog_from_plan.py` only derives tasks from `status: active` docs), so a machine gate is inert here and
  would only trip `check_finalize_plan_coverage.py`'s draft+gated-redundancy heuristic (scoped to FINALIZE plans per
  the 2026-07-30 no-double-gate ruling, not to a genuinely-judgment-requiring BATCH like this one — flagged as a
  real checker-heuristic gap, not fixed in this run). **HARD requirement for whoever flips this plan to `active`:
  set `gate_on_depends: true` in THE SAME EDIT** (mirroring batch11's same-day fix, which closed the exact
  "prose-only gating wastes dispatched-worker round-trips" trap this plan must not reproduce once it is actually
  dispatchable) — restated in the warning banner below and in batch15_finalize's own Progress Log. `status: draft`
  — a skill-drafted AO batch is never auto-shipped.
status: draft
nature: process
asset_group: [prediction]
stage: [data]
repos:
  [
    deployment-api,
    deployment-ui,
    instruments-service,
    deployment-service,
    features-service,
    unified-api-contracts,
    strategy-service,
    e2e-testing,
  ]
scope: [engineer]
tags: [prediction, ao-dispatch, satellite-batch, ag-closeout-audit, gated]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch14_2026_08_19.md,
    /plans/active/prediction_phase_c_data_status_ui_2026_07_24.md,
    /plans/active/prediction_phase_e_football_arb_live_2026_07_24.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
  [prediction_phase_ab_residuals_2026_07_24, prediction_phase_d_formal_smoke_and_backfill_2026_07_24]
gate_on_depends: false # INTENTIONAL while status:draft (inert either way, avoids a false check_finalize_plan_coverage.py
  # flag) -- MUST flip to true in the SAME edit that flips status: draft -> active. See summary + warning banner.
source: >-
  ag_closeout_auditor (slot 21, dispatch agt-6a0a6b), scheduled daily /ag-closeout-audit run scoped to the
  `prediction` tranche, 2026-08-19 — Phase 3 of the same audit that produced
  `prediction_satellite_ao_dispatch_batch14_2026_08_19.md`; see that doc's own `source:` for the full Phase 0-2
  numbers. This plan holds the GATED half of the extraction; see batch14 for the ungated half and the full Deferred
  population.
context_scope:
  [
    /plans/active/prediction_phase_c_data_status_ui_2026_07_24.md,
    /plans/active/prediction_phase_e_football_arb_live_2026_07_24.md,
    /codex/04-architecture/cross-venue-prediction-arb-detection.md,
  ]
---

# Prediction satellite AO dispatch batch 15 — 2026-08-19 (gated)

> **GATED — do not dispatch until `prediction_phase_ab_residuals_2026_07_24.md` AND
> `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md` both reach 0 open todos.** Currently held ONLY by
> `status: draft` (this plan is not yet operator-approved, so nothing dispatches regardless). **When an operator
> approves and flips `status: draft` -> `active`, that SAME edit MUST also flip `gate_on_depends: false` -> `true`**
> (frontmatter `depends_on` is already set; see `regen_backlog_from_plan.py`'s `_wire_gate_on_depends_prereqs`) —
> skipping that second flip reproduces the exact prose-only-gating trap batch11 hit today. Do not dispatch a todo
> below manually before both the operator approval AND the gate are in place.

## Todos

- [ ] [UI] P0. **RE-ADD the CQG/`canonical_question_group` axis to the already-shipped data-status dimensions
      panel.** The base panel (per-asset_group distinct `instrument_type`/`data_type`/`venue` census with counts)
      already shipped cross-cuttingly as `AxisValueCensus` (`deployment-ui@3fb6779`); the CQG axis this todo adds is
      confirmed still missing (0 `cqg`/`canonical_question_group` hits in the shipped component or its backing
      route). Wire `GET /data-status/prediction-catalogue`'s existing `cqg_counts` payload into the panel as an
      additional axis. pw:L2 regression required for the UI leg (CLAUDE.md's UI-testing-layers rule — cite the spec
      in your Done-when evidence). Repos: deployment-api, deployment-ui. Source:
      `prediction_phase_c_data_status_ui_2026_07_24.md` item at line 82. **Done when**: the CQG axis renders with
      counts in the panel, pw:L2 passes with a cited spec, and the source doc's own item flipped citing the SHAs.

- [ ] [BACKEND] P1. **Confirm honest-coverage green for prediction.** Verify `measure_honest_coverage.py` rolls up
      prediction correctly now that CQG cluster rows exist (output
      `gs://central-element-323112-honest-coverage/{date}/coverage.json`), AND verify the daily
      `honest-coverage-daily` Cloud Scheduler job actually fires (`gcloud scheduler jobs describe
      honest-coverage-daily --location=asia-northeast1`) — the source doc flags the script's own
      `last_executed: NEVER` header as unconfirmed. Repos: instruments-service, deployment-service. Source:
      `prediction_phase_c_data_status_ui_2026_07_24.md` item at line 92. **Done when**: a fresh `coverage.json` for
      prediction is verified correct (cite the date + a spot-checked CQG rollup number) AND the scheduler's last-run
      timestamp is confirmed within its cadence window; source doc's own item flipped citing both.

- [ ] [BACKEND] P1. **Unify the football cross-venue arb path onto the shared fixture identity — 3rd venue +
      correctness guards.** Two sibling pieces of the same E3 unification, combined into one todo since both touch
      the arb-engine/dispatch code in features-service (avoid a same-file race): (a) wire the arb engine to CONSUME
      `af_fixture_id` for the 3rd venue (bookmaker odds) — generalize `build_cross_venue_mapping` beyond its
      pairwise Kalshi<->Polymarket shape, OR resolve `SportsArbDutchingEngine`'s `decimal_odds_<outcome>_<venue>`
      features per `af_fixture_id`, so live-odds ^ Polymarket ^ Kalshi can pair on ONE fixture; also add a FOOTBALL
      prediction-arb catalogue slot (none exists yet — the wired slots today are crypto UP_DOWN_DAILY +
      MLB/NFL/NBA/tennis, no soccer). (b) 3-way arb correctness guards: exclude prediction-market "lay" (the NO-side
      complement, not a real exchange lay) from back-lay arbs; include it in 3-way arbs only with `exchange_meta`
      validation; keep the honest gate requiring a real two-sided book on BOTH venues before emitting an arb row.
      SSOT: `/codex/04-architecture/cross-venue-prediction-arb-detection.md`. Repos: features-service,
      unified-api-contracts, strategy-service, e2e-testing. Source:
      `prediction_phase_e_football_arb_live_2026_07_24.md` items at lines 134 and 154. **Done when**: a football
      fixture's live-odds/Polymarket/Kalshi legs resolve through one `af_fixture_id`-keyed arb row in a live/paper
      test, the 3-way correctness guards are unit-tested (lay-exclusion + 2-sided-book gate), `quality-gates.sh`
      green across all 4 repos, and both source-doc items flipped citing the SHAs.

## Progress Log

- **2026-08-19 (ag_closeout_auditor, prediction tranche, dispatch agt-6a0a6b)**: drafted alongside
  `prediction_satellite_ao_dispatch_batch14_2026_08_19.md` as the gated half of the same Phase 3 extraction.
