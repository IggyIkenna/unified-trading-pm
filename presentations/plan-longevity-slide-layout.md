# Plan & Longevity Presentation — Slide Layout Specification

**Deck:** The Path to $100M **Target:** New route at `/investor-relations/plan-presentation` (or append to board
presentation) **Slides:** 11 **Date:** April 2026

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
  title: "The Path to $100M",
  subtitle: "Strategy availability, service readiness, and capital growth — the plan for the next 30 months.",
  tagline: "FCA Authorised",
  stats: [
    { value: "$7.5M", label: "Today" },
    { value: "$10M+", label: "End 2026" },
    { value: "$25M+", label: "End 2027" },
    { value: "$100M", label: "End 2028" },
  ],
}
```

---

## Slide 2 — The Logic

**Type:** `doctrine` (reuse — problem/solution pairs work for the "why breadth exists" framing)

```ts
{
  id: 2,
  type: "doctrine",
  title: "Why Breadth Exists",
  subtitle: "We can't build and scale every strategy ourselves. We don't have the manpower, the capital, or the distribution network. The breadth exists to power two things.",
  points: [
    {
      problem: "We can't trade everything ourselves",
      solution: "Breadth powers investment management — we pick strategies, trade our capital, and partition away our alpha",
    },
    {
      problem: "Clients want infrastructure, not just returns",
      solution: "Same breadth powers bespoke white-label — clients get access to the infrastructure we trade on",
    },
    {
      problem: "Track record takes time to build",
      solution: "Platform revenue (bespoke builds) funds the business while track records compound",
    },
    {
      problem: "Scaling requires distribution we don't have yet",
      solution: "Advisory network and partnerships provide distribution into institutional channels",
    },
  ],
  differentiators: [
    "Internal alpha stays internal — we don't share signal logic, feature weights, or parameters",
    "Client strategies are bespoke — we don't trade the same strategy alongside you",
    "Infrastructure is shared — the same system powers both sides",
  ],
  conclusion: "The investment management side grows through track record. The platform side grows through client deployments. Both run on the same foundation.",
}
```

---

## Slide 3 — Capital Trajectory

**Type:** NEW — `trajectory` (horizontal timeline with milestones and growing bar/line)

### Layout

```
┌─────────────────────────────────────────────────────┐
│ From $7.5M to $100M                                 │
│ ─────────────────────                               │
│ Capital follows demonstrated performance. Each      │
│ stage is unlocked by track record.                  │
│                                                     │
│  $100M ·····································│ ██    │
│         ·                                   │ ██    │
│   $25M ····························│ ████   │ ██    │
│         ·                         │ ████   │ ██    │
│   $10M ···················│ ██████│ ████   │ ██    │
│         ·                 │ ██████│ ████   │ ██    │
│  $7.5M ──│ ██████████████│ ██████│ ████   │ ██    │
│         Now    End 2026   End 2027   End 2028       │
│                                                     │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐       │
│ │ $10M+      │ │ $25M+      │ │ $100M      │       │
│ │ DeFi +     │ │ 1yr track  │ │ 18mo+      │       │
│ │ ML strats  │ │ record on  │ │ track on   │       │
│ │ added      │ │ 4 families │ │ all fams   │       │
│ │ 2nd plat-  │ │ Instit.    │ │ Multiple   │       │
│ │ form client│ │ allocators │ │ mandates   │       │
│ └────────────┘ └────────────┘ └────────────┘       │
│                                                     │
│ ┌───────────────────────────────────────────────┐   │
│ │ The unlock at each stage is track record.     │   │
│ │ Every month of live trading compounds our     │   │
│ │ ability to raise.                             │   │
│ └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Data

```ts
{
  id: 3,
  type: "trajectory",
  title: "From $7.5M to $100M",
  subtitle: "Capital follows demonstrated performance. Each stage is unlocked by track record.",
  milestones: [
    {
      date: "Now",
      value: "$7.5M",
      detail: "Crypto mean reversion (30%+ annualised) + Bitcoin fund of funds",
      active: true,
    },
    {
      date: "End 2026",
      value: "$10M+",
      detail: "Decentralised finance + machine learning strategies added, second platform client",
    },
    {
      date: "End 2027",
      value: "$25M+",
      detail: "1+ year track record on 4 families, institutional allocators engaged",
    },
    {
      date: "End 2028",
      value: "$100M",
      detail: "18+ months track across all families, multiple mandates, sub-linear cost scaling",
    },
  ],
  callout: "The unlock at each stage is track record. Every month of live trading compounds our ability to raise.",
}
```

---

## Slide 4 — Strategy Availability Timeline

**Type:** NEW — `timeline-matrix` (rows = strategy families, columns = time periods, cells show status)

### Layout

```
┌─────────────────────────────────────────────────────┐
│ When Each Strategy Becomes Available                │
│ ─────────────────────────────────                   │
│                                                     │
│                  Now    May  Jun  Q3   Q4   Q2 2027 │
│ ┌───────────────┬─────┬────┬────┬────┬────┬───────┐ │
│ │Crypto Mean Rev│ ██  │ ██ │ ██ │ ██ │ ██ │  ██   │ │
│ │               │LIVE │    │    │    │    │       │ │
│ ├───────────────┼─────┼────┼────┼────┼────┼───────┤ │
│ │Bitcoin FoF    │ ██  │ ██ │ ██ │ ██ │ ██ │  ██   │ │
│ │               │LIVE │    │    │    │    │       │ │
│ ├───────────────┼─────┼────┼────┼────┼────┼───────┤ │
│ │DeFi Yield     │TEST │ ██ │ ██ │ ██ │ ██ │  ██   │ │
│ │               │     │LIVE│    │    │    │       │ │
│ ├───────────────┼─────┼────┼────┼────┼────┼───────┤ │
│ │ML Directional │     │TEST│ ██ │ ██ │ ██ │  ██   │ │
│ │               │     │    │LIVE│    │    │       │ │
│ ├───────────────┼─────┼────┼────┼────┼────┼───────┤ │
│ │Sports ML      │     │TEST│ ██ │ ██ │ ██ │  ██   │ │
│ │               │     │    │AVBL│    │    │       │ │
│ ├───────────────┼─────┼────┼────┼────┼────┼───────┤ │
│ │Options / Vol  │     │    │    │TEST│ ██ │  ██   │ │
│ │               │     │    │    │    │LIVE│       │ │
│ ├───────────────┼─────┼────┼────┼────┼────┼───────┤ │
│ │High Freq / MM │     │    │    │    │TEST│  ██   │ │
│ │               │     │    │    │    │    │ LIVE  │ │
│ └───────────────┴─────┴────┴────┴────┴────┴───────┘ │
│                                                     │
│ Legend: TEST = internal testing  LIVE = client-ready │
│         ██ = available and compounding track record  │
└─────────────────────────────────────────────────────┘
```

### Data

```ts
{
  id: 4,
  type: "timeline-matrix",
  title: "When Each Strategy Becomes Available",
  subtitle: "From internal testing through investment management to client deployment.",
  periods: ["Now", "May 2026", "Jun 2026", "Q3 2026", "Q4 2026", "Q2 2027"],
  strategies: [
    {
      name: "Crypto mean reversion",
      statuses: ["live", "live", "live", "live", "live", "live"],
    },
    {
      name: "Bitcoin fund of funds",
      statuses: ["live", "live", "live", "live", "live", "live"],
    },
    {
      name: "Decentralised finance yield",
      statuses: ["testing", "live", "live", "live", "live", "live"],
    },
    {
      name: "Machine learning directional",
      statuses: ["", "testing", "live", "live", "live", "live"],
    },
    {
      name: "Sports prediction",
      statuses: ["", "testing", "available", "available", "available", "available"],
    },
    {
      name: "Options / volatility",
      statuses: ["", "", "", "testing", "live", "live"],
    },
    {
      name: "High frequency / market making",
      statuses: ["", "", "", "", "testing", "live"],
    },
  ],
}
```

---

## Slide 5 — Service Availability Matrix

**Type:** `breadth-matrix` (reuse from board deck — rows = strategy families, columns = service types)

```ts
{
  id: 5,
  type: "breadth-matrix",
  title: "What\u2019s Available When, by Service",
  subtitle: "Data and research are always first. Internal testing next. Then investment management. Then bespoke builds.",
  columns: ["Internal Testing", "Investment Management", "Platform / Bespoke", "Data & Research"],
  rows: [
    {
      asset: "Crypto mean reversion",
      color: "green",
      cells: ["Done", "Live now", "Available now", "Available now"],
    },
    {
      asset: "Bitcoin fund of funds",
      color: "green",
      cells: ["Done", "Live now", "N/A (fund structure)", "Available now"],
    },
    {
      asset: "Decentralised finance yield",
      color: "violet",
      cells: ["Now", "May 2026", "May 2026 (first client)", "Available now"],
    },
    {
      asset: "Machine learning directional",
      color: "cyan",
      cells: ["May 2026", "June 2026", "June 2026", "Available now"],
    },
    {
      asset: "Sports prediction",
      color: "amber",
      cells: ["May 2026", "June 2026", "Q3 2026", "Available now"],
    },
    {
      asset: "Options / volatility",
      color: "cyan",
      cells: ["Q3 2026", "Q4 2026", "Q4 2026", "Q3 2026"],
    },
    {
      asset: "High frequency / market making",
      color: "green",
      cells: ["Q4 2026", "Q2 2027", "Q2 2027", "Q4 2026"],
    },
  ],
}
```

---

## Slide 6 — Alpha Partitioning

**Type:** `doctrine` (reuse — problem/solution pairs for internal vs client)

```ts
{
  id: 6,
  type: "doctrine",
  title: "What We Keep, What We Share",
  subtitle: "We partition strategies into two categories. The infrastructure is shared. The alpha is not.",
  points: [
    {
      problem: "Internal alpha",
      solution: "Strategies we run for our own investment management. Proprietary. Signal logic, feature weights, parameters never shared.",
    },
    {
      problem: "Bespoke client strategies",
      solution: "Built on the same infrastructure, but to the client\u2019s requirements. We don\u2019t trade the client\u2019s strategy ourselves.",
    },
  ],
  differentiators: [
    "Enough strategy families to allocate some internally and still build for clients without conflict",
    "Bespoke commercial terms \u2014 profit shares, retainers, subscriptions tailored to the engagement",
    "Client strategies stay with the client \u2014 if they leave, they can take the logic",
  ],
  conclusion: "The infrastructure is shared. The alpha is not.",
}
```

---

## Slide 7 — You Don't Have to Share Alpha

**Type:** `packaging` (reuse — modular engagement levels as cards)

```ts
{
  id: 7,
  type: "packaging",
  title: "You Don\u2019t Have to Give Us Anything",
  subtitle: "The platform is modular. Engage at whatever level you\u2019re comfortable with.",
  services: [
    {
      name: "Just Data",
      stages: ["Instruments & Data"],
      model: "Subscription",
      desc: "Normalised feeds across all five asset classes. We never see your signals.",
    },
    {
      name: "Just Execution",
      stages: ["Execution"],
      model: "Per-trade or subscription",
      desc: "Plug your own signals into our execution layer. We route and fill. We don\u2019t see the logic behind your orders.",
    },
    {
      name: "Just Research",
      stages: ["Research"],
      model: "Compute credits",
      desc: "Use our backtesting environment. Take your results and execute elsewhere if you want.",
    },
    {
      name: "Just Reporting",
      stages: ["Governance"],
      model: "Subscription",
      desc: "Client reporting and compliance tools. Your strategy stays entirely yours.",
    },
    {
      name: "Full Platform",
      stages: ["Instruments & Data", "Research", "Decision", "Execution", "Governance"],
      model: "Bespoke",
      desc: "Run everything on our infrastructure. Even then, we don\u2019t trade your strategy. Commercial terms are bespoke.",
    },
  ],
  note: "The engagement is modular and the commercial terms are bespoke. We\u2019re not asking anyone to hand over their edge.",
}
```

---

## Slide 8 — Why This Needs Experienced Humans

**Type:** `operations` (reuse — 3 columns)

```ts
{
  id: 8,
  type: "operations",
  title: "The AI Question",
  columns: [
    {
      title: "Experience Across Asset Classes",
      items: [
        "Personally traded options, delta one, high frequency, medium frequency",
        "Traditional finance, crypto, decentralised finance, and sports",
        "AI multiplies the judgement of the person directing it",
        "If you don\u2019t know what a good fill looks like, AI won\u2019t tell you",
      ],
    },
    {
      title: "Accountability Under Pressure",
      items: [
        "Significant drawdown + system built entirely by AI = you can\u2019t debug it",
        "You want to be able to switch off AI and solve things yourself",
        "Requires a team that understands the code, the strategies, and the markets",
        "Not just the prompts",
      ],
    },
    {
      title: "Building vs Operating",
      items: [
        "AI can help build software quickly",
        "Operating live trading across five asset classes is different",
        "Venue outages, position reconciliation across chains, regulatory reporting",
        "Operational experience compounds over years \u2014 you can\u2019t prompt-engineer it",
      ],
    },
  ],
  callout: "We use AI heavily in development and operations. But the system works because there are experienced humans making the critical decisions.",
  metrics: [
    { value: "5", label: "Asset Classes Traded" },
    { value: "3", label: "Years Operating" },
    { value: "22", label: "Microservices" },
    { value: "24,500+", label: "Automated Tests" },
  ],
}
```

---

## Slide 9 — Key Milestones

**Type:** `traction` (reuse — 3 columns for Q2 2026, End 2026, End 2027-2028)

```ts
{
  id: 9,
  type: "traction",
  title: "The Next 30 Months",
  achieved: [
    { text: "End of Q2 2026", detail: "(2 months)" },
    { text: "Decentralised finance platform client live", detail: "$125K growing to $250K+" },
    { text: "Machine learning strategies on own capital", detail: "Traditional finance + sports" },
    { text: "Appointed representative pipeline converting", detail: "3 prospects" },
    { text: "Capital under management: $8-10M", detail: "" },
  ],
  inProgress: [
    { text: "End of 2026", detail: "(8 months)" },
    { text: "Capital north of $10M", detail: "Multiple strategy families live" },
    { text: "Options and execution available", detail: "Full algo suite refined" },
    { text: "6+ months track record", detail: "On 4 strategy families" },
    { text: "Second platform client underway", detail: "" },
  ],
  launchReady: [
    { text: "End of 2027 \u2192 2028", detail: "(20-30 months)" },
    { text: "Capital above $25M (2027)", detail: "Institutional allocator threshold" },
    { text: "$100M target (2028)", detail: "18+ month track records" },
    { text: "Second Elysium-type partnership", detail: "Bespoke deal, live" },
    { text: "5+ appointed representatives", detail: "Regulatory umbrella scaled" },
  ],
  checkpoint: "The path is: demonstrate performance, compound track record, open institutional channels. The system is built. The question is execution and time.",
}
```

---

## Slide 10 — Why This Plan Is Realistic

**Type:** `operations` (reuse — 4 metrics + callout, no columns needed — use differentiator-style)

Could also use `doctrine` with 4 points:

```ts
{
  id: 10,
  type: "doctrine",
  title: "Why This Plan Is Realistic",
  subtitle: "This isn\u2019t a plan from zero. It\u2019s a plan from seven and a half million with demonstrated performance.",
  points: [
    {
      problem: "Starting from zero?",
      solution: "No \u2014 $7.5M live, 30%+ returns, first platform sold, first appointed representative onboarded",
    },
    {
      problem: "Track record takes forever?",
      solution: "Every month of live trading makes the next capital raise easier. We\u2019re most of the way through the hardest year",
    },
    {
      problem: "Scaling costs scale linearly?",
      solution: "The same 22 microservices that run $7.5M can run $100M. Infrastructure costs scale sub-linearly",
    },
    {
      problem: "Dependent on investment management fees alone?",
      solution: "Platform revenue ($125K growing to $250K+) funds the business while track records compound",
    },
  ],
  conclusion: "The path to a hundred million is: demonstrate performance, compound track record, open institutional channels.",
}
```

---

## Slide 11 — Demo

**Type:** `demo` (reuse from board deck — same clickable links)

Same as board presentation slide 11.

---

## New Renderers Required

| Type              | Status  | Notes                                                                                                                                                    |
| ----------------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `trajectory`      | **NEW** | Horizontal timeline with growing bars and milestone cards below. Animated bars growing on entry.                                                         |
| `timeline-matrix` | **NEW** | Rows = strategies, columns = time periods. Cells colour-coded: empty (grey), testing (amber), live (emerald), available (primary). Animated row stagger. |
| All others        | Reuse   | `cover`, `doctrine`, `breadth-matrix`, `packaging`, `operations`, `traction`, `demo` all exist in board deck.                                            |

---

## Files to Create / Modify

| File                                                           | Action                                                                    |
| -------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `plan-presentation-data.ts`                                    | **New** — 11 slides as specified above                                    |
| `plan-presentation-client.tsx`                                 | **New** — page component (can largely copy board-presentation-client.tsx) |
| `board-presentation-slide-part-a.tsx`                          | **Add** `trajectory` renderer                                             |
| `board-presentation-slide-part-b.tsx`                          | **Add** `timeline-matrix` renderer                                        |
| `app/(platform)/investor-relations/plan-presentation/page.tsx` | **New** — Next.js route                                                   |
| `app/(platform)/investor-relations/page.tsx`                   | **Update** — add link to plan presentation alongside board presentation   |
