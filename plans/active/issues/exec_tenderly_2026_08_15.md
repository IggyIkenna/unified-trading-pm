---
doc_type: issue
title: execution-service RecursiveLoopOrchestrator Tenderly-fork integration test is credential-blocked
summary: >-
  `execution-service/tests/defi_execution/unit/test_recursive_loop_orchestrator.py::test_tenderly_fork_full_cycle`
  exercises a 5-loop wstETH/WETH E-Mode open+unwind against a live Aave V3 pool via a Tenderly fork RPC. No Tenderly
  fork endpoint/API key is provisioned in this workspace's ambient credential set (GSM/CI secrets), so the test is
  `@pytest.mark.skip`ped pending provisioning. Filed to satisfy `check_xfail_skip_tracked.py`'s tracked-slug requirement
  (`ci-reconcile` root-caused this as the sole `quality-gates-v2` red on `execution-service` live-defi-rollout push
  `37bfaeed`, a genuine new-code push wiring real Uniswap/Lido/Jupiter/Aave/Kamino/Jito dispatch — the skip marker
  landed with that commit but without a tracking citation).
status: open
nature: issue
asset_group: [defi]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [credential-blocked, tenderly, aave-v3, integration-test, defi-execution]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md,
  ]
created: 2026-08-15
author: ci_reconciler (agt-f0dda8, slot 8)
source: ci_reconciler CI sweep (quality-gates-v2 red on execution-service live-defi-rollout push 37bfaeed)
parent_epic: defi_master
priority: P3
assigned_vm: NA
execution_scope: local-only
locked_by:
locked_since:
context_scope: [execution-service/tests/defi_execution/unit/test_recursive_loop_orchestrator.py, /codex/02-data/external-data-always-available-rule.md]
supersedes:
superseded_by:
depends_on: []
resolved_by:
drift_direction: advance-code
---

# execution-service Tenderly-fork Aave V3 integration test — credential-blocked

## What was found

`test_tenderly_fork_full_cycle` (RecursiveLoopOrchestrator 5-loop wstETH/WETH E-Mode open+unwind, Phase-4-deployed
receiver) requires a live Tenderly fork RPC endpoint plus real Aave V3 pool access. Neither is provisioned in this
workspace's ambient GSM/CI credential set. The test is correctly `@pytest.mark.skip`-ped rather than fabricating a pass,
per `/codex/02-data/external-data-always-available-rule.md`'s BLOCKED-CREDENTIALS pattern — the adapter/test scaffold
already exists and is wired, it just cannot execute against live infra without the credential.

## Todos

- [x] ✅ [OPERATOR] P3. Provision a Tenderly fork RPC endpoint + API key (and confirm Aave V3 pool read/write access
      through it) for `execution-service` CI, then un-skip `test_tenderly_fork_full_cycle` and verify it passes against
      the live fork. **D16 2026-08-21 operator ruling** (see
      `/plans/active/issues_corpus_completion_dispatch_2026_08_21.md`) **— provisioned**: `tenderly-api-key`, `tenderly-fork-rpc-url`,
      `defi-wallet-private-key` all confirmed present with non-empty latest versions in GSM
      (`central-element-323112`). Un-skipped and given a real body 2026-08-21/22 —
      `execution-service@58e4eed74a` (see Progress Log below for the real-fork run evidence and the
      new finding it surfaced). Real fork runs now happen against
      `tests/defi_execution/integration/test_recursive_loop_fork_e2e.py::TestRecursiveLoopPersistentDriverOnFork`, not
      the original `unit/test_recursive_loop_orchestrator.py` stub (moved there because it needs that directory's
      own `tenderly_fork`/`funded_wallet`/`aave_connector`/`uniswap_connector` fixtures, which pytest cannot resolve
      across into `unit/`).
- **na-eligibility-audit 2026-08-16** [body-hash:4939ad84f015af58]: KEEP-NA, valid — Single open todo requires provisioning a live Tenderly fork RPC endpoint + API key (with confirmed Aave V3 pool read/write access) to un-skip `test_tenderly_fork_full_cycle` — no such credential exists in the workspace's ambient GSM/CI secret set, and this cannot be self-served by an agent.

## Progress Log

**context-scout 2026-08-17**: populated/refreshed context_scope (2 entries)
**na-eligibility-audit 2026-08-17** (defi tranche, dispatch agt-f4fef7): KEEP-NA, valid — re-confirmed; no
substantive content change since the 2026-08-16 verdict (context-scout metadata touch only). Sole open todo still
requires operator-provisioned Tenderly fork RPC + API key, not agent-self-serviceable. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-21** (defi tranche, wave 2): KEEP-NA, valid — re-confirmed; sole open todo still requires an operator-provisioned Tenderly fork RPC + API key, not agent-self-serviceable. Doc stays `assigned_vm: NA`.
- **D16 dispatch, execution-service (slot 6) 2026-08-21/22**: Verified all three named secrets
  (`tenderly-api-key`, `tenderly-fork-rpc-url`, `defi-wallet-private-key`) have a non-empty ENABLED latest version
  via `gcloud secrets versions access` (byte lengths only checked, never printed values). Wrote a real test body
  (the original `test_tenderly_fork_full_cycle` was a literal `...` stub, not just skip-marked) at
  `tests/defi_execution/integration/test_recursive_loop_fork_e2e.py`, reusing this directory's existing
  `tenderly_fork`/`funded_wallet`/`aave_connector`/`uniswap_connector` conftest fixtures (the same ones
  `test_engine_to_fork_e2e.py` already uses), plus a new `wsteth_funded_wallet` fixture (the shared `funded_wallet`
  only funds ETH/USDC/DAI, and this is the first fork test needing wstETH collateral). Ran it for real against a live
  Tenderly Virtual TestNet twice:
  1. **First run found a genuine, separate bug**: `execution_service/defi_execution/protocols/aave_live.py`'s
     `TOKEN_ADDRESSES`/`TOKEN_DECIMALS` dicts had NO `"WSTETH"` entry at all — every live
     `supply()`/`borrow()`/`withdraw()`/`repay()` call for this archetype's own named collateral asset
     (`RecursiveLoopRequest.collateral_asset="WSTETH"` is the module's own scenario default) silently failed closed
     with `_resolve_token_address()` returning `None`, no exception, no log line. **Fixed same session** —
     `execution-service@58e4eed74a` adds `"WSTETH": required_lst_address("wstETH")` (reuses the
     existing UAC `lst_token_addresses` SSOT `lido.py`'s own `WSTETH_ADDRESS` already resolves through, not a second
     hardcoded literal) + `"WSTETH": 18` to `TOKEN_DECIMALS`.
  2. **With that fixed, two independent re-runs (fresh Tenderly VNet each time) reproduced a new, external,
     infra-side boundary, not a code bug**: the wallet's first 5 real on-chain writes (one ERC-20 `approve()` per
     loop's compounding supply amount — 1.0/0.5/0.25/0.125/0.0625 wstETH) land on-chain successfully with real tx
     hashes each time; the 6th real write — the actual `Pool.supply()` call to Aave's real pool contract
     (`0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`) — gets `HTTP 403 Forbidden` straight from Tenderly's own RPC
     gateway (`requests.exceptions.HTTPError`, not an on-chain revert, not a web3 exception the orchestrator's own
     error-classification path touches). Deterministic across both runs (VNet ids `9727b1ef-...`/`57e6a7a9-...`,
     distinct real approve tx hashes each time, identical failure point at write #6). Read as a write-RPC-call quota
     or contract-complexity guard on the currently-provisioned Tenderly account tier tied to `tenderly-api-key` —
     not something fixable in this repo's code. **Recorded, not silently glossed over** (per this dispatch's own
     "or record the exact failure" instruction): both new test methods are `@pytest.mark.xfail(strict=False)` citing
     this exact finding, not reverted to a plain `skip` — the whole point of a real test body over the original stub
     is that it un-xfails itself the moment Tenderly access is upgraded, with zero further code change.
  Also verified (same session, D19/D12 dispatch overlap): `bybit-testnet-trade-api-key` exists with a real value, but
  **`bybit-testnet-trade-api-key-secret` exists with an ENABLED version whose payload is 0 bytes** (empty) — would
  have silently broken a bybit-testnet CEX_WITHDRAW attempt; used `deribit-testnet-write-api-key`/`-secret` instead
  (both non-empty), see `cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16.md`'s Progress Log for that run's
  evidence. **New follow-up filed below** rather than left as prose.

## Todos (continued)

- [ ] [OPERATOR] P3. Upgrade or otherwise raise the write-RPC ceiling on the Tenderly account/plan tied to
      `tenderly-api-key` — the currently-provisioned tier accepts exactly 5 real on-chain writes per Virtual TestNet
      before returning `HTTP 403 Forbidden` on the 6th (reproduced twice, deterministic; see the dated Progress Log
      entry above for the two VNet ids + tx-hash evidence). Done-when: a 6+-write test
      (`tests/defi_execution/integration/test_recursive_loop_fork_e2e.py`) completes past write #6 without a 403; then
      remove the `xfail` markers from both tests in that file.
- [ ] [OPERATOR] P3. Provision a real value for `bybit-testnet-trade-api-key-secret` (the GSM secret exists with an
      ENABLED version but its payload is 0 bytes) — found verifying secrets for this same D16/D19 dispatch. Not
      currently blocking anything (deribit-testnet covered the CEX_WITHDRAW testnet-verification requirement
      instead), but leaves bybit-testnet unusable for any future testnet verification pass until filled in.
