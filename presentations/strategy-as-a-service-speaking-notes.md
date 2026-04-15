# Strategy as a Service — Speaking Notes

**Deck:** Trading Platform as a Service **Audience:** Prospective platform clients (fund managers, trading teams,
fintechs) **Tone:** Direct, practical, product-focused. Not a pitch — a walkthrough of what you get. **Duration:**
~10-12 minutes **Date:** April 2026

---

## Slide 1 — Cover

**"Trading Infrastructure Without the Build"**

Odum Research. We're FCA authorised. We've built a unified trading system that covers data, research, execution,
monitoring, and compliance across five asset classes — traditional finance, crypto, decentralised finance, sports, and
prediction markets.

Our first platform client is already live at $125,000 in contract revenue, growing to $250,000-plus annually. Twelve
thousand instruments normalised across 80-plus venues — breadth you would need years to replicate. The platform is
modular: use data, research, or execution independently. Expanding is adding access, not migrating systems. And if you
leave, bespoke strategy logic is yours — the switching cost is operational familiarity, not a contract.

---

## Slide 2 — The Problem You Face

**"Building This Is Harder Than It Looks"**

If you want to run a multi-asset trading operation today, you need to integrate dozens of data vendors, build a
backtesting environment that actually matches production, connect to execution venues with proper order management,
build monitoring and risk tools, and layer compliance on top.

To do what our platform does, you'd need to integrate over 80 venues across five asset classes, 28 decentralised finance
protocols on 11 blockchains, and 65-plus sports data sources. Each with different schemas, different settlement logic,
different connectivity.

Most teams underestimate this. They start with a data feed and a backtesting notebook. Then they realise the gap between
research and live is enormous — different data paths, different risk checks, different infrastructure. Going live takes
months of engineering that has nothing to do with alpha.

Even with modern AI tools, you still need someone who understands what a good fill looks like, how to reconcile
positions across chains, and what happens when a venue goes down at 3am. AI accelerates the build. It doesn't replace
the operational experience.

The question is whether you want to spend your time building infrastructure or trading.

---

## Slide 3 — What You Get

**"One Platform, Your Scope"**

Our platform is modular. You choose how deep you go.

The platform runs 22 microservices with over 24,500 automated tests. It is production infrastructure — not a demo, not a
prototype. Our first platform client is already using it for live decentralised finance strategies. You enter at any
layer and expand over time.

Five connected layers: instruments and data, research and modelling, decision and strategy, execution and control,
governance and reporting. You can enter at any layer and expand over time.

---

## Slide 4 — Engagement Levels

**"Start Where It Fits"**

There are five ways to engage, depending on what you need and how much of the stack you want to own.

**Data only.** Normalised feeds across all five asset classes. Twelve thousand live instruments. One schema regardless
of venue or asset class. You build everything else yourself. We never see your signals.

**Data plus research.** Everything above, plus access to our backtesting and simulation environment. Feature
engineering, machine learning pipelines, strategy simulation. You validate ideas on our infrastructure, then execute
wherever you want.

**Data, research, plus execution.** The research-to-live handoff is where most platforms break down. On ours, promoting
a strategy from backtest to live is a configuration change — same data pipeline, same features, same risk controls. You
also get access to our execution algorithms across all connected venues.

**Full platform.** The complete trading operating layer. Data, research, execution, monitoring, risk, client reporting,
compliance tools. You run your operation on our infrastructure. Your strategies, your risk parameters, your commercial
terms.

**Bespoke strategy development.** You want us to build specific strategies for you — decentralised finance yield,
traditional finance quant, sports prediction, whatever fits your mandate. We develop on the same infrastructure, hand
over the running strategy, and you operate it. Commercial terms are bespoke — typically a development fee plus an
ongoing retainer or performance share.

---

## Slide 5 — How You Plug In

**"How You Plug In"**

There are three ways to connect to the platform, depending on where you are in your own build.

First scenario: you already have signals. You have built your own research, you generate your own trading signals, and
you just need execution. You send signals to us via API. We execute across 80-plus venues with advanced algorithms —
time-weighted, volume-weighted, smart order routing, optimal execution. You get best execution reporting — slippage
analysis, fill quality, venue breakdown. We charge alpha-based fees on execution outperformance. You never touch our
research layer. Your intellectual property stays completely yours.

Second scenario: you want to build strategies on our infrastructure. You use our data, our feature library, our
backtesting environment to develop your own strategies. When you are ready, you promote to live — same code, same data,
same risk controls. No rewrite. That backtest-to-live cohesion is the core value — it would take you eighteen months to
build it yourself. You can use our frontend or build your own — the backend API is the same either way.

Third scenario: you want us to build strategies for you. You tell us what you want — decentralised finance yield, crypto
long/short, sports prediction, whatever fits your mandate. We build it, test it on our own capital first, then deploy it
for you. Either of us can operate it — through our frontend or through the backend API. Bespoke commercial terms. Built
by a team with decades of institutional trading experience. Nothing ships that we would not trust with our own money.

Across all three: the frontend can be ours or yours. The platform is API-first. You can use the full web interface,
connect via API with your own tools, or combine both. The backend infrastructure is the same regardless.

---

## Slide 6 — Coverage Breadth

**"What the Platform Covers"**

This is the coverage matrix. Every cell runs on shared infrastructure.

Traditional finance — CME Group, ICE, CBOE, NASDAQ, NYSE. Futures, options, equities. Full execution algorithm suite.

Centralised crypto — Binance, OKX, Bybit, Deribit, Coinbase, Hyperliquid, and more. Spot, perpetuals, options. Tick
data, orderbook, liquidations, funding rates.

Decentralised finance — 28 protocols across 11 blockchains. Uniswap, Aave, Morpho, Curve, Balancer, and chain-dominant
protocols on Solana, Arbitrum, Base, Optimism. Lending rates, pool data, gas fees. On-chain execution connectors.

Sports — 102 leagues, over 40,000 fixtures per year. Odds from 65-plus sources. Machine learning prediction pipeline.
Cross-bookmaker routing.

Prediction markets — Polymarket, Kalshi, and others. Binary and multi-outcome pricing. Cross-market arbitrage detection.

You don't need to use all of this. But it's there when you need it, and it all runs on one normalised schema.

---

## Slide 6 — Strategy Families Available

**"The Spectrum"**

If you engage at the bespoke strategy development level, or if you want to understand what kinds of strategies the
platform supports, here's the spectrum.

Low-risk, high-capacity: decentralised finance lending and stablecoin yield. Three to twelve percent annual returns.
Under one percent drawdown. Can absorb fifty to a hundred million-plus. Suitable for conservative mandates or as a base
layer.

Medium-risk, medium-capacity: basis trades, crypto long/short, traditional finance directional. Ten to thirty percent
returns. Five to twenty million capacity per strategy. The core of most multi-strategy portfolios.

Higher-risk, capacity-constrained: leveraged decentralised finance yield, concentrated liquidity provision. Twenty to
fifty percent returns. Five million per pool. Suitable for smaller, more aggressive allocations.

Sports and prediction markets: machine learning prediction, cross-bookmaker arbitrage. Fifty percent-plus returns.
Capacity is tighter — typically under a million. A specialist allocation.

The infrastructure is the same across all of these. The configuration changes, not the platform.

---

## Slide 6 — Strategies Available on the Platform

**"Strategies Available on the Platform"**

This is the catalog of what you can access or have us build for you. Thirty-five strategies across five asset classes.

For decentralised finance: yield and lending strategies across Aave, Ethena, Kamino, and multiple chains. Basis trades —
Ethereum, Bitcoin, Solana, L2 chains. Recursive staked basis for amplified yield. Concentrated liquidity provision on
Uniswap and Raydium. Cross-chain yield arbitrage and rebalancing.

For centralised crypto: momentum, mean reversion, cross-exchange arbitrage, statistical arbitrage, and exchange market
making.

For traditional finance: machine learning directional on equities, futures, and FX. Momentum. Options market making on
Deribit and CME. Relative volatility and volatility surface strategies.

For sports: machine learning prediction, halftime prediction, cross-bookmaker arbitrage, value betting, and exchange
market making on Betfair and Smarkets.

For prediction markets: cross-venue arbitrage between Polymarket, Kalshi, and traditional bookmakers.

You do not need to use all of these. This is the library. Bespoke builds can combine any of these or create entirely new
strategies on the same infrastructure.

---

## Slide 7 — Backtest to Live

**"The Gap That Doesn't Exist Here"**

This is the single most important thing to understand about the platform.

On most systems, backtesting and live trading are separate environments. You validate a strategy in one, then spend
months rebuilding it in another. Different data feeds, different feature calculations, different risk checks, different
code. Things break in translation. Teams spend more time on the handoff than on the research.

On our platform, backtest and live run on the same infrastructure. Same data pipeline. Same feature calculations. Same
risk controls. Same code. Promoting a strategy from backtest to live is a configuration change.

That means when you validate something in research, you know it will behave the same way in production. No translation
layer. No rewrite. No months of engineering.

This is also what makes the platform sticky — once you've built up validation history, data history, and operational
familiarity inside the system, recreating that elsewhere is expensive. We're transparent about that. The lock-in is
earned through value, not through contracts.

---

## Slide 8 — Why Not Build It Yourself?

**"The Honest Comparison"**

You could build this yourself. Here's what that looks like.

Integrating 80-plus venues across five asset classes — each with different schemas, different settlement, different
connectivity. Building a normalised schema layer. Building a backtesting environment that genuinely matches production.
Building execution infrastructure with proper order management. Building monitoring, risk, reconciliation, and
compliance tools. Connecting it all together so that a strategy can move from research to live without a rewrite.

With a strong team and modern AI tools, you could probably get a version of this running in 18 to 24 months. We've been
building for three years with a team that has traded all five asset classes.

The question is not whether you can build it. The question is whether building infrastructure is the best use of your
time and capital, or whether you'd rather spend that time on research, strategy development, and trading.

We've already integrated the venues, normalised the schemas, built the execution layer, built the monitoring tools, and
proved it with our own capital. You can access all of that through a subscription or a bespoke engagement, and start
trading in weeks rather than years.

---

## Slide 9 — Why Not Just Use AI?

**"What AI Can and Can't Do"**

AI has made it much faster to build software. We use it extensively ourselves. But there's a gap between building a
trading system and operating one.

AI can help you write code, build interfaces, and integrate APIs. What it can't do — yet — is:

Know what a good fill looks like across different venue microstructures. Reconcile positions across multiple blockchains
when a bridge fails. Handle a venue outage at 3am when positions are open. Debug a drawdown under pressure when the
cause isn't in the code but in a market microstructure change. Make the judgement call on whether a strategy is
underperforming because the market regime changed or because something is broken.

These are operational skills that compound over years. Our team had decades of experience at large trading institutions
making money before Odum even existed. We've personally traded options, delta one, high frequency, and medium frequency
across traditional finance, crypto, decentralised finance, and sports. That experience shapes every design decision in
the system.

AI is a force multiplier. It multiplies the judgement of the person directing it. If the judgement isn't there, the
multiplication doesn't help.

We use AI heavily — and believe anyone should. But the system works because there are experienced humans making the
critical decisions.

---

<!-- CRITICAL SLIDE — This answers the recurring concern about working with a firm that also trades. -->

## Slide 10 — Your Alpha Stays Yours

**"We Don't Need Your Edge"**

The most common concern: why work with a firm that also trades?

The answer is simple. We don't need your alpha. We have our own.

If you use our data — we never see your signals. If you use our execution — we route and fill without knowing the logic
behind your orders. If you use our research environment — you take your results and execute wherever you want.

Even on the full platform or bespoke strategy engagements — we will never front-run you and we will never build
strategies that overlap with what we've built for you. We make bespoke commercial deals. Your strategy is yours.

We partition our business clearly. Internal strategies stay internal — proprietary, not shared. Client strategies are
separate — built to your requirements, operated by you. We have enough strategy families across enough asset classes
that there's no conflict.

The trust is built on three things. First platform client already live and growing — this is operational, not
theoretical. 22 microservices, 24,500-plus automated tests — institutional-grade reliability before your first trade.
And modular access — you can use data, research, or execution independently without exposing your edge.

The infrastructure is shared. The alpha is not. That's the design.

---

## Slide 11 — Who Uses It Today

**"Proof Points"**

This is not a pitch from zero. The platform is live and generating revenue.

Investment management: $7.5 million under management across two mandates. Crypto mean reversion returning over thirty
percent annualised. Bitcoin fund of funds.

First platform client: a decentralised finance fund manager who bought the full end-to-end system. $125,000 in contract
revenue — seventy-five percent already received, paid in tranches. We're developing three decentralised finance
strategies yielding five to twenty percent annualised, giving his clients access to different risk profiles. Expected to
grow to $250,000-plus in annual revenue with an ongoing retainer.

Regulatory umbrella: one regulatory coverage client live under our FCA authorisation, three more in conversation.

The platform you'd be using is the same one running real capital and serving real clients today. It's not a demo. It's
not a prototype. It's production infrastructure.

---

## Slide 11 — How It Works Commercially

**"Commercial Terms"**

We work on annual contracts, scoped to what you need.

Platform access starts from ten thousand a month on an annual contract — that covers the layers and asset classes
relevant to your operation, plus ongoing platform updates, support, and compliance tooling. The scope is bespoke, so the
exact number depends on the conversation.

To put that in context: an in-house team to build and operate equivalent infrastructure would be five to ten engineers
at $150,000 to $250,000 each, plus twelve to eighteen months before you can trade. Our platform gets you live in weeks
at a fraction of the cost.

For bespoke strategy builds — where we develop specific strategies to your requirements — the model is a development fee
plus an ongoing retainer or performance share. We build, you operate. Terms are negotiated per engagement because
complexity varies.

You can start with a narrower scope — data access, research — and expand over time. Same infrastructure throughout, so
expanding is adding access, not migrating systems.

All engagements are 12-month annual contracts. We don't do off-the-shelf pricing because no two engagements are the
same. The first conversation is always about what you need and what scope makes sense.

---

## Slide 13 — Next Steps

**"How to Start"**

If this is interesting, the next step is a scoping call.

We map your infrastructure gaps — which asset classes, what you have today, where the gaps are — and scope the
engagement to exactly what you need.

From there, we set up a hands-on trial on the data and research layers. No commitment required. You evaluate the
normalisation quality, coverage depth, and backtesting environment with your own use cases before expanding to anything
broader.

Data access is live in days. Research environment in days. Execution integration in weeks. Full platform or bespoke
build scoped per engagement.

Contact: ikenna@odum-research.com Odum Research Ltd | FCA 975797 | odum-research.com

---

## Slide 14 — Demo

**"See It Live"**

Same live platform. I can walk you through whatever's most relevant to your setup.

- Dashboard — platform overview, positions, returns, risk
- Instruments — 12,000+ instruments, browse by asset class and venue
- Strategy research — backtests, comparison, machine learning analysis
- Trading — live positions, orders, execution quality
- Client reporting — executive dashboard, investment book of records
- Risk and scenarios — stress testing, historical replay
