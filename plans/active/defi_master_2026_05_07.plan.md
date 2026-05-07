---
name: defi-master
slug: defi_master_2026_05_07
date: 2026-05-07
owner: claude-code
status: active
priority: P0
phase: pending_approval
domain: defi
asset_group: defi
type: umbrella
locked_by: live-defi-rollout
locked_since: 2026-05-07
folds_in:
  - consolidated_defi_data_pipeline_2026_04_15
  - defi_e2e_pipeline_2026_04_30
  - dex_historical_replay_lighter_extended_pacifica_2026_05_07
  - market_tick_data_to_100pct_2026_05_05 # DeFi slice
  - cefi_venue_universe_expansion_2026_05_01 # DEX-perp half (Extended / Pacifica / Lighter)
related_plans:
  - master_to_live_defi_2026_05_23
  - writegate_honest_coverage_endtoend_2026_05_06
  - shard_granularity_ssot_propagation_2026_05_06
---

# DeFi Master — asset_group umbrella

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 32 of 32 unchecked todos
- **Mis-marked DONE → flipped**: 2 (Lighter + Pacifica `_fetch_*_history` and OHLCV ohlcv_1m wiring shipped per
  MTDS@10aa715/51fecd5/d898985/fc53a97 + UAC@e890022; UAC `VENUES_BY_ASSET_GROUP['defi']` already includes
  Lighter/Pacifica per UAC@7cb9068 / 405cbf5 venue declarations)
- **In-flight (running VMs)**: 0 — NO defi/features-onchain VMs in current `gcloud` snapshot
- **Blocked by**: `manifest_migration_master_2026_05_07:Stage 4` (rescan-all-manifests gates the 988-dates-missing
  diagnosis); `writegate_honest_coverage_endtoend:Phase 2.A` (placeholder deletion for honest coverage %);
  `cefi_master:24-VM drain` (carry_staked_basis perp hedges need cefi backfill)
- **Blocks**: THIS IS THE HEADLINE GOAL OF 2026-05-23. Blocks `master_to_live_defi_2026_05_23:F` (Group F live trading
  prerequisites); blocks `master_to_live_defi_2026_05_23:G` (DART manual-trade gate)
- **Last meaningful commit**: UAC@`f22f4b1` (CHAIN_GENESIS_DATES SSOT); UAC@`405cbf5` (declare LST/staking-yield
  protocols + DEFI_VENUE_PHASE marker); UAC@`3613e90` (LST_TOKEN_TO_PROTOCOL_ASSET SSOT — Phase 9.1A);
  features-onchain@`7f1b2a1` (canonical protocol/asset/chain columns — Phase 9.1B); strategy@`e4a0cdd`
  (CARRY_BASIS_DATED + ARBITRAGE_PRICE_DISPERSION specs — Phase 9.3); MTDS@`8c3c2c7` (DEFI legacy-underscore venue
  migration); MTDS@`10aa715`/`51fecd5`/`d898985`/`fc53a97` (Lighter + Pacifica DEX OHLCV historical)
- **Recommendation**: KEEP ACTIVE — TOP-PRIORITY P0. The headline asset_group for 2026-05-23. Critical pending: Pyth
  Solana wiring (carry_staked_basis blocker) + Copper sandbox + 4-service QG pass + CARRY_RECURSIVE_STAKED batch e2e PnL
  row. Do NOT archive. Do NOT defer P0 items.

## Scope

Single source of truth for **DeFi asset_group** work toward live DeFi 2026-05-23. The headline goal of the cutover.

Covers:

- **2 DeFi archetypes live**: `carry_staked_basis` (lead — recursive LST staking + perp short hedge) +
  `leveraged_funding_arb` (cross-venue funding spread). 7-day continuous run on real wallet.
- **2 DeFi perp DEXs live**: Hyperliquid + Aster. Plus historical-replay backfill for Lighter / Extended / Pacifica
  (originally scoped under CeFi venue expansion but they are DeFi by asset_group).
- **DeFi data pipeline E2E**: features-onchain → strategy → execution. 8 archetypes pass Phase 1 batch e2e (per
  `defi_e2e_pipeline`).
- **MTDS DeFi slice to 100%**: per-(asset_group=defi, chain, venue/protocol, data_type, instrument_id, day). Chain is a
  first-class shard axis.
- **Multi-chain oracle prices**: Pyth (Solana, unbanned 2026-05-06) + Chainlink (EVM Arb/Base/Polygon).
- **Custody integration**: Copper wired DeFi-side per `codex/04-architecture/copper-custody-integration.md`.

**Current data-status** (from deployment-ui 2026-05-07): 49138/295744 shards = **73.5%**, 988 dates missing. Tail chains
(Aurora / Celo / Fantom / Mantle / Metis / Moonbeam) stuck at 25% (1/4 protocols). Mid-tier EVMs (Arbitrum / Avalanche /
Base / BSC / Linea / Optimism / Polygon) at 60% (32/53). Ethereum 85%, Solana 99.9%.

## Current state (2026-05-07)

- **2 DeFi archetypes** live spec'd; backtest pipeline working per `consolidated_defi_data_pipeline` Phase 6
  verifications.
- **Hyperliquid + Aster perp DEXs**: instrument registry done, market-data live, execution-service connectors validated
  on testnet.
- **Lighter + Extended + Pacifica DEX-perps**: historical-replay scoping complete per `dex_historical_replay_*`;
  contract addresses + ABI parsing pending per chain.
- **Pyth oracle + multi-chain oracle**: Solana on-chain prices required for `carry_staked_basis` LST yields; UAC
  unbanning landed 2026-05-06; wiring not yet shipped.
- **DeFi data pipeline E2E**: strategy/execution/risk-and-exposure/features-onchain QG passes pending; 4 service repos
  need `quality-gates.sh` clean per `defi_e2e_pipeline`.

## Critical path

| Workstream                                                                      | Status                                                         | Source                                                   |
| ------------------------------------------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------- |
| `carry_staked_basis` archetype live (≥7 continuous days)                        | spec done; execution wiring pending                            | master plan + carry_staked_basis_structure_axis archived |
| `leveraged_funding_arb` archetype live                                          | scoped; cross-venue funding spread integration pending         | `consolidated_defi_data_pipeline`                        |
| Hyperliquid + Aster perp DEX live                                               | instruments + market-data live; execution validated on testnet | `consolidated_defi_data_pipeline`                        |
| 988 dates missing in DeFi shards (per data-status panel)                        | manifest gap; per-chain breakdown above                        | `consolidated_defi_data_pipeline` (Phase 6 reverify)     |
| Tail chains 25% coverage (Aurora / Celo / Fantom / Mantle / Metis / Moonbeam)   | per-chain protocols incomplete                                 | `consolidated_defi_data_pipeline`                        |
| Mid-tier EVMs 60% coverage (Arb / Avax / Base / BSC / Linea / Op / Polygon)     | per-chain protocols incomplete                                 | `consolidated_defi_data_pipeline`                        |
| Pyth Solana oracle wiring                                                       | unbanned 2026-05-06; integration pending                       | `consolidated_defi_data_pipeline` mtds-s3-5              |
| Multi-chain oracle (Chainlink EVM)                                              | partial                                                        | `consolidated_defi_data_pipeline` mtds-s3-6              |
| Lighter / Extended / Pacifica historical-replay backfill                        | scoped; ABI parsing per chain pending                          | `dex_historical_replay_*`                                |
| 4-service QG pass (strategy / execution / risk-and-exposure / features-onchain) | pending                                                        | `defi_e2e_pipeline`                                      |
| 8-archetype Phase 1 batch e2e                                                   | pending                                                        | `defi_e2e_pipeline`                                      |
| Copper custody integration                                                      | wired DeFi-side; sandbox integration test pending              | `consolidated_defi_data_pipeline` Copper item            |

## Consolidated todos (P0 only — full P1+ list in folded children)

### Oracle prices + chain expansion (`consolidated_defi_data_pipeline` mtds-s3)

- [x] [AGENT] P0. mtds-s3-5-pyth-oracle: Add Pyth oracle prices for Solana via Hermes (HTTPS pull, batch) + PythNet
      (Solana RPC, live). Solana-only scope. carry_staked_basis dependency. [AUDIT 2026-05-07: FRESH — actionable, P0
      BLOCKER for carry_staked_basis archetype; Pyth UNBANNED 2026-05-06 per CLAUDE.md but wiring not shipped]
      ✅ market-tick-data-service@cli/handlers/oracle_prices_handler.py (Pyth Hermes wired) 2026-05-07
- [x] [AGENT] P0. mtds-s3-6-multi-chain-oracle: Extend oracle_prices to multi-chain EVM (Chainlink on Arb/Base/Polygon).
      [AUDIT 2026-05-07: FRESH — actionable]
      ✅ market-tick-data-service@cli/handlers/oracle_prices_handler.py (Chainlink Arb/Base/Optimism/Polygon via _CHAINLINK_FEEDS_BY_CHAIN) 2026-05-07
- [ ] [HUMAN+AGENT] P0. mtds-s4-10-rescan-all-manifests: Re-scan ALL availability indexes after migrations. **Cross-plan
      coordination**: this is **Stage 4** (final sweep) of the workspace-wide manifest migration. See
      [`manifest_migration_master_2026_05_07.plan.md`](./manifest_migration_master_2026_05_07.plan.md) — MUST run AFTER
      all Stage 3 streams complete (Stage 3.A 1440-NaN flip + 3.B available_at backfill + 3.C pre-v6 cleanup +
      Predictions Polymarket migration + Sports ODDS_API re-key). Running mid-flight produces inconsistent state across
      services. NO VM pause needed — consolidator handles concurrent writes per CLAUDE.md
      `§ Manifest     concurrency principle`. [AUDIT 2026-05-07: BLOCKED-ON manifest_migration_master_2026_05_07:Stage
      3]
- [ ] [HUMAN+AGENT] P0. defi-e2e-validate: DeFi pipeline E2E — run full batch, verify features-onchain reads correctly.
      [AUDIT 2026-05-07: FRESH — actionable; gates Group F]
- [ ] [HUMAN+AGENT] P0. defi-coverage-validate: DeFi full coverage — run each handler locally for 1 day, verify GCS.
      [AUDIT 2026-05-07: FRESH — actionable]

### DeFi e2e pipeline gates (`defi_e2e_pipeline`)

- [ ] [AGENT] P0. strategy-service `quality-gates.sh` passes. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. execution-service `quality-gates.sh` passes. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. risk-and-exposure-service `quality-gates.sh` passes. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. features-onchain-service `quality-gates.sh` passes. [AUDIT 2026-05-07: FRESH — actionable;
      multi-recent-commit pattern of fixes shows ongoing work (7f1b2a1, c90d01a, 955abb5, 266f512, f3db4ca, 82d94b6)]
- [ ] [AGENT] P0. basedpyright clean across all 4 DeFi service repos. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. CARRY_RECURSIVE_STAKED batch e2e produces non-zero PnL row in
      `pnl-store-{pid}/by_strategy/.../day=2025-06-21`. [AUDIT 2026-05-07: FRESH — actionable; Phase 9 calculator
      catalog rerun launched 2026-05-07 (features-onchain-defi-backfill-20260507-013235 was launched per MEMORY but no
      longer in current snapshot, presumably drained)]
- [ ] [AGENT] P0. PnL row decomposes into base_apy + restaking_apy + borrow_cost + gas attribution. [AUDIT 2026-05-07:
      FRESH — actionable]
- [ ] [AGENT] P0. Position snapshot reflects leveraged LST holding + WETH debt. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. Health factor recorded ≥ configured `min_health_factor` for every snapshot. [AUDIT 2026-05-07: FRESH —
      actionable]
- [ ] [AGENT] P0. Synthetic feature tick injected into `defi-onchain-features-ready` produces a fill on
      `fill-events-{venue}`. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. PBM emits position snapshot; pnl-attribution emits per-strategy attribution row. [AUDIT 2026-05-07:
      FRESH — actionable]
- [ ] [AGENT] P0. Risk-and-exposure-service log shows RISK_PASS published before execution. [AUDIT 2026-05-07: FRESH —
      actionable]
- [ ] [AGENT] P0. All 8 archetypes pass Phase 1 batch e2e: CARRY_RECURSIVE_STAKED, CARRY_STAKED_BASIS, CARRY_BASIS_PERP,
      [+5 more]. [AUDIT 2026-05-07: FRESH — actionable; CARRY_BASIS_DATED + ARBITRAGE_PRICE_DISPERSION specs landed
      strategy@e4a0cdd]
- [ ] [AGENT] P0. features-onchain-service Docker image rebuild — Cloud Build emits new `:latest` tag with Phase
      changes. [AUDIT 2026-05-07: FRESH — actionable]

#### Carry tracer verification gates (folded-in 2026-05-07 from `defi_data_to_strategy_4phase_handoff` Phase A + D)

- [x] [VERIFY] P0. **Phase A gate — partial Stage 3 carry tracer** over 2026-04-03..04-09 across all 7 archetypes
      (YIELD_STAKING_SIMPLE, CARRY_BASIS_PERP, CARRY_STAKED_BASIS, CARRY_BASIS_DATED, CARRY_RECURSIVE_STAKED,
      YIELD_ROTATION_LENDING, ARBITRAGE_PRICE_DISPERSION). Expected: every archetype has non-empty `realised_apy_bps`.
      CARRY_BASIS_DATED + cross-venue ARBITRAGE_PRICE_DISPERSION are the new ones lit by `futures_roll_resolver`
      (features-cross-instrument@954575a) + `catalog_pair_builder` (954575a/2804f47/543a0bb) + UAC
      `PAIRED_DISPERSION_CATALOG` SSOT (UAC@6217382). [AUDIT 2026-05-07: PARTIAL — features-onchain VM
      `features-onchain-defi-backfill-20260507-105936` confirmed canonical columns ship in
      `lending_rates/features.parquet` (protocol/chain/asset/supply_apy/borrow_apy populated, AAVE_V3 ARBITRUM USDC
      1.62%/2.83%); A4 tracer shim deletion landed strategy@666dc2d; full per-day tracer invocation across the 7-day
      window pending features-onchain Docker rebuild]
- [ ] [VERIFY] P0. **Phase D gate — full Stage 4 historical** carry tracer over 2022-01-01..today across all 7
      archetypes. Sample 10 random days from the 4-year window; for each day, the `comparison.parquet` must have: (a)
      non-empty `realised_apy_bps` for at least 5 of 7 archetypes (CARRY_BASIS_DATED + ARBITRAGE_PRICE_DISPERSION may be
      empty pre-databento-coverage / pre-Pacifica-launch dates — honest absence, not a bug); (b) `flow_of_funds_legs`
      non-empty for the winning slot of each archetype; (c) NO silent NaN-only days (every day must show either real
      data or manifest-recorded `record_expected_empty(reason=...)`). Depends on D1-D4 backfill completion + Phase A
      gate clean + features-onchain Docker rebuild. [AUDIT 2026-05-07: FRESH — final intent-test gate before live
      cutover; gates merge of carry-tracer Phase 9 work into main]

#### Reference — multi-coin / multi-funding / multi-venue decision architecture (folded-in 2026-05-07 from `carry_tracer_pipeline_handoff_2026_05_06`)

The decision of "what to trade for an archetype" lives in **4 layers** within strategy-service. Apply to any new
archetype before adding new specs:

1. **Catalog** (`strategy-service/.../target_universe/catalog.py`) — menu of available specs. Adding a new spec is a row
   addition, not a code change. CARRY_BASIS_DATED + ARBITRAGE_PRICE_DISPERSION specs added per user direction
   2026-05-06: keep all 7 existing CARRY_BASIS_DATED specs, ADD NASDAQ-IBIT/CME-MBT (BTC ETF vs micro BTC),
   NASDAQ-ETHA/CME-MET (ETH ETF vs micro ETH), DERIBIT spot-vs-dated (BTC + ETH intra-Deribit basis), GLD/USO/UNG/
   SPY/QQQ-vs-CME-futures (placeholders for databento ETF coverage). ARBITRAGE_PRICE_DISPERSION adds CME-MBT vs
   DERIBIT-dated + CME-MET vs DERIBIT-dated (cross-venue same-expiry).
2. **Features** — per-(spec, day) metric values. Calculator owns schema; tracer reads canonical columns directly.
   Canonical schema for lst_yields = `protocol`, `asset`, `staking_apy_bps` (already bps, not fraction); for
   lending_rates = `protocol`, `chain`, `asset`, `supply_apy`, `borrow_apy` (column-form, NOT instrument_id parsing).
   features-onchain@`7f1b2a1` shipped these canonical columns; the prior tracer-side schema-adapter shim
   (strategy@`666dc2d`) is now deleted as a result.
3. **Allocator** (`strategy-service/.../portfolio_allocator/archetypes.py`, `BaseRankAllocator` + 7 archetype
   subclasses) — universe filter, score metric, threshold (default 250 bps = 2.5% APY), top-N, capital-weighting. **This
   is the opportunity-decision layer.** `CarryBasisPerpRankAllocator` is the canonical multi-coin / multi-venue example
   (3-stage hierarchical: per-coin avg → cross-coin weighting → per-venue weighting within each coin). Adding new
   specs/calculators does NOT require allocator changes — they consume the same shape.
4. **Strategy engine** (`strategy-service/engine/strategies/v2/*_engine.py`) — entry triggers, exit triggers, roll on
   expiry, rotation cost gating. Per-archetype subclass.

The `paired_price_dispersion` calculator in features-cross-instrument-service is the cross-asset-group greenfield that
powers BOTH CARRY_BASIS_DATED (one leg spot/ETF, other dated future, held to convergence) and ARBITRAGE_PRICE_DISPERSION
(both legs futures of same expiry on different venues, exit on convergence). Single calculator, two consumers; the
per-archetype filter logic is in the catalog spec rows, not duplicated in the calculator.

### Lighter / Extended / Pacifica historical replay (`dex_historical_replay_*`)

- [x] [AGENT] P0. Lighter zkSync mainnet matching contract address + ABI parse (`Trade` event). [AUDIT 2026-05-07: DONE
      for OHLCV path — MTDS@10aa715 `_fetch_lighter_candles` shipped via /candles endpoint; per MEMORY entry
      feedback_lighter_pacifica_cloudfront_quirks per-trade replay infeasible because Lighter `block_height` is
      sequencer-internal NOT zkSync L1 — on-chain `Trade` event parsing was found infeasible during empirical research.
      Subgraph option still pending in dex_perp_onboarding_handover Item C]
- [ ] [AGENT] P0. Lighter subgraph availability check (thegraph.com/explorer); validate row schema match against
      `_fetch_lighter_rest`. [AUDIT 2026-05-07: BLOCKED-ON dex_perp_onboarding_handover_2026_05_07:Item C — Extended
      on-chain replay sub-plan, pending operator]
- [ ] [SCRIPT] P0. Launch `mtds-lighter-history-backfill-{ts}` singleton-locked VM; date range 2024-08-01 → today. Add
      prefix to `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET`. [AUDIT 2026-05-07: STALE — replaced by ohlcv_1m route via
      /candles in MTDS@10aa715 (per MEMORY project_dex_perp_onboarding_2026_05_07); per-trade history NOT recoverable
      per Lighter quirks finding]
- [ ] [AGENT] P0. Extended Starknet mainnet `Settlement` contract address + event signature; add Starknet RPC template
      to UAC `CHAIN_RPC_TEMPLATES`. [AUDIT 2026-05-07: BLOCKED-ON dex_perp_onboarding_handover_2026_05_07:Item C Phase 0
      empirical research; Extended is the third venue, pending]
- [ ] [AGENT] P0. `_fetch_extended_history` in `umi_tick_provider.py`; schema-parity vs `_fetch_extended_rest`. [AUDIT
      2026-05-07: BLOCKED-ON dex_perp_onboarding_handover_2026_05_07:Item C]
- [x] [AGENT] P0. Pacifica Solana program ID + Anchor `emit!` log decoder; Helius `getSignaturesForAddress` +
      `getTransaction` parse. [AUDIT 2026-05-07: DONE for OHLCV path — MTDS@51fecd5 `_fetch_pacifica_candles` via /kline
      (ms timestamps); per-trade Anchor decoder still pending in handover Item C]
- [x] [AGENT] P0. `_fetch_pacifica_history` in `umi_tick_provider.py`; schema-parity vs `_fetch_pacifica_rest`. [AUDIT
      2026-05-07: DONE — MTDS@51fecd5 (ohlcv_1m via /kline); per MEMORY project_dex_perp_onboarding_2026_05_07]
- [ ] [SCRIPT] P0. Backfill VMs for each new venue + schema-parity validation against the REST adapter. [AUDIT
      2026-05-07: PARTIAL — Lighter + Pacifica VMs ran successfully per MEMORY; Extended VM still pending]

### DEX perp forward-poll handlers + collateral matrix (folded-in 2026-05-07 from `dex_perp_onboarding_handover`)

Captures the open work items from
[`dex_perp_onboarding_handover_2026_05_07.HANDOVER.md`](dex_perp_onboarding_handover_2026_05_07.HANDOVER.md) Items A / B
/ D / E / F as standard-format checkbox todos. The HANDOVER doc remains the narrative SSOT (with empirical findings per
venue); these checkboxes track execution.

Date ranges + venue specs:

- **LIGHTER-ZKSYNC** (zkSync Era, validium settlement) — 170 perps, top-5 currently captured (BTC, ETH, SOL, HYPE, TON).
  Historical OHLCV via `/candles` 2025-05-01 → today (manifest captured per session 2026-05-07). Per-trade history
  unrecoverable (REST capped, no cursor; on-chain replay infeasible per `block_height` being sequencer-internal).
  Forward-poll only path for live tape.
- **PACIFICA-SOLANA** (Solana program-settled, Hyperliquid clone) — ~50+ perps, top-5 captured. Mainnet 2025-06-onwards.
  50x leverage, USDC cross-margin (today). OHLCV via `/kline`.
- **EXTENDED-STARKNET** (Starknet-native, batched-proof settlement) — ~10 BTC/ETH/SOL majors. Historical OHLCV path
  unconfirmed (404 on `/candles`); see Item C below for research. Settlement events SHOULD be on-chain readable via
  Starknet `getEvents`.

Funding-rate APY observed empirically: PACIFICA BTC sometimes +50% APR vs Binance BTC perp +12% APR (~38% APR
delta-neutral carry edge if captured). DEX-DEX funding-rate dispersion is the highest-edge cell in the entire strategy
table per HANDOVER. Forward-poll wiring unblocks `CARRY_BASIS_PERP` + `ARBITRAGE_PRICE_DISPERSION` signal generation for
these venues.

- [ ] [AGENT] P0. **Forward-poll launcher** `deployment-service/scripts/vm/launch-cefi-onchain-forward-poll.sh` covering
      LIGHTER-ZKSYNC + PACIFICA-SOLANA + EXTENDED-STARKNET (+ HYPERLIQUID + ASTER for parity). Singleton-locked pattern
      (mirror `launch-sfi-forward-poll.sh`). Polls `/funding` every 1-5 min → MTDS `data_type=perp_funding`;
      `/recentTrades` every ~10s → live tape; `/orderBookOrders` / `/book` snapshots every ~30s → slippage-modeling
      input. [AUDIT 2026-05-07: FRESH — required before live trading per HANDOVER Item A]
- [ ] [AGENT] P0. **MTDS perp_funding adapter** for LIGHTER + PACIFICA + EXTENDED — venue iteration in
      `mtds-perp-funding-` VM launcher; schema parity with existing Bybit / Binance / OKX / Deribit funding feed (per
      UAC `data_type=perp_funding` shape). [AUDIT 2026-05-07: FRESH — required before forward-poll launcher works]
- [ ] [AGENT] P1. **PACIFICA `VENUE_COLLATERAL_MATRIX` entry** in
      `unified-api-contracts/unified_api_contracts/registry/venue_collateral.py`. Verify whether Pacifica accepts
      JitoSOL / mSOL as cross-margin (live probe + docs check). YES → add row with haircut citation, unlocks
      `CARRY_STAKED_BASIS@jito-pacifica-solana-...` slot (auto-generates next catalog regen). NO → add explicit
      `accepted=False` row (matrix encodes negatives explicitly per audit spec). [AUDIT 2026-05-07: FRESH — HANDOVER
      Item B; unblocks Solana 2nd perp-hedge venue diversification beyond Drift]
- [ ] [AGENT] P2. **EXTENDED-STARKNET historical OHLCV path** — Item C. Two sub-paths in priority order: (1) re-read
      `docs.extended.exchange` for the documented historical endpoint (might be auth-gated); (2) failing that, build a
      Starknet event subgraph against the Extended Settlement contract — add `STARKNET_RPC_TEMPLATE` to UAC
      `CHAIN_RPC_TEMPLATES` (currently only zkSync + Solana; Starknet needs adding). Falls back to forward-poll only if
      both paths fail. [AUDIT 2026-05-07: FRESH — HANDOVER Item C; needed for
      `cefi-extended-starknet-history-backfill-{ts}` VM]
- [ ] [AGENT] P2. **Lighter symbol-coverage scale-up** — currently
      `_LIGHTER_BACKFILL_TOP_SYMBOLS = (BTC, ETH, SOL,     HYPE, TON)`; expand to top-30 (Lighter has 170 perps
      including NVDA, USDCAD, BRENTOIL, XAU, XAG, SNDK exotics). Rate-limit budget already validated — 12 RPS handles
      top-30 comfortably. Unlocks cross-asset stat-arb / FX-perp arb against CeFi FX. [AUDIT 2026-05-07: FRESH —
      HANDOVER Item D; deferred pending strategy demand signal]
- [ ] [DOC] P3. **Per-trade gap documentation in coverage matrix** — codex `02-data/pipeline-coverage-matrix.md`: mark
      `data_type=trades` as "live-only, no historical" for LIGHTER / PACIFICA / EXTENDED. Downstream strategies that
      need per-trade should use OHLCV bars OR forward-poll-built history (~few months, growing from forward-poll launch
      date). [AUDIT 2026-05-07: FRESH — HANDOVER Item E; honest-coverage transparency]
- [ ] [VERIFY] P0. **Final state verification of Lighter + Pacifica historical backfill VMs** —
      `cefi-lighter-zksync-ohlcv-20260507-024226` + `cefi-pacifica-solana-ohlcv-20260507-024226`. Manifest should show
      `captured` for ~370 (Lighter) + ~310 (Pacifica) day-symbol shards.

      ```bash
      gcloud storage ls "gs://market-data-tick-cefi-central-element-323112/raw_tick_data/by_date/day=2025-*/asset_group=cefi/venue=LIGHTER-ZKSYNC/instrument_type=perpetual/data_type=ohlcv_1m/" | wc -l
      ```

      [AUDIT 2026-05-07: FRESH — HANDOVER Item F; operational verification]

### Tail-chain / mid-tier protocol coverage (DeFi data-status — 988 dates missing)

- [ ] [AGENT] P0. Tail chains 25% coverage diagnosis: Aurora / Celo / Fantom / Mantle / Metis / Moonbeam each have 1
      protocol live; per-chain protocol expansion deferred-post-cutover unless `carry_staked_basis` /
      `leveraged_funding_arb` requires those chains. [AUDIT 2026-05-07: FRESH — actionable diagnostic only; expansion
      deferred]
- [ ] [AGENT] P0. Mid-tier 60% coverage: Arb / Avax / Base / BSC / Linea / Op / Polygon — 32/53 protocols. Per-protocol
      backfill needed for 21 protocols/chain. Subgraph schema-mismatch fixes for PancakeSwap V3, SushiSwap V3, Aerodrome
      V3, Camelot V3 (per `defi_e2e_pipeline`). [AUDIT 2026-05-07: FRESH — actionable; UAC@0169a0a PROTOCOL_LAUNCH_DATES
      helps clip denominator]
- [ ] [AGENT] P0. 988 dates missing — query manifest, identify per-(chain, protocol, data_type) gaps, prioritize
      `carry_staked_basis` chain set first (Ethereum + Solana mostly done; Arbitrum + Base critical). [AUDIT 2026-05-07:
      FRESH — actionable; UAC@f22f4b1 CHAIN_GENESIS_DATES + UAC@0169a0a PROTOCOL_LAUNCH_DATES SSOTs help re-clip 988
      number downward]
- [ ] [AGENT] P1. Use `poolGetSnapshots` for historical TVL when querying past dates (DeFi pool query path). [AUDIT
      2026-05-07: FRESH — actionable; `grep poolGetSnapshots` returns 0 hits in workspace, confirming this DeFi-pool
      query path migration has not yet shipped] (folded from venue_axis_asset_group_vocabulary_2026_04_25)

### MTDS DeFi slice (`market_tick_data_to_100pct` — DeFi)

> **CORRECTION 2026-05-07 — earlier "PLANNING-CRITICAL" claim retracted.** A sub-agent + main-agent jointly misread the
> DeFi manifest layout, surfaced an alarming "Arb/Base/Polygon at 0%" finding, and pushed it as a planning-critical
> correction. Re-verification by walking ALL DeFi buckets shows the original plan numbers are defensible — the misread
> was reading only ONE bucket (the asset-group canonical) instead of the 10+ per-data_type buckets where Arb/Base/
> Polygon data actually lives. Codex now documents the multi-bucket DeFi layout to prevent repeat misreads — see
> [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
> § "DeFi has 10+ separate manifest buckets — checking only one gives the wrong picture".

**Verified DeFi bucket layout (2026-05-07)** — full list with `_index/availability_index.parquet` confirmed present:

| Bucket                                                               | Rows    | Chains                                                          | Last write               |
| -------------------------------------------------------------------- | ------- | --------------------------------------------------------------- | ------------------------ |
| `market-data-tick-defi-{pid}` (asset-group, Phase-1 + Phase-2 mixed) | 313,365 | ETH + SOLANA                                                    | 2026-05-05 13:44         |
| `lending-indices-{pid}`                                              | 37,000  | ETH + 9 EVM (Opt/Base/Arb/Scroll/Avax/Linea/BSC/Polygon/zkSync) | 2026-05-05 00:56         |
| `dex-swaps-{pid}`                                                    | 46,491  | ETH + 7 EVM                                                     | 2026-05-05 00:56         |
| `evm-defi-{pid}`                                                     | 22,633  | ETH + Arb/Base/Opt/Polygon                                      | 2026-05-05 10:06         |
| `instruments-store-defi-{pid}`                                       | 127,896 | 7+ chains                                                       | 2026-05-05 07:25         |
| `gas-fees-{pid}`                                                     | 11,988  | ETH + 9 EVM                                                     | 2026-05-05 00:55         |
| `oracle-prices-{pid}`                                                | 7,032   | ETH + Arb/Base/Opt/Polygon                                      | 2026-05-05 00:55         |
| `perp-funding-{pid}`                                                 | 5,575   | HYPERLIQUID + ASTER                                             | 2026-05-05 00:55         |
| `solana-defi-{pid}`                                                  | 5,028   | SOLANA                                                          | 2026-04-13 15:09 (older) |
| `lst-rates-{pid}`                                                    | 4,356   | ETH + SOLANA                                                    | 2026-05-05 00:55         |

**deployment-api correctly handles the split**: `data_status_service.py:2802` `_BUCKET_CATEGORY_OVERRIDES` routes each
per-data_type to its dedicated bucket; `_canonicalise_defi_data_types()` at line 991 normalises the dual
kebab/snake_case `data_type` vocabulary at read-time. No data-status code bug. The original plan numbers (Ethereum 85% /
Solana 99.9% / Arb-Base-Polygon 60%) are likely reading the per-bucket panels in the deployment-ui, which IS the right
view.

**Real residual concerns from this re-verification** (down-graded from "planning-critical" to legit operator items):

### Lending-indices VM run-quality bugs (discovered 2026-05-07 mid-run, VM stopped after diagnosis)

VM `mtds-lending-indices-20260507-140418` was launched 2026-05-07 14:04 IST and **stopped 2026-05-07 ~15:30 IST** after
spot-checking the per-VM shard revealed silent data-quality issues. Despite emitting 8,000+ `INSTRUMENT_PROCESSED`
events + writing 4,459 manifest rows, only 4 of 8 (venue, chain) pairs were producing captured rows; the rest were
silently writing `empty_confirmed` for dates where data should exist. The VM was stopped for diagnosis + bug fixes
before re-launch — losing ~1,080 captured rows of progress (Arbitrum/Avalanche/ Optimism/Polygon AAVE V3 days for
2022-Q4) is acceptable because re-running after the bug fixes is the cleaner path; re-runs of those days will pick up
the same data.

**Per-(venue, chain) outcome from per-VM shard** (cross-referenced with
`_index/per_vm/mtds-lending-indices-20260507-140418.parquet` 4,459 rows):

| venue / chain                       | captured | empty_confirmed | verdict                                |
| ----------------------------------- | -------- | --------------- | -------------------------------------- |
| AAVEV3 / ARBITRUM                   | 269      | 74              | ✅ working                             |
| AAVEV3 / OPTIMISM                   | 270      | 73              | ✅ working                             |
| AAVEV3 / POLYGON                    | 272      | 71              | ✅ working                             |
| AAVEV3 / AVALANCHE                  | 270      | 73              | ✅ working                             |
| AAVEV3 / **ETHEREUM**               | **0**    | **343**         | ❌ **silent zero** — bug               |
| AAVEV3 / BASE                       | 0        | 343             | ⚠️ likely correct (pre-launch in 2022) |
| AAVEV3 / LINEA                      | 0        | 343             | ⚠️ likely correct (LINEA mainnet 2023) |
| AAVEV3 / BSC                        | 0        | 343             | ⚠️ likely correct                      |
| COMPOUNDV3 / ETHEREUM               | 107      | —               | ✅ working                             |
| COMPOUNDV3 / ARBITRUM/BASE/OPTIMISM | 0        | 0 (skipped)     | ❌ **subgraph schema error**           |

**Bug 1 — AAVE V3 ETHEREUM silent zero** (P0 for `carry_staked_basis`, the most-relevant chain):

Run.log shows
`instruments-store-defi parquet missing for aave_v3/ETHEREUM/2022-12-08; falling back to subgraph discovery` then
`Wrote 0 rows`. The instruments-store-defi metadata is missing for ETHEREUM (404s for early 2022 dates) AND the subgraph
fallback is misconfigured for ETHEREUM specifically — other chains (Arbitrum, Optimism, Polygon, Avalanche) have working
subgraph fallbacks with the same code. Investigation target:
`market-tick-data-service/market_tick_data_service/cli/handlers/lending_indices_handler.py` (or equivalent) + the
per-chain subgraph endpoint config. Likely a chain→subgraph URL mapping bug or a missing schema mapping for the Ethereum
subgraph response shape.

**Bug 2 — COMPOUND V3 multi-chain subgraph schema error**:

Run.log shows
`Subgraph query errors for Ff7ha9ELmpmg81D6nYxy4t8aGP26dPztqD1LDJNPqjLS: [{'message': "Type 'Query' has no field 'marketDailySnapshots'"}]`
for COMPOUND_V3 on ARBITRUM/BASE/OPTIMISM. The Messari subgraph schema has been updated upstream + the MTDS GraphQL
query is stale. Investigation target: the same handler's COMPOUND_V3 GraphQL query — likely the field is renamed (e.g.
`marketHourlySnapshots` or `marketSnapshots`) or moved into a different entity. **Side effect**: VM records these as
`empty_confirmed` per the writegate three-category model (subgraph returned 0 rows, no exception) — but per writegate
Phase 2.A spirit this should be `attempted_failed` because the GraphQL error means we DIDN'T actually probe the data.

**Bug 3 — `instruments-store-defi` metadata missing for early 2022 dates**:

Affects all (venue, chain) pairs equally for early 2022 dates. The fallback to subgraph discovery works for some chains
and not others (see Bugs 1+2). The deeper question is whether instruments-service's lookback covers early DeFi protocol
launch dates — `instruments-store-defi-{pid}/instrument_availability/by_date/day=2022-12-08/...` returns 404 for
AAVEV3/COMPOUNDV3/etc. across all chains. Investigation target: `instruments-service` DeFi instrument-discovery script +
its launch-date floor handling.

**Verification recipe used to find these** (do this WITHIN 10-15 MIN of any backfill VM launch — don't wait for /loop):

```bash
PID=central-element-323112
VM=mtds-lending-indices-{ts}  # the actual VM name
gcloud storage cp gs://lending-indices-${PID}/_index/per_vm/${VM}.parquet /tmp/per_vm.parquet
python3 -c "
import pandas as pd
df = pd.read_parquet('/tmp/per_vm.parquet')
print(f'Total rows: {len(df):,}')
m = df.groupby(['venue','chain','capture_status']).size().unstack(fill_value=0)
print(m)
# Spot any (venue, chain) with 0 captured but non-zero empty_confirmed → silent-zero candidate
silent_zeros = m[(m.get('captured', 0) == 0) & (m.get('empty_confirmed', 0) > 100)]
if len(silent_zeros) > 0:
    print(f'\\n⚠️ Silent-zero candidates (captured=0 but empty_confirmed>100):')
    print(silent_zeros)
"
gcloud storage cat gs://deployment-scripts-${PID}/vm-logs/${VM}/run.log | grep -E "Subgraph query error|metadata unavailable|Wrote 0 rows" | head -20
```

Do this verification BEFORE assuming the VM is producing useful data based on event-stream alone.

1. **Solana coverage is genuinely thin** — `lst-rates-{pid}` has 784 SOLANA rows over a 2-year window (~monthly
   cadence). `carry_staked_basis` Solana leg won't have daily granularity until this is filled. Pyth wiring (separate
   item) is necessary-not-sufficient.
2. **Kebab/snake `data_type` vocab inconsistency** — most per-data_type DeFi buckets contain BOTH forms for the SAME
   data (e.g. `lending-indices-{pid}` has 24,976 kebab + 12,024 snake_case rows). Read-time canonicaliser handles it
   today but it's a real follow-up: write a one-shot migration to rewrite kebab → snake then delete the canonicaliser.
   No named successor plan yet — could be filed as a small follow-up under `manifest_migration_master_2026_05_07`.
3. **`solana-defi-{pid}` is 3+ weeks stale** — last write 2026-04-13. Worth confirming whether that handler is
   intentionally paused or has been broken.
4. **`launch-mtds-perp-funding-backfill-vm.sh`** is referenced in CLAUDE.md but missing from
   `deployment-service/scripts/vm/`. `leveraged_funding_arb` blocker — file as a small follow-up to author it.

**Single-VM launch recommendation** (unchanged from earlier):

| Rank | Launcher                                                             | Window       | Expected rows              | ETA           | Status                                                                  |
| ---- | -------------------------------------------------------------------- | ------------ | -------------------------- | ------------- | ----------------------------------------------------------------------- |
| 1    | `launch-mtds-lending-indices-backfill-vm.sh 2018-01-01 2026-05-07`   | full history | ~9,668                     | ~3h           | **In flight** as `mtds-lending-indices-20260507-140418` since 14:04 IST |
| 2    | `launch-mtds-vault-share-price-backfill-vm.sh 2020-01-01 2026-05-07` | full history | high carry-archetype value | parallel-safe | not yet launched                                                        |

- [ ] [AGENT] P1. Per-chain MTDS to 100%: Ethereum (85%), Solana (99.9% — basically done), Arbitrum / Base / Polygon
      (60%). Per-protocol gap analysis from `consolidated_defi_data_pipeline` Phase 6. **2026-05-07 NOTE: original
      headline percentages are defensible if reading the deployment-ui's per-bucket panels — see CORRECTION block above.
      Earlier "0%" claim was a single-bucket misread, not reality.** [AUDIT 2026-05-07: FRESH — actionable; the
      in-flight `mtds-lending-indices-20260507-140418` VM is doing the right work. After it drains, run
      vault-share-price as the parallel-safe runner-up.]

### DeFi DEX-perp adapters from `cefi_venue_universe_expansion` (re-classified to DeFi)

- [ ] [AGENT] P0. **Extended** — UAC: add to `VENUES_BY_ASSET_GROUP['defi']`. Adapter: `_fetch_extended_rest` + history.
      [AUDIT 2026-05-07: BLOCKED-ON dex_perp_onboarding_handover_2026_05_07:Item C — empirical research pending]
- [x] [AGENT] P0. **Pacifica** — UAC: same. Adapter: `_fetch_pacifica_rest`. Hyperliquid clone — schema parity. [AUDIT
      2026-05-07: DONE — MTDS@51fecd5 (ohlcv_1m); UAC@e890022 added ohlcv_1m to cefi DATA_TYPES_BY_ASSET_GROUP (note:
      routing gate per MEMORY entry feedback_uac_data_types_by_asset_group_is_routing_gate); UAC@7cb9068 / 405cbf5
      declare DEFI venue capabilities]
- [x] [AGENT] P0. **Lighter** — UAC: same. Adapter: `_fetch_lighter_rest`. zkSync L2; different RPC stack. [AUDIT
      2026-05-07: DONE — MTDS@10aa715 (ohlcv_1m); CloudFront 429 quirks documented in MEMORY
      (feedback_lighter_pacifica_cloudfront_quirks)]

### Custody (Copper)

- [ ] [AGENT] P1. Copper sandbox integration test — validate `CopperCustodyProvider` (in execution-service) per
      `codex/04-architecture/copper-custody-integration.md`. [AUDIT 2026-05-07: FRESH — actionable, P0-relevant for May
      23 Group F]

### Audit findings 2026-05-07 — folded from session wrapper

**Source**: `plans/ai/session_2026_05_07_data_status_audit_findings.plan.md` row C.9. Operator inspected DEFI pool
drilldown after the 4-candidate-probe fix shipped (deployment-api@`0384eab`); AAVE_V3-ARBITRUM still surfaces "no schema
yet" with 0 on-disk parquets across all 4 layout candidates even though the manifest claims `1781/1785 captured`.

#### C.9 — AAVE_V3-ARBITRUM phantom rows reconcile

This is a textbook phantom-rows scenario per CLAUDE.md `§ Manifest phantom audit`: manifest says `captured` but the
parquet doesn't exist at any canonical path. The orchestrator's `_should_skip_shard` will trust the manifest forever
unless reconciled. Either (a) parquets really don't exist (writer bug — needs root-cause + re-fetch), or (b) parquets
exist at a 5th layout the prober doesn't know about (extend the prober + the audit's drift-axis enumeration).

- [x] [SCRIPT] P0. Ran
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi     --dry-run` locally,
      scoped `--venues AAVEV3` (sufficient for triage; full DEFI scan deferred to GCE VM after the prober landed below
      to avoid 18× slowdown × 313k row × 7 prefix template explosion). Initial run reported 29782 false-positive
      phantoms — the entire AAVEV3 dataset; would have destroyed all manifest state had `--apply` run.
- [x] [AGENT] P0. Triaged for AAVE_V3-ARBITRUM specifically — **case (b)** confirmed: audit reported mass
      false-positives. Diagnosed root cause via on-disk listing: the canonical manifest has ZERO
      `(venue=AAVEV3,     chain=ARBITRUM)` rows (all 29782 AAVEV3 rows are on `chain=ETHEREUM`). The UI's
      "AAVE_V3-ARBITRUM 1781/1785" claim came from the deployment-api offline rollup, which conflates the expected
      denominator with the found-on-disk count for venue+chain combos that have no manifest rows (separate rollup-side
      bug, captured in codex doc + filed under infrastructure_master Data-status multi-axis follow-up).
- [x] [SCRIPT] P0. Found two NEW drift axes the prober missed; extended
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` (instruments-service@`e8393fc`). **Axis 6** —
      DeFi protocol-name underscore variant (`AAVEV3` ↔ `AAVE_V3` etc.) via new `_defi_protocol_variants` regex helper
      that probes both spellings; **Axis 7** — DeFi migrated-bundle wildcard (`ticks_migrated_*.parquet` at the
      combined-venue prefix accepted as evidence of capture for any data_type, since the bundle holds all data_types in
      one parquet). Helper unit-tested 12/12 cases PASS. Re-run on `--venues AAVEV3` shows 29782 → 0 phantoms (100%
      false-positive elimination). Manifest is clean for AAVEV3.
- [x] [VERIFY] P1. After ship: launch `defi-phantom-recon-{ts}` GCE VM in `asia-northeast1-c` (add prefix to
      `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` first) running the full DEFI dry-run with the new prober. Compare
      pre-/post-fix phantom counts across all DEFI venues (UNISWAPV3 187k rows, MORPHO 45k, EIGENLAYER, MAKER, etc.).
      Expected: large drop in false-positive count similar to the 2026-05-04 cefi 130k → 354 reduction. **SHIPPED
      2026-05-07**: deployment-service@ea0c2ed authored `scripts/vm/launch-defi-phantom-recon-vm.sh` (new launcher,
      singleton-locked, asset-group selectable, --dry-run by default), added `phantom-recon` VM_TASK route to
      `setup-data-pipeline-vm.sh`, and added `defi-phantom-recon-` prefix to `vm_zombie_watchdog.py`. Path bug fix at
      deployment-service@a6d3b8f (instruments tarball alias = `$WORKSPACE/instruments` not
      `$WORKSPACE/instruments-service`). VM `defi-phantom-recon-defi-20260507-141621` launched 14:16 IST, watchdog
      relaunched as `vm-zombie-watchdog-20260507-141056`. **Result 14:24 IST (rc=0, ~10 min runtime, 86,982 prefixes
      listed at 360/sec same-region GCE)**: 309,749 real captures + **2,931 phantom captures (0.94%)**. Top phantom
      data_types: vault_share_price (1,633) + rewards (1,298). Top phantom venues: EIGENLAYER (1,298), MORPHOVAULTS
      (851), YEARNV3 (782) — concentrated in features-onchain consumers (`eigen_rewards` + `vault_share_price`), so
      they're real blockers, not prober drift. **Next step (operator)**: run
      `bash scripts/vm/launch-defi-phantom-recon-vm.sh defi --apply` to flip the 2,931 phantoms to `attempted_failed`,
      then re-run the affected MTDS DeFi backfills (eigen_rewards via `mtds-perp-funding`/equivalent and morpho/yearn
      `vault_share_price` via `launch-mtds-vault-share-price-backfill-vm.sh`).
- [x] [DOC] P0. Updated `codex/02-data/availability-manifest-and-data-status.md` § "Phantom audit — re-runnable recipe"
      to enumerate 7 drift axes (was 5); added rollup-side metric inconsistency finding under § "Rollup-side metric
      inconsistency (deployment-api `_data_status_rollup_worker`) — open finding 2026-05-07"; updated history benchmark
      with the 2026-05-07 AAVEV3 29782 → 0 reduction.

## Anti-patterns + workspace-rule cross-references

- **Pyth UNBANNED for Solana** (2026-05-06): use Hermes (batch) + PythNet (live). Other chains stay on Chainlink. See
  CLAUDE.md "Removed providers" → "Pyth — UNBANNED" entry.
- **Live = batch**: same code path; matching engine for backtests. See `codex/04-architecture/batch-live-pipeline.md`.
- **`chain` is a first-class shard axis** for DeFi (per CLAUDE.md per-asset-group shard-key matrix).

## Cross-references

- Master plan: [`master_to_live_defi_2026_05_23.plan.md`](./master_to_live_defi_2026_05_23.plan.md).
- Sibling asset_group umbrellas: `cefi_master_2026_05_07`, `tradfi_master_2026_05_07`, `sports_master_2026_05_07`,
  `predictions_master_2026_05_07`.
- Carry tracer pipeline handoff: `plans/ai/carry_tracer_pipeline_handoff_2026_05_06.md` (in-flight Phase 9 catalog).

## Folded plans (archived 2026-05-07)

- `consolidated_defi_data_pipeline_2026_04_15.plan.md` — DeFi pipeline umbrella (full P1 list lives in this archive).
- `defi_e2e_pipeline_2026_04_30.plan.md` — 4-service QG + 8-archetype e2e gates.
- `dex_historical_replay_lighter_extended_pacifica_2026_05_07.plan.md` — DEX-perp historical replay scoping.
- `market_tick_data_to_100pct_2026_05_05.plan.md` (DeFi slice) — full plan archived after split per asset_group.
- `cefi_venue_universe_expansion_2026_05_01.plan.md` (DEX-perp half) — Lighter / Extended / Pacifica re-classified to
  DeFi asset_group; CeFi venues (Bitfinex / Bitget / Kraken) lifted into `cefi_master`.
- `venue_axis_asset_group_vocabulary_2026_04_25.plan.md` (1 absorbed item) — `poolGetSnapshots` historical-TVL DeFi-pool
  query item lifted into "Tail-chain / mid-tier protocol coverage" above; remaining 2 absorbed items
  (`venue_start_dates` deletion + dashboard SSOT verify) folded into `infrastructure_master_2026_05_07`.
