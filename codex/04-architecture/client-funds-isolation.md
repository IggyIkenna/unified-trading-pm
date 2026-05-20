# Client Funds Isolation — HARD RULE

**Codified 2026-05-20** per operator direction during Group H per-client isolation plan filing.

## The rule

**Funds NEVER move between different clients.** Every transfer (CEX withdrawal, DeFi deposit/withdraw, bridge,
sub-account move, rebalancing) operates within the scope of a single `client_id`. Source account and destination account
MUST share the same `client_id`.

Enforced at three layers (defence in depth):

1. **UAC schema layer**: `TransferIntent.source_account.client_id` and `TransferIntent.dest_account.client_id` are
   carried explicitly on every intent. UAC validator rejects construction where they differ.
2. **Strategy-service emission layer**: `IntraClientRebalanceCoordinator` (Phase E.3 of
   `plans/active/per_client_isolation_and_venue_fanout_topology_2026_05_20.md`) refuses to emit any TransferIntent where
   source/dest client_ids differ. Raises `CrossClientTransferForbiddenError` at emit time.
3. **Execution-service consumer layer**: `TransferCoordinator` (Phase 6 of same plan) rejects any TransferIntent where
   source/dest client_ids differ. Raises `CrossClientTransferForbiddenError` at consume time. This is the final gate
   before any RPC call hits a venue or chain.

Each layer alone is sufficient to block the violation; all three together make accidental cross-client moves impossible
via the canonical code paths.

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

| Layer             | Class / function                                        | Invariant                                                                                                                                          | Raises                                                  |
| ----------------- | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| UAC schema        | `TransferIntent` (Phase 1 of per-client-isolation plan) | Validator on construction: `source_account.client_id == dest_account.client_id`                                                                    | `CrossClientTransferForbiddenError` (construction-time) |
| strategy-service  | `IntraClientRebalanceCoordinator` (Phase E.3)           | At emit time: every TransferIntent emitted by this coordinator carries identical `client_id` on source + dest                                      | `CrossClientTransferForbiddenError` (emit-time)         |
| execution-service | `TransferCoordinator` (Phase 6)                         | At consume time: rejects any TransferIntent where source/dest client_ids differ; logs alert; emits `TransferResult.status = REJECTED_CROSS_CLIENT` | `CrossClientTransferForbiddenError` (consume-time)      |
| execution-service | `isolation_policy.assert_client_allowed()` (existing)   | Process-bound `CLIENT_ID` rejects any bus event whose `client_id` differs                                                                          | `CrossClientEventError` (already in place)              |

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

## Related SSOTs

- `plans/active/per_client_isolation_and_venue_fanout_topology_2026_05_20.md` — origin plan; Phase E.3 owns the
  IntraClientRebalanceCoordinator.
- `codex/04-architecture/execution-service-per-client-isolation.md` — existing per-process per-client model that this
  rule layers on top of.
- `codex/04-architecture/transfer-coordinator.md` — TransferCoordinator facade design (Phase 6).
- `codex/04-architecture/custody-providers.md` — Copper + CEFFU custody surface (June-1).
- `feedback_cross_client_funds_forbidden.md` (agent memory) — the operator-direction anchor for this rule.

## Plan-review checklist (use when filing transfer-related plans)

- [ ] Does any phase emit `TransferIntent`? If yes — explicit invariant statement that source.client_id ==
      dest.client_id is enforced + tested.
- [ ] Does any phase mention "rebalancing" without "intra-client" qualifier? If yes — review-blocking; rewrite.
- [ ] Does the test bundle include the 4 required tests above? If no — review-blocking; add them.
- [ ] Are alert rules wired so an attempted violation pages an operator? If no — file a follow-up.
