---
doc_type: codex-ssot
title: Post-Demo Follow-Up Orchestration
summary:
  Post-demo follow-up orchestration — 7-day stall trigger (Day0 record update, Day1-6 silent, Day7 one specific
  present-tense message + one asset + one calendar offer), asset-selection-by-signal table, next-stage qualification
  criteria, and Day14/21/quarterly decay; pricing never goes in a follow-up (rule 08).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [sales, engineer, admin]
tags: [demo-ops, sales, follow-up, orchestration, qualification, crm]
related:
  [
    /codex/14-customer-journeys/demo-ops/account-intelligence-record.md,
    /codex/14-customer-journeys/demo-ops/meeting-history-and-interest-tracking.md,
    /codex/14-customer-journeys/demo-ops/demo-decision-matrix.md,
  ]
created: 2026-04-20
authoritative_for: [post-demo follow-up orchestration]
referenced_by:
  [
    /codex/08-workflows/client-onboarding.md,
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/demo-ops/README.md,
    /codex/14-customer-journeys/demo-ops/account-intelligence-record.md,
    /codex/14-customer-journeys/demo-ops/meeting-history-and-interest-tracking.md,
    /codex/14-customer-journeys/experience/briefings-hub.md,
    /codex/14-customer-journeys/experience/dart-demo.md,
    /codex/14-customer-journeys/experience/marketing-journey.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Post-Demo Follow-Up Orchestration

> Seven-day stall trigger, asset / email delivery, provisioning, qualification criteria for moving to next stage. What
> happens when a demo lands without a named next commitment, or when the named commitment starts to lapse.

**Rule source:** [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md) — calm, not desperate

## Orchestration principles

Rule 02 posture applies to follow-up. The follow-up is **specific, present-tense, and calendar-driven.** It is not
nurturing, not needy, not desperate. A prospect who is not ready to act gets one useful follow-up and then orchestration
decays to a scheduled quarterly check-in, not weekly harassment.

## The seven-day stall trigger

If a demo closes without a named next commitment, or the named commitment does not materialise within seven days, the
orchestration triggers.

### Day 0 — Demo closes

- Sales person updates the account-intelligence record (see
  [`meeting-history-and-interest-tracking.md`](meeting-history-and-interest-tracking.md)).
- If `next_commitment_named` is populated with a specific action and deadline, the orchestration is dormant until the
  deadline.
- If `next_commitment_named` is absent (or vague: "we'll be in touch"), the seven-day stall trigger arms.

### Day 1-6 — Silent window

No automated outreach. The prospect is processing. A single thank-you message from the sales person is appropriate; a
proposal / asset dump is not.

### Day 7 — Stall-trigger fires

Automated orchestration produces one message. The message is:

- **Specific to the session.** References surfaces covered + reservations raised + a specific next step the sales person
  proposed.
- **Present tense.** No "just checking in"; no "circling back."
- **One asset max.** The relevant commercial model doc, or an extract of the pricing structure (not numbers), or a
  relevant session recording snippet if one was taken.
- **One calendar offer.** A specific 30-minute slot for a follow-up call.

Example Day-7 message:

> Jane,
>
> Following your DART signals-only demo on 2026-04-18, two points from the session worth following up:
>
> 1. You raised a question about per-instruction risk limits on the stat-arb-pairs-fixed surface. The implementation map
>    is in [instruction-schema-fit-and-package-boundaries.md] — page references in the footer.
> 2. The commercial shape we discussed fits signals-only DART with three venue packs and two chain packs. The commercial
>    model doc covers the tier assignment: [dart-entry-points.md].
>
> Thirty-minute follow-up slot: Thursday 2026-04-30 at 14:00 UK. Reply with "yes" or pick a time that works.
>
> Ikenna

No "unlock." No "best-in-class." No "let me know if you have any questions." Present tense, specific, calendar-driven.

## What goes out

Three possible asset attachments. Pick one based on session signals.

| Signal                                   | Asset                                                                                                                                                                                            |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Reservation on commercial shape          | [`../commercial-model/dart-entry-points.md`](../commercial-model/dart-entry-points.md) or [`../commercial-model/im-vs-reg-reporting-logic.md`](../commercial-model/im-vs-reg-reporting-logic.md) |
| Reservation on scope / schema fit        | [`../shared-core/instruction-schema-fit-and-package-boundaries.md`](../shared-core/instruction-schema-fit-and-package-boundaries.md)                                                             |
| Reservation on structure (SMA vs Pooled) | [`../shared-core/org-fund-client-entity-model.md`](../shared-core/org-fund-client-entity-model.md)                                                                                               |
| Diligence-depth question                 | Session recording snippet (if authorised) or relevant codex SSOT doc                                                                                                                             |
| No specific reservation                  | One relevant experience playbook (pb3 hub doc) + follow-up-call offer                                                                                                                            |

Pricing numbers never go in a follow-up message. Rule 08. Pricing is a synchronous conversation.

## Qualification criteria for next-stage advancement

A prospect advances through stages:

```
pb1 marketing → pb2 briefing → pb2 second call → pb3 demo → commercial close → onboarding → live
```

Qualification criteria for each transition:

| From → To                      | Qualification                                                                           |
| ------------------------------ | --------------------------------------------------------------------------------------- |
| pb1 booking → pb2 briefing     | Intro call produced a resolved commercial path                                          |
| pb2 briefing → pb2 second call | Briefing was read (log event); prospect books second call                               |
| pb2 second call → pb3 demo     | Second call confirmed fit; structure / schema / scope resolved; demo user provisioned   |
| pb3 demo → commercial close    | Demo produced a named next commitment (mandate, onboarding kickoff, commercial meeting) |
| commercial close → onboarding  | Terms agreed, legal drafted                                                             |
| onboarding → live              | Five (Reg Umbrella) or three (IM / DART) workstreams complete                           |

A prospect who does not advance after two rounds of follow-up at a given stage drops to scheduled quarterly check-in.

## Decay schedule

If a prospect does not advance after the Day-7 stall trigger:

- **Day 14:** Sales person sends one more focused message with a different asset or angle. Calendar offer retained.
- **Day 21:** If still unresponsive, sales person decays to a quarterly check-in cadence. One message per quarter,
  calendar-offered.
- **Year+1:** If no engagement in a full year, the account-intelligence record is archived but not deleted. A future
  re-engagement (they come back) re-activates the record with the prior context intact.

## Provisioning on advancement

When a prospect advances from pb3 demo → commercial close (commitment named):

- Commercial team picks up. Legal drafting begins.
- Demo user on staging is retained — the prospect may need to come back for a diligence-depth session.
- Account-intelligence record transitions ownership from sales-front-line to commercial-close team.

When the prospect advances from commercial close → onboarding:

- Onboarding team picks up per the five-workstream model (Reg Umbrella) or three-workstream model (IM / DART).
- User-management-ui provisions production-client, fund, clients, and API-key sets per
  [`../shared-core/org-fund-client-entity-model.md`](../shared-core/org-fund-client-entity-model.md). See
  [`../implementation-mapping/demo-email-and-provisioning-flow.md`](../implementation-mapping/demo-email-and-provisioning-flow.md).

## Orchestration implementation

Stage 3E's refactor plan includes orchestration automation as a named item; until that lands, orchestration runs
semi-manually with the sales person triggering messages from a template library informed by the account-intelligence
record. See
[`../implementation-mapping/demo-email-and-provisioning-flow.md`](../implementation-mapping/demo-email-and-provisioning-flow.md).

## Cross-references

- [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md) — calm follow-up posture
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — no pricing in follow-ups
- [account-intelligence-record.md](account-intelligence-record.md) — the record that drives orchestration
- [meeting-history-and-interest-tracking.md](meeting-history-and-interest-tracking.md) — session logs feed triggers
- [demo-decision-matrix.md](demo-decision-matrix.md) — the matrix informs what second-demo path fits
- [../commercial-model/](../commercial-model/) — assets sent in follow-ups
- [../implementation-mapping/demo-email-and-provisioning-flow.md](../implementation-mapping/demo-email-and-provisioning-flow.md)
  — email + provisioning spec
