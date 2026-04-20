---
scope: [sales, prospect]
---

# Marketing Journey — Anonymous Visitor to First Call

> Experience playbook for pb1. Conforms to [rule 01 (grammar)](../_ssot-rules/01-grammar.md) and
> [rule 02 (tone and posture)](../_ssot-rules/02-tone-and-posture.md).

**Internal label:** pb1 (pre-first-call marketing) **Status:** Stage 2 draft **Owner:** marketing

## Audience

A technically literate institutional reader — a CIO, COO, head of trading, portfolio manager, or family-office principal
— arriving at Odum's public website with no prior relationship and thirty seconds to decide whether Odum is worth a
call.

## Moment in journey

Pre-first-call. The visitor has usually been referred by a peer, has seen Odum mentioned in an industry channel, or is
searching for operating-grade trading infrastructure for a specific problem (regulated cover, systematic allocation,
DeFi-native execution). They are anonymous. No credentials, no gated content, no account.

## What Odum must prove

- Odum is a live operating firm — not a stealth pre-launch, not a platform looking for pilot clients.
- Odum covers three commercial paths — DART, Investment Management, Regulatory Umbrella — with a specific answer at
  each.
- The voice on the page is the voice of people who run trading operations, not a marketing agency rendering of one.
- There is a plausible next step for any of the three audiences, and that next step is a calendar slot — not a waitlist.

## Experience goal

The visitor leaves the site with a clear three-path frame (DART, IM, Reg Umbrella) and books one thirty-minute intro
call against the path that matches their intent.

## Walkthrough

The home page opens with two sentences that set the frame. The first names what Odum is: a firm that runs systematic
trading strategies on its own capital, under its own FCA permissions, on infrastructure Odum built. The second names the
three commercial paths — DART, Investment Management, Regulatory Umbrella — and the fact that each is a specific answer
to a specific operating problem, not a bundle.

From there the page splits into three service tiles. Each tile is the rule-09 expansion of its service — three
sentences, positioning / differentiator / proof point. DART is the accelerator for strategy, research, execution, and
control; Investment Management allocates client capital to Odum-run strategies; Regulatory Umbrella operates the
client's regulated activity under Odum's permissions. Each tile links to a short service page that unpacks the path
without naming pricing.

The middle of the page shows three concrete proof points. Named venues Odum trades on. Named chains Odum operates
across. Named regulatory permissions Odum holds. Numbers appear where they matter — twelve-month minimum commitment,
thirteen pricing building blocks, three commercial paths — and do not appear where they would invite shallow comparison.
Nothing is prefaced with "revolutionary" or "best-in-class". The posture is [axis.to](https://www.axis.to/) and
[podlabs.xyz](https://podlabs.xyz/): restrained, specific, written by an operating team.

The bottom of the page offers one action per path. Book the IM desk session. Book the DART briefing call. Book the Reg
Umbrella scoping call. Each booking flow takes the visitor straight to a calendar. No email capture wall, no newsletter,
no gated PDF. A visitor who is not ready to book a call leaves without friction; a visitor who is ready books in under
ninety seconds.

## Key messages

1. Odum runs systematic strategies on its own capital, under its own FCA permissions, on infrastructure we built to run
   them.
2. Three commercial paths — DART, Investment Management, Regulatory Umbrella. Each is a specific answer to a specific
   operating problem.
3. The research, execution, and reporting components Odum uses internally are the same ones clients use. One system,
   partitioned views.
4. Minimum engagement is twelve months. Onboarding is provisioning, legal review, and venue setup; the floor recovers
   that reality.
5. Book thirty minutes. The intro call resolves which path fits and what the next session looks like.

## What not to show

- Pricing numbers or building-block breakdowns on the public site — [rule 08](../_ssot-rules/08-pricing-principles.md),
  HIDDEN-ENTIRELY. Pricing conversations start at the intro call, not on the home page.
- Any implication of coming-soon, waitlist, or early-access posture — [rule 02](../_ssot-rules/02-tone-and-posture.md),
  HIDDEN-ENTIRELY. The product is live.
- Competitor names or comparisons — [rule 02](../_ssot-rules/02-tone-and-posture.md), HIDDEN-ENTIRELY.
- Named client references or anonymised case studies with identifying detail —
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY.
- Raw data feeds or data-subscription framing — [rule 07](../_ssot-rules/07-data-licensing-boundaries.md),
  HIDDEN-ENTIRELY. DART is enriched platform services, not raw resale.
- Strategy catalogue detail, research surface, or any authenticated UI route —
  [rule 03](../_ssot-rules/03-same-system-principle.md) + [rule 06](../_ssot-rules/06-show-dont-show-discipline.md),
  HIDDEN-ENTIRELY. Those surfaces live behind auth; the public site describes shape, not content.
- Internal engineering diagrams or architectural depth — HIDDEN-ENTIRELY unless the visitor is a diligence engineer
  reached through a different flow.
- Founder-mode personal narratives — [rule 02](../_ssot-rules/02-tone-and-posture.md), HIDDEN-ENTIRELY. The firm page
  handles firm-level story; product pages stay operational.

## Desired next step

Book the thirty-minute intro call on the service path that matches the visitor's intent.

## Internal handoff

The calendar booking lands in the Odum sales inbox and triggers creation of an account-intelligence record (see
[`demo-ops/account-intelligence-record.md`](../demo-ops/account-intelligence-record.md)). The record captures the
booking path, referring URL, declared intent, and any questions submitted alongside the booking. The owner of the intro
call — IM desk, DART sales, or Reg Umbrella — prepares based on the record, runs the call, and after the call updates
the record with the resolved commercial path. If the call produces intent, the prospect moves to the matching pb2
briefing. If not, the record is marked and the follow-up orchestration from
[`demo-ops/post-demo-followup-orchestration.md`](../demo-ops/post-demo-followup-orchestration.md) applies.

---

## Cross-references

- [rule 01 — grammar](../_ssot-rules/01-grammar.md)
- [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md)
- [rule 03 — same-system principle](../_ssot-rules/03-same-system-principle.md) — the "one system, partitioned views"
  claim on the home page
- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md)
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — no pricing on the public site
- [rule 09 — internal commercial one-liners](../_ssot-rules/09-internal-commercial-oneliners.md) — expansion pattern
  used by the three service tiles
- Impl-layer: [../playbooks/01-marketing-pre-first-call.md](../playbooks/01-marketing-pre-first-call.md)
- Follow-up briefing hub: [briefings-hub.md](briefings-hub.md)
- Commercial entry points: [../commercial-model/dart-entry-points.md](../commercial-model/dart-entry-points.md)
- Playwright spec: `unified-trading-system-ui/tests/e2e/playbooks/marketing.spec.ts`
