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

## Audit findings (to be filled by audit pass)

For each sub-question in Blocks A-E, fill:

- **Code state**: instruments-service registries (per-asset_group catalogue files), MTDS adapters per venue (per
  data_type capture), execution-service connectors per protocol (DeFi connectors per chain × per protocol; CeFi
  connectors per venue), UAC SSOT files (`SOURCE_COVERAGE_START`, `*_GENESIS_DATES`, `CHAIN_RPC_TEMPLATES`,
  `BUNDLED_DATA_TYPES`, etc.), feature service consumers — file:line citations.
- **Data state**: manifest coverage per (asset_group, venue, data_type) against expected universe; sample parquets
  populated (not 1440-NaN placeholders); coverage % per asset_group; on-disk evidence per chain (historical block /
  gas / oracle / pool-state / governance buckets).
- **Run state**: when did each capture path last write a non-empty parquet to production buckets; have any DeFi
  execution-service connectors placed a real tx (testnet count / mainnet count); has Tenderly bundle-simulation ever
  blocked a real order; has the matching engine ever simulated a multi-hop swap with live pool state.
- **Codex state**: per-asset-group catalogue docs + per-chain RPC docs + Tenderly integration doc + MEV protection
  doc — exist? Drift vs current code? Gaps?
- **Gap analysis**: per the four-axis matrix, what's missing per cell; concrete blockers for May-23 cutover; per-chain
  + per-protocol + per-archetype delta; what's deferred-post-May-23 with named successor plan.

## Operator notes / answers

(Empty — to be filled during iteration.)

## Iteration log

| Date | Author | Change |
| ---- | ------ | ------ |
| 2026-05-08 | ikenna + main agent | Initial draft created |

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
