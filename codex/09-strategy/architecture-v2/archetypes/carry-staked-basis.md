---
doc_type: codex-ssot
title: "Archetype: `CARRY_STAKED_BASIS`"
summary: >-
  Archetype CARRY_STAKED_BASIS: USDC-share-class market-neutral basis — SWAP -> STAKE -> TRANSFER LST as perp
  cross-margin -> SHORT perp, earning staking yield + funding at delta 0. LST_AS_MARGIN is the ONLY allowed structure
  (SPLIT_STAKE + COLLATERAL_BORROW deleted); eligibility DERIVED from VENUE_COLLATERAL_MATRIX (4 live slots 2026-05-20);
  staking APY from on-chain lst_rates, not vendor.
implementation_status: code-shipped
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, features-service, market-tick-data-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [strategy, carry, defi, cefi, execution, archetype, uac]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis-dated.md,
    ../families/carry-and-yield.md,
    ../cross-cutting/pnl-attribution.md,
    ../cross-cutting/restaking-reward-economics.md,
  ]
created: 2026-04-17
authoritative_for: [CARRY_STAKED_BASIS archetype specification (LST_AS_MARGIN staked basis)]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/defi/ethena-benchmark.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked-config-variants.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis-dated.md,
    /codex/09-strategy/architecture-v2/archetypes/yield-rotation-lending.md,
    /codex/09-strategy/architecture-v2/archetypes/yield-staking-simple.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: CARRY_STAKED_BASIS
family: CARRY_AND_YIELD
venue_universe: [LIDO, ROCKET_POOL, ETHERFI, JITO, MARINADE, DRIFT, DERIBIT, BYBIT, OKX, UNISWAP_V3, JUPITER]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 150
  min_sla_tier: premium
---

# Archetype: `CARRY_STAKED_BASIS`

> **Family:** [Carry & Yield](../families/carry-and-yield.md) **Settlement model:** Continuous; market-neutral
> multi-step paired position. **Code module (SHIPPED):**
> `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py`

## What it does

USDC-share-class market-neutral basis trade: deploy starting USDC into the native asset (ETH / SOL), stake into the LST,
transfer the LST to the perp venue as cross-margin, short the equivalent perp. Earn staking yield on the staked
principal + funding rate on the short. Delta = 0 because the perp short cancels the long underlying delta the LST
creates.

**Firm rule (post-2026-05-05):** the LST must be accepted as direct cross-margin at the perp venue, or the slot is
rejected at preflight. No SPLIT_STAKE fallback, no COLLATERAL_BORROW path. The execution structure is **`LST_AS_MARGIN`
only** — derived from the UAC venue collateral matrix at preflight, not user-chosen. Engine queries
[`unified_api_contracts.registry.venue_collateral.venue_accepts_collateral`](../../../../unified-api-contracts/unified_api_contracts/registry/venue_collateral.py)
on `(perp_venue, lst_asset)`; if False, the slot is rejected.

## Token / position flow — `LST_AS_MARGIN` (only allowed structure)

> **Hedge ratio (Phase 6B SHIPPED 2026-05-XX at `strategy-service@d6be15b`)** — hedge sizing is **DYNAMIC**:
> `eth_qty * lst_native_rate_now * (1 - margin_haircut)`. Per-tick adjustment via `compute_dynamic_hedge_ratio()` in
> `dynamic_hedge_ratio.py`, called from `on_tick` in `staked_basis.py`. LST exchange-rate stream covers jitoSOL/SOL,
> mSOL/SOL, bSOL/SOL, rETH/ETH, stETH/ETH, weETH/ETH. `peg_drift_threshold_bps` hysteresis band (default 25 bps ≈ 3σ
> daily) controls rebalance trigger. Staleness guard: if `lst_native_rate_ts` is >300s old, engine falls back to
> `lst_native_rate=1.0` and logs a warning. Full spec:
> [`../../../04-architecture/amm-slippage-simulation.md`](../../../04-architecture/amm-slippage-simulation.md) §
> "Hedge-ratio dynamic adjustment (Phase 6)".

```
1. SWAP (leader): USDC --> ETH/SOL on a spot venue (UNISWAP_V3, JUPITER, ...).
2. STAKE: ETH/SOL --> LST on the staking protocol.
3. TRANSFER: LST --> perp venue as cross-margin.
4. TRADE (hedge): SHORT perp_instrument equal-and-opposite to the LST principal.

   Net carry (USDC, annualised, bps):
       net_apy_bps = staking_apy_total + funding_apy - fees

       staking_apy_total combines base on-chain rate-diff + EIGEN restaking
       rewards + seasonal LST rewards minus dust slippage — see
       features-onchain `staking_apy_total` aggregator.
```

`stake_fraction` = `1.0` is the only meaningful value: the LST IS the perp margin, there is no spare USDC bucket. The
f-grid was a SPLIT_STAKE-era artefact and was retired with the deletion.

### Why SPLIT_STAKE was deleted (2026-05-05)

SPLIT_STAKE was the case where the perp venue did **not** accept the LST as margin, so the user staked half of starting
USDC into LST off-venue and posted the other half at the perp venue as USDC margin. It is **strictly dominated**:

- vs `CARRY_BASIS_PERP` at 2x size on the unstaked half: SPLIT_STAKE = `f·(staking + funding) + (1−f)·idle_yield`;
  basis-perp at 2x = `2·funding`. SPLIT_STAKE loses iff `funding > staking·f / (2−f)`. For f = 0.5 that's
  `funding > staking/3` — overwhelmingly the regime for MVP coins (BTC / ETH / SOL).
- vs `CARRY_RECURSIVE_STAKED`: when `staking > 3·funding` (the only regime where SPLIT_STAKE could beat basis-perp), the
  recursive variant wins by leverage — it amplifies the staking spread, SPLIT_STAKE doesn't.

There is no funding/staking regime where SPLIT_STAKE is the right answer; we removed it cleanly rather than carry the
flag.

### COLLATERAL_BORROW — also deleted (do NOT use)

Previous engine routed: stake LST → pledge as Aave collateral → borrow USDC → use that USDC as perp margin. **Removed
2026-05-04** because the stablecoin borrow rate (typically 5–8% APY) erodes the basis P&L faster than the staking +
funding earns it back. Same reasoning as SPLIT_STAKE: structurally narrower than the carry it's protecting.

## On-chain APY derivation (real, not vendor)

`staking_apy_bps` for both batch (tracer) and live (engine) is derived from MTDS `lst_rates` on-chain exchange-rate
ratio movement:

```
staking_apy_bps = ((rate[t] / rate[t-1])^365 - 1) * 1e4
```

`rate[t]` is the LST contract's current exchange rate (e.g. `getPooledEthByShares` for stETH, `getExchangeRate` for
rETH, `exchangeRate` for cbETH, on-chain method per LST captured in
[`market-tick-data-service/.../lst_rates_handler.py`](../../../../market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py)).
This is what the position would actually earn — not a DefiLlama-modelled or vendor-reported APY.

> **Non-goal: DefiLlama yields.** DefiLlama is a TVL / protocol-risk-context source only; it is **not** the LST APR
> source for this archetype. Staking APY is reconstructed from on-chain rate growth via the formula above and audited
> against the issuer's public endpoint where one exists (cbETH ↔ Coinbase `wrapped-assets/CBETH`, validated 0.00 bps
> drift on 2026-05-14). Empirical evidence + recommended decisions:
> [`plans/active/issues/lst_apr_sourcing_method_validated_2026_05_14.md`](../../../../plans/archive/issues/lst_apr_sourcing_method_validated_2026_05_14.md).

> **jitoSOL backtest window — clipped to 2023-10-01+ (resolved, default: clip).** The `oracle_prices` feed for
> jitoSOL-involving slots reads Pyth Hermes, whose archive API has no data before `ORACLE_COVERAGE_START["pyth_hermes"]`
> (2023-10-01) — an ~11-month gap vs. jitoSOL token genesis (2022-11-01). No Pythnet RPC historical-replay adapter is
> built to fill this gap (slow + expensive, no archive API); backtests over jitoSOL slots are clipped to the Hermes
> archive start rather than extended earlier. SSOT + override path:
> [`unified_api_contracts/registry/capability_declarations/_defi_oracle_coverage.py`](../../../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_oracle_coverage.py).

`funding_rate_apy_bps` = venue-published funding rate × cycles/day × 365 (pure arithmetic on raw venue data, no
modelling).

`usdc_idle_yield_apy_bps` = venue-specific USDC margin yield (HLP / HIP-3 funding rebate). **Not yet wired upstream** —
defaults to 0 until features-delta-one emits a `venue_funding_yield` series. Strategies running on USDC-margined venues
should treat current numbers as a conservative floor.

## Eligibility — derived, not declared

Adding a venue or LST to `VENUE_COLLATERAL_MATRIX` automatically expands the catalog's eligible slots on next
regeneration. No engine code changes, no catalog code changes — just a new matrix row.

Today's matrix (2026-05-20 — re-verified against `accepted_perp_collateral()` in UAC `venue_collateral.py`; original
2026-05-07 SSOT plan:
[`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](../../../../plans/archive/2026_05/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)):

| perp_venue                                                                                                       | LST acceptance                                                                                                                                                 | catalog rows produced (2026-05-20 actual) |
| ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| DRIFT                                                                                                            | JitoSOL (10% haircut), mSOL (10% haircut)                                                                                                                      | 2 rows                                    |
| DERIBIT                                                                                                          | stETH (7.5% haircut, X:PM/X:SM, offsets ETH-perp directly — effective 2026-01-13)                                                                              | 1 row                                     |
| BYBIT (UTA)                                                                                                      | stETH + wstETH (UTA cross-collateral per venue_collateral.py; METH + USDe are UTA-eligible but not in LST matrix)                                              | 1 row (LIDO/stETH only)                   |
| OKX (multi-currency / portfolio margin)                                                                          | wstETH — **confirmed in UAC venue_collateral.py since 2026-05-08 (Stream A flip)**; no catalog slot generated yet (OKX not in `_STAKED_BASIS_ETH_PERP_VENUES`) | 0 rows (slot pending)                     |
| HYPERLIQUID (L1)                                                                                                 | none (USDC-only) — explicit `accepted=False` rows                                                                                                              | 0 rows                                    |
| BINANCE (Multi-Assets Mode)                                                                                      | none — `BTC/ETH/BNB/XRP/ADA/DOT/SOL/USDC/USDT` only; cross-collateral feature retired                                                                          | 0 rows                                    |
| ASTER                                                                                                            | none — USDT/USDF/asBNB only                                                                                                                                    | 0 rows                                    |
| BINANCE-FUTURES / BYBIT-FUTURES / OKX-FUTURES / KRAKEN-FUTURES / BITFINEX-FUTURES / BITGET-FUTURES (Tardis-CeFi) | none — linear-USDT or coin-margined only; LST acceptance lives at the spot-UTA layer not the futures layer                                                     | 0 rows                                    |

**Effective slot count (2026-05-20 verified) = 4**: DRIFT/JitoSOL + DRIFT/mSOL + Deribit/stETH + Bybit/stETH. (Prior
"~7" estimate included Bybit/METH, Bybit/USDe, OKX/wstETH — those are not yet in the catalog.) This **supersedes the
prior 2026-05-05 claim** that DRIFT was the only venue.

**Per-venue wrap-step discipline (added 2026-05-12 per [`pnl-attribution.md`](../cross-cutting/pnl-attribution.md) HARD
RULE #5 "Staking yield: wrapped (price-delta) vs rebasing (balance-delta)")**: the on-chain `STAKE` leg shape depends on
the perp venue's accepted form:

| perp_venue                  | LST form                                                                                                | `STAKE` leg sequence                                                                                        | P&L attribution factor                                                                  |
| --------------------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| DRIFT (Solana)              | JitoSOL / mSOL (natively non-rebasing)                                                                  | `SWAP(USDC→SOL) → STAKE(SOL→jitoSOL via Jito stake pool) → TRANSFER(jitoSOL → Drift)` — no wrap step needed | `CARRY_BASE` (oracle price delta from Jito stake-pool getter)                           |
| DERIBIT                     | stETH (rebasing; Deribit absorbs daily rebase server-side via 7.5% haircut + offset-credit calibration) | `SWAP(USDC→ETH) → STAKE(Lido.submit → stETH) → TRANSFER(stETH → Deribit)` — NO wrap                         | `CARRY_BASE_REBASING` (position-balance-monitor reads Deribit subaccount balance delta) |
| BYBIT (UTA)                 | stETH + METH + USDe (rebasing; Bybit handles daily rebase at UTA layer)                                 | `SWAP(USDC→ETH) → STAKE(Lido.submit → stETH) → TRANSFER(stETH → Bybit UTA)` — NO wrap                       | `CARRY_BASE_REBASING` (position-balance-monitor reads Bybit UTA balance delta)          |
| OKX (multi-currency margin) | wstETH (wrapped non-rebasing — OKX has no daily-rebase reconciliation)                                  | `SWAP(USDC→ETH) → STAKE(Lido.submit → stETH → wstETH wrap via Lido wrap contract) → TRANSFER(wstETH → OKX)` | `CARRY_BASE` (oracle price delta from `wstETH.stEthPerToken()`)                         |

**Banned** at archetype `_build_legs` time:

- Posting wrapped `wstETH` to Bybit / Deribit — those venues calibrate their margin pricing on rebasing stETH; the
  wrapped form's price diverges from the underlying share-price and the venue's offset-credit math breaks.
- Posting rebasing `stETH` to OKX — OKX has no daily-rebase reconciliation; the position would mark as undersized every
  Lido rebase epoch (typically daily) and re-collateralization risk compounds.
- Treating jitoSOL / mSOL as needing a wrap step — they're natively non-rebasing, the issuer contract mints the
  rate-accreting form directly.

The archetype config (`default_basis_trade.yaml`) discriminator: each `(perp_venue, lst_asset)` row hardcodes whether
the `STAKE` leg includes the wrap step. This is part of the leg-sequence builder, not a runtime decision — the matrix
above is the SSOT.

**Why the prior claim was stale.** The 2026-05-05 SSOT comment in `unified-api-contracts/.../venue_collateral.py`
asserting _"NO production ETH-perp venue accepts an ETH LST as direct cross-margin today"_ predated three live venue
updates: Deribit's 2026-01-13 stETH cross-collateral haircut cut from 15% → 7.5% with explicit "stETH offsets ETH
derivative positions" wording; Bybit's 2024-02 stETH/METH UTA collateral additions and 2024-12-19 USDe addition (ratio
published to UTA spec page); and OKX's multi-currency-margin discount-rate list including wstETH. The doc-level
correction ships in this codex update; the matrix-level correction (with verified haircuts) ships in Stream A of the
named plan above.

**Phase 7a audit (operator-side) — STATUS: re-opened 2026-05-07.** The matrix encodes each individual (LST, perp_venue)
tuple — eETH/weETH ≠ stETH/wstETH ≠ rETH ≠ cbETH. Aave V3 takes weETH at 72.5% LTV but stETH only via the wstETH
wrapper, and Hyperliquid takes neither. Treating "ETH LSTs" as one bucket would lose every deployment decision the
matrix is supposed to make. Negative rows (`accepted=False`) are explicit so absences are self-documenting; positive
rows ship after Stream A's per-venue live-probe with haircut citations from the venue's risk-engine UI or docs URL.
Stream A's audit playbook lives at
[`/codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md`](../../../16-strategy-playbooks/defi/venue-collateral-2026-05-07.md)
(to be created by Stream A). Continuous-audit cadence (monthly?) is deferred to a separate plan named in Stream E
follow-throughs.

## Catalog axis (slot labels)

```
CARRY_STAKED_BASIS@{staking_protocol}-{perp_venue}-f{pct}-{stable}-1h-{stable}-v2-prod

Active slots (2026-05-20, post-Stream A):
  CARRY_STAKED_BASIS@jito-drift-f100-usdc-1h-usdc-v2-prod        # JitoSOL / DRIFT (Solana)
  CARRY_STAKED_BASIS@marinade-drift-f100-usdc-1h-usdc-v2-prod    # mSOL / DRIFT (Solana)
  CARRY_STAKED_BASIS@lido-deribit-f100-usdc-1h-usdc-v2-prod      # stETH / DERIBIT (ETH)
  CARRY_STAKED_BASIS@lido-bybit-f100-usdt-1h-usdt-v2-prod        # stETH / BYBIT UTA (ETH, USDT margin)
```

Note: the stable token differs per venue — USDC for DRIFT/DERIBIT, USDT for BYBIT UTA. This is resolved via
`_resolve_start_token(perp_venue, lst_asset)` in catalog.py.

**Pre-2026-05-07:** 2 slots (DRIFT/JitoSOL + DRIFT/mSOL). **Post-Stream A (2026-05-20):** 4 slots live (+ Deribit/stETH

- Bybit/stETH). Expected expansion to ~7 once OKX/wstETH + Bybit/METH haircut-verified per Stream A live probe. `f` is
  fixed at `100` (= 1.0) because LST_AS_MARGIN is the only allowed structure: the LST IS the perp margin, no spare USDC
  bucket. Built by `_build_carry_staked_basis` in
  [`strategy-service/.../target_universe/catalog.py`](../../../../strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py)
  from the matrix at module import — slot expansion is automatic once the matrix entries flip to `accepted=True`.

## Config schema

```yaml
share_class: USDC
capital_budget_share_class: USDC
capital_budget_amount: 1000000

# Required engine params (passed via initial_config dict):
# All 6 required params are validated at engine construction (__init__): ValueError is raised
# at boot if any are absent — earlier than tick-time preflight. Missing params cause immediate
# startup failure (not a silent default).
staking_protocol: JITO # live 2026-05-20: JITO / MARINADE (Solana) + LIDO (ETH, DERIBIT + BYBIT slots)
native_asset: SOL # SOL for Solana slots; ETH for DERIBIT/BYBIT slots
lst_asset: JitoSOL # JitoSOL / mSOL (Solana) · stETH (DERIBIT/BYBIT)
perp_venue:
  DRIFT # must appear in VENUE_COLLATERAL_MATRIX with the LST accepted=True
  # live venues: DRIFT (JitoSOL/mSOL) · DERIBIT (stETH) · BYBIT (stETH)
perp_instrument: SOL-PERP # SOL-PERP for Solana slots · ETH-PERP for ETH slots
spot_venue: JUPITER # USDC->native swap venue (JUPITER for Solana · UNISWAP_V3 for ETH)
start_token: USDC # entry token; must be in `accepted_perp_collateral(perp_venue)` (sanity check)
stake_fraction: "1.0" # always 1.0 post-2026-05-05 — LST is the perp margin

# Optional thresholds:
entry_bps: "200" # net carry must exceed this to enter
exit_bps: "50" # net carry below this triggers exit
min_health_factor: "1.25" # gates the perp short against LST-haircut breach
hedge_deadline_ms: "5000" # perp hedge deadline
peg_drift_threshold_bps:
  "25" # Phase 6B dynamic-hedge hysteresis band; rebalance fires when
  # |lst_native_rate_now - lst_native_rate_last_rebalance| × 1e4 > this. Default 25 ≈ 3σ daily.

# Leverage + net-delta controls (universal per StrategyInstanceDefinition; Stream D 2026-05-07):
# target_leverage = 1.0 is correct for LST_AS_MARGIN — the LST IS the full margin, no leverage multiplier.
# The field is present because StrategyInstanceDefinition is universal across all archetypes.
target_leverage: "1.0" # always 1.0 for carry_staked_basis; LST_AS_MARGIN does not support >1x
target_net_delta: "0.0" # delta-neutral: LST long leg + perp short hedge = net ~0 delta
max_underlying_move_pct: "5.0" # vol-cap clamp: pause rebalance if >5% move in 1h (wider than APD)
instrument_volatility_registry_lookup: "true" # use realized_vol_20 (1h candles) from FSS

# Chain constraint (UAC canonical/crosscutting/defi.ChainKind; Phase 3 defi_master 2026-05-18):
# Strategy refuses to size on-chain positions outside this list. CeFi perp venues are not
# chain-gated (they have no ChainKind). Defaults cover Jito/mSOL on Solana, stETH/rETH on
# Ethereum mainnet, and the primary L2 for gas-efficient on-chain execution.
allowed_chains: [ethereum, solana, arbitrum]
```

### Features expected (upstream `features-onchain` must publish)

- `staking_apy_bps` — on-chain rate-diff staking yield (annualised bps)
- `funding_rate_apy_bps` — perp funding rate (annualised bps)
- `usdc_idle_yield_apy_bps` — venue-specific USDC margin yield
- `health_factor` — LST haircut breach gate
- `lst_native_rate` — LST/native exchange rate (float, default 1.0 fallback) — used by `compute_dynamic_hedge_ratio()`
  for Phase 6B dynamic hedge sizing
- `lst_native_rate_ts` — unix timestamp of last `lst_native_rate` observation (float, optional). Staleness guard: if
  present and `now - lst_native_rate_ts > 300s`, engine falls back to `lst_native_rate=1.0` and logs a warning. Without
  this key published, the staleness guard never fires.

There is **no** `lending_protocol`, `borrow_asset`, or `borrow_apy_bps` — those belong to the deleted COLLATERAL_BORROW
path. There is also no SPLIT_STAKE fallback or USDC-margin alternative: if
`venue_accepts_collateral(perp_venue, lst_asset)` returns False, the slot is rejected at preflight.

## Execution semantics

`AtomicInstruction` with `execution_mode = LEADER_HEDGE`:

- **`LST_AS_MARGIN` (4 legs)**: SWAP (leader) + STAKE + TRANSFER + TRADE (hedge).

Compensation policy: `CLOSE_LEADER_IF_HEDGE_FAILS`. If the perp short fails within `hedge_deadline_ms`, the SWAP +
STAKE + TRANSFER legs are unwound (TRANSFER LST back + UNSTAKE + reverse SWAP) — strategy returns to USDC.

### LegController integration

The 4-leg sequence above is the **logical** flow. Mechanically, it is generated by
`LegController.update(slot, tick, execution_mode=LEADER_HEDGE)`:

1. `LegController` reads the slot universe and resolves SWAP → STAKE → TRANSFER → TRADE from the `CollateralFlowPlan`
   produced by the `ExecutionPlanner`.
2. Each leg fires as an `AtomicInstruction` in sequence; the SWAP leader triggers after pre-flight checks pass.
3. Compensation rules (`CLOSE_LEADER_IF_HEDGE_FAILS`) are enforced inside `LegController.on_leg_failure()`.

**Code-backport status:** DEFERRED — `carry_and_yield/staked_basis.py` still wires legs hand-built per the
pre-controller design. Backport tracked in `defi_recursive_borrow_archetypes_2026_05_10.md` factory-wiring phase. Docs
ship now per operator decision 2026-05-07.

## P&L attribution

| Leg                 | Income                                     | Cost           | Source                                          |
| ------------------- | ------------------------------------------ | -------------- | ----------------------------------------------- |
| Staked principal    | staking_apy_total_bps × notional           | mint/burn fees | `lst_rates` rate-diff + EIGEN + seasonal − dust |
| Perp short          | funding_apy_bps × notional (when positive) | commission     | venue funding feed                              |
| LST → perp transfer | n/a                                        | bridge/fee     | execution-service                               |
| Spot conversion     | n/a                                        | bid-ask spread | matching engine simulation                      |

`staking_apy_total_bps` is the aggregated staking APY: base on-chain rate-diff + EIGEN AVS rewards (when the LST is
restaked) + ETHFI / ANKR / Jito seasonal rewards − dust realisation slippage. Source: features-onchain
[`engine/staking_apy_total.py`](../../../../features-service (onchain
family)/features_onchain_service/engine/staking_apy_total.py) aggregator. The same value is consumed by
`YieldStakingSimpleRankAllocator` and `CarryStakedBasisRankAllocator` so both batch and live allocators see the same
number. Restaking economics detail: [restaking-reward-economics.md](../cross-cutting/restaking-reward-economics.md).

## Risk profile

- **Delta**: 0 by construction (LST long ≡ perp short on the underlying).
- **Liquidation**: when LST_AS_MARGIN, perp venue may liquidate if the LST haircut breaches; when SPLIT_STAKE, perp
  margin is USDC so liquidation only on the perp leg, not the LST.
- **Depeg risk**: stETH/rETH/JitoSOL discount-to-fair on secondary markets. Kill-switch at configured threshold.
- **Funding flip**: perp funding goes negative for an extended period — net carry collapses. Exit at `exit_bps`.
- **Smart contract risk**: LST contract bug + lending market exploit. Both are reduced vs the old COLLATERAL_BORROW path
  because there is no lending market in the loop anymore.

## Reaction to equity change

`react_to_equity_change` emits a 2-leg rescale: SWAP USDC↔ETH for the principal delta + matching TRADE on the perp. The
STAKE/UNSTAKE micro-flows are deferred to the lease-controller cash-sweep — no need to mint/burn LST on every equity
wobble.

## Per-archetype rank allocator

Capital allocation across the eligible (LST, perp_venue) slots uses
[`CarryStakedBasisRankAllocator`](../../../../strategy-service/strategy_service/portfolio_allocator/archetypes.py)
(Phase 8 of plan `carry_staked_basis_structure_axis_2026_05_04`). The ranker:

1. Filters to slots where `lst_asset` AND `venue` are populated (the universe is gated upstream by the catalog
   generator's `accepted_perp_collateral` filter — slots that don't pass the matrix never reach the allocator).
2. Scores each slot as `staking_apy_total_bps + funding_apy_bps` (USDC-denominated combined carry).
3. Drops slots scoring below `min_apy_bps` (default 250 = 2.5%, configurable per allocator instance).
4. Stage 1: ranks LSTs by their average score across surviving venues; truncates to `top_n_lsts` if set.
5. Stage 2: per surviving LST, ranks venues by per-venue score; truncates to `top_n_venues_per_lst` if set.
6. Final per-slot weight = stage_1_lst_weight × stage_2_venue_weight; sums to 1 across surviving slots.

Below threshold = the slot is dropped (zero allocation). If every slot is below threshold the snapshot returns all-zeros
with a rationale string — the caller decides whether to lend the cash instead.

`AllocatorArchetype.CARRY_STAKED_BASIS_RANK` is the registry key. The same `BaseRankAllocator` shape is reused by 6
sibling subclasses (one per rank-eligible archetype: `YieldStakingSimpleRankAllocator`, `CarryBasisPerpRankAllocator`,
`CarryRecursiveStakedRankAllocator`, `CarryBasisDatedRankAllocator`, `YieldRotationLendingRankAllocator`,
`ArbitragePriceDispersionRankAllocator`). Each gets its own universe filter + ranking metric — no cross-archetype
switching for now (future layer).

## Tracer protocol

`scripts/trace_carry_staked_basis.py` ranks the catalog slots by realised net USDC APY over a configurable window:

```bash
cd strategy-service
python scripts/trace_carry_staked_basis.py \
    --start-date 2026-04-05 \
    --end-date 2026-05-05
```

Reads MTDS `lst_rates` directly (same upstream as the live engine via the calculator refactor), pulls funding via
features-delta-one `funding_oi`. Output schema:

```
slot_label, lst_asset, perp_venue, perp_instrument, stake_fraction,
structure, days_observed, gross_carry_bps_avg, fees_bps,
net_apy_bps, max_drawdown_bps, hit_rate, first_date, last_date
```

Default output: `gs://strategy-store-{pid}/tracer_runs/CARRY_STAKED_BASIS/{run_date}/results.parquet`. Sorted by
`net_apy_bps` desc — winners feed the orchestrator's universe selector for capital allocation.

## Why structure is derived, not chosen

`VENUE_COLLATERAL_MATRIX` is the single source of truth for which tokens each venue accepts as margin. Re-declaring that
knowledge in the engine or catalog (e.g. as a `margin_structure` user param) creates drift: when Hyperliquid adds a new
accepted asset, you'd need a code change in three places. With derivation:

- Add the matrix row.
- Engine sees it next tick.
- Catalog regenerates.
- Tracer measures.
- Universe selector allocates.

No engine, catalog, or strategy code change needed.

## Migration from legacy

| Legacy                                                 | Status                                            |
| ------------------------------------------------------ | ------------------------------------------------- |
| `defi/staked-basis.md` (3-leg STAKE+LEND+BORROW+SHORT) | **Deleted** — basis erosion via stablecoin borrow |
| `defi/sol-staked-basis.md`                             | Folded into the SOL bundle at `f` slots above     |
| `staked_basis.py` (v1, with `borrow_apy_bps`)          | Replaced by `v2/carry_and_yield/staked_basis.py`  |

## Not in this archetype

- **Single LST passive hold** (no perp hedge) — `YIELD_STAKING_SIMPLE`
- **Flash-loan amplified staked basis** (recursive leverage loops) — `CARRY_RECURSIVE_STAKED`
- **Perp funding capture without LST collateral** (spot = raw asset) — `CARRY_BASIS_PERP`
- **Lending the LST for extra yield** — `YIELD_ROTATION_LENDING`

## See also

- **Active umbrella plan**: [`plans/active/defi_master.md`](/plans/epics/defi_master.md) — Fork 1 owns live
  carry_staked_basis deployment
- **Venue-matrix / canonicalisation plan**:
  [`plans/active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](../../../../plans/archive/2026_05/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
  (Stream A: venue collateral live probe; Stream D: target_leverage / vol-cap config schema)
- **Archived origin plan** (provenance of `CarryStakedBasisRankAllocator` Phase 8):
  [`plans/archive/carry_staked_basis_structure_axis_2026_05_04.plan.md`](../../../../plans/archive/carry_staked_basis_structure_axis_2026_05_04.plan.md)
- Family: [`carry-and-yield.md`](../families/carry-and-yield.md)
- Recursive variant: [`carry-recursive-staked.md`](carry-recursive-staked.md)
- Venue collateral SSOT:
  [`unified-api-contracts/unified_api_contracts/registry/venue_collateral.py`](../../../../unified-api-contracts/unified_api_contracts/registry/venue_collateral.py)
- LST rate handler:
  [`market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py`](../../../../market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py)
