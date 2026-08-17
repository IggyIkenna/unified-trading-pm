---
doc_type: issue
title: >-
  market-tick-data-service QG RED (pre-existing, not slot-24's diff): 2 DeFi handler unit tests fail on current LDR tip
summary: >-
  Full `quality-gates.sh` run for an unrelated cefi marker-migration task surfaced 2 failing unit tests in
  market-tick-data-service. Verified pre-existing via stash/re-run on a clean tree at the same HEAD
  (81f5fb8f) — byte-identical failures with the diff removed. Filed per worker.md § "4b) BLOCKED ON THE REPO, not
  your task — declare a repo-blocker" (repo-blocker protocol; the doc's own §4 is unrelated "Backlog-edit hygiene" —
  corrected citation 2026-08-17).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [qg-red, repo-blocker, defi, lst-rates, solana]
related: [/plans/active/defi_consolidated_closeout_2026_07_18.md]
created: 2026-08-17
author: slot-24 (data_engineering worker)
parent_epic: defi_master
priority: P2
estimate_class: refactor
assigned_role: backend_engineer
source: >-
  Surfaced by `bash scripts/quality-gates.sh --no-fix` while shipping
  `cefi_dated_perps_margin_marker_coverage_extension_2026_08_17` (BYBIT/COINBASE-FUTURES/BITGET-FUTURES marker
  migration). Confirmed pre-existing: `git stash` (removing the marker-migration diff) + re-run reproduces the SAME 2
  failures on HEAD=81f5fb8f, `origin/live-defi-rollout` (0 commits behind at the time of the check).
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: none
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# market-tick-data-service QG RED — 2 pre-existing DeFi handler test failures (2026-08-17)

## What I found

Both failures reproduce identically with or without the marker-migration diff, on `origin/live-defi-rollout`
HEAD=81f5fb8f (verified via `git stash` + targeted re-run):

1. `tests/unit/test_solana_defi_handler.py::TestCollectProtocol::test_writes_data_to_gcs` — asserts the write path
   contains `pipeline_mode=batch_onchain_subgraph`, but the actual written path carries
   `pipeline_mode=batch_solana_rpc`:

   ```
   AssertionError: assert 'day=2026-03-28/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue=KAMINO/chain=SOLANA/' in
   'raw_tick_data/by_date/day=2026-03-28/pipeline_mode=batch_solana_rpc/asset_group=defi/venue=KAMINO/chain=SOLANA/instrument_type=pool/data_type=dex_pool_state/KAMINO-SOLANA:POOL:SOL-USDC.parquet'
   ```

   Most likely stale-test-assertion drift from a recent KAMINO-SOLANA pipeline_mode change — the two most recent
   commits touching this area on LDR are `71106397 feat: wire oracle_prices capture for KAMINO-SOLANA` and
   `794c1472 feat(solana-defi): wire KAMINO-SOLANA oracle_prices capture`.

2. `tests/unit/test_lst_rates_handler.py::test_process_writes_canonical_partition_per_protocol_chain` — the manifest
   flush logs a non-fatal warning (`DefiManifestRecorder(lst_rates): flush failed (non-blocking): 404 ... bucket
   "lst-rates-bucket" does not exist`), then the test itself fails downstream (assertion not captured in this pass's
   truncated tail — needs a full-output re-run to pin the exact assert). Plausibly a test-fixture bucket-mock gap
   introduced by the same LST-rates venue-expansion work
   (`8746708c feat(defi): acquire lst_rates for new staking/restaking/vault venues`).

## Why it matters

Blocks a clean `quality-gates.sh` full run for EVERY slot shipping to this repo (the commit-boundary quality gate is
repo-wide, not diff-scoped) — not just this task's marker-migration work.

## Recommended decision

Not investigated further (out of scope for the DATA/cefi task that surfaced this) — needs a `backend_engineer`/
`data_engineering` pass on the DeFi solana/lst_rates handlers to either fix the pipeline_mode assertion (if
`batch_solana_rpc` is the now-correct value) or the write path (if the test is right and the recent KAMINO-SOLANA
commit regressed it), plus the lst_rates test-bucket mock gap.

## Todos

- [ ] [DATA] P2. Root-cause + fix `test_solana_defi_handler.py::TestCollectProtocol::test_writes_data_to_gcs` — determine
      whether `batch_solana_rpc` (actual) or `batch_onchain_subgraph` (test's expectation) is the correct
      `pipeline_mode` for KAMINO-SOLANA dex_pool_state writes post the oracle_prices-capture commits, then fix
      whichever side is wrong. Repo: market-tick-data-service.
- [ ] [DATA] P2. Root-cause + fix `test_lst_rates_handler.py::test_process_writes_canonical_partition_per_protocol_chain`
      — the `lst-rates-bucket` GCS mock/fixture returns 404 on manifest flush; likely a test-bucket registration gap
      from the recent LST-rates venue-expansion work. Repo: market-tick-data-service.

## Progress Log

- **2026-08-17 (slot-24)**: filed while shipping an unrelated cefi marker-migration task; verified pre-existing via
  stash/re-run, declared repo-blocker `qg_red` for market-tick-data-service.
- **2026-08-17 (slot-24, follow-up)**: corrected the `RULES.md § 4b` citation above (no such section exists —
  `unified-trading-pm/agents/RULES.md` §4 is unrelated "Backlog-edit hygiene"; the real repo-blocker protocol lives
  in `unified-trading-pm/agents/worker.md` § "4b) BLOCKED ON THE REPO, not your task"). Also confirmed via that
  protocol: **there is no bypass** — `quickmerge.sh` (lines 171, 419, 2582) always runs the full test suite
  (`SKIP_TESTS`/`SKIP_TYPECHECK` are hardcoded empty; the `--skip-*` flags are rejected), so no slot can ship ANY
  code change to market-tick-data-service — related or not — until this blocker clears. The 3 files for the
  BYBIT/COINBASE-FUTURES/BITGET-FUTURES margin-marker work (tracked in
  `cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md`'s open `[DATA] P2` todo) stay
  uncommitted in slot-24's working tree for this same reason — code+tests independently verified correct
  (113/113 unit tests pass, ruff clean) but cannot commit until RB-3d968cff clears, per the "commit only from a
  green tree" hard rule.
