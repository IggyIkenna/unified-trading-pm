---
doc_type: plan
title: >-
  Elysium October delivery — strategy-service completion bar, custody/transfer agnostic completion, and code-disclosure
  readiness
summary: >-
  Execution plan for everything the 2026-08-11 Elysium decisions created. Four workstreams: (1) define and meet a
  falsifiable completion bar for strategy-service, because the operator's decision to send that repository is gated on
  "it does everything we need" and no checklist exists; (2) finish the custody/transfer agnostic layer — the
  CustodyProvider and TransferAdapter protocols exist and are clean, but the per-venue custody-routing matrix was never
  built and several TransferCoordinator handlers are still May-23 stubs; (3) reconcile and complete the client document
  set, including a new artifact showing what the code looks like without sending it; (4) make strategy-service actually
  sendable, which is a disclosure-scrub problem because the repository holds every archetype across every family plus
  the risk engine and attribution.
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos: [execution-service, strategy-service, unified-api-contracts, unified-trading-pm]
scope: [admin, engineer]
tags: [elysium, carve-out, custody, transfers, client-communication, commercial-model]
last_updated: "2026-08-11"
related:
  [
    /codex/14-customer-journeys/commercial-model/elysium-carveout-deferral-voice-note-2026-08-11.md,
    /codex/14-customer-journeys/commercial-model/ODUM_SLA_v4_2026-07-24.md,
    /presentations/elysium/carveout-engineering.html,
    /plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md,
    /plans/archive/issues/venue_chain_custody_routing_matrix_2026_05_12.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-11
parent_epic: client_isolation_and_governance_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 14
estimate_calibrated_ai_days: 11.2
assigned_role:
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Interactive session 2026-08-11. Operator decisions: defer the code carve-out past the October delivery; offer the
  strategy-service repository instead but only once complete; standardise the support period at 30 days everywhere;
  cover the strategy- and asset-group-agnostic setup in client material for the ongoing-contract case rather than the
  carve-out case.
---

# Elysium October delivery — completion bar, custody completion, disclosure readiness

Everything below follows from four operator decisions taken on 2026-08-11, recorded in
[the voice-note record](/codex/14-customer-journeys/commercial-model/elysium-carveout-deferral-voice-note-2026-08-11.md).
The decision that generates the most work is the smallest sentence: **the strategy-service repository goes to the
client, but not until it "does everything we need".** That is currently unfalsifiable, so it is Phase 1.

**Codex SSOTs this plan is checked against** — read before touching the relevant todos, do not duplicate their content
here:

- [/codex/04-architecture/client-funds-isolation.md](/codex/04-architecture/client-funds-isolation.md) — funds never
  move between clients; `CrossClientTransferForbiddenError` is the structural guarantee
- [/codex/04-architecture/defi-execution-overview.md](/codex/04-architecture/defi-execution-overview.md) — custody
  `CLOUD_KMS_ENCRYPTED` convention, `DefiErrorCode`
- [/codex/04-architecture/tier-and-import-architecture.md](/codex/04-architecture/tier-and-import-architecture.md) — the
  tier rule that makes the carve-out closure computable
- [/codex/06-coding-standards/quality-gates.md](/codex/06-coding-standards/quality-gates.md) — every code todo here
  ships from a green tree

## Measured starting position (2026-08-11, verified against the tree)

Recorded so no todo below re-derives it, and so a later session can tell what has moved.

| Thing                               | State                                                                                                         |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `CustodyProvider` Protocol          | **Exists**, clean — `sign_transaction` / `get_balance` / `create_transfer` / `list_wallets` / `health_check`  |
| Custody factory                     | **Exists** — `mock · local_key · cloud_kms · copper · ceffu`                                                  |
| `TransferAdapter` Protocol          | **Exists** — internal transfer / withdrawal / on-chain / status / balance                                     |
| `CompositeTransferAdapter`          | **Exists** — routes internal+withdrawal to CCXT, on-chain to custody                                          |
| `TransferCoordinator`               | **Exists** in both execution-service and strategy-service; `CrossClientTransferForbiddenError` enforced       |
| `IntraClientRebalanceCoordinator`   | **Exists** — nets per-pair requests before emitting intents                                                   |
| `TransferInstructionV2` / `Bridge…` | **Exists** — strategy names venue/chain and target balance, never a rail. This is the agnosticism, in a type  |
| Transfer handlers                   | **PARTIAL** — `transfer_coordinator.py` carries "built-in stub handlers (used when no real handler is wired)" |
| `CustodyRoute` enum                 | **NOT BUILT** — proposed in the archived routing-matrix plan, never implemented                               |
| ClearLoop                           | **NOT IN CODE** — 4 planning docs, 0 source files. Code has no notion of which rail a transfer takes          |
| `VenueWalletCapabilities`           | **Exists** but `custody_provider` is a single string; no per-chain deposit routing                            |
| Completion bar for strategy-service | **DOES NOT EXIST** — this plan's Phase 1                                                                      |

---

## Phase 1 — The completion bar (gates the client send; do this first)

- [ ] [OPERATOR] P0. **Define "does everything we need" for strategy-service as a written, falsifiable checklist.** The
      operator's 2026-08-11 decision sends this repository once complete; until the bar exists the send cannot be
      scheduled and the voice note's promise has no resolution date. Enumerate per archetype in scope: which decisions
      it must make, which features it must consume, which instruction types it must emit, and what "correct" means for
      each. Output is a new codex doc, not a note in this plan.
- [ ] [AGENT] P0. **Audit strategy-service against the bar once written** and produce a gap list as `- [ ]` todos
      appended to this plan. Do not start closing gaps before the audit — the point of the bar is to stop scope
      drifting.
- [ ] [AGENT] P1. **Verify the two contracted archetypes emit every instruction type the mandate requires end to end.**
      `staked_basis` and `basis_perp` must produce `TradeInstruction`, `StakeInstruction`/`UnstakeInstruction`,
      `TransferInstructionV2` and `AtomicInstruction` correctly, and the funding-rate feature dependency must resolve —
      see the standing P0 in the
      [SLA issue doc](/plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md).
- [ ] [AGENT] P1. **Productionise the venue funding readers into the licensed set.** Carried forward as the recommended
      next item from the previous session and now also a Phase-1 blocker: an engineer reading the sent repository will
      trace `features["funding_rate_apy_bps"]` and find nothing outside `e2e-testing`.
- [ ] [OPERATOR] P2. **Decide whether the completion bar is shared with the client.** A written bar is a strong artefact
      — it converts "when it's ready" into an agreed definition — but it also fixes our obligations in writing before
      the SLA is settled. Deliberate choice, not a default.

## Phase 2 — Custody and transfer: finish the agnostic layer

> The abstraction is already right. What is missing is the routing matrix beneath it and the handlers behind the
> coordinator. Nothing in this phase requires redesigning the protocols.

- [ ] [AGENT] P0. **Replace the stub `TransferHandler` implementations in
      `execution-service/execution_service/transfer_coordinator.py`.** The file states they exist "when no real handler
      is wired for May-23". Enumerate every `BusTransferType`, state which have real handlers, and implement the rest or
      fail loudly rather than returning a synthetic success. **A stub that returns a success result on a funds-movement
      path is the single highest-risk item in this plan.**
- [ ] [AGENT] P0. **Add `CustodyRoute` to UAC** as proposed in
      [the archived routing-matrix plan](/plans/archive/issues/venue_chain_custody_routing_matrix_2026_05_12.md):
      `DIRECT_VENUE_WALLET · CLEARLOOP · CEFFU_MIRRORX · COPPER_SUB_ACCOUNT · FIREBLOCKS`. The plan was archived without
      implementation; re-derive its recommendation against the current tree before coding, since
      `VenueWalletCapabilities` has moved since.
- [ ] [AGENT] P0. **Extend `VenueWalletCapabilities` with per-chain deposit routing.** `custody_provider` as a single
      string cannot express "Binance USDT deposits route via ClearLoop on one chain and direct on another", which is the
      actual operational question when moving capital.
- [ ] [OPERATOR] P1. **Decide whether ClearLoop is modelled explicitly or stays opaque behind Copper.** Both are
      defensible: explicit modelling makes counterparty risk per route visible for operational due diligence (ClearLoop
      = LedgerEdge/Copper; MirrorX = CEFFU; direct = venue insolvency) and is what an allocator's ODD will ask about;
      opaque is less code and Copper already handles routing. **The decision changes whether Phase 2's schema work is
      one enum or a routing table**, so it gates the two todos above.
- [ ] [AGENT] P1. **Confirm the treasury-versus-trading wallet split is a real runtime path, not just a type.**
      `WalletType` has `FUNDING · TRADING · SPOT · UNIFIED` and `treasury_monitor.py` exists; verify a capital move from
      treasury to a per-strategy trading wallet executes end to end on testnet, and that a strategy cannot consume more
      than its `capital_budget_amount`.
- [ ] [AGENT] P1. **Verify `reserve_ratio`-style behaviour exists or correct the claim.** `rg reserve_ratio` returns
      zero hits fleet-wide, yet rev 1.0 of the carve-out document described capital moving "on a reserve ratio". Either
      the mechanism exists under another name — find it and record the name — or the claim was wrong and must not
      reappear in client material.
- [ ] [AGENT] P2. **Cross-venue capital movement integration test**: treasury → venue A trading wallet → venue B, across
      both a CCXT rail and a custody rail, asserting idempotency on replay and refusal across `client_id`.
- [ ] [AGENT] P2. **Record the custody/transfer architecture in codex** once Phase 2 lands — one doc, the protocol seam
      plus the routing matrix, `authoritative_for` custody routing. The archived plan is not a substitute; it is a
      proposal that was never executed, and leaving it as the only record is how this gap survived three months.

## Phase 3 — Client document set

- [ ] [AGENT] P0. **Fix `platform-architecture.html`: archetype count 8 → 6, venue-adapter count 13 → 20.** Both
      re-derived 2026-08-11. Republish to artifact `cd44b148-6752-437c-919f-d8b4cef42cba` (favicon 🏛️ — keep stable) and
      pass the URL or a duplicate artifact is created.
- [x] ✅ [AGENT] P0. **Support period standardised at 30 days everywhere** (operator ruling 2026-08-11, reversing the
      2026-08-09 ruling of 60). `ODUM_SLA_v4_2026-07-24.md` §1 line 88, §3 line 131 and §5 line 220 now all read 30.
      §11's "sixty (60) days' notice" for Option A termination is a **different term** and was deliberately left alone.
      `platform-architecture.html` already read 30 and is now consistent rather than contradictory.
- [ ] [OPERATOR] P0. **Reissue or side-letter the SLA to make 30 days actually binding.** The copy already in the
      client's hands states **sixty (60) calendar days** in its substantive §3, and the docx executive summary carries
      an express "substantive provisions prevail" clause. **Editing our record does not reduce their entitlement** — on
      the sent drafting they can hold us to 60. This was previously an optional cleanup; the 30-day ruling makes it the
      step that gives the ruling effect.
- [ ] [AGENT] P1. **Build the "what the code looks like" artifact** — deliverable 4 of 5. Contents agreed 2026-08-11:
      how to circuit-break the strategy; the full configuration surface at both the strategy and execution layers; the
      real strategy↔execution contracts (`StrategyInstructionEnvelope` + the 11 instruction subtypes); how an external
      strategy would be fed in; the data schemas; and how the client could contribute research by running their own
      ideas through backtests. **The last two belong to the ongoing-relationship case, not the carve-out case.**
- [ ] [AGENT] P1. **Cover the strategy- and asset-group-agnostic design in the ongoing-contract framing** (operator,
      2026-08-11): the same engine and instruction contract serve DeFi, CeFi, TradFi, sports and prediction, so
      multi-asset-group expansion is configuration plus an adapter rather than a new system. Explicitly _not_ a
      carve-out property — the carved package is static by construction.
- [ ] [AGENT] P1. **Reconcile `carveout-engineering.html` with the decision to send the whole strategy repository.** The
      document tells them the package is 2 of 6 carry archetypes; the repository contains all six plus every other
      family plus the risk engine, position monitor and attribution. **Two client-facing artefacts that contradict each
      other is worse than either position alone.** Either the document acknowledges the wider disclosure or the send is
      scoped down; that is Phase 4's first todo.
- [ ] [AGENT] P2. **Correct Exhibit A's non-resolving adapter paths** in the SLA manifest — carried from the previous
      session; real paths already verified and recorded on the issue doc. Wants a wording review before it lands.
- [ ] [AGENT] P3. **Re-check both HTML documents for the `var()`-in-SVG trap and count drift before any send**, per the
      [presentation README](/presentations/elysium/README.md) traps list.

## Phase 4 — Make strategy-service actually sendable

> This phase exists only because of the decision to send the whole repository. It is a disclosure-review problem, not an
> engineering one, and it is the phase most likely to be underestimated.

- [ ] [OPERATOR] P0. **Scope review before anything is sent: enumerate what the repository discloses.** All six carry
      archetypes; arbitrage, statistical arbitrage, volatility, market making, directional and liquidity-provision
      families; the risk engine; the position monitor; P&L attribution. Confirm explicitly that disclosing the non-carry
      families is intended — Exhibit B's non-compete clarification defines the Carry & Yield family as the contracted
      scope, so the other families are our own IP being shown voluntarily.
- [ ] [OPERATOR] P0. **Confirm no other client's identifiers, configuration or capital data are in the repository or its
      history.** Configuration under `client_id`, share classes, wallet identifiers and test fixtures are the likely
      carriers. **Git history counts** — a scrub of the working tree does not scrub the log.
- [ ] [AGENT] P1. **Produce the disclosure inventory** for the operator review above: every archetype module, every
      config file naming a client, every fixture containing real identifiers. Read-only; no deletions without the
      operator ruling.
- [ ] [OPERATOR] P1. **Decide the transfer mechanism and its terms** — a snapshot archive, a read-only mirror, or a
      time-boxed repository grant — and whether it carries a written confidentiality acknowledgement beyond the existing
      Consulting Agreement.
- [ ] [OPERATOR] P2. **Decide which documentation accompanies the repository.**
      [`carry-venue-live-integration-reference.md`](/codex/02-data/carry-venue-live-integration-reference.md) is worth
      more to a rebuilder than the source: per venue it gives the endpoint, funding field, settlement interval, symbol
      mapping and sign-convention gotcha. It should not travel with the code by default.

## Phase 5 — Research contribution path (ongoing relationship)

- [ ] [AGENT] P2. **Specify how the client runs their own ideas through our backtests.** Launch path is `deployment-api`
      (`test_strategy_backtest_launch` / `test_execution_backtest_launch` exist as unit tests, so the endpoints are
      real). Define what they submit, what isolation applies, what they get back, and what they may not see.
- [ ] [OPERATOR] P2. **Decide the commercial and IP treatment of client-contributed research.** If they propose a
      parameter set or a variant that works, who owns it — this interacts with Consulting Agreement Art. 4 and Exhibit
      B's non-compete, and answering it after they have contributed something is much worse than answering it before.
- [ ] [AGENT] P3. **Document the promotion ladder as the client sees it** — candidate through paper to live, the
      pre-flight gates, and which steps they can observe or approve under the managed service.

## Progress Log

- **2026-08-11** — Plan created from the interactive session's operator decisions. Measured starting position recorded
  in the table above rather than assumed, and it changed the shape of Phase 2 materially: the custody/transfer
  abstraction is **already agnostic and clean** (`CustodyProvider` and `TransferAdapter` protocols,
  `CompositeTransferAdapter` routing by transfer kind, `TransferInstructionV2` naming a target balance rather than a
  rail), so this is completion work, not design work. Two genuine gaps found: **`CustodyRoute` was proposed in a plan
  archived ~3 months ago and never built**, and **`transfer_coordinator.py` still carries stub handlers labelled "for
  May-23"** — a stub returning success on a funds-movement path is the highest-risk item here. **ClearLoop appears in 4
  planning documents and 0 source files**, so "Copper uses ClearLoop under the hood" is true of the product but
  invisible to our code. Also carried in: the 30-day standardisation (done), and the observation that it needs a
  client-facing reissue to have any effect, since the sent copy's binding §3 says 60 with a "substantive provisions
  prevail" clause.
