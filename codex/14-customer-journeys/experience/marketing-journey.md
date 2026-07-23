---
doc_type: codex-ssot
title: Marketing Journey — Anonymous Visitor to First Call
summary:
  pb1 anonymous-visitor-to-first-call marketing journey — the 5-path public nav (DART umbrella with signals-in/full,
  Odum Signals, Investment Management, Regulatory, Firm) with no email wall, plus the inline 6-axis light-auth
  questionnaire gate (since 2026-04-25) that is now the briefings access path.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [sales, prospect]
tags: [marketing, prospect, sales, ui, briefings, pricing]
related:
  [
    /codex/14-customer-journeys/experience/briefings-hub.md,
    ../authentication/light-auth-briefings.md,
    ../commercial-model/dart-entry-points.md,
    ../shared-core/competitive-landscape.md,
    ../implementation-mapping/route-mapping.md,
  ]
created: 2026-04-20
authoritative_for: [pb1 pre-first-call marketing journey experience]
referenced_by:
  [
    /codex/14-customer-journeys/authentication/light-auth-briefings.md,
    /codex/14-customer-journeys/demo-ops/account-intelligence-record.md,
    /codex/14-customer-journeys/experience/README.md,
    /codex/14-customer-journeys/implementation-mapping/persona-and-user-prototype-mapping.md,
    /codex/14-customer-journeys/implementation-mapping/playbook-to-qa-coverage.md,
    /codex/14-customer-journeys/implementation-mapping/route-mapping.md,
    /codex/14-customer-journeys/playbooks/01-marketing-pre-first-call.md,
    /codex/14-customer-journeys/presentations/target-experience-post-refactor.md,
  ]
owner:
last_reviewed:
code_refs:
  [
    unified-trading-system-ui/tests/e2e/playbooks/marketing-pre-first-call.spec.ts,
    unified-trading-system-ui/tests/e2e/playbooks/marketing-site-restructure.spec.ts,
  ]
---

# Marketing Journey — Anonymous Visitor to First Call

> Experience playbook for pb1. Conforms to [rule 01 (grammar)](../_ssot-rules/01-grammar.md) and
> [rule 02 (tone and posture)](../_ssot-rules/02-tone-and-posture.md).

**Internal label:** pb1 (pre-first-call marketing) **Status:** Stage 2 live **Owner:** marketing **Restructure:** 5-path
nav + light-auth briefings gate shipped under
[`../../../plans/archive/marketing_site_restructure_2026_04_20.plan.md`](../../../plans/archive/marketing_site_restructure_2026_04_20.plan.md).

## Audience

A technically literate institutional reader — a CIO, COO, head of trading, portfolio manager, or family-office principal
— arriving at Odum's public website with no prior relationship and thirty seconds to decide whether Odum is worth a
call.

## Moment in journey

Pre-first-call. The visitor has usually been referred by a peer, has seen Odum mentioned in an industry channel, or is
searching for operating-grade trading infrastructure for a specific problem (regulated cover, systematic allocation,
DeFi-native execution, or signal distribution). They are anonymous. No credentials, no gated content, no account.

## What Odum must prove

- Odum is a live operating firm — not a stealth pre-launch, not a platform looking for pilot clients.
- Odum covers five commercial paths — **DART** (split across direction arrows: signals-in and full pipeline), **Odum
  Signals** (signals-out direction), **Investment Management**, **Regulatory Umbrella**, and the **Firm** itself — with
  a specific answer at each.
- The voice on the page is the voice of people who run trading operations, not a marketing agency rendering of one.
- There is a plausible next step for any of these audiences, and that next step is a calendar slot — not a waitlist.

## Nav structure — 5 top-level paths

Locked decision M1 (plan `marketing_site_restructure_2026_04_20.plan.md`): the shell header exposes **five** top-level
paths plus a Contact CTA. DART is the umbrella for the two direction-arrow sub-paths; Odum Signals is a peer path rather
than a sub-page of DART.

| Nav label                 | Route                                                              | Covers                                                                              |
| ------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| **DART**                  | `/platform` (umbrella) + `/platform/signals-in` + `/platform/full` | Full data-analytics-research-trading stack; two direction arrows under the umbrella |
| **Odum Signals**          | `/signals`                                                         | Odum strategies delivered to a counterparty that executes (QRT-style, outbound)     |
| **Investment Management** | `/investment-management`                                           | Allocate client capital to Odum-run strategies under Odum's FCA permissions         |
| **Regulatory**            | `/regulatory`                                                      | FCA Umbrella — Odum's permissions cover the client's regulated activity             |
| **Firm**                  | `/who-we-are`                                                      | Team, operating history, FCA credentials                                            |
| _(secondary)_ Contact     | `/contact`                                                         | First-call booking for any path                                                     |

**Route alias note:** the nav label "Firm" resolves to `/who-we-are` — the existing route slug pre-dates the 5-path
rename. Implementation-mapping table
([`../implementation-mapping/route-mapping.md`](../implementation-mapping/route-mapping.md)) captures this alias.

## Direction-arrow naming (M3, locked)

Two direction arrows exist around DART and must be named explicitly in every marketing touchpoint:

- **DART Signals-In** — _your signals, our execution_. The client (Elysium, Desmond, an internal desk) owns the alpha;
  Odum owns the execution, reconciliation, and reporting. Lives under `/platform/signals-in`.
- **Odum Signals** (signals-out direction) — _Odum → counterparty_. Odum owns the alpha; the counterparty (QRT-style)
  owns the execution. Lives under `/signals`.

These two phrases are canonical. They replace earlier shorthand ("client-signal DART" / "Odum signals"). HTML copy and
React component copy both use this form.

## Experience goal

The visitor leaves the site with a clear five-path frame, identifies which path matches their intent in a single click
from `/`, and either (a) books a thirty-minute intro call or (b) enters the light-auth briefings gate if a sales contact
has already sent a code.

## Walkthrough

The home page opens with two sentences that set the frame. The first names what Odum is: a firm that runs systematic
trading strategies on its own capital, under its own FCA permissions, on infrastructure Odum built. The second names the
five commercial paths — DART, Signals, Investment Management, Regulatory, Firm — and the fact that each is a specific
answer to a specific operating problem, not a bundle.

From there the page splits into path tiles. Each tile is the rule-09 expansion of its service — three sentences,
positioning / differentiator / proof point. DART is framed as two direction arrows (signals-in + full); Odum Signals is
framed as Odum → counterparty; Investment Management allocates client capital to Odum-run strategies; Regulatory
Umbrella operates the client's regulated activity under Odum's permissions; the Firm tile summarises operating history
and FCA credentials. Each tile links to the named path route for a deeper read without naming pricing.

The middle of the page shows concrete proof points. Named venues Odum trades on. Named chains Odum operates across.
Named regulatory permissions Odum holds. Numbers appear where they matter — twelve-month minimum commitment, thirteen
pricing building blocks, five commercial paths — and do not appear where they would invite shallow comparison. Nothing
is prefaced with "revolutionary" or "best-in-class". The posture is [axis.to](https://www.axis.to/) and
[podlabs.xyz](https://podlabs.xyz/): restrained, specific, written by an operating team.

The bottom of the page offers one action per path. Book the IM desk session. Book the DART briefing call (specifying
signals-in or full). Book the Odum Signals scoping call. Book the Reg Umbrella scoping call. Each booking flow takes the
visitor straight to a calendar. No email capture wall, no newsletter, no gated PDF. A visitor who is not ready to book
leaves without friction; a visitor who is ready books in under ninety seconds.

## Deep Dive — light-auth gate (questionnaire IS the access path since 2026-04-25)

Any prospect who clicks a Deep Dive item from the side-nav (Briefings, Developer docs, FAQ, founder long-form story, or
one of the six briefing pillars) hits a light-auth gate. The gate **embeds the brief 6-axis questionnaire inline** —
filling it auto-activates the session and emails the prospect the access code (for return visits) plus a "Next steps"
block (read briefings → book Calendly → submit Strategy Evaluation DDQ). A secondary "I already have an access code"
disclosure supports warm hand-offs where sales has sent a per-path code in advance.

This means there's no longer a hard pre-req of "had a first call before getting briefings access" — the questionnaire
serves as the qualification step, generating the Firestore record sales pivots from. See
[`../authentication/light-auth-briefings.md`](../authentication/light-auth-briefings.md) for the full mechanism.

Behind the gate live six briefing pillars — one per commercial path plus the DART umbrella — each with schema detail,
custody mechanics, onboarding workstreams, and strategy-family catalogue material deliberately held back from the public
pages. Plus developer docs, founder long-form, and FAQ. This is the mid-funnel experience that used to live in a PDF;
now it lives in the same UI the prospect will use post-Sandbox-demo.

## Key messages

1. Odum runs systematic strategies on its own capital, under its own FCA permissions, on infrastructure we built to run
   them.
2. Five commercial paths — DART (umbrella for signals-in + full), Odum Signals (signals-out), Investment Management,
   Regulatory Umbrella, and the Firm. Each is a specific answer to a specific operating problem.
3. The research, execution, and reporting components Odum uses internally are the same ones clients use. One system,
   partitioned views.
4. Minimum engagement is twelve months. Onboarding is provisioning, legal review, and venue setup; the floor recovers
   that reality.
5. Book thirty minutes. The intro call resolves which path fits and what the next session looks like.

## Competitive landscape — internal positioning (not on the page)

> This section informs the voice of the public site but does not appear on it. Competitor firm names are
> [rule 02 (tone and posture)](../_ssot-rules/02-tone-and-posture.md) banned from external surfaces. The canonical comp
> set, tiers, and posture guidance live in
> [`../shared-core/competitive-landscape.md`](../shared-core/competitive-landscape.md) and should be read before any
> pitch deck, press piece, or discovery call that references the market.

The trading-infrastructure market is sold in six layers: data and market intelligence, research / backtest / strategy
development, execution and smart order routing, charting and terminal UX, open-source automation, and regulatory /
hosted-manager services. Specialists exist in every layer, and several are genuinely better on their home lane than Odum
would be if Odum tried to win that lane head-on. The honest external frame is therefore not "we beat any one of them" —
it is "we deliver a single operating layer across the layers the market usually sells separately, so the buyer stops
paying the stitching tax." Public-site copy expresses this without naming firms: _unified layer vs fragmented stack_.

Odum's combined shape sits across regulated coverage, investment-management reporting, strategy and research operating
system, downstream execution and operating control, one taxonomy across five categories (crypto, DeFi, TradFi, sports,
prediction), and one unified experience across the full trade lifecycle. Any single bullet in that list has a stronger
specialist. The combined shape does not, which is the thing protected in messaging.

**Posture rule for anyone running a discovery call:** partner-first, never conquest-first. If a prospect names a
specific firm, acknowledge the firm's strength on its home lane (honest), explain Odum's different shape (specific), and
decline to disparage — several of the firms referenced in the comp set are in Odum's own supplier stack. Internal PR
tone references split into two buckets: the DART-side institutional-infra register (reference firms on the execution /
research / reporting layer) and the fund-services register (reference firms on the hosted-manager / ManCo layer). See
[`../shared-core/competitive-landscape.md`](../shared-core/competitive-landscape.md) for the full comp set, tier
structure, and per-layer posture guidance.

The site keeps to the [rule 02](../_ssot-rules/02-tone-and-posture.md) voice and the
[rule 03](../_ssot-rules/03-same-system-principle.md) mechanism claim. The "unified layer" frame is the external
expression of the combined-shape advantage; the competitor set informs calibration but never appears on the page.

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
- Strategy catalogue detail, full schema specs, and fund/SMA hierarchy visuals on the public pages —
  [rule 03](../_ssot-rules/03-same-system-principle.md) + [rule 06](../_ssot-rules/06-show-dont-show-discipline.md),
  HIDDEN-ENTIRELY on `/platform`, `/signals`, `/investment-management`, `/regulatory`. These surfaces live behind the
  light-auth briefings gate (M5 / M7, locked). Public pages describe the shape; full detail lives at
  `/briefings/{pillar}`.
- Internal engineering diagrams or architectural depth — HIDDEN-ENTIRELY unless the visitor is a diligence engineer
  reached through a different flow.
- Founder-mode personal narratives — [rule 02](../_ssot-rules/02-tone-and-posture.md), HIDDEN-ENTIRELY. The firm page
  handles firm-level story; product pages stay operational.

## Desired next step

Two equally valid next steps from the public site:

1. **Click any Deep Dive item** (Briefings, Developer docs, FAQ, founder story) — fills the brief questionnaire on the
   lock screen, gets emailed the access code plus a "Next steps" framing.
2. **Book the thirty-minute intro call** on Calendly — for prospects who'd rather talk first. The call lands them in the
   same funnel; sales sends per-path code post-call so they can use the warm hand-off path.

Either route converges on: read briefings → book Calendly call (if not already booked) → submit Strategy Evaluation DDQ
→ get curated Sandbox demo.

## Internal handoff

The calendar booking lands in the Odum sales inbox and triggers creation of an account-intelligence record (see
[`demo-ops/account-intelligence-record.md`](../demo-ops/account-intelligence-record.md)). The record captures the
booking path, referring URL, declared intent, and any questions submitted alongside the booking. The owner of the intro
call — IM desk, DART sales, Signals sales, or Reg Umbrella — prepares based on the record, runs the call, and after the
call updates the record with the resolved commercial path. If the call produces intent, the prospect moves to the
matching pb2 briefing path (one of six pillars behind the light-auth gate). If not, the record is marked and the
follow-up orchestration from
[`demo-ops/post-demo-followup-orchestration.md`](../demo-ops/post-demo-followup-orchestration.md) applies.

---

## Cross-references

- [rule 01 — grammar](../_ssot-rules/01-grammar.md)
- [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md)
- [rule 03 — same-system principle](../_ssot-rules/03-same-system-principle.md) — the "one system, partitioned views"
  claim on the home page
- [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md) — five-path matrix
- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md)
- [rule 07 — data licensing boundaries](../_ssot-rules/07-data-licensing-boundaries.md)
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — no pricing on the public site
- [rule 09 — internal commercial one-liners](../_ssot-rules/09-internal-commercial-oneliners.md) — expansion pattern
  used by the five path tiles
- [shared-core/competitive-landscape.md](../shared-core/competitive-landscape.md) — internal comp set, tiers, PR tone
  references; public-site copy derives the "unified layer vs fragmented stack" frame from here without naming firms
- Impl-layer: [../playbooks/01-marketing-pre-first-call.md](../playbooks/01-marketing-pre-first-call.md)
- Follow-up briefing hub: [briefings-hub.md](briefings-hub.md)
- Light-auth gate: [../authentication/light-auth-briefings.md](../authentication/light-auth-briefings.md)
- Commercial entry points: [../commercial-model/dart-entry-points.md](../commercial-model/dart-entry-points.md)
- Route mapping: [../implementation-mapping/route-mapping.md](../implementation-mapping/route-mapping.md)
- Restructure plan:
  [../../../plans/archive/marketing_site_restructure_2026_04_20.plan.md](../../../plans/archive/marketing_site_restructure_2026_04_20.plan.md)
- Playwright specs: `unified-trading-system-ui/tests/e2e/playbooks/marketing-pre-first-call.spec.ts` +
  `marketing-site-restructure.spec.ts`
