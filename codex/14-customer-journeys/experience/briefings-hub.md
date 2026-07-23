---
doc_type: codex-ssot
title: Briefings Hub — Post-First-Call Research Landing
summary:
  pb2 post-first-call briefings hub — the single light-auth landing page presenting three default-collapsible briefing
  cards (IM, DART, Reg Umbrella) that route to the matching briefing and book the 45-minute second call; a discovery
  surface, not a qualification gate.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [sales, prospect]
tags: [briefings, prospect, sales, dart, investment-management, regulatory, ui]
related:
  [
    /codex/14-customer-journeys/experience/im-decision-journey.md,
    /codex/14-customer-journeys/experience/dart-briefing.md,
    /codex/14-customer-journeys/experience/regulatory-umbrella-briefing.md,
    ../playbooks/02-research-and-documentation.md,
    ../authentication/light-auth-briefings.md,
  ]
created: 2026-04-20
authoritative_for: [pb2 post-first-call briefings hub experience]
referenced_by:
  [
    /codex/14-customer-journeys/experience/README.md,
    /codex/14-customer-journeys/experience/dart-briefing.md,
    /codex/14-customer-journeys/experience/im-decision-journey.md,
    /codex/14-customer-journeys/experience/marketing-journey.md,
    /codex/14-customer-journeys/experience/regulatory-umbrella-briefing.md,
    /codex/14-customer-journeys/implementation-mapping/persona-and-user-prototype-mapping.md,
    /codex/14-customer-journeys/implementation-mapping/playbook-to-qa-coverage.md,
    /codex/14-customer-journeys/implementation-mapping/route-mapping.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Briefings Hub — Post-First-Call Research Landing

> Experience playbook for pb2 hub. Conforms to [rule 01 (grammar)](../_ssot-rules/01-grammar.md) and
> [rule 02 (tone and posture)](../_ssot-rules/02-tone-and-posture.md).

**Internal label:** pb2 (post-first-call research & documentation — hub) **Status:** Stage 2 draft **Owner:** sales

## Audience

A prospect who has had a thirty-minute intro call with Odum leadership, has a working frame for which service path fits
(DART, IM, or Reg Umbrella — sometimes two), and has been sent a light-auth briefing code to read the relevant briefing
material ahead of the second session.

## Moment in journey

Post-first-call. The prospect is between the intro and the second call. The intro resolved the high-level fit; the
briefing material gives them the shape of the engagement — structure, commercial posture, operating mechanism — so the
second call can move to specifics. The hub is the one page the prospect lands on when they arrive with their briefing
code.

## What Odum must prove

- Odum runs a coherent three-path operation — the briefings are internally consistent, not three disconnected pitches.
- The shared mechanism (one system, partitioned views) holds across every path.
- A prospect who fits two paths (for example Reg Umbrella + signals-only DART) can see how the paths compose.
- The briefing material is substantial enough to read alone; the second call deepens it, does not re-read it.

## Experience goal

The prospect picks the one briefing that matches their resolved path, reads it between the first and second call, and
arrives at the second call ready to discuss specifics — strategies, structure, pricing — not shape.

## Walkthrough

The briefings hub opens with one short paragraph that reframes the three paths in the voice of the service itself. DART
is the accelerator Odum uses internally, packaged for client use. Investment Management allocates client capital to
Odum-run strategies with reporting from the same surface. Regulatory Umbrella operates the client's regulated activity
under Odum's permissions. Each is a rule-09 expansion, not the one-liner.

From there the page presents three briefing cards. The prospect's account record drives which card is default-expanded —
if the intro call resolved to IM, the IM briefing card is open. The other two cards are collapsed but visible, so a
prospect who fits two paths can open both. Nothing is hidden behind another click; the hub is a discovery surface, not a
qualification gate.

Each briefing card names what the briefing covers — strategy surface, structure, reporting, regulatory posture,
commitment — and which specific sections answer which questions. The card is a navigation aid, not a pitch. A prospect
who opens the IM briefing from the hub lands on [`im-decision-journey.md`](im-decision-journey.md) in full. A prospect
who opens the DART briefing lands on [`dart-briefing.md`](dart-briefing.md), which includes the rule-10 fit-check before
pitching the service. A prospect who opens the Reg Umbrella briefing lands on
[`regulatory-umbrella-briefing.md`](regulatory-umbrella-briefing.md).

The hub closes with one sentence naming the next session. The second call is forty-five minutes. It is booked directly
from the hub; the calendar flow lives behind the same light-auth code. A prospect who is not ready to book reads the
briefing and comes back.

## Key messages

1. Three briefings, three paths, one operating system underneath.
2. The briefing is the substantive document. The second call deepens it; it does not re-read it.
3. Prospects who fit two paths read both briefings. The hub surfaces both, not just the default.
4. The second call is forty-five minutes, booked from the hub, owned by the desk that matches the resolved path.

## What not to show

- The other two briefings' internal pricing or scope detail when the prospect has resolved to one path —
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), LOCKED-VISIBLE with a short explanation. The cards are
  visible; the internal commercial detail is not.
- Production UI routes, strategy catalogue depth, or demo-environment screenshots —
  [rule 03](../_ssot-rules/03-same-system-principle.md) + [rule 06](../_ssot-rules/06-show-dont-show-discipline.md),
  HIDDEN-ENTIRELY. The hub is a document surface; the demo surface is pb3.
- Pricing numbers or building-block cost columns — [rule 08](../_ssot-rules/08-pricing-principles.md), HIDDEN-ENTIRELY.
- Raw data or tick-feed framing — [rule 07](../_ssot-rules/07-data-licensing-boundaries.md), HIDDEN-ENTIRELY.
- Internal operations detail (MLRO process internals, onboarding SOP, compliance escalations) —
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY. The prospect sees the fact that these
  exist; they do not see the SOP.
- Admin, ops, or engineering routes — HIDDEN-ENTIRELY.

## Desired next step

Open the briefing matching the resolved path and book the forty-five-minute second call from the briefing footer.

## Internal handoff

When a prospect lands on the hub, the CRM record updates with the landing event, the briefing code used, and the card
that the prospect opens first. If the prospect reads a briefing and books the second call, the booking flows to the desk
that owns that path — IM desk for pb2a, DART sales for pb2b, Reg Umbrella for pb2c. The desk prepares for the session
using the updated account-intelligence record (see
[`demo-ops/account-intelligence-record.md`](../demo-ops/account-intelligence-record.md)) and
[`demo-ops/pre-demo-discovery-framework.md`](../demo-ops/pre-demo-discovery-framework.md). If the prospect reads but
does not book within seven days, the post-demo follow-up orchestration triggers (see
[`demo-ops/post-demo-followup-orchestration.md`](../demo-ops/post-demo-followup-orchestration.md)) with the adapted
"briefing-read, no-book" variant.

---

## Cross-references

- [rule 01 — grammar](../_ssot-rules/01-grammar.md)
- [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md)
- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md)
- [rule 09 — internal commercial one-liners](../_ssot-rules/09-internal-commercial-oneliners.md) — three-card expansion
  pattern
- Impl-layer: [../playbooks/02-research-and-documentation.md](../playbooks/02-research-and-documentation.md)
- Three sub-briefings: [im-decision-journey.md](im-decision-journey.md) · [dart-briefing.md](dart-briefing.md) ·
  [regulatory-umbrella-briefing.md](regulatory-umbrella-briefing.md)
- Authentication: [../authentication/light-auth-briefings.md](../authentication/light-auth-briefings.md)
- Playwright spec: `unified-trading-system-ui/tests/e2e/playbooks/research-and-docs.spec.ts`
