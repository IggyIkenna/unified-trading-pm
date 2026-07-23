---
doc_type: codex-ssot
title: Investment Management — Warm-Prospect Demo
summary:
  pb3b warm-prospect IM demo on staging — walks 4 allocator surfaces (catalogue filtered to offered slots, positions+P&L
  attribution, NAV+fee accrual+investor statements, reconciliation+audit) with entitlement-scoped data; overlays the
  shared client-reporting-demo-walkthrough click-path.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [sales, prospect]
tags: [investment-management, demo, prospect, sales, reporting, warm-prospect, ui]
related:
  [
    /codex/14-customer-journeys/experience/im-decision-journey.md,
    /codex/14-customer-journeys/experience/staging-demo-journey.md,
    ../shared-core/client-reporting-demo-walkthrough.md,
    ../shared-core/org-fund-client-entity-model.md,
    ../commercial-model/im-vs-reg-reporting-logic.md,
  ]
created: 2026-04-20
authoritative_for: [pb3b IM warm-prospect demo experience]
referenced_by:
  [
    /codex/14-customer-journeys/commercial-model/im-profit-share-structures.md,
    /codex/14-customer-journeys/demo-ops/dart-demo-modes.md,
    /codex/14-customer-journeys/experience/README.md,
    /codex/14-customer-journeys/experience/im-decision-journey.md,
    /codex/14-customer-journeys/experience/staging-demo-journey.md,
    /codex/14-customer-journeys/implementation-mapping/persona-and-user-prototype-mapping.md,
    /codex/14-customer-journeys/implementation-mapping/playbook-to-qa-coverage.md,
    /codex/14-customer-journeys/implementation-mapping/route-mapping.md,
  ]
owner:
last_reviewed:
code_refs: [unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts]
---

# Investment Management — Warm-Prospect Demo

> Experience playbook for pb3b. Narrative overlay; the underlying reporting walkthrough lives in
> [`../shared-core/client-reporting-demo-walkthrough.md`](../shared-core/client-reporting-demo-walkthrough.md). Conforms
> to [rule 01 (grammar)](../_ssot-rules/01-grammar.md) and
> [rule 02 (tone and posture)](../_ssot-rules/02-tone-and-posture.md).

**Internal label:** pb3b (warm-prospect IM demo) **Status:** Stage 2 draft **Owner:** IM desk

## Audience

An allocator — family-office principal, multi-manager allocator, or institutional investment committee representative —
who has completed the pb2a briefing ([im-decision-journey.md](im-decision-journey.md)), attended the second call with
the IM desk, and is now viewing the staging environment to confirm the reporting transparency and allocation operating
model match what was described.

## Moment in journey

Warm-prospect demo. The prospect is logged into staging with a demo user scoped to the IM allocator restriction profile.
The second call resolved which strategy slots fit the allocator's mandate, whether the structure is SMA or Pooled, and a
first-pass commercial shape. The demo's job is to show the reporting and allocation surfaces the allocator will use
post-funding — specifically, that the reporting is operating-grade and that the allocator's view is the real operating
view, filtered for their entitlements.

## What Odum must prove

- The reporting surface the allocator sees in the demo is the same component tree Odum uses to run its own operation —
  not a purpose-built allocator-specific report assembly ([rule 03](../_ssot-rules/03-same-system-principle.md)).
- Positions, P&L attribution, reconciliation, and audit-trail views render with allocator-scoped data; the allocator
  does not see other allocators' data, and Odum's internal views do not appear on the demo path.
- The strategy slots the allocator is being offered are visible with maturity, capacity, and phase metadata — and the
  slots that are not offered (internal-only, client-exclusive, pre-BACKTESTED) are not visible.
- SMA and Pooled structural choices render differently on the demo — SMA shows a distinct fund entity; Pooled shows
  share classes inside a single fund — so the structural decision is tangible.
- Allocator-side NAV, fee accrual, and investor-statement generation are operating features, visible on the demo.

## Experience goal

The allocator leaves the demo either committing to a mandate signing (with a specific date) or naming a specific
reservation on structure, reporting, or pricing that the IM desk can address directly.

## Walkthrough

The IM desk opens the session by confirming the demo context — allocator firm name, the strategy slots scoped to their
mandate, the structure (SMA or Pooled) being demoed, and the demo mode (typically turbo for IM, because the reporting
surface is the single proof point). The session walks four surfaces.

The first is the strategy catalogue, filtered to the public and IM-reserved slots the allocator's mandate shape fits.
Each slot shows maturity (BACKTESTED and later only), phase (live), capacity, and a short descriptor. The narrative
confirms: these are the strategies on offer; no pre-maturity placeholders, no DART-only research surfaces.

The second is the positions and P&L view. Demo data renders the allocator's share (in a Pooled structure) or the full
SMA (in an SMA structure) with positions, exposures, P&L attribution, and reconciliation. The IM desk names that this is
the same components Odum uses to run its own positions internally —
[rule 03](../_ssot-rules/03-same-system-principle.md) — with entitlement filtering applied.

The third is allocator-side NAV and fee accrual. The view shows share-class NAV across time, management fee accrual,
performance fee accrual if applicable, and the investor-statement generation path. The narrative names the fact that
this is how the allocator's own investor reporting will be produced once live.

The fourth is reconciliation and audit trail. Venue-side fills reconciled against instructions, with any breaks surfaced
and resolved in the demo data. The audit trail is the trail a diligence visit would walk; the allocator sees its shape,
not its operational internals.

The session closes with the SMA-vs-Pooled structural recap. The demo has shown one of the two; the IM desk names the
trade-offs on the other, references
[`../shared-core/org-fund-client-entity-model.md`](../shared-core/org-fund-client-entity-model.md), and frames the next
step — mandate signing or one structural follow-up.

The underlying reporting click-path is the shared walkthrough in
[`../shared-core/client-reporting-demo-walkthrough.md`](../shared-core/client-reporting-demo-walkthrough.md). pb3b's
overlay is the narrative; the click-path is the shared asset.

## Key messages

1. You're looking at the production system, filtered to your allocator view. Staging is the production UI with a
   different entitlement set.
2. Reporting is the same surface Odum uses internally. One component tree, entitlement-sliced for allocator views.
3. The strategies on this page are the strategies on offer. Nothing pre-maturity, nothing client-exclusive, nothing
   DART-only is visible.
4. SMA and Pooled are structurally different. What you see now is your chosen structure; the trade-off on the other is a
   twenty-minute conversation.
5. Mandate signing is the next step. Onboarding runs legal, fund setup, venue provisioning, and reporting entitlements
   in parallel.

## What not to show

- DART research, promote, and strategy-authoring surfaces — [rule 04](../_ssot-rules/04-dart-commercial-axes.md) +
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY. Allocators allocate capital; they do not
  operate strategies, and those surfaces are not a plausible next step.
- Pre-BACKTESTED maturity strategy slots — [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY.
- Other allocators' positions, capital, or fund structure — [rule 06](../_ssot-rules/06-show-dont-show-discipline.md),
  HIDDEN-ENTIRELY. Entitlement slicing enforces this.
- Other allocators' investor-statement detail — [rule 06](../_ssot-rules/06-show-dont-show-discipline.md),
  HIDDEN-ENTIRELY.
- Internal pricing cost column — [rule 08](../_ssot-rules/08-pricing-principles.md), HIDDEN-ENTIRELY.
- Execution-layer depth beyond what surfaces on the reporting view —
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), LOCKED-VISIBLE with a short note. Execution is
  Odum-operated; the allocator sees the consequences, not the mechanism.
- Raw market or on-chain data feeds — [rule 07](../_ssot-rules/07-data-licensing-boundaries.md), HIDDEN-ENTIRELY. The
  reporting surface is Odum-enriched.
- Internal admin, ops, devops, or config routes — HIDDEN-ENTIRELY.
- Tier A / Tier B specific numbers — reserved for the commercial follow-up, not the demo.

## Desired next step

Agree the mandate signing date.

## Internal handoff

The IM desk captures the session outcome in the account-intelligence record — surfaces covered, structural resolution
(SMA or Pooled), gaps surfaced, reservations raised, named next commitment. If the allocator agrees the mandate signing,
the record transitions to onboarding ownership and the workstreams kick off — legal mandate draft, fund setup (Pooled
share class registration or SMA entity formation), venue and credential provisioning, and reporting entitlement
configuration. If the allocator surfaces a reservation on structure, pricing, or reporting, the reservation is captured
verbatim and routed to the IM desk for direct response. If the allocator has combined IM + Reg Umbrella intent, the pb3a
companion demo is scheduled through [`../demo-ops/demo-decision-matrix.md`](../demo-ops/demo-decision-matrix.md).

---

## Cross-references

- [rule 01 — grammar](../_ssot-rules/01-grammar.md)
- [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md)
- [rule 03 — same-system principle](../_ssot-rules/03-same-system-principle.md) — reporting is a filter over one
  component tree
- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md)
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md)
- Impl-layer: [../playbooks/03b-demo-im.md](../playbooks/03b-demo-im.md)
- Upstream briefing: [im-decision-journey.md](im-decision-journey.md)
- Shared walkthrough:
  [../shared-core/client-reporting-demo-walkthrough.md](../shared-core/client-reporting-demo-walkthrough.md)
- Shared reporting core: [../shared-core/shared-reporting-core.md](../shared-core/shared-reporting-core.md)
- Org / fund entity model:
  [../shared-core/org-fund-client-entity-model.md](../shared-core/org-fund-client-entity-model.md)
- SMA vs Pooled:
  [../../14-customer-journeys/playbook-concepts/sma-vs-pooled.md](../../14-customer-journeys/playbook-concepts/sma-vs-pooled.md)
- IM commercial model:
  [../commercial-model/im-vs-reg-reporting-logic.md](../commercial-model/im-vs-reg-reporting-logic.md)
- Demo restriction profile (IM): [../demo-ops/demo-restriction-profiles.md](../demo-ops/demo-restriction-profiles.md)
- Playwright spec: `unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts` (IM persona)
