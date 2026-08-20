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
    /plans/archive/2026_08/registry_ssot_hardening_2026_08_16.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md,
  ]
created: 2026-08-16
source: operator-request-2026-08-16
parent_epic: security_and_cross_cutting_master
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
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    /plans/active/issues/venue_e2e_wiring_660_triple_rescoping_2026_08_19.md,
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
| **Registry SSOT / capability-record naming / error-code coverage** | [registry_ssot_hardening_2026_08_16](/plans/archive/2026_08/registry_ssot_hardening_2026_08_16.md) |
| **Per-service config (contract step 11)** | [service_config_ownership_and_instruction_contract_2026_08_12](/plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md) § D |

**What is left, and is genuinely unowned**: walking steps **2-9 per (venue × data type)** as one connected chain —
reference data, batch capture, live adapter, features, position read across all three modes, slot eligibility,
instruction coverage, and **transfers** — rather than each leg being verified in isolation by a different plan. The
per-leg plans above each prove their own leg; nothing today proves a venue is wired END TO END.

**Also revised by that boundary check**: the universe denominator is less unsolved than this plan first assumed.
`venue_capability_route_axis` already did the parity measurement that produced the 40-undeclared-venue fact table,
so the universe work is *reconciling* against that, not deriving from scratch.

## Universe denominator — resolved 2026-08-16, plan flipped to `active`

> **⚠️ DENOMINATOR STALE — flagged 2026-08-19 (plan_reconciler, `agt-b2fcb2`); RULED 2026-08-19T18:46:58Z
> (`BLK-f87a4927`, answer B).** The 353 `(venue, data_type)` pair model below was superseded 2026-08-17 by a
> shipped, operator-ruled `unified-api-contracts@d19866d339`: the real unit is now 660 `(venue, instrument_type,
> data_type)` triples (12 cells unresolved, 3.4%) — see
> `nick_ai_platform_readiness_remediation_finalize_2026_08_16.md`'s 2026-08-18 Progress Log entry ("W6's blocker
> cleared... denominator re-measured 353 → 660"). **Operator decision: leave the 5 dependent AG batch plans
> (defi/cefi/sports/tradfi/prediction `venue_e2e_batch1_2026_08_16`) running/closed as-is against the OLD 353-pair
> unit — do not reopen already-archived batches.** The 353→660 gap is tracked separately:
> [`venue_e2e_wiring_660_triple_rescoping_2026_08_19.md`](/plans/active/issues/venue_e2e_wiring_660_triple_rescoping_2026_08_19.md).
> Do not cite "353"/"192 declared venues" below as current without checking that doc first.

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
      not this plan). Each row carries its declared archetype consumer(s) (`NONE` if orphaned). **Correction,
      same-day re-measurement**: an earlier draft of this entry claimed "298/353 rows (84%) orphaned... only 5 of 59
      `StrategyArchetype` members declared, all DeFi" — **wrong on both counts**, caught by directly probing
      `prediction`'s 4 rows (all 4 show real consumers, e.g. `MARKET_MAKING_PREDICTION`, not `NONE`).
      `ARCHETYPE_FEATURE_GROUPS` moves fast (concurrent AO work keeps declaring archetypes) and spans every
      asset_group, not DeFi-only — re-measured live: **40/60 `StrategyArchetype` members declared, 236/353 rows
      orphaned** as of this correction, already liable to be stale by the time this is read. Do not assume a row's
      orphan status from its asset_group — **re-run `generate_venue_work_list.py` and read the row's own
      `archetype_consumers` column**; every AG batch plan's "expect NONE" language has been corrected to match. Full
      row export: `--csv PATH` flag on the script. **Fork
      per-asset-group dispatch batches (P0, below) is now the next actionable item.**
- [x] ✅ [BACKEND] P0. **Fork per-asset-group dispatch batches — done 2026-08-16.** SHIPPED —
      `unified-trading-pm@613c5f2f96`. 5 fresh carve-out batch plans + gated finalize pairs authored, per the
      operator-selected "per contract-step-group" decomposition (steps 1-5 / 6-8 / 9 / gap-tracking / hard-rule
      confirmation as separate todos, each scoped to one AG's rows):
      [defi_venue_e2e_batch1_2026_08_16](/plans/archive/2026_08/defi_venue_e2e_batch1_2026_08_16.md) (200 rows,
      archived 2026-08-17 — done),
      [cefi_venue_e2e_batch1_2026_08_16](/plans/archive/2026_08/cefi_venue_e2e_batch1_2026_08_16.md) (70 rows,
      archived 2026-08-17 — done),
      [sports_venue_e2e_batch1_2026_08_16](/plans/active/sports_venue_e2e_batch1_2026_08_16.md) (31 rows),
      [tradfi_venue_e2e_batch1_2026_08_16](/plans/archive/2026_08/tradfi_venue_e2e_batch1_2026_08_16.md) (16 rows,
      archived 2026-08-17 — done),
      [prediction_venue_e2e_batch1_2026_08_16](/plans/archive/2026_08/prediction_venue_e2e_batch1_2026_08_16.md)
      (4 rows, archived 2026-08-18 — done).
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

**2026-08-16 — forked per-asset-group dispatch batches.** SHIPPED — `unified-trading-pm@613c5f2f96`. Authored 5
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

**2026-08-16 — Definition-of-done "cascade invariants" todo dispatched prematurely, skipped GATED.** A worker was
dispatched against the "No venue reads as supported while a leg cannot serve it" Definition-of-done todo despite
`gate_on_depends: true` on the 5 AG batch slugs, none of which are done yet (checked live:
defi_venue_e2e_batch1 4 open, cefi_venue_e2e_batch1 3 open, tradfi_venue_e2e_batch1 2 open, sports_venue_e2e_batch1
3 open, prediction_venue_e2e_batch1 7 open — 0/5 complete). This is the exact dispatch-vs-gate gap already
documented in this plan's own "authored, held at draft" log entry above (`depends_on` orders but doesn't gate
dispatch) — now confirmed recurring for the Definition of done section too, not just the initial draft-hold. Not
filing a fresh issue doc since the gap is already named in-plan; noting it here so the next worker dispatched
against this same todo doesn't re-derive the same investigation. Skipped with `reason_code: GATED`, no code
shipped — correctly nothing to verify/ship while the AG batches (the thing that would close any cascade gaps) are
still open.

**2026-08-17 — dispatched a THIRD time, still 0/5, parking durably this time (slot 15).** Re-dispatched against the
same "cascade invariants" Definition-of-done todo despite `gate_on_depends: true`. Re-confirmed live:
`defi_venue_e2e_batch1` 6 open, `cefi_venue_e2e_batch1` 4 open, `tradfi_venue_e2e_batch1` 2 open,
`sports_venue_e2e_batch1` 3 open, `prediction_venue_e2e_batch1` 7 open — still 0/5 complete. Per CLAUDE.md,
`depends_on` (and `gate_on_depends`) documents ordering + gates archival but does NOT affect dispatch — expected
behavior, not a fresh bug; the actually-implemented durable-gate mechanism is the separate `park_now` /
`auto_unpark__<task-id>` DB-condition path fixed in
`ao_park_wiring_dropped_repeats_premature_gated_dispatch_2026_08_11.md`. Skipping with `reason_code: GATED` and
`park_now: true` this time so the task actually stays gated until the 5 AG batches land, instead of relying on the
transient fleet cooldown alone (which is what let this redispatch a 2nd/3rd time).

**2026-08-17 — a SECOND, DIFFERENT Definition-of-done todo dispatched (slot 7): the "every unit reaches
`BACKTESTABLE`" P0 line, task id `venue_e2e_wiring-0fc22529c882` — not a repeat of the already-parked
"cascade invariants" todo (`venue_e2e_wiring-0920c40e9eed`, priority 999, still correctly parked).** Content-derived
task ids are per-checkbox-line, so each of this section's 3 todos is its own backlog row and `park_now` only gates
the one row it was called on — parking one Definition-of-done todo does NOT gate its siblings. Confirmed live via
`GET /api/backlog`: `venue_e2e_wiring-0920c40e9eed` (cascade invariants) parked priority 999 as expected;
`venue_e2e_wiring-0fc22529c882` (this one) was dispatchable at priority 10 with no blocking prereq; the third,
`venue_e2e_wiring-f798d2829e48` (the P1 carve-out-scope todo), is ALSO still unparked and dispatchable at priority
20 — same exposure, next in line for a wasted dispatch. Re-confirmed the gate is still not met: `defi_venue_e2e_batch1`
6 open, `cefi_venue_e2e_batch1` 4 open, `sports_venue_e2e_batch1` 2 open, `tradfi_venue_e2e_batch1` 0 open
(`status: active`, not yet archived — likely done pending archival, but the other 4 batches still carry real open
work regardless), `prediction_venue_e2e_batch1` 7 open. Skipped `venue_e2e_wiring-0fc22529c882` with
`reason_code: GATED` + `park_now: true` (confirmed: `auto_parked_condition:
"auto_unpark__venue_e2e_wiring-0fc22529c882"`). **Follow-up still open**: `venue_e2e_wiring-f798d2829e48` remains
unparked — whichever slot it dispatches to next should park it the same way, or main/operator can pre-park it via
`manual_park` directly rather than waiting for a live dispatch to catch it.

**context-scout 2026-08-17**: refreshed context_scope (6 entries) — kept the 3 codex SSOTs (integration-testing-layers,
shard-level-failure-isolation, instruments-service-as-ssot-for-mtds) and the umbrella parent, added 2 source paths the
doc's own "Derive the work list" todo names directly: the `VENUE_DATA_TYPE_CAPABILITIES` registry file and the
re-runnable `generate_venue_work_list.py` script.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
