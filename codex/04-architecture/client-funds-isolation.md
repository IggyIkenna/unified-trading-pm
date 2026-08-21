---
doc_type: codex-ssot
title: Client Funds Isolation — HARD RULE
summary:
  "HARD RULE: funds NEVER move between clients — every TransferIntent carries one client_id; enforced by UAC structural
  guarantee + execution-service consume-time raise + strategy-service IntraClientRebalanceCoordinator emit-time raise
  (CrossClientTransferForbiddenError)."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, client-reporting-api, deployment-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: [client-isolation, funds, transfers, rebalancing, execution, hard-rule]
related:
  [
    /codex/04-architecture/execution-service-per-client-isolation.md,
    /codex/04-architecture/per-client-isolation-architecture.md,
    /codex/04-architecture/transfer-coordinator.md,
    /codex/04-architecture/custody-providers.md,
  ]
created: 2026-05-20
authoritative_for: [client funds isolation HARD RULE, cross-client transfer prohibition]
referenced_by:
  [
    /codex/02-data/ledger-event-taxonomy.md,
    /codex/04-architecture/client-lifecycle-state-machine.md,
    /codex/04-architecture/execution-service-per-client-isolation.md,
    /codex/04-architecture/global-ledger-architecture.md,
    /codex/04-architecture/identity-model.md,
    /codex/04-architecture/per-client-isolation-architecture.md,
    /codex/04-architecture/transfer-coordinator.md,
    /codex/09-strategy/architecture-v2/cross-cutting/treasury-trading-wallet-invariant.md,
  ]
owner:
last_reviewed: 2026-10-22
code_refs:
---

# Client Funds Isolation — HARD RULE

**Codified 2026-05-20** per operator direction during Group H per-client isolation plan filing.

## The rule

**Funds NEVER move between different clients.** Every transfer (CEX withdrawal, DeFi deposit/withdraw, bridge,
sub-account move, rebalancing) operates within the scope of a single `client_id`. Source account and destination account
MUST share the same `client_id`.

Enforced via structural guarantee + runtime gate (2026-05-22 F-36/F-23 reconciliation — corrects earlier "3 layers"
wording that overstated the implemented raise count):

1. **UAC structural guarantee**: `TransferIntent` carries a single `client_id: str` field (not separate
   `source_account.client_id` / `dest_account.client_id`). By schema design there is only ONE client identity on an
   intent, so cross-client mixing is architecturally prevented at schema construction — no runtime validator is needed
   or present. Any code that tries to move funds between client A and client B must craft TWO intents, each with its own
   `client_id`; the routing layer catches that at the execution gate (layer 2).
2. **Execution-service runtime gate (ONLY implemented raise)**: `TransferCoordinator.execute()`
   (`transfer_coordinator.py:241`) rejects any TransferIntent whose `client_id` differs from the process-bound
   `CLIENT_ID` environment variable. Raises `CrossClientTransferForbiddenError` at consume time — the hard gate before
   any RPC call hits a venue or chain.

**Shipped 2026-06-23 (Phase E.3)**: strategy-service `IntraClientRebalanceCoordinator`
(`strategy_service/transfer_coordinator.py`, `strategy-service@1450019e`) adds the emit-time raise. It nets N
per-strategy intra-client transfers into ONE `TransferIntent` per
`client × {unordered venue pair} × asset × transfer_type` (signed sum, drop zero-nets, bidirectional flows collapse) and
raises `CrossClientTransferForbiddenError` on any cross-client `add_request` (defence-in-depth alongside the
execution-service consume-time raise; logs `CROSS_CLIENT_TRANSFER_FORBIDDEN` at ERROR for alert-on-attempt). Both
runtime raises (layer 2 execution-service consume + layer 3 strategy-service emit) are now live; the strategy-service
raise is on the coordinator, not yet on a live per-strategy emit loop (no live transfer-emit pipeline exists in
strategy-service today — the coordinator is the tested, importable primitive future rebalance code builds on).

## Why this is a HARD rule, not a preference

Each client is a **separately-managed account** under its own custody / legal entity. The Odum trading entities
([trading-entities note](../../ikenna_orchestrator/...)) — Odum Research UK and Odum Group Cayman — are different legal
entities operating under different jurisdictions. Cross-client fund movement would:

- **Breach custody boundaries**: client A's wallet keys / venue credentials are scoped to client A's authorisation;
  using them to move funds toward client B's accounts is custody-violation regardless of intent.
- **Breach regulatory boundaries**: separately-managed-account agreements typically forbid commingling. Moving funds
  between client accounts (even temporarily, even with reconciliation) is a regulatory breach.
- **Confuse settlement / reporting**: client-reporting-api computes per-client P&L attribution from on-chain
  - venue transfer histories. Cross-client moves would create attribution ambiguity that propagates into legal reporting
    deliverables.

This is operator/legal/compliance scope — not engineering preference. **Any plan proposal that frames "cross-client
rebalancing" as in-scope must be rewritten as "intra-client" or marked review-blocking.**

## The two legitimate rebalancing scopes

When a plan or codex doc references "rebalancing", "transfer", "fund movement", or "wallet/account migration", it must
scope to exactly one of these:

### (a) Intra-client multi-portfolio rebalancing

Shifting capital allocation between strategy archetypes (portfolios) **for the same client**.

Example: client X is over-allocated to `carry_staked_basis` and wants to reduce that exposure to fund
`arbitrage_price_dispersion`. The IntraClientRebalanceCoordinator:

1. Reads current allocation per archetype for client X from per-archetype position state stores
2. Reads target allocation from client X's clients.yaml configuration
3. Emits TransferIntent(s) where source_account = client_X.carry_staked_basis_wallet and dest_account =
   client_X.arbitrage_price_dispersion_wallet
4. **Invariant**: `source.client_id == dest.client_id == client_X`

### (b) Intra-client multi-wallet / multi-account rebalancing

Moving funds between **different wallets or accounts of the same client**.

Examples (all intra-client X):

- client X's main custody wallet → client X's archetype-specific subaccount (margin top-up)
- client X's Binance subaccount → client X's Coinbase wallet (CEX→CEX bridge via withdrawal+deposit pair)
- client X's Ethereum mainnet wallet → client X's Arbitrum L2 wallet (cross-chain bridge)
- client X's Aave deposit → client X's main wallet (DeFi withdraw)

**Invariant**: in every case, `source.client_id == dest.client_id == client_X`. The CHAIN, VENUE, ACCOUNT_TYPE may
differ; the `client_id` MUST NOT.

## What about strategy-level allocation decisions?

Strategy-service does NOT make cross-client allocation decisions. Each client owns their own allocation policy expressed
in `deployment-service/configs/strategy/{archetype}/clients.yaml`. The IntraClientRebalanceCoordinator reads each
client's policy independently and emits intents per client. If client A wants 60% on archetype X and client B wants 30%,
those are TWO independent intra-client decisions with NO fund movement between A and B.

## What "cross-client" CAN legitimately mean (don't confuse)

Some places in the codebase use "cross-client" in valid, non-fund-movement contexts. These are CORRECT usage, do not
rewrite:

- **`isolation_policy.assert_client_allowed()` "cross-client reject"** in
  `execution-service/execution_service/isolation_policy.py` — the **enforcement** that bus events from client X must not
  be processed by client Y's worker. This is the GOOD pattern preventing accidental contamination.
- **`CrossClientEventError`** — raised when an event-bus subscriber for client X receives an event tagged with client Y.
  Correct usage (rejection at consumer boundary).
- **"Cross-client read-only config"** — supervisor-level config visible to all ClientWorkers in a shard (e.g.
  MarkPriceAggregator's shared-memory dict). Read-only; no fund-movement implication. Prefer "**supervisor-level shared
  config**" wording for clarity, but "cross-tenant config" is also acceptable.

The distinguishing test: if the phrase references **fund movement, transfer, withdrawal, deposit, bridge, balance,
allocation shift, or rebalancing**, it MUST be intra-client. If it references **event processing, isolation enforcement,
or read-only config visibility**, "cross-client" is a valid descriptor.

## Code-level invariants

| Layer                       | Class / function                                                                                                         | Invariant                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Raises                                                                    |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| UAC schema                  | `TransferIntent` (single `client_id: str` field)                                                                         | Structural: one `client_id` per intent — no separate source/dest fields to mismatch; cross-client movement requires two distinct intents                                                                                                                                                                                                                                                                                                                                         | N/A — structural, not a runtime validator                                 |
| strategy-service            | `IntraClientRebalanceCoordinator` (Phase E.3 — SHIPPED 2026-06-23, `strategy-service@1450019e`)                          | At emit time: carries identical `client_id` per emitted TransferIntent + nets per-strategy transfers into one intent per `client × venue-pair × asset × type`; rejects cross-client `add_request`                                                                                                                                                                                                                                                                                | `CrossClientTransferForbiddenError` (emit-time — LIVE on the coordinator) |
| execution-service           | `TransferCoordinator.execute()` (`transfer_coordinator.py:241`)                                                          | At consume time: rejects any TransferIntent whose `client_id` ≠ process-bound CLIENT_ID; logs alert; emits `TransferResult.status = REJECTED_CROSS_CLIENT`                                                                                                                                                                                                                                                                                                                       | `CrossClientTransferForbiddenError` (the only current runtime raise)      |
| execution-service           | `isolation_policy.assert_client_allowed()` (existing)                                                                    | Process-bound `CLIENT_ID` rejects any bus event whose `client_id` differs                                                                                                                                                                                                                                                                                                                                                                                                        | `CrossClientEventError` (already in place)                                |
| execution-service           | `assert_fund_context_client_allowed()` (SHIPPED 2026-08-20, `execution-service@6d43020e`)                                | `TransferAdapter.execute_*` methods (Mock/LiveCcxt/LiveCustody/Composite) now enforce `FundTransferContext.client_id` at call time — closed a real gap: before this, `fund_context` was threaded through as pure metadata and a mismatched context executed silently. Fund-administration-service's redemption path populates it via `client_id=redemption.allocator_id` (`fund-administration-service@ccc751c`).                                                                | `CrossClientTransferForbiddenError`                                       |
| fund-administration-service | `resolve_treasury_source_wallet_id(fund_id, share_class)` (SHIPPED 2026-08-20, `fund-administration-service@b877fa8775`) | Derives a per-`(fund_id, share_class)` treasury source-wallet id for ledger attribution — never the flat process-wide `treasury_wallet_id` default, which would commingle every fund's ledger rows under one label. Not yet wired into the real transfer call (`execute_withdrawal` has no `from_wallet_id` param); precondition for replacing `LocalSimulatedTransferAdapter` with a real custody adapter via the existing `execute_onchain_transfer(from_wallet_id=...)` seam. | N/A — derivation only, no raise site yet                                  |

## Required tests

Every plan that adds transfer / rebalancing / fund-movement code MUST include:

1. **Happy path**: intra-client multi-portfolio rebalance emits valid TransferIntent → TransferCoordinator accepts →
   mock venue receives correctly-scoped call.
2. **Negative path**: construct a TransferIntent with `source.client_id = "client_A", dest.client_id = "client_B"` → UAC
   validator rejects at construction with `CrossClientTransferForbiddenError`.
3. **Defence-in-depth negative**: bypass UAC validator (test-only), submit hand-crafted intent to `TransferCoordinator`
   → coordinator rejects at consume time with `CrossClientTransferForbiddenError`.
4. **Audit-log assertion**: rejected intents produce alert (per alerting-service rule) so operator sees any attempted
   violation in monitoring.
5. **Multi-client batch isolation** (added 2026-08-20, redemption-cadence hardening): when one batch/tick processes
   redemptions for MULTIPLE clients (e.g. `GracePeriodHandler.run_once()`), a test must prove each produces its own
   isolated call with non-overlapping `fund_context`/`destination` — never netted or reordered across clients.
   Idempotency matters here too: the withdrawal call carries `idempotency_key=redemption_id` so a crashed-and-retried
   tick never double-withdraws (`execution-service@d8bae52a`, `fund-administration-service@af9d292`).
6. **Vehicle-type routing** (added 2026-08-20): `unified_api_contracts.internal.domain.strategy_service.client_registry.CLIENT_REGISTRY`
   (`ClientDefinition.vehicle_type: Literal["fund", "sma"]`, required — no default, `unified-api-contracts@60237ba19d`)
   is the SSOT for whether a client_id is a pooled-fund investor or a direct SMA client — resolved 1:1 per client_id
   (a client needing both vehicles gets two distinct client_ids, e.g. `acme-fund`/`acme-sma`, reusing this same
   isolation model rather than adding a new dimension). Fund-administration-service's redemption-creation endpoint
   (`post_redemption()`) rejects `sma`-typed client_ids with `403` before creating an `AllocatorRedemption` —
   `fund-administration-service@fb7dc9d7b1` — since the whole grace-period/NAV-per-share/redemption-fee machinery is
   pooled-fund-only by construction. **client-reporting-api's separate client registry** (`credentials-registry.yaml`
   via `unified_api_contracts.internal.reporting.client_config.ClientConfig`) is genuinely disjoint from
   `CLIENT_REGISTRY` (no join key between the two id spaces) — resolved
   (`plans/archive/2026_08/issues/client_reporting_api_nav_aggregation_vehicle_type_blind_2026_08_20.md`,
   `client-reporting-api@2af6176688`) by reusing `ClientConfig.is_pooled` as the reporting-side vehicle-type proxy
   (`"fund"` if pooled, else `"sma"`) rather than a cross-registry lookup. Both `nav.py` and `fund_operations.py` now
   carry a per-row `vehicleType` label plus a `nav_by_vehicle_type`/`aum_by_vehicle_type` breakdown — the blended
   `current_nav`/`total_aum` totals were deliberately left unchanged rather than excluding `"sma"`-classified clients,
   since only one real client currently sets `is_pooled` at all and excluding everyone else would misrepresent AUM.

## Related SSOTs

- `plans/active/per_client_isolation_and_venue_fanout_topology_2026_05_20.md` — origin plan; Phase E.3 owns the
  IntraClientRebalanceCoordinator.
- `/codex/04-architecture/execution-service-per-client-isolation.md` — existing per-process per-client model that this
  rule layers on top of.
- `/codex/04-architecture/transfer-coordinator.md` — TransferCoordinator facade design (Phase 6).
- `/codex/04-architecture/custody-providers.md` — Copper + CEFFU custody surface (June-1).
- `feedback_cross_client_funds_forbidden.md` (agent memory) — the operator-direction anchor for this rule.

## CeFi margin traceability (margin cluster, 2026-06-15)

CeFi perp margin is traceable end-to-end alongside the DeFi health path. strategy-service
`position/core/margin_event_emitter.py::emit_margin_event_for_cefi` computes margin health via the canonical UTL CeFi
models (`unified_trading_library.get_margin_model`, dispatched on the UAC `MarginModel` enum) off LIVE per-venue
balances and emits a `MarginEvent` with `venue_type="cefi"`. The CeFi model value is a margin-USAGE % (higher = worse —
the inverse of a DeFi health factor); it lands in `MarginHealthSnapshot.margin_usage_pct`, **never** `health_factor` (a
DeFi-only field), and severity maps from the model's own `severity_breach` (MMR bands), not the DeFi HF bands.

Live balances come from `position/core/venue_balance_tracker.py::CefiVenueBalanceReader` (wraps the UPI-backed
`AccountQueryClient` — **not** an execution-service import; the service-dep ban holds) → `PortfolioInputs`.
`position/api/margin_health.py` returns real per-client × venue `MarginHealthSnapshot[]` (model usage % + F28
`get_collateral_haircut` haircut-adjusted `collateral_usd` from the canonical UAC `venue_collateral` SSOT); the GCS
historical time-series is a documented Phase-2 layer on top. SSOT:
`plans/active/engine_findings_remediation_2026_06_15.md` (margin cluster).

## Plan-review checklist (use when filing transfer-related plans)

- [ ] Does any phase emit `TransferIntent`? If yes — explicit invariant statement that source.client_id ==
      dest.client_id is enforced + tested.
- [ ] Does any phase mention "rebalancing" without "intra-client" qualifier? If yes — review-blocking; rewrite.
- [ ] Does the test bundle include the 4 required tests above? If no — review-blocking; add them.
- [ ] Are alert rules wired so an attempted violation pages an operator? If no — file a follow-up.
