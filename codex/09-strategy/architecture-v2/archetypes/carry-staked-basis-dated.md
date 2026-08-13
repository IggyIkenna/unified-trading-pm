---
doc_type: codex-ssot
title: "Archetype: `CARRY_STAKED_BASIS_DATED`"
summary: >-
  Archetype CARRY_STAKED_BASIS_DATED: dated-contract variant of CARRY_STAKED_BASIS — stake into an LST posted as
  cross-margin + SHORT a dated (quarterly/monthly) futures contract, locking the basis premium at entry plus staking
  yield. net_apy_bps = staking_apy_total + annualised dated basis - fees; shares staked_basis.py via ALLOWED_ARCHETYPES;
  Deribit/Drift/Bybit slots; must roll before expiry.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [strategy, carry, defi, cefi, execution, archetype, deribit]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-dated.md,
    ../families/carry-and-yield.md,
  ]
created: 2026-05-18
authoritative_for: [CARRY_STAKED_BASIS_DATED archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-dated-inv.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp-inv.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
    /codex/09-strategy/architecture-v2/families/carry-and-yield.md,
    /codex/09-strategy/strategy-summary.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: CARRY_STAKED_BASIS_DATED
family: CARRY_AND_YIELD
venue_universe: [LIDO, ETHERFI, JITO, DERIBIT, DRIFT, BYBIT, UNISWAP_V3, JUPITER]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 150
  min_sla_tier: premium
---

# Archetype: `CARRY_STAKED_BASIS_DATED`

> **Family:** [Carry & Yield](../families/carry-and-yield.md) **Settlement model:** Hold to futures expiry; staking
> continues during the hold. **Code module (target):**
> `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py` (`ALLOWED_ARCHETYPES` =
> `CARRY_STAKED_BASIS_DATED`)

## What it does

Dated-contract variant of `CARRY_STAKED_BASIS`: stake ETH into an LST, transfer to the perp venue as cross-margin, SHORT
a **dated futures contract** (quarterly/monthly expiry) instead of a perpetual. Earns staking yield on the staked
principal during the hold period, PLUS the dated futures basis premium locked in at entry — which converts to P&L as the
contract converges to spot at expiry.

**vs `CARRY_STAKED_BASIS`**: replaces the perpetual hedge with a dated-expiry contract. The dated variant locks in the
basis premium at entry (guaranteed to zero out at expiry if held); the perp variant earns ongoing funding rate
(variable, can flip). Use `CARRY_STAKED_BASIS_DATED` when the dated basis premium exceeds expected perp funding over the
contract period and you prefer certainty of the basis over variability of funding.

**Combined yield** (USDC, annualised):

```
net_apy_bps = staking_apy_total_bps + (basis_at_entry_bps × 365 / days_to_expiry) − fees
```

## Token / position flow

```
1. ENTRY TRIGGER: net_apy_bps = staking_apy_total_bps + annualised_basis_bps > entry_bps

2. POSITION OPENING:
   a. SWAP: USDC → ETH/SOL on spot venue (UNISWAP_V3, JUPITER, ...)
   b. STAKE: ETH/SOL → LST (Lido/stETH, Ether.fi/weETH, Jito/JitoSOL, ...)
   c. TRANSFER: LST → perp venue as cross-margin
   d. TRADE: SHORT dated futures contract (equal-and-opposite to LST principal)
      Venue must accept the LST as cross-margin for the dated contract.

3. HOLD: staking yield accrues continuously; basis converges toward zero as expiry approaches.

4. EXIT:
   a. Hold to expiry → dated futures settles to spot; LST leg unwound (UNSTAKE + SWAP back to USDC)
   b. Early exit → buy back dated short; unwind TRANSFER + UNSTAKE + SWAP
   c. Risk trigger → close both legs; staking yield pro-rated to exit date

Net carry (USDC, annualised):
    net_apy_bps = staking_apy_total_bps + basis_at_entry_bps × (365 / days_to_expiry) − fees
```

## Key difference: dated vs perpetual hedge

| Dimension           | `CARRY_STAKED_BASIS` (perp)               | `CARRY_STAKED_BASIS_DATED` (dated)                |
| ------------------- | ----------------------------------------- | ------------------------------------------------- |
| Hedge instrument    | Perpetual contract (no expiry)            | Quarterly/monthly dated futures                   |
| Basis income        | Ongoing funding rate (variable, can flip) | Locked-in at entry, converges to 0 at expiry      |
| P&L certainty       | Variable — funding rate fluctuates daily  | Certain — basis is locked if held to expiry       |
| Funding regime risk | Funding flip → carry collapses            | None — no funding rate on dated contracts         |
| Roll requirement    | None (perp never expires)                 | Roll before expiry or accept cash settlement      |
| Capital efficiency  | Higher (continuous funding compounding)   | Similar; dated basis often larger than perp basis |
| Best regime         | Positive + stable funding (bull market)   | Steep contango with elevated dated basis          |

## Supported venues / instruments

**Venue eligibility gate**: the LST must be accepted as cross-margin for the **dated** contract at the perp venue.
`venue_accepts_collateral(perp_venue, lst_asset)` applies the same logic as `CARRY_STAKED_BASIS`.

| perp_venue | LST accepted (dated contracts)                                 | Catalog rows                 |
| ---------- | -------------------------------------------------------------- | ---------------------------- |
| DERIBIT    | stETH (7.5% haircut; accepted for BTC + ETH quarterly/monthly) | stETH × Q1/Q2 dated = 2 rows |
| DRIFT      | JitoSOL (10% haircut; SOL-DATED program on Drift)              | JitoSOL × SOL quarterly = 1  |
| BYBIT      | stETH (UTA cross-collateral, dated BTC/ETH futures)            | stETH × quarterly = 1 row    |

**Active catalog slots** (2026-05-20, from `catalog.py _build_carry_staked_basis_dated`):

```
CARRY_STAKED_BASIS_DATED@lido-deribit-eth-q1-usdc-v1-prod   # stETH × Deribit ETH-Q1 quarterly
CARRY_STAKED_BASIS_DATED@lido-deribit-eth-q2-usdc-v1-prod   # stETH × Deribit ETH-Q2 quarterly
CARRY_STAKED_BASIS_DATED@jito-drift-sol-q1-usdc-v1-prod     # JitoSOL × Drift SOL-Q1 dated
```

## Config schema

```yaml
# Required engine params (passed via initial_config dict):
staking_protocol: LIDO # LIDO | JITO | ETHERFI | ROCKETPOOL
native_asset: ETH # ETH | SOL
lst_asset: stETH # stETH | JitoSOL | weETH | rETH
perp_venue: DERIBIT # venue accepting lst_asset for dated contract margin
perp_instrument: ETH-Q2-2026 # dated futures symbol (venue-canonical format)
spot_venue: UNISWAP_V3 # USDC → native swap venue
start_token: USDC
stake_fraction: "1.0" # always 1.0 — LST is the cross-margin

# Entry/exit thresholds (combining staking yield + dated basis):
entry_bps: "300" # combined annualised yield must exceed this to enter
exit_bps: "100" # close early if combined annualised yield falls below this
min_health_factor: "1.25" # LST haircut breach gate
hedge_deadline_ms: "5000"

# Roll params:
rollover_days_before_expiry: 5 # days before expiry to roll or close
auto_roll_enabled: false # if true, engine opens next-quarter dated short on roll date

# Leverage + net-delta controls:
target_leverage: "1.0" # LST_AS_MARGIN; no leverage multiplier
target_net_delta: "0.0" # delta-neutral: LST long + dated short = net ~0 delta
max_underlying_move_pct: "5.0"

# Chain constraint:
allowed_chains: [ethereum, solana]
```

## Features expected (upstream `features-onchain` must publish)

Same as `CARRY_STAKED_BASIS` plus:

- `staking_apy_bps` — on-chain rate-diff staking yield (annualised bps)
- `dated_basis_bps` — `(future_price − spot_price) / spot_price × 10000` at last candle (annualised equivalent)
- `lst_native_rate` — LST/native exchange rate (hedge sizing)
- `lst_native_rate_ts` — staleness guard timestamp
- `days_to_expiry` — calendar days to dated contract expiry (for annualisation)

`funding_rate_apy_bps` is NOT needed — dated contracts have no funding rate. The `dated_basis_bps` replaces it.

## Execution semantics

`AtomicInstruction` with `execution_mode = LEADER_HEDGE` (same 4-leg flow as `CARRY_STAKED_BASIS`):

- **4-leg entry**: SWAP (leader) + STAKE + TRANSFER + TRADE (dated short)
- **Compensation policy**: `CLOSE_LEADER_IF_HEDGE_FAILS` — unwind SWAP + STAKE + TRANSFER if dated short fails

On expiry: execute exit automatically or roll to next quarter per `auto_roll_enabled`.

**Code-backport status:** DEFERRED — shares `staked_basis.py` engine via `ALLOWED_ARCHETYPES`; engine branches on
`archetype_id == CARRY_STAKED_BASIS_DATED` to read `dated_basis_bps` instead of `funding_rate_apy_bps` and set
`rollover_days_before_expiry` for expiry logic. Backport tracked in `defi_recursive_borrow_archetypes_2026_05_10.md`
factory-wiring phase.

## P&L attribution

| Leg                 | Income                           | Cost                | Source                         |
| ------------------- | -------------------------------- | ------------------- | ------------------------------ |
| Staked principal    | staking_apy_total_bps × notional | mint/burn fees      | `lst_rates` on-chain rate-diff |
| Dated short         | basis_at_entry_bps × days/365    | commission          | Deribit/Drift dated ticker     |
| LST → perp transfer | n/a                              | bridge/transfer fee | execution-service              |
| Spot conversion     | n/a                              | bid-ask spread      | matching engine simulation     |

## Risk profile

- **Delta**: 0 by construction (LST long ≡ dated short on the underlying)
- **Basis convergence risk**: dated basis can widen before converging — mark-to-market drawdown
- **Liquidation**: LST haircut breach at perp venue; same health-factor kill-switch as `CARRY_STAKED_BASIS`
- **Depeg risk**: stETH/JitoSOL discount-to-fair on secondary; same kill-switch as `CARRY_STAKED_BASIS`
- **Roll risk**: dated contracts expire; must roll or close 5 days before expiry to avoid delivery
- **No funding flip risk**: unlike perp variant, there is no funding rate component — basis is locked at entry
- Typical Sharpe: 1.5–3.0 (comparable to `CARRY_STAKED_BASIS` but with lower variance from funding-flip absence)

## Reaction to equity change

`react_to_equity_change` emits a 2-leg rescale: SWAP USDC↔ETH for the principal delta + matching TRADE on the dated
contract. STAKE/UNSTAKE micro-flows deferred to the lease-controller cash-sweep per `CARRY_STAKED_BASIS` pattern.

## Migration from legacy

No legacy doc. `CARRY_STAKED_BASIS_DATED` is a new archetype added 2026-05-18 per operator taxonomy decision
(strategy_archetype_taxonomy_2026_05_12.md § §2 "CARRY_STAKED_BASIS_DATED — NEW archetype").

## Not in this archetype

- **Perpetual funding capture with LST** (variable funding, no expiry lock) → `CARRY_STAKED_BASIS`
- **Dated basis without staking** (plain spot + dated short) → `CARRY_BASIS_DATED`
- **Recursive borrow loop** (amplified lending spread + perp hedge) → `CARRY_BASIS_PERP_INV`
- **Single LST passive hold** (no hedge) → `YIELD_STAKING_SIMPLE`

## See also

- Perp variant: [carry-staked-basis.md](carry-staked-basis.md)
- Dated basis (no staking): [carry-basis-dated.md](carry-basis-dated.md)
- Family: [carry-and-yield.md](../families/carry-and-yield.md)
- Venue collateral SSOT:
  [unified_api_contracts/.../registry/venue_collateral.py](../../../../unified-api-contracts/unified_api_contracts/registry/venue_collateral.py)
