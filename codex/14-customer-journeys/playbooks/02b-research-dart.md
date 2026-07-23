---
doc_type: codex-ssot
title: "Playbook 2b — Deep Dive: DART (Data Analytics, Research & Trading)"
summary:
  "pb2b implementation — /briefings/platform DART (Data Analytics, Research & Trading) deep-briefing; four catalogues,
  the 8-stage promote pipeline, client-vs-Odum IP lock-states and observability; promotes the prospect to the pb3c DART
  demo."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [customer-journey, playbook, briefings, dart, catalogues, prospect]
related:
  [
    /codex/14-customer-journeys/playbooks/02-research-and-documentation.md,
    /codex/14-customer-journeys/playbooks/02a-research-im.md,
    /codex/14-customer-journeys/playbooks/02c-research-regulatory.md,
    /codex/14-customer-journeys/playbooks/03c-demo-dart.md,
    ../experience/dart-briefing.md,
  ]
created: 2026-04-19
authoritative_for: [pb2b DART Deep Dive briefing playbook implementation]
referenced_by:
  [
    /codex/14-customer-journeys/experience/dart-briefing.md,
    /codex/14-customer-journeys/playbook-concepts/catalogue-execution-algo.md,
    /codex/14-customer-journeys/playbooks/02-research-and-documentation.md,
    /codex/14-customer-journeys/playbooks/02a-research-im.md,
    /codex/14-customer-journeys/playbooks/02c-research-regulatory.md,
    /codex/14-customer-journeys/playbooks/03c-demo-dart.md,
    /codex/14-customer-journeys/playbooks/README.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Playbook 2b — Deep Dive: DART (Data Analytics, Research & Trading)

> **Layer:** Implementation. Narrative lives in [experience/dart-briefing.md](../experience/dart-briefing.md).

## Who this is for

Prospect interested in running their own strategies on Odum infrastructure. Already had a first call; now getting a
deeper briefing on the DART proposition before committing to a demo.

**DART** stands for **D**ata Analytics, **R**esearch & **T**rading. First mention in any public doc expands the acronym;
thereafter use DART. Never use "DRT".

## Pre-req state

- Prospect has unlocked the Deep Dive section via the brief questionnaire on the lock screen OR a per-path access code
  (see [02-research-and-documentation.md](02-research-and-documentation.md) and
  [../authentication/light-auth-briefings.md](../authentication/light-auth-briefings.md))
- Selected the DART (Platform) pillar from the briefings hub OR landed here directly via a sales-sent link

## Route

`/briefings/platform`

## What they see

Deep-briefing content covering:

1. **What DART is** — the platform side of Odum: data acquisition, research stack, execution, observability, reporting.
   Usable either as infrastructure (you run your strategies on our platform) or as strategy-as-a-service (we build
   strategies to your spec and run them for you).

2. **The four catalogues** — the universe of what's available on the platform. See
   [../cross-cutting/catalogues.md](../playbook-concepts/catalogues.md):
   - **Data Catalogue** — 100+ venues, tick to daily, full market + sports + prediction markets
   - **Strategy Catalogue** — 18 archetypes × categories × instrument types
   - **ML Model Catalogue** — model families, training runs, registry
   - **Execution Algo Catalogue** — execution algorithms per venue, benchmarks

3. **Research → Trading lifecycle** — the 8-stage promote pipeline (data-validation → model-assessment → risk-stress →
   execution-readiness → paper-trading → champion → capital-allocation → governance). Each stage has a UI surface in
   pb3.

4. **Your IP vs Odum IP** — strategies you build remain yours; Odum-built strategies remain Odum's. Strategy catalogue
   lock states (PUBLIC / IM_RESERVED / CLIENT_EXCLUSIVE / RETIRED) enforce this.

5. **Observability** — real-time health + risk + reconciliation across everything running on the platform.

6. **Next steps** — link to booking a demo (promotes prospect to pb3c — DART flavour).

## Exit state

- **Books demo** → Odum admin provisions DART-flavoured staging account → pb3c
- **Needs more info** → Odum sales follow-up
- **Drops**

## Content source

- Current: [lib/briefings/content.ts](unified-trading-system-ui/lib/briefings/content.ts) (platform pillar)
- Target: transclude structured codex from 09-strategy/architecture-v2/.

## Visibility slicing

pb2b sits inside the briefings gate. No further slicing.

## Related codex references

The DART briefing transcludes or references (never duplicates):

- [../../09-strategy/architecture-v2/README.md](../../09-strategy/architecture-v2/README.md) — strategy taxonomy
- [../../09-strategy/architecture-v2/category-instrument-coverage.md](../../09-strategy/architecture-v2/category-instrument-coverage.md)
  — coverage matrix
- [../../02-data/availability-manifest-and-data-status.md](../../02-data/availability-manifest-and-data-status.md) —
  data catalogue structure
- [../cross-cutting/catalogues.md](../playbook-concepts/catalogues.md) — 4-catalogue pattern
- [../cross-cutting/catalogue-strategy.md](../playbook-concepts/catalogue-strategy.md)
- [../cross-cutting/catalogue-data.md](../playbook-concepts/catalogue-data.md)
- [../cross-cutting/catalogue-ml-model.md](../playbook-concepts/catalogue-ml-model.md)
- [../cross-cutting/catalogue-execution-algo.md](../playbook-concepts/catalogue-execution-algo.md)

## IR presentations surfaced here

`/investor-relations/platform-presentation` promotes into pb2b. See
[../page-triage/triage-matrix.md](../page-triage/triage-matrix.md).

## Test coverage

Under parent spec `tests/playbooks/research-and-documentation.spec.ts`:

1. Briefing renders all four catalogue sections
2. Links to codex catalogue docs open correctly
3. "Book a Demo" CTA routes to pb3c flavour

## Related

- pb2 hub: [02-research-and-documentation.md](02-research-and-documentation.md)
- Sibling: [02a-research-im.md](02a-research-im.md), [02c-research-regulatory.md](02c-research-regulatory.md)
- Demo flavour: [03c-demo-dart.md](03c-demo-dart.md)
