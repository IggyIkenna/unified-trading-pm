---
scope: [engineer, admin, sales]
---

# Playbook 2b — Research & Docs: DART (Data Analytics, Research & Trading)

> **Layer:** Implementation. Narrative lives in [experience/dart-briefing.md](../experience/dart-briefing.md).

## Who this is for

Prospect interested in running their own strategies on Odum infrastructure. Already had a first call; now getting a
deeper briefing on the DART proposition before committing to a demo.

**DART** stands for **D**ata Analytics, **R**esearch & **T**rading. First mention in any public doc expands the acronym;
thereafter use DART. Never use "DRT".

## Pre-req state

- Prospect signed in via briefings gate (pb2)
- Selected the DART (Platform) pillar from the briefings hub

## Route

`/briefings/platform`

## What they see

Deep-briefing content covering:

1. **What DART is** — the platform side of Odum: data acquisition, research stack, execution, observability, reporting.
   Usable either as infrastructure (you run your strategies on our platform) or as strategy-as-a-service (we build
   strategies to your spec and run them for you).

2. **The four catalogues** — the universe of what's available on the platform. See
   [../cross-cutting/catalogues.md](../cross-cutting/catalogues.md):
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

- Currently: [lib/briefings/content.ts](unified-trading-system-ui/lib/briefings/content.ts) (platform pillar)
- Long-term: transclude structured codex from 09-strategy/architecture-v2/

## Visibility slicing

pb2b is within the briefings gate. No further slicing.

## Related codex references

The DART briefing should transclude or reference (not duplicate):

- [../../09-strategy/architecture-v2/README.md](../../09-strategy/architecture-v2/README.md) — strategy taxonomy
- [../../09-strategy/architecture-v2/category-instrument-coverage.md](../../09-strategy/architecture-v2/category-instrument-coverage.md)
  — coverage matrix
- [../../02-data/availability-manifest-and-data-status.md](../../02-data/availability-manifest-and-data-status.md) —
  data catalogue structure
- [../cross-cutting/catalogues.md](../cross-cutting/catalogues.md) — 4-catalogue pattern
- [../cross-cutting/catalogue-strategy.md](../cross-cutting/catalogue-strategy.md)
- [../cross-cutting/catalogue-data.md](../cross-cutting/catalogue-data.md)
- [../cross-cutting/catalogue-ml-model.md](../cross-cutting/catalogue-ml-model.md)
- [../cross-cutting/catalogue-execution-algo.md](../cross-cutting/catalogue-execution-algo.md)

## IR presentations surfaced here

The `/investor-relations/platform-presentation` page is a **promote** candidate for pb2b. Decision in
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
