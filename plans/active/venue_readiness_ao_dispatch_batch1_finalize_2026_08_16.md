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

- [ ] [REVIEW] P1. **Prove both new SIT invariants go RED.** Invariants 2 and 4 must each be demonstrated failing on
      a deliberately-introduced regression — a mode-coverage gap for 2, an address mismatch for 4. A green invariant
      that has never been shown to fail is not evidence, and this batch adds two of them at once.
- [ ] [REVIEW] P2. Reconcile each shipped todo back into its true parent's own checkbox: the SIT invariants and the
      LST migration into `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14` and
      `e2e_wiring_reachability_audit_2026_08_15`, the skills audit into `venue_smoke_test_bar_2026_08_16`. Re-verify
      each cited commit resolves rather than trusting the parent's copy of the evidence line.
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
