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
status: archived
nature: issue
asset_group: [cefi]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [execution, order-management, financial-correctness, live-money-risk, stub-code, venue-readiness]
related:
  [
    /plans/archive/2026_08/cefi_venue_e2e_batch1_2026_08_16.md,
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

> **🟢 ARCHIVED 2026-08-17** — all 4 todos closed (P0 reachability, P0 /cancel wiring, P1 amend refusal, P2
> per-venue atomicity, P2 downstream-state audit). Follow-up fix work split into
> `plans/active/issues/execution_order_tracker_missing_cancelled_amended_status_2026_08_17.md` and
> `plans/archive/issues/kraken_futures_wrong_rest_base_url_2026_08_17.md`.

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
- [x] ✅ [BACKEND] P1. **Decide + implement `amend`'s real semantics per venue** — either wire a genuine
      modify-order call for venues whose API supports it, or make the endpoint explicitly refuse with a clear
      "not supported for this venue, cancel and replace instead" for venues that don't, verified against each of
      the 12 venues' real API capabilities (don't assume uniformly). Done-when: `/amend` never returns a fake
      success — either a real amend happened, or a clear refusal was returned. **Fixed —
      `execution-service@b8d225615b`: chose the explicit-refusal branch, deliberately, for all 12 venues.**
      Checked CCXT's `has['editOrder']` for all 12 — every one reports `True` — but that flag only means CCXT
      EXPOSES an `editOrder()` method, not that the exchange has a true exchange-native atomic amend; for
      several exchanges CCXT implements `editOrder()` as a client-side cancel+create composite instead, and
      confirming which is which per venue requires each exchange's own API documentation, not something
      verifiable from this repo checkout. Given the live-money stakes of a silently-non-atomic "amend"
      (partial-fill/race-condition exposure the caller wouldn't expect from something labeled "amend"), chose to
      refuse loud (`501`, clear message: "not implemented for any venue today... cancel + replace instead")
      rather than ship an unverified per-venue modify-order call under this session's time constraints. 2 new
      tests in `tests/unit/test_manual_amend_explicit_refusal.py`. 8595 passed/21 skipped, full
      `quality-gates.sh --no-fix` green before commit. **New follow-up todo below** for the deferred per-venue
      verification, so this doesn't silently stay "good enough forever."
- [x] ✅ [BACKEND] P2. **Verify true native-atomic `editOrder` support per venue against each exchange's own API
      docs (not just CCXT's `has['editOrder']` flag), then wire a real amend for confirmed-atomic venues** —
      follow-up from the P1 above, which deliberately chose blanket refusal over guessing at atomicity. Done-when:
      a cited per-venue verdict (native-atomic / cancel+replace-emulated / unsupported) for each of the 12
      venues, with real amend wired for any confirmed-atomic ones and the explicit-refusal path kept for the
      rest. **Fixed — `execution-service@eb0b0771d2`.** Per-venue verdicts, each checked against the exchange's
      own official API docs and (where available) the vendored CCXT source's actual `edit_order()` implementation
      (not just the `has` flag, which the P1 finding had already flagged as unreliable — and this session found a
      concrete case of that: CCXT's `has['editOrder']` is actually `False` for ASTER, contradicting the P1
      Progress Log's claim that "every one reports True" for all 12 — likely CCXT version drift since that check,
      or an imprecise original claim; corrected here since I measured it directly):
      - **BINANCE-SPOT**: native-atomic (cancel-replace variant) — `cancelReplace` is a single atomic exchange
        call (no client-side race) but returns a NEW order ID, not an in-place modify.
        [docs](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/trading-endpoints#cancel-an-existing-order-and-send-a-new-order-trade)
      - **BINANCE-FUTURES**: native-atomic, in-place (`PUT /fapi/v1/order` Modify Order, order ID retained).
        [docs](https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Modify-Order)
      - **BYBIT-SPOT / BYBIT-FUTURES**: native-atomic, in-place (`POST /v5/order/amend`, same endpoint across
        categories). [docs](https://bybit-exchange.github.io/docs/v5/order/amend-order)
      - **OKX-SPOT / OKX-FUTURES**: native-atomic, in-place (`POST /api/v5/trade/amend-order`, all instrument
        types). [docs](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-amend-order)
      - **COINBASE-SPOT**: native-atomic, in-place (`POST /brokerage/orders/edit`, order_id retained).
        [docs](https://docs.cloud.coinbase.com/advanced-trade/docs/apis/edit-order)
      - **KRAKEN-SPOT**: native-atomic, in-place — Kraken's own "Atomic Amends" (`POST /0/private/AmendOrder`,
        order identifiers unchanged, queue priority maintained where possible).
        [docs](https://docs.kraken.com/api/docs/rest-api/edit-order/)
      - **KRAKEN-FUTURES**: native-atomic endpoint exists (`POST .../derivatives/api/v3/editorder`,
        [docs](https://docs.kraken.com/api-reference/order-management/edit-order)) but this adapter doesn't
        reach it — see the new follow-up issue filed below.
      - **HYPERLIQUID**: native-atomic, in-place (single signed L1 `modify` exchange action).
        [docs](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#modify-multiple-orders)
      - **UPBIT**: native-atomic (cancel-replace variant) — Upbit's own "Cancel and New Order" is a single atomic
        exchange call, but returns a new order UUID, not an in-place modify.
        [docs](https://global-docs.upbit.com/reference/cancel-and-new-order)
      - **ASTER**: unsupported — confirmed no native amend endpoint exists at all (only place/cancel/query),
        both via direct WebFetch of Aster's own official API docs and via CCXT's `has['editOrder'] == False` for
        this venue specifically (the one venue where that flag is actually reliably negative). Kept the P1's
        explicit-refusal path, now venue-specific (`UnsupportedOperationError`) instead of blanket.

      Wired real `amend_order()` for all 11 confirmed-atomic venues through the same chain the P0 cancel fix
      built (`BaseCLOBAdapter` → per-venue adapter → `OrderAdapter` → `OrderAdapterMatchingEngine` →
      `ExecutionOrchestrator` → `/amend`), reusing a new shared `ccxt_amend_order()` helper in `ccxt_common.py`
      for the 6 venues whose CCXT `edit_order()` needs a `fetch_order()` first (to supply the `type`/`side` CCXT's
      signature requires but `AmendInstructionRequest` doesn't carry). `/amend` now returns `AMENDED` with the
      real post-amend order state, `AMEND_FAILED` with the real adapter error, or `501` only for a genuinely
      unsupported venue (Aster) or an unsupported matching engine — never a hardcoded status. Restricted to
      single-order instructions (409 if an instruction has >1 open order — ambiguous which order a single
      `new_quantity`/`new_price` would target). 7 new tests in `tests/unit/test_manual_amend_real_wiring.py`
      (replaces the now-stale `test_manual_amend_explicit_refusal.py`), full `quality-gates.sh` green before
      commit. **New follow-up issue filed** (out of this todo's scope, found during the research):
      `kraken_futures_wrong_rest_base_url_2026_08_17.md` — `KrakenCeFiAdapter(futures=True)` routes every
      private call (place/cancel/amend) through the Kraken **Spot** REST API, not the separate Kraken Futures
      surface; KRAKEN-FUTURES trading is non-functional through this adapter today (fails loud, not a fake
      success, so lower urgency than the stub bugs this doc chases, but still a real P0 gap).
- [x] ✅ [BACKEND] P2. **Audit whether any downstream state (order-tracking, position ledger) would show a stale
      "cancelled" order that is still actually live at the exchange** if this were ever hit before the fix lands
      — bounds the real-world blast radius the same way the withdraw-stub finding's equivalent todo did.
      Done-when: a cited answer, yes or no, with evidence. **Answered — YES, but a DIFFERENT-shaped staleness
      than the todo's own framing anticipated, and it is a PRESENT gap, not just a pre-fix historical exposure.**
      Traced the actual downstream state surface `/cancel` and `get_instruction_status` both read:
      `LiveOrchestrator.order_tracker` is `execution_service/orders/tracker.py`'s `OrderTracker` — its only two
      state-transition methods are `track_order()` (sets `status="SUBMITTED"` when an order is first tracked) and
      `update_fill()` (sets `status="FILLED"` on a fill). **There is no method anywhere on this class that sets a
      `"CANCELLED"` (or `"AMENDED"`) status** — confirmed by reading the full class body (`tracker.py:1-95`+) —
      and neither `/cancel`'s nor `/amend`'s handler in `manual_instruction_api.py` calls any tracker-mutating
      method after a successful venue-side cancel/amend (verified: `cancel_manual_instruction` only calls
      `cancel_order_fn(...)` per order id then returns a response dict; nothing touches `order_tracker`).
      Consequence: `GET /instructions/{id}` (`get_instruction_status`, which calls
      `order_tracker.get_order_status(order_id)` + `order_tracker.is_instruction_complete(instruction_id)`) keeps
      reporting a **successfully-cancelled** order as `"SUBMITTED"` forever after — it can never read
      `"CANCELLED"` because nothing ever writes that value — and `is_instruction_complete()` (which only returns
      `True` when every order shows `"FILLED"`) never flips to `True` for an instruction whose sole order was
      cancelled rather than filled, so the instruction's aggregate `status` field stays `"IN_PROGRESS"`
      indefinitely too. This is NOT the todo's originally-framed risk (a REST response lying that a still-live
      order is cancelled — that risk is now closed by the P0 `/cancel` fix, which propagates the venue's real
      per-order outcome). It IS a real, still-open risk of the opposite shape: **a caller who queries
      `GET /instructions/{id}` AFTER a genuinely successful `/cancel` sees a stale "still live" (`SUBMITTED`)
      picture of an order that is, in truth, dead at the exchange** — the inverse staleness direction, but the
      same class of "downstream state doesn't reflect the real order lifecycle" defect the todo asked about.
      Separately confirmed `instruction_to_order_ids`/`order_id_to_instruction` (the OTHER, unrelated
      instruction-tracking dict pair on `engine/orchestrator.py`, used only for orchestrator-lookup — not the same
      object as `order_tracker` above) are also never pruned on cancel, so a cancelled order's id stays resolvable
      via `_find_orchestrator_for_instruction` forever; this is lower-impact (lookup-only, no status field) but
      noted for completeness. **Position ledger**: no separate position-ledger write path was found reachable
      from `/cancel`/`/amend` at all in this service (`grep` for a position/ledger mutation call from either
      handler or the orchestrator `cancel_order`/`amend_order` methods returned nothing) — so there is no
      position-ledger-specific staleness to report; the only downstream state that reads order lifecycle at all is
      the `OrderTracker` described above. **Filed as a new, separate follow-up issue** (out of this P2 todo's own
      scope — an audit answers with evidence, it doesn't silently absorb the fix as unplanned work) rather than
      fixed inline: `plans/active/issues/execution_order_tracker_missing_cancelled_amended_status_2026_08_17.md`.

## Progress Log

- **2026-08-17 (final)**: Answered the last open todo (P2 downstream-state audit) — no code fix, audit-only.
  `OrderTracker` (`execution_service/orders/tracker.py`) has no state-transition method that ever writes
  `"CANCELLED"`/`"AMENDED"`, and neither `/cancel` nor `/amend` calls the tracker after a successful venue-side
  cancel/amend — so `GET /instructions/{id}` keeps reporting a genuinely-cancelled order as `"SUBMITTED"`
  indefinitely (the inverse of the todo's originally-framed risk, now that the P0 `/cancel` fix closed the
  "lying REST response" risk). No reachable position-ledger write path exists from either handler. Filed the fix
  as a separate follow-up issue rather than absorbing it as unplanned scope:
  `execution_order_tracker_missing_cancelled_amended_status_2026_08_17.md`. **Every todo on this doc is now
  closed** — ready for archival.
- **2026-08-17 (new session)**: Fixed the `/amend` P2 per-venue atomicity verification — `execution-service@eb0b0771d2`.
  Checked all 12 venues against each exchange's own official API docs (WebSearch/WebFetch) plus the vendored
  CCXT source's actual `edit_order()` bodies (not just the `has` flag). 11 of 12 confirmed native-atomic (some
  in-place/same-order-id, some atomic-cancel-replace/new-order-id — both close the race-condition risk this
  finding is actually about); only ASTER has none. Also corrected a small factual drift from the P1 Progress Log
  entry below: CCXT's `has['editOrder']` is NOT `True` for all 12 as previously stated — it's `False` for ASTER
  specifically in the currently-vendored CCXT version, confirmed by direct `.has` introspection, not just reading
  the flag's docstring. Wired real per-venue `amend_order()` for the 11 confirmed venues through the same chain
  the P0 cancel fix built, reusing a new shared `ccxt_amend_order()` helper for the 6 CCXT venues needing a
  `fetch_order()`-then-`edit_order()` two-step (to supply `type`/`side` the request schema doesn't carry).
  Restricted `/amend` to single-order instructions (409 otherwise — ambiguous target). 7 new tests, full QG
  green. Found and filed a new, separate P0 issue during this work rather than absorbing it as unplanned scope:
  `kraken_futures_wrong_rest_base_url_2026_08_17.md` (`KrakenCeFiAdapter(futures=True)` silently routes every
  private call through the Kraken Spot REST API instead of the real Kraken Futures surface). Only the P2
  downstream-state-audit todo remains open on this doc.
- **2026-08-17 (even later still, same session)**: Fixed the `/amend` P1 — `execution-service@b8d225615b`.
  Chose explicit refusal (501) over an unverified per-venue modify-order call: CCXT's `editOrder=True` flag is
  present for all 12 venues but doesn't distinguish true exchange-native atomic amend from CCXT's own
  cancel+create emulation, and confirming that distinction needs each exchange's own API docs. Added a new P2
  follow-up todo for that verification rather than leave it unrecorded. 2 new tests, full QG green. Only the
  two P2 todos (per-venue atomicity verification, downstream-state audit) remain open on this doc.
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
