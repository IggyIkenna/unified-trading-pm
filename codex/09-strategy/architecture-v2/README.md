---
scope: [engineer, admin]
---

# Strategy Architecture v2 — Family / Archetype / Axes / Cross-Cutting

> **Status:** Canonical architecture as of 2026-04-17. Supersedes the category-based organization in
> `09-strategy/{cefi,defi,sports,tradfi,prediction}/`. The old category docs remain in place as **reference** during
> migration — see [MIGRATION.md](MIGRATION.md) for the complete old-doc → new-archetype mapping.
>
> **Scope:** Every trading strategy in the Unified Trading System — sports, CeFi, DeFi, TradFi, prediction markets —
> maps to this taxonomy. No exceptions.
>
> **Migration principle:** v2 is a clean-start architecture. Existing strategies retain their full functionality (or
> enhanced functionality) but may get new naming, new archetype assignment, or adjusted config. Nothing is lost;
> [MIGRATION.md](MIGRATION.md) audits every existing doc and code module against the v2 placement.

## TL;DR

Every strategy is a composition of:

- **1 of 9 families** (orthogonal alpha styles) — what kind of edge you capture (UAC `StrategyFamily` enum SSOT)
- **1 of 57 archetypes** (code paths under a family) — the specific code implementation (UAC `StrategyArchetype` enum
  SSOT; expanded from 53 → 55 when `CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED` were
  split out of `CARRY_RECURSIVE_STAKED`; then to 57 by the 2026-05-18 taxonomy decision)
- **7 axes of composition** (signal × edge × staking × venue × expression × hold-policy × share-class)
- **10 cross-cutting concerns** — shared infrastructure

A strategy's identity has **5 layers**: family, archetype, instance, config, derived-categories.

Every strategy communicates with execution via a **polymorphic `StrategyInstruction`** (14 action types per UAC
`InstructionActionV2` SSOT) following 5 protocol rules. Batch = live: same code path, benchmark fills contract isolates
strategy alpha from execution alpha.

## Why this architecture (and why clean-start v2)

The system runs strategies across 5 categories and 7 DeFi chains, against ~70-80 execution endpoints. The legacy v1
organization was per-category (cefi/defi/sports/tradfi/prediction), which produced:

- **Code explosion**: 53 strategies today, 240+ realistic target — but mostly the same underlying logic with different
  venues
- **Hidden inconsistencies**: basis trade in `defi/basis-trade.md` vs `defi/btc-basis-trade.md` vs
  `defi/l2-basis-trade.md` are all the same archetype; different config
- **Category leakage into code**: `CEFI_ML_DIRECTIONAL_BTC` and `TRADFI_ML_DIRECTIONAL_SPY` share code but have
  different names
- **Unclear cross-cutting scope**: PnL attribution, margin health, rewards, share classes were partially duplicated per
  category

v2 fixes this by:

- **Collapsing 200+ legacy strategy variants into 53 code paths** (archetypes) served by shared family engines
- **Making every strategy config-driven**: new instances are config, not new code
- **Making categories derived labels**: execution category + data category are multi-valued tags derived from config,
  not routing axes
- **Making every cross-cutting concern its own versioned artifact**: feature groups, ML models, execution policies,
  venue capabilities, risk policies — all consumer-opt-in versioned

## 9 Families

A strategy belongs to exactly one family, determined by its **primary alpha source**. The 9th family (`PORTFOLIO`) was
added 2026-04-25 in Phase 9 for cross-category sleeves; SSOT is UAC
`unified_api_contracts.internal.architecture_v2.enums.StrategyFamily`.

| #   | Family                          | Alpha source                                                                                | Doc                                                                  |
| --- | ------------------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| 1   | **ML Directional**              | Model-predicted outcome probability vs implied                                              | [families/ml-directional.md](families/ml-directional.md)             |
| 2   | **Rules Directional**           | Hard-coded feature-threshold rules producing fire/no-fire signals                           | [families/rules-directional.md](families/rules-directional.md)       |
| 3   | **Carry & Yield**               | Rate / yield differential capture (funding, lending, staking, basis)                        | [families/carry-and-yield.md](families/carry-and-yield.md)           |
| 4   | **Arbitrage / Structural Edge** | Price dispersion or protocol mechanics (risk-free or near-risk-free payment)                | [families/arbitrage-structural.md](families/arbitrage-structural.md) |
| 5   | **Market Making**               | Bid-ask spread capture via two-sided quoting                                                | [families/market-making.md](families/market-making.md)               |
| 6   | **Event-Driven**                | Scheduled external events with measurable surprise                                          | [families/event-driven.md](families/event-driven.md)                 |
| 7   | **Vol Trading**                 | Vol-metric dislocation (IV/RV, skew, term, cross-asset vol)                                 | [families/vol-trading.md](families/vol-trading.md)                   |
| 8   | **Stat Arb / Pairs**            | Spread mean-reversion or momentum on paired underlyings                                     | [families/stat-arb-pairs.md](families/stat-arb-pairs.md)             |
| 9   | **Portfolio**                   | Cross-category sleeve allocation (multi-strategy / risk parity / factor / tactical overlay) | [families/portfolio.md](families/portfolio.md)                       |

### Family assignment decision tree

1. Is the alpha from **price dispersion**, risk-free mechanical? → **Arbitrage / Structural**
2. Is the alpha from **protocol mechanics** (liquidation bonus, yield, staking reward)? → **Arbitrage / Structural**
   (liquidation) or **Carry & Yield** (yield/basis/staking)
3. Is the alpha from a **spread between different underlyings** mean-reverting/trending? → **Stat Arb / Pairs**
4. Is the alpha from **vol metrics themselves** (IV/RV, skew, term)? → **Vol Trading**
5. Is the alpha from a **scheduled external event**? → **Event-Driven**
6. Is the alpha from **posting two-sided liquidity** and earning spread? → **Market Making**
7. Is the alpha from a **model output of outcome probability**? → **ML Directional**
8. Is the alpha from **explicit if-else rules on features**? → **Rules Directional**
9. Is the alpha from **cross-category sleeve allocation** (sub-strategies are themselves the underlyings)? →
   **Portfolio**

If it seems to straddle, identify the _primary_ alpha. "With vol overlay" where directional is primary is ML Directional
with vol hedge as risk management, not a composite.

### Rules

- **One family per strategy** — no composites, no ambiguity
- **No category prefixes on archetype IDs** — no `CEFI_ML_DIRECTIONAL`, no `TRADFI_ML_DIRECTIONAL`
- **No hybrid families** — if genuinely two alpha sources → two separate strategies sharing correlation_id

## 57 Archetypes

Archetypes distinguish different _code paths_ within a family. Distinguishing axis is usually **settlement model**
(continuous vs event-settled), **signal logic shape** (fixed basket vs cross-sectional ranking), or **structural
sub-variant** (e.g. MM passive-spread vs inventory-skew vs ML-lean; VOL spread-structures vs term-structure-arb).

The 2026-04-17 baseline shipped 18 archetypes; the Phase 9 expansion (2026-04-25) added 35 more for full coverage of MEV
(4), DeFi LP (3), Market Making sub-variants (5), VOL surface (17 variants from 1), prediction MM (1), cross-domain
event arb (1), and Portfolio sleeves (4); a subsequent split of `CARRY_RECURSIVE_STAKED` into
`CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED` brought the total to **55**; the 2026-05-18
taxonomy decision renamed `CARRY_RECURSIVE_BORROW_PERP_HEDGED` → `CARRY_BASIS_PERP_INV` (net 0) and added
`CARRY_STAKED_BASIS_DATED` + `CARRY_BASIS_DATED_INV` (+2) → **57** (uac@0196842). SSOT: UAC
`unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype` (`enum-wins` governance rule per
`strategy-summary.md:27`).

| Family                 | Archetypes                                                                                                                                                                                                                                                                                                                                                                                                                                    | Docs                     |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| ML Directional         | `ML_DIRECTIONAL_CONTINUOUS`, `ML_DIRECTIONAL_EVENT_SETTLED`                                                                                                                                                                                                                                                                                                                                                                                   | 2 docs under archetypes/ |
| Rules Directional      | `RULES_DIRECTIONAL_CONTINUOUS`, `RULES_DIRECTIONAL_EVENT_SETTLED`                                                                                                                                                                                                                                                                                                                                                                             | 2 docs                   |
| Carry & Yield          | `CARRY_BASIS_DATED`, `CARRY_BASIS_DATED_INV`, `CARRY_BASIS_PERP`, `CARRY_BASIS_PERP_INV`, `CARRY_STAKED_BASIS`, `CARRY_STAKED_BASIS_DATED`, `CARRY_RECURSIVE_STAKED`, `CARRY_RECURSIVE_BORROW_LENDING_ONLY`, `YIELD_ROTATION_LENDING`, `YIELD_STAKING_SIMPLE`                                                                                                                                                                                 | 10 docs                  |
| Arbitrage / Structural | `ARBITRAGE_PRICE_DISPERSION`, `LIQUIDATION_CAPTURE`, `ARBITRAGE_MEV_SANDWICH`, `ARBITRAGE_MEV_JIT_LIQUIDITY`, `ARBITRAGE_MEV_BACKRUN`, `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`, `ARBITRAGE_CROSS_DOMAIN_EVENT`                                                                                                                                                                                                                                     | 7 docs                   |
| Market Making          | `MARKET_MAKING_CONTINUOUS` (legacy), `MARKET_MAKING_EVENT_SETTLED` (sports exchange back/lay — not legacy), `MARKET_MAKING_PASSIVE_SPREAD`, `MARKET_MAKING_INVENTORY_SKEW`, `MARKET_MAKING_ML_LEAN`, `MARKET_MAKING_QUEUE_MICROSTRUCTURE`, `MARKET_MAKING_PREDICTION`, `DEFI_LP_CONCENTRATED`, `DEFI_LP_POOL`, `DEFI_LP_VAULT`                                                                                                                | 10 docs                  |
| Event-Driven           | `EVENT_DRIVEN`                                                                                                                                                                                                                                                                                                                                                                                                                                | 1 doc                    |
| Vol Trading            | `VOL_TRADING_OPTIONS` (legacy), `VOL_ARB_RV_IV`, `VOL_SPREAD_STRUCTURES`, `VOL_CARRY`, `VOL_OVERLAY_COVERED_CALLS`, `VOL_OVERLAY_PROTECTIVE_PUT`, `VOL_STRADDLE`, `VOL_SYNTHETIC_DELTA`, `VOL_MARKET_MAKING`, `VOL_ML_LEAN`, `VOL_0DTE_GAMMA_SCALPING`, `VOL_0DTE_PIN_RISK`, `VOL_TERM_STRUCTURE_ARB`, `VOL_TERM_STRUCTURE_SLOPE`, `VOL_DISPERSION`, `VOL_VARIANCE_SWAP`, `VOL_LEAPS_CONVEXITY`, `VOL_CROSS_ASSET_SPREAD`, `VOL_RATIO_SPREAD` | 19 docs                  |
| Stat Arb / Pairs       | `STAT_ARB_PAIRS_FIXED`, `STAT_ARB_CROSS_SECTIONAL`                                                                                                                                                                                                                                                                                                                                                                                            | 2 docs                   |
| Portfolio              | `PORTFOLIO_MULTI_STRATEGY`, `PORTFOLIO_RISK_PARITY`, `PORTFOLIO_FACTOR_ALLOCATION`, `PORTFOLIO_TACTICAL_OVERLAY`                                                                                                                                                                                                                                                                                                                              | 4 docs                   |

**Total: 57 archetypes.** Every strategy maps to exactly one. Per-archetype docs under `archetypes/` cover the May-23
live + immediate-backtest subset; the Phase 9 expansions are catalogued in the UAC enum + cross-referenced from
[`category-instrument-coverage.md`](category-instrument-coverage.md).

**Rule:** archetype IDs use structural descriptors (continuous vs event*settled, fixed vs cross_sectional, sub-variant
qualifiers like `_PASSIVE_SPREAD` / `_RV_IV` / `\_MEV*\*`), never category prefixes.

## 7 Axes of Composition

| #   | Axis              | Values                                                                                                          | Doc                                                    |
| --- | ----------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| 1   | Signal source     | ML, rules, TA, funding-rate, yield-spread, event-schedule, orderbook, liquidation-watcher, greeks, mempool      | [axes/signal-sources.md](axes/signal-sources.md)       |
| 2   | Edge method       | value (model_prob > implied), rate-differential, spread-capture, arb, z-score, momentum, vol-divergence         | [axes/edge-methods.md](axes/edge-methods.md)           |
| 3   | Staking method    | Kelly, fractional-Kelly, fixed-%, fixed-notional, confidence-scaled, vol-scaled, delta-paired, inventory-skewed | [axes/staking-methods.md](axes/staking-methods.md)     |
| 4   | Venue eligibility | Set of eligible venues + constraints; slow-moving; config-level                                                 | [axes/venue-eligibility.md](axes/venue-eligibility.md) |
| 5   | Expression        | spot, perp, atm_call, 25d_call, synthetic, LP, basket, auto                                                     | [axes/expression.md](axes/expression.md)               |
| 6   | Hold policy       | SAME_CANDLE_EXIT, HOLD_UNTIL_FLIP, CONTINUOUS, ONE_SHOT                                                         | [axes/hold-policy.md](axes/hold-policy.md)             |
| 7   | Share class       | USDT, USDC, ETH, BTC, USD, GBP, EUR, SOL — fixed at instance creation                                           | [axes/share-class.md](axes/share-class.md)             |

## 10 Cross-Cutting Concerns

| #   | Concern                                                                                           | Doc                                                                                        |
| --- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| 1   | Risk gates (4-layer)                                                                              | [cross-cutting/risk-gates.md](cross-cutting/risk-gates.md)                                 |
| 2   | Venue selection (eligibility slow-path + SOR fast-path)                                           | [cross-cutting/venue-selection-split.md](cross-cutting/venue-selection-split.md)           |
| 3   | Execution policies (rule-table per venue×action×condition, artifact-versioned)                    | [cross-cutting/execution-policies.md](cross-cutting/execution-policies.md)                 |
| 4   | Transfer / rebalance (venue-level capital movement service)                                       | [cross-cutting/transfer-rebalance.md](cross-cutting/transfer-rebalance.md)                 |
| 5   | Portfolio Allocator (strategy-level capital allocation; 8 allocator archetypes)                   | [cross-cutting/portfolio-allocator.md](cross-cutting/portfolio-allocator.md)               |
| 6   | MEV protection (DeFi execution policy for private-mempool routing)                                | [cross-cutting/mev-protection.md](cross-cutting/mev-protection.md)                         |
| 7   | Benchmark fills contract (batch = live; batch returns zero exec alpha)                            | [cross-cutting/benchmark-fills.md](cross-cutting/benchmark-fills.md)                       |
| 8   | Capital / client isolation                                                                        | [cross-cutting/capital-client-isolation.md](cross-cutting/capital-client-isolation.md)     |
| 9   | Trade expression (per-instruction spot/perp/options/synthetic)                                    | [cross-cutting/trade-expression.md](cross-cutting/trade-expression.md)                     |
| 10  | Venue-account coordination (shared-account primitives: aggregation, pre-flight, atomic rebalance) | [cross-cutting/venue-account-coordination.md](cross-cutting/venue-account-coordination.md) |

## Capital Flow Lifecycle (end-to-end)

Capital moves through the system at **three scopes** with a single unified event-driven primitive. Understanding this is
core to the architecture because it cuts across every cross-cutting concern and connects directly to regulatory
structure, wallet custody, onboarding, and fund versus SMA modes.

### The three scopes of capital flow

| Scope        | Moves between                                                          | Service owner                                                       | Typical trigger                                                                    |
| ------------ | ---------------------------------------------------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **Venue**    | Venues within one strategy (or shared across strategies on an account) | [Transfer / Rebalance service](cross-cutting/transfer-rebalance.md) | Balance drift, margin health warning, strategy capital request, bridge opportunity |
| **Strategy** | Strategies within one client's portfolio                               | [Portfolio Allocator service](cross-cutting/portfolio-allocator.md) | Allocator cadence, PnL change, performance review, manual client adjustment        |
| **Client**   | Clients within the platform (or treasury-to-client)                    | Platform Treasury + onboarding                                      | Client deposit, client withdrawal, fund subscription/redemption                    |

All three emit `TRANSFER` / `BRIDGE` / `AllocationDirective` events. Receiving strategy or service reconciles. **One
code path for all three scopes.**

### Per-category capital ownership model

Strategy families sit on top of venue categories, and each venue category has a distinct capital custody model with
different regulatory context. This directly shapes how transfers happen, where money starts, what the onboarding flow
looks like, and what the Treasury wallet concept means.

| Venue category                   | Custody model                           | Wallet structure                                                                                                            | Regulatory mode                                                                                   | Onboarding                                                                                                     |
| -------------------------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **DeFi (EVM + Solana)**          | Client wallet (default) or firm-managed | Client wallet typically accessed via Copper or Fireblocks; multi-sig MPC; we interact via custodian API for signing         | Not regulated in most jurisdictions as we interact with client's own wallet with their permission | Client onboards a wallet to Copper/Fireblocks, grants us signing permission; no transfer of funds to us        |
| **Sports (Unity prime broker)**  | Firm-managed pooled wallet              | Single Unity account per firm (not per client); Unity's unified wallet funds 10 sportsbooks                                 | Not regulated as trading activity in our permission set; pooling allowed under firm wallet        | Client contributes to Unity pool (fund-like structure); shares in P&L allocated proportionally                 |
| **CeFi (initially SMA)**         | Client account (SMA)                    | Client opens account at Binance/OKX/Bybit/Hyperliquid/Deribit, deposits, shares API keys with us, we trade on their account | SMA — separately managed account, client retains custody of assets at the exchange                | Client opens CEX account, deposits, generates API keys with trading permission (no withdrawal), shares with us |
| **CeFi (future fund structure)** | Firm treasury + firm exchange accounts  | Firm Treasury wallet → firm CEX accounts; client holds fund shares                                                          | Fund structure (third-party administrator); investor shares with proportional P&L                 | Investor subscribes to fund; we handle all wallet operations                                                   |
| **TradFi (initially IBKR)**      | Own money + SMA via IBKR tunnels        | Firm IBKR account for firm money; per-SME-client IBKR tunnel account for SMA clients                                        | SMA via IBKR tunnel (regulated IBKR custody); firm own-money from firm balance sheet              | SMA client opens IBKR tunnel, deposits, grants FIX API trading permission                                      |
| **TradFi (counterparty direct)** | Counterparty custody                    | Direct connection to counterparty's execution infra; they hold funds                                                        | Counterparty-arranged; we provide trading service                                                 | Counterparty connects directly; we receive allocation                                                          |

### Wallet movement patterns per category

Different categories have fundamentally different patterns for where money starts and how it moves during trading.

#### DeFi (client wallet → on-chain execution)

```
Client Copper/Fireblocks wallet
  │
  │ (we request signing via custodian API)
  ▼
Trading wallet (on-chain, client-owned)
  │
  │ (we execute on-chain tx: swap, lend, stake, transfer)
  ▼
Positions on Uniswap / Aave / Lido / etc.
```

**Inter-chain movements:** If strategy is multi-chain (e.g., yield rotation across Ethereum + Arbitrum + Optimism),
client wallet must exist on each chain, OR we emit `BRIDGE` instructions to move funds between client's wallet on each
chain using bridges (Circle CCTP, LayerZero, Stargate, etc.). Bridge config per chain pair lives in UAC venue capability
registry.

**Inter-protocol movements on same chain:** Between Aave, Uniswap, Lido, etc., we emit `TRANSFER` instructions — in DeFi
context, these are approvals + swaps + deposits, sometimes as ATOMIC multi-leg via multicall.

#### Sports (single pooled Unity wallet → 10 child books)

```
Firm Unity wallet (one account)
  │
  │ (Unity API routes to chosen child book per bet)
  ▼
Child book wallets (10 books managed by Unity)
  │
  │ (bets settled into Unity balance)
  ▼
Back to Unity central balance
```

**No inter-book transfers required** — Unity holds a central balance that funds all child books. A bet on Smarkets via
Unity and a bet on Betfair via Unity both debit/credit the same central balance. This is the key operational advantage
of Unity vs direct-book execution.

**Cash in / out:** Crypto deposits/withdrawals to Unity wallet (near-instant after semi-automated 1-tx wait). Rollover
requirement: deposits must be wagered at least 1x before withdrawal.

**Movement instructions:** Mostly just `TRADE` on Unity (Unity's API picks child book based on our specified eligible
books). Rarely `TRANSFER` — occasionally between Unity and firm treasury for capital planning.

#### CeFi (SMA mode — client CEX account)

```
Client CEX account (Binance / OKX / Bybit / Deribit / Hyperliquid)
  │
  ├── Funding wallet (deposited capital)
  │
  │ (we move between wallets if needed)
  │
  └── Trading wallet / cross-margin wallet
         │
         ▼
       Positions (spot, perp, options)
```

**Internal-to-venue transfers:** Binance has Funding wallet vs USD-M Futures wallet vs COIN-M Futures wallet vs Margin
wallet. We emit `TRANSFER` instructions to move between them on the client's account. Execution-service's Binance
adapter handles internal transfers via Binance's SAPI.

**Cross-venue transfers under SMA:** Generally not done — each SMA is per-venue. If a client has multiple venues, each
has its own SMA and its own API keys. We don't transfer between CEX A and CEX B unless client explicitly requests it
(rare).

**Cash in / out:** Client deposits/withdrawals happen directly between client bank/crypto wallet and the CEX. We don't
touch these. Our scope is only trading via API keys.

#### CeFi (future fund mode)

```
Firm Treasury wallet (aggregated investor capital via third-party administrator)
  │
  │ (we move per allocation policy)
  ▼
Firm CEX accounts (Binance / OKX / Bybit / Deribit / Hyperliquid)
  │
  │ (per-CEX funding → trading wallet transfers)
  ▼
Positions
```

**Inter-venue transfers:** Now possible because all accounts are firm-owned. Transfer/Rebalance service moves funds
between CEXes based on allocation policy + margin health.

**Cash in / out:** Investors subscribe/redeem fund shares via third-party administrator. Administrator moves fiat into
Treasury on subscription; out from Treasury on redemption. We manage the on-chain / CEX side.

#### TradFi (initially IBKR, moving to counterparty direct)

```
Firm IBKR account (own money)
  │
  ├── Separate sub-account per SMA client (tunnel structure)
  │
  │ (each tunnel = separate client SMA; we trade per tunnel)
  ▼
Positions (equities, futures, options, FX)
```

**Inter-venue transfers in TradFi:** IBKR routes to NYSE/NASDAQ/LSE/CME/CBOE/ICE automatically — we don't manage
per-venue transfers. IBKR is a meta-gateway.

**Cash in / out:** Client onboards to IBKR tunnel, deposits to their tunnel, trades via our API. We never hold client
funds.

**Counterparty direct (later):** Replaces per-SMA tunnels. Counterparty connects directly, routes via their own infra,
we just send instructions. Capital doesn't move through us at all.

### Treasury wallet concept (where it applies)

A **Treasury wallet** is a firm-owned holding venue for idle capital. It exists when:

- **DeFi with firm capital** — we hold a firm-owned on-chain Treasury for our own capital used in DeFi strategies (not
  client capital, which stays in client's Copper/Fireblocks wallet)
- **Sports (Unity pool)** — the Unity pool itself is conceptually the Treasury for sports
- **CeFi fund mode (future)** — explicit Treasury aggregating investor subscriptions before deployment
- **CeFi SMA mode (current)** — no firm Treasury; client deposits directly to their CEX

Transfer/Rebalance service treats Treasury as a node in its graph. When margin health drops on a CEX account (or DeFi
position), Transfer/Rebalance can top up from Treasury via:

- **CeFi SMA:** not applicable — client tops up, not us
- **CeFi fund mode:** Treasury → CEX via deposit address
- **DeFi firm capital:** Treasury wallet → on-chain transfer to trading wallet
- **Sports:** Unity pool → affected account (internal Unity mechanic)

### Capital flow as events

All capital movements are event-driven. Here's the full event catalog:

| Event                      | Producer                       | Consumer(s)                                 | Resulting action                                                                  |
| -------------------------- | ------------------------------ | ------------------------------------------- | --------------------------------------------------------------------------------- |
| `CLIENT_DEPOSIT`           | Onboarding / treasury service  | Portfolio Allocator, PBMS                   | Equity changes → Allocator re-weights → strategies re-emit targets                |
| `CLIENT_WITHDRAWAL`        | Onboarding / treasury service  | Portfolio Allocator, Transfer/Rebalance     | Allocator reduces weights; Transfer/Rebalance frees capital; positions close      |
| `ALLOCATION_REVIEW_DUE`    | Portfolio Allocator (schedule) | Allocator itself                            | Recompute weights; emit AllocationDirective per strategy                          |
| `AllocationDirective`      | Portfolio Allocator            | Strategy instances                          | Strategy updates equity; recomputes target; emits StrategyInstruction             |
| `MARGIN_HEALTH_WARNING`    | R&E service                    | Transfer/Rebalance                          | Plan top-up from Treasury (if available); escalate to allocation reduction if not |
| `VENUE_BALANCE_DRIFT`      | Transfer/Rebalance (schedule)  | Transfer/Rebalance itself                   | Plan TRANSFER to rebalance per venue allocation policy                            |
| `STRATEGY_CAPITAL_REQUEST` | Strategy instance              | Transfer/Rebalance                          | Move capital to enable new position                                               |
| `POSITION_UPDATED`         | PBMS (after fill)              | R&E, Portfolio Allocator                    | Re-evaluate margin health; re-weight if PnL-based allocator                       |
| `VENUE_EVACUATION`         | R&E, ops                       | Transfer/Rebalance, all strategies on venue | Close all positions; withdraw funds if possible                                   |

### Worked example 1: DeFi yield rotation across 3 chains + margin rescue

**Setup:** Client has $1M, strategy `YIELD_ROTATION_LENDING@aave-multichain-usdc-prod` runs on Aave across Ethereum,
Arbitrum, Optimism. Client wallet is in Copper.

```
t=0, initial state:
  Copper client wallet: $1M USDC on Ethereum

t=0, strategy computes targets based on APY:
  Target: {ETH: $400k, ARB: $300k, OPT: $300k}

t=0, strategy emits:
  TRANSFER (bridge) $300k Ethereum → Arbitrum (via Circle CCTP)
  TRANSFER (bridge) $300k Ethereum → Optimism (via Circle CCTP)
  [wait for bridges to settle ~5-20 min]
  LEND(aave_ethereum, $400k, target_supplied=$400k)
  LEND(aave_arbitrum, $300k, target_supplied=$300k)
  LEND(aave_optimism, $300k, target_supplied=$300k)

t=1h, Arbitrum APY drops, Optimism APY rises:
  Strategy recomputes: {ETH: $400k, ARB: $200k, OPT: $400k}

t=1h, strategy emits:
  LEND(aave_arbitrum, target_supplied=$200k)   [withdraws $100k]
  BRIDGE Arbitrum → Optimism $100k
  LEND(aave_optimism, target_supplied=$400k)   [deposits $100k]

t=2h, Aave Ethereum has a health-factor scare due to ETH price move:
  R&E publishes MARGIN_HEALTH_WARNING  (not applicable for simple lending, but
  if it were a leveraged CARRY_RECURSIVE_STAKED strategy on Aave, this would fire)

t=3h, client deposits another $500k USDC:
  Onboarding emits CLIENT_DEPOSIT event
  Allocator recomputes: if strategy is 100% of client capital, new equity = $1.5M
  AllocationDirective emitted to strategy: new_equity = $1.5M
  Strategy recomputes targets: {ETH: $600k, ARB: $300k, OPT: $600k}
  Emits more LEND + BRIDGE instructions to reach new targets
```

### Worked example 2: CeFi basis + directional on same Binance account (SMA)

**Setup:** Client has $1M SMA at Binance. Two strategies running on this single account:

- `CARRY_BASIS_PERP@binance-btc-usdt-prod` (basis, 7% capital, using cross-margin netting)
- `ML_DIRECTIONAL_CONTINUOUS@binance-btc-usdt-prod` (directional, 93% capital)

```
t=0, Allocator initial state:
  Basis strategy equity: $70k
  Directional strategy equity: $930k

Basis strategy emits:
  TRADE(spot BTC, target=+$70k worth, buy)
  TRADE(perp BTC, target=-$70k worth, sell)
  → Delta-neutral basis position; Binance nets margin to ~5% = $3.5k used

Directional strategy has $930k of collateral available (not $1M because $70k is
in spot+perp netted at $3.5k margin; practical available collateral ~$926.5k).

Directional strategy emits:
  TRADE(perp BTC, target=+$200k long)  based on ML signal
  → Pre-flight check: combined account health OK, approve
  → Fill; position updated

t=1h, funding rate on Binance BTC perp drops below threshold:
  Basis strategy re-evaluates: no longer worth holding
  Emits ATOMIC (must unwind both legs without breaching margin):
    close spot + close perp in one multicall
  → Execution uses Binance batch order API
  → Basis strategy equity freed → $70k back to cash

t=1h+1min, Allocator sees basis strategy idle:
  AllocationDirective to basis: new_equity = $0 (PAUSE)
  AllocationDirective to directional: new_equity = $1M (all capital)
  Directional strategy recomputes: can use more collateral now
  Emits TRADE to increase position to target based on new equity
```

### Worked example 3: Sports via Unity (single pooled wallet, pre-match + live)

**Setup:** Firm-managed Unity pool with $200k. Multiple strategies subscribe:

- `ARBITRAGE_PRICE_DISPERSION@unity-epl-1x2-usd-prod`
- `ML_DIRECTIONAL_EVENT_SETTLED@unity-epl-1x2-usd-prod`
- `MARKET_MAKING_EVENT_SETTLED@betfair-epl-mm-gbp-prod` (direct Betfair, not Unity)

```
t=0, Allocator state:
  Arb strategy equity: $60k   (30% — less allocation, higher Sharpe)
  Value betting equity: $100k (50% — main sports strategy)
  MM (Betfair direct) equity: $40k (20% — different venue, separate wallet)

t=0, strategies emit bets:
  Arb sees cross-book arb opportunity Manchester United 1X2:
    TRADE(unity child_book=Smarkets, back home, $5k)
    TRADE(unity child_book=3ET, lay home, equivalent $5k)
    → Unity executes both on single wallet; P&L guaranteed regardless of result
    → No transfer needed between books; Unity nets

  Value betting signals on another match:
    TRADE(unity, 1X2, draw, $8k)   [preferred book = VX, 0.2% commission]
    → Unity routes to VX, places bet, debits wallet

  MM places quotes on Betfair direct:
    QUOTE(betfair_direct, Man Utd vs Chelsea 1X2, spread 1 tick)
    → Separate wallet, separate API; MM lives independently from Unity strategies

t=match ends, bets settle:
  Unity wallet balance updates with wins/losses per strategy
  PBMS attributes fills per strategy (via correlation_id on each order)
  PnL per strategy available in reporting

t=monthly review, Unity subscription waiver check:
  R&E computes total effective turnover = absolute_wins + absolute_losses over month
  If < $260k, emit SUBSCRIPTION_FEE_WARNING event
  Allocator notified: may increase sports allocation to hit threshold

t=client deposits more:
  CLIENT_DEPOSIT $100k USD
  Allocator recomputes weights; emits new AllocationDirectives
  Sports strategies get more allocation; place more bets on next signal
```

### Regulatory quick reference by strategy family × category

(Full detail in `04-architecture/capital-structure-and-regulatory.md`.)

| Family                            | Typical category               | Custody model                                 | Transfer flows we own                                                                 |
| --------------------------------- | ------------------------------ | --------------------------------------------- | ------------------------------------------------------------------------------------- |
| ML Directional (continuous)       | CEFI / TRADFI                  | Client SMA (CeFi) or IBKR tunnel (TradFi)     | Internal venue wallet moves only                                                      |
| ML Directional (event-settled)    | SPORTS / PREDICTION            | Firm pooled (Unity) or firm Polymarket wallet | Treasury ↔ Unity; rarely moves                                                       |
| Rules Directional (continuous)    | CEFI / TRADFI                  | Client SMA / IBKR tunnel                      | Internal venue moves                                                                  |
| Rules Directional (event-settled) | SPORTS                         | Firm pooled (Unity)                           | Treasury ↔ Unity                                                                     |
| Carry & Yield (all)               | DEFI / CEFI                    | DeFi client wallet / CeFi SMA                 | Bridges + on-chain tx (DeFi); internal wallet moves (CeFi); no cross-client transfers |
| Arbitrage / Structural            | All                            | Varies                                        | ATOMIC multi-leg for fungible arb; multi-wallet per leg for cross-venue               |
| Market Making                     | All                            | Varies                                        | Quote lifecycle on single venue typically                                             |
| Event-Driven                      | CEFI / TRADFI                  | Client SMA / IBKR tunnel                      | Internal venue moves                                                                  |
| Vol Trading                       | CEFI (Deribit) / TRADFI (CBOE) | Client SMA / IBKR tunnel                      | Internal venue moves                                                                  |
| Stat Arb / Pairs                  | TRADFI / CEFI                  | IBKR tunnel / Client SMA                      | Paired leg execution; rare cross-venue moves                                          |

### Key takeaways

1. **The same capital-flow primitive** covers DeFi bridges, CEX internal transfers, Unity pool operations, and TradFi
   tunnel deposits — all via `TRANSFER` / `BRIDGE` / `AllocationDirective` events.
2. **SMA vs fund mode** changes WHO owns wallets but doesn't change the protocol — strategies + execution + PBMS + R&E
   behave identically; only custodial plumbing differs.
3. **Treasury wallet** is optional, used only where firm-managed capital is pooled (DeFi firm capital, Unity pool,
   future CeFi fund, own-money IBKR).
4. **Margin health, allocation, and equity changes all flow through the same unified event bus** — no bespoke
   per-category capital logic.
5. **Cross-category aggregation at portfolio level** is handled by the Portfolio Allocator regardless of underlying
   custody mode.

See [capital-flow-model](../../04-architecture/capital-flow-model.md) for the mechanical protocol, and
[capital-structure-and-regulatory](../../04-architecture/capital-structure-and-regulatory.md) for per-category custody,
onboarding, regulatory context, and fund-vs-SMA mode transitions.

## 5-Layer Identity Model

```
1. FAMILY                   — orthogonal alpha style (9 values; never changes)
2. ARCHETYPE                — code path under family (57 values; build-versioned)
3. STRATEGY INSTANCE        — slot: archetype + client_id + capital + risk_budget
                              + share_class + slot_label
4. CONFIG                   — hash-identified content: venues, instruments, feature/
                              model/policy refs, thresholds, lookbacks, Kelly, risk
                              limits, rebalance cadence, staking method
5. DERIVED CATEGORIES       — execution_categories + data_categories (multi-valued
                              lists, for UI/reporting)
```

Plus optional **slot version suffix** (`v1`, `v2`, ...) for material dependency changes that warrant human-visible
distinction (model family swap, venue swap, feature group major version).

**Full event tag** on every fill, instruction, PnL row, audit entry:

```
(family, archetype_id, archetype_build_version, strategy_instance_id,
 slot_version, config_hash, config_version, client_id, share_class)
```

### Slot label grammar

```
{archetype_id}@{venue_scope}-{instrument_scope}[-{timeframe}]-{share_class}[-v{N}]-{env}
```

Examples:

```
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-v2-prod       (model swap, same archetype)
CARRY_BASIS_PERP@uniswap-hyperliquid-eth-usdt-prod
CARRY_STAKED_BASIS@lido-aave-hyperliquid-eth-prod
CARRY_STAKED_BASIS@jito-drift-f100-usdc-1h-usdc-v2-prod    # Solana-native: JitoSOL as Drift cross-margin
CARRY_STAKED_BASIS@marinade-drift-f100-usdc-1h-usdc-v2-prod # Solana-native: mSOL as Drift cross-margin
YIELD_ROTATION_LENDING@aave-multichain-usdc-prod
ARBITRAGE_PRICE_DISPERSION@unity-epl-1x2-usd-prod
MARKET_MAKING_EVENT_SETTLED@betfair-epl-mm-gbp-prod
STAT_ARB_PAIRS_FIXED@ibkr-goog-meta-daily-usd-prod
VOL_TRADING_OPTIONS@deribit-btc-vol-usdt-prod
```

Full naming convention:
[../../06-coding-standards/strategy-identity-versioning.md](../../06-coding-standards/strategy-identity-versioning.md).

## Polymorphic StrategyInstruction (14 action types)

SSOT: UAC `unified_api_contracts.internal.architecture_v2.enums.InstructionActionV2`. Phase 9 added the last 3
(`CONVERT_DUST` / `LP_MINT` / `LP_BURN`) for the DeFi LP archetypes.

| #   | Action         | Target semantics                                      |
| --- | -------------- | ----------------------------------------------------- |
| 1   | `TRADE`        | position_units on instrument                          |
| 2   | `SWAP`         | one-shot fungible exchange                            |
| 3   | `LEND`         | supplied_amount on lending protocol                   |
| 4   | `BORROW`       | debt_amount on lending protocol                       |
| 5   | `STAKE`        | staked_amount on staking protocol                     |
| 6   | `UNSTAKE`      | unstake amount                                        |
| 7   | `QUOTE`        | continuous two-sided quote with spread + inventory    |
| 8   | `TRANSFER`     | target balance at same-chain destination              |
| 9   | `BRIDGE`       | cross-chain move                                      |
| 10  | `ATOMIC`       | multi-leg bundle (all-or-nothing)                     |
| 11  | `CANCEL`       | abort prior instruction by ID                         |
| 12  | `CONVERT_DUST` | sweep small leftover balances back to share-class     |
| 13  | `LP_MINT`      | open LP position (Uniswap V3 NPM mint / pool deposit) |
| 14  | `LP_BURN`      | close LP position (NPM burn / pool withdraw)          |

Plus parallel **`AccountInstruction`** (operator-driven) for CLOSE_ALL, SET_MARGIN_MODE, EMERGENCY_LIQUIDATE,
TRANSFER_SUBACCOUNT.

Full spec: [../../04-architecture/strategy-execution-protocol.md](../../04-architecture/strategy-execution-protocol.md).

## 5 Protocol Rules (strategy ↔ execution)

1. **Target state, not deltas** — idempotent reconciliation
2. **Intent + constraints, not algo prescriptions** — strategy says what/by when; execution picks how
3. **Polymorphic targets** — target semantics differ per action type
4. **Portfolio at strategy, instrument at execution, account at venue-coordination**
5. **Benchmark fills contract** — batch returns zero exec alpha; live measures alpha vs benchmark

## 3-Axis Versioning

| Axis             | Tracks                         | Versioned by             | Trigger         |
| ---------------- | ------------------------------ | ------------------------ | --------------- |
| **Code / Build** | Source code                    | Git SHA, semver          | Any code change |
| **Artifact**     | Runtime config / trained model | Content hash + monotonic | Content change  |
| **Schema**       | Data format / wire contract    | UAC semver               | Format change   |

Artifacts in the system — all versioned, all consumer-opt-in:

- Feature groups, ML models, execution policies, allocator algorithms, risk policies, venue capabilities, strategy
  archetypes, strategy configs, schema versions

Rule: consumers reference artifacts by explicit version. No auto-upgrade. Version bumps are deliberate opt-in.

Full model: [../../04-architecture/artifact-versioning.md](../../04-architecture/artifact-versioning.md).

## 3 Backtest Groups

| Group                  | Owner               | Fixed                                             | Dynamic                                            | Output             |
| ---------------------- | ------------------- | ------------------------------------------------- | -------------------------------------------------- | ------------------ |
| **A. ML Training**     | ml-training-service | Data, target, features, model family              | Hyperparameters, splits, calibration               | Versioned models   |
| **B. Strategy**        | strategy-service    | Archetype, venues, features, models, settlement   | Thresholds, Kelly, lookbacks, staking, risk limits | Deployable configs |
| **C. Execution Alpha** | execution-service   | Strategy instruction stream, venue microstructure | Algo choice, params, MEV, routing                  | Execution policies |

Benchmark fills contract binds them: Group B uses benchmark fills (zero exec alpha) so strategy alpha is isolated.

Full framework: [../../04-architecture/backtest-groups.md](../../04-architecture/backtest-groups.md).

## Venue Architecture (summary)

Venues classified into:

- **SINGLE_VENUE** — one endpoint, one account
- **META_BROKER** — one endpoint, one wallet, multiple child books (Unity for sports, IBKR for TradFi)
- **DATA_AGGREGATOR** — data only, no execution

Every venue declares: supported operations, supported instruments, collateral rules (with haircuts), liquidation spec,
margin netting rules, commission/fee structure.

Full venue list: [../../02-venues/venue-registry-reference.md](../../02-venues/venue-registry-reference.md). Prime
brokers: [../../02-venues/prime-brokers.md](../../02-venues/prime-brokers.md). Unity:
[../../02-venues/unity-integration.md](../../02-venues/unity-integration.md).

## Non-Negotiable Principles

1. **One family per strategy** — no composites
2. **Category is label, family is code** — no routing on category
3. **Artifact references by explicit version** — no auto-upgrade anywhere
4. **Target state, not deltas** — idempotent reconciliation
5. **Batch = live same code path** — benchmark fills contract bridges them
6. **UAC is single source of truth** — types, schemas, registries, compatibility
7. **Strategy P&L isolates from execution alpha** — via benchmark fills
8. **Every change is auditable** — full 9-field tuple on every event

## Document Layout (v2)

```
codex/
├── 02-venues/                            ← new
│   ├── venue-registry-reference.md       (authoritative venue list)
│   ├── prime-brokers.md                  (meta-broker model, Unity, IBKR)
│   └── unity-integration.md              (Unity technical spec)
│
├── 03-services/
│   ├── portfolio-allocator.md            ← new (8 allocator archetypes)
│   └── venue-capability-registry.md      ← new (UAC registry)
│
├── 04-architecture/                      ← new
│   ├── strategy-execution-protocol.md    (5 rules + instruction catalog)
│   ├── artifact-versioning.md            (3-axis model)
│   ├── execution-policy.md               (rule-table grammar)
│   ├── backtest-groups.md                (A/B/C + fixed/dynamic)
│   ├── capital-flow-model.md             (unified primitive)
│   ├── schema-versioning.md              (UAC schema migrations)
│   ├── slow-fast-routing-split.md        (strategy vs execution routing)
│   ├── capital-efficiency-patterns.md    (shared account + netting)
│   └── account-instructions.md           (operator-driven ops)
│
├── 06-coding-standards/
│   ├── strategy-identity-versioning.md   ← new
│   └── artifact-naming.md                ← new
│
└── 09-strategy/
    ├── README.md                         (legacy pointer; points to architecture-v2/)
    ├── architecture-v2/                  ← NEW canonical structure
    │   ├── README.md                     (this document)
    │   ├── MIGRATION.md                  (old doc → new archetype audit)
    │   ├── families/                     (9 docs)
    │   ├── archetypes/                   (57 docs — all archetypes documented; full enum in UAC SSOT)
    │   ├── axes/                         (7 docs)
    │   └── cross-cutting/                (10 docs)
    ├── cefi/                             (legacy, migrated via MIGRATION.md)
    ├── defi/                             (legacy)
    ├── sports/                           (legacy)
    ├── tradfi/                           (legacy)
    ├── prediction/                       (legacy)
    ├── cross-cutting/                    (some still canonical; see MIGRATION.md)
    └── templates/                        (preserved)
```

## Strategy Universe (v1 target post-migration)

- **Existing 53 strategies** → mapped onto (archetype, instance, config) triples per [MIGRATION.md](MIGRATION.md)
- **+~70-100 new instances** from natural archetype combinatorics (single-venue variants, share-class variants,
  Unity-enabled sports expansion)
- **Near-term live**: ~70-80 active instances
- **v1 target ceiling**: ~240-250 instances
- **Hard ceiling given venue coverage**: ~300-350

Full breakdown by archetype: see [archetypes/\*.md](archetypes/).

## Migration Status

See [MIGRATION.md](MIGRATION.md) for the complete audit of every existing doc and code module against v2 placement,
including:

- Old doc path → new archetype doc path
- Legacy strategy ID → new (archetype, slot_label) pair
- Functional delta (kept same / enhanced / retired)
- Migration phase (Wave 1 docs, Wave 2 code, Wave 3 UI)

No old doc is discarded without an explicit mapping. No existing functionality is lost — at worst it's enhanced.

## Implementation Phasing

See [../../plans/active/](../../../plans/active/) for the active week-to-live implementation plan. Key phases:

1. **Wave 1 (Day 1-2)**: Codex v2 docs + UAC schemas + retired CeFi venue cleanup
2. **Wave 2 (Day 3-4)**: strategy-service family engines + execution-service polymorphic orchestrator +
   portfolio-allocator-service + Unity adapter
3. **Wave 3 (Day 5)**: PBMS venue-account projection + R&E pre-flight + feature/ML versioning
4. **Wave 4 (Day 6)**: UI family navigation + backtest runners
5. **Wave 5 (Day 7)**: Migration execution + shadow deploy + cutover

## Authoring Conventions

Every archetype doc follows a standard structure (see [templates/archetype-doc.md](templates/archetype-doc.md)):

1. **What & why** — alpha source, edge thesis, position structure
2. **Token / position flow** — step-by-step bankroll + instruction sequence
3. **Instruments & venues** — eligible venue patterns, instrument types, expression
4. **Features & signals consumed** — required feature groups, model dependencies
5. **Edge method + staking + risk** — how edge is computed, sized, bounded
6. **Execution policy** — recommended policy ref, algo preferences per action
7. **P&L attribution** — components and settlement mechanics
8. **Risk profile** — expected drawdown, Sharpe, liquidation risks
9. **Kill-switch triggers** — conditions for auto-halt
10. **Example instances** — 2-3 worked examples with slot labels + config highlights
11. **Migration from legacy** — which old doc(s) this replaces + functional deltas

Family docs follow a similar structure focused on shared primitives across their archetypes.

## Next Steps for Readers

- **Implementers** — read
  [04-architecture/strategy-execution-protocol.md](../../04-architecture/strategy-execution-protocol.md) +
  [06-coding-standards/strategy-identity-versioning.md](../../06-coding-standards/strategy-identity-versioning.md)
- **Strategy designers** — read [families/\*.md](families/) for your family, then [archetypes/\*.md](archetypes/) for
  specific archetypes
- **Operators** — read [cross-cutting/portfolio-allocator.md](cross-cutting/portfolio-allocator.md) +
  [cross-cutting/venue-account-coordination.md](cross-cutting/venue-account-coordination.md)
- **UI/Reporting** — read this README + [axes/share-class.md](axes/share-class.md) +
  [cross-cutting/portfolio-allocator.md](cross-cutting/portfolio-allocator.md)

## Deployment & Isolation

Every archetype has deployment-topology requirements: which services must be isolated per client, which must be
co-located for latency, and the minimum SLA tier that satisfies it. These are declared in each archetype doc via a
`topology_requirements` frontmatter block. Execution-service is always isolated; strategy-service isolation depends on
the archetype (MM needs isolated + co-located; ML / rules accept shared).

**SSOT:**
[../../04-architecture/client-isolation-sla-and-runtime-profiles.md](../../04-architecture/client-isolation-sla-and-runtime-profiles.md)

## Capability wizard, manifest & prospectus (discovery/audit tooling)

The machine-generated view over this whole taxonomy: a **capability manifest** (every archetype × venue × instrument ×
source × risk edge, typed gaps, orphan/dead-end report), a **prospectus generator** (per-archetype investor-style doc,
two-sided-audited against the hand-written `archetypes/` docs above), an **interactive scenario stepper** (drive the
real engine with synthetic inputs, watch triggers/kill-switches), and the **wizard UI** (`/wizard`). SSOT:
[capability-wizard.md](capability-wizard.md) · question bank:
[capability-wizard-question-bank.md](capability-wizard-question-bank.md) · plan of record:
[`plans/active/capability_wizard_and_manifest_2026_06_11.md`](../../../plans/active/capability_wizard_and_manifest_2026_06_11.md).
