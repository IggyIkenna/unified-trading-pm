---
doc_type: issue
title: test_canonical_prefix_literal_shape (solana_amm_depth_provider) fails on a clean execution-service tree — blocks quality-gates.sh fleet-wide
summary: >-
  execution-service's tests/unit/providers/test_solana_amm_depth_provider_canonical_path.py::
  test_canonical_prefix_literal_shape fails on a clean `live-defi-rollout` HEAD (confirmed via
  git stash + re-run, no local diff present), which makes `bash scripts/quality-gates.sh` exit
  non-zero for EVERY worker in this repo regardless of what they touched — the green-tree
  commit gate blocks all execution-service shipping until this is fixed. Found 2026-08-17 while
  shipping kraken_futures_wrong_rest_base_url_2026_08_17.md's P0 (unrelated Kraken Futures
  transport work) — QG failed with this single test as the only failure.
status: resolved
nature: issue
asset_group: [defi]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [ci, quality-gates, test-failure, blocking, defi, gcs-paths, pipeline-mode]
related: [/plans/active/defi_consolidated_closeout_2026_07_18.md]
created: 2026-08-17
resolved: 2026-08-17
author: interactive-session
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by: execution-service@1554abdf19
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Discovered while running `bash scripts/quality-gates.sh` in execution-service for
  kraken_futures_wrong_rest_base_url_2026_08_17.md — confirmed pre-existing by
  `git stash push --include-untracked` (removing all Kraken-Futures diff) + re-running the
  full gate: identical single failure on the byte-clean origin/live-defi-rollout tree.
context_scope:
  [
    execution-service/tests/unit/providers/test_solana_amm_depth_provider_canonical_path.py,
    execution-service/execution_service/providers/solana_amm_depth_provider.py,
  ]
---

# `test_canonical_prefix_literal_shape` fails on a clean tree — blocks execution-service QG fleet-wide

## What I found

Running `bash scripts/quality-gates.sh` in `execution-service` (both with my unrelated Kraken
Futures diff staged AND on a byte-clean `origin/live-defi-rollout` tree via
`git stash push --include-untracked` + re-run) produces the identical single test failure:

```
FAILED tests/unit/providers/test_solana_amm_depth_provider_canonical_path.py::test_canonical_prefix_literal_shape
1 failed, 8629 passed, 21 skipped, 1 xpassed, 89 warnings
```

Exit code 1 both times — confirming this is pre-existing on `live-defi-rollout` HEAD, not caused
by any in-flight diff. Since `quality-gates.sh`'s Pass-1 sentinel requires a fully green run (no
`--skip-*` flags permitted), this blocks EVERY worker shipping ANY change to execution-service
via the standard `quality-gates.sh` → `quickmerge --agent` flow, regardless of what they touch.

The test (`tests/unit/providers/test_solana_amm_depth_provider_canonical_path.py:56-70`)
independently reassembles the expected canonical GCS list-prefix for Solana AMM depth data via
`derive_pipeline_mode_for_row()` (`unified_trading_library.pipeline_mode_resolver`) +
`build_defi_partition_path()` (`unified_api_contracts.gcs_paths`), pinned against a literal
fixed-date string (`_DAY = date(2026, 5, 19)`, no dynamic/"today" dependency). The assertion
failure means one of those two UAC/UTL functions' output shape has drifted since this test was
last green — either the source-aware `pipeline_mode` derivation for `raydium`/`orca` no longer
resolves to `batch_onchain_subgraph`, or `build_defi_partition_path`'s path-segment shape/order
changed. I have NOT determined which — that diagnosis is DeFi/UAC pipeline-mode territory
(`/codex/02-data/pipeline-mode-partition.md`, `/codex/02-data/defi-canonical-naming-ssot.md`),
outside my assigned `backend_engineer` task's craft/domain scope
(kraken_futures_wrong_rest_base_url_2026_08_17.md is Kraken CeFi REST transport work).

## Why it matters

Not itself a live-money-correctness issue (this is a unit test pinning a GCS prefix shape, no
runtime data-pipeline mutation), but it fleet-wide blocks the green-tree commit gate for
execution-service — every worker touching this repo hits it. Per the `entity-rename-and-split-
consumer-migration-rule` pattern, whichever consumer (this test, or the provider it pins) is
stale needs the fix, not a suppression.

## What I have NOT verified

- Which side is correct: whether `derive_pipeline_mode_for_row`/`build_defi_partition_path`
  regressed, or the test's expected literal is stale against an intentional path-shape change.
- Whether `execution_service/providers/solana_amm_depth_provider.py`'s own runtime prefix-build
  call (not just the test's independent reassembly) is affected the same way — i.e. whether this
  is "only the test is stale" or "the actual provider is now building the wrong GCS prefix in
  production."

## Todos

- [x] ✅ [BACKEND] P1. **Diagnose + fix `test_canonical_prefix_literal_shape`** — determine whether
      `derive_pipeline_mode_for_row("raydium"/"orca", "defi", "dex_pool_state")` or
      `build_defi_partition_path(...)` changed shape since this test was last green, and whether
      `execution_service/providers/solana_amm_depth_provider.py`'s own runtime prefix-build is
      affected the same way (not just the test's independent reassembly). Fix whichever side is
      wrong — update the test's literal ONLY if the new shape is confirmed intentional/correct;
      otherwise fix the regressed function. Done-when: `bash scripts/quality-gates.sh` green in
      execution-service with this test passing (not skipped/xfailed). — **Shipped:
      `execution-service@1554abdf19`.** The RESOLVER, not the test, was correct:
      `unified-trading-library/unified_trading_library/pipeline_mode_resolver.py`'s
      `_VENUE_ONLY_OVERRIDES` maps `RAYDIUM`/`ORCA` → `BATCH_SOLANA_RPC`, an intentional,
      already-cited change ("RULED 2026-07-28, defi_satellite_ao_dispatch_batch16 todo 1" — each
      protocol fetches over its own native REST API grouped under the `solana_rpc` source label,
      not The Graph subgraph). The test's literal still pinned the pre-ruling
      `batch_onchain_subgraph` shape and was never updated after that ruling shipped — a stale
      test, not a regression. `solana_amm_depth_provider.py`'s own runtime prefix-build calls the
      identical `derive_pipeline_mode_for_row` function, so **production was already correct**;
      confirmed no writer/reader mismatch via MTDS's companion
      `solana_defi_handler._SOLANA_PROTOCOL_SOURCE_OVERRIDES` table too (raydium/orca dex_pool_state
      is single-source, no override needed there — comment in that file confirms). Fix: updated
      both literal fixture strings in the test to `batch_solana_rpc`, plus the now-stale
      `batch_onchain_subgraph` mentions in the test's own docstring/comments AND the same stale
      comment in the provider file (misleading docs = a finding, fixed in the same commit). Both
      tests in the file pass (`test_canonical_prefix_literal_shape`,
      `test_load_date_uses_canonical_prefix_and_honest_absence`); full `bash scripts/quality-gates.sh`
      green (171s) on `execution-service`, unblocking the repo-wide green-tree gate.

## Progress Log

- **2026-08-17**: Filed while shipping kraken_futures_wrong_rest_base_url_2026_08_17.md's P0 —
  confirmed pre-existing via stash + clean-tree re-run (RULES.md § 4b protocol). Declaring a
  `qg_red` repo-blocker for `execution-service` via `POST /api/repo-blockers` in the same turn.
- **2026-08-17 (slot 8, backend_engineer)** — Fixed and shipped. Full diagnosis + fix detail in
  the flipped todo above — `execution-service@1554abdf19`. Root cause: the pipeline_mode resolver
  was correct (RAYDIUM/ORCA dex_pool_state → `batch_solana_rpc`, an intentional 2026-07-28 ruling
  already cited in `pipeline_mode_resolver.py`); the test's literal was the stale side. This repo
  is now unblocked for the standard `quality-gates.sh` → `quickmerge --agent` flow — every other
  worker's shipments to `execution-service` should stop hitting this failure.
