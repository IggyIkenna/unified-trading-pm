---
doc_type: plan
title: Venue smoke-test bar — a batch smoke test per data type per venue, plus testnet where reachable
summary: >-
  W5 of the venue-readiness umbrella. Establishes the minimum provable bar for every venue: a batch smoke test per
  data type, so at minimum we know we can backtest it honestly. Databento-sourced venues are exempt per operator
  ruling (that source is already trusted). Where credentials exist or can be provisioned programmatically, add a
  testnet smoke test too. Held at status draft alongside W4 for the same reason — the per-(venue x data type)
  denominator does not exist yet, and a smoke-test bar over an undefined set measures nothing.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [data, execution]
repos:
  [
    unified-api-contracts,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    execution-service,
  ]
scope: [engineer]
tags: [venue-readiness, smoke-test, testnet, carve-out-prerequisite, batch]
related:
  [
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
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
estimate_baseline_ai_days: 12.0
estimate_calibrated_ai_days: 9.6
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
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/06-coding-standards/integration-testing-layers.md,
  ]
---

# Venue smoke-test bar

> **Parent**: [`/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md`](/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md)
> (workstream W5). Sibling: [W4 venue e2e wiring](/plans/active/venue_e2e_wiring_2026_08_16.md), which shares this
> plan's blocker and its per-asset-group batch structure.

## Why

`BACKTESTABLE` is the floor for every venue in the universe, and it needs no venue credentials — so there is no
excuse for a venue sitting below it. The smoke test is what turns that from a claim into a measurement: **a batch
smoke test per data type per venue**, so at minimum we know we can research and backtest the venue honestly.

This is the cheapest possible check that catches the umbrella's failure mode 1 (partial wiring) at the data layer,
before any of W4's more expensive per-leg verification runs.

## Scope rulings (operator, 2026-08-16)

- **Databento-sourced venues are EXEMPT.** That source is already trusted; re-smoke-testing it spends budget to
  confirm something known. The exemption is by SOURCE, not by asset group — a TradFi venue sourced elsewhere is in
  scope. Resolve membership from `SOURCE_PRIORITY` / the Databento dataset list in
  [tradfi-databento-sourcing-ssot](/codex/02-data/tradfi-databento-sourcing-ssot.md), not by assuming "TradFi = exempt".
- **Testnet smoke tests where it is easy** — where credentials already exist or can be provisioned
  programmatically. Not a blocker for the batch bar, and not a reason to hold a venue below `BACKTESTABLE`.
- **A venue's testnet answer must be RECORDED either way.** Per the umbrella's `PAPER-READY` definition: does this
  venue have a testnet, how does it behave, or must we simulate it through our own matching engine in a way that
  stays close to both backtest and live? Written down per venue, not assumed.

## What this plan does NOT own (boundary measured 2026-08-16, before authoring)

**The per-service smoke harnesses already exist** — do not build a second one. `/data-pipeline-check-is`,
`/data-pipeline-check-mtds`, `/data-pipeline-check-mdps` and `/data-pipeline-check-features` each run a force-refetch
+ skip-if-fresh proof per shard against `-test-` buckets, and already carry the canonical-path leg. This plan's job
is **coverage and systematisation**, not a new harness: make those run per (venue × data type) across the whole
universe, with the exemption set and the testnet verdict recorded.

**But they must be audited before they are relied on — operator direction 2026-08-16.** Canonical expectations have
moved since those skills were written, and a smoke harness asserting a stale canonical shape reports green over
migrated data. Measured 2026-08-16:

- **ZERO of the four skills call `canonical_path_violations()`** — the UAC MACHINE ORACLE that CLAUDE.md requires
  ("never a re-implemented rule"). All four assert canonical in prose only.
- **Two carry their own stale-warning banners**: `data-pipeline-check-is` (line 25) and `data-pipeline-check-mtds`
  (line 255) both say that while the raw→canonical instrument-id migration is in flight, *"this check's pass/fail is
  actively misleading"* — dated 2026-07-18 and 2026-07-20 respectively.
- **Three canonical-changing dispatches landed 2026-08-16 alone** — cefi casing residual, sports venue-vocab +
  league_id delete, tradfi purge extension + twin-delete fix — so the drift is active, not historical.

- [ ] [BACKEND] P0. **Audit all four `/data-pipeline-check-*` skills against current canonical expectations before
      W5 depends on them.** Per skill: does its canonical leg call `canonical_path_violations()` or re-implement the
      rule; does it validate the filename instrument_id (the oracle is PATH-STRUCTURE-ONLY and VALUE-BLIND, so
      id-form and `instrument_type`/`data_type`/`venue`/`chain` VALUES must be checked separately or explicitly
      declared unchecked); is its stale-migration banner still true. Done-when: each skill either routes through the
      oracle or records why it cannot, and every banner is re-dated or removed. **This is a prerequisite of every
      other todo in this plan** — a harness that reports green over migrated data makes the whole bar worthless.

Contract step 1 (venue declared, batch/live capability axis) belongs to
[venue_capability_route_axis_and_cross_ag_declarations_2026_08_14](/plans/active/venue_capability_route_axis_and_cross_ag_declarations_2026_08_14.md),
which also already declares `batch = none` for venues with no batch source — those must not be reported as smoke
failures, they are declared absences.

## Why `status: draft`

Same single blocker as W4: the per-(venue × data type) denominator does not exist yet. A smoke-test bar reported
over an undefined set produces a percentage with no denominator — the exact shape of unfalsifiable progress this
workspace bans. **Flip to `active`** when the umbrella's "Define the universe precisely for W4/W5" todo lands.

## What a smoke test must actually prove

The trap here is a test that passes on absence. A smoke test that queries a shard, gets zero rows, and exits 0 has
proved nothing — and this corpus has already been burned by entity-agnostic checks passing for hours while the
target wrote zero rows.

- [ ] [BACKEND] P0. **Specify the smoke-test contract before writing any.** At minimum it must assert: rows were
      actually captured for the named (venue, data type) unit; they land at a CANONICAL path (per the machine
      oracle, not a re-implemented rule); the manifest reconciles for that shard atom; and the capture_status is a
      genuine capture rather than `expected_unattempted`. Done-when: the contract is written here and one reference
      implementation exists that provably FAILS on a venue with no data.
- [ ] [BACKEND] P0. **Derive the in-scope unit list** — every (venue × data type) minus the Databento-sourced
      exemptions, with the exemption set enumerated explicitly rather than described. Forks from the same universe
      definition W4 waits on.
- [ ] [BACKEND] P0. **Fork per-asset-group dispatch batches**, matching W4's structure so the two workstreams stay
      comparable per AG and do not each invent their own batching.
- [ ] [BACKEND] P1. **Record the testnet answer per venue** — has one / behaves how / must be simulated. This feeds
      the `PAPER-READY` state directly and is cheap to gather while a venue is already being examined.
- [ ] [BACKEND] P1. **Add testnet smoke tests where credentials are already available** or programmatically
      provisionable. Where they are not, mark `BLOCKED-CREDENTIALS` and build the path anyway — a credential ask,
      never a descope.
- [ ] [BACKEND] P2. **Wire the bar into the readiness derivation** so a venue cannot be reported `BACKTESTABLE`
      without its smoke tests passing. Per the DERIVED ruling, an absent check yields "unverified", not a pass.

## Definition of done

- [ ] [BACKEND] P0. **Every in-scope unit has a passing batch smoke test**, or a tracked todo naming why not.
- [ ] [BACKEND] P0. **The suite fails loudly on a venue with no data** — demonstrated, not asserted. A green suite
      that has never been shown to go red is not evidence.
- [ ] [BACKEND] P1. **Every venue has a recorded testnet verdict**, including "none, simulate via our matching
      engine" where that is the answer.

## Progress Log

**2026-08-16 — authored, held at `draft`.** Forked from the umbrella's W5 item. Authored now so the smoke-test
contract, the Databento exemption's real boundary (by source, not by asset group) and the batch structure are
settled; held out of ingestion until the universe denominator exists, matching W4. The "what a smoke test must
prove" section is deliberately specific about failing-on-absence — the pass-on-zero-rows trap has already cost this
corpus real time, and a smoke-test plan that does not name it invites it back.
