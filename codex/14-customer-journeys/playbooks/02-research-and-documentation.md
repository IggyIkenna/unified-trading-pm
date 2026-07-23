---
doc_type: codex-ssot
title: Playbook 2 — Deep Dive (formerly "Research & Documentation")
summary:
  'pb2 Deep Dive implementation — questionnaire-as-access-path light-auth gate to the /briefings hub (six pillar tiles)
  + sibling /docs //our-story //faq under one session; section renamed "Deep Dive" 2026-04-25; Strategy Evaluation DDQ
  gates the Tier-2 Sandbox demo.'
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [customer-journey, playbook, briefings, light-auth, ui, onboarding, prospect]
related:
  [
    /codex/14-customer-journeys/playbooks/01-marketing-pre-first-call.md,
    /codex/14-customer-journeys/playbooks/03-warm-prospect-demo.md,
    /codex/14-customer-journeys/playbooks/02a-research-im.md,
    ../authentication/light-auth-briefings.md,
    ../experience/briefings-hub.md,
  ]
created: 2026-04-19
authoritative_for: [pb2 Deep Dive briefings playbook implementation (access gate + hub click path)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/authentication/light-auth-briefings.md,
    /codex/14-customer-journeys/experience/briefings-hub.md,
    /codex/14-customer-journeys/page-triage/partial-archive.md,
    /codex/14-customer-journeys/playbook-concepts/investor-relations.md,
    /codex/14-customer-journeys/playbooks/01-marketing-pre-first-call.md,
    /codex/14-customer-journeys/playbooks/02a-research-im.md,
    /codex/14-customer-journeys/playbooks/02b-research-dart.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Playbook 2 — Deep Dive (formerly "Research & Documentation")

> **Layer:** Implementation. Narrative lives in [experience/briefings-hub.md](../experience/briefings-hub.md).

> **Section name:** the public marketing site labels this section **Deep Dive** in both nav surfaces (site-header Sheet
> drawer + Spaces dropdown). The "Research & Documentation" naming survives only in this codex file's URL slug and the
> Playwright spec filename — the user-facing label was renamed 2026-04-25.

## Who this is for

A prospect interested in Odum who wants to read briefings, developer docs, the founder story, or the FAQ before
committing to a call. Two valid entry channels (see §Pre-req state below):

- **Cold inbound** — found the marketing site, hits a Deep Dive item from the nav, fills the brief questionnaire on the
  lock screen to unlock.
- **Warm hand-off** — Odum sales sent a per-path code in advance; uses the "I already have a code" disclosure on the
  gate.

Most prospects in 2026 take the cold-inbound route — the questionnaire IS the access path now (since 2026-04-25).

## Pre-req state

- Prospect has either:
  - Submitted the brief questionnaire (cold inbound, channel A), OR
  - Received a per-path access code from Odum sales (warm hand-off, channel B), OR
  - Already has a cached `localStorage.odum-briefing-session` from a prior visit on the same browser.

There is no longer a hard pre-req of "had a first call" — the questionnaire serves as the qualification step, generating
the Firestore record sales pivots from.

## Canonical click path

```
(any Deep Dive entry: nav item, marketing-page deep link, direct URL)
    ↓
<BriefingAccessGate>  — locked
    ├── Confidentiality + funnel intro (3 lines)
    ├── Embedded questionnaire form (compact, 6-axis + Reg-Umbrella branch)
    └── ▸ "I already have an access code" disclosure (secondary)
    ↓ (submit OR paste correct code)
[setBriefingSessionActive() + email-back fires + redirect]
    ↓
/briefings (hub — six pillar tiles + "How to use this page" intro + "Next steps to a Sandbox demo" CTA)
    ├── /briefings/investment-management (pb2a)
    ├── /briefings/platform           — DART Start Here (pb2b)
    ├── /briefings/dart-signals-in    — DART Signals-In path
    ├── /briefings/dart-full          — DART Full pipeline
    ├── /briefings/signals-out        — Odum Signals (inverse direction)
    └── /briefings/regulatory         — Regulatory Umbrella (pb2c)

    Sibling Deep Dive routes (covered by the same session):
    ├── /docs (developer documentation)
    ├── /our-story (long-form founder narrative)
    └── /faq
```

After the briefings, the prospect either:

- Books a 30-min walk-through call on Calendly (`https://calendly.com/odum-ikenna`).
- Submits the deeper Strategy Evaluation DDQ at `/strategy-evaluation` — required (before or after the call) to unlock
  the curated Sandbox demo at Tier 2.
- Drops out of the funnel.

## What they see

### `/briefings` (hub)

- "How to use this page" intro section (3-step ordered list: read briefings → book call → submit Strategy Evaluation
  DDQ).
- Six briefing-pillar cards (DART Start Here / IM / DART Full / DART Signals-In / Odum Signals / Regulatory).
- Developer documentation link.
- "Next steps to a Sandbox demo" CTA section: Strategy Evaluation submit + Calendly call + Back to home.

### Briefing pillars (per-slug)

- See [02a-research-im.md](02a-research-im.md), [02b-research-dart.md](02b-research-dart.md),
  [02c-research-regulatory.md](02c-research-regulatory.md). DART Signals-In + DART Full + Odum Signals briefings live
  alongside but don't have dedicated sub-playbooks (yet).

### `/docs`, `/our-story`, `/faq`

- Same gate; same session. One unlock covers everything.

## Exit state

- **Promoted to Sandbox demo (pb3)** — Odum sales reviews the prospect's Strategy Evaluation DDQ submission, schedules a
  curated walkthrough, provisions a staging persona.
- **Wants another call first** — books Calendly, sales schedules.
- **Dropped** — no further action.

## Auth

- Light auth via questionnaire-as-access-path + secondary code-entry disclosure (see
  [../authentication/light-auth-briefings.md](../authentication/light-auth-briefings.md)).
- No Firebase, no personas, no entitlements — those kick in at Tier 2 (Sandbox demo).
- Access code rotates when prospect leaves funnel or every 90 days.

## Visibility slicing

Within the Deep Dive section, there's no per-user slicing — every authenticated session sees all six pillars + docs +
FAQ + Our Story. If Odum wants to direct a specific prospect to one pillar, that happens in the welcome email framing
(link directly to the relevant sub-briefing slug), not via auth.

The deeper visibility cut is at the **Strategy Evaluation → Sandbox demo** boundary: the prospect's DDQ answers shape
which strategies surface in their curated Sandbox walkthrough.

## Orphan concerns

- Briefings are currently loaded from JSON fixtures in
  [lib/briefings/content.ts](unified-trading-system-ui/lib/briefings/content.ts). Expanding the content may require
  moving to a CMS or to structured codex references. Tracked in [../roadmap/next-waves.md](../roadmap/next-waves.md).

## Nav SSOT

- Briefings layout: [app/(public)/briefings/layout.tsx](<unified-trading-system-ui/app/(public)/briefings/layout.tsx>)
- Sibling Deep Dive layouts (each wraps in the same gate):
  [app/(public)/docs/layout.tsx](<unified-trading-system-ui/app/(public)/docs/layout.tsx>),
  [app/(public)/our-story/layout.tsx](<unified-trading-system-ui/app/(public)/our-story/layout.tsx>),
  [app/(public)/faq/layout.tsx](<unified-trading-system-ui/app/(public)/faq/layout.tsx>).
- Briefings content fixture: [lib/briefings/content.ts](unified-trading-system-ui/lib/briefings/content.ts)
- Access gate (embeds questionnaire form):
  [components/briefings/briefing-access-gate.tsx](unified-trading-system-ui/components/briefings/briefing-access-gate.tsx)
- Reusable embedded form:
  [components/questionnaire/questionnaire-form.tsx](unified-trading-system-ui/components/questionnaire/questionnaire-form.tsx)
- Side-nav Sheet drawer (collapsible "Deep Dive" toggle with locks):
  [components/shell/site-header.tsx](unified-trading-system-ui/components/shell/site-header.tsx)
- Spaces dropdown "Deep Dive" section:
  [components/shell/spaces-nav-sections.tsx](unified-trading-system-ui/components/shell/spaces-nav-sections.tsx)

## Test coverage

- Playwright spec: `unified-trading-system-ui/tests/e2e/playbooks/research-and-documentation.spec.ts` (describe block:
  "pb2 — Deep Dive")
- Assertions:
  1. Anonymous visit to any Deep Dive route → gate renders, content hidden.
  2. Embedded questionnaire submit → session saves, hub renders, email fires.
  3. Disclosure code-entry with correct code → session saves, content renders inline.
  4. Disclosure code-entry with wrong code → rejection shown, no session.
  5. Six pillar tiles + sibling Deep Dive routes (`/docs`, `/our-story`, `/faq`) all render under one session.
  6. localStorage clear → gate reappears.

## Related

- Previous playbook: [01-marketing-pre-first-call.md](01-marketing-pre-first-call.md)
- Next playbook: [03-warm-prospect-demo.md](03-warm-prospect-demo.md)
- Light auth mechanism: [../authentication/light-auth-briefings.md](../authentication/light-auth-briefings.md)
- 7-step onboarding sequence: [../../08-workflows/client-onboarding.md](../../08-workflows/client-onboarding.md)
- Strategy Evaluation DDQ (the deeper gate to Sandbox): see Step 5 of client-onboarding above.
