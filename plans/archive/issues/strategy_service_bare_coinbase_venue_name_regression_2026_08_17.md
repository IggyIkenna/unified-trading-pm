---
doc_type: issue
title: strategy-service LDR HEAD red — bare "coinbase" venue_name regression
summary: >-
  `strategy-service` `origin/live-defi-rollout` HEAD (95f6c021) fails
  `tests/unit/position/test_position_adapter_factory.py::TestCoinbaseKrakenNowSupported::test_bare_coinbase_is_not_intercepted_by_the_cefi_route`
  ("assert 'coinbase' == 'ccxt:coinbase'"). Verified pre-existing and unrelated to a concurrent
  POLYMARKET archetype-slot ship (isolated the failing test against the parent commit, before that
  diff, byte-identical failure). Blocks any future strategy-service quickmerge re-gate until fixed.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [strategy]
repos: [strategy-service]
scope: [engineer]
tags: [qg-red, position-adapter, coinbase, cefi, repo-blocker]
related:
  [
    /plans/active/prediction_venue_e2e_batch1_2026_08_16.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-17
last_updated: "2026-08-17"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: agt-ed7f9d
source: prediction_venue_e2e_batch1_2026_08_16.md
---

# strategy-service: `test_bare_coinbase_is_not_intercepted_by_the_cefi_route` failing on LDR HEAD

## What I found

While shipping an unrelated change (`archetype_slots_cefi.py` — wiring POLYMARKET into
`MARKET_MAKING_CONTINUOUS`), `quickmerge --agent`'s Pass-1 re-gate failed on:

`tests/unit/position/test_position_adapter_factory.py::TestCoinbaseKrakenNowSupported::test_bare_coinbase_is_not_intercepted_by_the_cefi_route`

```
AssertionError: assert 'coinbase' == 'ccxt:coinbase'
```

Verified this is **pre-existing and unrelated to my diff**: checked out `strategy-service`
`origin/live-defi-rollout` HEAD (`95f6c021`, before my commit) in isolation and reran the single
test — byte-identical failure. My change touches only `archetype_slots_cefi.py`,
`batch_utils.py`, and `test_all_catalogued_archetypes_construct_and_fire.py` (a totally
different subsystem — v2 strategy archetype slot declarations, not the position-adapter
factory).

Root cause (from the test's own body, `tests/unit/position/test_position_adapter_factory.py:54-75`):
the test tries `get_position_adapter("coinbase", ...)`, expects either a `ValueError`
(cbETH address not yet migrated in the UAC registry — explicitly tolerated) or a non-CCXT
adapter whose `venue_name == "ccxt:coinbase"`. Currently it returns a non-CCXT adapter (the
`not isinstance(adapter, CCXTPositionAdapter)` assertion passes) but that adapter's
`venue_name` is literally `"coinbase"`, not `"ccxt:coinbase"` — the generic-token-balance
path's `venue_name` construction doesn't match what the test expects now that cbETH's UAC
registry address appears to be migrated (no more `ValueError` fallthrough).

## Why it matters

This is LDR HEAD red for ANY future `strategy-service` shipper whose changeset happens to
touch a file the full test suite runs against (i.e. everyone) — `quickmerge --agent`'s Pass-1
re-gate requires the WHOLE suite green, so this blocks unrelated ships until fixed.

## Recommended decision

Fix `get_position_adapter`'s generic-token-balance branch for bare `"coinbase"` (or the LST
adapter it delegates to) to set `venue_name = "ccxt:coinbase"` to match the test's contract —
or, if the test's expectation is now stale (e.g. the venue_name contract intentionally changed
when cbETH's address was migrated), update the test to assert the new real value instead.
Needs someone who owns `strategy_service/position/position_interface/` (position/CeFi routing
craft, not archetype-slot wiring) to pick the right side of that fix.

## Todos

- [x] ✅ [BACKEND] P1. Fix `strategy-service`'s bare-`"coinbase"` `venue_name` regression —
      `get_position_adapter("coinbase", ...)` returns `venue_name="coinbase"` where
      `tests/unit/position/test_position_adapter_factory.py::TestCoinbaseKrakenNowSupported::test_bare_coinbase_is_not_intercepted_by_the_cefi_route`
      expects `"ccxt:coinbase"` — either fix the adapter's `venue_name` or update the test to
      the new intended contract (repo: strategy-service). — strategy-service@e44ced71

## Progress Log

- 2026-08-17 (cicd escalation agt-ed7f9d): resolved. The TEST was wrong, not the code —
  `_generic_token_balance_adapter` (factory.py:301) sets `venue_name=v.lower()` for the bare
  `"coinbase"` LST path by design (never the `"ccxt:"` prefix, which is the CCXT-adapter
  naming convention only). The `"ccxt:coinbase"` assertion in
  `test_bare_coinbase_is_not_intercepted_by_the_cefi_route` was a copy-paste duplicate of the
  sibling `test_coinbase_spot_resolves_via_ccxt`'s assertion, introduced in the same commit
  (32386ce1) that this doc's own analysis traced the failure to — and it directly contradicts
  the test's own docstring ("not a specific outcome ... not something this test should couple
  to"). Removed the erroneous assertion. Verified: local `quality-gates.sh` green (6073
  passed, 0 failed, `✅ ALL QUALITY GATES PASSED`). Shipped via quickmerge —
  strategy-service@e44ced71, ancestry-verified on origin/live-defi-rollout. Repo-blocker
  RB-81272042 resolved (1 waiter notified). This unblocks promotion PR
  strategy-service#610 (LDR→main) — the fleet promote cycle picks up the new LDR HEAD on its
  next tick.
