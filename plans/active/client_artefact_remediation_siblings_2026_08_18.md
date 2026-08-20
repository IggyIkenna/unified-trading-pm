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
    /plans/audit/results/client_artefact_sibling_docs_audit_2026_08_18.md,
    /plans/audit/results/client_artefact_cross_document_consistency_2026_08_18.md,
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-18
last_updated: "2026-08-20"
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
    /codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html,
    /codex/14-customer-journeys/commercial-model/platform-architecture.html,
    /codex/14-customer-journeys/commercial-model/carveout-engineering.html,
    /codex/14-customer-journeys/commercial-model/ODUM_Elysium_Phase2_Update_2026-07-24.html,
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

- [x] ✅ [DOC] P0. **STOP-SHIP: remove the banned client name from `strategy-service-deep-dive.html`** — 6 hits,
      independently verified by direct grep 2026-08-18. **One hit is inside an SVG `<text>` element**, so a
      prose-only sweep misses it and a visual read of the rendered page will not show it in the body copy. The name
      is used for Copper's collateral-mirroring service, so it is factually correct and still forbidden: this
      rewrite keeps the mechanism (collateral mirrored to a venue without leaving custody) and drops the product
      name. Not a find-and-replace — the surrounding custody explanation needs rewording to stay readable. **Then
      grep all six artefacts, not just this one.** — unified-trading-pm@4067ff23da. All 6 hits reworded to
      describe the mirroring mechanism without naming the product (lede §05, SVG alt text, SVG label, callout
      heading, callout body ×2 in `strategy-service-deep-dive.html`); re-grepped the full `commercial-model/`
      directory afterward — the only other `clearloop` hit in the corpus is the internal (non-client-facing)
      `elysium-carveout-deferral-message-2026-08-11.md`, out of this item's client-artefact scope. Also fixed a
      blocking archive-safety-ratchet gate hit in an unrelated file
      (`cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`, repointed to codex) while shipping this.
- [x] ✅ [DOC] P0. **Remove the performance figures from `platform-architecture.html` and the ODUM Phase2 email** —
      violates the owning plan's "no performance figure anywhere until the overlays land" rule. Verified strings:
      `platform-architecture.html` "consistent positive annualised returns, generally ranging from single digits
      into double digits"; ODUM Phase2 "increasingly confident the strategies generate consistent positive
      annualised…". **Do NOT strip the other `annualised` occurrences** — "net carry (annualised, bps)" is a metric
      label and "stablecoin borrow rate, typically 5–8% annualised" is a market fact, not our performance. Removing
      those would damage correct content. — unified-trading-pm@512d5b07a8 (platform-architecture.html) +
      unified-trading-pm@98ee4fdc70 (ODUM Phase2 email), both slot-6, landed 2026-08-19T04:4XZ before this
      dispatch. Independently verified fresh (2026-08-19, slot 31, post fresh-pull): 0 hits for the banned phrase
      in either file; the 4 legitimate `annualised` occurrences in `platform-architecture.html` (metric label,
      market-fact borrow rate, methodology notes) are untouched.
- [x] ✅ [DOC] P0. **Re-frame `platform-architecture.html`'s staked-basis capability claim** — asserted present-tense,
      found materially false by the sibling audit. Target-state framing, or cut. — unified-trading-pm@512d5b07a8
      (slot-6): cut outright (the whole "runs on Solana against Drift" paragraph removed, not reframed — the plan's
      own wording allowed either). Verified fresh: 0 hits for the present-tense Drift/Solana staked-basis claim.
- [x] ✅ [DOC] P0. **Remove the invented strategy family from `platform-architecture.html` (4 hits) and `carveout-engineering.html` (1 hit)** —
      "Liquidity provision" / "DeFi liquidity provision" / "liquidation
      capture" is not a member of `StrategyFamily`, whose real enum has 9 named members. The
      `strategy-service-walkthrough.html` instance (2 hits) belongs to the Elysium child plan, not here. —
      unified-trading-pm@512d5b07a8 (platform-architecture.html, both call-sites reworded to real family names
      `structural arbitrage`/`portfolio`) + unified-trading-pm@98ee4fdc70 (carveout-engineering.html), both slot-6.
      Verified fresh: 0 hits for either invented term in either file.
- [x] ✅ [DOC] P1. **Reconcile the three-way custody contradiction** across the sibling documents. Per § A of the
      parent plan, the Fireblocks-in-enum / Ceffu-not-in-enum split is **deliberate and documented**
      (`CEFFU_ROUTES_VIA_COPPER_NOTE`; `SigningSurfaceStatus.OUT_OF_SCOPE`), so the fix is a consistent explanatory
      note across the documents — **never an edit to the enum list**, which would make them wrong. —
      unified-trading-pm@512d5b07a8 (slot-6): added a "Why this differs from the SigningSurface code enum" callout
      to `platform-architecture.html`, citing `CEFFU_ROUTES_VIA_COPPER_NOTE` and `SigningSurfaceStatus.OUT_OF_SCOPE`
      without touching the enum itself. Verified present fresh, 2026-08-19.
- [x] ✅ [REVIEW] P1. **Grade these four documents on the same two axes the other children apply** — status
      (live/partial/planned) and the evidence tier defined by the parent plan. They currently carry neither, which
      is part of why violations survived in them. **Verified 2026-08-19 (slot 1, review): 3 of the 4 already carry
      full rule-13 status + evidence-tier grading** — landed same session as items 2-5 above, by the same author,
      just never checkbox-flipped (the identical gap the 2026-08-19 slot-31 Progress Log entry already found and
      fixed for items 2-5). `unified-trading-pm@a7621fb5e5` (`strategy-service-deep-dive.html`, 12 sections),
      `unified-trading-pm@a472bdb5fd` (`platform-architecture.html`, 16 sections),
      `unified-trading-pm@5644680849` (`carveout-engineering.html`, 12 sections) — all three ancestors of
      `origin/live-defi-rollout`, all carry the `.st`/`.ev` CSS + legend lines matching rule 13 verbatim. Spot-checked
      grading quality against 3 specific audit findings rather than trusting the commit message alone: (1)
      `platform-architecture.html` §10 "Running it: isolation, capital, risk" (contains the unconfirmed reserve-ratio
      mechanism, audit P1) is graded `partial` + `~ assumed`, not over-claimed; (2) `strategy-service-deep-dive.html`
      §05/§07 (the transfer-wiring overstatement, audit's top P0 for this file) is graded `planned`/`partial` +
      `? check`/`~ assumed` with an explicit inline caveat ("not yet wired end-to-end in production — see the caveat
      in §05") added to §07's capability list; (3) `platform-architecture.html` §13 "Where the programme stands"
      (the self-reported readiness percentages, audit P2) is graded `partial` + `? check`, not `live`/`verified`. All
      three reflect the audit's findings honestly rather than over-claiming. **`ODUM_Elysium_Phase2_Update_2026-07-24.html`
      is out of scope for the pill mechanism by document type, not an oversight**: it has no `<style>` block and no
      numbered `sec-head` sections — it is a plain-prose personal letter (165 lines), not a walkthrough-style
      artefact rule 13 is built for. Retrofitting `.st`/`.ev` pills would mean inventing a section structure the
      source document never had. Its one disclosure violation (the performance-figure phrase) was already fixed in
      item 2 above; the audit found nothing else wrong in it.

## Progress Log

**2026-08-18 — split out** of [`client_artefact_remediation_2026_08_18.md`](/plans/archive/2026_08/client_artefact_remediation_2026_08_18.md)
per operator direction, to run in parallel with the Elysium and Nick AI children. Deliberately **ungated**
(`depends_on: []`) while its siblings gate on the parent's evidence-tier spec: these are stop-ship disclosure
violations and must not wait on a presentation-layer decision.

**context-scout 2026-08-19**: populated context_scope (6 entries) — added the 4 owned HTML files (the remaining
[REVIEW] grading todo touches all four).

**2026-08-19 (slot 31, infra)** — Dispatched item 2 (performance figures). Fresh-pulled before touching anything and
found items 2-5 already shipped minutes earlier by slot-6 (`unified-trading-pm@512d5b07a8` +
`unified-trading-pm@98ee4fdc70`, both ~04:4XZ today) — none of the four checkboxes had been flipped despite the
code landing. Independently re-verified each claim by direct grep against the live files rather than trusting the
commit messages alone (per rule 4a): performance-figure phrase, Drift/Solana staked-basis claim, and the two
invented-strategy-family terms all read 0 hits across the affected files; the custody-note callout is present.
Flipped all four checkboxes citing the real SHAs and slot-6 attribution — not claiming this session did the
underlying edit. Item 6 ([REVIEW] grading) remains genuinely open; out of scope for this dispatch (different task
type, not what was assigned).

**2026-08-19 (slot 1, review)** — Dispatched item 6 (the grading review). Fresh-pulled first and found the same gap
pattern as the slot-31 entry above: 3 of the 4 files (`strategy-service-deep-dive.html`, `platform-architecture.html`,
`carveout-engineering.html`) already carried full rule-13 status + evidence-tier grading, landed by slot-6 in the
same session as items 2-5 (`a7621fb5e5`, `a472bdb5fd`, `5644680849`, all ~04:5X on 2026-08-19) — checkbox never
flipped despite the code landing. Independently spot-checked grading quality (not just markup presence) against 3
specific audit findings — see the flipped checkbox above for detail — all three correctly reflect the audit rather
than over-claiming. Determined `ODUM_Elysium_Phase2_Update_2026-07-24.html` is out of scope for the pill mechanism
by document type (plain-prose letter, no `sec-head` sections to attach pills to), not a remaining gap. **Every todo
in this plan is now `[x]`** — this plan should be archived; per this plan's own structure, that is
[`client_artefact_remediation_siblings_finalize_2026_08_18.md`](/plans/active/client_artefact_remediation_siblings_finalize_2026_08_18.md)'s
own P2 todo (gated on this plan, now unblocked) — not done in this session, which was scoped to item 6 only.
