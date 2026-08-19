---
doc_type: plan
title: Client artefact remediation — Elysium strategy-service walkthrough
summary: >-
  All remediation touching strategy-service-walkthrough.html only — accuracy fixes, disclosure and completeness
  additions, the live re-grade, and the evidence-tier tagging for this one file. Split out of
  client_artefact_remediation_2026_08_18.md so it runs in parallel with the Nick AI and sibling children; the file
  scope is what makes that safe, since no other child edits this HTML.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [client-disclosure, elysium, artifact-remediation, audit-followup]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/client_artefact_remediation_2026_08_18.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/audit/results/client_artefact_live_regrade_2026_08_18.md,
    /plans/audit/results/client_artefact_axis0_content_verification_2026_08_18.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
  ]
created: 2026-08-18
last_updated: "2026-08-18"
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: infra
effort: high
drift_direction: none
depends_on: [client_artefact_remediation_2026_08_18]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: >-
  Operator direction 2026-08-18 to split client_artefact_remediation_2026_08_18.md by artefact for parallelism.
  Todos MOVED here from the parent's § A and § B plus the Elysium-scoped items of § E and § F — moved, not copied,
  so no todo is tracked in two places.
context_scope:
  [
    /plans/active/client_artefact_remediation_2026_08_18.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /codex/14-customer-journeys/commercial-model/strategy-service-walkthrough.html,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
  ]
---

# Client artefact remediation — Elysium strategy-service walkthrough

**File owned by this plan**: `codex/14-customer-journeys/commercial-model/strategy-service-walkthrough.html` — and
nothing else. No other remediation child edits it. Gated on the parent only for the evidence-tier spec.

Full evidence for every finding is in the audit reports listed in `related:`. Do not restate their reasoning here.

## Accuracy fixes

- [x] [DOC] P0. ✅ **Fix the instruction-type count in §01/§03** — says "9 Instruction types" / "The nine action
      types" and enumerates 9; the real `StrategyInstructionV2` union has **11**, missing `TransferInstructionV2`
      and `BridgeInstructionV2`. `/codex/04-architecture/strategy-execution-protocol.md` has correctly said 11 all
      along, so the codex was right and only this document drifted. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P0. ✅ **Fix §02's strategy-family list** — shows 5 families including an invented "Liquidity provision".
      The real `StrategyFamily` enum has 9 members: `ML_DIRECTIONAL, RULES_DIRECTIONAL, CARRY_AND_YIELD,
      ARBITRAGE_STRUCTURAL, MARKET_MAKING, EVENT_DRIVEN, VOL_TRADING, STAT_ARB_PAIRS, PORTFOLIO`. "Carry" and
      "Dispersion" are not separate families — they fold into `CARRY_AND_YIELD` and `VOL_TRADING`. This exact
      correction was already applied to `strategy-service-deep-dive.html` and never reached here. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P0. ✅ **Soften §11 "Automated movement"** — presented as functioning capability under a `partial` badge.
      Measured: `_ensure_default_handlers()` registers only `SUBACCOUNT_MOVE`; `CEX_WITHDRAW` is commented
      "NOT WIRED"; gas top-up/floor has no handler and no reserve-threshold logic anywhere; `REBALANCE` is
      enum-only; and `TransferCoordinator` is never instantiated in production code. The measured reality is closer
      to no production entry point at all than to a working subset. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P0. ✅ **Re-grade every `live` badge in this file to `partial`** — all 10 of them. The re-grade audit
      searched the whole workspace for positive real-capital evidence (a real fill, a mainnet transaction, a
      reconciled live P&L, a funded live client) and found none, so no section survives the conjunctive test. This
      is the definition working as designed, not a writing defect. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P1. ✅ **Add the custody explanatory note, do NOT edit the `SigningSurface` list** — the audit's original
      finding here was a FALSE POSITIVE. Ceffu is a stub ("STUB pending API spec" in the factory), its absence from
      the enum is deliberate (`CEFFU_ROUTES_VIA_COPPER_NOTE` — its signing routes via Copper), and Fireblocks is
      `SigningSurfaceStatus.OUT_OF_SCOPE`. Editing the list would make the document wrong; explain the design. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P1. ✅ **Fix the stale §05→§08 cross-reference** — the determinism proof is in §09. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P1. ✅ **Fix the CeFi spot-pair instrument-ID example** — uses instrument-type token `SPOT`; the real one
      is `SPOT_PAIR`. The other ID examples verified correct against `build_canonical_instrument_id()`, and all
      named venues are correctly bound in `VENUE_TO_ADAPTER_KEY` — one wrong token, not a systemic problem. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P0. ✅ **Remove the invented family's 2 hits in this file** (see § accuracy above) — the
      `platform-architecture.html` and `carveout-engineering.html` instances belong to the siblings child. **Shipped `unified-trading-pm@171dc40739`.**
- [ ] [DOC] P2. **Soften §12's capital-budget "enforced by construction" claim** — the wallet-funding framing is
      narrower and more defensible than the owning plan's still-`UNVERIFIED` enforcement line.
- [ ] [DOC] P2. **Caveat the hard `paper == batch-rerun` equality near §08/§09** — the now-default-ON dynamic
      universe lacks the manifest pinning that equality depends on (owning plan § H.8, open P0).
- [ ] [REVIEW] P1. **Resolve the two re-verification findings that did not confirm** — 4 of 6 came back CONFIRMED;
      the remaining 2 need a verdict before this document ships.
- [ ] [REVIEW] P1. **Verify §11's "Manual movement" claim, which likely overstates reachability the same way the
      automated path did.** It states manual transfers "use the same instruction types and the same rails as
      automated ones" — but `TransferCoordinator` is never instantiated in production and only `SUBACCOUNT_MOVE` has
      a registered handler, so "the same rails" may describe a path that does not exist either. Raised 2026-08-18 by
      the agent that reframed the automated half; it deliberately did **not** fix this, because it had not traced
      the manual route's actual code path and would have been asserting rather than verifying. Trace the real route
      first, then correct or confirm.

## Disclosure and completeness

- [x] [DOC] P1. ✅ **Add a scope statement near the top** stating this describes the full production repository and
      naming its intended audience — distinct from the future carve-out package. Without it a future editor could
      wrongly narrow this document to the carve-out's tighter scope. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P1. ✅ **Add a carve/hosted split note to §09** distinguishing strategy-owned position/fee/PnL
      reconciliation from custodian-spanning balance/transfer reconciliation, which sits closer to withheld IP. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P2. ✅ **Name the "strategy reads only processed data, never MTDS directly" invariant explicitly** —
      grep-confirmed absent. This document is its natural home. **Shipped `unified-trading-pm@171dc40739`.**
- [ ] [DOC] P2. **Add mirrored-custody routing content (§11)** — the two-custodian mirroring model, without the
      banned product name (see the siblings child for why that name never appears).
- [ ] [DOC] P2. **Add funding-route / per-client custody binding content (§11)**.
- [ ] [DOC] P2. **Add a capability-wizard boundary note (§04)** — one sentence distinguishing it from §04's
      per-archetype param-schema wizard.
- [ ] [DOC] P2. **Add rank-allocator weighting-layer content** — state it as a registered, extensible set rather
      than a fixed count, so the number cannot rot.
- [ ] [DOC] P2. **Add book-level overlay content (§12)** — vol-target, beta-hedge, no-trade band, rank-buffer.
- [ ] [DOC] P2. **Add fee/gas-as-decision-input content (§03/§08)** — currently they appear only as a
      reconciled/monitored quantity, never as an input to the decision.
- [ ] [DOC] P3. **Extend §03's `AtomicInstruction` block with a one-line worked example**, connecting it to §12's
      emergency-flatten reasoning.

## Evidence tiers and readiness

- [x] [DOC] P0. ✅ **Apply the parent's evidence-tier spec to every claim-bearing section in this file** — default
      `needs-check`; `machine-verified` requires naming the verifying command, skill or code symbol inline. **Shipped `unified-trading-pm@171dc40739`.**
- [ ] [DOC] P1. **Give every claim-bearing section its owner mark** (workstream / plan / epic that closes it), per
      `system_readiness_master.md` W21's closure invariant.
- [ ] [DOC] P1. **Audit the archetype-readiness (batch/paper/live) content** — never probed.
      `ARCHETYPE_FEATURE_GROUPS` declares ~40 of 60 and its docstring refuses to guess the rest, so any claim
      implying full coverage is wrong.

## Progress Log

**2026-08-18 — split out** of [`client_artefact_remediation_2026_08_18.md`](/plans/active/client_artefact_remediation_2026_08_18.md)
per operator direction. Todos moved, not copied.

**context-scout 2026-08-19**: populated context_scope (4 entries) — added the owned HTML file and the
elysium-delivery plan the two open § P2 todos (§12 capital-budget, §08/§09 equality caveat) cite.
