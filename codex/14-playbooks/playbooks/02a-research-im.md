# Playbook 2a — Research & Docs: Investment Management

> **Layer:** Implementation. Narrative lives in
> [experience/im-decision-journey.md](../experience/im-decision-journey.md).

## Who this is for

Prospect interested in allocating capital to Odum-managed systematic strategies. Already had a first call; now getting a
deeper briefing on the IM proposition before committing to a demo.

## Pre-req state

- Prospect signed in via briefings gate (pb2)
- Selected the Investment Management pillar from the briefings hub

## Route

`/briefings/investment-management`

## What they see

Deep-briefing content covering:

1. **What Odum IM is** — our own systematic strategies, run on our own platform, under our own FCA authorisation,
   offered to external allocators.
2. **The four catalogues** — the universe of what Odum can trade, each an SSOT (see
   [../cross-cutting/catalogues.md](../cross-cutting/catalogues.md)):
   - Data Catalogue (what data we have)
   - Strategy Catalogue (what strategies we run)
   - ML Model Catalogue (what models power our strategies)
   - Execution Algo Catalogue (how we execute)
3. **Fund structure options** — Pooled vs SMA (see
   [../cross-cutting/sma-vs-pooled.md](../cross-cutting/sma-vs-pooled.md))
4. **Client reporting** — what reporting you get as an allocator (same surface used in pb3 demo — see
   [../cross-cutting/client-reporting.md](../cross-cutting/client-reporting.md))
5. **Regulatory framework** — FCA 975797, MiFID II, how reporting + compliance flows
6. **Track record** — real capital, real returns, link to investor-facing materials
7. **Next steps** — link to booking a demo (promotes prospect to pb3)

## Exit state

- **Books demo** → Odum admin provisions IM-flavoured staging account → pb3b
- **Needs more info** → Odum sales follow-up
- **Drops**

## Content source

- Currently: [lib/briefings/content.ts](unified-trading-system-ui/lib/briefings/content.ts)
- Long-term: consider moving to structured codex with transclusion from [02a-research-im.md] itself → CMS pattern

## Visibility slicing

pb2a is within the briefings gate. No further slicing — once through the gate, prospect sees full IM briefing.

## Related codex references

The IM briefing should transclude or reference (not duplicate):

- [../../09-strategy/architecture-v2/README.md](../../09-strategy/architecture-v2/README.md) — strategy taxonomy
- [../../04-architecture/share-class-architecture.md](../../04-architecture/share-class-architecture.md) — share class /
  NAV
- [../../04-architecture/capital-structure-and-regulatory.md](../../04-architecture/capital-structure-and-regulatory.md)
  — regulatory framework
- [../../07-security/compliance.md](../../07-security/compliance.md) — MiFID II / FCA events
- [../cross-cutting/catalogues.md](../cross-cutting/catalogues.md) — 4-catalogue pattern
- [../cross-cutting/client-reporting.md](../cross-cutting/client-reporting.md) — what the IM prospect will see in pb3b

## IR presentations surfaced here

The `/investor-relations/investment-presentation` page (currently orphan) is a natural **promote** candidate for pb2a —
lift those slides into the briefings section or link out. Decision in
[../page-triage/triage-matrix.md](../page-triage/triage-matrix.md).

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
