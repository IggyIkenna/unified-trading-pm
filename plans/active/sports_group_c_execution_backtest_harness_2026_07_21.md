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
context_scope:
  [
    /codex/04-architecture/backtest-groups.md,
    /plans/archive/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md,
    execution-service/execution_service/matching_engine/engine.py,
    execution-service/execution_service/matching_engine/sports_matching.py,
    execution-service/execution_service/cli/backtest_domains.py,
  ]
---

> **✅ OPERATOR RULING 2026-08-08 — dispatch APPROVED; the craft-split question is a NON-QUESTION, closed.** This doc's
> "Open questions for operator sign-off" asks whether the fill-time odds-plumbing todo belongs to `backend_engineer` or
> `quant_dev`. **It makes no operational difference.** Verified against
> `agent-orchestrator/server/state_store/slots.py:616-624`: `backend_engineer`, `quant_dev`, `infra`, `ui_developer`,
> `data_engineering` and plain unset/`worker` **all collapse to the same `planning` dispatch group and the same worker
> pool** — `assigned_role` only selects which role-prompt file the worker is handed, never who executes it. Keep the
> existing `assigned_role: backend_engineer` and treat the question as resolved; do not re-raise it. The zero-caller
> `SportsMatchingEngine` (`execution_service/matching_engine/sports_matching.py`) is confirmed dead code — delete it
> rather than wiring it, per the workspace no-shims rule.

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

> **RESOLVED 2026-08-08 — see OPERATOR RULING banner above.** Craft-split is a non-question (all `assigned_role` values
> route to the same dispatch pool/worker; keep `backend_engineer`). Priority: no objection raised in the ruling to the
> existing P3 — stands unchanged.

- ~~Is `backend_engineer` the right craft for the CLI wiring, or does the fixture/data-layer portion belong to
  `quant_dev`~~ — makes no operational difference; kept as `backend_engineer`.
- ~~Priority: this stays P3 ... confirm no reason to raise it.~~ — no reason raised; P3 stands.

## Codex SSOTs

`/codex/04-architecture/backtest-groups.md` (Group C definition + output contract this harness must satisfy).

## Progress Log

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid (sports tranche) — re-confirms the 2026-07-30 entry below. Live
  re-verification (execution-service HEAD 4e7f4833, 2026-08-06): `run_sports_backtest` still does not exist in
  `backtest_domains.py`, `SportsMatchingEngine` still has zero real callers — factual premises unchanged. Independently
  re-derived and corroborated by `sports_satellite_ao_dispatch_batch9_2026_08_04.md`'s 2026-08-04 orphan-analysis pass,
  which excluded all 5 todos from AO dispatch for the same per-todo gating reasons. Not re-litigated.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — self-declared scope note that explicitly says
  'sits for operator review; flip to assigned_vm: planning if/when approved for dispatch', plus an 'Open questions for
  operator sign-off before implementation dispatches' section (craft split + priority) — an established,
  still-unanswered gate; not re-litigated
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added the 3 execution-service source files this
  scope note names directly (`engine.py`, `sports_matching.py`, `backtest_domains.py`) and the decision issue.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — 5 open items, all operator questions.
- **resolve-round5-sports 2026-08-08**: RESOLVED (the operator-question part) — the "Open questions for operator
  sign-off" section is answered by the OPERATOR RULING banner (dispatch approved, craft-split is a non-question,
  `SportsMatchingEngine` confirmed dead code) added earlier this session by a concurrent agent; struck through the
  now-answered bullets. Closes round-5 sports item 2. The 5 `[BACKEND]/[DESIGN]/[SCRIPT]` implementation checkboxes
  remain open (real code not yet shipped) — left unchanged per this corpus's evidence-backed-completion rule.
