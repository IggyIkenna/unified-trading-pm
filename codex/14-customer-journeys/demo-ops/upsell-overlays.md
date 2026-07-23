---
doc_type: codex-ssot
title: Upsell Overlays — Base Package vs Next Tier
summary:
  Staging-only tier-comparison overlay on LOCKED-VISIBLE surfaces (base package vs next-tier read-only preview) —
  sales-invoked, one per demo max; research/promote, venue/chain/instrument-pack, and analytics-pack upsells; never
  shows pricing, internal cost, client references, or forward-tense features; not used on first-look/Reg/IM demos.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [sales, engineer, admin]
tags: [demo-ops, sales, dart, upsell, locked-visible, catalogue]
related:
  [
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/demo-ops/dart-demo-modes.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-curation-rules.md,
    ../commercial-model/dart-entry-points.md,
  ]
created: 2026-04-20
authoritative_for: [upsell overlays (LOCKED-VISIBLE tier comparison)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/demo-ops/README.md,
    /codex/14-customer-journeys/demo-ops/dart-demo-modes.md,
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-curation-rules.md,
    /codex/14-customer-journeys/experience/staging-demo-journey.md,
    /codex/14-customer-journeys/presentations/target-experience-post-refactor.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Upsell Overlays — Base Package vs Next Tier

> The in-demo toggle that shows "this is your base package" next to "this is what the next tier adds". Used sparingly in
> late-stage demos.

**Rule source:** [rule 06](../_ssot-rules/06-show-dont-show-discipline.md) §LOCKED-VISIBLE vs HIDDEN-ENTIRELY

## What it is

A staging-only visual treatment marking a LOCKED-VISIBLE surface with a tier-comparison panel:

- **Base-package view** — what the current restriction profile unlocks.
- **Next-tier preview** — what upgrading unlocks, rendered read-only.

Applied to LOCKED-VISIBLE surfaces only. HIDDEN-ENTIRELY surfaces do not carry overlays.

## When overlays appear

1. **LOCKED-VISIBLE surface on catalogue / nav** — research / promote-pipeline surfaces for signals-only prospects;
   advanced analytics packs; out-of-scope venue packs.
2. **Sales-invoked toggle** in late-stage demos. Admin-pane control; hidden from prospect otherwise.
3. **Explicit prospect question.** "What would we see if we upgraded to full DART?" → overlay answers visually.

## When overlays do NOT appear

- First-look demos (rule 02 calm posture).
- Reg Umbrella demos (engagement is the engagement).
- IM demos (upsell within reporting confuses).
- Prospects who have expressed price sensitivity.

## What the overlay shows

### Research / promote upsell (signals-only → full DART)

Catalogue renders with "Full DART" badge on research phase pill; research surface LOCKED-VISIBLE with "Available in Full
DART" chip. On click: short description of research capability + cross-reference to
[`../experience/dart-briefing.md`](../experience/dart-briefing.md) signals-vs-full comparison + link to commercial
session. No pricing.

### Venue / chain / instrument-type pack upsell

Catalogue row outside current scope renders greyed with "Additional scope available" chip. On click: panel names the
pack and commercial process to add.

### Analytics pack upsell

Unpurchased analytics dashboard renders as preview tile with "Additional analytics pack" chip.

## What the overlay does NOT show

- **Pricing.** Never. Rule 08.
- **Internal cost.** Never. Rule 08 + rule 06.
- **Specific client references.** Never. Rule 06.
- **Competitor comparisons.** Never. Rule 02.
- **Forward-tense features.** Never. If not currently on Odum's stack, not an overlay.

## Design principles

- Sparse. One overlay per demo max.
- Read-only preview. Interaction happens after commercial upgrade.
- Honest framing. "Available in full DART" is honest; "unlock" is not (rule 02 banned vocabulary).
- Linked to the upgrade path.

## Anti-patterns

- Overlay everywhere — pressure. One per demo.
- Overlay pricing — never.
- Overlay aspirational features — only live capabilities.

## Cross-references

- [rule 06](../_ssot-rules/06-show-dont-show-discipline.md) — LOCKED-VISIBLE
- [rule 02](../_ssot-rules/02-tone-and-posture.md) — calm posture
- [rule 08](../_ssot-rules/08-pricing-principles.md)
- [demo-restriction-profiles.md](demo-restriction-profiles.md)
- [dart-demo-modes.md](dart-demo-modes.md)
- [../experience/dart-demo.md](../experience/dart-demo.md)
- [../commercial-model/dart-entry-points.md](../commercial-model/dart-entry-points.md)
- [../implementation-mapping/route-mapping.md](../implementation-mapping/route-mapping.md)
