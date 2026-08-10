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
last_updated: "2026-08-08"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
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

> **RECLASSIFIED 2026-08-08 (na-eligibility-audit, sports tranche, round7 RECLASSIFY sweep)** — flipped
> `assigned_vm: NA → planning` / `execution_scope: local-only → orchestrator-agent`. The 2026-08-08 OPERATOR RULING
> banner above explicitly says "dispatch APPROVED" and resolves both blocking design forks that kept this doc NA: the
> craft-split question (non-question, all `assigned_role`s route to the same pool) and todo 3's
> `SportsMatchingEngine`-vs-`L0Matcher` fork (ruled: delete `SportsMatchingEngine`, confirmed dead code). Conflict-check
> (§3 of `ao-dispatch-batch-naming-and-conflict-check.md`): checked
> `/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md` (the only other active `assigned_vm: planning` doc in
> `parent_epic: sports_master` touching sports consumers) — it lists this doc under `related:` and its Progress Log
> records investigating (not claiming) the craft-split question, but its own Todos (panel/arbitrage/ML/Betfair/
> catalogue-browser-dependency sections) do not include `run_sports_backtest`/Group-C harness work; no other
> batch/finalize doc or the consolidated-closeout doc claims this ground either
> (`grep -rl "run_sports_backtest\|SportsMatchingEngine" plans/active/*.md` — zero hits outside this doc and
> doc-inventory/index files). Clear to dispatch. Paired finalize sibling:
> `sports_group_c_execution_backtest_harness_2026_07_21_finalize_2026_08_08.md`.

**This is now an AO-dispatched plan (`assigned_vm: planning`).** It scopes the work AND is now the dispatch target — the
5 implementation checkboxes below are the AO backlog content.

## Why this is needed (not just "run the strategy backtest again")

Per `/codex/04-architecture/backtest-groups.md`, Group C ("execution alpha") is a distinct concern from Group B
("strategy alpha") — it fixes the strategy instruction stream and tunes/measures the EXECUTION side (algo choice, venue
routing, fill realism) against a matching engine with realistic microstructure. `L0Matcher`
(`execution_service/matching_engine/engine.py:290`) already generically routes `BookmakerCategory`/`"BET"` sources to
`BookType.L0_TOB` (`engine.py:813`) — fill-or-reject at top-of-book, size-checked — which is exactly the microstructure
model Group C needs for sports. That means the matcher-side prerequisite is already done; what's missing is purely the
CLI wiring, same shape as the 3 domains that already have it.

## Todos

- [x] ✅ [BACKEND] P3. Add `run_sports_backtest(args, config, config_path) -> int` to
      `execution_service/cli/backtest_domains.py`, mirroring `run_defi_backtest`'s structure (simplest of the three — no
      lateral-feed preloading needed): `setup_backtest(...)` → `_create_backtest_engine(...)` →
      `run_and_save_backtest(...)`. Needs an `extract_sports_instrument` extractor (new, alongside
      `extract_cefi_instrument`/`extract_tradfi_defi_instrument` in `engine/backtest/runner.py`) that resolves a
      sports/prediction fixture+market instrument from config instead of a CeFi/TradFi symbol. —
      execution-service@5e80d437. `run_sports_backtest` mirrors `run_defi_backtest` (no lateral-feed preloading) and
      wires `extract_sports_instrument` (fixture id from `strategy.fixture_id` / `strategy.instrument.instrument_id` /
      `strategy.instrument_id` / V2 `instruments` list — `instrument_id = fixture_id` convention). Full dispatch chain
      wired so the harness is reachable, not dead code: `DomainType.SPORTS`/`PREDICTION`, explicit
      `asset_group: sports|prediction` in `get_asset_group_from_config`, `backtest.py` domain map + date-skip category,
      and the engine-core extractor branch. 10 new unit tests (8 extractor + 2 runner wiring) + updated
      `test_all_members` (5 domains). `quality-gates.sh` full green on the committed HEAD (sentinel=37c83f3d; shipped as
      5e80d437 + test-fix 4ceaec57).
- [x] ✅ [BACKEND] P3. Wire a data source: reuse the Group-B fixture dataset shipped in `strategy-service@9a7de7f8`
      (`tests/fixtures/sports_odds/premier_league_arb_sample.py`, 3 synthetic EPL ticks) as the first hermetic input —
      port or import it into execution-service's catalog/data layer rather than inventing a second fixture format.
      Confirm whether `CatalogManager` needs a new sports/prediction data-type branch or can consume the same
      synthetic-tick shape CeFi uses. — execution-service@51bee662a. Ported `premier_league_arb_sample.py`
      (byte-compatible, same format — port, not import, per the no-service↔service-dep tier rule) to
      `execution_service/data/fixtures/sports_odds/`, and added `execution_service/data/sports_fixture_source.py`
      projecting it into the harness's hermetic input shapes: `strategy.instruction_data` (direction gated by value-bet
      `min_edge`, benchmark = decimal odds) + synthetic L0 TOB `QuoteTick`s registered through `CatalogManager`, plus a
      `build_sports_fixture_backtest_config()` hermetic config builder. **CatalogManager question confirmed: NO new
      branch needed** — CatalogManager is a domain-agnostic Nautilus `ParquetDataCatalog` wrapper; the sports
      synthetic-tick shape is the same QuoteTick shape CeFi registers (verified by write+read-back in
      `tests/unit/test_sports_fixture_source.py`). 5 new unit tests; QG full green on 3d3069cd; shipped as 51bee662a.
- [x] ✅ [DESIGN] P3. Deleted `SportsMatchingEngine` per operator ruling at
      `/plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md` L54 (2026-08-08): option (a). Resolve the
      `SportsMatchingEngine` vs `L0Matcher` duplication found while scoping this
      (`execution_service/matching_engine/sports_matching.py` — zero callers anywhere in `execution_service/` or
      `tests/`, always fills at requested odds with no rejection/queue model, i.e. Group-B-shaped behavior sitting in
      the matching-engine module). ~~Either: (a) delete it as unused dead code once confirmed truly orphaned, or (b) if
      it was meant to replace `L0Matcher` for sports specifically, explain why and wire it in instead of `L0Matcher`.~~
      Ruled: confirmed dead code, delete it (no shims) rather than wiring it — do not re-litigate. Do this BEFORE
      building the CLI below so the harness targets the right matcher (`L0Matcher`). — execution-service@70d18a44
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

- **2026-08-10 (slot 19, backend_engineer)**: Todo 2 shipped — `execution-service@51bee662a`. Ported the Group-B fixture
  (`strategy-service@9a7de7f8`'s `premier_league_arb_sample.py`, 3 synthetic EPL ticks) into
  `execution_service/data/fixtures/sports_odds/` (byte-compatible — port, not import, per the T4 no-service↔service-dep
  tier rule; reuses the exact same fixture format rather than inventing a second). Added
  `execution_service/data/sports_fixture_source.py` wiring it as the first hermetic input for `run_sports_backtest`: (1)
  `build_sports_fixture_instruction_data()` projects each tick's prediction into `strategy.instruction_data` (direction
  gated by the archetype `min_edge` 0.03 — 2 of 3 ticks fire, 1 no-trades; benchmark_price = home decimal odds), (2)
  `build_sports_fixture_quote_ticks()` projects the odds into synthetic L0 TOB `QuoteTick`s, (3)
  `register_sports_fixture_catalog()` writes them through `CatalogManager`, (4) `build_sports_fixture_backtest_config()`
  assembles a hermetic `run_sports_backtest`-consumable config (L0_TOB venue, embedded instruction stream,
  `data_source: local`). **CatalogManager question confirmed**: it is a domain-agnostic Nautilus `ParquetDataCatalog`
  wrapper — it stores Nautilus data objects (QuoteTick/TradeTick) keyed by instrument, so sports consumes the SAME
  synthetic-tick shape CeFi uses; NO new sports/prediction data-type branch needed (proven by register+read-back in
  `tests/unit/test_sports_fixture_source.py`). 5 new unit tests; QG full green on 3d3069cd.
- **2026-08-10 (slot 25, backend_engineer)**: Todo 1 shipped — `run_sports_backtest` + `extract_sports_instrument` +
  full dispatch wiring (DomainType.SPORTS/PREDICTION, domain detection, backtest.py map/date-skip, engine-core branch).
  Read the prerequisite context first: `backtest-groups.md` Group-C contract, `run_defi_backtest` as the structural
  mirror (no lateral-feed preloading), sports `instrument_id = fixture_id` convention from the sports matching surface.
  10 new unit tests + updated `test_all_members` (first QG pass caught `len(members) == 3` hard-code — fixed). QG green
  on 37c83f3d; shipped as execution-service@5e80d437 (feat) + 4ceaec57 (test fix) — re-created hashes from shared-clone
  contention, content verified identical.
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
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: **RECLASSIFY → planning.** With the operator-question
  resolution above, every prior pass's KEEP-NA rationale (2026-07-30/08-07: "self-declared scope note... an established,
  still-unanswered gate") no longer holds — the doc's own gate is answered. Flipped `assigned_vm: NA → planning`,
  `execution_scope: local-only → orchestrator-agent`, kept `assigned_role: backend_engineer` (ruling-confirmed).
  Conflict-check (§3 of `ao-dispatch-batch-naming-and-conflict-check.md`): no other active `assigned_vm: planning` doc
  in `parent_epic: sports_master` claims `run_sports_backtest`/ `SportsMatchingEngine` ground
  (`sports_taxonomy_p3_consumers_2026_08_08.md` references this doc but its own Todos don't touch execution-service's
  backtest CLI); no sibling batch/finalize doc claims it either (checked batch9/batch10, both pre-date today's ruling
  and both explicitly cite the now-resolved craft-split/SportsMatchingEngine forks as their reason for excluding this
  doc). Todo 3's remaining `(a) vs (b)` fork is also now resolved by the same ruling (delete `SportsMatchingEngine`) —
  annotated inline on that todo rather than flipped `[x]` (no commit ships the deletion yet, per the
  evidence-backed-completion rule). Todo 5 (docs/BACKTESTS.md placement) is the one item the ruling doesn't address;
  left as a real judgment call for the worker/finalize pass to resolve via precedent (do the other 3 domain runners'
  CLIs appear in that surface?) rather than blocking dispatch of the other 4 bounded todos on it. Paired finalize
  sibling authored: `sports_group_c_execution_backtest_harness_2026_07_21_finalize_2026_08_08.md`.
- **2026-08-10 (slot 4, backend_engineer)**: Todo 3 shipped — deleted `SportsMatchingEngine`
  (`execution_service/matching_engine/sports_matching.py`, 468 lines, zero callers anywhere in execution-service or
  tests) and removed its re-exports from `matching_engine/__init__.py` (BetOrder, BetStatus, MarketType, OpenBet,
  PortfolioSummary, SettlementResult, SportsMatchingEngine — all had zero importers from this package; real consumers
  import the distinct UAC types of the same names). Operator ruling 2026-08-08 option (a): delete rather than wire.
  execution-service@70d18a44.
