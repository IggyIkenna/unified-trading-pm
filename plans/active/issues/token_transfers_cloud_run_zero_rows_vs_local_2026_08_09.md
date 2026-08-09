---
doc_type: issue
title:
  token_transfers collector returns 0 rows from Cloud Run despite real data confirmed reachable via identical
  code+key+params outside the container
summary: >-
  Two live Cloud Run executions of the newly-scheduled uts-prod-mtds-collect-token-transfers job each wrote honest
  empty_confirmed/SOURCE_RETURNED_ZERO manifest rows for all 4 venues, but calling the same production function directly
  outside the container with the same key/params returned 7,518 real ETHEREUM rows — a genuine Cloud-Run-vs-direct-call
  discrepancy. Separately, ARBITRUM/BASE/OPTIMISM use Ethereum-mainnet token addresses that can never resolve on those
  chains.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, token_transfers, alchemy, honest-absence, cloud-run]
related:
  [/plans/active/defi_satellite_ao_dispatch_batch11_2026_08_09.md, /plans/active/defi_migration_audit_log_2026_07_24.md]
created: "2026-08-09"
author: slot-27
source: [defi_satellite_ao_dispatch_batch11-ab5706a4ba0a]
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# token_transfers: Cloud Run executions consistently return 0 rows; direct code-level test does not

## What I found

While wiring `collect-token-transfers` into the Cloud Scheduler chain
(`deployment-service/terraform/gcp/defi_collection_scheduler.tf@a791a273`,
`defi_satellite_ao_dispatch_batch11_2026_08_09.md`), two separate real production executions of the new
`uts-prod-mtds-collect-token-transfers` Cloud Run Job (`uts-prod-mtds-collect-token-transfers-zssjz`, `-x2lg2`) each
wrote a genuine, honest `capture_status=empty_confirmed`/`error_reason=SOURCE_RETURNED_ZERO` manifest row for all 4
venues (`ALCHEMY`/`{ETHEREUM,ARBITRUM,BASE,OPTIMISM}`, `2026-08-08`) — 0 rows collected, no exceptions, no warnings.

Immediately after the 2nd run, I called the exact same production function
(`token_transfers_handler._fetch_transfers_for_chain`, unmodified, same real `alchemy-api-key` secret,
`chain_name="ETHEREUM"`, `target_date=2026-08-08`) directly from a Python shell on this VM (not inside the Cloud Run
container) and got **7,518 real rows** (first: WETH transfer at block 0x... on 2026-08-08). A raw
`alchemy_getAssetTransfers` curl against `eth-mainnet.g.alchemy.com` with the exact block range the handler's own binary
search resolved also returned real data. So the code, the key, and the Alchemy API are all correct — only the **Cloud
Run execution path** consistently returns empty.

Separately (found during the same investigation, distinct bug): for `chain_name != "ETHEREUM"` (ARBITRUM/BASE/OPTIMISM),
the handler queries those chains using the **Ethereum-mainnet** contract addresses in `_FALLBACK_DEFI_TOKENS` (e.g. WETH
`0xc02aaa...`) — ERC-20 contract addresses are chain-specific; a raw `alchemy_getAssetTransfers` query against
`arb-mainnet` with the Ethereum WETH/USDT address, `fromBlock=0x0..latest` (full history), returns literally 0
transfers, confirming those 3 chains can **structurally never** produce data with the current address table regardless
of the Cloud Run issue above.

## Why it matters

The Cloud Scheduler cron (`20 2 * * *` daily, live as of 2026-08-09) will keep recording honest `empty_confirmed` rows
forever for ETHEREUM (not a placeholder — a real, correctly-classified absence per the honest-absence contract) even
though the token DOES have real transfer data available. This under-delivers the "MVP scope, wire a real source" intent
even though the wiring itself is correct and the manifest is not lying.

## Recommended decision

- [ ] [DATA] P2. Root-cause why `token_transfers_handler`'s Alchemy `alchemy_getAssetTransfers` calls return empty
      specifically when executed inside the `uts-prod-mtds-collect-token-transfers` Cloud Run Job (2 real executions,
      both zero) vs. real data when the identical function is called directly outside the container with the same
      key/params (7,518 rows for ETHEREUM/ 2026-08-08). Likely candidates to check first: Alchemy IP-based
      throttling/geo-restriction on the Cloud Run service's outbound NAT IP (shared with other Alchemy-calling DeFi
      `collect-*` jobs — check for concurrent-window rate-limit correlation), a response silently trimmed by an
      intermediate proxy/VPC egress rule, or a subtle timeout/short-circuit specific to the container's aiohttp/DNS
      resolver path (`_make_session()`'s `ThreadedResolver`). Repo: market-tick-data-service. Done when: a Cloud Run
      execution of `uts-prod-mtds-collect-token-transfers` writes at least one `capture_status=captured` row with
      `row_count>0`.
- [ ] [DATA] P2. Fix `token_transfers_handler._FALLBACK_DEFI_TOKENS` (and the equivalent instruments-manifest path in
      `_resolve_token_list`) to use chain-specific ERC-20 contract addresses for ARBITRUM/BASE/OPTIMISM instead of
      reusing the Ethereum-mainnet addresses — confirmed via a real `alchemy_getAssetTransfers` full-history
      (`fromBlock=0x0`) query per chain returning 0 for the current addresses. Repo: market-tick-data-service. Done
      when: each non-ETHEREUM chain's `WETH`/`USDC`/`USDT` addresses resolve to that chain's real canonical contract
      (verify against a block explorer or a canonical address registry) and a live run records a `captured` row with
      `row_count>0` for at least one non-ETHEREUM chain.

## Evidence

- Cloud Run executions: `uts-prod-mtds-collect-token-transfers-zssjz` (14:08 UTC),
  `uts-prod-mtds-collect-token-transfers-x2lg2` (14:53 UTC), both `succeededCount=1`, both wrote 4×
  `empty_confirmed`/`SOURCE_RETURNED_ZERO` rows to
  `gs://market-data-tick-defi-prd-central-element-323112/_index/per_vm/`.
- Direct-call reproduction: `.venv/bin/python` calling
  `token_transfers_handler._fetch_transfers_for_chain(session, real_key, "eth-mainnet", "ETHEREUM", date(2026,8,8), _FALLBACK_DEFI_TOKENS)`
  → 7,518 rows.
- Wrong-chain-address reproduction: raw `alchemy_getAssetTransfers` against `arb-mainnet` / `base-mainnet` /
  `opt-mainnet` for USDT's Ethereum-mainnet address, `fromBlock=0x0,toBlock=latest` → 0 transfers on all 3 (vs. 1000+ on
  `eth-mainnet` for the same query).
