# Strategy as a Service — Slide Layout Specification

**Deck:** Trading Platform as a Service **Target:** New route at `/investor-relations/strategy-service-presentation`
**Slides:** 14 **Date:** April 2026

---

## Design Language

Same as board presentation — navy + gold palette, Inter font, Framer Motion transitions, FCA badge header, keyboard nav.

---

## Slide 1 — Cover

**Type:** `cover` (reuse)

```ts
{
  id: 1,
  type: "cover",
  title: "Trading Infrastructure Without the Build",
  subtitle: "Institutional-grade trading infrastructure across five asset classes. Built for our own capital. Available to your team.",
  tagline: "FCA Authorised",
  stats: [
    { value: "5", label: "Asset Classes" },
    { value: "12,000+", label: "Live Instruments" },
    { value: "$7.5M", label: "Our Own Capital" },
    { value: "Weeks", label: "To Go Live" },
  ],
}
```

---

## Slide 2 — The Problem You Face

**Type:** `doctrine` (reuse)

```ts
{
  id: 2,
  type: "doctrine",
  title: "Building This Is Harder Than It Looks",
  subtitle: "To replicate what our platform provides, you would need to integrate 80+ venues across 5 asset classes, 28 decentralised finance protocols on 11 blockchains, and 65+ sports data sources \u2014 each with different schemas, settlement logic, and connectivity.",
  points: [
    {
      problem: "Data integration: 80+ venues, 5 asset classes, dozens of schemas",
      solution: "One normalised schema \u2014 already built, tested, and running",
    },
    {
      problem: "Research to live: backtests that don\u2019t match production",
      solution: "Same code path from backtest to live \u2014 configuration change, not rewrite",
    },
    {
      problem: "Execution: different APIs, different order types, different settlement",
      solution: "One execution layer across all venues, all asset classes",
    },
    {
      problem: "18-24 months of build time before you can trade",
      solution: "Live on our platform in weeks, not years",
    },
  ],
  differentiators: [
    "We\u2019ve been building for three years with a team that has traded all five asset classes",
    "The platform runs $7.5M of our own capital \u2014 this is not a prototype",
    "The question is whether building infrastructure is the best use of your time",
  ],
  conclusion: "You can build it yourself. Or you can start trading in weeks.",
}
```

---

## Slide 3 — What You Get

**Type:** `lifecycle-new` (reuse)

```ts
{
  id: 3,
  type: "lifecycle-new",
  title: "One Platform, Your Scope",
  subtitle: "The same system powering our investment management business \u2014 available to you. Enter at any layer, expand over time.",
  stages: [
    { name: "Instruments & Data", desc: "Discover, normalise, validate" },
    { name: "Research & Modelling", desc: "Features, ML, simulate" },
    { name: "Decision & Strategy", desc: "Signals, sizing, risk" },
    { name: "Execution & Control", desc: "Route, fill, monitor" },
    { name: "Governance & Reporting", desc: "Audit, comply, report" },
  ],
}
```

---

## Slide 4 — Engagement Levels

**Type:** `packaging` (reuse — 5 cards)

```ts
{
  id: 4,
  type: "packaging",
  title: "Start Where It Fits",
  subtitle: "Five engagement levels. You choose how deep you go.",
  services: [
    {
      name: "Data Only",
      stages: ["Instruments & Data"],
      model: "Subscription",
      desc: "Normalised feeds across all five asset classes. 12,000+ instruments. We never see your signals.",
    },
    {
      name: "Data + Research",
      stages: ["Instruments & Data", "Research"],
      model: "Subscription + compute",
      desc: "Everything above, plus backtesting and simulation. Feature engineering, machine learning pipelines. Execute wherever you want.",
    },
    {
      name: "Data + Research + Execution",
      stages: ["Instruments & Data", "Research", "Execution"],
      model: "Subscription + per-trade",
      desc: "Backtest to live is a config change \u2014 same data, same features, same risk controls. Plus execution algorithms across all venues.",
    },
    {
      name: "Full Platform",
      stages: ["Instruments & Data", "Research", "Decision", "Execution", "Governance"],
      model: "Enterprise subscription",
      desc: "The complete trading operating layer. Your strategies, your risk parameters, your commercial terms.",
    },
    {
      name: "Bespoke Strategy Build",
      stages: ["Instruments & Data", "Research", "Decision", "Execution", "Governance"],
      model: "Development fee + retainer",
      desc: "We build specific strategies to your requirements. You operate them. Typically $100K-$250K development plus ongoing terms.",
    },
  ],
  note: "Every level uses the same underlying infrastructure. Expanding from data to full platform is adding access, not migrating systems.",
}
```

---

## Slide 5 — Coverage Breadth

**Type:** `breadth-matrix` (reuse from board deck)

Same data as board presentation slide 5 — the 5×5 asset class × capability matrix.

---

## Slide 6 — Strategy Families Available

**Type:** `strategies` (reuse from board deck)

Same data as board presentation slide 6 — the risk/return/capacity spectrum table.

---

## Slide 7 — Backtest to Live

**Type:** `doctrine` (reuse)

```ts
{
  id: 7,
  type: "doctrine",
  title: "The Gap That Doesn\u2019t Exist Here",
  subtitle: "On most platforms, backtesting and live trading are separate environments. On ours, they are the same.",
  points: [
    {
      problem: "Backtest environment uses different data feeds",
      solution: "Same data pipeline serves both backtest and live",
    },
    {
      problem: "Feature calculations diverge between research and production",
      solution: "Same feature calculations, same code, same outputs",
    },
    {
      problem: "Risk controls have to be reimplemented for live",
      solution: "Same risk controls carry through \u2014 nothing to rebuild",
    },
    {
      problem: "Months of engineering to promote a strategy",
      solution: "Configuration change. Not a rewrite.",
    },
  ],
  differentiators: [
    "When you validate something in research, you know it will behave the same way in production",
    "No translation layer, no rewrite, no months of engineering",
    "Your validation history, data history, and operational familiarity accumulate over time",
  ],
  conclusion: "The research-to-production handoff is a configuration change. That\u2019s the single most important thing about this platform.",
}
```

---

## Slide 8 — Why Not Build It Yourself?

**Type:** `operations` (reuse — 3 columns)

```ts
{
  id: 8,
  type: "operations",
  title: "The Build vs Buy Comparison",
  columns: [
    {
      title: "If You Build",
      items: [
        "Integrate 80+ venues, each with different schemas",
        "Build normalised schema layer from scratch",
        "Build backtesting that actually matches production",
        "Build execution, monitoring, risk, compliance tools",
        "18-24 months before you can trade",
      ],
    },
    {
      title: "If You Use Our Platform",
      items: [
        "Venues already integrated and normalised",
        "Backtest to live on shared infrastructure",
        "Execution algorithms across all connected venues",
        "Monitoring, risk, reporting, and compliance included",
        "Live in weeks, not years",
      ],
    },
    {
      title: "What AI Can\u2019t Replace",
      items: [
        "Knowing what a good fill looks like across venue microstructures",
        "Reconciling positions across chains when a bridge fails",
        "Debugging a drawdown under pressure at 3am",
        "Judging whether underperformance is market regime or system fault",
        "Operational experience that compounds over years",
      ],
    },
  ],
  callout: "AI accelerates the build. It doesn\u2019t replace the operational experience. We use AI to move fast. We use experience to move correctly.",
  metrics: [
    { value: "3", label: "Years Building" },
    { value: "80+", label: "Venues Integrated" },
    { value: "22", label: "Microservices" },
    { value: "24,500+", label: "Automated Tests" },
  ],
}
```

---

## Slide 9 — Why Not Just Use AI?

**Type:** `faq` (reuse from board deck — single question, expanded)

```ts
{
  id: 9,
  type: "faq",
  title: "What AI Can and Can\u2019t Do",
  subtitle: "We use AI extensively. Here\u2019s where it helps and where it doesn\u2019t.",
  questions: [
    {
      q: "What AI is good at",
      a: "Writing code, building interfaces, integrating APIs, generating tests, reviewing pull requests, monitoring systems. We use it for all of these. It makes a small team operate like a much larger one.",
    },
    {
      q: "What AI can\u2019t do yet",
      a: "Know what a good fill looks like. Reconcile positions across blockchains when infrastructure fails. Handle venue outages with open positions. Debug a drawdown when the cause is market microstructure, not code. Make the judgement call on whether a strategy is broken or the market regime changed.",
    },
    {
      q: "Why experience matters",
      a: "Our team has personally traded options, delta one, high frequency, and medium frequency across traditional finance, crypto, decentralised finance, and sports. That experience shapes every design decision. AI multiplies judgement \u2014 if the judgement isn\u2019t there, the multiplication doesn\u2019t help.",
    },
    {
      q: "The bottom line",
      a: "You could use AI to build a trading system from scratch. You\u2019d still need experienced people to operate it. We\u2019ve already done both \u2014 the build and three years of operation. You can access the result rather than repeating the process.",
    },
  ],
}
```

---

## Slide 10 — Your Alpha Stays Yours

**Type:** `doctrine` (reuse)

```ts
{
  id: 10,
  type: "doctrine",
  title: "Your Alpha Stays Yours",
  subtitle: "We don\u2019t need your edge. We have our own.",
  points: [
    {
      problem: "Data only \u2014 do you see my signals?",
      solution: "No. You get normalised feeds. We never see what you do with them.",
    },
    {
      problem: "Execution \u2014 do you see my strategy logic?",
      solution: "No. We route and fill. We don\u2019t know the logic behind your orders.",
    },
    {
      problem: "Full platform \u2014 could you copy my strategy?",
      solution: "We don\u2019t trade the same strategy you\u2019re running. Commercial terms are bespoke. Your strategy is yours.",
    },
    {
      problem: "What if I leave?",
      solution: "If we built a bespoke strategy for you, the logic is yours. The switching cost is operational familiarity, not contractual lock-in.",
    },
  ],
  differentiators: [
    "Internal strategies stay internal \u2014 proprietary, not shared",
    "Client strategies are separate \u2014 built to your requirements, operated by you",
    "Enough strategy families across enough asset classes that there\u2019s no conflict",
  ],
  conclusion: "The infrastructure is shared. The alpha is not. That\u2019s the design.",
}
```

---

## Slide 11 — Who Uses It Today

**Type:** `traction` (reuse — 3 columns)

```ts
{
  id: 11,
  type: "traction",
  title: "Proof Points",
  achieved: [
    { text: "Our own capital", detail: "$7.5M under management, 30%+ annualised on crypto strategy" },
    { text: "First platform client", detail: "$125K engagement, decentralised finance fund \u2014 3 strategies, 5-20% yields" },
    { text: "Growing engagement", detail: "Expected to reach $250K+ with ongoing retainer" },
    { text: "FCA authorised", detail: "Ref 975797, one appointed representative live" },
  ],
  inProgress: [
    { text: "Expanding strategy coverage", detail: "Machine learning, options, and sports strategies coming through" },
    { text: "Execution services", detail: "Memorandum of understanding with institutional counterparty" },
    { text: "Additional regulatory clients", detail: "3 in active conversation" },
  ],
  launchReady: [
    { text: "Full platform across 5 asset classes", detail: "Production-grade, 22 microservices, 24,500+ tests" },
    { text: "35 strategies, 5 families", detail: "Available for bespoke deployment" },
    { text: "9 execution algorithms", detail: "Time-weighted, volume-weighted, smart routing, optimal execution" },
    { text: "Client reporting and compliance", detail: "Executive dashboard, investment book of records, regulatory reporting" },
  ],
  checkpoint: "The platform you\u2019d be using is the same one running real capital and serving real clients today.",
}
```

---

## Slide 12 — How It Works Commercially

**Type:** `strategies` (reuse table format — repurposed for pricing tiers)

```ts
{
  id: 12,
  type: "strategies",
  title: "Pricing and Terms",
  subtitle: "No off-the-shelf pricing. Every engagement is scoped to what you need.",
  families: [
    {
      name: "Data subscription",
      returns: "From a few hundred/month",
      drawdown: "",
      capacity: "Single to all asset classes",
      character: "Monthly subscription, scales with breadth",
      risk: "low",
    },
    {
      name: "Research access",
      returns: "Compute credits or subscription",
      drawdown: "",
      capacity: "Based on usage",
      character: "Backtesting and simulation capacity",
      risk: "low",
    },
    {
      name: "Execution",
      returns: "Per-trade or subscription",
      drawdown: "",
      capacity: "All connected venues",
      character: "Advanced algorithms as add-ons",
      risk: "low",
    },
    {
      name: "Full platform",
      returns: "Enterprise subscription",
      drawdown: "",
      capacity: "Scoped to engagement",
      character: "Includes reporting, compliance, ongoing updates",
      risk: "medium",
    },
    {
      name: "Bespoke strategy build",
      returns: "$100K-$250K development",
      drawdown: "",
      capacity: "Plus retainer or performance share",
      character: "We build, you operate. Terms negotiated per engagement.",
      risk: "medium",
    },
  ],
  callout: "The first conversation is always about what you need and what scope makes sense. We can have you looking at live data within days.",
}
```

---

## Slide 13 — Next Steps

**Type:** `ask` (reuse)

```ts
{
  id: 13,
  type: "ask",
  title: "How to Start",
  subtitle: "The next step is a conversation about what you\u2019re trying to do \u2014 which asset classes, what kind of strategies, what your current setup looks like, and where the gaps are.",
  asks: [
    {
      title: "Scoping Conversation",
      items: [
        "Which asset classes are you focused on?",
        "What does your current infrastructure look like?",
        "Where are the gaps \u2014 data, research, execution, monitoring?",
        "Are you looking for platform access or bespoke strategy development?",
      ],
    },
    {
      title: "Trial Period",
      items: [
        "We\u2019re happy to set up a trial on data and research layers",
        "See the normalisation quality, coverage, and backtesting environment",
        "Evaluate before committing to anything broader",
        "No commitment required to explore",
      ],
    },
    {
      title: "Timeline",
      items: [
        "Data access: days",
        "Research environment: days",
        "Execution integration: weeks",
        "Full platform or bespoke build: scoped per engagement",
      ],
    },
  ],
  contact: "ikenna@odum-research.com",
}
```

---

## Slide 14 — Demo

**Type:** `demo` (reuse from board deck)

Same clickable section cards as board presentation.

---

## Renderers Required

All reused from the board presentation. No new renderers needed.

| Slide                | Type             | Status                |
| -------------------- | ---------------- | --------------------- |
| 1. Cover             | `cover`          | Existing              |
| 2. Problem           | `doctrine`       | Existing              |
| 3. What You Get      | `lifecycle-new`  | Existing              |
| 4. Engagement Levels | `packaging`      | Existing              |
| 5. Coverage          | `breadth-matrix` | Existing              |
| 6. Strategy Families | `strategies`     | Existing              |
| 7. Backtest to Live  | `doctrine`       | Existing              |
| 8. Build vs Buy      | `operations`     | Existing              |
| 9. AI Question       | `faq`            | Existing              |
| 10. Alpha            | `doctrine`       | Existing              |
| 11. Proof Points     | `traction`       | Existing              |
| 12. Pricing          | `strategies`     | Existing (repurposed) |
| 13. Next Steps       | `ask`            | Existing              |
| 14. Demo             | `demo`           | Existing              |

All 14 slides use existing renderers. Zero new code needed — just a new data file and page route.

---

## Files to Create

| File                                                                                                     | Action                                                                             |
| -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `app/(platform)/investor-relations/strategy-service-presentation/page.tsx`                               | **New** route                                                                      |
| `app/(platform)/investor-relations/strategy-service-presentation/components/strategy-service-data.ts`    | **New** slide data                                                                 |
| `app/(platform)/investor-relations/strategy-service-presentation/components/strategy-service-client.tsx` | **New** page component (copy board-presentation-client.tsx, import different data) |
| `app/(platform)/investor-relations/page.tsx`                                                             | **Update** — add third presentation link                                           |
