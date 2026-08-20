---
doc_type: plan
title: Code readiness T3 — features, ML and strategy
summary: >-
  Tranche 3 of the five-agent code-readiness push — makes features-service, ml-service and strategy-service code-complete. Owns both strategy-service artefacts, the 60-archetype code-completeness matrix across batch, paper and live, the wizard and config surface, weightings, risk, exposure and PnL attribution.
status: active
nature: process
asset_group: [cross-cutting]
stage: [strategy]
repos: [features-service, ml-service, strategy-service]
scope: [engineer]
tags: [code-readiness, strategy, archetypes, features, wizard, pnl, tranche-3]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/audit/results/code_completion_scope_2026_08_19.md,
    /plans/audit/results/code_readiness_allocation_2026_08_19.json,
    /codex/14-customer-journeys/commercial-model/platform-architecture.html,
  ]
created: 2026-08-19
last_updated: 2026-08-19
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 50
estimate_calibrated_ai_days: 20
locked_by:
locked_since:
context_scope:
  [
    /plans/epics/system_readiness_master.md,
    /plans/audit/results/code_completion_scope_2026_08_19.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
supersedes:
superseded_by:
depends_on:
source: >-
  Operator directive 2026-08-19 — allocate every active plan and issue across five parallel agents and drive the four
  client artefacts to code-ready, excluding manifest migration and data backfills.
assigned_role: backend_engineer
effort: max # multi-day autonomous tranche — 30-40 todos spanning several repos, cross-tranche contract edges
drift_direction: advance-code
---

# Code readiness T3 — features, ML and strategy

> **Tranche 3 of 5.** Owned repos — **features-service, ml-service, strategy-service**. Allocated corpus —
> **77 docs** (25 spine, 0 excluded as data-movement), **338 open todos**
> at authoring. You are one of five agents running in parallel on disjoint repos.

**Two of the four artefacts are entirely yours** (`strategy-service-deep-dive.html`,
`strategy-service-walkthrough.html`). The headline number to move is archetype code-completeness — measured
2026-08-19 at ~6 ready / ~47 not_ready / ~7 unverified per mode, with only **32 of 60 archetypes having a v2 engine
registered at all**. Note the operator ruling: archetypes may remain pending REAL-DATA TESTING, but they must be
**code-ready for batch, paper and live**. Registration and wiring are in scope; a passing backtest is not.

## The goalpost — what "done" means (operator ruling 2026-08-19)

Everything in this tranche is **complete in code**. The ONLY things that may still be pending when this plan closes:

1. **Backfills still running** — batch data landing.
2. **Venue connectivity** — private feed and public feed, orders and trades.
3. **Market data live.**
4. **Testnets, where they exist.**
5. **Strategy archetypes code-ready for batch / paper / live — pending testing with real data.**

Anything outside those five that is not code-complete is REMAINING WORK. SSOT for the goalpost:
`/plans/epics/system_readiness_master.md` § "Definition of done".

**The acceptance test is the artefacts.** These four client-sendable documents must stop carrying `pending`,
`planned`, `partial`, `not built` or `unverified` on any claim that is not one of the five above:

- `/codex/14-customer-journeys/commercial-model/platform-architecture.html`
- `/codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html`
- `/codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html`
- `/codex/14-customer-journeys/commercial-model/strategy-service-walkthrough.html`

Their status markers carry `owner: W1`…`W22` tags binding each claim to a workstream in
`/plans/epics/system_readiness_master.md`. Closing a W-item is what clears its marker. **Never clear a marker by
editing the HTML** — the marker is derived from real state; change the state, then re-derive.

## Standing rules for this tranche — HARD

- **Do NOT run backfills, manifest migrations, corpus sweeps or GCS deletes** (operator ruling 2026-08-19). Fixing
  the manifest-writer / path-registry / capture-status **code** is IN scope; launching the data movement is NOT.
  A todo whose only remaining step is "relaunch the VM" or "apply the delete" is marked `BLOCKED-OPERATOR` and left.
- **Do NOT request or wait on API keys / credentials.** Where a real credential is missing, build the adapter and
  the full code path anyway and mark the item `BLOCKED-CREDENTIALS` — never descope it. SSOT:
  `/codex/02-data/external-data-always-available-rule.md`.
- **Edit ONLY the repos this tranche owns** (listed above). Another tranche owns every other repo, and a same-file
  edit across two agents is the one thing the workspace concurrency model forbids. Need a change in someone else's
  repo? File it via the handoff protocol below — never reach across.
- **Every claim ≤ its measurement.** A proxy (line count, exit 0, a green test, a cached `origin/`) is not the
  property. Measure it or say you did not. SSOT: `/codex/12-agent-workflow/measurement-claims-discipline.md`.
- **Commit + push + flip the checkbox in the SAME turn**, with `<repo>@<sha>` evidence. SSOT:
  `/codex/12-agent-workflow/commit-push-flip-rule.md`.
- **Ship code only via** `bash scripts/quickmerge.sh "msg" --agent --files '<paths>'` from a `quality-gates.sh`-green
  tree. Doc/plan-only changes go via `bash scripts/dev/safe-doc-push.sh`.

## Cross-tranche handoff protocol

Five agents run in parallel on disjoint repos. When your work needs a change in a repo you do not own:

1. Append a `- [ ]` todo to the OWNING tranche's plan under its `## Inbound requests` section, tagged
   `[FROM-<your-tranche>]`, naming the exact symbol/file and what shape you need.
2. Commit that plan edit via `safe-doc-push.sh` (doc-only, no code).
3. Keep working — build your side against the contract you asked for, behind a feature flag or an adapter seam if
   it does not exist yet. Do not block, and do not edit their repo yourself.

**Known blocking edges at authoring time** (T1 is upstream of everyone — it runs first and fastest by design):

- T4 delta-proxy repricer generalization → needs T1 to extend UAC `QuoteInstruction` with
  `delta` / `gamma` / `underlying_instrument_id`.
- T3 + T4 strategy→execution reference triple → needs T1 to add `reference_position` and `credit` to
  `StrategyInstructionEnvelope`.
- T5 readiness dump's execution-instruction leg (the structural reason all 864 rows read `unverified`) → needs T4
  to expose a real per-venue instruction-path check.
- T5 coverage dump at `instrument_type` / `data_type` grain → needs T2 to land those axes in `coverage.json`.

## Your allocated corpus

The full, reproducible allocation lives in `/plans/audit/results/code_readiness_allocation_2026_08_19.json`,
regenerated by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`. Every one of the 892 active plan/issue
docs is assigned to exactly one tranche, so nothing is orphaned and nothing is worked twice.

```bash
python3 -c "
import json
d=json.load(open('plans/audit/results/code_readiness_allocation_2026_08_19.json'))
for x in d['tranches']['T3-features-ml-strategy']['docs']:
    if not x['excluded_data_movement']:
        print(('SPINE ' if x['spine'] else '      '), x['priority'], x['open_todos'], x['path'])
"
```

**Work order**: `spine: true` docs FIRST, in priority order — those are the docs that back a presentation claim.
Then the tail. A doc flagged `excluded_data_movement: true` is skipped per the standing rules above; open its
todos only to confirm they are data-movement, then leave it.


## Inbound requests

> Other tranches append `- [ ] [FROM-Tn]` items here when they need a change in a repo you own. Work them at the
> priority they state — another agent is blocked on each one.

- [ ] [FROM-T1] P0. **Counterparty-facing surface for `strategy-service`** — T1 re-triaged its own plan's "External
      API surface" section 2026-08-20 and found this targets a repo T1 doesn't own.
      `platform-external-api-walkthrough.html` §02 states strategy-service has no counterparty-facing surface at
      all today; its real endpoints are admin-token-gated internal tooling (registry reads, restriction-profile
      router, operational-mode flip). §25 (owner: W22) additionally found "a workspace-wide search found no
      internal messaging — Pub/Sub or otherwise — connecting strategy-service's decisions to execution-service
      today, and no direct API client either" — the only live instruction path is manual
      (`ManualOperationHandler → LiveOrchestrator.execute_instruction()`). Two halves, likely joint with T4: (1) the
      messaging bridge (UTL `EventTransport`, strategy publishes its instruction stream, execution subscribes —
      the same pattern market data already uses), (2) the counterparty-facing HTTP/WebSocket surface itself. A
      matching item is filed on T4's `## Inbound requests` for the execution-subscribing half — don't let either
      side stall waiting on the other.
      **Correction + scoping, 2026-08-20 (investigated, deliberately NOT built this session — see reasoning
      below)**: the "no internal messaging" finding is TRUE for the general case but needs one correction — a
      narrow instance of exactly this bridge already exists and works end-to-end for 3 strategy families
      (`CARRY_AND_YIELD`, `ARBITRAGE_STRUCTURAL`, `STAT_ARB_PAIRS`, the "Group B" multi-leg `AtomicInstruction`
      mechanism): `strategy_service/engine/strategies/v2/live_routing.py::publish_atomic_instruction` (real
      production caller: `cli/handlers/group_b_handler.py`) publishes via UTL `EventTransport`;
      `execution_service/v2/atomic_instruction_router.py::route_atomic_instructions` subscribes and calls
      `AtomicLegExecutor` directly — ruled + shipped 2026-07-28
      (`plans/active/issues/prediction_arb_live_execution_bridge_2026_07_20.md`). **This is the exact pattern to
      mirror for the general case, not a design question** — the architecture (InMemoryTransport for paper,
      Pub/Sub for live, same code path) is already proven.
      **Correction to this todo's OWN prior entry, same day**: the paragraph originally here (written earlier
      today) claimed "no live/paper caller of the orchestrator's tick loop was found" — that was wrong, from an
      incomplete grep (missed a match my own search pattern should have caught). Traced further and found the
      real driver: `strategy_service/engine/backtest/runner.py::GroupBRunner` (despite the "Group B" name, its
      own docstring: "maintains a non-shadow `V2EngineOrchestrator` — emitted instructions are captured and
      benchmark-filled inline", `backtest_group` is just an internal harness-taxonomy label, not an archetype
      restriction — it's registered against whichever instance(s) a caller wires in, per-archetype, not scoped to
      3 families). `paper_run_handler.py` (the actual `--operation paper-run` T+1-cron caller) instantiates it
      too, for a promoted `carry_staked_basis` instance — confirming this IS the real live/paper driver.
      **The actual, now-precise gap**: `GroupBRunner._process_tick()` (`runner.py:244-270`) calls
      `orchestrator.on_tick(...)`, then UNCONDITIONALLY runs every returned instruction through
      `self._fill_engine.settle(...)` — a **local `BenchmarkFillEngine` simulation**, regardless of mode. The
      ONLY real external publish is a narrow, explicit exception: `if instruction is AtomicInstruction AND
      execution_mode is LEADER_HEDGE: self._atomic_publisher(instruction)` (`__init__`'s own comment: "Wire-in
      seam 2026-07-30 ruling... `None` (default) keeps the runner byte-identical for non-multi-leg / legacy
      backtests — no forward, no event-spine touch"). So the gap isn't a missing driver — it's that this driver's
      own 2026-07-30 wiring deliberately scoped the real-publish branch to ONLY `LEADER_HEDGE AtomicInstruction`;
      every other `StrategyInstructionEnvelope` (all ~56 non-Group-B archetypes) is always benchmark-filled
      locally and never reaches an external transport in ANY mode today, paper or nominally-live. This is now a
      well-scoped, buildable extension (mirror the existing `atomic_publisher` seam for the general instruction
      type) rather than an open architectural question — **but two things need resolving first, not guessed**:
      (1) whether "live" mode should SKIP local benchmark-fill settlement entirely once a real publish path
      exists (so real venue fills come back instead of a simulated one), or run both — settling AND publishing —
      which would be a real double-count risk; (2) `build_paper_run_attribution`/`build_paper_run_passive`
      (`engine/backtest/paper_run_attribution.py`/`paper_run_passive.py`) — grepped and found ZERO production
      callers, only their own file + 2 test files. **This also corrects an earlier claim from this session's own
      PnL investigation** (session 4, this plan's W9/W10/W13 row) that called these "the shared batch=paper=live
      code path... confirmed real, wired" — that was a second-hand subagent claim relayed without independently
      re-verifying the literal call site, and it does not hold up against a direct grep. Whatever function
      `GroupBRunner`/`PaperRunHandler` actually uses for attribution was NOT identified in this pass either — a
      real open item, not resolved here. The counterparty-facing HTTP/WebSocket surface (the second half of the
      original ask) still needs separate real product/security design (auth model, rate limits, what data is
      exposed), not attempted here.
- [ ] [FROM-T1] P0. **Do NOT wait on `StrategyInstructionEnvelope.reference_position` / `credit` — they are gated on an
      unresolved operator ruling, not in progress.** T1 investigated them and deliberately did not implement them, so this
      edge will NOT clear on its own; plan around it rather than blocking. The shape both tranche plans describe
      (flat `reference_position: dict[venue, Decimal]` plus a flat `credit`, "same shape as the existing price
      leg") was SUPERSEDED the same day it was written: the source issue carries a later operator revision ruling
      it incomplete — it resolves the venue axis but not the INSTRUMENT axis, since one strategy instance holds a
      universe of instruments, so a single envelope-level triple can only ever describe ONE instrument's reference
      state. The replacement (`references: list[InstrumentReferenceEntry]`, nesting the per-venue dict one level
      deeper) is published in that issue under the heading **"Proposed shape (illustrative — not finalized; this
      is what needs resolving, not what's decided)"**, immediately followed by **"Open questions for the operator
      — do not resolve unilaterally"** (Q12-Q16). Implementing the todo's literal text would re-commit the exact
      scalar-shape regression the operator caught; implementing the vector would answer five questions explicitly
      reserved for the operator.
      **Two points ARE settled whichever way Q12-Q16 land, so you can design against them today**: `credit` is
      OPTIONAL (a "flavor", never a mandatory field — pure-passive, fire-immediately and patient-then-escalate are
      all valid consumers), and it is strategy-COMPUTED and strategy-OWNED, with execution merely consuming it.
      Evidence: `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md`.
- [ ] [FROM-T1] P1. `strategy_instructions` writer/registry DIVERGENCE — your repo's own
      `strategy_service/engine/core/gcs_storage_service.py::write_instructions` hardcodes its own blob-path
      string (`f"strategy_instructions/client_id={client_id}/strategy_id={strategy_id}/day={date_str}/
      instructions.parquet"`) and bypasses UTL's `PATH_REGISTRY`/`build_path()` entirely. T1 just added a
      REQUIRED `mode={mode}` segment to the `strategy_instructions` `path_template` (path_registry_dead_mode_
      kwarg fix, 2026-08-20 — batch/paper/live rows were colliding on the same object path for
      `execution_fills`/`positions`/`strategy_instructions`/`pnl_attribution`/`strategy_orders`), but since this
      writer never calls `build_path()`, it will keep writing the OLD mode-less path regardless — the registry
      now describes a shape this writer does not produce. **Not fixed by T1**: this is your repo, and the fix
      shape depends on how `write_instructions`'s `client_id`/`date_str` params relate to a `mode` your service
      already has in scope (confirm before assuming — not measured by T1). Two options: migrate this writer to
      `build_path("strategy_instructions", ..., mode=mode)` so it's byte-parity with the registry, or if there's
      a reason this writer must stay hardcoded, at minimum add the `mode=` segment to its own literal string so
      readers going through the registry (currently zero real call sites, per `registry.py`'s own comment, but
      that could change) don't silently miss real data. Evidence: `unified_trading_library/config_interface/
      paths/registry.py` (`strategy_instructions` row + its own comment on this writer being the "unwired stub"
      case), `plans/active/issues/path_registry_dead_mode_kwarg_execution_fills_positions_strategy_instructions_
      pnl_attribution_2026_08_15.md`.
- [ ] [FROM-T1] P2. **Migrate `staked_basis.py`'s `_STAKING_PROTOCOL_CHAIN` off its own hardcoded dict onto UAC's
      new `get_chain_for_protocol()`.** Registry SSOT hardening 2026-08-16 todo 6 measured that your 8-entry
      lowercase protocol→chain map (`strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py:186`)
      genuinely duplicates data UAC already has: 7 of your 8 entries resolve exactly via UAC's existing
      `PROTOCOL-CHAIN` venue-suffix convention every `ALL_DEFI_VENUES` entry already follows — the data was
      never missing, only queried through the wrong mechanism. `unified_api_contracts.registry.venue_constants
      .get_chain_for_protocol(protocol: str) -> str | None` is that mechanism, shipped
      `unified-api-contracts@0d7afa29e`, tested against all 8 of your exact values (verbatim-copied into
      `tests/unit/test_get_chain_for_protocol.py` as the cross-repo parity check — if you ever change one of
      your 8 values, that test will fail and tell you the two sides drifted).
      **Not a blind swap**: `coinbase_staking` is the one entry that does NOT resolve via a real DeFi venue —
      measured zero matches in `ALL_DEFI_VENUES`, because it's Coinbase's custodial retail staking product, not
      an on-chain protocol. `get_chain_for_protocol()` handles it via a documented, explicit exception
      (`_NON_DEFI_STAKING_PROTOCOL_CHAIN`), so the function's return value for it is unchanged (`"ethereum"`) —
      you can swap the call site without special-casing anything on your end.
      **What to do**: replace `_STAKING_PROTOCOL_CHAIN.get(config.staking_protocol.lower(), "")` with
      `get_chain_for_protocol(config.staking_protocol) or ""` (same fallback-to-empty-string behavior on a
      genuine miss), then delete `_STAKING_PROTOCOL_CHAIN` itself — `_ALLOWED_CHAINS`/`ALLOWED_CHAINS` stay,
      they're a separate concern (which chains this strategy permits, not protocol→chain resolution). This is
      T3's own repo so T1 cannot make this edit. Evidence:
      `/plans/active/registry_ssot_hardening_2026_08_16.md` todo 6, `unified-api-contracts/unified_api_contracts
      /registry/venue_constants.py::get_chain_for_protocol`.

## Todos

### Archetype code completeness — the headline number

- [x] [BACKEND] P0. Register a v2 engine for all 60 `StrategyArchetype` members — **59/60 done**;
      `ARCHETYPE_ENGINE_REGISTRY` 32 -> 59. `strategy-service@1bda20fb` (source) + `strategy-service@3eb96f35`
      (portfolio package + tests). Registered the 22 shipped-but-withheld engines (17 `VOL_*`, 5 granular
      `MARKET_MAKING_*`) and BUILT the 5 that had no engine at all (`Vol0dtePinRiskEngine` + the whole `PORTFOLIO`
      family over a shared no-trade-band sleeve-rebalance spine reusing `portfolio_allocator.normalise_weights`).
      Each also got a Kelly tier, `target_universe` seeds (3 rows/archetype, +81) and — for the 5 new ones — a param
      schema. **The 60th, `ARBITRAGE_MEV_SANDWICH`, is deliberately NOT registered**: a POLICY exclusion (the firm
      does not extract value from other users' pending swaps; `sandwich_theoretical.py` is a post-hoc adverse-selection
      tracer, not an engine), asserted by `test_sandwich_theoretical.py` +
      `test_phase8_archetype_factory_smoke.py`. Evidence: `get_archetype_engine_class()` resolves all 59;
      `tests/unit` 3757 passed on the landed tree.
- [x] [BACKEND] P0. Give every archetype a `PARAM_SCHEMA_REGISTRY` entry — **done**, `strategy-service@37989f99`.
      Registry 40 -> 59; `check_archetype_schema_coverage().missing_schema` is empty and
      `_SCHEMA_COVERAGE_BASELINE_MISSING_SCHEMA` shrank to `frozenset()`. Every default is the ENGINE default cited
      to its real `*_param(...)` read at `file:line` (`test_param_schema.py` asserts the two agree, so a guessed
      default fails). `CARRY_FUNDING_DISPERSION` — the one this todo named as confirmed missing — is included. Two
      pairs share a param surface by construction: `CARRY_BASIS_DATED`/`_INV` (`CarryBasisDatedEngine`) and
      `CARRY_BASIS_PERP_INV`/`CARRY_RECURSIVE_BORROW_LENDING_ONLY` (`CarryRecursiveStakedEngine`). The baseline
      constant is KEPT, not deleted: empty is what makes the gate fail immediately on the next archetype registered
      without a schema.
- [x] [BACKEND] P0. Give every archetype a `target_universe` catalog entry — **done**, `strategy-service@1bda20fb`.
      `catalog_expansion.py` seeds all 27 newly-registered archetypes (table-driven; 3 rows each, +81 rows, 549 ->
      630). Measured: `specs_for_archetype()` non-empty for all 59 registered archetypes; the
      `target_universe_catalog` leg of `/archetype-code-completeness` is 177/177 ready, 0 not_ready.
- [x] [BACKEND] P0. Give every archetype an allocator-rank entry — **done**,
      `strategy-service@583a2a79` + `unified-trading-pm@a4609ff2be`. Promoted the archetype -> allocator table out of
      a private dict in `cli/handlers/paper_universe.py` into a shared SSOT
      (`engine/strategies/v2/archetype_allocator.py`), and in doing so found + fixed a real bug: 5 purpose-built
      `AllocatorArchetype.<VALUE>_RANK` engines were REGISTERED but UNREACHABLE — nothing selected them, so their
      archetypes silently got equal-weight `FIXED` instead of the metric each ranker was built for. Wired 4:
      `YIELD_STAKING_SIMPLE`, `YIELD_ROTATION_LENDING`, `CARRY_RECURSIVE_STAKED`, `CARRY_BASIS_DATED`. Deliberately
      left `CARRY_FUNDING_DISPERSION_RANK` unreachable (its archetype already maps to `CARRY_FUNDING_RANK` and both
      plausibly apply — a real ranking decision needing an operator DECISION, not a wiring oversight) and did NOT give
      the `*_INV`/`*_DATED` engine siblings their sibling's ranker (opposite-sign basis — the long-side metric would
      rank them backwards). Both boundaries pinned by `test_archetype_allocator.py` so they stay deliberate.
      Resolution is TOTAL (`resolve_allocator` never raises); the skill's `allocator_rank` leg is rewritten from
      ready-or-unverified to always-ready, naming the resolved allocator — absence of a dedicated ranker is a
      documented policy (equal weight), not an unknown.
- [x] [BACKEND] P0. Wire mode-specific dispatch for every archetype across **batch, paper AND live** — **done**,
      `strategy-service@9c11ab8b` (paper) + `strategy-service@583a2a79`/`unified-trading-pm@a4609ff2be` (batch verdict
      correction). **Found a real, long-standing production bug measuring this**: `paper_run_handler.py`'s
      subscription fallthrough read `config["perp_venue"]`/`config["perp_instrument"]` directly — most archetypes
      have no perp leg, so paper mode raised `KeyError` for **46 of the 59** factory-registered archetypes (~19
      predated the 2026-08-19 registration wave; registering 27 more widened it from 19 to 46). Built
      `paper_subscription.py`, a declarative per-archetype registry: all 59 declare a `(venue, instrument)`
      subscription identity, all **276/276 catalogue rows resolve** (proven, not just declared), with fallback key
      chains for genuine within-archetype heterogeneity (cross-venue rows name `leader_venue`; DeFi-LP rows `pool`;
      Deribit options-MM rows only `underlying`) and book-shaped archetypes (`PORTFOLIO_*`) subscribing at their
      `slot_label` since they trade a set, not one instrument. Separately, `batch_dispatch`'s `unverified` verdict
      was WRONG about the system: `batch_rerun.py` resolves via `archetype_for_slot_label()` over the immutable
      `TARGET_UNIVERSE`, and all 630 catalogue rows round-trip through it — measured, not assumed.
- [x] [BACKEND] P0. Re-run `/archetype-code-completeness` and drive it to zero `not_ready` — **done**,
      `strategy-service@37989f99`. **`not_ready` = 0 in all three modes** (was 47). All three mode-invariant legs
      are 177/177 ready: `engine_factory`, `param_schema`, `target_universe_catalog`. Remaining rows are
      `unverified`, not failing, and each NAMES its missing check rather than passing silently — which is what this
      todo required: `allocator_rank` (153 rows) is deliberately `unverified` because 8 GENERIC allocators may
      legitimately serve an archetype (a ruling, not wiring — its own todo above); `batch_dispatch` (42) /
      `paper_dispatch` (47) have no clean registry lookup yet so the skill emits a dated agent-audit record instead
      of guessing (the mode-dispatch todo below); `ARBITRAGE_MEV_SANDWICH` (1/mode) is `excluded_by_policy`, not a
      gap. **Zero `not_ready` does NOT mean the matrix is fully verified** — it means nothing FAILS a real machine
      check. The unverified population is different work and must not be reported as done.
- [x] ✅ [BACKEND] P1. Fix the DeFi catalog/engine config-key contract drift for the 5 remaining families
      (sports, ML-directional, market-making, vol). **Re-verified 2026-08-20**: the sweep is not "start the
      vol-family method on the other 3 families" as this plan's deferred table framed it — the systemic test
      (`test_all_catalogued_archetypes_construct_and_fire.py`) already parametrizes over the ENTIRE
      `ARCHETYPE_ENGINE_REGISTRY` (all 59 archetypes, not vol-scoped), so the sweep has been comprehensive and
      automated all along. Ran it clean (`GCP_PROJECT_ID` unset locally caused 3 unrelated DeFi bucket-naming
      failures — set it, re-ran, 143 passed / 3 xfailed). The 3 xfails are a `strict=True` allow-list, not
      silently-passing gaps: `RULES_DIRECTIONAL_EVENT_SETTLED` (9 rows, needs a real per-row
      `'<feat>:<op>:<val>|<outcome>|<stake_frac>|<max_odds>'` DSL string — no row emits one) and
      `MARKET_MAKING_EVENT_SETTLED` (6 rows, needs real per-exchange `back_instrument`/`lay_instrument` Betfair/
      Matchbook instrument IDs), both dated 2026-07-24, both explicitly "NOT fixed here... a design decision, not
      a rename" in the test's own allow-list comment — genuine remaining work, but `[DESIGN]`/`[STRATEGY]`-tagged
      (inventing plausible-looking threshold values or instrument IDs for live financial strategies would be
      fabrication, not a fix). One more open cross-repo design item in the issue doc
      (`defi_catalog_engine_config_key_contract_drift_2026_07_23.md:774`): the pollable-candidate-registry feed
      for `LIQUIDATION_CAPTURE`/`ARBITRAGE_MEV_LIQUIDATION_BUNDLE` has its transport shape ruled (2026-08-09) but
      needs a human design pass on features-service's per-candidate feature-naming before it can be broken into
      AO-dispatchable todos. Evidence:
      `/plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`.
- [ ] [BACKEND] P1. Build the venue/currency curtailment mechanism — `allowed_venues` is dead code today, and the
      catalog and `archetype_leg_spec_seeds` describe the same domain with no cross-check. Evidence:
      `/plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`.
- [ ] [BACKEND] P1. Generalize the venue-eligibility gate beyond `carry_and_yield`'s perp-hedge leg — the other 8
      in-scope families get `frozenset()` today. Evidence:
      `/plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md`.

- [ ] [BACKEND] P1. Delete entries from `clients_yaml_coverage.PENDING_CROSS_REPO_WAIVER` as T5 lands each
      archetype's `clients.yaml`/`clients_waiver.yaml` in `deployment-service`. Filed as an inbound request on T5's
      plan (`unified-trading-pm@96d5d2e1f1`); the frozenset is the shrinking worklist. 27 entries at authoring.
- [ ] [BACKEND] P2. Audit the other 3 engine families named in the config-key contract-drift issue (sports,
      ML-directional, market-making) the same way the vol family was audited on 2026-08-19 — by making the systemic
      construct-and-fire test exercise them and seeing which no-op. That method found 2 real drifts (8 keys) the
      A4 gate structurally cannot catch, because A4 compares the CATALOGUE against the schema and both sides can
      agree while the ENGINE reads a third spelling. Evidence:
      `/plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`.

### W6 — wizard, config and scaffolding

- [ ] [BACKEND] P0. Make strategy-service fully configurable from the wizard — rank-buffer hysteresis, no-trade
      band, beta-hedge overlay and vol-target-at-book-layer are all unimplemented. **2 of 4 shipped 2026-08-20
      — `strategy-service@ed9ff26875`**: rank-buffer hysteresis (`rank_buffer_k` on
      `BaseRankAllocator`, wired to `CarryFundingDispersionRankAllocator`) and the no-trade band
      (`GuardRailConfig.no_trade_band`), both real and tested but not yet reachable from a live caller — the
      `ClientAllocatorInstance`/`PortfolioAllocatorService` layer that would construct them with a real default
      has no confirmed production construction site anywhere in the repo (a separate, larger gap). Beta-hedge and
      vol-target-at-book-layer remain genuinely unbuilt — seam investigation done (`LegPortfolioState` doesn't
      exist, `target_net_delta` is per-leg not book-level, `portfolio_risk_gate.py` is vol-options-scoped, not a
      general fit): no existing seam to hook onto, needs a new cross-archetype aggregation layer designed first,
      correctly not attempted given financial-correctness stakes. Also **not** "from the wizard" yet for either
      shipped item — no UI/schema exposure, just the underlying mechanism. Evidence:
      `/plans/active/strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md`.
- [ ] [BACKEND] P0. Enforce that strategy-service reads ONLY processed data — epic definition-of-done item.
- [ ] [BACKEND] P1. Land the service config ownership and instruction contract remainder — typed `client_configs`
      schema, the schema-mechanism decision, the gate-assertion decision and the service-boundary contract writeup.
      Evidence: `/plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`.

### W7 — centralisation and anti-drift

- [ ] [BACKEND] P1. Migrate the 69 module-level reference-shaped constants to one of the four centralisation
      destinations. Evidence: `/plans/active/strategy_service_centralization_fixes_2026_08_16.md`.
- [ ] [BACKEND] P1. Finish wiring the asset-group-agnostic position-risk core.
- [ ] [BACKEND] P1. Complete the lazy/scoped loading refactor on the strategy-service side. Evidence:
      `/plans/active/lazy_scoped_loading_refactor_2026_08_16.md`.

### W9, W10, W13 — balances, risk, exposure, PnL

- [ ] [BACKEND] P0. **Tracked in a pre-existing sibling plan, not duplicated here** — found 2026-08-20:
      `/plans/active/strategy_service_centralization_fixes_2026_08_16.md` already owns this exact convergence
      (dated 2026-08-16, before this plan existed) with the full reconciliation already done (A and B are not
      independent — B's DeFi path already consumes A's `DeFiHealthAggregator.aggregate()` output; the genuinely
      redundant piece is `positions_health.py`'s separate re-derivation) and real remaining work tracked there:
      10 done / ~14 open todos, `sequential: true` (a real chain — route the live feed, switch archetypes onto
      it, extend the data model). Work this from that plan, not as a fresh T3 todo — the two plans would
      otherwise silently duplicate the same fix.
- [ ] [BACKEND] P0. Build stale-producer detection on the live path. If strategy-service stops publishing,
      execution-service does not detect it — the kill switch has 5 armed conditions and none is "an internal service
      went silent". Evidence: `/plans/active/producer_silence_flatten_protocol_2026_08_14.md` (23 open),
      `/plans/active/issues/live_path_has_no_stale_producer_revocation_2026_08_14.md`.
- [ ] [BACKEND] P0. Implement W9 account balances as the single strategy I/O.
- [ ] [BACKEND] P0. Collapse the three competing PnL surfaces to one wired path. **Re-verified 2026-08-20, claim
      mostly holds but needs correction before acting**: `compute_pnl` (`pnl/engine/orchestrator.py:426`) IS
      confirmed dead — only test callers (`tests/pnl/unit/test_engine.py`, `test_service_startup.py`), the real
      CLI compute path routes to `calculate_execution_alpha` instead. **But before deleting it**: it computes
      hold-day interest + sports-settlement PnL (routes to `SportsPnLEngine`) + standard per-instrument
      breakdown — confirm none of those three are uniquely-only-here before removing, don't just delete a
      formula that might not be duplicated elsewhere. The "execution-alpha compute_handler is dead with zero
      readers" half of the claim is **wrong, correct it**: `compute_handler.py` is reachable via the registered
      `--operation pnl-attribution` CLI operation (`service_entry.py:814-822,1008`) — code-live, not dead — but
      no cron/systemd/Terraform trigger was found anywhere in the repo, unlike `--operation paper-run` which is
      documented as the T+1 cron's Stage A (`service_entry.py:827-834`). Real decision needed: wire
      `pnl-attribution` into a cron trigger, or delete the orphaned CLI operation if `paper_run_attribution.py`
      already supersedes it. **Correction, session 6, same day**: the "`paper_run_passive.py`/
      `paper_run_attribution.py` confirmed real" claim below was WRONG — a second-hand subagent relay taken at
      face value rather than independently re-verified against the literal call site. Direct grep (session 6):
      `build_paper_run_attribution(` and `build_paper_run_passive(` have ZERO production callers anywhere in the
      repo — only their own definition files + 2 test files. The real live/paper driver is
      `engine/backtest/runner.py::GroupBRunner` (traced in the "Counterparty-facing surface" inbound-request
      item above) — it does NOT call either of these two functions; what it actually uses for attribution was
      not identified. "They ARE the shared batch=paper=live code path" is retracted — unverified, do not cite it.
      HWM
      confirmed compliant in the live path (`param_schema.py:1361,1371` uses UAC's `hwm_ledger` explicitly on
      TWR/Notional/PnL-recovery); the one raw-equity HWM implementation found (`pnl_monitor.py:70,201-202`) has
      no confirmed production instantiation site (dead code, not a live violation) and mock_data_provider's is
      explicitly D2-smoke/mock-only. SSOT: `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`.
- [ ] [BACKEND] P0. Build PnL attribution across every dimension the artefacts describe (W13) — currently
      "specified, not built".
- [ ] [BACKEND] P1. Fix the interest-accrual wrong engine and banned formula. Evidence:
      `/plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`.
- [x] ✅ [BACKEND] P1. Fix DeFi leverage archetypes reading health factor from the wrong source. **Already resolved
      before this todo was written** — all 11 items in the issue doc's todo list are `[x]`, including the operator
      ruling (2026-08-17) and the `DeFiHealthAggregator` reconciliation (2026-08-18, `[AGENT]`). Found 2026-08-20
      already at this state, predating this plan. Evidence:
      `/plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md`.
- [ ] [BACKEND] P1. Close the DeFi gas net-cost partial wiring gap — gas cost is silently dropped today. Evidence:
      `/plans/active/issues/defi_gas_net_cost_partial_wiring_gap_2026_08_17.md`.

### W16, W18 — preflight and canonical output paths

- [ ] [BACKEND] P0. Build the universal fail-closed startup readiness check — a strategy missing a required input
      fails REGISTRATION, not a live run. Missing or stale data fails closed by default (RULED).
- [ ] [BACKEND] P0. Land canonical output paths for strategy-service (W18), coordinating with T1's `PATH_REGISTRY`
      `mode=` fix so batch/paper/live no longer collide.
- [ ] [BACKEND] P1. Build trigger, latency-tracing and staleness-SLA mechanisms (W16) — "specified, not built".

### Position adapters and venue coverage

- [x] ✅ [BACKEND] P0. Close the position-adapter versus execution-connector asymmetry — strategy-service ships 8 DeFi
      position adapters against execution-service's ~16 live protocol connectors. **Already resolved before this
      todo was written**: found 2026-08-20 that the issue doc's own 20-item todo list is essentially all `[x]`
      (Lido/Marinade/Kamino/Jupiter adapters shipped 2026-08-15/16; generic-first EVM+SPL read/write paths shipped
      `strategy-service@4dbbd98e1d`/`execution-service@2b92d6ac69`; simulation-only connectors now fail-closed on
      live per `execution-service@9946ba5a3`), all dated 2026-08-14 through 17, predating this plan. Only 2 items
      remain, both non-agent-executable: `[AGENT] P2` wire real write paths for Solblaze/Jito Restaking (Solana
      Anchor non-ABI programs, no SDK dependency — judged too risky to hand-roll; execution-service, T4's repo) and
      `[OPERATOR] P2` a disclosure decision on out-of-mandate adapters (betfair/ibkr/polymarket). Evidence:
      `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`.
- [x] ✅ [BACKEND] P0. Fix CeFi live venue-string dispatch, broken for 9 of 12 major venues — the position-adapter
      factory hand-rolls a legacy bare-token venue table never extended to the canonical form. **Already fixed
      before this todo was written** — `strategy-service@9027c2f5a9` (factory match arms) +
      `strategy-service@c44322ddc0` (routed through the shared `split_venue_base_and_suffix` helper), both
      2026-08-17 by an AO worker (`slot-29·planning`), predating this plan's 2026-08-19 authorship. Discovered
      already-done 2026-08-20 while starting this todo — the plan text was stale from birth, never checked
      against existing work. Only 2 low-priority P3 leftovers remain open in the issue doc (dead-code
      `routing.py::_map_venue_to_ccxt` with zero production callers; a metadata-only `capabilities.py` table
      drift) — neither blocks live dispatch. Evidence: `/plans/active/issues/cefi_live_venue_string_dispatch_broken_2026_08_16.md`.
- [x] ✅ [BACKEND] P1. Resolve the instrument-universe hot-swap position-state contradiction — codex says restart
      required, shipped code hot-swaps live with no restart or error. **Not an agent todo**: the issue doc's sole
      follow-up is `[OPERATOR] P2` — rule option A (add a safe-field guard, mirroring the strategies-domain
      pattern) vs option B (confirm the hot-swap is intentional, correct the codex "restart required" row). Found
      2026-08-20 already scoped this way, predating this plan. Nothing for an agent to build until the operator
      rules A or B. Evidence: `/plans/active/issues/instrument_universe_hotswap_position_state_safety_unruled_2026_08_14.md`.
- [x] ✅ [BACKEND] P2. Resolve the orphan-coverage design gaps — `strategy_orders` / `strategy_positions` /
      `strategy_pnl` have NO live writer at all. **Already resolved before this todo was written**: items 1-4 of
      the issue doc's 5-item todo list are done (RULED 2026-08-05, sinks/paths shipped). Item 5's mechanical
      sub-parts (data-sink config, `PATH_REGISTRY` path fix) also shipped; the one remaining piece — wiring a real
      caller — is `[OPERATOR] P2`, blocked on whether inventing one would fabricate the corpus rather than wire up
      a real producer. Found 2026-08-20 already at this state, predating this plan. Evidence:
      `/plans/active/issues/strategy_ml_orphan_coverage_design_gaps_2026_08_03.md`.

### features-service and ml-service

- [ ] [BACKEND] P0. Fix the 5 of 7 on-chain feature groups writing byte-identical zero-feature-column parquets
      stamped `captured=True`, plus the 6 false-`captured` rows with zero GCS objects, plus the 4-repo
      `feature_group` vocabulary split. **Re-verified 2026-08-20 — narrower than titled, correctly NOT
      agent-attempted**: the false-`captured`-rows + consolidator portions already shipped 2026-07-30
      (`features-service@d8a643a0`). The one remaining piece (build 5 new protocol-specific MTDS chain-field
      collectors — ltv/liquidation_threshold/reward_rate/flash_loan_liquidity/health-factor per on-chain protocol)
      has been independently re-confirmed FIVE separate times (na-eligibility-audits 07-30, 08-03, 08-06, 08-16,
      round11-sweep 08-09) as needing a human sizing/scoping decision — which on-chain data source per
      protocol/field — not a bare mechanical build. Not attempted here for the same reason; a sixth re-derivation
      of this conclusion would waste the exact effort those audits exist to prevent. The vocabulary-split half
      also explicitly needs an operator ruling per the doc's own summary. Evidence:
      `/plans/active/issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`.
- [x] ✅ [BACKEND] P0. Remove the banned-vendor dependency — `corporate_actions` is sourced exclusively from
      `polygon_corporate_actions_adapter.py` and Massive-fka-Polygon.io is a FLEET-WIDE banned vendor. **SHIPPED
      2026-08-20 — `features-service@fa78040e30`**, unblocked mid-session by operator ruling R6
      (`/plans/audit/results/code_completion_scope_2026_08_19.md` § "Ruling 6 — Yahoo Finance"), which landed
      AFTER this todo was first written re-verified-not-attempted above — re-checked LDR mid-session per operator
      instruction and found the ruling. Built `yfinance_corporate_actions_adapter.py` (no credentials needed,
      mirrors the already-live `yfinance_earnings_adapter.py` pattern), wired it into
      `corporate_actions_handler.py`/`corporate_actions_calculator.py`, deleted the Polygon adapter +
      `_polygon_types.py` entirely (no shim). Honestly documented coverage gap: yfinance's
      `Ticker.dividends`/`Ticker.splits` don't carry pay_date/record_date/declaration_date/dividend_type the way
      Polygon did — left `None`/`UNSPECIFIED` rather than fabricated; `split_from`/`split_to` are derived from
      yfinance's own ratio via `Fraction`, not invented. Rewrote both test files (63 unit tests green) and the
      Polygon live-API integration test → a yfinance equivalent. Also corrected
      `/codex/02-data/tradfi-databento-sourcing-ssot.md`'s stale "COMPLETE ACROSS ALL REPOS" banner (a THIRD
      occurrence of this exact claim being wrong — `pm@ebaa20df4d`). **Still open, correctly not mine**: whether
      yfinance's coverage is complete/reliable enough vs Polygon's was never independently validated — the ruling
      decided the VENDOR, not the coverage-adequacy question; real diligence work if it matters later. Evidence:
      `/plans/active/issues/features_service_corporate_actions_polygon_io_banned_vendor_2026_08_18.md`.
- [ ] [BACKEND] P0. Build opportunity-detection feature producers for the 3 code-shipped MEV engines (BACKRUN,
      JIT_LIQUIDITY, LIQUIDATION_BUNDLE). `features.get(key, 0.0)` silently defaults, so these engines are
      registered and "shipped" but can never fire. **Re-verified 2026-08-20, correctly NOT agent-attempted**: the
      issue doc's own author already scoped the 3 remaining `[FEATURES]` calculator-build todos as needing "a
      design decision on exact derivation, not a blind guess" (BACKRUN's spread/swap-size derivation from
      `dex_pool_swap_flow`+`cross_venue_spreads`, JIT_LIQUIDITY's pending-swap-size producer, LIQUIDATION_BUNDLE's
      two upstream gaps including an unbuilt live margin-health scanner). Inventing plausible-looking MEV
      opportunity-detection formulas for live trading strategies would be fabrication, not a fix — matches this
      session's beta-hedge/vol-target caution. 2 of the doc's todos were already extracted to a dispatched satellite
      batch (archived 2026-08-20). Evidence:
      `/plans/active/issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md`.
- [ ] [BACKEND] P1. Give the calendar domain manifest visibility — `economic_events` / `forexfactory` /
      `corporate_actions` / `earnings_results` never call `record_captured`. Evidence:
      `/plans/active/issues/features_service_calendar_domain_manifest_tracking_gap_2026_08_18.md`.
- [x] ✅ [BACKEND] P1. Fix the `delta_one` dependency checker resolving the wrong PREDICTION bucket token —
      `_format_template_vars` does a naive `asset_group.lower()` with no abbreviation map, but PREDICTION's real
      bucket uses `pred`. **Already resolved before this todo was written — traced 2026-08-20**: the naive
      `_format_template_vars` lives in `unified_trading_library/core/dependency_checker.py:258` (UTL, T1's repo —
      confirmed still naive there, unfixed and correctly not mine to touch) but features-service's
      `DependencyChecker` subclass (`features_service/delta_one/app/core/dependency_checker.py:151-166`) overrides
      `_resolve_gcs_path` to special-case `market-data-processing-service` — the one real upstream bucket
      dependency this checker has — through `_resolve_mdps_bucket()`, which correctly routes
      `asset_group_lower == "prediction"` to `kind="market-data-tick-prediction"` (the real `-pred-prd-` bucket)
      instead of the naive UTL template. `features-service@09be801b` (cited in the issue doc's own remaining P3
      item). **One caveat found, not blocking**: the override only fires when `not self.test_mode` — a
      `test_mode=True` checker falls through to the base (naive) path, so PREDICTION test-mode bucket resolution
      may still be wrong; not chased further since it's a lower-severity test-only path, not live/prod. All 3
      remaining open items in the issue doc are VM-launch/benchmark-measurement work (relaunch a benchmark,
      investigate an OOM), explicitly out of scope for this tranche's "no VM launches / backfills" rule. Evidence:
      `/plans/active/issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md`.
- [x] ✅ [BACKEND] P2. Verify and fix the MVP universe filter settlement-suffix claim ("dropped every CeFi perpetual")
      — MEASURE it first, it was not independently verified. **Already resolved before this todo was written**:
      all 5 items in the issue doc are `[x]`, dated 2026-07-27 through 2026-08-06 (`features-service@a9429cba`
      confirmed + fixed the residual; `deployment-service@c1e0481` shipped the tarball-freshness default flip).
      Found 2026-08-20 already at this state, predating this plan. Evidence:
      `/plans/active/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md`.
- [ ] [BACKEND] P2. Complete feature-formula versioning. SSOT: `/codex/02-data/feature-formula-versioning.md`.

### Close-out

- [ ] [AGENT] P1. Work the non-spine tail of this tranche's allocation to zero open todos or an explicit
      `BLOCKED-*` tag on every remainder.
- [ ] [AGENT] P0. Post-phase codex audit across `/codex/09-strategy/` for every contract changed.
- [ ] [AGENT] P0. Confirm every marker in the two strategy-service artefacts now reads live, or is one of the five
      allowed pending states. Re-derive; never hand-edit the HTML.

## Progress Log

> Append-only. One entry per shippable unit — what you changed, the `<repo>@<sha>`, and what you MEASURED (not what
> you assume). This log is the handoff document if this agent's context ends and a fresh one resumes the tranche.

- 2026-08-19 — Plan authored. Allocation derived by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`
  against the 892-doc active corpus. No code work started yet.

- 2026-08-20 — **Archetype registration wave. `strategy-service@1bda20fb` + `strategy-service@3eb96f35`.**

  MEASURED, `/archetype-code-completeness` on the landed tree (`3eb96f35`, clean, == origin):

  | leg (of 180 rows) | before | after |
  | --- | --- | --- |
  | `engine_factory` | 96 ready / 84 not_ready | **177 ready / 0 not_ready** / 3 excluded |
  | `target_universe_catalog` | 96 ready / 84 not_ready | **177 ready / 0 not_ready** / 3 excluded |
  | `param_schema` | 105 ready / 75 not_ready | 120 ready / 57 not_ready / 3 excluded |
  | overall BATCH | 6 ready / **47 not_ready** / 7 unverified | 6 ready / **19 not_ready** / 1 excluded / 34 unverified |

  `ARCHETYPE_ENGINE_REGISTRY` 32 -> 59; `TARGET_UNIVERSE` 549 -> 630 rows; `PARAM_SCHEMA_REGISTRY` 35 -> 40.
  `tests/unit` 3757 passed. The remaining 19 `not_ready` are EXACTLY the schema-less-but-registered set — every
  other mode-invariant leg is clean, so the next unit is a single well-defined job.

  What was actually wrong, and is worth not re-learning:

  * **22 of the 28 "missing" engines were never missing.** They were code-written AND unit-tested, deliberately
    withheld from the registry by a policy requiring a passing backtest first. The matrix read that absence as
    "no engine exists". Three tests asserted the withholding as an invariant; all three are now
    `_assert_code_complete` (registration + schema + catalog + Kelly together, so a partial wiring cannot pass).
    **Never infer "is it backtested" from registry absence again.**
  * **Two real engine<->schema key drifts**, found by making the systemic construct-and-fire test exercise the newly
    registered engines: `VOL_SPREAD_STRUCTURES` read `atm_call`/`otm_put`/... (6 keys) and `VOL_VARIANCE_SWAP` read
    `atm_straddle_call`/`_put` (2) — spellings their own `PARAM_SCHEMA_REGISTRY` entries never declared. Sibling
    `VOL_RATIO_SPREAD` already used the schema names, so the schema was right and the engines had drifted. Any slot
    configured through the wizard surface would have silently no-op'd forever. **A4 cannot catch this class**: it
    compares CATALOGUE keys against the schema, and both can agree while the engine reads a third spelling. The
    method that found it — make the engine actually fire on a plausible tick — is the one that generalises.
  * **`ARBITRAGE_MEV_SANDWICH` is a policy exclusion, not a gap.** Added an `excluded_by_policy` verdict state to
    the skill so it reports on every leg rather than sitting permanently red. Honest denominator: 59 in scope, 1
    out of scope by decision. Adding an entry to `POLICY_EXCLUDED_ARCHETYPES` is a policy claim needing a cited
    decision + an enforcing test — never a way to silence a red cell.
  * **A4 gate improved, baseline shrunk 166 -> 106** (-60): taught it `key_template` hierarchy prefixes and exempted
    `venue`/`instrument_type`/`asset_group` (structural keys stamped on every row by the shared constructors, never
    read by a named engine `_param` call). Every retired entry was a false positive the module docstring had already
    predicted. Its "119 pairs" comment was itself stale — it measured 166.

  **Shipping incidents — read before trusting a quickmerge result:**

  * `quickmerge.sh` **exits 0 when the re-gate FAILS**. Three consecutive attempts reported exit 0 and landed
    NOTHING (lint; codex-compliance; the empty-string-fallback ratchet). Only checking origin's tree caught it.
  * Worse, `--files` given a DIRECTORY path stages nothing for it, silently. `1bda20fb` therefore landed the source
    registration WITHOUT the `portfolio/` package or the test updates, and quickmerge's recovery pass then reverted
    the unstaged test edits in the working tree. LDR was briefly inconsistent: `factory.py` referenced an absent
    module and the old tests asserted the opposite of the new code. Repaired by `3eb96f35` with every path named
    individually. Note `safe-doc-push.sh` REFUSES a wildcard outright; quickmerge accepting a directory and
    dropping it is the more dangerous behaviour because it produces a PARTIAL commit.
  * **`git diff FETCH_HEAD` reported no differences during the broken window** — because the local test edits had
    been reverted to match origin, so both sides agreed on the wrong content. Exit code, "✅ Landed", clean
    `git status` and an empty diff ALL passed. Only a per-file `git cat-file -e FETCH_HEAD:<path>` found it.

  Cross-tranche: 27 `clients.yaml`/waiver files filed to T5 (`unified-trading-pm@96d5d2e1f1`);
  `PENDING_CROSS_REPO_WAIVER` in strategy-service is the shrinking worklist.

- 2026-08-20 — **Param schemas for the last 19 archetypes. `strategy-service@37989f99`.**

  MEASURED on the landed tree (content-verified in origin, not just file presence — the file pre-existed):

  | leg (of 180 rows) | after registration wave | now |
  | --- | --- | --- |
  | `engine_factory` | 177 ready / 0 not_ready | 177 ready / 0 not_ready |
  | `param_schema` | 120 ready / **57 not_ready** | **177 ready / 0 not_ready** |
  | `target_universe_catalog` | 177 ready / 0 not_ready | 177 ready / 0 not_ready |
  | overall, per mode | 19 not_ready | **0 not_ready** |

  `PARAM_SCHEMA_REGISTRY` 40 -> 59. `_SCHEMA_COVERAGE_BASELINE_MISSING_SCHEMA` -> `frozenset()`, kept not deleted:
  an empty baseline is what makes the A1 gate fire on the NEXT archetype registered without a schema, and keeps its
  message saying "a NEW archetype has no schema". Full `quality-gates.sh` green before the push; 1755 v2 tests.

  Method worth reusing: every default was extracted from the engine's real
  `*_param(self.params, "<name>", <default>)` call with its `file:line`, then written table-driven.
  `test_param_schema.py` asserts the declared default equals the engine's, so this is not a place where a
  plausible-looking guess survives — it fails the gate.

  **Headline: 0 not_ready per mode, from 47 at plan authoring.** State it precisely — it means no archetype FAILS a
  machine check. 51-53 rows/mode remain `unverified` and are genuinely different work: `allocator_rank` is a
  per-archetype RULING (generic allocator vs dedicated rank engine), and batch/paper dispatch need a registry lookup
  built before they can be checked at all. Neither is closed by this commit.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)

## Deferred work after 2026-08-20 (session 2)

**Archetype code-completeness is now FULLY CLOSED** — every leg, every mode: 59/59 ready (or `excluded_by_policy`
for `ARBITRAGE_MEV_SANDWICH`). Zero `not_ready`, zero `unverified`. Started this tranche at ~6 ready / ~47 not_ready
/ ~7 unverified per mode. This was the plan's headline metric and its entire "Archetype code completeness" todo
section is now done.

| Area | State | Next concrete step |
| --- | --- | --- |
| Archetype code-completeness (all 7 legs, all 3 modes) | **DONE — 59/59 ready every leg/mode** | Nothing. |
| `CARRY_FUNDING_DISPERSION` vs `_DISPERSION_RANK` ambiguity | **DONE — operator decided 2026-08-20**: wired to `CARRY_FUNDING_DISPERSION_RANK` (matches the archetype's own cross-sectional design). `CARRY_FUNDING_RANK` is now the pinned-unreachable legacy alias instead. `strategy-service@<see Progress Log>`. | Nothing. |
| DeFi/vol/sports/ML/MM config-key contract drift | **DONE — sweep was already comprehensive, not vol-scoped.** The systemic construct-and-fire test parametrizes all 59 registered archetypes, confirmed green (143 passed/3 xfailed with `GCP_PROJECT_ID` set). 2 genuine remaining bugs, both `[DESIGN]`-blocked not mechanical: `RULES_DIRECTIONAL_EVENT_SETTLED`, `MARKET_MAKING_EVENT_SETTLED` (real per-row threshold/instrument-ID decisions, not derivable). | Nothing agent-executable. The 2 xfails need a human to pick real DSL thresholds / Betfair-Matchbook instrument IDs — don't fabricate plausible-looking values for live financial strategies. |
| W6 wizard / config | Untouched | rank-buffer hysteresis, no-trade band, beta-hedge overlay, vol-target-at-book-layer. The PORTFOLIO engines already ship a working no-trade band (`rebalance_band`) — reuse that shape. |
| W9/W10/W13 PnL, risk, exposure | **Genuinely open, re-scoped, with a correction.** Session 4's "`paper_run_attribution.py`/`paper_run_passive.py` confirmed real, shared batch=paper=live path" claim is RETRACTED (session 6) — zero production callers found on direct grep, was an unverified second-hand relay. The real live/paper driver is `GroupBRunner` (`engine/backtest/runner.py`); what it uses for attribution is unidentified. `compute_pnl` confirmed dead (formula may still hold unique sports/interest logic — verify before deleting); `compute_handler`'s CLI op is code-reachable but has no deployment trigger anywhere in-repo. HWM confirmed compliant in the live path. | Identify `GroupBRunner`'s real attribution path (not `paper_run_attribution.py`/`paper_run_passive.py` — those are dead code candidates now, not the answer) before touching PnL surfaces further. Decide `compute_handler`'s fate and confirm `compute_pnl`'s 3 capabilities are covered elsewhere before retiring it. |
| W16/W18 preflight + canonical paths | Untouched | Fail-closed startup readiness check; canonical output paths (needs T1's `PATH_REGISTRY` `mode=` fix). |
| Position adapters / venue coverage | **DONE — whole section found already resolved** (all 4 sub-items: CeFi dispatch, asymmetry, hot-swap, orphan-coverage), all shipped 2026-08-14 through 17 by prior sessions, predating this plan's 2026-08-19 authorship. This plan section was written stale from birth. Residue is entirely non-agent-executable: 2 `[OPERATOR]` decisions (instrument hot-swap A/B, out-of-mandate adapter disclosure) + 1 `[AGENT]` Solana-SDK item in execution-service (T4's repo). | Nothing. If picking this back up, it's an operator-decision chase (hot-swap A/B, disclosure), not new engineering. |
| features-service | **Swept 2026-08-20 — every item already correctly gated, not "untouched-and-actionable" as this row implied.** Onchain featureless shards: mechanical part shipped 2026-07-30, remaining scope independently reconfirmed 5x as needing human data-source scoping (not a build task). `corporate_actions`: zero live blast radius (built-but-never-run) + genuinely `[OPERATOR]`-gated vendor decision. Calendar manifest gap: gated on a `[REVIEW]` shard-atom design decision. `delta_one` PREDICTION-bucket bug: already fixed (`features-service@09be801b`); one test-mode-only caveat noted. Settlement-suffix (P2): already fully resolved. | Nothing agent-executable remains in this section. If revisited: chase the operator decisions (corporate_actions re-sourcing, calendar shard-atom question), or scope the on-chain MTDS collectors as their own dedicated human-sized work. |
| ml-service | Confirmed 2026-08-20: the MEV opportunity-detection gap is strategy-service + features-service scoped (3 calculators reading `features.get(key, 0.0)`), not a separate ml-service item — no distinct ml-service-only gap found in this tranche's allocated corpus. Correctly not agent-attempted: the issue doc's own author scoped all 3 calculator-builds as needing "a design decision on exact derivation, not a blind guess." | Nothing agent-executable found. ml-service itself was not otherwise touched this session — its allocated corpus may still have unswept non-spine docs (see the Close-out section's non-spine-tail todo). |
| Both strategy-service artefacts | Not re-derived | Re-derive markers only AFTER the W-items close; never hand-edit the HTML. |

**Cross-tranche**: T5 still owes 27 `clients.yaml`/waiver files (`PENDING_CROSS_REPO_WAIVER` in strategy-service is
the shrinking worklist) and the two `quickmerge.sh` defects
(`/plans/active/issues/quickmerge_exit_zero_on_failed_regate_and_silent_directory_files_2026_08_20.md`).

**Recommended next item (superseded 2026-08-20 session 3 — see Progress Log)**: position adapters/venue coverage
and config-key drift are both now DONE (found already-resolved or already-comprehensive). What's left with real
agent-executable scope: **W6 wizard/config** (untouched — rank-buffer hysteresis, no-trade band, beta-hedge
overlay, vol-target-at-book-layer; the PORTFOLIO engines' `rebalance_band` is a reusable shape) and **W16/W18
preflight + canonical paths** (untouched, blocked on T1's `PATH_REGISTRY` `mode=` fix for the paths half, but the
fail-closed startup readiness check has no such dependency). The PnL item is real but narrower than it reads —
see its row above; `compute_handler`'s cron-trigger decision and `compute_pnl`'s formula-uniqueness check are the
actual next actions there, not a from-scratch unification.

## Progress Log — 2026-08-20 session 2

- **Wired 5 orphaned rank allocators + corrected 2 wrong skill verdicts. `strategy-service@583a2a79`,
  `strategy-service@9c11ab8b` (already landed pre-checkpoint), `unified-trading-pm@a4609ff2be`.**

  MEASURED, final state, every leg of `/archetype-code-completeness`, all 3 modes:

  | leg | before this entry | now |
  | --- | --- | --- |
  | `allocator_rank` | 24 ready / 153 unverified | **177 ready / 0 unverified** |
  | `paper_dispatch` | 12 ready / 47 unverified | **59 ready / 0 unverified** (from session start of this checkpoint) |
  | `batch_dispatch` | 17 ready / 42 unverified | **59 ready / 0 unverified** |
  | **overall, every mode** | ready=6-8 / unverified=42-53 | **59/59 ready, 0 unverified, 0 not_ready** |

  Two skill verdicts were **wrong about the system**, not just cautious — measuring settled both:
  1. `allocator_rank`'s `unverified` reasoning ("which generic allocator is configured is not statically derivable")
     was true of the old private-dict lookup, not of the system: resolution is total
     (`archetype_allocator.resolve_allocator` never raises) and `FIXED` is a documented equal-weight policy.
  2. `batch_dispatch`'s `unverified` reasoning ("batch_rerun's replay path may still cover it; not independently
     confirmable") was provably false: `archetype_for_slot_label()` round-trips all 630 catalogue rows. Measured,
     not assumed.

  **Real bug found wiring the first one**: `ALLOCATOR_ARCHETYPE_REGISTRY` implements 9 dedicated `*_RANK` engines;
  the private dict selecting one mapped only 4. Five purpose-built rankers were dead code — their archetypes
  silently earned equal-weight `FIXED` instead of the metric built for them. Wired 4; left the 5th
  (`CARRY_FUNDING_DISPERSION_RANK`) deliberately unreachable pending an operator decision (see deferred table).

  **Shipping this required real incident handling — read before your first ship of a session on a busy checkout:**

  1. **Host-wide QG contention (7-18 concurrent `quality-gates.sh` processes measured)** caused a resource-timing
     gate to fail ("`Quality gates must complete in <300s`") on content that was independently verified clean
     (ruff, full pytest run, separately). Diagnosed as environmental, not content — retried, landed clean next
     attempt. **The absolute 300s wall-clock budget doesn't account for host-wide load** — worth its own issue if it
     recurs.
  2. **A DIFFERENT live session is sharing this exact slot's checkout right now** (the SessionStart hook warned
     about this at the very start of the session — it was real, not a false positive). Their in-progress
     agent-orchestrator plan edit showed up as unfamiliar dirty content under MY git identity (`slot-4·laptop` — the
     identity is derived from the slot path, not the process, so two sessions in one slot commit as the same
     "person"). **Never touched their file.** Confirmed via `git log -1 --format=%an` that the file's last real
     author was consistent with a peer session, and left it exactly as found.
  3. **My own unstaged edits got swept into `git stash` TWICE** by concurrent sessions' "pre-reconcile quarantine"
     autostashes — quickmerge's own forensic tooling caught the second instance itself ("Do NOT cite `<sha>` as
     evidence for these paths — it does not carry them... recover from the stash BEFORE re-running") and named the
     exact stash + recovery commands. **Recovery method**: `git stash show --stat stash@{N}` to confirm the stash
     is EITHER cleanly mine OR bundles a peer's file alongside mine (both happened, once each), then
     `git checkout stash@{N} -- <my-paths-only>` — never a blanket `pop`/`apply`, which would have also restored
     the peer's file into my working tree.
  4. **`--isolated` is the documented fix for exactly this symptom** ("pass it once edits keep reverting under
     contention, that IS the fix") — used it for the final successful ship after two content losses on the same
     two files. Content-verified in origin afterward (grepped for a distinctive string in `origin`'s blob, not just
     checked the SHA matched — a matching SHA after a contended reconcile is not proof of content, only of Git
     state).

  **The general lesson, stated once so it isn't re-learned**: on a heavily contended shared checkout, `local HEAD
  == origin HEAD` and `git status` clean are NOT proof your change landed — a peer's autostash can quarantine your
  unstaged edits while a `git pull --ff-only` cleanly fast-forwards past them, leaving both checks green while your
  content is sitting in an unnamed stash. The only real proof is grepping ORIGIN's blob content for something
  distinctively yours, every time, on a contended checkout.

## Progress Log — 2026-08-20 session 3

**Operator decision landed**: `CARRY_FUNDING_DISPERSION` → `CARRY_FUNDING_DISPERSION_RANK`, not the previously-wired
legacy `CARRY_FUNDING_RANK` alias. Evidence for the recommendation: the archetype engine's own docstring
(`funding_dispersion.py`) describes a flat cross-sectional rank with no venue/LST hierarchy, arriving as an
upstream `funding_rank_pct` feature — near-verbatim the same language as `CarryFundingDispersionRankAllocator`'s
own docstring, while `CARRY_FUNDING_RANK` is explicitly a legacy alias for the unrelated hierarchical
`CarryBasisPerpRankAllocator`. **Shipped — `strategy-service@06253843`**, content-verified at origin. First ship
attempt hit a real line-length lint failure (fixed); a second, harmless artifact along the way: a file-watcher
system-reminder caught the working tree mid-quickmerge showing the OLD content — this was quickmerge's own
internal stash/checkout mechanics transiently touching the file, not a real revert or a peer-session collision (no
stash existed afterward, no other session's quickmerge was touching this repo, and the final staged/pushed content
was correct throughout). Pinning test
inverted: `test_only_the_ambiguous_rank_engine_remains_unreachable` → `test_only_the_legacy_alias_rank_engine_remains_unreachable`,
now pinning `CARRY_FUNDING_RANK` (the harmless deprecated alias) as the sole unreachable rank engine instead.

**Major finding — the entire "Position adapters and venue coverage" plan section was stale from birth.** All 4 of
its todos (asymmetry, CeFi dispatch, hot-swap contradiction, orphan-coverage) turned out to already be resolved by
prior sessions dated 2026-08-14 through 17 — before this plan was even authored on 2026-08-19. Discovered while
starting the CeFi-dispatch todo the user prioritized: `git log` on the target file showed a commit
(`strategy-service@c44322ddc0`, `slot-29·planning`, 2026-08-17) already fixing the exact bug the todo described.
Pulling that thread through the section's 3 sibling issue docs found the same pattern in all of them — 20/20,
1/1, and 4/5 todo items already checked `[x]` respectively, each with real shipped SHAs. **Root cause: this plan
section was authored without checking `git log` / the issue docs' own todo-completion state against the plans that
were actively being worked in parallel the week before.** The general lesson: before writing a plan todo from an
issue doc's headline finding, read the issue doc's OWN todos/Progress-Log section first — a finding can be true
and its fix can already be shipped, and only the plan text is what's stale. All 4 todos corrected in place (flipped
to `[x]` with the discovery evidence, not silently deleted) rather than left to mislead the next session into
redoing already-done work. Zero net-new code was needed for this entire plan section; what shipped this session
(2 commits) is the checkbox-currency-correction, plus the one genuine ranker decision above.

## Progress Log — 2026-08-20 session 4

**Real code shipped**: W6 overlays — `strategy-service@ed9ff26875` (rank-buffer hysteresis + no-trade band, both
new tested guard-rail mechanisms; `funding_dispersion.py`'s misleading overlay-status docstring corrected). Full
detail in the sibling plan (`strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md`), summarized in
this plan's own W6 todo.

**Second major stale-plan sweep, this time the features-service/ml-service section.** Same method as session 3's
position-adapter sweep (read the cited issue doc's own todos/Progress-Log before treating a plan headline as
current), applied to all 6 items in "features-service and ml-service". Result: **every single item was either
already resolved or correctly gated on a human decision that predates this plan** — none were genuinely
agent-actionable "just go build it" work:

- Delta_one PREDICTION-bucket bug: already fixed (`features-service@09be801b`) via a features-service-side
  override (`_resolve_mdps_bucket`) that special-cases the one real upstream dependency — the underlying naive
  method it works around (`_format_template_vars`) lives in `unified_trading_library` (T1's repo), confirmed still
  naive there but correctly not touched (cross-repo, and already effectively mitigated at the real call site).
- Universe-filter settlement-suffix claim (P2): fully resolved, 5/5 todos done, dated back to 2026-08-06.
- Onchain featureless shards: mechanical piece shipped 2026-07-30; the remaining scope (building 5 new
  protocol-specific MTDS chain-field collectors) has been independently re-confirmed FIVE times by different
  na-eligibility-audit passes as needing a human data-source-per-protocol scoping decision, not a mechanical build.
  A sixth re-derivation of that same conclusion would have wasted exactly the effort those audits exist to save.
- MEV opportunity-detection producers (BACKRUN/JIT_LIQUIDITY/LIQUIDATION_BUNDLE): the issue doc's own author
  already scoped all 3 calculator-builds as needing "a design decision on exact derivation, not a blind guess" —
  inventing plausible MEV-opportunity formulas for a live strategy would be fabrication. Also confirmed this is
  NOT a distinct ml-service item as this plan's deferred table previously implied — it's strategy-service +
  features-service scoped, no separate ml-service gap found.
- Calendar domain manifest-tracking gap: gated on an unresolved `[REVIEW]` design question (do calendar
  data_types even belong in the Layer-1 EXPECTED universe) that must land before the mechanical `record_captured`
  wiring makes sense.
- `corporate_actions` banned-vendor removal: confirmed ZERO live production blast radius (built-but-never-run, no
  scheduler/Cloud-Run-job/orchestrator dispatch anywhere) and genuinely `[OPERATOR]`-gated on a vendor
  data-quality decision (yfinance vs. a paid contract), not a credentials gap — did not unilaterally pick a
  vendor for live financial data without that sign-off.

**The pattern holds across two independent sweeps now (session 3: position adapters/venue coverage; session 4:
features-service/ml-service)**: this plan's per-item descriptions were written from issue-doc HEADLINES without
reading those docs' own todo-completion state or their own author's design-decision gating. All corrections are
now in place with evidence rather than left to mislead. **Practical implication for whoever resumes this plan**:
before starting ANY remaining unchecked todo in this file, grep the cited issue doc's own `## Todos` and
`## Progress Log` sections first — the plan text alone is not reliable evidence of current state.

**What's left with genuinely new agent-executable scope in this plan, after two full sweeps**: none found this
session. Everything remaining is either `[OPERATOR]`-gated (corporate_actions re-sourcing, calendar shard-atom
question, `CARRY_FUNDING_DISPERSION_RANK`-class rulings), needs real design work before any code can be written
(beta-hedge/vol-target book-layer overlays, MEV calculators, onchain MTDS collectors), or depends on another
tranche (T1's `PATH_REGISTRY` `mode=` fix for W16/W18's canonical-paths half). The Close-out section's non-spine-tail
sweep and the two-artefact re-derivation remain legitimate next steps, but are sweep/verification work, not new
builds.

## Progress Log — 2026-08-20 session 5

**Operator directive mid-session: "did you recheck plans at LDR because several rulings landed today."** Had not —
pulled LDR (17 commits behind) and found a real, materially-relevant batch: `PATH_REGISTRY {mode}` ruled (migrate,
not quarantine — the W16/W18 blocker), `corporate_actions` vendor ruled (Yahoo Finance — my own P0 item marked
`[OPERATOR]`-gated last session), plus a large new architecture doc
(`/codex/04-architecture/cross-domain-state-fabric.md`, R1-R27) with real strategy-service implications (position
vectors R22, kill-switch declare/detect split R21) not yet built anywhere. **Lesson carried forward**: mid-session
LDR re-pulls for operator rulings are not optional on a long session — this workspace ships rulings continuously
and a plan's "blocked" state can go stale hours into the same session, not just across sessions.

**Collision risk found and handled, not silently worked around.** A separate, freshly-created 8-tranche
"state-fabric reconciliation audit" dispatch
(`/plans/audit/results/state_fabric_reconciliation_dispatch_2026_08_20.md`) has its OWN T3 (features-service +
greeks-service) / T4 (strategy-service) numbering, colliding with this plan's T3 identity, and its own
collision-check safety item was unchecked before dispatch. Live AO-backlog check for a dispatched job failed
(orchestrator `:8765` connection refused — infra issue, not routed around). Per operator decision: continued this
session's work (audit-only tranches don't refactor code, worst case is a finding filed against a stale snapshot —
a cheap, familiar class of problem this session has fixed a dozen times already) and left an honest partial-data-
point note on that dispatch doc's collision-check item rather than either checking it off (would overclaim — I only
know my own slot's state) or ignoring it (the next reader gets no signal at all).

**Shipped**: `features-service@fa78040e30` — Yahoo Finance replaces the banned-vendor Polygon.io
`corporate_actions` adapter (full detail on the flipped checkbox above). `unified-trading-pm@ebaa20df4d` — corrected
`tradfi-databento-sourcing-ssot.md`'s stale removal-complete banner (third time this exact claim needed correcting).

## Progress Log — 2026-08-20 session 6

**Worked the `## Inbound requests` section for the first time** — 2 of T1's `[FROM-T1]` items were small, well-scoped,
mechanical fixes; both shipped `strategy-service@8a7f80e8`: (1) `gcs_storage_service.py::write_instructions` was
hand-rolling its own `strategy_instructions` path, bypassing T1's `mode=` PATH_REGISTRY fix — now routes through
`build_path()`, byte-parity with the read side (`pnl/adapters/domain_adapter.py`), zero behavior change since it had
zero callers. (2) `staked_basis.py`'s 8-entry hardcoded `_STAKING_PROTOCOL_CHAIN` dict deleted, replaced with UAC's
`get_chain_for_protocol()` — a cross-repo parity test on the UAC side already pins all 8 of this repo's exact values.

**The P0 item (counterparty-facing surface + messaging bridge) got a real, evidence-based re-scoping, not a build.**
Traced the actual code: a working publish→subscribe→execute bridge already exists via UTL `EventTransport` but is
scoped narrowly to 3 multi-leg strategy families (`AtomicInstruction`/"Group B"). For the other ~56 archetypes
(`StrategyInstructionEnvelope`, the general type), the live/paper caller of the orchestrator's tick loop could not be
located — one candidate (`Phase6Driver`) is itself unwired dead code, the other (`V2BatchHarness`) is batch-only. This
is a genuine open question (not yet a design decision, not yet buildable) rather than a straightforward "add a publish
call" — routes real trading decisions once live, so traced rather than guessed. Full detail + the recommended next
trace (follow `paper_run_attribution.py`'s real call chain) on the flipped-but-still-partially-open checkbox above.
Did not attempt the HTTP/WebSocket counterparty surface (needs real product/security design, not mine to invent).

**Same-session correction, immediately after**: did the recommended trace myself rather than leave it for later,
and found a DIFFERENT answer than the "no live/paper caller found" claim just written above — corrected in place
on both the inbound-request item and the W9/W10/W13 deferred-table row, not left to mislead. Real driver:
`GroupBRunner` (`engine/backtest/runner.py`); `paper_run_attribution.py`/`paper_run_passive.py` have zero
production callers and are retracted as "the shared path." Lesson worth stating plainly: a subagent's relayed
claim ("confirmed real, wired") was carried forward and re-asserted twice this session without independently
re-checking the literal call site each time — the fix each time was a direct grep, seconds of work. Cite a
subagent's finding as ITS finding until independently re-verified, not as an established fact.
