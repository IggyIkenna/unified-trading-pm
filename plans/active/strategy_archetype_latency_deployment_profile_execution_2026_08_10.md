---
doc_type: plan
title:
  Execution — wire archetype-declared deployment-profile requirements into runtime-topology.yaml + derive deployments
  from active archetypes
summary: >-
  Implements the decision artifact produced by `strategy_archetype_latency_deployment_profile_audit_2026_08_10.md`
  (`depends_on` + `gate_on_depends: true` — this plan's todos are NOT offered to the dispatcher until that audit's
  decision artifact exists). Closes the gap the operator described 2026-08-10: "deployment style should be registered...
  the strategy archetype that is registered needs to attach to the deployments registered... if we take the union of
  registered deployments from the union of registered strategy archetypes, with resources needed on the deployments
  derived live from the configuration of the strategy archetype (how many clients etc), we are in business." Two mature,
  currently-disconnected systems (`runtime-topology.yaml`'s deployment_profiles/co_location_rules, and
  strategy-service's archetype registry) get a real link: each archetype declares its required deployment_profile (from
  the audit's decision table), and the set of live deployments + their sizing is derived from which archetypes are
  actually active, not maintained by hand.
status: active
nature: process
asset_group: [cross-cutting]
stage: [strategy]
repos: [strategy-service, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [strategy, execution, deployment-profile, archetype, runtime-topology, derived-infra]
related:
  [
    /plans/archive/2026_08/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md,
    unified-trading-pm/configs/runtime-topology.yaml,
    /codex/04-architecture/client-isolation-sla-and-runtime-profiles.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-10
last_updated: "2026-08-20" # retagged strategy_master -> execution_master (execution_master_scope audit) -- this plan
parent_epic: execution_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 4.0
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
depends_on: [strategy_archetype_latency_deployment_profile_audit_2026_08_10]
gate_on_depends: true
locked_by:
locked_since:
context_scope:
  [
    unified-trading-pm/configs/runtime-topology.yaml,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py,
    deployment-service/deployment_service/deployment_profile_derivation.py,
    deployment-service/deployment_service/deployment_profile_sizing.py,
    strategy-service/strategy_service/engine/strategies/v2/archetype_slot_resolver.py,
    /codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md,
  ]
supersedes:
superseded_by:
source: >-
  Operator direction 2026-08-10, following the audit plan's design. AO-dispatchable; every todo below is gated on the
  audit plan's decision artifact existing, so none require open-ended judgment at dispatch time.
---

# Execution — archetype-declared deployment profiles + derived deployment set

## Todos

- [x] ✅ [SCRIPT] P2. **Add a `deployment_profile` field to the strategy archetype registry** — `DeploymentProfile`
      enum + `ARCHETYPE_TO_DEPLOYMENT_PROFILE` mapping (60/60 archetypes) added to
      `unified_api_contracts/internal/architecture_v2/enums.py`, re-exported through `architecture_v2/__init__.py` and
      `internal/__init__.py`. Populated from the audit plan's decision artifact: Low→`co_located_vm` (market-making,
      arbitrage-structural, carry-and-yield basis, ml-directional, rules-directional, stat-arb-pairs),
      Medium/High→`distributed` (vol-trading, event-driven, portfolio, single-sided yield/staking). —
      unified-api-contracts@f39e800992
- [x] ✅ [SCRIPT] P2. **Add a `required_by_archetypes` reverse-index to `runtime-topology.yaml`** — new
      `archetype_deployment_profile_mapping` top-level section (v7→v8) mapping each deployment_profile back to its
      StrategyArchetype values. co_located_vm: 34 archetypes across 6 Low-latency families; distributed: 26 archetypes
      across 4 Medium/High families + single-sided yield. Rationale for new section (not retrofitting
      co_location_rules): co_location_rules enumerates service groups, deployment_profiles defines capabilities —
      neither models archetype→profile. Schema changelog documents v7_to_v8 migration. — unified-trading-pm@ab157b54a1
- [x] ✅ [SCRIPT] P2. **Build the "union of registered deployments = union of what active archetypes need" derivation**
      — a function/script (likely in `deployment-service`, alongside `runtime_topology_validator.py`) that, given the
      currently-active archetype set (from strategy-service's registry) and their declared `deployment_profile` needs,
      computes which deployment_profile instances should exist. Read-only/computing a plan, NOT auto-applying infra
      changes from this todo — that's a separate, later step gated on this one working correctly and being reviewed. —
      deployment-service@13223da3
- [x] ✅ [SCRIPT] P2. **Build live resource-sizing derivation** — given an active deployment_profile instance and the
      archetypes routed to it, derive required compute sizing from the archetypes' live configuration (client count,
      instrument count per client) rather than a static guess. Start with the SIMPLEST sound rule (e.g., linear in
      client count per archetype, sum across archetypes on that instance) and flag as a documented starting assumption —
      refining the sizing model is explicitly out of scope for this first pass. `ArchetypeLiveConfig` / `ArchetypeLoad`
      / `InstanceResourceSizing` + `derive_instance_resource_sizing()` / `derive_resource_sizing()` and a
      `--live-config` CLI flag in `deployment_service/deployment_profile_derivation.py`; fails loud
      (`MissingLiveConfigError`) when a routed archetype has no live-config row. — deployment-service@9116a2fe
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-12 (slot 18, backend_engineer) — already covered, no new code needed.** Verified
      (not assumed) that `tests/unit/test_deployment_profile_derivation.py` already carries exactly this coverage,
      landed with todo 3's own commit: `test_different_profiles_never_collapse_onto_one_instance` asserts a Low +
      Medium/High archetype pair derives 2 separate instances (never collapsed onto one), and
      `test_derivation_is_idempotent_and_order_independent` asserts `derive_required_deployment_profiles` is both
      order-independent (forward vs reversed input lists produce an equal result) and idempotent (repeated calls on
      unchanged input produce an equal result) — both properties this todo asks for.
      `git log -- tests/unit/ test_deployment_profile_derivation.py` confirms these two tests were added in
      `deployment-service@13223da3` (todo 3, not new here). Ran the full `bash scripts/quality-gates.sh` on current HEAD
      (`52936f60`, fresh-pulled) to confirm genuinely green today, not relying on the historical landing:
      `✅ ALL QUALITY GATES PASSED (336s)`, sentinel `.qg_last_passed_sha=52936f608b68cbf114f62e2272e12289773c7c72`. No
      code changes shipped this todo — the regression coverage already existed; this flip corrects the tracked-vs-actual
      gap.
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-12 (slot 18, backend_engineer) — already covered, no new code needed.** The reverse
      case is covered by `test_same_profile_archetypes_union_onto_one_instance`
      (`deployment-service/tests/unit/test_deployment_profile_derivation.py:68`): two `Low`-category archetypes
      (`MARKET_MAKING_CONTINUOUS` + `ARBITRAGE_PRICE_DISPERSION`) union onto ONE `co_located_vm` instance
      (`len(instances)==1`), never over-provisioned per archetype — exactly this todo's requirement. Complemented by
      `test_co_located_archetypes_sum_load_units_on_shared_instance` (:174), which additionally asserts the sizing sums
      across the two co-located archetypes on that shared instance. Both landed with todo 3's commit
      (`deployment-service@13223da3`, `git log -- tests/unit/test_deployment_profile_derivation.py` confirms). Ran the
      full `bash scripts/quality-gates.sh` on current HEAD (`52936f60`, fresh-pulled) to confirm genuinely green today:
      `✅ ALL QUALITY GATES PASSED (307s)`, sentinel `.qg_last_passed_sha=52936f608b68cbf114f62e2272e12289773c7c72`. No
      code shipped this todo — coverage already existed; this flip corrects the tracked-vs-actual gap.
- [x] ✅ [DOC] P1. **DONE 2026-08-12 (slot 18, backend_engineer) — unified-trading-pm@<SHA>.** Rebuilt
      `/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md` §6 from a 10-row family-label table to a
      60-row table keyed by the actual `StrategyArchetype` enum values, each row derived from
      `ARCHETYPE_TO_DEPLOYMENT_PROFILE` (34 `co_located_vm`→premium/co-located/strategy-isolated; 26
      `distributed`→standard/shared-OK). Fixed the stale `archetypes/*.md` runtime frontmatter — the 5 enumerated stale
      values (`CARRY_BASIS_PERP`, `RULES_DIRECTIONAL_CONTINUOUS`, `ML_DIRECTIONAL_CONTINUOUS`, `STAT_ARB_PAIRS_FIXED`,
      `ARBITRAGE_PRICE_DISPERSION`) + 5 invalid `min_sla_tier` enum values (`high` ×4 MEV + `ultra-premium` ×1
      queue-microstructure) → all `premium`/co-located. Also corrected a further 14 stale `Low`→`co_located_vm` docs the
      decision artifact's "5 stale" count had under-enumerated (binding contract item 1 requires EVERY
      `Low`→`co_located_vm` archetype to declare `premium` + `co_location: [execution, strategy]`), and added the
      missing `topology_requirements` block to `carry-funding-dispersion.md`. 25 archetype docs edited total; 0
      invalid/missing `min_sla_tier` values remain across the active registry.
- [x] ✅ [DOC] P2. **Residual gap (1) — two missing archetype docs — DONE 2026-08-12 (slot 16, backend_engineer).**
      Authored `/codex/09-strategy/architecture-v2/archetypes/tsmom-btc-cta.md` and
      `/codex/09-strategy/architecture-v2/archetypes/arbitrage-sports-dutching.md` from engine source
      (`strategy_service/engine/strategies/v2/rules_directional/tsmom_btc_cta.py` +
      `strategy_service/engine/strategies/v2/arbitrage_structural/sports_arb_dutching.py`), each carrying the
      runtime-enforced `topology_requirements` frontmatter (`premium` / co-located / strategy-isolated, matching
      `ARCHETYPE_TO_DEPLOYMENT_PROFILE`) so `topology_enforcement.load_topology_requirements()` no longer raises
      `FileNotFoundError` for either. Updated the README gap table to a closed-gap statement. —
      unified-trading-pm@b3eefb806d.
- [ ] [DOC] P2. BLOCKED-OPERATOR-DECISION — **Residual gaps (2)(3)(4) — still open, each a judgment call / operator ruling.** (2)
      `runtime-topology.yaml` `isolation_policies.strategy-service` `default: shared` — but the (now-correct)
      `co_located_vm` archetype docs declare `strategy-service: isolated`, so `_check_isolation()` would raise "topology
      declares default=shared" on boot; the decision artifact's item 6 commits the execution plan to wire a
      per-archetype strategy isolation section into runtime-topology.yaml but no todo here carries it (affects MM too —
      pre-existing). (3) VOL edge-case docs (`vol-market-making`, `vol-0dte-gamma-scalping`, `vol-0dte-pin-risk`)
      declare `premium` while the mapping says `distributed` — the decision artifact defers the first two to "keep
      distributed unless evidence is decisive"; needs an operator ruling. (4) `portfolio-*` + single-sided `yield-*`
      docs declare `basic` while the decision artifact's §6 says `standard` (arguably `basic` is correct for
      non-executing allocation/staking). Repo: unified-trading-pm (codex + configs/runtime-topology.yaml).
- [x] ✅ [DATA] P2. **DONE 2026-08-14 (slot 11, backend_engineer) — deployment-service@c9c1f9509.** Added
      `check_sla_tier_latency_budget_gap()` to `deployment_service/deployment_profile_derivation.py`: given a derived
      plan + `runtime-topology.yaml`, it maps each active archetype to its family + declared `min_sla_tier`
      (reverse-index walk of `archetype_deployment_profile_mapping`), compares the family's real E2E requirement
      (documented per-family ms figures sourced from `RUNTIME_TOPOLOGY_DECISIONS.md`'s 2026-08-10 table: market_making
      100ms, arbitrage_structural 300ms, carry_and_yield_basis 500ms, ml_directional 200ms, rules_directional 200ms,
      stat_arb_pairs 300ms) against the tier's declared `latency_budget_ms`, and returns an explicit warning string for
      every archetype whose real requirement exceeds its tier's budget — never silently drops the gap. Wired into the
      CLI: warnings are logged and included under `output["sla_tier_latency_budget_warnings"]` (non-fatal — a confirmed,
      documented gap, not a defect to block on) whenever `--runtime-topology` is passed. 4 new regression tests
      (`test_sla_tier_latency_gap_surfaced_when_real_requirement_exceeds_budget`,
      `..._absent_when_budget_covers_requirement`, `..._never_raises_on_missing_topology_sections`,
      `..._skips_archetype_not_in_reverse_index`) confirm the gap fires for a Low family exceeding premium's 40ms, stays
      silent when a budget genuinely covers the requirement, and never raises on partial/missing topology data. Full
      `bash scripts/quality-gates.sh` green on the shipped SHA (basedpyright caught + I fixed 4 new `Unknown`-type
      errors from the first draft before shipping — cast dict.get() results explicitly, matching the file's existing
      pattern).
- [x] ✅ [DOC] P3. **DONE 2026-08-15 (slot 24, backend_engineer) — unified-trading-pm.** Added a
      `## 2026-08-15 — archetype↔deployment link is now live-derived, not manually maintained` section to
      `/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md`, cross-referencing the code this plan landed:
      `ARCHETYPE_TO_DEPLOYMENT_PROFILE` (`unified-api-contracts@f39e800992`), the `archetype_deployment_profile_mapping`
      reverse-index (`unified-trading-pm@ab157b54a1`), `derive_required_deployment_profiles()` +
      `validate_against_runtime_topology()` (`deployment-service@13223da3`), `derive_instance_resource_sizing()`
      (`deployment-service@9116a2fe`), and `check_sla_tier_latency_budget_gap()` (`deployment-service@c9c1f9509`). Also
      added the two new code files to the doc's `code_refs` frontmatter.
- [x] ✅ [SCRIPT] P3. **DONE 2026-08-15 (slot 5, backend_engineer) — no code changes, verification-only.** Ran
      `deployment_service.deployment_profile_derivation` against the ACTUAL registered archetype set — not the full
      60-value `StrategyArchetype` enum, but `strategy_service.engine.strategies.v2.archetype_slot_resolver
      .STRATEGY_TYPE_TO_SLOT` (80 real slot rows spanning cefi/defi/tradfi/sports), which resolves to 17 distinct
      archetypes actually configured. Derivation output: 2 instances — `co_located_vm` (13 archetypes:
      ARBITRAGE_PRICE_DISPERSION, ARBITRAGE_SPORTS_DUTCHING, CARRY_BASIS_PERP, CARRY_RECURSIVE_STAKED,
      CARRY_STAKED_BASIS, LIQUIDATION_CAPTURE, MARKET_MAKING_CONTINUOUS, MARKET_MAKING_EVENT_SETTLED,
      ML_DIRECTIONAL_CONTINUOUS, ML_DIRECTIONAL_EVENT_SETTLED, RULES_DIRECTIONAL_CONTINUOUS, STAT_ARB_PAIRS_FIXED,
      TSMOM_BTC_CTA) and `distributed` (4 archetypes: EVENT_DRIVEN, VOL_TRADING_OPTIONS, YIELD_ROTATION_LENDING,
      YIELD_STAKING_SIMPLE) — `--runtime-topology` cross-check returned **zero drift** (exit 0; the only warnings were
      the pre-existing, already-documented `sla_tier_latency_budget_warnings` gap from todo 4, not a new finding).
      **Live-GCP-fleet comparison** (`gcloud run services list` + `gcloud compute instances list`, live project
      `central-element-323112`): `strategy-service` and `execution-service` each run as ONE singleton Cloud Run
      service today — there is no live infra split by `deployment_profile` (`co_located_vm` vs `distributed`) yet.
      **Sensible, stated divergence**: this derivation is explicitly read-only / plan-only per todo 3's own scope
      ("computing a plan, NOT auto-applying infra changes... a separate, later step gated on this one working
      correctly and being reviewed") — the derivation being correct does not imply the live fleet has been
      re-provisioned to match it yet, and it hasn't. No auto-apply todo exists in this plan, so this is the expected
      state, not a defect. Confirms the derivation genuinely works end-to-end against real strategy-service data
      (not just the unit-test archetype fixtures) — the "does this actually work" proof this todo asked for.
- [x] ✅ [SCRIPT] P3. **DONE (already covered) 2026-08-15 (slot 3, backend_engineer) —
      deployment-service@6a189157.** Verified (not assumed) that this exact requirement is already fully satisfied by
      `deployment_service/deployment_profile_sizing.py`, committed on origin `6a189157` (slot-17, 2026-08-11 21:37 —
      same day this todo was filed, but the checkbox was never flipped). It maps to a concrete machine size
      (`size_deployment_profile_instance` → `required_vcpu`/`required_memory_gib`/`machine_type` off the canonical
      `MEMORY_TIER_LADDER` for `co_located_vm`, Cloud-Run replica count for `distributed`) and fixes both blind spots
      by construction, not by patching `ArchetypeLoad.load_units` in place: `isolated_instances = client_count ×
      |isolated services at the SLA tier|` is a term separate from `instrument_slots = client_count ×
      instruments_per_client`, so (a) a 50-client/0-instrument archetype still contributes nonzero
      `isolated_service_instances` (client cost is never zero merely because instrument count is zero — see
      `test_sizing_is_linear_in_client_count`, which sizes with the default `instruments=0`), and (b) 1×100 vs 100×1
      (client × instrument) configs produce different `isolated_service_instances` (1×n vs 100×n) even though
      `instrument_slots` is identical in both, so they are no longer indistinguishable
      (`test_instrument_slots_scale_with_clients_times_instruments`). `SizingModel`'s coefficients are explicitly
      labelled a v1 starting assumption in the module docstring, not invented-and-unlabelled. Ran the full
      `bash scripts/quality-gates.sh` on current HEAD (fresh-pulled) to confirm genuinely green today, not relying on
      the historical landing: `✅ ALL QUALITY GATES PASSED (939s)`, sentinel
      `.qg_last_passed_sha=34bca6e6b6967d42d1275bb8e0121a65f79b3352`. No new code shipped — this flip corrects a
      tracked-vs-actual gap (coverage existed, checkbox didn't reflect it), same pattern as todos 5/6 above.

## Progress Log

- **backend_engineer (slot 11) 2026-08-14**: The SLA-tier-latency-budget-gap todo done — `deployment-service@c9c1f9509`.
  Added `check_sla_tier_latency_budget_gap()` to `deployment_profile_derivation.py`, wired into the CLI's
  `--runtime-topology` output as `sla_tier_latency_budget_warnings` + `logger.warning` lines (never fatal — this is a
  confirmed, documented gap per `RUNTIME_TOPOLOGY_DECISIONS.md`, not a bug to block shipping on). 4 new regression
  tests. First QG pass caught a self-inflicted basedpyright ratchet regression (4 new `Unknown`-type errors from not
  casting `dict.get()` results, matching the file's existing pattern) — fixed before re-running QG and shipping. Full
  `quality-gates.sh` green on the shipped SHA (`.qg_last_passed_sha=faa297664c53b63ca945321b6448fe1c5b860b6f`
  pre-push-rebase, post-push-ancestry-verified `c9c1f9509`).

- **backend_engineer (slot 8) 2026-08-10**: Todo 1 done. Added `DeploymentProfile` StrEnum (`distributed` /
  `co_located_vm`) + `ARCHETYPE_TO_DEPLOYMENT_PROFILE` mapping (60/60 `StrategyArchetype` values) to
  `unified_api_contracts/internal/architecture_v2/enums.py`, with re-exports through `architecture_v2/__init__.py` and
  `internal/__init__.py`. Populated from the audit plan's decision artifact
  (`/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md`): 41 Low-family archetypes → `co_located_vm`, 19
  Medium/High-family archetypes → `distributed`. Shipped via unified-api-contracts@f39e800992.

- **backend_engineer (slot 18) 2026-08-11**: Todo 3 done (code landed earlier via `deployment-service@13223da3` +
  follow-up basedpyright fixes `92535656`/`ecf711d8`; checkbox flip + Progress Log entry completed 2026-08-11 — the flip
  was missed in the original shipping turn). Built `deployment_service/deployment_profile_derivation.py` — the "union of
  registered deployments = union of what active archetypes need" derivation.
  `derive_required_deployment_profiles(active_archetypes)` unions the declared `DeploymentProfile` needs (UAC
  `ARCHETYPE_TO_DEPLOYMENT_PROFILE`) of the caller-supplied active archetype set into one instance per distinct profile
  (archetypes sharing a profile co-locate; different profiles never collapse), returns an idempotent sorted plan, and
  fails loud (`UnknownArchetypeError`) if an active archetype has no declared profile rather than silently
  under-provisioning. Read-only — computes a plan, never applies infra (auto-apply is the separately-gated later step).
  `validate_against_runtime_topology()` cross-checks the derived plan against runtime-topology.yaml's
  `deployment_profiles` + `archetype_deployment_profile_mapping` reverse-index so the UAC enum and YAML halves cannot
  silently diverge; a `--active-archetypes` CLI prints the plan. Unit tests in
  `tests/unit/test_deployment_profile_derivation.py` cover co-location, no-collapse, idempotency, unknown-archetype
  fail-loud, and topology drift detection. Verified 2026-08-11: full 60-archetype set derives
  `[co_located_vm, distributed]` with zero drift vs runtime-topology.yaml (exit 0).

- **backend_engineer (slot 4) 2026-08-11**: Todo 4 (live resource-sizing derivation) — checkbox flipped against
  `deployment-service@9116a2fe`, which a peer session landed mid-flight while this slot was building the same thing.
  **Duplicate dispatch, not duplicate work shipped**: the task was dispatched to this slot before that commit reached
  LDR; the collision surfaced on the pre-commit branch-drift check, so this slot's own competing sizing module
  (`deployment_profile_sizing.py`, a per-profile vCPU/GB linear model) was DISCARDED unshipped rather than landed
  alongside — two parallel sizing surfaces in one repo would be the defect, and the peer's implementation already
  satisfies the todo as written (linear in client count per archetype, summed across the archetypes on an instance,
  flagged a starting assumption, fail-loud on a missing live-config row). Verified the landed code by running it, not by
  reading it: `--active-archetypes` + `--live-config` + `--runtime-topology` over a 3-archetype set derives
  `co_located_vm` (total_load_units 68) + `distributed` (80) with zero topology drift, exit 0. That run also measured
  two blind spots in `ArchetypeLoad.load_units` — 50 clients × 0 instruments derives `total_load_units: 0`, and the
  product cannot separate client-driven from instrument-driven cost — and nothing yet maps the dimensionless proxy to a
  machine size. Filed as the new P3 todo above rather than folded in silently, since the plan scopes sizing-model
  refinement out of this first pass.

- 2026-08-10: Plan created, gated on the paired audit plan's decision artifact. Implements the operator's "union of
  registered deployments from union of registered archetypes, resources derived live from configuration" design
  verbatim.

- **backend_engineer (slot 18) 2026-08-12**: Todo 5 done. Dispatched this exact regression-test todo; found it already
  satisfied by tests landed alongside todo 3 (`deployment-service@13223da3`) —
  `test_different_profiles_never_collapse_onto_one_instance`
  - `test_derivation_is_idempotent_and_order_independent` in `tests/unit/test_deployment_profile_derivation.py`. Did not
    assume historical passing still holds: fresh-pulled to current HEAD (`52936f60`) and ran the full
    `bash scripts/quality-gates.sh` for deployment-service, which exercises this suite — green,
    `.qg_last_passed_sha=52936f608b68cbf114f62e2272e12289773c7c72`. No new code shipped for this todo; flip corrects a
    tracked-vs-actual gap (coverage existed, checkbox didn't reflect it). Todo 6 (the reverse co-location regression
    case) is a separate todo, also already covered by `test_same_profile_archetypes_union_onto_one_instance` in the same
    file — not flipped here since it wasn't this dispatch's todo; whoever picks up todo 6 can verify + flip it the same
    way.

- **backend_engineer (slot 18) 2026-08-12**: Todo 6 done. The reverse co-location regression case — archetypes sharing
  the SAME `deployment_profile` requirement must union onto shared infra, not over-provision one instance per archetype
  — is already covered by `test_same_profile_archetypes_union_onto_one_instance`
  (`deployment-service/tests/unit/test_deployment_profile_derivation.py:68`), landed alongside todo 3
  (`deployment-service@13223da3`). Two `Low`-category archetypes (`MARKET_MAKING_CONTINUOUS` +
  `ARBITRAGE_PRICE_DISPERSION`) derive exactly ONE `co_located_vm` instance holding both;
  `test_co_located_archetypes_sum_load_units_on_shared_instance` (:174) additionally asserts the per-instance sizing
  sums across both. Verified genuinely green today (not assumed from history): fresh-pulled to HEAD (`52936f60`) and ran
  the full `bash scripts/quality-gates.sh` for deployment-service — `✅ ALL QUALITY GATES PASSED (307s)`, sentinel
  `.qg_last_passed_sha=52936f608b68cbf114f62e2272e12289773c7c72`. No new code shipped; flip corrects a tracked-vs-actual
  gap.
- **backend_engineer (slot 7) 2026-08-12, dispatch
  `strategy_archetype_latency_deployment_profile_execution-73c2e13d68fc` — verified not-AO-eligible, skipped with GATED,
  no code action.** Dispatcher offered the residual-gaps todo (2)(3)(4), which self-labels "each a judgment call /
  operator ruling, not AO-eligible". Confirmed against the checkbox text + this plan's Progress Log: (3) `vol-*` docs
  declare `premium` vs the mapping's `distributed` — the decision artifact defers to "keep distributed unless evidence
  is decisive" and no ruling has landed; (4) `portfolio-*`/single-sided `yield-*` docs declare `basic` vs
  decision-artifact §6 `standard` — a judgment call the checkbox itself flags ("arguably `basic` is correct for
  non-executing allocation/staking"). Both genuinely need an operator ruling; a worker flipping either way would be
  making the ruling itself, which is not AO-eligible. (2) is a real boot-time inconsistency
  (`isolation_policies.strategy-service` `default: shared` vs the corrected `co_located_vm` docs declaring
  `strategy-service: isolated` → `_check_isolation()` would raise on boot) whose fix the decision artifact's item 6
  commits to but which **no todo in this plan carries** — flagged here for the plan owner / main agent to track as its
  own todo (touches live `configs/runtime-topology.yaml` + the isolation model, a design/config decision, not a bounded
  doc edit). No code shipped; checkbox left `[ ]` (correctly — it is not AO-done). **Flag for main/operator**:
  `regen_backlog_from_plan.py` derived an AO-dispatchable task from a checkbox that explicitly self-labels "not
  AO-eligible" — the same dispatch-scope pattern as the batch14 re-derivation thrash; a guard that skips checkboxes
  self-declaring non-AO-eligibility would stop this class.
- **backend_engineer (slot 21) 2026-08-13, same dispatch
  `strategy_archetype_latency_deployment_profile_execution- 73c2e13d68fc` — RE-CONFIRMED not-AO-eligible, skipped with
  GATED, no code action.** Second re-dispatch of the same checkbox to a fresh slot (first was slot 7, 2026-08-12).
  Independently re-verified against live state, not just reading the prior entry: `configs/runtime-topology.yaml`
  `isolation_policies.*` still reads `default: shared` (gap 2 unresolved), `archetypes/vol-market-making.md` still
  declares `min_sla_tier: premium` against the mapping's `distributed` (gap 3 unresolved), and no new commit touches
  `RUNTIME_TOPOLOGY_DECISIONS.md` or `configs/runtime-topology.yaml` since `ab157b54a1` — no operator ruling has landed
  on (3)/(4), and no todo in this plan carries the (2) isolation-policy fix. Same conclusion as slot 7: all three
  require operator judgment, not a worker guess. **This confirms the flagged dispatch-scope guard gap is still live** —
  two independent slots have now burned a dispatch cycle each on a checkbox that self-declares "not AO-eligible" in its
  own text. Recommend the guard fix (skip checkboxes whose text contains "not AO-eligible" / "operator ruling" at
  backlog-regen time) get prioritized ahead of a third recurrence.
- **backend_engineer (slot 26) 2026-08-14, same dispatch
  `strategy_archetype_latency_deployment_profile_execution-73c2e13d68fc` — THIRD recurrence (predicted by slot 21),
  RE-CONFIRMED not-AO-eligible, skipped with GATED, no code action.** Independently re-verified live state again (not
  relying on prior entries): `configs/runtime-topology.yaml` `isolation_policies.strategy-service.default` still reads
  `shared` (gap 2 unresolved), `/codex/09-strategy/architecture-v2/archetypes/vol-market-making.md` still declares
  `min_sla_tier: premium` against the mapping's `distributed` (gap 3 unresolved), `portfolio-*`/`yield-*` docs still
  declare `basic` vs the decision artifact's `standard` (gap 4 unresolved), and
  `git log ab157b54a1..HEAD -- codex/04- architecture/RUNTIME_TOPOLOGY_DECISIONS.md configs/runtime-topology.yaml`
  returns zero commits — no operator ruling has landed. Same conclusion as slots 7 and 21: all three sub-items require
  operator judgment, not a worker guess. Filed the recommended guard fix as a tracked, dispatchable issue doc (rather
  than a fourth prose recommendation):
  `/plans/archive/2026_08/issues/ao_backlog_regen_missing_self_declared_not_ao_eligible_guard_2026_08_14.md` (repo:
  agent-orchestrator, `_PERMANENT_NON_DISPATCHABLE_RE` in `server/regen_backlog_from_plan.py`).
- **backend_engineer (slot 10) 2026-08-14, same dispatch
  `strategy_archetype_latency_deployment_profile_execution-73c2e13d68fc` — FOURTH recurrence, RE-CONFIRMED
  not-AO-eligible, skipped with GATED, no code action.** Independently re-verified live state again:
  `isolation_policies.strategy-service.default` still `shared` (gap 2 unresolved), `vol-market-making.md` still
  `min_sla_tier: premium` vs the `distributed` mapping (gap 3 unresolved), `portfolio-*`/`yield-*` docs still declare
  `basic` vs the decision artifact's `standard` (gap 4 unresolved),
  `git log ab157b54a1..HEAD -- codex/04-architecture/ RUNTIME_TOPOLOGY_DECISIONS.md configs/runtime-topology.yaml` still
  returns zero commits. Same conclusion as slots 7, 21, 26 — all three require operator judgment. The guard-fix issue
  doc slot 26 filed is now RESOLVED + archived — slot 18, 2026-08-14, shipped the guard fix
  (agent-orchestrator@5c3dfb58c8: `_PERMANENT_NON_DISPATCHABLE_RE` extended with self-declared non-AO-eligibility
  patterns + `test_parse_skips_self_declared_not_ao_eligible_todos` regression test, QG green) —
  `/plans/archive/2026_08/issues/ao_backlog_regen_missing_self_declared_not_ao_eligible_guard_2026_08_14.md`. A future
  regen tick should stop dispatching this plan's residual-gaps todo; if it recurs after this fix lands, that's a fresh
  guard-gap, not this same root cause.

- **backend_engineer (slot 24) 2026-08-15**: The "update RUNTIME_TOPOLOGY_DECISIONS.md" todo done — doc-only, no code
  shipped. Added a dated section to `/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md` recording that the
  archetype↔deployment link this plan built is now runtime-enforced (not a document to keep manually in sync):
  `ARCHETYPE_TO_DEPLOYMENT_PROFILE`, the `archetype_deployment_profile_mapping` reverse-index,
  `derive_required_deployment_profiles()` / `validate_against_runtime_topology()`,
  `derive_instance_resource_sizing()`, and `check_sla_tier_latency_budget_gap()`, each cited by the SHA that landed it
  (todos 1-4/8 above). Two remaining open todos in this plan (the live-fleet verification proof and the
  load-formula/machine-sizing fix) are unrelated P3 work, untouched by this todo.

- **backend_engineer (slot 5) 2026-08-15**: The "verify against the actual current archetype set" todo done —
  verification-only, no code shipped. Extracted the REAL registered archetype set from
  `strategy_service.engine.strategies.v2.archetype_slot_resolver.STRATEGY_TYPE_TO_SLOT` (80 slot rows → 17 distinct
  archetypes; NOT the full 60-value enum) and ran `deployment_profile_derivation` against it with
  `--runtime-topology`: derives `co_located_vm` (13 archetypes) + `distributed` (4 archetypes), zero topology drift
  (exit 0), only the pre-existing documented SLA-tier-latency-budget warnings (todo 6's known gap, not new). Cross-
  checked against the actual live GCP fleet (`gcloud run services list` / `gcloud compute instances list`,
  `central-element-323112`): `strategy-service` + `execution-service` each run as ONE singleton Cloud Run service
  today, not yet split by `deployment_profile` — a sensible, stated divergence, since this derivation is read-only/
  plan-only by design (todo 3) and no auto-apply todo exists in this plan yet. Proves the derivation works end-to-end
  against real strategy-service data, not just unit-test fixtures. One P3 todo remains open (load-formula/machine-
  sizing fix).

- **backend_engineer (slot 3) 2026-08-15**: The "translate `total_load_units` into a concrete machine size, fix the
  load formula's two blind spots" todo done — verification-only, no code shipped. Found `deployment-service@6a189157`
  (slot-17, 2026-08-11, already on origin) had already built `deployment_profile_sizing.py`, a full replacement sizing
  module that maps to `machine_type`/`required_vcpu`/`required_memory_gib` via the canonical `MEMORY_TIER_LADDER` +
  Cloud Run replica ceiling, and fixes both measured blind spots by separating the per-client isolated-service term
  (`isolated_service_instances`, scales with `client_count` alone) from the per-instrument term (`instrument_slots`) —
  confirmed against its own regression tests (`test_sizing_is_linear_in_client_count`,
  `test_instrument_slots_scale_with_clients_times_instruments`). The checkbox had never been flipped even though the
  landing commit predates this todo's Progress Log entry by hours the same day. Ran the full `bash scripts/quality-
  gates.sh` on current HEAD (fresh-pulled) to confirm genuinely green today: `✅ ALL QUALITY GATES PASSED (939s)`,
  sentinel `.qg_last_passed_sha=34bca6e6b6967d42d1275bb8e0121a65f79b3352`. Every remaining open item in this plan is
  the residual-gaps todo, which self-declares not-AO-eligible (operator ruling required) — this plan is not
  fully done and stays active.

- **context-scout 2026-08-17**: rewrote context_scope (6 entries) -- the prior list's `runtime_topology_validator.py`
  was todo 3's own HEDGED guess ("likely in deployment-service, alongside runtime_topology_validator.py"); confirmed
  wrong via the Progress Log's own SHAs, real owner is `deployment_profile_derivation.py`. `archetypes.py`/
  `archetype_slots_common.py`/`dependencies.py` were never named anywhere in this doc's own body text either and
  don't match any shipped SHA -- replaced all 4 with the files the Progress Log actually cites (`enums.py`,
  `deployment_profile_derivation.py`, `deployment_profile_sizing.py`, `archetype_slot_resolver.py` -- the last
  confirmed "the ACTUAL registered archetype set" in the 2026-08-15 verification entry) plus the decision-artifact
  doc this whole plan implements.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
