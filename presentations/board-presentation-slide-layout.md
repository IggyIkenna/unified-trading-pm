# Board Presentation — Slide Layout Specification

**Deck:** One Unified Trading System **Target:** `/investor-relations/board-presentation` (unified-trading-system-ui)
**Slides:** 10 (down from 13) **Date:** April 2026

---

## Design Language

### Palette (unchanged from current deck)

| Token              | Colour              | Usage                                           |
| ------------------ | ------------------- | ----------------------------------------------- |
| `primary`          | Gold / brand accent | Titles, stats, callout borders, active elements |
| `foreground`       | White               | Body text, card text                            |
| `muted-foreground` | Dim grey-blue       | Subtitles, descriptions, secondary text         |
| `destructive`      | Red                 | Problem labels                                  |
| `emerald-400`      | Green               | Achieved / live / low-risk indicators           |
| `amber-400`        | Amber               | In-progress / medium-risk indicators            |
| `rose-400`         | Rose                | High-risk / prediction market colour            |
| `cyan-400`         | Cyan                | TradFi asset class                              |
| `green / emerald`  | Green               | CeFi asset class                                |
| `violet-400`       | Violet              | DeFi asset class                                |
| `amber-400`        | Amber               | Sports asset class                              |
| `rose-400`         | Rose                | Predictions asset class                         |
| `card`             | Dark card bg        | Card backgrounds                                |
| `border`           | Subtle border       | Card and section borders                        |

### Typography

- **Slide titles:** `text-3xl font-bold text-primary border-b border-border pb-2 mb-2` (h2)
- **Cover title:** `text-5xl md:text-6xl font-black` with gradient clip (foreground → primary)
- **Subtitles:** `text-muted-foreground` with `max-w-3xl`
- **Card headers:** `text-sm font-semibold text-primary uppercase tracking-wider`
- **Body text:** `text-xs text-muted-foreground` or `text-sm text-muted-foreground`
- **Stats:** Large `text-4xl font-bold text-primary` number, tiny `text-xs text-muted-foreground uppercase` label

### Animation

- Framer Motion on all slides
- Slide transition: `opacity 0→1, x 50→0` on enter, `opacity 1→0, x 0→-50` on exit, 0.3s
- Staggered card/row entry: `delay: 0.1 * i` (or `0.08 * i` for dense content)
- Initial: `opacity: 0, y: 20` (cards) or `opacity: 0, x: -20` (rows)

### Controls (unchanged)

- Header: Logo, FCA badge, autoplay toggle, fullscreen toggle, slide counter
- Footer: Previous/Next buttons, dot navigation
- Keyboard: Arrow keys, Space (next), F (fullscreen), Escape (exit fullscreen)

---

## Slide 1 — Cover

**Renderer:** `cover` (existing — no changes needed to renderer)

### Layout

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│              [centred, vertically centred]           │
│                                                     │
│         One Unified Trading System                  │
│         ← gradient text, 5xl/6xl, font-black →      │
│                                                     │
│     A single operating layer for multi-asset        │
│     trading, execution, and oversight.              │
│     Built for our own capital. Structured           │
│     for institutional clients.                      │
│         ← text-xl, muted, max-w-3xl →               │
│                                                     │
│         ════════════════════                         │
│         ← gradient bar, primary→violet, w-20 →      │
│                                                     │
│         FCA AUTHORISED | REF 975797                 │
│         ← text-sm, primary, uppercase, tracking →   │
│                                                     │
│     ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│     │   5    │ │ 12,000+│ │   22   │ │ $7.5M  │    │
│     │ Asset  │ │  Live  │ │ Micro- │ │  AUM   │    │
│     │Classes │ │Instrmnts│ │services│ │        │    │
│     └────────┘ └────────┘ └────────┘ └────────┘    │
│     ← grid-cols-4, gap-6, text-center →             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Data

```ts
{
  id: 1,
  type: "cover",
  title: "One Unified Trading System",
  subtitle: "A single operating layer for multi-asset trading, execution, and oversight. Built for our own capital. Structured for institutional clients.",
  tagline: "FCA Authorised",
  stats: [
    { value: "5", label: "Asset Classes" },
    { value: "12,000+", label: "Live Instruments" },
    { value: "22", label: "Microservices" },
    { value: "$7.5M", label: "AUM" },
  ],
}
```

---

## Slide 2 — The Problem

**Renderer:** `doctrine` (existing — no changes needed to renderer)

### Layout

```
┌─────────────────────────────────────────────────────┐
│ The Market Is Still Stitched Together                │
│ ─────────────────────────────────────                │
│ Most firms assemble separate tools for data,        │
│ research, execution, monitoring, and compliance...  │
│                                                     │
│ ┌──────────────────────┐ ┌──────────────────────┐   │
│ │ PROBLEM              │ │ PROBLEM              │   │
│ │ 4+ data vendors,     │ │ Strategies break     │   │
│ │ 4 schemas, 4 bills   │ │ when promoted to live│   │
│ │         →            │ │         →            │   │
│ │ SOLUTION             │ │ SOLUTION             │   │
│ │ One normalised       │ │ Same code path from  │   │
│ │ schema, all 5 assets │ │ simulation to prod   │   │
│ └──────────────────────┘ └──────────────────────┘   │
│ ┌──────────────────────┐ ┌──────────────────────┐   │
│ │ PROBLEM              │ │ PROBLEM              │   │
│ │ Execution fragmented │ │ Compliance bolted    │   │
│ │ across venues        │ │ on after the fact    │   │
│ │         →            │ │         →            │   │
│ │ SOLUTION             │ │ SOLUTION             │   │
│ │ One algo layer, one  │ │ Audit trail & ctrls  │   │
│ │ routing system       │ │ built into the layer │   │
│ └──────────────────────┘ └──────────────────────┘   │
│                                                     │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐             │
│ │ ✓ Cross- │ │ ✓ Back-  │ │ ✓ Same   │             │
│ │ asset    │ │ test to  │ │ infra    │             │
│ │ backtest │ │ live, no │ │ internal │             │
│ │ in one   │ │ rewrite  │ │ + client │             │
│ │ environ. │ │          │ │          │             │
│ └──────────┘ └──────────┘ └──────────┘             │
│                                                     │
│ ┌───────────────────────────────────────────────┐   │
│ │ The alternative is stitching. We built the    │   │
│ │ system.                                       │   │
│ └───────────────────────────────────────────────┘   │
│ ← callout: border-primary/30, bg-primary/5 →       │
└─────────────────────────────────────────────────────┘
```

### Data

```ts
{
  id: 2,
  type: "doctrine",
  title: "The Market Is Still Stitched Together",
  subtitle: "Most firms assemble separate tools for data, research, execution, monitoring, and compliance. Every boundary creates friction, reconciliation overhead, and operational risk.",
  points: [
    {
      problem: "4+ data vendors per firm, 4 schemas, 4 contracts",
      solution: "One normalised schema across all 5 asset classes",
    },
    {
      problem: "Strategies break when promoted to live",
      solution: "Same code path from simulation to production — config change, not rewrite",
    },
    {
      problem: "Execution fragmented across venues and asset classes",
      solution: "One algo layer, one order routing system, all venues",
    },
    {
      problem: "Compliance bolted on after the fact",
      solution: "Audit trail, controls, and regulatory reporting built into the operating layer",
    },
  ],
  differentiators: [
    "Cross-asset backtesting: DeFi, TradFi, crypto, sports, prediction markets — one environment",
    "Backtest to live with no rewrite — same data, same features, same risk controls",
    "Same infrastructure for internal capital and external clients",
  ],
  conclusion: "The alternative is stitching. We built the system.",
}
```

---

## Slide 3 — The Solution

**Renderer:** `lifecycle-new` (existing — no changes needed to renderer)

### Layout

```
┌─────────────────────────────────────────────────────┐
│ One System, Five Connected Layers                   │
│ ─────────────────────────────────                   │
│ From instrument discovery through execution to      │
│ regulatory reporting — the same layers govern       │
│ internal operations and client access.              │
│                                                     │
│ ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐  │
│ │   1    │ → │   2    │ → │   3    │ → │   4    │→ │
│ │Instrmts│   │Research│   │Decision│   │Executn │  │
│ │& Data  │   │& Model │   │& Strat │   │& Ctrl  │  │
│ │        │   │        │   │        │   │        │  │
│ │Discover│   │Feature,│   │Signals,│   │ Route, │  │
│ │normalis│   │ML, sim │   │sizing, │   │ fill,  │  │
│ │validate│   │        │   │risk    │   │monitor │  │
│ └────────┘   └────────┘   └────────┘   └────────┘  │
│                                                     │
│              ┌────────┐                             │
│            → │   5    │                             │
│              │Governce│                             │
│              │& Rptng │                             │
│              │        │                             │
│              │ Audit, │                             │
│              │comply, │                             │
│              │report  │                             │
│              └────────┘                             │
│                                                     │
│ ← Each stage: border-primary/30, bg-primary/5 →    │
│ ← Arrows between stages: ArrowRight icon →         │
│ ← Stages animate in with scale 0.8→1, staggered →  │
└─────────────────────────────────────────────────────┘
```

Note: The existing `lifecycle-new` renderer lays stages out horizontally in a flex row with arrows between them. With 5
stages instead of 7, each stage gets more horizontal space, which is an improvement.

### Data

```ts
{
  id: 3,
  type: "lifecycle-new",
  title: "One System, Five Connected Layers",
  subtitle: "From instrument discovery through execution to regulatory reporting — the same layers govern internal operations and client access.",
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

## Slide 4 — Why This Is Hard to Replicate

**Renderer:** `operations` (existing — no changes needed to renderer)

### Layout

```
┌─────────────────────────────────────────────────────┐
│ Why This Is Hard to Replicate                       │
│ ─────────────────────────────     ┌──┐┌──┐┌──┐┌──┐ │
│                                   │ 5││24K││22││7.5│ │
│                                   │AC││Tst││MS││AUM│ │
│                                   └──┘└──┘└──┘└──┘ │
│                                                     │
│ ┌─────────────────┐┌─────────────────┐┌───────────┐ │
│ │ ONE SHARED       ││ INTERNAL =      ││ ONE       │ │
│ │ INSTRUMENT LAYER ││ EXTERNAL        ││ OPERATING │ │
│ │                  ││                 ││ LAYER     │ │
│ │ → 12,000+ live   ││ → $7.5M AUM    ││ → Data,   │ │
│ │   instruments    ││   through the   ││   research│ │
│ │   across 5 asset ││   same system   ││   executn,│ │
│ │   classes        ││                 ││   monitor,│ │
│ │ → 28 DeFi proto- ││ → ~30%+ annual- ││   govrnce │ │
│ │   cols, 11 chains││   ised on CeFi  ││   — not   │ │
│ │ → 40,000+ sports ││   mean reversion││   bolted  │ │
│ │   fixtures/yr    ││                 ││   together│ │
│ │ → One canonical  ││ → Clients get   ││ → New     │ │
│ │   schema across  ││   same infra,   ││   venue → │ │
│ │   all domains    ││   not stripped   ││   every   │ │
│ │                  ││   down           ││   strategy│ │
│ │                  ││                 ││   benefits│ │
│ │                  ││ → If it degrades││ → < 1 day │ │
│ │                  ││   our P&L feels ││   to add  │ │
│ │                  ││   it first      ││   a venue │ │
│ └─────────────────┘└─────────────────┘└───────────┘ │
│                                                     │
│ ┌───────────────────────────────────────────────┐   │
│ │ Rebuilding this from scratch would be a       │   │
│ │ significant multi-year, multi-team effort.    │   │
│ │ We operate it with a small team — AI-assisted │   │
│ │ workflows handle routine operations, with     │   │
│ │ human approval gates at critical decisions.   │   │
│ └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Data

```ts
{
  id: 4,
  type: "operations",
  title: "Why This Is Hard to Replicate",
  columns: [
    {
      title: "One Shared Instrument Layer",
      items: [
        "12,000+ live instruments across 5 asset classes",
        "28 DeFi protocols across 11 blockchains",
        "40,000+ sports fixtures processed annually",
        "One canonical schema across all domains",
      ],
    },
    {
      title: "Internal = External",
      items: [
        "$7.5M AUM through the same system",
        "~30%+ annualised on CeFi mean reversion",
        "Clients get the same infrastructure, not a stripped-down version",
        "If it degrades, our P&L feels it first",
      ],
    },
    {
      title: "One Operating Layer",
      items: [
        "Data, research, execution, monitoring, governance — not bolted together",
        "New venue → every strategy benefits",
        "New strategy → every client benefits",
        "Under a day to integrate a new venue",
      ],
    },
  ],
  callout: "Rebuilding this from scratch would be a significant multi-year, multi-team effort. We operate it with a small team — AI-assisted workflows handle routine operations, with human approval gates at critical decisions.",
  metrics: [
    { value: "5", label: "Asset Classes" },
    { value: "24,500+", label: "Automated Tests" },
    { value: "22", label: "Microservices" },
    { value: "$7.5M", label: "AUM" },
  ],
}
```

---

## Slide 5 — Breadth Without Fragmentation

**Renderer:** `breadth-matrix` (NEW — must build)

### Layout

```
┌─────────────────────────────────────────────────────┐
│ Breadth Without Fragmentation                       │
│ ─────────────────────────────                       │
│ Every cell is served by the same underlying system. │
│                                                     │
│          Instruments  Data     Research  Execution  Monitor │
│ ┌───────┬──────────┬────────┬─────────┬──────────┬────────┐│
│ │TradFi │CME Group │Tick,   │Futures, │TWAP,VWAP,│P&L,    ││
│ │ (cyan)│ICE, CBOE,│orderbok│options, │SOR,      │risk,   ││
│ │       │NASDAQ,   │OHLCV   │equities │Almgren-  │recon   ││
│ │       │NYSE      │        │         │Chriss    │        ││
│ ├───────┼──────────┼────────┼─────────┼──────────┼────────┤│
│ │CeFi   │Binance,  │Tick,   │Spot,    │Same algo │Same    ││
│ │(green)│OKX,Bybit,│orderbk,│perps,   │suite +   │monitor ││
│ │       │Deribit +4│liqdtns,│options  │venue     │layer   ││
│ │       │          │funding │surface  │routing   │        ││
│ ├───────┼──────────┼────────┼─────────┼──────────┼────────┤│
│ │DeFi   │28 proto- │Lending │Yield    │Uniswap,  │On-chain││
│ │(violet│cols, 11  │rates,  │sim,     │Aave,     │position││
│ │)      │chains    │pool,gas│flash ln │Morpho    │tracking││
│ ├───────┼──────────┼────────┼─────────┼──────────┼────────┤│
│ │Sports │102 lgues,│Odds    │ML pred  │Cross-    │Settle- ││
│ │(amber)│40K+ fix/ │from 65+│pipeline │bookmaker │ment    ││
│ │       │yr        │sources │         │routing   │recon   ││
│ ├───────┼──────────┼────────┼─────────┼──────────┼────────┤│
│ │Predict│Polymarkt,│Binary/ │Cross-   │Prediction│Event   ││
│ │(rose) │Kalshi +3 │multi-  │market   │market    │resoltn ││
│ │       │          │outcome │arb det. │execution │tracking││
│ └───────┴──────────┴────────┴─────────┴──────────┴────────┘│
│                                                     │
│ ← scrolling venue ticker beneath (reuse existing) → │
│ [Binance] [OKX] [CME] [Aave] [Betfair] [Polymarket]│
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Visual Specification

- **Column headers:** `text-[10px] text-muted-foreground font-medium uppercase text-center`
- **Row headers:** Left-aligned, `text-xs font-semibold` in asset class colour. Each row has a `border-l-4` in its
  colour.
- **Cells:** `text-[10px] text-muted-foreground`. Brief — no more than 2-3 words per line, max 3 lines.
- **Grid:** `overflow-hidden rounded-lg border border-border`. Alternating row bg: `bg-card` / `bg-card/50`.
- **Row animation:** Staggered entry, `initial: { opacity: 0, x: -20 }`, `delay: 0.08 * i`.
- **Venue ticker:** Reuse the existing scrolling `VENUE_LIST` component from current coverage slide. Position it below
  the matrix with gradient fade edges. Auto-scroll, 30s loop.
- **No ArbitrageGalaxy on this slide.** The matrix is the visual. Keep it clean and structural.

### Data

```ts
{
  id: 5,
  type: "breadth-matrix",
  title: "Breadth Without Fragmentation",
  subtitle: "Every cell is served by the same underlying system.",
  columns: ["Instruments", "Data", "Research", "Execution", "Monitoring"],
  rows: [
    {
      asset: "TradFi",
      color: "cyan",
      cells: [
        "CME Group, ICE, CBOE, NASDAQ, NYSE",
        "Tick, orderbook, OHLCV",
        "Futures, options, equities",
        "TWAP, VWAP, SOR, Almgren-Chriss",
        "P&L, risk, reconciliation",
      ],
    },
    {
      asset: "Crypto CeFi",
      color: "green",
      cells: [
        "Binance, OKX, Bybit, Deribit +4",
        "Tick, orderbook, liquidations, funding",
        "Spot, perps, options surface",
        "Same algo suite + venue routing",
        "Same monitoring layer",
      ],
    },
    {
      asset: "DeFi",
      color: "violet",
      cells: [
        "28 protocols, 11 chains",
        "Lending rates, pool data, gas fees",
        "Yield simulation, flash loans",
        "Uniswap, Aave, Morpho connectors",
        "On-chain position tracking",
      ],
    },
    {
      asset: "Sports",
      color: "amber",
      cells: [
        "102 leagues, 40K+ fixtures/yr",
        "Odds from 65+ sources",
        "ML prediction pipeline",
        "Cross-bookmaker routing",
        "Settlement reconciliation",
      ],
    },
    {
      asset: "Predictions",
      color: "rose",
      cells: [
        "Polymarket, Kalshi +3",
        "Binary / multi-outcome pricing",
        "Cross-market arb detection",
        "Prediction market execution",
        "Event resolution tracking",
      ],
    },
  ],
}
```

---

## Slide 6 — Strategy Families

**Renderer:** `strategies` (NEW — must build)

### Layout

```
┌─────────────────────────────────────────────────────┐
│ Strategy Families — Risk, Return & Capacity         │
│ ─────────────────────────────────────────           │
│ Same infrastructure, configurable risk appetite.    │
│                                                     │
│ Family        Return     Drawdown  Capacity  Char.  │
│ ┌─────────────────────────────────────────────────┐ │
│ │● DeFi —     3-12%      <1%       $50M-     Lend,│ │
│ │  Stable     APY                  $100M+    stbl │ │
│ │  Yield                                    yield │ │
│ ├─────────────────────────────────────────────────┤ │
│ │● DeFi —     10-30%     5%        $5M-     Delta│ │
│ │  Basis      APY                  $20M     neutr│ │
│ │  Trades                                   fndng│ │
│ ├─────────────────────────────────────────────────┤ │
│ │● DeFi —     20-50%     15%       $5M/     Recur│ │
│ │  Leveraged  APY                  pool     sive,│ │
│ │                                           LP   │ │
│ ├─────────────────────────────────────────────────┤ │
│ │● CeFi       Market-    5-10%     $2M/     Momtm│ │
│ │  Trading    dependent            pair     ,arb │ │
│ ├─────────────────────────────────────────────────┤ │
│ │● TradFi     12-18%     8-10%     $5M/     ML   │ │
│ │  Quant                           name     dir, │ │
│ │                                           vol  │ │
│ ├─────────────────────────────────────────────────┤ │
│ │● Sports     Market-    20%       $100K-   ML,  │ │
│ │             dependent            $1M      arb  │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ┌───────────────────────────────────────────────┐   │
│ │ We deploy from $100K to $100M+ depending on   │   │
│ │ the strategy. The infrastructure is the same   │   │
│ │ — only the configuration changes.              │   │
│ └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Visual Specification

- **Table:** `overflow-hidden rounded-lg border border-border`
- **Header row:** `bg-card`, columns: Family | Return Range | Max Drawdown | Capacity | Character.
  `text-primary font-semibold text-left p-3 border-b border-primary`
- **Body rows:** Animated stagger (`delay: 0.1 * i`), `border-b border-border hover:bg-muted/50`
- **Row risk colour:** Each row has a left border accent:
  - Rows 1-2 (DeFi Stable, Basis): `border-l-4 border-emerald-400`
  - Row 3 (DeFi Leveraged): `border-l-4 border-amber-400`
  - Rows 4-5 (CeFi, TradFi): `border-l-4 border-sky-400`
  - Row 6 (Sports): `border-l-4 border-rose-400`
- **Family name column:** `font-semibold text-sm` (white)
- **Other columns:** `text-muted-foreground text-sm`
- **Callout:** Same style as other slides — `border-primary/30 bg-primary/5 text-center`

### Data

```ts
{
  id: 6,
  type: "strategies",
  title: "Strategy Families — Risk, Return & Capacity",
  subtitle: "Same infrastructure, configurable risk appetite.",
  families: [
    {
      name: "DeFi — Stable Yield",
      returns: "3-12% APY",
      drawdown: "<1%",
      capacity: "$50M-$100M+",
      character: "Lending, stablecoin yield",
      risk: "low",
    },
    {
      name: "DeFi — Basis Trades",
      returns: "10-30% APY",
      drawdown: "5%",
      capacity: "$5M-$20M",
      character: "Delta-neutral, funding capture",
      risk: "low",
    },
    {
      name: "DeFi — Leveraged",
      returns: "20-50% APY",
      drawdown: "15%",
      capacity: "$5M/pool",
      character: "Recursive staking, AMM LP",
      risk: "medium",
    },
    {
      name: "CeFi Trading",
      returns: "Market-dependent",
      drawdown: "5-10%",
      capacity: "$2M/pair",
      character: "Momentum, mean reversion, arb",
      risk: "medium",
    },
    {
      name: "TradFi Quant",
      returns: "12-18%",
      drawdown: "8-10%",
      capacity: "$5M/name",
      character: "ML directional, options, vol",
      risk: "medium",
    },
    {
      name: "Sports",
      returns: "Market-dependent",
      drawdown: "20%",
      capacity: "$100K-$1M",
      character: "ML prediction, arbitrage",
      risk: "high",
    },
  ],
  callout: "We deploy from $100K to $100M+ depending on the strategy. The infrastructure is the same — only the configuration changes.",
}
```

---

## Slide 7 — What Is Live Today

**Renderer:** `traction` (existing — modify to support 3 columns)

### Layout

```
┌─────────────────────────────────────────────────────┐
│ What Is Real Today                                  │
│ ─────────────────                                   │
│                                                     │
│ ┌───────────────┐ ┌───────────────┐ ┌─────────────┐ │
│ │ LIVE AND       │ │ IN ACTIVE     │ │ BUILT AND   │ │
│ │ REVENUE-       │ │ PIPELINE      │ │ LAUNCH-     │ │
│ │ GENERATING     │ │               │ │ READY       │ │
│ │ (emerald)      │ │ (amber)       │ │ (primary)   │ │
│ │                │ │               │ │             │ │
│ │ ✓ CeFi mean   │ │ ○ 3 additional│ │ ◆ Full      │ │
│ │   reversion   │ │   AR clients  │ │   trading   │ │
│ │   $4M AUM,    │ │   in conver-  │ │   platform  │ │
│ │   ~30%+ ann.  │ │   sation      │ │   UI, 5     │ │
│ │   $3.3M @ HWM │ │               │ │   asset cls │ │
│ │                │ │ ○ MOU for     │ │             │ │
│ │ ✓ BTC fund    │ │   execution   │ │ ◆ Data      │ │
│ │   of funds    │ │   services    │ │   provision │ │
│ │   $3.5M+ AUM  │ │               │ │   API       │ │
│ │                │ │ ○ Client      │ │             │ │
│ │ ✓ First AR    │ │   funding dev │ │ ◆ Backtest  │ │
│ │   client      │ │   (India Exch)│ │   to live   │ │
│ │   onboarded   │ │               │ │             │ │
│ │   FCA 975797  │ │               │ │ ◆ 35 strats │ │
│ │                │ │               │ │   5 families│ │
│ │ ✓ Platform    │ │               │ │             │ │
│ │   operational │ │               │ │ ◆ 9 exec    │ │
│ │   22 svcs,    │ │               │ │   algorithms│ │
│ │   24,500+ tst │ │               │ │             │ │
│ └───────────────┘ └───────────────┘ └─────────────┘ │
│                                                     │
│ ┌───────────────────────────────────────────────┐   │
│ │ All three services can onboard clients today. │   │
│ │ The bottleneck is commercial prioritisation,  │   │
│ │ not engineering.                              │   │
│ └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Renderer Modification

The existing `traction` renderer has 2 columns (achieved / inProgress). Modify to support a third column. The data shape
changes from:

```ts
// Old
{ achieved: [...], inProgress: [...] }
// New
{ categories: [
  { label: "...", color: "emerald", icon: "check", items: [...] },
  { label: "...", color: "amber", icon: "circle", items: [...] },
  { label: "...", color: "primary", icon: "diamond", items: [...] },
] }
```

Alternatively, keep backwards-compatible by adding a third field `launchReady` alongside `achieved` and `inProgress`.

### Data

```ts
{
  id: 7,
  type: "traction",
  title: "What Is Real Today",
  achieved: [
    { text: "CeFi mean reversion", detail: "$4M AUM, ~30%+ annualised, $3.3M at HWM" },
    { text: "BTC fund of funds", detail: "$3.5M+ AUM" },
    { text: "First AR client onboarded", detail: "FCA Appointed Representative, ref 975797" },
    { text: "Platform operational", detail: "22 microservices, 24,500+ tests, all passing QG" },
  ],
  inProgress: [
    { text: "3 additional AR clients", detail: "in conversation, evaluating coverage" },
    { text: "MOU for execution services", detail: "institutional counterparty" },
    { text: "Client funding development", detail: "India Exchange — delta one + arbitrage" },
  ],
  launchReady: [
    { text: "Full trading platform", detail: "UI across all 5 asset classes" },
    { text: "Data provision API", detail: "normalised feeds across all domains" },
    { text: "Backtest to live", detail: "same code path, config change to promote" },
    { text: "35 strategies, 5 families", detail: "30 code-complete, covering full spectrum" },
    { text: "9 execution algorithms", detail: "TWAP, VWAP, SOR, Almgren-Chriss + more" },
  ],
  checkpoint: "All three services can onboard clients today. The bottleneck is commercial prioritisation, not engineering.",
}
```

---

## Slide 8 — Three Services

**Renderer:** `packaging` (existing — no changes needed, just 3 cards instead of 6)

### Layout

```
┌─────────────────────────────────────────────────────┐
│ Three Commercial Wrappers, One System               │
│ ─────────────────────────────────────               │
│ Clients start where it fits. The system underneath  │
│ is the same.                                        │
│                                                     │
│ ┌───────────────┐ ┌───────────────┐ ┌─────────────┐ │
│ │ Trading       │ │ Investment    │ │ Regulatory  │ │
│ │ Platform as   │ │ Management   │ │ Umbrella    │ │
│ │ a Service     │ │               │ │             │ │
│ │               │ │               │ │             │ │
│ │ [Instrmts]    │ │ [Decision]    │ │ [Governce]  │ │
│ │ [Research]    │ │ [Execution]   │ │             │ │
│ │ [Decision]    │ │ [Governance]  │ │             │ │
│ │ [Execution]   │ │               │ │             │ │
│ │ [Governance]  │ │               │ │             │ │
│ │               │ │               │ │             │ │
│ │ Bespoke acces │ │ We run capital│ │ FCA AR      │ │
│ │ from data     │ │ $7.5M AUM    │ │ services.   │ │
│ │ feeds to full │ │ across two    │ │ Compliance, │ │
│ │ platform.     │ │ mandates.     │ │ MLRO, MiFID │ │
│ │ Same system,  │ │ Lower-yield  │ │ II. 1 client│ │
│ │ configurable  │ │ = lower fees. │ │ live, 3 in  │ │
│ │ scope.        │ │               │ │ pipeline.   │ │
│ │               │ │               │ │             │ │
│ │ Subscription  │ │ 20-40% perf   │ │ Onboarding  │ │
│ │ — scoped to   │ │ (strategy-    │ │ fee +       │ │
│ │ client need   │ │ dependent)    │ │ monthly     │ │
│ │               │ │               │ │ retainer    │ │
│ └───────────────┘ └───────────────┘ └─────────────┘ │
│                                                     │
│ Three wrappers. One system. An AR client who needs  │
│ execution uses the same algos. An IM client who     │
│ outgrows managed mandates graduates to platform.    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Data

```ts
{
  id: 8,
  type: "packaging",
  title: "Three Commercial Wrappers, One System",
  subtitle: "Clients start where it fits. The system underneath is the same.",
  services: [
    {
      name: "Trading Platform as a Service",
      stages: ["Instruments & Data", "Research", "Decision", "Execution", "Governance"],
      model: "Subscription — scoped to client need",
      desc: "Bespoke access from data feeds to research to the full trading platform. Same system, configurable scope.",
    },
    {
      name: "Investment Management",
      stages: ["Decision", "Execution", "Governance"],
      model: "20-40% performance (strategy-dependent)",
      desc: "We run capital. $7.5M AUM across two mandates. Lower-yielding strategies carry lower fees.",
    },
    {
      name: "Regulatory Umbrella",
      stages: ["Governance"],
      model: "Onboarding fee + monthly retainer",
      desc: "FCA Appointed Representative services. Compliance, MLRO, MiFID II reporting. 1 client live, 3 in pipeline.",
    },
  ],
  note: "Three wrappers. One system. An AR client who needs execution uses the same algos. An IM client who outgrows managed mandates graduates to platform access.",
}
```

---

## Slide 9 — The Flywheel

**Renderer:** `flywheel` (existing — no changes needed to renderer)

### Layout

```
┌─────────────────────────────────────────────────────┐
│ Why One Sale Leads to Others                        │
│ ─────────────────────────────                       │
│ The relationship deepens naturally because every    │
│ step uses the same system.                          │
│                                                     │
│ ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐  ┌─────┐│
│ │ Data │ → │Resrch│ → │ Live │ → │ Full │→ │Mngd ││
│ │      │   │      │   │Tradng│   │Platfm│  │/ AR ││
│ │entry │   │valid-│   │same  │   │compl.│  │we   ││
│ │point │   │ate   │   │code, │   │oprtng│  │run  ││
│ │ (●)  │   │ideas │   │live  │   │layer │  │it(●)││
│ └──────┘   └──────┘   └──────┘   └──────┘  └─────┘│
│         Regulatory coverage spans all stages        │
│                                                     │
│ ┌─────────────────────┐ ┌─────────────────────────┐ │
│ │                     │ │ CROSS-SELL EXAMPLES      │ │
│ │ The critical        │ │                         │ │
│ │ conversion is       │ │ → Data subscriber       │ │
│ │ research to live.   │ │   discovers signal      │ │
│ │ On most platforms,  │ │   quality → backtesting │ │
│ │ that transition     │ │                         │ │
│ │ requires a rewrite. │ │ → Backtester validates  │ │
│ │ On ours, it is a    │ │   edge → promotes to    │ │
│ │ configuration       │ │   live (config change)  │ │
│ │ change — same data, │ │                         │ │
│ │ same features, same │ │ → Live trader scales →  │ │
│ │ risk controls.      │ │   needs regulatory      │ │
│ │                     │ │   coverage              │ │
│ │ That continuity is  │ │                         │ │
│ │ what makes the      │ │ → AR client grows AUM → │ │
│ │ platform difficult  │ │   becomes IM client     │ │
│ │ to leave.           │ │                         │ │
│ └─────────────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Data

```ts
{
  id: 9,
  type: "flywheel",
  title: "Why One Sale Leads to Others",
  subtitle: "The relationship deepens naturally because every step uses the same system.",
  funnel: [
    { name: "Data", sub: "entry point", active: true },
    { name: "Research", sub: "validate ideas", active: false },
    { name: "Live Trading", sub: "same code, live capital", active: false },
    { name: "Full Platform", sub: "complete operating layer", active: false },
    { name: "Managed / AR", sub: "we run or regulate it", active: true },
  ],
  examples: [
    "Data subscriber discovers signal quality → starts backtesting",
    "Backtester validates edge → promotes to live (config change)",
    "Live trader scales → needs regulatory coverage",
    "AR client grows AUM → becomes investment management client",
  ],
}
```

---

## Slide 10 — The Ask

**Renderer:** `ask` (existing — no changes needed to renderer)

### Layout

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│              What Fits Your Network                 │
│              ← gradient text, 5xl, centred →        │
│                                                     │
│     Everything we've shown is shippable. The        │
│     question is which service resonates with the    │
│     people you work with — and what they'd need     │
│     to see to move.                                 │
│              ← muted, centred, max-w-2xl →          │
│                                                     │
│         ════════════════════                         │
│                                                     │
│ ┌───────────────┐ ┌───────────────┐ ┌─────────────┐ │
│ │ INVESTMENT    │ │ TRADING       │ │ REGULATORY  │ │
│ │ MANAGEMENT    │ │ PLATFORM      │ │ UMBRELLA    │ │
│ │               │ │ AS A SERVICE  │ │             │ │
│ │ → Current     │ │               │ │ → Ready     │ │
│ │   strategies: │ │ → DeFi client │ │   today     │ │
│ │   ready today │ │   deployment: │ │   — 1 client│ │
│ │               │ │   within 1    │ │   live, 3   │ │
│ │ → Additional  │ │   month       │ │   in pipe   │ │
│ │   strategies: │ │               │ │             │ │
│ │   within 2    │ │ → Broader     │ │ → Who needs │ │
│ │   months      │ │   access:     │ │   FCA covr? │ │
│ │               │ │   within 2    │ │             │ │
│ │ → Who in your │ │   months      │ │ → What      │ │
│ │   network     │ │               │ │   would     │ │
│ │   allocates   │ │ → Who needs   │ │   move them │ │
│ │   to alt      │ │   infra but   │ │   — pricing,│ │
│ │   strategies? │ │   doesn't     │ │   scope,    │ │
│ │               │ │   want to     │ │   speed?    │ │
│ │ → What would  │ │   build it?   │ │             │ │
│ │   they need?  │ │               │ │             │ │
│ │               │ │ → What would  │ │             │ │
│ │               │ │   land — data │ │             │ │
│ │               │ │   only, full  │ │             │ │
│ │               │ │   demo, spec. │ │             │ │
│ │               │ │   asset class?│ │             │ │
│ └───────────────┘ └───────────────┘ └─────────────┘ │
│                                                     │
│ Odum Research Ltd | FCA 975797 |                    │
│ ikenna@odum-research.com | odum-research.com        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Data

```ts
{
  id: 10,
  type: "ask",
  title: "What Fits Your Network",
  subtitle: "Everything we've shown is shippable. The question is which service resonates with the people you work with — and what they'd need to see to move.",
  asks: [
    {
      title: "Investment Management",
      items: [
        "Current strategies (CeFi, BTC): ready today",
        "Additional strategies, new asset classes: within 2 months",
        "Who in your network allocates to alternative strategies?",
        "What would they need — track record, reporting format, minimum ticket?",
      ],
    },
    {
      title: "Trading Platform as a Service",
      items: [
        "DeFi client deployment: within 1 month",
        "Broader platform access: within 2 months",
        "Who needs trading infrastructure but doesn't want to build it?",
        "What would land — data-only entry, full demo, specific asset class?",
      ],
    },
    {
      title: "Regulatory Umbrella",
      items: [
        "Ready today — 1 client live, 3 in pipeline",
        "Who in your network is entering UK regulation or needs FCA coverage?",
        "What would move them — pricing, scope, onboarding speed?",
      ],
    },
  ],
  contact: "ikenna@odum-research.com",
}
```

---

## Files to Create / Modify

| File                                  | Action                                               | What changes                                                                                                                                                                                                      |
| ------------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `board-presentation-data.ts`          | **Rewrite**                                          | All slide data as specified above. Update `VENUE_LIST` (remove CBOT/COMEX/NYMEX, keep grouped).                                                                                                                   |
| `board-presentation-slide-part-a.tsx` | **Add** `breadth-matrix` renderer                    | New grid/table component for slide 5. Keep `cover`, `doctrine`, `lifecycle-new`, `packaging`, `problem` renderers.                                                                                                |
| `board-presentation-slide-part-b.tsx` | **Add** `strategies` renderer, **modify** `traction` | New table component for slide 6. Modify traction to support 3 columns via `launchReady` field. Keep `flywheel`, `ask`, `operations`, `revenue`, `moat`, `coverage`, `demo` renderers (unused types are harmless). |
| `board-presentation-widgets.tsx`      | **No changes**                                       | `StatusBadge` and `MarketNode` components still work.                                                                                                                                                             |
| `board-presentation-client.tsx`       | **No changes**                                       | Navigation, fullscreen, autoplay all work with any number of slides.                                                                                                                                              |
