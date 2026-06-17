---
scope: [engineer, admin]
title: Archetype Production Param Schema Inventory (Phase B)
type: strategy
status: active
created: 2026-06-17
author: ikennaigboaka [slot-1·laptop]
---

# Archetype Production Param Schema Inventory (Phase B)

> **Provenance**: Phase B of `plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md`.
> Faithful, source-cited enumeration of the production config-parameter surface per v2 strategy archetype. This is the
> FLAT PARAM SCHEMA that Phase C's manifest exporter emits into the capability manifest. **Every default is quoted from
> source** — nothing here is aspirational.
>
> **Companion stub**: `cross-cutting/archetype-strategy-params.md` (this file is its concrete realisation).

## How v2 engines read params (the schema mechanism)

Every v2 archetype engine extends `BaseArchetypeEngineV2` (`strategy_service/engine/strategies/v2/base.py:55`) and
receives its config as a **flat `params: dict[str, str]`** slot field (`base.py:63`). Engines parse params through four
typed, fail-soft helpers in `strategy_service/engine/strategies/v2/_params.py` — the **third argument is the DEFAULT**:

| helper          | signature                         | type    | file:line       |
| --------------- | --------------------------------- | ------- | --------------- |
| `decimal_param` | `(params, key, default: Decimal)` | decimal | `_params.py:16` |
| `int_param`     | `(params, key, default: int)`     | int     | `_params.py:27` |
| `str_param`     | `(params, key, default: str)`     | str     | `_params.py:38` |
| `float_param`   | `(params, key, default: float)`   | float   | `_params.py:42` |

Direct `self.params.get(key, default)` and `str_param(...).lower() == "true"` (a **bool** idiom) also appear. Malformed
values fall back to the default with a `logger.warning` (never raise inside `on_tick`). Some engines declare a
class-level `REQUIRED_PARAMS: frozenset[...]` and raise `ValueError` in `__init__` when absent.

**Schema-emitter contract for Phase C**: a param row =
`{archetype, name, type, default, range_or_enum, units, required, source}`.
`type ∈ {int, float, decimal, str, enum, bool}`. `required = true` iff the param is in the engine's `REQUIRED_PARAMS` OR
the engine raises / returns `[]` when it is absent. `default = null` for required params with no literal default. The
legacy GCS config path is `strategy_config_loader.load_strategy_config()` (`engine/core/strategy_config_loader.py:30`) —
it returns the raw dict; the typed defaults live in the engines, not the loader.

Catalog/slot defaults (the firm's standing instances) live in `archetype_slots_defi.py` (DEFI*SLOTS, 27 factory
strings), `target_universe/catalog_staked_basis.py`, and the per-domain
`archetype_slots*{cefi,tradfi,sports}.py`. Kelly fractions per archetype are in `engine/strategies/v2/archetype_defaults.py:40` (`KELLY_FRACTION_BY_ARCHETYPE`).

All paths below are relative to `strategy-service/strategy_service/`.

---

## LIVE DeFi archetypes

### CARRY_STAKED_BASIS — `engine/strategies/v2/carry_and_yield/staked_basis.py`

Engine `CarryStakedBasisEngine` (`staked_basis.py:404`).
`ALLOWED_ARCHETYPES = {CARRY_STAKED_BASIS, CARRY_STAKED_BASIS_DATED}` (`:407`). `REQUIRED_PARAMS` (`:413`) — raised in
`__init__` (`:431`). Kelly = 0.375 (TIER_MID_VARIANCE). Config extracted in `_extract_config` (`:193`); thresholds in
`_preflight` (`:275`).

| name                    | type    | default                                                                 | range / enum                                                                                      | units      | required | source                |
| ----------------------- | ------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ---------- | -------- | --------------------- |
| staking_protocol        | str     | (none)                                                                  | lido/rocketpool/coinbase_staking/etherfi/eigenlayer/jito/marinade/drift/gmx (chain-gated, `:128`) | protocol   | **yes**  | `staked_basis.py:195` |
| native_asset            | str     | (none)                                                                  | e.g. ETH/SOL                                                                                      | token      | **yes**  | `staked_basis.py:196` |
| lst_asset               | str     | (none)                                                                  | e.g. stETH/weETH/rETH/JitoSOL/mSOL                                                                | token      | **yes**  | `staked_basis.py:197` |
| perp_venue              | str     | (none)                                                                  | must accept LST as collateral (`accepted_perp_collateral`)                                        | venue      | **yes**  | `staked_basis.py:198` |
| perp_instrument         | str     | (none)                                                                  | e.g. ETH-PERP                                                                                     | instrument | **yes**  | `staked_basis.py:199` |
| spot_venue              | str     | (none)                                                                  | e.g. UNISWAP_V3 / JUPITER                                                                         | venue      | **yes**  | `staked_basis.py:200` |
| start_token             | str     | `"USDC"`                                                                | USDC/USDT/FDUSD (`_STABLECOINS`, `:165`)                                                          | token      | no       | `staked_basis.py:201` |
| stake_fraction          | decimal | `"1.0"`                                                                 | must == 1.0 (LST_AS_MARGIN; else reject, `:243`)                                                  | fraction   | no       | `staked_basis.py:242` |
| min_health_factor       | decimal | `"1.25"`                                                                | >0; kill gate when LST posted as margin                                                           | ratio      | no       | `staked_basis.py:263` |
| entry_bps               | decimal | `"200"`                                                                 | net-carry entry threshold                                                                         | bps        | no       | `staked_basis.py:293` |
| exit_bps                | decimal | `"50"`                                                                  | net-carry exit threshold                                                                          | bps        | no       | `staked_basis.py:294` |
| hedge_deadline_ms       | int     | `5000`                                                                  | >0                                                                                                | ms         | no       | `staked_basis.py:469` |
| peg_drift_threshold_bps | decimal | `"25"` (`DEFAULT_PEG_DRIFT_THRESHOLD_BPS`, `dynamic_hedge_ratio.py:81`) | dynamic hedge-ratio rebalance trigger                                                             | bps        | no       | `staked_basis.py:489` |

Feature inputs (not config params): `staking_apy_bps`, `funding_rate_apy_bps`, `usdc_idle_yield_apy_bps` (opt),
`fees_apy_bps` (opt), `health_factor` (opt), `lst_native_rate` / `lst_native_rate_ts` (opt; staleness 300 s, `:170`).

### CARRY_BASIS_PERP — `engine/strategies/v2/carry_and_yield/basis_perp.py`

Engine `CarryBasisPerpEngine` (`basis_perp.py:45`). No `REQUIRED_PARAMS`. Kelly = 0.500 (TIER_STABLE_STRUCTURAL).
Perp-leg only (spot hedge composed by orchestrator).

| name              | type    | default    | range / enum                        | units    | required | source             |
| ----------------- | ------- | ---------- | ----------------------------------- | -------- | -------- | ------------------ |
| min_mid_price     | decimal | `"0.0001"` | skip ticks at/below                 | price    | no       | `basis_perp.py:63` |
| entry_funding_bps | decimal | `"50"`     | enter when \|funding\| ≥ this       | bps      | no       | `basis_perp.py:72` |
| exit_funding_bps  | decimal | `"10"`     | exit when \|funding\| ≤ this        | bps      | no       | `basis_perp.py:73` |
| stake_fraction    | decimal | `"0.5"`    | fraction of equity in perp notional | fraction | no       | `basis_perp.py:74` |

Feature input: `funding_rate_annualised_bps`. Direction from funding sign (`>0` → SHORT, `<0` → LONG).

### ARBITRAGE_PRICE_DISPERSION — `engine/strategies/v2/arbitrage_structural/price_dispersion.py`

Engine `ArbitragePriceDispersionEngine` (`price_dispersion.py:93`). `REQUIRED_PARAMS = {candidate_venues}` (`:98`, ≥2
venues, raised in `__init__` `:100` for the price-dispersion path). Kelly = 0.500. **Two paths dispatched on
`dispersion_type`**: `price-dispersion` (default) and `funding-rate-dispersion`.

Common:

| name              | type    | default              | range / enum                                        | units    | required | source                        |
| ----------------- | ------- | -------------------- | --------------------------------------------------- | -------- | -------- | ----------------------------- |
| dispersion_type   | enum    | `"price-dispersion"` | {price-dispersion, funding-rate-dispersion} (`:90`) | —        | no       | `price_dispersion.py:107,130` |
| stake_fraction    | decimal | `"0.1"`              | leader-leg notional fraction                        | fraction | no       | `price_dispersion.py:205,466` |
| hedge_deadline_ms | int     | `5000`               | >0                                                  | ms       | no       | `price_dispersion.py:206,467` |

price-dispersion path:

| name             | type      | default | range / enum                   | units      | required             | source                        |
| ---------------- | --------- | ------- | ------------------------------ | ---------- | -------------------- | ----------------------------- |
| candidate_venues | str (csv) | (none)  | comma-separated, ≥2 venues     | venue-list | **yes** (price path) | `price_dispersion.py:109,256` |
| dispersion_bps   | decimal   | `"30"`  | (sell_mid−buy_mid)/mid trigger | bps        | no                   | `price_dispersion.py:200`     |
| cost_bps         | decimal   | `"10"`  | subtracted as cost estimate    | bps        | no                   | `price_dispersion.py:201`     |

funding-rate-dispersion path:

| name                           | type      | default                  | range / enum                                                    | units      | required           | source                    |
| ------------------------------ | --------- | ------------------------ | --------------------------------------------------------------- | ---------- | ------------------ | ------------------------- |
| venue_universe                 | str (csv) | `""`                     | comma-separated, ≥2 venues                                      | venue-list | yes (funding path) | `price_dispersion.py:484` |
| pair_selection_mode            | enum      | `"single-best"`          | {single-best, top-k, all-above-threshold} (`PairSelectionMode`) | —          | no                 | `price_dispersion.py:358` |
| pair_selection_k               | int       | (none)                   | top-k size when mode=top-k                                      | count      | no                 | `price_dispersion.py:359` |
| min_spread_threshold_bps       | decimal   | `"5.0"`                  | min net spread to keep a pair                                   | bps        | no                 | `price_dispersion.py:361` |
| max_concurrent_pairs_per_slot  | int       | `5`                      | >0                                                              | count      | no                 | `price_dispersion.py:362` |
| target_leverage                | decimal   | `"5.0"`                  | per-pair leverage before vol clamp                              | ratio      | no                 | `price_dispersion.py:432` |
| vol_cap_clamp_feature          | str       | `"realized_vol_20"`      | RV feature key                                                  | feature    | no                 | `price_dispersion.py:533` |
| vol_cap_clamp_threshold_pct    | decimal   | `"80.0"`                 | RV percentile threshold                                         | pct        | no                 | `price_dispersion.py:534` |
| vol_cap_clamp_zscore_feature   | str       | `"vol_regime_zscore_20"` | z-score feature key                                             | feature    | no                 | `price_dispersion.py:535` |
| vol_cap_clamp_zscore_threshold | decimal   | `"2.0"`                  | z-score breach threshold                                        | z          | no                 | `price_dispersion.py:536` |
| vol_cap_clamp_combine          | enum      | `"any"`                  | {any, all}                                                      | —          | no                 | `price_dispersion.py:537` |
| vol_cap_clamp_target_leverage  | decimal   | `"1.0"`                  | clamped-down leverage on breach                                 | ratio      | no                 | `price_dispersion.py:538` |

Feature inputs: `mid_price_<venue>`, `funding_rate_<venue>`, `pair_cost_<long>_<short>_bps` (opt; missing → 0.0).

### CARRY_RECURSIVE_STAKED — `engine/strategies/v2/carry_and_yield/recursive_staked.py`

Engine `CarryRecursiveStakedEngine` (`recursive_staked.py:169`).
`ALLOWED_ARCHETYPES = {CARRY_RECURSIVE_BORROW_LENDING_ONLY, CARRY_BASIS_PERP_INV, CARRY_RECURSIVE_STAKED}` (`:172`). No
`REQUIRED_PARAMS` constant; `_extract_protocols` returns None (skip) when the four protocol strings are absent (`:95`).
Kelly = 0.125 (TIER_HIGH_VARIANCE).

| name                  | type    | default       | range / enum                                | units    | required   | source                    |
| --------------------- | ------- | ------------- | ------------------------------------------- | -------- | ---------- | ------------------------- |
| staking_yield_enabled | bool    | `"true"`      | "true"/other; false stubs the loop (`:194`) | —        | no         | `recursive_staked.py:194` |
| staking_protocol      | str     | `""`          | required for emit                           | protocol | yes (emit) | `recursive_staked.py:96`  |
| lending_protocol      | str     | `""`          | e.g. AAVE_V3_ETHEREUM (parsed `:63`)        | protocol | yes (emit) | `recursive_staked.py:97`  |
| native_asset          | str     | `""`          | e.g. ETH                                    | token    | yes (emit) | `recursive_staked.py:98`  |
| lst_asset             | str     | `""`          | e.g. stETH                                  | token    | yes (emit) | `recursive_staked.py:99`  |
| target_leverage       | decimal | `"2.5"`       | >1 effective leverage                       | ratio    | no         | `recursive_staked.py:130` |
| safety_buffer_ltv     | decimal | `"0.15"`      | buffer below protocol LTV                   | fraction | no         | `recursive_staked.py:131` |
| protocol_ltv          | decimal | `"0.75"`      | governance-asof override applied (`:142`)   | fraction | no         | `recursive_staked.py:132` |
| max_stETH_depeg_bps   | decimal | `"50"`        | kill if \|depeg\| > this                    | bps      | no         | `recursive_staked.py:86`  |
| min_health_factor     | decimal | `"1.25"`      | kill if health < this                       | ratio    | no         | `recursive_staked.py:90`  |
| min_net_apy_bps       | decimal | `"150"`       | entry threshold on net leveraged APY        | bps      | no         | `recursive_staked.py:160` |
| chain                 | str     | `""` (→ None) | stamped on instruction                      | chain    | no         | `recursive_staked.py:368` |

Feature inputs: `staking_apy_bps`, `borrow_apy_bps`, `depeg_bps`, `health_factor`. (`max_loops` is a hard-coded 10 in
`_build_loop_legs:397`, NOT a config param — though the DEFI_SLOTS catalog passes a `max_loops` key that the engine
currently ignores; see Findings F1.)

### YIELD_STAKING_SIMPLE — `engine/strategies/v2/carry_and_yield/staking_simple.py`

Engine `YieldStakingSimpleEngine` (`staking_simple.py:46`). No `REQUIRED_PARAMS`; `_resolve_context` returns None when
protocol/asset absent (`:58`). Kelly = 0.750 (TIER_NEAR_FULL).

| name             | type    | default       | range / enum                        | units    | required     | source                     |
| ---------------- | ------- | ------------- | ----------------------------------- | -------- | ------------ | -------------------------- |
| staking_protocol | str     | `""`          | required for action                 | protocol | yes (action) | `staking_simple.py:58`     |
| asset            | str     | `""`          | native asset, required              | token    | yes (action) | `staking_simple.py:59`     |
| lst_asset        | str     | `""` (→ None) | LST receipt token                   | token    | no           | `staking_simple.py:62`     |
| min_apy_bps      | int     | `200`         | unwind below this floor             | bps      | no           | `staking_simple.py:63`     |
| min_delta_units  | decimal | `"0"`         | suppress tiny reconciliation trades | units    | no           | `staking_simple.py:64`     |
| exit_queue_ok    | bool    | `"true"`      | "false" disables exit-queue unstake | —        | no           | `staking_simple.py:65`     |
| stake_fraction   | decimal | `"1.0"`       | fraction of equity to stake         | fraction | no           | `staking_simple.py:88,255` |

Feature input: `staking_apy_bps`.

### YIELD_ROTATION_LENDING — `engine/strategies/v2/carry_and_yield/rotation_lending.py`

Engine `YieldRotationLendingEngine` (`rotation_lending.py:52`). No `REQUIRED_PARAMS`. Kelly = 0.750.

| name                  | type      | default       | range / enum                           | units         | required | source                       |
| --------------------- | --------- | ------------- | -------------------------------------- | ------------- | -------- | ---------------------------- |
| asset                 | str       | `"USDC"`      | lent asset symbol                      | token         | no       | `rotation_lending.py:94,166` |
| min_apy_advantage_bps | int       | `25`          | rotate only if advantage ≥ this        | bps           | no       | `rotation_lending.py:95`     |
| min_apy_bps           | int       | `100`         | do not lend below this floor           | bps           | no       | `rotation_lending.py:96`     |
| stake_fraction        | decimal   | `"1.0"`       | fraction of equity to lend             | fraction      | no       | `rotation_lending.py:97,165` |
| candidate_protocols   | str (csv) | `""`          | comma-separated whitelist; empty ⇒ any | protocol-list | no       | `rotation_lending.py:199`    |
| protocol_chains       | str (csv) | `""`          | `protocol_id:chain_id` pairs           | map           | no       | `rotation_lending.py:189`    |
| current_chain         | str       | `""`          | chain where capital sits               | chain         | no       | `rotation_lending.py:65`     |
| bridge_hint           | str       | `""` (→ None) | bridge slug on BridgeInstructionV2     | slug          | no       | `rotation_lending.py:113`    |

Feature input: `apy_bps_<protocol_id>`.

### DEFI_LP_CONCENTRATED — `engine/strategies/v2/defi_lp/concentrated.py`

Engine `DefiLpConcentratedEngine` (`concentrated.py:187`). FAMILY=MARKET*MAKING. Kelly = 0.500. No `REQUIRED_PARAMS`;
no-ops until `pool_address` + the `lp_pool_sqrt_price*<pool>` feature present.

| name                           | type    | default | range / enum                       | units    | required     | source                |
| ------------------------------ | ------- | ------- | ---------------------------------- | -------- | ------------ | --------------------- |
| pool_address                   | str     | `""`    | V3 pool contract; no-op when empty | address  | yes (action) | `concentrated.py:233` |
| range_pct                      | decimal | `"5"`   | half-width of price range          | pct      | no           | `concentrated.py:243` |
| rebalance_band_pct             | decimal | `"3"`   | drift that triggers rebalance      | pct      | no           | `concentrated.py:244` |
| min_rebalance_interval_seconds | int     | `3600`  | rate-limit on rebalances           | seconds  | no           | `concentrated.py:245` |
| stake_fraction                 | decimal | `"1.0"` | fraction of equity deployed        | fraction | no           | `concentrated.py:246` |

Feature inputs: `lp_pool_sqrt_price_<pool>`, `lp_pool_token0_price_usd_<pool>`, `lp_pool_token1_price_usd_<pool>`.

### DEFI_LP_POOL — `engine/strategies/v2/defi_lp/pool.py`

Engine `DefiLpPoolEngine` (`pool.py:69`). FAMILY=MARKET_MAKING. Kelly = 0.500. No-op until `pool_address` + `venue`.

| name           | type    | default | range / enum                       | units    | required     | source        |
| -------------- | ------- | ------- | ---------------------------------- | -------- | ------------ | ------------- |
| pool_address   | str     | `""`    | pool contract; no-op when empty    | address  | yes (action) | `pool.py:106` |
| venue          | str     | `""`    | CURVE / BALANCER_V2 / BALANCER_V3  | venue    | yes (action) | `pool.py:107` |
| depeg_exit_bps | decimal | `"50"`  | withdraw if invariant drift ≥ this | bps      | no           | `pool.py:113` |
| stake_fraction | decimal | `"1.0"` | fraction of equity deployed        | fraction | no           | `pool.py:114` |

Feature input: `lp_pool_invariant_drift_bps_<pool>`.

### DEFI_LP_VAULT — `engine/strategies/v2/defi_lp/vault.py`

Engine `DefiLpVaultEngine` (`vault.py:61`). FAMILY=MARKET_MAKING. Kelly = 0.750. No-op until `vault_address` + `venue`.

| name             | type    | default | range / enum                     | units    | required     | source         |
| ---------------- | ------- | ------- | -------------------------------- | -------- | ------------ | -------------- |
| vault_address    | str     | `""`    | ERC-4626 vault; no-op when empty | address  | yes (action) | `vault.py:101` |
| venue            | str     | `""`    | YEARN_V3 / MORPHO / ...          | venue    | yes (action) | `vault.py:102` |
| min_apy_bps      | decimal | `"100"` | exit if realised APY < this      | bps      | no           | `vault.py:112` |
| max_drawdown_bps | decimal | `"500"` | exit if drawdown ≥ this          | bps      | no           | `vault.py:113` |
| stake_fraction   | decimal | `"1.0"` | fraction of equity deployed      | fraction | no           | `vault.py:114` |

Feature inputs: `vault_share_price_<vault>`, `vault_share_price_apy_bps_<vault>`, `vault_drawdown_bps_<vault>`.

---

## New VOL\_\* archetypes (this week)

Engines under `engine/strategies/v2/vol_trading/`. Convention: option-leg `*_instrument` params are **required for
action** (engine `return []` when absent); `*_venue` defaults to the current on-tick option venue (not a literal);
`max_slippage_bps` is an int with a per-engine default. No VOL engine declares a `REQUIRED_PARAMS` frozenset (the
instrument gating is a `get(...) is None → []` no-op). Kelly: VOL_TRADING_OPTIONS = 0.250 (others not yet in
`KELLY_FRACTION_BY_ARCHETYPE`, `archetype_defaults.py:98` — `V1_ARCHETYPES_IN_SCOPE` gates).

| archetype                  | name                                                                     | type    | default          | units          | required                  | source                                         |
| -------------------------- | ------------------------------------------------------------------------ | ------- | ---------------- | -------------- | ------------------------- | ---------------------------------------------- |
| VOL_CARRY                  | call_instrument / put_instrument                                         | str     | (none)           | instrument     | yes (action)              | `vol_trading/carry.py:107,108`                 |
| VOL_CARRY                  | entry_vrp                                                                | decimal | `0.04`           | vol-frac       | no                        | `vol_trading/carry.py:113`                     |
| VOL_CARRY                  | exit_vrp                                                                 | decimal | `0.01`           | vol-frac       | no                        | `vol_trading/carry.py:114`                     |
| VOL_CARRY                  | vega_budget_per_leg                                                      | decimal | `10`             | vega           | no                        | `vol_trading/carry.py:144`                     |
| VOL_CARRY                  | hedge_instrument                                                         | str     | (none)           | instrument     | no                        | `vol_trading/carry.py:167`                     |
| VOL_CARRY                  | hedge_venue                                                              | str     | (option venue)   | venue          | no                        | `vol_trading/carry.py:170`                     |
| VOL_CARRY                  | max_slippage_bps                                                         | int     | `50`             | bps            | no                        | `vol_trading/carry.py:190`                     |
| VOL_TRADING_OPTIONS        | call_instrument / put_instrument                                         | str     | (none)           | instrument     | yes (action)              | `vol_trading/options.py:71,72`                 |
| VOL_TRADING_OPTIONS        | divergence_bps                                                           | decimal | `500`            | bps            | no                        | `vol_trading/options.py:76`                    |
| VOL_TRADING_OPTIONS        | stake_vega_notional                                                      | decimal | `1000`           | vega-notional  | no                        | `vol_trading/options.py:81`                    |
| VOL_TRADING_OPTIONS        | max_slippage_bps                                                         | int     | `50`             | bps            | no                        | `vol_trading/options.py:82`                    |
| VOL_STRADDLE               | call_instrument / put_instrument                                         | str     | (none)           | instrument     | yes (action)              | `vol_trading/straddle.py:115,116`              |
| VOL_STRADDLE               | entry_vol_gap                                                            | decimal | `0.03`           | vol-frac       | no                        | `vol_trading/straddle.py:120`                  |
| VOL_STRADDLE               | max_slippage_bps                                                         | int     | `50`             | bps            | no                        | `vol_trading/straddle.py:159`                  |
| VOL_STRADDLE               | vega_budget_per_leg                                                      | decimal | `10`             | vega           | no                        | `vol_trading/straddle.py:179`                  |
| VOL_STRADDLE               | max_position_vega                                                        | decimal | `0` (0=uncapped) | vega           | no                        | `vol_trading/straddle.py:182`                  |
| VOL_RATIO_SPREAD           | entry_skew                                                               | decimal | `0.02`           | vol-skew       | no                        | `vol_trading/ratio_spread.py:82`               |
| VOL_RATIO_SPREAD           | atm_put / otm_put / atm_call / otm_call \_instrument                     | str     | (none)           | instrument     | yes (side-dependent)      | `vol_trading/ratio_spread.py:90,91,94,95`      |
| VOL_RATIO_SPREAD           | base_units                                                               | decimal | `5`              | units          | no                        | `vol_trading/ratio_spread.py:99`               |
| VOL_RATIO_SPREAD           | ratio                                                                    | decimal | `2`              | ratio (>1)     | no                        | `vol_trading/ratio_spread.py:100`              |
| VOL_RATIO_SPREAD           | max_slippage_bps                                                         | int     | `60`             | bps            | no                        | `vol_trading/ratio_spread.py:137`              |
| VOL_SYNTHETIC_DELTA        | call_instrument / put_instrument                                         | str     | (none)           | instrument     | yes (action)              | `vol_trading/synthetic_delta.py:93,94`         |
| VOL_SYNTHETIC_DELTA        | min_signal                                                               | float   | `0.0`            | signal [0,1]   | no                        | `vol_trading/synthetic_delta.py:97`            |
| VOL_SYNTHETIC_DELTA        | synthetic_units                                                          | decimal | `10`             | units          | no                        | `vol_trading/synthetic_delta.py:107`           |
| VOL_SYNTHETIC_DELTA        | max_slippage_bps                                                         | int     | `50`             | bps            | no                        | `vol_trading/synthetic_delta.py:143`           |
| VOL_0DTE_GAMMA_SCALPING    | call_instrument / put_instrument                                         | str     | (none)           | instrument     | yes (action)              | `vol_trading/gamma_scalping_0dte.py:99,100`    |
| VOL_0DTE_GAMMA_SCALPING    | entry_gamma_gap                                                          | decimal | `0.05`           | gamma-frac     | no                        | `vol_trading/gamma_scalping_0dte.py:105`       |
| VOL_0DTE_GAMMA_SCALPING    | exit_gamma_gap                                                           | decimal | `0.0`            | gamma-frac     | no                        | `vol_trading/gamma_scalping_0dte.py:106`       |
| VOL_0DTE_GAMMA_SCALPING    | gamma_units                                                              | decimal | `10`             | units          | no                        | `vol_trading/gamma_scalping_0dte.py:130`       |
| VOL_0DTE_GAMMA_SCALPING    | rehedge_delta                                                            | decimal | `0.10`           | delta-frac     | no                        | `vol_trading/gamma_scalping_0dte.py:169`       |
| VOL_0DTE_GAMMA_SCALPING    | hedge_instrument                                                         | str     | (none)           | instrument     | no                        | `vol_trading/gamma_scalping_0dte.py:224`       |
| VOL_0DTE_GAMMA_SCALPING    | hedge_venue                                                              | str     | (option venue)   | venue          | no                        | `vol_trading/gamma_scalping_0dte.py:230`       |
| VOL_0DTE_GAMMA_SCALPING    | max_slippage_bps                                                         | int     | `40`             | bps            | no                        | `vol_trading/gamma_scalping_0dte.py:270`       |
| VOL_ARB_RV_IV              | call_instrument / put_instrument                                         | str     | (none)           | instrument     | yes (action)              | `vol_trading/arb_rv_iv.py:100,101`             |
| VOL_ARB_RV_IV              | entry_gap                                                                | decimal | `0.03`           | vol-frac       | no                        | `vol_trading/arb_rv_iv.py:106`                 |
| VOL_ARB_RV_IV              | vega_budget_per_leg                                                      | decimal | `10`             | vega           | no                        | `vol_trading/arb_rv_iv.py:113`                 |
| VOL_ARB_RV_IV              | max_slippage_bps                                                         | int     | `50`             | bps            | no                        | `vol_trading/arb_rv_iv.py:148`                 |
| VOL_ARB_RV_IV              | hedge_instrument                                                         | str     | (none)           | instrument     | no                        | `vol_trading/arb_rv_iv.py:162`                 |
| VOL_ARB_RV_IV              | hedge_venue                                                              | str     | (option venue)   | venue          | no                        | `vol_trading/arb_rv_iv.py:180`                 |
| VOL_ML_LEAN                | call_instrument / put_instrument                                         | str     | (none)           | instrument     | yes (action)              | `vol_trading/ml_lean.py:93,94`                 |
| VOL_ML_LEAN                | vol_model_id                                                             | str     | `""`             | model-id       | no                        | `vol_trading/ml_lean.py:98`                    |
| VOL_ML_LEAN                | min_confidence                                                           | float   | `0.55`           | conf [0,1]     | no                        | `vol_trading/ml_lean.py:104`                   |
| VOL_ML_LEAN                | vega_budget_per_leg                                                      | decimal | `10`             | vega           | no                        | `vol_trading/ml_lean.py:114`                   |
| VOL_ML_LEAN                | max_slippage_bps                                                         | int     | `50`             | bps            | no                        | `vol_trading/ml_lean.py:147`                   |
| VOL_MARKET_MAKING          | quote_instrument                                                         | str     | (none)           | instrument     | yes (action)              | `vol_trading/market_making.py:83`              |
| VOL_MARKET_MAKING          | quote_half_spread_vol                                                    | decimal | `0.02`           | vol-frac       | no                        | `vol_trading/market_making.py:87`              |
| VOL_MARKET_MAKING          | inventory_skew_vol                                                       | decimal | `0.01`           | vol-frac       | no                        | `vol_trading/market_making.py:88`              |
| VOL_MARKET_MAKING          | max_inventory                                                            | decimal | `50`             | vega           | no                        | `vol_trading/market_making.py:89`              |
| VOL_MARKET_MAKING          | quote_size                                                               | decimal | `5`              | vega           | no                        | `vol_trading/market_making.py:90`              |
| VOL_MARKET_MAKING          | max_slippage_bps                                                         | int     | `30`             | bps            | no                        | `vol_trading/market_making.py:143`             |
| VOL_DISPERSION             | reference_correlation_iv                                                 | float   | `0.0`            | corr [0,1]     | no                        | `vol_trading/dispersion.py:111`                |
| VOL_DISPERSION             | index_call / index_put                                                   | str     | (none)           | instrument     | yes (action)              | `vol_trading/dispersion.py:114,115`            |
| VOL_DISPERSION             | entry_disp_gap                                                           | decimal | `0.03`           | vol-frac       | no                        | `vol_trading/dispersion.py:121`                |
| VOL_DISPERSION             | disp_vega_units                                                          | decimal | `10`             | vega           | no                        | `vol_trading/dispersion.py:128`                |
| VOL_DISPERSION             | component_call / component_put                                           | str     | (none)           | instrument     | no                        | `vol_trading/dispersion.py:152,153`            |
| VOL_DISPERSION             | max_slippage_bps                                                         | int     | `75`             | bps            | no                        | `vol_trading/dispersion.py:187`                |
| VOL_VARIANCE_SWAP          | call_wing / put_wing / atm_straddle_call / atm_straddle_put \_instrument | str     | (none)           | instrument     | yes (action)              | `vol_trading/variance_swap.py:143,144,145,146` |
| VOL_VARIANCE_SWAP          | skew_loading                                                             | float   | `0.5`            | weight [0,1]   | no                        | `vol_trading/variance_swap.py:151`             |
| VOL_VARIANCE_SWAP          | entry_var_gap                                                            | decimal | `0.01`           | var-frac       | no                        | `vol_trading/variance_swap.py:155`             |
| VOL_VARIANCE_SWAP          | max_slippage_bps                                                         | int     | `75`             | bps            | no                        | `vol_trading/variance_swap.py:172`             |
| VOL_VARIANCE_SWAP          | variance_notional                                                        | decimal | `10`             | notional       | no                        | `vol_trading/variance_swap.py:197`             |
| VOL_VARIANCE_SWAP          | call_wing_moneyness                                                      | decimal | `1.10`           | moneyness (>1) | no                        | `vol_trading/variance_swap.py:200`             |
| VOL_VARIANCE_SWAP          | put_wing_moneyness                                                       | decimal | `0.90`           | moneyness (<1) | no                        | `vol_trading/variance_swap.py:201`             |
| VOL_TERM_STRUCTURE_ARB     | near_instrument / far_instrument                                         | str     | (none)           | instrument     | yes (action)              | `vol_trading/term_structure_arb.py:105,106`    |
| VOL_TERM_STRUCTURE_ARB     | entry_term_gap                                                           | decimal | `0.02`           | vol-frac       | no                        | `vol_trading/term_structure_arb.py:111`        |
| VOL_TERM_STRUCTURE_ARB     | max_slippage_bps                                                         | int     | `60`             | bps            | no                        | `vol_trading/term_structure_arb.py:150`        |
| VOL_TERM_STRUCTURE_ARB     | calendar_vega_units                                                      | decimal | `10`             | vega           | no                        | `vol_trading/term_structure_arb.py:170`        |
| VOL_TERM_STRUCTURE_SLOPE   | near_instrument / far_instrument                                         | str     | (none)           | instrument     | yes (action)              | `vol_trading/term_structure_slope.py:92,93`    |
| VOL_TERM_STRUCTURE_SLOPE   | neutral_slope                                                            | float   | `0.0`            | vol/time       | no                        | `vol_trading/term_structure_slope.py:96`       |
| VOL_TERM_STRUCTURE_SLOPE   | entry_slope_gap                                                          | decimal | `0.01`           | vol/time       | no                        | `vol_trading/term_structure_slope.py:100`      |
| VOL_TERM_STRUCTURE_SLOPE   | slope_vega_units                                                         | decimal | `10`             | vega           | no                        | `vol_trading/term_structure_slope.py:111`      |
| VOL_TERM_STRUCTURE_SLOPE   | max_slippage_bps                                                         | int     | `60`             | bps            | no                        | `vol_trading/term_structure_slope.py:143`      |
| VOL_CROSS_ASSET_SPREAD     | asset_a_call / asset_a_put / asset_b_call / asset_b_put                  | str     | (none)           | instrument     | yes (action)              | `vol_trading/cross_asset_spread.py:93`         |
| VOL_CROSS_ASSET_SPREAD     | reference_spread                                                         | float   | `0.0`            | vol-frac       | no                        | `vol_trading/cross_asset_spread.py:98`         |
| VOL_CROSS_ASSET_SPREAD     | entry_spread_gap                                                         | decimal | `0.03`           | vol-frac       | no                        | `vol_trading/cross_asset_spread.py:102`        |
| VOL_CROSS_ASSET_SPREAD     | spread_vega_units                                                        | decimal | `10`             | vega           | no                        | `vol_trading/cross_asset_spread.py:110`        |
| VOL_CROSS_ASSET_SPREAD     | max_slippage_bps                                                         | int     | `75`             | bps            | no                        | `vol_trading/cross_asset_spread.py:158`        |
| VOL_LEAPS_CONVEXITY        | call_instrument / put_instrument                                         | str     | (none)           | instrument     | yes (action)              | `vol_trading/leaps_convexity.py:91,92`         |
| VOL_LEAPS_CONVEXITY        | entry_convexity_gap                                                      | decimal | `0.02`           | vol-frac       | no                        | `vol_trading/leaps_convexity.py:97`            |
| VOL_LEAPS_CONVEXITY        | convexity_vega_units                                                     | decimal | `10`             | vega           | no                        | `vol_trading/leaps_convexity.py:101`           |
| VOL_LEAPS_CONVEXITY        | max_slippage_bps                                                         | int     | `60`             | bps            | no                        | `vol_trading/leaps_convexity.py:131`           |
| VOL_SPREAD_STRUCTURES      | structure_units                                                          | decimal | `5`              | units          | no                        | `vol_trading/spread_structures.py:112`         |
| VOL_SPREAD_STRUCTURES      | skew_threshold                                                           | decimal | `0.03`           | vol-skew       | no                        | `vol_trading/spread_structures.py:116`         |
| VOL_SPREAD_STRUCTURES      | rich_iv_threshold                                                        | decimal | `0.55`           | vol-frac       | no                        | `vol_trading/spread_structures.py:117`         |
| VOL_SPREAD_STRUCTURES      | max_slippage_bps                                                         | int     | `70`             | bps            | no                        | `vol_trading/spread_structures.py:133`         |
| VOL_SPREAD_STRUCTURES      | atm_put / otm_put / atm_call / otm_call / far_otm_call / far_otm_put     | str     | (none)           | instrument     | yes (structure-dependent) | `vol_trading/spread_structures.py:~149,~176`   |
| VOL_OVERLAY_COVERED_CALLS  | call_instrument                                                          | str     | (none)           | instrument     | yes (action)              | `vol_trading/overlay_covered_calls.py:82`      |
| VOL_OVERLAY_COVERED_CALLS  | min_call_iv                                                              | decimal | `0.40`           | vol-frac       | no                        | `vol_trading/overlay_covered_calls.py:86`      |
| VOL_OVERLAY_COVERED_CALLS  | call_write_units                                                         | decimal | `10`             | units          | no                        | `vol_trading/overlay_covered_calls.py:90`      |
| VOL_OVERLAY_COVERED_CALLS  | cover_instrument                                                         | str     | (none)           | instrument     | no                        | `vol_trading/overlay_covered_calls.py:106`     |
| VOL_OVERLAY_COVERED_CALLS  | assume_existing_cover                                                    | bool    | `false`          | —              | no                        | `vol_trading/overlay_covered_calls.py:107`     |
| VOL_OVERLAY_COVERED_CALLS  | cover_units                                                              | decimal | `1`              | units          | no                        | `vol_trading/overlay_covered_calls.py:109`     |
| VOL_OVERLAY_COVERED_CALLS  | cover_venue                                                              | str     | (option venue)   | venue          | no                        | `vol_trading/overlay_covered_calls.py:111`     |
| VOL_OVERLAY_COVERED_CALLS  | max_slippage_bps                                                         | int     | `50`             | bps            | no                        | `vol_trading/overlay_covered_calls.py:129`     |
| VOL_OVERLAY_PROTECTIVE_PUT | put_instrument                                                           | str     | (none)           | instrument     | yes (action)              | `vol_trading/overlay_protective_put.py:80`     |
| VOL_OVERLAY_PROTECTIVE_PUT | max_put_iv                                                               | decimal | `0.60`           | vol-frac       | no                        | `vol_trading/overlay_protective_put.py:84`     |
| VOL_OVERLAY_PROTECTIVE_PUT | put_buy_units                                                            | decimal | `10`             | units          | no                        | `vol_trading/overlay_protective_put.py:88`     |
| VOL_OVERLAY_PROTECTIVE_PUT | hold_instrument                                                          | str     | (none)           | instrument     | no                        | `vol_trading/overlay_protective_put.py:104`    |
| VOL_OVERLAY_PROTECTIVE_PUT | assume_existing_long                                                     | bool    | `false`          | —              | no                        | `vol_trading/overlay_protective_put.py:105`    |
| VOL_OVERLAY_PROTECTIVE_PUT | protected_units                                                          | decimal | `1`              | units          | no                        | `vol_trading/overlay_protective_put.py:107`    |
| VOL_OVERLAY_PROTECTIVE_PUT | hold_venue                                                               | str     | (option venue)   | venue          | no                        | `vol_trading/overlay_protective_put.py:109`    |
| VOL_OVERLAY_PROTECTIVE_PUT | max_slippage_bps                                                         | int     | `50`             | bps            | no                        | `vol_trading/overlay_protective_put.py:128`    |

---

## New MARKET*MAKING*\* archetypes (this week)

Engines under `engine/strategies/v2/market_making/`. `skew_on_inventory` bool idiom = `self.params.get(key, "1") != "0"`
(default true). `MARKET_MAKING_CONTINUOUS` Kelly = 0.500; `MARKET_MAKING_EVENT_SETTLED` Kelly = 0.375. **Not yet in
`ARCHETYPE_ENGINE_REGISTRY`** (code-complete, unit-tested, not live-deployable): PASSIVE_SPREAD, PREDICTION,
QUEUE_MICROSTRUCTURE (per source notes; see Findings F3).

| archetype                          | name                             | type    | default            | units        | required     | source                                      |
| ---------------------------------- | -------------------------------- | ------- | ------------------ | ------------ | ------------ | ------------------------------------------- |
| MARKET_MAKING_CONTINUOUS           | min_mid_price                    | decimal | `0.0001`           | price        | no           | `market_making/continuous.py:61`            |
| MARKET_MAKING_CONTINUOUS           | half_spread_bps                  | int     | `10`               | bps          | no           | `market_making/continuous.py:67`            |
| MARKET_MAKING_CONTINUOUS           | max_inventory_abs                | decimal | `1.0`              | units        | no           | `market_making/continuous.py:68`            |
| MARKET_MAKING_CONTINUOUS           | refresh_cadence_ms               | int     | `1000`             | ms           | no           | `market_making/continuous.py:69`            |
| MARKET_MAKING_CONTINUOUS           | skew_on_inventory                | bool    | `true` ("0"=false) | —            | no           | `market_making/continuous.py:70`            |
| MARKET_MAKING_EVENT_SETTLED        | min_mid_price                    | decimal | `0.0001`           | price        | no           | `market_making/event_settled.py:81`         |
| MARKET_MAKING_EVENT_SETTLED        | back_instrument / lay_instrument | str     | `""` (empty → [])  | instrument   | yes (action) | `market_making/event_settled.py:85,86`      |
| MARKET_MAKING_EVENT_SETTLED        | half_spread_bps                  | int     | `30`               | bps          | no           | `market_making/event_settled.py:90`         |
| MARKET_MAKING_EVENT_SETTLED        | max_inventory_abs                | decimal | `100`              | units        | no           | `market_making/event_settled.py:91`         |
| MARKET_MAKING_EVENT_SETTLED        | refresh_cadence_ms               | int     | `5000`             | ms           | no           | `market_making/event_settled.py:92`         |
| MARKET_MAKING_EVENT_SETTLED        | skew_on_inventory                | bool    | `true` ("0"=false) | —            | no           | `market_making/event_settled.py:93`         |
| MARKET_MAKING_EVENT_SETTLED        | refresh_threshold_bps            | int     | `25`               | bps          | no           | `market_making/event_settled.py:145`        |
| MARKET_MAKING_INVENTORY_SKEW       | min_half_spread_bps              | int     | `5`                | bps          | no           | `market_making/inventory_skew.py:80`        |
| MARKET_MAKING_INVENTORY_SKEW       | spread_capture_frac              | decimal | `0.5`              | frac [0,1]   | no           | `market_making/inventory_skew.py:82`        |
| MARKET_MAKING_INVENTORY_SKEW       | quote_instrument                 | str     | (none)             | instrument   | yes (action) | `market_making/inventory_skew.py:107`       |
| MARKET_MAKING_INVENTORY_SKEW       | quote_size                       | decimal | `1`                | units        | no           | `market_making/inventory_skew.py:111`       |
| MARKET_MAKING_INVENTORY_SKEW       | max_inventory                    | decimal | `10`               | units        | no           | `market_making/inventory_skew.py:112`       |
| MARKET_MAKING_INVENTORY_SKEW       | inventory_target                 | decimal | `0`                | units        | no           | `market_making/inventory_skew.py:120`       |
| MARKET_MAKING_INVENTORY_SKEW       | inventory_skew                   | decimal | `1.0`              | half-spreads | no           | `market_making/inventory_skew.py:121`       |
| MARKET_MAKING_INVENTORY_SKEW       | imbalance_tilt                   | decimal | `0.5`              | half-spreads | no           | `market_making/inventory_skew.py:122`       |
| MARKET_MAKING_INVENTORY_SKEW       | max_slippage_bps                 | int     | `30`               | bps          | no           | `market_making/inventory_skew.py:175`       |
| MARKET_MAKING_ML_LEAN              | min_half_spread_bps              | int     | `5`                | bps          | no           | `market_making/ml_lean.py:96`               |
| MARKET_MAKING_ML_LEAN              | spread_capture_frac              | decimal | `0.5`              | frac [0,1]   | no           | `market_making/ml_lean.py:98`               |
| MARKET_MAKING_ML_LEAN              | mm_model_id                      | str     | `""`               | model-id     | no           | `market_making/ml_lean.py:110`              |
| MARKET_MAKING_ML_LEAN              | min_confidence                   | float   | `0.55`             | conf [0,1]   | no           | `market_making/ml_lean.py:115`              |
| MARKET_MAKING_ML_LEAN              | quote_instrument                 | str     | (none)             | instrument   | yes (action) | `market_making/ml_lean.py:142`              |
| MARKET_MAKING_ML_LEAN              | quote_size                       | decimal | `1`                | units        | no           | `market_making/ml_lean.py:146`              |
| MARKET_MAKING_ML_LEAN              | lean_skew                        | decimal | `1.0`              | half-spreads | no           | `market_making/ml_lean.py:154`              |
| MARKET_MAKING_ML_LEAN              | lean_size                        | decimal | `0.5`              | frac [0,1]   | no           | `market_making/ml_lean.py:155`              |
| MARKET_MAKING_ML_LEAN              | max_slippage_bps                 | int     | `30`               | bps          | no           | `market_making/ml_lean.py:202`              |
| MARKET_MAKING_PASSIVE_SPREAD       | quote_instrument                 | str     | (none)             | instrument   | yes (action) | `market_making/passive_spread.py:112`       |
| MARKET_MAKING_PASSIVE_SPREAD       | min_half_spread_bps              | int     | `5`                | bps          | no           | `market_making/passive_spread.py:84`        |
| MARKET_MAKING_PASSIVE_SPREAD       | spread_capture_frac              | decimal | `0.5`              | frac [0,1]   | no           | `market_making/passive_spread.py:86`        |
| MARKET_MAKING_PASSIVE_SPREAD       | quote_size                       | decimal | `1`                | units        | no           | `market_making/passive_spread.py:116`       |
| MARKET_MAKING_PASSIVE_SPREAD       | max_slippage_bps                 | int     | `30`               | bps          | no           | `market_making/passive_spread.py:155`       |
| MARKET_MAKING_PREDICTION           | quote_instrument                 | str     | (none)             | instrument   | yes (action) | `market_making/prediction.py:143`           |
| MARKET_MAKING_PREDICTION           | mm_model_id                      | str     | `""`               | model-id     | no           | `market_making/prediction.py:109`           |
| MARKET_MAKING_PREDICTION           | min_confidence                   | float   | `0.55`             | conf [0,1]   | no           | `market_making/prediction.py:114`           |
| MARKET_MAKING_PREDICTION           | prediction_skew                  | decimal | `1.0`              | half-spreads | no           | `market_making/prediction.py:116`           |
| MARKET_MAKING_PREDICTION           | min_half_spread_bps              | int     | `5`                | bps          | no           | `market_making/prediction.py:94`            |
| MARKET_MAKING_PREDICTION           | spread_capture_frac              | decimal | `0.5`              | frac [0,1]   | no           | `market_making/prediction.py:96`            |
| MARKET_MAKING_PREDICTION           | quote_size                       | decimal | `1`                | units        | no           | `market_making/prediction.py:147`           |
| MARKET_MAKING_PREDICTION           | max_slippage_bps                 | int     | `30`               | bps          | no           | `market_making/prediction.py:188`           |
| MARKET_MAKING_QUEUE_MICROSTRUCTURE | quote_instrument                 | str     | (none)             | instrument   | yes (action) | `market_making/queue_microstructure.py:115` |
| MARKET_MAKING_QUEUE_MICROSTRUCTURE | max_queue_ahead                  | decimal | `100`              | size         | no           | `market_making/queue_microstructure.py:134` |
| MARKET_MAKING_QUEUE_MICROSTRUCTURE | flow_skew                        | decimal | `0.5`              | half-spreads | no           | `market_making/queue_microstructure.py:135` |
| MARKET_MAKING_QUEUE_MICROSTRUCTURE | min_half_spread_bps              | int     | `5`                | bps          | no           | `market_making/queue_microstructure.py:88`  |
| MARKET_MAKING_QUEUE_MICROSTRUCTURE | spread_capture_frac              | decimal | `0.5`              | frac [0,1]   | no           | `market_making/queue_microstructure.py:90`  |
| MARKET_MAKING_QUEUE_MICROSTRUCTURE | quote_size                       | decimal | `1`                | units        | no           | `market_making/queue_microstructure.py:127` |
| MARKET_MAKING_QUEUE_MICROSTRUCTURE | max_slippage_bps                 | int     | `30`               | bps          | no           | `market_making/queue_microstructure.py:196` |

---

## Prod-vs-testing functional-alignment check (CSB / APD / basis-perp)

Method: compare the params the e2e catalog/slots/scenarios SET against the engine DEFAULTS for the params e2e does NOT
set. A divergence is FUNCTIONAL (not name-mismatch) when an unset param would behave differently in a real paper/prod
run than the smoke intent. e2e configs for these three are mostly **hand-authored** in the smoke tests (direct engine
instantiation with a literal `params={}`), with scenario-JSON + `_stepper_engine.resolve_strategy_type(...)` pulling the
strategy-service catalog for the stepper path.

### CARRY_STAKED_BASIS — defaults align (with one note)

- `test_csb_paper_e2e_smoke.py` sets `entry_bps="200"`, `exit_bps="50"` — **identical to engine defaults**
  (`staked_basis.py:293,294`).
- `min_health_factor`: NOT set by the smoke baseline → engine default `"1.25"` (`staked_basis.py:263`). The scenario
  JSONs (`csb_staked_basis_eth.json:12`, `_lst_accepted.json:12`) set it **explicitly to `"1.25"`** — so the unset smoke
  path and the explicit scenario path **converge on the same value**. Aligned.
- `hedge_deadline_ms` (default `5000`) and `peg_drift_threshold_bps` (default `"25"`): unset by all e2e CSB configs →
  engine defaults. Both are operationally-safe defaults a real run would accept; **no functional divergence**.
- `start_token`: smoke sets `"USDC"`; engine default is `"USDC"`. Aligned.
- **Verdict: DEFAULTS ALIGN.** No CSB param where the engine default diverges functionally from a paper/prod intent.

### ARBITRAGE_PRICE_DISPERSION — one functional divergence (smoke is more aggressive than engine/catalog default)

- The smoke tests (`test_apd_paper_e2e_smoke.py:66,67`; `test_failure_modes`, `test_additional_asset_groups`,
  `test_concurrent_archetype`) set **`dispersion_bps="20"`, `cost_bps="5"`**, whereas the **engine defaults are
  `dispersion_bps="30"`, `cost_bps="10"`** (`price_dispersion.py:200,201`) — and the scenario JSON
  (`apd_price_dispersion_btc.json:10,11`), the wizard backtest default (`backtest_from_wizard_config.py:32`), the
  `scenario_stepper.py:29` default, and the `_stepper_engine.py:345,346` read-defaults all use **30/10**. → **FUNCTIONAL
  DIVERGENCE**: a production/paper run that does NOT explicitly override these uses the engine default `30/10` — a
  **higher (more conservative) entry threshold and a larger assumed cost** than the smoke's `20/5`. A real run intending
  the smoke's looser threshold MUST set these explicitly; otherwise it trades less often. Direction is **conservative**
  (engine default is stricter), so it is fail-safe, not unsafe — but it IS a real behavioural delta the wizard must
  surface (it is a default the wizard should pre-fill from the engine, = 30/10, not from the smoke = 20/5).
- `hedge_deadline_ms`: smoke `"2000"` vs engine default `5000` vs scenario JSON `"5000"`. Unset → 5000. Cosmetic (hedge
  deadline tolerance), not edge-affecting.
- The live **APD catalog slot** (`archetype_slots_defi.py:361,393` — `APD`/`arbitrage_price_dispersion`) runs the
  **funding-rate-dispersion** path and sets `target_leverage="5.0"`, `min_spread_threshold_bps="5.0"`,
  `max_concurrent_pairs_per_slot="5"`, all `vol_cap_clamp_*` keys, and `stake_fraction="0.1"` — every value **matches
  the engine default** (`price_dispersion.py:432,361,362,533-538,466`). The price-dispersion smoke path and the
  funding-rate-dispersion catalog path are different code branches; the catalog (prod) path is fully aligned.
- **Verdict: ONE DIVERGENCE** — `dispersion_bps`/`cost_bps` (smoke 20/5 vs engine+catalog 30/10). Phase C should emit
  `30/10` (the engine default) as the wizard pre-fill, NOT the smoke value.

### CARRY_BASIS_PERP — defaults align

- `backtest_solana_basis.py` CLI defaults: `entry_funding_bps="50"`, `exit_funding_bps="10"`, `stake_fraction="0.5"` —
  **identical to engine defaults** (`basis_perp.py:72,73,74`); `min_mid_price="0.0001"` = engine default (`:63`).
- `colocated_engine.py` `SOL_BASIS`/`BTC_BASIS` slots set **none** of these → engine defaults `50/10/0.5/0.0001` apply.
  The DEFI*SLOTS catalog entries (`BASIS_TRADE`, `SOL_BASIS`, `BTC_BASIS`, `L2_BASIS`,
  `ENHANCED_BASIS*\*`—`archetype_slots_defi.py:64+`) set only routing keys (spot_venue/perp_venue/instrument/
  hold_policy), no threshold params → engine defaults apply.
- **Verdict: DEFAULTS ALIGN.**

---

## Findings (captured per the discovery-as-plan-todo rule — for the parent plan to triage)

- **F1 (P2, NICE-TO-HAVE)** — DEFI_SLOTS `RECURSIVE_STAKED_BASIS`/`UNHEDGED_RECURSIVE` pass `max_loops` in
  `initial_config` (`archetype_slots_defi.py:101,298`) but `CarryRecursiveStakedEngine` ignores it — `max_loops` is a
  hard-coded `10` in `_build_loop_legs` (`recursive_staked.py:397`). Dead catalog param; either wire it or drop it.
- **F2 (P2, NICE-TO-HAVE)** — Several DEFI_SLOTS keys are not engine params at all (e.g.
  `lending_venue`/`staking_venue`/ `flash_loan_venue`/`perp_hedge_enabled` for recursive;
  `range_policy`/`gas_aware_rebalance`/`pool_fee_bps`/ `rebalance_trigger`/`pool_type`/`range_width_pct` on the
  MARKET_MAKING_CONTINUOUS LP slots; `min_yield_diff_bps`/ `long_protocol`/`short_protocol`/`supports_flash_loans` on
  the ARBITRAGE_PRICE_DISPERSION lending-arb slots). They are legacy/aspirational config the current engines do not read
  — the wizard schema must be sourced from the **engine** param surface (this doc), not the catalog `initial_config`, to
  avoid emitting no-op fields.
- **F3 (P2, NICE-TO-HAVE)** — `MARKET_MAKING_PASSIVE_SPREAD`, `MARKET_MAKING_PREDICTION`,
  `MARKET_MAKING_QUEUE_MICROSTRUCTURE` are code-complete + unit-tested but NOT registered in `ARCHETYPE_ENGINE_REGISTRY`
  (per source notes). Phase C should gate their wizard exposure on registry membership (live-deployable set).
- **F4 (P1, feeds Phase C/wizard directly)** — APD `dispersion_bps`/`cost_bps` engine defaults (30/10) differ from the
  e2e smoke values (20/5). The wizard pre-fill MUST come from the engine default (30/10), not the smoke constant.
