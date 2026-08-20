---
doc_type: plan
title: Redemption Wallet-Transfer Execution — Per-Client Isolation Under Cadence Batching
summary:
  Hardens the wallet-transfer leg of the redemption cadence engine (companion plan
  fund_administration_redemption_cadence_engine_2026_08_20) so that batching many funds' outstanding redemptions into
  one cadence tick never violates the per-client funds-isolation HARD RULE — every withdrawal stays scoped to its own
  redemption's allocator/fund_context, confirmed by tests, not just by code shape.
status: active
nature: process
asset_group: [cross-cutting]
stage: [strategy]
repos: [fund-administration-service, execution-service, unified-api-contracts]
scope: [engineer]
tags: [fund-administration, redemption, client-isolation, wallet-transfer, execution]
related:
  [
    /plans/active/fund_administration_redemption_cadence_engine_2026_08_20.md,
    /plans/epics/client_isolation_and_governance_master.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: client_isolation_and_governance_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
depends_on: [fund_administration_redemption_cadence_engine_2026_08_20]
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: operator conversation relay (Greg/Patrick SMA-redemption chat) + interactive session slot 5, 2026-08-20
context_scope:
  [
    /codex/04-architecture/client-funds-isolation.md,
    /codex/04-architecture/per-client-isolation-architecture.md,
    fund-administration-service/fund_administration_service/background/grace_period_handler.py,
    fund-administration-service/fund_administration_service/allocation/transfer_protocol.py,
    execution-service/execution_service/engine/transfers/,
    /plans/active/fund_administration_redemption_cadence_engine_2026_08_20.md,
    /plans/epics/client_isolation_and_governance_master.md,
  ]
---

# Redemption Wallet-Transfer Execution — Per-Client Isolation Under Cadence Batching

**Why this doc exists**: once redemption processing moves from ad-hoc, per-request handling to a fixed cadence that
batches together every fund's outstanding withdrawals (companion plan
[`fund_administration_redemption_cadence_engine_2026_08_20.md`](fund_administration_redemption_cadence_engine_2026_08_20.md)),
the risk that matters is a batch loop accidentally netting or cross-wiring transfers across clients — exactly what
`client-funds-isolation.md`'s `CrossClientTransferForbiddenError` HARD RULE exists to prevent. The redemption code
already builds a per-redemption `FundTransferContext` and calls `execute_withdrawal` once per redemption
(`grace_period_handler.py:119-136`), which looks correct by inspection, but nothing in the corpus currently proves it
under a multi-client cadence batch. This plan proves it, hardens the idempotency/retry path a recurring cadence loop
introduces, and confirms the batch respects each redemption's own AML/KYC clearance rather than assuming request-time
clearance still holds at process time.

**Not in scope**: the `_WITHDRAWAL_FEES`/`_MOCK_WITHDRAWAL_FEES` hardcoded on-chain gas-fee stubs already tracked under
this epic (`client_isolation_and_governance_master.md`, hardcoded-value cleanup) are a distinct concept — blockchain
transaction cost, not the investor redemption-processing fee the companion plan adds to `FeeStructure`. Not touched
here to avoid conflating the two.

**Dependency note**: `depends_on` the companion plan for ordering only (not `gate_on_depends`) — every todo below tests
against a directly constructor-injected real adapter/redemption fixture, independent of whether the companion plan's
production DI wiring has landed yet.

## Todos

- [x] [BACKEND] P0. Prove per-client isolation holds under a multi-client cadence batch: add a test driving
  `GracePeriodHandler.run_once()` (`fund_administration_service/background/grace_period_handler.py`) over 2+ pending
  redemptions belonging to DIFFERENT `allocator_id`s in the SAME tick, and assert each produces its own
  `execute_withdrawal` call with a non-overlapping `FundTransferContext`/`destination` — never netted, batched, or
  reordered across allocators. Done-when: the test fails if `_withdraw_to_allocator` is ever refactored to share state
  across redemptions in the same `run_once()` call. — fund-administration-service@90603d94a7; Evidence: test-only quality gate 38 passed, 83.96% coverage; full quickmerge quality gate passed.

- [x] ✅ [BACKEND] P0. Confirm `FundTransferContext` actually trips execution-service's own per-client isolation
  enforcement when called via the structural `TransferAdapter` Protocol
  (`fund_administration_service/allocation/transfer_protocol.py:63`) — locate the `CrossClientTransferForbiddenError`
  raise site in `execution-service/execution_service/engine/transfers/` and add/confirm a test proving a redemption
  batch with a deliberately mismatched `fund_context` (wrong client's wallet as `destination`) is rejected, not
  silently executed. Done-when: that test asserts `CrossClientTransferForbiddenError` fires.
  — unified-api-contracts@040c871c, execution-service@6d43020e, fund-administration-service@ccc751c; Evidence: QG green in all three repos; new execution-service test `test_transfer_adapter_client_isolation.py` asserts `CrossClientTransferForbiddenError` fires on a mismatched `fund_context.client_id`, and fund-admin's `_withdraw_to_allocator` now carries `client_id=allocator_id` per redemption.

- [x] ✅ [BACKEND] P1. Add idempotency safety for the cadence loop's retry path: a `run_once()` tick that crashes after
  `execute_withdrawal` succeeds but before `_persist_processed` commits would, on the NEXT tick, find the same
  redemption still `APPROVED` and past its expiry — confirm `redemption_id` is used as (or maps to) the transfer's
  idempotency key so a retried tick never double-withdraws. Done-when: a test simulating exactly that crash sequence
  (transfer succeeds, persist fails, `run_once()` called again) asserts only ONE real withdrawal is issued for that
  redemption_id.
  — fund-administration-service@af9d292, execution-service@d8bae52a; Evidence: QG green in both repos; `_withdraw_to_allocator` passes `idempotency_key=redemption_id` and the adapters dedupe on it (execution-service `TestWithdrawalIdempotency` + fund-admin `test_crashed_tick_does_not_double_withdraw_on_retry`).

- [ ] [BACKEND] P1. Audit whether `AmlKycGate` clearance is re-evaluated at grace-period-EXPIRY time or only at
  redemption-REQUEST time — a grace period spanning hours-to-days means a client's AML/KYC status could change in
  between. State the finding as a fact (which one it currently is, cite the exact call site), and if it's
  request-time-only, add a re-check in `GracePeriodHandler._drive_unchecked` before `_withdraw_to_allocator` fires.
  Done-when: either a cited call site proving re-evaluation already happens, or a new re-check + test proving a
  redemption whose AML status flips to rejected between request and expiry is NOT paid out.

- [ ] [REVIEW] P2. Audit whether the single flat `treasury_wallet_id` default (`fund_administration_service/config.py`)
  is safe across multiple funds/share-classes settling in the same cadence tick, or whether it needs a per-fund/
  share-class override to avoid two funds' redemptions resolving to the same custody wallet. Done-when: a stated
  fact — either "confirmed safe because <reason>" with the reasoning cited, or a scoped follow-up todo naming the fix.

## Progress Log

- **2026-08-20**: Plan authored following `/plan-brainstorm`, as the client-isolation-focused companion to
  `fund_administration_redemption_cadence_engine_2026_08_20.md`. Split confirmed with the operator: this plan owns the
  wallet-transfer-execution + per-client-isolation leg under `client_isolation_and_governance_master`.

- **2026-08-20**: Shipped the multi-client cadence isolation regression test in `fund-administration-service@90603d94a7`; the test records destination, amount, and context fund per withdrawal and proves two allocator-specific approvals produce two non-overlapping calls in one `run_once()` tick. Test-only quality gate: 38 passed, 83.96% coverage; quickmerge full gate passed.

- **2026-08-20**: Shipped todo 2 (adapter-path per-client isolation enforcement). **Finding**: `FundTransferContext` did NOT previously trip execution-service's isolation via the `TransferAdapter` Protocol — the `CrossClientTransferForbiddenError` raise site is `TransferCoordinator.validate_intent` (`execution-service/execution_service/transfer_coordinator.py:261`), keyed on `TransferIntent.client_id`, a path fund-admin's `execute_withdrawal` never takes; all four adapters (Mock/CCXT/Custody/Composite) threaded `fund_context` through as pure metadata, so a mismatched context was silently executed. Closed the gap: added `FundTransferContext.client_id` (unified-api-contracts@040c871c), an `assert_fund_context_client_allowed()` guard wired into the fund-moving `execute_*` methods (execution-service@6d43020e), and populated `client_id=redemption.allocator_id` in `GracePeriodHandler._withdraw_to_allocator` (fund-administration-service@ccc751c). Tests: `tests/unit/engine/test_transfer_adapter_client_isolation.py` (execution-service) asserts `CrossClientTransferForbiddenError` fires before any venue/chain RPC on a mismatched `fund_context`; `test_withdraw_to_allocator_carries_allocator_client_id` (fund-admin) proves each redemption's withdrawal carries its own allocator client_id. QG green in all three repos.

- **2026-08-20**: Shipped todo 3 (idempotency safety for the cadence retry path). **Finding**: the redemption path previously had NO idempotency — a `run_once()` tick that crashed after the withdrawal succeeded but before `_persist_processed` committed would re-issue the withdrawal on the next tick. Fixed: `_withdraw_to_allocator` now passes `idempotency_key=redemption.redemption_id` (fund-administration-service@af9d292), and execution-service's `execute_withdrawal` adapters dedupe on the key (Mock/LiveCcxt memoize the issued `TransferResult`; Composite passes through; execution-service@d8bae52a). `LocalSimulatedTransferAdapter` (fund-admin's default production adapter) gained the same in-process dedupe. Tests: execution-service `TestWithdrawalIdempotency` (same key → one real withdrawal + same transfer_id; different keys → both execute; LiveCcxt exchange hit once) + fund-admin `test_crashed_tick_does_not_double_withdraw_on_retry` (persist-crash on tick 1, retry tick 2 → only ONE real withdrawal for that redemption_id). QG green both repos.
