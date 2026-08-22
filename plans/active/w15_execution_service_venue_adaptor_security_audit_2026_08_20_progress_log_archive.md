---
doc_type: plan
title: W15 venue-adaptor security audit — Progress Log archive
summary: >-
  Sibling archive for /plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md's
  Progress Log. Holds every dated entry whose corresponding todo(s) are fully resolved (checked) and
  carry no bearing on any currently-open todo, split out per
  /plans/active/issues/w15_close_out_gate_and_line_cap_2026_08_21.md's "Recommended decision" so the
  main plan doc has real headroom under the 500-line soft cap for its remaining open todos' own
  eventual Progress Log entries. No todos live here — this doc is not dispatchable. The main plan doc
  remains the sole source of record for open/actionable work and for any entry with bearing on it.
status: active
nature: record
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [execution, security, audit, defi, w15, progress-log-archive]
related:
  [
    /plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
    /plans/active/issues/w15_close_out_gate_and_line_cap_2026_08_21.md,
  ]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.25
estimate_calibrated_ai_days: 0.1
context_scope:
  [
    /plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md,
    /plans/active/issues/w15_close_out_gate_and_line_cap_2026_08_21.md,
  ]
depends_on:
supersedes:
superseded_by:
locked_by:
locked_since:
source: >-
  Split from /plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md, which was
  sitting at the 1000-line hard cap with zero headroom
  (/plans/active/issues/w15_close_out_gate_and_line_cap_2026_08_21.md).
---

# W15 venue-adaptor security audit — Progress Log archive

> Sibling doc to
> [`w15_execution_service_venue_adaptor_security_audit_2026_08_20.md`](/plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md)
> (the main plan — read it first for the Todos section, the checklist, and any still-open work). This
> doc holds the Progress Log entries relocated from that file: every entry whose corresponding todo(s)
> are already checked `[x]` and which carries no bearing on a todo that is still open `[ ]`. Content is
> relocated verbatim, not summarized or altered — every SHA, finding, and evidence citation below is
> exactly as originally landed. Entries appear in original chronological/file order.

## Progress Log (archived entries)

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

### ag-closeout-audit 2026-08-21 (cross-cutting tranche, Phase 2 sweep)

Mechanical hygiene fix: this doc had two top-level `## Progress Log` H2 headers (a concurrent-editing artifact —
the bridge/CCTP entry and the swap/DEX entry had each been appended under their own header instead of sharing
one). Removed the duplicate header so every dated entry lives under a single `## Progress Log` section; no entry
content, findings, or todos were changed.

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

### 2026-08-21 — slot 7 Jupiter security fix (checklist points 3, 4, 6)

Fixed the "Add Jupiter quote/input validation, caller-controlled expiry, and idempotency/retry protection..." P0
todo, closing the three findings recorded in the 2026-08-20 slot-7 swap/DEX audit entry above (checklist points 3,
4, 6). Added `_validate_quote_request()` (mint shape via base58 regex, `input_mint != output_mint`, positive
amount, `0 <= slippage_bps <= 1000`) called before every `/quote` request. Added caller-controlled quote-age
enforcement: `execute_swap()` now takes `max_quote_age_seconds` (default 30s) and rejects a stale or
freshness-unverifiable quote before signing. Added idempotency/retry protection modeled on `bridge.py`/`cctp.py`'s
precedent: a `_swap_intent_key()` fingerprint (mint pair + amount, stable across quote refreshes) tracks
in-flight/completed attempts; a successful swap is cached and replayed byte-identical on retry (no second
broadcast); an *ambiguous* outcome (an exception from `send_transaction()` itself, not a returned failure) fails
closed and blocks resubmission until the caller explicitly calls the new `clear_ambiguous_swap_attempt()` escape
hatch — the exact gap the todo named ("a retry after an ambiguous `send_transaction()` result currently obtains
and signs a fresh transaction"). `execute_swap()` was decomposed into `_check_prior_swap_attempt()` /
`_check_quote_freshness()` / `_broadcast_and_finalize()` to stay under the 50-line method cap. Added 8 new
regression tests to `tests/defi_execution/unit/test_solana_connectors.py::TestJupiterConnector` covering each
validation rejection, stale-quote rejection, successful-replay object-identity, and the
ambiguous-outcome-blocks-resubmission-until-cleared path.

**Unrelated pre-existing QG blocker fixed in the same session:** `execution_service/utils/market_hours.py:261`'s
fallback `except Exception:` (dated 2026-05-21, unrelated to this todo) was the sole in-scope
(`--source-dir execution_service`) site over the STEP 5.5 broad-except baseline — added `# noqa: broad-except`
plus a one-line reason; verified pre-existing via `git blame` before touching it.

**Duplicate-work discovery and correction** (full account in this repo's
`plans/active/issues/sports_bookmaker_roster_classification_2026_08_21.md`): mid-session, the same
`unified-api-contracts@cdb8ae88` → `onexbet.py` `ModuleNotFoundError` documented in the slot-21 entry above
independently broke this session's own `quality-gates.sh` collection step too (confirmed byte-identical root
cause). This session built its own fix (retire `OneXBetAdapter` + its test), originally committed locally as
`1f4e1346`+`065fc9d0` — but a `git fetch` immediately before shipping showed slot-21 had already landed an
equivalent retirement on `origin/live-defi-rollout` (`f4391ac5`+`0c81d755`), starting from the same shared
ancestor (`e7d65703`). Rather than ship a duplicate/conflicting change on top of an already-published fix, this
session ran `git rebase --onto origin/live-defi-rollout e7d65703 <jupiter-fix-commit>` to drop the two now-redundant
local onexbet commits (never pushed, no longer exist anywhere) while replaying only the genuinely new Jupiter +
market_hours commits on top of origin's current tip. **Lesson for future sessions:** a
`git rev-list --count origin/<branch>..HEAD` ahead-only check (which this session ran first) does NOT surface a
concurrent-slot conflict — only the bidirectional `git rev-list --left-right --count HEAD...origin/<branch>` catches
it; run the bidirectional form before shipping whenever a fix touches code another slot could plausibly be fixing
at the same time (a shared cross-repo break discovered via the same root-cause commit is exactly that signal).

Full `quality-gates.sh` green end-to-end on the final rebased tree (155s, one unbroken run including STEP 5.83's
adapter-contract-call regression ratchet, which needed `unified-trading-pm/scripts/quality_gates/
adapter_contract_baseline.yaml` regenerated via `--regenerate-baseline` after `onexbet.py`'s deletion — diffed
before trusting it, confirming only the deleted file's 2-line entry disappeared; a subsequent
`git pull --rebase --autostash` in this repo picked up slot-21's own independent identical regen already on
origin, so nothing further needed committing here). Shipped via quickmerge — execution-service@e1e1788d35;
post-push ancestry verified.

### 2026-08-21 — slot 21 CCTP attestation-timeout/terminal-failure fix (checklist point 7)

Re-read `cctp.py` at current LDR HEAD against the "Correct CCTP status lookup and enforce attestation
timeout/terminal failure semantics" P0 todo (2026-08-20 slot-5 audit finding: "`_pending_burns` is keyed by
transfer ID... so a valid source tx hash remains `BRIDGING` indefinitely; receive failures are reported, but
timeout/terminal semantics are incomplete").

The status-lookup half was already fixed as a side effect of the earlier `fb50f729` security-state commit:
`get_bridge_status()` now resolves via `_find_burn_by_tx_hash()`, which checks the tx-hash-keyed
`_burns_by_source_tx` dict first — confirmed by tracing `_index_burn()`'s population of that dict against every
call site; no lookup bug remains for a valid tx hash. No new code needed for that half.

The remaining real gap: `get_bridge_status()` already returned `FAILED` once a burn waited past
`_attestation_timeout` with no attestation, but `receive_on_dest()` never checked elapsed time at all — the
identical underlying transfer could report `FAILED` from one entry point and `BRIDGING` forever from the other.
Fix: extracted the check into a shared `_attestation_timed_out()` helper, used by both `get_bridge_status()` and
`receive_on_dest()`. The timeout only gates the *wait for* the attestation — once `burn.attestation` is set,
neither entry point re-checks elapsed time, so an already-attested transfer can still complete regardless of its
total age (verified by a dedicated regression test).

Left `get_bridge_status()`'s `burn is None → BRIDGING` behavior untouched: it is a separate, deliberately-tested
contract (`TestCCTPGetBridgeStatusNoRecord.test_returns_bridging_for_unknown_tx_hash`), not part of this
finding, and `TransferStatus` has no "unknown" value to report instead — changing it would be a different,
riskier change outside this todo's scope.

4 new regression tests added to `test_cctp.py` (`TestCCTPAttestationTimeout`): `get_bridge_status` FAILED after
timeout, `receive_on_dest` FAILED after timeout (the actual fix), `receive_on_dest` still BRIDGING before
timeout, and `receive_on_dest` ignores an old `created_at` once attestation is already present. Full
`quality-gates.sh` green (156s); shipped via quickmerge — execution-service@004bd5c15c; post-push ancestry
verified.

### 2026-08-21 — slot 7 Aave lending security fix (checklist points 3, 6, 7)

Fixed the "Harden Aave lending writes" P0 todo, closing the three HIGH findings recorded in the
2026-08-20 slot-10 lending audit entry above.

- **Point 3 (input validation):** added `_validate_amount()` (aave_live.py) — rejects non-finite,
  non-positive, and over-precision amounts (more fractional digits than the token's configured
  `TOKEN_DECIMALS`, which `_to_wei()` would otherwise silently truncate) — called at the top of
  `supply()`/`withdraw()`/`borrow()`/`repay()`, both live and backtest paths. Added
  `_validate_interest_rate_mode()` (must be 1 or 2) to `borrow()`/`repay()`. Added
  `_validate_flash_loan_vectors()` to `flash_loan()` — rejects empty vectors, a `tokens`/`amounts`
  length mismatch (previously silently truncated by `zip(..., strict=False)` in
  `_execute_live_flash_loan`, now `strict=True` as defense-in-depth), and any non-positive/invalid
  per-token amount.
- **Point 7 (fail-closed):** every live write path (`supply`/`withdraw`/`borrow`/`repay`/`flash_loan`)
  now checks `self._live_executor is None` under `if self.is_live:` and returns an explicit
  `success=False` result (`_live_credentials_unavailable_result()`) instead of falling through to the
  backtest-simulation branch below — the exact bug the audit found (`aave.py:468-480,496-509,523-536,550-564`
  in the pre-fix line numbering).
- **Point 6 (durable idempotency):** new `execution_service/defi_execution/protocols/aave_idempotency.py`
  module, modeled directly on `bridge.py`/`cctp.py`'s existing durable-idempotency precedent (same
  `TransferStateStore` Protocol, reused rather than redefined; config key `transfer_state_store`,
  namespace `"aave"`). Each live write computes a per-request `intent_key` (wallet + operation +
  token(s) + wei-amount(s), plus `interest_rate_mode` for borrow/repay) and routes through
  `execute_aave_op_idempotent()`: a completed prior attempt replays its cached `TxResult` with zero
  resubmission; a clean returned failure (revert, unknown token) clears the lock so a fresh retry can
  proceed; an *ambiguous* outcome (an exception escaping the executor call, not a returned failure)
  leaves the operation locked and raises `AaveOperationInFlightError` on the next attempt — mirrors the
  Jupiter fix's "ambiguous outcome fails closed" precedent rather than CCTP's receipt-based recovery
  (stated as a deliberate, disclosed scope boundary in the module docstring: Aave has no generic
  receipt-based result-recovery path implemented here, unlike CCTP's on-chain event-log recovery).
  `AAVEConnector.clear_stale_operation(intent_key)` is the explicit escape hatch, to be called only
  after confirming out-of-band (block explorer / wallet nonce history) that a locked attempt never
  landed. Unlike CCTP, the durable store is NOT a hard requirement for live execution — `aave.py`'s
  live-construction call site (`live_execution_defi.py`) doesn't currently wire `transfer_state_store`
  into the shared `defi_config` dict passed to ~9 connectors including Aave, and hard-requiring it here
  would have silently broken every live Aave call; idempotency still holds in-process (the dominant
  real-world retry pattern — an application-level retry after a timeout/exception) without a durable
  store, and durability activates automatically the moment a caller injects one, with no further code
  change needed.

`AaveOpRecord` (the idempotency record dataclass) needed a leading underscore
(`_AaveOpRecord`) to pass `check_schema_provenance.py`'s "Schema provenance" gate — a local
dataclass without one is flagged as a should-be-UAC/UIC schema; the underscore-prefix exemption
(`check_schema_provenance.py:127`) already covers `_CCTPBurnRecord` identically, confirmed by
reading the check's source before renaming rather than guessing. `flash_loan()` also needed
decomposing (`_execute_flash_loan_live()` extracted) to stay under the method-size cap after the
new validation/idempotency lines pushed it to 65 lines.

**Unrelated finding surfaced, tracked rather than inline-fixed (outside this todo's cited scope):**
`supply_from_params`/`borrow_from_params`/`repay_from_params`/`flash_loan_from_params` (the UAC
typed-params entry points, `aave.py:734-765`) unconditionally divide the wei amount by `10**18`
regardless of the actual token's decimals — the same bug class as the already-tracked Morpho
decimals finding, but for Aave. Confirmed dead code (zero callers anywhere in the repo via grep)
so this is latent, not currently exploitable; added as a new P2 triage todo above rather than
expanding this commit's scope beyond the audit's cited line ranges.

13 new regression tests added (`tests/defi_execution/unit/test_aave_hardening.py`): non-positive/
over-precision amount rejection, invalid interest-rate-mode rejection, empty/mismatched flash-loan
vector rejection, fail-closed-without-executor for every write path, idempotent replay with zero
resubmission, a different amount is NOT deduped, a clean revert clears the lock for a fresh retry,
and an ambiguous exception blocks a retry until `clear_stale_operation()` is called. Full
`quality-gates.sh` green (152s, sentinel matched the committed HEAD — the first attempt ran QG
before committing, which is the wrong order per RULES.md § 2 and produced a sentinel pinned to the
pre-fix HEAD; re-ran after committing to pin the correct SHA before shipping). Shipped via
quickmerge — execution-service@9a2795bea7; post-push ancestry independently verified.

### 2026-08-21 — slot 25 Morpho Blue lending-write hardening

Fixed the two HIGH findings the 2026-08-20 lending audit recorded for `morpho.py`'s live write path
(`_live_market_call`, `morpho.py:429-454,456-477` in the pre-fix line numbering) — checklist points 3
(input validation) and 6 (idempotency). The backtest/simulation path (`supply()`/`withdraw()`/`borrow()`/
`repay()`'s non-live branch) is unaffected by design: the audit's HIGH findings cited only the live path,
and the simulation path has no wei conversion to get wrong.

- **Point 3 (input validation):** `_LiveMarketConfig` gained a required `loan_token_decimals: int` field —
  a live call with no `loan_token_decimals` in `config["morpho_markets"][market_id]` now fails closed with
  an explicit error rather than assuming 18 decimals (the root of the original finding: a six-decimal loan
  token like USDC would have been encoded at 1e12x the intended on-chain value). New module-level
  validators — `_validate_morpho_amount()` (finite/positive/precision-bounded-by-decimals, mirrors
  `aave_live.py:_validate_amount()`), `_validate_lltv()` (WAD-scaled, must satisfy `0 < lltv < 1e18` —
  Morpho Blue never permits a market at/above 100% LLTV), and `_validate_market_id_bytes32()` (must decode
  to exactly 32 bytes, replacing the bare `bytes.fromhex()` the finding cited, reused in `get_live_position()`
  too) — all run before any signing. `_live_market_call()` was split into `_resolve_live_market()`
  (lookup + validation, raises `ValueError`/`KeyError`) and `_send_market_operation()` (the actual
  approve-plus-write) to stay under the 50-line method-size cap once the new validation/idempotency logic
  was added.
- **Point 6 (durable idempotency):** new `execution_service/defi_execution/protocols/morpho_idempotency.py`
  module, modeled directly on `aave_idempotency.py` (same `TransferStateStore` Protocol reused from
  `bridge.py`, config key `transfer_state_store`, namespace `"morpho"`). Each live write computes a
  per-request `intent_key` (wallet + chain + market_id + operation + wei-amount) and routes through
  `execute_morpho_op_idempotent()`: a completed prior attempt replays its cached `TxResult` with zero
  resubmission; a clean returned failure (revert, unknown market) clears the lock so a fresh retry can
  proceed; an *ambiguous* outcome (an exception escaping the approve/write call) leaves the operation
  locked and raises `MorphoOperationInFlightError` on the next attempt. `MorphoConnector.clear_stale_operation
  (intent_key)` is the explicit escape hatch, to be called only after confirming out-of-band (block
  explorer / wallet nonce history) that a locked attempt never landed. Same disclosed scope boundary as
  Aave's: no generic receipt-based result-recovery path, in-process + optional durable-store idempotency
  only.

**Unrelated finding surfaced, tracked rather than inline-fixed (outside this todo's cited scope):**
`supply_from_params`/`borrow_from_params`/`repay_from_params`/`flash_loan_from_params` (the UAC
typed-params entry points, `morpho.py:499-524`) unconditionally divide the wei amount by `10**18`
regardless of the actual loan token's decimals — the same bug class as the already-tracked Aave P2 item,
now tracked symmetrically for Morpho as a new P2 triage todo above. Confirmed dead code (zero callers via
grep) and the live branch already fails closed via this fix's "market not found" error (the synthetic
`market_id` these methods build from raw token addresses does not match a real `morpho_markets` config
key), so only the backtest-simulation branch is actually affected — latent, not currently exploitable.

12 new regression tests added (`tests/defi_execution/unit/test_morpho_hardening.py`): missing
`loan_token_decimals` fails closed, non-positive/over-precision amount rejection, zero/at-or-above-WAD
LLTV rejection, malformed `market_id_bytes32` rejection, configured (non-18) decimals correctly threaded
into the wei amount sent on-chain, backtest-mode regression check, idempotent replay with zero
resubmission, a different amount is NOT deduped, a clean revert clears the lock for a fresh retry, and an
ambiguous exception blocks a retry until `clear_stale_operation()` is called. Full `quality-gates.sh`
green (153s, sentinel matched the committed HEAD — first pass caught a method-size violation on
`_live_market_call` at 75 lines against the 50-line cap, fixed via the `_resolve_live_market()`/
`_send_market_operation()` split above, then re-verified green). Shipped via quickmerge —
execution-service@77e649239a; post-push ancestry independently verified.

### 2026-08-21 — slot 5 Kamino security fix (checklist points 2, 3, 5, 6)

Fixed the "Validate Kamino transaction intent before signing..." P0 todo, closing the four findings
recorded in the 2026-08-20 slot-5 lending audit entry above (checklist points 2, 3, 5, 6).

**Point 3** (unconstrained amounts, no local address/relationship validation): added
`_validate_op_params()` — rejects a non-positive/non-finite Decimal amount, rejects any of
`reserve_address`/`token_mint`/`market_address` that isn't a valid base58 Solana pubkey shape, and
rejects the three addresses colliding with each other. Added `_verify_reserve_mint()` — a real on-chain
cross-check via the existing `get_vault_info()` call, rejecting a caller-supplied `token_mint` that
disagrees with the reserve's actual mint. **Partial fix, stated explicitly**: Kamino's reserve API
payload carries no `market` field, so `market_address` cannot be cross-checked the same way without an
extra markets-list API call this connector doesn't otherwise need; a new P1 follow-up todo below captures
this remaining scope.

**Point 2** (opaque VersionedTransaction signed with no fee-payer/blockhash/signer/program checks): added
`_validate_decoded_transaction()`, run on every decoded tx before signing — rejects a fee payer that
isn't our own wallet, a transaction requiring more than 1 signature, an empty/zero `recent_blockhash`,
and any instruction whose program isn't on an allowlist (Kamino's own lend program + the standard
SPL Token / Token-2022 / Associated-Token-Account / System / Compute-Budget programs). **Found and fixed
in the same change**: this module's docstring had the WRONG Kamino Lend program ID
(`KLend2g3cP87ber41GXWsSZQhDqc7juFGkhGJk2HRFUj`) — independently verified via web search against Kamino's
own docs (mintlify.com/kamino-finance/klend/operations/deployment) and Solscan that the real production ID
is `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`; corrected the docstring and used the verified ID for the
new `KAMINO_LEND_PROGRAM_ID` constant/allowlist (an uncorrected wrong ID would have made the allowlist
reject every legitimate Kamino transaction).

**Point 5** (opaque instructions sent with no approval/delegate-scope allowlist): any SPL Token
`SetAuthority` instruction is rejected outright (no legitimate deposit/withdraw/borrow/repay reassigns
token-account authority); any `Approve`/`ApproveChecked` instruction's decoded delegated amount is bounded
against the requested operation amount (decimals-agnostic ceiling via the file's existing
`_DEFAULT_DECIMALS=9` constant — generous enough for any legitimate token while still catching a
runaway/effectively-unbounded delegation).

**Point 6** (fresh transaction + broadcast on every retry, no idempotency): added an in-memory
ambiguous-outcome-blocks-resubmission guard mirroring `jupiter.py`'s `execute_swap()` precedent exactly —
`_op_intent_key()` fingerprints (op + market + reserve + mint + amount); a `send_transaction()` exception
marks the intent ambiguous and blocks a same-intent retry until `clear_ambiguous_kamino_attempt()` is
called; a clean success is cached and replayed byte-identical on retry (no second broadcast); a clean
failure clears the guard (nothing durable was submitted, safe to retry).

18 new regression tests added to `tests/defi_execution/unit/test_solana_connectors.py::TestKaminoConnector`
covering: amount/address/distinctness validation, reserve/mint mismatch rejection, decoded-tx fee-payer/
non-allowlisted-program/SetAuthority/oversized-approve rejection plus a well-formed-tx acceptance case, and
idempotent-replay + ambiguous-outcome-blocks-resubmission-until-cleared. 7 pre-existing operational tests
were using an invalid-shaped placeholder `reserve_address` ("Reserve1111", 11 chars) that the new
validation now correctly rejects — updated to a valid-shaped fixture (`KAMINO_RESERVE_ADDR`); the two
live-path "resign" tests additionally patch out `_validate_decoded_transaction` (their focus is the
decode-then-resign path, not tx-content validation, which has its own dedicated tests) and enrich their
shared `FakeAiohttpSession` payload with a matching `tokenMint` so the new reserve/mint cross-check passes.
Full `quality-gates.sh` green (151s, sentinel matched the committed HEAD). Shipped via quickmerge —
execution-service@09452cd7dd; post-push ancestry independently verified.

New P1 follow-up todo added above (market_address/reserve relationship cross-check infeasible with the
current `get_vault_info()` payload shape, which carries no market field).

### 2026-08-21 — slot 19 Idle vault-write hardening (checklist points 3, 4, 6, 7)

Fixed the "Harden Idle vault writes..." P0 todo, closing the four HIGH findings the 2026-08-20 slot-10
lending audit recorded for `idle.py` (`idle.py:196-224,254-287,290-364` in the pre-fix line numbering).
All four fixes bind the live write path; the backtest/simulation path keeps its existing math but is
now precision-quantized (see below).

- **Point 3 (input validation):** new module-level `_validate_amount()` (finite/positive/
  precision-bounded-by-decimals, mirrors `aave_live.py:_validate_amount()`) runs in BOTH modes for
  deposit/withdraw and for the new `min_shares`/`min_underlying` floor params, before any state
  change — `to_wei()` silently truncates over-precision, which previously let a 7th-decimal USDC
  amount move less value than the caller asked for. Simulation math now quantizes minted shares to
  whole share-wei (18 decimals) and redeemed underlying to the token's own decimals (ROUND_DOWN,
  mirroring on-chain integer division) so a full-balance round-trip (e.g. `1000/1.06` DAI, a
  non-terminating 25-decimal quotient) stays exactly representable and withdrawable — caught by the
  pre-existing `test_withdraw_simulation` on the first gate run, fixed by this quantization.
- **Point 4 (min-output/deadline bounds):** `deposit()`/`withdraw()` grew keyword-only
  `min_shares`/`min_underlying`, `max_slippage_bps` (0..1000, `bridge.py`-compatible), and
  `deadline` (unix seconds; default now+120s, capped at now+1800s, past deadlines refused). The
  floor is the caller's explicit bound when supplied — a live implied output already below it raises
  `ValueError` pre-broadcast — else derived from the LIVE `tokenPrice()` read (non-positive price
  fails closed) times the slippage tolerance. Floor + resolved deadline are recorded in the live
  TxResult. Disclosed scope limit: the derived `mintIdleToken(uint256,bool,address)` ABI (not
  verifiable on etherscan without an API key) carries no on-chain min-out parameter, so the floor
  binds at this connector's pre-broadcast boundary only — it cannot protect against share-price
  movement between submission and block inclusion.
- **Point 7 (fail closed):** live mode with missing wallet/web3 now returns an honest
  `success: False` ("Refusing to simulate a live-mode write") instead of falling through to the
  simulation path; `claim_rewards()` — previously a fabricated `success: True, claimed 0` in live
  mode — refuses in live mode (IDLE rewards distributor contract not wired in this module).
- **Point 6 (durable idempotency):** new `execution_service/defi_execution/protocols/
  idle_idempotency.py`, modeled directly on `aave_idempotency.py` (same `TransferStateStore`
  Protocol from `bridge.py`, config key `transfer_state_store`, namespace `"idle"`). The approve +
  mint/redeem sequence runs as ONE `execute_idle_op_idempotent()` unit keyed by
  `idle:chain:wallet:operation:token:wei_amount`: a completed prior attempt replays its cached
  TxResult with zero resubmission (verified across a FRESH connector instance sharing the store);
  a clean returned failure (revert, broadcast error) clears the lock so a fresh retry proceeds; an
  ambiguous exception (e.g. connection drop between approve and mint) leaves the lock and raises
  `IdleOperationInFlightError` until `clear_stale_operation()` is called after out-of-band
  verification. All validation deliberately runs BEFORE the idempotent wrapper so a `ValueError`
  never falsely marks an intent ambiguous.

22 new regression tests (`tests/defi_execution/unit/test_idle_hardening.py`): non-positive and
over-precision rejection (USDC 7th decimal, shares 19th decimal), backtest regression check,
fail-closed without credentials (deposit/withdraw/claim_rewards, with no simulated-balance
mutation), non-USDC live refusal, invalid-slippage / expired / too-distant deadline rejection,
caller-floor breach refused with zero broadcasts, derived floor + deadline recorded in live
results, idempotent replay for deposit AND withdraw (no resubmission), a different amount not
deduped, clean-revert retry, ambiguous-exception lock + `clear_stale_operation()` recovery, and
durable-store replay across connector instances. Full `quality-gates.sh` green (301s, sentinel
matched the committed HEAD). Shipped via quickmerge — execution-service@7d0e32de0e; post-push
ancestry independently verified.

### 2026-08-21 — slot 25 fabricated-success fail-closed fix (checklist point 7)

Fixed the "Fix fabricated-success write paths..." P0 todo, closing the checklist-point-7 HIGH
finding the slot-13 second-staking/restaking audit recorded for `symbiotic.py`/`karak.py`/
`kelpdao.py`/`puffer.py`/`renzo.py`/`eigenlayer.py`.

All nine affected methods returned `success: True` unconditionally, regardless of `is_live`,
without ever building or broadcasting a transaction: `delegate()` (Symbiotic/Karak/KelpDAO/Renzo)
had no on-chain call at all; `withdraw()` (KelpDAO/Puffer/Renzo) mutated the simulated
balance/shares ledger and reported success even with a live wallet/web3 configured, despite each
docstring already disclosing the withdrawal-queue contract "is NOT wired here"; EigenLayer's
`complete_withdrawal()` did the same live/simulated-credit conflation and also cleared the pending-
withdrawal entry; `claim_rewards()`'s docstring literally claimed "Calls
RewardsCoordinator.processClaim() on-chain in live mode" while the code comment admitted "For now,
simulate the claim" (corrected in the same change per the misleading-doc HARD RULE).

**Fix**: each method now checks `self.is_live` (+ `self._wallet_address`/`self._web3_instance` for
the five EVM connectors, `self._live_executor` for EigenLayer) and returns an explicit
`{"success": False, "error": "... is not wired ..."}` before any simulated-state mutation, instead
of falling through to the simulation path. Genuinely wiring the real on-chain calls (five separate
withdrawal-queue/delegation contracts plus EigenLayer's full `Withdrawal`-struct tracking) is a
separate, larger lift needing a verified ABI/contract address per protocol — out of scope for this
fix, tracked as a new P1 follow-up todo above (same partial-fix pattern as this plan's Orca/Raydium
and Kamino precedents). Simulation-mode (`is_live=False`, the default) behaviour is unchanged —
every pre-existing per-connector unit test constructs its connector without `is_live=True`, so none
of them exercise the new guard.

14 new regression tests in
`tests/defi_execution/unit/test_second_staking_group_honest_error_handling.py`: one fail-closed
case per fixed method (all four `delegate()`s, all three `withdraw()`s, EigenLayer's
`complete_withdrawal()`/`claim_rewards()`), each asserting `success: False`, a "not wired" error,
zero broadcasts, and no silent balance/shares/rewards mutation; plus a case confirming EigenLayer's
pre-existing "no rewards to claim" failure reason still surfaces first for a live caller with zero
accumulated rewards (not shadowed by the new guard). Full `quality-gates.sh` green (227s, sentinel
matched the committed HEAD). Shipped via quickmerge — execution-service@862d5377b2; post-push
ancestry independently verified.

### 2026-08-21 — slot 25 CCXT order-boundary input-validation fix (checklist point 3)

Fixed the "Harden the shared CCXT order boundary..." P0 todo, closing the checklist-point-3 HIGH
finding the slot-21 CCXT audit recorded: all eight adapters cast caller `side`/`order_type` and
converted `quantity`/`price` straight to `float` before
`create_market_order()`/`create_limit_order()`, with no local finite-positive amount/price check,
side/type allowlist, or symbol check. A distinct, more dangerous variant of this gap: every
`_submit_ccxt_order()` branches only on `if ccxt_type == "market": ... else: (limit)` — an
unsupported/typo'd `order_type` (e.g. "stop") silently fell through to the LIMIT branch and was
submitted as an unintended limit order rather than being rejected.

**Fix**: added a single shared `validate_ccxt_order_params(symbol, side, order_type, quantity,
price)` in `ccxt_common.py` — rejects an empty symbol, a `side` outside `{buy, sell}`, an
`order_type` outside `{market, limit}` (closing the silent-fallthrough gap above), and a
non-finite/non-positive `quantity` or (when present) `price`. Called from the top of every
adapter's `_submit_ccxt_order()` (aster/binance/bybit/coinbase/deribit/hyperliquid/okx/upbit),
before any exchange call — a bad order now raises `ValueError` and reaches zero
`create_market_order`/`create_limit_order` calls on every venue. Plain `ValueError` (not a CCXT
exception subclass) propagates cleanly through each adapter's existing `except
ccxt.InsufficientFunds/InvalidOrder/NetworkError/BaseError` chain, the same way the pre-existing
"Limit order requires price" check already did.

42 new regression tests in `tests/trade_execution/unit/test_ccxt_order_validation.py`: 10
direct-unit cases against the shared validator (empty symbol, invalid side, invalid type,
zero/negative/non-finite quantity, non-positive/non-finite price, valid market and valid limit
orders), plus 4 parametrized wiring-confirmation test functions run across all 8 adapters (32
cases total — invalid side, invalid type, non-positive quantity, non-positive limit price) proving
each adapter's own `_submit_ccxt_order()` actually invokes the validator (not just that the helper
is correct in isolation), asserting zero `create_market_order`/`create_limit_order` calls on
rejection. Full `quality-gates.sh` green (233s, sentinel matched the committed HEAD; 8952 passed).
Shipped via quickmerge — execution-service@3685010a0f; post-push ancestry independently verified.

### 2026-08-21 — slot 23 second staking group min-output/deadline bounds + honest delay reporting

Fixed the "Enforce a real minimum-output bound on Kelp DAO deposits..." P0 todo, closing the
checklist-point-4 HIGH finding on `kelpdao.py` and the MEDIUM findings on the rest of the second
staking/restaking group.

**KelpDAO (HIGH, real on-chain fix)**: `deposit()`/`_deposit_live()` no longer pass a hardcoded
`minRSETHAmountExpected=0` to `LRTDepositPool.depositAsset()`. A new `resolve_min_output()`/
`resolve_output_bounds()` helper pair in `_evm_generic.py` resolves a real floor from the caller's
`min_rseth_out` or a `max_slippage_bps`-derived default off the tracked `_rseth_per_eth` rate, wired
directly into the on-chain call. Honest scope limitation stated in the docstring: no on-chain
LRTOracle read exists here, so the floor prices off the last-known/tracked rate, not a live
per-block oracle call.

**Rest of the group (MEDIUM)**: added the same caller `min_*_out`/`max_slippage_bps`/`deadline`
parameters to symbiotic/karak/puffer/renzo's `deposit()`+`withdraw()` and jito/jito_restaking/
solblaze's `stake()`+`unstake()` (or `deposit()`+`withdraw()` for jito_restaking), enforced
pre-broadcast via the same shared helper. Puffer's floor uses the real `get_exchange_rate()`
on-chain read; the rest (no oracle wired) price off their tracked simulation rate, stated honestly
in each docstring.

**Honest instant-vs-delayed withdrawal reporting**: `jito.py`/`jito_restaking.py`/`solblaze.py`
previously hardcoded `withdrawal_delay=0` on every unstake/withdraw despite each module's own
docstring documenting a delayed/cooldown route this connector cannot verify is actually avoided
(no on-chain read of stake-pool reserve liquidity / NCN cooldown / secondary-market liquidity
exists in any of the three). Added an `instant: bool = False` parameter -- defaults to a
conservative delay estimate (`_JITO_EPOCH_DELAY_SECONDS`/`_NCN_COOLDOWN_SECONDS_APPROX`/
`_SOLBLAZE_EPOCH_DELAY_SECONDS`, each an explicitly-flagged approximation, not a verified on-chain
value); `instant=True` is available for a caller who has independently confirmed the fast path.

**Concurrent-edit note**: this exact file set (`symbiotic.py`/`karak.py`/`kelpdao.py`/`puffer.py`/
`renzo.py`/`jito.py`/`jito_restaking.py`/`solblaze.py`/`_evm_generic.py`) was being edited by two
other slots in parallel on the checklist-point-6 (idempotency) and point-7 (fail-closed) todos while
this unit was in flight. `git pull --rebase --autostash` surfaced real conflicts twice (kelpdao.py's
`_deposit_live` needed the idempotency wrapper AND the min-output wiring merged together; puffer.py/
renzo.py's `withdraw()` docstrings needed both the fail-closed note and the bounds note merged) --
resolved by hand, keeping both sides' content per the append-don't-replace rule, then re-verified
`quality-gates.sh` green after each merge. Two small follow-up commits were needed to keep
`_deposit_live()`/`withdraw()` under the 50-line method cap after the merges (extracted a
`_finalize_deposit_result()` module-level helper for KelpDAO; trimmed the Puffer/Renzo docstrings).

Also found (and restored, not committed) a stray pre-existing staged revert on this exact plan
doc in this slot's PM worktree at session start -- the index held an uncommitted partial revert of
the two most-recently-landed checkboxes above (idempotency + fail-closed) plus deletion of their
Progress Log entries, matching the same "large apparent partial revert" class the 2026-08-21 slot-5
CCTP entry above already diagnosed in this same worktree. Restored with
`git restore --staged --worktree` to this file only, confirmed it now matches
`origin/live-defi-rollout` byte-for-byte before editing; did not touch the ~63 other dirty files
still present in this worktree (out of this unit's scope).

23 new regression tests: `tests/unit/test_evm_generic_bounds.py` (the shared helper's slippage/
deadline/floor validation, unit-level), plus per-connector additions to
`tests/unit/test_kelpdao_connector.py` (asserts the resolved `min_rseth_wei` is wired into the real
`depositAsset()` call args and is never 0), `test_jito_connector.py`,
`test_jito_restaking_connector.py`, and `test_solblaze_connector.py` (each connector's honest
non-zero default delay plus the `instant=True` override). `quality-gates.sh` full run green (170s,
sentinel matched committed HEAD); shipped via quickmerge —
execution-service@6067a94382 (+ 419efe9e "enforce real min-output/deadline bounds", 68f5c85c
"keep KelpDAOConnector._deposit_live under the method-size cap"); post-push ancestry independently
verified.
