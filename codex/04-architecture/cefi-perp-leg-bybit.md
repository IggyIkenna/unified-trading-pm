---
doc_type: codex-ssot
title: CeFi Perp Leg — Bybit (Family 2 SECONDARY venue)
summary:
  Bybit as Family 2 (CARRY_BASIS_PERP_INV) SECONDARY perp-hedge venue (≤50% of Hyperliquid notional for 30d
  post-cutover) — UTA USDC-margin topology, Arbitrum USDC deposit route, Feb-2025 hack counterparty cap + LST haircut,
  8h funding cadence vs HL per-block, DEFI_PERP_VENUE_OUTAGE/MARGIN_CALL kill-switches.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [cefi, defi, bybit, execution, strategy, kill-switch]
related:
  [
    plans/active/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md Phase 10,
    plans/archive/2026_07/master_to_live_defi_2026_05_23.md Group F (Family 2 perp leg),
  ]
created: 2026-05-15
authoritative_for: [Bybit Family-2 perp hedge-leg topology]
referenced_by: [/codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-perp-hedged.md]
owner:
last_reviewed: 2026-05-17
code_refs:
author: ikenna-slot-2
---

# CeFi Perp Leg — Bybit (Family 2 SECONDARY venue)

> **Context**: Family 2 (`CARRY_BASIS_PERP_INV`) runs a USDC-margined ETH perp short as the delta-hedge leg. Hyperliquid
> is PRIMARY; Bybit is SECONDARY (≤50% of HL notional for first 30 days post-cutover). This doc covers Bybit-specific
> topology, the Feb-2025 hack risk addendum, and funding-cadence differences vs HL.

## Bybit UTA (Unified Trading Account) overview

Bybit's Unified Trading Account merges spot, margin, and derivatives into a single margin pool. For Family 2:

- **Margin currency**: USDC posted as UTA collateral. The USDC margin path is independent of the LST lending loop — the
  LST stays inside Aave, never crosses to Bybit.
- **Instrument**: `ETH-PERP` (linear USDT-margined) or `ETH/USDC` (USDC-margined). Family 2 uses the USDC-margined
  instrument where available to avoid USDT conversion cost. If USDC-margined perp is unavailable, fall back to
  USDT-margined with `usdt_to_usdc_swap_cost` embedded in gas estimate.
- **Cross-margin**: default. Do NOT switch to isolated margin — isolated breaks the UTA netting benefit.
- **Leverage**: 10× cross-leverage default (same as HL). `PerpLegConfig.max_leverage` caps at 10×.

## USDC deposit route

Preferred: **Arbitrum USDC deposit** (~1 min finality, ~$0.02 gas). Ethereum mainnet deposit is ~3 min + higher gas. Do
NOT use BSC or Polygon routes — Bybit settlement path differs.

- Bridging latency encoded in kill-switch unwind timing: allow 2 min for Bybit USDC availability after on-chain tx.
- `PerpHedgeSizer` monitors `available_margin` via Bybit REST `/v5/account/wallet-balance`; top-up initiated when
  `available_margin / initial_margin < 1.5`.

## Feb-2025 hack addendum

In February 2025, Bybit suffered a cold-wallet exploit that drained approximately $1.4 billion. Bybit restored full
operations via a market buyback over ~72 hours. The event established a counterparty-trust discount that persists:

- **Counterparty cap**: Bybit total notional ≤ 50% of Hyperliquid leg notional for first 30 days post-cutover. After 30
  days, re-evaluate based on Bybit operational track record. Cap codified in `risk-and-exposure-service` venue-cap table
  and in `strategy-service` archetype config per Phase 8.
- **Collateral haircut**: Bybit UTA wstETH / stETH accepted at 10% haircut (updated 2026-05-07 reverification — see
  `venue-collateral-2026-05-07.md`). Family 2 does NOT use LST as Bybit margin (USDC path only); the haircut rows are
  relevant only if `CARRY_STAKED_BASIS` routes to Bybit for the LST-collateralised short.

## Funding cadence vs Hyperliquid

| Property                   | Hyperliquid                          | Bybit                                          |
| -------------------------- | ------------------------------------ | ---------------------------------------------- |
| Funding accrual            | Per-block (continuous, ~2s on HL L1) | Paid every 8 hours (00:00 / 08:00 / 16:00 UTC) |
| Funding APR predictability | High (very short accrual window)     | Lower (8h step; 1-period lag in APR estimate)  |
| Settlement currency        | USDC                                 | USDT or USDC depending on instrument           |
| Withdrawal dispute window  | 5 minutes (HL L1 bridge)             | Immediate (UTA USDC)                           |
| REST rate limit            | 120 req/min per IP                   | 120 req/min per IP                             |

**Implication for `PerpHedgeSizer`**: Bybit funding accrues in 8h blocks. The sizer's rolling 7d + 30d funding-APR
estimate uses the 8h payment timestamps, not per-block accrual. This introduces up to 8h of lag vs HL in detecting a
funding-sign flip. `DEFI_FUNDING_RATE_FLIP` alert fires when the next scheduled payment would be negative by > 1%
annualised, using the last confirmed 8h rate and the current predicted rate from Bybit's `/v5/market/tickers`.

## Kill-switch integration

- `DEFI_PERP_VENUE_OUTAGE` — fires when Bybit REST returns `10004 / rate-limit` or trading halted. Decision tree:
  HF-safe Family 1 leg → route new opens to HL only; HF-near-threshold → flash-close Family 1 + accept outright short on
  HL until Bybit recovers.
- `DEFI_PERP_MARGIN_CALL` — fires when `available_margin < MM x 1.2`. Top-up from treasury; if insufficient → partial
  unwind Family 1 first (releases collateral → ETH → USDC → Bybit deposit).

## See also

- [carry-recursive-borrow-perp-hedged.md](/codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-perp-hedged.md)
  — Family 2 archetype (primary consumer of this doc)
- [venue-collateral-2026-05-07.md](/codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md) — Bybit LST
  collateral acceptance + haircut evidence trail
- [interface-credential-convention.md](interface-credential-convention.md) — credential injection for Bybit REST adapter
  (`get_order_adapter(BYBIT, ...)`)
- [flash-loan-receiver.md](flash-loan-receiver.md) — flash-loan-receiver for Family 1 base (used by Family 2's lending
  loop)
