---
doc_type: issue
title: >-
  `ControlInstruction` (16th/final `StrategyInstructionV2` action type) is now wired into external dispatch;
  `unified-api-contracts` has no `account_id` field for it, a small residual schema gap
summary: >-
  Wiring the 16th and final `StrategyInstructionV2` action type — `execution-service/execution_service/api/
  external_instruction_api.py::submit_external_instruction`'s isinstance dispatch chain never called the
  already-real `_submit_control_instruction()`. Fixed: `ControlInstruction` now dispatches for real —
  `KILL_SWITCH` activates the durable kill switch directly (protective arming only; `kill_switch.deactivate()`
  has zero call sites on any external-facing router, confirmed by grep — `manual_unkill` stays human-only per
  `/codex/04-architecture/autonomous-recovery-matrix.md`), `FLATTEN_POSITION` delegates to the existing authorized
  `AccountInstructionOrchestrator.CLOSE_ALL` path. Both require a non-empty `authorization_id`.

  Residual finding (not blocking, tracked below): `ControlInstruction` carries no `account_id` field in
  `unified-api-contracts` (`unified_api_contracts/internal/architecture_v2/schemas.py`), so `FLATTEN_POSITION`'s
  translation to `AccountInstruction` passes `account_id=""` rather than a real value. Verified harmless today —
  every live CeFi venue adapter's `get_positions(account_id: str | None = None, ...)` accepts the parameter but
  ignores it entirely (grepped binance_ccxt/hyperliquid_ccxt/coinbase_ccxt/upbit_ccxt/bitget_native), since API-key
  scoping already resolves the account — but it is a real, honest gap that should be closed before any adapter
  starts using the parameter for real multi-account scoping.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [execution-service, external-api, control-instruction, kill-switch, instruction-vocabulary]
related:
  [
    /plans/active/walkthrough_feedback_remediation_2026_08_21.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/account-instructions.md,
  ]
created: 2026-08-21
source: >-
  Sub-agent dispatch: wire the 16th/final StrategyInstructionV2 action type (ControlInstruction) into the external
  dispatch chain, verified genuinely unwired at execution-service HEAD 959c045e9 before the fix.
author: agent
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.5
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    execution-service/execution_service/api/external_instruction_api.py,
    execution-service/execution_service/v2/account_orchestrator.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py,
  ]
drift_direction: advance-code
---

# ControlInstruction now dispatches for real; UAC's missing account_id field is the one open follow-up

## Resolution (2026-08-21)

`execution-service@b49a3f1a96` ("wire ControlInstruction into external dispatch — 16 of 16 action types live") adds
`isinstance(envelope, ControlInstruction)` as the first branch in `submit_external_instruction`'s dispatch chain
(right after `_enforce_client_org_binding`), and retypes `_submit_control_instruction(envelope: ControlInstruction,
auth: AuthContext)` off the real Pydantic schema instead of a loosely-typed `object` + getattr. `KILL_SWITCH` and
`FLATTEN_POSITION` both reach their real handlers; both require a non-empty `authorization_id`, honestly
`REJECTED` otherwise. `submit_external_instruction`'s own top-of-function `kill_switch.is_active()` gate already
blocks every instruction, this one included, once the switch is armed — the same precedent
`account_instruction_api` already established for `CLOSE_ALL`.

**Safety property verified, not just assumed**: `kill_switch.deactivate()` has zero call sites on this or any
other external-facing router — its only callers are `api/app.py`'s internal API-key-gated admin hook and the
internal `kill_switch_bus_bridge`. `manual_unkill` stays human-only. Tests:
`tests/unit/test_external_instruction_api.py::TestControlInstructionPath` (real dispatch to `kill_switch.activate`,
an explicit `test_kill_switch_never_exposes_a_deactivate_resume_path` regression guard, missing-authorization
rejection for both actions, real `FLATTEN_POSITION` dispatch through a real `AccountInstructionOrchestrator` +
fake order-adapter factory, cross-org denial) plus the pre-existing
`tests/unit/api/test_external_control_instruction.py` contract tests, updated to the real schema and the
function's new 2-argument signature. Evidence: `bash scripts/quality-gates.sh --no-fix` (ALL QUALITY GATES PASSED).
`platform-api-reference.html` §04 (lede, callout, instruction-type-support table, verified-marker line) and §07's
`501` row updated to match — `unified-trading-pm` (this ship).

## Open follow-up

- [ ] [BACKEND] P3. Add an `account_id: str | None` field to `ControlInstruction`
      (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py`) so `FLATTEN_POSITION`'s
      translation to `AccountInstruction` can carry a real venue account_id instead of `""`. Not urgent: every live
      CeFi venue adapter's `get_positions(account_id: str | None = None, instrument_id: str | None = None)` accepts
      the parameter but ignores it entirely (grepped `binance_ccxt.py`, `hyperliquid_ccxt.py`, `coinbase_ccxt.py`,
      `upbit_ccxt.py`, `bitget_native.py` — API-key scoping already resolves the account), so today's `""` is inert,
      not silently wrong. Close this before any adapter starts using `account_id` for real multi-account scoping.
