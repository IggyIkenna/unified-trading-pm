---
title: "unified-api-contracts: kamino DeFi venue fails execution-service reachability cascade invariant"
status: open
assigned_vm: NA
execution_scope: local-only
created: 2026-08-15
tags: [uac, execution-service, defi, venue-coverage-cascade, ci-blocking]
nature: issue
doc_type: issue
asset_group: defi
stage: execution
repos: [unified-api-contracts]
scope: engineer
summary: "unified-api-contracts venue-coverage cascade invariant fails on kamino DeFi venue (no reachable execution-service connector) — pre-existing on origin HEAD, blocks quickmerge fleet-wide."
related: [defi_consolidated_closeout_2026_07_18]
parent_epic: infrastructure_master
priority: P2
source: "discovered while shipping cefi_satellite_ao_dispatch_batch19-0b70e8929bb9"
resolved_by: ""
locked_by: ""
drift_direction: advance-code
depends_on: []
---

# uac_kamino_venue_reachability_cascade_regression_2026_08_15

## Finding

`unified-api-contracts` quality-gates.sh TESTS stage fails on a clean `origin/live-defi-rollout`
checkout (confirmed via `git stash` isolation — reproduces with zero local diff):

```
tests/test_execution_service_venue_coverage_cascade_invariant.py::
test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions

AssertionError: 1 strategy-service DeFi venue(s) have an execution-service connector that is
NEVER instantiated in production, beyond the known baseline:
  ['kamino']
```

This blocks `quickmerge.sh` STAGE 3 for every agent shipping through `unified-api-contracts`
(and any repo whose pre-flight audit finds UAC dirty mid-run), fleet-wide — not specific to any
one repo's own diff.

## Why

Discovered 2026-08-15 while shipping an unrelated Gap-3 change
(`cefi_satellite_ao_dispatch_batch19-0b70e8929bb9`, `unified-api-contracts` +
`market-tick-data-service`). `git stash` isolation confirmed the failure pre-exists on HEAD with
no local changes — some recent commit added a `kamino` strategy-service DeFi venue token without
wiring a reachable execution-service connector for it (invariant 3 of the venue-coverage cascade,
`/codex/06-coding-standards/integration-testing-layers.md`).

## How to apply

Two sanctioned remediations per the test's own failure message — pick whichever is actually true
of `kamino`'s current state (not evaluated here — out of scope for the task that discovered this):

1. Wire the `kamino` connector into a real execution-service dispatch path, or
2. If `kamino` is a deliberate, tracked gap (e.g. connector scaffolded ahead of go-live), add it
   to `tests/data/execution_service_venue_reachability_baseline.json` with a note explaining why.

## Status

Open — orphaned finding, no owning plan. Route to whichever AG closeout/dispatch batch owns
DeFi execution-service work, or resolve directly.
