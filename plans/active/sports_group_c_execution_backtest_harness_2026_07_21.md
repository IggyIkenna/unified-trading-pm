---
doc_type: plan
title: Sports/predictions Group-C execution-alpha backtest harness — scope note
summary: >-
  Scopes a `run_sports_backtest` CLI in execution-service, mirroring the 3 existing domain runners
  (run_cefi_backtest/run_tradfi_backtest/run_defi_backtest), so sports/predictions gets a real Group-C execution-alpha
  harness. Decided YES-needed (not a category error) in
  sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md — this plan is the scope note the
  decision-todo said to produce, not the implementation itself.
status: active
nature: design
asset_group: [sports, prediction]
stage: [execution]
repos: [execution-service]
scope: [engineer, admin]
tags: [sports, predictions, backtest, execution, matching-engine, group-c, scope-note]
related:
  [
    plans/active/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md,
    /codex/04-architecture/backtest-groups.md,
  ]
created: "2026-07-21"
last_updated: "2026-07-21"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    "sports_predictions_live_mode_and_backtest_execution_orphaned-007: the Group-C decision-todo's own text said 'if
    yes, scope it as its own plan' — this is that plan.",
  ]
assigned_role: backend_engineer
drift_direction: advance-code
---

# Sports/predictions Group-C execution-alpha backtest harness — scope note

**This is a LOCAL/human plan (`assigned_vm: NA`) — not ingested by the AO backlog.** It scopes the work; it does not
implement it. Sits for operator review; flip to `assigned_vm: planning` (or author a referencing AO plan) if/when
approved for dispatch.

## Why this is needed (not just "run the strategy backtest again")

Per `/codex/04-architecture/backtest-groups.md`, Group C ("execution alpha") is a distinct concern from Group B
("strategy alpha") — it fixes the strategy instruction stream and tunes/measures the EXECUTION side (algo choice, venue
routing, fill realism) against a matching engine with realistic microstructure. `L0Matcher`
(`execution_service/matching_engine/engine.py:290`) already generically routes `BookmakerCategory`/`"BET"` sources to
`BookType.L0_TOB` (`engine.py:813`) — fill-or-reject at top-of-book, size-checked — which is exactly the microstructure
model Group C needs for sports. That means the matcher-side prerequisite is already done; what's missing is purely the
CLI wiring, same shape as the 3 domains that already have it.

## Todos

- [ ] [BACKEND] P3. Add `run_sports_backtest(args, config, config_path) -> int` to
      `execution_service/cli/backtest_domains.py`, mirroring `run_defi_backtest`'s structure (simplest of the three — no
      lateral-feed preloading needed): `setup_backtest(...)` → `_create_backtest_engine(...)` →
      `run_and_save_backtest(...)`. Needs an `extract_sports_instrument` extractor (new, alongside
      `extract_cefi_instrument`/`extract_tradfi_defi_instrument` in `engine/backtest/runner.py`) that resolves a
      sports/prediction fixture+market instrument from config instead of a CeFi/TradFi symbol.
- [ ] [BACKEND] P3. Wire a data source: reuse the Group-B fixture dataset shipped in `strategy-service@9a7de7f8`
      (`tests/fixtures/sports_odds/premier_league_arb_sample.py`, 3 synthetic EPL ticks) as the first hermetic input —
      port or import it into execution-service's catalog/data layer rather than inventing a second fixture format.
      Confirm whether `CatalogManager` needs a new sports/prediction data-type branch or can consume the same
      synthetic-tick shape CeFi uses.
- [ ] [DESIGN] P3. Resolve the `SportsMatchingEngine` vs `L0Matcher` duplication found while scoping this
      (`execution_service/matching_engine/sports_matching.py` — zero callers anywhere in `execution_service/` or
      `tests/`, always fills at requested odds with no rejection/queue model, i.e. Group-B-shaped behavior sitting in
      the matching-engine module). Either: (a) delete it as unused dead code once confirmed truly orphaned, or (b) if it
      was meant to replace `L0Matcher` for sports specifically, explain why and wire it in instead of `L0Matcher`. Do
      this BEFORE building the CLI above so the harness targets the right matcher.
- [ ] [SCRIPT] P3. Add a hermetic test asserting `run_sports_backtest` produces a non-trivial `execution_alpha_bps` (per
      `backtest-groups.md`'s Group-C output contract) against the fixture data, proving the harness actually measures
      something (not just that it runs).
- [ ] [DESIGN] P3. Once the harness runs, decide whether it belongs in the routine backtest-groups verification surface
      (`docs/BACKTESTS.md` — currently DEAD per the sibling investigation's finding that its documented sports
      invocation was deleted at `strategy-service@fe2e0c7a`) or stays a manually-invoked one-off given sports is
      intentionally backtest-only / not on the live-mode critical path.

## Open questions for operator sign-off before implementation dispatches

- Is `backend_engineer` the right craft for the CLI wiring, or does the fixture/data-layer portion belong to `quant_dev`
  (same split question the sibling arb-decay-window design plan flagged for its own data-plumbing todo)?
- Priority: this stays P3 given sports/predictions' explicit backtest-only, not-on-critical-path status per
  `plans/archive/2026_07/master_to_live_defi_2026_05_23.md`'s readiness ladder — confirm no reason to raise it.

## Codex SSOTs

`/codex/04-architecture/backtest-groups.md` (Group C definition + output contract this harness must satisfy).
