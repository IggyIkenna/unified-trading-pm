---
doc_type: codex-ssot
title: "Playbook 2c — Deep Dive: Regulatory Umbrella"
summary:
  "pb2c implementation — /briefings/regulatory Reg Umbrella deep-briefing; FCA #975797 umbrella scope, included
  compliance/MLRO/supervision, the shared IM reporting surface and Pooled vs SMA choice; promotes the prospect to the
  pb3a Reg Umbrella demo."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [customer-journey, playbook, briefings, reg-umbrella, compliance, prospect]
related:
  [
    /codex/14-customer-journeys/playbooks/02-research-and-documentation.md,
    /codex/14-customer-journeys/playbooks/02a-research-im.md,
    /codex/14-customer-journeys/playbooks/02b-research-dart.md,
    /codex/14-customer-journeys/playbooks/03a-demo-reg-umbrella.md,
    ../../07-security/compliance.md,
  ]
created: 2026-04-19
authoritative_for: [pb2c Regulatory Umbrella Deep Dive briefing playbook implementation]
referenced_by:
  [
    /codex/14-customer-journeys/experience/regulatory-umbrella-briefing.md,
    /codex/14-customer-journeys/playbooks/02-research-and-documentation.md,
    /codex/14-customer-journeys/playbooks/02a-research-im.md,
    /codex/14-customer-journeys/playbooks/02b-research-dart.md,
    /codex/14-customer-journeys/playbooks/03a-demo-reg-umbrella.md,
    /codex/14-customer-journeys/playbooks/README.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Playbook 2c — Deep Dive: Regulatory Umbrella

> **Layer:** Implementation. Narrative lives in
> [experience/regulatory-umbrella-briefing.md](../experience/regulatory-umbrella-briefing.md).

## Who this is for

Prospect interested in operating under Odum's FCA umbrella — they're a firm who wants to conduct regulated activity but
doesn't have (or doesn't want to wait 12-24 months for) direct FCA authorisation. Already had a first call; now getting
a deeper briefing on how the umbrella works before committing to a demo.

## Pre-req state

- Prospect has unlocked the Deep Dive section via the brief questionnaire on the lock screen OR a per-path access code
  (see [02-research-and-documentation.md](02-research-and-documentation.md) and
  [../authentication/light-auth-briefings.md](../authentication/light-auth-briefings.md))
- Selected the Regulatory Umbrella pillar from the briefings hub OR landed here directly via a sales-sent link

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
   [../cross-cutting/client-reporting.md](../playbook-concepts/client-reporting.md)). Umbrella clients use Odum's
   reporting infrastructure for regulatory filings, investor reporting, performance reporting — everything.

5. **Fund structure options** — Pooled vs SMA (see
   [../cross-cutting/sma-vs-pooled.md](../playbook-concepts/sma-vs-pooled.md)). Same structural decision as IM.

6. **Regulatory events + audit trail** — MiFID II trade reporting, best-execution checking, event bus for audit.

7. **Next steps** — link to booking a demo (promotes prospect to pb3a — Reg Umbrella flavour).

## Exit state

- **Books demo** → Odum admin provisions Reg-Umbrella-flavoured staging account → pb3a
- **Needs more info** → Odum sales follow-up
- **Drops**

## Content source

- Current: [lib/briefings/content.ts](unified-trading-system-ui/lib/briefings/content.ts) (regulatory pillar)

## Visibility slicing

pb2c sits inside the briefings gate. No further slicing.

## Related codex references

The regulatory briefing transcludes or references (never duplicates):

- [../../07-security/compliance.md](../../07-security/compliance.md) — MiFID II / FCA / MLRO / ARM
- [../../04-architecture/capital-structure-and-regulatory.md](../../04-architecture/capital-structure-and-regulatory.md)
  — regulatory scope per activity
- [../cross-cutting/client-reporting.md](../playbook-concepts/client-reporting.md) — shared reporting surface
- [../cross-cutting/sma-vs-pooled.md](../playbook-concepts/sma-vs-pooled.md) — structural choice

## IR presentations surfaced here

`/investor-relations/regulatory-presentation` promotes into pb2c. `/investor-relations/disaster-recovery` also surfaces
here — regulatory prospects care about business continuity.

## Test coverage

Under parent spec `tests/playbooks/research-and-documentation.spec.ts`:

1. Briefing renders all sections
2. Emphasises "same client reporting as IM" cross-reference
3. "Book a Demo" CTA routes to pb3a flavour

## Related

- pb2 hub: [02-research-and-documentation.md](02-research-and-documentation.md)
- Sibling: [02a-research-im.md](02a-research-im.md), [02b-research-dart.md](02b-research-dart.md)
- Demo flavour: [03a-demo-reg-umbrella.md](03a-demo-reg-umbrella.md)
