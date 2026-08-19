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

## Todos

### Archetype code completeness — the headline number

- [ ] [BACKEND] P0. Register a v2 engine for all 60 `StrategyArchetype` members. `ARCHETYPE_ENGINE_REGISTRY` holds
      exactly 32 — verified directly against `strategy-service/strategy_service/engine/strategies/v2/factory.py`.
      `VOL_TRADING` is 18/19, `PORTFOLIO` 4/4 and `CARRY_AND_YIELD` 0/11 with no registered engine. Engines for most
      `VOL_*` and `MARKET_MAKING_*` variants are shipped as code with unit tests but deliberately withheld from
      registration — per the goalpost, code-ready registration is REQUIRED; only real-data testing may remain pending.
- [ ] [BACKEND] P0. Give every archetype a `PARAM_SCHEMA_REGISTRY` entry. `CARRY_FUNDING_DISPERSION` is confirmed
      missing.
- [ ] [BACKEND] P0. Give every archetype an allocator-rank entry and a `target_universe` catalog entry.
- [ ] [BACKEND] P0. Wire mode-specific dispatch for every archetype across **batch, paper AND live**. Paper's
      per-family tick-loader dispatch and live's dispatch below the shared orchestrator have no clean registry
      lookup today — build one rather than leaving the check unverifiable.
- [ ] [BACKEND] P0. Re-run `/archetype-code-completeness` after the above and drive it to zero `not_ready`. Every
      remaining `unverified` must name the missing check, never be a silent pass.
- [ ] [BACKEND] P1. Fix the DeFi catalog/engine config-key contract drift for the 5 remaining families
      (sports, ML-directional, market-making, vol). Evidence:
      `/plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`.
- [ ] [BACKEND] P1. Build the venue/currency curtailment mechanism — `allowed_venues` is dead code today, and the
      catalog and `archetype_leg_spec_seeds` describe the same domain with no cross-check. Evidence:
      `/plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`.
- [ ] [BACKEND] P1. Generalize the venue-eligibility gate beyond `carry_and_yield`'s perp-hedge leg — the other 8
      in-scope families get `frozenset()` today. Evidence:
      `/plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md`.

### W6 — wizard, config and scaffolding

- [ ] [BACKEND] P0. Make strategy-service fully configurable from the wizard — rank-buffer hysteresis, no-trade
      band, beta-hedge overlay and vol-target-at-book-layer are all unimplemented. Evidence:
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

- [ ] [BACKEND] P0. Converge the two parallel position-risk mechanisms onto ONE. `DeFiHealthAggregator` (DeFi-only,
      not live-fed) versus the already-live cross-service `margin_event_emitter.py` / `MarginEvent` — the epic says
      converge, explicitly.
- [ ] [BACKEND] P0. Build stale-producer detection on the live path. If strategy-service stops publishing,
      execution-service does not detect it — the kill switch has 5 armed conditions and none is "an internal service
      went silent". Evidence: `/plans/active/producer_silence_flatten_protocol_2026_08_14.md` (23 open),
      `/plans/active/issues/live_path_has_no_stale_producer_revocation_2026_08_14.md`.
- [ ] [BACKEND] P0. Implement W9 account balances as the single strategy I/O.
- [ ] [BACKEND] P0. Collapse the three competing PnL surfaces to one wired path. `compute_pnl` is dead with the
      right formula but wrong keying/schema/sink; the execution-alpha compute_handler is dead with zero readers;
      only `paper_run_passive.py` / `paper_run_attribution.py` are real. HWM is never raw equity — TWR / Notional /
      PnL-recovery only. SSOT: `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`.
- [ ] [BACKEND] P0. Build PnL attribution across every dimension the artefacts describe (W13) — currently
      "specified, not built".
- [ ] [BACKEND] P1. Fix the interest-accrual wrong engine and banned formula. Evidence:
      `/plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`.
- [ ] [BACKEND] P1. Fix DeFi leverage archetypes reading health factor from the wrong source. Evidence:
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

- [ ] [BACKEND] P0. Close the position-adapter versus execution-connector asymmetry — strategy-service ships 8 DeFi
      position adapters against execution-service's ~16 live protocol connectors. Evidence:
      `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`.
- [ ] [BACKEND] P0. Fix CeFi live venue-string dispatch, broken for 9 of 12 major venues — the position-adapter
      factory hand-rolls a legacy bare-token venue table never extended to the canonical form. Evidence:
      `/plans/active/issues/cefi_live_venue_string_dispatch_broken_2026_08_16.md`.
- [ ] [BACKEND] P1. Resolve the instrument-universe hot-swap position-state contradiction — codex says restart
      required, shipped code hot-swaps live with no restart or error. One of them is wrong; fix the code or the doc.
      Evidence: `/plans/active/issues/instrument_universe_hotswap_position_state_safety_unruled_2026_08_14.md`.
- [ ] [BACKEND] P2. Resolve the orphan-coverage design gaps — `strategy_orders` / `strategy_positions` /
      `strategy_pnl` have NO live writer at all. Evidence:
      `/plans/active/issues/strategy_ml_orphan_coverage_design_gaps_2026_08_03.md`.

### features-service and ml-service

- [ ] [BACKEND] P0. Fix the 5 of 7 on-chain feature groups writing byte-identical zero-feature-column parquets
      stamped `captured=True`, plus the 6 false-`captured` rows with zero GCS objects, plus the 4-repo
      `feature_group` vocabulary split. Evidence:
      `/plans/active/issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`.
- [ ] [BACKEND] P0. Remove the banned-vendor dependency — `corporate_actions` is sourced exclusively from
      `polygon_corporate_actions_adapter.py` and Massive-fka-Polygon.io is a FLEET-WIDE banned vendor. Build the
      replacement adapter; tag it credential-gated if the new source needs a key. Evidence:
      `/plans/active/issues/features_service_corporate_actions_polygon_io_banned_vendor_2026_08_18.md`.
- [ ] [BACKEND] P0. Build opportunity-detection feature producers for the 3 code-shipped MEV engines (BACKRUN,
      JIT_LIQUIDITY, LIQUIDATION_BUNDLE). `features.get(key, 0.0)` silently defaults, so these engines are
      registered and "shipped" but can never fire. Evidence:
      `/plans/active/issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md`.
- [ ] [BACKEND] P1. Give the calendar domain manifest visibility — `economic_events` / `forexfactory` /
      `corporate_actions` / `earnings_results` never call `record_captured`. Evidence:
      `/plans/active/issues/features_service_calendar_domain_manifest_tracking_gap_2026_08_18.md`.
- [ ] [BACKEND] P1. Fix the `delta_one` dependency checker resolving the wrong PREDICTION bucket token —
      `_format_template_vars` does a naive `asset_group.lower()` with no abbreviation map, but PREDICTION's real
      bucket uses `pred`. Evidence:
      `/plans/active/issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md`.
- [ ] [BACKEND] P2. Verify and fix the MVP universe filter settlement-suffix claim ("dropped every CeFi perpetual")
      — MEASURE it first, it was not independently verified. Evidence:
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
