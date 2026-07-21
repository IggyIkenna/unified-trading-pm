---
doc_type: plan
title: Sports arb-decay-window analysis + paper-trade alpha gate — design spec (no implementation)
summary: >-
  Brand-new feature work with zero prior spec (confirmed: grepped decay_window/arb_decay/alpha_gate/paper_trade_alpha
  across strategy-service + execution-service + codex, only unchecked todos in archived plans exist). This plan defines
  WHAT the arb-decay-window statistic measures and WHAT the paper-trade alpha gate's pass/fail criteria are, before any
  code is written — per operator ruling (BLK-b567ce7d, 2026-07-21) on
  sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md's todo, writing speculative
  threshold/decay-curve code against zero spec risks building the wrong thing.
status: active
nature: design
asset_group: [sports, prediction]
stage: [strategy]
repos: [strategy-service]
scope: [engineer, admin]
tags: [sports, arbitrage, decay-window, alpha-gate, paper-trade, promotion-gate, design]
related:
  [
    plans/active/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md,
    codex/09-strategy/operational/batch-live-reconciliation-threshold-calibration.md,
    codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
    codex/04-architecture/promote-workflow-architecture.md,
  ]
created: "2026-07-21"
last_updated: "2026-07-21"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: design
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    "operator ruling BLK-b567ce7d (2026-07-21): author a scoped design-only plan, assigned_vm: NA, NOT AO-dispatched —
    brand-new undefined feature work needs operator/spec sign-off on acceptance criteria + thresholds BEFORE any
    implementation dispatches",
  ]
assigned_role: quant_dev
drift_direction: advance-code
---

# Sports arb-decay-window analysis + paper-trade alpha gate — design spec

**This is a LOCAL/human plan (`assigned_vm: NA`) — not ingested by the AO backlog.** It defines the SPEC; it does not
implement code. The operator reviews this plan and, if satisfied, either does the implementation themselves or flips
this plan (or a follow-on AO-dispatched plan referencing it) to `assigned_vm: planning`.

**Prerequisite already shipped**: `strategy-service@9a7de7f8` — the Group-B sports/prediction fixture dataset +
`scripts/run_sports_arb_backtest.py` caller, the hermetic backtest harness this design's acceptance test will run
against.

**Existing building blocks this design must ground itself in** (do not re-derive from scratch — cite/reuse):

- `SportsArbDutchingEngine` (`strategy_service/engine/strategies/v2/arbitrage_structural/sports_arb_dutching.py`) — the
  dutched-stake N-venue arb engine that PRODUCES the edge this design measures the decay of.
- `codex/09-strategy/operational/batch-live-reconciliation-threshold-calibration.md` — the ONLY existing threshold/gate
  pattern in this codebase (`RECON_GREEN_THRESHOLDS`, WARNING/CRITICAL severity bands, a 7-day-soak calibration
  procedure). The alpha gate below should follow this SAME shape (a named threshold in a UAC constants module + a
  calibration procedure), not invent a new gate architecture.
- `codex/09-strategy/operational/paper-batch-live-reconciliation.md` — "live↔paper delta IS execution alpha" is the
  existing codex framing of "alpha" in this codebase; the paper-trade alpha gate below is a PROMOTION gate (paper → live
  eligibility), a different but related concept — this plan makes that distinction explicit (§2).

## 1. Arb-decay-window analysis — what it measures

**The problem**: `SportsArbDutchingEngine` detects a dutched-arbitrage opportunity (a complete odds-outcome set whose
implied probabilities sum to <1, `min_overround_savings_pct` gated) at signal time, but sports-book odds move
continuously — by the time all N legs actually fill (sequenced, `hedge_deadline_ms` apart per the engine's existing
`AtomicExecutionMode.SEQUENCED_WITH_PACING`), some or all of the detected edge may have evaporated. The
**arb-decay-window** is the analysis of how much edge survives as a function of elapsed time between signal and fill.

**Todos (spec only):**

- [ ] [DESIGN] P3. Define the decay-window STATISTIC precisely:
      `edge_bps_remaining(t) = observed_overround_savings_at_fill     - observed_overround_savings_at_signal`, measured
      per-leg at each leg's actual fill timestamp (not just the first/last leg) against the ORIGINAL signal-time odds
      snapshot the engine computed its dutched stakes from. State whether this is measured in absolute bps or as a
      fraction of the signal-time edge (recommend: both — absolute bps for a min-viable-edge floor, fraction for the
      decay-CURVE shape).
- [ ] [DESIGN] P3. Define the WINDOW boundaries: is decay measured from signal-time to (a) first-leg fill, (b) last-leg
      fill, or (c) each leg independently against a shared t=0? Recommend (c) — it directly answers "does
      `hedge_deadline_ms` need tightening" per-leg, which (a)/(b) collapse away. State the sampling granularity (e.g.
      per-100ms bucket vs per-fill-event) and the minimum + maximum window this analysis covers (must not exceed the
      engine's own `hedge_deadline_ms` + abort-on-adverse-move cutoff — decay data past that point is meaningless, the
      trade would already have aborted).
- [ ] [DESIGN] P3. Define the DATA SOURCE: this analysis needs the signal-time odds snapshot (already computed by the
      engine at detection) PLUS a fill-time odds re-snapshot per leg. State whether the paper-trade run's existing
      `GroupBRunner`/`AtomicInstruction` fill records already carry a fill-time odds value, or whether this requires a
      NEW field on the instruction/fill record (if new, name it explicitly — this is a real-code consequence of the
      design, flag it for the implementer, don't hide it).
- [ ] [DESIGN] P3. Define the OUTPUT shape: a decay curve (edge_bps_remaining vs elapsed_ms) aggregated across N paper
      runs, bucketed by outcome-set size (2-way vs 3-way) since a 3-way set's 3rd leg fills later by construction and
      should show more decay structurally, not because of a real venue-speed problem — conflating the two would
      mis-diagnose noise as a real regression.

## 2. Paper-trade alpha gate — pass/fail criteria for promotion

**The problem**: before `ARBITRAGE_SPORTS_DUTCHING` (or any sports archetype) is eligible for `paper_1d`→`live_early`
promotion (per `codex/04-architecture/promote-workflow-architecture.md`'s existing promote workflow), there needs to be
an explicit, named threshold the paper-run's realized performance must clear — analogous to `RECON_GREEN_THRESHOLDS`'s
`bps_delta_max`/`drawdown_pct`/`fill_rate_min`, but measuring REALIZED EDGE not paper-vs-live deltas (there is no live
leg yet at this gate — it fires BEFORE promotion, using pure paper data).

**Todos (spec only):**

- [ ] [DESIGN] P3. Define the GATE STATISTIC: recommend
      `realized_edge_bps_net = mean(edge_bps_remaining at actual     fill, per §1) - round_trip_fee_bps - decay-window §1's measured decay`,
      i.e. the edge that's LEFT after decay and fees, not the naive signal-time edge (which the arb-decay-window
      analysis above will show is systematically too optimistic). State the exact aggregation: mean across all paper
      trades in the soak window, or a percentile (e.g. p25, to gate on worst-case not average-case)? Recommend p25 — an
      arb strategy's failure mode is "average looks fine but the tail regularly goes negative," which a mean would mask
      (mirrors this workspace's own preference for tail-aware gates, e.g. `RECON_GREEN_THRESHOLDS`'s
      CRITICAL-band-on-any-single-trade design).
- [ ] [DESIGN] P3. Define the MINIMUM SAMPLE SIZE + soak duration before the gate can fire at all (an N=3 paper-run
      "pass" is not statistically meaningful for a strategy whose edge is inherently intermittent/event-driven, unlike a
      continuous market-making strategy). Recommend following the EXISTING 7-day-soak precedent in
      `batch-live-reconciliation-threshold-calibration.md` as the floor, adapted for sports' event-driven cadence (state
      explicitly: is "7 days" the right unit for a strategy that might only see a handful of qualifying fixtures in that
      window, or should the gate instead require a minimum TRADE count regardless of elapsed days? recommend requiring
      BOTH — a minimum elapsed-days floor AND a minimum trade-count floor, whichever binds later).
- [ ] [DESIGN] P3. Define the PASS/FAIL threshold VALUE and where it lives (recommend: a new
      `SPORTS_ARB_ALPHA_GATE_THRESHOLDS` entry in the same UAC `thresholds.py` module `RECON_GREEN_THRESHOLDS` already
      lives in, not a strategy-service-local constant — keeps the "thresholds are UAC SSOT, never hardcoded in service
      code" rule intact). State whether an initial threshold value is proposable now from the existing Group-B backtest
      fixture data (`tests/fixtures/sports_odds/premier_league_arb_sample.py`), or whether it must be operator-set
      pending real paper-run data (recommend: propose a conservative placeholder derived from the fixture +
      `min_overround_savings_pct`'s existing engine-level floor, explicitly flagged as "provisional pending real soak
      data," not asserted as final).
- [ ] [DESIGN] P3. Define the ACCEPTANCE TEST for this design: once implemented, what proves the gate works? Recommend a
      hermetic test using `scripts/run_sports_arb_backtest.py`'s existing fixture-driven paper run
      (`strategy-service@9a7de7f8`) asserting (a) the gate correctly PASSES on the fixture's known-profitable synthetic
      scenario and (b) correctly FAILS on a synthetic decayed-to-zero-edge scenario (a new fixture variant to add) —
      i.e. prove both the true-positive and true-negative path, not just that the code runs.

## 3. Open questions for operator sign-off before implementation dispatches

- Is `quant_dev` (strategy math craft) the right assigned_role for the eventual implementation, or does the fill-time
  odds re-snapshot data-plumbing (§1 todo 3) actually belong to `backend_engineer`/MTDS first? Flag this as a possible
  TWO-repo split (data plumbing in MTDS/execution-service; the gate math in strategy-service) once real implementation
  is scoped.
- Confirm p25 (tail-aware) vs mean for the gate statistic (§2 todo 1) — this is a real risk-appetite decision, not a
  mechanical one.
- Confirm the provisional threshold-value approach (§2 todo 3) is acceptable, or whether the operator wants to set the
  real number before any code ships (i.e. gate implementation on having real paper-run data first).

## Codex SSOTs

`codex/09-strategy/operational/batch-live-reconciliation-threshold-calibration.md` (the gate-architecture precedent),
`codex/09-strategy/operational/paper-batch-live-reconciliation.md` (existing "alpha" framing),
`codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` (P&L factor taxonomy the realized-edge statistic
must map into, not invent a parallel "other" bucket for), `codex/04-architecture/promote-workflow-architecture.md`
(where this gate fits in the paper→live promotion sequence).
