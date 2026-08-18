---
doc_type: plan
title: Client artefact remediation — the four sibling documents (STOP-SHIP disclosure violations)
summary: >-
  Fixes the hard disclosure-boundary violations the 2026-08-18 second-pass audit found in the four client artefacts
  the first-pass audit never opened — a banned client name appearing six times, performance figures in two
  documents, a materially false present-tense capability claim, and the invented strategy family. Split out of
  client_artefact_remediation_2026_08_18.md so it runs in parallel — it touches four HTML files that no sibling
  plan touches, and it is UNGATED because these are stop-ship violations.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [client-disclosure, artifact-remediation, audit-followup, stop-ship, disclosure-boundary]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/client_artefact_remediation_2026_08_18.md,
    /plans/audit/results/client_artefact_sibling_docs_audit_2026_08_18.md,
    /plans/audit/results/client_artefact_cross_document_consistency_2026_08_18.md,
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-18
last_updated: "2026-08-18"
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
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
  Operator direction 2026-08-18 to split client_artefact_remediation_2026_08_18.md by artefact for parallelism.
  This child is UNGATED and P0 — the second-pass audit found hard disclosure violations here, in documents no
  remediation plan covered at the time they became client-sendable.
context_scope:
  [
    /plans/audit/results/client_artefact_sibling_docs_audit_2026_08_18.md,
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
  ]
---

# Client artefact remediation — the four sibling documents

**Files owned by this plan** (no other remediation child touches them):
`codex/14-customer-journeys/commercial-model/{strategy-service-deep-dive, platform-architecture,
carveout-engineering, ODUM_Elysium_Phase2_Update_2026-07-24}.html`

**Do not send any of these documents to a client while a P0 below is open.** Evidence for every finding is in
[the sibling-docs audit](/plans/audit/results/client_artefact_sibling_docs_audit_2026_08_18.md); the disclosure
rules themselves are owned by
[show-dont-show-discipline](/codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md) — read the
codex rule, not a plan's restatement of it.

- [ ] [DOC] P0. **STOP-SHIP: remove the banned client name from `strategy-service-deep-dive.html`** — 6 hits,
      independently verified by direct grep 2026-08-18. **One hit is inside an SVG `<text>` element**, so a
      prose-only sweep misses it and a visual read of the rendered page will not show it in the body copy. The name
      is used for Copper's collateral-mirroring service, so it is factually correct and still forbidden: this
      rewrite keeps the mechanism (collateral mirrored to a venue without leaving custody) and drops the product
      name. Not a find-and-replace — the surrounding custody explanation needs rewording to stay readable. **Then
      grep all six artefacts, not just this one.**
- [ ] [DOC] P0. **Remove the performance figures from `platform-architecture.html` and the ODUM Phase2 email** —
      violates the owning plan's "no performance figure anywhere until the overlays land" rule. Verified strings:
      `platform-architecture.html` "consistent positive annualised returns, generally ranging from single digits
      into double digits"; ODUM Phase2 "increasingly confident the strategies generate consistent positive
      annualised…". **Do NOT strip the other `annualised` occurrences** — "net carry (annualised, bps)" is a metric
      label and "stablecoin borrow rate, typically 5–8% annualised" is a market fact, not our performance. Removing
      those would damage correct content.
- [ ] [DOC] P0. **Re-frame `platform-architecture.html`'s staked-basis capability claim** — asserted present-tense,
      found materially false by the sibling audit. Target-state framing, or cut.
- [ ] [DOC] P0. **Remove the invented strategy family from `platform-architecture.html` (4 hits) and
      `carveout-engineering.html` (1 hit)** — "Liquidity provision" / "DeFi liquidity provision" / "liquidation
      capture" is not a member of `StrategyFamily`, whose real enum has 9 named members. The
      `strategy-service-walkthrough.html` instance (2 hits) belongs to the Elysium child plan, not here.
- [ ] [DOC] P1. **Reconcile the three-way custody contradiction** across the sibling documents. Per § A of the
      parent plan, the Fireblocks-in-enum / Ceffu-not-in-enum split is **deliberate and documented**
      (`CEFFU_ROUTES_VIA_COPPER_NOTE`; `SigningSurfaceStatus.OUT_OF_SCOPE`), so the fix is a consistent explanatory
      note across the documents — **never an edit to the enum list**, which would make them wrong.
- [ ] [REVIEW] P1. **Grade these four documents on the same two axes the other children apply** — status
      (live/partial/planned) and the evidence tier defined by the parent plan. They currently carry neither, which
      is part of why violations survived in them.

## Progress Log

**2026-08-18 — split out** of [`client_artefact_remediation_2026_08_18.md`](/plans/active/client_artefact_remediation_2026_08_18.md)
per operator direction, to run in parallel with the Elysium and Nick AI children. Deliberately **ungated**
(`depends_on: []`) while its siblings gate on the parent's evidence-tier spec: these are stop-ship disclosure
violations and must not wait on a presentation-layer decision.
