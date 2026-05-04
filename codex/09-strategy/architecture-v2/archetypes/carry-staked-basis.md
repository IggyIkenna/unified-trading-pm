---
scope: [engineer, admin]
topology_requirements:
  isolation:
    execution-service: isolated
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `CARRY_STAKED_BASIS`

> **Family:** [Carry & Yield](../families/carry-and-yield.md) **Settlement model:** Continuous; market-neutral
> multi-step paired position. **Code module:**
> `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py`

## What it does

USDC-share-class market-neutral basis trade: deploy a fraction `f` of starting USDC into ETH (or SOL), stake into the
LST, short the equivalent perp on a venue, hold the (1−f) USDC at the perp venue as margin. Earn staking yield on the
staked fraction + funding rate on the short + idle yield on the cash fraction. Delta = 0 because the perp short cancels
the long underlying delta the LST creates.

The execution structure (which legs are emitted, which venue holds which asset) is **derived from the UAC venue
collateral matrix** at preflight, not user-chosen. Engine queries
[`unified_api_contracts.registry.venue_collateral.accepted_perp_collateral`](../../../../unified-api-contracts/unified_api_contracts/registry/venue_collateral.py)
on the `perp_venue` and emits whatever leg sequence is feasible. No baked-in structure choice.

## Token / position flow — two structures, derived from the matrix

### Structure A — LST_AS_MARGIN (when perp venue accepts the LST as cross-margin)

```
1. SWAP (leader): USDC --> ETH/SOL on a spot venue (UNISWAP_V3, JUPITER, ...).
2. STAKE: ETH/SOL --> LST on the staking protocol.
3. TRANSFER: LST --> perp venue as cross-margin.
4. TRADE (hedge): SHORT perp_instrument equal-and-opposite to the LST principal.

   Net carry (USDC, annualised, bps):
       net_apy_bps = staking_apy + funding_apy - fees

       Where staking_apy is derived on-chain (rate diff per day, annualised).
```

Eligibility: the perp venue must have a `(venue, lst_asset, accepted=True)` row in `VENUE_COLLATERAL_MATRIX`.

### Structure B — SPLIT_STAKE (when perp venue accepts only USDC)

```
1. SWAP (leader): f * USDC --> ETH/SOL on a spot venue.
2. STAKE: ETH/SOL --> LST on the staking protocol; LST stays at the staking venue.
3. TRADE (hedge): SHORT perp using (1-f) * USDC as margin.

   Net carry (USDC, annualised, bps):
       net_apy_bps = f * (staking_apy + funding_apy)
                    + (1 - f) * usdc_idle_yield
                    - fees
```

`f` ∈ (0, 1] is the only user-tunable structure parameter. `f = 1.0` is rejected at preflight on USDC-only venues (would
leave zero perp margin); valid splits are typically `f ∈ {0.5, 0.75}`.

### COLLATERAL_BORROW — deleted (do NOT use)

The previous engine implementation routed: stake LST → pledge as Aave collateral → borrow USDC → use that USDC as perp
margin. **Removed 2026-05-04** because the stablecoin borrow rate (typically 5–8% APY) erodes the basis P&L faster than
the staking + funding earns it back. There is no scenario where this dominates Structure A or B.

## On-chain APY derivation (real, not vendor)

`staking_apy_bps` for both batch (tracer) and live (engine) is derived from MTDS `lst_rates` on-chain exchange-rate
ratio movement:

```
staking_apy_bps = ((rate[t] / rate[t-1])^365 - 1) * 1e4
```

`rate[t]` is the LST contract's current exchange rate (e.g. `getPooledEthByShares` for stETH, `getExchangeRate` for
rETH, on-chain method per LST captured in
[`market-tick-data-service/.../lst_rates_handler.py`](../../../../market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py)).
This is what the position would actually earn — not a DefiLlama-modelled or vendor-reported APY.

`funding_rate_apy_bps` = venue-published funding rate × cycles/day × 365 (pure arithmetic on raw venue data, no
modelling).

`usdc_idle_yield_apy_bps` = venue-specific USDC margin yield (HLP / HIP-3 funding rebate). **Not yet wired upstream** —
defaults to 0 until features-delta-one emits a `venue_funding_yield` series. Strategies running on USDC-margined venues
should treat current numbers as a conservative floor.

## Eligibility — derived, not declared

Adding a venue or LST to `VENUE_COLLATERAL_MATRIX` automatically expands the catalog's eligible slots on next
regeneration. No engine code changes, no catalog code changes — just a new matrix row.

Today's matrix (2026-05-04):

| perp_venue            | accepts        | structure produced | LST eligibility            |
| --------------------- | -------------- | ------------------ | -------------------------- |
| HYPERLIQUID           | USDC           | SPLIT_STAKE        | n/a (no LST accepted)      |
| DERIBIT               | USDC, ETH, BTC | SPLIT_STAKE        | n/a                        |
| ASTER                 | USDC, USDT     | SPLIT_STAKE        | n/a                        |
| BINANCE / BYBIT / OKX | USDT, BTC, ETH | not eligible       | USDT-only (no USDC margin) |

No venue currently accepts an LST as direct margin. Once Aevo / GMX / Drift land in the matrix with `wstETH` / `jitoSOL`
accepted=True rows, their `LST_AS_MARGIN` slots will appear in the catalog automatically.

## Catalog axis (slot labels)

```
CARRY_STAKED_BASIS@{staking_protocol}-{perp_venue}-f{int(f*100)}-usdc-1h-usdc-v2-prod

Examples (2026-05-04):
  CARRY_STAKED_BASIS@lido-hyperliquid-f50-usdc-1h-usdc-v2-prod
  CARRY_STAKED_BASIS@lido-hyperliquid-f75-usdc-1h-usdc-v2-prod
  CARRY_STAKED_BASIS@etherfi-deribit-f50-usdc-1h-usdc-v2-prod
  CARRY_STAKED_BASIS@jito-hyperliquid-f50-usdc-1h-usdc-v2-prod
```

22 slots total: 3 ETH-LST × 3 ETH-perp × 2 f-values + 2 SOL-LST × 1 SOL-perp × 2 f-values. Built by
`_build_carry_staked_basis` in
[`strategy-service/.../target_universe/catalog.py`](../../../../strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py)
from the matrix at module import.

## Config schema

```yaml
share_class: USDC
capital_budget_share_class: USDC
capital_budget_amount: 100000 # ETH; 75000 for SOL bundles

# Required engine params (passed via initial_config dict):
staking_protocol: LIDO # required (LIDO / ROCKETPOOL / ETHERFI / JITO / MARINADE)
native_asset: ETH # ETH or SOL
lst_asset: stETH # stETH / rETH / weETH / JitoSOL / mSOL
perp_venue: HYPERLIQUID # must appear in VENUE_COLLATERAL_MATRIX
perp_instrument: ETH-PERP # or SOL-PERP
spot_venue: UNISWAP_V3 # USDC->native swap venue (UNISWAP_V3 / JUPITER / ...)
stake_fraction: "0.5" # f in (0, 1]; engine derives structure from venue capability

# Optional thresholds:
entry_bps: "200" # net carry must exceed this to enter
exit_bps: "50" # net carry below this triggers exit
min_health_factor: "1.25" # gate when LST_AS_MARGIN structure (irrelevant for SPLIT_STAKE)
hedge_deadline_ms: "5000" # perp hedge deadline
```

There is **no** `lending_protocol`, `borrow_asset`, or `borrow_apy_bps` — those belong to the deleted COLLATERAL_BORROW
path.

## Execution semantics

`AtomicInstruction` with `execution_mode = LEADER_HEDGE`:

- **Structure A (4 legs)**: SWAP (leader) + STAKE + TRANSFER + TRADE (hedge).
- **Structure B (3 legs)**: SWAP (leader) + STAKE + TRADE (hedge); LST stays at staking venue, USDC margin lives at the
  perp venue.

Compensation policy: `CLOSE_LEADER_IF_HEDGE_FAILS`. If the perp short fails within `hedge_deadline_ms`, the SWAP + STAKE
legs are unwound (UNSTAKE + reverse SWAP) — strategy returns to USDC.

## P&L attribution

| Leg              | Income                                     | Cost                        | Source                        |
| ---------------- | ------------------------------------------ | --------------------------- | ----------------------------- |
| Staked principal | staking_apy_bps × f × notional             | mint/burn fees              | `lst_rates` rate-diff per day |
| Perp short       | funding_apy_bps × notional (when positive) | commission                  | venue funding feed            |
| USDC margin      | usdc_idle_yield_apy_bps × (1-f) × notional | n/a                         | venue funding rebate (TODO)   |
| Spot conversion  | n/a                                        | bid-ask spread on USDC↔ETH | matching engine simulation    |

Restaking-eligible LSTs (weETH, pufETH, ankrETH, ETHx) accrue additional layers — see
[restaking-reward-economics.md](../cross-cutting/restaking-reward-economics.md). Those are recorded as separate
attribution rows; not part of the basis-trade carry calculation.

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

## Tracer protocol

`scripts/trace_carry_staked_basis.py` ranks the 22 catalog slots by realised net USDC APY over a configurable window:

```bash
cd strategy-service
python scripts/trace_carry_staked_basis.py \
    --start-date 2026-04-04 \
    --end-date 2026-05-03
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

- Plan:
  [`plans/active/carry_staked_basis_structure_axis_2026_05_04.plan.md`](../../../../plans/active/carry_staked_basis_structure_axis_2026_05_04.plan.md)
- Family: [`carry-and-yield.md`](../families/carry-and-yield.md)
- Recursive variant: [`carry-recursive-staked.md`](carry-recursive-staked.md)
- Venue collateral SSOT:
  [`unified-api-contracts/unified_api_contracts/registry/venue_collateral.py`](../../../../unified-api-contracts/unified_api_contracts/registry/venue_collateral.py)
- LST rate handler:
  [`market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py`](../../../../market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py)
