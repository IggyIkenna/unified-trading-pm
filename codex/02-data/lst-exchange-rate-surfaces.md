---
doc_type: codex-ssot
title: LST exchange-rate surfaces — four distinct prices, canonical homes, honest-coverage contract
summary: >-
  SSOT for the FOUR distinct "LST exchange rate" prices and where each canonically lives. They are NOT interchangeable:
  (1) CEX secondary-market spot (~1.0 peg, market-data-tick-cefi Tardis), (2) DEX pool exchange rate (~1.0 on-chain peg,
  dex_pool_swaps + derived mid), (3) on-chain oracle price (the price the AAVE lending market marks collateral at,
  drives LTV/liquidation — Chainlink aggregator + AaveOracle.getAssetPrice), (4) protocol redemption/accrual ratio
  (~1.23, the TRUE staking exchange rate, lst_rates/lst_yields). Each feeds a different PnL leg (staking accrual = #4;
  mark-to-market basis = #1/#2; recursive-staking collateral/LTV = #3). Defines the canonical shard atom per surface and
  the denominator-first honest-coverage contract (register the feed/venue so an un-captured rate shows as
  expected_unattempted RED BEFORE any backfill, never a phantom).
status: current
nature: ssot
asset_group: [defi]
stage: [data, strategy]
repos: [market-tick-data-service, instruments-service, unified-api-contracts, features-service, strategy-service]
scope: [engineer, admin]
tags: [lst, exchange-rate, staking, oracle, dex, honest-coverage, pnl-correctness, defi]
authoritative_for: [lst-exchange-rate, lst-oracle-price, lst-staking-accrual, lst-rate-canonical-homes]
related:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: "2026-07-21"
referenced_by:
code_refs:
last_reviewed: 2026-10-21
owner:
last_updated: "2026-07-21"
parent_epic: infrastructure_master
scope_note: money-path-adjacent — these rates value LST collateral (LTV/liquidation) and the staking-yield PnL leg.
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# LST exchange-rate surfaces — four distinct prices

An "LST exchange rate" is not one number. For a liquid-staking token (stETH the running example; same shape for
wstETH/rETH/cbETH/weETH/rsETH/ezETH on EVM, jitoSOL/mSOL/bSOL on Solana) there are **four distinct prices with distinct
canonical homes, and they must NEVER be substituted for one another.**

## The four surfaces

| #   | Rate (meaning)                                                                                                                   | Magnitude             | Canonical home (shard atom)                                                                                                                                                                    | Feeds which PnL leg                                  |
| --- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| 1   | **CEX secondary-market spot** (stETH/USDT, stETH/USD) — market peg to ETH                                                        | ~1.0                  | `raw_tick_data` · `pipeline_mode=batch_tardis` · `asset_group=cefi` · `venue={*-SPOT}` · `instrument_type=spot_pair` · `data_type={trades, book_snapshot_5}` · id `VENUE:SPOT_PAIR:BASE-QUOTE` | mark-to-market of the LST (basis vs short)           |
| 2   | **DEX pool exchange rate** (stETH/ETH from Curve/UniV3/Balancer)                                                                 | ~1.0                  | `venue={CURVE, UNISWAP_V3, BALANCER}-ETHEREUM` · `instrument_type=pool` · `data_type=dex_pool_swaps` (+ a derived per-interval mid)                                                            | mark-to-market / peg                                 |
| 3   | **On-chain oracle price** (Chainlink aggregator + `AaveOracle.getAssetPrice`) — the price the lending market marks collateral at | USD 8-dec / ETH-denom | `data_type=oracle_prices` on TWO venues: `CHAINLINK-ETHEREUM`:`SPOT_PAIR` (per feed) and `AAVE`(write)/`AAVE-ETHEREUM`(IS):`spot_asset` (getAssetPrice per reserve)                            | **recursive-staking collateral / LTV / liquidation** |
| 4   | **Protocol redemption / accrual ratio** (wstETH/stETH) — the TRUE staking exchange rate                                          | ~1.23                 | `lst_rates` (source) → `lst_yields` (feature) · `venue={LIDO, ROCKET_POOL, KELPDAO, RENZO, ETHERFI, …}-ETHEREUM`; the `exchange_rate`/`prev_rate` columns                                      | **the staking-yield accrual**                        |

**The money-path trap:** #1/#2 are ~1.0 SECONDARY-market pegs; #4 is the ~1.23 ACCRUAL ratio. Capturing spot mid does
NOT substitute for the staking-accrual rate, and vice-versa. #3 is denominated 8-dec USD (`getAssetPrice/1e8`) and is
the value the AAVE market uses — it drives LTV and liquidation, so recursive-staking collateral MUST use #3, not a #1/#2
proxy. This aligns with `pnl-attribution.md` Hard Rule #5 (staking yield via the exchange-rate index) and Hard Rule #4
(lending via the on-chain index).

## Canonical homes + the honest-coverage contract

### Surface #1 — CEX spot: denominator is ALREADY complete (completion = backfill, not build)

Every LST base (STETH/WSTETH/RETH/WEETH/CBETH/RSETH/EZETH/MSOL/JITOSOL) is in `CEFI_BASE_ASSET_UNIVERSE` **and** the
`STAKING_SPOT_EXCEPTION` perp-gate carve-out, so their spot pairs are MVP even without a perp. Tardis enumerates every
exchange-listed symbol — there is **no per-symbol IS allow-list**.

> **Anti-pattern (HARD): "adding STETH-USDT to the catalogue" is a no-op / phantom-minting — never do it.** The
> denominator already contains the LST bases; a manual list edit only risks minting `expected_unattempted` rows for
> venue×symbol pairs that are not actually listed (permanent-false RED). The gap is a **backfill-run** contiguity
> problem (cap-1 Tardis only ran some (venue,date) cells; degraded to Coinbase-only), not a build gap.

Honest absence: wstETH/rETH/rsETH/ezETH are DeFi-native wrappers rarely CEX-listed. If no venue lists a pair, the honest
state is `EXPECTED_INSTRUMENT_NOT_LISTED` (their rate comes from #2/#3), NOT a fetch target that reads RED forever.

### Surface #3 — Oracle price: SHIPPED 2026-07-21 (was dormant plumbing, now wired + manifest-verified)

**Update 2026-07-30**: the build described below shipped same-day as this doc (market-tick-data-service@672f82f5,
follow-ups `27e077da`/`51ec9af2`) — `OraclePricesHandler` now collects `AaveOracle.getAssetPrice()` via a dedicated
`_aave_oracle_collection.py` branch for all 6 LST reserves. Manifest-verified: venue=AAVE data_type=oracle_prices
source=aave shows 5,568 `capture_status=captured` rows, 2023-01-27→2026-07-22 (backfilled in 3 waves 07-23/07-27/07-28).
**Residual gap (tracked separately, NOT a build gap):** no oracle_prices row (any of the 3 venues — CHAINLINK/PYTH/AAVE)
has landed since 2026-07-22, an 8-day silence despite the rest of the DeFi manifest writing daily — see
`plans/active/issues/defi_oracle_prices_capture_stalled_since_2026_07_22.md`.

`AaveOracle.getAssetPrice()` was fully implemented and dormant (unwired to a running collection venue) before the above
fix: `aave_positions.py::_fetch_rpc_oracle_prices` (+ the LST adapters) and
`AAVE_ORACLE_ADDRESS = 0x54586bE62E3c3580375aE3723C145253060Ca0C2`. The RPC call was lifted/shared, not re-implemented.

- **Venue token (RULED):** write venue `AAVE`, IS venue `AAVE-ETHEREUM`, `instrument_type=spot_asset`,
  `data_type=oracle_prices`. This EXTENDS the already-existing `AAVE-ETHEREUM` venue (flip phase `pipeline`→`live`), not
  a new venue. `data_type=oracle_prices` + `instrument_type=spot_asset` disambiguates the shard atom from the existing
  `AAVE→governance_events` and from `AAVE_V3` lending.
- **Contract:** reuse the venue-agnostic `DEFI_SPOT_ASSET_ORACLE_PRICES` contract — NO new contract. `write_defi_rows`
  runs STRICT here, so AAVE rows MUST carry the `symbol`/`feed` column. TRAP: `AAVE_ORACLE_PRICES_SCHEMA`
  (`external/defi/schemas.py`) is the subgraph reserve shape — do NOT wire it as the write contract.
- **Chainlink feed gap:** `_CHAINLINK_FEEDS_BY_CHAIN['ETHEREUM']` carries only stETH/USD, stETH/ETH, cbETH/ETH, rETH/ETH
  — missing wstETH/weETH/rsETH/ezETH. Add ONLY feeds with a real price aggregator (most LRTs have PoR / exchange-rate
  feeds, not price aggregators — those get their price via the AAVE `getAssetPrice` path, which is the PRIMARY source;
  Chainlink is best-effort). Mirror discipline: add to BOTH the MTDS dict `{address,decimals,base,quote}` and the IS
  tuple `(address,base,quote)` — the invariant test asserts they mirror.
- **On-chain VERIFY before registering:** `eth_call getAssetPrice(token) != 0` at a recent block per LST reserve.
  rsETH/ezETH may only be on AAVE's Lido/Prime instances, not the main Pool — a wrong include seeds a permanent-false
  RED `expected_unattempted` cell.

### Surface #2 — DEX pool: discovery is fine, the collector is broken

IS pool-discovery needs no change (CURVE/UNISWAP_V3/BALANCER-ETHEREUM are live+MVP; Curve auto-discovers stETH/ETH via
its REST registry). The gap is the **collector**: Uniswap-V3 `dex_pool_swaps` is ~6 days shallow with no materialised
mid. **CORRECTION (verified 2026-07-21, `wf_f629fbb4-7da`):** the Ethereum LST subgraph endpoints are NOT dead — a live
probe hit the Curve stETH/ETH pool (`0xDC24316b9AE028F1497c275EB9192a3Ea0f67022`) + Balancer via the existing
`thegraph-api-key` secret + the shipped `dex_swaps_handler` cascade + UAC `SUBGRAPH_IDS`, all HTTP 200 /
`hasIndexingErrors:false` / at-head with real swaps. So #2 is a normal collector/backfill task (deepen UniV3 + derive
the per-interval mid), **not** an endpoint-dead blocker. Curve REST (`api.curve.finance`, no key) is a live
direct-alternative for pool-state.

### Surface #4 — Protocol redemption: HAVE, but the feature window is narrow

`lst_yields.exchange_rate`/`prev_rate` are the on-chain `getPooledEthByShares` / `stEthPerToken` / `getExchangeRate` /
`getRate` / `convertToAssets` eth_call values (MTDS `lst_rates_handler.py` `_EVM_LST_ABI_METADATA`). The FEATURE is only
~15 days (EVM-only) while the SOURCE `lst_rates` is broad — close with a features backfill, and fix the today-vs-prior
inner-join/vocab that drops Solana + LRTs from the feature output.

## The denominator-first honest-coverage invariant (sequencing rule)

1. **Register the denominator FIRST, fill SECOND.** Add the verified feed/venue to the IS catalogue + expected
   registries so every un-captured LST rate renders `expected_unattempted` (honest RED) BEFORE any backfill runs. This
   makes the gap visible and honest, not invisible; it is the correct state, not a regression.
2. **Shard atom IDENTICAL** across writer / manifest / IS-expected / gate / UI — a mismatch is a phantom absence. For
   the AAVE oracle:
   `(day, batch_<source>, defi, venue=AAVE, chain=ETHEREUM, instrument_type=spot_asset, data_type=oracle_prices, instrument_id=<symbol_lower>)`.
3. **Never fake `record_captured`.** Listed-but-empty → `record_empty`; an upload/RPC failure → `record_failed`
   (retryable); a never-listed CEX pair → `EXPECTED_INSTRUMENT_NOT_LISTED`. `source=` is mandatory on every
   `record_captured`; confirm `pipeline_mode_for_source('aave')` resolves (add to the UAC SOURCE map if absent).
4. **Verify reality before registering** (Phase 0): a feed/reserve/pair that cannot actually be captured must not be
   seeded into `expected_unattempted`, or it reads RED forever.

## Provenance

Grounded by the 2026-07-21 4-rate data-availability audit
(`plans/archive/issues/lst_exchange_rate_data_availability_2026_07_21.md` — archived 2026-07-30, all todos shipped) +
the pipeline-add understand sweep. Build plan of record: `plans/active/lst_rate_honest_coverage_2026_07_21.md`.
</content>
