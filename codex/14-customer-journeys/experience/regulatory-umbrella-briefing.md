---
doc_type: codex-ssot
title: Regulatory Umbrella — Post-First-Call Briefing
summary:
  pb2c Regulatory Umbrella post-first-call briefing — firms run regulated activity under Odum's FCA permissions (Odum as
  regulated counterparty) across 5 onboarding workstreams (legal, compliance, MLRO, venue, reporting); enumerates
  in/out-of-scope activities, 12-month floor, no direct-FCA-application advice.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [sales, prospect]
tags: [regulatory, briefing, prospect, sales, compliance, onboarding, ui]
related:
  [
    /codex/14-customer-journeys/experience/regulatory-demo.md,
    /codex/14-customer-journeys/experience/briefings-hub.md,
    ../commercial-model/im-vs-reg-reporting-logic.md,
    ../../07-security/compliance.md,
    ../shared-core/shared-reporting-core.md,
  ]
created: 2026-04-20
authoritative_for: [pb2c Regulatory Umbrella post-first-call briefing experience]
referenced_by:
  [
    /codex/04-architecture/commercial-service-families.md,
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/commercial-model/im-vs-reg-reporting-logic.md,
    /codex/14-customer-journeys/experience/README.md,
    /codex/14-customer-journeys/experience/briefings-hub.md,
    /codex/14-customer-journeys/experience/regulatory-demo.md,
    /codex/14-customer-journeys/implementation-mapping/persona-and-user-prototype-mapping.md,
    /codex/14-customer-journeys/implementation-mapping/playbook-to-qa-coverage.md,
  ]
owner:
last_reviewed:
code_refs: [unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts]
---

# Regulatory Umbrella — Post-First-Call Briefing

> Experience playbook for pb2c. Conforms to [rule 01 (grammar)](../_ssot-rules/01-grammar.md) and
> [rule 02 (tone and posture)](../_ssot-rules/02-tone-and-posture.md).

**Internal label:** pb2c (post-first-call Reg Umbrella briefing) **Status:** Stage 2 draft **Owner:** Reg Umbrella lead

## Audience

A principal at a firm that wants to run regulated trading activity — systematic or discretionary — without holding
direct FCA authorisation. Typical readers are emerging managers launching a strategy, established operators spinning out
a new vehicle, or DeFi-native firms stepping into regulated execution.

## Moment in journey

Post-first-call. The prospect has had a thirty-minute intro with Odum leadership and is reading the Regulatory Umbrella
briefing ahead of a second call. The intro resolved that the prospect wants regulatory cover; the briefing answers what
that cover actually involves — scope, onboarding, compliance posture, reporting surface, commercial shape — so the
second call moves to specifics.

## What Odum must prove

- Odum holds live FCA permissions and operates compliance, MLRO, and supervisory reporting internally — this is not
  outsourced oversight repackaged.
- Regulatory Umbrella is a real operating engagement: the firm operates under Odum's permissions, with Odum as the
  regulated counterparty, and Odum carries the corresponding compliance obligations.
- Onboarding covers the full set — legal scope, compliance signoff, MLRO coverage, venue setup, reporting setup — and
  has a predictable shape, not a bespoke negotiation per firm.
- The reporting surface the Umbrella firm uses is the same surface IM and DART clients use, filtered to the
  regulated-activity view.
- Commitment floor and onboarding cost recovery is twelve months; the floor reflects onboarding reality, not pricing
  anchor.

## Experience goal

The prospect finishes the briefing with a clear picture of the Umbrella engagement shape — regulatory scope, onboarding
path, compliance operating model, reporting surface, commitment — and books the second call to walk their specific
activity against Odum's permissions.

## Walkthrough

The briefing opens with the Reg Umbrella rule-09 expansion: firms running regulated activity operate under Odum's
permissions, with Odum handling regulatory scope, compliance, MLRO, and supervisory reporting. Reporting surfaces are
filtered views of Odum's internal operating system — see
[`../commercial-model/im-vs-reg-reporting-logic.md`](../commercial-model/im-vs-reg-reporting-logic.md). Odum is a live
regulated operator, not a regulatory broker.

The second section is regulatory scope. The briefing enumerates the permissions Odum holds and the activities they cover
— not a legal document, but specific enough that the prospect can check whether their planned activity fits. Activities
outside Odum's scope are named as outside scope, not hedged. A prospect whose activity is out of scope learns that from
the briefing, not from a third meeting.

The third section is the onboarding path. Five workstreams run in parallel: legal scoping and agreements, compliance
signoff, MLRO onboarding, venue and infrastructure setup, and reporting setup. Each has a stated owner inside Odum —
compliance team, MLRO, operations, engineering — and a stated dependency on the prospect. The reader leaves with a
mental model of what onboarding feels like and what they are responsible for.

The fourth section is the operating model once live. The Umbrella firm operates as the designated representative (or
equivalent structure) under Odum's permissions. Odum runs compliance monitoring, supervisory checks, transaction
reporting, and best-execution evidence on the firm's activity. The firm retains strategic and commercial control; the
regulatory operations layer runs through Odum. Reg-specific view: Pooled vs SMA is an accounting/setup choice for the
firm's structure — see [`../cross-cutting/sma-vs-pooled.md`](../playbook-concepts/sma-vs-pooled.md). MIFID surfaces,
transaction reporting, and supervisory artifacts render from the shared component tree.

The fifth section is commitment. The engagement is twelve months minimum. The rationale is identical across services:
legal, compliance, MLRO, venue, and reporting setup are fixed-cost provisioning that the twelve-month floor recovers.
Pricing is per block — regulatory umbrella reporting, reporting core, execution layer, venue packs, instrument-type
packs — and explored in the second call.

The briefing closes with the second-call hook: a forty-five-minute session with the Reg Umbrella lead to walk the
prospect's activity against Odum's permissions, confirm scope fit, and map the onboarding path specifically.

## Key messages

1. Odum holds FCA permissions and operates compliance, MLRO, and supervisory reporting internally. The firm does not
   broker regulation; it operates under it.
2. Regulatory Umbrella clients run their activity under Odum's permissions, as designated representatives or an
   equivalent structure. Odum carries the regulatory obligations that follow.
3. Onboarding has five workstreams — legal, compliance, MLRO, venue, reporting — each with a stated Odum owner.
4. Reporting surfaces filter from the shared component tree (see
   [`../commercial-model/im-vs-reg-reporting-logic.md`](../commercial-model/im-vs-reg-reporting-logic.md)).
   Reg-specific: Pooled vs SMA is an accounting/setup choice, not a product choice.
5. Twelve-month minimum engagement. Onboarding costs are real and the floor recovers them.

## What not to show

- Odum's internal compliance procedures, MLRO workbook, or supervisory SOPs —
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY. Prospects learn that the functions are
  operated; they do not learn how they are operated internally.
- Internal pricing cost column — [rule 08](../_ssot-rules/08-pricing-principles.md), HIDDEN-ENTIRELY.
- Other Umbrella clients' regulatory perimeters, firm names, or activities —
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY.
- DART research, promote, or strategy-authoring surfaces unless the prospect is a combined Umbrella + DART engagement —
  [rule 04](../_ssot-rules/04-dart-commercial-axes.md) + [rule 06](../_ssot-rules/06-show-dont-show-discipline.md),
  HIDDEN-ENTIRELY for pure Umbrella prospects.
- Pre-BACKTESTED maturity strategy slots — [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY.
- Direct FCA-application advisory. Odum operates its own permissions; it does not advise firms on obtaining their own.
  HIDDEN-ENTIRELY — if the prospect wants direct authorisation, Odum is the wrong counterparty for that project.
- Raw data feeds or regulatory-data-subscription framing — [rule 07](../_ssot-rules/07-data-licensing-boundaries.md),
  HIDDEN-ENTIRELY.
- Tier A / Tier B numbers — reserved for the second call.

## Desired next step

Book the forty-five-minute Regulatory Umbrella session.

## Internal handoff

The Reg Umbrella lead picks up the prospect once the session is booked. The CRM record updates with the briefing-read
event, the activity the prospect has declared, and any dwell signals on the regulatory-scope section that indicate scope
questions. Pre-session, the lead cross-references Odum's permissions against the prospect's declared activity and flags
fit or scope gap. The session walks the activity in detail, covers the onboarding path, and produces either a scoped
next step (legal terms draft, compliance pre-review) or a scope decision (out of scope, route elsewhere). If the session
produces alignment, the prospect transitions to pb3a — the warm-prospect Regulatory demo on staging — with a demo user
provisioned to the Umbrella restriction profile. If combined with DART or IM, both paths' demos are scheduled per
[`../demo-ops/demo-decision-matrix.md`](../demo-ops/demo-decision-matrix.md).

---

## Cross-references

- [rule 01 — grammar](../_ssot-rules/01-grammar.md)
- [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md)
- [rule 03 — same-system principle](../_ssot-rules/03-same-system-principle.md) — reporting is the same component tree
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) — block 2 (regulatory umbrella
  reporting) is the Umbrella-specific block
- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md)
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — twelve-month minimum
- [rule 09 — internal commercial one-liners](../_ssot-rules/09-internal-commercial-oneliners.md) — Reg Umbrella
  expansion
- Impl-layer: [../playbooks/02c-research-regulatory.md](../playbooks/02c-research-regulatory.md)
- Downstream demo: [regulatory-demo.md](regulatory-demo.md)
- Compliance reference: [../../07-security/compliance.md](../../07-security/compliance.md)
- Shared reporting core: [../shared-core/shared-reporting-core.md](../shared-core/shared-reporting-core.md)
- Org / fund hierarchy: [../shared-core/org-fund-client-entity-model.md](../shared-core/org-fund-client-entity-model.md)
- Playwright spec: `unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts` (Reg Umbrella persona)
