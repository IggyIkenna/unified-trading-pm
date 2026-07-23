---
doc_type: issue
title: Cross-Client Funds Isolation — Retroactive Audit (execution-service, 2026-05-20)
summary:
status: ACKED-INTO-CODE
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-20
locked_by: live-defi-rollout
source:
  [
    /codex/04-architecture/client-funds-isolation.md (HARD RULE SSOT),
    plans/active/per_client_isolation_and_venue_fanout_topology_2026_05_20.md (Group H plan),
  ]
consumer: [slot 7 Phase 6 — TransferCoordinator facade builder]
priority: P2
archived: 2026-05-22
---

> **[ACKED-INTO-CODE]** Archived 2026-05-22. TransferCoordinator facade shipped in
> `per_client_isolation_and_venue_fanout_topology_2026_05_20.md` Phase 5 (`[x] ✅` — thread-safe idempotency cache, HARD
> RULE cross-client rejection at 2 layers). All 6 BLOCKING gaps wrapped behind the facade. Closure criterion met. Moved
> to `plans/archive/issues/`.

# Cross-Client Funds Isolation — Retroactive Audit

**Scope**: every execution-service surface that handles fund movement (CEX withdraw, DeFi deposit/withdraw, bridge,
sub-account move).

**Question audited**: where could a cross-client fund movement be CONSTRUCTED today (i.e. `client_id` either missing
entirely from the call surface or could be mismatched between source and dest without the code noticing)?

**Verdict**: 6 BLOCKING gaps + 1 INSPECT + 1 OK. Phase 6 TransferCoordinator facade is the right consolidation point —
wrap each finding below behind a single enforcement layer.

## What I found

### 1. CEX Withdrawals — destination address unvalidated

**Where**:
[`execution-service/execution_service/engine/handlers/transfer_handler.py:330,343-349`](execution-service/execution_service/engine/handlers/transfer_handler.py#L330)

`to_address = instruction.metadata.get("to_address", "")` (line 330) — bare metadata pull with NO validation that the
address belongs to the calling instruction's client. Both `_execute_cex_withdrawal()` and `_execute_onchain_transfer()`
(line 372) pull destination from instruction metadata without cross-checking against a derived source-account client
binding. The instruction carries `client_id` (via `LiveTrigger.on_instruction` at `trigger.py:34`), but TransferHandler
never asserts the metadata-derived destination matches.

**Gap**: BLOCKING.

**Fix in Phase 6**: TransferCoordinator wraps TransferHandler; before delegating, validates that `to_address` maps to a
wallet registered to `instruction.client_id` (requires a client→wallets mapping, sourced from clients.yaml +
deployment-service config). Raises `CrossClientTransferForbiddenError` on mismatch.

### 2. DeFi protocol deposit/withdraw — `client_id` not in method signatures

**Where**:

- [`defi_execution/protocols/aave.py:967`](execution-service/execution_service/defi_execution/protocols/aave.py#L967)
  `withdraw(token, amount)`
- [`defi_execution/protocols/karak.py:118`](execution-service/execution_service/defi_execution/protocols/karak.py#L118)
  `withdraw(token, shares)`
- `defi_execution/protocols/{yearn,idle,morpho,puffer}.py` — same pattern

None of these accept `client_id`. Destination wallet is implicitly derived from the protocol connector's
`connect()`-time wallet. Nothing enforces that the connector's wallet belongs to the calling instruction's client.

**Gap**: BLOCKING.

**Fix in Phase 6**: TransferCoordinator intercepts ALL DeFi withdraw/deposit calls. Before delegating to the underlying
connector, validate that the connector's initialized wallet address is in the destination client's wallet set (registry
sourced from clients.yaml). Raise `CrossClientTransferForbiddenError` if not.

### 3. Hyperliquid bridge — `destination_address` is a bare string with zero validation

**Where**:

- [`defi_execution/hyperliquid_bridge.py:173-179`](execution-service/execution_service/defi_execution/hyperliquid_bridge.py#L173)
  `withdraw_usdc_from_hyperliquid(destination_address, ...)`
- [`defi_execution/hyperliquid_bridge.py:84`](execution-service/execution_service/defi_execution/hyperliquid_bridge.py#L84)
  `deposit_usdc_to_hyperliquid(...)` uses `wallet_address` from caller similarly

No `client_id` parameter; caller passes destination without ensuring it matches source client.

**Gap**: BLOCKING.

**Fix in Phase 6**: Add `client_id: str` to both bridge functions; assert `destination_address` is registered to
`client_id` before posting the action. OR Phase 6 TransferCoordinator wraps both as a facade.

### 4. v2 BridgeHandler — no `client_id` enforcement

**Where**: [`v2/handlers.py:265-276`](execution-service/execution_service/v2/handlers.py#L265) `BridgeHandler.handle()`

Returns `ActionHandlerResult` with no client_id field. Thin handler; real logic downstream. No evidence downstream
BridgeInstructionV2 consumption validates source/dest client match. Handler extracts `chain_from`, `chain_to`, `asset`
but never checks `client_id`.

**Gap**: INSPECT (thin handler; verify downstream consumption).

**Fix in Phase 6**: If BridgeInstructionV2 schema includes source/dest client bindings, add validation in `handle()`
before returning. If not, coordinate with strategy-service IntraClientRebalanceCoordinator (Phase E.3) to ensure
TransferIntent schema is fully populated before reaching execution-service. TransferCoordinator is the final gate;
reject any BridgeInstructionV2-derived TransferIntent where source/dest client_ids differ.

### 5. Intent engine bridge decomposition — `client_id` not plumbed through ExecutionSteps

**Where**:
[`algo_library/intent_engine.py:495-527`](execution-service/execution_service/algo_library/intent_engine.py#L495)
`_decompose_bridge()`

Intent class (lines 81-110) carries NO `client_id` field. Bridge decomposition produces ExecutionSteps with no client
binding. Steps route downstream without any client context.

**Gap**: BLOCKING.

**Fix in Phase 6**: Add `client_id: str` to Intent dataclass (line 81). Propagate to every ExecutionStep created by
`_decompose_bridge()` AND every other decomposition method. ExecutionStep gains a `client_id` field for downstream
validation.

### 6. `isolation_policy.assert_client_allowed()` only called at bus layer (orders), not fund-movement ops

**Where**:

- [`isolation_policy.py:80-94`](execution-service/execution_service/isolation_policy.py#L80) (the enforcer)
- [`engine/modes/live/trigger.py:17-43`](execution-service/execution_service/engine/modes/live/trigger.py#L17) (only
  known caller — `LiveTrigger.on_instruction()` for order events at line 34)

Transfer instructions enter the queue (line 43) without per-operation re-assertion of `client_id` validity. The existing
guard catches event-bus delivery to wrong client process; it does NOT catch a same-process operation that constructs a
cross-client fund movement.

**Gap**: BLOCKING.

**Fix in Phase 6**: TransferHandler.execute() must call `assert_client_allowed(instruction.client_id)` BEFORE accessing
source/destination account data (add at line 160, before `validate()`). All DeFi protocol connectors that execute
withdraws must call `assert_client_allowed(client_id)` before signing/posting transactions. All bridge functions must
call `assert_client_allowed(source_client_id)` AND `assert_client_allowed(dest_client_id)` as separate assertions.
Defence-in-depth: even if metadata is injected or a wallet is mis-initialized, the per-process client binding rejects
it.

### 7. Sub-account moves — not found in current code

**Where**: nothing.

**Gap**: OK (not yet implemented). Phase 6 plan body already names `subaccount_transfers_phase_2_2026_06_01.md` as the
named successor when these get added on demand.

## Cumulative summary

3 critical junctures missing `client_id` enforcement today:

1. **CEX withdrawal destination validation** (`transfer_handler.py`) — destination address never cross-checked
2. **DeFi protocol method signatures** (`aave.py`, `karak.py`, etc.) — withdraw/deposit methods don't accept `client_id`
3. **Bridge functions** (`hyperliquid_bridge.py`) — `destination_address` is bare parameter with zero client context

Plus the structural gap: `assert_client_allowed()` only invoked at bus layer for incoming instructions, not at the
operation layer where fund-movement decisions are made.

## Slot 7 Phase 6 — explicit action items derived from this audit

When slot 7 builds the `TransferCoordinator` facade per Phase 6 of the Group H plan, the facade must:

1. Accept a `TransferIntent` (UAC contract from slot 5 Phase 1).
2. Validate `source_account.client_id == dest_account.client_id` at the facade entry; raise
   `CrossClientTransferForbiddenError` otherwise.
3. Call `isolation_policy.assert_client_allowed(intent.source_account.client_id)` for defence-in-depth at the
   process-binding layer.
4. Validate destination address is registered to `intent.dest_account.client_id` via clients.yaml mapping; raise on
   mismatch.
5. Dispatch to the right downstream (`adapters/order_adapter.py` CEX withdraw / `defi_execution/protocols/*` DeFi /
   `defi_execution/hyperliquid_bridge.py` bridges / `v2/handlers.py` BridgeHandler).
6. Each existing downstream call gets wrapped (or its signature extended) such that no path bypasses the facade.
7. Tests per `/codex/04-architecture/client-funds-isolation.md` § "Required tests":
   - intra-client happy path
   - UAC validator rejects construction
   - defence-in-depth: TransferCoordinator rejects at consume time
   - alert assertion on rejection attempt
   - PLUS one test per BLOCKING gap above (5 additional tests) covering each pre-existing surface.

## Out-of-scope for this audit

- Order events (not fund-movement)
- Market data subscriptions
- The TransferCoordinator itself (slot 7 builds it; this audit is for what EXISTS today)
- Strategy-service surfaces (intra-client supervisor-level work; Phase E.3 owns)

## Closure criterion

This audit closes when slot 7 Phase 6 lands ALL of:

- TransferCoordinator facade implemented per items 1-6 above
- 5 BLOCKING gaps wrapped (CEX withdrawal validation, DeFi protocol method extension, bridge function extension, intent
  engine client_id plumbing, `assert_client_allowed` at operation layer)
- 1 INSPECT verified (BridgeHandler downstream behaviour confirmed)
- All required tests pass
- Codex doc `04-architecture/transfer-coordinator.md` cross-references `client-funds-isolation.md`

Archive this issue doc once slot 7 Phase 6 ships green.
