# Playbook 1 — Marketing, pre-first-call

## Who this is for

An anonymous visitor who stumbled on the Odum homepage or was referred by word of mouth. They have **no prior
relationship** with Odum, **no first call yet**, and the goal is to get them to either (a) book a first call, (b)
request a demo, or (c) bounce — no conversion pressure.

## Pre-req state

- None. No cookies, no session, no auth.
- Environment: primarily `odum-research.com` but `odum-research.co.uk` renders the same homepage too.

## Canonical click path

```
/
 ├── nav:Investment Management → /investment-management
 ├── nav:Data, Research & Trading (DART) → /platform
 ├── nav:Regulatory → /regulatory
 ├── nav:Who We Are → /firm
 ├── nav:Contact → /contact
 ├── CTA:Discuss a Mandate → /contact
 ├── CTA:Explore the Platform → /platform
 ├── CTA:Book a Demo → /contact (or /demo)
 ├── Three-services card "Invest" → /investment-management
 ├── Three-services card "Build & Run" → /platform
 ├── Three-services card "Regulate" → /regulatory
 └── Footer → /privacy, /terms, /contact
```

## What they see

### `/` (homepage) — [app/(public)/page.tsx](<unified-trading-system-ui/app/(public)/page.tsx>)

- Hero: "Unified Trading Infrastructure" + FCA reg number
- Three-service pitch (Invest / Build & Run / Regulate) — clickable cards
- Platform breadth stats (5 asset classes, 100+ venues, 24/7, 100+ TB market data, 5 service lines)
- "Who we work with" archetypes (allocators, trading firms, emerging managers, institutions)
- Coverage tabs (Crypto / DeFi / TradMkts / Sports / Prediction / Regulatory)
- "Why Odum" cards
- Final CTA (Discuss / Book Demo / Check Regulatory Fit)
- Static content is served from `public/homepage.html` via
  [components/marketing/marketing-static-from-file.tsx](unified-trading-system-ui/components/marketing/marketing-static-from-file.tsx)

### `/investment-management` — IM service landing

- Pitch for allocating capital to Odum-managed strategies
- FCA-regulated framework
- CTA: Discuss a Mandate

### `/platform` — DART service landing

- Pitch for building and running strategies on Odum infrastructure
- Strategy-as-a-service framing
- CTA: Book a Demo

### `/regulatory` — Reg Umbrella service landing

- Pitch for operating under Odum's FCA umbrella
- Compliance / MLRO / supervision included
- CTA: Check Regulatory Fit

### `/firm` — who we are

- Founders, team, history, investor list

### `/contact` — enquiry form

- Single form that captures name, firm, service of interest, free text
- Submits to an internal lead-capture endpoint

## Exit state

Three possible exits:

1. **Booked a call / sent enquiry** → Odum sales follows up, eventually sends briefings link → pb2
2. **Requested demo** → Odum admin provisions staging demo account → pb3
3. **Bounced** — no follow-up

## Visibility slicing

pb1 is **fully public**. Every route in pb1 should resolve 200 for an anonymous visitor; there's no entitlement gating
here. If a pb1 route requires auth, it doesn't belong in pb1.

## Orphan concerns

Per the audit, these `(public)/` routes are NOT linked from the homepage or the top nav:

- `/services/backtesting`, `/services/data`, `/services/investment`, `/services/platform`, `/services/regulatory` —
  early-stage public marketing cards; **merge-candidate** with the current `/investment-management` / `/platform` /
  `/regulatory` landing pages. Decision in [../page-triage/duplicate-clusters.md](../page-triage/duplicate-clusters.md).
- `/demo/preview` — orphan; no clear role in pb1. **Defer** — may fit into pb3 signup flow once demo-user provisioning
  hardens.
- `/pending` — orphan; likely for "awaiting approval" state after signup. **Defer**.

## Nav SSOT

- Top nav: [components/shell/site-header.tsx](unified-trading-system-ui/components/shell/site-header.tsx)
- Spaces dropdown "Marketing" section:
  [components/shell/spaces-nav-sections.tsx](unified-trading-system-ui/components/shell/spaces-nav-sections.tsx)
- Homepage content: `public/homepage.html` +
  [components/marketing/marketing-static-from-file.tsx](unified-trading-system-ui/components/marketing/marketing-static-from-file.tsx)

## Test coverage

- Playwright spec: `unified-trading-system-ui/tests/playbooks/marketing-pre-first-call.spec.ts`
- Assertions:
  1. Anonymous visit to `/` → renders 200, all three top CTAs visible
  2. Every href on the homepage resolves 200
  3. Top nav "Sign In" → `/login` renders
  4. Footer links all resolve
  5. Three-service cards land on the correct service page
  6. No auth gate appears anywhere in the pb1 tree

## Related

- Next playbook: [02-research-and-documentation.md](02-research-and-documentation.md)
- Marketing static content: `unified-trading-system-ui/public/*.html`
- Bloomberg-style aesthetic:
  [../cross-cutting/bloomberg-style-aesthetic.md](../cross-cutting/bloomberg-style-aesthetic.md)
