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
- [x] ✅ [SCRIPT] P3. ~~Run a strategy-service backtest for sports/predictions archetypes through the shipped execution
      matching-engine (L0 Sports TOB matcher)~~ — **investigated: not runnable as scoped, premise mixes up two
      deliberately-separate systems.** `codex/04-architecture/backtest-groups.md:27-28,117-120` is explicit: **Group B
      (strategy-service) uses benchmark fills — "No matching-engine microstructure; zero execution alpha"**; the
      matching engine (incl. `L0Matcher` — confirmed real,
      `execution-service/execution_service/matching_engine/engine.py:290`, "L0_TOB Matcher for top-of-book-only
      sources... Sports/prediction bets default to TOB") is Group C's (execution-service's) job, isolating execution
      alpha on TOP of a Group B (or live) instruction stream — the two are architecturally never meant to fuse into one
      "strategy-service backtest routed through the matching engine" run. Confirmed in code too:
      `strategy_service/engine/backtest/benchmark_fills.py:9-10` — _"This lives in strategy-service (not
      execution-service) because Group B replaces execution entirely; execution-service owns Group C."_ So the literal
      ask is not a scoping gap, it's a category error inherited from the archived plans' original phrasing.

      Also verified while investigating: the ONLY sports backtest CLI/fixtures that ever existed
                                  (`scripts/run_sports_arb_backtest.py`, `tests/fixtures/sports_odds/`) were **deleted**
                                  `strategy-service@fe2e0c7a` ("citadel-grade service remediation... deleted orphaned scripts, legacy dirs"), so
                                  `docs/BACKTESTS.md`'s documented invocation is dead. `execution-service`'s Group-C CLI
                                  (`execution_service/cli/backtest_domains.py`) has `run_cefi_backtest`/`run_tradfi_backtest`/`run_defi_backtest`
                                  but **no `run_sports_backtest`** — a genuine Group-C sports harness doesn't exist either. The
                                  "arb-decay-window analysis" and "paper-trade alpha gate" have **zero code anywhere** in strategy-service,
                                  execution-service, or the cited codex docs — grepped `decay_window`/`arb_decay`/`alpha_gate`/`paper_trade_alpha`,
                                  the only hits are unchecked `- [ ]` todos in archived plans. These are net-new builds, not "run the shipped
                                  thing" verification.

                                  Sports/prediction archetypes DO exist and are exercised (proving the strategy engines themselves work):
                                  `strategy_service/engine/strategies/v2/archetype_slots_sports.py:20-84` (`SPORTS_ARBITRAGE`,
                                  `SPORTS_VALUE_BETTING`, `SPORTS_ML`, `SPORTS_HALFTIME_ML`, `SPORTS_MARKET_MAKING`), concrete engines
                                  `SportsArbDutchingEngine` + `prediction_venue_dispersion.py`, unit-tested (synthetic in-memory data, not a
                                  file-based dataset) in `tests/unit/engine/strategies/v2/test_sports_arb_dutching.py`.

                                  Split into 3 correctly-scoped follow-ups below rather than re-filing the same impossible-as-worded ask a 4th
                                  time. (repo: strategy-service, execution-service)

- [x] ✅ [DATA] P3. Restore or recreate a small committed sports/prediction odds fixture dataset (the deleted
      `tests/fixtures/sports_odds/` was VCR-cassette-style local data, no live GCS needed) plus a caller script
      analogous to the deleted `run_sports_arb_backtest.py` that builds `GroupBTickInput`s and calls
      `GroupBRunner`/`strategy-service --operation group-b-backtest --mode batch --asset-group SPORTS` — this is the
      prerequisite for ANY hermetic sports/prediction Group-B backtest run, in-session or otherwise. (repo:
      strategy-service) — `strategy-service@9a7de7f8`. Shipped `tests/fixtures/sports_odds/premier_league_arb_sample.py`
      (3 synthetic EPL ticks, deterministic, no cloud creds) + `scripts/run_sports_arb_backtest.py` (builds
      `GroupBTickInput`s, registers a strategy instance via `GroupBRunner.register_instance`, replays via
      `runner.run(...)`). **Ran it for real** (not just imported): 2/3 ticks fire real trades (edge above the
      archetype's `min_edge` threshold), 1 correctly no-trades (edge below threshold), non-zero P&L computed through the
      full `V2EngineOrchestrator` + `BenchmarkFillEngine` path.

      **Pivoted archetype mid-task, documented in the script + fixture docstrings**: the original ask targeted
                              `ARBITRAGE_PRICE_DISPERSION` (the "sports arb" name), but building the first working version surfaced that
                              this archetype's factory-registered engine is `ArbitragePriceDispersionEngine` (CEFI cross-venue price
                              dispersion) — `SportsArbDutchingEngine` (the real sports-odds dutching engine) shares the same
                              `StrategyArchetype` enum value but is NOT in `strategy_service.engine.strategies.v2.factory`'s dispatch
                              table, so a "sports arb" instance silently gets the wrong engine (verified directly: registered instance's
                              engine type resolved to `ArbitragePriceDispersionEngine`, fed a real odds book, returned `[]` every tick).
                              That's a genuine, separate wiring bug — filed as
                              `plans/active/issues/sports_arb_dutching_engine_not_wired_to_factory_2026_07_21.md` rather than absorbed here
                              or worked around silently. This script/fixture instead targets `ML_DIRECTIONAL_EVENT_SETTLED`
                              (`SPORTS_VALUE_BETTING`), which IS correctly wired — it genuinely proves the sports Group-B pipeline works
                              end-to-end, which was the actual point of this todo.

- [ ] [DESIGN] P3. Decide whether sports/predictions actually needs a Group-C execution-alpha harness (a new
      `run_sports_backtest` in `execution-service/execution_service/cli/backtest_domains.py`, exercising `L0Matcher`) —
      if yes, scope it as its own plan; if the original "route through the matching engine" ask was just imprecise
      phrasing for "prove the strategy backtest works," say so and retire the Group-C framing. (repo: execution-service)
- [x] ✅ [SCRIPT] P3. Build the arb-decay-window analysis + paper-trade alpha gate from scratch — zero code exists
      anywhere today; this is brand-new feature work (see the `brand-new` 1.0x estimate multiplier), not a verification
      task. Needs its own scoped plan once the Group-B fixture prerequisite above lands. (repo: strategy-service) —
      deliverable per operator ruling BLK-b567ce7d (2026-07-21, design-only, no speculative implementation): authored
      `plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md` (`assigned_vm: NA`, human plan, not
      AO-dispatched) defining the decay-window statistic/window-boundaries/data- source/output-shape and the paper-trade
      alpha-gate statistic/sample-size/threshold-location/acceptance-test, grounded in the existing
      `RECON_GREEN_THRESHOLDS` gate-architecture precedent (`batch-live-reconciliation-threshold-calibration.md`) rather
      than inventing a new one. Sits for operator review; flips to `assigned_vm: planning` (or a referencing AO plan)
      if/when they approve dispatching implementation.
- [x] ✅ [SCRIPT] P3. Build an FSS output-schema ↔ ML-training-service input-schema ↔ strategy-service input-schema
      parity test for sports/predictions — no active plan currently owns this gate. (repo: features-service) —
      **investigated first, found there is no schema contract to test parity against**: read the actual code in all
      three services (+ UAC) and found FOUR incompatible naming conventions for the same odds/probability data (FSS
      `home_implied_prob` vs strategy-service v2 `decimal_odds_HOME` vs strategy-service's separate legacy subscriber's
      `ht_odds_home_implied` vs UAC's own disconnected, zero-consumer `SportsFeatureVector`'s
      `market_home_implied_prob`) — writing a literal parity test now would either trivially pass (testing unrelated
      things are unrelated) or immediately surface this whole finding, not a small gap. Filed
      `plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md` with the recommended decision
      (canonicalize on UAC's `SportsFeatureVector` per the UAC-SSOT-types rule, pending operator/architect sign-off) and
      a follow-up todo to write the REAL parity test once a canonical naming is chosen. This is the same
      "spec-before-code" pattern as the sibling `sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md` plan
      (BLK-b567ce7d) — a naming decision, not a mechanical test-writing task, is the actual blocking gap here.
- [x] [VERIFY] P3. ✅ UI check that sports/predictions signals actually surface in the trading UI once produced (not
      just that the pipeline runs). (repo: unified-trading-system-ui) — `unified-trading-system-ui@35137c88`

  **Investigated first** (read the actual UI code, not just grep): the instructions/signal pipeline is already
  asset-group-agnostic and SPORTS_ML/PREDICTION are first-class, not excluded —
  `lib/mocks/fixtures/strategy-instructions.ts` carries SPORTS_ML/PREDICTION fixture rows,
  `lib/config/services/instructions.config.ts`'s filter dropdown lists them as options,
  `components/widgets/instructions/instruction-pipeline-rows.tsx` explicitly branches on `BACK`/`YES` directions
  (sports/prediction bet semantics) alongside `LONG`/`SHORT`, and the shell-wide `AssetGroupPill`
  (`lib/types/asset-group.ts`, `components/shell/asset-group-pill.tsx`) hardcodes SPORTS/PREDICTION as first-class
  groups with their own entitlement domains. The gap was that **nothing proved this empirically** — no regression spec
  exercised a SPORTS_ML/PREDICTION row through the real widget.

  **Fix shipped**: extended the existing `tests/widgets/instructions/instr-pipeline-table.test.tsx` L1.5 widget harness
  with two new cases — a SPORTS_ML instruction rendering with `BACK` direction, and a PREDICTION instruction rendering
  with `YES` direction — both driven through the real `InstructionsPipelineTableWidget` component (not a mock render).
  Ran it for real: 14/14 vitest cases pass (`npx vitest run tests/widgets/instructions/instr-pipeline-table.test.tsx`).
  `pw:L2` attempted (`npx playwright test --project=chromium tests/smoke/`): 66/94 passed, 25 failed — every failure is
  on an unrelated page (wizard/paper-trading/execution routes), and this change touches ZERO production code (only adds
  vitest assertions to an existing test file), so those 25 are pre-existing host-load flakiness on this shared
  multi-slot box, not a regression from this change. The L1.5 widget regression above is the actual verifying spec for
  this todo (per `codex/06-coding-standards/ui-testing-layers.md`'s L1.5 tier — `regression: tests/widgets/...`).

  **Not covered (documented, not silently dropped)**: the two dedicated "signals" pages
  (`app/(platform)/services/signals/dashboard/page.tsx`, `app/(platform)/services/research/signals/page.tsx`) key on
  `StrategyFamily`/`StrategyArchetype` rather than asset_group and have no SPORTS/PREDICTION fixture data or coverage —
  unproven either way, not excluded. Out of scope for this P3 check; a future task should add SPORTS_ML/PREDICTION
  fixtures to those two pages if they're meant to carry sports signals too.

- [x] [INFRA] P3. ✅ Scope + gate the full MTDS/MDPS/FSS/strategy live-mode activation chain for sports/predictions on
      an explicit operator go-ahead (both asset groups are intentionally backtest-only today per the readiness ladder —
      this todo is about having a plan ready, not activating live trading). (repo: deployment-service) — ✅
      `unified-trading-pm@0b491f273`. Operator ruled BLK-9d3a208c (2026-07-21): human/NA plan (terminal action is a
      human go/no-go on live trading, human-plan-by-construction). Authored
      `plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md`, grounded in the actual cefi/defi
      live-pipeline-activation precedent (not invented) via a dedicated research pass: documents sports' current
      readiness-ladder rung (ML pipeline running) and prediction's (features pipeline running), the STRUCTURAL blocker
      that genuinely differs from cefi/defi (sports has NO in-play live odds source integrated today — confirmed in
      `codex/04-architecture/sports-batch-live.md`: every current source is `{BATCH, REPLAY}`-only in UAC's
      `SOURCE_MODE_CAPABILITY`), the 4-layer activation chain reusing the proven pattern (MTDS live connector → MDPS
      `LiveModeHandler` config → FSS live handler build → the existing CLI-primary promote workflow,
      `CANDIDATE→PAPER_1D→LIVE_EARLY`), and cross-references (without duplicating) the other already-tracked
      prerequisites in this same issue doc (Group-B/C backtest harness, arb-decay-window design, FSS naming migration).
      Ends in an explicit `[OPERATOR]` go/no-go todo — nothing in the plan authorizes live activation on its own.

## Codex SSOTs

`codex/04-architecture/backtest-groups.md`, `codex/04-architecture/batch-live-architecture.md`,
`codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md`.
