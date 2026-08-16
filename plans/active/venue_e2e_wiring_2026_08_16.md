---
doc_type: plan
title: Venue e2e wiring — instruments-service through execution-service, per venue, for batch/live/paper
summary: >-
  W4 of the venue-readiness umbrella and its largest workstream. Walk the Venue Readiness Contract steps 1-9 for
  every venue in the universe, instruments-service through execution-service, including transfers and feature-group
  availability, so no venue reads as supported while some leg of the chain cannot serve it. Flipped to active
  2026-08-16: the denominator blocker resolved — real denominator is (venue, data_type) pairs, 353 across 192
  declared venues, from `VENUE_DATA_TYPE_CAPABILITIES` via
  `unified-api-contracts/scripts/generate_venue_universe_denominator.py`.
status: active
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
depends_on:
  [
    defi_venue_e2e_batch1_2026_08_16,
    cefi_venue_e2e_batch1_2026_08_16,
    tradfi_venue_e2e_batch1_2026_08_16,
    sports_venue_e2e_batch1_2026_08_16,
    prediction_venue_e2e_batch1_2026_08_16,
  ]
gate_on_depends: true
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

## Universe denominator — resolved 2026-08-16, plan flipped to `active`

The Venue Readiness Contract is settled and the operator's rulings landed 2026-08-16. The denominator blocker that
held this plan at `status: draft` is now resolved: "158 capture venues across 84 families" was a stale one-off
manual tally (`venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md:62-65`) with no producing script —
do not cite it again. The contract applies per **(venue × data type)**, and that pair count IS the real unit count:
**192 declared venues, 353 (venue, data_type) pairs**, from `VENUE_DATA_TYPE_CAPABILITIES` in
`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:2564`, reproducible via
`unified-api-contracts/scripts/generate_venue_universe_denominator.py` (re-run it — the count moves as either
registry changes, it is not a constant). 8 `ALL_DEFI_VENUES` entries (5 Alchemy gas-fee-oracle spellings +
Fluid/Sushiswap-Arbitrum) have no capability declaration yet and are excluded from the denominator until one is
added — tracked as its own P1 todo in the umbrella plan, not a blocker here.

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

- [x] ✅ [BACKEND] P0. **Derive the work list — done 2026-08-16.** SHIPPED —
      `unified-api-contracts@9693ff0291` (new `scripts/generate_venue_work_list.py`, permanent/re-runnable, mirrors
      the sibling denominator/consumability scripts). One row per (venue × data type) — confirmed 353 rows across 192
      venues, cross-checked against `generate_venue_universe_denominator.py`'s count. Per asset_group: defi 200, cefi
      70, sports 31, tradfi 16, prediction 4, plus 32 rows `UNMAPPED` (venue absent from `VENUES_BY_ASSET_GROUP` —
      that gap is owned by
      [venue_capability_route_axis_and_cross_ag_declarations_2026_08_14](/plans/active/venue_capability_route_axis_and_cross_ag_declarations_2026_08_14.md),
      not this plan). Each row carries its declared archetype consumer(s) (`NONE` if orphaned). **298/353 rows (84%)
      have no declared archetype consumer** — consistent with, not a new finding beyond, the umbrella plan's already-
      tracked 172/192-venue orphan measurement (§ STRATEGY CONSUMABILITY,
      `unified-api-contracts@36a31a165f`): only 5 of 59 `StrategyArchetype` members are declared in
      `ARCHETYPE_FEATURE_GROUPS` today, so most rows have no consumer to wire toward yet — a scope gap tracked by the
      archetype-declaration backlog, not blocking this sweep. Full row export: `--csv PATH` flag on the script. **Fork
      per-asset-group dispatch batches (P0, below) is now the next actionable item.**
- [x] ✅ [BACKEND] P0. **Fork per-asset-group dispatch batches — done 2026-08-16.** SHIPPED —
      `unified-trading-pm@<pending-sha>`. 5 fresh carve-out batch plans + gated finalize pairs authored, per the
      operator-selected "per contract-step-group" decomposition (steps 1-5 / 6-8 / 9 / gap-tracking / hard-rule
      confirmation as separate todos, each scoped to one AG's rows):
      [defi_venue_e2e_batch1_2026_08_16](/plans/active/defi_venue_e2e_batch1_2026_08_16.md) (200 rows),
      [cefi_venue_e2e_batch1_2026_08_16](/plans/active/cefi_venue_e2e_batch1_2026_08_16.md) (70 rows),
      [sports_venue_e2e_batch1_2026_08_16](/plans/active/sports_venue_e2e_batch1_2026_08_16.md) (31 rows),
      [tradfi_venue_e2e_batch1_2026_08_16](/plans/active/tradfi_venue_e2e_batch1_2026_08_16.md) (16 rows),
      [prediction_venue_e2e_batch1_2026_08_16](/plans/active/prediction_venue_e2e_batch1_2026_08_16.md) (4 rows).
      The four Method todos below are now digest pointers, not dispatchable work (task_template.md §3 finding H) —
      the real work moved into the 5 batches. This plan's own `depends_on` + `gate_on_depends: true` now gates its
      Definition of done section on all 5 finishing.
- **[BACKEND] P0. CANCELLED — SUPERSEDED 2026-08-16 (interactive session, per the 5 AG batch plans above).** Steps
  1-5 per unit — declaration through features. Forked into each AG batch's own todo #1.
- **[BACKEND] P0. CANCELLED — SUPERSEDED 2026-08-16 (interactive session, per the 5 AG batch plans above).** Steps
  6-8 per unit — strategy and execution. Forked into each AG batch's own todo #2.
- **[BACKEND] P0. CANCELLED — SUPERSEDED 2026-08-16 (interactive session, per the 5 AG batch plans above).** Step
  9 per unit — transfers. Forked into each AG batch's own todo #3.
- **[BACKEND] P1. CANCELLED — SUPERSEDED 2026-08-16 (interactive session, per the 5 AG batch plans above).** Record
  every gap as a tracked todo in its AG batch. Forked into each AG batch's own todo #4.

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

**2026-08-16 — forked per-asset-group dispatch batches.** SHIPPED — `unified-trading-pm@<pending-sha>`. Authored 5
fresh carve-out AG batch plans + gated finalize pairs (defi 200 rows / cefi 70 / sports 31 / tradfi 16 /
prediction 4), following the operator-selected "per contract-step-group" decomposition (5 todos each: steps 1-5,
steps 6-8, step 9 transfers, gap-tracking, hard-rule confirmation). Converted this plan's own Method-section
per-step todos to digest pointers (task_template.md §3 finding H) since the real dispatchable work now lives in the
5 batches; added `depends_on` + `gate_on_depends: true` on those 5 batch slugs so this plan's Definition of done
section machine-holds until all 5 report done. Next actionable item: the 5 AG batch plans themselves (each
independently dispatchable — different files, no ordering constraint between them).

**2026-08-16 — denominator resolved, flipped to `active`.** SHIPPED —
`unified-api-contracts@e7ee398117` (new `scripts/generate_venue_universe_denominator.py`),
`unified-trading-pm@<this commit>` (this flip + the umbrella plan's todo). Real denominator: 192 declared venues,
353 (venue, data_type) pairs from `VENUE_DATA_TYPE_CAPABILITIES`. The "158/84" figure was a stale manual tally,
superseded — see the section above. 8 DeFi venues remain undeclared (tracked as a P1 todo in the umbrella, not a
blocker here). "Derive the work list" (P0, above) is now the next actionable item.
