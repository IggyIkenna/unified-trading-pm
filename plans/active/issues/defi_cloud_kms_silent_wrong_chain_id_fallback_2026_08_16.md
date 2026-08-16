---
doc_type: issue
title: CloudKmsCustodyProvider silently resolves an unmapped chain to chain_id=1 (Ethereum) instead of failing loud
summary: >-
  execution-service's CloudKmsCustodyProvider._resolve_chain_id() (the default May-23-cutover custody surface for
  HOT_TRADING/GAS_RESERVE wallets) hardcodes a narrow chain-name map and silently falls through to chain_id=1
  (Ethereum mainnet) for any unmapped chain, instead of raising like UAC's own canonical resolve_chain_id() does.
  Confirmed REACHABLE-BUT-GATED, not dead code: the provider is genuinely constructed and provisioned with real
  HSM-backed keys, and LINEA (one of the unmapped chains) is already wired end-to-end elsewhere in
  execution-service and marked "live" for data capture. Found during the venue_e2e_wiring_2026_08_16 defi batch
  sweep, step 9 (transfers).
status: open
nature: issue
asset_group: [defi]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [transfers, financial-correctness, live-money-risk, chain-resolution, venue-readiness]
related:
  [
    /plans/active/defi_venue_e2e_batch1_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/issues/cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16.md,
    /codex/04-architecture/transfer-architecture.md,
  ]
created: 2026-08-16
author: interactive-session
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found 2026-08-16 during defi_venue_e2e_batch1_2026_08_16.md's step-9 (transfers) contract sweep, then confirmed
  via a dedicated reachability research pass (same rigor as the sibling cefi CCXT-withdraw-stub finding).
context_scope:
  [
    execution-service/execution_service/custody/cloud_kms.py,
    execution-service/execution_service/custody/local_key.py,
    unified-api-contracts/unified_api_contracts/registry/chain_env.py,
    /codex/04-architecture/execution-modes-and-chain-resolution.md,
  ]
---

# CloudKmsCustodyProvider silently resolves an unmapped chain to chain_id=1 instead of failing loud

## What I found

`CloudKmsCustodyProvider._resolve_chain_id()` hardcodes a chain-name-to-chain-id map covering only ETHEREUM/
GOERLI/SEPOLIA/ARBITRUM/OPTIMISM/POLYGON/BSC/AVALANCHE/BASE/HOLESKY. For any other chain string it does NOT
raise — it falls through to `if upper.isdigit(): return int(upper); return 1`, silently returning **chain_id=1
(Ethereum mainnet)** for an unmapped chain name. UAC's own canonical `resolve_chain_id()`
(`unified_api_contracts/registry/chain_env.py:716`) raises `ValueError` on the exact same class of input — this
provider re-implements a narrower, stale, silently-failing duplicate of a function that already exists and
already does the right thing.

**`local_key.py` has the identical bug with an even narrower map** (no LINEA/BASE/HOLESKY at all).

A prior remediation pass already migrated `bridge_cost_model.py`, `sor_cross_chain.py`, and `uniswap.py` onto
UAC's canonical resolver (`/codex/04-architecture/execution-modes-and-chain-resolution.md:184-185`) — `cloud_kms.py`
and `local_key.py` were missed by that pass.

## Why it matters — and why this is NOT dead code

Unlike the sibling cefi CCXT-withdraw-stub finding (confirmed genuinely inert today), this one is
**REACHABLE-BUT-GATED**:

- `CloudKmsCustodyProvider` is the real, wired May-23-cutover default custody surface for HOT_TRADING/GAS_RESERVE
  wallets (`/codex/04-architecture/custody-providers.md`), constructed by a real factory branch
  (`custody/factory.py::_create_cloud_kms_provider`), backed by 10 real HSM-backed CMKs actually provisioned in
  GCP `asia-northeast1` (`/codex/15-runbooks/custody-onboarding-checklist.md` §B, smoke-tested PASSED 2026-05-12).
- **LINEA is not a hypothetical unmapped chain** — `AAVE_V3-LINEA` is an active instrument referenced in
  `execution_service/engine/handlers/{borrow,lend}_handler.py`, and `unified-api-contracts/registry/
  defi_venues.py` marks it `"live"` for data capture. (SCROLL/ZKSYNC are still `"pipeline"`, not yet IS-producible;
  PLASMA has zero execution-service references despite being `"live"` for data — so of the 4 originally-flagged
  chains, LINEA specifically is the live-reachable one today.)
- `transfer_handler.py`'s `_execute_onchain_transfer`/`_execute_custody_transfer` read the chain string straight
  from `instruction.metadata.get("chain", "ETHEREUM")` with **zero allowlist validation** before it reaches
  `_resolve_chain_id` — nothing upstream catches an unmapped chain.
- The only real gates are (a) system-wide pre-live-trading status (`.claude/CLAUDE.md`, unsuperseded as of
  2026-08-16), and (b) live `wallet_provisioning.json` content (GCS-hosted `signing_surface` per wallet) — **not
  verifiable from a repo checkout**, so this issue does NOT get to claim the same "confirmed inert" status the
  CCXT finding earned.

If a LINEA custody operation were ever attempted through a `CLOUD_KMS_ENCRYPTED` wallet before this is fixed, it
would silently sign with `chainId=1` (Ethereum) instead of LINEA's real `59144` — a wrong-chain signature, not a
no-op. Depending on the signing scheme this could produce an invalid transaction (safe-but-broken) or, in the
worst case, a transaction that is valid on the wrong chain.

## What I have NOT verified

- The live content of `wallet_provisioning.json` (GCS-hosted, not present in this checkout) — whether any
  HOT_TRADING/GAS_RESERVE wallet that could touch LINEA is actually assigned `signing_surface=CLOUD_KMS_ENCRYPTED`
  today, vs. `COPPER_MPC` (which is chain-agnostic and unaffected by this bug).
  `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` and the custody-onboarding-checklist may
  have this — worth checking as the FIRST step of the fix, since it directly determines urgency.

## Todos

- [ ] [BACKEND] P0. **Check live `wallet_provisioning.json` content** (GCS, not in a repo checkout) for any
      wallet with `signing_surface=CLOUD_KMS_ENCRYPTED` that could plausibly touch LINEA (or any other
      cloud_kms-unmapped chain). Done-when: a cited, evidence-backed answer — this determines whether the fix is
      urgent-before-any-LINEA-op or can follow normal priority.
- [ ] [BACKEND] P0. **Wire `cloud_kms.py` and `local_key.py` to call UAC's canonical `resolve_chain_id()`**
      instead of their local, narrower, silently-failing maps — the same fix the prior remediation pass already
      applied to `bridge_cost_model.py`/`sor_cross_chain.py`/`uniswap.py`. Done-when: an unmapped chain raises
      instead of silently resolving to chain_id=1, verified with a test exercising exactly this path (not just a
      unit test of `resolve_chain_id` in isolation — the actual `CloudKmsCustodyProvider.create_transfer` call
      chain).
- [ ] [BACKEND] P1. **Add upstream chain validation in `transfer_handler.py`'s `_execute_onchain_transfer`/
      `_execute_custody_transfer`** — fail loud on an unrecognized chain before it ever reaches a custody
      provider, as defense in depth (the direct fix above closes the specific silent-fallback bug; this closes
      the broader "no allowlist validation at the entry point" gap that let it happen).

## Progress Log

- **2026-08-16**: Filed during the defi AG batch's step-9 (transfers) venue-readiness sweep, immediately followed
  by a dedicated reachability research pass (mirroring the cefi CCXT-withdraw-stub investigation). Verdict:
  REACHABLE-BUT-GATED, not dead code — flagged to the operator directly as more urgent than the cefi finding,
  given a real, wired, provisioned custody path and a chain (LINEA) already marked live for this exact venue
  family.
