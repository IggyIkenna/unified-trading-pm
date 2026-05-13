# MVP universe per asset_group — May-23 cutover SSOT

**Created**: 2026-05-13 per operator scope clarification
**Status**: SSOT for **May-23 cutover scope only** — defines which subset of the broader codified architecture must complete a runnable 2-year backtest by 2026-05-23. Binds backtest config-grid sizing, ML training data volume, optimization-plan parallelism multipliers.

## Relationship to existing canonical SSOTs (DO NOT DUPLICATE THESE — REFERENCE THEM)

This doc layers **cutover-scope** on top of existing canonical SSOTs. Do not duplicate cell-level coverage data here — link to the cell-level SSOT instead:

| Information layer | Canonical SSOT (do not re-state here) | What this doc adds |
|---|---|---|
| `StrategyArchetype` enum (53 archetypes) | UAC `unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype` | Tier A (May-23) vs Tier B (code-ready only) classification |
| Per-archetype design (what it does, structure, risk) | `codex/09-strategy/architecture-v2/archetypes/<archetype>.md` (25 files) | n/a — full archetype semantics live there |
| `(archetype × category × instrument_type)` coverage matrix | `codex/09-strategy/architecture-v2/category-instrument-coverage.md` (SUPPORTED / PARTIAL / BLOCKED / N/A per cell) | Cutover-window backtest scope is a SUBSET of "SUPPORTED" cells |
| Per-archetype rollout instances (slot_label + capital_budget + initial_config) | `strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py` | n/a — that catalog is the live SSOT |
| Funding-rate-arb venue pair declarations | UAC `unified_api_contracts.internal.architecture_v2.paired_dispersion_catalog` | Subset of CeFi MVP coins × MVP venues participates in May-23 backtest |
| Per-venue collateral acceptance (LST_AS_MARGIN gating) | UAC `unified_api_contracts.registry.venue_collateral.venue_accepts_collateral` | DeFi LST-family archetypes inherit eligibility from this |
| Per-venue data-type capabilities | UAC `unified_api_contracts.registry.VENUE_DATA_TYPE_CAPABILITIES` (closed set) | Backtest universe filtered to capabilities present |
| Known venue tokens (closed set) | UAC `unified_api_contracts.registry.KNOWN_VENUE_TOKENS` | All venue names in this doc must resolve via that enum |
| Per-archetype capability declaration | UAC `unified_api_contracts.registry.capability_declarations.<archetype>` | Each Tier A archetype must have a capability declaration shipped |

**Hierarchy rule**: this doc cites the SSOT row + adds the cutover-scope annotation. If a row above ships a change, this doc inherits — no parallel maintenance.

## Two-layer scope model (CRITICAL)

The MVP universe has **two distinct scopes** that must not be confused:

### Layer 1: Data capture (broad)

**Rule**: capture ALL markets we can. This includes:
- All instrument-service reference data
- All MTDS tick captures
- All raw_tick_data parquets

**Rationale**: data capture is cheap relative to live trading; broad capture gives us optionality + historical
reconstruction without re-collection cost. Honest-absence semantics handle missing data correctly (CLAUDE.md "Honest
absence vs fake placeholders").

### Layer 2: Backtest / features / strategy / ML training (narrow per-asset-group MVP)

**Rule**: only the explicit per-asset-group MVP universe defined below feeds into:
- features-service compute
- strategy backtest config-grid
- execution-alpha measurement
- ML training + retraining

**Rationale**: backtests and ML training scale poorly with universe size (each instrument × each day × each config cell
= one worker). Narrowing to MVP universe makes cutover-window wall-clock tractable; post-cutover scope expansion follows.

## MVP universe per asset_group

### DeFi (data capture: unconstrained; backtest scope: narrow)

**Backtest universe** (carry_staked_basis + arbitrage_price_dispersion archetypes):

- **LST family**: stETH (Lido), wstETH (Lido wrapped), JitoSOL (Jito), mSOL (Marinade), weETH (EtherFi)
- **Margin venues with LST collateral**: Bybit UTA (stETH margin), Deribit (stETH margin), OKX (wstETH margin), Drift (JitoSOL + mSOL margin)
- **AMM venues**: Uniswap V3 (ETH chain + L2s in scope), Aave V3 (Ethereum + Arbitrum + Base for lending indices)
- **Bridge venues**: Hyperliquid + Aster (perp hedge legs for arbitrage_price_dispersion archetype)
- **Pyth oracle**: Solana on-chain price feeds (PythNet live + Hermes batch)
- **Chainlink oracle**: all EVM chains in scope for non-Solana price feeds

**DeFi data capture (broader)**: all DeFi venues per `unified_api_contracts.defi.DEFI_PERP_VENUES` + `DEFI_AMM_VENUES` +
`DEFI_LENDING_VENUES` regardless of whether they're in the backtest universe. EIGENLAYER rewards, MorphoVaults,
YearnV3 — captured for optionality, not currently in backtest.

### CeFi (data capture: ~30 MVP coins + dust-conversion spot coins; backtest scope: same set)

**Backtest universe** (30 MVP coins, exact list owned by `cefi_master_2026_05_07.md` + per-venue catalog):

- Top-30 by cross-venue volume + perp open-interest concentration.
- All 6 perp venues in scope: Bybit, Deribit, Binance, OKX, Hyperliquid, Aster.
- Per CLAUDE.md "DeFi + CeFi hybrid instrument universe (CRITICAL)": ALL CeFi venues are candidates for perp shorts in
  DeFi archetypes — eligibility is archetype-driven, not asset_group-locked.

**Dust-conversion spot coins** (captured for prices; NOT in backtest config-grid):

- Spot prices for any coin our dust-conversion algos need to convert back to USDC. **EIGEN** explicitly named (operator
  direction 2026-05-13). Add others as dust accumulates; expand list per operational need.

**CeFi data capture (broader)**: all instruments per venue catalog; the 30-coin MVP is a backtest-scope SUBSET, not a
capture-scope cap.

### TradFi (data capture: scoped; backtest scope: same)

**Backtest universe**:
- **S&P 500** (CME ES futures + ES.OPT options + SPY ETF cash equity)
- **BTC-related**: NASDAQ IBIT (BlackRock spot BTC ETF) + CME MBT (micro BTC futures) + CBOE BTC options on IBIT
- **ETH-related**: NASDAQ ETHA (BlackRock spot ETH ETF) + CME MET (micro ETH futures)
- **Up/down markets** (some additional TradFi instruments — exact list owned by `tradfi_master_2026_05_07.md` deliverable A): plus VIX 15m (CBOE) for vol regime
- **Other TradFi MVP**: GLD (gold ETF), USO (oil ETF), UNG (nat-gas ETF) per `defi_master` line 326 cross-instrument carry

**TradFi data capture**: Databento bulk (S&P + crypto-ETF universe) + Yahoo (VIX 15m gap window) + Barchart preload
(VIX 15m historical). All per UAC `SOURCE_PRIORITY` rules.

**Out of TradFi MVP** (post-cutover): full ETF universe (NYSE GBTC / ETHE etc. cleanup), individual equities beyond
S&P 500 components, fixed-income.

### Sports (data capture: unconstrained; backtest scope: Top-5 European football)

**Backtest universe** (RESOLVED 2026-05-08 in `sports_master_2026_05_07.md`):

- **Leagues**: EPL + LaLiga + Serie A + Bundesliga + Ligue 1 (deepest historical coverage, tightest market-making,
  most consistent fixture metadata)
- **Markets**: 1X2 (full-time result), Over/Under 2.5, Both Teams To Score (BTTS), Asian Handicap

**Sports data capture**: ALL leagues api-football + SFI cover (full broad capture); the Top-5 European is a
backtest-scope SUBSET.

**Out of Sports MVP** (post-cutover): MLS, lower-tier European leagues, non-football sports (basketball, tennis, etc.).

### Prediction (data capture: unconstrained; backtest scope: Polymarket subset)

**Backtest universe**:
- **Polymarket** in scope for May-23 backtest + live trading (operator direction 2026-05-13).
- Canonical question groups: BTC_UP_DOWN_HOURLY + other prediction-market archetypes per `predictions_master_2026_05_07.md`.

**Prediction data capture**: Polymarket + Kalshi + opinion.trade all captured at MTDS layer.

**Out of Prediction MVP** (post-cutover):
- **Kalshi** backtest + live → 2026-06-15 (`wave2_polymarket` plan Phase 3 split per operator direction 2026-05-13).
- **opinion.trade** backtest + live → 2026-06-15 (same split).

## Cross-asset implications

### Backtest config-grid sizing math

| Asset group | Instruments in backtest | Days (2-yr) | Config cells | Total workers (rough) |
|---|---:|---:|---:|---:|
| DeFi | ~12 LST + 4 AMM venues | 730 | ~15-20 | ~10K |
| CeFi | 30 coins × 6 perp venues | 730 | ~15-20 | ~50-65K |
| TradFi | ~10 instruments (S&P + crypto-ETF + futures + options) | 730 | ~10-15 | ~7-10K |
| Sports | ~1000 fixtures/yr × 5 leagues × 4 markets | n/a (fixture-bound) | ~10 | ~80K-200K |
| Prediction | Polymarket subset (~50 questions/day × 2yr) | 730 | ~10 | ~30-40K |

**Total backtest scope**: ~180K-400K worker-runs across the cutover-window 2-yr config-grid. At ~5s per worker on
`c3-highcpu-44` parallel-shard (per `mock_data_pipeline_benchmarking_2026_05_10` benchmark output), that's
~250K × 5s ÷ 176-way-parallel (`c3-highcpu-176`) = **~7000s ≈ 2 hours per archetype-bundle**, achievable in cutover
window.

**Without the MVP narrowing** (e.g., if CeFi expanded to 500 coins): worker count balloons 10×, wall-clock becomes
20+ hours per archetype — would not fit cutover window.

### ML training data volume

ML training scope is tied to the backtest universe (only MVP-universe features are used as training inputs):
- TradFi S&P swing-prediction: ~10 instruments × 730 days × ~50 features = ~365K training rows
- DeFi carry_staked_basis: ~12 LST × ~5 venues × 730 days × ~30 features = ~1.3M rows
- CeFi perp arbitrage: 30 coins × 6 venues × 730 days × ~20 features = ~2.6M rows
- Sports: ~5000 fixtures/yr × 2 yrs × ~80 features = ~800K rows
- Prediction: ~50 q/day × 730 days × ~25 features = ~900K rows

**Total**: ~6M training rows across all archetypes. Comfortable for lightgbm + small torch models on
`c3-highcpu-44` or `n2d-standard-32`.

### Feature compute parallelism multiplier

Per-asset-group features-service compute scales with backtest universe size, NOT data-capture universe size.
Optimization plan ([`compute_optimization_mock_data_2026_05_13.md`](../../plans/active/compute_optimization_mock_data_2026_05_13.md))
Phase 2 sizing uses MVP-universe numbers above.

## Strategy archetypes — backtest-complete by 2026-05-23 vs code-ready (operator direction 2026-05-13)

**Two-tier archetype scope**:

### Tier A: Backtest-complete by May-23 cutover (THE goalposts)

These archetypes MUST have a runnable 2-year backtest config-grid by 2026-05-23. They feed Group F items 17/18/20/21.

| Archetype family | Specific archetypes | Asset groups touched | Notes |
|---|---|---|---|
| **ml-continuous** | online-feature ML retraining loop, continuous regime detection | CeFi perp coins + ES (S&P futures) | Daily retraining cadence; ml-inference live mode |
| **ml-settled** | post-event-settlement ML (each fixture closes the training window) | Sports (Top-5 EU football, 4 markets) | Per-fixture lifecycle; ml-training fires on fixture settlement |
| **arbitrage-funding-rate** | cross-venue perp funding spread arb | CeFi (6 perp venues × 30 MVP coins) + DeFi perp legs (Hyperliquid, Aster) | This IS `arbitrage_price_dispersion` archetype per defi_master |
| **arbitrage-sports-book** | Polymarket vs Betfair odds discrepancy | Prediction (Polymarket) + Sports (Betfair odds) | Cross-domain — books on same event, different liquidity profile |
| **arbitrage-event-markets** | Polymarket vs CME event-contract arbitrage | Prediction (Polymarket) + TradFi (CME EVENT_CONTRACT) | Same event traded on prediction-market + CME futures (`cme_polymarket_arb_2026_05_08.md` covers this) |
| **defi-carry-family** | `carry_staked_basis`, `carry_recursive_borrow_lending_only`, `carry_recursive_borrow_perp_hedged`, `arbitrage_price_dispersion`, all other carry-family archetypes per `codex/09-strategy/architecture-v2/archetypes/` | DeFi (LST + AMM + lending) + CeFi (perp hedge legs) | ALL carry-family archetypes ship backtest-ready by May-23 |

**Note on arbitrage-price-dispersion vs arbitrage-funding-rate**: master plan + defi_master use `arbitrage_price_dispersion` as the archetype name; the user-facing term is "funding-rate arbitrage" (same thing). Cross-venue funding spread is the price-dispersion signal.

### Tier B: Code-ready but NOT in May-23 backtest scope

These archetypes have **production-quality code shipped** (registry, calculators, signal generators, execution wiring) but **do NOT need to complete a 2-year backtest** by 2026-05-23. Code-readiness drives architecture decisions (closed-set registry, capability_declarations, schema completeness) without consuming cutover-window backtest cycles.

| Archetype family | Asset groups | Why code-ready (not backtest) |
|---|---|---|
| **Options-strategy archetypes** | TradFi ES.OPT, CME crypto options, Deribit options, CBOE crypto-ETF options | Options pricing + greeks + matching engine must be production-quality for architecture consistency (matcher classes, capability declarations, archetype schema); 2-yr backtest deferred to post-cutover |
| **Other DeFi non-carry archetypes** (if any beyond carry family) | DeFi | Architecture coverage; future expansion lanes |
| **Vol-regime + cross-sectional ML beyond ml-continuous/ml-settled** | All asset groups | ML framework supports broader archetype patterns; specific architectures shipped, full-train deferred |
| **Long-tail prediction markets** (beyond Polymarket) | Prediction (Kalshi, opinion.trade) | Per `wave2_polymarket` plan split: Polymarket subset May-23, Kalshi/opinion.trade migration 2026-06-15 |

**Architectural rationale**: shipping options code-ready forces the matcher class hierarchy to be correct (L0 sports TOB / L1 TradFi / L2 CeFi / AMM / ALPHA_ZERO benchmark fills) + the closed-set archetype registry to handle all the surface area. If we descope options entirely, the architecture is biased to non-options patterns and post-cutover expansion becomes painful.

### Backtest config-grid scope per archetype

For Tier A archetypes (May-23 backtest scope), per `compute_optimization_mock_data_2026_05_13.md`:

| Archetype | Instruments | Config grid cells | Workers (730d × cells × insts) |
|---|---:|---:|---:|
| ml-continuous (CeFi + ES) | 30 CeFi + 1 ES = 31 | ~15 | ~340K worker-runs |
| ml-settled (Sports) | ~5000 fixtures × 4 markets | ~10 | ~200K worker-runs |
| arbitrage-funding-rate | 30 coins × 6 perp venues = 180 venue-pairs | ~10 | ~1.3M worker-runs ⚠ |
| arbitrage-sports-book | Top-5 EU × ~1000 fixtures × 4 markets | ~10 | ~200K worker-runs |
| arbitrage-event-markets | ~20 simultaneous Poly+CME events | ~10 | ~150K worker-runs |
| defi-carry-family (5 archetypes) | 12 LST × 4 AMM × 730 days | ~15 per archetype × 5 = 75 | ~440K worker-runs |

**Total**: ~2.6M backtest worker-runs across Tier A by May-23. ⚠ Funding-rate arb is the heaviest single component (venue-pair combinatorial). Optimization plan Phase 5 (big-machine SKU matrix) sizes for this.

**With `c3-highcpu-176` at ~5s/worker fully parallel**: 2.6M ÷ (176 × 16 hours × 3600s/5s) ≈ 1.3 days wall-clock for full Tier A backtest. Fits cutover window.

## What this SSOT does NOT cover

- **Live-trading universe**: subset of backtest universe per archetype. Live-trading capital allocation lives in
  `cross_cutting_may_23_deliverables` + `wallet_treasury_client_flow`.
- **Per-cycle expansion**: post-cutover scope grows (MLS, more coins, more TradFi instruments). Expansion plan owned
  by individual archetype owners + master plan post-cutover phases.
- **Data-type coverage** within each instrument (ohlcv vs trades vs orderbook vs funding): owned by per-venue catalog
  in `unified_api_contracts.<asset_group>.capability_declarations`.

## References

- Sports MVP resolved at `plans/epics/sports_master_2026_05_07.md` § "Leagues in scope" (2026-05-08).
- TradFi MVP at `plans/epics/tradfi_master_2026_05_07.md` deliverable A.
- DeFi archetypes + LST family at `plans/active/defi_master_2026_05_07.md` + `codex/09-strategy/architecture-v2/archetypes/`.
- CeFi MVP coin list at `plans/epics/cefi_master_2026_05_07.md` (catalog).
- Prediction MVP at `plans/epics/predictions_master_2026_05_07.md` + `plans/active/wave2_polymarket_record_captured_from_counts_2026_05_09.md`.
- Backtest config-grid scale + per-stage SKU at `plans/active/compute_optimization_mock_data_2026_05_13.md`.
- 2-yr config-grid backtest gates Group F item 18 of master plan.

## Continuous verification

This SSOT is read at cutover-window kickoff (2026-05-15 freeze gate) to confirm:
1. Each asset_group's backtest-universe matches the per-instrument catalog SHIPPED state.
2. Optimization plan parallelism multipliers reflect actual instrument counts.
3. ML training data volume estimates align with the backtest universe.

Last reviewed: 2026-05-13. Next review: 2026-05-22 pre-cutover sign-off.
