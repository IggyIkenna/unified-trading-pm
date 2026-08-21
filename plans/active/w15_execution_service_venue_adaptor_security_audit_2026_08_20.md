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

- [x] ✅ [BACKEND] P0. Replaced the Orca/Raydium placeholder liquidity instructions with validated protocol account
      metas and explicit positive amount/tick/range bounds; the current live paths serialize caller values and submit
      `Instruction(accounts=[])` (`orca.py:168-219,292-310`; `raydium.py:186-232,318-328`). Added positive-finite
      amount/liquidity validation, ordered in-range tick validation (Orca/Raydium's shared ±443636 tick bound), and
      replaced `accounts=[]` with the SPL Token program + pool + signing-authority accounts (the parsed pool pubkey
      was previously discarded, never used). — execution-service@6a509338f9 + evidence: 10 new regression tests
      (validation errors + non-empty accounts list); QG passed twice; post-push ancestry verified.

- [ ] [BACKEND] P1. Resolve full Orca Whirlpool / Raydium CLMM account derivation for add_liquidity/remove_liquidity
      -- position PDA, position_token_account, token_vault_a/b, and tick_array_lower/upper -- which the prior todo's
      partial fix (Token program + pool + authority only, 3 of ~11 required accounts) explicitly does not resolve;
      the instruction still cannot execute on-chain without them. Needs either a vendored official Orca/Raydium
      IDL-derived SDK or an on-chain account fetch+decode (Whirlpool/pool account layout, vault addresses) this
      connector does not yet have -- do not fabricate seeds/PDAs without a verifiable source. MEDIUM finding:
      checklist points 2 and 3 (`orca.py`, `raydium.py`). (repo: execution-service)

### DeFi by primitive — lending

- [x] ✅ [BACKEND] P0. Audit the lending group: aave.py, aave_live.py, morpho.py, kamino.py, idle.py — audit-only, no code changes; findings recorded below and HIGH items tracked in triage.
      Checklist point 5 (approval scope) is the primary risk here — a lending protocol interaction commonly
      needs an approval, and an unbounded one on a compromised key is a full-balance drain, not just the
      position's notional. Done-when: same evidence bar as above.

### DeFi by primitive — staking and restaking

- [x] ✅ [BACKEND] P0. Audited the staking/restaking subset `lido.py`, `etherfi.py`, `rocket_pool.py`, and
      `marinade.py` against the fixed seven-point checklist; findings and HIGH follow-ups are recorded in the
      Progress Log and triage todos below. (repo: execution-service)

- [x] ✅ [BACKEND] P0. Audit the remaining staking/restaking group: `symbiotic.py`, `eigenlayer.py`, `karak.py`, `kelpdao.py`, `puffer.py`, `renzo.py`, `jito.py`,
      `jito_restaking.py`, `solblaze.py`. Checklist points 3 and 7 matter most here (unbonding/withdrawal request
      validation; honest reporting of a failed unstake, since a silently-swallowed unstake failure looks
      identical to "still staked" from the caller's side). Done-when: same evidence bar as above.

### DeFi by primitive — perp / CLOB on-chain

- [x] ✅ [BACKEND] P0. Audit the on-chain perp/CLOB group: `hyperliquid.py`, `_hyperliquid_schemas.py`,
      `_hyperliquid_signing.py`, `aster.py`, `pacifica.py`, `bybit.py` (the DeFi-side Bybit protocol file, not
      the CeFi CCXT adapter — confirm which is which before starting). Checklist point 2 (signing/auth) is the
      primary risk — these are the files implementing custom signature schemes rather than reusing a vetted
      library. Done-when: same evidence bar as above.

### DeFi by primitive — yield/vault aggregators

- [ ] [BACKEND] P1. Audit the yield-aggregator group: `beefy.py`, `convex.py`, `yearn.py`, `pendle.py`.
      Checklist point 5 (approval scope) and point 3 (vault-share/withdrawal input validation) matter most.
      Done-when: same evidence bar as above.

### CeFi/TradFi

- [x] ✅ [BACKEND] P0. Audit the CCXT-wrapped CeFi adapters as one group (shared library, shared risk profile —
      audit the SHARED wrapping pattern once, then spot-check 2-3 individual adapters for per-venue deviations
      rather than repeating the full checklist per file): `aster_ccxt.py`, `binance_ccxt.py`, `bybit_ccxt.py`,
      `coinbase_ccxt.py`, `deribit_ccxt.py`, `hyperliquid_ccxt.py`, `okx_ccxt.py`, `upbit_ccxt.py`. Checklist
      point 1 (credential handling) is the primary shared-code risk. Done-when: one findings record for the
      shared pattern + individual notes for any adapter that deviates from it. — execution-service@audit-only + evidence: shared-pattern review, Binance/Bybit/Upbit spot-check, exact source anchors recorded in Progress Log; no production code changed.
- [x] ✅ [BACKEND] P0. Audit the native (non-CCXT) REST adapters — HIGHER risk than the CCXT group since these
      implement request signing by hand, without a battle-tested library: `bitfinex_native.py`,
      `bitget_native.py`, `kraken_rest_adapter.py`, `kraken_rest_mapping.py`, `kraken_rest_transport.py`,
      `kraken_ws_client.py`, `_native_base.py`, `_rate_limit.py`. Checklist point 2 (signing correctness) is the
      primary risk. Done-when: same evidence bar as the CCXT group above, full per-file checklist (no
      spot-check shortcut — these are exactly the higher-risk, hand-rolled implementations). — execution-service@audit-only + evidence: exact per-file checklist record in Progress Log; no production code changed.
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

- [x] ✅ [BACKEND] P0. Triage every finding recorded across the todos above. Any CRITICAL/HIGH finding not already
      fixed inline gets a new tracked todo (this doc if genuinely bounded, or a new issue doc per
      `/codex/11-project-management/` findings-triage convention if it needs its own design pass) — never left
      as prose in a findings record with no tracked follow-up. Done-when: every CRITICAL/HIGH finding from every
      phase above resolves to either a landed fix (cite the sha) or a new tracked todo/issue-doc (cite the
      slug), zero exceptions. — unified-trading-pm@(pending) + evidence: see Progress Log entry below.

- [x] ✅ [BACKEND] P0. Add strict bridge request validation and fail-closed live credential handling (bridge.py); HIGH findings: checklist points 1, 3, and 4. — execution-service@fb50f729,116c5e2f + evidence: verified already-landed (see Progress Log 2026-08-21 slot-7 entry below); no new code required.
- [x] ✅ [BACKEND] P0. Add CCTP amount/recipient validation and reject missing source wallet credentials before approve/burn (cctp.py); HIGH finding: checklist point 3. — execution-service@fa434b66a0 + evidence: verified already-landed in fb50f729 (see Progress Log entry below); added regression test coverage, no production code change required.
- [x] ✅ [BACKEND] P0. Make CCTP transfer tracking durable and idempotent across retries; preserve source burn tx hash and prevent duplicate approve/burn submissions; HIGH finding: checklist point 6. — execution-service@f4391ac596 + evidence: see Progress Log 2026-08-21 slot-21 entry below.
- [x] ✅ [BACKEND] P0. Define and enforce caller slippage/deadline bounds for Socket bridge routes, including validation of aggregator-produced transaction targets and calldata; HIGH findings: checklist points 2 and 4. — execution-service@fb50f729,3f54ca20 + evidence: verified already-landed (see Progress Log 2026-08-21 slot-22 entry below); no new code required.
- [ ] [BACKEND] P0. Correct CCTP status lookup and enforce attestation timeout/terminal failure semantics; HIGH finding: checklist point 7.
- [ ] [BACKEND] P0. Harden Aave lending writes: reject non-positive/non-integral amounts and invalid flash-loan vectors, fail closed instead of simulating success when live credentials/executor are absent, and add durable idempotency across approval plus operation retries; HIGH findings: checklist points 3, 6, and 7 (`aave.py`, `aave_live.py`).
- [ ] [BACKEND] P0. Harden Morpho Blue writes: validate amount/LLTV/market-id inputs, use configured loan-token decimals rather than unconditional 18-decimal conversion, and add durable idempotency across approval plus operation retries; HIGH findings: checklist points 3 and 6 (`morpho.py`).
- [ ] [BACKEND] P0. Validate Kamino transaction intent before signing: enforce positive amount and address/mint relationships, inspect/allowlist fee payer, programs, accounts, and token-approval scope in API-produced transactions, and add retry idempotency; HIGH findings: checklist points 2, 3, 5, and 6 (`kamino.py`).
- [ ] [BACKEND] P0. Harden Idle vault writes: validate positive amounts, enforce caller minimum-output/deadline bounds for mint/redeem, fail closed instead of simulating success in incomplete live mode, and add durable idempotency across approval plus mint retries; HIGH findings: checklist points 3, 4, 6, and 7 (`idle.py`).
- [ ] [BACKEND] P0. Harden Lido, EtherFi, and Rocket Pool writes: validate finite positive amounts before `to_wei()`, fail closed when `is_live` lacks loaded credentials instead of entering simulation, and add durable idempotency across approval-plus-wrap sequences and retries; HIGH findings: checklist points 3 and 6 (`lido.py:217-292,316-359,376-389`; `etherfi.py:211-325`; `rocket_pool.py:160-214`).
- [ ] [BACKEND] P0. Replace Marinade's placeholder `Instruction(accounts=[])` writes with validated protocol account metas, enforce positive lamport-safe amounts, and add retry/idempotency protection around Solana broadcast; HIGH findings: checklist points 2, 3, and 6 (`marinade.py:176-202`).
- [ ] [BACKEND] P0. Validate finite/positive amounts (reject non-positive Decimal before `to_wei()`/lamport conversion) and validate operator/network/address parameters instead of accepting arbitrary caller-supplied strings, across the second staking/restaking group; HIGH finding: checklist point 3 (`symbiotic.py:141-161,243-279`; `karak.py:141-163,244-284`; `kelpdao.py:154-178,212-258`; `puffer.py:156-186,188-212,214-242`; `renzo.py:119-154,178-225`; `eigenlayer.py:88-91,379-498`; `jito.py:104-125,228-305`; `jito_restaking.py:163-185,210-273`; `solblaze.py:164-202,204-242`). (repo: execution-service)
- [ ] [BACKEND] P0. Add durable idempotency across approval-plus-deposit and withdrawal/delegate retries for the live-capable connectors in the second staking/restaking group (Solana-only Jito/Jito-Restaking/SolBlaze are simulation-only and PASS/N-A here); HIGH finding: checklist point 6 (`symbiotic.py:186-202,254-263`; `karak.py:187-190,244-284`; `kelpdao.py:194-197,212-258`; `puffer.py:196-200,214-242`; `renzo.py:119-154,178-225`; `eigenlayer.py:170-221,379-498`). (repo: execution-service)
- [ ] [BACKEND] P0. Fix fabricated-success write paths that report success without performing the on-chain action, including under `is_live=True`: Symbiotic and Karak `delegate()`; Kelp DAO's unwired withdrawal queue and `delegate()`; Puffer's unwired withdrawal queue; Renzo's unwired withdrawal queue and `delegate()`; EigenLayer's `complete_withdrawal()` and `claim_rewards()`; HIGH finding: checklist point 7 (`symbiotic.py:265-279`; `karak.py:244-284`; `kelpdao.py:212-258`; `puffer.py:214-242`; `renzo.py:178-225`; `eigenlayer.py:481-498,516-547`). (repo: execution-service)
- [ ] [BACKEND] P0. Enforce a real minimum-output bound on Kelp DAO deposits instead of the hardcoded `minRSETHAmountExpected=0`, and add minimum-output/deadline bounds plus correct instant-vs-delayed withdrawal reporting across the rest of the second staking/restaking group; HIGH finding: checklist point 4 (`kelpdao.py:201-210`); MEDIUM findings: checklist point 4 (`symbiotic.py:171-202,243-263`; `karak.py:173-203,244-268`; `puffer.py:156-186,214-242`; `renzo.py:119-154,178-225`; `jito.py:104-125,228-305`; `jito_restaking.py:210-250`; `solblaze.py:164-202,204-242`). (repo: execution-service)
- [ ] [BACKEND] P1. Add the missing ERC-20 approval before EigenLayer's `depositIntoStrategy()` and replace Karak's hardcoded low-confidence vault address with a validated/derived one; MEDIUM findings: checklist points 5 and 2 (`eigenlayer.py:200-208,379-411`; `karak.py:80-84,194-202`). (repo: execution-service)
- [ ] [BACKEND] P0. Harden the shared CCXT order boundary with explicit side/type/symbol/finite-positive amount/price validation before `create_*_order`; HIGH finding: checklist point 3 (`ccxt_common.py` plus each adapter's `_submit_ccxt_order`).
- [ ] [BACKEND] P0. Add bounded execution semantics to every CCXT adapter: require a safe market-order price/slippage guard and a finite expiry (or venue-equivalent bounded time-in-force), rather than defaulting to unbounded market execution/GTC; HIGH finding: checklist point 4 (all eight adapters' `_submit_ccxt_order` paths).
- [ ] [BACKEND] P0. Make CCXT order placement durable and retry-safe: require/persist one client-order id across ambiguous retries, use each venue's verified parameter name, and reconcile an uncertain submission before resubmitting; HIGH finding: checklist point 6 (all eight adapters, with Coinbase's `client_oid` deviation at `coinbase_ccxt.py:116-146`).
- [ ] [BACKEND] P0. Enforce fail-closed credential initialization and redacted error logging for the CCXT group; Coinbase currently constructs a real exchange without a missing-key guard (`coinbase_ccxt.py:44-52`), and all order error paths persist raw exception text (`*_ccxt.py` order handlers plus `ccxt_common.py:372-405`); HIGH/MEDIUM findings: checklist point 1.

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

### 2026-08-21 — slot 21 CCXT-wrapped CeFi adapter audit

Reviewed the shared CCXT pattern in `trade_execution/adapters/ccxt_common.py` and `BaseCLOBAdapter`, then spot-checked Binance, Bybit, and Upbit in full order-submission/error paths and compared the same anchors across Aster, Coinbase, Deribit, Hyperliquid, and OKX. The fixed seven-point checklist results are:

- **Credential handling — FINDING MEDIUM/HIGH:** no adapter hardcodes a secret or logs a literal key, and the normal wrappers pass injected credentials into CCXT (`aster_ccxt.py:65-80`, `binance_ccxt.py:53-74`, `bybit_ccxt.py:52-74`, `deribit_ccxt.py:47-74`, `okx_ccxt.py:50-74`, `upbit_ccxt.py:78-94`). Hyperliquid is the documented exception in credential shape: `api_key`/`api_secret` carry wallet address/private key and are passed to CCXT's local EIP-712 signer (`hyperliquid_ccxt.py:49-76`), not sent as API-key auth. Coinbase omits the real-mode missing-credential guard and constructs CCXT with possibly-`None` credentials (`coinbase_ccxt.py:44-52`). All adapters also interpolate raw CCXT exception text into logger/event payloads (for example `binance_ccxt.py:173-192`, `bybit_ccxt.py:187-205`, `upbit_ccxt.py:203-222`; shared `ccxt_common.py:372-405`), with no redaction guarantee. No direct secret exposure was observed in the inspected success logs.
- **Signing/auth correctness — PASS with boundary limitation:** HMAC/API-key signing is delegated to CCXT for the seven API-key wrappers; Hyperliquid delegates EIP-712 wallet signing to CCXT. The adapters do not construct signatures, transmit private keys in request bodies/URLs, or add replayable hand-rolled nonces. The credential-source and wallet-address/private-key consistency checks remain caller/configuration responsibilities, not enforced by this wrapper.
- **Input validation before order write — FINDING HIGH:** all eight live paths cast caller `side`/`order_type` and convert caller `quantity`/`price` directly to `float` before `create_market_order`/`create_limit_order`, without local finite-positive amount/price checks, side/type allowlists, or strict instrument-symbol validation. Representative evidence: `binance_ccxt.py:85-109`, `bybit_ccxt.py:83-125`, `upbit_ccxt.py:109-137`; the same pattern is present in Aster, Coinbase, Deribit, Hyperliquid, and OKX. Exchange-side validation is not a substitute for the required pre-write adapter boundary.
- **Slippage/deadline bounds — FINDING HIGH:** market-order paths have no caller slippage/price protection, and the public default is `GTC` with no finite expiry. Limit-order paths can carry a venue time-in-force in most wrappers, but that does not protect market orders and does not create a safe default. Coinbase does not pass `time_in_force` at all (`coinbase_ccxt.py:116-146`), and Upbit's live path drops it (`upbit_ccxt.py:224-239`). These are CLOB orders rather than swaps, so token-approval/slippage semantics differ, but an unbounded market execution and unbounded order lifetime remain concrete bounds gaps.
- **Approval scope — PASS/N-A:** these are CCXT CLOB/API order paths; no ERC-20/SPL approval or allowance call is made by the eight adapters.
- **Idempotency/retry safety — FINDING HIGH:** client-order IDs are optional, not required or durably persisted, so an ambiguous network result can be retried as a new order. Most wrappers map a supplied ID into a venue parameter (`newClientOrderId`, `orderLinkId`, or `clientOrderId`), but that is only caller-provided best effort and there is no uncertain-submit reconciliation ledger. Coinbase uses `client_oid` (`coinbase_ccxt.py:116-120`), which is a venue-specific deviation requiring verification, and `ccxt_order_to_canonical()` generates a UUID only after a response (`ccxt_common.py:43-80`), too late to make submission idempotent.
- **Honest error handling — PASS with a logging limitation:** successful placement is emitted only after a validated CCXT response, and known placement/cancel/fill failures emit failure events and re-raise in the inspected adapters (`binance_ccxt.py:169-192`, `bybit_ccxt.py:171-205`, `upbit_ccxt.py:188-222`). `OrderNotFound` during fill lookup is intentionally returned as an empty fill set, not a successful order result; callers must not interpret it as confirmation of execution. Raw exception persistence is covered under the credential/logging finding above.

No production code or tests were changed for this audit-only unit. The four concrete HIGH findings (pre-write validation, execution bounds, idempotency/retry safety, and Coinbase's credential fail-closed deviation where applicable) are represented by explicit P0 triage todos above; the audit phase is complete.

No code was changed or tests run for this read-only audit; every HIGH finding is represented by one of the two explicit P0 triage todos added above.

### 2026-08-21 — slot 13 staking/restaking audit (remaining group)

Findings use the fixed seven-point checklist and exact implementation lines. EVM connectors delegate signing and credential loading to `BaseConnector`; Solana connectors explicitly declare simulation-only writes (`supports_live=False`).

- `symbiotic.py`: (1) PASS — centralized credentials and public metadata logging (`symbiotic.py:99-104`; `base.py:432-449`). (2) PASS — shared signer/checksummed calls (`symbiotic.py:193-201,254-262`). (3) HIGH — deposit/withdraw pass unchecked Decimal values through `to_wei()`, and delegate accepts an arbitrary network string (`symbiotic.py:141-161,243-279`; `_evm_generic.py:139-142`). (4) MEDIUM — no minimum output/share bound or deadline (`symbiotic.py:171-202,243-263`). (5) PASS — exact approval amount (`symbiotic.py:186-189`). (6) HIGH — approval+deposit and withdrawal retries have no idempotency key or durable submitted-tx record (`symbiotic.py:186-202,254-263`; `base.py:525-535`). (7) HIGH — delegate returns success without submitting a transaction, including in live mode (`symbiotic.py:265-279`); deposit/withdraw receipt failures otherwise surface.

- `karak.py`: (1) PASS — centralized wallet loading; no secret logging. (2) MEDIUM — shared signer is correct, but the live vault is an explicitly low-confidence hardcoded derived address with no runtime code/chain validation (`karak.py:80-84,194-202`). (3) HIGH — deposit/redeem amounts are unchecked and delegate accepts an arbitrary operator address (`karak.py:141-163,244-284`). (4) MEDIUM — no minimum output/share bound or deadline (`karak.py:173-203,244-268`). (5) PASS — exact approval (`karak.py:187-190`). (6) HIGH — approval+deposit and redeem have no retry/idempotency record. (7) HIGH — delegate reports success without on-chain delegation; deposit/redeem failures are returned by the shared helper.

- `kelpdao.py`: (1) PASS — credentials use the base loader; no secret is logged (`kelpdao.py:96-103`). (2) PASS — shared signing and checksummed token/pool calls (`kelpdao.py:194-210`). (3) HIGH — only token membership is validated; amount is not finite/positive, withdrawal accepts arbitrary/negative rsETH, and delegation accepts an unvalidated operator string (`kelpdao.py:154-178,212-258`). (4) HIGH — `depositAsset()` hardcodes `minRSETHAmountExpected=0, removing the output floor (`kelpdao.py:201-210`). (5) PASS — exact approval (`kelpdao.py:194-197`). (6) HIGH — approval then deposit has no idempotency key or durable retry record. (7) HIGH — unwired withdrawal queue still returns success and mutates balances; delegate likewise returns success without a transaction.

- `puffer.py`: (1) PASS — centralized wallet loading and metadata-only logging. (2) PASS — shared signer/checksummed ERC-4626 call (`puffer.py:188-212`). (3) HIGH — live deposit and simulation withdrawal accept unchecked amounts, including values truncated by `to_wei()` (`puffer.py:156-186,188-212,214-242`). (4) MEDIUM — no minimum pufETH output bound or deadline. (5) PASS — exact WETH approval (`puffer.py:196-200`). (6) HIGH — approval+deposit retries can duplicate the sequence. (7) HIGH — unwired withdrawal queue returns success and credits WETH, including for a live-capable connector (`puffer.py:214-242`).

- `renzo.py`: (1) PASS — base credential loading and no private-key logging. (2) PASS — shared nonce/chain-ID signing and fixed RestakeManager target (`renzo.py:156-176`). (3) HIGH — live deposit and simulation withdrawal accept unchecked amounts; delegate accepts an arbitrary operator address (`renzo.py:119-154,178-225`). (4) MEDIUM — `depositETH()` has no minimum ezETH output bound or deadline. (5) PASS/N-A — no ERC-20 approval path for ETH-only operation. (6) HIGH — retries create fresh deposit transactions with no idempotency key or durable record. (7) HIGH — unwired withdrawal queue returns success and credits WETH; delegate returns success without a transaction.

- `eigenlayer.py`: (1) PASS — private key is held by the executor and not logged (`eigenlayer.py:312-341`). (2) PASS — pending nonce, chain ID, and receipt status checks (`eigenlayer.py:170-221`). (3) HIGH — `_to_wei()` permits non-positive/fractional values; queue/completion do not validate positive shares or a matching pending request (`eigenlayer.py:88-91,379-498`). (4) PASS/N-A — direct restaking has no price-bearing swap leg. (5) MEDIUM — no approval is performed before `depositIntoStrategy()`, leaving allowance/scope unenforced (`eigenlayer.py:200-208,379-411`). (6) HIGH — retries resubmit with fresh pending nonces and no idempotency key or durable tx/root record. (7) HIGH — `complete_withdrawal()` and `claim_rewards()` always simulate success, including in live mode (`eigenlayer.py:481-498,516-547`).

- `jito.py`: (1), (2), and (5) PASS/N-A — simulation-only, no live credentials/signing/approval (`jito.py:24-51,141-151`). (3) HIGH — stake/unstake accept non-positive amounts and the fetched ratio is not constrained positive (`jito.py:104-125,228-305`). (4) MEDIUM — no minimum-output bound in the simulated conversion. (6) PASS/N-A because no transaction is submitted. (7) PASS with limitation — simulation-only status is documented and BaseConnector blocks `is_live=True`; this is not a swallowed live failure.

- `jito_restaking.py`: (1), (2), and (5) PASS/N-A — simulation-only, no live credential/signing/approval (`jito_restaking.py:19-33,77-103`). (3) HIGH — deposit accepts any token/non-positive amount; withdraw accepts non-positive VRT; delegate accepts an arbitrary operator key (`jito_restaking.py:163-185,210-273`). (4) MEDIUM — no minimum-output bound and withdrawal hardcodes delay zero despite documented possible cooling (`jito_restaking.py:210-250`). (6) PASS/N-A for on-chain retry safety. (7) PASS with simulation-only limitation, but unvalidated inputs and repeated full-balance delegation can misstate simulated state.

- `solblaze.py`: (1), (2), and (5) PASS/N-A — simulation-only, no live credential/signing/approval (`solblaze.py:21-33,73-97`). (3) HIGH — stake/unstake accept non-positive amounts and mutate state without balance/range validation (`solblaze.py:164-202,204-242`). (4) MEDIUM — no minimum-output bound and always reports instant withdrawal despite the documented epoch-delayed route. (6) PASS/N-A for on-chain retry safety. (7) PASS with simulation-only limitation; construction with `is_live=True` is rejected by the base contract.

No code was changed or tests run for this read-only audit. The HIGH findings require the existing triage phase to add explicit fixes/todos before W15 close-out.
- [ ] [BACKEND] P0. Harden perp/CLOB order boundaries across Hyperliquid, Aster, Pacifica, and the DeFi-side Bybit wrapper: reject non-finite/non-positive size and price, reject unknown side/order-type values, and preserve the underlying adapter's validation before any live submission; HIGH finding: checklist point 3 (hyperliquid.py:370-402,504-516; aster.py:394-427; pacifica.py:489-515; bybit.py:105-132).
- [ ] [BACKEND] P0. Define caller-controlled slippage and expiry/deadline bounds for market and resting perp orders; remove the implicit Hyperliquid 5% IOC buffer and make Aster/Pacifica/Bybit market semantics explicit and bounded; HIGH finding: checklist point 4 (hyperliquid.py:381-391; aster.py:394-427; pacifica.py:489-515; bybit.py:105-132).
- [ ] [BACKEND] P0. Add durable idempotency/client-order IDs and ambiguous-outcome recovery for the perp/CLOB order paths; thread client_order_id through the Bybit wrapper into BybitCCXTAdapter, and prevent duplicate retries for Hyperliquid nonce-based, Aster timestamp-based, and Pacifica timestamp/expiry-based submissions; HIGH finding: checklist point 6 (hyperliquid.py:504-546; aster.py:479-519; pacifica.py:559-655; bybit.py:105-132).
- [ ] [BACKEND] P0. Make Bybit position/balance read failures observable instead of returning empty positions or zero balance, while preserving the already honest failed-order result; MEDIUM finding related to checklist point 7 (bybit.py:136-176).
- [ ] [BACKEND] P0. Confirm Pacifica's future live enablement retains the current fail-closed boundary (supports_live=False) and validates the configured Solana keypair/account relationship before changing that flag; HIGH-risk signing/auth guardrail (pacifica.py:31-48,286-328,610-645).

- [ ] [BACKEND] P0. Add a process/key-scoped monotonic nonce allocator for Bitfinex, Bitget, and Kraken native
      signing, including concurrency protection and reuse across adapter instances; HIGH finding: checklist point 2
      (bitfinex_native.py:179-199, bitget_native.py:145-166, kraken_rest_transport.py:308-310,
      _native_base.py:75-82).
- [ ] [BACKEND] P0. Enforce finite-positive quantity/price, strict side/order-type/symbol, and bounded
      market-order expiry/slippage semantics at every native order and amend boundary; HIGH findings: checklist
      points 3 and 4 (bitfinex_native.py:337-365, bitget_native.py:274-315,
      kraken_rest_adapter.py:230-344,437-472, kraken_futures_orders.py:49-123,163-177).
- [ ] [BACKEND] P0. Preserve one client-order id across native submissions and reconcile ambiguous responses before
      retrying; do not discard invalid/missing IDs or allow a fresh retry to double-place an order; HIGH finding:
      checklist point 6 (bitfinex_native.py:337-368, bitget_native.py:274-318,
      kraken_rest_adapter.py:293-476, kraken_futures_orders.py:49-143).
- [ ] [BACKEND] P0. Make Kraken Spot/Futures response-envelope parsing fail closed and require a validated order
      result before constructing NEW/CANCELLED/AMENDED success results; malformed or empty payloads must be reported
      as failures, not interpreted as success; HIGH finding: checklist point 7
      (kraken_rest_transport.py:107-130,177-199, kraken_rest_adapter.py:344-362,390-412,472-476,
      kraken_futures_orders.py:123-143).
- [ ] [BACKEND] P1. Remove credential-derived key prefixes from native rate-limit identity/error text, replace
      blocking sleeps in async adapter paths with a non-blocking mechanism, and surface callback failures through
      stream health state; MEDIUM findings (_rate_limit.py:91-92,136-138,185-205,
      _native_base.py:90-105, kraken_ws_client.py:474-485,687-697).

### 2026-08-21 — slot 25 perp/CLOB audit

Findings use the fixed seven-point checklist and exact implementation lines.

- Hyperliquid signing and UAC schema boundaries PASS (`_hyperliquid_signing.py:32-108`; `hyperliquid.py:504-546`); HIGH input-validation gap and permissive side mapping (`hyperliquid.py:370-402,504-516`), fixed 5% IOC buffer with no caller deadline/slippage (`hyperliquid.py:381-391`), and no durable idempotency/client-order key (`hyperliquid.py:504-546`).
- Aster HMAC credentials/signing PASS (`aster.py:249-278`); HIGH unchecked quantity/price/side (`aster.py:394-427`), no slippage/deadline contract, and no client-order idempotency across fresh timestamped submissions (`aster.py:479-519`).
- Pacifica remains fail-closed (`supports_live=False`) and its Ed25519 scaffold does not post private material (`pacifica.py:166-211,286-328,559-645`); HIGH future-live input, expiry, and replay/idempotency gaps (`pacifica.py:489-515,559-655`).
- Bybit delegates credential/signing correctness and returns failed write results, but has HIGH unchecked wrapper inputs and drops the delegated `client_order_id` (`bybit.py:105-132`; `bybit_ccxt.py:208-226`); MEDIUM read failures become empty positions/zero balance (`bybit.py:136-176`).

### 2026-08-21 — slot 4 native REST adapter audit

Reviewed every file named by the native-adapter phase against all seven checklist points; no production code or tests were changed.

- `bitfinex_native.py`: (1) PASS at the adapter boundary — credentials are injected, required before private calls, and not logged; the implementation remains `BLOCKED-CREDENTIALS`/HTTP-client scaffolding. (2) HIGH — HMAC-SHA384 construction is structurally correct, but `_make_nonce()` uses instance-local mutable state without a lock or process/key allocator (`:179-199`), so concurrent adapters/calls can reuse or regress a nonce. (3) HIGH — `place_order()` forwards unchecked quantity, price, side, order type, and symbol; non-BUY sides become sells, and non-numeric client IDs are silently converted to `None` (`:337-365`). (4) HIGH — market orders have no caller slippage/price guard or finite expiry and the default is unbounded GTC (`:337-365`). (5) PASS/N-A — no approval path. (6) HIGH — client IDs are optional and non-numeric IDs are discarded; no ambiguous-submit reconciliation or durable retry record exists (`:361-368`). (7) PASS for the current fail-closed scaffold — it raises `NotImplementedError`; no live response is treated as success.
- `bitget_native.py`: (1) PASS — injected key/secret/passphrase are required and not logged. (2) HIGH — HMAC-SHA256/timestamp header construction is structurally correct, but `make_ms_nonce()` is wall-clock-only and has no monotonic/concurrency allocator (`:145-166`). (3) HIGH — `place_order()` forwards unchecked quantity, price, side, order type, symbol, and time-in-force (`:274-315`). (4) HIGH — market orders have no slippage/price protection or finite expiry and the default permits unbounded GTC (`:274-315`). (5) PASS/N-A — no approval path. (6) HIGH — `clientOid` is optional and no durable idempotency/reconciliation exists across an ambiguous response (`:312-318`). (7) PASS for the current fail-closed scaffold — the missing HTTP client raises rather than fabricating a result.
- `kraken_rest_adapter.py`: (1) PASS — private credentials are required at each boundary and no secret is logged (`:164-193`, transport `:279-295`). (2) HIGH — Spot and Futures signing functions use their documented schemes, but `_make_nonce()` is raw microsecond wall-clock time with no monotonic allocator and is shared across concurrent Spot/Futures calls only by unsynchronized instance state (`kraken_rest_transport.py:308-310`). (3) HIGH — Spot/Futures order and amend boundaries do not enforce finite-positive quantities/prices, strict side/type/pair values, or valid amend ranges (`kraken_rest_adapter.py:230-344,437-472`; `kraken_futures_orders.py:49-123,163-177`). (4) HIGH — market/GTC defaults have no caller slippage/price guard or finite expiry (`:293-344`). (5) PASS/N-A — no token-approval path. (6) HIGH — client IDs are optional and no durable uncertain-submit reconciliation exists. (7) HIGH — `place_order`, `cancel_order`, and `amend_order` construct NEW/CANCELLED results after transport returns an empty/malformed result; Futures can likewise fall through to a client ID/empty ID (`kraken_rest_transport.py:107-130,177-197`; `kraken_rest_adapter.py:344-362,390-412,472-476`; `kraken_futures_orders.py:123-143`).
- `kraken_rest_mapping.py`: (1) PASS/N-A — pure mapping/signing helpers do not handle or log credentials. (2) PASS with the nonce limitation owned by transport — Spot HMAC-SHA512 and Futures hash/HMAC-SHA512 message construction matches the documented path/body ordering (`:260-336`); no private key is transmitted in a body/URL. (3) PASS/N-A — parsing/mapping only, no write boundary. (4) PASS/N-A — no order submission. (5) PASS/N-A — no approval path. (6) PASS/N-A — no submission/retry state. (7) PASS — malformed order fields are parsed conservatively rather than reported as a network submission success; transport envelope validation remains a separate HIGH finding.
- `kraken_rest_transport.py`: (1) PASS — credentials are required and headers contain the API key/signature only; secrets are not logged (`:137-167,204-239,279-295`). (2) HIGH — both documented signing paths are used, but `_make_nonce()` is unsynchronized and not monotonic across concurrent calls/adapters (`:308-310`). (3) PASS/N-A — transport does not own order-field validation; callers currently omit it. (4) PASS/N-A — transport does not define execution bounds. (5) PASS/N-A — no approval path. (6) HIGH — no retry/idempotency or uncertain-submit reconciliation exists. (7) HIGH — `_extract_kraken_result()` returns `{}` for non-dict/missing/wrong-shaped results, and `_extract_kraken_futures_result()` accepts any non-`error` envelope; callers can interpret malformed responses as success (`:119-130,177-199`).
- `kraken_ws_client.py`: (1) PASS — public WS has no credentials; private token is supplied per reconnect and is not logged (`:356-454`). (2) PASS/N-A — public stream has no signing; private stream delegates authentication to the supplied expiring token. (3) PASS/N-A — read-only feed parser, no write boundary. (4) PASS/N-A — no trade submission. (5) PASS/N-A — no approval path. (6) PASS/N-A — reconnects re-subscribe but do not submit orders. (7) MEDIUM — downstream execution/ticker/book callback exceptions are caught, logged, and then discarded, with no failure signal or health-state transition (`:474-485`, analogous handlers `:279-280,687-697`), so consumers can believe the stream is being processed when callbacks are failing.
- `_native_base.py`: (1) PASS — credential checks do not log values; error events contain venue/code/message but no key/secret. (2) MEDIUM — nonce helpers are raw wall-clock generators with no monotonic or process/key-scoped coordination (`:75-82`); signing primitives themselves correctly use HMAC and do not transmit secrets. (3) PASS/N-A — shared helpers do not submit orders. (4) PASS/N-A — no execution-boundary semantics. (5) PASS/N-A — no approval path. (6) MEDIUM — shared helpers provide no idempotency/reconciliation primitive for the adapters. (7) PASS — HTTP classification always raises a canonical error rather than silently succeeding (`:154-200`). Additional MEDIUM support finding: `enforce_rate_limit()` calls blocking `time.sleep()` and is invoked from async adapter methods (`:90-105`).
- `_rate_limit.py`: (1) MEDIUM — the registry and timeout message retain/expose the first eight characters of the API key (`:91-92,136-138,185-205`); this is credential material and should not be logged or used as a persisted identity without an explicit redaction/hash contract. (2) PASS/N-A — no signing. (3) PASS/N-A — no write boundary. (4) PASS/N-A — no execution semantics. (5) PASS/N-A — no approval path. (6) MEDIUM — the documented multi-VM file-lock/token-counter protection is not implemented by the actual `get_bucket()`/`VenueRateLimitBucket` API; only an in-process token bucket exists (`:1-21,83-205`), so cross-process retries/rate limits are not protected. (7) PASS — rate-limit timeout raises rather than reporting a request as successful.

The HIGH findings are represented by the native validation/bounds, replay-safe nonce, and idempotency/envelope triage todos above; the MEDIUM support findings are represented by the native observability/rate-limit todo. No code changes or tests were required for this read-only audit.

### ag-closeout-audit 2026-08-21 (cross-cutting tranche, Phase 2 sweep)

Mechanical hygiene fix: this doc had two top-level `## Progress Log` H2 headers (a concurrent-editing artifact —
the bridge/CCTP entry and the swap/DEX entry had each been appended under their own header instead of sharing
one). Removed the duplicate header so every dated entry lives under a single `## Progress Log` section; no entry
content, findings, or todos were changed.

### 2026-08-21 — slot 24 findings triage sweep

Cross-checked every completed audit phase's Progress Log entry against the Triage-section todo list (a per-file citation search over every `- [ ]`/`- [x]` todo line, verified with a script, not eyeballed) to confirm every CRITICAL/HIGH finding resolves to a landed fix or a tracked follow-up todo, per this todo's done-when.

- **Gap found and closed:** the slot-13 second staking/restaking audit (`symbiotic.py`, `karak.py`, `kelpdao.py`, `puffer.py`, `renzo.py`, `eigenlayer.py`, `jito.py`, `jito_restaking.py`, `solblaze.py`) recorded multiple HIGH findings but had zero corresponding triage todos — the only place those nine filenames appeared was the completed audit-phase todo itself, not any fix todo. Added five new triage todos immediately after the Marinade todo, grouped by checklist point across the group: input validation (point 3), idempotency for the live-capable connectors (point 6), fabricated-success/honest-error-handling violations on unwired withdrawal-queue and `delegate()` paths (point 7), output-bound/deadline gaps including Kelp DAO's hardcoded `minRSETHAmountExpected=0` (point 4, P0), and the two remaining MEDIUM one-offs — EigenLayer's missing pre-deposit approval and Karak's hardcoded vault address (points 5 and 2, P1).
- **No other gap found.** Bridge/CCTP, swap/DEX (Jupiter/Orca/Raydium tracked via already-open DeFi-swap-section todos; Uniswap's HIGH findings already landed inline via two done todos with SHAs), lending, first staking group (Lido/EtherFi/RocketPool/Marinade), CCXT CeFi, native REST, and perp/CLOB all already had every HIGH finding covered by an existing todo — confirmed by the same per-file citation check. No CRITICAL-severity finding was ever recorded anywhere in this doc (grepped for the literal string; only the checklist definition and this triage todo's own text use it).
- **Cleanup:** removed a duplicate set of 4 native-REST-adapter triage todos (an earlier, less-precise pass had been appended twice — once generically, once with the slot-4 audit's own more exact `kraken_futures_orders.py` line citations) to avoid the backlog regen dispatching two near-identical fix tasks for the same findings.

No production code was changed — this is a triage-only pass per the todo's own scope; the five new todos and the duplicate removal are the deliverable.

### 2026-08-21 — slot 7 bridge.py triage-todo verification (checklist points 1, 3, 4)

Re-read `execution_service/defi_execution/protocols/bridge.py` at current LDR HEAD against the specific "Add strict
bridge request validation and fail-closed live credential handling" triage todo. The fix was already landed —
between the slot-5 audit (2026-08-20) and now, slot-10/15's commits `ef899bf5` (request reservation boundary) and
`fb50f729` (bridge transfer security state) introduced `_validate_request()` (finite/positive amount, max-amount
cap, `max_slippage_bps` range check, near-future `deadline` check, `_EVM_ADDRESS_RE` recipient validation,
`WELL_KNOWN_TOKENS` chain/token allowlist), replaced the silent-fallback `_resolve_token_address()` with one that
raises `ValueError` for any unlisted symbol/chain, and added `_validate_aggregator_target()` (Socket-returned
`txTarget`/`allowanceTarget` must be in `config["allowed_aggregator_targets"]`) plus a `_HEX_DATA_RE`/length check on
returned calldata. Commit `116c5e2f` (2026-08-20, predates the slot-5 audit read) had already removed the
`socket_api_key` prefix logging — grepped every `_api_key` reference in the current file; it is used only as the
`API-KEY` HTTP header, never logged. Fail-closed live-credential handling is present: `_prepare_bridge()` raises when
`is_live` and no durable `_state_store` is configured; `_route_and_execute()` raises when `is_live` and
`not self.has_signing_capability` — neither path falls through to simulated success. All three checklist points (1
credential handling, 3 input validation, 4 slippage/deadline bounds) verified against the live file content, not
assumed from the commit subject lines. No new code was needed; the todo checkbox above is flipped citing the two
substantive fix SHAs.

### 2026-08-21 — slot 5 CCTP triage-todo verification (checklist point 3)

Re-read `execution_service/defi_execution/protocols/cctp.py` at current LDR HEAD against the "Add CCTP
amount/recipient validation and reject missing source wallet credentials before approve/burn" triage todo. The fix
was already landed — the same slot-15 commit `fb50f729` (2026-08-20, "persist bridge transfer security state") that
fixed `bridge.py` also rewrote CCTP's `_validate_bridge_request()`: it now rejects non-finite/non-positive/
over-`max_bridge_amount` amounts, rejects amounts with more than 6 decimal places, validates `recipient` via
`_is_evm_address()` before it ever reaches `_address_to_bytes32()` (which itself now validates before `zfill()`
instead of accepting malformed/short hex), and raises `"CCTP source wallet credentials are required; refusing to
burn"` when `_wallet_address`/`_private_key`/`_web3_instance` is `None` — all four checks run at the top of
`bridge()`, before `_approve_and_burn()` ever touches the wallet. The MEDIUM credential-handling finding from the
original audit (`self._wallet_address or recipient` letting a destination address silently stand in for a missing
source wallet) is also gone — `bridge()` now asserts `self._wallet_address is not None` and passes it directly.

No regression test previously covered this guard, so this unit added six tests to
`tests/unit/defi_execution/test_cctp.py` (`TestCCTPBridgeValidation`) exercising zero/negative amount, over-max
amount, over-precision amount, invalid recipient, and missing source-wallet-credentials — each asserting the
specific `ValueError` message from `_validate_bridge_request()`. Quality gates green (execution-service, 178s full
run); shipped via quickmerge — execution-service@fa434b66a0.

**Unrelated finding surfaced and fixed in the same unit (not part of this todo's scope, but actively blocking it):**
this slot's `unified-trading-pm` worktree carried ~50 files of pre-existing, unattributed uncommitted/staged changes
at session start (a large apparent partial revert — unchecked checkboxes and removed Progress Log entries versus
LDR HEAD on several plan/issue docs, plus a staged addition to
`scripts/quality_gates/adapter_contract_baseline.yaml` of two baseline entries for `unified-trading-system-ui`
files that do not exist in this slot's UI checkout). The baseline addition caused execution-service's own
`quality-gates.sh` STEP 5.83 (adapter contract-call regression ratchet) to fail with an unrelated
`file missing or renamed` error. Restored (`git restore --staged --worktree`) only the two files this unit
directly needed clean — this plan doc and the baseline YAML — back to HEAD; did **not** touch or investigate the
remaining ~48 dirty files (out of this todo's scope; whoever owns that WIP should resolve it, since committing it
as-is would silently delete other slots' already-landed audit checkboxes/Progress Log entries). Separately, the
index also carried literal unresolved `git stash pop` conflict markers ("Updated upstream" vs "Stashed changes",
no active `MERGE_HEAD`/rebase state) on three unrelated files
(`plans/active/issues/ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21.md`,
`plans/active/sports_taxonomy_p2_migration_2026_08_08_finalize.md`,
`plans/active/walkthrough_feedback_remediation_2026_08_21.md`), which made git refuse **every** commit in this repo
regardless of which files were staged. Resolved with `git checkout --ours` (kept the already-committed HEAD side;
the stash itself is untouched — `git stash list` still has 95 entries, none dropped — so the discarded
"Stashed changes" side remains recoverable from the stash if it had any value). This repo's `unified-trading-pm`
worktree needs a dedicated cleanup pass; flagging rather than attempting it here.

### 2026-08-21 — slot 14 Orca/Raydium liquidity-instruction fix

Fixed the "Replace the Orca/Raydium placeholder liquidity instructions..." P0 todo. `add_liquidity`/
`remove_liquidity` in both `orca.py` and `raydium.py` now reject a non-finite/non-positive `amount_a`/`amount_b`/
`liquidity_amount` and an inverted or out-of-range `lower_tick`/`upper_tick` (validated against ±443636, the shared
Orca Whirlpool / Raydium CLMM tick-index bound per each protocol's public on-chain `tick_math.rs`, confirmed via web
search against `orca-so/whirlpools` and `raydium-io/raydium-clmm` before hardcoding) before any instruction is
built — closing checklist points 3/4 completely.

For checklist point 2 (account correctness): the live `_submit_whirlpool_ix`/`_submit_clmm_ix` helpers now populate
the accounts resolvable from inputs already available to these two methods — the SPL Token program, the pool
account itself (previously parsed into a discarded, unused `_pool_pubkey`), and the signing authority. **This is a
partial fix, stated explicitly rather than claimed as complete**: the real Whirlpool increase/decrease_liquidity and
Raydium CLMM add/remove_liquidity instructions need roughly 11 accounts including a per-position PDA,
`position_token_account`, both token vaults, and the lower/upper tick-array PDAs — none of which this method's
current signature has the data to derive (no position identity, no vault addresses, no tick_spacing in scope), and
fabricating unverifiable seeds/PDAs for a real on-chain program would be worse than the honest partial state. A new
P1 follow-up todo captures this remaining scope precisely rather than leaving it implied by a checked-off box.

10 new regression tests added to `tests/defi_execution/unit/test_solana_connectors.py` (5 per connector: reject
non-positive amount, reject inverted tick range, reject out-of-range tick, reject non-positive remove-liquidity
amount, and a live-path regression proving `accounts` is no longer `[]`); the shared Solana SDK mock in that file
needed a new `AccountMeta` mock alongside its existing `Instruction` mock, or every test in the file would have
failed to import. QG passed twice (187s pre-commit, 412s post-commit, both green); shipped —
execution-service@6a509338f9 (post-push ancestry independently verified).

### 2026-08-21 — slot 22 Socket bridge slippage/deadline/aggregator-target triage

Re-checked the triage todo "Define and enforce caller slippage/deadline bounds for Socket bridge routes, including
validation of aggregator-produced transaction targets and calldata" (checklist points 2 and 4) against the live
`bridge.py` on `origin/live-defi-rollout` (slot clean, ahead=0, behind=0) before writing any new code, per the
findings-triage convention. Both HIGH findings recorded in the 2026-08-20 slot-5 bridge/CCTP entry above are already
closed by commit `fb50f7296` ("fix(defi): persist bridge transfer security state", 2026-08-20, slot-15), refined for
line-length by `8b87a17a`/`3f54ca20` with no logic change (diffed to confirm):

- **Checklist point 2** (the original finding: `_execute_bridge_tx()` signed aggregator-supplied `txTarget`/`txData`
  with no validation): `_execute_bridge_tx()` now calls `_validate_aggregator_target()` on the resolved `txTarget`
  before signing (`bridge.py:703-705`), and again on `approvalData.allowanceTarget` in `_approve_if_needed()`
  (`bridge.py:725-726`) — both reject anything not on the EVM-address-shaped, config-driven
  `allowed_aggregator_targets` allowlist (`bridge.py:788-796`). Calldata is validated as well-formed hex and capped
  at 512002 chars before broadcast (`bridge.py:706-707`).
- **Checklist point 4** (the original finding: quote/build requests had no caller slippage bound or deadline):
  `bridge()`/`_validate_request()` now accept and range-check `max_slippage_bps` (0-1000) and `deadline` (must be a
  near-future timestamp bounded by `max_bridge_deadline_seconds`) (`bridge.py:607-624`); `_resolve_best_route()`
  computes the caller's minimum acceptable output from `max_slippage_bps` and raises before broadcasting if the
  Socket quote falls short (`bridge.py:649-652`); `deadline` is threaded into the `/build-tx` request
  (`bridge.py:780-781`).
- Test coverage exists in `tests/integration/test_bridge_e2e.py` and `tests/unit/test_live_bridge_adapter.py`
  (grepped, not just assumed).

No production code was changed for this todo — the fix was already shipped, just not yet cited against this specific
triage line. Flipped the checkbox above citing `fb50f7296`/`3f54ca20` as evidence.

**Unrelated finding fixed in the same session**: this repo's `plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md`
was found with a dangerous staged revert in the index (working tree matched a stale, pre-completion snapshot of this
same file — missing the landed Orca/Raydium checkbox, the Triage checkbox, the bridge/CCTP checkboxes, and two later
Progress Log entries, none of which this session authored). Restored via `git restore --staged --worktree` to match
`origin/live-defi-rollout` HEAD before making any edit, per the "never delete another agent's already-landed content"
rule — no content was lost since HEAD already had the correct state and nothing had been committed from the stale
index.

### 2026-08-21 — slot 21 CCTP idempotency fix (checklist point 6)

Re-read `cctp.py` at current LDR HEAD against the 2026-08-20 slot-5 audit's point-6 finding ("`uuid4()` is generated
for every call ... `_pending_burns` is process-local and retries repeat approval/burn"). A prior commit (`fb50f729`,
already cited against the point-3 triage todo above) had since replaced the random UUID with a deterministic
`uuid5(request_key)` and added a durable `_state_store`-backed idempotency check (`_existing_burn_as_record()`) —
partial progress, but a real gap remained: `_approve_and_burn()` only persisted the burn record *after*
`_extract_message_from_receipt()` succeeded. Any failure in that separate, fallible extraction step (a fresh
`wait_for_transaction_receipt()` call) — including a process crash — left an already-confirmed on-chain burn with no
durable trace, so a retry's idempotency check found nothing and re-ran the full approve+burn, double-burning the
caller's USDC for one logical transfer request.

Fix: `_approve_and_burn()` now persists a `_CCTPBurnRecord` (with `source_tx_hash`/`approve_tx_hash` set, empty
`message_bytes`/`message_hash`) immediately once the burn transaction confirms, *before* attempting message-log
extraction. Added `_recover_message()`, called from `_existing_burn_as_record()` whenever a found record has a
`source_tx_hash` but no `message_hash` — it retries the read-only extraction (safe to repeat, unlike the burn itself)
instead of falling through to a fresh `_approve_and_burn()`. Split the now-oversized `_approve_and_burn()` into a
second helper (`_send_approve_and_burn_txs()`) to stay under the 50-line method cap.

Added 3 regression tests to `test_cctp.py` (`TestCCTPBridgeIdempotency`): a same-connector retry never re-submits
approve/burn; a message-extraction failure preserves the burn tx hash (verified against both the in-memory index and
the injected durable state store) and a subsequent retry recovers without re-submitting; and durability survives a
fresh connector instance sharing only the state store (no in-memory carryover).

**Unrelated pre-existing repo-wide QG break found and fixed in the same session (blocked this todo's own ship path):**
`quality-gates.sh`'s TEST step failed at collection time for the *entire* execution-service repo
(`ModuleNotFoundError: unified_api_contracts.external.onexbet.schemas`), confirmed byte-identical on a stashed clean
tree at LDR HEAD (not caused by this change). Root cause: `unified-api-contracts@cdb8ae88` ("complete the 6-bookmaker
removal in canonical/domain/sports/") deleted `unified_api_contracts/external/onexbet/` *and*
`canonical/domain/bookmaker_registry.py` entirely, but `code_readiness_t2_refdata_marketdata_2026_08_19.md`'s own
already-open todo had explicitly flagged this as a STOP condition requiring the coordinated order "retire
execution-service's dead `OneXBetAdapter` FIRST, then remove `onexbet` from the registry" — the registry side went
ahead anyway. `OneXBetAdapter` was independently re-verified dead/unrouted here (`SportsHandler.BOOKMAKER_VENUES` is
empty; only test-only and re-export references besides). Retired the adapter, its dedicated test file, and the
dangling re-exports/comment (execution-service@f4391ac596, same push as the CCTP fix). Regenerated
`unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml` via `--regenerate-baseline` (diffed before
committing: only the deleted file's entry was removed, nothing else changed) since the file no longer exists. Full
`quality-gates.sh` green (8880 passed, 0 failed, 155s) on the final commit. Updated the T2 plan's own todo to reflect
current reality; see that plan for the remaining 5-token cleanup this did NOT touch.
