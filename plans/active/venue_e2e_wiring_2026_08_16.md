---
doc_type: plan
title: Venue e2e wiring — instruments-service through execution-service, per venue, for batch/live/paper
summary: >-
  W4 of the venue-readiness umbrella and its largest workstream. Walk the Venue Readiness Contract steps 1-9 for
  every venue in the universe, instruments-service through execution-service, including transfers and feature-group
  availability, so no venue reads as supported while some leg of the chain cannot serve it. Held at status draft
  deliberately: the contract is settled but the DENOMINATOR is not — "every venue in our universe" has no
  machine-readable definition yet, and dispatching a per-venue sweep without one produces confident coverage claims
  over an unknown set. Flip to active once the universe todo in the umbrella lands.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [data, features, strategy, execution]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    instruments-service,
    market-tick-data-service,
    features-service,
    strategy-service,
    execution-service,
  ]
scope: [engineer]
tags: [venue-readiness, e2e-wiring, transfers, carve-out-prerequisite, venue-coverage-cascade]
related:
  [
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/registry_ssot_hardening_2026_08_16.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md,
  ]
created: 2026-08-16
source: operator-request-2026-08-16
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: infra
estimate_baseline_ai_days: 20.0
estimate_calibrated_ai_days: 16.0
assigned_role: backend_engineer
effort: high
last_updated: "2026-08-16"
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /codex/06-coding-standards/integration-testing-layers.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
  ]
---

# Venue e2e wiring

> **Parent**: [`/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md`](/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md)
> (workstream W4). The contract this plan walks lives in the parent — this plan does not restate it.

## What this plan does NOT own (boundary measured 2026-08-16, before authoring)

This corpus already had 10 planning docs in play when this plan was written. The boundary below is the reason this
one exists at all — everything it claims is ground no existing plan owns. **Check this list before adding a todo
here**; if it belongs to one of these, it goes there.

| Owned elsewhere | Owner |
| --- | --- |
| **Contract step 1 (Declared)** — the route/mode axis on `VENUE_DATA_TYPE_CAPABILITIES`, the 40 venues that capture today with no capability entry, bookmaker spelling drift, the `VENUES_BY_ASSET_GROUP` ⊆ capability-record drift guard | [venue_capability_route_axis_and_cross_ag_declarations_2026_08_14](/plans/active/venue_capability_route_axis_and_cross_ag_declarations_2026_08_14.md) |
| **Step 12 (Reachability)** — "is it called from a production path", the reachability gate | [e2e_wiring_reachability_audit_2026_08_15](/plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md) |
| **Steps 6-8 read/execute asymmetry** — a venue tradeable but not reconcilable, the unreachable DeFi connectors | [venue_coverage_position_read_vs_execute_asymmetry_2026_08_14](/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md) |
| **Registry SSOT / capability-record naming / error-code coverage** | [registry_ssot_hardening_2026_08_16](/plans/active/registry_ssot_hardening_2026_08_16.md) |
| **Per-service config (contract step 11)** | [service_config_ownership_and_instruction_contract_2026_08_12](/plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md) § D |

**What is left, and is genuinely unowned**: walking steps **2-9 per (venue × data type)** as one connected chain —
reference data, batch capture, live adapter, features, position read across all three modes, slot eligibility,
instruction coverage, and **transfers** — rather than each leg being verified in isolation by a different plan. The
per-leg plans above each prove their own leg; nothing today proves a venue is wired END TO END.

**Also revised by that boundary check**: the universe denominator is less unsolved than this plan first assumed.
`venue_capability_route_axis` already did the parity measurement that produced the 40-undeclared-venue fact table,
so the universe work is *reconciling* against that, not deriving from scratch.

## Why this is `status: draft`

The Venue Readiness Contract is settled and the operator's rulings landed 2026-08-16. What is NOT settled is the
**denominator**. "Every venue in our universe" has no machine-readable definition: 158 capture venues across 84
families is the current measured figure, but the contract applies per **(venue × data type)**, so the real unit
count is unknown. A per-venue sweep dispatched against an undefined set produces exactly the failure this workspace
bans — a coverage claim that exceeds its measurement.

**Flip to `active` when** the umbrella's `[AGENT] P0 "Define the universe precisely for W4/W5"` todo lands with a
derived list and a stated denominator. That is the only blocker; nothing else here waits on anyone.

## The three failure modes this closes

1. **Partial wiring** — a venue in one service's registry and not another's, reading as supported while a leg cannot
   serve it. The venue-coverage cascade invariants already catch some directions; this makes full wiring the default.
2. **Asymmetry between read and execute** — the standing case tracked in
   [venue_coverage_position_read_vs_execute_asymmetry_2026_08_14](/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md),
   where a venue can be traded but not reconciled (or vice versa).
3. **Present but unreachable** — a component that exists and is never called from a production path. Reachability is
   contract step 12 and is a separate claim from capability: "does anything call it" is not "does it work".

## Method — per (venue × data type), not per venue

Each unit walks contract steps 1-9 and records a verdict per step with evidence. **A step with no real check
contributes "unverified", never a pass** — this is the binding consequence of the operator's DERIVED-readiness
ruling, and it is what stops the sweep manufacturing green.

- [ ] [BACKEND] P0. **Derive the work list** from the universe definition once it exists: one row per
      (venue × data type), with its declared archetype consumers. This is the plan's real todo list; the batches
      below fork from it.
- [ ] [BACKEND] P0. **Fork per-asset-group dispatch batches** rather than one giant plan — cefi, defi, tradfi,
      sports, prediction. Independent same-priority todos touching different files run concurrently by default; a
      single plan spanning all AGs would serialise or breach the line cap. Each batch gets its own
      `<ag>_venue_e2e_batchN_<date>.md` + gated finalize pair, following the established satellite-dispatch pattern.
- [ ] [BACKEND] P0. **Steps 1-5 per unit — declaration through features.** Declared in the UAC capability record;
      instruments-service resolves instruments with coverage windows; MTDS captures every declared data type and the
      manifest reconciles; a live adapter exists for every batch adapter (never the reverse); the venue's data
      reaches the feature groups that consume it.
- [ ] [BACKEND] P0. **Steps 6-8 per unit — strategy and execution.** A position adapter resolves in batch, live AND
      paper (the per-mode capability axis, not one boolean); the venue is declared in the archetype/slot catalogues
      that can legitimately trade it; an execution adaptor handles every `InstructionActionV2` those archetypes emit
      — compared by ACTION, not by venue name.
- [ ] [BACKEND] P0. **Step 9 per unit — transfers.** Every applicable `BusTransferType` has a working rail for the
      venue, instruments-service through execution-service. Transfers are the leg most often assumed rather than
      verified, and the one the carve-out counterparty depends on most directly.
- [ ] [BACKEND] P1. **Record every gap as a tracked todo in its AG batch**, never as prose. A gap found and described
      but not tracked is the false-progress failure this workspace names explicitly.

## Hard rules this sweep must not violate

- **strategy-service never reads MTDS directly.** Operator hard rule. If a unit appears to need it, the answer is a
  feature or a position adapter, not an import. There is a gate for this — do not route around it.
- **Execution fails closed on granularity.** A venue whose data cannot support a matching class must be REFUSED at
  the execution layer, not matched as if it had tick data. The fidelity-refusal path already exists
  (`refuse_unservable`); this sweep wires venues onto it rather than clamping silently.
- **Credentials gate RUNNING, never BUILDING.** Exhausting the free path is a credential ask, not a descope. Build
  the full path and mark `BLOCKED-CREDENTIALS` if it cannot be run.
- **No service-to-service dependencies.** Integrate by API contract and mocks; SIT fires at the staging boundary.

## Definition of done

- [ ] [BACKEND] P0. **Every unit in the universe reaches at least `BACKTESTABLE`**, derived from real checks, with
      unverified steps surfaced as unverified rather than absent.
- [ ] [BACKEND] P0. **No venue reads as supported while a leg cannot serve it** — the cascade invariants pass in
      both directions with no new baseline growth.
- [ ] [BACKEND] P1. **The carve-out's contracted scope is fully wired** — the four CEX venues plus Lido across the
      contracted archetypes, since this is the subset with a delivery date attached.

## Progress Log

**2026-08-16 — authored, held at `draft`.** Forked from the umbrella's W4 item. Authored now so the method, the
hard rules and the AG-batch fork structure are settled and reviewable; held out of ingestion because the universe
denominator does not exist yet. `status: draft` is the correct lever here — `depends_on` documents ordering but does
not gate dispatch, so it alone would not have stopped an AO worker picking this up against an undefined set.
