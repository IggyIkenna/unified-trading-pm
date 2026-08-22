---
doc_type: plan
title: Venue smoke-test bar — a batch smoke test per data type per venue, plus testnet where reachable
summary: >-
  W5 of the venue-readiness umbrella. Establishes the minimum provable bar for every venue: a batch smoke test per
  data type, so at minimum we know we can backtest it honestly. Databento-sourced venues are exempt per operator
  ruling (that source is already trusted). Where credentials exist or can be provisioned programmatically, add a
  testnet smoke test too.
status: active
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
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
drift_direction: advance-code
depends_on: [defi_venue_smoke_batch1_2026_08_20, cefi_venue_smoke_batch1_2026_08_20, sports_venue_smoke_batch1_2026_08_20, tradfi_venue_smoke_batch1_2026_08_20, prediction_venue_smoke_batch1_2026_08_20]
gate_on_depends: true
estimate_class: infra
estimate_baseline_ai_days: 12.0
estimate_calibrated_ai_days: 9.6
assigned_role: backend_engineer
effort: high
last_updated: "2026-08-17"
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

- [x] ✅ [BACKEND] P0. **Audit all four `/data-pipeline-check-*` skills against current canonical expectations before
      W5 depends on them.** Per skill: does its canonical leg call `canonical_path_violations()` or re-implement the
      rule; does it validate the filename instrument_id (the oracle is PATH-STRUCTURE-ONLY and VALUE-BLIND, so
      id-form and `instrument_type`/`data_type`/`venue`/`chain` VALUES must be checked separately or explicitly
      declared unchecked); is its stale-migration banner still true. Done-when: each skill either routes through the
      oracle or records why it cannot, and every banner is re-dated or removed. **This is a prerequisite of every
      other todo in this plan** — a harness that reports green over migrated data makes the whole bar worthless.
      — **Reconciled 2026-08-17 (slot 15, review), shipped via `venue_readiness_ao_dispatch_batch1_2026_08_16`, not
      by this plan's own (still-`draft`, undispatched) todo.** `unified-trading-pm@04fec8f2c4` added a per-skill
      "Canonical-oracle audit (2026-08-16)" section to all four `SKILL.md` files: IS/MDPS/features correctly do NOT
      route through the oracle (their write targets fall outside its `raw_tick_data/by_date/` scope — the sports
      reference-bucket exemption class), now stated inline instead of implicit; MTDS was found to be a real gap (its
      `canonical` leg was TradFi-only despite CEFI/DEFI being oracle-covered since 2026-07-20/23) and both
      misleading-banner claims (IS, MTDS) were re-verified still accurate. **The MTDS gap this audit found was then
      fixed, closing the loop this todo's done-when requires** — `market-tick-data-service@f90bf09a37` added
      `_run_oracle_canonical_leg`, routing CEFI/DEFI shards through `canonical_path_violations(require_pipeline_mode=True)`
      with negative-control proof (a path missing `pipeline_mode=` fails structurally, a raw wire-symbol filename fails
      on id-form, a genuine canonical path passes). Both SHAs independently re-verified this session as live ancestors
      of `origin/live-defi-rollout`; content spot-checked (the "Canonical-oracle audit" section is present verbatim in
      `cursor-configs/skills/data-pipeline-check-mtds/SKILL.md`, and `_run_oracle_canonical_leg` exists in MTDS's
      `pipeline_e2e_check.py`). **Filename id-form and independent `venue`/`data_type`/`chain` VALUE-checks remain
      declared unchecked where the oracle doesn't cover them (IS, MDPS, features)** — per this workspace's standing
      rule that the oracle is path-structure-only and value-blind, this is the correct, explicitly-stated outcome, not
      a remaining gap in this todo.

Contract step 1 (venue declared, batch/live capability axis) belongs to
[venue_capability_route_axis_and_cross_ag_declarations_2026_08_14](/plans/active/venue_capability_route_axis_and_cross_ag_declarations_2026_08_14.md),
which also already declares `batch = none` for venues with no batch source — those must not be reported as smoke
failures, they are declared absences.

## Why this was held at `status: draft`

Same single blocker as W4: the per-(venue × data type) denominator did not exist yet. A smoke-test bar reported
over an undefined set produces a percentage with no denominator — the exact shape of unfalsifiable progress this
workspace bans. **Flipped to `active` 2026-08-20 (/plan-reconcile F-G31-3)** — the umbrella's "Define the universe
precisely for W4/W5" todo landed 2026-08-16 (**192 declared venues, 353 (venue, data_type) pairs at that
measurement**,
`unified-api-contracts@e7ee398117`), the same day this doc's own text says it was waiting for. Its sibling W4
(`venue_e2e_wiring_2026_08_16.md`) flipped to `active` on that same criterion the same day; this doc's flip was
simply never applied, leaving 5 genuinely-unblocked P0/P1 todos undispatchable for 4 days.

## What a smoke test must actually prove

The trap here is a test that passes on absence. A smoke test that queries a shard, gets zero rows, and exits 0 has
proved nothing — and this corpus has already been burned by entity-agnostic checks passing for hours while the
target wrote zero rows.

- [ ] [BACKEND] P0. **Specify the smoke-test contract before writing any.** At minimum it must assert: rows were
      actually captured for the named (venue, data type) unit; they land at a CANONICAL path (per the machine
      oracle, not a re-implemented rule); the manifest reconciles for that shard atom; and the capture_status is a
      genuine capture rather than `expected_unattempted`. Done-when: the contract is written here and one reference
      implementation exists that provably FAILS on a venue with no data.
- [x] ✅ [BACKEND] P0. **Derive the in-scope unit list** — every (venue × data type) minus the Databento-sourced
      exemptions, with the exemption set enumerated explicitly rather than described. SHIPPED —
      `unified-api-contracts@23cf22dda6` adds the permanent, re-runnable
      `scripts/generate_venue_smoke_test_work_list.py`, which resolves the first venue-capable source per cell rather
      than applying a venue-wide exemption. Measured 2026-08-20: 361 declared pairs, 8 Databento exemptions, and 353
      in-scope rows (CEFI 70, DEFI 232, PREDICTION 4, SPORTS 39, TRADFI 8). Explicit exemptions are CBOE/ohlcv_1m,
      CBOE/ohlcv_1s, CME/ohlcv_1m, CME/ohlcv_1s, NASDAQ/ohlcv_1m, NASDAQ/ohlcv_1s, NYSE/ohlcv_1m, and NYSE/ohlcv_1s.
      Focused tests cover uniqueness, dual-source CBOE routing, and Yahoo-only KRX routing; the full UAC quality gate
      passed.
- [x] ✅ [BACKEND] P0. **Fork per-asset-group dispatch batches**, matching W4's structure so the two workstreams stay comparable per AG and do not each invent their own batching. — `unified-trading-pm@8bb0f87e3b` + evidence: five AG plans and five gated finalize companions added for 353 source-scoped in-scope rows.
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

**2026-08-17 (slot 15, review) — reconciled the AO dispatch batch's skills-audit shipment back into this doc.**
Despite this plan sitting `status: draft` (held for the universe-denominator blocker), `venue_readiness_ao_dispatch_batch1_2026_08_16`
independently dispatched and shipped this doc's own P0 skills-audit todo as a todo of its own, plus the real MTDS
canonical-leg gap that audit found. Flipped this doc's todo to done, citing both: `unified-trading-pm@04fec8f2c4`
(the per-skill audit) + `market-tick-data-service@f90bf09a37` (the MTDS canonical-leg fix the audit surfaced). Both
SHAs independently re-verified as live ancestors of `origin/live-defi-rollout` and content spot-checked, not trusted
from the batch plan's own copy of the evidence line. Part of
`venue_readiness_ao_dispatch_batch1_finalize_2026_08_16`'s reconciliation todo.

**CORRECTED 2026-08-20 (/plan-reconcile F-G31-3)**: the claim above that "this does not flip this plan's `status` —
the universe-denominator blocker... is unaffected" was itself wrong. The umbrella's "Define the universe precisely
for W4/W5" todo had already landed the DAY BEFORE this entry was written (2026-08-16,
`unified-api-contracts@e7ee398117`, 192 declared venues / 353 pairs) — this doc's own stated flip criterion. Flipped
`status: draft` → `active` in this correction pass, 4 days later than it should have.


**2026-08-20 — in-scope smoke-test list shipped.** `unified-api-contracts@23cf22dda6` added the source-scoped
generator and focused tests. The live registry now measures 200 declared venues / 361 pairs; the generator excludes
only the eight explicitly listed Databento cells and reports 353 rows for batch smoke testing. It resolves source by
`(venue, data_type)`, preserving CBOE's Yahoo Treasury-index cell and KRX's Yahoo daily cells in scope. UAC's full
quality gates passed (1155s); the landed commit is an ancestor of `origin/live-defi-rollout`.

**2026-08-20 — citation correction.** The earlier entry and checkbox cited the pre-push local SHA
`03c79c82a`, which was not the landed commit. Corrected both references to the quickmerge-verified
`unified-api-contracts@23cf22dda6`.

**2026-08-22 (slot 19, review) — Sports rows + testnet verdict reconciled into this contract.** Source:
`/plans/active/sports_venue_smoke_batch1_2026_08_20.md` (all five todos closed). **Current generator output
cited**: `unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py`, measured 2026-08-20/21 at
39 in-scope Sports (venue, data_type) rows (32 declared `sports` venues × `odds`, minus the Databento-exempt
set — 0 Sports cells fall in the 8-cell Databento exemption list). **Data floor cited**:
`/codex/02-data/sports-2020-06-data-floor.md`'s 2020-06-06 odds-start floor — the batch's own floor/oracle
verification todo (slot-4, 2026-08-21) directly asserted every Sports row resolves to a non-Databento source
and that the pre-floor `2020-06-05` window is rejected with the documented empty/inverted-range signal for
every distinct resolved source/data-type pair, plus the canonical-path negative control rejected via
`canonical_path_violations(require_pipeline_mode=True)`.
- **Row-level capture status**: VM execution attempt #2 (`pipeline-e2e-check-mtds-20260821-154512-a0ace0`,
  `--generator-scoped-sports`) measured 99 cells across the 33-shard generator-scoped set (force/skip/canonical
  legs): 0 passed, 75 failed fail-closed (`no_parquet_under:...` / `canonical_no_matching_objects_in_test_bucket`),
  24 skipped (`no_captured_data_for_cell`, declared cells with no captured data at all). RED, not a false pass —
  root cause is `--auto-day`-sampled days with no scheduled fixture/odds activity for the sampled venue, the same
  mechanism `/plans/archive/issues/sports_venue_smoke_checker_scope_and_canonical_gap_2026_08_20.md` already
  documented. This satisfies the "fails loudly, demonstrated not asserted" Definition-of-done bar for Sports
  specifically — the suite went RED on genuine absence, and every row's reason is individually named.
- **Testnet verdict, all 33 declared `VENUES_BY_ASSET_GROUP["sports"]` venues** (0 real venue-hosted
  testnet/sandbox/demo endpoint found for any): Group A (`BETFAIR_EX_UK`, `BETFAIR_EX_EU`) — real execution
  adapter, credential-blocked, simulated via the Betfair-specific `betfair_paper_matcher.py`. Group B
  (`MATCHBOOK`) — real execution adapter, production-only API, falls back to the generic `PaperBettingAdapter`.
  Group C (30 data-axis-only venues, no execution adapter) — simulated via the generic `PaperBettingAdapter`.
  Full per-venue table in `sports_venue_smoke_batch1_2026_08_20.md`'s 2026-08-22 (slot 13) Progress Log entry.
  0 of the 33 venues have any testnet endpoint at all (not merely unprovisioned), so no `BLOCKED-CREDENTIALS`
  tag applies to Sports — every venue's answer is "simulate via matching engine," recorded per-venue as this
  section's W5 P1 todo requires.

Per-AG reconciliation only — this entry closes Sports' own slice of the shared testnet/row-coverage todos above;
those todos stay unchecked pending the sibling DeFi/CeFi/TradFi/Prediction reconciliations
(`defi_venue_smoke_batch1_2026_08_20_finalize.md` / `cefi_...` / `tradfi_...` / `prediction_...`, each carrying
the same-shaped `[REVIEW] P2. Reconcile every <AG> row...` todo).
