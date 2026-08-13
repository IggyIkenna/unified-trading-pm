---
doc_type: codex-ssot
title: "Archetype: `ARBITRAGE_PRICE_DISPERSION`"
summary: >-
  Archetype ARBITRAGE_PRICE_DISPERSION: paired same-instrument cross-venue spread capture (cross-CEX/DEX spot-perp,
  sports cross-book, prediction, cross-venue vol, funding-rate dispersion) via ATOMIC or LEADER_HEDGE. SHIPPED: Variant
  A price_dispersion.py (requires >=2 candidate_venues) + Variant B funding-rate dispersion over 6 CeFi perps with
  dynamic-best-long-short pair selection + Variant C cross-venue-prediction-dispersion, an N-venue best-pair scan over
  Kalshi/Polymarket/Betfair gated on NET-of-fees edge.
implementation_status: code-shipped
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, arbitrage, defi, cefi, execution, archetype, binance]
related:
  [
    ../families/arbitrage-structural.md,
    /codex/09-strategy/architecture-v2/archetypes/liquidation-capture.md,
    ../cross-cutting/execution-policies.md,
    ../../../02-venues/unity-integration.md,
    ../cross-cutting/mev-protection.md,
    ../../../04-architecture/cross-venue-prediction-arb-detection.md,
  ]
created: 2026-04-17
authoritative_for: [ARBITRAGE_PRICE_DISPERSION archetype specification]
referenced_by:
  [
    /codex/02-venues/unity-integration.md,
    /codex/09-strategy/_archived_pre_v2/cefi/cross-exchange.md,
    /codex/09-strategy/_archived_pre_v2/prediction/prediction-arb.md,
    /codex/09-strategy/_archived_pre_v2/sports/arbitrage.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-cross-domain-event.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-backrun.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-liquidation-bundle.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-sandwich.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: ARBITRAGE_PRICE_DISPERSION
family: ARBITRAGE_STRUCTURAL
venue_universe:
  [
    BINANCE,
    BYBIT,
    OKX,
    DERIBIT,
    HYPERLIQUID,
    ASTER,
    KRAKEN,
    UNISWAP_V3,
    BALANCER,
    CURVE,
    UNITY,
    BETFAIR_DIRECT,
    SMARKETS_DIRECT,
    POLYMARKET,
  ]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 150
  min_sla_tier: premium
---

# Archetype: `ARBITRAGE_PRICE_DISPERSION`

> **Family:** [Arbitrage / Structural Edge](../families/arbitrage-structural.md) **Settlement model:** ATOMIC (when
> venue supports) or LEADER_HEDGE (when atomic isn't possible). **Code module (SHIPPED):**
> `strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion.py` (+
> `price_dispersion_hierarchical.py` for the hierarchical variant)

## What it does

Detects price dispersion between venues on the same (or equivalent) instrument and executes a paired position that locks
in the spread net of costs. Covers:

- Cross-CEX spot / perp arb
- Cross-DEX arb (same chain, flash-loan optionally)
- Sports cross-book arb (via Unity prime broker — single wallet)
- Cross-category arb (Polymarket ↔ Betfair/Unity for correlated markets)
- Cross-venue vol arb (same option quoted at different IVs on Deribit vs OKX options)
- Within-venue no-arb violations (butterfly / calendar / put-call parity)
- Funding-rate dispersion arb (net position sized to capture funding differential)

## Token / position flow

```
1. DISPERSION SCANNER (continuous):
   - Per eligible (instrument, venue) pair: read prices / odds / IVs
   - Compute gross spread: best_bid_venue_A - best_ask_venue_B (or equivalent)
   - Deduct all costs: fees, slippage, gas, bridge, commission, execution spread
   - If net_spread > min_edge_threshold: opportunity found

2. OPPORTUNITY VALIDATION:
   - Verify liquidity on both legs: can we execute our target size?
   - Verify venue connectivity healthy
   - Verify we have pre-funded capital on both venues (or flash-loan available)
   - Pre-flight check against venue-account health

3. EXECUTION DISPATCH:
   Select mode based on venue support:
   - ATOMIC: if both legs on same chain, use multicall / batch API / flash-loan
   - LEADER_HEDGE: if cross-venue non-atomic, declare leader leg + hedge leg +
                   max_hedge_delay + abort_on_adverse_move

4. SUBMIT + RECONCILE:
   - ATOMIC: entire bundle succeeds or reverts; P&L realized atomically
   - LEADER_HEDGE: execution submits leader; on fill, submits hedge immediately;
                   monitors reference price move; aborts + unwinds if thresholds breached

5. POST-EXIT STATE: capital returns to idle (typically net-zero exposure + cash profit)
```

**Venue × instrument coverage:** See
[`../category-instrument-coverage.md § 11. ARBITRAGE_PRICE_DISPERSION`](../category-instrument-coverage.md#11-arbitrage_price_dispersion).
The table below enumerates the execution-mode patterns by scenario — a complement to the coverage matrix, not a
duplicate.

## Supported scenarios + execution modes

| Scenario                                                    | Execution mode                          | Notes                                                                  |
| ----------------------------------------------------------- | --------------------------------------- | ---------------------------------------------------------------------- |
| Flash-loan DEX arb (Uniswap ↔ Balancer) single chain        | ATOMIC (flash-loan + multicall)         | Risk-free if profitable after gas                                      |
| Cross-DEX arb same chain without flash loan                 | ATOMIC (multicall)                      | Profitable if price dispersion > gas + slippage                        |
| Cross-CEX arb (Binance ↔ Bybit on BTC-USDT)                 | LEADER_HEDGE                            | Different API endpoints; legs can't be atomic                          |
| Sports cross-book via Unity                                 | ATOMIC within Unity API                 | Unity single-wallet routes bets to chosen child books; near-atomic     |
| Sports cross-book direct (Betfair direct ↔ Smarkets direct) | LEADER_HEDGE                            | Different accounts; leg-then-hedge                                     |
| Cross-venue vol arb (Deribit ↔ OKX options)                 | LEADER_HEDGE                            | Two options venues, separate wallets                                   |
| Within-surface no-arb violation                             | ATOMIC (multi-leg bundle on same venue) | E.g., butterfly: buy wings, sell body — single Deribit multi-leg order |
| Funding-rate dispersion arb                                 | LEADER_HEDGE (usually)                  | Enter paired position; hold until funding normalizes                   |

## Config schema

> **⚠️ SUPERSEDED (generic schema below)** — the generic `opportunity_type`/`eligible_venues`/`eligible_markets` schema
> below was the original design. The two deployed variants are documented in the concrete sections that follow. Use
> those for new strategy-instance configs.

```yaml
# LEGACY GENERIC SCHEMA — for reference only; use variant sections below for actual configs
opportunity_type: CROSS_BOOK_SPORTS # or CROSS_DEX_SPOT, CROSS_CEX_SPOT, CROSS_VENUE_VOL, SURFACE_NOARB, FUNDING_DISPERSION
eligible_venues:
  - UNITY # with child_books preference list
  - BETFAIR_DIRECT
  - SMARKETS_DIRECT
eligible_markets:
  - league: EPL
    markets: ["1X2", "OVER_UNDER_2_5"]
min_edge_bps: 50 # 50 bps minimum after all costs
max_capital_per_opp_pct: 0.05 # 5% of equity per opp
max_concurrent_opps: 10
execution_ordering:
  mode: ATOMIC # or LEADER_HEDGE
  leader: UNITY # for LEADER_HEDGE
  hedge: BETFAIR_DIRECT
  max_hedge_delay_ms: 500
  abort_on_adverse_move_bps: 10
execution_policy_ref: arb-fast-v2
share_class: USD

# Leverage + net-delta controls (universal per StrategyInstanceDefinition; Stream D 2026-05-07):
target_leverage: 1.0 # [1, 10]; hard-clamped by per-instrument vol cap at entry
target_net_delta: 0.0 # net directional delta target (0 = delta-neutral arb)
max_underlying_move_pct: 3.0 # vol-cap clamp: abort/skip if realized move > X% in 1h window
instrument_volatility_registry_lookup: true # use realized_vol_20 (1h candles) from FSS

# Chain constraint (UAC canonical/crosscutting/defi.ChainKind; Phase 3 defi_master 2026-05-18):
# Gates the DeFi on-chain leg only (CROSS_DEX_SPOT / CROSS_DEX_SPOT + flash-loan variants).
# CeFi perps, sports, and prediction legs have no ChainKind — not gated by this field.
# FUNDING_DISPERSION variant (Variant B): uses 6 CeFi perp venues (bybit/deribit/binance/okx/
# hyperliquid/aster) — no on-chain DeFi leg, so allowed_chains is irrelevant for that variant.
# For DEX-perp dispersion (if added in future): Drift (solana) is on-chain — chain-gate applies.
allowed_chains: [ethereum, arbitrum, solana, base, optimism]
```

### Variant A — Price-dispersion path (CURRENT IMPLEMENTATION in `price_dispersion.py`)

REQUIRED_PARAMS = `{"candidate_venues"}` — engine raises `ValueError` at boot if absent or contains fewer than 2 venues.

```yaml
# Required:
candidate_venues: [BINANCE, BYBIT] # ≥2 venues required; raises ValueError at boot if absent or <2

# Optional (engine defaults shown):
dispersion_bps: "30" # minimum cross-venue price gap to trigger entry
cost_bps: "10" # round-trip transaction cost estimate
stake_fraction: "0.1" # fraction of capital per opportunity
hedge_deadline_ms: "5000" # max ms between leader fill and hedge submission

# Universal StrategyInstanceDefinition fields:
target_leverage: "1.0"
target_net_delta: "0.0"
max_underlying_move_pct: "3.0"
instrument_volatility_registry_lookup: "true"
allowed_chains: [ethereum, arbitrum, solana, base, optimism]
share_class: USD
```

### Variant B — Funding-rate dispersion

Uses paired long/short positions across perp venues to capture funding-rate spread. Engine:
`price_dispersion._on_tick_funding_rate_dispersion()` + `funding_rate_dispersion.py` (VenuePair, PairSelectionMode,
VolCapClampConfig). Fully implemented as of 2026-05-20.

Venue universe (May-23): bybit, deribit, binance, okx, hyperliquid, aster (6 CeFi perps). Pair selection:
`dynamic-best-long-short` (PairSelectionMode) — ranks all venue pairs by funding spread net of cost, takes the best long
venue vs best short venue each tick.

Key params:

```
dispersion_type: "funding-rate-dispersion"
venue_universe: "bybit,deribit,binance,okx,hyperliquid,aster"
pair_selection_mode: "dynamic-best-long-short"
target_leverage: "5.0"
vol_cap_clamp_feature: "realized_vol_20"
vol_cap_clamp_threshold_pct: "80.0"
vol_cap_clamp_zscore_feature: "vol_regime_zscore_20"
vol_cap_clamp_zscore_threshold: "2.0"
vol_cap_clamp_combine: "any"
cost_bps: "10"
```

Catalog slots (catalog.py `_build_arbitrage_price_dispersion`):

- `ARBITRAGE_PRICE_DISPERSION@bybit-deribit-binance-okx-hyperliquid-aster-funding-rate-disp-btc-usdt-v5-prod`
- `ARBITRAGE_PRICE_DISPERSION@bybit-deribit-binance-okx-hyperliquid-aster-funding-rate-disp-eth-usdt-v5-prod`

## Execution semantics

- `ATOMIC` instruction type for bundled legs
- `TRADE` instructions sequenced for LEADER_HEDGE
- Execution-service enforces leader-hedge timing via execution_policy_ref
- Mid-execution abort if conditions breach (unwind whichever leg filled)

### LegController integration

Both ATOMIC and LEADER_HEDGE modes flow through `LegController.update(slot, tick)`. The controller reads the
`DispersionOpportunity` from `features-onchain` and maps it to the leg sequence:

- **ATOMIC mode**: buy leg + sell leg emitted as a single bundled `AtomicInstruction` with `execution_mode=ATOMIC`.
- **LEADER_HEDGE mode**: leader (larger/safer venue) fires first; `LegController.on_leader_fill()` triggers the hedge
  leg within `hedge_deadline_ms`; `CLOSE_LEADER_IF_HEDGE_FAILS` compensation on deadline breach.

**Code-backport status:** DEFERRED — `arbitrage/price_dispersion.py` still builds legs inline. Backport tracked in
`defi_recursive_borrow_archetypes_2026_05_10.md` factory-wiring phase. Docs ship now per operator decision 2026-05-07.

## P&L attribution

- **Arb edge captured**: (total_received - total_paid) on successful opp
- **Execution slippage**: difference between detected spread and realized spread
- **Gas / fees / commission**: per opp
- **Adverse-move losses** (leader-hedge aborts): unwind cost when hedge failed to fill in time

## Risk profile

- Drawdowns: rare but sharp when execution fails mid-sequence (partial fill, adverse move, gas auction loss)
- Typical Sharpe: 3+ when opportunities are found; limited by opportunity frequency
- Kill switches: abnormal dispersion (likely broken feed), consecutive execution failures, venue outage

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    self.max_capital_per_opp = new_equity * self.config.max_capital_per_opp_pct
    return []   # no in-flight positions to resize
```

## Example instances

Active catalog slots (2026-05-20, from `catalog.py _build_arbitrage_price_dispersion`):

```
Lending protocol arb (same chain, different protocols):
  ARBITRAGE_PRICE_DISPERSION@aave-compound-ethereum-usdc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@aave-morpho-ethereum-usdc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@aave-compound-arbitrum-usdc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@aave-morpho-arbitrum-usdc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@aave-compound-optimism-usdc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@aave-morpho-optimism-usdc-1h-usdc-v2-prod

Cross-chain yield arb (same protocol, different chains):
  ARBITRAGE_PRICE_DISPERSION@aave-ethereum-arbitrum-usdc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@aave-ethereum-optimism-usdc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@aave-arbitrum-base-usdc-1h-usdc-v2-prod

CEX-CEX spot/perp spread arb:
  ARBITRAGE_PRICE_DISPERSION@binance-okx-btc-1m-usdt-v2-prod
  ARBITRAGE_PRICE_DISPERSION@binance-bybit-eth-1m-usdt-v2-prod
  ARBITRAGE_PRICE_DISPERSION@okx-hyperliquid-sol-1m-usdt-v2-prod

Sports cross-book arb:
  ARBITRAGE_PRICE_DISPERSION@unity-betfair-matchbook-epl-gbp-v2-prod
  ARBITRAGE_PRICE_DISPERSION@unity-betfair-matchbook-nba-gbp-v2-prod

Prediction market arb:
  ARBITRAGE_PRICE_DISPERSION@polymarket-betfair-sports-gbp-v2-prod

Cross-venue dated futures arb (CME micro vs Deribit, same expiry):
  ARBITRAGE_PRICE_DISPERSION@cme-deribit-mbt-btc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@cme-deribit-met-eth-1h-usdc-v2-prod
```

Funding-rate dispersion slots live in the legacy-factory bridge (`archetype_slot_resolver.py`) not in the catalog — see
Variant B above for labels and config.

Bridge slots (2026-05-20, from `archetype_slot_resolver.py STRATEGY_TYPE_TO_SLOT`):

```
  ARBITRAGE_PRICE_DISPERSION@bybit-deribit-binance-okx-hyperliquid-aster-funding-rate-disp-btc-usdt-v5-prod
  ARBITRAGE_PRICE_DISPERSION@bybit-deribit-binance-okx-hyperliquid-aster-funding-rate-disp-eth-usdt-v5-prod
  ARBITRAGE_PRICE_DISPERSION@bybit-deribit-binance-okx-hyperliquid-aster-funding-rate-disp-sol-usdt-v5-prod
  # + XRP, DOGE, BNB, ADA, AVAX (4-venue), TRX (3-venue)
  # Reached via resolve_strategy_type("BTC_FUNDING_RATE_DISPERSION") etc.
```

## Migration from legacy

| Legacy                                                                                                                   | Notes                                                                                 |
| ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| `sports/arbitrage.md`                                                                                                    | Primary migration target                                                              |
| `defi/cross-chain-sor-rebalancing.md`                                                                                    | Split: transient dispersion arb → here; pure rebalancing → Transfer/Rebalance service |
| `defi/cross-chain-yield-arb.md`                                                                                          | If transient dispersion → here; if sustained rate spread → YIELD_ROTATION_LENDING     |
| Code: `cross_exchange_btc.py`, `lending_protocol_arb.py`, `prediction_arb_btc.py`, `vol_surface_btc.py` (if hard no-arb) | → `ArbitragePriceDispersionEngine`                                                    |

## Not in this archetype

- **Liquidation snipe during cascades** — `LIQUIDATION_CAPTURE`
- **Cross-strategy capital rebalancing** (move capital to a better strategy) — portfolio-allocator service, not a
  strategy
- **ML-predicted momentum divergence** (model says A will outperform B) — `ML_DIRECTIONAL_CONTINUOUS` on one leg, not
  structural arb
- **Cointegrated pair trades** (z-score reversion) — `STAT_ARB_PAIRS_FIXED`

## See also

- Family: [arbitrage-structural.md](../families/arbitrage-structural.md)
- Liquidation variant: [liquidation-capture.md](liquidation-capture.md)
- Leader-hedge execution: [../cross-cutting/execution-policies.md](../cross-cutting/execution-policies.md)
- Unity integration (primary sports venue):
  [../../../02-venues/unity-integration.md](../../../02-venues/unity-integration.md)
- MEV protection for DeFi arb: [../cross-cutting/mev-protection.md](../cross-cutting/mev-protection.md)
- **Venue-matrix / canonicalisation plan** (Stream B: funding-rate-dispersion multi-venue + Stream D: target_leverage /
  vol-cap config schema):
  [`plans/active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](../../../../plans/archive/2026_05/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
- **Finalisation plan** (APD execution orchestrator Phase A; archived 2026-05-09):
  [`plans/archive/arbitrage_price_dispersion_finalisation_2026_05_09.md`](../../../../plans/archive/arbitrage_price_dispersion_finalisation_2026_05_09.md)
