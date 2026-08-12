---
doc_type: plan
title: >-
  Elysium October delivery — close the gap between what the client documents assert and what the code contains
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
tags: [elysium, custody, transfers, production-readiness, audit, commercial-model]
last_updated: "2026-08-11"
related:
  [
    /codex/14-customer-journeys/commercial-model/elysium-carveout-deferral-message-2026-08-11.md,
    /codex/14-customer-journeys/commercial-model/ODUM_SLA_v4_2026-07-24.md,
    /codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html,
    /codex/14-customer-journeys/commercial-model/platform-architecture.html,
    /codex/14-customer-journeys/commercial-model/carveout-engineering.html,
    /plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md,
    /plans/archive/issues/venue_chain_custody_routing_matrix_2026_05_12.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/solana_lst_carry_jupiter_perps_and_kamino_borrow_2026_08_12.md,
    /plans/active/issues/check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md,
  ]
created: 2026-08-11
parent_epic: client_isolation_and_governance_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 16
estimate_calibrated_ai_days: 12.8
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

# October delivery — the claims audit

**What this plan is.** Three documents are now in the client's hands or about to be. They assert specific things about
the system. This plan closes the distance between those assertions and the code — in the direction of **making the code
true** wherever that is the right answer, and correcting the document wherever it is not.

**Two hard constraints, from the operator, 2026-08-11:**

1. **No new repositories and no new packages.** Nothing here creates a carve-out repo, a lite repo or an extraction
   package. Every item lands inside an existing repository.
2. **Every fix follows the existing architecture** — the tier model, the instruction contract, the typed-config pattern,
   the protocol-plus-factory pattern for pluggable providers, and the existing service boundaries. If a gap seems to
   need a new architectural concept, that is a signal the gap was misdiagnosed: stop and re-read the relevant codex
   SSOT.

> **HARD RULE — nothing in this plan appears in a client artefact.** This is the internal gap list. If a gap is material
> enough that a client document would be misleading without disclosing it, that is an operator escalation, not a licence
> to add it to an artefact.

**Codex SSOTs each fix is checked against:** [client-funds-isolation](/codex/04-architecture/client-funds-isolation.md)
· [defi-execution-overview](/codex/04-architecture/defi-execution-overview.md) ·
[tier-and-import-architecture](/codex/04-architecture/tier-and-import-architecture.md) ·
[config-reloader-pattern](/codex/06-coding-standards/config-reloader-pattern.md) ·
[quality-gates](/codex/06-coding-standards/quality-gates.md)

## A. The claims audit — verified 2026-08-11

Every row is a load-bearing assertion from a client document, checked against the tree. **Verified** means the named
symbol or behaviour was read in source. This table is the audit; the todos below are what it produced.

| Claim (document)                                             | Status         | Evidence / gap                                                                            |
| ------------------------------------------------------------ | -------------- | ----------------------------------------------------------------------------------------- |
| 11 instruction types + shared envelope (deep dive §02)       | **VERIFIED**   | `architecture_v2/schemas.py` — all 11 subtypes + `StrategyInstructionEnvelope` read       |
| Targets not deltas, so re-emission is idempotent (§02)       | **VERIFIED**   | `target_position_units`, `target_balance_at_destination`, `target_staked_amount`          |
| `eligible_venues` + `SOR_AT_EXECUTION` boundary (§02)        | **VERIFIED**   | Envelope fields present with that default                                                 |
| Atomic multi-leg with leader, deadline, compensation (§02)   | **VERIFIED**   | `AtomicInstruction`, `AtomicLeg`, `CompensationPolicy`                                    |
| `V2EngineOrchestrator` ticks archetypes (§01, §07)           | **VERIFIED**   | `engine/strategies/v2/orchestrator.py`; `register_instance`; 55 `on_tick` implementations |
| ~22 typed config schemas (§03)                               | **VERIFIED**   | `config.py` — all `TypedDict`, counted                                                    |
| Family defaults under `configs/defaults/` (§03)              | **VERIFIED**   | 8 default files                                                                           |
| `LiquidationProximityCircuit`, 7 graded responses (§04)      | **VERIFIED**   | All seven private methods read                                                            |
| `ArchetypeKillSwitchSubscriber`, per-archetype halt (§04)    | **VERIFIED**   | `on_armed` / `on_disarmed` / `is_archetype_halted` / `halt_behaviour`                     |
| `CustodyProvider` protocol + 5 providers (§05)               | **VERIFIED**   | Protocol + factory over mock/local_key/cloud_kms/copper/ceffu                             |
| `CompositeTransferAdapter` routes by transfer kind (§05)     | **VERIFIED**   | CCXT for internal + withdrawal, custody for on-chain                                      |
| Netting before intents exist (§05)                           | **VERIFIED**   | `IntraClientRebalanceCoordinator`                                                         |
| Cross-client transfer structurally impossible (§05)          | **VERIFIED**   | `CrossClientTransferForbiddenError` raised in `TransferCoordinator`                       |
| 19 API route modules (§06)                                   | **VERIFIED**   | Counted, all present                                                                      |
| Batch/live determinism verdict is produced (§09, platform)   | **VERIFIED**   | `batch-live-reconciliation-service`: `trade_recon.py`, daily determinism handler + stage  |
| Copper integration is live (§05)                             | **VERIFIED**   | `custody/copper.py` — sign, poll, balance, transfer, wallets, health                      |
| ClearLoop is Copper's mechanism, not our code (§05)          | **VERIFIED**   | 0 source hits fleet-wide; wording already credits Copper                                  |
| Promotion ladder candidate → paper → early live → live (§09) | **PARTIAL**    | `CANDIDATE`, `PAPER_1D`, `live_early` found; **no terminal full-live state confirmed**    |
| "Strategy families present" count (§08, factbar)             | **WAS WRONG**  | `StrategyFamily` has **9** members; document said 8 and invented "liquidity provision"    |
| "Attestation on every instruction" (§07 inherit-list)        | **WAS WRONG**  | `attestations=` populated only in MEV modules, **not** the carry archetypes               |
| Backtests launch through the deployment API (§09)            | **UNVERIFIED** | Inferred from test _filenames_; no endpoint decorator located. Verify or soften           |
| Capital budget enforced per instance (§07 inherit-list)      | **UNVERIFIED** | `capital_budget` in 13 modules; **no enforcement guard read**                             |
| Transfer handlers are real (implied by §05)                  | **FALSE**      | `transfer_coordinator.py` carries stub handlers "for May-23"                              |

## B. Close the unverified claims — do these first, a document asserts each one

- [ ] [AGENT] P0. **Verify capital-budget enforcement, or build it.** The deep dive tells the client an external
      strategy inherits "capital budget enforcement per instance". `capital_budget_amount` is on
      `StrategyInstanceDefinition` and appears in 13 modules, but no guard was read that refuses an instruction
      exceeding it. Find the enforcement point; if there is none, add it in `allocation_sizer.py` or the existing risk
      gate — **not a new component**.
- [ ] [AGENT] P0. **Verify the backtest launch path end to end, or correct §09.** `test_strategy_backtest_launch.py` and
      `test_execution_backtest_launch.py` exist in `deployment-api`, but no route decorator for a backtest endpoint was
      located. **Test filenames are a proxy, not the endpoint.** Exercise the real launch and record the route, or
      soften the document.
- [ ] [AGENT] P1. **Confirm the promotion ladder's terminal state.** `CANDIDATE`, `PAPER_1D` and `live_early` exist; the
      final full-live state was not confirmed. Two documents describe a four-rung ladder — either the fourth rung exists
      under another name (record it) or the ladder is three rungs and both documents need correcting.
- [ ] [AGENT] P1. **Decide whether the carry archetypes should populate `attestations`.** The field is on every
      instruction; only the MEV modules fill it. For a regulated allocator an attestation trail is a due-diligence
      answer, so populating it is probably right — but it is a deliberate choice, and the document has been softened so
      nothing is misstated meanwhile.
- [ ] [AGENT] P2. **Reconcile the two family enums.** `StrategyFamily` (mechanism axis, 9 members) and
      `StrategyFamilyId` (risk-aggregation axis) both exist, and `StrategyFamily` is declared in **two** places
      (`architecture_v2/enums.py` and `canonical/crosscutting/strategy_family.py`). Establish which is SSOT and whether
      the second is a re-export or a duplicate — an ambiguous count is what produced the document error above.

## C. Production gaps found by reading the tree

- [ ] [AGENT] P0. **Replace the stub `TransferHandler` implementations** in
      `execution-service/execution_service/transfer_coordinator.py`. The file states they exist "when no real handler is
      wired for May-23". Enumerate every `BusTransferType`, state which have real handlers, implement the rest or fail
      loudly. **A stub returning success on a funds-movement path reports money moved that did not move** — the
      highest-risk item in this plan. Fix within the existing handler protocol; introduce no new abstraction.
- [ ] [OPERATOR] P0. **Approve the real risk thresholds for `configs/carry_staked_basis.yaml`.** Its header reads
      "MAY-23 CUTOVER PLACEHOLDER VALUES — Risk thresholds below are CONSERVATIVE PLACEHOLDERS pending operator
      approval", covering `health_factor_target`, `health_factor_emergency_reduce_at`,
      `health_factor_emergency_close_at`, `staking_apr_threshold`, `perp_funding_threshold_bps`, `max_leverage` and
      `capital_usd`. **This is the client's own configuration, and the repository being sent contains that banner.**
      Values plan-of-record is the drawdown/liquidation strategy-risk-config plan dated 2026-05-23, which is now
      **archived** — so the plan of record for these unapproved thresholds is no longer active. Confirm it is still the
      intended source before approving.
- [ ] [AGENT] P0. **Productionise the venue funding readers.** The only direct-from-venue implementation lives in
      `e2e-testing/scripts/defi/funding_ensemble_engine.py`; `staked_basis` consumes a funding-rate feature and returns
      no decision without it. Land them in `features-service` following the existing calculator pattern — **no new
      repo**.
- [ ] [AGENT] P1. **Add `CustodyRoute` to UAC**, per
      [the archived routing-matrix plan](/plans/archive/issues/venue_chain_custody_routing_matrix_2026_05_12.md):
      `DIRECT_VENUE_WALLET · CLEARLOOP · CEFFU_MIRRORX · COPPER_SUB_ACCOUNT · FIREBLOCKS`. Re-derive that plan against
      the current tree first — `VenueWalletCapabilities` has moved since it was written.
- [ ] [AGENT] P1. **Extend `VenueWalletCapabilities` with per-chain deposit routing.** A single `custody_provider`
      string cannot express "this venue's deposits route via ClearLoop on one chain and direct on another".
- [ ] [OPERATOR] P1. **Decide whether ClearLoop is modelled explicitly or stays opaque behind Copper.** Explicit makes
      per-route counterparty risk visible for operational due diligence; opaque is less code and Copper already routes.
      **Gates the two todos above.**
- [ ] [AGENT] P1. **Confirm the treasury-versus-trading split executes, not just types.** Verify a treasury →
      per-strategy trading wallet move completes on testnet, and that an instance cannot exceed its budget.
- [ ] [AGENT] P1. **Verify `reserve_ratio`-style behaviour exists or retire the concept.** Zero hits fleet-wide, yet an
      early document draft described capital moving "on a reserve ratio". Find it under its real name or confirm
      absence.
- [ ] [AGENT] P2. **Sweep the contracted archetypes' configs for other placeholder or TODO markers** and list them here.
      One known banner means the convention exists; assume more until measured.
- [ ] [AGENT] P2. **Cross-venue capital movement integration test** — treasury → venue A → venue B across a CCXT rail
      and a custody rail, asserting idempotency on replay and refusal across `client_id`.
- [ ] [AGENT] P2. **Record the custody and transfer architecture in codex** once C lands: the protocol seam plus the
      routing matrix, `authoritative_for` custody routing. The archived plan is a proposal that was never executed, and
      leaving it as the only record is how this gap survived three months.

## D. Code-completion bar — gates the repository send

- [ ] [OPERATOR] P0. **Define "does everything we need" for strategy-service as a falsifiable checklist — CODE
      completeness only.** The operator clarified that the code completes this week while data and live/batch deployment
      continue to October, and the sent message says exactly that. Enumerate per archetype: decisions it must make,
      features it must consume, instruction types it must emit, and what "correct" means. Output is a codex doc.
- [ ] [AGENT] P0. **Audit strategy-service against the bar once written**, appending gaps here as todos. Do not start
      closing gaps before the bar exists — it is what stops scope drifting.
- [ ] [AGENT] P1. **Verify the two contracted archetypes emit every required instruction type end to end** —
      `TradeInstruction`, `StakeInstruction`/`UnstakeInstruction`, `TransferInstructionV2`, `AtomicInstruction`.

## E. Repository send readiness — disclosure review, not engineering

- [ ] [OPERATOR] P0. **Enumerate what the repository discloses before it goes.** All nine declared families, the risk
      engine, the position monitor, P&L attribution. Confirm that disclosing the non-carry families is intended —
      Exhibit B defines Carry & Yield as the contracted scope, so the rest is our own IP shown voluntarily.
- [ ] [OPERATOR] P0. **Confirm no other client's identifiers, configuration or capital data are present — including in
      git history.** A working-tree scrub does not scrub the log.
- [ ] [AGENT] P1. **Produce the disclosure inventory** for that review. Read-only; no deletions without a ruling.
- [ ] [OPERATOR] P1. **Decide the transfer mechanism** — snapshot, read-only mirror or time-boxed grant — and whether it
      carries a confidentiality acknowledgement beyond the Consulting Agreement.
- [ ] [OPERATOR] P2. **Decide which documentation accompanies the repository.**
      [`carry-venue-live-integration-reference.md`](/codex/02-data/carry-venue-live-integration-reference.md) is worth
      more to a rebuilder than the source. It should not travel with the code by default.

## F. Document consistency

- [x] ✅ [AGENT] P0. **Support period standardised at 30 days.** Operator ruling 2026-08-11, recorded in
      [`/codex/14-customer-journeys/commercial-model/elysium-carveout-deferral-message-2026-08-11.md`](/codex/14-customer-journeys/commercial-model/elysium-carveout-deferral-message-2026-08-11.md),
      reversing the 2026-08-09 ruling of 60 days recorded in
      [`/plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md`](/plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md).
      `ODUM_SLA_v4` §1/§3/§5 all read 30; §11's "sixty (60) days" Option-A termination notice is a different term and
      was left alone deliberately.
- [x] ✅ [AGENT] P0. **Deep-dive factual errors corrected**: family count 8 → **9** with the real member names (the
      earlier list invented "liquidity provision"), and "compliance attestation on every instruction" softened to "the
      attestation field on every instruction", since only the MEV modules populate it.
- [x] ✅ [AGENT] P0. **WITHDRAWN — premise was wrong.** An earlier revision claimed `platform-architecture.html` carried
      8-archetype / 13-venue counts needing correction; it states **no totals at all**. Those existed only in
      `carveout-engineering.html` rev 1.0 and were already fixed. Recorded because the error was mine: I asserted a
      defect in one document from a measurement taken on another.
- [x] ✅ [AGENT] P0. **Stale duplicates removed.** Moving the artefacts into codex left the old
      `presentations/elysium/*` paths and the old `…voice-note…` path live on origin, because `safe-doc-push` copies
      _named files_ into an isolated worktree and a deletion is not a file to copy. **Four stale copies of client-facing
      documents existed simultaneously.** Deleted, and the lesson recorded in the authoring notes.
- [x] ✅ [AGENT] P1. **All client artefacts consolidated and cross-checked** in
      [`/codex/14-customer-journeys/commercial-model/`](/codex/14-customer-journeys/commercial-model/).
- [ ] [OPERATOR] P0. **Reissue or side-letter the SLA to make 30 days binding.** The copy in the client's hands states
      **sixty (60) calendar days** in its substantive §3 under an express "substantive provisions prevail" clause.
      **Editing our record does not reduce their entitlement.**
- [ ] [AGENT] P2. **Correct Exhibit A's non-resolving adapter paths** in the SLA manifest; real paths already verified.
- [ ] [AGENT] P2. **Resolve the five stale June/May-2026 dates in SLA v4.**
- [ ] [AGENT] P3. **Re-check every client HTML for the `var()`-in-SVG trap and count drift before any send**, per the
      [authoring notes](/codex/14-customer-journeys/commercial-model/elysium-presentation-authoring-notes.md).

## G. Deferred — carve-out extraction (separate plan; DO NOT START)

- [ ] [OPERATOR] P3. **DO NOT START — the eleven-package extraction structure.** Specified in
      `carveout-engineering.html` as a proposal, not built.
- [ ] [OPERATOR] P3. **DO NOT START — `contracts-platform`, the ten-interface seam.** The document commits us to
      producing it if a CTO asks to see it: the one deferred item with an external trigger.
- [ ] [OPERATOR] P3. **DO NOT START — local, static and mock implementations behind the ten interfaces.**
- [ ] [OPERATOR] P3. **DO NOT START — the nine-condition hand-over acceptance test** from the document's §06.
- [ ] [OPERATOR] P3. **DO NOT START — carve-out estimate stands at ~1 week concentrated for a beta**, production-grade
      longer again.
- [ ] [AGENT] P2. **Specify how the client runs their own ideas through our backtests** — depends on the backtest-path
      verification in section B.
- [ ] [OPERATOR] P2. **Decide the commercial and IP treatment of client-contributed research** before a contribution
      exists rather than after.
- [ ] [AGENT] P3. **Document the promotion ladder as the client sees it** — depends on confirming its terminal state.

## H. Unified transfer model — investigation outcomes and the build (2026-08-12)

Operator direction: build the manual route and the full composite key + ratios, **but investigate first** — check codex
for existing discussion and conflicts, scan for existing behaviour, consolidate the SSOT in the right place rather than
adding slop. Rotation: audit per module before migrating. Duplicates: investigate the UAC pair before picking a home.

### H.1 The UAC "duplicates" are three legitimate layers — earlier claim CORRECTED

I previously recorded "TransferStatus/TransferResult declared in four places". **That conflated three different concepts
that share a name.** Measured 2026-08-12:

| Declaration                                            | Actual concept                                        | Enum members                                                                                                                                          |
| ------------------------------------------------------ | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `canonical/crosscutting/transfer_events.py`            | **The canonical bus contract**, strategy→execution    | `BusTransferType`, `TransferPurpose`, `TransferResultStatus`                                                                                          |
| `internal/domain/defi/transfers.py`                    | On-chain transfer **observation/verification**        | `TransferStatus`: PENDING SUBMITTED CONFIRMING CONFIRMED FAILED BRIDGING BRIDGE_COMPLETE; `TransferType`: SAME_CHAIN/CROSS_CHAIN (topology, not rail) |
| `execution-service/engine/transfers/adapter.py`        | Adapter-level result (implementation detail)          | `TransferStatus`: PENDING CONFIRMED FAILED                                                                                                            |
| `fund-administration-service/.../transfer_protocol.py` | **Deliberate structural mirror** of the adapter types | same 3 — docstrings say "Mirrors …" / "Narrow structural view over …"                                                                                 |

**`transfer_events.py` is already the intended SSOT**: it sits in `canonical/`, its docstring states it "replaces the
fragmented transfer surfaces in execution-service (CEX withdrawals, DeFi protocol deposits/withdrawals, bridges,
sub-account moves) with a single `TransferIntent` → `TransferResult` pair routed through `TransferCoordinator`", and it
already carries a `§ SSOT reconciliation` section. **The manual route therefore belongs there, not in a new module.**

- [ ] [AGENT] P1. **Resolve the one real type debt: `BusTransferType` vs `transfer_types.TransferType` "overlapping
      values"**, which `transfer_events.py` names in its own docstring. Decide whether the rail enum collapses into the
      bus taxonomy or stays a separate axis, and record the ruling in the docstring's reconciliation section.
- [ ] [AGENT] P2. **Decide the fate of the fund-admin mirror.** It exists because the tier model forbids service→service
      imports, so it is defensible — but the fields must be hand-synced across two repos. Either promote the
      adapter-level pair into UAC so both import it, or leave the mirror and add a test asserting field parity. **Do not
      simply delete it** — that would break the tier rule it was written to respect.
- [ ] [AGENT] P3. **Audit the three `deployment-api` treasury route modules** (`treasury.py`, `treasury_routes.py`,
      `client_treasury.py`) for genuine duplication versus deliberate separation, before touching any of them.

### H.2 The manual route — the actual gap

`TransferType` (the rail axis) has exactly three members: `ON_CHAIN`, `CEX_WITHDRAWAL`, `CEX_INTERNAL`. **All three are
API-executed.** A bookmaker deposit or a bank wire cannot be represented, so the model is crypto-only and not unified
across asset groups. `ApprovalBus` (`WithdrawalRequestedEvent` / `WithdrawalApprovedEvent`) provides human _approval of
a system-executed_ transfer — the inverse of what is needed.

- [ ] [AGENT] P0. **Add the manual/off-system route to the canonical bus taxonomy** in `transfer_events.py`, with a real
      state machine rather than a flag: `AWAITING_MANUAL_ACTION → ASSERTED_BY_OPERATOR → RECONCILED_AGAINST_BALANCE`.
      The system must never report settled on an operator assertion alone — a balance check closes it. This is what
      makes a manual movement UTS-compatible instead of a note in a spreadsheet.
- [ ] [AGENT] P0. **Add `CustodyRoute` as the rail axis** — ClearLoop (via Copper), direct on-chain, CEX internal, CEX
      withdrawal, **manual** — so the contract states what interface a transfer finally lands on. Supersedes the
      narrower framing in section C: the enum is the rail, the manual member is what unifies the asset groups.
- [ ] [AGENT] P0. **Manual TRADE capture in execution-service**, not just manual transfers. Betting venues will be
      operated by hand initially, and the fills still have to book in canonical form — same instruction contract, same
      ledgers, same attribution — or the sports asset group is invisible to reconciliation and P&L. Verify whether any
      manual-fill path exists before building.
- [ ] [AGENT] P1. **Reconcile the manual route against `withdrawal_approval_rules.py`** in UAC so approval and manual
      execution compose rather than conflict.

### H.3 Keying — prior art exists; read it before designing

Measured: `VenueWalletCapabilities` is keyed by **venue only** (`venue`, `deposits_to`, `trading_wallet_type`,
`requires_internal_transfer`). `FundTransferContext` carries `fund_id`, `share_class`, `allocation_id` — fund-level, not
client/account. Client isolation is enforced at the `TransferCoordinator`. `WalletType` gives
FUNDING/TRADING/SPOT/UNIFIED. **No `(client × venue × account_type × purpose)` key exists, and `reserve_ratio` is zero
hits fleet-wide.**

- [ ] [AGENT] P0. **READ FIRST, before any schema change:**
      `/codex/14-customer-journeys/shared-core/treasury-and-subaccount-model.md` and
      `/codex/14-customer-journeys/shared-core/fund-administration-and-custody.md`. The operator's recollection that
      treasury and client concepts already exist in some capacity is **confirmed** — a treasury-and-subaccount model is
      already written down. Reconcile against it and report conflicts rather than designing in parallel.
- [ ] [AGENT] P0. **Then extend to the full composite key + ratios**: `(client_id × venue × account_type × purpose)`
      with `purpose ∈ {TREASURY, TRADING}`, a strategy-settable reserve ratio, and `VenueWalletCapabilities` keyed per
      `(venue, chain)` rather than per venue. Venues span TradFi (IBKR), CeFi (Binance), DeFi (ERC-20 wallet) and manual
      books, so the key must hold all four without special cases.
- [ ] [AGENT] P1. **Consolidate the SSOT in one place and delete what it supersedes** — the operator's explicit
      constraint is no slop. If the treasury model already declares part of this, extend that declaration rather than
      adding a second one.

### H.4 Rotation research — audit per module before migrating

`e2e-testing/scripts/defi/` holds eight research modules: `funding_ensemble_engine`, `funding_regime_classifier`,
`funding_reversion_crossvenue_book`, `funding_reversion_multivenue_capital`, `funding_reversion_paper_trade`,
`staked_basis_funding_scan`, `plot_funding_history`, `launch_perp_funding_vm.sh`. Production holds only
`rotation_lending.py` (archetype) and `funding_dispersion.py` (analysis) in the carry package.

- [ ] [AGENT] P1. **Audit each of the eight against what production already ships**, per module, before migrating any of
      them. The risk is productionising a second implementation of `funding_dispersion` — the exact duplication class
      this section exists to prevent.
- [ ] [AGENT] P2. **Then migrate the survivors as optionality, not by force**: regime classification and dispersion into
      `features-service` as versioned calculators; reversion books into `strategy-service` as archetypes **registered
      but not enabled for any client**. Nothing turns on by default.
- [ ] [AGENT] P2. **Check `/plans/active/cross_venue_funding_reversion_research_2026_07_24.md` for conflicts** before
      migrating — an active plan already covers cross-venue funding reversion and may own some of these modules.

### H.5 Strategy composition and rotation breadth — AUDITED 2026-08-12, all four already built

**Headline: the operator's recollection was right on all four counts, and the honest finding is that this section
required almost no building.** What it required was reading. Each item below is ticked against source, and the one real
gap it surfaced is carried to H.7.

- [x] [AGENT] P0. ✅ **Composite = architecture (a): many instances, one archetype each, composed by the allocator with
      weights.** The allocator IS the composition layer, and it composes on TWO levels: - **Across instances** —
      `ClientAllocatorInstance.run()` (`strategy_service/portfolio_allocator/service.py`) takes `list[StrategySlot]`
      keyed by `strategy_instance_id`, produces `target_weights` per instance, and emits ONE `AllocationDirective` per
      client per tick. `apply_guard_rails` then constrains those weights by per-weight cap, turnover, correlation and
      **family + category diversification** — so "weights on archetypes" is expressed as weights on instances plus
      family-level guard rails. - **Within an axis** — the **rank allocator engines** do the coin/venue/protocol
      weighting the operator described. `_hierarchical_rank_weight` (`archetypes_rank.py`) is a 2-stage shape: group by
      an axis token, score the group by `avg(metric)`, filter by threshold, truncate to `top_n_groups`, then per
      surviving group filter and truncate to `top_n_per_group` and weight by metric. Axis tokens in use: coin, venue,
      protocol, expiry, LST. This confirms the H.3 reading — `StrategyInstanceDefinition` carrying ONE `archetype_id`
      and ONE `capital_budget_amount` is correct by design, not a limitation. **No composite-archetype or new
      composition concept should be built.** Keying work in H.3 can proceed on that basis.
- [x] [AGENT] P0. ✅ **Collateral-driven selection exists, and it gates SLOT EMISSION rather than switching at runtime —
      a stronger design than the one the operator asked for.** `accepted_perp_collateral(perp_venue)` reads the UAC
      `VENUE_COLLATERAL_MATRIX`; `_staked_basis_eligible()`
      (`engine/strategies/v2/target_universe/catalog_staked_basis.py`) means an (LST × perp_venue) pair that the venue
      cannot margin **is never emitted as a slot**, so the allocator can only ever weight feasible instances. Structure
      selection itself is `_derive_structure` (`carry_and_yield/staked_basis.py`): LST accepted → `LST_AS_MARGIN` with
      the venue's haircut; otherwise fall back to `USDC_MARGIN_BUFFERED` on USDC/USDT preference; neither → reject. The
      stETH-vs-wstETH nuance the operator raised is handled **and goes beyond the matrix**: `_BANNED_LST_PERP_COMBOS` is
      a defence-in-depth denylist for combinations the matrix technically permits but which are semantically wrong —
      `(wstETH, BYBIT)` and `(wstETH, DERIBIT)` because those margin engines credit the rebasing stETH balance rather
      than the wstETH price, and `(stETH, OKX)` because OKX does no daily rebase reconciliation and marks undersized
      each epoch. Each entry carries its reason inline.
- [x] [AGENT] P1. ✅ **ADV/volume filters exist and are wired — but the dynamic ranking is OPT-IN and defaults OFF.**
      `_resolve_dynamic_carry_coins()` is gated on `StrategyServiceConfig.enable_dynamic_carry_universe`, whose default
      is `False`: OFF returns the static coin list with **zero GCS I/O** (there is a regression test asserting live
      behaviour is byte-for-byte preserved), ON ranks by real ADV via `rank_top_n_by_adv`. On any failure it falls back
      to the static list rather than shrinking the catalog to zero, and logs loudly. **So "ADV-filtered" is true of the
      capability and false of the current default** — do not describe the running system as ADV-filtered without saying
      the flag is off. Whether to turn it on for the Elysium instance is an operator call (H.7).
      `engine/core/canonical_adv_ranked_universe_provider.py` is Layer 1 dynamic candidate discovery, built from the
      operator's own 2026-07-23 ask, and is consumed by `target_universe/catalog_carry.py`;
      `engine/core/rolling_adv_reader.py` provides the rolling window. Two things worth knowing: it is a **T4-local
      reader of the same GCS corpus** features-service's `adv.py` computes over, deliberately not an import (the
      no-service-imports tier rule), because `adv.py` computes on the fly and persists nothing there is to read. And its
      docstring records **path-convention corrections verified against real prod objects** where `adv.py`'s documented
      shape is wrong — an extra `instrument_type=` segment, and `timeframe=1d` not `24h`.
- [x] [AGENT] P1. ✅ **The dispersion basket is already built, and it is genuinely two-sided.**
      `CarryFundingDispersionEngine` (`carry_and_yield/funding_dispersion.py`, archetype `CARRY_FUNDING_DISPERSION`,
      registered `factory.py:73`) goes **LONG when `funding_rank_pct <= long_rank_pct` and SHORT when
      `>= 1 - short_rank_pct`** (both default 0.3333), sizing `target_units = target_equity * signed / mid_price`. It is
      explicit that this is **dollar-neutral, NOT delta-neutral** — the legs are different coins so they do not
      price-cancel, and residual beta is hedged at BOOK level, not leg-vs-leg. It carries a per-leg squeeze veto (cut a
      long that is crashing / a short that is squeezing on a >2σ 2-day adverse move) and honest-absence handling (rank
      absent → emit nothing, explicitly not flat). The cross-sectional rank is computed upstream and arrives
      per-instrument as a feature — which is precisely the two-level composition model established above. **Two
      allocator-level dispersion archetypes also exist**: `CARRY_FUNDING_DISPERSION_RANK` and
      `ARBITRAGE_PRICE_DISPERSION_RANK`.

### H.7 Findings from the H.5 audit

- [ ] [OPERATOR] P1. **The SOL-side staked-basis bundle currently has ZERO eligible (LST, perp_venue) pairs.** DRIFT was
      removed from the UAC `VENUE_COLLATERAL_MATRIX` on 2026-07-16 in the Solana-perp-DEX cull, and
      `catalog_staked_basis.py` records that no other live venue accepts JitoSOL or mSOL as `LST_AS_MARGIN`. The gating
      logic is behaving correctly — it emits nothing rather than emitting an infeasible slot — but the effect is that
      SOL staked basis is structurally unavailable, not merely unfunded. **Operator decision: re-admit a venue, accept
      USDC-margin-buffered structure for SOL, or retire the SOL bundle.** Not an engineering fix.
- [x] [SCRIPT] P2. ✅ **The "8 allocator archetypes" claim was systemic, not one stale docstring — fixed in all four
      places.** `ALLOCATOR_ARCHETYPE_REGISTRY` holds **17** engines; the figure 8 appeared in
      `portfolio_allocator/__init__.py`, in `/codex/03-services/portfolio-allocator.md` **three times including its
      `authoritative_for:` facet** (a frontmatter facet asserting authority over a wrong count — which is precisely how
      doc-retrieval lands a reader on it), and in
      `/codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md`. **Doc and code agreed with each other
      and both were wrong** — a false consensus, and the reason the entire Phase-8 rank-allocator group including both
      dispersion allocators stayed invisible to me for most of this session. All four now describe the two groups with
      **no total**, and the roster is de-duplicated: `03-services` owns it and `cross-cutting` points at it, since
      maintaining two copies is what let them drift to the same wrong number. **Evidence: strategy-service@66edb20d4d**
      (`__init__.py` docstring; `ALL QUALITY GATES PASSED (43s)`, real exit 0) + the two codex docs in this push.
- [x] [AGENT] P1. ✅ **Wrote the missing `CARRY_FUNDING_DISPERSION` archetype doc** —
      `/codex/09-strategy/architecture-v2/archetypes/carry-funding-dispersion.md`. It was implemented,
      factory-registered and had a target universe with **no entry in `archetypes/`**, found by mapping all 60
      `StrategyArchetype` members to expected doc slugs rather than eyeballing the directory. The doc leads with the
      misreading most likely to cost money: this is cross-sectional **price** reversion, not a funding-carry harvest,
      and dollar- not delta-neutral.
- [x] [AGENT] P2. ✅ **Corrected four stale counts and one dead link in `/codex/09-strategy/architecture-v2/README.md`**
      — "57 archetypes" (twice) against an enum of 60; "57 docs — all archetypes documented", which was **false**;
      `cross-cutting/ (10 docs)` against **31**; and a pointer to `templates/archetype-doc.md` which has **never
      existed**. Counts replaced with the verification command plus an exemplar doc, and a standing note that doc count
      ≠ archetype count (the directory also holds `-inv`/variant companions and `status: superseded` rename stubs).
- [x] [SCRIPT] P2. ✅ **`build_funding_dispersion()`'s docstring named four venues where its own tuple holds six** — the
      omissions being the two conditional CFTC-regulated perp venues (Kalshi-perp, edge TBD pending data accumulation;
      Polymarket-perp, `BLOCKED-UPSTREAM-OUTAGE` on DNS NXDOMAIN). The docstring now points at the tuple instead of
      duplicating it. **Evidence: strategy-service@66edb20d4d.**

- [ ] [AGENT] P2. **Two archetypes remain undocumented** — `TSMOM_BTC_CTA` (mentioned only in
      `category-instrument-coverage.md`) and `ARBITRAGE_SPORTS_DUTCHING` (**zero** codex mentions anywhere). Both need
      an `archetypes/*.md` written from source, modelled on `carry-basis-perp.md`. Deliberately scoped rather than done
      blind: writing an archetype spec requires reading its engine, and a guessed spec is worse than an acknowledged
      gap. Both are named in the README's own gap table so they cannot be silently forgotten.
- [x] [AGENT] P2. ✅ **Operator ruled ON (2026-08-12): "Turn it ON."** Default flipped `False → True` so ADV-ranked
      dynamic candidate discovery is the running behaviour, not just an available capability — which is what the
      operator asked for on 2026-07-23 and what makes "dynamic coin rotation" true of the _running system_. **Evidence:
      strategy-service@d1092e9d32** (`ALL QUALITY GATES PASSED`, real exit 0). Retagged from `[OPERATOR]` the moment the
      decision landed. The reproducibility debt this creates is H.8's P0, NOT this todo.
- [ ] [SCRIPT] P3. **`/codex/03-services/portfolio-allocator.md` describes a service that does not exist as a repo.** It
      is titled `portfolio-allocator-service` and said "Not inside strategy-service — separate service with its own
      lifecycle"; the code is at `strategy_service/portfolio_allocator/` and **no such repo is in the 26-repo estate**
      (verified). A correction banner is now in place, but the body still reads target-as-present. Either finish the
      rewrite to present-tense-plus-target, or split the target into its own design doc.

### H.8 Dynamic carry universe is ON — the reproducibility debt it creates (2026-08-12)

`enable_dynamic_carry_universe` default flipped `False → True` on operator instruction — **Evidence:
strategy-service@d1092e9d32** (`ALL QUALITY GATES PASSED`, real exit 0). Two consequences, one of which is a hard-rule
breach that must not be left implicit.

- [ ] [AGENT] P0. **Stamp the resolved dynamic-universe as-of date into the run manifest, so a batch rerun reproduces a
      paper run's coin set automatically.** Today `_resolve_as_of_date_cached(None)` resolves "yesterday UTC" at catalog
      import and the resolved value is recorded **nowhere machine-readable** — so a rerun of paper window W resolves a
      DIFFERENT universe and **`paper(W) == batch-rerun(W)` fails**. That equality is a HARD RULE
      ([paper-batch-live-reconciliation](/codex/09-strategy/operational/paper-batch-live-reconciliation.md)) **and an
      assertion in the client-facing documents**, which is what makes this P0 rather than a nicety: with the flag ON,
      the default configuration silently violates a published guarantee. Until this lands, the mitigation is manual —
      pin `DYNAMIC_CARRY_UNIVERSE_AS_OF_DATE` on any run whose trades must reproduce. Interim provenance shipped with
      the flag flip: the resolved date, coin set and pin-status are now logged at INFO on the success path (which
      previously logged nothing at all) plus a warning when unpinned, so a run's universe is at least recoverable from
      its logs. Note `RunManifest` is not defined in strategy-service, so scope the writer's location before starting.
- [x] [AGENT] P2. ✅ **Service-level scope RAISED and ACCEPTED by the operator (2026-08-12): "that's fine they can have
      it."** The flag sits on the `StrategyServiceConfig` singleton and `TARGET_UNIVERSE` is built once at module
      import, so turning it on moves the carry universe for **every** client the service runs, not just Elysium. Raised
      because the instruction was phrased per-instance; the operator ruled that all clients getting the dynamic universe
      is the intended outcome. **No further work** — per-client universes would require moving universe resolution off
      the import-time singleton, and that is explicitly NOT wanted. Retagged from `[OPERATOR]` since the decision is
      made.

### H.9 Jupiter perps — verified, and it does NOT restore SOL staked basis (2026-08-12)

Operator asked whether any liquid, non-hacked Solana perp venue remains. **Answer: Jupiter, and only Jupiter** — but the
collateral check that decides the staked-basis question came back negative.

**Measured against the UAC collateral registry** (`COLLATERAL_REGISTRY`, richer than `VENUE_COLLATERAL_MATRIX`): of
seven venues with collateral policies, **exactly one accepts a Solana LST — `kamino`, and its `venue_kind` is `lending`,
not `perp_cex`.** No perp venue anywhere in the registry accepts JitoSOL, mSOL, bSOL or even plain SOL as margin.
Hyperliquid's own policy note already states the consequence: _"No LST accepted as direct perp margin → staked-basis
runs straight-basis here."_

**Verified against Jupiter's own documentation** (`developers.jup.ag/docs/perps/`, fetched 2026-08-12): the JLP pool
custodies exactly six tokens — **SOL, ETH, BTC, USDC, USDT, JupUSD** — and collateral is side-dependent: _"SOL / wETH /
wBTC for long positions"_, _"USDC / USDT for short positions"_. **No LST appears anywhere.** A staked-basis trade needs
to short SOL perp while posting the LST as margin; on Jupiter a short requires USDC/USDT, so the LST cannot be the
margin token. Jupiter therefore yields `USDC_MARGIN_BUFFERED` for SOL, never `LST_AS_MARGIN`.

> **Integration work now lives in its own plan (2026-08-12):**
> [solana_lst_carry_jupiter_perps_and_kamino_borrow](/plans/active/solana_lst_carry_jupiter_perps_and_kamino_borrow_2026_08_12.md)
> — authored on operator instruction for full cross-repo integration, held at `status: draft` because it is gated on
> both an explicit operator decision to re-add a Solana perp venue AND an economics answer (is the stable borrow rate
> reliably below the staking yield). The todos below stay here as the Elysium-side decision record; the build steps are
> there.

- [ ] [OPERATOR] P2. **Decide whether to scope Jupiter PERPS integration** — the codex requires an explicit new operator
      decision (`/codex/04-architecture/solana-defi-coverage.md`: _"Do not re-add without an explicit new operator
      decision"_). What it buys: Solana perp hedge legs return for dispersion and straight basis, on the venue the
      operator already named as the intended one ($716M TVL at cull time, never hacked). What it does NOT buy: SOL
      staked basis — see the verification above. Cheaper than a cold start because Jupiter **spot** is already
      integrated (reference-data adapter, execution swap connector, and a live connector shipped 2026-08-08); the
      missing piece is perps, which our adapter does not emit (it emits `SPOT_PAIR` only) and the execution protocol
      does not cover (swap-only).
- [ ] [AGENT] P3. **If Jupiter perps is approved, add its `CollateralPolicy` to the UAC registry as a first step** —
      `venue_kind=PERP_DEX`, accepted collateral SOL/wETH/wBTC (long) and USDC/USDT (short), sourced to
      `developers.jup.ag/docs/perps/`. Doing this before any adapter work means `_staked_basis_eligible()` and
      `_derive_structure()` correctly resolve SOL to `USDC_MARGIN_BUFFERED` and emit no infeasible `LST_AS_MARGIN` slots
      — the gating logic then needs no change at all.
- [ ] [AGENT] P3. **Kamino is the unexplored Solana LST route.** It accepts JitoSOL/mSOL at a 15% haircut and is already
      in the collateral registry, so Solana LST carry may be expressible as a **lending/borrow** structure
      (`CARRY_RECURSIVE_BORROW_*`) rather than a perp-hedged basis. Assess whether that is a real strategy or a dead end
      before treating SOL LST carry as blocked on a perp venue.

### H.6 Gate findings — the two defects that hid a one-line violation for seven attempts (2026-08-12)

Found by paying the cost, per the workspace rule that a tool which misled you is itself a finding. Both are in
`scripts/plan-hygiene/check_reference_paths.py` / `run_hygiene_sweep.sh` and affect every agent who stages a doc.

**Moved out of this plan 2026-08-12 →
[check_reference_paths silent-skip and quiet-hides-violation](/plans/active/issues/check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md)**,
with the four fix todos. These are workspace plan-hygiene tooling defects affecting every agent who stages a doc, not
Elysium delivery work, so they belong in an issue doc rather than riding along in a client-delivery plan — correct
triage per the findings-triage rule, and it keeps this plan's todo list answerable to the October date.

The two defects in one line each, so this section still explains the seven failed pushes it was written to record: the
checker's `--only` mode **silently skips any path it cannot stat and then returns exit 0** (so "0 violations locally"
was a false negative from the wrong working directory, and it anchored six wrong diagnoses), and the hygiene sweep runs
it with `--quiet`, which **prints the violation count without the filename**.

## Progress Log

- **2026-08-12 — measurement lesson, recorded because it is the SECOND proxy-vs-property slip in one session.** I ran
  `bash scripts/quality-gates.sh --no-fix 2>&1 | tail -45` in the background, was notified "exit code 0", and reported
  the gate green. **That 0 was `tail`'s exit code, not the gate's** — a shell pipeline reports its LAST command's
  status, so piping a gate through `tail`/`grep`/`head` discards the verdict and replaces it with "did the pager run".
  The output file was exactly 45 lines, which is the tell. Compounding it, the visible tail showed only a
  peripheral-directory ruff warning, which read as "nearly clean" when in fact the summary had been cut off. **Rule:
  never pipe a gate. Redirect the full log to a file and capture `$?` on its own line**
  (`bash scripts/quality-gates.sh > "$LOG" 2>&1; echo "EXIT=$?"`), then read the log. Same shape as the
  `check_reference_paths` false negative earlier the same day — exit 0 from something that never did the work — which is
  why this is worth writing down rather than filing as a one-off slip.
- **2026-08-12 (fourth pass — codex ↔ code reconciliation)** — Operator asked for the remaining fixes plus a
  reconciliation of codex and strategy-service docs. **The root cause of my own H.5 blind spot turned out to be a
  documentation defect, not my search technique: the codex allocator SSOT and the code docstring both said "8 allocator
  archetypes" against a registry of 17, and they corroborated each other.** A false consensus between doc and code is
  far more dangerous than either being wrong alone, because cross-checking one against the other confirms the error.
  Fixed in all four locations, including an `authoritative_for:` frontmatter facet that asserted authority over the
  wrong count. Roster de-duplicated so two codex docs no longer maintain parallel tables — that duplication is what let
  both drift to the same wrong number. Wrote the missing `CARRY_FUNDING_DISPERSION` archetype doc (implemented and
  registered, zero codex entry) after reconciling all 60 enum members against doc slugs; corrected four stale counts and
  a never-existent `templates/archetype-doc.md` link in the architecture-v2 README, replacing counts with the command
  that derives them. Two archetypes remain undocumented and are now named in the README's own gap table rather than
  hidden behind an "all archetypes documented" claim that was false. **Refinement to yesterday's ADV tick:** the dynamic
  ADV universe is real but `enable_dynamic_carry_universe` defaults **False**, so "ADV-filtered" describes the
  capability and not the running default — now an operator decision. **Counter-finding worth keeping:** the client
  documents' "26 repositories" is right and the naive recount (31 `.git` dirs) is wrong — five are history-rewrite
  backup clones sharing a remote. Recorded in the authoring notes with the distinct-remote command, because the next
  person to measure will otherwise "correct" a correct number.

- **2026-08-12 (third pass)** — **H.5 audited; all four operator asks were already built.** Composite composition is
  architecture (a) and the allocator composes on two levels (across instances via `target_weights` + family/category
  guard rails, within an axis via the 2-stage hierarchical rank engines) — so H.3 keying can proceed and **no
  composite-archetype concept should be built**. Collateral-driven selection gates slot EMISSION, which is stronger than
  runtime switching, and already encodes the stETH/wstETH per-venue nuance in a reasoned denylist. ADV filters exist and
  are wired. The dispersion basket is complete and two-sided. Two findings raised to H.7 (SOL staked-basis has zero
  eligible pairs; the allocator docstring undercounts its registry). **Three published-document corrections, all of the
  same class — an asserted total that rotted:** the carry-archetype count was 6 and is 7 (the missed one is
  `CARRY_FUNDING_DISPERSION`, i.e. the number was wrong _because_ the dispersion capability was unknown); "liquidity
  provision" was listed as a `StrategyFamily` in `carveout-engineering.html` and in the deferral record, having been
  fixed in the deep dive a day earlier and missed in the other two. **And a correction to my own correction**: I had
  recorded that family as "invented", which is wrong — `DEFI_LP_CONCENTRATED`/`_POOL`/`_VAULT` are real archetypes, so
  liquidity provision is a genuine capability that was merely misfiled as a family. Recording an error's shape
  imprecisely is as costly as the error, because the record is what the next reader acts on. Counts have been removed
  rather than corrected wherever the argument did not need them.

- **2026-08-12 (second pass)** — Recorded four un-audited operator asks in H.5: composite-strategy modelling (which
  gates H.3), collateral-driven archetype selection, rotation volume/ADV filter coverage, and the dispersion basket.
  **Sections H and H.5 were blocked for seven `safe-doc-push` attempts by a single `check_reference_paths --only`
  violation, and the diagnosis was wrong for all seven.** Root cause, measured: line 371 of this file carried a **bare**
  `codex/...` reference (missing the leading slash) — a FORMAT violation, not the hypothesised dangling-at-origin
  existence violation. Two things hid it, and both are now recorded as gate findings in H.6: `run_hygiene_sweep.sh`
  invokes the checker with `--quiet`, which prints the violation **count without the filename**; and `_run_only()`
  **silently `continue`s past any path it cannot stat, then reports 0 violations and exit 0** — so the "same checker
  returns 0 locally" evidence that anchored six wrong guesses was a false negative produced by running it from the wrong
  working directory. The lesson is the one already in the rules: after two identical consecutive failures, stop guessing
  and get the actual identifier — a throwaway worktree at `origin/<branch>` plus the checker run **without** `--quiet`
  named the reference in one shot.
- **2026-08-12** — Investigation outcomes recorded in section H. **Corrected my own earlier over-call**: the "four
  duplicate `TransferStatus`/`TransferResult` declarations" are actually **three legitimate layers plus one deliberate
  mirror** — a bus contract, an on-chain observation schema and an adapter-level result, which merely share a name.
  `canonical/crosscutting/transfer_events.py` is already the self-declared SSOT, so the manual route belongs there
  rather than in anything new. The genuine debts are the `BusTransferType` vs `TransferType` value overlap (acknowledged
  in the file's own docstring) and the hand-synced fund-admin mirror, which exists to respect the no-service-imports
  tier rule and must not simply be deleted. Confirmed the operator's recollection that treasury/client prior art exists:
  `/codex/14-customer-journeys/shared-core/treasury-and-subaccount-model.md` and
  `/codex/14-customer-journeys/shared-core/fund-administration-and-custody.md` are both written and must be read before
  any keying change. Measured the manual gap precisely: the rail enum has three members, all API-executed, so a
  bookmaker deposit is unrepresentable; and `ApprovalBus` provides approval of a system-executed transfer, which is the
  inverse of the manual case. Added manual **trade** capture alongside manual transfers, since betting venues will be
  hand-operated at first and the fills must still book canonically.
- **2026-08-11** — Rewritten as a **claims audit** on operator instruction: no new repository build, full audit of
  everything missing, every fix in line with the existing architecture. Twenty-three load-bearing document claims were
  checked against the tree: **17 verified in source, 1 partial, 2 unverified, 1 false, 2 already-wrong-and-now-fixed.**
  The two wrong ones were in a document already published, and both are corrected — the family count was 8 where the
  enum has **9** members and the list invented "liquidity provision"; and "compliance attestation on every instruction"
  is untrue for the contracted archetypes, since only the MEV modules populate the field. The unverified claims are now
  todos rather than assumptions: capital-budget enforcement, and the backtest launch endpoint (inferred from test
  _filenames_, which is a proxy for an endpoint, not evidence of one). Production gaps carried from reading the tree:
  **stub transfer handlers labelled "for May-23"** — the highest risk, because a stub returning success on a funds path
  reports money moved that did not move — the never-built `CustodyRoute` matrix, **placeholder risk thresholds in the
  client's own strategy config**, and a test-only funding reader. Separately found and fixed: the codex move left **four
  stale duplicate copies** of client documents live on origin, because `safe-doc-push` commits named files from an
  isolated worktree and therefore never saw the deletions.
