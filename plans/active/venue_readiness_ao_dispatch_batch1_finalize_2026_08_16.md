---
doc_type: plan
title: Venue readiness AO dispatch batch 1 — finalize
summary: >-
  Gated finalize for `venue_readiness_ao_dispatch_batch1_2026_08_16`. Reconciles each shipped todo's evidence back
  into its true parent doc (the two reachability issue docs, the smoke-test-bar plan), verifies the two new SIT
  invariants were demonstrated to FAIL rather than merely to pass, then runs the archival ritual on any parent left
  with zero open todos.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, strategy, execution]
repos:
  [
    unified-api-contracts,
    execution-service,
    strategy-service,
    system-integration-tests,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [venue-readiness, ao-dispatch, finalize]
related:
  [
    /plans/active/venue_readiness_ao_dispatch_batch1_2026_08_16.md,
    /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
  ]
created: 2026-08-16
last_updated: "2026-08-16"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
effort: low
drift_direction: none
depends_on: [venue_readiness_ao_dispatch_batch1_2026_08_16]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: Authored alongside the parent plan per this workspace's mandatory finalize-plan rule (task_template.md §4).
context_scope: [/plans/active/venue_readiness_ao_dispatch_batch1_2026_08_16.md]
---

# Venue readiness AO dispatch batch 1 — finalize

- [x] ✅ [REVIEW] P1. **Prove both new SIT invariants go RED.** Invariants 2 and 4 must each be demonstrated failing on
      a deliberately-introduced regression — a mode-coverage gap for 2, an address mismatch for 4. A green invariant
      that has never been shown to fail is not evidence, and this batch adds two of them at once.
      — **Independently re-demonstrated live this session (slot 11), not trusted from either parent plan's own
      Progress Log claim.** Invariant 2 (`unified-api-contracts/tests/test_strategy_position_read_mode_cascade_invariant.py::test_mtds_venues_have_strategy_position_read_coverage_no_new_regressions`):
      removed `ACROSS-ETHEREUM` from `tests/data/strategy_position_read_mode_baseline.json`'s
      `missing_position_read_coverage` list (a real, still-missing venue — simulates a coverage gap shipping
      un-baselined) — test FAILED with `AssertionError: 1 NEW MTDS batch-capture venue(s) shipped ... ['ACROSS-ETHEREUM']`;
      `git checkout` restored the file byte-identical, re-ran, 4/4 green. Invariant 4
      (`unified-api-contracts/tests/test_lst_token_address_drift_invariant.py::test_lst_token_addresses_no_drift_from_execution_service`):
      edited `execution-service/execution_service/defi_execution/protocols/eigenlayer.py`'s
      `LST_TOKEN_ADDRESSES["cbETH"]` to a deliberately wrong literal (`0xDEADBEEF...`) — test FAILED with
      `AssertionError: 1 LST token address mismatch(es) ... ETHEREUM/cbETH: UAC registry=... != execution-service
      ...=0xDEADBEEF...`; `git checkout` restored the file byte-identical, re-ran, 7/7 green. Both repos confirmed
      clean (`git status --porcelain` empty) after restore — no code shipped, this todo is verification-only.
      **Side finding, not fixed (out of scope for this todo, noted for the next reconciliation pass)**: invariant
      2's own baseline JSON `description` field and the sibling test module's docstring both still say "106 of 159"
      MTDS batch venues lack coverage; the live baseline file actually holds 99 entries today (confirmed via
      `git log` on the file: 106 → 101 via `unified-api-contracts@7d168775` "unstale baselines" → 99 via a later
      untraced commit) — legitimate ratchet-down activity per the file's own convention, just never reflected in
      the prose count. Not fixed here since a correct fix needs the full 159-venue re-measurement, not a 1-line
      edit, and it doesn't affect this invariant's correctness (the test reads the JSON list, never the prose).
- [x] ✅ [REVIEW] P2. Reconcile each shipped todo back into its true parent's own checkbox: the SIT invariants and the
      LST migration into `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14` and
      `e2e_wiring_reachability_audit_2026_08_15`, the skills audit into `venue_smoke_test_bar_2026_08_16`. Re-verify
      each cited commit resolves rather than trusting the parent's copy of the evidence line.
      — **Done, all six cited SHAs independently re-verified as live ancestors of `origin/live-defi-rollout` before
      any checkbox was flipped (not trusted from batch1's own copy of the evidence lines) — content spot-checked too,
      not just ancestry.** `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`: flipped its own SIT
      invariant 2 todo + deferred-work table row (`unified-api-contracts@86d5f5af46`,
      `system-integration-tests@cce1adebc6`). `e2e_wiring_reachability_audit_2026_08_15.md`: flipped its own SIT
      invariant 2 todo (same two SHAs) and added a Chunk-B addendum to its already-checked LST-migration todo
      (`execution-service@529af8d22c`, `unified-api-contracts@6151de2a2a`). `venue_smoke_test_bar_2026_08_16.md`
      (held `status: draft`): flipped its own skills-audit todo, citing both the audit
      (`unified-trading-pm@04fec8f2c4`) and the MTDS canonical-leg gap it found and that got fixed
      (`market-tick-data-service@f90bf09a37`) — did not flip the plan's `status` itself, since the universe-denominator
      blocker for its OTHER todos is unaffected. Each parent doc also got a Progress Log entry naming the batch as the
      actual shipping session, since none of these three parent docs' authors cross-checked against batch1 before it
      duplicated their todos.
- [ ] [REVIEW] P2. **Confirm the LST migration did not add eETH or rsETH.** Their absence is a deliberate operator
      ruling (2026-08-16), not an oversight — a worker "completing" the registry would silently reintroduce the orphan
      class the reachability gate exists to catch.
- [ ] [REVIEW] P2. **Re-check the skills audit's verdicts against the oracle's own blind spots.** The oracle is
      path-structure-only and value-blind, so a skill that now calls it is still not checking filename instrument_id
      or the `instrument_type`/`data_type`/`venue`/`chain` values. Confirm each skill either checks those separately
      or explicitly declares them unchecked — "routes through the oracle" alone is not the bar.
- [ ] [DOC] P2. Run the standard 6-step archival ritual on `venue_readiness_ao_dispatch_batch1_2026_08_16` once every
      todo is `[x]` and unlocked, including the corpus-wide referrer-path fixup.
- [ ] [DOC] P3. For each parent doc touched: if reconciling left it with zero open todos, it is ALSO an archival
      candidate — run the ritual, not just a checkbox flip.

## Progress Log

- **2026-08-16** — Authored alongside the parent. `status: active` with `depends_on`+`gate_on_depends: true` —
  ingested immediately, machine-held until every parent task is done.

- **2026-08-17 (slot 11, review) — REVIEW P1 "prove both SIT invariants go RED" flipped.** Live-reproduced both
  negative controls myself (detail in the flipped checkbox above) rather than trusting the parent plan's own
  Progress Log claims that this had already been demonstrated. Both invariants correctly failed on a deliberately
  introduced regression and correctly passed once reverted; both touched repos verified clean afterward. Noted one
  small pre-existing doc-staleness (invariant 2's baseline description says "106", the file holds 99) as a
  non-blocking side finding — not fixed, needs a full re-measurement, doesn't affect the invariant's correctness.

- **2026-08-17 (slot 15, review) — REVIEW P2 "reconcile each shipped todo back into its true parent" flipped.**
  Read all three parent docs in full (`venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`,
  `e2e_wiring_reachability_audit_2026_08_15.md`, `venue_smoke_test_bar_2026_08_16.md`) and confirmed batch1's SIT
  invariant 2, LST migration Chunk B, and skills-audit todos each had a matching still-open (or already-checked but
  incomplete) copy in a parent that was never updated when batch1 shipped — same duplication shape batch1's own
  Progress Log already documented for its close-all and SIT-invariant-4 todos, just never closed on the receiving
  end. Independently re-verified (before touching any checkbox) that all 6 cited SHAs are live ancestors of
  `origin/live-defi-rollout` and spot-checked their content against each claim — did not trust batch1's own copy of
  the evidence lines. Full detail in the flipped checkbox above. Next open item is the P2 "confirm the LST migration
  did not add eETH or rsETH" todo.
