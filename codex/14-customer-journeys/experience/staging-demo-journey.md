---
doc_type: codex-ssot
title: Staging Demo Journey — Warm-Prospect Hub
summary:
  pb3 warm-prospect demo hub — the staging landing page confirming demo context (firm, resolved path, demo mode) and
  presenting three restriction-profile-gated flavour blocks routing to pb3a/pb3b/pb3c; scope-adjacent surfaces stay
  LOCKED-VISIBLE, sales admin controls hidden from the prospect.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [sales, prospect]
tags: [demo, staging, prospect, sales, warm-prospect, ui, restriction-profiles]
related:
  [
    /codex/14-customer-journeys/experience/regulatory-demo.md,
    /codex/14-customer-journeys/experience/investment-management-demo.md,
    /codex/14-customer-journeys/experience/dart-demo.md,
    ../demo-ops/demo-restriction-profiles.md,
    ../environments/staging-odum-research-co-uk.md,
  ]
created: 2026-04-20
authoritative_for: [pb3 warm-prospect demo hub experience]
referenced_by:
  [
    /codex/14-customer-journeys/demo-ops/dart-demo-modes.md,
    /codex/14-customer-journeys/demo-ops/demo-decision-matrix.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-curation-rules.md,
    /codex/14-customer-journeys/demo-ops/staging-demo-setup.md,
    /codex/14-customer-journeys/experience/README.md,
    /codex/14-customer-journeys/experience/dart-demo.md,
    /codex/14-customer-journeys/experience/investment-management-demo.md,
    /codex/14-customer-journeys/experience/regulatory-demo.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Staging Demo Journey — Warm-Prospect Hub

> Experience playbook for pb3 hub. Conforms to [rule 01 (grammar)](../_ssot-rules/01-grammar.md) and
> [rule 02 (tone and posture)](../_ssot-rules/02-tone-and-posture.md).

**Internal label:** pb3 (warm-prospect demo — hub) **Status:** Stage 2 draft **Owner:** sales

## Audience

A warm prospect who has read the matching pb2 briefing, booked and attended the forty-five-minute second call, and has
been provisioned a demo account on Odum's staging environment. The demo is the third encounter; the decision to demo was
explicit, not automatic.

## Moment in journey

Warm-prospect demo. The prospect has resolved their path (IM, signals-only DART, full DART, Reg Umbrella, or a
combination) and has a specific reason to see the product — the second call produced a scope proposal, and the demo
either confirms the proposal or surfaces a gap. The hub is the landing surface when the prospect logs into staging for
the first time.

## What Odum must prove

- The staging environment is a faithful view of the production system. Same UI, same component tree, same data shapes —
  the demo is not a sales-specific mock ([rule 03](../_ssot-rules/03-same-system-principle.md)).
- The demo's restriction profile reflects the resolved commercial path. What the prospect sees and does not see is
  deliberate and explainable ([rule 06](../_ssot-rules/06-show-dont-show-discipline.md)).
- The demo lands the prospect on surfaces that are plausible next steps in their engagement, not on a generic product
  tour.
- The next step is named — a mandate signing, an onboarding kickoff, a specific deeper session on one surface.

## Experience goal

The prospect leaves the demo with one of two outcomes — a specific next commitment (mandate, onboarding date, deep-dive
session), or a specific reservation (scope gap, timing, pricing) that sales can address directly. "Interesting, let's
keep in touch" is not an outcome; the hub is designed to resolve.

## Walkthrough

The hub is the landing page a demo user sees after signing in to `odum-research.co.uk`. The page opens with one short
paragraph confirming the demo context — the prospect's firm name, the path the demo is scoped to, the demo mode (broader
platform / turbo / deep-dive per [`../demo-ops/dart-demo-modes.md`](../demo-ops/dart-demo-modes.md)), and the sales
person present. This context is not decorative; it confirms that the session is scoped, not a generic tour.

The middle of the hub presents three navigational blocks, one per flavour. The prospect's restriction profile (see
[`../demo-ops/demo-restriction-profiles.md`](../demo-ops/demo-restriction-profiles.md)) determines which blocks unlock
and which show LOCKED-VISIBLE with an upgrade-path message. IM → pb3b; Reg Umbrella → pb3a; DART → pb3c. Combined
engagements unlock two; the third stays LOCKED-VISIBLE.

The bottom of the hub names the demo length — typically forty-five to sixty minutes — and the agenda structure for the
session. The agenda is not the click-path itself; it is the list of what the session will cover. The sales person runs
the click-path live inside the unlocked surface; the hub is the doorway, not the script.

The hub also exposes the demo controls available to the sales person — upsell overlays, demo-mode toggle, restriction
profile inspector. These are not shown to the prospect directly; they live behind an admin pane. See
[`../demo-ops/demo-restriction-profiles.md`](../demo-ops/demo-restriction-profiles.md) for the configuration model and
[`../demo-ops/upsell-overlays.md`](../demo-ops/upsell-overlays.md) for the base-package-vs-next-tier pattern.

## Key messages

1. The staging environment is the production UI. The restriction profile differs; the components do not.
2. This demo is scoped to your resolved path. What you see is deliberate; what you don't see is also deliberate.
3. The session agenda is on the page. We work through it together.
4. The next step is explicit at the end of the session — a mandate, an onboarding date, or a specific follow-up on one
   surface.

## What not to show

- Surfaces outside the resolved commercial path — [rule 04](../_ssot-rules/04-dart-commercial-axes.md) +
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), LOCKED-VISIBLE with a short explanation. Scope-adjacent
  surfaces (for example DART research for a signals-only prospect) are locked with an upgrade-path message; they are not
  hidden entirely, because hiding them breaks the upgrade conversation.
- Internal admin, ops, devops, or config routes — [rule 06](../_ssot-rules/06-show-dont-show-discipline.md),
  HIDDEN-ENTIRELY.
- Pre-BACKTESTED maturity strategy slots — [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY.
- Other clients' data, positions, or entitlement sets — [rule 06](../_ssot-rules/06-show-dont-show-discipline.md) +
  [rule 07](../_ssot-rules/07-data-licensing-boundaries.md), HIDDEN-ENTIRELY.
- Raw data feeds or data-subscription framing — [rule 07](../_ssot-rules/07-data-licensing-boundaries.md),
  HIDDEN-ENTIRELY. Demo data is Odum-enriched or synthetic.
- Internal cost column or any pricing breakdown — [rule 08](../_ssot-rules/08-pricing-principles.md), HIDDEN-ENTIRELY.
  Demo is shape and scope; numbers live in the commercial follow-up.
- Sales admin controls (restriction profile inspector, demo-mode toggle, upsell overlays) —
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY from the prospect's view.

## Desired next step

Complete the scoped flavour demo (pb3a, pb3b, or pb3c) and close the session with a named next commitment.

## Internal handoff

The hub records every click, every surface opened, and every LOCKED-VISIBLE click-through into the account-intelligence
record. After the session, the owning sales person closes the session with a structured post-demo update in
[`../demo-ops/meeting-history-and-interest-tracking.md`](../demo-ops/meeting-history-and-interest-tracking.md) style:
agenda covered, gaps surfaced, reservations raised, next commitment named. If the next commitment is a mandate, the
record transitions to onboarding ownership. If the next commitment is a follow-up session, the post-demo follow-up
orchestration scheduler queues the touch (see
[`../demo-ops/post-demo-followup-orchestration.md`](../demo-ops/post-demo-followup-orchestration.md)). If the prospect
surfaces a scope or timing reservation, the record captures it verbatim for the demo-decision-matrix review.

---

## Cross-references

- [rule 01 — grammar](../_ssot-rules/01-grammar.md)
- [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md)
- [rule 03 — same-system principle](../_ssot-rules/03-same-system-principle.md) — staging is production UI, filtered
- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md)
- Impl-layer: [../playbooks/03-warm-prospect-demo.md](../playbooks/03-warm-prospect-demo.md)
- Flavour demos: [regulatory-demo.md](regulatory-demo.md) ·
  [investment-management-demo.md](investment-management-demo.md) · [dart-demo.md](dart-demo.md)
- Demo restriction profiles: [../demo-ops/demo-restriction-profiles.md](../demo-ops/demo-restriction-profiles.md)
- Demo modes: [../demo-ops/dart-demo-modes.md](../demo-ops/dart-demo-modes.md)
- Pre-demo curation: [../demo-ops/pre-demo-curation-rules.md](../demo-ops/pre-demo-curation-rules.md)
- Environment: [../environments/staging-odum-research-co-uk.md](../environments/staging-odum-research-co-uk.md)
- Playwright spec: `unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts`
