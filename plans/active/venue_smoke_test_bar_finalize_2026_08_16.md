---
doc_type: plan
title: Venue smoke-test bar — finalize
summary: >-
  Gated finalize for `venue_smoke_test_bar_2026_08_16`. Verifies the smoke suite provably fails on a venue with no
  data (not merely that it passes), reconciles per-asset-group batch evidence into the umbrella's contract step 3,
  confirms every venue has a recorded testnet verdict, then runs the archival ritual on the parent and any AG batch
  left with zero open todos.
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
tags: [venue-readiness, smoke-test, testnet, finalize]
related:
  [
    /plans/active/venue_smoke_test_bar_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
  ]
created: 2026-08-16
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: backend_engineer
effort: low
drift_direction: none
depends_on: [venue_smoke_test_bar_2026_08_16]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: Authored alongside the parent plan per this workspace's mandatory finalize-plan rule (task_template.md §4).
context_scope:
  [
    /plans/active/venue_smoke_test_bar_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
  ]
---

# Venue smoke-test bar — finalize

- [ ] [REVIEW] P1. **Prove the suite goes RED.** Run it against a venue with no captured data and confirm it fails.
      A green suite that has never been demonstrated to fail is not evidence — and the pass-on-zero-rows trap has
      already cost this corpus real time, so this is the highest-value check in this plan, not a formality.
- [ ] [REVIEW] P2. Reconcile per-asset-group batch evidence into the umbrella's contract step 3 ("Market data —
      batch"), one row per (venue × data type). Re-verify each cited commit resolves.
- [ ] [REVIEW] P2. **Verify the Databento exemption was applied by SOURCE, not by asset group.** A TradFi venue
      sourced from anywhere else is in scope; if any were skipped on an asset-group assumption, they are unmeasured
      and must be reported as such rather than counted as exempt.
- [ ] [REVIEW] P2. Confirm **every venue has a recorded testnet verdict** — has one / behaves how / must be
      simulated through our own matching engine. A missing verdict blocks the venue's `PAPER-READY` claim.
- [ ] [DOC] P2. Run the standard 6-step archival ritual on `venue_smoke_test_bar_2026_08_16` once every todo is
      `[x]` and unlocked, including the corpus-wide referrer-path fixup.
- [ ] [DOC] P3. For each AG batch plan forked from the parent: if reconciling left it with zero open todos, run the
      same ritual on it rather than only flipping a checkbox.

## Progress Log

- **2026-08-16** — Authored alongside the parent plan. `status: active` with `depends_on`+`gate_on_depends: true` —
  ingested immediately but machine-held until every parent task is done. The parent is `status: draft` pending the
  universe denominator, so this stays gated until the parent is flipped to `active` and worked.

- **context-scout 2026-08-17**: refreshed context_scope (2 entries) — added the umbrella parent (todo 2 reconciles
  into its contract step 3); code-free finalize gate, no source path applicable.

- **context-scout 2026-08-20**: refreshed context_scope (2 entries)
