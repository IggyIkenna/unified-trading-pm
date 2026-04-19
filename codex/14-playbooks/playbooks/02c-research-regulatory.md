# Playbook 2c — Research & Docs: Regulatory Umbrella

## Who this is for

Prospect interested in operating under Odum's FCA umbrella — they're a firm who wants to conduct regulated activity but
doesn't have (or doesn't want to wait 12-24 months for) direct FCA authorisation. Already had a first call; now getting
a deeper briefing on how the umbrella works before committing to a demo.

## Pre-req state

- Prospect signed in via briefings gate (pb2)
- Selected the Regulatory Umbrella pillar from the briefings hub

## Route

`/briefings/regulatory`

## What they see

Deep-briefing content covering:

1. **What the umbrella is** — Odum's FCA permissions (reg #975797) cover specific activities; a third-party firm
   operating under the umbrella conducts those activities using Odum's authorisation while providing their own
   operational setup.

2. **Scope** — what activities are covered vs not covered. Per-activity licence mapping.

3. **Compliance, MLRO, supervision included** — Odum provides the compliance officer, money-laundering reporting
   officer, and supervision oversight. The client firm runs day-to-day operations.

4. **Client reporting** — **same reporting surface** as the IM playbook (see
   [../cross-cutting/client-reporting.md](../cross-cutting/client-reporting.md)). Umbrella clients use Odum's reporting
   infrastructure for regulatory filings, investor reporting, performance reporting — everything.

5. **Fund structure options** — Pooled vs SMA (see
   [../cross-cutting/sma-vs-pooled.md](../cross-cutting/sma-vs-pooled.md)). Same structural decision as IM.

6. **Regulatory events + audit trail** — MiFID II trade reporting, best-execution checking, event bus for audit.

7. **Next steps** — link to booking a demo (promotes prospect to pb3a — Reg Umbrella flavour).

## Exit state

- **Books demo** → Odum admin provisions Reg-Umbrella-flavoured staging account → pb3a
- **Needs more info** → Odum sales follow-up
- **Drops**

## Content source

- Currently: [lib/briefings/content.ts](unified-trading-system-ui/lib/briefings/content.ts) (regulatory pillar)

## Visibility slicing

pb2c is within the briefings gate. No further slicing.

## Related codex references

The regulatory briefing should transclude or reference (not duplicate):

- [../../07-security/compliance.md](../../07-security/compliance.md) — MiFID II / FCA / MLRO / ARM
- [../../04-architecture/capital-structure-and-regulatory.md](../../04-architecture/capital-structure-and-regulatory.md)
  — regulatory scope per activity
- [../cross-cutting/client-reporting.md](../cross-cutting/client-reporting.md) — shared reporting surface
- [../cross-cutting/sma-vs-pooled.md](../cross-cutting/sma-vs-pooled.md) — structural choice

## IR presentations surfaced here

The `/investor-relations/regulatory-presentation` page is a **promote** candidate for pb2c.
`/investor-relations/disaster-recovery` may also promote here (regulatory prospects care about business continuity).

## Test coverage

Under parent spec `tests/playbooks/research-and-documentation.spec.ts`:

1. Briefing renders all sections
2. Emphasises "same client reporting as IM" cross-reference
3. "Book a Demo" CTA routes to pb3a flavour

## Related

- pb2 hub: [02-research-and-documentation.md](02-research-and-documentation.md)
- Sibling: [02a-research-im.md](02a-research-im.md), [02b-research-dart.md](02b-research-dart.md)
- Demo flavour: [03a-demo-reg-umbrella.md](03a-demo-reg-umbrella.md)
