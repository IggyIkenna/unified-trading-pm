---
doc_type: issue
title: WS cassette coexistence test failing — `dex_swap_uniswap_v3_ws` connector landed without a UAC venue/cassette
summary: |
  `unified-api-contracts` test `test_ws_cassette_coexistence.py::test_ws_connector_has_cassette[dex_swap_uniswap_v3_ws]`
  fails on `live-defi-rollout` HEAD (reproduced via `git stash` — pre-existing, unrelated to any change in this
  session). MTDS landed `market-tick-data-service/market_tick_data_service/live/connectors/dex_swap_uniswap_v3_ws.py`
  but the WS-cassette coexistence map (`unified-api-contracts/tests/test_ws_cassette_coexistence.py::_CONNECTOR_TO_VENUE`)
  and a matching `unified_api_contracts/external/<venue>/mocks/*_ws.yaml` cassette were never added — the "Batch = Live"
  SSOT requires every live WS connector to have a frame cassette so the canary can detect schema drift. Surfaced by a
  full `quality-gates.sh` run on `unified-api-contracts` while landing `deployment_obs_backend_kinds_health_2026_07_09`
  task 1 (unrelated DeploymentKind/Cloud-Run-services change) — filed instead of absorbed since it's DeFi/MTDS-domain
  work, outside the deployment-observability plan's scope.
status: open
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer]
tags: [ws-cassette, defi, mtds, uniswap, canary-coverage]
related: [deployment_obs_backend_kinds_health_2026_07_09.md]
created: 2026-07-09
last_updated: 2026-07-09
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
source:
  [
    unified-api-contracts/tests/test_ws_cassette_coexistence.py#L56,
    market-tick-data-service/market_tick_data_service/live/connectors/dex_swap_uniswap_v3_ws.py,
  ]
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

# WS cassette coexistence test failing — `dex_swap_uniswap_v3_ws` has no UAC venue/cassette

## What I found

`tests/test_ws_cassette_coexistence.py::test_ws_connector_has_cassette[dex_swap_uniswap_v3_ws]` fails on
`unified-api-contracts` HEAD with:

```
AssertionError: Connector 'dex_swap_uniswap_v3_ws' not in _CONNECTOR_TO_VENUE map. Add it to
test_ws_cassette_coexistence.py when landing a new WS connector.
```

Confirmed pre-existing (reproduces identically via `git stash` before any change made in this session).
`market-tick-data-service/market_tick_data_service/live/connectors/dex_swap_uniswap_v3_ws.py` exists, but:

- `_CONNECTOR_TO_VENUE` in `unified-api-contracts/tests/test_ws_cassette_coexistence.py` has no
  `dex_swap_uniswap_v3_ws` entry.
- There is no `unified_api_contracts/external/<venue>/mocks/*_ws.yaml` cassette for this connector (only an unrelated
  REST cassette exists: `unified_api_contracts/external/thegraph/mocks/uniswap_v3_pools.yaml`).

## Why it matters

The WS cassette coexistence gate enforces "Batch = Live": every live WS connector needs a frame cassette so the canary
can detect live schema drift. Without one, this connector is unguarded, and the repo-wide `quality-gates.sh` run
currently fails on this test for EVERY agent working in `unified-api-contracts`, not just DeFi work.

## Recommended decision

Whoever owns the `dex_swap_uniswap_v3_ws` connector rollout should either:

- (a) Add a real `*_ws.yaml` cassette (with actual captured frames) under a `dex_swap_uniswap_v3` (or equivalent)
  venue dir + register it in `_CONNECTOR_TO_VENUE`, or
- (b) If this connector is a REST poller misnamed `*_ws.py` (like the existing `_REST_POLLER_CONNECTORS` carve-out),
  add it to that frozenset instead.

## Todos

- [ ] [DATA] P2. Determine whether `dex_swap_uniswap_v3_ws` is a true WS connector or a REST poller; if true-WS, add a
      `*_ws.yaml` cassette under the correct UAC venue dir + register it in `_CONNECTOR_TO_VENUE`
      (`unified-api-contracts/tests/test_ws_cassette_coexistence.py`); if REST-poller, add it to
      `_REST_POLLER_CONNECTORS` instead. (repo: unified-api-contracts, market-tick-data-service)
