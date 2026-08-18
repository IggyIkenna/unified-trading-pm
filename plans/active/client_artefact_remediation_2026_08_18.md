---
doc_type: plan
title: Client artefact remediation — fix accuracy, completeness and drift found by the 2026-08-18 audit
summary: >-
  Fixes every accuracy, completeness and target-state-fidelity finding from the 2026-08-18 audit of
  platform-external-api-walkthrough.html (Nick AI) and strategy-service-walkthrough.html (Elysium) — content-only
  edits to the two artefacts, citing real evidence for every change. Does NOT build new system functionality; where
  a finding traces to a genuine system gap rather than a documentation gap, this plan cites the existing tracked
  item instead of duplicating it (§ "Real system gaps — already tracked, not duplicated here").
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [client-disclosure, nick-ai, elysium, artifact-remediation, audit-followup]
related:
  [
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-18
last_updated: "2026-08-18"
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
assigned_role: infra
effort: high
drift_direction: none
depends_on: []
sequential: true
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: >-
  Operator direction 2026-08-18: audit both client artefacts with sub-agents, verify with an independent pass, then
  document and push a triage-ready dispatch plan so the agent-orchestrator fleet can pick up the remediation.
context_scope:
  [
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md,
    /plans/epics/system_readiness_master.md,
  ]
---

# Client artefact remediation — 2026-08-18 audit follow-up

**Read the audit first**:
[`/plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md`](/plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md)
— every todo below cites a specific finding from it. `sequential: true` because every todo edits one of only two
files (`strategy-service-walkthrough.html`, `platform-external-api-walkthrough.html`) — concurrent dispatch would
race edits on the same file, which the workspace's own concurrency rule forbids (independent todos must touch
different files).

**Disclosure boundary reminder for every todo below** — do not drift past this while fixing content:
- Both artefacts: no commercial figures, never name ClearLoop.
- Nick AI (`platform-external-api-walkthrough.html`): archetypes yes/edge no; code snippets limited to config
  schemas and API contracts; ML/features out of scope.
- Elysium (`strategy-service-walkthrough.html`): the config loop stays withheld; no performance figures.
- **No todo here authorises sending either document anywhere.** Both owning plans already carry their own final
  "operator review before send" gate — [`nick_ai_platform_disclosure_artifact_2026_08_16.md`](/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md)'s
  "Operator review before send" P0 todo and the equivalent disclosure-review items in
  [`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`](/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md)
  § E — this plan does not re-create that gate.

## A. Elysium walkthrough — accuracy fixes (P0)

- [ ] [DOC] P0. **Fix the instruction-type count in `strategy-service-walkthrough.html` §01/§03**: currently says
      "9 Instruction types" / "the nine action types" and lists 9. `unified-api-contracts/unified_api_contracts/
      internal/architecture_v2/schemas.py` declares 11 `StrategyInstructionEnvelope` subclasses (verified directly
      2026-08-18) — add `TransferInstructionV2` (line 327) and `BridgeInstructionV2` (line 336) to §03's table with
      their real fields, and update the stat-row to 11. Audit finding: § Section 2, Axis 2, finding 1.
- [ ] [DOC] P0. **Fix §02's strategy-family list** — currently shows 5 families including an invented "Liquidity
      provision" entry. `StrategyFamily(StrEnum)` in `unified-api-contracts/.../architecture_v2/enums.py` has 9 real
      members: `ML_DIRECTIONAL, RULES_DIRECTIONAL, CARRY_AND_YIELD, ARBITRAGE_STRUCTURAL, MARKET_MAKING,
      EVENT_DRIVEN, VOL_TRADING, STAT_ARB_PAIRS, PORTFOLIO`. Replace the invented list with the real 9, matching the
      correction already applied to the sibling `strategy-service-deep-dive.html` per
      `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` § F (never applied to this document).
      Audit finding: § Section 2, Axis 2, finding 2.
- [ ] [DOC] P0. **Soften §11 "Automated movement"** — re-verified 2026-08-18 against
      `execution-service/execution_service/transfer_coordinator.py`: only `SUBACCOUNT_MOVE` auto-registers a
      handler; `CEX_WITHDRAW` is commented "NOT WIRED"; gas top-up/floor has no implementation anywhere;
      `REBALANCE` is enum-only; `TransferCoordinator` is never instantiated in production code. Rewrite the section
      to state which rails have zero production wiring today rather than presenting dust-sweep/gas-top-up/rebalance
      as working "partial" capability. **Do not overstate readiness while the underlying system gap is still open**
      — see § "Real system gaps" below; this is a content-accuracy fix, not a claim that the gap is closed.
- [ ] [DOC] P1. **REVISED 2026-08-18 — the original custody finding was a FALSE POSITIVE; do not "fix" the block.**
      The audit claimed `SigningSurface` wrongly names `FIREBLOCKS_MPC` and wrongly omits `ceffu`, "which IS a
      working branch." Re-verification falsified both halves: (a) `ceffu` is **not** working —
      `execution-service/execution_service/custody/factory.py` logs it as "CeffuCustodyProvider (Binance
      institutional MPC — **STUB pending API spec**)"; (b) CEFFU's absence from the enum is a **deliberate,
      documented decision** — `unified-api-contracts/unified_api_contracts/internal/architecture_v2/
      custody_surfaces.py` carries a named constant `CEFFU_ROUTES_VIA_COPPER_NOTE` stating CEFFU's signing routes
      *via Copper*, so seeding a CEFFU surface would mean "inventing an enum member"; (c) `FIREBLOCKS_MPC` is
      covered by `SigningSurfaceStatus.OUT_OF_SCOPE` ("enum member retained for future flexibility but NOT a
      May-23 / June-1 target"). The artefact's quote is accurate **and** the architecture is coherent. **Correct
      action**: add one sentence explaining the CEFFU-routes-via-Copper design and the `OUT_OF_SCOPE` status, so a
      reader doesn't reach the same wrong conclusion the audit did. Editing the enum list would make the document
      wrong.
- [ ] [DOC] P1. **Fix the stale §05→§08 cross-reference** — "the determinism proof in §08" should point to §09,
      where the actual `live − batch = (paper − batch) + (live − paper)` decomposition lives.
- [ ] [DOC] P2. **Soften §12's capital-budget "enforced by construction" claim** — the wallet-funding framing is
      narrower and more defensible than "capital_budget_amount is enforced" (still `UNVERIFIED` per
      `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` § B), but currently reads as a settled
      guarantee. Qualify or narrow the claim to exactly what's true (funding isolation), not enforcement of the
      budget field itself.
- [ ] [DOC] P2. **Add a caveat near §08/§09's hard equality claim** — `paper == batch-rerun` is asserted
      unconditionally, but per `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` § H.8 (open
      P0), the now-default-ON dynamic universe currently lacks the manifest-pinning needed to guarantee this exactly
      when the universe resolution date differs between runs. State the guarantee's real current scope rather than
      an unconditional claim.

## B. Elysium walkthrough — disclosure and completeness (P1/P2)

- [ ] [DOC] P1. **Add a scope statement near the top of `strategy-service-walkthrough.html`** stating this describes
      the full production repository (the voluntary full-repo-send artefact per
      `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` § E), distinct from the future,
      narrower carve-out package (`elysium_carveout_stubbed_strategy_service_2026_08_12.md`). Resolves the audit's
      disclosure-boundary finding 1 — currently "Elysium" is never named anywhere in the document and there is no
      hosted-vs-carved framing at all.
- [ ] [DOC] P1. **Add a one-line carve/hosted split note to §09** distinguishing strategy-owned position/fee/PnL
      reconciliation (the disclosed side) from custodian-spanning balance/transfer reconciliation (the withheld
      `ReconciliationService`/`TreasuryService` IP per the carve-out plan) — relevant primarily once this content is
      reused for the future carve-out artefact.
- [ ] [DOC] P2. **Add mirrored-custody routing content** (§11) — Copper/Ceffu two-custodian mirroring, without
      naming ClearLoop or describing reconciliation mechanics: *"Custody is not single-provider. A wallet's signing
      surface can sit with more than one custodian at once, and balances mirrored onto a venue through one custodian
      are tracked distinctly from balances held directly — the routing between them is a capability of the custody
      layer, resolved beneath the strategy contract rather than by it."*
- [ ] [DOC] P2. **Add funding-route / per-client custody binding content** (§11) — a short paragraph stating that
      funding a strategy instance resolves against what that client has granted access to (venues, custodians,
      borrow/lend counterparties) rather than a single fixed path, without describing the route-resolution
      algorithm.
- [ ] [DOC] P2. **Add a capability-wizard boundary note** (§04) — one sentence: a separate capability layer,
      upstream of strategy-service's own config-schema wizard, resolves which archetypes/parameters a client may
      configure at all; what §04 validates is form, not eligibility.
- [ ] [DOC] P2. **Add rank-allocator weighting-layer content** — a new short passage stating that within a feasible
      universe, instances are weighted (not run at equal size) by a rank-allocation layer scoring candidates on an
      axis (coin/venue/protocol/expiry) — without naming the 17-engine registry count or specific engines.
- [ ] [DOC] P2. **Add book-level overlay content** (§12) — vol-target, beta-hedge, no-trade band and rank-buffer as
      a pre-decision sizing/veto layer, distinct from per-position limits already shown.
- [ ] [DOC] P2. **Name the "strategy reads only processed data, never MTDS directly" invariant explicitly** — not
      stated anywhere in this artefact (grep-confirmed 0 hits for MDPS/features-service/MTDS/Pub-Sub). Add one
      sentence near §01's data-flow description.
- [ ] [DOC] P2. **Add fee/gas-as-decision-input content** (§03/§08) — currently fees/gas appear only as a
      post-hoc reconciled quantity; state that expected fees (clearing, exchange, gas where relevant) are folded
      into the economics a slot is ranked and sized on.
- [ ] [DOC] P3. **Extend §03's `AtomicInstruction` block with a one-line worked example** (e.g. a recursive-staked
      entry: borrow → swap → stake) to connect the schema to the real chained-sequence reasoning already shown
      elsewhere in §12's emergency-flatten example.

## C. Nick AI walkthrough — accuracy fixes (P0/P1)

- [ ] [DOC] P0. **Rewrite §2/§3's external-API status framing** — both currently badged `live` without qualification.
      Re-verified 2026-08-18: `instruments-service` (`GET /v1/instruments`, `GET /v1/instruments/bulk`) and
      `market-tick-data-service` (`GET /external/market-data/availability`, `.../delivery/batch`,
      `.../delivery/stream`) have real, auth-protected, live-verified external surfaces
      (`instruments-service@2fcf7a19`, `market-tick-data-service@6fefa63676`). `execution-service`
      (`POST /external/instructions`, `execution-service@3567e7a180`) is live **for TRADE instructions only** — the
      other 10 of 11 `StrategyInstructionV2` types return an honest HTTP 501, not the same contract the artefact
      currently implies. `strategy-service` still has no true counterparty-facing surface (admin-token-gated
      internal tooling only) — keep that specific claim as `planned`. Name the concrete live endpoints and the
      TRADE-only caveat rather than a blanket "you get the contract our own execution service gets."
- [ ] [DOC] P1. **Fix §4's four-state coverage table** — the "Expected, absent" row (`empty_confirmed`) is marked
      "counts against coverage: Yes," but the "How to read 48.54%" callout two paragraphs later defines the
      denominator as `captured + attempted-failed + expected-unattempted` only, with no mention of `empty_confirmed`
      — an internal contradiction verified directly against the HTML (lines 508-512 vs 536-542). Either add the
      missing state's correct denominator treatment to the table, or reconcile the "Yes" verdict against the stated
      formula so the two agree.
- [ ] [DOC] P1. **Reconcile the 288-venue figure** — currently stated alone with no cross-reference to the three
      legitimately-different venue-count units the owning plan's own pre-audit explicitly instructed be stated
      together (151 canonical / 183 physical / "158-84" stale). Either state all units side by side, or explicitly
      scope "288" as the 2026-08-18 readiness-manifest grain, not directly comparable to the registry-declared
      counts.
- [ ] [DOC] P2. **Fix §14's "19-step contract" mislabel** — the quoted 864-row / 0-844-20 rollup was produced by the
      readiness-state-dump skill's 8-leg model (declared/IS/MTDS/MDPS/features/ml/strategy/execution), not the
      19-step Venue Readiness Contract used elsewhere in the pre-audit. Name the correct framework, or state both
      and which produced these specific numbers.
- [ ] [DOC] P2. **Qualify §16's "a great deal of testnet work is already complete"** with the real per-AG gaps: no
      per-venue cefi testnet declaration found anywhere; sports' live credential-probe surface is entirely stubbed;
      tradfi's only live credential-health probe covers Tardis only; Polymarket has no testnet and no written
      paper-trading ruling. Keep the real progress that does exist (AAVE Sepolia, Solana LST devnet, Kalshi demo
      host) but don't state it as a blanket "already complete."
- [ ] [DOC] P3. **Scope §5's "every figure is pending measurement" lede** to the coverage-percentage cells only —
      the readiness splits shown in the same tree summaries (e.g. "DeFi — 0 ready / 133 not-ready / 47 unverified")
      are already real, measured 2026-08-18 figures, not pending.

## D. Nick AI walkthrough — missing capability (P1/P2)

- [ ] [DOC] P1. **Add the 7 fully-absent capability sections**: fee/gas breakdown (clearing/broker/exchange/gas/
      other, consumed by strategy for decisions and execution for alpha PnL); collateral usability and cross-margin
      logic per venue; manual trade capability on every venue as the disaster path; a reconciliation framework
      section (thresholds/tolerances/intervals/degraded-behaviour/manual-trade-seen-vs-not-seen); PnL attribution
      across every risk/exposure dimension; risk in native-token AND share-class-normalised terms plus the Greeks
      and DART's dimensions; latency/tracing (time-received/time-sent), preflight input registration, and per-input
      staleness SLAs. **Write these as what the system is targeting, not as already-live** — every one of these maps
      to an open, unchecked P0 item in `system_readiness_master.md` (W5/W10/W12/W13/W16/W17) with zero items checked
      off; see § "Real system gaps" below. Draft copy for all 7 is in the audit's sub-agent transcript
      (§ Nick-AI-missing-capability agent) and should be pulled directly, calibrated for accurate present-tense vs.
      target-state framing before insertion.
- [ ] [DOC] P2. **Add the 4 present-thin capability sections**: transfer rails/custody eligibility per venue
      (Copper/Ceffu/manual/automated-prime-broker-per-broker/IBKR/Alpaca, not just qualitative rail-type language);
      the batch=live determinism mechanism by name (UTL `EventTransport` facade, `InMemoryTransport` for
      paper/colocated vs Pub/Sub for live); order lifecycle vocabulary (creates/updates/cancels/amends, plus
      execution-service state recovery on restart); TWAP named explicitly alongside straight-market in the
      execution-depths section.
- [ ] [DOC] P2. **Name MDPS/features-service explicitly as the intermediary** in §1's architecture diagram/table
      between MTDS and Strategy — resolves the "strategy reads only processed data, never MTDS directly" drift-risk
      for this artefact too (currently MTDS/MDPS/features are collapsed into one undifferentiated "Market data" box
      with a direct arrow to Strategy).

## E. Evidence-provenance tiers + audit-gap closure (added 2026-08-18, operator ruling)

**Operator ruling 2026-08-18**: the artefacts carry a SECOND axis, orthogonal to the existing
`live`/`partial`/`planned` status. Status says what the system **does**; the evidence tier says **how we know**, so
the operator can scroll the document before sending and see exactly which claims are settled and which need a
check. Three tiers, rendered as a distinct visual mark (not reusing the status pill):

| Tier                | Meaning                                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| **machine-verified** | Checked against code or measured data; names the command/skill/symbol so it is re-auditable on demand |
| **needs-check**      | Stated in good faith, not yet validated — operator or agent must confirm before the document is sent  |
| **assumption**       | Our best current understanding, explicitly not verified                                              |

Same ruling: **do NOT withhold full system functionality from the artefacts.** The operator uses the top-down view
to spot duplication, misplaced logic and wrong-home concerns. Missing capability is written in and marked, never
omitted.

- [ ] [DOC] P0. **Introduce the evidence-tier axis in both artefacts** — legend entry alongside the existing
      status legend, a distinct mark, and a one-line explanation of what the operator should do with each tier.
      Must not visually collide with `live`/`partial`/`planned`.
- [ ] [DOC] P0. **Tag every claim-bearing section in both artefacts with an evidence tier.** Default to
      `needs-check` — `machine-verified` requires naming the verifying command, skill or code symbol inline, and
      that citation is what makes the re-audit prompt cheap to run later.
- [ ] [DOC] P0. **Re-grade all `live` badges against the stricter definition** — "reachable on a production path
      AND validated with real capital" landed in both artefacts at `unified-trading-pm@832033d094`, but the marks
      were never re-graded and the 2026-08-18 audit never checked them (grep-confirmed: zero occurrences of "real
      capital" in the audit report). **Measured: 17 sections still marked `live`** — 7 in
      `platform-external-api-walkthrough.html`, 10 in `strategy-service-walkthrough.html`, of 39 graded sections
      across both. A `live` mark now needs POSITIVE capital-validation evidence; the master epic's own scope is
      "everything except going live with capital," so expect most to move to `partial`.
- [ ] [DOC] P0. **Audit the inherited glossary / canonical-instrument-ID material (Axis 0).** Both artefacts carry
      venue-glossary and canonical-ID content sourced from a sub-agent report and never verified; the 2026-08-18
      audit ran zero probes on it. Check every ID example against `build_canonical_instrument_id()` and every venue
      name against `VENUE_TO_ADAPTER_KEY` / `VENUE_CHAIN_MAP`. **Also check the framing, not just the syntax**: the
      point of a single dispatch function is that ONE envelope spans asset groups — content presenting per-asset-
      group ID *rules* inverts the asset-group-agnostic principle and teaches future readers the wrong model.
- [ ] [DOC] P1. **Audit the archetype-readiness (batch/paper/live) content**, added at operator request and never
      probed. `ARCHETYPE_FEATURE_GROUPS` declares ~40 of 60 and its docstring deliberately refuses to guess the
      rest — any artefact claim implying full coverage is wrong.
- [ ] [DOC] P1. **Ground or cut the forward claim** — `platform-external-api-walkthrough.html` states work "on the
      current plan complete over the remainder of this year" with no cited basis in any plan (verified present
      2026-08-18; the audit never flagged it). A counterparty can hold us to it. Find a citation or remove it.
- [ ] [RESEARCH] P1. **Research real per-venue transfer rails / custody eligibility / collateral / cross-margin,
      then write the best current answer into the artefact marked `assumption` or `needs-check`.** Measured
      2026-08-18: **no UAC registry field answers these** — `VenueCapabilityRecord` is market-data only (`route` +
      `data_types`); `VenueCapability` covers actions (`spot_trade`…`stake`); a registry-wide grep for
      `cross_margin|collateral_eligib|transfer_rail|withdraw_enabled|margin_asset` returns empty. Per operator
      ruling, this content goes IN (marked), it is not withheld — but the research output must also spawn a
      registry-extension todo under `system_readiness_master.md` W5 so the artefact ends up downstream of a machine
      SSOT rather than becoming the de-facto SSOT itself.
- [ ] [SCRIPT] P1. **Add a QG check validating artefact-quoted enum data against the UAC enums** (operator ruling
      2026-08-18). Root cause of two of this audit's three P0s: enum contents are hand-transcribed into six client
      HTMLs, so the same concern lives in seven places. Proof it recurs — the strategy-family correction was
      applied to `strategy-service-deep-dive.html` and never reached `strategy-service-walkthrough.html`, and
      `/codex/04-architecture/strategy-execution-protocol.md` has correctly said "11 polymorphic actions" all
      along while the artefact said 9. Check must cover all six artefacts in
      `codex/14-customer-journeys/commercial-model/`, be ratchet-baselined like the other checkers, and name which
      enum each artefact claim derives from.
- [ ] [REVIEW] P1. **Re-verify the six audit findings the audit itself did NOT independently check.** The report
      names them explicitly (targets-not-deltas, atomic multi-leg, cross-client-transfer-impossible, attestation,
      archetype counts 60/32, capital budget). This is now a demonstrated failure mode, not a hypothetical — the
      custody P1 in § A dissolved on first re-verification. Treat each as unconfirmed until checked against code.
- [ ] [REVIEW] P2. **Audit the four sibling client artefacts never covered** —
      `platform-architecture.html` (252 KB, the largest client doc in the repo), `carveout-engineering.html`
      (87 KB), `strategy-service-deep-dive.html` (66 KB),
      `ODUM_Elysium_Phase2_Update_2026-07-24.html` (14 KB). Disclosure boundary FIRST and reported separately.
      The audit covered 2 of 6 client-facing HTMLs.
- [ ] [REVIEW] P2. **Cross-document consistency sweep across all six artefacts.** No agent has compared documents
      to each other — the 4 sub-agents split two-per-artefact by axis, so sibling drift was invisible by
      construction and the one instance found was luck. Sweep for contradictory counts, enum members, status marks,
      venue numbers and mode vocabulary; separately verify every internal anchor resolves (one stale §05→§08 was
      found by reading — do it mechanically).

## Real system gaps — already tracked, not duplicated here

These findings trace to genuine gaps in the system itself, not documentation gaps. **Do not re-author them as todos
in this plan** — each already has an open, tracked item; this plan's job is to make sure the artefact team knows
they gate certain content from moving out of "thin"/"absent," not to re-derive the fix:

- **Transfer handler production wiring** (blocks A's §11 rewrite from ever becoming a "live" claim) —
  `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` § C, P0, open.
- **Capital-budget enforcement** — same plan § B, P0, open.
- **Dynamic-universe as-of-date pinning** (the paper==batch-rerun equality risk) — same plan § H.8, P0, open.
- **Fee/gas breakdown, collateral/cross-margin, manual-trade-on-every-venue, reconciliation framework, PnL
  attribution, risk-in-native+share-class-terms/Greeks, latency/tracing/preflight/SLA** —
  `system_readiness_master.md` W5, W10, W12, W13, W16, W17 — all P0, all open, zero items checked off across all
  six workstreams as of this audit.
- **Canonical output paths for everything strategy-service emits** — same epic, W18, P0, open.

Mirrored-custody routing, the funding-route graph, the rank-allocator weighting layer and the book-level overlays
(§ B above) are **not** in this list — the audit confirmed these already exist in the running system
(`CUSTODY_TRANSFER` rail, `ALLOCATOR_ARCHETYPE_REGISTRY`'s 17 engines, the carved `risk-guards-local` overlays per
`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` § H.5) — their absence from the artefact is
purely a documentation gap, which is why they're todos in § B rather than cross-references here.

## Progress Log

**2026-08-18 — authored**, immediately following
[`/plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md`](/plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md),
per operator direction to produce a triage-ready dispatch plan for the agent-orchestrator fleet. `sequential: true`
because every todo touches one of only two files. Deliberately excludes any todo that would build new system
functionality — those gaps are cross-referenced to their existing tracked items (§ "Real system gaps") rather than
duplicated, per the workspace's plan-authoring HARD RULE that a plan references other plans/epics rather than
re-deriving their content.
