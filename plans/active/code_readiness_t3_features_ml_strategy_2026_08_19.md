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
    /plans/active/code_readiness_t3_progress_history_2026_08_20.md,
  ]
created: 2026-08-19
last_updated: 2026-08-20
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

- [x] ✅ [FROM-T1] P0. **Counterparty-facing surface for `strategy-service`** — the messaging-bridge half is
      SHIPPED, `strategy-service@a8b53d9cc7`. T1's "no internal messaging" finding was true for the
      general instruction type but not the whole picture: a working publish→subscribe→execute bridge already
      existed via UTL `EventTransport`, narrowly scoped to LEADER_HEDGE `AtomicInstruction` (3 families) —
      `live_routing.py::publish_atomic_instruction` → `execution_service/v2/atomic_instruction_router.py`
      (ruled + shipped 2026-07-28). Traced its real driver, `engine/backtest/runner.py::GroupBRunner` (despite
      the "Group B" name it is NOT archetype-restricted — registered per whatever instance a caller wires in;
      confirmed via `paper_run_handler.py`, the real `--operation paper-run` T+1-cron caller). Its
      `_process_tick()` unconditionally benchmark-fills every instruction locally and only forwards the
      LEADER_HEDGE-atomic subset externally — so the real gap was that seam's scope, not a missing driver.
      **Built the general-instruction counterpart, mirroring the exact proven pattern**: `live_routing.py` gained
      `publish_strategy_instruction`/`_sync`, `filter_general_instructions` (complement of
      `filter_leader_hedge_atomics` by construction — an instruction is routed on exactly one of the two shards,
      never both, never neither), and `publish_general_instructions_sync`, all publishing onto a NEW, separate
      `strategy_instruction` shard. `GroupBRunner` gained an `instruction_publisher` seam (byte-identical when
      `None`, same as the existing `atomic_publisher` contract) firing for every non-LEADER_HEDGE instruction;
      `group_b_handler.py` wires both seams the same way. 10 new tests, including an explicit no-double-publish
      proof. **Deliberately NOT resolved, flagged not guessed**: whether live mode should skip local
      benchmark-fill settlement once a real publish path exists (settle+publish both would double-count) — that's
      a real design decision for whoever connects this to an actual live deployment, not decided here; this
      session shipped the publish-side plumbing only, additive and opt-in. Execution-service has no subscriber
      for the new shard yet — T4's half, matching how the atomic seam itself was wired ahead of its route side.
      **Also corrected in the same pass**: an earlier claim from this session's own PnL investigation (session 4,
      W9/W10/W13 row) that `paper_run_attribution.py`/`paper_run_passive.py` were "confirmed real, wired" was a
      second-hand subagent relay never independently re-verified — direct grep found zero production callers;
      retracted there. The counterparty-facing HTTP/WebSocket surface (the second half of the original ask)
      still needs separate real product/security design (auth model, rate limits, what data is exposed) —
      genuinely not attempted, correctly still open.
- [ ] [BACKEND] P0. **Operator decision 2026-08-20: run BOTH local benchmark-fill settlement AND the new
      general-instruction publish in live mode** (not skip-settlement) — explicitly needs its own downstream
      reconciliation logic to avoid double-counting the same trade's position/PnL impact once a real venue fill
      also comes back through execution-service. NOT built — design + build the reconciliation mechanism before
      wiring `instruction_publisher` into any real live deployment (it is currently opt-in/unwired in production
      regardless, per the checkbox above, so this is not blocking today, but IS the prerequisite before someone
      connects it). Needs: how to correlate a local benchmark fill against the real venue fill for the same
      instruction (likely `instruction_id`/`correlation_id`), which one is authoritative for PnL once both
      exist, and whether the local fill becomes a shadow/comparison value rather than a real position delta once
      live. No existing SSOT covers this — check `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`
      first, it may already define the right pattern for a different reconciliation case.
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
- [x] ✅ [FROM-T1] P1. **SHIPPED `strategy-service@8a7f80e8` (2026-08-20 session 6) — checkbox missed at ship
      time, flipped now.** `strategy_instructions` writer/registry DIVERGENCE — your repo's own
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
- [x] ✅ [FROM-T1] P2. **SHIPPED `strategy-service@8a7f80e8` (2026-08-20 session 6) — checkbox missed at ship
      time, flipped now.** Migrate `staked_basis.py`'s `_STAKING_PROTOCOL_CHAIN` off its own hardcoded dict onto UAC's
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
      `/plans/archive/2026_08/registry_ssot_hardening_2026_08_16.md` todo 6, `unified-api-contracts/unified_api_contracts
      /registry/venue_constants.py::get_chain_for_protocol`.

## Todos

### Walkthrough feedback 2026-08-21 — strategy cluster (operator feedback on platform-external-api-walkthrough.html; verified against strategy-service HEAD 2026-08-21)

- [x] [BACKEND] P0. Strategy wizard external endpoint — **done**, `deployment-api@8e26e27915`. Built
      `POST /api/strategy/wizard/{create,validate,deploy}` in `deployment-api/deployment_api/routes/
      strategy_wizard.py` (authenticated via `_authenticated_router`; `deploy` additionally gated on
      `Permission.DEPLOY_TRIGGER`, mirroring `strategy_backtest_launch.py`'s existing RBAC pattern), registered
      in `main.py`. No service->service dependency: deployment-api never imports strategy_service — the
      integration seam is the same GCS object strategy-service's `strategy_config_loader.load_strategy_config_gcs`
      already reads (`configs/strategies/{strategy_id}.json` in the strategy-store bucket). `create` returns a
      config-shape stub for a `StrategyArchetype` (UAC enum); `validate` structurally checks archetype-membership
      + JSON-well-formedness with no write; `deploy` re-validates then `upload_bytes`s to that GCS path and
      returns the `config_uri`. Deep archetype-param-schema validation (`PARAM_SCHEMA_REGISTRY`,
      strategy-service-internal) deliberately stays strategy-service-side via the existing
      `get_strategy_params`/`WizardParamPayloadError` seam. Request/response examples are in every route's
      docstring (see file — create/validate/deploy each show a full example request + response). **Hot config
      reload documented alongside, no new endpoint** (T5 hand-off): the write-side contract is the same GCS
      object; `strategy_service/config_reloaders.py`'s `DomainConfigReloader` polls `StrategyDomainConfig` and
      atomic-swaps only `SAFE_STRATEGY_RELOAD_FIELDS` (`strategy_params`), rejecting anything outside that
      allow-list via `UnsafeConfigChangeError` (previous config stays active) — request = GCS write, response =
      next reload tick's accept/reject, observable via strategy-service `log_event`. 9 new tests in
      `tests/unit/test_strategy_wizard.py`, all QG-green. Shipping this hit two real blockers along the way,
      both filed/resolved separately: a dirty `unified-api-contracts` dependency (transient, another concurrent
      session's WIP) and a genuine regression from `unified-api-contracts@4f25d5f0` breaking
      `deployment-api/deployment_api/services/prediction_catalogue.py` at import time (filed
      `/plans/archive/issues/deployment_api_prediction_catalogue_broken_by_uac_category_deletion_2026_08_21.md`,
      resolved + archived by a separate session at `deployment-api@9947cc40ae`) — see Progress Log for the full
      trace on both.
- [x] [BACKEND] P1. Add `staking_pnl` as a first-class dimension in `_PNL_DIMENSIONS` — **done**,
      `strategy-service@21937bb2cf`. `_PNL_DIMENSIONS` grew from 11 to 12 (`staking_pnl` added); it is
      accumulated as its own dimension (no longer silently mixed into whichever of carry/residual a caller
      happened to pick) and, since UAC's `PortfolioPnLAttribution` has no dedicated `staking_pnl` field yet
      (a cross-repo unified-api-contracts schema change, out of this wave's scope), deterministically folded
      into `carry_pnl` on construction via a new `_UAC_FOLD_TARGET` map — documented in-code so the fold-in is
      dropped once UAC ships the field. 2 new tests: `test_staking_pnl_is_first_class_dimension_folded_into_carry`,
      `test_staking_pnl_defaults_to_zero_when_unspecified`; existing `test_all_11_dimensions_sum` updated to
      assert `len(_PNL_DIMENSIONS) == 12`. Real list for T5's PnL-attribution section: delta/gamma/theta/vega/rho,
      funding, basis, interest_rate, carry, fx, residual, staking (staking folds into carry pending UAC field).

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
- [x] ✅ [BACKEND] P1. **Corrected 2026-08-21 — the prior re-triage was stale, citing an OLD, superseded
      "Recommendation" section.** Re-read the full issue doc: it has a `RESUME POINT 2026-07-23` addendum
      (below the stale Recommendation section) recording the operator's verbatim-quoted 3-layer target
      architecture AND an operator-approved build plan, "Build plan — 'complete the orphaned archetypes'
      (operator-approved 2026-07-23, in progress)" — and every single todo in that build plan (Phases 0-5,
      Layer-1 ADV-ranked candidate discovery, Layer-3 curtailment mechanism, both side-decisions) is `[x]`,
      shipped 2026-07-23 through 2026-07-26, weeks before this plan existed. Grepped the whole doc for any
      remaining `- [ ]` — zero. This item is fully done, not operator-gated; nothing to re-ask. Evidence:
      `/plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`. Follow-up: that
      issue doc looks archival-eligible (every todo done, unlocked) — worth a dedicated archival pass, not done
      here to stay scoped to this correction.
- [x] ✅ [BACKEND] P1. **Corrected 2026-08-21 — the prior re-triage was stale.** The issue doc already carries an
      `## OPERATOR RULING 2026-08-21` section (citing `/codex/04-architecture/cross-domain-state-fabric.md` §12,
      R17 — ONE declarative capability-gated resolver, generalized to every
      family, fail-closed) that closes exactly this decision — the todo just hadn't been retagged. Fixed
      directly in the issue doc: todo 1 flipped `[x]` citing the ruling, the venue-literal audit (todo 2) is
      also done (`pm@0fa40df01d`, 2 real drift findings — CME event root symbols, Phoenix stale listing), and
      the resolver-build + regression-check todos are now `[AGENT]`-actionable, no longer blocked. Evidence:
      `/plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md`.

- [ ] [BACKEND] P1. Delete entries from `clients_yaml_coverage.PENDING_CROSS_REPO_WAIVER` as T5 lands each
      archetype's `clients.yaml`/`clients_waiver.yaml` in `deployment-service`. Filed as an inbound request on T5's
      plan (`unified-trading-pm@96d5d2e1f1`); the frozenset is the shrinking worklist. 27 entries at authoring.
- [x] ✅ [BACKEND] P2. **Duplicate of the already-flipped todo above (line 306) — same finding, same resolution,
      tracked twice in this plan.** Audit the other 3 engine families named in the config-key contract-drift
      issue (sports, ML-directional, market-making) the same way the vol family was audited on 2026-08-19. Done
      2026-08-20 (session 3): the systemic construct-and-fire test already parametrizes all 59 registered
      archetypes, not vol-scoped — confirmed green except 2 genuine `[DESIGN]`-blocked xfails. See the flipped
      checkbox above and the deferred table for full detail; not re-done here. Evidence:
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

- [ ] [BACKEND] P1. **Re-scoped 2026-08-21 — tracked in the same sibling plan as the W9/W10/W13
      pointer above, not a separate build.** The 69-constant migration is
      `/plans/active/strategy_service_centralization_fixes_2026_08_16.md`'s own W7 section (4 open
      todos there: inventory all 69, migrate the unambiguous ones, an `[OPERATOR]` ruling on
      ambiguous ones, fix the exemplar). Work it from that plan — see this file's own
      Progress Log for what "fix the exemplar" already turned out to be partially done by an
      earlier fix this session.
- [ ] [BACKEND] P1. **Re-scoped 2026-08-21 — same sibling plan.** "Position-risk core" wiring is
      that plan's `DeFiHealthAggregator`/`MarginEvent` reconciliation work (the same 15-open,
      `sequential: true` chain the W9/W10/W13 row above already points to) — not a separate T3
      build. See the W9/W10/W13 row above for current status; do not track separately here.
- [x] ✅ [BACKEND] P1. **Verified 2026-08-21 — the strategy-service side is already done; what remains
      is UAC-scoped, not T3's to build.** `lazy_scoped_loading_refactor_2026_08_16.md` has exactly 2
      open todos, both explicitly about `unified-api-contracts`'s `registry/__init__.py`/
      `internal/__init__.py`/`internal/architecture_v2/__init__.py` (already "in progress 2026-08-20"
      per its own text) — zero open todos reference strategy-service's `factory.py`, confirming that
      layer landed. Cross-repo (T1's tranche), correctly not touched here. Evidence:
      `/plans/active/lazy_scoped_loading_refactor_2026_08_16.md`.

### W9, W10, W13 — balances, risk, exposure, PnL

- [ ] [BACKEND] P0. **Tracked in a pre-existing sibling plan, not duplicated here** — found 2026-08-20, re-verified
      2026-08-21 (unchanged): `/plans/active/strategy_service_centralization_fixes_2026_08_16.md` already owns
      this exact convergence (dated 2026-08-16, before this plan existed) with the full reconciliation already
      done (A and B are not independent — B's DeFi path already consumes A's `DeFiHealthAggregator.aggregate()`
      output; the genuinely redundant piece is `positions_health.py`'s separate re-derivation). Current state:
      **10 done / 15 open todos, `sequential: true`, `assigned_vm: planning`** (AO-dispatched — has NOT
      progressed since 2026-08-16, still exactly 10/15). Work this from that plan, not as a fresh T3 todo — the
      two plans would otherwise silently duplicate the same fix. Deliberately not worked directly in this
      session (a 15-item sequential-only chain in a separate plan competes for the same session time as this
      plan's own ~20 remaining directly-owned todos); worth picking up explicitly next time strategy-service
      work resumes, since AO dispatch hasn't moved it in 5 days.
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
      **Operator decision 2026-08-20 (confirmed strategy-service is the right home)**: wire `compute_handler`
      into a real cron trigger — do NOT delete it. **Operator's own spec for what PnL attribution IS, verbatim,
      captured here so it isn't lost**: "PnL attribution takes snapshots of market data processing service and
      feature service data and pretty much tries to attribute it to the total PnL change from account balance
      changes. We need a PnL total change, and then you attribute it and you get the residual, which is your
      error, so the error should become zero, of course. We should have alerts in Slack in one of our existing
      channels that UTS live alerts, probably if the attribution is wrong and broken down by which asset group,
      deployment, instruments, whatever." Concretely: `total_pnl_change` (from real account-balance deltas) −
      `sum(attributed factors, from MTDS + features-service snapshots)` = `residual`; residual should trend to
      ~0 for a correct attribution model; alert to the existing `uts-live-alerts`-style Slack channel (confirm
      exact channel name — SSOT `/codex/04-architecture/agent-orchestrator-alerting.md`'s adjacent
      `/codex/04-architecture/ci-alerting.md` doc names the pattern, not necessarily this exact channel) when
      residual is non-zero beyond a to-be-set tolerance, broken down by asset_group / deployment / instrument.
      **This is new scope beyond "wire the existing cron"** — the residual-computation + Slack-alerting
      machinery does not exist yet per this session's investigation; check `compute_handler.py`'s current
      output shape before assuming what's missing vs already there.
- [ ] [BACKEND] P0. Build PnL attribution across every dimension the artefacts describe (W13) — currently
      "specified, not built".
- [x] ✅ [BACKEND] P1. **12/13 already shipped across many prior sessions — verified 2026-08-21.** FUNDING leg
      (`strategy-service@aa1fcdc7`), STAKING leg (`strategy-service@e93902d8`), E4 row-set drop
      (`strategy-service@a90e85eb`), recursive-staking borrow leg (`strategy-service@23bd8b76`), ShareClass enum
      convergence (`unified-api-contracts@4df243f7`) — all done. The 1 remaining open todo ("Option B" true
      native-staking-return metric) is explicitly `assigned_vm: NA`, under a standing `## OPERATOR GATE` (changes
      live client NAV/PnL, needs a 3-lens money-path review) — repeatedly re-confirmed genuinely gated by 6+
      independent na-eligibility-audit passes since 2026-08-01, not a bare build task. Build spec exists at
      `/plans/active/issues/pnl_true_native_staking_return_spec_2026_08_20.md`, not yet approved. Not built here —
      correctly stays gated. Evidence:
      `/plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`.
- [x] ✅ [BACKEND] P1. Fix DeFi leverage archetypes reading health factor from the wrong source. **Already resolved
      before this todo was written** — all 11 items in the issue doc's todo list are `[x]`, including the operator
      ruling (2026-08-17) and the `DeFiHealthAggregator` reconciliation (2026-08-18, `[AGENT]`). Found 2026-08-20
      already at this state, predating this plan. Evidence:
      `/plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md`.
- [x] ✅ [BACKEND] P1. **Fully shipped — verified 2026-08-21, 0 open todos.** All 4 originally-flagged silent-zero
      engines fixed (`LIQUIDATION_CAPTURE` via new `GasCostUsdCalculator`, `features-service@20d71ed0fb` +
      `strategy-service@0088d62fe8`; `CARRY_STAKED_BASIS` via a gas-only `fees_apy_bps` sub-term,
      `strategy-service@f09969fe94`; `JIT_LIQUIDITY`'s gas+flash-fee gate,
      `strategy-service@fbf78dfe20`; `BACKRUN` priority-gas netting, `strategy-service@696094a9b9`), plus the much
      larger downstream `LIQUIDATION_CAPTURE` candidate-snapshot cross-repo effort this issue doc grew into (UAC
      typed contract, MTDS Aave V3 pre-liquidation producer, features-service enrichment, strategy-service typed
      context seam) — also fully shipped, with the archetype's paper-registration gate measured and honestly
      retained-blocked (real fixture candidates too small to clear the profit floor) rather than forced. Evidence:
      `/plans/active/issues/defi_gas_net_cost_partial_wiring_gap_2026_08_17.md`.

### W16, W18 — preflight and canonical output paths

- [ ] [BACKEND] P0. **Re-scoped 2026-08-21 — real, ruled, but its own "first concrete instance" ties
      directly to the stalled sibling plan.** Epic spec (`system_readiness_master.md` line 571-584):
      RULED 2026-08-18 — every archetype needs a NAMED startup-readiness check covering position/
      PnL/risk/venues/every market-data type it consumes, both presence AND freshness, fail-closed
      by default; done-when is explicit. The epic's own text names its first concrete instance as
      `strategy_service_centralization_fixes_2026_08_16.md`'s DeFi health-factor gates — the same
      15-open-todo, `sequential: true`, AO-stalled-5-days plan already flagged above (W9/W10/W13
      row). Building the GENERIC per-archetype mechanism before that first instance lands risks
      designing against an unproven shape; land the health-factor instance first (via that sibling
      plan), then generalize. Not attempted this session for the same reason: competes for session
      time with this plan's own ~15 remaining directly-owned todos, and the real unlock is picking
      up the sibling plan, not a fresh parallel mechanism here.
- [x] ✅ [BACKEND] P0. **Partially shipped 2026-08-21 — `unified-trading-library@78f7e269c2` +
      `strategy-service@42fedf7966`.** W18 (epic line 601-605) asks for one grammar across
      strategy-service's 5 emission datasets (`positions`/`pnl_attribution`/`risk_metrics`/
      `strategy_orders`/`strategy_instructions`). Audited all 5: `strategy_instructions` already
      had the full reference shape (`client_id`/`strategy_id`/`day`/`mode`); `positions` correctly
      uses a different axis (`account_key`/`snapshot_type`, no strategy identity — genuinely not a
      dialect gap); the other 3 (`strategy_orders`, `pnl_attribution`, `risk_metrics`) had NO
      `client_id=` segment at all — fixed to match the reference shape, dropping the redundant
      `by_date/` literal in the process for full consistency. Grepped every repo for real callers
      before changing anything: `strategy_orders` has zero fleet-wide callers (dead code, safe);
      `pnl_attribution` has exactly one real writer (`pnl/cli/main.py`'s cross-strategy batch,
      updated to `client_id="all"` matching its own existing `strategy_id="all"` convention) and 3
      readers (UTL `strategy.py`/`pnl.py`/`risk.py` domain clients, all updated with a `"*"`
      wildcard default); `risk_metrics` has a real READER (`RiskDomainClient.get_risk_metrics()`)
      but **no writer anywhere in the workspace** — flagged as its own separate finding, not fixed
      here (out of scope for a path-grammar change). Also corrected a stale docstring in UTL's
      `strategy.py` claiming `write_instructions` bypasses `PATH_REGISTRY` — fixed earlier this
      session (`strategy-service@8a7f80e8`), the comment was never updated. Both repos'
      `quality-gates.sh --no-fix` green (UTL: 0 failures; strategy-service: full whole-tree codex
      compliance clean — an earlier attempt hit 3 failures in files this change never touched,
      traced to a race with a concurrent quickmerge push, not a real blocker, confirmed by the
      clean retry). **Remaining W18 scope, not done here**: the `risk_metrics`-has-no-writer gap
      (needs its own scoping — is risk_metrics meant to be computed live, or was a writer just
      never built?), and confirming no OTHER strategy-service emission type exists outside these 5
      PATH_REGISTRY entries (e.g. account balances, once W9 lands, will need the same grammar
      applied from the start rather than retrofitted).
- [ ] [OPERATOR] P1. **Re-triaged 2026-08-21 — the real scope is massively larger and design-gated,
      not directly buildable.** Read the epic's own W16 spec (`plans/epics/system_readiness_master.md`
      line 562-593) — this is 2 genuinely separate things bundled under one line: (a) latency-tracing
      (time-data-received/time-data-sent per artefact) — small, mechanical, likely buildable, but
      needs its own scoping pass to find where to hook it; (b) the "generic price-sensitivity contract
      for fast execution-side repricing" — `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md`,
      a 998-line, 3-service, 11-open-judgment-call design doc, explicitly `assigned_vm: NA`/
      `KEEP-NA` because it's live execution-critical-path (order pricing/repricing) machinery —
      building this blind would mean inventing trading-mechanics decisions unilaterally, exactly
      what that doc's own judgment-call list repeatedly flags as not-AO-dispatchable. Do NOT build
      (b) without operator resolution of its judgment calls; (a) is a real, separately-scoped
      follow-up worth splitting out.

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
      rules A or B. Evidence: `/plans/archive/2026_08/issues/instrument_universe_hotswap_position_state_safety_unruled_2026_08_14.md`.
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
      agent-attempted before this correction**: the false-`captured`-rows + consolidator portions already shipped
      2026-07-30 (`features-service@d8a643a0`). The remaining piece (5 protocol-specific on-chain chain-field
      collectors for ltv/liquidation_threshold/reward_rate/flash_loan_liquidity/health-factor) had been
      independently re-confirmed FIVE times as "needs a human data-source-per-protocol decision" — **that framing
      was too broad, corrected 2026-08-20 (operator challenge: batch=live symmetry means whatever data source we
      already have for one mode we should have for the other — investigated rather than re-asserted)**:
      `execution-service/execution_service/defi_execution/protocols/aave_live.py::get_user_account_data()`
      already makes a REAL on-chain call (`Pool.getUserAccountData()` via a real Web3 ABI fragment, not
      simulated) returning exactly `ltv`, `currentLiquidationThreshold`, and `healthFactor` for AAVE_V3 — a
      proven, working data-source answer the 5 prior audits never found because they only searched inside
      features-service, not execution-service, for the same technical problem solved for a different purpose
      (execution needs it for borrow-safety checks; features needs it for feature computation). Grepped the
      other 6 protocols' execution-service modules (COMPOUND_V3, FLUID, EULER_V2, RADIANT, VENUS, BENQI, MORPHO)
      for the same pattern — none found; only AAVE_V3 has this today. **Operator decision 2026-08-20: build all
      7 protocols, not just AAVE_V3** — split into two todos below. Evidence:
      `/plans/active/issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`.
- [x] ✅ [AGENT] P0. **Corrected + shipped 2026-08-20, `features-service@f1288929de`** — the real root cause was
      NOT "no data source" for `risk_params`/`flash_loan_availability`: `AaveRiskCalculator` (real DefiLlama-
      sourced Aave V3 governance LTV/liquidation-threshold) and `FlashLoanCalculator` (Morpho, real TVL-minus-
      borrowed liquidity) already existed and worked, but were never called by the live `orchestrator.py`
      dispatch — only referenced from a schema registry file, dead code. Wired both in via new
      `_load_merged_risk_params_data`/`_load_merged_flash_loan_data` loaders (mirroring the proven
      `_load_merged_lending_data` multi-source pattern) feeding `_process_risk_params`/
      `_process_flash_loan_availability`. **Also built 5 NEW sibling-protocol liquidity calculators**
      (`compound_v3_liquidity_calculator.py`, `euler_v2_liquidity_calculator.py`, `fluid_liquidity_calculator.py`,
      `venus_liquidity_calculator.py`, `benqi_liquidity_calculator.py`) — tvlUsd-minus-totalBorrowUsd via
      DefiLlama, each verified against the LIVE `/pools` payload 2026-08-20 (real project slugs:
      `compound-v3`/`euler-v2`/`fluid-lending`/`venus-core-pool`(BSC-only)/`benqi-lending`), folded into
      `flash_loan_availability`'s multi-protocol blend the same way. Fixed 2 stale DefiLlama slugs in the process
      (`"euler"`→`"euler-v2"`, `"fluid"`→`"fluid-lending"` — the bare names matched zero live pools). New tests:
      `tests/onchain/unit/test_protocol_liquidity_calculators.py` (70 cases, parametrized across all 5).
      **Correction to the original framing**: mirroring `aave_live.py::getUserAccountData()` for `health_factor`
      (as this todo originally specified) would have been WRONG — that call is wallet-scoped (needs an account
      address), but features-service's `health_factor` group is a documented protocol-level AGGREGATE with no
      wallet parameter (see its own corrected docstring). Building it as specified would have recreated, inside
      features-service, the exact wrong-health-factor-source mistake already being fixed on the strategy-service
      side (`/plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md` →
      `/plans/active/strategy_service_centralization_fixes_2026_08_16.md`). Not built here — see the new
      `health_factor` todo below instead.
- [ ] [AGENT] P1. **Find `health_factor`'s real protocol-AGGREGATE on-chain source** (NOT
      `getUserAccountData()` — that's wallet-scoped, wrong shape, see the correction above).
      `REQUIRED_OUTPUT_COLUMNS["health_factor"]` wants `aave_health_factor`/`aave_total_collateral_eth`/
      `aave_total_debt_eth`/`aave_available_borrows_eth`/`aave_current_liquidation_threshold` as PROTOCOL-WIDE
      aggregates (across all Aave V3 positions on a market), not one wallet's numbers. Likely candidate: Aave's
      `AaveProtocolDataProvider.getReserveData()`-shaped call (protocol/reserve-level, no account param) — verify
      against real Aave docs, don't guess the ABI. `_load_merged_health_factor_data` would mirror the
      `risk_params`/`flash_loan_availability` loaders built this session once the real call is found.
- [ ] [AGENT] P2. **LTV / liquidation-threshold for COMPOUND_V3/EULER_V2/FLUID/VENUS/BENQI** — verified live
      2026-08-20 that DefiLlama's `poolMeta` carries NO ltv/liquidationThreshold field for any of these 5 (checked
      real pool objects: Compound's is a plain pool-name string, Euler's a vault-name string, Fluid/Venus/BENQI's
      is `None`) — unlike `AaveRiskCalculator`, which is mostly real governance-parameter constants
      (`_DEFAULT_LTV`/`_DEFAULT_LIQ_THRESHOLD`, documented "Source: Aave V3 Ethereum governance parameters", NOT
      fabricated). Building the same shape for these 5 needs each protocol's real governance/risk-parameter docs
      (Compound Comet collateral factors, Euler per-vault LTV configs, etc.) — genuine research, not a DefiLlama
      field and not a guess. Not built this session; `risk_params` stays AAVE-only until this lands.
      `reward_rate` is also still open — `EigenRewardsCalculator` only covers EIGEN-specific rewards, not a
      general per-protocol reward-token source.
- [ ] [AGENT] P2. **RADIANT — reuse already-proven RPC code, don't research an ABI from scratch (corrected
      2026-08-20, same session, right after filing the item below it originally).** RADIANT has ZERO pools in
      DefiLlama's `/pools` payload (TVL collapsed after its 2024 hacks, verified live) — the DefiLlama pattern
      used for the other 6 protocols genuinely can't cover it, so an RPC path is still needed. But it's NOT a
      from-scratch build: `market-tick-data-service/market_tick_data_service/cli/handlers/_radiant_oracle_collection.py`
      already makes a REAL, live-verified (2026-08-13, real eth_call, real returned prices) on-chain call against
      Radiant's own Arbitrum deployment, resolved via Radiant's own `LendingPoolAddressesProvider.getPriceOracle()`
      — confirming Radiant is an Aave V2 fork reusing `AavePositionsMixin`'s shared ABI (same repo,
      `market_interface/adapters/defi/aave_positions.py`), which ALSO already has `_RESERVE_DATA_ABI`/
      `getReserveData()` — the exact protocol-aggregate call shape the `health_factor` todo above needs (not
      `getUserAccountData()`). The same `AddressesProvider` that resolved Radiant's oracle address almost
      certainly resolves Radiant's own `LendingPool` address too via `getLendingPool()` (proven pattern, one more
      provider call) — verify that call live before assuming, don't guess the address. `instruments-service/
      reference_data/adapters/defi/radiant.py` has the curated per-chain vault/reserve addresses if needed.
      **Lesson repeated from the AAVE_V3 finding earlier this session, worth stating explicitly since it recurred
      within the same plan**: before writing "needs fresh RPC/ABI research," check MTDS/instruments-service (not
      just execution-service) for an adapter already solving the identical on-chain-read problem for a different
      purpose — this is now the SECOND time in one session that check found real, reusable, already-live code.
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
- [x] ✅ [AGENT] P1. **SHIPPED 2026-08-21, `features-service@b2851c442e`.** Found 3 of the 4 handlers already had
      `ManifestWriter`/`record_captured`/`record_empty` wiring (`economic_results_handler.py`,
      `forexfactory_handler.py`, `calendar_orchestrator.py`) — the issue doc's "checked directly, no handler has
      it" claim (dated 2026-08-18) was stale. Only `corporate_actions_handler.py` was missing it; added a
      `_write_manifest()` helper mirroring the sibling handlers' exact `feature_group` + `feature_family="calendar"`
      shard-atom pattern — dividends+splits combine into one `corporate_actions` manifest row (shared GCS path
      prefix), `earnings_results` gets its own row. 6 new/updated tests
      (`tests/calendar/unit/test_corporate_actions_handler.py`), full `quality-gates.sh` green. Evidence:
      `/plans/active/issues/features_service_calendar_domain_manifest_tracking_gap_2026_08_18.md` (its own todo 1/2
      should be re-flagged stale/closed by a future pass — not done in this edit, out of scope for a plan-checkbox
      flip).
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
- [x] ✅ [BACKEND] P2. **Already fully shipped — verified 2026-08-21.** `plans/archive/2026_06/features_registry_status_versioning_2026_05_28.md`: `status: complete`, 20/20 todos done, archived (all 5 phases — schema
      extension, 1,382-spec catalogue, per-group parquet stamping, `features-status` CLI + drift baseline, this
      codex doc itself). Nothing left to build; this todo was stale. SSOT: `/codex/02-data/feature-formula-versioning.md`.

### Close-out

- [ ] [AGENT] P3. Full 6-step archival of `/plans/active/issues/features_service_calendar_domain_manifest_tracking_gap_2026_08_18.md`
      (0 open todos as of 2026-08-21, currently bridged via `archive_exempt: true`) — repoint its 8 corpus referrers
      (`plans/audit/results/code_completion_scope_2026_08_19.md`, both `tradfi_satellite_ao_dispatch_batch17/19`
      docs + `_finalize`, `nick_ai_platform_readiness_remediation_2026_08_16.md`, `ag_closeout_audit_cross_cutting_parked_2026_08_19.md`,
      `system_readiness_master.md`, this plan) at the applicable codex SSOT
      (`/codex/02-data/availability-manifest-and-data-status.md` already documents the general pattern; confirm
      whether it needs a calendar-specific addendum), `git mv` to `plans/archive/issues/`, drop `archive_exempt`.
- [ ] [AGENT] P1. Work the non-spine tail of this tranche's allocation to zero open todos or an explicit
      `BLOCKED-*` tag on every remainder.
- [ ] [AGENT] P0. Post-phase codex audit across `/codex/09-strategy/` for every contract changed.
- [ ] [AGENT] P0. Confirm every marker in the two strategy-service artefacts now reads live, or is one of the five
      allowed pending states. Re-derive; never hand-edit the HTML.

## Progress Log

> Append-only. One entry per shippable unit — what you changed, the `<repo>@<sha>`, and what you MEASURED (not what
> you assume). This log is the handoff document if this agent's context ends and a fresh one resumes the tranche.
>
> **Sessions 1-6 (the original entries + the session-2 deferred-work table) moved to**
> `/plans/active/code_readiness_t3_progress_history_2026_08_20.md` on 2026-08-20 (session 9) — this plan hit its
> 1000-line hard cap. That doc is pure history now superseded by the entries below; nothing there is live status.
> Headline facts carried forward: archetype code-completeness is 59/59 ready every leg/mode (was ~6/47/7 at plan
> authoring); the position-adapters/venue-coverage and config-key-drift plan sections were both found already
> fully resolved by prior sessions predating this plan.

## Progress Log — 2026-08-20 session 7

**Built the general-instruction publish seam**, `strategy-service@a8b53d9cc7`: `GroupBRunner` now
forwards every non-LEADER_HEDGE instruction to an optional `instruction_publisher`, mirroring the proven
`atomic_publisher` seam exactly — additive, opt-in, byte-identical when unset, complementary shard so no
instruction is ever double-published or dropped. Full detail on the flipped checkbox. The "should live mode skip
local settlement" question is correctly left for whoever wires this into a real deployment, not decided here.

**Also this session: caught two shipped-but-unflipped checkboxes** (`strategy-service@8a7f80e8`'s two fixes had
real Progress Log entries but the actual todo checkboxes were never flipped — found only because the operator
asked "how many tasks are left" and a fresh count exposed the gap) and one duplicate todo tracking the same
already-resolved config-drift finding twice. Both fixed. **Lesson**: a Progress Log entry is not the same
artifact as a flipped checkbox — writing the former does not guarantee the latter happened; re-count `- [ ]` vs
`- [x]` periodically rather than trusting memory of what got flipped.

## Progress Log — 2026-08-20 session 8 (operator design-decision round)

**Operator challenged the "on-chain collectors need a human data-source decision" finding** (independently
re-confirmed 5× by prior audits) with a sharp, correct instinct: batch=live symmetry means whatever data source
batch already has, live should too — so why would this be unresolved? Investigated rather than re-asserting: the
5 prior audits were right that features-service itself has no data source, but wrong to frame it as unknown —
`execution-service/execution_service/defi_execution/protocols/aave_live.py::get_user_account_data()` already
makes a REAL on-chain call (`Pool.getUserAccountData()`, real Web3 ABI, not simulated) answering `ltv`/
`liquidation_threshold`/`health_factor` for AAVE_V3. **Lesson**: "needs a data-source decision" claims should be
checked against SIBLING repos solving the same underlying technical problem for a different purpose, not just
re-confirmed within the one repo that's missing it — the same real-world fact (how to read Aave's account data)
existed in the codebase the whole time, just in execution-service instead of features-service. The other 6
protocols (COMPOUND_V3, FLUID, EULER_V2, RADIANT, VENUS, BENQI, MORPHO) do NOT have an execution-service
equivalent (confirmed by grep) — for those, the "needs investigation" framing was and remains correct.

**Four operator design decisions resolved this session, todos updated accordingly** (see each item above for
full detail): (1) build all 7 on-chain protocol collectors, starting with AAVE_V3 now (pattern proven) and the
other 6 interactively with operator help finding each real read method; (2) run BOTH local settlement AND the
new publish seam in live mode — needs a downstream reconciliation mechanism, not yet built; (3) calendar data
DOES belong in Layer-1 honest-coverage — the manifest-visibility wiring is now mechanically buildable, not
design-gated; (4) wire `compute_handler` into a real cron trigger (confirmed strategy-service is correct), plus
a full operator-specified PnL-attribution design (residual = total PnL change − sum(attributed factors) →
should trend to ~0; Slack-alert on non-zero residual broken down by asset_group/deployment/instrument) captured
verbatim on that todo — this is new scope beyond "wire the existing cron", not yet built.

## Progress Log — 2026-08-20 session 9 (on-chain collectors — corrected + shipped)

**Operator declined to hand-hold the other-6-protocols research** ("I'm not gonna help... just do it yourself")
and asked a sharp follow-up: most of these protocols are multi-chain, so wouldn't a collector need to return
every chain and let the caller pick? Answered directly, then investigated rather than building on the stale
plan text: UAC's `ALL_DEFI_VENUES` already treats each protocol+chain pair as its own venue
(`COMPOUND_V3-ARBITRUM` vs `COMPOUND_V3-BASE`) — no "return all chains" design was needed, that axis was already
resolved. Verified live against DefiLlama's real `/pools` payload (not assumed): COMPOUND_V3 spans 6 chains,
EULER_V2 10, FLUID 5, MORPHO 11; VENUS is BSC-only live (despite a `VENUS-ETHEREUM` UAC venue — looks stale);
BENQI is Avalanche-only; **RADIANT has ZERO live pools** (TVL collapsed after its 2024 hacks).

**Bigger finding while checking this — the plan's AAVE_V3 build instruction was itself architecturally wrong in
two ways, both caught before writing code, not after:**

1. `AaveRiskCalculator`/`FlashLoanCalculator` (real DefiLlama-sourced data) already existed in features-service
   but were dead code — never called by the live `orchestrator.py` dispatch, only referenced from a schema
   registry file. The real bug was a wiring gap, not "no data source," and the fix pattern
   (`_load_merged_lending_data` already does exactly this for `lending_rates`) was already proven in the same
   file.
2. Mirroring `aave_live.py::getUserAccountData()` for `health_factor` (as the todo literally specified) would
   have been wrong-shaped: that call is wallet-scoped, but features-service's `health_factor` group is a
   documented protocol-level AGGREGATE (its own docstring, already corrected in an earlier pass: "does NOT poll
   any wallet... NOT used for strategy-service risk gating"). Building it as specified would have recreated,
   inside features-service, the exact wrong-health-factor-source mistake
   `/plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md` already spent 3
   rounds fixing on the strategy-service side — same field name, two genuinely different meanings.

**Shipped**: wired the 2 existing calculators in, built + verified (against the live API, not guessed) 5 new
sibling-protocol liquidity calculators for COMPOUND_V3/EULER_V2/FLUID/VENUS/BENQI, fixed 2 stale DefiLlama slugs
found in the process. Checked DefiLlama's real `poolMeta` field for all 5 before assuming LTV data was available
there too — it isn't (plain string or `None`, confirmed live) — so `risk_params` (LTV/liquidation-threshold)
correctly stays AAVE-only pending real per-protocol governance-parameter research, not built on a guess. Full
detail + evidence on the flipped checkbox and the 3 new follow-up todos above.

**Lesson**: "just do it yourself" from the operator was a signal to stop asking multiple-choice questions, not a
license to skip verification — the RADIANT-has-no-pools and poolMeta-has-no-LTV findings both came from actually
hitting the live API before writing code, not from assuming the DefiLlama pattern would generalize cleanly
across all 7 protocols.
- **na-eligibility-audit 2026-08-21** (cross-cutting tranche, first audit pass): KEEP-NA, valid — Tranche 3 of the operator-slot-launched code-readiness series (same Launch-prompts mechanism). Remaining open items mix explicit `[OPERATOR]`-tagged re-triaged items, an operator decision already made 2026-08-20 requiring downstream build work, per-protocol DeFi feature-producer research explicitly requiring real governance-parameter data ('checked DefiLlama's real poolMeta field... it isn't there, so risk_params correctly stays AAVE-only pending real per-protocol governance-parameter research, not built on a guess'), and a large W-item build backlog (PnL surfaces, universal fail-closed startup check, canonical output paths). None clears the whole-doc RECLASSIFY bar; operator-slot dispatch design also precludes AO-backlog eligibility.

## Progress Log — 2026-08-21 wave-1c (walkthrough feedback, strategy cluster)

- **`staking_pnl` first-class dimension — done + shipped**, `strategy-service@21937bb2cf`. See flipped checkbox
  above for detail; QG green, 2 new tests + 1 updated assertion.
- **Strategy wizard external endpoint — built, tested, `quality-gates.sh` green, NOT YET SHIPPED (blocked on an
  unrelated dirty dependency, see below)**. Built `deployment-api/deployment_api/routes/strategy_wizard.py`:
  `POST /api/strategy/wizard/{create,validate,deploy}`, authenticated (`_authenticated_router` + `X-API-Key`/
  Firebase bearer), `deploy` additionally gated on `Permission.DEPLOY_TRIGGER` (mirrors
  `strategy_backtest_launch.py`'s existing RBAC pattern). Registered in `deployment_api/main.py`. Architecture:
  deployment-api does NOT import strategy_service (no service->service dep, verified no prior import existed
  either) — the integration seam is the GCS object strategy-service's `strategy_config_loader
  .load_strategy_config_gcs` already reads (`gs://{strategy-store bucket}/configs/strategies/{strategy_id}.json`).
  `create` returns a config-shape stub for a given `StrategyArchetype` (UAC enum, no strategy-service import
  needed); `validate` structurally checks archetype-membership + JSON-well-formedness with no write; `deploy`
  re-validates then `upload_bytes`s to that exact GCS path and returns the `config_uri`. Deep archetype-param
  schema validation (`PARAM_SCHEMA_REGISTRY`, strategy-service-internal) deliberately stays strategy-service-side
  on load via the existing `get_strategy_params`/`WizardParamPayloadError` seam — documented in the module
  docstring, not duplicated here. Request/response examples are in every route's docstring (see file). **Hot
  config reload documented alongside** (no new endpoint — it doesn't need one): the write-side contract is the
  same GCS object; `strategy_service/config_reloaders.py`'s `DomainConfigReloader` polls `StrategyDomainConfig`
  and atomic-swaps only `SAFE_STRATEGY_RELOAD_FIELDS` (`strategy_params`), rejecting (previous config stays
  active) anything outside that allow-list via `UnsafeConfigChangeError` — this is the "request/response pattern"
  for T5 to hand off: request = GCS write, response = next reload tick's accept/reject, observable via
  strategy-service `log_event`. 9 new tests in `tests/unit/test_strategy_wizard.py` (create stub + 422,
  validate valid/invalid/empty-id, deploy success/422-no-write/502-on-storage-failure) — all GCS calls mocked.
  Also fixed 2 real gate violations found running the full-tree gate: STEP 5.12b hardcoded `gs://` literal in my
  own docstrings/Field descriptions (reworded, no literal scheme string) and STEP 5.5 broad-except baseline drift
  in `deployment_api/vm_utils.py:381` (pre-existing, unrelated to this todo, `# noqa: broad-except` with reason —
  the site is a documented best-effort confirm-poll, not a new bug) — both needed for a green tree, `--files`
  scoped to exactly these 4 touched files.
  **Ship blocked**: `quickmerge.sh` pre-flight repeatedly failed on deployment-api's path-dependency
  `unified-api-contracts` having uncommitted changes from another live concurrent session (confirmed live via
  `.py` mtime <60s at time of check, then again minutes later on a DIFFERENT larger diff — a prediction-market
  schema refactor touching 20+ files, still in flight as of this entry) — per workspace rules this is NOT mine to
  touch (not my scoped repo, not my task, live-session WIP). Retried twice (once after `unified-api-contracts`
  briefly cleared for the `strategy-service` ship, once after a `deployment-service` dirty-dep also cleared) —
  blocked again both times by `unified-api-contracts` picking up new unrelated WIP. **Follow-up**: retry
  `cd deployment-api && bash scripts/quickmerge.sh "feat(strategy-wizard): add authenticated wizard
  create/validate/deploy API" --agent --files 'deployment_api/routes/strategy_wizard.py deployment_api/main.py
  deployment_api/vm_utils.py tests/unit/test_strategy_wizard.py'` once `unified-api-contracts` is clean — code is
  complete and gate-green, this is purely a dependency-repo contention wait, not remaining implementation work.

- [x] [BACKEND] P0. Ship the already-built, already-QG-green strategy wizard external endpoint — **done**,
      `deployment-api@8e26e27915`. Landed once the P0 prediction_catalogue.py regression (see Progress Log entry
      below) was resolved by another session at `deployment-api@9947cc40ae` and the repo's gate went green again
      (5427 tests passed per the coordinator's signal, independently re-confirmed here by re-running
      `quality-gates.sh --no-fix` myself after `git pull --ff-only` before shipping, since HEAD had moved past
      my prior sentinel). Walkthrough-feedback checkbox above flipped with this sha.

## Progress Log — 2026-08-21 wave-1c, ship completion

Coordinator signaled the P0 issue doc (`deployment_api_prediction_catalogue_broken_by_uac_category_deletion_2026_08_21.md`)
was resolved + archived at `deployment-api@9947cc40ae` (catalogue facet now projects from canonical
`PredictionUnderlying` per an operator ruling; a config-descriptor int-encoding issue found alongside was pinned
too). Verified independently rather than trusting the signal blind: `git pull --ff-only` (already at
`9947cc40ae`), confirmed my WIP untouched (`strategy_wizard.py`/`main.py`/`vm_utils.py`/`test_strategy_wizard.py`
still present exactly as left), re-ran `quality-gates.sh --no-fix` myself (HEAD had moved past my prior sentinel,
so Pass-1's sentinel-verification would otherwise have refused Pass-2) — green, `exited with code 0`. Shipped:
`deployment-api@8e26e27915`. Both wizard-endpoint todos above flipped with this sha.

**Update 2026-08-21 (same session, following a coordinator signal that `unified-api-contracts@4f25d5f0` had
landed and cleared the earlier dirty-dep block)**: `git pull --ff-only` + re-gated deployment-api (HEAD had moved
since the prior sentinel) — the dirty-dep blocker IS clear, but `4f25d5f0` itself (a DIFFERENT, deliberate `feat!`
that deleted `PredictionMarketCategory`/`category_for_group`, tracked `[x]` done in
`walkthrough_feedback_remediation_2026_08_19.md` with "Manifest supersession flagged to T2 (no-migration scope
here)") broke `deployment-api/deployment_api/services/prediction_catalogue.py` at import time — that module is
imported eagerly by `tests/unit/conftest.py`, so `quality-gates.sh` now fails at pytest COLLECTION for the entire
deployment-api suite, not just prediction code. Confirmed via `git show 4f25d5f0` that the deleted helpers have no
same-shape successor (`underlying_for_group()` returns fine-grained per-asset `PredictionUnderlying`, not the old
7-value coarse bucket) — a correct fix is a real design decision (keep old bucket semantics via a new
locally-owned mapping table, or redesign the catalogue's category filter/facets around the two-axis model, and
possibly update deployment-ui too), genuinely out of this session's scope/visibility, so NOT attempted here.
Filed `/plans/archive/issues/deployment_api_prediction_catalogue_broken_by_uac_category_deletion_2026_08_21.md`
(`unified-trading-pm@49ce8f2fcf`) with the full trace + two candidate fix options for whoever picks it up.
**Net effect on this todo: still code-complete + still blocked, but now on a DIFFERENT, more specific reason** —
not `unified-api-contracts` dirty-state, but a real (if narrow, single-consumer) regression in deployment-api
itself that needs a design call before `quality-gates.sh` can go green again. The exact ship command from the
entry above is unchanged and still correct once the P0 issue doc is resolved.
