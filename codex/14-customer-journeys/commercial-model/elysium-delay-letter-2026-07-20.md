---
doc_type: codex-ssot
title: Elysium — Phase 2 delay letter (2026-07-20)
summary:
  Client letter sent to Elysium (Patrick) on 2026-07-20 explaining the Phase-2 delay — new target of September
  production readiness / October formal acceptance (~3 months behind the original June target), rationale (codebase
  scale, data-platform growth, edge cases at scale), and the extra scope delivered in exchange (Deribit as a fourth
  venue, complimentary 30-day post-launch monitoring, dynamic capital allocation, per-client fund isolation).
status: current
nature: record
asset_group: [meta]
stage: [meta]
repos: []
scope: [admin]
tags: [commercial-model, elysium, delay, timeline, client-communication]
related:
  [
    /codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/ODUM_SLA_v4_2026-07-24.md,
    /codex/14-customer-journeys/commercial-model/elysium-remaining-work-appendix-2026-07-24.md,
  ]
created: 2026-07-20
authoritative_for: [exact wording of the Elysium Phase-2 delay letter sent 2026-07-20]
referenced_by: []
owner:
last_reviewed:
code_refs: []
---

> **Provenance (2026-08-10 reconciliation).** Body synced to the letter **as actually sent**, which carried operator
> edits not present in the 2026-07-20 draft: the WhatsApp opening line, "for the delay" appended to both 30-day
> monitoring-period mentions, the CEFFU/SLA paragraphs merged, and a revised closing line. The typo "WhatsApp massager"
> is recorded **verbatim as sent** — this doc is `authoritative_for` exact wording, so it is not silently corrected.
>
> **Send-date caveat.** Both attachments carry mtime 2026-07-29 18:56 and the opening line above is absent from the
> 2026-07-20 draft, so the real send was likely ~29 July. Confirming and redating this record is a tracked todo on
> [`elysium_sla_v4_support_period_and_stale_dates_2026_08_08`](/plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md).

Hi Patrick,

Following the quick WhatsApp massager the other day I wanted to send a proper update on Phase 2 rather than keep sending
bits over email.

Short version is we're behind and I'm aware. I'd rather be honest now and give you a timeline I believe in with latest
context and with rationale as to the extra benefits this delay incorporates rather than keep moving it backwards a few
weeks every month.

I'm now targeting production readiness during September, with a production shadow run towards the end of the month,
followed by a live production run if you'd like to sit in, and formal acceptance during October.

That's around three months behind the original June target communicated most recently.

Back in May I genuinely thought we were weeks away. I underestimated how much engineering sat around the strategies
rather than the strategies themselves. We've now gone through the remaining work in a structured breakdown (around 900
tracked tasks, mostly infrastructure, integration and cleanup work) and rebuilt the timeline from the bottom up, so I
have much more confidence in this date than the previous one.

**Main points**

- All research was done several months ago, we're deep into the production build phase.
- Production readiness during September, acceptance during October (your sign off).
- Most of the extra time has gone into production infrastructure rather than strategy development.
- Platform now has dynamic capital allocation across venues and strategy versions, per-client fund isolation, automated
  capital allocation on client withdrawals and deposits, 24/7 monitoring and recovery and risk management,
  kill-switches, production accounting, and an overall much stronger data platform.
- Backtesting is now being tied directly into the live execution path rather than existing separately.
- We're including Deribit as a fourth venue for you at no additional cost.
- The draft SLA includes a complimentary 30-day post-launch monitoring period for the delay.
- CEFFU is entirely your decision and we can support either route.

**Why we're later**

The biggest mistake on our side was assuming development would continue at roughly the same speed.

Early on the platform was relatively small so changes were quick. Today it's roughly a 1.4-million-line codebase across
code and configuration, spread over more than twenty services. A feature that used to touch one or two modules can now
touch dozens, which means significantly more regression testing, documentation, validation and deployment work before
anything ships.

Looking back, we underestimated how much work sat around the strategies. The strategies themselves weren't the difficult
part but building the production platform around them was.

As the platform grew we also uncovered hundreds of edge cases and integration issues that simply don't appear until
software reaches this scale. They're not the most exciting or visible problems, but solving them is exactly what makes
the platform reliable enough to run real capital.

The data platform followed the same pattern. We're now storing over 30TB of compressed canonical market data
representing many billions of records across multiple venues and providers. Migrations that used to take minutes now
take days if they're going to be done properly. This does mean adding venues and strategy iterations happens at overall
a fraction of the time. I do believe we will expand our scope as we broaden our horizons and I want us to be ready for
that and not create new issues along the way.

**Building the platform**

A lot of the extra time has gone into building infrastructure that wasn't explicitly in the original scope but which we
felt was the right way to build the platform.

We've invested heavily in CI/CD, automated testing, deployment automation, agent-assisted development, documentation
generation and code quality checks. We also spent a lot of time building orchestration around the development workflow
itself so that human engineering effort goes into reviewing and validating changes rather than manually doing repetitive
work.

More importantly, we made a conscious decision to automate much more than just trading.

The platform now automates capital allocation across venues, trading decisions, risk management, operational monitoring,
incident detection and response, documentation, code hygiene and parts of the engineering workflow itself.

We could have delivered sooner by leaving much more of that manual. The strategy itself would still have worked, but the
operational complexity of running it would have been much higher. Capital movements, monitoring, incident response,
deployments and a lot of day-to-day operational work would all have needed manual intervention.

Instead we chose to automate those recurring jobs now. It delayed delivery, but permanently reduces the cost and
complexity of running the platform and makes it much easier to scale.

None of that additional work has increased the project cost to you. We could have frozen scope and delivered something
narrower earlier, but we'd rather hand over something we'd genuinely be happy running ourselves with meaningful capital.

**What's been built**

Since June we've completed per-client fund isolation, the backbone of the Copper integration (just waiting on your test
credentials), 24/7 monitoring with automatic recovery, wallet-level kill-switches, venue circuit breakers with failover,
production P&L accounting and attribution that the strategy can dynamically learn from, and high-water-mark accounting
directly from the trade ledger. We've created dynamic venue switching, capital rebalancing on client withdrawals,
response to exchange freeze and other risk protocols all automated.

We've also validated that our historical execution and live-paper execution are deterministic. We've replayed over a
thousand real trades with zero deviation between the two, which is the foundation for backtest numbers actually meaning
something.

One feature that's made a bigger difference than we expected is dynamic capital allocation.

Different venues accept different collateral as you know, as well as having dynamic funding rate moves, so the platform
automatically switches between basis and staked basis, handles venue-specific collateral rules and moves capital as
opportunities shift between venues. In today's compressed basis environment that's proving to be one of the biggest
contributors to maintaining returns.

At this point we're well past strategy discovery. The remaining work is integration, validation, production hardening,
and rollout rather than researching new strategies or changing architecture.

**Testing**

Alongside the backtesting we've built seventeen worst-case scenarios based on real CeFi failures, DeFi failures and
general trading risk from real life history.

Things like exchange failures, oracle issues, stablecoin de-pegs, liquidation cascades, gas spikes and venue outages.

Each one gets injected directly into the production code path so we can verify the right breaker, kill-switch and alert
actually fire. Writing those tests uncovered a number of real weaknesses that we've since fixed.

On the performance numbers we've previously sent, we're still extending the testing window, adding hedge mark-to-market,
execution costs and rerunning everything against the canonical dataset.

I expect the updated numbers to come out broadly similar, possibly a little more conservative, but much better
evidenced.

Across everything we've tested we're increasingly confident the strategies generate consistent positive annualised
returns, generally ranging from single digits into double digits depending on market conditions.

**Data**

The strategies themselves run on BTC, ETH and SOL across Binance, OKX, Bybit and Deribit, plus the on-chain staking and
Ethereum gas data. The specific spot, perpetual, funding and staking history those strategies consume comes to a few
terabytes and several billion records once fully backfilled, and we're roughly half way through that now.

That sits inside a much larger shared database, now over 30TB of compressed canonical data and tens of billions of
records across every venue and provider we cover, which is exactly what makes adding new venues and instruments quicker
from here.

One thing we've spent a lot of time on is making sure missing data is properly classified. There's a big difference
between "the venue had no data", "we never requested it" and "we requested it but retrieval failed". Treat those as the
same thing and you've quietly introduced survivorship bias into every backtest.

It isn't glamorous work but it's one of the foundations everything else depends on.

**If you'd rather move faster**

Production-first has always been our default rather than the only option.

If at any point you'd rather launch earlier with less operational automation we're happy to discuss that.

We'll explain exactly what we'd simplify, what manual operational work that creates afterwards and let you decide
whether that trade-off is worth it.

Our view is that investing in automation now is the better long-term decision because it permanently reduces operational
complexity and running costs rather than simply bringing launch forward.

**Venues**

The production venues were OKX, Bybit and Binance.

As discussed before, Binance doesn't currently accept staked ETH as futures collateral, so Binance runs standard basis
while OKX and Bybit run the staked basis strategies.

As a gesture for the additional development time we're also including Deribit as a 4th venue at no additional cost,
giving access to another source of liquidity and basis opportunities.

Because the venue layer is now registry-driven, adding future venues is significantly cheaper than the original
integrations.

**CEFFU and support**

CEFFU integration is entirely your decision. If you'd like to use it for the Binance leg we'll just need the API spec,
sandbox access, sub-account model and Copper production credentials before launch.

If you'd rather not use it, that's completely fine too. I've also attached a revised draft SLA covering post-launch
support. The original agreement was intentionally lightweight, so this mainly formalises monitoring, support
expectations and deliverables.

The SLA also includes a complimentary 30-day post-launch monitoring period for the delay.

Overall we're later than either of us wanted.

Equally, I think we're delivering a materially stronger platform than we originally scoped. A lot of the engineering
we've done wasn't strictly required by the contract, but we felt it was the right investment to make before asking you
to trust the platform with real capital, and we've absorbed that work ourselves rather than treating it as additional
scope.

Most of the difficult engineering is now behind us. What's left is finishing integrations, validating everything under
production conditions, and getting it live.

Happy if you want comment or suggest edits to any of the docs and happy to jump on a call this week or next if you'd
like to go through any of it properly.

Cheers,

Ikenna Igboaka Founder & CEO, Odum Research 📩 ikenna@odum-research.com 🇬🇧 FCA Registered Firm (FRN: 975797)
