---
name: defi-readiness-catalogue
overview: DeFi-led readiness audit — actual venue + asset + pool + LST + lending + perp + chain catalogue we have vs want, per-venue data-type taxonomy (funding rates / lending indices / governance / oracle prices / restaking / gas), Solana chain coverage, AMM slippage + rate-impact simulation primitives, RPC + MEV protection + Tenderly simulation hookups; with cross-asset-group catalogue gap-check (CeFi / TradFi / sports / prediction).
type: question
status: drafting
created: 2026-05-08
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-08
spawned_plan: null
related_codex:
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/honest-absence-downstream-handling.md
  - codex/04-architecture/interface-credential-convention.md
  - codex/04-architecture/flash-loan-receiver.md
  - codex/05-infrastructure/launcher-script-ssot.md
related_plans:
  - plans/epics/defi_master_2026_05_07.md
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/epics/cefi_master_2026_05_07.md
  - plans/epics/tradfi_master_2026_05_07.md
  - plans/epics/sports_master_2026_05_07.md
  - plans/epics/predictions_master_2026_05_07.md
---

# DeFi readiness — venue / asset / data catalogue + chain primitives + simulation hookups

## Intent

The May-23 cutover lands two DeFi archetypes (`carry_staked_basis` lead + `leveraged_funding_arb`) live on real wallet
≥7 continuous days, with hedge legs across 6 perp venues (Bybit / Deribit / Binance / OKX / Hyperliquid / Aster) and
full AWS↔GCP cloud parity. Both archetypes lean on a long list of **DeFi primitives we either have, partially have, or
don't have yet**: LSTs (jitoSOL / mSOL / bSOL on Solana, stETH / rETH on EVM), lending markets (Aave / Spark / Morpho /
Compound), DEX pools for hedge unwind (Uniswap V3 / Curve / Balancer / Raydium / Orca), oracle prices (Chainlink EVM +
Pyth Solana per the 2026-05-06 unbanning), gas-fee streams per chain (live + historical), and simulation surfaces (AMM
slippage, lending rate impact from our own trade, governance-protocol rate dynamics, restaking yield variability beyond
vanilla EigenLayer).

The operator's question collapses to: **what's actually in the catalogue today, what's the per-venue data-type matrix,
where are the gaps, and which gaps are blockers for the May-23 cutover?** With the same gap-check applied — at lower
detail — to CeFi / TradFi / sports / prediction so we have one workspace-wide catalogue audit, not five disconnected
per-asset-group probes.

The doc deliberately rakes across many orthogonal axes (venue / asset / chain / instrument-type / data-type / oracle /
simulation surface / live-vs-batch parity) because the operator's mental model is one cross-cutting catalogue, not five
silos. The audit pass will surface the actual state per axis; iteration will partition into per-archetype +
per-asset_group plans for execution.

## Question

### Block A — Cross-asset-group venue + asset catalogue baseline

A1. **What is the canonical SSOT today for the venue + asset catalogue per asset_group?** I expect this to live in UAC
under `unified_api_contracts.canonical.crosscutting.*` + per-domain registries (e.g. `domain.cefi.*`, `domain.defi.*`,
`domain.sports.*`, `domain.prediction.*`). Per the workspace asset-group vocabulary rule the axis is `asset_group ∈
{cefi, defi, tradfi, sports, prediction}` — but is there ONE canonical "give me every (asset_group, venue, asset,
data_type) tuple we currently capture" surface, or do I have to grep across 5 domain modules?

A2. **Per-asset-group catalogue counts** — at the leaf "we have / are capturing / can serve to a strategy today" level:
  - **CeFi**: how many venues × how many spot instruments × how many perp instruments × how many option roots × how many
    futures roots? (My ballpark: 6 perp venues + ~4 spot venues + Deribit options + ES.OPT/MBT/MET futures roots, but
    confirm.)
  - **TradFi**: which root products (ES / MBT / MET / VIX, etc.), which ETFs, which option chains (ES.OPT 11-cluster +
    others?), and which sources (Databento + Barchart + Yahoo per the VIX 15m layering rule)?
  - **Sports**: which leagues × which sources (api_football / footystats / understat / transfermarkt / soccer_football_
    info / open_meteo / odds_api / mdps_odds_horizon_bucket)? Per-source coverage windows per UAC `SOURCE_COVERAGE_
    START` + `DATA_TYPE_COVERAGE_START`?
  - **Prediction**: which canonical question groups, which venues (Polymarket + Kalshi + ?), how many market_ids
    enumerated per group, what coverage of recurring (HOURLY / DAILY) vs one-shot (ELECTION) groups? Is the
    instruments-service catalogue capturing all three lifecycle timestamps (`market_created_at` / `resolution_time` /
    `settlement_time`) per market_id?
  - **DeFi**: which chains × which protocols × which assets × which pools? (Detail in Block B.)

A3. **Are these catalogues exhaustively captured in the availability manifest, or only partially?** Per honest-coverage
rule, every (asset_group, venue, data_type, day) row should resolve to one of `captured` / `empty_confirmed` /
`attempted_failed` / `expected_unattempted`. Are there asset_groups where the manifest is silent (no row at all) for
day-shards that should exist?

### Block B — DeFi-specific catalogue (the deep dive)

B1. **DeFi venues + protocols across chains** — for each chain in scope (ethereum, arbitrum, base, polygon, optimism,
solana, others?), enumerate:
  - **Lending protocols**: Aave V3 / Spark / Morpho / Compound V3 / Radiant / Solend (Solana) / Kamino (Solana) — which
    are wired in instruments-service as catalogued markets, which are in execution-service as live connectors, which
    have historical capture in MTDS?
  - **DEX protocols**: Uniswap V3 + V4 / Curve / Balancer / Sushi / PancakeSwap / Raydium (Solana) / Orca (Solana) /
    Jupiter (Solana aggregator) — same three-axis question.
  - **LST protocols**: Lido (stETH on EVM) / Rocket Pool (rETH on EVM) / Frax / Jito (jitoSOL on Solana) / Marinade
    (mSOL on Solana) / Solblaze (bSOL on Solana) — catalogued + capture + execution wiring per protocol.
  - **Restaking + LRT protocols**: EigenLayer + Symbiotic + Karak (EVM); is there a Solana restaking surface in scope
    (Jito restaking?)? Which liquid restaking tokens (eETH / weETH from Ether.fi, ezETH from Renzo, rsETH from KelpDAO,
    etc.) are catalogued + captured?
  - **Perp DEXes**: Hyperliquid + Aster + dYdX + GMX + Vertex + Drift (Solana) — does the master plan's "6 perp venues"
    include any DEX perps (Hyperliquid + Aster YES per master), or are CeFi-only? (Bybit + Deribit + Binance + OKX = 4
    CeFi; Hyperliquid + Aster = 2 DeFi → all 6.) Confirm + enumerate per-venue funding rate + open-interest +
    liquidation cascade data capture.
  - **Yield aggregators / vaults**: Yearn / Convex / Aura / Beefy — are any of these catalogued, or is the model "we
    consume the underlying primitives directly, never a vault"?

B2. **Pool catalogue for swap unwind** — for each archetype's hedge unwind path, what DEX pools are we depending on?
For `carry_staked_basis` (long staked SOL leg + short SOL perp hedge): which Solana pools are we routing jitoSOL/SOL +
mSOL/SOL + bSOL/SOL unwinds through (Raydium / Orca / Jupiter aggregator)? For `leveraged_funding_arb`: which EVM pools
for collateral rotation (USDC/USDT / WETH/ETH / WBTC/BTC)? Per pool: catalogued (instruments-service has the pool
definition), captured (MTDS has historical depth + reserves), live (RPC connection ready for live mid + depth)?

B3. **Pool depth + slippage simulation** — for the AMM slippage simulation in the matching engine + for the strategy's
own pre-trade slippage estimate:
  - Are we capturing **historical pool reserves** (Uniswap V3 sqrtPriceX96 + tick-liquidity bitmap, Curve `D` invariant
    state, Balancer pool weights, Solana CLMM tick state) per block (or per N blocks), so the matching engine can
    replay realistic depth at any historical timestamp?
  - Are we capturing **historical swap events** with `amountIn` / `amountOut` / `sqrtPriceAfter` (or equivalent) per
    block, so we can fit slippage curves per pool?
  - Live side: are we polling pool state at sufficient frequency that the strategy's pre-trade slippage estimate is
    accurate for the next-block execution? What's the staleness budget?
  - Per-protocol shape: Uniswap V3 + Solana CLMMs are tick-bucket-based; Curve is invariant-based; Balancer is weight-
    based; aggregators (Jupiter / 1inch) are routing-based. Is the slippage simulation model per-protocol-shape, or
    one-size-fits-all?

B4. **LST + LRT data types per venue** — for each LST + LRT we hold or could hold:
  - **Yield-rate stream**: per-epoch staking reward rate (Lido oracle pushes, Rocket Pool node operator distribution,
    Solana validator MEV + base reward share). Captured historically? Available live?
  - **Peg / exchange rate**: stETH/ETH peg snapshot per block (Curve stETH-ETH pool mid + Lido oracle + Chainlink LST
    feed). jitoSOL/SOL exchange rate per epoch (Jito on-chain SSOT). Captured per block + per epoch?
  - **Slashing risk + validator state**: validator slashing events (per beacon chain epoch on Ethereum; per validator
    epoch on Solana). Are we ingesting slashing telemetry?
  - **Restaking yield decomposition**: native staking yield + restaking AVS rewards (EigenLayer operator stake share +
    AVS-specific reward streams) + LRT-protocol fee + points / season rewards (Ether.fi / Renzo / Kelp). Are seasonal
    points-style rewards modeled, or only the on-chain yield?

B5. **Lending market data types per venue** — for each lending protocol we touch:
  - **Per-asset borrow rate + supply rate** (Aave V3 reserve data, Compound V3 cToken state, Solana lending pool
    interest accrual). Captured historically per block? Live? Are we capturing the rate's **components** (utilization
    rate + interest rate model parameters + reserve factor + per-asset cap) so we can simulate rate impact from our own
    borrow / supply, or only the realized rate?
  - **Lending indices** — Aave's `liquidityIndex` + `variableBorrowIndex` per reserve per block. Captured? These are
    needed to compute exact debt + collateral at any block precisely; without them we approximate.
  - **Per-asset collateral configuration** — LTV / liquidation threshold / liquidation bonus / can-be-collateral /
    can-be-borrowed / borrow cap / supply cap. These change via governance vote — captured historically with the
    governance proposal that changed them?
  - **Governance protocol data** — Aave / Compound / Spark governance proposals (Tally / Snapshot off-chain + on-chain
    Governor contract) — are we ingesting proposal state + execution events so we can know "rate model X changes at
    block Y" before / as it happens? Master plan + cards-on-the-table: this is for simulating "what if Aave passes a
    proposal that flips USDC borrow cap" type scenarios.

B6. **Perp + funding-rate data per perp venue** — across the 6 perp venues (Bybit / Deribit / Binance / OKX /
Hyperliquid / Aster) for `leveraged_funding_arb`:
  - **Funding rate stream per instrument**: realized 8h funding (or per-venue cadence) + predicted next funding +
    funding-rate-components (premium index + interest rate component + clamps). Captured per venue per
    instrument-bundle? Live polling cadence?
  - **Open interest + long/short ratio per instrument**: critical for funding-arb regime detection. Captured?
  - **Liquidation cascade events**: per-venue liquidation feed (Bybit + Binance publish, Deribit + OKX have feeds;
    Hyperliquid + Aster — confirm). Captured? Used in slippage simulation for stress scenarios?
  - **Mark-price + index-price per instrument** vs trade tape: needed because funding is computed off mark/index, not
    trade. Captured per venue at adequate frequency?
  - **Per-venue maintenance-margin tier table + initial-margin tier table**: needed for pre-flight margin headroom
    check. Catalogued + versioned (these change)?

### Block C — Chain-level infrastructure primitives

C1. **Chain coverage** — which chains are we on, and at what level of integration:
  - Ethereum mainnet + L2s (Arbitrum / Optimism / Base / Polygon zkEVM + PoS / Linea / Scroll / others?) — per chain:
    (a) RPC connection wired for read in MTDS, (b) RPC connection wired for write in execution-service, (c) historical
    block + tx + log capture in MTDS, (d) genesis date + chain-launch date in UAC `*_GENESIS_DATES`, (e) gas-fee data
    captured, (f) MEV protection RPC (Flashbots Protect / MEV-Share / etc.) wired.
  - Solana — same six-axis check. Master plan unbanned Pyth on 2026-05-06 specifically because Solana on-chain price
    feeds for `carry_staked_basis` LST yields are required. Is Solana fully wired (Hermes pull for batch + PythNet RPC
    for live), or partial?
  - Cosmos / Sei / Sui / Aptos / TON — out of scope, or partial?

C2. **Gas-fee data — historical + live** — for each chain in scope:
  - **Historical**: are we capturing per-block base-fee (EIP-1559 chains) + priority-fee distribution + per-tx gasUsed
    + gasPrice for at least the strategy lookback window (≥2 years per the master plan batch backtest requirement)?
    What's the storage shape (per-chain bucket / per-block parquet)?
  - **Live**: how is the strategy + execution-service consuming live gas estimates for pre-trade cost calc + tx
    submission? RPC `eth_feeHistory` polling, mempool gas oracle (Blocknative / Etherscan / Alchemy), or chain-native
    gas oracle? Is gas budget enforced at pre-flight (refuse to send a tx whose expected gas cost > X% of expected
    PnL)?
  - Solana specifically: priority fee landscape is qualitatively different (per-tx priority fee + compute unit price +
    Jito tip for inclusion). Are all three captured?

C3. **Oracle prices** — for each chain:
  - **Chainlink** — which feeds per chain? (BTC/USD + ETH/USD baseline; LST feeds — stETH/USD, rETH/USD, etc.) — are we
    capturing per-update tick (off-chain reporting plus on-chain commit) or just on-chain commits? Historical capture?
  - **Pyth (Solana via PythNet + Hermes pull on EVM via Wormhole)** — re-unbanned 2026-05-06 for Solana LST pricing.
    Wired in MTDS for batch (Hermes HTTPS pull)? Wired for live (PythNet RPC subscription)? Cross-chain Pyth pulls on
    EVM in scope, or strict Solana-only? Confirm boundary.
  - **Protocol-internal oracles** — Uniswap V3 TWAP, Curve EMA, Aave's price oracle (which is itself a Chainlink
    aggregator + fallback). Captured for backtest replay?
  - **Off-chain price feeds for cross-validation** — CoinGecko / CoinMarketCap / venue mid-price. Captured for arb-vs-
    oracle reconciliation?

C4. **MEV protection + private RPC hookups** — for each chain, do we have:
  - **Private mempool / MEV-protected submission RPC** wired in execution-service? (Flashbots Protect on Ethereum;
    Cow Swap / 1inch Fusion routing for swaps; Solana Jito bundle submission for prioritized + MEV-protected inclusion;
    chain-specific equivalents on Arbitrum / Base / Polygon.) Per chain: catalogued + connector exists + tested with at
    least one historical or testnet tx?
  - **MEV simulation** — when we backtest a swap or a liquidation, are we simulating realistic MEV impact (sandwich
    loss probability, JIT-LP impact, validator extraction)? Or is the matching engine assuming zero MEV?
  - **Fallback policy** — if private RPC is down, do we fall back to public mempool with a slippage budget tightening,
    or do we halt? Per-chain configurable?

C5. **Tenderly simulations** — execution-service uses Tenderly fork fixtures in integration tests per CLAUDE.md
"DeFi integration tests." Pre-flight production use:
  - Is Tenderly's bundle-simulation API (`/api/v1/account/{user}/project/{project}/simulate-bundle`) wired into
    execution-service's pre-flight check, so before we send a real tx we can dry-run the entire bundle (approve + swap
    + repay) on a forked-state VM and verify it doesn't revert?
  - Is the simulation gating live order placement (BLOCK if simulated bundle reverts), or advisory-only?
  - Cost / rate-limit budget — Tenderly is paid + rate-limited; what's the per-archetype simulation budget per day?
  - Beyond pre-flight: are we using Tenderly forks for **scenario simulation** (Block A1 of the risk question doc — "if
    BTC drops 20%, what's the liquidation cascade in our Aave position?") at production cadence (overnight cron), or
    only ad-hoc?

C6. **RPC provider redundancy** — per chain we use, do we have ≥2 independent RPC providers configured (Alchemy +
Infura + QuickNode + Ankr + Helius for Solana + project-specific public RPC) with automatic fallback? Single-provider-
single-point-of-failure is a master plan Group F risk.

### Block D — Simulation realism (the rate-impact + slippage modeling question)

D1. **AMM swap slippage modeling per pool-shape** (depends on B3) — given a target swap, the matching engine simulates
the realized fill at historical state. Per-pool-shape model:
  - Uniswap V3 / V4: tick-bucket integration (`getAmountsForLiquidity` per tick crossed by the swap)?
  - Curve stable / Curve crypto: `D` invariant + `gamma` for crypto pools?
  - Balancer weighted + boosted: weight-based bonding curve?
  - Solana CLMM (Raydium / Orca): equivalent tick-bucket?
  - Aggregator (Jupiter / 1inch): per-route decomposition + per-leg per-pool simulation?
  Are these modeled accurately, or do we have a simplified linear-impact model that breaks for >X% pool depth?

D2. **Lending rate impact from our own trade** (depends on B5) — when we supply $X USDC to Aave or borrow $Y USDC, the
utilization rate moves, which moves the borrow + supply rate. For a backtest replay, are we recomputing the
post-trade rate using the captured interest-rate-model parameters, or assuming zero impact?

D3. **Governance-protocol rate-impact simulation** (depends on B5 governance) — passing an Aave proposal to change
USDC borrow cap or interest rate model parameters changes the rate environment. For scenario simulation, can we model
"if Aave passes proposal X at time T, what's the impact on our position over the next 30 days"? This requires the
governance proposal text + execution payload + simulation harness to apply it on a Tenderly fork.

D4. **Staking + restaking yield-stream simulation** (depends on B4) — for `carry_staked_basis` PnL projection over a
forward window, we need a stochastic model of the staking yield (per-epoch reward variability + slashing tail risk +
restaking AVS reward variability + LRT-protocol-fee changes). Is there a yield-stream simulator that handles all of
the above, or do we treat staking yield as a constant baseline?

D5. **Cross-asset correlation + co-movement** for the hedge legs — `carry_staked_basis` shorts SOL perp against long
jitoSOL; the hedge ratio assumes ~1:1 SOL-equivalent exposure but jitoSOL/SOL drifts (peg behavior + accrual). Is the
hedge ratio dynamically adjusted on the catalog of LST/SOL exchange rates, or static?

D6. **Slashing tail-risk modeling** — slashing events are rare-but-catastrophic. Do we have a Monte Carlo model
calibrated against historical slashing rates per chain (Ethereum beacon chain has a long history; Solana validator
slashing has a different shape) feeding into the carry archetype's tail-risk allocation?

### Block E — Cross-asset-group catalogue gap-check (sports / prediction / CeFi / TradFi)

E1. **CeFi catalogue** — for each of the 4 CeFi perp venues (Bybit / Binance / OKX / Deribit) + spot venues + options
(Deribit BTC + ETH + SOL) + futures (CME via Databento ES.OPT 11-cluster + MBT + MET):
  - Is every instrument-day enumerable from instruments-service catalogue × dates cross-product?
  - Is every (venue, data_type, day) writing to the manifest with one of the 4 capture states?
  - Are zero-activity bars (D-category per writegate Phase 3.D.5) being emitted for tradeable-but-illiquid instruments,
    or are we still on the legacy NaN-placeholder path?
  - Per-venue: trades + ohlcv (1m / 5m / 15m / 1h / 1d) + funding (perp) + open-interest (perp) + book-snapshot at
    chosen depths + liquidations — which are captured + which are stubs?

E2. **TradFi catalogue** — for each TradFi root (ES / MBT / MET / VIX / ES.OPT / ETF list):
  - Per-root: trades + ohlcv multi-timeframe + options chain (ES.OPT 11 clusters) + greeks (computed downstream or
    sourced)? VIX 15m source layering (Barchart preload + Yahoo rolling 60d + the gap window) per the workspace SSOT
    — is this fully wired in MDPS reader + reconcile + downstream consumers?
  - Are all TradFi non-trading-day skips (`venue_trading_calendar` HOLIDAY / WEEKEND / PARTIAL_HALF_DAY) emitting the
    correct typed `EXPECTED_*` empty_confirmed reasons per the writegate-honest-coverage rule?

E3. **Sports catalogue** — across sources (api_football / footystats / understat / transfermarkt / soccer_football_
info / open_meteo / odds_api / mdps_odds_horizon_bucket):
  - Per-source coverage windows correctly clipped via `SOURCE_COVERAGE_START` + per-(source, data_type)
    `DATA_TYPE_COVERAGE_START` overrides?
  - Per-data-type `available_at` correctly stamped at write-time (lineups @ kickoff-60min, fixture_stats @
    match_end_time, etc.)? `LookaheadBiasError` raising loud at every features-sports compute?
  - Cluster validation for fixture-bundle data_types (ODDS_SNAPSHOT / ODDS_MOVEMENT / ARBITRAGE per-league-tier expected
    bookmaker sets) wired in `record_captured`?

E4. **Prediction catalogue** — Polymarket + Kalshi + others:
  - Canonical-question-group SSOT (BTC_UP_DOWN_HOURLY / BTC_UP_DOWN_DAILY / SPX_UP_DOWN_DAILY / ELECTION_*) populated
    in UAC, with market_id → canonical_question_group mapping?
  - All three lifecycle timestamps (`market_created_at` / `resolution_time` / `settlement_time`) captured per
    market_id in instruments-service? MTDS CLOB capture respecting lifecycle bounds (no ticks outside [created,
    settled])?
  - Cluster validation per (canonical_question_group, day) wired (HOURLY → 24 expected, DAILY → 1, etc.)?

E5. **Cross-asset-group manifest health** — what's the workspace-wide honest-coverage % today (per the formula
`captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)`) per asset_group? Is there a
deployment-ui surface showing per-asset-group coverage at a glance, or is it asset_group-by-asset_group manual probing?

## What "answered" looks like

- A canonical plan exists in `plans/active/` (or folds into `defi_master_2026_05_07.md` + `master_to_live_defi_2026_05_
  23.md` Group F items 17-20) enumerating the per-venue / per-asset / per-chain / per-data-type gap-fill priorities for
  the May-23 cutover, with explicit P0 / P1 / P2 tagging.
- Codex SSOT(s) describe:
  - The cross-asset-group venue + asset catalogue index (single entry-point per asset_group → registry of all
    catalogued venues + assets + instruments + chains).
  - The DeFi venue + protocol + pool + LST + lending + perp catalogue per chain (the "what we trade" SSOT).
  - The DeFi data-type taxonomy per venue (the "what we collect" SSOT) — funding rates / OI / liquidations / lending
    indices / governance / oracle prices / gas / pool depth / LST yields / restaking rewards / slashing events.
  - Chain-level infrastructure SSOT — per-chain RPC providers + private MEV RPC + Tenderly account + gas oracles +
    historical capture buckets.
  - Simulation realism SSOT — per-pool-shape AMM slippage models, lending rate impact model, governance simulation
    harness, staking + restaking yield simulator, slashing tail-risk model.
- Real-data evidence per axis:
  - For each catalogued DeFi protocol, at least one historical day of capture in MTDS + at least one live tick + at
    least one execution-service connector test (testnet acceptable for execution if mainnet risk too high).
  - For each chain in scope, gas-fee history ≥ 2 years captured + live gas estimate wired into pre-flight cost check +
    private MEV RPC connected (or explicit "no MEV protection on chain X" decision recorded).
  - For Solana specifically, full Pyth wiring (Hermes batch + PythNet live) + jitoSOL/mSOL/bSOL exchange-rate stream
    + Solana validator MEV + base reward share captured.
  - Tenderly bundle-simulation pre-flight check wired in execution-service `connect()` + verified to reject a
    deliberately-broken bundle (synthetic test).
- Service-readiness checklist: per master plan Group F items 17-20, all gates green for `carry_staked_basis` +
  `leveraged_funding_arb` against real wallet ≥ 7 continuous days.
- Cross-asset-group baseline closed: each of CeFi / TradFi / sports / prediction has a 1-page coverage-state summary in
  the deployment-ui (or codex doc + screenshot) showing manifest coverage % + known gaps + deferred-post-May-23 items.
- The "do we have it / are we capturing it / can we trade it / can we simulate it" four-axis matrix is filled per
  (asset_group, venue, instrument-type, data-type) — what's missing is either P0 fixed pre-cutover or P1+ deferred
  with named successor plan per the Plan Archival HARD RULE.

## Audit findings (audit pass 1 — 2026-05-09)

Audit ran across code + plans + codex + UAC registry + GCS state. Each sub-block answered where evidence is concrete;
flagged where evidence is missing or incomplete. Findings ordered by block.

### Block A — Cross-asset-group venue + asset catalogue baseline

**A1 — Canonical SSOT per asset_group:**
- **Primary SSOT**: `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:VENUES_BY_ASSET_GROUP`
  is the canonical "venues per asset_group" dict. 5 keys: `cefi / defi / tradfi / sports / prediction`.
- **Per-domain entry points** under `unified-api-contracts/unified_api_contracts/canonical/domain/`: `onchain/` (DeFi),
  `sports/`, `prediction/` AND `predictions/` (BOTH exist — drift), `derivatives/`, `position/`, `features/`,
  `execution/`, `market/`, `infrastructure/`, `reference/`. **No top-level `defi/` package** — DeFi types live under
  `domain/onchain/` (visible) plus `internal/domain/defi/` (parquet records / protocol SDKs / protocol data).
- **Secondary "first-3 base venues" SSOT**: `unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/venue_set_variants.py:88`
  `_BASE_VENUES_BY_ASSET_GROUP` uses LOWERCASE venue ids (`okx / binance / bybit` for cefi; `aave_v3 / uniswap_v3 /
  lido` for defi) vs the registry uses UPPERCASE (`BINANCE-SPOT / BYBIT / OKX`). **Case-folding drift** between the
  two SSOTs.
- **AMBIGUITY**: Two prediction modules — `canonical/domain/prediction/__init__.py` AND
  `canonical/domain/predictions/__init__.py`. Need operator triage on which is canonical (or whether one is the legacy
  pre-canonical-question-group module).

**A2 — Per-asset-group counts (concrete):**
- **CeFi**: `VENUES_BY_ASSET_GROUP["cefi"]` lists ~21 venues at line 17+ of `market_data_categories.py`:
  BINANCE-SPOT, BINANCE-FUTURES, BYBIT, OKX, DERIBIT, UPBIT, COINBASE, BITFINEX-SPOT, BITFINEX-FUTURES, BITGET-SPOT,
  BITGET-FUTURES, KRAKEN-SPOT, KRAKEN-FUTURES, **HYPERLIQUID, ASTER, PACIFICA-SOLANA, EXTENDED-STARKNET, LIGHTER-ZKSYNC,
  GMX, DRIFT** — note all on-chain perp/CLOB venues are classified under **cefi** axis (resolves the Cat-5 FLAG 1 from
  the Explore audit: Hyperliquid is **CeFi by venue-axis SSOT**, comment in source: "On-chain CLOBs (reclassified from
  DEFI — CLOB-style data like CeFi)").
- **TradFi**: `ES_OPTIONS_CLUSTERS` in `unified-api-contracts/unified_api_contracts/canonical/crosscutting/honest_coverage.py:49`
  is the bundled-cluster SSOT (11-cluster ES.OPT taxonomy). Roots include ES / MBT / MET / VIX (per CLAUDE.md VIX-15m
  layering rule) but no compact list of "all TradFi roots in scope" found at single SSOT — distributed across
  Databento converter (CME) + VIX layering rule + ETF list (not located).
- **Sports**: `unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py:66` `SOURCE_COVERAGE_START`
  enumerates 8 sources (api_football, footystats, understat, transfermarkt, soccer_football_info, open_meteo, odds_api,
  mdps_odds_horizon_bucket) with absolute coverage start dates. `DATA_TYPE_COVERAGE_START` adds 5 per-(source,
  data_type) overrides. Looks complete + canonical.
- **Prediction**: `unified-api-contracts/unified_api_contracts/canonical/domain/predictions/canonical_groups.py:CanonicalQuestionGroup`
  StrEnum has 10 entries: BTC_UP_DOWN_HOURLY, BTC_UP_DOWN_DAILY, ETH_UP_DOWN_HOURLY, ETH_UP_DOWN_DAILY, SPX_UP_DOWN_DAILY,
  FED_RATE_DECISION_PER_FOMC, CPI_PRINT_PER_MONTH, ELECTION_PRESIDENT_2028, OSCARS_BEST_PICTURE, OTHER. Per-day expected
  market_ids derived at runtime from `canonical/domain/predictions/lifecycle.py:expected_market_ids_for_canonical_group`.
- **DeFi**: Detail in Block B + the 6-category sub-audit below (Cat 1-6).

**A3 — Manifest health % per asset_group:**
- **No central honest-coverage % surface found.** Searched for `measure_honest_coverage*` script across workspace —
  zero hits. `deployment-api/tests/unit/test_capture_status_csv_bodies.py` + `test_failure_rate_by_dimension.py` +
  `test_chain_breakdown_shards_vs_dates.py` + `test_coverage_drift.py` confirm the underlying logic exists at the
  manifest-row level, but **no aggregate per-asset-group coverage % view** in deployment-ui.
- **GAP**: per-asset-group manifest health % is not surfaced. Per the writegate-honest-coverage SSOT, the formula
  `captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)` should resolve at every drilldown
  level — but no UI or CLI reports the aggregate. **P1 finding** for E5.

### Block B — DeFi-specific catalogue (extending the 6-category sub-audit; see end of this section)

**B2 — Pool catalogue for swap unwind:**
- **Solana pools (jitoSOL/SOL, mSOL/SOL, bSOL/SOL via Raydium/Orca/Jupiter)**: NO MTDS adapter found. Solana DEX
  capture is **not wired** — `solana-defi-central-element-323112` bucket exists but the path inside is unverified
  (couldn't list contents in this audit pass).
- **EVM swap pools (USDC/USDT, WETH/ETH, WBTC/BTC)**: Uniswap V2/V3/V4 + Curve adapters in
  `market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/{uniswapv2,uniswapv3,uniswapv4,curve}_adapter.py`
  capture pool state + swap events via TheGraph subgraph. **Balancer adapter NOT FOUND** despite UAC declaring it.
- **Live websocket capture**: `defi_live/thegraph_ws_adapter.py` provides streaming pool state.

**B3 — Pool depth + slippage capture:**
- **Per-protocol shape capture** (sqrtPriceX96 / tick bitmap / D invariant): `_defi_graph_models.py` is the shared
  TheGraph schema. Uniswap V3 captures sqrtPriceX96 fields. Curve captures pool state but `D`-invariant + `gamma` not
  directly visible in adapter — would need deeper inspection.
- **Live polling cadence**: not surveyed in this audit pass — flagged for follow-up.
- **Solana CLMM (Raydium/Orca tick state)**: NOT captured. Gap.

**B4 — LST + LRT data types per venue** (covers Cat 3 + Cat 4):
- **Yield rate stream**: `oracle_prices_handler.py` complements `lst_rates_handler` — first reads market oracle price
  (Chainlink + Pyth), second reads protocol exchange rate (`convertToAssets(1e18)` for ERC-4626 vaults; jitoSOL/mSOL
  per-epoch rates). Captures `staking_yields` + `lst_rates` data_types per UAC.
- **Slashing + restaking-yield decomposition**: NO slashing adapter found in MTDS / features-onchain / UAC. Restaking
  yield decomposition (native + AVS rewards + LRT-protocol fee + seasonal points) NOT modeled. **GAP — D6 + B4 last
  bullet are NOT BUILT.**
- **Solana LST coverage cadence**: per `defi_master_2026_05_07.md` audit "thin (~monthly cadence per jitoSOL oracle)" —
  Pyth Hermes wiring complete (coverage start 2023-10-01 per `_defi_oracle_coverage.py:36`) but **first historical
  backfill not yet run**. P0 deferred.

**B5 — Lending market data types per venue:**
- **Lending indices (`liquidityIndex` + `variableBorrowIndex`)**: SCHEMA-WIRED. `unified-api-contracts/unified_api_contracts/internal/domain/defi/protocol_sdks.py:167-168`
  declares the Aave V3 fields. `internal/index_utils.py` has the RAY-math helper. `internal/market_data/defi.py:56`
  has `utilization_rate` field. `internal/schemas/contracts.py:489` canonicalises Aave's `liquidityIndex /
  variableBorrowIndex` naming. **Capture is per-Aave-V3-Ethereum but currently silent-zero** per the Cat-2 audit
  (Bug 1: 0/343 shards captured at `mtds-lending-indices-20260507-140418`; deferred to writegate Phase 2.A).
- **Per-asset collateral configuration (LTV / liquidation threshold / etc.)**: `unified-api-contracts/unified_api_contracts/registry/defi_reserve_params.py`
  is the SSOT for Aave V3 + Compound V3 + Morpho Blue reserve parameters (curated). LST-as-collateral params at lines
  88-105 (WSTETH, WEETH, CBETH).
- **Governance protocol data (Aave / Compound / Spark proposals via Tally / Snapshot / Governor contract)**: NO
  CAPTURE ADAPTER. Searched MTDS + instruments-service + UAC for governance_proposal / aave_governance / tally /
  snapshot_off_chain / governor_contract — zero substantive hits. **GAP — governance simulation is NOT BUILT** (D3
  also empty). Cannot model "if Aave passes proposal X" scenarios at the data level today.

**B6 — Perp + funding-rate data per perp venue** (across the 6 perp venues per master plan):
- **Funding rate stream**: `market-tick-data-service/market_tick_data_service/cli/handlers/perp_funding_handler.py`
  exists. Per-venue adapters in `adapters/{binance,bybit,deribit,okx}.py` + `adapters/cefi/ccxt_adapter.py`
  + `adapters/onchain_perps/{aster_adapter,hyperliquid_adapter}.py`. **Wired for all 6 perp venues** (CeFi-classified
  per VENUES_BY_ASSET_GROUP A2). 8h funding cadence + premium-index components per venue.
- **Open interest + liquidations**: `cli/handlers/liquidation_events_handler.py` + `liquidations_handler.py` exist;
  per-venue adapters reference `open_interest` + `liquidation_event` shapes.
- **Mark / index price**: confirmed in `adapters/{bybit,okx,binance,deribit}.py` + `_deribit_models.py` +
  `onchain_perps/aster_adapter.py` + `tradfi/databento_cme_converter.py` for futures.
- **Per-venue maintenance-margin tier table + initial-margin tier table**: NOT FOUND at single SSOT — would need
  per-venue per-instrument-type margin schedules. **GAP — pre-flight margin headroom check needs this; flag for
  audit follow-up.**

### Block C — Chain-level infrastructure primitives

**C1 — Chain coverage:**
- **CHAIN_GENESIS_DATES SSOT** at `unified-api-contracts/unified_api_contracts/registry/chain_env.py:91` lists **22
  chains**: ETHEREUM (2015-07-30), ARBITRUM (2021-08-31), BASE (2023-08-09), OPTIMISM (2021-12-16), POLYGON
  (2020-05-30), AVALANCHE (2020-09-22), BSC (2020-08-29), LINEA (2023-07-11), SCROLL (2023-10-17), ZKSYNC (2023-03-24),
  CELO (2020-04-22), AURORA (2021-05-12), FANTOM (2019-12-28), MANTLE (2023-07-14), GNOSIS (2018-10-08), METIS
  (2021-11-19), MOONBEAM (2022-01-11), BLAST (2024-02-29), MODE (2024-01-12), **SOLANA (2020-03-16)**, BITCOIN
  (2009-01-03).
- **CHAIN_RPC_TEMPLATES SSOT** at `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py:12`
  + `_defi_chain_data.py:15`. Resolved per chain+env via `registry/chain_env.py:376:resolve_rpc_url`.
- **GAP**: `GAS_FEE_CHAIN_START_DATES` referenced in chain_env.py comment (Alchemy archival RPC coverage start) but
  not located in this audit — flag for follow-up. Distinct from genesis (lags by months).

**C2 — Gas-fee data:**
- **Historical bucket**: `gs://gas-fees-central-element-323112/` exists (canonical) + `gs://gas-fees-test-central-element-323112/`
  (test). Live verification of date-range coverage NOT done in this audit pass — would need to probe contents.
- **EVM gas client**: `market-tick-data-service/market_tick_data_service/market_interface/clients/gas_fee_client.py:316-336`
  captures per-block base-fee + priority-fee distribution via `eth_feeHistory` + per-tx gasUsed/gasPrice. Tested at
  `tests/unit/test_gas_fee_handler.py` + `tests/market_interface/unit/test_gas_price_adapter.py`. **Wired**.
- **Solana gas client**: `market-tick-data-service/market_tick_data_service/market_interface/clients/solana_gas_client.py:277-328`
  captures `priority_fees_lamports` distribution + averages. **Wired** — Solana priority-fee landscape (per-tx priority
  fee + compute-unit price) covered. **Jito tip for inclusion** NOT explicitly captured at this client (would need a
  Jito-specific stream).
- **Live gas adapter**: `market_interface/adapters/infra/gas_price_adapter.py` — used at runtime by execution-service
  + by `MEV-protection codex § 3 Gas Price Strategy` (cap `maxPriorityFeePerGas` at 3 gwei for non-urgent tx).
- **Pre-flight gas-budget enforcement**: not surveyed in this pass — flag for follow-up. Codex describes the cap but
  enforcement logic location not confirmed.
- **Per-chain historical backfill jobs**: `market-tick-data-service/logs/backfill-20260504-232911/collect-gas-fees_2021-01-01_2026-05-03.log`
  shows a 4+ year backfill ran on 2026-05-04. Coverage span is ≥ 2 years per master plan requirement.

**C3 — Oracle prices:**
- **Canonical handler**: `market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py`
  is the SSOT for both Chainlink (eth_call latestRoundData on Ethereum + Arbitrum/Base/Optimism/Polygon via Alchemy)
  AND Pyth Network (REST API at hermes.pyth.network/v2/updates/price/{publish_time}, free no-auth).
- **Pyth coverage start**: `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_oracle_coverage.py:36`
  declares `pyth_hermes: 2023-10-01` — historical Hermes archive starts then.
- **Solana wiring**: Pyth Hermes (HTTPS pull batch mode) is wired. **PythNet RPC live subscription** NOT visible from
  grep — potentially deferred.
- **ERC-4626 vault share prices**: `convertToAssets(1e18)` future-extensibility hook noted in handler docstring.
- **Protocol-internal oracles** (Uniswap V3 TWAP, Curve EMA, Aave price oracle): not captured separately — Aave's
  internal oracle IS Chainlink with fallback, so existing Chainlink capture covers it. Uniswap TWAP + Curve EMA NOT
  explicitly captured. **GAP**.
- **Off-chain feeds (CoinGecko / CMC / venue mid)**: see operator note below — operator prior is "drop unless arb-vs-
  oracle reconciliation specifically needs it." No CoinGecko adapter exists. Aligned with operator prior.

**C4 — MEV protection + private RPC:**
- **MEV submission router**: `execution-service/execution_service/v2/mev_router.py` declares `MevSubmissionPolicy`
  registry covering 4+ modes: PUBLIC_MEMPOOL, FLASHBOTS_PROTECT, MEV_BLOCKER, MANIFOLD. Bloxroute explicitly
  excluded per v2 architecture notes.
- **Per-mode providers**: `execution-service/execution_service/defi_execution/mev/{flashbots,private_mempool,protection}.py`.
  - **FlashbotsProvider** (`flashbots.py`): **STUBBED**. Module docstring line 1: "Relay integration is stubbed until
    a paid Flashbots subscription is available. Falls back to direct submission with logging." Code path returns a
    pending result with logger.info; no actual relay submit. **NOT OPERATIONALLY LIVE**.
  - **PrivateMempoolProvider** (`private_mempool.py`): supports `https://rpc.flashbots.net` + `https://rpc.mevblocker.io`
    via simple URL replacement. Auth-free. **Wired**. This is the simpler path that should be functional.
- **MEV simulation in matching engine**: `execution-service/execution_service/matching_engine/amm.py:764` reads
  `sqrt_price_x96` from pool data — slippage from depth modeled. **MEV impact (sandwich loss probability, JIT-LP
  impact)** NOT explicitly modeled in matching engine — assumes zero MEV beyond the slippage envelope. **GAP for D1
  realism**.
- **Fallback policy**: codex `04-architecture/mev-protection.md` § 2 states `fallback_to_public: false` (fail loud if
  private RPC unavailable). Configurable per chain via `chain_config.yaml`.
- **Per-chain MEV story** (codex):
  - Ethereum mainnet: Flashbots Protect + MEV Blocker (Manifold listed but not detailed).
  - Arbitrum: NO Flashbots — uses centralised sequencer RPC ("sequencer = centralized, no mempool MEV").
  - Base / Optimism: same — centralised sequencers, structural MEV reduction by L2 architecture.
  - Solana: **Jito bundle submission** mentioned in CLAUDE.md but **NOT in mev_router.py** policy registry. **GAP** —
    Solana MEV protection not wired into the MevSubmissionMode enum.

**C5 — Tenderly simulations:**
- **Provider**: `execution-service/execution_service/providers/tenderly.py:TenderlyExecutionProvider`. Uses Tenderly
  Virtual TestNet API (`/vnets`, NOT the deprecated Fork API) at `https://api.tenderly.co/api/v1`. Creates a fork per
  batch run; advance_time for batch replay; chain_id parameterised; fund_wallet supports USDC/USDT/DAI/WETH/WBTC.
- **Pre-flight simulation gating**: codex `04-architecture/mev-protection.md` § 5 "On-Chain Simulation (Pre-flight
  via Tenderly)": `tenderly_fork.simulate_transaction(tx_params)` returns reverted/revert_reason; if reverted, raises
  `DeFiError(DefiErrorCode.TX_REVERTED, ...)`. **Wired** — but the codex doesn't say whether this fires on every live
  order or only on high-value swaps. **Flag for follow-up**: confirm pre-flight gating coverage.
- **Bundle simulation API (multi-tx)**: `simulate-bundle` endpoint NOT confirmed at the provider — provider has
  `simulate_transaction` (single-tx). Bundle simulation (approve + swap + repay atomic) might use a different code
  path. **Flag for follow-up**.
- **Cost / rate-limit budget**: NOT documented in codex. Tenderly is paid + rate-limited; per-archetype daily budget
  not declared. **GAP — flag for operator decision**.
- **Scenario simulation at production cadence**: no overnight cron VM running Tenderly scenarios. The integration-
  test Tenderly fixtures (`execution-service/tests/defi_execution/integration/conftest.py`) exist but cron-driven
  scenario sims are NOT scheduled. **GAP — D1/D2 stress-scenario harness not built on Tenderly**.

**C6 — RPC provider redundancy:**
- **Not surveyed in this audit pass.** Need to read `execution_service/config/chain_config.yaml` + UCI config files.
  CLAUDE.md mentions Alchemy + Helius for Solana. Single-vs-redundant RPC per chain unconfirmed. **Flag for follow-up.**
- **Alchemy is the primary EVM provider** — confirmed via `gas_fee_client.py` Alchemy references + `oracle_prices_handler.py`
  Alchemy RPC. Whether a fallback Infura/QuickNode is configured is unclear from grep.

### Block D — Simulation realism

**D1 — AMM swap slippage modeling per pool-shape:**
- **Matching engine** at `execution-service/execution_service/matching_engine/`:
  - `engine.py:7-12` declares 5 matchers: L0Matcher (sports TOB), L1Matcher (TradFi via NautilusTrader), L2Matcher
    (CeFi via NautilusTrader), **AMMMatcher (DeFi swaps — constant product x*y=k)**, BenchmarkMatcher (LEND/STAKE/BORROW
    instant fill at benchmark).
  - `amm.py` (39 functions) — Uniswap V2 pool model + Uniswap V3 sqrtPriceX96 reads.
  - `hooks.py` (43 functions) — `CustomCurveHook` supports `constant_sum`, `constant_mean` (Balancer-style
    weight-based), `polynomial`, `logarithmic` curves. Hook framework intended to extend to V4 hooks.
- **Per-protocol shape coverage**:
  - Uniswap V2 / V3: ✅ explicit support (UniswapV2Pool + sqrtPriceX96 reads).
  - Uniswap V4 hooks: ⚠ framework exists (`hooks.py`) but full integration unclear.
  - Curve `D` invariant + `gamma` for crypto pools: ❌ NOT explicitly modeled — `constant_mean` in CustomCurveHook
    approximates but isn't Curve's exact math.
  - Balancer weighted/boosted: ⚠ `constant_mean` in CustomCurveHook approximates Balancer-V2-weighted; "boosted"
    pools (with linear pools as building blocks) NOT modeled.
  - Solana CLMM (Raydium/Orca): ❌ NOT modeled. Tick-bucket integration absent.
  - Aggregator (Jupiter/1inch) per-route decomposition: ❌ NOT modeled. Single-pool assumption.
- **Verdict — D1**: PARTIAL. Uniswap V2/V3 well-covered. Curve / Balancer / Solana CLMM / aggregators are gaps. May
  break for >X% pool depth on those protocols.

**D2 — Lending rate impact from own trade:**
- **Schema supports it**: `internal/domain/defi/protocol_data.py:59` `utilization_rate: Decimal`,
  `internal/domain/instruments/_instruments_parquet_schema.py:309` `optimal_utilization_rate` column.
- **Simulation harness recomputing post-trade rate**: NOT FOUND in matching_engine. The `BenchmarkMatcher` does
  "instant fill at benchmark" — assumes zero rate-impact from own trade.
- **Verdict — D2**: NOT BUILT. Strategies that supply/borrow large fractions of utilization (e.g. Aave Spark USDC
  market) will have backtests that over-estimate yield by ignoring own-trade rate compression.

**D3 — Governance-protocol rate-impact simulation:**
- **Zero results.** Not built. No governance_sim / proposal_simulation / tenderly_governance harness in the workspace.
- **Verdict — D3**: NOT BUILT. Aave/Compound/Spark proposal what-if scenarios cannot be modeled today.

**D4 — Staking + restaking yield-stream simulation:**
- **No yield_simulator / staking_yield_sim adapters found.**
- **Schema supports inputs**: `staking_yields` data_type captured per Cat-3 audit (Lido / Ether.fi / Jito / Marinade
  on Ethereum / Solana). But SIMULATION (stochastic forward yield model + slashing + restaking AVS variability) is
  NOT BUILT.
- **Verdict — D4**: NOT BUILT. `carry_staked_basis` PnL projection treats staking yield as constant baseline.

**D5 — Cross-asset correlation + co-movement (dynamic hedge ratio):**
- `strategy-service/strategy_service/engine/strategies/v2/stat_arb_pairs/pairs_fixed.py` has a FIXED-ratio pair-trade
  engine. `strategy-service/strategy_service/configs/defaults/default_basis_trade.yaml` likely has carry archetype
  config — not deeply read in this pass.
- **`carry_staked_basis` dynamic hedge adjustment**: NOT confirmed. The `pairs_fixed.py` shape suggests static; no
  visible `dynamic_hedge_ratio` / `peg_drift_adjustment` calculator in features-onchain or strategy-service.
- **Verdict — D5**: LIKELY STATIC; flag for follow-up — needs deeper read of carry archetype engine.

**D6 — Slashing tail-risk modeling:**
- **Zero results** for slashing / SLASHING / restaking_yield in MTDS + features-onchain + UAC outside of one mention
  in `external/defillama/mocks/protocols.yaml`.
- **Verdict — D6**: NOT BUILT. No slashing event capture, no MC tail-risk model, no calibration against historical
  slashing rates per chain.

### Block E — Cross-asset-group catalogue gap-check

**E1 — CeFi catalogue** (using `VENUES_BY_ASSET_GROUP["cefi"]`):
- ~21 venues listed (see A2). Per-venue capture wiring confirmed in MTDS adapters: trades + ohlcv + funding (perp) +
  OI + liquidations + mark/index price all WIRED for binance/bybit/okx/deribit/upbit/coinbase + Tier-3
  (bitfinex/bitget/kraken) via ccxt + on-chain CLOBs (hyperliquid/aster) + DEX perps (pacifica/extended/lighter/gmx/drift).
- **Cluster-level options bundling** (Deribit BTC/ETH/SOL options): per `honest_coverage.py` BUNDLED_DATA_TYPES path,
  options chains are bundle-validated.
- **Zero-activity bars (D-category)**: per CLAUDE.md writegate Phase 3.D.5 Wave 3.M is PENDING — adapter audit not yet
  complete; some venues may still emit legacy NaN placeholders. **Flag** — cross-reference with writegate plan.
- **GAP**: per-venue maintenance-margin / initial-margin tier tables NOT located at single SSOT (B6 last bullet).

**E2 — TradFi catalogue:**
- **Roots**: ES / MBT / MET / VIX / ES.OPT — confirmed in `honest_coverage.py:ES_OPTIONS_CLUSTERS` for the 11-cluster
  options bundling.
- **VIX 15m source layering**: per CLAUDE.md SSOT (Barchart preload 2020-01-02 → 2025-11-12 + Yahoo rolling 60d + the
  honest gap window 2025-11-13 → today−60d). Wired in MTDS `umi_tick_provider.py` route + `is_vix_15m_gap_date()`
  helper.
- **TradFi non-trading-day skips**: `venue_trading_calendar` HOLIDAY/WEEKEND/PARTIAL_HALF_DAY emitting typed
  `EXPECTED_*` empty_confirmed reasons — per writegate `EMPTY_CONFIRMED_REASONS` + the 2026-05-08 codification.
  **Likely WIRED** but per-venue verification not done in this pass.
- **ETF list**: NOT located at single SSOT. Flag for follow-up.

**E3 — Sports catalogue:**
- **SOURCE_COVERAGE_START + DATA_TYPE_COVERAGE_START**: complete in `domain/sports/league_data.py` (see A2).
- **Per-data-type `available_at`**: per CLAUDE.md SSOT (lineups @ kickoff−60min, fixture_stats @ match_end_time, etc.).
  `LookaheadBiasError` raise-loud at every features-sports compute is the contract; verification per-calculator NOT
  done in this pass.
- **Cluster validation for fixture-bundle data_types** (ODDS_SNAPSHOT / ODDS_MOVEMENT / ARBITRAGE per-league-tier
  expected bookmaker sets): wired in `record_captured` per CLAUDE.md "Cluster validation MANDATORY" rule.
- **Looks complete and canonical**.

**E4 — Prediction catalogue:**
- **Canonical-question-group SSOT**: 10 entries in `CanonicalQuestionGroup` enum (BTC/ETH/SPX up-down hourly+daily,
  FED/CPI cadenced, ELECTION_2028, OSCARS, OTHER). Per-group min row counts in `PREDICTION_GROUPS` dict.
- **3-lifecycle timestamps** (`market_created_at` / `resolution_time` / `settlement_time`) in instruments-service: per
  the predictions plan SSOT path, this lives in `canonical/domain/predictions/lifecycle.py:expected_market_ids_for_canonical_group`.
  Not deeply verified in this pass — flag for follow-up.
- **Cluster validation per (canonical_question_group, day)**: per CLAUDE.md "Cluster validation MANDATORY" + the
  predictions plan, wired via `record_captured` for prediction bundled data types.

**E5 — Cross-asset-group manifest health:**
- **No central honest-coverage % surface exists in deployment-ui** (see A3). Per-(asset_group, venue, data_type) coverage
  is computable from manifest reads but no aggregate report.
- **Recommendation**: build a `measure_honest_coverage.py` script (per CLAUDE.md memory: "operator-run measure-honest-
  coverage.py on same-region GCE VM" referenced 2026-05-07 evening) and surface results in deployment-ui per writegate
  Phase 4. Currently it's a **manual asset-group-by-asset-group probe** task. **P1 finding**.

### Codex doc inventory + ambiguity

**DeFi-specific codex docs found**:
- `codex/02-data/defi-data-types-catalog.md` — SSOT for 14 MTDS DeFi data types + GCS path convention.
  `gs://{tick-defi-bucket}/raw_tick_data/by_date/day={date}/category=defi/venue={VENUE}-{CHAIN}/instrument_type={type}/data_type={data_type}/ticks.parquet`.
  Categories: lending / DEX / staking / bridging / governance / MEV. Last updated 2026-04-24.
- `codex/02-data/instrument-pipeline-defi.md` — instrument lifecycle + LST_TOKEN_TO_PROTOCOL_ASSET SSOT.
- `codex/04-architecture/{tenderly-execution-provider, mev-protection, defi-risk-monitoring, defi-phase3-infrastructure,
  defi-execution-overview}.md`.
- `codex/04-architecture/flash-loan-receiver.md` (Aave V3 receiver contract).
- `codex/07-security/mev-protection.md` — **POSSIBLE DUPLICATE/DRIFT** with `04-architecture/mev-protection.md`. Need
  to verify whether they describe same content from different angles or have drifted. **AMBIGUITY flag**.
- `codex/09-strategy/architecture-v2/cross-cutting/{mev-protection, restaking-reward-economics}.md` (likely strategy-
  side narrative; ambiguity vs 04-architecture/ unclear).
- `codex/09-strategy/architecture-v2/archetypes/{yield-rotation-lending, defi-lp-concentrated, defi-lp-pool}.md` —
  archetype docs. `carry-staked-basis.md` referenced in audit but path unconfirmed in this pass.
- `codex/15-runbooks/alerting/{kill_switch_defi_liquidation_risk, defi_aave_utilization_spike, defi_feature_stale,
  defi_funding_rate_flip, defi_weeth_depeg, defi_health_factor_critical}.md` — alerting runbooks (good coverage).
- `codex/11-project-management/defi-bucket-sizes-2026-05-07.md` (recent; likely capacity-planning).
- **Archived (out of scope)**: `codex/09-strategy/_archived_pre_v2/defi/{multi-chain-lending-yield, btc-lending-yield,
  aave-lending, sol-lending-yield}.md`.

**Ambiguity findings**:
- **`07-security/mev-protection.md` vs `04-architecture/mev-protection.md` vs `09-strategy/architecture-v2/cross-cutting/mev-protection.md`**:
  three docs with overlapping titles. Risk of drift — pick one canonical, redirect/dedupe the others.
- **`canonical/domain/prediction/` AND `canonical/domain/predictions/` (UAC, A1)**: dual-module ambiguity.

**Coverage gaps (codex says nothing about):**
- **Per-pool-shape AMM slippage simulation** (D1) — no codex doc walking through Uniswap V3 tick-bucket vs Curve D vs
  Balancer weighted vs Solana CLMM math.
- **Per-chain RPC provider redundancy** (C6) — no SSOT codex doc listing primary + fallback per chain.
- **Slashing tail-risk + staking yield simulation** (D4 + D6) — no architecture doc.
- **Governance simulation harness** (D3) — no architecture doc.
- **Per-asset-group manifest coverage % surface** (E5) — no doc on the measurement script + UI surface contract.

### Six-category protocol audit (from explore agent — 2026-05-09)

A separate explore agent ran a comprehensive audit across the 6 DeFi-primitive categories the operator listed (vaults
/ lending / LSTs / restaking-LRTs / perp DEXes / spot-swap DEXes). Full report below — file:line citations preserved.

#### Category 1 — Vaults / Yield Aggregators
- **Mentioned**: Yearn, Convex, Beefy, Pendle, Idle (CLAUDE.md + presentations only). Balancer also operates as a
  yield-LP-aggregator but is classified under DEX SSOT.
- **SSOT**: NONE. Yearn/Convex/Beefy/Pendle/Idle have ZERO UAC entries.
- **Catalogue / capture / connector**: ZERO. No instruments-service adapter, no MTDS adapter, no execution connector
  for any vault protocol.
- **Orphan finding**: `features-onchain-service/app/calculators/vault_share_price_apy_calculator.py` exists but has no
  upstream MTDS data source — **dead code OR missing upstream**. Either delete or wire upstream.
- **Verdict**: **P0-or-deferred decision required** — if vaults are May-23 scope, completely unimplemented; if not,
  CLAUDE.md should explicitly remove them from scope.

#### Category 2 — Lending Protocols
- **UAC SSOTs**: `defi_venue_capabilities.py:40-115` (Aave V3 / Compound V3 / Morpho / Morpho Blue / Fluid / Spark on
  EVM; Kamino on Solana). Reserve params at `defi_reserve_params.py:352-390`.
- **Catalogue**: Aave V3 Ethereum (10 reserves × A_TOKEN+DEBT_TOKEN = 20 instruments). Compound V3 Ethereum, Morpho
  Ethereum, Morpho Blue (curated), Kamino (Solana), Fluid (limited). **Spark and Radiant gaps**: Radiant has an
  instruments-service adapter but NO UAC entry (orphan); Spark in UAC but no instruments-service adapter (ghost).
- **Capture**: Aave V3 Ethereum + Polygon + Arbitrum (3 of 10 chains); Compound/Morpho/Morpho Blue/Fluid/Spark zero
  MTDS adapters. **CRITICAL BUG**: `mtds-lending-indices-20260507-140418` reported AAVE V3 ETHEREUM 0/343 shards
  captured (silent-zero per writegate Phase 2.A; deferred P0 fix-first).
- **Connectors**: Aave V3 (full flash-loan + borrow/lend/repay; Sepolia testnet validated); Morpho (lending connector
  exists; testnet pending); Compound/Spark/Radiant/Fluid/Kamino zero connectors.
- **Multi-chain gap**: Aave V3 declared on 9 non-Ethereum chains (Arbitrum, Avalanche, Base, BSC, Linea, Optimism,
  Polygon, Scroll, ZkSync) but ZERO instruments + ZERO MTDS adapters + ZERO connectors per non-Ethereum chain. **P0
  blocker if any archetype needs cross-chain Aave**.

#### Category 3 — LSTs (Liquid Staking Tokens)
- **UAC SSOTs**: `defi_venue_capabilities.py:138-154` (Lido, Ether.fi, Ethena on Ethereum; Jito, Marinade on Solana).
  LST-as-collateral params at `defi_reserve_params.py:88-105`.
- **Catalogue**: Lido (stETH/wstETH) + Ether.fi (eETH/weETH) on Ethereum. **Solana LSTs (jitoSOL/mSOL/bSOL) ZERO
  instruments-service catalog despite being CRITICAL for `carry_staked_basis`**.
- **Capture**: Lido + Ether.fi on Ethereum (oracle + protocol exchange rate); Jito + Marinade on Solana via
  `lst_adapters.py` (Pyth-oracle-based, unbanned 2026-05-06). Ethena: NO MTDS live capture (DefiLlama offline only).
  Solana cadence "thin (~monthly)" pending first historical backfill.
- **Connectors**: Lido + Ether.fi on Ethereum (Holesky testnet ready). Jito/Marinade/Ethena/Rocket Pool/Solblaze: zero
  connectors.
- **Orphans**: **Rocket Pool (rETH)** + **Solblaze (bSOL)** in CLAUDE.md but NOT in UAC + zero instruments + zero MTDS
  + zero connectors. If in scope, P0-blocking; if not, remove from CLAUDE.md.
- **Missing SSOT**: `LST_TOKEN_TO_PROTOCOL_ASSET` cited as `defi_master_2026_05_07.md` Phase 9.1A (commit 3613e90)
  but verification didn't confirm it's in current codebase. **Flag**.

#### Category 4 — Restaking + LRTs
- **UAC SSOTs**: `defi_venue_capabilities.py:151-154` — EigenLayer ONLY. Symbiotic / Karak / Renzo / KelpDAO / Puffer
  / Jito-restaking all in CLAUDE.md mentions but NO UAC entry.
- **Catalogue / capture / connector**: ZERO across all protocols. UAC declares `eigenlayer_rewards` data_type but no
  MTDS adapter implements it.
- **EigenLayer connector status**: `cicd_code_rollout_master_2026_03_13.plan.md:51` cites "EigenLayerConnector with 6
  operations + 25 tests" as completion note — but **NOT FOUND in current execution-service/venues/ or
  defi_execution/protocols/**. **AMBIGUOUS** — dead code, different branch, or not actually shipped?
- **defi_master deferred**: ZERO mention of restaking in `defi_master_2026_05_07.md` 2026-05-23 cutover scope.
  `carry_staked_basis` uses LSTs (vanilla staking) only; restaking is **post-May-23 deferred** by absence.

#### Category 5 — Perp DEXes
- **FLAG 1 RESOLVED** by `VENUES_BY_ASSET_GROUP["cefi"]`: HYPERLIQUID, ASTER, PACIFICA-SOLANA, EXTENDED-STARKNET,
  LIGHTER-ZKSYNC, GMX, DRIFT all classified under **cefi** axis (not defi). Comment in source: "On-chain CLOBs
  (reclassified from DEFI - CLOB-style data like CeFi)". The "6 perp venues" in master plan = 4 traditional CeFi
  (Bybit, Deribit, Binance, OKX) + 2 on-chain CLOBs (Hyperliquid, Aster). All cefi-axis.
- **GMX / DRIFT in UAC `defi_venue_capabilities.py:130-131`**: GMX captured (perp_funding, liquidations, oracle_prices
  for Arbitrum + Avalanche). But ALSO listed under `VENUES_BY_ASSET_GROUP["cefi"]`. **DUAL-CLASSIFICATION ambiguity
  remains** for GMX + DRIFT — both UAC and venue-set claim them.
- **Capture**: per-venue funding + OI + liquidations + mark/index wired across all 6 (B6 above). **Lighter / Pacifica
  / Extended OHLCV partial** — code shipped, contract-address + ABI-parsing pending, backfill not yet run.
- **Connectors**: Hyperliquid + Aster via execution-service. Aster connector "incomplete" per Cat-5 sub-audit (only
  error-handling code, not full trade execution). dYdX V4 / Vertex / Drift / Jupiter perps zero connectors.

#### Category 6 — Spot / Swap DEXes (AMM + CLMM)
- **UAC SSOTs**: `defi_venue_capabilities.py:18-128` lists 16 EVM DEXes + 2 Solana DEXes (Uniswap V2/V3/V4, Curve,
  Balancer, Sushi V2/V3, PancakeSwap V3, Camelot V3, Aerodromeq V3, Velodrome V2, TraderJoe V2 + Raydium, Orca).
  Aggregators (1inch, 0x, ParaSwap, Jupiter agg) NOT in UAC.
- **Catalogue**: Uniswap V2/V3/V4 + Curve only. **Balancer, Sushi, PancakeSwap, Camelot, Aerodromeq, Velodrome,
  TraderJoe, Raydium, Orca all ZERO instruments-service adapters** despite UAC declaring them live.
- **Capture**: Uniswap V2/V3 + Curve only via TheGraph subgraphs. Other 11 EVM + 2 Solana DEXes: zero MTDS adapters.
- **Connectors**: Uniswap V3 ONLY (full SwapRouter02 + ERC20-approve + exactInputSingle, Sepolia testnet validated).
  All others read-only at best.
- **Catastrophic gap**: 11 UAC-declared EVM DEXes + 2 Solana DEXes have ZERO implementation. If `carry_staked_basis`
  or other archetypes need multi-leg rebalancing across Balancer/Sushi/PancakeSwap, **cannot execute**. Solana DEX
  swaps for jitoSOL/mSOL/bSOL unwind: **cannot execute**.

### Critical blockers consolidated for 2026-05-23 cutover

In approximate priority order (P0 = blocking; P1 = degrades cutover quality; P2 = post-May-23 deferred):

| # | Finding | Severity | Successor |
| - | ------- | -------- | --------- |
| 1 | **Aave V3 Ethereum 0/343 shards silent-zero capture** | P0 | writegate Phase 2.A |
| 2 | **Solana LST instruments + execution connectors** (jitoSOL/mSOL/bSOL: zero instruments-service catalog + zero connectors) | P0 | needs new plan (defi_master Phase 9 extension) |
| 3 | **Pyth historical backfill not yet run** for Solana LST yields (Hermes wired since 2023-10-01 coverage, first run pending) | P0 | needs scheduled VM launch |
| 4 | **Lighter / Pacifica / Extended DEX-perp backfill not run** (OHLCV code shipped, contract-address + ABI parsing pending) | P0 | cefi_venue_universe_expansion plan |
| 5 | **Aster connector incomplete** (only error-handling code, no trade execution) | P0 | execution-service own plan |
| 6 | **Flashbots relay STUBBED** at execution-service `defi_execution/mev/flashbots.py` line 1 ("falls back to direct submission with logging until paid Flashbots subscription"). PrivateMempool path is wired (rpc.flashbots.net) which covers most use cases but Flashbots-bundle path is dead | P0 if archetype requires bundle-submission; P1 otherwise | new MEV-relay-paid-tier plan or accept private-mempool-only |
| 7 | **Solana MEV protection (Jito bundle submission) NOT in mev_router.py** policy registry | P0 if Solana-leg requires MEV protection; P1 otherwise | new Solana-MEV plan |
| 8 | **EigenLayer connector status ambiguous** (claimed shipped 2026-03-13 but not in current execution-service code) | P1 (not in May-23 scope per defi_master); needs verification anyway | follow-up audit |
| 9 | **Multi-chain Aave V3** (9 non-Ethereum chains declared in UAC but zero instruments + zero MTDS + zero connectors) | P0 if cross-chain leg required; P1 otherwise | new multi-chain Aave plan |
| 10 | **Catastrophic DEX gap** (11 EVM + 2 Solana DEXes in UAC but zero implementation) | P1 unless multi-leg rebalancing required for May-23 archetype; P2 otherwise | post-May-23 DEX rollout plan |
| 11 | **GMX / DRIFT dual-classification ambiguity** (in both UAC `defi_venue_capabilities.py` AND `VENUES_BY_ASSET_GROUP["cefi"]`) | P1 SSOT-cleanup | classification-decision sweep |
| 12 | **Vault catalogue complete absence** (Yearn / Convex / Beefy / Pendle / Idle in CLAUDE.md but zero workspace presence; orphan `vault_share_price_apy_calculator.py`) | P1 scope decision | remove from CLAUDE.md OR build |
| 13 | **Slashing event capture + tail-risk MC + restaking yield decomposition** (D4 + D6 + B4 last bullet) | P2 deferred | post-May-23 |
| 14 | **Governance proposal capture + governance-sim harness** (B5 + D3) | P2 deferred | post-May-23 |
| 15 | **Lending rate-impact-from-own-trade simulation** (D2) | P2 deferred (acceptable approximation for small fractions of utilization) | post-May-23 |
| 16 | **AMM slippage simulation gaps** (Curve D-invariant exact, Balancer boosted, Solana CLMM, aggregator routing) | P2 unless archetype size triggers bad approximation | post-May-23 |
| 17 | **Per-asset-group manifest coverage % UI surface** (E5) | P1 operability | writegate Phase 4 / new measurement script |
| 18 | **Honest-coverage measurement script** (`measure_honest_coverage.py` referenced in memory but not located) | P1 | same as #17 |
| 19 | **Codex doc duplication / drift** (`07-security/mev-protection.md` vs `04-architecture/mev-protection.md` vs `09-strategy/architecture-v2/cross-cutting/mev-protection.md`) | P2 codex hygiene | codex SSOT consolidation pass |
| 20 | **`canonical/domain/prediction/` + `canonical/domain/predictions/` dual modules** | P2 SSOT cleanup | UAC consolidation |
| 21 | **Per-venue maintenance-margin / initial-margin tier tables** (B6 last bullet — needed for pre-flight margin check) | P1 if pre-flight margin enforcement required for May-23 | margin-tier SSOT plan |
| 22 | **CoinGecko / off-chain price feeds** (per operator note: oracles are sufficient) | RESOLVED — out of scope unless arb-vs-oracle reconciliation specifically needs it | n/a |

### Items NOT verified in this audit pass (flagged for follow-up)

- **C6** — RPC provider redundancy per chain (need to read `chain_config.yaml` + UCI configs).
- **C5** — Tenderly bundle-simulation API (`simulate-bundle` for atomic approve+swap+repay) vs single-tx
  `simulate_transaction` distinction.
- **C5** — Tenderly per-archetype daily simulation budget + rate limit.
- **C2** — pre-flight gas-budget enforcement (codex describes 3-gwei priority cap; enforcement code path location not
  confirmed).
- **D5** — `carry_staked_basis` dynamic vs static hedge-ratio adjustment (need deeper read of carry archetype engine).
- **E1** — per-CeFi-venue confirmation that zero-activity bars (writegate Phase 3.D.5 D-category) are emitted (not legacy
  NaN placeholders) — depends on Wave 3.M adapter audit.
- **E2** — TradFi ETF list at single SSOT.
- **GAS_FEE_CHAIN_START_DATES** referenced in chain_env.py comment but not located — Alchemy archival RPC coverage
  start dates per chain.
- **`LST_TOKEN_TO_PROTOCOL_ASSET` SSOT** at `canonical/domain/predictions/lifecycle.py` (predictions plan Phase 9.1A) —
  cited as commit 3613e90 but presence in current code unconfirmed.
- **Solana DEX bucket** `gs://solana-defi-central-element-323112/` — exists but contents not probed.

## Operator notes / answers

**On C3 — off-chain price feeds (CoinGecko / CMC) — operator prior 2026-05-09:**
"i dunno why we need that if we have oracle". Recorded prior: Chainlink (EVM) + Pyth Hermes (Solana / cross-chain) +
on-tape venue mids are the canonical price surface. CoinGecko / CMC are NOT captured + NOT in plan. The narrow case
where an off-chain feed adds value is **arb-vs-oracle reconciliation** (catching a stale or manipulated oracle by
cross-checking against an independent off-chain mid). Decision: defer to "arb-vs-oracle reconciliation" sub-question
in any spawned plan — if reconciliation is needed, source is operator-decision-time (CoinGecko / CMC API / venue mid
average); if not, off-chain feeds are out of scope.

**On A1 — UAC dual-prediction modules** (`canonical/domain/prediction/` + `canonical/domain/predictions/`) and Cat-2
**Radiant orphan adapter** (instruments-service has it, UAC doesn't) — both flagged for SSOT-cleanup pass; need
operator triage on which is canonical.

**On Cat-1 vaults** (Yearn / Convex / Beefy / Pendle / Idle) — operator scope decision needed: in scope for May-23 or
post-May-23? CLAUDE.md mentions them but no implementation exists. If post-May-23, recommend removing from CLAUDE.md to
reduce scope confusion.

**On Cat-3 orphan LSTs** (Rocket Pool / Solblaze) — same operator scope decision: in scope for May-23 or remove from
CLAUDE.md.

## Iteration log

| Date | Author | Change |
| ---- | ------ | ------ |
| 2026-05-08 | ikenna + main agent | Initial draft created |
| 2026-05-09 | main agent (audit pass 1) | 6-category Explore audit (vaults / lending / LSTs / restaking-LRTs / perp DEXes / DEXes) + Block A/B-extended/C/D/E findings folded in. CoinGecko prior recorded. 22-blocker priority list drafted. Items pending follow-up enumerated. |

## Plan-shape decisions (filled before plan extraction)

- **Plan name + path**: TBD — likely splits into 3 plans:
  - `plans/active/defi_catalogue_chain_primitives_<date>.md` (DeFi venue + chain + Tenderly + MEV — folds into
    `defi_master_2026_05_07.md`)
  - `plans/active/defi_simulation_realism_<date>.md` (AMM slippage models + lending rate impact + governance sim +
    staking yield sim — composes with execution-service matching engine)
  - `plans/active/cross_asset_group_catalogue_audit_<date>.md` (CeFi / TradFi / sports / prediction baseline summary +
    deployment-ui catalogue surface — composes with deployment-api + UI)
- **Plan type**: mixed (code + infra + data capture + simulation modeling + business decisions on what to defer)
- **Owner side**: TBD — likely ikenna for cross-cutting design + simulation harness shape + deferred-vs-cutover
  decisions; harsh for per-protocol connector implementation + per-chain RPC + per-pool slippage-model implementation
- **Codex SSOTs touched**: TBD — likely:
  - NEW: `codex/02-data/defi-venue-protocol-catalogue.md` (per-chain × per-protocol × per-asset matrix)
  - NEW: `codex/02-data/defi-data-type-taxonomy.md` (per-venue data-type matrix; funding / OI / lending indices /
    governance / oracle / gas / LST yield / restaking / slashing)
  - NEW: `codex/05-infrastructure/chain-rpc-mev-tenderly.md` (per-chain RPC providers + MEV-protected RPCs + Tenderly
    integration + gas oracles)
  - NEW: `codex/04-architecture/amm-slippage-simulation.md` (per-pool-shape models + lending rate impact + governance
    sim + staking yield sim + slashing tail-risk)
  - UPDATE: `codex/04-architecture/interface-credential-convention.md` (any new connectors that ship)
  - UPDATE: `codex/02-data/availability-manifest-and-data-status.md` (any new data_types that get added)
  - UPDATE: `defi_master_2026_05_07.md` body (gap-fill priorities + per-archetype readiness matrix)
  - UPDATE: `master_to_live_defi_2026_05_23.md` Group F item rows (capture status + simulation readiness)
- **Cross-plan dependencies**:
  - Composes with `risk_simulations_limits_alerting_2026_05_08.md` (sibling question doc) — simulation harness + chain
    primitives feed risk simulations; pre-flight risk consumes Tenderly bundle simulation output.
  - Composes with `client_reporting_pnl_attribution_2026_05_08.md` (sibling) — PnL attribution decomposition needs
    per-archetype yield + funding + slippage + gas + MEV impact components from the simulation primitives.
  - Composes with `defi_master_2026_05_07.md` + `master_to_live_defi_2026_05_23.md` Group F items 17-20.
  - Composes with `cefi_master_2026_05_07.md` + `tradfi_master_2026_05_07.md` + `sports_master_2026_05_07.md` +
    `predictions_master_2026_05_07.md` for Block E baseline.
  - Composes with `live_pipeline_mtds_mdps_features_2026_05_08.md` + `pipeline_mode_partition_migration_2026_05_08.md`
    for the live-side capture wiring of any new data_types.
- **Estimated scope**: TBD — audit pass first to scope; expect ≥ 3 plans × 5-10 AI-day each for a serious gap-fill
  before May-23.

## Plan extraction record

(Empty — fills when the plan ships.)
