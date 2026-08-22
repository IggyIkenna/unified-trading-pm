---
doc_type: plan
title: POD collateral-delegation transfer rail — mock-first, real API pending POD spec
summary:
  POD (first DeFi allocator client) is building an API where we instruct "move X asset from venue A to venue B for
  fund Y" and POD internally resolves custodian address + exchange account and executes it — no signing, no wallet
  addresses on our side. This plan wires it as a new BusTransferType rail (generic, not POD-specific) through the
  EXISTING TransferAdapter/TransferHandler/TransferConfirmationPoller architecture, mock-first pending POD's real
  spec, so strategy stays venue-agnostic per the existing custody-provider invariant.
status: active
nature: design
asset_group: [defi]
stage: [execution]
repos: [unified-api-contracts, execution-service]
scope: [engineer]
tags: [transfer, custody, pod, collateral, execution]
related:
  [
    /codex/04-architecture/custody-providers.md,
    /codex/04-architecture/transfer-architecture.md,
    /codex/14-customer-journeys/pod-elysium-client-onboarding.md,
    /plans/active/code_readiness_t4_execution_settlement_2026_08_19.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-22
last_updated: 2026-08-22
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
context_scope:
  [
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/transfer_events.py,
    unified-api-contracts/unified_api_contracts/registry/capability.py,
    unified-api-contracts/unified_api_contracts/internal/domain/fund_administration/transfer_context.py,
    execution-service/execution_service/engine/transfers/adapter.py,
    execution-service/execution_service/engine/transfers/factory.py,
    execution-service/execution_service/engine/transfers/confirmation_poller.py,
    execution-service/execution_service/engine/transfers/live_bridge_adapter.py,
    execution-service/execution_service/engine/transfers/mock_adapter.py,
    execution-service/execution_service/engine/handlers/transfer_handler.py,
    /codex/04-architecture/custody-providers.md,
  ]
supersedes:
superseded_by:
source: whatsapp-2026-08-21-timo-pod-collateral-delegation-thread
assigned_role: backend_engineer
---

# POD collateral-delegation transfer rail

> **Architecture ruling (operator, 2026-08-22)**: don't force this into `CustodyProvider` (that protocol is for
> MPC/key signing — POD never hands us a wallet address, we never sign anything). Treat it as one more instruction on
> the SAME unified transfer path every other rail already uses: strategy states `(from_venue, to_venue, asset,
> amount)` via `TransferIntent`; execution-service's adapters absorb the per-venue/per-custodian mechanical
> differences (sub-account hops, wait-for-confirmation vs self-verify) via the UAC capability registry. This is
> already the architecture `custody-providers.md` §1 and `transfer-architecture.md` describe for Copper/CEFFU — this
> plan is an extension of the existing pattern (the BRIDGE rail's duck-typed-adapter-method precedent, specifically),
> not a new one.

## Codex SSOTs

- `/codex/04-architecture/custody-providers.md` — CustodyProvider protocol (signing-specific; POD does NOT implement
  this — see the ruling above).
- `/codex/04-architecture/transfer-architecture.md` — general BusTransferType/TransferAdapter home; this plan's
  target doc for the new rail's writeup.
- `/codex/04-architecture/client-funds-isolation.md` — `CrossClientTransferForbiddenError` invariant; POD transfers
  are per-`client_id` like every other rail.

## Progress Log

- 2026-08-22 — Plan authored per operator directive (WhatsApp thread with POD's Timo, 2026-08-21/22): POD is building
  a collateral-delegation API (fund→custodian-address→exchange-account mapping stays on POD's side); real API spec
  not yet delivered (Copper+Binance prod integration in progress, Copper sandbox can't delegate capital yet, prod
  access pending, "early Sep likely" per the thread). Operator ruled: unify under the existing TransferIntent/
  TransferAdapter path (not CustodyProvider), and build a fuller async mock (state-machine, not instant) since
  upstream code needs to be tested against realistic PENDING→CONFIRMED/FAILED timing before POD's real endpoint
  exists.

- 2026-08-22 — Section B item 1 shipped (execution-service@fbde066bf3): the duck-typed
  `execute_collateral_delegation` interface + `TransferHandler._get_collateral_delegation_execute()` getattr-dispatch
  resolver + its unit tests. **Scope note for whoever picks up item 2 next**: item 1's title ("Add
  `execute_collateral_delegation` to `TransferAdapter`-implementing adapters") reads broadly, but items 1-5 in
  Section B overlap enough (all plausibly touch `transfer_handler.py`/`adapter.py`) that landing all 5 in one todo
  would step on items 3-5's own file ownership (`live_pod_adapter.py`, `mock_pod_adapter.py`,
  `factory.py`'s `CompositeTransferAdapter`/`create_transfer_adapter`) before they're built. Item 1 was scoped
  narrowly to exactly what's independently shippable + testable today: the Protocol-comment note (mirrors BRIDGE's)
  and the handler-side getattr resolver (mirrors `_get_bridge_execute`) — proven via a fake adapter in tests, not a
  real one (no real adapter exists yet). Item 2 (`_execute_custodian_delegation_transfer` + `_dispatch_transfer`
  routing) should call `self._get_collateral_delegation_execute(instruction)` — already built — the same way
  `_execute_bridge_transfer` calls `self._get_bridge_execute(instruction)`.

---

## Section A — UAC schema (unified-api-contracts)

- [ ] [BACKEND] P0. **Add `BusTransferType.CUSTODIAN_COLLATERAL_DELEGATION`** to `BusTransferType` in
      `unified_api_contracts/canonical/crosscutting/transfer_events.py` (alongside the existing 13 members, e.g.
      `UNITY_WALLET_OP`/`IBKR_FUND_MOVE`). Docstring: "Cross-venue collateral move mediated by a third-party
      custodian API that resolves wallet/account mapping internally — we instruct, we don't sign or see addresses.
      POD is the first user of this rail; generic for any future custodian offering the same instruct-and-confirm
      model." Add the corresponding entry to `BUS_TRANSFER_TYPE_RAIL` dict: `TransferRail.OTHER` (matches
      `UNITY_WALLET_OP`/`IBKR_FUND_MOVE` — neither CCXT nor on-chain). Done: `bus_transfer_type_rail(CUSTODIAN_COLLATERAL_DELEGATION)`
      returns `TransferRail.OTHER`; existing `test_cassette_schema_parity`-style enum-completeness test (if one
      exists for `BusTransferType`) still passes with the new member included.
- [ ] [BACKEND] P1. **Register POD in the UAC capability registry** (`unified_api_contracts/registry/capability.py`'s
      `SourceCapability`/`register_capability` pattern, same shape used for CeFi/DeFi sources) — declare `"pod"` as a
      source with `operation_details` for a `collateral_delegation` operation: `signing_scheme="none"` (POD signs
      nothing on our side), env support (`sandbox`/`prod` — sandbox URL TBD per POD spec), and which venue-pairs POD
      can move between (start with `{BINANCE, OKX}` per the WhatsApp thread's example; extend as POD confirms
      coverage). This is the "restrictions" registry the operator's ruling calls for — resolve venue-pair coverage
      from here, not a hardcoded list in execution-service. Done: `resolve_capability("pod")` returns a real
      `SourceCapability`; a unit test asserts `BINANCE`→`OKX` is declared, an unlisted pair raises
      `UnsupportedOperationError`.
- [ ] [BACKEND] P2. **Extend `FundTransferContext` or add a sibling POD-fund mapping** —
      `unified_api_contracts/internal/domain/fund_administration/transfer_context.py`'s `FundTransferContext.fund_id`
      is OUR internal IM-Pooled-fund id, a different id-space from POD's own `fund_id` (POD's WhatsApp example: "fund
      123"). Add a small static lookup (client_id/fund_id → POD fund_id), following the same GCS-config pattern as
      `wallet_provisioning.json`/`wallet_mapping.json` (see `wallet-hierarchy-and-capital-flow.md`) rather than a new
      schema field on every transfer. Done: a `pod_fund_id_for(client_id: str) -> str` resolver exists and is unit
      tested; raises a named error (not `KeyError`) for an unmapped client.

## Section B — execution-service adapter (mock-first)

- [x] ✅ [BACKEND] P0. **Add `execute_collateral_delegation` to `TransferAdapter`-implementing adapters via the SAME
      duck-typed-method pattern BRIDGE uses** (`engine/transfers/adapter.py`'s comment above `get_transfer_status`
      explains why BRIDGE was NOT added to the `Protocol` itself — a required new method would break existing fake
      `TransferAdapter` test doubles elsewhere in the suite). Signature:
      `execute_collateral_delegation(from_venue: str, to_venue: str, token: str, amount: Decimal, fund_context:
      FundTransferContext | None, idempotency_key: str | None) -> TransferResult`. Dispatch it from
      `TransferHandler` via `getattr(self._adapter, "execute_collateral_delegation", None)` exactly mirroring
      `TransferHandler._execute_bridge_transfer`'s pattern — an adapter without it fails loud with an honest "adapter
      does not support collateral delegation" `TransferResult`, never a silent success. — execution-service@fbde066bf3.
      Shipped: the `adapter.py` Protocol-comment extended with the exact signature above +
      `TransferHandler._get_collateral_delegation_execute()` (getattr-based resolver, mirrors `_get_bridge_execute`
      exactly) + `tests/unit/test_transfer_handler_collateral_delegation_dispatch.py` (adapter-with-support resolves
      the bound method + is actually invokable; adapter-without-support fails loud with the honest message, never
      raises). Scope boundary (see Progress Log): the orchestration method that CALLS this resolver
      (`_execute_custodian_delegation_transfer`, item 2 below) and the concrete adapters that implement the method
      (items 3-5 below) are NOT part of this todo — this todo only lands the duck-typed interface + its dispatch
      resolver, so `getattr(self._adapter, "execute_collateral_delegation", None)` has somewhere real to resolve
      TO once items 3-5 land.
- [ ] [BACKEND] P0. **New `TransferHandler._execute_custodian_delegation_transfer` method**
      (`execution_service/engine/handlers/transfer_handler.py`, mirroring `_execute_bridge_transfer` at line ~568) —
      routed from `_resolve_transfer_type`/`_dispatch_transfer` when the resolved `BusTransferType` is
      `CUSTODIAN_COLLATERAL_DELEGATION`. Done: a unit test asserts an `ExecutionInstruction` classified as
      `CUSTODIAN_COLLATERAL_DELEGATION` reaches this method (not `_execute_onchain_transfer` or
      `_execute_custody_transfer`).
- [ ] [BACKEND] P0. **New `execution_service/engine/transfers/live_pod_adapter.py` — `LivePodCollateralAdapter`**
      (real REST client, mirrors `live_bridge_adapter.py`'s honest-not-configured-fails-loud shape). Every REST
      endpoint/path is `<TBD-POD-PROVIDES-API-SPEC>` per the proposed schema in Section C — construct the class with
      real constructor fields (`api_url`, `credentials_secret`, `sandbox: bool`) but every method raises
      `NotImplementedError("POD API spec pending — see /codex/04-architecture/transfer-architecture.md § POD")`,
      mirroring `CeffuCustodyProvider`'s stub-shipped pattern exactly (see `custody-providers.md` §2.4). This todo is
      NOT gated on POD's spec — the stub shell ships now so the factory/dispatch wiring is provably complete
      end-to-end against the mock; only the real REST method bodies (tracked separately in the epic) await the spec.
- [ ] [BACKEND] P0. **New `execution_service/engine/transfers/mock_pod_adapter.py` — `MockPodCollateralAdapter`**.
      Per operator ruling: a FULLER async simulator, not instant success — an in-memory per-`transfer_id` state
      machine transitioning `PENDING → CONFIRMED` (or `PENDING → FAILED`) after a configurable number of
      `get_transfer_status()` polls (default: 2nd poll resolves), so `TransferConfirmationPoller.wait_for_confirmation`
      exercises real multi-poll timing in tests, not a first-poll-always-done shortcut like
      `MockTransferAdapter.execute_bridge_transfer` today. Test hooks mirroring `MockCustodyProvider.set_balance()`:
      `force_outcome(transfer_id, status)` to make a specific test deterministic without waiting out the real poll
      count. Done: a test asserts a fresh delegation stays `PENDING` on poll 1 and resolves by poll 2 with default
      config, and `force_outcome` overrides that for a targeted failure-path test.
- [ ] [BACKEND] P1. **Wire the new adapter into `CompositeTransferAdapter`/`create_transfer_adapter`**
      (`engine/transfers/factory.py`) — add an optional `pod_adapter: TransferAdapter | None` constructor param to
      `CompositeTransferAdapter`, defaulting to an honestly-not-configured `LivePodCollateralAdapter(None)` exactly
      like `self._bridge` defaults today (line ~50), never a crash, never fabricated success. `create_transfer_adapter`
      gets a matching `pod_config: ... | None` param, BACKTEST/PAPER modes get `MockTransferAdapter` extended (or
      composed) with `MockPodCollateralAdapter`'s behavior for this rail specifically.

## Section C — Proposed external API (for POD)

- [ ] [BACKEND] P1. **Commit the proposed POD API schema to `/codex/04-architecture/transfer-architecture.md`** as a
      new section "§N POD collateral-delegation API — proposed, pending POD confirmation," mirroring
      `custody-providers.md` §2.4's "API integration — PENDING SPEC" table format exactly (request/response JSON
      shape, status taxonomy, idempotency contract, open questions list) — draft content already produced in-session
      (2026-08-22 WhatsApp-ready version); this todo is committing it as the durable doc, not re-deriving it. Field
      names should map close to 1:1 onto `TransferIntent`/`TransferResult` (`instruction_id`↔`idempotency_key`,
      `from_venue`/`to_venue`↔`source_venue`/`dest_venue`, `asset`, `amount`) so the eventual `LivePodCollateralAdapter`
      needs near-zero translation. Done: the section exists, cross-linked from `custody-providers.md` §10 References.
- [ ] [REVIEW] P2. **Cross-link `pod-elysium-client-onboarding.md`** to this plan and the new transfer-architecture.md
      section, so a reader following POD's client-onboarding doc discovers the collateral-delegation rail exists.

## Section D — Balance pre-check + health

- [ ] [BACKEND] P1. **Confirm whether `TransferHandler.validate()` already source-balance-checks other rails**
      (`transfer_handler.py:150`) before dispatch — if yes, extend the same check path to
      `CUSTODIAN_COLLATERAL_DELEGATION` (read from PBMS's balances projection per epic W9 "Account balances: the
      single strategy I/O," not from POD — POD exposes no balance-query endpoint per the WhatsApp thread). If no
      such check exists for any rail today, add one scoped to this rail only (do not silently expand scope to fix a
      pre-existing gap in unrelated rails — file that separately if found). Done: a test asserts a delegation
      instruction with `amount` exceeding the PBMS-projected source-venue balance is rejected in `validate()`, not
      submitted to the adapter.
- [ ] [BACKEND] P2. **Health-check stub for POD** — mirrors `custody-providers.md` §10A's `CustodyProvider.health_check()`
      contract conceptually (reachability + freshness signal) but POD has no key-rotation concept (no signing keys on
      our side), so the shape is simpler: reachability-only, `healthy: bool` + `last_round_trip_ms`. Stub raises
      `NotImplementedError` alongside the other POD methods until the real endpoint exists; not wired into the 60s
      custody-ping loop (that loop is `CustodyProvider`-specific — this is a separate, smaller check to add to
      execution-service's own `/health` composite once POD's real endpoint lands, tracked as a follow-up, not built
      here).

## Section E — Tests + verification

- [ ] [BACKEND] P0. **Unit tests for the new `BusTransferType` member + rail mapping** — extend whatever test file
      already covers `BUS_TRANSFER_TYPE_RAIL` completeness (grep for existing `BusTransferType` test coverage before
      writing a new file). Done: green under `unified-api-contracts`'s `quality-gates.sh`.
- [ ] [BACKEND] P0. **Unit tests for `MockPodCollateralAdapter`'s state machine + `TransferConfirmationPoller` against
      it** (multi-poll PENDING→CONFIRMED, PENDING→FAILED, `force_outcome` override) — new file
      `execution-service/tests/unit/engine/transfers/test_mock_pod_adapter.py`, following the existing
      `tests/unit/engine/transfers/` layout. Done: green under `execution-service`'s `quality-gates.sh`.
- [ ] [BACKEND] P0. **Unit tests for `TransferHandler._execute_custodian_delegation_transfer` dispatch routing +
      `CompositeTransferAdapter`'s `pod_adapter` wiring** (both the configured and honestly-not-configured
      fails-loud path). Done: green under `execution-service`'s `quality-gates.sh`.
- [ ] [AGENT] P1. **End-to-end mock-mode smoke**: construct a `TransferIntent` with
      `transfer_type=CUSTODIAN_COLLATERAL_DELEGATION`, drive it through `TransferHandler.execute` in
      BACKTEST/PAPER mode, confirm a `TransferResult` with `status=CONFIRMED` comes back within the mock's
      configured poll count, and that `recon_excluded`/ledger semantics (per
      `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`) are consistent with how every other rail's
      mock path behaves — do not special-case this rail's ledger handling. Evidence: passing test output + a one-line
      Progress Log entry citing it.

## Section F — Plan hygiene

- [ ] [AGENT] P2. **Add a pointer todo to `/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md`'s
      Ceffu-integration section** referencing this plan, mirroring the existing W22 pointer pattern at that file's
      "### W22" section — so T4 stays the single index a reader checks first, per this workspace's convention for
      every other spun-out W-plan.
