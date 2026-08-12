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
    /plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md,
    unified-trading-pm/configs/runtime-topology.yaml,
    /codex/04-architecture/client-isolation-sla-and-runtime-profiles.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-10
last_updated: 2026-08-10
parent_epic: strategy_master
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
    strategy-service/strategy_service/portfolio_allocator/archetypes.py,
    strategy-service/strategy_service/engine/strategies/v2/archetype_slots_common.py,
    deployment-service/deployment_service/runtime_topology_validator.py,
    deployment-service/deployment_service/dependencies.py,
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
      `git log -- tests/unit/     test_deployment_profile_derivation.py` confirms these two tests were added in
      `deployment-service@13223da3` (todo 3, not new here). Ran the full `bash scripts/quality-gates.sh` on current HEAD
      (`52936f60`, fresh-pulled) to confirm genuinely green today, not relying on the historical landing:
      `✅ ALL QUALITY GATES PASSED (336s)`, sentinel `.qg_last_passed_sha=52936f608b68cbf114f62e2272e12289773c7c72`. No
      code changes shipped this todo — the regression coverage already existed; this flip corrects the tracked-vs-actual
      gap.
- [ ] [SCRIPT] P2. **Regression test**: the reverse case — archetypes sharing the SAME deployment_profile requirement
      (e.g. two `Low`-category archetypes) should be able to co-locate per the existing `co_location_rules` structure,
      and the derivation should correctly union them onto shared infrastructure rather than over-provisioning one
      instance per archetype.
- [ ] [DOC] P1. **ADDED 2026-08-12 (/plan-reconcile) — genuine coverage gap, no tracked remediation existed until now.**
      Fix `/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md` §6's row set (7 inconsistent rows + ~37
      missing rows) and the stale `archetypes/*.md` runtime frontmatter (5 stale values + 5 invalid `min_sla_tier` enum
      values — these raise on `SLATier()` cast at runtime, a live correctness risk, not just a doc gap). Per
      `strategy_archetype_latency_deployment_profile_audit_2026_08_10.md`'s own binding decision artifact (todo 10),
      which commits this execution plan to fixing exactly this scope but whose actual todo list never carried it. Done
      when: §6 has 0 inconsistent/missing rows against the live archetype registry, and every `archetypes/*.md`
      frontmatter's `min_sla_tier` is a valid enum value. Repo: unified-trading-pm (codex) + strategy-service (archetype
      frontmatter).
- [ ] [DATA] P2. **Cross-check against the SLA-tier gap the audit plan may have flagged** (any archetype family whose
      real latency requirement exceeds even the `premium` tier's 40ms budget) — if the audit found such a gap, this
      plan's derivation logic must surface it as an explicit warning/exception rather than silently under- provisioning;
      if the audit found no such gap, this todo is a no-op confirmation, not new work.
- [ ] [DOC] P3. **Update `/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md`** (or wherever the audit plan's decision
      artifact landed) with a note that the archetype↔deployment link is now live-derived, not manually maintained,
      cross-referencing the new code paths added by this plan.
- [ ] [SCRIPT] P3. **Verify against the actual current archetype set**: run the new derivation against strategy-
      service's real, currently-registered archetypes and confirm the computed deployment plan matches (or sensibly
      diverges from, with a stated reason) the currently-live GCP fleet — this is the "does this actually work" proof,
      not just a unit-test pass.
- [ ] [SCRIPT] P3. **Translate `total_load_units` into a concrete machine size, and fix the load formula's two measured
      blind spots** (repo: deployment-service, `deployment_service/deployment_profile_derivation.py`). The sizing todo
      above deliberately stopped at a dimensionless load proxy — nothing yet maps it to vCPU/memory/machine_type, so no
      caller can provision from it. Two measured defects in `ArchetypeLoad.load_units`
      (`client_count * instrument_count_per_client`), verified 2026-08-11 by running the `--live-config` CLI: (a) an
      archetype with 50 clients and 0 declared instruments derives `total_load_units: 0` — clients cost nothing when the
      instrument count is zero, even though client isolation materialises per-client instances
      (`/codex/04-architecture/client-funds-isolation.md`); (b) the product cannot distinguish 1 client × 100
      instruments from 100 clients × 1 instrument, which are structurally different costs for the same reason. Fix =
      separate per-client and per-instrument terms, then map to a machine size (a per-`DeploymentProfile` base is needed
      too: `co_located_vm` bundles strategy/execution/MTDH on ONE VM, `distributed` scales them out separately).
      Coefficients must be calibrated or explicitly labelled a starting assumption — do not ship invented numbers
      unlabelled.

## Progress Log

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
