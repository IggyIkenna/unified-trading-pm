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

> **Hedge ratio audit 2026-05-12 (Phase 6A of `defi_simulation_realism_2026_05_10`)** — current hedge
> sizing is **STATIC** at `eth_qty * (1 - margin_haircut)` (1:1 against LST principal clamped by venue
> haircut), confirmed at `staked_basis.py:264`. NO per-tick / per-bar adjustment for LST/native peg drift.
> Phase 6B implementation (Harsh slot 4) introduces dynamic adjustment using LST exchange rate stream
> (jitoSOL/SOL, mSOL/SOL, bSOL/SOL, rETH/ETH, stETH/ETH, weETH/ETH) with `peg_drift_threshold_bps` hysteresis
> band (default 25 bps ≈ 3σ daily). Full spec:
> [`../../../04-architecture/amm-slippage-simulation.md`](../../../04-architecture/amm-slippage-simulation.md)
> § "Hedge-ratio dynamic adjustment (Phase 6)".

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

Today's matrix (2026-05-07 — venue-matrix re-verification, see plan
[`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](../../../../plans/ai/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)):

| perp_venue                                                                                                       | LST acceptance                                                                                             | catalog rows produced (post-Stream A flip) |
| ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| DRIFT                                                                                                            | JitoSOL (10% haircut), mSOL (10% haircut)                                                                  | 2 rows                                     |
| DERIBIT                                                                                                          | stETH (7.5% haircut, X:PM/X:SM, offsets ETH-perp directly — effective 2026-01-13)                          | 1 row                                      |
| BYBIT (UTA)                                                                                                      | stETH + METH + USDe (UTA cross-collateral; haircuts per Bybit margin-spec page)                            | up to 3 rows                               |
| OKX (multi-currency / portfolio margin)                                                                          | wstETH (multi-currency-margin discount-rate list; haircut TBD per Stream A live probe)                     | 1 row                                      |
| HYPERLIQUID (L1)                                                                                                 | none (USDC-only) — explicit `accepted=False` rows                                                          | 0 rows                                     |
| BINANCE (Multi-Assets Mode)                                                                                      | none — `BTC/ETH/BNB/XRP/ADA/DOT/SOL/USDC/USDT` only; cross-collateral feature retired                      | 0 rows                                     |
| ASTER                                                                                                            | none — USDT/USDF/asBNB only                                                                                | 0 rows                                     |
| GMX                                                                                                              | none — per-market collateral set excludes LSTs                                                             | 0 rows                                     |
| BINANCE-FUTURES / BYBIT-FUTURES / OKX-FUTURES / KRAKEN-FUTURES / BITFINEX-FUTURES / BITGET-FUTURES (Tardis-CeFi) | none — linear-USDT or coin-margined only; LST acceptance lives at the spot-UTA layer not the futures layer | 0 rows                                     |

**Effective slot count post-Stream A flip = ~7** (DRIFT/JitoSOL + DRIFT/mSOL + Deribit/stETH + Bybit/stETH +
Bybit/METH + Bybit/USDe-as-stable-not-LST + OKX/wstETH; final count depends on Stream A live-probe haircut
verifications). This **supersedes the prior 2026-05-05 claim** that DRIFT was the only venue.

**Per-venue wrap-step discipline (added 2026-05-12 per
[`pnl-attribution.md`](../cross-cutting/pnl-attribution.md) HARD RULE #5
"Staking yield: wrapped (price-delta) vs rebasing (balance-delta)")**: the
on-chain `STAKE` leg shape depends on the perp venue's accepted form:

| perp_venue | LST form | `STAKE` leg sequence | P&L attribution factor |
|---|---|---|---|
| DRIFT (Solana) | JitoSOL / mSOL (natively non-rebasing) | `SWAP(USDC→SOL) → STAKE(SOL→jitoSOL via Jito stake pool) → TRANSFER(jitoSOL → Drift)` — no wrap step needed | `CARRY_BASE` (oracle price delta from Jito stake-pool getter) |
| DERIBIT | stETH (rebasing; Deribit absorbs daily rebase server-side via 7.5% haircut + offset-credit calibration) | `SWAP(USDC→ETH) → STAKE(Lido.submit → stETH) → TRANSFER(stETH → Deribit)` — NO wrap | `CARRY_BASE_REBASING` (position-balance-monitor reads Deribit subaccount balance delta) |
| BYBIT (UTA) | stETH + METH + USDe (rebasing; Bybit handles daily rebase at UTA layer) | `SWAP(USDC→ETH) → STAKE(Lido.submit → stETH) → TRANSFER(stETH → Bybit UTA)` — NO wrap | `CARRY_BASE_REBASING` (position-balance-monitor reads Bybit UTA balance delta) |
| OKX (multi-currency margin) | wstETH (wrapped non-rebasing — OKX has no daily-rebase reconciliation) | `SWAP(USDC→ETH) → STAKE(Lido.submit → stETH → wstETH wrap via Lido wrap contract) → TRANSFER(wstETH → OKX)` | `CARRY_BASE` (oracle price delta from `wstETH.stEthPerToken()`) |

**Banned** at archetype `_build_legs` time:

- Posting wrapped `wstETH` to Bybit / Deribit — those venues calibrate their margin pricing on rebasing stETH; the
  wrapped form's price diverges from the underlying share-price and the venue's offset-credit math breaks.
- Posting rebasing `stETH` to OKX — OKX has no daily-rebase reconciliation; the position would mark as undersized
  every Lido rebase epoch (typically daily) and re-collateralization risk compounds.
- Treating jitoSOL / mSOL as needing a wrap step — they're natively non-rebasing, the issuer contract mints the
  rate-accreting form directly.

The archetype config (`default_basis_trade.yaml`) discriminator: each `(perp_venue, lst_asset)` row hardcodes
whether the `STAKE` leg includes the wrap step. This is part of the leg-sequence builder, not a runtime decision —
the matrix above is the SSOT.

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
[`codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md`](../../../16-strategy-playbooks/defi/venue-collateral-2026-05-07.md)
(to be created by Stream A). Continuous-audit cadence (monthly?) is deferred to a separate plan named in Stream E
follow-throughs.

## Catalog axis (slot labels)

```
CARRY_STAKED_BASIS@{staking_protocol}-{perp_venue}-f100-usdc-1h-usdc-v2-prod

Examples (2026-05-05):
  CARRY_STAKED_BASIS@jito-drift-f100-usdc-1h-usdc-v2-prod
  CARRY_STAKED_BASIS@marinade-drift-f100-usdc-1h-usdc-v2-prod
```

**Pre-2026-05-07:** 2 slots (DRIFT/JitoSOL + DRIFT/mSOL). **Post-Stream A flip:** ~7 slots once Deribit/stETH +
Bybit/stETH + Bybit/METH + OKX/wstETH (haircut-verified per Stream A live probe) land. `f` is fixed at `100` (= 1.0)
because LST_AS_MARGIN is the only allowed structure: the LST IS the perp margin, no spare USDC bucket. Built by
`_build_carry_staked_basis` in
[`strategy-service/.../target_universe/catalog.py`](../../../../strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py)
from the matrix at module import — slot expansion is automatic once the matrix entries flip to `accepted=True`.

## Config schema

```yaml
share_class: USDC
capital_budget_share_class: USDC
capital_budget_amount: 1000000

# Required engine params (passed via initial_config dict):
staking_protocol: JITO # JITO / MARINADE today; LIDO / ROCKETPOOL / ETHERFI when an ETH-perp venue lands LST margin
native_asset: SOL # SOL today; ETH when an ETH-perp venue lands LST margin
lst_asset: JitoSOL # JitoSOL / mSOL today
perp_venue: DRIFT # must appear in VENUE_COLLATERAL_MATRIX with the LST accepted=True
perp_instrument: SOL-PERP
spot_venue: JUPITER # USDC->native swap venue (JUPITER / UNISWAP_V3 / ...)
start_token: USDC # entry token; must be in `accepted_perp_collateral(perp_venue)` (sanity check)
stake_fraction: "1.0" # always 1.0 post-2026-05-05 — LST is the perp margin

# Optional thresholds:
entry_bps: "200" # net carry must exceed this to enter
exit_bps: "50" # net carry below this triggers exit
min_health_factor: "1.25" # gates the perp short against LST-haircut breach
hedge_deadline_ms: "5000" # perp hedge deadline
```

There is **no** `lending_protocol`, `borrow_asset`, or `borrow_apy_bps` — those belong to the deleted COLLATERAL_BORROW
path. There is also no SPLIT_STAKE fallback or USDC-margin alternative: if
`venue_accepts_collateral(perp_venue, lst_asset)` returns False, the slot is rejected at preflight.

## Execution semantics

`AtomicInstruction` with `execution_mode = LEADER_HEDGE`:

- **`LST_AS_MARGIN` (4 legs)**: SWAP (leader) + STAKE + TRANSFER + TRADE (hedge).

Compensation policy: `CLOSE_LEADER_IF_HEDGE_FAILS`. If the perp short fails within `hedge_deadline_ms`, the SWAP +
STAKE + TRANSFER legs are unwound (TRANSFER LST back + UNSTAKE + reverse SWAP) — strategy returns to USDC.

## P&L attribution

| Leg                 | Income                                     | Cost           | Source                                          |
| ------------------- | ------------------------------------------ | -------------- | ----------------------------------------------- |
| Staked principal    | staking_apy_total_bps × notional           | mint/burn fees | `lst_rates` rate-diff + EIGEN + seasonal − dust |
| Perp short          | funding_apy_bps × notional (when positive) | commission     | venue funding feed                              |
| LST → perp transfer | n/a                                        | bridge/fee     | execution-service                               |
| Spot conversion     | n/a                                        | bid-ask spread | matching engine simulation                      |

`staking_apy_total_bps` is the aggregated staking APY: base on-chain rate-diff + EIGEN AVS rewards (when the LST is
restaked) + ETHFI / ANKR / Jito seasonal rewards − dust realisation slippage. Source: features-onchain
[`engine/staking_apy_total.py`](../../../../features-onchain-service/features_onchain_service/engine/staking_apy_total.py)
aggregator. The same value is consumed by `YieldStakingSimpleRankAllocator` and `CarryStakedBasisRankAllocator` so both
batch and live allocators see the same number. Restaking economics detail:
[restaking-reward-economics.md](../cross-cutting/restaking-reward-economics.md).

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

- Plan:
  [`plans/archive/carry_staked_basis_structure_axis_2026_05_04.plan.md`](../../../../plans/archive/carry_staked_basis_structure_axis_2026_05_04.plan.md)
- Family: [`carry-and-yield.md`](../families/carry-and-yield.md)
- Recursive variant: [`carry-recursive-staked.md`](carry-recursive-staked.md)
- Venue collateral SSOT:
  [`unified-api-contracts/unified_api_contracts/registry/venue_collateral.py`](../../../../unified-api-contracts/unified_api_contracts/registry/venue_collateral.py)
- LST rate handler:
  [`market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py`](../../../../market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py)
