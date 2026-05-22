---
name: execution_master_audit_instructions
type: audit-instructions
epic: execution_master
assigned_vm: vm-trading-core
tier: L2
last_updated: 2026-05-22
---

# Execution Master — Audit Instructions

## Epic Scope

execution-service: venue handlers (all CeFi + DeFi venues), transfer coordinator, treasury, custody path
(`CLOUD_KMS_ENCRYPTED` for May-23; Copper + CEFFU post-June-1), flash loan receiver, matching engine. Hard rule:
cross-client funds movement FORBIDDEN at all 3 enforcement layers.

Codex SSOTs: `codex/04-architecture/client-funds-isolation.md`, `codex/04-architecture/flash-loan-receiver.md`,
`codex/04-architecture/custody-providers.md`, `codex/04-architecture/defi-execution-overview.md`

## Triggers

- Weekly (minimum cadence)
- After any new venue handler ships
- After any custody provider change or credential rotation
- After any transfer/withdraw/deposit code change
- When cross_client_funds_isolation retroactive audit shows new gaps

## Checklist

- [ ] (a) **CrossClientTransferForbiddenError at all 3 layers**: raised at UAC schema construction, strategy-service
      emit, and execution-service consume. Grep: `rg "CrossClientTransferForbiddenError" --include="*.py"` — verify 3
      distinct call sites

- [ ] (b) **client_id invariant on every fund movement**: every transfer/withdraw/deposit/bridge operation checks
      `source_account.client_id == dest_account.client_id`. Grep: `rg "client_id" execution-service/ --include="*.py"` —
      review all transfer-path usages Run: happy intra-client path test + UAC-validator-rejects-cross-client test

- [ ] (c) **CLOUD_KMS_ENCRYPTED path tested**: KMS custody path has end-to-end test (Tenderly fork or mock). Find:
      `rg "KMS|kms" execution-service/tests/ --include="*.py" -l` Verify: Copper/CEFFU June-1 timeline documented;
      May-23 ships on KMS only

- [ ] (d) **FlashLoanReceiver.sol matches codex**: contract in `deployment-service/contracts/FlashLoanReceiver.sol`
      matches description in `codex/04-architecture/flash-loan-receiver.md`. Grep:
      `rg "FlashLoanReceiver" deployment-service/ --include="*.sol"` Read: codex doc — verify ABI, callback signature,
      and re-entrancy protection match

- [ ] (e) **SwapRouter02 address matches UAC constant**: `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45` Grep:
      `rg "68b3465833fb72A70ecDF485E0e4C7bD8665Fc45" --include="*.py"` — verify it's a UAC constant, not hardcoded in
      execution-service business logic

- [ ] (f) **All venue handlers classify errors**: every venue handler calls `classify_venue_error()` on error path.
      Grep: `rg "classify_venue_error" execution-service/ --include="*.py"` — count vs handler file count

- [ ] (g) **6 BLOCKING gaps from retroactive audit shipped**: all items from
      `cross_client_funds_isolation_retroactive_audit_2026_05_20.md` are in code. Check: the active plan absorbing those
      gaps — all `- [x]`

- [ ] (h) **Shard-level failure isolation**: no `raise` inside per-venue loops in execution-service handlers. Grep:
      `rg "^\s+raise " execution-service/ --include="*.py"` — review each hit


### E2E Pipeline Verification (Batch → Paper → Live)

- (e2e-batch) **Batch e2e audit**: run `bash scripts/quality-gates.sh` with mock upstream features data → strategy
  produces signals → execution records manifest rows. Use `CLOUD_MOCK_MODE=true` and synthetic feature fixtures.
  Goal: confirm the entire batch code path executes without real upstream data.
- (e2e-paper) **Paper trading goal post**: paper trading for ≥1 DeFi archetype runs ≥7 days without silent failures.
  Manifest shows strategy_output + execution_record rows. PnL stream emits StrategyPnlStreamEvent. Dashboard shows
  paper positions. This is the gate before live.
- (e2e-live) **Live trading goal post**: live execution for ≥1 DeFi archetype with real wallet transactions confirmed
  on-chain. PnL calculator confirms realized + unrealized PnL matches expected from strategy signals.
- (post-trade) **Post-trade audit**: after live runs ≥7 days, verify execution records match strategy signals (no
  slippage model regression), PnL attribution is correct, and no cross-client fund movement occurred.
- (mock-upstream) **Mock upstream pattern**: strategy and execution audits MUST be runnable with mock MTDS + features
  data. Document the mock fixture location and how to substitute upstream parquets for independent downstream testing.

## Success Criteria

- All 8 checklist items GREEN
- Cross-client transfer impossible in all code paths (verified by tests)
- execution-service QG exits 0

- Batch e2e with mock upstream: full code path from features → strategy → execution runs without errors
- Paper trading ≥7 days: strategy_output + execution_record rows in manifest, PnL events flowing
- Live trading confirmed: ≥1 on-chain transaction verified for a real wallet

## Output Format

Result file at `plans/audit/results/execution_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
