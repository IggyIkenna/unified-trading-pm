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
    /plans/archive/2026_08/defi_venue_e2e_batch1_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/issues/cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16.md,
    /codex/04-architecture/transfer-architecture.md,
  ]
created: 2026-08-16
author: interactive-session
parent_epic: security_and_cross_cutting_master
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
    execution-service/execution_service/defi_execution/protocols/uniswap.py,
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

- [x] ✅ [OPERATOR] P0. **RESOLVED BY MEASUREMENT 2026-08-21 (operator-authorized inspection).** The live
      `wallet_provisioning.json` / `wallet_mapping.json` DO NOT EXIST: probed every resolvable prod GCP bucket
      kind (all 26 from `resolve_bucket_name`, via UTL `get_storage_client().list_blobs` — no subprocess CLI)
      for a `wallet-config/` prefix — zero hits; `config-store-prd` carries only `instruments-service*/`
      prefixes and `execution-store-prd` only `_index/`+`cefi/`. No wallet was ever provisioned through this
      config path, so nothing could have been signed against the wrong chain while the fallback existed — the
      exposure window is EMPTY.
- [ ] [BACKEND] P3. Residual from the 2026-08-21 measurement above: probe the AWS-side buckets for a
      `wallet-config/` prefix the same way (UTL `list_blobs`, `resolve_bucket_name(cloud="aws")`, needs
      AWS_ACCOUNT_ID) and confirm the same absence — the custody loader path is GCP-first so this is
      completeness, not a live risk. Owned by T4's tranche run.
- [x] ✅ [BACKEND] P0. **Wire `cloud_kms.py` and `local_key.py` to call UAC's canonical `resolve_chain_id()` — done
      2026-08-16.** SHIPPED — `execution-service@33bd57a6fc`. Both files' `_resolve_chain_id()` now delegate to
      UAC's `resolve_chain_id()` for every chain name outside a narrow 3-entry local alias
      (`GOERLI`/`SEPOLIA`/`HOLESKY` — UAC's canonical resolver models a testnet via `env="testnet"` on the SAME
      canonical chain name, not as distinct literal chain-name strings, so these three legacy/testnet-specific
      names have no direct UAC equivalent and were kept as a local passthrough; every other chain name, including
      LINEA, now raises `ValueError` if genuinely unmapped instead of silently returning chain_id=1). Verified via
      2 new regression tests per file: an isolated resolver test confirming `LINEA` now resolves correctly
      (59144, previously silently 1) and an unknown-chain-raises test, PLUS a full-call-chain test exercising the
      real `CloudKmsCustodyProvider.create_transfer`/`LocalKeyCustodyProvider.create_transfer` path (not just the
      isolated resolver) with mocked KMS/secrets clients, confirming the `ValueError` propagates before any
      signing occurs — satisfies the todo's own done-when. 77 passed/1 skipped locally; full
      `quality-gates.sh --no-fix` green before commit.
      **New finding, not yet fixed**: `uniswap.py`'s already-migrated call site
      (`defi_execution/protocols/uniswap.py:211-214`) still wraps `resolve_chain_id()` in a bare
      `except ValueError: self._chain_id = 1` — the identical silent-wrong-chain pattern this issue is about,
      despite being listed as already-fixed by the prior remediation pass. Out of scope for this todo (only
      `cloud_kms.py`/`local_key.py` were named), tracked as a new P1 todo below.
- [x] ✅ [BACKEND] P1. **Add upstream chain validation in `transfer_handler.py`'s `_execute_onchain_transfer`/
      `_execute_custody_transfer`** — fail loud on an unrecognized chain before it ever reaches a custody
      provider, as defense in depth (the direct fix above closes the specific silent-fallback bug; this closes
      the broader "no allowlist validation at the entry point" gap that let it happen). **Fixed —
      `execution-service@6626aea5c9`**: added a module-level `_validate_chain(chain: str) -> str | None` helper
      that resolves the chain via UAC's canonical `resolve_chain_id()` (mirroring the same narrow
      `GOERLI`/`SEPOLIA`/`HOLESKY` testnet-alias set already used in `cloud_kms.py`/`local_key.py`, since UAC
      models testnets via `env=` on the same canonical chain name rather than as distinct literal strings), and
      wired a check at the top of both `_execute_onchain_transfer` and `_execute_custody_transfer` that returns
      a clean `ExecutionResult` failure (never an uncaught exception) before the adapter/custody provider is
      ever called. 4 new tests in `tests/unit/test_transfer_handler_chain_validation.py`: unrecognized-chain
      rejection for both methods (asserting the fake adapter's `execute_onchain_transfer` was never invoked, not
      just that the final result failed), a recognized-chain acceptance test, and a testnet-alias acceptance
      test (confirms `SEPOLIA` isn't false-positive rejected). 8562 passed/21 skipped, full
      `quality-gates.sh --no-fix` green before commit.
- [x] ✅ [BACKEND] P1. **`uniswap.py`'s `resolve_chain_id()` call site still silently falls back to chain_id=1 on
      `ValueError`** (`execution-service/execution_service/defi_execution/protocols/uniswap.py:211-214`) — found
      2026-08-16 while fixing the sibling `cloud_kms.py`/`local_key.py` bug above. Despite being one of the three
      files this issue doc's "What I found" section credits as already migrated onto UAC's canonical resolver by
      a prior remediation pass, the migration only swapped the lookup table, not the silent-fallback behavior —
      an unrecognized `chain_name` (parsed from the venue string, e.g. `UNISWAP_V3-<CHAIN>`) still resolves to
      Ethereum mainnet instead of raising. Same failure class, same fix pattern: remove the `except ValueError`
      swallow, let it raise. **Fixed — `execution-service@c3d63e4411`**: removed the swallow in
      `UniswapConnector.__init__`; `self._chain_id` now comes straight from `resolve_chain_id(resolved_name, _env)`
      with no except clause. Note this file never had the `GOERLI`/`SEPOLIA`/`HOLESKY` local-alias need the
      `cloud_kms.py`/`local_key.py` fix required — its only local alias (`_CHAIN_NAME_ALIASES` in
      `uniswap_encoding.py`) is `"ETH"->"ETHEREUM"`, unrelated to testnet naming, so no alias dict was added here.
      2 new tests in `tests/defi_execution/unit/test_protocols.py`: a known-chain resolution check
      (`UNISWAP_V3-ARBITRUM` → 42161) and, per the done-when, a full-call-chain test constructing
      `UniswapConnector(venue="UNISWAP_V3-XYZUNKNOWNCHAIN")` directly (not an isolated resolver call) asserting
      `ValueError` — since the resolution happens in `__init__`, the constructor call itself is the full call
      chain here. 8546 passed/21 skipped, full `quality-gates.sh --no-fix` green before commit.

## Progress Log

**2026-08-16 (even later still, same session)**: Fixed the `transfer_handler.py` defense-in-depth P1 todo —
SHIPPED `execution-service@6626aea5c9`. Added a `_validate_chain()` helper (UAC `resolve_chain_id()` +
mirrored testnet-alias set) and wired it into `_execute_onchain_transfer`/`_execute_custody_transfer` so an
unrecognized chain fails loud with a clean `ExecutionResult` before the adapter/custody provider is ever
called. 4 new tests, 8562 passed/21 skipped, full `quality-gates.sh --no-fix` green before commit. This closes
every actionable-now todo from this issue doc — only the `[OPERATOR]`-owned live wallet-provisioning check
remains open.

**2026-08-16 (later still, same session)**: Fixed the `uniswap.py` P1 todo — SHIPPED `execution-service@c3d63e4411`.
Removed the `except ValueError: self._chain_id = 1` swallow in `UniswapConnector.__init__`; an unrecognized venue
chain suffix now raises instead of silently signing as Ethereum mainnet. 2 new tests added (known-chain resolution
+ full-constructor-call-chain unknown-chain-raises). Full `quality-gates.sh --no-fix` green (8546 passed/21
skipped) before commit. This closes every actionable-now todo from this issue doc except the `transfer_handler.py`
defense-in-depth P1 (still open) and the `[OPERATOR]`-owned live wallet-provisioning check.

**2026-08-16 (later, same session)**: Fixed the primary `cloud_kms.py`/`local_key.py` todo — SHIPPED
`execution-service@33bd57a6fc`. Both `_resolve_chain_id()` implementations now delegate to UAC's canonical
`resolve_chain_id()`, with a narrow local alias preserved for `GOERLI`/`SEPOLIA`/`HOLESKY` (UAC's resolver models
testnets via `env=` on the same canonical chain name, not as distinct literal strings, so these three have no
direct UAC equivalent). 4 new regression tests added (2 per file: an isolated-resolver LINEA/unknown-chain check,
and a full `create_transfer` call-chain check) — 77 passed/1 skipped, full `quality-gates.sh --no-fix` green
before commit. While fixing this, found `uniswap.py` has the identical silent-fallback bug at its own
already-migrated `resolve_chain_id()` call site — new P1 todo above, not fixed in this pass (out of this todo's
named scope).
**2026-08-16 (later, same session)**: Traced the exact GCS path template for `WalletProvisioningConfig`
(`unified_api_contracts/internal/domain/defi/wallet_config.py:211,638`) — narrows the operator's follow-up work,
but stopped short of actually querying live GCS content for this specific file: querying real production
custody/wallet-signing-surface assignments is judgment-and-access territory appropriate for the operator to run
directly, not something to chase autonomously via guessed credentials for data this sensitive. Retagged the
reachability todo `[OPERATOR]` accordingly.
- **2026-08-16**: Filed during the defi AG batch's step-9 (transfers) venue-readiness sweep, immediately followed
  by a dedicated reachability research pass (mirroring the cefi CCXT-withdraw-stub investigation). Verdict:
  REACHABLE-BUT-GATED, not dead code — flagged to the operator directly as more urgent than the cefi finding,
  given a real, wired, provisioned custody path and a chain (LINEA) already marked live for this exact venue
  family.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries) — added execution_service/defi_execution/protocols/uniswap.py (the shipped chain-id-fallback fix, execution-service@c3d63e4411)
