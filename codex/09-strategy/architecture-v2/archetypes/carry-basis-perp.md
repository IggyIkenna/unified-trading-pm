---
doc_type: codex-ssot
title: "Archetype: `CARRY_BASIS_PERP`"
summary: >-
  Archetype CARRY_BASIS_PERP: long spot + short perpetual capturing funding rate while delta-neutral; enter when
  annualized_funding > min_funding_threshold, rebalance on funding drop / venue migration / delta drift. Single-venue
  netted (Binance/OKX/Bybit) or LEADER_HEDGE cross-venue; includes the 2026-06-01 Solana DRIFT-perp + ORCA-spot basis
  variant.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [e2e-testing, strategy-service]
scope: [engineer, admin]
tags: [strategy, carry, defi, cefi, execution, archetype, binance]
related:
  [
    ../families/carry-and-yield.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-dated.md,
    ../../../04-architecture/drift-v2-data-sources.md,
    /codex/02-data/cefi-capture-universe.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
  ]
created: 2026-04-17
authoritative_for: [CARRY_BASIS_PERP archetype specification]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/defi/basis-trade.md,
    /codex/09-strategy/_archived_pre_v2/defi/btc-basis-trade.md,
    /codex/09-strategy/_archived_pre_v2/defi/l2-basis-trade.md,
    /codex/09-strategy/architecture-v2/MIGRATION.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-dated-inv.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-dated.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp-inv.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-overlay-protective-put.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: CARRY_BASIS_PERP
family: CARRY_AND_YIELD
venue_universe: [BINANCE, OKX, BYBIT, HYPERLIQUID, DERIBIT, KRAKEN, UNISWAP_V3, JUPITER, DRIFT, ORCA, RAYDIUM]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 150
  min_sla_tier: premium
---

# Archetype: `CARRY_BASIS_PERP`

> **Family:** [Carry & Yield](../families/carry-and-yield.md) **Settlement model:** Continuous; positions maintained as
> long as funding rate is favorable. **Code module (target):**
> `strategy-service/engine/strategies/carry_basis_perp_engine.py`

## What it does

Long spot + short perpetual future. Captures funding rate (paid by perp longs to perp shorts when perp > spot) while
staying delta-neutral. Position rebalanced when funding rate drops below threshold or moves to another venue.

## Token / position flow

```
1. FUNDING RATE SCAN: monitor funding rates across eligible perp venues for the target asset.
   Enter when annualized_funding > min_funding_threshold (after all costs).

2. PAIRED ENTRY:
   - TRADE: BUY spot (target_notional = allocated_equity)
   - TRADE: SELL perp at venue with highest funding (target_notional = allocated_equity)
   ATOMIC if same venue (e.g., Binance cross-margin netting — enormous capital efficiency).
   LEADER_HEDGE if cross-venue.

3. HOLD: collect funding every funding tick (4h / 8h typical).

4. REBALANCE TRIGGERS:
   - Funding drops below exit_threshold → close position
   - Better funding at another venue → migrate (close old, open new — sequential, not atomic)
   - Delta drift > rebalance_band → rebalance leg sizes
   - Equity change → scale both legs

5. EXIT: close both legs symmetrically (ATOMIC or LEADER_HEDGE).
```

## Supported venues / instruments

**Coverage matrix:** See
[`../category-instrument-coverage.md § 6. CARRY_BASIS_PERP`](../category-instrument-coverage.md#6-carry_basis_perp) for
the authoritative list of representative slot labels, venue pairs, and licensing constraints. Archetype-specific notes:

- Single-venue netted (Binance, OKX, Bybit) delivers the best capital efficiency.
- Cross-venue pairings (CEX spot + CEX perp, DEX spot + CEX perp, L2 spot + CEX perp) carry higher collateral + latency
  cost.
- Multi-coin rotation selects across eligible assets by funding-rate ranking (config-driven).

## Expression options

- Spot: actual asset holding
- Perp: perpetual future

## Hold policies

- CONTINUOUS — hold while funding favorable
- Rebalance cadence config (e.g., re-evaluate venue/coin selection every 4h/8h)

## Config schema

```yaml
spot_venue: UNISWAP_V3_ETHEREUM # or BINANCE for netted
spot_instrument: "UNISWAP_V3:ETH-USDC"
perp_venue: HYPERLIQUID
perp_instrument: "HYPERLIQUID:PERPETUAL:ETH-USD"
target_funding_rate_bps: 80 # 80 bps (8%) annualized minimum
exit_funding_rate_bps: 20 # exit when funding drops below 20 bps
delta_hedge_rebalance_pct: 2 # rebalance if delta > 2%
staking_method: fractional_kelly
max_allocated_equity_pct: 0.30
share_class: USDT
execution_policy_ref: cefi-defi-combined-v7
exploit_venue_netting: true # when spot + perp on same venue

# Leverage + net-delta controls (universal per StrategyInstanceDefinition; Stream D 2026-05-07):
target_leverage: 1.0 # [1, 10]; hard-clamped by per-instrument vol cap at entry
target_net_delta: 0.0 # net directional delta (0 = carry-neutral, delta-hedged)
max_underlying_move_pct: 3.0 # vol-cap clamp: skip entry if realized move > X% in 1h window
instrument_volatility_registry_lookup: true # use realized_vol_20 (1h candles) from FSS
```

## Execution semantics

- Entry: ATOMIC if spot+perp on same venue (Binance batch API); LEADER_HEDGE otherwise
- Exit: same
- Funding collection: passive; PBMS tracks funding accrual per position

### LegController integration

The 2-leg paired entry/exit is the **logical** flow. Mechanically, `LegController.update(slot, tick)` resolves the spot
(leader) and perp (hedge) legs from the `ExecutionPlanner`'s `PairedLegPlan`. Mode selection (ATOMIC vs LEADER_HEDGE) is
derived at preflight from `venue_accepts_batch_orders(venue)`.

**Code-backport status:** DEFERRED — `carry_and_yield/carry_basis_perp.py` still wires legs hand-built. Backport tracked
in `defi_recursive_borrow_archetypes_2026_05_10.md` factory-wiring phase. Docs ship now per operator decision
2026-05-07.

## P&L attribution

- **Funding P&L**: funding_rate × notional × holding_period (earned)
- **Basis change P&L**: entry_basis - exit_basis (minor, tends to zero for perps)
- **Fees / slippage**: per-fill
- **Execution alpha**: vs benchmark

## Risk profile

- Drawdowns: very low (delta-neutral); tail risks are funding reversal, spot/perp spread widening during stress
- Typical Sharpe: 1.5-3.5 for well-run basis (high thanks to low vol + consistent funding)
- Kill switches: funding flips negative beyond hold threshold, LST/spot depeg (if variant with LST), venue outage

## Reaction to equity change

Both legs scale proportionally → ATOMIC reconciliation to avoid delta breach.

## Example instances

```
Single-venue netted:
  CARRY_BASIS_PERP@binance-btc-usdt-prod
  CARRY_BASIS_PERP@okx-eth-usdt-prod
  CARRY_BASIS_PERP@bybit-sol-usdt-prod

Cross-venue:
  CARRY_BASIS_PERP@uniswap-hyperliquid-eth-usdt-prod
  CARRY_BASIS_PERP@coinbase-deribit-btc-usd-prod
  CARRY_BASIS_PERP@uniswap-arbitrum-hyperliquid-eth-usdt-prod

Multi-coin rotation:
  CARRY_BASIS_PERP@binance-multicoin-usdt-prod                 (auto-rotate across BTC/ETH/SOL)
```

## Migration from legacy

| Legacy                                                                         | Notes                                                                     |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| `defi/basis-trade.md`                                                          | Generic perp basis                                                        |
| `defi/btc-basis-trade.md`, `defi/l2-basis-trade.md`, `defi/sol-basis-trade.md` | All same archetype, different instance configs                            |
| `defi/ethena-benchmark.md`                                                     | Ethena's USDe is conceptually a staked-basis product; reference benchmark |
| Code: `basis_trade.py`, `btc_basis.py`, `sol_basis.py`, `l2_basis.py`          | All → `CarryBasisPerpEngine`                                              |

## Not in this archetype

- **Dated-contract basis** (expiry-based arbitrage) — `CARRY_BASIS_DATED`
- **LST collateral on the spot leg** (yield-bearing token + perp hedge) — `CARRY_STAKED_BASIS`
- **Flash-loan leveraged loops on top of staked basis** — `CARRY_RECURSIVE_STAKED`
- **Directional futures / perp trades** (no paired spot) — `ML_DIRECTIONAL_CONTINUOUS` or `RULES_DIRECTIONAL_CONTINUOUS`
- **Cross-venue perp spread arbitrage** (funding-rate differential between two perp venues for the same asset) —
  `ARBITRAGE_PRICE_DISPERSION`

## Solana basis variant (DRIFT perp + ORCA spot) — added 2026-06-01

> Added 2026-06-01 from `plans/archive/solana_basis_trading_mvp_2026_06_01.plan.md` Phase 3 (SolanaBasisGcsLoader wiring
> at strategy-service@6b7e03b7 / a6bbe54c). Strategy slot:
> `SOL_BASIS → CARRY_BASIS_PERP@raydium-drift-sol-1h-sol-v5-prod` (already mapped in
> `archetype_slot_resolver.STRATEGY_TYPE_TO_SLOT` — no new archetype needed).

The Solana basis instance of this archetype runs:

- **Short leg**: SOL-PERP on **DRIFT** (Solana CLOB hybrid w/ vAMM). Funding data via Drift Velocity Data API
  (`data.api.drift.trade`) per `/codex/04-architecture/drift-v2-data-sources.md`. Hourly funding cadence.
- **Long leg**: SOL on **ORCA** Whirlpool SOL/USDC
  ($28M TVL — most liquid Solana SOL/USDC pool). Pool state ingested at
  1-min cadence via Alchemy archive RPC (`getAccountInfo` of Whirlpool account at slot). Secondary: RAYDIUM classic AMM
  WSOL/USDC pool ($14M
  combined TVL) for redundancy / cross-venue dispersion check.
- **Entry**: when annualised Drift SOL-PERP funding > entry threshold (e.g., +500 bps) after fees.
- **Exit**: when funding inverts, drops below exit threshold, or delta-drift exceeds rebalance band.
- **Backtest loader**: `SolanaBasisGcsLoader` (`strategy_service/engine/backtest/solana_basis_loader.py`) reads Drift
  perp_funding + Orca/Raydium dex_pool_state parquets from
  `gs://market-data-tick-defi-prd-${PID}/raw_tick_data/by_date/day=*/pipeline_mode={batch|live}/asset_group=defi/…`.
  GCS-first with fixture fallback via `--source auto`.
- **Live = batch**: the `--live --continuous` flag on the underlying MTDS backfill scripts
  (`backfill_drift_v2_historical.py` + `backfill_solana_dex_state.py`, mtds@1d35c7f2) means the engine consumes the same
  schema from the same path in both modes.
- **Sign check (verified 2025-08-01 fixture run)**: positive Drift funding → SHORT perp + LONG spot → positive PnL in
  funding-positive regime (mirrored on backtest harness e2e-testing@3d02c74).
- **Promote path**: per CLAUDE.md Promote Workflow Path SSOT, valid May-23 target is `paper_1d → live_early`;
  `live_full` is post-cutover. Solana basis MVP G3 (paper) → G4 (live wallet, HUMAN-ONLY) flow tracked in
  `plans/archive/2026_07/defi_manifest_canonicalisation_2026_06_01.md` § G.

Capital efficiency note: Drift + Orca are NOT same-venue cross-margin netting (different programs). LEADER_HEDGE applies
— sequential, not atomic. Solana same-block atomicity (sub-second) is the saving grace vs cross-chain sequential
execution.

## Crypto-venue equity-perp basis variant (equity-basis arb) — added 2026-08-15

> Source: `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Phase 1b/4 (operator ruling
> 2026-07-25, "done first"). Documents the OPPORTUNITY + what's already decided; the full archetype design (dispersion +
> overnight-gap legs) is a still-open `[DESIGN]` P2 todo in that plan's Phase 4, not yet built — this section is not a
> claim that a new StrategyArchetype enum member exists. Structurally this is `CARRY_BASIS_PERP` (long spot + short
> perp, delta-neutral, funding capture) with a **crypto-venue single-stock perp** as the short leg and its **real-equity
> twin** as the long/hedge leg — no new archetype needed, per the README's "no category prefixes" rule.

**What it does.** Short a crypto-venue single-stock perpetual (Binance/OKX/Bybit — e.g. `NVDAUSDT`, `AAPLX`) + long the
real equity on a TradFi venue, capturing the perp's funding rate while staying basis-neutral against the real stock.
24/7-vs-market-hours overnight-gap exposure is a known, not-yet-modeled risk (the perp trades 24/7, the equity hedge
does not) — tracked as the "overnight gap" sub-item of the still-open Phase 4 design todo.

**Universe + sourcing.** The short leg's universe is the UAC `CEFI_EQUITY_PERP_BASE_UNIVERSE` allow-list
(`registry/cefi_instrument_universe.py`); each base is typed `PERPETUAL` (not a distinct `EQUITY_PERP` type, per the
2026-07-16 ruling) and tagged `is_equity_perp=True` at catalogue roll-up. The long leg's real-equity twin is discovered
via the `tracks_equity` catalogue tag → the Databento `DBEQ.BASIC` canonical equity instrument (`crypto_equity_link.py`
`tracks_equity`; `""` for pre-IPO standalones like SPCX, which have no basis leg — dispersion-only across crypto
venues). Full sourcing detail: [`cefi-capture-universe.md`](../../../02-data/cefi-capture-universe.md) § "Exception —
TradFi-linked perps".

**Hedge venue — RESOLVED (operator, 2026-08-08).** The long/hedge leg uses **IBKR cash-stock borrow** for all
single-name pairs (decided same-day 2026-06-20 in the source plan's Phase 1d NET-basis backtest; the 2026-08-08 ruling
approved building it). The IBKR adapter itself is a separate, still-open `[BACKEND]` P0 todo (source plan Phase 1e) —
not shipped by this doc.

**Backtest evidence.** A dividend-adjusted NET-basis backtest across 12 pairs (NVDA/MSFT/CRCL/INTC/GOOGL/AMD/TSLA/AMZN/
META/HOOD/AAPL/BABA, ~11-12mo regime window) confirms every pair remains NET-positive/TRADEABLE once dividend yield is
priced in (dividends sourced via yfinance, not Databento — see
[`tradfi-databento-sourcing-ssot.md`](../../../02-data/tradfi-databento-sourcing-ssot.md) § "DBEQ.BASIC has no dividends
/ corporate-actions schema"). Full per-pair table + methodology: source plan Progress Log, "2026-08-09 — NET-basis
backtest re-run with dividend yield priced in" — numbers are not duplicated here to avoid a second copy rotting
independently of the live backtest script (`e2e-testing/scripts/cefi/net_basis_scan.py`).

**Not yet covered by this variant** (tracked as the source plan's still-open Phase 4 `[DESIGN]` todo, not this doc):
cross-crypto-venue dispersion sizing, the 24/7-vs-market-hours overnight-gap model, and the full `LegController`/config
wiring for this specific venue pairing. **Distinct from** the separate, also still-open "INDEX-perp cash-and-carry" idea
(short Binance `SPXUSDT`/`NAS100`-style index perp + long CME `ES`/`NQ` future, Phase 1c) — that pairs a crypto
index-perp against a TradFi _future_, not a real equity spot, and is not this variant.

## See also

- Family: [carry-and-yield.md](../families/carry-and-yield.md)
- Staked variant: [carry-staked-basis.md](carry-staked-basis.md)
- Recursive variant: [carry-recursive-staked.md](carry-recursive-staked.md)
- Capital efficiency on same-venue netted basis:
  [../../../04-architecture/capital-efficiency-patterns.md](../../../04-architecture/capital-efficiency-patterns.md)
- Drift V2 data sources:
  [../../../04-architecture/drift-v2-data-sources.md](../../../04-architecture/drift-v2-data-sources.md)
- Solana DeFi coverage:
  [../../../04-architecture/solana-defi-coverage.md](../../../04-architecture/solana-defi-coverage.md)
