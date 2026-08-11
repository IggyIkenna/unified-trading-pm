---
doc_type: codex-ssot
title: Elysium/POD — carve-out deferral voice note script (2026-08-11)
summary: >-
  Speakable script for the voice note sent to both Elysium contacts explaining why the code carve-out is deferred past
  the October delivery, what a carve-out actually costs in engineering time, the AI-assisted Q&A route offered in its
  place, and the middle-ground offer of the strategy-service repository. Records the operator's decisions of 2026-08-11
  on both the deferral and the scope of the code offer.
authoritative_for:
  - elysium carve-out deferral messaging
  - elysium code-disclosure scope decision 2026-08-11
status: current
nature: record
owner: ikennaigboaka
referenced_by: []
last_reviewed: "2026-08-11"
asset_group: [defi]
stage: [meta]
repos: []
scope: [admin]
tags: [commercial-model, elysium, client-communication, carve-out, voice-note]
related:
  [
    /codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/elysium-delay-letter-2026-07-20.md,
    /presentations/elysium/carveout-engineering.html,
    /plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md,
  ]
created: 2026-08-11
last_updated: "2026-08-11"
code_refs: []
---

# Carve-out deferral — voice note script

**Audience:** both Elysium contacts, sent as a voice note. **Purpose:** defer the code carve-out past the October
delivery without it reading as a refusal, and replace it with something faster that they can actually use.

**Operator decisions recorded 2026-08-11 (interactive):**

1. **Defer the carve-out.** Concentrated effort is ~3 engineering days spread over 2–3 weeks of calendar; that time goes
   into the October delivery instead. Carve-out begins when there is bandwidth, after they have capital live.
2. **Offer the strategy-service repository as the middle ground — but only once it is complete.** Ruled by the operator
   after the disclosure trade-off was put to them: strategy-service contains **every** archetype across every family
   (carry, arbitrage, statistical arbitrage, volatility, market making, directional, liquidity provision) plus the risk
   engine, position monitor and P&L attribution — materially more than
   [`carveout-engineering.html`](/presentations/elysium/carveout-engineering.html) currently specifies (2 of 6 carry
   archetypes). **The two artefacts must be reconciled before both are in the client's hands.** Tracked as a todo on the
   [SLA issue doc](/plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md).
3. **The repo does not go out until strategy-service does everything the mandate needs** (operator, 2026-08-11). This is
   why the script says "once it's finished" rather than offering it immediately — and it is load-bearing, because the
   September/October readiness date is what gates the send. **Consequence to hold onto: the tangible artefact the client
   asked for is now downstream of the delivery, not a substitute for waiting.** The documents and the Q&A channel are
   what carry the interim, so they have to be good enough to do that job alone.
4. **Corollary — a completion bar now needs defining.** "Does everything we need" is not yet a checklist anywhere. Until
   it is, the send condition is unfalsifiable and the offer cannot be scheduled. First todo on the internal plan.

---

## Script

> Delivery notes: conversational, unhurried, ~100–120 seconds. Pause at each paragraph break. Do not read the bracketed
> stage directions. Nothing here needs a number in it — no dates beyond October, no fees.

Hey both — wanted to talk through the carve-out properly rather than go back and forth on email.

So the reason there isn't a standalone repo sitting ready to hand over is a deliberate design decision, and it's worth
explaining, because it's the thing that's kept us from being delayed even further — and it's a big part of why I'm
confident the infrastructure behind these strategies is best in class. We built the strategies to plug into the larger
platform. The strategy layer is agnostic about which venue, which asset class, which execution algorithm and which
custodian sits underneath it. That's why we can go from one venue to four, and from Ethereum to Solana, without
rewriting the entire strategy. The trade-off is that the strategy doesn't currently sit in its own box — it sits in a
system. So a carve-out isn't a copy. It's an extraction.

[pause]

And I think you'd understand — handing over large parts of the wider platform we've been investing in for years isn't
something I can commit to on a short timeline. That's not me being precious about it. It's that if we're going to do it,
the version worth having is a considered one, not a rushed extraction.

[pause]

I haven't costed it formally, but it's roughly three concentrated days of engineering — realistically spread across two
to three weeks once you account for everything else in flight. And what you'd get at the end of it is something that
complements the documents we've already sent you rather than replacing them.

My honest view is that those three days are better spent getting you to October. So what I'd suggest is: we push through
and deliver, we go through the whole thing together once you've got capital in it and it's live, and we start the
carve-out then, when there's actual bandwidth on both sides.

[pause]

The other thing — and I say this with respect because it's what I'd do too — you're going to point Claude or whatever
you're using at that code anyway. So a much faster loop is just: ask us the questions. Anything you want to know, we'll
answer it, and we'll use AI on our side to answer it properly and quickly. You've already got the two documents, which
cover the carve-out structure and how the platform actually works — and honestly that's a better starting point than a
code dump, because it's the same thing you'd get by asking AI to summarise fifty thousand lines, except it's accurate.
Nobody reads that much code anyway.

[pause]

And then on something tangible — once the strategy service is finished doing everything it needs to do for your mandate,
I'll send you that repository. That's the part that handles the strategy instructions, and it's the piece that
integrates most directly into your system, so it's genuinely the most relevant thing for you to look at. It's still
being completed for October, which is exactly why I'd rather you had it finished than early.

Let me know what you think — and if it's easier, just send questions over as they come up.

---

## Why each beat is there

| Beat                    | What it is doing                                                                                                                                                                                                                                                                                                 |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Agnostic-by-design open | Converts "there's no repo" from a gap into the reason we are not further delayed, and into a best-in-class claim. Pre-empts "why isn't it already separable?"                                                                                                                                                    |
| The commitment line     | Says plainly that large parts of the wider platform are not on the table, without defensiveness — and leaves the door open on timing rather than on principle. **Says "the wider platform", not "the codebase", deliberately: the next beat offers the strategy repository, and "codebase" would contradict it** |
| Costing it out loud     | Three days / two-to-three weeks. Naming a real number reads as candour and makes the deferral a scheduling call rather than a refusal                                                                                                                                                                            |
| October sequencing      | Puts their outcome first. The carve-out is delayed, not declined, and it happens once they have capital live                                                                                                                                                                                                     |
| The AI-Q&A route        | Meets them where they are instead of resisting it, and reframes the documents as the efficient artefact rather than the consolation prize                                                                                                                                                                        |
| The repo offer          | Answers "give us something tangible" without the extraction work. Operator-ruled 2026-08-11                                                                                                                                                                                                                      |
| Open-ended close        | Invites questions, which is the channel we actually want, rather than inviting a decision                                                                                                                                                                                                                        |

## Deliberately absent

- **No dates beyond October** and no fee figures — commercial conversation happens naturally, per operator instruction
  2026-08-11.
- **No support-period number.** The 30-vs-60-day inconsistency is unresolved (binding SLA says 60; every client-facing
  summary says 30); saying either number aloud creates a fourth version. See the P0 on the
  [SLA issue doc](/plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md).
- **No claim that the carve-out is hard or expensive for them.** The argument is scheduling and efficiency, not
  difficulty — a difficulty argument invites them to prove it is easy.
