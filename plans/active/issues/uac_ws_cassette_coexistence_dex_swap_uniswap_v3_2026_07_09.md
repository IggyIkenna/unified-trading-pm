---
doc_type: issue
title: unified-api-contracts STEP-5.7X WS cassette coexistence gate broken by real dex_swap_uniswap_v3_ws connector
summary: |
  market-tick-data-service@d02cf88f (2026-07-09) replaced the gap-013 dex_swap_scaffold_ws BLOCKED-BUILD
  placeholder with a real live per-block Uniswap V3 DEX-swap WS connector, but unified-api-contracts'
  test_ws_cassette_coexistence.py::test_ws_connector_has_cassette (STEP 5.7X) was not updated with a matching
  *_ws.yaml cassette — quality-gates.sh now fails on a clean unified-api-contracts tree for every worker,
  unrelated to their own change.
status: resolved
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer]
tags: [quality-gates, ws-cassette, defi, uniswap-v3, cross-repo-drift]
related: []
created: 2026-07-09
last_updated: 2026-07-09
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: advance-code
source:
  [
    market-tick-data-service/market_tick_data_service/live/connectors/dex_swap_uniswap_v3_ws.py,
    unified-api-contracts/tests/test_ws_cassette_coexistence.py#L213,
  ]
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: unified-api-contracts@2bb9c165
---

# unified-api-contracts WS cassette coexistence gate broken by the real dex_swap_uniswap_v3_ws connector

## What I found

While shipping an unrelated backend-engineer task (AWS Lambda census,
`deployment_obs_backend_kinds_health_2026_07_09.md`) that touches `unified-api-contracts` (a new `DeploymentKind.LAMBDA`
enum member), a full `bash scripts/quality-gates.sh` run on `unified-api-contracts` failed with:

```
FAILED tests/test_ws_cassette_coexistence.py::test_ws_connector_has_cassette[dex_swap_uniswap_v3_ws]
```

`test_ws_connector_has_cassette` (STEP 5.7X, `plans/active/canary_coverage_qg_enforcement_2026_05_20.md` Phase 4)
dynamically discovers every `*_ws.py` connector in the sibling `market-tick-data-service` connectors dir and asserts
each has a matching `*_ws.yaml` WS cassette under `unified_api_contracts/external/<venue>/mocks/`.
`market-tick-data-service/market_tick_data_service/live/connectors/dex_swap_uniswap_v3_ws.py` was added at
`mtds@d02cf88f` ("feat(defi): real live per-block Uniswap V3 DEX-swap streaming (replaces gap-013 placeholder)",
2026-07-09 01:26), replacing the `dex_swap_scaffold_ws` BLOCKED-BUILD placeholder tracked in
`plans/active/issues/wsfeedconnector_phase35_gap_2026_07_06.md` gap-013. No cassette was added alongside it, and the
connector isn't in `unified-api-contracts/tests/test_ws_cassette_coexistence.py::_CONNECTOR_TO_VENUE` /
`_REST_POLLER_CONNECTORS` either.

Verified this is genuinely pre-existing and unrelated to my change: `git stash` (temporarily removing my UAC diff),
re-ran, same failure — confirmed the tree is broken independent of anything I touched.

Not something I can safely fix myself (out of DeFi-craft scope for this task, and fabricating WS frame data for a
cassette I have no real capture for would put synthetic frames into a fixture meant to pin real wire behavior — the same
"no fabricated success" principle CLAUDE.md applies elsewhere).

## Why it matters

`quality-gates.sh` requires the FULL test suite green to write the `.qg_last_passed_sha` sentinel that
`quickmerge.sh --agent` checks before it will ship — this is a HARD RULE (RULES.md/CLAUDE.md), not a soft gate. With
this test failing, **no worker can ship ANY change through `unified-api-contracts`** via the sanctioned quickmerge path
regardless of what they touched, until either a cassette is added or the connector is added to `_REST_POLLER_CONNECTORS`
(if it's not a frame-cassette candidate). This is a cross-repo (MTDS ↔ UAC) drift gap that silently blocks the whole
fleet's UAC pipeline — exactly the "big finding" class CLAUDE.md's Findings Triage calls out for operator notification.

**Impact on my own task**: blocks shipping the `DeploymentKind.LAMBDA` UAC change from
`deployment_obs_backend_kinds_health_2026_07_09.md`. I am proceeding with the `deployment-service` + `deployment-api`
halves of that task (their own `quality-gates.sh` runs are unaffected — they don't execute UAC's test suite) and leaving
the UAC-side enum addition uncommitted pending this fix, documented in that plan's Progress Log.

## Recommended decision

Whoever owns `dex_swap_uniswap_v3_ws` (or the DeFi live-connector rollout, `wsfeedconnector_phase35_gap_2026_07_06.md`)
adds a `*_ws.yaml` cassette for it under `unified_api_contracts/external/uniswap_v3/mocks/` (or the correct venue dir)

- a `_CONNECTOR_TO_VENUE` entry, mirroring the pattern the other DEX-swap scaffold connectors already use — OR, if a
  real WS-frame cassette isn't practical for a per-block on-chain stream, add `dex_swap_uniswap_v3_ws` to
  `_REST_POLLER_CONNECTORS` with a comment explaining why (analogous to the existing DeFi entries there: `curve_defi_ws`
  / `jito_defi_ws` / `morpho_defi_ws` / `orca_defi_ws` / `raydium_defi_ws`).

## Actionable todos

- [x] ✅ [CODE] P1. Add a `dex_swap_uniswap_v3_ws` cassette (or `_REST_POLLER_CONNECTORS`/`_CONNECTOR_TO_VENUE` entry,
      per the recommended decision above) so
      `unified-api-contracts/tests/test_ws_cassette_coexistence.py::test_ws_connector_has_cassette[dex_swap_uniswap_v3_ws]`
      passes on a clean tree (repo: unified-api-contracts) — unified-api-contracts@2bb9c165

## Progress Log

- 2026-07-09 — Filed by slot-4 (backend-engineer) after `bash scripts/quality-gates.sh` on `unified-api-contracts`
  failed on a clean-of-my-changes tree while shipping an unrelated `deployment_obs_backend_kinds_health_2026_07_09.md`
  task. Confirmed pre-existing/unrelated via `git stash` re-run.
- 2026-07-09 — Verified RESOLVED by slot-7 (data_engineering). `unified-api-contracts@2bb9c165` ("feat(lifecycle-class):
  extend DeploymentKind to 6 compute kinds", landed 2026-07-09 06:53:37 UTC, already merged into current `.tabs/7`
  worktree HEAD `dacdcad1`) added `"dex_swap_uniswap_v3_ws"` to `_REST_POLLER_CONNECTORS` in
  `tests/test_ws_cassette_coexistence.py`. This removes the connector from `_get_true_ws_connector_stems()`, so the
  parametrized `test_ws_connector_has_cassette[dex_swap_uniswap_v3_ws]` case no longer exists (confirmed: pytest
  collects 0 items for that node id post-fix). Ran the full `tests/test_ws_cassette_coexistence.py` file standalone: 149
  passed, 20 skipped, 0 failed. No code change needed from this task — closing as already-resolved by a prior slot's
  unrelated commit that happened to touch the same allowlist.
