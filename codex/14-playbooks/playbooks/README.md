---
scope: [engineer, admin, sales]
---

# `playbooks/` — [IMPL LAYER]

> **Layer marker:** these docs are the **engineering-grade implementation layer** of the playbook SSOT. They describe
> the same journeys as the experience layer, but at the register of routes, services, entitlements, data bindings,
> Playwright specs, and auth tiers.
>
> **For narrative, sales-owned playbooks, read [`../experience/`](../experience/) first.** The experience layer is the
> new top-of-funnel content; this dir is the engineering substrate that makes those journeys run.

## Who reads what

| Reader               | Read first                                                                                     | Then                                                                        |
| -------------------- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Sales / commercial   | [`../experience/`](../experience/)                                                             | This dir only when cross-referenced                                         |
| Product / leadership | [`../experience/`](../experience/)                                                             | [`../_ssot-rules/`](../_ssot-rules/)                                        |
| Engineering          | This dir + [`../cross-cutting/`](../cross-cutting/)                                            | [`../_ssot-rules/`](../_ssot-rules/) when commercial decisions are in scope |
| Admin / ops          | This dir + [`../authentication/`](../authentication/) + [`../environments/`](../environments/) | All                                                                         |

## What lives in this dir

Three families of impl-layer playbooks, in the legacy numbering:

1. **pb1 — Pre-first-call marketing** ([01-marketing-pre-first-call.md](01-marketing-pre-first-call.md))
2. **pb2 — Post-first-call research & documentation** — hub
   ([02-research-and-documentation.md](02-research-and-documentation.md))
   - three sub-areas ([02a-research-im.md](02a-research-im.md), [02b-research-dart.md](02b-research-dart.md),
     [02c-research-regulatory.md](02c-research-regulatory.md))
3. **pb3 — Warm-prospect demo on staging** — hub ([03-warm-prospect-demo.md](03-warm-prospect-demo.md)) + three flavours
   ([03a-demo-reg-umbrella.md](03a-demo-reg-umbrella.md), [03b-demo-im.md](03b-demo-im.md),
   [03c-demo-dart.md](03c-demo-dart.md))

Each impl-layer doc describes:

- The canonical click path with concrete routes.
- The entitlement set required for the auth persona walking the path.
- The component and service dependencies behind each surface.
- The Playwright spec that asserts the path.
- The cross-cutting concerns invoked (visibility slicing, client reporting, catalogues, etc.).

## Relationship to the experience layer

Each impl-layer doc has (or will have) a sibling in [`../experience/`](../experience/) that describes the same journey
from the audience perspective. The two layers are paired:

| Experience doc                                                                 | Impl doc                                                                                                        |
| ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| [`../experience/im-decision-journey.md`](../experience/im-decision-journey.md) | [02a-research-im.md](02a-research-im.md) + [03b-demo-im.md](03b-demo-im.md)                                     |
| `../experience/reg-umbrella-decision-journey.md` (Stage 2)                     | [02c-research-regulatory.md](02c-research-regulatory.md) + [03a-demo-reg-umbrella.md](03a-demo-reg-umbrella.md) |
| `../experience/dart-signals-only-journey.md` (Stage 2)                         | [02b-research-dart.md](02b-research-dart.md) + [03c-demo-dart.md](03c-demo-dart.md)                             |
| `../experience/dart-full-pipeline-journey.md` (Stage 2)                        | [02b-research-dart.md](02b-research-dart.md) + [03c-demo-dart.md](03c-demo-dart.md)                             |
| `../experience/marketing-pre-first-call.md` (Stage 2)                          | [01-marketing-pre-first-call.md](01-marketing-pre-first-call.md)                                                |

When an impl-layer doc changes — a new route, a new entitlement axis, a new demo restriction — the matching experience
doc is reviewed in the same PR. Cross-references at the bottom of each doc are the propagation path.

## Where commercial content lives

Commercial-facing decisions (pricing framing, show / don't-show, tone, same-system claims) live in
[`../_ssot-rules/`](../_ssot-rules/), not here. Impl-layer docs cite the rules when their content touches a commercial
decision. Examples:

- Entitlement slicing for demo personas → cites [rule 06](../_ssot-rules/06-show-dont-show-discipline.md).
- "Research / promote surfaces locked for signals-only personas" → cites
  [rule 04](../_ssot-rules/04-dart-commercial-axes.md) and
  [rule 10](../_ssot-rules/10-strategy-instruction-schema-principles.md).
- "Reporting-surface component tree is the same across IM and DART" → cites
  [rule 03](../_ssot-rules/03-same-system-principle.md).

Adding a new commercial decision inside an impl-layer doc is a drift signal. Lift the decision into the rules dir and
cite it here.

## How to update an impl-layer doc

1. Identify the matching experience doc. Pair the update.
2. If the update invokes a commercial decision not in [`../_ssot-rules/`](../_ssot-rules/), pause — lift the decision
   into the rules dir first.
3. Update routes, entitlements, specs, cross-cutting references.
4. Update the matching Playwright spec under `unified-trading-system-ui/tests/e2e/playbooks/` in the same PR.
5. Cross-reference into / out of the experience doc.

## Cross-references

- [`../README.md`](../README.md) — playbook SSOT landing page with the layered structure
- [`../_ssot-rules/`](../_ssot-rules/) — the ten rules governing every experience doc
- [`../experience/`](../experience/) — narrative playbooks
- [`../glossary.md`](../glossary.md) — canonical terms
- [`../information-architecture.md`](../information-architecture.md) — IA tree
- [`../testing/test-matrix.md`](../testing/test-matrix.md) — playbook × persona × environment → test file
