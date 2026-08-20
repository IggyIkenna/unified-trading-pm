---
doc_type: plan
title: Client × Archetype Vehicle Eligibility — SMA vs Pooled Fund
summary:
  Design doc for a still-open product question — a client relationship's investment vehicle (direct SMA vs pooled
  fund) is a function of BOTH the client and the strategy archetype (a client may hold both vehicles; some archetypes
  may only be offerable under one). This determines whether a redemption ever touches fund-administration-service's
  AllocatorRedemption/NAV-cadence machinery (fund_administration_redemption_cadence_engine_2026_08_20.md) at all, or
  routes straight to a direct execution-service withdrawal. Captures the real existing hook points found in the code,
  the gap, a proposed shape, and the product questions still open before this can be scoped into dispatchable work.
status: active
nature: design
asset_group: [cross-cutting]
stage: [strategy]
repos: [strategy-service, fund-administration-service, unified-api-contracts]
scope: [engineer, admin]
tags: [strategy-agnostic, vehicle-eligibility, sma, fund-administration, archetype-capability]
related:
  [
    /plans/active/fund_administration_redemption_cadence_engine_2026_08_20.md,
    /plans/active/redemption_wallet_transfer_execution_2026_08_20.md,
    /plans/epics/strategy_master.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: strategy_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
depends_on: [fund_administration_redemption_cadence_engine_2026_08_20]
locked_by:
locked_since:
supersedes:
superseded_by:
source: operator conversation relay (Greg/Patrick SMA-redemption chat) + interactive session slot 5, 2026-08-20
context_scope:
  [
    strategy-service/strategy_service/client_context.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py,
    fund-administration-service/fund_administration_service/redemption/state_machine.py,
    /plans/active/fund_administration_redemption_cadence_engine_2026_08_20.md,
    /plans/active/redemption_wallet_transfer_execution_2026_08_20.md,
  ]
---

# Client × Archetype Vehicle Eligibility — SMA vs Pooled Fund

**Why this doc exists**: while scoping the redemption-cadence-engine plan, the operator raised a prior question the
plan had implicitly assumed away — `AllocatorRedemption`'s whole grace-period/NAV-per-share/cadence-batch machinery
only applies to a pooled-fund investor; a direct SMA client shares no NAV pool with anyone, so none of it applies to
them. But *which* vehicle a given relationship uses is not a client-level constant — the operator's own framing:
_"the same client [could] have an SMA and a fund, and it could be that some strategies you can't have an SMA or a
fund — the combination would tell you."_ That means vehicle eligibility is a function of **(client, archetype)**, not
either alone, and nothing in the codebase currently resolves that combination. This doc is the LOCAL/design capture
of that gap per `plan-brainstorm`'s Step 4 (still a genuine judgment call, not yet a bounded todo) — not yet
dispatchable AO work.

## What already exists (real hook points, not greenfield)

- **`ClientRuntimeContext`** (`strategy-service/strategy_service/client_context.py`) already binds `client_id` +
  `archetype_id` per running `ClientWorker` subprocess — this IS the (client, archetype) combination unit the
  operator described, already first-class in the runtime. It currently carries no vehicle-type field.
- A **separate** UAC `ClientContext` (JWT-claims model consumed by `prod_restrictions`/`access_control`) already
  carries a `fund_id` field alongside `org_id`/`audience`/`business_unit` — not to be confused with strategy-service's
  `ClientRuntimeContext` (the two share a name coincidentally; see that module's own docstring).
- **`ARCHETYPE_CAPABILITY_REGISTRY`** (`unified_api_contracts/internal/architecture_v2/archetype_capability.py`,
  G1.8 of `/codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md`) is an already-shipped, established
  pattern for exactly this SHAPE of question: a declarative per-archetype capability matrix (today: archetype →
  supported `ArchetypeInstrumentType`/`VenueCategoryV2`), sourced from a committed JSON manifest, loaded into a
  module-level registry, auto-mirrored to the UI's `coverage.ts` on every push. No vehicle-type axis exists on it
  today.
- **`restriction_profiles.py`** (same module) is a structurally-similar declarative YAML-driven profile resolver, but
  scoped to demo-ops persona/flavour tile-locking, not production client-strategy vehicle assignment — a similar
  idiom, not directly reusable.
- **Not a candidate**: `deployment-service/deployment_service/deployment_profile_derivation.py` — despite the name,
  this derives INFRA deployment-profile sizing (VM/shard sizing) from the active archetype set, not client-facing
  investment-vehicle structuring. Checked and ruled out during this doc's authoring.

## The gap

Nothing today resolves, for a given `(client_id, archetype_id)` pair, which vehicle (SMA or pooled fund) that
allocation runs under — no field on `ClientRuntimeContext`, no axis on `ARCHETYPE_CAPABILITY_REGISTRY`, no registry
anywhere. Consequently `fund-administration-service`'s redemption routing (both shipped companion plans) has no way
to know whether a given withdrawal request should ever create an `AllocatorRedemption` in the first place — today
that decision, if it happens at all, happens outside code (a product/deployment choice of which service a client
relationship is even wired to).

## Proposed shape (once the open questions below are resolved)

Following the codebase's own established idiom rather than inventing a new one:

1. Extend the `ARCHETYPE_CAPABILITY_REGISTRY` pattern with a vehicle-eligibility axis — which archetypes may be
   offered as SMA, pooled fund, or both — same manifest → registry → UI-mirror pipeline already in place for the
   instrument/category axis.
2. Add a per-`(client_id, archetype_id)` vehicle assignment alongside the existing per-client config surface
   `client_context.py` already reads from (`clients.yaml`) — the actual "combination" record the operator described.
3. Fund-administration-service's redemption entry point consults that assignment: `vehicle=FUND` routes into
   `AllocatorRedemption` (the already-shipped cadence engine); `vehicle=SMA` routes directly to a plain
   execution-service withdrawal, bypassing grace-period/NAV-per-share/fee machinery entirely — it was never meant to
   apply there.

This is deliberately NOT written as dispatchable todos yet — steps 1-2 both depend on the open questions below, and
"figure out the schema shape" is a judgment call, not a bounded outcome (`task_template.md` §4's dispatch-scope bar).

## Open questions (blocking — need an operator decision before this becomes a real plan)

- [ ] [OPERATOR] P1. Is `(client, archetype) → vehicle` a strict 1:1 mapping (each relationship picks exactly one
  vehicle), or can a single client split the SAME archetype's allocation across both an SMA sleeve and a fund sleeve
  concurrently? A strict mapping is a simple enum field; a split needs per-allocation (not per-relationship) vehicle
  tagging — materially different schema.
- [ ] [OPERATOR] P1. Is vehicle eligibility a HARD per-archetype constraint (some archetypes are structurally
  incapable of being offered as SMA — e.g. an operational/legal reason) or a SOFT per-client business choice (any
  archetype could be either, it's just what's been sold)? This determines whether the capability-registry axis is a
  real constraint the engine enforces or advisory metadata only.
- [ ] [OPERATOR] P2. When a client holds BOTH an SMA and a fund sleeve, are they represented as the SAME `client_id`
  with a vehicle dimension layered on, or as two DISTINCT `client_id`s (one per vehicle) — under the existing
  per-client-isolation model (`client-funds-isolation.md`), two distinct client_ids may already be sufficient with NO
  new field needed, just a registry/config decision. Worth ruling out the zero-code-change option first.

## Progress Log

- **2026-08-20**: Doc authored following `/plan-brainstorm` discipline after the operator raised the vehicle-
  eligibility question mid-review of the redemption-cadence-engine plan. Confirmed real existing hook points
  (`ClientRuntimeContext`, `ARCHETYPE_CAPABILITY_REGISTRY`, UAC `ClientContext.fund_id`) and ruled out
  `deployment_profile_derivation.py` as a candidate home. Kept `assigned_vm: NA` — the three open questions above are
  genuine product decisions, not yet a bounded AO todo.
