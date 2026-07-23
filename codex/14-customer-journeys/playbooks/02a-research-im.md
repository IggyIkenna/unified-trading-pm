---
doc_type: codex-ssot
title: "Playbook 2a — Deep Dive: Investment Management"
summary:
  "pb2a implementation — /briefings/investment-management IM deep-briefing covering the IM proposition, four catalogues,
  Pooled vs SMA, allocator client reporting, FCA 975797 framework and track record; promotes the prospect to the pb3b IM
  demo."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [customer-journey, playbook, briefings, investment-management, reporting, prospect]
related:
  [
    /codex/14-customer-journeys/playbooks/02-research-and-documentation.md,
    /codex/14-customer-journeys/playbooks/02b-research-dart.md,
    /codex/14-customer-journeys/playbooks/02c-research-regulatory.md,
    /codex/14-customer-journeys/playbooks/03b-demo-im.md,
    ../experience/im-decision-journey.md,
  ]
created: 2026-04-19
authoritative_for: [pb2a IM Deep Dive briefing playbook implementation]
referenced_by:
  [
    /codex/14-customer-journeys/experience/im-decision-journey.md,
    /codex/14-customer-journeys/playbooks/02-research-and-documentation.md,
    /codex/14-customer-journeys/playbooks/02b-research-dart.md,
    /codex/14-customer-journeys/playbooks/02c-research-regulatory.md,
    /codex/14-customer-journeys/playbooks/03b-demo-im.md,
    /codex/14-customer-journeys/playbooks/README.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Playbook 2a — Deep Dive: Investment Management

> **Layer:** Implementation. Narrative lives in
> [experience/im-decision-journey.md](../experience/im-decision-journey.md).

## Who this is for

Prospect interested in allocating capital to Odum-managed systematic strategies. Already had a first call; now getting a
deeper briefing on the IM proposition before committing to a demo.

## Pre-req state

- Prospect has unlocked the Deep Dive section via the brief questionnaire on the lock screen OR a per-path access code
  (see [02-research-and-documentation.md](02-research-and-documentation.md) and
  [../authentication/light-auth-briefings.md](../authentication/light-auth-briefings.md))
- Selected the Investment Management pillar from the briefings hub OR landed here directly via a sales-sent link

## Route

`/briefings/investment-management`

## What they see

Deep-briefing content covering:

1. **What Odum IM is** — our own systematic strategies, run on our own platform, under our own FCA authorisation,
   offered to external allocators.
2. **The four catalogues** — the universe of what Odum can trade, each an SSOT (see
   [../cross-cutting/catalogues.md](../playbook-concepts/catalogues.md)):
   - Data Catalogue (what data we have)
   - Strategy Catalogue (what strategies we run)
   - ML Model Catalogue (what models power our strategies)
   - Execution Algo Catalogue (how we execute)
3. **Fund structure options** — Pooled vs SMA (see
   [../cross-cutting/sma-vs-pooled.md](../playbook-concepts/sma-vs-pooled.md))
4. **Client reporting** — what reporting you get as an allocator (same surface used in pb3 demo — see
   [../cross-cutting/client-reporting.md](../playbook-concepts/client-reporting.md))
5. **Regulatory framework** — FCA 975797, MiFID II, how reporting + compliance flows
6. **Track record** — real capital, real returns, link to investor-facing materials
7. **Next steps** — link to booking a demo (promotes prospect to pb3)

## Exit state

- **Books demo** → Odum admin provisions IM-flavoured staging account → pb3b
- **Needs more info** → Odum sales follow-up
- **Drops**

## Content source

- Current: [lib/briefings/content.ts](unified-trading-system-ui/lib/briefings/content.ts)
- Target: structured codex with transclusion from this doc. CMS pattern tracked in
  [../roadmap/next-waves.md](../roadmap/next-waves.md).

## Visibility slicing

pb2a sits inside the Deep Dive gate. No further slicing — once through the gate, the prospect sees the full IM briefing.
The next slicing boundary is at Strategy Evaluation DDQ → Sandbox demo (pb3b).

## Related codex references

The IM briefing transcludes or references (never duplicates):

- [../../09-strategy/architecture-v2/README.md](../../09-strategy/architecture-v2/README.md) — strategy taxonomy
- [../../04-architecture/share-class-architecture.md](../../04-architecture/share-class-architecture.md) — share class /
  NAV
- [../../04-architecture/capital-structure-and-regulatory.md](../../04-architecture/capital-structure-and-regulatory.md)
  — regulatory framework
- [../../07-security/compliance.md](../../07-security/compliance.md) — MiFID II / FCA events
- [../cross-cutting/catalogues.md](../playbook-concepts/catalogues.md) — 4-catalogue pattern
- [../cross-cutting/client-reporting.md](../playbook-concepts/client-reporting.md) — what the IM prospect will see in
  pb3b

## IR presentations surfaced here

`/investor-relations/investment-presentation` promotes into pb2a: slides lift into the briefings section or link out.
See [../page-triage/triage-matrix.md](../page-triage/triage-matrix.md).

## Test coverage

Covered under the parent pb2 Playwright spec `tests/playbooks/research-and-documentation.spec.ts` — dedicated
sub-assertions for pb2a:

1. Briefing renders with all sections present
2. Links to external codex open correctly (or render inline if using transclusion)
3. "Book a Demo" CTA → `/contact` or `/demo` with IM context pre-filled

## Related

- pb2 hub: [02-research-and-documentation.md](02-research-and-documentation.md)
- Sibling: [02b-research-dart.md](02b-research-dart.md), [02c-research-regulatory.md](02c-research-regulatory.md)
- Demo flavour: [03b-demo-im.md](03b-demo-im.md)
