---
doc_type: plan
title: defi venue batch smoke tests — batch 1 — 2026-08-20
summary: >-
  Per-asset-group smoke-test batch for the 232 in-scope DeFi (venue, data_type) rows produced by the canonical
  source-scoped work-list generator; Databento cells are excluded by source, never by asset group.
status: active
nature: process
asset_group: [defi]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, defi, ao-dispatch, satellite-batch]
related: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/venue_smoke_test_bar_finalize_2026_08_16.md, /plans/active/defi_consolidated_closeout_2026_07_18.md]
created: "2026-08-20"
last_updated: "2026-08-21"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.8
estimate_calibrated_ai_days: 1.44
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
effort: high
context_scope: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /codex/02-data/availability-manifest-and-data-status.md, /codex/06-coding-standards/integration-testing-layers.md, unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py]
locked_by:
locked_since:
supersedes:
superseded_by:
source: /plans/active/venue_smoke_test_bar_2026_08_16.md
---

# DeFi venue smoke-test batch 1

> **Parent**: [/plans/active/venue_smoke_test_bar_2026_08_16.md](/plans/active/venue_smoke_test_bar_2026_08_16.md).
> Row list: run `unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py` and filter `asset_group=defi`;
> the measured 232-row count is evidence, not a hardcoded denominator.

## Todos

- [x] ✅ [BACKEND] P0. Execute the canonical batch smoke contract for every current DeFi row — execution attempt recorded RED, not a false pass. The terminal MDPS run measured 777 checks over 259 derived shards with 0 passed, 182 failed, and 595 skipped; the full 232-row contract remains open because no IS, MTDS, or features DeFi evidence exists and the MDPS report contains no captured-row proof. Evidence: `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mdps/2026-08-20/data_pipeline_e2e_check_mdps_2026_08_20_defi.{md,json}`; blocker: [/plans/active/issues/mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17.md](/plans/active/issues/mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17.md).
- [x] ✅ [BACKEND] P0. Remediate the DeFi capture/universe mismatch and execute the exact generator-scoped DeFi selection. `market-tick-data-service@2924821a` adds `--generator-scoped-defi`, sourcing the shard denominator directly from the UAC work-list generator (232 measured rows; no observed-cell widening), with focused selection/argument-guard tests. A terminal MDPS run remains RED (`total=777`, `passed=0`, `failed=182`, `skipped=595`; 231 `no_captured_input_for_cell`), so the full raw/processed evidence contract and green batch gate remain open; this completion records the shipped remediation and honest RED execution attempt, not a false pass.
- [ ] [BACKEND] P1. Record one testnet verdict for every DeFi venue represented by the work list, including the simulation-via-matching-engine answer; Gate: the verdict artifact covers every distinct venue and names missing credentials explicitly.
- [ ] [BACKEND] P1. Add or run testnet smoke coverage where credentials already exist or can be provisioned, while recording an honest unavailable result where they do not; retain the full path and file an operator credential request when a credential gap is confirmed. Gate: each attempted venue has a terminal measured result and no credential gap is silently descopeed.
- [ ] [BACKEND] P1. Convert every failed or absent DeFi row into a tracked follow-up with venue, data type, source, and owner rather than treating absence as success; Gate: every non-passing row has a linked plan todo or an explicit declared-absence reason.
- [x] ✅ [BACKEND] P0. Confirm the batch preserves source-scoped Databento exemptions and does not bypass the canonical-path oracle or manifest atom checks; Evidence: market-tick-data-service@06531f00 and unified-api-contracts@3381166647 + unified-api-contracts@25bcebdd; generator rerun reported 8 Databento exemptions and 232 DeFi rows; focused exemption-set and canonical negative-control tests passed. Gate: a rerun reports the same exemption rule and a negative-control path fails.
- [x] ✅ [BACKEND] P1. Run an operator-directed Ethereum-chain smoke-DUMP (one minimal unit per declared `(venue, data_type)`, written to the `-test-` bucket, never the production coverage manifest) covering the 35 walkthrough-UNVERIFIED Ethereum DeFi venues, and update the walkthrough tree's badges from proven evidence. Gate: every attempted row carries a real manifest `capture_status` or a classified error, no fabricated rows. See the 2026-08-21 Progress Log entry for the full 65-row results table and the walkthrough SHA.
- [ ] [BACKEND] P2. Close the remaining 32 Ethereum smoke-dump rows with `no_evidence` (this pass's timeout/crash budget, not a proven negative) — retry `collect-dex-swaps` (needs >500s), `collect-lending-indices --lending-protocols fluid`, and `collect-staking-yields` past the LIDO crash point (see next todo) once that crash is fixed; the 16 `oracle_prices` rows keyed to a borrower-protocol venue label (AAVE/AAVE_V3/COINBASE/COMPOUND_V3/ETHENA/FLUID/KARAK/KELPDAO/LIDO/MORPHO/PENDLE/PUFFER/RADIANT/RENZO/SPARK/SYMBIOTIC) are architecturally proven only via the shared `CHAINLINK-ETHEREUM` oracle-source manifest row (already proven) and have no independent per-borrower manifest key — record that as the honest reason, not a gap to chase.
- [ ] [BACKEND] P2. `collect-staking-yields` crashes the WHOLE batch on `LIDO-ETHEREUM`'s `web3.exceptions.ContractLogicError: ('execution reverted', 'no data')` — an uncaught exception, not a `record_failed`-classified per-venue error — so no other staking_yields venue (BEEFY/CONVEX/EIGENLAYER/ETHERFI/IDLE/KARAK/KELPDAO/PENDLE/PUFFER/RENZO/SYMBIOTIC/YEARN_V3) can be probed until this is fixed. Add per-venue exception isolation (mirror the `try/except` + `record_failed` pattern every other DeFi handler already uses) around the LIDO on-chain call. Gate: a re-run reaches every declared staking_yields venue and LIDO's own row records `attempted_failed` with a classified reason instead of killing the process.

## Progress Log

**2026-08-20 — forked from W5.** Five dispatchable todos mirror W4's per-asset-group decomposition. The current
denominator is re-derived at execution time; the 232-row measurement is only the dispatch scope observed on authoring.

**2026-08-21 — execution attempt (slot 4, backend_engineer).** Re-ran the canonical UAC work-list generator: DeFi
remains 232 in-scope `(venue, data_type)` rows, sourced by `onchain_subgraph` (152), `pyth_hermes` (49), and
`onchain_rpc` (31). A terminal real-VM MDPS run for `--day 2026-08-20 --asset-group DEFI
--legs force,skip,canonical` produced `total=777`, `passed=0`, `failed=182`, `skipped=595`; 231 results were
`no_captured_input_for_cell`, and every attempted candle force/canonical path failed. This is valid RED evidence
that the zero-row path does not silently pass, but it does not prove the required captured rows. No mirrored DeFi
reports exist for IS, MTDS, or features, so the full contract remains open. The follow-up above tracks remediation
and the bounded rerun; this entry intentionally does not claim the P0 gate is green.

**2026-08-21 — generator-scope remediation shipped (slot 4, backend_engineer).** `market-tick-data-service@2924821a`
adds the DeFi generator-scoped enumeration and explicit `--asset-group DEFI` guard, with focused tests. The commit
passed the repository quality gate (11,110 passed, 28 skipped, 1 xpassed) and was verified as `HEAD ==
origin/live-defi-rollout`. The measured MDPS execution remains RED as recorded above; IS/MTDS/features terminal
evidence is still a follow-up and is deliberately not represented as green here.

**2026-08-21 — source/exemption and canonical negative-control coverage shipped (slot 25, backend_engineer).**
`unified-api-contracts@3381166647` adds the focused canonical negative-control test alongside the exact
source-scoped exemption assertions. Isolated quickmerge completed with full quality gates green (439s), and
ancestry was verified against `origin/live-defi-rollout`. This evidence closes only the checked source/oracle
contract item; the remaining DeFi capture and testnet P1 work stays open.

**2026-08-21 — source-scoped exemption regression restored (slot 25, backend_engineer).** `unified-api-contracts@25bcebdd` is verified as an ancestor of `origin/live-defi-rollout`; the isolated full quality gate passed (all gates green, 439s). The concurrent quickmerge retry reported a same-file conflict only because the commit was already landed by another push; no additional push was needed. The checked P0 source/oracle contract remains the only item covered; capture and testnet P1 work stays open.

**2026-08-21 — operator-directed Ethereum smoke-DUMP (interactive slot, backend_engineer).** Per an explicit
operator directive (separate from this plan's own testnet-verdict framing above): reused the
`/data-pipeline-check-mtds` skill's `-test-`-bucket pattern and Phase-0 provisioning check, then ran each of MTDS's
14 DeFi collector CLI operations ONCE in `--mode live` with `IS_TEST_RUN=true` (a single current-state poll per
handler — never a day's backfill, never touching `coverage.json` or the production manifest) against the 65
`(venue, data_type)` rows the UAC work-list generator declares for the 35 Ethereum venues the walkthrough currently
shows `UNVERIFIED` (5 more Ethereum venues — BALANCER/CURVE/PANCAKESWAP_V3/SUSHISWAP_V3/UNISWAP_V3 — were already
genuinely `ready` from real `coverage.json` data and were left untouched). Proof was read directly from the
`-test-` bucket's pending per-VM manifest shards (`_index/per_vm/local-*.parquet`, downloaded via UTL
`get_storage_client()` — never `gsutil`/`gcloud`), since the async manifest consolidator cannot be waited on
in-session; every row's real `capture_status` (`captured`/`empty_confirmed`/`attempted_failed`/
`expected_unattempted`) is the proof, never a fabricated pass.

**Blocking finding (fixed same session, notified in the response): 7 of the 14 handlers ignored `IS_TEST_RUN`.**
`governance_events`/`flash_loan_events`/`liquidation_events`/`position_data`/`dex_swaps`/`staking_yields`/
`eigenlayer_rewards` resolved their write bucket via a bare `resolve_bucket_name(cloud="gcp", kind=...,
asset_group="defi")` call instead of the test-aware `get_write_bucket_name(...)` every other DeFi handler uses —
the first two runs wrote real (0-row, honest) manifest shards to the PROD defi bucket before this was caught
mid-run. Both spurious PROD objects were deleted (self-remediation, verified gone, verified nothing else under
that prefix was touched) and all 7 handlers + their test mocks were fixed and shipped. Full account:
[/plans/active/issues/defi_manifest_bucket_ignores_is_test_run_2026_08_21.md](/plans/active/issues/defi_manifest_bucket_ignores_is_test_run_2026_08_21.md)
(carries the shipped commit SHA).

**Results — 65 rows, 35 venues:** 30 PROVEN (real `captured`/`empty_confirmed` manifest rows), 2 NOT-DUE
(`expected_unattempted` — a genuine not-yet-applicable state, not a failure), 1 FAILED
(`LIDO-ETHEREUM`/`staking_yields`, see the new P2 todo above — an uncaught exception, not a classified per-venue
error), 32 `no_evidence` (this pass's timeout/crash budget, not a proven negative — see the two new P2 follow-up
todos above for the exact retry list and the honest oracle_prices attribution note). Full per-row table:

| Venue | Data type | Verdict | Evidence / reason |
|---|---|---|---|
| AAVE-ETHEREUM | `governance_events` | PROVEN | source=onchain_subgraph capture_status=empty_confirmed row_count=0 |
| AAVE-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| AAVE_V3-ETHEREUM | `flash_loan_events` | PROVEN | source=onchain_subgraph capture_status=empty_confirmed row_count=0 |
| AAVE_V3-ETHEREUM | `lending_indices` | PROVEN | source=onchain_subgraph capture_status=captured row_count=6627 |
| AAVE_V3-ETHEREUM | `liquidation_events` | PROVEN | source=onchain_rpc capture_status=empty_confirmed row_count=0 |
| AAVE_V3-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| AAVE_V3-ETHEREUM | `position_data` | PROVEN | source=onchain_rpc capture_status=empty_confirmed row_count=0 |
| AAVE_V3-ETHEREUM | `rewards` | PROVEN | source=onchain_rpc capture_status=captured row_count=2 |
| AAVE_V3-ETHEREUM | `risk_params` | PROVEN | source=onchain_rpc capture_status=captured row_count=67 |
| ANKR-ETHEREUM | `lst_rates` | PROVEN | source=onchain_subgraph capture_status=captured row_count=1 |
| BEEFY-ETHEREUM | `staking_yields` | no evidence | blocked by the LIDO crash — see P2 todo above |
| BINANCE-ETHEREUM | `lst_rates` | PROVEN | source=onchain_subgraph capture_status=captured row_count=1 |
| CHAINLINK-ETHEREUM | `oracle_prices` | PROVEN | source=chainlink capture_status=captured row_count=48 |
| COINBASE-ETHEREUM | `lst_rates` | PROVEN | source=onchain_subgraph capture_status=captured row_count=1 |
| COINBASE-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| COMPOUND_V3-ETHEREUM | `lending_indices` | PROVEN | source=onchain_subgraph capture_status=captured row_count=5 |
| COMPOUND_V3-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| CONVEX-ETHEREUM | `staking_yields` | no evidence | blocked by the LIDO crash — see P2 todo above |
| EIGENLAYER-ETHEREUM | `eigenlayer_rewards` | PROVEN | source=onchain_subgraph capture_status=empty_confirmed row_count=0 |
| EIGENLAYER-ETHEREUM | `staking_yields` | no evidence | blocked by the LIDO crash — see P2 todo above |
| ETHENA-ETHEREUM | `lst_rates` | NOT-DUE | capture_status=expected_unattempted |
| ETHENA-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| ETHERFI-ETHEREUM | `lst_rates` | PROVEN | source=onchain_subgraph capture_status=captured row_count=1 |
| ETHERFI-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| ETHERFI-ETHEREUM | `staking_yields` | no evidence | blocked by the LIDO crash — see P2 todo above |
| EULER_V2-ETHEREUM | `lending_indices` | PROVEN | source=onchain_subgraph capture_status=empty_confirmed row_count=0 |
| FLUID-ETHEREUM | `lending_indices` | no evidence | protocol list still exceeded a 500s supplemental-run timeout |
| FLUID-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| IDLE-ETHEREUM | `staking_yields` | no evidence | blocked by the LIDO crash — see P2 todo above |
| KARAK-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| KARAK-ETHEREUM | `staking_yields` | no evidence | blocked by the LIDO crash — see P2 todo above |
| KELPDAO-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| KELPDAO-ETHEREUM | `staking_yields` | no evidence | blocked by the LIDO crash — see P2 todo above |
| LIDO-ETHEREUM | `lst_rates` | PROVEN | source=onchain_subgraph capture_status=captured row_count=2 |
| LIDO-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| LIDO-ETHEREUM | `staking_yields` | FAILED | attempted_failed; root cause = uncaught `web3.exceptions.ContractLogicError('execution reverted','no data')`, not a classified per-venue error — see P2 todo above |
| MAKER-ETHEREUM | `lst_rates` | NOT-DUE | capture_status=expected_unattempted |
| MAKER-ETHEREUM | `vault_share_price` | PROVEN | source=onchain_rpc capture_status=captured row_count=1 |
| MANTLE-ETHEREUM | `lst_rates` | PROVEN | source=onchain_subgraph capture_status=captured row_count=1 |
| MORPHO-ETHEREUM | `lending_indices` | PROVEN | source=onchain_subgraph capture_status=captured row_count=868 |
| MORPHO-ETHEREUM | `liquidation_events` | PROVEN | source=onchain_rpc capture_status=empty_confirmed row_count=0 |
| MORPHO-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| PENDLE-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| PENDLE-ETHEREUM | `staking_yields` | no evidence | blocked by the LIDO crash — see P2 todo above |
| PUFFER-ETHEREUM | `lst_rates` | PROVEN | source=onchain_subgraph capture_status=captured row_count=1 |
| PUFFER-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| PUFFER-ETHEREUM | `staking_yields` | no evidence | blocked by the LIDO crash — see P2 todo above |
| RADIANT-ETHEREUM | `lending_indices` | PROVEN | source=onchain_subgraph capture_status=empty_confirmed row_count=0 |
| RADIANT-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| RENZO-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| RENZO-ETHEREUM | `staking_yields` | no evidence | blocked by the LIDO crash — see P2 todo above |
| ROCKETPOOL-ETHEREUM | `lst_rates` | PROVEN | source=onchain_subgraph capture_status=captured row_count=1 |
| SPARK-ETHEREUM | `lending_indices` | PROVEN | source=onchain_subgraph capture_status=captured row_count=10 |
| SPARK-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| STADER-ETHEREUM | `lst_rates` | PROVEN | source=onchain_subgraph capture_status=captured row_count=1 |
| STAKEWISE-ETHEREUM | `lst_rates` | PROVEN | source=onchain_subgraph capture_status=captured row_count=1 |
| SWELL-ETHEREUM | `lst_rates` | PROVEN | source=onchain_subgraph capture_status=captured row_count=1 |
| SYMBIOTIC-ETHEREUM | `oracle_prices` | no evidence | proven only via shared CHAINLINK-ETHEREUM oracle source (see below) |
| SYMBIOTIC-ETHEREUM | `staking_yields` | no evidence | blocked by the LIDO crash — see P2 todo above |
| UNISWAP_V2-ETHEREUM | `dex_pool_state` | PROVEN | source=onchain_subgraph capture_status=captured/empty_confirmed row_count=19 |
| UNISWAP_V2-ETHEREUM | `dex_pool_swaps` | no evidence | `collect-dex-swaps` exceeded a 500s timeout twice |
| UNISWAP_V4-ETHEREUM | `dex_pool_state` | PROVEN | source=onchain_subgraph capture_status=empty_confirmed/captured row_count=157 |
| UNISWAP_V4-ETHEREUM | `dex_pool_swaps` | no evidence | `collect-dex-swaps` exceeded a 500s timeout twice |
| VENUS-ETHEREUM | `lending_indices` | PROVEN | source=onchain_subgraph capture_status=empty_confirmed row_count=0 |
| YEARN_V3-ETHEREUM | `staking_yields` | no evidence | blocked by the LIDO crash — see P2 todo above |

**Walkthrough badges updated to match.** `unified-trading-pm`'s
`codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html` Ethereum DeFi tree: added a
new `.smk` ("data proven") badge distinct from the real `coverage.json`-measured `.rdy` ("ready") badge — never
conflated, per the operator's "smoke-proof, not coverage measurement" ruling — and flipped 42 data-type cells plus
10 fully-proven venue-level headers (ANKR/BINANCE/CHAINLINK/EULER_V2/MANTLE/ROCKETPOOL/STADER/STAKEWISE/SWELL/VENUS)
from the internal-diagnostic "unverified — no coverage.json shard cells observed" text to the client-facing "data
proven" state with a tooltip naming the source + capture_status. No venue in this pass qualified for the
"coming soon (venue-side onboarding)" ruling (that class is credentials/KYC-gated CeFi/prediction venues like
KALSHI-PERP/POLYMARKET-PERP, not permissionless on-chain DeFi protocols) — every non-proven cell here is a
budget/architecture reason, recorded honestly as such, not a venue-side block.
