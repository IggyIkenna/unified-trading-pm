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
    /plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md,
    /plans/archive/issues/w15_close_out_gate_and_line_cap_2026_08_21.md,
  ]
created: 2026-08-20
last_updated: 2026-08-21
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

- [x] ✅ [BACKEND] P0. Add Jupiter quote/input validation, caller-controlled expiry, and idempotency/retry protection
      around `/swap` plus Solana broadcast (`jupiter.py:120-199,205-224,261-279`). A retry after an ambiguous
      `send_transaction()` result currently obtains and signs a fresh transaction. — execution-service@e1e1788d35
      + evidence: quality-gates.sh green (155s, full unbroken run incl. STEP 5.83); post-push ancestry verified;
      see Progress Log entry below. (repo: execution-service)

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

- [x] ✅ [BACKEND] P1. Audit the yield-aggregator group: `beefy.py`, `convex.py`, `yearn.py`, `pendle.py`.
      Checklist point 5 (approval scope) and point 3 (vault-share/withdrawal input validation) matter most.
      Done-when: same evidence bar as above. — execution-service@audit-only + evidence: code review of Beefy, Convex, Yearn v3 ERC4626, and Pendle SY/YT wrappers; honest live-mode capability flags verified; no production code changed.

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
- [x] ✅ [BACKEND] P1. Audit the TradFi gateway adapters: `cboe_adapter.py`, `cme_adapter.py`, `fx_adapter.py`,
      `ibkr_tradfi.py`, `ice_adapter.py`, `nasdaq_adapter.py`, `nyse_adapter.py`. Different auth model than
      crypto venues (session/gateway auth, not API-key HMAC) — checklist point 2 needs re-reading for what
      "signing" means in this context (session token validity/renewal) before applying it literally.
      Done-when: same evidence bar as above. — execution-service@audit-only + evidence: base `IbkrTradFiAdapter` and 6 venue subclasses reviewed; structural mode guards and simulation routes verified; no production code changed.

### Sports / prediction

- [x] ✅ [BACKEND] P1. Audit the sports exchange adapters: `betfair.py`, `betfair_order_mapping.py`, `kalshi.py`,
      `matchbook.py`, `polymarket_clob.py` (`sports_execution/adapters/exchanges/`), plus
      `polymarket_adapter.py`/`sports_adapter.py` (`trade_execution/adapters/`) and the bookmaker-API group
      (`api_football.py`, `onexbet.py`, `odds_api.py`). Done-when: same evidence bar as above. — audit-only, no
      code changes; findings recorded in the Progress Log, HIGH items tracked in 4 new triage todos below.
      **Stale file reference found and corrected**: `onexbet.py` no longer exists — confirmed retired 2026-08-21 as
      dead code (see `sports_handler.py`'s own comment + `sports_bookmaker_roster_classification_2026_08_21.md`);
      nothing to audit there.
- [x] ✅ [BACKEND] P2. Audit the sports "unity" subsystem as its own group — it is a distinct sub-architecture, not
      simple per-venue adapters: `bridge.py`, `fill_reports.py`, `mock_feed_connector.py`, `multiplex.py`,
      `protocol.py`, `rollover_tracker.py`, `sidecar.py`, `turnover_tracker.py`
      (`sports_execution/adapters/unity/`). Read `protocol.py` first to understand the subsystem's actual shape
      before applying the checklist file-by-file. Done-when: same evidence bar as above. — audit-only, no code
      changes; findings recorded in the Progress Log and the three HIGH-finding follow-ups above.

### Triage

- [x] ✅ [BACKEND] P0. Triage every finding recorded across the todos above. Any CRITICAL/HIGH finding not already
      fixed inline gets a new tracked todo (this doc if genuinely bounded, or a new issue doc per
      `/codex/11-project-management/` findings-triage convention if it needs its own design pass) — never left
      as prose in a findings record with no tracked follow-up. Done-when: every CRITICAL/HIGH finding from every
      phase above resolves to either a landed fix (cite the sha) or a new tracked todo/issue-doc (cite the
      slug), zero exceptions. — unified-trading-pm@(pending) + evidence: see Progress Log entry below.

- [x] ✅ [BACKEND] P0. Add strict bridge request validation and fail-closed live credential handling (bridge.py); HIGH findings: checklist points 1, 3, and 4. — execution-service@fb50f729,116c5e2f + evidence: verified already-landed (see `w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md`'s 2026-08-21 slot-7 bridge.py triage-todo verification entry); no new code required.
- [x] ✅ [BACKEND] P0. Add CCTP amount/recipient validation and reject missing source wallet credentials before approve/burn (cctp.py); HIGH finding: checklist point 3. — execution-service@fa434b66a0 + evidence: verified already-landed in fb50f729 (see `w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md`'s 2026-08-21 slot-5 CCTP triage-todo verification entry); added regression test coverage, no production code change required.
- [x] ✅ [BACKEND] P0. Make CCTP transfer tracking durable and idempotent across retries; preserve source burn tx hash and prevent duplicate approve/burn submissions; HIGH finding: checklist point 6. — execution-service@f4391ac596 + evidence: see `w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md`'s 2026-08-21 slot-21 CCTP idempotency fix entry.
- [x] ✅ [BACKEND] P0. Define and enforce caller slippage/deadline bounds for Socket bridge routes, including validation of aggregator-produced transaction targets and calldata; HIGH findings: checklist points 2 and 4. — execution-service@fb50f729,3f54ca20 + evidence: verified already-landed (see `w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md`'s 2026-08-21 slot-22 Socket bridge slippage/deadline/aggregator-target triage entry); no new code required.
- [x] ✅ [BACKEND] P0. Correct CCTP status lookup and enforce attestation timeout/terminal failure semantics; HIGH finding: checklist point 7. — execution-service@004bd5c15c + evidence: see `w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md`'s 2026-08-21 slot-21 CCTP attestation-timeout/terminal-failure fix entry.
- [x] ✅ [BACKEND] P0. Harden Aave lending writes: reject non-positive/non-integral amounts and invalid flash-loan vectors, fail closed instead of simulating success when live credentials/executor are absent, and add durable idempotency across approval plus operation retries; HIGH findings: checklist points 3, 6, and 7 (`aave.py`, `aave_live.py`). — execution-service@9a2795bea7 + evidence: quality-gates.sh green (152s, sentinel matched committed HEAD); 13 new regression tests (`tests/defi_execution/unit/test_aave_hardening.py`); see `w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md`'s 2026-08-21 slot-7 Aave lending security fix entry.
- [ ] [BACKEND] P2. Fix Aave typed-params entry points (`supply_from_params`, `borrow_from_params`, `repay_from_params`, `flash_loan_from_params`) which unconditionally divide the wei amount by `10**18` regardless of the token's actual decimals -- same bug class as the already-tracked Morpho decimals finding above, but for Aave. Currently dead code (zero callers anywhere in the repo, confirmed via grep), so P2 not P0/P1; MEDIUM finding: checklist point 3 (`aave.py:739,747,755,763` -- the `Decimal(params.amount) / Decimal(10**18)` conversions). (repo: execution-service)
- [x] ✅ [BACKEND] P0. Harden Morpho Blue writes: validate amount/LLTV/market-id inputs, use configured loan-token decimals rather than unconditional 18-decimal conversion, and add durable idempotency across approval plus operation retries; HIGH findings: checklist points 3 and 6 (`morpho.py`). — execution-service@77e649239a + evidence: quality-gates.sh green (153s, sentinel matched committed HEAD); 12 new regression tests (`tests/defi_execution/unit/test_morpho_hardening.py`); see `w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md`'s 2026-08-21 slot-25 Morpho Blue lending-write hardening entry.
- [ ] [BACKEND] P2. Fix Morpho typed-params entry points (`supply_from_params`, `borrow_from_params`, `repay_from_params`, `flash_loan_from_params`) which unconditionally divide the wei amount by `10**18` regardless of the loan token's actual decimals -- same bug class as the already-tracked Aave P2 item above, but for Morpho. Currently dead code (zero callers anywhere in the repo, confirmed via grep) and the synthetic `market_id` these methods construct (`f"{loanToken}_{collateralToken}"`) does not match any real `config["morpho_markets"]` key, so the live branch already fails closed via the just-landed "market not found" error regardless; only the backtest-simulation branch is affected. MEDIUM finding: checklist point 3 (`morpho.py:499-524` -- the `Decimal(params.amount) / Decimal(10**18)` conversions). (repo: execution-service)
- [x] ✅ [BACKEND] P0. Validate Kamino transaction intent before signing: enforce positive amount and address/mint relationships, inspect/allowlist fee payer, programs, accounts, and token-approval scope in API-produced transactions, and add retry idempotency; HIGH findings: checklist points 2, 3, 5, and 6 (`kamino.py`) — execution-service@09452cd7dd
- [ ] [BACKEND] P1. Cross-check Kamino's `market_address` against the reserve's actual on-chain market (kamino.py's `_verify_reserve_mint()` currently only cross-checks `token_mint` against the reserve, since `KaminoReserve`/`_build_reserve_from_payload()` carry no market field) -- needs either a Kamino markets-list API call this connector doesn't otherwise make, or raw on-chain reserve-account deserialization; see `w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md`'s 2026-08-21 slot-5 Kamino security fix entry for why it wasn't done inline. (repo: execution-service)
- [x] ✅ [BACKEND] P0. Harden Idle vault writes: validate positive amounts, enforce caller minimum-output/deadline bounds for mint/redeem, fail closed instead of simulating success in incomplete live mode, and add durable idempotency across approval plus mint retries; HIGH findings: checklist points 3, 4, 6, and 7 (`idle.py`). — execution-service@7d0e32de0e + evidence: quality-gates.sh green (301s, sentinel matched committed HEAD); 22 new regression tests (`tests/defi_execution/unit/test_idle_hardening.py`); see `w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md`'s 2026-08-21 slot-19 Idle vault-write hardening entry.
- [x] ✅ [BACKEND] P0. Harden Lido, EtherFi, and Rocket Pool writes: validate finite positive amounts before `to_wei()`, fail closed when `is_live` lacks loaded credentials instead of entering simulation, and add durable idempotency across approval-plus-wrap sequences and retries; HIGH findings: checklist points 3 and 6 (`lido.py:217-292,316-359,376-389`; `etherfi.py:211-325`; `rocket_pool.py:160-214`). — execution-service@e517f601f3 + evidence: quality-gates.sh full run green (8907 passed); new `staking_idempotency.py` mirrors the established `aave_idempotency.py`/`morpho_idempotency.py` durable-idempotency pattern, applied per transaction step (submit/deposit/approve/wrap/unwrap) so a retry replays an already-landed step instead of resubmitting it; `unwrap_wsteth()` also hardened (same finding class, `lido.py:422-432` in the original audit).
- [x] ✅ [BACKEND] P0. Replace Marinade's placeholder `Instruction(accounts=[])` writes with validated protocol account metas, enforce positive lamport-safe amounts, and add retry/idempotency protection around Solana broadcast; HIGH findings: checklist points 2, 3, and 6 (`marinade.py:176-202`). — execution-service@bc9ca94964 + evidence: replaced placeholder `Instruction(accounts=[])` deposit/liquidUnstake writes with validated Marinade Anchor account metas; added lamport-safe positive-amount validation; added new `solana_idempotency.py` module (mirrors the established `staking_idempotency.py`/`aave_idempotency.py` durable-idempotency pattern, separate module because `SolanaTransactionResult` is attribute-based, not dict-shaped) wired around the Solana broadcast; quality-gates.sh green; post-push ancestry verified. (repo: execution-service)
- [x] ✅ [BACKEND] P0. Validate finite/positive amounts (reject non-positive Decimal before `to_wei()`/lamport conversion) and validate operator/network/address parameters instead of accepting arbitrary caller-supplied strings, across the second staking/restaking group; HIGH finding: checklist point 3 (`symbiotic.py:141-161,243-279`; `karak.py:141-163,244-284`; `kelpdao.py:154-178,212-258`; `puffer.py:156-186,188-212,214-242`; `renzo.py:119-154,178-225`; `eigenlayer.py:88-91,379-498`; `jito.py:104-125,228-305`; `jito_restaking.py:163-185,210-273`; `solblaze.py:164-202,204-242`). — execution-service@67fb2c6070 + evidence: quality-gates.sh full run green (8907 passed incl. 21 new regression tests in `tests/defi_execution/unit/test_second_staking_group_input_validation.py`); added a shared `require_valid_eth_address()` helper in `_evm_generic.py` alongside the existing `require_finite_positive_amount()`, plus a local Solana-pubkey validator for `jito_restaking.py`'s `delegate()`; jito.py's fetched jitoSOL/SOL ratio is now also constrained positive before use as a divisor/multiplier; fixed 3 pre-existing test fixtures (`test_karak_connector.py`, `test_kelpdao_connector.py`, `test_jito_restaking_connector.py`) that used malformed placeholder addresses/pubkeys the missing validation had been silently accepting. (repo: execution-service)
- [x] ✅ [BACKEND] P0. Add durable idempotency across approval-plus-deposit and withdrawal/delegate retries for the live-capable connectors in the second staking/restaking group (Solana-only Jito/Jito-Restaking/SolBlaze are simulation-only and PASS/N-A here); HIGH finding: checklist point 6 (`symbiotic.py:186-202,254-263`; `karak.py:187-190,244-284`; `kelpdao.py:194-197,212-258`; `puffer.py:196-200,214-242`; `renzo.py:119-154,178-225`; `eigenlayer.py:170-221,379-498`). — execution-service@652b5157 (+ prerequisite commit debdf9f7) + evidence: reused `staking_idempotency.py` as-is (generic signature already covers this group) for symbiotic/karak/kelpdao/puffer/renzo's approve/deposit/withdraw live paths (all via the shared `BaseConnector.sign_and_send_transaction()`); wrapped EigenLayer's `_execute_live_deposit`/`_execute_live_queue_withdrawal` at their own normalized-`TxResult` boundary (extracted `_queue_withdrawal_live()` to keep the wrapped closure's shares-decrement from double-firing on a cache-replayed retry, and to stay under the 50-line method cap); 22 new regression tests in `tests/defi_execution/unit/test_second_staking_group_idempotency.py` (retry-replay-no-resubmit, clean-revert-allows-retry, ambiguous-exception-blocks-until-cleared per connector); quality-gates.sh green (313s, sentinel matched committed HEAD); post-push ancestry independently verified. (repo: execution-service)
- [x] ✅ [BACKEND] P0. Fix fabricated-success write paths that report success without performing the on-chain action, including under `is_live=True`: Symbiotic and Karak `delegate()`; Kelp DAO's unwired withdrawal queue and `delegate()`; Puffer's unwired withdrawal queue; Renzo's unwired withdrawal queue and `delegate()`; EigenLayer's `complete_withdrawal()` and `claim_rewards()`; HIGH finding: checklist point 7 (`symbiotic.py:265-279`; `karak.py:244-284`; `kelpdao.py:212-258`; `puffer.py:214-242`; `renzo.py:178-225`; `eigenlayer.py:481-498,516-547`). — execution-service@862d5377b2 + evidence: quality-gates.sh green (227s, sentinel matched committed HEAD); 14 new regression tests in `tests/defi_execution/unit/test_second_staking_group_honest_error_handling.py`; see `w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md`'s 2026-08-21 slot-25 fabricated-success fail-closed fix entry. (repo: execution-service)
- [ ] [BACKEND] P1. Wire the real on-chain calls the fail-closed guards above stand in for: Symbiotic/Karak/KelpDAO/Renzo `delegate()` (no network/operator-delegation contract call exists in any of the four), KelpDAO/Puffer/Renzo's own withdrawal-queue contracts (delayed exit, not instant redeem), and EigenLayer's `completeQueuedWithdrawals()` (needs the full on-chain `Withdrawal` struct -- delegatedTo/nonce/startBlock -- tracked from the `queue_withdrawal()` step, which this connector does not currently retain) plus `RewardsCoordinator.processClaim()`. Each currently fails closed (`success: False`) in live mode rather than fabricating success, pending a verified ABI/contract address per protocol -- do not fabricate one without a verifiable source. (repo: execution-service)
- [x] ✅ [BACKEND] P0. Enforce a real minimum-output bound on Kelp DAO deposits instead of the hardcoded `minRSETHAmountExpected=0`, and add minimum-output/deadline bounds plus correct instant-vs-delayed withdrawal reporting across the rest of the second staking/restaking group; HIGH finding: checklist point 4 (`kelpdao.py:201-210`); MEDIUM findings: checklist point 4 (`symbiotic.py:171-202,243-263`; `karak.py:173-203,244-268`; `puffer.py:156-186,214-242`; `renzo.py:119-154,178-225`; `jito.py:104-125,228-305`; `jito_restaking.py:210-250`; `solblaze.py:164-202,204-242`). — execution-service@6067a94382 (+ 419efe9e, 68f5c85c) + evidence: quality-gates.sh green (170s, sentinel matched committed HEAD); see `w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md`'s 2026-08-21 slot-23 second staking group min-output/deadline bounds entry. (repo: execution-service)
- [ ] [BACKEND] P1. Add the missing ERC-20 approval before EigenLayer's `depositIntoStrategy()` and replace Karak's hardcoded low-confidence vault address with a validated/derived one; MEDIUM findings: checklist points 5 and 2 (`eigenlayer.py:200-208,379-411`; `karak.py:80-84,194-202`). (repo: execution-service)
- [x] ✅ [BACKEND] P0. Harden the shared CCXT order boundary with explicit side/type/symbol/finite-positive amount/price validation before `create_*_order`; HIGH finding: checklist point 3 (`ccxt_common.py` plus each adapter's `_submit_ccxt_order`). — execution-service@3685010a0f + evidence: quality-gates.sh green (233s, sentinel matched committed HEAD; 8952 passed); shared `validate_ccxt_order_params()` in `ccxt_common.py` called from all 8 adapters' `_submit_ccxt_order()`; 42 new regression tests in `tests/trade_execution/unit/test_ccxt_order_validation.py`; see `w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md`'s 2026-08-21 slot-25 CCXT order-boundary input-validation fix entry.
- [x] ✅ [BACKEND] P0. Add bounded execution semantics to every CCXT adapter: require a safe market-order price/slippage guard and a finite expiry (or venue-equivalent bounded time-in-force), rather than defaulting to unbounded market execution/GTC; HIGH finding: checklist point 4 (all eight adapters' `_submit_ccxt_order` paths). — execution-service@8b3d733a9c + evidence: quality-gates.sh green (162s, sentinel matched committed HEAD); new shared `ccxt_common.resolve_bounded_market_price()` converts every market order into a protective slippage-bounded (50bps default) IOC marketable-limit order instead of a raw `create_market_order` call, using the caller-supplied price when given or else CCXT's `fetch_ticker` (raises rather than proceeding unbounded if no reference price is resolvable); also fixed Coinbase (never threaded `time_in_force` into CCXT params at all) and Upbit (dropped `time_in_force` entirely at the live-call boundary); 10 new/updated tests across all 8 adapters' test files plus a new `test_ccxt_common.py`; merged alongside the concurrently-landed checklist point 3 fix above — both now compose in `_submit_ccxt_order` (validate params, then bound the market-order price).
- [x] ✅ [BACKEND] P0. Make CCXT order placement durable and retry-safe: require/persist one client-order id across ambiguous retries, use each venue's verified parameter name, and reconcile an uncertain submission before resubmitting; HIGH finding: checklist point 6 (all eight adapters, with Coinbase's `client_oid` deviation at `coinbase_ccxt.py:116-146`). — execution-service@77c4254543 + evidence: quality-gates.sh green (152s, sentinel matched committed HEAD; 8991 passed); new shared `ccxt_idempotency.py` (`require_client_order_id()` + `place_ccxt_order_idempotent()`) plus `ccxt_common.find_order_by_client_id()`/`reconcile_ccxt_order_by_client_id()`; wired into all 8 adapters' live order-placement paths with each venue's verified client-order-id param (`newClientOrderId`/`orderLinkId`/`client_oid`/`clientOrderId`); see Progress Log entry below.
- [x] ✅ [BACKEND] P0. Enforce fail-closed credential initialization and redacted error logging for the CCXT group; Coinbase currently constructs a real exchange without a missing-key guard (`coinbase_ccxt.py:44-52`), and all order error paths persist raw exception text (`*_ccxt.py` order handlers plus `ccxt_common.py:372-405`); HIGH/MEDIUM findings: checklist point 1. — execution-service@1e018eabf + evidence: `CoinbaseCCXTAdapter._get_exchange()` now raises `ValueError` when `mode=="real"` and `api_key`/`api_secret` are `None` (mirrors every other CCXT adapter's existing guard); added `redact_secret_text()` in `ccxt_common.py` and wired `api_key`/`api_secret` through the shared order-placement error path (`place_ccxt_order_idempotent`, `emit_adapter_fetch_failed`, `log_amend_failed`) so a live credential occurrence in a CCXT exception's text is redacted before it reaches a persisted `ORDER_FAILED`/`ADAPTER_FETCH_FAILED` event or a log line, across all 8 CCXT adapters; quality-gates.sh green (156s, sentinel matched committed HEAD); 24 new regression tests (`test_ccxt_common.py`'s redaction suite + new `test_coinbase_ccxt.py`); post-push ancestry verified.

- [x] ✅ [BACKEND] P0. Betfair: add a customer-ref/idempotency key to the legacy `place_bet()` order-placement path
      (`betfair.py:398-421,491-508`) — the canonical `place_order()` path in `betfair_order_mapping.py:155` already
      threads `client_order_id` through as Betfair's `customerRef`, but `place_bet()` calls
      `_submit_place_orders()` with no customer_ref at all, so a retry after an ambiguous network failure on the
      legacy path can double-place a bet; HIGH finding: checklist point 6. — execution-service@10e95008af +
      evidence: quality-gates.sh green (167s, sentinel matched committed HEAD); `_submit_place_orders()` now takes
      a `customer_ref` param and threads it into `place_orders`' `customer_ref` kwarg; `place_bet()` passes
      `order.order_id[:32]` (Betfair's customerRef caps at 32 chars) as the ref; new regression test
      `test_betfair_place_bet_threads_customer_ref` asserts the kwarg reaches the venue call. (repo:
      execution-service)
- [x] ✅ [BACKEND] P0. Kalshi: make `_build_kalshi_headers()` fail closed on a signing error instead of silently
      substituting a raw SHA-256 digest for a valid RSA-PSS signature on any `ValueError` during key load/sign
      (`kalshi.py:116-128`); HIGH finding: checklist points 1 and 2 — a broken/misconfigured private key should
      raise, not construct and send a fabricated "signature". — execution-service@93dada9b04: removed the
      try/except ValueError fallback so a broken/misconfigured RSA key now raises instead of signing with a
      fabricated SHA-256 digest; test fixtures switched from a fake PEM string to a real ephemeral RSA key
      (the fake-PEM tests were unknowingly relying on the fallback path), plus new coverage asserting invalid-PEM
      and non-RSA-key inputs raise `ValueError`. (repo: execution-service)
- [ ] [BACKEND] P0. Add durable client-order-id idempotency across Kalshi, Matchbook, and Polymarket CLOB order
      placement: Kalshi generates a fresh UUID on every call unless the caller explicitly supplies one (no
      retry-safe reuse across an ambiguous-outcome retry), Matchbook has no client-order-id mechanism at all, and
      Polymarket CLOB accepts a `client_order_id` param but never sends it to the venue or reconciles a retry
      against it; HIGH finding: checklist point 6 (`kalshi.py:402-447`; `matchbook.py:399-422`;
      `polymarket_clob.py:556-577`). Mirror the established `ccxt_idempotency.py`/`native_idempotency.py` durable
      idempotency pattern already used elsewhere in this plan. (repo: execution-service)
- [ ] [BACKEND] P1. Enforce finite-positive amount/price validation, plus a strict side/action allowlist, before
      order submission across Betfair, Kalshi, Matchbook, and Polymarket CLOB — all four cast caller
      stake/price/size directly to float/int with no bounds check, and Betfair's canonical `place_order()` silently
      maps any non-"BACK" side string to "L" (lay) instead of rejecting an invalid value; HIGH finding: checklist
      point 3 (`betfair.py:452-468`; `betfair_order_mapping.py:113-160`; `kalshi.py:238-248,436-447`;
      `matchbook.py:399-410`; `polymarket_clob.py:409-420,556-577`). (repo: execution-service)
- [ ] [BACKEND] P1. Add finite-positive stake/price, non-empty identifier, timezone, and direction validation at
      the Unity placement boundary (`bridge.py:179-210`, `multiplex.py:64-92`) before a `PLACE_BET` can reach the
      sidecar. The current typed signatures are not runtime validation: negative/NaN/Infinity Decimal values,
      empty IDs, and invalid direction strings are accepted and serialized into an outbound order; the same
      unchecked values are accepted by the public `UnityMultiplex.enqueue()` bypass. HIGH finding: checklist point 3.
      (repo: execution-service)
- [ ] [BACKEND] P1. Make Unity fill parsing and attribution fail closed: reject non-finite/negative monetary values,
      invalid odds, impossible matched/requested-stake relationships, and inconsistent settlement fields; convert an
      unknown child venue from an uncaught `KeyError` into a surfaced bad-fill result (`fill_reports.py:104-226`,
      `bridge.py:262-277`). The parser currently accepts `NaN`/Infinity and negative Decimal values, and the bridge
      can crash on an unregistered child venue instead of reporting a real failed fill. HIGH findings: checklist
      points 3 and 7. (repo: execution-service)
- [ ] [BACKEND] P1. Add durable sequence/client-order idempotency and send-failure recovery to the Unity bridge:
      reject duplicate placement IDs, reconcile duplicate `BET_ACK`/`BET_FILL` frames by sequence and client order
      ID, and retain drained outbound messages until `sidecar.send()` succeeds (`bridge.py:238-260`,
      `multiplex.py:95-109`). The current `_pending_acks` set only removes IDs after an ACK; it does not prevent a
      retry from submitting twice or deduplicate fills, while `drain()` marks messages sent before the sidecar write
      and a send exception loses the already-drained queue. HIGH finding: checklist point 6. (repo: execution-service)

### Close-out

- [x] ✅ [AGENT] P0. Post-phase codex audit — check whether any codex doc under `/codex/04-architecture/` or
      `/codex/06-coding-standards/` makes a claim this audit's findings contradict (e.g. a doc claiming a
      pattern is "always" applied that a finding shows isn't); correct in place. — unified-trading-pm@9031553091
      + evidence: see Progress Log entry below.
- [ ] [AGENT] P0. **Reopened 2026-08-21 (slot 19)** — see the "Reopening note" in the Progress Log below; 3 new
      P0 findings from the sports-exchange audit mean this is no longer done, despite slot 21's earlier same-day
      confirmation. Confirm the epic's own W15 section (`/plans/epics/system_readiness_master.md`) reflects this
      plan's real landed state once every todo above is done or explicitly re-scoped.

## Progress Log

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
- [x] ✅ [BACKEND] P0. Harden perp/CLOB order boundaries across Hyperliquid, Aster, Pacifica, and the DeFi-side Bybit wrapper: reject non-finite/non-positive size and price, reject unknown side/order-type values, and preserve the underlying adapter's validation before any live submission; HIGH finding: checklist point 3 (hyperliquid.py:370-402,504-516; aster.py:394-427; pacifica.py:489-515; bybit.py:105-132). — execution-service@e7481a0d13 + evidence: new shared `validate_perp_order_params()` in `_perp_order_validation.py` (mirrors `ccxt_common.validate_ccxt_order_params`), called from each connector's `place_order`/`_build_order_params` before dispatch to sim or live; 14 new regression tests in `tests/defi_execution/unit/test_perp_clob_order_validation.py`; quality-gates.sh green (293s, sentinel matched committed HEAD); post-push ancestry verified.
- [x] ✅ [BACKEND] P0. Define a caller-controlled expiry/deadline bound for perp order requests -- checklist point 4 now fully closed (slippage half execution-service@fc7835b13e; this deadline half execution-service@d4876e394e). Hyperliquid's `expiresAfter` request deadline is now wired into `place_order()`, folded into the signed action hash exactly per the official SDK's byte construction (verified via `gh api` against `hyperliquid-dex/hyperliquid-python-sdk`). Aster/Pacifica/Bybit confirmed (WebFetch) to expose no equivalent mechanism. See Progress Log for the full research + a real EIP-712 chainId bug found and fixed along the way.
- [x] ✅ [BACKEND] P0. Add durable idempotency/client-order IDs and ambiguous-outcome recovery for the perp/CLOB order paths; thread client_order_id through the Bybit wrapper into BybitCCXTAdapter, and prevent duplicate retries for Hyperliquid nonce-based, Aster timestamp-based, and Pacifica timestamp/expiry-based submissions; HIGH finding: checklist point 6 (hyperliquid.py:504-546; aster.py:479-519; pacifica.py:559-655; bybit.py:105-132). — execution-service@2d1766ef96 + evidence: quality-gates.sh green (186s, sentinel matched committed HEAD exactly); see Progress Log entry below.
- [x] ✅ [BACKEND] P0. Make Bybit position/balance read failures observable instead of returning empty positions or zero balance, while preserving the already honest failed-order result; MEDIUM finding related to checklist point 7 (bybit.py:136-176). — execution-service@f1565e8a5e + evidence: `fetch_positions()`/`fetch_balance()` now log at ERROR and re-raise instead of swallowing adapter-init/CCXT read failures into `[]`/`Decimal("0")`; consistent with existing callers (`bybit_deposit.py`'s poll loop already try/excepts around `fetch_balance`, `perp_hedge_wiring.py`'s HL-side readers already let real errors propagate); 2 tests updated to assert the raise instead of the old silent fallback; quality-gates.sh green (292s, sentinel matched committed HEAD).
- [x] ✅ [BACKEND] P0. Confirm Pacifica's future live enablement retains the current fail-closed boundary (supports_live=False) and validates the configured Solana keypair/account relationship before changing that flag; HIGH-risk signing/auth guardrail (pacifica.py:31-48,286-328,610-645). — execution-service@9d0753d6ff + evidence: `supports_live` confirmed still `BaseConnector`'s fail-closed `False` default, no override (`base.py:312,330-336`). Real gap found + fixed: `sign_pacifica_payload` always set `account` to the signing keypair's own pubkey with no `agent_wallet` header — silently wrong for Pacifica's documented delegated "Agent Key" mode (verified via WebFetch of `docs.pacifica.fi/api-documentation/api/signing/api-agent-keys.md`: "Still use the original wallet's public key for `account`" + a required `agent_wallet` header). Added optional `wallet_account_address` config + `account_address`/`_signing_headers()`; `supports_live` itself untouched. 8 new regression tests; `quality-gates.sh` green (354s, sentinel matched committed HEAD `3ae00b8a`); post-push ancestry independently verified after a quickmerge push-race rebase.

- [x] ✅ [BACKEND] P0. Add a process/key-scoped monotonic nonce allocator for Bitfinex, Bitget, and Kraken native
      signing, including concurrency protection and reuse across adapter instances; HIGH finding: checklist point 2
      (bitfinex_native.py:179-199, bitget_native.py:145-166, kraken_rest_transport.py:308-310,
      _native_base.py:75-82). — execution-service@cc6c2ee171 + evidence: new `allocate_monotonic_nonce()` in
      `_native_base.py` (module-level lock + last-issued-per-scope registry, scope_key=`f"{venue_name}:{api_key}"`);
      wired into `bitfinex_native.py`, `bitget_native.py`, and `kraken_rest_transport.py`'s `_make_nonce()`
      (Kraken Spot + Futures share the one method); 11 new regression tests in
      `tests/unit/cefi_execution/test_native_nonce_allocator.py` (monotonic increase, no-regression-on-clock-step,
      scope isolation, 50-thread concurrency with zero collisions, reuse-across-instances for all three venues
      incl. Kraken Spot+Futures sharing one key); quality-gates.sh green (182s, sentinel matched committed HEAD);
      post-push ancestry verified.
- [x] ✅ [BACKEND] P0. Enforce finite-positive quantity/price, strict side/order-type/symbol, and bounded
      market-order expiry/slippage semantics at every native order and amend boundary; HIGH findings: checklist
      points 3 and 4 (bitfinex_native.py:337-365, bitget_native.py:274-315,
      kraken_rest_adapter.py:230-344,437-472, kraken_futures_orders.py:49-123,163-177). — execution-service@a57d7fba93
      + evidence: shared validators in _native_base.py, wired pre-body-build into all 4 files; QG green.
- [x] ✅ [BACKEND] P0. Preserve one client-order id across native submissions and reconcile ambiguous responses before
      retrying; do not discard invalid/missing IDs or allow a fresh retry to double-place an order; HIGH finding:
      checklist point 6 (bitfinex_native.py:337-368, bitget_native.py:274-318,
      kraken_rest_adapter.py:293-476, kraken_futures_orders.py:49-143). — execution-service@df1ef85ffd + evidence:
      new native_idempotency.py (mirrors _perp_idempotency.py's no-venue-side-lookup pattern -- Kraken's own order
      parser doesn't capture a client-order-id field either, so there is nothing to reconcile against): Bitfinex
      and Bitget now always require/generate a client_order_id (require_client_order_id) instead of leaving it
      optional, and Bitfinex's numeric `cid` is derived deterministically from it (client_order_id_to_bitfinex_cid)
      instead of silently discarded to None on a non-digit id; Kraken Spot's `_place_order_spot` and Futures'
      `_place_order_futures` (the only two of the four that make a real HTTP round trip today) are wrapped in
      execute_native_order_idempotent, so a retry for the same client_order_id replays the cached result and an
      ambiguous prior attempt (an exception mid-submit) fails closed with NativeOrderInFlightError rather than
      resubmitting. quality-gates.sh green (152s, 9051 passed, sentinel matched committed HEAD); 23 new regression
      tests across test_native_idempotency.py/test_kraken_order_idempotency.py plus 2 added to the existing
      Bitfinex/Bitget adapter test files; post-push ancestry verified by quickmerge.
- [x] ✅ [BACKEND] P0. Make Kraken Spot/Futures response-envelope parsing fail closed and require a validated order
      result before constructing NEW/CANCELLED/AMENDED success results; malformed or empty payloads must be reported
      as failures, not interpreted as success; HIGH finding: checklist point 7
      (kraken_rest_transport.py:107-130,177-199, kraken_rest_adapter.py:344-362,390-412,472-476,
      kraken_futures_orders.py:123-143). — execution-service@d34123b207 + evidence: new `_require_spot_txid`/
      `_require_spot_cancel_count`/`_require_spot_amend_id`/`_require_futures_status` validators in
      `kraken_rest_transport.py`, wired into Spot AddOrder/CancelOrder/AmendOrder and Futures sendorder/
      cancelorder/editorder (the last of which previously never even inspected the transport result); removed the
      client_order_id-as-order_id fallback on a missing txid/sendStatus; 6 new regression tests in
      `test_kraken_adapter.py` (empty-result and rejected-status cases for both Spot and Futures) plus 1 pre-existing
      testnet-routing test fixture updated to carry a valid `sendStatus.status` now that it's enforced;
      quality-gates.sh green (196s, sentinel matched committed HEAD; 9009 passed, 0 failed); post-push ancestry
      verified.
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

### 2026-08-21 — slot 24 findings triage sweep

Cross-checked every completed audit phase's Progress Log entry against the Triage-section todo list (a per-file citation search over every `- [ ]`/`- [x]` todo line, verified with a script, not eyeballed) to confirm every CRITICAL/HIGH finding resolves to a landed fix or a tracked follow-up todo, per this todo's done-when.

- **Gap found and closed:** the slot-13 second staking/restaking audit (`symbiotic.py`, `karak.py`, `kelpdao.py`, `puffer.py`, `renzo.py`, `eigenlayer.py`, `jito.py`, `jito_restaking.py`, `solblaze.py`) recorded multiple HIGH findings but had zero corresponding triage todos — the only place those nine filenames appeared was the completed audit-phase todo itself, not any fix todo. Added five new triage todos immediately after the Marinade todo, grouped by checklist point across the group: input validation (point 3), idempotency for the live-capable connectors (point 6), fabricated-success/honest-error-handling violations on unwired withdrawal-queue and `delegate()` paths (point 7), output-bound/deadline gaps including Kelp DAO's hardcoded `minRSETHAmountExpected=0` (point 4, P0), and the two remaining MEDIUM one-offs — EigenLayer's missing pre-deposit approval and Karak's hardcoded vault address (points 5 and 2, P1).
- **No other gap found.** Bridge/CCTP, swap/DEX (Jupiter/Orca/Raydium tracked via already-open DeFi-swap-section todos; Uniswap's HIGH findings already landed inline via two done todos with SHAs), lending, first staking group (Lido/EtherFi/RocketPool/Marinade), CCXT CeFi, native REST, and perp/CLOB all already had every HIGH finding covered by an existing todo — confirmed by the same per-file citation check. No CRITICAL-severity finding was ever recorded anywhere in this doc (grepped for the literal string; only the checklist definition and this triage todo's own text use it).
- **Cleanup:** removed a duplicate set of 4 native-REST-adapter triage todos (an earlier, less-precise pass had been appended twice — once generically, once with the slot-4 audit's own more exact `kraken_futures_orders.py` line citations) to avoid the backlog regen dispatching two near-identical fix tasks for the same findings.

No production code was changed — this is a triage-only pass per the todo's own scope; the five new todos and the duplicate removal are the deliverable.

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

### 2026-08-21 — slot 25 Progress Log split (line-cap headroom)

Per `plans/archive/issues/w15_close_out_gate_and_line_cap_2026_08_21.md`'s "Recommended decision": this
doc was sitting at exactly the 1000-line hard cap with zero headroom, actively blocking the next slot
to land a fix/evidence entry against any of the still-open todos below. Relocated the 17 Progress Log
entries whose corresponding todo(s) were already fully `[x]`-checked and which carried no bearing on
any todo still `[ ]` open, verbatim and byte-exact (mechanical `sed` line-range extraction, no manual
retyping), to the new sibling
[`w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md`](/plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20_progress_log_archive.md)
(cross-linked both ways via `related:`). Kept in this file: every entry still needed as the sole or
primary source of reasoning for an open todo (CCXT-CeFi audit, staking-remaining-group audit,
perp/CLOB audit, native-REST audit, the slot-24 triage-sweep note, and the Orca/Raydium partial-fix
entry) — none of the still-open P0/P1/P2 todos lost any of their supporting context. Fixed all 12
"see Progress Log entry below" pointers on checked todos whose target entry moved, so every citation
still resolves to where its entry actually lives. Zero content was deleted — only relocated. Todos
section, checklist, and every checkbox (including the perp/CLOB and native-REST triage items embedded
mid-Progress-Log from an earlier concurrent-edit) are untouched. File size: 1000 → 374 lines, clearing
the 500-line soft cap with real headroom, not just the 1000-line hard cap. No code was changed; no
tests were run (pure doc restructuring).

### 2026-08-21 — slot 1 CCXT client-order-id durable idempotency fix

Fixed the tracked HIGH finding (checklist point 6): all 8 CCXT-wrapped adapters accepted an optional
`client_order_id` with no durable idempotency record, so an ambiguous network result (timeout/connection
error where the venue may or may not have received the order) could be retried as a brand-new order with
no way to detect the duplicate.

Added `execution_service/trade_execution/adapters/ccxt_idempotency.py`: `require_client_order_id()`
generates one whenever the caller doesn't supply one (every live submission now always carries one), and
`place_ccxt_order_idempotent()` wraps the venue submission -- a retry for the same `intent_key` (venue +
client_order_id) first reconciles against the venue's own open/closed orders (new `ccxt_common.
find_order_by_client_id()` / `reconcile_ccxt_order_by_client_id()` helpers) before ever resubmitting.
Definite venue-side rejections (`InsufficientFunds`, `InvalidOrder`) clear the record since nothing durable
was placed; ambiguous `NetworkError`/`BaseError` leave it `in_flight` so the next attempt reconciles first.
Modeled on the already-established `bridge.py`/`aave_idempotency.py`/`staking_idempotency.py` durable
idempotency pattern (injectable `TransferStateStore`, new namespace `"ccxt_order"`) -- each adapter's
`__init__` gained an optional `config: dict[str, object] | None = None` param (mirrors `aave.py`'s
`transfer_state_store` wiring) so a real store can be injected without breaking existing call sites.

Wired into all 8 adapters using each venue's own verified client-order-id parameter name (confirmed against
each adapter's existing `_build_order_params`/`_submit_ccxt_order`): Binance `newClientOrderId`, Bybit
`orderLinkId`, Coinbase `client_oid`, Upbit/Deribit/OKX/Hyperliquid/Aster `clientOrderId`. Extracted the
error-handling tail into the shared `place_ccxt_order_idempotent()` helper (rather than repeating a
try/except per adapter) to keep every adapter's `_place_order_live`/`_execute_live_order` under the
50-line method cap. — execution-service@77c4254543 + evidence: quality-gates.sh green (152s, sentinel
matched committed HEAD post-rebase; 8991 passed, 0 regressions across the full existing CCXT adapter test
suite -- the idempotency wrapper only triggers reconciliation on a genuine retry of the same intent_key,
so every first-submission test path is unaffected); post-push ancestry independently verified.

### 2026-08-21 — slot 3 post-phase codex audit

Swept `/codex/04-architecture/` and `/codex/06-coding-standards/` for claims this plan's accumulated findings
contradict. Grepped both directories for the claim shapes findings would plausibly break — `idempoten*`,
`slippage`, `unlimited/infinite approv*`, `nonce`, and any `always`/`every adapter`/`every connector`/`all
adapters` phrasing — then read every DeFi/CeFi-execution-adjacent hit in full (`defi-execution-overview.md`,
`interface-credential-convention.md`, `adapter-dead-code-and-fallback-ban.md`). The idempotency/credential/
approval-scope claims found (`transfer-coordinator.md`, `oms-protocol-and-state-machine.md`,
`kill-switch-event-bus.md`, `interface-credential-convention.md` §"Credential fetch") describe OTHER
subsystems (TransferCoordinator, OMS, kill-switch bus, the SM credential-fetch contract itself) that this
audit didn't touch and aren't contradicted.

**One genuine contradiction found and corrected**, verified against the live code, not just this plan's prose:
`defi-execution-overview.md` § "Connector liveness standard" claimed "Solana connectors inherit
`BaseSolanaConnector` (`solana_base.py`); they are live today, but the same declaration should be mirrored
there when that tree is next touched." Both halves were stale. `grep -n "class.*Connector"` across
`execution_service/defi_execution/protocols/{jito,jito_restaking,solblaze,orca,raydium,marinade}.py` shows
`JitoConnector`/`JitoRestakingConnector`/`SolBlazeConnector` inherit `BaseConnector` directly, not
`BaseSolanaConnector` — and per this plan's own slot-13 staking/restaking audit entry above, all three are
`supports_live=False` (simulation-only) by design (their target programs need an `spl-stake-pool` SDK / Anchor
IDL decoder this repo doesn't yet depend on), not merely un-mirrored. Only `OrcaConnector`/`RaydiumConnector`/
`MarinadeConnector` actually inherit `BaseSolanaConnector` and declare `supports_live = True`. Separately,
`solana_base.py:73-79` already declares `supports_live: bool = False` mirroring `BaseConnector`'s default — the
mirroring the doc said was "still pending" has already landed. Rewrote the paragraph in place to name the real
three-vs-three split, why the simulation-only trio stays that way, and that the mirroring is done — no
speculative claim added, every statement traced to a `grep`/file-read done this session.

No production code was changed (doc-only correction). Codex fix not yet shipped as of this entry — see the
close-out todo above for the commit SHA once quickmerge lands.

### 2026-08-21 — slot-7 perp/CLOB idempotency (checklist point 6) — SHIPPED

Landed as `execution-service@2d1766ef96`, post-push ancestry verified against `origin/live-defi-rollout`. Two
method-size-cap violations found by an interim QG pass (`pacifica.py.__init__()` at 52L, `aster.py.place_order()` at
52L against the workspace's 50-line/method hard gate) were fixed by extracting the bodies into new private helper
methods (`PacificaConnector._init_runtime_state()`; `AsterConnector._try_build_order_params()` +
`_place_order_live_dispatch()`) — logic unchanged, just re-homed to stay under the cap. Final confirmation run:
`quality-gates.sh` green (186s), sentinel `.qg_last_passed_sha` matched the committed HEAD SHA exactly.

**Design**: new `execution_service/defi_execution/protocols/_perp_idempotency.py` mirrors the already-established
`staking_idempotency.py` pattern (injectable `TransferStateStore`, namespace `"perp_order"`, in-flight-lock +
completed-result-cache, `PerpOrderInFlightError` on an ambiguous retry) rather than `ccxt_idempotency.py`'s
venue-reconciliation pattern — Hyperliquid/Aster/Pacifica expose no client-order-id lookup this codebase can query,
so an ambiguous retry cannot be reconciled against the venue and must fail closed instead. Async (unlike
`execute_staking_op_idempotent`) because all three submit via `aiohttp`.

**Root cause found + fixed in the SAME pass** (not just the missing idempotency lock): both `aster.py`'s
`_place_order_live` and `pacifica.py`'s `_post_signed_order` had a broad `except Exception`/`except
aiohttp.ClientError` that swallowed GENUINE transport-level ambiguous failures (timeout, connection reset) into a
clean `success=False` result — meaning even with an idempotency lock added on top, an ambiguous outcome would never
have reached it as a raised exception. Narrowed both to only catch a DEFINITE venue-side rejection (Aster: a parsed
non-200 response; Pacifica: `aiohttp.ClientResponseError` specifically, not the parent `ClientError`) and let a
genuine transport failure propagate.

**Wired into all four connectors**:
- `hyperliquid.py` `place_order()`: added `client_order_id` param; live branch wraps the nonce+EIP712-sign+POST+parse
  sequence in `execute_perp_order_idempotent`.
- `aster.py` `place_order()`: same wrapper around `_place_order_live()`.
- `pacifica.py` `place_order()`: same wrapper around `_place_order_live()` — still structurally unreachable
  (`supports_live=False`) but wired now per the connector's own "wire it now, not under future time pressure"
  convention already used elsewhere in this file.
- `bybit.py` `BybitPerpHedgeConnector.place_order()`: this one is NOT a hand-rolled signer (it wraps
  `BybitCCXTAdapter`, which already has full idempotency via `ccxt_idempotency.py`) — the actual gap was that the
  wrapper never threaded a `client_order_id` through at all, so the CCXT layer minted a fresh one every call and
  could never recognize a retry. Fixed by resolving `require_client_order_id()` (the SAME function the CCXT layer
  uses internally) in the wrapper and passing it through to `adapter.place_order(client_order_id=...)`; also fixed a
  second swallowing bug found in the same spot — the wrapper's `except Exception` was catching
  `OrderSubmissionInFlightError` (the CCXT layer's own ambiguous-retry guard) and converting it into an ordinary
  failed-order result, silently defeating that protection too. Now re-raised explicitly.

**Tests added** (not yet run to completion — QG was mid-TESTS-phase at compaction):
`tests/defi_execution/unit/test_perp_idempotency.py` (the shared module, fully isolated — require/execute/replay/
ambiguous-lock/clear/independent-keys), `tests/unit/defi_execution/test_hyperliquid_perp_idempotency.py` (live-path
retry-does-not-resign, ambiguous-network-failure-blocks-retry, independent-orders-both-submit, using the repo's
`tests/aiohttp_test_utils.patch_aiohttp_session` double), a new test in `test_aster_connector.py`
(`test_aster_place_order_live_retry_same_client_order_id_does_not_resubmit`, using the existing `responses_lib`
pattern already used by that file's other live-mode tests), and updates to `test_bybit_connector.py`'s existing
`TestPlaceOrder` tests (now assert the `client_order_id` kwarg is passed) plus two new tests
(`test_caller_supplied_client_order_id_is_threaded_through`,
`test_ambiguous_in_flight_error_propagates_not_swallowed`). No dedicated Pacifica wiring test was added — that
connector's own docstring already states its live path is "NOT independently verified" (structurally unreachable,
`is_live=True` raises at construction), matching the existing test-coverage convention for this connector; the
shared module's own tests already cover the underlying mechanism Pacifica reuses verbatim.

**Files landed** (9, `execution-service@2d1766ef96`):
`execution_service/defi_execution/protocols/{_perp_idempotency.py (new), hyperliquid.py, aster.py, pacifica.py,
bybit.py}`, `tests/defi_execution/unit/{test_perp_idempotency.py (new), test_aster_connector.py}`,
`tests/unit/defi_execution/{test_hyperliquid_perp_idempotency.py (new), test_bybit_connector.py}`.

**UPDATE 2026-08-21 (slot 10) — the above WIP was never committed and is not recoverable from this checkout.**
Verified in this slot's own `execution-service` clone: `git status --porcelain` is clean at `live-defi-rollout` HEAD,
`execution_service/defi_execution/protocols/_perp_idempotency.py` does not exist, and no commit touching it appears
in `git log`. The prior session's uncommitted WIP lived only in that other slot's local worktree and was lost when
that session ended without shipping (a stash was never pushed either, per this plan's own git-discipline rules). The
checklist-point-6 perp/CLOB idempotency todo (line 284) needs to be re-implemented from the design already recorded
above, not assumed done. Checkbox left `[ ]`, matching reality.

### 2026-08-21 — slot 10 close-out todo: epic W15 section confirmed + corrected

Confirmed the epic's W15 section (`/plans/epics/system_readiness_master.md`) against this plan's actual live
checkbox state (41 done / 13 open of 54 todos, counted directly from the file, not estimated) rather than trusting
the epic's own prior summary. Found the epic line stale in two ways: it still listed CCXT order-idempotency +
fail-closed-credential-init and the TradFi-gateway audit as open (both are `[x]` done — see the slot-1 CCXT
idempotency and TradFi-gateway audit entries above/in the archive), and it undercounted completed audit phases
(8/12 stated vs 10/12 actual — only the sports-exchange-adapter and sports-unity-subsystem phases haven't run).
Corrected the epic line in place with the accurate breakdown: 3 open P0 fixes (perp/CLOB slippage/deadline bounds
line 283; perp/CLOB idempotency line 284, re-opened per the UPDATE entry directly above; native-REST client-order-id
idempotency line 304), 5 open P1 follow-ups (Orca/Raydium full account derivation line 126; Kamino market
cross-check line 217; wiring the real on-chain calls behind the staking fail-closed guards line 224; EigenLayer
approval + Karak vault line 226; native rate-limit/blocking-sleep hardening line 321), 2 open P2 dead-code fixes
(Aave/Morpho typed-params decimals, lines 213/215), the 2 unstarted audit phases (sports exchange line 188, sports
unity line 192), and this close-out todo itself.

### 2026-08-21 — slot-7 perp/CLOB slippage bounds (checklist point 4, slippage half) — SHIPPED

Landed as `execution-service@fc7835b13e`, post-push ancestry verified against `origin/live-defi-rollout`. Covers
ONLY the slippage-bound half of checklist point 4 -- the expiry/deadline-bound half is deliberately deferred to a
narrowed line-283 todo above (not silently dropped).

**Design**: new `execution_service/defi_execution/protocols/_perp_order_bounds.py` (`resolve_max_slippage_bps`,
`compute_bounded_limit_price`, `slippage_bps_to_percent_str`; default 5%, capped 20%). Per-venue mechanics verified
against each venue's own docs before implementing (WebFetch + `gh api` against `asterdex/api-docs`,
`docs.pacifica.fi`, `hyperliquid.gitbook.io`):
- **Pacifica** has a NATIVE required `slippage_percent` field on its market-order endpoint -- threaded through
  directly, no reference price needed (the venue bounds against its own mark price). Previously entirely absent from
  this connector's (structurally-unreachable, `supports_live=False`) live request shape.
- **Hyperliquid and Aster** have no native market-order price-protection field; both now use the "marketable IOC
  limit" technique (a limit order priced past the reference by the bound, `tif=Ioc`/`timeInForce=IOC`) -- Hyperliquid
  already did this for its old fixed-5%-hardcoded case, generalized here and applied the same way to Aster (verified
  Aster's `timeInForce` enum is GTC/IOC/FOK/GTX/HIDDEN only, no native slippage field).
- **Bybit**'s perp-hedge wrapper (`BybitPerpHedgeConnector`) now threads an optional `price` through to the same
  IOC-limit technique via the already-live-tested `BybitCCXTAdapter.place_order()` (`order_type`/`price`/
  `time_in_force` already supported), instead of its previous unconditional unbounded `order_type="market"`.

**Real bug fixed alongside the missing bound**: Hyperliquid's market-order reference price previously fell back to a
hardcoded `Decimal("100")` when the caller supplied none -- wrong for essentially every real asset (e.g. BTC), which
silently produced a nonsensical IOC limit price. Now fetches a REAL live mark price via a new `/info
type=metaAndAssetCtxs` call (mirrors the existing `/info` call pattern already used for `meta`/`clearinghouseState`)
when no caller reference price is given.

**Backward compatible**: the only real caller today, `perp_hedge_consumer.py` (`connector.place_order(...)` for both
Hyperliquid and Bybit venues), never supplies a reference `price` -- so Aster/Pacifica/Bybit's behavior is
byte-for-byte unchanged for it (still an unbounded venue-native market order); Hyperliquid gets a strictly-better
live-mark-price-based IOC fill in place of the dangerous `$100` fallback, with no interface break.

**Deliberately deferred (see the narrowed line-283 todo above)**: a resting-order or per-request expiry/deadline
bound. Verified none of the four venues expose a per-order good-til-date: Hyperliquid's order schema has only
ALO/IOC/GTC time-in-force; Aster's `timeInForce` enum is GTC/IOC/FOK/GTX/HIDDEN; Pacifica's `tif` enum is
GTC/IOC/ALO/TOB; all three venues' only expiry-shaped field is a request-SIGNATURE freshness window (Pacifica's
`expiry_window`, already handled by `_perp_idempotency.py`), unrelated to how long a resting order stays open.
Hyperliquid's exchange action DOES support a request-processing deadline (`expiresAfter`, verified via WebFetch:
top-level POST field alongside `action`/`nonce`/`signature`, rejects the whole action if not processed in time) --
NOT wired in this pass because `_hyperliquid_signing.sign_l1_action` has no existing plumbing for it and the docs are
ambiguous on whether it factors into the signed msgpack hash; getting that wrong risks a signature that's silently
NOT enforcing the deadline while looking correct locally -- a worse outcome than deferring cleanly with the research
already recorded here.

**Tests added**: `tests/defi_execution/unit/test_perp_order_bounds.py` (the shared module, fully isolated -- resolve/
reject/ceiling, bounded-price math both directions, bps-to-percent conversion); two new live-mode tests in
`tests/defi_execution/integration/test_hyperliquid_mock.py` (reference-price-given bounds into IOC without an extra
`/info` call; no-price-given triggers the live mark-price fetch and bounds around THAT); two new tests in
`test_aster_connector.py` (market-with-price converts to LIMIT+IOC; market-without-price stays unbounded MARKET,
unchanged); two new tests in `test_pacifica_connector.py` (`_build_order_params` carries `slippage_percent` for
market, omits it for limit); two new tests in `test_bybit_connector.py` (reference-price bounds into limit+IOC;
an absurd `max_slippage_bps` above the 20% ceiling is rejected before reaching the adapter).

**Also fixed in the same pass** (stale doc pointer, per the "misled you = fix it" rule): `aster.py`'s module
docstring cited a dead docs URL (`asterdex/api-docs/blob/master/aster-finance-api.md`, 404 -- the file moved under
`V3(Recommended)/EN/aster-finance-futures-api-v3.md` in a repo restructure); corrected in place.

`quality-gates.sh` green (270s, 9022 passed, sentinel matched committed HEAD exactly).

**This close-out todo's own done-when ("once every todo above is done or explicitly re-scoped") is NOT yet
satisfied** — the 3 open P0s above are genuine unresolved HIGH findings, not re-scoped/deferred work, so the
checkbox below stays `[ ]` rather than being falsely flipped. No production code was changed; this is a doc-accuracy
fix only (epic doc + this Progress Log entry).

**Correction (2026-08-21, slot-7)**: slot 10's "not recoverable" finding above applied only to slot 10's own
checkout — slot 7's original uncommitted WIP survived in this session's own worktree across the context-compaction
that produced it, and was completed and shipped as `execution-service@2d1766ef96` (see the "SHIPPED" entry earlier
in this same Progress Log, and the flipped checkbox at line 284). The close-out todo's P0 count above is therefore
stale by one: 2 open P0 fixes remain, not 3 — perp/CLOB slippage/deadline bounds (line 283) and native-REST
client-order-id idempotency (line 304). The close-out todo's own checkbox stays `[ ]` (still 2 genuine open P0s plus
the 2 unstarted audit phases), but its epic-doc correction should be re-run once those clear rather than trusted as
current. **Update (2026-08-21, slot-7): checklist point 4 (line 283) is now done — see the two Progress Log entries
below.** Only one todo remains open in this "DeFi by primitive — perp / CLOB on-chain" section: the close-out
epic-reflection todo above, whose own epic-doc correction should be re-run now that both P0s it counted are closed.

### 2026-08-21 — slot-7 Hyperliquid request deadline (checklist point 4, remainder) + EIP-712 chainId fix — SHIPPED

Landed as `execution-service@d4876e394e` (rebased during push onto 2 upstream commits; full QG re-ran green
post-rebase, 269s), post-push ancestry verified. Closes checklist point 4 in full — see the slippage-half entry
above (`execution-service@fc7835b13e`) for that half's design.

**Resolved the deferred uncertainty**: pulled `hyperliquid-dex/hyperliquid-python-sdk`'s `utils/signing.py` via
`gh api` (the authoritative reference, not a doc page) and confirmed `expires_after`/`expiresAfter` IS part of the
signed hash -- `action_hash()` appends `b"\x00" + expires_after.to_bytes(8, "big")` AFTER the vault marker, only
when not `None`. Implemented `_hyperliquid_signing.sign_l1_action(..., expires_after_ms=...)` matching this exactly;
`hyperliquid.py`'s `place_order()` gained a `deadline: int | None` param (absolute unix seconds, matching this
codebase's existing AMM-swap deadline convention), validated in-range (future, ≤300s ahead) before the idempotency
lock, converted to ms, folded into the signature, and added to the POST body's top-level `expiresAfter` field.

**Real bug found + fixed in the same pass**: `_hyperliquid_signing.py`'s EIP-712 domain `chainId` varied by
`testnet_mode` (1337 mainnet / 421614 testnet) -- the official SDK's `l1_payload()` confirms it's ALWAYS 1337 for L1
actions regardless of network; only the phantom-agent `source` field ("a"/"b") distinguishes mainnet/testnet. The
prior behavior would have produced an EIP-712 domain hash Hyperliquid's testnet endpoint could never verify --
every testnet order/cancel would have failed signature verification. `testnet_mode` is a real, live-wired config
option (used at both `place_order()` and `cancel_order()` call sites), so this had real (if perhaps not yet
exercised) blast radius, not a theoretical gap. Fixed by removing the `is_mainnet`-conditional chainId branch
entirely; `source` still varies as before.

**Tests added**: new `tests/unit/defi_execution/test_hyperliquid_signing.py` -- domain chainId asserted 1337 for
BOTH `is_mainnet=True` and `False` (regression for the bug above, via patching `eth_account.messages.
encode_typed_data` to capture the full EIP-712 message), plus an independent byte-for-byte reconstruction of the
`expires_after`-folded hash (not trusting the production code's own math) compared against the actual signature
output. Four new tests in `test_hyperliquid_mock.py`: deadline threads into the POST body's `expiresAfter` (ms);
omitted when not supplied (unchanged prior behavior); a past deadline is rejected before any network call; a
deadline further than 300s ahead is rejected. `quality-gates.sh` green (9028 passed, sentinel matched committed HEAD
before the push-time rebase; QG re-ran and stayed green after).

### 2026-08-21 — slot 21 close-out todo: epic W15 section re-confirmed (all P0 clear)

Re-ran slot 10's confirmation now that the 2 P0s slot-7 flagged as still-open at the time (perp/CLOB
slippage/deadline bounds line 283; native-REST client-order-id idempotency line 304) have both since landed —
verified directly via `grep -c '^- \[x\]'`/`'^- \[ \]'` against this file: 44 done / 10 open of 54 todos. Listed
every remaining `- [ ]` by line: 126 (P1 Orca/Raydium full account derivation), 188 (P1 sports-exchange audit,
unrun), 192 (P2 sports-unity audit, unrun), 213 (P2 Aave typed-params dead-code decimals), 215 (P2 Morpho
typed-params dead-code decimals), 217 (P1 Kamino market cross-check), 224 (P1 wire real on-chain calls behind the
staking fail-closed guards), 226 (P1 EigenLayer approval + Karak vault address), 332 (P1 native rate-limit/
blocking-sleep hardening), and this close-out todo itself. **Zero open P0s** — every remaining item is P1/P2 and
each already carries its own explicit scope + deferral rationale in its todo text (dead code confirmed via grep,
needs a vendored SDK/on-chain account fetch not yet available, etc.), satisfying this todo's own done-when ("done
or explicitly re-scoped"). Corrected the epic's W15 section in place with this accurate zero-P0 breakdown
(previously stale at "3 P0 fixes... blocking close-out", written before slot-7's two P0 fixes landed). Checkbox
flipped. No production code was changed — this is a doc-accuracy confirmation only.

### 2026-08-21 — slot 19 sports exchange adapter audit + close-out gate re-check

Dispatched from `plans/archive/issues/w15_close_out_gate_and_line_cap_2026_08_21.md`'s close-out gate-check todo
("once the 11 items are all done or explicitly re-scoped, re-run the gate-check"). Re-derived the current open-item
list first (`grep -n "^- \[ \]"`, not trusted from the issue doc's now-stale 2026-08-21 snapshot): 5 of the original
11 items were already done or explicitly re-scoped by prior sessions (Orca/Raydium partial-fix re-scope, Aave/Morpho
dead-code P2 deferrals, Kamino cross-check deferral, wire-real-on-chain-calls deferral, EigenLayer/Karak MEDIUM
follow-up, native rate-limit MEDIUM follow-up — 6 total, all carrying their own documented deferral reasoning), and
the CCXT/perp-CLOB/native-REST P0 groups the issue doc listed as open were also already fully landed. The two
**genuinely open, non-deferred** items were the sports-exchange and sports-unity audit phases — full security
reviews that had simply not started yet, not deferred-with-reasoning work.

Audited the sports-exchange group per the fixed seven-point checklist: `betfair.py`, `betfair_order_mapping.py`
(`_BetfairCanonicalOrderMixin`), `kalshi.py`, `matchbook.py`, `polymarket_clob.py`
(`sports_execution/adapters/exchanges/`), plus the thin delegating wrappers `polymarket_adapter.py` and
`sports_adapter.py` (`trade_execution/adapters/`) and the bookmaker-API group `api_football.py`/`odds_api.py`
(`bookmaker_api/`, `aggregator/`). `onexbet.py` no longer exists in the repo (only a stale `.pyc` remains) —
confirmed via `sports_handler.py`'s own comment and `sports_bookmaker_roster_classification_2026_08_21.md` that it
was retired as dead code the same day this plan's issue doc was filed; the plan's file list is stale on this one
name, corrected in place on the checkbox above.

- **Credential handling — PASS with one FINDING HIGH:** Betfair/Kalshi/Matchbook/Polymarket all inject credentials
  at construction and never log secret material. Kalshi's `_build_kalshi_headers()` has a real fail-open bug: on
  ANY `ValueError` while loading/signing with the RSA private key, it silently substitutes a raw SHA-256 digest of
  the message as the "signature" instead of raising (`kalshi.py:116-128`) — a broken/misconfigured key degrades
  into sending a fabricated signature rather than failing closed.
- **Signing/auth correctness — PASS:** Kalshi RSA-PSS, Polymarket L2 HMAC-SHA256 (timestamp+nonce present, replay
  window venue-side), Betfair/Matchbook session-token REST auth all match each venue's documented scheme; no
  private key/session token is transmitted in a body/URL beyond the documented header contract. (The Kalshi
  fallback above is a credential/correctness finding, not a scheme-correctness one — the primary RSA-PSS path
  itself is correct.)
- **Input validation before order write — FINDING HIGH (all four exchanges):** Betfair (`place_bet`,
  `place_order`), Kalshi (`place_bet`, `place_order`), Matchbook (`_submit_offer`), and Polymarket CLOB
  (`place_order`, `_submit_clob_order`) all cast caller stake/price/size directly to `float`/`int` before building
  the order payload with no local finite-positive or side/action allowlist check — the exact same finding class
  already fixed for the CCXT/perp-CLOB/native-REST groups elsewhere in this plan. Betfair additionally silently
  maps any non-"BACK" side string to "L" (lay) rather than rejecting it (`betfair_order_mapping.py:143`) — a wrong
  caller value flips the bet direction instead of erroring.
- **Slippage/deadline bounds — PASS/N-A:** all four are LIMIT-order exchanges/CLOBs where the caller-supplied price
  IS the bound (no unbounded-market-order path exists in this group, unlike the CeFi/perp CCXT group). One MEDIUM
  note: Polymarket's CLOB supports a GTD (good-til-date) time-in-force per its own docs, but this adapter only ever
  passes GTC/FOK/IOC through — a caller has no way to bound an order's resting lifetime. No todo added for this
  MEDIUM-only gap (consistent with how other MEDIUM-only findings were handled elsewhere in this plan).
- **Approval scope — PASS/N-A:** fiat/USDC.e wagering and CLOB order placement; no ERC-20/SPL token-approval path
  exists in this adapter group.
- **Idempotency/retry safety — FINDING HIGH (3 of 4 exchanges, Betfair split):** Betfair's canonical
  `place_order()` path (`betfair_order_mapping.py:155`) DOES thread `client_order_id` through as Betfair's own
  `customerRef` (venue-side dedup), but the older, still-live `place_bet()` legacy path (`betfair.py:398-421`)
  calls `_submit_place_orders()` with no customer_ref at all — zero idempotency on that path. Kalshi mints a fresh
  UUID every call unless the caller explicitly supplies one (a caller-level retry after a timeout doesn't reuse the
  same id, defeating Kalshi's own dedup). Matchbook has no client-order-id concept anywhere. Polymarket CLOB accepts
  a `client_order_id` parameter but never sends it to the venue or uses it to reconcile a retry — pure dead
  plumbing today.
- **Honest error handling — PASS:** all four raise `BetRejectedError`/`BookmakerUnavailableError` on a non-success
  response rather than fabricating success; unexpected exceptions are logged via `UNKNOWN_VENUE_ERROR_RECEIVED` and
  re-raised, never swallowed.

`api_football.py` and `odds_api.py` are read-only market-data adapters (get_odds only) that are, per their own
docstrings and the prior 2026-08-01 dead-code audit, not wired into any live execution path — checklist points 2-6
are N/A by construction (no write surface); points 1 and 7 PASS (credentials not logged; non-200 raises a real
error). No new finding recorded for either.

No production code or tests were changed for this audit-only unit (matches this plan's established pattern for
every prior audit phase). Four new P0/P1 triage todos added immediately after the existing Triage section todos,
above, covering the 4 distinct HIGH-finding groups found (Betfair legacy idempotency; Kalshi fail-open signing;
cross-venue client-order-id idempotency; cross-venue input validation). Checkbox for the sports-exchange audit
phase flipped above.

**Close-out gate re-check result: still NOT met.** The sports-unity audit phase (line 192, P2 —
`sports_execution/adapters/unity/`) remains genuinely unstarted, not deferred/re-scoped, so this todo's own
done-when ("every todo above is done or explicitly re-scoped") is not yet satisfied. The close-out checkboxes
(this section, and the sibling checkbox in
`plans/archive/issues/w15_close_out_gate_and_line_cap_2026_08_21.md`) stay `[ ]` — flipping them now would be a
false-progress claim. Remaining blockers as of this entry: the 4 new triage todos just added above, plus the
sports-unity audit phase (line 192) — 5 items, down from 11 at the issue doc's original count.

**Reopening note**: this session landed concurrently with slot 21's close-out confirmation directly above, which
flipped this plan's close-out checkbox to `[x]` on a "zero open P0s" basis — accurate at the moment slot 21 wrote
it (before this session's sports-exchange audit existed), but no longer accurate now that the audit above found 3
new P0 findings. Reverted the close-out checkbox back to `[ ]` in the same edit as this entry; slot 21's entry
above is left untouched as an accurate record of what was true at the time it was written.

### 2026-08-22 — slot 21 sports Unity subsystem audit

Reviewed `protocol.py` first, then `bridge.py`, `fill_reports.py`, `mock_feed_connector.py`, `multiplex.py`,
`rollover_tracker.py`, `sidecar.py`, and `turnover_tracker.py` against the fixed seven-point checklist. This is
the Python boundary around the Java Feed Connector; the mock is simulation-only and is not treated as a live venue.

- **Credential handling — PASS:** `SidecarConfig.credentials_ref` is a Secret Manager reference and
  `UnityBridge.authenticate()` forwards that reference rather than a private key or plaintext credential
  (`sidecar.py:39-47`; `bridge.py:132-154`). The Python layer does not log the reference or secret material. The
  mock echoes the reference in its test-only `AUTH_OK` payload (`mock_feed_connector.py:77-103`), which is not a
  production path but should not be copied into a real connector.
- **Signing/auth correctness — PASS at this boundary:** the Java connector owns venue authentication; the Python
  bridge only sends the configured reference, requires `AUTH_OK`, and moves to `FAILED` on `AUTH_FAIL` or a closed
  stream (`bridge.py:132-154`). No private key or request signature is constructed in these files.
- **Input validation before order write — FINDING HIGH:** `UnityBridge.place_bet()` and the public
  `UnityMultiplex.enqueue()` accept unchecked Decimal amounts/prices, arbitrary direction and empty identifiers,
  then `_encode_place_bet()` serializes them directly into `PLACE_BET` (`bridge.py:179-210,302-318`;
  `multiplex.py:64-92`). The fill parser has the corresponding boundary weakness: `_as_decimal()` accepts
  `NaN`/Infinity and negative values, and `attribute_unity_fill()` trusts the result (`fill_reports.py:104-226`).
  Unknown child venues raise `KeyError` outside the bridge's `UnityFillReportParseError` handler, so malformed
  attribution can terminate a pump cycle rather than become an explicit failed fill.
- **Slippage/deadline bounds — FINDING MEDIUM:** price is carried as the caller's bet price, but the Unity
  `PLACE_BET` catalogue has no caller deadline, expiry, or time-in-force field (`protocol.py:25-39`;
  `bridge.py:302-318`). A matched/unmatched order can therefore have no Python-side lifetime bound. This is not
  upgraded to HIGH because the external book controls matching semantics and the adapter does not expose a market
  order path separate from the supplied price.
- **Approval scope — PASS/N-A:** this subsystem places sports bets through the connector and has no token approval
  or allowance call in the reviewed files.
- **Idempotency/retry safety — FINDING HIGH:** `_pending_acks` only removes a client-order ID after an ACK; it does
  not reject duplicate placement IDs or deduplicate repeated `BET_ACK`/`BET_FILL` frames. `UnityMultiplex.drain()`
  moves messages into `_sent` before `sidecar.send()` succeeds, so a send exception after draining loses the
  retryable outbound record (`bridge.py:238-260`; `multiplex.py:95-109`). There is no durable sequence/client-order
  record across process restart.
- **Honest error handling — FINDING HIGH:** malformed frames become an `ERROR` from `SidecarProcess.recv()`, and
  explicit sidecar errors are returned in `PumpResult.errors` (`sidecar.py:201-215`; `bridge.py:245-260`). However,
  bad numeric fills can pass parsing or trigger an uncaught `KeyError`, and duplicate settlement fills are appended
  and counted repeatedly (`bridge.py:262-277`), allowing accounting to report a successful duplicate or crash
  instead of surfacing a single failed/reconciled event.

No production code or tests were changed for this audit-only unit. The three concrete HIGH findings are represented
by the Unity placement-validation, fill-boundary/error-handling, and sequence/client-order-idempotency follow-ups
added in the Triage section above. Checklist points 1, 2, and 5 are PASS/PASS/N-A; point 4 is recorded as a MEDIUM
follow-up-free finding under the plan's established policy for MEDIUM-only issues. The Unity audit checkbox is now
flipped with this evidence; the plan still has open triage work and is not ready for close-out.
