---
doc_type: issue
title: Order cancel/amend HTTP endpoints are hardcoded fake-success stubs — never call any exchange adapter, affects every CEFI venue
summary: >-
  execution-service's /cancel and /amend manual-instruction HTTP endpoints log an event and return a hardcoded
  {"status":"CANCELLED"}/{"status":"AMENDED"} without ever calling any exchange adapter. The real per-venue
  cancel_order() implementations are genuine (verified CCXT/REST calls) but are unreachable from any production
  HTTP path. amend has zero real implementation anywhere in the codebase — only an orphaned, unused Protocol.
  Found during the venue_e2e_wiring_2026_08_16 cefi batch sweep, step 8 (execution) — same "claims success, does
  nothing" shape as the already-fixed CCXT-withdraw-stub finding from the same plan's step 9, just for order
  cancellation instead of fund withdrawal. Not CEFI-specific in the underlying code (the endpoints are
  venue-agnostic) — filed against cefi because that is where this sweep found it; likely affects every venue in
  every asset group that would ever route through this manual-instruction path.
status: open
nature: issue
asset_group: [cefi]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [execution, order-management, financial-correctness, live-money-risk, stub-code, venue-readiness]
related:
  [
    /plans/active/cefi_venue_e2e_batch1_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/issues/cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16.md,
  ]
created: 2026-08-16
author: interactive-session
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found 2026-08-16 during cefi_venue_e2e_batch1_2026_08_16.md's step-8 (execution) contract sweep — a dedicated
  research pass across execution-service's real InstructionActionV2/manual-instruction routing, checking actual
  instruction-action reachability (place/cancel/amend) per the parent plan's own "compared by ACTION, not by venue
  name" hard rule, not just adapter-class existence.
context_scope:
  [
    execution-service/execution_service/api/manual_instruction_api.py,
    execution-service/execution_service/trade_execution/oms/protocols.py,
    execution-service/execution_service/trade_execution/base_adapter.py,
  ]
---

# Order cancel/amend HTTP endpoints are hardcoded fake-success stubs

## What I found

`execution-service`'s only HTTP-reachable order cancel/amend surface —
`execution_service/api/manual_instruction_api.py`'s `POST /cancel` (lines 432-461) and `POST /amend` (lines
464-498) — do not call any exchange adapter. Confirmed by direct read of both full function bodies: each checks
only that an orchestrator/handler is initialized, calls `log_event(...)`, and unconditionally returns:

```python
# /cancel
return {"instruction_id": request.instruction_id, "status": "CANCELLED"}

# /amend
return {"instruction_id": request.instruction_id, "status": "AMENDED"}
```

Neither branch inspects `request.instruction_id` beyond logging it, neither calls any per-venue adapter method,
and neither can fail for any reason other than "orchestrator not initialized" (a 503). Every cancel/amend request,
for every venue, for any instruction ID (real or fabricated), returns a fake success.

**This is not because cancellation is unimplemented at the adapter layer** — the real per-venue `cancel_order`
methods are genuine, working implementations: verified full bodies for `binance_ccxt.py:270-306` (a real
`exchange.cancel_order()` CCXT call) and `kraken_rest_adapter.py:311-356` (a real Kraken REST `CancelOrder` call).
They are reachable in principle via `OrderAdapter.cancel_order` (`execution_service/adapters/order_adapter.py:
207,221`) — but no production caller path connects the `/cancel` HTTP endpoint to that method. The
`InstructionActionV2`-driven path (`execution_service/api/external_instruction_api.py`) doesn't help either — its
own docstring (lines 14-18) explicitly scopes CANCEL out of that router ("routes through a different internal
subsystem"), and that different subsystem is the stub above.

**Amend is worse: it has zero real implementation anywhere in the codebase**, not merely an unreachable one.
`BaseCLOBAdapter`'s abstract method set (`execution_service/trade_execution/base_adapter.py:93-200`) is
`place_order`/`cancel_order`/`get_order_status`/`get_fills`/`get_account_state`/`get_positions`/
`get_margin_state` — no amend/modify method exists on the interface at all. An `amend_order` `Protocol` does exist
separately (`execution_service/trade_execution/oms/protocols.py:22-23`), but it is referenced by exactly one file
in the entire repo — a test (`tests/trade_execution/unit/test_protocol_coverage.py:45`) — and zero real adapter
classes implement it.

**Confirmed uniform across all 12 of cefi's major venues** (BINANCE/BYBIT/OKX/COINBASE/KRAKEN families) checked in
this sweep — the stub is venue-agnostic code, so this is not a per-venue gap, it is a single shared-infrastructure
gap.

## Why it matters

This is a live-money correctness risk with the same shape as the already-fixed CCXT-withdraw-stub finding
(`plans/active/issues/cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16.md`, now shipped as
`execution-service@b9ddcd9193`): **a caller cannot distinguish "the order was actually cancelled" from "the stub
lied about it."** A strategy or operator that cancels an order and receives `{"status":"CANCELLED"}` could
reasonably act on that belief — free up allocated capital, re-hedge assuming the position is flat, place a
replacement order — while the original order remains genuinely live at the exchange. Unlike the withdraw-stub
finding, I have **not** yet confirmed real-world reachability (dead-code-today vs. live-reachable) — that is the
first todo below, done deliberately as a separate step rather than assumed, per this workspace's "claim ≤
measurement" rule.

## What I have NOT verified

- **Reachability**: whether any production code path (as opposed to a manual/ops HTTP call) actually invokes
  `/cancel` or `/amend` today. This is the single most important open question and is the first todo below —
  until it's answered this should be read as "a real, confirmed-present bug of unconfirmed reachability," the
  same posture the withdraw-stub finding started from before its own reachability sweep.
- Whether every one of the 12 CEFI venues' underlying exchange APIs even support order amendment natively (some
  exchanges require cancel-and-replace instead of a true amend) — relevant to whether the `amend` todo below
  should build a real amend, or make the endpoint honestly report "unsupported, use cancel+replace" per venue.

## Todos

- [x] ✅ [BACKEND] P0. **Confirm real-world reachability — done 2026-08-17. Verdict: LIVE-REACHABLE, NOT
      dead-code, materially different from the withdraw-stub finding's posture.** Traced every angle: (1)
      `manual_router` (this file's `APIRouter(prefix="/manual", ...)`) IS mounted in the running app —
      `execution_service/api/app.py:25,127`: `from execution_service.api.manual_instruction_api import router as
      manual_router` / `app.include_router(manual_router)`. Unlike the withdraw-stub bug (gated behind a Python
      object — `LiveCcxtTransferAdapter` — that nothing in production ever constructs), this is a live,
      registered HTTP route in the running service; anyone who can reach the service's HTTP surface with valid
      credentials for whatever auth layer sits in front of it can invoke `POST /manual/cancel`/`POST
      /manual/amend` TODAY and receive a fake success. (2) Zero first-party callers found anywhere in the
      workspace: grepped execution-service (CLI, other API routers, `__init__.py` — only an `__all__` export
      listing, not a caller), agent-orchestrator, deployment-ui, deployment-api, strategy-service — zero hits.
      The one UI-repo hit (`unified-trading-system-ui/lib/types/api-generated.ts`) is an OpenAPI-generated TS
      type definition, confirmed NOT an actual caller (no component/hook imports or invokes it). (3) **Not fully
      verified**: whether `/cancel`/`/amend` are gated by network-level auth (IAM/API-gateway/Cloud Run ingress
      policy) in front of the deployed service — this file's own code shows no per-route `Depends(get_auth...)`
      on either handler (unlike some other routes in this file that DO call `_check_service_state()` /
      auth-dependent helpers), so in-code enforcement is not confirmed either way; this is infra-level, outside
      what a repo checkout can settle. **Practical conclusion**: given this is genuinely operator-invokable
      HTTP surface (not a dormant object graph) and the system is pre-live-trading, this should be treated as
      at least as urgent as "before live-trading cutover," arguably more so than the withdraw-stub finding was
      at its own equivalent stage.
- [x] ✅ [BACKEND] P0. **Wire `/cancel` to the real per-venue `cancel_order`** via `OrderAdapter` (or whatever the
      real production instruction-routing path resolves to for this instruction's venue), and propagate the
      adapter's real result (success/failure/already-filled/not-found) instead of a hardcoded status. Done-when:
      an end-to-end test proves a cancel request reaches a real (or realistically mocked, per this workspace's
      test-fixture matrix) exchange call and the endpoint's response reflects that call's actual outcome, not a
      constant. **Fixed — `execution-service@0cb7c767ba`**. `CancelInstructionRequest` carries only
      `instruction_id`+`reason`, no venue — the fix looks up the instruction's real orchestrator, instrument_id,
      and open order IDs from `ExecutionOrchestrator`'s own tracking state (`instruction_to_order_ids`/
      `order_id_to_instruction`/`contexts`), not from caller input. Added `cancel_order()` to both
      `OrderAdapterMatchingEngine` (delegates to the real `OrderAdapter.cancel_order`) and `ExecutionOrchestrator`
      (delegates to the matching engine, `NotImplementedError` if the configured engine doesn't support live
      cancellation — e.g. a batch/simulated one), plus `get_instruction_instrument_id()` on `ExecutionOrchestrator`
      for the instrument-id lookup. `/cancel` now calls the real chain per open order, catches whatever exception
      the venue adapter raises (ccxt.*/REST-specific — genuinely varies by venue, verified via `binance_ccxt.py`'s
      real `cancel_order` re-raising the original ccxt exception), and returns `CANCELLED` only if every order
      genuinely cancelled, `CANCEL_FAILED` with a per-order-id `errors` map otherwise — never a hardcoded status.
      **Second bug found and fixed in the same pass**: the pre-existing `_get_active_orchestrator_or_raise`
      (used by `get_instruction_status`, the only other caller) picked `cached[0]` — the FIRST cached per-venue
      orchestrator, arbitrarily — silently wrong for any instruction tracked by a DIFFERENT cached venue on a
      multi-venue deployment. Replaced with `_find_orchestrator_for_instruction()`, which searches every cached
      orchestrator for the one that actually tracked the instruction; `get_instruction_status` now uses it too.
      7 new tests in `tests/unit/test_manual_cancel_real_wiring.py` (real-FastAPI-`TestClient`, per this
      workspace's HTTP-contract-test convention) covering: successful cancel calling the real adapter,
      cancel-failure surfacing as `CANCEL_FAILED` not a fake success, partial multi-order failure reporting only
      the failed order, 404/503 error paths, and the multi-venue orchestrator-lookup fix for both `/cancel` and
      `get_instruction_status`. 8593 passed/21 skipped, full `quality-gates.sh --no-fix` green before commit.
- [ ] [BACKEND] P1. **Decide + implement `amend`'s real semantics per venue** — either wire a genuine
      modify-order call for venues whose API supports it, or make the endpoint explicitly refuse with a clear
      "not supported for this venue, cancel and replace instead" for venues that don't, verified against each of
      the 12 venues' real API capabilities (don't assume uniformly). Done-when: `/amend` never returns a fake
      success — either a real amend happened, or a clear refusal was returned.
- [ ] [BACKEND] P2. **Audit whether any downstream state (order-tracking, position ledger) would show a stale
      "cancelled" order that is still actually live at the exchange** if this were ever hit before the fix lands
      — bounds the real-world blast radius the same way the withdraw-stub finding's equivalent todo did.
      Done-when: a cited answer, yes or no, with evidence.

## Progress Log

- **2026-08-17 (later, same session)**: Fixed the `/cancel` wiring P0 — `execution-service@0cb7c767ba`. Now
  calls the real per-venue `cancel_order` (looked up via the orchestrator's own instruction-tracking state, not
  caller input) and returns a genuine outcome instead of a hardcoded status. Found and fixed a second bug along
  the way: the pre-existing multi-venue orchestrator lookup picked `cached[0]` arbitrarily, silently wrong for
  any instruction tracked by a non-first venue — fixed for both `/cancel` and the pre-existing
  `get_instruction_status` endpoint. 7 new tests, full QG green. Only the P1 `amend` semantics todo and P2
  downstream-state-audit todo remain open.
- **2026-08-17**: Closed the reachability todo — verdict LIVE-REACHABLE (not dead-code), since the `/manual`
  router is genuinely mounted in the running app and reachable by anyone with HTTP+auth access, unlike the
  withdraw-stub bug which was gated behind an unconstructed Python object. Flagged to the operator directly
  given this raises urgency above the withdraw-stub finding's own equivalent stage. Network-level auth
  enforcement in front of the deployed service could not be verified from this checkout — infra-level, out of
  repo-read scope.
- **2026-08-16**: Filed during the cefi AG batch's step-8 (execution) venue-readiness sweep. Both endpoint bodies
  independently spot-checked by direct file read before filing. Flagged as a P0, same-shape-as-withdraw-stub
  finding given the live-money-correctness class, per this workspace's "big finding → notify operator" rule,
  rather than left as a silent plan todo.
