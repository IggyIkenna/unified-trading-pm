---
doc_type: codex-ssot
title: Bloomberg-style aesthetic
summary:
  Bloomberg-terminal UX principles for every post-login surface — dense scannable tables, knowledgeable-user initial
  state, 90%-invisible-by-default, 2-3-click-to-detail, keyboard-first — plus anti-patterns and colour/typography rules;
  the public marketing homepage is intentionally exempt.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [ui, aesthetic, ux, design, navigation, testing]
related: [../information-architecture.md, /codex/14-customer-journeys/playbook-concepts/visibility-slicing.md]
created: 2026-04-19
authoritative_for: [Bloomberg-style post-login UI aesthetic principles]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/information-architecture.md,
    /codex/14-customer-journeys/playbook-concepts/README.md,
    /codex/14-customer-journeys/playbooks/01-marketing-pre-first-call.md,
    /codex/14-customer-journeys/presentations/target-experience-post-refactor.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Bloomberg-style aesthetic

UX principles governing every surface in the platform (except public marketing).

> User quote: "pretty bloomberg terminal style feel — easy to scan, get to the information that you need fast, so
> collapsing boxes are not too messy. The initial state is like if someone knows, not if someone has no interest. In 90%
> of our services, they shouldn't see them. 99% of the time it should just be a click-click-click, and you're starting
> to get details on where you want to be rather than where you don't need to be."

## Principles

1. **Dense but scannable.** Prefer tables over cards when showing multiple entities. Table rows pack more into less
   space and scan faster than card grids.
2. **Initial state = knowledgeable user.** Landing on a page should assume the user knows what they want. Don't greet
   with onboarding copy; show the data. Onboarding material goes in a separate tab/hover, not the primary view.
3. **90% invisible by default.** Most services shouldn't appear in a user's sightline unless they have entitlement.
   Visibility slicing (see [visibility-slicing.md](visibility-slicing.md)) hides or padlocks everything irrelevant.
4. **Click-click-click to detail.** The fast path should take 2-3 clicks from dashboard to any specific datum. No wizard
   flows for routine navigation.
5. **Collapsing boxes default to collapsed** only when the box contains info 90%+ of users don't care about. If most
   users DO care, default expanded.
6. **Keyboard-first where possible.** Power-user shortcuts (Cmd+K palette, per-service hotkeys) are a first-class
   surface, not an accessibility afterthought.

## Anti-patterns

- ❌ Full-screen hero tiles on post-login pages (wastes vertical space)
- ❌ Modals for anything that could be a side panel
- ❌ "Welcome, <username>!" greetings (user knows who they are)
- ❌ Multi-step wizards for actions a power user does daily (inline-edit tables instead)
- ❌ Accordion-all-collapsed initial states on detail pages (user navigated here specifically; show the data)
- ❌ Confirmation dialogs for reversible actions (undo buttons are better)

## Reference implementations in the codebase

- Command palette:
  [components/shell/command-palette.tsx](unified-trading-system-ui/components/shell/command-palette.tsx) — Cmd+K to jump
  anywhere
- Lifecycle nav: [components/shell/lifecycle-nav.tsx](unified-trading-system-ui/components/shell/lifecycle-nav.tsx) —
  top-level 8-stage lifecycle strip + role-based filtering
- Strategy catalogue coverage matrix:
  [app/(platform)/services/strategy-catalogue/coverage/page.tsx](<unified-trading-system-ui/app/(platform)/services/strategy-catalogue/coverage/page.tsx>)
  — dense archetype × category grid with click-into-detail

## Anti-reference

- Marketing static homepage (`public/homepage.html`) is intentionally NOT Bloomberg-style — it's wide, spacious,
  story-first. That's correct for pb1. Apply these aesthetic principles only to post-login surfaces.

## Colour / typography

- Monospace for numeric data (prices, sizes, P&L)
- Sans-serif for labels and narrative
- Dark mode default (matches trading-room expectations)
- Minimal colour palette: red/green for P&L, yellow for warnings, muted blues/greys for structure
- Reserved colours (never overload): orange for alerts, purple for admin-only surfaces

## Testing

Aesthetic isn't automatically testable, but:

- Playwright can assert density (element count per viewport)
- Playwright can assert no wizard-flows on routine paths (specific routes should never render multi-step forms for
  non-signup actions)
- Visual regression via Percy (or similar) for key surfaces

## Related

- IA: [../information-architecture.md](../information-architecture.md)
- Visibility slicing: [visibility-slicing.md](visibility-slicing.md)
