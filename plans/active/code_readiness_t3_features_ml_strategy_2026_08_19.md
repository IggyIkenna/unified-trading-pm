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
- [ ] [BACKEND] P0. Give every archetype an allocator-rank entry. UNCHANGED by the 2026-08-19 wave: still 8 dedicated
      `AllocatorArchetype.<VALUE>_RANK` members (24/180 rows ready, 156 `unverified`). The skill deliberately reports
      absence here as `unverified` not `not_ready`, because 8 GENERIC allocators (FIXED / PNL_WEIGHTED /
      SHARPE_WEIGHTED / RISK_PARITY / KELLY / MIN_CVAR / REGIME_AWARE / MANUAL) may legitimately serve an archetype —
      so the real task is to RULE, per archetype, whether a generic allocator suffices or a dedicated rank engine is
      required, and make that verdict machine-readable rather than inferred from absence.
- [ ] [BACKEND] P0. Wire mode-specific dispatch for every archetype across **batch, paper AND live**. Paper's
      per-family tick-loader dispatch and live's dispatch below the shared orchestrator have no clean registry
      lookup today — build one rather than leaving the check unverifiable.
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
- [ ] [BACKEND] P1. Fix the DeFi catalog/engine config-key contract drift for the 5 remaining families
      (sports, ML-directional, market-making, vol). Evidence:
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

## Deferred work after 2026-08-20

Session ended with context exhausted, not with the tranche complete. Everything below is UNSTARTED unless noted;
nothing is blocked on an answer, so the next agent can pick any row up cold. The Progress Log above is the handoff —
read the two 2026-08-20 entries first, especially the shipping-incident notes.

| Area | State | Next concrete step |
| --- | --- | --- |
| Archetype code-completeness | **DONE — `not_ready` 47 -> 0/mode**, 3 mode-invariant legs 177/177 | Nothing. The residual `unverified` rows are the two below — different work. |
| `allocator_rank` (153 unverified) | Untouched, correctly reported | Per archetype, RULE whether a generic allocator suffices or a dedicated `<VALUE>_RANK` engine is needed; make the verdict machine-readable so absence stops being ambiguous. |
| Mode dispatch — batch (42) / paper (47) | Untouched | Build the registry lookup the skill says does not exist (paper's per-family tick-loader dispatch; live below the shared orchestrator), then re-run the dump. |
| Config-key contract drift | **Vol family DONE** (2 real drifts, 8 keys) | Same method — make the systemic construct-and-fire test exercise them and see which no-op — for sports, ML-directional, market-making. A4 structurally cannot catch this class. |
| W6 wizard / config | Untouched | rank-buffer hysteresis, no-trade band, beta-hedge overlay, vol-target-at-book-layer. NOTE: the PORTFOLIO engines already ship a working no-trade band (`rebalance_band`) — reuse that shape, do not invent a second one. |
| W9/W10/W13 PnL, risk, exposure | Untouched | Collapse the three competing PnL surfaces; HWM is never raw equity (TWR / Notional / PnL-recovery only). |
| W16/W18 preflight + canonical paths | Untouched | Fail-closed startup readiness check; canonical output paths (needs T1's `PATH_REGISTRY` `mode=` fix). |
| Position adapters / venue coverage | Untouched | CeFi live venue-string dispatch broken for 9 of 12 venues is the highest-value single fix. |
| features-service | Untouched | 5 of 7 on-chain feature groups write zero-feature parquets stamped `captured=True`; `corporate_actions` still on the banned Massive/Polygon.io vendor (build the replacement adapter, tag `BLOCKED-CREDENTIALS`, never descope). |
| ml-service | Untouched | MEV opportunity-detection producers — 3 registered engines can never fire because `features.get(key, 0.0)` silently defaults. |
| Both strategy-service artefacts | Not re-derived | Re-derive markers only AFTER the W-items close; never hand-edit the HTML. |

**Cross-tranche, both filed and both shrinking-worklist-shaped:**

- T5 owes 27 `clients.yaml`/waiver files (`PENDING_CROSS_REPO_WAIVER` in strategy-service is the worklist).
- T5 owes the two `quickmerge.sh` fixes —
  `/plans/active/issues/quickmerge_exit_zero_on_failed_regate_and_silent_directory_files_2026_08_20.md`.
  **Read that issue before your first ship of the session**: it cost this one four failed attempts and a briefly
  broken LDR.
- T1's `reference_position` / `credit` extension to `StrategyInstructionEnvelope` was never reached this session, so
  that edge is still open and unblocked.
