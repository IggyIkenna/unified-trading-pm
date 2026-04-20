---
scope: [sales, admin]
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
Until populated, the structure is: Tier B monthly × (1 + exclusivity_pct), where `exclusivity_pct` is a negotiated
figure.

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
