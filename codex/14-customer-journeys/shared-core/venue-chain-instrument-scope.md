---
doc_type: codex-ssot
title: Venue × Chain × Instrument-Type Scope
summary:
  Commercial-scope view of the three sub-scoping axes on rule-05 blocks 8/9/10 (venue / chain / instrument-type packs) —
  the 2026 live venue set (Binance/Coinbase/Bybit/Hyperliquid + CME/NSE go-live, Ethereum/Arbitrum/Base/Solana chains,
  Betfair/Polymarket), how they compose into demo restriction profiles, per-unit pricing, and catalogue-filter
  visibility.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin, sales]
tags: [cefi, defi, tradfi, sports, prediction, cost, instruments]
related:
  [
    ../_ssot-rules/05-building-block-dimensions.md,
    ../../02-venues/venue-registry-reference.md,
    ../../09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/14-customer-journeys/shared-core/strategy-origin-vs-stack-depth.md,
    /codex/14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md,
  ]
created: 2026-04-20
authoritative_for: [venue/chain/instrument-type block sub-scoping axes (blocks 8/9/10)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/commercial-model/building-block-packaging.md,
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/shared-core/README.md,
    /codex/14-customer-journeys/shared-core/data-licensing-boundaries.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Venue × Chain × Instrument-Type Scope

> Implementation reference for the sub-scoping axes on rule-05 blocks 8, 9, and 10. Names the venues Odum operates on,
> the chains, the instrument types, and how they compose into demo restriction profiles and pricing scope.

**Rule source:** [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) blocks 8, 9, 10
**Upstream taxonomy sources:** [`../../02-venues/`](../../02-venues/) +
[`../../09-strategy/architecture-v2/category-instrument-coverage.md`](../../09-strategy/architecture-v2/category-instrument-coverage.md)

## The three scoping axes

Every DART signals-only or full-pipeline engagement scopes on three independent axes. Same for Reg Umbrella engagements
that include an execution layer.

- **Venue scope.** Which CeFi venues, sports venues, prediction markets, TradFi venues? Per-venue or per-venue-group
  pack.
- **Chain scope.** Which DeFi chains? Per-chain pack.
- **Instrument-type scope.** Which instrument types (spot, perps, dated futures, options, lending, staking, yield,
  prediction markets, sports fixtures)? Per-type pack.

The three axes compose. A DeFi-native fund trading perps and spot on Binance + Coinbase + Arbitrum + Base buys:

- venue packs: Binance + Coinbase
- chain packs: Arbitrum + Base (if they run DeFi-resident execution on these chains)
- instrument-type packs: perps + spot

Three venue-pack units, two chain-pack units, two instrument-type-pack units. Pricing is per unit, tier per unit (rule
08 per-block mixability).

## Venue scope

Odum's venue coverage aligns with [`../../02-venues/`](../../02-venues/). Sub-scope granularity varies:

- **Individual venue.** Binance-spot, Coinbase, Bybit — each is one venue pack unit.
- **Venue group.** A bundled set (e.g. "tier-2 DEX pack" covering several smaller-cap DEXs) priced as one unit.

Per venue pack, Odum provides: connectivity, credentials handling, reference-data coverage, execution integration,
reconciliation adapters, venue-specific TCA.

### Current venue scope (2026)

Snapshot of the actual venue scope Odum operates on in 2026, matching the concrete mandates in
[`strategy-allocation-lock-matrix.md`](strategy-allocation-lock-matrix.md). Authoritative long-form list still lives in
[`../../02-venues/`](../../02-venues/); this table is the commercial-scope view.

**CEFI venues**

| Venue        | Status            | Notes                                                                       |
| ------------ | ----------------- | --------------------------------------------------------------------------- |
| Binance-spot | Live              | STAT_ARB_PAIRS_FIXED (PUBLIC) + BTC ML directional (IM_RESERVED, Jun 2026). |
| Binance-perp | Live              | BTC ML perp companion (IM_RESERVED) + Desmond perp-arb scope.               |
| Coinbase     | Live              | Mean-rev + BTC ML spot.                                                     |
| Bybit        | Live              | Cross-venue + perp scope.                                                   |
| Hyperliquid  | Live              | BTC perp + Desmond perp-arb scope.                                          |
| CME-futures  | Sept 2026 go-live | S&P futures for ML directional (IM_RESERVED co-invest mandate).             |
| NSE-options  | Oct 2026 go-live  | India Options delta trading (IM_RESERVED, gated on S&P signal).             |

**DeFi chains**

| Chain       | Status           | Notes                                                 |
| ----------- | ---------------- | ----------------------------------------------------- |
| Ethereum L1 | Live             | Elysium CARRY_BASIS_PERP + CARRY_STAKED_BASIS scope.  |
| Arbitrum    | Live             | Elysium + DeFi yield rotation scope.                  |
| Base        | Live             | Elysium + DeFi yield rotation scope.                  |
| Solana      | Sept 2026 upsell | Elysium CARRY_RECURSIVE_STAKED upsell go-live window. |

**Sports venues**

Capacity-bound (2 IM clients from June 2026). Feed/adapter stack:

- Betfair — in-play + pre-match exchange pricing + execution.
- Betradar — data feeds for the specific league set.
- API-Football — supplemental fixture metadata + league coverage.

League scope is deliberately narrow (specific leagues only) because capacity is strategy-bound, not
infrastructure-bound.

**Prediction markets**

| Venue      | Status |
| ---------- | ------ |
| Polymarket | Live.  |

**Adjacent but blocked / conditional:**

- **Bybit, OKX** — potential Q2-Q3 2026 CEFI addition if Desmond's perp-funding-arb strategy requires them for
  best-execution routing. Treated as venue-pack expansion inside his existing Tier B scope, not a separate venue
  onboarding project.
- **Kalshi** — BLOCKED per strategy-architecture-v2 block list (no Kalshi adapter integrated today). Re-opens if / when
  the Kalshi adapter is built.

**Out-of-scope venues for experience demos:** any venue not declared in the prospect's scope. The demo data surfaces
their declared venues; other venues do not appear.

## Chain scope

DeFi chains scope per-chain. Each chain pack provides RPC connectivity, wallet custody patterns, chain-specific
instrument metadata, gas management, and any chain-specific protocol integration.

Authoritative chain list: `CHAIN_RPC_TEMPLATES` in UAC `registry/capability_declarations/_defi.py` — SSOT for all chain
→ RPC mappings. Experience playbooks do not re-list chains; they reference by name the chains in the prospect's declared
scope.

## Instrument-type scope

Instrument-type coverage aligns with
[`../../09-strategy/architecture-v2/category-instrument-coverage.md`](../../09-strategy/architecture-v2/category-instrument-coverage.md).
Per-type packs cover handling depth across research, promote, execution, reporting for that instrument type.

### Supported instrument types

- Spot
- Perps (perpetual futures)
- Dated futures (with rolling-continuous underlying support via representative-future registry)
- Options
- Lending
- Staking
- Yield
- Prediction markets
- Sports fixtures (with in-play vs pre-match sub-types)

Each is a separate pack. Clients trading options + perps buy two instrument-type packs.

## How scope composes into restriction profiles

The demo restriction profile (see
[`../demo-ops/demo-restriction-profiles.md`](../demo-ops/demo-restriction-profiles.md)) encodes the scope as three sets:
`{venues}`, `{chains}`, `{instrument_types}`. The catalogue filter, navigation visibility, and demo data pipeline all
read from these sets.

The experience playbook for each audience inherits the restriction profile from the resolved commercial cell (see
[`strategy-origin-vs-stack-depth.md`](strategy-origin-vs-stack-depth.md)). A prospect whose signals touch only 3 venues
and 2 chains sees the catalogue filtered to those intersections.

## How scope composes into pricing

Block 8 (venue packs), block 9 (chain packs), block 10 (instrument-type packs) each price per-unit. Per rule 08 tier
mixability, the same engagement can have:

- Tier B on block 8 for one primary venue pack (certainty)
- Tier A on block 8 for a marginal venue pack (usage-variable)
- Tier B on block 9 for the primary chain
- Tier A on block 9 for a secondary chain

Sub-scoping means one block-identifier can have multiple instances in a quote (one per venue, one per chain, one per
instrument type), each with independent tier assignment.

## How scope composes into strategy catalogue visibility

The strategy catalogue (see [rule 03 sub-claim d](../_ssot-rules/03-same-system-principle.md)) has one row per
`(archetype, instrument_type, venue-or-chain, ...)` combination. The catalogue filter applies the audience's scope set
as an AND: row visible iff its venue ∈ audience.{venues} AND its instrument_type ∈ audience.{instrument_types} AND its
chain ∈ audience.{chains} (if applicable) AND its maturity ≥ BACKTESTED AND its lock_state is visible to the audience.

The `category-instrument-coverage.md` master matrix in 09-strategy is the SSOT for which rows exist; this doc explains
how they are filtered per audience.

## Edge cases

- **Cross-venue routing.** Some strategies require cross-venue routing as a capability. That is a block-11 analytics
  pack or part of execution layer block-7 capability; it is not a separate venue-pack unit.
- **Chain-agnostic DeFi strategies.** A strategy that runs on any of several chains with equivalent behaviour buys chain
  packs per the chains it runs on, not one bundled "DeFi" pack.
- **Sports fixture scope.** Sports fixtures sub-scope per league or competition, priced inside the instrument-type pack.
- **Prediction market scope.** Prediction markets sub-scope per venue (Polymarket, Kalshi) inside the instrument-type
  pack and the venue pack.

## Stage 3B registry implications

Stage 3B's UAC combo registry declares `venue`, `chain`, `instrument_type` as scope dimensions. The registry's blocker
predicates (see `infra-spec/stage-3b-uac-combo-rules.md`) check scope composability: e.g., `DeFi options` is BLOCKED
because no DeFi options protocol is integrated today; `Kalshi adapter` is BLOCKED pending adapter build.

## Cross-references

- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) — blocks 8, 9, 10
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — per-block tier mixability
- [`../../02-venues/`](../../02-venues/) — venue SSOT
- [`../../09-strategy/architecture-v2/category-instrument-coverage.md`](../../09-strategy/architecture-v2/category-instrument-coverage.md)
  — category × instrument coverage matrix
- [strategy-origin-vs-stack-depth.md](strategy-origin-vs-stack-depth.md) — the commercial matrix that scope plugs into
- [../demo-ops/demo-restriction-profiles.md](../demo-ops/demo-restriction-profiles.md) — profile encodes scope
- [../commercial-model/pricing-building-blocks.md](../commercial-model/pricing-building-blocks.md) — pricing structure
- [../infra-spec/stage-3b-uac-combo-rules.md](../../16-strategy-playbooks/infra-spec/stage-3b-uac-combo-rules.md) —
  Stage 3B registry
