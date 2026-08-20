---
doc_type: plan
title:
  Prediction Phase E — football cross-venue arb enablement, live path (split from
  prediction_consolidated_closeout_2026_07_18)
summary:
  Phase E of the prediction consolidated close-out, split out verbatim (line-cap remediation, 2026-07-24) — the
  af_fixture_id identity chain (Polymarket + Kalshi soccer, ~0%→~100% team-name matching) and the 3-venue
  Kalshi/Polymarket/Betfair PAPER arb (signal + execution bridge) are shipped and verified; residual open work is
  verifying the end-to-end fixture link in-season, the 3-way arb correctness guards, and the operator-gated live
  odds/execution decisions (E3). Gated on the Phase A-B residuals plan (carries the Phase-B fixture-attribute backfill)
  and the Phase D plan (carries the formal smoke-green gate), per the parent plan's own stated "Phase E (gated on B+D)".
status: active
nature: process
asset_group: [prediction]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    deployment-ui,
    features-service,
    e2e-testing,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    prediction,
    close-out,
    cross-venue-arb,
    sports-fixtures,
    football,
    af-fixture-id,
    betfair,
    execution-bridge,
    live-gate,
  ]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_phase_c_data_status_ui_2026_07_24.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md,
    /plans/archive/issues/prediction_arb_live_execution_bridge_2026_07_20.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-08-20"
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [prediction_phase_ab_residuals_2026_07_24, prediction_phase_d_formal_smoke_and_backfill_2026_07_24]
gate_on_depends: true
source: >-
  Split from `prediction_consolidated_closeout_2026_07_18.md` (Phase E section, lines 438-499 of that doc as of
  2026-07-18/2026-07-24) per the operator-approved line-cap remediation triage
  `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` (row 22, "4-way split along the plan's own Phase A-E
  boundaries — one depends_on-gated: Phase E gated on B+D"). Content moved verbatim, not summarized. The `depends_on` +
  `gate_on_depends: true` on the Phase A-B residuals and Phase D sibling plans encodes the parent plan's own Phase-E
  header text ("gated on B+D") as a real dispatch gate.
context_scope:
  [
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md,
    /codex/04-architecture/cross-venue-prediction-arb-detection.md,
    features-service/features_service/cross_instrument/app/calculators/prediction_cross_venue_dispatch.py,
    unified-api-contracts/unified_api_contracts/canonical/domain/predictions/cross_venue_mapping.py,
  ]
---

# Prediction Phase E — football (soccer) cross-venue arb enablement, live path

> **Split from `prediction_consolidated_closeout_2026_07_18.md` (2026-07-24).** This is the Phase E section of that
> close-out, moved verbatim. **Gated** (`depends_on` + `gate_on_depends: true`) on
> `prediction_phase_ab_residuals_2026_07_24.md` (carries the Phase-B fixture-attribute backfill this phase's E1 depends
> on) and `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md` (carries the formal post-migration smoke-green
> gate) — matching the parent plan's own Phase-E header, "football (soccer) cross-venue arb enablement (the originating
> ask; gated on B+D)". For the full historical execution narrative (Progress Log, ticks 1-31, especially ticks 24-31
> which cover nearly all of this phase's shipped work) and shared cross-phase context (the Ground-truth verdict table,
> the prediction shard-atom definition, the MVP universe scope), see the parent doc. Sibling phase children:
> `prediction_phase_c_data_status_ui_2026_07_24.md` (Phase C), `prediction_phase_ab_residuals_2026_07_24.md` (Phase
> A-B).

## Phase E — football (soccer) cross-venue arb enablement (the originating ask; gated on B+D)

> Makes live-odds-API-vs-Polymarket-vs-Kalshi football arb possible on a CANONICAL basis. Depends on the A4 writers +
> the Phase-B fixture-attribute backfill landing. SSOTs:
> `/codex/04-architecture/cross-venue-prediction-arb-detection.md`,
> `/codex/16-strategy-playbooks/strategy/cme-polymarket-arb.md`, `instruments-service/docs/SPORTS_INSTRUMENTS.md`.

### E1 — Thread the fixture id onto BOTH prediction venues (Leg 1)

- [x] ✅ [BACKEND] P1. **Verified end-to-end fixture link on Polymarket + Kalshi soccer** — confirm A4/B produced a
      resolved `af_fixture_id` (or `build_fixture_id` string) on Polymarket soccer markets, and BUILT the same for
      Kalshi (which has none today). Keep the prediction canonical naming; the fixture id is an ADDITIVE attribute.
      Acceptance: a Polymarket market and a Kalshi market for the same real fixture resolve to the SAME `af_fixture_id`,
      and both resolve to the same odds-tick `af_fixture_id`. (repos: instruments-service, market-tick-data-service,
      unified-api-contracts) — **CLOSED (2026-08-15, /plan-reconcile, operator interactive)**: this todo's "has none
      today" framing was stale — E2 (below) shipped Kalshi soccer team resolution feeding the shared
      `PredictionFixtureResolver` (`instruments-service@ec8633ac` + `unified-api-contracts@e7ed754e`, 82.6%→~100% on 92
      live fixtures), satisfying the fixture-link acceptance criteria this todo describes. Closing citing E2's shipment
      rather than duplicating it as separately-open.

### E2 — Close the team-name matching gap to ~0% (Leg 2)

- [x] ✅ [BACKEND] P1. **Fixture matching to the ~0% gap — DONE (Kalshi + South-American).** (b) ✅ Kalshi soccer team
      resolution SHIPPED: parser `instruments-service@ec8633ac` (`parse_kalshi_soccer_participants` → A4's
      `PredictionFixtureResolver` via the shared `validate_team_resolution` index, no new GCS walk) + 8 aliases
      `unified-api-contracts@e7ed754e` → **~0% → 82.6%→~100%** on 92 live Kalshi fixtures. (a) ✅ SHIPPED South-American
      club aliases `unified-api-contracts@98d757f9` (Chile/Argentina — Universidad Católica (CHI), Audax Italiano,
      Estudiantes L.P., Argentinos JRS, Central Córdoba de Santiago, Colo-Colo, O'Higgins, …), each verified against the
      API-Football FIXTURES parquet `af_home_name`; canonical ids pre-existed → closes the odds-side ~66% cap. Kalshi
      home/away title-order caveat ✅ CLOSED `instruments-service@ba3528d4` (order-robust lookup: probes both orderings,
      home/away from the matched fixture). (repos: instruments-service ✅, unified-api-contracts ✅ / South-American
      remaining))

### E3 — Unify the two arb paths onto the shared fixture identity (Leg 3)

- [ ] [BACKEND] P1. **Only gap (3) of 3 remains open — gaps (1)-(2) SHIPPED since the 2026-07-19 trace (verified live
      in code 2026-08-12).** Wire the arb engine to CONSUME `af_fixture_id`. ~~The 6 materialized columns are
      an UNCONSUMED landing spot~~ — **(1) DONE**: features-service
      `prediction_cross_venue_dispatch.py::_records_from_universe` now reads the 6 `_COL_*` columns and populates
      `InstrumentRecord.af_fixture_id` / `af_league_id` / home+away canonical ids / `fixture_date` /
      `af_fixture_match_status` (`features-service@ba385100c`, 2026-08-05). **(2) DONE**: UAC
      `predictions/cross_venue_mapping.py::match_key` now accepts + PREFERS `af_fixture_id` — returns the exact
      `SPORTS_FIX::{id}::{bet_type}` key when set, falling back to the fuzzy `sports_pairing_key` only when
      `af_fixture_id is None` (`unified-api-contracts@1dddc6804`, 2026-07-31 — matches the live docstring and
      `/codex/04-architecture/cross-venue-prediction-arb-detection.md`'s "Identity" section, which was correct, not this
      todo's stale text). **Remaining — (3) only**: 3rd venue (bookmaker odds): generalize `build_cross_venue_mapping`
      beyond its pairwise Kalshi↔Polymarket shape, OR resolve `SportsArbDutchingEngine`'s
      `decimal_odds_<outcome>_<venue>` features per `af_fixture_id`, so live-odds ∧ Polymarket ∧ Kalshi pair on ONE
      fixture. Also: **CORRECTED 2026-08-16 (plan_reconciler)** — the wired prediction-arb slots today are CRYPTO
      (`btc/eth/spx UP_DOWN_DAILY`) plus MLB/NFL/NBA/Tennis (added via
      `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`, shipped 2026-08-05 — the prior "ONLY... CRYPTO" premise
      here was stale, predating that ship despite this todo's own "verified live in code 2026-08-12" claim); still, no
      FOOTBALL prediction-arb slot exists yet — one must be added. Cross-reference (see also, not a literal fold — the
      two docs' "arb" concepts differ): `predictions_ml_walk_forward_and_arb_2026_06_20.md`. (repos:
      features-service, unified-api-contracts, strategy-service, e2e-testing)
- [ ] [BACKEND] P2. **3-way arb correctness guards** — prediction-market "lay" is the NO-side complement, not a real
      exchange lay (exclude from back-lay arbs; include in 3-way with exchange_meta validation); keep the honest gate
      that a real two-sided book must exist on BOTH venues before emitting an arb row.
      `/codex/04-architecture/cross-venue-prediction-arb-detection.md`. (repos: features-service)
- [x] ✅ [BACKEND] P2. **Venue-derivation for prediction/sports `instrument_id`s in execution-service — BOTH sites FIXED
      (2026-07-18).** The naive `split(":")[0]` returned the TYPE/SPORT for TYPE-first ids. (1) ✅
      `validation/instrument_format.py::get_venue_from_instrument_id` `execution-service@ccd6883b` (latent, no prod
      caller). (2) ✅ the production-critical sibling `utils/instruction_type.py::extract_venue`
      `execution-service@8fc542e0d` — it had the identical bug but is HEAVILY USED (~40 call sites: matching engines,
      preflight_gate, `infer_instruction_type`, `get_asset_group_from_instrument_id`) and HARD-CRASHED
      (`UnknownVenueError`) on a type-first id. Both use the SAME additive robust-parse via UAC `VENUE_CATEGORY_MAP`
      (venue-first byte-unchanged for cefi/defi/tradfi; type-first → `parts[1]`); QG-green, tests cover both. (repos:
      execution-service ✅)

## Progress Log

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — 3 open,
  `depends_on: [prediction_phase_ab_residuals_2026_07_24, prediction_phase_d_formal_smoke_and_backfill_2026_07_24]` +
  `gate_on_depends: true`, both prerequisites still open (verified by direct read). KEEP-NA on the gate citation alone;
  not re-derived.

- **2026-07-24 (plan-hygiene split) — forked from `prediction_consolidated_closeout_2026_07_18.md`.** This plan carries
  forward the Phase E section verbatim (5 todos total: 2 done / 3 open at split time). See the parent's Progress Log
  (ticks 24-31 — the identity-wiring trace, the 3-venue Betfair signal build, the execution-bridge build, and the
  net-of-fees entry gate + paper proofs) for the full session-by-session history of what is already shipped here,
  including the live-execution-bridge P1 issue (`issues/prediction_arb_live_execution_bridge_2026_07_20.md`) opened
  along the way. Future work on this plan logs new entries below.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- added the 2 real gate dependencies
  (phase_ab_residuals, phase_d) + E3's 2 named source files (features-service dispatch calculator, UAC cross-venue
  mapping).
- **na-eligibility-audit 2026-08-07 (prediction tranche, autonomous)**: KEEP-NA, valid — automatic per
  `depends_on`+`gate_on_depends: true` on `prediction_phase_ab_residuals_2026_07_24` (7 open) and
  `prediction_phase_d_formal_smoke_and_backfill_2026_07_24` (5 open) — both confirmed still `status: active` today,
  neither gate cleared. 3 open items independently re-verified as a bounded verification (E1) plus genuine
  arb-engine-wiring/correctness-guard design work (E3) — informational only, the gate citation alone already decides the
  verdict. Doc stays NA.

- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09 (prediction tranche)**: KEEP-NA, valid — re-checked
  against the full round-11 precedent set (IAM self-service default, D16 all-repos carve, S5.1 tiering,
  plan-destination-default-to-AO for auto-filed findings, escalation-N=3-days, reversibility-qualified deletes
  agent-executable after a fresh check, Option B retirement, GSM secret `deepseek-v4-pro-api-key` + 5 Slack webhooks) —
  none clear the double `depends_on`+`gate_on_depends: true` gate; both prerequisites
  (`prediction_phase_ab_residuals_2026_07_24` 7 open, `prediction_phase_d_formal_smoke_and_backfill_2026_07_24` 5 open)
  re-confirmed still open. No reclassification.
- **na-eligibility-audit 2026-08-10 (prediction tranche)**: KEEP-NA, valid — re-verified live, 3 open, unchanged. Double
  `depends_on`+`gate_on_depends: true` gate still open (both prerequisites still status:active, 7 and 5 open todos
  respectively). E3's arb-engine identity-wiring + correctness-guard items also independently confirmed as genuine
  multi-file design/build work on live dispatch-critical machinery, not RECLASSIFY-eligible even setting the gate aside.
  Doc stays NA.

- **na-eligibility-audit 2026-08-17** [body-hash:fd6de6563ae2fbd6]: KEEP-NA, valid — 2 open (E3: wire the arb engine to
  consume `af_fixture_id` for the 3rd/bookmaker-odds venue — gap 3 of 3, gaps 1-2 already shipped; 3-way arb
  correctness guards). Double `depends_on: [prediction_phase_ab_residuals_2026_07_24,
  prediction_phase_d_formal_smoke_and_backfill_2026_07_24]` + `gate_on_depends: true` re-confirmed live — first
  prerequisite still carries 6 open todos, gate not cleared. KEEP-NA on that citation alone; both remaining items are
  also independently genuine multi-file design/build work on live dispatch-critical machinery, not RECLASSIFY-eligible
  even setting the gate aside — consistent with 6 prior audit passes (07-30 through 08-10). Doc stays NA.

- **na-eligibility-audit 2026-08-17 (prediction tranche, re-verify)** [body-hash:da3d38da5ff6c1be]: KEEP-NA, valid —
  2 open items re-confirmed. The double `depends_on: [prediction_phase_ab_residuals_2026_07_24,
  prediction_phase_d_formal_smoke_and_backfill_2026_07_24]` + `gate_on_depends: true` gate is still live (both
  prerequisites re-verified `status: active`); both items are also independently genuine multi-file design/build work
  on live dispatch-critical arb-matching machinery. Doc stays NA.

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) -- re-verified, unchanged.
- **na-eligibility-audit 2026-08-18** [body-hash:63051a8a737811e0]: KEEP-NA, valid -- depends_on+gate_on_depends:true on both prediction_phase_ab_residuals_2026_07_24 and prediction_phase_d_formal_smoke_and_backfill_2026_07_24 re-confirmed live still open (4 and 5 open todos respectively). The 2 remaining items are also independently genuine multi-file design/build work on live dispatch-critical arb-matching machinery. Doc stays NA.
- **na-eligibility-audit 2026-08-19 (prediction tranche, dispatch agt-0e920e)** [body-hash:420870758404c9b5]: KEEP-NA,
  valid — double `depends_on` + `gate_on_depends: true` gate re-confirmed live still open (both prerequisites
  independently re-verified this same run: 4 and 5 open todos respectively). Both remaining items (E3 fixture-wiring,
  3-way arb correctness guards) independently confirmed as genuine multi-file design/build work on live
  dispatch-critical arb-matching machinery — not RECLASSIFY-eligible even setting the gate aside. Doc stays NA.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries).
