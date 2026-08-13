---
doc_type: codex-ssot
title: Elysium/POD — carve-out deferral message (2026-08-11)
summary: >-
  The message sent to both Elysium contacts explaining why the code carve-out is deferred past the October delivery,
  what a beta carve-out would actually cost in engineering time, the AI-assisted Q&A channel offered in its place, and
  the commitment to send the strategy-service repository in full once its code lands. Records the operator's decisions
  of 2026-08-11 on the deferral, the scope of the code offer, and the Copper/ClearLoop wording.
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
tags: [commercial-model, elysium, client-communication, carve-out, custody]
related:
  [
    /codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/elysium-delay-letter-2026-07-20.md,
    /codex/14-customer-journeys/commercial-model/carveout-engineering.html,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
  ]
created: 2026-08-11
last_updated: "2026-08-11"
code_refs: []
---

# Carve-out deferral — message to Elysium

**Audience:** both Elysium contacts. **Purpose:** defer the code carve-out past the October delivery without it reading
as a refusal, and replace it with two things they can use immediately — an AI-assisted Q&A channel and the
strategy-service repository in full.

**Operator decisions recorded 2026-08-11 (interactive):**

1. **Defer the carve-out.** A sensible _beta_ carve-out is ~1 week of concentrated engineering plus operator time, in
   practice spread over 2–3 weeks, and it delays the project by at least that week of human time. A production-grade
   standalone carve-out is longer again. That time goes into the October delivery instead.
2. **Send the strategy-service repository in full**, once its code lands. Ruled after the disclosure trade-off was put
   to the operator: the repository contains **every** archetype across every family — carry and yield, structural
   arbitrage, statistical arbitrage, volatility, market making, ML- and rules-directional, event-driven and portfolio —
   plus the risk engine, position monitor and P&L attribution, which is broader than the package
   [`carveout-engineering.html`](/codex/14-customer-journeys/commercial-model/carveout-engineering.html) specifies for a
   carve-out (that package names two carry archetypes). **Reconciled by distinguishing inspection from transfer** — see
   decision 4.
   <!-- Family list corrected 2026-08-12: previously named a "liquidity provision" family that StrategyFamily does not
   have. The same invention was fixed in strategy-service-deep-dive.html on 2026-08-11 but this record was missed, so the
   fix was half-applied for a day. The archetype TOTAL was also removed rather than corrected from 6 to 7 (the carry
   package declares seven ARCHETYPE values, the seventh being CARRY_FUNDING_DISPERSION) — a raw total re-rots on the next
   archetype added, whereas "names two" is a property of the carve-out spec and is stable. -->
3. **Timing: the strategy-service _code_ completes this week; the data, and the live/batch deployment, do not.** The
   message must be precise about which thing is finished, or "next week" reads as a claim that the whole mandate is
   done. The completion bar in the plan is therefore scoped to **code** completeness, not mandate readiness.
4. **Copper _is_ ClearLoop, for our purposes.** ClearLoop is Copper's service: we post collateral into Copper custody
   and ClearLoop mirrors it onto the exchange so it can be traded without leaving custody. **Our code instructs
   Copper**; there is no ClearLoop-specific code path, and `rg clearloop` across all 26 repositories returns zero source
   hits. The message therefore describes the Copper integration and names ClearLoop as Copper's mirroring mechanism —
   never as something we built. An engineer who greps the repository they are about to receive will find `copper.py`,
   and the wording has to survive that.
5. **TWO custodians, both named explicitly (operator ruling 2026-08-12).** Elysium need **Ceffu for Binance**, so the
   single-custodian framing above is no longer the whole picture and the message now names both. The operator chose
   explicit naming over a generic "qualified custodian" phrasing for the same reason decision 4 exists: **an engineer
   reading the repository will find `ceffu.py` next to `copper.py`**, so the wording has to survive that too. Ceffu's
   off-exchange settlement plays the role for Binance that ClearLoop plays for Copper's venues. What the message must
   NOT imply is that we built either mirroring mechanism, or that a cross-custodian move is free — it unmirrors, settles
   on-chain between the custodians, and re-mirrors. Routing detail belongs in
   [transfer-architecture](/codex/04-architecture/transfer-architecture.md), not in a client message.

---

## Message

> Send as written. Three things are load-bearing and should not be softened in a re-edit: it says the **code** completes
> this week (not the data or the deployment); it credits **Copper** with ClearLoop rather than implying we built it; and
> it names **both** custodians, since Ceffu carries the Binance leg and `ceffu.py` is in the repository being sent.

So, I've spent a few hours today actually starting to work through what the carve-out would involve rather than just
talking about it conceptually.

The main thing is there isn't a standalone carved-out repo, or set of repos, sitting there ready to send you right now.
And the reason for that is actually a deliberate design decision. It's also a big part of why I'm confident the
infrastructure behind these strategies is as strong as it is.

We built the strategies to plug into the wider platform. The strategy layer is largely agnostic to which venue it's
trading on, which asset class it's trading, which execution algorithm sits underneath it, which custodian is being used,
and so on. That's why we can move from one venue to four venues, or Ethereum to Solana, without rewriting the strategy
from scratch. It's also why we can backtest with confidence and then promote effectively the same strategy logic and
data flow into production.

The trade-off is that the strategy doesn't currently sit in its own independent box. It sits inside a system alongside a
lot of the rest of our IP stack, including strategy-agnostic execution algos. So a carve-out isn't really a copy. It's
an extraction.

And I think you'd understand that handing over large parts of the wider platform we've spent years building isn't
something I can just commit to doing on a short timeline. That's not me being precious about the code. It's more that,
if we're going to do a carve-out, the version worth having is a proper one rather than us rushing an extraction
together. I do say that with evidence, having already spent a few hours today starting to execute what was, frankly,
turning into a pretty half-baked carve-out plan.

I haven't formally costed the time, but my sense is that it's probably around a week of concentrated engineering and my
own time to produce a sensible beta carve-out. In reality that probably gets spread over two or three weeks once you
account for everything else currently in flight, and it delays the project by at least that week of human time. And
that's for a beta. A genuinely production-grade standalone carve-out would obviously take longer again.

Essentially what you'd get at the end of that exercise would complement the documentation we're already giving you. It
wouldn't replace it. And my view is that those engineering days are much better spent right now getting you to October.

So what I'd suggest is: we push through, finish the strategy, get it live and get capital into it. We then go through
the whole system together once it's actually running, and start the broader carve-out at that point, when there's
genuine bandwidth on both sides.

I'm not against doing the carve-out. I just don't think it's efficient to make it another pre-delivery workstream.

The other point — and I say this because you've already mentioned that you're going to point Claude or whichever LLM
you're using at the code anyway — is that there's actually a much faster feedback loop available to us in the meantime.
If you weren't using something like that, it would realistically take weeks just to get a base-level understanding of a
codebase of this size and how all of the services interact.

So rather than us spending a week extracting code so that you can then spend time getting an agent to reconstruct the
context around it, just send us the questions. Anything you want to understand about how a particular component works,
how a flow works, where something is implemented, what assumptions are made, or how services interact — ask us.

We can use an agent on our side which has full context of the wider codebase and answer those questions directly and
accurately. You've also already got the documents covering the carve-out structure and the wider platform architecture.

Honestly, that's a much better starting point than a raw code dump. A lot of what you'd initially be doing with Claude
is getting it to summarise tens of thousands of lines and reconstruct the architecture anyway. We can effectively give
you that understanding directly, except with the full system context intact.

Then, on something much more tangible: the strategy service's code should be complete on our side this week, and once
it's through that final refinement I'm happy to send you that repository in full. That's the service that handles the
actual strategy instructions and decision flow.

It's also the component that sits closest to your side of the system. It's what emits the instructions that drive
collateral and capital movements — including the custody legs. We work with two custodians: collateral posted into
Copper custody is mirrored onto the exchange by Copper's ClearLoop, and for Binance the equivalent runs through Ceffu,
so in both cases the collateral is traded against without leaving custody. The strategy layer doesn't distinguish
between them — it emits one instruction and the custody configuration determines the route. And it's what most directly
answers the questions around how the strategy itself actually works.

So from your perspective, it's genuinely the most relevant repository to inspect. I'll have that for you next week.

To be precise about what "complete" means there: I'm talking about the code. The data pipeline work and the live and
batch deployment continue through to October alongside the broader testing. That's exactly why I'd rather give you the
finished code than send you an earlier snapshot now. But it's already mature enough that, once you have it, you'll be
able to concretely understand the flows and how the strategy operates.

So overall, I don't want to fight giving you information or visibility before delivery. Quite the opposite.

We're giving you the code that most directly answers the questions you're trying to answer, we'll give you access to
effectively interrogate the wider system through us in the meantime, and we're sequencing the larger extraction at the
point where doing it properly doesn't actively delay the project.

That feels like the sensible balance to me. Let me know what you think, and honestly, if it's easier, just start firing
questions over as they come up.

---

## Changes made to the operator's draft, and why

| Change                                                                                                                         | Reason                                                                                                                                                                                                                                                                                         |
| ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| "ClearLoop instructions and the downstream flows around that" → the Copper leg, with ClearLoop as Copper's mirroring mechanism | **The draft's wording claims something the code does not contain.** `rg clearloop` across all 26 repositories returns **zero source hits**; what exists is `execution_service/custody/copper.py`. An engineer greps for a named integration; the corrected wording is accurate and survives it |
| Added an explicit paragraph defining "complete" as **the code**, with data and live/batch deployment continuing to October     | The draft said "complete this week" and "still going through its final refinement for October" in the same message, which reads as a contradiction. Naming which thing is finished removes it and protects the "next week" commitment                                                          |
| "the two documents" → "the documents"                                                                                          | A third document (the strategy-service deep dive) is being prepared; a hard count goes stale the moment it ships                                                                                                                                                                               |
| "an delays the project" → "and it delays the project"; "strategy agnostic" → "strategy-agnostic"                               | Typographical                                                                                                                                                                                                                                                                                  |
| Kept: the half-baked-plan admission, the week estimate, the "not being precious" line, the closing balance                     | These are the parts that make it read as candour rather than positioning. Not touched                                                                                                                                                                                                          |

## Deliberately absent

- **No support-period number.** Standardised at **30 days** internally on 2026-08-11, but the copy already in the
  client's hands states sixty (60) calendar days in its binding §3 under a "substantive provisions prevail" clause, so
  the entitlement is still 60 until reissued. Saying either number in this message would create a fourth version.
- **No fee figures and no dates beyond October / "next week"** — the commercial conversation happens naturally.
- **No claim that a carve-out is hard for _them_.** The argument is sequencing and efficiency. A difficulty argument
  invites them to prove it is easy.
