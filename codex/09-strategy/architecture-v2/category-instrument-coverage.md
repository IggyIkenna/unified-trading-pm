---
doc_type: codex-ssot
title: Category × Instrument Coverage Matrix (SSOT)
summary:
  The SSOT coverage matrix — for every v2 archetype each (category, instrument_type) cell is declared
  SUPPORTED/PARTIAL/BLOCKED/NA with representative venues, signal variant, gap reason, lock_state, and fully-spelled
  slot_label examples; also the dated-future rolling-continuous representative-future roll spec.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, features-service, strategy-service, unified-trading-system-ui]
scope: [engineer, admin]
tags: [strategy, catalogue, cefi, defi, tradfi, execution, data-quality]

  [
    /codex/09-strategy/architecture-v2/block-list.md,
    /codex/09-strategy/architecture-v2/restriction-policy.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/strategy-registry-v2.md,
  ]
created: 2026-04-20
authoritative_for: [architecture-v2 archetype coverage-status matrix (SUPPORTED/PARTIAL/BLOCKED/NA per cell)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/MIGRATION.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-dated.md,
    /codex/09-strategy/architecture-v2/archetypes/event-driven.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-continuous.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-event-settled.md,
    /codex/09-strategy/architecture-v2/archetypes/stat-arb-cross-sectional.md,
    /codex/09-strategy/architecture-v2/archetypes/stat-arb-pairs-fixed.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Category × Instrument Coverage Matrix (SSOT)

> **Status:** Canonical as of 2026-04-19. Supersedes the ad-hoc "Supported scenarios" / "Supported venues + instrument
> types" sections in individual archetype docs. Those per-archetype docs link back here and keep only the archetype's
> rows from the table below.
>
> **Scope:** For every one of the 57 v2 strategy archetypes (per UAC
> `unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype` SSOT; 57 as of 2026-05-18 V-1 — was 53 at doc
> creation, 55 per 2026-05-12 audit, 57 per taxonomy V-1), every `(category, instrument_type)` cell is declared
> SUPPORTED / PARTIAL / BLOCKED / N/A with representative venues, signal variant, gap reason, and fully-spelled
> representative `slot_label` examples.
>
> **Matrix-completeness banner (2026-05-08).** This doc was authored at the 2026-04-19 18-archetype baseline. The tables
> below currently cover the May-23 live + immediate-backtest archetype subset. The Phase 9 expansions (4 MEV + 1
> cross-domain event arb + 5 new MARKET*MAKING*_ + 3 DEFI*LP*_ + 17 expanded VOL*\* + 4 PORTFOLIO*\*) are catalogued in
> UAC; their full per-cell matrix rows are tracked under
> [`plans/archive/codex_refactor_2026_05_08.plan.md`](../../../plans/archive/codex_refactor_2026_05_08.plan.md) Phase
> A.4 + the per-archetype materialisation in Phase B.
>
> **Sources:** `strategy-service/strategy_service/engine/strategies/v2/`, UAC `registry/capability_declarations/`,
> [`02-venues/venue-registry-reference.md`](../../02-venues/venue-registry-reference.md),
> [`02-venues/unity-integration.md`](../../02-venues/unity-integration.md), individual
> [`architecture-v2/archetypes/*.md`](archetypes/).

---

## Purpose

The v2 architecture is intentionally factored so that **category is derived from the execution venue, not from the
strategy code**. The same `ARBITRAGE_PRICE_DISPERSION` engine runs against CeFi spot, DeFi spot, or Unity event-settled
markets — only the venue params differ. This document makes that combinatoric explicit so:

1. **Strategy authors** can see which `(archetype, category, instrument_type)` cells are live today and which are
   blocked by a missing venue, capability flag, or UAC declaration.
2. **UAC maintainers** can see which registry additions unblock which cells.
3. **UI / catalog** can render the matrix directly (via `lib/architecture-v2/coverage.ts` generated from this doc).
4. **Operators** can build a block list of cells that cannot launch today and track them to closure.

### Relationship to availability / lock state

This universe is a single combinatoric matrix. Some slots are `PUBLIC` (DIY-client visible), some are
`INVESTMENT_MANAGEMENT_RESERVED` (our funds), some are `CLIENT_EXCLUSIVE` (bespoke contract). Lock state is **metadata
on the slot**, not a code-path axis — same engines, same wires, different visibility and RBAC. Full principle + UI
surfaces: [`cross-cutting/strategy-availability-and-locking.md`](cross-cutting/strategy-availability-and-locking.md).

### Lock State (2026-04-20 snapshot)

Every cell in the coverage matrix below carries a `lock_state` metadata axis (orthogonal to `status`). Per the
2026-04-20 snapshot, only `STAT_ARB_PAIRS_FIXED × CEFI × spot|perp` cells are `PUBLIC`. All other cells default to
`INVESTMENT_MANAGEMENT_RESERVED`. See
[`cross-cutting/strategy-availability-and-locking.md`](cross-cutting/strategy-availability-and-locking.md) §Current Lock
State Snapshot for the full matrix + rationale.

IM_RESERVED cells currently running for own IM (live or with firm go-live date):

- `ML_DIRECTIONAL_CONTINUOUS × CEFI × spot` — Binance, Coinbase, Hyperliquid (BTC ML — Jun 2026 go-live, 10 IM clients)
- `ML_DIRECTIONAL_CONTINUOUS × CEFI × perp` — Binance-perp, Hyperliquid (BTC ML perp companion — Jun 2026 go-live)
- `ML_DIRECTIONAL_CONTINUOUS × TRADFI × dated_future` — CME (S&P futures — Sept 2026 go-live, CME co-invest)
- `VOL_TRADING_OPTIONS × TRADFI × option` — NSE (India options — Oct 2026 go-live, delta trading)
- `ML_DIRECTIONAL_EVENT_SETTLED × SPORTS × event_settled` — Betfair, Betradar (Sports ML — Jun 2026 go-live,
  capacity-bound)

Canonical source:
[`../../14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md`](../../14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md).

Features / data are **not** part of the category axis. A strategy's execution category is defined by where its
`StrategyInstruction` actions actually land; feature groups and ML models can draw from any category's data without
changing the strategy's execution category.

## Conventions

### Status legend

| Status      | Meaning                                                                                                                                                                                            |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SUPPORTED` | Archetype engine code exists, UAC declares the venue + instrument, execution-service has the adapter. Can launch.                                                                                  |
| `PARTIAL`   | Engine code exists and can emit correct instructions, but some declarative hook is missing (capability flag, policy registry entry, secondary venue data). Launchable with manual ops work-around. |
| `BLOCKED`   | At least one hard dependency missing: no supported venue, no adapter, no UAC enum value, or no data feed. Cannot launch until dependency lands.                                                    |
| `N/A`       | Combination doesn't make sense for this archetype (e.g., `YIELD_STAKING_SIMPLE × CeFi × spot` — CeFi has no native staking concept).                                                               |

### Instrument-type vocabulary

Eight types used as table rows. `perp` and `dated_future` are kept separate because they map to different venue
populations (perp = crypto-native CEX + DEX; dated = TradFi), even though the underlying strategy code path is unified.

| Instrument type | Covers                                                                                                                                                                                                                                                                                                                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `spot`          | Cash market — crypto spot pair, equity share, FX spot, physical commodity                                                                                                                                                                                                                                                                                                                   |
| `perp`          | Perpetual future (CEX + DEX perps)                                                                                                                                                                                                                                                                                                                                                          |
| `dated_future`  | Expiring future (TradFi index/commodity/FX, crypto dated future). By default traded via a **rolling continuous underlying** — the strategy subscribes to `{underlying}-dated-...` and the roll service auto-switches the live contract when the next expiry becomes more liquid. See [Dated-future rolls and representative futures](#dated-future-rolls-and-representative-futures) below. |
| `option`        | Call/put, vanilla or complex (single-venue multi-leg)                                                                                                                                                                                                                                                                                                                                       |
| `lending`       | Supplied balance on a lending protocol (a-token, c-token, debt token)                                                                                                                                                                                                                                                                                                                       |
| `staking`       | Staked native asset (LST: stETH, rETH, JitoSOL, mSOL)                                                                                                                                                                                                                                                                                                                                       |
| `lp`            | AMM liquidity pool position (Uniswap V3 range, Curve, Balancer)                                                                                                                                                                                                                                                                                                                             |
| `event_settled` | Binary outcome market (sports odds, prediction market)                                                                                                                                                                                                                                                                                                                                      |

### Categories (4)

| Category              | Execution venues                                                                                                                                               |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CeFi`                | Binance, OKX, Bybit, Hyperliquid (hybrid), Deribit                                                                                                             |
| `DeFi`                | 7 chains × (Uniswap V2/V3, Balancer, Curve, SushiSwap, Aave V3, Compound V3, Euler, Morpho, Kamino, Lido, Rocket Pool, Jito, Marinade, Drift, Hyperliquid DEX) |
| `TradFi`              | IBKR (NYSE/NASDAQ/LSE + FX + options), CME (ES/NQ/CL/GC/6E/6B), ICE (Brent, gas oil, softs)                                                                    |
| `Sports & Prediction` | Unity (META_BROKER: 10 child books), Betfair direct, Smarkets direct, Matchbook direct, Polymarket, Kalshi (execution-future)                                  |

Prediction is folded into `Sports & Prediction` because both settle event-driven and share the same archetype code
paths; they are only distinguished by venue.

### Slot label grammar (SSOT:

[`../../06-coding-standards/strategy-identity-versioning.md`](../../06-coding-standards/strategy-identity-versioning.md))

```
{ARCHETYPE_ID}@{venue_scope}-{instrument_scope}[-{timeframe}]-{share_class}[-v{N}]-{env}
```

- `venue_scope` — single venue (`binance`, `hyperliquid`), venue pair (`binance-bybit`), chain + dex
  (`uniswap-ethereum`, `multi-dex-arbitrum`), or meta-broker (`unity`, `ibkr`, `cme`).
- `instrument_scope` — base asset + quote / product code (`btc-usdt`, `eth-perp-usdc`, `es-dec25-usd`, `epl-1x2`,
  `sol-lst`, `aave-usdc`).
- `timeframe` — optional, for strategies with explicit cadence (`5m`, `1h`, `daily`, `live`).
- `share_class` — terminal settlement currency (`usdt`, `usdc`, `usd`, `gbp`, `eur`, `eth`, `btc`, `sol`).
- `vN` — optional slot version suffix for material dependency changes (model family swap, venue swap).
- `env` — `prod`, `uat`, `paper`, `shadow`.

All examples below use `prod`. Launch sequence for every strategy: `shadow` → `uat` → `paper` → `prod`.

### Dated-future rolls and representative futures

Most strategies that touch `dated_future` instruments (ML directional on CME ES, stat-arb on calendar spreads, basis
trades on Deribit BTC-dated) trade the **continuous underlying**, not a specific expiry contract. The strategy rolls
from ESZ5 to ESH6 automatically once ESH6 becomes the more liquid contract — it does not hold ESZ5 to expiry. This is a
cross-cutting capability; archetypes do not re-implement it.

#### Continuous-underlying concept

An **underlying** (pre-existing concept in the system) is the abstract representation of a tradeable instrument
independent of any specific expiry:

```
BTC-USD-DERIBIT-DATED          # rolling crypto dated future
ETH-USD-DERIBIT-DATED
ES-USD-CME                     # E-mini S&P
NQ-USD-CME                     # E-mini Nasdaq
CL-USD-CME                     # WTI crude
BRENT-USD-ICE                  # Brent crude
GC-USD-CME                     # gold future
6E-USD-CME                     # EUR/USD FX future
```

At any point in time each underlying resolves to a **representative future** — the currently-most-liquid listed contract
for that underlying. Liquidity is measured **deterministically from features** (open interest, 24h volume, bid-ask
depth, declared in a named feature group with a stable contract).

#### End-to-end flow

```
1. features-service (delta-one feature group) continuously computes, per underlying:
     representative_future(underlying_id, as_of) = <specific_contract_id>
   based on declared liquidity measure. A change in that mapping is a state transition.

2. On state transition, representative-future-service emits:
     REPRESENTATIVE_FUTURE_CHANGED {
       underlying_id, prior_contract, new_contract, decision_features, at
     }
   over Pub/Sub (plus in-process notifier for co-located subscribers).

3. strategy-service subscribers on any slot using the `-dated-` scope for that
   underlying receive the event. Each affected strategy instance reacts by
   emitting a FUTURES_ROLL (an ATOMIC instruction variant):
     ATOMIC {
       leg 1: TRADE(prior_contract, target_units = 0)      # close leg
       leg 2: TRADE(new_contract, target_units = current)  # open in new contract
     }
   Preferred expression: a **calendar-spread combo ticker** when the venue
   lists one (e.g., CME `ES Z5-H6`, Deribit `BTC-26DEC25-27MAR26` combo). When
   no combo ticker exists, the instruction falls back to two-leg ATOMIC with
   synthetic-price guardrails (see step 4).

4. execution-service handles the combo:
   - **Combo listed at venue** → execute as single order against combo ticker;
     venue guarantees simultaneous fill.
   - **Combo not listed** → synthesize the combo: two-leg ATOMIC with a
     `synthetic_fair_value_ref` computed from the individual legs' mid prices,
     constrained by `max_roll_slippage_bps`. execution-service already computes
     synthetic pricing for multi-leg bundles as part of the matching-engine
     contract (batch=live); the roll case reuses that primitive.
   - If combo creation fails at venue (e.g., exchange rejects non-standard
     ratio) → escalate to two-leg LEADER_HEDGE with hard slippage guard.

5. Circuit breakers:
   - Roll slippage > `max_roll_slippage_bps` → **hard stop**: unwind prior
     contract only, do not open new leg; alert ops; emit
     `FUTURES_ROLL_FAILED`.
   - Representative-future-service feed stale > T seconds → **soft freeze**:
     no new opens, existing positions held; alert ops.
   - Consecutive roll failures > N across the underlying → **ops escalation**,
     strategy paused pending review.
```

#### Slot-label convention for dated futures

- **Default (rolling continuous):** `{archetype}@{venue}-{underlying}-dated-{timeframe}-{shareclass}-{env}`. The
  representative-future-service resolves `-dated-` to a specific contract at any instant. Use this for directional,
  rules, stat-arb, and basis strategies that don't care about specific expiry dates.
- **Explicit expiry (fixed):** `{archetype}@{venue}-{underlying}-fixed-{contract_code}-{timeframe}-{shareclass}-{env}`.
  Used when the strategy is intentionally expiry-aware (calendar arbitrage, end-of-quarter basis, event-driven bets
  anchored on a specific expiry week).

Absence of both `-dated-` and `-fixed-` in an existing short-form label (e.g. `cme-es-nq-zscore`) implies rolling
continuous semantics by default. New labels must be explicit.

#### Affected archetypes

Rolling-by-default (use `-dated-`):

- `ML_DIRECTIONAL_CONTINUOUS`
- `RULES_DIRECTIONAL_CONTINUOUS`
- `STAT_ARB_PAIRS_FIXED` (when pairing dated futures)
- `STAT_ARB_CROSS_SECTIONAL`
- `ARBITRAGE_PRICE_DISPERSION` (when a leg is a dated future — except explicit calendar arb which uses `-fixed-` on both
  legs)
- `EVENT_DRIVEN` (macro reactions on CME ES, ICE Brent, CME CL)
- `MARKET_MAKING_CONTINUOUS` (if ever quoting a future — always quotes the front, so effectively rolling)

Context-dependent:

- `CARRY_BASIS_DATED` — default instance rolls with the front (`-dated-`); explicit end-of-quarter / expiry-targeted
  instances use `-fixed-{contract}`.

Expiry-aware by design (not served by this mechanism):

- `VOL_TRADING_OPTIONS` — term structure matters; option rolls are handled internal to the archetype with a distinct
  roll model (weekly → monthly → quarterly serial rolls).

#### Registries this depends on

- `RepresentativeFutureRegistry` (UAC) — declares which underlyings exist, which feature group feeds liquidity
  measurement, and roll-trigger thresholds (e.g., "roll when next contract's 7-day rolling OI exceeds current's by
  10%"). **Gap:** not yet declared — see UAC Registry Implications #11.
- Per-venue `MultiLegOrderCapability` — whether the venue lists calendar-spread combo tickers and `max_legs` for
  on-the-fly combo creation. Partially declared; see UAC Registry Implications #7.
- `cross-cutting/futures-roll-and-combos.md` — canonical rolls + combo-creation spec (**to write** as part of the
  rollout of this architecture).

---

# Archetypes (18)

Ordered by family to match [`README.md`](README.md). Each archetype section contains: a one-line summary, the coverage
table, and a block of representative slot_labels grouped by `(category, instrument_type)` cell.

---

## Family 1: ML Directional

### 1. `ML_DIRECTIONAL_CONTINUOUS`

> Family: [ml-directional](families/ml-directional.md). Code:
> `strategy_service/engine/strategies/v2/ml_directional/continuous.py`.

Model-predicted directional probability vs market implied; sized by Kelly × confidence. Holds until signal flips or
time-box expires. Category-agnostic — venue choice determines category.

#### Coverage

| Category            | Instrument    | Status    | Representative venues                              | Signal variant      | Notes / Gap                                                                                                                            |
| ------------------- | ------------- | --------- | -------------------------------------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| CeFi                | spot          | SUPPORTED | Binance, OKX, Bybit, Hyperliquid                   | price               | —                                                                                                                                      |
| CeFi                | perp          | SUPPORTED | Binance, OKX, Bybit, Hyperliquid, Deribit          | price               | —                                                                                                                                      |
| CeFi                | dated_future  | PARTIAL   | Deribit (BTC / ETH dated)                          | price               | Deribit dated futures adapter path exists; settlement-aware reconciliation not batch-tested                                            |
| CeFi                | option        | PARTIAL   | Deribit, OKX options                               | delta-as-expression | Expression axis supports `atm_call` / `25d_call` / `synthetic`; execution_policy lacks multi-leg option router for delta-1 replication |
| CeFi                | lending       | N/A       | —                                                  | —                   | ML directional predicts price, not rates — see `YIELD_ROTATION_LENDING` for rate alpha                                                 |
| CeFi                | staking       | N/A       | —                                                  | —                   | No CeFi native staking — see `YIELD_STAKING_SIMPLE`                                                                                    |
| CeFi                | lp            | N/A       | —                                                  | —                   | No CeFi LP concept                                                                                                                     |
| CeFi                | event_settled | N/A       | —                                                  | —                   | See `ML_DIRECTIONAL_EVENT_SETTLED`                                                                                                     |
| DeFi                | spot          | PARTIAL   | Uniswap V3, Balancer (per-chain)                   | price               | Price feed reliability on thin DEX pairs needs UAC `pricing_fidelity: Literal["tick","snapshot"]` flag                                 |
| DeFi                | perp          | SUPPORTED | Hyperliquid (DEX side), Drift                      | price               | —                                                                                                                                      |
| DeFi                | dated_future  | BLOCKED   | —                                                  | —                   | No DeFi dated-future venue; Deribit is CeFi                                                                                            |
| DeFi                | option        | BLOCKED   | —                                                  | —                   | No supported DeFi options venue (Lyra / Dopex archived 2026-03)                                                                        |
| DeFi                | lending       | N/A       | —                                                  | —                   | See `YIELD_ROTATION_LENDING`                                                                                                           |
| DeFi                | staking       | N/A       | —                                                  | —                   | See `YIELD_STAKING_SIMPLE`                                                                                                             |
| DeFi                | lp            | N/A       | —                                                  | —                   | See `MARKET_MAKING_CONTINUOUS` (LP submode)                                                                                            |
| DeFi                | event_settled | N/A       | —                                                  | —                   | See `ML_DIRECTIONAL_EVENT_SETTLED`                                                                                                     |
| TradFi              | spot          | PARTIAL   | IBKR (NYSE/NASDAQ/LSE equities, FX spot)           | price               | IBKR FIX adapter symbol universe + order-type capability not fully declared in UAC                                                     |
| TradFi              | perp          | N/A       | —                                                  | —                   | TradFi has no perpetuals                                                                                                               |
| TradFi              | dated_future  | PARTIAL   | CME (ES, NQ, CL, GC, 6E, 6B), ICE (Brent, gas oil) | price               | CME/ICE routing declaration incomplete; tick-window metadata present but adapter batch-tested only for ES/NQ/CL                        |
| TradFi              | option        | PARTIAL   | CBOE via IBKR (equity + VIX options)               | delta-as-expression | CME options-on-futures (ES options, CL options) not declared in UAC                                                                    |
| TradFi              | lending       | N/A       | —                                                  | —                   | No applicable concept                                                                                                                  |
| TradFi              | staking       | N/A       | —                                                  | —                   | No applicable concept                                                                                                                  |
| TradFi              | lp            | N/A       | —                                                  | —                   | No applicable concept                                                                                                                  |
| TradFi              | event_settled | N/A       | —                                                  | —                   | See `ML_DIRECTIONAL_EVENT_SETTLED`                                                                                                     |
| Sports & Prediction | any           | N/A       | —                                                  | —                   | Event-settled markets → `ML_DIRECTIONAL_EVENT_SETTLED`                                                                                 |

#### Representative slot_labels

```
# CeFi spot (price-driven directional, HOLD_UNTIL_FLIP)
ML_DIRECTIONAL_CONTINUOUS@binance-btc-usdt-5m-usdt-prod
ML_DIRECTIONAL_CONTINUOUS@binance-eth-usdt-15m-usdt-prod
ML_DIRECTIONAL_CONTINUOUS@okx-sol-usdt-5m-usdt-prod
ML_DIRECTIONAL_CONTINUOUS@bybit-btc-usdt-1h-usdt-prod
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-usdt-5m-usdt-prod

# CeFi perp (most common)
ML_DIRECTIONAL_CONTINUOUS@binance-btc-perp-5m-usdt-prod
ML_DIRECTIONAL_CONTINUOUS@bybit-eth-perp-15m-usdt-prod
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-perp-5m-usdt-prod
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-eth-perp-5m-usdt-v2-prod           # v2 = model family swap
ML_DIRECTIONAL_CONTINUOUS@deribit-btc-perp-1h-usdt-prod

# CeFi dated_future — rolling continuous (roll service picks actual contract)
ML_DIRECTIONAL_CONTINUOUS@deribit-btc-dated-daily-usdt-prod
ML_DIRECTIONAL_CONTINUOUS@deribit-eth-dated-daily-usdt-prod
# Expiry-anchored variant (explicit contract — rare for this archetype)
ML_DIRECTIONAL_CONTINUOUS@deribit-btc-fixed-dec25-daily-usdt-prod

# CeFi option (delta-as-expression)
ML_DIRECTIONAL_CONTINUOUS@deribit-btc-atm_call-daily-usdt-prod
ML_DIRECTIONAL_CONTINUOUS@deribit-eth-25d_call-daily-usdt-prod
ML_DIRECTIONAL_CONTINUOUS@deribit-btc-synthetic-daily-usdt-prod

# DeFi spot (PARTIAL — pricing fidelity flag missing)
ML_DIRECTIONAL_CONTINUOUS@uniswap-ethereum-weth-usdc-5m-usdc-prod
ML_DIRECTIONAL_CONTINUOUS@uniswap-arbitrum-weth-usdc-15m-usdc-prod

# DeFi perp
ML_DIRECTIONAL_CONTINUOUS@drift-solana-sol-perp-5m-usdc-prod
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-dex-btc-perp-5m-usdc-prod

# TradFi spot equity
ML_DIRECTIONAL_CONTINUOUS@ibkr-spy-1m-usd-prod
ML_DIRECTIONAL_CONTINUOUS@ibkr-aapl-daily-usd-prod
ML_DIRECTIONAL_CONTINUOUS@ibkr-eurusd-fx-15m-usd-prod

# TradFi dated_future — rolling continuous
ML_DIRECTIONAL_CONTINUOUS@cme-es-dated-1m-usd-prod
ML_DIRECTIONAL_CONTINUOUS@cme-nq-dated-15m-usd-prod
ML_DIRECTIONAL_CONTINUOUS@cme-cl-dated-daily-usd-prod
ML_DIRECTIONAL_CONTINUOUS@ice-brent-dated-daily-usd-prod
ML_DIRECTIONAL_CONTINUOUS@cme-gc-dated-daily-usd-prod
ML_DIRECTIONAL_CONTINUOUS@cme-6e-dated-15m-usd-prod

# TradFi option
ML_DIRECTIONAL_CONTINUOUS@ibkr-cboe-spy-atm_call-daily-usd-prod
ML_DIRECTIONAL_CONTINUOUS@ibkr-cboe-qqq-25d_put-daily-usd-prod
```

---

### 2. `ML_DIRECTIONAL_EVENT_SETTLED`

> Family: [ml-directional](families/ml-directional.md). Code:
> `strategy_service/engine/strategies/v2/ml_directional/event_settled.py`.

ML probability vs implied on a binary outcome market (sports, prediction). Position held until settlement; `ONE_SHOT`
hold policy. Fractional-Kelly per outcome, banked outside the position.

#### Coverage

| Category            | Instrument    | Status    | Representative venues                                                                                                     | Signal variant | Notes / Gap                                                                  |
| ------------------- | ------------- | --------- | ------------------------------------------------------------------------------------------------------------------------- | -------------- | ---------------------------------------------------------------------------- |
| CeFi                | any           | N/A       | —                                                                                                                         | —              | Event-settled does not apply to CeFi price markets                           |
| DeFi                | any           | N/A       | —                                                                                                                         | —              | Event-settled does not apply to DeFi price markets                           |
| TradFi              | any           | N/A       | —                                                                                                                         | —              | Event-settled does not apply to TradFi price markets                         |
| Sports & Prediction | event_settled | SUPPORTED | Unity (all 10 child books — VX, Sharpbet, 3ET, Betdex, Matchbook, IBCbet, Betfair-via-Unity, Broker5 + 2 commission-free) | price (odds)   | Primary deployment target; Unity wallet = single pool                        |
| Sports & Prediction | event_settled | PARTIAL   | Betfair direct, Smarkets direct, Matchbook direct, Betdaq direct                                                          | price (odds)   | Lay-side bankroll-as-collateral semantics need explicit execution_policy_ref |
| Sports & Prediction | event_settled | SUPPORTED | Polymarket                                                                                                                | price (binary) | USDC settlement on Polygon chain                                             |
| Sports & Prediction | event_settled | BLOCKED   | Kalshi                                                                                                                    | price          | Execution-future; data + pricing feeds live but execution adapter pending    |

#### Representative slot_labels

```
# Unity (primary — sports event-settled)
ML_DIRECTIONAL_EVENT_SETTLED@unity-epl-1x2-usd-prod
ML_DIRECTIONAL_EVENT_SETTLED@unity-epl-over_under_2_5-usd-prod
ML_DIRECTIONAL_EVENT_SETTLED@unity-champions-league-1x2-usd-prod
ML_DIRECTIONAL_EVENT_SETTLED@unity-la-liga-1x2-usd-prod
ML_DIRECTIONAL_EVENT_SETTLED@unity-nba-moneyline-usd-prod
ML_DIRECTIONAL_EVENT_SETTLED@unity-nba-spread-usd-prod
ML_DIRECTIONAL_EVENT_SETTLED@unity-atp-match-winner-usd-prod
ML_DIRECTIONAL_EVENT_SETTLED@unity-wta-match-winner-usd-prod

# Unity live (in-play)
ML_DIRECTIONAL_EVENT_SETTLED@unity-epl-1x2-live-usd-prod
ML_DIRECTIONAL_EVENT_SETTLED@unity-nba-live-moneyline-usd-prod

# Betfair direct (lay-capable)
ML_DIRECTIONAL_EVENT_SETTLED@betfair-direct-epl-1x2-gbp-prod
ML_DIRECTIONAL_EVENT_SETTLED@betfair-direct-cricket-match-winner-gbp-prod

# Smarkets direct
ML_DIRECTIONAL_EVENT_SETTLED@smarkets-direct-epl-1x2-gbp-prod

# Polymarket (prediction — USDC)
ML_DIRECTIONAL_EVENT_SETTLED@polymarket-us-election-president-usdc-prod
ML_DIRECTIONAL_EVENT_SETTLED@polymarket-btc-eoy-price-band-usdc-prod
ML_DIRECTIONAL_EVENT_SETTLED@polymarket-superbowl-winner-usdc-prod

# First-half prediction (specialised cadence)
ML_DIRECTIONAL_EVENT_SETTLED@unity-epl-first-half-1x2-usd-prod
```

---

## Family 2: Rules Directional

### 3. `RULES_DIRECTIONAL_CONTINUOUS`

> Family: [rules-directional](families/rules-directional.md). Code:
> `strategy_service/engine/strategies/v2/rules_directional/continuous.py`.

Explicit if-else rules on features (TA indicators, thresholds, z-scores) producing fire / no-fire signals. No ML model
dependency. Used where interpretability outranks predictive power (regulatory, research sandbox, fast iteration).

#### Coverage

| Category            | Instrument   | Status    | Representative venues            | Signal variant           | Notes / Gap                                                                                    |
| ------------------- | ------------ | --------- | -------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------- |
| CeFi                | spot         | SUPPORTED | Binance, OKX, Bybit, Hyperliquid | TA rule / z-score        | —                                                                                              |
| CeFi                | perp         | SUPPORTED | Binance, OKX, Bybit, Hyperliquid | TA rule / funding regime | —                                                                                              |
| CeFi                | dated_future | PARTIAL   | Deribit (BTC / ETH dated)        | TA rule                  | Settlement-aware rule harness not batch-tested                                                 |
| CeFi                | option       | BLOCKED   | —                                | —                        | Directional options via rules are non-standard; use `VOL_TRADING_OPTIONS` for vol-metric rules |
| DeFi                | spot         | PARTIAL   | Uniswap V3 (on-chain TA signals) | TA rule                  | Same pricing-fidelity concern as ML_DIRECTIONAL_CONTINUOUS                                     |
| DeFi                | perp         | PARTIAL   | Drift, Hyperliquid DEX           | TA rule / funding regime | No codex instance examples; capability declaration minor                                       |
| DeFi                | dated_future | BLOCKED   | —                                | —                        | No DeFi dated future                                                                           |
| DeFi                | option       | BLOCKED   | —                                | —                        | No supported DeFi options venue                                                                |
| TradFi              | spot         | PARTIAL   | IBKR equities, FX                | TA rule                  | IBKR FIX adapter declaration gap same as ML                                                    |
| TradFi              | dated_future | PARTIAL   | CME (ES/NQ/CL), ICE (Brent)      | TA rule                  | Same as ML                                                                                     |
| TradFi              | option       | BLOCKED   | —                                | —                        | See CeFi note                                                                                  |
| Sports & Prediction | any          | N/A       | —                                | —                        | Event-settled → `RULES_DIRECTIONAL_EVENT_SETTLED`                                              |

Lending / staking / lp / event_settled rows are uniformly N/A for this archetype — rate alpha and LP alpha belong to
carry/yield and market-making archetypes respectively.

#### Representative slot_labels

```
# CeFi spot (TA rules)
RULES_DIRECTIONAL_CONTINUOUS@binance-btc-usdt-15m-macd-usdt-prod
RULES_DIRECTIONAL_CONTINUOUS@binance-eth-usdt-1h-bollinger-usdt-prod
RULES_DIRECTIONAL_CONTINUOUS@hyperliquid-sol-usdt-5m-rsi-usdt-prod

# CeFi perp (TA + funding regime)
RULES_DIRECTIONAL_CONTINUOUS@binance-btc-perp-15m-ta-funding-usdt-prod
RULES_DIRECTIONAL_CONTINUOUS@bybit-eth-perp-1h-trend-funding-usdt-prod
RULES_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-perp-5m-vwap-usdt-prod

# DeFi perp
RULES_DIRECTIONAL_CONTINUOUS@drift-solana-sol-perp-15m-ta-usdc-prod

# TradFi equity
RULES_DIRECTIONAL_CONTINUOUS@ibkr-spy-daily-donchian-usd-prod
RULES_DIRECTIONAL_CONTINUOUS@ibkr-qqq-15m-breakout-usd-prod

# TradFi future — rolling continuous
RULES_DIRECTIONAL_CONTINUOUS@cme-es-dated-1m-ta-usd-prod
RULES_DIRECTIONAL_CONTINUOUS@cme-cl-dated-daily-trend-usd-prod
RULES_DIRECTIONAL_CONTINUOUS@cme-nq-dated-15m-breakout-usd-prod
RULES_DIRECTIONAL_CONTINUOUS@ice-brent-dated-daily-trend-usd-prod
```

---

### 4. `RULES_DIRECTIONAL_EVENT_SETTLED`

> Family: [rules-directional](families/rules-directional.md). Code:
> `strategy_service/engine/strategies/v2/rules_directional/event_settled.py`.

Hard-coded if-else rules on sports / prediction features (e.g., "back home team if xG differential > 1.2 AND rest_days
differential > 2"). No model; interpretable signal for research + regulatory audit. Sanity-check alongside ML.

#### Coverage

| Category             | Instrument    | Status  | Representative venues                  | Signal variant        | Notes / Gap                                                                                       |
| -------------------- | ------------- | ------- | -------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------- |
| CeFi / DeFi / TradFi | any           | N/A     | —                                      | —                     | Event-settled only                                                                                |
| Sports & Prediction  | event_settled | PARTIAL | Unity, Betfair direct, Smarkets direct | threshold-rule / odds | Engine code complete; codex doc missing (archetype file stub only); no example instances declared |
| Sports & Prediction  | event_settled | PARTIAL | Polymarket                             | threshold-rule        | Same — doc + examples gap                                                                         |
| Sports & Prediction  | event_settled | BLOCKED | Kalshi                                 | —                     | Execution adapter pending                                                                         |

This archetype is the "paper trail" complement to `ML_DIRECTIONAL_EVENT_SETTLED` — same venues, explicit rules instead
of learned model.

#### Representative slot_labels

```
# Unity (rules — Poisson / xG / rest-days / home-form thresholds)
RULES_DIRECTIONAL_EVENT_SETTLED@unity-epl-xg-diff-usd-prod
RULES_DIRECTIONAL_EVENT_SETTLED@unity-epl-home-form-rule-usd-prod
RULES_DIRECTIONAL_EVENT_SETTLED@unity-la-liga-elo-threshold-usd-prod
RULES_DIRECTIONAL_EVENT_SETTLED@unity-nba-rest-days-rule-usd-prod

# Betfair direct
RULES_DIRECTIONAL_EVENT_SETTLED@betfair-direct-epl-xg-diff-gbp-prod

# Polymarket rule-based (e.g., price-band anchor)
RULES_DIRECTIONAL_EVENT_SETTLED@polymarket-btc-price-band-rule-usdc-prod
```

---

### 19. `TSMOM_BTC_CTA`

> Family: [rules-directional](families/rules-directional.md). Code:
> `strategy_service/engine/strategies/v2/rules_directional/tsmom_btc_cta.py`.

BTC-level time-series-momentum / trend-following (CTA) leg — a single directional perp leg (long-or-short) sized by the
mean SIGN of trailing returns × inverse-vol scaling. A rules-directional family member: no ML model, fully
interpretable. The research engine proved it a true diversifier (positive in both the 2023 +1.4 and the 2026 −29%
selloff +2.3; corr to BTC buy-and-hold +0.00 / −0.85). Scope is intentionally BTC-only (the universe is the single
most-liquid major), CeFi perp primary leg + spot secondary expression.

#### Coverage

| Category            | Instrument | Status    | Representative venues                     | Signal variant | Notes / Gap                                                            |
| ------------------- | ---------- | --------- | ----------------------------------------- | -------------- | ---------------------------------------------------------------------- |
| CeFi                | perp       | SUPPORTED | Binance, OKX, Bybit, Hyperliquid, Deribit | price (trend)  | Primary directional leg — long-or-short, inverse-vol sized             |
| CeFi                | spot       | SUPPORTED | Binance, OKX, Bybit, Hyperliquid          | price (trend)  | Spot expression of the BTC trend leg (long-only when spot-constrained) |
| DeFi / TradFi       | any        | N/A       | —                                         | —              | BTC-only CeFi archetype by design                                      |
| Sports & Prediction | any        | N/A       | —                                         | —              | Not event-settled                                                      |

Lending / staking / lp / option / dated_future rows are uniformly N/A — this is a single-leg directional perp/spot trend
follower, not a carry, yield, or vol archetype.

#### Representative slot_labels

```
# CeFi perp (TSMOM trend leg — long-or-short)
TSMOM_BTC_CTA@binance-btc-perp-1d-tsmom-usdt-prod
TSMOM_BTC_CTA@hyperliquid-btc-perp-1d-tsmom-usdt-prod

# CeFi spot expression
TSMOM_BTC_CTA@binance-btc-usdt-1d-tsmom-usdt-prod
```

---

## Family 3: Carry & Yield

### 5. `CARRY_BASIS_DATED`

> Family: [carry-and-yield](families/carry-and-yield.md). Code:
> `strategy_service/engine/strategies/v2/carry_and_yield/basis_dated.py`.

Spot + dated-future paired position that locks in the annualised basis. Unwind at expiry (or roll). `LEADER_HEDGE`
execution: leader leg fills, hedge leg follows within a deadline; abort if adverse move before hedge fills.

#### Coverage

| Category            | Instrument          | Status    | Representative venues                                        | Signal variant     | Notes / Gap                                                                                         |
| ------------------- | ------------------- | --------- | ------------------------------------------------------------ | ------------------ | --------------------------------------------------------------------------------------------------- |
| CeFi                | spot + dated_future | SUPPORTED | Binance spot + Deribit dated, Coinbase + Deribit             | basis (annualised) | —                                                                                                   |
| CeFi                | spot + option       | PARTIAL   | Deribit spot synthetic via option parity                     | put-call parity    | Option-parity expression path exists but no worked instance                                         |
| DeFi                | spot + dated_future | BLOCKED   | —                                                            | —                  | No DeFi dated-future venue                                                                          |
| TradFi              | spot + dated_future | PARTIAL   | IBKR spot (equity ETF) + CME future, ICE Brent spot + future | basis              | IBKR ↔ CME cross-venue routing policy not declared; spot-commodity physical settlement out-of-scope |
| TradFi              | equity + ETF future | PARTIAL   | IBKR (SPY) + CME ES future                                   | index basis        | Dividend-adjusted basis calculation not in UAC canonical helpers                                    |
| Sports & Prediction | any                 | N/A       | —                                                            | —                  | No dated-future analogue                                                                            |

#### Representative slot_labels

```
# CeFi BTC / ETH basis — rolling continuous (default; trades the front as it rolls)
CARRY_BASIS_DATED@binance-deribit-btc-dated-usdt-prod
CARRY_BASIS_DATED@binance-deribit-eth-dated-usdt-prod
CARRY_BASIS_DATED@coinbase-deribit-btc-dated-usd-prod

# CeFi expiry-targeted basis (explicit contract — end-of-quarter arb)
CARRY_BASIS_DATED@binance-deribit-btc-fixed-dec25-usdt-prod
CARRY_BASIS_DATED@binance-deribit-eth-fixed-mar26-usdt-prod
CARRY_BASIS_DATED@coinbase-deribit-btc-fixed-jun26-usd-prod

# CeFi put-call parity synthetic (PARTIAL)
CARRY_BASIS_DATED@deribit-btc-parity-synthetic-usdt-prod

# TradFi index basis — rolling
CARRY_BASIS_DATED@ibkr-cme-spy-es-dated-usd-prod
CARRY_BASIS_DATED@ibkr-cme-qqq-nq-dated-usd-prod

# TradFi index basis — expiry-targeted
CARRY_BASIS_DATED@ibkr-cme-spy-es-fixed-dec25-usd-prod
CARRY_BASIS_DATED@ibkr-cme-qqq-nq-fixed-mar26-usd-prod

# TradFi commodity basis — rolling (Brent spot ETF + ICE future front)
CARRY_BASIS_DATED@ibkr-ice-brent-dated-usd-prod
CARRY_BASIS_DATED@ibkr-cme-gold-etf-gc-dated-usd-prod
CARRY_BASIS_DATED@ibkr-ice-brent-fixed-feb26-usd-prod
```

---

### 6. `CARRY_BASIS_PERP`

> Family: [carry-and-yield](families/carry-and-yield.md). Code:
> `strategy_service/engine/strategies/v2/carry_and_yield/basis_perp.py`.

Spot + perp delta-neutral pair that captures funding rate (positive-funding → short perp + long spot; negative-funding →
reverse). Held continuously; exits when funding sign flips or annualised funding drops below threshold.

#### Coverage

| Category                | Instrument                 | Status    | Representative venues                                                                                          | Signal variant               | Notes / Gap                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ----------------------- | -------------------------- | --------- | -------------------------------------------------------------------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CeFi                    | spot + perp (single venue) | SUPPORTED | Binance (cross-margin netted), OKX, Bybit, Hyperliquid, Deribit                                                | funding-rate                 | Cross-margin netting pre-flight gates spec'd in R&E Layer 3                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| CeFi                    | spot + perp (cross-venue)  | SUPPORTED | Binance spot + Bybit perp, OKX spot + Hyperliquid perp                                                         | funding-rate                 | LEADER_HEDGE mode; two wallets                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| DeFi                    | spot + perp (same chain)   | SUPPORTED | Uniswap ETH + Hyperliquid DEX perp                                                                             | funding-rate                 | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| DeFi                    | LST + perp                 | SUPPORTED | Lido stETH + Hyperliquid DEX ETH-perp                                                                          | funding-rate + staking yield | Note: effectively becomes `CARRY_STAKED_BASIS` (redirect there if staking is primary)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| DeFi (DEX-native L2/L1) | spot + perp                | PARTIAL   | Uniswap spot + Lighter zkSync perp, Uniswap spot + Pacifica Solana perp, Uniswap spot + Extended Starknet perp | funding-rate                 | Three DEX perp venues onboarded 2026-05-07 (UAC + MTDS): LIGHTER-ZKSYNC (170 perps incl. crypto + FX/stocks/commodities), PACIFICA-SOLANA (~50 Hyperliquid-clone perps), EXTENDED-STARKNET (~10 majors). Historical OHLCV bars only — per-trade history NOT available (REST capped at last ~100 trades, no on-chain replay). Funding rates emit per-venue but funding-rate forward-poll handler not yet wired for these venues; backfill hold pending forward-poll. Volume vs CeFi: thin → DEX funding often diverges +/- 30-50% APR vs Binance/Bybit, opening cross-venue funding-spread trades. |
| TradFi                  | any                        | N/A       | —                                                                                                              | —                            | TradFi has no perpetuals                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Sports & Prediction     | any                        | N/A       | —                                                                                                              | —                            | No perp analogue                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |

#### Representative slot_labels

```
# CeFi single-venue netted basis (most capital-efficient)
CARRY_BASIS_PERP@binance-btc-usdt-prod
CARRY_BASIS_PERP@binance-eth-usdt-prod
CARRY_BASIS_PERP@bybit-btc-usdt-prod
CARRY_BASIS_PERP@hyperliquid-btc-usdt-prod
CARRY_BASIS_PERP@deribit-btc-usdt-prod

# CeFi cross-venue (spot on one, perp on another)
CARRY_BASIS_PERP@binance-bybit-btc-usdt-prod
CARRY_BASIS_PERP@okx-hyperliquid-eth-usdt-prod

# DeFi same-chain
CARRY_BASIS_PERP@uniswap-hyperliquid-eth-usdt-prod
CARRY_BASIS_PERP@uniswap-drift-sol-perp-solana-usdc-prod

# LST variant (staking yield + funding)
CARRY_BASIS_PERP@lido-hyperliquid-steth-usdt-prod

# DEX-native L2/L1 perp (added 2026-05-07 with the Lighter/Pacifica/Extended onboarding)
CARRY_BASIS_PERP@uniswap-lighter-zksync-eth-usdc-prod
CARRY_BASIS_PERP@uniswap-pacifica-solana-sol-usdc-prod
CARRY_BASIS_PERP@uniswap-extended-starknet-eth-usdc-prod
# Cross-DEX funding-spread (DEX-DEX `ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion` sub-cell;
# canonicalised 2026-05-07 from legacy `leveraged_funding_arb` per slot 8 strategy audit ST-7)
CARRY_BASIS_PERP@hyperliquid-pacifica-btc-usdc-prod
CARRY_BASIS_PERP@hyperliquid-lighter-eth-usdc-prod
```

---

### 7. `CARRY_STAKED_BASIS`

> Family: [carry-and-yield](families/carry-and-yield.md). Code:
> `strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py`.

**Two-leg** DeFi-native (no borrow leg since 2026-05-04 engine rewrite): stake native asset → receive LST → deposit LST
as perp cross-margin → short perp to stay delta-neutral. Net yield = staking APY + funding APY. The old 3-leg
STAKE+LEND+BORROW path was deleted — see archetype doc § "Not in this archetype" for detail.

#### Coverage (2026-05-20 — reflects post-Stream A venues with confirmed LST cross-margin)

| Category            | Instrument     | Status    | Representative venues                              | Signal variant            | Notes / Gap                                                                       |
| ------------------- | -------------- | --------- | -------------------------------------------------- | ------------------------- | --------------------------------------------------------------------------------- |
| CeFi                | any            | N/A       | —                                                  | —                         | No CeFi native staking                                                            |
| DeFi (Ethereum)     | staking + perp | SUPPORTED | Lido stETH → DERIBIT ETH-perp (7.5% haircut, X:PM) | staking APY + funding APY | USDC margin; stETH deposited to Deribit X:Portfolio margin as cross-collateral    |
| DeFi (Ethereum)     | staking + perp | SUPPORTED | Lido stETH → BYBIT UTA ETH-perp (10% haircut)      | staking APY + funding APY | USDT margin; stETH deposited to Bybit Unified Trading Account as cross-collateral |
| DeFi (Solana)       | staking + perp | SUPPORTED | Jito JitoSOL → DRIFT SOL-perp (10% haircut)        | staking APY + funding APY | USDC margin; JitoSOL posted directly as Drift cross-margin                        |
| DeFi (Solana)       | staking + perp | SUPPORTED | Marinade mSOL → DRIFT SOL-perp (10% haircut)       | staking APY + funding APY | USDC margin; mSOL posted directly as Drift cross-margin                           |
| TradFi              | any            | N/A       | —                                                  | —                         | No applicable concept                                                             |
| Sports & Prediction | any            | N/A       | —                                                  | —                         | No applicable concept                                                             |

#### Active slot_labels (2026-05-20, from `catalog.py _build_carry_staked_basis`)

```
CARRY_STAKED_BASIS@jito-drift-f100-usdc-1h-usdc-v2-prod     # JitoSOL × DRIFT (Solana, USDC)
CARRY_STAKED_BASIS@marinade-drift-f100-usdc-1h-usdc-v2-prod # mSOL × DRIFT (Solana, USDC)
CARRY_STAKED_BASIS@lido-deribit-f100-usdc-1h-usdc-v2-prod   # stETH × DERIBIT (ETH, USDC)
CARRY_STAKED_BASIS@lido-bybit-f100-usdt-1h-usdt-v2-prod     # stETH × BYBIT UTA (ETH, USDT)
```

---

### 8. `CARRY_RECURSIVE_STAKED`

> Family: [carry-and-yield](families/carry-and-yield.md). Code:
> `strategy_service/engine/strategies/v2/carry_and_yield/recursive_staked.py`.

Recursive lending loop: supply LST (stETH), borrow stablecoin against it, swap back to LST, re-supply — repeat N times
to lever staking yield. Target LTV is a risk parameter; liquidation risk is the primary constraint.

#### Coverage

| Category            | Instrument                    | Status    | Representative venues                         | Signal variant                     | Notes / Gap                                                               |
| ------------------- | ----------------------------- | --------- | --------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------- |
| CeFi                | any                           | N/A       | —                                             | —                                  | No CeFi native staking                                                    |
| DeFi (Ethereum)     | staking + lending (recursive) | SUPPORTED | Lido stETH + Aave V3 (up to 6 loops, 75% LTV) | leveraged staking APY – borrow APY | Liquidation-cascade risk declared; per-protocol bonus schedule gap in UAC |
| DeFi (Ethereum)     | staking + lending (recursive) | SUPPORTED | Rocket Pool rETH + Aave V3                    | same                               | —                                                                         |
| DeFi (Ethereum)     | staking + lending (recursive) | PARTIAL   | Lido stETH + Compound V3, Euler, Morpho       | same                               | Alt lending protocols declared in UAC but not full recursive-loop tested  |
| DeFi (Solana)       | staking + lending (recursive) | SUPPORTED | Jito JitoSOL + Kamino                         | leveraged staking APY – borrow APY | —                                                                         |
| DeFi (Solana)       | staking + lending (recursive) | SUPPORTED | Marinade mSOL + Kamino                        | same                               | —                                                                         |
| TradFi              | any                           | N/A       | —                                             | —                                  | No applicable concept                                                     |
| Sports & Prediction | any                           | N/A       | —                                             | —                                  | No applicable concept                                                     |

#### Representative slot_labels

```
# Ethereum recursive stETH (Aave)
CARRY_RECURSIVE_STAKED@lido-aave-steth-ltv70-ethereum-prod
CARRY_RECURSIVE_STAKED@lido-aave-steth-ltv75-ethereum-prod
CARRY_RECURSIVE_STAKED@rocketpool-aave-reth-ltv70-ethereum-prod

# Ethereum alt protocols (PARTIAL — not batch-tested)
CARRY_RECURSIVE_STAKED@lido-compound-steth-ltv65-ethereum-prod
CARRY_RECURSIVE_STAKED@lido-morpho-steth-ltv70-ethereum-prod
CARRY_RECURSIVE_STAKED@lido-euler-steth-ltv70-ethereum-prod

# Solana recursive
CARRY_RECURSIVE_STAKED@jito-kamino-jitosol-ltv70-solana-prod
CARRY_RECURSIVE_STAKED@marinade-kamino-msol-ltv70-solana-prod
```

---

### 9. `YIELD_ROTATION_LENDING`

> Family: [carry-and-yield](families/carry-and-yield.md). Code:
> `strategy_service/engine/strategies/v2/carry_and_yield/rotation_lending.py`.

Rotate stablecoin / asset supply across lending venues (and chains) to chase the highest net lending rate. Emits `LEND`
(target supplied balance) and `BRIDGE` when cross-chain move is warranted by rate spread – bridge cost.

#### Coverage

| Category            | Instrument       | Status    | Representative venues                                                                                                                               | Signal variant                 | Notes / Gap                                                                                                                           |
| ------------------- | ---------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| CeFi                | lending          | BLOCKED   | —                                                                                                                                                   | —                              | CeFi lending products (Binance Earn, Bybit) have withdrawal lockups + counterparty risk; deliberately out-of-scope                    |
| DeFi (multi-chain)  | lending          | SUPPORTED | Aave V3 (Ethereum / Arbitrum / Optimism / Polygon / Base / Avalanche), Compound V3 (Ethereum), Euler (Ethereum), Morpho (Ethereum), Kamino (Solana) | lending-rate spread            | —                                                                                                                                     |
| DeFi                | LST yield        | PARTIAL   | Across Lido / Rocket Pool / Jito / Marinade                                                                                                         | staking-rate spread            | Cross-LST rotation not a "lending" operation per se — consider a separate archetype or fold into `YIELD_STAKING_SIMPLE` rotation mode |
| DeFi                | lending + bridge | SUPPORTED | Aave V3 across chains via Circle CCTP / LayerZero Stargate                                                                                          | rate spread net of bridge cost | Bridge cost + latency modeled in rotation decision                                                                                    |
| TradFi              | any              | N/A       | —                                                                                                                                                   | —                              | TradFi lending (Fed Funds, repo) out-of-scope                                                                                         |
| Sports & Prediction | any              | N/A       | —                                                                                                                                                   | —                              | No applicable concept                                                                                                                 |

#### Representative slot_labels

```
# Single-chain USDC rotation
YIELD_ROTATION_LENDING@aave-compound-morpho-usdc-ethereum-prod
YIELD_ROTATION_LENDING@aave-euler-usdc-ethereum-prod

# Multi-chain USDC rotation (primary deployment)
YIELD_ROTATION_LENDING@aave-multichain-usdc-prod
YIELD_ROTATION_LENDING@aave-ethereum-arbitrum-optimism-usdc-prod
YIELD_ROTATION_LENDING@aave-multichain-usdt-prod

# Solana lending
YIELD_ROTATION_LENDING@kamino-solana-usdc-prod

# WETH rotation (LST-adjacent)
YIELD_ROTATION_LENDING@aave-morpho-weth-ethereum-prod
```

---

### 10. `YIELD_STAKING_SIMPLE`

> Family: [carry-and-yield](families/carry-and-yield.md). Code:
> `strategy_service/engine/strategies/v2/carry_and_yield/staking_simple.py`.

Straightforward native-asset staking (no leverage, no hedge). Emits `STAKE` (target staked balance) and `UNSTAKE` on
client withdrawal or share-class rotation. Delta-exposed by design — stake ETH to earn ETH-denominated yield.

#### Coverage

| Category            | Instrument                   | Status    | Representative venues                                          | Signal variant | Notes / Gap                                           |
| ------------------- | ---------------------------- | --------- | -------------------------------------------------------------- | -------------- | ----------------------------------------------------- |
| CeFi                | any                          | N/A       | —                                                              | —              | No CeFi native staking                                |
| DeFi (Ethereum)     | staking                      | SUPPORTED | Lido (stETH), Rocket Pool (rETH), Ether.fi (eETH)              | staking APY    | Ether.fi capability declaration minor pending         |
| DeFi (Solana)       | staking                      | SUPPORTED | Jito (JitoSOL), Marinade (mSOL)                                | staking APY    | —                                                     |
| DeFi                | staking (multi-LST rotation) | PARTIAL   | Across stETH / rETH / eETH (Ethereum); JitoSOL / mSOL (Solana) | APY spread     | Rotation mode exists in code but no instance declared |
| TradFi              | any                          | N/A       | —                                                              | —              | No applicable concept                                 |
| Sports & Prediction | any                          | N/A       | —                                                              | —              | No applicable concept                                 |

#### Representative slot_labels

```
# Ethereum staking (ETH share class)
YIELD_STAKING_SIMPLE@lido-steth-ethereum-eth-prod
YIELD_STAKING_SIMPLE@rocketpool-reth-ethereum-eth-prod
YIELD_STAKING_SIMPLE@etherfi-eeth-ethereum-eth-prod

# Solana staking (SOL share class)
YIELD_STAKING_SIMPLE@jito-jitosol-solana-sol-prod
YIELD_STAKING_SIMPLE@marinade-msol-solana-sol-prod

# Multi-LST rotation (PARTIAL — no declared instance yet)
YIELD_STAKING_SIMPLE@multi-lst-ethereum-eth-prod
YIELD_STAKING_SIMPLE@multi-lst-solana-sol-prod
```

---

### 11. `CARRY_BASIS_DATED_INV`

> Family: [carry-and-yield](families/carry-and-yield.md). Added 2026-05-22.

Inverse dated-future carry: short spot + long dated future to capture negative basis (contango → negative carry). Mirror
of `CARRY_BASIS_DATED` for markets where futures trade at discount to spot. Same `LEADER_HEDGE` execution; leader leg is
the dated-future buy, spot short follows within deadline.

#### Coverage

| Category            | Instrument          | Status    | Representative venues                     | Signal variant        | Notes / Gap                                               |
| ------------------- | ------------------- | --------- | ----------------------------------------- | --------------------- | --------------------------------------------------------- |
| CeFi                | spot + dated_future | SUPPORTED | Deribit dated + Binance spot (short-spot) | basis (negative)      | Requires margin/short-selling permissions on spot venue   |
| DeFi                | spot + dated_future | BLOCKED   | —                                         | —                     | No DeFi dated-future venue; same gap as CARRY_BASIS_DATED |
| TradFi              | spot + dated_future | PARTIAL   | IBKR spot short + CME future long         | index basis (inverse) | Short-sale locate + margin cost reduce net carry          |
| Sports & Prediction | any                 | N/A       | —                                         | —                     | No dated-future analogue                                  |

#### Representative slot_labels

```
# CeFi inverted basis (BTC / ETH contango — short spot + long dated future)
CARRY_BASIS_DATED_INV@binance-deribit-btc-inv-dated-usdt-prod
CARRY_BASIS_DATED_INV@binance-deribit-eth-inv-dated-usdt-prod

# TradFi inverted index basis
CARRY_BASIS_DATED_INV@ibkr-cme-spy-inv-dated-usd-prod
```

---

### 12. `CARRY_BASIS_PERP_INV`

> Family: [carry-and-yield](families/carry-and-yield.md). Added 2026-05-22.

Inverse perp basis: long perp + short spot when funding is strongly negative (market is in backwardation — longs pay
less / receive funding). Mirror of `CARRY_BASIS_PERP`; activated when annualised funding drops below threshold
(typically −15% APR).

#### Coverage

| Category | Instrument                 | Status    | Representative venues                            | Signal variant          | Notes / Gap                                                                |
| -------- | -------------------------- | --------- | ------------------------------------------------ | ----------------------- | -------------------------------------------------------------------------- |
| CeFi     | spot + perp (single venue) | SUPPORTED | Binance, OKX, Bybit, Hyperliquid, Deribit        | funding-rate (negative) | Same margin infra as CARRY_BASIS_PERP; reversed direction flag             |
| CeFi     | spot + perp (cross-venue)  | SUPPORTED | Binance spot short + Bybit perp long             | funding-rate (negative) | LEADER_HEDGE; two wallets; locate cost on spot short must be modelled      |
| DeFi     | spot + perp (same chain)   | SUPPORTED | Uniswap ETH + Hyperliquid DEX perp (long)        | funding-rate (negative) | Gas cost for spot short on DEX must be modelled vs funding premium         |
| DeFi     | LST + perp                 | PARTIAL   | Lido stETH short + Hyperliquid DEX ETH-perp long | funding-rate (negative) | LST short requires borrow markets (AAVE/Morpho); borrowing cost eats carry |
| TradFi   | any                        | N/A       | —                                                | —                       | TradFi has no perpetuals                                                   |

#### Representative slot_labels

```
# CeFi inverse perp (single venue — negative funding regime)
CARRY_BASIS_PERP_INV@binance-btc-inv-perp-usdt-prod
CARRY_BASIS_PERP_INV@hyperliquid-eth-inv-perp-usdt-prod

# CeFi cross-venue inverse perp
CARRY_BASIS_PERP_INV@binance-bybit-btc-inv-cross-usdt-prod

# DeFi inverse perp (same chain)
CARRY_BASIS_PERP_INV@uniswap-hyperliquid-eth-inv-perp-ethereum-prod
```

---

### 13. `CARRY_STAKED_BASIS_DATED`

> Family: [carry-and-yield](families/carry-and-yield.md). Added 2026-05-22.

Staked-asset + dated-future combo: hold LST for staking yield AND short the dated future to capture basis convergence.
Earns staking APR + (spot − dated-future) basis simultaneously. Unwind at expiry or when staking + basis together fall
below threshold.

#### Coverage

| Category | Instrument          | Status    | Representative venues                         | Signal variant        | Notes / Gap                                                               |
| -------- | ------------------- | --------- | --------------------------------------------- | --------------------- | ------------------------------------------------------------------------- |
| DeFi     | LST + dated_future  | SUPPORTED | Lido stETH + Deribit ETH dated (CeFi short)   | staking yield + basis | DeFi LST long + CeFi dated short; hybrid DeFi+CeFi execution path         |
| DeFi     | LST + dated_future  | PARTIAL   | RocketPool rETH + CME ETH future (IBKR route) | staking yield + basis | CME crypto future routing via IBKR not fully declared in execution_policy |
| CeFi     | spot + dated_future | N/A       | —                                             | —                     | CeFi spot doesn't earn staking yield; use CARRY_BASIS_DATED instead       |
| TradFi   | any                 | N/A       | —                                             | —                     | No LST equivalent in TradFi                                               |

#### Representative slot_labels

```
# DeFi LST + CeFi dated (hybrid)
CARRY_STAKED_BASIS_DATED@lido-deribit-eth-staked-dated-prod
CARRY_STAKED_BASIS_DATED@rocketpool-deribit-eth-staked-dated-prod
CARRY_STAKED_BASIS_DATED@coinbase-cbeth-deribit-eth-staked-dated-prod

# Solana LST + CME/perpetual hedge
CARRY_STAKED_BASIS_DATED@jito-jitosol-deribit-sol-staked-dated-prod
```

---

### 14. `CARRY_RECURSIVE_BORROW_LENDING_ONLY`

> Family: [carry-and-yield](families/carry-and-yield.md). Added 2026-05-22.

Pure recursive borrow/lend loop WITHOUT the perp hedge. Borrow an asset at protocol rate A, lend at rate B on a
different protocol (or supply tier), capturing the rate differential. No spot or perp leg. Lower gas + execution risk vs
`CARRY_RECURSIVE_STAKED` but exposed to rate-spread compression.

#### Coverage

| Category | Instrument                 | Status    | Representative venues                                         | Signal variant    | Notes / Gap                                                                 |
| -------- | -------------------------- | --------- | ------------------------------------------------------------- | ----------------- | --------------------------------------------------------------------------- |
| DeFi     | lending pool (borrow+lend) | SUPPORTED | Aave V3 borrow → Compound supply; Morpho borrow → Aave supply | rate differential | Rate spread must exceed gas + protocol fees; liquidation risk on borrow leg |
| DeFi     | lending pool (stablecoin)  | SUPPORTED | USDC Aave V3 borrow → Morpho USDC supply                      | rate differential | Stable pair eliminates FX risk; tightest spreads                            |
| DeFi     | lending pool (volatile)    | PARTIAL   | ETH Euler V2 borrow → Aave V3 ETH supply                      | rate differential | Collateral price drop can trigger liquidation; LTV ratio must be modelled   |
| CeFi     | any                        | N/A       | —                                                             | —                 | CeFi lending loops exist but are margin products; not DeFi-native           |
| TradFi   | any                        | N/A       | —                                                             | —                 | Repo/reverse-repo analogue exists; out-of-scope for DeFi archetype          |

#### Representative slot_labels

```
# Stablecoin borrow/lend differential
CARRY_RECURSIVE_BORROW_LENDING_ONLY@aave-compound-usdc-lend-ethereum-prod
CARRY_RECURSIVE_BORROW_LENDING_ONLY@aave-morpho-usdc-lend-ethereum-prod
CARRY_RECURSIVE_BORROW_LENDING_ONLY@aave-morpho-usdt-lend-ethereum-prod

# ETH volatile borrow/lend
CARRY_RECURSIVE_BORROW_LENDING_ONLY@euler-aave-eth-lend-ethereum-prod
CARRY_RECURSIVE_BORROW_LENDING_ONLY@morpho-compound-eth-lend-ethereum-prod
```

---

## Family 4: Arbitrage / Structural

### 11. `ARBITRAGE_PRICE_DISPERSION`

> Family: [arbitrage-structural](families/arbitrage-structural.md). Code:
> `strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion.py`. Settlement: ATOMIC (preferred) or
> LEADER_HEDGE.

Detects price dispersion between venues on the same (or equivalent) instrument and locks in the spread via paired
execution. Covers price, funding-rate, IV, and odds dispersion depending on cell.

#### Coverage

| Category                | Instrument     | Status    | Representative venues                                                                                                                  | Signal variant                      | Notes / Gap                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ----------------------- | -------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CeFi                    | spot           | SUPPORTED | Binance ↔ Bybit, Binance ↔ OKX, cross-CEX stables                                                                                      | price                               | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| CeFi                    | perp           | PARTIAL   | Binance, OKX, Bybit, Hyperliquid, Deribit (price + funding-rate dispersion)                                                            | price + funding-rate                | UAC lacks `funding_arb` flag distinct from price-arb                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| CeFi                    | option         | PARTIAL   | Deribit ↔ OKX options                                                                                                                  | IV dispersion                       | UAC `vol_arb` not a separate capability; execution_policy lacks multi-leg vol-arb algo                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| DeFi                    | spot           | SUPPORTED | Uniswap V3 ↔ Balancer ↔ Curve (per chain), Sushi                                                                                       | price (cross-DEX)                   | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| DeFi                    | perp           | SUPPORTED | Hyperliquid ↔ Drift                                                                                                                    | price + funding-rate                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| DeFi (DEX-native L2/L1) | perp           | PARTIAL   | Lighter zkSync ↔ Pacifica Solana ↔ Extended Starknet ↔ Hyperliquid ↔ Aster                                                             | price + funding-rate                | Three perp DEXes onboarded 2026-05-07 (LIGHTER-ZKSYNC, PACIFICA-SOLANA, EXTENDED-STARKNET). Thin DEX-side liquidity → price/funding dispersion vs CeFi often >30bps; biggest opportunity: cross-DEX funding-spread (e.g. PACIFICA BTC funding +50% APR vs HYPERLIQUID +8%). Per-trade tick history NOT available — only ohlcv_1m via /candles + /kline. Forward-poll for live funding rates pending.                                                                                                                                                                                                                                                                                                                                                                |
| DeFi                    | lp             | PARTIAL   | Uniswap V3 single-chain flash-loan arb                                                                                                 | MEV-aware price dispersion          | Flash-loan receiver contract per-chain registry missing from UAC; deployed on testnet only on some chains                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| DeFi                    | option         | BLOCKED   | —                                                                                                                                      | —                                   | No supported DeFi options venue                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| TradFi                  | spot           | PARTIAL   | IBKR smart-router (NYSE ↔ NASDAQ ↔ ARCA for dual-listed), IBKR FX ↔ CME FX fut                                                         | price                               | Most TradFi intra-exchange arb subsumed by IBKR routing; explicit arb instances sparse                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| TradFi                  | dated_future   | PARTIAL   | CME calendar spreads, ICE Brent ↔ CME WTI                                                                                              | price (calendar / cross-product)    | Cross-product routing policy not declared in UAC                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| TradFi                  | option         | PARTIAL   | CBOE via IBKR + same-surface no-arb (butterfly / calendar / parity)                                                                    | IV dispersion / surface             | CME options-on-futures + cross-listed equity options arb not declared                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Sports & Prediction     | event_settled  | SUPPORTED | Unity 10 child books (single-wallet arb), Betfair direct ↔ Smarkets direct, Unity ↔ Betfair direct                                     | price (odds dispersion)             | Unity single-wallet makes this near-atomic                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Sports & Prediction     | event_settled  | SUPPORTED | Polymarket ↔ Unity / Betfair for correlated markets                                                                                    | price (cross-category arb)          | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| TradFi ↔ Prediction     | event_contract | PARTIAL   | CME ECES/ECNQ/ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E/ECBTC ↔ Polymarket BTC_UP_DOWN_DAILY / SPX_UP_DOWN_DAILY / etc. canonical_question_groups | price (cross-asset_group basis arb) | NEW per `cme_polymarket_arb_2026_05_08` plan: 9 CME event-contract roots semantically equivalent to Polymarket binary outcomes; basis exploitable when the venues' implied probabilities diverge >50bps annualised. Phase 1 (UAC `InstrumentType.EVENT_CONTRACT` + Databento BAG classifier) shipped 2026-05-08. Phase 2 cross-link (`linked_canonical_question_group`) blocked on `predictions_master` Phase 5 (6 of 9 canonical groups still need backfill: RUT/DJIA/GOLD/CRUDE/NATGAS/EUR up-down dailies). Phases 3–5 (MTDS shard atom + per-cluster expiry + strategy archetype `cme_polymarket_event_arb` + execution-service CME ClearPort connector) follow Phase 2. **Out of May-23 critical path** — option value of being live, not the deadline itself. |

Not applicable: lending (no arb concept for a supplied balance — `YIELD_ROTATION_LENDING` captures rate spread), staking
(no arb — `CARRY_STAKED_BASIS`).

#### Slot labels (active catalog + illustrative; 2026-05-20)

```
# CeFi spot (active catalog slots from _build_arbitrage_price_dispersion)
ARBITRAGE_PRICE_DISPERSION@binance-okx-btc-1m-usdt-v2-prod
ARBITRAGE_PRICE_DISPERSION@binance-bybit-eth-1m-usdt-v2-prod
ARBITRAGE_PRICE_DISPERSION@okx-hyperliquid-sol-1m-usdt-v2-prod

# CeFi perp (price; illustrative — not yet in catalog)
ARBITRAGE_PRICE_DISPERSION@binance-bybit-btc-perp-usdt-prod
ARBITRAGE_PRICE_DISPERSION@hyperliquid-binance-eth-perp-usdt-prod

# CeFi perp (funding-rate dispersion — bridge slots in archetype_slot_resolver.py; NOT in TARGET_UNIVERSE catalog)
# venue_universe = [bybit, deribit, binance, okx, hyperliquid, aster]; pair_selection_mode = dynamic-best-long-short.
ARBITRAGE_PRICE_DISPERSION@bybit-deribit-binance-okx-hyperliquid-aster-funding-rate-disp-btc-usdt-v5-prod
ARBITRAGE_PRICE_DISPERSION@bybit-deribit-binance-okx-hyperliquid-aster-funding-rate-disp-eth-usdt-v5-prod

# DEX-native L2/L1 perp dispersion (added 2026-05-07; thin DEX liquidity → wide spreads vs CeFi)
ARBITRAGE_PRICE_DISPERSION@hyperliquid-lighter-btc-perp-usdc-prod
ARBITRAGE_PRICE_DISPERSION@hyperliquid-pacifica-btc-perp-usdc-prod
ARBITRAGE_PRICE_DISPERSION@hyperliquid-extended-eth-perp-usdc-prod
# Cross-DEX funding-rate dispersion (the high-edge cell — funding diverges most between thin DEXes)
ARBITRAGE_PRICE_DISPERSION@multi-dex-btc-funding-usdc-prod
ARBITRAGE_PRICE_DISPERSION@multi-dex-eth-funding-usdc-prod
ARBITRAGE_PRICE_DISPERSION@multi-dex-sol-funding-usdc-prod

# CeFi option (IV dispersion)
ARBITRAGE_PRICE_DISPERSION@deribit-okx-btc-vol-usdt-prod
ARBITRAGE_PRICE_DISPERSION@deribit-okx-eth-vol-usdt-prod
ARBITRAGE_PRICE_DISPERSION@deribit-btc-surface-noarb-usdt-prod

# DeFi spot (cross-DEX per chain)
ARBITRAGE_PRICE_DISPERSION@multi-dex-eth-usdc-ethereum-prod
ARBITRAGE_PRICE_DISPERSION@multi-dex-weth-usdc-arbitrum-prod
ARBITRAGE_PRICE_DISPERSION@uniswap-balancer-eth-usdc-optimism-prod
ARBITRAGE_PRICE_DISPERSION@uniswap-sushi-weth-usdc-base-prod

# DeFi perp
ARBITRAGE_PRICE_DISPERSION@hyperliquid-drift-sol-perp-usdc-prod

# DeFi LP (flash-loan)
ARBITRAGE_PRICE_DISPERSION@uniswap-flashloan-eth-usdc-ethereum-prod
ARBITRAGE_PRICE_DISPERSION@uniswap-flashloan-weth-usdc-arbitrum-prod

# TradFi dated_future — cross-product ratio on rolling fronts (-dated- on both legs)
ARBITRAGE_PRICE_DISPERSION@cme-es-nq-dated-ratio-usd-prod
ARBITRAGE_PRICE_DISPERSION@ice-brent-cme-wti-dated-usd-prod
# TradFi dated_future — explicit calendar arbitrage (specific expiries locked on both legs)
ARBITRAGE_PRICE_DISPERSION@cme-es-calendar-fixed-dec25-mar26-usd-prod
ARBITRAGE_PRICE_DISPERSION@cme-cl-calendar-fixed-jan26-apr26-usd-prod

# TradFi option (same-surface no-arb)
ARBITRAGE_PRICE_DISPERSION@cboe-spy-surface-noarb-usd-prod
ARBITRAGE_PRICE_DISPERSION@cboe-qqq-surface-noarb-usd-prod

# Sports event_settled (Unity cross-book)
ARBITRAGE_PRICE_DISPERSION@unity-epl-1x2-usd-prod
ARBITRAGE_PRICE_DISPERSION@unity-nba-moneyline-usd-prod
ARBITRAGE_PRICE_DISPERSION@unity-champions-league-1x2-usd-prod
ARBITRAGE_PRICE_DISPERSION@unity-atp-ml-usd-prod
ARBITRAGE_PRICE_DISPERSION@unity-nfl-spread-usd-prod

# Sports event_settled (cross-exchange direct)
ARBITRAGE_PRICE_DISPERSION@betfair-smarkets-epl-1x2-gbp-prod
ARBITRAGE_PRICE_DISPERSION@betfair-matchbook-champions-league-gbp-prod

# Cross-category (Polymarket ↔ sports)
ARBITRAGE_PRICE_DISPERSION@polymarket-unity-elections-usdc-prod
ARBITRAGE_PRICE_DISPERSION@polymarket-betfair-sports-usdc-prod
ARBITRAGE_PRICE_DISPERSION@polymarket-unity-nba-champion-usdc-prod

# Cross-asset_group (CME event_contract ↔ Polymarket canonical_question_group)
# NEW per cme_polymarket_arb_2026_05_08 plan; archetype = cme_polymarket_event_arb (Phase 5).
# Currently PARTIAL — only ECES/ECBTC have Polymarket-side canonical groups (SPX_UP_DOWN_DAILY,
# BTC_UP_DOWN_DAILY); ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E blocked on predictions_master Phase 5.
ARBITRAGE_PRICE_DISPERSION@cme-polymarket-spx-up-down-daily-usd-prod
ARBITRAGE_PRICE_DISPERSION@cme-polymarket-btc-up-down-daily-usd-prod
```

---

### 12. `LIQUIDATION_CAPTURE`

> Family: [arbitrage-structural](families/arbitrage-structural.md). Code:
> `strategy_service/engine/strategies/v2/arbitrage_structural/liquidation_capture.py`.

Snipe liquidation bonuses on lending protocols when borrowers fall below liquidation threshold. Multi-leg ATOMIC
instruction: flash-loan → repay debt → seize collateral + bonus → unwind via swap → repay flash loan. Pure mechanical
edge when profitable-after-gas.

#### Coverage

| Category            | Instrument | Status    | Representative venues                                 | Signal variant              | Notes / Gap                                                                                                                                                                              |
| ------------------- | ---------- | --------- | ----------------------------------------------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CeFi                | any        | PARTIAL   | Hyperliquid (liquidation discovery API)               | liquidation-bonus (limited) | Hyperliquid has liquidation feed but CEX liquidations settle internally — not capturable in the classic flash-loan sense; edge is limited to bid-ladder placement near liquidation price |
| DeFi (Ethereum)     | lending    | SUPPORTED | Aave V3 liquidator (ETH, WBTC, USDC collateral pairs) | liquidation-bonus           | Flash-loan receiver contract deployed on Ethereum; per-protocol bonus schedule gap in UAC                                                                                                |
| DeFi (Ethereum)     | lending    | PARTIAL   | Compound V3, Euler, Morpho liquidators                | liquidation-bonus           | Deployments per-protocol not fully rolled out                                                                                                                                            |
| DeFi (L2)           | lending    | SUPPORTED | Aave V3 on Arbitrum / Optimism / Polygon / Base       | liquidation-bonus           | —                                                                                                                                                                                        |
| DeFi (Solana)       | lending    | SUPPORTED | Kamino liquidator                                     | liquidation-bonus           | Different mechanic than EVM flash-loans (Solana program-level)                                                                                                                           |
| TradFi              | any        | N/A       | —                                                     | —                           | No liquidator role in TradFi venues                                                                                                                                                      |
| Sports & Prediction | any        | N/A       | —                                                     | —                           | No applicable concept                                                                                                                                                                    |

#### Representative slot_labels

```
# Aave Ethereum liquidator (primary)
LIQUIDATION_CAPTURE@aave-ethereum-eth-usdc-prod
LIQUIDATION_CAPTURE@aave-ethereum-wbtc-usdc-prod
LIQUIDATION_CAPTURE@aave-ethereum-steth-usdc-prod

# Aave L2 liquidator
LIQUIDATION_CAPTURE@aave-arbitrum-eth-usdc-prod
LIQUIDATION_CAPTURE@aave-optimism-eth-usdc-prod
LIQUIDATION_CAPTURE@aave-polygon-matic-usdc-prod
LIQUIDATION_CAPTURE@aave-base-eth-usdc-prod

# Alt protocols (PARTIAL — deployments in flight)
LIQUIDATION_CAPTURE@compound-ethereum-eth-usdc-prod
LIQUIDATION_CAPTURE@euler-ethereum-eth-usdc-prod
LIQUIDATION_CAPTURE@morpho-ethereum-eth-usdc-prod

# Solana
LIQUIDATION_CAPTURE@kamino-solana-sol-usdc-prod


# CeFi near-liquidation bid-laddering (PARTIAL)
LIQUIDATION_CAPTURE@hyperliquid-btc-perp-bidladder-usdt-prod
```

---

## Family 5: Market Making

### 13. `MARKET_MAKING_CONTINUOUS`

> Family: [market-making](families/market-making.md). Code:
> `strategy_service/engine/strategies/v2/market_making/continuous.py`.

Two-sided quoting (or LP provision) on continuously-priced markets. Three sub-modes: `CLOB` (central limit order book),
`ACTIVE_LP` (Uniswap V3 concentrated liquidity, actively managed range), `PASSIVE_LP` (Curve / Balancer / Uniswap V2
passive pool).

#### Coverage

| Category            | Instrument    | Status    | Representative venues                                                        | Signal variant                | Notes / Gap                                                                               |
| ------------------- | ------------- | --------- | ---------------------------------------------------------------------------- | ----------------------------- | ----------------------------------------------------------------------------------------- |
| CeFi                | spot          | SUPPORTED | Binance, OKX, Bybit, Hyperliquid                                             | bid-ask spread                | —                                                                                         |
| CeFi                | perp          | SUPPORTED | Binance, OKX, Bybit, Hyperliquid, Deribit                                    | bid-ask spread + funding skew | —                                                                                         |
| CeFi                | dated_future  | PARTIAL   | Deribit BTC / ETH dated                                                      | spread                        | Settlement-aware inventory model needed                                                   |
| CeFi                | option        | PARTIAL   | Deribit, OKX options                                                         | vol-based spread              | Deribit MM requires multi-leg order capability; UAC lacks `multi_leg_order_max_legs` flag |
| DeFi (per chain)    | lp            | SUPPORTED | Uniswap V3 / V4 (ACTIVE_LP), Orca (Solana), Raydium (Solana)                 | AMM fees (concentrated range) | —                                                                                         |
| DeFi (per chain)    | lp            | SUPPORTED | Curve, Balancer, Uniswap V2 (PASSIVE_LP)                                     | AMM fees (passive pool)       | IL dynamics need archetype sub-section                                                    |
| DeFi                | perp          | BLOCKED   | —                                                                            | —                             | DeFi perp MM not exposed as third-party role (protocol-level MM on Hyperliquid)           |
| DeFi                | option        | BLOCKED   | —                                                                            | —                             | No supported DeFi options venue                                                           |
| TradFi              | spot          | PARTIAL   | IBKR (market-maker status required, regulatory overhead)                     | bid-ask spread                | IBKR MM designation not declared; needs counterparty arrangement                          |
| TradFi              | dated_future  | PARTIAL   | CME market-maker role                                                        | spread                        | Formal MM designation out-of-scope for initial rollout                                    |
| TradFi              | option        | PARTIAL   | CBOE market-maker role                                                       | vol-based spread              | Formal MM designation out-of-scope                                                        |
| Sports & Prediction | event_settled | PARTIAL   | Betfair direct (lay + back continuous), Unity child books that allow quoting | odds-spread                   | Bankroll-as-collateral lay semantics need explicit execution_policy_ref                   |

#### Representative slot_labels

```
# CeFi spot MM
MARKET_MAKING_CONTINUOUS@binance-btc-usdt-mm-usdt-prod
MARKET_MAKING_CONTINUOUS@okx-eth-usdt-mm-usdt-prod
MARKET_MAKING_CONTINUOUS@bybit-sol-usdt-mm-usdt-prod

# CeFi perp MM
MARKET_MAKING_CONTINUOUS@binance-btc-perp-mm-usdt-prod
MARKET_MAKING_CONTINUOUS@hyperliquid-eth-perp-mm-usdt-prod
MARKET_MAKING_CONTINUOUS@deribit-btc-perp-mm-usdt-prod

# CeFi option MM (PARTIAL)
MARKET_MAKING_CONTINUOUS@deribit-btc-option-mm-usdt-prod
MARKET_MAKING_CONTINUOUS@deribit-eth-option-strip-mm-usdt-prod

# DeFi active LP (Uniswap V3)
MARKET_MAKING_CONTINUOUS@uniswap-v3-weth-usdc-ethereum-active-usdc-prod
MARKET_MAKING_CONTINUOUS@uniswap-v3-weth-usdc-arbitrum-active-usdc-prod
MARKET_MAKING_CONTINUOUS@uniswap-v3-wbtc-weth-ethereum-active-usdc-prod

# DeFi active LP (Solana)
MARKET_MAKING_CONTINUOUS@orca-sol-usdc-solana-active-usdc-prod
MARKET_MAKING_CONTINUOUS@raydium-sol-usdc-solana-active-usdc-prod

# DeFi passive LP
MARKET_MAKING_CONTINUOUS@curve-3pool-ethereum-passive-usdc-prod
MARKET_MAKING_CONTINUOUS@balancer-eth-usdc-ethereum-passive-usdc-prod
MARKET_MAKING_CONTINUOUS@uniswap-v2-weth-usdc-ethereum-passive-usdc-prod

# Sports MM (PARTIAL)
MARKET_MAKING_CONTINUOUS@betfair-direct-epl-1x2-mm-gbp-prod
MARKET_MAKING_CONTINUOUS@unity-epl-1x2-mm-usd-prod
```

---

### 14. `MARKET_MAKING_EVENT_SETTLED`

> Family: [market-making](families/market-making.md). Code:
> `strategy_service/engine/strategies/v2/market_making/event_settled.py`.

Back + lay quoting on event-settled exchanges. Inventory-skewed quotes with hard lay-liability bankroll caps.
Continuous-ish quoting during market lifetime, final position snapped at event start, settled at outcome.

#### Coverage

| Category             | Instrument    | Status    | Representative venues                            | Signal variant    | Notes / Gap                                                              |
| -------------------- | ------------- | --------- | ------------------------------------------------ | ----------------- | ------------------------------------------------------------------------ |
| CeFi / DeFi / TradFi | any           | N/A       | —                                                | —                 | Event-settled only                                                       |
| Sports & Prediction  | event_settled | SUPPORTED | Betfair direct (primary — lay-native)            | odds-spread + lay | —                                                                        |
| Sports & Prediction  | event_settled | PARTIAL   | Smarkets direct, Matchbook direct, Betdaq direct | odds-spread       | Lay semantics per-venue differ slightly — capability flag per-venue gap  |
| Sports & Prediction  | event_settled | PARTIAL   | Polymarket (CLOB side)                           | binary bid/ask    | Polymarket CLOB MM supported in theory but quoting UX differs (no "lay") |
| Sports & Prediction  | event_settled | BLOCKED   | Kalshi                                           | —                 | Execution adapter pending                                                |
| Sports & Prediction  | event_settled | BLOCKED   | Unity child books                                | —                 | Unity's Feed Connector is order-placement, not quoting                   |

#### Representative slot_labels

```
# Betfair MM (primary)
MARKET_MAKING_EVENT_SETTLED@betfair-direct-epl-1x2-mm-gbp-prod
MARKET_MAKING_EVENT_SETTLED@betfair-direct-epl-ou25-mm-gbp-prod
MARKET_MAKING_EVENT_SETTLED@betfair-direct-atp-match-winner-mm-gbp-prod
MARKET_MAKING_EVENT_SETTLED@betfair-direct-nba-moneyline-mm-usd-prod
MARKET_MAKING_EVENT_SETTLED@betfair-direct-epl-ht-ft-mm-gbp-prod

# Smarkets / Matchbook (PARTIAL)
MARKET_MAKING_EVENT_SETTLED@smarkets-direct-epl-1x2-mm-gbp-prod
MARKET_MAKING_EVENT_SETTLED@matchbook-direct-atp-match-winner-mm-gbp-prod

# Polymarket CLOB MM (PARTIAL)
MARKET_MAKING_EVENT_SETTLED@polymarket-us-election-mm-usdc-prod
MARKET_MAKING_EVENT_SETTLED@polymarket-sports-mm-usdc-prod
```

---

### 20. `MARKET_MAKING_PASSIVE_SPREAD`

> Family: [market-making](families/market-making.md). Code:
> `strategy_service/engine/strategies/v2/market_making/passive_spread.py`.

Passive symmetric-spread quoting around mid — the baseline CeFi MM style, no inventory-skew or ML adjustment.

#### Coverage

| Category | Instrument | Status  | Representative venues                                       | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | spot       | PARTIAL | binance, okx, bybit, hyperliquid, deribit, coinbase, kraken | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| CeFi     | perp       | PARTIAL | binance, okx, bybit, hyperliquid, deribit, coinbase, kraken | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
MARKET_MAKING_PASSIVE_SPREAD@binance-spot-1d-usdt-prod
MARKET_MAKING_PASSIVE_SPREAD@binance-perp-1d-usdt-prod
```

---

### 21. `MARKET_MAKING_INVENTORY_SKEW`

> Family: [market-making](families/market-making.md). Code:
> `strategy_service/engine/strategies/v2/market_making/inventory_skew.py`.

Inventory-aware quoting — skews bid/ask around mid based on current position to mean-revert inventory toward flat.

#### Coverage

| Category | Instrument | Status  | Representative venues                                       | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | spot       | PARTIAL | binance, okx, bybit, hyperliquid, deribit, coinbase, kraken | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| CeFi     | perp       | PARTIAL | binance, okx, bybit, hyperliquid, deribit, coinbase, kraken | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
MARKET_MAKING_INVENTORY_SKEW@binance-spot-1d-usdt-prod
MARKET_MAKING_INVENTORY_SKEW@binance-perp-1d-usdt-prod
```

---

### 22. `MARKET_MAKING_ML_LEAN`

> Family: [market-making](families/market-making.md). Code:
> `strategy_service/engine/strategies/v2/market_making/ml_lean.py`.

ML-informed quote placement — adjusts spread/skew using a short-horizon price-move forecast rather than pure inventory
rules.

#### Coverage

| Category | Instrument | Status  | Representative venues                                       | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | spot       | PARTIAL | binance, okx, bybit, hyperliquid, deribit, coinbase, kraken | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| CeFi     | perp       | PARTIAL | binance, okx, bybit, hyperliquid, deribit, coinbase, kraken | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
MARKET_MAKING_ML_LEAN@binance-spot-1d-usdt-prod
MARKET_MAKING_ML_LEAN@binance-perp-1d-usdt-prod
```

---

### 23. `MARKET_MAKING_QUEUE_MICROSTRUCTURE`

> Family: [market-making](families/market-making.md). Code:
> `strategy_service/engine/strategies/v2/market_making/queue_microstructure.py`.

Queue-position-aware quoting on CeFi order books — models queue priority/fill probability, not applicable to AMM venues.

#### Coverage

| Category | Instrument | Status  | Representative venues                                       | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | spot       | PARTIAL | binance, okx, bybit, hyperliquid, deribit, coinbase, kraken | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| CeFi     | perp       | PARTIAL | binance, okx, bybit, hyperliquid, deribit, coinbase, kraken | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
MARKET_MAKING_QUEUE_MICROSTRUCTURE@binance-spot-1d-usdt-prod
MARKET_MAKING_QUEUE_MICROSTRUCTURE@binance-perp-1d-usdt-prod
```

---

### 24. `MARKET_MAKING_PREDICTION`

> Family: [market-making](families/market-making.md). Code:
> `strategy_service/engine/strategies/v2/market_making/prediction.py`.

Two-sided quoting on prediction markets — binary-outcome mechanics, time-to-resolution decay, distinct from CeFi/DeFi
MM.

#### Coverage

| Category   | Instrument    | Status  | Representative venues | Notes / Gap                                                                                                  |
| ---------- | ------------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| Prediction | event_settled | PARTIAL | polymarket, unity     | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
MARKET_MAKING_PREDICTION@polymarket-event_settled-1d-usdt-prod
```

---

### 25. `DEFI_LP_CONCENTRATED`

> Family: [market-making](families/market-making.md). Code:
> `strategy_service/engine/strategies/v2/market_making/lp_concentrated.py`.

Concentrated-liquidity LP positioning (Uniswap V3-style) — active range management around current price.

#### Coverage

| Category | Instrument | Status  | Representative venues      | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | -------------------------- | ------------------------------------------------------------------------------------------------------------ |
| DeFi     | lp         | PARTIAL | uniswap_v3, pancakeswap_v3 | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
DEFI_LP_CONCENTRATED@uniswap_v3-lp-1d-usdt-prod
```

---

### 26. `DEFI_LP_POOL`

> Family: [market-making](families/market-making.md). Code:
> `strategy_service/engine/strategies/v2/market_making/lp_pool.py`.

Traditional full-range / weighted-pool LP positioning (Balancer/Curve/Maverick-style).

#### Coverage

| Category | Instrument | Status  | Representative venues     | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | ------------------------- | ------------------------------------------------------------------------------------------------------------ |
| DeFi     | lp         | PARTIAL | balancer, curve, maverick | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
DEFI_LP_POOL@balancer-lp-1d-usdt-prod
```

---

### 27. `DEFI_LP_VAULT`

> Family: [market-making](families/market-making.md). Code:
> `strategy_service/engine/strategies/v2/market_making/lp_vault.py`.

LP-vault-wrapper positioning (Gamma/Arrakis/Steer) — delegates active range management to a third-party vault strategy.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| DeFi     | lp         | PARTIAL | gamma, arrakis, steer | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
DEFI_LP_VAULT@gamma-lp-1d-usdt-prod
```

---

## Family 6: Event-Driven

### 15. `EVENT_DRIVEN`

> Family: [event-driven](families/event-driven.md). Code:
> `strategy_service/engine/strategies/v2/event_driven/event_driven.py`.

Scheduled external events (macro data release, earnings, token unlock, protocol hard-fork, governance vote) with
measurable surprise vs consensus. Emits `TRADE` (directional bet on surprise) and optionally `LEND` / `STAKE` (for yield
events).

#### Coverage

| Category            | Instrument    | Status  | Representative venues                        | Signal variant               | Notes / Gap                                                                                                                               |
| ------------------- | ------------- | ------- | -------------------------------------------- | ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| CeFi                | spot          | PARTIAL | Binance, OKX (macro-reactive BTC / ETH)      | event-surprise (macro)       | External event calendar (Bloomberg / TE) not declared in UAC                                                                              |
| CeFi                | perp          | PARTIAL | Binance, Hyperliquid, Bybit                  | event-surprise (macro)       | Same calendar gap                                                                                                                         |
| CeFi                | option        | PARTIAL | Deribit (pre-FOMC vol, event straddles)      | IV regime change             | Event-straddle expression policy not declared                                                                                             |
| DeFi                | spot          | PARTIAL | Uniswap (token unlock / airdrop reactive)    | event-surprise (tokenomics)  | Token unlock calendar source gap (TokenUnlocks.io etc.)                                                                                   |
| DeFi                | perp          | PARTIAL | Hyperliquid (governance-vote reactive)       | event-surprise               | —                                                                                                                                         |
| DeFi                | lending       | PARTIAL | Aave (rate-update governance votes)          | event-surprise (rate change) | Protocol-governance calendar gap                                                                                                          |
| DeFi                | staking       | PARTIAL | Lido (oracle update / slashing event)        | event-surprise               | Slashing feed integration incomplete                                                                                                      |
| TradFi              | spot          | PARTIAL | IBKR equities (earnings reactive)            | event-surprise (earnings)    | Earnings calendar source gap                                                                                                              |
| TradFi              | dated_future  | PARTIAL | CME ES (NFP, FOMC, CPI reactive), CL (OPEC)  | event-surprise (macro)       | Event-type → instrument mapping not declared in execution_policy                                                                          |
| TradFi              | option        | PARTIAL | CBOE (earnings-vol, VIX jumps)               | IV regime change             | Same as CeFi option                                                                                                                       |
| Sports & Prediction | event_settled | PARTIAL | Unity (lineup-release reactive, injury news) | event-surprise (news)        | News-feed integration + lineup timing model not declared in event-driven archetype; likely evolves into dedicated news-reactive archetype |
| Sports & Prediction | event_settled | PARTIAL | Polymarket (news-driven binary)              | event-surprise (news)        | Same                                                                                                                                      |

#### Representative slot_labels

```
# CeFi macro-reactive spot / perp
EVENT_DRIVEN@binance-btc-usdt-nfp-usdt-prod
EVENT_DRIVEN@binance-btc-perp-fomc-usdt-prod
EVENT_DRIVEN@hyperliquid-eth-perp-cpi-usdt-prod

# CeFi option event straddle
EVENT_DRIVEN@deribit-btc-option-fomc-straddle-usdt-prod
EVENT_DRIVEN@deribit-eth-option-merge-straddle-usdt-prod

# DeFi token-unlock reactive
EVENT_DRIVEN@uniswap-ethereum-arb-token-unlock-usdc-prod
EVENT_DRIVEN@uniswap-arbitrum-sui-token-unlock-usdc-prod

# DeFi governance
EVENT_DRIVEN@aave-ethereum-governance-rate-update-usdc-prod

# DeFi staking slashing
EVENT_DRIVEN@lido-ethereum-slashing-event-eth-prod

# TradFi earnings
EVENT_DRIVEN@ibkr-aapl-earnings-usd-prod
EVENT_DRIVEN@ibkr-msft-earnings-usd-prod
EVENT_DRIVEN@ibkr-nvda-earnings-usd-prod

# TradFi macro — rolling continuous on futures (cboe VIX is not a dated-future rolling case)
EVENT_DRIVEN@cme-es-dated-nfp-usd-prod
EVENT_DRIVEN@cme-es-dated-fomc-usd-prod
EVENT_DRIVEN@cme-cl-dated-opec-usd-prod
EVENT_DRIVEN@cboe-vix-cpi-usd-prod

# Sports news-reactive
EVENT_DRIVEN@unity-epl-lineup-release-usd-prod
EVENT_DRIVEN@unity-nba-injury-news-usd-prod

# Prediction news-reactive
EVENT_DRIVEN@polymarket-us-election-debate-usdc-prod
```

---

## Family 7: Vol Trading

### 16. `VOL_TRADING_OPTIONS`

> Family: [vol-trading](families/vol-trading.md). Code: `strategy_service/engine/strategies/v2/vol_trading/options.py`.

Trades vol metrics themselves: IV/RV divergence (short straddle when IV > RV), skew (risk-reversal), term-structure
(calendar spread), cross-asset vol (BTC vol vs ETH vol). Always multi-leg; ATOMIC execution required.

#### Coverage

| Category            | Instrument                                                          | Status    | Representative venues                                  | Signal variant                     | Notes / Gap                                                                                                    |
| ------------------- | ------------------------------------------------------------------- | --------- | ------------------------------------------------------ | ---------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| CeFi                | option                                                              | SUPPORTED | Deribit (BTC, ETH options — full surface), OKX options | IV/RV, skew, term, cross-asset vol | Full Deribit surface-model support; multi-leg ATOMIC supported                                                 |
| DeFi                | option                                                              | BLOCKED   | —                                                      | —                                  | No supported DeFi options venue (Lyra / Dopex archived)                                                        |
| TradFi              | option                                                              | PARTIAL   | CBOE via IBKR (equity options, VIX options)            | IV/RV, skew, term                  | CME options-on-futures (ES options, CL options) not declared in UAC                                            |
| Sports & Prediction | any                                                                 | N/A       | —                                                      | —                                  | No vol concept                                                                                                 |
| any                 | spot / perp / dated_future / lending / staking / lp / event_settled | N/A       | —                                                      | —                                  | By definition — `VOL_TRADING_OPTIONS` trades options exclusively; use `ML_DIRECTIONAL_*` for other instruments |

#### Representative slot_labels

```
# CeFi Deribit (primary — BTC / ETH vol book)
VOL_TRADING_OPTIONS@deribit-btc-vol-usdt-prod
VOL_TRADING_OPTIONS@deribit-eth-vol-usdt-prod
VOL_TRADING_OPTIONS@deribit-btc-skew-usdt-prod
VOL_TRADING_OPTIONS@deribit-btc-term-structure-usdt-prod
VOL_TRADING_OPTIONS@deribit-btc-eth-cross-vol-usdt-prod
VOL_TRADING_OPTIONS@deribit-btc-atm-straddle-usdt-prod
VOL_TRADING_OPTIONS@deribit-btc-rr25-usdt-prod

# CeFi OKX options (smaller book)
VOL_TRADING_OPTIONS@okx-btc-vol-usdt-prod
VOL_TRADING_OPTIONS@okx-eth-vol-usdt-prod

# TradFi CBOE via IBKR (PARTIAL)
VOL_TRADING_OPTIONS@ibkr-cboe-spy-vol-usd-prod
VOL_TRADING_OPTIONS@ibkr-cboe-spy-skew-usd-prod
VOL_TRADING_OPTIONS@ibkr-cboe-vix-vol-usd-prod
VOL_TRADING_OPTIONS@ibkr-cboe-qqq-term-structure-usd-prod
```

---

### 28. `VOL_ARB_RV_IV`

> Family: [vol-trading](families/vol-trading.md). Code:
> `strategy_service/engine/strategies/v2/vol_trading/arb_rv_iv.py`.

Trades realized-vs-implied volatility divergence: short vol structures when IV richly exceeds RV, long when IV is cheap
relative to realized moves.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| TradFi   | option     | PARTIAL | cboe, cme             | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_ARB_RV_IV@deribit-option-1d-usdt-prod
VOL_ARB_RV_IV@cboe-option-1d-usdt-prod
```

---

### 29. `VOL_SPREAD_STRUCTURES`

> Family: [vol-trading](families/vol-trading.md). Code:
> `strategy_service/engine/strategies/v2/vol_trading/spread_structures.py`.

Multi-leg option spread structures (verticals, calendars, diagonals) expressing a directional-vol view with defined
risk.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| TradFi   | option     | PARTIAL | cboe, cme             | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_SPREAD_STRUCTURES@deribit-option-1d-usdt-prod
VOL_SPREAD_STRUCTURES@cboe-option-1d-usdt-prod
```

---

### 30. `VOL_CARRY`

> Family: [vol-trading](families/vol-trading.md). Code: `strategy_service/engine/strategies/v2/vol_trading/carry.py`.

Systematically harvests the vol risk premium — short-dated short-vol positions collecting the IV-over-RV carry, sized to
survive tail moves.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_CARRY@deribit-option-1d-usdt-prod
```

---

### 31. `VOL_OVERLAY_COVERED_CALLS`

> Family: [vol-trading](families/vol-trading.md). Code:
> `strategy_service/engine/strategies/v2/vol_trading/overlay_covered_calls.py`.

Covered-call overlay on an existing spot/perp position — sells calls against holdings for premium income, caps upside.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| TradFi   | option     | PARTIAL | cboe, cme             | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_OVERLAY_COVERED_CALLS@deribit-option-1d-usdt-prod
VOL_OVERLAY_COVERED_CALLS@cboe-option-1d-usdt-prod
```

---

### 32. `VOL_OVERLAY_PROTECTIVE_PUT`

> Family: [vol-trading](families/vol-trading.md). Code:
> `strategy_service/engine/strategies/v2/vol_trading/overlay_protective_put.py`.

Protective-put overlay — buys downside protection against an existing position, insurance-style tail-risk hedge.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| TradFi   | option     | PARTIAL | cboe, cme             | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_OVERLAY_PROTECTIVE_PUT@deribit-option-1d-usdt-prod
VOL_OVERLAY_PROTECTIVE_PUT@cboe-option-1d-usdt-prod
```

---

### 33. `VOL_STRADDLE`

> Family: [vol-trading](families/vol-trading.md). Code: `strategy_service/engine/strategies/v2/vol_trading/straddle.py`.

Long/short straddle and strangle structures around an expected volatility event (earnings-style catalysts, macro
prints).

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| TradFi   | option     | PARTIAL | cboe, cme             | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_STRADDLE@deribit-option-1d-usdt-prod
VOL_STRADDLE@cboe-option-1d-usdt-prod
```

---

### 34. `VOL_SYNTHETIC_DELTA`

> Family: [vol-trading](families/vol-trading.md). Code:
> `strategy_service/engine/strategies/v2/vol_trading/synthetic_delta.py`.

Constructs synthetic directional exposure via options (risk reversals, synthetic longs/shorts) instead of spot/perp.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_SYNTHETIC_DELTA@deribit-option-1d-usdt-prod
```

---

### 35. `VOL_MARKET_MAKING`

> Family: [vol-trading](families/vol-trading.md). Code:
> `strategy_service/engine/strategies/v2/vol_trading/market_making.py`.

Two-sided options quoting — provides liquidity across the strike/tenor grid, manages delta/gamma/vega inventory.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| TradFi   | option     | PARTIAL | cboe, cme             | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_MARKET_MAKING@deribit-option-1d-usdt-prod
VOL_MARKET_MAKING@cboe-option-1d-usdt-prod
```

---

### 36. `VOL_ML_LEAN`

> Family: [vol-trading](families/vol-trading.md). Code: `strategy_service/engine/strategies/v2/vol_trading/ml_lean.py`.

ML-informed vol-signal generation feeding into the vol-trading execution layer (skew/term-structure/RV forecasts).

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_ML_LEAN@deribit-option-1d-usdt-prod
```

---

### 37. `VOL_0DTE_GAMMA_SCALPING`

> Family: [vol-trading](families/vol-trading.md). Code:
> `strategy_service/engine/strategies/v2/vol_trading/0dte_gamma_scalping.py`.

Same-day-expiry gamma scalping — delta-hedges a 0DTE options position intraday, harvesting realized-vs-theoretical gamma
P&L.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| TradFi   | option     | PARTIAL | cboe, cme             | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_0DTE_GAMMA_SCALPING@deribit-option-1d-usdt-prod
VOL_0DTE_GAMMA_SCALPING@cboe-option-1d-usdt-prod
```

---

### 38. `VOL_0DTE_PIN_RISK`

> Family: [vol-trading](families/vol-trading.md). Code:
> `strategy_service/engine/strategies/v2/vol_trading/0dte_pin_risk.py`.

Trades same-day-expiry pin-risk dynamics around high-open-interest strikes into the close.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| TradFi   | option     | PARTIAL | cboe, cme             | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_0DTE_PIN_RISK@deribit-option-1d-usdt-prod
VOL_0DTE_PIN_RISK@cboe-option-1d-usdt-prod
```

---

### 39. `VOL_TERM_STRUCTURE_ARB`

> Family: [vol-trading](families/vol-trading.md). Code:
> `strategy_service/engine/strategies/v2/vol_trading/term_structure_arb.py`.

Cross-tenor implied-vol term-structure arbitrage — trades the curve shape (contango/backwardation) rather than a
single-tenor level.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| TradFi   | option     | PARTIAL | cboe, cme             | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_TERM_STRUCTURE_ARB@deribit-option-1d-usdt-prod
VOL_TERM_STRUCTURE_ARB@cboe-option-1d-usdt-prod
```

---

### 40. `VOL_TERM_STRUCTURE_SLOPE`

> Family: [vol-trading](families/vol-trading.md). Code:
> `strategy_service/engine/strategies/v2/vol_trading/term_structure_slope.py`.

Trades the SLOPE of the vol term structure specifically (front vs back tenor spread), distinct from full-curve arb.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| TradFi   | option     | PARTIAL | cboe, cme             | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_TERM_STRUCTURE_SLOPE@deribit-option-1d-usdt-prod
VOL_TERM_STRUCTURE_SLOPE@cboe-option-1d-usdt-prod
```

---

### 41. `VOL_DISPERSION`

> Family: [vol-trading](families/vol-trading.md). Code:
> `strategy_service/engine/strategies/v2/vol_trading/dispersion.py`.

Index-vs-component vol dispersion — short index vol, long component vol (or vice versa) on correlation-breakdown views.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| TradFi   | option     | PARTIAL | cboe, cme             | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_DISPERSION@deribit-option-1d-usdt-prod
VOL_DISPERSION@cboe-option-1d-usdt-prod
```

---

### 42. `VOL_VARIANCE_SWAP`

> Family: [vol-trading](families/vol-trading.md). Code:
> `strategy_service/engine/strategies/v2/vol_trading/variance_swap.py`.

Direct (where listed) or option-strip-replicated (Carr-Madan) variance-swap exposure — pure realized-variance payoff.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| TradFi   | option     | PARTIAL | cboe, cme             | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_VARIANCE_SWAP@deribit-option-1d-usdt-prod
VOL_VARIANCE_SWAP@cboe-option-1d-usdt-prod
```

---

### 43. `VOL_LEAPS_CONVEXITY`

> Family: [vol-trading](families/vol-trading.md). Code:
> `strategy_service/engine/strategies/v2/vol_trading/leaps_convexity.py`.

Long-dated (6m+) convex payoff structures via LEAPS — cheap synthetic delta-1 exposure or rolling portfolio-insurance
ladders.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| TradFi   | option     | PARTIAL | cboe, cme             | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_LEAPS_CONVEXITY@deribit-option-1d-usdt-prod
VOL_LEAPS_CONVEXITY@cboe-option-1d-usdt-prod
```

---

### 44. `VOL_CROSS_ASSET_SPREAD`

> Family: [vol-trading](families/vol-trading.md). Code:
> `strategy_service/engine/strategies/v2/vol_trading/cross_asset_spread.py`.

Cross-asset vol relative value — trades vol BETWEEN assets (e.g. BTC vol vs ETH vol), distinct from single-underlying
dispersion.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| TradFi   | option     | PARTIAL | cboe, cme             | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_CROSS_ASSET_SPREAD@deribit-option-1d-usdt-prod
VOL_CROSS_ASSET_SPREAD@cboe-option-1d-usdt-prod
```

---

### 45. `VOL_RATIO_SPREAD`

> Family: [vol-trading](families/vol-trading.md). Code:
> `strategy_service/engine/strategies/v2/vol_trading/ratio_spread.py`.

Ratio-spread structures (1x2, 2x3, broken-wing flies) with signal-driven strike selection.

#### Coverage

| Category | Instrument | Status  | Representative venues | Notes / Gap                                                                                                  |
| -------- | ---------- | ------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi     | option     | PARTIAL | deribit, okx, bybit   | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |
| TradFi   | option     | PARTIAL | cboe, cme             | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

#### Representative slot_labels

```
# Illustrative naming-convention examples — no live/paper instance confirmed yet
VOL_RATIO_SPREAD@deribit-option-1d-usdt-prod
VOL_RATIO_SPREAD@cboe-option-1d-usdt-prod
```

---

## Family 8: Stat Arb / Pairs

### 17. `STAT_ARB_PAIRS_FIXED`

> Family: [stat-arb-pairs](families/stat-arb-pairs.md). Code:
> `strategy_service/engine/strategies/v2/stat_arb_pairs/pairs_fixed.py`.

Pre-declared cointegrated pair (e.g., BTC / ETH, GOOG / META). Z-score of spread, enter when z > threshold, exit on
mean-reversion or time-box. Two-leg ATOMIC or LEADER_HEDGE.

#### Coverage

| Category            | Instrument      | Status    | Representative venues                                        | Signal variant          | Notes / Gap                                                          |
| ------------------- | --------------- | --------- | ------------------------------------------------------------ | ----------------------- | -------------------------------------------------------------------- |
| CeFi                | spot            | SUPPORTED | Binance, OKX, Bybit (intra-exchange pairs)                   | z-score reversion       | —                                                                    |
| CeFi                | perp            | SUPPORTED | Binance, OKX, Bybit, Hyperliquid (intra-exchange perp pairs) | z-score reversion       | —                                                                    |
| CeFi                | mixed spot+perp | SUPPORTED | Binance spot-vs-perp pair                                    | z-score (basis anomaly) | Different shape from `CARRY_BASIS_PERP` — StatArb z-score, not carry |
| DeFi                | spot            | PARTIAL   | Uniswap V3 (per-chain WETH vs WBTC, ETH vs stETH)            | z-score reversion       | Price-feed liquidity concerns on thinner pairs                       |
| DeFi                | perp            | PARTIAL   | Hyperliquid, Drift (SOL/ETH, alt/BTC pairs)                  | z-score reversion       | —                                                                    |
| TradFi              | spot            | PARTIAL   | IBKR equities (sector pairs: AAPL/MSFT, XOM/CVX, JPM/BAC)    | z-score reversion       | Pair pre-declaration config path fine; no batch-tested instances     |
| TradFi              | dated_future    | PARTIAL   | CME calendar / cross-product (ES vs NQ, CL vs HO)            | z-score reversion       | —                                                                    |
| Sports & Prediction | any             | N/A       | —                                                            | —                       | No pair-trading concept                                              |

#### Representative slot_labels

```
# CeFi spot pairs
STAT_ARB_PAIRS_FIXED@binance-btc-eth-spot-usdt-prod
STAT_ARB_PAIRS_FIXED@binance-eth-sol-spot-usdt-prod

# CeFi perp pairs
STAT_ARB_PAIRS_FIXED@binance-btc-eth-perp-usdt-prod
STAT_ARB_PAIRS_FIXED@bybit-sol-eth-perp-usdt-prod
STAT_ARB_PAIRS_FIXED@hyperliquid-btc-eth-perp-usdt-prod

# Spot-vs-perp StatArb (not basis)
STAT_ARB_PAIRS_FIXED@binance-btc-spot-perp-zscore-usdt-prod

# DeFi
STAT_ARB_PAIRS_FIXED@uniswap-ethereum-eth-wbtc-usdc-prod
STAT_ARB_PAIRS_FIXED@hyperliquid-sol-eth-perp-usdc-prod

# TradFi equity pairs
STAT_ARB_PAIRS_FIXED@ibkr-goog-meta-daily-usd-prod
STAT_ARB_PAIRS_FIXED@ibkr-aapl-msft-1h-usd-prod
STAT_ARB_PAIRS_FIXED@ibkr-xom-cvx-daily-usd-prod
STAT_ARB_PAIRS_FIXED@ibkr-jpm-bac-daily-usd-prod

# TradFi future pairs — rolling continuous on both legs
STAT_ARB_PAIRS_FIXED@cme-es-nq-dated-zscore-usd-prod
STAT_ARB_PAIRS_FIXED@cme-cl-ho-dated-crack-usd-prod
STAT_ARB_PAIRS_FIXED@ice-brent-cme-wti-dated-usd-prod
STAT_ARB_PAIRS_FIXED@cme-gc-cl-dated-zscore-usd-prod
```

---

### 18. `STAT_ARB_CROSS_SECTIONAL`

> Family: [stat-arb-pairs](families/stat-arb-pairs.md). Code:
> `strategy_service/engine/strategies/v2/stat_arb_pairs/cross_sectional.py`.

Cross-sectional ranking across a basket (top decile long, bottom decile short, or quintile rotation). Rebalances at
cadence (daily, weekly). ATOMIC basket execution or sequential per leg.

#### Coverage

| Category            | Instrument   | Status  | Representative venues                                     | Signal variant                    | Notes / Gap                                                                      |
| ------------------- | ------------ | ------- | --------------------------------------------------------- | --------------------------------- | -------------------------------------------------------------------------------- |
| CeFi                | spot         | PARTIAL | Binance (alt-basket cross-section)                        | momentum / mean-reversion ranking | Basket execution via sequential TRADE; batch-order path not tested               |
| CeFi                | perp         | PARTIAL | Hyperliquid, Bybit (alt-basket)                           | momentum / MR ranking             | —                                                                                |
| DeFi                | spot         | BLOCKED | —                                                         | —                                 | Multi-token atomic basket trade requires router support + gas efficiency concern |
| DeFi                | perp         | PARTIAL | Hyperliquid DEX, Drift (alt-perp basket)                  | momentum ranking                  | —                                                                                |
| TradFi              | spot         | PARTIAL | IBKR (S&P 500 sector basket, market-cap-tercile rotation) | momentum / mean-reversion ranking | Batch-order capability not declared for IBKR; basket of 50–500 legs              |
| TradFi              | dated_future | BLOCKED | —                                                         | —                                 | Cross-sectional basket on CME requires multi-leg order capability; not declared  |
| Sports & Prediction | any          | N/A     | —                                                         | —                                 | No cross-section concept                                                         |

#### Representative slot_labels

```
# CeFi spot alt-basket
STAT_ARB_CROSS_SECTIONAL@binance-alt-basket-momentum-usdt-prod
STAT_ARB_CROSS_SECTIONAL@binance-alt-basket-mr-usdt-prod

# CeFi perp alt-basket
STAT_ARB_CROSS_SECTIONAL@hyperliquid-alt-perp-momentum-usdt-prod
STAT_ARB_CROSS_SECTIONAL@bybit-alt-perp-weekly-usdt-prod

# DeFi perp alt-basket
STAT_ARB_CROSS_SECTIONAL@hyperliquid-dex-alt-perp-momentum-usdc-prod
STAT_ARB_CROSS_SECTIONAL@drift-solana-alt-perp-momentum-usdc-prod

# TradFi sector / market-cap
STAT_ARB_CROSS_SECTIONAL@ibkr-sp500-momentum-usd-prod
STAT_ARB_CROSS_SECTIONAL@ibkr-sp500-sector-rotation-usd-prod
STAT_ARB_CROSS_SECTIONAL@ibkr-russell2000-mr-usd-prod
STAT_ARB_CROSS_SECTIONAL@ibkr-sector-tercile-momentum-usd-prod
```

---

## Family 9: Portfolio

> Cross-category — Portfolio archetypes allocate across other archetypes' sleeves rather than trading a single
> instrument directly, so `asset_group = CROSS_CATEGORY` and `instrument_type = sleeve_mix` (both added 2026-07-21
> alongside this family's Phase-9 manifest materialisation — the family enum itself shipped 2026-04-25 but never had
> capability-manifest cells until now).

### 46. `PORTFOLIO_MULTI_STRATEGY`

> Family: [portfolio](families/portfolio.md). Code: `strategy_service/engine/strategies/v2/portfolio/multi_strategy.py`.

Allocates capital across multiple underlying strategy sleeves at a fixed risk-tier mix — a meta-strategy over the
catalogue, not a single-instrument trader.

#### Coverage

| Category       | Instrument | Status  | Canonical configs                                     | Notes / Gap                                                                                                  |
| -------------- | ---------- | ------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Cross-category | sleeve_mix | PARTIAL | 3 — Conservative / Balanced / Aggressive sleeve mixes | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

---

### 47. `PORTFOLIO_RISK_PARITY`

> Family: [portfolio](families/portfolio.md). Code: `strategy_service/engine/strategies/v2/portfolio/risk_parity.py`.

Risk-parity allocation across sleeves — weights each sleeve by inverse volatility contribution rather than equal
notional.

#### Coverage

| Category       | Instrument | Status  | Canonical configs                    | Notes / Gap                                                                                                  |
| -------------- | ---------- | ------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| Cross-category | sleeve_mix | PARTIAL | 2 — Crypto-only / Multi-asset parity | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

---

### 48. `PORTFOLIO_FACTOR_ALLOCATION`

> Family: [portfolio](families/portfolio.md). Code:
> `strategy_service/engine/strategies/v2/portfolio/factor_allocation.py`.

Factor-tilted allocation across sleeves grouped by exposure factor (momentum, carry, value).

#### Coverage

| Category       | Instrument | Status  | Canonical configs                         | Notes / Gap                                                                                                  |
| -------------- | ---------- | ------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Cross-category | sleeve_mix | PARTIAL | 2 — Momentum+Carry / Momentum+Value+Carry | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

---

### 49. `PORTFOLIO_TACTICAL_OVERLAY`

> Family: [portfolio](families/portfolio.md). Code:
> `strategy_service/engine/strategies/v2/portfolio/tactical_overlay.py`.

Tactical overlay that shifts sleeve weights based on a regime signal, on top of a static base allocation.

#### Coverage

| Category       | Instrument | Status  | Canonical configs                              | Notes / Gap                                                                                                  |
| -------------- | ---------- | ------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Cross-category | sleeve_mix | PARTIAL | 2 — Regime-switch / Signal-weighted allocation | Capability-manifest cell only (2026-07-21 Phase-9 regen) — not yet confirmed by a live batch/paper instance. |

---

# Block List (cross-archetype summary)

The 21 `(archetype, category, instrument)` triples with hard blockers, grouped by blocking reason. Each entry links back
to the cell in the archetype sections above.

## BL-1: No supported DeFi options venue

Archetypes affected: `ML_DIRECTIONAL_CONTINUOUS`, `RULES_DIRECTIONAL_CONTINUOUS`, `ARBITRAGE_PRICE_DISPERSION`,
`MARKET_MAKING_CONTINUOUS`, `VOL_TRADING_OPTIONS`.

Lyra and Dopex were archived 2026-03. No replacement DeFi options venue is currently declared. Unblock by evaluating
Aevo, Premia, Hegic, or accepting DeFi options as out-of-scope.

- `(ML_DIRECTIONAL_CONTINUOUS, DeFi, option)`
- `(RULES_DIRECTIONAL_CONTINUOUS, DeFi, option)`
- `(ARBITRAGE_PRICE_DISPERSION, DeFi, option)`
- `(MARKET_MAKING_CONTINUOUS, DeFi, option)`
- `(VOL_TRADING_OPTIONS, DeFi, option)`

## BL-2: No DeFi dated-future venue

Archetypes affected: `ML_DIRECTIONAL_CONTINUOUS`, `CARRY_BASIS_DATED`.

Deribit is CeFi. No on-chain dated-future venue currently supported.

- `(ML_DIRECTIONAL_CONTINUOUS, DeFi, dated_future)`
- `(CARRY_BASIS_DATED, DeFi, spot + dated_future)`

## BL-3: CeFi lending out-of-scope

Archetypes affected: `YIELD_ROTATION_LENDING`.

Binance Earn / Bybit lending have withdrawal lockups + counterparty risk. Decision: excluded from our product.

- `(YIELD_ROTATION_LENDING, CeFi, lending)`

## BL-4: CeFi directional options via rules (non-standard)

Archetypes affected: `RULES_DIRECTIONAL_CONTINUOUS`.

Directional options via rules is a degenerate case — use `VOL_TRADING_OPTIONS` for vol-metric rules or
`ML_DIRECTIONAL_CONTINUOUS` with expression=`atm_call` for directional options.

- `(RULES_DIRECTIONAL_CONTINUOUS, CeFi, option)`
- `(RULES_DIRECTIONAL_CONTINUOUS, TradFi, option)`

## BL-5: Kalshi execution adapter pending

Archetypes affected: `ML_DIRECTIONAL_EVENT_SETTLED`, `RULES_DIRECTIONAL_EVENT_SETTLED`, `MARKET_MAKING_EVENT_SETTLED`.

Data + pricing live; execution adapter not built.

- `(ML_DIRECTIONAL_EVENT_SETTLED, Sports & Prediction, event_settled) via Kalshi`
- `(RULES_DIRECTIONAL_EVENT_SETTLED, Sports & Prediction, event_settled) via Kalshi`
- `(MARKET_MAKING_EVENT_SETTLED, Sports & Prediction, event_settled) via Kalshi`

## BL-6: Unity cannot quote (Feed Connector is place-only)

Archetypes affected: `MARKET_MAKING_EVENT_SETTLED`.

Unity's Java Feed Connector accepts PLACE_BET / CANCEL but does not expose a quoting API. Unity child books quote
internally; we cannot add our own bids/offers through Unity.

- `(MARKET_MAKING_EVENT_SETTLED, Sports & Prediction, event_settled) via Unity`

## BL-7: DeFi perp MM not exposed as third-party role

Archetypes affected: `MARKET_MAKING_CONTINUOUS`.

Hyperliquid has protocol-level MM incentives; no third-party-MM role comparable to CLOB MM.

- `(MARKET_MAKING_CONTINUOUS, DeFi, perp)`

## BL-8: DeFi cross-sectional basket (multi-leg gas efficiency)

Archetypes affected: `STAT_ARB_CROSS_SECTIONAL`.

Atomic multi-token basket trade on DeFi is gas-prohibitive on EVM; requires specialised router (1inch Pathfinder style)
not currently declared.

- `(STAT_ARB_CROSS_SECTIONAL, DeFi, spot)`

## BL-9: TradFi cross-sectional on futures basket

Archetypes affected: `STAT_ARB_CROSS_SECTIONAL`.

Multi-leg cross-sectional on CME futures basket requires batch-order capability not declared for CME adapter.

- `(STAT_ARB_CROSS_SECTIONAL, TradFi, dated_future)`

## BL-10: Dated-future auto-roll + combo creation not yet live

Archetypes affected: all archetypes with `-dated-` slots on `dated_future` cells — `ML_DIRECTIONAL_CONTINUOUS`,
`RULES_DIRECTIONAL_CONTINUOUS`, `STAT_ARB_PAIRS_FIXED`, `STAT_ARB_CROSS_SECTIONAL`,
`ARBITRAGE_PRICE_DISPERSION × dated_future`, `EVENT_DRIVEN × dated_future`, `CARRY_BASIS_DATED` default mode.

The end-to-end flow (features-service liquidity measure → representative-future-service state transition →
`REPRESENTATIVE_FUTURE_CHANGED` event → strategy-service roll emission → execution-service combo resolution with
synthetic-price guardrails) is spec'd in
[Dated-future rolls and representative futures](#dated-future-rolls-and-representative-futures) but not yet implemented.
Specific missing pieces:

- `RepresentativeFutureRegistry` in UAC (see UAC Registry Implications #11)
- `representative-future-service` (new service OR sub-module of features-service) — not yet scaffolded
- `REPRESENTATIVE_FUTURE_CHANGED` event schema in UAC events
- `FUTURES_ROLL` instruction variant in the polymorphic `StrategyInstruction` (or reuse of `ATOMIC`)
- execution-service combo auto-creation when venue doesn't list the calendar-spread ticker
- `max_roll_slippage_bps` guardrail + `FUTURES_ROLL_FAILED` circuit breaker

> **[DELTA 2026-05-22]** **Current state:** Representative-future roll pipeline not yet implemented; dated-future
> strategies run fixed-contract slot labels only with manual expiry rotation. **Planned delta:**
> `plans/epics/strategy_master.md` Phase 11 — RepresentativeFutureRegistry (UAC), representative-future-service
> scaffold, REPRESENTATIVE_FUTURE_CHANGED event, FUTURES_ROLL instruction, execution-service combo auto-creation.
> **Target architecture:** Fully automated roll with synthetic-price guardrails + FUTURES_ROLL_FAILED circuit breaker.

Until this ships, dated-future strategies can run on **fixed-contract** slot labels only (`-fixed-{contract}-`), and ops
manually rotate to the next expiry. Workable for a handful of strategies; does not scale.

- `(any -dated- slot, any category, dated_future)` — functional but requires manual roll

---

# UAC Registry Implications

Ten concrete UAC additions are needed so this matrix becomes queryable at runtime (rather than lived in a doc). Each is
tracked separately in [`uac-registry-gaps.md`](uac-registry-gaps.md) (to be written as companion to this doc). In
summary:

| #   | Addition                                                                                                                                                                                                                                                                                                                                                                                                               | Unblocks                                                                                                                                                                                                                                                 |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `ArchetypeCapabilityV2` declaration — queryable archetype → (category, instrument_type) support map                                                                                                                                                                                                                                                                                                                    | The whole matrix; lets strategy-service validate config at deploy-time                                                                                                                                                                                   |
| 2   | `VenueCapabilityV2.supported_signal_variants: dict[InstrumentType, list[str]]`                                                                                                                                                                                                                                                                                                                                         | price vs funding-rate vs IV dispersion distinction                                                                                                                                                                                                       |
| 3   | `FlashLoanReceiverRegistry` with per-chain deployed contract addresses                                                                                                                                                                                                                                                                                                                                                 | `ARBITRAGE_PRICE_DISPERSION × DeFi × lp` (flash-loan arb)                                                                                                                                                                                                |
| 4   | `LiquidationBonusScheduleV2` per-protocol per-collateral-token                                                                                                                                                                                                                                                                                                                                                         | `LIQUIDATION_CAPTURE` precise edge calc                                                                                                                                                                                                                  |
| 5   | `EventCalendarSourceCapability` (Bloomberg, TradingEconomics, TokenUnlocks, protocol governance feeds)                                                                                                                                                                                                                                                                                                                 | `EVENT_DRIVEN` across all categories                                                                                                                                                                                                                     |
| 6   | `IvSurfaceFidelity: Literal["full_surface","atm_only","none"]` on option-capable venue                                                                                                                                                                                                                                                                                                                                 | `VOL_TRADING_OPTIONS`, `ARBITRAGE_PRICE_DISPERSION × option`                                                                                                                                                                                             |
| 7   | `MultiLegOrderCapability.max_legs: int` + per-venue exec-policy                                                                                                                                                                                                                                                                                                                                                        | Option MM + cross-sectional basket + ATOMIC multi-leg                                                                                                                                                                                                    |
| 8   | `PricingFidelity: Literal["tick","snapshot","derived"]` on spot-capable DeFi venue                                                                                                                                                                                                                                                                                                                                     | `ML_DIRECTIONAL_CONTINUOUS × DeFi × spot`                                                                                                                                                                                                                |
| 9   | `LaySideExecutionSemantics` per sports/prediction venue                                                                                                                                                                                                                                                                                                                                                                | `MARKET_MAKING_EVENT_SETTLED` variants                                                                                                                                                                                                                   |
| 10  | `CrossVenueRoutingPolicy` for TradFi (IBKR ↔ CME bridge, ETF ↔ future basis)                                                                                                                                                                                                                                                                                                                                           | `CARRY_BASIS_DATED × TradFi`, `ARBITRAGE_PRICE_DISPERSION × TradFi × dated_future`                                                                                                                                                                       |
| 11  | `RepresentativeFutureRegistry` + `REPRESENTATIVE_FUTURE_CHANGED` event contract — declares underlyings (`BTC-USD-DERIBIT-DATED`, `ES-USD-CME`, ...), the feature group that measures per-contract liquidity, roll-trigger threshold per underlying, and combo-ticker availability. Consumed by strategy-service (subscribers per `-dated-` slot) and execution-service (combo resolution + synthetic-price guardrail). | All `-dated-` slots across `ML_DIRECTIONAL_CONTINUOUS`, `RULES_DIRECTIONAL_CONTINUOUS`, `STAT_ARB_PAIRS_FIXED`, `STAT_ARB_CROSS_SECTIONAL`, `ARBITRAGE_PRICE_DISPERSION × dated_future`, `EVENT_DRIVEN × dated_future`, `CARRY_BASIS_DATED` default mode |

---

# How this SSOT is used

1. **Per-archetype docs** ([`architecture-v2/archetypes/*.md`](archetypes/)) include a short coverage section that is a
   pointer + slimmed table of just that archetype's rows, with a "Full coverage:
   [here](category-instrument-coverage.md#N-ARCHETYPE_ID)" back-link.
2. **Family docs** ([`architecture-v2/families/*.md`](families/)) include a family-level rollup — which categories the
   family covers at all, and which archetype implements which category.
3. **UI** —
   [`lib/architecture-v2/archetypes.ts`](../../../../unified-trading-system-ui/lib/architecture-v2/archetypes.ts) gains
   a `coverage: Record<Category, InstrumentCoverage[]>` field generated from this doc; rendered on `/families/[family]`
   and archetype detail pages with per-cell slot_labels and block-list reasons.
4. **Catalog** —
   [`/catalog`](<../../../../unified-trading-system-ui/app/(platform)/services/research/strategy/catalog/page.tsx>)
   shows the Cartesian product of (archetype × category × instrument_type), with filters and drill-down per cell.
5. **UAC PRs** — each row in the UAC Registry Implications table becomes an issue; tracked in
   [`uac-registry-gaps.md`](uac-registry-gaps.md).

---

# Changelog

- **2026-04-19** — First version. All 18 archetypes × 4 categories × 8 instrument types populated with representative
  slot_labels. 21 block-list entries. 10 UAC registry gaps identified. Companion doc `uac-registry-gaps.md` pending.
- **2026-05-08** — Refresh stub: scope updated to "53 archetypes" per UAC `StrategyArchetype` SSOT (PM@d6d0cd57
  refreshed `strategy-summary.md`); the 18-archetype matrix body is preserved as the May-23 live + immediate-backtest
  subset, full Phase 9 materialisation tracked under `plans/archive/codex_refactor_2026_05_08.plan.md` Phase A.4 + B.
  (Duplicate stub-line removed 2026-05-12 per slot 8 strategy audit ST-16.)
- **2026-05-12** — Currency note: UAC `StrategyArchetype` is now 55 (not 53) per slot 8 strategy audit ST-1 — the
  `CARRY_RECURSIVE_STAKED` split (into `CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED`) was
  the post-2026-05-08 delta. Matrix body remains the 18-archetype subset until the full 55-archetype materialisation
  ships under the codex_refactor plan above.
- **2026-05-18** — UAC `StrategyArchetype` now **57** (not 55) per V-1 taxonomy additions (uac@0196842): renamed
  `CARRY_RECURSIVE_BORROW_PERP_HEDGED` → `CARRY_BASIS_PERP_INV` (net 0) + added `CARRY_STAKED_BASIS_DATED` +
  `CARRY_BASIS_DATED_INV` (+2). Matrix body still the 18-archetype subset until full materialisation.
- **2026-04-19 (same day)** — Added dated-future rolls architecture: continuous-underlying concept,
  representative-future resolution via features, `REPRESENTATIVE_FUTURE_CHANGED` event contract, futures-roll as ATOMIC
  combo (listed or synthesized), circuit breakers. Slot-label convention now distinguishes rolling (`-dated-`) from
  fixed-expiry (`-fixed-{contract}-`). Updated slot-label examples across `ML_DIRECTIONAL_CONTINUOUS`,
  `RULES_DIRECTIONAL_CONTINUOUS`, `CARRY_BASIS_DATED`, `ARBITRAGE_PRICE_DISPERSION`, `STAT_ARB_PAIRS_FIXED`,
  `EVENT_DRIVEN`. New UAC registry gap #11 (`RepresentativeFutureRegistry`). New block-list entry BL-10 (auto-roll +
  combo creation not yet implemented).
