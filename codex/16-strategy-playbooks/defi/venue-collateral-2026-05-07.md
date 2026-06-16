---
scope: [engineer]
title: "ETH-LST + stablecoin-LST collateral acceptance — 2026-05-07 reverification"
created: 2026-05-08
author: defi-fork1-completion-tab
source:
  - unified-api-contracts/unified_api_contracts/registry/venue_collateral.py
  - plans/active/work_split_2026_05_08_ikenna.md Tab 1 (Stream A)
  - plans/active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md Stream A
related_plans:
  - plans/active/defi_master.md (Fork 1 carry_staked_basis)
  - plans/active/master_to_live_defi_2026_05_23.md Group F
---

# ETH-LST + stablecoin-LST collateral acceptance (2026-05-07 reverification)

## TL;DR

The `accept=False` LST entries in `unified_api_contracts/registry/venue_collateral.py` for DERIBIT / BYBIT / OKX were
stale as of 2026-05-05; live web-doc reverification on 2026-05-07 confirms multiple LST and stablecoin-LST collateral
types ARE now accepted on these CEX perp venues. Stream A flips the `accepted=False` rows to `accepted=True` with cited
haircut percentages; this codex doc captures the evidence trail.

The `carry_staked_basis` archetype's hedge-leg sizing logic (`accepted_perp_collateral(venue)`) now correctly returns
the LST set per venue, which is what the cross-collateral capital-efficient short on a CEX perp depends on.

## Verified rows (UAC@6c873e4..upcoming)

| Venue   | Token  | Pre-fix          | Post-fix            | Source                                                                                                                                 |
| ------- | ------ | ---------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| DERIBIT | stETH  | False            | True / 7.5% haircut | https://insights.deribit.com/exchange-updates/portfolio-margin-improvements-for-steth-and-cross-collateral-haircuts/ (eff. 2026-01-13) |
| BYBIT   | stETH  | False            | True / 10% haircut  | Bybit margin-spec page — UTA collateral since 2024-02                                                                                  |
| BYBIT   | wstETH | False            | True / 10% haircut  | Bybit margin-spec page — UTA collateral                                                                                                |
| BYBIT   | USDe   | (no prior entry) | True / 5% haircut   | Bybit margin-spec page — UTA collateral since 2024-12-19                                                                               |
| BYBIT   | sUSDe  | (no prior entry) | True / 7% haircut   | Bybit margin-spec page — UTA collateral; sUSDe staked variant                                                                          |
| OKX     | wstETH | False            | True / 10% haircut  | OKX cross-margin docs — multi-currency-margin discount-rate list                                                                       |
| OKX     | stETH  | False            | False (unchanged)   | Not on discount-rate list per same OKX docs                                                                                            |

## Caveats — pending live-API probe

Haircut percentages above are conservative web-doc citations. Each venue exposes the live haircut via account-level APIs
(`/private/get-position-mode`, `/v5/account/info`, `/api/v5/account/account-position-risk`). When operator credentials
are available, run a per-venue probe to confirm the exact 2026-05-07 ratio + paste evidence below.

The `accepted=True` flips above are **conservative-haircut placeholders**: actual venue haircut may be tighter (e.g.
Deribit weekly review may have moved stETH to 5%); too-tight haircut here means archetype underestimates capital
efficiency, which under-utilises the margin pool but does NOT cause a margin call. Too-loose would be the correctness
bug; the placeholders above err on the safe side.

## Why this matters for `carry_staked_basis` (May-23 lead archetype)

The archetype's leg-sequence logic uses `accepted_perp_collateral(venue)` (UAC `venue_collateral.py:206`) to filter to
perp-margining venues that accept the LST as direct margin — this is the capital-efficient short path that avoids
unwinding the LST to ETH for hedging. With the pre-2026-05-07 stale rows, the filter returned zero LST matches for
DERIBIT/BYBIT/OKX, so the archetype would either:

1. Skip those venues entirely (under-uses available perp liquidity), OR
2. Fall back to USD-collateralised short with the LST sold for USDC (eats the unstaking exit cost AND loses the LST
   yield component during the hedge horizon).

Both are wrong post-2026-01-13. The flips above unlock the capital-efficient cross-collateral path.

## What's NOT changed

- HYPERLIQUID rows stay `accepted=False` for all LSTs — Hyperliquid is USDC-only by design.
- BINANCE rows stay `accepted=False` — Binance Multi-Assets Mode currently lists only
  BTC/ETH/BNB/XRP/ADA/DOT/SOL/USDC/USDT (no LST entries).
- ASTER rows stay `accepted=False` — Aster supports USDC/USDT/USDF/asBNB only.
- GMX rows stay `accepted=False` — GMX-V2 per-market collateral sets exclude LSTs.
- The Tardis-captured `*-FUTURES` venue rows track the same gap (linear-USDT or coin-margined only).

## Follow-up items

1. **Live-API probe** — operator-credentialed venue API probe to confirm exact 2026-05-07 haircut ratios + adjust the
   placeholders above accordingly. Filed under `plans/active/defi_master.md` Stream A as "venue_collateral.py haircut
   precision."
2. **carry-staked-basis.md codex doc** — when codex `09-strategy/architecture-v2/archetypes/carry-staked-basis.md` is
   written (currently absent), it should reference this doc + the `accepted_perp_collateral()` helper as the filter
   SSOT. Tracked in master-plan Group F.

## Family 1 — lender admission (recursive supply-borrow loop)

Family 1 (`CARRY_RECURSIVE_BORROW_LENDING_ONLY`) runs a pure-lending loop: LST collateral → Aave V3 E-Mode → borrow ETH
→ swap back to LST via Uniswap V3 SwapRouter02 → redeposit → repeat. The swap-back leg uses the **same SwapRouter02
address `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45` on all chains** (Ethereum, Arbitrum, Base) — no chain-specific
disambiguation required; Uniswap V3 is deployed at this address cross-chain.

Lender admission table (May-23 top-7 cells):

| Lender      | Chain    | Collateral | Debt | E-Mode / Mode   | LTV (max)       | Status                      |
| ----------- | -------- | ---------- | ---- | --------------- | --------------- | --------------------------- |
| Aave V3     | Ethereum | wstETH     | WETH | ETH_CORRELATED  | 0.93            | ADMITTED — flagship cell    |
| Morpho Blue | Ethereum | wstETH     | WETH | per-market LLTV | 0.945           | ADMITTED — highest-LTV      |
| Aave V3     | Arbitrum | wstETH     | WETH | ETH_CORRELATED  | 0.93            | ADMITTED — cheap gas        |
| Aave V3     | Base     | cbETH      | WETH | ETH_CORRELATED  | 0.93 (low-conf) | ADMITTED — Base-native LST  |
| Morpho Blue | Ethereum | sUSDe      | USDC | per-market      | 0.86            | ADMITTED — stable loop      |
| Aave V3     | Ethereum | weETH      | WETH | ETH_CORRELATED  | 0.93            | ADMITTED — restaking points |
| Aave V3     | Base     | wstETH     | WETH | ETH_CORRELATED  | 0.93 (low-conf) | ADMITTED — cheapest gas     |

Lender admission logic: `defi_reserve_params.py` per-chain E-Mode table. Morpho Blue per-market LLTV read from
`defi_reserve_params.py:morpho_markets`. Base chain E-Mode LTVs marked low-confidence until Base Aave V3 params are
live-verified (planned in `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` as P0 unblocker).

## Family 2 — CeFi perp-venue pairing (delta-hedge leg)

Family 2 (`CARRY_BASIS_PERP_INV`) adds a USDC-margined ETH perp short on top of Family 1. The perp margin is **USDC
only** — the LST collateral admitted above does NOT flow to the perp venue. The perp leg uses:

- **Hyperliquid (PRIMARY)**: USDC-only margin (no LST admitted). Margin funded via Arbitrum USDC bridge (~10s finality).
  Funding accrues per-block (continuous). Withdrawal dispute window: 5 minutes.
- **Bybit (SECONDARY, ≤50% of HL notional for first 30 days post-cutover)**: USDC posted as UTA margin. `wstETH` and
  `stETH` accepted at 10% haircut (per `## Verified rows` above), but Family 2 uses USDC-margin path — LST stays in the
  lending loop. Funding paid every 8h (vs HL per-block). Bybit counterparty cap: ≤50% of HL notional for 30d
  post-cutover (Feb-2025 hack discount per `carry-recursive-borrow-perp-hedged.md` § Bybit counterparty cap policy).

Neither HL nor Bybit accept LST as direct perp margin in Family 2. The `accepted_perp_collateral(venue)` filter from
`carry_staked_basis` does NOT apply to Family 2 — the margin leg is fully separated from the lending loop.

## Per-cell backtest verdicts (Phase 12)

Backtest scenario taxonomy for cells using LST collateral:
[recursive-borrow-backtest-scenarios-2026-05.md](recursive-borrow-backtest-scenarios-2026-05.md).

Category B scenarios that directly test collateral-acceptance correctness:

- `SCN-B1-FLASH-CRASH-LST-DEPEG` — validates that 3% wstETH depeg does not liquidate cells where venue LTV margin still
  holds
- `SCN-B4-CBETH-PEG-COINBASE` — validates cbETH bridge-risk alerting fires before collateral value drops below
  acceptance threshold at each venue

Venue-collateral rows with `accepted=True` in the tables above are the cells exercised by these scenarios. Venues with
`accepted=False` (HL, Binance, Aster, GMX) are skipped in Category B.

## Composes with

- `unified-api-contracts/unified_api_contracts/registry/venue_collateral.py` — the SSOT this doc cites.
- `unified-trading-pm/codex/04-architecture/interface-credential-convention.md` — execution-service credential injection
  (relevant for the live-API probe follow-up).
- `unified-trading-pm/plans/active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` — the
  canonicalisation plan that defines Stream A.
- [recursive-borrow-backtest-scenarios-2026-05.md](recursive-borrow-backtest-scenarios-2026-05.md) — Phase 12 scenario
  taxonomy; per-cell verdict matrix; harness shape.
