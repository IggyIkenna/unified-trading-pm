---
doc_type: plan
title: Venue e2e wiring — finalize
summary: >-
  Gated finalize for `venue_e2e_wiring_2026_08_16`. Reconciles each per-asset-group batch's evidence back into the
  umbrella's Venue Readiness Contract, verifies that every unit's readiness verdict is DERIVED from a real check
  rather than declared, confirms no venue-coverage cascade baseline grew, then runs the archival ritual on the parent
  and any AG batch left with zero open todos.
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
tags: [venue-readiness, e2e-wiring, finalize]
related:
  [
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
  ]
created: 2026-08-16
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
effort: low
drift_direction: none
depends_on: [venue_e2e_wiring_2026_08_16]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: Authored alongside the parent plan per this workspace's mandatory finalize-plan rule (task_template.md §4).
context_scope:
  [
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
  ]
---

# Venue e2e wiring — finalize

- [ ] [REVIEW] P2. Reconcile every completed per-asset-group batch back into the umbrella's contract-step evidence
      (`venue_readiness_and_registry_hardening_2026_08_16`), one row per contract step per AG. Re-verify each cited
      commit resolves — do not trust a batch plan's own copy of the evidence line.
- [ ] [REVIEW] P1. **Verify every readiness verdict is DERIVED, not declared.** Per the operator's 2026-08-16
      ruling, a step with no real machine check must read `unverified`, never contribute a pass. Sample the units
      that reached `BACKTESTABLE` and confirm each step's verdict traces to an actual check — a derived model that
      quietly accepted declarations is the failure this todo exists to catch.
- [ ] [REVIEW] P1. Confirm **no venue-coverage cascade baseline grew** during the sweep. Growth is permitted only
      with a re-measurement and a reviewed diff; a baseline that grew silently to keep the sweep green is a
      regression, not a result.
- [ ] [REVIEW] P2. Re-check `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14` — if the sweep closed the
      read-vs-execute asymmetry for any venue, flip its checkbox there with evidence rather than leaving the issue
      doc stale.
- [ ] [DOC] P2. Run the standard 6-step archival ritual on `venue_e2e_wiring_2026_08_16` once every todo is `[x]`
      and unlocked, including the corpus-wide referrer-path fixup.
- [ ] [DOC] P3. For each AG batch plan forked from the parent: if reconciling left it with zero open todos, it is
      ALSO an archival candidate — run the same ritual, not just a checkbox flip.

## Progress Log

- **2026-08-16** — Authored alongside the parent plan. `status: active` with `depends_on`+`gate_on_depends: true` —
  ingested immediately but machine-held until every parent task is done. Note the parent itself is `status: draft`
  pending the universe denominator, so this finalize will stay gated until the parent is flipped to `active` and
  worked.

- **context-scout 2026-08-17**: refreshed context_scope (3 entries) — added the umbrella parent (todo 1 reconciles
  into its contract-step evidence) and the read-vs-execute-asymmetry issue doc (todo 4 names it explicitly);
  code-free finalize gate, no source path applicable.

- **context-scout 2026-08-20**: refreshed context_scope (3 entries)
