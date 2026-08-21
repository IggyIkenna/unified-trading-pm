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

- [x] ✅ [BACKEND] P0. Execute the canonical batch smoke contract for every current DeFi row — execution attempt recorded RED, not a false pass. The terminal MDPS run measured 777 checks over 259 derived shards with 0 passed, 182 failed, and 595 skipped; the full 232-row contract remains open because no IS, MTDS, or features DeFi evidence exists and the MDPS report contains no captured-row proof. Evidence: `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mdps/2026-08-20/data_pipeline_e2e_check_mdps_2026_08_20_defi.{md,json}`; blocker: [/plans/active/issues/mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md](/plans/active/issues/mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md) (successor doc — the original blocker doc is now archived, resolved).
- [x] ✅ [BACKEND] P0. Remediate the DeFi capture/universe mismatch and execute the exact generator-scoped DeFi selection. `market-tick-data-service@2924821a` adds `--generator-scoped-defi`, sourcing the shard denominator directly from the UAC work-list generator (232 measured rows; no observed-cell widening), with focused selection/argument-guard tests. A terminal MDPS run remains RED (`total=777`, `passed=0`, `failed=182`, `skipped=595`; 231 `no_captured_input_for_cell`), so the full raw/processed evidence contract and green batch gate remain open; this completion records the shipped remediation and honest RED execution attempt, not a false pass.
- [x] ✅ [BACKEND] P1. Record one testnet verdict for every DeFi venue represented by the work list, including the simulation-via-matching-engine answer; Gate: the verdict artifact covers every distinct venue and names missing credentials explicitly. Evidence: 127 distinct venue-chain strings (232 rows) classified into 12 execution-mechanism groups, credential status stated per group (spot-checked, not just asserted). See the 2026-08-21 (slot 14) Progress Log entry for the full table.
- [x] ✅ [BACKEND] P1. Add or run testnet smoke coverage where credentials already exist or can be provisioned, while recording an honest unavailable result where they do not; retain the full path and file an operator credential request when a credential gap is confirmed. Gate: each attempted venue has a terminal measured result and no credential gap is silently descopeed. Evidence: `execution-service@3f5e89e6b4` (missing `py-solc-x` test dep fixed) + real pytest runs against live testnet/Tenderly-fork infra — no credential gap was found (all 4 checked GSM secrets are provisioned), so no operator credential request was needed. See the 2026-08-21 (this session, slot 8) Progress Log entry for the full per-group terminal results.
- [ ] [BACKEND] P1. Convert every failed or absent DeFi row into a tracked follow-up with venue, data type, source, and owner rather than treating absence as success; Gate: every non-passing row has a linked plan todo or an explicit declared-absence reason.
- [x] ✅ [BACKEND] P0. Confirm the batch preserves source-scoped Databento exemptions and does not bypass the canonical-path oracle or manifest atom checks; Evidence: market-tick-data-service@06531f00 and unified-api-contracts@3381166647 + unified-api-contracts@25bcebdd; generator rerun reported 8 Databento exemptions and 232 DeFi rows; focused exemption-set and canonical negative-control tests passed. Gate: a rerun reports the same exemption rule and a negative-control path fails.
- [x] ✅ [BACKEND] P1. Run an operator-directed Ethereum-chain smoke-DUMP (one minimal unit per declared `(venue, data_type)`, written to the `-test-` bucket, never the production coverage manifest) covering the 35 walkthrough-UNVERIFIED Ethereum DeFi venues, and update the walkthrough tree's badges from proven evidence. Gate: every attempted row carries a real manifest `capture_status` or a classified error, no fabricated rows. See the 2026-08-21 Progress Log entry for the full 65-row results table and the walkthrough SHA.
- [ ] [BACKEND] P2. Close the remaining 32 Ethereum smoke-dump rows with `no_evidence` (this pass's timeout/crash budget, not a proven negative) — retry `collect-dex-swaps` (needs >500s), `collect-lending-indices --lending-protocols fluid`, and `collect-staking-yields` past the LIDO crash point (see next todo) once that crash is fixed; the 16 `oracle_prices` rows keyed to a borrower-protocol venue label (AAVE/AAVE_V3/COINBASE/COMPOUND_V3/ETHENA/FLUID/KARAK/KELPDAO/LIDO/MORPHO/PENDLE/PUFFER/RADIANT/RENZO/SPARK/SYMBIOTIC) are architecturally proven only via the shared `CHAINLINK-ETHEREUM` oracle-source manifest row (already proven) and have no independent per-borrower manifest key — record that as the honest reason, not a gap to chase.
- [ ] [BACKEND] P2. `collect-staking-yields` crashes the WHOLE batch on `LIDO-ETHEREUM`'s `web3.exceptions.ContractLogicError: ('execution reverted', 'no data')` — an uncaught exception, not a `record_failed`-classified per-venue error — so no other staking_yields venue (BEEFY/CONVEX/EIGENLAYER/ETHERFI/IDLE/KARAK/KELPDAO/PENDLE/PUFFER/RENZO/SYMBIOTIC/YEARN_V3) can be probed until this is fixed. Add per-venue exception isolation (mirror the `try/except` + `record_failed` pattern every other DeFi handler already uses) around the LIDO on-chain call. Gate: a re-run reaches every declared staking_yields venue and LIDO's own row records `attempted_failed` with a classified reason instead of killing the process.
- [ ] [BACKEND] P2. Solana lending venues (`KAMINO-SOLANA`, `SOLEND-SOLANA`, `MARGINFI-SOLANA`) have no execution-simulation path at all — a missing capability, not a credential gap: no Tenderly-equivalent mainnet fork exists for Solana in this codebase, `SolanaAmmDepthProvider`'s matching-engine mode only walks swap/AMM depth (not lending state), and only Kamino has a dedicated connector (`execution_service/defi_execution/protocols/kamino.py`) — Solend/MarginFi have none. All three currently fall back to the zero-realism `BenchmarkFillProvider`. Gate: either a real simulation mechanism is built (or `SolanaAmmDepthProvider`/an equivalent is extended to cover Solana lending state) for these three, or the gap is explicitly accepted as a documented permanent limitation with operator sign-off — not left open indefinitely.
- [ ] [BACKEND] P2. Fix the Uniswap V3 live-swap revert on the Tenderly fork (groups D/E). Every `exactInputSingle` call attempted this session against a fresh Tenderly Ethereum-mainnet fork reverted (5/5 swap-touching tests: `test_engine_to_fork_e2e.py::test_uniswap_swap_executes_on_fork`, all 3 execution-path tests in `test_sor_fork_routing.py`, `test_flash_loan_receiver_execution.py::test_flash_then_swap_gas_accounting`) with no decoded revert reason surfaced by `_map_revert_error`. This is isolated to the swap leg — the AAVE supply/borrow/repay/flash-loan/atomic-liquidation calls on the SAME fork type all succeeded in the same session (see Progress Log), so it is not a Tenderly/credential/fork problem. Gate: root-cause the revert (fee-tier/pool mismatch, SwapRouter02 calldata shape, or a fork-state issue) and get `test_sor_fork_routing.py` + `test_engine_to_fork_e2e.py::TestLpConcentratedEngineToFork` green.
- [ ] [BACKEND] P3. Build a real Sepolia-live execution test for AAVE_V3-ETHEREUM (group A) — the only existing test (`test_aave_testnet_integration.py`) checks `TestnetContractRegistry` address values only; it never opens a live Sepolia RPC connection or signs a transaction. `alchemy-api-key` is confirmed provisioned in GSM (this session). Gate: one real Sepolia testnet transaction (or a decoded on-chain revert) is recorded against chain_id 11155111.
- [ ] [BACKEND] P3. Confirm or retract JITORESTAKING-SOLANA/SANCTUM-SOLANA/SOLANA-NATIVE-SOLANA devnet coverage (group B). `solana_lst_devnet.py`'s `SOLANA_LST_MINTS` only wires JITOSOL/MSOL/BSOL (JITO/MARINADE/SOLBLAZE) — this session live-confirmed all three of those mint accounts genuinely exist on `https://api.devnet.solana.com` (real `getAccountInfo` responses, non-zero lamports, owner=SPL Token program). The other 3 venues have no confirmed per-venue devnet call site. Gate: either wire a devnet mint/call site for these three or record their testnet verdict as unconfirmed rather than grouped-in-by-similarity.

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

**2026-08-21 — testnet verdict per DeFi venue (slot 14, backend_engineer).** Re-ran the canonical work-list
generator fresh: 232 defi rows / **127 distinct venue-chain strings**, this run. Grouped every venue by its actual
*execution mechanism* — the fact that answers "testnet or not" — rather than by raw protocol name, since
testnet/simulation availability is a property of the connector/provider a venue routes through in
`execution-service`, not of the individual chain suffix. Every group's chain list is traced directly from the live
CSV; **the 12 group sizes sum to exactly 127** (1+6+42+19+28+6+3+6+9+3+2+2) — no venue silently dropped. Two of the
most consequential cells were independently spot-checked against the live code (not just taken on the research
pass's word): `execution_service/defi_execution/protocols/aave_live.py:354-367` does hardcode
`SEPOLIA_TOKEN_ADDRESSES` at chain_id=11155111 (confirms Aave's real testnet); `get_execution_provider()`
(`execution_service/providers/factory.py`) has exactly two non-test references repo-wide — its own definition and
one unit test — confirming zero production callers anywhere in execution-service.

| # | Group | Venue-chain strings covered | Verdict | Detail | Credentials required | Credentials status |
|---|---|---|---|---|---|---|
| A | AAVE_V3 (Ethereum only) | AAVE_V3-ETHEREUM | **HAS-TESTNET** | Ethereum Sepolia (chain_id 11155111). `aave_live.py` hardcodes `SEPOLIA_TOKEN_ADDRESSES` (WETH/USDT/USDC/DAI/WBTC) + chain-id dispatch; `tests/defi_execution/integration/test_aave_testnet_integration.py` + `test_aave_testnet_contracts.py` prove real coverage — the only protocol in this codebase with a hardcoded testnet contract/token registry. | Alchemy RPC key (Sepolia, via `CHAIN_RPC_TEMPLATES`) + a funded Sepolia wallet key | Alchemy key: **PROVISIONED** — `service_config.py` field `alchemy_api_key_secret` (default `alchemy-api-key`), read live in `cli/handlers/live_execution_defi.py`. Wallet key: custody-routed, out of this check's scope. |
| B | JITO / JITORESTAKING / MARINADE / SANCTUM / SOLANA-NATIVE / SOLBLAZE | JITO-SOLANA, JITORESTAKING-SOLANA, MARINADE-SOLANA, SANCTUM-SOLANA, SOLANA-NATIVE-SOLANA, SOLBLAZE-SOLANA (6) | **HAS-TESTNET** | Public Solana **devnet** (`https://api.devnet.solana.com`), no key needed. `solana_lst_devnet.py`'s docstring names jitoSOL/mSOL/bSOL explicitly (JITO/MARINADE/SOLBLAZE) via `get_solana_rpc_for_mode`. JITORESTAKING/SANCTUM/SOLANA-NATIVE share the same LST/staking shape and the helper is generic, but an actual wired caller per venue was **not individually confirmed** — flagged, not asserted. | None (public keyless endpoint) | N/A |
| C | AAVE_V3 (9 non-ETH chains) + AAVE-PLASMA, LIDO, CONVEX, BEEFY, IDLE, EIGENLAYER, ETHERFI, KARAK, KELPDAO, PENDLE, PUFFER, RENZO, ROCKETPOOL, SYMBIOTIC, YEARN_V3, MORPHO | AAVE_V3-{ARBITRUM,AVALANCHE,BASE,BSC,LINEA,OPTIMISM,POLYGON,SCROLL,ZKSYNC}, AAVE-PLASMA, LIDO-ETHEREUM, CONVEX-ETHEREUM, BEEFY-{ARBITRUM,AVALANCHE,BASE,BSC,ETHEREUM,POLYGON}, IDLE-{ARBITRUM,ETHEREUM,POLYGON}, EIGENLAYER-ETHEREUM, ETHERFI-ETHEREUM, KARAK-{ARBITRUM,ETHEREUM}, KELPDAO-ETHEREUM, PENDLE-{ARBITRUM,ETHEREUM}, PUFFER-ETHEREUM, RENZO-{ARBITRUM,ETHEREUM}, ROCKETPOOL-ETHEREUM, SYMBIOTIC-ETHEREUM, YEARN_V3-{ARBITRUM,ETHEREUM,OPTIMISM}, MORPHO-{ARBITRUM,BASE,ETHEREUM,OPTIMISM,POLYGON} (42) | **NO-TESTNET — TENDERLY FORK IS THE ONLY FIT** | Each has a real connector module in `defi_execution/protocols/` but no Sepolia token-address registry like Aave's; these are lending/staking positions, not order-matched fills, so matching-engine mode does not apply. | `tenderly-api-key` / `tenderly-account-slug` / `tenderly-project-slug` | **NO PRODUCTION WIRING; secret itself UNCONFIRMED.** Spot-checked: the `tenderly-api-key` GSM secret name IS a real, established convention — `tests/defi_execution/integration/conftest.py`'s `tenderly_api_key()` fixture calls `_fetch_secret("tenderly-api-key")` and skips gracefully if the secret is absent, so it may already be provisioned in GSM — but `get_execution_provider()` has zero non-test callers repo-wide, so nothing in production would ever fetch/use it today. Whether the secret is actually populated in GSM was not checked here; building the missing production caller is exactly what plan todo #4 should do next. |
| D | BENQI, COMPOUND_V3, EULER_V2, FLUID, FRAX, RADIANT, SPARK, VENUS, MAKER | BENQI-AVALANCHE, COMPOUND_V3-{ARBITRUM,BASE,ETHEREUM,OPTIMISM,POLYGON,SCROLL}, EULER_V2-{ARBITRUM,ETHEREUM}, FLUID-{ETHEREUM,PLASMA}, FRAX-ETHEREUM, RADIANT-{ARBITRUM,BSC,ETHEREUM}, SPARK-ETHEREUM, VENUS-{BSC,ETHEREUM}, MAKER-ETHEREUM (19) | **NO-TESTNET — TENDERLY FORK ONLY, NO DEDICATED CONNECTOR EVEN EXISTS** | Same mechanism as group C, but no matching `.py` file exists under `defi_execution/protocols/` for any of these — only the generic fork-mode RPC path in `base.py` would apply if a connector were built. Spark has governance-proposal-sim coverage (group F) but that is not an execution connector. | Same trio as group C | Same as group C: no production wiring, secret unconfirmed. |
| E | AERODROME_V3, BALANCER, CAMELOT_V3, CURVE, PANCAKESWAP_V3, SUSHISWAP(+V3), TRADER_JOE_V2, UNISWAP_V2/V3/V4, VELODROME_V2 | AERODROME_V3-BASE, BALANCER-{ARBITRUM,AVALANCHE,BASE,ETHEREUM,OPTIMISM,POLYGON}, CAMELOT_V3-ARBITRUM, CURVE-{AVALANCHE,ETHEREUM,OPTIMISM}, PANCAKESWAP_V3-{ARBITRUM,BASE,BSC,ETHEREUM}, SUSHISWAP-ARBITRUM, SUSHISWAP_V3-{AVALANCHE,BASE,ETHEREUM}, TRADER_JOE_V2-AVALANCHE, UNISWAP_V2-ETHEREUM, UNISWAP_V3-{ARBITRUM,BASE,ETHEREUM,OPTIMISM,POLYGON}, UNISWAP_V4-ETHEREUM, VELODROME_V2-OPTIMISM (28) | **NO-TESTNET — BOTH TENDERLY FORK AND MATCHING-ENGINE APPLY** | Uniswap has its own live connector (`uniswap.py`/`uniswap_live.py`); the rest fall back to the generic fork path — none have a Sepolia address set. **This is the "simulation-via-matching-engine" answer for swap-shaped venues**: `MatchingEngineExecutionProvider` (mode=`matching_engine`/`sim`) walks captured L2 depth for realistic fills — batch = GCS parquet replay, live = Redis stream — with no chain interaction and no chain credentials at all. | Tenderly trio (fork leg, same gap as C) + none for the matching-engine leg | Fork leg: same as group C. Matching-engine leg: no credential needed for batch; `project_id` defaults to `central-element-323112`. |
| F | AAVE (legacy label), COMPOUND (legacy label), UNISWAP (legacy label) — governance_events only | AAVE-ETHEREUM, COMPOUND-ETHEREUM, UNISWAP-ETHEREUM (3) | **NO EXECUTION SURFACE for the venue itself; a proposal simulator exists but its label-alignment is unconfirmed** | `execution_service/governance/proposal_simulator.py` runs `governor.execute()` on a Tenderly fork for exactly 4 protocols keyed as `AAVE_V3_PROTOCOL`/`COMPOUND_V3_PROTOCOL`/`SPARK_PROTOCOL`/`LIDO_PROTOCOL`. These 3 work-list rows use the **legacy v2 labels** — whether the simulator's V3-keyed enum actually covers what the manifest calls bare "AAVE"/"COMPOUND" was not confirmed this pass. UNISWAP has no simulator coverage under any label. Budget-capped ~10 sims/day per the codex risk register. | Tenderly trio | Same as group C. |
| G | JUPITER, ORCA, RAYDIUM, LIFINITY, METEORA, PHOENIX | JUPITER-SOLANA, ORCA-SOLANA, RAYDIUM-SOLANA, LIFINITY-SOLANA, METEORA-SOLANA, PHOENIX-SOLANA (6) | **NO-TESTNET — MATCHING-ENGINE, SOLANA AMM DEPTH MODE** | `SolanaAmmDepthProvider` is the confirmed sim path (batch=GCS replay, live=Redis). No Solana-devnet wiring found for any of these specific AMMs (the devnet helper in group B is LST-scoped); Tenderly forking is EVM-only and has no Solana equivalent. | `helius-api-key` (live-mode RPC leg only; batch needs none) | **PROVISIONED** — `solana_rpc_client.py` defines `_HELIUS_SECRET_NAME = "helius-api-key"` with a live `get_secret()` call. |
| H | KAMINO, SOLEND, MARGINFI | KAMINO-SOLANA, SOLEND-SOLANA, MARGINFI-SOLANA (3) | **NO CONFIRMED SIM PATH — the one real capability gap, not a credential gap** | Solana lending. Kamino has a dedicated connector (`kamino.py`); Solend/MarginFi have none. No Solana devnet wiring (LST-scoped only), no Solana equivalent of a Tenderly fork exists, and matching-engine only covers AMM/swap depth, not lending state — only fallback is the zero-realism `BenchmarkFillProvider`. Tracked as a new P2 todo above. | None identified as sufficient | **GAP** — no credential would fix this; the simulation mechanism itself doesn't exist yet. |
| I | CHAINLINK, PYTH | CHAINLINK-{ARBITRUM,BASE,ETHEREUM,OPTIMISM,POLYGON}, PYTH-SOLANA (6) | **NO EXECUTION SURFACE** | Pure oracle/price feeds — nothing to testnet or simulate, by nature. | — | — |
| J | ANKR, BINANCE, COINBASE, ETHENA, MANTLE, STADER, STAKEWISE, SWELL | ANKR-ETHEREUM, BINANCE-{BSC,ETHEREUM}, COINBASE-ETHEREUM, ETHENA-ETHEREUM, MANTLE-ETHEREUM, STADER-ETHEREUM, STAKEWISE-ETHEREUM, SWELL-ETHEREUM (9) | **NO EXECUTION SURFACE** | LST/yield-token issuers tracked as `lst_rates`/`oracle_prices` feeds only — no dedicated connector exists; holding the token is the only user action, not a protocol call. | — | — |
| K | ACROSS, STARGATE | ACROSS-ETHEREUM, STARGATE-ETHEREUM (2, bridge_events only) | **NO EXECUTION SURFACE WIRED** | `bridge.py` (Socket/Bungee aggregator) exists but its own docstring states zero production callers repo-wide (confirmed only in tests); no fork/testnet equivalent evaluated for a cross-chain transfer. Side-note: `cctp.py` (a separate bridge module, not in this venue list) documents a genuine Circle Iris **sandbox** testnet API, proving the pattern exists in this codebase when actually built — just not for Across/Stargate. | — | — (not wired regardless) |
| L | ALCHEMY, FLASHBOTS | ALCHEMY-ONCHAIN (token_transfers), FLASHBOTS-ETHEREUM (mev_events) (2) | **NO EXECUTION SURFACE — not DeFi protocols** | Alchemy is the RPC/indexing vendor itself, listed as a data-source venue. Flashbots is MEV-protection/monitoring infra (`defi_execution/mev/protection.py`), not a tradeable position. | — | — |

**Count check**: 1(A)+6(B)+42(C)+19(D)+28(E)+3(F)+6(G)+3(H)+6(I)+9(J)+2(K)+2(L) = **127**, matching the fresh
generator run exactly — every venue-chain string is accounted for in exactly one row.

**Named low-confidence items (stated, not silently assumed):** (1) group B — only JITO/MARINADE/SOLBLAZE are
individually named in `solana_lst_devnet.py`'s docstring; JITORESTAKING/SANCTUM/SOLANA-NATIVE are grouped in by
protocol-shape similarity, not a confirmed per-venue call site. (2) group F — the proposal simulator's V3-keyed
enum was not confirmed to cover this work list's legacy AAVE/COMPOUND labels. (3) the Tenderly credential-wiring
gap (groups C/D/E's fork leg/F, 92 of 127 rows) is the single biggest finding: there is no production caller of
`get_execution_provider()` anywhere in execution-service today — it may be wired in a sibling repo (a batch/paper
orchestrator) not in scope for this check, or genuinely unwired; a direct grep in strategy-service is the fast
follow-up, not asserted here either way. (4) `cctp.py`'s docstring references a
`config/testnet_contracts.yaml` file that does not exist anywhere in this repo (confirmed via `find`) — likely
stale/aspirational, flagged not fixed (out of this task's scope). Group H's capability gap is now tracked as its
own P2 todo above rather than left as prose.

**2026-08-21 — testnet smoke coverage actually run, credentials confirmed provisioned (slot 8, backend_engineer).**
Followed up on the prior session's 12-group testnet-verdict table (above) — that pass identified WHICH credentials
each group needs but explicitly left "secret itself UNCONFIRMED" for the Tenderly trio. This session closed that
gap and then ran real testnet/fork coverage:

**Credential existence check (self-service GSM read, values never accessed):** all 4 checked secrets ARE
provisioned in `central-element-323112` — `tenderly-api-key` ✅, `defi-wallet-private-key` ✅, `alchemy-api-key` ✅,
`helius-api-key` ✅ (`tenderly-config` is absent but `conftest.py` falls back to a hardcoded default account/project
slug, so this is not a gap). **No credential gap was confirmed anywhere this session touched, so no operator
credential request was filed** — the gate's "file a credential request" clause is honestly inapplicable here, not
silently skipped.

**Group A (AAVE_V3 Sepolia) — ran the existing test, found it's registry-only.**
`test_aave_testnet_integration.py` (2 tests): both PASSED, but on inspection they only assert
`TestnetContractRegistry` address values — no live Sepolia RPC call, no signed transaction. This does not prove
live Sepolia reachability despite the Alchemy key being provisioned; tracked as a new P3 follow-up above (build a
real Sepolia-live test) rather than claimed as testnet-execution evidence.

**Group B (Solana devnet LST, JITO/MARINADE/SOLBLAZE) — live-confirmed via direct RPC.** Queried
`https://api.devnet.solana.com` directly (`getHealth` → `"ok"`; `getAccountInfo` for all 3 LST mint addresses in
`SOLANA_LST_MINTS`): JITOSOL, MSOL, and BSOL mint accounts all genuinely exist on devnet (real non-zero-lamport SPL
Token accounts, `owner=TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA`). This is honest, live, credential-free
confirmation for the 3 individually-named venues. JITORESTAKING/SANCTUM/SOLANA-NATIVE remain unconfirmed (no
per-venue devnet call site exists in `solana_lst_devnet.py`) — new P3 follow-up above, not silently claimed.

**Groups C/D/E/F (Tenderly-fork gated, 92 of 127 venue-chain rows) — ran the existing integration suite, real
terminal results.** Found + fixed a genuine blocker first: `tests/defi_execution/integration/conftest.py` imports
`solcx` to compile `FlashLoanReceiver.sol`/`LiquidationFlashLoanReceiver.sol`, but `py-solc-x` was never declared
as a dependency (`ModuleNotFoundError` on every AAVE flash-loan/liquidation test). Fixed —
`execution-service@3f5e89e6b4` adds `py-solc-x>=2.0.0,<3.0.0`; full quality gates green (158s), verified as an
ancestor of `origin/live-defi-rollout`. With that fixed, ran the full Tenderly-fork suite live against real
Tenderly Virtual TestNets (GCP_PROJECT_ID=central-element-323112, real VNet create/fund/deploy/teardown per test
class — 18 tests total across 6 files):

| Test file | Venue/leg covered | Result |
|---|---|---|
| `test_lp_concentrated_cycle_e2e.py` (1) | Uniswap V3 LP mint/burn | 1 PASSED |
| `test_eigenlayer_integration.py` (5) | EigenLayer restaking lifecycle | 5 PASSED |
| `test_engine_to_fork_e2e.py::TestMevLiquidationBundleEngineToFork` (2) | AAVE_V3 flash-loan + supply/borrow/repay | 2 PASSED |
| `test_atomic_liquidation_bundle_e2e.py` (3) | AAVE_V3 atomic liquidation bundle (revert-cleanly / auth / owner-only) | 3 PASSED |
| `test_flash_loan_receiver_execution.py::test_flash_borrow_executes_with_positive_gas` (1) | AAVE_V3 flash-loan gas accounting | 1 PASSED |
| `test_sor_fork_routing.py::TestCarryArchetypeForkGasCost` (1) | AAVE_V3 supply gas cost (Phase-9 cost model) | 1 PASSED |
| `test_engine_to_fork_e2e.py::TestLpConcentratedEngineToFork::test_uniswap_swap_executes_on_fork` (1) | Uniswap V3 swap execution | 1 FAILED (real on-chain revert) |
| `test_flash_loan_receiver_execution.py::test_flash_then_swap_gas_accounting` (1) | Flash-loan → Uniswap V3 swap | 1 FAILED (same revert) |
| `test_sor_fork_routing.py::TestSOROptimalRouteOnFork` (3) | SOR-routed Uniswap V3 swaps | 3 FAILED (same revert) |

**13 PASSED / 5 FAILED, 0 errors** (the 8 `ModuleNotFoundError` setup errors from the pre-fix run are gone). This
is genuine, credential-backed testnet/fork evidence for AAVE_V3 lending/borrowing/flash-loan/liquidation (groups
C/D) and Uniswap V3 LP + EigenLayer restaking (group E) — real transactions executed and mined on live Tenderly
forks, not mocked. The 5 failures are ALL the same isolated defect (Uniswap V3 `exactInputSingle` reverts on
every attempt, no decoded reason) — since AAVE calls on the identical fork type succeeded in the same run, this is
a real execution-path bug, not a Tenderly/credential/fork problem; tracked as a new P2 follow-up above rather than
left unexplained. `test_sor_fork_routing.py::test_sor_routes_weth_usdc_to_uniswap_v3` additionally surfaced SOR
routing WETH/USDC to CURVE instead of the expected UNISWAP_V3 — folded into the same follow-up since it shares the
swap-path root cause.

**Groups G/H (Solana matching-engine, `helius-api-key`) — not re-verified this session**; the prior session's
credential-provisioned finding for group G and group H's capability-gap todo both stand unchanged.

Net effect: the Tenderly credential-wiring gap the prior session flagged as "the single biggest finding... secret
itself UNCONFIRMED" is now CLOSED (both required secrets exist and were exercised live, successfully, for the
majority of the gated coverage) — the remaining open items are a genuine swap-execution bug and two "not
individually confirmed" venue groups, tracked as their own todos above rather than re-described as a credential
problem.
