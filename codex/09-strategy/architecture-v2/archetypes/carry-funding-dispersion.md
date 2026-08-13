---
doc_type: codex-ssot
title: "Archetype: `CARRY_FUNDING_DISPERSION`"
summary: >-
  Archetype CARRY_FUNDING_DISPERSION: dollar-neutral (NOT delta-neutral) cross-sectional funding-rank reversion — LONG
  the lowest-funding coins and SHORT the highest-funding coins across DIFFERENT coins on the same arbitraged venue. The
  edge is cross-sectional PRICE reversion of the funding rank, not a funding-carry harvest. Per-instrument leg engine
  reads an upstream funding_rank_pct; residual market beta is hedged at BOOK level, not leg-vs-leg. Carries a per-leg
  squeeze veto. Documented 2026-08-12 — the engine shipped and was registered long before this doc existed.
implementation_status: code-shipped
status: current
nature: ssot
asset_group: [defi, cefi]
stage: [meta]
repos: [strategy-service, e2e-testing]
scope: [engineer, admin]
tags: [strategy, carry, dispersion, funding, defi, cefi, archetype, cross-sectional]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
    /codex/03-services/portfolio-allocator.md,
    /codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
  ]
created: 2026-08-12
authoritative_for: [CARRY_FUNDING_DISPERSION archetype specification]
referenced_by: []
owner: ikennaigboaka
last_reviewed: "2026-08-12"
last_updated: "2026-08-12"
code_refs:
  [
    strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/,
    strategy-service/strategy_service/engine/strategies/v2/target_universe/,
    strategy-service/strategy_service/portfolio_allocator/,
  ]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 150
  min_sla_tier: premium
---

# Archetype: `CARRY_FUNDING_DISPERSION`

> **Why this doc was missing.** The engine has been implemented, registered in the archetype factory and given a target
> universe for months, but had **no entry in `archetypes/`** — while the allocator SSOT simultaneously undercounted its
> own registry and omitted the entire rank-allocator layer. The two gaps reinforced each other: a reader working from
> codex could not discover this capability, and the client-facing document set consequently asserted a carry-archetype
> count that was one short. Found and closed 2026-08-12.

## What it does

A **cross-sectional long/short on perpetuals ranked by funding rate**: go LONG the lowest-funding coins and SHORT the
highest-funding coins, on **different coins** at the **same arbitraged venue**.

**The single most important thing to understand, and the one most likely to be got wrong:** this is **~99%
cross-sectional PRICE reversion, not a funding-carry harvest.** Extreme or crowded funding marks a crowded position that
mean-reverts on arbitraged venues; the funding rank is the _signal_, not the _income_. Anyone reading the name and
assuming it earns the funding spread will size and attribute it wrongly.

It is **dollar-neutral, NOT delta-neutral** — equal dollars long and short in aggregate, but **per-coin directional**,
because the long basket and the short basket hold different assets and therefore do **not** price-cancel the way a
same-coin spot/perp basis does. Residual market beta is hedged at **BOOK level** (beta-hedge + vol-target overlays),
never leg-versus-leg.

## Architecture — batch == live, rank upstream, leg per instrument

The cross-sectional rank is computed **upstream** (feature layer / rank allocator over the whole universe) and arrives
at this engine **per instrument** as the `funding_rank_pct` feature. This engine is the **per-instrument leg engine**:
it reads its own rank and emits its own single perp leg.

That split is what makes the basket expressible without a composite archetype — see
[cross-cutting/portfolio-allocator](/codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md). A basket
of N coins is **N instances of this one archetype**, each emitting one leg, coordinated by the shared rank. The matching
allocator archetype is `CARRY_FUNDING_DISPERSION_RANK` (single-stage, ranks the whole cohort by raw perp funding bps, no
venue/LST hierarchy).

## Features expected

| Feature                       | Required | Meaning                                                                 |
| ----------------------------- | -------- | ----------------------------------------------------------------------- |
| `funding_rank_pct`            | **YES**  | Cross-sectional funding rank in `[0, 1]` — 0 = lowest funding in cohort |
| `funding_rate_annualised_bps` | no       | Raw annualised funding, carried as an attestation only                  |
| `funding_inverse_vol_weight`  | no       | Inverse-vol leg weight (default `1.0`)                                  |
| `funding_squeeze_sigma`       | no       | 2-day move in trailing-vol units — the squeeze/crash signal             |

**Honest absence is load-bearing:** `funding_rank_pct` absent → the engine emits **nothing**. It does not go flat and it
does not assume a neutral rank. No cross-sectional signal means no decision.

## Config schema

| Param               | Default  | Effect                                                           |
| ------------------- | -------- | ---------------------------------------------------------------- |
| `long_rank_pct`     | `0.3333` | LONG when `funding_rank_pct <= this`                             |
| `short_rank_pct`    | `0.3333` | SHORT when `funding_rank_pct >= 1 - this`                        |
| `stake_fraction`    | `0.5`    | Fraction of equity in the perp leg notional                      |
| `min_mid_price`     | `0.0001` | Skip ticks at or below this mid                                  |
| `squeeze_threshold` | `2.0`    | Veto a leg on a greater-than-this-sigma adverse move; 0 disables |

Coins between the two thresholds are **FLAT** — the middle of the cohort is deliberately not traded.

## Execution semantics

Emits a single `TradeInstruction` per tick with `target_position_units = target_equity * signed_weight / mid_price`,
where `signed_weight` is negative for the short leg. Targets not deltas, so re-emission is idempotent. Leg weight is
`stake_fraction × inverse_vol_weight`, with the inverse-vol factor clamped to `[0, 2]` for sizing safety.

`attestations` carries `funding_rank_pct`, `funding_bps` and `leg_weight` — enough to reconstruct the sizing decision
from the instruction alone.

`declare_leg_portfolio_state()` returns a single `perp` leg whose side tracks the sign of the current position, with
`target_net_delta` = signed `stake_fraction`, `CashSweepPolicy.THRESHOLD` and `LegSizingStrategy.CONVICTION_WEIGHTED`.

### The squeeze veto — the one accretive directional overlay

Of the research overlays evaluated (EWMA smoothing, rank buffer, no-trade band, HL veto, inverse-vol, beta-hedge,
vol-target), all but one are signal- or portfolio-layer concerns folded into the rank and the inverse-vol weight
feature. The exception is **per-leg and lives in the engine**: cut a leg on a large adverse 2-day move — a long that is
crashing, a short that is squeezing. This is the asymmetry that makes the veto directional rather than symmetric.

## Supported venues

Candidate slots are **per (venue, coin)** on the arbitraged venues. The venue set is data in
`target_universe/catalog_carry.py`, not a constant to be quoted from memory — read `_FUNDING_DISPERSION_VENUES`.

**Hyperliquid is deliberately EXCLUDED**: it is a momentum venue, not a reversion venue, so the edge inverts there. This
is an upstream universe exclusion, not an engine check.

Two venues in the set are conditional and should not be read as live edge: **Kalshi-perp** (CFTC-regulated, live from
2026-05-29; mean-reversion edge **TBD pending data accumulation**) and **Polymarket-perp** (`BLOCKED-UPSTREAM-OUTAGE`,
DNS NXDOMAIN from 2026-06-21 — wired to tolerate honest absence, contributes once funding data arrives).

> **Doc-vs-code note (2026-08-12):** `build_funding_dispersion()`'s own docstring enumerates four venues while the tuple
> immediately beneath it holds six. Trust the tuple. A tracked fix is in
> [the Elysium readiness plan](/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md).

## Coin universe — dynamic ADV ranking is OPT-IN and defaults OFF

The coin universe resolves through `_resolve_dynamic_carry_coins()`, shared with `CARRY_BASIS_PERP`:

- **Default (`enable_dynamic_carry_universe = False`)** — returns the **static** coin list with **zero GCS I/O**. Live
  behaviour is byte-for-byte preserved, and there is a regression test asserting exactly that.
- **Opt-in ON** — ranks candidates by **real ADV** from the MDPS `processed_candles` corpus via `rank_top_n_by_adv`.

On any failure — read error or empty ranked result — it **falls back to the static list rather than shrinking the
catalog to zero**, and logs loudly so a persistent data gap stays visible instead of silently masking. **Do not describe
this archetype as ADV-filtered without saying the flag is off by default**; the capability exists, the default does not
use it.

## Risk profile

- **Per-coin directional.** The dollar-neutrality is an aggregate property of the book, not a property of any leg. A
  reader who assumes leg-level hedging will under-estimate single-name risk.
- **Venue-dependent edge.** Reversion holds on arbitraged venues and inverts on momentum venues — the venue set is part
  of the strategy, not deployment configuration.
- **Crowding is the signal and the hazard.** The same extreme funding that marks a reversion candidate marks a position
  that can squeeze first; that is what the squeeze veto exists for.
- **Book-level overlays are prerequisites, not enhancements.** Without beta-hedge and vol-target the residual market
  beta is unmanaged.

## Not in this archetype

- Funding-carry harvesting — that is `CARRY_BASIS_PERP` (same-coin, delta-neutral).
- Same-coin spot/perp basis, staking, lending or borrowing legs.
- Leg-versus-leg hedging of any kind.
- Cross-venue price dispersion — that is `ARBITRAGE_PRICE_DISPERSION`, which ranks **venues** for one coin, whereas this
  ranks **coins** on one venue.
- Computing the cross-sectional rank. That is upstream, by design.

## See also

- [`carry-basis-perp`](/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md) — the delta-neutral
  funding-carry archetype this one is most often confused with
- [`arbitrage-price-dispersion`](/codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md) —
  dispersion on the venue axis rather than the coin axis
- [portfolio-allocator](/codex/03-services/portfolio-allocator.md) — the rank-allocator roster
- [cross-cutting/portfolio-allocator](/codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md) — why a
  basket needs no composite archetype
