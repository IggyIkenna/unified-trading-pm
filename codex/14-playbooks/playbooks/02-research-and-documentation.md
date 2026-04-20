# Playbook 2 — Research & Documentation (post-first-call briefings)

> **Layer:** Implementation. Narrative lives in [experience/briefings-hub.md](../experience/briefings-hub.md).

## Who this is for

A prospect who had a first call with Odum and is now getting deeper-dive content to inform their interest. They're not
yet committing to a demo, but they want to understand the product before deciding. Three pillars — they'll click into
the one(s) relevant to them.

## Pre-req state

- Prospect has had a first call.
- Odum sales has sent them the briefings access code.
- They know which of IM / DART / Regulatory Umbrella interests them.

## Canonical click path

```
(email link)
    ↓
/briefings (light-auth gate — enter access code)
    ↓ (session stored in localStorage)
/briefings (hub — three pillar tiles)
    ├── Investment Management → /briefings/investment-management (pb2a)
    ├── Data, Analytics, Research & Trading → /briefings/platform (pb2b)
    └── Regulatory Umbrella → /briefings/regulatory (pb2c)
```

After the briefing, the prospect either:

- Returns for another call to discuss what they read
- Gets promoted to pb3 with a staging demo account
- Drops out of the funnel

## What they see

### `/briefings` (hub)

- Three large tiles, each linking to a sub-briefing
- Each tile has a 2-3 sentence teaser framing the pillar
- Access-code gate wraps the whole section

### `/briefings/investment-management` (pb2a)

- See [02a-research-im.md](02a-research-im.md)

### `/briefings/platform` (pb2b)

- See [02b-research-dart.md](02b-research-dart.md)

### `/briefings/regulatory` (pb2c)

- See [02c-research-regulatory.md](02c-research-regulatory.md)

## Exit state

- **Promoted to pb3** — Odum sales provisions staging demo account and sends link
- **Needs another call** — Odum sales schedules follow-up
- **Dropped** — no further action

## Auth

- Light auth via briefings gate (see
  [../authentication/light-auth-briefings.md](../authentication/light-auth-briefings.md))
- No Firebase, no personas, no entitlements
- Access code rotates when prospect leaves funnel or every 90 days

## Visibility slicing

Within the briefings section, there's no per-user slicing — every authenticated prospect sees all three pillars. If Odum
wants to hide a pillar for a specific prospect, that happens in the welcome email framing (link directly to the relevant
sub-briefing), not via auth.

## Orphan concerns

- Briefings are currently loaded from JSON fixtures in
  [lib/briefings/content.ts](unified-trading-system-ui/lib/briefings/content.ts). Expanding the content may require
  moving to a CMS or to structured codex references. Tracked in [../roadmap/next-waves.md](../roadmap/next-waves.md).

## Nav SSOT

- Briefings layout: [app/(public)/briefings/layout.tsx](<unified-trading-system-ui/app/(public)/briefings/layout.tsx>)
- Briefings content fixture: [lib/briefings/content.ts](unified-trading-system-ui/lib/briefings/content.ts)
- Access gate:
  [components/briefings/briefing-access-gate.tsx](unified-trading-system-ui/components/briefings/briefing-access-gate.tsx)
- Spaces dropdown "Research & Documentation" section:
  [components/shell/spaces-nav-sections.tsx](unified-trading-system-ui/components/shell/spaces-nav-sections.tsx)

## Test coverage

- Playwright spec: `unified-trading-system-ui/tests/playbooks/research-and-documentation.spec.ts`
- Assertions:
  1. Anonymous visit to `/briefings` → gate renders, content hidden
  2. Correct access code → session saves, hub renders
  3. Three pillar tiles link correctly
  4. Each sub-briefing renders with inter-briefing links working
  5. localStorage clear → gate reappears
  6. Wrong access code → rejection shown, no session

## Related

- Previous playbook: [01-marketing-pre-first-call.md](01-marketing-pre-first-call.md)
- Next playbook: [03-warm-prospect-demo.md](03-warm-prospect-demo.md)
- Light auth mechanism: [../authentication/light-auth-briefings.md](../authentication/light-auth-briefings.md)
