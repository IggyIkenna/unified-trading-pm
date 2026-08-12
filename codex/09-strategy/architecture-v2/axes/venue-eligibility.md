---
doc_type: codex-ssot
title: "Axis: Venue Eligibility"
summary:
  Venue-eligibility axis — the slow-moving set of venues a strategy MAY execute on plus per-venue constraints (max
  notional, min liquidity, fee tier, Unity child-book preferences, chain eligibility), vs the fast-moving execution-time
  SOR pick. Eligibility auto-gated on credentials + adapter action support + capability registry; declares
  venue_routing_mode (SOR_AT_EXECUTION / STRATEGY_PICKED / META_BROKER) and pre-funding vs SOR.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [strategy, venue-eligibility, execution, defi, cefi, sports]
related:
  [
    ../../../04-architecture/slow-fast-routing-split.md,
    ../../../02-venues/venue-registry-reference.md,
    ../cross-cutting/transfer-rebalance.md,
    ../cross-cutting/mev-protection.md,
  ]
created: 2026-04-17
authoritative_for: [venue-eligibility axis (strategy-config venue set + per-venue constraints)]
referenced_by:
  [
    /codex/04-architecture/slow-fast-routing-split.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/axes/edge-methods.md,
    /codex/09-strategy/architecture-v2/axes/expression.md,
    /codex/09-strategy/architecture-v2/axes/signal-sources.md,
    /codex/09-strategy/architecture-v2/axes/staking-methods.md,
    /codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md,
    /codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Axis: Venue Eligibility

> **What it is:** The set of venues a strategy is allowed to execute on, plus per-venue constraints. This is the
> _slow-moving_ venue dimension (eligibility) — the _fast-moving_ venue pick at execution time (SOR among eligible
> venues) is an execution-service concern.
>
> **How it relates:** Strategy config declares eligibility; execution-service picks per-tick among eligible for fungible
> SOR cases. See [slow-fast routing split](../../../04-architecture/slow-fast-routing-split.md).

## Eligibility vs selection

```
SLOW-MOVING (strategy config)          FAST-MOVING (execution)
─────────────────────────────          ────────────────────────
• Which venues can this strategy use    • Which venue to route THIS order to
• Which child books on Unity            • Current best quote + net cost
• Pre-funded venue allocation           • Current venue health / latency
• Regulatory / custody constraints      • MEV protection submission mode
• Credential availability               • Rate-limit headroom
• Chain/protocol support                • Real-time liquidity
```

Strategy emits intent with `eligible_venues: [...]`. Execution-service's SOR picks the one that will actually receive
the order right now.

### RULING 3 (operator, 2026-08-12) — eligibility splits THREE ways, and only the first excludes globally

The two-column split above is right but under-specified: it does not say where a **research or edge preference** belongs,
and the code has been putting those in the catalogue. Three distinct kinds of "this venue is not for this strategy":

| Kind                          | Example                                                                 | Where it belongs                          | Excludes globally? |
| ----------------------------- | ----------------------------------------------------------------------- | ----------------------------------------- | ------------------ |
| **1. Physical capability**    | You cannot trade options on Hyperliquid, so it is not an options venue    | Venue / capability registry (UAC)         | **YES**            |
| **2. Research / edge view**   | Hyperliquid is a momentum venue, so a reversion edge inverts there        | **Strategy INSTANCE config**              | **NO**             |
| **3. Execution-time pick**    | OKX has the better quote right now                                       | SOR at execution                          | n/a                |

**The operator's ruling, verbatim in effect:** _"we're not optimising to venues based on previous research. We're giving
the list of allowable venues and their constraints, which make them less allowable for some things or some configs, but
it's the config that ultimately decides."_ If we have options on both Deribit and OKX, **both are eligible candidates** and
the config decides which is subscribed to — the catalogue does not pre-pick a winner on our research view.

**Code currently violates this.** `_FUNDING_DISPERSION_VENUES` in `catalog_carry.py` omits `HYPERLIQUID` with the comment
"HL excluded — momentum", which is a kind-2 reason enforced as a kind-1 exclusion. The effect is that **no instance config
can ever opt Hyperliquid into funding dispersion**, even for a deliberate experiment, and the reason is invisible to the
operator configuring the instance. Hyperliquid IS present in `_CARRY_BASIS_PERP_VENUE_BUNDLES` and in the staked-basis perp
venues, so this is an inconsistency within one file, not a considered policy.

The correction is to emit the slot and let config exclude it, carrying the research view as a **default** in instance config
plus a documented rationale — never as an absent catalogue row. Tracked in
[the Elysium readiness plan](/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md) § H.15.

> **Why this matters beyond one venue:** a catalogue that bakes in research produces a universe nobody can audit against
> the venue's real capabilities, and every future edge revision needs a code change instead of a config change. The
> constraint registry answers "could this work"; the instance config answers "do we want it".

## Eligibility constraints

When declaring eligibility in config, strategies specify:

### Venue set

```yaml
venues:
  - BINANCE
  - OKX
  - BYBIT
  # or for DeFi:
  - UNISWAP_V3_ETHEREUM
  - UNISWAP_V3_ARBITRUM
  - UNISWAP_V3_OPTIMISM
```

### Venue-specific constraints

```yaml
venue_constraints:
  BINANCE:
    max_notional_usd: 500_000 # don't route more than this to Binance
    min_liquidity_usd: 100_000 # skip if Binance has less depth
    fee_tier: VIP_3 # expected fee tier for this venue
  UNISWAP_V3_ETHEREUM:
    min_pool_tvl: 10_000_000
    fee_tier: 500 # 0.05% pool
```

### Child-book eligibility (Unity meta-broker)

For Unity-routed sports strategies, specify which child books are eligible:

```yaml
venue: UNITY
unity_child_books_eligible:
  - PINNACLE_VIA_UNITY
  - VX
  - SHARPBET
  - BETFAIR_VIA_UNITY
  # exclude IBCbet (high commission) unless explicit
unity_child_book_preferences:
  preferred_first: [VX, SHARPBET] # lowest commission first
  avoid: [BROKER5] # 3% commission — only if spread justifies
```

### Chain eligibility (DeFi)

```yaml
chains_eligible:
  - ETHEREUM
  - ARBITRUM
  - OPTIMISM
  - POLYGON
  - BASE
  - AVALANCHE
# NOT listed = excluded
```

### Credential + capability gating

Eligibility is automatically gated on:

- Credentials present in Secret Manager for this (client, venue) pair
- Venue adapter supports the action type (no LEND on Binance; no QUOTE on Polymarket)
- Venue capability registry confirms instrument is tradeable on venue

If any of these fail, the venue is filtered out at strategy startup.

## Custody model × venue eligibility

Per [capital-structure-and-regulatory](../../../04-architecture/capital-structure-and-regulatory.md):

- **CeFi SMA client**: venues limited to those where client has an account + API keys
- **CeFi fund mode (future)**: firm-owned accounts across all supported CEXes
- **DeFi client wallet**: venues limited to chains the client has wallet access to
- **DeFi firm capital**: all supported chains/protocols
- **Sports Unity pool**: Unity only (firm-managed)
- **Sports direct books**: per-book accounts
- **TradFi IBKR SMA**: IBKR routes internally; venue = IBKR always
- **TradFi counterparty direct**: whatever counterparty supports

## Pre-funding vs SOR-at-execution

For **fungible assets with SOR** (crypto spot across CEXes, DeFi DEX swaps):

- Strategy declares eligible venues
- Strategy or ops pre-funds each eligible venue with some allocation
- Execution-service's SOR picks best-price venue at tick time among pre-funded venues
- Strategy rebalances pre-funding allocation on schedule (Transfer/Rebalance service)

For **non-fungible** (perps — different funding rates; options — different strikes; sports bookmakers — different
lines):

- Strategy picks ONE specific venue per opportunity at emission time
- No SOR at execution
- Strategy handles venue swap explicitly (close on A, open on B)

## Declaring the mode

```yaml
venue_routing_mode: SOR_AT_EXECUTION # execution picks per tick among eligible
# or
venue_routing_mode: STRATEGY_PICKED # strategy names the specific venue per instruction
# or
venue_routing_mode: META_BROKER # venue is meta-broker (Unity), which itself routes
```

## Venue categories and strategy universe

Every venue is tagged with category: CEFI / DEFI / SPORTS / TRADFI / PREDICTION. Strategy's `execution_categories` label
is derived from the union of its eligible venues' categories. This is used for investor-facing reporting + UI filters,
NOT for code routing. See [../families/](../families/) README capital flow section.

## Not in this axis

- **Real-time venue pick** (SOR at tick time) — that's execution-service, not strategy config
- **Credential rotation** — ops concern
  ([credential management](../../../04-architecture/capital-structure-and-regulatory.md))
- **Transfer / bridge planning** — [transfer-rebalance cross-cutting](../cross-cutting/transfer-rebalance.md)
- **MEV protection mode** — [mev-protection cross-cutting](../cross-cutting/mev-protection.md)
- **Which algo to use on venue** — execution_policy_ref

## Cross-references

- Slow/fast routing split:
  [../../../04-architecture/slow-fast-routing-split.md](../../../04-architecture/slow-fast-routing-split.md)
- Venue registry: [../../../02-venues/venue-registry-reference.md](../../../02-venues/venue-registry-reference.md)
- Unity meta-broker: [../../../02-venues/unity-integration.md](../../../02-venues/unity-integration.md)
- Capital structure per category:
  [../../../04-architecture/capital-structure-and-regulatory.md](../../../04-architecture/capital-structure-and-regulatory.md)
