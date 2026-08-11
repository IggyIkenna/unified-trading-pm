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
      Values plan-of-record: `drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.md`.
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

## Progress Log

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
