---
doc_type: issue
title:
  Aster margining registry (venue_collateral.py) drifted vs live Aster docs — product-identity ambiguity, needs operator
  decision before touching
summary: >-
  Re-verification (source: cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md leg (e), from
  perp_funding_data_semantics_and_cadence_2026_06_16.md) found live Aster docs describe a materially richer collateral
  set (BTC/ETH/BNB/SOL and more, with real haircuts) than the currently-registered USDC/USDT-only UAC
  venue_collateral.py rows — but WHICH Aster product corresponds to our fapi.asterdex.com REST integration is genuinely
  ambiguous from the docs alone, so no registry edit was made.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: [aster, margining, collateral, data-correctness, perp-funding]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md,
    /plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md,
  ]
created: 2026-07-28
priority: P2
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: ["cross_cutting_satellite_ao_dispatch_batch1b-006, slot 14, 2026-07-28"]
drift_direction: advance-code
---

# Aster margining registry — live-docs re-verify finding (2026-07-28)

## What I found

Currently registered in `unified-api-contracts/unified_api_contracts/registry/venue_collateral.py` (module docstring
says all Aster haircuts are "F28 live-probed 2026-06-17", not placeholders):

- `ASTER`/`USDC`: accepted, 0% haircut, `CROSS`
- `ASTER`/`USDT`: accepted, 1% haircut, `CROSS`
- `ASTER`/`stETH`, `wstETH`, `weETH`, `JitoSOL`, `mSOL`: all explicitly rejected

Re-fetched live Aster documentation (`docs.asterdex.com`) 2026-07-28. Two DIFFERENT collateral tables exist on the live
docs site and they disagree with each other AND with the registered rows:

**Page 1** (`trading/perpetuals/single-asset-mode-and-multi-asset-mode.md`, general "Aster Perps"): lists collateral
across 4 chains (BNB Chain, Ethereum, Arbitrum, Solana) — USDT/USDC/USD1/BTC/ETH/BNB/SOL/JLP/etc, with stablecoins at
99-99.99%, BTC/ETH at 95% (5% haircut), volatile tokens as low as 10%. States "Single-Asset Mode uses USDT with ISOLATED
margin per position" while "Multi-Asset Mode" is cross-only.

**Page 2** (`astherusex-orderbook-perp-guide/margin.md`, "AstherusEX" — the orderbook/API product, closer in description
to our Binance-Futures-compatible `fapi.asterdex.com` integration): lists BSC-network collateral
(SlisBNB/LisUSD/BTC/ETH/USDT/WBETH/BNB/Stone/LISTA, no USDC) and ETH-network collateral (BTC/ETH/USDT only, no USDC) —
cross-margin only, "Multi-Assets Mode only supports Cross Margin Mode."

**Neither live table matches the registered rows exactly** — both list BTC/ETH as accepted (95%, i.e. NOT rejected,
contrary to nothing being registered for BTC/ETH today) and Page 2 doesn't list USDC as accepted collateral at all
(contrary to the registered `USDC: 0% haircut`).

## Why it matters

`venue_collateral.py` feeds real cash-and-carry / funding-short sizing decisions
(`perp_funding_data_semantics_and_cadence_2026_06_16.md`'s leg (e) exists specifically to gate this). A wrong haircut or
a wrongly-omitted/included collateral asset directly mis-sizes a real position. This is NOT a confirmed-unchanged result
(the done-when in the parent todo explicitly allows either outcome) — it's a genuine drift signal, but blindly
overwriting the registry from either live-docs table risks encoding the WRONG product's rules if `fapi.asterdex.com`
doesn't map 1:1 to either page.

## Recommended decision

**[OPERATOR]** Confirm which live Aster product `market_tick_data_service`'s `fapi.asterdex.com` REST integration
(`api_football`-style Binance-Futures-compatible endpoints — `/fapi/v1/fundingRate`, `/fapi/v1/depth`, etc.) actually
corresponds to: (A) the general multi-chain "Aster Perps" product (Page 1), or (B) the "AstherusEX" orderbook product
(Page 2), or (C) neither (a 3rd distinct API surface not covered by either doc page). Once confirmed, update
`venue_collateral.py`'s Aster rows to match the correct product's live collateral table (adding BTC/ETH/etc. rows as
applicable, correcting haircuts, and confirming/dropping the USDC row depending on which product is live-verified).

## Todos

- [ ] [VERIFY] P2. **Retagged 2026-07-29 (operator: not sure, needs live verification)** — hit the live
      `fapi.asterdex.com` endpoints (`/fapi/v1/fundingRate`, `/fapi/v1/depth`, etc.) and compare the response
      shape/fields against both candidate tables in "What I found" above to determine which Aster product this actually
      is — general "Aster Perps" (multi-chain) vs "AstherusEX" (orderbook) vs a 3rd surface. Once determined, correct
      the `venue_collateral.py` ASTER rows against the right live table. (repo: unified-api-contracts, registry
      verification only — no code change until the product is confirmed).
