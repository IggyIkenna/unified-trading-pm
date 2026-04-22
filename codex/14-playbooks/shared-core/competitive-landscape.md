---
scope: [sales, admin]
---

# Competitive landscape — Market Deep Dive (internal)

> Internal SSOT for how Odum positions against the rest of the stack. Sales, marketing, and PR read this before any
> external conversation, pitch deck, or press piece that references the competitive set. This file is **internal** —
> competitor names do not appear on public pages (rule 02 line 74 stands). External copy uses the "unified layer vs
> fragmented stack" frame without naming firms.

**Scope:** sales, marketing, PR, senior admin. **Derivation:**
[rule 02 (tone and posture)](../_ssot-rules/02-tone-and-posture.md),
[rule 03 (same-system principle)](../_ssot-rules/03-same-system-principle.md),
[rule 04 (DART commercial axes)](../_ssot-rules/04-dart-commercial-axes.md),
[rule 09 (internal commercial one-liners)](../_ssot-rules/09-internal-commercial-oneliners.md).

## Core frame

The trading-infrastructure market is sold in **layers**. Most buyers assemble a stack by picking a specialist for each
layer and stitching them together. Odum's advantage is not that any single layer beats its specialist on that
specialist's home lane — several of them are genuinely better there. The advantage is that Odum delivers **one operating
layer** spanning the layers the market usually sells separately, so the buyer stops paying the stitching tax (duplicated
workflows, inconsistent taxonomies, vendor handoffs between research / execution / reporting).

Posture: **partner-first, not conquest-first.** Several of the named firms below are in Odum's own supplier stack. Never
frame externally as "we beat X". Frame externally as "we eliminate the stitching".

## The six layers of fragmentation

Each layer names the typical specialists and Odum's relationship to that layer.

### 1. Data and market intelligence

**Specialists:** Amberdata, Tardis, Databento.

Best-in-class normalised feeds + derivatives / DeFi analytics. Odum **sources from** this tier; does not compete. Any
public framing that suggests Odum competes on raw market data is wrong and violates
[rule 07 (data licensing boundaries)](../_ssot-rules/07-data-licensing-boundaries.md).

### 2. Research, backtest, strategy development

**Specialists:** Deltix QuantOffice, QuantConnect / LEAN.

Strong quant research environments. Odum extends further than either: strategies built on DART run against the same live
execution + reporting layers Odum uses for its own capital, across five asset categories (crypto, DeFi, TradFi, sports,
prediction), without migration between backtest and live. The batch = live architectural principle is the underlying
mechanism — not a slogan.

### 3. Execution and smart order routing

**Specialists:** Talos, CoinRoutes, Versify, Aplo, Deltix CryptoCortex, Interactive Brokers.

Institutional execution + venue connectivity. Odum integrates with, does not replace — the differentiator is that
execution sits inside the same operating system as research, risk, and reporting. Buyers using a pure-execution vendor
still have to stitch it into their research and reporting environments themselves. DART clients do not.

### 4. Charting and terminal UX

**Specialist:** TradingView.

Best charting UX. Odum still uses TradingView for some own charts. TradingView never tried to be an operating layer;
naming it as a comp is a category error externally and should only appear as a reference point in internal design
conversations.

### 5. Open-source automation

**Specialist:** Hummingbot.

Excellent crypto-market-making automation framework. Different audience — operators who run their own infrastructure and
want a toolkit, not a managed operating layer. Not a like-for-like comp for DART or IM.

### 6. Regulatory platforms / hosted-manager

**Specialists:** Waystone, FundRock.

Deep fund-structure + AIFM / ManCo services, respected in the institutional-allocator space. Odum's Regulatory Umbrella
is narrower: a quick route for trading firms to operate regulated activity under Odum's FCA permissions, on the same
operating stack as IM clients. Waystone-scale multi-jurisdictional ManCo is not the frame; "trading firm wants regulated
cover without their own FCA application" is.

## Odum's combined shape

Odum sits **across** layers the market usually sells separately:

- regulated coverage
- investment-management reporting
- strategy and research operating system
- downstream execution + operating control
- one taxonomy across five categories (crypto, DeFi, TradFi, sports, prediction)
- one unified experience across the full trade lifecycle

This combination is the thing worth protecting in messaging. Any one of the six bullets, in isolation, has a stronger
specialist.

## Advantage framing (canonical language)

**Do say** (internal and external): "unified layer vs fragmented stack". "We eliminate the vendor stitching, duplicated
workflows, and inconsistent UX that come with assembling a stack yourself." "Same system Odum runs its own capital on."

**Do not say** (internal or external): "We beat [specialist] on their home lane." (Often not true; always bad posture.)
"Best-in-class [any layer]." (Violates [rule 02](../_ssot-rules/02-tone-and-posture.md).) "[Specialist] is outdated /
legacy / slow." (Disparagement — rule 02 line 74.)

## Comp tiers

Internal shorthand for how close each firm is to Odum's combined shape. Tier labels appear in internal notes and CRM
comp tags; they never appear externally.

### Tier A — closest combined-shape comps

Firms whose product footprint overlaps multiple Odum layers simultaneously.

- **Deltix** — research-to-execution + CryptoCortex crypto extension. Overlaps research + execution layers.
- **Talos** — institutional digital-asset lifecycle. Overlaps execution + ops + some reporting.
- **CoinRoutes** — execution + order-handling infrastructure.
- **Versify** — institutional digital-asset operating stack.

### Tier B — partial / single-layer comps

Firms that own one layer strongly but do not span the combined shape.

- **Amberdata** — data layer (layer 1).
- **QuantConnect** — research layer (layer 2).
- **Interactive Brokers** — execution + brokerage (layer 3).
- **TradingView** — charting (layer 4).
- **Hummingbot** — automation framework (layer 5).
- **Aplo** — execution (layer 3).

### Tier C — tone-only references

Firms Odum looks to for voice / posture rather than feature overlap. See rule 02.

- **[axis.to](https://www.axis.to/)** — restrained institutional register.
- **[podlabs.xyz](https://podlabs.xyz/)** — operating-team voice, specificity over puffery.
- **Nurp** — founder-led niche reference (used selectively).

### Umbrella / IM comp set — different category

- **Waystone** — multi-jurisdictional ManCo / AIFM. Tone reference for the fund-services side.
- **FundRock** — hosted AIFM services. Same tone bucket.

Regulatory Umbrella comparison lives in this set, not in the DART / execution comp set above.

## PR and tone guidance

| Surface                                      | Tone reference                                                      |
| -------------------------------------------- | ------------------------------------------------------------------- |
| DART side (research / execution / reporting) | Talos / Deltix / CoinRoutes / Versify — institutional infra voice   |
| Umbrella / IM side                           | Waystone / FundRock — fund-services voice                           |
| Founder / firm story                         | axis.to / podlabs.xyz / boutiques — operating-team voice, selective |

**Founder-led niche reference** (Axis, Hummingbot, boutique operators) is useful selectively: when the piece is about
operating style, not product footprint.

## External-surface rules (hard constraints)

1. **No competitor names on public pages.** Rule 02 line 74 stands. Website, briefings (pb2 public layer), proposals,
   blog posts, LinkedIn copy — zero firm names from Tier A / Tier B / Umbrella set.
2. **Tier C tone references are fine as hyperlinks in internal docs and in founder / about-style content** where the
   reference is a voice cue, not a product comparison. Still not a claim that Odum is like them.
3. **"Unified layer vs fragmented stack"** is the canonical external frame for the combined-shape advantage. No
   competitor names needed.
4. **Partner-first.** If asked directly about a named firm (discovery call, briefing), acknowledge the firm's strength
   on its home lane (honest), explain Odum's different shape (specific), and do not disparage. Several of the firms
   above are in Odum's own supplier stack.

## Cross-references

- [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md) — banned posture (line 74), Tier C voice
  references
- [rule 03 — same-system principle](../_ssot-rules/03-same-system-principle.md) — the mechanism behind the combined
  shape
- [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md) — DART's five-path matrix
- [rule 07 — data licensing boundaries](../_ssot-rules/07-data-licensing-boundaries.md) — Odum sources from layer 1,
  does not resell
- [rule 09 — internal commercial one-liners](../_ssot-rules/09-internal-commercial-oneliners.md) — expansion pattern for
  DART / IM / Reg Umbrella
- [experience/marketing-journey.md](../experience/marketing-journey.md) — external positioning (no competitor names)
- [`_ssot-rules/09-internal-commercial-oneliners.md` § Competitive positioning table](../_ssot-rules/09-internal-commercial-oneliners.md)
  — compact per-path vendor comp table
