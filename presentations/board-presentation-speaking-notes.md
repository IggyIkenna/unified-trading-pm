# Board Presentation — Speaking Notes

**Deck:** One Unified Trading System **Audience:** Strategic Advisors **Duration:** 5 minutes (turbo) / 10 minutes
(full) **Date:** April 2026

---

## Slide 1 — Cover

**"One Unified Trading System"**

We're FCA authorised. We've been around for three years and we've built a unified trading system. One platform covering
data, research, execution, monitoring, and compliance across five asset classes - not just traditional finance, but also
crypto, decentralised finance, sports, and even prediction markets.

Externally we provide regulatory coverage for those without licences. We also manage investments currently over $7m for
two strategy funds — one is a crypto strategy returning over 30% annualised, and another Bitcoin fund of funds strategy
returning over 8% annualised. We expanded our services to incorporate end to end trading infrastructure for small to
medium sized teams looking to accelerate their entry into trading.

We trust the strategies with our own capital. When you use our platform, you are using the same infrastructure we use
for our own capital. That alignment is deliberate, and everything I'm about to show you runs on that foundation.

---

<!-- CRITICAL SLIDE — If they only listen to one slide before this section, make it this one. This is where the problem lands. The backtest-to-live gap is the single insight that makes the platform sticky and differentiates us from a dashboard company. -->

## Slide 2 — The Problem

**"The Market Is Still Stitched Together"**

The problem is fragmentation. To do what we do, a firm would need to integrate over 80 venues across five asset classes,
28 decentralised finance protocols on 11 blockchains, and 65-plus sports data sources — each with different schemas,
different settlement logic, different connectivity. Most firms stitch together four or five vendors for data, sometimes
build their own, sometimes use other vendors that don't cover everything they need so they have to build custom
solutions anyway. Then compliance is bolted on at the end. Every boundary creates reconciliation overhead, operational
risk, and slows down time-to-market.

We replaced all of that with one codebase, one language, one configuration structure, one schema normalisation layer,
one deployment infrastructure, and one web-based interface.

But the most expensive gap in a stitched-together setup is between research and production. On most platforms, a
strategy that works in backtest requires a significant rewrite to go live — different data feeds, different code paths,
different risk checks. Poor execution assumptions and data quality mean things break in that translation. Teams spend
months on it and still get it wrong.

On our platform, promoting a strategy from backtest to live is a configuration change. Same data pipeline, same feature
calculations, same risk controls, same code. We've materially reduced that gap by keeping both on shared infrastructure.
That continuity creates real stickiness, because once you've validated a strategy in our environment, recreating that
validation elsewhere becomes expensive.

---

## Slide 3 — The Solution

**"One System, Five Connected Layers"**

Our answer is five connected layers, not five separate products.

First: instruments and data — we discover, normalise, and validate reference data and market data across all five asset
classes. Second: research and modelling — feature engineering, machine learning, backtesting, simulation. Third:
decision and strategy — signal generation, position sizing, risk assessment. Fourth: execution and control — order
routing, fill management, real-time monitoring. Fifth: governance and reporting — audit trails, regulatory reporting,
compliance controls.

What makes this different from a diagram is that these layers genuinely share infrastructure underneath. The instrument
layer that tells our decentralised finance lending strategy which Aave markets exist is the same layer that tells our
traditional finance strategy which CME futures are listed today. The feature pipeline that computes volatility for
crypto is the one that computes odds movement features for sports. That shared foundation is what makes the cross-asset
capability real rather than aspirational.

---

## Slide 4 — Why This Is Hard to Replicate

**"Structural Differentiation"**

Three structural points.

First: a shared instrument and schema layer. Twelve thousand live instruments across five asset classes, all normalised
into one canonical model. Every strategy, every service, every interaction touches the same instrument layer. That's an
architectural decision we made early and it compounds over time.

Second: we built this for ourselves first, and now we share it. Seven and a half million of real capital runs through
the same infrastructure you would use. We have clients for every service we offer — investment management, regulatory
coverage, and the trading platform. Nothing we deploy for a client goes through without the same vetting we apply to our
own capital. If anything degrades, our returns feel it before yours do.

Third: a connected operating layer across workflows. Data, research, execution, monitoring, governance — these are not
bolted together. When we integrate a new venue, the benefit propagates rather than sitting in a silo. When we add a new
strategy, every user can access it. And we will never run a strategy that overlaps with what we've built for you — your
strategies are separate from ours.

Rebuilding this from scratch would be a significant multi-year, multi-team effort. We operate it with a small team
because AI-assisted workflows handle the majority of routine operations, with human approval gates at critical
decisions.

---

## Slide 5 — Breadth Without Fragmentation

**"The Coverage Matrix"**

Take a moment to scan this. Rows are the five asset classes. Columns are the five capability layers I just described.

The point is not the list of markets. The point is that this coverage sits on a common operating layer rather than
separate stacks by asset class. We haven't seen another provider that spans these five domains on shared infrastructure.
Most cover one or two well.

If something in this matrix is relevant to someone you work with, I'd rather have a focused conversation about that than
try to cover everything now.

---

## Slide 6 — Strategy Families

**"Risk, Return & Capacity"**

We run 35 strategies across five families, but the individual strategies aren't the point for this conversation. The
point is the spectrum.

At one end: low-risk, high-capacity strategies — decentralised finance lending, stablecoin yield. These can absorb
serious capital. At the other end: higher-return strategies with tighter capacity constraints. In between: basis trades,
crypto momentum, traditional finance directional.

Capacity is the dimension most people overlook. A strategy returning forty percent that can only absorb five million is
a very different proposition from one returning eight percent that takes a hundred million. For investment management,
this shapes fee structures — we charge twenty to forty percent of performance depending on the strategy, with
lower-yielding strategies carrying lower fees.

The detail is available if useful. What matters here is that the full range runs on a common foundation.

---

<!-- CRITICAL SLIDE — This is the credibility slide. If an advisor remembers nothing else from the entire presentation, they need to walk away knowing: real money, real returns, first platform sold, pipeline active. Everything else is context for this. -->

## Slide 7 — What Is Live Today

**"What Is Real"**

I want to be very clear about what's real versus what's ready.

Live and revenue-generating. Four million under management in a crypto mean reversion strategy — over thirty percent
annualised return with one year of live track record. Three point three million currently at high watermark. That's on
Binance and OKX, running through our infrastructure daily. Separately, three and a half million in a Bitcoin fund of
funds with five years of track record. One regulatory coverage client fully onboarded under our FCA authorisation. And
our first trading platform sale — $125,000 in contract revenue — seventy-five percent already received, paid in tranches
from a decentralised finance client who has bought the full end-to-end system. We're developing three decentralised
finance strategies yielding five to twenty percent annualised, giving his clients access to different risk profiles. We
expect this to grow to $250,000-plus in annual revenue with an ongoing retainer.

In active commercial pipeline. Three additional regulatory coverage prospects in conversation — firms that need
regulatory coverage and are evaluating us. A memorandum of understanding for execution services with an institutional
counterparty. And a funding development focused on options on India Exchange — delta one and arbitrage.

Built and launch-ready. The broader platform product with the interface across all five asset classes. Data provision
with normalised feeds. Backtesting infrastructure with the backtest-to-live continuity I described. Thirty-five
strategies across five families, thirty of which are code-complete. Nine execution algorithms.

I want to be honest about the distinction between 'built' and 'sold.' The platform is production-grade. We have two
investment management mandates, one regulatory coverage client, and one platform sale generating revenue today. The
broader product is ready for additional deployments. That is exactly why we are here.

Across all three services, the remaining constraint is more commercial focus and sequencing than core engineering
build-out.

---

<!-- CRITICAL SLIDE — This is the "what do you actually sell" slide. If they can't explain your business in one sentence after leaving, the meeting failed. "Three commercial wrappers around one underlying system" is that sentence. -->

## Slide 8 — Three Services

**"Three Commercial Wrappers, One System"**

The way to think about this is: three commercial wrappers around one underlying system.

First: Trading Platform as a Service. You get bespoke access — it could be just normalised data feeds, or data plus
backtesting, or the full trading platform with execution and monitoring. Subscription model, scoped to what you need.

Second: Investment Management. We run capital. Twenty to forty percent performance fee, strategy-dependent —
lower-yielding strategies carry lower fees. Seven and a half million under management today across two mandates.

Third: Regulatory Umbrella. FCA regulatory coverage under our authorisation. Compliance supervision, money laundering
reporting officer coverage, best execution reporting. One onboarded, three more in conversation.

A regulatory coverage client who needs execution uses the same algorithms. An investment management mandate that
outgrows managed capital can graduate to platform access. The commercial relationship evolves — what's underneath stays
the same.

One thing to be clear about: everything we build for a client goes through the same vetting we apply to our own capital.
We don't ship anything we wouldn't trust with our own money. And we don't build strategies that overlap with what a
client is running — your strategies stay separate from ours.

---

## Slide 9 — The Flywheel

**"Why One Sale Leads to Others"**

The land-and-expand logic follows naturally from the architecture.

You enter at data access. You see the normalisation quality and coverage, so you start using the research environment.
You validate a strategy — and here's the critical moment: going live is not a rewrite. It's a configuration change. Same
data pipeline, same features, same risk controls. That conversion from research to live is where most platforms lose
people, and it's where we have the strongest continuity.

From there, you can deepen in different directions. A live trading user may need regulatory coverage. A platform user
may want us to run a sleeve of capital directly. A regulatory coverage client may expand the scope of what they do under
our umbrella.

Every step deepens the engagement because you're already inside the platform. The switching cost is the accumulated
validation, data history, and operational familiarity you've built up over time.

---

## Slide 10 — The Ask

**"What Fits Your Network"**

Everything I've shown is either live today or close enough that the next conversation can be practical rather than
theoretical.

Investment management — running today on current strategies, with additional strategies across new asset classes coming
through. The regulatory umbrella is live now. The trading platform has its first sale completed — $125,000 in contract
revenue — seventy-five percent already received, paid in tranches — and is ready for broader deployment.

So the question I'd put to you is: which of these three fits the people you know? If someone in your network allocates
to alternative strategies, what would they need from us? If someone needs infrastructure, would they want a data-only
entry point or a full platform walkthrough? If someone needs regulatory coverage, what's their main concern?

I'd rather tailor what comes next to what's actually relevant in your network than hand over a generic pack. What
resonated?

---

## Slide 11 — Demo

**"Platform Demo"**

This is the live system. I can click into any of these sections and walk you through whatever is most interesting. What
would you like to see?
