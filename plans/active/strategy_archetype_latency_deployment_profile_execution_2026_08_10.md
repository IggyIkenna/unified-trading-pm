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
- [ ] [SCRIPT] P2. **Add a `required_by_archetypes` reverse-index to `runtime-topology.yaml`'s `co_location_rules`
      /`deployment_profiles` sections** (or a new adjacent section if retrofitting the existing ones is awkward — state
      the reasoning) so a deployment-profile entry can be traced back to which archetypes require it — the
      deployment-side half of the link.
- [ ] [SCRIPT] P2. **Build the "union of registered deployments = union of what active archetypes need" derivation** — a
      function/script (likely in `deployment-service`, alongside `runtime_topology_validator.py`) that, given the
      currently-active archetype set (from strategy-service's registry) and their declared `deployment_profile` needs,
      computes which deployment_profile instances should exist. Read-only/computing a plan, NOT auto-applying infra
      changes from this todo — that's a separate, later step gated on this one working correctly and being reviewed.
- [ ] [SCRIPT] P2. **Build live resource-sizing derivation** — given an active deployment_profile instance and the
      archetypes routed to it, derive required compute sizing from the archetypes' live configuration (client count,
      instrument count per client) rather than a static guess. Start with the SIMPLEST sound rule (e.g., linear in
      client count per archetype, sum across archetypes on that instance) and flag as a documented starting assumption —
      refining the sizing model is explicitly out of scope for this first pass.
- [ ] [SCRIPT] P2. **Regression test**: two archetypes with different required deployment_profiles must NOT get silently
      collapsed onto one shared instance, and the derivation must be idempotent (same active-archetype-set in → same
      deployment-plan out, no drift between repeated runs with unchanged input).
- [ ] [SCRIPT] P2. **Regression test**: the reverse case — archetypes sharing the SAME deployment_profile requirement
      (e.g. two `Low`-category archetypes) should be able to co-locate per the existing `co_location_rules` structure,
      and the derivation should correctly union them onto shared infrastructure rather than over-provisioning one
      instance per archetype.
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

## Progress Log

- **backend_engineer (slot 8) 2026-08-10**: Todo 1 done. Added `DeploymentProfile` StrEnum (`distributed` /
  `co_located_vm`) + `ARCHETYPE_TO_DEPLOYMENT_PROFILE` mapping (60/60 `StrategyArchetype` values) to
  `unified_api_contracts/internal/architecture_v2/enums.py`, with re-exports through `architecture_v2/__init__.py` and
  `internal/__init__.py`. Populated from the audit plan's decision artifact
  (`/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md`): 41 Low-family archetypes → `co_located_vm`, 19
  Medium/High-family archetypes → `distributed`. Shipped via unified-api-contracts@f39e800992.

- 2026-08-10: Plan created, gated on the paired audit plan's decision artifact. Implements the operator's "union of
  registered deployments from union of registered archetypes, resources derived live from configuration" design
  verbatim.
