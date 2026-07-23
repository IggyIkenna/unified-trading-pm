---
doc_type: codex-ssot
title: Strategy Allocation Lock Matrix — Current Snapshot
summary:
  Dated (2026-04-20) snapshot of which strategy cells are INVESTMENT_MANAGEMENT_RESERVED (hidden from DART prospects) vs
  PUBLIC — only STAT_ARB_PAIRS_FIXED crypto pairs + BTC-FoF wrapper are PUBLIC; every other archetype×instrument×venue
  is IM_RESERVED by default. Per-client override (Elysium/Desmond) grants access without locking out others.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service, unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [strategy, defi, cefi, tradfi, sports, ui, registry]
related:
  [
    ../_ssot-rules/06-show-dont-show-discipline.md,
    /codex/14-customer-journeys/shared-core/strategy-origin-vs-stack-depth.md,
    ../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md,
    ../../09-strategy/architecture-v2/category-instrument-coverage.md,
  ]
created: 2026-04-20
authoritative_for: [strategy allocation lock-state snapshot (IM_RESERVED vs PUBLIC cells)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md,
    /codex/09-strategy/architecture-v2/restriction-policy.md,
    /codex/14-customer-journeys/commercial-model/exclusivity-and-noncompete.md,
    /codex/14-customer-journeys/commercial-model/im-profit-share-structures.md,
    /codex/14-customer-journeys/commercial-model/signal-leasing.md,
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/experience/dart-briefing.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Strategy Allocation Lock Matrix — Current Snapshot

> Concrete snapshot (dated 2026-04-20) of which strategy cells are IM_RESERVED (hidden from DART prospects) vs PUBLIC
> (available). Stage 3B's UAC combo registry reads from this. UI `lib/architecture-v2/availability.ts` seed data mirrors
> this. Codex strategy-v2 `strategy-availability-and-locking.md` cites this.

**Rule sources:** [rule 03](../_ssot-rules/03-same-system-principle.md) (one system, partitioned views),
[rule 06](../_ssot-rules/06-show-dont-show-discipline.md) (show / don't-show discipline). **Enum canonical name:**
`INVESTMENT_MANAGEMENT_RESERVED` (UI + UAC identifier).

## Decision rule (locked 2026-04-20)

**ONLY** two strategy groups are PUBLIC (reusable by DART prospects):

1. `STAT_ARB_PAIRS_FIXED` × crypto pairs (mean reversion) — our existing live IM strategy with 1yr+ track record. No
   exclusivity signed with any client, so can be offered to DART prospects.
2. BTC FoF wrapper — **external fund**, NOT in the catalogue enum. Surfaced only in client-reporting for the specific
   wrapper mandate. Does not consume Odum-system compute.

**EVERY OTHER ARCHETYPE × INSTRUMENT × VENUE CELL** is `INVESTMENT_MANAGEMENT_RESERVED` by default. The rationale:
they're part of Odum's forward plan (Q2-Q4 2026 + 2027 roadmap). Even cells Odum isn't yet running live are held
reserved so DART prospects don't see them as "offered" and so Odum retains strategic flexibility.

**Exception — Elysium engagement**: Elysium runs CARRY_BASIS_PERP, CARRY_STAKED_BASIS, YIELD_ROTATION_LENDING cells on
our infrastructure. They do NOT have exclusivity. Other prospects are NOT blocked from the same strategies by Elysium —
they're blocked because those cells are IM_RESERVED (forward plan). Elysium operates under a per-client override that
grants them access (similar to CLIENT_EXCLUSIVE semantics but without the lock-out effect on other clients).

## The matrix

### PUBLIC cells (DART prospects can access)

| Archetype            | Category | Instrument | Representative venues     | Notes                                                                  |
| -------------------- | -------- | ---------- | ------------------------- | ---------------------------------------------------------------------- |
| STAT_ARB_PAIRS_FIXED | CEFI     | spot       | Binance, Coinbase, Bybit  | Crypto mean-reversion — existing IM, 1yr+ live. No exclusivity signed. |
| STAT_ARB_PAIRS_FIXED | CEFI     | perp       | Binance-perp, Hyperliquid | Same strategy family on perps.                                         |

### IM_RESERVED cells — currently running for own IM

| Archetype                    | Category | Instrument    | Venues                              | Status            | Notes                                                              |
| ---------------------------- | -------- | ------------- | ----------------------------------- | ----------------- | ------------------------------------------------------------------ |
| ML_DIRECTIONAL_CONTINUOUS    | CEFI     | spot          | Binance, Coinbase, Hyperliquid      | Jun 2026 go-live  | BTC ML for 10 IM clients × $500k                                   |
| ML_DIRECTIONAL_CONTINUOUS    | CEFI     | perp          | Binance-perp, Hyperliquid           | Jun 2026 go-live  | BTC ML perp companion                                              |
| ML_DIRECTIONAL_CONTINUOUS    | TRADFI   | dated_future  | CME (S&P futures)                   | Sept 2026 go-live | CME co-invest ($500k → $5M ramping)                                |
| VOL_TRADING_OPTIONS          | TRADFI   | option        | NSE (India options)                 | Oct 2026 go-live  | India Options delta trading for convex payouts ($5-10M allocation) |
| ML_DIRECTIONAL_EVENT_SETTLED | SPORTS   | event_settled | Betfair, Betradar, specific leagues | Jun 2026 go-live  | Sports ML for 2 clients × $50-100k (capacity-bound)                |

### IM_RESERVED cells — forward plan (not yet live)

Every other cell in
[`../../09-strategy/architecture-v2/category-instrument-coverage.md`](../../09-strategy/architecture-v2/category-instrument-coverage.md)
is IM_RESERVED by default. These include (non-exhaustive):

- `RULES_DIRECTIONAL_*` on all categories (reserved for future signal variants)
- `CARRY_BASIS_DATED` on CEFI / DEFI (future dated-future carry)
- `CARRY_BASIS_PERP` on CEFI / DEFI (Elysium uses, but IM_RESERVED for others)
- `CARRY_STAKED_BASIS` on DEFI (Elysium uses, IM_RESERVED for others)
- `CARRY_RECURSIVE_STAKED` on DEFI (Elysium upsell Nov 2026)
- `YIELD_ROTATION_LENDING` on DEFI (Elysium uses, IM_RESERVED for others)
- `YIELD_STAKING_SIMPLE` on DEFI (IM_RESERVED)
- `ARBITRAGE_PRICE_DISPERSION` on all categories (Desmond's funding arb scope — uses via client-signal DART but the
  archetype itself is IM_RESERVED)
- `LIQUIDATION_CAPTURE` on DEFI
- `MARKET_MAKING_CONTINUOUS` on CEFI / DEFI (Q2 2027 live per deck)
- `MARKET_MAKING_EVENT_SETTLED` on SPORTS / PREDICTION
- `EVENT_DRIVEN` on all categories
- `VOL_TRADING_OPTIONS` on DEFI / CEFI (NSE is IM_RESERVED with concrete mandate; other venues remain forward-plan
  IM_RESERVED)
- `STAT_ARB_CROSS_SECTIONAL` on all categories (extension of mean-rev to cross-sectional; not yet shipped)

## Special cases

### BTC Fund of Funds (external wrapper)

- Odum allocates a BTC-client mandate to an **external** fund-of-funds. Odum does not operate the strategy.
- Revenue: 0.5 BTC/year (50 BTC × 5% FoF annualised × 20% Odum share).
- **NOT in the strategy catalogue**. No catalogue cell, no lock_state.
- Surfaces in `client-reporting` for the specific wrapper mandate only.

### Elysium (client-downstream DeFi)

- Runs CARRY_BASIS_PERP + CARRY_STAKED_BASIS + YIELD_ROTATION_LENDING + (upsell) CARRY_RECURSIVE_STAKED + future
  MEV-enhanced variants.
- Lock-state semantic: cells are IM_RESERVED by default, but Elysium's entitlement includes a per-client override
  granting them operational access. Modelled as `reservingBusinessUnitId = "elysium"` in the registry so the cells
  render for Elysium admin but IM_RESERVED for all other DART prospects.
- Alternative modelling: create a `CLIENT_ACTIVE_NON_EXCLUSIVE` lock state. Decision: use the entitlement-override
  approach (simpler, no new enum value required).

### Desmond (client-downstream perp-funding-arb)

- Uses `ARBITRAGE_PRICE_DISPERSION` archetype on CEFI perps (Binance-perp + Hyperliquid + potentially OKX/Bybit).
- He brings his own signals — signals-only DART.
- Lock-state semantic: ARBITRAGE_PRICE_DISPERSION is IM_RESERVED as forward plan. Desmond gets per-client override (same
  mechanism as Elysium).
- Commodity-alpha space, so no exclusivity premium.

## Enforcement points

| Enforcement point         | File                                                                      | Behaviour                                                                               |
| ------------------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| UAC type-level            | `unified_api_contracts/internal/architecture_v2/strategy_availability.py` | `LockState` enum defines valid values                                                   |
| UTL events                | `unified_trading_library` STANDARD_LIFECYCLE_EVENTS                       | `STRATEGY_AVAILABILITY_CHANGED` emitted on any flip                                     |
| strategy-service runtime  | `strategy_service/availability/`                                          | Thread-safe registry; fails-loud on unauthorised allocation                             |
| UI data                   | `unified-trading-system-ui/lib/architecture-v2/availability.ts`           | TS mirror of the enum + helpers                                                         |
| UI seed                   | `unified-trading-system-ui/lib/architecture-v2/availability-store.tsx`    | Provider populates from this matrix on first mount                                      |
| Catalogue filter          | catalogue list pages                                                      | Applies `slotsVisibleTo(audience, registry)` to hide IM_RESERVED from prospect personas |
| Demo restriction profiles | `../demo-ops/demo-restriction-profiles.md`                                | Rule-06 enforcement documented per cell                                                 |

## Transitions

A cell transitions from IM_RESERVED → PUBLIC when:

1. Odum decides to offer the archetype × instrument × venue combination as a DART-reusable strategy.
2. There is no active client engagement on that specific cell that would create conflict.
3. Commercial team signs off (no exclusivity commitments on that cell).
4. Admin invokes the lock-state toggle at `/services/strategy-catalogue/admin/lock-state` which emits
   `STRATEGY_AVAILABILITY_CHANGED`.

A cell transitions from IM_RESERVED → CLIENT_EXCLUSIVE when a client signs a rule-04 exclusivity premium covering that
scope. This is a Tier B block 12 commercial event.

A cell transitions from any state → RETIRED when the strategy is wound down. RETIRED preserves catalogue history for
audit; allocator cannot push capital; no new engagements.

## Stage 3 implications

Stage 3B's UAC combo registry reads this matrix as the authoritative current-state for `lock_state`. Stage 3C's
derivation engine resolves `slots_visible_to(audience, registry)` using this. Stage 3E refactor plan includes a
follow-up item to turn this matrix into generated seed data (Python → TypeScript codegen) so the doc and the runtime
stay in lockstep.

## Cross-references

- [rule 03 — same-system principle](../_ssot-rules/03-same-system-principle.md)
- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md)
- [strategy-origin-vs-stack-depth.md](strategy-origin-vs-stack-depth.md) — per-client commercial path
- [dart-pricing-axes.md](dart-pricing-axes.md) — signals-only vs full-DART pricing
- [../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md](../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md)
  — maturity + lock ladder
- [../../09-strategy/architecture-v2/category-instrument-coverage.md](../../09-strategy/architecture-v2/category-instrument-coverage.md)
  — master coverage matrix (the 205-cell universe)
- [../demo-ops/demo-restriction-profiles.md](../demo-ops/demo-restriction-profiles.md) — demo rendering enforcement
- UI enum:
  [`unified-trading-system-ui/lib/architecture-v2/availability.ts`](../../../../unified-trading-system-ui/lib/architecture-v2/availability.ts)
