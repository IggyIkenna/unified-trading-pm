---
doc_type: codex-ssot
title: DART Entry Points — Three Commercial Paths
summary:
  Maps the three practical DART commercial paths (reporting-only visibility, signals-only downstream, full pipeline) to
  the rule-04 origin×depth matrix cells, block compositions, and buyer shapes; includes named 2026-pipeline worked
  examples (Elysium signals-only, Desmond combined, India Options NOT-DART).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [sales, admin]
tags: [commercial-model, dart, pricing, building-blocks, elysium, im, signal-leasing]
related:
  [
    /codex/14-customer-journeys/commercial-model/building-block-packaging.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/commercial-model/fixed-vs-variable-commercials.md,
    /codex/14-customer-journeys/commercial-model/exclusivity-and-noncompete.md,
    /codex/14-customer-journeys/commercial-model/im-profit-share-structures.md,
    /codex/14-customer-journeys/commercial-model/signal-leasing.md,
  ]
created: 2026-04-20
authoritative_for: [three DART commercial entry paths (reporting-only / signals-only / full-pipeline)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/commercial-model/README.md,
    /codex/14-customer-journeys/commercial-model/building-block-packaging.md,
    /codex/14-customer-journeys/commercial-model/exclusivity-and-noncompete.md,
    /codex/14-customer-journeys/commercial-model/fixed-vs-variable-commercials.md,
    /codex/14-customer-journeys/commercial-model/im-vs-reg-reporting-logic.md,
    /codex/14-customer-journeys/demo-ops/demo-decision-matrix.md,
    /codex/14-customer-journeys/demo-ops/post-demo-followup-orchestration.md,
  ]
owner:
last_reviewed:
code_refs:
---

# DART Entry Points — Three Commercial Paths

> Opens with the DART rule-09 expansion. Maps the three practical DART commercial paths — reporting-only visibility,
> signals-only downstream, full pipeline — to the rule-04 matrix cells, names who buys each, and what block composition
> each requires.

**Rule sources:** [rule 04](../_ssot-rules/04-dart-commercial-axes.md),
[rule 05](../_ssot-rules/05-building-block-dimensions.md),
[rule 09](../_ssot-rules/09-internal-commercial-oneliners.md),
[rule 10](../_ssot-rules/10-strategy-instruction-schema-principles.md)

## Rule 09 expansion

DART is the set of services Odum uses to build, research, promote, execute, and monitor its own systematic strategies,
packaged for client use. Clients who operate their own strategies can plug their signals into Odum's execution and
reporting stack, or they can use the full research and promotion pipeline. The underlying components are the same as
Odum's internal operation — one system, partitioned views.

## The three practical paths

Rule 04 resolves every DART conversation on two axes: strategy origin × stack depth. The 2 × 3 matrix collapses to three
practical commercial paths. Each path has a distinct block composition, a distinct demo profile, and a distinct prospect
shape.

### Path 1 — Reporting-only visibility

**Matrix cell:** `(Odum, reporting-only)` — or sometimes `(Client, reporting-only)` for emerging managers.

**What the prospect wants:** Visibility into Odum-run strategies' performance (allocator) or into their own firm's
regulated activity (Reg Umbrella). No execution integration, no research surface, no strategy authoring.

**Commercial home:** This is **not DART commercially.** Route to IM or Reg Umbrella. DART pricing and DART demo profiles
do not apply. The prospect sees [`im-decision-journey.md`](../experience/im-decision-journey.md) or
[`regulatory-umbrella-briefing.md`](../experience/regulatory-umbrella-briefing.md).

**Typical block set:** reporting core (block 1) + IM allocator reporting (block 3) OR regulatory umbrella reporting
(block 2) + selected analytics packs (block 11).

**Typical buyer:** Family office, institutional allocator, emerging manager under regulated cover.

### Path 2 — Signals-only DART (downstream integration)

**Matrix cell:** `(Client, downstream)`.

**What the prospect wants:** Keep their strategy generation upstream (IP stays theirs). Buy Odum's execution, trading
terminal, position monitoring, reconciliation, reporting, and scoped analytics. Does NOT buy the research / promote
pipeline.

**Commercial home:** DART briefing pb2b. Rule 10 fit-check runs before demo.
[`../shared-core/instruction-schema-fit-and-package-boundaries.md`](../shared-core/instruction-schema-fit-and-package-boundaries.md)
is the fit-check implementation map.

**Typical block set:** reporting core (1) + strategy-service entry (4) + instructions integration (5) + execution layer
(7) + venue packs (8) × N + chain packs (9) × N + instrument-type packs (10) × N + optional analytics packs (11).

**Does NOT include:** research / promote pipeline (block 6). Rule 04 enforcement.

**Typical buyer:** DeFi-native fund with a working signals flow hitting operational limits (venue onboarding, treasury
rebalancing, reg cover, monitoring fragility). Prop firm or single-strategy manager wanting Odum's downstream stack
without the research layer.

**Tier shape:** Typically Tier B on sticky blocks (reporting, strategy-service, instructions integration); Tier A on
marginal venue / chain / instrument-type packs.

**Upgrade path:** signals-only → full DART is a formal commercial event (rule 10 enforcement). Not a bolt-on.

### Path 3 — Full DART pipeline

**Matrix cell:** `(Client, full-pipeline)` or `(Odum, full-pipeline)`.

**What the prospect wants:** The deeper stack. Research surface to interrogate historical data, backtest candidates,
promote through paper to live, execute, monitor, report. Strategy origin is either the client (they build) or Odum (Odum
built, Odum strategy IP licensed to the client).

**Commercial home:** DART briefing pb2b (both variants walked; the fit-check resolves which branch).

**Typical block set:** Everything in signals-only plus research / promote pipeline (block 6) plus expanded analytics
(block 11). For `(Odum, full)` engagements, add the Odum strategy exposure premium.

**Typical buyer:** Fund wanting to build and run strategies on Odum infrastructure top-to-bottom. Prop firm buying Odum
strategy IP with the full stack.

**Tier shape:** Tier B on the core blocks (reporting, strategy-service, instructions integration, research, promote,
execution, primary venue / chain / instrument packs); Tier A possible on marginal packs.

## Who buys what — worked examples

### Example A — Signals-only path

**Prospect:** DeFi stat-arb fund running their own strategy on their own infrastructure. Hits operational limits on
venue onboarding and cross-chain treasury rebalancing.

**Resolution:** `(Client, downstream)` → signals-only DART.

**Block composition:**

- reporting core (Tier B)
- strategy-service entry (Tier B)
- instructions integration (Tier B, standard schema depth — see
  [`../shared-core/instruction-schema-fit-and-package-boundaries.md`](../shared-core/instruction-schema-fit-and-package-boundaries.md))
- execution layer (Tier B)
- venue packs × 2 primary CeFi venues (Tier B), × 1 marginal (Tier A)
- chain packs × 2 primary DeFi chains (Tier A — usage-variable)
- instrument-type packs × 2 (perps + spot; Tier A)

### Example B — Full DART path

**Prospect:** Multi-manager hedge fund wanting to build new systematic strategies on Odum infrastructure.

**Resolution:** `(Client, full-pipeline)` → full DART.

**Block composition:**

- reporting core (Tier B)
- strategy-service entry (Tier B)
- instructions integration — not always required for full-pipeline (research-originated flows); depends on strategy
  shape
- research / promote pipeline (Tier B)
- execution layer (Tier B)
- venue / chain / instrument packs (mixed tiers per scope)
- analytics packs × 2 (Tier A)

### Example C — Full DART + Odum strategy premium

**Prospect:** Institutional prop firm wanting to run Odum-developed strategies on their own capital.

**Resolution:** `(Odum, full-pipeline)` → full DART + Odum strategy exposure.

**Block composition:** Full DART set (as in Example B) plus Odum strategy exposure premium. Premium expressed as Tier B
uplift.

### Example D — Combined Reg Umbrella + signals-only DART

**Prospect:** Emerging manager launching a strategy with regulated cover and downstream execution.

**Resolution:** Two cells: `(Client, downstream)` signals-only DART + Reg Umbrella engagement.

**Block composition:** Two commercial engagements with shared infrastructure.

- Reg Umbrella side: reporting core + regulatory umbrella reporting + execution layer + venue packs + instrument-type
  packs.
- Signals-only DART side: reporting core (shared) + strategy-service entry + instructions integration + scoped
  analytics.

Pricing combines blocks across both engagements; the client receives one invoice per engagement, not one bundled.

## Named-client worked examples (2026 pipeline)

These are the three named 2026-pipeline engagements and how they resolve against the rule-04 matrix. Two are DART paths
(Elysium, Desmond); India Options is explicitly NOT DART and is included at the end as a pointer.

### Worked example — Elysium (signals-only DART, DeFi staked-basis)

**Matrix cell:** `(Client, downstream)` → signals-only DART.

**Strategy scope:** DeFi staked-basis (carry-staked-basis archetype) on Drift perps plus staked ETH/SOL collateral.
Client keeps strategy IP + decision logic upstream; Odum provides the downstream execution, cross-chain treasury
management, reconciliation, reporting, analytics.

**Commercial mechanic:** Profit-share **replaces** block pricing post go-live. Onboarding is a fixed
$125k (partially
paid; remaining $35k as of April 2026). Once live, Odum takes **30% of Elysium's fees/returns** from the
strategy they operate via our stack. See [`im-profit-share-structures.md`](im-profit-share-structures.md) §Elysium
framing — rationale: client preferred upside-aligned mechanics over flat Tier B monthly.

**Capital phases:**

- **Phase A** ($500k own capital, Jun 2026 go-live): proves out the strategy on Elysium's own book.
- **Phase B** ($5-10M via their downstream client, H2 2026): scales once Phase A's 3-month track record is in.

**Block composition baseline (for reference, before profit-share replaces it):**

- Reporting core (Tier B)
- Strategy-service entry × 1 (Tier B)
- Instructions integration — standard depth (Tier B)
- Execution layer (Tier B)
- Chain packs × 4 (Ethereum L1 / Arbitrum / Base / Solana; Tier B)
- Instrument-type packs × 2 (spot + perp; Tier B)
- Analytics pack × 1 (execution quality; Tier A)

Equivalent Tier B: ~£24k/mo (see [`../shared-core/dart-pricing-axes.md`](../shared-core/dart-pricing-axes.md) §Worked
example — Elysium Phase A). Actual commercial = profit-share replaces this.

**2026 revenue target:**

- **Conservative**: $125k total 2026 (onboarding + baseline profit-share).
- **Aspirational**: $200-230k total 2026 with MEV + Solana L1 expansion + recursive-staking upsells added through Q3/Q4.

**Does NOT include:** research / promote pipeline (block 6). Rule 04 boundary preserved even though the commercial
mechanic is profit-share-shaped.

### Worked example — Desmond (prospective, Reg Umbrella + signals-only DART combined)

**Matrix cell:** Two cells: `(Client, downstream)` signals-only DART + Reg Umbrella engagement. Composed per Example D
above but with a named prospect profile.

**Strategy scope:** Perp-funding arbitrage on CeFi perps — Binance-perp, Hyperliquid, possibly Bybit + OKX depending on
exchange onboarding outcomes. Strategy-family commodity-archetype (perp-funding arb). Client keeps strategy IP upstream.

**Commercial mechanic:** Two-engagement bundle with shared infrastructure.

- **Reg Umbrella side**: reporting core + regulatory umbrella reporting + execution layer + venue packs (2-4 CeFi perp
  venues) + instrument-type packs (perps). ~£12k/mo Tier B.
- **Signals-only DART side**: reporting core (shared) + strategy-service entry × 1 + instructions integration (standard
  depth) + scoped execution analytics. ~£10k/mo Tier B.
- **Combined Tier B monthly**: **~£22k/mo** (Reg Umbrella £12k + signals-only DART £10k).
- **Upfront fee**: **£25-50k range** — £25k worst-case / £50k best-case. Covers two-engagement onboarding, per-venue
  provisioning, Reg Umbrella compliance setup, signals-integration build.

**Start date:** **May 2026 earliest** (calendar constraint on client side).

**IP-power tier:** Commodity archetype (perp-funding arb on liquid CeFi perps). Standard 20-30% exclusivity uplift
available if Desmond wants scoped exclusivity on their specific venue set; no special premium above the commodity band
because the strategy family is not uniquely differentiated. See
[`exclusivity-and-noncompete.md`](exclusivity-and-noncompete.md) §IP-power tier anchors.

**Revenue risk:** If Desmond slips past May, revenue slip is ~£22k-57k per month of delay (monthly + pro-rata upfront);
the overall 2026 cash plan absorbs a 2-3 month slip without stress.

### Worked example — India Options (NOT DART — `(Odum, full-pipeline)` IM engagement)

**Matrix cell:** `(Odum, full-pipeline)` — this is **NOT a DART engagement**. Included here to make the routing explicit
and prevent accidental DART-framing in sales conversations.

**Strategy scope:** Odum-developed delta trading on NSE (Indian) options. Odum brings the strategy IP, the new-venue
integration (NSE options adapter + clearing + margin), and the execution. Client allocates capital.

**Commercial mechanic:** IM-framework, not DART Tier A/B blocks.

- **$100k upfront onboarding** (covers NSE options integration + options-specific infrastructure; amortised over 3
  months; commercially framed as block 13 custom premium per [`pricing-building-blocks.md`](pricing-building-blocks.md)
  §India Options special structure).
- **Ongoing**: standard **30-35% performance-share** + platform-fee client choice (Option A +5% perf uplift OR Option B
  $500/mo flat).
- **Allocation target**: $5-10M year-1 expected (gated on S&P ML signal proving out first).

**Routing note:** If a prospect approaches mentioning Indian options, route the conversation to
[`im-profit-share-structures.md`](im-profit-share-structures.md) §India Options — NOT to DART path resolution. The cell
`(Odum, full-pipeline)` still resolves to an IM commercial path when Odum brings the strategy IP and manages the
capital; DART path resolution is for clients doing their own research / their own signal generation.

See [`im-profit-share-structures.md`](im-profit-share-structures.md) for the full IM mechanic.

## What each path does NOT include

Rule-04 enforcement keeps these boundaries clean:

- **Signals-only does NOT include research / promote pipeline** (block 6). Clients wanting that upgrade to full DART.
- **Reporting-only does NOT include execution integration.** Reporting-only is IM / Reg Umbrella commercially;
  execution-service integration is DART or Reg Umbrella specifically.
- **Reporting-only does NOT include strategy-service entry** (block 4). That is a DART block.
- **Full DART pricing applies even when the client doesn't generate their own strategies** — the `(Odum, full)` cell.
  Don't let "I'll take your strategy but skip your research stack" become a lighter package.

## Cross-references

- [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md)
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md)
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md)
- [rule 09 — internal commercial one-liners](../_ssot-rules/09-internal-commercial-oneliners.md)
- [rule 10 — strategy instruction schema](../_ssot-rules/10-strategy-instruction-schema-principles.md)
- [../shared-core/strategy-origin-vs-stack-depth.md](../shared-core/strategy-origin-vs-stack-depth.md)
- [../shared-core/instruction-schema-fit-and-package-boundaries.md](../shared-core/instruction-schema-fit-and-package-boundaries.md)
- [building-block-packaging.md](building-block-packaging.md) — full block × package matrix
- [pricing-building-blocks.md](pricing-building-blocks.md) — pricing structure (TBD numbers)
- [fixed-vs-variable-commercials.md](fixed-vs-variable-commercials.md) — Tier A vs Tier B
- [exclusivity-and-noncompete.md](exclusivity-and-noncompete.md) — Tier B modifiers
- [../experience/dart-briefing.md](../experience/dart-briefing.md) — pb2b briefing
- [../experience/dart-demo.md](../experience/dart-demo.md) — pb3c demo
- [im-profit-share-structures.md](im-profit-share-structures.md) — IM mechanics (India Options, CME asymmetric, standard
  perf-share + platform-fee choice)
- [signal-leasing.md](signal-leasing.md) — fourth commercial path
- [../shared-core/dart-pricing-axes.md](../shared-core/dart-pricing-axes.md) — signals-only vs full-DART anchor tables,
  Elysium worked example
