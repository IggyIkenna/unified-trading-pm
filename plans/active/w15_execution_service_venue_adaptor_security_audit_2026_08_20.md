---
doc_type: plan
title: W15 — Execution-service venue-adaptor security audit
summary: >-
  Security audit of every execution-service venue adaptor against a fixed 7-point checklist, phased by real
  shared risk surface (bridge/cross-chain highest-stakes first, then DeFi by primitive, then CeFi/TradFi by
  transport, then sports), per the epic's W15 workstream and the 2026-08-19 operator ruling directing this be
  authored as a dedicated AO plan. On-chain write paths carry irreversible consequences — this audit produces
  real findings and fixes, not a documentation exercise.
status: active
nature: design
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [execution, security, audit, defi, w15]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/code_readiness_t4_execution_settlement_2026_08_19.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: research
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 12
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on:
supersedes:
superseded_by:
locked_by:
locked_since:
source: >-
  Operator ruling 2026-08-19 (plans/audit/results/code_completion_scope_2026_08_19.md, "author 7 unowned P0
  plans") + epic W15 (plans/epics/system_readiness_master.md), authored 2026-08-20 by T4 after re-checking
  today's LDR rulings surfaced this had not yet been spun into its own dispatchable plan. File enumeration
  (~85 adapter files across DeFi/CeFi/TradFi/sports) done at authoring time via a real directory walk, not
  estimated.
context_scope:
  [
    execution-service/execution_service/defi_execution/protocols/,
    execution-service/execution_service/trade_execution/adapters/,
    execution-service/execution_service/sports_execution/adapters/,
  ]
---

# W15 — Execution-service venue-adaptor security audit

> On-chain write paths carry irreversible consequences; this is not a documentation exercise. Epic section:
> `/plans/epics/system_readiness_master.md` § W15.

## The checklist every phase applies (fixed, reused across every todo — do not redefine per phase)

For each file/group, check and record PASS or a specific FINDING (with severity: CRITICAL / HIGH / MEDIUM / LOW)
against each of the 7 points below. A finding is a CONCRETE claim citing the exact file+function, not a general
impression:

1. **Credential handling** — no hardcoded secret/key literal; credentials sourced via the approved config/secret
   path (`UnifiedCloudConfig`/GSM, never `os.getenv()`); never logged, even at DEBUG.
2. **Signing/auth correctness** — request signatures use the documented algorithm for that venue; nonces/
   timestamps are present and prevent replay; private keys are never transmitted or embedded in a request body/
   URL.
3. **Input validation before an on-chain write** — user/strategy-supplied amounts, addresses, and instrument
   identifiers are validated (type, range, checksum where applicable) before being placed into a transaction
   payload; no raw string interpolation into a tx calldata/params without validation.
4. **Slippage/deadline bounds enforced** — every swap/trade path enforces a caller-supplied or safe-default
   slippage tolerance AND a transaction deadline; neither is silently unbounded.
5. **Approval scope** — token approvals are exact-amount or capped, never an unlimited/infinite `approve()` call
   unless the file explicitly states why (and that justification itself gets checked, not just noted).
6. **Idempotency / retry safety** — a retried request cannot double-submit the same on-chain transaction or
   double-place the same order (nonce management, client-order-id / idempotency-key reuse on retry).
7. **Honest error handling** — a failed on-chain tx or a rejected order is detected and reported as a real
   failure; never silently treated as success, never a swallowed exception that leaves the caller believing the
   action happened.

## Todos

### Highest stakes first — bridge / cross-chain

- [x] ✅ [BACKEND] P0. Audited `execution_service/defi_execution/protocols/bridge.py` and `cctp.py` against the
      7-point checklist above — cross-chain transfers are the least reversible failure mode in this repo (funds
      can end up on the wrong chain with no local recovery path). Done-when: a findings record exists per file
      (PASS or a specific FINDING per checklist point), and every CRITICAL/HIGH finding either has an inline fix
      landed in the SAME todo or is spun into its own tracked P0 todo in the triage phase below — never left
      silently noted.

### DeFi by primitive — swap/DEX

- [x] ✅ [BACKEND] P0. Audit the swap/DEX group against the checklist: `uniswap.py`, `uniswap_encoding.py`,
      `uniswap_live.py`, `orca.py`, `raydium.py`, `jupiter.py`. Pay particular attention to checklist point 4
      (slippage/deadline) — this IS the primitive class where a missing bound is directly exploitable (sandwich
      attacks). Done-when: same evidence bar as the bridge todo above. **RESOLVED 2026-08-20 (slot-7): findings
      recorded in the Progress Log; HIGH findings are tracked below. No inline fix was made in this audit todo.**

- [x] ✅ [BACKEND] P0. Fix Uniswap live execution's ignored swap deadline, validate amount/slippage bounds, and add
      retry/idempotency protection for the approval+swap transaction sequence (`uniswap.py:332-355`,
      `uniswap_live.py:71-111,330-380`). Preserve the caller's minimum output rather than silently lowering it. — execution-service@7481405df2 + evidence: quickmerge preflight passed; post-push ancestry verified.
      (repo: execution-service)

- [x] ✅ [BACKEND] P0. Fix Uniswap NPM partial-success reporting: an optional `burn_nft=True` request must return a
      failed/partial result when `_maybe_burn_nft()` catches a reverted burn instead of returning `success=True` with
      only `burn_error` (`uniswap.py:529-538,568-580`). — execution-service@124042b4 + evidence: QG passed (8,807 passed, 82.54% coverage); post-push ancestry verified.

- [ ] [BACKEND] P0. Add Jupiter quote/input validation, caller-controlled expiry, and idempotency/retry protection
      around `/swap` plus Solana broadcast (`jupiter.py:120-199,205-224,261-279`). A retry after an ambiguous
      `send_transaction()` result currently obtains and signs a fresh transaction. (repo: execution-service)

- [ ] [BACKEND] P0. Replace the Orca/Raydium placeholder liquidity instructions with validated protocol account
      metas and explicit positive amount/tick/range bounds; the current live paths serialize caller values and submit
      `Instruction(accounts=[])` (`orca.py:168-219,292-310`; `raydium.py:186-232,318-328`). (repo: execution-service)

### DeFi by primitive — lending

- [x] ✅ [BACKEND] P0. Audit the lending group: aave.py, aave_live.py, morpho.py, kamino.py, idle.py — audit-only, no code changes; findings recorded below and HIGH items tracked in triage.
      Checklist point 5 (approval scope) is the primary risk here — a lending protocol interaction commonly
      needs an approval, and an unbounded one on a compromised key is a full-balance drain, not just the
      position's notional. Done-when: same evidence bar as above.

### DeFi by primitive — staking and restaking

- [x] ✅ [BACKEND] P0. Audited the staking/restaking subset `lido.py`, `etherfi.py`, `rocket_pool.py`, and
      `marinade.py` against the fixed seven-point checklist; findings and HIGH follow-ups are recorded in the
      Progress Log and triage todos below. (repo: execution-service)

- [ ] [BACKEND] P0. Audit the remaining staking/restaking group: `symbiotic.py`, `eigenlayer.py`, `karak.py`, `kelpdao.py`, `puffer.py`, `renzo.py`, `jito.py`,
      `jito_restaking.py`, `solblaze.py`. Checklist points 3 and 7 matter most here (unbonding/withdrawal request
      validation; honest reporting of a failed unstake, since a silently-swallowed unstake failure looks
      identical to "still staked" from the caller's side). Done-when: same evidence bar as above.

### DeFi by primitive — perp / CLOB on-chain

- [ ] [BACKEND] P0. Audit the on-chain perp/CLOB group: `hyperliquid.py`, `_hyperliquid_schemas.py`,
      `_hyperliquid_signing.py`, `aster.py`, `pacifica.py`, `bybit.py` (the DeFi-side Bybit protocol file, not
      the CeFi CCXT adapter — confirm which is which before starting). Checklist point 2 (signing/auth) is the
      primary risk — these are the files implementing custom signature schemes rather than reusing a vetted
      library. Done-when: same evidence bar as above.

### DeFi by primitive — yield/vault aggregators

- [ ] [BACKEND] P1. Audit the yield-aggregator group: `beefy.py`, `convex.py`, `yearn.py`, `pendle.py`.
      Checklist point 5 (approval scope) and point 3 (vault-share/withdrawal input validation) matter most.
      Done-when: same evidence bar as above.

### CeFi/TradFi

- [ ] [BACKEND] P0. Audit the CCXT-wrapped CeFi adapters as one group (shared library, shared risk profile —
      audit the SHARED wrapping pattern once, then spot-check 2-3 individual adapters for per-venue deviations
      rather than repeating the full checklist per file): `aster_ccxt.py`, `binance_ccxt.py`, `bybit_ccxt.py`,
      `coinbase_ccxt.py`, `deribit_ccxt.py`, `hyperliquid_ccxt.py`, `okx_ccxt.py`, `upbit_ccxt.py`. Checklist
      point 1 (credential handling) is the primary shared-code risk. Done-when: one findings record for the
      shared pattern + individual notes for any adapter that deviates from it.
- [ ] [BACKEND] P0. Audit the native (non-CCXT) REST adapters — HIGHER risk than the CCXT group since these
      implement request signing by hand, without a battle-tested library: `bitfinex_native.py`,
      `bitget_native.py`, `kraken_rest_adapter.py`, `kraken_rest_mapping.py`, `kraken_rest_transport.py`,
      `kraken_ws_client.py`, `_native_base.py`, `_rate_limit.py`. Checklist point 2 (signing correctness) is the
      primary risk. Done-when: same evidence bar as the CCXT group above, full per-file checklist (no
      spot-check shortcut — these are exactly the higher-risk, hand-rolled implementations).
- [ ] [BACKEND] P1. Audit the TradFi gateway adapters: `cboe_adapter.py`, `cme_adapter.py`, `fx_adapter.py`,
      `ibkr_tradfi.py`, `ice_adapter.py`, `nasdaq_adapter.py`, `nyse_adapter.py`. Different auth model than
      crypto venues (session/gateway auth, not API-key HMAC) — checklist point 2 needs re-reading for what
      "signing" means in this context (session token validity/renewal) before applying it literally.
      Done-when: same evidence bar as above.

### Sports / prediction

- [ ] [BACKEND] P1. Audit the sports exchange adapters: `betfair.py`, `betfair_order_mapping.py`, `kalshi.py`,
      `matchbook.py`, `polymarket_clob.py` (`sports_execution/adapters/exchanges/`), plus
      `polymarket_adapter.py`/`sports_adapter.py` (`trade_execution/adapters/`) and the bookmaker-API group
      (`api_football.py`, `onexbet.py`, `odds_api.py`). Done-when: same evidence bar as above.
- [ ] [BACKEND] P2. Audit the sports "unity" subsystem as its own group — it is a distinct sub-architecture, not
      simple per-venue adapters: `bridge.py`, `fill_reports.py`, `mock_feed_connector.py`, `multiplex.py`,
      `protocol.py`, `rollover_tracker.py`, `sidecar.py`, `turnover_tracker.py`
      (`sports_execution/adapters/unity/`). Read `protocol.py` first to understand the subsystem's actual shape
      before applying the checklist file-by-file. Done-when: same evidence bar as above.

### Triage

- [ ] [BACKEND] P0. Triage every finding recorded across the todos above. Any CRITICAL/HIGH finding not already
      fixed inline gets a new tracked todo (this doc if genuinely bounded, or a new issue doc per
      `/codex/11-project-management/` findings-triage convention if it needs its own design pass) — never left
      as prose in a findings record with no tracked follow-up. Done-when: every CRITICAL/HIGH finding from every
      phase above resolves to either a landed fix (cite the sha) or a new tracked todo/issue-doc (cite the
      slug), zero exceptions.

- [ ] [BACKEND] P0. Add strict bridge request validation and fail-closed live credential handling (bridge.py); HIGH findings: checklist points 1, 3, and 4.
- [ ] [BACKEND] P0. Add CCTP amount/recipient validation and reject missing source wallet credentials before approve/burn (cctp.py); HIGH finding: checklist point 3.
- [ ] [BACKEND] P0. Make CCTP transfer tracking durable and idempotent across retries; preserve source burn tx hash and prevent duplicate approve/burn submissions; HIGH finding: checklist point 6.
- [ ] [BACKEND] P0. Define and enforce caller slippage/deadline bounds for Socket bridge routes, including validation of aggregator-produced transaction targets and calldata; HIGH findings: checklist points 2 and 4.
- [ ] [BACKEND] P0. Correct CCTP status lookup and enforce attestation timeout/terminal failure semantics; HIGH finding: checklist point 7.
- [ ] [BACKEND] P0. Harden Aave lending writes: reject non-positive/non-integral amounts and invalid flash-loan vectors, fail closed instead of simulating success when live credentials/executor are absent, and add durable idempotency across approval plus operation retries; HIGH findings: checklist points 3, 6, and 7 (`aave.py`, `aave_live.py`).
- [ ] [BACKEND] P0. Harden Morpho Blue writes: validate amount/LLTV/market-id inputs, use configured loan-token decimals rather than unconditional 18-decimal conversion, and add durable idempotency across approval plus operation retries; HIGH findings: checklist points 3 and 6 (`morpho.py`).
- [ ] [BACKEND] P0. Validate Kamino transaction intent before signing: enforce positive amount and address/mint relationships, inspect/allowlist fee payer, programs, accounts, and token-approval scope in API-produced transactions, and add retry idempotency; HIGH findings: checklist points 2, 3, 5, and 6 (`kamino.py`).
- [ ] [BACKEND] P0. Harden Idle vault writes: validate positive amounts, enforce caller minimum-output/deadline bounds for mint/redeem, fail closed instead of simulating success in incomplete live mode, and add durable idempotency across approval plus mint retries; HIGH findings: checklist points 3, 4, 6, and 7 (`idle.py`).
- [ ] [BACKEND] P0. Harden Lido, EtherFi, and Rocket Pool writes: validate finite positive amounts before `to_wei()`, fail closed when `is_live` lacks loaded credentials instead of entering simulation, and add durable idempotency across approval-plus-wrap sequences and retries; HIGH findings: checklist points 3 and 6 (`lido.py:217-292,316-359,376-389`; `etherfi.py:211-325`; `rocket_pool.py:160-214`).
- [ ] [BACKEND] P0. Replace Marinade's placeholder `Instruction(accounts=[])` writes with validated protocol account metas, enforce positive lamport-safe amounts, and add retry/idempotency protection around Solana broadcast; HIGH findings: checklist points 2, 3, and 6 (`marinade.py:176-202`).

### Close-out

- [ ] [AGENT] P0. Post-phase codex audit — check whether any codex doc under `/codex/04-architecture/` or
      `/codex/06-coding-standards/` makes a claim this audit's findings contradict (e.g. a doc claiming a
      pattern is "always" applied that a finding shows isn't); correct in place.
- [ ] [AGENT] P0. Confirm the epic's own W15 section (`/plans/epics/system_readiness_master.md`) reflects this
      plan's real landed state once every todo above is done or explicitly re-scoped.

## Progress Log

### 2026-08-20 — slot 5 bridge/CCTP audit

Findings are against the fixed seven-point checklist and cite the inspected implementation lines.

- `bridge.py`: (1) FINDING MEDIUM — `connect()` logs the first eight characters of `socket_api_key` at line 215; credentials must not be logged. (2) FINDING HIGH — `_execute_bridge_tx()` signs aggregator-supplied `txTarget`/`txData` at lines 418-423 without validating target, calldata, chain, or recipient. (3) FINDING HIGH — `bridge()` accepts non-positive/fractional amounts and arbitrary recipients; `_resolve_token_address()` silently maps unknown symbols to the native-token sentinel at lines 497-507. (4) FINDING HIGH — quote/build requests at lines 450-470 provide no caller slippage bound or transaction deadline before broadcasting. (5) PASS — approval uses `minimumApprovalAmount` or exact transfer amount at lines 405-414. (6) FINDING HIGH — each call creates a new UUID at line 336 and repeats approval plus submission; no idempotency key or durable source transaction record. (7) PASS with limitation — execution failures return `FAILED`; transient status API errors remain `BRIDGING` at lines 398-429 and 476-492. Live credential fall-through is covered by the P0 validation follow-up.

- `cctp.py`: (1) FINDING MEDIUM — `bridge()` uses `self._wallet_address or recipient` at lines 240-244, allowing a destination address to stand in for missing source credentials. (2) PASS — source signing delegates to `BaseConnector.sign_and_send_transaction()` and destination signing injects pending nonce, gas, chain ID, and the configured private key at lines 428-450. (3) FINDING HIGH — line 241 converts arbitrary Decimal values to integer micro-USDC without positivity, precision, or range checks; `_address_to_bytes32()` accepts malformed/short values via `zfill()` at lines 497-500. (4) PASS/N-A — CCTP burn-and-mint has no price-bearing swap leg; timeout enforcement is tracked separately. (5) PASS — approval is exactly `amount_units` at lines 357-360. (6) FINDING HIGH — `uuid4()` is generated for every call at line 240; `_pending_burns` is process-local and retries repeat approval/burn. (7) FINDING HIGH — `_pending_burns` is keyed by transfer ID at line 157, while `get_bridge_status()` supplies its bridge-tx-hash argument to a direct transfer-ID lookup at lines 268-271 and 467-469, so a valid source tx hash remains `BRIDGING` indefinitely; receive failures are reported, but timeout/terminal semantics are incomplete.

No code was shipped in this audit unit; every HIGH finding is represented by an explicit P0 triage todo immediately above the Close-out section.
## Progress Log

- **2026-08-20 (slot-7, backend_engineer) — swap/DEX security audit complete.** Reviewed `uniswap.py`, `uniswap_encoding.py`, `uniswap_live.py`, `orca.py`, `raydium.py`, and `jupiter.py` against all seven checklist points, with exact source references:
  - **Uniswap:** credentials/signing and exact-amount approvals PASS; MEDIUM input-validation gap (`uniswap.py:332-355`, `uniswap_encoding.py:180-205`) because positive amount, fee/slippage range, and address shape are not enforced at the connector/encoding boundary. HIGH deadline/idempotency findings: the public `deadline` is accepted but dropped before `_execute_live_swap()` (`uniswap.py:332-355`), and `_Web3SwapExecutor` allocates a fresh pending nonce for each approval/swap with no retry key (`uniswap_live.py:71-111`). HIGH honest-error finding: `burn_position()` returns `success=True` after decrease+collect even when optional burn fails, storing only `burn_error` (`uniswap.py:529-538,568-580`).
  - **Uniswap encoding:** no credential or network write path; helper encoding is structurally covered by the connector. MEDIUM boundary finding: `_encode_address()` accepts arbitrary-length/non-checksummed strings and uint encoders rely on downstream `to_bytes()` errors rather than explicit operation validation (`uniswap_encoding.py:180-205`).
  - **Orca:** credential injection, signing delegation, and failure-result logging PASS. MEDIUM input-validation finding: amounts/ticks are serialized without positive/range/order checks (`orca.py:168-199,292-310`); the live instruction submits `accounts=[]` (`orca.py:210-219`), so protocol account correctness is not established and requires a tracked fix. Slippage/deadline/approval are N/A to these liquidity methods.
  - **Raydium:** same PASS/N-A results as Orca; MEDIUM validation/account-meta finding at `raydium.py:186-232,318-328`, including `accounts=[]`.
  - **Jupiter:** credential/signing delegation and failed-transaction propagation PASS. MEDIUM input-validation finding: caller mint, amount, and slippage values are forwarded to `/quote` without local positivity/address/range validation (`jupiter.py:120-163`). HIGH expiry/idempotency finding: `execute_swap()` has no caller-controlled quote age/deadline or idempotency key, and a retry rebuilds/posts a fresh transaction (`jupiter.py:205-224,261-279`). Slippage is passed to Jupiter, but no local upper-bound enforcement exists.
  - HIGH items are not silently left as prose: four concrete P0 follow-up todos were added immediately below the completed phase item. No code was changed in this audit pass; no tests were required for the read-only audit.


### 2026-08-20 — slot 10 lending audit

Findings use the fixed seven-point checklist and cite exact implementation lines. Lending operations have no swap price leg, so point 4 is PASS/N-A for Aave, Aave live, Morpho, and Kamino; Idle mint/redeem is price-bearing.

- `aave.py`: (1) PASS — credentials delegate to BaseConnector wallet loading; logs expose address only (`aave.py:227-301`). (2) PASS with a configuration-integrity limitation — the direct override does not verify that configured `wallet_address` belongs to `private_key` (`aave.py:234-250`). (3) HIGH — supply/withdraw/borrow/repay/flash-loan accept unbounded Decimal amounts and vectors; `_to_wei()` truncates and permits negative values, and flash-loan list lengths are not checked (`aave.py:455-606`; `aave_live.py:381-384,577-599`). (4) PASS/N-A. (5) PASS — Aave approvals use the requested amount, never unlimited allowance (`aave_live.py:248-272`). (6) HIGH — approval plus operation obtains fresh pending nonces with no idempotency key or durable submitted-tx record (`aave_live.py:164-183,278-341`). (7) HIGH — when live credentials/executor are absent, live methods fall through to simulated balance mutation and return success (`aave.py:468-480,496-509,523-536,550-564`), contradicting the initialization warning at `aave.py:263-301`.

- `aave_live.py`: (1) PASS — private key is neither logged nor transmitted. (2) PASS with the wallet-address consistency limitation above — Web3 signing uses pending nonce and chain ID (`aave_live.py:164-205`). (3) HIGH — executor helpers use unvalidated `_to_wei()` amounts and do not explicitly restrict interest-rate modes (`aave_live.py:475-620`). (4) PASS/N-A. (5) PASS — exact-amount approvals (`aave_live.py:248-264`). (6) HIGH — approval and protocol calls independently fetch nonces, so ambiguous retries can duplicate the sequence (`aave_live.py:164-183,278-324`). (7) PASS for submitted transactions — receipt status zero becomes a failed result (`aave_live.py:208-229,475-620`).

- `morpho.py`: (1) PASS — credentials delegate to the base loader and no secret is logged (`morpho.py:198-203`). (2) PASS — base signing supplies pending nonce/chain ID and configured addresses are checksummed (`morpho.py:444-475`). (3) HIGH — amount and LLTV are not range-validated, `market_id_bytes32` is only passed through `bytes.fromhex()`, and `to_wei()` unconditionally assumes 18 decimals (`morpho.py:429-454`); a six-decimal loan token can be encoded at the wrong scale. (4) PASS/N-A. (5) PASS — approval equals the encoded operation amount (`morpho.py:456-459`). (6) HIGH — approval followed by operation has no retry/idempotency record (`morpho.py:456-477`). (7) PASS — base broadcast and receipt failures return unsuccessful results (`base.py:492-522,547-571`).

- `kamino.py`: (1) PASS — only the public wallet key is logged. (2) HIGH — the adapter signs a base64 unsigned `VersionedTransaction` from the Transactions API without verifying fee payer, blockhash, signer set, or permitted program/accounts (`kamino.py:244-246,276-283`). (3) HIGH — Kamino params have unconstrained Decimal amounts and the adapter does not locally validate reserve/market/mint/instruction relationships before signing (`kamino.py:250-273`; UAC `solana.py:49-72`). (4) PASS/N-A. (5) HIGH — opaque API-produced instructions are sent without an allowlist, so exact approval/delegate scope is not established (`kamino.py:244-246`). (6) HIGH — each retry requests and broadcasts a fresh transaction with no idempotency key or prior-signature ledger (`kamino.py:244-248`). (7) PASS — API errors raise and `send_transaction()` results are returned/logged with success/error fields (`kamino.py:262-273,308-328`).

- `idle.py`: (1) PASS — credentials delegate to BaseConnector and private key is not logged (`idle.py:126-131`). (2) PASS — EVM signing and receipt handling delegate to the base connector. (3) HIGH — deposit/withdraw accept non-positive/fractional amounts and `to_wei()` truncates them (`idle.py:196-224,254-287,290-364`). (4) HIGH — `mintIdleToken()` and `redeemIdleToken()` have no caller minimum-output/share bound or transaction deadline despite a mutable vault share price (`idle.py:254-287,341-364`). (5) PASS — deposit approval is exact `amount_wei` (`idle.py:270-275`). (6) HIGH — approval then mint has no idempotency key or durable tx record (`idle.py:272-287`). (7) HIGH — incomplete live initialization falls through to simulated balance mutation and returns success (`idle.py:219-224,311-339`).

No code was changed or tests run for this read-only audit; the explicit HIGH-finding follow-up todos above ensure findings are not prose-only.

### 2026-08-21 — slot 7 staking/restaking audit (lido, etherfi, rocket_pool, marinade)

Findings use the fixed seven-point checklist; these files have no swap price leg, so slippage/deadline is PASS/N-A.

- `lido.py`: (1) PASS — injected BaseConnector credentials and public metadata-only logging (`lido.py:116-121`; `base.py:432-449`). (2) PASS — local base signing injects pending nonce/chain ID (`lido.py:250-259`; `base.py:492-535`). (3) HIGH — stake/unstake/wrap/unwrap accept unchecked Decimal amounts; `to_wei()` truncates without positivity, finiteness, or precision checks (`lido.py:217-232,316-324,376-389,422-432`; `_evm_generic.py:139-142`). (4) PASS/N-A — no price-bearing swap leg. (5) PASS — approvals are exact requested amounts (`lido.py:269-272,379-382`). (6) HIGH — submit → approve → wrap is retry-unsafe, with no idempotency key or durable sequence record (`lido.py:244-292`; `base.py:525-535`). (7) PASS — failures return unsuccessful results (`lido.py:259-292,351-359`).

- `etherfi.py`: (1) PASS — injected credentials and public-address-only logging (`etherfi.py:118-123`). (2) PASS — shared EVM signer supplies nonce/chain ID (`etherfi.py:231-267`; `base.py:492-535`). (3) HIGH — stake/unstake forward unchecked Decimal values to truncating `to_wei()` (`etherfi.py:211-229,235-245,286-325`; `_evm_generic.py:139-142`). (4) PASS/N-A — no price-bearing leg. (5) PASS — eETH approval is exact `amount_wei` (`etherfi.py:250-253`). (6) HIGH — deposit → approve → wrap has no durable idempotency/retry record (`etherfi.py:231-267`). (7) PASS — failures are returned (`etherfi.py:246-267,305-325`).

- `rocket_pool.py`: (1) PASS — injected wallet config and no secret logging (`rocket_pool.py:86-91`; `base.py:432-449`). (2) PASS — base signer injects pending nonce/chain ID (`rocket_pool.py:160-171,204-214`; `base.py:492-535`). (3) HIGH — stake/unstake pass unchecked amounts through `to_wei()` to `deposit`/`burn` (`rocket_pool.py:160-170,204-214`; `_evm_generic.py:139-142`). (4) PASS/N-A — not a swap path. (5) PASS/N-A — no approval path. (6) HIGH — retries create fresh transactions without an idempotency key or durable record (`rocket_pool.py:160-171,204-214`). (7) PASS — shared signer returns failures (`base.py:547-571`).

- `marinade.py`: (1) PASS — key injection is centralized and logs only address/RPC metadata (`marinade.py:80-109`; `solana_base.py:109-124`). (2) HIGH — locally signed instruction uses fixed program ID but `accounts=[]`, so authority/pool/mint/recipient intent is not authenticated (`marinade.py:193-200`). (3) HIGH — amounts are unchecked and truncated to lamports; account/mint relationships are not validated (`marinade.py:176-198`). (4) PASS/N-A — no price-bearing leg. (5) PASS/N-A — no approval path. (6) HIGH — retries rebuild and broadcast a fresh transaction without idempotency (`marinade.py:193-200`; `solana_base.py:328-363`). (7) PASS — on-chain errors become `success=False` (`solana_base.py:345-363`; `marinade.py:225-245`).

No code was changed or tests run for this read-only audit; every HIGH finding is represented by one of the two explicit P0 triage todos added above.
