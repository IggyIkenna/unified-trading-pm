---
doc_type: plan
title: >-
  Elysium October delivery — production completion and issue fixes ahead of the strategy-service repository send
summary: >-
  Internal plan for closing the gap between what the codebase should contain for the October delivery and what currently
  exists. Four workstreams: (1) a falsifiable code-completion bar for strategy-service, since the operator's decision to
  send that repository is gated on it; (2) finish the custody/transfer layer — the CustodyProvider and TransferAdapter
  protocols are clean, but the per-venue custody-routing matrix was never built and several TransferCoordinator handlers
  are still May-23 stubs; (3) resolve placeholder production values, chiefly the risk thresholds in the client's own
  strategy config; (4) repository send readiness, which is a disclosure-review problem. NOT a carve-out plan — a
  carve-out plan will be authored separately once the October delivery lands.
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos: [execution-service, strategy-service, unified-api-contracts, unified-trading-pm]
scope: [admin, engineer]
tags: [elysium, custody, transfers, production-readiness, commercial-model]
last_updated: "2026-08-11"
related:
  [
    /codex/14-customer-journeys/commercial-model/elysium-carveout-deferral-message-2026-08-11.md,
    /codex/14-customer-journeys/commercial-model/ODUM_SLA_v4_2026-07-24.md,
    /codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html,
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
  Interactive session 2026-08-11. Operator decisions: defer the code carve-out past the October delivery; send the
  strategy-service repository in full once its code lands; standardise the support period at 30 days; and rescope this
  plan away from carve-out extraction to production completion and issue fixes, with a carve-out plan to follow later.
---

# October delivery — production completion and issue fixes

**Scope, stated precisely because it changed on 2026-08-11.** This plan covers the gap between **what the codebase
should contain for the October delivery** and what it contains today. It is **not a carve-out plan** — the carve-out is
deferred past October and will get its own plan when it is scheduled. Extraction, packaging and interface-seam work are
therefore out of scope here.

> **HARD RULE — nothing in this plan appears in a client artefact.** This is the internal gap list. Placeholder values,
> stub handlers, unbuilt routing matrices and missing readers are all recorded here so they get fixed; none of them is
> discussed in the platform-architecture document, the carve-out specification, the strategy-service deep dive or the
> deferral message. The client-facing documents describe the system as it will be delivered. If a gap is material enough
> that a client-facing document would be misleading without it, that is an escalation to the operator, not a licence to
> add it to an artefact.

**Codex SSOTs this plan is checked against** — read before touching the relevant todos:

- [/codex/04-architecture/client-funds-isolation.md](/codex/04-architecture/client-funds-isolation.md) — funds never
  move between clients; `CrossClientTransferForbiddenError` is the structural guarantee
- [/codex/04-architecture/defi-execution-overview.md](/codex/04-architecture/defi-execution-overview.md) — custody
  convention, `DefiErrorCode`
- [/codex/06-coding-standards/quality-gates.md](/codex/06-coding-standards/quality-gates.md) — every code todo ships
  from a green tree

## Measured starting position (2026-08-11, verified against the tree)

Recorded so no todo re-derives it, and so a later session can tell what has moved.

| Thing                               | State                                                                                                          |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `CustodyProvider` Protocol          | **Exists**, clean — `sign_transaction` / `get_balance` / `create_transfer` / `list_wallets` / `health_check`   |
| Custody factory                     | **Exists** — `mock · local_key · cloud_kms · copper · ceffu`                                                   |
| `TransferAdapter` Protocol          | **Exists** — internal transfer / withdrawal / on-chain / status / balance                                      |
| `CompositeTransferAdapter`          | **Exists** — routes internal+withdrawal to CCXT, on-chain to custody                                           |
| `TransferCoordinator`               | **Exists** in both services; `CrossClientTransferForbiddenError` enforced; idempotency cache present           |
| `IntraClientRebalanceCoordinator`   | **Exists** — nets per-pair requests before emitting intents                                                    |
| `TransferInstructionV2` / `Bridge…` | **Exists** — strategy names venue/chain and target balance, never a rail                                       |
| `LiquidationProximityCircuit`       | **Exists** — 7 graded responses (oracle buffer → pause → partial unwind → hedge failover → flash close)        |
| `ArchetypeKillSwitchSubscriber`     | **Exists** — per-archetype arm/disarm over the bus with declared halt behaviour                                |
| Transfer handlers                   | **PARTIAL** — `transfer_coordinator.py` carries "built-in stub handlers (used when no real handler is wired)"  |
| `CustodyRoute` enum                 | **NOT BUILT** — proposed in the archived routing-matrix plan, never implemented                                |
| ClearLoop                           | **NOT IN CODE** — 4 planning docs, 0 source files. Copper's service; we instruct Copper                        |
| `VenueWalletCapabilities`           | **Exists** but `custody_provider` is a single string; no per-chain deposit routing                             |
| Risk thresholds in client config    | **PLACEHOLDERS** — `configs/carry_staked_basis.yaml` header marks them conservative, pending operator approval |
| Funding-rate reader                 | **TEST-ONLY** — only direct-from-venue implementation lives in `e2e-testing`                                   |
| Code-completion bar                 | **DOES NOT EXIST** — Phase 1                                                                                   |

---

## Phase 1 — The code-completion bar (gates the repository send)

- [ ] [OPERATOR] P0. **Define "does everything we need" for strategy-service as a written, falsifiable checklist —
      scoped to CODE completeness only.** Operator clarified 2026-08-11: the strategy-service _code_ completes this
      week; the data pipeline and the live/batch deployment continue to October. The bar gates the repository send on
      code, not on mandate readiness, and the sent message says so explicitly. Enumerate per archetype in scope: which
      decisions it must make, which features it must consume, which instruction types it must emit, and what "correct"
      means for each. Output is a codex doc, not a note in this plan.
- [ ] [AGENT] P0. **Audit strategy-service against the bar once written** and append the gap list here as `- [ ]` todos.
      Do not start closing gaps before the audit — the bar exists to stop scope drifting.
- [ ] [AGENT] P1. **Verify the two contracted archetypes emit every instruction type the mandate requires, end to end.**
      `staked_basis` and `basis_perp` must produce `TradeInstruction`, `StakeInstruction`/`UnstakeInstruction`,
      `TransferInstructionV2` and `AtomicInstruction` correctly.
- [ ] [AGENT] P1. **Productionise the venue funding readers.** The only direct-from-venue implementation is in
      `e2e-testing/scripts/defi/funding_ensemble_engine.py`. `staked_basis` consumes a funding-rate feature and returns
      no decision without it. An engineer reading the sent repository will trace the feature and find a test harness.
- [ ] [AGENT] P2. **Confirm the promotion ladder runs end to end for the contracted archetypes** — candidate, paper,
      early live, live, with the pre-flight gate firing at each step. The deep-dive document describes this to the
      client as a live mechanism, so it must be one.

## Phase 2 — Custody and transfer: finish the layer

> The abstraction is already right. What is missing is the routing matrix beneath it and the handlers behind the
> coordinator. Nothing here requires redesigning the protocols.

- [ ] [AGENT] P0. **Replace the stub `TransferHandler` implementations in
      `execution-service/execution_service/transfer_coordinator.py`.** The file states they exist "when no real handler
      is wired for May-23". Enumerate every `BusTransferType`, state which have real handlers, and implement the rest or
      fail loudly. **A stub returning a success result on a funds-movement path is the highest-risk item in this plan**
      — it reports money moved that did not move.
- [ ] [AGENT] P0. **Add `CustodyRoute` to UAC** as proposed in
      [the archived routing-matrix plan](/plans/archive/issues/venue_chain_custody_routing_matrix_2026_05_12.md):
      `DIRECT_VENUE_WALLET · CLEARLOOP · CEFFU_MIRRORX · COPPER_SUB_ACCOUNT · FIREBLOCKS`. Re-derive that plan's
      recommendation against the current tree first — `VenueWalletCapabilities` has moved since it was written.
- [ ] [AGENT] P0. **Extend `VenueWalletCapabilities` with per-chain deposit routing.** A single `custody_provider`
      string cannot express "this venue's USDT deposits route via ClearLoop on one chain and direct on another", which
      is the operational question when moving capital.
- [ ] [OPERATOR] P1. **Decide whether ClearLoop is modelled explicitly or stays opaque behind Copper.** Explicit makes
      per-route counterparty risk visible for operational due diligence (ClearLoop = LedgerEdge/Copper; MirrorX = CEFFU;
      direct = venue insolvency), which an allocator's ODD will ask about. Opaque is less code, and Copper already
      routes. **Gates the two todos above**, since it decides whether the schema work is one enum or a routing table.
- [ ] [AGENT] P1. **Confirm the treasury-versus-trading split executes, not just types.** `WalletType` has
      `FUNDING · TRADING · SPOT · UNIFIED` and `treasury_monitor.py` exists; verify a treasury → per-strategy trading
      wallet move completes on testnet, and that an instance cannot exceed its `capital_budget_amount`.
- [ ] [AGENT] P1. **Verify `reserve_ratio`-style behaviour exists, or retire the concept.** `rg reserve_ratio` returns
      zero hits fleet-wide, yet an earlier draft of a client document described capital moving "on a reserve ratio".
      Either find the mechanism under its real name and record it, or confirm it does not exist so it never reappears.
- [ ] [AGENT] P2. **Cross-venue capital movement integration test**: treasury → venue A trading wallet → venue B, across
      a CCXT rail and a custody rail, asserting idempotency on replay and refusal across `client_id`.
- [ ] [AGENT] P2. **Record the custody and transfer architecture in codex** once this phase lands — the protocol seam
      plus the routing matrix, `authoritative_for` custody routing. The archived plan is a proposal that was never
      executed; leaving it as the only record is how this gap survived three months.

## Phase 3 — Placeholder and provisional values

- [ ] [OPERATOR] P0. **Approve the real risk thresholds for `configs/carry_staked_basis.yaml`.** The committed file's
      header reads "⚠️ MAY-23 CUTOVER PLACEHOLDER VALUES ⚠️ — Risk thresholds below are CONSERVATIVE PLACEHOLDERS
      pending operator approval". The affected values include `health_factor_target`,
      `health_factor_emergency_reduce_at`, `health_factor_emergency_close_at`, `staking_apr_threshold`,
      `perp_funding_threshold_bps`, `max_leverage` and `capital_usd`. **This is the client's own strategy
      configuration**, and the repository being sent contains that header — so an engineer reading it learns the risk
      limits are unapproved. Approve the values and remove the banner, or the send exposes an open question as a defect.
      Plan-of-record for the values: `drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.md`.
- [ ] [AGENT] P1. **Sweep the contracted archetypes' configs for other placeholder or TODO markers** before the send,
      and list them here. One known banner means the convention exists; assume there are others until measured.
- [ ] [AGENT] P2. **Resolve the stale June/May-2026 dates in SLA v4** — five occurrences, all overtaken by the
      September-readiness / October-acceptance timeline. Tracked in detail on the
      [SLA issue doc](/plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md).

## Phase 4 — Repository send readiness

> Required because the operator decided to send strategy-service in full. This is a disclosure review, not engineering,
> and it is the phase most likely to be underestimated.

- [ ] [OPERATOR] P0. **Scope review: enumerate what the repository discloses before it goes.** All six carry archetypes;
      arbitrage, statistical arbitrage, volatility, market making, directional and liquidity-provision families; the
      risk engine; the position monitor; P&L attribution. Confirm explicitly that disclosing the non-carry families is
      intended — Exhibit B defines Carry & Yield as the contracted scope, so the others are our own IP shown
      voluntarily.
- [ ] [OPERATOR] P0. **Confirm no other client's identifiers, configuration or capital data are present — including in
      git history.** Configs keyed by `client_id`, share classes, wallet identifiers and fixtures are the likely
      carriers. A working-tree scrub does not scrub the log.
- [ ] [AGENT] P1. **Produce the disclosure inventory** for that review: every archetype module, every config naming a
      client, every fixture with real identifiers. Read-only; no deletions without the operator ruling.
- [ ] [OPERATOR] P1. **Decide the transfer mechanism** — snapshot archive, read-only mirror, or time-boxed repository
      grant — and whether it carries a confidentiality acknowledgement beyond the Consulting Agreement.
- [ ] [OPERATOR] P2. **Decide which documentation accompanies the repository.**
      [`carry-venue-live-integration-reference.md`](/codex/02-data/carry-venue-live-integration-reference.md) is worth
      more to a rebuilder than the source: per venue it gives the endpoint, funding field, settlement interval, symbol
      mapping and sign-convention gotcha. It should not travel with the code by default.

## Phase 5 — Client document consistency (hygiene only)

- [x] ✅ [AGENT] P0. **Support period standardised at 30 days** (operator ruling 2026-08-11, reversing the 2026-08-09
      ruling of 60). `ODUM_SLA_v4_2026-07-24.md` §1 line 88, §3 line 131 and §5 line 220 all read 30. §11's "sixty (60)
      days' notice" for Option-A termination is a **different term** and was deliberately left alone.
- [x] ✅ [AGENT] P0. **WITHDRAWN — the premise was wrong.** A previous revision of this plan claimed
      `platform-architecture.html` carried 8-archetype / 13-venue counts needing correction. Cross-check 2026-08-11
      found it states **no archetype or venue total at all** — zero `N of M` patterns. Those counts existed only in
      `carveout-engineering.html` rev 1.0 and were already fixed there. Recorded rather than deleted because the error
      was mine: I asserted a defect in one document from a measurement taken on another.
- [x] ✅ [AGENT] P1. **All four client-facing artefacts consolidated into
      [`/codex/14-customer-journeys/commercial-model/`](/codex/14-customer-journeys/commercial-model/)** alongside the
      existing Elysium materials, and cross-checked against each other. Support period consistent at 30 days across all
      of them; ClearLoop wording corrected to credit Copper; the carve-out specification gained an
      inspection-is-not-transfer note reconciling its narrower package scope against sending the full repository.
- [ ] [OPERATOR] P0. **Reissue or side-letter the SLA to make 30 days binding.** The copy in the client's hands states
      **sixty (60) calendar days** in its substantive §3, under an express "substantive provisions prevail" clause.
      **Editing our record does not reduce their entitlement.** This was optional cleanup before the 30-day ruling; it
      is now the step that gives the ruling effect.
- [ ] [AGENT] P2. **Correct Exhibit A's non-resolving adapter paths** in the SLA manifest — real paths already verified
      and recorded on the issue doc. Wants a wording review before it lands.
- [ ] [AGENT] P3. **Re-check every client HTML document for the `var()`-in-SVG trap and count drift before any send**,
      per the [authoring notes](/codex/14-customer-journeys/commercial-model/elysium-presentation-authoring-notes.md).

## Deferred — carve-out extraction (separate plan, not scheduled)

Recorded here only so the work is not lost. **Do not start any of it under this plan.** A carve-out plan will be
authored after the October delivery, per the operator's 2026-08-11 decision and the
[deferral message](/codex/14-customer-journeys/commercial-model/elysium-carveout-deferral-message-2026-08-11.md).

- [ ] [OPERATOR] P3. **DO NOT START — build the eleven-package extraction structure.** Specified in
      `carveout-engineering.html` as a proposal; not built. Belongs to the future carve-out plan.
- [ ] [OPERATOR] P3. **DO NOT START — build `contracts-platform`, the ten-interface seam.** The specification commits us
      to producing it if a CTO asks to see it, which is the one item here with an external trigger.
- [ ] [OPERATOR] P3. **DO NOT START — local, static and mock implementations behind each of the ten interfaces**: mocks,
      documented extension points, static universe and frozen config.
- [ ] [OPERATOR] P3. **DO NOT START — run the nine-condition hand-over acceptance test** specified in the carve-out
      document's §06.
- [ ] [OPERATOR] P3. **DO NOT START — carve-out estimate stands at ~1 week concentrated for a beta**, production-grade
      longer again. Revised 2026-08-11 from the earlier ~3-day figure after the operator began the work.

### Research-contribution path — specification deferred with the above

- [ ] [AGENT] P2. **Specify how the client runs their own ideas through our backtests.** The launch path is
      `deployment-api` (`test_strategy_backtest_launch` and `test_execution_backtest_launch` exist, so the endpoints are
      real). Define what they submit, what isolation applies, what comes back, and what they may not see. The deep-dive
      document describes this at a level that now needs the detail behind it.
- [ ] [OPERATOR] P2. **Decide the commercial and IP treatment of client-contributed research.** If they propose a
      parameter set or variant that works, who owns it — this interacts with Consulting Agreement Art. 4 and Exhibit B's
      non-compete. Answering it before a contribution exists is much easier than after.
- [ ] [AGENT] P3. **Document the promotion ladder as the client sees it** — candidate through paper to live, the
      pre-flight gates, and which steps they can observe or approve under the managed service.

## Progress Log

- **2026-08-11** — Plan created, then **rescoped the same day on operator instruction: this is no longer a carve-out
  plan.** It now covers production completion and issue fixes only; carve-out extraction is deferred to a separate plan
  and is listed at the end purely so it is not lost. The measured starting position was recorded rather than assumed and
  changed Phase 2 materially: the custody and transfer abstraction is **already agnostic and clean** (`CustodyProvider`
  and `TransferAdapter` protocols, `CompositeTransferAdapter` routing by transfer kind, `TransferInstructionV2` naming a
  target balance rather than a rail), so this is completion work rather than design work. Three genuine gaps found by
  reading the tree: **`CustodyRoute` was proposed in a plan archived ~3 months ago and never built**;
  **`transfer_coordinator.py` still carries stub handlers labelled "for May-23"** — a stub returning success on a
  funds-movement path is the highest-risk item here; and **the client's own strategy config carries a placeholder banner
  on its risk thresholds**, which the repository send would expose. **ClearLoop appears in 4 planning documents and 0
  source files** — it is Copper's service, and our code instructs Copper. Also corrected an error of my own: a todo
  asserting `platform-architecture.html` carried wrong counts, which it never did.
