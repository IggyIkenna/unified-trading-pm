# `experience/` — Narrative playbooks, sales-owned

The experience layer of the playbook SSOT. Every doc in this dir answers to the ten rules in
[`../_ssot-rules/`](../_ssot-rules/). Experience docs are sales- and product-owned; impl-layer docs under
[`../playbooks/`](../playbooks/) are engineering-owned and describe the same journeys at a different register.

## What belongs here

One doc per (audience × moment-in-journey) cell. Each doc is a stable, citable narrative of what that audience
experiences at that moment in their relationship with Odum. Nine sections, in order, every time
([rule 01](../_ssot-rules/01-grammar.md)).

The canonical set (Stage 1 ships `im-decision-journey.md`; Stage 2 ships the rest):

| Internal | Audience × moment                                                         | File                                                               |
| -------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| pb1      | Anonymous marketing visitor — pre-first-call                              | [marketing-journey.md](marketing-journey.md)                       |
| pb2      | Warm prospect — briefings hub                                             | [briefings-hub.md](briefings-hub.md)                               |
| pb2a     | IM allocator — post-first-call briefing → warm demo                       | [im-decision-journey.md](im-decision-journey.md)                   |
| pb2b     | DART prospect — post-first-call briefing (signals-only vs full fit-check) | [dart-briefing.md](dart-briefing.md)                               |
| pb2c     | Reg Umbrella firm — post-first-call briefing                              | [regulatory-umbrella-briefing.md](regulatory-umbrella-briefing.md) |
| pb3      | Warm prospect — staging demo hub                                          | [staging-demo-journey.md](staging-demo-journey.md)                 |
| pb3a     | Reg Umbrella — warm-prospect demo                                         | [regulatory-demo.md](regulatory-demo.md)                           |
| pb3b     | IM allocator — warm-prospect demo                                         | [investment-management-demo.md](investment-management-demo.md)     |
| pb3c     | DART — warm-prospect demo (signals-only or full pipeline)                 | [dart-demo.md](dart-demo.md)                                       |

IM collapses its briefing and warm-demo narrative into one decision-journey doc (`im-decision-journey.md`), with pb3b's
separate narrative overlay referencing the shared walkthrough in
[`../shared-core/client-reporting-demo-walkthrough.md`](../shared-core/client-reporting-demo-walkthrough.md). DART and
Reg Umbrella split briefing and demo because the demo is structurally distinct from the briefing.

### Reader paths by role

| Role                                                  | Start with                                                         | Then                                                           |
| ----------------------------------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------- |
| Anonymous visitor sales reviewer                      | [marketing-journey.md](marketing-journey.md)                       | [briefings-hub.md](briefings-hub.md)                           |
| IM desk                                               | [im-decision-journey.md](im-decision-journey.md)                   | [investment-management-demo.md](investment-management-demo.md) |
| DART sales                                            | [dart-briefing.md](dart-briefing.md)                               | [dart-demo.md](dart-demo.md)                                   |
| Reg Umbrella lead                                     | [regulatory-umbrella-briefing.md](regulatory-umbrella-briefing.md) | [regulatory-demo.md](regulatory-demo.md)                       |
| Product / engineering reviewing narrative ↔ impl fit | Any experience doc                                                 | Matching impl-layer doc under [`../playbooks/`](../playbooks/) |

## Grammar enforcement

Every doc in this dir has the nine sections from [rule 01](../_ssot-rules/01-grammar.md):

1. Audience
2. Moment in journey
3. What Odum must prove
4. Experience goal
5. Walkthrough
6. Key messages
7. What not to show
8. Desired next step
9. Internal handoff

An experience doc missing any section is not shippable. The Stage 2 agent runs a completeness check against every doc
before commit.

## Tone

Calm, specific, credible, lightly guided. Rule 02 enforces the anti-AI-marketing-tone guardrails — read
[`../_ssot-rules/02-tone-and-posture.md`](../_ssot-rules/02-tone-and-posture.md) before writing, and read aloud before
shipping.

Benchmarks: [axis.to](https://www.axis.to/) and [podlabs.xyz](https://podlabs.xyz/). What to borrow: restrained
headlines, specific proof points, sparse navigation. What not to borrow: crypto-native vocabulary, waitlist energy,
forward-tense marketing.

## Show / don't-show discipline

Every doc has a populated §7 "what not to show" section citing rule 06 and (as relevant) rule 07 + rule 08. Empty §7 is
a drafting failure. LOCKED-VISIBLE vs HIDDEN-ENTIRELY is an explicit choice per item; the canonical reference
([im-decision-journey.md](im-decision-journey.md)) demonstrates the pattern.

## Test coverage

Every experience playbook has a matching Playwright spec under `unified-trading-system-ui/tests/e2e/playbooks/`. The
spec asserts section 5's walkthrough path and section 8's exit. Stage 2 inventories the existing specs and
cross-references them into each doc's cross-references section. When an experience doc changes, the spec updates in the
same PR.

## Relationship to impl-layer docs

Impl-layer docs under [`../playbooks/`](../playbooks/) describe the engineering click-path: routes, services,
entitlements, data bindings. Experience docs describe the narrative: what the audience believes, what Odum must prove,
what the sales person says. The two layers reference each other through the cross-references section at the bottom of
every doc.

An impl-layer change (new route, new entitlement axis, new demo restriction) does not automatically rewrite the
experience doc, but it does trigger a review. The cross-reference chain is how that trigger propagates.

## How to add a new experience doc

1. Copy [TEMPLATE.md](TEMPLATE.md).
2. Fill the nine sections. Rule 01 compliance.
3. Read aloud. Rule 02 compliance; replace any hedging or marketing-register prose.
4. Populate §7 explicitly. Rule 06 compliance; cite rule 07 and rule 08 where applicable.
5. Chain §8 (desired next step) to §9 (internal handoff) — they must tell one continuous story.
6. Add a Playwright spec (or reference an existing one) under `unified-trading-system-ui/tests/e2e/playbooks/`.
7. Cross-reference the matching impl-layer doc under `../playbooks/` if one exists.
8. Update this README's canonical-set table.

## Relationship to Stage 2 + Stage 3

- Stage 2 writes the remaining experience docs and creates `commercial-model/`, `demo-ops/`, `shared-core/`, and
  `implementation-mapping/` dirs that experience docs cite but don't duplicate.
- Stage 3 specs the infra (UAC combo registry + derivation engine) that implements rule-03 same-system + rule-06
  visibility slicing + rule-05 building-block entitlements at runtime.

Experience docs stay stable through both stages; they describe the product's audience face. Stage 2 expands the set;
Stage 3 makes the claims run.
