---
doc_type: codex-ssot
title: Exclusivity and Non-Compete — What It Means, Who Gets It
summary:
  Defines the block-12 exclusivity / non-compete premium (Tier-B-only) — the three scope axes it binds, the four
  IP-power tier anchors (20-30% commodity → 120-200% uniquely-differentiated uplift on Tier B monthly), revenue-forgone
  × margin quote method, legal framing, and leadership/legal escalation triggers.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [sales, admin]
tags: [commercial-model, exclusivity, pricing, dart, tier-b, ip-power]
related:
  [
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/commercial-model/fixed-vs-variable-commercials.md,
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/commercial-model/im-profit-share-structures.md,
    ../shared-core/dart-pricing-axes.md,
  ]
created: 2026-04-20
authoritative_for: [exclusivity / non-compete commercial premium (block 12) negotiation framing]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/_ssot-rules/05-building-block-dimensions.md,
    /codex/14-customer-journeys/commercial-model/README.md,
    /codex/14-customer-journeys/commercial-model/building-block-packaging.md,
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/commercial-model/elysium-account-trajectory-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/fixed-vs-variable-commercials.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Exclusivity and Non-Compete — What It Means, Who Gets It

> Exclusivity premium is rule 05 block 12 and rule 08 Tier-B-only modifier. This doc defines what exclusivity means at
> each tier, what the premium structure looks like, and the legal framing that carries it.

**Rule sources:** [rule 05](../_ssot-rules/05-building-block-dimensions.md) block 12,
[rule 08](../_ssot-rules/08-pricing-principles.md)

## What exclusivity is

A Tier B client pays Odum a premium above the standard Tier B monthly to restrict Odum from offering the same capability
to direct competitors for a bounded scope and term.

The "same capability" is defined by the intersection of three axes:

- **Venue / chain / instrument-type scope.** Which venue packs, chain packs, instrument-type packs.
- **Strategy family scope.** Which strategy archetypes or families the exclusivity covers.
- **Geographic / commercial scope.** Which competitor set the restriction covers (e.g., "DeFi-native stat-arb funds in
  North America" or "UCITS-regulated systematic managers in Europe").

The exclusivity applies to the **intersection** of those scopes. Odum can still serve other clients on other venue /
strategy / scope combinations.

## Why exclusivity is Tier-B-only

Rule 08: Tier A does not unlock exclusivity. The commercial logic:

1. **Revenue predictability.** Exclusivity requires Odum to forgo future revenue from a scope. The monthly-fixed Tier B
   structure aligns Odum's revenue guarantee with the forgone-revenue commitment.
2. **Usage variance on Tier A.** If the Tier A client's usage ramps slowly, Odum's compensation for the exclusivity is
   undercut by the variable billing. Tier B eliminates that risk.
3. **Commitment signalling.** A client willing to sign Tier B + exclusivity is signalling depth of commitment that Tier
   A does not carry.

## Premium structure

Exclusivity is expressed as a **percentage uplift on the Tier B fixed monthly** for the blocks the exclusivity covers.
The percentage depends on:

- **Scope breadth.** Broader scope (more venues / more instrument types / more strategy families) → higher percentage.
- **Term length.** Longer term → higher aggregate premium; per-month percentage may be flatter.
- **Competitive density.** Scopes where Odum could plausibly have many future clients → higher premium because Odum
  forgoes more.
- **Market attractiveness.** High-demand scopes carry higher premiums.

Indicative ranges are populated by finance in [`pricing-building-blocks.md`](pricing-building-blocks.md) block 12 row.
Until tightened by finance, the structure is: Tier B monthly × (1 + exclusivity_pct), where `exclusivity_pct` is a
negotiated figure anchored to the IP-power tier (see next section).

## IP-power tier anchors — 2026 strategy catalogue

Exclusivity premium is anchored to a four-tier ladder based on strategy scarcity and venue-access difficulty. The
percentages below are **anchor ranges** — each specific quote still computes `revenue-forgone × margin multiplier` over
the exclusivity term, which may land higher or lower than the anchor depending on the scope negotiated.

Cross-reference [`../shared-core/dart-pricing-axes.md`](../shared-core/dart-pricing-axes.md) §IP-power exclusivity tiers
(block 12) — same anchor ranges, same worked examples; this doc provides the commercial negotiation framing,
`dart-pricing-axes.md` provides the pricing-model framing.

### Tier 1 — Commodity archetype (20-30% uplift)

Strategies where the archetype is well-known and multiple external competitors could in principle offer a similar
capability. Exclusivity limits Odum's ability to serve direct competitors on the same venue × strategy-family scope, but
the scope is not alpha-defining.

**Anchor uplift on Tier B monthly: 20-30%.**

Examples from the 2026 catalogue:

- **ML directional on liquid CeFi perps** (BTC / ETH perp on Binance / Coinbase / Hyperliquid) — the archetype and
  instrument set are widely covered.
- **Perp-funding arbitrage on CeFi perps** (Desmond's strategy scope — Binance-perp / Hyperliquid / Bybit / OKX) —
  funding-arb is a commodity archetype with many implementations; Odum's edge is operational execution quality, not
  alpha uniqueness.

### Tier 2 — Specialised venue + archetype combo (50-80% uplift)

Strategies that combine a non-commodity archetype with a specialised venue. The archetype by itself might be
commoditised elsewhere, but the specific venue integration + execution pattern is scarce.

**Anchor uplift on Tier B monthly: 50-80%.**

Examples from the 2026 catalogue:

- **Hyperliquid market-making** — market-making is a widely-known archetype, but Hyperliquid's venue mechanics (on-chain
  perp DEX with discrete auction matching, rebate structure, latency-sensitive MM) require specialised integration.
- **Drift carry-basis** — carry-basis is a known archetype, but Drift's Solana-L1 specifics + the staked-basis
  collateral overlay (Elysium's scope) are specialised enough to warrant tier-2 exclusivity pricing.

### Tier 3 — Scarce venue access (80-120% uplift)

Strategies where the venue itself is difficult to access (new jurisdiction, unusual clearing, specialised legal entity
requirement). Archetype may or may not be commoditised; venue access is the scarce resource.

**Anchor uplift on Tier B monthly: 80-120%.**

Examples from the 2026 catalogue:

- **Indian options NSE delta trading** — NSE options access requires Indian regulatory + clearing + margin
  infrastructure that is hard to stand up. Even a commoditised delta-trading archetype becomes scarce when tied to NSE
  venue access. Onboarding premium is already embedded in the India Options $100k onboarding fee (see
  [`im-profit-share-structures.md`](im-profit-share-structures.md) §India Options); block-12 exclusivity stacks on top
  of that if a client wants to lock Odum out of offering NSE options access to competitors.
- **Kalshi prediction markets** — regulated US event-contract venue; integration is not commoditised and Kalshi's
  operating rules are specialised.

### Tier 4 — Uniquely differentiated multi-leg strategy (120-200% uplift)

Strategies where the multi-leg structure, signal composition, or execution pathway is uniquely Odum-differentiated —
competitors could not easily replicate even with venue access. Alpha is structural, not just operational.

**Anchor uplift on Tier B monthly: 120-200%.**

Examples from the 2026 catalogue:

- **Custom DeFi stat-arb** — client-specific multi-leg configurations on DeFi perps / spot / staked-basis overlays that
  compose Odum's execution infrastructure in a non-replicable way.
- **Novel event-driven multi-leg** — event-settled strategies that compose multiple archetypes (e.g., macro-calendar
  event-driven + sports fixture-settled + prediction market convergence) in a way that is uniquely Odum.

### How to apply the tier anchors in a quote

1. Identify the strategy family + venue combo under exclusivity. Match to the tier above.
2. Compute Odum's estimated revenue forgone from NOT serving the same scope to a direct competitor over the exclusivity
   term.
3. Compute revenue-forgone × margin multiplier (1.5-2× typical).
4. Compare against the anchor uplift × Tier B monthly base. The higher of the two is the negotiating position; the
   anchor is a floor for commodity-tier scopes and a ceiling-check for ambitious scopes.
5. Document the specific forgone-revenue estimate inline in the quote's exclusivity line so the client sees the
   reasoning.

## Legal framing

The exclusivity is expressed in the commercial contract as a **non-compete clause** with specific bounded terms:

- **Scope.** Named venues, chains, instrument types, strategy families, geographic / commercial perimeter.
- **Term.** Named number of months, typically aligned with or extending the base engagement term.
- **Carve-outs.** Explicit carve-outs for existing Odum clients on overlapping scopes, for Odum's internal strategies,
  and for any scopes Odum has already committed to prior engagements.
- **Termination triggers.** What happens if the client terminates early (does the exclusivity unwind? a negotiated
  tail?).
- **Breach and remedies.** What counts as a breach on Odum's side and what the remedy is.

Legal reviews every exclusivity clause before signing. The clauses are not form clauses; each is negotiated to the
scope.

## Custom solution premium (block 13) — related but distinct

Rule 05 block 13 is a separate modifier: custom solution premium. It covers bespoke feature development or non-standard
integrations specific to one client. Like block 12, it is Tier-B-only.

Block 13 does NOT imply exclusivity — it implies custom build. A client can buy block 13 (custom feature) without block
12 (exclusivity) or vice versa. Some engagements carry both (custom-built feature that is also exclusive to the client's
scope).

## What exclusivity is NOT

- **Not a global monopoly.** Exclusivity is scope-bounded. Odum retains other clients on non-overlapping scopes.
- **Not a market-maker monopoly.** Multiple clients can hold exclusivity on non-overlapping scopes.
- **Not a guarantee of Odum's full attention.** Odum's operational team serves multiple clients; exclusivity is
  commercial, not operational.
- **Not a data-licence exclusivity.** Rule 07's enriched-services framing still applies. Exclusivity on a venue pack
  (block 8) is exclusivity on Odum's enriched venue integration for the scope, not exclusivity on the venue's underlying
  data feed (which Odum does not resell).
- **Not silent.** Exclusivity is a named contract clause with visible terms; it is not a handshake.

## Negotiation discipline

- **Scope the exclusivity to what the client actually needs.** A prospect asking for exclusivity on "the entire DeFi
  stack" is usually actually asking for exclusivity on their specific strategy family + venue set. Narrow-scope
  exclusivity is cheaper for them and cheaper for Odum.
- **Align term with engagement term.** Exclusivity for twelve months on a twelve-month engagement is the floor. Longer
  exclusivity requires longer base engagement or a renewed commitment.
- **Price the foregone revenue, not the optics.** The premium should reflect Odum's estimate of revenue forgone from
  other clients on the scope over the exclusivity term. It should not be priced as a status symbol.
- **Document carve-outs explicitly.** Any existing Odum client on an overlapping scope is named as a carve-out; any Odum
  internal strategy that uses the scope is named; any commitment from prior engagements is named.
- **Leadership signoff required.** Any exclusivity clause goes through leadership review before the quote is sent.

## Escalation triggers

Escalate to leadership / legal before committing to exclusivity when:

- Scope is broader than named venue / chain / instrument-type packs (e.g., "entire asset class" — too broad; scope it).
- Term is longer than 36 months (long exclusivity compounds revenue risk).
- Carve-outs are contested (prospect is asking Odum to exit an existing relationship).
- Client asks for exclusivity at Tier A (declined; route to Tier B conversation).

## Cross-references

- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) — block 12 (exclusivity) + block
  13 (custom)
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — Tier-B-only modifier rule
- [rule 07 — data licensing boundaries](../_ssot-rules/07-data-licensing-boundaries.md) — exclusivity is on Odum's
  enriched output, not on upstream data
- [pricing-building-blocks.md](pricing-building-blocks.md) — block 12 row
- [fixed-vs-variable-commercials.md](fixed-vs-variable-commercials.md) — Tier B requirement
- [dart-entry-points.md](dart-entry-points.md) — exclusivity most common on `(Odum, full)` Full DART + Odum strategy
  engagements
- [../shared-core/strategy-origin-vs-stack-depth.md](../shared-core/strategy-origin-vs-stack-depth.md) — cell resolution
- [../shared-core/dart-pricing-axes.md](../shared-core/dart-pricing-axes.md) — IP-power tier anchors (pricing-model
  framing; same ranges)
- [../shared-core/strategy-allocation-lock-matrix.md](../shared-core/strategy-allocation-lock-matrix.md) — which
  strategy cells are exclusivity-eligible (non-IM_RESERVED) per the 2026 allocation snapshot
- [im-profit-share-structures.md](im-profit-share-structures.md) — India Options $100k onboarding ties into tier-3
  venue-access pricing
