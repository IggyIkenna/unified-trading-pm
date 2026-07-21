---
doc_type: issue
title:
  Sports/predictions strategy+execution backtest and live-mode activation — orphaned across 3 archived plans, never
  re-homed
summary: >-
  Triaging archived-plan debt (`sports_ml_may_23_2026.epic.md`, `sports_e2e_validation_2026_03_27.plan.md`,
  `sports_predictions_e2e_2026_05_05.plan.md`) surfaced a recurring cluster of open items describing the same underlying
  gap that was never re-homed into an active plan when its parent epics were restructured 2026-06-20: running a
  sports/predictions strategy backtest and an execution-service backtest through the already-shipped L0 Sports TOB
  matching-engine class, a `spread_calculator` in features-service, arb-decay-window analysis, a paper-trade alpha gate,
  an FSS/ML-training/strategy-service schema-parity test, a UI check that predictions actually render, and the full
  MTDS/MDPS/FSS/strategy live-mode activation chain for sports. None of this is stale — the matching-engine code,
  arb_calculator, and ML walk-forward pieces it depends on have shipped — but the "wire it up and run it end-to-end"
  step has no owning plan anywhere in `plans/active/`.
status: open
nature: issue
asset_group: [sports, prediction]
stage: [strategy, execution]
repos: [strategy-service, execution-service, features-service]
scope: [engineer]
tags:
  [sports, predictions, backtest, execution, matching-engine, spread-calculator, live-mode, orphaned-work, plan-debt]
related:
  [
    plans/archive/sports_ml_may_23_2026.epic.md,
    plans/archive/sports_e2e_validation_2026_03_27.plan.md,
    plans/archive/sports_predictions_e2e_2026_05_05.plan.md,
    plans/active/sports_master_closeout_2026_07_21.md,
    plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md,
    plans/active/issues/pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md,
  ]
created: "2026-07-21"
parent_epic: sports_master
priority: P3
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [pm_qg_plan_discipline_and_frontmatter_regression-004]
resolved_by:
locked_by:
depends_on: []
---

# What I found

Three archived plans independently describe the same downstream work — running sports/predictions strategy and execution
through backtest, then live mode — and in each case the item was quietly dropped when the plan was restructured into
`sports_master`/`predictions_master` (2026-06-20), rather than carried forward or explicitly ruled out of scope:

1. **`sports_ml_may_23_2026.epic.md`** — "Strategy backtest" and "Execution backtest (Sports L0 TOB matcher)". The
   matcher CODE shipped (`execution-service/execution_service/matching_engine/`, confirmed 5 matcher classes incl. L0
   Sports TOB per `plans/active/master_to_live_defi_2026_05_23.md:812`) but no plan runs it end-to-end for sports.

2. **`sports_e2e_validation_2026_03_27.plan.md`** — `spread_calculator` in FSS, a strategy-service arb backtest, and an
   "optimal decay window" analysis (Phase 3); MTDS/MDPS/FSS/strategy live-mode wiring (Phase 5). `arb_calculator`
   shipped (confirmed `features-service@9347dbeb`) but `spread_calculator` and the backtest/live-mode items don't appear
   anywhere in `plans/active/`.

3. **`sports_predictions_e2e_2026_05_05.plan.md`** — same `spread_calculator` gap plus strategy-service backtest,
   execution-service matching-engine pass, arb-decay-window analysis, a paper-trade alpha gate (Group F); an
   FSS/ML-training/strategy-service schema-parity test and a UI check that predictions render correctly (Group H); and
   the full unattended live-pipeline activation chain (Group I).

Cross-checked all of `plans/active/*.md` and `plans/active/issues/*.md` by keyword (`spread_calculator`, "live mode",
"execution backtest", "strategy backtest") — no active plan or issue owns any of this. `sports_master.md`'s own routing
tables account for the ML-training half (`predictions_ml_walk_forward_and_arb_2026_06_20.md`) and the data/coverage half
(`sports_consolidated_closeout_2026_07_19.md`, `sports_master_closeout_2026_07_21.md`), but the
strategy+execution+live-mode half was never given a routing entry.

# Why it matters

Per `plans/active/master_to_live_defi_2026_05_23.md`'s asset-group readiness ladder, Sports and Prediction are
deliberately scoped to "ML pipeline running" / "features pipeline running" for the May-23 cutover — no live trading this
cycle — so this gap did not block that milestone. But it means there is currently no tracked path to actually proving
the shipped matching-engine + arb-calculator code works end-to-end for sports/predictions, nor any owner for eventually
turning on live mode. Left unfiled, this class of work keeps re-appearing as a stale checkbox in newly-archived plans
(as it did three times here) instead of accumulating real progress.

# Recommended decision

File this as one tracked backlog item rather than reviving three separate archived plans. Given it's explicitly
post-May-23 / not on the critical path, P3 is appropriate — the goal is visibility, not urgency.

## Todos

- [x] ✅ [SCRIPT] P3. ~~Implement `spread_calculator`~~ — **CORRECTION, not orphaned**: verified live in
      features-service that the sharp-soft-spread/vig/max-min FUNCTIONALITY this todo describes already ships, wired
      into the real feature-export pipeline (`odds_features_exporter.py:225`), just under different names than a single
      `spread_calculator.py` module mirroring `arb_calculator.py`'s file layout: `sharp_soft_gap_home/     draw/away` +
      `book_range_prob_home/draw/away` (= max-min across books) in
      `features_service/sports/calculators/odds_prob_space.py` (`compute_prob_space_features`), and `market_vig`/
      `vig_pct` (+ a bucketed `vig_bucket`) in `odds_calculator.py`/`bucketed_features_calculator.py`. My original
      GENUINELY_ORPHANED verdict was wrong — it grepped only for a literal `spread_calculator` symbol and didn't find
      the equivalent functionality under its actual names. Writing a duplicate `spread_calculator.py` now would be
      redundant tech debt, not a real gap — no code shipped, none needed. (repo: features-service)
- [ ] [SCRIPT] P3. Run a strategy-service backtest for sports/predictions archetypes through the shipped execution
      matching-engine (L0 Sports TOB matcher), including an arb-decay-window analysis and a paper-trade alpha gate.
      (repo: strategy-service)
- [ ] [SCRIPT] P3. Build an FSS output-schema ↔ ML-training-service input-schema ↔ strategy-service input-schema parity
      test for sports/predictions — no active plan currently owns this gate. (repo: features-service)
- [ ] [VERIFY] P3. UI check that sports/predictions signals actually surface in the trading UI once produced (not just
      that the pipeline runs). (repo: unified-trading-system-ui)
- [ ] [INFRA] P3. Scope + gate the full MTDS/MDPS/FSS/strategy live-mode activation chain for sports/predictions on an
      explicit operator go-ahead (both asset groups are intentionally backtest-only today per the readiness ladder —
      this todo is about having a plan ready, not activating live trading). (repo: deployment-service)

## Codex SSOTs

`codex/04-architecture/backtest-groups.md`, `codex/04-architecture/batch-live-architecture.md`,
`codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md`.
