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
parent_epic: uac_master
priority: P2
source: "discovered while shipping cefi_satellite_ao_dispatch_batch19-0b70e8929bb9"
resolved_by: ""
locked_by: ""
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    unified-api-contracts/tests/test_execution_service_venue_coverage_cascade_invariant.py,
    unified-api-contracts/tests/data/execution_service_venue_reachability_baseline.json,
    /codex/06-coding-standards/integration-testing-layers.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
  ]
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

## Status — RESOLVED 2026-08-15 via remediation 2 (verified 2026-08-16)

**The CI block is gone.** `kamino` was added to
`unified-api-contracts/tests/data/execution_service_venue_reachability_baseline.json`
(`unreachable_defi_venues: ["morpho", "kamino"]`) with a note recording the measured root cause:
`KaminoConnector` declares `supports_live = True`, but `DeFiAdapter` — the one dispatcher wired
into `live_execution_handler.py` — has zero references to a KAMINO venue-gate marker. Genuinely
unreachable, not a false positive from the invariant's v2 rewrite.

Verified 2026-08-16: `unified-api-contracts` `quality-gates.sh` runs green (991s), so the
fleet-wide quickmerge STAGE 3 block is cleared.

**The underlying gap is still open and is tracked** — `morpho` and `kamino` both remain
unreachable, under the P0 "wire a real dispatcher that reaches the connectors execution-service
already has" todo in
[`/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`](/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md).
So this issue is closed as a CI incident, not as a capability gap.

**Worth preserving — the invariant worked exactly as designed.** It was built on 2026-08-14 to
detect "a venue we can trade and cannot reconcile", and within a day it caught a real instance
that a human review had not. The baseline note also demonstrates the ratchet moving the right
way: the four `uniswap_*` entries were REMOVED in the same change that wired
`DeFiAdapter.uniswap_connector`.

**Correction to a claim made elsewhere**: this baseline is not "shrink-only". Its own note says
_"do not grow this list except by re-running the measurement and reviewing the diff"_ — growth is
permitted with a re-measurement and review, which is what `kamino` was. A strictly shrink-only
reading would have forced a rushed wiring fix during an unrelated ship.

- [ ] [AGENT] P2. **Close this doc once `morpho` and `kamino` leave the baseline** — and per the
      ratchet convention, remove each in the SAME change that wires its dispatcher path, never as
      a separate cleanup.
- **na-eligibility-audit 2026-08-16** [body-hash:01a99120392fffec]: KEEP-NA, valid — This is a resolved CI-incident doc: the fleet-wide unified-api-contracts quality-gates.sh block (kamino DeFi venue failing the execution-service venue-coverage-cascade invariant) was fixed via the sanctioned remediation-2 path (added kamino to the reachability baseline with a measured root-cause note) on 2026-08-15, verified green (991s quality-gates.sh run) on 2026-08-16 — the doc explicitly states 'this issue is closed as a CI incident, not as a capability gap.' The sole remaining open todo (line 92, '[AGENT] P2. Close this doc once `morpho` and `kamino` leave the
baseline') stays open until the P0 dispatcher-wiring work in
`venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md` lands and both venues can be removed from the
reachability baseline in that same change, per the ratchet convention this doc's body states above.
- **context-scout 2026-08-17**: populated context_scope (5 entries) — including a fingerprint match:
  `venue_readiness_and_registry_hardening_2026_08_16.md` independently records the identical
  `unreachable_defi_venues: ["morpho", "kamino"]` baseline content (`unified-api-contracts@88a71f8e`) and the same
  test file, actively tracking the wiring work that would let both venues leave the baseline (this doc's own sole
  open todo). context_scope added on both docs.
