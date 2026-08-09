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

- [x] ✅ [DATA] P2. Root-cause why `token_transfers_handler`'s Alchemy `alchemy_getAssetTransfers` calls return empty
      specifically when executed inside the `uts-prod-mtds-collect-token-transfers` Cloud Run Job —
      market-tick-data-service@0b18705b + live verification below. **Network/IP throttling ruled out**: the sibling
      `uts-prod-mtds-collect-bridge-events` job runs in the SAME Cloud Run environment (same
      project/region/networking/shared NAT IP, same `_make_session()` `ThreadedResolver`, same `alchemy-api-key`)
      calling a DIFFERENT Alchemy RPC method (`eth_getLogs`) and got 5,244/6,591 real rows on the same days — so the
      IP-throttling/geo-restriction/DNS-resolver candidates the todo listed are falsified. **Actual bug found by code
      inspection**: `_fetch_transfers_for_chain`'s per-token `alchemy_getAssetTransfers` call used a raw
      `session.post(...)` + `data.get("result", {}).get("transfers", [])` instead of the shared `_rpc_call` helper
      (already used by the block-range binary search, and already used by the working sibling `bridge_events_handler`) —
      a 200-with-JSON-RPC-`"error"`-envelope response silently fell through to `{}` → `[]` with **no exception and no
      log line at all**, so if every per-token call for a chain errored this way the chain fell through to
      `record_zero_rows` (an honest-looking `empty_confirmed`) instead of `record_failed`. This matches the observed
      symptom exactly: fast completion (~4-8s per chain), zero warnings in Cloud Logging across both failed executions,
      real 200-shaped responses. Fix: switched the per-token call to `_rpc_call` (raises on a JSON-RPC error envelope)
      and made the chain raise if EVERY per-token attempt fails (so a real failure now surfaces as `record_failed` with
      the actual error text logged, never silently as zero). 34/34 unit tests pass (2 new tests added covering
      all-fail→raise and partial-fail→partial-rows). **Live verification**: built the fixed commit into a fresh image
      (Cloud Build `555599fb-368d-4cb9-94df-232a4ab58b96`, SUCCESS), retagged it `:latest` (matching Terraform's
      declared `local.mtds_image`, no IaC drift), pointed the job at it, executed live
      (`uts-prod-mtds-collect-token-transfers-t7577`) — **`token_transfers for 2026-08-08: 7518 rows total`**, a real
      `capture_status=captured` manifest row with `row_count=7518`, matching the original direct-call reproduction
      exactly. Repo: market-tick-data-service. Done when: a Cloud Run execution of
      `uts-prod-mtds-collect-token-transfers` writes at least one `capture_status=captured` row with `row_count>0` — ✅
      met, execution `-t7577`, 2026-08-09 16:25:37 UTC. Evidence: cloudbuild=555599fb-368d-4cb9-94df-232a4ab58b96
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
- Sibling-job control (2026-08-09): `uts-prod-mtds-collect-bridge-events` (same project/region/networking, same
  `alchemy-api-key`, same `_make_session()`) — `bridge_events for 2026-08-08: 6591 rows total` /
  `2026-08-07: 6591 rows total` — real Alchemy data via `eth_getLogs` from the same Cloud Run environment, ruling out
  network/IP/DNS causes.
- Fix commit: `market-tick-data-service@0b18705b` — `_fetch_transfers_for_chain` now uses `_rpc_call` (raises on a
  JSON-RPC `"error"` envelope) instead of a raw `session.post` that silently coerced any non-`"result"` response to an
  empty transfer list; raises when every per-token attempt for a chain fails so the caller records `record_failed`
  instead of `record_zero_rows`. 34/34 unit tests pass (`test_raises_when_every_token_call_fails`,
  `test_partial_token_failure_returns_successful_rows` added).
- Live re-verification: Cloud Build `555599fb-368d-4cb9-94df-232a4ab58b96` (SUCCESS) → retagged `:latest` → job
  execution `uts-prod-mtds-collect-token-transfers-t7577` → `token_transfers for 2026-08-08: 7518 rows total`,
  `capture_status=captured` manifest row written (`market-data-tick-defi-prd-central-element-323112/_index/per_vm/`).
- Caveat: no raw JSON-RPC error body was captured from the two ORIGINAL failing executions (they logged zero warnings by
  construction — that silence was the bug), so this fix is confirmed correct-by-code-inspection + confirmed-working
  live, but whether the original two runs' underlying Alchemy-side condition was a genuine per-call RPC error vs. some
  other transient condition that had already cleared by the time of this re-verification (~1.5-3h later) could not be
  distinguished after the fact. Either way, the handler no longer has a code path that can silently misclassify a real
  failure as an honest empty — if it recurs, the next Cloud Run execution will now log the real error and record
  `record_failed`, giving a diagnosable signal instead of another silent `empty_confirmed`.
